"""Jardin del museo: plantas con silueta reconocible, macetas, muro de piedra, cerca de estacas y puerta gotica.

Plantas (todas de hojas planas, nada de bolas):
  sunflower  - girasol: tallo, hojas grandes, cabezuela con disco y corona de petalos (guino a la pintura)
  lavender   - mata de lavanda: abanico de hojas gris verdoso + espigas moradas
  geranium   - mata de geranio de jardinera: hojas redondas festoneadas + umbelas de flores
  rose_bush  - rosal: copa de hojas ordenadas como tejas + rosas
Todas reciben un builder B (museum_lib) y trabajan en coordenadas de mundo (o locales si el B es de un prop).
"""
import math, random
from mathutils import Vector

UP = Vector((0, 0, 1))
LEAF_MATS = ["M_Plant_Leaf", "M_Plant_LeafLight", "M_Leaf_Dark"]


def _basis(n):
    n = Vector(n).normalized()
    a = n.cross(UP)
    if a.length < 1e-3:
        a = Vector((1, 0, 0))
    a.normalize()
    return n, a, n.cross(a).normalized()


# ----------------------------------------------------------------- plantas
def grass(b, c, h, n=7):
    x, y, z = c
    for k in range(n):
        a = random.uniform(0, math.tau)
        lean = random.uniform(0.12, 0.4)
        d = Vector((math.cos(a) * lean, math.sin(a) * lean, 1.0))
        b.blade(Vector((x + math.cos(a) * 0.03, y + math.sin(a) * 0.03, z - 0.01)), d, h * random.uniform(0.6, 1.1),
                random.uniform(0.03, 0.045), random.choice(["M_Plant_Leaf", "M_Plant_LeafLight", "M_Plant_Leaf", "M_Ivy_Light"]))


def petal(b, base, tip_dir, n, L, W, mat, thick=0.004):
    """Petalo de girasol a medida: nace estrecho, ensancha hacia la mitad y acaba en punta (ref. del usuario)."""
    import bmesh
    t = Vector(tip_dir).normalized()
    n = Vector(n).normalized()
    sd = n.cross(t).normalized()
    base = Vector(base)
    N = 8
    left, right = [], []
    for k in range(N + 1):
        u = k / N
        w = W * 0.5 * (math.sin(math.pi * u ** 0.85) ** 0.75) * (0.55 + 0.45 * (1 - u))
        p = base + t * (u * L) + n * (0.015 * L * math.sin(math.pi * u))   # leve combado
        left.append(p + sd * w)
        right.append(p - sd * w)
    pts = left + list(reversed(right[1:-1]))
    bm = bmesh.new()
    f = bm.faces.new([bm.verts.new(q) for q in pts])
    res = bmesh.ops.extrude_face_region(bm, geom=[f])
    nv = [g for g in res["geom"] if isinstance(g, bmesh.types.BMVert)]
    bmesh.ops.translate(bm, vec=-n * thick, verts=nv)
    b._push(bm, mat)


def flower_head(b, c, n, size, mat, petals=13, disc_mat="M_Sunflower_Disc"):
    """Cabezuela de girasol (ref. del usuario): disco marron grande con centro oscuro y DOS coronas limpias
    de petalos apuntados; la de atras desfasada medio paso y algo mas anaranjada. size = radio total."""
    n, a, bb = _basis(n)
    c = Vector(c)
    rd = size * 0.44
    b.leaf(c + n * 0.016, n, a, rd, disc_mat, thick=0.022, res=24, shape='disc')
    b.leaf(c + n * 0.03, n, a, rd * 0.45, "M_Bark", thick=0.004, res=16, shape='disc')
    L = size - rd * 0.8
    for ring, (off, rot, back, m, lk, wk) in enumerate(((0.004, 0.0, 0.08, mat, 1.0, 0.42),
                                                        (-0.006, 0.5, 0.2, "M_Fabric_Mustard", 1.1, 0.4))):
        for k in range(petals):
            ang = (k + rot) * math.tau / petals
            rad = a * math.cos(ang) + bb * math.sin(ang)
            tip = (rad - n * back).normalized()
            nn = (n - tip * n.dot(tip)).normalized()
            petal(b, c + n * off + rad * rd * 0.8, tip, nn, L * lk, L * wk, m)
    b.leaf(c - n * 0.02, n, a, rd * 1.1, "M_Plant_Leaf", thick=0.005, res=14, shape='round')   # caliz


