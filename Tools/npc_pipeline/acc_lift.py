"""Levanta accesorios hundidos en la prenda (corbatas) para que descansen SOBRE la ropa. Solo mueve los vertices de los materiales indicados
(en todas las shape keys por igual, asi no cambia ninguna diferencia). Uso: blender -b WORK.blend --python acc_lift.py -- Pref Mat1,Mat2 [--clear 0.004] [--save]"""
import bpy, sys, collections
sys.path.insert(0, r'D:\TheLivingCanvas\Tools\npc_pipeline')
import penetration_sweep as PS
from mathutils.bvhtree import BVHTree
O = bpy.data.objects


def lift(pref, mats_, clear=0.004, iters=6):
    ob = O[pref + '_Mesh']; me = ob.data
    mats = [m.name if m else '' for m in me.materials]
    cf = [pl for pl in me.polygons if PS.is_cloth(mats[pl.material_index])]
    cv = {v for pl in cf for v in pl.vertices}
    co = [v.co.copy() for v in me.vertices]
    bvh = BVHTree.FromPolygons(co, [tuple(pl.vertices) for pl in cf])
    vs = {v for pl in me.polygons if mats[pl.material_index] in mats_ for v in pl.vertices} - cv
    delta = {}
    for i in vs:
        loc, nor, idx, dist = bvh.find_nearest(co[i])
        if loc is None or dist > 0.05: continue
        d = (co[i] - loc).dot(nor)
        delta[i] = nor * max(0.0, clear - d)
    adj = collections.defaultdict(set)
    for e in me.edges:
        a, b = e.vertices
        if a in vs and b in vs: adj[a].add(b); adj[b].add(a)
    for _ in range(iters):   # suaviza el desplazamiento sin bajarlo: max(vecinos, propio)
        new = {}
        for i, d in delta.items():
            nb = [delta[j] for j in adj[i] if j in delta]
            avg = (d + sum(nb, d * 0)) / (1 + len(nb))
            new[i] = avg if avg.length > d.length else d
        delta = new
    moved = [i for i, d in delta.items() if d.length > 1e-5]
    keys = me.shape_keys.key_blocks if me.shape_keys else []
    for k in keys:
        for i in moved: k.data[i].co += delta[i]
    for i in moved: me.vertices[i].co += delta[i]
    return len(vs), len(moved), max([delta[i].length for i in moved] + [0]) * 1000


if __name__ == '__main__':
    a = sys.argv[sys.argv.index('--') + 1:]
    clear = float(a[a.index('--clear') + 1]) if '--clear' in a else 0.004
    print('LIFT', a[0], lift(a[0], a[1].split(','), clear))
    if '--save' in a: bpy.ops.wm.save_mainfile(); print('SAVED')
