"""The screen-overlay animations, drawn from scratch (no game art), into art/frames/ (FRAME x FRAME, RGBA):

    swirl_NN.png  SWIRL_FRAMES frames of one turn: a black hole seen a little from above, spiral arms of violet light
                  winding into it, the hot disc with its streaks turning, the photon ring; it loops
    burst_NN.png  BURST_FRAMES frames of the collapse: a white-violet flash, a purple shock ring racing out, sparks
                  flying and fading
(core.png, the thrown core's glow, comes from Blender: render_frames.py.) Then pack_frames.py.

    python art/make_frames.py
"""
import math
from pathlib import Path

import numpy as np
from PIL import Image

OUT = Path(__file__).resolve().parent / "frames"
FRAME = 128
SS = 3                      # drawn at 3x and shrunk: smooth edges
SWIRL_FRAMES = 16
BURST_FRAMES = 12
rng = np.random.default_rng(154)


def grid():
    n = FRAME * SS
    y, x = (np.mgrid[0:n, 0:n] + 0.5) / SS - FRAME / 2
    return x, y


def over(dst, col, alpha):
    a = np.clip(alpha, 0, 1)[..., None]
    dst[..., :3] = np.asarray(col) * a + dst[..., :3] * (1 - a)
    dst[..., 3] = a[..., 0] + dst[..., 3] * (1 - a[..., 0])


def add(dst, col, alpha):
    """Light added on top (glows)."""
    a = np.clip(alpha, 0, 1)[..., None]
    dst[..., :3] = np.clip(dst[..., :3] * dst[..., 3:4] + np.asarray(col) * a, 0, 1) / np.maximum(
        np.clip(dst[..., 3:4] + a, 0, 1), 1e-6)
    dst[..., 3] = np.clip(dst[..., 3] + a[..., 0], 0, 1)


def mix(a, b, t):
    t = np.clip(t, 0, 1)[..., None]
    return np.asarray(a) * (1 - t) + np.asarray(b) * t


def save(img, name):
    OUT.mkdir(exist_ok=True)
    im = Image.fromarray(np.clip(img * 255 + 0.5, 0, 255).astype(np.uint8), "RGBA")
    im.resize((FRAME, FRAME), Image.LANCZOS).save(OUT / name)


def swirl(i):
    x, y = grid()
    phase = 2 * math.pi * i / SWIRL_FRAMES
    img = np.zeros(x.shape + (4,))
    # Seen 30 degrees from above: the plane's y is squashed.
    sq = 0.42
    px, py = x, y / sq
    r = np.sqrt(px ** 2 + py ** 2)
    ang = np.arctan2(py, px)
    hole_r = 15.0
    # Spiral arms of violet light winding in (log spiral), turning with the phase.
    arms = 0.5 + 0.5 * np.cos(3 * (ang + phase) + np.log(np.maximum(r, 1)) * 5.5)
    arm_fade = np.clip((r - hole_r) / 6, 0, 1) * np.clip((62 - r) / 22, 0, 1)
    arm_col = mix((0.35, 0.1, 0.85), (0.85, 0.45, 1.0), arms)
    add(img, (0.25, 0.05, 0.5), np.clip(1 - r / 64, 0, 1) ** 1.5 * 0.55)          # a violet haze
    add(img, arm_col, (arms ** 3) * arm_fade * 0.85)
    # The hot disc: streaks around it turning, white-orange near the hole.
    streak = 0.5 + 0.5 * np.cos(7 * (ang + phase * 1.6) + r * 0.35)
    disc_t = np.clip((r - hole_r) / (38 - hole_r), 0, 1)
    disc_a = np.clip((r - hole_r + 1) / 2, 0, 1) * np.clip((38 - r) / 10, 0, 1) * (0.55 + 0.45 * streak)
    disc_col = mix((1.0, 0.95, 0.85), (1.0, 0.5, 0.25), disc_t)
    disc_col = mix(disc_col, (0.6, 0.2, 0.9), np.clip(disc_t * 1.4 - 0.4, 0, 1))
    back = y < 0                                     # the far half of the disc, behind the hole
    add(img, disc_col, disc_a * back)
    # The event horizon (round: seen from any side) and the photon ring.
    rr = np.sqrt(x ** 2 + y ** 2)
    over(img, (0, 0, 0), np.clip((hole_r - rr) * 1.2, 0, 1))
    add(img, (1.0, 0.9, 1.0), np.exp(-((rr - hole_r - 0.6) / 1.1) ** 2) * 0.95)
    add(img, disc_col, disc_a * ~back)               # the near half crosses in front
    save(img, "swirl_%02d.png" % i)


def burst(i):
    x, y = grid()
    t = i / (BURST_FRAMES - 1)
    img = np.zeros(x.shape + (4,))
    r = np.sqrt(x ** 2 + y ** 2)
    ang = np.arctan2(y, x)
    # The flash: white-violet core, big at once, shrinking and fading.
    core_r = 34 * (1 - t) ** 0.7 + 4
    add(img, (0.95, 0.8, 1.0), np.clip(1 - r / core_r, 0, 1) ** 1.2 * (1 - t) ** 0.8)
    add(img, (0.7, 0.25, 1.0), np.clip(1 - r / (core_r * 1.7), 0, 1) * (1 - t) * 0.8)
    # The shock ring racing out.
    ring_r = 8 + 54 * t ** 0.6
    width = 3 + 6 * t
    wobble = 1 + 0.08 * np.cos(ang * 9 + t * 4)
    ring = np.exp(-((r - ring_r * wobble) / width) ** 2) * (1 - t) ** 0.9
    add(img, mix((1.0, 0.85, 1.0), (0.6, 0.15, 1.0), np.full(r.shape, t)), ring)
    # Sparks: flecks flying out along fixed directions.
    for k in range(18):
        a = 2 * math.pi * k / 18 + 0.17 * math.sin(k * 7)
        d = (10 + 50 * t ** 0.7) * (0.7 + 0.5 * ((k * 37) % 10) / 10)
        sx, sy = math.cos(a) * d, math.sin(a) * d
        spark = np.exp(-(((x - sx) ** 2 + (y - sy) ** 2) / (2.2 + 2 * t) ** 2))
        add(img, (1.0, 0.75, 1.0), spark * (1 - t) ** 1.3)
    save(img, "burst_%02d.png" % i)


for i in range(SWIRL_FRAMES):
    swirl(i)
for i in range(BURST_FRAMES):
    burst(i)
print("frames in", OUT)
