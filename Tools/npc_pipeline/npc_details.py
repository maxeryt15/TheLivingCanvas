"""Detail helpers shared by every NPC: colour regions, hair tones, eyes, skin make-up, buttons, belt, watch, lanyard, shoe soles.
Everything is built in WORLD space on the final low-poly meshes (rest pose, objects at identity), flat shaded.
"""
import bpy, bmesh, math
from mathutils import Vector, Matrix
from mathutils.bvhtree import BVHTree


# ---------------------------------------------------------------------------------------------- materials / colour regions
def mat(name, col, metal=0.0, rough=0.7):
    col = tuple(col) + ((1.0,) if len(col) == 3 else ())
    m = bpy.data.materials.get(name) or bpy.data.materials.new(name)
    m.use_nodes = True
    b = next(n for n in m.node_tree.nodes if n.type == 'BSDF_PRINCIPLED')
    b.inputs['Base Color'].default_value = col
    b.inputs['Metallic'].default_value = metal
    b.inputs['Roughness'].default_value = rough
    return m


def region_materials(o, prefix, default, rules, leg_rule=None):
    """default=(name,rgb); rules=[(name,rgb,pred(centre,normal)->bool)] later rules override earlier ones. Face material = first match from the end."""
    me = o.data
    me.materials.clear()
    me.materials.append(mat(prefix + '_' + default[0], default[1]))
    for r in rules:
        me.materials.append(mat(prefix + '_' + r[0], r[1]))
    for p in me.polygons:
        idx = 0
        for i, r in enumerate(rules):
            if r[2](p.center, p.normal):
                idx = i + 1
        p.material_index = idx
        p.use_smooth = False
    if leg_rule:     # the shell that reaches the ankles (trousers) keeps the trouser material even where it is above the cut plane, so no coat colour shows through gaps under the hem
        names = [m.name for m in me.materials]
        k = names.index(prefix + '_' + leg_rule)
        bm = bmesh.new(); bm.from_mesh(me); bm.faces.ensure_lookup_table()
        seen = set()
        for f0 in bm.faces:
            if f0.index in seen:
                continue
            st = [f0]; seen.add(f0.index); comp = []
            while st:
                a = st.pop(); comp.append(a)
                for e in a.edges:
                    for b in e.link_faces:
                        if b.index not in seen:
                            seen.add(b.index); st.append(b)
            if min(v.co.z for f in comp for v in f.verts) < 0.2:
                for f in comp:
                    if me.materials[me.polygons[f.index].material_index].name.endswith('_Tweed'):
                        me.polygons[f.index].material_index = k
        bm.free()


def hair_tones(o, prefix, colors, bands=7):
    """Flowing bands of 3 close tones around the head axis (low-poly strand look, easy to repaint)."""
    me = o.data
    me.materials.clear()
    for i, c in enumerate(colors):
        me.materials.append(mat('%s_Hair%d' % (prefix, i), c, 0.0, 0.9))
    pat = [1, 0, 1, 2, 1, 1, 0, 2] if len(colors) > 2 else [0, 1]
    for p in me.polygons:
        c = p.center
        th = math.atan2(c.x, -(c.y + 0.07))
        b = math.floor(th * bands * 0.5 + 0.8 * math.sin(c.z * 9.0 + th))
        p.material_index = pat[b % len(pat)]
        p.use_smooth = False


def make_eyes(base_name, prefix, iris, white=(0.80, 0.77, 0.72), pupil=(0.015, 0.015, 0.015), iris2=None, blind=None):
    """Low-poly eyes copied from the MPFB asset already fitted to the base; faces classified into white / iris / pupil."""
    src = [o for o in bpy.data.objects if o.name.startswith(base_name + '.') and 'low-poly' in o.name][0]
    src.hide_set(False)
    me = bpy.data.meshes.new_from_object(src.evaluated_get(bpy.context.evaluated_depsgraph_get()))
    me.transform(src.matrix_world)
    src.hide_set(True)
    old = bpy.data.objects.get(prefix + '_Eyes')
    if old:
        bpy.data.objects.remove(old)
    o = bpy.data.objects.new(prefix + '_Eyes', me)
    bpy.context.collection.objects.link(o)
    me.materials.clear()
    for n, c, r in (('EyeWhite', white, 0.35), ('EyeIris', iris, 0.3), ('EyePupil', pupil, 0.3)):
        me.materials.append(mat('%s_%s' % (prefix, n), c, 0.0, r))
    if blind is not None:      # blind eye: milky white, no iris or pupil
        me.materials.append(mat('%s_EyeBlind' % prefix, (0.86, 0.86, 0.85), 0.0, 0.5))
    if iris2 is not None:      # heterochromia: the eye on the +x side gets its own iris colour
        me.materials.append(mat('%s_EyeIris2' % prefix, iris2, 0.0, 0.3))
    bm = bmesh.new()
    bm.from_mesh(me)
    cen = {}
    for v in bm.verts:
        cen.setdefault(v.co.x < 0, []).append(v.co)
    cen = {k: sum(v, Vector()) / len(v) for k, v in cen.items()}
    for f in bm.faces:
        cc = f.calc_center_median()
        d = (cc - cen[cc.x < 0]).normalized().dot(Vector((0, -1, 0)))
        f.material_index = 2 if d > 0.88 else (1 if d > 0.62 else 0)
        if iris2 is not None and f.material_index == 1 and cc.x > 0:
            f.material_index = 3
        if blind is not None and (cc.x > 0) == (blind > 0) and f.material_index in (1, 2):
            f.material_index = len(me.materials) - 1 if iris2 is None else len(me.materials) - 1
        f.smooth = False
    bm.to_mesh(me)
    bm.free()
    return o


def make_brows(base_name, prefix, color):
    src = [o for o in bpy.data.objects if o.name.startswith(base_name + '.') and 'eyebrow' in o.name][0]
    src.hide_set(False)
    me = bpy.data.meshes.new_from_object(src.evaluated_get(bpy.context.evaluated_depsgraph_get()))
    me.transform(src.matrix_world)
    src.hide_set(True)
    old = bpy.data.objects.get(prefix + '_Brows')
    if old:
        bpy.data.objects.remove(old)
    o = bpy.data.objects.new(prefix + '_Brows', me)
    bpy.context.collection.objects.link(o)
    me.materials.clear()
    me.materials.append(mat(prefix + '_Brows', color, 0.0, 0.9))
    for p in me.polygons:
        p.material_index = 0
        p.use_smooth = False
    return o


