"""Tool belt for the Courier: leather belt ring over the outermost garment, buckle, hammer, wrench and a nail pouch with nails."""
import bpy, bmesh, math
from mathutils import Vector, Matrix
from npc_details import mat, new_obj, add_box, add_cyl, tree_of


def _ring(meshes, z, n=64, height=0.032, thick=0.007, off=0.002):
    """Outline of the garments at height z: for every angle a ray comes in from outside and hits the outermost surface."""
    ts = [tree_of(m) for m in meshes]
    cx, cy = 0.0, -0.01
    pts = []
    for i in range(n):
        a = 2 * math.pi * i / n
        d = Vector((math.cos(a), math.sin(a), 0))
        best = None
        for t in ts:
            h = t.ray_cast(Vector((cx, cy, z)) + d * 0.6, -d)
            if h[0] is not None:
                r = (Vector((h[0].x - cx, h[0].y - cy, 0))).length
                if best is None or r > best:
                    best = r
        pts.append((a, best if best is not None else 0.17))
    # light smoothing so the belt does not copy every facet
    rs = [r for _, r in pts]
    sm = [(rs[i - 1] + 2 * rs[i] + rs[(i + 1) % n]) / 4 for i in range(n)]
    return [(a, sm[i]) for i, (a, _) in enumerate(pts)], cx, cy


