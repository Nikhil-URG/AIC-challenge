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
echo "============================================"

cd "$AIC_DIR"

pixi run ros2 run aic_model aic_model \
  --ros-args \
  -p use_sim_time:=true \
  -p policy:=my_policy_node.SFPInsertionPolicy
