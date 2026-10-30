"""Draws the pack's enemy reskins (kinds) from nothing: every pixel comes from the code below, none from the game.

    python kinds.py            -> out/kinds/<kind>/<slot>.png at each slot's size (kind_slots)

Each base model's slots have a role (the head with its eye, the body shell, limbs, a strap, a band ...), learnt from
where the slot sits on the model; each kind paints those roles in its own colours and patterns.
"""
import math
import os
import random
import struct
import zlib

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "out", "kinds")

# slot -> (role, width, height) for each base, from kind_slots
BASES = {
    0x78: [("head", 32, 32), ("shell", 32, 32), ("limb", 16, 16), ("grad", 16, 16), ("tiny", 4, 4),
           ("headside", 32, 32), ("env", 32, 16), ("strap", 16, 32), ("torso", 32, 64), ("band", 32, 16)],
    0x8C: [("head", 32, 32), ("shell", 32, 32), ("limb", 16, 16), ("grad", 16, 16), ("headside", 32, 32),
           ("env", 32, 16), ("strap", 16, 32), ("band", 32, 16), ("scope", 8, 8), ("torso", 32, 64)],
    0xE1: [("head", 32, 32), ("env", 16, 16), ("body", 64, 32)],
    0xEE: [("teeth", 32, 16), ("speckle", 16, 16), ("ear", 16, 32), ("ribs", 16, 32), ("sheen", 32, 32),
           ("flash", 16, 16), ("shell", 32, 32), ("shell", 32, 32), ("head", 32, 32), ("swirl", 32, 32),
           ("plates", 32, 32), ("bands", 32, 32), ("nozzle", 64, 32)],
    0x54: [("panel", 16, 16), ("engine", 32, 16), ("panel2", 32, 16), ("bar", 32, 16), ("dark", 16, 16),
           ("emblem", 32, 64), ("scope", 8, 8)],
}


def png(path, w, h, px, channels=3):
    """An 8-bit RGB (or RGBA, channels 4) PNG of rows of pixels."""
    raw = b"".join(b"\x00" + bytes(px[y * w * channels:(y + 1) * w * channels]) for y in range(h))
    def chunk(t, d):
        return struct.pack(">I", len(d)) + t + d + struct.pack(">I", zlib.crc32(t + d) & 0xFFFFFFFF)
    data = b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", struct.pack(">IIBBBBB", w, h, 8, 6 if channels == 4 else 2, 0, 0, 0))
    data += chunk(b"IDAT", zlib.compress(raw, 9)) + chunk(b"IEND", b"")
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "wb") as f:
        f.write(data)


def clamp(c):
    return max(0, min(255, int(c)))


def shade(c, k):
    return tuple(clamp(v * k) for v in c)


def paint(w, h, fn):
    px = []
    for y in range(h):
        for x in range(w):
            px += [clamp(v) for v in fn(x, y, w, h)]
    return px


def rounded(x, y, w, h):
    """A soft cylinder shading across x (lit from the upper left), 0.6-1.15."""
    u = (x + 0.5) / w
    return 0.62 + 0.53 * math.sin(math.pi * u) ** 0.7 - 0.08 * (y / h)


def eye(x, y, w, h, rim, lens=(10, 10, 14)):
    """A domed eye-lens in the upper middle with two highlights; None outside it."""
    cx, cy, rx, ry = w * 0.5, h * 0.42, w * 0.36, h * 0.3
    d = ((x - cx) / rx) ** 2 + ((y - cy) / ry) ** 2
    if d <= 1.0 and y <= cy + ry * 0.55:
        if ((x - cx + rx * 0.35) ** 2 + (y - cy + ry * 0.35) ** 2) < (w * 0.07) ** 2:
            return (215, 220, 235)
        if ((x - cx + rx * 0.05) ** 2 + (y - cy + ry * 0.05) ** 2) < (w * 0.035) ** 2:
            return (160, 165, 185)
        return shade(lens, 1.0 + 0.6 * (1 - d))
    if 1.0 < d <= 1.35 and y <= cy + ry * 0.6:
        return rim
    return None


def speckle(seed):
    rnd = random.Random(seed)
    table = [rnd.random() for _ in range(4096)]
    return lambda x, y: table[(x * 73 + y * 151) % 4096]


# ------------------------------------------------------------------------------------------------ the kinds

