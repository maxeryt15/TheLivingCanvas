"""Gentleman props: suit details, rich pocket watch, detailed buttons, eye scar, texture patterns (pinstripes)."""
import bpy, bmesh, math
from mathutils import Vector, Matrix
import npc_details as D
from npc_details import mat, new_obj, add_box, add_cyl, frame, tree_of
from npc_props import _cone_between, strap, strap_mesh, _outside_pusher


def _surf(tr, x, z, off=0.0):
    h = tr.ray_cast(Vector((x, -0.8, z)), Vector((0, 1, 0)))
    if h[0] is None:
        return None, None
    n = h[1].normalized()
    if n.y > 0:
        n = -n
    return h[0] + n * off, n


def suit_buttons(cloth, prefix, zs, x=0.0, color=(0.30, 0.17, 0.07), rim=(0.72, 0.58, 0.28), radius=0.0115, name='Buttons'):
    """Four-hole horn buttons with a gold-ish rim ring, a raised dish and a stitched cross of thread; sit on the placket line."""
    tr = tree_of(cloth)
    bm = bmesh.new()
    for z in zs:
        p, n = _surf(tr, x, z, 0.0006)
        if p is None:
            continue
        M = frame(n)
        add_cyl(bm, M, Vector((0, 0, 0.0016)), radius, 0.0032, 1, 12, p)                       # rim ring
        add_cyl(bm, M, Vector((0, 0, 0.0040)), radius * 0.82, 0.0024, 0, 12, p)                # dish
        for dx, dy in ((-0.0032, -0.0032), (0.0032, -0.0032), (-0.0032, 0.0032), (0.0032, 0.0032)):
            add_cyl(bm, M, Vector((dx, dy, 0.0054)), 0.0011, 0.0010, 2, 6, p)                  # thread holes
        add_box(bm, M, Vector((0, 0, 0.0056)), (0.0075, 0.0009, 0.0007), 2, p)                 # thread cross
        add_box(bm, M, Vector((0, 0, 0.0056)), (0.0009, 0.0075, 0.0007), 2, p)
    return new_obj(bm, prefix + '_' + name, [mat(prefix + '_ButtonHorn', color, 0.1, 0.5), mat(prefix + '_ButtonRim', rim, 0.9, 0.35), mat(prefix + '_ButtonThread', (0.05, 0.04, 0.03), 0.0, 0.8)])


