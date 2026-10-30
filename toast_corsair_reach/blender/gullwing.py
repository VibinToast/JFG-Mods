"""Gullwing Docks (Corsair Reach 1.2): builds the level from nothing and exports blender/out/gullwing.glb.

Run in Blender 5.2 with jfg64 0.6.0+, after JFG-Studio has built its catalog once (the game's textures):
    blender --background --factory-startup --addons jfg64 --python gullwing.py
Then in JFG-Studio: reimport_geometry (or import the .glb) into the level `gullwing`.

Game coordinates throughout (x east, z south, y up); DESIGN.md has the plan this follows. The harbour is split in
two by walls the hero can't climb: the west (headland, market, canal, warehouse's back lane) and the east (yard,
warehouse, ship, far pier, harbour gate), joined only by the gatehouse door. The far pier is reached only across
the ship's deck; colliders stand over its bulwarks and every wall top within a jump is 250 or more above the floor.
"""
import json
import math
import os
import random
import sys

import bpy

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import common as C  # noqa: E402
from common import Mesh, block, sides, tiled, post, collider  # noqa: E402
import jfg64  # noqa: E402

NAME = "gullwing"
scene, coll = C.new_scene(NAME)
spots = {}

# ------------------------------------------------------------------------------------------------ our own images
FONT = {
    "K": ["1.1", "11.", "1..", "11.", "1.1"], "E": ["111", "1..", "11.", "1..", "111"],
    "P": ["11.", "1.1", "11.", "1..", "1.."], "O": ["111", "1.1", "1.1", "1.1", "111"],
    "U": ["1.1", "1.1", "1.1", "1.1", "111"], "T": ["111", ".1.", ".1.", ".1.", ".1."],
}


