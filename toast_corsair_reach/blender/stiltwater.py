"""Stiltwater Outskirts (Corsair Reach 2.1): builds the level from nothing and exports blender/out/stiltwater.glb.

Run in Blender 5.2 with jfg64 0.6.0+, after JFG-Studio has built its catalog once (the game's textures):
    blender --background --factory-startup --addons jfg64 --python stiltwater.py
Then in JFG-Studio: reimport_geometry (or import the .glb) into the level `stiltwater`.

Game coordinates throughout (x east, z south, y up); levels/2.1_stiltwater.md has the plan. A flooded marsh, the
water 40 deep everywhere (every hero wades), boardwalks at 60 on plank sides with ramps down into the water. One
water grid over the whole marsh: every footprint standing in it sits on the 100 grid (x mostly on 200), so the grid's
lines through their edges stay few. South to north: the landing jetty (start), the reed beds and their crossing, the
hut cluster (west), the mud islands, the leaning chapel (east), the fishers' rest, and the flood gate in the town
wall (north). Banks too steep to climb close the west, south and east; the town wall the north.
"""
import json
import math
import os
import random
import sys

import bpy

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import common as C  # noqa: E402
from common import Mesh, block, tiled, post, collider  # noqa: E402
import jfg64  # noqa: E402

NAME = "stiltwater"
scene, coll = C.new_scene(NAME)
spots = {}
rnd = random.Random(2101)

WATER_Y, BED_Y, DECK_Y = 0.0, -40.0, 60.0
MARSH = (-2000, -1900, 1800, 2000)  # the water's rectangle (x0, z0, x1, z1)


# ------------------------------------------------------------------------------------------------ our own images
def emblem_px(x, y):
    """The colony's emblem: a pale stilt house over three waves on a deep teal board, a pale rim."""
    if x in (0, 31) or y in (0, 31):
        return (0.78, 0.8, 0.74)
    if x in (1, 30) or y in (1, 30):
        return (0.2, 0.26, 0.26)
    pale = (0.86, 0.84, 0.72)
    if 9 <= x <= 22 and 9 <= y <= 15 and abs(x - 15.5) <= (y - 8) * 1.1:
        return pale  # the roof
    if 11 <= x <= 20 and 15 <= y <= 19:
        return (0.95, 0.72, 0.3) if 14 <= x <= 17 and 16 <= y <= 18 else pale  # the walls, a lit window
    if y in range(20, 23) and x in (12, 19):
        return pale  # the stilts
    for k, wy in enumerate((22, 25, 28)):
        if abs(y - (wy + math.sin(x * 0.9 + k) * 1.2)) < 0.8 and 4 <= x <= 27:
            return (0.55, 0.78, 0.82)
    return (0.1, 0.32, 0.34)


def reed_px(x, y):
    """Reed stalks, olive and straw, seed heads at the top."""
    col = (x * 5 + 3) % 4
    if y < 7 and col == 0:
        return (0.35, 0.24, 0.13)
    if col == 3:
        return (0.12, 0.16, 0.08)
    k = 0.8 + 0.25 * ((x * 7 + y) % 5) / 4
    return tuple(c * k for c in ((0.42, 0.48, 0.22) if col == 1 else (0.55, 0.52, 0.28)))


def window_px(x, y):
    """A lit window: four warm panes in a dark frame."""
    if x in (0, 15) or y in (0, 15) or x in (7, 8) or y in (7, 8):
        return (0.12, 0.08, 0.05)
    k = 1.0 - 0.25 * (abs(x - 7.5) + abs(y - 7.5)) / 7.5
    return (1.0 * k, 0.72 * k, 0.3 * k)


def sandbag_px(x, y):
    """Rows of sandbags, staggered: tan burlap with dark seams."""
    row = y // 4
    xx = (x + (4 if row % 2 else 0)) % 8
    if y % 4 == 3 or xx == 7:
        return (0.22, 0.18, 0.12)
    k = 0.85 + 0.15 * math.sin(xx * 0.8) + 0.04 * ((x + y) % 2)
    return (0.6 * k, 0.52 * k, 0.36 * k)


# ------------------------------------------------------------------------------------------------ materials
MATS, M = [], {}


def mat(name, material):
    M[name] = len(MATS)
    MATS.append(material)
    return M[name]


PLANK = mat("plank", C.game(0x193D))     # boardwalk boards, ramps
DECK = mat("deck", C.game(0x16D9))       # hut floors, the gate platform, roof decks
DARK = mat("dark", C.game(0x16DB))       # wet plank sides, pilings, hut walls, the hull
THATCH = mat("thatch", C.game(0x0000))   # hut and rest roofs
MUD = mat("mud", C.game(0x0CB0))         # the mud islands
BED = mat("bed", C.game(0x1959))         # the marsh bed under the water
MOSSG = mat("mossg", C.game(0x16E3))     # moss on the bank tops
BANK = mat("bank", C.game(0x1958))       # wet mossy rock: the banks
STONE = mat("stone", C.game(0x1736))     # mossy stone blocks: the chapel, its tower, the cover
FLAGS = mat("flags", C.game(0x16DF))     # grey flagstones: the chapel's floor, the dais
SLATE = mat("slate", C.game(0x0CAF))     # grey stone: the chapel's roof, the town's roofs
ASHLAR = mat("ashlar", C.game(0x0828))   # the town wall and its gate
WATER = mat("water", C.game(0x0DED, "water"))
EMBLEM = mat("emblem", C.own_material("colony_emblem", C.own_image("colony_emblem", 32, 32, emblem_px)))
REED = mat("reed", C.own_material("reed_stalks", C.own_image("reed_stalks", 16, 32, reed_px)))
WINDOW = mat("window", C.own_material("lit_window", C.own_image("lit_window", 16, 16, window_px)))
SANDBAG = mat("sandbag", C.own_material("sandbags", C.own_image("sandbags", 16, 16, sandbag_px)))
EDGE = jfg64.boundary_material()


def mesh(name, uv=200.0):
    return Mesh(name, MATS, coll, uv_size=uv)


edges = Mesh("colliders", [EDGE], coll)
wtr = Mesh("marsh_water", MATS, coll, uv_size=1000.0)  # its texture doesn't repeat: cut at 1000s (grid lines)
HOLES = []  # footprints standing in the marsh water (x0, z0, x1, z1)


def hole(r):
    HOLES.append(tuple(r))
    return r


def gable(m, x0, z0, x1, z1, eave, ridge, wall, roof, along="x", over=25.0, both=False):
    """A gable roof over x0..x1, z0..z1 (eaves `over` out), its ridge along `along`; the end walls' triangles."""
    def f(pts, mt, facing):
        if both:
            m.quad2(pts, mt, apart=12.0)  # closer reads as a folded floor
        else:
            m.face(pts, mt, facing)
    if along == "x":
        zm = (z0 + z1) / 2
        a, b = x0 - over, x1 + over
        f([(a, z0 - over, eave - 10), (b, z0 - over, eave - 10), (b, zm, ridge), (a, zm, ridge)], roof, (0, -1, 1))
        f([(b, z1 + over, eave - 10), (a, z1 + over, eave - 10), (a, zm, ridge), (b, zm, ridge)], roof, (0, 1, 1))
        m.face([(x0, z1, eave), (x0, z0, eave), (x0, zm, ridge)], wall, (-1, 0, 0))
        m.face([(x1, z0, eave), (x1, z1, eave), (x1, zm, ridge)], wall, (1, 0, 0))
    else:
        xm = (x0 + x1) / 2
        a, b = z0 - over, z1 + over
        f([(x0 - over, b, eave - 10), (x0 - over, a, eave - 10), (xm, a, ridge), (xm, b, ridge)], roof, (-1, 0, 1))
        f([(x1 + over, a, eave - 10), (x1 + over, b, eave - 10), (xm, b, ridge), (xm, a, ridge)], roof, (1, 0, 1))
        m.face([(x0, z0, eave), (x1, z0, eave), (xm, z0, ridge)], wall, (0, -1, 0))
        m.face([(x1, z1, eave), (x0, z1, eave), (xm, z1, ridge)], wall, (0, 1, 0))