def sunflower(b, base, h, face, lean=0.0):
    """Girasol: tallo con leve curva, 3 hojas acorazonadas con peciolo (caidas), cabezuela inclinada al frente."""
    base = Vector(base)
    face = Vector(face).normalized()
    side = face.cross(UP).normalized()
    pts = [base]
    for k in range(1, 6):
        t = k / 5
        pts.append(base + UP * h * t + face * (0.08 * t * t) + side * (lean * t * t))
    for p0, p1 in zip(pts, pts[1:]):
        b.seg(p0, p1, 0.016 * (1.0 - 0.3 * (p0 - base).length / h), "M_Plant_Leaf", seg=6)
    for k, t in enumerate((0.32, 0.5, 0.68)):
        q = base.lerp(pts[-1], t)
        ang = k * 2.4 + random.uniform(-0.3, 0.3)
        out = (side * math.cos(ang) + face * math.sin(ang) * 0.6).normalized()
        pet = q + out * 0.08 + UP * 0.02
        b.seg(q, pet, 0.006, "M_Plant_Leaf", seg=4)
        tip = (out - UP * 0.35).normalized()
        nn = (UP - tip * UP.dot(tip)).normalized()
        ln = random.uniform(0.13, 0.17) * (1.15 - t * 0.4)
        b.leaf(pet + tip * ln * 0.8, nn, tip, ln, random.choice(["M_Plant_Leaf", "M_Leaf_Dark"]), thick=0.005, res=20, shape='heart')
    head_n = (face * 0.85 + UP * 0.45).normalized()
    flower_head(b, pts[-1] + face * 0.02, head_n, random.uniform(0.17, 0.2), "M_Flower_Yellow")


# especies de pradera: (petalos, centro, n_petalos)
SPECIES = {
    "daisy":      ("M_Flower_White", "M_Flower_Yellow", (7, 8)),
    "buttercup":  ("M_Flower_Yellow", "M_Fabric_Mustard", (6, 6)),
    "cornflower": ("M_Flower_Iris", "M_Sunflower_Disc", (6, 7)),
    "pink":       ("M_Flower_Rose", "M_Flower_Yellow", (6, 6)),
}
SPECIES_BY_MAT = {"M_Flower_White": "daisy", "M_Flower_Yellow": "buttercup", "M_Flower_Iris": "cornflower",
                  "M_Flower_Rose": "pink", "M_Flower_Lavender": "cornflower"}


def meadow_flower(b, c, h, species):
    """Florecita de pradera: tallo con 1-2 hojas, corona de 6-8 petalos y centro de color."""
    pm, cm, (n0, n1) = SPECIES[species]
    base = Vector(c)
    bend = Vector((random.uniform(-0.06, 0.06), random.uniform(-0.06, 0.06), 0))
    top = base + UP * h + bend
    mid = base + UP * h * 0.5 + bend * 0.3
    b.seg(base, mid, 0.006, "M_Plant_Leaf", seg=4)
    b.seg(mid, top, 0.005, "M_Plant_Leaf", seg=4)
    for k in range(random.choice((1, 2))):
        q = base.lerp(top, random.uniform(0.25, 0.55))
        a = random.uniform(0, math.tau)
        out = Vector((math.cos(a), math.sin(a), 0))
        tip = (out + UP * 0.6).normalized()
        nn = (UP - tip * UP.dot(tip)).normalized()
        ln = random.uniform(0.05, 0.07)
        b.leaf(q + tip * ln * 0.9, nn, tip, ln, random.choice(["M_Plant_LeafLight", "M_Plant_Leaf"]), thick=0, res=6)
    n = (UP + Vector((random.uniform(-0.35, 0.35), random.uniform(-0.35, 0.35), 0))).normalized()
    n, a, bb = _basis(n)
    np_ = random.randint(n0, n1)
    ps = random.uniform(0.026, 0.034)
    for k in range(np_):
        ang = k * math.tau / np_ + random.uniform(-0.1, 0.1)
        rad = a * math.cos(ang) + bb * math.sin(ang)
        tip = (rad + n * 0.12).normalized()
        nn = (n - tip * n.dot(tip)).normalized()
        b.leaf(top + rad * ps * 0.25 + tip * ps * 0.85, nn, tip, ps, pm, thick=0, res=6)
    b.leaf(top + n * 0.006, n, a, ps * 0.42, cm, thick=0.006, res=8, shape='disc')


