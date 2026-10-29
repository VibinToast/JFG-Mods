"""Singularity's textures and HUD icon, drawn from scratch (no game art), into art/textures/*.png:

    core.png      32 x 32  the thrown core: near-black violet with glowing magenta veins
    band.png      64 x 16  the energy band orbiting the core: cyan to violet, see-through at its edges
    horizon.png   16 x 16  the black hole's event horizon: black with a faint violet sheen
    disc.png      64 x 32  the accretion disc, u around it and v outward: hot white-orange inside, violet streaks out to
                           nothing (the disc spins, so the streaks swirl)
    rim.png       32 x 8   the photon ring hugging the horizon: a thin bright line
    blast.png     32 x 32  the collapse blast's shell: white-hot middle, violet shock edge
    icon.png      64 x 64  the HUD icon (the weapon panel and selector): the black hole and its disc, on clear
                           (and icon_big.png 256 x 256; hud_icon.png 32 x 22 and hud_icon_big.png 176 x 120 from them,
                           cropped to fill: the game's sprite and the big icon mods' HUDs draw)
    disc2.png     32 x 32  the 3D black hole's spinning disc (32 x 32 keeps its soft alpha in the game: RGBA32)
    arms.png      32 x 32  its spiral arms ring
    glow.png      16 x 16  the glow shell round its sphere

    python make_textures.py
"""
import math
from pathlib import Path

import numpy as np
from PIL import Image, ImageFilter

OUT = Path(__file__).resolve().parent / "textures"
rng = np.random.default_rng(154)


def save(name, rgba):
    OUT.mkdir(exist_ok=True)
    Image.fromarray(np.clip(rgba * 255 + 0.5, 0, 255).astype(np.uint8), "RGBA").save(OUT / name)


def mix(a, b, t):
    t = np.clip(t, 0, 1)[..., None]
    return np.asarray(a) * (1 - t) + np.asarray(b) * t


def noise(w, h, scale, octaves=3, wrap_x=True):
    """Tileable value noise (wraps in x so a band joins up), 0..1."""
    total = np.zeros((h, w))
    amp, norm = 1.0, 0.0
    for o in range(octaves):
        cw, ch = max(2, int(w / scale) * (2 ** o)), max(2, int(h / scale) * (2 ** o))
        grid = rng.random((ch + 1, cw + 1))
        if wrap_x:
            grid[:, -1] = grid[:, 0]
        img = Image.fromarray((grid * 255).astype(np.uint8)).resize((w, h), Image.BICUBIC)
        total += np.asarray(img) / 255.0 * amp
        norm += amp
        amp *= 0.5
    return total / norm


def core():
    w = h = 32
    n = noise(w, h, 8, 3)
    veins = np.abs(n - 0.5) < 0.06                    # thin contour lines read as veins
    base = mix((0.05, 0.02, 0.09), (0.16, 0.05, 0.24), n)
    glow = mix(base, (1.0, 0.3, 0.95), veins.astype(float))
    rgba = np.dstack([glow, np.ones((h, w))])
    save("core.png", rgba)


def band():
    w, h = 64, 16
    v = (np.arange(h) + 0.5) / h
    u = (np.arange(w) + 0.5) / w
    across = 1 - np.abs(v - 0.5) * 2                  # 1 in the middle, 0 at the edges
    pulse = 0.65 + 0.35 * np.sin(u * math.pi * 2 * 4)  # four bright knots around the band
    t = np.outer(across ** 1.5, pulse)
    col = mix((0.45, 0.15, 1.0), (0.55, 1.0, 1.0), t)
    alpha = np.clip(np.outer(across, np.ones(w)) * 1.4 - 0.1, 0, 1)
    save("band.png", np.dstack([col, alpha]))


def horizon():
    w = h = 16
    n = noise(w, h, 4, 2)
    col = mix((0.0, 0.0, 0.0), (0.07, 0.02, 0.12), n)
    save("horizon.png", np.dstack([col, np.ones((h, w))]))


