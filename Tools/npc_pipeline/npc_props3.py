"""Tourist props: travel camera, sandals built around the real feet, palm-tree motif painter."""
import bpy, bmesh, math, random
from mathutils import Vector, Matrix
import npc_details as D
from npc_details import mat, new_obj, add_box, add_cyl, frame, tree_of
from npc_props import _cone_between, strap, strap_mesh, _snap_fn, _outside_pusher


def travel_camera(prefix, meshes, neck_z, chest_z, strap_col=(0.70, 0.12, 0.12), body=(0.045, 0.045, 0.05), silver=(0.72, 0.73, 0.76), name='Camera'):
    """Compact travel camera on a neck strap: leatherette body with a silver top plate, right-hand grip, zoom lens with rings and hood, flash, viewfinder, shutter, mode dial,
    strap lugs. Hangs flat on the chest; the strap runs from the lugs round the back of the neck over the shoulders."""
    tr = tree_of(meshes[0])
    push = _outside_pusher(meshes)
    h = tr.ray_cast(Vector((0, -0.8, chest_z)), Vector((0, 1, 0)))
    n = h[1].normalized()
    if n.y > 0:
        n = -n
    M = frame(n)
    p = h[0] + n * 0.012
    W, Hh, Dp = 0.118, 0.072, 0.040
    bm = bmesh.new()
    O = Vector((0, 0, 0))
    add_box(bm, M, Vector((0, 0, Dp / 2)), (W, Hh, Dp), 0, p)                                   # body
    add_box(bm, M, Vector((0, Hh / 2 - 0.006, Dp / 2)), (W + 0.002, 0.012, Dp + 0.002), 1, p)  # silver top band
    add_box(bm, M, Vector((0, -Hh / 2 + 0.004, Dp / 2)), (W + 0.002, 0.008, Dp + 0.002), 1, p)  # silver bottom band
    add_box(bm, M, Vector((W / 2 - 0.011, -0.004, Dp + 0.0035)), (0.022, Hh - 0.022, 0.007), 0, p)   # grip bulge (right side of the camera)
    add_box(bm, M, Vector((W / 2 - 0.011, -0.004, Dp + 0.0075)), (0.016, Hh - 0.028, 0.0015), 2, p)  # grip texture strip
    # lens: base ring, barrel, zoom ring, front element, hood
    lc = Vector((-0.012, -0.002, Dp))
    add_cyl(bm, M, lc + Vector((0, 0, 0.003)), 0.0305, 0.006, 1, 14, p)
    add_cyl(bm, M, lc + Vector((0, 0, 0.012)), 0.0265, 0.014, 0, 14, p)
    add_cyl(bm, M, lc + Vector((0, 0, 0.021)), 0.0285, 0.006, 1, 14, p)
    add_cyl(bm, M, lc + Vector((0, 0, 0.028)), 0.0235, 0.010, 0, 14, p)
    add_cyl(bm, M, lc + Vector((0, 0, 0.0345)), 0.0255, 0.003, 1, 14, p)
    add_cyl(bm, M, lc + Vector((0, 0, 0.0362)), 0.0185, 0.003, 3, 12, p)
    add_cyl(bm, M, lc + Vector((0.0, 0.0, 0.0376)), 0.0095, 0.0014, 4, 10, p)                       # glass highlight ring
    # top: viewfinder hump, flash, shutter, dial, hot shoe
    add_box(bm, M, Vector((-0.012, Hh / 2 + 0.006, Dp / 2 + 0.002)), (0.040, 0.012, 0.030), 1, p)
    add_box(bm, M, Vector((-0.012, Hh / 2 + 0.010, Dp / 2 + 0.002)), (0.030, 0.004, 0.022), 0, p)
    add_box(bm, M, Vector((0.034, Hh / 2 + 0.004, Dp / 2 - 0.006)), (0.020, 0.008, 0.016), 0, p)          # flash housing
    add_box(bm, M, Vector((0.034, Hh / 2 + 0.0055, Dp - 0.002)), (0.016, 0.005, 0.0016), 4, p)           # flash window
    d1 = M @ Vector((-0.040, Hh / 2 + 0.005, Dp / 2 - 0.006))
    _cone_between(bm, p + d1 - M.to_3x3() @ Vector((0, 0.004, 0)), p + d1 + M.to_3x3() @ Vector((0, 0.003, 0)), 0.0075, 0.0075, 10, 2)           # mode dial
    d2 = M @ Vector((0.050, Hh / 2 + 0.004, Dp / 2 + 0.010))
    _cone_between(bm, p + d2 - M.to_3x3() @ Vector((0, 0.003, 0)), p + d2 + M.to_3x3() @ Vector((0, 0.005, 0)), 0.0062, 0.0055, 8, 2)            # shutter button
    add_box(bm, M, Vector((-0.040, 0.0, Dp + 0.001)), (0.012, 0.010, 0.002), 4, p)                         # AF lamp
    add_box(bm, M, Vector((0.030, 0.012, Dp + 0.001)), (0.014, 0.011, 0.002), 3, p)                        # optical finder window
    # strap lugs
    lugs = []
    for sx in (-1, 1):
        lug = p + M @ Vector((sx * (W / 2 + 0.004), Hh / 2 - 0.010, Dp / 2))
        add_box(bm, M, Vector((sx * (W / 2 + 0.0025), Hh / 2 - 0.010, Dp / 2)), (0.006, 0.010, 0.010), 1, p)
        lugs.append(lug)
    # neck strap: lugs -> up the chest -> over the shoulders -> back of the neck
    tn = tree_of(meshes[0])
    sk = tree_of(meshes[-1])
    zn = neck_z - 0.012
    ring = [v.co for v in bpy.data.objects[meshes[-1]].data.vertices if abs(v.co.z - zn) < 0.02 and abs(v.co.x) < 0.10]
    cen = Vector((0.0, (min(v.y for v in ring) + max(v.y for v in ring)) / 2, zn))
    back = []
    for k in range(0, 15):
        th = math.pi - math.pi * k / 14
        d = Vector((math.cos(th), math.sin(th), 0.0))
        best = None
        for t in (tn, sk):
            hh = t.ray_cast(cen, d, 0.16)
            if hh[0] is not None and (best is None or (hh[0] - cen).length < (best[0] - cen).length):
                best = hh
        back.append((best[0] + best[1].normalized() * 0.008) if best else cen + d * 0.07)
    zs = neck_z - 0.040
    left = [lugs[0].lerp(Vector((back[0].x - 0.012, -0.075, zs)), s / 6.0) for s in range(7)]
    right = [lugs[1].lerp(Vector((back[-1].x + 0.012, -0.075, zs)), s / 6.0) for s in range(7)]
    path = left + back + right[::-1]
    pts = strap(meshes, path, 0.016, 0.006, relax=4)
    pts = [(push(q, 0.006), n_) for q, n_ in pts]
    m_ = len(pts)
    for i in range(m_ // 2):          # the garment is not perfectly symmetric: build one side and mirror it so both straps match exactly
        q, n_ = pts[m_ - 1 - i]
        pts[i] = (Vector((-q.x, q.y, q.z)), Vector((-n_.x, n_.y, n_.z)))
    pts[0] = (Vector((-lugs[1].x, lugs[1].y, lugs[1].z)), pts[0][1])
    pts[-1] = (lugs[1], pts[-1][1])
    strap_mesh(bm, pts, 0.016, 5)
    mats = [mat(prefix + '_CamBody', body, 0.2, 0.55), mat(prefix + '_CamSilver', silver, 0.9, 0.3), mat(prefix + '_CamGrip', (0.02, 0.02, 0.025), 0.0, 0.9),
            mat(prefix + '_CamGlass', (0.03, 0.07, 0.16), 0.0, 0.05), mat(prefix + '_CamGlint', (0.75, 0.80, 0.90), 0.0, 0.2), mat(prefix + '_CamStrap', strap_col, 0.0, 0.8)]
    return new_obj(bm, prefix + '_' + name, mats)


def _hull(pts):
    pts = sorted(set(pts))
    if len(pts) < 3:
        return pts

    def cross(o, a, b):
        return (a[0] - o[0]) * (b[1] - o[1]) - (a[1] - o[1]) * (b[0] - o[0])
    lo = []
    for q in pts:
        while len(lo) >= 2 and cross(lo[-2], lo[-1], q) <= 0:
            lo.pop()
        lo.append(q)
    up = []
    for q in reversed(pts):
        while len(up) >= 2 and cross(up[-2], up[-1], q) <= 0:
            up.pop()
        up.append(q)
    return lo[:-1] + up[:-1]


def sandals(prefix, skin_mesh, sole=(0.12, 0.55, 0.62), footbed=(0.88, 0.80, 0.62), strap_col=(0.85, 0.30, 0.22), strap2=(0.95, 0.76, 0.22), name='Sandals', thick=0.016):
    """Flat sandals built around the real feet: sole = outline of the foot (convex hull, grown a little), two-tone (sole + footbed), a forefoot strap, an instep strap
    and a heel strap that wraps the ankle; all straps follow the skin surface."""
    low = bpy.data.objects[skin_mesh]
    tr = tree_of(skin_mesh)
    bm = bmesh.new()
    for sd in (-1, 1):
        fv = [v.co for v in low.data.vertices if v.co.x * sd > 0.04 and v.co.z < 0.09]
        low_pts = [(v.x, v.y) for v in fv if v.z < 0.04]
        hull = _hull(low_pts)
        cx = sum(q[0] for q in hull) / len(hull)
        cy = sum(q[1] for q in hull) / len(hull)
        grown = [(cx + (q[0] - cx) * 1.10 + 0.0, cy + (q[1] - cy) * 1.07) for q in hull]
        zb = max(0.0, min(v.z for v in fv) - 0.002)
        ztop = zb + thick
        # sole slab
        bot = [bm.verts.new(Vector((x, y, zb))) for x, y in grown]
        mid = [bm.verts.new(Vector((x, y, zb + thick * 0.6))) for x, y in grown]
        top = [bm.verts.new(Vector((x * 0.985 + cx * 0.015, y * 0.985 + cy * 0.015, ztop))) for x, y in grown]
        nn = len(grown)
        for i in range(nn):
            j = (i + 1) % nn
            f = bm.faces.new([bot[i], bot[j], mid[j], mid[i]])
            f.material_index = 0
            f.smooth = False
            f = bm.faces.new([mid[i], mid[j], top[j], top[i]])
            f.material_index = 1
            f.smooth = False
        cb = bm.verts.new(Vector((cx, cy, zb)))
        ct = bm.verts.new(Vector((cx, cy, ztop)))
        for i in range(nn):
            j = (i + 1) % nn
            f = bm.faces.new([bot[j], bot[i], cb])
            f.material_index = 0
            f.smooth = False
            f = bm.faces.new([top[i], top[j], ct])
            f.material_index = 1
            f.smooth = False
        ys = [q[1] for q in grown]
        ytoe, yheel = min(ys), max(ys)
        xs = [q[0] for q in grown]
        xl, xr = min(xs), max(xs)

        def skin_top(x, y, fallback):
            hh = tr.ray_cast(Vector((x, y, 0.35)), Vector((0, 0, -1)))
            if hh[0] is not None and hh[0].z < 0.14:
                return hh[0].z + 0.0045
            return fallback

        def ribbon(y, width, mi, lift=0.0):
            row = []
            for i in range(15):
                x = xl + 0.002 + (xr - xl - 0.004) * i / 14
                z = skin_top(x, y, ztop + 0.001) + lift
                row.append(Vector((x, y, max(z, ztop + 0.001))))
            for a, b in zip(row, row[1:]):
                q = [bm.verts.new(a + Vector((0, -width / 2, 0))), bm.verts.new(a + Vector((0, width / 2, 0))), bm.verts.new(b + Vector((0, width / 2, 0))), bm.verts.new(b + Vector((0, -width / 2, 0)))]
                for order in (q, [bm.verts.new(v.co) for v in q[::-1]]):
                    f = bm.faces.new(order)
                    f.material_index = mi
                    f.smooth = False
        ribbon(ytoe + (yheel - ytoe) * 0.30, 0.016, 2)
        ribbon(ytoe + (yheel - ytoe) * 0.50, 0.013, 3)
        # heel strap around the back of the ankle
        zc = ztop + 0.045
        ctr = Vector((cx, yheel - 0.05, zc))
        arc = []
        for k in range(0, 13):
            a = math.radians(-100 + 200 * k / 12)         # sweep round the back
            d = Vector((math.sin(a), math.cos(a), 0.0))
            hh = tr.ray_cast(ctr, d, 0.12)
            r = (hh[0] - ctr).length + 0.0045 if hh[0] is not None else 0.045
            arc.append(ctr + d * r)
        for a, b in zip(arc, arc[1:]):
            q = [bm.verts.new(a + Vector((0, 0, -0.007))), bm.verts.new(a + Vector((0, 0, 0.007))), bm.verts.new(b + Vector((0, 0, 0.007))), bm.verts.new(b + Vector((0, 0, -0.007)))]
            for order in (q, [bm.verts.new(v.co) for v in q[::-1]]):
                f = bm.faces.new(order)
                f.material_index = 2
                f.smooth = False
        for end in (arc[0], arc[-1]):          # tabs joining the heel strap to the sole
            for t in (0.0, 1.0):
                pass
            q = [bm.verts.new(end + Vector((0, 0, -0.007))), bm.verts.new(end + Vector((0, 0, 0.007))), bm.verts.new(Vector((end.x, end.y, ztop + 0.001))), bm.verts.new(Vector((end.x, end.y, ztop + 0.001)))]
    return new_obj(bm, prefix + '_' + name, [mat(prefix + '_SandalSole', sole, 0.0, 0.8), mat(prefix + '_SandalFoot', footbed, 0.0, 0.8), mat(prefix + '_SandalStrapA', strap_col, 0.0, 0.8), mat(prefix + '_SandalStrapB', strap2, 0.0, 0.8)])


def paint_motifs(img, obj_name, zones, seed=11):
    """Stamp small motifs (palm trees) into a baked garment texture. Each stamp is drawn in the tangent plane of a random surface point (world-up stays up),
    mapped to UV through the local UV Jacobian, so the palms are upright and sized in metres."""
    import numpy as np
    rnd = random.Random(seed)
    o = bpy.data.objects[obj_name]
    me = o.data
    uvd = me.uv_layers.active.data
    W, H = img.size
    px = np.empty(W * H * 4, dtype=np.float32)
    img.pixels.foreach_get(px)
    px = px.reshape(H, W, 4)

    def disc(cx, cy, r, col, a=1.0):
        r_i = int(r) + 1
        y0, y1, x0, x1 = max(0, int(cy) - r_i), min(H, int(cy) + r_i + 1), max(0, int(cx) - r_i), min(W, int(cx) + r_i + 1)
        if y0 >= y1 or x0 >= x1:
            return
        yy, xx = np.mgrid[y0:y1, x0:x1]
        m = (((xx - cx) ** 2 + (yy - cy) ** 2) <= r * r)[..., None]
        px[y0:y1, x0:x1, :3] = np.where(m, np.array(col, dtype=np.float32) * a + px[y0:y1, x0:x1, :3] * (1 - a), px[y0:y1, x0:x1, :3])

    def line(p0, p1, r, col):
        n = int(max(abs(p1[0] - p0[0]), abs(p1[1] - p0[1]))) + 1
        for k in range(n + 1):
            t = k / max(n, 1)
            disc(p0[0] + (p1[0] - p0[0]) * t, p0[1] + (p1[1] - p0[1]) * t, r, col)
    polys = []
    for p_ in me.polygons:
        loops = list(p_.loop_indices)
        if len(loops) < 3:
            continue
        pos = [me.vertices[me.loops[l].vertex_index].co for l in loops[:3]]
        uvs = [uvd[l].uv.copy() for l in loops[:3]]
        e1, e2 = pos[1] - pos[0], pos[2] - pos[0]
        nrm = e1.cross(e2)
        if nrm.length < 1e-10:
            continue
        nn = nrm.normalized()
        A = Matrix(((e1.x, e2.x, nn.x), (e1.y, e2.y, nn.y), (e1.z, e2.z, nn.z)))
        try:
            Ai = A.inverted()
        except ValueError:
            continue
        polys.append((p_, loops, pos, uvs, Ai, nrm.length / 2, nn))
    for z in zones:
        sel = [e for e in polys if z['zmin'] <= e[0].center.z <= z['zmax'] and (z.get('front') is None or ((e[0].center.y < 0) == z['front']))]
        if not sel:
            continue
        weights = [e[5] for e in sel]
        for _ in range(z['count']):
            e = rnd.choices(sel, weights)[0]
            p_, loops, pos, uvs, Ai, area, nn = e
            r1, r2 = rnd.random(), rnd.random()
            if r1 + r2 > 1:
                r1, r2 = 1 - r1, 1 - r2
            uvc = uvs[0] + (uvs[1] - uvs[0]) * r1 + (uvs[2] - uvs[0]) * r2

            def to_px(dx, dz, e=e, uvc=uvc, Ai=Ai, nn=nn):
                right = Vector((0, 0, 1)).cross(nn)
                if right.length < 1e-6:
                    right = Vector((1, 0, 0))
                right.normalize()
                up = nn.cross(right)
                if up.z < 0:
                    up = -up
                v3 = right * dx + up * dz
                c = Ai @ v3
                uvv = uvc + (e[3][1] - e[3][0]) * c[0] + (e[3][2] - e[3][0]) * c[1]
                return (uvv[0] * (W - 1), uvv[1] * (H - 1))
            s = z.get('size', 0.05) * rnd.uniform(0.85, 1.15)
            lw = max(1.2, s * 0.045 * W / 1.0 * 0.5)
            # trunk (slight curve)
            base = (0.0, 0.0)
            bend = rnd.uniform(-0.18, 0.18) * s
            prev = to_px(*base)
            for k in range(1, 7):
                t = k / 6
                cur = to_px(bend * t * t, s * 0.62 * t)
                line(prev, cur, lw * 0.75, z['trunk'])
                prev = cur
            top = (bend, s * 0.62)
            for a_deg, ln in ((-150, 0.45), (-110, 0.52), (-70, 0.52), (-30, 0.45), (-175, 0.30), (-5, 0.30)):     # fronds drooping from the crown
                a = math.radians(a_deg)
                pts = []
                for k in range(0, 6):
                    t = k / 5
                    fx = top[0] + math.cos(a + math.pi) * s * ln * t * -1
                    fz = top[1] + math.sin(-a * 0 + math.radians(40)) * s * ln * t * (1 - t * 1.3)
                    pts.append(to_px(top[0] + (math.cos(math.radians(a_deg + 180)) * s * ln) * t, top[1] + (s * ln * 0.45) * math.sin(math.pi * t) - (s * ln * 0.55) * t * t))
                for q0, q1 in zip(pts, pts[1:]):
                    line(q0, q1, lw * 0.8, z['leaf'])
            for dxc, dzc in ((-0.012, -0.012), (0.012, -0.012)):
                c = to_px(top[0] + dxc * s * 8, top[1] - 0.025 * s * 4)
                disc(c[0], c[1], lw * 0.9, z.get('nut', z['trunk']))
    img.pixels.foreach_set(px.reshape(-1))
    img.update()
