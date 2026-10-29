"""Concussion Cannon's textures and HUD icon, drawn from scratch (no game art), into art/textures/*.png:

  The held cannon (opaque; the game lights models by vertex colour only, so the light from above is baked in: the
  barrel is an 8-sided lathe, u around it, and each 1/8 of the texture's width is one face, shaded by how far it
  faces up):
    metal.png      64 x 32  gunmetal panels, a deep blue stripe, seams and rivets
    coil.png       32 x 16  the coils round the barrel and the muzzle's lip: cyan, white-hot at the ridge
    core.png       32 x 16  the glowing core window: cyan with white arcs crackling round it
    muzzle.png     16 x 16  inside the flared muzzle: cyan at the lip to white at the throat
    grip.png       32 x 8   the grip: four 8-pixel strips, light to dark (the box's faces pick theirs), with grooves
  The effects (soft alpha, so 32 x 32 at most: RGBA32 in the game):
    wave.png       32 x 32  the cone shockwave's outer shells: u around, v from apex (top row) to the open end
                            (bottom): streaks running outward, fading in from the apex, a bright rim with a deep blue
                            edge
    wave2.png      32 x 32  its inner shell: thinner, whiter streaks
    orb.png        16 x 16  the charge orb (opaque): white-cyan with veins
    orb_glow.png   32 x 32  the orb's glow shell: crackling arcs on faint blue
    impact.png     32 x 32  the wall-slam burst's spikes: u across a spike, v from its base (top) to its tip (bottom)
    impact_glow.png 16 x 16 the burst's puff shell
  The HUD:
    icon.png       64 x 64  the cannon side-on, firing two shock arcs, on clear (and icon_big.png 256 x 256);
                            hud_icon.png 32 x 22 and hud_icon_big.png 176 x 120 are cropped from them to fill
  and previews/textures.png, every texture above enlarged on a checkerboard.

    python make_textures.py
"""
import math
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFilter

HERE = Path(__file__).resolve().parent
OUT = HERE / "textures"
PREVIEW = HERE / "previews"
rng = np.random.default_rng(310)

SIDES = 8                                             # the cannon lathe's sides (build_models.py SIDES)
DEEP = (0.03, 0.10, 0.42)                             # the palette: deep blue edge, electric blue, cyan, white
BLUE = (0.10, 0.42, 1.00)
CYAN = (0.35, 0.95, 1.00)
WHITE = (0.92, 1.00, 1.00)
GUNMETAL = (0.36, 0.40, 0.50)


def save(name, rgba):
    OUT.mkdir(exist_ok=True)
    Image.fromarray(np.clip(rgba * 255 + 0.5, 0, 255).astype(np.uint8), "RGBA").save(OUT / name)


def mix(a, b, t):
    t = np.clip(t, 0, 1)[..., None]
    return np.asarray(a) * (1 - t) + np.asarray(b) * t


def ramp(t, stops):
    """Colour along t (0..1) through evenly spaced colour stops."""
    t = np.clip(t, 0, 1) * (len(stops) - 1)
    i = np.minimum(t.astype(int), len(stops) - 2)
    out = np.zeros(t.shape + (3,))
    for k in range(len(stops) - 1):
        m = i == k
        out[m] = mix(stops[k], stops[k + 1], (t - k))[m]
    return out


def noise(w, h, scale, octaves=3, wrap_x=True):
    """Tileable value noise (wraps in x so a ring joins up), 0..1."""
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


def face_light(w, lo=0.42, hi=1.0):
    """Per column: the baked light of the lathe face it lands on (face i covers angles i/SIDES..(i+1)/SIDES of a turn;
    angle 90 degrees is the top), a little brighter on the left."""
    face = (np.arange(w) * SIDES) // w
    a = 2 * np.pi * (face + 0.5) / SIDES
    up = 0.5 + 0.5 * np.sin(a)
    return lo + (hi - lo) * np.clip(up + 0.12 * np.cos(a), 0, 1)


