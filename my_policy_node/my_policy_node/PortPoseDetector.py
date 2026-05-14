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
PortPoseDetector — wraps the trained YOLO-pose model to detect SC / SFP ports
in an RGB image and estimate their 3D position in the robot base_link frame.

Model classes  (from aic_pose_model training):
    0  SC_SKL   — SC fibre port
    1  SPF_SKL  — SFP (small-form-factor pluggable) network port

Depth is estimated from the detected bounding-box width and the approximate
known physical width of each port face.
"""

from pathlib import Path
from typing import Dict, List, Optional, Tuple

import numpy as np

# ── Per-class approximate face width (metres) used for depth estimation ───────
# SC port body face: ≈13 mm; SFP cage opening: ≈20 mm
_PORT_FACE_W: Dict[int, float] = {0: 0.013, 1: 0.020}

# Only report detections above this confidence
_CONF_THRESH = 0.40

CLASS_SC  = 0  # SC_SKL
CLASS_SFP = 1  # SPF_SKL


class PortPoseDetector:
    """
    Lightweight wrapper around the trained YOLO-pose model.

    Usage::

        detector = PortPoseDetector(PortPoseDetector.find_model())
        dets = detector.detect(img_rgb)
        det  = detector.best_detection(dets, target_class=CLASS_SC)
        port_pos, ins_axis = detector.estimate_port_3d(
            det, K, cam_pos, cam_R, img_w, img_h
        )
    """

    def __init__(self, model_path: Path) -> None:
        from ultralytics import YOLO  # lazy import — keeps ROS startup fast
        self._model = YOLO(str(model_path))

    # ── Model discovery ───────────────────────────────────────────────────────

    @staticmethod
    def find_model() -> Optional[Path]:
        """Return the path to best.pt if found in any standard location."""
        pkg_root = Path(__file__).resolve().parent.parent
        candidates = [
            pkg_root / "yolo_pose_model" / "aic_output" / "best.pt",
            pkg_root / "pose_model" / "best.pt",
            Path.home() / "ws_aic/src/aic/my_policy_node/yolo_pose_model/aic_output/best.pt",
        ]
        for c in candidates:
            if c.is_file():
                return c
        return None

    # ── Inference ─────────────────────────────────────────────────────────────

    def detect(self, img_rgb: np.ndarray) -> List[dict]:
        """
        Run YOLO-pose inference on an RGB uint8 image (H×W×3).

        Returns a list of detection dicts (one per object, confidence-filtered):
            class_id   int
            conf       float
            bbox_norm  np.ndarray (4,)  cx,cy,bw,bh normalised to [0,1]
            kp_px      np.ndarray (17,2) keypoint pixel coordinates
            kp_conf    np.ndarray (17,)  per-keypoint confidence
        """
        results = self._model(img_rgb, verbose=False)
        detections: List[dict] = []
        for r in results:
            if r.boxes is None or r.keypoints is None:
                continue
            kp_xy   = r.keypoints.xy.cpu().numpy()         # (N, 17, 2)
            kp_conf = (
                r.keypoints.conf.cpu().numpy()              # (N, 17)
                if r.keypoints.conf is not None
                else np.ones((len(r.boxes), 17), dtype=np.float32)
            )
            for i in range(len(r.boxes)):
                conf = float(r.boxes.conf[i])
                if conf < _CONF_THRESH:
                    continue
                detections.append({
                    "class_id":  int(r.boxes.cls[i]),
                    "conf":      conf,
                    "bbox_norm": r.boxes.xywhn[i].cpu().numpy(),
                    "kp_px":     kp_xy[i],    # (17, 2)
                    "kp_conf":   kp_conf[i],  # (17,)
                })
        return detections

    def best_detection(
        self,
        detections: List[dict],
        target_class: Optional[int] = None,
    ) -> Optional[dict]:
        """Return highest-confidence detection, optionally filtered by class."""
        filtered = [
            d for d in detections
            if target_class is None or d["class_id"] == target_class
        ]
        if not filtered:
            return None
        return max(filtered, key=lambda d: d["conf"])

    # ── 3-D estimation ────────────────────────────────────────────────────────

    def estimate_port_3d(
        self,
        detection: dict,
        K: np.ndarray,       # (3,3) camera intrinsics
        cam_pos: np.ndarray,  # (3,) camera origin in base_link
        cam_R: np.ndarray,    # (3,3) camera rotation (cols = axes in base_link)
        img_w: int,
        img_h: int,
    ) -> Tuple[Optional[np.ndarray], Optional[np.ndarray]]:
        """
        Estimate (port_pos, insertion_axis) in base_link frame.

        Depth is derived from the detected bounding-box width compared to the
        known approximate physical port width.  The insertion axis is
        approximated as the camera forward direction — valid because ports face
        the camera during manipulation.

        Returns (port_pos, insertion_axis) or (None, None) on failure.
        """
        bw_px = float(detection["bbox_norm"][2]) * img_w
        if bw_px < 4:
            return None, None

        face_w_m = _PORT_FACE_W.get(detection["class_id"], 0.015)
        depth_m  = K[0, 0] * face_w_m / bw_px

        # Port centre in 2-D: centroid of confident keypoints, or bbox centre
        kp_px   = detection["kp_px"]
        kp_conf = detection["kp_conf"]
        vis_mask = kp_conf > 0.3
        if np.any(vis_mask):
            cx_px, cy_px = kp_px[vis_mask].mean(axis=0)
        else:
            cx_px = float(detection["bbox_norm"][0]) * img_w
            cy_px = float(detection["bbox_norm"][1]) * img_h

        # Unproject 2-D centre to camera-frame 3-D point
        x_c = (cx_px - K[0, 2]) / K[0, 0] * depth_m
        y_c = (cy_px - K[1, 2]) / K[1, 1] * depth_m
        p_cam = np.array([x_c, y_c, depth_m])

        # Transform to base_link
        port_pos = cam_R @ p_cam + cam_pos

        # Insertion axis ≈ camera Z-axis (forward) — ports face the camera
        insertion_axis = cam_R[:, 2] / max(np.linalg.norm(cam_R[:, 2]), 1e-9)

        return port_pos, insertion_axis
