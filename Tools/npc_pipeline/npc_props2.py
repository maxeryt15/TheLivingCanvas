"""More NPC props: woven straw hat, mustache, straw stalk in the mouth, gloves modelled from the character's own hand."""
import bpy, bmesh, math
from mathutils import Vector, Matrix
import npc_details as D
from npc_details import mat, new_obj, add_box, add_cyl, frame, tree_of
from npc_props import _head_info, _cone_between, _snap_fn, _outside_pusher, strap, strap_mesh
import npc_accessories as A


def straw_hat(prefix, hair, straw=(0.78, 0.60, 0.28), straw2=(0.66, 0.48, 0.19), band=(0.12, 0.22, 0.10), name='Hat', brim=0.105, crown_h=0.085, wide=0.014, tilt_back=0.0):
    """Woven straw hat: rounded crown from stacked rings in two alternating straw tones (weave bands), drooping brim of concentric rings, rim edge and hat band."""
    top, hx, hy, lowz = _head_info(hair)
    bm = bmesh.new()
    cz = top.z - 0.060
    Rx, Ry = hx + wide, hy + wide
    cx, cy = top.x, top.y
    NS = 16

    def ring(r_scale, z):
        return [bm.verts.new(Vector((cx + Rx * r_scale * math.sin(2 * math.pi * i / NS), cy + Ry * r_scale * math.cos(2 * math.pi * i / NS), z))) for i in range(NS)]

    def join(a, b, mi):
        for i in range(NS):
            j = (i + 1) % NS
            f = bm.faces.new([a[i], a[j], b[j], b[i]])
            f.material_index = mi
            f.smooth = False

    prof = [(1.00, 0.0), (1.00, 0.20), (0.985, 0.42), (0.94, 0.62), (0.84, 0.80), (0.66, 0.93), (0.38, 0.99)]
    rings = [ring(rs, cz + crown_h * zh) for rs, zh in prof]
    for k in range(len(prof) - 1):
        join(rings[k], rings[k + 1], 0 if k % 2 == 0 else 1)
    topc = bm.verts.new(Vector((cx, cy, cz + crown_h)))
    for i in range(NS):
        j = (i + 1) % NS
        f = bm.faces.new([rings[-1][i], rings[-1][j], topc])
        f.material_index = 1
        f.smooth = False
    b0 = ring(1.012, cz + 0.002)
    b1 = ring(1.012, cz + crown_h * 0.24)
    join(b0, b1, 2)
    pb = [(1.0, 0.0), (1.0 + brim * 0.35 / Rx, -0.004), (1.0 + brim * 0.70 / Rx, -0.012), (1.0 + brim / Rx, -0.024)]
    br = [ring(rs, cz + dz) for rs, dz in pb]
    for k in range(len(pb) - 1):
        join(br[k], br[k + 1], 0 if k % 2 == 0 else 1)
    under = [ring(rs, cz + dz - 0.004) for rs, dz in pb[::-1]]
    join(br[-1], under[0], 2)
    for k in range(len(under) - 1):
        join(under[k], under[k + 1], 1 if k % 2 == 0 else 0)
    if tilt_back:      # pitch the whole hat so the front of the brim rises, pivoting low on the back of the head
        piv = Vector((cx, cy + hy * 0.75, cz - 0.01))
        th = -math.radians(tilt_back)
        R = Matrix.Rotation(th, 3, 'X')
        for v in bm.verts:
            v.co = piv + R @ (v.co - piv) + Vector((0, 0, -0.02))
    return new_obj(bm, prefix + '_' + name, [mat(prefix + '_HatStraw', straw, 0.0, 0.95), mat(prefix + '_HatStrawB', straw2, 0.0, 0.95), mat(prefix + '_HatBand', band, 0.0, 0.8)])


