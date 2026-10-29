"""Singularity's three models, built in Blender from textures/*.png (make_textures.py), saved as singularity.blend
and exported as models/*.glb, with preview renders in previews/. Low-poly, as the game's own objects.

    "C:/Program Files/Blender Foundation/Blender 5.2/blender.exe" --background --factory-startup --python build_models.py

- core:      the thrown weapon. A faceted dark sphere (radius 6) with a glowing band orbiting it, tilted. ~140 tris.
- blackhole: the open singularity at size 1 (the mod scales it up as it opens and spins it): a dark sphere (radius 22)
             in a violet glow shell, the bright disc (24 to 70) and the spiral arms (55 to 150), each tilted a little.
- blast:     the collapse: a shell (radius 10) the mod grows and fades.
Blender's Z is up and 1 unit is 1 game unit; the glTF export turns it to the game's Y up. Colours come from vertex
colours (white: as the texture; the horizon is black) and the textures; see-through materials blend.
"""
import math
from pathlib import Path

import bmesh
import bpy
from mathutils import Matrix

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
    # Emission so the preview looks as the game draws it (unlit by the scene's light: these glow).
    nt.links.new(tex.outputs["Color"], bsdf.inputs["Emission Color"])
    bsdf.inputs["Emission Strength"].default_value = 1.0
    if blend:
        nt.links.new(tex.outputs["Alpha"], bsdf.inputs["Alpha"])
        m.surface_render_method = "BLENDED"
    m.use_backface_culling = not double
    m["doubleSided"] = double
    return m


def white_colours(obj, rgb=(1.0, 1.0, 1.0)):
    me = obj.data
    attr = me.color_attributes.new("Col", "BYTE_COLOR", "CORNER")
    for d in attr.data:
        d.color = (*rgb, 1.0)


def mesh_object(name, bm, mat):
    me = bpy.data.meshes.new(name)
    bm.to_mesh(me)
    bm.free()
    obj = bpy.data.objects.new(name, me)
    bpy.context.collection.objects.link(obj)
    me.materials.append(mat)
    return obj


def uv_sphere(name, radius, segments, rings, mat, u_repeat=1.0):
    bm = bmesh.new()
    uv = bm.loops.layers.uv.new("UVMap") # calc_uvs fills the layer that exists
    bmesh.ops.create_uvsphere(bm, u_segments=segments, v_segments=rings, radius=radius, calc_uvs=True)
    for f in bm.faces:
        f.smooth = False
        for l in f.loops:
            l[uv].uv = (l[uv].uv.x * u_repeat, l[uv].uv.y)
    return mesh_object(name, bm, mat)


def ring(name, inner, outer, segments, mat, u_repeat=1.0):
    """A flat ring in the XY plane: u around it; the texture's top row at the inner edge, its bottom at the outer."""
    bm = bmesh.new()
    uv = bm.loops.layers.uv.new("UVMap")
    verts_in, verts_out = [], []
    for i in range(segments):
        a = 2 * math.pi * i / segments
        verts_in.append(bm.verts.new((inner * math.cos(a), inner * math.sin(a), 0)))
        verts_out.append(bm.verts.new((outer * math.cos(a), outer * math.sin(a), 0)))
    for i in range(segments):
        j = (i + 1) % segments
        f = bm.faces.new((verts_in[i], verts_in[j], verts_out[j], verts_out[i]))
        u0, u1 = i / segments * u_repeat, (i + 1) / segments * u_repeat
        for l, (u, v) in zip(f.loops, ((u0, 0), (u1, 0), (u1, 1), (u0, 1))):
            l[uv].uv = (u, 1 - v) # a texture's top row is the inner edge (glTF and Blender count v from the bottom)
    bmesh.ops.triangulate(bm, faces=bm.faces[:])
    return mesh_object(name, bm, mat)


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


def triangulate(obj):
    bm = bmesh.new()
    bm.from_mesh(obj.data)
    bmesh.ops.triangulate(bm, faces=bm.faces[:])
    bm.to_mesh(obj.data)
    bm.free()


