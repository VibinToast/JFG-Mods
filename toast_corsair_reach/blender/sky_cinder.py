"""Cinderhold's sky (Corsair Reach 3.1, reused by 3.3): a dark red dusk under ash clouds, the volcano on the northern
horizon with the summit forge burning on its top and its smoke lit from below, every pixel drawn here.

    blender --background --factory-startup --addons jfg64 --python sky_cinder.py   -> out/sky_cinder.glb
Then in JFG-Studio: import_sky (out/sky_cinder.glb, "cinder") and set_level sky pack:sky/cinder.
As sky_storm.py: a sphere faced inwards, unlit, the image times the vertex colours; the horizon row is the fog colour
(70, 30, 20) all round, so the fog meets the sky without a seam. The volcano is a cone of its own inside the dome
(vertex colours on a small rock image): the dome moves with the camera, so it stays on the horizon, due north
(game -z), as far away as the sky. VOLCANO = False leaves it out (a level standing on the volcano itself).
With SKY_VARIANT=rim in the environment it builds 3.3's copy instead: no volcano (the Crown stands on it), the horizon
row at the Crown's fog colour (90, 25, 15), its own names -> out/sky_cinder_rim.glb (import_sky as "cinder_rim").
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

RIM = os.environ.get("SKY_VARIANT") == "rim"
VOLCANO = not RIM
NAME = "sky_cinder_rim" if RIM else "sky_cinder"
R = 9000.0
W, H = 64, 32  # u once round the sky, v from the horizon (row 0) to straight up
HORIZON = ((90, 25, 15) if RIM else (70, 30, 20))  # the level's fog colour (set_level fogR/G/B)
HORIZON = tuple(c / 255 for c in HORIZON)


def noise(seed):
    """Periodic value noise over the image (x wraps), smooth, 0..1."""
    rnd = random.Random(seed)
    grids = []
    for cells_x, cells_y, amp in ((6, 3, 0.5), (12, 6, 0.3), (24, 12, 0.2)):
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


N = noise(53)
N2 = noise(91)


def mix(a, b, t):
    t = max(0.0, min(1.0, t))
    return tuple(a[i] + (b[i] - a[i]) * t for i in range(3))


def sky_px(x, row_from_top):
    y = H - 1 - row_from_top  # 0 at the horizon
    t = y / (H - 1)
    # the fog's red-brown at the horizon, a deep blood red, near black overhead
    base = mix(HORIZON, (0.2, 0.05, 0.035), min(1.0, t / 0.4))
    base = mix(base, (0.06, 0.02, 0.02), (t - 0.4) / 0.6)
    n = N(x, y)
    # ash clouds in banks: dark grey-brown, their bellies lit red by the lava below
    mass = max(0.0, min(1.0, (n - 0.38) * 3.0))
    belly = mix((0.1, 0.07, 0.07), (0.42, 0.12, 0.06), max(0.0, min(1.0, (N(x, y + 2) - 0.3) * 2.2)) * (1 - t))
    c = mix(base, belly, 0.8 * mass)
    # a few rents with a dull orange glow behind (the sun low in the west-south-west: x near 0 is game west)
    rent = max(0.0, min(1.0, (N2(x, y) - 0.66) * 5.0)) * (1 - t)
    west = 0.5 + 0.5 * math.cos((x + 0.5) / W * math.tau + 0.4)
    c = mix(c, (0.75, 0.32, 0.1), 0.55 * rent * (0.4 + 0.6 * west))
    return c


def rock_px(x, y):
    """The volcano's flank: basalt, a few glowing cracks (16 x 16; the vertex colours darken it to its shade)."""
    g = ((x * 7 + y * 11) % 13) / 13.0
    if (x + 2 * y) % 9 == 0 and y > 4:
        return (1.0, 0.45, 0.15)
    return (0.55 + 0.15 * g, 0.5 + 0.12 * g, 0.48 + 0.1 * g)


def plain_px(x, y):
    """Near white with a faint grain (a plain white 8 x 8 is one of the game's own images, which a pack can't
    carry): the smoke and the forge's fire take their colours from the vertex colours (8 x 8)."""
    g = ((x * 3 + y * 5) % 7) / 7.0
    return (0.9 + 0.1 * g, 0.88 + 0.1 * g, 0.86 + 0.1 * g)


scene, coll = C.new_scene(NAME)
img = C.own_image(NAME + "_clouds", W, H, sky_px)
mat = C.own_material(NAME, img)

bm = bmesh.new()
bmesh.ops.create_uvsphere(bm, u_segments=24, v_segments=12, radius=R)
bmesh.ops.reverse_faces(bm, faces=bm.faces[:])  # seen from inside
mesh = bpy.data.meshes.new(NAME)
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
        uv.data[li].uv = (ang / math.tau, max(0.02, min(0.98, elev / (math.pi / 2))))
        north = max(0.0, math.sin(ang))  # Blender +y = game north: the volcano's glow on the clouds
        if elev >= 0:
            k = 1.0 + 0.25 * north * max(0.0, 1 - elev / 0.5)
            c = (k, 1.0 + 0.05 * north, 1.0)
        else:
            d = min(1.0, -elev / 0.6)
            c = (1.0 - 0.4 * d, 1.0 - 0.45 * d, 1.0 - 0.45 * d)
        col.data[li].color = (*[min(1.0, v_) for v_ in c], 1.0)