def flower_patch(b, cx, cy, count, species, ok, mix=0.12, spread=(0.5, 0.9)):
    """Parche natural: denso en el centro, bordes desflecados, una especie dominante y alguna intrusa."""
    sx, sy = random.uniform(*spread), random.uniform(*spread)
    rot = random.uniform(0, math.pi)
    others = [k for k in SPECIES if k != species]
    for i in range(count):
        dx, dy = random.gauss(0, sx * 0.55), random.gauss(0, sy * 0.55)
        x = cx + dx * math.cos(rot) - dy * math.sin(rot)
        y = cy + dx * math.sin(rot) + dy * math.cos(rot)
        if not ok(x, y):
            continue
        sp = species if random.random() > mix else random.choice(others)
        meadow_flower(b, (x, y, 0.0), random.uniform(0.18, 0.38), sp)


def lavender(b, base, sc=1.0):
    base = Vector(base)
    for k in range(12):          # hojas finas gris verdoso
        a = random.uniform(0, math.tau)
        d = Vector((math.cos(a) * 0.45, math.sin(a) * 0.45, 1.0))
        b.blade(base + Vector((math.cos(a), math.sin(a), 0)) * 0.03, d, random.uniform(0.18, 0.26) * sc, 0.022, "M_Leaf_Sage")
    for k in range(9):           # espigas: tallo + capullos apuntados hacia arriba
        a = k * math.tau / 9 + random.uniform(-0.2, 0.2)
        spread = random.uniform(0.18, 0.32)
        top = base + Vector((math.cos(a) * spread, math.sin(a) * spread, 0)) * sc + UP * random.uniform(0.42, 0.6) * sc
        mid = base.lerp(top, 0.5) + UP * 0.03
        b.seg(base, mid, 0.006, "M_Leaf_Sage", seg=4)
        b.seg(mid, top, 0.005, "M_Leaf_Sage", seg=4)
        d = (top - mid).normalized()
        for j in range(5):
            q = top - d * (j * 0.022)
            for s in (-1, 1):
                rad = Vector((-d.y, d.x, 0)).normalized() * s if abs(d.z) < 0.999 else Vector((s, 0, 0))
                tip = (d * 0.7 + rad * 0.5).normalized()
                b.leaf(q + tip * 0.012, rad, tip, 0.016, "M_Flower_Lavender", thick=0.004, res=6)


def geranium(b, base, out, color, sc=1.0):
    """Mata de geranio: hojas redondas festoneadas en cupula + 2-3 umbelas de flores del mismo color."""
    base = Vector(base)
    out = Vector(out).normalized()
    for k in range(9):
        a = k * math.tau / 9 + random.uniform(-0.25, 0.25)
        rad = Vector((math.cos(a), math.sin(a), 0))
        p = base + rad * random.uniform(0.04, 0.1) * sc + UP * random.uniform(0.04, 0.11) * sc
        nn = (rad * 0.6 + UP).normalized()
        t = (rad - nn * rad.dot(nn)).normalized()
        b.leaf(p, nn, t, random.uniform(0.045, 0.06) * sc, random.choice(["M_Plant_Leaf", "M_Plant_LeafLight"]), thick=0.004, res=12, shape='round')
    for k in range(random.randint(2, 3)):
        a = random.uniform(0, math.tau)
        top = base + Vector((math.cos(a), math.sin(a), 0)) * 0.05 * sc + out * 0.03 + UP * random.uniform(0.18, 0.26) * sc
        b.seg(base + UP * 0.05, top, 0.006, "M_Plant_Leaf", seg=4)
        for j in range(8):
            if j == 0:
                q, nn = top + UP * 0.025, UP
            else:
                aa = j * math.tau / 7
                rad = Vector((math.cos(aa), math.sin(aa), 0))
                q, nn = top + rad * 0.035 + UP * 0.012, (rad * 0.7 + UP).normalized()
            tt = Vector((nn.y, -nn.x, 0)).normalized() if abs(nn.z) < 0.99 else Vector((1, 0, 0))
            b.leaf(q, nn, tt, 0.022, color, thick=0.004, res=10, shape='round')