def mustache(prefix, skin_mesh, base_name, color=(0.30, 0.28, 0.26), name='Mustache', width=0.036, thick=0.0075, droop=0.0045, curl=0.0):
    """Mustache over the upper lip: tapered ribbon with volume, split at the philtrum, tips curling down at the mouth corners; ray-snapped to the skin."""
    pts = A._lip_points(skin_mesh, base_name)
    ztop = max(p.z for p in pts)
    cx = sum(p.x for p in pts) / len(pts)
    tr = tree_of(skin_mesh)
    bm = bmesh.new()
    NX = 18                                   # one continuous strip from tip to tip: no seam, no spike at the philtrum
    prev = None
    tips = []
    prev_mid = None
    for i in range(NX + 1):
        u = (i / NX) * 2.0 - 1.0              # -1 .. 1
        t = abs(u)
        x = cx + u * width
        zc = ztop + 0.0068 - 0.0012 * (1.0 - t) ** 2 - droop * (t ** 1.6) - (0.0 if t < 0.8 else 0.004 * (t - 0.8) / 0.2)
        hh = 0.0058 * (1.0 - 0.45 * t)
        lift_c = thick * (0.62 + 0.38 * t) * (1.0 - 0.55 * t * t)       # slightly thinner at the centre, full bulk on the cheeks, tapering to the tips
        col = []
        for k, dz in enumerate((-hh, 0.0, hh)):
            h = tr.ray_cast(Vector((x, -0.6, zc + dz)), Vector((0, 1, 0)))
            if h[0] is None:
                col = None
                break
            n = h[1].normalized()
            if n.y > 0:
                n = -n
            col.append(h[0] + n * lift_c * (1.0 if k == 1 else 0.55))
        if col is None:
            prev = None
            continue
        if prev is not None:
            for k in range(2):
                q = [bm.verts.new(v) for v in (prev[k], prev[k + 1], col[k + 1], col[k])]
                f = bm.faces.new(q)
                f.material_index = 0
                f.smooth = False
        prev = col
        if curl and i in (0, NX):
            tips.append((1 if i == NX else -1, col, hh))
    for s, c0, hh0 in tips:
        # waxed tip: the strip itself keeps going as a spiral in the XZ plane (outward-up), narrowing, same ribbon section, smooth shaded
        tip = c0[1]
        r0, turns, n = curl, 0.8, 16
        cen = Vector((tip.x, tip.y, tip.z + r0))
        prevc = c0
        for k in range(1, n + 1):
            f = k / n
            th = -math.pi / 2 + f * turns * 2 * math.pi
            r = r0 * (1.0 - 0.6 * f)
            c = Vector((cen.x + s * math.cos(th) * r, tip.y - 0.002 * f, cen.z + math.sin(th) * r))
            f2 = min(1.0, f + 0.02)
            th2 = -math.pi / 2 + f2 * turns * 2 * math.pi
            r2 = r0 * (1.0 - 0.6 * f2)
            t = Vector((s * (math.cos(th2) * r2 - math.cos(th) * r), 0, math.sin(th2) * r2 - math.sin(th) * r)).normalized()
            nrm = Vector((-t.z, 0, t.x)) * s
            w = hh0 * 0.55 * (1.0 - 0.75 * f) + 0.0006
            lift = 0.0045 * (1.0 - 0.7 * f) + 0.0005
            col = [c - nrm * w, c + Vector((0, -lift, 0)), c + nrm * w]
            for kk in range(2):
                q = (prevc[kk], prevc[kk + 1], col[kk + 1], col[kk])
                if s < 0:
                    q = q[::-1]
                f_ = bm.faces.new([bm.verts.new(v) for v in q])
                f_.material_index = 0
                f_.smooth = True
            prevc = col
    bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=1e-5)
    return new_obj(bm, prefix + '_' + name, [mat(prefix + '_MustacheHair', color, 0.0, 0.9)])


