"""Stormspire (Corsair Reach 2.4): builds the level from nothing and exports blender/out/stormspire.glb.

    blender --background --factory-startup --addons jfg64 --python stormspire.py

Mirefall's last level: the lighthouse on its rock where the corsairs' storm engine runs on the Stormglass. From the
town's causeway gatehouse (the way back) the causeway (0, parapets 140 with colliders over them) runs 1,200 north
over the sea to the keeper's islet (40: the keeper's cottage, a shed, the tower door). The tower stands on the islet:
round outside (a 16-sided drum, 1,060 across), a square stairwell inside (700). Its ground floor (50) has a ramp up
the west wall to the north half-floor (220, the slickers' landing) and another up the east wall to the south
half-floor (400), where the gallery door is held by a pulley across the stairwell (a switch). Outside, the gallery
(220 wide, rails at 150 with colliders to 1,300) climbs once round the tower: east from the door (400) up to the
north balcony (650, wide: the wardens; two lookouts on perches over it at 880), west and up to the south balcony
(900) over the door. Through the south wall at 900, the keeper's floor (squads round six blocks; a storeroom nook);
the lamp room door in the stairwell's partition opens on a ramp up the west wall and along the north wall, through
a slot in the lamp room's floor, to the lamp room (1,200: 1,000 across, barred windows all round, the storm engine in
the middle, the lift cage out on the east side: the way on).

Game units: x east, z south (north is -z), y up. The level's numbers are in levels/2.4_stormspire.md (As built).
"""
import json
import math
import os
import random
import sys

import bpy

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import common as C  # noqa: E402
from common import Mesh, tiled, post, collider, lip, fence, walls, ceiling, plane_rect, strip  # noqa: E402
import jfg64  # noqa: E402

NAME = "stormspire"
scene, coll = C.new_scene(NAME)
rnd = random.Random(24)

TZ = -600.0                       # the tower's centre (x 0)
RA = 530.0                        # the tower's outside (the 16-gon's apothem)
RL = 500.0                        # the lamp room's inside
RG = 750.0                        # the gallery's outer edge (220 wide)
RB = 900.0                        # the north balcony's outer edge
HALF = math.radians(11.25)
COS = math.cos(HALF)
IX0, IZ0, IX1, IZ1 = -350.0, -950.0, 350.0, -250.0   # the square stairwell inside
YI = 40.0      # the islet
Y0 = 50.0      # the tower's ground floor
YG1 = 220.0    # the north half-floor
YG2 = 400.0    # the south half-floor, the gallery door
YN = 650.0     # the north balcony
YK = 900.0     # the south balcony, the keeper's floor
YL = 1200.0    # the lamp room
YTOP = 1500.0  # the lamp room's ceiling
SEA = -120.0
SLAB = 30.0    # the gallery's thickness


# ------------------------------------------------------------------------------------------------ our own images
def window_px(x, y):
    """A lit window: four warm panes in a dark frame (as 2.1's)."""
    if x in (0, 15) or y in (0, 15) or x in (7, 8) or y in (7, 8):
        return (0.16, 0.11, 0.07)
    k = 1.0 - 0.25 * (y / 15.0)
    return (1.0 * k, 0.78 * k, 0.38 * k)


