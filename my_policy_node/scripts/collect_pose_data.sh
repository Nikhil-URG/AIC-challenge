#!/usr/bin/env bash
# collect_pose_data.sh — Collect labeled images for port pose estimation.
#
# Terminal A — start the simulation (keep it running):
#   bash ~/ws_aic/src/aic/my_policy_node/scripts/run_sim_sfp.sh
#
# Terminal B — run this script:
#   cd ~/ws_aic/src/aic
#   bash my_policy_node/scripts/collect_pose_data.sh
#
# Collected data is written to:
#   ~/ws_aic/src/aic/my_policy_node/pose_data/
#
# Override the output directory:
#   POSE_DATA_DIR=/path/to/dir bash my_policy_node/scripts/collect_pose_data.sh
#
# Stop with Ctrl+C in Terminal B, then Ctrl+C in Terminal A.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
AIC_DIR="$(dirname "$SCRIPT_DIR")"

POSE_DATA_DIR="${POSE_DATA_DIR:-$HOME/ws_aic/src/aic/my_policy_node/pose_data}"
POSE_SAMPLES_PER_TRIAL="${POSE_SAMPLES_PER_TRIAL:-200}"

echo "============================================"
echo " SFP / SC Pose Data Collection"
echo " Policy  : my_policy_node.PoseDataCollector"
echo " Output  : $POSE_DATA_DIR"
echo " Samples : $POSE_SAMPLES_PER_TRIAL per trial"
echo " Working : $AIC_DIR"
echo "============================================"
echo ""
echo " Override samples: POSE_SAMPLES_PER_TRIAL=500 bash $0"
echo ""

cd "$AIC_DIR"

POSE_DATA_DIR="$POSE_DATA_DIR" \
POSE_SAMPLES_PER_TRIAL="$POSE_SAMPLES_PER_TRIAL" \
pixi run ros2 run aic_model aic_model \
  --ros-args \
  -p use_sim_time:=true \
  -p policy:=my_policy_node.PoseDataCollector