def suit_details(prefix, cloth, z_chest, z_waist, lapel_apex, lapel_top, x_off=0.085, square_on=True, cloth_col=(0.20, 0.12, 0.055), trim=(0.10, 0.06, 0.03), square=(0.93, 0.90, 0.80), square2=(0.55, 0.12, 0.14), name='SuitDetails'):
    """Welt breast pocket with a folded pocket square (white with a dark-red fold), two flap pockets with piping and buttons, lapel stitch lines and a buttonhole,
    elbow patches. Everything is ray-snapped onto the jacket."""
    tr = tree_of(cloth)
    bm = bmesh.new()
    # breast pocket (wearer's left = x<0 on screen right; keep it on the character's left chest = +x? the jacket front faces -y, character's left is +x)
    p, n = _surf(tr, x_off, z_chest, 0.0045)
    if p is not None:
        M = frame(n)
        add_box(bm, M, Vector((0, 0, 0)), (0.092, 0.020, 0.0035), 1, p)                          # welt
        add_box(bm, M, Vector((0, 0.0105, 0.0)), (0.092, 0.0018, 0.0042), 1, p)                  # welt edge line
        # pocket square: a folded handkerchief with three layered points (tall, medium, short), each a thin triangular prism, slightly fanned, with a coloured border line
        def prism(base_x, h, w, tilt, mi, lift):
            ang = math.radians(tilt)
            ax = Vector((math.sin(ang), math.cos(ang), 0.0))          # direction of the point in the pocket plane
            side = Vector((math.cos(ang), -math.sin(ang), 0.0))
            b0 = Vector((base_x, 0.002, 0.0))
            tri = [b0 - side * w / 2, b0 + side * w / 2, b0 + ax * h]
            th = 0.0030
            lo = [bm.verts.new(p + M @ (q + Vector((0, 0, 0.0038 + lift)))) for q in tri]
            hi = [bm.verts.new(p + M @ (q + Vector((0, 0, 0.0038 + lift + th)))) for q in tri]
            bm.faces.new(hi).material_index = mi
            bm.faces.new(lo[::-1]).material_index = mi
            for i in range(3):
                j = (i + 1) % 3
                bm.faces.new([lo[i], lo[j], hi[j], hi[i]]).material_index = mi
            # coloured border along the two long edges of the point
            for (qa, qb) in ((tri[0], tri[2]), (tri[1], tri[2])):
                for_ = (qb - qa)
                nrm = Vector((-for_.y, for_.x, 0.0)).normalized() * 0.0011
                quad = [bm.verts.new(p + M @ (qa + Vector((0, 0, 0.0038 + lift + th + 0.0003)))), bm.verts.new(p + M @ (qb + Vector((0, 0, 0.0038 + lift + th + 0.0003)))),
                        bm.verts.new(p + M @ (qb + nrm + Vector((0, 0, 0.0038 + lift + th + 0.0003)))), bm.verts.new(p + M @ (qa + nrm + Vector((0, 0, 0.0038 + lift + th + 0.0003))))]
                try:
                    bm.faces.new(quad).material_index = 3
                except ValueError:
                    pass
        if square_on:
            prism(-0.014, 0.026, 0.030, -14.0, 2, 0.0)
            prism(0.002, 0.032, 0.034, 0.0, 2, 0.0014)
            prism(0.018, 0.023, 0.028, 16.0, 2, 0.0028)
    # lower flap pockets with piping and a small button
    for sx in (-1, 1):
        p, n = _surf(tr, sx * 0.105, z_waist, 0.0045)
        if p is None:
            continue
        M = frame(n)
        add_box(bm, M, Vector((0, 0, 0)), (0.108, 0.034, 0.0038), 0, p + M @ Vector((0, 0.0, 0.0)))            # flap
        add_box(bm, M, Vector((0, -0.0195, 0.0)), (0.110, 0.0032, 0.0046), 1, p)                         # flap bottom piping
        add_box(bm, M, Vector((0, 0.0175, -0.0018)), (0.108, 0.0020, 0.0034), 1, p)                      # top seam shadow line
        add_cyl(bm, M, Vector((0, -0.002, 0.0032)), 0.0046, 0.0022, 3, 8, p)                              # small flap button (thread colour)
    # lapel stitch: dotted line a little inside each lapel edge
    for sx in (-1, 1):
        for i in range(14):
            t = (i + 0.5) / 14
            z = lapel_top + (lapel_apex - lapel_top) * t
            xc = sx * (0.056 * (1 - t) + 0.010 * t) * 1.0 + sx * 0.012
            p, n = _surf(tr, xc, z, 0.0022)
            if p is None:
                continue
            M = frame(n)
            add_box(bm, M, Vector((0, 0, 0)), (0.0018, 0.0075, 0.0009), 1, p)
    # elbow patches would need the arm surface: skipped when the suit has short sleeves
    mats = [mat(prefix + '_SuitFlap', cloth_col, 0.0, 0.9), mat(prefix + '_SuitPiping', trim, 0.0, 0.9), mat(prefix + '_PocketSquare', square, 0.0, 0.8), mat(prefix + '_PocketSquareFold', square2, 0.0, 0.8)]
    return new_obj(bm, prefix + '_' + name, mats)


