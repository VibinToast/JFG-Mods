"""The golden-hour sunset sky of Gullwing Docks (Corsair Reach 1.2): a dome with lit clouds and the low sun's glow in
the west, every pixel drawn here.

    blender --background --factory-startup --addons jfg64 --python sky_sunset.py   -> out/sky_sunset.glb
Then in JFG-Studio: import_sky (out/sky_sunset.glb, "sunset") and set_level sky pack:sky/sunset.
The game draws a sky behind everything, centred on the camera, unlit: the faces point inwards, and the colour is the
image times the vertex colours. The image goes round the sky once (the sun is in it, in the west); the vertex
colours warm the western half and cool the east overhead, and are plain white at the horizon, so the horizon is
exactly the level's fog colour (235, 160, 130) all round and the fog meets the sky without a seam.
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
W, H = 64, 32  # u once round the sky (u 0 = game west), v from the horizon (row 0) to straight up


def noise(seed):
    """Periodic value noise over the image (x wraps), smooth, 0..1."""
    rnd = random.Random(seed)
    grids = []
    for cells_x, cells_y, amp in ((6, 3, 0.55), (12, 5, 0.3), (24, 9, 0.15)):
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


N = noise(23)
SUN_U, SUN_V = 0.0, 4.5
HORIZON = (235 / 255, 160 / 255, 130 / 255)  # the level's fog colour (set_level fogR/G/B)  # the sun: due west, a little over the horizon (pixels)


def mix(a, b, t):
    return tuple(a[i] + (b[i] - a[i]) * t for i in range(3))


def sky_px(x, row_from_top):
    y = H - 1 - row_from_top  # 0 at the horizon
    t = y / (H - 1)
    # the fog's orange-pink at the horizon, rose, then violet-blue overhead
    if t < 0.3:
        base = mix(HORIZON, (0.95, 0.5, 0.48), t / 0.3)
    else:
        base = mix((0.95, 0.5, 0.48), (0.28, 0.24, 0.5), min(1.0, (t - 0.3) / 0.7) ** 0.8)
    # the sun's glow round due west (x wraps)
    dx = min(abs(x - SUN_U), W - abs(x - SUN_U))
    glow = math.exp(-(dx / 9.0) ** 2 - ((y - SUN_V) / 7.0) ** 2)
    base = mix(base, (1.0, 0.88, 0.6), 0.75 * glow)
    if dx ** 2 + ((y - SUN_V) * 1.4) ** 2 <= 5.0:
        return (1.0, 0.95, 0.78)  # the sun's disc
    # long low clouds, lit orange from below, darker violet on top
    band = math.exp(-((t - 0.3) / 0.25) ** 2)
    c = min(0.9, max(0.0, (N(x, y) - 0.4) * 6.0) * band)
    lit = 0.5 + 0.5 * glow
    under = max(0.0, min(1.0, (N(x, y + 2) - 0.35) * 3.0))  # undersides catch the sun, tops stay violet
    cloud = mix((0.36, 0.24, 0.42), (1.0, 0.8, 0.52), min(1.0, lit * (0.4 + 0.6 * under)))
    return mix(base, cloud, c)


scene, coll = C.new_scene("sky_sunset")
img = C.own_image("sky_sunset_clouds", W, H, sky_px)
mat = C.own_material("sky_sunset", img)

bm = bmesh.new()
bmesh.ops.create_uvsphere(bm, u_segments=24, v_segments=12, radius=R)
bmesh.ops.reverse_faces(bm, faces=bm.faces[:])  # seen from inside
mesh = bpy.data.meshes.new("sky_sunset")
bm.to_mesh(mesh)
bm.free()
uv = mesh.uv_layers.new(name="UV")
col = mesh.color_attributes.new("Col", "BYTE_COLOR", "CORNER")
for poly in mesh.polygons:
    cx = sum(mesh.vertices[mesh.loops[li].vertex_index].co.x for li in poly.loop_indices) / len(poly.loop_indices)
    cy = sum(mesh.vertices[mesh.loops[li].vertex_index].co.y for li in poly.loop_indices) / len(poly.loop_indices)
    base = math.atan2(cy, -cx)  # 0 = game west (Blender -x)
    for li in poly.loop_indices:
        co = mesh.vertices[mesh.loops[li].vertex_index].co
        elev = math.asin(max(-1.0, min(1.0, co.z / R)))
        ang = math.atan2(co.y, -co.x)
        if abs(ang - base) > math.pi:  # keep one face's u on one side of the seam
            ang += math.tau if ang < base else -math.tau
        u = ang / math.tau
        v = max(0.02, min(0.98, elev / (math.pi / 2)))  # below the horizon: the horizon's row
        uv.data[li].uv = (u, v)
        west = 0.5 + 0.5 * math.cos(ang)  # 1 facing the sun, 0 away
        if elev >= 0:
            up = min(1.0, elev / 0.5)  # 0 at the horizon (plain white: the fog's colour shows), 1 well up
            k = 1.0 - up * (0.22 - 0.22 * west)
            c = (k, k * (1.0 - up * (0.08 - 0.08 * west)), k * (1.0 + up * (0.05 - 0.12 * west)))
        else:
            d = min(1.0, -elev / 0.6)
            c = (1.0 - 0.3 * d, 1.0 - 0.3 * d, 1.0 - 0.25 * d)  # below the horizon: the horizon's row, darkening
        col.data[li].color = (*[min(1.0, v_) for v_ in c], 1.0)
mesh.materials.append(mat)
obj = bpy.data.objects.new("sky_sunset", mesh)
coll.objects.link(obj)
out = jfg64.export(os.path.join(C.OUT, "sky_sunset.glb"), objects=[obj])
print("SKY", out.get("triangles") if isinstance(out, dict) else out)