def straw_in_mouth(prefix, skin_mesh, base_name, name='Straw', length=0.115, color=(0.86, 0.72, 0.36), tip=(0.70, 0.50, 0.18)):
    """Wheat/straw stalk at the corner of the mouth, angled up and out, with a node and husks at the free end."""
    pts = A._lip_points(skin_mesh, base_name)
    zmid = (max(p.z for p in pts) + min(p.z for p in pts)) / 2
    xs = [p.x for p in pts]
    cx = sum(xs) / len(xs)
    xr = max(xs)
    tr = tree_of(skin_mesh)
    h = tr.ray_cast(Vector((cx + (xr - cx) * 0.55, -0.6, zmid)), Vector((0, 1, 0)))
    start = h[0] + Vector((0, -0.001, 0.0))
    d = Vector((0.66, -0.74, 0.06)).normalized()
    bm = bmesh.new()
    _cone_between(bm, start, start + d * length, 0.0024, 0.0020, 6, 0)
    node = start + d * length * 0.55
    _cone_between(bm, node - d * 0.002, node + d * 0.002, 0.0022, 0.0022, 6, 1)
    end = start + d * length
    side = Vector((0, 0, 1)).cross(d).normalized()
    for k in range(3):
        off = side * (k - 1) * 0.0035
        _cone_between(bm, end - d * 0.006 + off, end + d * 0.016 + off * 1.8, 0.0024, 0.0004, 5, 1)
    return new_obj(bm, prefix + '_' + name, [mat(prefix + '_StrawStalk', color, 0.0, 0.8), mat(prefix + '_StrawTip', tip, 0.0, 0.8)])


