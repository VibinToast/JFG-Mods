"""Concussion Cannon's four models, built in Blender from textures/*.png (make_textures.py), saved as concussion.blend
and exported as models/*.glb, with preview renders in previews/. Low-poly, as the game's own objects.

    "C:/Program Files/Blender Foundation/Blender 5.2/blender.exe" --background --factory-startup --python build_models.py

- cannon:  (with an empty node "barrel" at the muzzle tip: the shot origin) the held weapon: an 8-sided barrel (rear cap, body with a glowing core window, three coils, a flared
           muzzle with a glowing mouth), a raked grip under its rear and a sight. Built muzzle along -Y, top +Z, 30
           long; then turned and scaled into the hand's frame by the constants below: the grip centre at the origin
           (the game draws the held gun with the hero's hand-joint matrix, in the hero's model units, as its own
           guns; the object's scale isn't used). ~280 tris.
- wave:    the cone shockwave: three nested open cones, apex at the origin, opening along -Y (forward), 100 long,
           35 degrees half-angle outside; the mod scales and fades it. ~190 tris.
- charge:  the charge orb at the muzzle: a bright core (radius 4) in a crackling glow shell (radius 6).
- impact:  the wall-slam burst: twenty spikes (to radius ~15) out of a soft puff (radius 8).
Blender's Z is up and 1 unit is 1 game unit; the glTF export turns it to the game's Y up (glTF = (x, z, -y)). All
vertex colours are white (the game lights these by vertex colour only, so the cannon's light is baked in its
textures); see-through materials blend and are double-sided.
"""
import math
from pathlib import Path

import bmesh
import bpy
from mathutils import Matrix, Vector

# The cannon in the hand's frame, in glTF/game coordinates (Y up), as the stock hand guns (their grip at the origin,
# aiming along about (0.72..0.78, -0.36, -0.50..-0.60), 66 to 78 from grip to muzzle). Change them and re-run.
AIM = (0.75, -0.36, -0.55)    # from the grip centre to the muzzle tip
UP = (0.0, 1.0, 0.0)          # roughly the cannon's top (made square to AIM): the grip hangs the other way
LENGTH = 70.0                 # grip centre to muzzle tip
SCALE = 1.0                   # an extra uniform scale on top of LENGTH
GIRTH = 0.6                   # the barrel's thickness (and the grip's), against the built model's chunky 1.0
GRIP_OFFSET = (0.0, 0.0, 0.0) # where the grip centre lands

SIDES = 8                     # the barrel's sides (make_textures.py bakes a light per side: keep them equal)
AXIS_Z = 5.0                  # the barrel axis above the grip centre (built units)
REAR, MUZZLE = 7.0, -23.0     # the barrel's ends along Y (built units: 30 long)
GRIP_Y = 5.0                  # the grip centre along Y, under the rear (built units), so little sticks out behind it

HERE = Path(__file__).resolve().parent
TEX = HERE / "textures"
OUT = HERE / "models"
PREVIEW = HERE / "previews"


def clear():
    bpy.ops.wm.read_factory_settings(use_empty=True)


def material(name, image, blend=False, double=False):
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
    if blend:
        nt.links.new(tex.outputs["Alpha"], bsdf.inputs["Alpha"])
        m.surface_render_method = "BLENDED"
    m.use_backface_culling = not double
    m["doubleSided"] = double
    return m


def white_colours(obj, rgb=(1.0, 1.0, 1.0)):
    attr = obj.data.color_attributes.new("Col", "BYTE_COLOR", "CORNER")
    for d in attr.data:
        d.color = (*rgb, 1.0)


def mesh_object(name, bm, mats):
    me = bpy.data.meshes.new(name)
    bm.to_mesh(me)
    bm.free()
    obj = bpy.data.objects.new(name, me)
    bpy.context.collection.objects.link(obj)
    for m in mats:
        me.materials.append(m)
    return obj


def triangulate(obj):
    bm = bmesh.new()
    bm.from_mesh(obj.data)
    bmesh.ops.triangulate(bm, faces=bm.faces[:])
    bm.to_mesh(obj.data)
    bm.free()


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