def pocket_watch2(prefix, cloth, x_button, z_button, x_pocket, z_pocket, gold=(0.82, 0.68, 0.38), name='PocketWatch'):
    """Pocket watch on a double-link chain: T-bar at the button, a curved chain made of alternating links, a fob medallion, and the watch with a bow (crown ring),
    crown, bezel ring, cream dial with hour ticks and hands lying on the vest/jacket."""
    tr = tree_of(cloth)
    bm = bmesh.new()
    push = _outside_pusher([cloth])
    # T-bar through the buttonhole
    p0, n0 = _surf(tr, x_button, z_button, 0.0045)
    if p0 is not None:
        M0 = frame(n0)
        add_box(bm, M0, Vector((0, 0, 0)), (0.020, 0.0030, 0.0030), 0, p0)
        add_cyl(bm, M0, Vector((-0.0105, 0, 0)), 0.0042, 0.0034, 0, 8, p0)
    # chain: catenary between button and pocket, built from links
    N = 22
    chain = []
    for i in range(N + 1):
        s = i / N
        x = x_button + (x_pocket - x_button) * s
        z = z_button + (z_pocket - z_button) * s - 0.020 * math.sin(math.pi * s)
        chain.append(Vector((x, -0.7, z)))
    pts = []
    for q in chain:
        p, n = _surf(tr, q.x, q.z, 0.0055)
        if p is not None:
            pts.append((p, n))
    for i in range(len(pts) - 1):
        a, b = pts[i][0], pts[i + 1][0]
        n = pts[i][1]
        mid = (a + b) / 2
        d = (b - a)
        if d.length < 1e-5:
            continue
        side = d.cross(n).normalized()
        s0 = 0.0030 if i % 2 == 0 else 0.0018
        _cone_between(bm, mid - d * 0.5, mid + d * 0.5, s0, s0, 6, 0)
        if i % 2 == 1:
            _cone_between(bm, mid + side * 0.0015 - d * 0.35, mid + side * 0.0015 + d * 0.35, 0.0011, 0.0011, 5, 0)
    # fob medallion hanging from the middle of the chain
    if len(pts) > 6:
        mp, mn = pts[len(pts) // 2]
        Mf = frame(mn)
        add_cyl(bm, Mf, Vector((0, -0.020, 0.0)), 0.0085, 0.0034, 0, 10, mp)
        add_cyl(bm, Mf, Vector((0, -0.020, 0.0023)), 0.0055, 0.0010, 1, 8, mp)
        _cone_between(bm, mp, mp + Mf @ Vector((0, -0.012, 0.0)), 0.0010, 0.0010, 4, 0)
    # the watch in the pocket
    pw, nw = _surf(tr, x_pocket, z_pocket, 0.0065)
    if pw is not None:
        Mw = frame(nw)
        R = 0.0175
        add_cyl(bm, Mw, Vector((0, 0, 0.0)), R, 0.0075, 0, 16, pw)                         # case
        add_cyl(bm, Mw, Vector((0, 0, 0.0043)), R * 0.84, 0.0016, 1, 16, pw)                # dial (cream)
        add_cyl(bm, Mw, Vector((0, 0, 0.0038)), R * 1.02, 0.0020, 0, 16, pw)                # bezel ring
        for k in range(12):                                                                  # hour ticks
            a = math.pi * 2 * k / 12
            tk = Vector((math.sin(a) * R * 0.70, math.cos(a) * R * 0.70, 0.0056))
            add_box(bm, Mw, tk, (0.0013 if k % 3 else 0.0020, 0.0040 if k % 3 == 0 else 0.0025, 0.0004), 2, pw)
        add_box(bm, Mw, Vector((0.0, 0.0055, 0.0057)), (0.0014, 0.0120, 0.0005), 2, pw)    # minute hand
        add_box(bm, Mw, Vector((0.0045, 0.0, 0.0057)), (0.0100, 0.0016, 0.0005), 2, pw)    # hour hand
        add_cyl(bm, Mw, Vector((0, R + 0.0025, 0.0)), 0.0034, 0.0045, 0, 8, pw)             # crown
        _cone_between(bm, pw + Mw @ Vector((0, R + 0.0010, 0.0)), pw + Mw @ Vector((0, R + 0.0065, 0.0)), 0.0042, 0.0042, 8, 0)
        add_cyl(bm, Mw, Vector((0, R + 0.0075, 0.0)), 0.0060, 0.0014, 0, 10, pw)           # bow ring
    return new_obj(bm, prefix + '_' + name, [mat(prefix + '_ChainGold', gold, 1.0, 0.3), mat(prefix + '_PocketWatchBezel', (0.95, 0.80, 0.45), 1.0, 0.25), mat(prefix + '_PocketWatchFace', (0.93, 0.90, 0.80), 0.0, 0.4)])


def eye_scar(skin_name, eyes_name, out_name, side=1, color=(0.92, 0.88, 0.84, 1), width=0.0011, lift=0.0009):
    """Pale scar crossing one eye vertically, slightly slanted: from above the brow, over the eyelid and eyeball, down the cheek. Ray-cast on skin AND eye mesh, nearest hit wins."""
    import npc_accessories as A
    old = bpy.data.objects.get(out_name)
    if old:
        bpy.data.objects.remove(old)
    cl, cr = A.eye_centres(eyes_name)
    c = cl if (cl.x > 0) == (side > 0) else cr
    trs = [A._tree(skin_name), A._tree(eyes_name)]
    path = [(c.x - 0.006 * side, c.z + 0.034), (c.x - 0.003 * side, c.z + 0.018), (c.x - 0.0005 * side, c.z + 0.006), (c.x + 0.0015 * side, c.z - 0.004),
            (c.x + 0.004 * side, c.z - 0.016), (c.x + 0.007 * side, c.z - 0.030)]
    dense = []
    for (xa, za), (xb, zb) in zip(path, path[1:]):
        for k in range(5):
            dense.append((xa + (xb - xa) * k / 5, za + (zb - za) * k / 5))
    dense.append(path[-1])
    L, R = [], []
    for i, (x, z) in enumerate(dense):
        xa, za = dense[max(i - 1, 0)]
        xb, zb = dense[min(i + 1, len(dense) - 1)]
        tx, tz = xb - xa, zb - za
        ln = math.hypot(tx, tz) or 1.0
        w = width * (0.45 + 0.55 * math.sin(math.pi * i / (len(dense) - 1)))
        px, pz = -tz / ln * w, tx / ln * w
        for sd, lst in ((1, L), (-1, R)):
            best = None
            for t in trs:
                h = t.ray_cast(Vector((x + sd * px, -0.6, z + sd * pz)), Vector((0, 1, 0)))
                if h[0] is not None and (best is None or h[0].y < best[0].y):
                    best = h
            n = best[1].normalized()
            if n.y > 0:
                n = -n
            lst.append(best[0] + n * lift)
    bm = bmesh.new()
    for i in range(len(dense) - 1):
        f = bm.faces.new([bm.verts.new(v) for v in (L[i], R[i], R[i + 1], L[i + 1])])
        f.smooth = False
    me = bpy.data.meshes.new(out_name)
    bm.to_mesh(me)
    bm.free()
    o = bpy.data.objects.new(out_name, me)
    bpy.context.collection.objects.link(o)
    o.data.materials.append(mat(out_name + '_Mat', color))
    return o


def paint_pattern(img, obj_name, zones, seed=2):
    """Paint a procedural pattern into a baked garment texture by walking every UV triangle and evaluating the pattern at the world position of each texel.
    zones: [dict(zmin, zmax, fn=lambda x, y, z -> alpha (0..1), color=(r,g,b))]."""
    import numpy as np
    o = bpy.data.objects[obj_name]
    me = o.data
    uvd = me.uv_layers.active.data
    W, H = img.size
    px = np.empty(W * H * 4, dtype=np.float32)
    img.pixels.foreach_get(px)
    px = px.reshape(H, W, 4)
    for p_ in me.polygons:
        loops = list(p_.loop_indices)
        if len(loops) < 3:
            continue
        vs = [me.vertices[me.loops[l].vertex_index].co for l in loops]
        uvs = [uvd[l].uv for l in loops]
        cz = p_.center.z
        zs = [z for z in zones if z['zmin'] <= cz <= z['zmax']]
        if not zs:
            continue
        for i in range(1, len(loops) - 1):
            a, b, c = vs[0], vs[i], vs[i + 1]
            ua, ub, uc = uvs[0], uvs[i], uvs[i + 1]
            x0 = int(min(ua[0], ub[0], uc[0]) * (W - 1))
            x1 = int(max(ua[0], ub[0], uc[0]) * (W - 1)) + 1
            y0 = int(min(ua[1], ub[1], uc[1]) * (H - 1))
            y1 = int(max(ua[1], ub[1], uc[1]) * (H - 1)) + 1
            if x1 <= x0 or y1 <= y0:
                continue
            yy, xx = np.mgrid[y0:y1 + 1, x0:x1 + 1]
            u = xx / (W - 1.0)
            v = yy / (H - 1.0)
            den = (ub[1] - uc[1]) * (ua[0] - uc[0]) + (uc[0] - ub[0]) * (ua[1] - uc[1])
            if abs(den) < 1e-12:
                continue
            w1 = ((ub[1] - uc[1]) * (u - uc[0]) + (uc[0] - ub[0]) * (v - uc[1])) / den
            w2 = ((uc[1] - ua[1]) * (u - uc[0]) + (ua[0] - uc[0]) * (v - uc[1])) / den
            w3 = 1 - w1 - w2
            inside = (w1 >= -0.02) & (w2 >= -0.02) & (w3 >= -0.02)
            X = w1 * a.x + w2 * b.x + w3 * c.x
            Y = w1 * a.y + w2 * b.y + w3 * c.y
            Z = w1 * a.z + w2 * b.z + w3 * c.z
            for zn in zs:
                al = zn['fn'](X, Y, Z) * inside
                ok = (yy < H) & (xx < W)
                col = np.array(zn['color'], dtype=np.float32)
                sub = px[y0:y1 + 1, x0:x1 + 1, :3] if False else None
                ys, xs = np.nonzero(ok & (al > 0.01))
                for yi, xi in zip(ys, xs):
                    Y_, X_ = y0 + yi, x0 + xi
                    if Y_ < H and X_ < W:
                        w = float(al[yi, xi])
                        px[Y_, X_, :3] = px[Y_, X_, :3] * (1 - w) + col * w
    img.pixels.foreach_set(px.reshape(-1))
    img.update()


def leather_patches(prefix, cloth, joints, color=(0.26, 0.135, 0.06), stitch=(0.10, 0.055, 0.03), name='Patches', elbow=(0.062, 0.092), shoulder=(0.046, 0.066)):
    """Brown leather patches on both sleeves: oval elbow patches on the outside of the elbow and oval shoulder patches on the top of the shoulder, each a snapped oval of rings
    (follows the sleeve surface), with a dashed stitch ring just inside the edge."""
    tr = tree_of(cloth)
    bm = bmesh.new()

    def oval(centre, ray_dir, U, V, ru, rv, lift=0.0042):
        n_r, n_s = 4, 18
        grid = []
        ctr_hit = tr.ray_cast(centre - ray_dir * 0.35, ray_dir)
        for ir in range(n_r + 1):
            rr = ir / n_r
            ring = []
            for isec in range(n_s):
                a = 2 * math.pi * isec / n_s
                pnt = centre + U * (math.cos(a) * ru * rr) + V * (math.sin(a) * rv * rr)
                h = tr.ray_cast(pnt - ray_dir * 0.35, ray_dir)
                if h[0] is None:
                    ring.append(None)
                    continue
                n = h[1].normalized()
                if n.dot(ray_dir) > 0:
                    n = -n
                ring.append(h[0] + n * (lift + (0.0010 if ir == n_r else 0.0)))
            grid.append(ring)
        for ir in range(n_r):
            for isec in range(n_s):
                j = (isec + 1) % n_s
                q = [grid[ir][isec], grid[ir][j], grid[ir + 1][j], grid[ir + 1][isec]]
                if any(v is None for v in q) and ir > 0:
                    continue
                if ir == 0:
                    q = [grid[0][0], grid[1][isec], grid[1][j]]
                    if any(v is None for v in q):
                        continue
                f = bm.faces.new([bm.verts.new(v) for v in q])
                f.material_index = 0
                f.smooth = False
                # reversed copy so it shows from both sides
        # stitch dashes inside the rim
        for isec in range(0, n_s, 1):
            a = 2 * math.pi * (isec + 0.5) / n_s
            for rs, step in ((0.82, 0.12),):
                pa = centre + U * (math.cos(a - step) * ru * rs) + V * (math.sin(a - step) * rv * rs)
                pb = centre + U * (math.cos(a + step * 0.2) * ru * rs) + V * (math.sin(a + step * 0.2) * rv * rs)
                ha = tr.ray_cast(pa - ray_dir * 0.35, ray_dir)
                hb = tr.ray_cast(pb - ray_dir * 0.35, ray_dir)
                if ha[0] is None or hb[0] is None:
                    continue
                na = ha[1].normalized() if ha[1].dot(ray_dir) < 0 else -ha[1].normalized()
                A_ = ha[0] + na * (lift + 0.0016)
                B_ = hb[0] + na * (lift + 0.0016)
                d = B_ - A_
                if d.length < 1e-5:
                    continue
                sd = d.cross(na).normalized() * 0.0008
                f = bm.faces.new([bm.verts.new(v) for v in (A_ + sd, A_ - sd, B_ - sd, B_ + sd)])
                f.material_index = 1
                f.smooth = False
    for sx in (1, -1):
        el = Vector((joints['elbow'].x * sx, joints['elbow'].y, joints['elbow'].z))
        wr = Vector((joints['wrist'].x * sx, joints['wrist'].y, joints['wrist'].z))
        sh = Vector((joints['shoulder'].x * sx, joints['shoulder'].y, joints['shoulder'].z))
        arm = (wr - el).normalized()
        # elbow: on the back of the elbow, ray from behind (+y) towards the front
        ray = Vector((0, -1, 0))
        U = arm.cross(ray).normalized()
        V = arm
        oval(el + Vector((0, 0.05, 0)), ray, U, V, elbow[0], elbow[1])
        # shoulder: top of the shoulder, ray downwards, long axis along the arm direction (horizontal)
        top = Vector((0, 0, -1))
        armh = (el - sh)
        armh.z = 0
        armh = armh.normalized()
        U2 = armh
        V2 = Vector((0, 1, 0))
        oval(Vector((sh.x + armh.x * 0.015, sh.y, sh.z + 0.05)), top, U2, V2, shoulder[1], shoulder[0])
    return new_obj(bm, prefix + '_' + name, [mat(prefix + '_PatchLeather', color, 0.0, 0.75), mat(prefix + '_PatchStitch', stitch, 0.0, 0.8)])
