"""Lista vertices del delantal hundidos en pose (SOLO LECTURA). Uso: blender -b X.blend --python apron_where.py -- Pnt Sit [--fix script]"""
import bpy, sys, runpy
sys.path.insert(0, r'D:\TheLivingCanvas\Tools\npc_pipeline')
import pose_lib as PL
from mathutils.bvhtree import BVHTree
a = sys.argv[sys.argv.index('--') + 1:]; pref, pose = a[0], a[1]
if '--fix' in a: sys.argv = ['x', '--'] + (a[a.index('--fixargs') + 1:] if '--fixargs' in a else []); runpy.run_path(a[a.index('--fix') + 1])
ob = bpy.data.objects[pref + '_Mesh']; arm = bpy.data.objects[pref + '_Rig']; me = ob.data
mats = [m.name if m else None for m in me.materials]; cal = PL.calibrate(arm)
PL.reset(arm); bpy.context.view_layer.update()
def pts():
    ev = ob.evaluated_get(bpy.context.evaluated_depsgraph_get()); m = ev.to_mesh(); P = [v.co.copy() for v in m.vertices]; ev.to_mesh_clear(); return P
R = pts(); PL.apply(arm, cal[pose]); bpy.context.view_layer.update(); P = pts()
tl = []
for p in me.polygons:
    if mats[p.material_index] == pref + '_clothes_Paint' and sum(R[v].z for v in p.vertices) / len(p.vertices) > 0.4:
        vs = list(p.vertices)
        for k in range(1, len(vs) - 1): tl.append((vs[0], vs[k], vs[k + 1]))
bvh = BVHTree.FromPolygons(P, tl)
AP = {pref + '_ApronCloth', pref + '_ApronTrim', pref + '_ApronBand'}
vs = sorted({v for p in me.polygons if mats[p.material_index] in AP for v in p.vertices})
for v in vs:
    loc, nor, idx, d = bvh.find_nearest(P[v], 0.08)
    if loc is not None and (P[v] - loc).dot(nor) < -0.015:
        print('W v%d %s rest(%.3f,%.3f,%.3f) d=%.1fmm w=%s' % (v, mats[[p.material_index for p in me.polygons if v in p.vertices][0]][4:], *R[v], (P[v] - loc).dot(nor) * 1000, {ob.vertex_groups[g.group].name: round(g.weight, 2) for g in me.vertices[v].groups}))
