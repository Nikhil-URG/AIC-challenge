#
#  Copyright (C) 2026 Intrinsic Innovation LLC
#
#  Licensed under the Apache License, Version 2.0 (the "License")
#
"""
ScreenshotCollector — captures clean centre-camera PNGs for manual annotation.

Unlike PoseDataCollector this does NOT auto-label keypoints.  Images are saved
to disk for upload to Roboflow where keypoints are placed manually.

Output layout:
    <OUT_BASE_DIR>/
        sfp_port_0/   000000.png  000001.png  ...
        sfp_port_1/   000000.png  000001.png  ...
        sc_port/      000000.png  000001.png  ...

aic_engine calls insert_cable once per task.  Each call uses task.port_name
to determine the subfolder, so all ports are collected in one sim session.

Env vars:
    PLUG_TYPE  — optional filter; if set only collect tasks whose port_name
                 matches (e.g. PLUG_TYPE=sfp_port_0 skips sfp_port_1 and sc)
    N_SAMPLES  — images to capture per task/port (default 50)
    OUT_BASE   — root screenshots directory
                 (default: .../pose_data/screenshots/)

Run via:
    Terminal A:  bash scripts/run_sim_sfp.sh
    Terminal B:  bash scripts/capture_port_screenshots.sh
                 # or to collect only one port type:
                 PLUG_TYPE=sfp_port_0 bash scripts/capture_port_screenshots.sh
"""

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

# ── Config (env vars) ─────────────────────────────────────────────────────────
# PLUG_TYPE filter: if set, skip tasks whose port_name doesn't match.
# Matching is done after stripping underscores and lowercasing, so
# "sfp_port_0", "sfpport0", "sfp_port0" all match each other.
_PLUG_TYPE_FILTER = os.environ.get("PLUG_TYPE", "").lower().replace("_", "")

_N_SAMPLES = int(os.environ.get("N_SAMPLES", 50))

_OUT_BASE = Path(os.environ.get(
    "OUT_BASE",
    str(Path.home() / "ws_aic/src/aic/my_policy_node/pose_data/screenshots")
))

# Viewpoint sampling — same parameters as PoseDataCollector
_VP_LAT_MAX       = 0.05
_VP_AXIAL_MIN     = 0.00
_VP_AXIAL_MAX     = 0.20
_VP_KP            = 6.0
_VP_ORIENT_KP     = 3.0
_VP_DONE_M        = 0.005
_VP_DONE_RAD      = 0.05
_VP_SETTLED_TICKS = 8
_VP_TIMEOUT_S     = 10.0
_MAX_LIN_VEL      = 0.15
_MAX_ANG_VEL      = 1.5


# ── Geometry helpers ──────────────────────────────────────────────────────────

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
    ax = np.array([
        R_err[2,1]-R_err[1,2],
        R_err[0,2]-R_err[2,0],
        R_err[1,0]-R_err[0,1],
    ]) / (2 * math.sin(angle))
    return ax * angle


# ── Policy ────────────────────────────────────────────────────────────────────