def lathe(name, segments, mats, sides=SIDES, axis_z=0.0):
    """A surface of revolution about the Y axis (at height axis_z). segments: ((r0, y0), (r1, y1), material index,
    v0, v1), traced rear to front along the outside (then back in through the muzzle), so each band faces the
    profile's left: outward on the outside, forward on the end faces, inward in the mouth. u = i / sides around,
    angle 90 degrees on top; texture v from v0 (top row) to v1."""
    bm = bmesh.new()
    uv = bm.loops.layers.uv.new("UVMap")

    def pos(r, y, i):
        a = 2 * math.pi * i / sides
        return Vector((r * math.cos(a), y, axis_z + r * math.sin(a)))

    for (r0, y0), (r1, y1), mi, v0, v1 in segments:
        want2 = (-(y1 - y0), r1 - r0)                  # the band's facing in the profile (radial, along Y)
        for i in range(sides):
            corners = [(r0, y0, i, v0), (r0, y0, i + 1, v0), (r1, y1, i + 1, v1), (r1, y1, i, v1)]
            if r0 == 0:
                corners = corners[1:]
            elif r1 == 0:
                corners = corners[:3]
            verts = [bm.verts.new(pos(r, y, k)) for r, y, k, _ in corners]
            f = bm.faces.new(verts)
            f.material_index = mi
            for l, (_, _, k, v) in zip(f.loops, corners):
                l[uv].uv = (k / sides, 1 - v)
            f.normal_update()
            mid = 2 * math.pi * (i + 0.5) / sides
            want = Vector((want2[0] * math.cos(mid), want2[1], want2[0] * math.sin(mid)))
            if f.normal.dot(want) < 0:
                f.normal_flip()
            f.smooth = False
    bmesh.ops.remove_doubles(bm, verts=bm.verts[:], dist=1e-5)
    return mesh_object(name, bm, mats)


def box(name, centre, size, mat, rot_x=0.0):
    """A box with grip.png's strips by facing: top the lightest, the sides, front/back, the bottom the darkest."""
    bm = bmesh.new()
    uv = bm.loops.layers.uv.new("UVMap")
    bmesh.ops.create_cube(bm, size=1.0)
    bmesh.ops.scale(bm, vec=Vector(size), verts=bm.verts)
    bmesh.ops.rotate(bm, cent=Vector(), matrix=Matrix.Rotation(rot_x, 3, "X"), verts=bm.verts)
    bmesh.ops.translate(bm, vec=Vector(centre), verts=bm.verts)
    up = Matrix.Rotation(rot_x, 3, "X") @ Vector((0, 0, 1))
    side = Vector((1, 0, 0))
    for f in bm.faces:
        f.normal_update()
        n = f.normal
        strip = 0 if n.dot(up) > 0.7 else 3 if n.dot(up) < -0.7 else 1 if abs(n.dot(side)) > 0.7 else 2
        # The face's two in-plane axes, to spread its corners over its strip.
        a = (up if abs(n.dot(up)) < 0.7 else side).cross(n).normalized()
        b = n.cross(a)
        ps = [l.vert.co for l in f.loops]
        ua = [p.dot(a) for p in ps]
        vb = [p.dot(b) for p in ps]
        for l, s_, t_ in zip(f.loops, ua, vb):
            s = (s_ - min(ua)) / max(1e-6, max(ua) - min(ua))
            t = (t_ - min(vb)) / max(1e-6, max(vb) - min(vb))
            l[uv].uv = ((strip + 0.1 + 0.8 * s) / 4, t)
    return mesh_object(name, bm, [mat])


def gltf_to_blender(v):
    return Vector((v[0], -v[2], v[1]))


def hand_matrix():
    """Built frame (muzzle -Y, top +Z) to the hand's: the grip centre to the origin, the grip-to-muzzle-tip line
    along AIM, the top toward UP, thinned by GIRTH and scaled to LENGTH."""
    def basis(f, u):
        f = f.normalized()
        u = (u - f * u.dot(f)).normalized()
        return Matrix((u.cross(f), f, u)).transposed()  # columns: right, forward, up
    girth = Matrix.Diagonal((GIRTH, 1, GIRTH, 1))
    tip = (girth @ Vector((0, MUZZLE - GRIP_Y, AXIS_Z, 1))).to_3d()
    built = basis(tip, Vector((0, 0, 1)))
    hand = basis(gltf_to_blender(AIM), gltf_to_blender(UP))
    rot = hand @ built.transposed()
    k = LENGTH / tip.length * SCALE
    return (Matrix.Translation(gltf_to_blender(GRIP_OFFSET)) @ rot.to_4x4() @ Matrix.Scale(k, 4)
            @ girth @ Matrix.Translation((0, -GRIP_Y, 0)))


