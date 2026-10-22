"""Reusable accessories for NPCs. Import and call; every function builds faceted, flat-shaded objects."""
import bpy, bmesh, math
from mathutils import Vector, Matrix
from mathutils.bvhtree import BVHTree


def mat(name, col, metal=0.0, rough=0.6):
    m = bpy.data.materials.get(name) or bpy.data.materials.new(name)
    m.use_nodes = True
    b = next(n for n in m.node_tree.nodes if n.type == 'BSDF_PRINCIPLED')
    b.inputs['Base Color'].default_value = col
    b.inputs['Metallic'].default_value = metal
    b.inputs['Roughness'].default_value = rough
    return m


def _tree(name):
    dg = bpy.context.evaluated_depsgraph_get()
    ev = bpy.data.objects[name].evaluated_get(dg)
    me = ev.to_mesh()
    t = BVHTree.FromPolygons([ev.matrix_world @ v.co for v in me.vertices], [p.vertices[:] for p in me.polygons])
    ev.to_mesh_clear()
    return t


def eye_centres(eyes_name):
    o = bpy.data.objects[eyes_name]
    L_, R_ = [], []
    for v in o.data.vertices:
        (L_ if v.co.x < 0 else R_).append(v.co)
    cl = sum(L_, Vector()) / len(L_)
    cr = sum(R_, Vector()) / len(R_)
    return cl, cr


def round_glasses(eyes_name, out_name, color=(0.04, 0.02, 0.015, 1), radius=0.0225, tube=0.0016, brow_clear=None, shape='round', drop=0.0, out=0.0):
    """Thin round frames in front of the eyes, bridge and two temple arms that stop at the ear. Faceted (14-gon rims)."""
    old = bpy.data.objects.get(out_name)
    if old:
        bpy.data.objects.remove(old)
    cl, cr = eye_centres(eyes_name)
    fy = min(cl.y, cr.y) - 0.017 - out
    parts = []
    cl, cr = cl - Vector((0, 0, drop)), cr - Vector((0, 0, drop))     # frames sit lower: the bridge rests on the nose, brows stay clear

    def curve(name, pts, cyc=False):
        cu = bpy.data.curves.new(name, 'CURVE')
        cu.dimensions = '3D'
        cu.bevel_depth = tube
        cu.bevel_resolution = 1
        cu.resolution_u = 1
        sp = cu.splines.new('POLY')
        sp.points.add(len(pts) - 1)
        for p, v in zip(sp.points, pts):
            p.co = (v.x, v.y, v.z, 1)
        sp.use_cyclic_u = cyc
        o = bpy.data.objects.new(name, cu)
        bpy.context.collection.objects.link(o)
        parts.append(o)

    N = 14
    for c, n in ((cl, 'rl'), (cr, 'rr')):
        if shape == 'rect':
            # librarian frames: wide rounded rectangle (chamfered corners), slightly taller at the outer edge
            w, h, k = radius * 1.12, radius * 0.72, radius * 0.28
            pts = [(-w + k, -h), (w - k, -h), (w, -h + k), (w, h - k), (w - k, h), (-w + k, h), (-w, h - k), (-w, -h + k)]
            curve(n, [Vector((c.x + px, fy, c.z + pz - 0.001)) for px, pz in pts], True)
        elif shape == 'hex':
            curve(n, [Vector((c.x + radius * math.cos(2 * math.pi * i / 6), fy, c.z + radius * math.sin(2 * math.pi * i / 6) - 0.001)) for i in range(6)], True)
        else:
            curve(n, [Vector((c.x + radius * math.cos(2 * math.pi * i / N), fy, c.z + radius * 0.92 * math.sin(2 * math.pi * i / N))) for i in range(N)], True)
    curve('br', [Vector((cl.x + radius, fy, cl.z + 0.004)), Vector((0, fy - 0.004, cl.z + 0.008)), Vector((cr.x - radius, fy, cl.z + 0.004))])
    for s, c in ((-1, cl), (1, cr)):
        curve('tm%d' % s, [Vector((c.x + s * radius, fy, c.z + 0.004)), Vector((s * 0.068, fy + 0.04, c.z + 0.004)), Vector((s * 0.076, fy + 0.085, c.z + 0.002))])
    bpy.ops.object.select_all(action='DESELECT')
    for o in parts:
        o.select_set(True)
    bpy.context.view_layer.objects.active = parts[0]
    bpy.ops.object.convert(target='MESH')
    bpy.ops.object.join()
    g = bpy.context.active_object
    g.name = out_name
    g.data.materials.clear()
    g.data.materials.append(mat(out_name + '_Mat', color))
    for p in g.data.polygons:
        p.use_smooth = False
    return g