def skin_makeup(low_name, base_name, prefix, skin, lips, blush=None, shadow=None, eye_centres=None, lip_strength=1.0, scar=None):
    """Vertex colours 'Col' on the skin mesh (lips from MPFB's lips group, soft cheek blush, eyelid shadow), skin material reads them."""
    from mathutils.kdtree import KDTree
    low = bpy.data.objects[low_name]
    base = bpy.data.objects[base_name]
    me = low.data
    if 'Col' in me.color_attributes:
        me.color_attributes.remove(me.color_attributes['Col'])
    ca = me.color_attributes.new('Col', 'FLOAT_COLOR', 'POINT')
    import numpy as np
    nv_ = len(base.data.vertices)
    basis_ = np.empty(nv_ * 3, dtype=np.float32)
    base.data.vertices.foreach_get('co', basis_)
    shaped_ = basis_.copy()          # base.data holds the UNSHAPED coordinates: mix the shape keys, or every lookup lands on the wrong spot of the face
    if base.data.shape_keys:
        kb_ = base.data.shape_keys.key_blocks
        b0_ = np.empty(nv_ * 3, dtype=np.float32)
        kb_[0].data.foreach_get('co', b0_)
        for k_ in kb_[1:]:
            if abs(k_.value) > 1e-6:
                a_ = np.empty(nv_ * 3, dtype=np.float32)
                k_.data.foreach_get('co', a_)
                shaped_ += (a_ - b0_) * k_.value
    shaped_ = shaped_.reshape(-1, 3)
    kd = KDTree(nv_)
    for i_ in range(nv_):
        kd.insert(Vector(shaped_[i_]), i_)
    kd.balance()
    vg = base.vertex_groups.get('lips')

    def lipw(co):
        if vg is None:
            return 0.0
        _, i, d = kd.find(co)
        if d > 0.01:
            return 0.0
        try:
            return vg.weight(i)
        except RuntimeError:
            return 0.0

    def g(p, c, r):
        return math.exp(-((p - c).length ** 2) / (r * r))

    sk, lp = Vector(skin), Vector(lips)
    bl = Vector(blush) if blush else None
    sh = Vector(shadow) if shadow else None
    cl, cr = eye_centres if eye_centres else (None, None)
    for v in me.vertices:
        p = v.co
        col = sk.copy()
        if bl is not None and cl is not None:
            for sx in (1, -1):
                col = col.lerp(bl, g(p, Vector((sx * 0.052, cl.y - 0.0, cl.z - 0.05)), 0.028) * 0.7)
        if sh is not None and cl is not None and p.y < cl.y + 0.03:
            col = col.lerp(sh, max(g(p, cl + Vector((0, -0.006, 0.012)), 0.017), g(p, cr + Vector((0, -0.006, 0.012)), 0.017)) * 0.6)
        if scar is not None:      # pale scar tissue along the carved groove
            sd_ = min((p - q).length for q in scar[0])
            if sd_ < scar[1]:
                col = col.lerp(Vector(scar[2]), (1.0 - sd_ / scar[1]) ** 0.7 * 0.95)
        w = lipw(p)
        if w > 0.1 and lip_strength >= 1.0:
            col = col.lerp(lp, min(1.0, max(0.0, (w - 0.45) * 3.0)))     # tight to the lips: a soft halo of lipstick on the skin looked like a red moustache
        elif w > 0.45:   # subtle lipstick: only the core of the lips, partial strength
            col = col.lerp(lp, min(1.0, (w - 0.45) * 1.5) * lip_strength)
        ca.data[v.index].color = (col.x, col.y, col.z, 1.0)
    m = bpy.data.materials.get(prefix + '_Skin') or bpy.data.materials.new(prefix + '_Skin')
    m.use_nodes = True
    nt = m.node_tree
    b = next(n for n in nt.nodes if n.type == 'BSDF_PRINCIPLED')
    b.inputs['Roughness'].default_value = 0.85
    for n in [n for n in nt.nodes if n.type == 'VERTEX_COLOR']:
        nt.nodes.remove(n)
    vc = nt.nodes.new('ShaderNodeVertexColor')
    vc.layer_name = 'Col'
    nt.links.new(vc.outputs['Color'], b.inputs['Base Color'])
    me.materials.clear()
    me.materials.append(m)
    for p in me.polygons:
        p.material_index = 0
        p.use_smooth = False


# ---------------------------------------------------------------------------------------------- geometry helpers
def tree_of(name):
    ev = bpy.data.objects[name].evaluated_get(bpy.context.evaluated_depsgraph_get())
    me = ev.to_mesh()
    t = BVHTree.FromPolygons([ev.matrix_world @ v.co for v in me.vertices], [p.vertices[:] for p in me.polygons])
    ev.to_mesh_clear()
    return t


def frame(nor):
    z = nor
    x = Vector((0, 0, 1)).cross(z)
    if x.length < 1e-4:
        x = Vector((1, 0, 0))
    x = x.normalized()
    y = z.cross(x)
    return Matrix(((x.x, y.x, z.x), (x.y, y.y, z.y), (x.z, y.z, z.z))).to_4x4()


def new_obj(bm, name, mats):
    old = bpy.data.objects.get(name)
    if old:
        bpy.data.objects.remove(old)
    me = bpy.data.meshes.new(name)
    bm.to_mesh(me)
    bm.free()
    o = bpy.data.objects.new(name, me)
    bpy.context.collection.objects.link(o)
    for m in mats:
        me.materials.append(m)
    for p in me.polygons:
        p.use_smooth = False
    return o


def add_box(bm, M, centre, size, mi, origin=Vector()):
    r = bmesh.ops.create_cube(bm, size=1.0)
    for v in r['verts']:
        v.co = M @ (Vector((v.co.x * size[0], v.co.y * size[1], v.co.z * size[2])) + centre) + origin
    for f in {f for v in r['verts'] for f in v.link_faces}:
        f.material_index = mi
        f.smooth = False


def add_cyl(bm, M, centre, radius, depth, mi, seg=10, origin=Vector(), r2=None):
    r = bmesh.ops.create_cone(bm, cap_ends=True, segments=seg, radius1=radius, radius2=(r2 if r2 is not None else radius), depth=depth)
    for v in r['verts']:
        v.co = M @ (v.co + centre) + origin
    for f in {f for v in r['verts'] for f in v.link_faces}:
        f.material_index = mi
        f.smooth = False


# ---------------------------------------------------------------------------------------------- accessories
def buttons(cloth, prefix, zs, x, color=(0.80, 0.68, 0.45), radius=0.0085, name='Buttons', face_dir=None):
    """Row of flat buttons on the front of a garment. x=0 for a centre-front closure."""
    t = tree_of(cloth)
    bm = bmesh.new()
    for z in zs:
        h = t.ray_cast(Vector((x, -0.8, z)), Vector((0, 1, 0)))
        if h[0] is None:
            continue
        n = h[1].normalized()
        if n.y > 0:
            n = -n
        M = frame(n)
        add_cyl(bm, M, Vector((0, 0, 0.0022)), radius, 0.0044, 0, 8, h[0] + n * 0.0006)
        add_cyl(bm, M, Vector((0, 0, 0.0046)), radius * 0.45, 0.0016, 1, 6, h[0] + n * 0.0006)
    return new_obj(bm, prefix + '_' + name, [mat(prefix + '_ButtonFace', color, 0.1, 0.45), mat(prefix + '_ButtonHole', (0.05, 0.04, 0.035), 0.0, 0.8)])


def belt(cloth, prefix, z, width=0.032, color=(0.12, 0.07, 0.04), buckle=(0.80, 0.68, 0.40), name='Belt', thick=0.0045, cx=0.0, cy=0.0):
    """Ring-shaped belt around the garment at height z with a front buckle (rays inward from a circle)."""
    t = tree_of(cloth)
    N = 40
    bm = bmesh.new()
    rows = []
    # centre of the garment at that height
    ctr = None
    ring = []
    for i in range(N):
        a = 2 * math.pi * i / N
        d = Vector((math.sin(a), -math.cos(a), 0))
        o = Vector((cx, cy, z)) + d * 0.6
        h = t.ray_cast(o, -d)
        if h[0] is None:
            continue
        ring.append((i, h[0], h[1].normalized()))
    if len(ring) < N * 0.8:
        return None
    pts = [(p + n * thick, n) for _, p, n in ring]
    for k in range(len(pts)):
        a_, b_ = pts[k], pts[(k + 1) % len(pts)]
        for dz, dz2 in ((0.0, 0.0),):
            v = [bm.verts.new(a_[0] + Vector((0, 0, width / 2))), bm.verts.new(b_[0] + Vector((0, 0, width / 2))), bm.verts.new(b_[0] - Vector((0, 0, width / 2))), bm.verts.new(a_[0] - Vector((0, 0, width / 2)))]
            f = bm.faces.new(v)
            f.material_index = 0
            f.smooth = False
            f2 = bm.faces.new([bm.verts.new(x.co) for x in v[::-1]])
            f2.material_index = 0
            f2.smooth = False
    # buckle at the front
    h = t.ray_cast(Vector((cx, -0.8, z)), Vector((0, 1, 0)))
    if h[0] is not None:
        n = h[1].normalized()
        M = frame(n)
        W, H, T = 0.034, width + 0.008, 0.0045
        add_box(bm, M, Vector((0, 0, 0)), (W, H, T), 1, h[0] + n * (thick + 0.0016))
        add_box(bm, M, Vector((0, 0, 0.003)), (W - 0.012, H - 0.012, T), 0, h[0] + n * (thick + 0.0016))
    return new_obj(bm, prefix + '_' + name, [mat(prefix + '_BeltLeather', color, 0.0, 0.6), mat(prefix + '_BeltBuckle', buckle, 1.0, 0.35)])


