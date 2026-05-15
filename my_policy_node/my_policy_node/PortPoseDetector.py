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

Model classes from aic_pose_model training:
    0  SC_SKL   - SC fibre port
    1  SPF_SKL  - SFP small-form-factor pluggable network port

Depth is estimated by solving a Perspective-n-Point problem from the detected
2D keypoints and measured 3D port datums.
"""

import json
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import cv2
import numpy as np
import yaml

# Only report detections above this confidence
_CONF_THRESH = 0.40

CLASS_SC  = 0  # SC_SKL
CLASS_SFP = 1  # SPF_SKL

_CLASS_NAMES = {
    CLASS_SC: "SC_SKL",
    CLASS_SFP: "SPF_SKL",
}

# The current YOLO head emits 17 keypoint slots. For SC labels, the first 12
# slots are physical points and the remaining 5 are zero-visibility padding.
# For SFP labels, all 17 slots are intended to be physical CAD points. The
# built-in SFP table currently has 16 measured rows, so the 17th prediction is
# skipped unless a CAD keypoint config supplies it.
_TASK_KEYPOINT_COUNTS = {
    CLASS_SC: 12,
    CLASS_SFP: 17,
}

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

_MIN_PNP_POINTS = 4
_KPT_CONF_THRESH = 0.30
_RANSAC_REPROJ_ERROR_PX = 6.0


def _unit_scale_to_m(units: str) -> float:
    normalized = units.strip().lower()
    if normalized in {"m", "meter", "meters", "metre", "metres"}:
        return 1.0
    if normalized in {"mm", "millimeter", "millimeters", "millimetre", "millimetres"}:
        return 1e-3
    raise ValueError(f"Unsupported CAD units {units!r}. Use 'm' or 'mm'.")


def _load_structured(path: Path) -> dict:
    with path.open("r", encoding="utf-8") as handle:
        if path.suffix.lower() == ".json":
            return json.load(handle)
        if path.suffix.lower() in {".yaml", ".yml"}:
            return yaml.safe_load(handle)
    raise ValueError(f"Unsupported CAD keypoint file type: {path}")


def _class_id_from_key(key: Any) -> Optional[int]:
    text = str(key).strip()
    if text in {"0", "1"}:
        return int(text)
    normalized = text.upper().replace("-", "_")
    aliases = {
        "SC": CLASS_SC,
        "SC_SKL": CLASS_SC,
        "SC_PORT": CLASS_SC,
        "SFP": CLASS_SFP,
        "SPF": CLASS_SFP,
        "SFP_SKL": CLASS_SFP,
        "SPF_SKL": CLASS_SFP,
        "SFP_PORT": CLASS_SFP,
        "SFP_NIC": CLASS_SFP,
    }
    return aliases.get(normalized)


def _payload_value(payload: Any, keys: tuple[str, ...]) -> Any:
    if not isinstance(payload, dict):
        return None
    for key in keys:
        if key in payload:
            value = payload[key]
            if isinstance(value, dict) and "data" in value:
                return value["data"]
            return value
    return None


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

    def __init__(
        self,
        model_path: Path,
        cad_keypoints_path: Optional[Path] = None,
        conf_thresh: float = _CONF_THRESH,
        keypoint_conf_thresh: float = _KPT_CONF_THRESH,
        ransac_reproj_error_px: float = _RANSAC_REPROJ_ERROR_PX,
    ) -> None:
        from ultralytics import YOLO  # lazy import — keeps ROS startup fast
        self._model = YOLO(str(model_path))
        self._conf_thresh = float(conf_thresh)
        self._kpt_conf_thresh = float(keypoint_conf_thresh)
        self._ransac_reproj_error_px = float(ransac_reproj_error_px)
        self._object_points_m = {
            class_id: points.copy()
            for class_id, points in _OBJECT_POINTS_M.items()
        }
        self._target_points_m = {
            class_id: point.copy()
            for class_id, point in _TARGET_POINTS_M.items()
        }
        self._insertion_axis_obj = {
            class_id: axis.copy()
            for class_id, axis in _INSERTION_AXIS_OBJ.items()
        }
        if cad_keypoints_path is not None:
            self._load_cad_keypoints(cad_keypoints_path)

    def _load_cad_keypoints(self, path: Path) -> None:
        """
        Override built-in CAD keypoints from JSON/YAML.

        Accepted compact format:
            {"units": "mm", "classes": {"SC_SKL": [[...]], "SPF_SKL": [[...]]}}

        Accepted expanded per-class format:
            {
              "units": "mm",
              "classes": {
                "SPF_SKL": {
                  "points": [[...]],
                  "target_point": [...],
                  "insertion_axis": [...]
                }
              }
            }
        """
        if not path.is_file():
            raise FileNotFoundError(path)

        data = _load_structured(path)
        if not isinstance(data, dict):
            raise ValueError(f"CAD keypoint config must be a mapping: {path}")

        default_units = str(data.get("units", "m"))
        classes = data.get("classes", data)
        if not isinstance(classes, dict):
            raise ValueError(f"CAD keypoint config must contain a class mapping: {path}")

        for class_key, payload in classes.items():
            class_id = _class_id_from_key(class_key)
            if class_id is None:
                continue

            class_units = default_units
            if isinstance(payload, dict) and "units" in payload:
                class_units = str(payload["units"])
            scale = _unit_scale_to_m(class_units)

            raw_points = _payload_value(
                payload,
                ("points", "object_points", "keypoints", "keypoints_3d"),
            )
            if raw_points is None and not isinstance(payload, dict):
                raw_points = payload
            if raw_points is None:
                raise ValueError(f"Missing CAD points for class {class_key} in {path}")

            points = np.asarray(raw_points, dtype=np.float64)
            if points.ndim != 2 or points.shape[1] != 3 or len(points) < _MIN_PNP_POINTS:
                raise ValueError(
                    f"CAD points for {class_key} must have shape (N, 3) with N >= "
                    f"{_MIN_PNP_POINTS}; got {points.shape}"
                )
            if not np.isfinite(points).all():
                raise ValueError(f"CAD points for {class_key} contain non-finite values")
            self._object_points_m[class_id] = points * scale

            raw_target = _payload_value(payload, ("target_point", "target", "port_target"))
            if raw_target is not None:
                target = np.asarray(raw_target, dtype=np.float64).reshape(3)
                self._target_points_m[class_id] = target * scale

            raw_axis = _payload_value(payload, ("insertion_axis", "axis"))
            if raw_axis is not None:
                axis = np.asarray(raw_axis, dtype=np.float64).reshape(3)
                norm = np.linalg.norm(axis)
                if norm < 1e-9:
                    raise ValueError(f"Insertion axis for {class_key} is zero length")
                self._insertion_axis_obj[class_id] = axis / norm

    # ── Model discovery ───────────────────────────────────────────────────────

    @staticmethod
    def _artifact_candidates(filename: str) -> list[Path]:
        pkg_root = Path(__file__).resolve().parent.parent
        cwd = Path.cwd()
        candidates = [
            pkg_root / "yolo_pose_model" / "aic_output" / filename,
            pkg_root / "pose_model" / filename,
            cwd / "yolo_pose_model" / "aic_output" / filename,
            cwd / "my_policy_node" / "yolo_pose_model" / "aic_output" / filename,
            Path.home() / "ws_aic/src/aic/my_policy_node/yolo_pose_model/aic_output" / filename,
        ]
        candidates.extend(
            parent / "my_policy_node" / "yolo_pose_model" / "aic_output" / filename
            for parent in cwd.parents
        )
        return candidates

    @staticmethod
    def find_model() -> Optional[Path]:
        """Return the path to best.pt if found in any standard location."""
        for c in PortPoseDetector._artifact_candidates("best.pt"):
            if c.is_file():
                return c
        return None

    @staticmethod
    def find_cad_keypoints() -> Optional[Path]:
        """Return the path to cad_keypoints.yaml if found beside the YOLO model."""
        for c in PortPoseDetector._artifact_candidates("cad_keypoints.yaml"):
            if c.is_file():
                return c
        for c in PortPoseDetector._artifact_candidates("cad_keypoints.yml"):
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
                if conf < self._conf_thresh:
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

    def _candidate_indices(self, class_id: int, kp_len: int, conf_len: int) -> np.ndarray:
        object_points = self._object_points_m.get(class_id)
        if object_points is None:
            return np.empty((0,), dtype=np.int32)
        count = min(
            int(_TASK_KEYPOINT_COUNTS.get(class_id, len(object_points))),
            len(object_points),
            kp_len,
            conf_len,
        )
        return np.arange(count, dtype=np.int32)

    def _valid_correspondences(
        self,
        detection: dict,
        img_w: int,
        img_h: int,
    ) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
        class_id = int(detection["class_id"])
        object_points_all = self._object_points_m.get(class_id)
        if object_points_all is None:
            return (
                np.empty((0, 3), dtype=np.float64),
                np.empty((0, 2), dtype=np.float64),
                np.empty((0,), dtype=np.float64),
                np.empty((0,), dtype=np.int32),
            )

        kp_px = np.asarray(detection["kp_px"], dtype=np.float64)
        kp_conf = np.asarray(detection["kp_conf"], dtype=np.float64)
        point_indices = self._candidate_indices(class_id, len(kp_px), len(kp_conf))
        if len(point_indices) == 0:
            return (
                np.empty((0, 3), dtype=np.float64),
                np.empty((0, 2), dtype=np.float64),
                np.empty((0,), dtype=np.float64),
                point_indices,
            )

        image_points = kp_px[point_indices]
        point_conf = kp_conf[point_indices]
        valid = (
            (point_conf >= self._kpt_conf_thresh)
            & np.isfinite(image_points).all(axis=1)
            & (image_points[:, 0] >= 0.0)
            & (image_points[:, 0] < float(img_w))
            & (image_points[:, 1] >= 0.0)
            & (image_points[:, 1] < float(img_h))
            & (np.linalg.norm(image_points, axis=1) > 1.0)
        )
        valid_indices = point_indices[valid]
        return (
            object_points_all[valid_indices],
            kp_px[valid_indices],
            kp_conf[valid_indices],
            valid_indices,
        )

    def detection_quality(
        self,
        detection: dict,
        img_w: int,
        img_h: int,
    ) -> tuple[int, float, float]:
        """Rank by usable PnP keypoint count, then mean kp confidence, then box confidence."""
        _, _, point_conf, _ = self._valid_correspondences(detection, img_w, img_h)
        usable = int(len(point_conf))
        mean_kp_conf = float(np.mean(point_conf)) if usable else 0.0
        det_conf = float(detection.get("conf", 0.0))
        return usable, mean_kp_conf, det_conf

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
        target_obj = self._target_points_m.get(class_id)
        axis_obj = self._insertion_axis_obj.get(class_id)
        if target_obj is None or axis_obj is None:
            return None, None

        object_points, image_points, point_conf, used_indices = self._valid_correspondences(
            detection, img_w, img_h
        )
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
                reprojectionError=self._ransac_reproj_error_px,
                iterationsCount=100,
                confidence=0.99,
            )
            if not ok or rvec is None or tvec is None:
                return None, None
            if inliers is None or len(inliers) < _MIN_PNP_POINTS:
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
            rank = np.linalg.matrix_rank(object_points - object_points.mean(axis=0))
            pnp_flag = cv2.SOLVEPNP_IPPE if rank <= 2 else cv2.SOLVEPNP_EPNP
            ok, rvec, tvec = cv2.solvePnP(
                object_points,
                image_points,
                K64,
                D,
                flags=pnp_flag,
            )
            if not ok or rvec is None or tvec is None:
                return None, None

        projected, _ = cv2.projectPoints(object_points, rvec, tvec, K64, D)
        projected = projected.reshape(-1, 2)
        reproj_errors = np.linalg.norm(projected - image_points, axis=1)
        if inliers is not None and len(inliers):
            inlier_local = inliers.reshape(-1)
        else:
            inlier_local = np.arange(len(object_points), dtype=np.int32)
        detection["pnp_used_indices"] = used_indices.tolist()
        detection["pnp_inlier_indices"] = used_indices[inlier_local].tolist()
        detection["pnp_valid_points"] = int(len(object_points))
        detection["pnp_inliers"] = int(len(inlier_local))
        detection["pnp_mean_kp_conf"] = float(np.mean(point_conf)) if len(point_conf) else 0.0
        detection["pnp_reprojection_error_px"] = (
            float(np.mean(reproj_errors[inlier_local]))
            if len(inlier_local)
            else float(np.mean(reproj_errors))
        )

        R_obj_cam, _ = cv2.Rodrigues(rvec)
        target_cam = (R_obj_cam @ target_obj.reshape(3, 1) + tvec).reshape(3)
        axis_cam = R_obj_cam @ axis_obj

        if target_cam[2] <= 0.01:
            return None, None

        port_pos = cam_R @ target_cam + cam_pos
        insertion_axis = cam_R @ axis_cam
        insertion_axis /= max(np.linalg.norm(insertion_axis), 1e-9)

        return port_pos, insertion_axis
