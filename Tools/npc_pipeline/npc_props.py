"""Job/personality props for NPCs: hats, bags, straps, apron, camera, headphones, glasses on head, pocket watch, radio, brush, gloves...
All faceted, flat shaded, built in world space on the final low-poly meshes (rest pose). Every function returns the new object.
"""
import bpy, bmesh, math
from mathutils import Vector, Matrix
import npc_details as D
from npc_details import mat, new_obj, add_box, add_cyl, frame, tree_of


def bounds(name):
    o = bpy.data.objects[name]
    vs = [o.matrix_world @ v.co for v in o.data.vertices]
    return (Vector((min(v.x for v in vs), min(v.y for v in vs), min(v.z for v in vs))), Vector((max(v.x for v in vs), max(v.y for v in vs), max(v.z for v in vs))))


def _snap_fn(meshes):
    ts = [tree_of(n) for n in meshes]

    def snap(p, off):
        best = None
        for t in ts:
            loc, nor, idx, dist = t.find_nearest(p)
            if loc is not None and (best is None or dist < best[0]):
                best = (dist, loc, nor.normalized())
        return best[1] + best[2] * off, best[2]
    return snap


def strap(meshes, path, width, off=0.003, relax=4):
    """Ribbon following `path` (world points) lying on the outermost of `meshes`. Returns (rows, snapped pts). Double sided."""
    snap = _snap_fn(meshes)
    pts = [snap(p, off) for p in path]
    for _ in range(relax):
        new = [pts[0]]
        for i in range(1, len(pts) - 1):
            new.append(snap(pts[i][0].lerp((pts[i - 1][0] + pts[i + 1][0]) / 2, 0.5), off))
        new.append(pts[-1])
        pts = new
    return pts


def strap_mesh(bm, pts, width, mi):
    rows = []
    for i, (p, n) in enumerate(pts):
        a = pts[max(i - 1, 0)][0]
        b = pts[min(i + 1, len(pts) - 1)][0]
        side = (b - a).normalized().cross(n).normalized() * (width / 2)
        rows.append((p + side, p - side))
    for a, b in zip(rows, rows[1:]):
        quad = [bm.verts.new(v) for v in (a[0], a[1], b[1], b[0])]
        for order in (quad, [bm.verts.new(v.co) for v in quad[::-1]]):
            f = bm.faces.new(order)
            f.material_index = mi
            f.smooth = False


def _head_info(hair):
    lo, hi = bounds(hair)
    return Vector(((lo.x + hi.x) / 2, (lo.y + hi.y) / 2, hi.z)), (hi.x - lo.x) / 2, (hi.y - lo.y) / 2, lo.z


# ------------------------------------------------------------------------------------------------- headwear
def sun_hat(prefix, hair, straw=(0.62, 0.45, 0.18), band=(0.08, 0.2, 0.1), name='Hat', brim=0.115, crown_h=0.075):
    top, hx, hy, lowz = _head_info(hair)
    bm = bmesh.new()
    cz = top.z - 0.075
    R = max(hx, hy) + 0.012
    M = Matrix.Identity(4)
    add_cyl(bm, M, Vector((0, 0, 0)), R, crown_h, 0, 14, Vector((top.x, top.y, cz + crown_h / 2)), r2=R * 0.88)
    # brim: flat ring made of a very short wide cone
    add_cyl(bm, M, Vector((0, 0, 0)), R + brim, 0.006, 0, 18, Vector((top.x, top.y, cz + 0.002)), r2=R + brim * 0.97)
    add_cyl(bm, M, Vector((0, 0, 0)), R + 0.003, 0.016, 1, 14, Vector((top.x, top.y, cz + 0.012)), r2=R + 0.003)
    return new_obj(bm, prefix + '_' + name, [mat(prefix + '_HatStraw', straw, 0.0, 0.9), mat(prefix + '_HatBand', band, 0.0, 0.8)])


def baseball_cap(prefix, hair, color=(0.10, 0.25, 0.45), brim_color=(0.06, 0.12, 0.25), name='Cap'):
    top, hx, hy, lowz = _head_info(hair)
    bm = bmesh.new()
    R = max(hx, hy) + 0.024   # icosphere facets sit inside the nominal radius, so the dome needs margin or hair/skin poke through
    cz = top.z - 0.085
    M = Matrix.Identity(4)
    # dome: hemisphere from an icosphere, lower half removed
    g = bmesh.ops.create_icosphere(bm, subdivisions=3, radius=1.0)
    for v in g['verts']:
        v.co = Vector((v.co.x * R, v.co.y * R * 1.04, v.co.z * (R * 1.0))) + Vector((top.x, top.y, cz))
    bmesh.ops.delete(bm, geom=[f for f in bm.faces if f.calc_center_median().z < cz - 0.005], context='FACES')
    for f in bm.faces:
        f.material_index = 0
        f.smooth = False
    # visor: wide flat wedge at the front (-y)
    vy = top.y - R * 1.04
    add_box(bm, M, Vector((0, 0, 0)), (R * 1.25, 0.085, 0.009), 1, Vector((top.x, vy - 0.035, cz + 0.004)))
    return new_obj(bm, prefix + '_' + name, [mat(prefix + '_CapCloth', color, 0.0, 0.9), mat(prefix + '_CapVisor', brim_color, 0.0, 0.7)])


def beret(prefix, hair, color=(0.45, 0.10, 0.12), name='Beret', extra=0.025):
    top, hx, hy, lowz = _head_info(hair)
    bm = bmesh.new()
    R = max(hx, hy) + extra
    g = bmesh.ops.create_icosphere(bm, subdivisions=2, radius=1.0)
    ctr = Vector((top.x + 0.012, top.y - 0.005, top.z - 0.035))
    tilt = Matrix.Rotation(math.radians(8), 3, 'Y')
    for v in g['verts']:
        v.co = ctr + tilt @ Vector((v.co.x * R, v.co.y * R * 1.02, v.co.z * 0.055))
    for f in bm.faces:
        f.material_index = 0
        f.smooth = False
    add_cyl(bm, Matrix.Identity(4), Vector((0, 0, 0)), 0.006, 0.014, 1, 6, ctr + Vector((0, 0, 0.055)))
    return new_obj(bm, prefix + '_' + name, [mat(prefix + '_BeretWool', color, 0.0, 0.95), mat(prefix + '_BeretTip', (0.05, 0.03, 0.03), 0.0, 0.8)])


def sunglasses_on_head(prefix, hair, frame_col=(0.04, 0.04, 0.05), lens=(0.05, 0.10, 0.12), name='SunglassesHead'):
    top, hx, hy, lowz = _head_info(hair)
    bm = bmesh.new()
    M = Matrix.Identity(4)
    y = top.y - hy * 0.55
    z = top.z - 0.006
    for sx in (-1, 1):
        add_box(bm, M, Vector((0, 0, 0)), (0.050, 0.008, 0.036), 1, Vector((sx * 0.033, y - 0.03, z - 0.03)))
        add_box(bm, M, Vector((0, 0, 0)), (0.042, 0.004, 0.028), 0, Vector((sx * 0.033, y - 0.035, z - 0.03)))
    add_box(bm, M, Vector((0, 0, 0)), (0.012, 0.008, 0.006), 1, Vector((0, y - 0.03, z - 0.022)))
    return new_obj(bm, prefix + '_' + name, [mat(prefix + '_Lens', lens, 0.0, 0.2), mat(prefix + '_SunFrame', frame_col, 0.0, 0.5)])


