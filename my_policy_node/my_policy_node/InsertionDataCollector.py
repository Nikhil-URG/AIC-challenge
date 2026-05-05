"""
InsertionDataCollector — v1.0

Policy class that runs the full simple_insertion_node state machine
(align_xy → orient → hover → stabilize → insert) inside the aic_model
Policy interface, recording every frame as a LeRobot dataset.

Works for both SFP (Trial 1/2) and SC (Trial 3) tasks; the port/plug
frame names are resolved from the Task message at runtime.

Usage — collect 50 SFP episodes:
  pixi run ros2 run aic_model aic_model --ros-args \\
    -p use_sim_time:=true \\
    -p policy:=my_policy_node.InsertionDataCollector \\
    -p num_episodes:=50 \\
    -p output_dir:=datasets/sfp_insertion \\
    -p repo_id:=your_hf_username/sfp_insertion_demos

Usage — collect 50 SC episodes:
  pixi run ros2 run aic_model aic_model --ros-args \\
    -p use_sim_time:=true \\
    -p policy:=my_policy_node.InsertionDataCollector \\
    -p num_episodes:=50 \\
    -p output_dir:=datasets/sc_insertion \\
    -p repo_id:=your_hf_username/sc_insertion_demos

After collection, push to HuggingFace:
  pixi run python -c "
  from lerobot.datasets import LeRobotDataset
  ds = LeRobotDataset('your_hf_username/sfp_insertion_demos',
                      root='datasets/sfp_insertion')
  ds.push_to_hub()
  "
"""

import math
import time
import random
import shutil
import numpy as np
from pathlib import Path
from typing import Optional

import rclpy
from rclpy.node import Node
from rclpy.time import Time
from rclpy.duration import Duration
from tf2_ros import Buffer, TransformListener, TransformException
from geometry_msgs.msg import Twist, Wrench, Vector3
from std_srvs.srv import Trigger

from aic_control_interfaces.msg import MotionUpdate, TrajectoryGenerationMode
from aic_model.policy import (
    Policy,
    GetObservationCallback,
    MoveRobotCallback,
    SendFeedbackCallback,
)
from aic_model_interfaces.msg import Observation
from aic_task_interfaces.msg import Task

try:
    from lerobot.datasets import LeRobotDataset
    _has_lerobot = True
except ImportError:
    _has_lerobot = False

try:
    from aic_training_interfaces.srv import ExpandXacro
    _has_expand = True
except ImportError:
    _has_expand = False

try:
    from gazebo_msgs.srv import SpawnEntity, DeleteEntity
    _has_gazebo = True
except ImportError:
    _has_gazebo = False

try:
    import cv2
    _has_cv2 = True
except ImportError:
    _has_cv2 = False

try:
    from tf_transformations import quaternion_from_euler
except ImportError:
    def quaternion_from_euler(r, p, y):
        cy, sy = math.cos(y * 0.5), math.sin(y * 0.5)
        cp, sp = math.cos(p * 0.5), math.sin(p * 0.5)
        cr, sr = math.cos(r * 0.5), math.sin(r * 0.5)
        return [sr*cp*cy - cr*sp*sy, cr*sp*cy + sr*cp*sy,
                cr*cp*sy - sr*sp*cy, cr*cp*cy + sr*sp*sy]


# ── Image dimensions (camera native 1024×1152, stored at 4× downscale) ───────
_IMG_H = 256   # 1024 // 4
_IMG_W = 288   # 1152 // 4

# ── Tuning ────────────────────────────────────────────────────────────────────

# Approach: bring plug to APPROACH_Z_ABOVE above entrance with XY + orientation
# both corrected simultaneously and confirmed stable before insertion starts.
APPROACH_KP          = 4.0
APPROACH_ORIENT_KP   = 3.0
APPROACH_Z_ABOVE     = 0.008   # 8 mm above entrance
APPROACH_DONE_M      = 0.002   # 2 mm position tolerance
APPROACH_DONE_RAD    = 0.025   # ~1.4 ° orientation tolerance
APPROACH_SETTLED_TICKS = 20    # hold both stable for 2 s (at 10 Hz) before inserting
APPROACH_TIMEOUT_S   = 60.0

