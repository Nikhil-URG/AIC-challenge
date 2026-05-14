#!/usr/bin/env python3
"""
review_yolo_labels.py — Interactive YOLO-pose label reviewer and corrector.

Supports 10-keypoint labels (sfp_nic: kp0-4 = port0, kp5-9 = port1; sc_port:
kp0-4 real, kp5-9 invisible).  Invisible keypoints (visibility=0) are shown as
small grey crosses and cannot be selected or moved.

Usage:
    python scripts/review_yolo_labels.py <dataset_dir>
    python scripts/review_yolo_labels.py --purge <dataset_dir>

    <dataset_dir>: a class subdir (sfp_nic/) or the root (yolo_labeled/)

Zoom / Pan:
    Scroll wheel      →  zoom in/out centered on cursor
    Right-click drag  →  pan
    h                 →  reset view to full image
    (matplotlib toolbar zoom-rect also works; disables kp editing while active)

Keypoint editing:
    Left-click on a dot   →  select keypoint (turns red + cross-hair)
    Left-click elsewhere   →  move selected keypoint to that pixel
    Invisible kps (grey ×) cannot be selected.

Save / Navigate:
    s / Enter  →  save label + overwrite image with keypoints burned in → next
    n          →  next without saving
    b          →  back to previous image
    r          →  reset to last-saved values
    d          →  mark image for deletion (.delete flag)
    q / Esc    →  quit

After reviewing run --purge to delete flagged samples:
    python scripts/review_yolo_labels.py --purge pose_data/yolo_labeled/
"""

import sys
from pathlib import Path

import cv2
import matplotlib
matplotlib.use("TkAgg")
import matplotlib.pyplot as plt
import matplotlib.colors as mcolors
from matplotlib.patches import Rectangle, Circle
import numpy as np


BBOX_PAD_PX  = 60
SELECT_TOL   = 22     # click-to-select radius (image pixels)
KP_RADIUS    = 9      # dot radius (image pixels)
ZOOM_FACTOR  = 1.25

# port 0: warm palette   port 1: cool palette   (indices 0-4 / 5-9)
KP_COLORS = [
    "limegreen",   # p0 center
    "gold",        # p0 top-left
    "orange",      # p0 top-right
    "tomato",      # p0 bottom-right
    "coral",       # p0 bottom-left
    "deepskyblue", # p1 center
    "mediumpurple",# p1 top-left
    "plum",        # p1 top-right
    "violet",      # p1 bottom-right
    "lightblue",   # p1 bottom-left
]
KP_NAMES = [
    "p0:ctr", "p0:TL", "p0:TR", "p0:BR", "p0:BL",
    "p1:ctr", "p1:TL", "p1:TR", "p1:BR", "p1:BL",
]
# Corner order for drawing port rectangles: TL→TR→BR→BL→TL
_PORT_RECT_IDX = [1, 2, 3, 4]       # relative to port start (0=center)
_PORT_OFFSETS  = [0, 5]             # start index of port 0 and port 1

CLASS_NAMES = {0: "sfp_nic", 1: "sc_port"}


# ── YOLO I/O ──────────────────────────────────────────────────────────────────

def read_label(lbl_path: Path, img_w: int, img_h: int):
    """Parse label → (class_id, kp_pixels (N,2), vis (N,))."""
    parts = lbl_path.read_text().strip().split()
    n_kp  = (len(parts) - 5) // 3
    if n_kp < 1:
        return None, None, None
    class_id = int(parts[0])
    kps, vis = [], []
    for i in range(n_kp):
        base = 5 + i * 3
        kps.append([float(parts[base]) * img_w, float(parts[base+1]) * img_h])
        vis.append(int(float(parts[base+2])))
    return class_id, np.array(kps, dtype=np.float32), np.array(vis, dtype=np.int32)


def write_label(lbl_path: Path, class_id: int, kp: np.ndarray,
                vis: np.ndarray, img_w: int, img_h: int) -> None:
    visible = kp[vis > 0]
    if len(visible) == 0:
        return
    pad  = BBOX_PAD_PX
    x0   = max(0,         visible[:, 0].min() - pad)
    x1   = min(img_w - 1, visible[:, 0].max() + pad)
    y0   = max(0,         visible[:, 1].min() - pad)
    y1   = min(img_h - 1, visible[:, 1].max() + pad)
    parts = [
        str(class_id),
        f"{(x0+x1)/2/img_w:.6f}", f"{(y0+y1)/2/img_h:.6f}",
        f"{(x1-x0)/img_w:.6f}",   f"{(y1-y0)/img_h:.6f}",
    ]
    for i, (u, v) in enumerate(kp):
        if vis[i] > 0:
            parts += [f"{u/img_w:.6f}", f"{v/img_h:.6f}", "2"]
        else:
            parts += ["0.000000", "0.000000", "0"]
    lbl_path.write_text(" ".join(parts) + "\n")