def brush_behind_ear(prefix, hair, side=1, name='Brush', handle=(0.55, 0.30, 0.12), tip=(0.9, 0.2, 0.15), ear_z=None, ear_y=-0.02, direction=(0.30, 0.30, 0.90)):
    """Paint brush tucked behind the ear, angled up and back like a pencil behind the ear."""
    top, hx, hy, lowz = _head_info(hair)
    bm = bmesh.new()
    ez = ear_z if ear_z is not None else top.z - 0.095
    p0 = Vector((side * (hx * 0.93), top.y + ear_y, ez))
    z = Vector((side * direction[0], direction[1], direction[2])).normalized()
    x = Vector((1, 0, 0))
    y = z.cross(x).normalized()
    x = y.cross(z)
    M = Matrix(((x.x, y.x, z.x), (x.y, y.y, z.y), (x.z, y.z, z.z))).to_4x4()
    add_cyl(bm, M, Vector((0, 0, 0)), 0.0048, 0.115, 0, 6, p0 + z * 0.0)
    add_cyl(bm, M, Vector((0, 0, 0)), 0.0042, 0.026, 2, 6, p0 + z * 0.07)
    add_cyl(bm, M, Vector((0, 0, 0)), 0.0042, 0.024, 1, 6, p0 + z * 0.095, r2=0.001)
    return new_obj(bm, prefix + '_' + name, [mat(prefix + '_BrushHandle', handle, 0.0, 0.6), mat(prefix + '_BrushTip', tip, 0.0, 0.7), mat(prefix + '_BrushFerrule', (0.7, 0.7, 0.72), 1.0, 0.4)])


# ------------------------------------------------------------------------------------------------- body props
def bag_with_strap(prefix, meshes, shoulder_x, hip_z, shoulder_z, bag_w=0.24, bag_h=0.17, bag_d=0.07, color=(0.55, 0.36, 0.16), strap_col=(0.35, 0.22, 0.10), side=1, name='Bag', hip_x=0.19):
    """Cross-body bag: strap from the `side` shoulder, over chest and back, to the opposite hip where the bag hangs against the hip."""
    snap = _snap_fn(meshes)
    sx = side * shoulder_x
    hx = -side * hip_x
    N = 14
    front, back = [], []
    for i in range(N + 1):
        s = i / N
        x = sx + (hx - sx) * s
        z = shoulder_z + (hip_z - shoulder_z) * s
        front.append(Vector((x, -0.16 * (1 - s), z)))
        back.append(Vector((x, 0.16 * (1 - s), z)))
    bm = bmesh.new()
    strap_mesh(bm, strap(meshes, front, 0.03, 0.004), 0.03, 1)
    strap_mesh(bm, strap(meshes, back, 0.03, 0.004), 0.03, 1)
    # bag on the hip side surface
    loc, nor = snap(Vector((hx * 0.9, 0.0, hip_z)), 0.0)
    nx = 1.0 if nor.x > 0 else -1.0
    cen = Vector((loc.x + nx * (bag_d / 2 + 0.012), loc.y, hip_z - bag_h * 0.45))
    M = Matrix.Identity(4)
    add_box(bm, M, Vector((0, 0, 0)), (bag_d, bag_w, bag_h), 0, cen)
    add_box(bm, M, Vector((0, 0, 0)), (bag_d + 0.006, bag_w + 0.004, bag_h * 0.42), 2, cen + Vector((0, 0, bag_h * 0.30)))
    add_box(bm, M, Vector((0, 0, 0)), (0.008, 0.028, 0.024), 3, cen + Vector((nx * (bag_d / 2 + 0.006), 0, bag_h * 0.1)))
    add_box(bm, M, Vector((0, 0, 0)), (bag_d * 0.9, bag_w * 0.55, 0.004), 1, cen + Vector((0, 0, bag_h * 0.5 + 0.002)))   # top strap handle base
    return new_obj(bm, prefix + '_' + name, [mat(prefix + '_BagCanvas', color, 0.0, 0.85), mat(prefix + '_BagStrap', strap_col, 0.0, 0.8), mat(prefix + '_BagFlap', tuple(c * 0.82 for c in color), 0.0, 0.85), mat(prefix + '_BagBuckle', (0.82, 0.68, 0.38), 1.0, 0.35)])


def camera_on_neck(prefix, meshes, neck_z, chest_z, half=0.065, strap_col=(0.05, 0.05, 0.06), body=(0.07, 0.07, 0.08), accent=(0.75, 0.12, 0.10), name='Camera'):
    """Strap around the neck (like the lanyard) and a compact camera hanging on the chest."""
    cy = -0.03
    N = 9
    left = [Vector((-half * (s ** 1.2), -0.20, chest_z + 0.03 + (neck_z - chest_z - 0.03) * s)) for s in [i / N for i in range(N + 1)]]
    back = [Vector((-half * math.cos(math.pi * k / 12), cy + 0.085 * math.sin(math.pi * k / 12) + 0.02, neck_z + 0.012)) for k in range(1, 12)]
    right = [Vector((-p.x, p.y, p.z)) for p in reversed(left)]
    pts = strap(meshes, left + back + right, 0.015, 0.0033)
    bm = bmesh.new()
    strap_mesh(bm, pts, 0.016, 0)
    snap = _snap_fn(meshes)
    h = tree_of(meshes[0]).ray_cast(Vector((0, -0.8, chest_z)), Vector((0, 1, 0)))
    n = h[1].normalized()
    p = h[0] + n * 0.003
    M = frame(n)
    add_box(bm, M, Vector((0, 0, 0.0155)), (0.105, 0.068, 0.031), 1, p)            # body
    add_box(bm, M, Vector((0, 0.0, 0.0315)), (0.105, 0.068, 0.004), 2, p + Vector((0, 0, 0)))   # accent top plate
    add_cyl(bm, M, Vector((0.012, 0, 0.040)), 0.024, 0.026, 1, 12, p)              # lens barrel
    add_cyl(bm, M, Vector((0.012, 0, 0.0545)), 0.017, 0.004, 3, 12, p)             # glass
    add_box(bm, M, Vector((-0.04, 0.02, 0.034)), (0.016, 0.012, 0.010), 2, p)      # shutter button
    return new_obj(bm, prefix + '_' + name, [mat(prefix + '_CamStrap', strap_col, 0.0, 0.8), mat(prefix + '_CamBody', body, 0.2, 0.5), mat(prefix + '_CamAccent', accent, 0.0, 0.6), mat(prefix + '_CamGlass', (0.04, 0.08, 0.14), 0.0, 0.1)])


