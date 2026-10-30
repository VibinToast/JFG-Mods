"""Sunwreck Beach (Corsair Reach 1.1): builds the level from nothing and exports blender/out/sunwreck.glb.

Run in Blender 5.2 with jfg64 0.6.0+, after JFG-Studio has built its catalog once (the game's textures):
    blender --background --factory-startup --addons jfg64 --python sunwreck.py
Then in JFG-Studio: reimport_geometry (or import the .glb) into the level `sunwreck`.

Game coordinates throughout (x east, z south, y up); DESIGN.md has the plan this follows.
"""
import json
import math
import os
import sys

import bpy

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import common as C  # noqa: E402
from common import G, Mesh, smooth  # noqa: E402
import jfg64  # noqa: E402

NAME = "sunwreck"
scene, coll = C.new_scene(NAME)

# ------------------------------------------------------------------------------------------------ materials
SAND = C.game(0x185E)
GRASS = C.game(0x195F)
CLIFF = C.game(0x0C40)
STONE = C.game(0x195A)
PATH = C.game(0x1959)
HULL = C.game(0x16DB)
PLANK = C.game(0x193D)
CHAR = C.game(0x193D, name="charred_193D")
THATCH = C.game(0x0000)
WEAVE = C.game(0x0BE9)
BURNT = C.game(0x0BE9, name="charred_0BE9")
CRATE = C.game(0x0A39)
TRUNK = C.game(0x1351)
LEAF = C.game(0x195F, name="leaf_195F")  # solid: decoration that isn't solid can't share a piece with water
WATER = C.game(0x0DED, "water")
EDGE = jfg64.boundary_material()


def flag_px(x, y):
    """The corsairs' flag: a skull over crossed oars, bone white on black."""
    cx, cy = 15.5, 12.0
    dx, dy = x - cx, y - cy
    skull = (dx * dx) / 36 + (dy * dy) / 30 <= 1.0 or (abs(dx) <= 4 and 14 <= y <= 18)
    eye = ((x - 13) ** 2 + (y - 11) ** 2 <= 2.2) or ((x - 18) ** 2 + (y - 11) ** 2 <= 2.2)
    oar = any(abs((y - 25) - k * (x - 15.5)) <= 1.1 and 4 <= x <= 27 for k in (0.55, -0.55))
    blade = any(abs(x - bx) <= 2 and abs(y - by) <= 1.6 for bx, by in ((4, 19), (27, 19), (4, 31), (27, 31)))
    if (skull and not eye) or oar or blade:
        return (0.92, 0.88, 0.78)
    frayed = (x * 7 + y * 13) % 11 == 0
    return (0.05, 0.05, 0.06) if not frayed else (0.12, 0.1, 0.1)


