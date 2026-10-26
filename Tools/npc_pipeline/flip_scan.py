"""Caras cuya normal se invierte (dot<0 respecto al reposo) en una pose, por material y zona. SOLO LECTURA. Uso: blender -b X.blend --python flip_scan.py -- Tou BendForward"""
import bpy, sys, collections
sys.path.insert(0, r'D:\TheLivingCanvas\Tools\npc_pipeline')
import pose_lib as PL
a = sys.argv[sys.argv.index('--') + 1:]; pref = a[0]
ob = bpy.data.objects[pref + '_Mesh']; arm = bpy.data.objects[pref + '_Rig']; me = ob.data; cal = PL.calibrate(arm)
mats = [m.name if m else None for m in me.materials]
def ev():
    e = ob.evaluated_get(bpy.context.evaluated_depsgraph_get()); m = e.to_mesh(); r = ([v.co.copy() for v in m.vertices], [p.normal.copy() for p in m.polygons], [p.center.copy() for p in m.polygons]); e.to_mesh_clear(); return r
PL.reset(arm); bpy.context.view_layer.update(); R = ev()
for pose in a[1:]:
    PL.reset(arm); PL.apply(arm, cal[pose]); bpy.context.view_layer.update(); P = ev(); c = collections.Counter(); zs = collections.defaultdict(list)
    for i, p in enumerate(me.polygons):
        if R[1][i].dot(P[1][i]) < 0.0: c[mats[p.material_index]] += 1; zs[mats[p.material_index]].append(round(R[2][i].z, 2))
    print('FLIP', pose, dict(c), {k: (min(v), max(v)) for k, v in zs.items()})
