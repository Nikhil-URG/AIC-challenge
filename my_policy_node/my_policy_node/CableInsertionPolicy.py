#
#  Copyright (C) 2026 Intrinsic Innovation LLC
#
#  Licensed under the Apache License, Version 2.0 (the "License");
#  you may not use this file except in compliance with the License.
#  You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
#  Unless required by applicable law or agreed to in writing, software
#  distributed under the License is distributed on an "AS IS" BASIS,
#  WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#  See the License for the specific language governing permissions and
#  limitations under the License.
#

import os

os.environ["HF_HUB_ENABLE_HF_TRANSFER"] = "1"

import time
import json
import torch
import numpy as np
import cv2
import draccus
from pathlib import Path
from typing import Dict
from rclpy.node import Node
from rclpy.duration import Duration
from rclpy.time import Time
from tf2_ros import TransformException
from geometry_msgs.msg import Twist, Vector3, Point, Pose, Quaternion, Transform

from aic_model.policy import (
    GetObservationCallback,
    MoveRobotCallback,
    Policy,
    SendFeedbackCallback,
)
from aic_model_interfaces.msg import Observation
from aic_task_interfaces.msg import Task

from aic_control_interfaces.msg import (
    MotionUpdate,
    TrajectoryGenerationMode,
)
from geometry_msgs.msg import Wrench

from lerobot.policies.act.modeling_act import ACTPolicy
from lerobot.policies.act.configuration_act import ACTConfig
from safetensors.torch import load_file
from huggingface_hub import snapshot_download