def board(x, y, dark=False):
    """Weathered planks, 8 pixels to a plank."""
    plank = (y // 8) % 2
    base = ((0.3, 0.2, 0.13) if plank else (0.27, 0.18, 0.11)) if dark else \
        ((0.47, 0.34, 0.21) if plank else (0.42, 0.3, 0.18))
    grain = ((x * 3 + y * 5) % 7) * 0.012
    return tuple(c + grain for c in base)


def text_at(x, y, word, x0, y0, scale=2):
    """Is pixel (x, y) on a letter of `word` drawn from (x0, y0) in our 3 x 5 letters, `scale` pixels each?"""
    cx = (x - x0) // scale
    cy = (y - y0) // scale
    if x < x0 or y < y0 or cy >= 5:
        return False
    k, col = cx // 4, cx % 4
    if k >= len(word) or col == 3:
        return False
    return FONT[word[k]][cy][col] == "1"


def keepout_px(x, y):
    """The smugglers' door sign: KEEP OUT in red on dark boards, a pale frame."""
    if x in (0, 31) or y in (0, 31):
        return (0.75, 0.7, 0.6)
    if text_at(x, y, "KEEP", 2, 4) or text_at(x, y, "OUT", 6, 18):
        return (0.82, 0.16, 0.1)
    return board(x, y, dark=True)


def fish_px(x, y):
    """A fishmonger's sign: a blue-grey fish on planks, a white border."""
    if x in (0, 1, 30, 31) or y in (0, 1, 30, 31):
        return (0.88, 0.85, 0.78)
    dx, dy = (x - 14) / 9.0, (y - 16) / 5.0
    body = dx * dx + dy * dy <= 1.0
    tail = 22 <= x <= 28 and abs(y - 16) <= (x - 21) * 0.9
    if (x - 9) ** 2 + (y - 15) ** 2 <= 1.5:
        return (0.05, 0.05, 0.08)
    if body:
        k = 0.9 + 0.12 * ((x + y) % 3 == 0)
        return (0.38 * k, 0.55 * k, 0.66 * k) if y < 17 else (0.75, 0.8, 0.82)
    if tail:
        return (0.32, 0.48, 0.58)
    return board(x, y)


def canvas_px(x, y):
    """Striped awning canvas, red and cream."""
    stripe = (x // 4) % 2
    k = 0.92 + 0.08 * math.sin(y * 0.8)
    return tuple(c * k for c in ((0.78, 0.16, 0.12) if stripe else (0.9, 0.84, 0.7)))


def sail_px(x, y):
    """The patched sail: cream canvas in panels, darker patches, the corsairs' skull over crossed oars."""
    k = 0.94 + 0.06 * ((x * 5 + y * 3) % 5) / 4
    col = (0.84 * k, 0.78 * k, 0.64 * k)
    if x % 8 == 0:
        col = (0.66, 0.6, 0.48)  # seams
    for (px0, py0, px1, py1, tint) in ((3, 6, 11, 15, (0.7, 0.62, 0.46)), (20, 44, 29, 55, (0.76, 0.66, 0.5)),
                                       (22, 4, 27, 10, (0.62, 0.56, 0.44))):
        if px0 <= x <= px1 and py0 <= y <= py1:
            col = tint
            if x in (px0, px1) or y in (py0, py1):
                col = (0.45, 0.38, 0.3)  # stitching
    cx, cy = 15.5, 27.0
    dx, dy = x - cx, y - cy
    skull = dx * dx / 30 + dy * dy / 24 <= 1.0 or (abs(dx) <= 3 and 30 <= y <= 33)
    eye = ((x - 13.5) ** 2 + (y - 26) ** 2 <= 2.0) or ((x - 17.5) ** 2 + (y - 26) ** 2 <= 2.0)
    oar = any(abs((y - 37) - k2 * (x - 15.5)) <= 1.0 and 5 <= x <= 26 for k2 in (0.6, -0.6))
    if (skull and not eye) or oar:
        return (0.42, 0.1, 0.07)
    if y >= 62 and (x * 7) % 5 == 0:
        return (0.5, 0.45, 0.36)  # frayed hem
    return col


def rope_px(x, y):
    """A coil of rope on deck planks."""
    d = math.hypot(x - 15.5, y - 15.5)
    if d > 14.5:
        return board(x, y)
    a = math.atan2(y - 15.5, x - 15.5)
    ring = (d + a / math.tau * 2.4) % 2.4
    twist = 0.85 + 0.15 * math.sin(a * 9 + d)
    if d < 3:
        return (0.2, 0.15, 0.1)
    return tuple(c * twist for c in ((0.74, 0.62, 0.4) if ring < 1.5 else (0.5, 0.4, 0.24)))


def flag_px(x, y):
    """The corsairs' flag: a skull over crossed oars, bone white on black."""
    dx, dy = x - 15.5, y - 12.0
    skull = (dx * dx) / 36 + (dy * dy) / 30 <= 1.0 or (abs(dx) <= 4 and 14 <= y <= 18)
    eye = ((x - 13) ** 2 + (y - 11) ** 2 <= 2.2) or ((x - 18) ** 2 + (y - 11) ** 2 <= 2.2)
    oar = any(abs((y - 25) - k * (x - 15.5)) <= 1.1 and 4 <= x <= 27 for k in (0.55, -0.55))
    blade = any(abs(x - bx) <= 2 and abs(y - by) <= 1.6 for bx, by in ((4, 19), (27, 19), (4, 31), (27, 31)))
    if (skull and not eye) or oar or blade:
        return (0.92, 0.88, 0.78)
    return (0.05, 0.05, 0.06) if (x * 7 + y * 13) % 11 else (0.12, 0.1, 0.1)


def shutter_px(x, y):
    """A shuttered window: two blue-green louvred shutters in a dark frame."""
    if x in (0, 15) or y in (0, 1, 30, 31) or x in (7, 8):
        return (0.16, 0.11, 0.08)
    slat = 0.8 + 0.2 * ((y % 3) == 0)
    return (0.22 * slat, 0.44 * slat, 0.42 * slat)


# ------------------------------------------------------------------------------------------------ materials
MATS, M = [], {}


def mat(name, material):
    M[name] = len(MATS)
    MATS.append(material)
    return M[name]


PAVE = mat("pave", C.game(0x1946))      # stone pavers: quays, market, ramps
MASON = mat("mason", C.game(0x0828))    # grey ashlar: harbour walls, bridge, towers
MOSS = mat("moss", C.game(0x1958))      # wet mossy stone: quay faces at the water
BRICK = mat("brick", C.game(0x04F3))    # warehouse, barracks, gatehouse
PLASTER = mat("plaster", C.game(0x008B))  # houses, sheds
ROOF = mat("roof", C.game(0x1933))      # terracotta roofs
PLANK = mat("plank", C.game(0x193D))    # piers, gangplank, loft
DARK = mat("dark", C.game(0x16DB))      # wet pilings, the hull, frames
DECK = mat("deck", C.game(0x16D9))      # deck planks, warehouse floor
CLIFF = mat("cliff", C.game(0x0C40))    # headland and the north cliff
CRATE = mat("crate", C.game(0x0A39))    # cargo
MUD = mat("mud", C.game(0x1959))        # the harbour floor under the water
WATER = mat("water", C.game(0x0DED, "water"))
LEDGE = mat("ledge", jfg64.game_texture_material(0x193D, "ledge", name="ledge_193D"))
SAIL = mat("sail", C.own_material("gull_sail", C.own_image("gull_sail", 32, 64, sail_px)))
FISH = mat("fish", C.own_material("fish_sign", C.own_image("fish_sign", 32, 32, fish_px)))
KEEPOUT = mat("keepout", C.own_material("keepout_sign", C.own_image("keepout_sign", 32, 32, keepout_px)))
CANVAS = mat("canvas", C.own_material("awning", C.own_image("awning", 16, 16, canvas_px)))
ROPE = mat("rope", C.own_material("rope_coil", C.own_image("rope_coil", 32, 32, rope_px)))
FLAG = mat("flag", C.own_material("corsair_flag", C.own_image("corsair_flag", 32, 32, flag_px)))
SHUTTER = mat("shutter", C.own_material("shutter", C.own_image("shutter", 16, 32, shutter_px)))
EDGE = jfg64.boundary_material()


def mesh(name, uv=200.0):
    return Mesh(name, MATS, coll, uv_size=uv)


edges = Mesh("colliders", [EDGE], coll)
wtr = Mesh("harbour_water", MATS, coll, uv_size=1024.0)  # its texture doesn't repeat: few repeats, few cuts


def slab(m, pts, mat_, thick=10.0):
    """A thin sloping roof (an awning) seen from above and below: its top, its underside `thick` under it (closer
    reads as a folded floor), and its front edge."""
    m.face(pts, mat_, (0, 0, 1))
    m.face([(x, z, y - thick) for (x, z, y) in pts[::-1]], mat_, (0, 0, -1))
    a, b = pts[2], pts[3]
    m.face([(a[0], a[1], a[2] - thick), (b[0], b[1], b[2] - thick), (b[0], b[1], b[2]), (a[0], a[1], a[2])], mat_, None)


def box(m, x0, z0, x1, z1, y0, y1, side, top=None, which="nsew", inset=0.0):
    """A plain block nobody walks on much (one face on top)."""
    return block(m, x0, z0, x1, z1, y0, y1, side, top, which, size=None, inset=inset)


def floors(m, rect, holes, y, top, size=130.0):
    """Floor over rect minus holes (blocks standing on it): no hidden ground under them."""
    for r in C.rects_minus(rect, holes):
        tiled(m, r[0], r[1], r[2], r[3], y, top, size=size)


def lip(m, a, b, ya, yb, h=100, thick=25, coll_to=None, mat_=MASON, base=None):
    """A parapet along a -> b ((x, z)) on floor ya..yb, `thick` to the left of a -> b, `h` tall; with coll_to, a
    collider from its top up to that height over it (so nobody hops over)."""
    dx, dz = b[0] - a[0], b[1] - a[1]
    L = math.hypot(dx, dz)
    nx, nz = -dz / L * thick, dx / L * thick
    pts = [(a[0], a[1]), (b[0], b[1]), (b[0] + nx, b[1] + nz), (a[0] + nx, a[1] + nz)]
    tops = [ya + h, yb + h, yb + h, ya + h]
    foot = [ya, yb, yb, ya] if base is None else [base] * 4
    m.face([(p[0], p[1], t) for p, t in zip(pts, tops)], mat_, (0, 0, 1))
    cx, cz = sum(p[0] for p in pts) / 4, sum(p[1] for p in pts) / 4
    for i in range(4):
        p, q = pts[i], pts[(i + 1) % 4]
        m.face([(p[0], p[1], foot[i]), (q[0], q[1], foot[(i + 1) % 4]), (q[0], q[1], tops[(i + 1) % 4]),
                (p[0], p[1], tops[i])], mat_, ((p[0] + q[0]) / 2 - cx, (p[1] + q[1]) / 2 - cz, 0))
    if coll_to:
        mx, mz = nx / 2, nz / 2  # down the parapet's middle
        collider(edges, (a[0] + mx, a[1] + mz), (b[0] + mx, b[1] + mz), min(tops), coll_to)


def facade(m, a, b, out, eave=380.0, rise=100.0, depth=140.0, y0=0.0, wall=PLASTER, windows=0, win_y=230.0,
           roof=True):
    """A house front from a to b ((x, z)) facing `out` ((x, z)): its wall to the eave, a tiled roof sloping back
    `depth` and up `rise`, and shuttered windows."""
    m.face([(a[0], a[1], y0), (b[0], b[1], y0), (b[0], b[1], eave), (a[0], a[1], eave)], wall, (out[0], out[1], 0))
    back = (-out[0] * depth, -out[1] * depth)
    if roof:
        m.face([(a[0], a[1], eave), (b[0], b[1], eave), (b[0] + back[0], b[1] + back[1], eave + rise),
                (a[0] + back[0], a[1] + back[1], eave + rise)], ROOF, (out[0], out[1], 1.5))
    L = math.hypot(b[0] - a[0], b[1] - a[1])
    ux, uz = (b[0] - a[0]) / L, (b[1] - a[1]) / L
    for k in range(windows):
        t = (k + 0.5) / windows * L
        cx, cz = a[0] + ux * t + out[0] * 2.5, a[1] + uz * t + out[1] * 2.5
        p0 = (cx - ux * 22, cz - uz * 22)
        p1 = (cx + ux * 22, cz + uz * 22)
        m.face([(p0[0], p0[1], win_y), (p1[0], p1[1], win_y), (p1[0], p1[1], win_y + 80), (p0[0], p0[1], win_y + 80)],
               SHUTTER, (out[0], out[1], 0), [(0, 0), (1, 0), (1, 1), (0, 1)])


def gable(m, x0, z0, x1, z1, eave, ridge, wall, along="x", which_ends=("a", "b"), slopes=("a", "b")):
    """A gable roof over x0..x1, z0..z1: the ridge along `along` at `ridge`, eaves at `eave`; the end walls'
    triangles (wall) and the two slopes (ROOF)."""
    if along == "x":
        zm = (z0 + z1) / 2
        if "a" in slopes:
            m.face([(x0, z0, eave), (x1, z0, eave), (x1, zm, ridge), (x0, zm, ridge)], ROOF, (0, -1, 1))
        if "b" in slopes:
            m.face([(x1, z1, eave), (x0, z1, eave), (x0, zm, ridge), (x1, zm, ridge)], ROOF, (0, 1, 1))
        if "a" in which_ends:
            m.face([(x0, z0, eave), (x0, z1, eave), (x0, zm, ridge)], wall, (-1, 0, 0))
        if "b" in which_ends:
            m.face([(x1, z1, eave), (x1, z0, eave), (x1, zm, ridge)], wall, (1, 0, 0))
    else:
        xm = (x0 + x1) / 2
        if "a" in slopes:
            m.face([(x0, z1, eave), (x0, z0, eave), (xm, z0, ridge), (xm, z1, ridge)], ROOF, (-1, 0, 1))
        if "b" in slopes:
            m.face([(x1, z0, eave), (x1, z1, eave), (xm, z1, ridge), (xm, z0, ridge)], ROOF, (1, 0, 1))
        if "a" in which_ends:
            m.face([(x1, z0, eave), (x0, z0, eave), (xm, z0, ridge)], wall, (0, -1, 0))
        if "b" in which_ends:
            m.face([(x0, z1, eave), (x1, z1, eave), (xm, z1, ridge)], wall, (0, 1, 0))


def decal(m, pts, mat_):
    C.decal(m, pts, mat_)


# ================================================================================================ A. the headland
hl = mesh("headland")
# L0, the start landing at 420: open to the sea on the west, south and east (parapets with colliders over them)
block(hl, -2210, 1250, -1690, 1460, -10, 420, CLIFF, PAVE, which="swe")
sides(hl, -1950, 1250, -1690, 1460, 190, 420, CLIFF, "n")  # its face over L2
block(hl, -2100, 1460, -1980, 1500, -10, 420, CLIFF, PAVE, which="we")  # the step out under the arch
# leg 1 down the west side (420 -> 300), L1 (300), leg 2 back south (300 -> 190), L2 (190), leg 3 north (190 -> 20)
block(hl, -2210, 650, -1950, 1250, 180, 300, CLIFF, PAVE, which="e", y1b=420, along="z")
block(hl, -2210, 450, -1690, 650, 40, 300, CLIFF, PAVE, which="e")
block(hl, -1950, 650, -1690, 1000, 100, 300, CLIFF, PAVE, which="e", y1b=190, along="z")
block(hl, -1950, 1000, -1450, 1250, -40, 190, CLIFF, PAVE, which="e")
sides(hl, -1690, 1000, -1450, 1250, -10, 190, CLIFF, "s")
hy3 = block(hl, -1690, 300, -1450, 1000, 0, 20, CLIFF, PAVE, which="", y1b=190, along="z")
sides(hl, -1690, 300, -1450, 700, 15, hy3, CLIFF, "e")
sides(hl, -1690, 700, -1450, 1000, -40, hy3, CLIFF, "e")
block(hl, -1690, -50, -1450, 300, 0, 20, CLIFF, PAVE, which="")  # the foot of the stair
# rock round it: the west wall of leg 1 and the headland's north mass
box(hl, -2250, 450, -2210, 1250, 250, 650, CLIFF, which="e")
sides(hl, -2250, -50, -1970, 450, 295, 650, CLIFF, "s")
sides(hl, -1970, -50, -1690, 450, 295, 650, CLIFF, "s")
sides(hl, -2250, -50, -1690, 450, 15, 650, CLIFF, "e")
hl.face([(-2250, -50, 650), (-1690, -50, 650), (-1690, 450, 650), (-2250, 450, 650)], CLIFF, (0, 0, 1))
# the level's west edge seen from the start: the headland's face down to the sea
hl.face([(-2250, -1300, -10), (-2250, 450, -10), (-2250, 450, 650), (-2250, -1300, 650)], CLIFF, (-1, 0, 0))
hl.face([(-2250, 450, -10), (-2250, 1250, -10), (-2250, 1250, 650), (-2250, 450, 650)], CLIFF, (-1, 0, 0))
# parapets: L0 (with the arch back to the beach in its south side), L2 and leg 3 over the harbour, L1 over leg 3
lip(hl, (-2210, 1250), (-2210, 1460), 420, 420, h=45, thick=-25, coll_to=900)
lip(hl, (-2183, 1460), (-2130, 1460), 420, 420, h=45, thick=-25, coll_to=900)  # 2 apart: abutting ends flicker
lip(hl, (-1950, 1460), (-1717, 1460), 420, 420, h=45, thick=-25, coll_to=900)
lip(hl, (-1690, 1460), (-1690, 1250), 420, 420, h=45, thick=-25, coll_to=900)
lip(hl, (-1950, 1250), (-1717, 1250), 420, 420, h=45, thick=20)
lip(hl, (-1450, 1250), (-1450, 1002), 190, 190, h=60, thick=-25, coll_to=700)
lip(hl, (-1690, 1250), (-1477, 1250), 190, 190, h=60, thick=-25, coll_to=700)
lip(hl, (-1450, 998), (-1450, 700), 190, 20 + 170 * 400 / 700, h=60, thick=-25, coll_to=700)
lip(hl, (-1690, 650), (-1690, 452), 300, 300, h=50, thick=-25)
# the arch back towards the beach: two pillars and a lintel
for (xa, xb) in ((-2128, -2100), (-1980, -1952)):
    sides(hl, xa, 1440, xb, 1480, 420, 600, MASON)  # no tops: the lintel sits on them
box(hl, -2128, 1440, -1952, 1480, 600, 652, MASON, which="nsew")
hl.face([(-2100, 1480, 600), (-1980, 1480, 600), (-1980, 1440, 600), (-2100, 1440, 600)], MASON, (0, 0, -1))
spots["start"] = (-2040, 420, 1330)
spots["exit_back"] = (-2040, 420, 1482)
hl.build()

# ================================================================================================ B. the market and the west
w = mesh("west")
block(w, -1450, -50, -475, 700, -40, 20, MOSS, PAVE, which="")
sides(w, -1450, 600, -475, 700, -40, 20, MOSS, "s")
sides(w, -575, -50, -475, 75, -40, 20, MOSS, "e")
sides(w, -575, 325, -475, 700, -40, 20, MOSS, "e")
block(w, -900, -550, -475, -50, -40, 20, MOSS, PAVE, which="")  # the canal street
sides(w, -900, -550, -475, -50, -40, 20, MOSS, "e")
block(w, -900, -1000, -700, -550, 0, 20, MASON, PAVE, which="")  # the lane to the warehouse's back door
block(w, -1450, -450, -1250, -50, 0, 20, MASON, PAVE, which="")  # the back alley
# steps out of the water, every 300 or so along the quays
STEPS_W = [(-1400, 700, -1320, 770), (-900, 700, -820, 770), (-475, 470, -405, 550), (-475, -320, -405, -240),
           (-620, 700, -540, 770)]
for (a0, b0, a1, b1) in STEPS_W:
    box(w, a0, b0, a1, b1, -40, -5, MOSS, which="nse" if a0 == -475 else "sew")  # not the face against the quay
# the houses round the market: plaster fronts, tiled roofs, shutters
facade(w, (-1690, -50), (-1450, -50), (0, 1), windows=2)
facade(w, (-1450, -50), (-1450, -450), (1, 0), windows=2)
facade(w, (-1250, -450), (-1250, -50), (-1, 0), windows=2)
facade(w, (-1250, -50), (-900, -50), (0, 1), windows=3)
facade(w, (-900, -50), (-900, -1000), (1, 0), windows=5)
facade(w, (-900, -1000), (-700, -1000), (0, 1), windows=1)
for (a0, b0, a1, b1) in ((-2250, -1300, -1690, -50), (-1690, -1300, -1590, -190), (-1590, -1300, -1450, -450), (-1450, -1300, -1250, -590),
                         (-1250, -1300, -1110, -450), (-1110, -1300, -1040, -190), (-1040, -1300, -900, -1000),
                         (-900, -1300, -700, -1140)):
    w.face([(a0, b1, 480), (a1, b1, 480), (a1, b0, 480), (a0, b0, 480)], ROOF, (0, 0, 1))  # the houses' flat tops
w.face([(-2250, -50, 480), (-1690, -50, 480), (-1690, -50, 650), (-2250, -50, 650)], CLIFF, (0, -1, 0))
# the smugglers' door at the alley's end: a doorway 160 x 160 in the house front, a short dark passage behind it
ZD = -450
w.face([(-1450, ZD, 0), (-1430, ZD, 0), (-1430, ZD, 380), (-1450, ZD, 380)], PLASTER, (0, 1, 0))
w.face([(-1270, ZD, 0), (-1250, ZD, 0), (-1250, ZD, 380), (-1270, ZD, 380)], PLASTER, (0, 1, 0))
w.face([(-1430, ZD, 180), (-1270, ZD, 180), (-1270, ZD, 380), (-1430, ZD, 380)], PLASTER, (0, 1, 0))
w.face([(-1450, ZD, 380), (-1250, ZD, 380), (-1250, ZD - 140, 480), (-1450, ZD - 140, 480)], ROOF, (0, 1, 1.5))
tiled(w, -1430, ZD - 90, -1270, ZD, 20, DECK)
w.face([(-1430, ZD - 90, 0), (-1270, ZD - 90, 0), (-1270, ZD - 90, 180), (-1430, ZD - 90, 180)], DARK, (0, 1, 0))
w.face([(-1430, ZD - 90, 0), (-1430, ZD, 0), (-1430, ZD, 180), (-1430, ZD - 90, 180)], PLASTER, (1, 0, 0))
w.face([(-1270, ZD, 0), (-1270, ZD - 90, 0), (-1270, ZD - 90, 180), (-1270, ZD, 180)], PLASTER, (-1, 0, 0))
w.face([(-1430, ZD - 90, 180), (-1270, ZD - 90, 180), (-1270, ZD, 180), (-1430, ZD, 180)], DARK, (0, 0, -1))
decal(w, [(-1390, ZD + 4, 200), (-1310, ZD + 4, 200), (-1310, ZD + 4, 270), (-1390, ZD + 4, 270)], KEEPOUT)
spots["smugglers_door"] = (-1350, 20, ZD - 6)
spots["smugglers_exit"] = (-1350, 20, ZD - 60)
spots["smugglers_lamp"] = (-1350, 300, ZD + 30)
w.build()

# ------------------------------------------------------------------------------------------------ the market stalls
mk = mesh("market", uv=128.0)
# the machine gun stall at the way in from the stair: back board, side boards, an awning; the chest inside
box(mk, -1335, 80, -1315, 240, 0, 230, PLANK, which="nsew")
for (za, zb) in ((80, 92), (228, 240)):
    box(mk, -1440, za, -1335, zb, 0, 110, PLANK, which="nsw")
slab(mk, [(-1320, 70, 238), (-1320, 250, 238), (-1460, 250, 222), (-1460, 70, 222)], CANVAS)
decal(mk, [(-1311, 110, 120), (-1311, 210, 120), (-1311, 210, 200), (-1311, 110, 200)], FISH)
spots["chest"] = (-1365, 20, 160)
# counters along the houses, under an awning (outside the squads' region)
for (xa, xb) in ((-1225, -1095), (-1060, -930)):
    box(mk, xa, -45, xb, 15, 0, 100, CRATE, PLANK, which="sew")
slab(mk, [(-1240, -48, 250), (-915, -48, 250), (-915, 80, 200), (-1240, 80, 200)], CANVAS)
decal(mk, [(-1170, 19, 30), (-1130, 19, 30), (-1130, 19, 80), (-1170, 19, 80)], FISH)
# cover in the market square: five fish counters, solid blocks 105 tall
COVER_B = [(-1150, 200), (-1110, 470), (-920, 320), (-740, 160), (-720, 460)]
for n, (cx, cz) in enumerate(COVER_B):
    box(mk, cx - 45, cz - 70, cx + 45, cz + 70, 0, 105, CRATE, PLANK, which="nsew")
    if n % 2 == 0:
        decal(mk, [(cx - 49, cz + 40, 30), (cx - 49, cz - 40, 30), (cx - 49, cz - 40, 95), (cx - 49, cz + 40, 95)],
              FISH)
spots["cover_market"] = COVER_B
# the crane on the canal bank, its jib over the water
box(mk, -538, 642, -502, 678, 15, 380, DARK, which="nsew")
box(mk, -502, 650, -280, 670, 352, 374, DARK, which="nse")
mk.face([(-502, 670, 352), (-280, 670, 352), (-280, 650, 352), (-502, 650, 352)], DARK, (0, 0, -1))
box(mk, -306, 656, -298, 664, 230, 350, DARK, which="nsew")
box(mk, -322, 640, -282, 680, 200, 232, CRATE, which="nsew")
mk.face([(-322, 680, 200), (-282, 680, 200), (-282, 640, 200), (-322, 640, 200)], CRATE, (0, 0, -1))
mk.build()

# ------------------------------------------------------------------------------------------------ the market pier
pr = mesh("pier", uv=128.0)
block(pr, -1180, 700, -1020, 900, -40, 20, MASON, PLANK, which="ews", y1b=110, along="z")
tiled(pr, -1180, 900, -1020, 1060, 110, PLANK)
tiled(pr, -1180, 900, -1020, 1060, 100, DARK, size=200, facing=(0, 0, -1))
sides(pr, -1180, 900, -1020, 1060, 100, 110, DARK, "ews", inset=0)
for px in (-1172, -1028):
    for pz in (955, 1055):
        post(pr, px, pz, 14, -40, 100, DARK, n=6, cap=False)
# the smugglers' cache under the pier's end: a dry stone landing over the water
box(pr, -1160, 965, -1040, 1045, -40, 0, MOSS, which="nsew")
box(pr, -1150, 1005, -1112, 1043, 0, 38, CRATE, which="nsew")
pr.face([(-1100, 1040, 112.5), (-1060, 1040, 112.5), (-1060, 1000, 112.5), (-1100, 1000, 112.5)], ROPE, (0, 0, 1),
        [(0, 0), (1, 0), (1, 1), (0, 1)])
post(pr, -1030, 1052, 6, 110, 235, DARK, n=4)
box(pr, -1040, 1042, -1020, 1062, 235, 260, CRATE)
spots["cache"] = (-1100, 0, 985)
spots["pier_lamp"] = (-1030, 250, 1052)
pr.build()

# ------------------------------------------------------------------------------------------------ C. the canal, its bridge, the winch
cn = mesh("canal")
block(cn, -475, 75, -175, 325, -40, 20, MASON, PAVE, which="ns")
for (za, zb) in ((78, 102), (298, 322)):
    box(cn, -470, za, -180, zb, 15, 78, MASON)
post(cn, -300, 450, 40, -40, 215, MASON, n=6)
box(cn, -345, 405, -255, 495, 215, 230, DARK)
spots["winch"] = (-300, 230, 450)
spots["bridge_mid"] = (-320, 20, 200)
# the water: the market harbour and the canal, round the blocks standing in it
HOLES_W = [(-1180, 700, -1020, 900), (-1160, 965, -1040, 1045), (-475, 75, -175, 325), (-175, 50, -125, 350),
           (-1450, -550, -475, 700)] + STEPS_W  # the last: the market and the canal street (land)
C.water_box(cn, (-1450, -550, -125, 1150), HOLES_W, -40, -10, MUD, WATER, wm=wtr)
cn.build()

# ================================================================================================ the harbour walls
hw = mesh("walls", uv=256.0)
# the dividing wall between the canal (west) and the corsairs' side (east), 320 high
box(hw, -125, -550, -75, 50, -40, 320, MASON, which="ew")
box(hw, -125, 350, -75, 1220, -40, 320, MASON, which="ews")
hw.face([(-475, -550, -40), (-125, -550, -40), (-125, -550, 0), (-475, -550, 0)], MOSS, (0, 1, 0))  # the canal's end
# the market harbour's sea wall and the east sea wall behind the ship and the far pier, 300 high
box(hw, -1450, 1150, -125, 1220, -40, 300, MASON, which="ns")
box(hw, -75, 660, 1950, 720, -40, 300, MASON, which="ns")
# the fort wall east of the ship, 450 high, with the postern the bow's causeway runs through
FX0, FX1, PZ0, PZ1, PTOP = 1400, 1460, 485, 575, 260
for (za, zb, y0) in ((-150, 400, 15), (400, PZ0, -40), (PZ1, 660, -40)):
    sides(hw, FX0, za, FX1, zb, y0, 450, MASON, "w", inset=0)
for (za, zb) in ((-1300, PZ0), (PZ1, 660)):
    sides(hw, FX0, za, FX1, zb, 15, 450, MASON, "e", inset=0)
hw.face([(FX0, PZ0, PTOP), (FX0, PZ1, PTOP), (FX0, PZ1, 450), (FX0, PZ0, 450)], MASON, (-1, 0, 0))
hw.face([(FX1, PZ1, PTOP), (FX1, PZ0, PTOP), (FX1, PZ0, 450), (FX1, PZ1, 450)], MASON, (1, 0, 0))
hw.face([(FX0, PZ0, 15), (FX1, PZ0, 15), (FX1, PZ0, PTOP), (FX0, PZ0, PTOP)], MASON, (0, 1, 0))
hw.face([(FX1, PZ1, 15), (FX0, PZ1, 15), (FX0, PZ1, PTOP), (FX1, PZ1, PTOP)], MASON, (0, -1, 0))
hw.face([(FX0, PZ1, PTOP), (FX1, PZ1, PTOP), (FX1, PZ0, PTOP), (FX0, PZ0, PTOP)], MASON, (0, 0, -1))
hw.face([(FX0, -1300, 450), (FX1, -1300, 450), (FX1, 660, 450), (FX0, 660, 450)], MASON, (0, 0, 1))
hw.build()

# ================================================================================================ the gatehouse
gh = mesh("gatehouse")
GX0, GX1, GZ0, GZ1 = -175, 25, 50, 350
TZ0, TZ1, TH = 120, 280, 200  # the passage through it: 160 wide, 180 high (the door is 198 x 199)
for (x, out) in ((GX0, -1), (GX1, 1)):
    gh.face([(x, GZ0, -40), (x, TZ0, -40), (x, TZ0, 380), (x, GZ0, 380)], BRICK, (out, 0, 0))
    gh.face([(x, TZ1, -40), (x, GZ1, -40), (x, GZ1, 380), (x, TZ1, 380)], BRICK, (out, 0, 0))
    gh.face([(x, TZ0, TH), (x, TZ1, TH), (x, TZ1, 380), (x, TZ0, 380)], BRICK, (out, 0, 0))
gh.face([(GX1, GZ0, -40), (GX0, GZ0, -40), (GX0, GZ0, 380), (GX1, GZ0, 380)], BRICK, (0, -1, 0))
gh.face([(GX0, GZ1, -40), (GX1, GZ1, -40), (GX1, GZ1, 380), (GX0, GZ1, 380)], BRICK, (0, 1, 0))
tiled(gh, GX0, TZ0, GX1, TZ1, 20, PAVE)
gh.face([(GX0, TZ0, 20), (GX1, TZ0, 20), (GX1, TZ0, TH), (GX0, TZ0, TH)], MASON, (0, 1, 0))
gh.face([(GX1, TZ1, 20), (GX0, TZ1, 20), (GX0, TZ1, TH), (GX1, TZ1, TH)], MASON, (0, -1, 0))
gh.face([(GX0, TZ1, TH), (GX1, TZ1, TH), (GX1, TZ0, TH), (GX0, TZ0, TH)], MASON, (0, 0, -1))
gable(gh, GX0 - 10, GZ0 - 10, GX1 + 10, GZ1 + 10, 380, 480, BRICK, along="x")
decal(gh, [(GX1 + 4, 140, 230), (GX1 + 4, 260, 230), (GX1 + 4, 260, 330), (GX1 + 4, 140, 330)], FLAG)
spots["gate_door"] = (GX0 + 5, 20, 200)
spots["gate_lamp_w"] = (GX0 - 30, 230, 330)
spots["gate_lamp_e"] = (GX1 + 40, 240, 90)
gh.build()

# ================================================================================================ D. the yard, the terraces, the tower
e = mesh("east")
R1, R3 = (460, -250, 560, -100), (860, 50, 980, 150)
GANG = (845, 230, 995, 410)
floors(e, (-75, -350, 560, 50), [R1], 20, PAVE)
floors(e, (-75, -550, 520, -350), [], 20, PAVE)
floors(e, (25, 50, 1400, 400), [R3, GANG], 20, PAVE)
floors(e, (-75, 350, 25, 400), [], 20, PAVE)
floors(e, (1000, -150, 1400, 50), [], 20, PAVE)
sides(e, -75, 300, 450, 400, -40, 20, MOSS, "s")
sides(e, 1240, 300, 1400, 400, -40, 20, MOSS, "s")
STEPS_E = [(100, 400, 180, 470), (1300, 400, 1380, 470)]
for (a0, b0, a1, b1) in STEPS_E:
    box(e, a0, b0, a1, b1, -40, -5, MOSS, which="sew")
# the water west of the ship's stern and east of its bow (the hull lies against the quay and the sea wall)
C.water_box(e, (-75, 400, 450, 660), STEPS_E, -40, -10, MUD, WATER, wm=wtr)
C.water_box(e, (1240, 400, FX0, 660), STEPS_E + [(1240, PZ0, FX0, PZ1)], -40, -10, MUD, WATER, wm=wtr)
# the loading terrace (70) and the tower terrace (120), with ramps between
R2, R4, LAND = (680, -350, 820, -250), (600, -750, 800, -690), (520, -950, 600, -690)
floors(e, (560, -350, 1000, 50), [R2, R3], 70, PAVE)
sides(e, 560, -350, 1000, 50, 15, 70, MASON, "ws")
sides(e, 900, -150, 1000, 50, 15, 70, MASON, "e")
floors(e, (520, -750, 1000, -350), [R4, LAND], 120, PAVE)
sides(e, 560, -450, 1000, -350, 65, 120, MASON, "s")
sides(e, 520, -450, 560, -350, 15, 120, MASON, "s")
sides(e, 520, -550, 1000, -350, 15, 120, MASON, "w")
block(e, *R1, 15, 20, MASON, PAVE, which="ns", y1b=70, along="x")
block(e, *R2, 65, 120, MASON, PAVE, which="ew", y1b=70, along="z")
block(e, *R3, 15, 70, MASON, PAVE, which="ew", y1b=20, along="z")
block(e, *R4, 115, 200, DARK, PLANK, which="s", y1b=120, along="x")
block(e, *LAND, 115, 200, DARK, PLANK, which="s")
# cargo stacks in the yard: cover for the boarders
COVER_D = [(130, -400), (330, -250), (160, -120)]
for (cx, cz) in COVER_D:
    box(e, cx - 50, cz - 50, cx + 50, cz + 50, 15, 115, CRATE)
spots["cover_yard"] = COVER_D
# the barracks between the warehouse and the tower: a steep roof nobody stands on
facade(e, (300, -550), (520, -550), (0, 1), eave=260, wall=BRICK, windows=2, win_y=130, roof=False)
sides(e, 300, -950, 520, -550, 115, 260, BRICK, "e", inset=0)
gable(e, 300, -1300, 520, -550, 260, 470, BRICK, along="z", which_ends=("b",))
# the watchtower: 600 x 200 x 200, a room at 200 (Tribal) through a door off the landing, the lookout on top
TX0, TX1, TZ0_, TZ1_ = 600, 800, -950, -750
e.face([(TX0, TZ1_, 115), (TX1, TZ1_, 115), (TX1, TZ1_, 500), (TX0, TZ1_, 500)], MASON, (0, 1, 0))
e.face([(TX1, TZ1_, 115), (TX1, TZ0_, 115), (TX1, TZ0_, 500), (TX1, TZ1_, 500)], MASON, (1, 0, 0))
DZ0, DZ1, DTOP = -880, -800, 350
e.face([(TX0, TZ0_, 200), (TX0, DZ0, 200), (TX0, DZ0, 500), (TX0, TZ0_, 500)], MASON, (-1, 0, 0))
e.face([(TX0, DZ1, 200), (TX0, TZ1_, 200), (TX0, TZ1_, 500), (TX0, DZ1, 500)], MASON, (-1, 0, 0))
e.face([(TX0, DZ0, DTOP), (TX0, DZ1, DTOP), (TX0, DZ1, 500), (TX0, DZ0, 500)], MASON, (-1, 0, 0))
# the room
RX0, RX1, RZ0, RZ1 = TX0 + 15, TX1 - 15, TZ0_ + 15, TZ1_ - 15
tiled(e, RX0, RZ0, RX1, RZ1, 200, PLANK)
e.face([(RX0, RZ1, 360), (RX1, RZ1, 360), (RX1, RZ0, 360), (RX0, RZ0, 360)], DECK, (0, 0, -1))
sides(e, RX0, RZ0, RX1, RZ1, 200, 360, MASON, "nse", inward=True)
for f in ((RX0, RZ0, DZ0), (RX0, DZ1, RZ1)):
    e.face([(f[0], f[2], 200), (f[0], f[1], 200), (f[0], f[1], 360), (f[0], f[2], 360)], MASON, (1, 0, 0))
e.face([(RX0, DZ1, DTOP), (RX0, DZ0, DTOP), (RX0, DZ0, 360), (RX0, DZ1, 360)], MASON, (1, 0, 0))
for (z, out) in ((DZ0, 1), (DZ1, -1)):
    e.face([(TX0, z, 200), (RX0, z, 200), (RX0, z, DTOP), (TX0, z, DTOP)], MASON, (0, out, 0))
e.face([(TX0, DZ1, DTOP), (RX0, DZ1, DTOP), (RX0, DZ0, DTOP), (TX0, DZ0, DTOP)], MASON, (0, 0, -1))
# the top: a floor at 500 for the lookout, a parapet 40 round it
tiled(e, TX0, TZ0_, TX1, TZ1_, 500, MASON, size=110)
sides(e, TX0, TZ0_, TX1, TZ1_, 500, 515, MASON, "nsew", inset=0)  # a curb: the lookout fires over it
sides(e, TX0 + 12, TZ0_ + 12, TX1 - 12, TZ1_ - 12, 500, 515, MASON, "nsew", inward=True)
for f in ((TX0, TZ0_, TX1, TZ0_ + 12), (TX0, TZ1_ - 12, TX1, TZ1_), (TX0, TZ0_ + 12, TX0 + 12, TZ1_ - 12),
          (TX1 - 12, TZ0_ + 12, TX1, TZ1_ - 12)):
    e.face([(f[0], f[3], 515), (f[2], f[3], 515), (f[2], f[1], 515), (f[0], f[1], 515)], MASON, (0, 0, 1))
post(e, 788, -762, 5, 515, 720, DARK, n=4)
decal(e, [(788, -762, 640), (788, -682, 640), (788, -682, 705), (788, -762, 705)], FLAG)
decal(e, [(640, TZ1_ + 4, 300), (680, TZ1_ + 4, 300), (680, TZ1_ + 4, 380), (640, TZ1_ + 4, 380)], SHUTTER)
decal(e, [(720, TZ1_ + 4, 300), (760, TZ1_ + 4, 300), (760, TZ1_ + 4, 380), (720, TZ1_ + 4, 380)], SHUTTER)
spots["perch_tower"] = (700, 500, -850)
spots["tribal_tower"] = (720, 200, -860)
spots["tower_door"] = (TX0, 200, -840)
# the sheds east of the tower: tall, so their roofs are out of reach
facade(e, (800, -750), (1000, -750), (0, 1), eave=450, rise=110, depth=180, y0=115, windows=1, win_y=260)
sides(e, 1000, -750, 1400, -350, 115, 450, PLASTER, "w", inset=0)
sides(e, 1000, -350, 1400, -150, 65, 450, PLASTER, "w", inset=0)
sides(e, 1000, -750, 1400, -150, 15, 450, PLASTER, "s", inset=0)
gable(e, 1000, -760, 1400, -150, 450, 560, PLASTER, along="z", which_ends=("b",), slopes=("a",))
# the sheds' tops behind their roofs (seen from the headland and the tower)
e.face([(1200, -150, 560), (1400, -150, 560), (1400, -760, 560), (1200, -760, 560)], ROOF, (0, 0, 1))
e.face([(800, -930, 560), (1400, -930, 560), (1400, -1300, 560), (800, -1300, 560)], ROOF, (0, 0, 1))
for zc in (-560, -260):
    decal(e, [(996, zc + 50, 125 if zc < -350 else 75), (996, zc - 50, 125 if zc < -350 else 75),
              (996, zc - 50, 300), (996, zc + 50, 300)], SHUTTER)
e.build()

# ================================================================================================ E. the warehouse
wh = mesh("warehouse", uv=220.0)
WX0, WX1, WZ0, WZ1, EAVE, RIDGE, T = -700, 300, -1300, -550, 600, 720, 20
FD0, FD1, FDH = 0, 180, 250        # the front doorway (no door): in the south wall
BD0, BD1, BDH = -980, -820, 180    # the back doorway (the squad's door): in the west wall
tiled(wh, WX0 + T, WZ0 + T, WX1 - T, WZ1 - T, 20, DECK)
# outer walls (brick) and the same inside, with the two doorways
wh.face([(WX0, WZ1, 0), (FD0, WZ1, 0), (FD0, WZ1, EAVE), (WX0, WZ1, EAVE)], BRICK, (0, 1, 0))
wh.face([(FD1, WZ1, 0), (WX1, WZ1, 0), (WX1, WZ1, EAVE), (FD1, WZ1, EAVE)], BRICK, (0, 1, 0))
wh.face([(FD0, WZ1, FDH), (FD1, WZ1, FDH), (FD1, WZ1, EAVE), (FD0, WZ1, EAVE)], BRICK, (0, 1, 0))
wh.face([(WX0, WZ0, 0), (WX0, BD0, 0), (WX0, BD0, EAVE), (WX0, WZ0, EAVE)], BRICK, (-1, 0, 0))
wh.face([(WX0, BD1, 0), (WX0, WZ1, 0), (WX0, WZ1, EAVE), (WX0, BD1, EAVE)], BRICK, (-1, 0, 0))
wh.face([(WX0, BD0, BDH), (WX0, BD1, BDH), (WX0, BD1, EAVE), (WX0, BD0, EAVE)], BRICK, (-1, 0, 0))
wh.face([(WX1, WZ1, 0), (WX1, WZ0, 0), (WX1, WZ0, EAVE), (WX1, WZ1, EAVE)], BRICK, (1, 0, 0))
IX0, IX1, IZ0, IZ1 = WX0 + T, WX1 - T, WZ0 + T, WZ1 - T
wh.face([(IX1, IZ1, 20), (FD1, IZ1, 20), (FD1, IZ1, EAVE), (IX1, IZ1, EAVE)], BRICK, (0, -1, 0))
wh.face([(FD0, IZ1, 20), (IX0, IZ1, 20), (IX0, IZ1, EAVE), (FD0, IZ1, EAVE)], BRICK, (0, -1, 0))
wh.face([(FD1, IZ1, FDH), (FD0, IZ1, FDH), (FD0, IZ1, EAVE), (FD1, IZ1, EAVE)], BRICK, (0, -1, 0))
wh.face([(IX0, IZ1, 20), (IX0, BD1, 20), (IX0, BD1, EAVE), (IX0, IZ1, EAVE)], BRICK, (1, 0, 0))
wh.face([(IX0, BD0, 20), (IX0, IZ0, 20), (IX0, IZ0, EAVE), (IX0, BD0, EAVE)], BRICK, (1, 0, 0))
wh.face([(IX0, BD1, BDH), (IX0, BD0, BDH), (IX0, BD0, EAVE), (IX0, BD1, EAVE)], BRICK, (1, 0, 0))
wh.face([(IX1, IZ0, 20), (IX1, IZ1, 20), (IX1, IZ1, EAVE), (IX1, IZ0, EAVE)], BRICK, (-1, 0, 0))
wh.face([(IX0, IZ0, 20), (IX1, IZ0, 20), (IX1, IZ0, EAVE), (IX0, IZ0, EAVE)], BRICK, (0, 1, 0))
# the doorways' reveals (through the wall) and lintels
for (z, out) in ((FD0, 1), (FD1, -1)):
    wh.face([(z, WZ1, 20), (z, IZ1, 20), (z, IZ1, FDH), (z, WZ1, FDH)], BRICK, (out, 0, 0))
wh.face([(FD0, IZ1, FDH), (FD1, IZ1, FDH), (FD1, WZ1, FDH), (FD0, WZ1, FDH)], BRICK, (0, 0, -1))
tiled(wh, FD0, IZ1, FD1, WZ1, 20, DECK)
for (z, out) in ((BD0, 1), (BD1, -1)):
    wh.face([(WX0, z, 20), (IX0, z, 20), (IX0, z, BDH), (WX0, z, BDH)], BRICK, (0, out, 0))
wh.face([(WX0, BD1, BDH), (IX0, BD1, BDH), (IX0, BD0, BDH), (WX0, BD0, BDH)], BRICK, (0, 0, -1))
tiled(wh, WX0, BD0, IX0, BD1, 20, DECK)
# the roof: gable along x, its underside the ceiling
gable(wh, WX0 - 15, WZ0, WX1 + 15, WZ1 + 15, EAVE, RIDGE, BRICK, along="x")
ZM = (WZ0 + WZ1 + 15) / 2
wh.face([(IX1, IZ0, EAVE), (IX0, IZ0, EAVE), (IX0, ZM, RIDGE - 12), (IX1, ZM, RIDGE - 12)], DECK, (0, 1, -1))
wh.face([(IX0, IZ1, EAVE), (IX1, IZ1, EAVE), (IX1, ZM, RIDGE - 12), (IX0, ZM, RIDGE - 12)], DECK, (0, -1, -1))
wh.face([(IX0, IZ0, EAVE), (IX0, IZ1, EAVE), (IX0, ZM, RIDGE - 12)], BRICK, (1, 0, 0))
wh.face([(IX1, IZ1, EAVE), (IX1, IZ0, EAVE), (IX1, ZM, RIDGE - 12)], BRICK, (-1, 0, 0))
# the loft along the north wall at 220, its stair up the east wall
LZ = -1080
tiled(wh, IX0, IZ0, IX1 - 100, LZ, 220, PLANK)
tiled(wh, IX1 - 100, IZ0, IX1, LZ, 220, PLANK)
tiled(wh, IX0, IZ0, IX1, LZ, 208, DARK, size=260, facing=(0, 0, -1))
wh.face([(IX0, LZ, 208), (IX1 - 100, LZ, 208), (IX1 - 100, LZ, 220), (IX0, LZ, 220)], DARK, (0, 1, 0))
block(wh, IX1 - 100, LZ, IX1, -660, 15, 220, BRICK, PLANK, which="ws", y1b=20, along="z")
lip(wh, (IX0 + 2, LZ), (IX1 - 100, LZ), 220, 220, h=30, thick=-12, mat_=DARK)  # low: the lookout fires over it
# crates: cover for the deckhands on the floor; a hanging crane hook
COVER_E = [(-480, -860), (-260, -700), (-160, -960), (50, -800)]
for (cx, cz) in COVER_E:
    box(wh, cx - 50, cz - 50, cx + 50, cz + 50, 15, 120, CRATE)
spots["cover_warehouse"] = COVER_E
box(wh, -330, -905, -322, -897, 330, 700, DARK, which="nsew")
box(wh, -350, -925, -302, -877, 300, 332, DARK, which="nsew")
wh.face([(-350, -877, 300), (-302, -877, 300), (-302, -925, 300), (-350, -925, 300)], DARK, (0, 0, -1))
spots["back_door"] = (WX0 + 6, 20, (BD0 + BD1) / 2)
spots["front_door"] = ((FD0 + FD1) / 2, 20, WZ1)
spots["loft_far"] = (-600, 220, -1180)
spots["key"] = (-300, 220, -1180)
spots["tribal_loft"] = (-640, 220, -1250)
# the lean-to against the warehouse's south wall: its roof a ledge (any hero who can grab), a health on it
box(wh, -680, -550, -500, -470, 15, 170, PLANK, LEDGE, which="sew")
spots["leanto_top"] = (-590, 170, -510)
wh.build()

# ================================================================================================ F. the ship
sh = mesh("ship", uv=160.0)
SZ = 530.0
STN = [(450, 112), (520, 120), (1240, 120)]  # a blunt bow: the water meets it, and the causeway leaves its middle
GATE0, GATE1 = 841, 999  # the boarding gate's doorway (the door is 198 x 199)


def hb(x):
    for (xa, a), (xb, b) in zip(STN, STN[1:]):
        if xa <= x <= xb:
            return a + (b - a) * (x - xa) / (xb - xa)
    return STN[-1][1]


XS = sorted({450, 520, 600, 700, 800, GATE0, GATE1, 1040, 1100, 1150, 1200, 1240})
for xa, xb in zip(XS, XS[1:]):
    ha, hb_ = hb(xa), hb(xb)
    for side in (-1, 1):
        za, zb = SZ + side * ha, SZ + side * hb_
        out = (0, side, 0)
        sh.face([(xa, za, -40), (xb, zb, -40), (xb, zb, 70), (xa, za, 70)], DARK, out)
        gate = side == -1 and GATE0 <= xa and xb <= GATE1
        frame = side == -1 and 800 <= xa and xb <= 1040 and not gate
        top = 90 if gate else 150
        if not frame:
            sh.face([(xa, za, 70), (xb, zb, 70), (xb, zb, top), (xa, za, top)], DECK, out)
        if gate or frame:
            continue
        ia, ib = SZ + side * (ha - 8), SZ + side * (hb_ - 8)
        sh.face([(xa, ia, 90), (xb, ib, 90), (xb, ib, 150), (xa, ia, 150)], DECK, (0, -side, 0))
        sh.face([(xa, za, 150), (xb, zb, 150), (xb, ib, 150), (xa, ia, 150)], DARK, (0, 0, 1))
        if side == -1:
            collider(edges, (xa, za + 4), (xb, zb + 4), 150, 300)  # low enough to shoot the nests over from the quay
        else:
            collider(edges, (xa, za - 4), (xb, zb - 4), 150, 450)
    # the deck, in pieces about 100 x 110
    ia, ib = hb(xa) - 8, hb(xb) - 8
    for (s0, s1) in ((-1, 0), (0, 1)):
        sh.face([(xa, SZ + s0 * ia, 90), (xb, SZ + s0 * ib, 90), (xb, SZ + s1 * ib, 90), (xa, SZ + s1 * ia, 90)],
                DECK, (0, 0, 1))
sh.face([(450, SZ - 112, -40), (450, SZ + 112, -40), (450, SZ + 112, 150), (450, SZ - 112, 150)], DARK, (-1, 0, 0))
collider(edges, (446, SZ - 112), (446, SZ + 112), 150, 450)
# the bow: a flat stem either side of the causeway, its bulwark and colliders, a bowsprit over the causeway
for (za, zb) in ((SZ - 120, PZ0), (PZ1, SZ + 120)):
    sh.face([(1240, za, -40), (1240, zb, -40), (1240, zb, 150), (1240, za, 150)], DARK, (1, 0, 0))
    ia, ib = max(za, SZ - 112), min(zb, SZ + 112)
    sh.face([(1232, ib, 90), (1232, ia, 90), (1232, ia, 150), (1232, ib, 150)], DECK, (-1, 0, 0))
    sh.face([(1232, ia, 150), (1240, ia, 150), (1240, ib, 150), (1232, ib, 150)], DARK, (0, 0, 1))
    collider(edges, (1236, za), (1236, zb), 150, 300 if za < SZ else 450)
BS = [(1236, -7, 143), (1236, 7, 143), (1236, 7, 157), (1236, -7, 157)]
for k in range(4):
    a, b = BS[k], BS[(k + 1) % 4]
    sh.face([(a[0], SZ + a[1], a[2]), (b[0], SZ + b[1], b[2]), (1340, SZ + b[1], b[2] + 110), (1340, SZ + a[1], a[2] + 110)],
            DARK, None)
# the boarding gate on the quay side: two posts and a lintel over a doorway 158 x 159, its gangplank from the quay
for (xa, xb) in ((800, GATE0), (GATE1, 1040)):
    box(sh, xa, 408, xb, 440, 65, 300, DARK)
box(sh, GATE0, 408, GATE1, 440, 249, 300, DARK, which="ns")
sh.face([(GATE0, 440, 249), (GATE1, 440, 249), (GATE1, 408, 249), (GATE0, 408, 249)], DARK, (0, 0, -1))
block(sh, GANG[0], GANG[1], GANG[2], 360, 15, 20, DARK, PLANK, which="ew", y1b=90, along="z")
block(sh, GANG[0], 360, GANG[2], GANG[3], 15, 90, DARK, PLANK, which="ew")  # a landing at the top: level floor at the door
sh.face([(GATE0, 410, 90), (GATE1, 410, 90), (GATE1, 418, 90), (GATE0, 418, 90)], DECK, (0, 0, 1))
spots["ship_door"] = (920, 90, 424)
# the stern cabin: a Tribal and ammo inside, its door facing the deck
CX0, CX1, CZ0, CZ1, CT = 458, 600, SZ - 104, SZ + 104, 235
CD0, CD1, CDH = SZ - 40, SZ + 40, 200
sh.face([(CX1, CZ1, 90), (CX1, CD1, 90), (CX1, CD1, CT), (CX1, CZ1, CT)], DECK, (1, 0, 0))
sh.face([(CX1, CD0, 90), (CX1, CZ0, 90), (CX1, CZ0, CT), (CX1, CD0, CT)], DECK, (1, 0, 0))
sh.face([(CX1, CD1, CDH), (CX1, CD0, CDH), (CX1, CD0, CT), (CX1, CD1, CT)], DECK, (1, 0, 0))
sh.face([(CX0, CZ0, 150), (CX1, CZ0, 150), (CX1, CZ0, CT), (CX0, CZ0, CT)], DECK, (0, -1, 0))
sh.face([(CX1, CZ1, 150), (CX0, CZ1, 150), (CX0, CZ1, CT), (CX1, CZ1, CT)], DECK, (0, 1, 0))
sh.face([(CX0, CZ1, 150), (CX0, CZ0, 150), (CX0, CZ0, CT), (CX0, CZ1, CT)], DECK, (-1, 0, 0))
sh.face([(CX0, CZ1, CT), (CX1, CZ1, CT), (CX1, CZ0, CT), (CX0, CZ0, CT)], DECK, (0, 0, 1))
I0, I1 = CX0 + 10, CX1 - 10
sh.face([(I0, CZ0 + 10, CT - 10), (I1, CZ0 + 10, CT - 10), (I1, CZ1 - 10, CT - 10), (I0, CZ1 - 10, CT - 10)],
        DECK, (0, 0, -1))
sh.face([(I1, CZ0 + 10, 90), (I0, CZ0 + 10, 90), (I0, CZ0 + 10, CT - 10), (I1, CZ0 + 10, CT - 10)], DARK, (0, 1, 0))
sh.face([(I0, CZ1 - 10, 90), (I1, CZ1 - 10, 90), (I1, CZ1 - 10, CT - 10), (I0, CZ1 - 10, CT - 10)], DARK, (0, -1, 0))
sh.face([(I0, CZ0 + 10, 90), (I0, CZ1 - 10, 90), (I0, CZ1 - 10, CT - 10), (I0, CZ0 + 10, CT - 10)], DARK, (1, 0, 0))
sh.face([(I1, CD0, 90), (I1, CZ0 + 10, 90), (I1, CZ0 + 10, CT - 10), (I1, CD0, CT - 10)], DARK, (-1, 0, 0))
sh.face([(I1, CZ1 - 10, 90), (I1, CD1, 90), (I1, CD1, CT - 10), (I1, CZ1 - 10, CT - 10)], DARK, (-1, 0, 0))
sh.face([(I1, CD0, CDH), (I1, CD1, CDH), (I1, CD1, CT - 10), (I1, CD0, CT - 10)], DARK, (-1, 0, 0))
for (z, out) in ((CD0, 1), (CD1, -1)):
    sh.face([(I1, z, 90), (CX1, z, 90), (CX1, z, CDH), (I1, z, CDH)], DARK, (0, out, 0))
sh.face([(I1, CD1, CDH), (CX1, CD1, CDH), (CX1, CD0, CDH), (I1, CD0, CDH)], DARK, (0, 0, -1))
spots["tribal_cabin"] = (500, 90, SZ - 60)
spots["cabin_ammo"] = (505, 90, SZ + 60)
# the stern flag
post(sh, 470, SZ, 4, CT, 420, DARK, n=4)
decal(sh, [(470, SZ, 350), (470, SZ + 90, 350), (470, SZ + 90, 412), (470, SZ, 412)], FLAG)
# masts with crow's nests at 400 (the lookouts), yards and patched sails braced round so they show from the quay
NESTS = []
for mx in (690, 1150):
    post(sh, mx, SZ, 14, 90, 580, DARK, n=6, cap=True)
    box(sh, mx - 40, SZ - 42, mx + 40, SZ + 42, 85, 192, DARK, PLANK)  # the mast's foot: cover
    tiled(sh, mx - 45, SZ - 45, mx + 45, SZ + 45, 400, PLANK, size=100)
    sh.face([(mx - 45, SZ + 45, 390), (mx + 45, SZ + 45, 390), (mx + 45, SZ - 45, 390), (mx - 45, SZ - 45, 390)],
            DARK, (0, 0, -1))
    sides(sh, mx - 45, SZ - 45, mx + 45, SZ + 45, 390, 412, DARK, "nsew", inset=0)  # a rim: the lookout fires over it
    sides(sh, mx - 41, SZ - 41, mx + 41, SZ + 41, 400, 412, DARK, "nsew", inward=True)
    NESTS.append((mx, 400, SZ))
    a = math.radians(30)
    dx, dz = 95 * math.sin(a), 95 * math.cos(a)
    box(sh, mx - 6, SZ - 110, mx + 6, SZ + 110, 372, 384, DARK, which="nsew")
    decal(sh, [(mx - dx, SZ - dz, 205), (mx + dx, SZ + dz, 205), (mx + dx, SZ + dz, 370), (mx - dx, SZ - dz, 370)],
          SAIL)
spots["nests"] = NESTS
# the other cover on deck: a cargo stack and a hatch
COVER_F = [(690, SZ), (880, SZ + 20), (1010, SZ - 10), (1150, SZ)]
for (cx, cz) in COVER_F[1:3]:
    box(sh, cx - 38, cz - 42, cx + 38, cz + 42, 85, 192, CRATE)
spots["cover_ship"] = COVER_F
for (rx, rz) in ((640, SZ + 70), (1210, SZ - 20)):
    sh.face([(rx - 20, rz + 20, 92.5), (rx + 20, rz + 20, 92.5), (rx + 20, rz - 20, 92.5), (rx - 20, rz - 20, 92.5)],
            ROPE, (0, 0, 1), [(0, 0), (1, 0), (1, 1), (0, 1)])
# the bow's causeway through the fort wall's postern to the far pier
hyc = block(sh, 1240, PZ0, FX1, PZ1, -40, 90, MASON, PLANK, which="", y1b=20, along="x", size=110)
sides(sh, 1240, PZ0, FX0, PZ1, -40, hyc, MASON, "ns", inset=0)
for (z0, z1) in ((PZ0 + 3, PZ0 + 13), (PZ1 - 13, PZ1 - 3)):  # set in from the causeway's sides (flicker)
    lip(sh, (1240, z0), (FX0, z0), hyc(1240, z0), hyc(FX0, z0), h=70, thick=z1 - z0, mat_=DARK,
        coll_to=None)
    collider(edges, (1240, (z0 + z1) / 2), (FX0, (z0 + z1) / 2), 100, 400)
spots["bow"] = (1200, 90, SZ)
sh.build()

# ================================================================================================ G. the far pier and the harbour gate
fa = mesh("far")
floors(fa, (1460, -750, 1950, 660), [], 20, PAVE)
TOWERS = [(1700, -1340, 1820, -1220), (1980, -1340, 2100, -1220)]
floors(fa, (1460, -1300, 2250, -750), [(t[0], -1300, t[2], t[3]) for t in TOWERS] + [(2150, -1300, 2250, -750)], 20,
       PAVE)
# the storehouse east of the far pier and the rock at G's east side
facade(fa, (1950, 660), (1950, -750), (-1, 0), eave=420, rise=110, depth=160, windows=4, win_y=200)
facade(fa, (1950, -750), (2150, -750), (0, 1), eave=420, rise=110, depth=160, windows=1, win_y=200)
fa.face([(2110, -750, 530), (2250, -750, 530), (2250, 720, 530), (2110, 720, 530)], ROOF, (0, 0, 1))
fa.face([(1950, 720, -10), (2250, 720, -10), (2250, 720, 530), (1950, 720, 530)], PLASTER, (0, 1, 0))
sides(fa, 2150, -1300, 2250, -750, 15, 650, CLIFF, "w", inset=0)
sides(fa, 2150, -1300, 2250, -750, 15, 650, CLIFF, "s", inset=0)
fa.face([(2150, -750, 650), (2250, -750, 650), (2250, -1300, 650), (2150, -1300, 650)], CLIFF, (0, 0, 1))
fa.face([(2250, -1300, -10), (2250, 720, -10), (2250, 720, 650), (2250, -1300, 650)], CLIFF, (1, 0, 0))
# the gate between two towers, the torch-lit cave mouth behind it
for (a0, b0, a1, b1) in TOWERS:
    box(fa, a0, b0, a1, b1, 15, 440, MASON, which="sew")
    sides(fa, a0 - 8, b1 - 128, a1 + 8, b1 + 8, 440, 480, MASON, "sew", inset=0)
    fa.face([(a0 - 8, b1 + 8, 480), (a1 + 8, b1 + 8, 480), (a1 + 8, b1 - 128, 480), (a0 - 8, b1 - 128, 480)], MASON,
            (0, 0, 1))
GD0, GD1, GDH, GZF = 1821, 1979, 180, -1290
fa.face([(1820, GZF, GDH), (1980, GZF, GDH), (1980, GZF, 420), (1820, GZF, 420)], MASON, (0, 1, 0))
fa.face([(1820, GZF - 30, 420), (1980, GZF - 30, 420), (1980, GZF, 420), (1820, GZF, 420)], MASON, (0, 0, 1))
fa.face([(1820, GZF, GDH), (1980, GZF, GDH), (1980, GZF - 30, GDH), (1820, GZF - 30, GDH)], MASON, (0, 0, -1))
decal(fa, [(1860, GZF + 4, 250), (1940, GZF + 4, 250), (1940, GZF + 4, 330), (1860, GZF + 4, 330)], FLAG)
KZ0 = -1490
tiled(fa, 1820, KZ0, 1980, -1300, 20, CLIFF, size=110)
tiled(fa, 1820, KZ0, 1980, GZF - 30, 200, CLIFF, size=200, facing=(0, 0, -1))
fa.face([(1820, KZ0, 15), (1820, -1340, 15), (1820, -1340, 200), (1820, KZ0, 200)], CLIFF, (1, 0, 0))  # the towers' sides go on
fa.face([(1980, -1340, 15), (1980, KZ0, 15), (1980, KZ0, 200), (1980, -1340, 200)], CLIFF, (-1, 0, 0))
fa.face([(1980, KZ0, 15), (1820, KZ0, 15), (1820, KZ0, 200), (1980, KZ0, 200)], DARK, (0, 1, 0))
spots["harbour_door"] = (1900, 20, GZF - 8)
spots["harbour_exit"] = (1900, 20, -1440)
spots["tower_flames"] = [(1760, 480, -1240), (2040, 480, -1240)]
spots["cave_torches"] = [(1835, 150, -1400), (1965, 150, -1400)]
# cover in front of the gate: stone blocks
COVER_G = [(1600, -1000), (1720, -1120), (1790, -880), (1990, -1080), (2050, -880)]
for (cx, cz) in COVER_G:
    box(fa, cx - 50, cz - 50, cx + 50, cz + 50, 15, 115, MASON)
spots["cover_gate"] = COVER_G
# the far pier: cargo, bollards and a lantern post along it
for (cx, cz) in ((1880, -300), (1880, 150), (1540, -500)):
    box(fa, cx - 45, cz - 45, cx + 45, cz + 45, 15, 100, CRATE)
    box(fa, cx - 30, cz - 30, cx + 30, cz + 30, 100, 160, CRATE)
for bz in (-600, -200, 250):
    post(fa, 1475 + 20, bz, 12, 15, 60, DARK, n=6)
post(fa, 1520, 400, 6, 15, 240, DARK, n=4)
box(fa, 1510, 390, 1530, 410, 240, 265, CRATE)
spots["far_lamp"] = (1520, 260, 400)
fa.build()

# ================================================================================================ the cliffs and the level's edge
cl = mesh("cliff", uv=240.0)
rng = random.Random(12)
cols = sorted(set(list(range(-2250, 2251, 150)) + [1820, 1980]))
rows = [0, 250, 500, 750]
jag = {}
for x in cols:
    for k, y in enumerate(rows):
        base = [-1290, -1320, -1350, -1385][k]
        jag[(x, y)] = base - (rng.uniform(0, 8) if k == 0 else rng.uniform(0, 45))
for xa, xb in zip(cols, cols[1:]):
    for k in range(len(rows) - 1):
        ya, yb = rows[k], rows[k + 1]
        if 1820 <= xa and xb <= 1980 and ya < 200:
            ya = 200  # the cave mouth
            za, zb = GZF - 30, GZF - 30
            cl.face([(xa, za, ya), (xb, zb, ya), (xb, jag[(xb, yb)], yb), (xa, jag[(xa, yb)], yb)], CLIFF, (0, 1, 0.3))
            continue
        cl.face([(xa, jag[(xa, ya)], ya), (xb, jag[(xb, ya)], ya), (xb, jag[(xb, yb)], yb), (xa, jag[(xa, yb)], yb)],
                CLIFF, (0, 1, 0.3))
    cl.face([(xa, jag[(xa, 750)], 750), (xb, jag[(xb, 750)], 750), (xb, -1500, 760), (xa, -1500, 760)], CLIFF,
            (0, 0, 1))
cl.build()
# boundary colliders behind the cliffs and buildings at the level's edge (never over the open sea: the sea walls and
# the parapets with colliders close the south and the start)
for (a, b) in (((-2250, -1500), (2250, -1500)), ((2250, -1500), (2250, 720)), ((-2250, 1250), (-2250, -1500))):
    collider(edges, a, b, -60, 1300)
edges.build()
wtr.build()

# ------------------------------------------------------------------------------------------------ the open sea beyond the walls
far = Mesh("sea_far", [MATS[WATER]], coll, uv_size=6000.0)


# one grid out to the horizon, so neighbouring pieces share whole edges (an edge ending on the middle of another's
# reads as water hovering); small pieces near the level (a big triangle's box meets every query near it), big far out
SEA_IN = [(-75, 720, 2250, 1500), (-1450, 1220, -75, 1500), (-1690, 1250, -1450, 1500), (-2250, 1460, -2100, 1500),
          (-2250, 1250, -2210, 1460),
          (-1980, 1460, -1690, 1500)]  # the sea inside the level's square: south of its walls and the start


def sea_cuts(lo, hi, inner, edges):
    """Cut points from lo to hi: every 6000 (the water's texture repeats there, and it doesn't tile: a piece across a
    repeat gets cut by the importer, which left holes far out), the level's edges, and pieces of 600 or less near it."""
    out = sorted({lo, hi} | {v for v in range(-12000, 12001, 6000) if lo < v < hi} | {v for v in edges if lo < v < hi})
    fine = []
    for p, q in zip(out, out[1:]):
        n = max(1, math.ceil((q - p) / 600)) if inner[0] <= p and q <= inner[1] else 1
        fine += [p + (q - p) * k / n for k in range(n)]
    return fine + [hi]


ex = sea_cuts(-12000, 12000, (-2250, 2250), [-2250, -2210, -2100, -1980, -1690, -1450, -75, 2250])
ez = sea_cuts(-6000, 12000, (-1500, 1500), [-1500, 720, 1220, 1250, 1460, 1500])
for i in range(len(ex) - 1):
    for j in range(len(ez) - 1):
        cx, cz = (ex[i] + ex[i + 1]) / 2, (ez[j] + ez[j + 1]) / 2
        inside = -2250 < cx < 2250 and -1500 < cz < 1500
        if inside and not any(r[0] < cx < r[2] and r[1] < cz < r[3] for r in SEA_IN):
            continue
        if -2250 < cx < 2250 and cz < -1500:
            continue  # behind the north cliff
        far.face([(ex[i], ez[j], -10), (ex[i + 1], ez[j], -10), (ex[i + 1], ez[j + 1], -10), (ex[i], ez[j + 1], -10)],
                 0, (0, 0, 1))
far.build()

# ------------------------------------------------------------------------------------------------ light: golden hour
level = [o for o in coll.all_objects if o.type == "MESH"]
SUN_DIR = (0.84, 0.22, -0.48)  # low from the west-south-west (Blender space: the light's travel)
LAMPS = [
    (-1350, -400, 300, 260, (0.12, 0.2, 0.5)),     # the smugglers' blue lantern
    (-1380, 160, 240, 300, (0.5, 0.32, 0.12)),     # the chest stall
    (-900, 640, 250, 320, (0.5, 0.3, 0.1)),        # the promenade
    (-1030, 1052, 250, 280, (0.5, 0.3, 0.1)),      # the pier's end
    (-300, 450, 260, 300, (0.55, 0.33, 0.1)),      # the winch's lamp
    (-205, 200, 330, 260, (0.5, 0.3, 0.12)),       # the gatehouse door
    (65, 90, 240, 260, (0.5, 0.3, 0.12)),          # its east side
    (700, -850, 540, 260, (0.5, 0.32, 0.12)),      # the tower lookout's lantern
    (700, -850, 300, 200, (0.45, 0.3, 0.12)),      # the tower room
    (-200, -800, 420, 520, (0.45, 0.28, 0.1)),     # the warehouse
    (-560, -1180, 300, 280, (0.5, 0.3, 0.1)),      # the loft lookout's lantern
    (690, 530, 440, 240, (0.5, 0.32, 0.12)),       # the nests
    (1150, 530, 440, 240, (0.5, 0.32, 0.12)),
    (920, 380, 280, 280, (0.5, 0.32, 0.12)),       # the boarding gate
    (520, 530, 200, 200, (0.45, 0.28, 0.1)),       # the cabin
    (1520, 400, 260, 300, (0.5, 0.3, 0.1)),        # the far pier
    (1760, -1240, 480, 360, (0.6, 0.32, 0.1)),     # the harbour gate's tower fires
    (2040, -1240, 480, 360, (0.6, 0.32, 0.1)),
    (1900, -1400, 150, 300, (0.6, 0.3, 0.08)),     # the cave mouth's torches
]


def extra(x, z, y, mname):
    if mname.startswith("game_1958") or mname.startswith("game_1959"):  # wet stone and mud darker near the water
        k = max(0.0, min(1.0, (y + 20) / 50.0))
        return (0.7 + 0.3 * k, 0.72 + 0.28 * k, 0.78 + 0.22 * k)
    return (1.0, 1.0, 1.0)


TINTS = {"game_0828": (1.0, 0.96, 0.9), "game_1933": (1.05, 0.92, 0.85), "game_008B": (1.02, 0.96, 0.9)}
C.bake(level, SUN_DIR, (0.95, 0.66, 0.36), (0.36, 0.31, 0.5), tints=TINTS, lamps=LAMPS, extra=extra,
       soft={"game_1946": (0.55, 0.3)})

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
    json.dump({k: tup(v) for k, v in spots.items()}, f, indent=1)
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(C.OUT, NAME + ".blend"))
print("GULLWING", json.dumps(report))
print("PARTS", json.dumps({o.name: sum(len(p.vertices) - 2 for p in o.data.polygons) for o in level}))
