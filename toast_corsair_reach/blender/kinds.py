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
    # the shielded soldier: the blue one's slots, plus the shield's emblem strip and its face
    0x99: [("head", 32, 32), ("shell", 32, 32), ("limb", 16, 16), ("grad", 16, 16), ("tiny", 4, 4),
           ("headside", 32, 32), ("emblem", 32, 16), ("env", 32, 16), ("strap", 16, 32), ("torso", 32, 64),
           ("band", 32, 16), ("shieldface", 32, 32)],
    # the captain: head, shell, a masked limb, its belt panel ("armour") and an 8 x 8 the model leaves untextured
    0x12F: [("head", 32, 32), ("shell", 32, 32), ("limb", 16, 16), ("tiny", 4, 4), ("headside", 32, 32),
            ("band", 32, 16), ("env", 32, 16), ("armour", 32, 32), ("scope", 8, 8)],
    # the big-shield soldier: the shielded one's slots, plus its shield's see-through face (64 x 40) and a glow
    0x9C: [("head", 32, 32), ("shell", 32, 32), ("limb", 16, 16), ("grad", 16, 16), ("tiny", 4, 4),
           ("headside", 32, 32), ("emblem", 32, 16), ("env", 32, 16), ("strap", 16, 32), ("torso", 32, 64),
           ("band", 32, 16), ("shieldface", 32, 32), ("shieldglow", 64, 40), ("glow", 32, 32)],
    # the undead ant: three wide body sheets, a head, two shell pieces, two masked limbs and a tiny one (roles by
    # size: the model's own images were not looked at)
    0x121: [("body", 64, 32), ("head", 32, 32), ("limb", 16, 16), ("body", 64, 32), ("shell", 32, 32),
            ("shell", 32, 32), ("tiny", 8, 8), ("body", 64, 32), ("limb", 32, 32)],
    # the striped flyer: a long body sheet, a tiny one, a shell, two wing strips and a panel (roles by size)
    0x2D: [("body", 32, 64), ("tiny", 8, 8), ("shell", 32, 32), ("wing", 32, 16), ("panel", 16, 16),
           ("wing", 32, 16)],
    # the big bug: bands, shells, a head, a thin strip, a wide body sheet, a masked limb and a leg (roles by size)
    0x122: [("band", 32, 16), ("band", 32, 16), ("shell", 32, 32), ("shell", 32, 32), ("tiny", 8, 8),
            ("head", 32, 32), ("strip", 32, 4), ("shell", 32, 32), ("body", 64, 32), ("shell", 32, 32),
            ("limb", 16, 16), ("shell", 32, 32), ("leg", 16, 32)],
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
            if r in ("emblem", "shieldface", "armour", "shieldglow", "glow"):
                return pal[r](x, y, w, h)
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


