
import bpy, bmesh
from mathutils import Vector

def fix_normals(ob, axis_xy, verbose=True):
    """Orienta las normales hacia fuera por componente conexa: cerradas con recalc; abiertas (tiras, paneles, anillos) por la
    direccion desde el eje del cuerpo (piezas grandes) o desde su propio centro (piezas pequenas)."""
    me = ob.data; mw = ob.matrix_world; nm = mw.to_3x3()
    bm = bmesh.new(); bm.from_mesh(me); bm.faces.ensure_lookup_table()
    seen = set(); comps = []
    for f in bm.faces:
        if f in seen: continue
        st = [f]; seen.add(f); comp = []
        while st:
            c = st.pop(); comp.append(c)
            for e in c.edges:
                for g in e.link_faces:
                    if g not in seen: seen.add(g); st.append(g)
        comps.append(comp)
    flipped = 0
    for comp in comps:
        edges = {e for f in comp for e in f.edges}
        closed = all(len(e.link_faces) == 2 for e in edges)
        if closed:
            before = sum(1 for f in comp if f.normal.length > 0)
            bmesh.ops.recalc_face_normals(bm, faces=comp)
            continue
        xs = [v.co.x for f in comp for v in f.verts]
        wide = (max(xs) - min(xs)) > 0.12
        pts = [mw @ f.calc_center_median() for f in comp]
        cen = sum(pts, Vector()) / len(pts)
        ref = axis_xy if wide else (cen.x, cen.y)
        good = tot = 0
        for f, c in zip(comp, pts):
            n = nm @ f.normal; dx, dy = c.x - ref[0], c.y - ref[1]
            if dx * dx + dy * dy < 1e-8 or n.x * n.x + n.y * n.y < 0.04: continue
            tot += 1; good += 1 if dx * n.x + dy * n.y > 0 else 0
        if tot >= 3 and good / tot < 0.5:
            bmesh.ops.reverse_faces(bm, faces=comp); flipped += 1
    bm.to_mesh(me); bm.free(); me.update()
    if verbose: print(ob.name, 'componentes', len(comps), 'invertidos', flipped)
    return flipped