def trailing_ivy(b, start, out, length, ivy_leaf):
    p = Vector(start)
    down = Vector((0, 0, -1))
    for k in range(int(length / 0.05)):
        q = p + down * 0.05 + out * (0.008 if k < 3 else 0.0)
        b.seg(p, q, 0.004, "M_Bark", seg=4)
        if k % 2 == 0:
            ivy_leaf(b, q, out, UP, random.uniform(0.03, 0.045))
        p = q


def rose(b, c, n, mat):
    n, a, bb = _basis(n)
    c = Vector(c)
    for k in range(5):
        ang = k * math.tau / 5
        rad = a * math.cos(ang) + bb * math.sin(ang)
        tip = (rad + n * 0.9).normalized()
        nn = (rad - tip * rad.dot(tip)).normalized() * -1
        b.leaf(c + tip * 0.02, nn, tip, 0.028, mat, thick=0.004, res=10, shape='round')
    b.leaf(c + n * 0.012, n, a, 0.018, mat, thick=0.006, res=10, shape='round')


def rose_bush(b, c, r, roses=8):
    """Copa ordenada: hojas como tejas (punta hacia abajo) sobre un nucleo, y rosas asomando."""
    c = Vector(c)
    cores = []
    for i in range(3):
        a = i * math.tau / 3 + random.uniform(-0.3, 0.3)
        rr = r * random.uniform(0.62, 0.8)
        cc = c + Vector((math.cos(a) * r * 0.42, math.sin(a) * r * 0.42, rr * 0.82))
        cores.append((cc, rr))
    cores.append((c + UP * r * 1.0, r * 0.75))
    for (cc, rr) in cores:
        b.blob(tuple(cc), rr * 0.82, "M_Leaf_Dark", squash=(1, 1, 0.9), sub=2, amp=rr * 0.06)
        nl = int(34 * (rr / 0.6) ** 2) + 10
        for k in range(nl):
            d = Vector((random.gauss(0, 1), random.gauss(0, 1), random.gauss(0, 1) * 0.7 + 0.35)).normalized()
            p = cc + d * rr * 0.9
            if p.z < c.z + 0.05:
                continue
            tip = (-UP + d * 0.35).normalized()
            tip = (tip - d * tip.dot(d)).normalized()
            b.leaf(p, (d + UP * 0.2).normalized(), tip, random.uniform(0.13, 0.17) * (0.8 + rr * 0.3),
                   random.choice(["M_Plant_Leaf", "M_Plant_LeafLight", "M_Plant_Leaf"]), thick=0.006, res=7)
    mat = random.choice(["M_Flower_Rose", "M_Flower_White", "M_Flower_Rose"])
    for k in range(roses):
        cc, rr = random.choice(cores)
        d = Vector((random.gauss(0, 1), random.gauss(0, 1), abs(random.gauss(0, 1)) + 0.4)).normalized()
        rose(b, cc + d * rr * 0.98, d, mat)


# ----------------------------------------------------------------- macetas
def urn(b, c=(0, 0, 0), sc=1.0, mat="M_Museum_Roof"):
    """Maceta en forma de urna: peana, pie, cuerpo acampanado y labio enrollado. Devuelve la cota de la tierra."""
    x, y, z = c
    b.cyl((x, y, z + 0.05 * sc), 0.25 * sc, 0.1 * sc, mat, seg=16, bev=0, amp=0.003)
    b.cyl((x, y, z + 0.15 * sc), 0.13 * sc, 0.1 * sc, mat, seg=14, r2=0.15 * sc, bev=0, amp=0.003)
    b.cyl((x, y, z + 0.4 * sc), 0.17 * sc, 0.4 * sc, mat, seg=18, r2=0.31 * sc, bev=0, amp=0.004)
    ring = [Vector((x + math.cos(k * math.tau / 24) * 0.32 * sc, y + math.sin(k * math.tau / 24) * 0.32 * sc, z + 0.61 * sc)) for k in range(25)]
    for p0, p1 in zip(ring, ring[1:]):
        b.seg(p0, p1, 0.035 * sc, mat, seg=8)
    for zz in (0.3, 0.46):   # bandas decorativas
        b.cyl((x, y, z + zz * sc), (0.19 + (zz - 0.2) * 0.6) * sc, 0.025 * sc, mat, seg=18, bev=0, amp=0.002)
    b.cyl((x, y, z + 0.6 * sc), 0.29 * sc, 0.03, "M_Soil", seg=18, bev=0, amp=0.003)
    return z + 0.61 * sc


