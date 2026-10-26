"""Comprueba que el torso interior (add_torso_backing.py) no asoma por la ropa. SOLO LECTURA salvo que se use --apply-first.
Aplica el torso en memoria (sin guardar), y en reposo + frames de Walk mide, para cada vertice nuevo, la distancia con signo al vertice de ropa mas cercano
(a lo largo de su normal; negativo = dentro). Correctivos silenciados (como en Unity). Salida: CHK <pref> maxout_mm, n_outside (>-2 mm), por pose.
Uso: blender -b WORK.blend --python backing_check.py -- Pref [--frames 1,8,16,24,32] [--args ...pasados a add_torso_backing]"""
import bpy, sys, os, runpy
sys.path.insert(0, r'D:\TheLivingCanvas\Tools\npc_pipeline')
import pose_lib as PL
from mathutils.kdtree import KDTree
a = sys.argv[sys.argv.index('--') + 1:]; pref = a[0]
frames = [int(x) for x in a[a.index('--frames') + 1].split(',')] if '--frames' in a else [1, 8, 16, 24, 32]
extra = a[a.index('--args') + 1:] if '--args' in a else []
O = bpy.data.objects; ob = O[pref + '_Mesh']; arm = O[pref + '_Rig']; S = bpy.context.scene
n0 = len(ob.data.vertices)
sys.argv = ['x', '--', pref] + extra; runpy.run_path(r'D:\TheLivingCanvas\Tools\npc_pipeline\add_torso_backing.py')
new = list(range(n0, len(ob.data.vertices)))
mats = [m.name.lower() if m else '' for m in ob.data.materials]
GARM = ('cloth', 'suit', 'apron', 'dress', 'shirt', 'blouse', 'jacket')
cl = sorted({v for p in ob.data.polygons[:len(ob.data.polygons)] if any(g in mats[p.material_index] for g in GARM) and min(p.vertices) < n0 for v in p.vertices if v < n0})
for k in ob.data.shape_keys.key_blocks:
    if k.name.startswith('Corrective_'): k.mute = True
name = {'Stu': 'Student', 'Grd': 'Guard', 'Gen': 'Gentleman', 'Cur': 'Curator', 'Gar': 'Gardener', 'Caf': 'Cafe', 'Tou': 'Tourist', 'Cou': 'Courier', 'Doc': 'Docent', 'Pnt': 'Painter', 'Rose': 'Rose'}.get(pref, pref)
walk = next((x for x in bpy.data.actions if x.name.startswith('U_') and f'_{name}_Walk' in x.name), None)
worst = 9
for fr in [0] + frames:
    PL.reset(arm)
    if fr and walk:
        ad = arm.animation_data or arm.animation_data_create(); ad.action = walk; ad.action_slot = walk.slots[0]; S.frame_set(fr)
    bpy.context.view_layer.update()
    ev = ob.evaluated_get(bpy.context.evaluated_depsgraph_get()); m = ev.to_mesh(); m.calc_normals_split() if hasattr(m, 'calc_normals_split') else None
    from mathutils.bvhtree import BVHTree
    from mathutils import Vector
    m.calc_loop_triangles(); tris = [t for t in m.loop_triangles if any(g in mats[m.polygons[t.polygon_index].material_index] for g in GARM)]
    bvh = BVHTree.FromPolygons([v.co.copy() for v in m.vertices], [tuple(t.vertices) for t in tris])
    cen = {}
    for v in new: cen.setdefault(round(m.vertices[v].co.z, 2), []).append(m.vertices[v].co)
    mx = 9.0; nout = 0; ntouch = 0
    for v in new:
        co = m.vertices[v].co; zc = cen[round(co.z, 2)]; c = sum(zc, Vector()) / len(zc)
        d = Vector((co.x - c.x, co.y - c.y, 0)); d = d.normalized() if d.length > 1e-4 else Vector((0, -1, 0))
        hit = bvh.ray_cast(co, d, 1.0)
        if hit[0] is None:
            nout += 1
            if fr == 0: print('  ESC z', round(co.z, 3))
            continue
        mx = min(mx, hit[3]); ntouch += hit[3] < 0.002

    ev.to_mesh_clear(); worst = min(worst, mx)
    print('CHK', pref, 'fr', fr, 'min_margin_mm', round(mx * 1000, 1), 'escape', nout, 'touch<2mm', ntouch)
print('CHKTOTAL', pref, 'worst_margin_mm', round(worst * 1000, 1))
