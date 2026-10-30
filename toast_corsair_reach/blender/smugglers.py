"""Smugglers' Run (Corsair Reach 1.4, optional): builds the level from nothing and exports blender/out/smugglers.glb.

    blender --background --factory-startup --addons jfg64 --python smugglers.py

The smugglers' tunnels under the docks, at night. From the docks' side door a stone stair goes down (20 -> -60) to
the rum cellar (casks, a green lamp, 3 drowned crew among three vats); a small loop of brick tunnels round a block
(a dead end with a Tribal, a niche with ammo) slopes on to the drowned tavern (-80): its floor under 30 of water,
three stout tables and the bar counter as cover, a wooden stair up the north wall to the gallery (perch 180) where
the lookout stands, a Tribal in the alcove behind it. East of the tavern a passage passes the strongroom's square
window (sill 30; the chest with the shotgun, the health upgrade, two Tribals) and turns north, down into the rock
(-80 -> -150): the landing stage (3 deckhands among cargo) and the passage on to the grotto's torchlight (the exit).

Game units: x east, z south (north is -z), y up. The level's numbers are in levels/1.4_smugglers.md (As built).
"""
import json
import math
import os
import random
import sys

import bpy

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import common as C  # noqa: E402
from common import Mesh, tiled, post, collider, strip, walls, ceiling, plane_rect, lip, fence  # noqa: E402
import jfg64  # noqa: E402

NAME = "smugglers"
scene, coll = C.new_scene(NAME)
rnd = random.Random(41)

YA, YB, YD = 20.0, -60.0, -80.0        # the stair's top (the docks' side door), the cellar and tunnels, the tavern
YW, YH, YF = -85.0, -115.0, -150.0     # the tavern's water and the floor under it (30 deep), the landing stage
TUN = 280.0                            # tunnels 200 wide, 280 high