def deck_union(m, rects, y, top, side, abut=(), bottom=BED_Y, size=130.0, seg=200.0, cuts=()):
    """Floor at y over the union of rects (tiled; none under the blocks standing on it, `cuts`), and plank sides from
    `bottom` along its outline only, left out where it meets a block in `abut` (ramps, huts) that covers it."""
    xs = sorted({v for r in list(rects) + list(abut) for v in (r[0], r[2])})
    zs = sorted({v for r in list(rects) + list(abut) for v in (r[1], r[3])})
    nx, nz = len(xs) - 1, len(zs) - 1

    def cov(rs, i, j):
        if i < 0 or j < 0 or i >= nx or j >= nz:
            return False
        cx, cz = (xs[i] + xs[i + 1]) / 2, (zs[j] + zs[j + 1]) / 2
        return any(r[0] < cx < r[2] and r[1] < cz < r[3] for r in rs)
    on = [[cov(rects, i, j) for j in range(nz)] for i in range(nx)]
    ab = [[cov(abut, i, j) for j in range(nz)] for i in range(nx)]

    def solid(i, j):
        return 0 <= i < nx and 0 <= j < nz and (on[i][j] or ab[i][j])
    for j in range(nz):
        run = None
        for i in range(nx + 1):
            if i < nx and on[i][j]:
                run = xs[i] if run is None else run
            elif run is not None:
                for r in C.rects_minus((run, zs[j], xs[i], zs[j + 1]), list(cuts)):
                    tiled(m, r[0], r[1], r[2], r[3], y, top, size=size)
                run = None

    def wall(a, b, facing):
        L = math.hypot(b[0] - a[0], b[1] - a[1])
        n = max(1, math.ceil(L / seg))
        for k in range(n):
            p = (a[0] + (b[0] - a[0]) * k / n, a[1] + (b[1] - a[1]) * k / n)
            q = (a[0] + (b[0] - a[0]) * (k + 1) / n, a[1] + (b[1] - a[1]) * (k + 1) / n)
            m.face([(p[0], p[1], bottom), (q[0], q[1], bottom), (q[0], q[1], y), (p[0], p[1], y)], side, facing)
    for i in range(nx):
        for j in range(nz):
            if not on[i][j]:
                continue
            if not solid(i - 1, j):
                wall((xs[i], zs[j]), (xs[i], zs[j + 1]), (-1, 0, 0))
            if not solid(i + 1, j):
                wall((xs[i + 1], zs[j]), (xs[i + 1], zs[j + 1]), (1, 0, 0))
            if not solid(i, j - 1):
                wall((xs[i], zs[j]), (xs[i + 1], zs[j]), (0, -1, 0))
            if not solid(i, j + 1):
                wall((xs[i], zs[j + 1]), (xs[i + 1], zs[j + 1]), (0, 1, 0))
    for r in rects:
        hole(r)


RAMPS = []


def ramp(m, x0, z0, x1, z1, low, y_lo=2.0, y_hi=DECK_Y):
    """Planks from a deck down to the water on the side `low` (n, s, e, w); its sides from the marsh bed."""
    along = "x" if low in "ew" else "z"
    ya, yb = (y_lo, y_hi) if low in "wn" else (y_hi, y_lo)
    skip = {"w": "e", "e": "w", "n": "s", "s": "n"}[low]
    block(m, x0, z0, x1, z1, BED_Y, ya, DARK, PLANK, which="nsew".replace(skip, ""), size=130.0, y1b=yb, along=along)
    RAMPS.append((x0, z0, x1, z1))
    hole((x0, z0, x1, z1))


def mound(m, x0, z0, x1, z1, edge, peak, top, side, step=100.0):
    """A mud bank: a plain grid of squares (step) rising from `edge` at its rim to `peak` in its middle, its rim a
    bank from the marsh bed (edge - BED_Y high: a step out of the water)."""
    nx, nz = max(1, round((x1 - x0) / step)), max(1, round((z1 - z0) / step))

    def h(x, z):
        u, v = (x - x0) / (x1 - x0), (z - z0) / (z1 - z0)
        return edge + (peak - edge) * math.sin(math.pi * min(1, max(0, u))) * math.sin(math.pi * min(1, max(0, v)))
    gx = [x0 + (x1 - x0) * i / nx for i in range(nx + 1)]
    gz = [z0 + (z1 - z0) * j / nz for j in range(nz + 1)]
    for i in range(nx):
        for j in range(nz):
            a, b, c, d = (gx[i], gz[j]), (gx[i + 1], gz[j]), (gx[i + 1], gz[j + 1]), (gx[i], gz[j + 1])
            m.face([(p[0], p[1], h(*p)) for p in (a, b, c, d)], top, (0, 0, 1))
    C.walls(m, x0, z0, x1, z1, BED_Y, edge, side, step=step)
    hole((x0, z0, x1, z1))
    return h


def lantern(m, x, z, y, h=170.0):
    """A lantern post: a dark post and a lit box on top (the bake's lamp list warms round it)."""
    post(m, x, z, 6, y, y + h, DARK, n=4, phase=math.pi / 4)
    m.box(x - 13, z - 13, x + 13, z + 13, y + h, y + h + 30, WINDOW, DARK)
    m.box(x - 17, z - 17, x + 17, z + 17, y + h + 30, y + h + 38, DARK)


def window(m, plane, c, u, v, out, w=44.0, h=60.0):
    """A lit window picture on a wall in plane x = c or z = c, 4 out from it (towards `out`, +1 or -1)."""
    if plane == "z":
        zz = c + 4 * out  # the decal's back 2 behind it: clear of the wall
        C.decal(m, [(u - w / 2, zz, v), (u + w / 2, zz, v), (u + w / 2, zz, v + h), (u - w / 2, zz, v + h)], WINDOW)
    else:
        xx = c + 4 * out
        C.decal(m, [(xx, u - w / 2, v), (xx, u + w / 2, v), (xx, u + w / 2, v + h), (xx, u - w / 2, v + h)], WINDOW)


# ================================================================================================ the boardwalks
dk = mesh("boardwalks")
JETTY = (-200, 1600, 200, 1900)          # A. the landing jetty's head
BW1 = (0, 1000, 200, 1600)                # the jetty's walk north to the crossing
CROSS = (-1200, 800, 1000, 1000)          # B. the reed beds' crossing: west to the huts, east to the rest
N1 = (-1200, 400, -1000, 800)             # up to the hut plaza
PLAZA = (-1600, 0, -1000, 400)            # C. the hut plaza (the slickers' fight)
N2 = (-1200, -500, -1000, 0)              # on north to the mud islands
DE = (-200, -600, 400, -400)              # D -> E: the islands' landing to the chapel
LE = (400, -800, 600, -300)               # E. the chapel's landing (its west door)
SEF = (400, -300, 600, 400)               # E -> F, south
FS = (800, 600, 1000, 800)                # F -> B, the rest's south walk to the crossing
GBW = (-200, -1400, 0, -600)              # the gate boardwalk north from the crossing of DE
GATE = (-400, -1900, 600, -1400)          # G. the gate platform
DECKS = [JETTY, BW1, CROSS, N1, PLAZA, N2, DE, LE, SEF, FS, GBW, GATE]

# blocks that meet the decks (their sides are left out there)
L1 = (-1800, -500, -1600, -300)           # the lookout hut with the stair up its side (Tribal 1 on its roof)
L1_STAIR = (-1600, -400, -1400, 0)        # its stair: 240 at z -400 down to the plaza (60) at z 0, 24 degrees
L1_LAND = (-1600, -500, -1400, -400)      # the stair's top landing at 240
L2 = (-1800, 100, -1600, 300)             # the second lookout hut, on the plaza's west edge
H1_RAMP = (-1600, 400, -1400, 600)        # up to the big hut's door (60 -> 120)
FREST = (600, 200, 1000, 600)             # F. the fishers' rest at 80
NAVE = (600, -800, 1300, -400)            # E. the chapel's footprint
BELL_RAMP = (400, -1100, 600, -800)       # the bell tower's stair: 60 at z -800 to 180 at z -1100
BELL_LAND = (400, -1200, 600, -1100)      # its top landing at 180
TOWER = (200, -1200, 400, -900)           # the bell tower (its top is the loft, 180)
WALL = (-2250, -1950, 2050, -1900)        # the town wall

