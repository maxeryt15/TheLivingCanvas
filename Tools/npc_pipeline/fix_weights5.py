"""Prendas ajustadas siguen al cuerpo: en las zonas donde la prenda esta a < NEAR m de la piel (Low) se copian los pesos del vertice de piel mas cercano,
asi cuerpo y tela se mueven igual y la piel no asoma al animar. Despues 1 iteracion de suavizado y un 'inflado' de INFLATE m a lo largo de la normal
(margen para el cuerpo). Las zonas sueltas/lejanas (bajos de falda, perneras anchas) conservan sus pesos.
Uso: exec(open(r"D:/TheLivingCanvas/Tools/npc_pipeline/fix_weights5.py").read()); run_all5()"""
import bpy, bmesh
from mathutils.bvhtree import BVHTree

exec(open(r"D:/TheLivingCanvas/Tools/npc_pipeline/fix_weights2.py", encoding='utf-8').read())  # smooth_weights, PREFIXES
GARMENT = ('_Suit', '_Pants', '_Tee', '_Shirt', '_Dress', '_Top', '_Shorts', '_Apron')
NEAR = 0.035
INFLATE = 0.004
O = bpy.data.objects


def follow_body(ob, low, arm):
    deform = {b.name for b in arm.data.bones if b.use_deform}
    bm = bmesh.new(); bm.from_mesh(low.data); bm.transform(low.matrix_world); bm.faces.ensure_lookup_table()
    bvh = BVHTree.FromBMesh(bm); bm.free()
    lg = {g.index: g.name for g in low.vertex_groups}
    low_w = [{lg[g.group]: g.weight for g in v.groups if lg.get(g.group) in deform and g.weight > 1e-3} for v in low.data.vertices]
    mw = ob.matrix_world
    groups = {g.name: g for g in ob.vertex_groups}
    n = 0
    for v in ob.data.vertices:
        p = mw @ v.co
        loc, nrm, fi, dist = bvh.find_nearest(p, NEAR)
        if loc is None:
            continue
        poly = low.data.polygons[fi]
        near = min(poly.vertices, key=lambda k: ((low.matrix_world @ low.data.vertices[k].co) - p).length)
        w = low_w[near]
        if not w:
            continue
        for g in list(v.groups):
            ob.vertex_groups[g.group].remove([v.index])
        s = sum(w.values())
        for name, val in w.items():
            if name not in groups:
                groups[name] = ob.vertex_groups.new(name=name)
            groups[name].add([v.index], val / s, 'REPLACE')
        n += 1
    smooth_weights(ob, deform, iters=1, factor=0.4)
    return n


def inflate(ob, amount):
    me = ob.data
    me.calc_normals() if hasattr(me, 'calc_normals') else None
    for v in me.vertices:
        v.co += v.normal * amount
    me.update()


def run_all5():
    res = {}
    for pre in PREFIXES:
        arm = O[pre + '_Rig']; low = O[pre + '_Low']
        for ob in arm.children:
            if ob.type == 'MESH' and ob.name.endswith(GARMENT):
                n = follow_body(ob, low, arm)
                inflate(ob, INFLATE)
                res[ob.name] = n
    print('W5', res)
    return res
