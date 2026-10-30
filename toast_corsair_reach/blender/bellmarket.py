"""Drowned Bellmarket (Corsair Reach 2.2): builds the level from nothing and exports blender/out/bellmarket.glb.

Run in Blender 5.2 with jfg64 0.6.0+, after JFG-Studio has built its catalog once (the game's textures):
    blender --background --factory-startup --addons jfg64 --python bellmarket.py
Then in JFG-Studio: reimport_geometry (or import the .glb) into the level `bellmarket`.

Game coordinates throughout (x east, z south, y up); levels/2.2_bellmarket.md has the plan. Mirefall's hub, a town
under the storm: the market square is a flooded basin (cobbles at -25, water 20 deep) with the fountain court
standing out of it; a loop of streets at 0 round it (the west street, the north lane, the east street, the south
street); the gate arcade (60) on the south, where 2.1's passage comes in; the bell tower (north-west), climbed inside
on ramps between half-floors (0 / 180 / 360 / 540) to the bell chamber at 700, and from its east door the rooftop
shortcut (520 -> 340 -> 180 -> a stair) down by the causeway; the causeway gates (north), two doors in a walled
passage; the cistern's arch (east) under a blue lamp. Every floor is on the 100 grid; houses are solid blocks.
"""
import json
import math
import os
import random
import sys

import bpy

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import common as C  # noqa: E402
from common import Mesh, block, tiled, post  # noqa: E402
import jfg64  # noqa: E402

NAME = "bellmarket"
scene, coll = C.new_scene(NAME)
spots = {}
rnd = random.Random(2202)

BED_Y, WATER_Y = -25.0, -5.0     # the square's cobbles under the flood, and the water's surface (20 deep)
ARC_Y = 60.0                     # the gate arcade
BASIN = (-700, -300, 700, 900)   # the flooded square (x0, z0, x1, z1)


# ------------------------------------------------------------------------------------------------ our own images
def window_px(x, y):
    """A lit window: four warm panes in a dark frame (as 2.1's)."""
    if x in (0, 15) or y in (0, 15) or x in (7, 8) or y in (7, 8):
        return (0.16, 0.11, 0.07)
    k = 1.0 - 0.25 * (y / 15.0)
    return (1.0 * k, 0.78 * k, 0.38 * k)


def blue_px(x, y):
    """The cistern's lamp: cold blue panes in an iron frame, brightest in the middle."""
    if x in (0, 15) or y in (0, 15) or x == 8:
        return (0.08, 0.1, 0.14)
    d = math.hypot(x - 7.5, y - 7.5) / 8.0
    k = 1.0 - 0.45 * d
    return (0.35 * k, 0.7 * k, 1.0 * k)