def _frame(loc, nor):
    z = nor
    x = Vector((0, 0, 1)).cross(z).normalized()
    y = z.cross(x)
    return Matrix(((x.x, y.x, z.x), (x.y, y.y, z.y), (x.z, y.z, z.z))).to_4x4()


def lanyard_with_card(cloth_name, out_name, strap_col, card_col, accent_col, neck_z=1.40, card_z=1.15, half=0.075):
    """V-shaped flat strap hanging on the chest (rays from the front onto `cloth_name`) and an ID card at its tip."""
    old = bpy.data.objects.get(out_name)
    if old:
        bpy.data.objects.remove(old)
    t = _tree(cloth_name)
    bm = bmesh.new()

    def front(x, z, off):
        h = t.ray_cast(Vector((x, -0.6, z)), Vector((0, 1, 0)))
        return (None, None) if h[0] is None else (h[0] + h[1].normalized() * off, h[1].normalized())

    for sx in (-1, 1):
        rows = []
        N = 10
        for i in range(N + 1):
            s = i / N
            x = sx * half * (1 - s) ** 1.0
            z = neck_z - (neck_z - card_z - 0.012) * s
            p, n = front(x, z, 0.0035)
            if p is None:
                continue
            tang = Vector((-sx * half, 0, -(neck_z - card_z))).normalized()
            side = tang.cross(n).normalized() * 0.0085
            rows.append((p + side, p - side))
        for a, b in zip(rows, rows[1:]):
            quad = [bm.verts.new(v) for v in (a[0], a[1], b[1], b[0])]
            for order in (quad, quad[::-1]):          # both sides: open strips are culled from behind in Unity otherwise
                f = bm.faces.new(order) if order is quad else bm.faces.new([bm.verts.new(v.co) for v in order])
                f.material_index = 0
                f.smooth = False
    # the card
    p, n = front(0, card_z, 0.0045)
    M = _frame(p, n)
    def box(c, sx_, sy_, sz_, mi):
        r = bmesh.ops.create_cube(bm, size=1.0)
        for v in r['verts']:
            v.co = M @ (Vector((v.co.x * sx_, v.co.y * sy_, v.co.z * sz_)) + c) + p
        for f in {f for v in r['verts'] for f in v.link_faces}:
            f.material_index = mi
            f.smooth = False
    box(Vector((0, 0, 0)), 0.056, 0.086, 0.003, 1)            # card
    box(Vector((0, 0.030, 0.0018)), 0.056, 0.020, 0.0008, 2)   # coloured header band
    box(Vector((-0.013, -0.004, 0.0018)), 0.020, 0.024, 0.0008, 3)   # photo block
    for k in range(2):
        box(Vector((0.012, -0.002 - k * 0.008, 0.0018)), 0.022, 0.0028, 0.0008, 3)
    box(Vector((0, 0.047, 0.0)), 0.014, 0.008, 0.003, 4)       # clip
    me = bpy.data.meshes.new(out_name)
    bm.to_mesh(me)
    bm.free()
    o = bpy.data.objects.new(out_name, me)
    bpy.context.collection.objects.link(o)
    for m in (mat(out_name + '_Strap', strap_col), mat(out_name + '_Card', card_col), mat(out_name + '_Band', accent_col), mat(out_name + '_Text', (0.08, 0.07, 0.06, 1)), mat(out_name + '_Clip', (0.8, 0.62, 0.2, 1), 1.0, 0.35)):
        me.materials.append(m)
    return o


