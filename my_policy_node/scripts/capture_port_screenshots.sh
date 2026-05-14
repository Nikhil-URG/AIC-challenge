#!/usr/bin/env bash
# capture_port_screenshots.sh — Capture centre-camera screenshots for YOLO annotation.
#
# aic_engine calls insert_cable once per port task.  Each port saves its
# images to its own subfolder under OUT_BASE:
#
#   pose_data/screenshots/
#     sfp_port_0/   000000.png  ...
#     sfp_port_1/   000000.png  ...
#     sc_port/      000000.png  ...
#
# Usage — collect ALL port types in one sim session:
#   Terminal A:  bash run_sim_sfp.sh
#   Terminal B:  bash capture_port_screenshots.sh
#
# Usage — collect only one specific port:
#   PLUG_TYPE=sfp_port_0 bash capture_port_screenshots.sh
#   PLUG_TYPE=sfp_port_1 bash capture_port_screenshots.sh
#   PLUG_TYPE=sc_port    bash capture_port_screenshots.sh
#
# Override number of images per port (default 50):
#   N_SAMPLES=80 bash capture_port_screenshots.sh

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
AIC_DIR="$(dirname "$SCRIPT_DIR")"

N_SAMPLES="${N_SAMPLES:-50}"
OUT_BASE="${OUT_BASE:-$HOME/ws_aic/src/aic/my_policy_node/pose_data/screenshots}"
PLUG_TYPE="${PLUG_TYPE:-}"   # empty = collect all port types

echo "============================================"
echo " Port Screenshot Capture"
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
  -p policy:=my_policy_node.ScreenshotCollector