# ------------------------------------------------------------------------------------------------ our own images
def tavern_sign_px(x, y):
    """The tavern's sign: a dark board in a frame, a foaming tankard on the left, an anchor on the right."""
    frame = (0.13, 0.08, 0.05)
    if x < 2 or x > 61 or y < 2 or y > 29:
        return frame
    board = (0.3, 0.18, 0.09) if (y // 7) % 2 else (0.27, 0.16, 0.08)
    if y % 7 == 0:
        board = (0.18, 0.11, 0.06)
    amber, foam, pale = (0.86, 0.58, 0.14), (0.92, 0.9, 0.8), (0.82, 0.76, 0.6)
    if 10 <= x <= 23 and 9 <= y <= 25:
        return foam if y <= 11 else amber if (x - 10) % 4 else (0.7, 0.45, 0.1)
    if 8 <= x <= 25 and 6 <= y <= 9 and (x + y) % 3:
        return foam
    if 24 <= x <= 28 and 12 <= y <= 21 and not (25 <= x <= 26 and 14 <= y <= 19):
        return amber
    if 44 <= x <= 46 and 6 <= y <= 24:
        return pale
    if 39 <= x <= 51 and 9 <= y <= 10:
        return pale
    d = math.hypot(x - 45, y - 18)
    if 6.0 <= d <= 7.6 and y >= 19:
        return pale
    if math.hypot(x - 45, y - 5) < 2.0:
        return pale
    return board


def bottles_px(x, y):
    """Two shelves of bottles: green, brown, dark blue and amber, with stoppers and a highlight."""
    wall = (0.12, 0.1, 0.08)
    if y in (14, 15, 30, 31):
        return (0.36, 0.22, 0.1) if y in (14, 30) else (0.2, 0.12, 0.06)
    shelf = 0 if y < 14 else 16
    yy = y - shelf
    cols = [(0.15, 0.4, 0.15), (0.38, 0.2, 0.08), (0.12, 0.15, 0.35), (0.65, 0.42, 0.1)]
    k = (x - 1) // 5
    xx = (x - 1) % 5
    if 0 <= k <= 5 and xx < 3:
        tall = 4 if (k + shelf // 16) % 2 else 2
        if yy >= tall + 3:
            c = cols[(k + shelf // 8) % 4]
            return (min(1, c[0] + 0.25), min(1, c[1] + 0.25), min(1, c[2] + 0.25)) if xx == 0 and yy > tall + 5 else c
        if xx == 1 and yy >= tall:
            return (0.55, 0.45, 0.3) if yy == tall else cols[(k + shelf // 8) % 4]
    return wall


def cask_px(x, y):
    """A cask's end: staves across, an iron hoop round the rim, a bung in the middle."""
    d = math.hypot(x - 15.5, y - 15.5)
    if d > 15.5:
        return (0.08, 0.06, 0.05)
    if d > 13.2:
        return (0.2, 0.2, 0.22) if d > 14 else (0.32, 0.32, 0.34)
    v = 0.85 + 0.15 * (((x * 13 + y * 3) % 7) / 7.0)
    c = (0.48 * v, 0.31 * v, 0.15 * v)
    if x % 6 == 0:
        c = (0.3, 0.19, 0.09)
    if d < 2.2:
        c = (0.16, 0.1, 0.05)
    return c


def grotto_glow_px(x, y):
    """Torchlight round the passage's last bend: a warm orange opening fading into the dark rock."""
    d = math.hypot((x - 15.5) / 1.0, (y - 18) / 1.3)
    k = max(0.0, 1 - d / 15.0)
    return (0.1 + 0.85 * k ** 1.2, 0.07 + 0.55 * k ** 1.5, 0.05 + 0.2 * k ** 2.2)


# ------------------------------------------------------------------------------------------------ materials
MATS = []


def mat(material):
    MATS.append(material)
    return len(MATS) - 1


WALL = mat(C.game(0x1736))     # mossy stone blocks: the stair, cellar and tunnels
FLOOR = mat(C.game(0x16DF))    # grey flagstones: the cellar, tunnels and the tavern's dry floor
STAIR = mat(C.game(0x060D))    # pale worn stone: the cellar stair
CEIL = mat(C.game(0x07F2))     # dark rock: ceilings, the way back's darkness
BRICK = mat(C.game(0x0CAF))    # grey stone blocks: the tavern's walls
BOARDS = mat(C.game(0x16D9))   # upright boards: the tavern's ceiling, the gallery's front, rails
PLANK = mat(C.game(0x16DB))    # planks: tables, the bar, the stair and gallery floor, cargo
MASON = mat(C.game(0x0828))    # the strongroom's walls
PAVE = mat(C.game(0x1946))     # the strongroom's floor
MUD = mat(C.game(0x1959))      # the floor under the tavern's water
CLIFF = mat(C.game(0x0C40))    # the rock near the grotto: the landing stage, the last passage
WATER = mat(C.game(0x0DED, "water"))
SIGN = mat(C.own_material("tavern_sign", C.own_image("tavern_sign", 64, 32, tavern_sign_px)))
BOTTLES = mat(C.own_material("bottle_shelves", C.own_image("bottle_shelves", 32, 32, bottles_px)))
CASK = mat(C.own_material("cask_end", C.own_image("cask_end", 32, 32, cask_px)))
GLOW = mat(C.own_material("grotto_glow", C.own_image("grotto_glow", 32, 32, grotto_glow_px)))
EDGE = jfg64.boundary_material()


def mesh(name, uv=200.0):
    return Mesh(name, MATS, coll, uv_size=uv)


shell = mesh("cellar", 200.0)     # the stair, the cellar, the tunnels
tav = mesh("tavern", 200.0)       # the tavern's walls, floors, stair and gallery
hol = mesh("tavern_floor", 200.0)
wtr = Mesh("tavern_water", MATS, coll, uv_size=512.0)
east = mesh("east", 200.0)        # the strongroom passage, the strongroom, the way down, the landing, the last passage
wood = mesh("wood", 160.0)        # tables, bar, rails, cargo, beams
props = mesh("props", 128.0)      # vats, decals, brackets
edges = Mesh("colliders", [EDGE], coll)
spots = {}


def decal(m, plane, c, u0, v0, u1, v1, mat_, facing_sign):
    """A picture on a wall, once, 2 in front of it (two faces in one plane flicker): plane "x" (u is z) or "z"
    (u is x), facing +1 or -1 along the plane's axis, read the right way round from that side."""
    o = c + 2 * facing_sign
    if plane == "z":   # seen looking north (+1), east is on the right; looking south (-1), west is
        a, b = (u0, u1) if facing_sign > 0 else (u1, u0)
        pts = [(a, o, v0), (b, o, v0), (b, o, v1), (a, o, v1)]
        f = (0, facing_sign, 0)
    else:              # seen looking west (+1), north is on the right; looking east (-1), south is
        a, b = (u1, u0) if facing_sign > 0 else (u0, u1)
        pts = [(o, a, v0), (o, b, v0), (o, b, v1), (o, a, v1)]
        f = (facing_sign, 0, 0)
    m.face(pts, mat_, f, [(0, 0), (1, 0), (1, 1), (0, 1)])


def bracket(m, x, z, y, wall):
    """A lantern's iron bracket on a wall (`wall` the side it hangs from: "n", "s", "e" or "w"), 2 off it."""
    off = {"n": (0, 14), "s": (0, -14), "e": (-14, 0), "w": (14, 0)}[wall]
    bx, bz = x + off[0], z + off[1]
    m.box(bx - 10, bz - 10, bx + 10, bz + 10, y - 16, y, PLANK, bottom=True)


# ================================================================================================ A. the cellar stair
AX0, AX1 = -1400.0, -1200.0
A_TOP, A_FOOT = -860.0, -600.0     # the landing at 20 to z -860, the stair down to -60 at z -600


def afloor(x, z):
    if z <= A_TOP:
        return YA
    if z >= A_FOOT:
        return YB
    return YA + (YB - YA) * (z - A_TOP) / (A_FOOT - A_TOP)


tiled(shell, AX0, -1000, AX1, A_TOP, YA, STAIR)
tiled(shell, AX0, A_TOP, AX1, A_FOOT, YA, STAIR, YB, along="z")
tiled(shell, AX0, A_FOOT, AX1, -400, YB, FLOOR)
walls(shell, AX0, -1000, AX1, A_TOP, YA, YA + TUN, WALL, "ew", inward=True)
walls(shell, AX0, A_TOP, AX1, A_FOOT, afloor, lambda x, z: afloor(x, z) + TUN, WALL, "ew", inward=True)
walls(shell, AX0, A_FOOT, AX1, -400, YB, YB + TUN, WALL, "ws", inward=True)
ceiling(shell, AX0, -1000, AX1, A_TOP, YA + TUN, CEIL)
ceiling(shell, AX0, A_TOP, AX1, A_FOOT, YA + TUN, CEIL, YB + TUN, along="z")
ceiling(shell, AX0, A_FOOT, AX1, -400, YB + TUN, CEIL)
# the way back: a dark recess in the north wall, the docks' side door somewhere up it
REC = (-1360.0, -1130.0, -1240.0, -1000.0)
plane_rect(shell, "z", -1000, AX0, YA, AX1, YA + TUN, [(REC[0], YA, REC[2], YA + 220)], WALL, (0, 1, 0))
tiled(shell, *REC, YA, CEIL)
walls(shell, *REC, YA, YA + 220, CEIL, "nwe", inward=True)
ceiling(shell, *REC, YA + 220, CEIL)
bracket(props, AX1, -930, 230, "e")
spots["start"] = [-1300, YA, -910]
spots["way_back_exit"] = [-1300, YA, -1065]
spots["stair_lantern"] = [AX1 - 14, 230, -930]

# ================================================================================================ B. the rum cellar
BX0, BX1, BZ0, BZ1, BTOP = -1200.0, -700.0, -600.0, -200.0, 300.0
tiled(shell, BX0, BZ0, BX1, BZ1, YB, FLOOR)
ceiling(shell, BX0, BZ0, BX1, BZ1, BTOP, CEIL)
plane_rect(shell, "x", BX0, BZ0, YB, BZ1, BTOP, [(BZ0, YB, -400, YB + TUN)], WALL, (1, 0, 0))
plane_rect(shell, "x", BX1, BZ0, YB, BZ1, BTOP, [(-400, YB, BZ1, YB + TUN)], WALL, (-1, 0, 0))
plane_rect(shell, "z", BZ0, BX0, YB, BX1, BTOP, [], WALL, (0, 1, 0))
plane_rect(shell, "z", BZ1, BX0, YB, BX1, BTOP, [], WALL, (0, -1, 0))
# three great vats (cover: 92 across, 110 tall), one per member; region x -1135..-765, z -560..-240
CELLAR_COVER = [(-1050, -470), (-850, -470), (-950, -320)]
for (x, z) in CELLAR_COVER:
    post(props, x, z, 46, YB, YB + 110, PLANK, n=8, phase=math.pi / 8)
spots["cellar_cover"] = CELLAR_COVER
spots["cellar_region"] = [[-1135, -560], [-765, -560], [-765, -240], [-1135, -240]]
# casks stacked three high along the north and south walls, their ends to the room (no shelves: a long thin shelf
# top filled the hero's collision list)
for (zc, sgn, x0, x1) in ((BZ0, 1, -1180, -720), (BZ1, -1, -1180, -940)):
    n = int((x1 - x0) // 55)
    for row in range(3):
        y0 = YB + 2 + row * 54
        for k in range(n):
            u = x0 + k * 55 + 2
            decal(props, "z", zc, u, y0, u + 50, y0 + 50, CASK, sgn)
spots["cellar_light"] = [-950, 200, -400]

# ================================================================================================ C. the tunnels
# a loop round a block (x -500..-300, z -200..100): the north run from the cellar, west and east runs, the south run
# on to the tavern; a dead end west off the west run (Tribal 1), a niche south off the south run (ammo)
RN = (-700.0, -400.0, -100.0, -200.0)
RW = (-700.0, -200.0, -500.0, 100.0)
RE = (-300.0, -200.0, -100.0, 100.0)
RS = (-700.0, 100.0, -100.0, 300.0)
RTOP = YB + TUN
for r in (RN, RW, RE, RS):
    tiled(shell, *r, YB, FLOOR)
    ceiling(shell, *r, RTOP, CEIL)
plane_rect(shell, "z", -400, -700, YB, -100, RTOP, [], WALL, (0, 1, 0))
plane_rect(shell, "x", -100, -400, YB, 100, RTOP, [], WALL, (-1, 0, 0))
plane_rect(shell, "z", -200, -500, YB, -300, RTOP, [], WALL, (0, -1, 0))   # the block
plane_rect(shell, "x", -500, -200, YB, 100, RTOP, [], WALL, (-1, 0, 0))
plane_rect(shell, "x", -300, -200, YB, 100, RTOP, [], WALL, (1, 0, 0))
plane_rect(shell, "z", 100, -500, YB, -300, RTOP, [], WALL, (0, 1, 0))
SPUR = (-1000.0, -100.0, -700.0, 80.0)
plane_rect(shell, "x", -700, -200, YB, 300, RTOP, [(SPUR[1], YB, SPUR[3], YB + 260)], WALL, (1, 0, 0))
NICHE = (-450.0, 300.0, -330.0, 400.0)
plane_rect(shell, "z", 300, -700, YB, -100, RTOP, [(NICHE[0], YB, NICHE[2], YB + 180)], WALL, (0, -1, 0))
tiled(shell, *SPUR, YB, FLOOR)
walls(shell, *SPUR, YB, YB + 260, WALL, "nsw", inward=True)
ceiling(shell, *SPUR, YB + 260, CEIL)
tiled(shell, *NICHE, YB, FLOOR)
walls(shell, *NICHE, YB, YB + 180, WALL, "sew", inward=True)
ceiling(shell, *NICHE, YB + 180, CEIL)
# the link down into the tavern (-60 -> -80)
LINK = (-100.0, 100.0, 0.0, 300.0)
tiled(shell, *LINK, YB, FLOOR, YD, along="x")
walls(shell, *LINK, lambda x, z: YB + (YD - YB) * (x + 100) / 100, lambda x, z: YB + TUN + (YD - YB) * (x + 100) / 100,
      WALL, "ns", inward=True)
ceiling(shell, *LINK, YB + TUN, CEIL, YD + TUN, along="x")
TUNNEL_LANTERNS = [(-400, -400, 140, "n"), (-700, 0, 140, "w"), (-100, -50, 140, "e"), (-560, 300, 140, "s"),
                   (-1000, -10, 110, "w")]
for (x, z, y, w) in TUNNEL_LANTERNS:
    bracket(props, x, z, y, w)
spots["tunnel_lanterns"] = [[x, y, z] for x, z, y, _ in TUNNEL_LANTERNS]
spots["tribal_dead_end"] = [-930, -10]
spots["ammo_niche"] = [-390, 360]

# ================================================================================================ D. the drowned tavern
TX0, TX1, TZ0, TZ1, TTOP = 0.0, 800.0, -100.0, 500.0, 570.0
HOLLOW = (120.0, 100.0, 700.0, 500.0)    # the flooded floor: water at -85 over a floor at -115
GAL = (150.0, -100.0, 800.0, 60.0)       # the stair (x 150..550, -80 -> 100) and the gallery (x 550..800, at 100)
GAL_Y = 100.0
for r in C.rects_minus((TX0, TZ0, TX1, TZ1), [HOLLOW, GAL]):
    tiled(tav, *r, YD, FLOOR)


def stair_top(x, z):
    return YD + (GAL_Y - YD) * (x - 150) / 400


tiled(tav, 150, -100, 550, 60, YD, PLANK, GAL_Y, along="x")
tiled(tav, 550, -100, 800, 60, GAL_Y, PLANK)
walls(tav, 150, -100, 550, 60, YD, stair_top, BOARDS, "s")
walls(tav, 550, -100, 800, 60, YD, GAL_Y, BOARDS, "s")
# the hollow's sides (the dry floor's edge), its floor and water in one grid through every hole's edges
strip(tav, (120, 500), (120, 100), YH, YH, YD, YD, WALL, (1, 0, 0))
strip(tav, (120, 100), (700, 100), YH, YH, YD, YD, WALL, (0, 1, 0))
strip(tav, (700, 100), (700, 500), YH, YH, YD, YD, WALL, (-1, 0, 0))
TABLES = [(180.0, 170.0, 270.0, 260.0), (380.0, 160.0, 470.0, 250.0), (560.0, 220.0, 650.0, 310.0)]
COUNTER = (250.0, 360.0, 470.0, 440.0)
WHOLES = TABLES + [COUNTER, (512.0, 100.0, 512.0, 500.0)]   # zero-width: the water's texture repeats at 512
C.water_box(hol, HOLLOW, WHOLES, YH, YW, MUD, WATER, wm=wtr)
for t in TABLES:   # stout tables, 100 over the floor under the water
    tiled(wood, *t, YH + 100, PLANK, size=200.0)
    walls(wood, *t, YH, YH + 100, BOARDS)
tiled(wood, *COUNTER, YH + 115, PLANK)
walls(wood, *COUNTER, YH, YH + 115, PLANK)
spots["tavern_cover"] = [[(t[0] + t[2]) / 2, (t[1] + t[3]) / 2] for t in TABLES + [COUNTER]]
spots["tavern_region"] = [[140, 120], [680, 120], [680, 480], [140, 480]]
# the walls: the way in (west, z 100..300), the way on (east, z 200..400), the alcove behind the gallery (north)
ALC = (680.0, -190.0, 780.0, -100.0)
plane_rect(tav, "x", TX0, TZ0, YD, TZ1, TTOP, [(100, YD, 300, YD + TUN)], BRICK, (1, 0, 0))
plane_rect(tav, "x", TX1, TZ0, YD, TZ1, TTOP, [(200, YD, 400, YD + TUN)], BRICK, (-1, 0, 0))
plane_rect(tav, "z", TZ0, TX0, YD, TX1, TTOP, [(ALC[0], GAL_Y, ALC[2], GAL_Y + 160)], BRICK, (0, 1, 0))
plane_rect(tav, "z", TZ1, TX0, YH, TX1, TTOP, [(TX0, YH, HOLLOW[0], YD), (HOLLOW[2], YH, TX1, YD)], BRICK, (0, -1, 0))
ceiling(tav, TX0, TZ0, TX1, TZ1, TTOP, BOARDS)
tiled(tav, *ALC, GAL_Y, PLANK)
walls(tav, *ALC, GAL_Y, GAL_Y + 160, BRICK, "nwe", inward=True)
ceiling(tav, *ALC, GAL_Y + 160, BOARDS)
# beams under the ceiling (sides and undersides only: their tops would lie against the ceiling)
for zc in (120.0, 320.0):
    for (a, b, f) in (((2, zc - 15), (798, zc - 15), (0, -1, 0)), ((798, zc + 15), (2, zc + 15), (0, 1, 0))):
        strip(wood, a, b, TTOP - 45, TTOP - 45, TTOP - 1, TTOP - 1, PLANK, f, step=260)
    tiled(wood, 2, zc - 15, 798, zc + 15, TTOP - 45, PLANK, facing=(0, 0, -1), size=260)
# a board balustrade 100 high up the stair's open side and along the gallery's front, no collider (a fall is 180
# at most, onto the dry floor or the water: a rail's collider read as an invisible wall over the floor below);
# the lookout's stretch (x 520..700) has only a rim 20 high (a lookout's rim over 20 blocks it firing down: 1.3),
# wide enough that its lines down to the way in, the water and the way on all pass over the rim
RIM_X0 = 520.0
lip(wood, (RIM_X0, 60), (150, 60), stair_top(RIM_X0, 0), YD, BOARDS, h=100, thick=12)
lip(wood, (550, 60), (RIM_X0, 60), GAL_Y, stair_top(RIM_X0, 0), BOARDS, h=20, thick=12, caps=(False, False))
lip(wood, (700, 60), (550, 60), GAL_Y, GAL_Y, BOARDS, h=20, thick=12, caps=(False, False))
lip(wood, (798, 60), (700, 60), GAL_Y, GAL_Y, BOARDS, h=100, thick=12, caps=(False, True))
spots["perch"] = [610, GAL_Y, 38]
spots["tribal_alcove"] = [730, GAL_Y, -150]
spots["lookout_lantern"] = [720, 240, -98]
bracket(props, 720, -100, 240, "n")
# behind the bar: two shelves of bottles and the tavern's sign over them, on the south wall
decal(props, "z", TZ1, 260, -60, 360, 40, BOTTLES, -1)
decal(props, "z", TZ1, 360, -60, 460, 40, BOTTLES, -1)
decal(props, "z", TZ1, 290, 110, 430, 180, SIGN, -1)
spots["bar_candles"] = [[300, YH + 115, 400], [420, YH + 115, 400]]
spots["table_candles"] = [[(t[0] + t[2]) / 2, YH + 100, (t[1] + t[3]) / 2] for t in TABLES]

# ================================================================================================ E. the strongroom passage
P2 = (800.0, 200.0, 1400.0, 400.0)
WIN = (950.0, 1090.0)                  # the window: 140 square, its sill 30 over the passage's floor
SILL, WTOP = YD + 30, YD + 170
tiled(east, *P2, YD, FLOOR)
ceiling(east, *P2, YD + TUN, CEIL)
plane_rect(east, "z", P2[1], P2[0], YD, 1200, YD + TUN, [], WALL, (0, 1, 0))
plane_rect(east, "z", P2[3], P2[0], YD, P2[2], YD + TUN, [(WIN[0], SILL, WIN[1], WTOP)], WALL, (0, -1, 0))
plane_rect(east, "x", P2[2], P2[1], YD, P2[3], YD + TUN, [], WALL, (-1, 0, 0))
# the window's reveal through the wall (z 400..450): its sill, sides and lintel
tiled(east, WIN[0], 400, WIN[1], 450, SILL, MASON)
walls(east, WIN[0], 400, WIN[1], 450, SILL, WTOP, MASON, "ew", inward=True)
ceiling(east, WIN[0], 400, WIN[1], 450, WTOP, MASON)
SR = (850.0, 450.0, 1150.0, 750.0)
SR_TOP = YD + 300
tiled(east, *SR, YD, PAVE)
ceiling(east, *SR, SR_TOP, MASON)
plane_rect(east, "z", SR[1], SR[0], YD, SR[2], SR_TOP, [(WIN[0], SILL, WIN[1], WTOP)], MASON, (0, 1, 0))
plane_rect(east, "z", SR[3], SR[0], YD, SR[2], SR_TOP, [], MASON, (0, -1, 0))
plane_rect(east, "x", SR[0], SR[1], YD, SR[3], SR_TOP, [], MASON, (1, 0, 0))
plane_rect(east, "x", SR[2], SR[1], YD, SR[3], SR_TOP, [], MASON, (-1, 0, 0))
# strongboxes along the side walls (not on the way in), cask ends stacked in the corners
for (x0, z0, x1, z1) in ((860, 560, 920, 640), (1080, 560, 1140, 640)):
    wood.box(x0, z0, x1, z1, YD, YD + 50, PLANK)
for (u0, sgn) in ((870, -1), (1080, -1)):
    for row in range(2):
        for k in range(2):
            decal(props, "z", SR[3], u0 + k * 34, YD + 2 + row * 34, u0 + k * 34 + 32, YD + 34 + row * 34, CASK, sgn)
spots["glass"] = [[WIN[0], 400], [WIN[1], 400], SILL]
spots["chest"] = [1000, YD, 700]
spots["upgrade"] = [1000, YD, 590]
spots["tribals_strongroom"] = [[890, 705], [1110, 705]]

# ================================================================================================ F. the grotto passage
# north from the strongroom passage, down into the rock (-80 -> -150), the landing stage, the last passage
NP = (1200.0, -300.0, 1400.0, 200.0)
tiled(east, *NP, YF, FLOOR, YD, along="z")


def npfloor(x, z):
    return YF + (YD - YF) * (z - NP[1]) / (NP[3] - NP[1])


walls(east, *NP, npfloor, lambda x, z: npfloor(x, z) + TUN, WALL, "ew", inward=True)
ceiling(east, *NP, YF + TUN, CEIL, YD + TUN, along="z")
LR = (1050.0, -750.0, 1450.0, -300.0)
LR_TOP = YF + 400
tiled(east, *LR, YF, FLOOR)
ceiling(east, *LR, LR_TOP, CEIL)
plane_rect(east, "z", LR[1], LR[0], YF, LR[2], LR_TOP, [(1200, YF, 1400, YF + TUN)], CLIFF, (0, 1, 0))
plane_rect(east, "z", LR[3], LR[0], YF, LR[2], LR_TOP, [(1200, YF, 1400, YF + TUN)], CLIFF, (0, -1, 0))
plane_rect(east, "x", LR[0], LR[1], YF, LR[3], LR_TOP, [], CLIFF, (1, 0, 0))
plane_rect(east, "x", LR[2], LR[1], YF, LR[3], LR_TOP, [], CLIFF, (-1, 0, 0))
# cargo the smugglers were moving down to the grotto: three plain stacks (cover), region x 1075..1425, z -720..-330
CARGO = [(1105.0, -665.0, 1195.0, -575.0), (1305.0, -685.0, 1395.0, -595.0), (1205.0, -515.0, 1295.0, -425.0)]
for c in CARGO:
    tiled(wood, *c, YF + 100, PLANK, size=200.0)
    walls(wood, *c, YF, YF + 100, PLANK)
spots["landing_cover"] = [[(c[0] + c[2]) / 2, (c[1] + c[3]) / 2] for c in CARGO]
spots["landing_region"] = [[1075, -720], [1425, -720], [1425, -330], [1075, -330]]
FP = (1200.0, -1000.0, 1400.0, -750.0)
tiled(east, *FP, YF, CLIFF)
ceiling(east, *FP, YF + TUN, CEIL)
walls(east, *FP, YF, YF + TUN, CLIFF, "new", inward=True)
# the passage's end: torchlight round the bend (our own picture on the rock), the exit in front of it
decal(props, "z", FP[1], 1230, YF, 1370, YF + 200, GLOW, 1)
spots["grotto_exit"] = [1300, YF, -955]
spots["start_from_grotto"] = [1300, YF, -850]
LANDING_LANTERNS = [(1050, -520, -50, "w"), (1450, -520, -50, "e"), (1215, -1000, -60, "n"), (1385, -1000, -60, "n")]
for (x, z, y, w) in LANDING_LANTERNS:
    bracket(props, x, z, y, w)
P2_LANTERNS = [(1000, 200, 120, "n"), (1400, 300, 120, "e"), (1200, 0, 60, "w")]
for (x, z, y, w) in P2_LANTERNS:
    bracket(props, x, z, y, w)
spots["landing_lanterns"] = [[x, y, z] for x, z, y, _ in LANDING_LANTERNS]
spots["p2_lanterns"] = [[x, y, z] for x, z, y, _ in P2_LANTERNS]

# ------------------------------------------------------------------------------------------------ boundary colliders
for (a, b) in (((-1600, -1200), (1600, -1200)), ((1600, -1200), (1600, 1000)), ((1600, 1000), (-1600, 1000)),
               ((-1600, 1000), (-1600, -1200))):
    collider(edges, a, b, -400, 900)

for m in (shell, tav, hol, wtr, east, wood, props, edges):
    m.build()

# ------------------------------------------------------------------------------------------------ light: candles
level = [o for o in coll.all_objects if o.type == "MESH"]
WARM = (0.55, 0.33, 0.11)
CANDLE = (0.42, 0.27, 0.09)
GREEN = (0.08, 0.3, 0.12)
LAMPS = [
    (AX1 - 14, -930, 230, 320, WARM),                                   # the stair's lantern
    (-950, -400, 200, 560, GREEN), (-720, -300, 140, 220, CANDLE),      # the cellar's green lamp
    *[(x, z, y, 280, WARM) for (x, z, y, _) in TUNNEL_LANTERNS],
    (-390, 360, 40, 150, CANDLE),                                       # the niche
    (225, 215, 0, 230, CANDLE), (425, 205, 0, 230, CANDLE), (605, 265, 0, 230, CANDLE),   # candles on the tables
    (300, 400, 20, 240, CANDLE), (420, 400, 20, 240, CANDLE),           # on the bar
    (400, 200, 380, 520, (0.22, 0.15, 0.06)),                           # the chandelier
    (720, -86, 240, 320, WARM),                                         # the lookout's lantern
    (40, 200, 120, 220, CANDLE),                                        # the way in
    *[(x, z, y, 300, WARM) for (x, z, y, _) in P2_LANTERNS],
    (1000, 600, 160, 340, (0.3, 0.24, 0.08)),                            # the strongroom's gold light
    *[(x, z, y, 300, WARM) for (x, z, y, _) in LANDING_LANTERNS],
    (1300, -990, -20, 460, (0.75, 0.45, 0.15)),                         # the grotto's torchlight
]


def extra(x, z, y, mname):
    if z < -1000.5:   # the way back: darkness
        return (0.35, 0.35, 0.4)
    return (1.0, 1.0, 1.0)


C.bake(level, (0.0, 0.0, -1.0), (0.0, 0.0, 0.0), (0.17, 0.21, 0.17), lamps=LAMPS, extra=extra, shadow=0.0,
       ao_strength=0.4)

# the water: murky green, warmer under the candles
for o in level:
    if o.name != "tavern_water":
        continue
    m = o.data
    attr = m.color_attributes["Col"]
    for p in m.polygons:
        for li in p.loop_indices:
            co = o.matrix_world @ m.vertices[m.loops[li].vertex_index].co
            gx, gz, gy = co.x, -co.y, co.z
            c = [0.08, 0.17, 0.12]
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
print("SMUGGLERS", json.dumps(report, default=str))
print("PARTS", json.dumps({o.name: sum(len(p.vertices) - 2 for p in o.data.polygons) for o in level}))
