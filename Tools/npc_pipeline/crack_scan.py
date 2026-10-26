"""Busca GRIETAS (SOLO LECTURA): vertices de bordes abiertos que quedan a menos de TOL de otro vertice de borde abierto sin estar unidos (costuras milimetricas por las que se ve a traves).
Ignora ojos, boca, cejas, pestanas, labios. Uso: blender -b X.blend --python crack_scan.py -- Pref [--tol 0.006]. Salida: CRK por NPC (n pares, por material, z media) y los 8 pares mas cercanos."""
import bpy, bmesh, sys, collections
from mathutils.kdtree import KDTree
a = sys.argv[sys.argv.index('--') + 1:]; pref = a[0]; TOL = float(a[a.index('--tol') + 1]) if '--tol' in a else 0.006
ob = bpy.data.objects[pref + '_Mesh']; me = ob.data; mats = [m.name if m else '' for m in me.materials]
SKIP = ('eye', 'mouth', 'brow', 'lash', 'lip', 'lining')
bm = bmesh.new(); bm.from_mesh(me); bm.verts.ensure_lookup_table(); bm.edges.ensure_lookup_table()
GARM = ('cloth', 'suit', 'apron', 'scarf', 'hat', 'shirt', 'blouse', 'jacket', 'vest', 'dress', 'skirt')
ONLY = '--garments' in a
def ok(f):
    n = mats[f.material_index].lower()
    if any(s in n for s in SKIP): return False
    return (not ONLY) or any(g in n for g in GARM)
bv = {}
for e in bm.edges:
    fs = [f for f in e.link_faces if ok(f)]
    if len(fs) == 1:
        for v in e.verts: bv.setdefault(v.index, set()).add(mats[fs[0].material_index])
kd = KDTree(len(bv)); ids = list(bv)
for i, v in enumerate(ids): kd.insert(bm.verts[v].co, i)
kd.balance()
nb = {v: {o.index for e in bm.verts[v].link_edges for o in e.verts} for v in ids}
pairs = {}
for i, v in enumerate(ids):
    for co, j, d in kd.find_range(bm.verts[v].co, TOL):
        w = ids[j]
        if w <= v or w in nb[v]: continue
        if set(bm.verts[v].link_faces) & set(bm.verts[w].link_faces): continue
        pairs[(v, w)] = d
by = collections.Counter(); zs = []
for (v, w), d in pairs.items():
    m = sorted(bv[v] | bv[w]); by[tuple(m)] += 1; zs.append((bm.verts[v].co.z + bm.verts[w].co.z) / 2)
print('CRK', pref, 'bordes_verts', len(bv), 'pares', len(pairs), 'z', (round(min(zs), 2), round(max(zs), 2)) if zs else None)
for k, n in by.most_common(5): print('CRK  ', pref, n, k)
for (v, w), d in sorted(pairs.items(), key=lambda kv: kv[1])[:6]: print('CRK   par', v, w, 'd_mm', round(d * 1000, 2), tuple(round(x, 3) for x in bm.verts[v].co))