def apron(prefix, meshes, z_top, z_bot, half_top=0.085, half_bot=0.13, color=(0.78, 0.74, 0.62), trim=(0.15, 0.22, 0.30), name='Apron', neck_z=None):
    """Apron panel following the front surface (ray grid), neck strap to the back of the neck and waist ties."""
    t = tree_of(meshes[0])
    snap = _snap_fn(meshes)
    bm = bmesh.new()
    NX, NZ = 9, 16
    rows = []
    for j in range(NZ + 1):
        s = j / NZ
        z = z_top + (z_bot - z_top) * s
        half = half_top + (half_bot - half_top) * s
        row = []
        for i in range(NX + 1):
            x = -half + 2 * half * i / NX
            p, n = snap(Vector((x, -0.25, z)), 0.0) if False else (None, None)
            h = t.ray_cast(Vector((x, -0.8, z)), Vector((0, 1, 0)))
            if h[0] is None:
                row.append(None)
                continue
            nn = h[1].normalized()
            row.append(bm.verts.new(h[0] + nn * 0.011))
        rows.append(row)
    for j in range(NZ):
        for i in range(NX):
            q = [rows[j][i], rows[j][i + 1], rows[j + 1][i + 1], rows[j + 1][i]]
            if any(v is None for v in q):
                continue
            f = bm.faces.new(q)
            f.material_index = 1 if (j == NZ - 1) else 0
            f.smooth = True
    # pocket on the panel
    zc = z_top + (z_bot - z_top) * 0.62
    h = t.ray_cast(Vector((0, -0.8, zc)), Vector((0, 1, 0)))
    if h[0] is not None:
        n = h[1].normalized()
        M = frame(n)
        add_box(bm, M, Vector((0, 0, 0)), (0.115, 0.075, 0.0028), 1, h[0] + n * 0.0075)
    # neck strap + waist ties
    if neck_z is not None:
        for sx in (-1, 1):
            path = [Vector((sx * half_top * (1 - s) + sx * 0.05 * s, -0.20 + 0.19 * s, z_top + (neck_z - z_top) * s)) for s in [i / 8 for i in range(9)]]
            strap_mesh(bm, strap(meshes, path, 0.012, 0.004), 0.014, 1)
    wz = z_top + (z_bot - z_top) * 0.30
    path = [Vector((half_top * 1.2 * math.cos(a), -0.2 * math.cos(a) * 0 + 0.20 * math.sin(a) - 0.0, wz)) for a in [math.pi * 1.5 + math.pi * k / 20 for k in range(0, 21)]]
    ring = [Vector((0.2 * math.sin(a), -0.2 * math.cos(a), wz)) for a in [2 * math.pi * k / 30 for k in range(0, 31)]]
    strap_mesh(bm, strap(meshes, ring, 0.016, 0.004), 0.016, 1)
    return new_obj(bm, prefix + '_' + name, [mat(prefix + '_ApronCloth', color, 0.0, 0.9), mat(prefix + '_ApronTrim', trim, 0.0, 0.9)])


def _outside_pusher(meshes):
    """push(p, clear): keep a point outside every mesh in `meshes`. Normal orientation is decided per query as 'away from the body axis'
    (garments are open shells with unreliable winding)."""
    ts = [tree_of(n) for n in meshes]

    def push(p, clear=0.004):
        for _ in range(3):
            for t in ts:
                loc, nor, _, d = t.find_nearest(p)
                if loc is None or d > 0.03:
                    continue
                n = nor.normalized()
                if n.dot(Vector((loc.x, loc.y + 0.01, 0.0))) < 0:
                    n = -n
                if (p - loc).dot(n) < clear:
                    p = loc + n * clear
        return p
    return push


def headphones_on_neck(prefix, meshes, neck_z, color=(0.08, 0.08, 0.09), accent=(0.9, 0.5, 0.1), name='Headphones'):
    """Headphones resting round the neck: the band runs behind the neck (never across the throat), arms come forward over the collarbones to the cups on the chest."""
    push = _outside_pusher(meshes)
    snap = _snap_fn(meshes)
    zn = neck_z - 0.012
    tee = bpy.data.objects[meshes[0]]
    ring = [v.co for v in tee.data.vertices if abs(v.co.z - zn) < 0.02 and abs(v.co.x) < 0.10]
    cen = Vector((0.0, (min(v.y for v in ring) + max(v.y for v in ring)) / 2, zn))
    t_tee = tree_of(meshes[0])
    t_skin = tree_of(meshes[-1])
    back = []
    for k in range(0, 15):                              # from the left side of the neck, behind, to the right side
        th = math.pi - math.pi * k / 14
        d = Vector((math.cos(th), math.sin(th), 0.0))
        best = None
        for t in (t_tee, t_skin):
            h = t.ray_cast(cen, d, 0.16)
            if h[0] is not None and (best is None or (h[0] - cen).length < (best[0] - cen).length):
                best = h
        back.append((best[0] + best[1].normalized() * 0.008) if best else cen + d * 0.07)
    bm = bmesh.new()
    cups = []
    for sx in (-1, 1):
        h = t_tee.ray_cast(Vector((sx * 0.07, -0.8, neck_z - 0.050)), Vector((0, 1, 0)))
        cups.append((sx, h))
    path = []
    left = [c for c in cups if c[0] == -1][0][1]
    right = [c for c in cups if c[0] == 1][0][1]
    # left arm: cup -> collarbone -> side of the neck -> band
    def arm(h, sx):
        pc = h[0] + h[1].normalized() * 0.016
        side = back[0] if sx < 0 else back[-1]
        mid = pc.lerp(side, 0.5) + Vector((0, -0.012, 0.01))
        return [pc, pc.lerp(mid, 0.5), mid, mid.lerp(side, 0.5)]
    la = arm(left, -1)
    ra = arm(right, 1)
    path = la + back + ra[::-1]
    pts = []
    for q in path:
        q = push(q, 0.007)
        pts.append((q, snap(q, 0.0)[1]))
    strap_mesh(bm, pts, 0.014, 0)
    for sx, h in cups:
        n = h[1].normalized()
        M = frame(n)
        add_cyl(bm, M, Vector((0, 0, 0)), 0.029, 0.026, 0, 10, h[0] + n * 0.014)
        add_cyl(bm, M, Vector((0, 0, 0.0135)), 0.021, 0.004, 1, 10, h[0] + n * 0.014)
    return new_obj(bm, prefix + '_' + name, [mat(prefix + '_PhonesBody', color, 0.1, 0.5), mat(prefix + '_PhonesAccent', accent, 0.0, 0.5)])


def pocket_watch(prefix, meshes, x_button, z_button, x_pocket, z_pocket, name='PocketWatch', gold=(0.82, 0.68, 0.38)):
    t = tree_of(meshes[0])
    bm = bmesh.new()
    pts = []
    for i in range(9):
        s = i / 8
        x = x_button + (x_pocket - x_button) * s
        z = z_button + (z_pocket - z_button) * s - 0.022 * math.sin(math.pi * s)
        pts.append(Vector((x, -0.7, z)))
    sp = []
    for p in pts:
        h = t.ray_cast(p, Vector((0, 1, 0)))
        if h[0] is None:
            continue
        sp.append((h[0] + h[1].normalized() * 0.004, h[1].normalized()))
    strap_mesh(bm, sp, 0.0035, 0)
    h = t.ray_cast(Vector((x_pocket, -0.7, z_pocket)), Vector((0, 1, 0)))
    if h[0] is not None:
        n = h[1].normalized()
        M = frame(n)
        add_cyl(bm, M, Vector((0, 0, 0)), 0.014, 0.006, 0, 12, h[0] + n * 0.005)
        add_cyl(bm, M, Vector((0, 0, 0.0033)), 0.011, 0.0012, 1, 12, h[0] + n * 0.005)
    return new_obj(bm, prefix + '_' + name, [mat(prefix + '_ChainGold', gold, 1.0, 0.35), mat(prefix + '_PocketWatchFace', (0.92, 0.9, 0.82), 0.0, 0.4)])


