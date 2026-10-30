"""Draws the pack's picture (thumb.png, 256 x 256) from nothing: the three worlds of Corsair Reach on a starfield,
under the corsairs' pennant.    python thumb.py
"""
import math
import os
import random

from kinds import png

HERE = os.path.dirname(os.path.abspath(__file__))
W = H = 256
SS = 3  # supersampling for smooth edges


def mix(a, b, t):
    return tuple(a[i] + (b[i] - a[i]) * t for i in range(3))


def sky(x, y):
    t = y / H
    return mix((14, 18, 46), (60, 30, 70), t ** 1.4)


rnd = random.Random(4)
STARS = [(rnd.uniform(0, W), rnd.uniform(0, H), rnd.uniform(0.3, 1.0)) for _ in range(90)]
PLANETS = [  # (x, y, radius, painter)
    (62, 168, 40, "cay"), (138, 128, 34, "mire"), (206, 176, 44, "cinder")]


def planet(kind, u, v, d):
    """Colour on a planet at (u, v) in -1..1 across its disc, d its distance from the centre (0-1)."""
    light = max(0.0, 0.25 + 0.75 * (-u * 0.6 - v * 0.55 + math.sqrt(max(0.0, 1 - d * d)) * 0.6))
    if kind == "cay":  # turquoise sea, sandy islands with green crowns
        land = math.sin(u * 5.1 + 1.3) * math.cos(v * 4.3) + 0.4 * math.sin(u * 11 + v * 7)
        c = (225, 205, 140) if land > 0.55 else ((70, 150, 80) if land > 0.45 else (40, 190, 200))
    elif kind == "mire":  # slate blue with storm bands and rain streaks
        band = math.sin(v * 9 + u * 1.5)
        c = (90, 110, 140) if band > 0.3 else (60, 75, 105)
        if (int((u + v * 0.5) * 40) % 7) == 0:
            c = (150, 170, 200)
    else:  # red-black rock with glowing cracks
        crack = abs(math.sin(u * 7.3 + math.sin(v * 5.1) * 2) * math.cos(v * 6.7 - u * 2))
        c = (240, 110, 30) if crack < 0.08 else (55, 25, 22)
        if crack < 0.08:
            return c  # the cracks glow, unlit
    return tuple(ch * (0.25 + 0.95 * light) for ch in c)


def flag(x, y):
    """The corsairs' pennant in the top left: black, a bone-white skull over crossed oars."""
    fx, fy = x - 18, y - 16
    if not (0 <= fx <= 92 and 0 <= fy <= 58 - fx * 0.25):
        if 12 <= x <= 16 and 10 <= y <= 120:
            return (120, 85, 50)  # the pole
        return None
    sx, sy = fx - 34, fy - 22
    skull = (sx / 13) ** 2 + (sy / 11) ** 2 <= 1 or (abs(sx) < 7 and 8 <= sy <= 15)
    eye = (sx + 5) ** 2 + (sy - 1) ** 2 < 9 or (sx - 5) ** 2 + (sy - 1) ** 2 < 9
    oar = any(abs(sy - 28 - k * sx) < 2 for k in (0.45, -0.45)) and abs(sx) < 30 and fy < 50
    if (skull and not eye) or oar:
        return (235, 228, 210)
    return (12, 12, 16)


def pixel(x, y):
    for px, py, r, kind in PLANETS:
        d = math.hypot(x - px, y - py) / r
        if d <= 1:
            return planet(kind, (x - px) / r, (y - py) / r, d)
        if d <= 1.12:  # a thin glow of atmosphere
            glow = {"cay": (90, 220, 230), "mire": (120, 140, 190), "cinder": (240, 90, 40)}[kind]
            return mix(sky(x, y), glow, (1.12 - d) / 0.12 * 0.8)
    f = flag(x, y)
    if f:
        return f
    c = sky(x, y)
    for sx, sy, b in STARS:
        if abs(x - sx) < 0.7 and abs(y - sy) < 0.7:
            return mix(c, (255, 250, 230), b)
    return c


def main():
    px = []
    for y in range(H):
        for x in range(W):
            acc = [0.0, 0.0, 0.0]
            for j in range(SS):
                for i in range(SS):
                    c = pixel(x + (i + 0.5) / SS, y + (j + 0.5) / SS)
                    acc = [acc[k] + c[k] for k in range(3)]
            px += [max(0, min(255, int(a / (SS * SS)))) for a in acc]
    out = os.path.join(os.path.dirname(HERE), "thumb.png")
    png(out, W, H, px)
    print(out)


if __name__ == "__main__":
    main()
