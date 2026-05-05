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

import json
import math
import time
from pathlib import Path
from typing import Optional

import cv2
import draccus
import numpy as np
import torch
from geometry_msgs.msg import Twist, Vector3, Wrench
from rclpy.duration import Duration
from rclpy.node import Node
from rclpy.time import Time
from safetensors.torch import load_file
from tf2_ros import TransformException

from aic_control_interfaces.msg import MotionUpdate, TrajectoryGenerationMode
from aic_model.policy import (
    GetObservationCallback,
    MoveRobotCallback,
    Policy,
    SendFeedbackCallback,
)
from aic_model_interfaces.msg import Observation
from aic_task_interfaces.msg import Task

from std_srvs.srv import Trigger

from lerobot.policies.act.configuration_act import ACTConfig
from lerobot.policies.act.modeling_act import ACTPolicy

# ── Approach constants — identical to InsertionDataCollector ─────────────────
_APPROACH_KP            = 4.0
_APPROACH_ORIENT_KP     = 3.0
_APPROACH_Z_ABOVE       = 0.008   # 8 mm before entrance
_APPROACH_DONE_M        = 0.002   # 2 mm position tolerance
_APPROACH_DONE_RAD      = 0.025   # ~1.4° orientation tolerance
_APPROACH_SETTLED_TICKS = 20      # 2 s stable at 10 Hz
_APPROACH_TIMEOUT_S     = 60.0
_MAX_LIN_VEL            = 0.15    # m/s
_MAX_ANG_VEL            = 1.5     # rad/s

# ── Stall-recovery constants ───────────────────────────────────────────────────
_STALL_RATE_MM_S         = 0.5    # mm/s — below this is considered stalled
_STALL_WINDOW_S          = 4.0    # seconds without progress before triggering
_STALL_GRACE_S           = 5.0    # seconds at ACT start before stall check begins
_FORCE_BACKOFF_SPEED_MPS = 0.015  # m/s pullback (matches data collector PULLBACK_VEL_M_S)
_FORCE_BACKOFF_DIST_M    = 0.008  # 8 mm pullback  (matches data collector PULLBACK_DIST_M)
_MAX_REALIGN_RETRIES     = 10


# ── Geometry helpers — copied verbatim from InsertionDataCollector ────────────

def _quat_to_rot(q):
    x, y, z, w = q
    return np.array([
        [1 - 2*(y*y + z*z),   2*(x*y - w*z),   2*(x*z + w*y)],
        [    2*(x*y + w*z), 1 - 2*(x*x + z*z),   2*(y*z - w*x)],
        [    2*(x*z - w*y),   2*(y*z + w*x), 1 - 2*(x*x + y*y)],
    ])


def _rot_error(R_cur: np.ndarray, R_des: np.ndarray) -> np.ndarray:
    """Axis-angle rotation error: angular velocity to rotate R_cur → R_des."""
    R_err = R_des @ R_cur.T
    angle = math.acos(max(-1.0, min(1.0, (np.trace(R_err) - 1) / 2)))
    if angle < 1e-6:
        return np.zeros(3)
    axis = np.array([
        R_err[2, 1] - R_err[1, 2],
        R_err[0, 2] - R_err[2, 0],
        R_err[1, 0] - R_err[0, 1],
    ]) / (2 * math.sin(angle))
    return axis * angle


# ── Policy root resolution ────────────────────────────────────────────────────

def _find_policy_root() -> Path:
    candidate = Path(__file__).resolve().parent.parent / "policy"
    if candidate.is_dir():
        return candidate
    try:
        from ament_index_python.packages import get_package_share_directory
        share = Path(get_package_share_directory("my_policy_node"))
        candidate = share / "policy"
        if candidate.is_dir():
            return candidate
    except Exception:
        pass
    candidate = Path.home() / "ws_aic/src/aic/my_policy_node/policy"
    if candidate.is_dir():
        return candidate
    raise FileNotFoundError(
        "Cannot locate my_policy_node/policy/. "
        "Ensure the workspace is at ~/ws_aic/src/aic/."
    )


