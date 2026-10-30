"""Shared helpers for the Corsair Reach level scripts (run inside Blender 5.2 with the jfg64 add-on 0.6.0+).

Coordinates: the scripts think in the game's units, x east, z south (north is -z), y up. Blender is Z up with
its y = the game's -z, so G(x, z, y) gives a Blender point. Everything is made from nothing with fixed seeds.
"""
import math
import os
import random

import bmesh
import bpy
import jfg64
from mathutils import Vector
from mathutils.bvhtree import BVHTree

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "out")  # built .glb and drawn images: not committed (they hold the game's pixels)


def G(x, z, y=0.0):
    """A Blender point from game x, z (south) and y (up)."""
    return (float(x), -float(z), float(y))


def smooth(t):
    t = min(1.0, max(0.0, t))
    return t * t * (3 - 2 * t)


def new_scene(name):
    """A scene of our own with one collection for the level (never touches what is open)."""
    old = bpy.data.scenes.get(name)
    if old is not None:
        bpy.data.scenes.remove(old)
    scene = bpy.data.scenes.new(name)
    if bpy.context.window is not None:
        bpy.context.window.scene = scene
    coll = bpy.data.collections.new(name)
    scene.collection.children.link(coll)
    return scene, coll


# ------------------------------------------------------------------------------------------------ materials

def game(tex_id, surface="solid", name=None):
    return jfg64.game_texture_material(tex_id, surface, name=name)


def own_image(name, w, h, painter):
    """An image of our own, drawn by `painter(x, y) -> (r, g, b)` (0-1, y from the top) and saved as a PNG."""
    os.makedirs(OUT, exist_ok=True)
    img = bpy.data.images.get(name)
    if img is not None:
        bpy.data.images.remove(img)
    img = bpy.data.images.new(name, w, h, alpha=False)
    px = []
    for row in range(h - 1, -1, -1):  # Blender's rows go up from the bottom
        for col in range(w):
            r, g, b = painter(col, row)
            px += [r, g, b, 1.0]
    img.pixels = px
    img.filepath_raw = os.path.join(OUT, name + ".png")
    img.file_format = "PNG"
    img.save()
    return img


def own_material(name, image, surface="solid"):
    mat = bpy.data.materials.get(name) or bpy.data.materials.new(name)
    mat.use_nodes = True
    nodes = mat.node_tree.nodes
    bsdf = next(n for n in nodes if n.type == "BSDF_PRINCIPLED")
    tex = next((n for n in nodes if n.type == "TEX_IMAGE"), None) or nodes.new("ShaderNodeTexImage")
    tex.image = image
    tex.interpolation = "Closest"
    mat.node_tree.links.new(tex.outputs["Color"], bsdf.inputs["Base Color"])
    jfg64.set_surface(mat, surface)
    return mat


# ------------------------------------------------------------------------------------------------ mesh building

