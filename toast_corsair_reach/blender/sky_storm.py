"""Mirefall's storm sky (Corsair Reach 2.1, reused by 2.2 and 2.4): a dome of heavy rain clouds, dark slate
overhead, torn in places where a paler sky shows through, every pixel drawn here.

    blender --background --factory-startup --addons jfg64 --python sky_storm.py   -> out/sky_storm.glb
Then in JFG-Studio: import_sky (out/sky_storm.glb, "storm") and set_level sky pack:sky/storm.
As sky_sunset.py: faces inwards, unlit, the image times the vertex colours. No sun, no landmark (the lighthouse is
modelled in 2.1's own backdrop, and 2.4 stands on it): the same dome fits all three levels. The horizon row is the
fog colour (60, 70, 85) all round, so the fog meets the sky without a seam; 2.4's fog (55, 65, 80) is close enough.
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
W, H = 64, 32  # u once round the sky, v from the horizon (row 0) to straight up


def noise(seed):
    """Periodic value noise over the image (x wraps), smooth, 0..1."""
    rnd = random.Random(seed)
    grids = []
    for cells_x, cells_y, amp in ((5, 3, 0.5), (10, 6, 0.3), (20, 10, 0.2)):
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


N = noise(41)
N2 = noise(77)
HORIZON = (60 / 255, 70 / 255, 85 / 255)  # the level's fog colour (set_level fogR/G/B)


def mix(a, b, t):
    return tuple(a[i] + (b[i] - a[i]) * t for i in range(3))


def sky_px(x, row_from_top):
    y = H - 1 - row_from_top  # 0 at the horizon
    t = y / (H - 1)
    # the fog's blue-grey at the horizon, darker slate up into the cloud deck
    base = mix(HORIZON, (0.13, 0.15, 0.2), min(1.0, t / 0.55) ** 0.9)
    n = N(x, y)
    # heavy cloud masses: darker bellies, paler tops where the storm's light catches them
    mass = max(0.0, min(1.0, (n - 0.35) * 3.0))
    belly = mix((0.1, 0.11, 0.15), (0.2, 0.23, 0.3), max(0.0, min(1.0, (N(x, y + 2) - 0.3) * 2.5)))
    c = mix(base, belly, 0.75 * mass)
    # rents in the deck: a paler, colder sky (where the lightning shows best)
    rent = max(0.0, min(1.0, (N2(x, y) - 0.62) * 5.0)) * (0.4 + 0.6 * math.sin(math.pi * min(1.0, t * 1.4)))
    c = mix(c, (0.42, 0.48, 0.58), 0.6 * rent)
    # rain curtains: faint streaks down from the cloud deck near the horizon
    if t < 0.4 and (x * 7 + y * 3) % 11 == 0:
        c = mix(c, (0.3, 0.34, 0.42), 0.35 * (1 - t / 0.4))
    return c


scene, coll = C.new_scene("sky_storm")
img = C.own_image("sky_storm_clouds", W, H, sky_px)
mat = C.own_material("sky_storm", img)

bm = bmesh.new()
bmesh.ops.create_uvsphere(bm, u_segments=24, v_segments=12, radius=R)
bmesh.ops.reverse_faces(bm, faces=bm.faces[:])  # seen from inside
mesh = bpy.data.meshes.new("sky_storm")
bm.to_mesh(mesh)
bm.free()
uv = mesh.uv_layers.new(name="UV")
col = mesh.color_attributes.new("Col", "BYTE_COLOR", "CORNER")
for poly in mesh.polygons:
    cx = sum(mesh.vertices[mesh.loops[li].vertex_index].co.x for li in poly.loop_indices) / len(poly.loop_indices)
    cy = sum(mesh.vertices[mesh.loops[li].vertex_index].co.y for li in poly.loop_indices) / len(poly.loop_indices)
    base = math.atan2(cy, -cx)
    for li in poly.loop_indices:
        co = mesh.vertices[mesh.loops[li].vertex_index].co
        elev = math.asin(max(-1.0, min(1.0, co.z / R)))
        ang = math.atan2(co.y, -co.x)
        if abs(ang - base) > math.pi:  # keep one face's u on one side of the seam
            ang += math.tau if ang < base else -math.tau
        u = ang / math.tau
        v = max(0.02, min(0.98, elev / (math.pi / 2)))  # below the horizon: the horizon's row
        uv.data[li].uv = (u, v)
        if elev >= 0:
            up = min(1.0, elev / 0.6)
            k = 1.0 - 0.15 * up  # the zenith a little darker still
            c = (k, k, k * 1.02)
        else:
            d = min(1.0, -elev / 0.6)
            c = (1.0 - 0.35 * d, 1.0 - 0.33 * d, 1.0 - 0.3 * d)
        col.data[li].color = (*[min(1.0, v_) for v_ in c], 1.0)
mesh.materials.append(mat)
obj = bpy.data.objects.new("sky_storm", mesh)
coll.objects.link(obj)
out = jfg64.export(os.path.join(C.OUT, "sky_storm.glb"), objects=[obj])
print("SKY", out.get("triangles") if isinstance(out, dict) else out)