def soldier(pal):
    """A painter for the soldier-type bases (0x78, 0x8C) from a palette dict."""
    sp = speckle(pal.get("seed", 1))

    def role(r):
        def fn(x, y, w, h):
            k = rounded(x, y, w, h)
            base = pal["coat"]
            if r in ("shell", "torso"):
                c = pal["pattern"](x, y, w, h)
                return shade(c, k * (0.92 + 0.1 * sp(x, y)))
            if r == "head":
                e = eye(x, y, w, h, pal["trim"])
                if e:
                    return e
                c = pal["hat"](x, y, w, h)
                return shade(c, k * (0.95 + 0.08 * sp(x, y)))
            if r == "headside":
                c = pal["hat"](x, y, w, h)
                return shade(c, k * (0.9 + 0.1 * sp(x, y)))
            if r == "limb":
                return shade(pal["limb"], k * (0.9 + 0.12 * sp(x, y)))
            if r == "grad":
                return shade(pal["limb"], 1.1 - 0.9 * y / h)
            if r == "tiny":
                return pal["trim"]
            if r == "env":  # what the eye reflects: our own sky over sand
                return (120 + 4 * y, 170 + 3 * y, 230) if y < h * 0.6 else (200, 180, 130)
            if r == "strap":
                return shade(pal["strap"], 0.7 + 0.5 * math.sin(math.pi * (x + 0.5) / w))
            if r == "band":
                c = pal["band"](x, y, w, h)
                return shade(c, 0.75 + 0.35 * math.sin(math.pi * (y + 0.5) / h))
            if r == "scope":
                return shade(pal["trim"], 1.2 if (x + y) % 3 else 0.7)
            return base
        return fn
    return role


