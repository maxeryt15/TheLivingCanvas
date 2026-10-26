"""Mide cuanto quedan DENTRO de una prenda base los vertices de otras piezas (delantal, correa...) en varias poses y Walk. SOLO LECTURA (no guarda).
Uso: blender -b X.blend --python layer_scan.py -- Caf Caf_ApronCloth,Caf_ApronTrim,Caf_ApronBand [zmin_base=0.4]
Base = caras de <Pref>_clothes_Paint con centroide z > zmin_base en reposo (excluye zapatos). dist con signo respecto a la normal de la base (negativo = dentro)."""
import bpy, sys, numpy as np
sys.path.insert(0, r'D:\TheLivingCanvas\Tools\npc_pipeline')
import pose_lib as PL
from mathutils.bvhtree import BVHTree
a = sys.argv[sys.argv.index('--') + 1:]
if '--fix' in a:   # aplica en memoria un script de correccion antes de medir (sin guardar): --fix <script> [args del script tras --fixargs]
    import runpy; _fa = a[a.index('--fix') + 2:] if len(a) > a.index('--fix') + 2 else []; _fs = a[a.index('--fix') + 1]; sys.argv = ['x', '--'] + (a[a.index('--fixargs') + 1:] if '--fixargs' in a else []); runpy.run_path(_fs); sys.argv = ['x', '--'] + a
    a = a[:a.index('--fix')] + a[a.index('--fix') + 2:]
pref = a[0]; parts = a[1].split(','); zmin = float(a[2]) if len(a) > 2 else 0.4
O = bpy.data.objects; ob = O[pref + '_Mesh']; arm = O[pref + '_Rig']; me = ob.data; S = bpy.context.scene
mats = [m.name if m else None for m in me.materials]; cal = PL.calibrate(arm)
PL.reset(arm); bpy.context.view_layer.update()
def pts():
    ev = ob.evaluated_get(bpy.context.evaluated_depsgraph_get()); m = ev.to_mesh(); P = [v.co.copy() for v in m.vertices]; ev.to_mesh_clear(); return P
P0 = pts()
CL = [p.index for p in me.polygons if mats[p.material_index] == pref + '_clothes_Paint' and sum(P0[v].z for v in p.vertices) / len(p.vertices) > zmin]
TR = [p for p in me.polygons if mats[p.material_index] in parts]
tv = sorted({v for p in TR for v in p.vertices})
tris = []
for i in CL:
    vs = list(me.polygons[i].vertices)
    for k in range(1, len(vs) - 1): tris.append((vs[0], vs[k], vs[k + 1]))
print('LS base faces', len(CL), 'part verts', len(tv), 'part faces', len(TR))
def meas(tag):
    P = pts(); bvh = BVHTree.FromPolygons(P, tris); d = []
    for v in tv:
        loc, nor, idx, dist = bvh.find_nearest(P[v], 0.08)
        if loc is not None: d.append((P[v] - loc).dot(nor))
    d = np.array(d) * 1000
    print('LS %-14s verts<-1mm %3d/%d  <-5mm %3d  <-15mm %3d  (min %.1f)' % (tag, (d < -1).sum(), len(d), (d < -5).sum(), (d < -15).sum(), d.min()))
meas('Idle')
for p in ('Sit', 'Crouch', 'BendForward', 'Twist_A', 'LegKick_L', 'LegKick_R', 'KneeBend_R'):
    PL.reset(arm); PL.apply(arm, cal[p]); meas(p)
name = {'Caf': 'Cafe', 'Gar': 'Gardener', 'Tou': 'Tourist', 'Cur': 'Curator', 'Cou': 'Courier', 'Pnt': 'Painter', 'Rose': 'Rose'}[pref]
walk = next(x for x in bpy.data.actions if x.name.startswith('U_') and '_%s_Walk' % name in x.name)
PL.reset(arm); ad = arm.animation_data or arm.animation_data_create(); ad.action = walk; ad.action_slot = walk.slots[0]
for f in (1, 5, 9, 13, 17, 21, 25, 29, 33, 37): S.frame_set(f); bpy.context.view_layer.update(); meas('Walk@%d' % f)
ad.action = None; PL.reset(arm)
if '--where' in a:
    for tag, setp in (('Idle', lambda: PL.reset(arm)), ('Walk@33', None)):
        PL.reset(arm)
        if tag != 'Idle': ad = arm.animation_data or arm.animation_data_create(); ad.action = walk; ad.action_slot = walk.slots[0]; S.frame_set(33)
        bpy.context.view_layer.update(); P = pts(); bvh = BVHTree.FromPolygons(P, tris); out = []
        for v in tv:
            loc, nor, idx, dist = bvh.find_nearest(P[v], 0.08)
            if loc is not None and (P[v] - loc).dot(nor) < -0.005:
                mt = sorted({mats[p.material_index] for p in me.polygons if v in p.vertices})
                out.append((v, round((P[v] - loc).dot(nor) * 1000, 1), tuple(round(c, 2) for c in P[v]), mt))
        print('LSW', tag, len(out)); [print('LSW', o) for o in sorted(out, key=lambda t: t[1])[:12]]
