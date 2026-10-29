"""Rolling Shellback's textures, drawn from scratch (no game art), into art/textures/*.png:

  The beetle (opaque; the game lights models by vertex colour only, so a light from above is baked in):
    shell.png      64 x 32  the shell plates. Each half is one plate's outside: u across the plate from its right
                            side, over the top, to its left side (lit by how far it faces up), v along it from the
                            front edge (top row) to the rear edge (bottom row), a pale bronze lip along both edges.
                            The left half is the plain plate; the right half the middle plate, with the three spine
                            slits glowing amber
    belly.png      32 x 32  the soft underside: glowing amber, segment lines across, hottest down the middle of the
                            belly; u around the body, v from the front (top row) to the rear
    glow.png       16 x 16  the weak spot and the eyes: white-hot in the middle through amber to a deep orange rim
    parts.png      32 x 16  the legs (top half) and the head (bottom half): four 8-pixel strips each, light to dark
                            (the tubes' and boxes' faces pick theirs); the darkest leg strip is the plates' inside
  The effects:
    spine.png      16 x 16  the spine (opaque): v from its tip (top row, white-hot) to its base (deep amber)
    spine_glow.png 32 x 32  the spine's glow shell (soft alpha): amber streaks, fading toward both ends
    spark.png      32 x 32  one ray of the deflect spark (soft alpha): base along the top row, tip at the bottom middle
    star.png       32 x 32  a dizzy star (soft alpha): a fat four-point star, pale yellow, with a soft halo
    dust.png       32 x 32  the rolling dust ring (soft alpha): u around (tiles), v from the inner edge (top row) out
  and previews/textures.png, every texture above enlarged on a checkerboard.

    python make_textures.py
"""
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw

HERE = Path(__file__).resolve().parent
OUT = HERE / "textures"
PREVIEW = HERE / "previews"
rng = np.random.default_rng(159)

PHI0 = 5.0                                            # a plate's arc runs PHI0..180-PHI0 degrees (build_models.py)
TEAL = (0.10, 0.40, 0.37)                             # the palette: dark teal, bronze, the plate's pale lip, ambers
BRONZE = (0.52, 0.40, 0.16)
LIP = (0.66, 0.62, 0.40)
DEEP_ORANGE = (0.55, 0.12, 0.02)
AMBER = (1.00, 0.52, 0.06)
GOLD = (1.00, 0.78, 0.28)
HOT = (1.00, 0.96, 0.78)
CHARCOAL = (0.11, 0.12, 0.12)


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


def plate(w, h, slits):
    """One plate's outside, w x h (see the docstring)."""
    u = (np.arange(w) + 0.5) / w
    v = (np.arange(h) + 0.5) / h
    uu, vv = np.meshgrid(u, v)
    phi = np.radians(PHI0 + (180 - 2 * PHI0) * uu)
    up = np.sin(phi)                                   # how far the outside faces up, standing
    # The light: from above and a little in front (the plate's front half leans forward, so lighter), a touch more
    # on the left than the right.
    light = 0.32 + 0.95 * up ** 1.6 * (1.0 - 0.18 * vv) + 0.06 * np.cos(phi)
    n = noise(w, h, 6, 2, wrap_x=False)
    col = mix(TEAL, BRONZE, 0.15 + 0.4 * n + 0.2 * up)
    # Faint grooves along the plate (across v), so the arc reads when it curls.
    col[np.abs(((uu * 6) % 1) - 0.5) < 0.07] *= 0.8
    col = col * light[..., None]
    # The pale bronze lip on both edges (standing, the arch shows each plate's front edge over the one in front;
    # curled, the ball shows the rear edges), brightest on top, a dark line inside each and a darker outer row.
    lip = (vv > 0.88) | (vv < 0.1)
    col[lip] = mix(LIP, (1.0, 0.95, 0.75), np.clip(up - 0.4, 0, 1))[lip] * (0.55 + 0.5 * light[lip, None])
    col[((vv > 0.84) | (vv < 0.14)) & ~lip] *= 0.45
    col[(vv > 0.96) | (vv < 0.03)] *= 0.75
    # A few pits.
    pits = (rng.random((h, w)) < 0.025) & (vv > 0.25) & (vv < 0.72)
    col[pits] *= 0.6
    for x in slits:                                    # a slit: a dark outline round an amber core, along v
        d = np.abs(uu - x) * w
        body = (vv > 0.3) & (vv < 0.68)
        col[body & (d < 2.0)] = (0.04, 0.03, 0.02)
        core = body & (d < 0.9) & (vv > 0.34) & (vv < 0.64)
        col[core] = mix(AMBER, HOT, 1 - np.abs(vv - 0.49) / 0.15)[core]
    return col


