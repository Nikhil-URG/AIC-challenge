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
PortPoseDetector - wraps the trained YOLO-pose model to detect SC / SFP ports
in an RGB image and estimate their 3D position in the robot base_link frame.

Model classes  (from aic_pose_model training):
    0  SC_SKL   — SC fibre port
    1  SPF_SKL  — SFP (small-form-factor pluggable) network port

Depth is estimated by solving a Perspective-n-Point problem from the detected
2D keypoints and measured 3D port datums.
"""

from pathlib import Path
from typing import Dict, List, Optional, Tuple

import cv2
import numpy as np

# Only report detections above this confidence
_CONF_THRESH = 0.40

CLASS_SC  = 0  # SC_SKL
CLASS_SFP = 1  # SPF_SKL

# Measured keypoint datums in object coordinates, converted from mm to metres.
# Coordinate system: X right, Y forward, Z upward. For both ports, insertion
# into the socket is approximately object -Y, so the approach side is +Y.
_OBJECT_POINTS_M: Dict[int, np.ndarray] = {
    CLASS_SC: np.array([
        [  1.5,   7.5, -14.9],
        [  0.0,   0.0,   0.0],
        [  0.0, -25.6,   0.0],
        [  1.5, -33.1, -15.2],
        [  7.5, -33.1, -15.2],
        [-15.2, -19.1,   0.0],
        [  9.0,  -6.5,   0.0],
        [  9.0,  -6.5,   0.0],
        [  9.0,   0.0,   0.0],
        [  7.5,   7.5, -14.9],
        [  4.5,  -6.5,  -7.1],
        [  4.5, -19.1,  -7.1],
    ], dtype=np.float64) * 1e-3,
    CLASS_SFP: np.array([
        [  0.0,   0.0,   0.0],
        [  0.0, -25.0,   0.0],
        [ 21.5, -25.0,   0.0],
        [ 21.5,  -8.6,   0.0],
        [ 11.0,   0.0,   0.0],
        [ 49.4,  -4.4, -11.7],
        [ 49.4, -13.7, -11.7],
        [ 63.5, -13.7, -11.7],
        [ 63.5,  -4.5, -11.7],
        [ 72.6,  -4.4, -11.7],
        [ 72.6, -13.7, -11.7],
        [ 86.7, -13.7, -11.7],
        [ 86.7,  -4.4, -11.7],
        [ 35.5, -20.0, -14.0],
        [ 35.5, -25.0, -14.0],
        [102.5, -25.0, -14.0],
    ], dtype=np.float64) * 1e-3,
}

# Class-specific insertion target expressed in the same object coordinates.
# SFP: center of the front cage opening. SC: midpoint between the inner datum
# pair supplied for the ferrule opening.
_TARGET_POINTS_M: Dict[int, np.ndarray] = {
    CLASS_SC: np.array([4.5, -12.8, -7.1], dtype=np.float64) * 1e-3,
    CLASS_SFP: np.array([10.75, -12.5, 0.0], dtype=np.float64) * 1e-3,
}

_INSERTION_AXIS_OBJ: Dict[int, np.ndarray] = {
    CLASS_SC: np.array([0.0, -1.0, 0.0], dtype=np.float64),
    CLASS_SFP: np.array([0.0, -1.0, 0.0], dtype=np.float64),
}

# The current SFP keypoint model was trained with 17 slots. In the available
# labels, the first five SFP points describe the port opening; later points are
# wider component landmarks whose manual order is less reliable. Use the stable
# opening correspondences for the controller-facing pose.
_PNP_POINT_INDICES: Dict[int, np.ndarray] = {
    CLASS_SC: np.array([0, 1, 2, 3, 4, 5, 6, 8, 9, 10, 11]),
    CLASS_SFP: np.arange(5),
}

_MIN_PNP_POINTS = 4
_KPT_CONF_THRESH = 0.30


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
            kp_px      np.ndarray (N,2) keypoint pixel coordinates
            kp_conf    np.ndarray (N,)  per-keypoint confidence
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
        dist_coeffs: Optional[np.ndarray] = None,
    ) -> Tuple[Optional[np.ndarray], Optional[np.ndarray]]:
        """
        Estimate (port_pos, insertion_axis) in base_link frame.

        solvePnP estimates the measured object datum pose in the camera frame.
        The returned position is the class-specific insertion target, not the
        arbitrary datum origin, so the ACT approach moves toward the port mouth.

        Returns (port_pos, insertion_axis) or (None, None) on failure.
        """
        class_id = int(detection["class_id"])
        object_points_all = _OBJECT_POINTS_M.get(class_id)
        target_obj = _TARGET_POINTS_M.get(class_id)
        axis_obj = _INSERTION_AXIS_OBJ.get(class_id)
        if object_points_all is None or target_obj is None or axis_obj is None:
            return None, None

        kp_px = np.asarray(detection["kp_px"], dtype=np.float64)
        kp_conf = np.asarray(detection["kp_conf"], dtype=np.float64)
        point_indices = _PNP_POINT_INDICES.get(class_id, np.arange(len(object_points_all)))
        point_indices = point_indices[
            point_indices < min(len(object_points_all), len(kp_px), len(kp_conf))
        ]
        if len(point_indices) < _MIN_PNP_POINTS:
            return None, None

        object_points = object_points_all[point_indices]
        image_points = kp_px[point_indices]
        point_conf = kp_conf[point_indices]
        valid = (
            (point_conf > _KPT_CONF_THRESH)
            & np.isfinite(image_points).all(axis=1)
            & (image_points[:, 0] >= 0.0)
            & (image_points[:, 0] < float(img_w))
            & (image_points[:, 1] >= 0.0)
            & (image_points[:, 1] < float(img_h))
            & (np.linalg.norm(image_points, axis=1) > 1.0)
        )
        object_points = object_points[valid]
        image_points = image_points[valid]
        if len(object_points) < _MIN_PNP_POINTS:
            return None, None

        D = np.zeros((5, 1), dtype=np.float64)
        if dist_coeffs is not None:
            D = np.asarray(dist_coeffs, dtype=np.float64).reshape(-1, 1)

        K64 = np.asarray(K, dtype=np.float64)
        inliers = None
        if len(object_points) >= 6:
            ok, rvec, tvec, inliers = cv2.solvePnPRansac(
                object_points,
                image_points,
                K64,
                D,
                flags=cv2.SOLVEPNP_EPNP,
                reprojectionError=6.0,
                iterationsCount=100,
                confidence=0.99,
            )
            if not ok or rvec is None or tvec is None:
                return None, None
            if inliers is not None and len(inliers) >= _MIN_PNP_POINTS:
                inlier_idx = inliers.reshape(-1)
                ok, rvec, tvec = cv2.solvePnP(
                    object_points[inlier_idx],
                    image_points[inlier_idx],
                    K64,
                    D,
                    rvec,
                    tvec,
                    useExtrinsicGuess=True,
                    flags=cv2.SOLVEPNP_ITERATIVE,
                )
                if not ok:
                    return None, None
        else:
            ok, rvec, tvec = cv2.solvePnP(
                object_points,
                image_points,
                K64,
                D,
                flags=cv2.SOLVEPNP_IPPE,
            )
            if not ok or rvec is None or tvec is None:
                return None, None

        R_obj_cam, _ = cv2.Rodrigues(rvec)
        target_cam = (R_obj_cam @ target_obj.reshape(3, 1) + tvec).reshape(3)
        axis_cam = R_obj_cam @ axis_obj

        if target_cam[2] <= 0.01:
            return None, None

        port_pos = cam_R @ target_cam + cam_pos
        insertion_axis = cam_R @ axis_cam
        insertion_axis /= max(np.linalg.norm(insertion_axis), 1e-9)

        return port_pos, insertion_axis
