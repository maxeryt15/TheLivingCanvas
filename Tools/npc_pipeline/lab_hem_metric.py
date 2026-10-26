"""Laboratorio (solo memoria, NO guarda): aplica en memoria layer_weights.reweight(pref, ztop, tmax, xs) y mide capas camiseta/pantalon en reposo, poses y Walk.
Uso: blender -b WORK.blend --python lab_hem_metric.py -- Doc [ztop tmax xs]   (sin parametros = linea base)"""
import bpy, sys
sys.path.insert(0, r'D:\TheLivingCanvas\Tools\npc_pipeline')
import pose_lib as PL, layer_clip_scan as LC, layer_weights as LW
a = sys.argv[sys.argv.index('--') + 1:]; pref = a[0]
if len(a) > 1: print('LAB reweight n=', LW.reweight(pref, float(a[1]), float(a[2]), float(a[3])))
ob, me, U, L, fu, fl = LC.setup(pref); arm = bpy.data.objects[pref + '_Rig']
name = {'Gen': 'Gentleman', 'Doc': 'Docent', 'Pnt': 'Painter', 'Grd': 'Guard', 'Cur': 'Curator', 'Caf': 'Cafe', 'Cou': 'Courier', 'Pnt': 'Painter', 'Tou': 'Tourist', 'Gar': 'Gardener'}[pref]
walk = next(x for x in bpy.data.actions if x.name.startswith('U_') and '_%s_Walk' % name in x.name); cal = PL.calibrate(arm); S = bpy.context.scene
zU = min(me.vertices[i].co.z for i in U); zL = max(me.vertices[i].co.z for i in L)
def one(tag):
    P_, q1, q2 = LC.measure(ob, me, U, L, fu, fl, zU - 0.02, zL + 0.05)
    n1 = [d for d in q1.values() if d < -0.002]; n2 = [d for d in q2.values() if d > 0.002]
    print('MET %-12s upper-in-lower n=%3d worst %5.1fmm | lower-out-of-upper n=%3d worst %5.1fmm' % (tag, len(n1), -min(n1, default=0) * 1000, len(n2), max(n2, default=0) * 1000))
PL.reset(arm); one('Idle')
for nm in ('Sit', 'Crouch', 'BendForward', 'Twist_A', 'LegKick_L', 'LegKick_R', 'KneeBend_R'):
    PL.reset(arm); PL.apply(arm, cal[nm]); one(nm)
PL.reset(arm); ad = arm.animation_data or arm.animation_data_create(); ad.action = walk; ad.action_slot = walk.slots[0]
for f in (1, 5, 9, 13, 17, 21, 25, 29, 33, 37): S.frame_set(f); bpy.context.view_layer.update(); one('Walk@%d' % f)
