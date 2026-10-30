"""Blackwater Grotto (Corsair Reach 1.3): builds the level from nothing and exports blender/out/blackwater.glb.

    blender --background --factory-startup --addons jfg64 --python blackwater.py

A sea cave walked down round its sides at night. The torch tunnel (400 -> 360) opens on a wooden walkway along the
north and west walls (360) that looks over the lagoon (water 0, its floor -30: 30 deep everywhere, so a fall is
never a trap), the galleon wedged against the north wall under a crack in the roof, and the vault door seen through
the bars of its yard. Down the west wall the crab ledges (260, 160), two rope bridges by the island (160) to the east
landing (40); a stair climbs from the landing back up to the walkway (the loop). The jetty leads to the galleon's
hull door (the winch on its forecastle holds it); through the hold and out of a breach in its stern to the yard, the
vault door (purple key, from the island), the vault (-100) and the sea door, the level's exit.

Game units: x east, z south (north is -z), y up. The level's numbers are in levels/1.3_blackwater.md (As built).
"""
import json
import math
import os
import random
import sys

import bpy

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import common as C  # noqa: E402
from common import Mesh, tiled, post, collider  # noqa: E402
import jfg64  # noqa: E402

NAME = "blackwater"
scene, coll = C.new_scene(NAME)
rnd = random.Random(31)

FL, WL, WALK = -30.0, 0.0, 360.0   # the lagoon's floor, its water, the walkway


# ------------------------------------------------------------------------------------------------ our own images
def rock_bg(x, y, seed=0):
    v = ((x * 37 + y * 91 + seed * 13) % 17) / 17.0
    return (0.22 + 0.06 * v, 0.27 + 0.06 * v, 0.27 + 0.05 * v)


def marks_px(x, y):
    """The corsairs' marks daubed on the rock in red ochre: a ring over a cross of two strokes, three dots."""
    c = rock_bg(x, y)
    ochre = (0.62, 0.2, 0.12)
    d = math.hypot(x - 15.5, y - 10)
    ring = 5.0 <= d <= 7.2
    cross = (abs((x - 16) - (y - 23)) < 1.4 or abs((x - 16) + (y - 23)) < 1.4) and 17 <= y <= 29 and 9 <= x <= 23
    dots = any(math.hypot(x - dx, y - dy) < 1.6 for dx, dy in ((5, 27), (27, 27), (16, 3)))
    if ring or cross or dots:
        k = 0.85 + 0.15 * (((x * 7 + y * 3) % 5) / 5)
        return tuple(v * k for v in ochre)
    return c