def shell():
    w, h = 64, 32
    col = np.concatenate([plate(w // 2, h, ()), plate(w // 2, h, (0.30, 0.5, 0.70))], axis=1)
    save("shell.png", np.dstack([col, np.ones((h, w))]))


def belly():
    """u around the body from its top (u = 0) down one side, under it (u = 0.5) and up the other."""
    w = h = 32
    u = (np.arange(w) + 0.5) / w
    v = (np.arange(h) + 0.5) / h
    uu, vv = np.meshgrid(u, v)
    under = 0.5 - 0.5 * np.cos(2 * np.pi * uu)        # 0 on top, 1 underneath
    n = noise(w, h, 5, 2)
    t = 0.15 + 0.6 * under + 0.25 * (n - 0.5)
    col = ramp(t, (DEEP_ORANGE, AMBER, GOLD, HOT))
    seg = np.abs(((vv * 7) % 1) - 0.5) > 0.36          # the segment lines across
    col[seg] = mix(col, DEEP_ORANGE, np.full((h, w), 0.75))[seg]
    col *= (0.55 + 0.45 * under)[..., None]
    save("belly.png", np.dstack([col, np.ones((h, w))]))


def glow():
    w = h = 16
    y, x = np.mgrid[0:h, 0:w]
    r = np.hypot(x + 0.5 - w / 2, y + 0.5 - h / 2) / (w / 2)
    col = ramp(1 - r, (DEEP_ORANGE, AMBER, GOLD, HOT, HOT))
    ring = np.abs(r - 0.62) < 0.08
    col[ring] = mix(col, AMBER, np.full((h, w), 0.6))[ring]
    save("glow.png", np.dstack([col, np.ones((h, w))]))


def parts():
    w, h = 32, 16
    shade = np.repeat([1.0, 0.75, 0.58, 0.4], 8)[None, :]
    legs = np.full((8, w, 3), CHARCOAL) * (0.9 + 0.25 * noise(w, 8, 4, 2))[..., None]
    legs = legs * (shade * 1.6)[..., None]
    legs[3] *= 0.55                                    # a joint band
    legs[:, ::8] = legs[:, ::8] * 0.7 + np.asarray(TEAL) * 0.3
    head = mix(TEAL, BRONZE, 0.3 + 0.5 * noise(w, 8, 4, 2)) * (shade * 1.25)[..., None]
    head[(rng.random((8, w)) < 0.06)] *= 0.6
    head[7] *= 0.6
    col = np.concatenate([legs, head], axis=0)
    save("parts.png", np.dstack([col, np.ones((h, w))]))


def spine():
    w = h = 16
    v = (np.arange(h) + 0.5) / h
    u = (np.arange(w) + 0.5) / w
    uu, vv = np.meshgrid(u, v)
    streak = 0.5 + 0.5 * np.cos(2 * np.pi * uu * 3)
    col = ramp(1 - vv * 0.9 + streak * 0.12, (DEEP_ORANGE, AMBER, GOLD, HOT))
    save("spine.png", np.dstack([col, np.ones((h, w))]))


def spine_glow():
    w = h = 32
    v = (np.arange(h) + 0.5) / h
    u = (np.arange(w) + 0.5) / w
    uu, vv = np.meshgrid(u, v)
    s = noise(w, 4, 4, 2)[np.zeros((h, w), int), np.arange(w)[None, :].repeat(h, 0)]
    ends = np.sin(np.pi * vv) ** 0.8                   # fades to nothing at both ends
    col = mix(AMBER, GOLD, s * 1.2)
    alpha = np.clip(ends * (0.35 + 0.45 * s), 0, 1)
    save("spine_glow.png", np.dstack([col, alpha]))


def spark():
    w = h = 32
    v = (np.arange(h) + 0.5) / h
    u = (np.arange(w) + 0.5) / w
    uu, vv = np.meshgrid(u, v)
    core = np.exp(-((uu - 0.5) / (0.06 + 0.16 * (1 - vv))) ** 2)
    col = ramp(np.clip((1 - vv) * 0.55 + core * 0.55, 0, 1), (AMBER, GOLD, HOT, (1, 1, 1)))
    alpha = np.clip((1 - vv) ** 1.1 * (0.25 + 0.75 * core) + (1 - vv) * 0.2, 0, 1) * core ** 0.3
    save("spark.png", np.dstack([col, alpha]))


def star():
    w = h = 32
    y, x = np.mgrid[0:h, 0:w]
    dx, dy = (x + 0.5 - w / 2) / (w / 2), (y + 0.5 - h / 2) / (h / 2)
    r = np.hypot(dx, dy)
    a = np.arctan2(dy, dx)
    edge = 0.42 + 0.48 * np.abs(np.cos(2 * a)) ** 3    # four points
    body = np.clip((edge - r) / 0.08, 0, 1)
    halo = np.clip(1 - r, 0, 1) ** 2 * 0.45
    col = mix(mix(GOLD, (1, 1, 0.85), np.clip(1 - r / 0.4, 0, 1)), (1, 1, 1), np.clip(1 - r / 0.15, 0, 1))
    col = mix(mix(AMBER, GOLD, 0.6), col, body)        # the halo amber, the star pale yellow
    save("star.png", np.dstack([col, np.maximum(body, halo)]))


def dust():
    w = h = 32
    v = (np.arange(h) + 0.5) / h
    u = (np.arange(w) + 0.5) / w
    uu, vv = np.meshgrid(u, v)
    n = noise(w, h, 5, 3)
    puffs = 0.5 + 0.5 * np.cos(2 * np.pi * uu * 3 + 3 * n)
    band = np.sin(np.pi * vv) ** 0.7                   # fades at the inner and outer edges
    col = mix((0.42, 0.36, 0.28), (0.78, 0.71, 0.60), 0.3 + 0.5 * n + 0.2 * (1 - vv))
    alpha = np.clip(band * (0.25 + 0.55 * puffs * n * 1.4), 0, 0.85)
    save("dust.png", np.dstack([col, alpha]))


NAMES = ["shell.png", "belly.png", "glow.png", "parts.png", "spine.png", "spine_glow.png", "spark.png", "star.png",
         "dust.png"]


def preview_sheet():
    """Every texture enlarged (nearest) on a checkerboard, with its name and size, in previews/textures.png."""
    tiles = []
    for nm in NAMES:
        im = Image.open(OUT / nm).convert("RGBA")
        k = max(1, min(256 // im.size[0], 160 // im.size[1]))
        big = im.resize((im.size[0] * k, im.size[1] * k), Image.NEAREST)
        tiles.append((nm, im.size, big))
    cols, cw, ch = 3, 280, 200
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


for f in (shell, belly, glow, parts, spine, spine_glow, spark, star, dust):
    f()
preview_sheet()
print("textures in", OUT)