def warn_px(x, y):
    """The engine's warning plate: yellow and black chevrons round a dark plate with a pale lightning bolt."""
    if x < 5 or x > 26 or y < 5 or y > 26:
        return (0.95, 0.78, 0.12) if ((x + y) // 4) % 2 == 0 else (0.08, 0.07, 0.06)
    bolt = [(14, 7), (19, 7), (16, 14), (20, 14), (12, 25), (14, 17), (11, 17)]
    # inside the bolt: a crude test on the two slanted strokes
    in_top = 7 <= y <= 15 and abs(x - (19 - (y - 7) * 0.45)) < 2.2
    in_bot = 14 <= y <= 25 and abs(x - (18 - (y - 14) * 0.6)) < 2.0
    if in_top or in_bot or (y in (14, 15) and 13 <= x <= 20):
        return (0.85, 0.92, 1.0)
    del bolt
    return (0.16, 0.17, 0.2)


def glass_px(x, y):
    """The Stormglass's glow: pale blue, brightest in the middle, a few white streaks."""
    d = math.hypot((x - 7.5) / 8.0, (y - 15.5) / 16.0)
    k = max(0.0, 1.0 - d)
    streak = 0.25 if (x + y * 3) % 11 == 0 else 0.0
    return (min(1.0, 0.35 + 0.55 * k + streak), min(1.0, 0.6 + 0.4 * k + streak), 1.0)


def lattice_px(x, y):
    """The lift cage's iron lattice: diagonal bars over a dim inside."""
    if (x + y) % 8 in (0, 1) or (x - y) % 8 in (0, 1) or x in (0, 31) or y in (0, 31):
        return (0.2, 0.2, 0.22)
    return (0.05, 0.06, 0.08)


def portcullis_px(x, y):
    """The causeway gate's portcullis: dark iron bars, the passage black behind."""
    if x % 6 in (0, 1) or y % 10 in (0, 1):
        return (0.22, 0.2, 0.18)
    return (0.03, 0.03, 0.04)


# ------------------------------------------------------------------------------------------------ materials
MATS, M = [], {}


def mat(name, material):
    M[name] = len(MATS)
    MATS.append(material)
    return M[name]


WHITE = mat("white", C.game(0x0715))     # the tower's whitewashed stone, the cottage
ASHLAR = mat("ashlar", C.game(0x0828))   # the causeway, parapets, the gatehouse, the sea wall
ROCK = mat("rock", C.game(0x08A8))       # the islet's cliffs and mounds, cover blocks on the islet
MOSS = mat("moss", C.game(0x1958))       # the islet's wet ground
PAVE = mat("pave", C.game(0x0AC0))       # the causeway's road
FLAGS = mat("flags", C.game(0x16DF))     # the gallery, the balconies, the stair's floors
DECK = mat("deck", C.game(0x16D9))       # the keeper's floor, the ramps inside
DARK = mat("dark", C.game(0x16DB))       # beams, rails, posts, cables, the bars
SLATE = mat("slate", C.game(0x0CAF))     # roofs
METAL = mat("metal", C.game(0x0B0B))     # the engine, its housings, the cage
WATER = mat("water", C.game(0x0DED, "water"))
LEDGE = mat("ledge", jfg64.game_texture_material(0x16DF, "ledge", name="ledge_16DF"))
WINDOW = mat("window", C.own_material("lit_window", C.own_image("lit_window", 16, 16, window_px)))
WARN = mat("warn", C.own_material("warning_plate", C.own_image("warning_plate", 32, 32, warn_px)))
GLASS = mat("glass", C.own_material("storm_glass", C.own_image("storm_glass", 16, 32, glass_px)))
LATTICE = mat("lattice", C.own_material("lift_lattice", C.own_image("lift_lattice", 32, 32, lattice_px)))
GATE = mat("gate", C.own_material("portcullis", C.own_image("portcullis", 32, 32, portcullis_px)))
EDGE = jfg64.boundary_material()


def mesh(name, uv=200.0):
    return Mesh(name, MATS, coll, uv_size=uv)


ground_parts = []
cw = mesh("causeway")          # the causeway, the gatehouse
isl = mesh("islet")            # the sea wall, cliffs, cottage, shed, cover
tw = mesh("tower", uv=160.0)   # the tower's outside and the lamp room
ins = mesh("inside")           # the stairwell, the keeper's floor, the stair to the lamp room
gal = mesh("gallery")          # the gallery, its balconies and rails
props = mesh("props", 128.0)   # the engine, lanterns, bars, cables, pictures
edges = Mesh("colliders", [EDGE], coll)
spare = Mesh("spare", [EDGE], coll)   # never built: fences whose collider another fence already gives
spots = {}
LAMPS = []
WARM = (0.55, 0.36, 0.14)
COLD = (0.25, 0.45, 0.85)


# ------------------------------------------------------------------------------------------------ the 16-gon
def P(r, deg):
    """A point r out from the tower's centre at deg (0 south, 90 east, 180 north, 270 west)."""
    a = math.radians(deg)
    return (r * math.sin(a), TZ + r * math.cos(a))


def V(a, k):
    """The corner at the end of side k (side k faces 22.5 k degrees) of the 16-gon of apothem a."""
    return P(a / COS, 22.5 * k + 11.25)


def L(k, r, t):
    """Side k's frame: r out along its normal, t along it (towards side k + 1)."""
    a = math.radians(22.5 * k)
    return (r * math.sin(a) + t * math.cos(a), TZ + r * math.cos(a) - t * math.sin(a))


def nrm(k, s=1.0):
    a = math.radians(22.5 * k)
    return (s * math.sin(a), s * math.cos(a), 0.0)


def tan_(k):
    a = math.radians(22.5 * k)
    return (math.cos(a), -math.sin(a), 0.0)


def half(a):
    return a * math.tan(HALF)


def ngon(a):
    """The 16-gon's half-planes: nx x + nz z <= c."""
    out = []
    for k in range(16):
        s, c = math.sin(math.radians(22.5 * k)), math.cos(math.radians(22.5 * k))
        out.append((s, c, a + c * TZ))
    return out


def wedge(d0, d1):
    """The half-planes keeping deg0 <= angle <= deg1 (d1 - d0 under 180)."""
    a0, a1 = math.radians(d0), math.radians(d1)
    return [(-math.cos(a0), math.sin(a0), math.sin(a0) * TZ), (math.cos(a1), -math.sin(a1), -math.sin(a1) * TZ)]


def inside(planes, x, z, eps=0.5):
    return all(nx * x + nz * z <= c + eps for nx, nz, c in planes)


def clip(poly, nx, nz, c):
    out = []
    for i in range(len(poly)):
        p, q = poly[i], poly[(i + 1) % len(poly)]
        dp, dq = nx * p[0] + nz * p[1] - c, nx * q[0] + nz * q[1] - c
        if dp <= 0:
            out.append(p)
        if (dp < 0 < dq) or (dq < 0 < dp):
            t = dp / (dp - dq)
            out.append((p[0] + (q[0] - p[0]) * t, p[1] + (q[1] - p[1]) * t))
    return out


def area(poly):
    return abs(sum(poly[i][0] * poly[(i + 1) % len(poly)][1] - poly[(i + 1) % len(poly)][0] * poly[i][1]
                   for i in range(len(poly)))) / 2


def tile_flat(m, planes, y, mt, box, xs_extra=(), zs_extra=(), skip=None, step=125.0, facing=(0, 0, 1)):
    """A flat floor (or ceiling) at y over the convex region `planes`, in grid cells of at most `step` through the
    extra lines (holes' and walls' edges), each cell clipped to the region; skip(x0, z0, x1, z1) leaves one out."""
    x0, z0, x1, z1 = box
    xs = C._cuts(x0, x1, [v for v in xs_extra if x0 < v < x1], step)
    zs = C._cuts(z0, z1, [v for v in zs_extra if z0 < v < z1], step)
    for i in range(len(xs) - 1):
        for j in range(len(zs) - 1):
            a, b, c, d = xs[i], zs[j], xs[i + 1], zs[j + 1]
            if skip is not None and skip(a, b, c, d):
                continue
            poly = [(a, b), (c, b), (c, d), (a, d)]
            for (nx, nz, cc) in planes:
                poly = clip(poly, nx, nz, cc)
                if len(poly) < 3:
                    break
            if len(poly) < 3 or area(poly) < 4.0:
                continue
            m.face([(p[0], p[1], y) for p in poly], mt, facing)


def in_rects(rects, a, b, c, d):
    cx, cz = (a + c) / 2, (b + d) / 2
    return any(r[0] <= cx <= r[2] and r[1] <= cz <= r[3] for r in rects)


def all_inside(planes, a, b, c, d):
    return all(inside(planes, x, z, 0.5) for x, z in ((a, b), (c, b), (c, d), (a, d)))


def side_wall(m, k, a, y0, y1, holes, mt, inward=False, step=220.0):
    """Side k of the 16-gon of apothem a, y0 to y1, less openings (t0, v0, t1, v1) (t across the side, 0 its
    middle), in pieces of at most `step` high; facing out (inward: into the room)."""
    h = half(a)
    rects = C.rects_minus((0.0, y0, 2 * h, y1), [(t0 + h, v0, t1 + h, v1) for (t0, v0, t1, v1) in holes])
    f = nrm(k, -1.0 if inward else 1.0)
    for (u0, v0, u1, v1) in rects:
        vs = C.cuts(v0, v1, step)
        for va, vb in zip(vs, vs[1:]):
            p, q = L(k, a, u0 - h), L(k, a, u1 - h)
            m.face([(p[0], p[1], va), (q[0], q[1], va), (q[0], q[1], vb), (p[0], p[1], vb)], mt, f,
                   [(u0 / 128, va / 128), (u1 / 128, va / 128), (u1 / 128, vb / 128), (u0 / 128, vb / 128)])


def side_reveal(m, k, t0, t1, v0, v1, a0, a1, mt, sill=True):
    """An opening's reveal through side k's wall between apothems a0 and a1: its jambs, sill and lintel."""
    p0, p1, q0, q1 = L(k, a0, t0), L(k, a1, t0), L(k, a0, t1), L(k, a1, t1)
    tn = tan_(k)
    m.face([(p0[0], p0[1], v0), (p1[0], p1[1], v0), (p1[0], p1[1], v1), (p0[0], p0[1], v1)], mt, tn)
    m.face([(q0[0], q0[1], v0), (q1[0], q1[1], v0), (q1[0], q1[1], v1), (q0[0], q0[1], v1)], mt,
           (-tn[0], -tn[1], 0))
    m.face([(p0[0], p0[1], v1), (p1[0], p1[1], v1), (q1[0], q1[1], v1), (q0[0], q0[1], v1)], mt, (0, 0, -1))
    if sill:
        m.face([(p0[0], p0[1], v0), (p1[0], p1[1], v0), (q1[0], q1[1], v0), (q0[0], q0[1], v0)], mt, (0, 0, 1))


def lbox(m, k, r0, r1, t0, t1, y0, y1, mt, top=None, inner=False, bottom=True):
    """A block in side k's frame (r0..r1 out, t0..t1 along); the face against the wall (r0) left out."""
    top = mt if top is None else top
    c = [L(k, r0, t0), L(k, r1, t0), L(k, r1, t1), L(k, r0, t1)]
    m.face([(p[0], p[1], y1) for p in c], top, (0, 0, 1))
    if bottom:
        m.face([(p[0], p[1], y0) for p in c], mt, (0, 0, -1))
    n, tn = nrm(k), tan_(k)
    sides = [(c[1], c[2], n), (c[0], c[1], (-tn[0], -tn[1], 0)), (c[2], c[3], tn)]
    if inner:
        sides.append((c[3], c[0], (-n[0], -n[1], 0)))
    for a, b, f in sides:
        m.face([(a[0], a[1], y0), (b[0], b[1], y0), (b[0], b[1], y1), (a[0], a[1], y1)], mt, f)


def reveal(m, plane, c0, c1, u0, u1, y, h, mt, floor_mt):
    """A doorway's reveal through a wall between planes c0 and c1 (plane "z": z = c, u is x): its floor at y, its
    two sides and its lintel's underside at y + h (2.3's)."""
    a, b = min(c0, c1), max(c0, c1)
    if plane == "z":
        tiled(m, u0, a, u1, b, y, floor_mt, size=100.0)
        m.face([(u0, a, y), (u0, b, y), (u0, b, y + h), (u0, a, y + h)], mt, (1, 0, 0))
        m.face([(u1, a, y), (u1, b, y), (u1, b, y + h), (u1, a, y + h)], mt, (-1, 0, 0))
        m.face([(u0, a, y + h), (u1, a, y + h), (u1, b, y + h), (u0, b, y + h)], mt, (0, 0, -1))
    else:
        tiled(m, a, u0, b, u1, y, floor_mt, size=100.0)
        m.face([(a, u0, y), (b, u0, y), (b, u0, y + h), (a, u0, y + h)], mt, (0, 1, 0))
        m.face([(a, u1, y), (b, u1, y), (b, u1, y + h), (a, u1, y + h)], mt, (0, -1, 0))
        m.face([(a, u0, y + h), (b, u0, y + h), (b, u1, y + h), (a, u1, y + h)], mt, (0, 0, -1))


def lantern(m, x, z, y, h=170.0, colour=WARM, radius=300.0):
    """A lamp on an iron post: a glass box (lit window image) under a dark cap."""
    post(m, x, z, 6, y, y + h, DARK, n=4, cap=False, phase=math.pi / 4)
    for (a, b, f) in (((x - 12, z + 12), (x + 12, z + 12), (0, 1, 0)), ((x + 12, z - 12), (x - 12, z - 12), (0, -1, 0)),
                      ((x + 12, z + 12), (x + 12, z - 12), (1, 0, 0)), ((x - 12, z - 12), (x - 12, z + 12), (-1, 0, 0))):
        m.face([(a[0], a[1], y + h), (b[0], b[1], y + h), (b[0], b[1], y + h + 28), (a[0], a[1], y + h + 28)], WINDOW, f,
               [(0, 0), (1, 0), (1, 1), (0, 1)])
    m.face([(x - 12, z - 12, y + h), (x + 12, z - 12, y + h), (x + 12, z + 12, y + h), (x - 12, z + 12, y + h)], DARK,
           (0, 0, -1))
    m.box(x - 16, z - 16, x + 16, z + 16, y + h + 28, y + h + 36, DARK)
    LAMPS.append((x, z, y + h + 14, radius, colour))


def decal_side(m, k, t, y, w, h, mt, out=4.0):
    """A picture on side k's outside, `out` in front of it, centred t along it, y..y+h."""
    p, q = L(k, RA + out, t - w / 2), L(k, RA + out, t + w / 2)
    m.face([(p[0], p[1], y), (q[0], q[1], y), (q[0], q[1], y + h), (p[0], p[1], y + h)], mt, nrm(k),
           [(0, 0), (1, 0), (1, 1), (0, 1)])


# ================================================================================================ A. the causeway
CW_Z0, CW_Z1, CW_RAMP = 500.0, 1700.0, 640.0
COVER_A = [(-70, 1350), (60, 1160), (-60, 960)]     # broken parapet blocks (90 x 90, 105 tall)
CART = (40.0, 780.0)
cov_a = [(x - 45, z - 45, x + 45, z + 45) for x, z in COVER_A]
for rr in C.rects_minus((-150, CW_RAMP, 150, CW_Z1), cov_a):
    tiled(cw, *rr, 0.0, PAVE, size=100.0)
tiled(cw, -150, CW_Z0, 150, CW_RAMP, YI, PAVE, 0.0, along="z", size=100.0)
for xs, f in ((150, (1, 0, 0)), (-150, (-1, 0, 0))):
    strip(cw, (xs, CW_Z0), (xs, CW_RAMP), -200, -200, YI, 0, ASHLAR, f)
    strip(cw, (xs, CW_RAMP), (xs, CW_Z1), -200, -200, 0, 0, ASHLAR, f)
# the parapets (140, a collider to 400 over them), inside the causeway's edges
lip(cw, (150, CW_Z0), (150, CW_RAMP), YI, 0.0, ASHLAR, h=140, thick=25, coll_to=400, edges=edges, caps=(True, False))
lip(cw, (150, CW_RAMP), (150, CW_Z1), 0.0, 0.0, ASHLAR, h=140, thick=25, coll_to=400, edges=edges, caps=(False, False))
lip(cw, (-150, CW_RAMP), (-150, CW_Z0), 0.0, YI, ASHLAR, h=140, thick=25, coll_to=400, edges=edges, caps=(False, True))
lip(cw, (-150, CW_Z1), (-150, CW_RAMP), 0.0, 0.0, ASHLAR, h=140, thick=25, coll_to=400, edges=edges, caps=(False, False))
for (x, z) in COVER_A:   # fallen parapet blocks
    cw.box(x - 45, z - 45, x + 45, z + 45, 0, 105, ASHLAR)
# the wrecked cart: a bed on its side, two wheels (dark boards), outside the cover's lines
cx, cz = CART
cw.box(cx - 35, cz - 70, cx + 35, cz + 70, 0, 60, DARK)
cw.box(cx + 37, cz - 50, cx + 43, cz - 10, 0, 50, DARK)
cw.box(cx + 37, cz + 10, cx + 43, cz + 50, 0, 50, DARK)
spots["cover_a"] = COVER_A
spots["cart"] = CART

# the gatehouse at the south end (the town's side): a passage 160 x 170 into it, 130 deep, the way back
GX0, GX1, GZ0, GZ1, GTOP = -260.0, 260.0, 1700.0, 1900.0, 380.0
plane_rect(cw, "z", GZ0, GX0, -200, GX1, GTOP, [(-80, 0, 80, 170)], ASHLAR, (0, -1, 0))
plane_rect(cw, "z", GZ1, GX0, -200, GX1, GTOP, [], ASHLAR, (0, 1, 0))
plane_rect(cw, "x", GX0, GZ0, -200, GZ1, GTOP, [], ASHLAR, (-1, 0, 0))
plane_rect(cw, "x", GX1, GZ0, -200, GZ1, GTOP, [], ASHLAR, (1, 0, 0))
tiled(cw, GX0, GZ0, GX1, GZ1, GTOP, ASHLAR, size=None if False else 260.0)
PZ1 = 1830.0
tiled(cw, -80, GZ0, 80, PZ1, 0.0, PAVE, size=80.0)
cw.face([(-80, GZ0, 0), (-80, PZ1, 0), (-80, PZ1, 170), (-80, GZ0, 170)], ASHLAR, (1, 0, 0))
cw.face([(80, GZ0, 0), (80, PZ1, 0), (80, PZ1, 170), (80, GZ0, 170)], ASHLAR, (-1, 0, 0))
cw.face([(-80, GZ0, 170), (80, GZ0, 170), (80, PZ1, 170), (-80, PZ1, 170)], DARK, (0, 0, -1))
cw.face([(-80, PZ1, 0), (80, PZ1, 0), (80, PZ1, 170), (-80, PZ1, 170)], GATE, (0, -1, 0),
        [(0, 0), (1, 0), (1, 1), (0, 1)])
# merlons along the gatehouse's top, front edge
for x in (-230, -130, -30, 70, 170):
    cw.box(x, GZ0, x + 60, GZ0 + 40, GTOP, GTOP + 50, ASHLAR)
lantern(cw, -120, GZ0 - 30, 0.0, h=190)
lantern(cw, 120, GZ0 - 30, 0.0, h=190)
spots["start0"] = (0, 0, 1600)
spots["exit_back"] = (0, 0, 1770)
cw.build()

# ================================================================================================ B. the keeper's islet
IS_X0, IS_X1, IS_Z0, IS_Z1 = -700.0, 700.0, -1300.0, 500.0
COTTAGE = (-600.0, 100.0, -400.0, 400.0)
COVER_B = [(-150, 350), (50, 250), (250, 350)]       # fallen tower stones (100 x 100, 110 tall)
cov_b = [(x - 50, z - 50, x + 50, z + 50) for x, z in COVER_B]
TOWER_OUT = ngon(RA)
MOUNDS = [(-520, -1150, 150, 60), (520, -1150, 150, 60), (560, -100, 120, 40)]


def isl_height(x, z):
    y = YI
    for (mx, mz, r, h) in MOUNDS:
        d = math.hypot(x - mx, z - mz)
        if d < r:
            y += h * C.smooth(1 - d / r)
    return y


def isl_skip(x, z):
    a, b, c, d = x - 50, z - 50, x + 50, z + 50
    if all_inside(TOWER_OUT, a, b, c, d):
        return True
    return in_rects([COTTAGE] + cov_b, a, b, c, d)


def isl_mat(x, z, y, slope):
    return M["rock"] if slope > 14 else M["moss"]


ground = C.heightfield("islet_ground", coll, IS_X0, IS_Z0, IS_X1, IS_Z1, 100.0, isl_height, isl_mat, MATS,
                       boundary=0, skip=isl_skip)
ground_parts.append(ground)
# the islet's cliffs down into the sea, and the sea wall on top (150, a collider to 400 over it)
for (a, b, f) in (((IS_X0, IS_Z0), (IS_X1, IS_Z0), (0, -1, 0)), ((IS_X1, IS_Z0), (IS_X1, IS_Z1), (1, 0, 0)),
                  ((IS_X1, IS_Z1), (150, IS_Z1), (0, 1, 0)), ((-150, IS_Z1), (IS_X0, IS_Z1), (0, 1, 0)),
                  ((IS_X0, IS_Z1), (IS_X0, IS_Z0), (-1, 0, 0))):
    strip(isl, a, b, -200, -200, YI, YI, ROCK, f)
lip(isl, (IS_X1, IS_Z0), (IS_X1, IS_Z1), YI, YI, ASHLAR, h=150, thick=25, coll_to=400, edges=edges)
lip(isl, (IS_X0, IS_Z1), (IS_X0, IS_Z0), YI, YI, ASHLAR, h=150, thick=25, coll_to=400, edges=edges)
lip(isl, (IS_X0 + 25, IS_Z0), (IS_X1 - 25, IS_Z0), YI, YI, ASHLAR, h=150, thick=25, coll_to=400, edges=edges,
    caps=(False, False))
lip(isl, (IS_X1 - 25, IS_Z1), (150, IS_Z1), YI, YI, ASHLAR, h=150, thick=25, coll_to=400, edges=edges,
    caps=(False, True))
lip(isl, (-150, IS_Z1), (IS_X0 + 25, IS_Z1), YI, YI, ASHLAR, h=150, thick=25, coll_to=400, edges=edges,
    caps=(True, False))
for (x, z) in COVER_B:
    isl.box(x - 50, z - 50, x + 50, z + 50, YI, YI + 110, WHITE, ROCK)
spots["cover_b"] = COVER_B
spots["islet_region"] = (-350, 160, 350, 450)
# rocks along the sea wall, out of every fight
for i, (x, z) in enumerate([(-640, -300), (-650, 0), (640, -420), (630, 60), (-300, -1240), (320, -1240)]):
    C.boulder(isl, x, z, isl_height(x, z), 40, 55, 100 + i, ROCK)

# the keeper's cottage: whitewashed, a slate gable roof, its door on the east side towards the path
cx0, cz0, cx1, cz1 = COTTAGE
CT, EAVE, RIDGE = 15.0, 260.0, 360.0
DOOR_C = (210.0, Y0, 300.0, Y0 + 170)         # in z (u), the door's opening
plane_rect(isl, "x", cx1, cz0, YI, cz1, EAVE, [DOOR_C], WHITE, (1, 0, 0))
plane_rect(isl, "x", cx0, cz0, YI, cz1, EAVE, [], WHITE, (-1, 0, 0))
plane_rect(isl, "z", cz0, cx0, YI, cx1, EAVE, [], WHITE, (0, -1, 0))
plane_rect(isl, "z", cz1, cx0, YI, cx1, EAVE, [], WHITE, (0, 1, 0))
plane_rect(isl, "x", cx1 - CT, cz0 + CT, Y0, cz1 - CT, EAVE - 10, [DOOR_C], WHITE, (-1, 0, 0))
plane_rect(isl, "x", cx0 + CT, cz0 + CT, Y0, cz1 - CT, EAVE - 10, [], WHITE, (1, 0, 0))
plane_rect(isl, "z", cz0 + CT, cx0 + CT, Y0, cx1 - CT, EAVE - 10, [], WHITE, (0, 1, 0))
plane_rect(isl, "z", cz1 - CT, cx0 + CT, Y0, cx1 - CT, EAVE - 10, [], WHITE, (0, -1, 0))
tiled(isl, cx0 + CT, cz0 + CT, cx1 - CT, cz1 - CT, Y0, DECK, size=100.0)
ceiling(isl, cx0 + CT, cz0 + CT, cx1 - CT, cz1 - CT, EAVE - 10, DARK, size=200.0)
# the door's jambs, threshold and lintel through the wall
isl.face([(cx1 - CT, DOOR_C[0], Y0), (cx1, DOOR_C[0], Y0), (cx1, DOOR_C[0], DOOR_C[3]), (cx1 - CT, DOOR_C[0], DOOR_C[3])],
         WHITE, (0, 1, 0))
isl.face([(cx1 - CT, DOOR_C[2], Y0), (cx1, DOOR_C[2], Y0), (cx1, DOOR_C[2], DOOR_C[3]), (cx1 - CT, DOOR_C[2], DOOR_C[3])],
         WHITE, (0, -1, 0))
isl.face([(cx1 - CT, DOOR_C[0], DOOR_C[3]), (cx1, DOOR_C[0], DOOR_C[3]), (cx1, DOOR_C[2], DOOR_C[3]),
          (cx1 - CT, DOOR_C[2], DOOR_C[3])], WHITE, (0, 0, -1))
tiled(isl, cx1 - CT, DOOR_C[0], cx1, DOOR_C[2], Y0, DECK, size=100.0)
# the gables and the roof (ridge along z), drawn outside only: a roof drawn both sides reads as a folded floor
for (zz, f) in ((cz0, (0, -1, 0)), (cz1, (0, 1, 0))):
    isl.face([(cx0, zz, EAVE), (cx1, zz, EAVE), ((cx0 + cx1) / 2, zz, RIDGE)], WHITE, f)
OV = 25.0
mx = (cx0 + cx1) / 2
for (xe, f) in ((cx0 - OV, (-1, 0, 1)), (cx1 + OV, (1, 0, 1))):
    ye = EAVE - OV * (RIDGE - EAVE) / (mx - cx0)
    isl.face([(xe, cz0 - OV, ye), (xe, cz1 + OV, ye), (mx, cz1 + OV, RIDGE), (mx, cz0 - OV, RIDGE)], SLATE, f)
for (zz, x, y) in ((cz0 - 4, -500, 140), (cz1 + 4, -500, 140)):
    f = (0, -1, 0) if zz < cz0 + 1 else (0, 1, 0)
    isl.face([(x - 22, zz, y), (x + 22, zz, y), (x + 22, zz, y + 54), (x - 22, zz, y + 54)], WINDOW, f,
             [(0, 0), (1, 0), (1, 1), (0, 1)])
isl.face([(cx0 - 4, 300, 140), (cx0 - 4, 200, 140), (cx0 - 4, 200, 194), (cx0 - 4, 300, 194)], WINDOW, (-1, 0, 0),
         [(0, 0), (1, 0), (1, 1), (0, 1)])
LAMPS.append((-500, 250, 200, 260, WARM))
spots["cottage"] = {"health": (-470, Y0, 180), "ammo": (-530, Y0, 180), "ammo2": (-470, Y0, 330),
                    "tribal": (-540, Y0, 330), "light": (-500, 220, 250)}
# the shed: an open-fronted lean-to (west side open) on the east of the islet
SX0, SZ0, SX1, SZ1 = 420.0, 200.0, 620.0, 400.0
isl.wall((SX1, SZ0), (SX1, SZ1), YI, YI, 240, 240, DARK, double=True)
isl.wall((SX0, SZ0), (SX1, SZ0), YI, YI, 200, 240, DARK, double=True)
isl.wall((SX0, SZ1), (SX1, SZ1), YI, YI, 200, 240, DARK, double=True)
isl.face([(SX0 - 20, SZ0 - 15, 196), (SX1 + 10, SZ0 - 15, 242), (SX1 + 10, SZ1 + 15, 242), (SX0 - 20, SZ1 + 15, 196)],
         SLATE, (-0.2, 0, 1))
spots["shed_crates"] = [(560, YI, 250), (560, YI, 340), (480, YI, 360)]
lantern(isl, -200, 470, YI, h=180)     # by the causeway's head
lantern(isl, 200, 470, YI, h=180)
lantern(isl, -150, -20, YI, h=180)     # either side of the tower door
lantern(isl, 150, -20, YI, h=180)
spots["tower_door"] = (0, Y0, -160)
spots["islet_lanterns"] = [(-200, 470), (200, 470), (-150, -20), (150, -20)]

# ================================================================================================ the tower's outside
for k in range(16):
    holes = []
    if k == 0:
        holes = [(-80, Y0, 80, Y0 + 170), (-80, YG2, 80, YG2 + 170), (-80, YK, 80, YK + 170)]
    elif k == 4:
        holes = [(-80, YL, 80, YL + 170)]
    elif k % 2 == 1:
        holes = [(-70, YL + 30, 70, YL + 220)]
    side_wall(tw, k, RA, YI, YTOP, holes, WHITE)
    if k == 4:
        side_wall(tw, k, RL, YL, YTOP, [(-80, YL, 80, YL + 170)], WHITE, inward=True)
        side_reveal(tw, k, -80, 80, YL, YL + 170, RL, RA, WHITE, sill=False)
    elif k % 2 == 1:
        side_wall(tw, k, RL, YL, YTOP, [(-70, YL + 30, 70, YL + 220)], WHITE, inward=True)
        side_reveal(tw, k, -70, 70, YL + 30, YL + 220, RL, RA, WHITE)
        for t in (-35, 0, 35):   # iron bars, a collider in the window's outer face (a grille)
            p = L(k, (RL + RA) / 2, t)
            post(props, p[0], p[1], 5, YL + 30, YL + 220, DARK, n=4, cap=False, phase=math.pi / 4)
        a, b = L(k, RA, -70), L(k, RA, 70)
        collider(edges, a, b, YL + 30, YL + 220)
    else:
        side_wall(tw, k, RL, YL, YTOP, [], WHITE, inward=True)
# the doorways through the south wall (180 deep): the tower door, the gallery door, the keeper's door
for y in (Y0, YG2, YK):
    reveal(tw, "z", IZ1, TZ + RA, -80, 80, y, 170, WHITE, FLAGS)
# the lamp room's ceiling and the roof
for k in range(16):
    a, b = V(RL, k - 1), V(RL, k)
    tw.face([(0, TZ, YTOP), (a[0], a[1], YTOP), (b[0], b[1], YTOP)], DARK, (0, 0, -1))
    a, b = V(RA, k - 1), V(RA, k)
    tw.face([(a[0], a[1], YTOP), (b[0], b[1], YTOP), (0, TZ, YTOP + 280)], SLATE, (*nrm(k)[:2], 1.0))
props.box(-14, TZ - 14, 14, TZ + 14, YTOP + 270, YTOP + 330, DARK)   # the vane's post
# lit windows on the outside (the stair and the keeper's floor)
for (k, y) in ((2, 230), (5, 290), (10, 300), (13, 310), (2, 1000), (6, 1010), (10, 1000), (14, 1010)):
    decal_side(props, k, 0, y, 40, 56, WINDOW)
# the lift cage out on the east side (side 4), its door through the lamp room's wall
CAGE_R, CAGE_T, CAGE_TOP = 700.0, 100.0, YL + 210
c4 = [L(4, RA, -CAGE_T), L(4, CAGE_R, -CAGE_T), L(4, CAGE_R, CAGE_T), L(4, RA, CAGE_T)]
tiled(tw, RA, TZ - CAGE_T, CAGE_R, TZ + CAGE_T, YL, METAL, size=100.0)
tiled(tw, RL, TZ - 80, RA, TZ + 80, YL, METAL, size=100.0)
tw.face([(p[0], p[1], YL - 20) for p in c4], DARK, (0, 0, -1))
tw.face([(p[0], p[1], CAGE_TOP) for p in c4], SLATE, (0, 0, 1))
tw.face([(p[0], p[1], CAGE_TOP - 16) for p in c4], DARK, (0, 0, -1))   # 16 under: closer reads as a fold
for (a, b) in ((c4[0], c4[1]), (c4[1], c4[2]), (c4[2], c4[3])):
    tw.wall(a, b, CAGE_TOP - 16, CAGE_TOP - 16, CAGE_TOP, CAGE_TOP, DARK,
            facing=((a[0] + b[0]) / 2 - 615, (a[1] + b[1]) / 2 - TZ, 0))
for (a, b) in ((c4[0], c4[1]), (c4[1], c4[2]), (c4[2], c4[3])):
    tw.wall(a, b, YL, YL, CAGE_TOP - 16, CAGE_TOP - 16, LATTICE, double=True)
    tw.wall(a, b, YL - 20, YL - 20, YL, YL, DARK, facing=((a[0] + b[0]) / 2 - 615, (a[1] + b[1]) / 2 - TZ, 0))
spots["lift_door"] = (515, YL, TZ)
spots["exit_on"] = (625, YL, TZ)
LAMPS.append((620, TZ, YL + 150, 220, COLD))
tw.build()

# ================================================================================================ C. the stairwell inside
# walls: the square inside, 50 to 1180 (the keeper's floor's ceiling), the south wall's three doorways
DOORS_S = [(-80, Y0, 80, Y0 + 170), (-80, YG2, 80, YG2 + 170), (-80, YK, 80, YK + 170)]
YC = YL - 20     # the keeper's floor's ceiling (the lamp room's floor's underside)
plane_rect(ins, "z", IZ1, IX0, Y0, IX1, YC, DOORS_S, WHITE, (0, -1, 0))
plane_rect(ins, "z", IZ0, IX0, YG1, IX1, YC, [], WHITE, (0, 1, 0))
plane_rect(ins, "x", IX1, -600, Y0, IZ1, YC, [], WHITE, (-1, 0, 0))
plane_rect(ins, "x", IX1, IZ0, YG1, -600, YC, [], WHITE, (-1, 0, 0))
plane_rect(ins, "x", IX0, -600, Y0, IZ1, YC, [], WHITE, (1, 0, 0))
plane_rect(ins, "x", IX0, IZ0, YG1, -600, YC, [], WHITE, (1, 0, 0))
# the walls round the lamp room's floor slot (1180..1200) where the stair comes up
strip(ins, (IX0, IZ0), (IX0, -560), YC, YC, YL, YL, WHITE, (1, 0, 0))
strip(ins, (IX0, IZ0), (210, IZ0), YC, YC, YL, YL, WHITE, (0, 1, 0))
# the ground floor (50) and R1 up the west wall (50 -> 220, solid), G1 the north half (220, solid)
R1 = (IX0, -600.0, -210.0, IZ1)
tiled(ins, -210, -600, IX1, IZ1, Y0, FLAGS, size=120.0)
tiled(ins, IX0, -600, -210, IZ1, YG1, FLAGS, Y0, along="z", size=110.0)
walls(ins, IX0, -600, -210, IZ1, Y0, lambda x, z: Y0 + (IZ1 - z) / (IZ1 + 600) * (YG1 - Y0), WHITE, which="e")
COVER_G1 = [(-230, -850), (-30, -850), (-130, -700), (90, -700)]   # stone blocks 80 x 80, 110 tall
cov_g1 = [(x - 40, z - 40, x + 40, z + 40) for x, z in COVER_G1]
for rr in C.rects_minus((IX0, IZ0, 210, -600), cov_g1):
    tiled(ins, *rr, YG1, FLAGS, size=120.0)
for (x, z) in COVER_G1:
    ins.box(x - 40, z - 40, x + 40, z + 40, YG1, YG1 + 110, WHITE, FLAGS)
strip(ins, (-210, -600), (IX1, -600), Y0, Y0, YG1, YG1, WHITE, (0, 1, 0))
lip(ins, (210, -600), (-210, -600), YG1, YG1, ASHLAR, h=100, thick=20, caps=(False, True))
spots["cover_g1"] = COVER_G1
spots["g1_region"] = (-330, -930, 190, -620)
# R2 up the east wall (220 -> 400, solid on G1), north to south
tiled(ins, 210, IZ0, IX1, -600, YG1, DECK, YG2, along="z", size=110.0)
walls(ins, 210, IZ0, 211, -600, YG1, lambda x, z: YG1 + (z - IZ0) / (-600 - IZ0) * (YG2 - YG1), WHITE, which="w")
strip(ins, (210, -600), (IX1, -600), YG1, YG1, YG2 - 20, YG2 - 20, WHITE, (0, 1, 0))
# G2: the south half slab at 400 (the gallery door), its underside the ground floor's ceiling
tiled(ins, IX0, -600, IX1, IZ1, YG2, FLAGS, size=120.0)
ceiling(ins, IX0, -600, IX1, IZ1, YG2 - 20, DARK, size=180.0)
strip(ins, (IX0, -600), (210, -600), YG2 - 20, YG2 - 20, YG2, YG2, FLAGS, (0, -1, 0))
lip(ins, (IX0, -600), (210, -600), YG2, YG2, ASHLAR, h=100, thick=20, caps=(False, True))
# the pulley over the north half-floor (the switch) and its rope across the stairwell to the gallery door
spots["switch"] = (0, 560, IZ0 + 12)
props.box(-3, IZ0 + 2, 3, IZ1 - 6, 600, 606, DARK)
props.box(-40, IZ0 + 2, 40, IZ0 + 8, 520, 600, DARK)
# the stair room's ceiling (the keeper's floor's underside)
ceiling(ins, IX0, IZ0, IX1, IZ1, YK - 20, DARK, size=200.0)
# the engine's cables up the walls
for (x, z, y0, y1) in ((IX1 - 10, -500, Y0, YK - 20), (IX1 - 10, -850, YG1, YK - 20), (-340, -780, YG1, YK - 20),
                       (IX1 - 10, -480, YK, YC), (IX1 - 10, -880, YK, YC), (100, IZ0 + 10, YK, YC)):
    post(props, x, z, 7, y0, y1, DARK, n=4, cap=False)
LAMPS += [(-100, -780, 420, 420, WARM), (100, -420, 230, 330, WARM), (0, -420, 600, 380, WARM)]

# ================================================================================================ E. the keeper's floor
# the stair to the lamp room: the foot landing (900) and a ramp up the west band (900 -> 1090, solid), the corner
# landing, a ramp along the north band (1090 -> 1200, solid); partitions shut it off from the hall
WB = -200.0      # the west band's east edge
NB = -800.0      # the north band's south edge
PA = (-200.0, NB, -160.0, IZ1)       # partition A (the lamp room door in it)
PB = (-160.0, NB, 210.0, -760.0)     # partition B
LDOOR = (-425.0, -265.0)             # the lamp room door's opening in partition A (z)
YW = 1090.0
COVER_K = [(-60, -620), (100, -620), (250, -620), (-60, -400), (100, -400), (250, -400)]
cov_k = [(x - 40, z - 40, x + 40, z + 40) for x, z in COVER_K]
for rr in C.rects_minus((IX0, IZ0, IX1, IZ1), [(IX0, IZ0, WB, -440.0), (WB, IZ0, 210.0, NB), PA, PB] + cov_k):
    tiled(ins, *rr, YK, DECK, size=120.0)
tiled(ins, IX0, NB, WB, -440, YW, DECK, YK, along="z", size=110.0)       # the west ramp
tiled(ins, IX0, IZ0, WB, NB, YW, DECK, size=100.0)                       # the corner landing
tiled(ins, WB, IZ0, 210, NB, YW, DECK, YL, along="x", size=110.0)        # the north ramp
strip(ins, (210, IZ0), (210, NB), YK, YK, YL, YL, WHITE, (1, 0, 0))      # its east end, the nook's west wall
for (x, z) in COVER_K:   # the keeper's sea chests and engine parts: blocks 80 x 80, 110 tall
    ins.box(x - 40, z - 40, x + 40, z + 40, YK, YK + 110, DARK, METAL)
# partition A: its hall face (x -160), its stair face (x -200, from 900 to 1200), the door's reveal
plane_rect(ins, "x", -160, -760, YK, IZ1, YC, [(LDOOR[0], YK, LDOOR[1], YK + 170)], WHITE, (1, 0, 0))
plane_rect(ins, "x", WB, NB, YK, IZ1, YL, [(LDOOR[0], YK, LDOOR[1], YK + 170)], WHITE, (-1, 0, 0))
reveal(ins, "x", WB, -160, LDOOR[0], LDOOR[1], YK, 170, WHITE, DECK)
# partition B: its hall face (z -760), its stair face (z -800), its east end (x 210, the nook)
plane_rect(ins, "z", -760, -160, YK, 210, YC, [], WHITE, (0, 1, 0))
plane_rect(ins, "z", NB, WB, YK, 210, YL, [], WHITE, (0, -1, 0))
strip(ins, (210, NB), (210, -760), YK, YK, YC, YC, WHITE, (1, 0, 0))
# the keeper's ceiling (the lamp room's floor's underside) less the slot over the stair
SLOT_W = (IX0, IZ0, WB, -560.0)
SLOT_N = (WB, IZ0, 210.0, NB)
for rr in C.rects_minus((IX0, IZ0, IX1, IZ1), [SLOT_W, SLOT_N, PA, PB]):
    ceiling(ins, *rr, YC, DARK, size=200.0)
strip(ins, (IX0, -560), (WB, -560), YC, YC, YL, YL, DARK, (0, -1, 0))     # the slab's edge over the stair's foot
# shelves in the nook (the storeroom): a long low chest along its north wall
ins.box(225, IZ0 + 2, 340, IZ0 + 42, YK, YK + 60, DARK, DECK)
spots["cover_k"] = COVER_K
spots["k_region"] = (-140, -740, 330, -270)
spots["lamp_door"] = (-180, YK, -345)
spots["stair_foot"] = {"health": (-300, YK, -300), "ammo": (-250, YK, -400)}
spots["nook"] = {"tribal": (280, YK, -880)}
spots["keeper_door"] = (0, YK, -160)
LAMPS += [(60, -500, 1100, 380, WARM), (280, -860, 1080, 200, WARM), (-275, -350, 1080, 220, WARM),
          (-275, -880, 1180, 260, WARM)]
ins.build()

# ================================================================================================ F. the lamp room
LR = mesh("lamp_room", uv=160.0)
ENGINE = (0.0, TZ)
COVER_F = [(230, -450), (-60, -330), (240, -680)]   # brass housings 90 x 90, 110 tall
cov_f = [(x - 45, z - 45, x + 45, z + 45) for x, z in COVER_F]
ENG_BOX = (-110.0, TZ - 110, 110.0, TZ + 110)
holes_f = [SLOT_W, SLOT_N, ENG_BOX] + cov_f
xs_f = [IX0, WB, 210.0, IX1] + [v for h in holes_f for v in (h[0], h[2])]
zs_f = [IZ0, NB, -560.0, IZ1] + [v for h in holes_f for v in (h[1], h[3])]
tile_flat(LR, ngon(RL), YL, FLAGS, (-RL / COS, TZ - RL / COS, RL / COS, TZ + RL / COS), xs_f, zs_f,
          skip=lambda a, b, c, d: in_rects(holes_f, a, b, c, d), step=130.0)
# balustrades round the slot (100, no collider: the drop onto the stair is under 240)
lip(LR, (IX0, IZ0), (IX0, -560), YL, YL, ASHLAR, h=100, thick=20, caps=(False, True))
lip(LR, (210, IZ0), (IX0 - 20, IZ0), YL, YL, ASHLAR, h=100, thick=20, caps=(True, False))
lip(LR, (IX0, -560), (WB, -560), YL, YL, ASHLAR, h=100, thick=20, caps=(True, True))
lip(LR, (WB, -560), (WB, NB), YL, YL, ASHLAR, h=100, thick=20, caps=(True, True))
lip(LR, (WB + 20, NB), (210, NB), YL, YL, ASHLAR, h=100, thick=20, caps=(False, True))
# the storm engine: a plinth, a brass drum with warning plates, the Stormglass on top, rods to the ceiling
LR.box(*ENG_BOX[:2], *ENG_BOX[2:], YL, YL + 40, METAL, METAL)
ring = [(ENGINE[0] + 100 * math.cos(k * math.tau / 8 + math.pi / 8), ENGINE[1] + 100 * math.sin(k * math.tau / 8 + math.pi / 8))
        for k in range(8)]
for k in range(8):
    a, b = ring[k], ring[(k + 1) % 8]
    LR.face([(a[0], a[1], YL + 40), (b[0], b[1], YL + 40), (b[0], b[1], YL + 140), (a[0], a[1], YL + 140)],
            WARN if k % 2 == 0 else METAL, ((a[0] + b[0]) / 2 - ENGINE[0], (a[1] + b[1]) / 2 - ENGINE[1], 0),
            [(0, 0), (1, 0), (1, 1), (0, 1)] if k % 2 == 0 else None)
LR.face([(p[0], p[1], YL + 140) for p in ring], METAL, (0, 0, 1))
gr = [(ENGINE[0] + 45 * math.cos(k * math.tau / 6), ENGINE[1] + 45 * math.sin(k * math.tau / 6)) for k in range(6)]
for k in range(6):
    a, b = gr[k], gr[(k + 1) % 6]
    mid = ((a[0] + b[0]) / 2 - ENGINE[0], (a[1] + b[1]) / 2 - ENGINE[1])
    LR.face([(a[0], a[1], YL + 200), (b[0], b[1], YL + 200), (ENGINE[0], ENGINE[1], YL + 290)], GLASS,
            (mid[0], mid[1], 0.6), [(0, 0), (1, 0), (0.5, 1)])
    LR.face([(a[0], a[1], YL + 200), (b[0], b[1], YL + 200), (ENGINE[0], ENGINE[1], YL + 140)], GLASS,
            (mid[0], mid[1], -0.6), [(0, 1), (1, 1), (0.5, 0)])
for k in range(4):
    a = k * math.tau / 4 + math.pi / 4
    post(props, ENGINE[0] + 80 * math.cos(a), ENGINE[1] + 80 * math.sin(a), 6, YL + 140, YTOP, DARK, n=4, cap=False)
for (x, z) in COVER_F:
    LR.box(x - 45, z - 45, x + 45, z + 45, YL, YL + 110, METAL, WARN)
spots["cover_f"] = COVER_F
spots["f_region"] = (-150, -760, 330, -250)
spots["tribal_f"] = (-440, YL, -760)
spots["engine"] = (0, YL, TZ)
LAMPS += [(0, TZ, YL + 250, 650, (0.3, 0.55, 1.0)), (0, TZ, YL + 250, 300, (0.25, 0.4, 0.7))]
LR.build()

# ================================================================================================ D. the gallery
ANG0 = 22.5   # a side's span


def b_deg(k):
    """The radial line at the start of side k."""
    return 22.5 * k - 11.25


def ring_ramp(m, k, a0, a1, h0, h1, mt, nu=2, nv=2):
    """Side k of the ring between apothems a0 and a1, rising h0 -> h1 along it: its top in small pieces, its
    underside, its outer edge."""
    IS, IE, OS, OE = V(a0, k - 1), V(a0, k), V(a1, k - 1), V(a1, k)

    def p(t, s):
        i = (IS[0] + (IE[0] - IS[0]) * t, IS[1] + (IE[1] - IS[1]) * t)
        o = (OS[0] + (OE[0] - OS[0]) * t, OS[1] + (OE[1] - OS[1]) * t)
        return (i[0] + (o[0] - i[0]) * s, i[1] + (o[1] - i[1]) * s)
    for i in range(nu):
        t0, t1 = i / nu, (i + 1) / nu
        y0, y1 = h0 + (h1 - h0) * t0, h0 + (h1 - h0) * t1
        for j in range(nv):
            s0, s1 = j / nv, (j + 1) / nv
            pts = [p(t0, s0), p(t1, s0), p(t1, s1), p(t0, s1)]
            ys = [y0, y1, y1, y0]
            m.face([(q[0], q[1], yy) for q, yy in zip(pts, ys)], mt, (0, 0, 1))
    under_edge(m, k, a0, a1, h0, h1)


def under_edge(m, k, a0, a1, h0, h1):
    IS, IE, OS, OE = V(a0, k - 1), V(a0, k), V(a1, k - 1), V(a1, k)
    m.face([(IS[0], IS[1], h0 - SLAB), (OS[0], OS[1], h0 - SLAB), (OE[0], OE[1], h1 - SLAB), (IE[0], IE[1], h1 - SLAB)],
           DARK, (0, 0, -1))
    m.face([(OS[0], OS[1], h0 - SLAB), (OE[0], OE[1], h1 - SLAB), (OE[0], OE[1], h1), (OS[0], OS[1], h0)], ASHLAR,
           nrm(k))


def lower_h(k):
    """The lower ring's heights at side k's start and end (sides 1-6: 400 -> 650)."""
    return YG2 + (YN - YG2) * (k - 1) / 6, YG2 + (YN - YG2) * k / 6


def upper_h(k):
    """Sides 10-14: 650 -> 900."""
    return YN + (YK - YN) * (k - 10) / 5, YN + (YK - YN) * (k - 9) / 5


TOWER_IN = ngon(RA)
# the lower landing (side 0, 400) outside the gallery door
tile_flat(gal, wedge(-11.25, 11.25) + ngon(RG), YG2, FLAGS, (-160, TZ + 500, 160, TZ + 780), [-80, 80],
          [TZ + RA], skip=lambda a, b, c, d: all_inside(TOWER_IN, a, b, c, d))
under_edge(gal, 0, RA, RG, YG2, YG2)
for k in range(1, 7):
    ring_ramp(gal, k, RA, RG, *lower_h(k), FLAGS)
# the north balcony (sides 7-9, 650, out to 900): the wardens' landing, three stone blocks on it
COVER_N = [(-125, -1250), (0, -1250), (125, -1250)]
cov_n = [(x - 40, z - 40, x + 40, z + 40) for x, z in COVER_N]
tile_flat(gal, wedge(146.25, 213.75) + ngon(RB), YN, FLAGS, (-560, TZ - 940, 560, TZ - 420),
          [v for h in cov_n for v in (h[0], h[2])], [v for h in cov_n for v in (h[1], h[3])] + [TZ - RA],
          skip=lambda a, b, c, d: all_inside(TOWER_IN, a, b, c, d) or in_rects(cov_n, a, b, c, d), step=125.0)
for k in (7, 8, 9):
    under_edge(gal, k, RA, RB, YN, YN)
for (x, z) in COVER_N:
    gal.box(x - 40, z - 40, x + 40, z + 40, YN, YN + 110, WHITE, FLAGS)
spots["cover_n"] = COVER_N
spots["n_region"] = [P(640, 146.25), P(918, 146.25), P(918, 213.75), P(640, 213.75)]
for k in range(10, 15):
    ring_ramp(gal, k, RA, RG, *upper_h(k), FLAGS)
# the south balcony (sides 15, 0, 1 at 900) over the door, the keeper's door into the tower
tile_flat(gal, wedge(-33.75, 33.75) + ngon(RG), YK, FLAGS, (-460, TZ + 380, 460, TZ + 780), [-80, 80], [TZ + RA],
          skip=lambda a, b, c, d: all_inside(TOWER_IN, a, b, c, d))
for k in (15, 0, 1):
    under_edge(gal, k, RA, RG, YK, YK)
spots["s_balcony"] = {"health": L(0, 640, -150), "ammo": L(0, 640, 150), "ammo2": L(15, 640, 0)}
# the slab's open ends: the north balcony's two sides, the south balcony's east end, the lower landing's west end


def slab_end(m, deg, r0, r1, y, toward):
    a, b = P(r0, deg), P(r1, deg)
    d = math.radians(deg)
    tn = (math.cos(d) * toward, -math.sin(d) * toward, 0)
    m.face([(a[0], a[1], y - SLAB), (b[0], b[1], y - SLAB), (b[0], b[1], y), (a[0], a[1], y)], ASHLAR, tn)


slab_end(gal, 146.25, RG / COS, RB / COS, YN, -1)
slab_end(gal, 213.75, RG / COS, RB / COS, YN, 1)
slab_end(gal, 33.75, RA / COS, RG / COS, YK, 1)
slab_end(gal, -11.25, RA / COS, RG / COS, YG2, -1)
# parapets at the open ends: the lower landing's west end (under the south balcony), the south balcony's east end
lip(gal, P(RG / COS - 8, -11.25), P(RA / COS + 4, -11.25), YG2, YG2, ASHLAR, h=150, thick=25, coll_to=460,
    edges=edges)
lip(gal, P(RA / COS + 4, 33.75), P(RG / COS - 8, 33.75), YK, YK, ASHLAR, h=150, thick=25, coll_to=400, edges=edges)
# the rails round the outer edge (150, posts 160 apart), a collider in their line up to 1,300
chain = []
for k in range(0, 7):
    chain.append((V(RG, k - 1), V(RG, k), *(lower_h(k) if k else (YG2, YG2)), edges))
chain.append((V(RG, 6), V(RB, 6), YN, YN, edges))
for k in (7, 8, 9):
    chain.append((V(RB, k - 1), V(RB, k), YN, YN, edges))
chain.append((V(RB, 9), V(RG, 9), YN, YN, edges))
for k in range(10, 15):
    chain.append((V(RG, k - 1), V(RG, k), *upper_h(k), edges))
chain.append((V(RG, 14), V(RG, 15), YK, YK, edges))
chain.append((V(RG, 15), V(RG, 0), YK, YK, spare))
chain.append((V(RG, 0), V(RG, 1), YK, YK, spare))
for i, (a, b, ya, yb, e) in enumerate(chain):
    fence(gal, e, a, b, ya, yb, DARK, h=150, every=160, coll=1300 - max(ya, yb), first=(i == 0))
# the lookouts' perches over the north balcony (sides 7 and 9, 880), and the broken balcony (side 12, a ledge)
for k in (7, 9):   # small (64 across): its own floor would stop the lookout's steep shots down onto the balcony
    lbox(gal, k, RA, 640, -32, 32, 850, 880, WHITE, FLAGS)
    spots[f"perch_{k}"] = (*L(k, 610, 0), 880)
    spots[f"flames_{k}"] = (*L(k, 555, 0), 880)
    LAMPS.append((*L(k, 600, 0), 940, 260, (0.6, 0.32, 0.1)))
BROKEN_Y = 915.0
lbox(gal, 12, RA, 640, -80, 80, BROKEN_Y - 30, BROKEN_Y, WHITE, LEDGE)
spots["tribal_broken"] = (*L(12, 590, 0), BROKEN_Y)
spots["midges_gallery"] = P(640, 78.75)
gal.build()

# ------------------------------------------------------------------------------------------------ the sea
far = Mesh("sea", [MATS[WATER]], coll, uv_size=6000.0)
SEA_IN = [(IS_X0, IS_Z0, IS_X1, IS_Z1), (-150, IS_Z1, 150, GZ0), (GX0, GZ0, GX1, GZ1)]


def sea_cuts(lo, hi, inner, edges_):
    out = sorted({lo, hi} | {v for v in range(-12000, 12001, 6000) if lo < v < hi} | {v for v in edges_ if lo < v < hi})
    fine = []
    for p, q in zip(out, out[1:]):
        n = max(1, math.ceil((q - p) / 600)) if inner[0] <= p and q <= inner[1] else 1
        fine += [p + (q - p) * k / n for k in range(n)]
    return fine + [hi]


ex = sea_cuts(-12000, 12000, (-2400, 2400), [-2400, IS_X0, GX0, -150, 150, GX1, IS_X1, 2400])
ez = sea_cuts(-12000, 12000, (-2400, 2700), [-2400, IS_Z0, IS_Z1, GZ0, GZ1, 2700])
for i in range(len(ex) - 1):
    for j in range(len(ez) - 1):
        cx_, cz_ = (ex[i] + ex[i + 1]) / 2, (ez[j] + ez[j + 1]) / 2
        if any(r[0] < cx_ < r[2] and r[1] < cz_ < r[3] for r in SEA_IN):
            continue
        far.face([(ex[i], ez[j], SEA), (ex[i + 1], ez[j], SEA), (ex[i + 1], ez[j + 1], SEA), (ex[i], ez[j + 1], SEA)],
                 0, (0, 0, 1))
far.build()

for m in (isl, props, edges):
    m.build()

# ------------------------------------------------------------------------------------------------ light: the storm
level = [o for o in coll.all_objects if o.type == "MESH"]
SUN_DIR = (0.35, -0.25, -0.9)   # high and grey, from the south-west (Blender space: the light's travel)


def extra(x, z, y, mname):
    if mname.startswith("lit_window"):
        return (2.2, 2.0, 1.6)
    if mname.startswith("storm_glass"):
        return (2.6, 2.6, 2.8)
    if mname.startswith("warning_plate"):
        return (1.4, 1.4, 1.5)
    inside_tower = IX0 - 1 < x < IX1 + 1 and IZ0 - 1 < z < IZ1 + 1 and Y0 - 1 < y < YL - 1
    if inside_tower:
        return (0.8, 0.8, 0.85)
    if y > YL - 1 and math.hypot(x, z - TZ) < RL + 1:
        return (0.85, 0.95, 1.2)   # the lamp room: the engine's cold glow
    return (1.0, 1.0, 1.0)


TINTS = {"game_0715": (0.88, 0.9, 0.95), "game_0AC0": (0.82, 0.84, 0.88), "game_16DF": (0.9, 0.9, 0.95),
         "game_1958": (0.85, 0.88, 0.9)}
C.bake(level, SUN_DIR, (0.45, 0.5, 0.6), (0.2, 0.25, 0.32), tints=TINTS, lamps=LAMPS, extra=extra,
       soft={"game_1958": (0.5, 0.3), "game_0AC0": (0.5, 0.3), "game_08A8": (0.5, 0.3)})
sea = bpy.data.objects["sea"].data
scol = sea.color_attributes.get("Col") or sea.color_attributes.new("Col", "BYTE_COLOR", "CORNER")
for d in scol.data:
    d.color_srgb = (0.42, 0.5, 0.58, 1.0)

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
print("STORMSPIRE", json.dumps(report, default=str))
print("PARTS", json.dumps({o.name: sum(len(p.vertices) - 2 for p in o.data.polygons) for o in level}))