def hand_gloves(prefix, skin_mesh, joints, belt_z, x=0.17, y=-0.02, color=(0.55, 0.34, 0.14), cuff=(0.18, 0.28, 0.14), name='Gloves', inflate=0.0035, cuff_len=0.04,
                base_name=None, tris=420, spin=90.0, pair_side=None, pair_gap=0.05):
    """Work gloves modelled from the character's own hand: the hand of the full-resolution base body (real finger shapes, shape keys applied) is copied,
    decimated to a low-poly glove, inflated along its normals, closed at the wrist with a cuff, turned so the fingers point down and hung at the belt."""
    wrist = Vector(joints['wrist'])
    elbow = Vector(joints['elbow'])
    fdir = (wrist - elbow).normalized()
    src = bpy.data.objects[base_name or skin_mesh]
    was_hidden = src.hide_get()
    src.hide_set(False)
    ev = src.evaluated_get(bpy.context.evaluated_depsgraph_get())
    me = bpy.data.meshes.new_from_object(ev)
    src.hide_set(was_hidden)
    bm = bmesh.new()
    bm.from_mesh(me)
    cutz = -cuff_len
    bm.faces.ensure_lookup_table()
    kill = [v for v in bm.verts if not ((v.co - wrist).dot(fdir) > cutz and v.co.x > 0.2)]
    bmesh.ops.delete(bm, geom=kill, context='VERTS')
    # keep only the biggest connected island (the base mesh also carries helper geometry)
    seen, islands = set(), []
    for f0 in bm.faces:
        if f0.index in seen:
            continue
        stack, comp = [f0], []
        seen.add(f0.index)
        while stack:
            f = stack.pop()
            comp.append(f)
            for e in f.edges:
                for nf in e.link_faces:
                    if nf.index not in seen:
                        seen.add(nf.index)
                        stack.append(nf)
        islands.append(comp)
    if islands:
        big = max(islands, key=len)
        keepf = set(f.index for f in big)
        bmesh.ops.delete(bm, geom=[f for f in bm.faces if f.index not in keepf], context='FACES')
        bmesh.ops.delete(bm, geom=[v for v in bm.verts if not v.link_faces], context='VERTS')
    # close the open wrist ring
    bmesh.ops.holes_fill(bm, edges=[e for e in bm.edges if e.is_boundary], sides=64)
    bm.to_mesh(me)
    bm.free()
    tmp = bpy.data.objects.new('_glove_tmp', me)
    bpy.context.collection.objects.link(tmp)
    mod = tmp.modifiers.new('d', 'DECIMATE')
    mod.ratio = min(1.0, tris / max(1, len(me.polygons)))
    dg = bpy.context.evaluated_depsgraph_get()
    me2 = bpy.data.meshes.new_from_object(tmp.evaluated_get(dg))
    bpy.data.objects.remove(tmp)
    bpy.data.meshes.remove(me)
    g = bmesh.new()
    g.from_mesh(me2)
    bmesh.ops.recalc_face_normals(g, faces=g.faces[:])
    g.verts.ensure_lookup_table()
    for v in g.verts:
        v.co = v.co + v.normal * inflate
    for f in g.faces:
        f.material_index = 0 if (f.calc_center_median() - wrist).dot(fdir) > 0.0 else 1
        f.smooth = False
    R1 = fdir.rotation_difference(Vector((0, 0, -1))).to_matrix()
    Rz = Matrix.Rotation(math.radians(spin), 3, 'Z')
    out = bmesh.new()
    layout = [(1, 1, 0.0), (-1, 1, 0.0)] if pair_side is None else [(1, pair_side, 0.0), (-1, pair_side, -pair_gap)]
    for side, pos, dy in layout:      # pair_side=-1: both gloves hang together on the character's right (x<0), one slightly in front of the other
        vm = {}
        for v in g.verts:
            co = Rz @ (R1 @ (v.co - wrist))
            if side < 0:
                co.x = -co.x
            vm[v] = out.verts.new(co + Vector((pos * x, y + dy, belt_z + 0.01)))
        for f in g.faces:
            vs = [vm[v] for v in f.verts]
            if side < 0:
                vs = vs[::-1]
            nf = out.faces.new(vs)
            nf.material_index = f.material_index
            nf.smooth = False
    if pair_side is not None:      # small leather strap + ring joining the two cuffs at the belt
        top = belt_z + 0.01 + 0.01
        for dy, h in ((0.0, 0.03), (-pair_gap, 0.03)):
            for dz in (0.0,):
                pass
        a = Vector((pair_side * x, y, top + 0.012))
        b = Vector((pair_side * x, y - pair_gap, top + 0.012))
        _cone_between(out, a, b, 0.0035, 0.0035, 6, 1)
        _cone_between(out, a + Vector((0, 0, 0.0)), a + Vector((0, 0, 0.03)), 0.0035, 0.0035, 6, 1)
        _cone_between(out, b, b + Vector((0, 0, 0.03)), 0.0035, 0.0035, 6, 1)
    g.free()
    bpy.data.meshes.remove(me2)
    return new_obj(out, prefix + '_' + name, [mat(prefix + '_GloveLeather', color, 0.0, 0.8), mat(prefix + '_GloveCuff', cuff, 0.0, 0.8)])