class ScreenshotCollector(Policy):
    """Moves to random viewpoints around each port and saves centre-camera images."""

    def __init__(self, parent_node: Node) -> None:
        super().__init__(parent_node)
        self._rng = np.random.default_rng()
        _OUT_BASE.mkdir(parents=True, exist_ok=True)
        filter_msg = (f"filter='{_PLUG_TYPE_FILTER}' (skipping non-matching tasks)"
                      if _PLUG_TYPE_FILTER else "no filter (collecting all port types)")
        self.get_logger().info(
            f"ScreenshotCollector ready\n"
            f"  output base : {_OUT_BASE}\n"
            f"  samples/port: {_N_SAMPLES}\n"
            f"  {filter_msg}\n"
            f"  (waiting for tasks from aic_engine...)"
        )

    # ── TF helpers ────────────────────────────────────────────────────────────

    def _lookup(self, frame: str) -> Tuple[Optional[np.ndarray], Optional[np.ndarray]]:
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

    # ── Motion helpers ────────────────────────────────────────────────────────

    def _make_cmd(self, lin: np.ndarray, ang: np.ndarray) -> MotionUpdate:
        spd = np.linalg.norm(lin)
        if spd > _MAX_LIN_VEL:
            lin = lin / spd * _MAX_LIN_VEL
        asc = np.linalg.norm(ang)
        if asc > _MAX_ANG_VEL:
            ang = ang / asc * _MAX_ANG_VEL
        msg = MotionUpdate()
        msg.velocity = Twist(
            linear =Vector3(x=float(lin[0]), y=float(lin[1]), z=float(lin[2])),
            angular=Vector3(x=float(ang[0]), y=float(ang[1]), z=float(ang[2])),
        )
        msg.header.frame_id = "base_link"
        msg.header.stamp    = self.get_clock().now().to_msg()
        msg.target_stiffness = np.diag([100., 100., 100., 50., 50., 50.]).flatten().tolist()
        msg.target_damping   = np.diag([40.,  40.,  40.,  15., 15., 15.]).flatten().tolist()
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
            if (np.linalg.norm(pos_err) < _VP_DONE_M and
                    np.linalg.norm(omega) < _VP_DONE_RAD):
                settled += 1
                if settled >= _VP_SETTLED_TICKS:
                    self._stop(move_robot)
                    return True
            else:
                settled = 0
            self.sleep_for(0.1)
        self._stop(move_robot)
        return False

    # ── Viewpoint sampling ────────────────────────────────────────────────────

    def _sample_offsets(
        self,
        base_pos: np.ndarray,
        base_R: np.ndarray,
        axis: np.ndarray,
        n: int,
    ) -> List[Tuple[np.ndarray, np.ndarray]]:
        ref   = np.array([1., 0., 0.]) if abs(axis[0]) < 0.9 else np.array([0., 1., 0.])
        perp1 = np.cross(-axis, ref);  perp1 /= np.linalg.norm(perp1)
        perp2 = np.cross(-axis, perp1)
        viewpoints = []
        for _ in range(n):
            lat_u = self._rng.uniform(-_VP_LAT_MAX, _VP_LAT_MAX)
            lat_v = self._rng.uniform(-_VP_LAT_MAX, _VP_LAT_MAX)
            axial = self._rng.uniform(_VP_AXIAL_MIN, _VP_AXIAL_MAX)
            pos   = base_pos + axial * (-axis) + lat_u * perp1 + lat_v * perp2
            viewpoints.append((pos, base_R))
        return viewpoints

    # ── Main entry point ──────────────────────────────────────────────────────

    def insert_cable(
        self,
        task: Task,
        get_observation: GetObservationCallback,
        move_robot: MoveRobotCallback,
        send_feedback: SendFeedbackCallback,
        **kwargs,
    ) -> bool:

        # Determine class name from task (e.g. "sfp_port_0", "sc_port")
        port_name  = getattr(task, "port_name",  "unknown").lower()
        plug_type  = getattr(task, "plug_type",  "unknown").lower()
        # Folder name: prefer port_name (distinguishes port 0 vs 1), fall back to plug_type
        class_name = port_name if port_name != "unknown" else plug_type

        # Apply PLUG_TYPE filter — skip tasks that don't match
        if _PLUG_TYPE_FILTER:
            task_key = class_name.replace("_", "")
            if task_key != _PLUG_TYPE_FILTER:
                self.get_logger().info(
                    f"Skipping task port_name='{port_name}' "
                    f"(filter='{_PLUG_TYPE_FILTER}')"
                )
                return True

        out_dir = _OUT_BASE / class_name
        out_dir.mkdir(parents=True, exist_ok=True)

        existing  = sorted(out_dir.glob("*.png"))
        start_idx = int(existing[-1].stem) + 1 if existing else 0

        self.get_logger().info(
            f"ScreenshotCollector: port='{class_name}'  "
            f"samples={_N_SAMPLES}  start_idx={start_idx}  out={out_dir}"
        )
        send_feedback(f"ScreenshotCollector: collecting {_N_SAMPLES} images for '{class_name}'")

        # Get current TCP as sampling base
        base_pos, base_R = self._lookup("gripper/tcp")
        if base_pos is None:
            self.get_logger().error("Cannot lookup gripper/tcp — skipping trial")
            return True

        axis = base_R[:, 2]
        axis /= np.linalg.norm(axis)

        viewpoints = self._sample_offsets(base_pos, base_R, axis, _N_SAMPLES)
        saved = 0

        for i, (vp_pos, vp_R) in enumerate(viewpoints):
            send_feedback(f"[{class_name}] {i+1}/{_N_SAMPLES}  saved={saved}")

            reached = self._move_to(vp_pos, vp_R, move_robot)
            if not reached:
                self.get_logger().warn(
                    f"[{class_name}] viewpoint {i+1} not reached — "
                    f"capturing from current position"
                )

            self.sleep_for(0.15)
            obs     = get_observation()
            img_msg = obs.center_image
            img_np  = np.frombuffer(img_msg.data, dtype=np.uint8).reshape(
                img_msg.height, img_msg.width, 3
            )
            img_bgr = cv2.cvtColor(img_np, cv2.COLOR_RGB2BGR)

            idx      = start_idx + saved
            out_path = out_dir / f"{idx:06d}.png"
            cv2.imwrite(str(out_path), img_bgr)
            saved += 1
            self.get_logger().info(f"[{class_name}] saved {out_path.name}  ({saved}/{_N_SAMPLES})")

        send_feedback(f"[{class_name}] done — {saved} images in {out_dir}")
        self.get_logger().info(
            f"ScreenshotCollector: '{class_name}' complete — {saved} images"
        )
        return True
