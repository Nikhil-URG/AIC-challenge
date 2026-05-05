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
import numpy as np
import cv2
import random
from pathlib import Path
from typing import Optional
from rclpy.node import Node
from rclpy.duration import Duration
from rclpy.time import Time
from tf2_ros import TransformException
from geometry_msgs.msg import Twist, Point, Pose, Quaternion, WrenchStamped, Vector3
from std_srvs.srv import Empty, Trigger

from aic_model.policy import (
    GetObservationCallback,
    MoveRobotCallback,
    Policy,
    SendFeedbackCallback,
)
from aic_model_interfaces.msg import Observation
from aic_task_interfaces.msg import Task

from aic_control_interfaces.msg import MotionUpdate, TrajectoryGenerationMode
from geometry_msgs.msg import Wrench

# Optional interfaces (may not be in all environments)
try:
    from aic_training_interfaces.srv import ExpandXacro
    _has_expand_xacro = True
except ImportError:
    _has_expand_xacro = False

try:
    from gazebo_msgs.srv import SpawnEntity, DeleteEntity
    _has_gazebo_services = True
except ImportError:
    _has_gazebo_services = False

from lerobot.datasets import LeRobotDataset

# tf_transformations for quaternion math
try:
    from tf_transformations import quaternion_from_euler, euler_from_quaternion
except ImportError:
    # Fallback minimal implementations
    def quaternion_from_euler(roll, pitch, yaw):
        cy = np.cos(yaw * 0.5); sy = np.sin(yaw * 0.5)
        cp = np.cos(pitch * 0.5); sp = np.sin(pitch * 0.5)
        cr = np.cos(roll * 0.5); sr = np.sin(roll * 0.5)
        return [sr*cp*cy - cr*sp*sy, cr*sp*cy + sr*cp*sy, cr*cp*sy - sr*sp*cy, cr*cp*cy + sr*sp*sy]
    def euler_from_quaternion(q):
        import math
        x, y, z, w = q
        t0 = 2.0*(w*x + y*z); t1 = 1.0 - 2.0*(x*x + y*y)
        roll = math.atan2(t0, t1)
        t2 = 2.0*(w*y - z*x); t2 = max(-1.0, min(1.0, t2))
        pitch = math.asin(t2)
        t3 = 2.0*(w*z + x*y); t4 = 1.0 - 2.0*(y*y + z*z)
        yaw = math.atan2(t3, t4)
        return (roll, pitch, yaw)