def _cone_between(bm, a, b, r1, r2, seg, mi):
    """Cone/cylinder from point a (radius r1) to point b (radius r2)."""
    axis = b - a
    z = axis.normalized()
    x = z.cross(Vector((0, 0, 1)))
    if x.length < 1e-4:
        x = z.cross(Vector((1, 0, 0)))
    x = x.normalized()
    y = z.cross(x)
    R = Matrix(((x.x, y.x, z.x), (x.y, y.y, z.y), (x.z, y.z, z.z)))
    r = bmesh.ops.create_cone(bm, cap_ends=True, segments=seg, radius1=r1, radius2=r2, depth=axis.length)
    for v in r['verts']:
        v.co = (a + b) / 2 + R @ v.co
    for f in {f for v in r['verts'] for f in v.link_faces}:
        f.material_index = mi
        f.smooth = False


def chest_radio(prefix, meshes, x, z, name='Radio', body=(0.06, 0.06, 0.07), accent=(0.8, 0.12, 0.1)):
    """Shoulder/chest two-way radio: chamfered body, display, speaker slits, emergency + function buttons, side PTT key, volume knob, tapered antenna."""
    t = tree_of(meshes[0])
    h = t.ray_cast(Vector((x, -0.8, z)), Vector((0, 1, 0)))
    n = h[1].normalized()
    M = frame(n)
    bm = bmesh.new()
    p = h[0] + n * 0.0035
    L = lambda v: p + M @ v
    add_box(bm, M, Vector((0, 0, 0.010)), (0.056, 0.100, 0.020), 0, p)                      # body
    add_box(bm, M, Vector((0, 0, 0.0215)), (0.050, 0.094, 0.003), 0, p)                      # chamfer step
    add_box(bm, M, Vector((0, 0.034, 0.0235)), (0.032, 0.016, 0.0012), 2, p)                 # display
    for k in range(5):                                                                        # speaker slits
        add_box(bm, M, Vector((0, 0.012 - k * 0.0062, 0.0232)), (0.034, 0.0024, 0.0012), 3, p)
    add_box(bm, M, Vector((0.0, -0.030, 0.0238)), (0.013, 0.011, 0.003), 1, p)               # emergency button
    for sx in (-1, 1):
        add_box(bm, M, Vector((sx * 0.013, -0.041, 0.0236)), (0.009, 0.007, 0.0026), 4, p)    # function keys
    add_box(bm, M, Vector((-0.0295, 0.014, 0.012)), (0.005, 0.030, 0.011), 4, p)             # side PTT key
    _cone_between(bm, L(Vector((-0.015, 0.050, 0.011))), L(Vector((-0.015, 0.0585, 0.011))), 0.0065, 0.0060, 8, 4)   # volume knob
    _cone_between(bm, L(Vector((0.018, 0.050, 0.011))), L(Vector((0.018, 0.057, 0.011))), 0.0068, 0.0062, 8, 4)      # antenna collar
    _cone_between(bm, L(Vector((0.018, 0.057, 0.011))), L(Vector((0.021, 0.140, 0.026))), 0.0050, 0.0034, 6, 0)      # antenna (leans out so it clears the lapel)
    add_box(bm, M, Vector((0.0, -0.002, -0.002)), (0.030, 0.050, 0.006), 4, p)               # belt-clip plate on the back
    return new_obj(bm, prefix + '_' + name, [mat(prefix + '_RadioBody', body, 0.1, 0.5), mat(prefix + '_RadioButton', accent, 0.0, 0.5), mat(prefix + '_RadioScreen', (0.15, 0.5, 0.35), 0.0, 0.3),
                                           mat(prefix + '_RadioGrille', (0.012, 0.012, 0.015), 0.0, 0.8), mat(prefix + '_RadioKey', (0.30, 0.30, 0.32), 0.1, 0.6)])


def tie(prefix, meshes, z_top, z_bot, color=(0.02, 0.03, 0.10), dots=(0.30, 0.38, 0.55), name='Tie', x=0.0, v_limit=None, pattern='dots', stripe2=None):
    """Necktie lying on the chest: knot, narrow neck, blade widening then pointed tip, following the surface (ray grid) with polka dots."""
    tr = tree_of(meshes[0])
    bm = bmesh.new()
    NZ, NX = (40, 6) if pattern != 'dots' else (16, 4)
    prof = [(0.0, 0.016), (0.07, 0.017), (0.13, 0.011), (0.20, 0.011), (0.30, 0.016), (0.55, 0.021), (0.80, 0.0235), (0.93, 0.016), (1.0, 0.0)]

    def half(s):
        for (s0, h0), (s1, h1) in zip(prof, prof[1:]):
            if s0 <= s <= s1:
                return h0 + (h1 - h0) * (s - s0) / (s1 - s0)
        return 0.0

    rows = []
    for j in range(NZ + 1):
        s = j / NZ
        z = z_top + (z_bot - z_top) * s
        hw = half(s)
        if v_limit:   # never wider than the jacket opening (apex z, top z, half width at top)
            za, zt, ht = v_limit
            hw = max(0.0, min(hw, ht * (z - za) / (zt - za) - 0.0035))
        row = []
        for i in range(NX + 1):
            xx = x - hw + 2 * hw * i / NX
            hh = tr.ray_cast(Vector((xx, -0.8, z)), Vector((0, 1, 0)))
            if hh[0] is None:
                row.append(None)
                continue
            nn = hh[1].normalized()
            off = 0.0075 if s < 0.12 else 0.0055
            row.append(hh[0] + nn * off)
        rows.append(row)
    bmrows = []
    for r in rows:
        bmrows.append([bm.verts.new(v) if v is not None else None for v in r])
    for j in range(NZ):
        for i in range(NX):
            q = [bmrows[j][i], bmrows[j][i + 1], bmrows[j + 1][i + 1], bmrows[j + 1][i]]
            if any(v is None for v in q):
                continue
            try:
                f = bm.faces.new(q)
            except ValueError:
                continue
            f.material_index = 0
            if pattern == 'bands':      # horizontal bands across the blade: clean at any resolution
                bj = j % 8
                f.material_index = 1 if bj in (2, 3) else (2 if (stripe2 and bj in (5,)) else 0)
            if pattern == 'diag':      # regimental diagonal stripes: two stripe colours over the base
                band = (j * 0.45 + i * 1.0) % 5.0
                f.material_index = 1 if band < 1.1 else (2 if (stripe2 and 2.6 <= band < 3.3) else 0)
            f.smooth = False
    # polka dots on the blade
    def at(u, v):
        j = min(int(v * NZ), NZ - 1)
        fv = v * NZ - j
        i = min(int(u * NX), NX - 1)
        fu = u * NX - i
        a, b, c, d = rows[j][i], rows[j][i + 1], rows[j + 1][i + 1], rows[j + 1][i]
        if None in (a, b, c, d):
            return None, None
        top = a.lerp(b, fu)
        bot = d.lerp(c, fu)
        pt = top.lerp(bot, fv)
        nrm = (b - a).cross(d - a)
        if nrm.length < 1e-9:
            return None, None
        nrm = nrm.normalized()
        if nrm.y > 0:
            nrm = -nrm
        return pt, nrm
    k = 0
    for v in ([] if pattern != 'dots' else [0.34 + 0.085 * m for m in range(7)]):
        cols = [0.25, 0.5, 0.75] if k % 2 == 0 else [0.37, 0.63]
        k += 1
        for u in cols:
            hw = half(v)
            if v_limit:
                zz = z_top + (z_bot - z_top) * v
                hw = min(hw, v_limit[2] * (zz - v_limit[0]) / (v_limit[1] - v_limit[0]) - 0.0035)
            if hw < 0.0165 or v > 0.9:
                continue
            u2 = 0.5 + (u - 0.5) * min(1.0, hw / 0.021)
            pt, nrm = at(u2, v)
            if pt is None:
                continue
            M = frame(nrm)
            add_cyl(bm, M, Vector((0, 0, 0)), 0.0034, 0.0008, 1, 6, pt + nrm * 0.0007)
    return new_obj(bm, prefix + '_' + name, [mat(prefix + '_TieSilk', color, 0.0, 0.6), mat(prefix + '_TieDots', dots, 0.0, 0.6), mat(prefix + '_TieStripe2', stripe2 or dots, 0.0, 0.6)])