class Mesh:
    """Faces in game coordinates, each with a material slot and planar UVs (or given ones), built into one object.
    `face(pts, mat, facing)` takes [(x, z, y)]; `facing` (game x, z, y) turns the face to that side."""

    def __init__(self, name, materials, coll, uv_size=256.0):
        self.name, self.materials, self.coll, self.uv = name, materials, coll, uv_size
        self.verts, self.faces, self.mats, self.uvs = [], [], [], []

    def face(self, pts, mat=0, facing=None, uvs=None):
        bpts = [Vector(G(*p)) for p in pts]
        n = (bpts[1] - bpts[0]).cross(bpts[2] - bpts[0])
        if n.length < 1e-6 and len(bpts) > 3:
            n = (bpts[2] - bpts[0]).cross(bpts[3] - bpts[0])
        if n.length < 1e-6:
            return
        if facing is not None and n.dot(Vector(G(*facing))) < 0:
            bpts = bpts[::-1]
            uvs = uvs[::-1] if uvs else None
            n = -n
        if uvs is None:
            ax = 2 if abs(n.z) >= max(abs(n.x), abs(n.y)) else 0 if abs(n.x) >= abs(n.y) else 1
            keep = [k for k in range(3) if k != ax]
            uvs = [(p[keep[0]] / self.uv, p[keep[1]] / self.uv) for p in bpts]
        base = len(self.verts)
        self.verts += [p[:] for p in bpts]
        self.faces.append(tuple(range(base, base + len(bpts))))
        self.mats.append(mat)
        self.uvs.append(uvs)

    def quad2(self, pts, mat=0, apart=1.5):
        """Both sides of a face (seen from either side: thin walls), the back `apart` behind the front: two faces in
        one place flicker (z-fighting, owner's play-test)."""
        self.face(pts, mat)
        a, b, c = (Vector(G(*p)) for p in pts[:3])
        n = (b - a).cross(c - a)
        if n.length < 1e-6:
            return
        n = n.normalized() * apart
        back = []
        for p in pts[::-1]:
            q = Vector(G(*p)) - n
            back.append((q.x, -q.y, q.z))
        self.face(back, mat)

    def box(self, x0, z0, x1, z1, y0, y1, mat=0, top=None, bottom=False):
        """An axis-aligned block (game coords); top: the top's material slot."""
        top = mat if top is None else top
        xa, xb, za, zb = min(x0, x1), max(x0, x1), min(z0, z1), max(z0, z1)
        self.face([(xa, zb, y1), (xb, zb, y1), (xb, za, y1), (xa, za, y1)], top, (0, 0, 1))
        if bottom:
            self.face([(xa, za, y0), (xb, za, y0), (xb, zb, y0), (xa, zb, y0)], mat, (0, 0, -1))
        self.face([(xa, zb, y0), (xb, zb, y0), (xb, zb, y1), (xa, zb, y1)], mat, (0, 1, 0))
        self.face([(xb, za, y0), (xa, za, y0), (xa, za, y1), (xb, za, y1)], mat, (0, -1, 0))
        self.face([(xb, zb, y0), (xb, za, y0), (xb, za, y1), (xb, zb, y1)], mat, (1, 0, 0))
        self.face([(xa, za, y0), (xa, zb, y0), (xa, zb, y1), (xa, za, y1)], mat, (-1, 0, 0))

    def obox(self, cx, cz, hw, hd, yaw, y0, y1, mat=0, top=None, y1b=None):
        """A block turned by yaw degrees about y, centre cx, cz, half sizes hw (along its x) and hd. y1b: the top's
        height at its far end (+hd), for a sloped top."""
        top = mat if top is None else top
        y1b = y1 if y1b is None else y1b
        c, s = math.cos(math.radians(yaw)), math.sin(math.radians(yaw))
        corner = [(-hw, -hd), (hw, -hd), (hw, hd), (-hw, hd)]
        pts = [(cx + a * c + b * s, cz - a * s + b * c) for a, b in corner]
        tops = [y1, y1, y1b, y1b]
        self.face([(p[0], p[1], t) for p, t in zip(pts, tops)], top, (0, 0, 1))
        for i in range(4):
            a, b = pts[i], pts[(i + 1) % 4]
            mx, mz = (a[0] + b[0]) / 2 - cx, (a[1] + b[1]) / 2 - cz
            self.face([(a[0], a[1], y0), (b[0], b[1], y0), (b[0], b[1], tops[(i + 1) % 4]), (a[0], a[1], tops[i])],
                      mat, (mx, mz, 0))

    def wall(self, a, b, y0a, y0b, y1a, y1b, mat=0, facing=None, double=False):
        """A wall from a to b ((x, z)), bottom y0, top y1 at each end; facing (x, z, y) or both sides."""
        pts = [(a[0], a[1], y0a), (b[0], b[1], y0b), (b[0], b[1], y1b), (a[0], a[1], y1a)]
        if double:
            self.quad2(pts, mat)
        else:
            self.face(pts, mat, facing)

    def build(self):
        mesh = bpy.data.meshes.new(self.name)
        mesh.from_pydata(self.verts, [], self.faces)
        for m in self.materials:
            mesh.materials.append(m)
        uv = mesh.uv_layers.new(name="UV")
        for poly, mat, coords in zip(mesh.polygons, self.mats, self.uvs):
            poly.material_index = mat
            for li, c in zip(poly.loop_indices, coords):
                uv.data[li].uv = c
        mesh.validate()
        mesh.update()
        obj = bpy.data.objects.new(self.name, mesh)
        self.coll.objects.link(obj)
        return obj