def build_cannon():
    m_metal = material("cannon_metal", "metal.png")
    m_coil = material("cannon_coil", "coil.png")
    m_core = material("cannon_core", "core.png")
    m_mouth = material("cannon_mouth", "muzzle.png")
    METAL, COIL, CORE, MOUTH = range(4)
    segs = [
        ((0.0, REAR), (3.4, REAR), METAL, 0.0, 0.12),          # rear cap
        ((3.4, REAR), (3.4, 1.0), METAL, 0.12, 0.62),           # body
        ((3.4, 1.0), (2.7, 0.4), METAL, 0.62, 0.66),
        ((2.7, 0.4), (2.7, -4.0), CORE, 0.0, 1.0),              # the glowing core window
        ((2.7, -4.0), (3.4, -4.6), METAL, 0.66, 0.7),
        ((3.4, -4.6), (3.4, -6.0), METAL, 0.7, 0.8),
    ]
    y, r = -6.0, 3.4
    for _ in range(3):                                          # the coils: a ridge each
        segs.append(((r, y), (4.6, y - 0.8), COIL, 0.0, 0.5))
        segs.append(((4.6, y - 0.8), (3.3, y - 1.6), COIL, 0.5, 1.0))
        y, r = y - 1.6, 3.3
    segs += [
        ((3.3, y), (3.0, -14.0), METAL, 0.0, 0.3),              # barrel
        ((3.0, -14.0), (7.0, MUZZLE), METAL, 0.3, 1.0),         # the flare
        ((7.0, MUZZLE), (5.8, MUZZLE), COIL, 0.3, 0.7),         # the lip, glowing
        ((5.8, MUZZLE), (1.6, -18.0), MOUTH, 0.0, 1.0),         # into the mouth
        ((1.6, -18.0), (0.0, -18.0), MOUTH, 1.0, 1.0),          # its throat
    ]
    barrel = lathe("cannon_barrel", segs, [m_metal, m_coil, m_core, m_mouth], axis_z=AXIS_Z)
    m_grip = material("cannon_grip", "grip.png")
    grip = box("cannon_grip", (0, GRIP_Y, 0), (2.6, 3.4, 8.5), m_grip, rot_x=math.radians(15))
    sight = box("cannon_sight", (0, 1.5, AXIS_Z + 3.6), (1.6, 8.0, 1.4), m_grip)
    for o in (barrel, grip, sight):
        white_colours(o)
    cannon = join("cannon", [barrel, grip, sight])
    cannon.data.transform(hand_matrix())
    triangulate(cannon)
    return cannon


def cone(name, half_angle, length, segments, stations, mat, u_repeat=1.0, turn=0.0):
    """An open cone, apex at the origin, opening along -Y, flaring a little toward its end (its half-angle reached at
    the end). stations: distances along it for the rings. u around (u_repeat times), texture top row at the apex."""
    bm = bmesh.new()
    uv = bm.loops.layers.uv.new("UVMap")
    tan = math.tan(math.radians(half_angle))
    rings = []
    for d in stations:
        r = tan * d * (0.85 + 0.15 * d / length)
        rings.append([bm.verts.new((r * math.cos(2 * math.pi * (i / segments + turn)), -d,
                                    r * math.sin(2 * math.pi * (i / segments + turn)))) for i in range(segments)])
    for j in range(len(stations) - 1):
        v0, v1 = stations[j] / length, stations[j + 1] / length
        for i in range(segments):
            k = (i + 1) % segments
            f = bm.faces.new((rings[j][i], rings[j][k], rings[j + 1][k], rings[j + 1][i]))
            u0, u1 = i / segments * u_repeat, (i + 1) / segments * u_repeat
            for l, (u, v) in zip(f.loops, ((u0, v0), (u1, v0), (u1, v1), (u0, v1))):
                l[uv].uv = (u, 1 - v)
    return mesh_object(name, bm, [mat])


