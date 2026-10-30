"""Caldera Crown (Corsair Reach 3.3, Cinderhold's last level and the pack's finale): builds the level from nothing and
exports blender/out/crown.glb.

    blender --background --factory-startup --addons jfg64 --python crown.py
Then in JFG-Studio: reimport_geometry (or import the .glb) into the level `crown`.

Game coordinates throughout (x east, z south, y up). The volcano's summit at night, climbed from the south-east:
  A  the roof door ledge (600): the doorhouse with the roof door (back down to the Bellows) and the service lift (the
     coolant vents), a railing over the drop to the flats
  B  the switchbacks: four legs 300 wide (275 to walk, a rock lip on the outer edge) up the cone's south face, 600 ->
     1,000, landings at the turns; two lookouts on perches a leg up, ember beetles and cinder wasps at the west landing
  C  the ash shelf (1,000, 900 x 600): the crown guards round a fire drum; a lava pool with the rim gate's
     counterweight switch on a basalt pillar; a Tribal's alcove
  D  the rim gate: a cut through the rim, a ramp 1,000 -> 1,100, the switch door in a wall across it
  E  the rim walk round the inside of the crater (1,100 -> 1,300), a railing over the lava lake far below; a bay with
     slag gunners, cinder wasps further on, a Tribal at its dead end
  Q  the quiet room (1,400): full health before the arena
  F  the Crown: a ring walkway (430-700 from its centre) round a shallow molten pit, two causeways to the island
  G  the forge core on the island: its door (locked by the last wave), a Tribal and the shuttle pad (the way home)
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

NAME = "crown"
scene, coll = C.new_scene(NAME)
spots = {}


# ------------------------------------------------------------------------------------------------ own images
def banner_px(x, y):
    """The forge-masters' banner: dark red cloth, a gold crown of three points over a gold hammer, a gold hem."""
    W, H = 32, 64
    cloth = (0.32, 0.05, 0.04) if (x // 2 + y // 3) % 5 else (0.27, 0.04, 0.03)
    gold = (0.92, 0.7, 0.22)
    if x < 2 or x > W - 3 or y > H - 4:
        return gold
    if y < 3:
        return (0.12, 0.08, 0.06)
    if 12 <= y <= 24:  # the crown
        t = (24 - y) / 12.0
        for px in (8, 16, 24):
            if abs(x - px) < 1 + 3.5 * (1 - t):
                return gold
        if y >= 21 and 6 <= x <= 26:
            return gold
    if 30 <= y <= 50 and abs(x - 16) <= 1:  # the hammer's haft
        return gold
    if 28 <= y <= 33 and 9 <= x <= 23:  # its head
        return gold
    return cloth


def runes_px(x, y):
    """Glowing runes cut in dark iron: orange strokes in a 4 x 4 grid of cells."""
    cx, cy = x % 8, y % 8
    cell = (x // 8) * 7 + (y // 8) * 13
    strokes = [
        cx == 2 + cell % 3 and 1 <= cy <= 6,
        cy == 2 + (cell // 3) % 3 and 1 <= cx <= 6,
        cx - cy == (cell % 5) - 2 and 1 <= cx <= 6,
    ]
    if any(strokes[:1 + cell % 3]):
        return (1.0, 0.55, 0.12)
    return (0.1, 0.07, 0.06) if (x + y) % 5 else (0.14, 0.09, 0.07)


def gold_px(x, y):
    """Molten gold for the Crown's spikes: bright gold, darker veins."""
    v = math.sin(x * 0.8 + y * 0.45) + math.sin(y * 0.9 - x * 0.3)
    return (0.95, 0.72, 0.22) if v > -0.6 else (0.62, 0.38, 0.1)


def hatch_px(x, y):
    """The shuttle pad's hatch: a riveted iron door, a yellow-black hazard frame, a green lamp at the top."""
    W, H = 32, 64
    if x < 3 or x > W - 4 or y < 3 or y > H - 4:
        return (0.95, 0.75, 0.1) if ((x + y) // 4) % 2 else (0.08, 0.07, 0.06)
    if 6 <= y <= 9 and 12 <= x <= 19:
        return (0.3, 1.0, 0.4)
    if (x in (6, 25) or y in (14, 50)) and y % 4 == 0:
        return (0.62, 0.6, 0.56)
    return (0.36, 0.36, 0.38) if (y // 12) % 2 else (0.31, 0.31, 0.33)


def grille_px(x, y):
    """The service lift's cage: dark iron bars over a dim shaft."""
    if x % 8 in (0, 1) or y % 16 in (0, 1):
        return (0.42, 0.4, 0.38)
    return (0.05, 0.05, 0.06)


def streak_px(x, y):
    """A lava river seen from far above: glowing orange, a darker crust at its edges (the backdrop)."""
    e = abs(x - 7.5) / 8.0
    return (1.0, 0.45 + 0.2 * (1 - e), 0.1) if e < 0.6 else (0.4, 0.12, 0.05)


MATS = []


def mat(material):
    MATS.append(material)
    return len(MATS) - 1


ASH = mat(C.game(0x060D))      # ash ground: legs, landings, the shelf, the rim walk
CRUST = mat(C.game(0x0C3E))    # scorched crust: lava banks, the crater
BASALT = mat(C.game(0x0C37))   # basalt cliffs and lips
COLUMN = mat(C.game(0x1660))   # basalt columns: the switch's pillar
SLAG = mat(C.game(0x07F2))     # slag lumps: cover
LAVA = mat(C.game(0x1547, "lava"))
STONE = mat(C.game(0x0A20))    # dressed stone: the causeways, the anvils, the doorhouse
PAVE = mat(C.game(0x08A8))     # the Crown's ring and the quiet room
IRON = mat(C.game(0x0B0C))     # braziers, the gate wall, trim
BRICK = mat(C.game(0x171C))    # the forge core, the gate
BANNER = mat(C.own_material("crown_banner", C.own_image("crown_banner", 32, 64, banner_px)))
RUNES = mat(C.own_material("crown_runes", C.own_image("crown_runes", 32, 32, runes_px)))
GOLD = mat(C.own_material("crown_gold", C.own_image("crown_gold", 16, 16, gold_px)))
HATCH = mat(C.own_material("crown_hatch", C.own_image("crown_hatch", 32, 64, hatch_px)))
GRILLE = mat(C.own_material("crown_grille", C.own_image("crown_grille", 16, 32, grille_px)))
STREAK = mat(C.own_material("crown_streak", C.own_image("crown_streak", 16, 16, streak_px)))
EDGE = jfg64.boundary_material()


def mesh(name, uv=200.0):
    return Mesh(name, MATS, coll, uv_size=uv)


edges = Mesh("colliders", [EDGE], coll)

# ------------------------------------------------------------------------------------------------ the plan in numbers
CX, CZ = 750.0, -1250.0    # the crater's centre: lake r < 480 (bed 870, lava 900), walk r 675-925 (ledge from 534)
AX, AZ = -1500.0, -1200.0  # the Crown's centre: island r < 290, pit 290-430, ring 430-700
YA, YS, YW0, YW1, YC = 600.0, 1000.0, 1100.0, 1300.0, 1400.0
LAKE_BED, LAKE = 870.0, 900.0
PIT_BED, PIT = YC - 36, YC - 6
POOL = (1400, 0, 1500, 100)  # the shelf's lava pool: its bed vertices (x0, z0, x1, z1); banks out to 100 round them
POOL_BED, POOL_LAVA = YS - 36, YS - 6


def clamp(v, a, b):
    return max(a, min(b, v))


def f1(x):  # leg 1, west from the ledge: 600 at x 1,000, 700 at x -1,200
    return YA + 100 * (1000 - clamp(x, -1200, 1000)) / 2200


def f2(x):  # leg 2, east: 700 -> 800
    return 700 + 100 * (clamp(x, -1200, 700) + 1200) / 1900


def f3(x):  # leg 3, west: 800 at x 700 -> 900
    return 900 - 100 * (clamp(x, -1200, 700) + 1200) / 1900


def f4(x):  # leg 4, east: 900 -> 1,000 at the shelf
    return 900 + 100 * (clamp(x, -1200, 700) + 1200) / 1900


def lerp(a, b, t):
    return a + (b - a) * clamp(t, 0.0, 1.0)


def b12(x, z):  # the bank under leg 2 / the east landing, down to leg 1
    up = f2(x) if x <= 700 else 800.0
    return lerp(up, f1(x), (z - 1300) / 100)


def b23(x, z):
    return lerp(f3(x), f2(x), (z - 900) / 100)


def b34(x, z):
    up = f4(x) if x <= 700 else YS
    lo = f3(x) if x <= 700 else 800.0
    return lerp(up, lo, (z - 500) / 100)


def shelf(x, z):
    if POOL[0] <= x <= POOL[2] and POOL[1] <= z <= POOL[3]:
        return POOL_BED
    return YS


def gate_floor(x, z):  # the cut through the rim: a ramp 1,000 -> 1,100 over z -100..-300 (26.6 degrees), then level
    return YS + 100 * clamp((-100 - z) / 200, 0, 1)


def qpass_floor(x, z):  # from the walk's end west to the quiet room: 1,300 -> 1,400 over x -200..-400
    return YW1 + 100 * clamp((-200 - x) / 200, 0, 1)


def rect(x0, x1, z0, z1, fn):
    return (x0, x1, z0, z1, fn if callable(fn) else (lambda x, z, v=fn: v))


ZONES = [
    rect(1000, 1500, 1400, 1700, YA),                          # A
    rect(-1200, 1000, 1400, 1700, lambda x, z: f1(x)),         # leg 1
    rect(-1500, -1200, 1000, 1700, 700.0),                     # the west landing 1-2
    rect(-1200, 1000, 1300, 1400, b12),
    rect(-1200, 700, 1000, 1300, lambda x, z: f2(x)),          # leg 2
    rect(700, 1000, 600, 1300, 800.0),                         # the east landing 2-3
    rect(1000, 1200, 1000, 1200, 800.0),                       # Tribal 1's alcove
    rect(-1200, 700, 900, 1000, b23),
    rect(-1500, -1200, 900, 1000, lambda x, z: lerp(900, 700, (z - 900) / 100)),
    rect(-1200, 700, 600, 900, lambda x, z: f3(x)),            # leg 3
    rect(-1500, -1200, 200, 900, 900.0),                       # the west landing 3-4
    rect(-1200, 1000, 500, 600, b34),
    rect(-1200, 700, 200, 500, lambda x, z: f4(x)),            # leg 4
    rect(700, 1600, -100, 500, shelf),                         # C
    rect(1600, 1800, 200, 400, YS),                            # Tribal 2's alcove
    rect(1000, 1300, -600, -100, gate_floor),                  # D
    rect(-400, -100, -1300, -1100, qpass_floor),               # to the quiet room
    rect(-700, -400, -1350, -1050, YC),                        # Q
    rect(-800, -700, -1300, -1100, YC),                        # into the Crown
]

WALK_A0, WALK_A1 = 35.0, 180.0   # degrees round the crater (0 east, 90 south)
BAY = (96.0, 124.0, 1100.0)      # the gunners' bay: angles and its outer radius


def walk_floor(phi):
    return YW0 + (YW1 - YW0) * clamp((phi - 70.0) / 100.0, 0, 1)


def polar(x, z, cx=CX, cz=CZ):
    r = math.hypot(x - cx, z - cz)
    a = math.degrees(math.atan2(z - cz, x - cx))
    if a < -90:
        a += 360.0
    return r, a


def at(r, phi, cx=CX, cz=CZ):
    return (cx + r * math.cos(math.radians(phi)), cz + r * math.sin(math.radians(phi)))


def walk_zone(x, z):
    r, a = polar(x, z)
    rout = BAY[2] if BAY[0] <= a <= BAY[1] else 925.0
    da = max(WALK_A0 - a, a - WALK_A1) * math.pi / 180 * r
    d = max(534 - r, r - rout, da)
    # outside the railing (r 662) the ledge falls 40 to its edge at 534, so the lake shows over it from the walk;
    # every grid triangle under the walk (r 675+) keeps its corners at 534 or more: its floor stays level
    return walk_floor(clamp(a, WALK_A0, WALK_A1)) - 40 * clamp((660 - r) / 126, 0, 1), d


def causeway(x, z):
    return -1600 <= x <= -1400 and (-1700 <= z <= -1500 or -900 <= z <= -700)


def arena(x, z):
    ra = math.hypot(x - AX, z - AZ)
    # the pit: every grid vertex 290-430 from the centre is its bed, so the 100 grid holds a closed ring of lava;
    # its banks are the triangles from those vertices up to the island's and the ring's (36 over 100 or more)
    y = YC if causeway(x, z) or ra <= 290 or ra >= 430 else PIT_BED
    return y, ra - 700


def zone_at(x, z):
    best = None
    for (x0, x1, z0, z1, fn) in ZONES:
        d = max(x0 - x, x - x1, z0 - z, z - z1)
        if best is None or d < best[1]:
            best = (fn, d)
    fl, d = best[0](x, z), best[1]
    wf, wd = walk_zone(x, z)
    if wd < d:
        fl, d = wf, wd
    af, ad = arena(x, z)
    if ad < d:
        fl, d = af, ad
    return fl, d


def cliff(x, z):
    """Rock beyond the floors: higher to the north (the summit), higher still round the Crown."""
    ra = math.hypot(x - AX, z - AZ)
    return (1350 + 400 * smooth((800 - z) / 1600) + 60 * math.sin(x / 290.0) * math.cos(z / 330.0)
            + 30 * math.sin(x / 123.0 + z / 171.0) + 180 * smooth(1 - (ra - 600) / 700))


def bowl(x, z):
    r = math.hypot(x - CX, z - CZ)
    return LAKE_BED if r <= 480 else LAKE_BED + (r - 480) * 13


def H(x, z):
    if z > 1700:  # the cone's outer face below the lip and the railing: dropping to the flats' level
        top = H(x, 1700)
        return top + (60 - top) * smooth((z - 1700) / 300)
    fl, d = zone_at(x, z)
    if d <= 0:
        return fl
    rock = max(cliff(x, z), fl + 350)
    if d > 150:
        y = 100.0 * round(rock / 100.0)  # plateaus out of reach: flat, so they merge into few faces
    else:
        y = fl + (rock - fl) * smooth(d / 50.0)
    return min(y, bowl(x, z))


def ground_mat(x, z, y, slope):
    ra = math.hypot(x - AX, z - AZ)
    rc = math.hypot(x - CX, z - CZ)
    if causeway(x, z):
        return 4  # dressed stone
    if slope > 40:
        return 2
    if rc < 540 or 270 < ra < 450:
        return 1  # crust: the crater, the pit's banks
    if POOL[0] - 120 <= x <= POOL[2] + 120 and POOL[1] - 120 <= z <= POOL[3] + 120:
        return 1
    if ra < 700 or (-800 <= x <= -400 and -1350 <= z <= -1050):
        return 3  # the Crown's paving, the quiet room
    return 0


X0, Z0, X1, Z1 = -2400, -2100, 1900, 2000
ground = C.heightfield("ground", coll, X0, Z0, X1, Z1, 100.0, H, ground_mat,
                       [MATS[ASH], MATS[CRUST], MATS[BASALT], MATS[PAVE], MATS[STONE]], boundary=420.0,
                       flat_angle=1.2, merge_above=1450.0)
spots["ground_tris"] = len(ground.data.polygons)

# ------------------------------------------------------------------------------------------------ lava
lava = Mesh("lava", MATS, coll, uv_size=200.0)
C.water_surface(lava, H, 200, -1800, 1300, -700, 100.0, LAKE, LAVA, merge=3)               # the crater lake
C.water_surface(lava, H, -2000, -1700, -1000, -700, 100.0, PIT, LAVA, merge=2)             # the Crown's pit
C.water_surface(lava, H, 1300, -100, 1600, 200, 100.0, POOL_LAVA, LAVA, merge=2)           # the shelf's pool
lava.build()

# ------------------------------------------------------------------------------------------------ the backdrop
# the flats far below, south of the cone: big quads out of reach (behind the lip, its collider and the railing),
# dark ash with lava rivers glowing in them
bd = mesh("backdrop", 1000.0)
for x0 in range(-6000, 6000, 1000):
    for z0 in range(1900, 7900, 1000):
        bd.face([(x0, z0, 40), (x0 + 1000, z0, 40), (x0 + 1000, z0 + 1000, 40), (x0, z0 + 1000, 40)], ASH, (0, 0, 1))
RIVERS = [[(-5200, 3000), (-3100, 3600), (-1500, 4600), (300, 5200), (2600, 6100)],
          [(4800, 2600), (3300, 3400), (2100, 4300), (900, 5200)]]
for pts in RIVERS:
    for (ax, az), (bx, bz) in zip(pts, pts[1:]):
        L = math.hypot(bx - ax, bz - az)
        nx, nz = -(bz - az) / L * 45, (bx - ax) / L * 45
        bd.face([(ax - nx, az - nz, 44), (bx - nx, bz - nz, 44), (bx + nx, bz + nz, 44), (ax + nx, az + nz, 44)],
                STREAK, (0, 0, 1), [(0, 0), (1, 0), (1, 1), (0, 1)])
bd.build()

# ------------------------------------------------------------------------------------------------ lips and railings
rk = mesh("lips", 128.0)
# leg 1 and the west landing over the outer face: a rock lip 150 with a collider to 400 (the drop to the flats)
C.lip(rk, (-1500, 1675), (-1200, 1675), 700, 700, BASALT, h=150.0, caps=(False, False))
C.lip(rk, (-1200, 1675), (1000, 1675), f1(-1200), f1(1000), BASALT, h=150.0, caps=(False, True))
for xa in range(-1500, 1000, 250):  # its collider in pieces of 250 (one long one fills the hero's collision list)
    xb = min(xa + 250, 1000)
    C.collider(edges, (xa, 1688), (xb, 1688), min(f1(xa), f1(xb)) + 150, max(f1(xa), f1(xb)) + 400)
# the ledge: a railing (seen through) for the view down, its collider in its line
C.fence(rk, edges, (1000, 1690), (1350, 1690), YA, YA, IRON, h=150.0, coll=400.0)
# legs 2-4 over the leg below: a rock lip 100 without a collider (a fall of 200 at most lands on the leg below)
P1 = (-300.0, 1300.0)  # lookout 1's perch: x, the leg's edge (z) it stands out from
P2 = (-900.0, 900.0)   # lookout 2's perch
LIPS = [  # (x from, x to, z of the lip's inner face, floor fn, caps): pieces that butt leave out the cap between them
    (-1100, P1[0] - 34, 1275, f2, (True, True)), (P1[0] + 34, 700, 1275, f2, (True, False)),
    (700, 1000, 1275, lambda x: 800.0, (False, True)),
    (-1500, -1200, 875, lambda x: 900.0, (False, False)), (-1200, P2[0] - 34, 875, f3, (False, True)),
    (P2[0] + 34, 450, 875, f3, (True, True)),
    (-1050, 700, 475, f4, (True, False)), (700, 1000, 475, lambda x: YS, (False, True)),
]
for (xa, xb, zl, fn, caps) in LIPS:
    C.lip(rk, (xa, zl), (xb, zl), fn(xa), fn(xb), BASALT, h=100.0, thick=25.0, caps=caps)
rk.build()

# ------------------------------------------------------------------------------------------------ lookouts' perches
pr = mesh("perches", 128.0)
BRAZ = []  # (x, z, floor): braziers, the game's flames on top (placed in Studio)
for n, ((px, ez), fn, up_floor) in enumerate(((P1, b12, f2), (P2, b23, f3))):
    top = up_floor(px) + 60
    # 64 across, 110 deep: 40 on the upper leg's floor, 70 out over the bank
    pr.box(px - 32, ez - 40, px + 32, ez + 70, fn(px, ez + 70) - 20, top, BASALT, top=STONE)
    spots[f"lookout{n + 1}"] = (px, ez + 40, top)
    BRAZ.append((px - 80, ez - 60, up_floor(px - 80)))
pr.build()

# ------------------------------------------------------------------------------------------------ cover
cv = mesh("cover", 128.0)
ROCKS = [  # (x, z): slag boulders r 55, 110 tall: cover on the legs and in the fights
    (500, 1600), (60, 1470), (-650, 1620),                                   # leg 1 (lookout 1 above)
    (-1400, 1560), (-1330, 1380), (-1400, 1170), (-1100, 1520), (-1020, 1120),  # the west landing (beetles)
    (-400, 1080), (300, 1220),                                               # leg 2
    (-700, 700), (150, 820),                                                 # leg 3
    (-1430, 650), (-400, 300), (300, 420),                                   # the west landing 3-4, leg 4
    (850, 40), (1170, 50), (870, 340), (1170, 330),                          # the shelf (crown guards)
]
for n, (x, z) in enumerate(ROCKS):
    C.boulder(cv, x, z, H(x, z), 58, 110 + (n % 3) * 8, 700 + n, SLAG)
for n, (r, a) in enumerate(((940, 104.5), (940, 115.5))):  # the bay: the gunners' cover
    x, z = at(r, a)
    C.boulder(cv, x, z, H(x, z), 60, 118, 760 + n, SLAG)
spots["walk_rocks"] = [at(940, 104.5), at(940, 115.5)]
# the shelf's fire drum (140 across, 100 tall; cover) with the game's flames on top
cv_drum = (1010.0, 200.0)
C.post(cv, cv_drum[0], cv_drum[1], 70, YS - 5, YS + 100, IRON, n=10, cap=True)
spots["fire_drum"] = (cv_drum[0], cv_drum[1], YS + 100)
# anvils on the ring (90 x 90, 110 tall): cover for the waves
# (40 off the ring's outer wall at least: an anvil nearer joins the wall and gets no hole)
# and 45 inside their squad's region: one touching its edge gets none either)
ANVILS = [(-990, -1490), (-990, -1350), (-990, -1200), (-990, -1050), (-990, -910),   # wave 1 (east)
          (-2010, -1490), (-2010, -1350), (-2010, -1050), (-2010, -910),              # wave 2 (west)
          (-1680, -690), (-1320, -690)]                                               # wave 3's forgemasters
for (x, z) in ANVILS:
    cv.box(x - 45, z - 45, x + 45, z + 45, YC - 40, YC + 80, STONE, top=IRON)  # its foot under the pit's bank
    cv.box(x - 35, z - 35, x + 35, z + 35, YC + 80, YC + 110, IRON)
spots["anvils"] = ANVILS
cv.build()

# ------------------------------------------------------------------------------------------------ braziers
bz = mesh("braziers", 96.0)
BRAZ += [(-1820, -1700, YC), (-1180, -1700, YC), (-1820, -700, YC), (-1180, -700, YC)]  # the causeways' heads
for (x, z, y) in BRAZ:
    C.post(bz, x, z, 12, y - 5, y + 90, IRON, n=6, cap=False)
    C.post(bz, x, z, 30, y + 90, y + 118, IRON, n=8, cap=True)
spots["braziers"] = [(x, z, y + 118) for (x, z, y) in BRAZ]
bz.build()

# ------------------------------------------------------------------------------------------------ A: the doorhouse
dh = mesh("doorhouse", 128.0)
HX0, HX1, HZ0, HZ1 = 1350, 1500, 1400, 1700
HT = YA + 180   # rooms 180 high (the ceiling), the roof slab to 200
OPEN = [(1430, YA - 10, 1530, YA + 160), (1570, YA - 10, 1670, YA + 160)]  # the lift's and the roof door's (z, y)
C.plane_rect(dh, "x", HX0, HZ0, YA - 10, HZ1, YA + 200, OPEN, STONE, (-1, 0, 0))          # the front, outside
C.plane_rect(dh, "x", HX0 + 20, HZ0 + 20, YA - 10, HZ1 - 20, HT, OPEN, STONE, (1, 0, 0))  # inside
for (z0, y0, z1, y1) in OPEN:  # jambs and lintels
    dh.wall((HX0, z0), (HX0 + 20, z0), y0, y0, y1, y1, STONE, facing=(0, 1, 0))
    dh.wall((HX0 + 20, z1), (HX0, z1), y0, y0, y1, y1, STONE, facing=(0, -1, 0))
    dh.face([(HX0, z0, y1), (HX0 + 20, z0, y1), (HX0 + 20, z1, y1), (HX0, z1, y1)], STONE, (0, 0, -1))
C.plane_rect(dh, "z", HZ0, HX0, YA - 10, HX1, YA + 200, [], STONE, (0, -1, 0))            # north and south, outside
C.plane_rect(dh, "z", HZ1, HX0, YA - 10, HX1, YA + 200, [], STONE, (0, 1, 0))
C.plane_rect(dh, "z", HZ0 + 20, HX0 + 20, YA - 10, HX1, HT, [], STONE, (0, 1, 0))        # their inside faces
C.plane_rect(dh, "z", HZ1 - 20, HX0 + 20, YA - 10, HX1, HT, [], STONE, (0, -1, 0))
C.plane_rect(dh, "x", HX1, HZ0 + 20, YA - 10, HZ1 - 20, HT, [], STONE, (-1, 0, 0))       # the back wall
dh.wall((HX0 + 20, 1540), (HX1, 1540), YA - 10, YA - 10, HT, HT, STONE, facing=(0, -1, 0))  # between the rooms
dh.wall((HX1, 1560), (HX0 + 20, 1560), YA - 10, YA - 10, HT, HT, STONE, facing=(0, 1, 0))
dh.box(HX0 - 10, HZ0 - 10, HX1, HZ1 + 10, YA + 200, YA + 220, IRON)                       # the roof slab
C.ceiling(dh, HX0 + 20, HZ0 + 20, HX1, HZ1 - 20, HT, STONE, size=130.0)
C.decal(dh, [(HX1 - 4, 1520, YA + 2), (HX1 - 4, 1440, YA + 2), (HX1 - 4, 1440, YA + 170),
             (HX1 - 4, 1520, YA + 170)], GRILLE)    # the lift's cage on the back wall
C.decal(dh, [(HX1 - 4, 1660, YA + 2), (HX1 - 4, 1580, YA + 2), (HX1 - 4, 1580, YA + 170),
             (HX1 - 4, 1660, YA + 170)], HATCH)     # the roof door, back down to the Bellows
C.decal(dh, [(HX0 - 4, 1440, YA + 170), (HX0 - 4, 1520, YA + 170), (HX0 - 4, 1520, YA + 195),
             (HX0 - 4, 1440, YA + 195)], RUNES)     # a glowing sign over the lift
dh.build()
spots["roof_door_exit"] = (1450, 1620, YA)
spots["lift_exit"] = (1450, 1480, YA)
spots["start0"] = (1280, 1620, YA)
spots["start1"] = (1280, 1480, YA)

# ------------------------------------------------------------------------------------------------ C: the pool's pillar
pl = mesh("pillar", 96.0)
C.post(pl, 1450, 50, 34, POOL_BED - 10, YS + 160, COLUMN, n=6, cap=True)
pl.box(1380, 35, 1450, 65, YS + 150, YS + 168, IRON)        # the arm the counterweight hangs from
pl.box(1388, 38, 1412, 62, YS + 90, YS + 135, IRON)        # the counterweight
C.post(pl, 1400, 50, 3, YS + 135, YS + 150, IRON, n=4, cap=False)
pl.build()
spots["switch"] = (1414, 50, YS + 120)

# ------------------------------------------------------------------------------------------------ D: the rim gate
gt = mesh("gate", 128.0)
WZ0, WZ1 = -440, -400
GX0, GX1, GY = 1070, 1230, YW0 + 160  # the opening for the mine door (202 x 192)
C.plane_rect(gt, "z", WZ1, 950, YW0 - 20, 1350, YW0 + 380, [(GX0, YW0 - 20, GX1, GY)], BRICK, (0, 0, 1))
C.plane_rect(gt, "z", WZ0, 950, YW0 - 20, 1350, YW0 + 380, [(GX0, YW0 - 20, GX1, GY)], BRICK, (0, 0, -1))
gt.face([(950, WZ1, YW0 + 380), (1350, WZ1, YW0 + 380), (1350, WZ0, YW0 + 380), (950, WZ0, YW0 + 380)], BRICK,
        (0, 0, 1))
gt.wall((GX0, WZ0), (GX0, WZ1), YW0 - 20, YW0 - 20, GY, GY, BRICK, facing=(1, 0, 0))
gt.wall((GX1, WZ1), (GX1, WZ0), YW0 - 20, YW0 - 20, GY, GY, BRICK, facing=(-1, 0, 0))
gt.face([(GX0, WZ0, GY), (GX1, WZ0, GY), (GX1, WZ1, GY), (GX0, WZ1, GY)], BRICK, (0, 0, -1))
for bx in (GX0 - 65, GX1 + 5):  # banners either side of the door, on the shelf's side
    C.decal(gt, [(bx, WZ1 + 4, YW0 + 40), (bx + 60, WZ1 + 4, YW0 + 40), (bx + 60, WZ1 + 4, YW0 + 260),
                 (bx, WZ1 + 4, YW0 + 260)], BANNER)
gt.build()
spots["gate_door"] = ((GX0 + GX1) / 2, (WZ0 + WZ1) / 2, YW0)

# ------------------------------------------------------------------------------------------------ E: the rim walk's railing
rw = mesh("rim_rail", 128.0)
ANG = list(range(int(WALK_A0), int(WALK_A1), 10)) + [WALK_A1]
for n, (aa, ab) in enumerate(zip(ANG, ANG[1:])):
    pa, pb = at(662, aa), at(662, ab)
    ya, yb = walk_floor(aa), walk_floor(ab)
    C.fence(rw, edges, pa, pb, ya, yb, IRON, h=150.0, every=150.0, coll=400.0, first=(n == 0))
rw.build()

# ------------------------------------------------------------------------------------------------ Q: the quiet room
qr = mesh("quiet_room", 64.0)
for bz_ in (-1330, -1070):  # two banners on iron frames against the room's north and south sides
    fz = bz_ + (10 if bz_ < -1200 else -10)
    C.post(qr, -640, bz_, 6, YC - 5, YC + 260, IRON, n=4)
    C.post(qr, -520, bz_, 6, YC - 5, YC + 260, IRON, n=4)
    qr.box(-646, bz_ - 6, -514, bz_ + 6, YC + 254, YC + 266, IRON)
    C.decal(qr, [(-630, fz, YC + 30), (-530, fz, YC + 30), (-530, fz, YC + 248), (-630, fz, YC + 248)], BANNER)
qr.build()

# ------------------------------------------------------------------------------------------------ G: the forge core
core = mesh("core", 128.0)
KX0, KX1, KZ0, KZ1 = AX - 120, AX + 120, AZ - 120, AZ + 120   # 240 x 240; the south wall 40 thick (the door's reveal)
KT = YC + 300
DX0, DX1, DY = AX - 80, AX + 80, YC + 160                     # the doorway for the mine door
C.plane_rect(core, "z", KZ1, KX0, YC - 10, KX1, KT, [(DX0, YC - 10, DX1, DY)], BRICK, (0, 0, 1))
C.plane_rect(core, "z", KZ1 - 40, KX0 + 20, YC - 10, KX1 - 20, KT - 20, [(DX0, YC - 10, DX1, DY)], BRICK, (0, 0, -1))
core.wall((DX0, KZ1 - 40), (DX0, KZ1), YC - 10, YC - 10, DY, DY, BRICK, facing=(1, 0, 0))
core.wall((DX1, KZ1), (DX1, KZ1 - 40), YC - 10, YC - 10, DY, DY, BRICK, facing=(-1, 0, 0))
core.face([(DX0, KZ1 - 40, DY), (DX1, KZ1 - 40, DY), (DX1, KZ1, DY), (DX0, KZ1, DY)], BRICK, (0, 0, -1))
C.plane_rect(core, "z", KZ0, KX0, YC - 10, KX1, KT, [], BRICK, (0, 0, -1))
C.plane_rect(core, "x", KX0, KZ0, YC - 10, KZ1, KT, [], BRICK, (-1, 0, 0))
C.plane_rect(core, "x", KX1, KZ0, YC - 10, KZ1, KT, [], BRICK, (1, 0, 0))
C.plane_rect(core, "z", KZ0 + 20, KX0 + 20, YC - 10, KX1 - 20, KT - 20, [], BRICK, (0, 0, 1))
C.plane_rect(core, "x", KX0 + 20, KZ0 + 20, YC - 10, KZ1 - 40, KT - 20, [], BRICK, (1, 0, 0))
C.plane_rect(core, "x", KX1 - 20, KZ0 + 20, YC - 10, KZ1 - 40, KT - 20, [], BRICK, (-1, 0, 0))
C.ceiling(core, KX0 + 20, KZ0 + 20, KX1 - 20, KZ1 - 40, KT - 20, IRON, size=100.0)
core.face([(KX0, KZ1, KT), (KX1, KZ1, KT), (KX1, KZ0, KT), (KX0, KZ0, KT)], IRON, (0, 0, 1))  # the roof
# the Crown on the roof: eight gold spikes round its edge, leaning out
for k in range(8):
    a = math.radians(22.5 + 45 * k)
    bx_, bz_ = AX + 95 * math.cos(a), AZ + 95 * math.sin(a)
    tx, tz = AX + 125 * math.cos(a), AZ + 125 * math.sin(a)
    ta = a + math.pi / 2
    ox, oz = 22 * math.cos(ta), 22 * math.sin(ta)
    ix, iz = -14 * math.cos(a), -14 * math.sin(a)
    p0, p1, p2 = (bx_ - ox, bz_ - oz, KT), (bx_ + ox, bz_ + oz, KT), (bx_ + ix, bz_ + iz, KT)
    tip = (tx, tz, KT + 170)
    for (u, v) in ((p0, p1), (p1, p2), (p2, p0)):
        core.face([u, v, tip], GOLD, ((u[0] + v[0]) / 2 - bx_, (u[1] + v[1]) / 2 - bz_, 0.3),
                  [(0, 0), (1, 0), (0.5, 1)])
# glowing runes on the outside walls and inside; the shuttle pad's hatch on the inside of the north wall
for (pts_, fac) in (
        ([(KX0 - 4, KZ1 - 30, YC + 60), (KX0 - 4, KZ0 + 30, YC + 60), (KX0 - 4, KZ0 + 30, YC + 240),
          (KX0 - 4, KZ1 - 30, YC + 240)], 0),
        ([(KX1 + 4, KZ0 + 30, YC + 60), (KX1 + 4, KZ1 - 30, YC + 60), (KX1 + 4, KZ1 - 30, YC + 240),
          (KX1 + 4, KZ0 + 30, YC + 240)], 0),
        ([(KX1 - 30, KZ0 - 4, YC + 60), (KX0 + 30, KZ0 - 4, YC + 60), (KX0 + 30, KZ0 - 4, YC + 240),
          (KX1 - 30, KZ0 - 4, YC + 240)], 0)):
    C.decal(core, pts_, RUNES)
C.decal(core, [(AX - 50, KZ0 + 24, YC + 2), (AX + 50, KZ0 + 24, YC + 2), (AX + 50, KZ0 + 24, YC + 200),
               (AX - 50, KZ0 + 24, YC + 200)], HATCH)
for bx in (KX0 + 24, KX1 - 24):  # runes inside on the east and west walls
    sgn = 1 if bx < AX else -1
    pts_ = [(bx, AZ + 50 * sgn, YC + 70), (bx, AZ - 50 * sgn, YC + 70), (bx, AZ - 50 * sgn, YC + 200),
            (bx, AZ + 50 * sgn, YC + 200)]
    C.decal(core, pts_, RUNES)
core.build()
spots["core_door"] = (AX, KZ1 - 20, YC)
spots["final_exit"] = (AX, AZ - 55, YC)
spots["tribal4"] = (AX + 60, AZ + 40, YC)

# ------------------------------------------------------------------------------------------------ light
level = [o for o in coll.all_objects if o.type == "MESH"]
SUN_DIR = (-0.25, -0.35, -0.9)  # a faint high light from the south-east: the summit's glow on the ash clouds
LAVA_C = (0.7, 0.24, 0.06)
LAMPS = []
for k in range(8):  # the crater lake's glow, up the inner walls and onto the rim walk
    x, z = at(400, 22.5 + 45 * k)
    LAMPS.append((x, z, LAKE + 150, 650, LAVA_C))
for k in range(8):  # the pit round the island
    x, z = AX + 360 * math.cos(math.radians(45 * k)), AZ + 360 * math.sin(math.radians(45 * k))
    LAMPS.append((x, z, YC + 30, 330, LAVA_C))
LAMPS.append((AX, AZ, YC + 520, 900, (0.85, 0.42, 0.1)))  # the forge's fire on the core's roof
LAMPS.append((1450, 50, YS + 30, 300, LAVA_C))            # the shelf's pool
for (x, z, y) in BRAZ:
    LAMPS.append((x, z, y + 140, 260, (0.6, 0.35, 0.1)))
LAMPS.append((cv_drum[0], cv_drum[1], YS + 160, 380, (0.65, 0.35, 0.1)))
LAMPS.append((1420, 1550, YA + 150, 240, (0.5, 0.3, 0.12)))  # the doorhouse lamp


def extra(x, z, y, mname):
    if mname.startswith("crown_runes"):
        return (2.6, 2.0, 1.6)
    if mname.startswith("crown_streak") or mname.startswith("crown_hatch"):
        return (2.2, 2.0, 1.8)
    if mname.startswith("crown_gold"):
        return (1.8, 1.6, 1.4)
    if y < 100:
        return (0.55, 0.5, 0.5)  # the flats far below in the dark
    return (1.0, 1.0, 1.0)


TINTS = {"game_060D": (1.0, 0.9, 0.85), "game_0C37": (0.95, 0.88, 0.86)}
C.bake(level, SUN_DIR, (0.38, 0.14, 0.1), (0.36, 0.2, 0.17), tints=TINTS, lamps=LAMPS, extra=extra,
       soft={"game_060D": (0.6, 0.2), "game_0C3E": (0.6, 0.2), "game_0C37": (0.6, 0.25), "game_08A8": (0.6, 0.2)})
lme = bpy.data.objects["lava"].data  # the lava glows of itself
lcol = lme.color_attributes.get("Col")
for d in lcol.data:
    d.color_srgb = (1.0, 0.92, 0.8, 1.0)

# ------------------------------------------------------------------------------------------------ export
os.makedirs(C.OUT, exist_ok=True)
report = jfg64.budgets(level)
out = jfg64.export(os.path.join(C.OUT, NAME + ".glb"), collection=coll)
spots["budgets"] = report
spots["export"] = {k: v for k, v in out.items() if k != "objects"} if isinstance(out, dict) else str(out)
spots["walk"] = {f"{a}": at(800, a) + (walk_floor(a),) for a in range(35, 181, 15)}


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
print("CROWN", json.dumps(report))
print("PARTS", json.dumps({o.name: sum(len(p.vertices) - 2 for p in o.data.polygons) for o in level}))