ramp(dk, -400, 1700, -200, 1800, "w")     # off the jetty's head
ramp(dk, -200, 1200, 0, 1300, "w")        # off the jetty's walk
ramp(dk, -800, 600, -600, 800, "n")       # off the crossing
ramp(dk, -600, 1000, -400, 1200, "s")
ramp(dk, 600, 1000, 800, 1200, "s")
ramp(dk, 400, 600, 600, 800, "n")
ramp(dk, -400, 600, -200, 800, "n")
ramp(dk, -1000, -200, -800, -100, "e")    # off the walk north from the plaza
ramp(dk, 0, -400, 200, -200, "s")         # off DE
ramp(dk, -400, -1100, -200, -1000, "w")   # off the gate boardwalk
ramp(dk, 0, -1300, 200, -1200, "e")
ramp(dk, 200, -100, 400, 0, "w")          # off the walk south from the chapel
ramp(dk, -400, -1400, -200, -1200, "s")   # off the gate platform's front
ISL_RAMP = (-1000, -500, -800, -400)      # the plaza walk down onto the island (60 -> 20)
block(dk, *ISL_RAMP, BED_Y, DECK_Y, DARK, PLANK, which="ns", size=130.0, y1b=20.0, along="x")
hole(ISL_RAMP)
ISL_UP = (-400, -600, -200, -400)          # off the island up onto DE (20 -> 60)
block(dk, *ISL_UP, BED_Y, 20.0, DARK, PLANK, which="ns", size=130.0, y1b=DECK_Y, along="x")
hole(ISL_UP)

# the cover standing on the decks (no floor under it): the plaza's crates and barrels, the gate's sandbags and carts
PLAZA_REGION = (-1560, 40, -1040, 360)
COVER_C = [(-1450, 130), (-1450, 290), (-1290, 280), (-1140, 130)]
GATE_REGION = (-360, -1860, 560, -1440)
COVER_G = [(-250, -1540, "s"), (150, -1520, "c"), (420, -1560, "s"), (-80, -1680, "c"), (280, -1700, "s"),
           (-260, -1790, "s"), (460, -1780, "c")]
CUTS = [(x - 45, z - 45, x + 45, z + 45) if k % 2 == 0 else (x - 30, z - 30, x + 30, z + 30)
        for k, (x, z) in enumerate(COVER_C)]
CUTS += [(x - 60, z - 40, x + 60, z + 40) if kind == "s" else (x - 70, z - 45, x + 70, z + 45)
         for (x, z, kind) in COVER_G]
ABUT = RAMPS + [ISL_RAMP, ISL_UP, L1_STAIR, L2, H1_RAMP, FREST, NAVE, BELL_RAMP, WALL]
deck_union(dk, DECKS, DECK_Y, PLANK, DARK, abut=ABUT, cuts=CUTS)
# pilings along the walks' sides (looks), every 200, just proud of the plank sides
for (x0, z0, x1, z1) in (BW1, N1, N2, GBW, SEF):
    for z in range(int(z0) + 200, int(z1), 400):
        for x in (x0 - 6, x1 + 6):
            post(dk, x, z, 7, BED_Y, DECK_Y + 30, DARK, n=4)
for (x0, z0, x1, z1) in (CROSS, DE):
    for x in range(int(x0) + 200, int(x1), 400):
        if any(r[0] - 10 <= x <= r[2] + 10 for r in RAMPS) or -200 <= x <= 200:
            continue
        for z in (z0 - 6, z1 + 6):
            post(dk, x, z, 7, BED_Y, DECK_Y + 30, DARK, n=4)
dk.build()

# ================================================================================================ A. the landing jetty
a = mesh("jetty")
spots["start"] = (100, DECK_Y, 1800)
spots["chest"] = (-120, DECK_Y, 1680)      # the machine gun chest, facing the start
lantern(a, -150, 1650, DECK_Y)
spots["lantern_jetty"] = (-150, DECK_Y + 185, 1650)
# the colony's sign: two posts and a board with the emblem, facing north (the way the hero goes)
post(a, -150, 1860, 6, DECK_Y, DECK_Y + 170, DARK, n=4)
post(a, -30, 1860, 6, DECK_Y, DECK_Y + 170, DARK, n=4)
C.decal(a, [(-30, 1862, DECK_Y + 80), (-150, 1862, DECK_Y + 80), (-150, 1862, DECK_Y + 160),
            (-30, 1862, DECK_Y + 160)], EMBLEM)
# the heroes' ship, tied up east of the jetty: a hull (square below the waterline, its bow drawn in above it), a
# deck at 150, a cabin with lit windows, a mast
SHIP = hole((400, 1500, 600, 1900))
a.box(400, 1500, 600, 1900, BED_Y, 40, DARK)
hull = [(400, 1900), (600, 1900), (600, 1600), (560, 1530), (500, 1500), (440, 1530), (400, 1600)]
for k in range(len(hull)):
    p, q = hull[k], hull[(k + 1) % len(hull)]
    cx = sum(h[0] for h in hull) / len(hull)
    cz = sum(h[1] for h in hull) / len(hull)
    a.face([(p[0], p[1], 40), (q[0], q[1], 40), (q[0], q[1], 150), (p[0], p[1], 150)], DARK,
           ((p[0] + q[0]) / 2 - cx, (p[1] + q[1]) / 2 - cz, 0))
a.face([(p[0], p[1], 150) for p in hull], DECK, (0, 0, 1))
a.box(445, 1700, 555, 1840, 150, 240, DARK, THATCH)
window(a, "x", 445, 1770, 175, -1)
window(a, "x", 555, 1770, 175, 1)
post(a, 500, 1640, 8, 150, 480, DARK, n=6)
a.box(470, 1630, 530, 1650, 380, 390, DARK)  # a spar
# mooring posts on the jetty's east edge
for z in (1650, 1850):
    post(a, 190, z, 9, DECK_Y, DECK_Y + 45, DARK, n=6)
a.build()

# ================================================================================================ B. reeds in the water
rd = mesh("reeds", uv=120.0)
REEDS = []
tries = 0
while len(REEDS) < 24 and tries < 4000:
    tries += 1
    if len(REEDS) < 13:
        x, z = rnd.uniform(-650, 650), rnd.uniform(420, 1500)      # the reed beds
    else:
        x, z = rnd.uniform(-1900, 1700), rnd.uniform(-1800, 1900)  # scattered through the marsh
    if not (MARSH[0] + 80 < x < MARSH[2] - 80 and MARSH[1] + 80 < z < MARSH[3] - 80):
        continue
    if any(r[0] - 70 < x < r[2] + 70 and r[1] - 70 < z < r[3] + 70 for r in HOLES + [NAVE, TOWER, L1, L2, FREST,
                                                                                    (-1600, 600, -1200, 900)]):
        continue
    if any(math.hypot(x - p[0], z - p[1]) < 140 for p in REEDS):
        continue
    REEDS.append((x, z))
    hgt = rnd.uniform(80, 120)
    post(rd, x, z, rnd.uniform(20, 28), BED_Y, hgt, REED, n=4, phase=rnd.uniform(0, 1.5))
spots["reeds"] = REEDS
rd.build()

# ================================================================================================ C. the hut cluster
hc = mesh("huts")
# the plaza's cover (squad 2): two crate stacks and two water barrels, about 100 tall, 90 across
for k, (x, z) in enumerate(COVER_C):
    if k % 2 == 0:
        hc.box(x - 45, z - 45, x + 45, z + 45, DECK_Y - 2, DECK_Y + 110, DARK, DECK)
    else:
        post(hc, x, z, 46, DECK_Y - 2, DECK_Y + 105, DARK, n=8, phase=math.pi / 8)
        post(hc, x, z, 49, DECK_Y + 40, DECK_Y + 52, DARK, n=8, cap=False, phase=math.pi / 8)  # a hoop
spots["cover_plaza"] = COVER_C
spots["plaza_region"] = PLAZA_REGION
lantern(hc, -1020, 20, DECK_Y)
lantern(hc, -1580, 380, DECK_Y)
spots["lanterns_plaza"] = [(-1020, DECK_Y + 185, 20), (-1580, DECK_Y + 185, 380)]