def heightfield(name, coll, x0, z0, x1, z1, step, height, material_of, materials, boundary=420.0, flat_angle=0.6,
                ring_every=4, tile=3, merge_above=None, skip=None):
    """Ground from a height function: a grid over game x0..x1, z0..z1, `height(x, z)` its floor, each face's
    material from `material_of(x, z, y, slope_degrees)`, triangulated. The walkable ground stays a plain grid:
    triangles as big as the grid square at most. Bigger ones let the hero fall through or stop at an invisible wall
    (owner's play-tests): the importer gives each triangle to one segment by its centre, and where it reaches past
    the segment's split the game doesn't find it. Only ground at `merge_above` or higher (cliff tops nobody reaches)
    is merged, inside tiles of `tile` squares. skip(x, z): squares left out (ground hidden under blocks, so a fall
    can't land on it). A boundary collider wall rings the edge, `boundary` over the highest point."""
    nx, nz = int(round((x1 - x0) / step)) + 1, int(round((z1 - z0) / step)) + 1
    hs = [[height(x0 + i * step, z0 + j * step) for i in range(nx)] for j in range(nz)]
    bm = bmesh.new()
    vs = [[bm.verts.new(G(x0 + i * step, z0 + j * step, hs[j][i])) for i in range(nx)] for j in range(nz)]
    for j in range(nz - 1):
        for i in range(nx - 1):
            if skip is not None and skip(x0 + (i + 0.5) * step, z0 + (j + 0.5) * step):
                continue
            # two triangles split from (i, j) to (i + 1, j + 1), as water_surface cuts the shoreline
            a, b, c3, d = vs[j][i], vs[j][i + 1], vs[j + 1][i + 1], vs[j + 1][i]
            for tri in ((a, b, c3), (a, c3, d)):
                f = bm.faces.new(tri)
                f.normal_update()
                if f.normal.z < 0:
                    f.normal_flip()
                c = f.calc_center_median()
                slope = math.degrees(math.acos(max(-1, min(1, f.normal.z))))
                f.material_index = material_of(c.x, -c.y, c.z, slope)
    bmesh.ops.delete(bm, geom=[v for v in bm.verts if not v.link_faces], context="VERTS")
    for e in bm.edges:
        a, b = e.verts
        if merge_above is None or min(a.co.z, b.co.z) < merge_above:
            e.seam = True  # walkable ground: no merging across this edge
            continue
        for axis in (0, 1):
            if abs(a.co[axis] - b.co[axis]) < 1e-3:
                cell = (a.co[axis] - (x0 if axis == 0 else -z0)) / step
                if abs(cell / tile - round(cell / tile)) < 1e-3:
                    e.seam = True
    bmesh.ops.dissolve_limit(bm, angle_limit=math.radians(flat_angle), use_dissolve_boundaries=False,
                             verts=bm.verts[:], edges=bm.edges[:], delimit={"MATERIAL", "SEAM"})
    bmesh.ops.triangulate(bm, faces=bm.faces[:], quad_method="BEAUTY", ngon_method="BEAUTY")
    mesh = bpy.data.meshes.new(name)
    bm.to_mesh(mesh)
    bm.free()
    for m in materials:
        mesh.materials.append(m)
    _planar_uvs(mesh)
    obj = bpy.data.objects.new(name, mesh)
    coll.objects.link(obj)
    if boundary:
        top = max(max(r) for r in hs) + boundary
        ring = ([(x0 + i * step, z0) for i in range(nx)] + [(x1, z0 + j * step) for j in range(1, nz)]
                + [(x1 - i * step, z1) for i in range(1, nx)] + [(x0, z1 - j * step) for j in range(1, nz - 1)])
        corners = {0, nx - 1, nx + nz - 2, 2 * nx + nz - 3}
        keep = [k for k in range(len(ring)) if k % ring_every == 0 or k in corners]
        m = Mesh(name + "_edge", [jfg64.boundary_material()], coll)
        for n in range(len(keep)):
            ka, kb = keep[n], keep[(n + 1) % len(keep)]
            span = range(ka, kb + 1) if kb > ka else list(range(ka, len(ring))) + [0]
            low = min(height(*ring[k]) for k in span) - 60  # one tall wall per few grid squares, under them all
            a, b = ring[ka], ring[kb]
            ya = yb = low
            m.face([(a[0], a[1], ya), (b[0], b[1], yb), (b[0], b[1], top), (a[0], a[1], top)], 0,
                   ((x0 + x1) / 2 - (a[0] + b[0]) / 2, (z0 + z1) / 2 - (a[1] + b[1]) / 2, 0))
        m.build()
    return obj


