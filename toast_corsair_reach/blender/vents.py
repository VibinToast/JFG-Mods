"""Coolant Vents (Corsair Reach 3.4, Cinderhold's optional side level): builds the level from nothing and exports
blender/out/vents.glb.

    blender --background --factory-startup --addons jfg64 --python vents.py
Then in JFG-Studio: import the .glb (first time) or reimport_geometry into the level `vents`.

Game coordinates throughout (x east, z south, y up). The one cool place in the volcano: a cluster of round vent
chambers under the Bellows, joined by short pipes 200 wide, all under a roof (no sky):
  A       the vent hatch (500): the way back to the Bellows' side door; start point 0
  K1-K6   six chambers on a ring of 600 round the manifold: K1 (south) from the hatch, K4 (north) on to the pump hall
  M       the manifold in the middle, where the two cross-links meet (K2-M-K5 and K3-M-K6)
  D1, D2  dead ends out from K3 (west-north-west) and K6 (east-south-east): ash walkers and a Tribal each
  H       the pump hall (840 x 560 at 370) north of K4: two rows of pumps and vent stacks as cover, the coolant
          channel along its north wall with the health upgrade's alcove behind it, the rockets chest's alcove (west),
          two Tribals' alcoves (south, east)
  L       the service lift off the hall's east wall (the way on to the Crown); start point 1
Each chamber: a polygon round its centre (mouths cut as chords exactly 200 wide where its pipes meet it), a floor of
grid cells clipped to it (cover blocks cut out of it), walls (a pipe band low, panels above), a dome up to a grille
over the middle where the coolant light comes down.
"""
import json
import math
import os
import sys

import bpy

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import common as C  # noqa: E402
from common import Mesh  # noqa: E402
import jfg64  # noqa: E402

NAME = "vents"
scene, coll = C.new_scene(NAME)
spots = {}


# ------------------------------------------------------------------------------------------------ own images
def hn(x, y, s=0):
    h = (x * 374761393 + y * 668265263 + s * 2147483647) & 0xFFFFFFFF
    h = ((h ^ (h >> 13)) * 1274126177) & 0xFFFFFFFF
    return ((h ^ (h >> 16)) & 0xFFFF) / 65535.0


def sc(c, k):
    return tuple(max(0.0, min(1.0, v * k)) for v in c)


def gauge_px(x, y):
    """A pressure gauge on a plate: brass rim, a pale face, ticks, a red zone and the needle in it."""
    n = hn(x, y, 1)
    u, v = (x + 0.5) / 32 - 0.5, (y + 0.5) / 32 - 0.5
    r = math.hypot(u, v)
    if r > 0.46:
        return sc((0.32, 0.36, 0.42), 0.85 + 0.2 * n)
    if r > 0.40:
        return sc((0.62, 0.5, 0.24), 0.85 + 0.25 * n)
    if r < 0.05:
        return (0.08, 0.08, 0.09)
    a = math.degrees(math.atan2(v, u)) % 360.0
    t = ((a - 135.0) % 360.0) / 270.0
    if 0.33 < r < 0.38 and 0.78 < t < 1.0:
        return (0.8, 0.15, 0.1)
    if 0.29 < r < 0.38 and t < 1.0 and (t * 270.0) % 30.0 < 5.0:
        return (0.1, 0.1, 0.12)
    na = math.radians(135.0 + 0.86 * 270.0)
    ex, ey = 0.32 * math.cos(na), 0.32 * math.sin(na)
    k = max(0.0, min(1.0, (u * ex + v * ey) / (ex * ex + ey * ey)))
    if math.hypot(u - k * ex, v - k * ey) < 0.03:
        return (0.55, 0.06, 0.05)
    return sc((0.92, 0.9, 0.82), 0.92 + 0.08 * n)


def valve_px(x, y):
    """A red hand wheel on dark iron."""
    n = hn(x, y, 2)
    u, v = (x + 0.5) / 32 - 0.5, (y + 0.5) / 32 - 0.5
    r = math.hypot(u, v)
    red = sc((0.74, 0.14, 0.1), 0.8 + 0.3 * (0.5 - v) + 0.1 * n)
    if 0.30 < r < 0.40:
        return red
    if r < 0.31 and (abs(u) < 0.035 or abs(v) < 0.035):
        return red
    if r < 0.09:
        return (0.5, 0.1, 0.08)
    return sc((0.22, 0.24, 0.27), 0.8 + 0.3 * n)


