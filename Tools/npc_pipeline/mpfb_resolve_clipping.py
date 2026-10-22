"""Collision resolver for the Rose NPC clothes. Run after mpfb_clothes.py and mpfb_clothes_polish.py.
Layer order (inner to outer): body, blouse, collar, trousers, cardigan. Each outer vertex is pushed out along the inner
surface normal until it clears the inner layer by CLEAR plus its own solidify thickness. No global scaling.
"""
import bpy
import bmesh
from mathutils.bvhtree import BVHTree

CLEAR = 0.0025
ORDER = [('Rose_Blouse', ['Rose_Low']),
         ('Rose_Collar', ['Rose_Low', 'Rose_Blouse']),
         ('Rose_Trousers', ['Rose_Low', 'Rose_Blouse', 'Rose_Shoes']),
         ('Rose_Cardigan', ['Rose_Low', 'Rose_Blouse', 'Rose_Collar']),      # trousers are not pushed against: the cardigan already stands 2.6 cm off the body, farther out than the trousers (1.2 cm)
         ('Rose_Shoes', ['Rose_Low']),
         ('Rose_Glasses', ['Rose_Low'])]


def bvh_of(name):
    dg = bpy.context.evaluated_depsgraph_get()
    ev = bpy.data.objects[name].evaluated_get(dg)
    me = ev.to_mesh()
    verts = [ev.matrix_world @ v.co for v in me.vertices]
    polys = [p.vertices[:] for p in me.polygons]
    ev.to_mesh_clear()
    return BVHTree.FromPolygons(verts, polys)


def thickness(obj):
    for m in obj.modifiers:
        if m.type == 'SOLIDIFY':
            return abs(m.thickness)
    return 0.0


def relax(obj, iterations=2, factor=0.35):
    """Light Laplacian relax of interior vertices (boundaries stay put) to remove sliver facets left by the pushes."""
    bm = bmesh.new()
    bm.from_mesh(obj.data)
    interior = [v for v in bm.verts if v.link_faces and all(not e.is_boundary for e in v.link_edges)]
    for _ in range(iterations):
        bmesh.ops.smooth_vert(bm, verts=interior, factor=factor, use_axis_x=True, use_axis_y=True, use_axis_z=True)
    bm.to_mesh(obj.data)
    bm.free()


for name, inner in ORDER:
    obj = bpy.data.objects[name]
    if name in ('Rose_Cardigan', 'Rose_Blouse', 'Rose_Trousers'):
        relax(obj)
    need = CLEAR + (0.002 if name == 'Rose_Glasses' else thickness(obj))      # glasses: tube radius ~1.6 mm
    moved = 0
    for it in range(8):
        trees = [bvh_of(n) for n in inner]
        changed = 0
        for v in obj.data.vertices:
            for t in trees:
                loc, nor, idx, dist = t.find_nearest(v.co)
                if loc is None:
                    continue
                side = (v.co - loc).dot(nor)
                if side < need and dist < need * 3:
                    v.co += nor * (need - side)
                    changed += 1
        moved += changed
        obj.data.update()
        if changed == 0:
            break
    print(name, 'pushed', moved)
