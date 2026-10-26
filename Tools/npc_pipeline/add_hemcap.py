"""Generico (Cafe, Curator, ...; version de add_caf_hemcap.py): cierra la falda/vestido por abajo. Tapa el anillo de dobladillo de la falda (borde abierto de Caf_clothes_Paint, 47 verts, z~0.49) con un disco de 2 anillos + centro,
mismo material (Caf_clothes_Paint). Pesos: anillo exterior = los del dobladillo; anillo interior y centro = mezcla con el promedio. UV/color: copiados del dobladillo (promedio en el centro).
Marca tlc_hemcap. Uso: blender -b NPCs_Shell_Face_<X>_WORK.blend --python add_hemcap.py -- Cur [--save]   Registra reports/fix_hemcap.json"""
import bpy, sys, json, collections, bmesh
sys.path.insert(0, r'D:\TheLivingCanvas\Tools\npc_pipeline')
import pose_lib as PL
from mathutils import Vector
a = sys.argv[sys.argv.index('--') + 1:]
PREF = a[0]
CAFE = '--cafe' in a   # mismo metodo que Cafe (aprobado): reparto lateral a los muslos, ancho 0.04, disco en abanico
BW = float(a[a.index('--bw') + 1]) if '--bw' in a else (0.04 if CAFE else 0.10)
ob = bpy.data.objects[PREF + '_Mesh']; arm = bpy.data.objects[PREF + '_Rig']; me = ob.data
assert not ob.get('tlc_hemcap'), 'ya aplicado'
PL.reset(arm); bpy.context.view_layer.update()
mats = [m.name if m else None for m in me.materials]; ci = mats.index(PREF + '_clothes_Paint')
bm = bmesh.new(); bm.from_mesh(me); bm.verts.ensure_lookup_table(); bm.edges.ensure_lookup_table()
dl = bm.verts.layers.deform.verify(); sk = list(bm.verts.layers.shape.values()); uvl = list(bm.loops.layers.uv.values())
col = list(bm.loops.layers.float_color.values()) + list(bm.loops.layers.color.values())
cl = {f for f in bm.faces if f.material_index == ci}
bes = [e for e in bm.edges if sum(1 for f in e.link_faces if f in cl) == 1 and all(0.3 < v.co.z < 0.8 for v in e.verts)]
nbr = collections.defaultdict(set)
for e in bes:
    nbr[e.verts[0]].add(e.verts[1]); nbr[e.verts[1]].add(e.verts[0])
seen = set(); comps = []
for v0 in nbr:
    if v0 in seen: continue
    st = [v0]; comp = set()
    while st:
        v = st.pop()
        if v in comp: continue
        comp.add(v); st.extend(nbr[v] - comp)
    seen |= comp; comps.append(comp)
comps = [c for c in comps if len(c) >= 20 and max(v.co.z for v in c) < 0.75]
assert comps, 'no hay anillo de dobladillo'
hem = min(comps, key=lambda c: sum(v.co.z for v in c) / len(c))
be = [e for e in bes if e.verts[0] in hem and e.verts[1] in hem]; NH = len(hem)
print('HEM loop', NH, 'z', round(min(v.co.z for v in hem), 3), round(max(v.co.z for v in hem), 3))
# isla de la falda (caras de ropa conectadas al anillo, sin cruzar a otras prendas distintas)
isl = set(); st = [next(iter(hem))]
while st:
    v = st.pop()
    if v in isl: continue
    isl.add(v)
    for f in v.link_faces:
        if f in cl:
            for w in f.verts:
                if w not in isl: st.append(w)
adj = collections.defaultdict(list)
for e in be:
    for v in e.verts: adj[v].append(e)
# --- pliegue en L al sentarse: la falda y el delantal por delante (y<0) bajo z=0.80 siguen a los muslos (mitad izq/der por x); atras sigue la pelvis.
TLg = next(g.index for g in ob.vertex_groups if g.name.lower() == 'thigh_l'); TRg = next(g.index for g in ob.vertex_groups if g.name.lower() == 'thigh_r')
SK = {PREF + '_ApronCloth', PREF + '_ApronTrim', PREF + '_ApronBand'}
skv = {v for v in isl if 0.3 < v.co.z < 1.0 and abs(v.co.x) < 0.30} | {v for f in bm.faces if mats[f.material_index] in SK for v in f.verts if 0.45 < v.co.z < 1.0 and abs(v.co.x) < 0.30}
nre = 0
for v in skv:
    f_ = min(1.0, max(0.0, (-v.co.y + 0.02) / 0.08)); h_ = min(1.0, max(0.0, ((0.95 - v.co.z) / 0.25 if CAFE else (0.78 - v.co.z) / 0.12))); al = f_ * h_
    if al <= 0: continue
    t_ = min(1.0, max(0.0, 0.5 + v.co.x / BW)); c_ = collections.Counter()
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
assert len(order) == NH, (len(order), NH)
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
    t = min(1.0, max(0.0, 0.5 + x / BW)); return {TL_: t, TR_: 1 - t}