def water_surface(m, height, x0, z0, x1, z1, step, level, mat=0, merge=3):
    """Water at `level` over the grid of `height` wherever the ground is below it, cut along the shoreline (the
    ground's own grid triangles clipped at the level), so the sheet never reaches under the sand: a sheet under a
    shore let the hero sink through the floor (owner's play-test). Squares wholly under water join up to `merge`
    in a row."""
    nx, nz = int(round((x1 - x0) / step)), int(round((z1 - z0) / step))
    for j in range(nz):
        run = None
        for i in range(nx + 1):
            full = False
            if i < nx:
                xa, za = x0 + i * step, z0 + j * step
                corners = [(xa, za), (xa + step, za), (xa + step, za + step), (xa, za + step)]
                hs = [height(x, z) for x, z in corners]
                full = max(hs) < level - 0.5
            if full and (run is None or i - run < merge):
                if run is None:
                    run = i
                continue
            if run is not None:  # close the run of whole squares
                xa, xb, za = x0 + run * step, x0 + i * step, z0 + j * step
                m.face([(xa, za, level), (xb, za, level), (xb, za + step, level), (xa, za + step, level)], mat,
                       (0, 0, 1))
                run = i if full else None
                if full:
                    continue
            if i >= nx or min(hs) >= level:
                continue
            pts = [(x, z, h) for (x, z), h in zip(corners, hs)]
            for tri in ((pts[0], pts[1], pts[2]), (pts[0], pts[2], pts[3])):
                poly = []
                for k in range(3):
                    p, q = tri[k], tri[(k + 1) % 3]
                    if p[2] < level:
                        poly.append((p[0], p[1]))
                    if (p[2] < level) != (q[2] < level):
                        t = (level - p[2]) / (q[2] - p[2])
                        poly.append((p[0] + (q[0] - p[0]) * t, p[1] + (q[1] - p[1]) * t))
                if len(poly) >= 3:
                    m.face([(x, z, level) for x, z in poly], mat, (0, 0, 1))


