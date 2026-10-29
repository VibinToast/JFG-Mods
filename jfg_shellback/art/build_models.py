"""Rolling Shellback's models, built in Blender from textures/*.png (make_textures.py), saved as shellback.blend and
exported as models/*.glb, with preview renders in previews/. Low-poly, as the game's own enemies.

    "C:/Program Files/Blender Foundation/Blender 5.2/blender.exe" --background --factory-startup --python build_models.py

- shellback: the beetle, rigged as the decomp's animated-model conventions ask (MSR 12a): one armature, one skin,
             one root bone; rigid skinning (each vertex 100 % to one bone, each triangle on one bone); rotation keys
             on every bone, translation keys on the root only, no scale keys; one glTF animation per game
             animation, named "NN_name" (ordered) with "_loop" on the loops, at 30 fps. Bones all point straight up
             with no roll (the game keeps no joint rest rotation; the importer bakes it anyway).
             Standing it is ~140 long, 68 wide (its feet ~80 apart) and 60 high, facing FORWARD; curled a ball of
             radius ~38 round (0, 0, BALL_Z). The shell is PLATES plates, each a slice of that ball's sphere (so they
             close into it exactly), laid on a wide arch when standing. As no bone but the root may move, the curl is
             all hinges: the middle plate rides the body, each plate hangs from its neighbour nearer the middle by a
             hinge placed where one turn round X takes it from the arch to the ball, and the head hangs from the
             front plate by a neck hinge found the same way; the root carries the whole up to the ball's height.
             Empties barrel (point 0, the spine muzzle), point1 (over the head) and point2 (the weak spot) ride their bones.
- spine:     the projectile: a glowing amber spine 24 long round the origin, pointing FORWARD, in a soft glow shell.
- spark:     the deflect spark: twenty soft rays round a white-hot core, ~30 across.
- dizzy:     four stars on a ring ~40 across (round the origin, flat in XY: the mod spins it over the head).
- dust:      a low dust ring ~50 across, flat on the floor.
Blender's Z is up and 1 unit is 1 game unit; the glTF export turns it to the game's Y up (glTF = (x, z, -y)), so
Blender +Y is glTF -Z, the game's forward. Everything is built facing -Y (the build frame: the constants and comments
below speak of it) and turned to FORWARD as it is output: the mesh, the bones, the points, every animation's moves. All
vertex colours are white (the game lights by vertex colour only, so the shell's light is baked in its texture);
see-through materials blend and are double-sided.
"""
import math
from pathlib import Path

import bmesh
import bpy
from mathutils import Matrix, Vector

# ---- The joints (the game takes up to 45). Names, count and limits are here.
MAX_BONES = 45
PLATES = 5                    # shell plates, front to back, one bone each (3..5 fit the curl below)
ANTENNA_BONES = True          # False: the antennae ride the head bone (saves 2 bones)
ROOT, BODY, NECK, HEAD = "root", "body", "neck", "head"
SPIN = "ball"                 # under the root, at the ball's centre, parent of the rest: 04_ball_loop rolls on it
PLATE_NAME = "plate_{}"       # plate_0 at the front
ANTENNA_NAME = "antenna_{}"   # antenna_L, antenna_R
LEG_NAME = "leg_{}{}"         # leg_FL .. leg_BR: F(ront) M(iddle) B(ack), L(eft, +X) R(ight, -X); it faces -Y
BONE_LEN = 6.0                # bones point up (+Z) this long: only their heads (the joints) matter
POINTS = ("barrel", "point1", "point2")   # the attach points 0-2 (numbered from 0): spine muzzle, over the head, the weak spot

# ---- The animations, in the game's order: (glTF name, pose maker, frames at FPS). Keys on every frame 0..frames, a
# loop's last key the same as its first ("_loop" names loop in the game). BLEND_FRAMES: extras.blendFrames, where not
# the game's default 4.
FPS = 30
DEATH_FRAMES = 30             # 09_death's length: 10_dead holds its last frame (no loop: the game fades the body when it ends)
ANIMS = [("00_idle_loop", "idle", 60), ("01_walk_loop", "walk", 30), ("02_turn_loop", "turn", 18),
         ("03_curl", "curl", 15), ("04_ball_loop", "ball", 16), ("05_dizzy_loop", "dizzy", 30),
         ("06_uncurl", "uncurl", 15), ("07_fire", "fire", 18), ("08_hit", "hit", 9),
         ("09_death", "death", DEATH_FRAMES), ("10_dead", "dead", 1)]
BLEND_FRAMES = {"04_ball_loop": 0, "10_dead": 0}   # each starts exactly where the one before it ends
FIRE_AT = 7                   # the fire action's recoil frame (the spines leave): 7 / 18 = 39 %

# ---- The shape (Blender units = game units, Z up), in the build frame: facing -Y, its left +X.
FORWARD = "+Y"                # the way it faces in the .blend and the export: "+Y" (glTF -Z, the game's) or "-Y"
FACE = Matrix.Rotation(math.pi, 4, "Z") if FORWARD == "+Y" else Matrix()   # build frame -> output
BALL_Z = 38.0                 # the ball's centre height
BALL_R = 38.5                 # the front plate's radius; each plate behind is PLATE_STEP smaller (they shingle)
PLATE_STEP = 0.8
X_SQUASH = 0.9                # the plates' width against their radius (68 wide standing; the ball is 69 across X)
PHI0 = 5.0                    # each plate's arc runs PHI0..180-PHI0 degrees across (make_textures.py PHI0)
PHI_SEGS, THETA_SEGS = 7, 3
THICK = 2.5                   # the plates' thickness (their rear lip)
BALL_SPAN = 248.0             # the ball: plate centres spread over this many degrees round X (head and tail fill the rest)
ARCH_C = (0.0, 8.0, -15.0)    # standing: the plates' tops lie on an arch round this point ...
ARCH_R = 75.0                 # ... of this radius (top 60 high)
ARCH_FRONT, ARCH_BACK = 35.0, -35.0   # ... from this angle (front plate, degrees toward -Y) to this (back plate)
BODY_AT, BODY_SIZE = (0.0, 6.0, 25.0), (22.0, 33.0, 11.0)   # the soft body under the shell (an ellipsoid)
HEAD_AT = (0.0, -50.0, 25.0)  # the head joint
HEAD_BALL = (22.0, 175.0, 180.0)    # curled: the head's distance from the ball centre, its angle round X, its turn
LEG_Y = (-24.0, 0.0, 24.0)    # front, middle, back legs, along Y from the body's centre
LEG_FOLD, LEG_TUCK = 140.0, 40.0     # curled: legs fold under the body and lean toward its middle (degrees)
DIZZY_CURL = {"plate_0": 0.45, NECK: 0.85}  # dizzy: the ball with these hinges only part curled (front open, head out)
DIZZY_ROLL = -55.0            # ... rolled back this far (degrees round X), so the opening faces forward
LEAD = {NECK: 0.5}            # these hinges finish curling by this share of the curl (the head tucks in first)
LEG_LEAD = 0.6                # and the legs fold by this share
POINT2_UP = 22.0              # point1 (over the head) this far over the head joint
# Hit spheres (jfgformats 0.9: empties hit0.. under their bones; extras radius, percent = damage % (100 normal,
# never 255), weight = lock-on aim weight (0 never)): (name, bone, where, radius, percent, weight). "where" is one of
# hit_places()'s spots.
HITS = [("hit0", SPIN, "ball centre", 40, 100, 100),     # the body: standing 23 up, curled the ball's middle
        ("hit1", HEAD, "head", 14, 100, 40),
        ("hit2", PLATE_NAME.format(PLATES - 1), "weak spot", 16, 150, 20)]