def ring(name, radii, segments, mat, y=0.0, u_repeat=1.0, turn=0.0):
    """A flat ring in Blender's XZ plane (facing along Y: the shot's direction once turned by its yaw), radii from the
    inside out; the texture's v runs from the inner edge (top row) to the outer edge, so its rim is the ring's edge."""
    bm = bmesh.new()
    uv = bm.loops.layers.uv.new("UVMap")
    r0, r1 = radii[0], radii[-1]
    rings = [[bm.verts.new((r * math.cos(2 * math.pi * (i / segments + turn)), y,
                            r * math.sin(2 * math.pi * (i / segments + turn)))) for i in range(segments)] for r in radii]
    for j in range(len(radii) - 1):
        v0, v1 = (radii[j] - r0) / (r1 - r0), (radii[j + 1] - r0) / (r1 - r0)
        for i in range(segments):
            k = (i + 1) % segments
            f = bm.faces.new((rings[j][i], rings[j][k], rings[j + 1][k], rings[j + 1][i]))
            u0, u1 = i / segments * u_repeat, (i + 1) / segments * u_repeat
            for l, (u, v) in zip(f.loops, ((u0, v0), (u1, v0), (u1, v1), (u0, v1))):
                l[uv].uv = (u, 1 - v)
    return mesh_object(name, bm, [mat])


def build_wave():
    """The blast: a shock ring facing along the shot (the mod grows it as it flies and fades it out), two rings a little
    apart for some depth, see-through in the middle with a bright outer rim."""
    m_wave = material("wave_blend", "wave.png", blend=True, double=True)
    m_wave2 = material("wave2_blend", "wave2.png", blend=True, double=True)
    outer = ring("wave_outer", (12, 30, 48, 60), 16, m_wave, y=0.0, u_repeat=2)
    inner = ring("wave_inner", (8, 24, 40, 50), 16, m_wave2, y=-6.0, u_repeat=3, turn=0.5 / 16)
    for o in (outer, inner):
        white_colours(o)
    wave = join("wave", [outer, inner])
    triangulate(wave)
    return wave


def uv_sphere(name, radius, segments, rings, mat, u_repeat=1.0):
    bm = bmesh.new()
    uv = bm.loops.layers.uv.new("UVMap")              # calc_uvs fills the layer that exists
    bmesh.ops.create_uvsphere(bm, u_segments=segments, v_segments=rings, radius=radius, calc_uvs=True)
    for f in bm.faces:
        f.smooth = False
        for l in f.loops:
            l[uv].uv = (l[uv].uv.x * u_repeat, l[uv].uv.y)
    return mesh_object(name, bm, [mat])


def build_charge():
    core = uv_sphere("charge_core", 4, 8, 6, material("charge_core", "orb.png"))
    shell = uv_sphere("charge_glow", 6, 10, 6, material("charge_glow_blend", "orb_glow.png", blend=True, double=True),
                      u_repeat=2)
    shell.rotation_euler = (math.radians(25), 0, math.radians(15))
    for o in (core, shell):
        white_colours(o)
    charge = join("charge", [core, shell])
    bpy.ops.object.transform_apply(rotation=True)
    triangulate(charge)
    return charge


def build_impact():
    """Twenty spikes, one out of each face of an icosahedron (their bases pulled in so they read as spikes, their
    lengths ragged), out of an icosphere puff."""
    m_spike = material("impact_blend", "impact.png", blend=True, double=True)
    m_puff = material("impact_glow_blend", "impact_glow.png", blend=True, double=True)
    ico = bmesh.new()
    bmesh.ops.create_icosphere(ico, subdivisions=1, radius=6)
    faces = [[v.co.copy() for v in f.verts] for f in ico.faces]
    ico.free()
    bm = bmesh.new()
    uv = bm.loops.layers.uv.new("UVMap")
    for n, tri in enumerate(faces):
        c = sum(tri, Vector()) / 3
        base = [c + (p - c) * 0.55 for p in tri]
        tip = c.normalized() * (12.5 + 2.5 * math.sin(n * 2.4))  # 10 to 15
        for a, b in ((0, 1), (1, 2), (2, 0)):
            f = bm.faces.new([bm.verts.new(base[a]), bm.verts.new(base[b]), bm.verts.new(tip)])
            for l, co in zip(f.loops, ((0, 1), (1, 1), (0.5, 0))):  # base along the top row, tip at the bottom
                l[uv].uv = co
    spikes = mesh_object("impact_spikes", bm, [m_spike])
    bm = bmesh.new()
    uv = bm.loops.layers.uv.new("UVMap")
    bmesh.ops.create_icosphere(bm, subdivisions=2, radius=8, calc_uvs=True)
    puff = mesh_object("impact_puff", bm, [m_puff])
    for o in (spikes, puff):
        white_colours(o)
    impact = join("impact", [spikes, puff])
    triangulate(impact)
    return impact


