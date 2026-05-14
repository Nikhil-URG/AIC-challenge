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
PoseAutoLabeler — captures images and writes YOLO-pose labels in one sim run.

Class layout (kpt_shape: [10, 3]):
    sfp_nic  (class 0) — NIC card with both SFP ports detected simultaneously.
                         kp0-kp4: sfp_port_0 (center, TL, TR, BR, BL)
                         kp5-kp9: sfp_port_1 (center, TL, TR, BR, BL)
    sc_port  (class 1) — SC fibre port.
                         kp0-kp4: port keypoints (center + 4 cardinal pts)
                         kp5-kp9: all zeros with visibility=0 (padding)

Both classes share kpt_shape=[10,3] so a single YOLO-pose head covers them.

For each SFP task call (port_0 OR port_1), images of the whole NIC card are
collected with both ports projected simultaneously.  This means calling
insert_cable for sfp_port_0 and sfp_port_1 each produces NIC card images —
doubling data volume from different TCP starting positions.

Output:
    <OUT_BASE>/
        sfp_nic/   images/*.png   labels/*.txt
        sc_port/   images/*.png   labels/*.txt
        data.yaml

Run via:
    Terminal A:  bash scripts/run_sim_sfp.sh
    Terminal B:  bash scripts/collect_yolo_labels.sh

After collection run:
    python scripts/review_yolo_labels.py pose_data/yolo_labeled/
"""

import math
import os
import time
from pathlib import Path
from typing import Optional, Tuple

import cv2
import numpy as np
import yaml
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

# ── Keypoints in entrance_link frame (meters) ─────────────────────────────────
# Shared by both SFP ports (same physical socket shape, different world position).
_KP_SFP = np.array([
    [ 0.000,  0.000, 0.000],   # 0  center
    [-0.006, -0.004, 0.000],   # 1  top-left
    [ 0.006, -0.004, 0.000],   # 2  top-right
    [ 0.006,  0.004, 0.000],   # 3  bottom-right
    [-0.006,  0.004, 0.000],   # 4  bottom-left
], dtype=np.float64)

_KP_SC = np.array([
    [ 0.000,  0.000,  0.000],  # 0  center
    [ 0.0013, 0.000,  0.000],  # 1  right
    [ 0.000,  0.0013, 0.000],  # 2  bottom
    [-0.0013, 0.000,  0.000],  # 3  left
    [ 0.000, -0.0013, 0.000],  # 4  top
], dtype=np.float64)

# ── Class mapping ─────────────────────────────────────────────────────────────
# Two classes only.  sfp_port_0 and sfp_port_1 tasks both produce sfp_nic labels.
_CLASS_MAP   = {"sfp_nic": 0, "sc_port": 1}
_CLASS_NAMES = ["sfp_nic", "sc_port"]   # index = class_id
_N_KP        = 10                        # keypoints per instance (must match kpt_shape)

# ── Config ────────────────────────────────────────────────────────────────────
_PLUG_TYPE_FILTER = os.environ.get("PLUG_TYPE", "").lower().replace("_", "")
_N_SAMPLES        = int(os.environ.get("N_SAMPLES", 100))
_BBOX_PAD_PX      = int(os.environ.get("BBOX_PAD_PX", 60))
_OUT_BASE         = Path(os.environ.get(
    "OUT_BASE",
    str(Path.home() / "ws_aic/src/aic/my_policy_node/pose_data/yolo_labeled")
))

# Viewpoint sampling
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

# Minimum visible keypoints required to accept a frame.
# For sfp_nic (10 kps): require both port centres + at least 3 corners each.
_MIN_VIS_NIC = 8   # of 10
# For sc_port (5 kps): require all 5.
_MIN_VIS_SC  = 5   # of 5


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


# ── YOLO I/O ──────────────────────────────────────────────────────────────────

def _write_yolo_label(
    path: Path,
    class_id: int,
    kp_2d: np.ndarray,    # (_N_KP, 2) — invisible kps must be (0,0)
    vis: np.ndarray,       # (_N_KP,)  — 2=visible, 0=invisible
    img_w: int,
    img_h: int,
) -> None:
    visible = kp_2d[vis > 0]
    if len(visible) == 0:
        return
    pad  = _BBOX_PAD_PX
    x0   = max(0,         visible[:, 0].min() - pad)
    x1   = min(img_w - 1, visible[:, 0].max() + pad)
    y0   = max(0,         visible[:, 1].min() - pad)
    y1   = min(img_h - 1, visible[:, 1].max() + pad)
    parts = [
        str(class_id),
        f"{(x0+x1)/2/img_w:.6f}", f"{(y0+y1)/2/img_h:.6f}",
        f"{(x1-x0)/img_w:.6f}",   f"{(y1-y0)/img_h:.6f}",
    ]
    for i, (u, v) in enumerate(kp_2d):
        if vis[i] > 0:
            parts += [f"{u/img_w:.6f}", f"{v/img_h:.6f}", "2"]
        else:
            parts += ["0.000000", "0.000000", "0"]
    path.write_text(" ".join(parts) + "\n")


def _write_data_yaml(out_base: Path) -> None:
    cfg = {
        "path":      str(out_base),
        "nc":        len(_CLASS_NAMES),
        "names":     _CLASS_NAMES,
        "kpt_shape": [_N_KP, 3],
    }
    (out_base / "data.yaml").write_text(yaml.dump(cfg, default_flow_style=None))


# ── Policy ────────────────────────────────────────────────────────────────────

class PoseAutoLabeler(Policy):
    """
    Captures images of each port and writes YOLO-pose labels using TF projection.

    SFP tasks → sfp_nic class (both ports in one label, 10 keypoints).
    SC tasks  → sc_port class (5 real + 5 zero-visibility keypoints).
    """

    def __init__(self, parent_node: Node) -> None:
        super().__init__(parent_node)
        self._rng      = np.random.default_rng()
        self._counters = {}   # class_name → int
        _OUT_BASE.mkdir(parents=True, exist_ok=True)
        _write_data_yaml(_OUT_BASE)
        filter_msg = (f"filter='{_PLUG_TYPE_FILTER}'" if _PLUG_TYPE_FILTER
                      else "no filter (collecting all port types)")
        self.get_logger().info(
            f"PoseAutoLabeler ready\n"
            f"  output   : {_OUT_BASE}\n"
            f"  samples  : {_N_SAMPLES}/task\n"
            f"  classes  : {_CLASS_NAMES}  kpt_shape=[{_N_KP},3]\n"
            f"  {filter_msg}"
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

    def _lookup_entrance(
        self, module: str, port_name: str
    ) -> Tuple[Optional[np.ndarray], Optional[np.ndarray], Optional[np.ndarray]]:
        """Return (entrance_pos, entrance_R, port_pos) for a named port."""
        port_frames = [
            f"task_board/{module}/{port_name}_link",
            f"task_board/{module}/{port_name}",
        ]
        port_pos, port_R = None, None
        for f in port_frames:
            port_pos, port_R = self._lookup(f)
            if port_pos is not None:
                break
        if port_pos is None:
            return None, None, None

        entrance_pos, entrance_R = None, None
        for f in port_frames:
            entrance_pos, entrance_R = self._lookup(f + "_entrance")
            if entrance_pos is not None:
                break
        if entrance_pos is None:
            entrance_pos = port_pos + np.array([0., 0., 0.02])
            entrance_R   = port_R
            self.get_logger().warn(
                f"Entrance TF not found for '{port_name}' — using port+2 cm fallback"
            )
        return entrance_pos, entrance_R, port_pos

    # ── Projection ────────────────────────────────────────────────────────────

    def _project(
        self,
        kp_3d: np.ndarray,   # (N, 3) in base_link
        K: np.ndarray,
        cam_frame: str,
        img_w: int,
        img_h: int,
    ) -> Tuple[Optional[np.ndarray], Optional[np.ndarray]]:
        """Return (kp_2d, vis) arrays, or (None, None) on TF failure."""
        cam_pos, cam_R = self._lookup(cam_frame)
        if cam_pos is None:
            return None, None
        N     = len(kp_3d)
        kp_2d = np.zeros((N, 2), dtype=np.float32)
        vis   = np.zeros(N, dtype=np.int32)
        for i, p_w in enumerate(kp_3d):
            p_cam = cam_R.T @ (p_w - cam_pos)
            if p_cam[2] <= 0.01:
                continue
            u = K[0, 0] * p_cam[0] / p_cam[2] + K[0, 2]
            v = K[1, 1] * p_cam[1] / p_cam[2] + K[1, 2]
            if 0 <= u < img_w and 0 <= v < img_h:
                kp_2d[i] = [u, v]
                vis[i]   = 2
        return kp_2d, vis

    # ── Motion helpers ────────────────────────────────────────────────────────

    def _make_cmd(self, lin: np.ndarray, ang: np.ndarray) -> MotionUpdate:
        for vec, limit in ((lin, _MAX_LIN_VEL), (ang, _MAX_ANG_VEL)):
            spd = np.linalg.norm(vec)
            if spd > limit:
                vec[:] = vec / spd * limit
        msg = MotionUpdate()
        msg.velocity = Twist(
            linear =Vector3(x=float(lin[0]), y=float(lin[1]), z=float(lin[2])),
            angular=Vector3(x=float(ang[0]), y=float(ang[1]), z=float(ang[2])),
        )
        msg.header.frame_id = "base_link"
        msg.header.stamp    = self.get_clock().now().to_msg()
        msg.target_stiffness = np.diag([100.,100.,100.,50.,50.,50.]).flatten().tolist()
        msg.target_damping   = np.diag([40., 40., 40.,15.,15.,15.]).flatten().tolist()
        msg.feedforward_wrench_at_tip = Wrench(
            force=Vector3(x=0.,y=0.,z=0.), torque=Vector3(x=0.,y=0.,z=0.)
        )
        msg.wrench_feedback_gains_at_tip = [0.5, 0.5, 0.5, 0., 0., 0.]
        msg.trajectory_generation_mode.mode = TrajectoryGenerationMode.MODE_VELOCITY
        return msg

    def _stop(self, move_robot):
        move_robot(motion_update=self._make_cmd(np.zeros(3), np.zeros(3)))

    def _move_to(self, target_pos, target_R, move_robot) -> bool:
        settled = 0
        t0 = time.time()
        while time.time() - t0 < _VP_TIMEOUT_S:
            tcp_pos, tcp_R = self._lookup("gripper/tcp")
            if tcp_pos is None:
                self.sleep_for(0.1); continue
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

    def _sample_viewpoints(self, base_pos, base_R, axis, n):
        ref   = np.array([1.,0.,0.]) if abs(axis[0]) < 0.9 else np.array([0.,1.,0.])
        perp1 = np.cross(-axis, ref); perp1 /= np.linalg.norm(perp1)
        perp2 = np.cross(-axis, perp1)
        vps = []
        for _ in range(n):
            lat_u = self._rng.uniform(-_VP_LAT_MAX, _VP_LAT_MAX)
            lat_v = self._rng.uniform(-_VP_LAT_MAX, _VP_LAT_MAX)
            axial = self._rng.uniform(_VP_AXIAL_MIN, _VP_AXIAL_MAX)
            vps.append((base_pos + axial*(-axis) + lat_u*perp1 + lat_v*perp2, base_R))
        return vps

    # ── Main entry point ──────────────────────────────────────────────────────

    def insert_cable(
        self,
        task: Task,
        get_observation: GetObservationCallback,
        move_robot: MoveRobotCallback,
        send_feedback: SendFeedbackCallback,
        **kwargs,
    ) -> bool:
        port_name = getattr(task, "port_name", "unknown").lower()
        module    = getattr(task, "target_module_name", "")
        is_sc     = "sc" in port_name

        # Determine output class and apply filter
        class_name = "sc_port" if is_sc else "sfp_nic"
        class_id   = _CLASS_MAP[class_name]

        if _PLUG_TYPE_FILTER:
            if class_name.replace("_", "") != _PLUG_TYPE_FILTER:
                self.get_logger().info(
                    f"Skipping '{port_name}' → class '{class_name}' "
                    f"(filter='{_PLUG_TYPE_FILTER}')"
                )
                return True

        # ── Resolve keypoints ──────────────────────────────────────────────
        if is_sc:
            e_pos, e_R, p_pos = self._lookup_entrance(module, port_name)
            if e_pos is None:
                self.get_logger().error(f"SC port TF not found for '{port_name}'")
                return False
            kp_3d_real = (e_R @ _KP_SC.T).T + e_pos          # (5, 3)
            # Pad to _N_KP with zeros; vis will be set to 0 for the padding
            kp_3d = np.vstack([kp_3d_real, np.zeros((5, 3))])  # (10, 3)
            vis_mask = np.array([2,2,2,2,2, 0,0,0,0,0], dtype=np.int32)

            # Insertion axis and sampling base from the SC port
            delta = p_pos - e_pos
            dlen  = np.linalg.norm(delta)
            axis  = delta / dlen if dlen > 0.005 else np.array([0.,0.,-1.])
            min_vis = _MIN_VIS_SC

        else:
            # SFP NIC: look up both ports regardless of which port called us
            e0_pos, e0_R, p0_pos = self._lookup_entrance(module, "sfp_port_0")
            e1_pos, e1_R, p1_pos = self._lookup_entrance(module, "sfp_port_1")

            if e0_pos is None or e1_pos is None:
                self.get_logger().error(
                    "Cannot lookup both SFP port TF frames — "
                    "is ground_truth:=true and the right sim scene loaded?"
                )
                return False

            kp_3d_p0 = (e0_R @ _KP_SFP.T).T + e0_pos   # (5, 3)
            kp_3d_p1 = (e1_R @ _KP_SFP.T).T + e1_pos   # (5, 3)
            kp_3d    = np.vstack([kp_3d_p0, kp_3d_p1])  # (10, 3)
            vis_mask = np.full(_N_KP, 2, dtype=np.int32)

            # Sampling axis: average insertion direction of both ports
            axis_0 = p0_pos - e0_pos; axis_0 /= max(np.linalg.norm(axis_0), 1e-6)
            axis_1 = p1_pos - e1_pos; axis_1 /= max(np.linalg.norm(axis_1), 1e-6)
            axis   = (axis_0 + axis_1) / 2
            axis  /= np.linalg.norm(axis)
            min_vis = _MIN_VIS_NIC

        # ── Setup output dirs ──────────────────────────────────────────────
        out_dir = _OUT_BASE / class_name
        img_dir = out_dir / "images"
        lbl_dir = out_dir / "labels"
        img_dir.mkdir(parents=True, exist_ok=True)
        lbl_dir.mkdir(parents=True, exist_ok=True)

        start_idx = self._counters.get(class_name, 0)
        # Sync counter with disk in case we're resuming
        existing = sorted(img_dir.glob("*.png"))
        if existing:
            start_idx = max(start_idx, int(existing[-1].stem) + 1)
        self._counters[class_name] = start_idx

        self.get_logger().info(
            f"PoseAutoLabeler: port='{port_name}' → class='{class_name}' "
            f"(id={class_id})  samples={_N_SAMPLES}  start_idx={start_idx}"
        )
        send_feedback(
            f"PoseAutoLabeler: collecting {_N_SAMPLES} images for '{class_name}'"
        )

        # ── Viewpoint sampling base ────────────────────────────────────────
        base_pos, base_R = self._lookup("gripper/tcp")
        if base_pos is None:
            self.get_logger().error("Cannot lookup gripper/tcp")
            return True

        viewpoints = self._sample_viewpoints(base_pos, base_R, axis, _N_SAMPLES)
        saved = skipped = 0

        for i, (vp_pos, vp_R) in enumerate(viewpoints):
            send_feedback(
                f"[{class_name}] {i+1}/{_N_SAMPLES}  saved={saved}  skipped={skipped}"
            )

            if not self._move_to(vp_pos, vp_R, move_robot):
                self.get_logger().warn(
                    f"[{class_name}] viewpoint {i+1} not reached — capturing anyway"
                )

            self.sleep_for(0.15)
            obs     = get_observation()
            img_msg = obs.center_image
            ci      = obs.center_camera_info

            if ci.width == 0 or not any(ci.k):
                skipped += 1
                continue

            K         = np.array(ci.k).reshape(3, 3)
            cam_frame = ci.header.frame_id
            img_w, img_h = img_msg.width, img_msg.height

            kp_2d, vis = self._project(kp_3d, K, cam_frame, img_w, img_h)
            if kp_2d is None:
                skipped += 1
                continue

            # Apply the static visibility mask (zeros out SC padding and any
            # keypoints that projected outside the image)
            vis = vis & vis_mask   # bitwise AND: 2&2=2, 2&0=0, 0&0=0

            n_vis = int(np.sum(vis > 0))
            if n_vis < min_vis:
                skipped += 1
                self.get_logger().debug(
                    f"[{class_name}] sample {i+1}: only {n_vis} visible kps "
                    f"(need {min_vis}) — skipping"
                )
                continue

            idx = self._counters[class_name]
            img_np  = np.frombuffer(img_msg.data, dtype=np.uint8).reshape(img_h, img_w, 3)
            img_bgr = cv2.cvtColor(img_np, cv2.COLOR_RGB2BGR)
            cv2.imwrite(str(img_dir / f"{idx:06d}.png"), img_bgr)
            _write_yolo_label(lbl_dir / f"{idx:06d}.txt", class_id, kp_2d, vis, img_w, img_h)

            self._counters[class_name] = idx + 1
            saved += 1
            self.get_logger().info(
                f"[{class_name}] #{idx}  vis={n_vis}/{_N_KP}  "
                f"p0_ctr={kp_2d[0].round(1)}px  saved={saved}/{_N_SAMPLES}"
            )

        send_feedback(f"[{class_name}] done — {saved} saved, {skipped} skipped")
        self.get_logger().info(
            f"PoseAutoLabeler: '{class_name}' complete — {saved} saved, {skipped} skipped"
        )
        return True