def hazard_px(x, y):
    """Yellow and black hazard stripes."""
    n = hn(x, y, 3)
    if ((x + y) // 4) % 2:
        return sc((0.92, 0.74, 0.12), 0.85 + 0.2 * n)
    return sc((0.09, 0.09, 0.1), 0.8 + 0.4 * n)


def grille_px(x, y):
    """A vent grille with the coolant light behind its bars."""
    n = hn(x, y, 4)
    if x in (0, 15) or y in (0, 15):
        return sc((0.25, 0.27, 0.3), 0.9 + 0.2 * n)
    if x % 3 == 0:
        return sc((0.07, 0.08, 0.1), 0.9 + 0.2 * n)
    return sc((0.55, 0.72, 0.82), 0.82 + 0.25 * n)


def hatch_px(x, y):
    """The vent hatch: a riveted iron door with a red hand wheel and a hazard band at its foot."""
    n = hn(x, y, 5)
    if x < 2 or x > 29 or y < 2:
        return sc((0.12, 0.13, 0.15), 0.9 + 0.2 * n)
    if y > 53:
        return hazard_px(x, y)
    if (x in (4, 27)) and y % 8 == 4:
        return (0.55, 0.6, 0.66)
    r = math.hypot(x + 0.5 - 16, y + 0.5 - 26)
    if 6 < r < 8.5 or (r < 7 and (abs(x + 0.5 - 16) < 1.1 or abs(y + 0.5 - 26) < 1.1)):
        return sc((0.74, 0.14, 0.1), 0.85 + 0.2 * n)
    return sc((0.3, 0.34, 0.4), 0.85 + 0.2 * n)


def glow_px(x, y):
    """A glass coolant tube, pale blue and bright in its middle, metal caps at its ends."""
    n = hn(x, y, 6)
    if y < 2 or y > 13:
        return sc((0.3, 0.32, 0.35), 0.9 + 0.2 * n)
    t = 1.0 - abs((x + 0.5) / 16 - 0.5) * 2
    return sc((0.45 + 0.5 * t, 0.78 + 0.22 * t, 1.0), 0.95 + 0.05 * n)


def arrow_px(x, y):
    """The service lift's sign: pale chevrons pointing up on dark iron."""
    n = hn(x, y, 7)
    d = abs(x + 0.5 - 8)
    yy = (y % 11)
    if d < 6 and abs(yy - (2 + d * 0.9)) < 1.3:
        return sc((0.8, 0.95, 1.0), 0.95 + 0.05 * n)
    return sc((0.1, 0.11, 0.13), 0.8 + 0.4 * n)


MATS = []


def mat(material):
    MATS.append(material)
    return len(MATS) - 1


FLOOR = mat(C.game(0x0EE2))    # riveted grey-blue plates: the chambers' floors
PLATE = mat(C.game(0x1873))    # diamond plate: the pipes' floors, the lift
TILE = mat(C.game(0x00CD))     # blue-grey tiles: the pump hall's floor, the alcoves
WALL = mat(C.game(0x1056))     # blue-grey panels: the chambers' walls
PIPES = mat(C.game(0x14AF))    # runs of pipe: the pipes' walls, the chambers' and the hall's low band
CEIL = mat(C.game(0x1697))     # dark panels: domes and ceilings
IRON = mat(C.game(0x0B0C))     # riveted iron: the hall's walls, the lintels
METAL = mat(C.game(0x0B0B))    # worn metal: the pumps
GRATE = mat(C.game(0x0DBF))    # slatted grating: the vent stacks
RAIL = mat(C.game(0x0F66))     # dark riveted rails: trims, the lift's frame
BED = mat(C.game(0x0EE1))      # the coolant channel's bed
COOL = mat(C.game(0x11D0, "water"))  # the coolant (a scrolled surface over the channel's bed)
GAUGE = mat(C.own_material("vents_gauge", C.own_image("vents_gauge", 32, 32, gauge_px)))
VALVE = mat(C.own_material("vents_valve", C.own_image("vents_valve", 32, 32, valve_px)))
HAZARD = mat(C.own_material("vents_hazard", C.own_image("vents_hazard", 32, 16, hazard_px)))
GRILLE = mat(C.own_material("vents_grille", C.own_image("vents_grille", 16, 16, grille_px)))
HATCH = mat(C.own_material("vents_hatch", C.own_image("vents_hatch", 32, 64, hatch_px)))
GLOW = mat(C.own_material("vents_glow", C.own_image("vents_glow", 16, 16, glow_px)))
ARROW = mat(C.own_material("vents_arrow", C.own_image("vents_arrow", 16, 32, arrow_px)))


def mesh(name, uv=200.0):
    return Mesh(name, MATS, coll, uv_size=uv)


# ------------------------------------------------------------------------------------------------ the plan in numbers
PIPE_W, PIPE_H = 200.0, 250.0
WALL_H, DOME_H, GRILLE_R = 360.0, 520.0, 60.0
BAND = 130.0          # the pipe band at the foot of a chamber's wall
STEP_DEG = 20.0       # the chambers' outlines: a vertex at least every 20 degrees
RING = 600.0


def ring(deg):
    return (round(RING * math.cos(math.radians(deg))), round(RING * math.sin(math.radians(deg))))


# name: (x, z, radius, floor)
CH = {
    "A": (0.0, 1045.0, 160.0, 500.0),
    "K1": (*ring(90), 210.0, 490.0),
    "K2": (*ring(150), 260.0, 470.0),
    "K3": (*ring(210), 260.0, 440.0),
    "K4": (*ring(270), 220.0, 400.0),
    "K5": (*ring(330), 260.0, 430.0),
    "K6": (*ring(30), 260.0, 470.0),
    "M": (0.0, 0.0, 260.0, 450.0),
}
CH["D1"] = (CH["K3"][0] - 600 * math.cos(math.radians(30)), CH["K3"][1] - 600 * 0.5, 230.0, 470.0)
CH["D2"] = (CH["K6"][0] + 600 * math.cos(math.radians(30)), CH["K6"][1] + 600 * 0.5, 230.0, 450.0)
CH["D1"] = (round(CH["D1"][0]), round(CH["D1"][1]), 230.0, 470.0)
CH["D2"] = (round(CH["D2"][0]), round(CH["D2"][1]), 230.0, 450.0)

# the pump hall
HX0, HX1, HZ0, HZ1, HY, HTOP = -420.0, 420.0, -1496.0, -936.0, 370.0, 970.0
HCZ = (HZ0 + HZ1) / 2                       # -1216
CHAN = (HX0, HZ0, HX1, -1406.0)             # the coolant channel along the north wall
CHAN_BED, CHAN_LVL = 335.0, 362.0           # 27 deep, 8 under the bank
ALC_UP = (-60.0, -1586.0, 60.0, HZ0)        # the health upgrade's alcove behind the channel (north)
ALC_CHEST = (-520.0, -1300.0, HX0, -1140.0)  # the rockets chest's alcove (west)
ALC_T3 = (-330.0, HZ1, -210.0, -846.0)      # Tribal 3's alcove (south wall, west of the door)
ALC_T4 = (HX1, -1120.0, 510.0, -1000.0)     # Tribal 4's alcove (east wall)
ALC_H = 200.0
LIFT = (HX1, -1400.0, 680.0, -1240.0)       # the service lift's room off the east wall
HALL_DOOR = (-100.0, 100.0)                 # the pipe from K4 into the south wall

# links: pipes between chambers (and K4's into the hall's south wall)
LINKS = [("A", "K1"), ("K1", "K2"), ("K1", "K6"), ("K2", "K3"), ("K3", "K4"), ("K4", "K5"), ("K5", "K6"),
         ("K2", "M"), ("M", "K5"), ("K3", "M"), ("M", "K6"), ("K3", "D1"), ("K6", "D2"), ("K4", "HALL")]
HALL_PT = (0.0, HZ1)


def cover_rects(name, lo, hi):
    """Four square blocks on a chamber's diagonals, lo..hi from its centre each way."""
    x, z = CH[name][0], CH[name][1]
    return [(x + sx * (lo if sx > 0 else hi), z + sz * (lo if sz > 0 else hi),
             x + sx * (hi if sx > 0 else lo), z + sz * (hi if sz > 0 else lo))
            for sx in (-1, 1) for sz in (-1, 1)]


# cover: vent stacks (swarmer chambers) and coolant tanks (the dead ends)
COVER = {
    "K2": cover_rects("K2", 50, 135), "M": cover_rects("M", 50, 135), "K5": cover_rects("K5", 50, 135),
    "D1": cover_rects("D1", 45, 125), "D2": cover_rects("D2", 45, 125),
}
REGION = {"K2": 170, "M": 170, "K5": 170, "D1": 155, "D2": 155}
# the hall: pumps (north row, 120 tall) and vent stacks (south row, 110 tall)
PUMPS = [(cx - 40, HCZ - 150, cx + 40, HCZ - 50) for cx in (-290, -145, 0, 145, 290)]
STACKS = [(cx - 40, HCZ + 70, cx + 40, HCZ + 150) for cx in (-290, -130, 130, 290)]
HALL_REGION = (-360.0, HCZ - 175, 360.0, HCZ + 215)


# ------------------------------------------------------------------------------------------------ geometry helpers
def mouths_of(name):
    """(angle in degrees, the other end) of each pipe meeting chamber `name`."""
    x, z = CH[name][0], CH[name][1]
    out = []
    for a, b in LINKS:
        if name not in (a, b):
            continue
        other = b if a == name else a
        ox, oz = HALL_PT if other == "HALL" else (CH[other][0], CH[other][1])
        out.append((math.degrees(math.atan2(oz - z, ox - x)) % 360.0, other))
    return sorted(out)


FLATS = {"A": [(90.0, 120.0)]}   # flat walls (angle, width): the hatch on A's south wall


def outline(name):
    """The chamber's polygon: [(angle, kind of the edge from this vertex: "mouth" (a pipe's chord), "flat" (a flat
    wall) or None (the round wall))], counter-clockwise in angle."""
    R = CH[name][2]
    items = [(phi, math.degrees(math.asin(PIPE_W / 2 / R)), "mouth") for phi, _ in mouths_of(name)]
    items += [(phi, math.degrees(math.asin(w / 2 / R)), "flat") for phi, w in FLATS.get(name, [])]
    items.sort()
    pts = []
    for i, (phi, al, kind) in enumerate(items):
        a1 = phi + al
        nphi, nal, _ = items[(i + 1) % len(items)]
        nxt = nphi - nal + (360.0 if i == len(items) - 1 else 0.0)
        gap = nxt - a1
        assert gap > 10.0, (name, phi, gap)
        pts.append(((phi - al) % 360.0, kind))
        n = max(1, math.ceil(gap / STEP_DEG))
        for k in range(n):
            pts.append(((a1 + gap * k / n) % 360.0, None))
    return pts


def at(name, deg, r=None):
    x, z, R, _ = CH[name]
    r = R if r is None else r
    return (x + r * math.cos(math.radians(deg)), z + r * math.sin(math.radians(deg)))


def clip(poly, a, b):
    """Sutherland-Hodgman: the part of poly [(x, z)] on the left of a -> b (inside a counter-clockwise outline seen
    with z down: the side the centre is on)."""
    def side(p):
        return (b[0] - a[0]) * (p[1] - a[1]) - (b[1] - a[1]) * (p[0] - a[0])
    out = []
    for i in range(len(poly)):
        p, q = poly[i], poly[(i + 1) % len(poly)]
        sp, sq = side(p), side(q)
        if sp >= 0:
            out.append(p)
        if (sp >= 0) != (sq >= 0):
            t = sp / (sp - sq)
            out.append((p[0] + (q[0] - p[0]) * t, p[1] + (q[1] - p[1]) * t))
    return out


def area(poly):
    return 0.5 * abs(sum(poly[i][0] * poly[(i + 1) % len(poly)][1] - poly[(i + 1) % len(poly)][0] * poly[i][1]
                         for i in range(len(poly))))


def floor_cells(m, verts, y, holes, mat_, box):
    """Floor over the convex polygon `verts` [(x, z)], in cells of at most 100 through every hole's edges, the holes
    (cover blocks) left out (no hidden ground under them)."""
    x0, z0, x1, z1 = box
    xs = C._cuts(x0, x1, [v for h in holes for v in (h[0], h[2])], 100.0)
    zs = C._cuts(z0, z1, [v for h in holes for v in (h[1], h[3])], 100.0)
    cx = sum(p[0] for p in verts) / len(verts)
    cz = sum(p[1] for p in verts) / len(verts)
    # orient the outline so the centre is on the left of every edge
    a, b = verts[0], verts[1]
    if (b[0] - a[0]) * (cz - a[1]) - (b[1] - a[1]) * (cx - a[0]) < 0:
        verts = verts[::-1]
    for i in range(len(xs) - 1):
        for j in range(len(zs) - 1):
            u0, u1, v0, v1 = xs[i], xs[i + 1], zs[j], zs[j + 1]
            mx, mz = (u0 + u1) / 2, (v0 + v1) / 2
            if any(h[0] < mx < h[2] and h[1] < mz < h[3] for h in holes):
                continue
            poly = [(u0, v0), (u1, v0), (u1, v1), (u0, v1)]
            for k in range(len(verts)):
                poly = clip(poly, verts[k], verts[(k + 1) % len(verts)])
                if len(poly) < 3:
                    break
            if len(poly) < 3 or area(poly) < 4.0:
                continue
            m.face([(p[0], p[1], y) for p in poly], mat_, (0, 0, 1))


def decal_on(m, a, b, centre, out, y0, y1, mat_, frac=(0.0, 1.0)):
    """A picture of our own on a wall from a to b ((x, z)), `out` in front of it towards `centre`, over the part
    frac of its length, from y0 to y1."""
    dx, dz = b[0] - a[0], b[1] - a[1]
    ln = math.hypot(dx, dz)
    nx, nz = -dz / ln, dx / ln
    mx, mz = (a[0] + b[0]) / 2, (a[1] + b[1]) / 2
    if (centre[0] - mx) * nx + (centre[1] - mz) * nz < 0:
        nx, nz = -nx, -nz
    p = (a[0] + dx * frac[0] + nx * out, a[1] + dz * frac[0] + nz * out)
    q = (a[0] + dx * frac[1] + nx * out, a[1] + dz * frac[1] + nz * out)
    # bottom-left, bottom-right, top-right, top-left as seen from the centre's side
    if (q[0] - p[0]) * nz - (q[1] - p[1]) * nx > 0:
        p, q = q, p
    C.decal(m, [(p[0], p[1], y0), (q[0], q[1], y0), (q[0], q[1], y1), (p[0], p[1], y1)], mat_)


# ------------------------------------------------------------------------------------------------ the chambers
cham = mesh("chambers")
deco = mesh("decor", uv=100.0)
LAMPS = []
COOL_L = (0.3, 0.5, 0.62)
CHORDS = {}   # (chamber, other) -> (chord centre, its two ends, floor)
FLAT_EDGES = {}
for name, (cx, cz, R, y) in CH.items():
    ol = outline(name)
    verts = [at(name, a) for a, _ in ol]
    ms = mouths_of(name)
    holes = COVER.get(name, [])
    floor_cells(cham, verts, y, holes, FLOOR, (cx - R, cz - R, cx + R, cz + R))
    mi = 0
    for k, (a, kind) in enumerate(ol):
        p, q = verts[k], verts[(k + 1) % len(verts)]
        inward = (cx - (p[0] + q[0]) / 2, cz - (p[1] + q[1]) / 2, 0)
        if kind == "flat":
            FLAT_EDGES[name] = (p, q)
        if kind == "mouth":
            phi, other = ms[mi]
            mi += 1
            mid = ((p[0] + q[0]) / 2, (p[1] + q[1]) / 2)
            CHORDS[(name, other)] = (mid, p, q, y)
            cham.wall(p, q, y + PIPE_H, y + PIPE_H, y + WALL_H, y + WALL_H, IRON, inward)  # the lintel
            decal_on(deco, p, q, (cx, cz), 4, y + PIPE_H + 6, y + PIPE_H + 30, HAZARD)
            continue
        cham.wall(p, q, y, y, y + BAND, y + BAND, PIPES, inward)
        cham.wall(p, q, y + BAND, y + BAND, y + WALL_H, y + WALL_H, WALL, inward)
    # the dome up to the grille
    inner = [at(name, a, GRILLE_R) for a, _ in ol]
    for k in range(len(ol)):
        p, q = verts[k], verts[(k + 1) % len(verts)]
        pi, qi = inner[k], inner[(k + 1) % len(inner)]
        cham.face([(p[0], p[1], y + WALL_H), (q[0], q[1], y + WALL_H), (qi[0], qi[1], y + DOME_H),
                   (pi[0], pi[1], y + DOME_H)], CEIL, (0, 0, -1))
    deco.face([(p[0], p[1], y + DOME_H) for p in inner], GRILLE, (0, 0, -1),
              [(0.5 + (p[0] - cx) / (2 * GRILLE_R), 0.5 + (p[1] - cz) / (2 * GRILLE_R)) for p in inner])
    LAMPS.append((cx, cz, y + DOME_H - 30, R + 260, COOL_L))
    LAMPS.append((cx, cz, y + 120, R + 40, (0.08, 0.13, 0.16)))
    # gauges, valves and glowing coolant tubes on the walls (the edges furthest from the mouths)
    walls_free = [k for k, (a, kd) in enumerate(ol) if kd is None and ol[(k - 1) % len(ol)][1] is None
                  and ol[(k + 1) % len(ol)][1] is None]
    rnd = sorted(walls_free, key=lambda k: ((sum(map(ord, name)) * 7 + k * 13) % 97))
    for j, k in enumerate(rnd[:3]):
        p, q = verts[k], verts[(k + 1) % len(verts)]
        if j == 0:
            decal_on(deco, p, q, (cx, cz), 4, y + 110, y + 160, GAUGE, (0.3, 0.7))
        elif j == 1:
            decal_on(deco, p, q, (cx, cz), 4, y + 60, y + 260, GLOW, (0.4, 0.6))
            mx, mz = (p[0] + q[0]) / 2, (p[1] + q[1]) / 2
            LAMPS.append((mx, mz, y + 160, 220, (0.18, 0.32, 0.4)))
        else:
            decal_on(deco, p, q, (cx, cz), 4, y + 90, y + 150, VALVE, (0.3, 0.7))
    # cover blocks
    for (x0, z0, x1, z1) in holes:
        if name.startswith("D"):   # coolant tanks: metal, a glowing band
            deco.box(x0, z0, x1, z1, y, y + 115, METAL)
        else:                      # vent stacks: grating, a grille on top
            deco.box(x0, z0, x1, z1, y, y + 110, GRATE, top=GRILLE)

spots["chambers"] = {k: list(v) for k, v in CH.items()}
spots["mouths"] = {k: [[round(a, 1), o] for a, o in mouths_of(k)] for k in CH}
spots["cover"] = COVER
spots["region"] = {k: [CH[k][0] - r, CH[k][1] - r, CH[k][0] + r, CH[k][1] + r] for k, r in REGION.items()}

# ------------------------------------------------------------------------------------------------ the pipes
pipes = mesh("pipes")


def pipe(a, b):
    """The pipe from chamber a's mouth to b's (or the hall's south wall): floor, walls and ceiling in cells."""
    pa, la, ra, ya = CHORDS[(a, b)]
    if b == "HALL":
        pb, yb = (HALL_PT[0], HALL_PT[1]), HY
    else:
        pb, _, _, yb = CHORDS[(b, a)]
    dx, dz = pb[0] - pa[0], pb[1] - pa[1]
    L = math.hypot(dx, dz)
    ux, uz = dx / L, dz / L
    nx, nz = -uz, ux
    w = PIPE_W / 2

    def P(u, v):
        return (pa[0] + ux * u + nx * v, pa[1] + uz * u + nz * v)

    def Y(u):
        return ya + (yb - ya) * u / L
    us = C.cuts(0.0, L, 100.0)
    for u0, u1 in zip(us, us[1:]):
        for v0, v1 in ((-w, 0.0), (0.0, w)):
            pts = [P(u0, v0), P(u1, v0), P(u1, v1), P(u0, v1)]
            ys = [Y(u0), Y(u1), Y(u1), Y(u0)]
            pipes.face([(p[0], p[1], yy) for p, yy in zip(pts, ys)], PLATE, (0, 0, 1))
            pipes.face([(p[0], p[1], yy + PIPE_H) for p, yy in zip(pts, ys)], CEIL, (0, 0, -1))
    ws = C.cuts(0.0, L, 200.0)
    for u0, u1 in zip(ws, ws[1:]):
        for v, sgn in ((-w, 1), (w, -1)):
            p, q = P(u0, v), P(u1, v)
            pipes.wall(p, q, Y(u0), Y(u1), Y(u0) + PIPE_H, Y(u1) + PIPE_H, PIPES, (nx * sgn, nz * sgn, 0))
    mid = P(L / 2, 0)
    LAMPS.append((mid[0], mid[1], Y(L / 2) + 200, 260, (0.12, 0.22, 0.28)))
    return {"from": a, "to": b, "a": pa, "b": pb, "ya": ya, "yb": yb, "length": L}


spots["pipes"] = [pipe(a, b) for a, b in LINKS]

# ------------------------------------------------------------------------------------------------ the pump hall
hall = mesh("hall")
# floor (south of the channel), cut round the pumps and stacks
hx = C._cuts(HX0, HX1, [v for h in PUMPS + STACKS for v in (h[0], h[2])] + list(HALL_DOOR) + [-330, -210], 100.0)
hz = C._cuts(CHAN[3], HZ1, [v for h in PUMPS + STACKS for v in (h[1], h[3])] + [-1400, -1240, -1300, -1140, -1120,
                                                                                 -1000], 100.0)
for i in range(len(hx) - 1):
    for j in range(len(hz) - 1):
        u0, u1, v0, v1 = hx[i], hx[i + 1], hz[j], hz[j + 1]
        mx, mz = (u0 + u1) / 2, (v0 + v1) / 2
        if any(h[0] < mx < h[2] and h[1] < mz < h[3] for h in PUMPS + STACKS):
            continue
        hall.face([(u0, v0, HY), (u1, v0, HY), (u1, v1, HY), (u0, v1, HY)], TILE, (0, 0, 1))
# the coolant channel: its bed and surface, the bank
cool = mesh("coolant", uv=128.0)
C.water_box(hall, CHAN, [], CHAN_BED, CHAN_LVL, BED, COOL, piece=(200.0, 90.0), wm=cool)
C.plane_rect(hall, "z", CHAN[3], HX0, CHAN_BED, HX1, HY, [], IRON, (0, -1, 0))
# walls: a pipe band, then riveted iron, with their openings
DOOR_H = HY + PIPE_H
C.plane_rect(hall, "z", HZ1, HX0, HY, HX1, HY + BAND, [(HALL_DOOR[0], HY, HALL_DOOR[1], DOOR_H),
                                                     (ALC_T3[0], HY, ALC_T3[2], HY + ALC_H)], PIPES, (0, -1, 0))
C.plane_rect(hall, "z", HZ1, HX0, HY + BAND, HX1, HTOP, [(HALL_DOOR[0], HY, HALL_DOOR[1], DOOR_H),
                                                        (ALC_T3[0], HY, ALC_T3[2], HY + ALC_H)], IRON, (0, -1, 0))
C.plane_rect(hall, "z", HZ0, HX0, CHAN_BED, HX1, HY + BAND, [(ALC_UP[0], HY, ALC_UP[2], HY + ALC_H)], PIPES,
             (0, 1, 0))
C.plane_rect(hall, "z", HZ0, HX0, HY + BAND, HX1, HTOP, [(ALC_UP[0], HY, ALC_UP[2], HY + ALC_H)], IRON, (0, 1, 0))
for xw, face_dir, holes in ((HX0, (1, 0, 0), [(ALC_CHEST[1], HY, ALC_CHEST[3], HY + ALC_H)]),
                            (HX1, (-1, 0, 0), [(LIFT[1], HY, LIFT[3], DOOR_H),
                                               (ALC_T4[1], HY, ALC_T4[3], HY + ALC_H)])):
    C.plane_rect(hall, "x", xw, HZ0, CHAN_BED, CHAN[3], HY, [], PIPES, face_dir)          # the channel's ends
    C.plane_rect(hall, "x", xw, HZ0, HY, HZ1, HY + BAND, holes, PIPES, face_dir)
    C.plane_rect(hall, "x", xw, HZ0, HY + BAND, HZ1, HTOP, holes, IRON, face_dir)
C.ceiling(hall, HX0, HZ0, HX1, HZ1, HTOP, CEIL, size=210.0)


def alcove(m, rect, open_side, h=ALC_H, fmat=TILE, wmat=IRON):
    x0, z0, x1, z1 = rect
    C.tiled(m, x0, z0, x1, z1, HY, fmat, size=100.0)
    C.ceiling(m, x0, z0, x1, z1, HY + h, CEIL, size=100.0)
    C.walls(m, x0, z0, x1, z1, HY, HY + h, wmat, which="nsew".replace(open_side, ""), inward=True)


alcove(hall, ALC_UP, "s")
alcove(hall, ALC_CHEST, "e")
alcove(hall, ALC_T3, "n")
alcove(hall, ALC_T4, "w")
# the service lift's room: a cage on its back wall, the sign over it
C.tiled(hall, LIFT[0], LIFT[1], LIFT[2], LIFT[3], HY, PLATE, size=100.0)
C.ceiling(hall, LIFT[0], LIFT[1], LIFT[2], LIFT[3], DOOR_H, CEIL, size=100.0)
C.walls(hall, LIFT[0], LIFT[1], LIFT[2], LIFT[3], HY, DOOR_H, PIPES, which="nse", inward=True)
C.decal(deco, [(LIFT[2] - 4, LIFT[3] - 20, HY), (LIFT[2] - 4, LIFT[1] + 20, HY), (LIFT[2] - 4, LIFT[1] + 20, HY + 200),
               (LIFT[2] - 4, LIFT[3] - 20, HY + 200)], GRILLE)
C.decal(deco, [(LIFT[2] - 4, -1335, HY + 206), (LIFT[2] - 4, -1305, HY + 206), (LIFT[2] - 4, -1305, HY + 246),
               (LIFT[2] - 4, -1335, HY + 246)], ARROW)
# hazard bands over the hall's openings, gauges and valves on its walls, coolant tubes
C.decal(deco, [(HX1 - 4, LIFT[3], DOOR_H + 6), (HX1 - 4, LIFT[1], DOOR_H + 6), (HX1 - 4, LIFT[1], DOOR_H + 30),
               (HX1 - 4, LIFT[3], DOOR_H + 30)], HAZARD)
C.decal(deco, [(HALL_DOOR[0], HZ1 - 4, DOOR_H + 6), (HALL_DOOR[1], HZ1 - 4, DOOR_H + 6),
               (HALL_DOOR[1], HZ1 - 4, DOOR_H + 30), (HALL_DOOR[0], HZ1 - 4, DOOR_H + 30)], HAZARD)
for gx in (-300, -150, 150, 300):   # coolant tubes on the north wall over the channel
    C.decal(deco, [(gx - 12, HZ0 + 4, HY + 40), (gx + 12, HZ0 + 4, HY + 40), (gx + 12, HZ0 + 4, HY + 330),
                   (gx - 12, HZ0 + 4, HY + 330)], GLOW)
    LAMPS.append((gx, HZ0 + 80, HY + 200, 300, (0.2, 0.36, 0.46)))
for gz in (-1050, -1350):          # gauges on the west wall
    C.decal(deco, [(HX0 + 4, gz + 25, HY + 150), (HX0 + 4, gz - 25, HY + 150), (HX0 + 4, gz - 25, HY + 200),
                   (HX0 + 4, gz + 25, HY + 200)], GAUGE)
# pumps: metal housings, a valve wheel on the front of each, a warm glow (the heat they carry off)
for (x0, z0, x1, z1) in PUMPS:
    deco.box(x0, z0, x1, z1, HY, HY + 120, METAL, top=IRON)
    C.decal(deco, [(x0 + 15, z1 + 4, HY + 45), (x1 - 15, z1 + 4, HY + 45), (x1 - 15, z1 + 4, HY + 95),
                   (x0 + 15, z1 + 4, HY + 95)], VALVE)
for (x0, z0, x1, z1) in STACKS:
    deco.box(x0, z0, x1, z1, HY, HY + 110, GRATE, top=GRILLE)
# overhead pipes along the long walls (out of reach, clear of the walls)
for zp, d in ((HZ1 - 40, -1), (HZ0 + 40, 1)):
    deco.box(HX0 + 2, zp - 14, HX1 - 2, zp + 14, HY + 470, HY + 498, RAIL, bottom=True)
LAMPS.append((0, HCZ, HTOP - 60, 700, (0.22, 0.38, 0.48)))
LAMPS.append((-250, HCZ - 100, HY + 150, 260, (0.42, 0.16, 0.06)))   # the pumps' warm glow, against the blue
LAMPS.append((250, HCZ - 100, HY + 150, 260, (0.42, 0.16, 0.06)))
LAMPS.append((0, ALC_UP[1] + 45, HY + 150, 200, (0.3, 0.5, 0.4)))     # the upgrade's alcove
LAMPS.append((ALC_CHEST[0] + 50, -1220, HY + 150, 220, (0.35, 0.3, 0.2)))
LAMPS.append(((LIFT[0] + LIFT[2]) / 2, (LIFT[1] + LIFT[3]) / 2, HY + 200, 300, (0.3, 0.45, 0.5)))

# the vent hatch: a hatch on A's south wall (the way back), a hazard band at its foot
ax, az, aR, ay = CH["A"]
hp, hq = FLAT_EDGES["A"]
decal_on(deco, hp, hq, (ax, az), 4, ay, ay + 180, HATCH, (0.125, 0.875))
A_WALL = (hp[1] + hq[1]) / 2   # the flat wall's z
LAMPS.append((ax, az + 80, ay + 200, 300, (0.4, 0.2, 0.08)))   # the Bellows' warmth through the hatch

spots["hall"] = {"rect": [HX0, HZ0, HX1, HZ1], "floor": HY, "top": HTOP, "pumps": PUMPS, "stacks": STACKS,
                 "region": HALL_REGION, "channel": CHAN, "alc_up": ALC_UP, "alc_chest": ALC_CHEST, "alc_t3": ALC_T3,
                 "alc_t4": ALC_T4, "lift": LIFT}
spots["start0"] = (ax, az - 30, ay)
spots["exit_back"] = (ax, A_WALL - 50, ay)
spots["start1"] = (LIFT[0] + 70, (LIFT[1] + LIFT[3]) / 2, HY)
spots["exit_lift"] = (LIFT[2] - 45, (LIFT[1] + LIFT[3]) / 2, HY)

# ------------------------------------------------------------------------------------------------ light
cham.build()
pipes.build()
hall.build()
cool.build()
deco.build()
level = [o for o in coll.all_objects if o.type == "MESH"]


def extra(x, z, y, mname):
    if mname.startswith(("vents_glow", "vents_grille")):
        return (2.6, 2.6, 2.6)
    if mname.startswith(("vents_gauge", "vents_valve", "vents_hazard", "vents_hatch", "vents_arrow")):
        return (1.7, 1.7, 1.7)
    return (1.0, 1.0, 1.0)


# the kit's ambient (0.1, 0.12, 0.14) lifted (these textures go black under it, as 3.1 and 3.3 found)
C.bake(level, (0.0, 0.0, -1.0), (0.0, 0.0, 0.0), (0.2, 0.24, 0.28), lamps=LAMPS, extra=extra, shadow=0.0,
       ao_strength=0.4)
cme = bpy.data.objects["coolant"].data  # the coolant glows pale blue of itself
ccol = cme.color_attributes.get("Col")
for d in ccol.data:
    d.color_srgb = (0.7, 0.92, 1.0, 1.0)

# ------------------------------------------------------------------------------------------------ export
os.makedirs(C.OUT, exist_ok=True)
report = jfg64.budgets(level)
out = jfg64.export(os.path.join(C.OUT, NAME + ".glb"), collection=coll)
spots["budgets"] = report
spots["export"] = {k: v for k, v in out.items() if k != "objects"} if isinstance(out, dict) else str(out)
spots["lamps"] = len(LAMPS)


def tup(v):
    if isinstance(v, (tuple, list)) and v and isinstance(v[0], (int, float)):
        return [round(c, 1) if isinstance(c, (int, float)) else c for c in v]
    if isinstance(v, (list, tuple)):
        return [tup(x) for x in v]
    if isinstance(v, dict):
        return {k: tup(x) for k, x in v.items()}
    return v


with open(os.path.join(C.OUT, NAME + "_spots.json"), "w", encoding="utf-8") as f:
    json.dump({k: tup(v) for k, v in spots.items()}, f, indent=1, default=str)
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(C.OUT, NAME + ".blend"))
print("VENTS", json.dumps(report, default=str))
print("PARTS", json.dumps({o.name: sum(len(p.vertices) - 2 for p in o.data.polygons) for o in level}))
