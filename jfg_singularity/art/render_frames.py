"""The black hole's swirl animation for the screen overlay, rendered from singularity.blend's black hole (build_models.py):
SWIRL_FRAMES frames of one turn of its disc, seen a little from above, on a clear background, into frames/swirl_NN.png
(FRAME x FRAME). Also frames/core.png, the thrown core's glow. Then pack_frames.py makes them C data for the mod.

    "C:/Program Files/Blender Foundation/Blender 5.2/blender.exe" --background art/singularity.blend --python art/render_frames.py
"""
import math
from pathlib import Path

import bpy

HERE = Path(__file__).resolve().parent
OUT = HERE / "frames"
SWIRL_FRAMES = 12
FRAME = 128

scene = bpy.context.scene
scene.render.engine = "BLENDER_EEVEE"
scene.render.resolution_x = scene.render.resolution_y = FRAME
scene.render.film_transparent = True
scene.render.image_settings.file_format = "PNG"
scene.render.image_settings.color_mode = "RGBA"
scene.view_settings.view_transform = "Standard"

world = bpy.data.worlds.new("frames")
world.use_nodes = True
world.node_tree.nodes["Background"].inputs[1].default_value = 0.0
scene.world = world

for o in bpy.data.objects:
    o.hide_render = True
bh = bpy.data.objects["blackhole"]
core = bpy.data.objects["core"]

cam = bpy.data.objects.new("frame_cam", bpy.data.cameras.new("frame_cam"))
scene.collection.objects.link(cam)
cam.data.type = "ORTHO"
scene.camera = cam

# The disc's material glows more for the overlay (it is drawn over the game, not lit by it).
for mat in bh.data.materials:
    bsdf = mat.node_tree.nodes.get("Principled BSDF")
    if bsdf is not None and mat.name != "horizon":
        bsdf.inputs["Emission Strength"].default_value = 1.6

OUT.mkdir(exist_ok=True)


def aim(target, distance, elevation_deg, ortho):
    e = math.radians(elevation_deg)
    cam.location = (target.x, target.y - distance * math.cos(e), target.z + distance * math.sin(e))
    cam.rotation_euler = (math.radians(90 - elevation_deg), 0, 0)
    cam.data.ortho_scale = ortho


bh.hide_render = False
start = bh.rotation_euler.z
aim(bh.location, 300, 22, 92)
for i in range(SWIRL_FRAMES):
    bh.rotation_euler.z = start - 2 * math.pi * i / SWIRL_FRAMES  # turns the way the swirl streaks run
    scene.render.filepath = str(OUT / ("swirl_%02d.png" % i))
    bpy.ops.render.render(write_still=True)
bh.rotation_euler.z = start
bh.hide_render = True

core.hide_render = False
aim(core.location, 200, 15, 26)
scene.render.filepath = str(OUT / "core.png")
bpy.ops.render.render(write_still=True)
print("FRAMES", SWIRL_FRAMES)
