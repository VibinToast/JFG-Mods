"""Slag Flats (Corsair Reach 3.1, Cinderhold's entry level): builds the level from nothing and exports
blender/out/slagflats.glb.

    blender --background --factory-startup --addons jfg64 --python slagflats.py
Then in JFG-Studio: reimport_geometry (or import the .glb) into the level `slagflats`.

Game coordinates throughout (x east, z south, y up). A canyon run from the south-west onto wide flats crossed by three
lava rivers, then the ore yard and the forge gate in the north-east, rising 0 -> 350:
  A  the landing ledge (0), a small lava pool beside it (lava taught where it is harmless)
  B  the basalt canyon (0 -> 100), 300 wide (450 where squad 1 fights), the machine gun niche, a column stair
  C  the flats (100-200), rivers R1 (x -850), R2 (x 0, from a spring at z -350 into the lake bay), R3 (x 780), one
     stone bridge each; slag heaps; the lake bay with the lava-walker's island (Juno)
  D  the ore yard (220): rails, ore carts, the gantry with the rail signal, the office; the switch gate north
  E  the forge gate court (350) up a ramp: the foundry's great door, the vestibule with the exit
Lava (the kit): a surface 30 over a solid floor, banks 36 high, never on the required path.
"""
import json
import math
import os
import sys

import bpy

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import common as C  # noqa: E402
from common import Mesh, smooth  # noqa: E402
import jfg64  # noqa: E402

NAME = "slagflats"
scene, coll = C.new_scene(NAME)

# ------------------------------------------------------------------------------------------------ materials
ASH = C.game(0x060D)      # ash ground on the flats
CRUST = C.game(0x0C3E)    # cooled lava crust: the landing, the canyon floor, scorched banks
BASALT = C.game(0x0C37)   # basalt cliffs
COLUMN = C.game(0x1660)   # basalt columns
SLAG = C.game(0x07F2)     # slag lumps
LAVA = C.game(0x1547, "lava")
STONE = C.game(0x0A20)    # dressed stone: bridges, plinths
PAVE = C.game(0x08A8)     # the forge court and the vestibule
YARDF = C.game(0x16DF)    # the ore yard's floor
IRON = C.game(0x0B0C)     # carts, gantry, braziers, roofs
BRICK = C.game(0x171C)    # the foundry's facade, the gate wall, the office
EDGE = jfg64.boundary_material()


def sigil_px(x, y):
    """The forge-masters' banner: an anvil under a flame, orange on soot black, a red border (32 x 64)."""
    if x < 2 or x > 29 or y < 2 or y > 61:
        return (0.45, 0.08, 0.04)
    # the swallow-tail at the bottom: black notch
    if y > 52 and abs(x - 15.5) < (y - 52) * 1.3:
        return (0.03, 0.02, 0.02)
    # the flame: a teardrop, yellow core
    fx, fy = x - 15.5, y - 20.0
    flame = (fx * fx) / 30.0 + ((fy + 4) * (fy + 4)) / 110.0 <= 1.0 and fy > -14
    core = (fx * fx) / 8.0 + ((fy + 1) * (fy + 1)) / 30.0 <= 1.0
    if core:
        return (1.0, 0.86, 0.35)
    if flame:
        return (0.95, 0.42, 0.08)
    # the anvil: a top slab, a waist, a foot
    if 33 <= y <= 36 and 6 <= x <= 27 or (y == 33 and 3 <= x < 6):
        return (0.85, 0.36, 0.08)
    if 37 <= y <= 41 and 12 <= x <= 19:
        return (0.85, 0.36, 0.08)
    if 42 <= y <= 45 and 8 <= x <= 23:
        return (0.85, 0.36, 0.08)
    return (0.05, 0.04, 0.04) if (x * 3 + y * 5) % 17 else (0.09, 0.06, 0.05)