def watch(mesh_name, prefix, joints, side=1, band=(0.10, 0.06, 0.04), face=(0.85, 0.82, 0.74), metal=(0.78, 0.66, 0.38), name='Watch', back=0.02, **_):
    """Wrist watch on the skin: the band follows the exact wrist cross-section (plane cut of the skin mesh) and the case sits on the back of the wrist."""
    bm, ctr, ax, u, v, ang = wrist_band(mesh_name, prefix, joints, side, back=back, width=0.018, thick=0.0035)
    outward = Vector((side, 0.0, 0.55))
    out = (u * outward.dot(u) + v * outward.dot(v)).normalized()
    # distance from the centre to the skin in that direction
    best = max((p - ctr).dot(out) for a_, p in ang)
    zax = out
    xax = ax
    yax = zax.cross(xax)
    Mb = Matrix(((xax.x, yax.x, zax.x), (xax.y, yax.y, zax.y), (xax.z, yax.z, zax.z))).to_4x4()
    case_c = ctr + out * (best + 0.0045)
    add_cyl(bm, Mb, Vector((0, 0, 0)), 0.0135, 0.0065, 1, 12, case_c)
    add_cyl(bm, Mb, Vector((0, 0, 0.0034)), 0.0105, 0.0012, 2, 12, case_c)
    add_box(bm, Mb, Vector((0, 0.0035, 0.0044)), (0.0016, 0.0085, 0.0008), 0, case_c)
    add_box(bm, Mb, Vector((0.0025, 0, 0.0044)), (0.0070, 0.0016, 0.0008), 0, case_c)
    return new_obj(bm, prefix + '_' + name, [mat(prefix + '_WatchBand', band, 0.0, 0.6), mat(prefix + '_WatchCase', metal, 1.0, 0.35), mat(prefix + '_WatchFace', face, 0.0, 0.4)])


def lanyard(suit, low, prefix, card_z, neck_z, strap=(0.10, 0.30, 0.38), card=(0.9, 0.9, 0.86), band=(0.55, 0.20, 0.12), name='Lanyard', half=0.07, width=0.011):
    """Flat strap hanging around the neck, lying on the collar/shoulders at the back (snapped to the outermost surface), V on the chest, ID card at the tip."""
    ts = [tree_of(n) for n in (suit, low)]

    def snap(p, off):
        best = None
        for t in ts:
            loc, nor, idx, dist = t.find_nearest(p)
            if loc is None:
                continue
            if best is None or dist < best[0]:
                best = (dist, loc, nor)
        return best[1] + best[2].normalized() * off, best[2].normalized()

    def snap_top(p, off):
        """Outermost surface seen from above (shoulders, collar): the strap must lie on the jacket, not on the skin under it."""
        best = None
        for t in ts:
            h = t.ray_cast(Vector((p.x, p.y, p.z + 0.3)), Vector((0, 0, -1)))
            if h[0] is not None and (best is None or h[0].z > best[0].z):
                best = h
        if best is None:
            return snap(p, off)
        n = best[1].normalized()
        return best[0] + n * off, n

    top_probe = Vector((0, 0, max(v.co.z for v in bpy.data.objects[low].data.vertices) + 0.1))
    sg = []
    for t in ts:
        loc, nor, _, _ = t.find_nearest(top_probe)
        sg.append(1.0 if (top_probe - loc).dot(nor) > 0 else -1.0)

    def push_out(p, clear=0.0045):
        """Keep a strap vertex outside every garment/skin surface (no clipping)."""
        for _ in range(3):
            for t, sgn in zip(ts, sg):
                loc, nor, _, d = t.find_nearest(p)
                if loc is None or d > 0.03:
                    continue
                n = nor * sgn
                if (p - loc).dot(n) < clear:
                    p = loc + n * clear
        return p

    cy = -0.03
    # the strap rests on the shoulders (trapezius slope) instead of climbing the neck: it comes down the chest in a soft curve,
    # widens towards the shoulder tops and crosses the nape just above the shoulder line
    zs = neck_z - 0.035
    reach = half + 0.025
    N = 12
    left = []
    for i in range(N + 1):
        s = i / N
        left.append(Vector((-reach * (s ** 1.5), -0.20, card_z + 0.012 + (zs - card_z - 0.012) * s)))
    # back of the neck: outward rays from the neck axis at collar height, outermost surface (skin or collar), so the strap hugs the neck
    zn = neck_z - 0.015
    suitobj = bpy.data.objects[suit]
    ring = [v.co for v in suitobj.data.vertices if abs(v.co.z - zn) < 0.02 and abs(v.co.x) < 0.10]   # the collar ring (skin at the back of the neck is trimmed away under the jacket)
    cen = Vector((0.0, (min(v.y for v in ring) + max(v.y for v in ring)) / 2, zn))
    back = []
    for k in range(1, 14):
        th = math.pi - math.pi * k / 14
        d = Vector((math.cos(th), math.sin(th), 0.0))
        far = None
        for t in (ts[0], ts[1]):                    # first surface met going outward from the neck axis: collar, or skin where there is no collar
            hh = t.ray_cast(cen, d, 0.16)
            if hh[0] is not None and (far is None or (hh[0] - cen).length < (far[0] - cen).length):
                far = hh
        if far is None:
            back.append((cen + d * 0.06, d))
        else:
            n = far[1].normalized()
            if n.dot(d) < 0:
                n = -n
            back.append((far[0] - n * 0.012, n))   # runs under the collar / hair: nothing of the strap shows at the back
    right = [Vector((-p.x, p.y, p.z)) for p in reversed(left)]
    nl = len(left)
    pts = []
    for g in left:
        pts.append(snap_top(g, 0.006) if g.z > zs - 0.05 else snap(g, 0.006))
    pts += back
    for g in right:
        pts.append(snap_top(g, 0.006) if g.z > zs - 0.05 else snap(g, 0.006))
    fixed = set(range(nl, nl + len(back)))
    for _ in range(4):
        new = [pts[0]]
        for i in range(1, len(pts) - 1):
            if i in fixed:
                new.append(pts[i])
                continue
            q = (pts[i - 1][0] + pts[i + 1][0]) / 2
            g2 = pts[i][0].lerp(q, 0.5)
            new.append(snap_top(g2, 0.006) if g2.z > zs - 0.05 else snap(g2, 0.006))
        new.append(pts[-1])
        pts = new
    bm = bmesh.new()
    rows = []
    for i, (p, n) in enumerate(pts):
        a = pts[max(i - 1, 0)][0]
        b = pts[min(i + 1, len(pts) - 1)][0]
        tang = (b - a).normalized()
        side = tang.cross(n).normalized() * (width / 2)
        if i in fixed:
            rows.append((p + side, p - side))
        else:
            rows.append((push_out(p + side), push_out(p - side)))
    for a, b in zip(rows, rows[1:]):
        quad = [bm.verts.new(v) for v in (a[0], a[1], b[1], b[0])]
        f = bm.faces.new(quad)
        f.material_index = 0
        f.smooth = False
        f2 = bm.faces.new([bm.verts.new(v.co) for v in quad[::-1]])
        f2.material_index = 0
        f2.smooth = False
    # card at the front tip
    tip, tn = pts[0][0], pts[0][1]
    tn2 = pts[-1][0]
    mid = (tip + tn2) / 2
    h = ts[0].ray_cast(Vector((mid.x, -0.8, card_z)), Vector((0, 1, 0)))
    if h[0] is not None:
        # hang the card in front of everything under it (jacket, shirt, buttons): plane at the most forward surface of its footprint
        fy = []
        for t in ts:
            for dx in (-0.03, 0.0, 0.03):
                for dz in (-0.048, 0.0, 0.048):
                    hh = t.ray_cast(Vector((mid.x + dx, -0.8, card_z + dz)), Vector((0, 1, 0)))
                    if hh[0] is not None:
                        fy.append(hh[0].y)
        n = (Vector((0, -1, 0)) * 0.75 + h[1].normalized() * 0.25).normalized()
        M = frame(n)
        p = Vector((mid.x, min(fy + [h[0].y]) - 0.010, card_z))
        add_box(bm, M, Vector((0, 0, 0)), (0.056, 0.086, 0.003), 1, p)
        add_box(bm, M, Vector((0, 0.030, 0.0018)), (0.056, 0.020, 0.0008), 2, p)
        add_box(bm, M, Vector((-0.013, -0.004, 0.0018)), (0.020, 0.024, 0.0008), 3, p)
        for k in range(2):
            add_box(bm, M, Vector((0.012, -0.002 - k * 0.008, 0.0018)), (0.022, 0.0028, 0.0008), 3, p)
        add_box(bm, M, Vector((0, 0.047, 0.0)), (0.014, 0.008, 0.003), 4, p)
        # short strap pieces joining the V tip to the clip
        for sx in (-1, 1):
            a = pts[0][0] if sx < 0 else pts[-1][0]
            b = p + M @ Vector((0, 0.047, 0.0))
            tang = (b - a).normalized()
            side = tang.cross(n).normalized() * (width / 2)
            quad = [bm.verts.new(v) for v in (a + side, a - side, b - side, b + side)]
            for order in (quad, [bm.verts.new(v.co) for v in quad[::-1]]):
                f = bm.faces.new(order)
                f.material_index = 0
                f.smooth = False
    return new_obj(bm, prefix + '_' + name, [mat(prefix + '_LanyardStrap', strap, 0.0, 0.7), mat(prefix + '_LanyardCard', card, 0.0, 0.6), mat(prefix + '_LanyardBand', band, 0.0, 0.7),
                                           mat(prefix + '_LanyardInk', (0.08, 0.07, 0.06), 0.0, 0.8), mat(prefix + '_LanyardClip', (0.8, 0.62, 0.2), 1.0, 0.35)])