# ----------------------------------------------------------------- cerramiento
STONES = ["M_Museum_Stone", "M_Path_Stone", "M_Path_StoneWarm", "M_Path_Stone"]


def stone_wall(b, A, C, h=1.15, th=0.5, faces_both=True):
    """Muro macizo de mamposteria: nucleo continuo + piedras encastradas en las caras + albardilla continua."""
    A, C = Vector(A), Vector(C)
    ln = (C - A).length
    dv = (C - A).normalized()
    nv = Vector((-dv.y, dv.x, 0))
    yaw = math.degrees(math.atan2(dv.y, dv.x))
    n = max(1, int(ln / 1.6))
    for k in range(n):   # nucleo por tramos solapados (sin rendijas)
        t0, t1 = ln * k / n - 0.05, ln * (k + 1) / n + 0.05
        m = A + dv * ((t0 + t1) / 2)
        b.box((m.x, m.y, h / 2), (t1 - t0, th, h), "M_Path_Stone", rot=(0, 0, yaw), bev=0.03, amp=0.025, cuts=2)
    for side in ((-1, 1) if faces_both else (1,)):
        for zc in (0.27, 0.62, 0.95):
            if zc > h - 0.12:
                continue
            t = random.uniform(0.0, 0.25)
            while t < ln - 0.15:
                r = random.uniform(0.17, 0.25)
                q = A + dv * (t + r) + nv * side * (th / 2 - r * 0.3 * 0.55 + 0.03)
                b.blob((q.x, q.y, zc + random.uniform(-0.04, 0.04)), r, random.choice(STONES), squash=(1.35, 0.3, 0.75), sub=1,
                       amp=r * 0.08, rot=(0, 0, yaw + random.uniform(-6, 6)))
                t += r * 2.0
    t = 0.0
    while t < ln - 0.05:   # albardilla: losas planas continuas que vuelan un poco
        sl = min(random.uniform(0.55, 0.85), ln - t)
        m = A + dv * (t + sl / 2)
        b.box((m.x, m.y, h + 0.05), (sl + 0.02, th + 0.14, 0.1), random.choice(["M_Museum_Stone", "M_Path_Stone"]),
              rot=(0, random.uniform(-1.5, 1.5), yaw + random.uniform(-2, 2)), bev=0.03, amp=0.01, cuts=0)
        t += sl


def pier(b, x, y, h=1.35, w=0.62, finial=True):
    b.box((x, y, h / 2), (w, w, h), "M_Museum_Stone", bev=0.04, amp=0.012, cuts=1)
    b.box((x, y, h + 0.05), (w + 0.12, w + 0.12, 0.1), "M_Museum_Stone", bev=0.03, amp=0.006, cuts=0)
    if finial:
        b.cyl((x, y, h + 0.22), w * 0.32, 0.25, "M_Museum_Stone", seg=4, r2=0.02, rot=(0, 0, 45), bev=0, amp=0.004)


def picket_run(b, A, C, base_h=0.54, h=1.14):
    """Cerca de estacas blanca sobre zocalo de piedra: postes, dos largueros y estacas en punta."""
    A, C = Vector(A), Vector(C)
    ln = (C - A).length
    dv = (C - A).normalized()
    yaw = math.degrees(math.atan2(dv.y, dv.x))
    stone_wall(b, A, C, h=base_h, th=0.42)
    z0 = base_h + 0.1
    np_ = max(1, int(ln / 2.0))
    for k in range(np_ + 1):   # postes con remate
        q = A + dv * (ln * k / np_)
        b.box((q.x, q.y, z0 + h / 2 + 0.05), (0.11, 0.11, h + 0.1), "M_Picket", rot=(0, 0, yaw), bev=0.012, amp=0.003, cuts=0)
        b.cyl((q.x, q.y, z0 + h + 0.16), 0.075, 0.12, "M_Picket", seg=4, r2=0.01, rot=(0, 0, yaw + 45), bev=0, amp=0.002)
    for zz in (z0 + 0.18, z0 + h - 0.22):   # largueros
        m = A + dv * (ln / 2)
        b.box((m.x, m.y, zz), (ln, 0.035, 0.07), "M_Picket", rot=(0, 0, yaw), bev=0.006, amp=0.003, cuts=max(1, int(ln / 1.5)))
    nvec = Vector((-dv.y, dv.x, 0))
    t = 0.12
    while t < ln - 0.08:   # estacas en punta (perfil de 5 lados extruido)
        q = A + dv * t + nvec * 0.03
        hh = h - 0.04 + 0.03 * math.sin(t * 2.1)
        wv = dv * 0.04
        pts = [q - wv + UP * z0, q + wv + UP * z0, q + wv + UP * (z0 + hh - 0.07), q + UP * (z0 + hh), q - wv + UP * (z0 + hh - 0.07)]
        b.prism([tuple(p) for p in pts], tuple(nvec * 0.022), "M_Picket", amp=0.003)
        t += 0.16


