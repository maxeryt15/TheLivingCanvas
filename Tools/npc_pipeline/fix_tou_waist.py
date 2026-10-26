"""Tourist: junta camiseta/short en la cintura. La piel bajo la ropa no existe en la espalda (z 0.79-1.17) y el dobladillo de la camiseta (z~0.98) topa con el borde del
short (z~0.986) sin solape: queda una rendija por la que se ve a traves del cuerpo (ya en reposo desde atras, y abierta en BendForward).
Correccion (solo posiciones, en todas las shape keys por igual): los vertices del anillo inferior de la camiseta (z < ZH sobre la isla superior) bajan DROP y se empujan a lo
largo de la normal del short hasta quedar >= OUT por fuera. Pesos sin cambio.
Uso: blender -b WORK.blend --python fix_tou_waist.py -- [--drop 0.02 --out 0.004 --zh 0.995 --save]"""
import bpy, bmesh, sys, json, collections
from mathutils.bvhtree import BVHTree
a = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else []
def opt(k, d): return float(a[a.index(k) + 1]) if k in a else d
WMIX = opt('--wmix', 0.0); DROP = opt('--drop', 0.02); OUT = opt('--out', 0.004); ZH = opt('--zh', 0.995)
ob = bpy.data.objects['Tou_Mesh']; me = ob.data; mats = [m.name for m in me.materials]; assert not ob.get('tlc_waist_fix'), 'ya aplicado'
rest = [v.co.copy() for v in me.vertices]
cl = [p for p in me.polygons if mats[p.material_index] == 'Tou_clothes_Paint']
par = {}
def fd(x):
    while par[x] != x: par[x] = par[par[x]]; x = par[x]
    return x
for p in cl:
    for v in p.vertices: par.setdefault(v, v)
for p in cl:
    vs = list(p.vertices)
    for v in vs[1:]: par[fd(v)] = fd(vs[0])
isl = collections.defaultdict(list)
for v in par: isl[fd(v)].append(v)
up = max(isl.values(), key=lambda c: sum(rest[v].z for v in c) / len(c)); lo = max((c for c in isl.values() if c is not up), key=len); upset = set(up); loset = set(lo)
tl = []
for p in cl:
    if set(p.vertices) <= loset:
        vs = list(p.vertices)
        for k in range(1, len(vs) - 1): tl.append((vs[0], vs[k], vs[k + 1]))
bvh = BVHTree.FromPolygons(rest, tl)
bm = bmesh.new(); bm.from_mesh(me); bm.verts.ensure_lookup_table()
hem = sorted({v.index for e in bm.edges if e.is_boundary for v in e.verts if v.index in upset and rest[v.index].z < 1.05})   # lazo inferior abierto de la camiseta
nb = sorted({o.index for i in hem for e in bm.verts[i].link_edges for o in [e.other_vert(bm.verts[i])] if o.index in upset and o.index not in set(hem) and rest[o.index].z < 1.10})
bm.free(); W = {i: 1.0 for i in hem}; W.update({i: 0.5 for i in nb}); ring = sorted(W)
shape = me.shape_keys.key_blocks if me.shape_keys else []
rec = {}
for i in ring:
    from mathutils import Vector
    w = W[i]; q = rest[i] + Vector((0, 0, -DROP * w))
    loc, nor, idx, dist = bvh.find_nearest(q, 0.05); d = (q - loc).dot(nor) if loc else None
    delta = Vector((0, 0, -DROP * w))
    if loc is not None and d < OUT * w: delta = delta + nor * (OUT * w - d)
    for kb in shape: kb.data[i].co = kb.data[i].co + delta
    me.vertices[i].co = me.vertices[i].co + delta; rec[i] = [round(x * 1000, 1) for x in delta]
if WMIX > 0:   # pesos del anillo = mezcla con los pesos del vertice mas cercano del borde del short (la camiseta acompana al short en la cintura)
    from mathutils.kdtree import KDTree
    top = [v for v in lo if rest[v].z > 0.94]; kd = KDTree(len(top)); [kd.insert(rest[v], k) for k, v in enumerate(top)]; kd.balance()
    for i in hem:
        j = top[kd.find(rest[i])[1]]; cur = collections.Counter({ob.vertex_groups[g.group].name: g.weight * (1 - WMIX) for g in me.vertices[i].groups})
        for g in me.vertices[j].groups: cur[ob.vertex_groups[g.group].name] += g.weight * WMIX
        t4 = sorted(cur.items(), key=lambda kv: -kv[1])[:4]; sm = sum(x for _, x in t4)
        for g in list(me.vertices[i].groups): ob.vertex_groups[g.group].remove([i])
        for n, x in t4: ob.vertex_groups[n].add([i], x / sm, 'REPLACE')
ob['tlc_waist_fix'] = 'drop%.3f out%.3f wmix%.2f' % (DROP, OUT, WMIX); me.update(); print('WAISTFIX moved', len(ring))
json.dump(rec, open(r'D:\TheLivingCanvas\ArtSource\_Exports\NPC_Validation\Tourist\reports\fix_waist.json', 'w'))
if '--save' in a: bpy.ops.wm.save_mainfile(); print('SAVED')