HERE = Path(__file__).resolve().parent
TEX = HERE / "textures"
OUT = HERE / "models"
PREVIEW = HERE / "previews"

SIDES = "LR"
LEG_ROWS = "FMB"
MID = PLATES // 2


def side_sign(s):
    return 1.0 if s == "L" else -1.0                   # its left is +X (it faces -Y)


def antenna_base(s):
    return Vector(HEAD_AT) + Vector((4.5 * side_sign(s), -11.0, 7.0))


def leg_points(s, dy):
    """Hip, knee, ankle, foot: up and out from the body's side, then down to the floor."""
    k = side_sign(s)
    y = BODY_AT[1] + dy
    splay = dy * 0.25
    hip = Vector((17 * k, y, 22))
    knee = Vector((31 * k, y + splay * 0.6, 29))
    ankle = Vector((37 * k, y + splay * 0.9, 9))
    foot = Vector((40 * k, y + splay, 0))
    return hip, knee, ankle, foot


# ---- Standing (the rest pose) and curled: each shell part's frame in both.

def plate_radius(i):
    return BALL_R - PLATE_STEP * i


def plate_half(i):
    """Half a plate's span round X (degrees): its share of BALL_SPAN, plus an overlap with the next."""
    return BALL_SPAN / (PLATES - 1) / 2 + 4.0


def plate_angles(i):
    """(standing, curled) angle of plate i's middle round X, degrees, positive toward the front (-Y)."""
    t = i / (PLATES - 1)
    return ARCH_FRONT + (ARCH_BACK - ARCH_FRONT) * t, BALL_SPAN / 2 - BALL_SPAN * t


def lerp(a, b, t):
    return a + (b - a) * t


def direction(deg):
    a = math.radians(deg)
    return Vector((0.0, -math.sin(a), math.cos(a)))


def rot_x(deg):
    return Matrix.Rotation(math.radians(deg), 4, "X")


def rot_y(deg):
    return Matrix.Rotation(math.radians(deg), 4, "Y")


def rot_z(deg):
    return Matrix.Rotation(math.radians(deg), 4, "Z")


def about(point, m):
    """m (a 4x4 rotation) about point."""
    return Matrix.Translation(point) @ m @ Matrix.Translation(-Vector(point))


def plate_frame(i):
    """Plate i standing: built round the origin with its middle straight up, this puts it on the arch."""
    s, _ = plate_angles(i)
    return Matrix.Translation(Vector(ARCH_C) + direction(s) * (ARCH_R - plate_radius(i))) @ rot_x(s)


def ball_space():
    """The ball (built round the origin) in the root's space: centred where the middle plate's sphere stands, turned
    so the middle plate keeps its standing turn (it rides the body)."""
    s, b = plate_angles(MID)
    return Matrix.Translation(plate_frame(MID).to_translation()) @ rot_x(s - b)


def plate_ball(i):
    return ball_space() @ rot_x(plate_angles(i)[1])


def head_ball():
    d, g, turn = HEAD_BALL
    return ball_space() @ Matrix.Translation(direction(g) * d) @ rot_x(turn)


def root_ball():
    """The root's move in the ball: the ball centre up to (0, 0, BALL_Z), untilted."""
    return Matrix.Translation((0, 0, BALL_Z)) @ ball_space().inverted()


def hinge(parent_rest, parent_ball, child_rest, child_ball, fallback):
    """The child's move relative to its parent from standing to curled, which is a turn round X about one point
    (it is a rigid move in the YZ plane): (degrees, that point). A turn of nothing keeps the fallback point."""
    m = parent_rest @ parent_ball.inverted() @ child_ball @ child_rest.inverted()
    q = m.to_quaternion()
    ang = 2 * math.atan2(q.x, q.w)
    if abs(ang) < 1e-6:
        return 0.0, Vector(fallback)
    t = m.to_translation()
    r = Matrix.Rotation(ang, 3, "X")
    a = Matrix.Identity(3) - r                         # (I - R) p = t, in the YZ plane
    det = a[1][1] * a[2][2] - a[1][2] * a[2][1]
    return math.degrees(ang), Vector((0, (t.y * a[2][2] - a[1][2] * t.z) / det, (a[1][1] * t.z - a[2][1] * t.y) / det))


def shell_chain():
    """(bone, parent, curl degrees, joint) for the body, plates and neck, parents first: the middle plate on the
    body, the plates in front and behind each hanging from the next one in, the neck on the front plate."""
    ident = Matrix()
    rest = {BODY: ident, NECK: Matrix.Translation(HEAD_AT)}
    ball = {BODY: ident, NECK: head_ball()}
    for i in range(PLATES):
        rest[PLATE_NAME.format(i)] = plate_frame(i)
        ball[PLATE_NAME.format(i)] = plate_ball(i)
    links = [(PLATE_NAME.format(MID), BODY)]
    links += [(PLATE_NAME.format(i), PLATE_NAME.format(i + 1)) for i in range(MID - 1, -1, -1)]
    links += [(PLATE_NAME.format(i), PLATE_NAME.format(i - 1)) for i in range(MID + 1, PLATES)]
    links.append((NECK, PLATE_NAME.format(0)))
    out = [(SPIN, ROOT, 0.0, ball_space().to_translation()), (BODY, SPIN, 0.0, Vector(BODY_AT))]
    for child, parent in links:
        fallback = rest[child].to_translation()
        ang, at = hinge(rest[parent], ball[parent], rest[child], ball[child], fallback)
        out.append((child, parent, ang, at))
    return out


CHAIN = shell_chain()


def bone_table():
    """(name, parent, head) for every bone, parents first."""
    bones = [(ROOT, None, Vector())] + [(n, p, at) for n, p, _, at in CHAIN]
    bones.append((HEAD, NECK, Vector(HEAD_AT)))
    if ANTENNA_BONES:
        for s in SIDES:
            bones.append((ANTENNA_NAME.format(s), HEAD, antenna_base(s)))
    for r, dy in zip(LEG_ROWS, LEG_Y):
        for s in SIDES:
            bones.append((LEG_NAME.format(r, s), BODY, leg_points(s, dy)[0]))
    assert len(bones) <= MAX_BONES, f"{len(bones)} bones, over MAX_BONES {MAX_BONES}"
    return bones


def smooth(t):
    t = min(1.0, max(0.0, t))
    return t * t * (3 - 2 * t)


class Pose:
    """One pose's settings; transforms() turns them into each bone's move (armature space, applied to the rest
    geometry). Every bone but the root only turns about its joint."""

    def __init__(self, curl=0.0):
        self.curl = curl                  # 0 standing .. 1 the ball, on every hinge ...
        self.curl_at = {}                 # ... but these (bone -> curl)
        self.curl_add = {}                # bone -> curl added on its hinge (negative opens the shell: the flare)
        self.whole = Matrix()             # the root's own move (bob, rock, flip), on top of the curl's
        self.spin = 0.0                   # the ball rolling forward: degrees round X about its centre
        self.head = Matrix()              # the head's own turn about its joint
        self.legs = {}                    # leg name -> (forward swing, lift) degrees
        self.leg_fold = 0.0               # extra fold under the body (degrees, on top of the curl's)
        self.antennae = {s: (0.0, 0.0) for s in SIDES}   # (pitch down, yaw out) degrees
        self.ground = False               # lift/sink so its lowest point is on the floor (curl in-betweens)