# L1: the lookout hut with the stair (a solid base to 240: dark pilings below, plank walls above, a flat roof deck)
ROOF_Y = 240.0
x0, z0, x1, z1 = L1
C.walls(hc, x0, z0, x1, z1, BED_Y, ROOF_Y, DARK, which="nsw")
C.walls(hc, x0, -300 - 100, x1, z1, BED_Y, ROOF_Y, DARK, which="e")  # its east side beside the stair (z -400..-300)
tiled(hc, x0, z0, x1, z1, ROOF_Y, DECK)
hole(L1)
for (wx, wz) in ((-1700, -300),):
    window(hc, "z", -300, wx, 140, 1)
window(hc, "x", -1800, -400, 140, -1)
# its stair: 240 at the landing (z -400) down to the plaza (60) at z 0; its west side only where L1 isn't
block(hc, *L1_STAIR, BED_Y, ROOF_Y, DARK, PLANK, which="e", size=130.0, y1b=DECK_Y, along="z")
C.walls(hc, -1600, -300, -1400, 0, BED_Y, lambda x, z: ROOF_Y + (DECK_Y - ROOF_Y) * (z + 400) / 400, DARK, which="w")
hole(L1_STAIR)
block(hc, *L1_LAND, BED_Y, ROOF_Y, DARK, DECK, which="ne", size=130.0)
hole(L1_LAND)
# parapets: the stair's open side a plank balustrade (100, no collider: a fall into water is harmless); the roof's and
# landing's outer edges over the water 150 with a collider to 400 over them; the roof's south edge a 20 rim (the
# lookout's line of fire over the plaza)
C.lip(hc, (-1400, 0), (-1400, -400), DECK_Y, ROOF_Y, DARK, h=100, thick=-20, caps=(True, False))
C.lip(hc, (-1400, -400), (-1400, -500), ROOF_Y, ROOF_Y, DARK, h=150, thick=-20, coll_to=400, edges=edges,
      caps=(False, True))
# (a lip starting or ending against another's inner face has no cap there: the two would lie in one plane)
C.lip(hc, (-1420, -500), (-1800, -500), ROOF_Y, ROOF_Y, DARK, h=150, thick=-20, coll_to=400, edges=edges,
      caps=(False, True))
C.lip(hc, (-1800, -480), (-1800, -300), ROOF_Y, ROOF_Y, DARK, h=150, thick=-20, coll_to=400, edges=edges,
      caps=(False, True))
C.lip(hc, (-1780, -300), (-1600, -300), ROOF_Y, ROOF_Y, DARK, h=20, thick=-15, caps=(False, True))
spots["perch_l1"] = (-1690, ROOF_Y, -390)
spots["tribal_l1"] = (-1760, ROOF_Y, -350)
spots["l1_flames"] = (-1760, ROOF_Y, -455)
post(hc, -1760, -455, 14, ROOF_Y, ROOF_Y + 40, STONE, n=6)  # a brazier for the lookout's fire
# L2: the second lookout hut on the plaza's west edge (no way up), a 20 rim round its roof
x0, z0, x1, z1 = L2
C.walls(hc, x0, z0, x1, z1, BED_Y, ROOF_Y, DARK, which="nsw")
C.walls(hc, x0, z0, x1, z1, DECK_Y, ROOF_Y, DARK, which="e")
tiled(hc, x0, z0, x1, z1, ROOF_Y, DECK)
hole(L2)
window(hc, "x", -1600, 200, 120, 1)
window(hc, "x", -1800, 200, 120, -1)
for (p, q, caps) in (((-1600, 100), (-1600, 300), (True, True)), ((-1615, 300), (-1800, 300), (False, True)),
                     ((-1800, 285), (-1800, 100), (False, True)), ((-1785, 100), (-1615, 100), (False, False))):
    C.lip(hc, p, q, ROOF_Y, ROOF_Y, DARK, h=20, thick=15, caps=caps)
spots["perch_l2"] = (-1690, ROOF_Y, 200)
spots["l2_flames"] = (-1760, ROOF_Y, 140)
post(hc, -1760, 140, 14, ROOF_Y, ROOF_Y + 40, STONE, n=6)

# H1: the big hut on stilts over the water (floor 120), its door up a ramp from the plaza; under it the secret
H1 = (-1600, 600, -1200, 900)
HF, HE, HR = 120.0, 300.0, 410.0
x0, z0, x1, z1 = H1
block(hc, *H1_RAMP, BED_Y, DECK_Y, DARK, PLANK, which="ew", size=130.0, y1b=HF, along="z")
C.walls(hc, *H1_RAMP, BED_Y, HF - 22, DARK, which="s")  # its end under the hut's floor
hole(H1_RAMP)
tiled(hc, x0, z0, x1, z1, HF, DECK)
tiled(hc, x0, z0, x1, z1, HF - 22, DARK, facing=(0, 0, -1))  # the floor's underside, seen when wading under it
C.sides(hc, x0, z0, x1, z1, HF - 22, HF, DARK)
for x in (x0 + 15, (x0 + x1) / 2, x1 - 15):
    for z in (z0 + 15, (z0 + z1) / 2, z1 - 15):
        post(hc, x, z, 11, BED_Y, HF - 22, DARK, n=5, cap=False)
DOOR_H1 = (-1560, HF, -1440, HF + 170)
# walls: outer faces, and inner ones 10 in (the inside is seen through the door), the door in the north wall
C.plane_rect(hc, "z", z0, x0, HF, x1, HE, [(DOOR_H1[0], DOOR_H1[1], DOOR_H1[2], DOOR_H1[3])], DARK, (0, -1, 0))
C.plane_rect(hc, "z", z0 + 10, x0 + 10, HF, x1 - 10, HE, [(DOOR_H1[0], DOOR_H1[1], DOOR_H1[2], DOOR_H1[3])], DARK,
             (0, 1, 0))
for (xa, xb) in ((DOOR_H1[0], DOOR_H1[0]), (DOOR_H1[2], DOOR_H1[2])):  # the door's reveal
    hc.face([(xa, z0, HF), (xa, z0 + 10, HF), (xa, z0 + 10, HF + 170), (xa, z0, HF + 170)], DARK,
            (1 if xa == DOOR_H1[0] else -1, 0, 0))
hc.face([(DOOR_H1[0], z0, HF + 170), (DOOR_H1[2], z0, HF + 170), (DOOR_H1[2], z0 + 10, HF + 170),
         (DOOR_H1[0], z0 + 10, HF + 170)], DARK, (0, 0, -1))
C.walls(hc, x0, z0, x1, z1, HF, HE, DARK, which="sew")
C.walls(hc, x0 + 10, z0 + 10, x1 - 10, z1 - 10, HF, HE, DARK, which="sew", inward=True)
C.ceiling(hc, x0 + 10, z0 + 10, x1 - 10, z1 - 10, HE, DARK)
gable(hc, x0, z0, x1, z1, HE, HR, DARK, THATCH, along="x")
for wx in (-1500, -1300):
    window(hc, "z", z1, wx, 190, 1)
    window(hc, "z", z1 - 10, wx, 190, -1)
window(hc, "x", x0, 750, 190, -1)
window(hc, "x", x0 + 10, 750, 190, 1)
spots["tribal_h1"] = (-1280, HF, 820)
spots["health_h1"] = (-1520, HF, 820)
spots["secret"] = [(-1430, BED_Y, 740), (-1370, BED_Y, 760)]  # under the big hut, between its stilts
# two closed huts beyond the plaza, for the cluster's look (on pilings in the water: no way in)
for (hx0, hz0, hx1, hz1, along) in ((-2000, -200, -1800, 0, "z"),):
    hole((hx0, hz0, hx1, hz1))
    C.walls(hc, hx0, hz0, hx1, hz1, BED_Y, 60, DARK)
    C.walls(hc, hx0, hz0, hx1, hz1, 60, 220, DARK)
    gable(hc, hx0, hz0, hx1, hz1, 220, 320, DARK, THATCH, along=along)
    window(hc, "x", hx1, (hz0 + hz1) / 2, 120, 1)
