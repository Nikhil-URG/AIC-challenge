# SFP / SC Plug Insertion Policy

Imitation-learning policy for inserting SFP (small form-factor pluggable) and SC fibre plugs
into their respective sockets on the AIC task board.  Uses a pre-trained
[ACT (Action Chunking Transformer)](https://tonyzhaozh.github.io/aloha/) model with a
ground-truth alignment phase and a tiered stall-recovery strategy.

---

## Running the policy

Two terminals are required.

### Terminal A — simulation

```bash
bash ~/ws_aic/src/aic/my_policy_node/scripts/run_sim_sfp.sh
```

This starts the Gazebo simulation inside the `aic_eval` distrobox with:

- `ground_truth:=true` — publishes task-board TF frames required by the alignment phase
- `attach_cable_to_gripper:=true` — cable already held at start
- Auto-restart loop — when `aic_engine` finishes its trials Gazebo shuts down and restarts after 3 s

Keep this terminal running for the full session.

### Terminal B — policy node

```bash
cd ~/ws_aic/src/aic
bash my_policy_node/scripts/run_sfp_insertion.sh
```

This runs:

```bash
pixi run ros2 run aic_model aic_model \
  --ros-args \
  -p use_sim_time:=true \
  -p policy:=my_policy_node.SFPInsertionPolicy
```

Useful YOLO/PnP runtime parameters are exposed by the same launch path:

```bash
SFP_YOLO_APPROACH_STANDOFF_M=0.100 \
SFP_YOLO_HANDOFF_STANDOFF_M=0.002 \
SFP_YOLO_FOCAL_LENGTH_PX=0.0 \
bash my_policy_node/scripts/run_sfp_insertion.sh
```

`SFP_YOLO_FOCAL_LENGTH_PX=0.0` means "use the focal length from each
`CameraInfo` message". The YOLO weights and CAD keypoint YAML are discovered
by the policy code from `my_policy_node/yolo_pose_model/aic_output/`.

Stop with `Ctrl+C` in Terminal B first, then Terminal A.

---

## Trained model

| Item | Value |
|------|-------|
| Location | `policy/sfp_insertion_demos_act_20260504_184125_steplast/pretrained_model/` |
| Architecture | ACT (Action Chunking Transformer) via lerobot 0.5.x |
| Inputs | Left / centre / right camera images (scaled ×0.25), TCP pose + velocity + error, joint positions (26-dim state), wrist force (3-dim) |
| Outputs | 7-dim action: Cartesian velocity `[vx, vy, vz, ωx, ωy, ωz, gripper]` |
| Normalisation | Manual — stats loaded from `policy_preprocessor_step_3_normalizer_processor.safetensors`; `select_action()` expects pre-normalised inputs and returns normalised outputs |

The policy path is resolved automatically in priority order:
1. Relative to `SFPInsertionPolicy.py` (`../../policy/`)
2. ROS2 ament share directory
3. `~/ws_aic/src/aic/my_policy_node/policy/` (fallback)

If multiple `pretrained_model/` directories exist under `policy/`, the most recently modified one is used.

---

## Implementation — `SFPInsertionPolicy`

**File:** `my_policy_node/SFPInsertionPolicy.py`

### High-level flow

```
insert_cable()
  │
  ├─ _tare()                    Zero F/T sensor at trial start
  ├─ _wait_for_tf()             Check for task-board TF (ground_truth mode)
  │
  ├─ _gt_approach()             Phase 1: KP velocity alignment (position + orientation)
  │
  ├─ _yolo_detect_tf()          No-GT fallback: YOLO pose + CAD PnP across 3 cameras
  ├─ _approach_to_yolo_pos()    Move to visual standoff, re-detect, then hand off
  │
  └─ for attempt in 0..10:
       ├─ attempt 0        → plain ACT
       ├─ attempts 1-2     → 2 mm backoff + realign → plain ACT
       ├─ attempts 3-5     → 3 mm backoff + realign → ACT + lateral-hold overlay
       └─ attempts 6-10    → 3 mm backoff → wiggle entry → ACT
```

### Phase 1 — Ground-truth approach (`_gt_approach`)

Replicates `InsertionDataCollector._approach()` exactly:

- Looks up port, entrance, and plug TF frames from the simulation ground-truth
- Computes the **insertion axis** as `(port_pos − entrance_pos) / ‖…‖`
- Sets target 8 mm before the entrance along `−axis`
- Commands velocity `v = KP_pos × pos_err + KP_orient × rot_err` at 10 Hz
- Corrects **both position and orientation simultaneously** (matching training distribution)
- Declares "settled" after 20 consecutive ticks with `‖pos_err‖ < 2 mm` and `‖rot_err‖ < 1.4°`
- Times out after 60 s and continues to ACT from current position

| Constant | Value | Description |
|----------|-------|-------------|
| `_APPROACH_KP` | 4.0 | Position P-gain |
| `_APPROACH_ORIENT_KP` | 3.0 | Orientation P-gain |
| `_APPROACH_Z_ABOVE` | 8 mm | Standoff distance before entrance |
| `_APPROACH_DONE_M` | 2 mm | Position convergence threshold |
| `_APPROACH_DONE_RAD` | 0.025 rad (~1.4°) | Orientation convergence threshold |
| `_APPROACH_SETTLED_TICKS` | 20 | Ticks both stable = done |

### Visual 6D pose fallback (`ground_truth:=false`)

When task-board TF is not available, `SFPInsertionPolicy` uses
`PortPoseDetector`:

- Runs the YOLO pose model on left, center, and right images
- Chooses the camera by usable CAD-matched keypoint count first, then PnP
  inliers, keypoint confidence, and detection confidence
- Uses 12 physical SC keypoints or up to 17 SFP keypoints, depending on the
  task class and available CAD rows
- Uses the camera matrix/distortion from each `CameraInfo`; optionally overrides
  focal length with `yolo_focal_length_px`
- Solves PnP in the camera frame, transforms the result through camera TF into
  `base_link`, and publishes RViz markers/TF for debugging
- Moves slowly to `yolo_approach_standoff_m` (default 100 mm), takes a second
  image for a refined estimate, then moves to `yolo_handoff_standoff_m` before
  ACT starts

### Phase 2 — ACT inference loop (`_act_phase`)

Runs the trained model at **10 Hz**:

1. **Observation preparation** — converts ROS `Observation` message to a dict of normalised tensors (3 camera images + state + wrist force)
2. **Inference** — `policy.select_action(obs)` → normalised action → manual denormalise → `[vx, vy, vz, ωx, ωy, ωz]`
3. **Command** — `MotionUpdate` in `MODE_VELOCITY` with Cartesian impedance control (stiffness diag `[100,100,100,50,50,50]`, damping `[40,40,40,15,15,15]`)

**Stall detection** (position-based, not force-based):

- Tracks axial progress of the plug TF along the insertion axis
- Rate below `0.5 mm/s` for `4 s` → stall declared → returns `"stall"` to trigger recovery
- First `5 s` of each ACT phase are a **grace period** (no stall check) to allow lateral/orientation correction before axial push begins

**Close-range zone** (`dist_remaining < 10 mm`):

- Stall detection suppressed — plug is expected to stop when fully seated
- When `dist_remaining ≤ 2 mm` → stop and declare success immediately

> Force is intentionally **not** used for stall detection. The simulated wrist sensor registers inertial spikes whenever the arm accelerates, making force unreliable as a realignment trigger. The F/T sensor is only tared at the start of each trial.

### Recovery strategy

| Attempt | Pullback | Mode |
|---------|----------|------|
| 1–2 | 2 mm | Plain ACT |
| 3–5 | 3 mm | ACT + **lateral-hold overlay** |
| 6–10 | 3 mm | **Wiggle entry** → ACT |

**Lateral-hold overlay (attempts 3–5)**

Mirrors `InsertionDataCollector`'s `INSERT_HOLD_KP × lat_err`.  Computes the plug's lateral drift (perpendicular to the insertion axis) relative to where the ACT phase started and adds a restoring velocity on top of ACT's output before clipping:

```
lat_drift = (plug_pos − lat_ref) − axial_component × axis
lin += 10.0 × (−lat_drift)
```

**Wiggle entry (attempts 6–10)**

When repeated alignment + ACT still fails:

1. `_gt_approach` with `z_above = 1 mm` (plug positioned flush with entrance)
2. Circular oscillation in the plane perpendicular to the insertion axis (1.5 mm radius, 1.5 Hz) with a 3 mm/s axial push — sweeps through all lateral offsets
3. Once plug crosses the 10 mm close-range threshold, oscillation stops and ACT takes over

### F/T tare

`std_srvs/Trigger` is called on `/aic_controller/tare_force_torque_sensor` at the start of every trial (`insert_cable()` entry) to zero the sensor at the robot's home configuration.

### Cartesian impedance parameters

Identical to `InsertionDataCollector` throughout all phases:

| Parameter | Value |
|-----------|-------|
| Stiffness (lin) | 100 N/m per axis |
| Stiffness (rot) | 50 Nm/rad per axis |
| Damping (lin) | 40 Ns/m per axis |
| Damping (rot) | 15 Nms/rad per axis |
| Wrench feedback gains | `[0.5, 0.5, 0.5, 0, 0, 0]` |

---

## File layout

```
my_policy_node/
├── my_policy_node/
│   ├── SFPInsertionPolicy.py     # Main policy (this document)
│   ├── InsertionDataCollector.py # Training data collector (reference)
│   ├── CableInsertionPolicy.py   # Earlier HuggingFace-based policy
│   └── ...
├── scripts/
│   ├── run_sim_sfp.sh            # Terminal A: start simulation
│   ├── run_sfp_insertion.sh      # Terminal B: run policy node
│   ├── run_sim_sc.sh             # Terminal A variant for SC data collection
│   ├── collect_sfp_episodes.sh   # Data collection for SFP
│   └── collect_sc_episodes.sh    # Data collection for SC
├── notebooks/
│   └── train_policy_cluster.ipynb  # ACT training notebook (JupyterHub)
└── policy/
    └── sfp_insertion_demos_act_20260504_184125_steplast/
        └── pretrained_model/     # Weights + normalisation stats
```