class AutoDataCollector(Policy):
    """
    Automated data collection for cable insertion.
    Uses scene randomization via training utils and force-controlled insertion.
    Records episodes as LeRobot dataset.
    """

    def __init__(self, parent_node: Node):
        super().__init__(parent_node)
        self._parent_node = parent_node
        self._task = None

        # Dataset config
        self._max_episodes = 50
        self._current_episode = 0
        self._output_dir = Path("datasets/cable_insertion")
        self._repo_id = "your_username/cable_insertion_autocollect"
        self._fps = 10
        self._dataset = None
        self._episode_start_time = None
        self._frames_collected = 0

        # Force monitoring
        self._insertion_force_threshold = 20.0
        self._retract_velocity = 0.02
        self._clear_force_threshold = 5.0

        # PI control
        self._tip_x_error_integrator = 0.0
        self._tip_y_error_integrator = 0.0
        self._max_integrator_windup = 0.05

        # Velocity
        self._insertion_velocity = 0.005

        # Service clients
        self._tare_client = self._parent_node.create_client(Trigger, '/aic_controller/tare_force_torque_sensor')
        self._reset_client = self._parent_node.create_client(Trigger, '/scoring/reset_joints')

        if _has_expand_xacro:
            self._expand_client = self._parent_node.create_client(ExpandXacro, '/expand_xacro')
        else:
            self._expand_client = None
        if _has_gazebo_services:
            self._spawn_client = self._parent_node.create_client(SpawnEntity, '/gz_server/spawn_entity')
            self._delete_client = self._parent_node.create_client(DeleteEntity, '/gz_server/delete_entity')
        else:
            self._spawn_client = None
            self._delete_client = None

        self.get_logger().info("AutoDataCollector initialized")

    def _wait_for_tf(self, target_frame: str, source_frame: str, timeout_sec: float = 10.0) -> bool:
        start = self.time_now()
        timeout = Duration(seconds=timeout_sec)
        attempt = 0
        while (self.time_now() - start) < timeout:
            try:
                self._parent_node._tf_buffer.lookup_transform(target_frame, source_frame, Time())
                return True
            except TransformException:
                if attempt % 20 == 0:
                    self.get_logger().info(f"Waiting for TF: {source_frame} -> {target_frame}")
                attempt += 1
                self.sleep_for(0.1)
        self.get_logger().error(f"TF timeout: {source_frame} -> {target_frame}")
        return False

    def _get_wrench_force(self, observation: Observation) -> float:
        if observation is None or observation.wrist_wrench is None:
            return 0.0
        f = observation.wrist_wrench.wrench.force
        return np.sqrt(f.x**2 + f.y**2 + f.z**2)

    def _get_plug_position(self) -> Optional[np.ndarray]:
        try:
            plug_tf = self._parent_node._tf_buffer.lookup_transform(
                "base_link",
                f"{self._task.cable_name}/{self._task.plug_name}_link",
                Time(),
            )
            return np.array([plug_tf.transform.translation.x,
                            plug_tf.transform.translation.y,
                            plug_tf.transform.translation.z])
        except TransformException:
            return None

    def _get_port_position(self) -> Optional[np.ndarray]:
        try:
            port_frame = f"task_board/{self._task.target_module_name}/{self._task.port_name}_link"
            port_tf = self._parent_node._tf_buffer.lookup_transform("base_link", port_frame, Time())
            return np.array([port_tf.transform.translation.x,
                            port_tf.transform.translation.y,
                            port_tf.transform.translation.z])
        except TransformException:
            return None

    def _get_gripper_pose(self) -> Optional[Pose]:
        try:
            gripper_tf = self._parent_node._tf_buffer.lookup_transform("base_link", "gripper/tcp", Time())
            return Pose(
                position=Point(x=gripper_tf.transform.translation.x,
                               y=gripper_tf.transform.translation.y,
                               z=gripper_tf.transform.translation.z),
                orientation=gripper_tf.transform.rotation,
            )
        except TransformException:
            return None

    def _align_over_port(self, move_robot: MoveRobotCallback,
                         port_position: np.ndarray, plug_position: np.ndarray) -> bool:
        self.get_logger().info("Aligning over port...")
        try:
            gripper_tf = self._parent_node._tf_buffer.lookup_transform("base_link", "gripper/tcp", Time())
            gripper_xyz = np.array([gripper_tf.transform.translation.x,
                                    gripper_tf.transform.translation.y,
                                    gripper_tf.transform.translation.z])
            gripper_quat = gripper_tf.transform.rotation
        except TransformException:
            self.get_logger().error("Cannot get gripper pose for alignment")
            return False

        self._tip_x_error_integrator = 0.0
        self._tip_y_error_integrator = 0.0

        z_target = port_position[2] + 0.15
        start_pose = gripper_xyz.copy()

        steps = 40
        for step in range(steps):
            frac = step / steps
            current_target = start_pose + frac * (np.array([port_position[0], port_position[1], z_target]) - start_pose)
            pose = Pose(
                position=Point(x=current_target[0], y=current_target[1], z=current_target[2]),
                orientation=gripper_quat,
            )
            self.set_pose_target(move_robot=move_robot, pose=pose)

            current_plug = self._get_plug_position()
            if current_plug is not None:
                tip_x_error = port_position[0] - current_plug[0]
                tip_y_error = port_position[1] - current_plug[1]
                self._tip_x_error_integrator = np.clip(
                    self._tip_x_error_integrator + tip_x_error,
                    -self._max_integrator_windup, self._max_integrator_windup
                )
                self._tip_y_error_integrator = np.clip(
                    self._tip_y_error_integrator + tip_y_error,
                    -self._max_integrator_windup, self._max_integrator_windup
                )
            self.sleep_for(0.05)
        return True

    def _insert_with_force_control(self,
                                   get_observation: GetObservationCallback,
                                   move_robot: MoveRobotCallback,
                                   send_feedback: SendFeedbackCallback) -> bool:
        self.get_logger().info("Starting force-controlled insertion")
        port_position = self._get_port_position()
        if port_position is None:
            return False

        insertion_complete = False
        retry_mode = False
        retry_offset = np.zeros(2)
        start_time = time.time()
        max_time = 30.0

        while time.time() - start_time < max_time and not insertion_complete:
            observation = get_observation()
            if observation is None:
                continue

            current_force = self._get_wrench_force(observation)
            current_plug_pos = self._get_plug_position()
            gripper_pose = self._get_gripper_pose()
            if current_plug_pos is None or gripper_pose is None:
                continue

            twist = Twist()
            if retry_mode:
                self.get_logger().info(f"Retry: moving up with offset {retry_offset}")
                twist.linear.z = self._retract_velocity
                twist.linear.x = float(retry_offset[0])
                twist.linear.y = float(retry_offset[1])
                if current_force < self._clear_force_threshold:
                    retry_mode = False
                    self.get_logger().info("Cleared, retrying insertion")
            else:
                if current_force > self._insertion_force_threshold:
                    self.get_logger().info(f"Force threshold reached: {current_force:.2f} N")
                    retry_mode = True
                    retry_offset = np.random.uniform(-0.01, 0.01, 2)
                    twist.linear.z = self._retract_velocity
                    twist.linear.x = float(retry_offset[0])
                    twist.linear.y = float(retry_offset[1])
                else:
                    twist.linear.z = -self._insertion_velocity
                    tip_x_error = port_position[0] - current_plug_pos[0]
                    tip_y_error = port_position[1] - current_plug_pos[1]
                    self._tip_x_error_integrator = np.clip(
                        self._tip_x_error_integrator + tip_x_error,
                        -self._max_integrator_windup, self._max_integrator_windup
                    )
                    self._tip_y_error_integrator = np.clip(
                        self._tip_y_error_integrator + tip_y_error,
                        -self._max_integrator_windup, self._max_integrator_windup
                    )
                    i_gain = 0.15
                    twist.linear.x = float(i_gain * self._tip_x_error_integrator)
                    twist.linear.y = float(i_gain * self._tip_y_error_integrator)

            motion_update = self.set_cartesian_twist_target(twist)
            move_robot(motion_update=motion_update)

            # Record frame
            action = np.array([
                twist.linear.x, twist.linear.y, twist.linear.z,
                twist.angular.x, twist.angular.y, twist.angular.z,
                0.0
            ], dtype=np.float32)
            # Ensure we have a task set
            if hasattr(self, '_task') and self._task is not None:
                self._add_frame(observation, action, self._task)

            # Check completion
            if current_plug_pos is not None and port_position is not None:
                depth = port_position[2] - current_plug_pos[2]
                if depth > -0.01 and current_force < 5.0:
                    self.get_logger().info(f"Insertion complete! Depth: {depth:.4f}m")
                    insertion_complete = True

            time.sleep(0.05)

        if insertion_complete:
            time.sleep(5.0)
            return True
        else:
            self.get_logger().warn("Insertion timed out")
            return False

    def _state_from_observation(self, observation: Observation) -> np.ndarray:
        tcp_pose = observation.controller_state.tcp_pose
        tcp_vel = observation.controller_state.tcp_velocity
        return np.array([
            tcp_pose.position.x, tcp_pose.position.y, tcp_pose.position.z,
            tcp_pose.orientation.x, tcp_pose.orientation.y, tcp_pose.orientation.z, tcp_pose.orientation.w,
            tcp_vel.linear.x, tcp_vel.linear.y, tcp_vel.linear.z,
            tcp_vel.angular.x, tcp_vel.angular.y, tcp_vel.angular.z,
            *observation.controller_state.tcp_error,
            *observation.joint_states.position[:7],
        ], dtype=np.float32)

    def _img_to_numpy(self, img_msg) -> np.ndarray:
        arr = np.frombuffer(img_msg.data, dtype=np.uint8).reshape(img_msg.height, img_msg.width, 3)
        if arr.shape[:2] != (270, 480):
            arr = cv2.resize(arr, (480, 270), interpolation=cv2.INTER_AREA)
        return arr

    def _initialize_dataset(self, observation: Observation):
        features = {
            "observation.images.left_camera": {"shape": (3, 270, 480), "dtype": "uint8"},
            "observation.images.center_camera": {"shape": (3, 270, 480), "dtype": "uint8"},
            "observation.images.right_camera": {"shape": (3, 270, 480), "dtype": "uint8"},
            "observation.state": {"shape": (26,), "dtype": "float32"},
            "observation.board_position": {"shape": (3,), "dtype": "float32"},
            "action": {"shape": (7,), "dtype": "float32"},
            "task": {"dtype": "string"},
        }
        self._dataset = LeRobotDataset.create(
            repo_id=self._repo_id,
            fps=self._fps,
            features=features,
            root=self._output_dir,
            use_videos=False,
        )
        self._episode_start_time = time.time()
        self.get_logger().info(f"Dataset created at {self._output_dir}")

    def _add_frame(self, observation: Observation, action: np.ndarray, task: Task):
        if self._dataset is None:
            self._initialize_dataset(observation)
        # Get current board position from TF
        board_frame = f"task_board/{task.target_module_name}"
        try:
            board_tf = self._parent_node._tf_buffer.lookup_transform("base_link", board_frame, Time())
            board_pos = np.array([board_tf.transform.translation.x,
                                  board_tf.transform.translation.y,
                                  board_tf.transform.translation.z], dtype=np.float32)
        except TransformException:
            board_pos = np.zeros(3, dtype=np.float32)

        frame = {
            "observation.images.left_camera": self._img_to_numpy(observation.left_image),
            "observation.images.center_camera": self._img_to_numpy(observation.center_image),
            "observation.images.right_camera": self._img_to_numpy(observation.right_image),
            "observation.state": self._state_from_observation(observation),
            "observation.board_position": board_pos,
            "action": action,
            "task": getattr(task, 'description', "Insert cable"),
        }
        self._dataset.add_frame(frame)
        self._frames_collected += 1

    def _save_episode(self):
        if self._dataset is not None:
            self._dataset.save_episode()
            self.get_logger().info(f"Episode {self._current_episode} saved ({self._frames_collected} frames)")
            self._frames_collected = 0

    def _finalize_dataset(self):
        if self._dataset is not None:
            self._dataset.finalize()
            self.get_logger().info(f"Dataset finalized at {self._output_dir}")
            if self._repo_id and self._repo_id != "your_username/cable_insertion_autocollect":
                try:
                    self._dataset.push_to_hub(commit_message=f"Auto-collected {self._current_episode} episodes")
                    self.get_logger().info(f"Dataset pushed to: {self._repo_id}")
                except Exception as e:
                    self.get_logger().error(f"Failed to push dataset: {e}")

    def _tare_force_sensor(self):
        if self._tare_client.wait_for_service(timeout_sec=1.0):
            self._tare_client.call_async(Trigger.Request())
            self.get_logger().info("Tared F/T sensor")
        else:
            self.get_logger().warn("Tare service not available")

    def _tare_force_sensor(self):
        if self._tare_client.wait_for_service(timeout_sec=1.0):
            self._tare_client.call_async(Trigger.Request())
            self.get_logger().info("Tared F/T sensor")
        else:
            self.get_logger().warn("Tare service not available")

    def _reset_simulation(self):
        try:
            if self._reset_client.wait_for_service(timeout_sec=1.0):
                self._reset_client.call_async(Trigger.Request())
                self.get_logger().info("Reset joints service called")
                time.sleep(2.0)
                return
        except Exception as e:
            self.get_logger().debug(f"Scoring reset not available: {e}")
        for srv_name in ['/reset_simulation', '/reset_world']:
            try:
                reset_client = self._parent_node.create_client(Empty, srv_name)
                if reset_client.wait_for_service(timeout_sec=0.5):
                    reset_client.call_async(Empty.Request())
                    self.get_logger().info(f"Gazebo reset: {srv_name}")
                    time.sleep(2.0)
                    return
            except Exception:
                pass
        self.get_logger().warn("No reset service found")

    def _delete_entity(self, name: str) -> bool:
        if self._delete_client is None:
            return False
        try:
            req = DeleteEntity.Request()
            req.name = name
            req.force = True
            self._delete_client.call_async(req)
            time.sleep(0.5)
            self.get_logger().info(f"Deleted: {name}")
            return True
        except Exception as e:
            self.get_logger().error(f"Delete failed {name}: {e}")
            return False

    def _spawn_entity(self, name: str, xml: str, pose: Optional[Pose] = None) -> bool:
        if self._spawn_client is None:
            return False
        try:
            req = SpawnEntity.Request()
            req.name = name
            req.xml = xml
            req.allow_renaming = False
            if pose:
                req.initial_pose = pose
            self._spawn_client.call_async(req)
            time.sleep(1.0)
            self.get_logger().info(f"Spawned: {name}")
            return True
        except Exception as e:
            self.get_logger().error(f"Spawn failed {name}: {e}")
            return False

    def _expand_xacro(self, package_name: str, relative_path: str, xacro_args: list) -> Optional[str]:
        if self._expand_client is None or not self._expand_client.wait_for_service(timeout_sec=2.0):
            self.get_logger().error("ExpandXacro service not available")
            return None
        req = ExpandXacro.Request()
        req.package_name = package_name
        req.relative_path = relative_path
        req.xacro_arguments = xacro_args
        future = self._expand_client.call_async(req)
        start = self.time_now()
        while not future.done():
            if (self.time_now() - start).nanoseconds > 5e9:
                self.get_logger().error("ExpandXacro timeout")
                return None
            time.sleep(0.1)
        resp = future.result()
        if resp.success:
            return resp.xml
        else:
            self.get_logger().error(f"ExpandXacro failed: {resp.message}")
            return None

    def _randomize_board_pose(self):
        x = random.uniform(0.15, 0.18)
        y = random.uniform(-0.2, 0.1)
        z = 1.14
        yaw = random.uniform(3.0, 3.14159)
        q = quaternion_from_euler(0.0, 0.0, yaw)
        pose = Pose(
            position=Point(x=x, y=y, z=z),
            orientation=Quaternion(x=q[0], y=q[1], z=q[2], w=q[3])
        )
        components = {
            'nic_card_mount_0_present': random.choice([True, False]),
            'nic_card_mount_1_present': random.choice([True, False]),
            'sc_port_0_present': random.choice([True, False]),
            'sc_port_1_present': random.choice([True, False]),
            'sfp_mount_rail_0_present': random.choice([True, False]),
            'sfp_mount_rail_1_present': random.choice([True, False]),
            'lc_mount_rail_0_present': random.choice([True, False]),
            'lc_mount_rail_1_present': random.choice([True, False]),
        }
        return pose, yaw, components

    def reset_scene(self, task: Task) -> bool:
        """Reset scene with randomization using training utils or fallback."""
        self.get_logger().info("Resetting scene...")

        if self._expand_client is not None and self._spawn_client is not None:
            self._delete_entity("task_board")
            self._delete_entity("cable_0")
            time.sleep(1.0)

            board_pose, yaw, components = self._randomize_board_pose()
            xacro_args = [
                "ground_truth:=true",
                f"task_board_x:={board_pose.position.x}",
                f"task_board_y:={board_pose.position.y}",
                f"task_board_z:={board_pose.position.z}",
                "task_board_roll:=0.0",
                "task_board_pitch:=0.0",
                f"task_board_yaw:={yaw}",
            ]
            for comp, present in components.items():
                xacro_args.append(f"{comp}:={str(present).lower()}")
            xacro_args.extend([
                "spawn_cable:=true",
                "cable_type:=sfp_sc_cable",
                "attach_cable_to_gripper:=true",
            ])

            xml = self._expand_xacro('aic_description', 'urdf/task_board.urdf.xacro', xacro_args)
            if xml is not None and self._spawn_entity("task_board", xml, board_pose):
                time.sleep(2.0)
                self._tare_force_sensor()
                time.sleep(0.5)
                return True
            else:
                self.get_logger().warn("Training utils spawn failed, using fallback")

        # Fallback to joint reset
        self._reset_simulation()
        time.sleep(2.0)
        self._tare_force_sensor()
        time.sleep(0.5)
        return True

    def insert_cable(
        self,
        task: Task,
        get_observation: GetObservationCallback,
        move_robot: MoveRobotCallback,
        send_feedback: SendFeedbackCallback,
        **kwargs,
    ):
        self._task = task
        self.get_logger().info(f"AutoDataCollector: {self._max_episodes} episodes")

        while self._current_episode < self._max_episodes:
            self.get_logger().info(f"=== Episode {self._current_episode + 1}/{self._max_episodes} ===")

            if not self.reset_scene(task):
                self.get_logger().error("Scene reset failed")
                return False

            port_frame = f"task_board/{task.target_module_name}/{task.port_name}_link"
            if not self._wait_for_tf("base_link", port_frame, timeout_sec=10.0):
                self.get_logger().error("Port TF not available")
                break

            try:
                port_tf = self._parent_node._tf_buffer.lookup_transform("base_link", port_frame, Time())
                port_position = np.array([port_tf.transform.translation.x,
                                         port_tf.transform.translation.y,
                                         port_tf.transform.translation.z])
            except TransformException as e:
                self.get_logger().error(f"Cannot get port position: {e}")
                break

            plug_position = self._get_plug_position()
            if plug_position is None:
                self.get_logger().error("Plug position not available")
                break

            send_feedback(f"Episode {self._current_episode+1}: Aligning")
            if not self._align_over_port(move_robot, port_position, plug_position):
                self.get_logger().warn("Alignment failed - retrying")
                time.sleep(1.0)
                continue

            send_feedback("Inserting...")
            success = self._insert_with_force_control(get_observation, move_robot, send_feedback)

            if success:
                self._save_episode()
                self._current_episode += 1
                self.get_logger().info(f"Episode {self._current_episode} completed")
                self._tip_x_error_integrator = 0.0
                self._tip_y_error_integrator = 0.0

                if self._current_episode >= self._max_episodes:
                    self._finalize_dataset()
                    self.get_logger().info("All episodes collected.")
                    break
            else:
                self.get_logger().warn("Insertion failed - retrying")
                time.sleep(1.0)

        return True

    def set_cartesian_twist_target(self, twist: Twist, frame_id: str = "base_link"):
        motion_update_msg = MotionUpdate()
        motion_update_msg.velocity = twist
        motion_update_msg.header.frame_id = frame_id
        motion_update_msg.header.stamp = self.get_clock().now().to_msg()
        motion_update_msg.target_stiffness = np.diag([100.0, 100.0, 100.0, 50.0, 50.0, 50.0]).flatten()
        motion_update_msg.target_damping = np.diag([40.0, 40.0, 40.0, 15.0, 15.0, 15.0]).flatten()
        motion_update_msg.feedforward_wrench_at_tip = Wrench(force=Vector3(x=0.0, y=0.0, z=0.0),
                                                              torque=Vector3(x=0.0, y=0.0, z=0.0))
        motion_update_msg.wrench_feedback_gains_at_tip = [0.5, 0.5, 0.5, 0.0, 0.0, 0.0]
        motion_update_msg.trajectory_generation_mode.mode = TrajectoryGenerationMode.MODE_VELOCITY
        return motion_update_msg