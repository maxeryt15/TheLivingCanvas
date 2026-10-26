"""Student: reconstruye la correa del bolso (Stu_BagStrap) como UNA cinta continua y lisa en vez de 37 quads planos que se ven como bloques cuadrados.
Pasos: ordena los 38 'peldaños' (pares de vertices) de la cinta actual; ajusta una spline Catmull-Rom a cada borde; subdivide x SUB; suaviza (extremos fijos);
fuerza un minimo de separacion con la camiseta; ancho constante; pesos interpolados de los peldaños originales (top 4); shape keys = posicion (la correa no tiene deltas faciales);
caras lisas (smooth) y normales hacia fuera de la camiseta. Uso: blender -b WORK.blend --python fix_stu_strap_rebuild.py -- [--save]"""
import bpy, bmesh, sys, json, collections
from mathutils import Vector
from mathutils.bvhtree import BVHTree
from mathutils.interpolate import poly_3d_calc
SUB = 2; HALF = 0.015; CLEAR = 0.003; FIXED = 2
ob = bpy.data.objects['Stu_Mesh']; me = ob.data; mats = [m.name for m in me.materials]; vg = ob.vertex_groups
bm = bmesh.new(); bm.from_mesh(me); bm.faces.ensure_lookup_table(); bm.verts.ensure_lookup_table()
dl = bm.verts.layers.deform.active; uvl = bm.loops.layers.uv; col = bm.loops.layers.color.active if bm.loops.layers.color.active else None
cols = bm.verts.layers.color.active if bm.verts.layers.color.active else None
si = mats.index('Stu_BagStrap')
st = [f for f in bm.faces if f.material_index == si]; ss = {f.index for f in st}
adj = {f.index: [g.index for e in f.edges for g in e.link_faces if g != f and g.index in ss] for f in st}
ends = [i for i, a in adj.items() if len(a) == 1]; order = []; prev = None; cur = ends[0]
while cur is not None:
    order.append(cur); nxt = [x for x in adj[cur] if x != prev]; prev, cur = cur, (nxt[0] if nxt else None)
assert len(order) == 37
def shared(f, g): return [v for v in f.verts if v in g.verts]
rungs = []
f0 = bm.faces[order[0]]; sh = shared(f0, bm.faces[order[1]]); rungs.append([v for v in f0.verts if v not in sh])
for k in range(len(order) - 1): rungs.append(shared(bm.faces[order[k]], bm.faces[order[k + 1]]))
rungs.append([v for v in bm.faces[order[-1]].verts if v not in shared(bm.faces[order[-1]], bm.faces[order[-2]])])
assert all(len(r) == 2 for r in rungs) and len(rungs) == 38
for k in range(1, len(rungs)):
    a0, b0 = rungs[k - 1]; a, b = rungs[k]
    if (b.co - a.co).dot(b0.co - a0.co) < 0: rungs[k] = [b, a]
A = [r[0].co.copy() for r in rungs]; B = [r[1].co.copy() for r in rungs]
Wn = [[{g: w for g, w in v[dl].items()} for v in r] for r in rungs]   # pesos por peldaño (a, b)
def cr(P, s):
    i = int(s); t = s - i; n = len(P)
    p0, p1, p2, p3 = P[max(i - 1, 0)], P[i], P[min(i + 1, n - 1)], P[min(i + 2, n - 1)]
    if t == 0: return p1.copy()
    return 0.5 * ((2 * p1) + (-p0 + p2) * t + (2 * p0 - 5 * p1 + 4 * p2 - p3) * t * t + (-p0 + 3 * p1 - 3 * p2 + p3) * t ** 3)
n = len(rungs); S = [k / SUB for k in range((n - 1) * SUB + 1)]
NA = [cr(A, s) for s in S]; NB = [cr(B, s) for s in S]
def blend_w(s, side):
    i = int(s); t = s - i; w0 = Wn[i][side]; w1 = Wn[min(i + 1, n - 1)][side]; acc = collections.Counter()
    for g, w in w0.items(): acc[g] += w * (1 - t)
    for g, w in w1.items(): acc[g] += w * t
    top = sorted(acc.items(), key=lambda kv: -kv[1])[:4]; tot = sum(x for _, x in top)
    return {g: x / tot for g, x in top}