def apron2(prefix, meshes, z_top, z_bot, neck_z, half_top=0.09, half_hip=0.145, half_bot=0.165, color=(0.82, 0.76, 0.64), trim=(0.62, 0.22, 0.14), band=(0.50, 0.17, 0.11), name='Apron', strap_w=0.014, back_straps=False):
    """Cafe apron: bib with a curved waist taper and a flared skirt, hem band, seam piping along the sides, waist band with a bow at the back, neck loop,
    patch pocket with trim. Every panel point is ray-snapped to the dress (plus a push-out), so nothing sinks into the bust."""
    snap = _snap_fn(meshes)
    push = _outside_pusher(meshes)
    tr = tree_of(meshes[0])
    bm = bmesh.new()
    NX, NZ = 12, 24
    wz = z_top + (z_bot - z_top) * 0.30                                   # waist z (apron seen from the front: bib above, skirt below)

    def half_at(s):
        z = z_top + (z_bot - z_top) * s
        if z > wz:
            t = (z_top - z) / max(z_top - wz, 1e-6)                       # bib: narrow at the chest, slimming a little at the waist
            return half_top * (1.0 - 0.18 * t * t)
        t = (wz - z) / max(wz - z_bot, 1e-6)
        return half_top * 0.82 + (half_bot - half_top * 0.82) * (t ** 0.8)
    rows = []
    for j in range(NZ + 1):
        s = j / NZ
        z = z_top + (z_bot - z_top) * s
        hw = half_at(s)
        row = []
        for i in range(NX + 1):
            x = -hw + 2 * hw * i / NX
            h = tr.ray_cast(Vector((x, -0.8, z)), Vector((0, 1, 0)))
            if h[0] is None:
                row.append(None)
                continue
            n = h[1].normalized()
            if n.y > 0:
                n = -n
            row.append(push(h[0] + n * 0.012, 0.009))
        rows.append(row)
    vv = [[bm.verts.new(v) if v is not None else None for v in r] for r in rows]
    for j in range(NZ):
        for i in range(NX):
            q = [vv[j][i], vv[j][i + 1], vv[j + 1][i + 1], vv[j + 1][i]]
            if any(v is None for v in q):
                continue
            f = bm.faces.new(q)
            hem = (j >= NZ - 2)
            f.material_index = 1 if hem else 0
            f.smooth = False
    # side piping: thin strips along both edges of the panel
    for sx_idx in (0, NX):
        for j in range(NZ):
            a, b = rows[j][sx_idx], rows[j + 1][sx_idx]
            if a is None or b is None:
                continue
            inward = Vector((1 if sx_idx == 0 else -1, 0, 0)) * 0.0045
            q = [bm.verts.new(a + Vector((0, -0.0014, 0))), bm.verts.new(a + inward + Vector((0, -0.0014, 0))), bm.verts.new(b + inward + Vector((0, -0.0014, 0))), bm.verts.new(b + Vector((0, -0.0014, 0)))]
            try:
                f = bm.faces.new(q if sx_idx == 0 else q[::-1])
            except ValueError:
                continue
            f.material_index = 1
            f.smooth = False
    # waist band across the apron
    jw = int(round((wz - z_top) / (z_bot - z_top) * NZ))
    for dj in (0, 1):
        if jw + dj < NZ and rows[jw + dj][0] is not None:
            for i in range(NX):
                a, b = rows[jw + dj][i], rows[jw + dj][i + 1]
                c_, d_ = rows[jw + dj + 1][i + 1], rows[jw + dj + 1][i]
                if None in (a, b, c_, d_):
                    continue
                lift = Vector((0, -0.0022, 0))
                f = bm.faces.new([bm.verts.new(v + lift) for v in (a, b, c_, d_)])
                f.material_index = 2
                f.smooth = False
    # patch pocket with trim
    pz = z_top + (z_bot - z_top) * 0.58
    ph = tr.ray_cast(Vector((0, -0.8, pz)), Vector((0, 1, 0)))
    if ph[0] is not None:
        n = ph[1].normalized()
        if n.y > 0:
            n = -n
        M = frame(n)
        p0 = push(ph[0] + n * 0.0155, 0.0125)
        add_box(bm, M, Vector((0, 0, 0)), (0.118, 0.080, 0.003), 0, p0)
        add_box(bm, M, Vector((0, 0.0385, 0.0018)), (0.118, 0.0065, 0.0016), 1, p0)
        add_box(bm, M, Vector((0, 0, 0.0)), (0.0035, 0.080, 0.0034), 1, p0 + M @ Vector((0, 0, 0.0004)))
    # neck loop: straps from the bib corners over the shoulders and round the back of the neck
    zs = z_top
    for sx in (-1, 1):
        start = rows[0][NX if sx > 0 else 0]
        if start is None:
            continue
        path = [start, Vector((sx * 0.062, -0.06, neck_z - 0.040)), Vector((sx * 0.058, -0.02, neck_z - 0.030)), Vector((sx * 0.056, 0.02, neck_z - 0.032))]       # ends on the shoulder top, hidden under the neck loop
        if back_straps:      # wide straps that go over the shoulder and down the back to the waist ties
            path = [start, Vector((sx * 0.070, -0.07, neck_z - 0.055)), Vector((sx * 0.064, -0.03, neck_z - 0.038)), Vector((sx * 0.060, 0.02, neck_z - 0.042)),
                    Vector((sx * 0.062, 0.07, neck_z - 0.10)), Vector((sx * 0.068, 0.09, neck_z - 0.20)), Vector((sx * 0.074, 0.10, wz + 0.02))]
        pts = strap(meshes, path, strap_w - 0.002, 0.006, relax=3)
        strap_mesh(bm, [(push(q, 0.006), n_) for q, n_ in pts], strap_w, 2)
    # waist ties round the back, finished in a bow
    ring = [Vector((0.2 * math.sin(a), -0.2 * math.cos(a), wz)) for a in [2 * math.pi * k / 36 for k in range(0, 37)]]
    pts = strap(meshes, ring, 0.016, 0.005)
    strap_mesh(bm, [(push(q, 0.006), n_) for q, n_ in pts], 0.018, 2)
    bk = tr.ray_cast(Vector((0, 0.8, wz)), Vector((0, -1, 0)))
    if bk[0] is not None:
        n = bk[1].normalized()
        if n.y < 0:
            n = -n
        M = frame(n)
        c0 = push(bk[0] + n * 0.012, 0.01)
        for sx in (-1, 1):
            add_box(bm, M, Vector((sx * 0.022, 0.002, 0.004)), (0.036, 0.020, 0.008), 2, c0)          # bow loops
            add_box(bm, M, Vector((sx * 0.012, -0.034, 0.002)), (0.012, 0.050, 0.004), 2, c0)         # tails
        add_box(bm, M, Vector((0, 0, 0.007)), (0.014, 0.016, 0.010), 1, c0)                           # knot
    return new_obj(bm, prefix + '_' + name, [mat(prefix + '_ApronCloth', color, 0.0, 0.9), mat(prefix + '_ApronTrim', trim, 0.0, 0.9), mat(prefix + '_ApronBand', band, 0.0, 0.9)])


