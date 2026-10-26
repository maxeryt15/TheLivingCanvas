"""Pesos de prenda ajustada: los vertices de prenda a menos de HUG m de la piel (en reposo) heredan los pesos del vertice de piel mas cercano,
con mezcla lineal segun la distancia (t = 1 - d/HUG). Evita que mangas/bajos se hundan en la piel cuando el hueso gira.
Maximo 4 influencias, normalizado. Uso: blender -b X.blend --python hug_weights.py -- salida.blend Pref [Pref ...]
"""
import bpy, bmesh, sys
from mathutils.kdtree import KDTree
from mathutils.bvhtree import BVHTree

HUG = 0.02
CLOTH_KEYS = ('clothes_paint', 'suit_', 'aproncloth', 'blouse', 'scarfcloth')


def run(pref):
    ob = bpy.data.objects[pref + '_Mesh']; me = ob.data
    bm = bmesh.new(); bm.from_mesh(me)
    dl = bm.verts.layers.deform.verify()
    bm.verts.ensure_lookup_table(); bm.faces.ensure_lookup_table()
    def mat(f): return (me.materials[f.material_index].name.lower() if me.materials[f.material_index] else '')
    skin_f = [f for f in bm.faces if mat(f).endswith('skin_paint')]
    cloth_f = [f for f in bm.faces if any(k in mat(f) for k in CLOTH_KEYS)]
    skin_v = list({v for f in skin_f for v in f.verts} - {v for f in cloth_f for v in f.verts})
    cloth_v = list({v for f in cloth_f for v in f.verts})
    kd = KDTree(len(skin_v)); [kd.insert(v.co, i) for i, v in enumerate(skin_v)]; kd.balance()
    verts = [v.co.copy() for v in bm.verts]
    bvh = BVHTree.FromPolygons(verts, [tuple(v.index for v in f.verts) for f in skin_f])
    n = 0
    for v in cloth_v:
        loc, nor, idx, dist = bvh.find_nearest(v.co)
        if loc is None or dist > HUG:
            continue
        t = 1.0 - dist / HUG
        sv = skin_v[kd.find(v.co)[1]]
        w = {}
        for g, x in v[dl].items(): w[g] = w.get(g, 0.0) + x * (1 - t)
        for g, x in sv[dl].items(): w[g] = w.get(g, 0.0) + x * t
        top = sorted(w.items(), key=lambda kv: -kv[1])[:4]
        s = sum(x for _, x in top) or 1.0
        v[dl].clear()
        for g, x in top: v[dl][g] = x / s
        n += 1
    bm.to_mesh(me); bm.free(); me.update()
    print(f'{pref}: vertices de prenda ajustados {n}/{len(cloth_v)}')


a = sys.argv[sys.argv.index('--') + 1:]
for p in a[1:]:
    run(p)
bpy.ops.wm.save_as_mainfile(filepath=a[0])
print('HUGDONE', a[0])
