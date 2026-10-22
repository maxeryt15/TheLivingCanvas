"""Cierra costuras abiertas (pinholes / 'lineas de sutura') en las mallas de los NPC.

Causa: la malla se decima por partes (cabeza / cuerpo) y las piezas se unen con T-junctions y vertices casi coincidentes sin soldar,
asi que quedan bordes abiertos y huecos de pocos milimetros que en Unity se ven como puntos/lineas claras u oscuras.

close_seams(ob, tol):
  0. suelda duplicados exactos (1e-5);
  1. suelda vertices de borde que estan a menos de `tol` entre si;
  2. T-junctions: parte el borde abierto mas cercano en la proyeccion del vertice y los suelda;
  3. rellena huecos pequenos (<= max_hole aristas);
  4. triangula.
Los UV son por loop (se conservan); los pesos de vertice se quedan los del vertice que sobrevive.
Uso (Blender): exec(open(r"D:/TheLivingCanvas/Tools/npc_pipeline/fix_seams.py").read()); close_seams(bpy.data.objects['Cou_Low'])
"""
import bpy
import bmesh
from mathutils import Vector


def _boundary_verts(bm):
    return [v for v in bm.verts if any(len(e.link_faces) == 1 for e in v.link_edges)]


def _stats(bm):
    return sum(1 for e in bm.edges if len(e.link_faces) == 1), sum(1 for e in bm.edges if len(e.link_faces) > 2)


def _closest_on_edge(p, a, b):
    ab = b - a
    t = max(0.0, min(1.0, (p - a).dot(ab) / max(ab.length_squared, 1e-18)))
    return a + ab * t, t


def close_seams(ob, tol=0.003, max_hole=8, iterations=3, verbose=True):
    me = ob.data
    bm = bmesh.new()
    bm.from_mesh(me)
    before = _stats(bm)
    bmesh.ops.remove_doubles(bm, verts=bm.verts[:], dist=1e-5)   # 0. duplicados exactos (vertices coincidentes sin soldar), sean de borde o no
    for _ in range(iterations):
        # 1. soldar vertices de borde cercanos
        bv = _boundary_verts(bm)
        bmesh.ops.remove_doubles(bm, verts=bv, dist=tol)
        bm.verts.ensure_lookup_table()
        bm.edges.ensure_lookup_table()
        # 2. T-junctions: vertice de borde sobre una arista de borde ajena
        changed = False
        bedges = [e for e in bm.edges if len(e.link_faces) == 1]
        for v in _boundary_verts(bm):
            if not v.is_valid or not any(len(x.link_faces) == 1 for x in v.link_edges):
                continue
            best = None
            for e in bedges:
                if not e.is_valid or v in e.verts:
                    continue
                a, b = e.verts[0].co, e.verts[1].co
                q, t = _closest_on_edge(v.co, a, b)
                d = (q - v.co).length
                if 0.02 < t < 0.98 and d < tol and (best is None or d < best[0]):
                    best = (d, e, t)
            if best:
                _, e, t = best
                ev0 = e.verts[0]
                ne, nv = bmesh.utils.edge_split(e, ev0, t)
                bmesh.ops.pointmerge(bm, verts=[v, nv], merge_co=v.co)
                changed = True
                bm.verts.ensure_lookup_table()
                bm.edges.ensure_lookup_table()
                bedges = [x for x in bm.edges if len(x.link_faces) == 1]
        if not changed:
            break
    # 3. rellenar huecos pequenos
    bm.edges.ensure_lookup_table()
    be = [e for e in bm.edges if len(e.link_faces) == 1]
    seen = set()
    loops = []
    for e in be:
        if e in seen:
            continue
        comp, st = [], [e]
        seen.add(e)
        while st:
            c = st.pop()
            comp.append(c)
            for v in c.verts:
                for n in v.link_edges:
                    if len(n.link_faces) == 1 and n not in seen:
                        seen.add(n)
                        st.append(n)
        loops.append(comp)
    filled = 0
    uvl = bm.loops.layers.uv.get('UV_Paint') or bm.loops.layers.uv.active
    for comp in loops:
        if len(comp) <= max_hole:
            nb = comp[0].link_faces[0]
            res = bmesh.ops.holes_fill(bm, edges=comp, sides=max_hole)
            for f in res.get('faces', []):
                f.material_index = nb.material_index
                f.smooth = False
                for l in f.loops:      # UV de la cara vecina que comparte el vertice (sin esto el parche cae en un texel negro)
                    for o in l.vert.link_loops:
                        if o.face not in res['faces']:
                            l[uvl].uv = o[uvl].uv
                            break
            filled += len(res.get('faces', []))
    bmesh.ops.triangulate(bm, faces=bm.faces[:], quad_method='BEAUTY', ngon_method='BEAUTY')
    after = _stats(bm)
    bm.to_mesh(me)
    bm.free()
    me.update()
    if verbose:
        print(ob.name, 'boundary/nonmanifold', before, '->', after, 'holes filled faces', filled)
    return before, after


def _boundary_loops(bm):
    be = [e for e in bm.edges if len(e.link_faces) == 1]
    seen, loops = set(), []
    for e in be:
        if e in seen:
            continue
        comp, st = [], [e]
        seen.add(e)
        while st:
            c = st.pop()
            comp.append(c)
            for v in c.verts:
                for n in v.link_edges:
                    if len(n.link_faces) == 1 and n not in seen:
                        seen.add(n)
                        st.append(n)
        loops.append(comp)
    return loops


