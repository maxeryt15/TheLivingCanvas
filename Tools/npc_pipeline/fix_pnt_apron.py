"""Painter: el delantal (Pnt_ApronCloth/Trim/Band) se hunde 10-18 mm en la falda del vestido (Pnt_clothes_Paint) al caminar/sentarse porque sus pesos difieren de los de la falda.
Correccion (solo pesos): para vertices del delantal con z < ZMAX en reposo y a < NEAR de la falda, pesos = pesos interpolados (baricentricos) del triangulo de falda mas cercano, top 4 normalizados,
mezclados con los originales con t = 1 para d <= D0 y bajando linealmente a 0 en NEAR. Posiciones sin cambio.
Uso: blender -b NPCs_Shell_Face_CAFE_WORK.blend --python fix_caf_apron.py -- [--zmax 1.0 --d0 0.012 --near 0.03 --save]  Registra reports/fix_apron.json"""
import bpy, sys, json, collections
sys.path.insert(0, r'D:\TheLivingCanvas\Tools\npc_pipeline')
import pose_lib as PL
from mathutils.bvhtree import BVHTree
from mathutils.interpolate import poly_3d_calc
a = sys.argv[sys.argv.index('--') + 1:]
def opt(k, d): return float(a[a.index(k) + 1]) if k in a else d
ZMAX = opt('--zmax', 1.0); D0 = opt('--d0', 0.012); NEAR = opt('--near', 0.03)
ob = bpy.data.objects['Pnt_Mesh']; arm = bpy.data.objects['Pnt_Rig']; me = ob.data
assert not ob.get('tlc_apron_reweight'), 'ya aplicado'
PL.reset(arm); bpy.context.view_layer.update()
rest = [v.co.copy() for v in me.vertices]
mats = [m.name if m else None for m in me.materials]
CL = [p for p in me.polygons if mats[p.material_index] == 'Pnt_clothes_Paint' and sum(rest[v].z for v in p.vertices) / len(p.vertices) > 0.4]
tl = []
for p in CL:
    vs = list(p.vertices)
    for k in range(1, len(vs) - 1): tl.append((vs[0], vs[k], vs[k + 1]))
bvh = BVHTree.FromPolygons(rest, tl)
AP = ('Pnt_ApronCloth', 'Pnt_ApronTrim', 'Pnt_ApronBand')
sel = sorted({v for p in me.polygons if mats[p.material_index] in AP for v in p.vertices if rest[v].z < ZMAX})
rec = {}
for i in sel:
    loc, nor, idx, dist = bvh.find_nearest(rest[i], NEAR)
    if loc is None: continue
    t = 1.0 if dist <= D0 else max(0.0, 1.0 - (dist - D0) / (NEAR - D0))
    tr = tl[idx]; ws = poly_3d_calc([rest[k] for k in tr], loc); tgt = collections.Counter()
    for w, k in zip(ws, tr):
        for g in me.vertices[k].groups: tgt[ob.vertex_groups[g.group].name] += w * g.weight
    cur = {ob.vertex_groups[g.group].name: g.weight for g in me.vertices[i].groups}
    new = collections.Counter()
    for b, w in cur.items(): new[b] += (1 - t) * w
    for b, w in tgt.items(): new[b] += t * w
    top = sorted(new.items(), key=lambda kv: -kv[1])[:4]; s = sum(v for _, v in top)
    for g in list(me.vertices[i].groups): ob.vertex_groups[g.group].remove([i])
    for b, v in top:
        if v / s > 0.01: ob.vertex_groups[b].add([i], v / s, 'REPLACE')
    rec[i] = {'t': round(t, 3), 'd_mm': round(dist * 1000, 1), 'old': {k: round(v, 3) for k, v in cur.items()}}
ob['tlc_apron_reweight'] = 'zmax%.2f d0%.3f near%.3f' % (ZMAX, D0, NEAR)
me.update(); bpy.context.view_layer.update()
print('FIX apron verts', len(rec), 'of', len(sel))
json.dump(rec, open(r'D:\TheLivingCanvas\ArtSource\_Exports\NPC_Validation\Painter\reports\fix_apron.json', 'w'))
if '--save' in a:
    bpy.ops.wm.save_mainfile(); print('SAVED')