hc.build()

# ================================================================================================ D. the mud islands
mi = mesh("islands", uv=220.0)
ISL = (-800, -900, -400, -300)
h_isl = mound(mi, *ISL, 20.0, 40.0, MUD, BANK)
COVER_D = [(-700, -780), (-500, -780), (-700, -440), (-500, -440)]
for k, (x, z) in enumerate(COVER_D):
    C.boulder(mi, x, z, h_isl(x, z), 45, 108, 40 + k, BANK)
spots["cover_islands"] = COVER_D
spots["island_region"] = (-780, -880, -420, -320)
LAST = (-800, -1200, -600, -1000)
h_last = mound(mi, *LAST, 20.0, 32.0, MUD, BANK)
spots["last_bank"] = [(-740, h_last(-740, -1100), -1100), (-660, h_last(-660, -1100), -1100)]
C.boulder(mi, -720, -1160, h_last(-720, -1160), 22, 30, 51, BANK)  # a stone on the bank, for the look
mi.build()

# ================================================================================================ E. the leaning chapel
ch = mesh("chapel", uv=220.0)
A = math.radians(9.0)                      # it leans east, sinking at its altar end
X0, Y0, ZC = 600.0, DECK_Y, -600.0          # the west door's sill
VI, VO = 180.0, 200.0                       # inner and outer half width
H, RIDGE = 380.0, 500.0                     # walls' height and the ridge over the floor (local)


def T(u, v, w):
    """The chapel's own frame (u east along the nave, v south across it, w up from its floor) to game (x, z, y)."""
    return (X0 + u * math.cos(A) + w * math.sin(A), ZC + v, Y0 - u * math.sin(A) + w * math.cos(A))


def lf(m, pts, mt, facing=None):
    f = None
    if facing is not None:
        fu, fv, fw = facing
        f = (fu * math.cos(A) + fw * math.sin(A), fv, -fu * math.sin(A) + fw * math.cos(A))
    m.face([T(*p) for p in pts], mt, f)


def w_at(u, y):
    """The local height w at u where the world height is y."""
    return (y - Y0 + u * math.sin(A)) / math.cos(A)


def floor_y(x):
    return Y0 - (x - X0) / math.cos(A) * math.sin(A)


# the nave's length: its east wall meets the water's surface at x 1300 (the edge of its hole in the water)
lo, hi = 600.0, 800.0
for _ in range(60):
    L = (lo + hi) / 2
    if T(L, 0, w_at(L, WATER_Y))[0] < NAVE[2]:
        lo = L
    else:
        hi = L
L = (lo + hi) / 2
U0 = Y0 / math.sin(A)       # where the floor meets the water's surface inside
UD = 560.0                   # the dais's west face (130 of dais before the east wall)
# the slice where the walls' foot (world y -40) comes back to x = X0
lo2, hi2 = 0.0, 60.0
for _ in range(60):
    u = (lo2 + hi2) / 2
    if T(u, 0, w_at(u, BED_Y))[0] < X0:
        lo2 = u
    else:
        hi2 = u
US = (lo2 + hi2) / 2

# the north and south walls: slices along the nave from the marsh bed (y -40) to w = H, outer and inner faces
cuts_u = C.cuts(US, L, 140.0)
for side in (-1, 1):
    vo, vi = side * VO, side * VI
    face_o, face_i = (0, side, 0), (0, -side, 0)
    # the first sliver at the west end, down to the sill and the landing's edge
    ch.face([T(0, vo, 0), T(US, vo, w_at(US, BED_Y)), T(US, vo, H), T(0, vo, H)], STONE, (0, side, 0))
    for ua, ub in zip(cuts_u, cuts_u[1:]):
        lf(ch, [(ua, vo, w_at(ua, BED_Y)), (ub, vo, w_at(ub, BED_Y)), (ub, vo, H), (ua, vo, H)], STONE, face_o)
    for ua, ub in zip(C.cuts(20.0, L - 20, 140.0), C.cuts(20.0, L - 20, 140.0)[1:]):
        lf(ch, [(ua, vi, 0), (ub, vi, 0), (ub, vi, H), (ua, vi, H)], STONE, face_i)
    lf(ch, [(0, vo, H), (L, vo, H), (L, vi, H), (0, vi, H)], STONE, (0, 0, 1))  # the wall's top
    # lit windows, outside and in
    for uw in (160, 300, 440):
        for (vv, out) in ((vo + side * 4, side), (vi - side * 4, -side)):
            pts = [(uw - 25, vv, 190), (uw + 25, vv, 190), (uw + 25, vv, 290), (uw - 25, vv, 290)]
            C.decal(ch, [T(*p) for p in pts], WINDOW)
# the west wall (the door in it: 160 wide, 200 high) and the east wall, with their gables
DOOR_V, DOOR_W = 80.0, 200.0
for (uo, ui, sgn) in ((0.0, 20.0, -1), (L, L - 20, 1)):
    for (uu, vv, f) in ((uo, VO, sgn), (ui, VI, -sgn)):
        bot = 0.0 if sgn < 0 else (w_at(uu, BED_Y) if uu == L else 0.0)
        if sgn < 0:
            lf(ch, [(uu, -vv, bot), (uu, -DOOR_V, bot), (uu, -DOOR_V, H), (uu, -vv, H)], STONE, (f, 0, 0))
            lf(ch, [(uu, DOOR_V, bot), (uu, vv, bot), (uu, vv, H), (uu, DOOR_V, H)], STONE, (f, 0, 0))
            lf(ch, [(uu, -DOOR_V, DOOR_W), (uu, DOOR_V, DOOR_W), (uu, DOOR_V, H), (uu, -DOOR_V, H)], STONE, (f, 0, 0))
        else:
            for va, vb in ((-vv, 0.0), (0.0, vv)):
                lf(ch, [(uu, va, bot), (uu, vb, bot), (uu, vb, H), (uu, va, H)], STONE, (f, 0, 0))
        lf(ch, [(uu, -vv, H), (uu, vv, H), (uu, 0, RIDGE - 10)], STONE, (f, 0, 0))
for vv in (-DOOR_V, DOOR_V):  # the door's reveal and lintel
    lf(ch, [(0, vv, 0), (20, vv, 0), (20, vv, DOOR_W), (0, vv, DOOR_W)], STONE, (0, -vv, 0))
lf(ch, [(0, -DOOR_V, DOOR_W), (20, -DOOR_V, DOOR_W), (20, DOOR_V, DOOR_W), (0, DOOR_V, DOOR_W)], STONE, (0, 0, -1))
# the roof: two slopes outside; inside, a ceiling 20 under the walls' tops (a roof's own underside lies close
# enough over its top to read as a folded floor)
for ua, ub in zip(C.cuts(-25, L + 25, 200.0), C.cuts(-25, L + 25, 200.0)[1:]):
    for sv in (-1, 1):
        lf(ch, [(ua, sv * (VO + 25), H - 15), (ub, sv * (VO + 25), H - 15), (ub, 0, RIDGE), (ua, 0, RIDGE)], SLATE,
           (0, sv, 1))
for ua, ub in zip(C.cuts(20, L - 20, 200.0), C.cuts(20, L - 20, 200.0)[1:]):
    for v0_, v1_ in ((-VI, 0.0), (0.0, VI)):
        lf(ch, [(ua, v0_, H - 20), (ub, v0_, H - 20), (ub, v1_, H - 20), (ua, v1_, H - 20)], DARK, (0, 0, -1))
# the floor: flagstones in squares from the door to the dais, the water's shoreline on a square's edge
ch_floor = []
for (ua, ub) in ((20.0, U0), (U0, UD)):
    us = C.cuts(ua, ub, 130.0)
    for u0_, u1_ in zip(us, us[1:]):
        for v0_, v1_ in ((-VI, 0.0), (0.0, VI)):
            lf(ch, [(u0_, v0_, 0), (u1_, v0_, 0), (u1_, v1_, 0), (u0_, v1_, 0)], FLAGS, (0, 0, 1))