def gloves_on_belt(prefix, meshes, z, x=0.17, name='Gloves', color=(0.62, 0.45, 0.20), cuff=(0.2, 0.3, 0.15)):
    t = tree_of(meshes[0])
    bm = bmesh.new()
    for sx in (1,):
        h = t.ray_cast(Vector((sx * x, -0.8, z)), Vector((0, 1, 0)))
        if h[0] is None:
            h = t.ray_cast(Vector((sx * x * 0.8, -0.8, z)), Vector((0, 1, 0)))
        n = h[1].normalized()
        M = frame(n)
        p = h[0] + n * 0.003
        for k, dx in enumerate((-0.012, 0.012)):
            add_box(bm, M, Vector((dx, -0.03, 0.007)), (0.034, 0.10, 0.014), 0, p)
            add_box(bm, M, Vector((dx, 0.032, 0.008)), (0.036, 0.022, 0.016), 1, p)
            for f_ in range(4):
                add_box(bm, M, Vector((dx + (f_ - 1.5) * 0.0085, -0.088, 0.007)), (0.0075, 0.04, 0.011), 0, p)
    return new_obj(bm, prefix + '_' + name, [mat(prefix + '_GloveLeather', color, 0.0, 0.8), mat(prefix + '_GloveCuff', cuff, 0.0, 0.8)])


def wristband(prefix, mesh_name, joints, side=1, color=(0.85, 0.25, 0.1), name='Wristband'):
    return D.watch(mesh_name, prefix, joints, side=side, band=color, face=color, metal=color, name=name, from_end=0.035) if False else _wristband(prefix, mesh_name, joints, side, color, name)


def _wristband(prefix, mesh_name, joints, side, color, name):
    import numpy as np
    o = bpy.data.objects[mesh_name]
    el = Vector((joints['elbow'].x * side, joints['elbow'].y, joints['elbow'].z))
    wr = Vector((joints['wrist'].x * side, joints['wrist'].y, joints['wrist'].z))
    pts = np.array([(o.matrix_world @ v.co)[:] for v in o.data.vertices if side * v.co.x > 0.28 and v.co.z < el.z - 0.03 and v.co.z > wr.z - 0.1])
    ctr = pts.mean(0)
    u_, s_, vt = np.linalg.svd(pts - ctr)
    ax = Vector(vt[0])
    if (wr - el).dot(ax) < 0:
        ax = -ax
    proj = (pts - ctr) @ np.array(ax[:])
    t0 = proj.max() - 0.03
    slab = pts[np.abs(proj - t0) < 0.015]
    c = Vector(ctr) + ax * t0
    r = max(((Vector(p) - c) - ax * ((Vector(p) - c).dot(ax))).length for p in slab) + 0.004
    up = Vector((0, 0, 1))
    u = ax.cross(up)
    u = u.normalized() if u.length > 1e-4 else Vector((1, 0, 0))
    v = ax.cross(u).normalized()
    bm = bmesh.new()
    N = 12
    ra, rb = [], []
    for i in range(N):
        a = 2 * math.pi * i / N
        d = u * math.cos(a) + v * math.sin(a)
        ra.append(bm.verts.new(c + d * r + ax * 0.016))
        rb.append(bm.verts.new(c + d * r - ax * 0.016))
    for i in range(N):
        j = (i + 1) % N
        f = bm.faces.new((ra[i], ra[j], rb[j], rb[i]))
        f.material_index = 0
        f.smooth = False
    f1 = bm.faces.new(list(reversed(ra)))
    f2 = bm.faces.new(rb)
    return new_obj(bm, prefix + '_' + name, [mat(prefix + '_WristbandCloth', color, 0.0, 0.9)])


def bracelet(prefix, skin_mesh, joints, side=1, color=(0.85, 0.25, 0.1), back=0.03, width=0.014, thick=0.003, name='Bracelet', second=None):
    """Band(s) hugging the real wrist cross-section (plane cut of the skin mesh). second=(color, back) adds another band."""
    bm, ctr, ax, u, v, ang = D.wrist_band(skin_mesh, prefix, joints, side, back=back, width=width, thick=thick)
    mats = [mat(prefix + '_BraceletA', color, 0.0, 0.6)]
    if second:
        bm2, c2, ax2, u2, v2, ang2 = D.wrist_band(skin_mesh, prefix, joints, side, back=second[1], width=width, thick=thick)
        tmp = bpy.data.meshes.new('t')
        bm2.to_mesh(tmp)
        bm2.free()
        for f in tmp.polygons:
            pass
        n0 = len(bm.verts)
        bm.from_mesh(tmp)
        bm.faces.ensure_lookup_table()
        for f in bm.faces[-len(tmp.polygons):]:
            f.material_index = 1
        bpy.data.meshes.remove(tmp)
        mats.append(mat(prefix + '_BraceletB', second[0], 0.0, 0.6))
    return new_obj(bm, prefix + '_' + name, mats)


