"""Faceted low-poly game mesh from an MPFB basemesh. Run inside Blender (MCP).
Head and body are decimated separately (head denser for readable faces), then
the neck boundary loops are bridged so the mesh is watertight and flat shaded.
"""
import bpy
import bmesh

NECK_Z = 1.37          # split height for a 1.65 m character
HEAD_RATIO = 0.25
BODY_RATIO = 0.10


def _part(src_me, name, keep):
    bm = bmesh.new()
    bm.from_mesh(src_me)
    bm.faces.ensure_lookup_table()
    bmesh.ops.delete(bm, geom=[f for f in bm.faces if not keep(f)], context='FACES')
    me = bpy.data.meshes.new(name)
    bm.to_mesh(me)
    bm.free()
    return me


def _decimated(me, ratio):
    o = bpy.data.objects.new("_tmp", me)
    bpy.context.collection.objects.link(o)
    m = o.modifiers.new("d", 'DECIMATE')
    m.ratio = ratio
    m.use_symmetry = True
    out = bpy.data.meshes.new_from_object(o.evaluated_get(bpy.context.evaluated_depsgraph_get()))
    bpy.data.objects.remove(o)
    return out


def build(basemesh_name, out_name, neck_z=NECK_Z):
    base = bpy.data.objects[basemesh_name]
    ds = bpy.context.evaluated_depsgraph_get()
    full = bpy.data.meshes.new_from_object(base.evaluated_get(ds))  # helpers masked, targets baked
    head = _decimated(_part(full, "h", lambda f: f.calc_center_median().z >= neck_z), HEAD_RATIO)
    body = _decimated(_part(full, "b", lambda f: f.calc_center_median().z < neck_z), BODY_RATIO)
    bm = bmesh.new()
    bm.from_mesh(head)
    bm.from_mesh(body)
    bmesh.ops.bridge_loops(bm, edges=[e for e in bm.edges if e.is_boundary])
    bmesh.ops.triangulate(bm, faces=bm.faces[:])
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    old = bpy.data.objects.get(out_name)
    if old:
        bpy.data.objects.remove(old)
    me = bpy.data.meshes.new(out_name)
    bm.to_mesh(me)
    bm.free()
    for p in me.polygons:
        p.use_smooth = False
    o = bpy.data.objects.new(out_name, me)
    bpy.context.collection.objects.link(o)
    return o


def lowpoly_object(src_name, out_name, target_tris, symmetric=True):
    """Faceted low-poly copy of a (possibly very dense) fitted MPFB asset: dissolve flat areas, then collapse-decimate to ~target_tris.
    Keeps the source object untouched. Flat shaded. Run AFTER the MPFB mask modifiers on the base have been switched off."""
    src = bpy.data.objects[src_name]
    ds = bpy.context.evaluated_depsgraph_get()
    me = bpy.data.meshes.new_from_object(src.evaluated_get(ds))
    me.transform(src.matrix_world)
    bm = bmesh.new()
    bm.from_mesh(me)
    bmesh.ops.dissolve_limit(bm, angle_limit=0.035, verts=bm.verts, edges=bm.edges)
    bmesh.ops.triangulate(bm, faces=bm.faces[:])
    tris = len(bm.faces)
    bm.to_mesh(me)
    bm.free()
    old = bpy.data.objects.get(out_name)
    if old:
        bpy.data.objects.remove(old)
    o = bpy.data.objects.new(out_name, me)
    bpy.context.collection.objects.link(o)
    m = o.modifiers.new('d', 'DECIMATE')
    m.ratio = min(1.0, target_tris / max(tris, 1))
    m.use_symmetry = symmetric
    out = bpy.data.meshes.new_from_object(o.evaluated_get(bpy.context.evaluated_depsgraph_get()))
    o.modifiers.clear()
    o.data = out
    for p in out.polygons:
        p.use_smooth = False
    return o


def push_out(outer_name, inner_names, clearance=0.003, iterations=8, reach=None):
    """Push each vertex of `outer` out along the nearest inner-surface normal until it clears the inner layers. No global scaling."""
    from mathutils.bvhtree import BVHTree
    outer = bpy.data.objects[outer_name]
    total = 0
    for _ in range(iterations):
        dg = bpy.context.evaluated_depsgraph_get()
        trees = []
        for n in inner_names:
            ev = bpy.data.objects[n].evaluated_get(dg)
            me = ev.to_mesh()
            trees.append(BVHTree.FromPolygons([ev.matrix_world @ v.co for v in me.vertices], [p.vertices[:] for p in me.polygons]))
            ev.to_mesh_clear()
        changed = 0
        for v in outer.data.vertices:
            for t in trees:
                loc, nor, idx, dist = t.find_nearest(v.co)
                if loc is None:
                    continue
                side = (v.co - loc).dot(nor)
                if side < clearance and dist < (reach or clearance * 4):
                    v.co += nor * (clearance - side)
                    changed += 1
        total += changed
        outer.data.update()
        if not changed:
            break
    return total


