#!/usr/bin/env bash
# collect_yolo_labels.sh — Capture images + YOLO-pose labels via sim TF.
#
# PoseAutoLabeler moves to random viewpoints around each port, captures the
# centre-camera image, projects the known 3D keypoints into 2D pixel coords,
# and writes a 20-column YOLO-pose label file alongside each image.
#
# Output:
#   pose_data/yolo_labeled/
#     sfp_port_0/  images/*.png  labels/*.txt
#     sfp_port_1/  images/*.png  labels/*.txt
#     sc_port/     images/*.png  labels/*.txt
#     data.yaml
#
# Usage — collect all port types in one session:
#   Terminal A:  bash scripts/run_sim_sfp.sh
#   Terminal B:  bash scripts/collect_yolo_labels.sh
#
# Collect only one port type:
#   PLUG_TYPE=sfp_port_0 bash scripts/collect_yolo_labels.sh
#
# Override samples per port (default 100):
#   N_SAMPLES=200 bash scripts/collect_yolo_labels.sh
#
# After collecting, review labels:
#   python scripts/review_yolo_labels.py pose_data/yolo_labeled

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
AIC_DIR="$(dirname "$SCRIPT_DIR")"

N_SAMPLES="${N_SAMPLES:-100}"
OUT_BASE="${OUT_BASE:-$HOME/ws_aic/src/aic/my_policy_node/pose_data/yolo_labeled}"
PLUG_TYPE="${PLUG_TYPE:-}"

echo "============================================"
echo " YOLO Pose Auto-Labeler"
echo " Filter    : ${PLUG_TYPE:-all port types}"
echo " Samples   : $N_SAMPLES per port"
echo " Output    : $OUT_BASE/<port_name>/"
echo "============================================"
echo ""

cd "$AIC_DIR"

N_SAMPLES="$N_SAMPLES" \
OUT_BASE="$OUT_BASE" \
PLUG_TYPE="$PLUG_TYPE" \
pixi run ros2 run aic_model aic_model \
  --ros-args \
  -p use_sim_time:=true \
  -p policy:=my_policy_node.PoseAutoLabeler \
  -p ground_truth:=true