def trim_sleeves(cloth, joints, keep_before=0.06):
    """Cut the garment's sleeves with a clean plane `keep_before` metres before the wrist joint (round, even edge) so the wrist skin and a watch show."""
    o = bpy.data.objects[cloth]
    bm = bmesh.new()
    bm.from_mesh(o.data)
    n = len(bm.faces)
    for side in (1, -1):
        el = Vector((joints['elbow'].x * side, joints['elbow'].y, joints['elbow'].z))
        wr = Vector((joints['wrist'].x * side, joints['wrist'].y, joints['wrist'].z))
        ax = (wr - el).normalized()
        co = wr - ax * keep_before
        geom = bm.verts[:] + bm.edges[:] + bm.faces[:]
        res = bmesh.ops.bisect_plane(bm, geom=geom, dist=0.0001, plane_co=co, plane_no=ax)
        outer = [g for g in res['geom'] if isinstance(g, bmesh.types.BMFace) and side * g.calc_center_median().x > 0.25 and (g.calc_center_median() - co).dot(ax) > 0.0001]
        bmesh.ops.delete(bm, geom=outer, context='FACES')
    # bisect_plane splits every face crossing the plane; faces beyond it near the hand are removed above
    bmesh.ops.delete(bm, geom=[v for v in bm.verts if not v.link_faces], context='VERTS')
    bm.to_mesh(o.data)
    bm.free()
    for p in o.data.polygons:
        p.use_smooth = False
    return n - len(o.data.polygons)


def cross_section(mesh_name, plane_co, plane_no, near, radius=0.07):
    """Exact cross-section of a mesh by a plane: the cut points that lie within `radius` of `near` (so only the limb we want)."""
    o = bpy.data.objects[mesh_name]
    bm = bmesh.new()
    bm.from_mesh(o.data)
    bm.transform(o.matrix_world)
    geom = bm.verts[:] + bm.edges[:] + bm.faces[:]
    res = bmesh.ops.bisect_plane(bm, geom=geom, dist=0.00005, plane_co=plane_co, plane_no=plane_no)
    pts = [g.co.copy() for g in res['geom_cut'] if isinstance(g, bmesh.types.BMVert) and (g.co - near).length < radius]
    bm.free()
    return pts


def wrist_band(skin_mesh, prefix, joints, side=1, back=0.02, width=0.018, thick=0.0035, band=(0.1, 0.06, 0.04), name='Band'):
    """Ring that follows the REAL wrist cross-section; returns (object, centre, axis, outward) so a watch face can be added."""
    el = Vector((joints['elbow'].x * side, joints['elbow'].y, joints['elbow'].z))
    wr = Vector((joints['wrist'].x * side, joints['wrist'].y, joints['wrist'].z))
    ax = (wr - el).normalized()
    c0 = wr - ax * back
    pts = cross_section(skin_mesh, c0, ax, c0)
    if len(pts) < 5:
        pts = cross_section(skin_mesh, c0, ax, c0, 0.12)
    ctr = sum(pts, Vector()) / len(pts)
    up = Vector((0, 0, 1))
    u = ax.cross(up)
    u = u.normalized() if u.length > 1e-4 else Vector((1, 0, 0))
    v = ax.cross(u).normalized()
    ang = sorted(((math.atan2((p - ctr).dot(v), (p - ctr).dot(u)), p) for p in pts), key=lambda t: t[0])
    bm = bmesh.new()
    ra, rb, dirs = [], [], []
    for a, p in ang:
        d = (p - ctr)
        d = (d - ax * d.dot(ax)).normalized()
        base = p - ax * (p - ctr).dot(ax)
        ra.append(bm.verts.new(base + d * thick + ax * width / 2))
        rb.append(bm.verts.new(base + d * thick - ax * width / 2))
        dirs.append(d)
    n = len(ra)
    for i in range(n):
        j = (i + 1) % n
        f = bm.faces.new((ra[i], ra[j], rb[j], rb[i]))
        f.material_index = 0
        f.smooth = False
    return bm, ctr, ax, u, v, ang


def split_at_z(name, zs):
    """Cut a garment with horizontal planes so colour regions (jacket/trousers, hem bands) meet on a clean straight line instead of a saw-tooth."""
    o = bpy.data.objects[name]
    bm = bmesh.new()
    bm.from_mesh(o.data)
    for z in zs:
        bmesh.ops.bisect_plane(bm, geom=bm.verts[:] + bm.edges[:] + bm.faces[:], dist=0.0001, plane_co=Vector((0, 0, z)), plane_no=Vector((0, 0, 1)))
    bm.to_mesh(o.data)
    bm.free()
    for p_ in o.data.polygons:
        p_.use_smooth = False


def split_planes(name, planes):
    """Cut a garment with arbitrary planes [(point, normal), ...] so colour regions (shirt V, bib, stripes) have clean straight borders."""
    o = bpy.data.objects[name]
    bm = bmesh.new()
    bm.from_mesh(o.data)
    for co, no in planes:
        bmesh.ops.bisect_plane(bm, geom=bm.verts[:] + bm.edges[:] + bm.faces[:], dist=0.0001, plane_co=Vector(co), plane_no=Vector(no))
    bm.to_mesh(o.data)
    bm.free()
    for p_ in o.data.polygons:
        p_.use_smooth = False


