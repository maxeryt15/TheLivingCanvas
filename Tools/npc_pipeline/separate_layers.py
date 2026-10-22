"""Separa capas solapadas (ropa sobre ropa, accesorios sobre prendas: delantal/vestido, chaqueta/camisa, botones, parches, corbata...) para que no se
solapen en el mismo plano (z-fighting / parpadeo) ni se atraviesen. Por cada vertice de una isla que queda a < TRIGGER de otra isla, y por FUERA de ella
(la otra superficie esta detras de su normal), se empuja hacia afuera hasta MIN_GAP. La isla de piel no se mueve (es la base).
Uso: exec(open(r"D:/TheLivingCanvas/Tools/npc_pipeline/separate_layers.py").read()); separate_layers_npc('Caf')"""
import bpy, bmesh
from mathutils import Vector
from mathutils.bvhtree import BVHTree

O = bpy.data.objects
TRIGGER = 0.0012    # distancia por debajo de la cual dos capas se consideran solapadas (1.2 mm)
MIN_GAP = 0.0022    # separacion final (2.2 mm)
MIN_FACES = 4       # islas minusculas (puntos de decoracion) tambien cuentan


def _islands(bm):
    seen = {}; n = 0
    for f in bm.faces:
        if f.index in seen:
            continue
        stack = [f]; seen[f.index] = n
        while stack:
            cur = stack.pop()
            for v in cur.verts:
                for nf in v.link_faces:
                    if nf.index not in seen:
                        seen[nf.index] = n; stack.append(nf)
        n += 1
    return seen, n


def separate_layers_npc(prefix, max_iter=2):
    ob = O[prefix + '_Mesh']; me = ob.data; mw = ob.matrix_world; nm = mw.to_3x3(); inv = mw.inverted().to_3x3()
    skin_mats = {i for i, m in enumerate(me.materials) if m and m.name.endswith('skin_Paint')}
    report = {'moved': 0, 'islands': 0}
    for it in range(max_iter):
        bm = bmesh.new(); bm.from_mesh(me); bm.verts.ensure_lookup_table(); bm.faces.ensure_lookup_table(); bm.normal_update()
        isl, n = _islands(bm)
        wco = [mw @ v.co for v in bm.verts]
        # la isla de piel es la que mas caras de piel tiene
        cnt = {}
        for f in bm.faces:
            if f.material_index in skin_mats: cnt[isl[f.index]] = cnt.get(isl[f.index], 0) + 1
        skin_island = max(cnt, key=cnt.get) if cnt else -1
        report['islands'] = n
        island_verts = {}
        for f in bm.faces:
            for v in f.verts: island_verts.setdefault(isl[f.index], set()).add(v.index)
        moves = {}
        for gi in range(n):
            if gi == skin_island:
                continue
            polys = [tuple(v.index for v in f.verts) for f in bm.faces if isl[f.index] != gi]
            if not polys:
                continue
            bvh = BVHTree.FromPolygons(wco, polys)
            for vi in island_verts[gi]:
                v = bm.verts[vi]
                p = wco[vi]
                loc, nrm, fi, d = bvh.find_nearest(p, TRIGGER)
                if loc is None:
                    continue
                nv = (nm @ v.normal).normalized()
                # solo si la otra capa queda por detras de este vertice (este vertice es el de fuera)
                if d > 1e-5 and (loc - p).dot(nv) > 0:
                    continue
                push = MIN_GAP - d
                dirv = nv if d <= 1e-5 else ((p - loc).normalized() if (p - loc).dot(nv) > 0 else nv)
                moves[vi] = inv @ (dirv * push)
        for vi, dv in moves.items():
            bm.verts[vi].co += dv
        report['moved'] += len(moves)
        bm.to_mesh(me); bm.free(); me.update()
        if not moves:
            break
    return report