mesh.materials.append(mat)
sky = bpy.data.objects.new(NAME, mesh)
coll.objects.link(sky)
objs = [sky]

if VOLCANO:
    # a cone due north, inside the dome: its foot under the horizon, its top about 40 degrees up (over the
    # levels' rims: 25-35 degrees from the flats), a crater rim
    rock = C.own_material(NAME + "_rock", C.own_image(NAME + "_rock", 16, 16, rock_px))
    plain = C.own_material(NAME + "_plain", C.own_image(NAME + "_plain", 8, 8, plain_px))
    mats = []  # per face: 0 rock, 1 plain
    D = 6000.0                      # distance north (Blender +y): every point stays inside the dome (R)
    foot, top_r, top_y, base_y = 5000.0, 700.0, D * math.tan(math.radians(40)), -1500.0
    n = 14
    vm = bpy.data.meshes.new(NAME + "_volcano")
    verts, faces, cols, uvs = [], [], [], []
    rng = random.Random(5)

    def ring(r, y, jitter):
        return [(r * math.cos(k * math.tau / n) * (1 + jitter * (rng.random() - 0.5)),
                 D + r * math.sin(k * math.tau / n) * 0.35, y) for k in range(n)]

    rings = [ring(foot, base_y, 0.1), ring(foot * 0.55, top_y * 0.45, 0.12), ring(top_r, top_y, 0.08),
             ring(top_r * 0.8, top_y + 25, 0.0)]
    shade = [(0.2, 0.12, 0.11), (0.3, 0.17, 0.15), (0.75, 0.38, 0.22), (1.0, 0.85, 0.5)]  # glow towards the top
    for j in range(3):
        for k in range(n):
            if math.sin((k + 0.5) * math.tau / n) > 0.15:
                continue  # the far side, hidden behind the near one (sky faces draw in no depth order)
            a, b = rings[j][k], rings[j][(k + 1) % n]
            c2, d2 = rings[j + 1][(k + 1) % n], rings[j + 1][k]
            base_i = len(verts)
            verts += [a, b, c2, d2]
            faces.append((base_i, base_i + 3, base_i + 2, base_i + 1))  # facing the camera at the centre
            mats.append(0)
            cols += [shade[j], shade[j], shade[j + 1], shade[j + 1]]
            uvs += [(k / 2, j * 2), ((k + 1) / 2, j * 2), ((k + 1) / 2, j * 2 + 2), (k / 2, j * 2 + 2)]
    # the summit forge's fire over the crater: three tongues of flame, bright at the rim
    for s_, (w0, h0, x0) in enumerate(((700, 900, 0), (420, 600, -380), (450, 700, 350))):
        bi = len(verts)
        yb = top_y - 30
        verts += [(x0 - w0 / 2, D - 60 - s_ * 5, yb), (x0 + w0 / 2, D - 60 - s_ * 5, yb),
                  (x0 + 40, D - 60 - s_ * 5, yb + h0)]
        faces.append((bi, bi + 2, bi + 1))
        mats.append(1)
        cols += [(1.0, 0.8, 0.4), (1.0, 0.8, 0.4), (0.85, 0.3, 0.08)]
        uvs += [(0, 0), (1, 0), (0.5, 1)]
    # smoke over the crater: three leaning sheets, dark, lit orange underneath
    for s_, (w0, lean) in enumerate(((1100, -700), (1400, 400), (1000, 1200))):
        y0, y1 = top_y + 350, top_y + 1000 + s_ * 120
        a = (-w0 * 0.5, D + 50 + s_ * 20, y0)
        b = (w0 * 0.5, D + 50 + s_ * 20, y0)
        c2 = (lean + w0 * 0.9, D + 120 + s_ * 20, y1)
        d2 = (lean - w0 * 0.9, D + 120 + s_ * 20, y1)
        bi = len(verts)
        verts += [a, b, c2, d2]
        faces.append((bi, bi + 3, bi + 2, bi + 1))
        mats.append(1)
        cols += [(0.55, 0.22, 0.1), (0.55, 0.22, 0.1), (0.24, 0.17, 0.16), (0.24, 0.17, 0.16)]
        uvs += [(0, 0), (1, 0), (1, 1), (0, 1)]
    vm.from_pydata(verts, [], faces)
    vm.update()
    # face the centre (the camera): flip any face whose normal points away from the origin
    for poly in vm.polygons:
        if poly.normal.dot(poly.center) > 0:
            poly.flip()
    vm.update()
    vm.materials.append(rock)
    vm.materials.append(plain)
    for poly, m_ in zip(vm.polygons, mats):
        poly.material_index = m_
    vuv = vm.uv_layers.new(name="UV")
    vcol = vm.color_attributes.new("Col", "BYTE_COLOR", "CORNER")
    for poly in vm.polygons:
        for li in poly.loop_indices:
            vi = vm.loops[li].vertex_index
            vuv.data[li].uv = uvs[vi]
            vcol.data[li].color = (*cols[vi], 1.0)
    vm.validate()
    vm.update()
    vo = bpy.data.objects.new(NAME + "_volcano", vm)
    coll.objects.link(vo)
    objs.append(vo)

out = jfg64.export(os.path.join(C.OUT, NAME + ".glb"), objects=objs)
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(C.OUT, NAME + ".blend"))
print("SKY", out.get("triangles") if isinstance(out, dict) else out)