def tiled(m, x0, z0, x1, z1, y0, mat=0, y1=None, along="x", size=130.0, facing=(0, 0, 1)):
    """A floor over x0..x1, z0..z1 in squares of about `size` (no big floor triangles: see heightfield); y0 at the
    x0 (or z0) end and y1 at the other (a ramp along `along`). facing (0, 0, -1) makes a ceiling."""
    y1 = y0 if y1 is None else y1
    nx = max(1, math.ceil(abs(x1 - x0) / size))
    nz = max(1, math.ceil(abs(z1 - z0) / size))

    def hy(x, z):
        t = (x - x0) / (x1 - x0) if along == "x" else (z - z0) / (z1 - z0)
        return y0 + (y1 - y0) * t
    for a in range(nx):
        u0, u1 = x0 + (x1 - x0) * a / nx, x0 + (x1 - x0) * (a + 1) / nx
        for b in range(nz):
            v0, v1 = z0 + (z1 - z0) * b / nz, z0 + (z1 - z0) * (b + 1) / nz
            m.face([(u0, v0, hy(u0, v0)), (u1, v0, hy(u1, v0)), (u1, v1, hy(u1, v1)), (u0, v1, hy(u0, v1))], mat,
                   facing)
    return hy


def sides(m, x0, z0, x1, z1, y0, top, mat=0, which="nsew", inset=0.0, inward=False):
    """The walls of a block x0..x1, z0..z1 from y0 up to `top` (a height or top(x, z)), facing out (inward: facing
    in, a room's walls), set `inset` in from its top's edges where a neighbour's wall shares the plane (two faces in
    one plane flicker). which: n (-z), s (+z), e (+x), w (-x)."""
    t = top if callable(top) else (lambda x, z, v=top: v)
    xa, xb, za, zb = min(x0, x1) + inset, max(x0, x1) - inset, min(z0, z1) + inset, max(z0, z1) - inset
    k = -1 if inward else 1
    if "n" in which:
        m.face([(xb, za, y0), (xa, za, y0), (xa, za, t(xa, za)), (xb, za, t(xb, za))], mat, (0, -k, 0))
    if "s" in which:
        m.face([(xa, zb, y0), (xb, zb, y0), (xb, zb, t(xb, zb)), (xa, zb, t(xa, zb))], mat, (0, k, 0))
    if "e" in which:
        m.face([(xb, zb, y0), (xb, za, y0), (xb, za, t(xb, za)), (xb, zb, t(xb, zb))], mat, (k, 0, 0))
    if "w" in which:
        m.face([(xa, za, y0), (xa, zb, y0), (xa, zb, t(xa, zb)), (xa, za, t(xa, za))], mat, (-k, 0, 0))


def block(m, x0, z0, x1, z1, y0, y1, side, top=None, which="nsew", size=130.0, y1b=None, along="x", inset=0.0):
    """A walkable block: its top tiled (size None: one face, for tops nobody walks on), y1 to y1b along `along` for
    a ramp, and its walls from y0 on the sides in `which`."""
    top = side if top is None else top
    if size is None:
        y1b_ = y1 if y1b is None else y1b
        hy = (lambda x, z: y1 + (y1b_ - y1) * ((x - x0) / (x1 - x0) if along == "x" else (z - z0) / (z1 - z0)))
        m.face([(x0, z0, hy(x0, z0)), (x1, z0, hy(x1, z0)), (x1, z1, hy(x1, z1)), (x0, z1, hy(x0, z1))], top,
               (0, 0, 1))
    else:
        hy = tiled(m, x0, z0, x1, z1, y1, top, y1b, along, size)
    if which:
        sides(m, x0, z0, x1, z1, y0, hy, side, which, inset)
    return hy


def post(m, x, z, r, y0, y1, mat=0, n=6, cap=True, phase=0.0):
    """An n-sided post (a piling, a mast) from y0 to y1."""
    ring = [(x + r * math.cos(phase + k * math.tau / n), z + r * math.sin(phase + k * math.tau / n)) for k in range(n)]
    for k in range(n):
        a, b = ring[k], ring[(k + 1) % n]
        m.face([(a[0], a[1], y0), (b[0], b[1], y0), (b[0], b[1], y1), (a[0], a[1], y1)], mat,
               ((a[0] + b[0]) / 2 - x, (a[1] + b[1]) / 2 - z, 0))
    if cap:
        m.face([(p[0], p[1], y1) for p in ring], mat, (0, 0, 1))