def neckerchief(prefix, meshes, neck_z, color=(0.75, 0.12, 0.10), dot=(0.92, 0.88, 0.80), name='Neckerchief', off=0.0045):
    """Band tied around the neck with a small triangle falling on the chest."""
    cy = -0.03
    ring = [Vector((0.082 * math.sin(a), cy - 0.082 * math.cos(a), neck_z - 0.012)) for a in [2 * math.pi * k / 28 for k in range(29)]]
    pts = strap(meshes, ring, 0.04, off)
    bm = bmesh.new()
    strap_mesh(bm, pts, 0.04, 0)
    t = tree_of(meshes[0])
    h = t.ray_cast(Vector((0, -0.8, neck_z - 0.03)), Vector((0, 1, 0)))
    if h[0] is not None:
        n = h[1].normalized()
        M = frame(n)
        p = h[0] + n * 0.006
        v0 = bm.verts.new(M @ Vector((-0.034, 0.0, 0.0)) + p)
        v1 = bm.verts.new(M @ Vector((0.034, 0.0, 0.0)) + p)
        v2 = bm.verts.new(M @ Vector((0.0, -0.062, 0.0)) + p)
        for tri in ((v0, v1, v2), tuple(bm.verts.new(v.co) for v in (v2, v1, v0))):      # back face on its own vertices
            f = bm.faces.new(tri)
            f.material_index = 0
            f.smooth = False
        for dx, dy in ((0.0, -0.018), (-0.012, -0.034), (0.012, -0.034)):
            add_cyl(bm, M, Vector((dx, dy, 0.0015)), 0.0035, 0.001, 1, 6, p)
    return new_obj(bm, prefix + '_' + name, [mat(prefix + '_ScarfCloth', color, 0.0, 0.9), mat(prefix + '_ScarfDots', dot, 0.0, 0.9)])


def lapel_fold(prefix, meshes, z_top, z_apex, half_top, color, name='LapelFold', width=0.0105, lift=0.0045, inner=0.0035):
    """Soft fold along both edges of a V opening. A sloped ribbon from just inside the opening up onto the jacket, in the jacket colour:
    it hides the stair-stepped colour border and reads as the rolled lapel edge."""
    tr = tree_of(meshes[0])
    bm = bmesh.new()
    N = 22
    for sx in (-1, 1):
        rows = []
        for i in range(N + 1):
            t = i / N
            z = z_top + (z_apex + 0.012 - z_top) * t
            xc = sx * half_top * (z - z_apex) / (z_top - z_apex)
            w = width * (1.0 - 0.55 * t)
            pair = []
            for xx, lf in ((xc - sx * inner, lift * 0.35), (xc + sx * w, lift)):
                h = tr.ray_cast(Vector((xx, -0.8, z)), Vector((0, 1, 0)))
                if h[0] is None:
                    pair = None
                    break
                pair.append(h[0] + h[1].normalized() * lf)
            rows.append(pair)
        for a, b in zip(rows, rows[1:]):
            if a is None or b is None:
                continue
            q4 = [bm.verts.new(v) for v in (a[0], a[1], b[1], b[0])]
            try:
                f = bm.faces.new(q4)
            except ValueError:
                continue
            f.material_index = 0
            f.smooth = False
            f2 = bm.faces.new([bm.verts.new(v.co) for v in q4[::-1]])
            f2.material_index = 0
            f2.smooth = False
    return new_obj(bm, prefix + '_' + name, [mat(prefix + '_LapelFoldCloth', color, 0.0, 0.85)])


def _star_prism(bm, M, centre, r_out, r_in, points, depth, mi, origin=Vector()):
    """Flat faceted star (extruded polygon) lying in the local XY plane, rising along local +Z."""
    n = points * 2
    ring = [Vector((centre.x + (r_out if i % 2 == 0 else r_in) * math.sin(math.pi * i / points), centre.y + (r_out if i % 2 == 0 else r_in) * math.cos(math.pi * i / points), centre.z)) for i in range(n)]
    bot = [bm.verts.new(origin + M @ v) for v in ring]
    top = [bm.verts.new(origin + M @ (v + Vector((0, 0, depth)))) for v in ring]
    faces = [bm.faces.new(top), bm.faces.new(bot[::-1])]
    for i in range(n):
        j = (i + 1) % n
        faces.append(bm.faces.new([bot[i], bot[j], top[j], top[i]]))
    for f in faces:
        f.material_index = mi
        f.smooth = False


def medal(prefix, mesh, x, z, name='Medal', gold=(0.85, 0.66, 0.20), ribbon=((0.45, 0.04, 0.06), (0.88, 0.86, 0.80), (0.05, 0.12, 0.38)), stone=(0.55, 0.05, 0.06)):
    """Military medal: gold bar pin, three-stripe ribbon, faceted star with a centre disc, hanging on the chest."""
    t = tree_of(mesh)
    h = t.ray_cast(Vector((x, -0.8, z)), Vector((0, 1, 0)))
    n = h[1].normalized()
    if n.y > 0:
        n = -n
    M = frame(n)
    bm = bmesh.new()
    p = h[0] + n * 0.0035
    add_box(bm, M, Vector((0, 0.030, 0.0015)), (0.036, 0.006, 0.003), 0, p)                 # bar pin
    for k, mi in enumerate((1, 2, 3)):
        add_box(bm, M, Vector(((k - 1) * 0.0066, 0.0125, 0.001)), (0.0066, 0.033, 0.0016), mi, p)   # ribbon stripes
    _star_prism(bm, M, Vector((0, -0.0105, 0.0)), 0.0165, 0.0085, 8, 0.0032, 0, p)           # star
    add_cyl(bm, M, Vector((0, -0.0105, 0.0042)), 0.0058, 0.0016, 4, 10, p)                   # centre disc
    return new_obj(bm, prefix + '_' + name, [mat(prefix + '_MedalGold', gold, 1.0, 0.35), mat(prefix + '_MedalRibbonA', ribbon[0], 0.0, 0.7), mat(prefix + '_MedalRibbonB', ribbon[1], 0.0, 0.7),
                                           mat(prefix + '_MedalRibbonC', ribbon[2], 0.0, 0.7), mat(prefix + '_MedalStone', stone, 0.0, 0.4)])