def metal():
    w, h = 64, 32
    light = face_light(w)[None, :]
    n = noise(w, h, 8, 2)
    col = np.asarray(GUNMETAL) * (0.85 + 0.3 * n)[..., None]
    y, x = np.mgrid[0:h, 0:w]
    stripe = (y >= 9) & (y <= 11)
    col[stripe] = mix(col, (0.12, 0.25, 0.65), np.full((h, w), 0.85))[stripe]
    col[(y == 8) | (y == 12)] *= 0.55                  # the stripe's edges
    col[(y == 0) | (y == 21)] *= 0.45                  # panel seams across the barrel
    col[x % (w // SIDES) == 0] *= 0.6                  # the lathe's edges
    rivet = (x % (w // SIDES) == w // SIDES // 2) & ((y == 3) | (y == 25))
    col[rivet] = (0.75, 0.82, 0.9)
    col = col * light[..., None]
    col[(y == 1) & ~stripe] += 0.05                    # a faint bevel catch under each seam
    save("metal.png", np.dstack([col, np.ones((h, w))]))


def coil():
    """v across the coil's ridge (top row the near foot, middle the ridge, bottom the far foot)."""
    w, h = 32, 16
    v = (np.arange(h) + 0.5) / h
    ridge = 1 - np.abs(v - 0.5) * 2                     # 0 at the feet, 1 on the ridge
    light = face_light(w, 0.7, 1.0)
    t = np.outer(ridge, np.ones(w))
    col = ramp(t, (DEEP, BLUE, CYAN, WHITE)) * light[None, :, None]
    col[:, ::w // SIDES] *= 0.75
    save("coil.png", np.dstack([col, np.ones((h, w))]))


def lightning(w, h, lines, jag=0.22):
    """Bright 0..1 where jagged lines wrap round in u (random walks pinned to join at the seam)."""
    out = np.zeros((h, w))
    y = np.arange(h)[:, None]
    for _ in range(lines):
        walk = np.cumsum(rng.standard_normal(w)) * jag * h / 4
        walk -= np.linspace(0, walk[-1] - walk[0], w)   # end where it starts, so it wraps
        centre = rng.uniform(0.3, 0.7) * h + walk - walk.mean()
        out = np.maximum(out, np.exp(-((y - centre[None, :]) / 0.9) ** 2))
    return out


def core():
    w, h = 32, 16
    v = (np.arange(h) + 0.5) / h
    body = 1 - np.abs(v - 0.5) * 2
    n = noise(w, h, 6, 2)
    col = ramp(np.outer(body * 0.55 + 0.25, np.ones(w)) + (n - 0.5) * 0.25, (BLUE, CYAN, WHITE))
    col = mix(col, WHITE, lightning(w, h, 2))
    save("core.png", np.dstack([col, np.ones((h, w))]))


def muzzle():
    w = h = 16
    v = (np.arange(h) + 0.5) / h                      # 0 at the lip, 1 at the throat
    u = (np.arange(w) + 0.5) / w
    streak = 0.5 + 0.5 * np.cos(2 * np.pi * u * 4)
    t = np.outer(v, np.ones(w)) * 0.85 + np.outer(np.ones(h), streak) * 0.2
    save("muzzle.png", np.dstack([ramp(t, (BLUE, CYAN, WHITE, WHITE)), np.ones((h, w))]))


def grip():
    w, h = 32, 8
    shade = np.repeat([1.0, 0.78, 0.6, 0.42], 8)[None, :]
    col = np.full((h, w, 3), (0.24, 0.27, 0.36)) * shade[..., None]
    col[1::2] *= 0.7                                   # grooves
    col[:, 3::8] = col[:, 3::8] * 0.5 + np.asarray(BLUE) * 0.35  # a blue inlay line down each face
    save("grip.png", np.dstack([col, np.ones((h, w))]))


def wave(name="wave.png", lines=1.0, whiten=0.0, base_alpha=0.6):
    """v from the apex (0) to the open end (1). Streaks run along v, leaning a little so they twist as it spreads."""
    w = h = 32
    v = (np.arange(h) + 0.5) / h
    u = (np.arange(w) + 0.5) / w
    uu, vv = np.meshgrid(u, v)
    s = noise(w, 4, 4 / lines, 3)                      # streak strength by u (wraps)
    shift = (vv * 3).astype(int)                       # lean: each third of the length slides one pixel round
    s = s[np.zeros_like(shift), (np.arange(w)[None, :] + shift) % w]
    s = np.clip((s - 0.35) / 0.5, 0, 1) ** 1.5
    t = np.clip(s * 0.65 + vv ** 2 * 0.45 + whiten, 0, 1)
    col = ramp(t, (DEEP, BLUE, CYAN, WHITE))
    alpha = np.clip(vv / 0.25, 0, 1) ** 1.2 * (base_alpha + (1.0 - base_alpha) * s)
    # The rim: white-hot at 85..95 % of the way, its last rows deep blue.
    rim = np.exp(-((vv - 0.9) / 0.05) ** 2)
    col = mix(col, WHITE, rim)
    alpha = np.maximum(alpha, rim)
    edge = vv > 0.95
    col[edge] = mix(col, BLUE, np.full_like(vv, 0.8))[edge]
    alpha[edge] = 0.9
    col[vv > 0.98] = DEEP
    save(name, np.dstack([col, alpha]))


def orb():
    w = h = 16
    n = noise(w, h, 4, 2)
    veins = np.clip(1 - np.abs(n - 0.5) / 0.08, 0, 1)
    col = mix(mix(CYAN, WHITE, n * 1.2), BLUE, veins * 0.8)
    save("orb.png", np.dstack([col, np.ones((h, w))]))


def orb_glow():
    w = h = 32
    arcs = lightning(w, h, 3, 0.12)
    col = mix(BLUE, WHITE, arcs * 1.1)
    alpha = 0.22 + 0.73 * arcs
    save("orb_glow.png", np.dstack([col, alpha]))


def impact():
    """A spike: its base along the top row, its tip at the bottom middle. White at the base, a white core line,
    cyan then deep blue toward the tip and the sides, fading out."""
    w = h = 32
    v = (np.arange(h) + 0.5) / h
    u = (np.arange(w) + 0.5) / w
    uu, vv = np.meshgrid(u, v)
    core_line = np.exp(-((uu - 0.5) / (0.09 + 0.12 * (1 - vv))) ** 2)
    t = np.clip((1 - vv) * 0.6 + core_line * 0.5, 0, 1)
    col = ramp(t, (DEEP, BLUE, CYAN, WHITE))
    alpha = np.clip((1 - vv) ** 1.2 * (0.35 + 0.65 * core_line) + (1 - vv) * 0.25, 0, 1)
    save("impact.png", np.dstack([col, alpha]))


def impact_glow():
    w = h = 16
    n = noise(w, h, 4, 2)
    col = mix(CYAN, WHITE, n)
    save("impact_glow.png", np.dstack([col, 0.35 + 0.35 * n]))


def icon(size=64, name="icon.png"):
    """The cannon side-on, muzzle to the right, two shock arcs leaving it. Drawn at 8x in 72-unit coordinates and
    shrunk, so its edges are smooth; then a dark outline so it reads on any background, as the game's icons do."""
    s = 8 * size / 64
    n = int(64 * s)
    im = Image.new("RGBA", (n, n), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)

    def c(rgb, a=1.0):
        return tuple(int(round(k * 255)) for k in rgb) + (int(a * 255),)

    k = 0.8                                            # the design is 72 units wide: fit it in 64

    def P(pts):
        return [(((x - 2) * k + 1) * s, ((y - 30) * k + 32) * s) for x, y in pts]

    def box(x0, y0, x1, y1, col, r=0):
        d.rounded_rectangle(P([(x0, y0), (x1, y1)]), radius=r * k * s, fill=col)

    dark, mid, light = (0.17, 0.2, 0.3), (0.34, 0.39, 0.52), (0.6, 0.67, 0.8)
    # The shock arcs, behind the muzzle's mouth.
    for r, wdt, col in ((16, 3.6, BLUE), (9.5, 3.4, CYAN)):
        bb = P([(55 - r, 30 - r * 1.25), (55 + r, 30 + r * 1.25)])
        d.arc(bb, -58, 58, fill=c(col), width=int(wdt * k * s))
        d.arc(bb, -50, 50, fill=c(WHITE), width=int(wdt * k * s * 0.35))
    # The grip, raked back.
    d.polygon(P([(12, 33), (21, 33), (17, 50), (8, 50)]), fill=c(dark))
    d.polygon(P([(18, 33), (21, 33), (17, 50), (14, 50)]), fill=c(mid))
    # The body, its rear cap and the barrel.
    box(2, 22, 34, 38, c(mid), 3)
    box(2, 22, 34, 25.5, c(light), 2)
    box(2, 34, 34, 38, c(dark), 2)
    box(1, 24, 5, 36, c(dark), 1.5)
    box(4, 29, 33, 31, c((0.12, 0.25, 0.65)))          # the deep blue stripe
    box(32, 25, 44, 35, c(mid))
    box(32, 25, 44, 27, c(light))
    box(32, 33, 44, 35, c(dark))
    # The core window, glowing.
    box(10, 25, 23, 34, c(BLUE), 2)
    box(11, 26.5, 22, 32.5, c(CYAN), 1.5)
    box(12, 28.5, 21, 30.5, c(WHITE), 1)
    # The coils.
    for x in (33.5, 37.5, 41.5):
        box(x, 20.5, x + 2.6, 39.5, c(BLUE), 1.2)
        box(x + 0.5, 21.5, x + 2.1, 38.5, c(CYAN), 0.8)
        box(x + 1.0, 23, x + 1.6, 37, c(WHITE))
    # The flared muzzle, and its glowing mouth.
    d.polygon(P([(44, 25), (54, 15.5), (57, 15.5), (57, 44.5), (54, 44.5), (44, 35)]), fill=c(mid))
    d.polygon(P([(44, 25), (54, 15.5), (57, 15.5), (57, 19), (44, 28)]), fill=c(light))
    d.polygon(P([(44, 32), (57, 41), (57, 44.5), (54, 44.5), (44, 35)]), fill=c(dark))
    d.ellipse(P([(54.5, 16.5), (60, 43.5)]), fill=c(BLUE))
    d.ellipse(P([(55.5, 19), (59.3, 41)]), fill=c(CYAN))
    d.ellipse(P([(56.5, 23), (58.6, 37)]), fill=c(WHITE))

    img = im.resize((size, size), Image.LANCZOS)
    px = np.asarray(img).astype(float) / 255
    a8 = px[..., 3]
    ring = np.asarray(Image.fromarray((a8 * 255).astype(np.uint8)).filter(ImageFilter.MaxFilter(3))) / 255.0
    outline = np.clip(ring - a8, 0, 1)
    px[..., :3] = px[..., :3] * (1 - outline[..., None]) + np.array((0.0, 0.03, 0.12)) * outline[..., None]
    px[..., 3] = np.maximum(a8, outline * 0.9)
    save(name, px)


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


def preview_sheet():
    """Every texture enlarged (nearest) on a checkerboard, with its name and size, in previews/textures.png."""
    names = ["metal.png", "coil.png", "core.png", "muzzle.png", "grip.png", "wave.png", "wave2.png", "orb.png",
             "orb_glow.png", "impact.png", "impact_glow.png", "icon.png", "hud_icon.png", "hud_icon_big.png"]
    tiles = []
    for nm in names:
        im = Image.open(OUT / nm).convert("RGBA")
        k = max(1, min(256 // im.size[0], 160 // im.size[1]))
        big = im.resize((im.size[0] * k, im.size[1] * k), Image.NEAREST)
        tiles.append((nm, im.size, big))
    cols, cw, ch = 4, 280, 200
    rows = (len(tiles) + cols - 1) // cols
    sheet = Image.new("RGBA", (cols * cw, rows * ch), (24, 26, 34, 255))
    d = ImageDraw.Draw(sheet)
    for i, (nm, size, big) in enumerate(tiles):
        x0, y0 = (i % cols) * cw + 12, (i // cols) * ch + 8
        chk = Image.new("RGBA", big.size)
        cd = ImageDraw.Draw(chk)
        for yy in range(0, big.size[1], 8):
            for xx in range(0, big.size[0], 8):
                g = 90 if (xx // 8 + yy // 8) % 2 else 60
                cd.rectangle((xx, yy, xx + 7, yy + 7), fill=(g, g, g, 255))
        chk.alpha_composite(big)
        sheet.paste(chk, (x0, y0 + 16))
        d.text((x0, y0), f"{nm}  {size[0]} x {size[1]}", fill=(220, 230, 240, 255))
    PREVIEW.mkdir(exist_ok=True)
    sheet.save(PREVIEW / "textures.png")


for f in (metal, coil, core, muzzle, grip, wave, orb, orb_glow, impact, impact_glow, icon):
    f()
wave("wave2.png", lines=2.0, whiten=0.25, base_alpha=0.4)
icon(256, "icon_big.png")
fit("icon.png", 32, 22, "hud_icon.png")            # the game's HUD sprite (as its gun icons)
fit("icon_big.png", 176, 120, "hud_icon_big.png")  # the big one, drawn sharp by mods' HUDs
preview_sheet()
print("textures in", OUT)