def lead(c, by):
    """A hinge's curl at the whole curl c, when it finishes by the share by of it (eased, so it starts gently)."""
    return smooth(c / by) if by < 1 else c


def root_curl(c):
    """The root from standing to the ball's place: its rise and turn, shared out evenly along the curl."""
    m = root_ball()
    q = m.to_quaternion()
    return Matrix.Translation(m.to_translation() * c) @ Matrix.Rotation(2 * math.atan2(q.x, q.w) * c, 4, "X")


def transforms(p):
    c = p.curl
    out = {ROOT: root_curl(c)}
    for name, parent, ang, at in CHAIN:
        if name == SPIN:
            out[name] = out[parent] @ about(at, rot_x(p.spin))   # positive: the top rolls forward (-Y built)
            continue
        s = p.curl_at.get(name, lead(c, LEAD.get(name, 1.0))) + p.curl_add.get(name, 0.0)
        out[name] = out[parent] @ about(at, rot_x(ang * s))
    head = out[NECK] @ about(HEAD_AT, p.head)
    out[HEAD] = head
    tuck_head = p.curl_at.get(NECK, lead(c, LEAD.get(NECK, 1.0)))
    for s in SIDES:
        k = side_sign(s)
        pitch, yaw = p.antennae[s]
        m = head @ about(antenna_base(s), rot_z(yaw * k) @ rot_x(pitch + 80 * tuck_head))
        if ANTENNA_BONES:
            out[ANTENNA_NAME.format(s)] = m
    for r, dy in zip(LEG_ROWS, LEG_Y):
        for s in SIDES:
            name = LEG_NAME.format(r, s)
            k = side_sign(s)
            fwd, lift = p.legs.get(name, (0.0, 0.0))
            fc = lead(c, LEG_LEAD)
            tuck = {"F": -LEG_TUCK, "M": 0.0, "B": LEG_TUCK}[r] * fc   # folded, they point inward: to the middle
            hip = leg_points(s, dy)[0]
            fold = LEG_FOLD * fc + p.leg_fold
            out[name] = out[BODY] @ about(hip, rot_z(-k * (fwd - tuck)) @ rot_y(k * (fold - lift)))
    out = {n: p.whole @ m for n, m in out.items()}
    if p.ground:                                    # its lowest point to the floor (to the ball's, curled)
        g = Matrix.Translation((0, 0, -lowest(out) + lowest(transforms(Pose(1.0))) * c))
        out = {n: g @ m for n, m in out.items()}
    return out


PARTS = {}                                # bone name -> its rest vertices (filled by the build), for lowest()


def lowest(moves):
    return min((moves[b] @ v).z for b, vs in PARTS.items() for v in vs)


# ---- Building meshes.

def clear():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.context.scene.render.fps = FPS


MATS = {}


def material(name, image, blend=False, double=False):
    if name in MATS:
        return MATS[name]
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    nt = m.node_tree
    bsdf = nt.nodes.get("Principled BSDF")
    tex = nt.nodes.new("ShaderNodeTexImage")
    tex.image = bpy.data.images.load(str(TEX / image))
    tex.interpolation = "Closest"
    nt.links.new(tex.outputs["Color"], bsdf.inputs["Base Color"])
    # Emission so the preview looks as the game draws it (unlit by the scene's light).
    nt.links.new(tex.outputs["Color"], bsdf.inputs["Emission Color"])
    bsdf.inputs["Emission Strength"].default_value = 1.0
    bsdf.inputs["Roughness"].default_value = 1.0
    bsdf.inputs["Specular IOR Level"].default_value = 0.0
    if blend:
        nt.links.new(tex.outputs["Alpha"], bsdf.inputs["Alpha"])
        m.surface_render_method = "BLENDED"
    m.use_backface_culling = not double
    m["doubleSided"] = double
    MATS[name] = m
    return m


def white_colours(obj):
    attr = obj.data.color_attributes.new("Col", "BYTE_COLOR", "CORNER")
    for d in attr.data:
        d.color = (1.0, 1.0, 1.0, 1.0)


class Builder:
    """Faces into one bmesh with UVs and material slots; face() orients each face to a wanted outward direction."""

    def __init__(self, mats):
        self.bm = bmesh.new()
        self.uv = self.bm.loops.layers.uv.new("UVMap")
        self.mats = mats

    def face(self, pts, uvs, mat, out=None):
        f = self.bm.faces.new([self.bm.verts.new(p) for p in pts])
        f.material_index = mat
        for l, t in zip(f.loops, uvs):
            l[self.uv].uv = t
        f.normal_update()
        if out is not None and f.normal.dot(out) < 0:
            f.normal_flip()
        f.smooth = False
        return f

    def finish(self, name, bone=None):
        bmesh.ops.remove_doubles(self.bm, verts=self.bm.verts[:], dist=1e-4)
        bmesh.ops.triangulate(self.bm, faces=self.bm.faces[:])
        me = bpy.data.meshes.new(name)
        self.bm.to_mesh(me)
        self.bm.free()
        obj = bpy.data.objects.new(name, me)
        bpy.context.collection.objects.link(obj)
        for m in self.mats:
            me.materials.append(m)
        white_colours(obj)
        if bone:
            vg = obj.vertex_groups.new(name=bone)
            vg.add(range(len(me.vertices)), 1.0, "REPLACE")
            PARTS.setdefault(bone, []).extend(v.co.copy() for v in me.vertices)
        return obj


def strip_uv(k, s, t, top_half):
    """parts.png: strip k (0 lightest .. 3 darkest), s across it, t along it, in the legs' (top) or head's half."""
    v0 = 0.5 if top_half else 0.0
    return ((k + 0.1 + 0.8 * s) / 4, v0 + 0.05 + 0.4 * t)


def strip_for(n):
    return 0 if n.z > 0.55 else 1 if n.z > -0.1 else 2 if n.z > -0.6 else 3


def tube(b, path, mat, top_half, sides=4, up=Vector((0, 0, 1)), cap=False):
    """A tube along path [(point, rx, rz)]: rx sideways, rz along up (square for 4 sides, set 45 degrees off so a face
    looks up). A radius 0 point is a tip; cap closes the last ring. Each face takes its parts.png strip by facing."""
    rings = []
    for j, (p, rx, rz) in enumerate(path):
        p = Vector(p)
        fwd = (Vector(path[min(j + 1, len(path) - 1)][0]) - Vector(path[max(j - 1, 0)][0])).normalized()
        side = fwd.cross(up).normalized()
        u = side.cross(fwd).normalized()
        ring = []
        for i in range(sides):
            a = 2 * math.pi * (i + 0.5) / sides
            ring.append(p + side * math.cos(a) * rx + u * math.sin(a) * rz)
        rings.append(ring)
    n = len(path) - 1
    for j in range(n):
        for i in range(sides):
            k = (i + 1) % sides
            pts = [rings[j][i], rings[j][k], rings[j + 1][k], rings[j + 1][i]]
            mid = sum(pts, Vector()) / 4
            axis = Vector(path[j][0]).lerp(Vector(path[j + 1][0]), 0.5)
            out = mid - axis
            if path[j + 1][1] == 0:
                pts = pts[:3]
            nrm = (pts[1] - pts[0]).cross(pts[2] - pts[0])
            if nrm.dot(out) < 0:
                nrm = -nrm
            st = strip_for(nrm.normalized())
            uvs = [strip_uv(st, s, t, top_half) for s, t in ((0, j / n), (1, j / n), (1, (j + 1) / n), (0, (j + 1) / n))]
            b.face(pts, uvs[:len(pts)], mat, out)
    if cap:
        last = rings[-1]
        d = Vector(path[-1][0]) - Vector(path[-2][0])
        b.face(last, [strip_uv(2, 0.5 + 0.5 * math.cos(2 * math.pi * (i + 0.5) / sides),
                               0.5 + 0.5 * math.sin(2 * math.pi * (i + 0.5) / sides), top_half) for i in range(sides)],
               mat, d)