def v_planes(z_top, z_v, half_w):
    """Two planes forming a V opening (apex at z_v on the centre line, half_w wide at z_top)."""
    k = half_w / (z_top - z_v)
    n = (1.0, 0.0, -k)
    m = (1.0, 0.0, k)
    return [((0, 0, z_v), n), ((0, 0, z_v), m)]


def paint_wrinkles(low_name, img, eyes_name, strength=0.3, color_mul=0.62, width_px=2.2, brow_z=None, extra=None):
    """Draw subtle wrinkle lines (forehead, crow's feet, under-eye, nasolabial, chin crease) straight into the baked skin texture.
    Points are defined on the face in front view (x, z), ray-cast onto the skin mesh to get UV coordinates, then painted as soft dark strokes."""
    import numpy as np
    o = bpy.data.objects[low_name]
    tr = tree_of(low_name)
    cl, cr = eye_centres_world(eyes_name)
    ez = (cl.z + cr.z) / 2
    ex = abs(cl.x)
    uv = o.data.uv_layers.active.data
    W, H = img.size
    px = np.empty(W * H * 4, dtype=np.float32)
    img.pixels.foreach_get(px)
    px = px.reshape(H, W, 4)

    def to_uv(x, z):
        h = tr.ray_cast(Vector((x, -0.6, z)), Vector((0, 1, 0)))
        if h[0] is None:
            return None
        poly = o.data.polygons[h[2]]
        loops = list(poly.loop_indices)
        vs = [o.data.vertices[o.data.loops[l].vertex_index].co for l in loops]
        best = None
        for i in range(1, len(loops) - 1):       # triangle fan, barycentric
            a, b, c = vs[0], vs[i], vs[i + 1]
            v0, v1, v2 = b - a, c - a, h[0] - a
            d00, d01, d11, d20, d21 = v0.dot(v0), v0.dot(v1), v1.dot(v1), v2.dot(v0), v2.dot(v1)
            den = d00 * d11 - d01 * d01
            if abs(den) < 1e-12:
                continue
            bv = (d11 * d20 - d01 * d21) / den
            bw = (d00 * d21 - d01 * d20) / den
            bu = 1 - bv - bw
            if min(bu, bv, bw) > -0.02:
                u = uv[loops[0]].uv * bu + uv[loops[i]].uv * bv + uv[loops[i + 1]].uv * bw
                return u
        return None

    def stroke(points, a=1.0):
        P = []
        dense = []
        for (xa, za), (xb, zb) in zip(points, points[1:]):      # many short pieces: a stroke never jumps across a UV seam / island
            for k in range(8):
                dense.append((xa + (xb - xa) * k / 8, za + (zb - za) * k / 8))
        dense.append(points[-1])
        P = []
        for (x, z) in dense:
            u = to_uv(x, z)
            P.append(None if u is None else (u[0] * (W - 1), u[1] * (H - 1)))
        for a_, b_ in zip(P, P[1:]):
            if a_ is None or b_ is None:
                continue
            (x0, y0), (x1, y1) = a_, b_
            if abs(x1 - x0) > 0.025 * W or abs(y1 - y0) > 0.025 * H:
                continue
            n = int(max(abs(x1 - x0), abs(y1 - y0))) + 1
            for k in range(n + 1):
                t = k / max(n, 1)
                cx, cy = x0 + (x1 - x0) * t, y0 + (y1 - y0) * t
                r = int(width_px * 2)
                for yy in range(int(cy) - r, int(cy) + r + 1):
                    for xx in range(int(cx) - r, int(cx) + r + 1):
                        if 0 <= xx < W and 0 <= yy < H:
                            d = ((xx - cx) ** 2 + (yy - cy) ** 2) ** 0.5
                            w = max(0.0, 1.0 - d / (width_px * 1.2)) * strength * a
                            if w > 0:
                                px[yy, xx, :3] = px[yy, xx, :3] * (1 - w) + px[yy, xx, :3] * color_mul * w

    def arc(x0, x1, z, sag, n=9):
        return [(x0 + (x1 - x0) * i / n, z + sag * (1 - (2 * i / n - 1) ** 2)) for i in range(n + 1)]
    bz = brow_z if brow_z is not None else ez + 0.027
    for k, dz in enumerate((0.016, 0.032, 0.048)):                    # forehead lines
        stroke(arc(-ex * 1.25, ex * 1.25, bz + dz, 0.004), 1.0 - 0.15 * k)
    for sx in (-1, 1):
        for k, dz in enumerate((0.006, 0.0, -0.006)):                 # crow's feet fanning out from the outer eye corner
            stroke([(sx * (ex + 0.027), ez + dz * 0.2), (sx * (ex + 0.040), ez + dz * 1.6)], 0.8)
        stroke([(sx * (ex + 0.020), ez - 0.024), (sx * (ex + 0.0), ez - 0.027), (sx * (ex - 0.017), ez - 0.025)], 0.7)       # under-eye bag
        stroke([(sx * 0.020, ez - 0.036), (sx * 0.030, ez - 0.058), (sx * 0.034, ez - 0.082)], 1.0)                           # nasolabial fold
        stroke([(sx * 0.0035, ez + 0.012), (sx * 0.0045, ez + 0.0245)], 0.9)                                                 # frown lines between the brows
    stroke(arc(-0.018, 0.018, ez - 0.108, -0.002), 0.8)                # chin crease
    for line in (extra or []):
        stroke(line, 1.0)
    px2 = px.reshape(-1)
    img.pixels.foreach_set(px2)
    img.update()


def paint_stains(img, obj_name, zones, seed=3):
    """Soft organic stains (mud, dirt, dust, sweat) painted into the baked texture of a garment, so they read as smudges and not as coloured triangles.
    zones: [dict(zmin, zmax, count, r=(min,max) metres, color=(r,g,b), alpha, x_abs=(lo,hi) optional, front=None|True|False)].
    Each stain is a cluster of soft round blobs placed at random points of the garment surface; blob size follows the local UV scale."""
    import random
    import numpy as np
    rnd = random.Random(seed)
    o = bpy.data.objects[obj_name]
    me = o.data
    uvd = me.uv_layers.active.data
    W, H = img.size
    px = np.empty(W * H * 4, dtype=np.float32)
    img.pixels.foreach_get(px)
    px = px.reshape(H, W, 4)
    polys = []
    for p_ in me.polygons:
        loops = list(p_.loop_indices)
        if len(loops) < 3:
            continue
        a, b, c = [me.vertices[me.loops[l].vertex_index].co for l in loops[:3]]
        area = ((b - a).cross(c - a)).length / 2
        if area < 1e-9:
            continue
        ua, ub, uc = [uvd[l].uv for l in loops[:3]]
        uv_len = ((ub - ua).length + (uc - ua).length) / 2
        m_len = ((b - a).length + (c - a).length) / 2
        polys.append((p_, loops, area, uv_len / max(m_len, 1e-9) * W))
    for z in zones:
        sel = []
        for e in polys:
            cz = e[0].center
            if not (z['zmin'] <= cz.z <= z['zmax']):
                continue
            if 'x_abs' in z and not (z['x_abs'][0] <= abs(cz.x) <= z['x_abs'][1]):
                continue
            if z.get('front') is True and cz.y > 0:
                continue
            if z.get('front') is False and cz.y < 0:
                continue
            sel.append(e)
        if not sel:
            continue
        weights = [e[2] for e in sel]
        col = np.array(z['color'], dtype=np.float32)
        for _ in range(z['count']):
            e = rnd.choices(sel, weights)[0]
            loops = e[1]
            r1, r2 = rnd.random(), rnd.random()
            if r1 + r2 > 1:
                r1, r2 = 1 - r1, 1 - r2
            uv0, uv1, uv2 = uvd[loops[0]].uv, uvd[loops[1]].uv, uvd[loops[2]].uv
            u = uv0 + (uv1 - uv0) * r1 + (uv2 - uv0) * r2
            cx, cy = u[0] * (W - 1), u[1] * (H - 1)
            scale = e[3]
            base_r = rnd.uniform(*z['r']) * scale
            for k in range(rnd.randint(3, 6)):
                bx = cx + rnd.uniform(-1, 1) * base_r * 0.9
                by = cy + rnd.uniform(-1, 1) * base_r * 0.9
                rad = base_r * rnd.uniform(0.45, 1.0)
                r = int(rad * 2.2) + 1
                y0, y1, x0, x1 = max(0, int(by) - r), min(H, int(by) + r + 1), max(0, int(bx) - r), min(W, int(bx) + r + 1)
                if y0 >= y1 or x0 >= x1:
                    continue
                yy, xx = np.mgrid[y0:y1, x0:x1]
                d2 = ((xx - bx) ** 2 + (yy - by) ** 2) / (rad * rad)
                w = np.exp(-d2 * 1.6) * z['alpha'] * rnd.uniform(0.6, 1.0)
                w = np.where(w > 0.04, w, 0.0)[..., None]
                px[y0:y1, x0:x1, :3] = px[y0:y1, x0:x1, :3] * (1 - w) + col * w
    img.pixels.foreach_set(px.reshape(-1))
    img.update()