def mix(w, t, x):
    c = collections.Counter()
    for g, v in w.items(): c[g] += (1 - t) * v
    for g, v in (side_w(x) if CAFE else avg).items(): c[g] += t * v   # el disco converge hacia el centroide de la deformacion del anillo (no hacia un solo muslo)
    top = sorted(c.items(), key=lambda kv: -kv[1])[:4]; s = sum(v for _, v in top if v > 1e-6); return {g: v / s for g, v in top if v > 1e-6}
def newv(co, w):
    v = bm.verts.new(co)
    for l in sk: v[l] = co.copy()
    for g, x in w.items(): v[dl][g] = x
    return v
SC = (0.75, 0.5, 0.25)   # radios relativos de los anillos interiores (suaviza el pliegue al sentarse)
rings = [order] + [[newv(cen + (v.co - cen) * k, mix(W[i], (1 - k), (cen + (v.co - cen) * k).x)) for i, v in enumerate(order)] for k in SC]
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
        f = bm.faces.new((rings[r][i], rings[r][j], rings[r + 1][j], rings[r + 1][i])); f.material_index = ci; f.smooth = CAFE; setloop(f, [ID[r][i], ID[r][j], ID[r + 1][j], ID[r + 1][i]]); new.append(f)
# centro: malla de rejilla (grid_fill) en vez de abanico triangular => sin polo donde convergen todas las lineas
if CAFE:
    center = newv(cen, mix({}, 1.0, 0.0))
    for i in range(N):
        j = (i + 1) % N
        g = bm.faces.new((rings[-1][i], rings[-1][j], center)); g.material_index = ci; g.smooth = True; setloop(g, [ID[-1][i], ID[-1][j], cd]); new.append(g)
else:
  inner = rings[-1]; ie = [bm.edges.get((inner[i], inner[(i + 1) % N])) for i in range(N)]
  assert all(ie), 'anillo interior incompleto'
  gf = bmesh.ops.triangle_fill(bm, use_beauty=True, use_dissolve=False, edges=ie)
  gf = {'faces': [e for e in gf['geom'] if isinstance(e, bmesh.types.BMFace)]}
  print('FILL faces', len(gf['faces']))
  gverts = {v for f in gf['faces'] for v in f.verts if v not in set(inner)}
  tw = collections.Counter(avg); ts = sum(tw.values())
  for v in gverts:
      for l in sk: v[l] = v.co.copy()
      v[dl].clear()
      for g_, x_ in tw.items(): v[dl][g_] = x_ / ts
  for f in gf['faces']:
      f.material_index = ci; f.smooth = False; new.append(f)
      for lp in f.loops:
          for l, u in zip(uvl, cd[0]): lp[l].uv = u
          for l, c in zip(col, cd[1]): lp[l] = c
bm.normal_update()
bmesh.ops.recalc_face_normals(bm, faces=new)   # coherentes entre si
bm.normal_update()
down = sum(1 for f in new if f.normal.z < 0)
if down < len(new) / 2:
    for f in new: f.normal_flip()
bm.to_mesh(me); bm.free(); me.update(); ob['tlc_hemcap'] = 'hem %dv' % NH + ''
rec = {'faces': len(new), 'flipped': down < len(new) / 2}
json.dump(rec, open(r'D:/TheLivingCanvas/ArtSource/_Exports/NPC_Validation/%s/reports/fix_hemcap.json' % {'Caf': 'Cafe', 'Cur': 'Curator', 'Gar': 'Gardener', 'Tou': 'Tourist', 'Pnt': 'Painter', 'Rose': 'Rose'}[PREF], 'w'), indent=1); print('HEMCAP', rec)
if '--save' in a: bpy.ops.wm.save_mainfile(); print('SAVED')
