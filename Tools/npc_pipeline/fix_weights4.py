"""Piezas sueltas sobre la ropa (parches de codo/hombro, hombreras, botones, medalla...): cada isla conexa se ata RIGIDA al hueso dominante
del vertice mas cercano de la PRENDA que lleva debajo (la manga ya esta bien pesada), no al del cuerpo (que esta recortado bajo la ropa).
Sin esto los parches quedaban en el aire junto al brazo al bajar los brazos.
Uso: exec(open(r"D:/TheLivingCanvas/Tools/npc_pipeline/fix_weights4.py").read()); run_all4()"""
import bpy, bmesh
from mathutils.bvhtree import BVHTree

PAIRS = {  # pieza -> prenda de referencia
    'Gen_Patches': 'Gen_Suit', 'Gen_SuitDetails': 'Gen_Suit', 'Gen_Buttons': 'Gen_Suit', 'Gen_Tie': 'Gen_Suit',
    'Grd_SleevePatch': 'Grd_Suit', 'Grd_Epaulettes': 'Grd_Suit', 'Grd_Buttons': 'Grd_Suit', 'Grd_Medal': 'Grd_Suit', 'Grd_Radio': 'Grd_Suit', 'Grd_Tie': 'Grd_Suit',
    'Cur_Buttons': 'Cur_Suit', 'Cur_Brooch': 'Cur_Suit', 'Doc_Buttons': 'Doc_Suit',
}
O = bpy.data.objects


def rigid_from_garment(ob, gar):
    arm = O[ob.name[:3] + '_Rig']
    deform = {b.name for b in arm.data.bones if b.use_deform}
    gbm = bmesh.new(); gbm.from_mesh(gar.data); gbm.transform(gar.matrix_world); gbm.faces.ensure_lookup_table()
    bvh = BVHTree.FromBMesh(gbm)
    gnames = {g.index: g.name for g in gar.vertex_groups}
    gw = []
    for v in gar.data.vertices:
        d = {gnames[g.group]: g.weight for g in v.groups if gnames.get(g.group) in deform}
        gw.append(max(d, key=d.get) if d else None)
    me = ob.data
    bm = bmesh.new(); bm.from_mesh(me)
    seen, comps = set(), []
    for v in bm.verts:
        if v in seen:
            continue
        st, comp = [v], []
        seen.add(v)
        while st:
            c = st.pop(); comp.append(c)
            for e in c.link_edges:
                o = e.other_vert(c)
                if o not in seen:
                    seen.add(o); st.append(o)
        comps.append([x.index for x in comp])
    bm.free()
    n = 0
    for idx in comps:
        pts = [ob.matrix_world @ me.vertices[i].co for i in idx]
        cen = sum(pts, pts[0] * 0) / len(pts)
        loc, nrm, fi, dist = bvh.find_nearest(cen)
        if loc is None:
            continue
        poly = gar.data.polygons[fi]
        near = min(poly.vertices, key=lambda k: ((gar.matrix_world @ gar.data.vertices[k].co) - cen).length)
        bone = gw[near]
        if not bone:
            continue
        for g in ob.vertex_groups:
            g.remove(idx)
        vg = ob.vertex_groups.get(bone) or ob.vertex_groups.new(name=bone)
        vg.add(idx, 1.0, 'REPLACE')
        n += 1
    gbm.free()
    return n


def rigid_nearest_bone(ob):
    """cada isla conexa se ata rigida al hueso (no dedos) cuyo segmento esta mas cerca de su centroide."""
    arm = O[ob.name[:3] + '_Rig']
    mwa = arm.matrix_world
    skip = ('index', 'thumb', 'middle', 'ring', 'pinky', 'ball', 'Root', 'root')
    seg = {b.name: (mwa @ b.head_local, mwa @ b.tail_local) for b in arm.data.bones if b.use_deform and not any(k in b.name for k in skip)}
    me = ob.data
    bm = bmesh.new(); bm.from_mesh(me)
    seen, comps = set(), []
    for v in bm.verts:
        if v in seen:
            continue
        st, comp = [v], []
        seen.add(v)
        while st:
            c = st.pop(); comp.append(c)
            for e in c.link_edges:
                o = e.other_vert(c)
                if o not in seen:
                    seen.add(o); st.append(o)
        comps.append([x.index for x in comp])
    bm.free()

    def sd(p, a, b):
        ab = b - a
        t = max(0.0, min(1.0, (p - a).dot(ab) / max(ab.length_squared, 1e-12)))
        return (p - (a + ab * t)).length
    n = 0
    for idx in comps:
        pts = [ob.matrix_world @ me.vertices[i].co for i in idx]
        cen = sum(pts, pts[0] * 0) / len(pts)
        bone = min(seg, key=lambda k: sd(cen, *seg[k]))
        for g in ob.vertex_groups:
            g.remove(idx)
        vg = ob.vertex_groups.get(bone) or ob.vertex_groups.new(name=bone)
        vg.add(idx, 1.0, 'REPLACE')
        n += 1
    return n


def run_all4():
    res = {}
    for name, ref in PAIRS.items():
        if name in O and ref in O:
            res[name] = rigid_nearest_bone(O[name])
    print('W4', res)
    return res