def export(obj, name, extra=()):
    OUT.mkdir(exist_ok=True)
    bpy.ops.object.select_all(action="DESELECT")
    for o in (obj, *extra):
        o.select_set(True)
    bpy.ops.export_scene.gltf(filepath=str(OUT / (name + ".glb")), export_format="GLB", use_selection=True,
                              export_yup=True, export_apply=True, export_vertex_color="ACTIVE",
                              export_extras=True, export_image_format="AUTO")


def build():
    clear()
    models = {"cannon": build_cannon(), "wave": build_wave(), "charge": build_charge(), "impact": build_impact()}
    report = {}
    # The shot origin: an empty named "barrel" at the muzzle tip, exported as a node beside the cannon's (jfgformats
    # makes it the gun's barrel point).
    barrel = bpy.data.objects.new("barrel", None)
    bpy.context.collection.objects.link(barrel)
    barrel.location = hand_matrix() @ Vector((0, MUZZLE, AXIS_Z))
    for name, obj in models.items():
        export(obj, name, (barrel,) if name == "cannon" else ())
        report[name] = len(obj.data.polygons)
    tip = hand_matrix() @ Vector((0, MUZZLE, AXIS_Z))
    g = [(v.co.x, v.co.z, -v.co.y) for v in models["cannon"].data.vertices]
    lo = [min(c[i] for c in g) for i in range(3)]
    hi = [max(c[i] for c in g) for i in range(3)]
    print("CONCUSSION tris", report)
    print("CONCUSSION muzzle tip: blender (%.2f, %.2f, %.2f), glTF/game (%.2f, %.2f, %.2f), %.1f from the grip"
          % (tip.x, tip.y, tip.z, tip.x, tip.z, -tip.y, tip.length))
    print("CONCUSSION cannon bounds, glTF/game: min (%.1f, %.1f, %.1f) max (%.1f, %.1f, %.1f) size %.1f x %.1f x %.1f"
          % (*lo, *hi, *(h - l for h, l in zip(hi, lo))))
    # Laid out for the previews (after the export, which wants them at the origin).
    # The cannon as it sits in the hand's frame; the wave pointing right.
    models["cannon"].location = (-110, 0, 40)
    models["wave"].location = (-40, 0, 30)
    models["wave"].rotation_euler = (0, 0, math.radians(90))
    models["charge"].location = (125, 0, 55)
    models["charge"].scale = (2.0, 2.0, 2.0)
    models["impact"].location = (125, 0, 5)
    models["impact"].scale = (1.5, 1.5, 1.5)
    bpy.ops.wm.save_as_mainfile(filepath=str(HERE / "concussion.blend"))
    return models


def render(path, loc, target, lens, size):
    scene = bpy.context.scene
    cam = scene.camera
    cam.location = loc
    cam.rotation_euler = (Vector(target) - Vector(loc)).to_track_quat("-Z", "Y").to_euler()
    cam.data.lens = lens
    scene.render.resolution_x, scene.render.resolution_y = size
    scene.render.filepath = str(path)
    bpy.ops.render.render(write_still=True)


def preview(models):
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
    render(PREVIEW / "models.png", (20, -300, 120), (20, 0, 30), 35, (1200, 500))
    # The cannon alone at its game size, three-quarter view from the front left.
    for name, obj in models.items():
        obj.hide_render = name != "cannon"
    c = models["cannon"]
    c.location = (0, 0, 0)
    centre = sum((Vector(b) for b in c.bound_box), Vector()) / 8
    m = hand_matrix()
    f, u = (m.to_3x3() @ Vector((0, -1, 0))).normalized(), (m.to_3x3() @ Vector((0, 0, 1))).normalized()
    side = u.cross(f)                                  # the cannon's right
    eye = centre + (-side * 0.85 + u * 0.35 - f * 0.25).normalized() * 150
    render(PREVIEW / "cannon.png", tuple(eye), tuple(centre), 40, (800, 500))


preview(build())
