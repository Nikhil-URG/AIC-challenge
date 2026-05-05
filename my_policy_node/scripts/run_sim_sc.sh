#!/usr/bin/env bash
# run_sim_sc.sh — Terminal A for SC data collection.
#
# Run this in a separate terminal BEFORE starting collect_sc_episodes.sh.
# Uses the default simulation config (all 3 trials). The collector script
# passes plug_type_filter:=sc so SFP trials are skipped automatically.
#
# Usage:
#   bash ~/ws_aic/src/aic/my_policy_node/scripts/run_sim_sc.sh
#
# Stop with Ctrl+C once collect_sc_episodes.sh reports "Collection finished."

set -euo pipefail

echo "=========================================="
echo " SC Simulation Runner (Terminal A)"
echo " Press Ctrl+C to stop."
echo "=========================================="

INNER=$(mktemp /tmp/aic_sim_XXXXXX.sh)
trap "rm -f $INNER" EXIT

cat > "$INNER" << 'EOF'
#!/bin/bash -l
while true; do
  /entrypoint.sh \
    spawn_task_board:=false \
    spawn_cable:=false \
    attach_cable_to_gripper:=true \
    ground_truth:=true \
    start_aic_engine:=true
  echo "Simulation ended -- restarting in 3 s..."
  sleep 3
done
EOF
chmod +x "$INNER"

exec distrobox enter -r aic_eval -- bash -l "$INNER"