def trim_hidden_body(body_name, cloth_names, keep=lambda c: False, margin_rings=1):
    """Delete body faces completely covered by clothes (ray test along the normal), keeping a one-ring margin and anything `keep(centre)` says."""
    from mathutils.bvhtree import BVHTree
    body = bpy.data.objects[body_name]
    dg = bpy.context.evaluated_depsgraph_get()
    trees = []
    for n in cloth_names:
        ev = bpy.data.objects[n].evaluated_get(dg)
        me = ev.to_mesh()
        trees.append(BVHTree.FromPolygons([ev.matrix_world @ v.co for v in me.vertices], [p.vertices[:] for p in me.polygons]))
        ev.to_mesh_clear()
    bm = bmesh.new()
    bm.from_mesh(body.data)
    bm.normal_update()

    def covered(v):
        n = v.normal
        if n.length < 1e-6:
            return False
        o = v.co - n * 0.04                                 # start inside the body: also catches skin poking through big decimated cloth faces
        return any(t.ray_cast(o, n, 0.16)[0] is not None for t in trees)

    cv = {v: covered(v) for v in bm.verts}
    safe = {v: cv[v] and all(cv[e.other_vert(v)] for e in v.link_edges) for v in bm.verts}
    dele = [f for f in bm.faces if all(safe[v] for v in f.verts) and not keep(f.calc_center_median())]
    bmesh.ops.delete(bm, geom=dele, context='FACES')
    bmesh.ops.delete(bm, geom=[v for v in bm.verts if not v.link_faces], context='VERTS')
    bm.faces.ensure_lookup_table()
    seen = set()
    small = []
    for f in bm.faces:                                       # drop tiny loose fragments left by the trim
        if f.index in seen:
            continue
        st = [f]
        comp = []
        seen.add(f.index)
        while st:
            x = st.pop()
            comp.append(x)
            for e in x.edges:
                for nf in e.link_faces:
                    if nf.index not in seen:
                        seen.add(nf.index)
                        st.append(nf)
        if len(comp) < 30:
            small += comp
    bmesh.ops.delete(bm, geom=small, context='FACES')
    bmesh.ops.delete(bm, geom=[v for v in bm.verts if not v.link_faces], context='VERTS')
    bm.to_mesh(body.data)
    bm.free()
    return len(dele)


def fix_poke(body_name, cloth_name, iterations=8, margin=0.004, reach=0.06):
    """Body vertices that stick out through large decimated cloth faces: push the nearest cloth face's corners outward until they cover them."""
    from mathutils.bvhtree import BVHTree
    body = bpy.data.objects[body_name]
    cloth = bpy.data.objects[cloth_name]
    total = 0
    for _ in range(iterations):
        dg = bpy.context.evaluated_depsgraph_get()
        ev = cloth.evaluated_get(dg)
        me = ev.to_mesh()
        verts = [ev.matrix_world @ v.co for v in me.vertices]
        polys = [p.vertices[:] for p in me.polygons]
        tree = BVHTree.FromPolygons(verts, polys)
        ev.to_mesh_clear()
        bme = bmesh.new()
        bme.from_mesh(body.data)
        bme.normal_update()
        changed = 0
        for v in bme.verts:
            loc, nor, idx, dist = tree.find_nearest(v.co, reach)
            if loc is None:
                continue
            nn = nor.normalized()
            out = (v.co - loc).dot(nn)                    # >0: the skin vertex is outside the cloth face
            if out > -margin:
                push = v.normal.normalized() * (out + margin)
                for vi in polys[idx]:
                    cloth.data.vertices[vi].co += push
                changed += 1
        bme.free()
        total += changed
        cloth.data.update()
        if not changed:
            break
    return total


def extend_hem(name, dz, near_x=0.3):
    """Extrude the lowest torso boundary ring of a garment downward by dz (an untucked hem that overlaps the trousers instead of leaving a belly strip)."""
    o = bpy.data.objects[name]
    bm = bmesh.new()
    bm.from_mesh(o.data)
    bs = [e for e in bm.edges if e.is_boundary and abs((e.verts[0].co.x + e.verts[1].co.x) / 2) < near_x]
    if not bs:
        return 0
    zmin = min(min(v.co.z for v in e.verts) for e in bs)
    low = [e for e in bs if min(v.co.z for v in e.verts) < zmin + 0.06 and (e.verts[0].co.z + e.verts[1].co.z) / 2 < zmin + 0.08]
    ext = bmesh.ops.extrude_edge_only(bm, edges=low)
    for v in [g for g in ext['geom'] if isinstance(g, bmesh.types.BMVert)]:
        v.co.z -= dz
    bm.normal_update()
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    for f in bm.faces:
        f.smooth = False
    bm.to_mesh(o.data)
    bm.free()
    return len(low)
