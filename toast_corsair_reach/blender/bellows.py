"""The Bellows (Corsair Reach 3.2, Cinderhold's foundry): builds the level from nothing and exports
blender/out/bellows.glb.

    blender --background --factory-startup --addons jfg64 --python bellows.py
Then in JFG-Studio: reimport_geometry (or import the .glb) into the level `bellows`.

Game coordinates throughout (x east, z south, y up). A foundry on three floors: the ground floor at 350 (carrying on
from the flats' forge gate), the gallery at 600 and the catwalks at 850. Under a roof everywhere, lit by its furnaces
and the molten channel (no sky).
  A  the loading dock (350, 800 x 600, 700 high): the way back to the flats' foundry door in its west wall, carts,
     a crane; the shortcut ramp up to the foreman's office in its east wall (its door at the top, shut until the
     gallery patrol is dead)
  B  the furnace rooms (350) off a right-angled run of corridors: B1 and B2 (furnace hands among coal bunkers),
     B3 a side room (a Tribal, ammo)
  C  the casting hall (350, 1,400 x 1,000, 900 high): the molten channel down its middle (x 340-460) under two iron
     bridges; ingot stacks and the mould bed (the crawlspace S inside it: full health, ammo) on the west floor;
     turrets on plinths and the forgemasters on the east floor; the stair up the east wall to the gallery; the crane
     on the south wall (its release opens the foreman's door); the catwalk across it over the channel at 850 with
     three lookouts' perches on its west side
  D  the gallery (600) along the hall's north wall, the patrol; the east office (D1: health, ammo) and the foreman's
     office (D2, behind the switch door: the tango key, a Tribal); from D2 the stair room (E0) up to the catwalk
  E  the catwalk (850, 200 wide, railed: posts, a rail and a collider), a railed bay with a Tribal
  F  the bellows chamber (850, 900 x 700, 700 high), through the tango key door: the bellows and its furnace; the
     exit door south (its squads keep it shut) and the passage up to the Crown; a side door east under a blue light
     (the Coolant Vents)
Lava (the kit): a surface 30 over a solid floor, banks 36 high, never on the required path.
"""
import json
import math
import os
import sys

import bpy

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import common as C  # noqa: E402
from common import Mesh, tiled, post, collider, strip, walls, ceiling, plane_rect, lip, fence  # noqa: E402
import jfg64  # noqa: E402

NAME = "bellows"
scene, coll = C.new_scene(NAME)

Y0, YG, YC = 350.0, 600.0, 850.0    # the ground floor, the gallery, the catwalks
TUN = 300.0                          # corridors 200 wide, 300 high
DOOR_W, DOOR_H = 160.0, 155.0        # door openings (the mine door 0x19D is 202 x 192)


# ------------------------------------------------------------------------------------------------ our own images
def sigil_px(x, y):
    """The forge-masters' banner (3.1's): an anvil under a flame, orange on soot black, a red border (32 x 64)."""
    if x < 2 or x > 29 or y < 2 or y > 61:
        return (0.45, 0.08, 0.04)
    if y > 52 and abs(x - 15.5) < (y - 52) * 1.3:
        return (0.03, 0.02, 0.02)
    fx, fy = x - 15.5, y - 20.0
    flame = (fx * fx) / 30.0 + ((fy + 4) * (fy + 4)) / 110.0 <= 1.0 and fy > -14
    core = (fx * fx) / 8.0 + ((fy + 1) * (fy + 1)) / 30.0 <= 1.0
    if core:
        return (1.0, 0.86, 0.35)
    if flame:
        return (0.95, 0.42, 0.08)
    if 33 <= y <= 36 and 6 <= x <= 27 or (y == 33 and 3 <= x < 6):
        return (0.85, 0.36, 0.08)
    if 37 <= y <= 41 and 12 <= x <= 19:
        return (0.85, 0.36, 0.08)
    if 42 <= y <= 45 and 8 <= x <= 23:
        return (0.85, 0.36, 0.08)
    return (0.05, 0.04, 0.04) if (x * 3 + y * 5) % 17 else (0.09, 0.06, 0.05)