def export(obj, name):
    OUT.mkdir(exist_ok=True)
    bpy.ops.object.select_all(action="DESELECT")
    obj.select_set(True)
    bpy.ops.export_scene.gltf(filepath=str(OUT / (name + ".glb")), export_format="GLB", use_selection=True,
                              export_yup=True, export_apply=True, export_vertex_color="ACTIVE",
                              export_extras=True, export_image_format="AUTO")


def build():
    clear()
    m_core = material("core", "core.png")
    m_band = material("band_blend", "band.png", blend=True, double=True)
    m_horizon = material("horizon", "horizon.png")
    m_rim = material("rim_blend", "rim.png", blend=True, double=True)
    m_disc = material("disc_blend", "disc.png", blend=True, double=True)
    m_blast = material("blast_blend", "blast.png", blend=True, double=True)

    # The thrown core.
    sphere = uv_sphere("core_sphere", 6, 10, 6, m_core)
    band = ring("core_band", 7.5, 10.5, 16, m_band, u_repeat=2)
    band.rotation_euler = (math.radians(70), math.radians(20), 0)
    for o in (sphere, band):
        white_colours(o)
    core = join("core", [sphere, band])
    bpy.ops.object.transform_apply(rotation=True, scale=True)
    triangulate(core)
    core.location = (-60, 0, 10)

    # The black hole at size 1 (the game object; the mod spins it about its vertical and scales it): a solid dark
    # sphere in the middle with a violet glow shell, the bright disc round it, and wider spiral arms, tilted.
    m_disc2 = material("disc2_blend", "disc2.png", blend=True, double=True)
    m_arms = material("arms_blend", "arms.png", blend=True, double=True)
    m_glow = material("glow_blend", "glow.png", blend=True, double=True)
    horizon = uv_sphere("bh_horizon", 22, 16, 10, m_horizon)
    shell = uv_sphere("bh_glow", 27, 12, 8, m_glow, u_repeat=2)
    disc = ring("bh_disc", 24, 70, 24, m_disc2, u_repeat=3)
    arms_ring = ring("bh_arms", 55, 150, 24, m_arms, u_repeat=1)
    disc.rotation_euler = (math.radians(8), 0, 0)
    arms_ring.rotation_euler = (math.radians(-6), math.radians(10), 0)
    arms_ring.location = (0, 0, 2)
    for o in (horizon, shell, disc, arms_ring):
        white_colours(o)
    bh = join("blackhole", [horizon, shell, disc, arms_ring])
    bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
    triangulate(bh)
    bh.location = (0, 0, 30)

    # The collapse blast.
    blast = uv_sphere("blast", 10, 12, 7, m_blast, u_repeat=2)
    white_colours(blast)
    triangulate(blast)
    blast.location = (70, 0, 20)

    bpy.ops.wm.save_as_mainfile(filepath=str(HERE / "singularity.blend"))
    report = {}
    for obj, name in ((core, "core"), (bh, "blackhole"), (blast, "blast")):
        loc = obj.location.copy()
        obj.location = (0, 0, 0)
        export(obj, name)
        obj.location = loc
        report[name] = len(obj.data.polygons)
    print("SINGULARITY", report)
    return core, bh, blast


def preview():
    PREVIEW.mkdir(exist_ok=True)
    scene = bpy.context.scene
    scene.render.engine = "BLENDER_EEVEE"
    scene.render.resolution_x, scene.render.resolution_y = 1200, 500
    scene.render.film_transparent = False
    world = bpy.data.worlds.new("w")
    world.use_nodes = True
    world.node_tree.nodes["Background"].inputs[0].default_value = (0.12, 0.2, 0.12, 1)
    scene.world = world
    cam = bpy.data.objects.new("cam", bpy.data.cameras.new("cam"))
    bpy.context.collection.objects.link(cam)
    cam.location = (5, -330, 140)
    cam.rotation_euler = (math.radians(73), 0, 0)
    cam.data.lens = 35
    scene.camera = cam
    scene.render.filepath = str(PREVIEW / "models.png")
    bpy.ops.render.render(write_still=True)


build()
preview()