def disc():
    w, h = 64, 32
    v = (np.arange(h) + 0.5) / h                      # 0 at the inner edge, 1 at the outer
    u = (np.arange(w) + 0.5) / w
    streaks = noise(w, 4, 6, 3)                       # streaks run around the disc (u)
    streaks = np.asarray(Image.fromarray((streaks * 255).astype(np.uint8)).resize((w, h), Image.BICUBIC)) / 255.0
    heat = np.outer(1 - v, np.ones(w))
    heat = np.clip(heat * 1.15 + (streaks - 0.5) * 0.5, 0, 1)
    col = np.where(heat[..., None] > 0.6,
                   mix((1.0, 0.55, 0.25), (1.0, 0.95, 0.85), (heat - 0.6) / 0.4),
                   mix((0.35, 0.08, 0.75), (1.0, 0.55, 0.25), heat / 0.6))
    inner = np.clip(np.outer(v, np.ones(w)) / 0.08, 0, 1)             # a hard inner edge, soft outer fade
    outer = np.clip((1 - np.outer(v, np.ones(w))) / 0.45, 0, 1)
    alpha = inner * outer * (0.55 + 0.45 * streaks)
    save("disc.png", np.dstack([col, alpha]))


def rim():
    w, h = 32, 8
    v = (np.arange(h) + 0.5) / h
    across = np.exp(-((v - 0.5) / 0.18) ** 2)
    col = mix((0.6, 0.35, 1.0), (1.0, 1.0, 1.0), across)
    save("rim.png", np.dstack([np.repeat(col[:, None, :], w, 1), np.repeat(across[:, None], w, 1)]))


def blast():
    w = h = 32
    y, x = np.mgrid[0:h, 0:w]
    n = noise(w, h, 6, 3)
    t = np.clip(n * 1.3 - 0.15, 0, 1)
    col = np.where(t[..., None] > 0.5, mix((0.85, 0.5, 1.0), (1.0, 1.0, 1.0), (t - 0.5) * 2),
                   mix((0.3, 0.05, 0.6), (0.85, 0.5, 1.0), t * 2))
    alpha = 0.55 + 0.45 * t
    save("blast.png", np.dstack([col, alpha]))


def icon(size=64, name="icon.png"):
    """Drawn at 4x and shrunk, so its edges are smooth."""
    s = 4
    n = size * s
    y, x = ((np.mgrid[0:n, 0:n] + 0.5) / s - size / 2) * (64.0 / size)
    # The disc: an ellipse (seen from a little above), tilted, behind and in front of the hole.
    a = math.radians(-18)
    xr, yr = x * math.cos(a) - y * math.sin(a), x * math.sin(a) + y * math.cos(a)
    e = np.sqrt((xr / 29) ** 2 + (yr / 9.5) ** 2)
    ang = np.arctan2(yr / 9.5, xr / 29)
    swirl = 0.5 + 0.5 * np.sin(ang * 3 + e * 9)
    disc_a = np.clip((1 - e) / 0.12, 0, 1) * np.clip((e - 0.42) / 0.1, 0, 1)
    heat = np.clip((1 - e) * 1.6 + swirl * 0.3 - 0.2, 0, 1)
    disc_c = mix((0.45, 0.12, 0.9), (1.0, 0.7, 0.35), heat)
    disc_c = mix(disc_c, (1.0, 0.97, 0.9), np.clip(heat - 0.75, 0, 1) * 4)
    r = np.sqrt(x ** 2 + y ** 2)
    hole = np.clip((12.5 - r) * 1.5, 0, 1)
    rim_a = np.exp(-((r - 13.0) / 1.1) ** 2)
    glow_a = np.clip(1 - r / 30, 0, 1) ** 2 * 0.55
    front = yr > 0                                    # the near half of the disc crosses in front of the hole
    out = np.zeros((n, n, 4))
    out[..., :3] = (0.55, 0.25, 1.0)
    out[..., 3] = glow_a
    def over(col, alpha):
        al = np.clip(alpha, 0, 1)[..., None]
        out[..., :3] = np.asarray(col) * al + out[..., :3] * (1 - al)
        out[..., 3] = al[..., 0] + out[..., 3] * (1 - al[..., 0])
    over(disc_c, disc_a * ~front)
    over(np.broadcast_to((1.0, 0.92, 1.0), (n, n, 3)), rim_a)
    over(np.broadcast_to((0.0, 0.0, 0.0), (n, n, 3)), hole)
    over(disc_c, disc_a * front)
    # A dark outline so it reads on any background, as the game's icons do.
    alpha = out[..., 3]
    img = Image.fromarray(np.clip(out * 255, 0, 255).astype(np.uint8), "RGBA").resize((size, size), Image.LANCZOS)
    a8 = np.asarray(img)[..., 3].astype(float) / 255
    ring = np.asarray(Image.fromarray((a8 * 255).astype(np.uint8)).filter(ImageFilter.MaxFilter(3))) / 255.0
    px = np.asarray(img).astype(float) / 255
    outline = np.clip(ring - a8, 0, 1)
    px[..., :3] = px[..., :3] * (1 - outline[..., None]) + np.array((0.05, 0.0, 0.1)) * outline[..., None]
    px[..., 3] = np.maximum(a8, outline * 0.9)
    save(name, px)


