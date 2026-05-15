#!/usr/bin/env bash
# run_sfp_insertion.sh — Run the trained SFP plug insertion policy.
#
# Terminal A — start the simulation (keep it running):
#   bash ~/ws_aic/src/aic/my_policy_node/scripts/run_sim_sfp.sh
#
# Terminal B — run this script:
#   cd ~/ws_aic/src/aic
#   bash my_policy_node/scripts/run_sfp_insertion.sh
#
# Stop with Ctrl+C in Terminal B, then Ctrl+C in Terminal A.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
AIC_DIR="$(dirname "$SCRIPT_DIR")"

echo "============================================"
echo " SFP Insertion — Trained Policy"
echo " Policy : my_policy_node.SFPInsertionPolicy"
echo " Working : $AIC_DIR"
echo " YOLO visual standoff : ${SFP_YOLO_APPROACH_STANDOFF_M:-0.100} m"
echo " YOLO handoff standoff: ${SFP_YOLO_HANDOFF_STANDOFF_M:-0.002} m"
echo " YOLO focal override  : ${SFP_YOLO_FOCAL_LENGTH_PX:-0.0} px (0 = CameraInfo)"
echo "============================================"

cd "$AIC_DIR"

SFP_YOLO_MODEL_PATH="${SFP_YOLO_MODEL_PATH:-}"
SFP_YOLO_CAD_KEYPOINTS_PATH="${SFP_YOLO_CAD_KEYPOINTS_PATH:-}"
SFP_YOLO_APPROACH_STANDOFF_M="${SFP_YOLO_APPROACH_STANDOFF_M:-0.100}"
SFP_YOLO_HANDOFF_STANDOFF_M="${SFP_YOLO_HANDOFF_STANDOFF_M:-0.002}"
SFP_YOLO_FOCAL_LENGTH_PX="${SFP_YOLO_FOCAL_LENGTH_PX:-0.0}"
SFP_YOLO_APPROACH_MAX_SPEED_MPS="${SFP_YOLO_APPROACH_MAX_SPEED_MPS:-0.05}"

source "$AIC_DIR/pixi_env_setup.sh"
export ROS_LOG_DIR="${ROS_LOG_DIR:-/tmp/roslog}"

if command -v pixi >/dev/null 2>&1; then
  pixi run ros2 run aic_model aic_model \
    --ros-args \
    -p use_sim_time:=true \
    -p policy:=my_policy_node.SFPInsertionPolicy \
    -p yolo_model_path:="$SFP_YOLO_MODEL_PATH" \
    -p yolo_cad_keypoints_path:="$SFP_YOLO_CAD_KEYPOINTS_PATH" \
    -p yolo_approach_standoff_m:="$SFP_YOLO_APPROACH_STANDOFF_M" \
    -p yolo_handoff_standoff_m:="$SFP_YOLO_HANDOFF_STANDOFF_M" \
    -p yolo_focal_length_px:="$SFP_YOLO_FOCAL_LENGTH_PX" \
    -p yolo_approach_max_speed_mps:="$SFP_YOLO_APPROACH_MAX_SPEED_MPS"
else
  source "$AIC_DIR/.pixi/envs/default/setup.sh"
  ros2 run aic_model aic_model \
    --ros-args \
    -p use_sim_time:=true \
    -p policy:=my_policy_node.SFPInsertionPolicy \
    -p yolo_model_path:="$SFP_YOLO_MODEL_PATH" \
    -p yolo_cad_keypoints_path:="$SFP_YOLO_CAD_KEYPOINTS_PATH" \
    -p yolo_approach_standoff_m:="$SFP_YOLO_APPROACH_STANDOFF_M" \
    -p yolo_handoff_standoff_m:="$SFP_YOLO_HANDOFF_STANDOFF_M" \
    -p yolo_focal_length_px:="$SFP_YOLO_FOCAL_LENGTH_PX" \
    -p yolo_approach_max_speed_mps:="$SFP_YOLO_APPROACH_MAX_SPEED_MPS"
fi