lf(ch, [(0, -DOOR_V, 0), (20, -DOOR_V, 0), (20, DOOR_V, 0), (0, DOOR_V, 0)], FLAGS, (0, 0, 1))  # the sill
# the cover for squad 6: three stone pew-ends (80 across, about 110 over the floor), upright on the sloping floor
NAVE_REGION = (625, -765, 975, -435)
COVER_E = [(690, -690), (800, -510), (910, -690)]
for (x, z) in COVER_E:
    ch.box(x - 40, z - 40, x + 40, z + 40, floor_y(x + 40) - 6, floor_y(x) + 110, STONE, FLAGS)
spots["cover_nave"] = COVER_E
spots["nave_region"] = NAVE_REGION
# the flooded east end: water from the shoreline to the dais; broken pews standing in it
X_SHORE, X_DAIS = T(U0, 0, 0)[0], T(UD, 0, 0)[0]
PEWS = [(1040, -770, 1080, -650), (1040, -550, 1080, -430)]
for (px0, pz0, px1, pz1) in PEWS:
    ch.box(px0, pz0, px1, pz1, floor_y(px1) - 6, 18, DARK, DECK)
xs_in = C._cuts(X_SHORE, X_DAIS, [1000.0] + [v for p in PEWS for v in (p[0], p[2])], 200.0)
zs_in = C._cuts(ZC - VI, ZC + VI, [v for p in PEWS for v in (p[1], p[3])], 100.0)
for i in range(len(xs_in) - 1):
    for j in range(len(zs_in) - 1):
        u0_, u1_, v0_, v1_ = xs_in[i], xs_in[i + 1], zs_in[j], zs_in[j + 1]
        cx, cz = (u0_ + u1_) / 2, (v0_ + v1_) / 2
        if any(p[0] < cx < p[2] and p[1] < cz < p[3] for p in PEWS):
            continue
        wtr.face([(u0_, v0_, WATER_Y), (u1_, v0_, WATER_Y), (u1_, v1_, WATER_Y), (u0_, v1_, WATER_Y)], WATER, (0, 0, 1))
# the altar dais at the east end, out of the water (25), the altar on it
DAIS_Y = 25.0
X_EAST = T(L - 20, 0, w_at(L - 20, DAIS_Y))[0]
block(ch, X_DAIS, ZC - VI + 5, X_EAST + 4, ZC + VI - 5, floor_y(X_DAIS) - 6, DAIS_Y, STONE, FLAGS, which="w")
ch.box(X_EAST - 60, ZC - 60, X_EAST - 15, ZC + 60, DAIS_Y, DAIS_Y + 55, STONE, FLAGS)  # the altar
spots["key"] = ((X_DAIS + X_EAST - 60) / 2, DAIS_Y, ZC)  # on the dais before the altar
spots["candles"] = [(X_EAST - 38, DAIS_Y + 55, ZC - 45), (X_EAST - 38, DAIS_Y + 55, ZC + 45)]
spots["chapel_door"] = (X0, DECK_Y, ZC)
spots["chapel_inside"] = (X0 + 60, DECK_Y, ZC)
hole(NAVE)
spots["nave"] = {"L": L, "U0": U0, "x_shore": X_SHORE, "x_dais": X_DAIS, "x_east": X_EAST}

# the bell tower (upright: it stands on firmer ground) north of the landing; its loft at 180 up an outside stair
x0, z0, x1, z1 = TOWER
LOFT = 180.0
C.walls(ch, x0, z0, x1, z1, BED_Y, LOFT, STONE)
tiled(ch, x0, z0, x1, z1, LOFT, DECK)
hole(TOWER)
block(ch, *BELL_RAMP, BED_Y, LOFT, DARK, PLANK, which="e", size=130.0, y1b=DECK_Y, along="z")
C.walls(ch, 400, -900, 600, -800, BED_Y, lambda x, z: LOFT + (DECK_Y - LOFT) * (z + 1100) / 300, DARK, which="w")
hole(BELL_RAMP)
block(ch, *BELL_LAND, BED_Y, LOFT, DARK, DECK, which="ne", size=130.0)
hole(BELL_LAND)
for (cx, cz) in ((x0 + 15, z0 + 15), (x1 - 15, z0 + 15), (x0 + 15, z1 - 15), (x1 - 15, z1 - 15)):
    ch.box(cx - 12, cz - 12, cx + 12, cz + 12, LOFT, 398, STONE)  # into the spire, not flush with its underside
RING = [(x0 - 20, z0 - 20), (x1 + 20, z0 - 20), (x1 + 20, z1 + 20), (x0 - 20, z1 + 20)]
for k in range(4):
    p, q = RING[k], RING[(k + 1) % 4]
    ch.face([(p[0], p[1], 390), (q[0], q[1], 390), ((x0 + x1) / 2, (z0 + z1) / 2, 470)], SLATE,
            ((p[0] + q[0]) / 2 - (x0 + x1) / 2, (p[1] + q[1]) / 2 - (z0 + z1) / 2, 1))
ch.face([(x0 - 20, z0 - 20, 390), (x1 + 20, z0 - 20, 390), (x1 + 20, z1 + 20, 390), (x0 - 20, z1 + 20, 390)], SLATE,
        (0, 0, -1))  # under the spire's roof
ch.box(270, -1080, 330, -1020, 300, 360, ASHLAR)  # the bell
post(ch, 300, -1050, 3, 360, 400, DARK, n=4, cap=False)
# balustrades (100, no collider: a fall is 220 into the water at most)
C.lip(ch, (x0, z1), (x0, z0), LOFT, LOFT, STONE, h=100, thick=20)
C.lip(ch, (x0 + 20, z0), (600, z0), LOFT, LOFT, STONE, h=100, thick=20, caps=(False, True))
C.lip(ch, (600, z0 + 20), (600, -1100), LOFT, LOFT, DARK, h=100, thick=20, caps=(False, False))
C.lip(ch, (x1, z1), (x0 + 20, z1), LOFT, LOFT, STONE, h=100, thick=20, caps=(True, False))
C.lip(ch, (x1, -1100), (x1, z1 - 20), LOFT, LOFT, STONE, h=100, thick=20, caps=(True, False))
C.lip(ch, (600, -1100), (600, -800), LOFT, DECK_Y, DARK, h=100, thick=20, caps=(False, True))
spots["tribal_loft"] = (240, LOFT, -1150)
spots["loft_lamp"] = (380, LOFT, -1180)
ch.build()

# ================================================================================================ F. the fishers' rest
fr = mesh("rest")
x0, z0, x1, z1 = FREST
REST_Y = 80.0
block(fr, x0, z0, x1, z1, BED_Y, REST_Y, DARK, DECK, size=130.0)
hole(FREST)
for (px, pz) in ((x0 + 25, z0 + 25), (x1 - 25, z0 + 25), (x0 + 25, z1 - 25), (x1 - 25, z1 - 25)):
    post(fr, px, pz, 10, REST_Y, 330, DARK, n=6)
gable(fr, x0 + 25, z0 + 25, x1 - 25, z1 - 25, 330, 420, DARK, THATCH, along="x", over=40, both=True)
fr.face([(x0 + 28, z1 - 25, 330), (x0 + 28, z0 + 25, 330), (x0 + 28, (z0 + z1) / 2, 420)], DARK, (1, 0, 0))
fr.face([(x1 - 28, z0 + 25, 330), (x1 - 28, z1 - 25, 330), (x1 - 28, (z0 + z1) / 2, 420)], DARK, (-1, 0, 0))
fr.box(770, 370, 830, 430, REST_Y, REST_Y + 50, STONE)  # the brazier
spots["brazier"] = (800, REST_Y + 50, 400)
spots["rest"] = [(700, REST_Y, 280), (900, REST_Y, 280), (900, REST_Y, 520), (700, REST_Y, 520)]
# nets drying on a rack along the north edge (outside the posts)
for x in (650, 950):
    post(fr, x, 215, 5, REST_Y, REST_Y + 130, DARK, n=4)
C.lip(fr, (650, 212), (950, 212), REST_Y + 120, REST_Y + 120, DARK, h=8, thick=6, under=True)
fr.build()