def rope(x, y, w, h, light=(196, 160, 98), dark=(120, 88, 48)):
    """Twisted rope across a band: diagonal strands."""
    return light if ((x + y) // 2) % 3 else dark


def canvas(x, y, w, h):
    """Tan sailcloth: a fine weave, a darker seam every 16 rows."""
    weave = 1.0 + 0.06 * (((x + y) % 2) * 2 - 1)
    c = (192, 162, 112) if (y // 16) % 2 == 0 else (180, 150, 102)
    if y % 16 == 15:
        c = (130, 104, 70)
    return shade(c, weave)


BOARDER = {
    "seed": 7, "coat": (186, 156, 108), "trim": (120, 88, 48), "limb": (150, 122, 80), "strap": (140, 104, 58),
    # canvas with two rope bands round the body
    "pattern": lambda x, y, w, h: rope(x, y, w, h) if (h * 0.3 <= y < h * 0.3 + 4) or (h * 0.62 <= y < h * 0.62 + 4)
    else canvas(x, y, w, h),
    "hat": lambda x, y, w, h: rope(x, y, w, h) if abs(y - h * 0.2) < 2 else canvas(x, y, w, h),
    "band": rope,
    # the shield: planks lashed with rope, and its face of stretched canvas laced at the edges with our mark
    "emblem": lambda x, y, w, h: rope(x, y, w, h) if abs(x - y * 2) < 3 or abs((w - x) - y * 2) < 3
    else ((112, 80, 50) if (x // 8) % 2 else (128, 92, 58)),
    "shieldface": lambda x, y, w, h: (rope(x, y, w, h) if (x < 3 or x > w - 4 or y < 3 or y > h - 4)
                                      else (150, 40, 30) if (abs(x - y) < 2 or abs(x + y - (w - 1)) < 2)
                                      and 6 < x < w - 7 else canvas(x, y, w, h)),
}
GOLD = (222, 176, 64)
FIRST_MATE = {
    "seed": 9, "coat": (168, 26, 26), "trim": GOLD, "limb": (140, 20, 22), "strap": (60, 30, 20),
    # a long red coat with gold piping down its front and round its hem
    "pattern": lambda x, y, w, h: GOLD if abs(x - w / 2) < 1.5 or y > h - 3 or (y % 10 == 4 and abs(x - w / 2) < 5)
    else (170, 28, 26),
    "hat": lambda x, y, w, h: GOLD if abs(y - h * 0.22) < 1.5 else (24, 18, 20),  # a black hat with a gold band
    "band": lambda x, y, w, h: GOLD if y % 5 in (1, 2) else (110, 20, 18),
    # the coat's skirts: red, a column of gold buttons, a gold hem
    "armour": lambda x, y, w, h: GOLD if y > h - 4 or ((x in (12, 13, 18, 19)) and y % 8 in (2, 3))
    else (150, 22, 22) if (x // 4) % 4 else (128, 18, 18),
}


def cave_crab(role):
    """A crab-backed beetle from the grotto's pools: coral orange shell, pale barnacle spots, dark joints."""
    sp = speckle(17)
    coral, dark, pale = (232, 104, 64), (110, 40, 28), (238, 226, 205)
    rnd = random.Random(21)
    spots = [(rnd.random(), rnd.random(), 0.06 + 0.07 * rnd.random()) for _ in range(9)]

    def barnacle(x, y, w, h):
        for (u, v, r) in spots:
            d = math.hypot((x + 0.5) / w - u, (y + 0.5) / h - v)
            if d < r:
                return shade(pale, 0.75 + 0.35 * (1 - d / r)) if d > r * 0.35 else (90, 80, 70)
        return None

    def fn(x, y, w, h):
        s = sp(x, y)
        base = shade(coral, 0.84 + 0.24 * s)
        if role == "head":
            e = eye(x, y, w, h, dark, lens=(20, 12, 10))
            return e or shade(base, rounded(x, y, w, h))
        if role in ("shell", "speckle", "plates"):
            b = barnacle(x, y, w, h)
            seg = 0.82 + 0.22 * math.sin(math.pi * ((y * 3 / h) % 1.0))
            return b or shade(base, seg * rounded(x, y, w, h))
        if role == "teeth":
            return pale if (x // 3) % 2 == 0 and y > h * 0.35 else dark
        if role == "ribs":
            return shade(dark, 0.8 + 0.4 * ((y // 3) % 2))
        if role == "sheen":
            t = (math.sin(x / w * 6 + y / h * 3) + 1) / 2
            return tuple(coral[i] + (pale[i] - coral[i]) * t * 0.5 for i in range(3))
        if role == "flash":
            return (255, 200, 140) if (x + y) % 4 < 2 else (230, 90, 50)
        if role == "swirl":
            d = math.hypot(x - w / 2, y - h / 2) / (w / 2)
            return shade(coral, 0.6 + 0.5 * abs(math.sin(d * 7 + math.atan2(y - h / 2, x - w / 2))))
        if role == "bands":
            return coral if (y // 5) % 2 == 0 else dark
        if role == "ear":
            return eye(x, y, w, h, dark, lens=(30, 14, 10)) or base
        if role == "nozzle":
            hole = any(math.hypot(x - cx, y - h / 2) < 4 for cx in (w * 0.3, w * 0.55, w * 0.8))
            return (20, 10, 8) if hole else shade(dark, 0.8 + 0.3 * s)
        return base
    return fn


BLACK = (26, 24, 28)
VAULT_GUARD = {
    "seed": 11, "coat": BLACK, "trim": GOLD, "limb": (34, 30, 34), "strap": (150, 115, 40),
    # black armour with gold bands across the chest and a gold collar
    "pattern": lambda x, y, w, h: GOLD if y % 16 in (5, 6) or y < 3 else (30, 28, 32) if (x // 6) % 2 else BLACK,
    "hat": lambda x, y, w, h: GOLD if abs(y - h * 0.2) < 1.5 or abs(x - w / 2) < 1 else (22, 20, 24),
    "band": lambda x, y, w, h: GOLD if y % 5 in (1, 2) else BLACK,
    "emblem": lambda x, y, w, h: GOLD if (x + y) % 8 < 2 else (40, 34, 30),
    # the shield: black plate, a gold rim and a gold coin in the middle
    "shieldface": lambda x, y, w, h: (GOLD if (x < 3 or x > w - 4 or y < 3 or y > h - 4)
                                      or math.hypot(x - w / 2 + 0.5, y - h / 2 + 0.5) < w * 0.22
                                      else (36, 32, 36) if (x // 4 + y // 4) % 2 else BLACK),
    # its see-through face (alpha added in main) and glow: a dim gold sheen
    "shieldglow": lambda x, y, w, h: shade(GOLD, 0.45 + 0.35 * math.sin(math.pi * (x + 0.5) / w)),
    "glow": lambda x, y, w, h: shade(GOLD, 0.4 + 0.6 * max(0.0, 1 - math.hypot(x - w / 2, y - h / 2) / (w / 2))),
}

def drowned_crew(role):
    """A crewman the sea took back: seaweed green-grey, dark weed strands hanging down, pale barnacle spots, a dull
    sea-green eye."""
    sp = speckle(23)
    grey, weed, dark, pale = (104, 122, 100), (56, 92, 52), (34, 46, 34), (196, 200, 176)
    rnd = random.Random(29)
    spots = [(rnd.random(), rnd.random(), 0.05 + 0.06 * rnd.random()) for _ in range(7)]
    strands = [(rnd.random(), 0.3 + 0.6 * rnd.random()) for _ in range(6)]

    def barnacle(x, y, w, h):
        for (u, v, r) in spots:
            d = math.hypot((x + 0.5) / w - u, (y + 0.5) / h - v)
            if d < r:
                return shade(pale, 0.7 + 0.35 * (1 - d / r)) if d > r * 0.3 else (70, 74, 62)
        return None

    def strand(x, y, w, h):
        for (u, length) in strands:
            wob = u + 0.03 * math.sin(y / h * 9 + u * 20)
            if abs((x + 0.5) / w - wob) < 0.035 and (y + 0.5) / h < length:
                return shade(weed, 0.75 + 0.3 * sp(x, y))
        return None

    def fn(x, y, w, h):
        s = sp(x, y)
        base = shade(grey, 0.78 + 0.3 * s)
        if (x * 5 + y * 3) % 11 == 0:
            base = shade(weed, 0.9 + 0.2 * s)
        if role == "head":
            e = eye(x, y, w, h, dark, lens=(30, 70, 55))
            return e or strand(x, y, w, h) or shade(base, rounded(x, y, w, h))
        if role in ("body", "shell"):
            return strand(x, y, w, h) or barnacle(x, y, w, h) or shade(base, rounded(x, y, w, h))
        if role == "limb":
            return shade(base, 0.7 + 0.25 * ((y // 4) % 2)) if (x + y) % 9 else shade(dark, 1.0)
        return shade(dark, 0.9 + 0.3 * s)
    return fn


# ------------------------------------------------------------------------------------------------ world 2: Mirefall

SLICKER = {
    "seed": 31, "coat": (222, 182, 38), "trim": (40, 36, 30), "limb": (160, 128, 30), "strap": (38, 32, 28),
    # yellow oilskins, shiny where the rain runs, two dark straps crossing the chest
    "pattern": lambda x, y, w, h: (36, 30, 26) if abs(x - (w * 0.3 + y * 0.25)) < 2 or abs(x - (w * 0.7 - y * 0.25)) < 2
    else ((245, 214, 90) if (x + y * 2) % 13 == 0 else (222, 182, 38)),
    # a sou'wester: a yellow brim and crown, a dark band
    "hat": lambda x, y, w, h: (40, 36, 30) if abs(y - h * 0.3) < 1.5 else (215, 175, 40),
    "band": lambda x, y, w, h: (222, 182, 38) if y % 6 < 2 else (38, 32, 28),
}
BELL_LOOKOUT = {
    "seed": 37, "coat": (108, 110, 116), "trim": (58, 60, 68), "limb": (78, 80, 88), "strap": (52, 46, 40),
    # a grey hooded cloak, darker folds running down it
    "pattern": lambda x, y, w, h: (84, 86, 94) if (x + 3) % 9 < 2 else (112, 114, 120),
    "hat": lambda x, y, w, h: (70, 72, 80) if y > h * 0.7 else (100, 102, 110),  # the hood, shadowed at its rim
    "band": lambda x, y, w, h: (58, 60, 68) if y % 5 in (1, 2) else (100, 102, 110),
}

STEEL, STEEL_D, RIVET = (78, 86, 96), (46, 52, 60), (150, 160, 170)
TOWER_WARDEN = {
    "seed": 67, "coat": STEEL, "trim": (120, 130, 142), "limb": (58, 64, 74), "strap": (40, 36, 34),
    # rain-dark steel plates, rivet rows, wet streaks running down
    "pattern": lambda x, y, w, h: RIVET if y % 12 == 3 and x % 4 == 1
    else STEEL_D if y % 12 == 0 or (x * 7 + y) % 23 == 0 else (STEEL if (x // 8) % 2 else (70, 78, 88)),
    "hat": lambda x, y, w, h: RIVET if abs(y - h * 0.25) < 1.2 and x % 3 == 0 else (64, 72, 82),  # a steel helm
    "band": lambda x, y, w, h: STEEL_D if y % 5 in (1, 2) else (92, 100, 110),
    # the shield: iron plates riveted at the edges, a bell in pale steel on its face (the market's guard)
    "emblem": lambda x, y, w, h: RIVET if x % 6 == 2 and y in (2, h - 3) else STEEL_D if (x // 8) % 2 else STEEL,
    "shieldface": lambda x, y, w, h: (RIVET if (x < 3 or x > w - 4 or y < 3 or y > h - 4) and (x + y) % 4 == 0
                                      else STEEL_D if (x < 3 or x > w - 4 or y < 3 or y > h - 4)
                                      else (176, 184, 192) if (8 <= y <= 22 and abs(x - w / 2 + 0.5) <= (y - 6) * 0.45)
                                      or (23 <= y <= 25 and 7 <= x <= w - 8) else (60, 68, 78)),
}


def storm_midge(role):
    """A biting flyer of the storm: slate grey, electric-blue stripes, pale glowing wing edges."""
    sp = speckle(43)
    slate, blue, dark = (72, 80, 94), (70, 175, 255), (34, 38, 48)

    def fn(x, y, w, h):
        s = sp(x, y)
        if role in ("body", "shell"):
            if (y // 5) % 3 == 0:
                return shade(blue, 0.85 + 0.3 * s)
            return shade(slate, rounded(x, y, w, h) * (0.9 + 0.15 * s))
        if role == "wing":
            edge = y < 2 or y > h - 3
            return shade(blue, 1.1) if edge else shade(slate, 0.75 + 0.35 * (x / w))
        if role == "panel":
            return shade(blue, 1.2) if (x + y) % 5 == 0 else shade(dark, 0.9 + 0.2 * s)
        return blue
    return fn


def marsh_leech(role):
    """A swollen bug of the bog: slimy green-brown, dark spots, wet highlights."""
    sp = speckle(47)
    green, brown, dark = (78, 92, 46), (96, 74, 42), (36, 34, 22)
    rnd = random.Random(53)
    spots = [(rnd.random(), rnd.random(), 0.06 + 0.07 * rnd.random()) for _ in range(9)]

    def fn(x, y, w, h):
        s = sp(x, y)
        u, v = (x + 0.5) / w, (y + 0.5) / h
        base = green if math.sin(u * 7 + v * 5 + s) > 0 else brown
        for (a, b, r) in spots:
            if math.hypot(u - a, v - b) < r:
                return shade(dark, 0.8 + 0.3 * s)
        if (x * 3 + y * 7) % 17 == 0:
            return (170, 190, 120)  # a wet glint
        if role in ("shell", "body", "head", "band"):
            return shade(base, rounded(x, y, w, h) * (0.85 + 0.2 * s))
        if role in ("limb", "leg"):
            return shade(brown, 0.6 + 0.3 * ((y // 3) % 2))
        return shade(dark, 1.0 + 0.3 * s)
    return fn


def bog_walker(role):
    """One of the drowned of the marsh: peat brown, green moss in patches, root-dark streaks, a pale dead eye."""
    sp = speckle(59)
    peat, moss, dark, pale = (84, 60, 40), (70, 102, 48), (36, 26, 18), (176, 182, 160)
    rnd = random.Random(61)
    patches = [(rnd.random(), rnd.random(), 0.1 + 0.12 * rnd.random()) for _ in range(6)]

    def fn(x, y, w, h):
        s = sp(x, y)
        u, v = (x + 0.5) / w, (y + 0.5) / h
        base = shade(peat, 0.8 + 0.3 * s)
        for (a, b, r) in patches:
            if math.hypot(u - a, (v - b) * 0.8) < r * (0.8 + 0.4 * s):
                base = shade(moss, 0.8 + 0.3 * s)
        if (x * 5 + y) % 13 == 0:
            base = shade(dark, 1.0)
        if role == "head":
            e = eye(x, y, w, h, dark, lens=(120, 126, 108))
            return e or shade(base, rounded(x, y, w, h))
        if role in ("body", "shell"):
            return shade(base, rounded(x, y, w, h))
        if role == "limb":
            return shade(base, 0.7 + 0.25 * ((y // 4) % 2))
        return shade(pale if role == "tiny" else dark, 0.9 + 0.2 * s)
    return fn


MASKED = {(0xEE, 1), (0x12F, 2), (0x121, 2), (0x121, 8), (0x122, 10)}  # slots whose base image has a cut-out: ours gets one too (a rounded blob)
BLEND = {(0x9C, 12): 150, (0x9C, 13): 120}  # slots whose base image is see-through: ours too, at this alpha

KINDS = {
    "deckhand": (0x78, lambda r: soldier(DECKHAND)(r)),
    "lookout": (0x8C, lambda r: soldier(LOOKOUT)(r)),
    "skitterer": (0xEE, sand_beetle),  # 0xE1 hung in the air in the hold (owner's play-test): a ground beetle
    "gull_raider": (0x54, gull),
    "boarder": (0x99, lambda r: soldier(BOARDER)(r)),
    "first_mate": (0x12F, lambda r: soldier(FIRST_MATE)(r)),
    "cave_crab": (0xEE, cave_crab),
    "vault_guard": (0x9C, lambda r: soldier(VAULT_GUARD)(r)),
    "drowned_crew": (0x121, drowned_crew),
    "slicker": (0x78, lambda r: soldier(SLICKER)(r)),
    "bell_lookout": (0x8C, lambda r: soldier(BELL_LOOKOUT)(r)),
    "storm_midge": (0x2D, storm_midge),
    "marsh_leech": (0x122, marsh_leech),
    "bog_walker": (0x121, bog_walker),
    "tower_warden": (0x99, lambda r: soldier(TOWER_WARDEN)(r)),
}


def main():
    for name, (base, painter) in KINDS.items():
        for slot, (role, w, h) in enumerate(BASES[base]):
            px = paint(w, h, painter(role))
            if (base, slot) in BLEND:
                rgba = []
                for i in range(w * h):
                    rgba += px[i * 3:i * 3 + 3] + [BLEND[(base, slot)]]
                png(os.path.join(OUT, name, f"{slot}.png"), w, h, rgba, channels=4)
            elif (base, slot) in MASKED:
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
