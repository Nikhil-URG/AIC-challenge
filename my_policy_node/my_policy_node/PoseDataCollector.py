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

"""
PoseDataCollector — collects labeled training images for keypoint-based
port pose estimation.

For each trial the arm visits SAMPLES_PER_TRIAL random viewpoints in a
hemisphere around the port entrance, captures the center camera image, and
writes image + projected 2D keypoint labels to disk.

Output layout:
    <POSE_DATA_DIR>/<plug_type>/
        images/   000000.png  000001.png  ...
        labels/   000000.json 000001.json ...
    <POSE_DATA_DIR>/camera_info.json   (written once from first observation)

Run via:
    Terminal A:  bash scripts/run_sim_sfp.sh
    Terminal B:  bash scripts/collect_pose_data.sh
"""

import json
import math
import os
import time
from pathlib import Path
from typing import List, Optional, Tuple

import cv2
import numpy as np
from geometry_msgs.msg import Twist, Vector3, Wrench
from rclpy.node import Node
from rclpy.time import Time
from tf2_ros import TransformException

from aic_control_interfaces.msg import MotionUpdate, TrajectoryGenerationMode
from aic_model.policy import (
    GetObservationCallback,
    MoveRobotCallback,
    Policy,
    SendFeedbackCallback,
)
from aic_task_interfaces.msg import Task

# ── Port keypoints in the entrance_link frame (meters) ────────────────────────
# SFP: rectangular opening ~12 mm × 8 mm — center + 4 corners
_KP_SFP = np.array([
    [ 0.000,  0.000, 0.000],   # 0  center
    [-0.006, -0.004, 0.000],   # 1  top-left
    [ 0.006, -0.004, 0.000],   # 2  top-right
    [ 0.006,  0.004, 0.000],   # 3  bottom-right
    [-0.006,  0.004, 0.000],   # 4  bottom-left
], dtype=np.float64)

# SC: circular opening ~2.5 mm radius — center + 4 cardinal points
_KP_SC = np.array([
    [ 0.000,  0.000,  0.000],  # 0  center
    [ 0.0013, 0.000,  0.000],  # 1  right
    [ 0.000,  0.0013, 0.000],  # 2  bottom
    [-0.0013, 0.000,  0.000],  # 3  left
    [ 0.000, -0.0013, 0.000],  # 4  top
], dtype=np.float64)

_KP_BY_TYPE = {"sfp": _KP_SFP, "sc": _KP_SC}

# ── Per-trial collection parameters ───────────────────────────────────────────
# insert_cable holds control until it returns — collect all samples in one call.
# Target: 200 samples per sim run; ~3 runs gives ~600 for initial training.
# Override via env var: POSE_SAMPLES_PER_TRIAL=500 bash collect_pose_data.sh
import os as _os
_SAMPLES_PER_TRIAL   = int(_os.environ.get("POSE_SAMPLES_PER_TRIAL", 200))
_VP_LAT_MAX          = 0.05   # ±5 cm lateral offset from current TCP pos
_VP_AXIAL_MIN        = 0.00   # stay at current distance or retreat
_VP_AXIAL_MAX        = 0.20   # up to 20 cm retreat for far-away views
_VP_KP               = 6.0
_VP_ORIENT_KP        = 3.0
_VP_DONE_M           = 0.005  # 5 mm position tolerance
_VP_DONE_RAD         = 0.05   # ~3°
_VP_SETTLED_TICKS    = 8      # 0.8 s at 10 Hz
_VP_TIMEOUT_S        = 10.0   # per-viewpoint — generous for wider offsets
_MAX_LIN_VEL         = 0.15
_MAX_ANG_VEL         = 1.5


# ── Geometry helpers ───────────────────────────────────────────────────────────

def _quat_to_rot(q) -> np.ndarray:
    x, y, z, w = q
    return np.array([
        [1-2*(y*y+z*z),   2*(x*y-w*z),   2*(x*z+w*y)],
        [  2*(x*y+w*z), 1-2*(x*x+z*z),   2*(y*z-w*x)],
        [  2*(x*z-w*y),   2*(y*z+w*x), 1-2*(x*x+y*y)],
    ])


