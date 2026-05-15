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
import os
import time
from pathlib import Path
from typing import Optional

import cv2
import draccus
import numpy as np
import torch
from geometry_msgs.msg import TransformStamped, Twist, Vector3, Wrench
from visualization_msgs.msg import Marker, MarkerArray
from rclpy.duration import Duration
from rclpy.node import Node
from rclpy.time import Time
from safetensors.torch import load_file
from tf2_ros import TransformBroadcaster, TransformException

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

from my_policy_node.PortPoseDetector import CLASS_SC, CLASS_SFP, PortPoseDetector

# ── Approach constants — identical to InsertionDataCollector ─────────────────
_APPROACH_KP            = 4.0
_APPROACH_AXIS_ORIENT_KP = 1.5
_APPROACH_AXIS_MAX_ANG_VEL = 0.35
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
_CLOSE_THRESH_M          = 0.010  # 10 mm to port — suppress stall, plug nearly inserted
_INSERT_DONE_M           = 0.002  # 2 mm — declare success
_BACKOFF_SPEED_MPS       = 0.015  # m/s pullback speed
_BACKOFF_SHORT_M         = 0.002  # 2 mm — attempts 1-2
_BACKOFF_LONG_M          = 0.003  # 3 mm — attempts 3+
# ── Lateral-correction overlay (attempts 3-5, mirrors data collector) ─────────
_LATERAL_KP              = 10.0   # lateral hold gain  (INSERT_HOLD_KP)
# ── Wiggle-entry mode (attempts > 5) ──────────────────────────────────────────
_WIGGLE_Z_ABOVE          = 0.001  # 1 mm above entrance before wiggling
_WIGGLE_AMP_M            = 0.0015 # 1.5 mm circular wiggle amplitude
_WIGGLE_FREQ_HZ          = 1.5    # Hz
_WIGGLE_PUSH_MPS         = 0.003  # gentle axial push during wiggle
_WIGGLE_TIMEOUT_S        = 20.0
_MAX_REALIGN_RETRIES     = 10
_SERVO_INSERT_SPEED_MPS  = 0.010

# ── YOLO/PnP safety and debug ─────────────────────────────────────────────────
_YOLO_MAX_TARGET_DIST_M   = 0.12
_YOLO_MAX_UPWARD_STEP_M   = 0.04
_YOLO_MAX_DOWNWARD_STEP_M = 0.04
_YOLO_CALIBRATION_PROBE_M = 0.003
_YOLO_CALIBRATION_MAX_POS_SPREAD_M = 0.030
_YOLO_CALIBRATION_MAX_Z_SPREAD_M = 0.020
_YOLO_CALIBRATION_MAX_AXIS_SPREAD_RAD = math.radians(35.0)

# Empirical correction from YOLO/PnP object datum to the simulator's SFP port
# TF frame. Initial calibration from GT comparison:
# raw=[-0.4495, 0.2109, 0.1911], gt=[-0.3844, 0.2129, 0.1335].
_YOLO_PORT_BIAS_M = {
    CLASS_SFP: np.array([0.0652, 0.0020, -0.0576], dtype=float),
}
_YOLO_SFP_AXIS_M = np.array([0.0, 0.0, -1.0], dtype=float)
_YOLO_SFP_ENTRANCE_OFFSET_M = 0.0458


# ── Geometry helpers — copied verbatim from InsertionDataCollector ────────────

def _quat_to_rot(q):
    x, y, z, w = q
    return np.array([
        [1 - 2*(y*y + z*z),   2*(x*y - w*z),   2*(x*z + w*y)],
        [    2*(x*y + w*z), 1 - 2*(x*x + z*z),   2*(y*z - w*x)],
        [    2*(x*z - w*y),   2*(y*z + w*x), 1 - 2*(x*x + y*y)],
    ])


def _axis_align_error(cur_axis: np.ndarray, des_axis: np.ndarray) -> np.ndarray:
    """Smallest axis-angle correction that rotates cur_axis onto des_axis."""
    cur = np.asarray(cur_axis, dtype=float)
    des = np.asarray(des_axis, dtype=float)
    cur /= max(np.linalg.norm(cur), 1e-9)
    des /= max(np.linalg.norm(des), 1e-9)
    v = np.cross(cur, des)
    s = float(np.linalg.norm(v))
    c = float(np.clip(np.dot(cur, des), -1.0, 1.0))
    if s < 1e-6:
        return np.zeros(3)
    return (v / s) * math.atan2(s, c)


# ── Policy root resolution ────────────────────────────────────────────────────

def _find_policy_root() -> Path:
    env_policy_root = os.environ.get("MY_POLICY_NODE_POLICY_ROOT")
    if env_policy_root:
        candidate = Path(env_policy_root).expanduser()
        if candidate.is_dir():
            return candidate

    candidate = Path(__file__).resolve().parent.parent / "policy"
    if candidate.is_dir():
        return candidate

    for parent in (Path.cwd().resolve(), *Path.cwd().resolve().parents):
        candidate = parent / "my_policy_node" / "policy"
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
        "Set MY_POLICY_NODE_POLICY_ROOT or run from a workspace containing "
        "my_policy_node/policy."
    )


def _declare_or_get(parent_node: Node, name: str, default):
    try:
        parent_node.declare_parameter(name, default)
    except Exception:
        pass
    return parent_node.get_parameter(name).value


def _as_bool(value) -> bool:
    if isinstance(value, str):
        return value.strip().lower() in {"1", "true", "yes", "on"}
    return bool(value)


_POLICY_ROOT = _find_policy_root()
_DEFAULT_PRETRAINED = (
    _POLICY_ROOT
    / "sfp_insertion_demos_act_20260504_184125_steplast"
    / "pretrained_model"
)


def _looks_like_git_lfs_pointer(path: Path) -> bool:
    try:
        with open(path, "rb") as f:
            header = f.read(128)
    except OSError:
        return False
    return header.startswith(b"version https://git-lfs.github.com/spec/")