_POLICY_ROOT = _find_policy_root()
_DEFAULT_PRETRAINED = (
    _POLICY_ROOT
    / "sfp_insertion_demos_act_20260504_184125_steplast"
    / "pretrained_model"
)


class SFPInsertionPolicy(Policy):
    """
    ACT imitation-learning policy for SFP (and SC) plug insertion.

    GT approach phase (ground_truth:=true required):
      Replicates InsertionDataCollector's KP approach exactly — corrects both
      position AND orientation simultaneously before handing off to ACT.
      Uses velocity control throughout; no mode switching before ACT.

    ACT phase:
      Runs the trained policy at 10 Hz with manual normalisation/denormalisation.
    """

    def __init__(self, parent_node: Node):
        super().__init__(parent_node)
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self._insertion_axis: np.ndarray = np.array([0.0, 0.0, -1.0])  # updated by _gt_approach

        policy_path = self._resolve_policy_path()
        self.get_logger().info(f"SFPInsertionPolicy: loading from {policy_path}")

        with open(policy_path / "config.json") as f:
            config_dict = json.load(f)
        config_dict.pop("type", None)

        config = draccus.decode(ACTConfig, config_dict)
        self.policy = ACTPolicy(config)
        self.policy.load_state_dict(load_file(policy_path / "model.safetensors"))
        self.policy.eval()
        self.policy.to(self.device)

        self.get_logger().info(
            f"SFPInsertionPolicy ready on {self.device}  ({policy_path.parent.name})"
        )

        stats = load_file(
            policy_path / "policy_preprocessor_step_3_normalizer_processor.safetensors"
        )

        def _s(key, shape):
            return stats[key].to(self.device).view(*shape)

        self.img_stats = {
            "left":   {"mean": _s("observation.images.left_camera.mean",   (1, 3, 1, 1)),
                       "std":  _s("observation.images.left_camera.std",    (1, 3, 1, 1))},
            "center": {"mean": _s("observation.images.center_camera.mean", (1, 3, 1, 1)),
                       "std":  _s("observation.images.center_camera.std",  (1, 3, 1, 1))},
            "right":  {"mean": _s("observation.images.right_camera.mean",  (1, 3, 1, 1)),
                       "std":  _s("observation.images.right_camera.std",   (1, 3, 1, 1))},
        }
        self.state_mean  = _s("observation.state.mean",        (1, -1))
        self.state_std   = _s("observation.state.std",         (1, -1))
        self.wrist_mean  = _s("observation.wrist_force.mean",  (1, -1))
        self.wrist_std   = _s("observation.wrist_force.std",   (1, -1))
        self.action_mean = _s("action.mean", (1, -1))
        self.action_std  = _s("action.std",  (1, -1))

        self.get_logger().info("Normalization statistics loaded.")
        self._image_scale = 0.25

        self._tare_cli = parent_node.create_client(
            Trigger, "/aic_controller/tare_force_torque_sensor"
        )

    # ── Model path resolution ─────────────────────────────────────────────

    @staticmethod
    def _resolve_policy_path() -> Path:
        if _DEFAULT_PRETRAINED.is_dir():
            return _DEFAULT_PRETRAINED
        candidates = sorted(
            _POLICY_ROOT.glob("*/pretrained_model"),
            key=lambda p: p.parent.stat().st_mtime,
        )
        if not candidates:
            raise FileNotFoundError(
                f"No pretrained_model directory found under {_POLICY_ROOT}"
            )
        return candidates[-1]

    # ── Force/torque tare ────────────────────────────────────────────────

    def _tare(self) -> None:
        """Zero the force/torque sensor so readings start from 0 each trial."""
        if self._tare_cli.wait_for_service(timeout_sec=1.0):
            future = self._tare_cli.call_async(Trigger.Request())
            deadline = time.monotonic() + 3.0
            while not future.done() and time.monotonic() < deadline:
                self.sleep_for(0.05)
            self.get_logger().info("F/T sensor tared")
        else:
            self.get_logger().warn("Tare service unavailable — force readings may be biased")

    # ── TF helpers ───────────────────────────────────────────────────────

    def _wait_for_tf(self, target: str, source: str, timeout_sec: float = 5.0) -> bool:
        start = self.time_now()
        timeout = Duration(seconds=timeout_sec)
        attempt = 0
        while (self.time_now() - start) < timeout:
            try:
                self._parent_node._tf_buffer.lookup_transform(target, source, Time())
                return True
            except TransformException:
                if attempt % 20 == 0:
                    self.get_logger().info(f"Waiting for TF '{source}' → '{target}'...")
                attempt += 1
                self.sleep_for(0.1)
        return False

    def _lookup_pos_rot(self, frame: str):
        """Return (position np[3], rotation np[3,3]) in base_link frame, or (None, None)."""
        try:
            tf = self._parent_node._tf_buffer.lookup_transform("base_link", frame, Time())
            t = tf.transform.translation
            q = tf.transform.rotation
            pos = np.array([t.x, t.y, t.z])
            rot = _quat_to_rot((q.x, q.y, q.z, q.w))
            return pos, rot
        except TransformException:
            return None, None

    def _lookup_pos(self, frame: str) -> Optional[np.ndarray]:
        pos, _ = self._lookup_pos_rot(frame)
        return pos

    # ── Motion command helpers ────────────────────────────────────────────

    def _make_motion_update(
        self,
        lin: np.ndarray,
        ang: np.ndarray,
        frame_id: str = "base_link",
    ) -> MotionUpdate:
        # Normalise to velocity limits (same as data collector)
        spd = np.linalg.norm(lin)
        if spd > _MAX_LIN_VEL:
            lin = lin / spd * _MAX_LIN_VEL
        asc = np.linalg.norm(ang)
        if asc > _MAX_ANG_VEL:
            ang = ang / asc * _MAX_ANG_VEL

        twist = Twist(
            linear=Vector3(x=float(lin[0]), y=float(lin[1]), z=float(lin[2])),
            angular=Vector3(x=float(ang[0]), y=float(ang[1]), z=float(ang[2])),
        )
        msg = MotionUpdate()
        msg.velocity = twist
        msg.header.frame_id = frame_id
        msg.header.stamp = self.get_clock().now().to_msg()
        msg.target_stiffness = np.diag(
            [100.0, 100.0, 100.0, 50.0, 50.0, 50.0]
        ).flatten().tolist()
        msg.target_damping = np.diag(
            [40.0, 40.0, 40.0, 15.0, 15.0, 15.0]
        ).flatten().tolist()
        msg.feedforward_wrench_at_tip = Wrench(
            force=Vector3(x=0.0, y=0.0, z=0.0),
            torque=Vector3(x=0.0, y=0.0, z=0.0),
        )
        msg.wrench_feedback_gains_at_tip = [0.5, 0.5, 0.5, 0.0, 0.0, 0.0]
        msg.trajectory_generation_mode.mode = TrajectoryGenerationMode.MODE_VELOCITY
        return msg

    def _send_cmd(
        self,
        move_robot: MoveRobotCallback,
        lin: np.ndarray,
        ang: Optional[np.ndarray] = None,
    ) -> None:
        if ang is None:
            ang = np.zeros(3)
        move_robot(motion_update=self._make_motion_update(
            np.asarray(lin, float), np.asarray(ang, float)
        ))

    def _stop(self, move_robot: MoveRobotCallback) -> None:
        self._send_cmd(move_robot, np.zeros(3), np.zeros(3))

    def _backoff(
        self,
        move_robot: MoveRobotCallback,
        send_feedback: SendFeedbackCallback,
    ) -> None:
        """Pull back along the reverse insertion axis to clear a stuck position."""
        backoff_vel = -self._insertion_axis * _FORCE_BACKOFF_SPEED_MPS
        dur = _FORCE_BACKOFF_DIST_M / _FORCE_BACKOFF_SPEED_MPS
        self.get_logger().info(
            f"Backoff: {_FORCE_BACKOFF_DIST_M*1000:.0f} mm along "
            f"{(-self._insertion_axis).round(3)} for {dur:.2f}s"
        )
        send_feedback(f"Force spike — backing off {_FORCE_BACKOFF_DIST_M*1000:.0f} mm...")
        t0 = time.time()
        while time.time() - t0 < dur:
            self._send_cmd(move_robot, backoff_vel)
            self.sleep_for(0.05)
        self._stop(move_robot)
        self.sleep_for(0.1)

    # ── Observation building ──────────────────────────────────────────────

    @staticmethod
    def _img_to_tensor(
        raw_img,
        device: torch.device,
        scale: float,
        mean: torch.Tensor,
        std: torch.Tensor,
    ) -> torch.Tensor:
        img_np = np.frombuffer(raw_img.data, dtype=np.uint8).reshape(
            raw_img.height, raw_img.width, 3
        )
        if scale != 1.0:
            img_np = cv2.resize(
                img_np, None, fx=scale, fy=scale, interpolation=cv2.INTER_AREA
            )
        tensor = (
            torch.from_numpy(img_np.copy())
            .permute(2, 0, 1)
            .float()
            .div(255.0)
            .unsqueeze(0)
            .to(device)
        )
        return (tensor - mean) / std

    def prepare_observations(self, obs_msg: Observation) -> dict:
        tcp = obs_msg.controller_state.tcp_pose
        vel = obs_msg.controller_state.tcp_velocity
        state_np = np.array(
            [
                tcp.position.x, tcp.position.y, tcp.position.z,
                tcp.orientation.x, tcp.orientation.y, tcp.orientation.z, tcp.orientation.w,
                vel.linear.x, vel.linear.y, vel.linear.z,
                vel.angular.x, vel.angular.y, vel.angular.z,
                *obs_msg.controller_state.tcp_error,
                *obs_msg.joint_states.position[:7],
            ],
            dtype=np.float32,
        )
        raw_state = torch.from_numpy(state_np).unsqueeze(0).to(self.device)

        ft = obs_msg.wrist_wrench.wrench.force
        wrist_np = np.array([ft.x, ft.y, ft.z], dtype=np.float32)
        raw_wrist = torch.from_numpy(wrist_np).unsqueeze(0).to(self.device)

        return {
            "observation.images.left_camera": self._img_to_tensor(
                obs_msg.left_image, self.device, self._image_scale,
                self.img_stats["left"]["mean"], self.img_stats["left"]["std"],
            ),
            "observation.images.center_camera": self._img_to_tensor(
                obs_msg.center_image, self.device, self._image_scale,
                self.img_stats["center"]["mean"], self.img_stats["center"]["std"],
            ),
            "observation.images.right_camera": self._img_to_tensor(
                obs_msg.right_image, self.device, self._image_scale,
                self.img_stats["right"]["mean"], self.img_stats["right"]["std"],
            ),
            "observation.state":       (raw_state - self.state_mean) / self.state_std,
            "observation.wrist_force": (raw_wrist - self.wrist_mean) / self.wrist_std,
        }

    # ── GT approach (mirrors InsertionDataCollector exactly) ──────────────

    def _gt_approach(
        self,
        task: Task,
        move_robot: MoveRobotCallback,
        send_feedback: SendFeedbackCallback,
    ) -> bool:
        """
        Simultaneously corrects position AND orientation using KP velocity control,
        identical to InsertionDataCollector._approach().

        Position target: entrance_pos - axis * APPROACH_Z_ABOVE  (8 mm before entrance)
        Orientation target: plug rotation aligned to port rotation
        Settled when both position and orientation are within tolerance for 2 s.
        """
        port_frames = [
            f"task_board/{task.target_module_name}/{task.port_name}_link",
            f"task_board/{task.target_module_name}/{task.port_name}",
        ]
        entrance_frames = [f + "_entrance" for f in port_frames]
        plug_frames = [
            f"{task.cable_name}/{task.plug_name}_link",
            f"{task.cable_name}/{task.plug_name}",
        ]

        # Resolve port position + rotation
        port_pos, port_R = None, None
        for frame in port_frames:
            port_pos, port_R = self._lookup_pos_rot(frame)
            if port_pos is not None:
                break
        if port_pos is None:
            self.get_logger().error("Cannot find port TF — skipping GT approach")
            return False

        # Resolve entrance position (fallback: port + 2 cm in z)
        entrance_pos = None
        for frame in entrance_frames:
            entrance_pos = self._lookup_pos(frame)
            if entrance_pos is not None:
                break
        if entrance_pos is None:
            entrance_pos = port_pos + np.array([0.0, 0.0, 0.02])
            self.get_logger().warn("Entrance frame not found — using port + 2 cm fallback")

        # Insertion axis and approach target
        delta = port_pos - entrance_pos
        dlen = np.linalg.norm(delta)
        axis = delta / dlen if dlen > 0.005 else np.array([0.0, 0.0, -1.0])
        self._insertion_axis = axis   # persist for force monitoring and backoff
        target = entrance_pos - axis * _APPROACH_Z_ABOVE

        self.get_logger().info(
            f"GT approach  port={port_pos.round(3)}  "
            f"entrance={entrance_pos.round(3)}  axis={axis.round(3)}  "
            f"target={target.round(3)}"
        )

        settled = 0
        t0 = time.time()

        while time.time() - t0 < _APPROACH_TIMEOUT_S:
            # Look up plug position and rotation
            plug_pos, plug_R = None, None
            for frame in plug_frames:
                plug_pos, plug_R = self._lookup_pos_rot(frame)
                if plug_pos is not None:
                    break

            if plug_pos is None:
                self.sleep_for(0.1)
                continue

            pos_err = target - plug_pos
            omega = (
                _rot_error(plug_R, port_R)
                if (plug_R is not None and port_R is not None)
                else np.zeros(3)
            )

            lin_vel = _APPROACH_KP * pos_err
            ang_vel = _APPROACH_ORIENT_KP * omega
            self._send_cmd(move_robot, lin_vel, ang_vel)

            pos_ok = np.linalg.norm(pos_err) < _APPROACH_DONE_M
            rot_ok = np.linalg.norm(omega) < _APPROACH_DONE_RAD

            if pos_ok and rot_ok:
                settled += 1
                if settled >= _APPROACH_SETTLED_TICKS:
                    self._stop(move_robot)
                    self.get_logger().info(
                        f"GT approach complete  "
                        f"pos_err={np.linalg.norm(pos_err)*1000:.1f} mm  "
                        f"rot_err={math.degrees(np.linalg.norm(omega)):.2f}°"
                    )
                    return True
            else:
                settled = 0

            if int((time.time() - t0) * 5) % 10 == 0:
                send_feedback(
                    f"GT approach: pos={np.linalg.norm(pos_err)*1000:.1f}mm  "
                    f"rot={math.degrees(np.linalg.norm(omega)):.1f}°  "
                    f"settled={settled}/{_APPROACH_SETTLED_TICKS}"
                )

            self.sleep_for(1.0 / 10)

        self._stop(move_robot)
        self.get_logger().warn(
            "GT approach timeout — starting ACT from current position"
        )
        return False

    # ── Main entry point ──────────────────────────────────────────────────

    def insert_cable(
        self,
        task: Task,
        get_observation: GetObservationCallback,
        move_robot: MoveRobotCallback,
        send_feedback: SendFeedbackCallback,
        **kwargs,
    ) -> bool:
        self._task = task
        self.policy.reset()
        self.get_logger().info(f"SFPInsertionPolicy.insert_cable() — {task}")
        self._tare()

        port_frame = f"task_board/{task.target_module_name}/{task.port_name}_link"
        has_gt = self._wait_for_tf("base_link", port_frame, timeout_sec=3.0)

        if not has_gt:
            self.get_logger().info(
                "No task-board TF (ground_truth=false) — running ACT-only."
            )
            self._act_phase(get_observation, move_robot, send_feedback)
            return True

        send_feedback("GT approach: aligning position and orientation...")
        self._gt_approach(task, move_robot, send_feedback)
        self.sleep_for(0.3)

        for attempt in range(_MAX_REALIGN_RETRIES + 1):
            if attempt > 0:
                send_feedback(
                    f"Realign attempt {attempt}/{_MAX_REALIGN_RETRIES}: "
                    "backing off and realigning..."
                )
                self._backoff(move_robot, send_feedback)
                self.policy.reset()
                self._gt_approach(task, move_robot, send_feedback)
                self.sleep_for(0.3)

            send_feedback(f"ACT insertion (attempt {attempt + 1})...")
            result = self._act_phase(get_observation, move_robot, send_feedback)

            if result != "stall":
                break

            if attempt >= _MAX_REALIGN_RETRIES:
                self.get_logger().warn(
                    f"Max realign retries ({_MAX_REALIGN_RETRIES}) reached — finishing."
                )

        return True

    # ── ACT inference loop ────────────────────────────────────────────────

    def _act_phase(
        self,
        get_observation: GetObservationCallback,
        move_robot: MoveRobotCallback,
        send_feedback: SendFeedbackCallback,
        timeout_sec: float = 60.0,
    ):
        """
        Run ACT inference loop.  Returns True on timeout/completion.
        Returns "stall" when the plug stops making axial progress for
        _STALL_WINDOW_S seconds, mirroring InsertionDataCollector's logic.
        Force is NOT used for stall detection — inertial spikes during motion
        make force unreliable as a trigger.
        """
        # Build plug frame list from stored task
        task = self._task
        plug_frames = [
            f"{task.cable_name}/{task.plug_name}_link",
            f"{task.cable_name}/{task.plug_name}",
        ]

        start = time.time()
        step = 0

        # Stall detection state (mirrors _reset_stall / _check_stall)
        lat_ref        = None   # plug position when ACT started
        stall_last_prog = 0.0
        stall_last_t    = time.monotonic()
        stall_start     = None

        while time.time() - start < timeout_sec:
            t0 = time.time()

            obs_msg = get_observation()
            if obs_msg is None:
                continue

            # ── Stall detection via plug TF ───────────────────────────────
            plug_pos = None
            for frame in plug_frames:
                plug_pos = self._lookup_pos(frame)
                if plug_pos is not None:
                    break

            if plug_pos is not None:
                if lat_ref is None:
                    lat_ref = plug_pos.copy()

                axial_prog = float(np.dot(plug_pos - lat_ref, self._insertion_axis))
                now = time.monotonic()
                dt  = max(now - stall_last_t, 0.01)
                rate_mm_s = (axial_prog - stall_last_prog) / dt * 1000.0
                stall_last_prog = axial_prog
                stall_last_t    = now

                elapsed_act = time.time() - start
                if rate_mm_s < _STALL_RATE_MM_S and elapsed_act > _STALL_GRACE_S:
                    if stall_start is None:
                        stall_start = now
                    elif now - stall_start >= _STALL_WINDOW_S:
                        self._stop(move_robot)
                        self.get_logger().warn(
                            f"Stall at ACT step {step}: "
                            f"axial_prog={axial_prog*1000:.1f}mm  "
                            f"rate={rate_mm_s:.2f}mm/s < {_STALL_RATE_MM_S}mm/s "
                            f"for {now - stall_start:.1f}s — triggering realign"
                        )
                        return "stall"
                else:
                    stall_start = None

            # ── ACT inference ─────────────────────────────────────────────
            obs = self.prepare_observations(obs_msg)

            with torch.inference_mode():
                normalized_action = self.policy.select_action(obs)

            raw_action = (normalized_action * self.action_std) + self.action_mean
            a = raw_action[0].cpu().numpy()

            lin = np.clip(a[:3], -_MAX_LIN_VEL, _MAX_LIN_VEL)
            ang = np.clip(a[3:6], -_MAX_ANG_VEL, _MAX_ANG_VEL)
            self._send_cmd(move_robot, lin, ang)

            if step % 10 == 0:
                prog_mm = float(np.dot(plug_pos - lat_ref, self._insertion_axis)) * 1000 if (plug_pos is not None and lat_ref is not None) else float("nan")
                send_feedback(
                    f"ACT step {step}  prog={prog_mm:.1f}mm  "
                    f"v=[{lin[0]:.3f},{lin[1]:.3f},{lin[2]:.3f}] m/s"
                )
            step += 1

            elapsed = time.time() - t0
            time.sleep(max(0.0, 0.1 - elapsed))

        self.get_logger().info(
            f"ACT phase complete after {step} steps ({timeout_sec:.0f} s timeout)"
        )
        return True
