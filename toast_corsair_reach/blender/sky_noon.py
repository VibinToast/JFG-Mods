"""The noon sky of Driftwood Cay (Corsair Reach 1.1): a dome with clouds, every pixel drawn here.

    blender --background --factory-startup --addons jfg64 --python sky_noon.py   -> out/sky_noon.glb
Then in JFG-Studio: import_sky (out/sky_noon.glb, "noon") and set_level sky pack:sky/noon.
The game draws a sky behind everything, centred on the camera, unlit: the faces point inwards, and the colour is the
image times the vertex colours.
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

R = 9000.0  # the size of the game's own big domes
W, H = 64, 32  # the cloud image: u goes round the sky 4 times, v from the horizon (row 0) to straight up


def noise(seed):
    """Periodic value noise over the image (x wraps), smooth, 0..1."""
    rnd = random.Random(seed)
    grids = []
    for cells_x, cells_y, amp in ((4, 3, 0.55), (8, 5, 0.3), (16, 9, 0.15)):
        g = [[rnd.random() for _ in range(cells_x)] for _ in range(cells_y + 1)]
        grids.append((cells_x, cells_y, amp, g))

    def at(x, y):
        total = 0.0
        for cx, cy, amp, g in grids:
            fx, fy = x / W * cx, y / H * cy
            ix, iy = int(fx), int(fy)
            tx, ty = fx - ix, fy - iy
            tx, ty = tx * tx * (3 - 2 * tx), ty * ty * (3 - 2 * ty)
            a, b = g[iy][ix % cx], g[iy][(ix + 1) % cx]
            c, d = g[min(iy + 1, cy)][ix % cx], g[min(iy + 1, cy)][(ix + 1) % cx]
            total += amp * ((a * (1 - tx) + b * tx) * (1 - ty) + (c * (1 - tx) + d * tx) * ty)
        return total
    return at


N = noise(11)


def sky_px(x, row_from_top):
    y = H - 1 - row_from_top  # 0 at the horizon
    t = y / (H - 1)
    blue = tuple(a + (b - a) * t ** 0.8 for a, b in zip((0.66, 0.82, 0.96), (0.2, 0.45, 0.88)))
    # clouds: thickest a little above the horizon, thinning towards the top
    band = math.exp(-((t - 0.32) / 0.3) ** 2)
    c = max(0.0, (N(x, y) - 0.42) * 5.0) * band
    c = min(1.0, c)
    shade = 0.84 + 0.16 * max(0.0, min(1.0, (N(x + 3, y + 2) - 0.3) * 2))  # grey-blue undersides
    cloud = (1.0 * shade, 1.0 * shade, 1.0 * shade)
    return tuple(blue[i] * (1 - c) + cloud[i] * c for i in range(3))


scene, coll = C.new_scene("sky_noon")
img = C.own_image("sky_noon_clouds", W, H, sky_px)
mat = C.own_material("sky_noon", img)

bm = bmesh.new()
bmesh.ops.create_uvsphere(bm, u_segments=24, v_segments=12, radius=R)
bmesh.ops.reverse_faces(bm, faces=bm.faces[:])  # seen from inside
mesh = bpy.data.meshes.new("sky_noon")
bm.to_mesh(mesh)
bm.free()
uv = mesh.uv_layers.new(name="UV")
col = mesh.color_attributes.new("Col", "BYTE_COLOR", "CORNER")
for poly in mesh.polygons:
    cx = sum(mesh.vertices[mesh.loops[li].vertex_index].co.x for li in poly.loop_indices) / len(poly.loop_indices)
    cy = sum(mesh.vertices[mesh.loops[li].vertex_index].co.y for li in poly.loop_indices) / len(poly.loop_indices)
    base = math.atan2(cy, cx)
    for li in poly.loop_indices:
        co = mesh.vertices[mesh.loops[li].vertex_index].co
        elev = math.asin(max(-1.0, min(1.0, co.z / R)))
        ang = math.atan2(co.y, co.x)
        if abs(ang - base) > math.pi:  # keep one face's u on one side of the seam
            ang += math.tau if ang < base else -math.tau
        u = ang / math.tau * 4.0
        v = max(0.02, min(0.98, elev / (math.pi / 2)))  # below the horizon: the horizon's row
        uv.data[li].uv = (u, v)
        if elev >= 0:
            k = 0.86 + 0.14 * (1 - elev / (math.pi / 2))  # a touch darker straight up
            c = (k, k, k)
        else:
            d = min(1.0, -elev / 0.6)
            c = (0.8 - 0.25 * d, 0.92 - 0.2 * d, 0.95 - 0.15 * d)  # sea haze below the horizon
        col.data[li].color = (*c, 1.0)
mesh.materials.append(mat)
obj = bpy.data.objects.new("sky_noon", mesh)
coll.objects.link(obj)
out = jfg64.export(os.path.join(C.OUT, "sky_noon.glb"), objects=[obj])
print("SKY", out.get("triangles") if isinstance(out, dict) else out)