def _validate_safetensors_files(policy_path: Path) -> None:
    required_files = [
        policy_path / "model.safetensors",
        policy_path / "policy_preprocessor_step_3_normalizer_processor.safetensors",
    ]
    missing = [path for path in required_files if not path.is_file()]
    if missing:
        raise FileNotFoundError(
            "SFPInsertionPolicy checkpoint is incomplete; missing: "
            + ", ".join(str(path) for path in missing)
        )

    lfs_pointers = [path for path in required_files if _looks_like_git_lfs_pointer(path)]
    if lfs_pointers:
        raise RuntimeError(
            "SFPInsertionPolicy checkpoint files are Git LFS pointer files, not "
            "downloaded safetensors weights: "
            + ", ".join(str(path) for path in lfs_pointers)
            + ". From the repository root, install Git LFS if needed and run: "
            "git lfs pull --include='my_policy_node/policy/**'"
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
        self._port_pos: Optional[np.ndarray] = None                    # updated by _gt_approach
        self.policy: Optional[ACTPolicy] = None
        self._act_available = False

        policy_path = self._resolve_policy_path()
        self.get_logger().info(f"SFPInsertionPolicy: loading from {policy_path}")
        try:
            _validate_safetensors_files(policy_path)

            with open(policy_path / "config.json") as f:
                config_dict = json.load(f)
            config_dict.pop("type", None)

            config = draccus.decode(ACTConfig, config_dict)
            self.policy = ACTPolicy(config)
            self.policy.load_state_dict(load_file(policy_path / "model.safetensors"))
            self.policy.eval()
            self.policy.to(self.device)

            self.get_logger().info(
                f"ACT policy ready on {self.device}  ({policy_path.parent.name})"
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
            self._act_available = True
            self.get_logger().info("Normalization statistics loaded.")
        except Exception as exc:
            self.get_logger().warn(
                "ACT safetensors policy is unavailable; continuing with "
                f"YOLO/servo insertion fallback. Reason: {exc}"
            )
        self._image_scale = 0.25

        self._tare_cli = parent_node.create_client(
            Trigger, "/aic_controller/tare_force_torque_sensor"
        )

        # ── Ground-truth flag ─────────────────────────────────────────────
        try:
            self._use_gt = bool(parent_node.get_parameter("ground_truth").value)
        except Exception:
            try:
                parent_node.declare_parameter("ground_truth", True)
                self._use_gt = bool(parent_node.get_parameter("ground_truth").value)
            except Exception:
                self._use_gt = True
        self.get_logger().info(f"SFPInsertionPolicy: use_gt={self._use_gt}")

        # ── YOLO / PnP runtime parameters ────────────────────────────────
        self._yolo_approach_standoff_m = max(
            0.0,
            float(_declare_or_get(parent_node, "yolo_approach_standoff_m", 0.100)),
        )
        self._yolo_handoff_standoff_m = max(
            0.0,
            float(_declare_or_get(parent_node, "yolo_handoff_standoff_m", 0.010)),
        )
        self._yolo_sc_handoff_standoff_m = max(
            0.0,
            float(_declare_or_get(parent_node, "yolo_sc_handoff_standoff_m", 0.010)),
        )
        self._yolo_focal_length_px = float(
            _declare_or_get(parent_node, "yolo_focal_length_px", 0.0)
        )
        self._yolo_device = str(
            _declare_or_get(parent_node, "yolo_device", "cpu")
        )
        self._yolo_imgsz = int(
            _declare_or_get(parent_node, "yolo_imgsz", 640)
        )
        self._yolo_min_conf = float(
            _declare_or_get(parent_node, "yolo_min_conf", 0.40)
        )
        self._yolo_kpt_conf = float(
            _declare_or_get(parent_node, "yolo_keypoint_conf", 0.30)
        )
        self._yolo_ransac_reproj_px = float(
            _declare_or_get(parent_node, "yolo_ransac_reproj_error_px", 6.0)
        )
        self._yolo_refine_after_approach = _as_bool(
            _declare_or_get(parent_node, "yolo_refine_after_approach", True)
        )
        self._yolo_approach_max_speed_mps = max(
            0.005,
            float(_declare_or_get(parent_node, "yolo_approach_max_speed_mps", 0.05)),
        )
        focal_msg = (
            f"{self._yolo_focal_length_px:.1f}px"
            if self._yolo_focal_length_px > 0.0
            else "CameraInfo"
        )
        self.get_logger().info(
            "SFPInsertionPolicy YOLO params: "
            f"visual_standoff={self._yolo_approach_standoff_m*1000:.0f}mm "
            f"sfp_handoff_standoff={self._yolo_handoff_standoff_m*1000:.0f}mm "
            f"sc_handoff_standoff={self._yolo_sc_handoff_standoff_m*1000:.0f}mm "
            f"focal={focal_msg} "
            f"device={self._yolo_device} "
            f"imgsz={self._yolo_imgsz} "
            f"refine={self._yolo_refine_after_approach}"
        )

        # TF broadcaster — used to publish YOLO-estimated debug frames
        self._tf_pub = TransformBroadcaster(parent_node)

        # Marker publisher — sphere + arrow for RViz YOLO detection overlay
        self._marker_pub = parent_node.create_publisher(
            MarkerArray, "/aic/yolo_detections", 10
        )
        self._debug_transforms: list[TransformStamped] = []
        self._debug_markers = MarkerArray()
        self._debug_pub_timer = parent_node.create_timer(0.25, self._republish_debug_pose)

        # ── YOLO port-pose detector (optional) ───────────────────────────
        self._pose_detector: Optional[PortPoseDetector] = None
        model_path = PortPoseDetector.find_model()
        cad_keypoints_path = PortPoseDetector.find_cad_keypoints()
        if model_path is not None:
            try:
                self._pose_detector = PortPoseDetector(
                    model_path,
                    cad_keypoints_path=cad_keypoints_path,
                    conf_thresh=self._yolo_min_conf,
                    keypoint_conf_thresh=self._yolo_kpt_conf,
                    ransac_reproj_error_px=self._yolo_ransac_reproj_px,
                    device=self._yolo_device,
                    imgsz=self._yolo_imgsz,
                )
                self.get_logger().info(
                    f"SFPInsertionPolicy: YOLO pose model loaded from {model_path}"
                    + (
                        f" with CAD keypoints {cad_keypoints_path}"
                        if cad_keypoints_path is not None
                        else ""
                    )
                )
            except Exception as exc:
                self.get_logger().warn(
                    f"SFPInsertionPolicy: failed to load YOLO pose model: {exc}"
                )
        else:
            self.get_logger().warn(
                "SFPInsertionPolicy: YOLO pose model not found — "
                "YOLO-based approach will be disabled"
            )

    def _republish_debug_pose(self) -> None:
        """Keep YOLO/GT debug TF and markers visible for late RViz subscribers."""
        if self._debug_transforms:
            now = self.get_clock().now().to_msg()
            for tf in self._debug_transforms:
                tf.header.stamp = now
                self._tf_pub.sendTransform(tf)
        if self._debug_markers.markers:
            now = self.get_clock().now().to_msg()
            for marker in self._debug_markers.markers:
                marker.header.stamp = now
            self._marker_pub.publish(self._debug_markers)

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
        dist_m: float = _BACKOFF_SHORT_M,
    ) -> None:
        """Pull back along the reverse insertion axis to clear a stuck position."""
        backoff_vel = -self._insertion_axis * _BACKOFF_SPEED_MPS
        dur = dist_m / _BACKOFF_SPEED_MPS
        self.get_logger().info(
            f"Backoff: {dist_m*1000:.0f} mm along "
            f"{(-self._insertion_axis).round(3)} for {dur:.2f}s"
        )
        send_feedback(f"Backing off {dist_m*1000:.0f} mm...")
        t0 = time.time()
        while time.time() - t0 < dur:
            self._send_cmd(move_robot, backoff_vel)
            self.sleep_for(0.05)
        self._stop(move_robot)
        self.sleep_for(0.1)

    def _wiggle_entry(
        self,
        move_robot: MoveRobotCallback,
        send_feedback: SendFeedbackCallback,
    ) -> bool:
        """
        Position plug 1 mm above the entrance, then apply a circular oscillation
        perpendicular to the insertion axis with a gentle axial push until the plug
        enters the close-range zone (_CLOSE_THRESH_M).  Returns True on entry.
        """
        # Position plug right at entrance before wiggling
        self._gt_approach(
            self._task, move_robot, send_feedback, z_above=_WIGGLE_Z_ABOVE
        )
        self.sleep_for(0.2)

        # Build two orthogonal vectors in the plane perpendicular to axis
        axis = self._insertion_axis
        ref = np.array([1.0, 0.0, 0.0]) if abs(axis[0]) < 0.9 else np.array([0.0, 1.0, 0.0])
        perp1 = np.cross(axis, ref)
        perp1 /= np.linalg.norm(perp1)
        perp2 = np.cross(axis, perp1)

        plug_frames = [
            f"{self._task.cable_name}/{self._task.plug_name}_link",
            f"{self._task.cable_name}/{self._task.plug_name}",
        ]

        send_feedback("Wiggle entry: searching for port...")
        w = 2.0 * math.pi * _WIGGLE_FREQ_HZ
        t0 = time.time()

        while time.time() - t0 < _WIGGLE_TIMEOUT_S:
            t = time.time() - t0

            # Check if plug has entered close-range zone
            plug_pos = None
            for frame in plug_frames:
                plug_pos = self._lookup_pos(frame)
                if plug_pos is not None:
                    break
            if plug_pos is not None and self._port_pos is not None:
                dist = float(np.dot(self._port_pos - plug_pos, axis))
                if dist <= _CLOSE_THRESH_M:
                    self._stop(move_robot)
                    self.get_logger().info(
                        f"Wiggle entry succeeded  dist={dist*1000:.1f}mm"
                    )
                    return True

            # Circular wiggle velocity (derivative of circular position)
            wig_vel = _WIGGLE_AMP_M * w * (
                -math.sin(w * t) * perp1 + math.cos(w * t) * perp2
            )
            lin = axis * _WIGGLE_PUSH_MPS + wig_vel
            self._send_cmd(move_robot, lin)
            self.sleep_for(0.05)

        self._stop(move_robot)
        self.get_logger().warn("Wiggle entry timed out")
        return False

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

    # ── GT approach ───────────────────────────────────────────────────────

    def _gt_approach(
        self,
        task: Task,
        move_robot: MoveRobotCallback,
        send_feedback: SendFeedbackCallback,
        z_above: float = _APPROACH_Z_ABOVE,
    ) -> bool:
        """
        Simultaneously corrects position and connector-axis orientation using
        KP velocity control.

        Position target: entrance_pos - axis * APPROACH_Z_ABOVE  (8 mm before entrance)
        Orientation target: plug insertion axis aligned to port insertion axis
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
        target = entrance_pos - axis * z_above
        port_axis_idx = 2
        port_axis_sign = 1.0
        if port_R is not None:
            axis_in_port = port_R.T @ axis
            port_axis_idx = int(np.argmax(np.abs(axis_in_port)))
            port_axis_sign = 1.0 if axis_in_port[port_axis_idx] >= 0.0 else -1.0

        self._port_pos = port_pos   # used by _act_phase for close-range detection

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
                # Fall back to TCP frame (always available from robot controller)
                plug_pos, plug_R = self._lookup_pos_rot("gripper/tcp")
                if plug_pos is None:
                    self.sleep_for(0.1)
                    continue

            pos_err = target - plug_pos
            omega = (
                _axis_align_error(plug_R[:, port_axis_idx] * port_axis_sign, axis)
                if (plug_R is not None and port_R is not None)
                else np.zeros(3)
            )

            lin_vel = _APPROACH_KP * pos_err
            ang_vel = _APPROACH_AXIS_ORIENT_KP * omega
            ang_speed = float(np.linalg.norm(ang_vel))
            if ang_speed > _APPROACH_AXIS_MAX_ANG_VEL:
                ang_vel = ang_vel / ang_speed * _APPROACH_AXIS_MAX_ANG_VEL
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

    # ── YOLO TF helpers ───────────────────────────────────────────────────

    @staticmethod
    def _rot_to_quat(R: np.ndarray):
        """Rotation matrix → (x, y, z, w) quaternion via Shepperd's method."""
        trace = R[0, 0] + R[1, 1] + R[2, 2]
        if trace > 0:
            s = 0.5 / math.sqrt(trace + 1.0)
            w = 0.25 / s
            x = (R[2, 1] - R[1, 2]) * s
            y = (R[0, 2] - R[2, 0]) * s
            z = (R[1, 0] - R[0, 1]) * s
        elif R[0, 0] > R[1, 1] and R[0, 0] > R[2, 2]:
            s = 2.0 * math.sqrt(1.0 + R[0, 0] - R[1, 1] - R[2, 2])
            w = (R[2, 1] - R[1, 2]) / s
            x = 0.25 * s
            y = (R[0, 1] + R[1, 0]) / s
            z = (R[0, 2] + R[2, 0]) / s
        elif R[1, 1] > R[2, 2]:
            s = 2.0 * math.sqrt(1.0 + R[1, 1] - R[0, 0] - R[2, 2])
            w = (R[0, 2] - R[2, 0]) / s
            x = (R[0, 1] + R[1, 0]) / s
            y = 0.25 * s
            z = (R[1, 2] + R[2, 1]) / s
        else:
            s = 2.0 * math.sqrt(1.0 + R[2, 2] - R[0, 0] - R[1, 1])
            w = (R[1, 0] - R[0, 1]) / s
            x = (R[0, 2] + R[2, 0]) / s
            y = (R[1, 2] + R[2, 1]) / s
            z = 0.25 * s
        return float(x), float(y), float(z), float(w)

    def _publish_yolo_tfs(
        self,
        port_frame: str,
        entrance_frame: str,
        port_pos: np.ndarray,
        ins_axis: np.ndarray,
        cam_R: np.ndarray,
        conf: float = 1.0,
        *,
        frame_prefix: str = "yolo",
        marker_ns: str = "yolo",
        color: tuple = (1.0, 0.6, 0.0),
        publish_tf: bool = True,
    ) -> None:
        """
        Publish port and entrance TF frames estimated from YOLO detection,
        plus RViz markers (sphere at port centre, arrow along insertion axis).

        Port orientation is approximated as the camera frame (ports face the
        camera squarely during manipulation).  Entrance is placed 2 cm in
        front of the port along the insertion axis.
        """
        now = self.get_clock().now().to_msg()
        qx, qy, qz, qw = self._rot_to_quat(cam_R)
        entrance_pos = port_pos - ins_axis * 0.02
        if frame_prefix:
            port_frame = f"{frame_prefix}/{port_frame}"
            entrance_frame = f"{frame_prefix}/{entrance_frame}"

        transforms = []
        if publish_tf:
            for child_id, pos in [
                (port_frame,     port_pos),
                (entrance_frame, entrance_pos),
            ]:
                tf = TransformStamped()
                tf.header.stamp = now
                tf.header.frame_id = "base_link"
                tf.child_frame_id = child_id
                tf.transform.translation.x = float(pos[0])
                tf.transform.translation.y = float(pos[1])
                tf.transform.translation.z = float(pos[2])
                tf.transform.rotation.x = qx
                tf.transform.rotation.y = qy
                tf.transform.rotation.z = qz
                tf.transform.rotation.w = qw
                transforms.append(tf)
            child_ids = {tf.child_frame_id for tf in transforms}
            self._debug_transforms = [
                tf for tf in self._debug_transforms
                if tf.child_frame_id not in child_ids
            ] + transforms
            for tf in transforms:
                self._tf_pub.sendTransform(tf)

        # ── RViz markers ─────────────────────────────────────────────────
        markers = MarkerArray()

        # Sphere at estimated port centre
        sphere = Marker()
        sphere.header.stamp = now
        sphere.header.frame_id = "base_link"
        sphere.ns = f"{marker_ns}_port"
        sphere.id = 0
        sphere.type = Marker.SPHERE
        sphere.action = Marker.ADD
        sphere.pose.position.x = float(port_pos[0])
        sphere.pose.position.y = float(port_pos[1])
        sphere.pose.position.z = float(port_pos[2])
        sphere.pose.orientation.w = 1.0
        sphere.scale.x = sphere.scale.y = sphere.scale.z = 0.015  # 15 mm sphere
        sphere.color.r = float(color[0])
        sphere.color.g = float(color[1])
        sphere.color.b = float(color[2])
        sphere.color.a = 0.85
        sphere.lifetime.sec = 0
        markers.markers.append(sphere)

        # Arrow along insertion axis (entrance → port)
        arrow = Marker()
        arrow.header.stamp = now
        arrow.header.frame_id = "base_link"
        arrow.ns = f"{marker_ns}_axis"
        arrow.id = 1
        arrow.type = Marker.ARROW
        arrow.action = Marker.ADD
        # Arrow defined by two points: entrance → port
        from geometry_msgs.msg import Point
        p0, p1 = Point(), Point()
        p0.x, p0.y, p0.z = float(entrance_pos[0]), float(entrance_pos[1]), float(entrance_pos[2])
        p1.x, p1.y, p1.z = float(port_pos[0]),     float(port_pos[1]),     float(port_pos[2])
        arrow.points = [p0, p1]
        arrow.scale.x = 0.004  # shaft diameter
        arrow.scale.y = 0.008  # head diameter
        arrow.scale.z = 0.005  # head length
        arrow.color.r = float(color[0])
        arrow.color.g = float(color[1])
        arrow.color.b = float(color[2])
        arrow.color.a = 0.9
        arrow.lifetime.sec = 0
        markers.markers.append(arrow)

        namespaces = {marker.ns for marker in markers.markers}
        self._debug_markers.markers = [
            marker for marker in self._debug_markers.markers
            if marker.ns not in namespaces
        ] + markers.markers
        self._marker_pub.publish(markers)

    def _publish_gt_markers(self, port_pos: np.ndarray, entrance_pos: np.ndarray) -> None:
        """Publish GT port/axis markers for direct RViz comparison with YOLO."""
        delta = port_pos - entrance_pos
        dlen = np.linalg.norm(delta)
        if dlen < 1e-6:
            return
        self._publish_yolo_tfs(
            "gt_port_marker",
            "gt_port_marker_entrance",
            port_pos,
            delta / dlen,
            np.eye(3),
            1.0,
            frame_prefix="debug",
            marker_ns="gt",
            color=(0.0, 1.0, 0.1),
            publish_tf=False,
        )

    def _yolo_detect_tf(
        self,
        target_class: int,
        port_frame: str,
        entrance_frame: str,
        get_observation: GetObservationCallback,
        send_feedback: SendFeedbackCallback,
        timeout_sec: float = 10.0,
        min_conf: float = 0.70,
    ) -> bool:
        """
        Detect the target port with YOLO and publish its pose as debug TF
        frames and markers. Does NOT move the robot.

        Returns True once a detection with confidence ≥ min_conf is found
        (or the best detection seen before timeout_sec).
        """
        if self._pose_detector is None:
            return False

        t0 = time.time()
        best_conf:      float            = 0.0
        best_score:     tuple            = (-1, -1, -1.0, -1.0, float("-inf"))
        best_port_pos:  Optional[np.ndarray] = None
        best_ins_axis:  Optional[np.ndarray] = None
        best_cam_R:     Optional[np.ndarray] = None
        best_cam_name:  str              = "unknown"

        while time.time() - t0 < timeout_sec:
            obs = get_observation()
            if obs is None:
                self.sleep_for(0.1)
                continue

            det, port_pos, ins_axis, cam_R, cam_name = \
                self._best_detection_all_cameras(obs, target_class)

            if det is None:
                self.sleep_for(0.1)
                continue

            conf = det["conf"]
            raw_msg = ""
            if "raw_port_pos" in det:
                raw_msg = f" raw={det['raw_port_pos'].round(3)}"
            kp_msg = (
                f" kp={det.get('pnp_valid_points', 0)}"
                f"/{det.get('pnp_inliers', 0)}"
                f" kpconf={det.get('pnp_mean_kp_conf', 0.0):.2f}"
                f" reproj={det.get('pnp_reprojection_error_px', float('nan')):.1f}px"
            )
            send_feedback(
                f"YOLO({cam_name}) cls={det['class_id']} conf={conf:.2f} "
                f"{kp_msg} pos={port_pos.round(3)}{raw_msg}"
            )

            score = det.get("selection_score", self._yolo_selection_score(det))
            if score > best_score:
                best_score    = score
                best_conf     = conf
                best_port_pos = port_pos
                best_ins_axis = ins_axis
                best_cam_R    = cam_R
                best_cam_name = cam_name

            # Publish TF immediately so RViz shows it while scanning
            self._publish_yolo_tfs(
                port_frame, entrance_frame, port_pos, ins_axis, cam_R, conf
            )

            if conf >= min_conf:
                break   # good enough — stop early

            self.sleep_for(0.05)

        if best_port_pos is None:
            self.get_logger().warn(
                f"YOLO: no detection for class={target_class} within {timeout_sec:.0f}s"
            )
            return False

        # Publish the best estimate as a final debug TF + marker
        self._publish_yolo_tfs(
            port_frame, entrance_frame, best_port_pos, best_ins_axis, best_cam_R, best_conf
        )
        self._port_pos       = best_port_pos
        self._insertion_axis = best_ins_axis

        self.get_logger().info(
            f"PnP pose accepted: yolo/{port_frame}  cam={best_cam_name}  "
            f"conf={best_conf:.2f}  pos={best_port_pos.round(3)}  "
            f"axis={best_ins_axis.round(3)}"
        )
        return True

    def _publish_yolo_gt_comparison(
        self,
        task: Task,
        target_class: int,
        port_frame: str,
        entrance_frame: str,
        get_observation: GetObservationCallback,
        send_feedback: SendFeedbackCallback,
    ) -> None:
        """
        When GT TF exists, publish both GT and YOLO estimates and log the error.

        This intentionally does not feed the YOLO result into the controller.
        It is a diagnostics path so bad PnP estimates are visible without moving
        the arm toward them.
        """
        gt_port, _ = self._lookup_pos_rot(port_frame)
        gt_entrance = self._lookup_pos(entrance_frame)
        if gt_port is None or gt_entrance is None:
            return

        self._publish_gt_markers(gt_port, gt_entrance)
        if self._pose_detector is None:
            return

        saved_port = None if self._port_pos is None else self._port_pos.copy()
        saved_axis = None if self._insertion_axis is None else self._insertion_axis.copy()
        ok = self._yolo_detect_tf(
            target_class,
            port_frame,
            entrance_frame,
            get_observation,
            send_feedback,
            timeout_sec=2.0,
            min_conf=0.95,
        )
        if not ok or self._port_pos is None:
            self._port_pos = saved_port
            self._insertion_axis = saved_axis
            return

        yolo_port = self._port_pos.copy()
        err = yolo_port - gt_port
        raw_note = ""
        if _YOLO_PORT_BIAS_M.get(target_class) is not None:
            raw_yolo = yolo_port - _YOLO_PORT_BIAS_M[target_class]
            raw_err = raw_yolo - gt_port
            raw_note = (
                f" raw_dx={raw_err[0]*1000:.1f}mm"
                f" raw_dy={raw_err[1]*1000:.1f}mm"
                f" raw_dz={raw_err[2]*1000:.1f}mm"
                f" raw_norm={np.linalg.norm(raw_err)*1000:.1f}mm"
            )
        self.get_logger().warn(
            "YOLO vs GT port error "
            f"task={task.target_module_name}/{task.port_name} "
            f"dx={err[0]*1000:.1f}mm dy={err[1]*1000:.1f}mm "
            f"dz={err[2]*1000:.1f}mm norm={np.linalg.norm(err)*1000:.1f}mm "
            f"gt={gt_port.round(4)} yolo={yolo_port.round(4)}{raw_note}"
        )

        self._port_pos = saved_port
        self._insertion_axis = saved_axis

    # ── YOLO-based approach (no ground-truth TF required) ────────────────

    def _camera_matrix_for_yolo(self, camera_info) -> np.ndarray:
        K = np.array(camera_info.k, dtype=np.float64).reshape(3, 3)
        if self._yolo_focal_length_px > 0.0:
            K[0, 0] = self._yolo_focal_length_px
            K[1, 1] = self._yolo_focal_length_px
        return K

    @staticmethod
    def _yolo_selection_score(det: dict) -> tuple:
        return (
            int(det.get("pnp_valid_points", 0)),
            int(det.get("pnp_inliers", 0)),
            float(det.get("pnp_mean_kp_conf", 0.0)),
            float(det.get("conf", 0.0)),
            -float(det.get("pnp_reprojection_error_px", 1e9)),
        )

    def _best_detection_all_cameras(
        self,
        obs,
        target_class: int,
    ):
        """
        Run YOLO on all three cameras and return the best PnP-ready detection.

        Selection prefers the camera/detection with the most usable CAD-matched
        keypoints, then the most PnP inliers, then the strongest keypoint
        confidence. Box confidence is only a later tie-breaker.

        Returns (det, port_pos, ins_axis, cam_R, cam_name) or
                (None, None, None, None, None) when nothing is detected.
        """
        cameras = [
            ("center", obs.center_camera_info, obs.center_image),
            ("left",   obs.left_camera_info,   obs.left_image),
            ("right",  obs.right_camera_info,  obs.right_image),
        ]
        best = (None, None, None, None, None)
        best_score = (-1, -1, -1.0, -1.0, float("-inf"))

        for cam_name, ci, img_msg in cameras:
            if ci.width == 0 or not any(ci.k):
                continue
            K         = self._camera_matrix_for_yolo(ci)
            D         = np.array(ci.d, dtype=np.float64) if ci.d else None
            cam_frame = ci.header.frame_id
            img_w, img_h = img_msg.width, img_msg.height

            cam_pos, cam_R = self._lookup_pos_rot(cam_frame)
            if cam_pos is None:
                continue

            img_np = np.frombuffer(
                img_msg.data, dtype=np.uint8
            ).reshape(img_h, img_w, 3)
            dets = self._pose_detector.detect(img_np)
            for det in dets:
                if int(det["class_id"]) != int(target_class):
                    continue

                port_pos, ins_axis = self._pose_detector.estimate_port_3d(
                    det, K, cam_pos, cam_R, img_w, img_h, D
                )
                if port_pos is None:
                    continue
                raw_port_pos = port_pos.copy()
                bias = _YOLO_PORT_BIAS_M.get(target_class)
                if bias is not None:
                    port_pos = port_pos + bias
                    det["raw_port_pos"] = raw_port_pos
                    det["bias_m"] = bias

                det["camera_name"] = cam_name
                det["selection_score"] = self._yolo_selection_score(det)
                if det["selection_score"] > best_score:
                    best_score = det["selection_score"]
                    best = (det, port_pos, ins_axis, cam_R, cam_name)

        return best

    def _move_tcp_delta(
        self,
        get_observation: GetObservationCallback,
        move_robot: MoveRobotCallback,
        delta: np.ndarray,
        timeout_sec: float = 3.0,
        done_m: float = 0.0015,
    ) -> bool:
        obs0 = get_observation()
        if obs0 is None:
            return False
        p0 = obs0.controller_state.tcp_pose.position
        target = np.array([p0.x, p0.y, p0.z], dtype=float) + np.asarray(delta, dtype=float)

        t0 = time.time()
        while time.time() - t0 < timeout_sec:
            obs = get_observation()
            if obs is None:
                self.sleep_for(0.05)
                continue
            p = obs.controller_state.tcp_pose.position
            tcp_pos = np.array([p.x, p.y, p.z], dtype=float)
            err = target - tcp_pos
            if float(np.linalg.norm(err)) < done_m:
                self._stop(move_robot)
                return True

            lin_vel = _APPROACH_KP * err
            lin_speed = float(np.linalg.norm(lin_vel))
            if lin_speed > self._yolo_approach_max_speed_mps:
                lin_vel = lin_vel / lin_speed * self._yolo_approach_max_speed_mps
            self._send_cmd(move_robot, lin_vel)
            self.sleep_for(1.0 / 20)

        self._stop(move_robot)
        return False

    def _yolo_pose_sample(self, get_observation: GetObservationCallback, target_class: int):
        obs = get_observation()
        if obs is None:
            return None
        det, port_pos, ins_axis, cam_R, cam_name = self._best_detection_all_cameras(
            obs, target_class
        )
        if det is None or port_pos is None or ins_axis is None:
            return None
        axis = np.asarray(ins_axis, dtype=float)
        axis /= max(np.linalg.norm(axis), 1e-9)
        return {
            "det": det,
            "port_pos": np.asarray(port_pos, dtype=float),
            "ins_axis": axis,
            "cam_R": cam_R,
            "cam_name": cam_name,
        }

    def _yolo_probe_axis(self, get_observation: GetObservationCallback) -> np.ndarray:
        obs = get_observation()
        if obs is not None and obs.center_camera_info.header.frame_id:
            _, cam_R = self._lookup_pos_rot(obs.center_camera_info.header.frame_id)
            if cam_R is not None:
                axis = np.asarray(cam_R[:, 0], dtype=float)
                axis[2] = 0.0
                norm = float(np.linalg.norm(axis))
                if norm > 1e-6:
                    return axis / norm
        return np.array([1.0, 0.0, 0.0], dtype=float)

    def _calibrate_yolo_pose_probe(
        self,
        target_class: int,
        port_frame: str,
        entrance_frame: str,
        get_observation: GetObservationCallback,
        move_robot: MoveRobotCallback,
        send_feedback: SendFeedbackCallback,
    ) -> bool:
        if self._pose_detector is None:
            return False

        send_feedback("YOLO calibration: probing keypoints left/right...")
        probe_axis = self._yolo_probe_axis(get_observation)
        probe = probe_axis * _YOLO_CALIBRATION_PROBE_M

        samples = []
        first = self._yolo_pose_sample(get_observation, target_class)
        if first is not None:
            samples.append(first)

        moves = (probe, -2.0 * probe, probe)
        labels = ("right", "left", "center")
        current_offset = np.zeros(3, dtype=float)
        for label, delta in zip(labels, moves):
            if not self._move_tcp_delta(get_observation, move_robot, delta):
                self.get_logger().warn(f"YOLO calibration probe move failed at {label}")
                break
            current_offset += delta
            self.sleep_for(0.15)
            sample = self._yolo_pose_sample(get_observation, target_class)
            if sample is not None:
                samples.append(sample)
        if float(np.linalg.norm(current_offset)) > 5e-4:
            self._move_tcp_delta(get_observation, move_robot, -current_offset)
            self.sleep_for(0.15)
            sample = self._yolo_pose_sample(get_observation, target_class)
            if sample is not None:
                samples.append(sample)

        if len(samples) < 2:
            self.get_logger().warn("YOLO calibration: not enough PnP samples")
            send_feedback("YOLO calibration failed: not enough stable detections")
            return False

        positions = np.stack([s["port_pos"] for s in samples], axis=0)
        median_pos = np.median(positions, axis=0)
        pos_spread = float(np.max(np.linalg.norm(positions - median_pos, axis=1)))
        z_spread = float(np.ptp(positions[:, 2]))
        axes = np.stack([s["ins_axis"] for s in samples], axis=0)
        ref_axis = axes[0].copy()
        for i in range(len(axes)):
            if float(np.dot(axes[i], ref_axis)) < 0.0:
                axes[i] *= -1.0
        mean_axis = np.mean(axes, axis=0)
        mean_axis /= max(np.linalg.norm(mean_axis), 1e-9)
        axis_spread = float(
            max(
                math.acos(float(np.clip(np.dot(axis, mean_axis), -1.0, 1.0)))
                for axis in axes
            )
        )

        self.get_logger().info(
            "YOLO calibration samples: "
            f"n={len(samples)} pos_spread={pos_spread*1000:.1f}mm "
            f"z_spread={z_spread*1000:.1f}mm "
            f"axis_spread={math.degrees(axis_spread):.1f}deg "
            f"median={median_pos.round(4)} axis={mean_axis.round(4)}"
        )

        if (
            pos_spread > _YOLO_CALIBRATION_MAX_POS_SPREAD_M
            or z_spread > _YOLO_CALIBRATION_MAX_Z_SPREAD_M
            or axis_spread > _YOLO_CALIBRATION_MAX_AXIS_SPREAD_RAD
        ):
            self.get_logger().error(
                "Rejecting YOLO handoff: calibration samples disagree "
                f"(pos_spread={pos_spread*1000:.1f}mm, "
                f"z_spread={z_spread*1000:.1f}mm, "
                f"axis_spread={math.degrees(axis_spread):.1f}deg)"
            )
            send_feedback("YOLO calibration rejected unstable PnP pose")
            return False

        best_i = int(np.argmin(np.linalg.norm(positions - median_pos, axis=1)))
        best = samples[best_i]
        self._port_pos = median_pos
        self._insertion_axis = mean_axis
        self._publish_yolo_tfs(
            port_frame,
            entrance_frame,
            self._port_pos,
            self._insertion_axis,
            best["cam_R"],
            float(best["det"].get("conf", 0.0)),
        )
        send_feedback(
            f"YOLO calibration ok: spread={pos_spread*1000:.0f}mm "
            f"z={z_spread*1000:.0f}mm"
        )
        return True

    def _approach_to_yolo_pos(
        self,
        get_observation: GetObservationCallback,
        move_robot: MoveRobotCallback,
        send_feedback: SendFeedbackCallback,
        target_class: int,
        standoff_m: float = 0.04,    # metres in front of port along insertion axis
        timeout_sec: float = 25.0,
        done_m: float = 0.008,       # 8 mm position tolerance
    ) -> bool:
        """
        Move TCP to the YOLO-estimated approach position using observation-based
        TCP pose (always available — no TF lookup required).

        Approach target = port_pos - insertion_axis * standoff_m
        (i.e. standoff_m before the port along the direction you insert from).
        """
        if self._port_pos is None or self._insertion_axis is None:
            self.get_logger().warn("_approach_to_yolo_pos: no YOLO estimate available")
            return False

        axis = self._insertion_axis
        entrance_pos = self._port_pos
        if target_class == CLASS_SFP:
            # The corrected YOLO point is aligned to the simulator's SFP port
            # TF, not the entrance TF. Mirror GT approach:
            # entrance = port - axis * 45.8 mm, target = entrance - axis * standoff.
            axis = _YOLO_SFP_AXIS_M / np.linalg.norm(_YOLO_SFP_AXIS_M)
            entrance_pos = self._port_pos - axis * _YOLO_SFP_ENTRANCE_OFFSET_M
            self._insertion_axis = axis

        target = entrance_pos.copy()
        if abs(axis[2]) > 1e-3:
            # Align laterally to the detected port, but stop before the port in
            # depth instead of driving the TCP directly to the detected Z.
            target[2] = entrance_pos[2] - axis[2] * standoff_m
        else:
            target = entrance_pos - axis * standoff_m
        obs0 = get_observation()
        if obs0 is not None:
            p0 = obs0.controller_state.tcp_pose.position
            tcp0 = np.array([p0.x, p0.y, p0.z])
            target_delta = target - tcp0
            target_dist = float(np.linalg.norm(target_delta))
            vertical_step = float(target_delta[2])
            if (
                (target_dist > _YOLO_MAX_TARGET_DIST_M and vertical_step > 0.0)
                or vertical_step > _YOLO_MAX_UPWARD_STEP_M
                or vertical_step < -_YOLO_MAX_DOWNWARD_STEP_M
            ):
                self.get_logger().error(
                    "Rejecting YOLO approach target as implausible: "
                    f"tcp={tcp0.round(4)} target={target.round(4)} "
                    f"delta_mm={np.round(target_delta * 1000, 1)} "
                    f"dist={target_dist*1000:.1f}mm "
                    f"vertical={vertical_step*1000:.1f}mm"
                )
                send_feedback("YOLO PnP target rejected; skipping visual approach")
                return False

        self.get_logger().info(
            f">>> YOLO approach START  "
            f"port={self._port_pos.round(4)}  "
            f"entrance={entrance_pos.round(4)}  "
            f"axis={axis.round(4)}  "
            f"target={target.round(4)}  "
            f"standoff={standoff_m*1000:.1f}mm"
        )

        t0 = time.time()
        settled = 0

        while time.time() - t0 < timeout_sec:
            obs = get_observation()
            if obs is None:
                self.sleep_for(0.05)
                continue

            tcp = obs.controller_state.tcp_pose
            tcp_pos = np.array([
                tcp.position.x, tcp.position.y, tcp.position.z,
            ])

            pos_err = target - tcp_pos
            err_m = float(np.linalg.norm(pos_err))

            lin_vel = _APPROACH_KP * pos_err
            lin_speed = float(np.linalg.norm(lin_vel))
            if lin_speed > self._yolo_approach_max_speed_mps:
                lin_vel = lin_vel / lin_speed * self._yolo_approach_max_speed_mps
            self._send_cmd(move_robot, lin_vel)

            if int((time.time() - t0) * 5) % 5 == 0:
                send_feedback(
                    f"YOLO approach: err={err_m*1000:.0f}mm "
                    f"target=[{target[0]:.3f},{target[1]:.3f},{target[2]:.3f}]"
                )

            if err_m < done_m:
                settled += 1
                if settled >= 5:   # 0.5 s stable at 10 Hz
                    self._stop(move_robot)
                    self.get_logger().info(
                        f"YOLO pos-approach complete: err={err_m*1000:.1f}mm"
                    )
                    return True
            else:
                settled = 0

            self.sleep_for(1.0 / 10)

        self._stop(move_robot)
        self.get_logger().warn(
            f"YOLO pos-approach timeout after {timeout_sec:.0f}s — "
            "continuing from current position"
        )
        return False

    def _handoff_standoff_for_class(self, target_class: int) -> float:
        if target_class == CLASS_SC:
            return self._yolo_sc_handoff_standoff_m
        return self._yolo_handoff_standoff_m

    def _yolo_approach(
        self,
        target_class: int,
        get_observation: GetObservationCallback,
        move_robot: MoveRobotCallback,
        send_feedback: SendFeedbackCallback,
        port_frame: str = "",
        entrance_frame: str = "",
        z_above: float = _APPROACH_Z_ABOVE,
    ) -> bool:
        """
        Drive the TCP to a point z_above metres in front of the detected port.

        Scans all three cameras each iteration and picks the highest-confidence
        detection.  Publishes TF frames and RViz markers whenever a detection
        is found so the result is visible in RViz throughout the approach.

        Returns True when settled at the approach pose, False on timeout.
        """
        if self._pose_detector is None:
            return False

        settled   = 0
        no_detect = 0
        t0        = time.time()

        while time.time() - t0 < _APPROACH_TIMEOUT_S:
            obs = get_observation()
            if obs is None:
                continue

            det, port_pos, ins_axis, cam_R, cam_name = \
                self._best_detection_all_cameras(obs, target_class)

            if det is None:
                no_detect += 1
                if no_detect % 10 == 0:
                    send_feedback(
                        f"YOLO: no detection in any camera ({no_detect} frames)"
                    )
                self.sleep_for(0.1)
                continue
            no_detect = 0

            # Persist for ACT stall / done detection
            self._insertion_axis = ins_axis
            self._port_pos       = port_pos

            # Publish TF frames + RViz markers (static — persists between iterations)
            if port_frame:
                self._publish_yolo_tfs(
                    port_frame,
                    entrance_frame or port_frame + "_entrance",
                    port_pos, ins_axis, cam_R, det["conf"],
                )

            # KP position control toward approach target
            approach_target = port_pos - ins_axis * z_above
            tcp_pos, _ = self._lookup_pos_rot("gripper/tcp")
            if tcp_pos is None:
                self.sleep_for(0.1)
                continue

            pos_err = approach_target - tcp_pos
            self._send_cmd(move_robot, _APPROACH_KP * pos_err)

            pos_err_m = float(np.linalg.norm(pos_err))

            if int((time.time() - t0) * 5) % 10 == 0:
                send_feedback(
                    f"YOLO({cam_name}): cls={det['class_id']} "
                    f"conf={det['conf']:.2f} "
                    f"kp={det.get('pnp_valid_points', 0)}"
                    f"/{det.get('pnp_inliers', 0)} "
                    f"err={pos_err_m*1000:.0f}mm"
                )

            if pos_err_m < _APPROACH_DONE_M:
                settled += 1
                if settled >= _APPROACH_SETTLED_TICKS:
                    self._stop(move_robot)
                    self.get_logger().info(
                        f"YOLO approach settled — cam={cam_name} "
                        f"cls={det['class_id']} conf={det['conf']:.2f} "
                        f"err={pos_err_m*1000:.1f}mm"
                    )
                    return True
            else:
                settled = 0

            self.sleep_for(1.0 / 10)

        self._stop(move_robot)
        self.get_logger().warn("YOLO approach timed out")
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
        if self.policy is not None:
            self.policy.reset()
        self.get_logger().info(f"SFPInsertionPolicy.insert_cable() — {task}")
        self._tare()

        port_frame    = f"task_board/{task.target_module_name}/{task.port_name}_link"
        entrance_frame = port_frame + "_entrance"
        port_lower = task.port_name.lower()
        target_cls = CLASS_SC if "sc" in port_lower else CLASS_SFP

        # Check ground-truth TF availability (skip wait entirely when use_gt=False)
        if self._use_gt:
            has_gt = self._wait_for_tf("base_link", port_frame, timeout_sec=3.0)
        else:
            has_gt = False
            self.get_logger().info("ground_truth=false — skipping GT TF wait")

        if not has_gt:
            if self._pose_detector is not None:
                self.get_logger().info(
                    f"No GT TF — YOLO scan (class={target_cls}, all cameras, arm still)"
                )
                send_feedback("PnP: scanning cameras from current position...")

                # Phase 1 — detect port while arm is stationary (best position estimate)
                yolo_ok = self._yolo_detect_tf(
                    target_cls, port_frame, entrance_frame,
                    get_observation, send_feedback,
                )

                # Phase 2 — log current TCP, then approach to a safe visual
                # standoff. This gives the second PnP pass a larger target in
                # the image without jumping straight into the port.
                if yolo_ok:
                    # Log TCP vs port so we know how far the arm is from detection
                    obs0 = get_observation()
                    if obs0 is not None:
                        p = obs0.controller_state.tcp_pose.position
                        tcp_now = np.array([p.x, p.y, p.z])
                        self.get_logger().info(
                            f"TCP now:  [{tcp_now[0]:.4f}, {tcp_now[1]:.4f}, {tcp_now[2]:.4f}]"
                        )
                    self.get_logger().info(
                        f"Port est: {self._port_pos.round(4)}"
                    )
                    send_feedback(
                        f"YOLO port at {self._port_pos.round(3)} — "
                        f"approaching {self._yolo_approach_standoff_m*1000:.0f} mm standoff..."
                    )
                    approach_ok = self._approach_to_yolo_pos(
                        get_observation, move_robot, send_feedback,
                        target_class=target_cls,
                        standoff_m=self._yolo_approach_standoff_m,
                        timeout_sec=25.0,
                    )
                    if not approach_ok:
                        self.get_logger().error(
                            "YOLO approach failed or was rejected; refusing ACT "
                            "handoff because TCP is outside ACT start distribution."
                        )
                        send_feedback("YOLO approach failed — not starting ACT")
                        self._stop(move_robot)
                        return False

                    if self._yolo_refine_after_approach:
                        send_feedback("YOLO: refining pose from closer camera view...")
                        refined_ok = self._yolo_detect_tf(
                            target_cls,
                            port_frame,
                            entrance_frame,
                            get_observation,
                            send_feedback,
                            timeout_sec=3.0,
                            min_conf=self._yolo_min_conf,
                        )
                        if not refined_ok:
                            self.get_logger().warn(
                                "YOLO refine pass did not improve pose; keeping "
                                "the initial estimate"
                            )

                    calibrated_ok = self._calibrate_yolo_pose_probe(
                        target_cls,
                        port_frame,
                        entrance_frame,
                        get_observation,
                        move_robot,
                        send_feedback,
                    )
                    if not calibrated_ok:
                        self.get_logger().error(
                            "YOLO calibration failed; refusing handoff because "
                            "PnP pose is not stable under small camera motion."
                        )
                        self._stop(move_robot)
                        return False

                    handoff_standoff_m = self._handoff_standoff_for_class(target_cls)
                    if abs(handoff_standoff_m - self._yolo_approach_standoff_m) > 1e-4:
                        send_feedback(
                            f"ACT handoff: moving to insertion handoff standoff "
                            f"{handoff_standoff_m*1000:.0f} mm..."
                        )
                        self.get_logger().info(
                            f"ACT handoff START  standoff="
                            f"{handoff_standoff_m*1000:.0f}mm class={target_cls}"
                        )
                        approach_ok = self._approach_to_yolo_pos(
                            get_observation,
                            move_robot,
                            send_feedback,
                            target_class=target_cls,
                            standoff_m=handoff_standoff_m,
                            timeout_sec=25.0,
                        )
                        if not approach_ok:
                            if self._act_available:
                                self.get_logger().error(
                                    "YOLO handoff approach failed; refusing ACT "
                                    "handoff because TCP is outside ACT start distribution."
                                )
                                send_feedback("YOLO handoff approach failed — not starting ACT")
                                self._stop(move_robot)
                                return False
                            self.get_logger().warn(
                                "YOLO handoff approach failed; continuing with "
                                "servo insertion fallback from the current pose."
                            )
                            send_feedback(
                                "YOLO handoff did not settle — starting servo insertion anyway"
                            )
                    send_feedback(
                        "Approach done — starting "
                        + ("ACT insertion..." if self._act_available else "servo insertion...")
                    )
                else:
                    self.get_logger().warn(
                        "YOLO: no detection — refusing ACT handoff from current position"
                    )
                    send_feedback("YOLO missed — not starting ACT")
                    self._stop(move_robot)
                    return False
            else:
                self.get_logger().error(
                    "No GT TF and no YOLO model; refusing ACT handoff from "
                    "unverified current position."
                )
                send_feedback("No pose detection — not starting ACT")
                self._stop(move_robot)
                return False

            result = self._act_phase(get_observation, move_robot, send_feedback)
            if result == "stall":
                send_feedback("No insertion progress — final reachable pose, stopping task")
                self.get_logger().warn(
                    "No insertion progress after handoff; stopping insert_cable "
                    "instead of retrying."
                )
                self._stop(move_robot)
            return True

        self._publish_yolo_gt_comparison(
            task,
            target_cls,
            port_frame,
            entrance_frame,
            get_observation,
            send_feedback,
        )
        send_feedback("GT approach: aligning position and orientation...")
        self._gt_approach(task, move_robot, send_feedback)
        self.sleep_for(0.3)

        for attempt in range(_MAX_REALIGN_RETRIES + 1):
            if attempt > 0:
                # Pullback: short (2 mm) for first 2 retries, slightly longer (3 mm) after
                pullback = _BACKOFF_LONG_M if attempt >= 3 else _BACKOFF_SHORT_M
                self.get_logger().info(
                    f"Recovery attempt {attempt}/{_MAX_REALIGN_RETRIES}  "
                    f"pullback={pullback*1000:.0f}mm  "
                    f"mode={'wiggle' if attempt > 5 else 'lateral' if attempt >= 3 else 'plain'}"
                )
                self._backoff(move_robot, send_feedback, dist_m=pullback)
                if self.policy is not None:
                    self.policy.reset()

                if attempt > 5:
                    # Wiggle mode: position right at entrance and oscillate in
                    send_feedback(f"Wiggle entry (attempt {attempt + 1})...")
                    self._wiggle_entry(move_robot, send_feedback)
                else:
                    self._gt_approach(task, move_robot, send_feedback)

                self.sleep_for(0.3)

            # Choose ACT mode based on attempt count
            lateral = 3 <= attempt <= 5
            send_feedback(
                f"{'ACT' if self._act_available else 'Servo'} insertion (attempt {attempt + 1}"
                + (", lateral correction" if lateral else "")
                + (", post-wiggle" if attempt > 5 else "")
                + ")..."
            )
            result = self._act_phase(
                get_observation, move_robot, send_feedback,
                lateral_correct=lateral,
            )

            if result != "stall":
                break

            send_feedback("No insertion progress — final reachable pose, stopping task")
            self.get_logger().warn(
                "No insertion progress; stopping insert_cable instead of "
                "entering recovery retry loop."
            )
            self._stop(move_robot)
            break

        return True

    # ── Deterministic insertion fallback ─────────────────────────────────

    def _servo_insert_phase(
        self,
        get_observation: GetObservationCallback,
        move_robot: MoveRobotCallback,
        send_feedback: SendFeedbackCallback,
        timeout_sec: float = 60.0,
        lateral_correct: bool = False,
    ):
        """
        Insert with a simple velocity servo when the ACT checkpoint is not
        available.  YOLO/GT provides the port and axis; this phase only pushes
        along that axis and optionally corrects lateral drift from plug TF.
        """
        task = self._task
        plug_frames = [
            f"{task.cable_name}/{task.plug_name}_link",
            f"{task.cable_name}/{task.plug_name}",
        ]

        axis = np.asarray(self._insertion_axis, dtype=float)
        norm = float(np.linalg.norm(axis))
        if norm < 1e-6:
            axis = np.array([0.0, 0.0, -1.0], dtype=float)
        else:
            axis = axis / norm
        self._insertion_axis = axis

        start = time.time()
        step = 0
        lat_ref = None
        stall_last_prog = 0.0
        stall_last_t = time.monotonic()
        stall_start = None
        lat_correct_ref: Optional[np.ndarray] = None

        self.get_logger().warn(
            "Using YOLO/servo insertion fallback because ACT weights are unavailable"
        )

        while time.time() - start < timeout_sec:
            t0 = time.time()
            obs_msg = get_observation()

            plug_pos = None
            for frame in plug_frames:
                plug_pos = self._lookup_pos(frame)
                if plug_pos is not None:
                    break

            if plug_pos is not None:
                if lat_ref is None:
                    lat_ref = plug_pos.copy()
                if lat_correct_ref is None:
                    lat_correct_ref = plug_pos.copy()

                axial_prog = float(np.dot(plug_pos - lat_ref, axis))
                now = time.monotonic()
                dt = max(now - stall_last_t, 0.01)
                rate_mm_s = (axial_prog - stall_last_prog) / dt * 1000.0
                stall_last_prog = axial_prog
                stall_last_t = now

                if self._port_pos is not None:
                    dist_remaining = float(np.dot(self._port_pos - plug_pos, axis))
                    if dist_remaining <= _INSERT_DONE_M:
                        self._stop(move_robot)
                        self.get_logger().info(
                            f"Servo insertion complete  dist={dist_remaining*1000:.1f}mm  "
                            f"step={step}"
                        )
                        return True

                elapsed = time.time() - start
                if rate_mm_s < _STALL_RATE_MM_S and elapsed > _STALL_GRACE_S:
                    if stall_start is None:
                        stall_start = now
                    elif now - stall_start >= _STALL_WINDOW_S:
                        self._stop(move_robot)
                        self.get_logger().warn(
                            f"Servo stall at step {step}: "
                            f"axial_prog={axial_prog*1000:.1f}mm  "
                            f"rate={rate_mm_s:.2f}mm/s"
                        )
                        return "stall"
                else:
                    stall_start = None

            lin = axis * _SERVO_INSERT_SPEED_MPS
            if lateral_correct and plug_pos is not None and lat_correct_ref is not None:
                disp = plug_pos - lat_correct_ref
                axial_component = float(np.dot(disp, axis))
                lat_drift = disp - axial_component * axis
                lin += _LATERAL_KP * (-lat_drift)

            lin = np.clip(lin, -_MAX_LIN_VEL, _MAX_LIN_VEL)
            self._send_cmd(move_robot, lin)

            if step % 10 == 0:
                prog_mm = (
                    float(np.dot(plug_pos - lat_ref, axis)) * 1000.0
                    if plug_pos is not None and lat_ref is not None
                    else float("nan")
                )
                send_feedback(
                    f"Servo step {step}  prog={prog_mm:.1f}mm  "
                    f"v=[{lin[0]:.3f},{lin[1]:.3f},{lin[2]:.3f}] m/s"
                )

            step += 1
            time.sleep(max(0.0, 0.1 - (time.time() - t0)))

        self._stop(move_robot)
        self.get_logger().info(
            f"Servo insertion phase complete after {step} steps ({timeout_sec:.0f} s timeout)"
        )
        return True

    # ── ACT inference loop ────────────────────────────────────────────────

    def _act_phase(
        self,
        get_observation: GetObservationCallback,
        move_robot: MoveRobotCallback,
        send_feedback: SendFeedbackCallback,
        timeout_sec: float = 60.0,
        lateral_correct: bool = False,
    ):
        """
        Run ACT inference loop.  Returns True on timeout/completion.
        Returns "stall" when the plug stops making axial progress for
        _STALL_WINDOW_S seconds.

        lateral_correct=True adds a lateral-hold overlay on top of ACT's output
        (INSERT_HOLD_KP * lat_err), used from attempt 3 onward when plain ACT
        keeps drifting sideways.
        """
        if not self._act_available or self.policy is None:
            return self._servo_insert_phase(
                get_observation,
                move_robot,
                send_feedback,
                timeout_sec=timeout_sec,
                lateral_correct=lateral_correct,
            )

        # Build plug frame list from stored task
        task = self._task
        plug_frames = [
            f"{task.cable_name}/{task.plug_name}_link",
            f"{task.cable_name}/{task.plug_name}",
        ]

        start = time.time()
        step = 0

        # Stall detection state (mirrors _reset_stall / _check_stall)
        lat_ref         = None   # plug position when ACT started (axial reference)
        stall_last_prog = 0.0
        stall_last_t    = time.monotonic()
        stall_start     = None

        # Lateral-correction overlay reference (set on first plug observation)
        lat_correct_ref: Optional[np.ndarray] = None

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

                # Close-range: plug is nearly in — distance-based success,
                # never stall-trigger (plug stops moving once inserted).
                if self._port_pos is not None:
                    dist_remaining = float(
                        np.dot(self._port_pos - plug_pos, self._insertion_axis)
                    )
                    if dist_remaining <= _INSERT_DONE_M:
                        self._stop(move_robot)
                        self.get_logger().info(
                            f"Insertion complete  dist={dist_remaining*1000:.1f}mm  "
                            f"step={step}"
                        )
                        return True
                    if dist_remaining <= _CLOSE_THRESH_M:
                        stall_start = None   # suppress stall — plug nearly seated
                        self.sleep_for(max(0.0, 0.1 - (time.time() - t0)))
                        continue

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

            lin = np.array(a[:3], dtype=float)
            ang = np.array(a[3:6], dtype=float)

            # Lateral-correction overlay: cancel drift perpendicular to axis
            if lateral_correct and plug_pos is not None:
                if lat_correct_ref is None:
                    lat_correct_ref = plug_pos.copy()
                disp = plug_pos - lat_correct_ref
                axial_component = float(np.dot(disp, self._insertion_axis))
                lat_drift = disp - axial_component * self._insertion_axis
                lin += _LATERAL_KP * (-lat_drift)   # push back toward starting line

            lin = np.clip(lin, -_MAX_LIN_VEL, _MAX_LIN_VEL)
            ang = np.clip(ang, -_MAX_ANG_VEL, _MAX_ANG_VEL)
            self._send_cmd(move_robot, lin, ang)

            if step % 10 == 0:
                prog_mm = float(np.dot(plug_pos - lat_ref, self._insertion_axis)) * 1000 if (plug_pos is not None and lat_ref is not None) else float("nan")
                lat_mm = float(np.linalg.norm((plug_pos - lat_correct_ref) - float(np.dot(plug_pos - lat_correct_ref, self._insertion_axis)) * self._insertion_axis) * 1000) if (lateral_correct and lat_correct_ref is not None and plug_pos is not None) else float("nan")
                send_feedback(
                    f"ACT step {step}  prog={prog_mm:.1f}mm"
                    + (f"  lat_drift={lat_mm:.1f}mm" if lateral_correct else "")
                    + f"  v=[{lin[0]:.3f},{lin[1]:.3f},{lin[2]:.3f}] m/s"
                )
            step += 1

            elapsed = time.time() - t0
            time.sleep(max(0.0, 0.1 - elapsed))

        self.get_logger().info(
            f"ACT phase complete after {step} steps ({timeout_sec:.0f} s timeout)"
        )
        return True