def collider(e, a, b, y0, y1):
    """An invisible wall from a to b ((x, z)), y0 to y1, solid from both sides (two faces: Mesh `e` of the boundary
    material). Over a parapet or bulwark the player sees, never standing in the open."""
    e.face([(a[0], a[1], y0), (b[0], b[1], y0), (b[0], b[1], y1), (a[0], a[1], y1)], 0, None)
    e.face([(b[0], b[1], y0), (a[0], a[1], y0), (a[0], a[1], y1), (b[0], b[1], y1)], 0, None)


def rects_minus(rect, holes):
    """The parts of rect (x0, z0, x1, z1) outside the holes, as rectangles: the cells between all the edges, joined
    along x in each row."""
    x0, z0, x1, z1 = rect
    xs = sorted({x0, x1} | {v for h in holes for v in (h[0], h[2]) if x0 < v < x1})
    zs = sorted({z0, z1} | {v for h in holes for v in (h[1], h[3]) if z0 < v < z1})
    out = []
    for j in range(len(zs) - 1):
        run = None
        for i in range(len(xs) - 1):
            cx, cz = (xs[i] + xs[i + 1]) / 2, (zs[j] + zs[j + 1]) / 2
            free = not any(h[0] < cx < h[2] and h[1] < cz < h[3] for h in holes)
            if free and run is None:
                run = xs[i]
            if not free and run is not None:
                out.append((run, zs[j], xs[i], zs[j + 1]))
                run = None
        if run is not None:
            out.append((run, zs[j], xs[-1], zs[j + 1]))
    return out


def _cuts(a, b, edges, step):
    """Points from a to b through every edge between them, no gap over `step`."""
    pts = sorted({a, b} | {v for v in edges if a < v < b})
    out = [pts[0]]
    for p, q in zip(pts, pts[1:]):
        n = max(1, math.ceil((q - p) / step - 1e-6))
        out += [p + (q - p) * k / n for k in range(1, n + 1)]
    return out


def water_box(m, rect, holes, floor_y, level, floor_mat, water_mat, piece=(200.0, 100.0), wm=None):
    """A pool in a walled hollow: its floor at floor_y (in m) and its surface at `level` (in wm, or m) over rect
    minus holes (blocks standing in it), in pieces of at most piece (x, z): walkable floor and water in small
    pieces (see heightfield). One grid through every hole's edges, so neighbouring pieces share whole edges (a piece
    edge ending on the middle of another's reads as a water edge hovering in the open). The surface never reaches
    under anything solid."""
    wm = wm or m
    x0, z0, x1, z1 = rect
    xs = _cuts(x0, x1, [v for h in holes for v in (h[0], h[2])], piece[0])
    zs = _cuts(z0, z1, [v for h in holes for v in (h[1], h[3])], piece[1])
    for i in range(len(xs) - 1):
        for j in range(len(zs) - 1):
            u0, u1, v0, v1 = xs[i], xs[i + 1], zs[j], zs[j + 1]
            cx, cz = (u0 + u1) / 2, (v0 + v1) / 2
            if any(h[0] < cx < h[2] and h[1] < cz < h[3] for h in holes):
                continue
            m.face([(u0, v0, floor_y), (u1, v0, floor_y), (u1, v1, floor_y), (u0, v1, floor_y)], floor_mat, (0, 0, 1))
            wm.face([(u0, v0, level), (u1, v0, level), (u1, v1, level), (u0, v1, level)], water_mat, (0, 0, 1))


def _planar_uvs(mesh, size=256.0):
    uv = mesh.uv_layers.get("UV") or mesh.uv_layers.new(name="UV")
    for poly in mesh.polygons:
        n = poly.normal
        ax = 2 if abs(n.z) >= max(abs(n.x), abs(n.y)) * 0.8 else 0 if abs(n.x) >= abs(n.y) else 1
        keep = [k for k in range(3) if k != ax]
        for li in poly.loop_indices:
            c = mesh.vertices[mesh.loops[li].vertex_index].co
            uv.data[li].uv = (c[keep[0]] / size, c[keep[1]] / size)