def shoulder_boards(prefix, mesh, board=(0.008, 0.009, 0.013), gold=(0.85, 0.66, 0.20), x0=0.062, x1=0.172, half_w=0.027, chevrons=3, rockers=2, name='Epaulettes'):
    """Slip-on rank boards on both shoulders (black sleeve, gold insignia), snapped to the shoulder surface.
    Insignia like a first sergeant: chevrons with the apex towards the neck, a diamond, then rockers (arcs) towards the arm."""
    tr = tree_of(mesh)
    bm = bmesh.new()

    def top(x, y):
        h = tr.ray_cast(Vector((x, y, 2.5)), Vector((0, 0, -1)))
        return (h[0], h[1].normalized()) if h[0] is not None else (None, None)

    def quad(vs, mi, flip):
        vs = [bm.verts.new(v) for v in vs]
        if flip:
            vs = vs[::-1]
        f = bm.faces.new(vs)
        f.material_index = mi
        f.smooth = False
        return f

    def strip(pts2, half, sx, off=0.0066):
        """Gold line along 2D points (x, y): corners are offset in the XY plane and each ray-snapped to the surface (no normal-dependent skew)."""
        L, R = [], []
        n = len(pts2)
        for i, (x, y) in enumerate(pts2):
            xa, ya = pts2[max(i - 1, 0)]
            xb, yb = pts2[min(i + 1, n - 1)]
            tx, ty = xb - xa, yb - ya
            ln = math.hypot(tx, ty) or 1.0
            px, py = -ty / ln * half, tx / ln * half
            for side, lst in ((1, L), (-1, R)):
                pt, nn = top(x + side * px, y + side * py)
                if pt is None:
                    return
                lst.append(pt + Vector((0, 0, 1)) * off * 0.9 + nn * off * 0.1)
        for i in range(n - 1):
            quad((L[i], R[i], R[i + 1], L[i + 1]), 1, sx < 0)

    for sx in (-1, 1):
        NXs, NYs = 12, 4
        grid = []
        for i in range(NXs + 1):
            x = sx * (x0 + (x1 - x0) * i / NXs)
            row = []
            for j in range(NYs + 1):
                y = -half_w + 2 * half_w * j / NYs
                pt, nn = top(x, y)
                row.append(pt + nn * 0.0045 if pt is not None else None)
            grid.append(row)
        for i in range(NXs):
            for j in range(NYs):
                q = [grid[i][j], grid[i + 1][j], grid[i + 1][j + 1], grid[i][j + 1]]
                if any(v is None for v in q):
                    continue
                quad(q, 0, sx < 0)

        def skirt(a, b):
            if a is None or b is None:
                return
            pa, _ = top(a.x, a.y)
            pb, _ = top(b.x, b.y)
            if pa is None or pb is None:
                return
            vs = (a, b, pb + Vector((0, 0, 0.0004)), pa + Vector((0, 0, 0.0004)))
            quad(vs, 0, False)
            quad(vs[::-1], 0, False)
        for j in range(NYs):
            skirt(grid[0][j], grid[0][j + 1])
            skirt(grid[NXs][j], grid[NXs][j + 1])
        for i in range(NXs):
            skirt(grid[i][0], grid[i + 1][0])
            skirt(grid[i][NYs], grid[i + 1][NYs])
        # button at the neck end
        px, nx = top(sx * (x0 + 0.010), 0.0)
        if px is not None:
            add_cyl(bm, frame(nx), Vector((0, 0, 0)), 0.0058, 0.004, 1, 8, px + nx * 0.0072)
        # insignia (sx * distance from the neck = x; 'toward the arm' is larger |x|)
        lw = 0.0021
        xa = x0 + 0.030                                   # apex of the first chevron
        reach = half_w - 0.0045
        for k in range(chevrons):
            xc = xa + k * 0.0105
            strip([(sx * xc, -reach), (sx * (xc - 0.0), -reach * 0.0 + 0.0)] if False else [(sx * (xc + 0.0165), -reach), (sx * xc, 0.0), (sx * (xc + 0.0165), reach)], lw, sx)
        xd = xa + chevrons * 0.0105 + 0.0105          # diamond
        dm = 0.0085
        ctr = []
        for ddx, ddy in ((-dm, 0), (0, dm * 0.8), (dm, 0), (0, -dm * 0.8)):
            pt, nn = top(sx * (xd + ddx), ddy)
            if pt is None:
                ctr = []
                break
            ctr.append(pt + nn * 0.0066)
        if len(ctr) == 4:
            quad(ctr, 1, sx < 0)
        for k in range(rockers):
            xr = xd + 0.016 + k * 0.0105
            arc = [(sx * (xr + 0.0075 * math.sin(math.pi * u / 8.0)), -reach + 2 * reach * u / 8.0) for u in range(9)]
            strip(arc, lw, sx)
    return new_obj(bm, prefix + '_' + name, [mat(prefix + '_BoardCloth', board, 0.0, 0.85), mat(prefix + '_BoardGold', gold, 1.0, 0.4)])


def sleeve_patch(prefix, mesh, z_top, z_bot, half_w=0.040, board=(0.008, 0.009, 0.013), gold=(0.85, 0.66, 0.20), chevrons=3, rockers=2, name='SleevePatch', y_c=0.0):
    """Rank patch on the outside of each upper arm: black shield (flat top, rounded bottom) with gold insignia (chevrons apex up, diamond, rockers),
    ray-snapped to the sleeve from the outside."""
    tr = tree_of(mesh)
    bm = bmesh.new()

    def surf(sx, y, z):
        h = tr.ray_cast(Vector((sx * 0.7, y, z)), Vector((-sx, 0, 0)))
        return (h[0], h[1].normalized()) if h[0] is not None else (None, None)

    def quad(vs, mi, flip):
        vs = [bm.verts.new(v) for v in vs]
        if flip:
            vs = vs[::-1]
        f = bm.faces.new(vs)
        f.material_index = mi
        f.smooth = False

    height = z_top - z_bot
    for sx in (-1, 1):
        flip = sx > 0            # outward normal is +x for sx=+1: winding so faces look outwards
        NY, NZ = 8, 10

        def outline_half(t):          # t=0 top .. 1 bottom; flat sides for 55 %, then a semicircle-ish round
            if t < 0.55:
                return half_w
            u = (t - 0.55) / 0.45
            return half_w * math.sqrt(max(0.0, 1.0 - u * u))
        grid = []
        for j in range(NZ + 1):
            t = j / NZ
            z = z_top - height * t
            hw = max(outline_half(t), 0.0015)
            row = []
            for i in range(NY + 1):
                y = y_c - hw + 2 * hw * i / NY
                pt, nn = surf(sx, y, z)
                row.append(pt + nn * 0.0045 if pt is not None else None)
            grid.append(row)
        for j in range(NZ):
            for i in range(NY):
                q = [grid[j][i], grid[j][i + 1], grid[j + 1][i + 1], grid[j + 1][i]]
                if any(v is None for v in q):
                    continue
                quad(q, 0, flip)

        def strip(pts2, half):
            L, R = [], []
            n = len(pts2)
            for k, (y, z) in enumerate(pts2):
                ya, za = pts2[max(k - 1, 0)]
                yb, zb = pts2[min(k + 1, n - 1)]
                ty, tz = yb - ya, zb - za
                ln = math.hypot(ty, tz) or 1.0
                py, pz = -tz / ln * half, ty / ln * half
                for side, lst in ((1, L), (-1, R)):
                    pt, nn = surf(sx, y + side * py, z + side * pz)
                    if pt is None:
                        return
                    lst.append(pt + nn * 0.0068)
            for k in range(n - 1):
                quad((L[k], R[k], R[k + 1], L[k + 1]), 1, flip)
        lw = 0.0021
        za = z_top - 0.013
        reach = half_w - 0.008
        for k in range(chevrons):
            zc = za - k * 0.0105
            strip([(y_c - reach, zc - 0.0175), (y_c, zc), (y_c + reach, zc - 0.0175)], lw)
        zd = za - chevrons * 0.0105 - 0.011
        dm = 0.0085
        pts = []
        for dy, dz in ((-dm * 0.8, 0), (0, dm), (dm * 0.8, 0), (0, -dm)):
            pt, nn = surf(sx, y_c + dy, zd + dz)
            if pt is None:
                pts = []
                break
            pts.append(pt + nn * 0.0068)
        if len(pts) == 4:
            quad(pts, 1, flip)
        for k in range(rockers):
            zr = zd - 0.016 - k * 0.0105
            arc = [(y_c - reach + 2 * reach * u / 8.0, zr - 0.0075 * math.sin(math.pi * u / 8.0)) for u in range(9)]
            strip(arc, lw)
    return new_obj(bm, prefix + '_' + name, [mat(prefix + '_PatchCloth', board, 0.0, 0.85), mat(prefix + '_PatchGold', gold, 1.0, 0.4)])