def lune_point(i, phi, theta, r):
    """A point on plate i's sphere (its own frame: built round the origin, its middle straight up)."""
    p, t = math.radians(phi), math.radians(theta)
    return Vector((r * math.cos(p) * X_SQUASH, -r * math.sin(p) * math.sin(t), r * math.sin(p) * math.cos(t)))


def build_plate(i, m_shell, m_parts, m_glow):
    """Plate i: its outside (shell.png, the slit half on the middle plate), its rear lip, a plain inside; the back
    plate also carries the glowing weak spot beyond its rear edge."""
    b = Builder([m_shell, m_parts, m_glow])
    R, h = plate_radius(i), plate_half(i)
    u0 = 0.5 if i == PLATES // 2 else 0.0
    phis = [PHI0 + (180 - 2 * PHI0) * k / PHI_SEGS for k in range(PHI_SEGS + 1)]
    thetas = [h - 2 * h * k / THETA_SEGS for k in range(THETA_SEGS + 1)]    # front edge to rear edge
    for a in range(PHI_SEGS):
        for t in range(THETA_SEGS):
            q = [(a, t), (a + 1, t), (a + 1, t + 1), (a, t + 1)]
            pts = [lune_point(i, phis[x], thetas[y], R) for x, y in q]
            uvs = [(u0 + 0.5 * x / PHI_SEGS, 1 - y / THETA_SEGS) for x, y in q]       # the lip: the last rows
            b.face(pts, uvs, 0, sum(pts, Vector()))
        # The rear lip, facing back.
        pa, pb = phis[a], phis[a + 1]
        pts = [lune_point(i, pa, -h, R), lune_point(i, pb, -h, R), lune_point(i, pb, -h, R - THICK),
               lune_point(i, pa, -h, R - THICK)]
        uvs = [(u0 + 0.5 * a / PHI_SEGS, 0.13), (u0 + 0.5 * (a + 1) / PHI_SEGS, 0.13),
               (u0 + 0.5 * (a + 1) / PHI_SEGS, 0.05), (u0 + 0.5 * a / PHI_SEGS, 0.05)]
        b.face(pts, uvs, 0, lune_point(i, 90, -h - 30, 1))
    # The inside: coarse (it only stops the eye seeing through the shell from below).
    for a in range(4):
        pa, pb = PHI0 + (180 - 2 * PHI0) * a / 4, PHI0 + (180 - 2 * PHI0) * (a + 1) / 4
        pts = [lune_point(i, pa, h, R - THICK), lune_point(i, pb, h, R - THICK), lune_point(i, pb, -h, R - THICK),
               lune_point(i, pa, -h, R - THICK)]
        b.face(pts, [strip_uv(3, s, t, True) for s, t in ((0, 0), (1, 0), (1, 1), (0, 1))], 1, -sum(pts, Vector()))
    if i == PLATES - 1:                                # the weak spot: a glowing pad curving on past the rear edge
        ws_phi = [30 + 120 * k / 4 for k in range(5)]
        ws_theta = [-h + 3, -h - 9, -h - 22]
        for a in range(4):
            for t in range(2):
                q = [(a, t), (a + 1, t), (a + 1, t + 1), (a, t + 1)]
                pts = [lune_point(i, ws_phi[x], ws_theta[y], R - 1.0) for x, y in q]
                uvs = [(x / 4, 1 - y / 2) for x, y in q]
                b.face(pts, uvs, 2, sum(pts, Vector()))
    obj = b.finish(PLATE_NAME.format(i))
    # Into its standing place (the rest pose).
    obj.data.transform(plate_frame(i))
    PARTS.setdefault(PLATE_NAME.format(i), []).extend(v.co.copy() for v in obj.data.vertices)
    vg = obj.vertex_groups.new(name=PLATE_NAME.format(i))
    vg.add(range(len(obj.data.vertices)), 1.0, "REPLACE")
    return obj


def build_body(m_belly):
    """The soft glowing body: an ellipsoid, poles front and back; u round it from the top, v front to back."""
    b = Builder([m_belly])
    c = Vector(BODY_AT)
    ax, ay, az = BODY_SIZE
    around, rings = 8, 5

    def pt(j, k):
        psi = math.pi * j / rings
        a = 2 * math.pi * k / around
        return c + Vector((ax * math.sin(psi) * math.sin(a), -ay * math.cos(psi), az * math.sin(psi) * math.cos(a)))

    for j in range(rings):
        for k in range(around):
            q = [(j, k), (j, k + 1), (j + 1, k + 1), (j + 1, k)]
            if j == 0:
                q = q[1:]
            elif j == rings - 1:
                q = q[:3]
            pts = [pt(*x) for x in q]
            uvs = [(x[1] / around, 1 - x[0] / rings) for x in q]
            b.face(pts, uvs, 0, sum(pts, Vector()) / len(pts) - c)
    return b.finish(BODY, BODY)


def build_head(m_parts, m_glow):
    """A low wedge of a head with a horn, two short tusks and two glowing eyes; the neck reaches back under the
    front plate."""
    b = Builder([m_parts, m_glow])
    h = Vector(HEAD_AT)
    tube(b, [(h + Vector((0, 14, -2)), 8, 7), (h + Vector((0, 2, 0)), 13, 9), (h + Vector((0, -10, -1)), 11, 8),
             (h + Vector((0, -16, -3)), 6, 5)], 0, False, cap=True)
    tube(b, [(h + Vector((0, -8, 6)), 3.2, 3.2), (h + Vector((0, -15, 8)), 2.0, 2.0), (h + Vector((0, -22, 11)), 0, 0)],
         0, False, sides=3, up=Vector((0, 1, 0)))
    for k in (1, -1):
        tube(b, [(h + Vector((5 * k, -15, -4)), 1.8, 1.8), (h + Vector((7 * k, -22, -5)), 0, 0)], 0, False, sides=3)
        e = h + Vector((8.3 * k, -10.5, 2.5))       # an eye on the head's front corner, facing out and forward
        out = Vector((k, -0.8, 0.2)).normalized()
        side = out.cross(Vector((0, 0, 1))).normalized()
        up = side.cross(out).normalized()
        pts = [e + side * 2.4 * x + up * 2.0 * y for x, y in ((-1, -1), (1, -1), (1, 1), (-1, 1))]
        b.face(pts, [(0.1, 0.1), (0.9, 0.1), (0.9, 0.9), (0.1, 0.9)], 1, out)
    if not ANTENNA_BONES:
        for s in SIDES:
            antenna(b, s, 0)
    return b.finish(HEAD, HEAD)


def antenna(b, s, mat):
    k = side_sign(s)
    a = antenna_base(s)
    tube(b, [(a, 1.3, 1.3), (a + Vector((5 * k, -9, 6)), 1.0, 1.0), (a + Vector((10 * k, -16, 14)), 0, 0)], mat, True,
         sides=3)


