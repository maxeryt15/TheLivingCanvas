"""Cafe: cierra el vestido por abajo. Tapa el anillo de dobladillo de la falda (borde abierto de Caf_clothes_Paint, 47 verts, z~0.49) con un disco de 2 anillos + centro,
mismo material (Caf_clothes_Paint). Pesos: anillo exterior = los del dobladillo; anillo interior y centro = mezcla con el promedio. UV/color: copiados del dobladillo (promedio en el centro).
Marca tlc_hemcap. Uso: blender -b NPCs_Shell_Face_CAFE_WORK.blend --python add_caf_hemcap.py -- [--save]   Registra reports/fix_hemcap.json"""
import bpy, sys, json, collections, bmesh
sys.path.insert(0, r'D:\TheLivingCanvas\Tools\npc_pipeline')
import pose_lib as PL
from mathutils import Vector
a = sys.argv[sys.argv.index('--') + 1:]
ob = bpy.data.objects['Caf_Mesh']; arm = bpy.data.objects['Caf_Rig']; me = ob.data
assert not ob.get('tlc_hemcap'), 'ya aplicado'
PL.reset(arm); bpy.context.view_layer.update()
mats = [m.name if m else None for m in me.materials]; ci = mats.index('Caf_clothes_Paint')
bm = bmesh.new(); bm.from_mesh(me); bm.verts.ensure_lookup_table(); bm.edges.ensure_lookup_table()
dl = bm.verts.layers.deform.verify(); sk = list(bm.verts.layers.shape.values()); uvl = list(bm.loops.layers.uv.values())
col = list(bm.loops.layers.float_color.values()) + list(bm.loops.layers.color.values())
cl = {f for f in bm.faces if f.material_index == ci}
be = [e for e in bm.edges if sum(1 for f in e.link_faces if f in cl) == 1 and all(0.47 < v.co.z < 0.52 for v in e.verts)]
assert len(be) == 47, len(be)
adj = collections.defaultdict(list)
for e in be:
    for v in e.verts: adj[v].append(e)
# --- pliegue en L al sentarse: la falda y el delantal por delante (y<0) bajo z=0.80 siguen a los muslos (mitad izq/der por x); atras sigue la pelvis.
TLg = next(g.index for g in ob.vertex_groups if g.name.lower() == 'thigh_l'); TRg = next(g.index for g in ob.vertex_groups if g.name.lower() == 'thigh_r')
SK = {'Caf_clothes_Paint', 'Caf_ApronCloth', 'Caf_ApronTrim', 'Caf_ApronBand'}
skv = {v for f in bm.faces if mats[f.material_index] in SK for v in f.verts if 0.45 < v.co.z < 1.0 and abs(v.co.x) < 0.30}
nre = 0
for v in skv:
    f_ = min(1.0, max(0.0, (-v.co.y + 0.02) / 0.08)); h_ = min(1.0, max(0.0, (0.95 - v.co.z) / 0.25)); al = f_ * h_
    if al <= 0: continue
    t_ = min(1.0, max(0.0, 0.5 + v.co.x / 0.04)); c_ = collections.Counter()
    for g_, x_ in v[dl].items(): c_[g_] += (1 - al) * x_
    c_[TLg] += al * t_; c_[TRg] += al * (1 - t_)
    top_ = sorted(c_.items(), key=lambda kv: -kv[1])[:4]; ss = sum(x_ for _, x_ in top_)
    v[dl].clear()
    for g_, x_ in top_: v[dl][g_] = x_ / ss
    nre += 1
print('REWEIGHT', nre)
start = be[0].verts[0]; order = [start]; prev = None; cur = start
while True:
    nxt = None
    for e in adj[cur]:
        o = e.other_vert(cur)
        if o is not prev and o not in order: nxt = o; break
    if nxt is None: break
    order.append(nxt); prev, cur = cur, nxt
assert len(order) == 47, len(order)
# datos de loop (uv/col) de la cara de ropa adyacente a cada vertice del borde
def loopdata(v):
    f = next(f for f in v.link_faces if f in cl); lp = next(l for l in f.loops if l.vert == v)
    return [tuple(lp[l].uv) for l in uvl], [tuple(lp[l]) for l in col]
