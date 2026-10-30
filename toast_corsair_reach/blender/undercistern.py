"""The Undercistern (Corsair Reach 2.3): builds the level from nothing and exports blender/out/undercistern.glb.

    blender --background --factory-startup --addons jfg64 --python undercistern.py

The old waterworks under Mirefall's hub town, lit by oil lamps. From the town's cistern door a stair comes down
(100 -> 0) to the pump gallery (0): three old pumps, a channel along its south wall and, across it behind bars, the
valve that holds the sluice gate shut. Through the sluice a passage goes down (0 -> -150) to the cell block (three
cells with square windows, a Tribal behind each pane) and on to the channel walks (-150): a walkway beside a water
channel north to south, then east to west, two side tunnels across the channels (the drain rats' holes: ammo at the
end of one, a Tribal at the other). From the walks' west end the return stair climbs back to the pump gallery (a
door the second rat pack keeps shut: the loop) and a stair goes down (-150 -> -300) to the guard room and the great
cistern (-300): 1,200 x 1,000, 700 high, under 30 of water, eight pillars, the plinth with the blue key in the
middle, a gallery on the south side (the lookout) reached by a stair along the east wall. Its east door (shut until
the bog walkers are dead) opens on the return stair up (-300 -> 0) to the way out into the town.

Game units: x east, z south (north is -z), y up. The level's numbers are in levels/2.3_undercistern.md (As built).
"""
import json
import math
import os
import random
import sys

import bpy

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import common as C  # noqa: E402
from common import Mesh, tiled, post, collider, strip, walls, ceiling, plane_rect, lip  # noqa: E402
import jfg64  # noqa: E402

NAME = "undercistern"
scene, coll = C.new_scene(NAME)
rnd = random.Random(23)

TUN = 300.0                      # corridors 200 wide, 300 high
Y0, Y1, Y2 = 0.0, -150.0, -300.0  # the three tiers
FW, FL = -330.0, -300.0          # the great cistern: its floor under the water, the water
BCF, BCW = -35.0, -5.0           # the pump gallery's channel: floor, water (30 deep)
DCF, DCW = -185.0, -155.0        # the channel walks' channels
FTOP = 400.0                     # the great cistern's vault (700 over its tier)


# ------------------------------------------------------------------------------------------------ our own images
def iron_px(x, y):
    """An iron grate: dark bars both ways, rust in the corners of each square."""
    bar = (0.2, 0.19, 0.18)
    if x % 8 in (0, 1) or y % 8 in (0, 1):
        return (0.3, 0.28, 0.26) if (x % 8 == 0 or y % 8 == 0) else bar
    rust = (0.36, 0.2, 0.1) if (x % 8 in (2, 7) and y % 8 in (2, 7)) else None
    return rust or (0.05, 0.06, 0.06)


def marks_px(x, y):
    """The colony's old water marks: a stone panel, three tide lines (each lower, older) and chalk notches."""
    base = 0.36 + 0.04 * ((x * 7 + y * 13) % 5) / 4
    stone = (base * 0.9, base, base * 0.95)
    for k, line in enumerate((8, 15, 23)):
        if abs(y - line) <= 0:
            return (0.12, 0.16, 0.13)
        if y == line + 1:
            return (0.22, 0.28, 0.22)
        if line - 4 <= y <= line - 1 and 2 <= x <= 7 + k * 2 and x % 2 == 0:
            return (0.85, 0.85, 0.8)   # tally notches beside each line
    if y > 24:
        return (stone[0] * 0.7, stone[1] * 0.8, stone[2] * 0.7)  # the green stain under the lowest line
    return stone


def valve_px(x, y):
    """The sluice's valve wheel: an iron ring with six spokes and a hub, red paint worn off, on a dark plate."""
    cx, cy = 15.5, 15.5
    d = math.hypot(x - cx, y - cy)
    a = math.atan2(y - cy, x - cx)
    red, iron = (0.55, 0.12, 0.08), (0.3, 0.27, 0.25)
    if 11.5 <= d <= 14.5:
        return red if (x + y) % 5 else iron
    if d < 3.5:
        return iron
    if d < 11.5 and min(abs(((a / (math.tau / 6)) % 1) - 0.5), 0.5) > 0.42:
        return red
    return (0.08, 0.08, 0.09)


def lamp_px(x, y):
    """An oil lamp's glass: warm amber, brighter in the middle, a dark frame."""
    if x in (0, 15) or y in (0, 15) or x in (7, 8) and y < 3:
        return (0.18, 0.12, 0.06)
    d = math.hypot(x - 7.5, y - 9) / 9
    k = max(0.0, 1 - d)
    return (min(1, 0.7 + 0.3 * k), 0.42 + 0.45 * k, 0.12 + 0.3 * k ** 2)