def pointed_arch(cx, z_spring, half, n=10):
    """Arco apuntado equilatero: dos arcos de radio = luz que se cortan en la clave. Devuelve puntos izq->clave->dcha."""
    span = 2 * half
    left = []
    for k in range(n + 1):   # arco izquierdo: centro en el arranque derecho
        a = math.pi - (math.pi / 3) * k / n
        left.append((cx + half + span * math.cos(a), z_spring + span * math.sin(a)))
    right = [(2 * cx - u, z) for (u, z) in reversed(left)]
    return left + right[1:]


def gothic_gate(b, leaves_cb, cx, y, half=1.25, spring=2.35):
    """Portada de hierro gotica entre dos pilares: arco apuntado doble con reja en el timpano y pinaculos.
    Las hojas se crean aparte (leaves_cb) para poder abrirlas en Unity."""
    for sx in (-1, 1):   # pilares con basa, imposta y pinaculo
        x = cx + sx * (half + 0.36)
        b.box((x, y, 0.1), (0.86, 0.86, 0.2), "M_Museum_Stone", bev=0.03, amp=0.008, cuts=0)
        b.box((x, y, 1.3), (0.72, 0.72, 2.4), "M_Museum_Stone", bev=0.04, amp=0.012, cuts=2)
        b.box((x, y, 2.55), (0.86, 0.86, 0.12), "M_Museum_Stone", bev=0.03, amp=0.006, cuts=0)
        b.cyl((x, y, 3.05), 0.4, 0.9, "M_Museum_Stone", seg=4, r2=0.03, rot=(0, 0, 45), bev=0, amp=0.006)
        for dx, dy in ((0.3, 0.3), (-0.3, 0.3), (0.3, -0.3), (-0.3, -0.3)):
            b.cyl((x + dx, y + dy, 2.78), 0.08, 0.32, "M_Museum_Stone", seg=4, r2=0.01, rot=(0, 0, 45), bev=0, amp=0.003)
        b.seg((x, y, 3.45), (x, y, 3.7), 0.02, "M_Iron", seg=6)
        b.blob((x, y, 3.72), 0.035, "M_Museum_Brass", squash=(1, 1, 1.6), sub=1, amp=0.002)
    outer = pointed_arch(cx, spring, half + 0.0, n=12)
    inner = pointed_arch(cx, spring + 0.16, half - 0.16, n=12)
    for arc in (outer, inner):
        for (u0, z0), (u1, z1) in zip(arc, arc[1:]):
            b.seg((u0, y, z0), (u1, y, z1), 0.045, "M_Iron", seg=8)
    for (u0, z0), (u1, z1) in zip(outer[::3], inner[::3]):   # montantes entre arcos
        b.seg((u0, y, z0), (u1, y, z1), 0.028, "M_Iron", seg=6)
    # reja del timpano: barrotes verticales que unen el dintel con el arco interior (nada flotando)
    ib = pointed_arch(cx, spring + 0.16, half - 0.16, n=40)
    u = cx - half + 0.3
    while u < cx + half - 0.25:
        ztop = max(z for (uu, z) in ib if abs(uu - u) < 0.08)
        b.seg((u, y, spring), (u, y, ztop + 0.02), 0.018, "M_Iron", seg=5)
        u += 0.25
    b.seg((cx - half, y, spring), (cx + half, y, spring), 0.045, "M_Iron", seg=8)   # dintel de hierro
    for k in range(1, 8):   # cresteria: puntas de lanza doradas sobre el arco exterior
        u, z = outer[k * len(outer) // 8]
        b.seg((u, y, z), (u, y, z + 0.05), 0.02, "M_Iron", seg=5)
        b.cyl((u, y, z + 0.11), 0.035, 0.14, "M_Museum_Brass", seg=4, r2=0.003, bev=0, amp=0.0)
    leaves_cb(cx, y, half, spring)


def palette_outline(size):
    """Silueta clasica de paleta: ovalo con escotadura para el pulgar (2D, eje u horizontal, eje v vertical)."""
    pts = []
    for k in range(36):
        a = k * math.tau / 36
        r = 1.0 + 0.12 * math.cos(2 * a)
        u, v = math.cos(a) * r * 1.0, math.sin(a) * r * 0.78
        # escotadura en el lado izquierdo-inferior
        d = math.hypot(u + 0.75, v + 0.25)
        if d < 0.38:
            k2 = (0.38 - d) / 0.38
            u += 0.32 * k2
            v += 0.12 * k2
        pts.append((u * size, v * size))
    return pts


def palette_shape(b, c, plane, size, mat, thick=0.05, dabs=True, brush=False):
    """Paleta solida con agujero de pulgar PASANTE (relleno con hueco), canto, manchas de pintura planas y pincel.
    plane: 'x' -> la paleta mira a +-X (bandera); 'y' -> mira a +-Y."""
    import bmesh
    from mathutils import Matrix
    cx, cy, cz = c
    def P(u, v, w=0.0):
        return Vector((cx + w, cy + u, cz + v)) if plane == 'x' else Vector((cx + u, cy + w, cz + v))
    nrm = Vector((1, 0, 0)) if plane == 'x' else Vector((0, 1, 0))
    outline = palette_outline(size)
    hole = [(-0.42 * size + 0.11 * size * math.cos(k * math.tau / 16), 0.18 * size + 0.13 * size * math.sin(k * math.tau / 16)) for k in range(16)]
    bm = bmesh.new()
    def loop(pts2):
        vs = [bm.verts.new(P(u, v, -thick / 2)) for (u, v) in pts2]
        return [bm.edges.new((vs[i], vs[(i + 1) % len(vs)])) for i in range(len(vs))]
    edges = loop(outline) + loop(hole)
    bmesh.ops.triangle_fill(bm, use_beauty=True, use_dissolve=True, edges=edges)
    faces = list(bm.faces)
    res = bmesh.ops.extrude_face_region(bm, geom=faces)
    nv = [g for g in res["geom"] if isinstance(g, bmesh.types.BMVert)]
    bmesh.ops.translate(bm, vec=nrm * thick, verts=nv)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    edges_b = [e for e in bm.edges if len(e.link_faces) == 2 and e.calc_face_angle(0) > 0.8]
    bmesh.ops.bevel(bm, geom=edges_b, offset=min(0.012, thick * 0.3), segments=2, affect='EDGES')
    b._push(bm, mat)
    if dabs:   # manchas de pintura planas en ambas caras (gotas aplastadas, no bolas)
        cols = ["M_Flower_Yellow", "M_Fabric_Blue", "M_Flower_Geranium", "M_Plant_LeafLight", "M_Flower_White", "M_Flower_Lavender"]
        spots = [(0.35, 0.45), (0.65, 0.15), (0.6, -0.25), (0.25, -0.5), (-0.15, -0.55), (-0.05, 0.5)]
        for (u, v), m in zip(spots, cols):
            for s in (-1, 1):
                q = P(u * size, v * size, s * (thick / 2 + 0.004))
                t = (P(1, 0) - P(0, 0)).normalized()
                b.leaf(q, nrm * s, t, size * random.uniform(0.11, 0.14), m, thick=0.008, res=12, shape='round')
    if brush:   # pincel apoyado cruzando la paleta
        p0, p1 = P(-0.2 * size, -0.75 * size, thick / 2 + 0.02), P(0.95 * size, 0.55 * size, thick / 2 + 0.02)
        d = (p1 - p0).normalized()
        b.seg(p0, p1, 0.012, "M_Museum_WoodDark", seg=8)
        b.seg(p1, p1 + d * 0.05, 0.014, "M_Museum_Brass", seg=8)
        b.seg(p1 + d * 0.05, p1 + d * 0.11, 0.012, "M_Flower_Yellow", seg=8)
