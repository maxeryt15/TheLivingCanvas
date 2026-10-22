"""Corrige pesos de hueso erroneos en las piezas de los NPC (picos / vertices que se estiran al animar).

Causa: algunos vertices de ropa y accesorios quedaron ligados a huesos lejanos (p. ej. bolsa o pantalon -> foot_r, hombreras -> pelvis,
cinturon -> head). En T-pose no se nota; con una animacion real el vertice viaja con el hueso lejano y se ve una 'aguja'.

fix_all(): por cada pieza (menos *_Low) detecta vertices con peso > 0.15 en un hueso a mas de 0.30 m de su segmento (cabeza-cola)
y les copia los pesos del vertice mas cercano del cuerpo (*_Low), que esta bien pesado. Se repite hasta que no quedan.
Uso (Blender, escena All10_Review*.blend abierta):  exec(open(r"D:/TheLivingCanvas/Tools/npc_pipeline/fix_weights.py").read()); fix_all()
"""
import bpy
import bmesh
from mathutils import Vector
from mathutils.bvhtree import BVHTree

PREFIXES = ['Cur', 'Grd', 'Stu', 'Gar', 'Caf', 'Tou', 'Gen', 'Cou', 'Doc', 'Pnt']
MAX_DIST = 0.30
MIN_W = 0.15
MIN_HOPS = 3


def _seg_dist(p, a, b):
    ab = b - a
    t = max(0.0, min(1.0, (p - a).dot(ab) / max(ab.length_squared, 1e-12)))
    return (p - (a + ab * t)).length


def _hops(arm):
    """distancia en saltos de esqueleto entre dos huesos."""
    par = {b.name: (b.parent.name if b.parent else None) for b in arm.data.bones}

    def anc(n):
        out = [n]
        while par.get(n):
            n = par[n]
            out.append(n)
        return out

    def hops(a, b):
        A, B = anc(a), anc(b)
        common = [x for x in A if x in B]
        if not common:
            return 99
        c = common[0]
        return A.index(c) + B.index(c)
    return hops


def bad_vertices(ob, seg, ctx=None):
    """Vertices cuyo hueso dominante esta lejos de su segmento Y lejos (>= MIN_HOPS saltos) del hueso dominante del cuerpo mas cercano.
    Asi el pelo largo (cabeza) o el borde de un abrigo (muslo) no se tocan: solo los pesos claramente equivocados."""
    mw = ob.matrix_world
    vg = {g.index: g.name for g in ob.vertex_groups}
    out = []
    for v in ob.data.vertices:
        p = mw @ v.co
        dom = max(v.groups, key=lambda g: g.weight, default=None)
        if dom is None:
            continue
        n = vg.get(dom.group)
        if n not in seg or dom.weight < MIN_W or _seg_dist(p, *seg[n]) <= MAX_DIST:
            continue
        if ctx is not None:
            loc, nrm, fi, dist = ctx['bvh'].find_nearest(p)
            if loc is not None:
                poly = ctx['low'].data.polygons[fi]
                near = min(poly.vertices, key=lambda k: ((ctx['low'].matrix_world @ ctx['low'].data.vertices[k].co) - p).length)
                w = ctx['low_w'][near]
                if w:
                    c = max(w, key=w.get)
                    if ctx['hops'](n, c) < MIN_HOPS:
                        continue
        out.append(v.index)
    return out


def fix_mesh(ob, low, seg, bvh, low_w, ctx):
    bad = bad_vertices(ob, seg, ctx)
    if not bad:
        return 0
    mw = ob.matrix_world
    groups = {g.name: g for g in ob.vertex_groups}
    for vi in bad:
        v = ob.data.vertices[vi]
        p = mw @ v.co
        loc, nrm, fi, dist = bvh.find_nearest(p)
        if loc is None:
            continue
        poly = low.data.polygons[fi]
        near = min(poly.vertices, key=lambda k: ((low.matrix_world @ low.data.vertices[k].co) - p).length)
        w = low_w[near]
        if not w:
            continue
        for g in list(v.groups):
            ob.vertex_groups[g.group].remove([vi])
        s = sum(w.values())
        for name, val in w.items():
            if name not in groups:
                groups[name] = ob.vertex_groups.new(name=name)
            groups[name].add([vi], val / s, 'REPLACE')
    return len(bad)


def fix_all(max_iter=3, verbose=True):
    O = bpy.data.objects
    total = {}
    for pre in PREFIXES:
        arm = O[pre + '_Rig']
        mwa = arm.matrix_world
        seg = {b.name: (mwa @ b.head_local, mwa @ b.tail_local) for b in arm.data.bones}
        low = O[pre + '_Low']
        bm = bmesh.new()
        bm.from_mesh(low.data)
        bm.transform(low.matrix_world)
        bm.faces.ensure_lookup_table()
        bvh = BVHTree.FromBMesh(bm)
        bm.free()
        lg = {g.index: g.name for g in low.vertex_groups}
        low_w = []
        for v in low.data.vertices:
            low_w.append({lg[g.group]: g.weight for g in v.groups if lg.get(g.group) in seg and g.weight > 0.001})
        ctx = dict(bvh=bvh, low=low, low_w=low_w, hops=_hops(arm))
        for ob in arm.children:
            if ob.type != 'MESH' or ob.name.endswith('_Low'):
                continue
            n = 0
            for _ in range(max_iter):
                k = fix_mesh(ob, low, seg, bvh, low_w, ctx)
                n += k
                if not k:
                    break
            if n:
                total[ob.name] = n
                if verbose:
                    print('pesos corregidos', ob.name, n, 'vertices; restantes', len(bad_vertices(ob, seg, ctx)))
    return total
