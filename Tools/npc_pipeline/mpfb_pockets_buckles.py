"""Trouser pockets (slanted front pockets + stitched back patch pockets) and gold shoe buckles with a leather strap.
Run after mpfb_finish.py (needs the final trousers and shoes)."""
import bpy, bmesh, math
from mathutils import Vector, Matrix

for n in ('Rose_Pockets', 'Rose_ShoeBuckles'):
    o = bpy.data.objects.get(n)
    if o:
        bpy.data.objects.remove(o)


def mat(name, col, metal=0.0, rough=0.7):
    m = bpy.data.materials.get(name) or bpy.data.materials.new(name)
    m.use_nodes = True
    b = next(n for n in m.node_tree.nodes if n.type == 'BSDF_PRINCIPLED')
    b.inputs['Base Color'].default_value = col
    b.inputs['Metallic'].default_value = metal
    b.inputs['Roughness'].default_value = rough
    return m


pocket_m = mat('Trousers_Pocket', (0.035, 0.035, 0.040, 1))
strap_m = mat('Shoes_Strap', (0.055, 0.025, 0.012, 1), 0.0, 0.6)
gold = bpy.data.materials['Gold']
dg = bpy.context.evaluated_depsgraph_get()
scene = bpy.context.scene


from mathutils.bvhtree import BVHTree
_bvh = {}


def cast(obj_name, origin, direction):
    """Ray cast against ONE object only (so other clothes never block it)."""
    if obj_name not in _bvh:
        ev = bpy.data.objects[obj_name].evaluated_get(dg)
        me_ = ev.to_mesh()
        _bvh[obj_name] = BVHTree.FromPolygons([ev.matrix_world @ v.co for v in me_.vertices], [p.vertices[:] for p in me_.polygons])
        ev.to_mesh_clear()
    h = _bvh[obj_name].ray_cast(origin, direction)
    if h[0] is not None:
        n = h[1].normalized()
        return h[0], (n if n.dot(direction) < 0 else -n)
    return None, None


def strip_on_surface(bm, obj_name, path, width_fn, ray_dir_fn, raised, mi, skirt=0.0015):
    """Raised ribbon following `path` (list of (x,y,z) ray origins). ray_dir_fn gives the cast direction."""
    left, right = [], []
    for i, p in enumerate(path):
        loc, nor = cast(obj_name, p, ray_dir_fn(p))
        if loc is None:
            return
        t = (path[min(i + 1, len(path) - 1)] - path[max(i - 1, 0)])
        side = t.cross(nor).normalized()
        w = width_fn(i / (len(path) - 1)) / 2
        left.append((loc + nor * raised + side * w, loc - nor * skirt + side * w))
        right.append((loc + nor * raised - side * w, loc - nor * skirt - side * w))
    for i in range(len(path) - 1):
        a0, a1, b0, b1 = left[i][0], left[i + 1][0], right[i][0], right[i + 1][0]
        for quad in ((a0, a1, b1, b0),):                                   # top
            f = bm.faces.new([bm.verts.new(v) for v in quad]); f.material_index = mi; f.smooth = False
        for s_, o_ in ((left, 0), (right, 1)):                             # side walls
            q = (s_[i][0], s_[i + 1][0], s_[i + 1][1], s_[i][1])
            f = bm.faces.new([bm.verts.new(v) for v in (q if o_ == 0 else q[::-1])]); f.material_index = mi; f.smooth = False


# ---------------------------------------------------------------- pockets: two front patch pockets on the outer thigh (outline with a stitched inner line)
def pocket_path(sx):
    pts = [(0.160, 0.886), (0.122, 0.886), (0.098, 0.886), (0.090, 0.880), (0.088, 0.868), (0.088, 0.832), (0.088, 0.806),
           (0.091, 0.790), (0.100, 0.780), (0.115, 0.776), (0.135, 0.776), (0.160, 0.776)]
    return [(sx * x, z - 0.048) for x, z in pts]               # top edge sits just below the cardigan hem