def boulder(m, x, z, y, r, h, seed, mat=0, sides=7, sink=18.0):
    """A lumpy boulder of our own into Mesh `m` (game coords): `sides`-sided, three rings and a crown, r across
    and h tall over the floor y (about 35 triangles at 7 sides). As squad cover: r 50+ and h 100+."""
    rng = random.Random(seed)
    rings = []
    for frac, rad in ((-sink / max(h, 1), 0.9), (0.45, 1.08), (0.82, 0.72)):
        ring = []
        for k in range(sides):
            a = k * math.tau / sides + rng.uniform(-0.25, 0.25) + seed
            rr = r * rad * rng.uniform(0.85, 1.12)
            ring.append((x + rr * math.cos(a), z + rr * math.sin(a), y + h * frac + rng.uniform(-6, 6)))
        rings.append(ring)
    apex = (x + rng.uniform(-r, r) * 0.15, z + rng.uniform(-r, r) * 0.15, y + h)
    for j in range(2):
        for k in range(sides):
            a0, b0 = rings[j][k], rings[j][(k + 1) % sides]
            a1, b1 = rings[j + 1][k], rings[j + 1][(k + 1) % sides]
            out = ((a0[0] + b0[0]) / 2 - x, (a0[1] + b0[1]) / 2 - z, 0.2 * j)
            m.face([a0, b0, b1, a1], mat, out)
    for k in range(sides):
        a, b = rings[2][k], rings[2][(k + 1) % sides]
        m.face([a, b, apex], mat, ((a[0] + b[0]) / 2 - x, (a[1] + b[1]) / 2 - z, 1.0))


def decal(m, pts, mat):
    """A picture of our own on a quad, the whole image once: pts bottom-left, bottom-right, top-right, top-left;
    seen from both sides."""
    m.face(pts, mat, None, [(0, 0), (1, 0), (1, 1), (0, 1)])
    # from behind, read the right way round, and 2 units apart: two faces in one place flicker (owner's play-test)
    a, b, c = (Vector(G(*p)) for p in pts[:3])
    n = (b - a).cross(c - a).normalized() * 2.0  # the front's facing, in Blender space
    back = []
    for p in pts[::-1]:
        q = Vector(G(*p)) - n
        back.append((q.x, -q.y, q.z))
    m.face(back, mat, None, [(1, 1), (0, 1), (0, 0), (1, 0)])


def low_rock(name, coll, x, z, y, radius, seed, material, squash=1.0, detail=1, keep=0.55):
    """A jfg64 rock, decimated to `keep` of its triangles (a level's budget is small)."""
    obj = jfg64.rock(name, radius=radius, seed=seed, squash=squash, location=G(x, z, y), material=material,
                     collection=coll, detail=detail)
    if keep < 1.0:
        mod = obj.modifiers.new("lowpoly", "DECIMATE")
        mod.ratio = keep
        dg = bpy.context.evaluated_depsgraph_get()
        mesh = bpy.data.meshes.new_from_object(obj.evaluated_get(dg))
        old = obj.data
        obj.modifiers.clear()
        obj.data = mesh
        bpy.data.meshes.remove(old)
    return obj


def floor_at(objs, x, z, below=None):
    """The highest floor of `objs` under game (x, z) (or the first under `below`), or None."""
    best = None
    for o in objs:
        h = jfg64.ground_height(o, x, -z, below=below)
        if h is not None and (best is None or h > best):
            best = h
    return best


# ------------------------------------------------------------------------------------------------ light bake