def satchel(prefix, meshes, shoulder_x, hip_z, shoulder_z, bag_w=0.25, bag_h=0.22, bag_d=0.075, side=-1, hip_x=0.15, name='Bag',
            canvas=(0.55, 0.45, 0.27), flap=(0.06, 0.22, 0.28), strap_col=(0.06, 0.20, 0.30), leather=(0.30, 0.15, 0.08), metal=(0.75, 0.62, 0.30),
            pins=((0.80, 0.12, 0.12), (0.90, 0.75, 0.10), (0.15, 0.55, 0.62)), pom=(0.85, 0.35, 0.50), stars=None):
    """Student satchel: cross-body strap that ends in two metal rings on the top corners of the bag (front and back halves), flap with buckle strap, front pocket, pins and a pom keychain."""
    snap = _snap_fn(meshes)
    push = _outside_pusher(meshes)
    sx = side * shoulder_x
    hx = -side * hip_x
    loc, nor = snap(Vector((hx * 0.9, 0.0, hip_z)), 0.0)
    nx = 1.0 if nor.x > 0 else -1.0
    cen = Vector((loc.x + nx * (bag_d / 2 + 0.014), loc.y, hip_z - bag_h * 0.45))
    top_z = cen.z + bag_h / 2
    A_f = Vector((cen.x, cen.y - bag_w / 2 + 0.022, top_z + 0.006))
    A_b = Vector((cen.x, cen.y + bag_w / 2 - 0.022, top_z + 0.006))
    N = 16
    bm = bmesh.new()

    def half(A, ysgn):
        path = []
        for i in range(N + 1):
            s_ = i / N
            path.append(Vector((sx + (A.x - sx) * s_, ysgn * 0.16 * (1 - s_) + A.y * s_, shoulder_z + (A.z - shoulder_z) * s_)))
        return path
    front = half(A_f, -1)
    back = half(A_b, 1)
    # one continuous strap: bag (back corner) -> up the back -> over the top of the shoulder -> down the chest -> bag (front corner)
    over = [Vector((sx, y, shoulder_z + 0.03 * (1 - (y / 0.16) ** 2))) for y in (0.11, 0.055, 0.0, -0.055, -0.11)]
    path = back[::-1] + over + front[1:]
    pts = strap(meshes, path, 0.03, 0.007, relax=6)
    pts = [(A_b, pts[0][1])] + [(push(q, 0.006), n_) for q, n_ in pts[1:-1]] + [(A_f, pts[-1][1])]
    strap_mesh(bm, pts, 0.03, 2)
    for A in (A_f, A_b):
        add_cyl(bm, Matrix.Identity(4), Vector((0, 0, 0)), 0.0075, 0.004, 4, 8, A + Vector((nx * 0.001, 0, 0)))       # metal ring where the strap meets the bag
    M = Matrix.Identity(4)
    out = Vector((nx, 0, 0))
    Fm = frame(out)
    add_box(bm, M, Vector((0, 0, 0)), (bag_d, bag_w, bag_h), 0, cen)                                                    # body
    fh_, fz_ = (0.34, 0.33) if stars else (0.58, 0.18)
    add_box(bm, M, Vector((nx * (bag_d / 2 + 0.003), 0, bag_h * fz_)), (0.006, bag_w + 0.006, bag_h * fh_), 1, cen)   # flap over the outside face
    add_box(bm, M, Vector((0, 0, bag_h / 2 + 0.003)), (bag_d + 0.008, bag_w + 0.006, 0.008), 1, cen)                    # lid
    if not stars:
        add_box(bm, M, Vector((nx * (bag_d / 2 + 0.0075), 0, -bag_h * 0.22)), (0.012, bag_w * 0.82, bag_h * 0.34), 0, cen)  # front pocket
    if not stars:
        add_box(bm, M, Vector((nx * (bag_d / 2 + 0.0135), 0, -bag_h * 0.07)), (0.0016, bag_w * 0.82, 0.003), 3, cen)        # pocket zip line
    add_box(bm, M, Vector((nx * (bag_d / 2 + 0.007), 0, bag_h * (0.16 if stars else 0.02))), (0.0035, 0.022, bag_h * (0.26 if stars else 0.46)), 3, cen)          # buckle strap
    add_box(bm, M, Vector((nx * (bag_d / 2 + 0.0095), 0, -bag_h * (0.0 if stars else 0.14))), (0.005, 0.030, 0.016), 4, cen)                # buckle
    for k, col in enumerate((5, 6, 7) if not stars else ()):                                                                                   # pins on the flap
        add_cyl(bm, Fm, Vector((0, 0, 0)), 0.0075, 0.0022, col, 8, cen + Vector((nx * (bag_d / 2 + 0.0075), (k - 1) * 0.052, bag_h * 0.30 - 0.006 * (k % 2))))
    if stars:      # colourful stars over the bag body (below the flap), as little faceted star prisms
        import random
        rnd = random.Random(5)
        placed = []
        zlo, zhi = -bag_h / 2 + 0.022, bag_h * 0.12
        tries = 0
        while len(placed) < stars['count'] and tries < 400:
            tries += 1
            yy_, zz_ = rnd.uniform(-bag_w / 2 + 0.022, bag_w / 2 - 0.022), rnd.uniform(zlo, zhi)
            if any((yy_ - a) ** 2 + (zz_ - b) ** 2 < 0.027 ** 2 for a, b in placed):
                continue
            placed.append((yy_, zz_))
            r_ = rnd.uniform(0.0085, 0.0125)
            Mc = Matrix.Rotation(rnd.uniform(0, 1.2), 3, 'Z')
            frame_s = Fm @ Matrix.Rotation(rnd.uniform(0, 1.2), 4, 'Z')
            _star_prism(bm, frame_s, Vector((0, 0, 0)), r_, r_ * 0.45, 5, 0.0022, 9 + rnd.randrange(len(stars['colors'])), cen + Vector((nx * (bag_d / 2 + 0.0006), yy_, zz_)))
    kc = cen + Vector((nx * (bag_d / 2 + 0.006), -bag_w / 2 + 0.018, -bag_h / 2))
    for k in range(0 if stars else 3):                                                                                    # keychain chain + pom
        add_box(bm, M, Vector((0, 0, -0.005 - 0.009 * k)), (0.0035, 0.0035, 0.008), 4, kc)
    if not stars:
        add_box(bm, M, Vector((0, 0, -0.045)), (0.018, 0.018, 0.018), 8, kc)
    mats = [mat(prefix + '_BagCanvas', canvas, 0.0, 0.85), mat(prefix + '_BagFlap', flap, 0.0, 0.85), mat(prefix + '_BagStrap', strap_col, 0.0, 0.8), mat(prefix + '_BagLeather', leather, 0.0, 0.7),
            mat(prefix + '_BagBuckle', metal, 1.0, 0.35), mat(prefix + '_BagPinA', pins[0], 0.0, 0.5), mat(prefix + '_BagPinB', pins[1], 0.0, 0.5), mat(prefix + '_BagPinC', pins[2], 0.0, 0.5),
            mat(prefix + '_BagPom', pom, 0.0, 0.9)] + [mat(prefix + '_BagStar%d' % i, c_, 0.0, 0.6) for i, c_ in enumerate((stars or {}).get('colors', []))]
    return new_obj(bm, prefix + '_' + name, mats)