def cap_trim_holes(ob, min_edges=9, uv_name='UV_Paint', verbose=True):
    """Cierra los huecos grandes de la malla del cuerpo (zonas recortadas bajo la ropa) con tapas.
    Sin tapa, el borde del hueco queda justo bajo el escote/cuello/mangas de la ropa y por la rendija se ve el interior
    (puntos o lineas claras/oscuras). La tapa usa un solo texel de piel (UV constante) y el material de la cara vecina."""
    me = ob.data
    bm = bmesh.new()
    bm.from_mesh(me)
    uvl = bm.loops.layers.uv.get(uv_name) or bm.loops.layers.uv.active
    n_caps = 0
    for comp in _boundary_loops(bm):
        if len(comp) < min_edges:
            continue
        edge_face = comp[0].link_faces[0]
        mat = edge_face.material_index
        uv = Vector((0.0, 0.0))
        for l in edge_face.loops:
            uv += l[uvl].uv
        uv /= len(edge_face.loops)          # texel de piel dentro de una isla (cara vecina)
        res = bmesh.ops.holes_fill(bm, edges=comp, sides=len(comp) + 2)
        for f in res['faces']:
            f.material_index = mat
            f.smooth = False
            for l in f.loops:
                l[uvl].uv = uv
        n_caps += len(res['faces'])
    new_faces = [f for f in bm.faces if len(f.verts) > 4]
    if new_faces:
        bmesh.ops.triangulate(bm, faces=new_faces, quad_method='BEAUTY', ngon_method='EAR_CLIP')
    after = _stats(bm)
    bm.to_mesh(me)
    bm.free()
    me.update()
    if verbose:
        print(ob.name, 'tapas:', n_caps, 'ngons; borde/no-manifold ->', after)
    return n_caps


def kill_folded_slivers(ob, zmax=None, max_area=3e-5, min_angle=120.0, iterations=12, verbose=True):
    """Elimina los triangulos minusculos plegados (normal opuesta a la de un vecino) que dejo la union de piezas.
    Forman una 'banda de pliegue' de milimetros que en Unity se ve como puntos/lineas claras u oscuras (costura).
    Se colapsa la arista mas corta de cada triangulo plegado hasta que no quedan.  zmax: solo por debajo de esa z (mundo)."""
    import math
    mw = ob.matrix_world
    me = ob.data
    bm = bmesh.new()
    bm.from_mesh(me)
    removed = 0
    for it in range(iterations):
        bm.normal_update()
        bad = []
        for f in bm.faces:
            if f.calc_area() > max_area:
                continue
            if zmax is not None and (mw @ f.calc_center_median()).z > zmax:
                continue
            for e in f.edges:
                if len(e.link_faces) == 2:
                    o = e.link_faces[0] if e.link_faces[1] == f else e.link_faces[1]
                    if f.normal.length < 1e-9 or o.normal.length < 1e-9 or math.degrees(f.normal.angle(o.normal)) > min_angle:
                        bad.append(f)      # normal nula = triangulo degenerado
                        break
        if not bad:
            break
        done = set()
        for f in bad:
            if not f.is_valid or f in done:
                continue
            e = min(f.edges, key=lambda x: x.calc_length())
            if not e.is_valid:
                continue
            nb = {x for v in e.verts for x in v.link_faces}
            if nb & done:
                continue
            bmesh.ops.collapse(bm, edges=[e])
            done |= nb
            removed += 1
        bm.verts.ensure_lookup_table()
    left = 0
    bm.normal_update()
    stats = _stats(bm)
    bm.to_mesh(me)
    bm.free()
    me.update()
    if verbose:
        print(ob.name, 'slivers colapsados:', removed, '; borde/no-manifold', stats)
    return removed


def heal_dark_uv_faces(ob, img, max_area=4e-4, dark=0.35, bright_nb=0.5, verbose=True):
    """Caras pequenas cuyo UV cae en un texel oscuro (agujero del bake / mancha negra) rodeadas de caras claras:
    se les da el UV del centro de una cara vecina (color plano igual al del entorno). Es el triangulo oscuro de las costuras del cuello/escote."""
    import numpy as np
    from collections import defaultdict
    me = ob.data
    uvl = me.uv_layers['UV_Paint'].data
    w, h = img.size
    a = np.empty(w * h * 4, dtype=np.float32)
    img.pixels.foreach_get(a)
    a = a.reshape(h, w, 4)

    def col(poly):
        ls = list(poly.loop_indices)[:3]
        us = [uvl[l].uv for l in ls]
        cs = []
        for b in [(1/3, 1/3, 1/3), (.6, .2, .2), (.2, .6, .2), (.2, .2, .6)]:
            u = sum(b[i] * us[i][0] for i in range(3))
            v = sum(b[i] * us[i][1] for i in range(3))
            cs.append(a[min(h - 1, max(0, int(v * h))), min(w - 1, max(0, int(u * w))), :3])
        return np.mean(cs, axis=0)

    lum = lambda c: float(0.3 * c[0] + 0.59 * c[1] + 0.11 * c[2])
    cols = {pl.index: col(pl) for pl in me.polygons}
    e2f = defaultdict(list)
    for pl in me.polygons:
        for ek in pl.edge_keys:
            e2f[ek].append(pl.index)
    fixed = []
    for pl in me.polygons:
        if pl.area > max_area or lum(cols[pl.index]) > dark:
            continue
        nbs = sorted({j for ek in pl.edge_keys for j in e2f[ek] if j != pl.index})
        if nbs and all(lum(cols[j]) > bright_nb for j in nbs):
            fixed.append((pl, nbs[0]))
    for pl, j in fixed:
        npoly = me.polygons[j]
        c = sum((uvl[l].uv for l in npoly.loop_indices), Vector((0.0, 0.0))) / len(npoly.loop_indices)
        for l in pl.loop_indices:
            uvl[l].uv = c
    me.update()
    if verbose:
        print(ob.name, 'caras oscuras curadas:', len(fixed))
    return len(fixed)
