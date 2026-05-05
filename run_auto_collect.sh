#!/bin/bash
# Setup and run automated data collection

export AIC_RESULTS_DIR=$HOME/aic_results

# Terminal 1: Zenoh
echo "=== Terminal 1: Starting Zenoh router ==="
pixi run ros2 run rmw_zenoh_cpp rmw_zenohd &
ZENOH_PID=$!

# Wait for Zenoh
sleep 2

# Terminal 2: Build (if needed)
echo "=== Building workspace ==="
source /opt/ros/kilted/setup.bash
colcon build --cmake-args -DCMAKE_BUILD_TYPE=Release --merge-install --symlink-install --packages-ignore lerobot_robot_aic
source install/setup.bash

# Terminal 3: Launch simulation
echo "=== Terminal 3: Launching simulation ==="
pixi run ros2 launch aic_bringup aic_gz_bringup.launch.py &
SIM_PID=$!

sleep 5

# Terminal 4: Run data collector policy
echo "=== Terminal 4: Running AutoDataCollector ==="
pixi run ros2 run aic_model aic_model --ros-args \
  -p use_sim_time:=true \
  -p policy:=my_policy_node.AutoDataCollector &
MODEL_PID=$!

# Terminal 5: Run engine
echo "=== Terminal 5: Running aic_engine ==="
pixi run ros2 run aic_engine aic_engine --ros-args \
  -p config_file_path:=$(ros2 pkg prefix aic_engine)/share/aic_engine/config/sample_config.yaml \
  -p model_node_name:=aic_model \
  -p ground_truth:=true \
  -p use_sim_time:=true

# Cleanup
kill $MODEL_PID $SIM_PID $ZENOH_PID 2>/dev/null
echo "All done!"