def tool_belt(prefix, meshes, z, name='ToolBelt', leather=(0.17, 0.095, 0.045), metal=(0.62, 0.62, 0.64), wood=(0.45, 0.27, 0.10), grip=(0.85, 0.35, 0.05)):
    ring, cx, cy = _ring(meshes, z)
    bm = bmesh.new()
    n = len(ring)
    hh = 0.016
    for i in range(n):
        a0, r0 = ring[i]
        a1, r1 = ring[(i + 1) % n]
        P = []
        for a, r in ((a0, r0), (a1, r1)):
            d = Vector((math.cos(a), math.sin(a), 0))
            base = Vector((cx, cy, z)) + d * (r + 0.002)
            P.append((base + Vector((0, 0, -hh)), base + Vector((0, 0, hh)), base + d * 0.007 + Vector((0, 0, hh)), base + d * 0.007 + Vector((0, 0, -hh))))
        a, b = P
        for (u, v, w, x) in ((0, 1, 1, 0), (1, 2, 2, 1), (2, 3, 3, 2), (3, 0, 0, 3)):
            q = [bm.verts.new(a[u]), bm.verts.new(a[v]), bm.verts.new(b[v]), bm.verts.new(b[u])]
            f = bm.faces.new(q)
            f.material_index = 0
            f.smooth = False

    def at(deg):
        a = math.radians(deg)
        k = min(range(n), key=lambda j: abs(((ring[j][0] - a + math.pi) % (2 * math.pi)) - math.pi))
        r = ring[k][1] + 0.009
        return Vector((cx + math.cos(a) * r, cy + math.sin(a) * r, z)), Matrix.Rotation(a, 4, 'Z')

    # buckle at the front (-y)
    o, M = at(-90)
    add_box(bm, M, Vector((0.002, 0, 0)), (0.006, 0.050, 0.040), 1, o)
    add_box(bm, M, Vector((0.005, 0, 0)), (0.004, 0.034, 0.024), 0, o)
    add_box(bm, M, Vector((0.007, 0, 0)), (0.003, 0.006, 0.026), 1, o)

    # hammer: loop on the belt, handle hanging down, head up beside the belt
    o, M = at(-30)
    add_box(bm, M, Vector((0.002, 0, 0.002)), (0.010, 0.030, 0.036), 0, o)                       # belt loop
    add_cyl(bm, M, Vector((0.016, 0, -0.088)), 0.0135, 0.20, 3, 8, o)                              # rubber grip handle (short, thick)
    add_cyl(bm, M, Vector((0.016, 0, -0.192)), 0.0155, 0.012, 3, 8, o)                              # grip end cap
    add_cyl(bm, M, Vector((0.016, 0, 0.012)), 0.0095, 0.040, 2, 8, o)                              # neck
    add_box(bm, M, Vector((0.016, 0.012, 0.042)), (0.026, 0.078, 0.030), 2, o)                     # head
    add_box(bm, M, Vector((0.016, -0.040, 0.048)), (0.014, 0.028, 0.018), 2, o)                    # claw
    add_box(bm, M, Vector((0.016, 0.056, 0.042)), (0.030, 0.012, 0.034), 2, o)                     # striking face

    # adjustable wrench (monkey wrench): ring end at the belt, tapered handle, head with fixed jaw, sliding jaw and worm screw
    o, M = at(-150)
    add_box(bm, M, Vector((0.002, 0, 0.002)), (0.010, 0.030, 0.036), 0, o)                          # belt loop
    add_box(bm, M, Vector((0.010, 0, 0.004)), (0.007, 0.034, 0.030), 2, o)                          # ring end (plate)
    add_box(bm, M, Vector((0.0112, 0, 0.004)), (0.008, 0.014, 0.014), 4, o)                         # hanging hole
    add_box(bm, M, Vector((0.010, 0, -0.060)), (0.007, 0.024, 0.100), 2, o)                         # upper handle
    add_box(bm, M, Vector((0.010, 0, -0.135)), (0.007, 0.028, 0.050), 2, o)                         # lower handle (wider)
    add_box(bm, M, Vector((0.010, 0, -0.178)), (0.007, 0.048, 0.036), 2, o)                         # head body
    add_box(bm, M, Vector((0.010, 0.019, -0.215)), (0.007, 0.012, 0.050), 2, o)                     # fixed jaw
    add_box(bm, M, Vector((0.010, -0.019, -0.212)), (0.007, 0.012, 0.044), 2, o)                    # sliding jaw
    add_box(bm, M, Vector((0.0115, 0.0, -0.196)), (0.006, 0.026, 0.010), 4, o)                      # jaw gap shadow
    add_cyl(bm, M, Vector((0.0145, -0.011, -0.200)), 0.0058, 0.040, 5, 8, o)                         # worm screw
    for k in range(5):
        add_cyl(bm, M, Vector((0.0145, -0.011, -0.186 - k * 0.0075)), 0.0064, 0.0022, 2, 8, o)     # knurling rings

    # nail pouch on the right hip with nails sticking out
    o, M = at(40)
    add_box(bm, M, Vector((0.002, 0, 0.004)), (0.010, 0.060, 0.036), 0, o)                         # belt loop strap
    add_box(bm, M, Vector((0.026, 0, -0.050)), (0.040, 0.092, 0.086), 4, o)                        # pouch
    add_box(bm, M, Vector((0.047, 0, -0.030)), (0.006, 0.070, 0.040), 4, o)                        # front flap
    for k, dy in enumerate((-0.030, -0.012, 0.004, 0.020, 0.034)):
        add_cyl(bm, M, Vector((0.022 + 0.004 * (k % 2), dy, -0.002 + 0.006 * (k % 3))), 0.0017, 0.040, 5, 5, o, r2=0.0006)   # nail shank
        add_cyl(bm, M, Vector((0.022 + 0.004 * (k % 2), dy, 0.017 + 0.006 * (k % 3))), 0.0046, 0.0018, 5, 6, o)              # nail head
    return new_obj(bm, prefix + '_' + name, [mat(prefix + '_BeltLeather', leather, 0.0, 0.85), mat(prefix + '_BeltMetal', metal, 0.8, 0.35),
                                              mat(prefix + '_ToolSteel', (0.40, 0.41, 0.44), 0.8, 0.35), mat(prefix + '_ToolGrip', grip, 0.0, 0.7),
                                              mat(prefix + '_PouchLeather', (0.12, 0.07, 0.035), 0.0, 0.9), mat(prefix + '_Nail', (0.55, 0.55, 0.57), 0.8, 0.4)])