def hair_filler(hair_name, skin_name, max_gap=0.022, min_gap=0.0006, where=None, color=None, lift=0.0008):
    """Close the gap between the edge of the hair shell and the scalp: every open (boundary) edge of the hair gets a strip of quads reaching down to the nearest skin surface,
    using the material of the neighbouring hair face so it bakes with the same hair texture."""
    from mathutils.bvhtree import BVHTree
    o = bpy.data.objects[hair_name]
    s = bpy.data.objects[skin_name]
    bmS = bmesh.new()
    bmS.from_mesh(s.data)
    treeS = BVHTree.FromBMesh(bmS)
    bm = bmesh.new()
    bm.from_mesh(o.data)
    bm.edges.ensure_lookup_table()
    cache = {}

    def proj(v):
        if v.index in cache:
            return cache[v.index]
        loc, nor, idx, d = treeS.find_nearest(v.co)
        res = None
        if loc is not None and min_gap < d < max_gap:
            n = nor.normalized()
            if (v.co - loc).dot(n) < 0:
                n = -n
            res = loc + n * lift
        cache[v.index] = res
        return res
    added = 0
    fill_mi = None
    if color is not None:       # plain flat sheet in its own colour (only covers a gap, no hair detail)
        o.data.materials.append(mat(hair_name.split('_')[0] + '_HairFill', color, 0.0, 0.9))
        fill_mi = len(o.data.materials) - 1
    for e in [e for e in bm.edges if e.is_boundary]:
        v0, v1 = e.verts
        if where is not None and not (where(v0.co) and where(v1.co)):
            continue
        p0, p1 = proj(v0), proj(v1)
        if p0 is None or p1 is None:
            continue
        mi = e.link_faces[0].material_index if fill_mi is None else fill_mi
        q = [v0, v1, bm.verts.new(p1), bm.verts.new(p0)]
        try:
            f = bm.faces.new(q)
        except ValueError:
            continue
        f.material_index = mi
        f.smooth = False
        added += 1
    bm.to_mesh(o.data)
    bm.free()
    bmS.free()
    return added


def carve_scar(low_name, eyes_name, side=1, depth=0.0030, radius=0.0036):
    """Scar carved INTO the skin mesh (a groove), not a decal: the faces around the path are subdivided, then the vertices near the polyline are pushed inward with a smooth profile.
    The path runs on the skin beside the eye (forehead over the outer brow, past the outer eye corner, down the cheekbone) and never touches the eyeball. Returns the path points."""
    o = bpy.data.objects[low_name]
    tr = tree_of(low_name)
    cl, cr = eye_centres_world(eyes_name)
    c = cl if (cl.x > 0) == (side > 0) else cr
    s_ = 1.0 if side > 0 else -1.0
    # vertical scar on the axis of the eye: one stretch over the brow and eyelid crease (stopping before the eyeball), one on the cheek below it (starting after the eyeball)
    xs0 = c.x + s_ * 0.001
    segs_ctrl = [[(xs0 - s_ * 0.002, c.z + 0.056), (xs0 + s_ * 0.001, c.z + 0.044), (xs0 + s_ * 0.003, c.z + 0.032), (xs0 + s_ * 0.004, c.z + 0.024)],
                 [(xs0 + s_ * 0.0035, c.z - 0.0165), (xs0 + s_ * 0.0050, c.z - 0.030), (xs0 + s_ * 0.0065, c.z - 0.046), (xs0 + s_ * 0.0075, c.z - 0.058)]]
    pts = []
    pieces = []
    for ctrl in segs_ctrl:
        dense = []
        for (xa, za), (xb, zb) in zip(ctrl, ctrl[1:]):
            for k in range(6):
                dense.append((xa + (xb - xa) * k / 6, za + (zb - za) * k / 6))
        dense.append(ctrl[-1])
        piece = []
        for x, z in dense:
            h = tr.ray_cast(Vector((x, -0.6, z)), Vector((0, 1, 0)))
            if h[0] is not None:
                piece.append(h[0])
        pieces.append(piece)
        pts += piece
    bm = bmesh.new()
    bm.from_mesh(o.data)

    def near(p, r):
        return min((p - q).length for q in pts) < r
    for _ in range(4):
        es = [e for e in bm.edges if e.calc_length() > 0.0028 and near((e.verts[0].co + e.verts[1].co) / 2, 0.009)]
        if not es:
            break
        bmesh.ops.subdivide_edges(bm, edges=es, cuts=1, use_grid_fill=True)
    bm.normal_update()
    segs = [sg for pc in pieces for sg in zip(pc, pc[1:])]

    def dist(p):
        best = 1e9
        for a, b in segs:
            ab = b - a
            t = max(0.0, min(1.0, (p - a).dot(ab) / max(ab.length_squared, 1e-12)))
            best = min(best, (p - (a + ab * t)).length)
        return best
    moved = 0
    for v in bm.verts:
        d = dist(v.co)
        if d < radius:
            w = (1.0 - (d / radius) ** 2) ** 1.5
            n = v.normal.copy()
            if n.y > 0:
                n = -n
            v.co = v.co - n * depth * w
            moved += 1
    for f in bm.faces:
        f.smooth = False
    bm.to_mesh(o.data)
    bm.free()
    o.data.update()
    return pts