def burn_keypoints(img_rgb: np.ndarray, kp: np.ndarray,
                   vis: np.ndarray) -> np.ndarray:
    """Return BGR image with visible keypoints and port rectangle outlines."""
    out = cv2.cvtColor(img_rgb, cv2.COLOR_RGB2BGR)

    # Draw port rectangles (connect corners in order TL→TR→BR→BL)
    for port_idx, port_start in enumerate(_PORT_OFFSETS):
        corners = []
        for rel in _PORT_RECT_IDX:
            ki = port_start + rel
            if ki < len(kp) and vis[ki] > 0:
                corners.append((int(round(kp[ki, 0])), int(round(kp[ki, 1]))))
        if len(corners) == 4:
            color = (0, 200, 100) if port_idx == 0 else (200, 100, 0)
            for j in range(4):
                cv2.line(out, corners[j], corners[(j+1) % 4], color, 1, cv2.LINE_AA)

    # Draw keypoints
    for i, (u, v) in enumerate(kp):
        pt = (int(round(u)), int(round(v)))
        r, g, b = [int(c*255) for c in mcolors.to_rgb(KP_COLORS[i % len(KP_COLORS)])]
        bgr = (b, g, r)
        if vis[i] > 0:
            cv2.circle(out, pt, KP_RADIUS,     bgr,         -1, cv2.LINE_AA)
            cv2.circle(out, pt, KP_RADIUS,     (255,255,255), 1, cv2.LINE_AA)
            cv2.line(out, (pt[0]-14,pt[1]),   (pt[0]+14,pt[1]),   (255,255,255), 1)
            cv2.line(out, (pt[0],pt[1]-14),   (pt[0],pt[1]+14),   (255,255,255), 1)
            cv2.putText(out, str(i), (pt[0]+12, pt[1]+5),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.45, (255,255,255), 1, cv2.LINE_AA)
        else:
            # invisible — small grey cross at (0,0), skip drawing
            pass
    return out


# ── Dataset discovery ─────────────────────────────────────────────────────────

def collect_pairs(root: Path):
    pairs = []
    def _scan(img_dir, lbl_dir, cls):
        for p in sorted(img_dir.glob("*.png")):
            lbl = lbl_dir / (p.stem + ".txt")
            if lbl.exists():
                pairs.append((p, lbl, cls))
    if (root / "images").is_dir():
        _scan(root / "images", root / "labels", root.name)
    else:
        for sub in sorted(root.iterdir()):
            if sub.is_dir() and (sub / "images").is_dir():
                _scan(sub / "images", sub / "labels", sub.name)
    return pairs


# ── Reviewer ──────────────────────────────────────────────────────────────────