def stripes(a, b, width=4):
    return lambda x, y, w, h: a if (y // width) % 2 == 0 else b


DECKHAND = {
    "seed": 3, "coat": (200, 40, 40), "trim": (235, 225, 210), "limb": (110, 25, 30), "strap": (95, 60, 35),
    "pattern": stripes((205, 35, 35), (238, 232, 220)),
    # a black bandana over the head, knotted at the side (a red dot pattern on it)
    "hat": lambda x, y, w, h: (20, 18, 22) if y < h * 0.62 or (x > w * 0.78 and y < h * 0.85)
    else (140, 30, 30),
    "band": lambda x, y, w, h: (210, 170, 60) if abs(x - w / 2) < 3 and abs(y - h / 2) < 4 else (25, 22, 20),
}
LOOKOUT = {
    "seed": 5, "coat": (25, 35, 80), "trim": (220, 180, 70), "limb": (18, 24, 55), "strap": (90, 60, 35),
    # a navy coat with two columns of gold buttons and a gold hem
    "pattern": lambda x, y, w, h: (225, 185, 70) if ((abs(x - w * 0.35) < 1.6 or abs(x - w * 0.65) < 1.6)
                                                    and y % 8 in (3, 4)) or y > h - 3 else (28, 38, 88),
    "hat": lambda x, y, w, h: (220, 180, 70) if abs(y - h * 0.18) < 1.5 else (22, 30, 72),
    "band": lambda x, y, w, h: (225, 185, 70) if y % 6 < 2 else (30, 40, 90),
}


def skitterer(role):
    sp = speckle(9)

    def fn(x, y, w, h):
        sand = (226, 196, 138)
        s = sp(x, y)
        c = shade(sand, 0.85 + 0.25 * s)
        if s > 0.82:
            c = (150, 115, 70)  # dark grains
        elif s < 0.06:
            c = (250, 240, 215)  # bright grains
        if role == "head":
            e = eye(x, y, w, h, (120, 90, 50), lens=(20, 14, 8))
            return e or shade(c, rounded(x, y, w, h))
        if role == "env":
            return (240, 225, 180) if y < h / 2 else (170, 140, 90)
        return shade(c, 0.75 + 0.35 * math.sin(math.pi * (y + 0.5) / h))
    return fn


def gull(role):
    sp = speckle(11)

    def fn(x, y, w, h):
        white, grey, orange = (236, 236, 232), (130, 135, 140), (240, 140, 40)
        if role in ("panel", "panel2"):
            seam = x % 8 == 0 or y % 8 == 0
            c = grey if seam else (white if (x // 8 + y // 8) % 3 else (205, 208, 210))
            return shade(c, 0.9 + 0.12 * sp(x, y))
        if role == "engine":
            d = abs(y - h / 2) / (h / 2)
            return shade(orange, 1.25 - 0.6 * d)
        if role == "bar":
            inner = 3 <= y < h - 3 and 3 <= x < w - 3
            return shade(orange, 1.1) if inner else (60, 62, 66)
        if role == "dark":
            return shade((70, 74, 80), 0.9 + 0.2 * sp(x, y))
        if role == "emblem":  # a wing shape in grey on white
            u, v = x / w, y / h
            wing = abs(v - 0.5 - 0.25 * math.sin(u * math.pi * 2)) < 0.08
            return grey if wing else shade(white, 0.85 + 0.15 * u)
        if role == "scope":
            return orange if (x + y) % 2 else (255, 200, 120)
        return white
    return fn


def sand_beetle(role):
    """A scuttling beetle the colour of the beach: sand-speckled shell, darker joints."""
    sp = speckle(13)
    sand, dark, pale = (222, 192, 132), (120, 88, 52), (246, 232, 196)

    def fn(x, y, w, h):
        s = sp(x, y)
        grain = (150, 115, 70) if s > 0.84 else (pale if s < 0.07 else shade(sand, 0.86 + 0.22 * s))
        if role == "head":
            e = eye(x, y, w, h, dark, lens=(24, 16, 10))
            return e or shade(grain, rounded(x, y, w, h))
        if role in ("shell", "speckle"):
            seg = 0.8 + 0.25 * math.sin(math.pi * ((y * 3 / h) % 1.0))
            return shade(grain, seg * rounded(x, y, w, h))
        if role == "teeth":
            return pale if (x // 3) % 2 == 0 and y > h * 0.35 else dark
        if role == "ribs":
            return shade(dark, 0.8 + 0.4 * ((y // 3) % 2))
        if role == "sheen":
            t = (math.sin(x / w * 6 + y / h * 3) + 1) / 2
            return tuple(sand[i] + (pale[i] - sand[i]) * t for i in range(3))
        if role == "flash":
            return (255, 220, 120) if (x + y) % 4 < 2 else (240, 140, 40)
        if role == "swirl":
            d = math.hypot(x - w / 2, y - h / 2) / (w / 2)
            return shade(sand, 0.6 + 0.6 * abs(math.sin(d * 7 + math.atan2(y - h / 2, x - w / 2))))
        if role == "plates":
            return shade(pale, 0.75 if y % 11 in (0, 1) or x % 16 == 0 else 1.0)
        if role == "bands":
            return sand if (y // 5) % 2 == 0 else dark
        if role == "ear":
            return eye(x, y, w, h, dark, lens=(30, 20, 12)) or grain
        if role == "nozzle":
            hole = any(math.hypot(x - cx, y - h / 2) < 4 for cx in (w * 0.3, w * 0.55, w * 0.8))
            return (20, 14, 10) if hole else shade(dark, 0.8 + 0.3 * s)
        return grain
    return fn


MASKED = {(0xEE, 1)}  # slots whose base image has a cut-out: ours gets one too (a rounded blob)

KINDS = {
    "deckhand": (0x78, lambda r: soldier(DECKHAND)(r)),
    "lookout": (0x8C, lambda r: soldier(LOOKOUT)(r)),
    "skitterer": (0xEE, sand_beetle),  # 0xE1 hung in the air in the hold (owner's play-test): a ground beetle
    "gull_raider": (0x54, gull),
}


def main():
    for name, (base, painter) in KINDS.items():
        for slot, (role, w, h) in enumerate(BASES[base]):
            px = paint(w, h, painter(role))
            if (base, slot) in MASKED:
                rgba = []
                for i in range(w * h):
                    x, y = i % w, i // w
                    inside = ((x + 0.5 - w / 2) / (w / 2)) ** 2 + ((y + 0.5 - h / 2) / (h / 2)) ** 2 <= 0.95
                    rgba += px[i * 3:i * 3 + 3] + [255 if inside else 0]
                png(os.path.join(OUT, name, f"{slot}.png"), w, h, rgba, channels=4)
            else:
                png(os.path.join(OUT, name, f"{slot}.png"), w, h, px)
        print(name, len(BASES[base]), "slots")


if __name__ == "__main__":
    main()