def round_brooch(cloth_name, out_name, x, z, radius=0.013, base_col=(0.8, 0.62, 0.2, 1), stone_col=(0.05, 0.3, 0.22, 1)):
    """Small faceted gold disc brooch with a centre stone, lying on the cloth surface."""
    old = bpy.data.objects.get(out_name)
    if old:
        bpy.data.objects.remove(old)
    t = _tree(cloth_name)
    h = t.ray_cast(Vector((x, -0.6, z)), Vector((0, 1, 0)))
    p, n = h[0], h[1].normalized()
    M = _frame(p, n)
    bm = bmesh.new()
    r = bmesh.ops.create_cone(bm, cap_ends=True, segments=10, radius1=radius, radius2=radius * 0.9, depth=0.0025, matrix=Matrix.Translation((0, 0, 0.0012)))
    for f in bm.faces:
        f.material_index = 0
    r2 = bmesh.ops.create_cone(bm, cap_ends=True, segments=6, radius1=radius * 0.55, radius2=radius * 0.35, depth=0.003, matrix=Matrix.Translation((0, 0, 0.0035)))
    for f in {f for v in r2['verts'] for f in v.link_faces}:
        f.material_index = 1
    for v in bm.verts:
        v.co = M @ v.co + p + n * 0.0008
    for f in bm.faces:
        f.smooth = False
    me = bpy.data.meshes.new(out_name)
    bm.to_mesh(me)
    bm.free()
    o = bpy.data.objects.new(out_name, me)
    bpy.context.collection.objects.link(o)
    me.materials.append(mat(out_name + '_Gold', base_col, 1.0, 0.35))
    me.materials.append(mat(out_name + '_Stone', stone_col, 0.0, 0.3))
    return o


def fitted_glasses(eyes_name, out_name, skin_name, hair_name, color=(0.08, 0.03, 0.03, 1), half_w=0.0215, half_h=0.0145, tube=0.0028, shape='rect', drop=0.004):
    """Glasses whose rims follow the face surface: every point is ray-snapped to the front of skin/hair and then pushed out of both, so nothing clips.
    Rims are centred on the eyes (dropped a little so the brows stay above the frame); temples run back along the head and stay outside skin and hair."""
    old = bpy.data.objects.get(out_name)
    if old:
        bpy.data.objects.remove(old)
    cl, cr = eye_centres(eyes_name)
    skin, hair = _tree(skin_name), _tree(hair_name)
    clear = tube * 1.2 + 0.0025

    def outward(t, probe):
        loc, nor, _, _ = t.find_nearest(probe)
        return 1.0 if (probe - loc).dot(nor) > 0 else -1.0

    top = Vector((0, 0, max(v.co.z for v in bpy.data.objects[hair_name].data.vertices) + 0.05))
    sgn = {id(skin): outward(skin, top), id(hair): outward(hair, top)}

    def front(x, z):
        ys = []
        for t in (skin, hair):
            h = t.ray_cast(Vector((x, -0.6, z)), Vector((0, 1, 0)))
            if h[0] is not None:
                ys.append(h[0].y)
        return (min(ys) if ys else cl.y) - clear

    def push(p):
        for _ in range(3):
            for t in (skin, hair):
                loc, nor, _, d = t.find_nearest(p)
                if loc is None or d > 0.05:
                    continue
                n = nor * sgn[id(t)]
                if (p - loc).dot(n) < clear:
                    p = loc + n * clear
        return p

    def dens(pts, n=4, closed=True):
        out = []
        m = len(pts)
        for i in range(m if closed else m - 1):
            a, b = pts[i], pts[(i + 1) % m]
            for k in range(n):
                out.append(a.lerp(b, k / n))
        if not closed:
            out.append(pts[-1])
        return out

    parts = []

    def curve(name, pts, cyc=False):
        cu = bpy.data.curves.new(name, 'CURVE')
        cu.dimensions = '3D'
        cu.bevel_depth = tube
        cu.bevel_resolution = 1
        cu.resolution_u = 1
        sp = cu.splines.new('POLY')
        sp.points.add(len(pts) - 1)
        for q, v in zip(sp.points, pts):
            q.co = (v.x, v.y, v.z, 1)
        sp.use_cyclic_u = cyc
        o = bpy.data.objects.new(name, cu)
        bpy.context.collection.objects.link(o)
        parts.append(o)

    w, h, k = half_w, half_h, half_h * 0.36
    if shape == 'rect':
        outline = [(-w + k, -h), (w - k, -h), (w, -h + k), (w, h - k), (w - k, h), (-w + k, h), (-w, h - k), (-w, -h + k)]
    else:
        outline = [(w * math.cos(2 * math.pi * i / 14), h * math.sin(2 * math.pi * i / 14)) for i in range(14)]
    # rigid frame: one plane in front of the cheekbones, brows and bangs (real glasses are rigid), small gap at the eyes is the price
    rim_pts, flats = [], []
    for c, n in ((cl, 'rl'), (cr, 'rr')):
        zc = c.z - drop
        flat = [Vector((c.x + px, 0, zc + pz)) for px, pz in outline]
        flats.append(dens(flat, 4, True))
    xl, xr = cl.x + w, cr.x - w
    zb = (cl.z + cr.z) / 2 - drop + h * 0.55
    bpts = [Vector((xl + (xr - xl) * i / 6, 0, zb + 0.004 * math.sin(math.pi * i / 6))) for i in range(7)]
    yp = min(front(q.x, q.z) for q in sum(flats, []) + bpts)
    for (c, n), fl in zip(((cl, 'rl'), (cr, 'rr')), flats):
        curve(n, [Vector((q.x, yp, q.z)) for q in fl], True)
    curve('br', [Vector((q.x, yp, q.z)) for q in bpts])
    # temples: straight back from the outer rim corner to just in front of the ear, then fitted outside skin and hair
    for s, c in ((-1, cl), (1, cr)):
        zc = c.z - drop + h * 0.55
        a = Vector((c.x + s * w, yp, zc))
        b = Vector((s * 0.078, a.y + 0.075, zc - 0.002))
        line = [a.lerp(b, i / 12) for i in range(13)]
        curve('tm%d' % s, [push(q) for q in line])
    bpy.ops.object.select_all(action='DESELECT')
    for o in parts:
        o.select_set(True)
    bpy.context.view_layer.objects.active = parts[0]
    bpy.ops.object.convert(target='MESH')
    bpy.ops.object.join()
    g = bpy.context.active_object
    g.name = out_name
    g.data.materials.clear()
    g.data.materials.append(mat(out_name + '_Mat', color))
    for p_ in g.data.polygons:
        p_.use_smooth = False
    return g