# ================================================================================================ G. the flood gate and the town wall
g = mesh("gate", uv=220.0)
DOOR_X0, DOOR_X1, DOOR_TOP = 20.0, 180.0, 240.0
# the wall's south face (the marsh side), the gateway in it, a reveal 50 deep, two towers over the gate
C.plane_rect(g, "z", -1900, -2250, BED_Y, 2050, 450, [(DOOR_X0, DECK_Y, DOOR_X1, DOOR_TOP)], ASHLAR, (0, 1, 0))
for x in (DOOR_X0, DOOR_X1):
    g.face([(x, -1950, DECK_Y), (x, -1900, DECK_Y), (x, -1900, DOOR_TOP), (x, -1950, DOOR_TOP)], ASHLAR,
           (1 if x == DOOR_X0 else -1, 0, 0))
g.face([(DOOR_X0, -1950, DOOR_TOP), (DOOR_X1, -1950, DOOR_TOP), (DOOR_X1, -1900, DOOR_TOP),
        (DOOR_X0, -1900, DOOR_TOP)], ASHLAR, (0, 0, -1))
tiled(g, DOOR_X0, -1950, DOOR_X1, -1900, DECK_Y, DECK)
for (xa, xb) in ((-2250, 0), (0, 200), (200, 2050)):
    n = max(1, math.ceil((xb - xa) / 400))
    for k in range(n):
        p, q = xa + (xb - xa) * k / n, xa + (xb - xa) * (k + 1) / n
        g.face([(p, -1900, 450), (q, -1900, 450), (q, -1950, 450), (p, -1950, 450)], ASHLAR, (0, 0, 1))
for (tx0, tx1) in ((-120, DOOR_X0), (DOOR_X1, 320)):
    g.box(tx0, -1990, tx1, -1900, 450, 580, ASHLAR)
    for k in range(2):  # merlons
        mx = tx0 + 20 + k * (tx1 - tx0 - 60)
        g.box(mx, -1990, mx + 40, -1900, 580, 620, ASHLAR)
spots["gate_lamps"] = [(-50, 600, -1880), (250, 600, -1880)]
# the passage beyond the gate, into the town (the exit at its end); its north face of the wall round the doorway
C.plane_rect(g, "z", -1950, 0, DECK_Y, 200, 300, [(DOOR_X0, DECK_Y, DOOR_X1, DOOR_TOP)], ASHLAR, (0, -1, 0))
tiled(g, 0, -2150, 200, -1950, DECK_Y, DECK)
C.walls(g, 0, -2150, 200, -1950, DECK_Y, 300, ASHLAR, which="new", inward=True)
C.ceiling(g, 0, -2150, 200, -1950, 300, DARK)
lantern(g, 30, -2120, DECK_Y, h=150)
spots["gate_door"] = (100.0, DECK_Y, -1925.0)
spots["exit_onward"] = (100.0, DECK_Y, -2105.0)
spots["start_from_2_2"] = (100.0, DECK_Y, -2010.0)
# the gate fight's cover: sandbag walls and carts (about 100 tall, 80 across or more), 7 for 7 members
for (x, z, kind) in COVER_G:
    if kind == "s":
        g.box(x - 60, z - 40, x + 60, z + 40, DECK_Y - 2, DECK_Y + 100, SANDBAG)
    else:
        g.box(x - 70, z - 45, x + 70, z + 45, DECK_Y - 2, DECK_Y + 110, DARK, PLANK)
        for wx in (x - 45, x + 45):  # wheels painted on its sides
            C.decal(g, [(wx - 25, z - 47, DECK_Y), (wx + 25, z - 47, DECK_Y), (wx + 25, z - 47, DECK_Y + 50),
                        (wx - 25, z - 47, DECK_Y + 50)], DARK)
            C.decal(g, [(wx + 25, z + 47, DECK_Y), (wx - 25, z + 47, DECK_Y), (wx - 25, z + 47, DECK_Y + 50),
                        (wx + 25, z + 47, DECK_Y + 50)], DARK)
spots["cover_gate"] = [(x, z) for (x, z, _k) in COVER_G]
spots["gate_region"] = GATE_REGION
lantern(g, -380, -1420, DECK_Y)
lantern(g, 580, -1420, DECK_Y)
spots["lanterns_gate"] = [(-380, DECK_Y + 185, -1420), (580, DECK_Y + 185, -1420)]
lantern(g, 420, -320, DECK_Y)          # the chapel's landing
lantern(g, 180, 820, DECK_Y)           # the crossing
lantern(g, -20, -580, DECK_Y)          # where the gate boardwalk leaves DE
spots["lanterns_more"] = [(420, DECK_Y + 185, -320), (180, DECK_Y + 185, 820), (-20, DECK_Y + 185, -580)]
g.build()

# ================================================================================================ the banks round the marsh
bk = mesh("banks", uv=260.0)
TOP = 360.0
OUT = 150.0
x0, z0, x1, z1 = MARSH
for (za, zb) in zip(C.cuts(-1900, 2000, 400.0), C.cuts(-1900, 2000, 400.0)[1:]):
    bk.face([(x0, za, BED_Y), (x0, zb, BED_Y), (x0 - OUT, zb, TOP), (x0 - OUT, za, TOP)], BANK, (1, 0, 0.3))
    bk.face([(x1, zb, BED_Y), (x1, za, BED_Y), (x1 + OUT, za, TOP), (x1 + OUT, zb, TOP)], BANK, (-1, 0, 0.3))
for (xa, xb) in zip(C.cuts(x0, x1, 400.0), C.cuts(x0, x1, 400.0)[1:]):
    bk.face([(xb, z1, BED_Y), (xa, z1, BED_Y), (xa, z1 + OUT, TOP), (xb, z1 + OUT, TOP)], BANK, (0, -1, 0.3))
bk.face([(x0, z1, BED_Y), (x0 - OUT, z1, TOP), (x0, z1 + OUT, TOP)], BANK, (1, -1, 0.3))
bk.face([(x1, z1, BED_Y), (x1, z1 + OUT, TOP), (x1 + OUT, z1, TOP)], BANK, (-1, -1, 0.3))
bk.face([(x0 - OUT, z1, TOP), (x0 - OUT, z1 + OUT, TOP), (x0, z1 + OUT, TOP)], MOSSG, (0, 0, 1))
bk.face([(x1 + OUT, z1, TOP), (x1, z1 + OUT, TOP), (x1 + OUT, z1 + OUT, TOP)], MOSSG, (0, 0, 1))
# the tops nobody reaches: big squares out to the level's edge
for (za, zb) in zip(C.cuts(-1950, 2000, 400.0), C.cuts(-1950, 2000, 400.0)[1:]):
    bk.face([(-2250, za, TOP), (x0 - OUT, za, TOP), (x0 - OUT, zb, TOP), (-2250, zb, TOP)], MOSSG, (0, 0, 1))
    bk.face([(x1 + OUT, za, TOP), (2050, za, TOP), (2050, zb, TOP), (x1 + OUT, zb, TOP)], MOSSG, (0, 0, 1))
bk.face([(-2250, 2000, TOP), (x0 - OUT, 2000, TOP), (x0 - OUT, 2250, TOP), (-2250, 2250, TOP)], MOSSG, (0, 0, 1))
bk.face([(x1 + OUT, 2000, TOP), (2050, 2000, TOP), (2050, 2250, TOP), (x1 + OUT, 2250, TOP)], MOSSG, (0, 0, 1))
for (xa, xb) in zip(C.cuts(x0 - OUT, x1 + OUT, 400.0), C.cuts(x0 - OUT, x1 + OUT, 400.0)[1:]):
    bk.face([(xa, z1 + OUT, TOP), (xb, z1 + OUT, TOP), (xb, 2250, TOP), (xa, 2250, TOP)], MOSSG, (0, 0, 1))
