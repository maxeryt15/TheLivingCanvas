"""Cierra con un 'cono' (labio) cada borde abierto de una prenda hacia la superficie interior mas cercana (piel u otra prenda por debajo):
cuello, punos, bajos de pantalon/camisa, cintura, aberturas de chaqueta. El labio es una tira de caras que sale del borde de la prenda,
sigue la direccion de la prenda y se apoya a ~1 mm de la piel; toma los pesos de la piel (se mueve con ella) y el material/UV de la prenda.
Evita el hueco visible entre prenda y piel y la luz/vacio detras del borde. Se aplica sobre la malla ya fusionada <prefijo>_Mesh.
Uso: exec(open(r"D:/TheLivingCanvas/Tools/npc_pipeline/add_lips.py").read()); add_lips_npc('Caf')"""
import bpy, bmesh
from mathutils import Vector
from mathutils.bvhtree import BVHTree

O = bpy.data.objects
GARM_SUFFIX = ('clothes_Paint', 'ApronCloth', 'Suit_Blouse', 'Suit_Shirt')
MAX_DIST = 0.02       # el labio solo baja a superficies a menos de 2 cm (con 4.5 cm el cuello de la chaqueta subia conos hasta la mandibula)
OFFSET = 0.0012       # el labio queda 1.2 mm por encima de la superficie de apoyo (sin z-fight)
LIP_SKIP = ('ApronCloth',)   # los delantales (con tirantes colgando) no generan labios; si sirven de apoyo a otras prendas
MIN_LOOP = 6          # bordes minimos de un lazo
MIN_LOOP_LEN = 0.18   # longitud minima del lazo (m): cuello, punos, bajos y cinturas si; extremos de tirantes/correas (3-5 cm) no (dejaban lineas oscuras sobre la piel)
MIN_VALID = 0.9      # fraccion minima de vertices del lazo con apoyo valido


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


def add_lips_npc(prefix, max_dist=MAX_DIST):
    ob = O[prefix + '_Mesh']
    me = ob.data; mw = ob.matrix_world; nm = mw.to_3x3()
    garm = {i for i, m in enumerate(me.materials) if m and m.name.endswith(GARM_SUFFIX)}
    skin = {i for i, m in enumerate(me.materials) if m and m.name.endswith('skin_Paint')}
    bm = bmesh.new(); bm.from_mesh(me)
    bm.verts.ensure_lookup_table(); bm.faces.ensure_lookup_table(); bm.edges.ensure_lookup_table()
    bm.normal_update()
    orig_faces = list(bm.faces); orig_edges = list(bm.edges)   # las caras/bordes nuevos del labio no cuentan en las siguientes islas
    dl = bm.verts.layers.deform.verify()
    isl, nisl = _islands(bm)
    # islas de prenda: mayoria de caras con material de prenda y tamano razonable
    count = {}; gcount = {}
    for f in orig_faces:
        i = isl[f.index]; count[i] = count.get(i, 0) + 1
        if f.material_index in garm: gcount[i] = gcount.get(i, 0) + 1
    garment_islands = [i for i in count if count[i] >= 40 and gcount.get(i, 0) >= 0.7 * count[i]]
    wco = [mw @ v.co for v in bm.verts]
    report = {'islands': len(garment_islands), 'loops': 0, 'lips': 0, 'skipped': 0}
    new_geo = []
    skip_mats = {i for i, m in enumerate(me.materials) if m and m.name.endswith(LIP_SKIP)}
    for gi in garment_islands:
        if any(f.material_index in skip_mats for f in orig_faces if isl[f.index] == gi):
            continue
        # superficies de apoyo: piel + prendas de OTRAS islas
        polys = []; fmap = []
        for f in orig_faces:
            if isl[f.index] == gi:
                continue
            if f.material_index in skin or (f.material_index in garm and isl[f.index] in garment_islands):
                polys.append(tuple(v.index for v in f.verts)); fmap.append(f)
        bvh = BVHTree.FromPolygons(wco, polys)
        # bordes abiertos de esta isla en caras de prenda
        bedges = [e for e in orig_edges if len(e.link_faces) == 1 and e.link_faces[0].index in isl and isl[e.link_faces[0].index] == gi and e.link_faces[0].material_index in garm]
        # lazos = componentes conexas por vertice
        parent = {}
        def find(a):
            while parent[a] != a:
                parent[a] = parent[parent[a]]; a = parent[a]
            return a
        for e in bedges:
            for v in e.verts: parent.setdefault(v.index, v.index)
        for e in bedges:
            a, b = find(e.verts[0].index), find(e.verts[1].index)
            if a != b: parent[a] = b
        loops = {}
        for e in bedges: loops.setdefault(find(e.verts[0].index), []).append(e)
        for edges in loops.values():
            if len(edges) < MIN_LOOP:
                continue
            if sum((wco[e.verts[0].index] - wco[e.verts[1].index]).length for e in edges) < MIN_LOOP_LEN:
                continue
            report['loops'] += 1
            verts = {v for e in edges for v in e.verts}
            tgt = {}; src_w = {}
            for v in verts:
                p = wco[v.index]; n = (nm @ v.normal).normalized()
                loc, nrm, fi, d = bvh.find_nearest(p, max_dist)
                if loc is None or (loc - p).dot(n) > 0.002:
                    continue   # no hay apoyo por dentro de la prenda
                away = (p - loc); away = away.normalized() if away.length > 1e-6 else n
                tgt[v.index] = mw.inverted() @ (loc + away * OFFSET)
                hf = fmap[fi]
                near = min(hf.verts, key=lambda q: (wco[q.index] - loc).length)
                src_w[v.index] = {g: w for g, w in near[dl].items()}
            if len(tgt) < MIN_VALID * len(verts):
                report['skipped'] += 1
                continue
            # suaviza la altura del apoyo a lo largo del borde (2 pasadas): evita picos por las facetas de la piel
            nb = {}
            for e in edges:
                a, b = e.verts[0].index, e.verts[1].index
                nb.setdefault(a, []).append(b); nb.setdefault(b, []).append(a)
            for _ in range(2):
                sm = {}
                for vi, pt in tgt.items():
                    pts = [pt] + [tgt[q] for q in nb.get(vi, []) if q in tgt]
                    sm[vi] = sum(pts, Vector()) / len(pts)
                tgt = sm
            newv = {}
            for v in verts:
                co = tgt.get(v.index, v.co - v.normal * 0.004)
                nv = bm.verts.new(co)
                w = src_w.get(v.index)
                if w is None:
                    w = {g: x for g, x in v[dl].items()}
                for g, x in w.items(): nv[dl][g] = x
                newv[v.index] = nv
            for e in edges:
                f = e.link_faces[0]
                # orden (a->b) del borde dentro de la cara f; la cara nueva recorre (b, a, a', b')
                loop = next(l for l in f.loops if l.edge == e)
                a, b = loop.vert, loop.link_loop_next.vert
                try:
                    nf = bm.faces.new((b, a, newv[a.index], newv[b.index]))
                except ValueError:
                    continue
                nf.material_index = f.material_index; nf.smooth = f.smooth
                la = next(l for l in nf.loops if l.vert == a); lb = next(l for l in nf.loops if l.vert == b)
                la.copy_from(loop); lb.copy_from(loop.link_loop_next)
                for l in nf.loops:
                    if l.vert == newv[a.index]: l.copy_from(loop)
                    elif l.vert == newv[b.index]: l.copy_from(loop.link_loop_next)
                report['lips'] += 1
    bm.normal_update()
    bm.to_mesh(me); bm.free(); me.update()
    return report