def beauty_mark(skin_name, base_name, out_name, side=1, dx=0.021, dz=0.0035, radius=0.0024, color=(0.035, 0.02, 0.016, 1)):
    """Small dark mole on the skin, placed relative to the upper lip (top of the MPFB 'lips' group), on the `side` cheek; ray-snapped to the skin surface."""
    old = bpy.data.objects.get(out_name)
    if old:
        bpy.data.objects.remove(old)
    from mathutils.kdtree import KDTree
    base = bpy.data.objects[base_name]
    low = bpy.data.objects[skin_name]
    vg = base.vertex_groups['lips']
    import numpy as np
    nv = len(base.data.vertices)
    basis = np.empty(nv * 3, dtype=np.float32)
    base.data.vertices.foreach_get('co', basis)
    shaped = basis.copy()                    # base.data coordinates are the unshaped basis: mix the active shape keys (what the low-poly body was built from)
    if base.data.shape_keys:
        kb = base.data.shape_keys.key_blocks
        b0 = np.empty(nv * 3, dtype=np.float32)
        kb[0].data.foreach_get('co', b0)
        for k in kb[1:]:
            if abs(k.value) > 1e-6:
                a = np.empty(nv * 3, dtype=np.float32)
                k.data.foreach_get('co', a)
                shaped += (a - b0) * k.value
    shaped = shaped.reshape(-1, 3)
    kd = KDTree(nv)
    for i in range(nv):
        kd.insert(Vector(shaped[i]), i)
    kd.balance()
    pts = []
    for v in low.data.vertices:          # same mapping skin_makeup uses: low-poly vertex -> nearest MPFB vertex -> lips weight
        _, i, d = kd.find(v.co)
        if d < 0.01:
            try:
                if vg.weight(i) > 0.5:
                    pts.append(v.co.copy())
            except RuntimeError:
                pass
    zt = max(p.z for p in pts)
    cx = sum(p.x for p in pts) / len(pts)
    t = _tree(skin_name)
    x = cx + side * dx
    h = t.ray_cast(Vector((x, -0.6, zt + dz)), Vector((0, 1, 0)))
    p, n = h[0], h[1].normalized()
    if n.y > 0:
        n = -n
    zax = n
    xax = Vector((0, 0, 1)).cross(zax).normalized()
    yax = zax.cross(xax)
    R = Matrix(((xax.x, yax.x, zax.x), (xax.y, yax.y, zax.y), (xax.z, yax.z, zax.z)))
    bm = bmesh.new()
    r = bmesh.ops.create_cone(bm, cap_ends=True, segments=6, radius1=radius, radius2=radius * 0.85, depth=0.0008)
    for v in r['verts']:
        v.co = p + n * 0.0005 + R @ v.co
    for f in bm.faces:
        f.smooth = False
    me = bpy.data.meshes.new(out_name)
    bm.to_mesh(me)
    bm.free()
    o = bpy.data.objects.new(out_name, me)
    bpy.context.collection.objects.link(o)
    o.data.materials.append(mat(out_name + '_Mat', color))
    return o


