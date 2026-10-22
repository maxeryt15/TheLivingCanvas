"""Simple gold chain with a small cross pendant for the Rose NPC. Run after mpfb_resolve_clipping.py.
The chain rests on the neck base and drops into a soft U on the chest; the cross hangs from the lowest point.
"""
import bpy, bmesh, math
from mathutils import Vector, Matrix
from mathutils.bvhtree import BVHTree

for n in ('Rose_Pearls', 'Rose_Necklace'):
    old = bpy.data.objects.get(n)
    if old:
        bpy.data.objects.remove(old)
gold = bpy.data.materials['Gold']
dg = bpy.context.evaluated_depsgraph_get()
trees = []
for n in ('Rose_Low', 'Rose_Blouse', 'Rose_Collar'):      # chain lies on the blouse/neck and passes under the cardigan trim
    ev = bpy.data.objects[n].evaluated_get(dg)
    me = ev.to_mesh()
    trees.append(BVHTree.FromPolygons([ev.matrix_world @ v.co for v in me.vertices], [p.vertices[:] for p in me.polygons]))
    ev.to_mesh_clear()
C = Vector((0, -0.030, 0))
N = 72
pts, nors = [], []
for i in range(N):
    phi = 2 * math.pi * i / N                              # 0 = front
    z = 1.430 - 0.072 * max(0.0, math.cos(phi)) ** 1.3     # on the neck base, dropping into a soft U on the chest
    d = Vector((math.sin(phi), -math.cos(phi), 0))
    o = C + d * 0.22
    o.z = z
    best = None
    for t in trees:
        h = t.ray_cast(o, -d, 0.22)
        if h[0] is not None and (best is None or (h[0] - C).length > (best[0] - C).length):
            best = h
    if best is None:
        continue
    pts.append(best[0] + best[1].normalized() * 0.0022)
    nors.append(best[1].normalized())
for _ in range(4):
    pts = [p.lerp((pts[i - 1] + pts[(i + 1) % len(pts)]) / 2, 0.5) for i, p in enumerate(pts)]
cu = bpy.data.curves.new('chain', 'CURVE')
cu.dimensions = '3D'
cu.bevel_depth = 0.0017
cu.bevel_resolution = 1
cu.resolution_u = 1
sp = cu.splines.new('POLY')
sp.points.add(len(pts) - 1)
for p, v in zip(sp.points, pts):
    p.co = (v.x, v.y, v.z, 1)
sp.use_cyclic_u = True
chain = bpy.data.objects.new('chain', cu)
bpy.context.collection.objects.link(chain)
# pendant at the lowest front point
low_i = min(range(len(pts)), key=lambda i: pts[i].z)
P = pts[low_i]
nrm = nors[low_i]
b = bmesh.new()


def box(c, sx, sy, sz):
    r = bmesh.ops.create_cube(b, size=1.0)
    for v in r['verts']:
        v.co = Vector((v.co.x * sx, v.co.y * sy, v.co.z * sz)) + c


box(Vector((0, -0.0105, 0)), 0.0052, 0.0210, 0.0032)        # upright of the cross (about 2.1 cm); local Y points down the chest
box(Vector((0, -0.0060, 0)), 0.0150, 0.0050, 0.0032)        # arm, set above the middle
bmesh.ops.create_icosphere(b, subdivisions=1, radius=0.0030, matrix=Matrix.Translation((0, 0.0012, 0)))   # small bail where it meets the chain
z_ax = nrm
x_ax = Vector((0, 0, 1)).cross(z_ax).normalized()
y_ax = z_ax.cross(x_ax)                                      # points up the chest
M = Matrix(((x_ax.x, y_ax.x, z_ax.x), (x_ax.y, y_ax.y, z_ax.y), (x_ax.z, y_ax.z, z_ax.z))).to_4x4()
for v in b.verts:
    v.co = M @ v.co + P + nrm * 0.0020
for f in b.faces:
    f.smooth = False
me = bpy.data.meshes.new('cross')
b.to_mesh(me)
b.free()
cross = bpy.data.objects.new('cross', me)
bpy.context.collection.objects.link(cross)
bpy.ops.object.select_all(action='DESELECT')
chain.select_set(True)
bpy.context.view_layer.objects.active = chain
bpy.ops.object.convert(target='MESH')
chain.select_set(True)
cross.select_set(True)
bpy.ops.object.join()
ob = bpy.context.active_object
ob.name = 'Rose_Necklace'
ob.data.name = 'Rose_Necklace'
ob.data.materials.clear()
ob.data.materials.append(gold)
for p in ob.data.polygons:
    p.use_smooth = False
print('necklace built, chain points', len(pts))
