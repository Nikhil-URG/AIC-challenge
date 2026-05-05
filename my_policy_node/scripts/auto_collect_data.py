import os
os.environ["HF_HUB_ENABLE_HF_TRANSFER"] = "1"

import time
import json
import argparse
import numpy as np
import cv2
import draccus
from pathlib import Path
from typing import Dict, Optional
from rclpy.node import Node
from rclpy.duration import Duration
from rclpy.time import Time
from rclpy.executors import SingleThreadedExecutor
from rclpy.qos import QoSProfile, ReliabilityPolicy, HistoryPolicy
from tf2_ros import Buffer, TransformListener, TransformException
from geometry_msgs.msg import Twist, Vector3, Point, Pose, Quaternion, Transform, WrenchStamped
from sensor_msgs.msg import Image, CameraInfo, JointState
from std_msgs.msg import Header
import rclpy

from lerobot.datasets import LeRobotDataset
# from lerobot.datasets.utils import # dataset_to_policy_format

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


class AutoDataCollector(Policy):
    """
    Automated data collection policy using CheatCode alignment + force control.
    Collects 50 episodes and saves to LeRobot dataset format.
    """

    def __init__(self, parent_node: Node):
        super().__init__(parent_node)
        self._parent_node = parent_node
        self._tf_buffer = Buffer()
        self._tf_listener = TransformListener(self._tf_buffer, parent_node)
        
        # Configuration
        self._num_episodes = 50
        self._current_episode = 0
        self._output_dir = Path("datasets/cable_insertion")
        self._repo_id = "Nikhil-Ravi/teleop_dataset_aic_2026"
        self._fps = 10
        
        # Dataset
        self._dataset = None
        self._episode_start_time = None
        self._frames_collected = 0
        
        # Control params
        self._insertion_force_threshold = 20.0  # N
        self._insertion_velocity = 0.005  # m/s
        self._retract_velocity = 0.02  # m/s
        self._z_offset_initial = 0.15
        self._max_retries = 3
        
        # PI control
        self._tip_x_error_integrator = 0.0
        self._tip_y_error_integrator = 0.0
        self._max_integrator_windup = 0.05
        
        self.get_logger().info("AutoDataCollector initialized")

    def _wait_for_tf(self, target_frame: str, source_frame: str, timeout_sec: float = 5.0) -> bool:
        """Wait for a TF frame to become available."""
        start = self.time_now()
        timeout = Duration(seconds=timeout_sec)
        attempt = 0
        while (self.time_now() - start) < timeout:
            try:
                self._tf_buffer.lookup_transform(target_frame, source_frame, Time())
                return True
            except TransformException:
                if attempt % 20 == 0:
                    self.get_logger().info(f"Waiting for transform '{source_frame}' -> '{target_frame}'...")
                attempt += 1
                self.sleep_for(0.1)
        return False

    def _get_wrench_force(self, observation: Observation) -> float:
        """Extract total force magnitude from wrist wrench."""
        if observation is None or observation.wrist_wrench is None:
            return 0.0
        f = observation.wrist_wrench.wrench.force
        return np.sqrt(f.x**2 + f.y**2 + f.z**2)

    def _get_plug_position(self, task: Task) -> Optional[np.ndarray]:
        """Get current plug tip position in base_link frame."""
        try:
            plug_tf = self._tf_buffer.lookup_transform(
                "base_link",
                f"{task.cable_name}/{task.plug_name}_link",
                Time(),
            )
            return np.array([
                plug_tf.transform.translation.x,
                plug_tf.transform.translation.y,
                plug_tf.transform.translation.z,
            ])
        except TransformException:
            return None

    def _get_port_position(self, task: Task) -> Optional[np.ndarray]:
        """Get port position in base_link frame."""
        try:
            port_frame = f"task_board/{task.target_module_name}/{task.port_name}_link"
            port_tf = self._tf_buffer.lookup_transform("base_link", port_frame, Time())
            return np.array([
                port_tf.transform.translation.x,
                port_tf.transform.translation.y,
                port_tf.transform.translation.z,
            ])
        except TransformException:
            return None

    def _initialize_dataset(self, observation: Observation):
        """Create LeRobot dataset with appropriate features."""
        features = {
            "observation.images.left_camera": {"shape": (3, 270, 480), "dtype": "float32"},
            "observation.images.center_camera": {"shape": (3, 270, 480), "dtype": "float32"},
            "observation.images.right_camera": {"shape": (3, 270, 480), "dtype": "float32"},
            "observation.state": {"shape": (26,), "dtype": "float32"},
            "action": {"shape": (7,), "dtype": "float32"},
            "task": {"dtype": "string"},
        }
        
        self._dataset = LeRobotDataset.create(
            repo_id=self._repo_id,
            fps=self._fps,
            features=features,
            root=self._output_dir,
            use_videos=False,  # Save as images for simplicity; set True for videos
        )
        self._episode_start_time = time.time()
        self.get_logger().info(f"Dataset created at {self._output_dir}")

    def _add_frame(self, observation: Observation, action: np.ndarray, task: Task):
        """Add a frame to the current episode."""
        if self._dataset is None:
            self._initialize_dataset(observation)

        timestamp = time.time() - self._episode_start_time
        
        # Convert ROS images to numpy arrays, resize to model input size
        def img_to_numpy(img_msg):
            arr = np.frombuffer(img_msg.data, dtype=np.uint8).reshape(img_msg.height, img_msg.width, 3)
            return cv2.resize(arr, (480, 270), interpolation=cv2.INTER_AREA)
        
        frame = {
            "observation.images.left_camera": img_to_numpy(observation.left_image),
            "observation.images.center_camera": img_to_numpy(observation.center_image),
            "observation.images.right_camera": img_to_numpy(observation.right_image),
            "observation.state": self._state_from_observation(observation),
            "action": action,
            "task": task.description if hasattr(task, 'description') else "Insert cable",
            "timestamp": timestamp,
        }
        
        self._dataset.add_frame(frame)
        self._frames_collected += 1

    def _state_from_observation(self, observation: Observation) -> np.ndarray:
        """Extract state vector from observation."""
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

    def _save_episode(self):
        """Finalize current episode."""
        if self._dataset is not None:
            self._dataset.save_episode()
            self.get_logger().info(f"Episode {self._current_episode} saved with {self._frames_collected} frames")
            self._frames_collected = 0
            self._episode_start_time = time.time()

    def _align_to_port(self, task: Task, port_pos: np.ndarray, plug_pos: np.ndarray, 
                       move_robot: MoveRobotCallback) -> bool:
        """Align gripper above port using CheatCode PI control."""
        self.get_logger().info("Phase 1: Aligning over port")
        
        try:
            gripper_tf = self._parent_node._tf_buffer.lookup_transform("base_link", "gripper/tcp", Time())
            gripper_xyz = np.array([
                gripper_tf.transform.translation.x,
                gripper_tf.transform.translation.y,
                gripper_tf.transform.translation.z,
            ])
            gripper_quat = gripper_tf.transform.rotation
        except TransformException:
            self.get_logger().error("Cannot get gripper pose for alignment")
            return False

        # Reset integrators
        self._tip_x_error_integrator = 0.0
        self._tip_y_error_integrator = 0.0

        z_target = port_pos[2] + self._z_offset_initial
        target_pose = Pose(
            position=Point(x=port_pos[0], y=port_pos[1], z=z_target),
            orientation=gripper_quat,
        )
        
        # Smooth interpolation over 2 seconds
        steps = 40
        for step in range(steps):
            frac = step / steps
            # Interpolate
            current_pos = gripper_xyz + frac * (np.array([target_pose.position.x, target_pose.position.y, target_pose.position.z]) - gripper_xyz)
            pose = Pose(
                position=Point(x=current_pos[0], y=current_pos[1], z=current_pos[2]),
                orientation=gripper_quat,
            )
            self.set_pose_target(move_robot=move_robot, pose=pose)
            
            # Update integrators
            current_plug_pos = self._get_plug_position(task)
            if current_plug_pos is not None:
                tip_x_error = port_pos[0] - current_plug_pos[0]
                tip_y_error = port_pos[1] - current_plug_pos[1]
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

    def _force_insertion(self, task: Task, port_pos: np.ndarray,
                        get_observation: GetObservationCallback,
                        move_robot: MoveRobotCallback,
                        send_feedback: SendFeedbackCallback) -> bool:
        """Insert with force monitoring and automatic retry."""
        retry_offset = np.zeros(2)
        retrying = False
        start_time = time.time()
        max_duration = 30.0
        
        self.get_logger().info("Phase 2: Force-controlled insertion")
        
        while time.time() - start_time < max_duration:
            observation = get_observation()
            if observation is None:
                continue
            
            current_force = self._get_wrench_force(observation)
            plug_pos = self._get_plug_position(task)
            
            if plug_pos is None:
                continue
            
            twist = Twist()
            
            if retrying:
                # Retract with offset
                twist.linear.z = self._retract_velocity
                twist.linear.x = float(retry_offset[0])
                twist.linear.y = float(retry_offset[1])
                
                if current_force < 5.0:
                    retrying = False
                    self.get_logger().info("Cleared, retrying insertion")
            else:
                # Downward insertion
                twist.linear.z = -self._insertion_velocity
                
                # XY PI control
                xy_error = port_pos[:2] - plug_pos[:2]
                self._tip_x_error_integrator = np.clip(
                    self._tip_x_error_integrator + xy_error[0],
                    -self._max_integrator_windup, self._max_integrator_windup
                )
                self._tip_y_error_integrator = np.clip(
                    self._tip_y_error_integrator + xy_error[1],
                    -self._max_integrator_windup, self._max_integrator_windup
                )
                i_gain = 0.15
                twist.linear.x = float(i_gain * self._tip_x_error_integrator)
                twist.linear.y = float(i_gain * self._tip_y_error_integrator)
                
                if current_force > self._insertion_force_threshold:
                    self.get_logger().info(f"Force {current_force:.2f}N exceeds threshold, retrying with offset")
                    retrying = True
                    retry_offset = np.random.uniform(-0.01, 0.01, 2)
            
            motion_update = self.set_cartesian_twist_target(twist)
            move_robot(motion_update=motion_update)
            
            # Record frame
            action = np.array([
                twist.linear.x, twist.linear.y, twist.linear.z,
                twist.angular.x, twist.angular.y, twist.angular.z,
                0.0  # gripper placeholder
            ])
            self._add_frame(observation, action, task)
            
            # Check completion
            depth = port_pos[2] - plug_pos[2]
            if depth > -0.01 and current_force < 5.0:
                self.get_logger().info(f"Insertion complete: depth={depth:.4f}m")
                time.sleep(5.0)
                return True
            
            time.sleep(0.1)  # 10 Hz control
        
        return False

    def insert_cable(
        self,
        task: Task,
        get_observation: GetObservationCallback,
        move_robot: MoveRobotCallback,
        send_feedback: SendFeedbackCallback,
        **kwargs,
    ):
        """
        Main entry point. Collects multiple episodes automatically.
        """
        self._task = task
        self.get_logger().info(f"AutoDataCollector starting - collecting {self._num_episodes} episodes")
        
        port_frame = f"task_board/{task.target_module_name}/{task.port_name}_link"
        
        if not self._wait_for_tf("base_link", port_frame):
            self.get_logger().error("Port TF not available")
            return False
        
        try:
            port_tf = self._parent_node._tf_buffer.lookup_transform("base_link", port_frame, Time())
            port_pos = np.array([port_tf.transform.translation.x, port_tf.transform.translation.y, port_tf.transform.translation.z])
        except TransformException as e:
            self.get_logger().error(f"Cannot get port position: {e}")
            return False
        
        episodes_completed = 0
        attempts = 0
        max_attempts = self._num_episodes * 2
        
        while episodes_completed < self._num_episodes and attempts < max_attempts:
            attempts += 1
            self.get_logger().info(f"Episode {episodes_completed + 1}/{self._num_episodes} (attempt {attempts})")
            
            # Ensure we're at a safe starting height
            self.get_logger().info("Moving to safe starting height...")
            safe_pose = Pose(
                position=Point(x=-0.4, y=0.45, z=0.3),
                orientation=Quaternion(x=1.0, y=0.0, z=0.0, w=0.0),
            )
            self.set_pose_target(move_robot=move_robot, pose=safe_pose)
            time.sleep(2.0)
            
            # Get plug position
            plug_pos = self._get_plug_position(task)
            if plug_pos is None:
                self.get_logger().warn("No plug detected, skipping episode")
                continue
            
            # Align above port
            if not self._align_to_port(task, port_pos, plug_pos, move_robot):
                self.get_logger().warn("Alignment failed, retrying...")
                continue
            
            # Perform insertion
            success = self._force_insertion(task, port_pos, get_observation, move_robot, send_feedback)
            
            if success:
                self._save_episode()
                episodes_completed += 1
                self._current_episode = episodes_completed
                send_feedback(f"Episode {episodes_completed} completed")
                
                # Reset integrators for next episode
                self._tip_x_error_integrator = 0.0
                self._tip_y_error_integrator = 0.0
            else:
                self.get_logger().warn("Insertion failed, retrying...")
        
        if self._dataset is not None:
            self.get_logger().info("Finalizing dataset...")
            self._dataset.finalize()
            self.get_logger().info(f"Dataset saved to: {self._dataset.root}")
            
            # Push to hub if configured
            if self._repo_id and self._repo_id != "your_username/cable_insertion_autocollect":
                try:
                    self._dataset.push_to_hub(commit_message=f"Auto-collected {episodes_completed} episodes")
                    self.get_logger().info(f"Dataset pushed to: {self._repo_id}")
                except Exception as e:
                    self.get_logger().error(f"Failed to push dataset: {e}")
        
        self.get_logger().info(f"Collection complete: {episodes_completed} episodes from {attempts} attempts")
        return True