def _lip_points(skin_name, base_name, indices=False, thr=0.5):
    """Low-poly skin vertices that belong to the MPFB 'lips' group (base shape-key mix -> nearest mapping)."""
    from mathutils.kdtree import KDTree
    import numpy as np
    base = bpy.data.objects[base_name]
    low = bpy.data.objects[skin_name]
    vg = base.vertex_groups['lips']
    nv = len(base.data.vertices)
    basis = np.empty(nv * 3, dtype=np.float32)
    base.data.vertices.foreach_get('co', basis)
    shaped = basis.copy()
    if base.data.shape_keys:
        kb = base.data.shape_keys.key_blocks
        b0 = np.empty(nv * 3, dtype=np.float32)
        kb[0].data.foreach_get('co', b0)
        for k in kb[1:]:
            if abs(k.value) > 1e-6:
                arr = np.empty(nv * 3, dtype=np.float32)
                k.data.foreach_get('co', arr)
                shaped += (arr - b0) * k.value
    shaped = shaped.reshape(-1, 3)
    kd = KDTree(nv)
    for i in range(nv):
        kd.insert(Vector(shaped[i]), i)
    kd.balance()
    pts = []
    for v in low.data.vertices:
        _, i, d = kd.find(v.co)
        if d < 0.01:
            try:
                if vg.weight(i) > thr:
                    pts.append(v.index if indices else v.co.copy())
            except RuntimeError:
                pass
    return pts


def _disc(bm, t, x, z, r, depth, mi=0, off=0.0004):
    h = t.ray_cast(Vector((x, -0.6, z)), Vector((0, 1, 0)))
    if h[0] is None:
        return False
    p, n = h[0], h[1].normalized()
    if n.y > 0:
        n = -n
    xax = Vector((0, 0, 1)).cross(n).normalized()
    yax = n.cross(xax)
    R = Matrix(((xax.x, yax.x, n.x), (xax.y, yax.y, n.y), (xax.z, yax.z, n.z)))
    c = bmesh.ops.create_cone(bm, cap_ends=True, segments=6, radius1=r, radius2=r * 0.85, depth=depth)
    for v in c['verts']:
        v.co = p + n * off + R @ v.co
    return True


def freckles(skin_name, eyes_name, out_name, count=34, seed=7, color=(0.36, 0.21, 0.14, 1)):
    """Scattered freckles on the nose bridge and cheeks below the eyes: tiny flat discs ray-snapped to the skin (vertex colours are too coarse for 2 mm dots)."""
    import random
    old = bpy.data.objects.get(out_name)
    if old:
        bpy.data.objects.remove(old)
    rnd = random.Random(seed)
    cl, cr = eye_centres(eyes_name)
    t = _tree(skin_name)
    ez = (cl.z + cr.z) / 2
    bm = bmesh.new()
    placed = []
    tries = 0
    while len(placed) < count and tries < 800:
        tries += 1
        if rnd.random() < 0.28:                                   # nose bridge
            x, z = rnd.uniform(-0.0075, 0.0075), ez - rnd.uniform(0.006, 0.026)
        else:                                                      # cheeks
            x, z = rnd.choice((-1, 1)) * rnd.uniform(0.012, 0.052), ez - rnd.uniform(0.014, 0.046)
        if any((x - a) ** 2 + (z - b) ** 2 < 0.0052 ** 2 for a, b in placed):
            continue
        if _disc(bm, t, x, z, rnd.uniform(0.0010, 0.0016), 0.0005):
            placed.append((x, z))
    for f in bm.faces:
        f.smooth = False
    me = bpy.data.meshes.new(out_name)
    bm.to_mesh(me)
    bm.free()
    o = bpy.data.objects.new(out_name, me)
    bpy.context.collection.objects.link(o)
    o.data.materials.append(mat(out_name + '_Mat', color))
    return o


