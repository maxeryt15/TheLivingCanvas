"""Mide cuanto queda la tira del bolso (Stu_BagStrap) por dentro de la camiseta (Stu_clothes_Paint, isla superior) en varias poses. SOLO LECTURA.
Uso: blender -b X.blend --python strap_scan.py -- Stu"""
import bpy, sys, numpy as np
sys.path.insert(0, r'D:\TheLivingCanvas\Tools\npc_pipeline')
import pose_lib as PL
from mathutils.bvhtree import BVHTree
pref = sys.argv[sys.argv.index('--') + 1]
O = bpy.data.objects; ob = O[pref + '_Mesh']; arm = O[pref + '_Rig']; me = ob.data; S = bpy.context.scene
mats = [m.name for m in me.materials]; cal = PL.calibrate(arm)
CL = [p.index for p in me.polygons if mats[p.material_index] == pref + '_clothes_Paint']
ST = [p for p in me.polygons if mats[p.material_index] == pref + '_BagStrap']
sv = sorted({v for p in ST for v in p.vertices})
def pts():
    ev = ob.evaluated_get(bpy.context.evaluated_depsgraph_get()); m = ev.to_mesh(); P = [v.co.copy() for v in m.vertices]; ev.to_mesh_clear(); return P
def meas(tag):
    P = pts(); tris = []
    for i in CL:
        vs = list(me.polygons[i].vertices)
        for k in range(1, len(vs) - 1): tris.append((vs[0], vs[k], vs[k + 1]))
    bvh = BVHTree.FromPolygons(P, tris); dv = []; dc = []
    for v in sv:
        loc, nor, idx, dist = bvh.find_nearest(P[v], 0.05)
        if loc is not None: dv.append((P[v] - loc).dot(nor))
    for p in ST:
        c = sum((P[v] for v in p.vertices), P[p.vertices[0]] * 0) / len(p.vertices)
        loc, nor, idx, dist = bvh.find_nearest(c, 0.05)
        if loc is not None: dc.append((c - loc).dot(nor))
    dv = np.array(dv) * 1000; dc = np.array(dc) * 1000
    print('STRAP %-14s verts<-1mm %2d/%d (min %.1f) | face centers<0.5mm %2d/%d (min %.1f)' % (tag, (dv < -1).sum(), len(dv), dv.min(), (dc < 0.5).sum(), len(dc), dc.min()))
PL.reset(arm); meas('Idle')
for p in ('ArmsUp_L', 'ArmsUp_R', 'ElbowBend_R', 'ShoulderCross_L', 'BendForward', 'Twist_A', 'Twist_B', 'Sit'):
    PL.reset(arm); PL.apply(arm, cal[p]); meas(p)
walk = next(x for x in bpy.data.actions if x.name.startswith('U_') and '_Student_Walk' in x.name)
PL.reset(arm); ad = arm.animation_data or arm.animation_data_create(); ad.action = walk; ad.action_slot = walk.slots[0]
for f in (1, 10, 20, 30, 40): S.frame_set(f); bpy.context.view_layer.update(); meas('Walk@%d' % f)
ad.action = None; PL.reset(arm)