class Reviewer:
    def __init__(self, pairs):
        self.pairs    = pairs
        self.idx      = 0
        self.selected = -1    # -1 = nothing selected
        self.kp       = None  # (N,2) current keypoints
        self.vis      = None  # (N,) visibility
        self.orig_kp  = None
        self.orig_vis = None
        self.modified = False
        self._pan_active = False
        self._pan_start  = None
        self._pan_xlim   = None
        self._pan_ylim   = None

        self.fig, self.ax = plt.subplots(figsize=(15, 10))
        self.fig.patch.set_facecolor("#1e1e1e")
        self.fig.canvas.manager.set_window_title("YOLO Label Reviewer")

        c = self.fig.canvas.mpl_connect
        c("button_press_event",   self._on_press)
        c("button_release_event", self._on_release)
        c("motion_notify_event",  self._on_motion)
        c("scroll_event",         self._on_scroll)
        c("key_press_event",      self._on_key)

        self._load()
        plt.tight_layout(pad=0.5)
        plt.show()

    # ── Data loading ──────────────────────────────────────────────────────────

    def _load(self):
        if self.idx >= len(self.pairs):
            print("All images reviewed.")
            plt.close(self.fig); return
        if self.idx < 0:
            self.idx = 0

        img_path, lbl_path, cls = self.pairs[self.idx]
        img_bgr = cv2.imread(str(img_path))
        if img_bgr is None:
            print(f"Cannot read {img_path} — skipping")
            self.idx += 1; self._load(); return

        self.img        = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2RGB)
        self.img_h, self.img_w = self.img.shape[:2]
        self.class_name = cls
        self.img_path   = img_path
        self.lbl_path   = lbl_path

        self.class_id, kp, vis = read_label(lbl_path, self.img_w, self.img_h)
        if kp is None:
            print(f"Cannot parse {lbl_path} — skipping")
            self.idx += 1; self._load(); return

        self.kp       = kp.copy()
        self.vis      = vis.copy()
        self.orig_kp  = kp.copy()
        self.orig_vis = vis.copy()
        self.selected = -1
        self.modified = False
        self._reset_view = True
        self._draw()

    # ── Drawing ───────────────────────────────────────────────────────────────

    def _draw(self):
        if self._reset_view:
            xlim = (0, self.img_w)
            ylim = (self.img_h, 0)
            self._reset_view = False
        else:
            xlim = self.ax.get_xlim()
            ylim = self.ax.get_ylim()

        self.ax.clear()
        self.ax.set_facecolor("#1e1e1e")
        self.ax.imshow(self.img, origin="upper")
        self.ax.set_xlim(xlim)
        self.ax.set_ylim(ylim)

        kp, vis = self.kp, self.vis

        # Bounding box (over visible keypoints only)
        visible = kp[vis > 0]
        if len(visible):
            pad = BBOX_PAD_PX
            self.ax.add_patch(Rectangle(
                (max(0, visible[:,0].min()-pad), max(0, visible[:,1].min()-pad)),
                min(self.img_w-1, visible[:,0].max()+pad) - max(0, visible[:,0].min()-pad),
                min(self.img_h-1, visible[:,1].max()+pad) - max(0, visible[:,1].min()-pad),
                lw=1, ec="white", fc="none", ls="--", alpha=0.5
            ))

        # Port rectangle outlines — connect corners of each port group
        for port_start in _PORT_OFFSETS:
            corners = []
            for rel in _PORT_RECT_IDX:
                ki = port_start + rel
                if ki < len(kp) and vis[ki] > 0:
                    corners.append(kp[ki])
            if len(corners) == 4:
                xs = [c[0] for c in corners] + [corners[0][0]]
                ys = [c[1] for c in corners] + [corners[0][1]]
                color = "limegreen" if port_start == 0 else "deepskyblue"
                self.ax.plot(xs, ys, "-", color=color, lw=1, alpha=0.6, zorder=3)

        # Keypoints
        for i, (u, v) in enumerate(kp):
            sel   = (i == self.selected)
            color = "red" if sel else KP_COLORS[i % len(KP_COLORS)]
            if vis[i] > 0:
                self.ax.add_patch(Circle((u, v), KP_RADIUS, color=color,
                                         ec="white", lw=1.2, zorder=5))
                if sel:
                    r2 = KP_RADIUS * 2.2
                    self.ax.plot([u-r2, u+r2], [v, v],    "w-", lw=0.8, zorder=4)
                    self.ax.plot([u, u], [v-r2, v+r2],    "w-", lw=0.8, zorder=4)
                self.ax.text(u + KP_RADIUS + 4, v + 4, KP_NAMES[i % len(KP_NAMES)],
                             color="white", fontsize=7.5, va="center", zorder=6,
                             bbox=dict(boxstyle="round,pad=0.1", fc="#0005", ec="none"))
            else:
                # Invisible keypoint — small grey ×
                self.ax.plot(u, v, "x", color="#666", ms=7, mew=1.2, zorder=4)

        # Title
        mod      = "  [modified *]" if self.modified else ""
        sel_hint = (f"  kp{self.selected} ({KP_NAMES[self.selected % len(KP_NAMES)]}) "
                    "selected — click to place"
                    if self.selected != -1 else "")
        tb_mode  = ""
        try:
            m = self.fig.canvas.toolbar.mode
            if m: tb_mode = f"  [{m} — toolbar active]"
        except Exception:
            pass

        self.ax.set_title(
            f"[{self.idx+1}/{len(self.pairs)}]  {self.class_name}{mod}{sel_hint}{tb_mode}\n"
            "scroll=zoom  right-drag=pan  h=reset  "
            "s=save+next  n=skip  b=back  r=reset-kps  d=delete  q=quit",
            color="white", fontsize=8.5, pad=6
        )
        self.ax.axis("off")
        self.fig.canvas.draw_idle()

    # ── Mouse events ──────────────────────────────────────────────────────────

    def _toolbar_active(self):
        try:
            return bool(self.fig.canvas.toolbar.mode)
        except Exception:
            return False

    def _on_press(self, event):
        if event.inaxes is not self.ax or event.xdata is None:
            return
        if event.button == 3:
            self._pan_active = True
            self._pan_start  = (event.xdata, event.ydata)
            self._pan_xlim   = self.ax.get_xlim()
            self._pan_ylim   = self.ax.get_ylim()
            return
        if event.button != 1 or self._toolbar_active():
            return
        x, y = event.xdata, event.ydata
        if self.selected == -1:
            # Find nearest VISIBLE keypoint
            best_d, best_i = float("inf"), -1
            for i, (u, v) in enumerate(self.kp):
                if self.vis[i] == 0:
                    continue
                d = math.hypot(u - x, v - y)
                if d < best_d:
                    best_d, best_i = d, i
            if best_d < SELECT_TOL:
                self.selected = best_i
                self._draw()
        else:
            self.kp[self.selected] = [
                float(np.clip(x, 0, self.img_w - 1)),
                float(np.clip(y, 0, self.img_h - 1)),
            ]
            self.selected = -1
            self.modified = True
            self._draw()

    def _on_release(self, event):
        if event.button == 3:
            self._pan_active = False

    def _on_motion(self, event):
        if not self._pan_active or event.inaxes is not self.ax or event.xdata is None:
            return
        dx = self._pan_start[0] - event.xdata
        dy = self._pan_start[1] - event.ydata
        self.ax.set_xlim(self._pan_xlim[0]+dx, self._pan_xlim[1]+dx)
        self.ax.set_ylim(self._pan_ylim[0]+dy, self._pan_ylim[1]+dy)
        self.fig.canvas.draw_idle()

    def _on_scroll(self, event):
        if event.inaxes is not self.ax or event.xdata is None:
            return
        f  = 1.0 / ZOOM_FACTOR if event.button == "up" else ZOOM_FACTOR
        x, y = event.xdata, event.ydata
        xl, yl = self.ax.get_xlim(), self.ax.get_ylim()
        self.ax.set_xlim(x-(x-xl[0])*f, x+(xl[1]-x)*f)
        self.ax.set_ylim(y-(y-yl[0])*f, y+(yl[1]-y)*f)
        self.fig.canvas.draw_idle()

    # ── Key events ────────────────────────────────────────────────────────────

    def _on_key(self, event):
        k = event.key
        if k in ("s", "enter"):
            write_label(self.lbl_path, self.class_id, self.kp,
                        self.vis, self.img_w, self.img_h)
            annotated = burn_keypoints(self.img, self.kp, self.vis)
            cv2.imwrite(str(self.img_path), annotated)
            print(f"[{self.idx+1}/{len(self.pairs)}] saved  "
                  f"{self.lbl_path.name}  +  {self.img_path.name}")
            self.idx += 1; self._load()
        elif k == "n":
            self.idx += 1; self._load()
        elif k == "b":
            self.idx = max(0, self.idx - 1); self._load()
        elif k == "r":
            self.kp  = self.orig_kp.copy()
            self.vis = self.orig_vis.copy()
            self.selected = -1; self.modified = False; self._draw()
        elif k == "d":
            self.lbl_path.with_suffix(".delete").touch()
            print(f"[{self.idx+1}/{len(self.pairs)}] marked for deletion: "
                  f"{self.img_path.name}")
            self.idx += 1; self._load()
        elif k in ("q", "escape"):
            print(f"Quit after reviewing {self.idx}/{len(self.pairs)} images.")
            plt.close(self.fig)
        elif k == "h":
            self._reset_view = True; self._draw()


# ── Purge ─────────────────────────────────────────────────────────────────────

def purge(root: Path):
    flags = list(root.rglob("*.delete"))
    if not flags:
        print("Nothing marked for deletion."); return
    for flag in flags:
        img = flag.parent.parent / "images" / flag.with_suffix(".png").name
        lbl = flag.parent.parent / "labels" / flag.with_suffix(".txt").name
        for p in (flag, img, lbl):
            if p.exists():
                p.unlink(); print(f"  deleted {p.name}")
    print(f"Purged {len(flags)} samples.")


# ── Entry point ───────────────────────────────────────────────────────────────

import math

def main():
    args = sys.argv[1:]
    if len(args) == 2 and args[0] == "--purge":
        purge(Path(args[1])); return
    if not args:
        print(__doc__); sys.exit(1)
    root  = Path(args[0])
    pairs = collect_pairs(root)
    if not pairs:
        print(f"No labeled image pairs found under: {root}"); sys.exit(1)
    print(f"Found {len(pairs)} labeled images under {root}")
    print("scroll=zoom  right-drag=pan  h=reset  "
          "s=save+next  n=skip  b=back  r=reset-kps  d=delete  q=quit")
    Reviewer(pairs)

if __name__ == "__main__":
    main()