LD = [loopdata(v) for v in order]
cen = sum((v.co for v in order), Vector()) / len(order)
def wdict(v): return {g: w for g, w in v[dl].items()}
W = [wdict(v) for v in order]
avg = collections.Counter()
for w in W:
    for g, x in w.items(): avg[g] += x / len(W)
TL_ = next(g.index for g in ob.vertex_groups if g.name.lower() == 'thigh_l'); TR_ = next(g.index for g in ob.vertex_groups if g.name.lower() == 'thigh_r')
def side_w(x):   # reparto lateral: el disco descansa sobre los muslos (x>0 = thigh_l); franja de mezcla estrecha en el centro => pliegue recto entre muslos
    t = min(1.0, max(0.0, 0.5 + x / 0.04)); return {TL_: t, TR_: 1 - t}
def mix(w, t, x):
    c = collections.Counter()
    for g, v in w.items(): c[g] += (1 - t) * v
    for g, v in side_w(x).items(): c[g] += t * v
    top = sorted(c.items(), key=lambda kv: -kv[1])[:4]; s = sum(v for _, v in top if v > 1e-6); return {g: v / s for g, v in top if v > 1e-6}
def newv(co, w):
    v = bm.verts.new(co)
    for l in sk: v[l] = co.copy()
    for g, x in w.items(): v[dl][g] = x
    return v
SC = (0.75, 0.5, 0.25)   # radios relativos de los anillos interiores (suaviza el pliegue al sentarse)
rings = [order] + [[newv(cen + (v.co - cen) * k, mix(W[i], min(1.0, (1 - k) * 1.6), (cen + (v.co - cen) * k).x)) for i, v in enumerate(order)] for k in SC]
center = newv(cen, mix({}, 1.0, 0.0))
N = len(order); new = []
def setloop(f, lps):
    for lp, (uv, cc) in zip(f.loops, lps):
        for l, u in zip(uvl, uv): lp[l].uv = u
        for l, c in zip(col, cc): lp[l] = c
def mid(a, b, t): return ([tuple(x[j] * (1 - t) + y[j] * t for j in range(2)) for x, y in zip(a[0], b[0])], [tuple(p * (1 - t) + q * t for p, q in zip(x, y)) for x, y in zip(a[1], b[1])])
cd = ([tuple(sum(x[0][k][j] for x in LD) / N for j in range(2)) for k in range(len(uvl))], [tuple(sum(x[1][k][j] for x in LD) / N for j in range(4)) for k in range(len(col))])
ID = [[LD[i] for i in range(N)]] + [[mid(LD[i], cd, 1 - k) for i in range(N)] for k in SC]
for r in range(len(rings) - 1):
    for i in range(N):
        j = (i + 1) % N
        f = bm.faces.new((rings[r][i], rings[r][j], rings[r + 1][j], rings[r + 1][i])); f.material_index = ci; f.smooth = True; setloop(f, [ID[r][i], ID[r][j], ID[r + 1][j], ID[r + 1][i]]); new.append(f)
for i in range(N):
    j = (i + 1) % N
    g = bm.faces.new((rings[-1][i], rings[-1][j], center)); g.material_index = ci; g.smooth = True; setloop(g, [ID[-1][i], ID[-1][j], cd]); new.append(g)
bm.normal_update()
down = sum(1 for f in new if f.normal.z < 0)
if down < len(new) / 2:
    for f in new: f.normal_flip()
bm.to_mesh(me); bm.free(); me.update(); ob['tlc_hemcap'] = 'hem z~0.49 47v'
rec = {'faces': len(new), 'flipped': down < len(new) / 2}
json.dump(rec, open(r'D:/TheLivingCanvas/ArtSource/_Exports/NPC_Validation/Cafe/reports/fix_hemcap.json', 'w'), indent=1); print('HEMCAP', rec)
if '--save' in a: bpy.ops.wm.save_mainfile(); print('SAVED')