def bake(objects, sun_dir, sun, ambient, tints=None, lamps=(), extra=None, ao_len=220.0, ao_strength=0.45,
         shadow=0.3, skip=("collider", "water"), soft=None):
    """Vertex light of our own on the "Col" layer, per face corner: ambient (darkened by ambient occlusion: a few
    short rays) + sun (Lambert, shadowed by a ray to the sun), times the material's tint, plus warm pools round
    `lamps` [(x, z, y, radius, (r, g, b))]. extra(x, z, y, material_name) -> (r, g, b) multiplies at the end
    (wet sand, soot). Water and colliders are skipped (and don't cast). tints: {material name: (r, g, b)}.
    soft: {material name: (shadow, ao_strength)} for open ground, where a hard shadow on one corner of a big
    triangle spreads across all of it (dark wedges on the beach: owner's play-test)."""
    soft = soft or {}
    tints = tints or {}
    dg = bpy.context.evaluated_depsgraph_get()
    verts, polys = [], []
    for o in objects:
        if o.type != "MESH":
            continue
        m = o.data
        mw = o.matrix_world
        base = len(verts)
        verts += [mw @ v.co for v in m.vertices]
        for p in m.polygons:
            mat = m.materials[p.material_index] if m.materials else None
            if mat is not None and jfg64.surface_of(mat) in skip:
                continue
            polys.append([base + i for i in p.vertices])
    tree = BVHTree.FromPolygons(verts, polys)
    to_sun = -Vector(sun_dir).normalized()
    rng = random.Random(7)
    dirs = []
    for k in range(6):
        a = k * math.tau / 6 + 0.3
        dirs.append(Vector((math.cos(a) * 0.75, math.sin(a) * 0.75, 0.66)).normalized())
    for o in objects:
        if o.type != "MESH":
            continue
        m = o.data
        attr = m.color_attributes.get("Col")
        if attr is not None:
            m.color_attributes.remove(attr)
        attr = m.color_attributes.new("Col", "BYTE_COLOR", "CORNER")
        m.color_attributes.active_color = attr
        mw = o.matrix_world
        nm = mw.to_3x3().inverted_safe().transposed()
        for p in m.polygons:
            mat = m.materials[p.material_index] if m.materials else None
            mname = mat.name if mat else ""
            surf = jfg64.surface_of(mat) if mat else "solid"
            n = (nm @ p.normal).normalized()
            t = tints.get(mname, (1.0, 1.0, 1.0))
            sh, aos = soft.get(mname, (shadow, ao_strength))
            for li in p.loop_indices:
                co = mw @ m.vertices[m.loops[li].vertex_index].co
                if surf in ("collider",):
                    attr.data[li].color = (1, 1, 1, 1)
                    continue
                if surf == "water":
                    c = [min(1.0, ambient[i] + sun[i] * 0.7) for i in range(3)]
                    attr.data[li].color = (*c, 1.0)
                    continue
                start = co + n * 3.0
                d = max(0.0, n.dot(to_sun))
                lit = d
                if d > 0 and tree.ray_cast(start, to_sun, 6000.0)[0] is not None:
                    lit = d * sh
                hits = 0
                if ao_len:
                    # the hemisphere round the normal: turn the fixed directions to it
                    rot = Vector((0, 0, 1)).rotation_difference(n)
                    for dvec in dirs:
                        if tree.ray_cast(start, rot @ dvec, ao_len)[0] is not None:
                            hits += 1
                ao = 1.0 - aos * hits / len(dirs)
                col = [(ambient[i] * ao + sun[i] * lit) * t[i] for i in range(3)]
                gx, gz, gy = co.x, -co.y, co.z
                for (lx, lz, ly, r, lc) in lamps:
                    dist = math.sqrt((gx - lx) ** 2 + (gz - lz) ** 2 + (gy - ly) ** 2)
                    if dist < r:
                        k = (1 - dist / r) ** 2
                        col = [col[i] + lc[i] * k for i in range(3)]
                if extra is not None:
                    e = extra(gx, gz, gy, mname)
                    col = [col[i] * e[i] for i in range(3)]
                attr.data[li].color = (*[min(1.0, max(0.0, c)) for c in col], 1.0)
        m.update()