def hair_layers(hair_name, tiers=6, locks=16, length=0.055, width=0.030, span=105.0, z_top_off=0.035, z_low=None, seed=4, spread=0.012, tilt=0.010):
    """Layered locks on the back (and sides) of a hair shell: tiers of overlapping tapered strands, each tier slightly lower and further out, so the nape reads as worked hair
    instead of a smooth cap. Locks are ray-snapped to the existing hair surface; added as faces of the same mesh, material = one of the hair tones."""
    import random
    rnd = random.Random(seed)
    o = bpy.data.objects[hair_name]
    tr = tree_of(hair_name)
    vs = [v.co for v in o.data.vertices]
    zt = max(v.z for v in vs)
    zl = z_low if z_low is not None else min(v.z for v in vs if v.y > 0) + 0.01
    cx = (min(v.x for v in vs) + max(v.x for v in vs)) / 2
    cy = (min(v.y for v in vs) + max(v.y for v in vs)) / 2
    nmat = len(o.data.materials)
    bm = bmesh.new()
    bm.from_mesh(o.data)
    for t in range(tiers):
        f_ = t / max(tiers - 1, 1)
        zc = (zt - z_top_off) + (zl - (zt - z_top_off)) * f_
        n_l = max(6, int(locks * (1.0 - 0.25 * f_)))
        for k in range(n_l):
            a = math.radians(-span + 2 * span * (k + (0.5 if t % 2 else 0.0)) / n_l)         # 0 = straight back
            d = Vector((math.sin(a), math.cos(a), 0.0))
            origin = Vector((cx, cy, zc))
            h = tr.ray_cast(origin, d, 0.4)
            if h[0] is None:
                continue
            n = h[1].normalized()
            if n.dot(d) < 0:
                n = -n
            side = Vector((-d.y, d.x, 0.0))
            w = width * rnd.uniform(0.8, 1.2)
            L = length * rnd.uniform(0.75, 1.25) * (1.0 - 0.2 * f_)
            top = h[0] + n * 0.0015
            tip = top + Vector((0, 0, -L)) + n * (tilt + 0.004 * t) + side * rnd.uniform(-spread, spread) * 0.5
            mid_ = top + (tip - top) * 0.5 + n * 0.0035
            q = [bm.verts.new(top + side * w / 2), bm.verts.new(top - side * w / 2), bm.verts.new(mid_ - side * w * 0.46), bm.verts.new(tip - side * w * 0.30 + side * rnd.uniform(-0.002, 0.002)),
                 bm.verts.new(tip + side * w * 0.30), bm.verts.new(mid_ + side * w * 0.46)]
            q = [q[0], q[5], q[4], q[3], q[2], q[1]][::-1] if False else [q[0], q[1], q[2], q[3], q[4], q[5]]
            try:
                fq = bm.faces.new(q)
            except ValueError:
                continue
            fq.material_index = rnd.randrange(nmat) if nmat else 0
            fq.smooth = False
            fb = bm.faces.new([bm.verts.new(v.co) for v in q[::-1]])
            fb.material_index = fq.material_index
            fb.smooth = False
    bm.to_mesh(o.data)
    bm.free()


def hair_strands(hair_name, amp=0.0055, freq=22.0, drift=5.0, y_min=-0.02, cuts=1, noise=0.35, seed=3):
    """Combed-strand relief for the back and sides of a hair shell: the faces behind y_min are subdivided and the vertices are pushed along their normals by a ridge pattern that
    follows the head's circumference (phase = freq * angle + drift * z) plus a little noise, so the back reads as flowing locks instead of a smooth cap. No loose geometry."""
    import random
    rnd = random.Random(seed)
    o = bpy.data.objects[hair_name]
    bm = bmesh.new()
    bm.from_mesh(o.data)
    vs = [v.co for v in bm.verts]
    cx = (min(v.x for v in vs) + max(v.x for v in vs)) / 2
    cy = (min(v.y for v in vs) + max(v.y for v in vs)) / 2
    for _ in range(cuts):
        es = [e for e in bm.edges if (e.verts[0].co.y + e.verts[1].co.y) / 2 > y_min and e.calc_length() > 0.012]
        if es:
            bmesh.ops.subdivide_edges(bm, edges=es, cuts=1, use_grid_fill=True)
    bm.normal_update()
    zt = max(v.co.z for v in bm.verts)
    zb = min(v.co.z for v in bm.verts)
    phases = {}
    for v in bm.verts:
        if v.co.y <= y_min:
            continue
        th = math.atan2(v.co.x - cx, v.co.y - cy)
        fade = min(1.0, (v.co.y - y_min) / 0.04)
        zf = 1.0 if v.co.z < zt - 0.03 else max(0.0, (zt - v.co.z) / 0.03)
        w = math.sin(freq * th + drift * v.co.z * 10.0) + noise * (rnd.random() - 0.5) * 2
        n = v.normal.copy()
        if n.dot(Vector((v.co.x - cx, v.co.y - cy, 0.0))) < 0:
            n = -n
        v.co = v.co + n * amp * w * fade * (0.55 + 0.45 * zf)
    for f in bm.faces:
        f.smooth = False
    bm.to_mesh(o.data)
    bm.free()


def smooth_region(name, where, iters=6, factor=0.5, pin_boundary=True):
    """Laplacian-relax the vertices of a mesh that satisfy where(co); open-boundary vertices stay put so cut edges (hems) are not changed."""
    o = bpy.data.objects[name]
    bm = bmesh.new(); bm.from_mesh(o.data)
    vs = [v for v in bm.verts if where(v.co) and not (pin_boundary and v.is_boundary)]
    for _ in range(iters):
        new = {}
        for v in vs:
            nb = [e.other_vert(v).co for e in v.link_edges]
            if nb:
                avg = sum(nb, Vector()) / len(nb)
                new[v.index] = v.co.lerp(avg, factor)
        for v in vs:
            if v.index in new:
                v.co = new[v.index]
    bm.to_mesh(o.data); bm.free()


def paint_skin_scars(low_name, img, scars, joints, color=(0.84, 0.66, 0.58), width_px=3.2, alpha=0.9):
    """Small pale scars painted into the baked skin texture on arms and hands. Each scar: side (+1 left / -1 right), part ('upper' shoulder->elbow, 'forearm' elbow->wrist,
    'hand' = forearm axis continued past the wrist), t=(t0, t1) fractions along that axis, lat=(l0, l1) sideways offsets (m), dir = direction the ray comes from (the side of the limb)."""
    import numpy as np
    o = bpy.data.objects[low_name]
    tr = tree_of(low_name)
    uv = o.data.uv_layers.active.data
    W, H = img.size
    px = np.empty(W * H * 4, dtype=np.float32)
    img.pixels.foreach_get(px)
    px = px.reshape(H, W, 4)
    sh, el, wr = Vector(joints['shoulder']), Vector(joints['elbow']), Vector(joints['wrist'])

    def to_uv(origin, d):
        h = tr.ray_cast(origin, d)
        if h[0] is None:
            return None
        poly = o.data.polygons[h[2]]
        loops = list(poly.loop_indices)
        vs = [o.data.vertices[o.data.loops[l].vertex_index].co for l in loops]
        for i in range(1, len(loops) - 1):
            a, b, c = vs[0], vs[i], vs[i + 1]
            v0, v1, v2 = b - a, c - a, h[0] - a
            d00, d01, d11, d20, d21 = v0.dot(v0), v0.dot(v1), v1.dot(v1), v2.dot(v0), v2.dot(v1)
            den = d00 * d11 - d01 * d01
            if abs(den) < 1e-12:
                continue
            bv = (d11 * d20 - d01 * d21) / den
            bw = (d00 * d21 - d01 * d20) / den
            bu = 1 - bv - bw
            if min(bu, bv, bw) > -0.02:
                return uv[loops[0]].uv * bu + uv[loops[i]].uv * bv + uv[loops[i + 1]].uv * bw
        return None

    for s in scars:
        d = Vector(s['dir']).normalized()
        P = []
        if 'pts' in s:        # free points (x, y, z) in world space, e.g. a smudge on the face
            pts = [Vector(q) for q in s['pts']]
            dense = []
            for qa, qb in zip(pts, pts[1:]):
                for k in range(8):
                    dense.append(qa.lerp(qb, k / 8))
            dense.append(pts[-1])
            for c in dense:
                u = to_uv(c + d * 0.15, -d)
                P.append(None if u is None else (u[0] * (W - 1), u[1] * (H - 1)))
        else:
            sx = float(s['side'])
            m = lambda p: Vector((p.x * sx, p.y, p.z))
            a, b = (m(sh), m(el)) if s['part'] == 'upper' else (m(el), m(wr))
            axis = (b - a)
            lat = axis.normalized().cross(d).normalized()
            N = 14
            for k in range(N + 1):
                f = k / N
                t = s['t'][0] + (s['t'][1] - s['t'][0]) * f
                l = s['lat'][0] + (s['lat'][1] - s['lat'][0]) * f
                c = a + axis * t + lat * l
                u = to_uv(c + d * 0.15, -d)
                P.append(None if u is None else (u[0] * (W - 1), u[1] * (H - 1)))
        col_ = np.array(s.get('color', color), dtype=np.float32)
        wpx = s.get('width_px', width_px)
        al = s.get('alpha', alpha)
        for p0, p1 in zip(P, P[1:]):
            if p0 is None or p1 is None:
                continue
            (x0, y0), (x1, y1) = p0, p1
            if abs(x1 - x0) > 0.03 * W or abs(y1 - y0) > 0.03 * H:
                continue
            n = int(max(abs(x1 - x0), abs(y1 - y0))) + 1
            for k in range(n + 1):
                tt = k / max(n, 1)
                cx, cy = x0 + (x1 - x0) * tt, y0 + (y1 - y0) * tt
                r = int(wpx * 2)
                for yy in range(int(cy) - r, int(cy) + r + 1):
                    for xx in range(int(cx) - r, int(cx) + r + 1):
                        if 0 <= xx < W and 0 <= yy < H:
                            dd = ((xx - cx) ** 2 + (yy - cy) ** 2) ** 0.5
                            w = (max(0.0, 1.0 - dd / (wpx * 1.1)) ** s.get('falloff', 1.0)) * al
                            if w > 0:
                                px[yy, xx, :3] = px[yy, xx, :3] * (1 - w) + col_ * w
    img.pixels.foreach_set(px.reshape(-1))
    img.update()