def awning_px(x, y):
    """Market canvas: bottle-green and cream stripes, darker at the scalloped hem."""
    stripe = (x // 4) % 2
    col = (0.18, 0.42, 0.3) if stripe else (0.88, 0.84, 0.7)
    if y > 12 and (x % 4 in (0, 3)):
        col = tuple(c * 0.6 for c in col)
    k = 0.9 + 0.1 * math.sin(y * 0.9)
    return tuple(c * k for c in col)


def sign_px(x, y):
    """The market's sign: a pale bell on a deep blue board, a pale rim."""
    if x in (0, 31) or y in (0, 31):
        return (0.82, 0.78, 0.62)
    if x in (1, 30) or y in (1, 30):
        return (0.12, 0.12, 0.16)
    bell = (0.92, 0.82, 0.5)
    if 13 <= x <= 18 and 5 <= y <= 7:
        return bell  # the crown
    if 8 <= y <= 22 and abs(x - 15.5) <= 3 + (y - 8) * 0.35:
        return bell
    if 22 < y <= 24 and 6 <= x <= 25:
        return bell  # the lip
    if 25 <= y <= 27 and 14 <= x <= 17:
        return bell  # the clapper
    return (0.1, 0.18, 0.36)


# ------------------------------------------------------------------------------------------------ materials
MATS, M = [], {}


def mat(name, material):
    M[name] = len(MATS)
    MATS.append(material)
    return M[name]


COBBLE = mat("cobble", C.game(0x0AC0))     # the streets' cobbles
COURT = mat("court", C.game(0x0BEB))       # the fountain court's paving, the arcade's floor
BED = mat("bed", C.game(0x1958))           # mossy cobbles under the flood
ASHLAR = mat("ashlar", C.game(0x0828))     # the fountain, the basin's rim, the causeway's walls, the cistern
TOWER = mat("tower", C.game(0x16DF))       # the bell tower's stone, cover blocks
PLASTER = mat("plaster", C.game(0x0715))   # house walls
BRICK = mat("brick", C.game(0x1946))       # house walls, the arcade
TIMBER = mat("timber", C.game(0x0A26))     # timbered house walls, stall counters
DECK = mat("deck", C.game(0x16D9))         # the tower's floors and ramps
DARK = mat("dark", C.game(0x16DB))         # beams, posts, the bell (darkened)
SLATE = mat("slate", C.game(0x0CAF))       # roofs, the flat roofs' tops
SHINGLE = mat("shingle", C.game(0x0BE9))   # some roofs
WATER = mat("water", C.game(0x0DED, "water"))
WINDOW = mat("window", C.own_material("lit_window", C.own_image("lit_window", 16, 16, window_px)))
BLUE = mat("blue", C.own_material("cistern_lamp", C.own_image("cistern_lamp", 16, 16, blue_px)))
AWNING = mat("awning", C.own_material("market_awning", C.own_image("market_awning", 16, 16, awning_px)))
SIGN = mat("sign", C.own_material("bell_sign", C.own_image("bell_sign", 32, 32, sign_px)))
EDGE = jfg64.boundary_material()


def mesh(name, uv=200.0):
    return Mesh(name, MATS, coll, uv_size=uv)


edges = Mesh("colliders", [EDGE], coll)
wtr = Mesh("square_water", MATS, coll, uv_size=1000.0)  # its texture doesn't repeat: cut at 1000s


def inside(rs, x, z):
    return any(r[0] < x < r[2] and r[1] < z < r[3] for r in rs)


def ground(m, rects, y, top, holes=(), grid=100.0):
    """Floor at y over the union of rects minus holes, on one grid (every 100 plus every edge), each row's cells
    joined in pairs (pieces of 200 x 100 at most): no long thin triangles, no T-junctions inside a row."""
    allr = list(rects) + list(holes)
    lo_x, hi_x = min(r[0] for r in rects), max(r[2] for r in rects)
    lo_z, hi_z = min(r[1] for r in rects), max(r[3] for r in rects)
    xs = sorted({v for r in allr for v in (r[0], r[2]) if lo_x <= v <= hi_x} |
                {grid * k for k in range(int(lo_x // grid), int(hi_x // grid) + 2) if lo_x <= grid * k <= hi_x})
    zs = sorted({v for r in allr for v in (r[1], r[3]) if lo_z <= v <= hi_z} |
                {grid * k for k in range(int(lo_z // grid), int(hi_z // grid) + 2) if lo_z <= grid * k <= hi_z})
    n = 0
    for j in range(len(zs) - 1):
        cz = (zs[j] + zs[j + 1]) / 2
        i = 0
        while i < len(xs) - 1:
            cx = (xs[i] + xs[i + 1]) / 2
            if inside(rects, cx, cz) and not inside(holes, cx, cz):
                k = i + 1
                if k < len(xs) - 1 and xs[k + 1] - xs[i] <= 2 * grid + 1:
                    cx2 = (xs[k] + xs[k + 1]) / 2
                    if inside(rects, cx2, cz) and not inside(holes, cx2, cz):
                        k += 1
                m.face([(xs[i], zs[j], y), (xs[k], zs[j], y), (xs[k], zs[j + 1], y), (xs[i], zs[j + 1], y)], top,
                       (0, 0, 1))
                n += 1
                i = k
            else:
                i += 1
    return n


def gable(m, x0, z0, x1, z1, eave, ridge, wall, roof, along="x", over=25.0, ends=(True, True)):
    """A gable roof over x0..x1, z0..z1 (eaves `over` out), its ridge along `along`; the end walls' triangles
    (ends: (west, east) or (north, south); left out against a taller neighbour's wall: two faces in one plane)."""
    if along == "x":
        zm = (z0 + z1) / 2
        a, b = x0 - over, x1 + over
        m.face([(a, z0 - over, eave - 10), (b, z0 - over, eave - 10), (b, zm, ridge), (a, zm, ridge)], roof, (0, -1, 1))
        m.face([(b, z1 + over, eave - 10), (a, z1 + over, eave - 10), (a, zm, ridge), (b, zm, ridge)], roof, (0, 1, 1))
        if ends[0]:
            m.face([(x0, z1, eave), (x0, z0, eave), (x0, zm, ridge)], wall, (-1, 0, 0))
        if ends[1]:
            m.face([(x1, z0, eave), (x1, z1, eave), (x1, zm, ridge)], wall, (1, 0, 0))
    else:
        xm = (x0 + x1) / 2
        a, b = z0 - over, z1 + over
        m.face([(x0 - over, b, eave - 10), (x0 - over, a, eave - 10), (xm, a, ridge), (xm, b, ridge)], roof, (-1, 0, 1))
        m.face([(x1 + over, a, eave - 10), (x1 + over, b, eave - 10), (xm, b, ridge), (xm, a, ridge)], roof, (1, 0, 1))
        if ends[0]:
            m.face([(x0, z0, eave), (x1, z0, eave), (xm, z0, ridge)], wall, (0, -1, 0))
        if ends[1]:
            m.face([(x1, z1, eave), (x0, z1, eave), (xm, z1, ridge)], wall, (0, 1, 0))


def window(m, plane, c, u, v, out, w=44.0, h=60.0, mat_=None):
    """A lit window picture on a wall in plane x = c or z = c, 4 out from it (towards `out`, +1 or -1)."""
    mt = WINDOW if mat_ is None else mat_
    if plane == "z":
        zz = c + 4 * out  # the decal's back 2 behind it: clear of the wall
        C.decal(m, [(u - w / 2, zz, v), (u + w / 2, zz, v), (u + w / 2, zz, v + h), (u - w / 2, zz, v + h)], mt)
    else:
        xx = c + 4 * out
        C.decal(m, [(xx, u - w / 2, v), (xx, u + w / 2, v), (xx, u + w / 2, v + h), (xx, u - w / 2, v + h)], mt)


def lantern(m, x, z, y, h=170.0, lamp=None):
    """A lantern post: a dark post and a lit box on top (the bake's lamp list warms round it)."""
    post(m, x, z, 6, y, y + h, DARK, n=4, phase=math.pi / 4)
    m.box(x - 13, z - 13, x + 13, z + 13, y + h, y + h + 30, WINDOW if lamp is None else lamp, DARK)
    m.box(x - 17, z - 17, x + 17, z + 17, y + h + 30, y + h + 38, DARK)


def jambs(m, plane, c0, c1, u0, v0, u1, v1, mt, sill=True):
    """The reveal of an opening u0..u1 x v0..v1 through a wall between planes c0 and c1 (plane "x": x = c, u is z;
    "z": z = c, u is x): its two sides, its lintel's underside and (sill) its sill."""
    a, b = min(c0, c1), max(c0, c1)
    if plane == "z":
        m.face([(u0, a, v0), (u0, b, v0), (u0, b, v1), (u0, a, v1)], mt, (1, 0, 0))
        m.face([(u1, a, v0), (u1, b, v0), (u1, b, v1), (u1, a, v1)], mt, (-1, 0, 0))
        m.face([(u0, a, v1), (u1, a, v1), (u1, b, v1), (u0, b, v1)], mt, (0, 0, -1))
        if sill:
            m.face([(u0, a, v0), (u1, a, v0), (u1, b, v0), (u0, b, v0)], mt, (0, 0, 1))
    else:
        m.face([(a, u0, v0), (b, u0, v0), (b, u0, v1), (a, u0, v1)], mt, (0, 1, 0))
        m.face([(a, u1, v0), (b, u1, v0), (b, u1, v1), (a, u1, v1)], mt, (0, -1, 0))
        m.face([(a, u0, v1), (a, u1, v1), (b, u1, v1), (b, u0, v1)], mt, (0, 0, -1))
        if sill:
            m.face([(a, u0, v0), (a, u1, v0), (b, u1, v0), (b, u0, v0)], mt, (0, 0, 1))


SEG = {"n": None, "s": None, "e": None, "w": None}


def house(m, x0, z0, x1, z1, eave, ridge, along, wall, roof, sides="nsew", spans=None, wins=(), over=25.0,
          ends=(True, True)):
    """A solid house: walls from 0 to its eave on `sides` (spans: {side: [(u0, u1)]} to draw part of a side, where a
    lower neighbour stands against the rest), a gable roof, lit windows on the sides in `wins`."""
    spans = spans or {}
    for s in sides:
        for (u0, u1) in spans.get(s, [(None, None)]):
            if s in "ns":
                a, b = (x0, x1) if u0 is None else (u0, u1)
                zc = z0 if s == "n" else z1
                C.strip(m, (a, zc), (b, zc), 0, 0, eave, eave, wall, (0, -1 if s == "n" else 1, 0), step=300.0)
            else:
                a, b = (z0, z1) if u0 is None else (u0, u1)
                xc = x0 if s == "w" else x1
                C.strip(m, (xc, a), (xc, b), 0, 0, eave, eave, wall, (-1 if s == "w" else 1, 0, 0), step=300.0)
    gable(m, x0, z0, x1, z1, eave, ridge, wall, roof, along=along, over=over, ends=ends)
    for s in wins:
        if s in "ns":
            zc, out = (z0, -1) if s == "n" else (z1, 1)
            n = max(1, int((x1 - x0) // 160))
            for k in range(n):
                u = x0 + (x1 - x0) * (k + 0.5) / n
                window(m, "z", zc, u, eave - 130, out, w=40, h=54)
                if eave > 330 and k % 2 == 0:
                    window(m, "z", zc, u, 80, out, w=40, h=54)
        else:
            xc, out = (x0, -1) if s == "w" else (x1, 1)
            n = max(1, int((z1 - z0) // 160))
            for k in range(n):
                u = z0 + (z1 - z0) * (k + 0.5) / n
                window(m, "x", xc, u, eave - 130, out, w=40, h=54)
                if eave > 330 and k % 2 == 1:
                    window(m, "x", xc, u, 80, out, w=40, h=54)


# ================================================================================================ the plan
# open floor at 0 (rectangles, overlapping where they meet)
RING = (-900, -500, 900, 1100)            # round the flooded square
LANE_N = (-1000, -800, 1500, -500)        # the north lane (the back lane), tower foot to east street
FOOT = (-1600, -600, -1000, -500)         # the tower's foot
STREET_W = (-1600, -600, -1200, 1300)     # the west street
LANE_W = (-1200, 100, -900, 400)          # the square's west lane
LANE_E = (900, 100, 1200, 400)            # the square's east lane
STREET_E = (1200, -800, 1500, 1300)       # the east street
STREET_S = (-1600, 1100, 1500, 1300)      # the south street, in front of the arcade
FORE = (-400, -1300, 400, -800)           # the causeway's forecourt
CAUSE = (-150, -1900, 150, -1300)         # the causeway passage
TOWER_IN = (-1750, -1000, -1050, -650)    # the tower's ground floor (its south half)
TDOOR = (-1480, -650, -1320, -600)        # the tower door's reveal
HOUSE_IN = (-1870, 130, -1630, 370)       # the open house in the west street
HOUSE_DOOR = (-1630, 150, -1600, 350)
FLOORS = [RING, LANE_N, FOOT, STREET_W, LANE_W, LANE_E, STREET_E, STREET_S, FORE, CAUSE, TOWER_IN, TDOOR,
          HOUSE_IN, HOUSE_DOOR]

STAIR = (-400, -1300, -250, -800)         # the shortcut's last stair, by the forecourt
R1 = (-1750, -1000, -1610, -680)          # the tower's first ramp (0 -> 180), solid
DOORWALL_O = (-150, -1430, 150, -1370)    # the causeway's outer gate wall (lime)
DOORWALL_I = (-150, -1680, 150, -1620)    # its inner gate wall (blue)
STEPS = (-300, 1200, 300, 1300)          # the two steps up to the arcade
# cover: plain blocks 100 x 100 (fallen masonry, stall counters) on the 50 grid, so the floor under each is left out
# exactly (no hidden ground under blocks) without thin slivers; 100 apart or more, 30 or more inside their region
COVER_F = [(-100, -1150), (200, -1150), (50, -950), (250, -950), (-100, -750), (200, -750)]   # the forecourt
COVER_W = [(-1450, -150), (-1350, 200), (-1450, 550)]                                           # the west street
STREET_STALLS = [(-1150, 1150, -1000, 1250), (950, 1150, 1100, 1250)]                         # by the south row


def sq100(c):
    return (c[0] - 50, c[1] - 50, c[0] + 50, c[1] + 50)


GROUND_HOLES = [BASIN, STAIR, R1, DOORWALL_O, DOORWALL_I, STEPS] + [sq100(c) for c in COVER_F + COVER_W] +     STREET_STALLS

g = mesh("streets", uv=220.0)
spots["street_cells"] = ground(g, FLOORS, 0.0, COBBLE, GROUND_HOLES)
g.build()

# ================================================================================================ B. the flooded square
COURT_RECTS = [(-550, 100, -200, 800), (200, 100, 550, 800), (-200, 400, 200, 800)]
PLINTH = (-200, 0, 200, 400)
GROT = (-140, 60, 140, 340)               # the grotto inside the plinth
LEDGE = (-140, 220, 140, 340)             # its dry ledge (0)
GAP = (-60, 60)                           # the gap in its north face: x -60..60, up to 110
sq = mesh("square", uv=200.0)
# the basin's rim (0 down to the drowned cobbles), facing in
C.walls(sq, *BASIN, BED_Y, 0.0, ASHLAR, inward=True, step=300.0)
# the fountain court: paving at 0, its sides down into the water
STALLS = [(-400, 600), (-150, 600), (150, 600), (400, 600)]
for r in COURT_RECTS:
    for rr in C.rects_minus(r, [sq100(c) for c in STALLS]):
        tiled(sq, *rr, 0.0, COURT, size=110.0)
C.strip(sq, (-550, 100), (-200, 100), BED_Y, BED_Y, 0, 0, ASHLAR, (0, -1, 0))
C.strip(sq, (200, 100), (550, 100), BED_Y, BED_Y, 0, 0, ASHLAR, (0, -1, 0))
C.strip(sq, (-550, 800), (-550, 100), BED_Y, BED_Y, 0, 0, ASHLAR, (-1, 0, 0))
C.strip(sq, (550, 100), (550, 800), BED_Y, BED_Y, 0, 0, ASHLAR, (1, 0, 0))
C.strip(sq, (550, 800), (-550, 800), BED_Y, BED_Y, 0, 0, ASHLAR, (0, 1, 0), step=300.0)
# steps down into the flood on the court's west and east sides (looks: a 25 step needs none)
# the plinth: outer faces, the gap in the north face, the grotto's inner faces, ceiling and ledge
PT = 160.0
C.plane_rect(sq, "z", 0, -200, BED_Y, 200, PT, [(GAP[0], BED_Y, GAP[1], 110)], ASHLAR, (0, -1, 0))
C.plane_rect(sq, "x", -200, 0, BED_Y, 400, PT, [], ASHLAR, (-1, 0, 0))
C.plane_rect(sq, "x", 200, 0, BED_Y, 400, PT, [], ASHLAR, (1, 0, 0))
C.plane_rect(sq, "z", 400, -200, 0, 200, PT, [], ASHLAR, (0, 1, 0))
tiled(sq, -200, 0, 200, 400, PT, ASHLAR, size=135.0)
jambs(sq, "z", 0, 60, GAP[0], BED_Y, GAP[1], 110, ASHLAR, sill=False)
C.plane_rect(sq, "z", 60, -140, BED_Y, 140, 120, [(GAP[0], BED_Y, GAP[1], 110)], ASHLAR, (0, 1, 0))
C.plane_rect(sq, "x", -140, 60, BED_Y, 340, 120, [], ASHLAR, (1, 0, 0))
C.plane_rect(sq, "x", 140, 60, BED_Y, 340, 120, [], ASHLAR, (-1, 0, 0))
C.plane_rect(sq, "z", 340, -140, 0, 140, 120, [], ASHLAR, (0, -1, 0))
C.ceiling(sq, -140, 60, 140, 340, 120, ASHLAR, size=150.0)
tiled(sq, *LEDGE, 0.0, COURT, size=140.0)
C.strip(sq, (-140, 220), (140, 220), BED_Y, BED_Y, 0, 0, ASHLAR, (0, -1, 0))
spots["grotto"] = {"tribal": (-60, 0, 290), "upgrade": (60, 0, 290), "gap": (0, BED_Y, 0)}
# the column and its bowl on top of the plinth (the landmark from the arcade)
post(sq, 0, 200, 46, PT, 420, ASHLAR, n=8, cap=False)
post(sq, 0, 200, 120, 420, 452, ASHLAR, n=8)
post(sq, 0, 200, 30, 452, 560, ASHLAR, n=8, cap=False)
post(sq, 0, 200, 70, 560, 580, ASHLAR, n=8)
# a bell hung in an iron frame on the column's top
sq.box(-56, 192, 56, 208, 580, 700, DARK)
sq.box(-56, 192, 56, 208, 700, 712, DARK, top=DARK)
post(sq, 0, 200, 36, 610, 690, DARK, n=8)
# the market stalls on the court (squad 1's cover): counters 100 x 100 x 100, an awning board on the back half
for (x, z) in STALLS:
    sq.box(x - 50, z - 50, x + 50, z + 50, 0, 100, TIMBER, DARK)
    sq.box(x - 50, z + 10, x + 50, z + 50, 100, 140, AWNING, DARK)
spots["stalls"] = STALLS
spots["court_region"] = (-525, 125, 525, 775)
spots["stall_region"] = (-525, 440, 525, 775)
spots["patrol"] = [(-400, 150), (-400, 480), (400, 480), (400, 150)]
sq.build()

# the flood: one grid through every edge of the court, plinth and ledge, and zero-width cuts at the water's repeats
WHOLES = COURT_RECTS + [(-200, 0, -60, 60), (60, 0, 200, 60), (-200, 60, -140, 400), (140, 60, 200, 400),
                        (-140, 340, 140, 400), LEDGE]
ZERO = [(0, BASIN[1], 0, BASIN[3])]
wb = mesh("square_bed", uv=220.0)
C.water_box(wb, BASIN, WHOLES + ZERO, BED_Y, WATER_Y, BED, WATER, wm=wtr)
wb.build()
wtr.build()

# ================================================================================================ A. the gate arcade
ar = mesh("arcade", uv=200.0)
ARC = (-600, 1300, 600, 1600)
block(ar, *ARC, 0.0, ARC_Y, BRICK, COURT, which="n", size=120.0)
block(ar, -300, 1200, 300, 1250, 0.0, 20.0, BRICK, COURT, which="nwe", size=150.0)
block(ar, -300, 1250, 300, 1300, 0.0, 40.0, BRICK, COURT, which="nwe", size=150.0)
# the back wall with the way back to 2.1, its roof on posts along the front
C.plane_rect(ar, "z", 1600, -600, ARC_Y, 600, 300, [(-100, ARC_Y, 100, 280)], BRICK, (0, -1, 0))
for x in range(-500, 501, 200):
    post(ar, x, 1320, 14, ARC_Y, 300, DARK, n=6, cap=False)
C.ceiling(ar, -625, 1280, 625, 1600, 300, DARK, size=200.0)
tiled(ar, -625, 1280, 625, 1600, 345, SLATE, size=240.0)  # 45 over the ceiling: closer reads as a folded floor
C.strip(ar, (-625, 1280), (625, 1280), 300, 300, 345, 345, DARK, (0, 1, 0), step=300.0)
ar.box(-598, 1300, 598, 1312, 262, 280, DARK)  # the beam over the posts (20 under the ceiling)
# the passage south to 2.1's town gate
tiled(ar, -100, 1600, 100, 1800, ARC_Y, COURT, size=110.0)
C.walls(ar, -100, 1600, 100, 1800, ARC_Y, 280, BRICK, which="ews", inward=True)
C.ceiling(ar, -100, 1600, 100, 1800, 280, DARK, size=110.0)
lantern(ar, -560, 1340, ARC_Y, h=150)
lantern(ar, 560, 1340, ARC_Y, h=150)
C.decal(ar, [(-260, 1596, 140), (-160, 1596, 140), (-160, 1596, 240), (-260, 1596, 240)], SIGN)
C.decal(ar, [(160, 1596, 140), (260, 1596, 140), (260, 1596, 240), (160, 1596, 240)], SIGN)
spots["start0"] = (0, ARC_Y, 1480)
spots["exit_back"] = (0, ARC_Y, 1740)
spots["arcade_lanterns"] = [(-560, ARC_Y + 165, 1340), (560, ARC_Y + 165, 1340)]
ar.build()

# ================================================================================================ the houses
hs = mesh("houses", uv=200.0)
# (x0, z0, x1, z1, eave, ridge, along, wall, roof, sides, spans, wins)
HOUSES = [
    # round the square
    (-1200, -500, -900, 100, 380, 500, "z", PLASTER, SLATE, "nsew", {}, "nsew"),
    (-1200, 400, -900, 1100, 340, 460, "z", TIMBER, SHINGLE, "nsew", {}, "nsew"),
    (900, -500, 1200, 100, 360, 480, "z", BRICK, SHINGLE, "nsew", {}, "nsew"),
    (900, 400, 1200, 1100, 400, 520, "z", PLASTER, SLATE, "nsew", {}, "nsew"),
    # the west row
    (-1900, -600, -1600, 100, 420, 540, "z", BRICK, SLATE, "es", {}, "e", (False, True)),
    (-1900, 400, -1600, 1300, 380, 500, "z", PLASTER, SHINGLE, "ne", {}, "e"),
    # the south row, either side of the arcade
    (-1900, 1300, -600, 1600, 400, 520, "x", TIMBER, SLATE, "ne", {"n": [(-1600, -600)]}, "n"),
    (600, 1300, 1500, 1600, 380, 490, "x", BRICK, SHINGLE, "nw", {}, "n"),
    # the east row (the cistern between)
    (1500, -800, 1900, -300, 400, 520, "z", PLASTER, SLATE, "w", {}, "w", (True, False)),
    (1500, 300, 1900, 1600, 380, 500, "z", TIMBER, SLATE, "w", {"w": [(300, 1300)]}, "w", (False, True)),
    # the north row east of the forecourt
    (400, -1300, 900, -800, 420, 540, "x", BRICK, SLATE, "swe", {"e": [(-1300, -800)]}, "s"),
    (900, -1300, 1500, -800, 380, 500, "x", PLASTER, SHINGLE, "se", {}, "s", (False, True)),
]
for hd in HOUSES:
    house(hs, *hd[:12], ends=hd[12] if len(hd) > 12 else (True, True))
# the open house in the west street (Tribal 1): walls 30 thick, a wide doorway onto the street, a ceiling
OH = (-1900, 100, -1600, 400)
C.plane_rect(hs, "x", -1600, 100, 0, 400, 320, [(150, 0, 350, 200)], BRICK, (1, 0, 0))
jambs(hs, "x", -1630, -1600, 150, 0, 350, 200, BRICK, sill=False)
C.walls(hs, *HOUSE_IN, 0, 300, BRICK, which="nsw", inward=True)
C.plane_rect(hs, "x", -1630, 130, 0, 370, 300, [(150, 0, 350, 200)], BRICK, (-1, 0, 0))
C.ceiling(hs, *HOUSE_IN, 300, DARK, size=130.0)
gable(hs, -1900, 100, -1600, 400, 320, 420, BRICK, SHINGLE, along="x")
window(hs, "x", -1600, 110 + 20, 230, 1, w=30, h=50)
spots["open_house"] = {"tribal": (-1780, 0, 200), "health": (-1780, 0, 310)}
# the backdrop: roofs beyond the north edge and the lighthouse far to the north-east (the storm engine on top)
for (bx0, bz0, bx1, bz1, eave, ridge, along) in [(-400, -2300, 0, -1950, 520, 640, "x"),
                                                 (300, -2200, 800, -1900, 480, 600, "x"),
                                                 (900, -1800, 1400, -1400, 520, 640, "z"),
                                                 (-1500, -1900, -1000, -1550, 600, 720, "x"),
                                                 (1550, -1200, 1950, -900, 520, 650, "z")]:
    C.walls(hs, bx0, bz0, bx1, bz1, 300, eave, PLASTER, step=500.0)
    gable(hs, bx0, bz0, bx1, bz1, eave, ridge, PLASTER, SLATE, along=along)
    window(hs, "z", bz1, (bx0 + bx1) / 2, eave - 110, 1, w=40, h=50)
LH = (2300, -5300)
C.boulder(hs, LH[0], LH[1], -60, 520, 520, 79, ASHLAR, sides=8, sink=40.0)
post(hs, LH[0], LH[1], 110, 440, 1500, ASHLAR, n=8, cap=False)
post(hs, LH[0], LH[1], 135, 1500, 1640, WINDOW, n=8, cap=False)
hs.face([(LH[0] + 150 * math.cos(k * math.tau / 8), LH[1] + 150 * math.sin(k * math.tau / 8), 1640)
         for k in range(8)], SLATE, (0, 0, -1))
for k in range(8):
    a0, a1 = k * math.tau / 8, (k + 1) * math.tau / 8
    hs.face([(LH[0] + 150 * math.cos(a0), LH[1] + 150 * math.sin(a0), 1640),
             (LH[0] + 150 * math.cos(a1), LH[1] + 150 * math.sin(a1), 1640), (LH[0], LH[1], 1800)], SLATE,
            (math.cos((a0 + a1) / 2), math.sin((a0 + a1) / 2), 1))
# stalls along the south street against the houses (outside every region)
for (x0, z0, x1, z1) in STREET_STALLS:
    hs.box(x0, z0, x1, z1, 0, 100, TIMBER, DARK)
    hs.box(x0, z0 + 50, x1, z1, 100, 150, AWNING, DARK)
# lanterns round the square and the streets
LANTERNS = [(-880, 1080), (880, 1080), (-880, -480), (880, -480), (-1220, -520), (-1580, 700), (1480, 700),
            (1220, -780), (-1220, 1120), (1220, 1120)]
for (x, z) in LANTERNS:
    lantern(hs, x, z, 0.0)
spots["lanterns"] = [(x, 185, z) for (x, z) in LANTERNS]
hs.build()

# ================================================================================================ D. the bell tower
# footprint x -1800..-1000, z -1400..-600, walls 50 thick: inside x -1750..-1050, z -1350..-650. Half-floors: the
# ground (south half, 0), G1 (north half, a solid block to 180), G2 (south half, a slab at 360), G3 (north half, a
# slab at 540), the bell chamber (south half, a slab at 700); ramps along the west band (x -1750..-1610: R1 0->180,
# R3 360->540) and the east band (x -1190..-1050: R2 180->360, R4 540->700), each about 27-29 degrees.
TX0, TZ0, TX1, TZ1 = -1800, -1400, -1000, -600
IX0, IZ0, IX1, IZ1 = -1750, -1350, -1050, -650
WB, EB = -1610, -1190          # the west band's east edge, the east band's west edge
MID = -1000
TTOP, CEIL = 1000.0, 960.0
t = mesh("tower", uv=200.0)
tf = mesh("tower_floors", uv=180.0)
# openings (plane, u0, v0, u1, v1, collider?) on each face
DOOR = (-1480, 0, -1320, 170)
OPEN_S = [DOOR, (-1560, 380, -1440, 500)]                      # the door; the second floor's window
OPEN_E = [(-990, 700, -850, 860), (-1300, 740, -1180, 880)]     # the chamber's door to the roofs; an arch
OPEN_N = [(-1650, 740, -1530, 880), (-1300, 740, -1180, 880)]   # arches over the well (out of reach)
C.plane_rect(t, "z", TZ1, TX0, 0, TX1, TTOP, OPEN_S, TOWER, (0, 1, 0))
C.plane_rect(t, "z", IZ1, IX0, 0, IX1, CEIL, OPEN_S, TOWER, (0, -1, 0))
C.plane_rect(t, "x", TX1, TZ0, 0, TZ1, TTOP, OPEN_E, TOWER, (1, 0, 0))
C.plane_rect(t, "x", IX1, IZ0, 0, IZ1, CEIL, OPEN_E, TOWER, (-1, 0, 0))
C.plane_rect(t, "z", TZ0, TX0, 0, TX1, TTOP, OPEN_N, TOWER, (0, -1, 0))
C.plane_rect(t, "z", IZ0, IX0, 0, IX1, CEIL, OPEN_N, TOWER, (0, 1, 0))
C.plane_rect(t, "x", TX0, TZ0, 0, TZ1, TTOP, [], TOWER, (-1, 0, 0))
C.plane_rect(t, "x", IX0, IZ0, 0, IZ1, CEIL, [], TOWER, (1, 0, 0))
for (u0, v0, u1, v1) in OPEN_S:
    jambs(t, "z", IZ1, TZ1, u0, v0, u1, v1, TOWER, sill=v0 > 0)
for (u0, v0, u1, v1) in OPEN_E:
    jambs(t, "x", IX1, TX1, u0, v0, u1, v1, TOWER)
for (u0, v0, u1, v1) in OPEN_N:
    jambs(t, "z", IZ0, TZ0, u0, v0, u1, v1, TOWER)
# colliders in the arches the chamber and the ramps reach (falls of 700): the east arch; the window on G2 (a drop of
# 360 to the street)
C.collider(edges, (TX1 - 25, -1300), (TX1 - 25, -1180), 740, 1100)
C.collider(edges, (-1560, TZ1 - 25), (-1440, TZ1 - 25), 380, 800)
C.ceiling(t, IX0, IZ0, IX1, IZ1, CEIL, DARK, size=240.0)
# the roof: a slate pyramid from the walls' tops, and a small lantern-spire
OV = 40
corners = [(TX0 - OV, TZ0 - OV), (TX1 + OV, TZ0 - OV), (TX1 + OV, TZ1 + OV), (TX0 - OV, TZ1 + OV)]
apex = ((TX0 + TX1) / 2, (TZ0 + TZ1) / 2, 1330)
for k in range(4):
    p, q = corners[k], corners[(k + 1) % 4]
    t.face([(p[0], p[1], TTOP - 10), (q[0], q[1], TTOP - 10), apex], SLATE,
           ((p[0] + q[0]) / 2 - apex[0], (p[1] + q[1]) / 2 - apex[1], 1))
post(t, apex[0], apex[1], 8, 1300, 1420, DARK, n=4)
# lit windows outside (the tower lit from inside), and the bell sign over the door
for (u, v) in [(-1100, 250), (-1300, 450), (-1550, 620), (-1700, 820), (-1100, 820)]:
    window(t, "z", TZ1, u, v, 1, w=46, h=70)
for (u, v) in [(-700, 250), (-1150, 600), (-700, 820)]:
    window(t, "x", TX1, u, v, 1, w=46, h=70)
C.decal(t, [(-1290, TZ1 + 4, 150), (-1190, TZ1 + 4, 150), (-1190, TZ1 + 4, 250), (-1290, TZ1 + 4, 250)], SIGN)
# the pulley over the door (the switch is the game's; this is its frame: a beam on two brackets over the lintel)
block(t, -1470, TZ1, -1330, TZ1 + 30, 300, 320, DARK, which="sew", size=None)
block(t, -1470, TZ1, -1450, TZ1 + 30, 200, 300, DARK, which="sew", size=None)
block(t, -1350, TZ1, -1330, TZ1 + 30, 200, 300, DARK, which="sew", size=None)
spots["switch"] = (-1400, 235, TZ1 + 6)
spots["door"] = (-1400, 0, -625)
# the outer balconies of the two bell lookouts: A on the east face (450), B on the south face (600); a 20 rim
BAL_A = (-1000, -780, -890, -620, 450)
BAL_B = (-1240, -600, -1080, -490, 600)
# (no face against the tower's wall: two faces in one plane; rims stop 1 short of each other for the same reason)
x0, z0, x1, z1, y = BAL_A
block(t, x0, z0, x1, z1, y - 30, y, TOWER, DECK, which="nse", size=None)
t.face([(x0, z0, y - 30), (x1, z0, y - 30), (x1, z1, y - 30), (x0, z1, y - 30)], TOWER, (0, 0, -1))
block(t, x1 - 10, z0, x1, z1, y, y + 20, TOWER, which="nse", size=None)
block(t, x0, z1 - 10, x1 - 11, z1, y, y + 20, TOWER, which="nse", size=None)
block(t, x0, z0, x1 - 11, z0 + 10, y, y + 20, TOWER, which="nse", size=None)
block(t, x0, z0 + 50, x0 + 30, z1 - 50, y - 120, y - 34, DARK, which="nse", size=None)  # a corbel
x0, z0, x1, z1, y = BAL_B
block(t, x0, z0, x1, z1, y - 30, y, TOWER, DECK, which="sew", size=None)
t.face([(x0, z0, y - 30), (x1, z0, y - 30), (x1, z1, y - 30), (x0, z1, y - 30)], TOWER, (0, 0, -1))
block(t, x0, z1 - 10, x1, z1, y, y + 20, TOWER, which="sew", size=None)
block(t, x0, z0, x0 + 10, z1 - 11, y, y + 20, TOWER, which="sew", size=None)
block(t, x1 - 10, z0, x1, z1 - 11, y, y + 20, TOWER, which="sew", size=None)
block(t, x0 + 50, z0, x1 - 50, z0 + 30, y - 120, y - 34, DARK, which="sew", size=None)
spots["perch_a"] = (-950, 450, -730)
spots["flames_a"] = (-935, 450, -660)
spots["perch_b"] = (-1190, 600, -540)
spots["flames_b"] = (-1115, 600, -530)
# --- inside: R1 (solid, 0 -> 180) up the west band to G1
block(tf, *R1, 0.0, 180.0, TOWER, DECK, which="e", size=110.0, y1b=0.0, along="z")
# G1: the north half, solid to 180 (its top less R2's band), its face to the ground floor
G1 = (IX0, IZ0, IX1, MID)
COVER_G1 = [(-1550, -1250), (-1350, -1250), (-1450, -1100)]
COVER_G3 = [(-1550, -1200), (-1350, -1200)]
for rr in C.rects_minus((IX0, IZ0, EB, MID), [sq100(c) for c in COVER_G1]):
    tiled(tf, *rr, 180.0, DECK, size=120.0)
tiled(tf, EB, IZ0, IX1, -1320, 180.0, DECK, size=140.0)
C.strip(tf, (WB, MID), (IX1, MID), 0, 0, 180, 180, TOWER, (0, 1, 0))
# R2 (solid on G1, 180 -> 360) up the east band, south to G2
block(tf, EB, -1320, IX1, MID, 180.0, 180.0, TOWER, DECK, which="ws", size=110.0, y1b=360.0, along="z")
# G2: the south half slab at 360 (and R3's foot in the west band), its underside the ground floor's ceiling
tiled(tf, WB, MID, IX1, IZ1, 360.0, DECK, size=120.0)
tiled(tf, IX0, -680, WB, IZ1, 360.0, DECK, size=140.0)
C.ceiling(tf, WB, MID, IX1, IZ1, 340.0, DARK, size=180.0)
C.ceiling(tf, IX0, -680, WB, IZ1, 340.0, DARK, size=140.0)
C.strip(tf, (WB, MID), (EB, MID), 340, 340, 360, 360, DECK, (0, -1, 0))


def slab_ramp(m, x0, z_lo, x1, z_hi, y_lo, y_hi, side_x, side_face, thick=20.0):
    """A ramp slab in a band x0..x1 from (z_lo, y_lo) to (z_hi, y_hi): its top (tiled), its underside and the
    side facing the well (at side_x, facing side_face)."""
    tiled(m, x0, z_lo, x1, z_hi, y_lo, DECK, y_hi, along="z", size=110.0)
    tiled(m, x0, z_lo, x1, z_hi, y_lo - thick, DARK, y_hi - thick, along="z", size=160.0, facing=(0, 0, -1))
    C.strip(m, (side_x, z_lo), (side_x, z_hi), y_lo - thick, y_hi - thick, y_lo, y_hi, DECK, side_face)


# R3 (a slab, 360 -> 540) up the west band from G2 to G3
slab_ramp(tf, IX0, -680, WB, MID, 360.0, 540.0, WB, (1, 0, 0))
# G3: the north half slab at 540 (and R4's foot in the east band)
for rr in C.rects_minus((IX0, IZ0, EB, MID), [sq100(c) for c in COVER_G3]):
    tiled(tf, *rr, 540.0, DECK, size=120.0)
tiled(tf, EB, IZ0, IX1, -1320, 540.0, DECK, size=140.0)
C.ceiling(tf, IX0, IZ0, EB, MID, 520.0, DARK, size=180.0)
C.ceiling(tf, EB, IZ0, IX1, -1320, 520.0, DARK, size=140.0)
C.strip(tf, (WB, MID), (EB, MID), 520, 520, 540, 540, DECK, (0, 1, 0))
# R4 (a slab, 540 -> 700) up the east band from G3 to the bell chamber
slab_ramp(tf, EB, -1320, IX1, MID, 540.0, 700.0, EB, (-1, 0, 0))
# the bell chamber: the south half at 700
tiled(tf, IX0, MID, IX1, IZ1, 700.0, DECK, size=120.0)
C.ceiling(tf, IX0, MID, IX1, IZ1, 680.0, DARK, size=180.0)
C.strip(tf, (IX0, MID), (EB, MID), 680, 680, 700, 700, DECK, (0, -1, 0))
# cover on the landings: stone blocks (G1: three for the slickers; G3: two for the wardens)
for (x, z) in COVER_G1:
    tf.box(x - 50, z - 50, x + 50, z + 50, 180, 290, TOWER, DECK)
for (x, z) in COVER_G3:
    tf.box(x - 50, z - 50, x + 50, z + 50, 540, 650, TOWER, DECK)
spots["cover_g1"] = COVER_G1
spots["cover_g3"] = COVER_G3
spots["g1_region"] = (-1730, -1330, -1210, -1020)
spots["g3_region"] = (-1730, -1330, -1210, -1020)
# the bell: a beam across the chamber, the bell hung from it (its rim at 790), a table under the east arch
BELL = (-1400, -825)
tf.box(IX0 + 3, BELL[1] - 12, IX1 - 3, BELL[1] + 12, 900, 930, DARK)
post(tf, BELL[0], BELL[1], 90, 790, 830, DARK, n=8, cap=False)
post(tf, BELL[0], BELL[1], 64, 830, 900, DARK, n=8, cap=False)
tf.face([(BELL[0] + 90 * math.cos(k * math.tau / 8), BELL[1] + 90 * math.sin(k * math.tau / 8), 790)
         for k in range(8)], DARK, (0, 0, -1))
tf.face([(BELL[0] + 90 * math.cos(k * math.tau / 8), BELL[1] + 90 * math.sin(k * math.tau / 8), 830)
         for k in range(8)], DARK, (0, 0, 1))
spots["key_lime"] = (-1260, 700, -760)
spots["tribal_chamber"] = (-1640, 700, -760)
spots["tribal_g2"] = (-1500, 360, -720)
spots["chamber_door"] = (-1020, 700, -920)
tf.build()
t.build()

# ================================================================================================ the rooftop shortcut
# from the chamber's east door (700) a drop onto roof A (520), B (340), C (180), then the stair to the forecourt
rf = mesh("roofs", uv=200.0)
ROOF_A = (-1000, -1300, -800, -800, 520.0)
ROOF_B = (-800, -1300, -600, -800, 340.0)
ROOF_C = (-600, -1300, -400, -800, 180.0)
for (x0, z0, x1, z1, y) in (ROOF_A, ROOF_B, ROOF_C):
    block(rf, x0, z0, x1, z1, 0.0, y, BRICK if y != 340.0 else PLASTER, SLATE, which="s", size=130.0)
C.strip(rf, (-800, -1300), (-800, -800), 340, 340, 520, 520, BRICK, (1, 0, 0))
C.strip(rf, (-600, -1300), (-600, -800), 180, 180, 340, 340, PLASTER, (1, 0, 0))
# parapets (150, colliders to 400) on the long falls: A and B both sides, C's north edge
for (x0, z0, x1, z1, y) in (ROOF_A, ROOF_B):
    C.lip(rf, (x1, z1), (x0, z1), y, y, TOWER, h=150, thick=25, coll_to=400, edges=edges, caps=(True, False))
    C.lip(rf, (x0, z0), (x1, z0), y, y, TOWER, h=150, thick=25, coll_to=400, edges=edges,
          caps=(False, True))
C.lip(rf, (-600, -1300), (-400, -1300), 180, 180, TOWER, h=150, thick=25, coll_to=400, edges=edges,
      caps=(False, True))
# the stair: a landing at 180 by the causeway wall, then down south to the north lane at 0 (26.6 degrees)
block(rf, -400, -1300, -250, -1160, 0.0, 180.0, BRICK, SLATE, which="e", size=150.0)
block(rf, -400, -1160, -250, -800, 0.0, 180.0, BRICK, DECK, which="e", size=120.0, y1b=0.0, along="z")
for (x, y) in [(-950, 520), (-650, 340)]:
    window(rf, "z", -800, x, y - 150, 1, w=40, h=54)
lantern(rf, -320, -1270, 180.0, h=140)
spots["tribal_roof_c"] = (-500, 180, -1050)
spots["lantern_c"] = (-320, 180 + 155, -1270)
rf.build()

# ================================================================================================ F. the causeway gates
cw = mesh("causeway", uv=200.0)
for (x0, x1, face) in ((-400, -150, (1, 0, 0)), (150, 400, (-1, 0, 0))):
    xc = -150 if x0 < 0 else 150
    C.plane_rect(cw, "x", xc, -1900, 0, -1300, 450, [], ASHLAR, face)
    C.plane_rect(cw, "z", -1300, x0, 0, x1, 450, [], ASHLAR, (0, 1, 0))
    tiled(cw, x0, -1900, x1, -1300, 450, ASHLAR, size=250.0)
C.plane_rect(cw, "z", -1900, -150, 0, 150, 450, [], ASHLAR, (0, 1, 0))
# the two gate walls across it (60 deep: the doors' reveals), each with a doorway 160 x 170 and a lamp over it
GATES = {"outer": DOORWALL_O, "inner": DOORWALL_I}
for name, (x0, z0, x1, z1) in GATES.items():
    C.plane_rect(cw, "z", z1, -150, 0, 150, 450, [(-80, 0, 80, 170)], TOWER, (0, 1, 0))
    C.plane_rect(cw, "z", z0, -150, 0, 150, 450, [(-80, 0, 80, 170)], TOWER, (0, -1, 0))
    tiled(cw, -150, z0, 150, z1, 450, TOWER, size=150.0)
    jambs(cw, "z", z0, z1, -80, 0, 80, 170, TOWER, sill=False)
    tiled(cw, -80, z0, 80, z1, 0.0, COBBLE, size=80.0)
    cw.box(-20, z1 + 2, 20, z1 + 16, 200, 240, BLUE if name == "inner" else WINDOW, DARK)
spots["door_outer"] = (0, 0, -1400)
spots["door_inner"] = (0, 0, -1650)
spots["exit_2_4"] = (0, 0, -1840)
spots["start3"] = (0, 0, -1760)
spots["forecourt_region"] = (-220, -1270, 360, -560)
for (x, z) in COVER_F:  # fallen masonry from the gatehouse
    cw.box(x - 50, z - 50, x + 50, z + 50, 0, 110, TOWER, ASHLAR)
spots["cover_f"] = COVER_F
cw.build()

# ================================================================================================ E. the cistern door
cs = mesh("cistern", uv=200.0)
CX0, CZ0, CX1, CZ1, CEAVE = 1500, -300, 1980, 300, 560.0
C.plane_rect(cs, "x", CX0, CZ0, 0, CZ1, CEAVE, [(-100, 0, 100, 220)], ASHLAR, (-1, 0, 0))
C.plane_rect(cs, "z", CZ0, CX0, 0, CX1, CEAVE, [], ASHLAR, (0, -1, 0))
C.plane_rect(cs, "z", CZ1, CX0, 0, CX1, CEAVE, [], ASHLAR, (0, 1, 0))
tiled(cs, CX0, CZ0, CX1, CZ1, CEAVE, SLATE, size=240.0)
# the lamp house on top (blue panes), and a blue lamp on each side of the arch
cs.box(1660, -80, 1820, 80, CEAVE, 700, BLUE, DARK)
corners = [(1640, -100), (1840, -100), (1840, 100), (1640, 100)]
for k in range(4):
    p, q = corners[k], corners[(k + 1) % 4]
    cs.face([(p[0], p[1], 700), (q[0], q[1], 700), (1740, 0, 790)], SLATE, ((p[0] + q[0]) / 2 - 1740,
                                                                            (p[1] + q[1]) / 2, 1))
block(cs, 1488, -40, 1500, 40, 226, 262, ASHLAR, which="nsw", size=None)   # the arch's keystone
lantern(cs, 1460, -150, 0.0, h=190, lamp=BLUE)
lantern(cs, 1460, 150, 0.0, h=190, lamp=BLUE)
# the way down inside: a level threshold, a ramp (0 -> -140, 28 degrees), the landing with the exit
PX0, PX1, PX2, PX3 = 1500, 1560, 1820, 1960
tiled(cs, PX0, -100, PX1, 100, 0.0, COBBLE, size=100.0)
tiled(cs, PX1, -100, PX2, 100, 0.0, ASHLAR, -140.0, along="x", size=100.0)
tiled(cs, PX2, -100, PX3, 100, -140.0, ASHLAR, size=100.0)


def pfloor(x, z):
    if x <= PX1:
        return 0.0
    if x >= PX2:
        return -140.0
    return -140.0 * (x - PX1) / (PX2 - PX1)


C.walls(cs, PX0, -100, PX3, 100, pfloor, lambda x, z: pfloor(x, z) + 220.0, ASHLAR, which="nse", inward=True,
        step=130.0)
C.ceiling(cs, PX0, -100, PX1, 100, 220.0, DARK, size=100.0)
C.ceiling(cs, PX1, -100, PX2, 100, 220.0, DARK, 80.0, along="x", size=100.0)
C.ceiling(cs, PX2, -100, PX3, 100, 80.0, DARK, size=100.0)
spots["exit_2_3"] = (1890, -140, 0)
spots["start2"] = (1380, 0, 0)
spots["start1"] = (700, 0, -650)
cs.build()

# ------------------------------------------------------------------------------------------------ the squads' places
spots["west_region"] = (-1580, -300, -1220, 700)
bw = mesh("west_cover", uv=160.0)
for (x, z) in COVER_W:  # rubble from the fallen houses
    bw.box(x - 50, z - 50, x + 50, z + 50, 0, 105, BRICK, ASHLAR)
spots["cover_w"] = COVER_W
bw.build()

# ------------------------------------------------------------------------------------------------ the level's edge
# a collider ring round everything, outside the houses' backs (none of them can be climbed: walls 340 and more)
RING_E = [(-1960, -1960), (2000, -1960), (2000, 1860), (-1960, 1860)]
for k in range(4):
    C.collider(edges, RING_E[k], RING_E[(k + 1) % 4], -200, 1400)
edges.build()

# ------------------------------------------------------------------------------------------------ light: the storm
level = [o for o in coll.all_objects if o.type == "MESH"]
SUN_DIR = (0.25, -0.15, -0.95)  # from above, a little from the south-west (Blender space: the light's travel)
WARM = (0.5, 0.32, 0.12)
COLD = (0.12, 0.26, 0.55)
LAMPS = [(x, z, 185, 300, WARM) for (x, z) in LANTERNS] + [
    (-560, 1340, ARC_Y + 165, 260, WARM), (560, 1340, ARC_Y + 165, 260, WARM),    # the arcade
    (0, 1700, ARC_Y + 180, 200, WARM),                                            # the passage back
    (0, 150, 30, 200, (0.25, 0.32, 0.4)),                                        # the grotto's glow
    (-1400, -820, 120, 380, (0.5, 0.3, 0.12)),                                    # the tower: ground floor
    (-1450, -1180, 300, 380, (0.5, 0.3, 0.12)),                                   # G1
    (-1300, -820, 480, 380, (0.5, 0.3, 0.12)),                                    # G2
    (-1450, -1180, 660, 380, (0.5, 0.3, 0.12)),                                   # G3
    (-1400, -820, 820, 420, (0.62, 0.38, 0.14)),                                  # the bell chamber
    (-935, -660, 510, 260, (0.6, 0.32, 0.1)),                                     # the lookouts' fires
    (-1115, -530, 660, 260, (0.6, 0.32, 0.1)),
    (-320, -1270, 335, 300, WARM),                                                # the stair's landing
    (1460, -150, 205, 300, COLD), (1460, 150, 205, 300, COLD),                    # the cistern's blue lamps
    (1700, 0, 120, 300, COLD),                                                    # inside the cistern door
    (0, -1400, 230, 260, WARM), (0, -1650, 230, 260, COLD),                       # the gates' lamps
]


def extra(x, z, y, mname):
    if mname.startswith("game_1958") and y < 0:
        return (0.75, 0.8, 0.82)  # the drowned cobbles darker
    if mname.startswith("lit_window"):
        return (2.2, 2.0, 1.6)  # the windows glow
    if mname.startswith("cistern_lamp"):
        return (2.0, 2.2, 2.6)
    if y > 1450 and z < -4000:
        return (2.0, 2.2, 2.6)  # the lighthouse's lamp room: the storm engine's cold glow
    if mname.startswith("game_16DB") and IX0 < x < IX1 and IZ0 < z < IZ1 and y > 780:
        return (0.55, 0.55, 0.6)  # the bell's iron
    return (1.0, 1.0, 1.0)


TINTS = {"game_0AC0": (0.82, 0.84, 0.88), "game_0715": (0.9, 0.9, 0.92), "game_1946": (0.85, 0.82, 0.8),
         "game_0BEB": (0.85, 0.85, 0.88), "game_16D9": (0.8, 0.78, 0.76)}  # rain-dark stone and boards
C.bake(level, SUN_DIR, (0.5, 0.55, 0.6), (0.25, 0.3, 0.35), tints=TINTS, lamps=LAMPS, extra=extra,
       soft={"game_0AC0": (0.5, 0.3), "game_0BEB": (0.5, 0.3), "game_1958": (0.5, 0.3)})
# the flood (the bake leaves water out): murky grey-green over its own texture
wme = bpy.data.objects["square_water"].data
wcol = wme.color_attributes.get("Col") or wme.color_attributes.new("Col", "BYTE_COLOR", "CORNER")
for d in wcol.data:
    d.color_srgb = (0.52, 0.58, 0.56, 1.0)

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
    if isinstance(v, dict):
        return {k: tup(x) for k, x in v.items()}
    return v


with open(os.path.join(C.OUT, NAME + "_spots.json"), "w", encoding="utf-8") as f:
    json.dump({k: tup(v) for k, v in spots.items()}, f, indent=1)
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(C.OUT, NAME + ".blend"))
print("BELLMARKET", json.dumps(report))
print("PARTS", json.dumps({o.name: sum(len(p.vertices) - 2 for p in o.data.polygons) for o in level}))