def coins_px(x, y):
    """Gold coins heaped together: rims, faces, a glint each."""
    base = (0.42, 0.3, 0.08)
    for cy in range(2, 32, 7):
        for cx in range((cy // 7) % 2 * 3 + 2, 33, 7):
            d = math.hypot(x - cx, y - cy)
            if d < 3.4:
                if d < 1.0 and (x + y) % 3 == 0:
                    return (1.0, 0.95, 0.7)
                return (0.95, 0.75, 0.25) if d < 2.4 else (0.68, 0.48, 0.12)
    return base


def chart_px(x, y):
    """The trade chart: a coast on parchment, a dotted red route north-east to a mark."""
    edge = min(x, y, 31 - x, 31 - y)
    paper = (0.86, 0.76, 0.55) if edge > 1 else (0.6, 0.48, 0.3)
    coast = abs(y - (20 + 4 * math.sin(x / 4.0))) < 1.0 and x < 18
    land = y > 20 + 4 * math.sin(x / 4.0) and x < 18
    route = abs((y - 26) + (x - 4) * 0.83) < 0.9 and (x + y) % 3 != 0 and 4 <= x <= 27
    mark = abs(x - 27) == abs(y - 6) and abs(x - 27) <= 2
    rose = 2.5 <= math.hypot(x - 6, y - 6) <= 3.5 or (x == 6 and 1 <= y <= 11) or (y == 6 and 1 <= x <= 11)
    if mark or route:
        return (0.7, 0.12, 0.1)
    if coast or rose:
        return (0.32, 0.22, 0.14)
    if land:
        return (0.74, 0.66, 0.46)
    return paper


def rope_px(x, y):
    """Twisted rope along the image."""
    t = ((x + y * 0.8) % 6) / 6.0
    k = 0.75 + 0.25 * math.sin(t * math.tau)
    return (0.72 * k, 0.58 * k, 0.36 * k) if 2 <= y <= 13 else (0.3, 0.22, 0.14)


def canvas_px(x, y):
    """Tan sailcloth, a fine weave and a seam."""
    k = 0.92 + 0.08 * ((x + y) % 2)
    if y % 16 == 0:
        k *= 0.75
    return (0.7 * k, 0.6 * k, 0.42 * k)


def iron_px(x, y):
    """Dark iron with a little rust and a rivet."""
    k = 0.85 + 0.15 * (((x * 5 + y * 11) % 7) / 7)
    if math.hypot(x - 7.5, y - 7.5) < 1.6:
        return (0.4, 0.38, 0.36)
    rust = 0.08 if (x * 3 + y * 7) % 9 == 0 else 0.0
    return (0.18 * k + rust, 0.18 * k + rust * 0.4, 0.2 * k)


def falls_px(x, y):
    """Falling water: pale streaks on teal, for a texscroll running down."""
    k = ((x * 7) % 5) / 5.0
    streak = (y + x * 3) % 11 < 3
    return (0.55 + 0.3 * k, 0.8 + 0.15 * k, 0.85) if streak else (0.25 + 0.1 * k, 0.5 + 0.1 * k, 0.55 + 0.1 * k)


def dawn_px(x, y):
    """Through the sea door: the cove at dawn, a pink-gold sky over a dark sea and the sun's edge."""
    hz = 20
    if y < hz:
        t = y / hz
        sky = tuple(a + (b - a) * t for a, b in zip((0.36, 0.32, 0.55), (1.0, 0.72, 0.5)))
        if math.hypot(x - 21, y - hz) < 4.5:
            return (1.0, 0.92, 0.66)
        return sky
    glint = abs(x - 21) < (y - hz) * 0.5 + 1 and (x + y) % 2 == 0
    return (0.95, 0.65, 0.4) if glint else (0.1, 0.2, 0.28)


# ------------------------------------------------------------------------------------------------ materials
MATS = []


def mat(material):
    MATS.append(material)
    return len(MATS) - 1


ROCK = mat(C.game(0x1958))     # wet mossy rock: the cavern's walls, shelf and island faces
CEIL = mat(C.game(0x07F2))     # dark rock: the roof, tunnel ceilings, the way back's darkness
STONE = mat(C.game(0x1660))    # dark grey rock floor: shelves, island, landing, yard, stair
MUD = mat(C.game(0x1959))      # the lagoon's floor
PLANK = mat(C.game(0x193D))    # the walkway's boards, steps, the key tower
DECK = mat(C.game(0x16D9))     # bridges, jetty, gangway, the galleon's floors
HULL = mat(C.game(0x16DB))     # the galleon's hull, pilings, posts, cargo
MASON = mat(C.game(0x0828))    # the vault, its passage, its cells
PAVE = mat(C.game(0x1946))     # the vault's floor
CLIFF = mat(C.game(0x0C40))    # the torch tunnel, the sea door, the smugglers' passage
WATER = mat(C.game(0x0DED, "water"))
FALLS = mat(C.own_material("falls", C.own_image("falls", 16, 32, falls_px)))
LEDGE = mat(jfg64.game_texture_material(0x1660, "ledge", name="ledge_1660"))
MARKS = mat(C.own_material("corsair_marks", C.own_image("corsair_marks", 32, 32, marks_px)))
COINS = mat(C.own_material("gold_coins", C.own_image("gold_coins", 32, 32, coins_px)))
CHART = mat(C.own_material("trade_chart", C.own_image("trade_chart", 32, 32, chart_px)))
ROPE = mat(C.own_material("rope_rail", C.own_image("rope_rail", 16, 16, rope_px)))
CANVAS = mat(C.own_material("tent_canvas", C.own_image("tent_canvas", 16, 16, canvas_px)))
IRON = mat(C.own_material("grille_iron", C.own_image("grille_iron", 16, 16, iron_px)))
DAWN = mat(C.own_material("dawn_cove", C.own_image("dawn_cove", 32, 32, dawn_px)))
EDGE = jfg64.boundary_material()


def mesh(name, uv=200.0):
    return Mesh(name, MATS, coll, uv_size=uv)


cave = mesh("cave", 256.0)        # the cavern's walls, roof and the crack's chimney
rock = mesh("rock", 200.0)        # walkway, shelves, island, landing, yard, stair
wood = mesh("wood", 160.0)        # bridges, jetty, gangway, the galleon, rails, the key tower
lag = mesh("lagoon_floor", 200.0)
wtr = Mesh("lagoon_water", MATS, coll, uv_size=512.0)
falls = Mesh("waterfall", MATS, coll, uv_size=256.0)
vault = mesh("vault", 200.0)      # the passage, the vault, its cells, the sea door
tun = mesh("tunnels", 200.0)      # the torch tunnel, the way back, the smugglers' passage
props = mesh("props", 128.0)      # stalagmites, cover, gold, tents, grille, decals
edges = Mesh("colliders", [EDGE], coll)
spots = {}


# ------------------------------------------------------------------------------------------------ helpers
def cuts(a, b, step):
    n = max(1, math.ceil(abs(b - a) / step - 1e-6))
    return [a + (b - a) * k / n for k in range(n + 1)]


def strip(m, a, b, y0a, y0b, y1a, y1b, mat_, facing, step=200.0):
    """A wall from a to b ((x, z)), bottom y0 and top y1 at each end, in pieces of at most `step` along it (no long
    thin triangles near the hero)."""
    L = math.hypot(b[0] - a[0], b[1] - a[1])
    ts = cuts(0.0, 1.0, step / max(L, 1e-6))
    for t0, t1 in zip(ts, ts[1:]):
        p = (a[0] + (b[0] - a[0]) * t0, a[1] + (b[1] - a[1]) * t0)
        q = (a[0] + (b[0] - a[0]) * t1, a[1] + (b[1] - a[1]) * t1)
        lo0, lo1 = y0a + (y0b - y0a) * t0, y0a + (y0b - y0a) * t1
        hi0, hi1 = y1a + (y1b - y1a) * t0, y1a + (y1b - y1a) * t1
        if hi0 - lo0 < 0.5 and hi1 - lo1 < 0.5:
            continue
        m.face([(p[0], p[1], lo0), (q[0], q[1], lo1), (q[0], q[1], hi1), (p[0], p[1], hi0)], mat_, facing)


def sides(m, x0, z0, x1, z1, y0, top, mat_, which="nsew", inward=False, step=200.0):
    """A block's walls from y0 to top (a height or top(x, z)), facing out (inward: a room's), in pieces."""
    t = top if callable(top) else (lambda x, z, v=top: v)
    b = y0 if callable(y0) else (lambda x, z, v=y0: v)
    k = -1 if inward else 1
    if "n" in which:
        strip(m, (x1, z0), (x0, z0), b(x1, z0), b(x0, z0), t(x1, z0), t(x0, z0), mat_, (0, -k, 0), step)
    if "s" in which:
        strip(m, (x0, z1), (x1, z1), b(x0, z1), b(x1, z1), t(x0, z1), t(x1, z1), mat_, (0, k, 0), step)
    if "e" in which:
        strip(m, (x1, z1), (x1, z0), b(x1, z1), b(x1, z0), t(x1, z1), t(x1, z0), mat_, (k, 0, 0), step)
    if "w" in which:
        strip(m, (x0, z0), (x0, z1), b(x0, z0), b(x0, z1), t(x0, z0), t(x0, z1), mat_, (-k, 0, 0), step)


def ramp_fn(x0, z0, x1, z1, y0, y1, along):
    def hy(x, z):
        t = (x - x0) / (x1 - x0) if along == "x" else (z - z0) / (z1 - z0)
        return y0 + (y1 - y0) * t
    return hy


def block(m, x0, z0, x1, z1, y0, y1, side, top=None, which="nsew", y1b=None, along="x", size=130.0):
    """A walkable block: its top tiled (y1 to y1b along `along` for a ramp), its walls from y0 on `which`."""
    top = side if top is None else top
    y1b = y1 if y1b is None else y1b
    tiled(m, x0, z0, x1, z1, y1, top, y1b, along, size)
    hy = ramp_fn(x0, z0, x1, z1, y1, y1b, along)
    if which:
        sides(m, x0, z0, x1, z1, y0, hy, side, which)
    return hy


def ceiling(m, x0, z0, x1, z1, y, mat_, y1=None, along="x", size=200.0):
    tiled(m, x0, z0, x1, z1, y, mat_, y1, along, size, facing=(0, 0, -1))


def plane_rect(m, plane, c, u0, v0, u1, v1, holes, mat_, facing, step=220.0):
    """A flat wall in the plane x = c (plane "x": u is z) or z = c (plane "z": u is x), v is height, over u0..u1,
    v0..v1 minus rectangular holes (u0, v0, u1, v1), in pieces of at most `step`."""
    for r in C.rects_minus((u0, v0, u1, v1), holes):
        us, vs = cuts(r[0], r[2], step), cuts(r[1], r[3], step)
        for a, b in zip(us, us[1:]):
            for p, q in zip(vs, vs[1:]):
                if plane == "x":
                    pts = [(c, a, p), (c, b, p), (c, b, q), (c, a, q)]
                else:
                    pts = [(a, c, p), (b, c, p), (b, c, q), (a, c, q)]
                m.face(pts, mat_, facing)


def lip(m, a, b, ya, yb, h=150.0, thick=25.0, coll_to=None, mat_=ROCK, seg=200.0, caps=(True, True), under=False):
    """A parapet along a -> b ((x, z)) on floor ya..yb, `thick` to the left of a -> b, `h` tall, in pieces; with
    coll_to (over its top), a collider up to that much over the floor (so nobody hops over). caps: its end faces
    (left out where it butts against another parapet: two faces in one plane flicker)."""
    dx, dz = b[0] - a[0], b[1] - a[1]
    L = math.hypot(dx, dz)
    nx, nz = -dz / L * thick, dx / L * thick
    ts = cuts(0.0, 1.0, seg / L)
    for t0, t1 in zip(ts, ts[1:]):
        p = (a[0] + dx * t0, a[1] + dz * t0)
        q = (a[0] + dx * t1, a[1] + dz * t1)
        y0, y1 = ya + (yb - ya) * t0, ya + (yb - ya) * t1
        pts = [p, q, (q[0] + nx, q[1] + nz), (p[0] + nx, p[1] + nz)]
        tops = [y0 + h, y1 + h, y1 + h, y0 + h]
        foot = [y0, y1, y1, y0]
        m.face([(pp[0], pp[1], tt) for pp, tt in zip(pts, tops)], mat_, (0, 0, 1))
        if under:  # a bar in the air: its underside too
            m.face([(pp[0], pp[1], ff) for pp, ff in zip(pts, foot)], mat_, (0, 0, -1))
        cx, cz = sum(pp[0] for pp in pts) / 4, sum(pp[1] for pp in pts) / 4
        for i in range(4):
            if i == 1 and (t1 < 1.0 or not caps[1]) or i == 3 and (t0 > 0.0 or not caps[0]):
                continue  # the joins between pieces are inside the parapet
            u, w = pts[i], pts[(i + 1) % 4]
            m.face([(u[0], u[1], foot[i]), (w[0], w[1], foot[(i + 1) % 4]), (w[0], w[1], tops[(i + 1) % 4]),
                    (u[0], u[1], tops[i])], mat_, ((u[0] + w[0]) / 2 - cx, (u[1] + w[1]) / 2 - cz, 0))
    if coll_to:
        mx, mz = nx / 2, nz / 2
        collider(edges, (a[0] + mx, a[1] + mz), (b[0] + mx, b[1] + mz), min(ya, yb) + h, max(ya, yb) + coll_to)


def rim(m, x0, z0, x1, z1, y, h, thick, mat_=ROCK):
    """A rim round a square top (a perch, a nest): four parapets that meet without overlapping (the north and south
    ones run the full width, the east and west ones between them, without end faces)."""
    t = thick
    lip(m, (x0, z0), (x1, z0), y, y, h=h, thick=t, mat_=mat_)
    lip(m, (x1, z0 + t), (x1, z1 - t), y, y, h=h, thick=t, mat_=mat_, caps=(False, False))
    lip(m, (x1, z1), (x0, z1), y, y, h=h, thick=t, mat_=mat_)
    lip(m, (x0, z1 - t), (x0, z0 + t), y, y, h=h, thick=t, mat_=mat_, caps=(False, False))


def rails(m, a, b, y, h=110.0, coll_h=420.0, every=100.0):
    """A rope rail on a bridge edge from a to b at deck height y: posts, a rope along the top, a collider over it."""
    for p in cuts(0.0, 1.0, every / math.hypot(b[0] - a[0], b[1] - a[1])):
        post(m, a[0] + (b[0] - a[0]) * p, a[1] + (b[1] - a[1]) * p, 6, y, y + h, HULL, n=4, phase=math.pi / 4)
    dx, dz = b[0] - a[0], b[1] - a[1]
    L = math.hypot(dx, dz)
    ox, oz = -dz / L * 3, dx / L * 3
    for t0, t1 in zip(cuts(0, 1, 200 / L), cuts(0, 1, 200 / L)[1:]):
        p = (a[0] + dx * t0, a[1] + dz * t0)
        q = (a[0] + dx * t1, a[1] + dz * t1)
        for (sx, sz) in ((ox, oz), (-ox, -oz)):
            m.face([(p[0] + sx, p[1] + sz, y + h - 10), (q[0] + sx, q[1] + sz, y + h - 10),
                    (q[0] + sx, q[1] + sz, y + h), (p[0] + sx, p[1] + sz, y + h)], ROPE, (sx, sz, 0))
    collider(edges, a, b, y, y + coll_h)


def fence(m, a, b, ya, yb, h=150.0, every=160.0, coll=550.0, first=True):
    """The walkway's rail along a -> b on floor ya..yb: posts and a rail along their tops at `h`, seen through
    (the first view over the lagoon at eye height: a solid parapet hid it), and a collider in its line from the
    floor to `coll` over it. first: its first post (left out where it starts at another fence's last)."""
    L = math.hypot(b[0] - a[0], b[1] - a[1])
    for t in cuts(0.0, 1.0, every / L)[(0 if first else 1):]:
        y = ya + (yb - ya) * t
        post(m, a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t, 8, y, y + h + 6, HULL, n=4, phase=math.pi / 4)
    dx, dz = (b[0] - a[0]) / L * 3, (b[1] - a[1]) / L * 3
    tr = 9.0 / L  # the rails stop inside the end posts: rails meeting at a corner would overlap
    for k in (1.0,):
        # 6 thick, centred on the line (lip draws `thick` to the left of a -> b)
        aa = (a[0] + (b[0] - a[0]) * tr + dz, a[1] + (b[1] - a[1]) * tr - dx)
        bb = (b[0] - (b[0] - a[0]) * tr + dz, b[1] - (b[1] - a[1]) * tr - dx)
        y0, y1 = ya + (yb - ya) * tr, yb - (yb - ya) * tr
        lip(m, aa, bb, y0 + h * k - 10, y1 + h * k - 10, h=10, thick=6, mat_=HULL, seg=260.0, under=True)
    collider(edges, a, b, min(ya, yb), max(ya, yb) + coll)


def deck(m, x0, z0, x1, z1, y, thick=12.0, which="nsew"):
    """A plank deck (a bridge): top, underside and edges."""
    tiled(m, x0, z0, x1, z1, y, DECK)
    tiled(m, x0, z0, x1, z1, y - thick, DECK, facing=(0, 0, -1), size=200.0)
    sides(m, x0, z0, x1, z1, y - thick, y, HULL, which)


def floor_at(x, z):
    return FL


# ================================================================================================ the cavern's shell
# the roof: a grid at 1000-1130, higher round the crack over the galleon; the crack's cells are open to the sky
XS = [-1650 + 200 * i for i in range(17)]                         # -1650 .. 1550
ZS = [-920, -700, -500, -300, -100, 100, 300, 500, 700, 900]
CRACK = {(150, -700), (150, -500), (350, -500), (350, -300)}       # cells' lower corners (x, z), 200 square
CH = {}
for x in XS:
    for z in ZS:
        CH[(x, z)] = 1040 + rnd.uniform(-60, 80)
for (cx, cz) in CRACK:
    for x in (cx, cx + 200):
        for z in (cz, cz + 200):
            CH[(x, z)] = 1180 + rnd.uniform(-20, 20)


def ceil_at(x, z):
    """The roof's height on a grid line (the walls' tops), between its vertices."""
    i = max(0, min(len(XS) - 2, int((x - XS[0]) // 200)))
    if abs(z - ZS[0]) < 1e-6 or abs(z - ZS[-1]) < 1e-6 or z in ZS:
        za = min(ZS, key=lambda v: abs(v - z))
        t = (x - XS[i]) / 200.0
        return CH[(XS[i], za)] * (1 - t) + CH[(XS[i + 1], za)] * t
    xa = min(XS, key=lambda v: abs(v - x))
    j = max(k for k in range(len(ZS) - 1) if ZS[k] <= z)
    t = (z - ZS[j]) / (ZS[j + 1] - ZS[j])
    return CH[(xa, ZS[j])] * (1 - t) + CH[(xa, ZS[j + 1])] * t


for i in range(len(XS) - 1):
    for j in range(len(ZS) - 1):
        x0, x1, z0, z1 = XS[i], XS[i + 1], ZS[j], ZS[j + 1]
        if (x0, z0) in CRACK:
            continue
        cave.face([(x0, z0, CH[(x0, z0)]), (x1, z0, CH[(x1, z0)]), (x1, z1, CH[(x1, z1)]), (x0, z1, CH[(x0, z1)])],
                  CEIL, (0, 0, -1))
# the crack's chimney: rock up to 1450 round the open cells, open at the top (the sky shows)
for (cx, cz) in CRACK:
    for (a, b, nb) in (((cx, cz), (cx + 200, cz), (cx, cz - 200)), ((cx + 200, cz), (cx + 200, cz + 200), (cx + 200, cz)),
                       ((cx + 200, cz + 200), (cx, cz + 200), (cx, cz + 200)), ((cx, cz + 200), (cx, cz), (cx - 200, cz))):
        if nb in CRACK:
            continue
        cave.face([(a[0], a[1], CH[a]), (b[0], b[1], CH[b]), (b[0], b[1], 1450), (a[0], a[1], 1450)], ROCK, (cx + 100 - (a[0] + b[0]) / 2, cz + 100 - (a[1] + b[1]) / 2, 0))

JAG = {}


def cave_wall(plane, c, us, bottom, rows, inward, special, mat_=ROCK):
    """The cavern's rock wall in the plane x = c or z = c over the cut points `us`: each column from its bottom
    (bottom(u0, u1) -> (b0, b1)) through `rows` (jagged into the cavern by up to 60) to the roof."""
    def P(u, y, j):
        if plane == "x":
            return (c + inward[0] * j, u, y)
        return (u, c + inward[1] * j, y)
    for u0, u1 in zip(us, us[1:]):
        b0, b1 = bottom(u0, u1)
        if b0 is None:
            continue
        t0 = ceil_at(c, u0) if plane == "x" else ceil_at(u0, c)
        t1 = ceil_at(c, u1) if plane == "x" else ceil_at(u1, c)
        hs = [h for h in rows if h > max(b0, b1) + 30]

        def jag(u, h):  # rock juts in only over the hero's reach: at the floor and the water the wall stays flat
            if u in special or h < 500:
                return 0.0
            return JAG.setdefault((plane, c, u, h), rnd.uniform(-15, 60))
        col0 = [(b0, 0.0)] + [(h, jag(u0, h)) for h in hs] + [(t0, 0.0)]
        col1 = [(b1, 0.0)] + [(h, jag(u1, h)) for h in hs] + [(t1, 0.0)]
        face_dir = (inward[0], inward[1], 0)
        for k in range(len(col0) - 1):
            cave.face([P(u0, col0[k][0], col0[k][1]), P(u1, col1[k][0], col1[k][1]),
                       P(u1, col1[k + 1][0], col1[k + 1][1]), P(u0, col0[k + 1][0], col0[k + 1][1])], mat_, face_dir)


# the torch tunnel's mouth in the north wall (behind the walkway), x -1625..-1375, 300 high
TUN_X0, TUN_X1 = -1625.0, -1375.0
xs_n = sorted(set(XS) | {TUN_X0, TUN_X1})
cave_wall("z", -920, xs_n, lambda a, b: (660.0, 660.0) if TUN_X0 <= a and b <= TUN_X1 else (WALK, WALK),
          [620, 860], (0, 1), {TUN_X0, TUN_X1, XS[0], XS[-1]})


# the west wall: behind the walkway (360), the ramp down (360 -> 260), the crab ledge (260), the lagoon (-30)
def west_bottom(z):
    if z < -200:
        return WALK
    if z < 100:
        return WALK - 100 * (z + 200) / 300
    if z < 500:
        return 260.0
    return FL


ALC_Z0, ALC_Z1 = 280.0, 380.0   # the ledge alcove (Tribal 1) in the west wall, 260 -> 400
zs_w = sorted(set(ZS) | {-200, 100, ALC_Z0, ALC_Z1, 500})
cave_wall("x", -1650, [z for z in zs_w if z <= 500],
          lambda a, b: (400.0, 400.0) if ALC_Z0 <= a and b <= ALC_Z1 else (west_bottom(a + 0.01), west_bottom(b - 0.01)),
          [620, 860], (1, 0), {-920, 100, -200, ALC_Z0, ALC_Z1, 500})
cave_wall("x", -1650, [z for z in zs_w if z >= 500], lambda a, b: (FL, FL), [250, 620, 860], (1, 0), {500, 900})

# the east wall: behind the walkway (360), the stair (360 -> 40), the landing (40), the lagoon; the smugglers'
# passage (1.4's arrival) opens in it at z 450..650, 240 high
STUB_Z0, STUB_Z1 = 450.0, 650.0


def east_bottom(z):
    if z < -700:
        return WALK
    if z < 230:
        return WALK - 320 * (z + 700) / 930
    if z < 700:
        return 40.0
    return FL


zs_e = sorted(set(ZS) | {230, STUB_Z0, STUB_Z1, 700})
cave_wall("x", 1550, [z for z in zs_e if z <= 700],
          lambda a, b: (280.0, 280.0) if STUB_Z0 <= a and b <= STUB_Z1 else (east_bottom(a + 0.01), east_bottom(b - 0.01)),
          [620, 860], (-1, 0), {-920, 230, STUB_Z0, STUB_Z1, 700})
cave_wall("x", 1550, [z for z in zs_e if z >= 700], lambda a, b: (FL, FL), [250, 620, 860], (-1, 0), {700, 900})
# the south wall, from the lagoon's floor
cave_wall("z", 900, XS, lambda a, b: (FL, FL), [250, 620, 860], (0, -1), {XS[0], XS[-1]})

# ================================================================================================ A. the torch tunnel
# 250 wide, floor 400 at its north end falling to 360 at the walkway, 300 high; the way back in a dark recess
TZ0, TZ1 = -1400.0, -920.0


def tfloor(x, z):
    return 400 - 40 * (z - TZ0) / (TZ1 - TZ0)


tiled(tun, TUN_X0, TZ0, TUN_X1, TZ1, 400, STONE, 360, along="z")
sides(tun, TUN_X0, TZ0, TUN_X1, TZ1, lambda x, z: tfloor(x, z), lambda x, z: tfloor(x, z) + 300, CLIFF, "ew",
      inward=True)
ceiling(tun, TUN_X0, TZ0, TUN_X1, TZ1, 700, CEIL, 660, along="z")
REC_X0, REC_X1, REC_Z0 = -1560.0, -1440.0, -1480.0
plane_rect(tun, "z", TZ0, TUN_X0, 400, TUN_X1, 700, [(REC_X0, 400, REC_X1, 600)], CLIFF, (0, 1, 0))
tiled(tun, REC_X0, REC_Z0, REC_X1, TZ0, 400, CEIL)
sides(tun, REC_X0, REC_Z0, REC_X1, TZ0, 400, 600, CEIL, "new", inward=True)
ceiling(tun, REC_X0, REC_Z0, REC_X1, TZ0, 600, CEIL)
# the corsairs' marks on both walls, and lantern brackets
C.decal(props, [(TUN_X0 + 3, -1150, 430), (TUN_X0 + 3, -1250, 430), (TUN_X0 + 3, -1250, 530),
                (TUN_X0 + 3, -1150, 530)], MARKS)
C.decal(props, [(TUN_X1 - 3, -1060, 425), (TUN_X1 - 3, -960, 425), (TUN_X1 - 3, -960, 525),
                (TUN_X1 - 3, -1060, 525)], MARKS)
for (bx, bz, by) in ((TUN_X0 + 14, -1300, 520), (TUN_X1 - 14, -1050, 505)):
    props.box(bx - 12, bz - 12, bx + 12, bz + 12, by - 16, by, HULL)   # 2 off the wall
spots["start"] = [-1500, -1310]
spots["way_back_exit"] = [-1500, 400, -1455]
spots["tunnel_lanterns"] = [[TUN_X0 + 12, -1300, 520], [TUN_X1 - 12, -1050, 505]]

# ================================================================================================ B. the walkway
# the north band (z -920..-700) and the west run (x -1650..-1430) at 360, the ramp down to the crab ledge
tiled(rock, -1650, -920, 1550, -700, WALK, PLANK)
W1 = (-1650, -700, -1430, -200)
block(rock, *W1, FL, WALK, ROCK, PLANK, "e")
block(rock, -1650, -200, -1430, 100, FL, WALK, ROCK, PLANK, "e", y1b=260, along="z")

# the band's face over the lagoon (z -700), from the lagoon's floor (the yard's 20 under the vault door), with the
# vault's doorway (160 x 180) and the waterfall's alcove (x 900..1060, 200..320)
DOOR_X0, DOOR_X1, DOOR_H = -230.0, -70.0, 200.0
ALV_X0, ALV_X1, ALV_Y0, ALV_Y1, ALV_Z = 900.0, 1060.0, 200.0, 320.0, -800.0
plane_rect(rock, "z", -700, -1430, FL, -400, WALK, [], ROCK, (0, 1, 0))
plane_rect(rock, "z", -700, -400, 20, 500, WALK, [(DOOR_X0, 20, DOOR_X1, DOOR_H)], ROCK, (0, 1, 0))
plane_rect(rock, "z", -700, 500, FL, 1330, WALK, [(ALV_X0, FL, ALV_X1, ALV_Y1)], ROCK, (0, 1, 0))
# under the alcove's lip: the wall's top edge sits on the ledge's corners (the importer finds the ledge)
plane_rect(rock, "z", -700, ALV_X0, FL, ALV_X1, ALV_Y0, [], ROCK, (0, 1, 0))
tiled(rock, ALV_X0, ALV_Z, ALV_X1, -700, ALV_Y0, LEDGE, size=170.0)
sides(rock, ALV_X0, ALV_Z, ALV_X1, -700, ALV_Y0, ALV_Y1, ROCK, "new", inward=True)
ceiling(rock, ALV_X0, ALV_Z, ALV_X1, -700, ALV_Y1, CEIL)
spots["secret_ledge"] = [980, ALV_Y0, -760]
# the waterfall beside it: water pouring from a cleft under the walkway down the rock to the lagoon (a sheet 2 in
# front of the wall, solid: a non-colliding sheet beside the lagoon's see-through water breaks the segment's
# collision, import_geometry)
FALL_X0, FALL_X1 = 1070.0, 1230.0
for a, b in zip(cuts(FALL_X0, FALL_X1, 80), cuts(FALL_X0, FALL_X1, 80)[1:]):
    for p, q in zip(cuts(WL, 345, 175), cuts(WL, 345, 175)[1:]):
        falls.face([(a, -698, p), (b, -698, p), (b, -698, q), (a, -698, q)], FALLS, (0, 1, 0),
                   [(a / 80, p / 160), (b / 80, p / 160), (b / 80, q / 160), (a / 80, q / 160)])

# rails (150, colliders 400 over them): the band's south edge, the west run, the ramp. Wooden rails rather than
# solid parapets: from the hero's eye (55 up) a 150 parapet hid the lagoon, the galleon and the vault door
fence(wood, (1342, -712), (-1442, -712), WALK, WALK, first=False)  # the stair's rail has the corner post
fence(wood, (-1442, -712), (-1442, -200), WALK, WALK, first=False)
fence(wood, (-1442, -200), (-1442, 100), WALK, 260, first=False)
# torches on posts along the back wall
WALK_TORCHES = [(-1300, -900), (-600, -900), (200, -900), (900, -900), (-1640, -450)]
for (x, z) in WALK_TORCHES:
    post(wood, x, z, 8, WALK, WALK + 110, HULL, n=4, phase=math.pi / 4)
spots["walkway_torches"] = [[x, WALK + 110, z] for x, z in WALK_TORCHES]

# ================================================================================================ C. the crab ledges
# shelf 1 at 260 (x -1650..-1150, z 100..500), a ramp down east (260 -> 160), shelf 2 at 160 (x -900..-700)
W3 = (-1650, 100, -1150, 500)
block(rock, *W3, FL, 260, ROCK, STONE, "s")
strip(rock, (-1150, 100), (-1430, 100), FL, FL, 260, 260, ROCK, (0, -1, 0))
strip(rock, (-1150, 250), (-1150, 100), FL, FL, 260, 260, ROCK, (1, 0, 0))
W4 = (-1150, 250, -900, 500)
block(rock, *W4, FL, 260, ROCK, STONE, "ns", y1b=160, along="x")
W5 = (-900, 100, -700, 550)
block(rock, *W5, FL, 160, ROCK, STONE, "nse")
strip(rock, (-900, 100), (-900, 250), FL, FL, 160, 160, ROCK, (-1, 0, 0))
strip(rock, (-900, 500), (-900, 550), FL, FL, 160, 160, ROCK, (-1, 0, 0))
# low rock rims along the open edges (60, no colliders: a fall lands in 30 of water)
# (where one rim butts against another's side, or a wall, it has no end face there: two faces in one plane flicker)
lip(rock, (-1430, 100), (-1172, 100), 260, 260, h=60, thick=22, caps=(True, False))
lip(rock, (-1150, 100), (-1150, 250), 260, 260, h=60, thick=22)
lip(rock, (-1150, 500), (-1650, 500), 260, 260, h=60, thick=22, caps=(False, False))
lip(rock, (-1150, 250), (-900, 250), 260, 160, h=60, thick=22)
lip(rock, (-900, 500), (-1150, 500), 160, 260, h=60, thick=22, caps=(True, False))
lip(rock, (-900, 100), (-700, 100), 160, 160, h=60, thick=22)
lip(rock, (-700, 122), (-700, 150), 160, 160, h=60, thick=22, caps=(False, True))
lip(rock, (-700, 350), (-700, 528), 160, 160, h=60, thick=22, caps=(True, False))
lip(rock, (-700, 550), (-900, 550), 160, 160, h=60, thick=22)
lip(rock, (-900, 250), (-900, 122), 160, 160, h=60, thick=22, caps=(True, False))
lip(rock, (-900, 528), (-900, 500), 160, 160, h=60, thick=22, caps=(False, True))
# the Tribal's alcove off shelf 1, in the west wall
tiled(rock, -1750, ALC_Z0, -1650, ALC_Z1, 260, STONE)
sides(rock, -1750, ALC_Z0, -1650, ALC_Z1, 260, 400, ROCK, "nsw", inward=True)
ceiling(rock, -1750, ALC_Z0, -1650, ALC_Z1, 400, CEIL)
spots["tribal_alcove"] = [-1705, 330]
# stalagmites: the crabs' cover (110 tall, about 90 across). Studio makes one hole per obstacle only when their
# boxes stay more than 20 apart (it merges nearer ones, in a chain) and clear of the region's edge: these are
# spaced for the region x -1615..-1195, z 135..465
CRAB_COVER = [(-1500, 220), (-1290, 215), (-1480, 380), (-1300, 385)]
for k, (x, z) in enumerate(CRAB_COVER):
    C.boulder(props, x, z, 260, 45, 112, 40 + k, ROCK, sides=6)
spots["crab_cover"] = CRAB_COVER
# the lookout's pillar across the water: a perch at 320 with a rim 30 high
PIL = (-910, -410, -790, -290)
block(rock, *PIL, FL, 320, ROCK, STONE, "nsew", size=None if False else 130.0)
rim(rock, *PIL, 320, 30, 12)
spots["pillar_perch"] = [-850, 320, -350]

# ================================================================================================ D. bridges and the island
deck(wood, -700, 150, -550, 350, 160, which="ns")
rails(wood, (-700, 152), (-550, 152), 160)
rails(wood, (-700, 348), (-550, 348), 160)
for (x, z) in ((-680, 160), (-570, 160), (-680, 340), (-570, 340)):
    post(wood, x, z, 10, FL, 148, HULL, n=6, cap=False)
ISL = (-550, -50, 50, 450)
block(rock, *ISL, FL, 160, ROCK, STONE, "nsew")
# the second bridge: planks at 160 to x 350, then a rock ramp down to the landing (160 -> 40)
deck(wood, 50, 230, 350, 430, 160, which="ns")
rails(wood, (50, 232), (350, 232), 160)
rails(wood, (50, 428), (350, 428), 160)
for (x, z) in ((70, 240), (200, 240), (330, 240), (70, 420), (200, 420), (330, 420)):
    post(wood, x, z, 10, FL, 148, HULL, n=6, cap=False)
RAMP2 = (350, 230, 600, 430)
block(rock, *RAMP2, FL, 160, ROCK, STONE, "nsw", y1b=40, along="x")
lip(rock, (350, 230), (600, 230), 160, 40, h=80, thick=20)
lip(rock, (600, 430), (350, 430), 40, 160, h=80, thick=20)
# the island's camp: cover for the squads, two tents on the north edge, the key's lookout stair in the north-east
ISLAND_COVER = [(-440, 165), (-120, 165), (-280, 255), (-440, 345), (-120, 345)]   # region x -525..15, z 75..430
for k, (x, z) in enumerate(ISLAND_COVER):
    C.boulder(props, x, z, 160, 42, 110, 60 + k, ROCK)
spots["island_cover"] = ISLAND_COVER


def tent(m, cx, z0, z1, y, half=55.0, ridge=105.0):
    """An A-frame tent open to the south: two canvas sides (seen from both sides), a back gable, two poles."""
    m.quad2([(cx - half, z0, y), (cx - half, z1, y), (cx, z1, y + ridge), (cx, z0, y + ridge)], CANVAS)
    m.quad2([(cx, z0, y + ridge), (cx, z1, y + ridge), (cx + half, z1, y), (cx + half, z0, y)], CANVAS)
    m.face([(cx - half, z0, y), (cx, z0, y + ridge), (cx + half, z0, y)], CANVAS, (0, 1, 0))
    m.face([(cx - half, z0 - 1.5, y), (cx + half, z0 - 1.5, y), (cx, z0 - 1.5, y + ridge)], CANVAS, (0, -1, 0))
    post(m, cx, z1 - 4, 4, y, y + ridge + 10, HULL, n=4)


tent(props, -470, -40, 55, 160)
tent(props, -330, -40, 55, 160)
spots["tents"] = [[-470, 160, 10], [-330, 160, 10]]
# the lookout stair: steps 195, 230, a platform at 260 (the key)
block(wood, -200, -40, -130, 60, 160, 195, HULL, PLANK, "nsw")
block(wood, -130, -40, -60, 60, 160, 230, HULL, PLANK, "ns")
sides(wood, -130, -40, -60, 60, 195, 230, HULL, "w")
block(wood, -60, -40, 40, 60, 160, 260, HULL, PLANK, "nse")
sides(wood, -60, -40, 40, 60, 230, 260, HULL, "w")
post(wood, 30, -30, 6, 260, 360, HULL, n=4)
spots["key"] = [-10, 260, 10]

# ================================================================================================ E. the east landing
LAND = (600, 230, 1550, 700)
tiled(rock, *LAND, 40, STONE)
strip(rock, (700, 230), (600, 230), FL, FL, 40, 40, ROCK, (0, -1, 0))
strip(rock, (1330, 230), (860, 230), FL, FL, 40, 40, ROCK, (0, -1, 0))
strip(rock, (600, 430), (600, 700), FL, FL, 40, 40, ROCK, (-1, 0, 0))
strip(rock, (600, 700), (1550, 700), FL, FL, 40, 40, ROCK, (0, 1, 0))
# the stair back up to the walkway (the loop) along the east wall: 40 -> 360
block(rock, 1330, -700, 1550, 230, FL, WALK, ROCK, STONE, "w", y1b=40, along="z")
fence(wood, (1342, 230), (1342, -712), 40, WALK)
# the jetty (a solid crib of planks) to the gangway, and the gangway up to the hull door (40 -> 55)
block(wood, 700, -370, 860, 230, FL, 40, HULL, DECK, "ne")
strip(wood, (700, -210), (700, 230), FL, FL, 40, 40, HULL, (-1, 0, 0))
block(wood, 500, -370, 700, -210, FL, 55, HULL, DECK, "ns", y1b=40, along="x")
for (x, z) in ((715, -355), (845, -355), (845, 0), (715, 0)):
    post(wood, x, z, 9, 40, 100, HULL, n=6)
# the smugglers' passage: a stub off the landing's east wall where 1.4's exit arrives (its way back at the end)
tiled(tun, 1550, STUB_Z0, 1750, STUB_Z1, 40, STONE)
sides(tun, 1550, STUB_Z0, 1750, STUB_Z1, 40, 280, CLIFF, "nse", inward=True)
ceiling(tun, 1550, STUB_Z0, 1750, STUB_Z1, 280, CEIL)
spots["landing_start_1_4"] = [1610, 40, 550]
spots["way_back_1_4_exit"] = [1720, 40, 550]

# ================================================================================================ F/G. the galleon
# wedged against the north wall under the crack: hull x 100..500 from the wall (z -700) to z -200, its bow out to
# z -30; the hull's top slopes 300 (stern) -> 340 (bow): tilted. Its hold (open to the roof, the deck long gone):
# a well at 20 by the stern, a slope up to 55 at the hull door; the captain's cabin under the stern castle
HX0, HX1, HXI0, HXI1 = 100.0, 500.0, 130.0, 470.0
HZ0, HZB, HZBOW = -700.0, -200.0, -30.0


def htop(z):
    return 300 + 40 * (min(z, HZB) - HZ0) / (HZB - HZ0)


def hfloor(z):
    if z < -520:
        return 20.0
    if z < -380:
        return 20 + 35 * (z + 520) / 140
    return 55.0


BR_Z0, BR_Z1, BR_Y1 = -620.0, -520.0, 200.0     # the breach in the stern's west side, to the yard
HD_Z0, HD_Z1, HD_Y0, HD_Y1 = -370.0, -210.0, 55.0, 235.0   # the hull door (east side), 160 x 180
CAB_Z = -620.0                                  # the cabin's bulkhead


def hull_side(x, facing, bottom, z0, z1, hole):
    """A side of the hull from bottom(z) to its top, with one opening (z0, z1, y0, y1)."""
    hz0, hz1, hy0, hy1 = hole
    pts = sorted({z0, z1, hz0, hz1} | {z for z in cuts(z0, z1, 160)})
    for a, b in zip(pts, pts[1:]):
        if hz0 <= a and b <= hz1:
            strip(wood, (x, a), (x, b), bottom(a), bottom(b), hy0, hy0, HULL, facing)
            strip(wood, (x, a), (x, b), hy1, hy1, htop(a), htop(b), HULL, facing)
        else:
            strip(wood, (x, a), (x, b), bottom(a), bottom(b), htop(a), htop(b), HULL, facing)


hull_side(HX0, (-1, 0, 0), lambda z: FL, HZ0, HZB, (BR_Z0, BR_Z1, 20.0, BR_Y1))
hull_side(HX1, (1, 0, 0), lambda z: FL, HZ0, HZB, (HD_Z0, HD_Z1, HD_Y0, HD_Y1))
hull_side(HXI0, (1, 0, 0), hfloor, CAB_Z, HZB, (BR_Z0, BR_Z1, 20.0, BR_Y1))
hull_side(HXI1, (-1, 0, 0), hfloor, CAB_Z, HZB, (HD_Z0, HD_Z1, HD_Y0, HD_Y1))
# the hull walls' tops (30 thick) and the stern castle over the cabin
for (xa, xb) in ((HX0, HXI0), (HXI1, HX1)):
    for a, b in zip(cuts(CAB_Z, HZB, 130), cuts(CAB_Z, HZB, 130)[1:]):
        wood.face([(xa, a, htop(a)), (xb, a, htop(a)), (xb, b, htop(b)), (xa, b, htop(b))], HULL, (0, 0, 1))
for xa, xb in zip(cuts(HX0, HX1, 140), cuts(HX0, HX1, 140)[1:]):
    wood.face([(xa, HZ0, htop(HZ0)), (xb, HZ0, htop(HZ0)), (xb, CAB_Z, htop(CAB_Z)), (xa, CAB_Z, htop(CAB_Z))],
              DECK, (0, 0, 1))
# the reveals: the breach's floor, sides and lintel; the door's sill, sides and lintel
tiled(wood, HX0, BR_Z0, HXI0, BR_Z1, 20, DECK)
wood.face([(HX0, BR_Z0, 20), (HXI0, BR_Z0, 20), (HXI0, BR_Z0, BR_Y1), (HX0, BR_Z0, BR_Y1)], HULL, (0, 1, 0))
wood.face([(HX0, BR_Z1, 20), (HXI0, BR_Z1, 20), (HXI0, BR_Z1, BR_Y1), (HX0, BR_Z1, BR_Y1)], HULL, (0, -1, 0))
wood.face([(HX0, BR_Z0, BR_Y1), (HXI0, BR_Z0, BR_Y1), (HXI0, BR_Z1, BR_Y1), (HX0, BR_Z1, BR_Y1)], HULL, (0, 0, -1))
tiled(wood, HXI1, HD_Z0, HX1, HD_Z1, HD_Y0, DECK)
wood.face([(HXI1, HD_Z0, HD_Y0), (HX1, HD_Z0, HD_Y0), (HX1, HD_Z0, HD_Y1), (HXI1, HD_Z0, HD_Y1)], HULL, (0, 1, 0))
wood.face([(HXI1, HD_Z1, HD_Y0), (HX1, HD_Z1, HD_Y0), (HX1, HD_Z1, HD_Y1), (HXI1, HD_Z1, HD_Y1)], HULL, (0, -1, 0))
wood.face([(HXI1, HD_Z0, HD_Y1), (HX1, HD_Z0, HD_Y1), (HX1, HD_Z1, HD_Y1), (HXI1, HD_Z1, HD_Y1)], HULL, (0, 0, -1))
# the hold's floor
tiled(wood, HXI0, CAB_Z, HXI1, -520, 20, DECK)
tiled(wood, HXI0, -520, HXI1, -380, 20, DECK, 55, along="z")
tiled(wood, HXI0, -380, HXI1, HZB, 55, DECK)
# the bulkheads: the cabin's (z -620, a doorway 100 x 180) and the forecastle's (z -200)
CD_X0, CD_X1, CD_Y1 = 250.0, 350.0, 180.0
plane_rect(wood, "z", CAB_Z, HXI0, 20, HXI1, htop(CAB_Z), [(CD_X0, 20, CD_X1, CD_Y1)], HULL, (0, 1, 0))
plane_rect(wood, "z", CAB_Z - 2, HXI0, 20, HXI1, 240, [(CD_X0, 20, CD_X1, CD_Y1)], HULL, (0, -1, 0))
plane_rect(wood, "z", HZB, HXI0, 55, HXI1, 340, [], HULL, (0, -1, 0))
# the captain's cabin: floor, its sides, a low ceiling (the north wall is the cavern's)
tiled(wood, HXI0, HZ0, HXI1, CAB_Z - 2, 20, DECK)
strip(wood, (HXI0, HZ0), (HXI0, CAB_Z - 2), 20, 20, 240, 240, HULL, (1, 0, 0))
strip(wood, (HXI1, CAB_Z - 2), (HXI1, HZ0), 20, 20, 240, 240, HULL, (-1, 0, 0))
ceiling(wood, HXI0, HZ0, HXI1, CAB_Z - 2, 240, HULL)
spots["cabin"] = [300, 20, -665]
# the bow: two raked sides to the stem, and the forecastle deck at 340 (the winch); inside it, the water meets a
# wall at the hull's end (z -200)
strip(wood, (HX0, HZB), (HX1, HZB), FL, FL, 55, 55, HULL, (0, 1, 0))
STEM = (300.0, HZBOW)
for (a, b) in (((HX0, HZB), STEM), (STEM, (HX1, HZB))):
    mx, mz = (a[0] + b[0]) / 2 - 300, (a[1] + b[1]) / 2 - (HZB + 60)
    strip(wood, a, b, FL, FL, 340, 340, HULL, (mx, mz, 0), step=130)
mid_w, mid_e, tipc = (200.0, (HZB + HZBOW) / 2), (400.0, (HZB + HZBOW) / 2), (300.0, HZB)
for tri in (((HX0, HZB), tipc, mid_w), (tipc, (HX1, HZB), mid_e), (tipc, mid_e, STEM), (tipc, STEM, mid_w)):
    wood.face([(p[0], p[1], 340) for p in tri], DECK, (0, 0, 1))
# the winch on the forecastle: a drum between two cheeks (the switch beside it)
wood.box(260, -150, 275, -110, 340, 390, HULL)
wood.box(325, -150, 340, -110, 340, 390, HULL)
post(wood, 300, -130, 18, 350, 380, HULL, n=6)
spots["winch_switch"] = [300, 340, -95]
# its wales (two bands round the sides, 2 off the planks), a bowsprit, the fore mast's stump
for y in (140.0, 240.0):
    for (za, zb) in ((HZ0, BR_Z0), (BR_Z1, HZB)) if y < BR_Y1 else ((HZ0, HZB),):
        lip(wood, (HX0 - 2, za), (HX0 - 2, zb), y, y, h=14, thick=6, mat_=DECK, under=True, caps=(za != HZ0, True))
    for (za, zb) in ((HZB, HD_Z1), (HD_Z0, HZ0)) if HD_Y0 < y < HD_Y1 else ((HZB, HZ0),):
        lip(wood, (HX1 + 2, za), (HX1 + 2, zb), y, y, h=14, thick=6, mat_=DECK, under=True,
            caps=(True, zb != HZ0))


def spar(m, p, q, r, mat_):
    """A square beam from p to q ((x, z, y)), r thick."""
    d = [q[i] - p[i] for i in range(3)]
    L = math.sqrt(sum(v * v for v in d))
    d = [v / L for v in d]
    up = (0.0, 0.0, 1.0) if abs(d[2]) < 0.9 else (1.0, 0.0, 0.0)
    s1 = (d[1] * up[2] - d[2] * up[1], d[2] * up[0] - d[0] * up[2], d[0] * up[1] - d[1] * up[0])
    n1 = math.sqrt(sum(v * v for v in s1))
    s1 = [v / n1 * r for v in s1]
    s2 = (d[1] * s1[2] - d[2] * s1[1], d[2] * s1[0] - d[0] * s1[2], d[0] * s1[1] - d[1] * s1[0])
    ring = [(s1[i] + s2[i] for i in range(3)), (s1[i] - s2[i] for i in range(3)), (-s1[i] - s2[i] for i in range(3)),
            (-s1[i] + s2[i] for i in range(3))]
    ring = [tuple(v) for v in ring]
    for k in range(4):
        a, b = ring[k], ring[(k + 1) % 4]
        out = [(a[i] + b[i]) / 2 for i in range(3)]
        m.face([tuple(p[i] + a[i] for i in range(3)), tuple(p[i] + b[i] for i in range(3)),
                tuple(q[i] + b[i] for i in range(3)), tuple(q[i] + a[i] for i in range(3))], mat_, tuple(out))
    m.face([tuple(q[i] + c[i] for i in range(3)) for c in ring], mat_, tuple(d))


spar(wood, (300, -60, 300), (300, 140, 430), 12, HULL)        # the bowsprit, out over the water
post(wood, 300, -80, 16, 340, 520, HULL, n=6)                   # the fore mast, broken off
spar(wood, (300, -80, 470), (360, -150, 600), 9, HULL)          # a splintered spar leaning off it
# the mast, broken off at its crow's nest (480): the lookout's perch, a rim 20 high
MAST = (400.0, -590.0)   # its nest (z -650..-530) clear of the hold squad's region (from z -525)
post(wood, MAST[0], MAST[1], 20, 20, 460, HULL, n=6, cap=False)
NEST = (MAST[0] - 60, MAST[1] - 60, MAST[0] + 60, MAST[1] + 60)
tiled(wood, *NEST, 480, DECK)
tiled(wood, *NEST, 462, DECK, facing=(0, 0, -1))
sides(wood, *NEST, 462, 480, HULL, "nsew")
rim(wood, *NEST, 480, 20, 10, HULL)   # 20: the lookout fires down at the landing over it (raycast)
spots["nest"] = [MAST[0], 480, MAST[1]]
# cargo in the hold: the squad's cover (80 across, 100 over the floor)
HOLD_COVER = [(220, -455), (380, -455), (220, -280), (380, -280)]  # region x 145..455, z -525..-202; one each
for (x, z) in HOLD_COVER:
    lo, hi = min(hfloor(z - 35), hfloor(z + 35)), max(hfloor(z - 35), hfloor(z + 35))
    wood.box(x - 35, z - 35, x + 35, z + 35, lo - 5, hi + 100, HULL)
spots["hold_cover"] = HOLD_COVER

# ================================================================================================ the yard and its grille
YARD = (-400, -700, 100, -470)
tiled(rock, *YARD, 20, STONE)
sides(rock, *YARD, FL, 20, ROCK, "sw")
GX, GZ = -392.0, -478.0   # the grille's lines, 8 in from the yard's edges
for x in cuts(GX, 92, 55):
    post(props, x, GZ, 7, 20, 458, IRON, n=4, phase=math.pi / 4)
for z in cuts(-700, GZ, 55)[:-1]:
    post(props, GX, z, 7, 20, 458, IRON, n=4, phase=math.pi / 4)
for y0 in (210, 436):   # two bars across the posts, 8 thick
    lip(props, (92, GZ + 4), (GX, GZ + 4), y0, y0, h=14, thick=8, mat_=IRON, seg=125, under=True)
    lip(props, (GX - 4, GZ - 6), (GX - 4, -697), y0, y0, h=14, thick=8, mat_=IRON, seg=115, under=True)
collider(edges, (-400, GZ), (100, GZ), 20, 460)
collider(edges, (GX, -700), (GX, -470), 20, 460)
spots["vault_door"] = [-150, 20, -720]
spots["yard_torches"] = [[-262, 20, -690], [-38, 20, -690]]
for x in (-262, -38):
    post(props, x, -690, 7, 20, 150, HULL, n=4)

# ================================================================================================ H. the vault
# its passage north from the door (20) down to the vault (-100), 200 wide; the vault 700 x 450, 400 high
PX0, PX1, PZ0, PZ1 = -250.0, -50.0, -1000.0, -700.0
PR, PL = -740.0, -770.0   # the doorway: a reveal 160 wide, 40 deep (z -740..-700), the door stands in it; level to -770
tiled(vault, DOOR_X0, PR, DOOR_X1, PZ1, 20, PAVE)
tiled(vault, PX0, PL, PX1, PR, 20, PAVE)
tiled(vault, PX0, PZ0, PX1, PL, -100, PAVE, 20, along="z")


def pfloor(x, z):
    return 20.0 if z > PL else -100 + 120 * (z - PZ0) / (PL - PZ0)


sides(vault, PX0, PZ0, PX1, PR, lambda x, z: pfloor(x, z), 270, MASON, "ew", inward=True)
ceiling(vault, PX0, PZ0, PX1, PR, 270, MASON)
plane_rect(vault, "z", PR, PX0, 20, PX1, 270, [(DOOR_X0, 20, DOOR_X1, DOOR_H)], MASON, (0, -1, 0))
strip(vault, (DOOR_X0, PR), (DOOR_X0, PZ1), 20, 20, DOOR_H, DOOR_H, MASON, (1, 0, 0))
strip(vault, (DOOR_X1, PZ1), (DOOR_X1, PR), 20, 20, DOOR_H, DOOR_H, MASON, (-1, 0, 0))
ceiling(vault, DOOR_X0, PR, DOOR_X1, PZ1, DOOR_H, MASON)
VX0, VX1, VZ0, VZ1, VY, VTOP = -500.0, 200.0, -1450.0, -1000.0, -100.0, 300.0
tiled(vault, VX0, VZ0, VX1, VZ1, VY, PAVE)
ceiling(vault, VX0, VZ0, VX1, VZ1, VTOP, MASON)
plane_rect(vault, "z", VZ1, VX0, VY, VX1, VTOP, [(PX0, VY, PX1, 270)], MASON, (0, -1, 0))
plane_rect(vault, "z", VZ0, VX0, VY, VX1, VTOP, [], MASON, (0, 1, 0))
SD_Z0, SD_Z1 = -1400.0, -1150.0   # the sea door's tunnel in the west wall
plane_rect(vault, "x", VX0, VZ0, VY, VZ1, VTOP, [(SD_Z0, VY, SD_Z1, VY + 300)], MASON, (1, 0, 0))
# three cells in the east wall behind square windows (100 x 100, sills 30 over the floor): Tribals 4-6
CELLS = [(-1415, -1315), (-1275, -1175), (-1135, -1035)]
SILL = VY + 30
plane_rect(vault, "x", VX1, VZ0, VY, VZ1, VTOP, [(a, SILL, b, SILL + 100) for a, b in CELLS], MASON, (-1, 0, 0))
for (a, b) in CELLS:
    c0, c1 = a - 5, b + 5
    tiled(vault, VX1 + 2, c0, VX1 + 130, c1, VY, PAVE)
    sides(vault, VX1 + 2, c0, VX1 + 130, c1, VY, 60, MASON, "nse", inward=True)
    ceiling(vault, VX1 + 2, c0, VX1 + 130, c1, 60, MASON)
    plane_rect(vault, "x", VX1 + 2, c0, VY, c1, 60, [(a, SILL, b, SILL + 100)], MASON, (1, 0, 0))
    # the sill's top (2 thick) between the two faces
    vault.face([(VX1, a, SILL), (VX1, b, SILL), (VX1 + 2, b, SILL), (VX1 + 2, a, SILL)], MASON, (0, 0, 1))
spots["cells"] = [[VX1 + 70, (a + b) / 2] for a, b in CELLS]
spots["glass"] = [[[VX1, a], [VX1, b], SILL] for a, b in CELLS]
# the hoard: five piles of gold (cover for the vault's squad), a few small heaps by the walls
VAULT_COVER = [(-330, -1345), (-10, -1345), (-170, -1230), (-330, -1110), (-10, -1110)]  # region x -420..175
for k, (x, z) in enumerate(VAULT_COVER):
    C.boulder(props, x, z, VY, 45, 105, 80 + k, COINS)
for k, (x, z, r, h) in enumerate(((-455, -1430, 38, 55), (-30, -1435, 32, 45), (175, -1440, 25, 40))):
    C.boulder(props, x, z, VY, r, h, 90 + k, COINS, sides=6)
spots["vault_cover"] = VAULT_COVER
# the trade chart on a table by the sea door
TB = (-490, -1110, -440, -1040)
props.box(TB[0], TB[1], TB[2], TB[3], VY, -40, HULL)
props.face([(TB[0] + 6, TB[3] - 6, -38), (TB[2] - 6, TB[3] - 6, -38), (TB[2] - 6, TB[1] + 6, -38),
            (TB[0] + 6, TB[1] + 6, -38)], CHART, (0, 0, 1), [(0, 0), (1, 0), (1, 1), (0, 1)])
spots["chart"] = [-465, -40, -1075]
spots["chest"] = [-150, VY, -1405]

# ================================================================================================ I. the sea door
# a tunnel west from the vault (-100) rising to 0, 250 wide; at its end the cove at dawn (the exit)
SX0, SX1 = -900.0, VX0


SXL = -780.0   # level at the far end (the exit), then down to the vault


def sfloor(x, z):
    return 0.0 if x < SXL else -100 * (x - SXL) / (SX1 - SXL)


tiled(vault, SX0, SD_Z0, SXL, SD_Z1, 0, CLIFF)
tiled(vault, SXL, SD_Z0, SX1, SD_Z1, 0, CLIFF, -100, along="x")
for (xa, xb) in ((SX0, SXL), (SXL, SX1)):   # split at the kink, so the walls meet the ceiling
    sides(vault, xa, SD_Z0, xb, SD_Z1, lambda x, z: sfloor(x, z), lambda x, z: sfloor(x, z) + 300, CLIFF, "ns",
          inward=True)
ceiling(vault, SX0, SD_Z0, SXL, SD_Z1, 300, CLIFF)
ceiling(vault, SXL, SD_Z0, SX1, SD_Z1, 300, CLIFF, 200, along="x")
plane_rect(vault, "x", SX0, SD_Z0, 0, SD_Z1, 300, [], CLIFF, (1, 0, 0))
vault.face([(SX0 + 2, SD_Z1 - 30, 10), (SX0 + 2, SD_Z0 + 30, 10), (SX0 + 2, SD_Z0 + 30, 250),
            (SX0 + 2, SD_Z1 - 30, 250)], DAWN, (1, 0, 0), [(0, 0), (1, 0), (1, 1), (0, 1)])
spots["sea_door_exit"] = [SX0 + 40, 0, (SD_Z0 + SD_Z1) / 2]

# ================================================================================================ the lagoon
HOLES = [W1, (-1650, -200, -1430, 100), W3, W4, W5, ISL, PIL, RAMP2, LAND, (1330, -700, 1550, 230),
         (700, -370, 860, 230), (500, -370, 700, -210), YARD, (HX0, HZ0, HX1, HZB)]
# zero-width cuts where the water's texture repeats (every 512): it doesn't tile, and the importer would cut
# pieces across a repeat (T-junctions)
for v in range(-1536, 1537, 512):
    HOLES.append((v, -700, v, 900))
for v in (-512, 0, 512):
    HOLES.append((-1650, v, 1550, v))
C.water_box(lag, (-1650, -700, 1550, 900), HOLES, FL, WL, MUD, WATER, wm=wtr)

# ------------------------------------------------------------------------------------------------ boundary colliders
for (a, b) in (((-1765, -1505), (1765, -1505)), ((1765, -1505), (1765, 910)), ((1765, 910), (-1765, 910)),
               ((-1765, 910), (-1765, -1505))):
    collider(edges, a, b, -200, 1600)

for m in (cave, rock, wood, lag, vault, tun, props, edges, wtr, falls):
    m.build()

# ------------------------------------------------------------------------------------------------ light: a moon shaft
level = [o for o in coll.all_objects if o.type == "MESH"]
SUN_DIR = (0.06, -0.04, -1.0)    # the moon straight over the crack (Blender space: the light's travel)
WARM = (0.55, 0.32, 0.1)
LAMPS = [
    (TUN_X0 + 12, -1300, 520, 300, WARM), (TUN_X1 - 12, -1050, 505, 300, WARM),
    *[(x, z, WALK + 120, 330, WARM) for (x, z) in WALK_TORCHES],
    (-1600, 150, 330, 300, WARM),                    # shelf 1's lantern
    (-850, -350, 380, 280, (0.6, 0.36, 0.12)),       # the pillar lookout's lantern
    (-400, 20, 230, 320, WARM), (-10, 40, 320, 260, WARM),     # the camp, the key tower
    (800, -380, 110, 300, WARM), (1000, 650, 120, 340, WARM), (1480, 300, 120, 320, WARM),   # jetty, landing
    (300, -250, 140, 260, (0.5, 0.3, 0.1)), (300, -660, 120, 200, (0.5, 0.3, 0.1)),        # the hold, the cabin
    (MAST[0], MAST[1], 520, 240, (0.6, 0.36, 0.12)),                                        # the nest's lantern
    (-262, -690, 170, 260, (0.6, 0.34, 0.1)), (-38, -690, 170, 260, (0.6, 0.34, 0.1)),     # the vault door
    (-450, -1420, 60, 320, WARM), (150, -1420, 60, 320, WARM), (-150, -1030, 60, 300, WARM),   # the vault
    (SX0 + 60, (SD_Z0 + SD_Z1) / 2, 120, 380, (0.7, 0.42, 0.35)),                          # dawn at the sea door
    (1690, 550, 160, 220, (0.15, 0.3, 0.15)),                                               # the smugglers' passage
    (980, -750, 260, 200, (0.15, 0.3, 0.32)),                                               # the ledge
]


def extra(x, z, y, mname):
    if REC_X0 - 1 <= x <= REC_X1 + 1 and z < TZ0 + 1:          # the way back: darkness
        return (0.35, 0.35, 0.4)
    return (1.0, 1.0, 1.0)


C.bake(level, SUN_DIR, (0.55, 0.7, 0.85), (0.13, 0.21, 0.27), lamps=LAMPS, extra=extra, shadow=0.0,
       ao_strength=0.4)


# the lagoon glows faintly teal; brighter under the moon shaft and by the torches; the falls pale
def under_crack(x, z):
    return any(cx - 30 <= x <= cx + 230 and cz - 30 <= z <= cz + 230 for (cx, cz) in CRACK)


for o in level:
    if o.name not in ("lagoon_water", "waterfall"):
        continue
    m = o.data
    attr = m.color_attributes["Col"]
    for p in m.polygons:
        for li in p.loop_indices:
            co = o.matrix_world @ m.vertices[m.loops[li].vertex_index].co
            gx, gz, gy = co.x, -co.y, co.z
            c = [0.07, 0.24, 0.26]
            if o.name == "waterfall":
                c = [0.3, 0.5, 0.55]
            if under_crack(gx, gz):
                c = [c[0] + 0.18, c[1] + 0.24, c[2] + 0.28]
            for (lx, lz, ly, r, lc) in LAMPS:
                d = math.sqrt((gx - lx) ** 2 + (gz - lz) ** 2 + (gy - ly) ** 2)
                if d < r * 1.3:
                    k = (1 - d / (r * 1.3)) ** 2 * 0.6
                    c = [c[i] + lc[i] * k for i in range(3)]
            attr.data[li].color = (*[min(1.0, v) for v in c], 1.0)
    m.update()

# ------------------------------------------------------------------------------------------------ export
os.makedirs(C.OUT, exist_ok=True)
report = jfg64.budgets(level)
out = jfg64.export(os.path.join(C.OUT, NAME + ".glb"), collection=coll)
spots["budgets"] = report
spots["export"] = {k: v for k, v in out.items() if k != "objects"} if isinstance(out, dict) else str(out)


def tup(v):
    if isinstance(v, (tuple, list)) and v and isinstance(v[0], (int, float)):
        return [round(c, 1) for c in v]
    if isinstance(v, list):
        return [tup(x) for x in v]
    return v


with open(os.path.join(C.OUT, NAME + "_spots.json"), "w", encoding="utf-8") as f:
    json.dump({k: tup(v) for k, v in spots.items()}, f, indent=1, default=str)
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(C.OUT, NAME + ".blend"))
print("BLACKWATER", json.dumps(report, default=str))
print("PARTS", json.dumps({o.name: sum(len(p.vertices) - 2 for p in o.data.polygons) for o in level}))