# Insertion
INSERT_VEL_M_S       = 0.006   # 6 mm/s axial push
INSERT_ORIENT_KP     = 1.5     # orientation correction applied during push
INSERT_HOLD_KP       = 10.0    # lateral hold gain
INSERT_TIMEOUT_S     = 120.0   # generous overall budget
INSERT_DONE_M        = 0.002

# Stall recovery: pull back then re-run a mini-approach before pushing again.
STALL_RATE_MM_S      = 0.5
STALL_WINDOW_S       = 1.5     # declare stall after 1.5 s without progress
MAX_STALL_CYCLES     = 30      # never give up (30 pull-back/re-approach cycles)
PULLBACK_VEL_M_S     = 0.015   # retract speed
PULLBACK_DIST_M      = 0.008   # pull back 8 mm
REAPPROACH_TIMEOUT_S = 6.0     # re-approach budget after each pullback
REAPPROACH_SETTLED   = 10      # ticks both stable before pushing again

# Close-range: once plug is within this distance, skip pullback cycles and push
# straight through.  High contact force sustained for FORCE_SUCCESS_TICKS at
# this range is treated as a fully-seated indication.
CLOSE_THRESH_M       = 0.010   # 10 mm — engage close-range mode
FORCE_SUCCESS_N      = 15.0    # sustained axial force threshold
FORCE_SUCCESS_TICKS  = 8       # consecutive ticks at force+close = success

MAX_VEL_M_S          = 0.25
MAX_ANG_VEL_RAD_S    = 1.5

RECORD_FPS           = 10


# ── Rotation helpers ──────────────────────────────────────────────────────────
def _quat_to_rot(q):
    x, y, z, w = q
    return np.array([
        [1-2*(y*y+z*z),   2*(x*y-w*z),   2*(x*z+w*y)],
        [  2*(x*y+w*z), 1-2*(x*x+z*z),   2*(y*z-w*x)],
        [  2*(x*z-w*y),   2*(y*z+w*x), 1-2*(x*x+y*y)],
    ])


def _rot_error(R_cur, R_des):
    R_err = R_des @ R_cur.T
    angle = math.acos(max(-1.0, min(1.0, (np.trace(R_err) - 1) / 2)))
    if angle < 1e-6:
        return np.zeros(3)
    axis = np.array([R_err[2,1]-R_err[1,2],
                     R_err[0,2]-R_err[2,0],
                     R_err[1,0]-R_err[0,1]]) / (2 * math.sin(angle))
    return axis * angle