def build_antenna(m_parts, s):
    b = Builder([m_parts])
    antenna(b, s, 0)
    return b.finish(ANTENNA_NAME.format(s), ANTENNA_NAME.format(s))


def build_leg(m_parts, r, s, dy):
    b = Builder([m_parts])
    hip, knee, ankle, foot = leg_points(s, dy)
    tube(b, [(hip, 3.4, 3.4), (knee, 3.0, 3.0), (ankle, 2.2, 2.2), (foot, 0, 0)], 0, True)
    name = LEG_NAME.format(r, s)
    return b.finish(name, name)


def join(name, parts):
    bpy.ops.object.select_all(action="DESELECT")
    for p in parts:
        p.select_set(True)
    bpy.context.view_layer.objects.active = parts[0]
    bpy.ops.object.join()
    obj = bpy.context.view_layer.objects.active
    obj.name = name
    obj.data.name = name
    return obj


def point_places():
    """The attach points (name -> (bone, standing place)): the middle spine slit's centre (the fan's), over the
    head, and the middle of the glowing weak spot."""
    last = PLATES - 1
    return {
        POINTS[0]: (PLATE_NAME.format(MID), plate_frame(MID) @ lune_point(MID, 90, 0, plate_radius(MID))),
        POINTS[1]: (HEAD, Vector(HEAD_AT) + Vector((0, -4, POINT2_UP))),
        POINTS[2]: (PLATE_NAME.format(last), plate_frame(last) @ lune_point(last, 90, -plate_half(last) - 9,
                                                                             plate_radius(last) - 1.0)),
    }


def hit_places():
    """The hit spheres (name -> (bone, standing centre, radius, percent, weight))."""
    spots = {"ball centre": ball_space().to_translation(),          # the ball bone's joint: the curled ball's centre
             "head": Vector(HEAD_AT) + Vector((0, -4, 0)),          # the head's middle (neck to snout)
             "weak spot": point_places()[POINTS[2]][1]}
    return {name: (bone, spots[where], radius, percent, weight) for name, bone, where, radius, percent, weight in HITS}


def build_points(arm):
    """Empties parented to their bones, in place at the rest pose: the attach points, then the hit spheres (their
    radius, percent and weight as custom properties, exported as glTF extras)."""
    out = []
    hits = hit_places()
    places = {**point_places(), **{n: (h[0], h[1]) for n, h in hits.items()}}
    for name, (bone, at) in places.items():
        e = bpy.data.objects.new(name, None)
        e.empty_display_size = 4
        if name in hits:
            _, _, radius, percent, weight = hits[name]
            assert 0 <= percent < 255 and 0 <= weight <= 255, name
            e.empty_display_type = "SPHERE"
            e.empty_display_size = radius
            e["radius"], e["percent"], e["weight"] = float(radius), int(percent), int(weight)
        bpy.context.collection.objects.link(e)
        e.parent = arm
        e.parent_type = "BONE"
        e.parent_bone = bone
        bpy.context.view_layer.update()
        e.matrix_world = Matrix.Translation(FACE @ at)
        out.append(e)
    bpy.context.view_layer.update()
    for e, (_, at) in zip(out, places.values()):
        assert (e.matrix_world.to_translation() - FACE @ at).length < 1e-3, e.name
    return out


def build_armature():
    arm_data = bpy.data.armatures.new("shellback_rig")
    arm = bpy.data.objects.new("shellback_rig", arm_data)
    bpy.context.collection.objects.link(arm)
    bpy.context.view_layer.objects.active = arm
    bpy.ops.object.mode_set(mode="EDIT")
    for name, parent, head in bone_table():
        eb = arm_data.edit_bones.new(name)
        eb.head = FACE @ head
        eb.tail = FACE @ head + Vector((0, 0, BONE_LEN))
        eb.roll = 0.0
        if parent:
            eb.parent = arm_data.edit_bones[parent]
            eb.use_connect = False
    bpy.ops.object.mode_set(mode="OBJECT")
    return arm


def build_shellback():
    m_shell = material("shellback_shell", "shell.png")
    m_belly = material("shellback_belly", "belly.png")
    m_glow = material("shellback_glow", "glow.png")
    m_parts = material("shellback_parts", "parts.png")
    parts = [build_body(m_belly)]
    parts += [build_plate(i, m_shell, m_parts, m_glow) for i in range(PLATES)]
    parts.append(build_head(m_parts, m_glow))
    if ANTENNA_BONES:
        parts += [build_antenna(m_parts, s) for s in SIDES]
    parts += [build_leg(m_parts, r, s, dy) for r, dy in zip(LEG_ROWS, LEG_Y) for s in SIDES]
    mesh = join("shellback", parts)
    mesh.data.transform(FACE)
    arm = build_armature()
    mesh.parent = arm
    mod = mesh.modifiers.new("Armature", "ARMATURE")
    mod.object = arm
    return arm, mesh, build_points(arm)


# ---- The animations.

def legs_gait(t, turn=False):
    """A tripod gait at phase t (0..1 a cycle): front-left, middle-right and back-left step together, then the other
    three. Each leg lifts and swings forward through half the cycle and pushes back on the floor through the other.
    Turning, the right side strokes the other way, so it steps round on the spot."""
    out = {}
    for r in LEG_ROWS:
        for s in SIDES:
            group = (r in "FB") == (s == "L")
            ph = 2 * math.pi * (t + (0.0 if group else 0.5))
            fwd = -math.cos(ph) * (14.0 if r != "M" else 11.0)
            lift = max(0.0, math.sin(ph)) * 16.0
            if turn and s == "R":
                fwd = -fwd
            out[LEG_NAME.format(r, s)] = (fwd, lift)
    return out


def flare_out(amount):
    """Open every plate hinge by amount (a share of its curl, uncurling past standing): the plates fan up apart and
    the amber body shows between them. Negative clamps them shut."""
    return {PLATE_NAME.format(i): -amount for i in range(PLATES) if i != MID}


def anim_walk(f, n):
    t = f / n
    p = Pose()
    p.legs = legs_gait(t)
    bob = 1.3 * (0.5 - 0.5 * math.cos(4 * math.pi * t))
    p.whole = Matrix.Translation((0, 0, bob)) @ about((0, 0, 30), rot_y(1.5 * math.sin(2 * math.pi * t)))
    p.head = rot_z(4 * math.sin(2 * math.pi * t)) @ rot_x(2 * math.sin(4 * math.pi * t))
    for s in SIDES:
        p.antennae[s] = (6 * math.sin(4 * math.pi * t + (0 if s == "L" else 1)), 4 * math.sin(2 * math.pi * t))
    return p


def anim_turn(f, n):
    t = f / n
    p = Pose()
    p.legs = legs_gait(t, turn=True)
    p.whole = Matrix.Translation((0, 0, 1.0 * (0.5 - 0.5 * math.cos(4 * math.pi * t)))) @ rot_z(
        3 * math.sin(2 * math.pi * t))
    for s in SIDES:
        p.antennae[s] = (5 * math.sin(4 * math.pi * t), 8 * math.sin(2 * math.pi * t))
    return p


def anim_curl(f, n):
    p = Pose(smooth(f / n))
    p.ground = True
    return p


def anim_ball(f, n):
    """The closed ball rolling forward, one whole turn per loop (the game moves it; it can't spin the object)."""
    p = Pose(1.0)
    p.spin = 360.0 * f / n
    return p


