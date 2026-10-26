"""Student: el anillo de dobladillo de la camiseta (v4630-4655) queda 22-35 mm DENTRO del pantalon por detras y a los lados (verificado: layer_clip_scan V1 en reposo
+ renders). Correccion minima: mueve SOLO esos vertices a lo largo de la normal del pantalon hasta quedar OUT por fuera (en todas las shape keys por igual).
Uso: blender -b NPCs_Shell_Face_STUDENT_WORK.blend --python fix_stu_hem.py -- [--weights] [--save]   (sin --save no guarda: experimento en memoria)
--weights: ademas copia los pesos del triangulo de pantalon mas cercano (top 4 normalizados) a esos vertices. Registra el cambio en ArtSource/_Exports/NPC_Validation/Student/reports/fix_hem.json"""
import bpy, sys, json, collections, bmesh
sys.path.insert(0, r'D:\TheLivingCanvas\Tools\npc_pipeline')
import pose_lib as PL, layer_clip_scan as LC
from mathutils.bvhtree import BVHTree
from mathutils.interpolate import poly_3d_calc
a = sys.argv[sys.argv.index('--') + 1:]
OUT = 0.003; THRESH = 0.015
OUTDIR = r'D:/TheLivingCanvas/ArtSource/_Exports/NPC_Validation/Student/reports'
ob, me, U, L, fu, fl = LC.setup('Stu'); arm = bpy.data.objects['Stu_Rig']
PL.reset(arm)
rest = [v.co.copy() for v in me.vertices]
tl = []
for p in fl:
    vs = list(p.vertices)
    for k in range(1, len(vs) - 1): tl.append((vs[0], vs[k], vs[k + 1]))
bvh = BVHTree.FromPolygons(rest, tl)
zU = min(rest[i].z for i in U); zL = max(rest[i].z for i in L)
P, v1, v2 = LC.measure(ob, me, U, L, fu, fl, zU - 0.02, zL + 0.05)
sel = sorted(i for i, d in v1.items() if d < -THRESH)
assert sel and all(4630 <= i <= 4655 for i in sel), sel
if '--nofix' in a: sel = []
rec = {'verts': {}, 'out_mm': OUT * 1000, 'thresh_mm': THRESH * 1000}
shape = me.shape_keys.key_blocks if me.shape_keys else []
for i in sel:
    loc, nor, idx, dist = bvh.find_nearest(rest[i]); d = (rest[i] - loc).dot(nor)
    delta = nor * (-d + OUT)
    old_w = {ob.vertex_groups[g.group].name: round(g.weight, 3) for g in me.vertices[i].groups}
    for kb in shape: kb.data[i].co = kb.data[i].co + delta
    me.vertices[i].co = me.vertices[i].co + delta
    rec['verts'][i] = {'moved_mm': round(delta.length * 1000, 1), 'old_weights': old_w}
    if '--weights' in a:
        t = tl[idx]; ws = poly_3d_calc([rest[k] for k in t], loc); acc = collections.Counter()
        for w, k in zip(ws, t):
            for g in me.vertices[k].groups: acc[g.group] += w * g.weight
        top = sorted(acc.items(), key=lambda kv: -kv[1])[:4]; s = sum(x for _, x in top)
        for g in list(me.vertices[i].groups): ob.vertex_groups[g.group].remove([i])
        for gi, x in top: ob.vertex_groups[gi].add([i], x / s, 'REPLACE')
        rec['verts'][i]['new_weights'] = {ob.vertex_groups[gi].name: round(x / s, 3) for gi, x in top}
me.update(); bpy.context.view_layer.update()
P2, a2, b2 = LC.measure(ob, me, U, L, fu, fl, zU - 0.02, zL + 0.05)
print('FIX moved', len(sel), 'rest V1 before', len([1 for d in v1.values() if d < -0.002]), 'after', len([1 for d in a2.values() if d < -0.002]), 'V2 before', len([1 for d in v2.values() if d > 0.002]), 'after', len([1 for d in b2.values() if d > 0.002]),
      'worstV1 after mm', round(-min(a2.values()) * 1000, 1), 'worstV2 after mm', round(max(b2.values()) * 1000, 1))
INSET = float(a[a.index('--inset') + 1]) / 1000 if '--inset' in a else 0
if INSET:   # pantalon: vertices de la banda de solape con la camiseta (z > hem) se hunden INSET a lo largo de su normal (solo se ven bajo la camiseta)
    from mathutils import Vector
    from mathutils.kdtree import KDTree
    bm_ = bmesh.new(); bm_.from_mesh(me); bm_.verts.ensure_lookup_table()
    ring = sorted({v.index for e in bm_.edges if e.is_boundary and all(x.index in set(U) for x in e.verts) and max(x.co.z for x in e.verts) < 1.05 for v in e.verts}); bm_.free()
    kd = KDTree(len(ring)); [kd.insert(Vector((rest[i].x, rest[i].y, 0)), k) for k, i in enumerate(ring)]; kd.balance()
    ids = [i for i in L if rest[i].z > rest[ring[kd.find(Vector((rest[i].x, rest[i].y, 0)))[1]]].z + 0.015]   # solo vertices del pantalon bajo la camiseta (por encima del dobladillo local)
    nrm = {}
    for i in ids:
        loc, n, idx, dist = bvh.find_nearest(rest[i]); nrm[i] = n.copy()
    bm_n = {}
    for i in ids:
        d = nrm[i] * -INSET
        for kb in shape: kb.data[i].co = kb.data[i].co + d
        me.vertices[i].co = me.vertices[i].co + d
    me.update(); bpy.context.view_layer.update(); rec['inset_pants'] = {'n': len(ids), 'mm': INSET * 1000}
if '--metric' in a:
    walk = next(x for x in bpy.data.actions if x.name.startswith('U_') and '_Student_Walk' in x.name); cal = PL.calibrate(arm); S = bpy.context.scene
    def one(tag):
        P_, q1, q2 = LC.measure(ob, me, U, L, fu, fl, zU - 0.02, zL + 0.05)
        n1 = [d for d in q1.values() if d < -0.002]; n2 = [d for d in q2.values() if d > 0.002]
        print('MET %-14s shirt-in-pants n=%3d worst %5.1fmm | pants-out-of-shirt n=%3d worst %5.1fmm' % (tag, len(n1), -min(n1, default=0) * 1000, len(n2), max(n2, default=0) * 1000))
    PL.reset(arm); one('Idle')
    for nm in ('Sit', 'Crouch', 'BendForward', 'Twist_A', 'ArmsUp_R', 'LegKick_L', 'KneeBend_R'):
        PL.reset(arm); PL.apply(arm, cal[nm]); one(nm)
    PL.reset(arm); ad = arm.animation_data or arm.animation_data_create(); ad.action = walk; ad.action_slot = walk.slots[0]
    for f in (1, 9, 17, 25, 33): S.frame_set(f); bpy.context.view_layer.update(); one('Walk@%d' % f)
    ad.action = None; PL.reset(arm)
if '--scan' in a:
    import os; d = OUTDIR + '/scan_' + ('geom_w' if '--weights' in a else 'geom'); os.makedirs(d, exist_ok=True)
    LC.PS.OUT = d; LC.run('Stu')
rec['inset_ids'] = ids if INSET else []
json.dump(rec, open(r'D:\TheLivingCanvas\ArtSource\_Exports\NPC_Validation\Student\reports\fix_hem%s.json' % ('_w' if '--weights' in a else ''), 'w'), indent=1)
if '--save' in a:
    bpy.ops.wm.save_mainfile(); print('SAVED')