def disc2():
    """32 x 32, u around the disc (it repeats round it), v outward: white-hot at the inner edge, through pink to
    violet, with streaks slanting so the spin reads as a swirl; mostly opaque."""
    w = h = 32
    v = (np.arange(h) + 0.5) / h
    u = (np.arange(w) + 0.5) / w
    uu, vv = np.meshgrid(u, v)
    streak = 0.5 + 0.5 * np.cos(2 * np.pi * (uu * 2 + vv * 1.5))
    heat = np.clip(1 - vv * 1.1 + (streak - 0.5) * 0.35, 0, 1)
    col = np.where(heat[..., None] > 0.6, mix((1.0, 0.55, 0.85), (1.0, 0.97, 1.0), (heat - 0.6) / 0.4),
                   mix((0.4, 0.1, 0.85), (1.0, 0.55, 0.85), heat / 0.6))
    alpha = np.clip((1 - vv) / 0.25, 0, 1) * (0.75 + 0.25 * streak)
    alpha = np.maximum(alpha, 0.0) * np.clip(vv / 0.06, 0.6, 1)
    save("disc2.png", np.dstack([col, alpha]))


def arms():
    """32 x 32 for the spiral arms ring: u around, v outward; two bright violet arms slanting across (a spiral when
    wrapped round), see-through between them, fading at both edges."""
    w = h = 32
    v = (np.arange(h) + 0.5) / h
    u = (np.arange(w) + 0.5) / w
    uu, vv = np.meshgrid(u, v)
    arm = np.clip(np.cos(2 * np.pi * (uu * 2 - vv * 0.9)), 0, 1) ** 2
    edge = np.clip(vv / 0.2, 0, 1) * np.clip((1 - vv) / 0.35, 0, 1)
    col = mix((0.35, 0.08, 0.8), (0.9, 0.6, 1.0), arm)
    alpha = np.clip(arm * 0.95 + 0.15, 0, 1) * edge
    save("arms.png", np.dstack([col, alpha]))


def glow():
    """16 x 16 for the glow shell round the sphere: violet, half see-through."""
    w = h = 16
    n = noise(w, h, 4, 2)
    col = mix((0.45, 0.12, 0.85), (0.75, 0.4, 1.0), n)
    save("glow.png", np.dstack([col, np.full((h, w), 0.25)]))


for f in (core, band, horizon, disc, rim, blast, icon, disc2, arms, glow):
    f()
icon(256, "icon_big.png")


def fit(src, w, h, out, threshold=60):
    """The picture's solid part (alpha over threshold) scaled to fill w x h, centred: the HUD icons."""
    im = Image.open(OUT / src).convert("RGBA")
    box = im.split()[3].point(lambda a: 255 if a > threshold else 0).getbbox()
    im = im.crop(box)
    k = min(w / im.size[0], h / im.size[1])
    im = im.resize((max(1, round(im.size[0] * k)), max(1, round(im.size[1] * k))), Image.LANCZOS)
    canvas = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    canvas.paste(im, ((w - im.size[0]) // 2, (h - im.size[1]) // 2), im)
    canvas.save(OUT / out)


fit("icon.png", 32, 22, "hud_icon.png")       # the game's HUD sprite (as its gun icons)
fit("icon_big.png", 176, 120, "hud_icon_big.png")  # the big one, drawn sharp by mods' HUDs
print("textures in", OUT)