def _rot_error(R_cur: np.ndarray, R_des: np.ndarray) -> np.ndarray:
    R_err = R_des @ R_cur.T
    angle = math.acos(max(-1.0, min(1.0, (np.trace(R_err) - 1) / 2)))
    if angle < 1e-6:
        return np.zeros(3)
    axis = np.array([
        R_err[2,1]-R_err[1,2],
        R_err[0,2]-R_err[2,0],
        R_err[1,0]-R_err[0,1],
    ]) / (2 * math.sin(angle))
    return axis * angle


class PoseDataCollector(Policy):

    def __init__(self, parent_node: Node):
        super().__init__(parent_node)
        self._rng = np.random.default_rng()
        self._output_root = Path(
            os.environ.get(
                "POSE_DATA_DIR",
                Path.home() / "ws_aic/src/aic/my_policy_node/pose_data",
            )
        )
        self._sample_counters: dict = {}   # plug_type → int
        self._camera_info_saved = False
        self.get_logger().info(
            f"PoseDataCollector ready — output dir: {self._output_root}  "
            f"(waiting for tasks from aic_engine...)"
        )

    # ── TF helpers ─────────────────────────────────────────────────────────────

    def _lookup(self, frame: str) -> Tuple[Optional[np.ndarray], Optional[np.ndarray]]:
        """Return (position, rotation_matrix) in base_link, or (None, None)."""
        try:
            tf = self._parent_node._tf_buffer.lookup_transform(
                "base_link", frame, Time()
            )
            t = tf.transform.translation
            q = tf.transform.rotation
            return (
                np.array([t.x, t.y, t.z]),
                _quat_to_rot((q.x, q.y, q.z, q.w)),
            )
        except TransformException:
            return None, None

    # ── Motion helpers ─────────────────────────────────────────────────────────

    def _make_cmd(self, lin: np.ndarray, ang: np.ndarray) -> MotionUpdate:
        spd = np.linalg.norm(lin)
        if spd > _MAX_LIN_VEL:
            lin = lin / spd * _MAX_LIN_VEL
        asc = np.linalg.norm(ang)
        if asc > _MAX_ANG_VEL:
            ang = ang / asc * _MAX_ANG_VEL
        msg = MotionUpdate()
        msg.velocity = Twist(
            linear=Vector3(x=float(lin[0]), y=float(lin[1]), z=float(lin[2])),
            angular=Vector3(x=float(ang[0]), y=float(ang[1]), z=float(ang[2])),
        )
        msg.header.frame_id = "base_link"
        msg.header.stamp = self.get_clock().now().to_msg()
        msg.target_stiffness = np.diag(
            [100., 100., 100., 50., 50., 50.]
        ).flatten().tolist()
        msg.target_damping = np.diag(
            [40., 40., 40., 15., 15., 15.]
        ).flatten().tolist()
        msg.feedforward_wrench_at_tip = Wrench(
            force=Vector3(x=0., y=0., z=0.),
            torque=Vector3(x=0., y=0., z=0.),
        )
        msg.wrench_feedback_gains_at_tip = [0.5, 0.5, 0.5, 0., 0., 0.]
        msg.trajectory_generation_mode.mode = TrajectoryGenerationMode.MODE_VELOCITY
        return msg

    def _stop(self, move_robot: MoveRobotCallback) -> None:
        move_robot(motion_update=self._make_cmd(np.zeros(3), np.zeros(3)))

    def _move_to(
        self,
        target_pos: np.ndarray,
        target_R: np.ndarray,
        move_robot: MoveRobotCallback,
    ) -> bool:
        """KP position + orientation controller. Returns True when settled."""
        settled = 0
        t0 = time.time()
        while time.time() - t0 < _VP_TIMEOUT_S:
            tcp_pos, tcp_R = self._lookup("gripper/tcp")
            if tcp_pos is None:
                self.sleep_for(0.1)
                continue
            pos_err = target_pos - tcp_pos
            omega   = _rot_error(tcp_R, target_R)
            move_robot(motion_update=self._make_cmd(
                _VP_KP * pos_err, _VP_ORIENT_KP * omega
            ))
            if np.linalg.norm(pos_err) < _VP_DONE_M and np.linalg.norm(omega) < _VP_DONE_RAD:
                settled += 1
                if settled >= _VP_SETTLED_TICKS:
                    self._stop(move_robot)
                    return True
            else:
                settled = 0
            self.sleep_for(0.1)
        self._stop(move_robot)
        return False

    # ── Viewpoint sampling ─────────────────────────────────────────────────────

    def _sample_offsets(
        self,
        base_pos: np.ndarray,  # current TCP position (known reachable)
        base_R: np.ndarray,    # current TCP rotation
        axis: np.ndarray,      # insertion axis (points INTO port)
        n: int,
    ) -> List[Tuple[np.ndarray, np.ndarray]]:
        """
        Sample n positions as small offsets from base_pos.
        All positions are close to a known-reachable point so IK never fails.
        Lateral ±2.5 cm + axial 0–12 cm retreat gives image-space diversity.
        """
        ref = np.array([1., 0., 0.]) if abs(axis[0]) < 0.9 else np.array([0., 1., 0.])
        perp1 = np.cross(-axis, ref);  perp1 /= np.linalg.norm(perp1)
        perp2 = np.cross(-axis, perp1)

        viewpoints = []
        for _ in range(n):
            lat_u  = self._rng.uniform(-_VP_LAT_MAX,   _VP_LAT_MAX)
            lat_v  = self._rng.uniform(-_VP_LAT_MAX,   _VP_LAT_MAX)
            axial  = self._rng.uniform(_VP_AXIAL_MIN,  _VP_AXIAL_MAX)
            # retreat along -axis (away from port) + lateral shift
            pos = base_pos + axial * (-axis) + lat_u * perp1 + lat_v * perp2
            viewpoints.append((pos, base_R))
        return viewpoints

    # ── Keypoint projection ────────────────────────────────────────────────────

    def _project(
        self,
        kp_3d_world: np.ndarray,  # (N, 3) in base_link frame
        K: np.ndarray,             # (3, 3) camera intrinsic matrix
        cam_frame: str,
        img_w: int,
        img_h: int,
    ) -> Optional[np.ndarray]:
        """
        Project 3D world-frame keypoints into the camera image.
        Returns (N, 2) pixel coordinates, or None if any point is behind
        the camera or outside the image bounds.
        """
        cam_pos, cam_R = self._lookup(cam_frame)
        if cam_pos is None:
            return None

        kp_2d = []
        for p_w in kp_3d_world:
            # Transform from base_link into camera frame
            p_cam = cam_R.T @ (p_w - cam_pos)
            if p_cam[2] <= 0.01:   # behind or too close to camera plane
                return None
            u = K[0, 0] * p_cam[0] / p_cam[2] + K[0, 2]
            v = K[1, 1] * p_cam[1] / p_cam[2] + K[1, 2]
            # Reject if outside image
            if not (0 <= u < img_w and 0 <= v < img_h):
                return None
            kp_2d.append([float(u), float(v)])

        return np.array(kp_2d, dtype=np.float32)

    # ── I/O ────────────────────────────────────────────────────────────────────

    def _save_camera_info(self, obs) -> None:
        """Write camera_info.json once from the first valid observation."""
        if self._camera_info_saved:
            return
        ci = obs.center_camera_info
        if ci.width == 0:
            return
        path = self._output_root / "camera_info.json"
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "w") as f:
            json.dump({
                "K":        list(ci.k),        # row-major 3×3
                "D":        list(ci.d),        # distortion coefficients
                "frame_id": ci.header.frame_id,
                "width":    ci.width,
                "height":   ci.height,
            }, f, indent=2)
        self._camera_info_saved = True
        self.get_logger().info(
            f"Camera info saved → {path}  "
            f"frame={ci.header.frame_id}  {ci.width}×{ci.height}"
        )

    def _save_sample(
        self,
        obs,
        kp_2d: np.ndarray,
        kp_3d_world: np.ndarray,
        port_pos: np.ndarray,
        port_R: np.ndarray,
        plug_type: str,
    ) -> int:
        idx  = self._sample_counters.get(plug_type, 0)
        base = self._output_root / plug_type
        (base / "images").mkdir(parents=True, exist_ok=True)
        (base / "labels").mkdir(parents=True, exist_ok=True)

        img = obs.center_image
        img_np = np.frombuffer(img.data, dtype=np.uint8).reshape(
            img.height, img.width, 3
        )
        cv2.imwrite(
            str(base / "images" / f"{idx:06d}.png"),
            cv2.cvtColor(img_np, cv2.COLOR_RGB2BGR),
        )

        label = {
            "image":           f"images/{idx:06d}.png",
            "plug_type":       plug_type,
            "keypoints_2d":    kp_2d.tolist(),        # [[u,v], ...] 5 points
            "keypoints_3d":    kp_3d_world.tolist(),   # [[x,y,z], ...] in base_link
            "port_pos":        port_pos.tolist(),
            "port_R":          port_R.tolist(),
            "img_width":       img.width,
            "img_height":      img.height,
            "camera_frame":    obs.center_camera_info.header.frame_id,
        }
        with open(base / "labels" / f"{idx:06d}.json", "w") as f:
            json.dump(label, f)

        self._sample_counters[plug_type] = idx + 1
        return idx

    # ── Main entry point ───────────────────────────────────────────────────────

    def insert_cable(
        self,
        task: Task,
        get_observation: GetObservationCallback,
        move_robot: MoveRobotCallback,
        send_feedback: SendFeedbackCallback,
        **kwargs,
    ) -> bool:
        plug_type = getattr(task, "plug_type", "sfp").lower()
        kp_local  = _KP_BY_TYPE.get(plug_type, _KP_SFP)

        total_so_far = self._sample_counters.get(plug_type, 0)
        self.get_logger().info(
            f"PoseDataCollector: plug={plug_type}  "
            f"samples_so_far={total_so_far}"
        )

        # ── Resolve port / entrance TF frames ─────────────────────────────
        port_frames = [
            f"task_board/{task.target_module_name}/{task.port_name}_link",
            f"task_board/{task.target_module_name}/{task.port_name}",
        ]
        entrance_frames = [f + "_entrance" for f in port_frames]

        port_pos, port_R = None, None
        for frame in port_frames:
            port_pos, port_R = self._lookup(frame)
            if port_pos is not None:
                break
        if port_pos is None:
            self.get_logger().error("Port TF not found — is ground_truth:=true?")
            return False

        entrance_pos, entrance_R = None, None
        for frame in entrance_frames:
            entrance_pos, entrance_R = self._lookup(frame)
            if entrance_pos is not None:
                break
        if entrance_pos is None:
            entrance_pos = port_pos + np.array([0., 0., 0.02])
            entrance_R   = port_R
            self.get_logger().warn("Entrance TF not found — using port + 2 cm fallback")

        delta = port_pos - entrance_pos
        dlen  = np.linalg.norm(delta)
        axis  = delta / dlen if dlen > 0.005 else np.array([0., 0., -1.])

        # 3D keypoints in base_link frame (transform from entrance_link frame)
        kp_3d_world = (entrance_R @ kp_local.T).T + entrance_pos

        # ── Get current arm position as sampling base ──────────────────────
        # aic_engine positions the arm near the approach point before calling
        # insert_cable — use that known-reachable position as base for offsets.
        base_pos, base_R = self._lookup("gripper/tcp")
        if base_pos is None:
            self.get_logger().error("Cannot lookup gripper/tcp — skipping trial")
            return True

        viewpoints = self._sample_offsets(base_pos, base_R, axis, _SAMPLES_PER_TRIAL)
        saved   = 0
        t_start = time.time()

        for i, (vp_pos, vp_R) in enumerate(viewpoints):
            send_feedback(
                f"Sample {i+1}/{len(viewpoints)}  "
                f"saved={saved}  total={self._sample_counters.get(plug_type, 0)}"
            )

            if not self._move_to(vp_pos, vp_R, move_robot):
                self.get_logger().warn(
                    f"Sample {i+1} not reached — capturing from current position"
                )
                # Fall through: still capture wherever the arm stopped

            obs = get_observation()
            if obs is None:
                continue

            self._save_camera_info(obs)

            ci = obs.center_camera_info
            if ci.width == 0 or not any(ci.k):
                self.get_logger().warn("Camera info missing — skipping")
                continue

            K = np.array(ci.k).reshape(3, 3)
            cam_frame = ci.header.frame_id

            kp_2d = self._project(
                kp_3d_world, K, cam_frame, obs.center_image.width, obs.center_image.height
            )
            if kp_2d is None:
                self.get_logger().debug(f"Sample {i+1}: keypoints not visible — skipping")
                continue

            idx = self._save_sample(
                obs, kp_2d, kp_3d_world, port_pos, port_R, plug_type
            )
            saved += 1
            self.get_logger().info(
                f"Saved #{idx}  plug={plug_type}  "
                f"center_kp={kp_2d[0].round(1)} px  "
                f"t={time.time()-t_start:.1f}s"
            )

        self.get_logger().info(
            f"Trial done: {saved} saved  "
            f"total={self._sample_counters.get(plug_type, 0)}  "
            f"elapsed={time.time()-t_start:.1f}s"
        )
        return True