class CableInsertionPolicy(Policy):
    """
    Imitation learning policy for cable insertion using ACT (Action Chunking Transformer).
    Loads a pre-trained model from HuggingFace and runs inference to control the robot.
    """

    def __init__(self, parent_node: Node):
        super().__init__(parent_node)
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

        repo_id = "grkw/aic_act_policy"

        policy_path = Path(
            snapshot_download(
                repo_id=repo_id,
                allow_patterns=["config.json", "model.safetensors", "*.safetensors"],
            )
        )

        with open(policy_path / "config.json", "r") as f:
            config_dict = json.load(f)
            if "type" in config_dict:
                del config_dict["type"]

        config = draccus.decode(ACTConfig, config_dict)

        self.policy = ACTPolicy(config)
        model_weights_path = policy_path / "model.safetensors"
        self.policy.load_state_dict(load_file(model_weights_path))
        self.policy.eval()
        self.policy.to(self.device)

        self.get_logger().info(f"CableInsertionPolicy loaded on {self.device} from {policy_path}")

        stats_path = (
            policy_path / "policy_preprocessor_step_3_normalizer_processor.safetensors"
        )
        stats = load_file(stats_path)

        def get_stat(key, shape):
            return stats[key].to(self.device).view(*shape)

        self.img_stats = {
            "left": {
                "mean": get_stat("observation.images.left_camera.mean", (1, 3, 1, 1)),
                "std": get_stat("observation.images.left_camera.std", (1, 3, 1, 1)),
            },
            "center": {
                "mean": get_stat("observation.images.center_camera.mean", (1, 3, 1, 1)),
                "std": get_stat("observation.images.center_camera.std", (1, 3, 1, 1)),
            },
            "right": {
                "mean": get_stat("observation.images.right_camera.mean", (1, 3, 1, 1)),
                "std": get_stat("observation.images.right_camera.std", (1, 3, 1, 1)),
            },
        }

        self.state_mean = get_stat("observation.state.mean", (1, -1))
        self.state_std = get_stat("observation.state.std", (1, -1))

        self.action_mean = get_stat("action.mean", (1, -1))
        self.action_std = get_stat("action.std", (1, -1))

        self.image_scaling = 0.25

        self.action_velocity_scale = 0.5

        self._tip_x_error_integrator = 0.0
        self._tip_y_error_integrator = 0.0
        self._max_integrator_windup = 0.05

        self.get_logger().info("Normalization statistics loaded successfully.")

    def _wait_for_tf(self, target_frame: str, source_frame: str, timeout_sec: float = 5.0) -> bool:
        """Wait for a TF frame to become available."""
        start = self.time_now()
        timeout = Duration(seconds=timeout_sec)
        attempt = 0
        while (self.time_now() - start) < timeout:
            try:
                self._parent_node._tf_buffer.lookup_transform(
                    target_frame,
                    source_frame,
                    Time(),
                )
                return True
            except TransformException:
                if attempt % 20 == 0:
                    self.get_logger().info(f"Waiting for transform '{source_frame}' -> '{target_frame}'...")
                attempt += 1
                self.sleep_for(0.1)
        return False

    def calc_aligned_pose(
        self,
        port_transform: Transform,
        z_offset: float = 0.1,
    ) -> Pose:
        """Calculate aligned gripper pose above port using ground truth."""
        try:
            plug_tf_stamped = self._parent_node._tf_buffer.lookup_transform(
                "base_link",
                f"{self._task.cable_name}/{self._task.plug_name}_link",
                Time(),
            )
        except TransformException:
            return None

        port_xy = (port_transform.translation.x, port_transform.translation.y)
        plug_xyz = (
            plug_tf_stamped.transform.translation.x,
            plug_tf_stamped.transform.translation.y,
            plug_tf_stamped.transform.translation.z,
        )

        try:
            gripper_tf_stamped = self._parent_node._tf_buffer.lookup_transform(
                "base_link", "gripper/tcp", Time()
            )
        except TransformException:
            return None

        gripper_xyz = (
            gripper_tf_stamped.transform.translation.x,
            gripper_tf_stamped.transform.translation.y,
            gripper_tf_stamped.transform.translation.z,
        )

        tip_x_error = port_xy[0] - plug_xyz[0]
        tip_y_error = port_xy[1] - plug_xyz[1]

        self._tip_x_error_integrator = np.clip(
            self._tip_x_error_integrator + tip_x_error,
            -self._max_integrator_windup,
            self._max_integrator_windup,
        )
        self._tip_y_error_integrator = np.clip(
            self._tip_y_error_integrator + tip_y_error,
            -self._max_integrator_windup,
            self._max_integrator_windup,
        )

        i_gain = 0.15
        target_x = port_xy[0] + i_gain * self._tip_x_error_integrator
        target_y = port_xy[1] + i_gain * self._tip_y_error_integrator
        target_z = port_transform.translation.z + z_offset - (gripper_xyz[2] - plug_xyz[2])

        return Pose(
            position=Point(x=target_x, y=target_y, z=target_z),
            orientation=gripper_tf_stamped.transform.rotation,
        )

    @staticmethod
    def _img_to_tensor(
        raw_img,
        device: torch.device,
        scale: float,
        mean: torch.Tensor,
        std: torch.Tensor,
    ) -> torch.Tensor:
        """Converts ROS Image -> Resized -> Permuted -> Normalized Tensor."""
        img_np = np.frombuffer(raw_img.data, dtype=np.uint8).reshape(
            raw_img.height, raw_img.width, 3
        )

        if scale != 1.0:
            img_np = cv2.resize(
                img_np, None, fx=scale, fy=scale, interpolation=cv2.INTER_AREA
            )

        tensor = (
            torch.from_numpy(img_np)
            .permute(2, 0, 1)
            .float()
            .div(255.0)
            .unsqueeze(0)
            .to(device)
        )

        return (tensor - mean) / std

    def prepare_observations(self, obs_msg: Observation) -> Dict[str, torch.Tensor]:
        """Convert ROS Observation message into dictionary of normalized tensors."""

        obs = {
            "observation.images.left_camera": self._img_to_tensor(
                obs_msg.left_image,
                self.device,
                self.image_scaling,
                self.img_stats["left"]["mean"],
                self.img_stats["left"]["std"],
            ),
            "observation.images.center_camera": self._img_to_tensor(
                obs_msg.center_image,
                self.device,
                self.image_scaling,
                self.img_stats["center"]["mean"],
                self.img_stats["center"]["std"],
            ),
            "observation.images.right_camera": self._img_to_tensor(
                obs_msg.right_image,
                self.device,
                self.image_scaling,
                self.img_stats["right"]["mean"],
                self.img_stats["right"]["std"],
            ),
        }

        tcp_pose = obs_msg.controller_state.tcp_pose
        tcp_vel = obs_msg.controller_state.tcp_velocity

        state_np = np.array(
            [
                tcp_pose.position.x,
                tcp_pose.position.y,
                tcp_pose.position.z,
                tcp_pose.orientation.x,
                tcp_pose.orientation.y,
                tcp_pose.orientation.z,
                tcp_pose.orientation.w,
                tcp_vel.linear.x,
                tcp_vel.linear.y,
                tcp_vel.linear.z,
                tcp_vel.angular.x,
                tcp_vel.angular.y,
                tcp_vel.angular.z,
                *obs_msg.controller_state.tcp_error,
                *obs_msg.joint_states.position[:7],
            ],
            dtype=np.float32,
        )

        raw_state_tensor = (
            torch.from_numpy(state_np).float().unsqueeze(0).to(self.device)
        )
        obs["observation.state"] = (raw_state_tensor - self.state_mean) / self.state_std

        return obs

    def insert_cable(
        self,
        task: Task,
        get_observation: GetObservationCallback,
        move_robot: MoveRobotCallback,
        send_feedback: SendFeedbackCallback,
        **kwargs,
    ):
        """
        Execute the cable insertion task using the trained imitation learning policy.
        Uses ground truth alignment, then ACT for fine control.
        
        Args:
            task: The task specification
            get_observation: Callback to get current observation from sensors
            move_robot: Callback to send motion commands to the robot
            send_feedback: Callback to send feedback/status updates
        """
        self._task = task
        self.policy.reset()
        self.get_logger().info(f"CableInsertionPolicy.insert_cable() enter. Task: {task}")

        port_frame = f"task_board/{task.target_module_name}/{task.port_name}_link"

        if not self._wait_for_tf("base_link", port_frame):
            self.get_logger().warn("Port TF not available, using ACT only mode")
            return self._insert_with_act_only(task, get_observation, move_robot, send_feedback)

        try:
            port_tf_stamped = self._parent_node._tf_buffer.lookup_transform(
                "base_link", port_frame, Time()
            )
        except TransformException as e:
            self.get_logger().warn(f"Could not lookup port: {e}")
            return self._insert_with_act_only(task, get_observation, move_robot, send_feedback)

        port_transform = port_tf_stamped.transform

        send_feedback("Phase 1: Aligning with port (using ground truth)...")

        z_offset = 0.15
        for step in range(50):
            pose = self.calc_aligned_pose(port_transform, z_offset=z_offset)
            if pose:
                self.set_pose_target(move_robot=move_robot, pose=pose)
            self.sleep_for(0.05)

        send_feedback("Phase 2: Descending to approach...")

        while z_offset > 0.02:
            z_offset -= 0.002
            pose = self.calc_aligned_pose(port_transform, z_offset=z_offset)
            if pose:
                self.set_pose_target(move_robot=move_robot, pose=pose)
            self.sleep_for(0.05)

        send_feedback("Phase 3: Final insertion with ACT...")

        return self._insert_with_act_only(task, get_observation, move_robot, send_feedback)

    def _insert_with_act_only(
        self,
        task: Task,
        get_observation: GetObservationCallback,
        move_robot: MoveRobotCallback,
        send_feedback: SendFeedbackCallback,
    ) -> bool:
        """Fallback: Use ACT policy only (original behavior)."""
        start_time = time.time()
        timeout_seconds = 60.0

        while time.time() - start_time < timeout_seconds:
            loop_start = time.time()

            observation_msg = get_observation()
            if observation_msg is None:
                continue

            obs_tensors = self.prepare_observations(observation_msg)

            with torch.inference_mode():
                normalized_action = self.policy.select_action(obs_tensors)

            raw_action_tensor = (normalized_action * self.action_std) + self.action_mean

            action = raw_action_tensor[0].cpu().numpy()

            action[:3] *= self.action_velocity_scale
            action = np.clip(action, -0.15, 0.15)

            twist = Twist(
                linear=Vector3(
                    x=float(action[0]), y=float(action[1]), z=float(action[2])
                ),
                angular=Vector3(
                    x=float(action[3]), y=float(action[4]), z=float(action[5])
                ),
            )
            motion_update = self.set_cartesian_twist_target(twist)
            move_robot(motion_update=motion_update)
            send_feedback("ACT insertion in progress...")

            elapsed = time.time() - loop_start
            time.sleep(max(0, 0.25 - elapsed))

        return True

    def set_cartesian_twist_target(self, twist: Twist, frame_id: str = "base_link"):
        """Create a MotionUpdate message with Cartesian velocity control."""
        motion_update_msg = MotionUpdate()
        motion_update_msg.velocity = twist
        motion_update_msg.header.frame_id = frame_id
        motion_update_msg.header.stamp = self.get_clock().now().to_msg()

        motion_update_msg.target_stiffness = np.diag(
            [100.0, 100.0, 100.0, 50.0, 50.0, 50.0]
        ).flatten()
        motion_update_msg.target_damping = np.diag(
            [40.0, 40.0, 40.0, 15.0, 15.0, 15.0]
        ).flatten()

        motion_update_msg.feedforward_wrench_at_tip = Wrench(
            force=Vector3(x=0.0, y=0.0, z=0.0), torque=Vector3(x=0.0, y=0.0, z=0.0)
        )

        motion_update_msg.wrench_feedback_gains_at_tip = [0.5, 0.5, 0.5, 0.0, 0.0, 0.0]

        motion_update_msg.trajectory_generation_mode.mode = (
            TrajectoryGenerationMode.MODE_VELOCITY
        )

        return motion_update_msg