NW = [(blend_w(s, 0), blend_w(s, 1)) for s in S]
m = len(S)
# suavizado (extremos fijos) sobre centro y direccion; ancho constante
C = [(NA[k] + NB[k]) / 2 for k in range(m)]; D = [(NB[k] - NA[k]).normalized() for k in range(m)]
cl = [p for p in bm.faces if mats[p.material_index] == 'Stu_clothes_Paint']
P0 = [v.co.copy() for v in bm.verts]; tris = []
for f in cl:
    vs = [v.index for v in f.verts]
    for k in range(1, len(vs) - 1): tris.append((vs[0], vs[k], vs[k + 1]))
bvh = BVHTree.FromPolygons(P0, tris)
def smooth(arr, passes, lam):
    for _ in range(passes):
        new = [x.copy() for x in arr]
        for k in range(FIXED * SUB, m - FIXED * SUB): new[k] = arr[k] * (1 - lam) + (arr[k - 1] + arr[k + 1]) * 0.5 * lam
        arr = new
    return arr
def push(Cc):
    out = []
    for k, c in enumerate(Cc):
        if FIXED * SUB <= k < m - FIXED * SUB:
            for sgn in (0, -1, 1):
                p = c + D[k] * HALF * sgn
                loc, nor, idx, dist = bvh.find_nearest(p, 0.03)
                if loc is not None and (p - loc).dot(nor) < CLEAR: c = c + nor * (CLEAR - (p - loc).dot(nor)); 
        out.append(c)
    return out
C = smooth(C, 6, 0.5); D = [d.normalized() for d in smooth([d.copy() for d in D], 4, 0.5)]
C = push(C); C = smooth(C, 2, 0.3); C = push(C)
NA = [C[k] - D[k] * HALF for k in range(m)]; NB = [C[k] + D[k] * HALF for k in range(m)]
SW = {v.index: dict(v[dl].items()) for f in cl for v in f.verts}   # pesos de la camiseta (antes de borrar)
# borrar la correa vieja
old_faces = list(st); old_verts = {v for f in st for v in f.verts}
bmesh.ops.delete(bm, geom=old_faces, context='FACES')
bmesh.ops.delete(bm, geom=[v for v in old_verts if v.is_valid and not v.link_faces], context='VERTS')
shape = list(bm.verts.layers.shape)
def newv(p, w):
    v = bm.verts.new(p)
    for key in shape: v[key] = p.copy()
    for gi, x in w.items(): v[dl][gi] = x
    return v
SHIRTW = '--shirtw' in sys.argv
def shirt_w(p, orig):
    """pesos de la camiseta (triangulo mas cercano) mezclados con los originales: 100% camiseta a <8 mm, 100% original a >20 mm (extremos del bolso)"""
    loc, nor, idx, dist = bvh.find_nearest(p, 0.06)
    if loc is None: return orig
    t = min(max((dist - 0.008) / 0.012, 0.0), 1.0); tri = tris[idx]; ws = poly_3d_calc([P0[k] for k in tri], loc); acc = collections.Counter()
    for w, k in zip(ws, tri):
        for g, x in SW[k].items(): acc[g] += w * x * (1 - t)
    for g, x in orig.items(): acc[g] += x * t
    top = sorted(acc.items(), key=lambda kv: -kv[1])[:4]; tot = sum(x for _, x in top)
    return {g: x / tot for g, x in top}
RA = []; RB = []
for k in range(m):
    wa, wb = NW[k]
    if SHIRTW: wa = shirt_w(NA[k], wa); wb = shirt_w(NB[k], wb)
    RA.append(newv(NA[k], wa)); RB.append(newv(NB[k], wb))
nf = []
for k in range(m - 1):
    f = bm.faces.new((RA[k], RA[k + 1], RB[k + 1], RB[k])); f.material_index = si; f.smooth = True; nf.append(f)
bm.normal_update()
flip = 0
for f in nf:
    loc, nor, idx, dist = bvh.find_nearest(f.calc_center_median(), 0.08)
    if loc is not None and dist < 0.012 and f.normal.dot(nor) < 0: f.normal_flip(); flip += 1
bm.verts.index_update(); bm.faces.index_update(); bm.normal_update()
bm.to_mesh(me); bm.free(); me.update()
print('REBUILD rungs', m, 'quads', m - 1, 'flipped', flip, 'verts total', len(me.vertices))
if '--save' in sys.argv: bpy.ops.wm.save_mainfile(); print('SAVED')
