"""The night sky over Blackwater Grotto (Corsair Reach 1.3), seen through the crack in the cavern's roof: a dome with
stars and a high moon, every pixel drawn here.

    blender --background --factory-startup --addons jfg64 --python sky_night.py   -> out/sky_night.glb
Then in JFG-Studio: import_sky (out/sky_night.glb, "night") and set_level sky pack:sky/night.
The game draws a sky behind everything, centred on the camera, unlit: the faces point inwards, and the colour is the
image times the vertex colours. The horizon is the level's fog colour (10, 30, 40).
"""
import math
import os
import random
import sys

import bmesh
import bpy

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import common as C  # noqa: E402
import jfg64  # noqa: E402

R = 9000.0
W, H = 64, 32  # the star image: u goes round the sky 4 times, v from the horizon (row 0) to straight up
HORIZON = (10 / 255, 30 / 255, 40 / 255)
ZENITH = (4 / 255, 8 / 255, 26 / 255)
MOON_ELEV, MOON_AZ = math.radians(72), math.radians(35)  # high: the crack shows the sky almost straight up

rnd = random.Random(23)
STARS = {}
for _ in range(70):
    x, y = rnd.randrange(W), rnd.randrange(4, H)
    STARS[(x, y)] = 0.45 + 0.55 * rnd.random() ** 2


def sky_t(row_from_top):
    return (H - 1 - row_from_top) / (H - 1)  # 0 at the horizon


def sky_px(x, row_from_top):
    t = sky_t(row_from_top)
    c = [HORIZON[i] + (ZENITH[i] - HORIZON[i]) * t ** 0.7 for i in range(3)]
    s = STARS.get((x, H - 1 - row_from_top))
    if s:
        tint = (0.85, 0.9, 1.0) if (x + row_from_top) % 3 else (1.0, 0.95, 0.85)
        c = [min(1.0, c[i] + s * tint[i]) for i in range(3)]
    return tuple(c)


MW = 32


def moon_px(x, y):
    """A pale moon with grey seas, in a soft halo fading to the sky's colour round it."""
    cx = cy = (MW - 1) / 2
    d = math.hypot(x - cx, y - cy) / (MW / 2)
    t = math.sin(MOON_ELEV) ** 2
    sky = [HORIZON[i] + (ZENITH[i] - HORIZON[i]) * t for i in range(3)]
    if d < 0.48:
        sea = 0.0
        for (sx, sy, sr) in ((-0.15, -0.1, 0.16), (0.12, 0.08, 0.12), (0.02, 0.22, 0.09)):
            if math.hypot((x - cx) / (MW / 2) - sx, (y - cy) / (MW / 2) - sy) < sr:
                sea = 0.18
        k = 0.95 - sea - 0.12 * d
        return (k * 0.92, k * 0.96, k * 1.0)
    halo = max(0.0, 1 - (d - 0.48) / 0.52) ** 2 * 0.35
    return tuple(min(1.0, sky[i] + halo * (0.6, 0.7, 0.85)[i]) for i in range(3))


scene, coll = C.new_scene("sky_night")
img = C.own_image("sky_night_stars", W, H, sky_px)
mat = C.own_material("sky_night", img)
moon_img = C.own_image("sky_night_moon", MW, MW, moon_px)
moon_mat = C.own_material("sky_night_moon", moon_img)

from mathutils import Vector  # noqa: E402

# the moon: a quad inside the dome, facing its centre
n = Vector((math.cos(MOON_ELEV) * math.cos(MOON_AZ), math.cos(MOON_ELEV) * math.sin(MOON_AZ), math.sin(MOON_ELEV)))
side = n.cross(Vector((0, 0, 1))).normalized()
up = side.cross(n).normalized()
centre = n * (R * 0.97)
half = R * 0.07

bm = bmesh.new()
bmesh.ops.create_uvsphere(bm, u_segments=24, v_segments=12, radius=R)
bmesh.ops.reverse_faces(bm, faces=bm.faces[:])  # seen from inside
mv = [bm.verts.new(centre + (sx * side + sy * up) * half) for sx, sy in ((-1, -1), (1, -1), (1, 1), (-1, 1))]
mf = bm.faces.new(mv)
mf.normal_update()
if mf.normal.dot(n) > 0:  # face the camera at the centre
    mf.normal_flip()
mf.material_index = 1
mesh = bpy.data.meshes.new("sky_night")
bm.to_mesh(mesh)
bm.free()
mesh.materials.append(mat)
mesh.materials.append(moon_mat)
uv = mesh.uv_layers.new(name="UV")
col = mesh.color_attributes.new("Col", "BYTE_COLOR", "CORNER")
for poly in mesh.polygons:
    if poly.material_index == 1:
        for li in poly.loop_indices:
            d = mesh.vertices[mesh.loops[li].vertex_index].co - centre
            uv.data[li].uv = (0.5 + d.dot(side) / (2 * half), 0.5 + d.dot(up) / (2 * half))
            col.data[li].color = (1, 1, 1, 1)
        continue
    cx = sum(mesh.vertices[mesh.loops[li].vertex_index].co.x for li in poly.loop_indices) / len(poly.loop_indices)
    cy = sum(mesh.vertices[mesh.loops[li].vertex_index].co.y for li in poly.loop_indices) / len(poly.loop_indices)
    base = math.atan2(cy, cx)
    for li in poly.loop_indices:
        co = mesh.vertices[mesh.loops[li].vertex_index].co
        elev = math.asin(max(-1.0, min(1.0, co.z / R)))
        ang = math.atan2(co.y, co.x)
        if abs(ang - base) > math.pi:  # keep one face's u on one side of the seam
            ang += math.tau if ang < base else -math.tau
        uv.data[li].uv = (ang / math.tau * 4.0, max(0.02, min(0.98, elev / (math.pi / 2))))
        d = min(1.0, max(0.0, -elev / 0.6))
        c = 1.0 - 0.4 * d  # darker below the horizon
        col.data[li].color = (c, c, c, 1.0)
obj = bpy.data.objects.new("sky_night", mesh)
coll.objects.link(obj)
out = jfg64.export(os.path.join(C.OUT, "sky_night.glb"), objects=[obj])
print("SKY", out.get("triangles") if isinstance(out, dict) else out)