def trim_leg_shell(name, z_cut):
    """Delete the part of the trouser shell (the connected piece that reaches the ankles) above z_cut: it is hidden under the jacket and, with projected UVs,
    it overlaps the jacket in the texture atlas (green bleeding into the jacket, red into the trousers)."""
    o = bpy.data.objects[name]
    bm = bmesh.new(); bm.from_mesh(o.data); bm.faces.ensure_lookup_table()
    seen = set(); kill = []
    for f0 in bm.faces:
        if f0.index in seen:
            continue
        st = [f0]; seen.add(f0.index); comp = []
        while st:
            a = st.pop(); comp.append(a)
            for e in a.edges:
                for b in e.link_faces:
                    if b.index not in seen:
                        seen.add(b.index); st.append(b)
        if min(v.co.z for f in comp for v in f.verts) < 0.2:
            kill += [f for f in comp if f.calc_center_median().z > z_cut]
    bmesh.ops.delete(bm, geom=kill, context='FACES_ONLY')
    bmesh.ops.delete(bm, geom=[v for v in bm.verts if not v.link_faces], context='VERTS')
    bm.to_mesh(o.data); bm.free()


def close_notches(name, zmin=0.06, zmax=0.6, hem_z=0.085, xmin=0.2):
    """Close V-shaped notches (missing wedges) in a trouser leg: the open boundary edges above the hem form a chain; its two lower ends are joined and the hole is filled."""
    o = bpy.data.objects[name]
    bm = bmesh.new(); bm.from_mesh(o.data)
    sel = [e for e in bm.edges if e.is_boundary and min(v.co.z for v in e.verts) >= zmin - 0.002 and max(v.co.z for v in e.verts) < zmax
           and not (max(v.co.z for v in e.verts) < hem_z) and abs(sum(v.co.x for v in e.verts) / 2) > xmin]
    seen = set(); comps = []
    for e0 in sel:
        if e0.index in seen:
            continue
        st = [e0]; seen.add(e0.index); comp = []
        while st:
            e = st.pop(); comp.append(e)
            for v in e.verts:
                for e2 in v.link_edges:
                    if e2 in sel and e2.index not in seen:
                        seen.add(e2.index); st.append(e2)
        comps.append(comp)
    filled = 0
    for comp in comps:
        deg = {}
        for e in comp:
            for v in e.verts:
                deg[v] = deg.get(v, 0) + 1
        ends = sorted([v for v, d in deg.items() if d == 1], key=lambda v: v.co.z)[:2]
        if len(ends) == 2:
            try:
                ne = bm.edges.new(ends)
            except ValueError:
                ne = bm.edges.get(ends)
            res = bmesh.ops.holes_fill(bm, edges=comp + [ne], sides=0)
            filled += len(res.get('faces', []))
    bm.to_mesh(o.data); bm.free()
    return filled


def split_planes_region(name, planes):
    """Like split_planes, but each plane is (point, normal, pred): only faces whose centre satisfies pred(centre) are cut (so stripe planes for the torso do not slice the sleeves)."""
    o = bpy.data.objects[name]
    bm = bmesh.new()
    bm.from_mesh(o.data)
    for co, no, pred in planes:
        faces = [f for f in bm.faces if pred(f.calc_center_median())]
        edges = list({e for f in faces for e in f.edges})
        verts = list({v for f in faces for v in f.verts})
        bmesh.ops.bisect_plane(bm, geom=verts + edges + faces, dist=0.0001, plane_co=Vector(co), plane_no=Vector(no))
    bm.to_mesh(o.data)
    bm.free()
    for p_ in o.data.polygons:
        p_.use_smooth = False


def fill_bake_holes(img, obj_names, thr=0.004, iters=24):
    """Baking can miss tiny UV triangles and leave black texels INSIDE a UV island (dark specks / lines on the model). Rasterise the UV coverage of `obj_names`,
    find covered texels that are still pure black and fill them from their painted neighbours."""
    import numpy as np
    W, H = img.size
    px = np.empty(W * H * 4, dtype=np.float32)
    img.pixels.foreach_get(px)
    px = px.reshape(H, W, 4)
    cov = np.zeros((H, W), dtype=bool)
    for n in obj_names:
        me = bpy.data.objects[n].data
        uv = me.uv_layers.active.data
        for p in me.polygons:
            pts = [(uv[l].uv[0] * W, uv[l].uv[1] * H) for l in p.loop_indices]
            for i in range(1, len(pts) - 1):
                tri = np.array([pts[0], pts[i], pts[i + 1]])
                mn = np.floor(tri.min(0)).astype(int).clip(0, [W - 1, H - 1])
                mx = np.ceil(tri.max(0)).astype(int).clip(0, [W - 1, H - 1])
                xs, ys = np.meshgrid(np.arange(mn[0], mx[0] + 1), np.arange(mn[1], mx[1] + 1))
                q = np.stack([xs.ravel() + 0.5, ys.ravel() + 0.5], 1)
                a, b, c = tri
                d = (b[1] - c[1]) * (a[0] - c[0]) + (c[0] - b[0]) * (a[1] - c[1])
                if abs(d) < 1e-9:
                    cov[ys.ravel().clip(0, H - 1), xs.ravel().clip(0, W - 1)] = True      # degenerate sliver: mark its bounding texels
                    continue
                w1 = ((b[1] - c[1]) * (q[:, 0] - c[0]) + (c[0] - b[0]) * (q[:, 1] - c[1])) / d
                w2 = ((c[1] - a[1]) * (q[:, 0] - c[0]) + (a[0] - c[0]) * (q[:, 1] - c[1])) / d
                m = (w1 >= -0.02) & (w2 >= -0.02) & (1 - w1 - w2 >= -0.02)
                cov[q[m, 1].astype(int).clip(0, H - 1), q[m, 0].astype(int).clip(0, W - 1)] = True
    black = px[:, :, :3].max(axis=2) < thr
    hole = cov & black
    n0 = int(hole.sum())
    good = ~black
    for _ in range(iters):
        if not hole.any():
            break
        acc = np.zeros((H, W, 3), dtype=np.float32)
        cnt = np.zeros((H, W), dtype=np.float32)
        for dy in (-1, 0, 1):
            for dx in (-1, 0, 1):
                if dx == 0 and dy == 0:
                    continue
                g = np.roll(np.roll(good, dy, 0), dx, 1)
                v = np.roll(np.roll(px[:, :, :3], dy, 0), dx, 1)
                acc += v * g[:, :, None]
                cnt += g
        fill = hole & (cnt > 0)
        px[fill, :3] = acc[fill] / cnt[fill][:, None]
        good = good | fill
        hole = hole & ~fill
    img.pixels.foreach_set(px.reshape(-1))
    img.update()
    return n0, int(hole.sum())
