"""Mide el forro (material Caf_Lining_Mat) contra el vestido en poses y Walk: por vertice del forro, distancia con signo a la malla evaluada del vestido (+ = fuera). Uso: blender -b X.blend --python check_caf_lining.py"""
import bpy, sys
sys.path.insert(0, r'D:\TheLivingCanvas\Tools\npc_pipeline')
import pose_lib as PL
from mathutils.bvhtree import BVHTree
ob = bpy.data.objects['Caf_Mesh']; arm = bpy.data.objects['Caf_Rig']; S = bpy.context.scene
cal = PL.calibrate(arm)
def meas(tag):
    dg = bpy.context.evaluated_depsgraph_get(); ev = ob.evaluated_get(dg); me = ev.to_mesh(); mn = [m.name if m else None for m in me.materials]
    pos = [v.co.copy() for v in me.vertices]
    tl = [(p.vertices[0], p.vertices[k], p.vertices[k + 1]) for p in me.polygons if mn[p.material_index] == 'Caf_clothes_Paint' and pos[p.vertices[0]].z > 0.3 for k in range(1, len(p.vertices) - 1)]
    bvh = BVHTree.FromPolygons(pos, tl)
    lv = sorted({v for p in me.polygons if mn[p.material_index] == 'Caf_Lining_Mat' for v in p.vertices})
    out = []
    for i in lv:
        loc, n, idx, d = bvh.find_nearest(pos[i]); out.append((pos[i] - loc).dot(n))
    print('   which', [(j, round(x*1000)) for j, x in zip(lv, out) if x > 0]) if tag in ('Crouch','BendForward') else None; n_out = sum(1 for x in out if x > 0.0)
    print('LIN %-10s verts %d outside %d maxOut %.1fmm' % (tag, len(out), n_out, max(out) * 1000)); ev.to_mesh_clear()
PL.reset(arm); meas('Idle')
for nm in ('Sit', 'Crouch', 'BendForward', 'LegKick_L', 'KneeBend_R', 'Twist_A'):
    PL.reset(arm); PL.apply(arm, cal[nm]); bpy.context.view_layer.update(); meas(nm)
walk = next(x for x in bpy.data.actions if x.name.startswith('U_') and '_Cafe_Walk' in x.name or x.name.startswith('U_') and '_Caf_Walk' in x.name)
PL.reset(arm); ad = arm.animation_data or arm.animation_data_create(); ad.action = walk; ad.action_slot = walk.slots[0]
for f in (1, 9, 17, 25, 33): S.frame_set(f); bpy.context.view_layer.update(); meas('Walk@%d' % f)
