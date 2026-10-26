"""Courier: bolsa, herramientas y guante colgados del cinturon estan 100 % en pelvis; al levantar/sentar el muslo lo atraviesan (hasta 78 mm medidos con layer_scan).
Correccion (solo pesos, por isla rigida): cada isla conexa de Cou_PouchLeather/ToolSteel/ToolGrip/GloveLeather/GloveCuff mezcla sus pesos con thigh_l/thigh_r (segun signo de x del centroide)
con t = clip((ZTOP - zc) / SPAN, 0, TMAX) (zc = z minima... del centroide de la isla). Todos los vertices de la isla reciben los MISMOS pesos => la pieza se mueve rigida.
Uso: blender -b NPCs_Shell_Face_COURIER_WORK.blend --python fix_cou_props.py -- [--ztop 0.92 --span 0.22 --tmax 0.9 --save]  Marca tlc_props_reweight. Registra reports/fix_props.json"""
import bpy, sys, json, collections
sys.path.insert(0, r'D:\TheLivingCanvas\Tools\npc_pipeline')
import pose_lib as PL
a = sys.argv[sys.argv.index('--') + 1:]
def opt(k, d): return float(a[a.index(k) + 1]) if k in a else d
ZTOP = opt('--ztop', 0.92); SPAN = opt('--span', 0.22); TMAX = opt('--tmax', 0.9)
ob = bpy.data.objects['Cou_Mesh']; arm = bpy.data.objects['Cou_Rig']; me = ob.data
assert not ob.get('tlc_props_reweight'), 'ya aplicado'
PL.reset(arm); bpy.context.view_layer.update()
mn = [m.name if m else None for m in me.materials]
PARTS = ('Cou_PouchLeather', 'Cou_ToolSteel', 'Cou_ToolGrip', 'Cou_GloveLeather', 'Cou_GloveCuff')
vg = {g.name: g.index for g in ob.vertex_groups}
# --- etapa 1: cinturon (Cou_BeltLeather/BeltMetal) con pesos del triangulo de ropa mas cercano (en reposo) -> sigue a la cintura/cadera como la ropa, no a spine_03.
from mathutils.bvhtree import BVHTree
from mathutils.interpolate import poly_3d_calc
rest = [v.co.copy() for v in me.vertices]
CLP = [p for p in me.polygons if mn[p.material_index] == 'Cou_clothes_Paint' and sum(rest[v].z for v in p.vertices) / len(p.vertices) > 0.4]
tl = []
for p in CLP:
    vs_ = list(p.vertices)
    for k in range(1, len(vs_) - 1): tl.append((vs_[0], vs_[k], vs_[k + 1]))
bvh = BVHTree.FromPolygons(rest, tl)
bvs = sorted({v for p in me.polygons if mn[p.material_index] in ('Cou_BeltLeather', 'Cou_BeltMetal') for v in p.vertices})
nb = 0
for v in bvs:
    loc, nor, idx, dist = bvh.find_nearest(rest[v], 0.05)
    if loc is None: continue
    t_ = tl[idx]; ws = poly_3d_calc([rest[k] for k in t_], loc); acc = collections.Counter()
    for w, k in zip(ws, t_):
        for g in me.vertices[k].groups: acc[ob.vertex_groups[g.group].name] += w * g.weight
    top = sorted(acc.items(), key=lambda kv: -kv[1])[:4]; s_ = sum(x for _, x in top)
    for g in list(me.vertices[v].groups): ob.vertex_groups[g.group].remove([v])
    for b, x in top: ob.vertex_groups[vg[b]].add([v], x / s_, 'REPLACE')
    nb += 1
print('BELT reweighted', nb, 'of', len(bvs))

par = {}
def find(x):
    while par[x] != x: par[x] = par[par[x]]; x = par[x]
    return x
for p in me.polygons:
    if mn[p.material_index] in PARTS:
        vs = list(p.vertices)
        for v in vs: par.setdefault(v, v)
        for v in vs[1:]: par[find(v)] = find(vs[0])
isl = collections.defaultdict(list)
for v in par: isl[find(v)].append(v)
rec = []
for r, vs in isl.items():
    cz = sum(me.vertices[v].co.z for v in vs) / len(vs); cx = sum(me.vertices[v].co.x for v in vs) / len(vs)
    t = min(TMAX, max(0.0, (ZTOP - cz) / SPAN))
    if t <= 0.01: continue
    th = 'thigh_l' if cx > 0 else 'thigh_r'
    for v in vs:
        cur = {ob.vertex_groups[g.group].name: g.weight for g in me.vertices[v].groups}
        new = collections.Counter()
        for b, w in cur.items(): new[b] += (1 - t) * w
        new[th] += t
        top = sorted(new.items(), key=lambda kv: -kv[1])[:4]; s = sum(x for _, x in top)
        for g in list(me.vertices[v].groups): ob.vertex_groups[g.group].remove([v])
        for b, x in top: ob.vertex_groups[vg[b]].add([v], x / s, 'REPLACE')
    rec.append({'verts': len(vs), 'cz': round(cz, 3), 'cx': round(cx, 3), 't': round(t, 2), 'bone': th})
me.update(); ob['tlc_props_reweight'] = 'ztop%.2f span%.2f tmax%.2f' % (ZTOP, SPAN, TMAX)
print('PROPS islands', len(isl), 'changed', len(rec), rec[:8])
json.dump(rec, open(r'D:/TheLivingCanvas/ArtSource/_Exports/NPC_Validation/Courier/reports/fix_props.json', 'w'), indent=1)
if '--save' in a: bpy.ops.wm.save_mainfile(); print('SAVED')