def densify(pts, per=3):
    out = []
    for (x0, z0), (x1, z1) in zip(pts, pts[1:]):
        for k in range(per):
            t = k / per
            out.append((x0 + (x1 - x0) * t, z0 + (z1 - z0) * t))
    out.append(pts[-1])
    return out


bm = bmesh.new()
for sx in (1, -1):
    pts = densify(pocket_path(sx))
    path = [Vector((x, -0.45, z)) for x, z in pts]
    strip_on_surface(bm, 'Rose_Trousers', path, lambda u: 0.0055, lambda p: Vector((0, 1, 0)), 0.0030, 0)         # pocket outline
    inner = [Vector((x - sx * 0.0075 if abs(x) < 0.15 else x, -0.45, z + (0.0075 if z > 0.80 else (0.0 if z > 0.745 else -0.0075)) * (-1 if z > 0.80 else 1) * (-1 if z > 0.80 else 1))) for x, z in pts]
    strip_on_surface(bm, 'Rose_Trousers', inner, lambda u: 0.0022, lambda p: Vector((0, 1, 0)), 0.0020, 0)        # stitched inner line
me = bpy.data.meshes.new('Rose_Pockets')
bm.to_mesh(me)
bm.free()
ob = bpy.data.objects.new('Rose_Pockets', me)
bpy.context.collection.objects.link(ob)
me.materials.append(pocket_m)

# ---------------------------------------------------------------- shoe buckles: leather strap over the instep + gold buckle
bm = bmesh.new()
YS = -0.118
for side in (1, -1):
    cx = 0.190 * side
    # strap across the top of the shoe (rays straight down, sweeping from one flank to the other)
    path = []
    for i in range(13):
        t = -1 + 2 * i / 12
        path.append(Vector((cx + t * 0.047, YS, 0.30)))
    strip_on_surface(bm, 'Rose_Shoes', path, lambda u: 0.0150, lambda p: Vector((0, 0, -1)), 0.0022, 0, 0.002)
    # buckle frame on top (gold), built in a local frame aligned to the surface
    loc, nor = cast('Rose_Shoes', Vector((cx, YS, 0.30)), Vector((0, 0, -1)))
    if loc is None:
        continue
    z_ax = nor
    x_ax = Vector((0, 1, 0)).cross(z_ax).normalized() * -1
    y_ax = z_ax.cross(x_ax)
    M = Matrix(((x_ax.x, y_ax.x, z_ax.x), (x_ax.y, y_ax.y, z_ax.y), (x_ax.z, y_ax.z, z_ax.z))).to_4x4()
    def box(c, sx_, sy_, sz_, mi=1):
        r = bmesh.ops.create_cube(bm, size=1.0)
        for v in r['verts']:
            v.co = M @ (Vector((v.co.x * sx_, v.co.y * sy_, v.co.z * sz_)) + c) + loc + nor * 0.0022
        for f in {f for v in r['verts'] for f in v.link_faces}:
            f.material_index = mi
            f.smooth = False

    W, H, T, Z = 0.036, 0.026, 0.0045, 0.0048
    box(Vector((0, H / 2 - T / 2, Z)), W, T, 0.0030)               # top bar
    box(Vector((0, -H / 2 + T / 2, Z)), W, T, 0.0030)              # bottom bar
    box(Vector((W / 2 - T / 2, 0, Z)), T, H, 0.0030)               # right bar
    box(Vector((-W / 2 + T / 2, 0, Z)), T, H, 0.0030)              # left bar
    box(Vector((0.002, 0, Z + 0.0008)), 0.0030, H - T, 0.0026)     # centre prong bar
me = bpy.data.meshes.new('Rose_ShoeBuckles')
bm.to_mesh(me)
ob = bpy.data.objects.new('Rose_ShoeBuckles', me)
bpy.context.collection.objects.link(ob)
me.materials.append(strap_m)
me.materials.append(gold)
bm.free()
print('pockets built')
