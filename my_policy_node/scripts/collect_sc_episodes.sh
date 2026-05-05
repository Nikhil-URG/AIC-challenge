#!/usr/bin/env bash
# collect_sc_episodes.sh
#
# Collect 50 SC plug insertion demonstrations (Trial 3).
# Saves a LeRobot dataset locally at ~/datasets/sc_insertion.
#
# BEFORE RUNNING:
#   Terminal A — start the simulation runner (auto-restarts after each session):
#     bash ~/ws_aic/src/aic/my_policy_node/scripts/run_sim_sc.sh
#
#   Terminal B (this script) — run from host:
#     cd ~/ws_aic/src/aic
#     bash my_policy_node/scripts/collect_sc_episodes.sh
#
#   Both scripts loop automatically until collection is complete.
#   Stop Terminal A with Ctrl+C once Terminal B reports "Collection finished."
#
# AFTER COLLECTION — push to HuggingFace (optional):
#   cd ~/ws_aic/src/aic
#   pixi run python my_policy_node/scripts/push_dataset_to_hub.py \
#     --root ~/datasets/sc_insertion \
#     --repo-id YOUR_HF_USERNAME/sc_insertion_demos

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
AIC_DIR="$(dirname "$SCRIPT_DIR")"
WS_DIR="$(dirname "$(dirname "$AIC_DIR")")"

NUM_EPISODES=50
OUTPUT_DIR="$HOME/datasets/sc_insertion"
REPO_ID="local/sc_insertion_demos"   # change before pushing to HF

echo "============================================================"
echo " SC Plug Insertion Data Collection"
echo " Episodes  : $NUM_EPISODES"
echo " Output    : $OUTPUT_DIR"
echo " Working in: $AIC_DIR"
echo "============================================================"

cd "$AIC_DIR"

# Loop: each aic_engine session runs 1 SC trial then shuts down the policy
# node.  Resume the dataset across sessions until NUM_EPISODES are collected.
# Timeout = 1 trial × 3 min + 2 min margin = 5 min per session.
SESSION_TIMEOUT_S=300

while true; do
  timeout "$SESSION_TIMEOUT_S" \
    pixi run ros2 run aic_model aic_model \
      --ros-args \
      -p use_sim_time:=true \
      -p policy:=my_policy_node.InsertionDataCollector \
      -p num_episodes:="$NUM_EPISODES" \
      -p output_dir:="$OUTPUT_DIR" \
      -p repo_id:="$REPO_ID" \
      -p plug_type_filter:=sc || true

  TOTAL=0
  if [ -f "$OUTPUT_DIR/meta/info.json" ]; then
    TOTAL=$(python3 -c \
      "import json; print(json.load(open('$OUTPUT_DIR/meta/info.json')).get('total_episodes', 0))" \
      2>/dev/null || echo 0)
  fi
  echo "Episodes saved: $TOTAL / $NUM_EPISODES"
  [ "$TOTAL" -ge "$NUM_EPISODES" ] && break

  echo "Waiting for Terminal A simulation to restart..."
  sleep 5
done

echo ""
echo "Collection finished. Dataset at: $OUTPUT_DIR"
echo ""
echo "To push to HuggingFace, set REPO_ID and run:"
echo "  pixi run python my_policy_node/scripts/push_dataset_to_hub.py \\"
echo "    --root $OUTPUT_DIR \\"
echo "    --repo-id YOUR_HF_USERNAME/sc_insertion_demos"
