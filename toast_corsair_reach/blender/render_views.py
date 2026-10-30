"""Renders a level's views from the hero's eye height, to look at a build (not part of the pack).

    blender --background --factory-startup --addons jfg64 out/<level>.blend --python render_views.py -- <views.json>

views.json: {"sky": [r, g, b], "fog": [r, g, b, start, depth], "views": [{"name", "eye": [x, z, y], "look": [x, z, y],
"lens": 24}]} in game coordinates. Writes out/views/<level>_<name>.png. Materials are shown as the game draws them:
the texture times the baked vertex colours.
"""
import json
import math
import os
import sys

import bpy
from mathutils import Vector

args = sys.argv[sys.argv.index("--") + 1:]
spec = json.load(open(args[0], encoding="utf-8"))
level = os.path.splitext(os.path.basename(bpy.data.filepath))[0]
out = os.path.join(os.path.dirname(bpy.data.filepath), "views")
os.makedirs(out, exist_ok=True)
scene = bpy.data.scenes.get(level) or bpy.context.scene


def G(x, z, y):
    return Vector((x, -z, y))


for mat in bpy.data.materials:
    if not mat.use_nodes:
        continue
    nt = mat.node_tree
    tex = next((n for n in nt.nodes if n.type == "TEX_IMAGE"), None)
    out_node = next((n for n in nt.nodes if n.type == "OUTPUT_MATERIAL"), None)
    if out_node is None:
        continue
    col = nt.nodes.new("ShaderNodeVertexColor")
    col.layer_name = "Col"
    mul = nt.nodes.new("ShaderNodeMix")
    mul.data_type = "RGBA"
    mul.blend_type = "MULTIPLY"
    mul.inputs["Factor"].default_value = 1.0
    emit = nt.nodes.new("ShaderNodeEmission")
    if tex is not None:
        nt.links.new(tex.outputs["Color"], mul.inputs[6])
    else:
        mul.inputs[6].default_value = (1, 1, 1, 1)
    nt.links.new(col.outputs["Color"], mul.inputs[7])
    nt.links.new(mul.outputs[2], emit.inputs["Color"])
    shader = emit.outputs["Emission"]
    if "collider" in mat.name:
        tr = nt.nodes.new("ShaderNodeBsdfTransparent")
        shader = tr.outputs["BSDF"]
    elif "water" in mat.name:
        tr = nt.nodes.new("ShaderNodeBsdfTransparent")
        mix = nt.nodes.new("ShaderNodeMixShader")
        mix.inputs["Fac"].default_value = 0.75
        nt.links.new(tr.outputs["BSDF"], mix.inputs[1])
        nt.links.new(emit.outputs["Emission"], mix.inputs[2])
        shader = mix.outputs["Shader"]
    nt.links.new(shader, out_node.inputs["Surface"])
    mat.blend_method = "BLEND" if ("water" in mat.name or "collider" in mat.name) else "OPAQUE"

world = bpy.data.worlds.new("sky")
world.use_nodes = True
bg = world.node_tree.nodes.get("Background")
bg.inputs["Color"].default_value = (*spec.get("sky", [0.55, 0.7, 0.9]), 1.0)
scene.world = world
scene.render.engine = "BLENDER_EEVEE"
scene.render.resolution_x, scene.render.resolution_y = 960, 540
scene.view_settings.view_transform = "Standard"
cam_data = bpy.data.cameras.new("view")
cam = bpy.data.objects.new("view", cam_data)
scene.collection.objects.link(cam)
scene.camera = cam
for v in spec["views"]:
    eye, look = G(*v["eye"]), G(*v["look"])
    cam.location = eye
    cam.rotation_euler = (look - eye).to_track_quat("-Z", "Y").to_euler()
    cam_data.lens = v.get("lens", 22)
    cam_data.clip_end = 20000
    scene.render.filepath = os.path.join(out, f"{level}_{v['name']}.png")
    bpy.ops.render.render(write_still=True, scene=scene.name)
    print("VIEW", scene.render.filepath)
