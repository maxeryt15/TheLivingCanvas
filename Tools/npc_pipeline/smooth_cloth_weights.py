"""Suaviza los pesos de la prenda en zonas donde se mezclan huesos distintos (axila, hombro): evita triangulos pellizcados/estirados.
Para cada vertice de prenda cuyos pesos tocan >=2 de los huesos de BONES, hace ITER pasadas: w = (1-A)*propio + A*media de vecinos (aristas de prenda).
Max 4 influencias, normalizado. Uso: blender -b X.blend --python smooth_cloth_weights.py -- salida.blend Pref [Pref ...]
"""
import bpy, bmesh, sys
ITER, A = 4, 0.5
EQ_LEN = 0.012  # m: aristas de prenda mas cortas que esto en reposo -> sus vertices comparten pesos (media del grupo)
BONES = ('upperarm', 'clavicle', 'spine_03', 'spine_02', 'neck_01')
CK = ('clothes_paint', 'suit_', 'aproncloth', 'blouse', 'scarfcloth')


def run(pref):
    ob = bpy.data.objects[pref + '_Mesh']; me = ob.data
    names = {i: g.name for i, g in enumerate(ob.vertex_groups)}
    bm = bmesh.new(); bm.from_mesh(me); dl = bm.verts.layers.deform.verify(); bm.verts.ensure_lookup_table()
    cf = [f for f in bm.faces if any(k in (me.materials[f.material_index].name.lower() if me.materials[f.material_index] else '') for k in CK)]
    cv = {v for f in cf for v in f.verts}
    nb = {v: {o for e in v.link_edges for o in [e.other_vert(v)] if o in cv} for v in cv}
    sel = [v for v in cv if sum(1 for g in v[dl].keys() if any(b in names[g] for b in BONES)) >= 2]
    selset = set(sel)
    for _ in range(ITER):
        new = {}
        for v in sel:
            w = {g: x * (1 - A) for g, x in v[dl].items()}
            ns = list(nb[v])
            if ns:
                for o in ns:
                    for g, x in o[dl].items(): w[g] = w.get(g, 0.0) + x * A / len(ns)
            top = sorted(w.items(), key=lambda kv: -kv[1])[:4]; s = sum(x for _, x in top) or 1.0
            new[v] = [(g, x / s) for g, x in top]
        for v, ws in new.items():
            v[dl].clear()
            for g, x in ws: v[dl][g] = x
    # grupos de vertices unidos por aristas cortas: pesos medios identicos (una arista corta con pesos distintos se estira muchisimo al animar)
    par = {v: v for v in cv}
    def find(x):
        while par[x] is not x:
            par[x] = par[par[x]]; x = par[x]
        return x
    for v in cv:
        for o in nb[v]:
            if (v.co - o.co).length < EQ_LEN: par[find(v)] = find(o)
    groups = {}
    for v in cv: groups.setdefault(find(v), []).append(v)
    neq = 0
    for g in groups.values():
        if len(g) < 2: continue
        w = {}
        for v in g:
            for k, x in v[dl].items(): w[k] = w.get(k, 0.0) + x / len(g)
        top = sorted(w.items(), key=lambda kv: -kv[1])[:4]; sm = sum(x for _, x in top) or 1.0
        for v in g:
            v[dl].clear()
            for k, x in top: v[dl][k] = x / sm
        neq += len(g)
    print(f'{pref}: vertices con pesos igualados por arista corta {neq}')
    bm.to_mesh(me); bm.free(); me.update()
    print(f'{pref}: vertices suavizados {len(sel)}/{len(cv)}')


a = sys.argv[sys.argv.index('--') + 1:]
for p in a[1:]: run(p)
bpy.ops.wm.save_as_mainfile(filepath=a[0])
print('SMOOTHDONE', a[0])