def door_px(x, y):
    """The old door at the top of the return stair: planks, two iron bands, a ring handle."""
    if y in (12, 13, 50, 51):
        return (0.16, 0.15, 0.15)
    if x in (0, 31) or y in (0, 63):
        return (0.12, 0.08, 0.05)
    if math.hypot(x - 24, y - 33) < 3.2 and math.hypot(x - 24, y - 33) > 1.8:
        return (0.3, 0.28, 0.25)
    plank = (x // 8) % 2
    g = 0.03 * ((x * 11 + y * 5) % 3)
    if x % 8 == 0:
        return (0.14, 0.09, 0.05)
    return (0.34 + g, 0.22 + g, 0.12) if plank else (0.3 + g, 0.2 + g, 0.11)


# ------------------------------------------------------------------------------------------------ materials
MATS = []


def mat(material):
    MATS.append(material)
    return len(MATS) - 1


BRICK = mat(C.game(0x1946))    # old brick: the passages, the cell block, the return stair
ASHLAR = mat(C.game(0x0828))   # dressed stone: the great cistern's walls, pillars and plinth, the pumps
MOSS = mat(C.game(0x1736))     # mossy stone blocks: the entry stair, the pump gallery, the guard room
SLIME = mat(C.game(0x1958))    # wet mossy rock: the channels' banks and the walks' walls
FLAGS = mat(C.game(0x16DF))    # grey flagstones: floors
PAVE = mat(C.game(0x0BEB))     # paving: the gallery, the plinth's top, the landing
CEIL = mat(C.game(0x07F2))     # dark rock: the passages' and rooms' ceilings
VAULT = mat(C.game(0x0CAF))    # grey stone: the great cistern's vault
MUD = mat(C.game(0x1959))      # the floor under the water
DARK = mat(C.game(0x16DB))     # dark wood and iron: pipes, lamp arms, the bars
WATER = mat(C.game(0x0DED, "water"))
IRON = mat(C.own_material("drain_grate", C.own_image("drain_grate", 16, 16, iron_px)))
MARKS = mat(C.own_material("water_marks", C.own_image("water_marks", 32, 32, marks_px)))
VALVE = mat(C.own_material("valve_wheel", C.own_image("valve_wheel", 32, 32, valve_px)))
LAMP = mat(C.own_material("oil_lamp", C.own_image("oil_lamp", 16, 16, lamp_px)))
DOOR = mat(C.own_material("old_door", C.own_image("old_door", 32, 64, door_px)))
EDGE = jfg64.boundary_material()


def mesh(name, uv=200.0):
    return Mesh(name, MATS, coll, uv_size=uv)


upper = mesh("upper")          # A, B, C1, the cell block and its cells
walks = mesh("walks")          # D, T1, T2, W, R, S2, E, X
hall = mesh("cistern")         # F and G
wet = mesh("wet_floors")       # the floors under the water
wtr = Mesh("water", MATS, coll, uv_size=512.0)
props = mesh("props", 128.0)   # pumps, pillars' bases, lamps, bars, pictures
edges = Mesh("colliders", [EDGE], coll)
spots = {"lamps": []}


def decal(m, plane, c, u0, v0, u1, v1, mat_, facing_sign):
    """A picture on a wall, once, 2 in front of it: plane "x" (u is z) or "z" (u is x), facing +1 or -1 along the
    plane's axis, read the right way round from that side (1.4's)."""
    o = c + 2 * facing_sign
    if plane == "z":
        a, b = (u0, u1) if facing_sign > 0 else (u1, u0)
        pts = [(a, o, v0), (b, o, v0), (b, o, v1), (a, o, v1)]
        f = (0, facing_sign, 0)
    else:
        a, b = (u1, u0) if facing_sign > 0 else (u0, u1)
        pts = [(o, a, v0), (o, b, v0), (o, b, v1), (o, a, v1)]
        f = (facing_sign, 0, 0)
    m.face(pts, mat_, f, [(0, 0), (1, 0), (1, 1), (0, 1)])


def lamp(m, x, z, y, wall, radius=360.0, colour=(0.55, 0.36, 0.12)):
    """An oil lamp hung on a wall: an iron arm out of the wall (no face against it), the amber glass 20-36 out
    (no top: the cap covers it), a cap over it. (x, z) on the wall's plane, y the glass's top; wall: the side of
    the lamp the wall is on (n: a north wall, the lamp out to the south)."""
    ox, oz = {"n": (0, 1), "s": (0, -1), "e": (-1, 0), "w": (1, 0)}[wall]
    px, pz = -oz, ox  # along the wall

    def P(out, side, yy):
        return (x + ox * out + px * side, z + oz * out + pz * side, yy)
    # the arm: 6 x 6, from the wall to 24 out
    a0, a1, ay0, ay1 = 0.0, 24.0, y + 4, y + 10
    m.face([P(a0, -3, ay1), P(a0, 3, ay1), P(a1, 3, ay1), P(a1, -3, ay1)], DARK, (0, 0, 1))
    m.face([P(a0, -3, ay0), P(a1, -3, ay0), P(a1, 3, ay0), P(a0, 3, ay0)], DARK, (0, 0, -1))
    m.face([P(a0, -3, ay0), P(a0, -3, ay1), P(a1, -3, ay1), P(a1, -3, ay0)], DARK, (-px, -pz, 0))
    m.face([P(a0, 3, ay0), P(a1, 3, ay0), P(a1, 3, ay1), P(a0, 3, ay1)], DARK, (px, pz, 0))
    # the glass: out 20..36, 16 across, y-26..y (sides and bottom)
    g0, g1 = 20.0, 36.0
    yb, yt = y - 26, y
    for (u0, w0, u1, w1, f) in ((g0, -8, g0, 8, (-ox, -oz, 0)), (g1, -8, g1, 8, (ox, oz, 0)),
                                (g0, -8, g1, -8, (-px, -pz, 0)), (g0, 8, g1, 8, (px, pz, 0))):
        m.face([P(u0, w0, yb), P(u1, w1, yb), P(u1, w1, yt), P(u0, w0, yt)], LAMP, f,
               [(0, 0), (1, 0), (1, 1), (0, 1)])
    m.face([P(g0, -8, yb), P(g1, -8, yb), P(g1, 8, yb), P(g0, 8, yb)], DARK, (0, 0, -1))
    # the cap: 20 across, y..y+5
    c0, c1 = 18.0, 38.0
    m.face([P(c0, -10, yt + 5), P(c1, -10, yt + 5), P(c1, 10, yt + 5), P(c0, 10, yt + 5)], DARK, (0, 0, 1))
    m.face([P(c0, -10, yt), P(c0, 10, yt), P(c1, 10, yt), P(c1, -10, yt)], DARK, (0, 0, -1))
    for (u0, w0, u1, w1, f) in ((c0, -10, c0, 10, (-ox, -oz, 0)), (c1, -10, c1, 10, (ox, oz, 0)),
                                (c0, -10, c1, -10, (-px, -pz, 0)), (c0, 10, c1, 10, (px, pz, 0))):
        m.face([P(u0, w0, yt), P(u1, w1, yt), P(u1, w1, yt + 5), P(u0, w0, yt + 5)], DARK, f)
    cx, cz, cy = x + ox * 28, z + oz * 28, y - 13
    spots["lamps"].append([round(cx), round(cy), round(cz)])
    LAMPS.append((cx, cz, cy, radius, colour))


def reveal(m, plane, c0, c1, u0, u1, y, h, mt, floor_mt):
    """A doorway's reveal through a wall between planes c0 and c1 (plane "x": x = c, u is z; "z": z = c, u is x):
    its floor at y, its two sides and its lintel's underside at y + h."""
    a, b = min(c0, c1), max(c0, c1)
    if plane == "z":
        tiled(m, u0, a, u1, b, y, floor_mt, size=200.0)
        m.face([(u0, a, y), (u0, b, y), (u0, b, y + h), (u0, a, y + h)], mt, (1, 0, 0))
        m.face([(u1, a, y), (u1, b, y), (u1, b, y + h), (u1, a, y + h)], mt, (-1, 0, 0))
        m.face([(u0, a, y + h), (u1, a, y + h), (u1, b, y + h), (u0, b, y + h)], mt, (0, 0, -1))
    else:
        tiled(m, a, u0, b, u1, y, floor_mt, size=200.0)
        m.face([(a, u0, y), (b, u0, y), (b, u0, y + h), (a, u0, y + h)], mt, (0, 1, 0))
        m.face([(a, u1, y), (b, u1, y), (b, u1, y + h), (a, u1, y + h)], mt, (0, -1, 0))
        m.face([(a, u0, y + h), (b, u0, y + h), (b, u1, y + h), (a, u1, y + h)], mt, (0, 0, -1))


def window(m, c0, c1, u0, u1, v0, v1, mt):
    """A square window's reveal through a wall between z = c0 and c1: sides, sill and lintel."""
    a, b = min(c0, c1), max(c0, c1)
    m.face([(u0, a, v0), (u0, b, v0), (u0, b, v1), (u0, a, v1)], mt, (1, 0, 0))
    m.face([(u1, a, v0), (u1, b, v0), (u1, b, v1), (u1, a, v1)], mt, (-1, 0, 0))
    m.face([(u0, a, v1), (u1, a, v1), (u1, b, v1), (u0, b, v1)], mt, (0, 0, -1))
    m.face([(u0, a, v0), (u1, a, v0), (u1, b, v0), (u0, b, v0)], mt, (0, 0, 1))


LAMPS = []

# ================================================================================================ A. the entry stair
AX0, AX1 = -1400.0, -1200.0
A_N, A_ST, A_SF, A_S = -1720.0, -1600.0, -1400.0, -1100.0   # the top landing (the way back), the stair, the landing
YA = 100.0


def afloor(x, z):
    if z <= A_ST:
        return YA
    if z >= A_SF:
        return Y0
    return YA + (Y0 - YA) * (z - A_ST) / (A_SF - A_ST)


tiled(upper, AX0, A_N, AX1, A_ST, YA, FLAGS)
tiled(upper, AX0, A_ST, AX1, A_SF, YA, FLAGS, Y0, along="z")
tiled(upper, AX0, A_SF, AX1, A_S, Y0, FLAGS)
walls(upper, AX0, A_N, AX1, A_ST, YA, YA + TUN, MOSS, "ew", inward=True)
walls(upper, AX0, A_ST, AX1, A_SF, afloor, lambda x, z: afloor(x, z) + TUN, MOSS, "ew", inward=True)
walls(upper, AX0, A_SF, AX1, A_S, Y0, Y0 + TUN, MOSS, "ew", inward=True)
plane_rect(upper, "z", A_N, AX0, YA, AX1, YA + TUN, [], MOSS, (0, 1, 0))
ceiling(upper, AX0, A_N, AX1, A_ST, YA + TUN, CEIL)
ceiling(upper, AX0, A_ST, AX1, A_SF, YA + TUN, CEIL, Y0 + TUN, along="z")
ceiling(upper, AX0, A_SF, AX1, A_S, Y0 + TUN, CEIL)
spots["start"] = [-1300, Y0, -1250]
spots["way_back_exit"] = [-1300, YA, -1665]

# ================================================================================================ B. the pump gallery
BX0, BX1, BZ0, BZ1, BTOP = -1500.0, -900.0, -1100.0, -700.0, 450.0
CHN = (-1260.0, -820.0, -900.0, -700.0)          # the channel along the south wall
PUMPS = [(-1400.0, -1050.0, -1300.0, -950.0), (-1250.0, -1000.0, -1150.0, -900.0), (-1100.0, -1050.0, -1000.0, -950.0)]
ALC = (-1140.0, -700.0, -1020.0, -600.0)         # the valve's alcove behind the bars, floor 60
ALC_Y, ALC_TOP = 60.0, 220.0
SLUICE = (-1060.0, -900.0)                       # the sluice doorway in the east wall (z), 170 high
RDOOR = (-1460.0, -1300.0)                       # the return door in the south wall (x), 170 high
for r in C.rects_minus((BX0, BZ0, BX1, BZ1), [CHN] + PUMPS):
    tiled(upper, *r, Y0, FLAGS)
plane_rect(upper, "z", BZ0, BX0, Y0, BX1, BTOP, [(AX0, Y0, AX1, Y0 + TUN)], MOSS, (0, 1, 0))
plane_rect(upper, "x", BX0, BZ0, Y0, BZ1, BTOP, [], MOSS, (1, 0, 0))
plane_rect(upper, "x", BX1, BZ0, Y0, CHN[1], BTOP, [(SLUICE[0], Y0, SLUICE[1], 170)], MOSS, (-1, 0, 0))
plane_rect(upper, "x", BX1, CHN[1], BCF, BZ1, BTOP, [], MOSS, (-1, 0, 0))
plane_rect(upper, "z", BZ1, BX0, Y0, CHN[0], BTOP, [(RDOOR[0], Y0, RDOOR[1], 170)], MOSS, (0, -1, 0))
plane_rect(upper, "z", BZ1, CHN[0], BCF, BX1, BTOP, [(ALC[0], ALC_Y, ALC[2], ALC_TOP)], MOSS, (0, -1, 0))
ceiling(upper, BX0, BZ0, BX1, BZ1, BTOP, CEIL)
# the channel: its banks, floor and water (zero-width holes where the water's texture repeats)
strip(upper, (CHN[2], CHN[1]), (CHN[0], CHN[1]), BCF, BCF, Y0, Y0, SLIME, (0, 1, 0))
strip(upper, (CHN[0], CHN[1]), (CHN[0], CHN[3]), BCF, BCF, Y0, Y0, SLIME, (1, 0, 0))
C.water_box(wet, CHN, [(-1024.0, CHN[1], -1024.0, CHN[3])], BCF, BCW, MUD, WATER, wm=wtr)
# the pumps: stone housings 110 tall (cover, one per crawler), an iron pipe from each up into the vault
for (x0, z0, x1, z1) in PUMPS:
    C.block(props, x0, z0, x1, z1, Y0, 110.0, ASHLAR, top=DARK, size=None)
    post(props, (x0 + x1) / 2, (z0 + z1) / 2, 14, 110.0, BTOP, DARK, n=6, cap=False)
spots["pump_cover"] = [[(p[0] + p[2]) / 2, (p[1] + p[3]) / 2] for p in PUMPS]
spots["pump_region"] = [[-1480, -1080], [-1480, -830], [-920, -830], [-920, -1080]]
# the valve's alcove (sill 60 over the gallery's floor, 95 over the channel's), its bars, the valve wheel
tiled(upper, ALC[0], ALC[1], ALC[2], ALC[3], ALC_Y, FLAGS)
walls(upper, *ALC, ALC_Y, ALC_TOP, MOSS, "wes", inward=True)
ceiling(upper, *ALC, ALC_TOP, CEIL)
for k in range(4):
    post(props, -1116.0 + 24 * k, -690.0, 4.5, ALC_Y, ALC_TOP, DARK, n=4, phase=math.pi / 4, cap=False)
decal(props, "z", ALC[3], -1118, 98, -1042, 174, VALVE, -1)
spots["valve_switch"] = [-1080, 136, -612]
spots["sluice_door"] = [-880, Y0, -980]
spots["return_door"] = [-1380, Y0, -680]
# the doorways' reveals through the walls (40 deep)
reveal(upper, "x", BX1, BX1 + 40, SLUICE[0], SLUICE[1], Y0, 170.0, MOSS, FLAGS)
reveal(walks, "z", BZ1, BZ1 + 40, RDOOR[0], RDOOR[1], Y0, 170.0, MOSS, FLAGS)
decal(props, "x", BX0, -1010, 120, -930, 200, MARKS, 1)
lamp(props, -1200.0, -1300.0, 210.0, "e")                     # the entry stair
lamp(props, -1000.0, BZ0, 250.0, "n")
lamp(props, BX0, -880.0, 250.0, "w")
lamp(props, -960.0, BZ1, 250.0, "s", radius=320.0)            # by the valve's alcove

# ================================================================================================ C1. the sluice passage
CX0, CX1, CX2 = -860.0, -660.0, -360.0
CZ0, CZ1 = -1080.0, -880.0


def c1floor(x, z):
    return Y0 if x <= CX1 else Y0 + (Y1 - Y0) * (x - CX1) / (CX2 - CX1)


tiled(upper, CX0, CZ0, CX1, CZ1, Y0, FLAGS)
tiled(upper, CX1, CZ0, CX2, CZ1, Y0, FLAGS, Y1, along="x")
walls(upper, CX0, CZ0, CX1, CZ1, Y0, Y0 + TUN, BRICK, "ns", inward=True)
walls(upper, CX1, CZ0, CX2, CZ1, c1floor, lambda x, z: c1floor(x, z) + TUN, BRICK, "ns", inward=True)
plane_rect(upper, "x", CX0, CZ0, Y0, CZ1, Y0 + TUN, [(SLUICE[0], Y0, SLUICE[1], 170)], BRICK, (1, 0, 0))
ceiling(upper, CX0, CZ0, CX1, CZ1, Y0 + TUN, CEIL)
ceiling(upper, CX1, CZ0, CX2, CZ1, Y0 + TUN, CEIL, Y1 + TUN, along="x")

# ================================================================================================ C. the cell block
HX0, HX1, HZ0, HZ1, HTOP = -360.0, 440.0, -1180.0, -780.0, 250.0
COVER_C = [(-200.0, -1050.0, -100.0, -950.0), (50.0, -950.0, 150.0, -850.0), (250.0, -1100.0, 350.0, -1000.0)]
CELLS_N = [(-200.0, 0.0), (200.0, 400.0)]       # north cells (x), z -1420..-1220
CELL_S = (0.0, 200.0)                            # the south cell (x), z -740..-540
WIN = 140.0                                      # square windows, sill 30
WV0, WV1 = Y1 + 30, Y1 + 30 + WIN
for r in C.rects_minus((HX0, HZ0, HX1, HZ1), COVER_C):
    tiled(upper, *r, Y1, FLAGS)
plane_rect(upper, "x", HX0, HZ0, Y1, HZ1, HTOP, [(CZ0, Y1, CZ1, Y1 + TUN)], BRICK, (1, 0, 0))
plane_rect(upper, "x", HX1, HZ0, Y1, HZ1, HTOP, [(CZ0, Y1, CZ1, Y1 + TUN)], BRICK, (-1, 0, 0))
wins_n = [((a + b) / 2 - WIN / 2, (a + b) / 2 + WIN / 2) for a, b in CELLS_N]
win_s = ((CELL_S[0] + CELL_S[1]) / 2 - WIN / 2, (CELL_S[0] + CELL_S[1]) / 2 + WIN / 2)
plane_rect(upper, "z", HZ0, HX0, Y1, HX1, HTOP, [(u0, WV0, u1, WV1) for u0, u1 in wins_n], BRICK, (0, 1, 0))
plane_rect(upper, "z", HZ1, HX0, Y1, HX1, HTOP, [(win_s[0], WV0, win_s[1], WV1)], BRICK, (0, -1, 0))
ceiling(upper, HX0, HZ0, HX1, HZ1, HTOP, CEIL)
for (x0, z0, x1, z1) in COVER_C:   # fallen masonry, 100 tall: the player's cover from the leeches
    C.block(props, x0, z0, x1, z1, Y1, Y1 + 100, ASHLAR, size=None)
spots["cell_cover"] = [[(p[0] + p[2]) / 2, (p[1] + p[3]) / 2] for p in COVER_C]
spots["cell_region"] = [[HX0 + 20, HZ0 + 20], [HX0 + 20, HZ1 - 20], [HX1 - 20, HZ1 - 20], [HX1 - 20, HZ0 + 20]]
CTOP = Y1 + 250
spots["cells"] = []
spots["glass"] = []
for (a, b), (u0, u1) in zip(CELLS_N, wins_n):
    z0, z1 = -1420.0, -1220.0
    tiled(upper, a, z0, b, z1, Y1, FLAGS)
    walls(upper, a, z0, b, z1, Y1, CTOP, BRICK, "nwe", inward=True)
    plane_rect(upper, "z", z1, a, Y1, b, CTOP, [(u0, WV0, u1, WV1)], BRICK, (0, -1, 0))
    ceiling(upper, a, z0, b, z1, CTOP, CEIL)
    window(upper, z1, HZ0, u0, u1, WV0, WV1, BRICK)
    decal(props, "z", z0, a + 50, Y1 + 60, a + 110, Y1 + 120, MARKS, 1)
    spots["cells"].append([(a + b) / 2, Y1, -1340.0])
    spots["glass"].append({"a": [u0, (z1 + HZ0) / 2], "b": [u1, (z1 + HZ0) / 2], "bottom": WV0})
z0, z1 = -740.0, -540.0
a, b = CELL_S
tiled(upper, a, z0, b, z1, Y1, FLAGS)
walls(upper, a, z0, b, z1, Y1, CTOP, BRICK, "swe", inward=True)
plane_rect(upper, "z", z0, a, Y1, b, CTOP, [(win_s[0], WV0, win_s[1], WV1)], BRICK, (0, 1, 0))
ceiling(upper, a, z0, b, z1, CTOP, CEIL)
window(upper, HZ1, z0, win_s[0], win_s[1], WV0, WV1, BRICK)
decal(props, "z", z1, a + 90, Y1 + 60, a + 150, Y1 + 120, MARKS, -1)
spots["cells"].append([(a + b) / 2, Y1, -620.0])
spots["glass"].append({"a": [win_s[0], (HZ1 + z0) / 2], "b": [win_s[1], (HZ1 + z0) / 2], "bottom": WV0})
reveal(upper, "x", HX1, HX1 + 40, CZ0, CZ1, Y1, TUN, BRICK, FLAGS)
lamp(props, 100.0, HZ0, 140.0, "n")
lamp(props, -250.0, HZ1, 140.0, "s")
lamp(props, 330.0, HZ1, 140.0, "s")

# ================================================================================================ D. the channel walks
DX0, DX1, DX2 = 480.0, 680.0, 880.0       # D-east: the walkway x 480..680, its channel 680..880
DZ0, DZ1 = -1180.0, -320.0                # D-east north to south
SX0, SZ0, SZ1, SZ2 = -560.0, -320.0, -120.0, 40.0   # D-south: walkway z -320..-120, channel -120..40
DTOP = Y1 + TUN
T1 = (880.0, -900.0, 1180.0, -740.0)      # the first rats' tunnel (east, across the channel): the ammo cache
T2 = (0.0, 40.0, 160.0, 300.0)            # the second rats' tunnel (south, across the channel): Tribal 4
TT = Y1 + 220                             # the tunnels' ceiling
ECH = (DX1, DZ0, DX2, DZ1)                # D-east's channel
SCH = (SX0, SZ1, DX2, SZ2)                # D-south's channel
tiled(walks, DX0, DZ0, DX1, DZ1, Y1, FLAGS)
tiled(walks, SX0, SZ0, DX2, SZ1, Y1, FLAGS)
C.water_box(wet, ECH, [(DX1, -1024.0, DX2, -1024.0), (DX1, -512.0, DX2, -512.0)], DCF, DCW, MUD, WATER, wm=wtr)
C.water_box(wet, SCH, [(-512.0, SZ1, -512.0, SZ2), (0.0, SZ1, 0.0, SZ2), (512.0, SZ1, 512.0, SZ2),
                       (SX0, 0.0, DX2, 0.0)], DCF, DCW, MUD, WATER, wm=wtr)
strip(walks, (DX1, DZ0), (DX1, DZ1), DCF, DCF, Y1, Y1, SLIME, (-1, 0, 0))     # D-east channel's west bank
strip(walks, (DX1, DZ1), (DX2, DZ1), DCF, DCF, Y1, Y1, SLIME, (0, -1, 0))     # its south end
strip(walks, (DX2, SZ1), (SX0, SZ1), DCF, DCF, Y1, Y1, SLIME, (0, 1, 0))      # D-south channel's north bank
plane_rect(walks, "z", DZ0, DX0, Y1, DX1, DTOP, [], SLIME, (0, 1, 0))
plane_rect(walks, "z", DZ0, DX1, DCF, DX2, DTOP, [], SLIME, (0, 1, 0))
plane_rect(walks, "x", DX0, DZ0, Y1, DZ1, DTOP, [(CZ0, Y1, CZ1, Y1 + TUN)], SLIME, (1, 0, 0))
plane_rect(walks, "x", DX2, DZ0, DCF, DZ1, DTOP, [(T1[1], Y1, T1[3], TT)], SLIME, (-1, 0, 0))
plane_rect(walks, "x", DX2, SZ0, Y1, SZ1, DTOP, [], SLIME, (-1, 0, 0))
plane_rect(walks, "x", DX2, SZ1, DCF, SZ2, DTOP, [], SLIME, (-1, 0, 0))
plane_rect(walks, "z", SZ0, SX0, Y1, DX0, DTOP, [], SLIME, (0, 1, 0))
plane_rect(walks, "z", SZ2, SX0, DCF, DX2, DTOP, [(T2[0], Y1, T2[2], TT)], SLIME, (0, -1, 0))
plane_rect(walks, "x", SX0, SZ1, DCF, SZ2, DTOP, [], SLIME, (1, 0, 0))
ceiling(walks, DX0, DZ0, DX2, DZ1, DTOP, CEIL)
ceiling(walks, SX0, SZ0, DX2, SZ2, DTOP, CEIL)
for (x0, z0, x1, z1), which in ((T1, "nse"), (T2, "wes")):
    tiled(walks, x0, z0, x1, z1, Y1, FLAGS)
    walls(walks, x0, z0, x1, z1, Y1, TT, BRICK, which, inward=True)
    ceiling(walks, x0, z0, x1, z1, TT, CEIL)
# grates where the channels run in and out of the walls
decal(props, "z", DZ0, DX1 + 40, DCF, DX2 - 40, DCF + 110, IRON, 1)
decal(props, "x", SX0, SZ1 + 30, DCF, SZ2 - 30, DCF + 100, IRON, 1)
decal(props, "x", DX2, SZ1 + 30, DCF, SZ2 - 30, DCF + 100, IRON, -1)
decal(props, "x", DX0, -560, Y1 + 70, -480, Y1 + 150, MARKS, 1)
spots["rats1_region"] = [[DX0 + 20, T1[1] + 10], [DX0 + 20, T1[3] - 10], [T1[2] - 20, T1[3] - 10],
                         [T1[2] - 20, T1[1] + 10]]
spots["rats1_members"] = [[1120, Y1, -860], [1120, Y1, -780], [1060, Y1, -820]]
spots["rats2_region"] = [[T2[0] + 10, SZ0 + 20], [T2[0] + 10, T2[3] - 20], [T2[2] - 10, T2[3] - 20],
                         [T2[2] - 10, SZ0 + 20]]
spots["rats2_members"] = [[40, Y1, 250], [120, Y1, 250], [80, Y1, 190]]
spots["ammo_cache"] = [1140, Y1, -820]
spots["tribal_t2"] = [80, Y1, 260]
lamp(props, DX0, -650.0, Y1 + 230, "w")
lamp(props, 0.0, SZ0, Y1 + 230, "n")
lamp(props, -400.0, SZ0, Y1 + 230, "n")
lamp(props, T1[2], -820.0, Y1 + 170, "e", radius=280.0)
lamp(props, 80.0, T2[3], Y1 + 170, "s", radius=280.0)

# ================================================================================================ W and R: the return stair
WX0, WX1 = -1280.0, SX0
S2 = (-900.0, -700.0)                     # the stair down to the guard room, off W's south wall
tiled(walks, WX0, SZ0, WX1, SZ1, Y1, FLAGS)
plane_rect(walks, "z", SZ0, WX0, Y1, WX1, DTOP, [], BRICK, (0, 1, 0))
plane_rect(walks, "z", SZ1, WX0, Y1, WX1, DTOP, [(S2[0], Y1, S2[1], DTOP)], BRICK, (0, -1, 0))
ceiling(walks, WX0, SZ0, WX1, SZ1, DTOP, CEIL)
RX0, RX1 = -1480.0, WX0
RZ0, RZ1, RZ2, RZ3 = -660.0, -620.0, SZ0, SZ1   # the door's step, the stair's top, its foot, the landing's end


def rfloor(x, z):
    if z <= RZ1:
        return Y0
    if z >= RZ2:
        return Y1
    return Y0 + (Y1 - Y0) * (z - RZ1) / (RZ2 - RZ1)


tiled(walks, RX0, RZ0, RX1, RZ1, Y0, BRICK)
tiled(walks, RX0, RZ1, RX1, RZ2, Y0, FLAGS, Y1, along="z")
tiled(walks, RX0, RZ2, RX1, RZ3, Y1, FLAGS)
walls(walks, RX0, RZ0, RX1, RZ1, Y0, Y0 + TUN, BRICK, "we", inward=True)
walls(walks, RX0, RZ1, RX1, RZ2, rfloor, lambda x, z: rfloor(x, z) + TUN, BRICK, "we", inward=True)
walls(walks, RX0, RZ2, RX1, RZ3, Y1, DTOP, BRICK, "w", inward=True)
plane_rect(walks, "z", RZ0, RX0, Y0, RX1, Y0 + TUN, [(RDOOR[0], Y0, RDOOR[1], 170)], BRICK, (0, 1, 0))
plane_rect(walks, "z", RZ3, RX0, Y1, RX1, DTOP, [], BRICK, (0, -1, 0))
ceiling(walks, RX0, RZ0, RX1, RZ1, Y0 + TUN, CEIL)
ceiling(walks, RX0, RZ1, RX1, RZ2, Y0 + TUN, CEIL, DTOP, along="z")
ceiling(walks, RX0, RZ2, RX1, RZ3, DTOP, CEIL)
lamp(props, RX0, -470.0, 110.0, "w")
lamp(props, -900.0, SZ0, Y1 + 230, "n")

# ================================================================================================ S2, E, X: down to the guard room
S2Z0, S2Z1 = SZ1, 180.0


def s2floor(x, z):
    return Y1 + (Y2 - Y1) * (z - S2Z0) / (S2Z1 - S2Z0)


tiled(walks, S2[0], S2Z0, S2[1], S2Z1, Y1, FLAGS, Y2, along="z")
walls(walks, S2[0], S2Z0, S2[1], S2Z1, s2floor, lambda x, z: s2floor(x, z) + TUN, BRICK, "we", inward=True)
ceiling(walks, S2[0], S2Z0, S2[1], S2Z1, DTOP, CEIL, Y2 + TUN, along="z")
EX0, EX1, EZ0, EZ1, ETOP = -1000.0, -600.0, 180.0, 600.0, Y2 + TUN
XZ0, XZ1 = 400.0, 600.0                   # the way on to the great cistern
tiled(walks, EX0, EZ0, EX1, EZ1, Y2, FLAGS)
plane_rect(walks, "z", EZ0, EX0, Y2, EX1, ETOP, [(S2[0], Y2, S2[1], ETOP)], MOSS, (0, 1, 0))
plane_rect(walks, "z", EZ1, EX0, Y2, EX1, ETOP, [], MOSS, (0, -1, 0))
plane_rect(walks, "x", EX0, EZ0, Y2, EZ1, ETOP, [], MOSS, (1, 0, 0))
plane_rect(walks, "x", EX1, EZ0, Y2, EZ1, ETOP, [(XZ0, Y2, XZ1, ETOP)], MOSS, (-1, 0, 0))
ceiling(walks, EX0, EZ0, EX1, EZ1, ETOP, CEIL)
# the guards' bench along the west wall (40 high: a step, not a deck) and the colony's water marks
C.block(walks, EX0 + 1, 260.0, EX0 + 61, 520.0, Y2, Y2 + 40, DARK, which="nse")
decal(props, "z", EZ0, -680, Y2 + 70, -620, Y2 + 130, MARKS, 1)
spots["guard_room"] = {"health": [-800, Y2, 300], "ammo": [-700, Y2, 520], "tribal": [-940, Y2 - 0, 220]}
lamp(props, EX0, 220.0, Y2 + 220, "w")
lamp(props, -800.0, EZ1, Y2 + 220, "s")
XX0, XX1 = EX1, -400.0
tiled(walks, XX0, XZ0, XX1, XZ1, Y2, FLAGS)
walls(walks, XX0, XZ0, XX1, XZ1, Y2, ETOP, MOSS, "ns", inward=True)
ceiling(walks, XX0, XZ0, XX1, XZ1, ETOP, CEIL)

# ================================================================================================ F. the great cistern
FX0, FX1, FZ0, FZ1 = -400.0, 800.0, 400.0, 1400.0
LANDX = 660.0                         # the dry landing (x 660..800, z 400..740) and the gallery stair along the east wall
LZ1 = 740.0
GZ0, GY = 1240.0, -100.0              # the gallery (z 1240..1400) at -100: perch 230 over the floor, 200 over the water
HOL = (FX0, FZ0, LANDX, GZ0)          # the flooded floor
PLINTH = (120.0, 740.0, 280.0, 900.0)
PLY = FW + 70                         # the plinth's top: 70 over the floor, 40 over the water
# three rows about 300 apart; the back row only at the sides, out of the gallery lookout's lines to the way in, the
# plinth and the east door
PILLARS = [(-200, 560), (100, 560), (400, 560), (-200, 860), (500, 860), (-200, 1120), (560, 1120)]
PR = 60.0
PIL = [(x - PR, z - PR, x + PR, z + PR) for x, z in PILLARS]
GDOOR = (500.0, 660.0)                # the east doorway (z), 170 high, onto the return stair


def gstair(x, z):
    return FL + (GY - FL) * (z - LZ1) / (GZ0 - LZ1)


C.water_box(wet, HOL, PIL + [PLINTH, (0.0, FZ0, 0.0, GZ0), (512.0, FZ0, 512.0, GZ0), (FX0, 512.0, LANDX, 512.0),
                              (FX0, 1024.0, LANDX, 1024.0)], FW, FL, MUD, WATER, wm=wtr)
tiled(hall, LANDX, FZ0, FX1, LZ1, FL, PAVE)
tiled(hall, LANDX, LZ1, FX1, GZ0, FL, PAVE, GY, along="z")
tiled(hall, FX0, GZ0, FX1, FZ1, GY, PAVE)
strip(hall, (LANDX, FZ0), (LANDX, LZ1), FW, FW, FL, FL, ASHLAR, (-1, 0, 0))            # the landing's face
walls(hall, LANDX, LZ1, FX1, GZ0, FW, gstair, ASHLAR, "w")                            # the stair's side
strip(hall, (FX0, GZ0), (LANDX, GZ0), FW, FW, GY, GY, ASHLAR, (0, -1, 0))             # the gallery's face
C.block(hall, *PLINTH, FW, PLY, ASHLAR, top=PAVE, size=None)
for p in PIL:
    walls(hall, *p, FW, FTOP, ASHLAR)
    walls(props, p[0] - 6, p[1] - 6, p[2] + 6, p[3] + 6, FL - 10, FL + 40, BRICK, step=300.0)   # a wet plinth band
plane_rect(hall, "z", FZ0, FX0, FW, LANDX, FTOP, [], ASHLAR, (0, 1, 0))
plane_rect(hall, "z", FZ0, LANDX, FL, FX1, FTOP, [], ASHLAR, (0, 1, 0))
plane_rect(hall, "x", FX0, FZ0, FW, GZ0, FTOP, [(XZ0, FL, XZ1, ETOP)], ASHLAR, (1, 0, 0))
plane_rect(hall, "x", FX0, GZ0, GY, FZ1, FTOP, [], ASHLAR, (1, 0, 0))
plane_rect(hall, "x", FX1, FZ0, FL, LZ1, FTOP, [(GDOOR[0], FL, GDOOR[1], FL + 170)], ASHLAR, (-1, 0, 0))
walls(hall, LANDX, LZ1, FX1, GZ0, gstair, FTOP, ASHLAR, "e", inward=True)
plane_rect(hall, "x", FX1, GZ0, GY, FZ1, FTOP, [], ASHLAR, (-1, 0, 0))
plane_rect(hall, "z", FZ1, FX0, GY, FX1, FTOP, [], ASHLAR, (0, -1, 0))
ceiling(hall, FX0, FZ0, FX1, FZ1, FTOP, VAULT, size=250.0)
# the gallery's front: a balustrade 100 high (no collider: the fall is 230 at most, into the water), cut to a rim
# of 20 where the lookout stands (x 150..450), 1 short of the west wall
RIM = (150.0, 450.0)
lip(hall, (FX0 + 1, GZ0), (RIM[0], GZ0), GY, GY, ASHLAR, h=100, thick=12, caps=(False, True))
lip(hall, (RIM[0], GZ0), (RIM[1], GZ0), GY, GY, ASHLAR, h=20, thick=12, caps=(False, False))
lip(hall, (RIM[1], GZ0), (LANDX - 1, GZ0), GY, GY, ASHLAR, h=100, thick=12, caps=(True, True))
decal(props, "x", FX0, 700, FL + 60, 780, FL + 140, MARKS, 1)
decal(props, "z", FZ0, 200, FL + 70, 280, FL + 150, MARKS, 1)
spots["plinth"] = [(PLINTH[0] + PLINTH[2]) / 2, PLY, (PLINTH[1] + PLINTH[3]) / 2]
spots["perch"] = [300, GY, GZ0 + 25]
spots["pillars"] = PILLARS
spots["crawler_region"] = [[FX0 + 20, FZ0 + 20], [FX0 + 20, GZ0 - 20], [LANDX - 20, GZ0 - 20], [LANDX - 20, FZ0 + 20]]
spots["walker_region"] = [[300, FZ0 + 20], [300, 1000], [LANDX - 20, 1000], [LANDX - 20, FZ0 + 20]]
spots["gallery_ammo"] = [-300, GY, 1330]
spots["g_door"] = [820, FL, (GDOOR[0] + GDOOR[1]) / 2]
lamp(props, 100.0, FZ0, FL + 280, "n", radius=520.0)
lamp(props, FX0, 900.0, FL + 280, "w", radius=520.0)
lamp(props, FX1, 720.0, FL + 220, "e", radius=420.0)
lamp(props, 300.0, FZ1, GY + 170, "s", radius=420.0)           # the lookout's lamp
lamp(props, FX1, 1320.0, GY + 170, "e", radius=320.0)

# ================================================================================================ G. the way out
reveal(hall, "x", FX1, FX1 + 40, GDOOR[0], GDOOR[1], FL, 170.0, ASHLAR, PAVE)
GX0, GXS, GX1, GX2 = FX1 + 40, 920.0, 1500.0, 1700.0   # a level floor 80 past the door, the stair, the landing
GZA, GZB = 480.0, 680.0


def gfloor(x, z):
    if x <= GXS:
        return FL
    return FL + (Y0 - FL) * (x - GXS) / (GX1 - GXS) if x < GX1 else Y0


tiled(hall, GX0, GZA, GXS, GZB, FL, FLAGS)
tiled(hall, GXS, GZA, GX1, GZB, FL, FLAGS, Y0, along="x")
tiled(hall, GX1, GZA, GX2, GZB, Y0, FLAGS)
walls(hall, GX0, GZA, GXS, GZB, FL, FL + TUN, BRICK, "ns", inward=True)
walls(hall, GXS, GZA, GX1, GZB, gfloor, lambda x, z: gfloor(x, z) + TUN, BRICK, "ns", inward=True)
walls(hall, GX1, GZA, GX2, GZB, Y0, Y0 + TUN, BRICK, "nse", inward=True)
plane_rect(hall, "x", GX0, GZA, FL, GZB, FL + TUN, [(GDOOR[0], FL, GDOOR[1], FL + 170)], BRICK, (1, 0, 0))
ceiling(hall, GX0, GZA, GXS, GZB, FL + TUN, CEIL)
ceiling(hall, GXS, GZA, GX1, GZB, FL + TUN, CEIL, Y0 + TUN, along="x")
ceiling(hall, GX1, GZA, GX2, GZB, Y0 + TUN, CEIL)
decal(props, "x", GX2, 520, Y0, 640, Y0 + 220, DOOR, -1)
spots["exit"] = [1635, Y0, 580]
lamp(props, 1200.0, GZA, FL + 330, "n", radius=320.0)
lamp(props, GX2, 500.0, Y0 + 230, "e", radius=300.0)

# ------------------------------------------------------------------------------------------------ boundary colliders
for (a, b) in (((-1600, -1800), (1800, -1800)), ((1800, -1800), (1800, 1500)), ((1800, 1500), (-1600, 1500)),
               ((-1600, 1500), (-1600, -1800))):
    collider(edges, a, b, -500, 800)

for m in (upper, walks, hall, wet, wtr, props, edges):
    m.build()

# ------------------------------------------------------------------------------------------------ light: oil lamps
level = [o for o in coll.all_objects if o.type == "MESH"]


def extra(x, z, y, mname):
    if z < -1630:      # the way back up to the town: darkness
        return (0.4, 0.42, 0.5)
    wet_ = (y < FL + 60 and z > FZ0 - 1 and x < FX1 + 1) or \
        (y < Y1 + 25 and ((x > DX0 - 1 and z > DZ0 - 1) or (SZ0 - 1 < z < SZ2 + 1 and x > SX0 - 1))) or \
        (y < Y0 + 20 and -899 > x > -1261 and z > -830)
    if wet_:            # the water's green tint low on the walls round it
        return (0.85, 1.12, 1.0)
    return (1.0, 1.0, 1.0)


C.bake(level, (0.0, 0.0, -1.0), (0.0, 0.0, 0.0), (0.12, 0.16, 0.25), lamps=LAMPS, extra=extra, shadow=0.0,
       ao_strength=0.4)

# the water: dark green-blue, warmer under the lamps
for o in level:
    if o.name != "water":
        continue
    m = o.data
    attr = m.color_attributes["Col"]
    for p in m.polygons:
        for li in p.loop_indices:
            co = o.matrix_world @ m.vertices[m.loops[li].vertex_index].co
            gx, gz, gy = co.x, -co.y, co.z
            c = [0.06, 0.14, 0.14]
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
    if isinstance(v, dict):
        return {k: tup(x) for k, x in v.items()}
    return v


with open(os.path.join(C.OUT, NAME + "_spots.json"), "w", encoding="utf-8") as f:
    json.dump({k: tup(v) for k, v in spots.items()}, f, indent=1, default=str)
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(C.OUT, NAME + ".blend"))
print("UNDERCISTERN", json.dumps(report, default=str))
print("PARTS", json.dumps({o.name: sum(len(p.vertices) - 2 for p in o.data.polygons) for o in level}))