class InsertionDataCollector(Policy):
    """
    Data collection policy for SFP/SC cable insertion.

    Runs the full simple_insertion_node state machine within the aic_model
    Policy interface so every step is recorded as a LeRobot dataset frame.
    Spawns a randomised task board between episodes using training utils.
    """

    def __init__(self, parent_node: Node):
        super().__init__(parent_node)
        self._node = parent_node

        # ── Parameters (override via --ros-args -p <name>:=<value>) ──────────
        self._node.declare_parameter('num_episodes',     50)
        self._node.declare_parameter('output_dir',       'datasets/insertion_demos')
        self._node.declare_parameter('repo_id',          'local/insertion_demos')
        self._node.declare_parameter('plug_type_filter', '')  # '' = record all types

        self._num_episodes      = self._node.get_parameter('num_episodes').value
        self._output_dir        = Path(self._node.get_parameter('output_dir').value)
        self._repo_id           = self._node.get_parameter('repo_id').value
        self._plug_type_filter  = self._node.get_parameter('plug_type_filter').value

        # ── TF ────────────────────────────────────────────────────────────────
        self._tf = Buffer()
        self._tf_listener = TransformListener(self._tf, parent_node)

        # ── Dataset state ─────────────────────────────────────────────────────
        self._dataset:    Optional[LeRobotDataset] = None
        self._ep_frames:  int = 0
        self._ep_start_t: float = 0.0

        # ── Services ──────────────────────────────────────────────────────────
        self._tare_cli   = parent_node.create_client(Trigger, '/aic_controller/tare_force_torque_sensor')
        self._reset_cli  = parent_node.create_client(Trigger, '/scoring/reset_joints')
        self._expand_cli = (parent_node.create_client(ExpandXacro, '/expand_xacro')
                            if _has_expand else None)
        self._spawn_cli  = (parent_node.create_client(SpawnEntity,  '/gz_server/spawn_entity')
                            if _has_gazebo else None)
        self._delete_cli = (parent_node.create_client(DeleteEntity, '/gz_server/delete_entity')
                            if _has_gazebo else None)

        # ── Stall tracking ────────────────────────────────────────────────────
        self._last_prog   = 0.0
        self._last_prog_t = time.monotonic()
        self._stall_start: Optional[float] = None

        # ── Cross-trial episode counter ───────────────────────────────────────
        self._total_completed = 0

        self.get_logger().info(
            f"InsertionDataCollector ready  "
            f"episodes={self._num_episodes}  "
            f"output={self._output_dir}  "
            f"repo_id={self._repo_id}"
        )

    # ── TF helpers ────────────────────────────────────────────────────────────
    def _tf_lookup(self, target: str, source: str):
        """Return TransformStamped or None."""
        try:
            return self._tf.lookup_transform(
                target, source, Time(),
                timeout=Duration(seconds=0.05))
        except TransformException:
            return None

    def _pos(self, target: str, source: str) -> Optional[np.ndarray]:
        t = self._tf_lookup(target, source)
        if t is None:
            return None
        p = t.transform.translation
        return np.array([p.x, p.y, p.z])

    def _pos_rot(self, target: str, source: str):
        t = self._tf_lookup(target, source)
        if t is None:
            return None, None
        p  = t.transform.translation
        q  = t.transform.rotation
        return (np.array([p.x, p.y, p.z]),
                _quat_to_rot((q.x, q.y, q.z, q.w)))

    def _first_pos(self, frames):
        for f in frames:
            p = self._pos('base_link', f)
            if p is not None:
                return p, f
        return None, None

    def _first_pos_rot(self, frames):
        for f in frames:
            p, R = self._pos_rot('base_link', f)
            if p is not None:
                return p, R, f
        return None, None, None

    # ── Motion ────────────────────────────────────────────────────────────────
    def _cmd(self, move_robot: MoveRobotCallback,
             lin, ang=(0., 0., 0.)) -> np.ndarray:
        lin = np.asarray(lin, dtype=float)
        ang = np.asarray(ang, dtype=float)
        spd = np.linalg.norm(lin)
        if spd > MAX_VEL_M_S:
            lin = lin / spd * MAX_VEL_M_S
        asc = np.linalg.norm(ang)
        if asc > MAX_ANG_VEL_RAD_S:
            ang = ang / asc * MAX_ANG_VEL_RAD_S

        twist = Twist()
        twist.linear.x  = lin[0]; twist.linear.y  = lin[1]; twist.linear.z  = lin[2]
        twist.angular.x = ang[0]; twist.angular.y = ang[1]; twist.angular.z = ang[2]

        msg = MotionUpdate()
        msg.velocity         = twist
        msg.header.frame_id  = 'base_link'
        msg.header.stamp     = self.get_clock().now().to_msg()
        msg.target_stiffness = np.diag([100., 100., 100., 50., 50., 50.]).flatten()
        msg.target_damping   = np.diag([40.,  40.,  40., 15., 15., 15.]).flatten()
        msg.feedforward_wrench_at_tip = Wrench(
            force=Vector3(x=0., y=0., z=0.),
            torque=Vector3(x=0., y=0., z=0.))
        msg.wrench_feedback_gains_at_tip = [0.5, 0.5, 0.5, 0.0, 0.0, 0.0]
        msg.trajectory_generation_mode.mode = TrajectoryGenerationMode.MODE_VELOCITY
        move_robot(motion_update=msg)

        return np.array([lin[0], lin[1], lin[2],
                         ang[0], ang[1], ang[2], 0.0], dtype=np.float32)

    def _stop(self, move_robot):
        self._cmd(move_robot, [0, 0, 0])

    def _retract(self, move_robot, axis: np.ndarray,
                 duration: float = 2.5, speed: float = 0.04):
        """Move robot away from port after insertion so the next episode starts clean."""
        retract_v = -axis * speed
        t0 = time.monotonic()
        while time.monotonic() - t0 < duration:
            self._cmd(move_robot, retract_v)
            self.sleep_for(0.05)
        self._stop(move_robot)
        self.sleep_for(0.3)

    # ── Stall detection ───────────────────────────────────────────────────────
    def _reset_stall(self):
        self._last_prog   = 0.0
        self._last_prog_t = time.monotonic()
        self._stall_start = None

    def _check_stall(self, progress: float):
        now  = time.monotonic()
        rate = ((progress - self._last_prog)
                / max(now - self._last_prog_t, 0.01) * 1000.0)
        self._last_prog   = progress
        self._last_prog_t = now
        if rate < STALL_RATE_MM_S:
            if self._stall_start is None:
                self._stall_start = now
            return True, now - self._stall_start, rate
        self._stall_start = None
        return False, 0.0, rate

    # ── Dataset ───────────────────────────────────────────────────────────────
    def _remove_corrupted_parquets(self, directory: Path) -> int:
        """Scan directory for corrupted parquet files and delete them.
        Returns the number of files removed."""
        try:
            import pyarrow.parquet as _pq
        except ImportError:
            return 0
        removed = 0
        for pq_file in sorted(directory.rglob("*.parquet")):
            try:
                _pq.read_schema(str(pq_file))
            except Exception:
                pq_file.unlink(missing_ok=True)
                removed += 1
                self.get_logger().warn(f"Removed corrupted parquet: {pq_file.name}")
        return removed

    def _init_dataset(self):
        if not _has_lerobot:
            self.get_logger().warn("lerobot not installed — data will NOT be saved")
            return

        # resume() needs meta/episodes/*.parquet locally; without it, it falls back
        # to HuggingFace Hub (404 for local-only repos).  metadata_buffer_size=1
        # ensures that file is written after every episode so cross-session resume
        # always has valid local parquets to load.
        episodes_dir = self._output_dir / "meta" / "episodes"

        # Repair: remove any corrupted parquets left by a mid-write Ctrl-C.
        if episodes_dir.exists():
            n = self._remove_corrupted_parquets(episodes_dir)
            if n:
                self.get_logger().warn(f"Repaired {n} corrupted parquet(s)")

        has_flushed_episodes = (episodes_dir.exists() and
                                any(episodes_dir.rglob("*.parquet")))

        if has_flushed_episodes:
            try:
                self._dataset = LeRobotDataset.resume(
                    repo_id=self._repo_id,
                    root=self._output_dir,
                )
                # Force immediate per-episode flush so the next session can resume.
                try:
                    self._dataset.writer._meta._metadata_buffer_size = 1
                except Exception:
                    pass
                self._total_completed = self._dataset.meta.total_episodes
                self.get_logger().info(
                    f"Resumed dataset at {self._output_dir}  "
                    f"({self._total_completed} episodes already saved)")
                return
            except Exception as e:
                self.get_logger().warn(
                    f"resume() failed even after repair ({e}) — starting fresh")
                shutil.rmtree(self._output_dir)

        # Create fresh — remove any leftover partial directory first.
        if self._output_dir.exists():
            shutil.rmtree(self._output_dir)
            self.get_logger().warn(f"Removed incomplete dataset dir {self._output_dir}")

        features = {
            "observation.images.left_camera":   {"shape": (3, _IMG_H, _IMG_W), "dtype": "image"},
            "observation.images.center_camera": {"shape": (3, _IMG_H, _IMG_W), "dtype": "image"},
            "observation.images.right_camera":  {"shape": (3, _IMG_H, _IMG_W), "dtype": "image"},
            "observation.state":                {"shape": (26,),          "dtype": "float32"},
            "observation.wrist_force":          {"shape": (3,),           "dtype": "float32"},
            "action":                           {"shape": (7,),           "dtype": "float32"},
        }
        self._dataset = LeRobotDataset.create(
            repo_id=self._repo_id,
            fps=RECORD_FPS,
            features=features,
            root=self._output_dir,
            use_videos=False,
            metadata_buffer_size=1,
        )
        self.get_logger().info(f"Dataset initialised at {self._output_dir}")

    def _img_np(self, img_msg) -> np.ndarray:
        arr = np.frombuffer(img_msg.data, dtype=np.uint8).reshape(
            img_msg.height, img_msg.width, 3)
        # Downsample 4× (1024×1152 → 256×288) using stride; clip to exact target
        arr = arr[::4, ::4][:_IMG_H, :_IMG_W]
        return arr.transpose(2, 0, 1)

    def _state_np(self, obs: Observation) -> np.ndarray:
        cs  = obs.controller_state
        tcp = cs.tcp_pose
        vel = cs.tcp_velocity
        return np.array([
            tcp.position.x, tcp.position.y, tcp.position.z,
            tcp.orientation.x, tcp.orientation.y,
            tcp.orientation.z, tcp.orientation.w,
            vel.linear.x,  vel.linear.y,  vel.linear.z,
            vel.angular.x, vel.angular.y, vel.angular.z,
            *cs.tcp_error,
            *obs.joint_states.position[:7],
        ], dtype=np.float32)

    def _record(self, obs: Observation, action: np.ndarray, task_str: str):
        if obs is None:
            return
        if self._dataset is None:
            self._init_dataset()
        if self._dataset is None:
            return
        f = obs.wrist_wrench.wrench.force
        self._dataset.add_frame({
            "observation.images.left_camera":   self._img_np(obs.left_image),
            "observation.images.center_camera": self._img_np(obs.center_image),
            "observation.images.right_camera":  self._img_np(obs.right_image),
            "observation.state":                self._state_np(obs),
            "observation.wrist_force":          np.array([f.x, f.y, f.z], dtype=np.float32),
            "action":                           action,
            "task":                             task_str,
        })
        self._ep_frames += 1

    def _save_ep(self, ep_num: int, task_str: str):
        if self._dataset is not None:
            self._dataset.save_episode()
            self.get_logger().info(f"Saved episode {ep_num}  ({self._ep_frames} frames)")
        self._ep_frames = 0

    def _discard_ep(self):
        """Drop frames from a failed episode without writing to disk."""
        if self._dataset is not None:
            try:
                self._dataset.clear_episode_buffer(delete_images=True)
            except Exception as e:
                self.get_logger().warn(f"clear_episode_buffer failed: {e}")
        self._ep_frames = 0

    # ── Scene management ──────────────────────────────────────────────────────
    def _tare(self):
        if self._tare_cli.wait_for_service(timeout_sec=1.0):
            future = self._tare_cli.call_async(Trigger.Request())
            deadline = time.monotonic() + 3.0
            while not future.done() and time.monotonic() < deadline:
                self.sleep_for(0.05)
            self.get_logger().info("F/T tared")
        else:
            self.get_logger().warn("Tare service unavailable")

    def _reset_scene(self, cable_type: str) -> bool:
        self.get_logger().info("Resetting scene…")
        if self._expand_cli and self._spawn_cli:
            for name in ["task_board", "cable_0"]:
                if self._delete_cli:
                    req = DeleteEntity.Request()
                    req.name = name
                    req.force = True
                    self._delete_cli.call_async(req)
            self.sleep_for(1.5)

            x   = random.uniform(0.15, 0.18)
            y   = random.uniform(-0.20, 0.10)
            yaw = random.uniform(3.00, 3.14159)
            nic_rail = random.randint(0, 4)

            xacro_args = [
                "ground_truth:=true",
                f"task_board_x:={x:.4f}",
                f"task_board_y:={y:.4f}",
                "task_board_z:=1.14",
                "task_board_roll:=0.0",
                "task_board_pitch:=0.0",
                f"task_board_yaw:={yaw:.4f}",
                f"nic_card_mount_{nic_rail}_present:=true",
                "sc_port_0_present:=true",
                "spawn_cable:=true",
                f"cable_type:={cable_type}",
                "attach_cable_to_gripper:=true",
            ]

            if self._expand_cli.wait_for_service(timeout_sec=3.0):
                req = ExpandXacro.Request()
                req.package_name    = 'aic_description'
                req.relative_path   = 'urdf/task_board.urdf.xacro'
                req.xacro_arguments = xacro_args
                future = self._expand_cli.call_async(req)
                deadline = time.monotonic() + 8.0
                while not future.done() and time.monotonic() < deadline:
                    self.sleep_for(0.1)
                if future.done():
                    resp = future.result()
                    if resp.success:
                        spawn_req = SpawnEntity.Request()
                        spawn_req.name = "task_board"
                        spawn_req.xml  = resp.xml
                        self._spawn_cli.call_async(spawn_req)
                        self.sleep_for(2.5)
                        self._tare()
                        self.sleep_for(0.5)
                        return True
                    else:
                        self.get_logger().warn(f"ExpandXacro failed: {resp.message}")
            else:
                self.get_logger().warn("ExpandXacro service not ready — using fallback")

        # Fallback: joint reset — await completion so robot is fully homed before proceeding
        if self._reset_cli.wait_for_service(timeout_sec=5.0):
            future = self._reset_cli.call_async(Trigger.Request())
            deadline = time.monotonic() + 20.0
            while not future.done() and time.monotonic() < deadline:
                self.sleep_for(0.2)
        else:
            self.get_logger().warn("reset_joints service unavailable")
        self.sleep_for(5.0)  # let controller fully settle at home
        self._tare()
        self.sleep_for(0.5)
        return True

    # ── State machine — one insertion episode ─────────────────────────────────
    def _run_episode(
        self,
        task: Task,
        get_observation: GetObservationCallback,
        move_robot: MoveRobotCallback,
        send_feedback: SendFeedbackCallback,
        task_str: str,
    ) -> bool:
        """Execute one full insertion. Returns True on success, False on failure."""

        # ── Resolve frame names from Task ─────────────────────────────────────
        port_frames = [
            f"task_board/{task.target_module_name}/{task.port_name}_link",
            f"task_board/{task.target_module_name}/{task.port_name}",
        ]
        entrance_frames = [f + '_entrance' for f in port_frames]
        plug_frames = [
            f"{task.cable_name}/{task.plug_name}_link",
            f"{task.cable_name}/{task.plug_name}",
        ]

        # ── Wait for port TF ──────────────────────────────────────────────────
        send_feedback("waiting for TF")
        deadline = time.monotonic() + 15.0
        port_pos = port_R = None
        while time.monotonic() < deadline:
            port_pos, port_R, _ = self._first_pos_rot(port_frames)
            if port_pos is not None:
                break
            self.sleep_for(0.2)
        if port_pos is None:
            self.get_logger().error(f"Port TF unavailable: {port_frames[0]}")
            return False

        entrance_pos, _ = self._first_pos(entrance_frames)
        if entrance_pos is None:
            entrance_pos = port_pos + np.array([0., 0., 0.02])
            self.get_logger().warn("Entrance frame not found — using port + 2 cm fallback")

        delta = port_pos - entrance_pos
        dlen  = np.linalg.norm(delta)
        axis  = (delta / dlen if dlen > 0.005
                 else (port_R[:, 0] if port_R is not None else np.array([0., 0., -1.])))

        self.get_logger().info(
            f"port={port_pos.round(3)}  entrance={entrance_pos.round(3)}  "
            f"axis={axis.round(3)}")

        def refresh():
            nonlocal port_pos, port_R, entrance_pos, axis
            pp, pR, _ = self._first_pos_rot(port_frames)
            if pp is not None:
                port_pos, port_R = pp, pR
            ep, _ = self._first_pos(entrance_frames)
            if ep is not None:
                entrance_pos = ep
            d = port_pos - entrance_pos
            dl = np.linalg.norm(d)
            if dl > 0.005:
                axis = d / dl
            return self._first_pos(plug_frames)[0]

        def step(obs, action):
            self._record(obs, action, task_str)
            self.sleep_for(1.0 / RECORD_FPS)

        # ── APPROACH: correct XY + Z + orientation simultaneously ───────────────
        # Target: APPROACH_Z_ABOVE mm above entrance along the insertion axis.
        # Both position and orientation must be stable for APPROACH_SETTLED_TICKS
        # consecutive ticks before we start pushing.
        def _approach(timeout: float, settled_ticks: int, log_tag: str) -> bool:
            target = entrance_pos - axis * APPROACH_Z_ABOVE
            t0 = time.monotonic()
            settled = 0
            while time.monotonic() - t0 < timeout:
                plug_pos_l = refresh()
                if plug_pos_l is None:
                    self.sleep_for(0.1)
                    continue
                _, plug_R_l = self._pos_rot('base_link', plug_frames[0])
                pos_err = target - plug_pos_l
                omega   = (_rot_error(plug_R_l, port_R)
                           if (plug_R_l is not None and port_R is not None)
                           else np.zeros(3))
                action = self._cmd(move_robot,
                                   APPROACH_KP * pos_err,
                                   APPROACH_ORIENT_KP * omega)
                step(get_observation(), action)
                pos_ok = np.linalg.norm(pos_err) < APPROACH_DONE_M
                rot_ok = np.linalg.norm(omega) < APPROACH_DONE_RAD
                settled = (settled + 1) if (pos_ok and rot_ok) else 0
                if settled >= settled_ticks:
                    self._stop(move_robot)
                    self.get_logger().info(
                        f"{log_tag} ✓  "
                        f"pos={np.linalg.norm(pos_err)*1000:.1f}mm  "
                        f"rot={math.degrees(np.linalg.norm(omega)):.1f}°")
                    return True
            self._stop(move_robot)
            self.get_logger().warn(f"{log_tag} timeout — best-effort insert")
            return False

        send_feedback("approach")
        _approach(APPROACH_TIMEOUT_S, APPROACH_SETTLED_TICKS, "approach")

        plug_pos = refresh()
        if plug_pos is None:
            return False

        # ── INSERT with orientation correction + pull-back re-approach on stall ─
        send_feedback("insert")
        lat_ref = plug_pos.copy()
        self._reset_stall()
        stall_count        = 0
        force_success_streak = 0
        _last_dist: Optional[float] = None
        _none_streak  = 0
        t0 = time.monotonic()

        while time.monotonic() - t0 < INSERT_TIMEOUT_S:
            plug_pos = refresh()
            if plug_pos is None:
                _none_streak += 1
                if (_none_streak >= 8 and _last_dist is not None
                        and _last_dist < 0.015):
                    self._stop(move_robot)
                    self.get_logger().info(
                        f"Insertion complete ✓ (plug TF lost, "
                        f"last dist={_last_dist*1000:.1f}mm)")
                    self._retract(move_robot, axis)
                    return True
                self.sleep_for(0.1)
                continue
            _none_streak = 0
            obs = get_observation()

            # Orientation correction during insertion (prevents angular wedging)
            _, plug_R_i = self._pos_rot('base_link', plug_frames[0])
            omega_i = (_rot_error(plug_R_i, port_R)
                       if (plug_R_i is not None and port_R is not None)
                       else np.zeros(3))

            ft = obs.wrist_wrench.wrench.force
            axial_force = abs(np.dot(np.array([ft.x, ft.y, ft.z]), axis))

            axial_prog = np.dot(plug_pos - lat_ref, axis)
            lat_vec    = (plug_pos - lat_ref) - axial_prog * axis
            lat_err    = -lat_vec   # correction toward lat_ref line
            lat_dist   = np.linalg.norm(lat_vec)

            dist_remaining = np.dot(port_pos - plug_pos, axis)
            _last_dist = dist_remaining

            stalled, stall_dur, rate = self._check_stall(axial_prog)

            # Close-range mode: plug is nearly inserted — sustained force = success,
            # never pull back (pullback from this depth times out every time).
            if dist_remaining < CLOSE_THRESH_M:
                if axial_force >= FORCE_SUCCESS_N:
                    force_success_streak += 1
                else:
                    force_success_streak = 0

                self.get_logger().debug(
                    f"close-range  remaining={dist_remaining*1000:.1f}mm  "
                    f"F={axial_force:.1f}N  streak={force_success_streak}/{FORCE_SUCCESS_TICKS}")

                if force_success_streak >= FORCE_SUCCESS_TICKS:
                    self._stop(move_robot)
                    self.get_logger().info(
                        f"Insertion complete ✓ (force+close)  "
                        f"remaining={dist_remaining*1000:.1f}mm  F={axial_force:.1f}N")
                    self._retract(move_robot, axis)
                    return True

                # Keep pushing gently — orientation-corrected, slower in close range
                action = self._cmd(
                    move_robot,
                    axis * INSERT_VEL_M_S + INSERT_HOLD_KP * lat_err,
                    INSERT_ORIENT_KP * omega_i,
                )
                step(obs, action)
                continue

            if stalled and stall_dur >= STALL_WINDOW_S:
                stall_count += 1
                if stall_count > MAX_STALL_CYCLES:
                    self.get_logger().warn(
                        f"max stall cycles ({MAX_STALL_CYCLES}) — giving up")
                    self._stop(move_robot)
                    return False

                self.get_logger().warn(
                    f"stall {stall_count}/{MAX_STALL_CYCLES}  "
                    f"F={axial_force:.1f}N  rate={rate:.2f}mm/s — pull back & re-approach")

                # Pull back PULLBACK_DIST_M along -axis
                t_pb = time.monotonic()
                pb_dur = PULLBACK_DIST_M / PULLBACK_VEL_M_S
                while time.monotonic() - t_pb < pb_dur:
                    self._cmd(move_robot, -axis * PULLBACK_VEL_M_S)
                    self.sleep_for(0.05)
                self._stop(move_robot)
                self.sleep_for(0.1)

                # Re-approach: correct position + orientation before next push
                _approach(REAPPROACH_TIMEOUT_S, REAPPROACH_SETTLED, "re-approach")

                plug_pos = refresh()
                if plug_pos is None:
                    continue
                lat_ref = plug_pos.copy()
                self._reset_stall()
                continue

            # Normal insertion step: push axially + hold lateral + correct orientation
            action = self._cmd(
                move_robot,
                axis * INSERT_VEL_M_S + INSERT_HOLD_KP * lat_err,
                INSERT_ORIENT_KP * omega_i,
            )
            step(obs, action)

            self.get_logger().debug(
                f"insert  remaining={dist_remaining*1000:.1f}mm  "
                f"lat={lat_dist*1000:.1f}mm  F={axial_force:.1f}N  rate={rate:.2f}mm/s")

            if dist_remaining <= INSERT_DONE_M:
                self._stop(move_robot)
                self.get_logger().info(
                    f"Insertion complete ✓  "
                    f"remaining={dist_remaining*1000:.1f}mm  F={axial_force:.1f}N")
                self._retract(move_robot, axis)
                return True

        self.get_logger().warn("insert timeout")
        self._stop(move_robot)
        return False

    # ── Policy entry point ────────────────────────────────────────────────────
    def insert_cable(
        self,
        task: Task,
        get_observation: GetObservationCallback,
        move_robot: MoveRobotCallback,
        send_feedback: SendFeedbackCallback,
        **kwargs,
    ) -> bool:
        """
        Called once per trial by aic_engine.  Attempts the insertion up to
        MAX_RETRIES times (no scene reset between retries — just restart the
        state machine so align_xy brings the arm back to position).  Returns
        True as soon as one episode is saved; the engine will set up a fresh
        scene for the next trial.  Episodes accumulate in self._dataset across
        all trial calls within this lifecycle.
        """
        MAX_RETRIES = 10

        # Initialise (or resume) the dataset once so _total_completed is correct.
        if self._dataset is None:
            self._init_dataset()

        task_str = getattr(task, 'description',
                           f"Insert {task.plug_name} into {task.port_name}")

        # Already have enough episodes — nothing more to record this session.
        if self._total_completed >= self._num_episodes:
            send_feedback(f"target {self._num_episodes} already reached — skipping trial")
            return True

        # Skip trials whose plug type doesn't match the filter (e.g. skip SFP when
        # collecting SC data with the full 3-trial default simulation config).
        if self._plug_type_filter and task.plug_type != self._plug_type_filter:
            self.get_logger().info(
                f"Skipping {task.plug_type} trial (filter={self._plug_type_filter})")
            send_feedback(f"skip — plug_type={task.plug_type}")
            return True

        self.get_logger().info(
            f"Trial insertion  total_saved={self._total_completed}  "
            f"target={self._num_episodes}  task='{task_str}'")

        for attempt in range(1, MAX_RETRIES + 1):
            self.get_logger().info(f"  attempt {attempt}/{MAX_RETRIES}")

            success = self._run_episode(
                task, get_observation, move_robot, send_feedback, task_str)

            if success:
                self._total_completed += 1
                self._save_ep(self._total_completed, task_str)
                send_feedback(
                    f"Episode {self._total_completed}/{self._num_episodes} saved ✓")
                self.get_logger().info(
                    f"Episode {self._total_completed} saved  "
                    f"({self._total_completed}/{self._num_episodes} total)")

                if self._total_completed >= self._num_episodes and self._dataset is not None:
                    self._dataset.finalize()
                    self.get_logger().info(
                        f"Collection complete: {self._total_completed} episodes "
                        f"at {self._output_dir}")

                return True   # tell engine this trial succeeded

            self.get_logger().warn(f"  attempt {attempt} failed — retrying")
            self._discard_ep()

        self.get_logger().error(
            f"All {MAX_RETRIES} attempts failed for this trial")
        return False