def lip_scar(skin_name, base_name, out_name, dx=0.007, color=(0.84, 0.60, 0.56, 1)):
    """Thin pale scar crossing the lower lip (slightly slanted), ray-snapped to the skin."""
    old = bpy.data.objects.get(out_name)
    if old:
        bpy.data.objects.remove(old)
    pts = _lip_points(skin_name, base_name)
    zmin, zmax = min(p.z for p in pts), max(p.z for p in pts)
    cx = sum(p.x for p in pts) / len(pts)
    t = _tree(skin_name)
    zmid = zmin + (zmax - zmin) * 0.50
    path = [(cx + dx + 0.0040, zmid + 0.0020), (cx + dx + 0.0008, zmid - (zmid - zmin) * 0.45), (cx + dx - 0.0030, zmin + (zmid - zmin) * 0.08 - 0.0035)]
    dense = []
    for (xa_, za_), (xb_, zb_) in zip(path, path[1:]):          # follow the lip relief: many short segments
        for k in range(6):
            dense.append((xa_ + (xb_ - xa_) * k / 6, za_ + (zb_ - za_) * k / 6))
    dense.append(path[-1])
    path = dense
    bm = bmesh.new()
    L, Rr = [], []
    for i, (x, z) in enumerate(path):
        xa, za = path[max(i - 1, 0)]
        xb, zb = path[min(i + 1, len(path) - 1)]
        tx, tz = xb - xa, zb - za
        ln = math.hypot(tx, tz) or 1.0
        px, pz = -tz / ln * 0.0011, tx / ln * 0.0011
        for sd, lst in ((1, L), (-1, Rr)):
            h = t.ray_cast(Vector((x + sd * px, -0.6, z + sd * pz)), Vector((0, 1, 0)))
            n = h[1].normalized()
            if n.y > 0:
                n = -n
            lst.append(h[0] + n * 0.0007)
    for i in range(len(path) - 1):
        f = bm.faces.new([bm.verts.new(v) for v in (L[i], Rr[i], Rr[i + 1], L[i + 1])])
        f.smooth = False
    me = bpy.data.meshes.new(out_name)
    bm.to_mesh(me)
    bm.free()
    o = bpy.data.objects.new(out_name, me)
    bpy.context.collection.objects.link(o)
    o.data.materials.append(mat(out_name + '_Mat', color))
    return o


def lipstick(skin_name, base_name, out_name, color=(0.62, 0.035, 0.05, 1), lift=0.0007, thr=0.5):
    """Lipstick as a thin copy of the lip faces of the skin mesh (faces whose vertices all belong to the MPFB lips group), lifted a hair off the skin:
    crisp edges instead of a vertex-colour halo."""
    old = bpy.data.objects.get(out_name)
    if old:
        bpy.data.objects.remove(old)
    idx = set(_lip_points(skin_name, base_name, indices=True, thr=thr))
    low = bpy.data.objects[skin_name]
    me = low.data
    bm = bmesh.new()
    vm = {}
    for p_ in me.polygons:
        if all(i in idx for i in p_.vertices):
            vs = []
            for i in p_.vertices:
                if i not in vm:
                    vm[i] = bm.verts.new(me.vertices[i].co + me.vertices[i].normal * lift)
                vs.append(vm[i])
            try:
                f = bm.faces.new(vs)
            except ValueError:
                continue
            f.smooth = False
    me2 = bpy.data.meshes.new(out_name)
    bm.to_mesh(me2)
    bm.free()
    o = bpy.data.objects.new(out_name, me2)
    bpy.context.collection.objects.link(o)
    o.data.materials.append(mat(out_name + '_Mat', color))
    return o


def wart(skin_name, out_name, eyes_name=None, dx=0.017, dz=0.004, radius=0.0036, color=(0.33, 0.17, 0.13, 1)):
    """Small wart on the side of the nose: a faceted bump ray-snapped to the skin, a little darker than the skin. Position is relative to the nose tip."""
    old = bpy.data.objects.get(out_name)
    if old:
        bpy.data.objects.remove(old)
    low = bpy.data.objects[skin_name]
    cl_, cr_ = eye_centres(eyes_name)
    ez_ = (cl_.z + cr_.z) / 2
    cand = [v.co for v in low.data.vertices if abs(v.co.x) < 0.02 and ez_ - 0.075 < v.co.z < ez_ - 0.01]
    tip = min(cand, key=lambda c: c.y)                  # nose tip = most forward point near the centre line of the head
    t = _tree(skin_name)
    h = t.ray_cast(Vector((tip.x + dx, -0.6, tip.z + dz)), Vector((0, 1, 0)))
    p, n = h[0], h[1].normalized()
    if n.y > 0:
        n = -n
    bm = bmesh.new()
    r = bmesh.ops.create_icosphere(bm, subdivisions=1, radius=radius)
    for v in r['verts']:
        v.co = p + n * radius * 0.35 + v.co
    for f in bm.faces:
        f.smooth = False
    me = bpy.data.meshes.new(out_name)
    bm.to_mesh(me)
    bm.free()
    o = bpy.data.objects.new(out_name, me)
    bpy.context.collection.objects.link(o)
    o.data.materials.append(mat(out_name + '_Mat', color))
    return o