def hazard_px(x, y):
    """Hazard stripes: yellow and black diagonals (32 x 16)."""
    return (0.92, 0.72, 0.1) if ((x + y) // 6) % 2 == 0 else (0.06, 0.05, 0.05)


def rails_px(x, y):
    """A rail track from above, across the image: two iron rails over dark sleepers on ballast (32 x 32; the
    track runs along v)."""
    if x in (7, 8, 23, 24):
        return (0.55, 0.52, 0.5) if x in (8, 24) else (0.3, 0.28, 0.27)
    if 3 <= x <= 28 and y % 8 in (2, 3, 4):
        return (0.24, 0.16, 0.11) if (x + y) % 5 else (0.18, 0.12, 0.08)
    g = ((x * 7 + y * 13) % 11) / 11.0
    return (0.28 + 0.1 * g, 0.26 + 0.08 * g, 0.24 + 0.07 * g)


def glow_px(x, y):
    """A furnace-lit window: orange glass in four panes, dark bars (16 x 16)."""
    if x in (0, 15, 7, 8) or y in (0, 15, 7, 8):
        return (0.1, 0.07, 0.05)
    k = 0.8 + 0.2 * math.sin(x * 0.7 + y * 0.4)
    return (1.0 * k, 0.55 * k, 0.15 * k)


SIGIL = C.own_material("forge_sigil", C.own_image("forge_sigil", 32, 64, sigil_px))
HAZARD = C.own_material("hazard_stripes", C.own_image("hazard_stripes", 32, 16, hazard_px))
RAILS = C.own_material("rail_track", C.own_image("rail_track", 32, 32, rails_px), "nocollide")
GLOW = C.own_material("furnace_window", C.own_image("furnace_window", 16, 16, glow_px))

spots = {}  # positions Studio needs (game coords), written to out/slagflats_spots.json


# ------------------------------------------------------------------------------------------------ the plan in numbers
def seg(px, pz, a, b):
    dx, dz = b[0] - a[0], b[1] - a[1]
    L2 = dx * dx + dz * dz
    t = max(0.0, min(1.0, ((px - a[0]) * dx + (pz - a[1]) * dz) / L2))
    return math.hypot(px - (a[0] + t * dx), pz - (a[1] + t * dz)), t, math.sqrt(L2)


CANYON = [(-2150, 1300), (-2080, 650), (-1820, 430), (-1560, 320), (-1430, 300)]
CANYON_LEN = sum(math.hypot(b[0] - a[0], b[1] - a[1]) for a, b in zip(CANYON, CANYON[1:4]))


def canyon_at(x, z):
    """(distance to the canyon's line, arc length along it)."""
    best, s0 = None, 0.0
    for a, b in zip(CANYON, CANYON[1:]):
        d, t, L = seg(x, z, a, b)
        if best is None or d < best[0]:
            best = (d, s0 + t * L)
        s0 += L
    return best


def canyon_hw(s):
    """Half width: 150, widening to 225 where squad 1 fights (s 330..600)."""
    k = smooth((s - 250) / 80.0) * (1 - smooth((s - 600) / 80.0))
    return 150 + 75 * k


def canyon_floor(s):
    return 0.0 if s < 150 else min(100.0, 100.0 * (s - 150) / (CANYON_LEN - 150))


def point_at(s):
    s0 = 0.0
    for a, b in zip(CANYON, CANYON[1:]):
        L = math.hypot(b[0] - a[0], b[1] - a[1])
        if s <= s0 + L:
            t = (s - s0) / L
            return (a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t)
        s0 += L
    return CANYON[-1]


# the rivers: centre x at z, half width, bank level B (lava at B - 6, bed at B - 36)
def cx1(z):
    return -850 + 40 * math.sin(z / 260.0)


def cx2(z):
    return 35 * math.sin(z / 230.0 + 1.0)


def cx3(z):
    return 780 + 40 * math.sin(z / 280.0 + 2.0)


RIVERS = [  # (centre, half width, bank, z start (spring) or None)
    (cx1, 110, 120.0, None),
    (cx2, 95, 150.0, -350.0),
    (cx3, 115, 180.0, None),
]
SPRING_Z = -350.0
LAKE = (-350, 750, 350, 1450)  # the bay south of R2 (rect x0, z0, x1, z1)
ISLAND = (0.0, 1200.0)
BRIDGES = [  # (x0, z0, x1, z1, bank): the deck at bank + 4, a causeway of ground under it
    (-1100, 200, -600, 400, 120.0),
    (-200, 0, 300, 200, 150.0),
    (600, -400, 1000, -200, 180.0),
]
POOL = (-2340, 1560, 130)  # the landing's small lava pool (x, z, r)


def river_d(i, x, z):
    cx, hw, B, z0 = RIVERS[i]
    if z0 is not None and z < z0:
        return math.hypot(x - cx(z0), z - z0)
    return abs(x - cx(z))


def river_profile(i, x, z):
    """The ground in and beside river i: bed at B - 36, rising to the bank over 100 (20 degrees); None away."""
    cx, hw, B, z0 = RIVERS[i]
    d = river_d(i, x, z)
    if d >= hw + 50:
        return None
    return B - 36 + 36 * smooth((d - (hw - 50)) / 100.0)


def base(x):
    """The flats' ground: rising west to east in steps, level round each river (both banks the same height)."""
    knots = [(-1550, 100), (-1150, 120), (-550, 120), (-280, 150), (280, 150), (475, 180), (1085, 180),
             (1200, 200), (1300, 200)]
    if x <= knots[0][0]:
        return knots[0][1]
    for (xa, ya), (xb, yb) in zip(knots, knots[1:]):
        if x <= xb:
            return ya + (yb - ya) * smooth((x - xa) / (xb - xa))
    return knots[-1][1]


HEAPS = [  # (x, z, r, h): slag heaps every 400-600, kept off the rivers' banks
    (-1300, -50, 170, 110), (-1280, 600, 150, 90), (-430, -620, 140, 100), (60, -650, 120, 80),
    (1120, 480, 150, 100), (1120, -700, 130, 90), (380, 650, 120, 70),
]
RING = (-1290, -480, 150, 85, 150)  # the slag heap hollow: centre, ring radius, ring half-width, height


def heaps(x, z):
    h = 0.0
    for (hx, hz, r, hh) in HEAPS:
        d = math.hypot(x - hx, z - hz)
        if d < r:
            h = max(h, hh * smooth(1 - d / r) + 6 * math.sin(x / 37.0 + z / 53.0))
    rx, rz, rr, rw, rh = RING
    d = math.hypot(x - rx, z - rz)
    if abs(d - rr) < rw:
        ang = math.atan2(z - rz, x - rx)  # +pi/2 = south (+z): the gap faces south-east
        gap = smooth(abs(ang - 0.9) / 0.55)
        h = max(h, rh * smooth(1 - abs(d - rr) / rw) * gap)
    # keep heaps off the river banks: banks stay under 40
    for i in range(3):
        d = river_d(i, x, z)
        h *= smooth((d - (RIVERS[i][1] + 70)) / 120.0)
    return h


def flats_floor(x, z):
    for (bx0, bz0, bx1, bz1, B) in BRIDGES:
        if bx0 <= x <= bx1 and bz0 <= z <= bz1:
            return B  # the causeway under the bridge (left out of the mesh)
    y = base(x) + heaps(x, z)
    for i in range(3):
        p = river_profile(i, x, z)
        if p is not None:
            y = min(y, p)
    return y


def lake_floor(x, z):
    B = RIVERS[1][2]
    y = B - 36 + 36 * smooth((850 - z) / 100.0)  # the north shore
    d = math.hypot(x - ISLAND[0], z - ISLAND[1])
    y = max(y, B - 36 + 61 * smooth((250 - d) / 100.0))  # the island: top flat to r 150, 31 over the lava
    p = river_profile(1, x, z) if z < 900 else None  # R2's channel runs into the lake, not across the island
    return min(y, p) if p is not None else y


def landing_floor(x, z):
    px, pz, r = POOL
    d = math.hypot(x - px, z - pz)
    return -36 + 36 * smooth((d - (r - 50)) / 100.0) if d < r + 50 else 0.0


def rect(x0, x1, z0, z1, fn):
    return ("rect", x0, x1, z0, z1, fn)


ZONES = [
    rect(-2450, -2050, 1250, 1650, landing_floor),                                        # A
    rect(-2050, -1750, 1050, 1350, lambda x, z: 0.0),                                    # the niche
    rect(-1550, 1250, -800, 750, flats_floor),                                           # C
    rect(LAKE[0], LAKE[2], LAKE[1], LAKE[3], lake_floor),                                # the bay
    rect(1150, 1450, -550, -250, lambda x, z: 200 + 20 * smooth((x - 1250) / 100.0)),    # to the yard
    rect(1350, 2150, -750, -150, lambda x, z: 220.0),                                    # D
    rect(1650, 2050, -1150, -750,                                                        # the ramp up
         lambda x, z: 220 + 130 * max(0.0, min(1.0, (-900 - z) / 250.0))),  # 27.5 degrees
    rect(1550, 2150, -1550, -1050, lambda x, z: 350.0),                                  # E
    rect(1650, 2050, -1750, -1550, lambda x, z: 350.0),                                  # the vestibule (rock behind)
]


def cliff(x, z):
    """Rock beyond the floors: 600-ish, higher to the east (the forge's mountain)."""
    return (620 + 70 * math.sin(x / 310.0) * math.cos(z / 270.0) + 35 * math.sin(x / 130.0 + z / 170.0)
            + 380 * smooth((x - 900) / 1100.0))  # the north stays low: the volcano shows over it


def zone_at(x, z):
    """(floor, how far outside it) of the zone x, z is deepest in (or nearest to)."""
    best = None
    for zn in ZONES:
        _, x0, x1, z0, z1, fn = zn
        d = max(x0 - x, x - x1, z0 - z, z - z1)
        if best is None or d < best[1]:
            best = (fn, d)
    d, s = canyon_at(x, z)
    dc = d - canyon_hw(s)
    if dc < best[1]:
        return canyon_floor(s), dc
    return best[0](x, z), best[1]


def H(x, z):
    fl, d = zone_at(x, z)
    if d <= 0:
        return fl
    if d > 150:
        return 100.0 * round(cliff(x, z) / 100.0)  # plateaus out of reach: flat, so they merge into few faces
    return fl + (cliff(x, z) - fl) * smooth(d / 50.0)


def in_rect(x, z, r):
    return r[0] <= x <= r[2] and r[1] <= z <= r[3]


def ground_mat(x, z, y, slope):
    if slope > 40:
        return 2  # basalt cliffs
    if x > 1150:
        return 4 if z < -1050 else 3  # paving in the court and vestibule, the yard's slabs
    if x < -1550 or (in_rect(x, z, LAKE) and y < 160):
        return 1  # crust: the landing, the canyon, the lake shore
    for i in range(3):
        if river_d(i, x, z) < RIVERS[i][1] + 60:
            return 1  # scorched crust along the lava
    return 0  # ash


def under_blocks(x, z):
    """Squares wholly under the bridges (their causeways), left out so nothing lands on hidden ground."""
    return any(b[0] < x < b[2] and b[1] < z < b[3] for b in BRIDGES)


ground = C.heightfield("ground", coll, -2500, -1800, 2500, 1800, 100.0, H, ground_mat,
                       [ASH, CRUST, BASALT, YARDF, PAVE], boundary=420.0, flat_angle=1.2, merge_above=500.0,
                       skip=under_blocks)
spots["ground_tris"] = len(ground.data.polygons)

# ------------------------------------------------------------------------------------------------ lava
lava = Mesh("lava", [LAVA], coll, uv_size=200.0)
C.water_surface(lava, H, -1200, -900, -500, 900, 100.0, RIVERS[0][2] - 6, merge=2)       # R1
C.water_surface(lava, H, -300, -700, 400, 1500, 100.0, RIVERS[1][2] - 6, merge=2)        # R2, its spring, the lake
C.water_surface(lava, H, 500, -900, 1100, 900, 100.0, RIVERS[2][2] - 6, merge=2)         # R3
C.water_surface(lava, H, -2500, 1300, -2100, 1800, 100.0, -6.0, merge=2)                 # the landing's pool
lava.build()

# ------------------------------------------------------------------------------------------------ the bridges
br = Mesh("bridges", [STONE], coll, uv_size=128.0)
for n, (bx0, bz0, bx1, bz1, B) in enumerate(BRIDGES):
    top = B + 4
    C.tiled(br, bx0, bz0, bx1, bz1, top, 0, size=130.0)
    C.sides(br, bx0, bz0, bx1, bz1, B - 46, top, 0, which="ns")
    # parapets 90 high on both edges (no collider: a fall lands in lava 30 deep, banks 36: walk out)
    C.lip(br, (bx0 + 30, bz0), (bx1 - 30, bz0), top, top, 0, h=90.0, thick=22.0)
    C.lip(br, (bx1 - 30, bz1), (bx0 + 30, bz1), top, top, 0, h=90.0, thick=22.0)
    spots[f"bridge{n + 1}"] = ((bx0 + bx1) / 2, (bz0 + bz1) / 2, top)
br.build()

# ------------------------------------------------------------------------------------------------ basalt columns
cols = Mesh("columns", [COLUMN, BASALT], coll, uv_size=96.0)


def column(x, z, r, h, phase=0.0, cap=True):
    y = H(x, z)
    C.post(cols, x, z, r, y - 25, y + h, 0, n=6, cap=cap, phase=phase)
    return y


# squad 1's cover where the canyon widens (one per member, 100 across, 110 tall)
S1 = [(-2200, 790), (-2000, 780), (-2160, 970), (-2020, 950)]
for k, (x, z) in enumerate(S1):
    column(x, z, 50, 112, 0.3 * k)
# squad 2's cover along the last bends
S2 = [(-1950, 570), (-1800, 440), (-1660, 360)]
for k, (x, z) in enumerate(S2):
    column(x, z, 50, 110, 0.5 * k)
# the column stair up the canyon's west wall: steps of 70 to a top at 210 with a full health (any hero)
STAIR = [(-2240, 1060, 50, 70), (-2255, 1150, 50, 140), (-2250, 1250, 70, 210)]
for k, (x, z, r, h) in enumerate(STAIR):
    yb = H(-2230, 1140)  # the canyon floor beside them
    C.post(cols, x, z, r, yb - 25, yb + h, 0, n=6, cap=True, phase=0.2 * k)
spots["stair_top"] = (STAIR[2][0], STAIR[2][1], H(-2230, 1140) + 210)
# columns against the canyon walls (decoration, tall, their feet at the wall's foot, alternating sides)
for k, sc in enumerate(range(260, int(CANYON_LEN) - 40, 120)):
    (px, pz) = point_at(sc)
    (qx, qz) = point_at(sc + 1)
    L = math.hypot(qx - px, qz - pz) or 1.0
    side = 1 if k % 2 else -1
    nx, nz = -(qz - pz) / L * side, (qx - px) / L * side
    off = canyon_hw(sc) + 30
    x, z = px + nx * off, pz + nz * off
    fy = canyon_floor(sc)
    C.post(cols, x, z, 48 + 8 * (k % 3), fy - 30, fy + 260 + 40 * (k % 4), 1 if k % 3 == 0 else 0, n=6, cap=True,
           phase=0.4 * k)
cols.build()

# ------------------------------------------------------------------------------------------------ slag lumps: cover
lumps = Mesh("slag", [SLAG, CRUST], coll, uv_size=128.0)
LUMPS = [  # (x, z): cover on the bridge approaches and round the fights (r 55+, 110 tall)
    (-1250, 250), (-1180, 470), (-1350, 380),          # bridge 1's near bank: run from lump to lump
    (-450, 300), (-330, 520), (-520, 80), (-300, 150),  # mid1: the wasps' ground, behind bridge 1's turret
    (100, 300), (-120, 380),                            # bridge 2's near bank (mid1 side of R2 is x < -180)
    (420, 0), (330, -250), (450, -420),                 # mid2, before bridge 3
    (1100, -100), (1080, -500), (1120, -300),           # bridge 3's far end: the gunners' cover
    (-90, 1150), (60, 1270),                            # on the lava-walker's island
]
for n, (x, z) in enumerate(LUMPS):
    C.boulder(lumps, x, z, H(x, z), 60, 112 + (n % 3) * 8, 300 + n, n % 2)
lumps.build()

# ------------------------------------------------------------------------------------------------ turret plinths
pl = Mesh("plinths", [STONE, IRON], coll, uv_size=128.0)
PLINTHS = [(-470, 470), (390, 320)]  # far banks of bridges 1 and 2
for n, (x, z) in enumerate(PLINTHS):
    y = H(x, z)
    pl.box(x - 55, z - 55, x + 55, z + 55, y - 20, y + 70, 0)
    spots[f"turret{n + 4}"] = (x, z, y + 70)
pl.build()

# ------------------------------------------------------------------------------------------------ the ore yard
yd = Mesh("yard", [IRON, BRICK, HAZARD, GLOW, STONE], coll, uv_size=128.0)
YF = 220.0
# ore carts as cover (140 x 80, 105 tall: an iron tub on a base), on the tracks; one per member of squads 7-8
CARTS = [(1530, -570), (1760, -570), (1500, -330), (1700, -330)]  # on the tracks
BINS = [(1470, -450), (1640, -450), (1840, -450)]                 # ore bins between them
for (x, z) in CARTS:
    yd.box(x - 62, z - 28, x + 62, z + 28, YF - 10, YF + 30, 0)
    yd.box(x - 70, z - 35, x + 70, z + 35, YF + 30, YF + 105, 0, top=0)
for (x, z) in BINS:
    yd.box(x - 40, z - 40, x + 40, z + 40, YF - 10, YF + 110, 4)
spots["yard_cover"] = CARTS + BINS
# the gantry over the tracks: two legs at the yard's edges, a beam at 500, hazard stripes on it
GX = 1380  # over the yard's way in from the flats, out of the squads' region (a beam over a region is an obstacle)
for (z0, z1) in ((-572, -536), (-264, -228)):
    yd.box(GX - 18, z0, GX + 18, z1, YF - 10, YF + 300, 0)
yd.box(GX - 25, -568, GX + 25, -232, YF + 270, YF + 310, 0)  # its ends inside the legs (no face in a leg's plane)
C.decal(yd, [(GX + 29, -500, YF + 272), (GX + 29, -300, YF + 272), (GX + 29, -300, YF + 308),
             (GX + 29, -500, YF + 308)], 2)
C.decal(yd, [(GX - 29, -300, YF + 272), (GX - 29, -500, YF + 272), (GX - 29, -500, YF + 308),
             (GX - 29, -300, YF + 308)], 2)
spots["signal"] = (GX + 45, -400, YF + 250)
# the office in the south-east corner: brick walls 200 high, a doorway west, a lit window south, an iron roof
OX0, OX1, OZ0, OZ1 = 1960, 2100, -340, -170
T = 20
OT = YF + 208  # wall tops inside the roof slab (a top under a ceiling, or in its plane, flickers)
HOLE = [(-300, YF - 10, -195, YF + 150)]  # the doorway in the west wall (z, y)
C.plane_rect(yd, "x", OX0, OZ0, YF - 10, OZ1, OT, HOLE, 1, (-1, 0, 0))            # outside faces
C.plane_rect(yd, "x", OX1, OZ0, YF - 10, OZ1, OT, [], 1, (1, 0, 0))
C.plane_rect(yd, "z", OZ0, OX0, YF - 10, OX1, OT, [], 1, (0, -1, 0))
C.plane_rect(yd, "z", OZ1, OX0, YF - 10, OX1, OT, [], 1, (0, 1, 0))
C.plane_rect(yd, "x", OX0 + T, OZ0 + T, YF - 10, OZ1 - T, OT, HOLE, 1, (1, 0, 0))  # inside faces
C.plane_rect(yd, "x", OX1 - T, OZ0 + T, YF - 10, OZ1 - T, OT, [], 1, (-1, 0, 0))
C.plane_rect(yd, "z", OZ0 + T, OX0 + T, YF - 10, OX1 - T, OT, [], 1, (0, 1, 0))
C.plane_rect(yd, "z", OZ1 - T, OX0 + T, YF - 10, OX1 - T, OT, [], 1, (0, -1, 0))
yd.wall((OX0, -300), (OX0 + T, -300), YF - 10, YF - 10, YF + 150, YF + 150, 1, facing=(0, 1, 0))   # the jambs
yd.wall((OX0 + T, -195), (OX0, -195), YF - 10, YF - 10, YF + 150, YF + 150, 1, facing=(0, -1, 0))
yd.face([(OX0, -300, YF + 150), (OX0 + T, -300, YF + 150), (OX0 + T, -195, YF + 150), (OX0, -195, YF + 150)], 1,
        (0, 0, -1))
yd.box(OX0 - 15, OZ0 - 15, OX1 + 15, OZ1 + 15, YF + 200, YF + 216, 0)   # the roof (its underside: the ceiling)
yd.face([(OX0 + T, OZ0 + T, YF + 200), (OX1 - T, OZ0 + T, YF + 200), (OX1 - T, OZ1 - T, YF + 200),
         (OX0 + T, OZ1 - T, YF + 200)], 0, (0, 0, -1))
C.decal(yd, [(2010, OZ1 + 4, YF + 90), (2060, OZ1 + 4, YF + 90), (2060, OZ1 + 4, YF + 150),
             (2010, OZ1 + 4, YF + 150)], 3)
spots["office"] = ((OX0 + OX1) / 2 + 10, (OZ0 + OZ1) / 2, YF)
# the yard gate: a brick wall across the ramp's foot (z -780..-740), an opening 160 x 160 for the door, a reveal
WZ0, WZ1, WX0, WX1 = -780, -740, 1550, 2150
DX0, DX1, DY1 = 1770, 1930, YF + 160
C.plane_rect(yd, "z", WZ1, WX0, YF - 20, WX1, YF + 360, [(DX0, YF - 20, DX1, DY1)], 1, (0, 0, 1))
C.plane_rect(yd, "z", WZ0, WX0, YF - 20, WX1, YF + 360, [(DX0, YF - 20, DX1, DY1)], 1, (0, 0, -1))
yd.face([(WX0, WZ1, YF + 360), (WX1, WZ1, YF + 360), (WX1, WZ0, YF + 360), (WX0, WZ0, YF + 360)], 1, (0, 0, 1))
yd.wall((DX0, WZ0), (DX0, WZ1), YF - 20, YF - 20, DY1, DY1, 1, facing=(1, 0, 0))
yd.wall((DX1, WZ1), (DX1, WZ0), YF - 20, YF - 20, DY1, DY1, 1, facing=(-1, 0, 0))
yd.face([(DX0, WZ0, DY1), (DX1, WZ0, DY1), (DX1, WZ1, DY1), (DX0, WZ1, DY1)], 1, (0, 0, -1))
C.decal(yd, [(DX0 - 10, WZ1 + 4, DY1 + 10), (DX1 + 10, WZ1 + 4, DY1 + 10), (DX1 + 10, WZ1 + 4, DY1 + 50),
             (DX0 - 10, WZ1 + 4, DY1 + 50)], 2)
spots["yard_door"] = ((DX0 + DX1) / 2, (WZ0 + WZ1) / 2, YF)
yd.build()
rails = Mesh("rails", [RAILS], coll)
for tz in (-570, -330):  # two tracks along x, 2 over the floor (pictures: nocollide)
    for x0 in range(1380, 2100, 100):
        if tz == -330 and x0 >= 1900:
            break  # the office
        rails.face([(x0, tz + 30, YF + 2), (x0 + 100, tz + 30, YF + 2), (x0 + 100, tz - 30, YF + 2),
                    (x0, tz - 30, YF + 2)], 0, (0, 0, 1), [(0, 0), (0, 3), (1, 3), (1, 0)])
rails.build()

# ------------------------------------------------------------------------------------------------ the forge gate
fg = Mesh("forge", [BRICK, IRON, SIGIL, HAZARD, GLOW, BASALT, PAVE], coll, uv_size=128.0)
EY = 350.0
FZ0, FZ1 = -1580, -1540  # the facade (40 thick)
FX0, FX1 = 1500, 2200
GX0, GX1, GY1 = 1700, 2000, EY + 216  # the great opening for the cave-style door (338 x 256)
C.plane_rect(fg, "z", FZ1, FX0, EY - 20, FX1, EY + 620, [(GX0, EY - 20, GX1, GY1)], 0, (0, 0, 1))
C.plane_rect(fg, "z", FZ0, FX0, EY - 20, FX1, EY + 300, [(GX0, EY - 20, GX1, GY1)], 0, (0, 0, -1))
fg.wall((GX0, FZ0), (GX0, FZ1), EY - 20, EY - 20, GY1, GY1, 0, facing=(1, 0, 0))
fg.wall((GX1, FZ1), (GX1, FZ0), EY - 20, EY - 20, GY1, GY1, 0, facing=(-1, 0, 0))
fg.face([(GX0, FZ0, GY1), (GX1, FZ0, GY1), (GX1, FZ1, GY1), (GX0, FZ1, GY1)], 0, (0, 0, -1))
# pilasters and a cornice
for px in (1560, GX0 - 55, GX1 + 15, 2100):
    fg.box(px, FZ1 + 1, px + 40, FZ1 + 30, EY - 10, EY + 560, 0)
fg.box(1580, FZ1 + 1, 2120, FZ1 + 45, EY + 560, EY + 600, 1)
# banners with the sigil either side of the door, hazard over it
for bx in (1610, 2010):
    C.decal(fg, [(bx + 2, FZ1 + 34, EY + 240), (bx + 78, FZ1 + 34, EY + 240), (bx + 78, FZ1 + 34, EY + 500),
                 (bx + 2, FZ1 + 34, EY + 500)], 2)
C.decal(fg, [(GX0, FZ1 + 4, GY1 + 20), (GX1, FZ1 + 4, GY1 + 20), (GX1, FZ1 + 4, GY1 + 70),
             (GX0, FZ1 + 4, GY1 + 70)], 3)
# glowing windows high in the facade
for wx in (1512, 2148):
    C.decal(fg, [(wx, FZ1 + 4, EY + 520), (wx + 40, FZ1 + 4, EY + 520), (wx + 40, FZ1 + 4, EY + 550),
                 (wx, FZ1 + 4, EY + 550)], 4)
# the vestibule: a rock ceiling at 640, the glow of the furnaces on its back wall
C.ceiling(fg, 1650, -1745, 2050, FZ0, EY + 290, 5, size=220.0)  # its edges end inside the rock (no fold)
C.decal(fg, [(1760, -1702, EY + 40), (1940, -1702, EY + 40), (1940, -1702, EY + 200), (1760, -1702, EY + 200)], 4)
spots["forge_door"] = ((GX0 + GX1) / 2, (FZ0 + FZ1) / 2, EY)
spots["exit"] = (1850, -1680, EY)
spots["start1"] = (1850, -1600, EY)
# braziers: an iron post and bowl, fire on top (the game's flames are placed in Studio)
BRAZ = [(1610, -1480), (2090, -1480), (1610, -1120), (2090, -1120)]  # the court's corners, out of the region
for (x, z) in BRAZ:
    C.post(fg, x, z, 14, EY - 5, EY + 90, 1, n=6, cap=False)
    C.post(fg, x, z, 34, EY + 90, EY + 120, 1, n=8, cap=True)
spots["braziers"] = [(x, z, EY + 120) for (x, z) in BRAZ]
# cover in the court for the gunners: two ingot stacks (100 x 100, 110)
for (x, z) in ((1740, -1300), (1960, -1300)):
    fg.box(x - 50, z - 50, x + 50, z + 50, EY - 10, EY + 110, 1)
fg.build()

# colliders over the gate wall and the facade tops are not needed: both meet cliffs over 300 high
# ------------------------------------------------------------------------------------------------ light
level = [o for o in coll.all_objects if o.type == "MESH"]
SUN_DIR = (0.8, 0.32, -0.5)  # a low red sun in the west-south-west, about 30 degrees up (Blender space: the light's travel)
GLOW_C = (0.62, 0.24, 0.06)
LAMPS = []
for i, (cx, hw, B, z0) in enumerate(RIVERS):
    for z in range(-800, 801, 200):
        if z0 is not None and z < z0:
            continue
        LAMPS.append((cx(z), z, B + 10, 320, GLOW_C))
for (x, z) in ((-250, 900), (250, 900), (-200, 1200), (200, 1200), (0, 1400), (0, 1000)):
    LAMPS.append((x, z, 160, 320, GLOW_C))  # the lake
LAMPS.append((POOL[0], POOL[1], 10, 300, GLOW_C))
for (x, z) in BRAZ:
    LAMPS.append((x, z, EY + 140, 280, (0.6, 0.35, 0.1)))
LAMPS += [
    (1850, -1700, EY + 150, 380, (0.8, 0.4, 0.1)),   # the furnaces' glow in the vestibule
    (1850, -1500, EY + 120, 300, (0.6, 0.3, 0.08)),  # spilling out of the door
    (2030, -255, YF + 120, 160, (0.5, 0.3, 0.1)),    # the office lamp
    (GX + 40, -400, YF + 260, 260, (0.45, 0.28, 0.1)),  # the signal's lamp
]


def extra(x, z, y, mname):
    if mname.startswith("furnace_window"):
        return (2.4, 2.0, 1.6)
    return (1.0, 1.0, 1.0)


TINTS = {"game_060D": (1.0, 0.92, 0.86), "game_0C37": (0.95, 0.9, 0.88)}
# the kit's ambient (0.2, 0.12, 0.1) left the canyon black over these dark textures: lifted, the same hue
C.bake(level, SUN_DIR, (0.9, 0.35, 0.2), (0.34, 0.21, 0.17), tints=TINTS, lamps=LAMPS, extra=extra,
       soft={"game_060D": (0.6, 0.2), "game_0C3E": (0.6, 0.2), "game_0C37": (0.6, 0.25)})
# the lava glows of itself: the bake's sun and shade don't touch it
lme = bpy.data.objects["lava"].data
lcol = lme.color_attributes.get("Col")
for d in lcol.data:
    d.color_srgb = (1.0, 0.92, 0.8, 1.0)

# ------------------------------------------------------------------------------------------------ export
os.makedirs(C.OUT, exist_ok=True)
report = jfg64.budgets(level)
out = jfg64.export(os.path.join(C.OUT, NAME + ".glb"), collection=coll)
spots["budgets"] = report
spots["export"] = {k: v for k, v in out.items() if k != "objects"} if isinstance(out, dict) else str(out)
spots["canyon"] = {"len": CANYON_LEN, "squad1": point_at(460), "end": point_at(CANYON_LEN)}


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
print("SLAGFLATS", json.dumps(report))
print("PARTS", json.dumps({o.name: sum(len(p.vertices) - 2 for p in o.data.polygons) for o in level}))