def anim_dizzy(f, n):
    t = f / n
    p = Pose(1.0)                                       # the ball, its front hinges part open, the head out, lolling
    p.curl_at = dict(DIZZY_CURL)
    p.ground = True
    rock = 7 * math.sin(2 * math.pi * t)                # rocking side to side on its round back (rolling, not sliding)
    p.whole = Matrix.Translation((math.radians(rock) * BALL_Z, 0, 0)) @ about((0, 0, BALL_Z), rot_y(rock) @
                                                                              rot_x(DIZZY_ROLL))
    p.head = rot_y(25 * math.sin(2 * math.pi * t + 0.8)) @ rot_z(15 * math.sin(4 * math.pi * t))
    for s in SIDES:
        p.antennae[s] = (20 * math.sin(4 * math.pi * t + (0 if s == "L" else 2)), 15)
    for r_ in LEG_ROWS:
        for s in SIDES:
            p.legs[LEG_NAME.format(r_, s)] = (8 * math.sin(2 * math.pi * (2 * t + LEG_ROWS.index(r_) / 3)), 0)
    return p


def anim_uncurl(f, n):
    return anim_curl(n - f, n)


def anim_fire(f, n):
    p = Pose()
    if f <= FIRE_AT:                                    # brace: crouch, plates rising
        k = smooth(f / FIRE_AT)
        drop, flare, back, nod = -4 * k, 0.3 * k, 0.0, 8 * k
    else:                                               # the recoil, then settling back
        t = (f - FIRE_AT) / (n - FIRE_AT)
        kick = math.exp(-t * 5) * math.cos(t * 9)
        drop, flare = -4 * (1 - smooth(t)) + 2 * kick, 0.3 * (1 - smooth(t)) + 0.1 * kick
        back, nod = 6 * kick, -10 * kick + 8 * (1 - smooth(t))
    p.curl_add = flare_out(flare)
    p.whole = Matrix.Translation((0, back, drop)) @ about((0, 30, 0), rot_x(-back * 0.6))
    p.head = rot_x(nod)
    p.legs = {LEG_NAME.format(r, s): (0.0, -drop * 1.5) for r in LEG_ROWS for s in SIDES}
    for s in SIDES:
        p.antennae[s] = (-20 * min(1.0, f / FIRE_AT), 12)
    return p


def anim_hit(f, n):
    t = f / n
    k = min(1.0, f / 2.0) * (1 - smooth((f - 2) / (n - 2))) if f > 0 else 0.0
    p = Pose()
    p.whole = Matrix.Translation((0, 5 * k, 1.5 * k)) @ about((0, 30, 0), rot_x(-7 * k)) @ \
        rot_z(5 * k * math.sin(t * 9))
    p.curl_add = flare_out(-0.06 * k)                  # the plates clamp down
    p.head = rot_x(18 * k)
    p.legs = {LEG_NAME.format(r, s): (8 * k * (1 if r == "F" else -1), 10 * k) for r in LEG_ROWS for s in SIDES}
    for s in SIDES:
        p.antennae[s] = (40 * k, 15 * k)
    return p


def anim_death(f, n, settle_down=True):
    """Hops and rolls over onto its back (half a turn about Y), legs flailing and slowing, and settles with its shell
    on the floor, still for its last frames (10_dead holds the last)."""
    t = f / n
    flip = smooth(min(1.0, t / 0.45))
    hop = 18 * math.sin(math.pi * min(1.0, t / 0.45))
    land = max(0.0, t - 0.45) / 0.55
    settle = 3 * math.exp(-land * 8) * math.sin(land * 20) if t > 0.45 else 0.0
    p = Pose()
    down = -death_rest_height() * smooth(land) if settle_down else 0.0
    p.whole = Matrix.Translation((0, 0, hop + settle + down)) @ about((0, BODY_AT[1], 32), rot_y(180 * flip))
    twitch = max(0.0, 1 - land / 0.75)                   # gone by 80 % of the way
    p.legs = {LEG_NAME.format(r, s): (18 * twitch * math.sin(f * 1.9 + 2 * LEG_ROWS.index(r) + (s == "L")),
                                      20 * twitch * abs(math.sin(f * 1.3 + LEG_ROWS.index(r))))
              for r in LEG_ROWS for s in SIDES}
    p.leg_fold = 45 * smooth(land)
    p.head = rot_x(25 * flip)
    p.curl_add = flare_out(0.12 * math.sin(math.pi * min(1.0, t / 0.45)))
    for s in SIDES:
        p.antennae[s] = (50 * smooth(land), 20 * twitch * math.sin(f * 2.3))
    return p


_DEATH_REST = []


def death_rest_height():
    """How far the dead pose's lowest point is off the floor before it settles (measured once)."""
    if not _DEATH_REST:
        _DEATH_REST.append(lowest(transforms(anim_death(DEATH_FRAMES, DEATH_FRAMES, settle_down=False))))
    return _DEATH_REST[0]


def anim_idle(f, n):
    t = f / n
    p = Pose()
    p.curl_add = {PLATE_NAME.format(i): -0.03 * (0.5 - 0.5 * math.cos(2 * math.pi * t - 0.5 * i)) for i in range(PLATES)}
    p.whole = Matrix.Translation((0, 0, 0.6 * math.sin(2 * math.pi * t)))
    p.head = rot_z(5 * math.sin(2 * math.pi * t)) @ rot_x(3 * math.sin(4 * math.pi * t))
    for s in SIDES:
        k = 0 if s == "L" else 1.3
        p.antennae[s] = (10 * math.sin(4 * math.pi * t + k), 9 * math.sin(2 * math.pi * t + k))
    return p


ANIM_FUNCS = {"walk": anim_walk, "turn": anim_turn, "curl": anim_curl, "ball": anim_ball, "dizzy": anim_dizzy,
              "uncurl": anim_uncurl, "fire": anim_fire, "hit": anim_hit, "death": anim_death, "idle": anim_idle,
              "dead": lambda f, n: anim_death(DEATH_FRAMES, DEATH_FRAMES)}


def bake(arm, name, frames, fn):
    """Key every bone on every frame from fn's pose: a bone's basis is its move relative to its parent's. Only the
    root moves; the others only turn (their moves are built as turns about their joints), and nothing scales."""
    act = bpy.data.actions.new(name)
    if name in BLEND_FRAMES:
        act["blendFrames"] = BLEND_FRAMES[name]
    act.use_fake_user = True
    arm.animation_data_create()
    arm.animation_data.action = act
    bones = arm.data.bones
    parents = {b.name: (b.parent.name if b.parent else None) for b in bones}
    prev, first = {}, {}
    lows = []
    for f in range(frames + 1):
        built = transforms(fn(f, max(frames, 1)))
        lows.append(lowest(built))
        moves = {n: FACE @ m @ FACE.inverted() for n, m in built.items()}   # the same moves, turned to FORWARD
        for b in bones:
            local = b.matrix_local
            par = moves[parents[b.name]] if parents[b.name] else Matrix()
            basis = local.inverted() @ par.inverted() @ moves[b.name] @ local
            loc, rot, scale = basis.decompose()
            assert b.name == ROOT or loc.length < 1e-3, (name, f, b.name, loc)
            assert (scale - Vector((1, 1, 1))).length < 1e-4, (name, f, b.name, scale)
            if b.name in prev:
                rot.make_compatible(prev[b.name])
            if f == 0:
                first[b.name] = rot.copy()
            elif f == frames and name.endswith("_loop") and abs(rot.dot(first[b.name])) > 0.99999:
                rot = first[b.name].copy()                 # a loop ends on its first key exactly (a whole turn's
            prev[b.name] = rot                             # quaternion comes out negated otherwise)
            pb = arm.pose.bones[b.name]
            pb.rotation_mode = "QUATERNION"
            pb.rotation_quaternion = rot
            pb.keyframe_insert("rotation_quaternion", frame=f, group=b.name)
            if b.name == ROOT:
                pb.location = loc
                pb.keyframe_insert("location", frame=f, group=b.name)
    for fc in fcurves(act):
        for k in fc.keyframe_points:
            k.interpolation = "LINEAR"
    track = arm.animation_data.nla_tracks.new()
    track.name = name
    track.strips.new(name, 0, act)
    track.mute = True
    arm.animation_data.action = None
    return act, min(lows), max(lows)