def work_boot_details(prefix, boots, z0=0.085, z1=0.235, name='BootLaces', lace=(0.10, 0.07, 0.04), tongue=(0.40, 0.25, 0.11), metal=(0.70, 0.70, 0.72)):
    """Work-boot lacing for both feet: padded tongue strip up the front, crossing laces with metal eyelets, lifted a few mm off the leather by ray snapping."""
    tr = tree_of(boots)
    bm = bmesh.new()
    for sgn in (-1, 1):
        # front centre line of this boot: horizontal ray from the front at each height
        xs = [v.co.x for v in bpy.data.objects[boots].data.vertices if v.co.x * sgn > 0.02 and v.co.z < 0.1]
        cx = sum(xs) / len(xs)
        levels = [z0 + (z1 - z0) * i / 9 for i in range(10)]
        front = []
        for z in levels:
            h = tr.ray_cast(Vector((cx, -0.6, z)), Vector((0, 1, 0)))
            if h[0] is None:
                front.append(None)
                continue
            n = h[1].normalized()
            if n.y > 0:
                n = -n
            front.append((h[0], n))
        pts = [f for f in front if f]
        # tongue: ribbon along the centre line
        for a, b in zip(pts, pts[1:]):
            quad = []
            for (p, n) in (a, b):
                side = Vector((1, 0, 0)).cross(n)
                side = (Vector((1, 0, 0)) - n * n.x).normalized() * 0.026
                quad.append((p + n * 0.004 + side, p + n * 0.004 - side))
            q = [bm.verts.new(v) for v in (quad[0][0], quad[0][1], quad[1][1], quad[1][0])]
            f = bm.faces.new(q); f.material_index = 0; f.smooth = False
        # laces: bars across the tongue, with eyelets at the ends
        for (p, n) in pts[1:]:
            t = (Vector((1, 0, 0)) - n * n.x).normalized()
            for s in (-1, 1):
                c = p + n * 0.0075 + t * s * 0.020
                add_cyl(bm, _frame_x(t, n), Vector((0, 0, 0)), 0.0030, 0.0035, 2, 8, c)
            M = _frame_x(t, n)
            add_box(bm, M, Vector((0, 0, 0)), (0.046, 0.0045, 0.0045), 1, p + n * 0.0072)
    return new_obj(bm, prefix + '_' + name, [mat(prefix + '_BootTongue', tongue, 0.0, 0.9), mat(prefix + '_BootLace', lace, 0.0, 0.9), mat(prefix + '_BootEyelet', metal, 0.8, 0.35)])


def _frame_x(t, n):
    """Matrix with local x = t (across the boot), local z = n (out of the boot)."""
    z = n.normalized()
    x = (t - z * t.dot(z)).normalized()
    y = z.cross(x)
    return Matrix(((x.x, y.x, z.x), (x.y, y.y, z.y), (x.z, y.z, z.z))).to_4x4()


def brushes_in_apron(prefix, meshes, x, z, count=3, name='Brushes', wood=(0.55, 0.32, 0.14), ferrule=(0.70, 0.70, 0.72), tips=((0.12, 0.30, 0.64), (0.72, 0.13, 0.13), (0.88, 0.74, 0.16))):
    """Paint brushes sticking out of the apron's chest area: handles rise from the cloth, with ferrule and a coloured bristle tip."""
    from npc_props import _cone_between
    tr = tree_of(meshes[0])
    h = tr.ray_cast(Vector((x, -0.8, z)), Vector((0, 1, 0)))
    n = h[1].normalized() if h[0] is not None else Vector((0, -1, 0))
    base = h[0] if h[0] is not None else Vector((x, -0.12, z))
    if n.y > 0:
        n = -n
    bm = bmesh.new()
    for k in range(count):
        dx = (k - (count - 1) / 2) * 0.022
        tilt = (k - (count - 1) / 2) * 0.16
        a = base + Vector((dx, 0, -0.012)) + n * 0.003
        d = Vector((tilt, -0.10, 1.0)).normalized()
        L = 0.105 + 0.012 * (k % 2)
        b = a + d * L
        _cone_between(bm, a, b, 0.0032, 0.0022, 6, 0)                          # handle
        _cone_between(bm, b - d * 0.004, b + d * 0.022, 0.0034, 0.0034, 6, 1)  # ferrule
        _cone_between(bm, b + d * 0.020, b + d * 0.046, 0.0034, 0.0006, 6, 2 + (k % 3))  # bristles
    return new_obj(bm, prefix + '_' + name, [mat(prefix + '_BrushWood', wood, 0.0, 0.7), mat(prefix + '_BrushFerrule', ferrule, 0.8, 0.4),
                                              mat(prefix + '_BrushBlue', tips[0], 0.0, 0.9), mat(prefix + '_BrushRed', tips[1], 0.0, 0.9), mat(prefix + '_BrushYellow', tips[2], 0.0, 0.9)])