def shoe_bows(prefix, shoes_name, color=(0.62, 0.10, 0.10), knot=(0.45, 0.06, 0.06), name='ShoeBows'):
    """Small bow on the front of each flat: two loops + knot, placed by ray-casting down onto the instep behind the toe cap."""
    tr = tree_of(shoes_name)
    ob = bpy.data.objects[shoes_name]
    bm = bmesh.new()
    for sd in (-1, 1):
        vs = [v.co for v in ob.data.vertices if v.co.x * sd > 0]
        ytoe = min(v.y for v in vs)
        xc = sum(v.x for v in vs) / len(vs)
        y = ytoe + 0.050
        h = tr.ray_cast(Vector((xc, y, 0.3)), Vector((0, 0, -1)))
        if h[0] is None:
            continue
        n = h[1].normalized()
        if n.z < 0:
            n = -n
        M = frame(n)
        p0 = h[0] + n * 0.002
        for s2 in (-1, 1):
            add_box(bm, M, Vector((s2 * 0.0105, 0.0, 0.0045)), (0.016, 0.011, 0.007), 0, p0)
            add_box(bm, M, Vector((s2 * 0.0185, 0.0, 0.0035)), (0.007, 0.014, 0.005), 0, p0)
        add_box(bm, M, Vector((0, 0, 0.0055)), (0.007, 0.010, 0.0075), 1, p0)
    return new_obj(bm, prefix + '_' + name, [mat(prefix + '_BowCloth', color, 0.0, 0.8), mat(prefix + '_BowKnot', knot, 0.0, 0.8)])