def hazard_px(x, y):
    """Hazard stripes: yellow and black diagonals (32 x 16), 3.1's."""
    return (0.92, 0.72, 0.1) if ((x + y) // 6) % 2 == 0 else (0.06, 0.05, 0.05)


def mouth_px(x, y):
    """A furnace mouth: white-hot at the bottom, orange, dark at the arch (16 x 16), a grate of bars."""
    if x in (3, 7, 8, 12) and y > 4:
        return (0.12, 0.07, 0.05)
    t = y / 15.0
    k = 0.85 + 0.15 * math.sin(x * 1.3 + y * 0.7)
    return (min(1.0, (0.6 + 0.4 * t) * k), (0.2 + 0.6 * t * t) * k, (0.05 + 0.3 * t ** 3) * k)


def gauge_px(x, y):
    """A pressure gauge on a brass plate: a pale dial, a red sector, the needle (32 x 32)."""
    dx, dy = x - 15.5, y - 15.5
    r = math.hypot(dx, dy)
    if r > 15:
        return (0.42, 0.32, 0.14) if (x + y) % 7 else (0.3, 0.22, 0.1)
    if r > 13:
        return (0.7, 0.55, 0.22)
    a = math.degrees(math.atan2(dy, dx))
    if r < 11 and abs(a + 40) < 5 and r > 1.5:      # the needle, near the red
        return (0.08, 0.06, 0.06)
    if 9 < r < 12 and -75 < a < -10:                 # the red sector
        return (0.8, 0.12, 0.08)
    if 10 < r < 12.5 and int((a + 180) // 22.5) % 2 == 0:
        return (0.15, 0.13, 0.12)
    return (0.9, 0.86, 0.74)


def leather_px(x, y):
    """The bellows' leather: dark tan, creased in folds along it, stitched seams (32 x 32)."""
    fold = 0.75 + 0.25 * math.cos(x / 32.0 * math.tau * 2)
    if y in (3, 28) and x % 4 < 2:
        return (0.65, 0.5, 0.3)
    g = ((x * 13 + y * 7) % 9) / 9.0
    return (0.36 * fold + 0.03 * g, 0.22 * fold + 0.02 * g, 0.12 * fold + 0.01 * g)


def door_px(x, y):
    """An iron door in its frame (32 x 64): riveted plates, a bar across, hazard paint at its foot."""
    if x < 2 or x > 29 or y < 2:
        return (0.12, 0.1, 0.09)
    if y > 56:
        return (0.92, 0.72, 0.1) if ((x + y) // 4) % 2 == 0 else (0.06, 0.05, 0.05)
    if 28 <= y <= 31:
        return (0.5, 0.42, 0.34)
    if x in (5, 26) and y % 8 == 4:
        return (0.6, 0.55, 0.5)
    g = ((x * 5 + y * 11) % 13) / 13.0
    return (0.24 + 0.05 * g, 0.21 + 0.04 * g, 0.19 + 0.04 * g) if (y // 16) % 2 else (0.2 + 0.05 * g, 0.18, 0.16)


# ------------------------------------------------------------------------------------------------ materials
MATS = []


def mat(material):
    MATS.append(material)
    return len(MATS) - 1


FLOOR = mat(C.game(0x16DF))    # grey flagstones: the dock, the furnace rooms, the hall floor
PLATE = mat(C.game(0x1873))    # diamond plate: the gallery, the offices, the bellows chamber, bridges, ramps
GRATE = mat(C.game(0x0DBF))    # slatted grating (opaque): the catwalk and the perches
IRON = mat(C.game(0x0B0C))     # riveted iron plates: the hall's walls, bridges, bunkers, the crane
BRICK = mat(C.game(0x171C))    # furnace brick: the dock, the furnaces, the bellows chamber
RBRICK = mat(C.game(0x0D70))   # dark red brick: the furnace rooms
PANEL = mat(C.game(0x1643))    # dark panels: the offices and the stair room
RAIL = mat(C.game(0x0F66))     # dark riveted rails: the catwalk's edges and rails, posts
CEIL = mat(C.game(0x07F2))     # dark rock: ceilings
RUST = mat(C.game(0x0C3D))     # rust brown: ingots, moulds, carts
CRUST = mat(C.game(0x0C3E))    # scorched crust: the channel's banks and bed
WOOD = mat(C.game(0x16DB))     # dark wood: the bellows' boards, desks
LAVA = mat(C.game(0x1547, "lava"))
SIGIL = mat(C.own_material("forge_sigil", C.own_image("forge_sigil", 32, 64, sigil_px)))
HAZARD = mat(C.own_material("hazard_stripes", C.own_image("hazard_stripes", 32, 16, hazard_px)))
MOUTH = mat(C.own_material("furnace_mouth", C.own_image("furnace_mouth", 16, 16, mouth_px)))
GAUGE = mat(C.own_material("pressure_gauge", C.own_image("pressure_gauge", 32, 32, gauge_px)))
LEATHER = mat(C.own_material("bellows_leather", C.own_image("bellows_leather", 32, 32, leather_px)))
DOORP = mat(C.own_material("iron_door", C.own_image("iron_door", 32, 64, door_px)))
EDGE = jfg64.boundary_material()


def mesh(name, uv=200.0):
    return Mesh(name, MATS, coll, uv_size=uv)


dock = mesh("dock")            # A, the way back's recess, the shortcut ramp
rooms = mesh("furnace_rooms")  # B1-B3 and their corridors
hall = mesh("hall")            # C's floor, walls and ceiling, the mould bed
chan = mesh("channel", 120.0)  # the channel's bed and banks, the bridges
lava = Mesh("lava", MATS, coll, uv_size=200.0)
gal = mesh("gallery")          # the gallery, the stair up to it
cat = mesh("catwalk", 128.0)   # the catwalk, perches, the bay, its rails
offs = mesh("offices")         # D1, D2, E0
bel = mesh("bellows_chamber")  # F, the exit passage, the side recess
props = mesh("props", 128.0)   # furnaces, bunkers, ingots, plinths, carts, the crane, the bellows
deco = mesh("decals", 64.0)    # pictures on the walls
edges = Mesh("colliders", [EDGE], coll)
spots = {}
LAMPS = []
FURN = (0.85, 0.4, 0.1)
WARM = (0.42, 0.26, 0.12)
DIM = (0.26, 0.16, 0.08)
RED = (0.75, 0.12, 0.06)
BLUE = (0.18, 0.32, 0.75)


def lamp(x, z, y, r, c):
    LAMPS.append((x, z, y, r, c))


def room(m, x0, z0, x1, z1, y, top, wmat, fmat, cmat, holes=None, which="nsew", skip=(), ceil=True):
    """A room: its floor (minus `skip` rects: blocks standing on it), its walls facing in, with openings
    holes[side] = [(u0, v0, u1, v1)] (u: x on n/s walls, z on e/w walls), and its ceiling."""
    holes = holes or {}
    for r in C.rects_minus((x0, z0, x1, z1), list(skip)):
        tiled(m, *r, y, fmat)
    if "n" in which:
        plane_rect(m, "z", z0, x0, y, x1, top, holes.get("n", []), wmat, (0, 1, 0))
    if "s" in which:
        plane_rect(m, "z", z1, x0, y, x1, top, holes.get("s", []), wmat, (0, -1, 0))
    if "w" in which:
        plane_rect(m, "x", x0, z0, y, z1, top, holes.get("w", []), wmat, (1, 0, 0))
    if "e" in which:
        plane_rect(m, "x", x1, z0, y, z1, top, holes.get("e", []), wmat, (-1, 0, 0))
    if ceil:
        ceiling(m, x0, z0, x1, z1, top, cmat, size=220.0)


def reveal(m, plane, c0, c1, u0, u1, y, h, mt, floor_mt):
    """A doorway's reveal through a wall between planes c0 and c1 (plane "x": x = c, u is z; "z": z = c, u is x):
    its floor at y, its two sides and its lintel's underside at y + h (2.3's)."""
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


def decal(m, plane, c, u0, v0, u1, v1, mat_, facing_sign):
    """A picture on a wall, once, 4 in front of it (2 out flickers: the kit): plane "x" (u is z) or "z" (u is x),
    facing +1 or -1 along the plane's axis, read the right way round from that side."""
    o = c + 4 * facing_sign
    if plane == "z":
        a, b = (u0, u1) if facing_sign > 0 else (u1, u0)
        pts = [(a, o, v0), (b, o, v0), (b, o, v1), (a, o, v1)]
        f = (0, facing_sign, 0)
    else:
        a, b = (u1, u0) if facing_sign > 0 else (u0, u1)
        pts = [(o, a, v0), (o, b, v0), (o, b, v1), (o, a, v1)]
        f = (facing_sign, 0, 0)
    m.face(pts, mat_, f, [(0, 0), (1, 0), (1, 1), (0, 1)])


def sq(x, z, h=50.0):
    return (x - h, z - h, x + h, z + h)


def cover_block(x, z, y, top_mat=RUST, side=IRON, h=110.0):
    """Squad cover: 100 x 100, 110 tall (a coal bunker, an ingot stack)."""
    C.block(props, x - 50, z - 50, x + 50, z + 50, y, y + h, side, top=top_mat, size=None)


def furnace(x0, z0, x1, z1, y, face, h=350.0):
    """A brick furnace against a wall: three sides (the wall's side left out), a top nobody reaches, and its
    glowing mouth on `face` (n, s, e, w), 30-130 over the floor."""
    which = {"e": "nse", "w": "nsw", "n": "new", "s": "sew"}[face]
    C.block(props, x0, z0, x1, z1, y, y + h, BRICK, top=BRICK, which=which, size=None)
    if face in "ew":
        c, sign = (x1, 1) if face == "e" else (x0, -1)
        decal(deco, "x", c, (z0 + z1) / 2 - 45, y + 30, (z0 + z1) / 2 + 45, y + 130, MOUTH, sign)
    else:
        c, sign = (z1, 1) if face == "s" else (z0, -1)
        decal(deco, "z", c, (x0 + x1) / 2 - 45, y + 30, (x0 + x1) / 2 + 45, y + 130, MOUTH, sign)


# ================================================================================================ A. the loading dock
AX0, AX1, AZ0, AZ1, ATOP = -2000.0, -1200.0, -1500.0, -900.0, 1050.0
BACK = (-1280.0, -1120.0)              # the way back's doorway in the west wall (z)
SHORT_Z = (-1480.0, -1280.0)           # the shortcut ramp's opening in the east wall (z)
C1X = (-1700.0, -1500.0)               # corridor 1's opening in the south wall (x)
CARTS = [(-1640.0, -1050.0), (-1440.0, -1110.0)]
cart_feet = [(x - 70, z - 40, x + 70, z + 40) for (x, z) in CARTS]
room(dock, AX0, AZ0, AX1, AZ1, Y0, ATOP, BRICK, FLOOR, CEIL,
     holes={"w": [(BACK[0], Y0, BACK[1], Y0 + DOOR_H + 5)], "e": [(SHORT_Z[0], Y0, SHORT_Z[1], Y0 + TUN)],
            "s": [(C1X[0], Y0, C1X[1], Y0 + TUN)]}, skip=cart_feet)
# the way back: a recess 140 deep, the foundry's inner door painted at its end
room(dock, AX0 - 140, BACK[0], AX0, BACK[1], Y0, Y0 + DOOR_H + 5, BRICK, FLOOR, CEIL, which="nsw")
decal(deco, "x", AX0 - 140, BACK[0] + 10, Y0, BACK[1] - 10, Y0 + 150, DOORP, 1)
decal(deco, "x", AX0, BACK[0] - 10, Y0 + DOOR_H + 15, BACK[1] + 10, Y0 + DOOR_H + 55, HAZARD, 1)
spots["start0"] = [-1880, Y0, -1200]
spots["way_back_exit"] = [AX0 - 95, Y0, -1200]
# ore carts: iron tubs on a rust base (decoration, out of every region)
for (x, z) in CARTS:
    C.block(props, x - 70, z - 40, x + 70, z + 40, Y0, Y0 + 30, RUST, top=RUST, size=None, which="nsew")
    props.box(x - 66, z - 36, x + 66, z + 36, Y0 + 30, Y0 + 105, IRON, top=RUST)
# the crane: a post in the north-east corner, its jib along x, a chain and a hanging ladle
post(props, -1290.0, -1410.0, 22, Y0, 1000.0, RAIL, n=6)
props.box(-1700, -1425, -1312, -1395, 900, 930, IRON, bottom=True)
post(props, -1650.0, -1410.0, 4, 640.0, 900.0, RAIL, n=4, cap=False)
props.box(-1690, -1450, -1610, -1370, 600, 640, RUST, bottom=True)
decal(deco, "z", AZ0, -1600, Y0 + 300, -1500, Y0 + 400, GAUGE, 1)
decal(deco, "x", AX1, -1120, Y0 + 200, -1040, Y0 + 360, SIGIL, -1)
spots["crates_dock"] = [[-1900, -980], [-1920, -1440], [-1330, -980]]
lamp(-1800, -1300, 700, 520, WARM)
lamp(-1400, -1050, 700, 520, WARM)
lamp(-2060, -1200, 470, 260, (0.7, 0.34, 0.1))   # the flats' furnace glow behind the way back

# the shortcut: a ramp up east from the dock (350 -> 600, 520 long: 26 degrees), then level to D2's door
SX0, SXR, SX1 = AX1, -680.0, -440.0


def sfloor(x, z):
    if x >= SXR:
        return YG
    return Y0 + (YG - Y0) * (x - SX0) / (SXR - SX0)


tiled(dock, SX0, SHORT_Z[0], SXR, SHORT_Z[1], Y0, PLATE, YG, along="x", size=130.0)
tiled(dock, SXR, SHORT_Z[0], SX1, SHORT_Z[1], YG, PLATE)
walls(dock, SX0, SHORT_Z[0], SX1, SHORT_Z[1], sfloor, lambda x, z: sfloor(x, z) + TUN, BRICK, "ns", inward=True)
ceiling(dock, SX0, SHORT_Z[0], SXR, SHORT_Z[1], Y0 + TUN, CEIL, YG + TUN, along="x")
ceiling(dock, SXR, SHORT_Z[0], SX1, SHORT_Z[1], YG + TUN, CEIL)
lamp(-800, -1380, 760, 320, DIM)

# ================================================================================================ B. the furnace rooms
B1 = (-1950.0, -660.0, -1350.0, -160.0)
B2 = (-1060.0, -660.0, -560.0, -160.0)
B3 = (-1060.0, 80.0, -560.0, 480.0)
BTOP = 1000.0
C2Z = (-460.0, -260.0)       # corridor 2 (B1 -> B2), along x
C3X = (-910.0, -710.0)       # corridor 3 (B2 -> B3), along z
C4Z = (-440.0, -240.0)       # corridor 4 (B2 -> the hall), along x
# corridor 1: the dock -> B1
room(rooms, C1X[0], AZ1, C1X[1], B1[1], Y0, Y0 + TUN, RBRICK, FLOOR, CEIL, which="ew")
lamp(-1600, -780, 600, 260, DIM)
# B1: two furnaces on the west wall; four coal bunkers (squad 1's cover, one a member)
F_B1 = [(-1950.0, -600.0, -1850.0, -440.0), (-1950.0, -380.0, -1850.0, -220.0)]
COVER_B1 = [(-1700.0, -530.0), (-1500.0, -490.0), (-1680.0, -300.0), (-1480.0, -290.0)]
room(rooms, *B1, Y0, BTOP, RBRICK, FLOOR, CEIL,
     holes={"n": [(C1X[0], Y0, C1X[1], Y0 + TUN)], "e": [(C2Z[0], Y0, C2Z[1], Y0 + TUN)]},
     skip=F_B1 + [sq(x, z) for x, z in COVER_B1])
for f in F_B1:
    furnace(*f, Y0, "e")
    lamp(f[2] + 20, (f[1] + f[3]) / 2, Y0 + 100, 430, FURN)
for (x, z) in COVER_B1:
    cover_block(x, z, Y0)
decal(deco, "z", B1[3], -1700, Y0 + 220, -1620, Y0 + 300, GAUGE, -1)
spots["furnaces_b1"] = [[f[2] + 30, Y0, (f[1] + f[3]) / 2] for f in F_B1]
spots["b1_region"] = [[-1820, -620], [-1820, -200], [-1390, -200], [-1390, -620]]
spots["b1_cover"] = COVER_B1
# corridor 2
room(rooms, B1[2], C2Z[0], B2[0], C2Z[1], Y0, Y0 + TUN, RBRICK, FLOOR, CEIL, which="ns")
lamp(-1200, -360, 600, 260, DIM)
spots["after_b1"] = [[-1230, -330], [-1170, -390]]
# B2: two furnaces on the north wall; four bunkers
F_B2 = [(-1000.0, -660.0, -840.0, -560.0), (-780.0, -660.0, -620.0, -560.0)]
COVER_B2 = [(-930.0, -440.0), (-690.0, -440.0), (-930.0, -280.0), (-690.0, -280.0)]
room(rooms, *B2, Y0, BTOP, RBRICK, FLOOR, CEIL,
     holes={"w": [(C2Z[0], Y0, C2Z[1], Y0 + TUN)], "e": [(C4Z[0], Y0, C4Z[1], Y0 + TUN)],
            "s": [(C3X[0], Y0, C3X[1], Y0 + TUN)]},
     skip=F_B2 + [sq(x, z) for x, z in COVER_B2])
for f in F_B2:
    furnace(*f, Y0, "s")
    lamp((f[0] + f[2]) / 2, f[3] + 20, Y0 + 100, 430, FURN)
for (x, z) in COVER_B2:
    cover_block(x, z, Y0)
spots["b2_region"] = [[-1020, -530], [-1020, -200], [-600, -200], [-600, -530]]
spots["b2_cover"] = COVER_B2
# corridor 3 and B3: the side room (a dying furnace, a Tribal, ammo)
room(rooms, C3X[0], B2[3], C3X[1], B3[1], Y0, Y0 + TUN, RBRICK, FLOOR, CEIL, which="ew")
F_B3 = (-900.0, 380.0, -720.0, 480.0)
room(rooms, *B3, Y0, 750.0, RBRICK, FLOOR, CEIL, holes={"n": [(C3X[0], Y0, C3X[1], Y0 + TUN)]}, skip=[F_B3])
furnace(*F_B3, Y0, "n", h=300.0)
lamp(-810, 360, Y0 + 90, 380, (0.55, 0.24, 0.07))
lamp(-810, 150, 650, 300, DIM)
decal(deco, "x", B3[0], 200, Y0 + 160, 360, Y0 + 400, SIGIL, 1)
spots["b3"] = {"tribal": [-990, 420], "ammo": [-630, 420], "health": [-630, 150]}
# corridor 4: B2 -> the hall's west door
HX0, HX1, HZ0, HZ1, HTOP = -300.0, 1100.0, -1000.0, 0.0, 1250.0
room(rooms, B2[2], C4Z[0], HX0, C4Z[1], Y0, Y0 + TUN, RBRICK, FLOOR, CEIL, which="ns")
lamp(-430, -340, 600, 240, DIM)

# ================================================================================================ C. the casting hall
CHX = (340.0, 460.0)                     # the channel
BED, MOLTEN = Y0 - 36, Y0 - 6            # its bed and the molten surface (30 deep, banks 36)
BRIDGES = [(-710.0, -570.0), (-340.0, -200.0)]
INGOTS = [(-40.0, -660.0), (170.0, -430.0), (-110.0, -150.0), (180.0, -110.0)]   # the west floor's cover
MB = (-300.0, -800.0, -80.0, -560.0)    # the mould bed against the west wall; the crawlspace inside it
MB_TOP, MB_IN = Y0 + 220, (-280.0, -780.0, -100.0, -580.0)
MB_DOOR = (-230.0, -150.0)              # its opening in the south face, 150 high
PLINTHS = [(590.0, -470.0), (590.0, -110.0)]  # the turrets' plinths on the east bank, 100 tall
COVER_C = [(760.0, -680.0), (850.0, -500.0), (760.0, -300.0), (850.0, -130.0)]   # the forgemasters'
STAIR = (960.0, 1100.0)                 # the stair up the east wall: ramp z -560..-40, landing z -820..-560
GZ = -820.0                             # the gallery's edge (z -1000..-820 at 600)
CATX = (300.0, 500.0)                   # the catwalk
PERCHES = [-780.0, -480.0, -180.0]      # the lookouts' perches (z centres) on the catwalk's west side, x 190..300
BAY = (500.0, -940.0, 640.0, -820.0)    # the railed bay on the catwalk's east side (Tribal 3), over the gallery

hall_skip = [(CHX[0], HZ0, CHX[1], HZ1), MB, (STAIR[0], GZ, STAIR[1], -40.0)]
hall_skip += [sq(x, z) for x, z in INGOTS + PLINTHS + COVER_C]
room(hall, HX0, HZ0, HX1, HZ1, Y0, HTOP, IRON, FLOOR, CEIL,
     holes={"n": [(-200.0, YG, -40.0, YG + DOOR_H), (740.0, YG, 900.0, YG + 200), (CATX[0], YC, CATX[1], YC + TUN)],
            "s": [(320.0, YC, 480.0, YC + DOOR_H)],
            "w": [(C4Z[0], Y0, C4Z[1], Y0 + TUN)]},
     skip=hall_skip)
# the channel's ends under the north and south walls (the walls go down to its bed there)
strip(hall, (CHX[0], HZ0), (CHX[1], HZ0), BED, BED, Y0, Y0, CRUST, (0, 1, 0))
strip(hall, (CHX[1], HZ1), (CHX[0], HZ1), BED, BED, Y0, Y0, CRUST, (0, -1, 0))
# the channel: its banks, bed and the molten surface (holes where the bridges stand on its bed)
bridge_holes = [(CHX[0], z0, CHX[1], z1) for (z0, z1) in BRIDGES]
zs = [HZ0] + [v for b in BRIDGES for v in b] + [HZ1]
for k in range(0, len(zs), 2):
    strip(chan, (CHX[0], zs[k + 1]), (CHX[0], zs[k]), BED, BED, Y0, Y0, CRUST, (1, 0, 0))
    strip(chan, (CHX[1], zs[k]), (CHX[1], zs[k + 1]), BED, BED, Y0, Y0, CRUST, (-1, 0, 0))
C.water_box(chan, (CHX[0], HZ0, CHX[1], HZ1), bridge_holes, BED, MOLTEN, CRUST, LAVA, piece=(120.0, 100.0), wm=lava)
# the iron bridges: blocks on the bed, flush with the banks, rails 90 high (no collider: a fall lands in 30 of
# molten metal with banks 36 high, out in a step)
for n, (z0, z1) in enumerate(BRIDGES):
    C.block(chan, CHX[0], z0, CHX[1], z1, BED, Y0, IRON, top=PLATE, which="ns", size=None)
    lip(chan, (CHX[0], z0), (CHX[1], z0), Y0, Y0, RAIL, h=90.0, thick=16.0)
    lip(chan, (CHX[1], z1), (CHX[0], z1), Y0, Y0, RAIL, h=90.0, thick=16.0)
    spots[f"bridge{n + 1}"] = [400, Y0, (z0 + z1) / 2]
for z in range(-950, 1, 150):
    lamp(400, z, Y0 + 30, 380, (0.75, 0.32, 0.07))
# where the metal pours in: a furnace mouth over the channel's north end
decal(deco, "z", HZ0, CHX[0] - 10, Y0 + 20, CHX[1] + 10, Y0 + 170, MOUTH, 1)
lamp(400, -980, Y0 + 120, 420, (0.95, 0.45, 0.1))
spots["lava_glows"] = [[400, Y0 + 60, -850], [400, Y0 + 60, -420], [400, Y0 + 60, -60]]

# the west floor: ingot stacks; the mould bed with the crawlspace (S) inside it
for (x, z) in INGOTS:
    cover_block(x, z, Y0, top_mat=RUST, side=RUST)
x0, z0, x1, z1 = MB
hall.face([(x1, z0, Y0), (x0, z0, Y0), (x0, z0, MB_TOP), (x1, z0, MB_TOP)], RUST, (0, -1, 0))   # north face
strip(hall, (x1, z1), (x1, z0), Y0, Y0, MB_TOP, MB_TOP, RUST, (1, 0, 0))                         # east face
plane_rect(hall, "z", z1, x0, Y0, x1, MB_TOP, [(MB_DOOR[0], Y0, MB_DOOR[1], Y0 + 150)], RUST, (0, 1, 0))
tiled(hall, x0, z0, x1, z1, MB_TOP, RUST)
i0, j0, i1, j1 = MB_IN
room(hall, i0, j0, i1, j1, Y0, Y0 + 150, RUST, FLOOR, CEIL,
     holes={"s": [(MB_DOOR[0], Y0, MB_DOOR[1], Y0 + 150)]})
reveal(hall, "z", j1, z1, MB_DOOR[0], MB_DOOR[1], Y0, 150.0, RUST, FLOOR)
lamp(-190, -680, Y0 + 120, 200, (0.45, 0.22, 0.06))
spots["crawlspace"] = {"health": [-230, -700], "ammo": [-150, -650]}
# the turrets' plinths
for (x, z) in PLINTHS:
    C.block(props, x - 50, z - 50, x + 50, z + 50, Y0, Y0 + 100, IRON, top=PLATE, size=None)
spots["turrets"] = [[x, Y0 + 100, z] for x, z in PLINTHS]
# the forgemasters' cover on the east floor: ingot stacks
for (x, z) in COVER_C:
    cover_block(x, z, Y0, top_mat=RUST, side=RUST)
spots["forgemasters_region"] = [[510, -780], [510, -20], [940, -20], [940, -780]]
spots["forgemasters_cover"] = COVER_C
spots["west_floor_region"] = [[-290, -800], [-290, -20], [470, -20], [470, -800]]
# the crane on the south wall: a jib out of the wall at 1,000, a chain and a ladle; its release under the jib
props.box(-120, -260, -80, -4, 1000, 1030, IRON, bottom=True)
post(props, -100.0, -240.0, 4, 780.0, 1000.0, RAIL, n=4, cap=False)
props.box(-145, -285, -55, -195, 700, 780, RUST, bottom=True)
decal(deco, "z", HZ1, -150, 920, -50, 1000, HAZARD, -1)
spots["crane_release"] = [-100, 960, -8]
lamp(-100, -40, 960, 260, RED)
# banners and gauges on the hall's walls
for z in (-800.0, -300.0):
    decal(deco, "x", HX1, z - 40, 700, z + 40, 960, SIGIL, -1)
decal(deco, "x", HX0, -900, Y0 + 400, -820, Y0 + 660, SIGIL, 1)
lamp(1090, -400, 760, 480, (0.5, 0.26, 0.08))
lamp(700, -400, 700, 420, DIM)
lamp(0, -450, 700, 420, DIM)

# ================================================================================================ D. the gallery
gx0, gx1 = HX0, HX1
tiled(gal, gx0, HZ0, gx1, GZ, YG, PLATE)
tiled(gal, gx0, HZ0, gx1, GZ, YG - 20, IRON, size=200.0, facing=(0, 0, -1))
strip(gal, (STAIR[0], GZ), (gx0, GZ), YG - 20, YG - 20, YG, YG, IRON, (0, 1, 0))   # its edge (the landing's side east)


def open_rail(m, a, b, y, h=100.0, every=160.0, first=True, last=True):
    """A balustrade the hero sees through (a solid 100 lip hid the hall and the crane's release from the gallery
    at eye height): a kerb 30 high, posts and a rail at `h`, no collider (a fall from the gallery is 250, onto the
    hall floor)."""
    lip(m, a, b, y, y, RAIL, h=30.0, thick=20.0, caps=(first, last))
    dx, dz = b[0] - a[0], b[1] - a[1]
    L = math.hypot(dx, dz)
    nx, nz = -dz / L * 10.0, dx / L * 10.0   # the kerb's middle (it lies to the left of a -> b)
    ts = C.cuts(0.0, 1.0, every / L)
    for t in ts[(0 if first else 1):(len(ts) if last else -1)]:
        # up into the rail, capless (a cap in the rail's top plane flickers)
        post(m, a[0] + dx * t + nx, a[1] + dz * t + nz, 6, y + 30, y + h - 4, RAIL, n=4, phase=math.pi / 4,
             cap=False)
    tr = 8.0 / L   # the rail (6 thick, centred on the posts) stops inside the end posts
    aa = (a[0] + dx * tr + nx * 0.7, a[1] + dz * tr + nz * 0.7)
    bb = (b[0] - dx * tr + nx * 0.7, b[1] - dz * tr + nz * 0.7)
    lip(m, aa, bb, y + h - 10, y + h - 10, RAIL, h=10.0, thick=6.0, under=True)


open_rail(gal, (STAIR[0], GZ), (gx0, GZ), YG, last=False)
# the stair up the east wall: the landing (600) and the ramp (600 -> 350 southwards, 520 long: 26 degrees)
tiled(gal, STAIR[0], GZ, STAIR[1], -560.0, YG, PLATE)
strip(gal, (STAIR[1], GZ), (STAIR[0], GZ), Y0, Y0, YG - 20, YG - 20, IRON, (0, -1, 0))     # under the gallery
strip(gal, (STAIR[0], GZ), (STAIR[0], -560.0), Y0, Y0, YG, YG, IRON, (-1, 0, 0))
C.block(gal, STAIR[0], -560.0, STAIR[1], -40.0, Y0, YG, IRON, top=PLATE, which="w", y1b=Y0, along="z")
lip(gal, (STAIR[0], -40.0), (STAIR[0], -560.0), Y0, YG, RAIL, h=100.0, thick=20.0)
open_rail(gal, (STAIR[0], -560.0), (STAIR[0], GZ), YG, first=False)
spots["gallery_patrol"] = [[-180, YG, -910], [880, YG, -910]]
spots["gallery_region"] = [[-290, -990], [-290, -830], [1090, -830], [1090, -990]]
spots["stair_foot"] = [1030, Y0, -20]
lamp(-120, -990, YG + 170, 300, WARM)
lamp(820, -990, YG + 200, 300, WARM)

# D2: the foreman's office (600), behind the switch door; its west door to the shortcut, its east to E0
D2 = (-400.0, -1640.0, 160.0, -1040.0)
DOOR_SW = (-200.0, -40.0)               # the switch door (x), through z -1040..-1000
DOOR_SC = (-1460.0, -1300.0)            # the shortcut's door (z), through x -440..-400
DOOR_E0 = (-1600.0, -1440.0)            # the open doorway to E0 (z), through x 160..190
DESK = (-20.0, -1580.0, 140.0, -1510.0)
room(offs, *D2, YG, 950.0, PANEL, PLATE, CEIL,
     holes={"s": [(DOOR_SW[0], YG, DOOR_SW[1], YG + DOOR_H)], "w": [(DOOR_SC[0], YG, DOOR_SC[1], YG + DOOR_H)],
            "e": [(DOOR_E0[0], YG, DOOR_E0[1], YG + 200)]}, skip=[DESK])
C.block(props, *DESK, YG, YG + 70, WOOD, top=WOOD, size=None)
reveal(offs, "z", D2[3], HZ0, DOOR_SW[0], DOOR_SW[1], YG, DOOR_H, PANEL, PLATE)
reveal(offs, "x", SX1, D2[0], DOOR_SC[0], DOOR_SC[1], YG, DOOR_H, PANEL, PLATE)
plane_rect(offs, "x", SX1, SHORT_Z[0], YG, SHORT_Z[1], YG + TUN, [(DOOR_SC[0], YG, DOOR_SC[1], YG + DOOR_H)], BRICK,
           (-1, 0, 0))   # the shortcut's end wall round the door
reveal(offs, "x", D2[2], 190.0, DOOR_E0[0], DOOR_E0[1], YG, 200.0, PANEL, PLATE)
decal(deco, "z", D2[1], -160, YG + 60, -80, YG + 300, SIGIL, 1)
decal(deco, "x", D2[0], -1200, YG + 120, -1140, YG + 180, GAUGE, 1)
decal(deco, "z", HZ0, DOOR_SW[0] - 10, YG + DOOR_H + 10, DOOR_SW[1] + 10, YG + DOOR_H + 50, HAZARD, 1)
lamp(-120, -1340, 880, 420, WARM)
spots["switch_door"] = [-120, YG, -1020]
spots["shortcut_door"] = [-420, YG, -1380]
spots["key"] = [-260, YG, -1560]
spots["tribal_d2"] = [60, YG, -1150]
spots["d2_health"] = [-300, YG, -1100]

# D1: the east office (600): health and ammo after the hall
D1 = (640.0, -1400.0, 1000.0, -1040.0)
DOOR_D1 = (740.0, 900.0)
room(offs, *D1, YG, 950.0, PANEL, PLATE, CEIL, holes={"s": [(DOOR_D1[0], YG, DOOR_D1[1], YG + 200)]})
reveal(offs, "z", D1[3], HZ0, DOOR_D1[0], DOOR_D1[1], YG, 200.0, PANEL, PLATE)
decal(deco, "z", D1[1], 780, YG + 140, 840, YG + 200, GAUGE, 1)
decal(deco, "z", D1[1], 880, YG + 140, 940, YG + 200, GAUGE, 1)
lamp(820, -1220, 880, 320, WARM)
spots["d1"] = {"health": [760, YG, -1320], "ammo": [900, YG, -1320]}

# E0: the stair room from D2 up to the catwalk (600 -> 850 northwards-south, 520 long: 26 degrees)
EX0, EZ0, EZ1, ESPLIT = 190.0, -1640.0, -1040.0, -1300.0
ERAMP = (-1640.0, -1120.0)


def eramp(z):
    return YG + (YC - YG) * max(0.0, min(1.0, (z - ERAMP[0]) / (ERAMP[1] - ERAMP[0])))


tiled(offs, EX0, EZ0, CATX[0], ESPLIT, YG, PLATE)                                  # the strip by the ramp
C.block(offs, CATX[0], ERAMP[0], CATX[1], ERAMP[1], YG, YG, PANEL, top=PLATE, which="", y1b=YC, along="z")
tiled(offs, CATX[0], ERAMP[1], CATX[1], EZ1, YC, PLATE)
strip(offs, (CATX[0], EZ0), (CATX[0], ESPLIT), YG, YG, YG, eramp(ESPLIT), PANEL, (-1, 0, 0))   # the ramp's side
plane_rect(offs, "z", EZ0, EX0, YG, CATX[1], 1200.0, [], PANEL, (0, 1, 0))
plane_rect(offs, "x", EX0, EZ0, YG, ESPLIT, 1200.0, [(DOOR_E0[0], YG, DOOR_E0[1], YG + 200)], PANEL, (1, 0, 0))
plane_rect(offs, "z", ESPLIT, EX0, YG, CATX[0], 1200.0, [], PANEL, (0, -1, 0))
strip(offs, (CATX[0], ESPLIT), (CATX[0], EZ1), eramp(ESPLIT), YC, 1200.0, 1200.0, PANEL, (1, 0, 0), step=110.0)
walls(offs, CATX[0], EZ0, CATX[1], EZ1, lambda x, z: eramp(z), 1200.0, PANEL, "e", inward=True, step=110.0)
plane_rect(offs, "z", EZ1, CATX[0], YC, CATX[1], 1200.0, [(CATX[0], YC, CATX[1], YC + TUN)], PANEL, (0, -1, 0))
ceiling(offs, EX0, EZ0, CATX[1], ESPLIT, 1200.0, CEIL)
ceiling(offs, CATX[0], ESPLIT, CATX[1], EZ1, 1200.0, CEIL)
lamp(250, -1500, 900, 380, DIM)
lamp(400, -1150, 1100, 360, DIM)
spots["e0_health"] = [245, YG, -1360]

# ================================================================================================ E. the catwalk
# through the hall's north wall from E0, across the hall over the channel, through the south wall to F
reveal(cat, "z", EZ1, HZ0, CATX[0], CATX[1], YC, TUN, IRON, GRATE)
CZ0, CZ1 = HZ0, HZ1
tiled(cat, CATX[0], CZ0, CATX[1], CZ1, YC, GRATE, size=100.0)
tiled(cat, CATX[0], CZ0, CATX[1], CZ1, YC - 20, IRON, size=200.0, facing=(0, 0, -1))
gaps_w = [(c - 32, c + 32) for c in PERCHES]
gaps_e = [(BAY[1], BAY[3])]


def runs(z0, z1, gaps):
    out, a = [], z0
    for g0, g1 in sorted(gaps):
        out.append((a, g0))
        a = g1
    out.append((a, z1))
    return out


for (a, b) in runs(CZ0, CZ1, gaps_w):
    strip(cat, (CATX[0], b), (CATX[0], a), YC - 20, YC - 20, YC, YC, RAIL, (-1, 0, 0))
for (a, b) in runs(CZ0, CZ1, gaps_e):
    strip(cat, (CATX[1], a), (CATX[1], b), YC - 20, YC - 20, YC, YC, RAIL, (1, 0, 0))
# the rails: posts, a rail at 150 and a collider to 400 over the walk (a fall is 500)
for (a, b) in runs(CZ0 + 8, CZ1 - 8, gaps_w):
    fence(cat, edges, (CATX[0] + 4, a), (CATX[0] + 4, b), YC, YC, RAIL, h=150.0, every=160.0, coll=400.0)
for (a, b) in runs(CZ0 + 8, CZ1 - 8, gaps_e):
    fence(cat, edges, (CATX[1] - 4, a), (CATX[1] - 4, b), YC, YC, RAIL, h=150.0, every=160.0, coll=400.0)
# the lookouts' perches: 110 out, 64 across, no rim (a 20 rim 47 from the lookout stopped its shots down to the
# hall's west door: raycast), hazard paint on the edge; the lookout stands 25 from the edge
for n, c in enumerate(PERCHES):
    px0, pz0, pz1 = CATX[0] - 110, c - 32, c + 32
    tiled(cat, px0, pz0, CATX[0], pz1, YC, GRATE, size=110.0)
    tiled(cat, px0, pz0, CATX[0], pz1, YC - 20, IRON, size=110.0, facing=(0, 0, -1))
    strip(cat, (px0, pz1), (px0, pz0), YC - 20, YC - 20, YC, YC, HAZARD, (-1, 0, 0))
    strip(cat, (px0, pz0), (CATX[0], pz0), YC - 20, YC - 20, YC, YC, RAIL, (0, -1, 0))
    strip(cat, (CATX[0], pz1), (px0, pz1), YC - 20, YC - 20, YC, YC, RAIL, (0, 1, 0))
    spots[f"perch{n + 5}"] = [px0 + 25, YC, c]
    spots[f"perch{n + 5}_flames"] = [CATX[0] + 30, YC, c + 62]
    lamp(CATX[0] - 40, c, YC + 110, 300, RED)
# the railed bay (Tribal 3), over the gallery
bx0, bz0, bx1, bz1 = BAY
tiled(cat, bx0, bz0, bx1, bz1, YC, GRATE, size=110.0)
tiled(cat, bx0, bz0, bx1, bz1, YC - 20, IRON, size=110.0, facing=(0, 0, -1))
strip(cat, (bx1, bz0), (bx0, bz0), YC - 20, YC - 20, YC, YC, RAIL, (0, -1, 0))
strip(cat, (bx0, bz1), (bx1, bz1), YC - 20, YC - 20, YC, YC, RAIL, (0, 1, 0))
strip(cat, (bx1, bz1), (bx1, bz0), YC - 20, YC - 20, YC, YC, RAIL, (1, 0, 0))
# (its rails 14 in: their end posts clear of the catwalk's, whose caps would share a plane with them)
fence(cat, edges, (bx0 + 14, bz0 + 14), (bx1 - 14, bz0 + 14), YC, YC, RAIL, coll=400.0)
fence(cat, edges, (bx1 - 14, bz0 + 14), (bx1 - 14, bz1 - 14), YC, YC, RAIL, coll=400.0, first=False)
fence(cat, edges, (bx1 - 14, bz1 - 14), (bx0 + 14, bz1 - 14), YC, YC, RAIL, coll=400.0, first=False)
spots["tribal_bay"] = [590, YC, -880]
lamp(570, -880, YC + 140, 260, WARM)
# the tango key door's reveal through the hall's south wall into F
reveal(cat, "z", HZ1, 40.0, 320.0, 480.0, YC, DOOR_H, IRON, GRATE)
decal(deco, "z", HZ1, 310, YC + DOOR_H + 10, 490, YC + DOOR_H + 50, HAZARD, -1)
spots["key_door"] = [400, YC, 20]

# ================================================================================================ F. the bellows chamber
FX0, FZ0, FX1, FZ1, FTOP = -50.0, 40.0, 850.0, 740.0, 1550.0
SIDE_Z = (520.0, 680.0)            # the side door (z) in the east wall, to the Coolant Vents
COVER_F = [(110.0, 190.0), (650.0, 190.0), (110.0, 610.0), (650.0, 610.0)]
BEL = (180.0, 330.0, 560.0, 470.0)   # the bellows' footprint
FURN_F = (770.0, 300.0, 850.0, 500.0)
NOZ = (560.0, 385.0, 770.0, 415.0)
room(bel, FX0, FZ0, FX1, FZ1, YC, FTOP, BRICK, PLATE, CEIL,
     holes={"n": [(320.0, YC, 480.0, YC + DOOR_H)], "s": [(320.0, YC, 480.0, YC + DOOR_H)],
            "e": [(SIDE_Z[0], YC, SIDE_Z[1], YC + DOOR_H)]},
     skip=[BEL, FURN_F, NOZ] + [sq(x, z) for x, z in COVER_F])
for (x, z) in COVER_F:
    cover_block(x, z, YC, top_mat=RUST, side=RUST)
# the bellows: a bottom board, a top board hinged at the nozzle (1,080 at the back, 930 at the front), pleated
# leather between, and the nozzle along the floor into the furnace
b0x, b0z, b1x, b1z = BEL
C.block(props, b0x, b0z, b1x, b1z, YC, YC + 30, WOOD, top=WOOD, size=None)
TB = YC + 30


def top_under(x):  # the top board's underside over x
    return 1060.0 + (910.0 - 1060.0) * (x - b0x) / (b1x - b0x)


# the top board: 20 thick, overhanging the leather by 10
props.face([(b0x - 10, b1z + 10, top_under(b0x - 10) + 20), (b1x, b1z + 10, top_under(b1x) + 20),
            (b1x, b0z - 10, top_under(b1x) + 20), (b0x - 10, b0z - 10, top_under(b0x - 10) + 20)], WOOD, (0, 0, 1))
props.face([(b0x - 10, b0z - 10, top_under(b0x - 10)), (b1x, b0z - 10, top_under(b1x)),
            (b1x, b1z + 10, top_under(b1x)), (b0x - 10, b1z + 10, top_under(b0x - 10))], WOOD, (0, 0, -1))
for (za, sgn) in ((b0z - 10, -1), (b1z + 10, 1)):
    props.face([(b0x - 10, za, top_under(b0x - 10)), (b1x, za, top_under(b1x)), (b1x, za, top_under(b1x) + 20),
                (b0x - 10, za, top_under(b0x - 10) + 20)], WOOD, (0, sgn, 0))
props.face([(b0x - 10, b1z + 10, top_under(b0x - 10)), (b0x - 10, b0z - 10, top_under(b0x - 10)),
            (b0x - 10, b0z - 10, top_under(b0x - 10) + 20), (b0x - 10, b1z + 10, top_under(b0x - 10) + 20)],
           WOOD, (-1, 0, 0))
props.face([(b1x, b0z - 10, top_under(b1x)), (b1x, b1z + 10, top_under(b1x)), (b1x, b1z + 10, top_under(b1x) + 20),
            (b1x, b0z - 10, top_under(b1x) + 20)], WOOD, (1, 0, 0))
# the leather sides: six folds, in and out by 14
xs = [b0x + (b1x - b0x) * k / 6 for k in range(7)]
for (zo, sgn) in ((b0z, -1), (b1z, 1)):
    for k in range(6):
        za = zo - sgn * (0 if k % 2 == 0 else 14)
        zb = zo - sgn * (14 if k % 2 == 0 else 0)
        props.face([(xs[k], za, TB), (xs[k + 1], zb, TB), (xs[k + 1], zb, top_under(xs[k + 1])),
                    (xs[k], za, top_under(xs[k]))], LEATHER, (0, sgn, 0))
props.face([(b0x, b1z, TB), (b0x, b0z, TB), (b0x, b0z, top_under(b0x)), (b0x, b1z, top_under(b0x))], LEATHER,
           (-1, 0, 0))
props.face([(b1x, b0z, TB), (b1x, b1z, TB), (b1x, b1z, top_under(b1x)), (b1x, b0z, top_under(b1x))], LEATHER,
           (1, 0, 0))
# the nozzle: an iron spout 40 high along the floor, into the furnace's mouth (no face against the furnace)
nx0, nz0, nx1, nz1 = NOZ
props.face([(nx0, nz1, YC + 40), (nx1, nz1, YC + 40), (nx1, nz0, YC + 40), (nx0, nz0, YC + 40)], IRON, (0, 0, 1))
props.face([(nx1, nz0, YC), (nx0, nz0, YC), (nx0, nz0, YC + 40), (nx1, nz0, YC + 40)], IRON, (0, -1, 0))
props.face([(nx0, nz1, YC), (nx1, nz1, YC), (nx1, nz1, YC + 40), (nx0, nz1, YC + 40)], IRON, (0, 1, 0))
furnace(*FURN_F, YC, "w", h=300.0)
lamp(760, 400, YC + 120, 640, (1.0, 0.5, 0.12))
lamp(200, 400, 1300, 640, (0.3, 0.16, 0.08))
decal(deco, "z", FZ0, 40, YC + 250, 120, YC + 510, SIGIL, 1)
decal(deco, "z", FZ0, 680, YC + 250, 760, YC + 510, SIGIL, 1)
decal(deco, "x", FX0, 360, YC + 160, 440, YC + 240, GAUGE, 1)
spots["f_region"] = [[0, 100], [0, 700], [740, 700], [740, 100]]
spots["f_cover"] = COVER_F
spots["tribal_bellows"] = [90, YC, 400]
spots["bellows_centre"] = [370, YC, 400]
# the exit door (south) and the passage up to the Crown: level 80, a ramp 850 -> 1,100 (520 long), a landing
reveal(bel, "z", FZ1, FZ1 + 40, 320.0, 480.0, YC, DOOR_H, BRICK, PLATE)
decal(deco, "z", FZ1, 310, YC + DOOR_H + 10, 490, YC + DOOR_H + 50, HAZARD, -1)
PZ0, PR0, PR1, PZ1 = FZ1 + 40, 860.0, 1380.0, 1520.0
YT = 1100.0


def pfloor(x, z):
    return YC + (YT - YC) * max(0.0, min(1.0, (z - PR0) / (PR1 - PR0)))


tiled(bel, CATX[0], PZ0, CATX[1], PR0, YC, PLATE)
tiled(bel, CATX[0], PR0, CATX[1], PR1, YC, PLATE, YT, along="z", size=130.0)
tiled(bel, CATX[0], PR1, CATX[1], PZ1, YT, PLATE)
walls(bel, CATX[0], PZ0, CATX[1], PZ1, pfloor, lambda x, z: pfloor(x, z) + TUN, BRICK, "ew", inward=True, step=130.0)
plane_rect(bel, "z", PZ0, CATX[0], YC, CATX[1], YC + TUN, [(320.0, YC, 480.0, YC + DOOR_H)], BRICK, (0, 1, 0))
plane_rect(bel, "z", PZ1, CATX[0], YT, CATX[1], YT + TUN, [], BRICK, (0, -1, 0))
ceiling(bel, CATX[0], PZ0, CATX[1], PR0, YC + TUN, CEIL)
ceiling(bel, CATX[0], PR0, CATX[1], PR1, YC + TUN, CEIL, YT + TUN, along="z")
ceiling(bel, CATX[0], PR1, CATX[1], PZ1, YT + TUN, CEIL)
decal(deco, "z", PZ1, 340, YT, 460, YT + 240, DOORP, -1)
lamp(400, 1100, 1100, 420, (0.4, 0.2, 0.08))
lamp(400, 1460, YT + 200, 320, (0.7, 0.3, 0.08))   # the Crown's glow from beyond
spots["exit_door"] = [400, YC, FZ1 + 20]
spots["exit_crown"] = [400, YT, PZ1 - 45]
spots["start1"] = [400, YT, PZ1 - 110]
spots["after_f"] = {"health": [340, YC, 820], "ammo": [460, YC, 820]}
# the side door east (open: a mine door that opens as the hero comes), a recess 200 deep, a cold blue light
reveal(bel, "x", FX1, FX1 + 40, SIDE_Z[0], SIDE_Z[1], YC, DOOR_H, BRICK, PLATE)
RX0, RX1 = FX1 + 40, FX1 + 240
room(bel, RX0, SIDE_Z[0], RX1, SIDE_Z[1], YC, YC + 200, IRON, PLATE, CEIL,
     holes={"w": [(SIDE_Z[0], YC, SIDE_Z[1], YC + DOOR_H)]})
decal(deco, "x", RX1, SIDE_Z[0] + 20, YC, SIDE_Z[1] - 20, YC + 190, DOORP, -1)
decal(deco, "x", FX1, SIDE_Z[0] - 10, YC + DOOR_H + 10, SIDE_Z[1] + 10, YC + DOOR_H + 50, HAZARD, -1)
lamp(FX1 - 30, 600, YC + 220, 340, BLUE)
lamp(RX1 - 60, 600, YC + 150, 260, BLUE)
spots["side_door"] = [FX1 + 20, YC, 600]
spots["exit_vents"] = [RX1 - 45, YC, 600]
spots["start2"] = [RX0 + 70, YC, 600]
spots["blue_light"] = [FX1 - 30, YC + 220, 600]

# ------------------------------------------------------------------------------------------------ boundary colliders
for (a, b) in (((-2300, -1800), (1300, -1800)), ((1300, -1800), (1300, 1650)), ((1300, 1650), (-2300, 1650)),
               ((-2300, 1650), (-2300, -1800))):
    collider(edges, a, b, 0, 1700)

for m in (dock, rooms, hall, chan, lava, gal, cat, offs, bel, props, deco, edges):
    m.build()

# ------------------------------------------------------------------------------------------------ light: furnaces
level = [o for o in coll.all_objects if o.type == "MESH"]


def extra(x, z, y, mname):
    if mname.startswith(("furnace_mouth",)):
        return (2.6, 2.2, 1.8)
    if mname.startswith(("hazard_stripes", "forge_sigil", "pressure_gauge", "iron_door")):
        return (1.5, 1.4, 1.3)
    return (1.0, 1.0, 1.0)


# the kit's ambient (0.12, 0.07, 0.06) leaves these dark textures black (3.1's lesson): lifted, the same hue; the
# furnaces and the channel do the rest
C.bake(level, (0.0, 0.0, -1.0), (0.0, 0.0, 0.0), (0.24, 0.14, 0.11), lamps=LAMPS, extra=extra, shadow=0.0,
       ao_strength=0.4)
# the molten metal glows of itself
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
print("BELLOWS", json.dumps(report, default=str))
print("PARTS", json.dumps({o.name: sum(len(p.vertices) - 2 for p in o.data.polygons) for o in level}))
