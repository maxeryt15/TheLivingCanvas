"""Compara <Pref>_Mesh del .blend abierto contra el de otro .blend (solo lectura): vertices, shape keys, pesos, UV, materiales, caras.
Uso: blender -b WORK.blend --python diff_npc_blend.py -- Stu <ruta al otro .blend>"""
import bpy, sys, numpy as np
pref, other = sys.argv[sys.argv.index('--') + 1:][:2]
cur = bpy.data.objects[pref + '_Mesh']
with bpy.data.libraries.load(other) as (df, dt): dt.objects = [pref + '_Mesh']
ref = dt.objects[0]
def co(me, kb=None):
    a = np.empty(len(me.vertices) * 3)
    (kb.data if kb else me.vertices).foreach_get('co', a); return a.reshape(-1, 3)
m1, m2 = cur.data, ref.data
print('DIFF verts', len(m1.vertices), len(m2.vertices), 'faces', len(m1.polygons), len(m2.polygons), 'mats equal', [m.name for m in m1.materials] == [m.name for m in m2.materials])
d = np.linalg.norm(co(m1) - co(m2), axis=1); ch = np.nonzero(d > 1e-9)[0]
print('DIFF basis moved verts', len(ch), 'max mm', round(d.max() * 1000, 2))
k1 = {k.name: k for k in m1.shape_keys.key_blocks}; k2 = {k.name: k for k in m2.shape_keys.key_blocks}
print('DIFF key names equal', list(k1) == list(k2))
for n in k1:
    dk = np.linalg.norm(co(m1, k1[n]) - co(m2, k2[n]), axis=1); rel = np.linalg.norm((co(m1, k1[n]) - co(m1)) - (co(m2, k2[n]) - co(m2)), axis=1)
    print('DIFF key %-12s abs moved %3d  key-delta change max %.2e m' % (n, (dk > 1e-9).sum(), rel.max()))
n1 = [g.name for g in cur.vertex_groups]; n2 = [g.name for g in ref.vertex_groups]
W1 = [{n1[g.group]: g.weight for g in v.groups} for v in m1.vertices]; W2 = [{n2[g.group]: g.weight for g in v.groups} for v in m2.vertices]
wch = [i for i in range(len(W1)) if any(abs(W1[i].get(k, 0) - W2[i].get(k, 0)) > 1e-7 for k in set(W1[i]) | set(W2[i]))]
print('DIFF weight-changed verts', len(wch), 'vgroup names equal', n1 == n2)
u1 = np.empty(len(m1.loops) * 2); m1.uv_layers.active.data.foreach_get('uv', u1); u2 = np.empty(len(m2.loops) * 2); m2.uv_layers.active.data.foreach_get('uv', u2)
print('DIFF uv max', float(np.abs(u1 - u2).max()), 'moved-vert ids range', (int(ch.min()), int(ch.max())) if len(ch) else None, 'ids', ch.tolist()[:100])