def sign_px(x, y):
    """A painted warning board: weathered planks with a red cross and a white bar."""
    plank = (y // 8) % 2
    base = (0.45, 0.32, 0.2) if plank else (0.4, 0.28, 0.17)
    grain = ((x * 3 + y * 5) % 7) * 0.012
    col = tuple(c + grain for c in base)
    if abs(x - y) <= 2 or abs(x + y - 31) <= 2:
        if 4 <= x <= 27:
            col = (0.75, 0.12, 0.08)
    if y in (2, 3, 28, 29) and 3 <= x <= 28:
        col = (0.85, 0.82, 0.74)
    return col


FLAG = C.own_material("corsair_flag", C.own_image("corsair_flag", 32, 32, flag_px))
SIGN = C.own_material("warning_sign", C.own_image("warning_sign", 32, 32, sign_px))


TINTS = {
    "charred_193D": (0.34, 0.3, 0.28),
    "charred_0BE9": (0.3, 0.27, 0.25),
    "game_16DB": (0.9, 0.82, 0.74),
    "game_0C40": (0.95, 0.9, 0.86),
    "game_195A": (0.98, 0.95, 0.9),
    "leaf_195F": (0.8, 1.05, 0.7),
}

spots = {}  # positions Studio needs (game coords), written to out/sunwreck_spots.json

# ------------------------------------------------------------------------------------------------ the hull frame
HS, HB = (700.0, -250.0), (-150.0, -650.0)  # stern and bow on the ground (x, z)
HL = math.hypot(HB[0] - HS[0], HB[1] - HS[1])
HD = ((HB[0] - HS[0]) / HL, (HB[1] - HS[1]) / HL)
HP = (-HD[1], HD[0])  # across the hull, towards its north side (w > 0)
assert HP[1] < 0


def hfloor(u):
    return 2.0 + 118.0 * u / HL  # 2 over the sand at the stern: no floor lying in the beach's plane


def hpt(u, w, v):
    """A hull-frame point: u along from the stern, w across (north side positive), v over the floor there."""
    return (HS[0] + HD[0] * u + HP[0] * w, HS[1] + HD[1] * u + HP[1] * w, hfloor(u) + v)


def hull_local(x, z):
    dx, dz = x - HS[0], z - HS[1]
    return dx * HD[0] + dz * HD[1], dx * HP[0] + dz * HP[1]


# ------------------------------------------------------------------------------------------------ the ground

def inside(x, z, xa, xb, za, zb):
    return xa <= x <= xb and za <= z <= zb


def rect_w(x, z, xa, xb, za, zb, feather):
    dx = max(xa - x, 0.0, x - xb)
    dz = max(za - z, 0.0, z - zb)
    return 1.0 - smooth(math.hypot(dx, dz) / feather)


def mix(a, b, w):
    return a * (1 - w) + b * w


def H(x, z):
    h = 0.0
    # south-west sand mounds
    h = mix(h, 18 + 14 * math.sin(x / 230.0) * math.cos(z / 190.0), rect_w(x, z, -1700, -100, 900, 1380, 250))
    # the burnt village: two low terraces, 20 in the east rising to 60 in the west
    hv = 20 + 40 * smooth((-750 - x) / 700.0)
    h = mix(h, hv, rect_w(x, z, -1600, -700, 150, 850, 250))
    # the dunes, with the camp, the bow's landing and the path onto the cliff levelled
    hd = 100 + 28 * math.sin(x / 260.0 + 1.0) * math.sin(z / 210.0) + 10 * math.cos(x / 120.0 + z / 170.0)
    hd = min(140.0, max(70.0, hd))
    for (cx, cz, r, lv) in ((-1000, -720, 240, 140), (-150, -650, 150, 118), (-150, -860, 160, 136)):
        hd = mix(hd, lv, 1 - smooth((math.hypot(x - cx, z - cz) - r) / 120.0))
    h = mix(h, hd, rect_w(x, z, -1400, -50, -900, -250, 260))
    # the sea: a hollow from the shore down to -60, a reef, open water beyond to the edge
    if z > -880:
        shore = 1000 + 70 * math.sin(z / 420.0)
        h = mix(h, -60.0, smooth((x - shore) / 380.0))
    # the south cliff, with the tide-pool cove cut into it
    cove = inside(x, z, 1080, 1420, 1230, 1430)
    if cove:
        h = -40.0 if z < 1350 else 0.0  # wade in, a dry flat at the back
    elif z > 1380:
        h = mix(h, 400.0, smooth((z - 1380) / 120.0))
    # the west cliff
    if x < -1750:
        h = mix(h, 450.0, smooth((-1750 - x) / 120.0))
    # the headland: under the cliff path's blocks, its cliffs, the spire shelf, the gate passage, the notch
    if inside(x, z, -260, 1210, -1700, -910):
        h = 60.0
    if x < -280 and z < -920:
        h = 520.0
    if z <= -1690:
        h = 650.0
        if 960 <= x <= 1240:
            h = 420.0 if z >= -1810 else 150.0
    if 1240 < x <= 1650 and -1690 < z < -1440:
        h = 60.0  # under the gate passage's blocks
    if 1200 <= x <= 1560 and -1440 <= z <= -900:
        h = 230.0
    if x > 1560 and -1440 <= z < -700:
        h = -60.0
    # the cove between the hull and the cliff path: low sand
    if inside(x, z, 150, 950, -900, -300):
        h = mix(h, 20.0, 0.8)
    # the reef: a ridge of rock along x 1800 from the headland to the south cliff, too steep to climb, so the
    # level's edge behind it is never reached (an invisible wall in open water stood out: owner's play-test)
    if 1750 <= x <= 1850 and -1330 <= z <= 1500:
        h = 120 + 35 * math.sin(z / 230.0) + 15 * math.sin(z / 71.0)
    # under the hull and its cabin: below the plank floor, the hull's skin reaching into the sand
    u, w = hull_local(x, z)
    if 20 < u < HL - 20 and (-150 < w < 165 or (200 < u < 430 and -345 < w <= -150)):
        h = min(h, hfloor(u) - 12)
    return h


def ground_mat(x, z, y, slope):
    if slope > 38 or y > 300:
        return 2  # cliff rock
    if 85 < y < 160 and slope < 22 and x < -50 and z < -200:
        return 1  # grass on the dune tops
    return 0  # sand


def under_blocks(x, z):
    """Grid squares wholly under the cliff path's blocks and the gate passage: left out, so a fall never lands on
    hidden ground inside them."""
    return (inside(x, z, -210, 1160, -1650, -960) or inside(x, z, 1290, 1600, -1640, -1490))


ground = C.heightfield("ground", coll, -2000, -1900, 2000, 1500, 100.0, H, ground_mat, [SAND, GRASS, CLIFF],
                       boundary=420.0, flat_angle=1.2, merge_above=440.0, skip=under_blocks)
spots["ground_tris"] = len(ground.data.polygons)

# ------------------------------------------------------------------------------------------------ the sea
sea = Mesh("sea", [WATER], coll, uv_size=1024.0)
C.water_surface(sea, H, -2000, -1900, 2000, 1500, 100.0, -20.0, merge=2)  # cut along the shore, never under the sand
sea.build()
far = Mesh("sea_far", [WATER], coll, uv_size=6000.0)  # far away: few texture repeats, few cuts
# the open sea from the level's edge out to the horizon (it stopped short, and black showed past it)
# in squares that grow with distance: near the level small (a big triangle's box meets every collision query near
# it and fills the hero's list, decomp MSR 15), far out large
def far_sea(xa, xb, za, zb, y):
    edges_x = [xa]
    while edges_x[-1] < xb:
        d = min(abs(edges_x[-1]), abs(edges_x[-1] - 2000))
        edges_x.append(min(xb, edges_x[-1] + (1000 if d < 1500 else 6000)))
    edges_z = [za]
    while edges_z[-1] < zb:
        d = min(abs(edges_z[-1] + 1900), abs(edges_z[-1] - 1500))
        edges_z.append(min(zb, edges_z[-1] + (1000 if d < 1500 else 6000)))
    for i in range(len(edges_x) - 1):
        for j in range(len(edges_z) - 1):
            a0, a1, b0, b1 = edges_x[i], edges_x[i + 1], edges_z[j], edges_z[j + 1]
            far.face([(a0, b0, y), (a1, b0, y), (a1, b1, y), (a0, b1, y)], 0, (0, 0, 1))


far_sea(2000, 14000, -2000, 12000, -20)
far_sea(-4000, 2000, 1500, 12000, -20)
far_sea(600, 14000, -14000, -2000, -60)
far.build()

# ------------------------------------------------------------------------------------------------ the beached hull
SECTION = [(150, -25), (165, 80), (135, 185), (60, 245), (-40, 255), (-125, 205), (-160, 100), (-150, -25)]
STATIONS = [(0, 0.92), (180, 1.0), (420, 1.0), (650, 0.95), (820, 0.8), (HL, 0.62)]
HOLES = {(1, 3), (3, 4), (3, 3)}  # (station pair, section segment): broken planks the sun shines through
CABIN = (220.0, 400.0)  # u range of the captain's cabin, off the hold's south side

hull = Mesh("hull", [HULL, PLANK, CRATE], coll, uv_size=160.0)
for k in range(len(STATIONS) - 1):
    (u0, s0), (u1, s1) = STATIONS[k], STATIONS[k + 1]
    for i in range(len(SECTION) - 1):
        if (k, i) in HOLES:
            continue
        if k == 1 and i in (5, 6):  # the cabin's opening
            continue
        (w0, v0), (w1, v1) = SECTION[i], SECTION[i + 1]
        quad = [hpt(u0, w0 * s0, v0 * s0), hpt(u0, w1 * s0, v1 * s0), hpt(u1, w1 * s1, v1 * s1), hpt(u1, w0 * s1, v0 * s1)]
        mid_w, mid_v = (w0 + w1) / 2, (v0 + v1) / 2 - 110  # outward from the section's middle
        out = (HP[0] * mid_w, HP[1] * mid_w, mid_v)
        hull.face(quad, 0, out)
        t0, t1 = s0 * 0.94, s1 * 0.94  # the inside skin, a plank's thickness in
        inner = [hpt(u0, w0 * t0, v0 * t0), hpt(u0, w1 * t0, v1 * t0), hpt(u1, w1 * t1, v1 * t1), hpt(u1, w0 * t1, v0 * t1)]
        hull.face(inner, 0, (-out[0], -out[1], -out[2]))
# the ribs: strips round the inside, seen through the holes and in the hold
for ur in (110, 300, 540, 740):
    s = 1.0 if ur < 650 else 0.9
    for i in range(len(SECTION) - 1):
        if (ur, i) in ((740, 3), (740, 4), (300, 3)):
            continue  # broken away with the planks over it
        (w0, v0), (w1, v1) = SECTION[i], SECTION[i + 1]
        a = [hpt(ur - 9, w0 * s * 0.88, v0 * s * 0.9), hpt(ur - 9, w1 * s * 0.88, v1 * s * 0.9),
             hpt(ur + 9, w1 * s * 0.88, v1 * s * 0.9), hpt(ur + 9, w0 * s * 0.88, v0 * s * 0.9)]
        mid_w, mid_v = (w0 + w1) / 2, (v0 + v1) / 2 - 110
        hull.face(a, 0, (-HP[0] * mid_w, -HP[1] * mid_w, -mid_v))  # facing into the hold
# the plank floor, tilted from the stern (0) to the bow (120)
for k in range(len(STATIONS) - 1):
    (u0, s0), (u1, s1) = STATIONS[k], STATIONS[k + 1]
    # in pieces about 80 long and 100 across: no big floor triangles (see common.heightfield)
    nu = max(1, math.ceil((u1 - u0) / 80))
    for a in range(nu):
        ua, ub = u0 + (u1 - u0) * a / nu, u0 + (u1 - u0) * (a + 1) / nu
        sa, sb = s0 + (s1 - s0) * a / nu, s0 + (s1 - s0) * (a + 1) / nu
        for wa, wb in ((-148, -50), (-50, 50), (50, 148)):
            hull.face([hpt(ua, wa * sa, 0), hpt(ub, wa * sb, 0), hpt(ub, wb * sb, 0), hpt(ua, wb * sa, 0)], 1, (0, 0, 1))


def hbox(m, u0, u1, w0, w1, v0, v1, mat, both=False):
    """A block in the hull's frame (its top follows the floor's slope)."""
    c = [hpt(u, w, v) for u in (u0, u1) for w in (w0, w1) for v in (v0, v1)]
    # c index: u*4 + w*2 + v
    faces = [((0, 2, 6, 4), None), ((1, 5, 7, 3), (0, 0, 1)), ((0, 4, 5, 1), "w0"), ((2, 3, 7, 6), "w1"),
             ((0, 1, 3, 2), "u0"), ((4, 6, 7, 5), "u1")]
    for idx, want in faces:
        pts = [c[i] for i in idx]
        if want is None:
            continue
        if isinstance(want, str):
            sign = -1 if want.endswith("0") else 1
            if want[0] == "u":
                want = (HD[0] * sign, HD[1] * sign, 0)
            else:
                want = (HP[0] * sign, HP[1] * sign, 0)
        if both:
            m.quad2(pts, mat)
        else:
            m.face(pts, mat, want)


# the deck rail along the north side, reached up two fallen cargo crates (steps of 65)
hbox(hull, 520, 800, 62, 118, -20, 110, 1)  # inside the hull's skin there
r0, r1, rw0, rw1 = 560.0, 740.0, 10.0, 62.0  # u along, w across; up from the floor (0) to the rail (110)
rtop = [hpt(r0, rw0, 0), hpt(r1, rw0, 110), hpt(r1, rw1, 110), hpt(r0, rw1, 0)]
hull.face(rtop, 1, (0, 0, 1))
hull.face([hpt(r0, rw0, -10), hpt(r1, rw0, -10), hpt(r1, rw0, 110)], 2, (-HP[0], -HP[1], 0))
hull.face([hpt(r1, rw0, -10), hpt(r1, rw1, -10), hpt(r1, rw1, 110), hpt(r1, rw0, 110)], 2, (HD[0], HD[1], 0))
# the open sea chest on the rail (the gate key goes in it)
hbox(hull, 740, 772, 66, 96, 110, 130, 1)
lid = [hpt(740, 96, 130), hpt(772, 96, 130), hpt(772, 104, 156), hpt(740, 104, 156)]
hull.face(lid, 1, (-HP[0], -HP[1], 0.5))
spots["key"] = hpt(690, 82, 110)
spots["chest_open"] = hpt(756, 80, 132)
# fallen barrels and a crate in the hold: cover for the skitterers
hbox(hull, 300, 360, -110, -40, -20, 95, 2)
# the captain's cabin: a deckhouse lying off the south side
cab = (CABIN[0], CABIN[1])
CY = hfloor((cab[0] + cab[1]) / 2)  # the cabin's own floor, level


def cpt(u, w, y):
    p = hpt(u, w, 0)
    return (p[0], p[1], y)


def cbox(u0, u1, w0, w1, y0, y1, mat):
    c = [cpt(u, w, y) for u in (u0, u1) for w in (w0, w1) for y in (y0, y1)]
    hull.face([c[1], c[5], c[7], c[3]], mat, (0, 0, 1))
    for idx, want in (((0, 4, 5, 1), (HP[0] * -1, HP[1] * -1, 0)), ((2, 3, 7, 6), (HP[0], HP[1], 0)),
                      ((0, 1, 3, 2), (-HD[0], -HD[1], 0)), ((4, 6, 7, 5), (HD[0], HD[1], 0))):
        hull.face([c[i] for i in idx], mat, want)


for (u0, u1, w0, w1) in ((cab[0], cab[1], -330, -320), (cab[0], cab[0] + 10, -318, -150), (cab[1] - 10, cab[1], -318, -150)):
    cbox(u0, u1, w0, w1, CY - 30, CY + 197, 1)  # just under the roof: no faces in one plane
hull.face([cpt(cab[0], -150, CY + 208), cpt(cab[1], -150, CY + 208), cpt(cab[1], -330, CY + 208), cpt(cab[0], -330, CY + 208)], 0, (0, 0, 1))
hull.face([cpt(cab[0], -150, CY + 200), cpt(cab[1], -150, CY + 200), cpt(cab[1], -330, CY + 200), cpt(cab[0], -330, CY + 200)], 0, (0, 0, -1))
hull.face([cpt(cab[0], -150, CY), cpt(cab[0], -330, CY), cpt(cab[1], -330, CY), cpt(cab[1], -150, CY)], 1, (0, 0, 1))
spots["tribal_cabin"] = hpt((cab[0] + cab[1]) / 2, -260, 0)
spots["stern"] = hpt(-60, 0, 0)
spots["hold_bow"] = hpt(820, 0, 0)
spots["hold_mid"] = hpt(420, 0, 0)
spots["hold_beams"] = [hpt(300, 0, 245), hpt(560, 0, 250)]
# the broken mainmast, fallen on the sand by the stern, its crow's nest split open
hull.obox(930, -40, 260, 14, 28, H(930, -40) - 4, H(930, -40) + 24, 0)
hull.obox(1140, 70, 40, 40, 28, H(1140, 70) - 10, H(1140, 70) + 45, 1)
hull_obj = hull.build()

# ------------------------------------------------------------------------------------------------ the village
vil = Mesh("village", [WEAVE, BURNT, THATCH, HULL, PLANK, CHAR], coll, uv_size=128.0)


def hut(cx, cz, yaw, burnt, seed):
    gy = H(cx, cz)
    deck = gy + 40
    vil.obox(cx, cz, 115, 115, yaw, gy - 25, deck, 5 if burnt else 4)
    c, s = math.cos(math.radians(yaw)), math.sin(math.radians(yaw))

    def p(a, b):
        return (cx + a * c + b * s, cz - a * s + b * c)
    corners = [p(-100, -100), p(100, -100), p(100, 100), p(-100, 100)]
    mat = 1 if burnt else 0
    rnd = [(seed * 37 + k * 53) % 100 / 100.0 for k in range(8)]
    for i in range(4):
        a, b = corners[i], corners[(i + 1) % 4]
        if burnt and rnd[i] < 0.3:
            continue  # this wall burnt away
        top_a = deck + (170 if not burnt else 60 + 110 * rnd[i])
        top_b = deck + (170 if not burnt else 60 + 110 * rnd[i + 4])
        if i == 3:  # the door side: a gap 80 wide in the middle
            m1 = ((a[0] * 0.6 + b[0] * 0.4), (a[1] * 0.6 + b[1] * 0.4))
            m2 = ((a[0] * 0.4 + b[0] * 0.6), (a[1] * 0.4 + b[1] * 0.6))
            vil.wall(a, m1, deck, deck, top_a, top_a, mat, double=True)
            vil.wall(m2, b, deck, deck, top_b, top_b, mat, double=True)
            if not burnt:
                vil.wall(m1, m2, deck + 130, deck + 130, top_a, top_b, mat, double=True)
        else:
            vil.wall(a, b, deck, deck, top_a, top_b, mat, double=True)
    if not burnt:
        apex = (cx, cz, deck + 290)
        eaves = [p(-130, -130), p(130, -130), p(130, 130), p(-130, 130)]
        for i in range(4):
            a, b = eaves[i], eaves[(i + 1) % 4]
            vil.face([(a[0], a[1], deck + 160), (b[0], b[1], deck + 160), apex], 2, ((a[0] + b[0]) / 2 - cx, (a[1] + b[1]) / 2 - cz, 1))
            under = (apex[0], apex[1], apex[2] - 10)
            vil.face([(b[0], b[1], deck + 152), (a[0], a[1], deck + 152), under], 2, (cx - (a[0] + b[0]) / 2, cz - (a[1] + b[1]) / 2, -1))
    else:
        # a charred roof beam fallen across
        vil.obox(cx + 20, cz - 10, 120, 9, yaw + 30, deck, deck + 18, 5)
    return deck


HUTS = [(-1500, 250, 10, False), (-1520, 560, 35, True), (-1420, 840, 5, True), (-900, 880, -15, True)]
for n, (hx, hz, hyaw, burnt) in enumerate(HUTS):
    d = hut(hx, hz, hyaw, burnt, n + 3)
    if not burnt:
        spots["tribal_hut"] = (hx, hz, d)
        # steps up to the door (west side): 20 and 40
        c, s = math.cos(math.radians(hyaw)), math.sin(math.radians(hyaw))
        bx, bz = hx - 140 * c, hz + 140 * s
        vil.obox(bx, bz, 30, 45, hyaw, H(bx, bz) - 25, d - 20, 4)
# overturned boats (cover): prisms of planks
for (bx, bz, byaw) in ((-980, 400, 70), (-760, 180, -20), (-1640, 760, 40)):
    gy = H(bx, bz)
    c, s = math.cos(math.radians(byaw)), math.sin(math.radians(byaw))

    def bp(a, b, y):
        return (bx + a * c + b * s, bz - a * s + b * c, y)
    L2, W2 = 120, 55
    ridge0, ridge1 = bp(-L2, 0, gy + 95), bp(L2, 0, gy + 95)
    for side in (-1, 1):
        a0, a1 = bp(-L2 + 20, side * W2, gy - 10), bp(L2 - 20, side * W2, gy - 10)
        vil.face([a0, a1, ridge1, ridge0], 3, (s * side, c * side, 0.6))
    vil.face([bp(-L2 + 20, -W2, gy - 10), bp(-L2 + 20, W2, gy - 10), ridge0], 3, (-c, s, 0))
    vil.face([bp(L2 - 20, W2, gy - 10), bp(L2 - 20, -W2, gy - 10), ridge1], 3, (c, -s, 0))
vil.build()

# ------------------------------------------------------------------------------------------------ the camp on the dunes
camp = Mesh("camp", [CRATE, CHAR, FLAG], coll, uv_size=96.0)
CRATES = [(-1180, -820), (-880, -880), (-1080, -560), (-820, -640)]
for (cx, cz) in CRATES:
    gy = H(cx, cz)
    camp.box(cx - 50, cz - 50, cx + 50, cz + 50, gy - 20, gy + 105, 0)
# the cookfire's logs (the flames are the game's object, placed in Studio) and the corsair flag on a pole
fy = H(-1000, -720)
camp.obox(-1000, -720, 45, 8, 20, fy - 4, fy + 12, 1)
camp.obox(-1000, -720, 45, 8, 110, fy + 2, fy + 18, 1)
camp.box(-1215, -905, -1205, -895, fy - 10, fy + 330, 1)
C.decal(camp, [(-1205, -900, fy + 230), (-1065, -900, fy + 230), (-1065, -900, fy + 325), (-1205, -900, fy + 325)], 2)
spots["campfire"] = (-1000, -720, fy)
camp.build()

# ------------------------------------------------------------------------------------------------ the cliff path
cliff = Mesh("cliffpath", [PATH, CLIFF, STONE, PLANK, SIGN, FLAG], coll, uv_size=200.0)
LEGS = [  # (x0, x1, z centre, y at x0, y at x1): three legs 250 wide, two switchbacks
    (-250, 950, -1050, 140, 240),
    (0, 950, -1300, 350, 270),
    (0, 950, -1550, 360, 420),
]


def strip(x0, x1, za, zb, ya, yb, along="x"):
    """A walkable block from x0 to x1 (za..zb across), its top from ya to yb along `along`, walls down to 40."""
    def hy(x, z):
        if along == "x":
            return ya + (yb - ya) * (x - x0) / (x1 - x0)
        return ya + (yb - ya) * (z - za) / (zb - za)
    # the top in squares of about 100: big floor triangles let the hero fall through (see common.heightfield)
    nxs = max(1, math.ceil(abs(x1 - x0) / 130))
    nzs = max(1, math.ceil(abs(zb - za) / 130))
    for a in range(nxs):
        u0, u1 = x0 + (x1 - x0) * a / nxs, x0 + (x1 - x0) * (a + 1) / nxs
        for b in range(nzs):
            v0, v1 = za + (zb - za) * b / nzs, za + (zb - za) * (b + 1) / nzs
            cliff.face([(u0, v1, hy(u0, v1)), (u1, v1, hy(u1, v1)), (u1, v0, hy(u1, v0)), (u0, v0, hy(u0, v0))], 0,
                       (0, 0, 1))
    base = -70
    # the walls 3 in from the top's edges: a neighbouring block's wall in the same place flickered (play-test)
    xa, xb = min(x0, x1) + 3, max(x0, x1) - 3
    za, zb = za + 3, zb - 3
    cliff.face([(xa, zb, base), (xb, zb, base), (xb, zb, hy(xb, zb)), (xa, zb, hy(xa, zb))], 1, (0, 1, 0))
    cliff.face([(xb, za, base), (xa, za, base), (xa, za, hy(xa, za)), (xb, za, hy(xb, za))], 1, (0, -1, 0))
    cliff.face([(xb, zb, base), (xb, za, base), (xb, za, hy(xb, za)), (xb, zb, hy(xb, zb))], 1, (1, 0, 0))
    cliff.face([(xa, za, base), (xa, zb, base), (xa, zb, hy(xa, zb)), (xa, za, hy(xa, za))], 1, (-1, 0, 0))


for (x0, x1, zc, y0, y1) in LEGS:
    strip(x0, x1, zc - 125, zc + 125, y0, y1)
# switchback 1 (east, leg 1 -> leg 2) and 2 (west, leg 2 -> leg 3)
strip(950, 1200, -1425, -925, 270, 240, along="z")
strip(-250, 0, -1675, -1175, 360, 350, along="z")
# the gate landing
strip(950, 1250, -1675, -1425, 420, 420)


def lip(a, b, ya, yb, height=150, thick=26, collider=420):
    """A rock parapet along a -> b on a path whose floor is ya..yb there, with a collider rising above it."""
    dx, dz = b[0] - a[0], b[1] - a[1]
    L = math.hypot(dx, dz)
    nx, nz = -dz / L * thick, dx / L * thick
    pts_top = [(a[0], a[1]), (b[0], b[1]), (b[0] + nx, b[1] + nz), (a[0] + nx, a[1] + nz)]
    tops = [ya + height, yb + height, yb + height, ya + height]
    cliff.face([(p[0], p[1], t) for p, t in zip(pts_top, tops)], 2, (0, 0, 1))
    for i in range(4):
        p, q = pts_top[i], pts_top[(i + 1) % 4]
        yp = ya if i in (0, 3) else yb
        yq = yb if i in (0, 1) else ya
        mx, mz = (p[0] + q[0]) / 2 - (a[0] + b[0] + nx) / 2, (p[1] + q[1]) / 2 - (a[1] + b[1] + nz) / 2
        cliff.face([(p[0], p[1], yp - 40), (q[0], q[1], yq - 40), (q[0], q[1], tops[(i + 1) % 4]), (p[0], p[1], tops[i])],
                   2, (mx, mz, 0))
    if collider:
        edges.face([(a[0], a[1], ya + height), (b[0], b[1], yb + height), (b[0], b[1], yb + height + collider),
                    (a[0], a[1], ya + height + collider)], 0, None)
        edges.face([(b[0], b[1], yb + height), (a[0], a[1], ya + height), (a[0], a[1], ya + height + collider),
                    (b[0], b[1], yb + height + collider)], 0, None)


edges = Mesh("path_colliders", [EDGE], coll)
# leg 1's outer (south) edge over the cove and the hull, then the switchback's south edge
lip((150, -925), (946, -925), 140 + 100 * 400 / 1200, 240, thick=-26)
lip((954, -925), (1196, -925), 240, 240, thick=-26)
# the spire shelf's south and east edges (drops to the beach and the sea)
lip((1206, -903), (1528, -903), 230, 230, thick=-26)
lip((1555, -935), (1555, -1436), 230, 230, thick=-26)
# the gate landing's south edge: a low parapet, and a collider above it so leg 2 can't jump the gate
lip((950, -1425), (1240, -1425), 420, 420, height=100, thick=-26)
# the lookout notch's parapet over the drop to the harbour
lip((960, -1805), (1240, -1805), 420, 420, height=100, thick=26, collider=500)
# boulders on leg 1: cover from the lookout
for n, bx in enumerate((250, 520, 760)):
    by = 140 + 100 * (bx + 250) / 1200
    C.boulder(cliff, bx, -1010 - 30 * n, by, 62, 115, 20 + n, 2)
# the palisade gate: a wall of logs across the landing's east end, a doorway 160 x 180 in it, two rock pillars
GX = 1250
# the doorway 150 wide and 148 high, well under the door's 198 x 199, so the door overlaps its frame all round
for (za, zb) in ((-1720, -1625), (-1475, -1380)):
    cliff.box(GX - 30, za, GX + 30, zb, 180, 700, 3)
cliff.box(GX - 8, -1645, GX + 8, -1455, 570, 712, 3, bottom=True)  # over the doorway, its ends inside the posts
cliff.box(GX - 45, -1690, GX + 45, -1640, 380, 690, 2)
cliff.box(GX - 45, -1460, GX + 45, -1410, 380, 690, 2)
C.decal(cliff, [(GX - 34, -1610, 612), (GX - 34, -1490, 612), (GX - 34, -1490, 705), (GX - 34, -1610, 705)], 5)
# the passage behind the gate: a floor at 420 walled in rock, the exit at its end
strip(1250, 1360, -1650, -1450, 420, 420)
cliff.box(1284, -1765, 1636, -1652, 60, 724, 1)
cliff.box(1284, -1448, 1636, -1396, 150, 724, 1)
cliff.box(1362, -1648, 1632, -1452, 60, 718, 1)
edges.face([(GX, -1720, 700), (GX, -1380, 700), (GX, -1380, 1150), (GX, -1720, 1150)], 0, (-1, 0, 0))
edges.face([(GX, -1380, 700), (GX, -1720, 700), (GX, -1720, 1150), (GX, -1380, 1150)], 0, (1, 0, 0))
# the warning sign at the foot of the path
sy = H(-150, -860)
cliff.box(-60, -905, -50, -895, sy - 10, sy + 150, 3)
C.decal(cliff, [(-110, -898, sy + 100), (0, -898, sy + 100), (0, -898, sy + 170), (-110, -898, sy + 170)], 4)
spots["door"] = (GX, -1550, 420)
spots["exit"] = (1320, -1550, 420)
spots["arrive"] = (1080, -1550, 420)
spots["lookout_point"] = (1100, -1760, 420)
spots["torches"] = [(GX - 50, -1665, 700), (GX - 50, -1435, 700)]
cliff.build()
edges.build()

# the lookout's spire: a tall rock column on the shelf, a level perch on top
spire = Mesh("spire", [CLIFF, STONE], coll, uv_size=160.0)
SX, SZ = 1420, -1150
ring0 = [(SX + 105 * math.cos(a), SZ + 105 * math.sin(a)) for a in [k * math.tau / 6 + 0.2 for k in range(6)]]
ring1 = [(SX + 80 * math.cos(a), SZ + 80 * math.sin(a)) for a in [k * math.tau / 6 + 0.45 for k in range(6)]]
for i in range(6):
    a0, b0 = ring0[i], ring0[(i + 1) % 6]
    a1, b1 = ring1[i], ring1[(i + 1) % 6]
    mid = ((a0[0] + b0[0]) / 2 - SX, (a0[1] + b0[1]) / 2 - SZ, 0)
    spire.face([(a0[0], a0[1], 200), (b0[0], b0[1], 200), (b1[0], b1[1], 500), (a1[0], a1[1], 500)], 0, mid)
spire.face([(p[0], p[1], 500) for p in ring1], 1, (0, 0, 1))
spots["perch"] = (SX, SZ, 500)
spire.build()

# ------------------------------------------------------------------------------------------------ rocks: cover and landmarks
ROCKS = [  # (x, z, radius, squash): village cover, beach cover every 400-600, the sandbar's arch pillars
    (-1200, 440, 95, 1.1), (-950, 640, 95, 1.05), (-1170, 690, 95, 1.0),
    (520, 640, 100, 1.1), (820, 280, 105, 1.0), (430, 120, 95, 1.1), (760, -60, 100, 1.0),
]
rocks = Mesh("rocks", [STONE, CLIFF], coll, uv_size=128.0)
for n, (rx, rz, rr, sq) in enumerate(ROCKS):
    C.boulder(rocks, rx, rz, H(rx, rz), rr * 0.68, 105 * sq + (n % 3) * 12, 40 + n, 0)
# the arch over the sandbar's view north: two tall rocks and a slab across
C.boulder(rocks, 150, 880, H(150, 880), 75, 290, 61, 1, sides=6)
C.boulder(rocks, 560, 880, H(560, 880), 75, 290, 62, 1, sides=6)
rocks.obox(355, 880, 270, 55, 4, 225, 300, 1)
rocks.build()
# the tide-pool cove: a rock roof over its back, and a ledge (grab) with the ammo crate
cove = Mesh("cove", [CLIFF, STONE], coll, uv_size=160.0)
cove.face([(1080, 1530, 300), (1420, 1530, 300), (1420, 1330, 270), (1080, 1330, 270)], 0, (0, 0, -1))
cove.face([(1080, 1530, 310), (1420, 1530, 310), (1420, 1330, 280), (1080, 1330, 280)], 0, (0, 0, 1))
ledge_top = jfg64.game_texture_material(0x195A, "ledge", name="ledge_195A")
cove.materials.append(ledge_top)
cove.box(1270, 1375, 1360, 1430, -10, 160, 1, top=2)
spots["cove_tribal"] = (1180, 1395, 0)
spots["cove_health"] = (1120, 1400, 0)
spots["cove_ammo"] = (1325, 1410, 160)
cove.build()

# ------------------------------------------------------------------------------------------------ palms and grass


def palm(name, x, z, lean, seed):
    m = Mesh(name, [TRUNK, LEAF], coll, uv_size=64.0)
    gy = H(x, z)
    top = (x + lean[0], z + lean[1], gy + 330)
    midp = (x + lean[0] * 0.35, z + lean[1] * 0.35, gy + 170)
    rings = []
    for (cx, cz, cy), r in (((x, z, gy - 10), 16), (midp, 12), (top, 9)):
        rings.append([(cx + r * math.cos(k * math.tau / 4), cz + r * math.sin(k * math.tau / 4), cy) for k in range(4)])
    for j in range(2):
        for k in range(4):
            a0, b0 = rings[j][k], rings[j][(k + 1) % 4]
            a1, b1 = rings[j + 1][k], rings[j + 1][(k + 1) % 4]
            cx = (a0[0] + b0[0]) / 2 - x
            cz = (a0[1] + b0[1]) / 2 - z
            m.face([a0, b0, b1, a1], 0, (cx, cz, 0))
    for k in range(5):
        a = k * math.tau / 5 + seed
        dx, dz = math.cos(a), math.sin(a)
        tip = (top[0] + dx * 190, top[1] + dz * 190, top[2] - 70)
        side = (-dz * 46, dx * 46)
        mid = (top[0] + dx * 95, top[1] + dz * 95, top[2] + 15)
        frond = [top, (mid[0] + side[0], mid[1] + side[1], mid[2]), tip, (mid[0] - side[0], mid[1] - side[1], mid[2])]
        m.face(frond, 1, (0, 0, 1))
        m.face([(p[0], p[1], p[2] - 5) for p in frond], 1, (0, 0, -1))  # its underside, apart from the top
    return m.build()


PALMS = [(170, 1060, (40, -60)), (560, 1080, (-50, -40)), (-680, 330, (60, 30)),
         (250, 420, (-40, 60))]
for n, (px, pz, lean) in enumerate(PALMS):
    palm(f"palm{n}", px, pz, lean, n * 0.7)

# ------------------------------------------------------------------------------------------------ backdrops beyond the edge
back = Mesh("backdrop", [PLANK, HULL, THATCH, CLIFF], coll, uv_size=200.0)
# the corsairs' watchtower behind the gate, seen from the sandbar
back.box(1600, -2060, 1690, -1970, 300, 860, 0)
back.box(1570, -2090, 1720, -1940, 860, 950, 1)
back.face([(1560, -1930, 950), (1730, -1930, 950), (1645, -2015, 1040)], 2, (0, 1, 0.5))
back.face([(1730, -2100, 950), (1560, -2100, 950), (1645, -2015, 1040)], 2, (0, -1, 0.5))
back.face([(1730, -1930, 950), (1730, -2100, 950), (1645, -2015, 1040)], 2, (1, 0, 0.5))
back.face([(1560, -2100, 950), (1560, -1930, 950), (1645, -2015, 1040)], 2, (-1, 0, 0.5))
# the harbour far below the notch: piers, the moored ship, a warehouse
back.box(900, -2700, 2600, -2600, -100, -20, 0)
back.box(1400, -3300, 1500, -2702, -100, -20, 0)
back.box(2100, -3600, 2900, -3150, -100, 300, 1, top=2)
sx0, sx1, sz = 1650, 2450, -3000
back.face([(sx0, sz - 100, -40), (sx1, sz - 100, -40), (sx1 - 60, sz, 90), (sx0 + 60, sz, 90)], 1, (0, -1, 0.3))
back.face([(sx1, sz + 100, -40), (sx0, sz + 100, -40), (sx0 + 60, sz, 90), (sx1 - 60, sz, 90)], 1, (0, 1, 0.3))
for mx in (1900, 2200):
    back.box(mx - 10, sz - 10, mx + 10, sz + 10, 80, 480, 0)
# the headland's sea cliffs east of the shelf, standing out of the water
back.box(1644, -1745, 2000, -1300, -100, 520, 3)
back.build()

# ------------------------------------------------------------------------------------------------ light
level = [o for o in coll.all_objects if o.type == "MESH"]
SUN_DIR = (-0.3, 0.28, -0.91)  # from high in the south-east (Blender space: the light's travel)
LAMPS = [
    (-1000, -720, fy + 30, 300, (0.55, 0.3, 0.1)),  # the cookfire
    (GX - 50, -1665, 700, 260, (0.5, 0.3, 0.12)),  # the gate's torches
    (GX - 50, -1435, 700, 260, (0.5, 0.3, 0.12)),
    (SX, SZ, 530, 220, (0.45, 0.32, 0.12)),  # the lookout's lantern
    (1250, 1460, 60, 260, (0.05, 0.18, 0.22)),  # the cove's water glow
]


def extra(x, z, y, mat):
    if mat.startswith("game_185E"):  # wet sand at the shore and under the water
        k = smooth((y + 25) / 40.0)
        return (0.72 + 0.28 * k, 0.74 + 0.26 * k, 0.8 + 0.2 * k)
    return (1.0, 1.0, 1.0)


C.bake(level, SUN_DIR, (0.62, 0.6, 0.55), (0.42, 0.47, 0.56), tints=TINTS, lamps=LAMPS, extra=extra,
       soft={"game_185E": (0.8, 0.15), "game_195F": (0.8, 0.15)})

# ------------------------------------------------------------------------------------------------ export
os.makedirs(C.OUT, exist_ok=True)
report = jfg64.budgets(level)
out = jfg64.export(os.path.join(C.OUT, NAME + ".glb"), collection=coll)
spots["budgets"] = report
spots["export"] = {k: v for k, v in out.items() if k != "objects"} if isinstance(out, dict) else str(out)


def tup(v):
    return [round(c, 1) for c in v] if isinstance(v, (tuple, list)) and v and isinstance(v[0], (int, float)) else v


with open(os.path.join(C.OUT, NAME + "_spots.json"), "w", encoding="utf-8") as f:
    json.dump({k: ([tup(x) for x in v] if isinstance(v, list) and v and isinstance(v[0], tuple) else tup(v))
               for k, v in spots.items()}, f, indent=1)
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(C.OUT, NAME + ".blend"))
print("SUNWRECK", json.dumps(report))
print("PARTS", json.dumps({o.name: sum(len(p.vertices) - 2 for p in o.data.polygons) for o in level}))