def fcurves(act):
    """An action's F-curves (Blender 5 keeps them in layered channelbags)."""
    if hasattr(act, "fcurves") and len(getattr(act, "fcurves", [])):
        return list(act.fcurves)
    out = []
    for layer in getattr(act, "layers", []):
        for strip in layer.strips:
            for bag in strip.channelbags:
                out.extend(bag.fcurves)
    return out


# ---- The static models.

def lathe_y(b, profile, sides, mat, u_repeat=1.0):
    """A surface of revolution about Y: profile [(r, y, v)] tip to base, u round it, outward faces."""
    for j in range(len(profile) - 1):
        (r0, y0, v0), (r1, y1, v1) = profile[j], profile[j + 1]
        for i in range(sides):
            a0, a1 = 2 * math.pi * i / sides, 2 * math.pi * (i + 1) / sides
            q = [(r0, y0, a0, v0), (r0, y0, a1, v0), (r1, y1, a1, v1), (r1, y1, a0, v1)]
            if r0 == 0:
                q = q[1:]
            elif r1 == 0:
                q = q[:3]
            pts = [Vector((r * math.cos(a), y, r * math.sin(a))) for r, y, a, _ in q]
            uvs = [(a / (2 * math.pi) * u_repeat, 1 - v) for _, _, a, v in q]
            mid = sum(pts, Vector()) / len(pts)
            b.face(pts, uvs, mat, Vector((mid.x, 0, mid.z)))


def build_spine():
    b = Builder([material("spine_core", "spine.png"), material("spine_glow_blend", "spine_glow.png", True, True)])
    lathe_y(b, [(0, -12, 0.0), (1.6, -4, 0.35), (1.9, 4, 0.7), (0.9, 10, 0.95), (0, 12, 1.0)], 6, 0)
    lathe_y(b, [(0, -15, 0.0), (4.5, -4, 0.35), (4.5, 6, 0.7), (0, 14, 1.0)], 6, 1, 2.0)
    spine = b.finish("spine")
    spine.data.transform(FACE)
    return spine


def build_spark():
    """Twenty rays out of an icosahedron's faces (their bases pulled in, lengths ragged) round a white-hot core."""
    b = Builder([material("spark_blend", "spark.png", True, True)])
    ico = bmesh.new()
    bmesh.ops.create_icosphere(ico, subdivisions=1, radius=3)
    faces = [[v.co.copy() for v in f.verts] for f in ico.faces]
    ico.free()
    for n, tri in enumerate(faces):
        c = sum(tri, Vector()) / 3
        base = [c + (p - c) * 0.5 for p in tri]
        tip = c.normalized() * (13 + 3 * math.sin(n * 2.4))
        for a, z in ((0, 1), (1, 2), (2, 0)):
            b.face([base[a], base[z], tip], [(0, 1), (1, 1), (0.5, 0)], 0)
    for x in (1, -1):                                   # the core: an octahedron, all at the ray's bright base
        for y in (1, -1):
            for z in (1, -1):
                pts = [Vector((4 * x, 0, 0)), Vector((0, 4 * y, 0)), Vector((0, 0, 4 * z))]
                b.face(pts, [(0.4, 0.97), (0.6, 0.97), (0.5, 0.9)], 0, Vector((x, y, z)))
    return b.finish("spark")


def build_dizzy():
    """Four stars on a ring of radius 15, each three crossed quads (so it reads from any side), 10 across."""
    b = Builder([material("star_blend", "star.png", True, True)])
    for k in range(4):
        a = 2 * math.pi * k / 4
        c = Vector((15 * math.cos(a), 15 * math.sin(a), 2 * math.sin(2 * a)))
        tangent = Vector((-math.sin(a), math.cos(a), 0))
        radial = Vector((math.cos(a), math.sin(a), 0))
        for e1, e2 in ((tangent, Vector((0, 0, 1))), (radial, Vector((0, 0, 1))), (tangent, radial)):
            pts = [c + (e1 * x + e2 * y) * 5 for x, y in ((-1, -1), (1, -1), (1, 1), (-1, 1))]
            b.face(pts, [(0, 0), (1, 0), (1, 1), (0, 1)], 0)
    return b.finish("dizzy")


def build_dust():
    """A low ring on the floor: inner edge 8 out and 1 up, a puffy crest 16 out and 6 up, outer edge 25 out."""
    b = Builder([material("dust_blend", "dust.png", True, True)])
    rings = [(8, 1, 0.0), (16, 6, 0.5), (25, 2, 1.0)]
    seg = 12
    for j in range(len(rings) - 1):
        (r0, z0, v0), (r1, z1, v1) = rings[j], rings[j + 1]
        for i in range(seg):
            a0, a1 = 2 * math.pi * i / seg, 2 * math.pi * (i + 1) / seg
            pts = [Vector((r0 * math.cos(a0), r0 * math.sin(a0), z0)), Vector((r0 * math.cos(a1), r0 * math.sin(a1), z0)),
                   Vector((r1 * math.cos(a1), r1 * math.sin(a1), z1)), Vector((r1 * math.cos(a0), r1 * math.sin(a0), z1))]
            u0, u1 = i / seg * 3, (i + 1) / seg * 3
            b.face(pts, [(u0, 1 - v0), (u1, 1 - v0), (u1, 1 - v1), (u0, 1 - v1)], 0, Vector((0, 0, 1)))
    return b.finish("dust")


# ---- Export, report, previews.

def export(objs, name, animations=False):
    OUT.mkdir(exist_ok=True)
    bpy.ops.object.select_all(action="DESELECT")
    for o in objs:
        o.select_set(True)
    kw = dict(filepath=str(OUT / (name + ".glb")), export_format="GLB", use_selection=True, export_yup=True,
              export_apply=False, export_vertex_color="ACTIVE", export_extras=True, export_image_format="AUTO",
              export_animations=animations)
    if animations:
        kw.update(export_animation_mode="ACTIONS", export_optimize_animation_size=False, export_force_sampling=False,
                  export_anim_slide_to_zero=False, export_def_bones=False, export_skins=True)
    bpy.ops.export_scene.gltf(**kw)


def glvec(v):
    return (v.x, v.z, -v.y)


def tris(obj):
    return sum(len(p.vertices) - 2 for p in obj.data.polygons)


def set_pose(arm, name, frame):
    ad = arm.animation_data
    ad.action = bpy.data.actions[name]
    if hasattr(ad, "action_slot") and ad.action_slot is None and len(ad.action.slots):
        ad.action_slot = ad.action.slots[0]
    bpy.context.scene.frame_set(frame)


