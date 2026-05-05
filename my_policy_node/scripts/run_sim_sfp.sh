#!/usr/bin/env bash
# run_sim_sfp.sh — Terminal A for SFP data collection.
#
# Run this in a separate terminal BEFORE starting collect_sfp_episodes.sh.
# It loops the simulation automatically: when aic_engine finishes its 2 SFP
# trials, Gazebo shuts down and this script restarts it after 3 seconds.
#
# Usage:
#   bash ~/ws_aic/src/aic/my_policy_node/scripts/run_sim_sfp.sh
#
# Stop with Ctrl+C once collect_sfp_episodes.sh reports "Collection finished."

set -euo pipefail

SFP_CONFIG="$HOME/ws_aic/src/aic/aic_engine/config/sfp_only_config.yaml"

echo "=========================================="
echo " SFP Simulation Runner (Terminal A)"
echo " Config: $SFP_CONFIG"
echo " Press Ctrl+C to stop."
echo "=========================================="

# Write the loop script to /tmp — distrobox shares the host filesystem.
INNER=$(mktemp /tmp/aic_sim_XXXXXX.sh)
trap "rm -f $INNER" EXIT

cat > "$INNER" << EOF
#!/bin/bash -l
while true; do
  /entrypoint.sh \\
    spawn_task_board:=false \\
    spawn_cable:=false \\
    attach_cable_to_gripper:=true \\
    ground_truth:=true \\
    start_aic_engine:=true \\
    aic_engine_config_file:=$SFP_CONFIG
  echo "Simulation ended -- restarting in 3 s..."
  sleep 3
done
EOF
chmod +x "$INNER"

exec distrobox enter -r aic_eval -- bash -l "$INNER"
