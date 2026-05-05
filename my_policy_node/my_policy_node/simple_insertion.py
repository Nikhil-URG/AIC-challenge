#!/usr/bin/env python3
"""
Simple insertion node — v7.0

Changes over v6.1:
  - Tare F/T sensor via /aic_controller/tare_force_torque_sensor before alignment.
  - Fix 0 N force readings: subscribe as WrenchStamped (not bare Wrench).
  - Orient: timeout 15→45 s, threshold 0.05→0.03 rad, require 10 consecutive settled ticks.
  - Stabilize: hold 1→5 s, re-checks orientation during settle, tighter XY gate (2→1.5 mm).
"""

import rclpy
from rclpy.node import Node
import numpy as np
import time
import math

from geometry_msgs.msg import Twist, Wrench, WrenchStamped, Vector3
from std_srvs.srv import Trigger
from tf2_ros import TransformException
from tf2_ros.buffer import Buffer
from tf2_ros.transform_listener import TransformListener
from aic_control_interfaces.msg import MotionUpdate, TrajectoryGenerationMode


PORT_FRAMES = [
    'task_board/nic_card_mount_0/sfp_port_0_link',
    'task_board/nic_card_mount_0/sfp_port_0',
    'sfp_port_0_link',
]
PORT_ENTRANCE_FRAMES = [
    'task_board/nic_card_mount_0/sfp_port_0_link_entrance',
    'task_board/nic_card_mount_0/sfp_port_0_entrance',
]
PLUG_FRAMES = [
    'cable_0/sfp_tip_link',
    'sfp_tip_link',
    'cable_0/sfp_tip',
]
GRIPPER_FRAME   = 'gripper/tcp'

# Force/torque topic — adjust if your ATI publishes on a different topic
FT_TOPIC = '/fts_broadcaster/wrench'

# ── Tuning ────────────────────────────────────────────────────────────────────
ALIGN_KP            = 4.0
ALIGN_DONE_M        = 0.002
ALIGN_Z_CLEARANCE   = 0.10
ALIGN_TIMEOUT_S     = 60.0

ORIENT_KP           = 3.0     # angular gain (rad/s per rad error)
ORIENT_DONE_RAD     = 0.03    # ~1.7°
ORIENT_TIMEOUT_S    = 60.0
ORIENT_SETTLED_TICKS = 10     # must hold below threshold for this many ticks before proceeding

HOVER_HEIGHT_M      = 0.010   # 10 mm above entrance
HOVER_KP            = 3.0
HOVER_DONE_M        = 0.002
HOVER_TIMEOUT_S     = 30.0
VERIFY_XY_TOL_M     = 0.0015  # 1.5 mm

STABILIZE_S         = 5.0     # pause after hover before inserting

INSERT_VEL_M_S      = 0.004
INSERT_HOLD_KP      = 10.0
LATERAL_ABORT_M     = 0.005   # abort insertion if lateral err exceeds 5 mm
INSERT_TIMEOUT_S    = 120.0   # SFP insertion can take time
INSERT_DONE_M       = 0.002

# Stall detection
STALL_RATE_MM_S     = 0.3     # mm/s — below this = stalled
STALL_WINDOW_S      = 3.0     # how long below rate before wiggle
FORCE_HIGH_N        = 15.0    # N axial force considered high (sanity check)

# Wiggle
WIGGLE_AMP_M        = 0.003   # 3 mm amplitude
WIGGLE_FREQ_HZ      = 1.5
WIGGLE_DURATION_S   = 2.0

RETRACT_KP          = 6.0
RETRACT_DONE_M      = 0.003

# Velocity caps — the P-controllers naturally ramp down as error shrinks;
# these caps only limit the initial fast-approach phase.
MAX_VEL_M_S         = 0.25    # linear: was 0.10, raised so far-away align/hover is fast
MAX_ANG_VEL_RAD_S   = 1.5     # angular: was 0.3, raised so orient converges quickly when far
MAX_RETRIES         = 5
MAX_WIGGLES         = 3       # retract after this many consecutive stall+wiggle cycles
LOG_EVERY_N_TICKS   = 5