def render(path, loc, target, lens, size):
    scene = bpy.context.scene
    cam = scene.camera
    cam.location = loc
    cam.rotation_euler = (Vector(target) - Vector(loc)).to_track_quat("-Z", "Y").to_euler()
    cam.data.lens = lens
    scene.render.resolution_x, scene.render.resolution_y = size
    scene.render.filepath = str(path)
    bpy.ops.render.render(write_still=True)


def preview(arm, mesh, statics):
    PREVIEW.mkdir(exist_ok=True)
    scene = bpy.context.scene
    scene.render.engine = "BLENDER_EEVEE"
    scene.render.film_transparent = False
    world = bpy.data.worlds.new("w")
    world.use_nodes = True
    world.node_tree.nodes["Background"].inputs[0].default_value = (0.12, 0.13, 0.1, 1)
    scene.world = world
    cam = bpy.data.objects.new("cam", bpy.data.cameras.new("cam"))
    bpy.context.collection.objects.link(cam)
    scene.camera = cam
    # A floor grid to read the height against (not exported: it's made after the exports).
    bpy.ops.mesh.primitive_plane_add(size=400, location=(0, 0, -0.05))
    floor = bpy.context.active_object
    fm = bpy.data.materials.new("floor")
    fm.use_nodes = True
    fm.node_tree.nodes["Principled BSDF"].inputs["Base Color"].default_value = (0.05, 0.055, 0.05, 1)
    floor.data.materials.append(fm)
    sun = bpy.data.objects.new("sun", bpy.data.lights.new("sun", "SUN"))
    sun.data.energy = 2.0
    bpy.context.collection.objects.link(sun)
    for o in statics.values():
        o.hide_render = True
    three_q = ((-150, -175, 110), (0, 0, 28))
    side = ((-260, 0, 45), (0, 0, 30))
    for pose, frame, shots in (("00_idle_loop", 0, {"standing": three_q, "standing_side": side}),
                               ("03_curl", 8, {"curling": three_q}),
                               ("04_ball_loop", 0, {"curled": ((-110, -150, 80), (0, 0, 36))}),
                               ("05_dizzy_loop", 7, {"dizzy": ((-120, -150, 85), (0, 0, 32))}),
                               ("07_fire", FIRE_AT, {"fire": three_q}),
                               ("09_death", DEATH_FRAMES, {"death": three_q})):
        set_pose(arm, pose, frame)
        for nm, (loc, tgt) in shots.items():
            render(PREVIEW / (nm + ".png"), FACE @ Vector(loc), FACE @ Vector(tgt), 40, (800, 600))
    arm.animation_data.action = None
    scene.frame_set(0)
    # The static models in a row, each scaled to read.
    mesh.hide_render = True
    floor.hide_render = True
    for (name, o), x, s in zip(statics.items(), (-90, -30, 30, 90), (2.0, 1.4, 1.2, 1.0)):
        o.hide_render = False
        o.location = (x, 0, 25)
        o.scale = (s, s, s)
    statics["spine"].rotation_euler = (0, 0, math.radians(60))
    statics["dizzy"].rotation_euler = (math.radians(30), 0, 0)
    statics["dust"].rotation_euler = (math.radians(35), 0, 0)
    render(PREVIEW / "models.png", (0, -260, 40), (0, 0, 25), 35, (1200, 400))


def build():
    clear()
    arm, mesh, points = build_shellback()
    report = {"anims": {}}
    for name, kind, frames in ANIMS:
        _, lo, hi = bake(arm, name, frames, ANIM_FUNCS[kind])
        report["anims"][name] = (frames, lo, hi)
    statics = {"spine": build_spine(), "spark": build_spark(), "dizzy": build_dizzy(), "dust": build_dust()}
    export([arm, mesh, *points], "shellback", animations=True)
    for name, o in statics.items():
        export([o], name)
    print("SHELLBACK bones (name, parent, head blender xyz, head glTF xyz):")
    for name, parent, head in bone_table():
        head = FACE @ head
        print("  %-10s %-8s (%6.1f, %6.1f, %6.1f)  (%6.1f, %6.1f, %6.1f)" % (name, parent or "-", *head, *glvec(head)))
    print("SHELLBACK tris: shellback %d, " % tris(mesh) + ", ".join("%s %d" % (n, tris(o)) for n, o in statics.items()))
    print("SHELLBACK materials:", [m.name for m in mesh.data.materials])
    print("SHELLBACK hinges (bone, curl degrees standing -> ball):",
          ", ".join("%s %.1f" % (n, a) for n, _, a, _ in CHAIN))
    print("SHELLBACK anims (frames at %d fps, lowest point min/max over the frames):" % FPS)
    for name, (frames, lo, hi) in report["anims"].items():
        print("  %-13s %3d frames (%d keys, %.2f s)  lowest %.1f .. %.1f" % (name, frames, frames + 1, frames / FPS,
                                                                           lo, hi))
    for name, (bone, at) in point_places().items():
        at = FACE @ at
        print("SHELLBACK %s on %s at blender (%.1f, %.1f, %.1f), glTF (%.1f, %.1f, %.1f)" % (name, bone, *at, *glvec(at)))
    for name, (bone, at, radius, percent, weight) in hit_places().items():
        at = FACE @ at
        print("SHELLBACK %s on %s at blender (%.1f, %.1f, %.1f), glTF (%.1f, %.1f, %.1f), radius %g, percent %d, weight %d"
              % (name, bone, *at, *glvec(at), radius, percent, weight))
    co = [v.co for v in mesh.data.vertices]
    lo = [min(c[i] for c in co) for i in range(3)]
    hi = [max(c[i] for c in co) for i in range(3)]
    print("SHELLBACK standing bounds, blender: min (%.1f, %.1f, %.1f) max (%.1f, %.1f, %.1f)" % (*lo, *hi))
    ball = transforms(Pose(1.0))
    pts = [ball[b] @ v for b, vs in PARTS.items() for v in vs]
    c = Vector((0, 0, BALL_Z))
    print("SHELLBACK ball: lowest z %.1f, highest %.1f, furthest from (0,0,%g): %.1f, y %.1f..%.1f, x %.1f..%.1f"
          % (min(p.z for p in pts), max(p.z for p in pts), BALL_Z, max((p - c).length for p in pts),
             min(p.y for p in pts), max(p.y for p in pts), min(p.x for p in pts), max(p.x for p in pts)))
    worst = sorted(((max((ball[b] @ v - c).length for v in vs), b) for b, vs in PARTS.items()), reverse=True)[:4]
    print("SHELLBACK ball, furthest parts from its centre:", ", ".join("%s %.1f" % (b, d) for d, b in worst))
    mid = PLATES // 2
    f = plate_frame(mid)
    for u in (0.30, 0.5, 0.70):                        # make_textures.py's slit columns
        phi = PHI0 + (180 - 2 * PHI0) * u
        p = f @ lune_point(mid, phi, 0, plate_radius(mid))
        n = (f.to_3x3() @ Vector((math.cos(math.radians(phi)), 0, math.sin(math.radians(phi))))).normalized()
        p, n = FACE @ p, FACE.to_3x3() @ n
        print("SHELLBACK slit (standing) at glTF (%.1f, %.1f, %.1f), facing (%.2f, %.2f, %.2f)" % (*glvec(p), *glvec(n)))
    # Keep the rest pose in the saved file.
    arm.animation_data.action = None
    bpy.ops.wm.save_as_mainfile(filepath=str(HERE / "shellback.blend"))
    preview(arm, mesh, statics)
    bpy.ops.wm.save_as_mainfile(filepath=str(HERE / "shellback.blend"))


build()
