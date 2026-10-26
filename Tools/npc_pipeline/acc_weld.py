"""Funde en una sola pieza continua las tiras (cinturones, correas, ribetes) que shell_cull dejo como cuadrados sueltos con huecos de 2-5 mm.
Solo toca los vertices de los materiales indicados (no compartidos con otros materiales). Distancia de fusion = min(MAXW, 0.45 * arista mas corta).
Uso: blender -b WORK.blend --python acc_weld.py -- Pref Mat1,Mat2 [--maxw 0.006] [--save]"""
import bpy, bmesh, sys, collections
from mathutils.kdtree import KDTree
O = bpy.data.objects


def islands(me, vs):
    adj = collections.defaultdict(set)
    for e in me.edges:
        a, b = e.vertices
        if a in vs and b in vs: adj[a].add(b); adj[b].add(a)
    seen, n = set(), 0
    for s in vs:
        if s in seen: continue
        n += 1; st = [s]; seen.add(s)
        while st:
            v = st.pop()
            for q in adj[v]:
                if q not in seen: seen.add(q); st.append(q)
    return n


def weld(pref, names, maxw=0.006):
    ob = O[pref + '_Mesh']; me = ob.data; out = []
    mats = [m.name if m else '' for m in me.materials]
    for n in names:
        vs = {v for pl in me.polygons if mats[pl.material_index] == n for v in pl.vertices}
        other = {v for pl in me.polygons if mats[pl.material_index] != n for v in pl.vertices}
        vs -= other
        before = islands(me, vs)
        el = min((me.vertices[e.vertices[0]].co - me.vertices[e.vertices[1]].co).length for e in me.edges if e.vertices[0] in vs and e.vertices[1] in vs and (me.vertices[e.vertices[0]].co - me.vertices[e.vertices[1]].co).length > 1e-5)
        dist = maxw
        # une SOLO vertices de islas distintas a menos de maxw (no colapsa los de un mismo cuadrado)
        adj = collections.defaultdict(set)
        for e in me.edges:
            x, y = e.vertices
            if x in vs and y in vs: adj[x].add(y); adj[y].add(x)
        isl = {}
        for s0 in vs:
            if s0 in isl: continue
            isl[s0] = s0; st = [s0]
            while st:
                v = st.pop()
                for q in adj[v]:
                    if q not in isl: isl[q] = s0; st.append(q)
        L = sorted(vs); kd = KDTree(len(L))
        for i in L: kd.insert(me.vertices[i].co, i)
        kd.balance()
        par = {i: i for i in L}
        def find(i):
            while par[i] != i: par[i] = par[par[i]]; i = par[i]
            return i
        for i in L:
            for co, j, d in kd.find_range(me.vertices[i].co, maxw):
                if isl[j] != isl[i]: par[find(i)] = find(j)
        groups = collections.defaultdict(list)
        for i in L: groups[find(i)].append(i)
        bm = bmesh.new(); bm.from_mesh(me); bm.verts.ensure_lookup_table()
        tmap = {}
        for g in groups.values():
            if len(g) > 1:
                c = sum((me.vertices[i].co for i in g), me.vertices[g[0]].co * 0) / len(g)
                tgt = bm.verts[g[0]]
                for i in g:
                    if i != g[0]: tmap[bm.verts[i]] = tgt
                tgt.co = c
        bmesh.ops.weld_verts(bm, targetmap=tmap)
        bm.to_mesh(me); bm.free(); me.update()
        mats = [m.name if m else '' for m in me.materials]
        vs2 = {v for pl in me.polygons if mats[pl.material_index] == n for v in pl.vertices} - {v for pl in me.polygons if mats[pl.material_index] != n for v in pl.vertices}
        out.append((n, f'dist {dist*1000:.1f} mm', f'islas {before} -> {islands(me, vs2)}', f'verts {len(vs)} -> {len(vs2)}'))
    return out


if __name__ == '__main__':
    a = sys.argv[sys.argv.index('--') + 1:]
    mw = float(a[a.index('--maxw') + 1]) if '--maxw' in a else 0.006
    for l in weld(a[0], a[1].split(','), mw): print('WELD', a[0], l)
    if '--save' in a: bpy.ops.wm.save_mainfile(); print('SAVED')