def quat_to_rot(q):
    """Quaternion (x,y,z,w) → 3×3 rotation matrix."""
    x, y, z, w = q
    return np.array([
        [1-2*(y*y+z*z),   2*(x*y-w*z),   2*(x*z+w*y)],
        [  2*(x*y+w*z), 1-2*(x*x+z*z),   2*(y*z-w*x)],
        [  2*(x*z-w*y),   2*(y*z+w*x), 1-2*(x*x+y*y)],
    ])

def rot_error_axis_angle(R_cur, R_des):
    """
    Rotation error from R_cur to R_des as axis-angle vector (in current frame).
    Returns omega vector whose direction = axis, magnitude = angle.
    """
    R_err = R_des @ R_cur.T
    angle = math.acos(max(-1.0, min(1.0, (np.trace(R_err) - 1) / 2)))
    if angle < 1e-6:
        return np.zeros(3)
    axis = np.array([
        R_err[2, 1] - R_err[1, 2],
        R_err[0, 2] - R_err[2, 0],
        R_err[1, 0] - R_err[0, 1],
    ]) / (2 * math.sin(angle))
    return axis * angle


class SimpleInsertionNode(Node):
    def __init__(self):
        super().__init__('simple_insertion_node')

        self.declare_parameter('debug_mode',        True)
        self.declare_parameter('insertion_velocity', INSERT_VEL_M_S)
        self.declare_parameter('align_kp',          ALIGN_KP)
        self.declare_parameter('hover_kp',          HOVER_KP)
        self.declare_parameter('insert_hold_kp',    INSERT_HOLD_KP)
        self.declare_parameter('max_vel',           MAX_VEL_M_S)
        self.declare_parameter('max_retries',       MAX_RETRIES)
        self.declare_parameter('lateral_abort_m',   LATERAL_ABORT_M)
        self.declare_parameter('ft_topic',          FT_TOPIC)

        def gp(n, t):
            return getattr(self.get_parameter(n).get_parameter_value(),
                           f'{t}_value')

        self.debug_mode         = gp('debug_mode',        'bool')
        self.insertion_velocity = gp('insertion_velocity','double')
        self.align_kp           = gp('align_kp',         'double')
        self.hover_kp           = gp('hover_kp',         'double')
        self.insert_hold_kp     = gp('insert_hold_kp',   'double')
        self.max_vel            = gp('max_vel',           'double')
        self.max_retries        = gp('max_retries',       'integer')
        self.lateral_abort_m    = gp('lateral_abort_m',  'double')
        self.ft_topic           = gp('ft_topic',          'string')

        self.get_logger().info(
            f"align_kp={self.align_kp}  hover_kp={self.hover_kp}  "
            f"hold_kp={self.insert_hold_kp}  ins_vel={self.insertion_velocity}  "
            f"lateral_abort={self.lateral_abort_m*1000:.0f}mm  "
            f"max_retries={self.max_retries}"
        )

        self.tf_buffer   = Buffer()
        self.tf_listener = TransformListener(self.tf_buffer, self)
        self.motion_pub  = self.create_publisher(
            MotionUpdate, '/aic_controller/pose_commands', 10)

        # Force/torque subscriber — ATI publishes WrenchStamped
        self._ft_force  = np.zeros(3)
        self._ft_torque = np.zeros(3)
        self._ft_received = False
        self._ft_sub = self.create_subscription(
            WrenchStamped, self.ft_topic, self._ft_cb, 10)

        # Tare service client
        self._tare_client = self.create_client(
            Trigger, '/aic_controller/tare_force_torque_sensor')
        self._tare_future = None

        self.current_step = "init"
        self.completed    = False
        self._retry_count = 0

        self._port_pos     = None
        self._entrance_pos = None
        self._plug_pos     = None
        self._port_axis    = None
        self._port_R       = None   # rotation matrix of port frame in base_link
        self._plug_R       = None   # rotation matrix of plug frame in base_link
        self._hover_target = None
        self._lat_ref      = None

        # stall tracking
        self._last_progress    = 0.0
        self._last_prog_time   = 0.0
        self._stall_start      = None

        self._orient_settled   = 0    # consecutive ticks below ORIENT_DONE_RAD
        self._wiggle_count     = 0    # total wiggles this insertion attempt

        self._phase_start  = None
        self._state        = "wait_for_tf"
        self._startup_end  = time.monotonic() + 20.0
        self._tick_count   = 0

        self._timer = self.create_timer(0.1, self._tick)
        self.log("INFO", "Waiting 20 s for TF warm-up…")

    # ── logging — explicit if/elif avoids the logger severity crash ───────────
    def log(self, level, msg):
        ts   = time.strftime("%H:%M:%S")
        line = f"[{ts}] [{self.current_step}] {msg}"
        if level == "DEBUG":
            if self.debug_mode:
                self.get_logger().debug(line)
        elif level == "INFO":
            self.get_logger().info(line)
        elif level == "WARN":
            self.get_logger().warn(line)
        elif level == "ERROR":
            self.get_logger().error(line)

    def step(self, name):
        self.current_step = name
        self._phase_start = time.monotonic()
        self._tick_count  = 0
        self.log("INFO", f"▶ {name}  (attempt {self._retry_count+1}/{self.max_retries})")

    # ── force/torque callback ─────────────────────────────────────────────────
    def _ft_cb(self, msg: WrenchStamped):
        # Force is in the sensor frame; axial dot-products in insert() are still
        # meaningful if the sensor Z-axis is roughly aligned with base_link Z.
        # Transform the wrench into base_link here if your mount has a large rotation.
        self._ft_force  = np.array([msg.wrench.force.x,  msg.wrench.force.y,  msg.wrench.force.z])
        self._ft_torque = np.array([msg.wrench.torque.x, msg.wrench.torque.y, msg.wrench.torque.z])
        self._ft_received = True

    # ── TF helpers ────────────────────────────────────────────────────────────
    def _lookup_transform(self, target, source):
        try:
            return self.tf_buffer.lookup_transform(
                target, source, rclpy.time.Time(),
                timeout=rclpy.duration.Duration(seconds=0.05))
        except TransformException as e:
            self.log("DEBUG", f"TF miss {target}<-{source}: {e}")
            return None

    def _lookup_pos(self, target, source):
        t = self._lookup_transform(target, source)
        if t is None:
            return None
        p = t.transform.translation
        return np.array([p.x, p.y, p.z])

    def _lookup_pos_rot(self, target, source):
        """Return (pos, rot_matrix) or (None, None)."""
        t = self._lookup_transform(target, source)
        if t is None:
            return None, None
        p = t.transform.translation
        q = t.transform.rotation
        pos = np.array([p.x, p.y, p.z])
        rot = quat_to_rot((q.x, q.y, q.z, q.w))
        return pos, rot

    def _find(self, candidates):
        for f in candidates:
            p = self._lookup_pos('base_link', f)
            if p is not None:
                return p, f
        return None, None

    def _find_with_rot(self, candidates):
        for f in candidates:
            p, R = self._lookup_pos_rot('base_link', f)
            if p is not None:
                return p, R, f
        return None, None, None

    def _refresh(self):
        self._port_pos, self._port_R, pf = self._find_with_rot(PORT_FRAMES)
        self._entrance_pos, _            = self._find(PORT_ENTRANCE_FRAMES)
        self._plug_pos, self._plug_R, _  = self._find_with_rot(PLUG_FRAMES)

        if self._entrance_pos is None and self._port_pos is not None:
            self._entrance_pos = self._port_pos + np.array([0, 0, 0.02])
            self.log("DEBUG", "Entrance fallback: port + 2 cm")

        if self._port_pos is not None and self._entrance_pos is not None:
            delta = self._port_pos - self._entrance_pos
            dlen  = np.linalg.norm(delta)
            if dlen > 0.005:
                self._port_axis = delta / dlen
            elif self._port_R is not None:
                # Use port frame X-axis as insertion axis
                self._port_axis = self._port_R[:, 0]
            else:
                self._port_axis = np.array([0., 0., -1.])

            self._hover_target = self._entrance_pos - self._port_axis * HOVER_HEIGHT_M

        return (self._port_pos is not None
                and self._plug_pos is not None
                and self._port_axis is not None)

    # ── motion ────────────────────────────────────────────────────────────────
    def _pub(self, lin_xyz, ang_xyz=(0., 0., 0.)):
        lin = np.array(lin_xyz, dtype=float)
        ang = np.array(ang_xyz, dtype=float)
        spd = np.linalg.norm(lin)
        if spd > self.max_vel:
            lin = lin / spd * self.max_vel
        asc = np.linalg.norm(ang)
        if asc > MAX_ANG_VEL_RAD_S:
            ang = ang / asc * MAX_ANG_VEL_RAD_S

        twist = Twist()
        twist.linear.x  = lin[0]; twist.linear.y  = lin[1]; twist.linear.z  = lin[2]
        twist.angular.x = ang[0]; twist.angular.y = ang[1]; twist.angular.z = ang[2]

        msg = MotionUpdate()
        msg.velocity             = twist
        msg.header.frame_id      = 'base_link'
        msg.header.stamp         = self.get_clock().now().to_msg()
        msg.target_stiffness     = np.diag([100.,100.,100.,50.,50.,50.]).flatten()
        msg.target_damping       = np.diag([40., 40., 40., 15.,15.,15.]).flatten()
        msg.feedforward_wrench_at_tip = Wrench(
            force=Vector3(x=0.,y=0.,z=0.), torque=Vector3(x=0.,y=0.,z=0.))
        msg.wrench_feedback_gains_at_tip = [0.5, 0.5, 0.5, 0.0, 0.0, 0.0]
        msg.trajectory_generation_mode.mode = TrajectoryGenerationMode.MODE_VELOCITY
        self.motion_pub.publish(msg)
        return lin, ang

    def _stop(self):
        self._pub([0, 0, 0])

    def _go_to(self, target, kp):
        err = target - self._plug_pos
        cmd, _ = self._pub(kp * err)
        return cmd, np.linalg.norm(err)

    # ── stall detection ───────────────────────────────────────────────────────
    def _check_stall(self, progress):
        """
        progress : axial progress in METERS (scalar).
        Returns (stalled_bool, stall_duration_s, rate_mm_s).
        """
        now = time.monotonic()
        # Convert delta-meters / delta-seconds  →  mm/s
        rate = (progress - self._last_progress) / max(now - self._last_prog_time, 0.01) * 1000.0
        self._last_progress  = progress
        self._last_prog_time = now

        if rate < STALL_RATE_MM_S:
            if self._stall_start is None:
                self._stall_start = now
            stall_dur = now - self._stall_start
            return True, stall_dur, rate
        else:
            self._stall_start = None
            return False, 0.0, rate

    def _reset_stall(self):
        self._last_progress  = 0.0
        self._last_prog_time = time.monotonic()
        self._stall_start    = None

    # ── state machine ─────────────────────────────────────────────────────────
    def _tick(self):
        if self.completed:
            return
        self._tick_count += 1
        log_now = (self._tick_count % LOG_EVERY_N_TICKS == 0)

        # ── WAIT_FOR_TF ──────────────────────────────────────────────────────
        if self._state == "wait_for_tf":
            if time.monotonic() < self._startup_end:
                return
            self.log("INFO", "Checking TF…")
            if not self._refresh():
                self.log("ERROR", "Required TF frames missing — aborting.")
                self.completed = True; return
            if self._lookup_pos('base_link', GRIPPER_FRAME) is None:
                self.log("ERROR", f"'{GRIPPER_FRAME}' not found — aborting.")
                self.completed = True; return
            self.log("INFO",
                f"port={self._port_pos.round(4)}  "
                f"entrance={self._entrance_pos.round(4)}  "
                f"plug={self._plug_pos.round(4)}  "
                f"axis={self._port_axis.round(4)}  "
                f"hover={self._hover_target.round(4)}")
            self._state = "tare"; self.step("tare")

        # ── TARE — zero the F/T sensor before any motion ─────────────────────
        elif self._state == "tare":
            if self._tare_future is None:
                if not self._tare_client.service_is_ready():
                    self.log("WARN", "Tare service not ready — waiting…")
                    return
                self.log("INFO", "Calling tare service…")
                self._tare_future = self._tare_client.call_async(Trigger.Request())
                return
            if not self._tare_future.done():
                return
            result = self._tare_future.result()
            if result.success:
                self.log("INFO", f"Tare OK: {result.message}")
            else:
                self.log("WARN", f"Tare returned failure: {result.message} — proceeding anyway")
            # Wait briefly for the new zero to propagate before reading force
            time.sleep(0.5)
            self.log("INFO", f"F/T reading after tare: {self._ft_force.round(3)} N")
            self._state = "align_xy"; self.step("align_xy")

        # ── ALIGN XY ─────────────────────────────────────────────────────────
        elif self._state == "align_xy":
            elapsed = time.monotonic() - self._phase_start
            if elapsed > ALIGN_TIMEOUT_S:
                self.log("WARN", "align_xy timed out"); self._stop(); self.completed = True; return
            if not self._refresh():
                self.log("WARN", "Lost frames"); return

            target = np.array([
                self._port_pos[0],
                self._port_pos[1],
                self._entrance_pos[2] + ALIGN_Z_CLEARANCE,
            ])
            err    = target - self._plug_pos
            xy_err = np.linalg.norm(err[:2])
            cmd, _ = self._pub(self.align_kp * err)

            if log_now:
                self.log("INFO",
                    f"align_xy  xy_err={xy_err*1000:.1f}mm  "
                    f"z_err={err[2]*1000:.1f}mm  "
                    f"cmd=[{cmd[0]:.3f},{cmd[1]:.3f},{cmd[2]:.3f}]  t={elapsed:.1f}s")

            if xy_err < ALIGN_DONE_M:
                self.log("INFO", f"align_xy done ✓  xy_err={xy_err*1000:.1f}mm")
                self._stop()
                self._state = "orient"; self.step("orient")

        # ── ORIENT — align plug rotation to match port frame ──────────────────
        elif self._state == "orient":
            elapsed = time.monotonic() - self._phase_start
            if elapsed > ORIENT_TIMEOUT_S:
                self.log("WARN", "orient timed out — proceeding anyway")
                self._stop()
                self._orient_settled = 0
                self._state = "hover"; self.step("hover"); return
            if not self._refresh():
                self.log("WARN", "Lost frames"); return

            if self._port_R is None or self._plug_R is None:
                self.log("WARN", "No rotation data — skipping orient")
                self._state = "hover"; self.step("hover"); return

            omega = rot_error_axis_angle(self._plug_R, self._port_R)
            ang_err = np.linalg.norm(omega)

            target_xy = np.array([
                self._port_pos[0], self._port_pos[1],
                self._entrance_pos[2] + ALIGN_Z_CLEARANCE,
            ])
            lin_cmd = self.align_kp * (target_xy - self._plug_pos)
            ang_cmd = ORIENT_KP * omega
            self._pub(lin_cmd, ang_cmd)

            if ang_err < ORIENT_DONE_RAD:
                self._orient_settled += 1
            else:
                self._orient_settled = 0

            if log_now:
                self.log("INFO",
                    f"orient  ang_err={math.degrees(ang_err):.1f}°  "
                    f"omega=[{omega[0]:.3f},{omega[1]:.3f},{omega[2]:.3f}]  "
                    f"settled={self._orient_settled}/{ORIENT_SETTLED_TICKS}  t={elapsed:.1f}s")

            if self._orient_settled >= ORIENT_SETTLED_TICKS:
                self.log("INFO",
                    f"orient done ✓  ang_err={math.degrees(ang_err):.1f}°  "
                    f"held {ORIENT_SETTLED_TICKS} ticks")
                self._stop()
                self._orient_settled = 0
                self._state = "hover"; self.step("hover")

        # ── HOVER — descend to 10 mm above entrance ───────────────────────────
        elif self._state == "hover":
            elapsed = time.monotonic() - self._phase_start
            if elapsed > HOVER_TIMEOUT_S:
                self.log("WARN", "hover timed out — retrying align")
                self._stop(); self._state = "align_xy"; self.step("align_xy"); return
            if not self._refresh():
                self.log("WARN", "Lost frames"); return

            cmd, dist = self._go_to(self._hover_target, self.hover_kp)

            if log_now:
                self.log("INFO",
                    f"hover  dist={dist*1000:.1f}mm  "
                    f"plug={self._plug_pos.round(4)}  "
                    f"target={self._hover_target.round(4)}  t={elapsed:.1f}s")

            if dist < HOVER_DONE_M:
                self._stop()
                self._state = "verify"; self.step("verify")

        # ── VERIFY — gate check before committing to insert ───────────────────
        elif self._state == "verify":
            if not self._refresh():
                self.log("WARN", "Lost frames"); return

            xy_err = np.linalg.norm((self._hover_target - self._plug_pos)[:2])
            self.log("INFO",
                f"verify  xy_err={xy_err*1000:.1f}mm  "
                f"(tol={VERIFY_XY_TOL_M*1000:.0f}mm)")

            if xy_err > VERIFY_XY_TOL_M:
                self.log("WARN", f"XY misaligned at hover — back to align_xy")
                self._state = "align_xy"; self.step("align_xy")
            else:
                self.log("INFO", "Alignment verified ✓ — stabilizing…")
                self._state = "stabilize"; self.step("stabilize")

        # ── STABILIZE — pause so arm settles before insertion ─────────────────
        elif self._state == "stabilize":
            elapsed = time.monotonic() - self._phase_start

            if not self._refresh():
                self.log("WARN", "Lost frames"); return
            hold_err = self._hover_target - self._plug_pos
            self._pub(self.hover_kp * hold_err)

            if log_now:
                dist = np.linalg.norm(hold_err)
                ft_mag = np.linalg.norm(self._ft_force)
                orient_ok = "—"
                if self._port_R is not None and self._plug_R is not None:
                    ang_err = np.linalg.norm(rot_error_axis_angle(self._plug_R, self._port_R))
                    orient_ok = f"{math.degrees(ang_err):.1f}°"
                self.log("INFO",
                    f"stabilize  {elapsed:.2f}/{STABILIZE_S:.1f}s  "
                    f"drift={dist*1000:.1f}mm  orient={orient_ok}  F={ft_mag:.2f}N")

            if elapsed >= STABILIZE_S:
                xy_err = np.linalg.norm(hold_err[:2])
                if xy_err > VERIFY_XY_TOL_M:
                    self.log("WARN",
                        f"Drifted during stabilize (xy={xy_err*1000:.1f}mm > "
                        f"{VERIFY_XY_TOL_M*1000:.1f}mm) — re-aligning")
                    self._state = "align_xy"; self.step("align_xy"); return
                # Re-check orientation before committing
                if self._port_R is not None and self._plug_R is not None:
                    ang_err = np.linalg.norm(rot_error_axis_angle(self._plug_R, self._port_R))
                    if ang_err > ORIENT_DONE_RAD * 2:
                        self.log("WARN",
                            f"Orientation drifted during stabilize ({math.degrees(ang_err):.1f}°) — re-orienting")
                        self._state = "orient"; self.step("orient"); return
                self.log("INFO", "Stabilized ✓ — locking reference and inserting")
                self._lat_ref = self._plug_pos.copy()
                self._reset_stall()
                self._wiggle_start = None
                self._wiggle_count = 0
                self._state = "insert"; self.step("insert")

        # ── INSERT ────────────────────────────────────────────────────────────
        elif self._state == "insert":
            elapsed = time.monotonic() - self._phase_start
            if elapsed > INSERT_TIMEOUT_S:
                self.log("WARN", "insert timed out — retracting")
                self._stop(); self._do_retract(); return
            if not self._refresh():
                self.log("WARN", "Lost frames"); return

            # On first tick, warn loudly if F/T sensor has never published
            if self._tick_count == 1:
                if not self._ft_received:
                    self.log("WARN",
                        f"F/T SENSOR: no data received on '{self.ft_topic}'. "
                        "Run: ros2 topic list | grep -iE 'ft|wrench|ati'  "
                        "and update the ft_topic parameter.")
                else:
                    self.log("INFO", f"F/T sensor active — F={self._ft_force.round(3)} N")

            axis = self._port_axis

            vec          = self._plug_pos - self._lat_ref
            axial_prog   = np.dot(vec, axis)

            cur_axial    = np.dot(self._plug_pos, axis)
            ref_axial    = np.dot(self._lat_ref,  axis)
            cur_lat_pos  = self._plug_pos  - cur_axial * axis
            ref_lat_pos  = self._lat_ref   - ref_axial * axis
            lat_err      = ref_lat_pos - cur_lat_pos
            lat_dist     = np.linalg.norm(lat_err)

            # ── LATERAL ABORT ─────────────────────────────────────────────────
            if lat_dist > self.lateral_abort_m:
                self.log("WARN",
                    f"Lateral error {lat_dist*1000:.1f}mm > "
                    f"{self.lateral_abort_m*1000:.0f}mm — aborting insertion")
                self._stop(); self._do_retract(); return

            # ── WIGGLE if stalling ────────────────────────────────────────────
            # Pass axial_prog in meters so _check_stall converts to mm/s correctly
            stalled, stall_dur, prog_rate = self._check_stall(axial_prog)
            axial_force = abs(np.dot(self._ft_force, axis))

            if stalled and stall_dur >= STALL_WINDOW_S:
                if self._wiggle_start is None:
                    self._wiggle_count += 1
                    if self._wiggle_count > MAX_WIGGLES:
                        self.log("WARN",
                            f"Stall after {MAX_WIGGLES} wiggles — retracting")
                        self._stop(); self._do_retract(); return
                    self._wiggle_start = time.monotonic()
                    self.log("WARN",
                        f"Stall detected ({prog_rate:.2f} mm/s, "
                        f"F_axial={axial_force:.1f}N) — wiggle {self._wiggle_count}/{MAX_WIGGLES}")

                wig_elapsed = time.monotonic() - self._wiggle_start
                if wig_elapsed < WIGGLE_DURATION_S:
                    ref_vec = np.array([0., 0., 1.])
                    if abs(np.dot(axis, ref_vec)) > 0.9:
                        ref_vec = np.array([1., 0., 0.])
                    lat1 = np.cross(axis, ref_vec)
                    lat1 /= np.linalg.norm(lat1)
                    t_wig = wig_elapsed
                    wig_vel = (WIGGLE_AMP_M * 2 * math.pi * WIGGLE_FREQ_HZ
                               * math.cos(2 * math.pi * WIGGLE_FREQ_HZ * t_wig)) * lat1
                    insert_cmd = axis * self.insertion_velocity
                    lat_corr   = self.insert_hold_kp * lat_err
                    cmd, _     = self._pub(insert_cmd + wig_vel + lat_corr)
                    if log_now:
                        self.log("INFO",
                            f"wiggle  t={t_wig:.1f}/{WIGGLE_DURATION_S:.1f}s  "
                            f"F={axial_force:.1f}N  lat={lat_dist*1000:.1f}mm")
                    return
                else:
                    self._wiggle_start = None
                    self._reset_stall()

            else:
                self._wiggle_start = None

            # ── Normal insertion velocity ─────────────────────────────────────
            axial_vel  = axis * self.insertion_velocity
            lat_corr   = self.insert_hold_kp * lat_err
            cmd, _     = self._pub(axial_vel + lat_corr)

            # Distance remaining to port along insertion axis
            if self._port_pos is None or self._plug_pos is None:
                return
            dist_remaining = np.dot(self._port_pos - self._plug_pos, axis)

            if log_now:
                self.log("INFO",
                    f"insert  traveled={axial_prog*1000:.1f}mm  remaining={dist_remaining*1000:.1f}mm  "
                    f"lateral_err={lat_dist*1000:.1f}mm  "
                    f"F_axial={axial_force:.1f}N  rate={prog_rate:.2f}mm/s  "
                    f"cmd=[{cmd[0]:.4f},{cmd[1]:.4f},{cmd[2]:.4f}]  t={elapsed:.1f}s")

            if dist_remaining <= INSERT_DONE_M:
                self.log("INFO",
                    f"Insertion complete ✓  traveled={axial_prog*1000:.1f}mm  "
                    f"remaining={dist_remaining*1000:.1f}mm  lateral_err={lat_dist*1000:.1f}mm")
                self._stop()
                self._state = "check_insertion"; self.step("check_insertion")

        # ── CHECK INSERTION ───────────────────────────────────────────────────
        elif self._state == "check_insertion":
            if not self._refresh():
                self.log("WARN", "Lost frames"); return

            dist_to_port = np.linalg.norm(self._port_pos - self._plug_pos)
            self.log("INFO", f"check_insertion  dist_to_port={dist_to_port*1000:.1f}mm")

            if dist_to_port <= INSERT_DONE_M * 3:
                self.log("INFO", "Insertion verified ✓")
                self.completed = True
            else:
                self.log("WARN", f"Not at port depth ({dist_to_port*1000:.1f}mm) — retracting")
                self._do_retract()

        # ── RETRACT ───────────────────────────────────────────────────────────
        elif self._state == "retract":
            elapsed = time.monotonic() - self._phase_start
            if elapsed > 15.0:
                self.log("WARN", "retract timed out — trying align_xy")
                self._stop(); self._state = "align_xy"; self.step("align_xy"); return
            if not self._refresh():
                self.log("WARN", "Lost frames"); return

            cmd, dist = self._go_to(self._hover_target, RETRACT_KP)

            if log_now:
                self.log("INFO",
                    f"retract  dist={dist*1000:.1f}mm  t={elapsed:.1f}s")

            if dist < RETRACT_DONE_M:
                self.log("INFO", "Retracted ✓")
                self._stop()
                self._state = "verify"; self.step("verify")

    def _do_retract(self):
        self._retry_count += 1
        if self._retry_count >= self.max_retries:
            self.log("ERROR", f"Max retries ({self.max_retries}) reached — giving up.")
            self.completed = True
            return
        self.log("INFO", f"Retry {self._retry_count}/{self.max_retries} — retracting to hover")
        self._state = "retract"; self.step("retract")


def main(args=None):
    print("--- simple_insertion v7.1 (fast-far/slow-near caps, stabilize gain fix, insert 120s) ---")
    rclpy.init(args=args)
    node = SimpleInsertionNode()
    while not node.completed and rclpy.ok():
        rclpy.spin_once(node, timeout_sec=0.1)
    node.log("INFO", "Done.")
    node.destroy_node()
    rclpy.shutdown()


if __name__ == '__main__':
    main()