# dead trees along the bank tops (silhouettes against the storm)
for k in range(9):
    side = k % 3
    if side == 0:
        x, z = rnd.uniform(-2230, -2170), rnd.uniform(-1700, 1900)
    elif side == 1:
        x, z = rnd.uniform(1970, 2030), rnd.uniform(-1700, 1900)
    else:
        x, z = rnd.uniform(-1800, 1700), rnd.uniform(2170, 2230)
    hgt = rnd.uniform(260, 420)
    post(bk, x, z, 14, TOP - 10, TOP + hgt, DARK, n=4, phase=rnd.uniform(0, 1))
    for b in range(1):
        ang = rnd.uniform(0, math.tau)
        by = TOP + hgt * rnd.uniform(0.5, 0.85)
        ex, ez = x + math.cos(ang) * 90, z + math.sin(ang) * 90
        C.lip(bk, (x, z), (ex, ez), by, by + 50, DARK, h=12, thick=8, under=True)
bk.build()
# colliders behind the bank tops and over the town wall
for (p, q, ya) in (((-2250, -1950), (-2250, 2250), 300), ((2050, -1950), (2050, 2250), 300),
                   ((-2250, 2250), (2050, 2250), 300), ((-2250, -1925), (2050, -1925), 450)):
    collider(edges, p, q, ya, 1300)

# ================================================================================================ beyond the wall: the town, the lighthouse
bd = mesh("backdrop", uv=260.0)
HOUSES = [(-1500, -2300, -1200, -2050, 560, 680, "x"), (-900, -2350, -600, -2100, 600, 720, "z"),
          (-420, -2420, -120, -2220, 540, 660, "x"), (420, -2300, 720, -2050, 580, 700, "z"),
          (1000, -2350, 1300, -2100, 560, 690, "x"), (1500, -2250, 1750, -2050, 520, 640, "z")]
for (hx0, hz0, hx1, hz1, eave, ridge, along) in HOUSES:
    C.walls(bd, hx0, hz0, hx1, hz1, 380, eave, STONE, which="s", step=400.0)
    C.walls(bd, hx0, hz0, hx1, hz1, 380, eave, STONE, which="ew", step=400.0)
    gable(bd, hx0, hz0, hx1, hz1, eave, ridge, STONE, SLATE if hx0 % 2 else THATCH, along=along)
    window(bd, "z", hz1, (hx0 + hx1) / 2, eave - 110, 1, w=40, h=50)
# the market's bell tower behind the town (2.2's landmark)
C.walls(bd, 200, -2800, 420, -2580, 380, 900, STONE, step=400.0)
for k in range(4):
    p = ((200, -2800), (420, -2800), (420, -2580), (200, -2580))[k]
    q = ((420, -2800), (420, -2580), (200, -2580), (200, -2800))[k]
    bd.face([(p[0], p[1], 900), (q[0], q[1], 900), (310, -2690, 1040)], SLATE,
            ((p[0] + q[0]) / 2 - 310, (p[1] + q[1]) / 2 + 2690, 1))
window(bd, "z", -2580, 310, 780, 1, w=60, h=70)
# the lighthouse on its rock, far to the north-east: the storm engine's glow on top (the world's goal)
C.boulder(bd, 1400, -4600, -40, 520, 520, 77, BANK, sides=8, sink=40.0)
post(bd, 1400, -4600, 110, 440, 1500, STONE, n=8, cap=False)
post(bd, 1400, -4600, 135, 1500, 1640, WINDOW, n=8, cap=False)
bd.face([(1400 + 150 * math.cos(k * math.tau / 8), -4600 + 150 * math.sin(k * math.tau / 8), 1640)
         for k in range(8)], SLATE, (0, 0, -1))
for k in range(8):
    a0, a1 = k * math.tau / 8, (k + 1) * math.tau / 8
    bd.face([(1400 + 150 * math.cos(a0), -4600 + 150 * math.sin(a0), 1640),
             (1400 + 150 * math.cos(a1), -4600 + 150 * math.sin(a1), 1640), (1400, -4600, 1800)], SLATE,
            (math.cos((a0 + a1) / 2), math.sin((a0 + a1) / 2), 1))
bd.build()
edges.build()

# ================================================================================================ the marsh water
wb = mesh("marsh_bed", uv=260.0)
ZERO = [(v, MARSH[1], v, MARSH[3]) for v in (-2000, -1000, 0, 1000)] + \
       [(MARSH[0], v, MARSH[2], v) for v in (-1000, 0, 1000, 2000)]
C.water_box(wb, MARSH, HOLES + ZERO, BED_Y, WATER_Y, BED, WATER, wm=wtr)
wb.build()
wtr.build()

# ------------------------------------------------------------------------------------------------ light: the storm
level = [o for o in coll.all_objects if o.type == "MESH"]
SUN_DIR = (0.25, -0.15, -0.95)  # from above, a little from the south-west (Blender space: the light's travel)
WARM = (0.5, 0.32, 0.12)
LAMPS = [
    (-150, 1650, DECK_Y + 200, 300, WARM),            # the jetty's lantern
    (180, 820, DECK_Y + 200, 300, WARM),              # the crossing
    (-1020, 20, DECK_Y + 200, 300, WARM),             # the plaza
    (-1580, 380, DECK_Y + 200, 300, WARM),
    (-1400, 750, 250, 260, (0.55, 0.34, 0.12)),       # inside the big hut
    (-1760, -455, ROOF_Y + 60, 260, (0.6, 0.32, 0.1)),  # the lookouts' fires
    (-1760, 140, ROOF_Y + 60, 260, (0.6, 0.32, 0.1)),
    (-1430, 750, 40, 160, (0.3, 0.2, 0.08)),          # a glow under the big hut (the secret)
    (-20, -580, DECK_Y + 200, 300, WARM),             # the gate boardwalk's foot
    (420, -320, DECK_Y + 200, 300, WARM),             # the chapel's landing
    (spots["key"][0] + 60, spots["key"][2], 110, 280, (0.6, 0.38, 0.14)),  # the altar's candles
    (760, -600, 200, 260, (0.25, 0.2, 0.12)),         # the nave's windows
    (300, -1050, 260, 220, (0.45, 0.3, 0.12)),        # the bell loft
    (800, 400, 180, 340, (0.62, 0.32, 0.1)),          # the fishers' brazier
    (-380, -1420, DECK_Y + 200, 300, WARM),           # the gate platform
    (580, -1420, DECK_Y + 200, 300, WARM),
    (-50, -1860, 560, 420, (0.55, 0.3, 0.1)),         # the gate towers' fires
    (250, -1860, 560, 420, (0.55, 0.3, 0.1)),
    (40, -2100, 230, 200, WARM),                      # the passage beyond the gate
    (500, 1770, 220, 200, (0.4, 0.3, 0.15)),          # the ship's cabin
]


def extra(x, z, y, mname):
    if mname.startswith("game_1959") or mname.startswith("game_0CB0") or mname.startswith("game_1958"):
        k = max(0.0, min(1.0, (y + 40) / 80.0))  # wet mud and rock darker near and under the water
        return (0.72 + 0.28 * k, 0.75 + 0.25 * k, 0.8 + 0.2 * k)
    if mname.startswith("lit_window"):
        return (2.2, 2.0, 1.6)  # the windows glow
    if y > 1450 and z < -4000:
        return (2.0, 2.2, 2.6)  # the lighthouse's lamp room: the storm engine's cold glow
    return (1.0, 1.0, 1.0)


TINTS = {"game_1736": (0.95, 1.0, 0.95), "game_0828": (0.95, 0.97, 1.0), "game_0000": (0.9, 0.95, 0.85),
         "game_193D": (0.7, 0.68, 0.66), "game_16D9": (0.72, 0.72, 0.75)}  # rain-dark boards
C.bake(level, SUN_DIR, (0.5, 0.55, 0.6), (0.25, 0.3, 0.35), tints=TINTS, lamps=LAMPS, extra=extra,
       soft={"game_193D": (0.5, 0.3), "game_0CB0": (0.5, 0.3), "game_1959": (0.5, 0.3)})
# the flood water (the bake leaves water out): murky, a dull green-grey over its own texture
wme = bpy.data.objects["marsh_water"].data
wcol = wme.color_attributes.get("Col") or wme.color_attributes.new("Col", "BYTE_COLOR", "CORNER")
for d in wcol.data:
    d.color_srgb = (0.5, 0.56, 0.5, 1.0)

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
print("STILTWATER", json.dumps(report))
print("PARTS", json.dumps({o.name: sum(len(p.vertices) - 2 for p in o.data.polygons) for o in level}))
