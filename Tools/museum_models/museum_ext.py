"""Museo EXTERIOR (Blender 5.x). Ejecutar: exec(open(...).read()) y llamar build().

Edificio 16 x 12 m, dos plantas + tejado a dos aguas con frontispicio cruzado sobre la entrada.
Silueta: portico con columnas, frontispicio con ojo de buey, chimenea y veleta en forma de PINCEL.
Fachada principal mira a -Y. Los huecos salen de museum_dims (los mismos que usa el interior).
"""
import bpy, math, random, sys
from mathutils import Vector

P = r"D:\TheLivingCanvas\Tools\museum_models"
if P not in sys.path:
    sys.path.insert(0, P)
import importlib, museum_lib as L, museum_dims as D
importlib.reload(L); importlib.reload(D)
from museum_lib import B, Face, wall, col
import museum_garden as G
importlib.reload(G)

PITCH = math.radians(33)
TAN = math.tan(PITCH)
EAVE_Z = D.WT - 0.1


def to_col(ob, c):
    for k in ob.users_collection:
        k.objects.unlink(ob)
    c.objects.link(ob)
    return ob


def faces(b):
    return {'F': Face(b, 'x', D.Y0, -1), 'B': Face(b, 'x', D.Y1, 1),
            'W': Face(b, 'y', D.X0, -1), 'E': Face(b, 'y', D.X1, 1)}


# ----------------------------------------------------------------- cuerpo
def body(cA):
    # plinto de piedra (sobresale 0.14 hacia fuera)
    b = B("Ext_Plinth", 0.5)
    ex = 0.07
    T = D.TH + 0.14
    wall(b, 'x', D.Y0 + D.TH / 2 - ex, D.X0 - 0.07, D.X1 + 0.07, 0, 1.0, T, "M_Museum_Stone", [D.FRONT[0]])
    wall(b, 'x', D.Y1 - D.TH / 2 + ex, D.X0 - 0.07, D.X1 + 0.07, 0, 1.0, T, "M_Museum_Stone", [D.BACK[0]])
    wall(b, 'y', D.X0 + D.TH / 2 - ex, D.IY0, D.IY1, 0, 1.0, T, "M_Museum_Stone")
    wall(b, 'y', D.X1 - D.TH / 2 + ex, D.IY0, D.IY1, 0, 1.0, T, "M_Museum_Stone")
    b.finish(cA)

    # muros de revoco (crema envejecida) con huecos
    b = B("Ext_Walls", 0.5)
    wall(b, 'x', D.Y0 + D.TH / 2, D.X0, D.X1, 1.0, D.WT, D.TH, "M_Museum_Plaster", D.FRONT)
    wall(b, 'x', D.Y1 - D.TH / 2, D.X0, D.X1, 1.0, D.WT, D.TH, "M_Museum_Plaster", D.BACK)
    wall(b, 'y', D.X0 + D.TH / 2, D.IY0, D.IY1, 1.0, D.WT, D.TH, "M_Museum_Plaster", D.WEST)
    wall(b, 'y', D.X1 - D.TH / 2, D.IY0, D.IY1, 1.0, D.WT, D.TH, "M_Museum_Plaster", D.EAST)
    # frontones (triangulos) de los lados cortos y del frontispicio cruzado
    # hastiales con la misma pendiente que el faldon: suben hasta meterse en el tejado (sin ranura bajo el alero)
    for sx in (-1, 1):
        xs = D.X0 if sx < 0 else D.X1 - D.TH
        b.prism([(xs, -6.0, D.WT), (xs, 6.0, D.WT), (xs, 6.0, D.WT + 0.6), (xs, 0.0, D.WT + 0.6 + 6.0 * TAN), (xs, -6.0, D.WT + 0.6)],
                (D.TH, 0, 0), "M_Museum_Plaster", amp=0.01)
    # friso que cierra el hueco entre la coronacion del muro y el faldon (fachadas larga delantera y trasera)
    for y in (D.Y0 + D.TH / 2, D.Y1 - D.TH / 2):
        b.box((0, y, D.WT + 0.28), (16.0, D.TH, 0.56), "M_Museum_Plaster", bev=0, amp=0.01, cuts=10)
    # frontispicio saliente: avanza hasta la linea del alero para que el faldon no le pase por delante
    PF = -6.95
    b.prism([(-3.0, PF, 7.9), (3.0, PF, 7.9), (3.0, PF, 8.05), (0.0, PF, 8.05 + 3.0 * TAN), (-3.0, PF, 8.05)],
            (0, -5.6 - PF, 0), "M_Museum_Plaster", amp=0.01)
    b.box((0, -6.5, 7.86), (6.25, 1.05, 0.14), "M_Museum_Stone", bev=0.02, amp=0.005, cuts=4)   # moldura de base
    b.finish(cA)

    # esquinas de sillares + cornisas (piedra azul grisacea)
    b = B("Ext_Trim_Stone", 0.5)
    zs = [1.15 + 0.62 * i for i in range(int((D.WT - 1.15 - 0.3) / 0.62))]
    for sx in (-1, 1):
        for sy in (-1, 1):
            for i, z in enumerate(zs):
                wf = 0.8 if i % 2 == 0 else 0.5
                ws = 0.5 if i % 2 == 0 else 0.8
                b.box((sx * (8 - wf / 2), sy * (5.6 + 0.235), z), (wf, 0.47, 0.54), "M_Museum_Stone", bev=0.03, amp=0.014, cuts=0)
                b.box((sx * (7.6 + 0.235), sy * (6 - ws / 2), z), (0.47, ws, 0.54), "M_Museum_Stone", bev=0.03, amp=0.014, cuts=0)
    # imposta entre plantas
    b.box((0, D.Y0 - 0.07, 4.3), (16.3, 0.2, 0.34), "M_Museum_Stone", cuts=10)
    b.box((0, D.Y1 + 0.07, 4.3), (16.3, 0.2, 0.34), "M_Museum_Stone", cuts=10)
    b.box((D.X0 - 0.07, 0, 4.3), (0.2, 11.4, 0.34), "M_Museum_Stone", cuts=8)
    b.box((D.X1 + 0.07, 0, 4.3), (0.2, 11.4, 0.34), "M_Museum_Stone", cuts=8)
    # cornisa bajo el alero + dentellones
    b.box((0, D.Y0 - 0.12, D.WT - 0.05), (16.5, 0.34, 0.3), "M_Museum_Stone", cuts=10)
    b.box((0, D.Y1 + 0.12, D.WT - 0.05), (16.5, 0.34, 0.3), "M_Museum_Stone", cuts=10)
    b.box((D.X0 - 0.1, 0, D.WT - 0.05), (0.3, 11.4, 0.3), "M_Museum_Stone", cuts=8)
    b.box((D.X1 + 0.1, 0, D.WT - 0.05), (0.3, 11.4, 0.3), "M_Museum_Stone", cuts=8)
    for i in range(30):
        x = -7.55 + i * 0.52
        for y in (D.Y0 - 0.1, D.Y1 + 0.1):
            b.box((x, y, D.WT - 0.25), (0.2, 0.18, 0.16), "M_Museum_Stone", bev=0.015, amp=0.008, cuts=0)
    b.finish(cA)


# ----------------------------------------------------------------- ventanas
def plant_tuft(b, base, out, alo, up, sc=1.0):
    """Mata de hojas planas alargadas que brotan en abanico (sin bolas)."""
    for k in range(9):
        a = k * math.tau / 9 + random.uniform(-0.3, 0.3)
        radial = (alo * math.cos(a) + out * math.sin(a) * 0.8).normalized()
        t = (radial * 0.6 + up * random.uniform(0.8, 1.4)).normalized()
        n = (up - t * up.dot(t) + radial * 0.3).normalized()
        n = (n - t * n.dot(t)).normalized()
        ln = random.uniform(0.11, 0.16) * sc
        b.leaf(base + t * ln * 0.9, n, t, ln, random.choice(["M_Plant_Leaf", "M_Plant_LeafLight", "M_Leaf_Dark"]), thick=0.005)
        b.seg(base, base + t * ln * 0.3, 0.005, "M_Plant_Leaf")


def small_flower(b, c, n, m):
    t = Vector((n.y, -n.x, 0)).normalized() if abs(n.z) < 0.99 else Vector((1, 0, 0))
    b.leaf(c, n, t, 0.045, m, thick=0.004)
    b.blob(c + n * 0.006, 0.015, "M_Soil", squash=(1, 1, 0.6), sub=1, amp=0.002)
    b.seg(c - n * 0.005, c - Vector((0, 0, 0.18)), 0.004, "M_Plant_Leaf")


WOOD = "M_Museum_Wood"
STONE = "M_Museum_Stone"


def is_arched(c, w, zs, zt):
    """Ventanas de arco rebajado: las grandes de planta baja y el ventanal central sobre la entrada."""
    if zs < D.FL1 and abs((zs - D.FL0) - 0.9) < 0.05 and w >= 1.2:
        return True
    return zs >= D.FL1 and abs(c) < 0.1 and abs((zs - D.FL1) - 0.5) < 0.05


def arch_rise(w):
    return min(0.5, w * 0.3)


def arch_pts(c, zsp, a, bz, n, a0=0.0, a1=math.pi):
    return [(c + a * math.cos(a0 + (a1 - a0) * k / n), zsp + bz * math.sin(a0 + (a1 - a0) * k / n)) for k in range(n + 1)]


def arch_spandrels(b, F, c, w, zt, v0, v1, mat):
    """Enjutas: rellenan las esquinas superiores del hueco recto -> el hueco se lee como arco rebajado.
    Atraviesan todo el muro (v0..v1), asi el interior coincide."""
    rise = arch_rise(w)
    zsp = zt - rise
    ext = tuple(Vector(F.P(0, v1, 0)) - Vector(F.P(0, v0, 0)))
    n = 10
    for (a0, a1, cu) in ((0.0, math.pi / 2, c + w / 2), (math.pi / 2, math.pi, c - w / 2)):
        pts = arch_pts(c, zsp, w / 2, rise, n, a0, a1)
        poly = [F.P(u, v0, z) for (u, z) in pts] + [F.P(cu, v0, zt)]
        b.prism(poly, ext, mat, amp=0.003)


def voussoirs(b, F, c, w, zt):
    """Dovelas de piedra siguiendo el arco, con clave mas grande y salientes de imposta."""
    rise = arch_rise(w)
    zsp = zt - rise
    out = Vector(F.P(0, 1, 0)) - Vector(F.P(0, 0, 0))
    n = 9
    for k in range(n):
        a0, a1 = math.pi * k / n + 0.012, math.pi * (k + 1) / n - 0.012
        key = (k == n // 2)
        t = 0.26 + (0.1 if key else 0.0)
        q = [F.P(c + (w / 2 + rr) * math.cos(aa), 0.0, zsp + (rise + rr) * math.sin(aa)) for (aa, rr) in ((a0, 0), (a1, 0), (a1, t), (a0, t))]
        b.prism(q, tuple(out * (0.11 if key else 0.07)), STONE, amp=0.003)
    for sg in (-1, 1):
        F.box(c + sg * (w / 2 + 0.1), 0.04, zsp - 0.05, 0.2, 0.12, 0.1, STONE, bev=0.015, amp=0.004, cuts=0)


def sash(F, c, w, z0, z1, v, cols, rows, meet=False):
    """Hoja de ventana: marco (travesano inferior mas ancho) + junquillos."""
    iw = w - 0.16
    x0, x1 = c - iw / 2, c + iw / 2
    st = 0.055
    for x in (x0 + st / 2, x1 - st / 2):
        F.box(x, v, (z0 + z1) / 2, st, 0.05, z1 - z0, WOOD, bev=0.008, amp=0.002, cuts=0)
    F.box(c, v, z1 - st / 2, iw, 0.05, st, WOOD, bev=0.008, amp=0.002, cuts=0)
    F.box(c, v, z0 + 0.045, iw, 0.05, 0.09, WOOD, bev=0.008, amp=0.002, cuts=0)
    if meet:
        F.box(c, v + 0.005, (z0 + z1) / 2, 0.075, 0.06, z1 - z0, WOOD, bev=0.008, amp=0.002, cuts=0)
    for i in range(1, cols):
        x = x0 + i * iw / cols
        if meet and abs(x - c) < 0.02:
            continue
        F.box(x, v, (z0 + z1) / 2, 0.028, 0.035, z1 - z0, WOOD, bev=0, amp=0.002, cuts=0)
    for j in range(1, rows):
        F.box(c, v, z0 + 0.09 + j * (z1 - z0 - 0.09) / rows, iw, 0.035, 0.028, WOOD, bev=0, amp=0.002, cuts=0)


def louvered_shutter(S, u, zm, sw, sh_h, v=0.04):
    """Contraventana de librillo: bastidor + lamas finas inclinadas + travesano central."""
    G_ = "M_Museum_Shutter"
    st = 0.06
    for x in (u - sw / 2 + st / 2, u + sw / 2 - st / 2):
        S.box(x, v, zm, st, 0.05, sh_h, G_, bev=0.01, amp=0.003, cuts=1)
    for z in (zm - sh_h / 2 + 0.05, zm + sh_h / 2 - 0.04, zm):
        S.box(u, v, z, sw - 0.02, 0.05, 0.08 if abs(z - zm) > 0.01 else 0.07, G_, bev=0.01, amp=0.003, cuts=0)
    n = int((sh_h - 0.2) / 0.065)
    for k in range(n):
        z = zm - sh_h / 2 + 0.11 + k * 0.065
        if abs(z - zm) < 0.06:
            continue
        S.box(u, v - 0.004, z, sw - 2 * st + 0.01, 0.045, 0.016, G_, rot=(0, 0, 0), bev=0, amp=0.001, cuts=0)
        S.box(u, v + 0.012, z - 0.012, sw - 2 * st + 0.01, 0.006, 0.02, "M_Leaf_Dark", bev=0, amp=0.0, cuts=0)  # sombra de lama


def window_box(fr, F, c, w, zs, color):
    """Jardinera colgada DELANTE del alfeizar (sobre escuadras de hierro): las plantas crecen libres por delante."""
    zb = zs - 0.42
    V = 0.43   # centro del cajon; el alfeizar llega hasta v=0.28
    F.box(c, V, zb, w + 0.12, 0.3, 0.3, "M_Museum_Shutter", bev=0.02, amp=0.004, cuts=2)
    F.box(c, V + 0.005, zb + 0.16, w + 0.2, 0.36, 0.045, "M_Museum_AwningB", bev=0.012, amp=0.003, cuts=2)
    F.box(c, V + 0.005, zb - 0.155, w + 0.18, 0.34, 0.035, "M_Museum_AwningB", bev=0.01, amp=0.003, cuts=2)
    npnl = max(2, int(w / 0.6))
    pw = (w - 0.1) / npnl
    for k in range(npnl):
        u = c - (w - 0.1) / 2 + pw / 2 + k * pw
        F.box(u, V + 0.155, zb, pw - 0.08, 0.012, 0.17, "M_Museum_AwningB", bev=0.004, amp=0.001, cuts=0)
        F.box(u, V + 0.16, zb, pw - 0.13, 0.012, 0.12, "M_Museum_Shutter", bev=0.003, amp=0.001, cuts=0)
    for sg in (-1, 1):   # escuadras: brazo horizontal + tornapunta hasta la pared
        u = c + sg * (w / 2 - 0.08)
        F.box(u, (V + 0.18) / 2, zb - 0.17, 0.04, V - 0.16, 0.04, "M_Iron", bev=0.006, amp=0.001, cuts=0)
        v0 = 0.18 if zb - 0.45 < 1.05 else 0.03   # sobre el zocalo (que sobresale 0.14) en planta baja
        fr.seg(F.P(u, v0, zb - 0.4), F.P(u, V, zb - 0.17), 0.018, "M_Iron", seg=5)
    F.box(c, V, zb + 0.14, w, 0.26, 0.03, "M_Soil", bev=0, amp=0.004, cuts=1)
    out = (Vector(F.P(0, 1, 0)) - Vector(F.P(0, 0, 0))).normalized()
    n = max(2, int(w / 0.55))
    for i in range(n):
        u = c - w / 2 + 0.22 + i * (w - 0.44) / max(1, n - 1)
        G.geranium(fr, Vector(F.P(u, V + 0.04, zb + 0.15)), out, color, sc=1.6)
    for u in (c - w / 2 + 0.12, c + w / 2 - 0.25):
        G.trailing_ivy(fr, Vector(F.P(u, V + 0.17, zb + 0.16)), out, random.uniform(0.25, 0.4), ivy_leaf)


def window(fr, gl, sh, key, c, w, zs, zt, shutters=True, planter=False, juliet=False, hood=False, curtain=True, wb=None):
    F, Gl, S = faces(fr)[key], faces(gl)[key], faces(sh)[key]
    h = zt - zs
    zm = (zs + zt) / 2
    arched = is_arched(c, w, zs, zt)
    rise = arch_rise(w) if arched else 0.0
    zsp = zt - rise
    small = h < 1.0
    Gl.box(c, -0.2, zm, w - 0.08, 0.03, h - 0.08, "M_Museum_Glass", bev=0, amp=0, cuts=0)
    # forro del hueco
    for sg in (-1, 1):
        F.box(c + sg * (w / 2 - 0.05), -0.12, (zs + zsp) / 2, 0.1, 0.5, zsp - zs, WOOD, bev=0.015, amp=0.005, cuts=0)
    F.box(c, -0.12, zs + 0.05, w, 0.5, 0.1, WOOD, bev=0.015, amp=0.005, cuts=0)
    if arched:
        arch_spandrels(fr, F, c, w, zt, -0.4, 0.0, "M_Museum_Plaster")
        pts = arch_pts(c, zsp, w / 2 - 0.05, rise - 0.05, 16)
        for p0, p1 in zip(pts, pts[1:]):
            fr.seg(F.P(p0[0], -0.12, p0[1]), F.P(p1[0], -0.12, p1[1]), 0.05, WOOD, seg=6)
        F.box(c, -0.14, zsp, w - 0.1, 0.08, 0.07, WOOD, bev=0.01, amp=0.003, cuts=0)        # travesano del abanico
        for k in range(1, 6):                                                               # radios del abanico
            a = math.pi * k / 6
            fr.seg(F.P(c, -0.15, zsp + 0.03), F.P(c + (w / 2 - 0.09) * math.cos(a), -0.15, zsp + (rise - 0.09) * math.sin(a)), 0.014, WOOD, seg=5)
        hub = arch_pts(c, zsp + 0.03, 0.14, 0.11, 8)
        for p0, p1 in zip(hub, hub[1:]):
            fr.seg(F.P(p0[0], -0.15, p0[1]), F.P(p1[0], -0.15, p1[1]), 0.016, WOOD, seg=5)
        voussoirs(fr, F, c, w, zt)
        cols = 4 if w > 1.5 else 2
        sash(F, c, w, zs + 0.06, zsp - 0.04, -0.14, cols, 3 if (zsp - zs) > 1.0 else 2, meet=True)
    else:
        F.box(c, -0.12, zt - 0.05, w, 0.5, 0.1, WOOD, bev=0.015, amp=0.005, cuts=0)
        if small:
            sash(F, c, w, zs + 0.05, zt - 0.05, -0.14, 2 if w >= 0.6 else 1, 2)
        else:   # guillotina: hoja baja delante, hoja alta detras
            meet = zs + h * 0.5
            cols = 2 if w >= 1.2 else 1
            sash(F, c, w, zs + 0.06, meet + 0.03, -0.12, cols, 2)
            sash(F, c, w, meet - 0.03, zt - 0.05, -0.165, cols, 2)
        # recerco de piedra con orejetas
        bw = 0.13
        for sg in (-1, 1):
            F.box(c + sg * (w / 2 + bw / 2), 0.03, zm + 0.02, bw, 0.08, h + 0.04, STONE, bev=0.015, amp=0.004, cuts=1)
            F.box(c + sg * (w / 2 + bw + 0.04), 0.03, zt - 0.02, 0.09, 0.08, 0.22, STONE, bev=0.012, amp=0.003, cuts=0)
        F.box(c, 0.03, zt + bw / 2 + 0.02, w + 2 * bw + 0.16, 0.08, bw, STONE, bev=0.015, amp=0.004, cuts=1)
        F.box(c, 0.07, zt + 0.12, 0.22, 0.12, 0.26, STONE, bev=0.02, amp=0.004, cuts=0)
    # cortinas recogidas (tonos claros que contrastan con el cristal)
    if curtain and h > 0.9:
        cm = L.curtain_mat(key, c, zs)
        ctop = zsp - 0.05
        for sg in (-1, 1):
            uc = c + sg * (w / 2 - 0.2)
            Gl.box(uc, -0.173, (zs + ctop) / 2 + 0.05, 0.22, 0.014, ctop - zs - 0.1, cm, bev=0, amp=0.01, cuts=3)
            Gl.blob(uc + sg * 0.03, -0.168, zs + (ctop - zs) * 0.38, 0.04, "M_Museum_Brass", squash=(1.4, 0.6, 0.6), sub=1, amp=0.002)
    # alfeizar de piedra con mensulas
    F.box(c, 0.1, zs - 0.07, w + 0.36, 0.36, 0.12, STONE, bev=0.025, amp=0.008, cuts=0)
    if not juliet:
        for sg in (-1, 1):
            F.box(c + sg * (w / 2 + 0.04), 0.12, zs - 0.22, 0.1, 0.2, 0.18, STONE, bev=0.02, amp=0.004, cuts=0)
    if hood:
        hw, zb = w / 2 + 0.36, zt + 0.12 + 0.13
        o = Vector(F.P(0, 1, 0)) - Vector(F.P(0, 0, 0))
        fr.prism([F.P(c - hw, 0.0, zb), F.P(c + hw, 0.0, zb), F.P(c, 0.0, zb + 0.38)], tuple(o * 0.2), STONE, amp=0.006)
        F.box(c, 0.1, zb - 0.02, 2 * hw + 0.06, 0.2, 0.06, STONE, bev=0.015, amp=0.004, cuts=0)
    if shutters and h > 1.3 and w >= 1.2:
        lst = {'F': D.FRONT, 'B': D.BACK, 'W': D.WEST, 'E': D.EAST}[key]
        lim = 7.15 if key in 'FB' else 5.15          # antes de los sillares de esquina
        zones = []                                  # huecos vecinos con su recerco / marco de puerta
        for (c2, w2, zs2, zt2) in lst:
            if abs(c2 - c) < 1e-3 or zs2 >= zt or zt2 <= zs:
                continue
            m = 0.45 if abs(zs2 - zs) > 0.5 and zs2 < D.FL1 and zt2 - zs2 > 2.0 else 0.32
            zones.append((c2 - w2 / 2 - m, c2 + w2 / 2 + m))
        sides = []
        for sg in (-1, 1):
            start = c + sg * (w / 2 + 0.22)
            avail = lim - abs(start) if sg * start > 0 else 99.0
            for (z0, z1) in zones:
                if sg > 0 and z1 > start:
                    avail = min(avail, z0 - start)
                if sg < 0 and z0 < start:
                    avail = min(avail, start - z1)
            sides.append((sg, avail))
        sw = min([w * 0.36, 0.62] + [a_ for (_, a_) in sides if a_ >= 0.38])
        for (sg, avail) in sides:
            if avail < 0.38:
                continue   # no cabe: ni pisa la ventana vecina ni la puerta ni los sillares
            u = c + sg * (w / 2 + 0.22 + sw / 2)
            ztop = zsp - 0.02 if arched else zt + 0.03       # en ventanas de arco, solo hasta el arranque
            louvered_shutter(S, u, (zs - 0.03 + ztop) / 2, sw, ztop - zs + 0.03)
            for zz in (zs + 0.25, ztop - 0.25):   # bisagras
                S.box(c + sg * (w / 2 + 0.205), 0.04, zz, 0.07, 0.03, 0.035, "M_Iron", bev=0.004, amp=0.001, cuts=0)
            S.box(u + sg * (sw / 2 - 0.08), 0.06, zs + 0.15, 0.03, 0.04, 0.09, "M_Iron", bev=0.004, amp=0.001, cuts=0)  # tope
    if planter:
        wb_ = wb or fr
        window_box(wb_, faces(wb_)[key], c, w, zs, ["M_Flower_Geranium", "M_Flower_Rose", "M_Flower_White"][int(abs(c * 7 + zs)) % 3])
    if juliet:
        F.box(c, 0.2, zs - 0.06, w + 0.5, 0.42, 0.1, STONE, bev=0.025, amp=0.008, cuts=3)
        rail_z = zs + 0.85
        F.box(c, 0.38, rail_z, w + 0.4, 0.05, 0.05, "M_Iron", bev=0.01, amp=0.003, cuts=3)
        F.box(c, 0.38, zs + 0.08, w + 0.4, 0.04, 0.04, "M_Iron", bev=0.008, amp=0.002, cuts=3)
        for k in range(11):
            uu = c - (w + 0.4) / 2 + 0.1 + k * (w + 0.2) / 10
            F.box(uu, 0.38, zs + 0.45, 0.025, 0.025, 0.78, "M_Iron", bev=0, amp=0.002, cuts=0)
        for k in range(5):   # volutas
            uu = c - (w + 0.2) / 2 + 0.2 + k * (w - 0.2) / 4
            ring = [F.P(uu + 0.08 * math.cos(j * math.tau / 12), 0.38, zs + 0.45 + 0.1 * math.sin(j * math.tau / 12)) for j in range(13)]
            for p0, p1 in zip(ring, ring[1:]):
                fr.seg(p0, p1, 0.01, "M_Iron", seg=4)


def awning(b, c, w, zt):
    n = 8
    sw = w / n
    a = math.radians(24)
    for i in range(n):
        m = "M_Museum_AwningA" if i % 2 == 0 else "M_Museum_AwningB"
        x = c - w / 2 + sw / 2 + i * sw
        b.box((x, D.Y0 - 0.5, zt + 0.72), (sw, 1.0, 0.04), m, rot=(a * 57.2958, 0, 0), bev=0, amp=0.008, cuts=1)
        b.box((x, D.Y0 - 0.98, zt + 0.27), (sw, 0.04, 0.2), m, bev=0, amp=0.008, cuts=0)
    for sgn in (-1, 1):
        b.box((c + sgn * (w / 2 + 0.02), D.Y0 - 0.5, zt + 0.52), (0.04, 1.0, 0.04), "M_Iron", rot=(a * 57.2958, 0, 0), bev=0, amp=0.005, cuts=0)


def windows(cA):
    fr, gl, sh, aw = B("Ext_Window_Frames", 0.5), B("Ext_Window_Glass", 0.5), B("Ext_Shutters", 0.5), B("Ext_Awnings", 0.5)
    wb = B("Ext_WindowBoxes", 0.5)
    random.seed(11)
    for (c, w, zs, zt) in D.FRONT[1:]:
        gnd = zs < D.FL1
        over_porch = abs(c) < 3.0   # sobre el tejadillo del portico (PA) o junto a las zancas de la escalinata (PB)
        window(fr, gl, sh, 'F', c, w, zs, zt, shutters=(abs(c) > 0.1), planter=(abs(c) > 0.1 and not over_porch), juliet=(abs(c) < 0.1),
               hood=(not gnd and abs(c) > 0.1), wb=wb)
        if gnd and w > 1.7:
            awning(aw, c, w + 0.5, zt)
    for (c, w, zs, zt) in D.BACK[1:]:
        high = (zs - (D.FL0 if zs < D.FL1 else D.FL1)) > 1.5
        window(fr, gl, sh, 'B', c, w, zs, zt, shutters=(not high) and w >= 1.2, hood=(zs > D.FL1 and not high and w >= 1.2),
               curtain=not high)
    for (c, w, zs, zt) in D.WEST:
        high = (zs - (D.FL0 if zs < D.FL1 else D.FL1)) > 1.5
        window(fr, gl, sh, 'W', c, w, zs, zt, shutters=(not high), curtain=not high)
    for (c, w, zs, zt) in D.EAST:
        high = (zs - (D.FL0 if zs < D.FL1 else D.FL1)) > 1.5
        window(fr, gl, sh, 'E', c, w, zs, zt, shutters=(not high), curtain=not high)
    for b in (fr, gl, sh, aw, wb):
        b.finish(cA)


# ----------------------------------------------------------------- puertas
def door(fr, key, c, w, zs, zt, mat, leaves=2, transom=False, handle=True):
    F = faces(fr)[key]
    h = zt - zs
    zl = zs + 0.05
    zdoor_top = zt - (0.75 if transom else 0.0)
    dh = zdoor_top - zl
    F.box(c - w / 2 + 0.07, -0.1, (zs + zt) / 2, 0.14, 0.5, h, "M_Museum_Wood", bev=0.02, amp=0.01, cuts=1)
    F.box(c + w / 2 - 0.07, -0.1, (zs + zt) / 2, 0.14, 0.5, h, "M_Museum_Wood", bev=0.02, amp=0.01, cuts=1)
    F.box(c, -0.1, zt - 0.07, w, 0.5, 0.14, "M_Museum_Wood", bev=0.02, amp=0.01, cuts=1)
    # puerta de hojas
    lw = (w - 0.28) / leaves
    for i in range(leaves):
        u = c - (w - 0.28) / 2 + lw / 2 + i * lw
        F.box(u, -0.12, zl + dh / 2, lw - 0.02, 0.1, dh, mat, bev=0.02, amp=0.01, cuts=2)
        # cuarterones
        for zz, hh in ((zl + dh * 0.27, dh * 0.36), (zl + dh * 0.74, dh * 0.34)):
            F.box(u, -0.06, zz, lw - 0.3, 0.04, hh, "M_Sign_Board" if mat == "M_Museum_Door" else "M_Museum_WoodDark", bev=0.015, amp=0.008, cuts=0)
        if handle:
            hu = u + (lw / 2 - 0.14) * (1 if i == 0 else -1) if leaves == 2 else u + lw / 2 - 0.14
            F.box(hu, -0.02, zl + dh * 0.5, 0.05, 0.07, 0.3, "M_Museum_Brass", bev=0.01, amp=0.003, cuts=0)
            F.blob(hu, 0.02, zl + dh * 0.5, 0.05, "M_Museum_Brass", sub=1, amp=0.004)
    if transom:
        F.box(c, -0.1, zdoor_top + 0.05, w - 0.28, 0.12, 0.08, "M_Museum_Wood", bev=0.01, amp=0.005, cuts=1)
    return F


def stone_steps(b, cx, yw, sgn, width, top, nsteps, depth, landing, seed=0):
    """Escalinata de sillares: rellano + peldanos de bloques con juntas, bocel redondeado en cada huella
    y zancas laterales con remate inclinado. sgn: hacia donde sale la escalera (-1 = -Y)."""
    rnd = random.Random(seed)
    r = top / (nsteps + 1)
    hw = width / 2

    def blocks(y0, y1, ztop):
        x = cx - hw
        while x < cx + hw - 0.05:
            ln = min(rnd.uniform(0.75, 1.3), cx + hw - x)
            if cx + hw - (x + ln) < 0.3:
                ln = cx + hw - x
            b.box((x + ln / 2, (y0 + y1) / 2, ztop / 2), (ln - 0.014, abs(y1 - y0) - 0.012, ztop),
                  rnd.choice(["M_Museum_Stone", "M_Path_Stone"]), bev=0.025, amp=0.006, cuts=1)
            x += ln
        b.seg((cx - hw + 0.03, y1 + sgn * 0.012, ztop - 0.03), (cx + hw - 0.03, y1 + sgn * 0.012, ztop - 0.03), 0.034,
              "M_Museum_Stone", seg=8)   # bocel
    yl = yw + sgn * landing
    if landing > 1.2:   # rellano en dos hiladas
        blocks(yw, yw + sgn * landing * 0.5, top)
        blocks(yw + sgn * landing * 0.5, yl, top)
    else:
        blocks(yw, yl, top)
    y = yl
    for k in range(1, nsteps + 1):
        y2 = y + sgn * depth
        blocks(y, y2, top - k * r)
        y = y2
    yf = y
    for sx in (-1, 1):   # zancas: muro bajo con remate de piedra inclinado
        x0 = cx + sx * hw
        prof = [(x0, yw, 0.0), (x0, yf, 0.0), (x0, yf, r + 0.22), (x0, yl, top + 0.36), (x0, yw, top + 0.36)]
        b.prism(prof, (sx * 0.34, 0, 0), "M_Museum_Stone", amp=0.006)
        xc = x0 + sx * 0.17
        cap = [(xc - 0.21, yf + sgn * 0.04, r + 0.2), (xc - 0.21, yf + sgn * 0.04, r + 0.3), (xc - 0.21, yl, top + 0.46),
               (xc - 0.21, yw, top + 0.46), (xc - 0.21, yw, top + 0.36), (xc - 0.21, yl, top + 0.36)]
        b.prism(cap, (0.42, 0, 0), "M_Path_StoneWarm", amp=0.004)
        b.box((xc, yf + sgn * 0.1, r + 0.3), (0.42, 0.2, 0.2), "M_Path_StoneWarm", bev=0.03, amp=0.004, cuts=0)   # dado de arranque


def torus_ring(b, c, u, v, out, R, w, d, mat, n=40, m=8):
    """Aro continuo (UNA sola malla cerrada con vertices compartidos): radio mayor R, semiancho radial w, fondo d a lo largo de out."""
    import bmesh
    bm = b.bm
    mi = b._mi(mat)
    ring = []
    for i in range(n):
        th = i * math.tau / n
        rad = u * math.cos(th) + v * math.sin(th)
        row = []
        for k in range(m):
            ph = k * math.tau / m + math.pi / m
            row.append(bm.verts.new(c + rad * (R + w * math.cos(ph)) + out * (d * math.sin(ph))))
        ring.append(row)
    fs = []
    for i in range(n):
        for k in range(m):
            f = bm.faces.new((ring[i][k], ring[(i + 1) % n][k], ring[(i + 1) % n][(k + 1) % m], ring[i][(k + 1) % m]))
            f.material_index = mi
            f.smooth = False
            fs.append(f)
    bmesh.ops.recalc_face_normals(bm, faces=fs)


def oculus(fr, gl, c, out, r):
    """Ojo de buey: cristal, aro de laton, cruceta y anillo de piedra. Los aros son toros continuos (antes 28 cilindros sueltos
    cada uno) y el cristal queda por delante de la pared: el muro tiene deformacion y en el hastial -X el cristal quedaba 1 cm enterrado."""
    out = Vector(out).normalized()
    u = Vector((0, 0, 1)).cross(out).normalized()
    v = Vector((0, 0, 1))
    gl.leaf(c + out * 0.075, out, u, r, "M_Museum_Glass", thick=0.03, res=32, shape='disc')
    torus_ring(fr, c + out * 0.07, u, v, out, r, 0.03, 0.035, "M_Museum_Brass")
    torus_ring(fr, c + out * 0.05, u, v, out, r + 0.12, 0.075, 0.065, "M_Museum_Stone", n=48)
    for d in (u, v):
        fr.seg(c + out * 0.09 - d * r, c + out * 0.09 + d * r, 0.016, "M_Museum_Brass", seg=6)
    q = c + out * 0.07 + v * (r + 0.12)   # clave
    fr.box(tuple(q), (abs(u.x) * 0.18 + abs(out.x) * 0.14, abs(u.y) * 0.18 + abs(out.y) * 0.14, 0.26), "M_Museum_Stone",
           bev=0.02, amp=0.004, cuts=0)


def entrance(cA):
    fr, gl = B("Ext_Entrance", 0.5), B("Ext_Entrance_Glass", 0.5)
    c0 = D.FRONT[0]
    door(fr, 'F', 0.0, 2.4, D.FL0, c0[3], "M_Museum_Door", leaves=2, transom=True)
    Gf = faces(gl)['F']
    Gf.box(0.0, -0.2, D.FRONT[0][3] - 0.375, 2.1, 0.03, 0.66, "M_Museum_Glass", bev=0, amp=0, cuts=0)
    F = faces(fr)['F']
    for k in range(-3, 4):  # radios del montante
        F.box(k * 0.28, -0.13, D.FRONT[0][3] - 0.375, 0.035, 0.05, 0.68, "M_Museum_Wood", bev=0, amp=0.004, cuts=0)
    # arquitrabe de piedra
    F.box(0, 0.05, c0[3] + 0.12, 2.86, 0.3, 0.26, "M_Museum_Stone", bev=0.03, amp=0.012, cuts=3)
    for sgn in (-1, 1):
        F.box(sgn * 1.33, 0.05, (D.FL0 + c0[3]) / 2, 0.2, 0.3, c0[3] - D.FL0, "M_Museum_Stone", bev=0.03, amp=0.012, cuts=2)
    # escalinata principal: rellano bajo el portico + 2 peldanos, con zancas
    stone_steps(fr, 0.0, D.Y0, -1, 5.4, D.FL0, 2, 0.45, 1.7, seed=3)
    # portico: columnas, viga, rotulo y cubierta
    for sgn in (-1, 1):
        x = sgn * 2.25
        fr.cyl((x, -7.4, D.FL0 + 1.65), 0.17, 3.3, "M_Museum_Plaster", seg=14, r2=0.15, bev=0, amp=0.008)
        fr.box((x, -7.4, D.FL0 + 0.1), (0.44, 0.44, 0.2), "M_Museum_Stone", bev=0.03, amp=0.01, cuts=0)
        fr.box((x, -7.4, D.FL0 + 3.35), (0.5, 0.5, 0.16), "M_Museum_Stone", bev=0.03, amp=0.01, cuts=0)
    fr.box((0, -7.0, 3.95), (5.3, 2.0, 0.3), "M_Museum_Stone", bev=0.03, amp=0.012, cuts=4)
    fr.box((0, -8.02, 3.95), (4.6, 0.08, 0.56), "M_Sign_Board", bev=0.02, amp=0.006, cuts=2)
    fr.text("MUSEUM", (0, -8.1, 3.95), 0.36, "M_Sign_Letters", ext=0.03)
    ang = 10
    fr.box((0, -6.98, 4.48), (5.8, 2.2, 0.16), "M_Museum_Roof", rot=(ang, 0, 0), bev=0.02, amp=0.012, cuts=4)
    for i in range(14):
        fr.box((-2.6 + i * 0.4, -6.98, 4.6), (0.06, 2.1, 0.06), "M_Museum_Roof", rot=(ang, 0, 0), bev=0, amp=0.008, cuts=0)
    # farolillos
    for sgn in (-1, 1):
        fr.box((sgn * 1.9, -6.16, 2.4), (0.06, 0.22, 0.3), "M_Museum_Brass", bev=0, amp=0.003, cuts=0)
        fr.box((sgn * 1.9, -6.34, 2.55), (0.2, 0.2, 0.3), "M_Lamp_Glow", bev=0.02, amp=0.004, cuts=0)
        fr.box((sgn * 1.9, -6.34, 2.74), (0.26, 0.26, 0.05), "M_Museum_Metal", bev=0.01, amp=0.003, cuts=0)
    # ojo de buey del frontispicio
    oculus(fr, gl, Vector((0, -6.95, 9.0)), Vector((0, -1, 0)), 0.38)
    # puerta trasera + peldano
    door(fr, 'B', 0.0, 1.4, D.FL0, D.FL0 + 2.6, "M_Museum_Wood", leaves=1, transom=False)
    stone_steps(fr, 0.0, D.Y1, 1, 2.0, D.FL0, 2, 0.32, 1.0, seed=7)
    # ojos de buey de los hastiales laterales
    for sx in (-1, 1):
        oculus(fr, gl, Vector((sx * 8.0, 0, 10.0)), Vector((sx, 0, 0)), 0.5)
    fr.finish(cA)
    gl.finish(cA)


# ----------------------------------------------------------------- tejado
def roof(cA):
    b = B("Ext_Roof_Main", 0.5)
    run = 6.8
    L = run / math.cos(PITCH)
    rise = run * TAN
    zc = EAVE_Z + rise / 2 + 0.12
    nrm = {1: (0, math.sin(PITCH), math.cos(PITCH)), -1: (0, -math.sin(PITCH), math.cos(PITCH))}
    for s in (1, -1):  # s=+1 vertiente trasera (+y)
        rx = -s * math.degrees(PITCH)
        b.box((0, s * run / 2, zc), (18.0, L, 0.3), "M_Museum_Roof", rot=(rx, 0, 0), bev=0.03, amp=0.018, cuts=10)
        n = nrm[s]
        # nervios de teja (direccion de pincelada: de alero a cumbrera)
        for i in range(36):
            x = -8.75 + i * 0.5
            o = 0.19
            b.box((x, s * run / 2 + n[1] * o, zc + n[2] * o), (0.07, L - 0.25, 0.06), "M_Museum_Roof", rot=(rx, 0, 0), bev=0, amp=0.01, cuts=3)
        # hiladas
        for j in range(1, 15):
            t = (j / 15.0 - 0.5) * (L - 0.3)
            ty, tz = math.cos(PITCH) * t * (-s) , math.sin(PITCH) * t
            b.box((0, s * run / 2 + ty + n[1] * 0.17, zc + tz + n[2] * 0.17), (17.8, 0.07, 0.05), "M_Museum_Roof", rot=(rx, 0, 0), bev=0, amp=0.01, cuts=8)
        # tabica del hastial
        for sx in (-1, 1):
            b.box((sx * 9.0, s * run / 2, zc), (0.12, L + 0.05, 0.36), "M_Museum_WoodDark", rot=(rx, 0, 0), bev=0.02, amp=0.01, cuts=4)
    ridge_z = EAVE_Z + rise + 0.12 + 0.2
    b.box((0, 0, ridge_z), (18.1, 0.55, 0.32), "M_Museum_Roof", bev=0.04, amp=0.015, cuts=10)
    b.finish(cA)

    # frontispicio cruzado
    b = B("Ext_Roof_CrossGable", 0.5)
    hr = 3.2
    L2 = hr / math.cos(PITCH)
    zc2 = EAVE_Z + hr * TAN / 2 + 0.12
    ylen = 5.0
    yc = D.Y0 - 1.0 + ylen / 2 - 0.0
    yc = -7.0 + ylen / 2
    for s in (1, -1):
        ry = s * math.degrees(PITCH)
        b.box((s * hr / 2, yc, zc2), (L2, ylen, 0.3), "M_Museum_Roof", rot=(0, ry, 0), bev=0.03, amp=0.018, cuts=6)
        for i in range(10):
            y = -6.8 + i * 0.5
            nx = s * math.sin(PITCH) if False else s * math.sin(PITCH)
            b.box((s * hr / 2 + nx * 0.19, y, zc2 + math.cos(PITCH) * 0.19), (L2 - 0.25, 0.07, 0.06), "M_Museum_Roof", rot=(0, ry, 0), bev=0, amp=0.01, cuts=3)
        b.box((s * hr / 2, -7.0, zc2), (L2 + 0.05, 0.12, 0.36), "M_Museum_WoodDark", rot=(0, ry, 0), bev=0.02, amp=0.01, cuts=3)
    b.box((0, yc, EAVE_Z + hr * TAN + 0.12 + 0.2), (0.5, ylen + 0.1, 0.3), "M_Museum_Roof", bev=0.04, amp=0.015, cuts=4)
    b.finish(cA)

    # canalones y bajantes
    b = B("Ext_Gutters", 0.5)
    for s in (-1, 1):
        if s > 0:
            b.box((0, s * 6.78, EAVE_Z - 0.12), (18.0, 0.16, 0.13), "M_Museum_Metal", bev=0.02, amp=0.006, cuts=8)
        else:   # delante, el canalon se corta en el frontispicio
            for sx in (-1, 1):
                b.box((sx * 6.08, s * 6.78, EAVE_Z - 0.12), (5.85, 0.16, 0.13), "M_Museum_Metal", bev=0.02, amp=0.006, cuts=4)
    for sx in (-1, 1):
        for sy in (-1, 1):
            b.cyl((sx * 7.45, sy * 6.4, (EAVE_Z - 0.1) / 2 + 0.05), 0.07, EAVE_Z - 0.1, "M_Museum_Metal", seg=10, bev=0, amp=0.005)
    b.finish(cA)

    # chimenea: fuste de piedra con hiladas, coronacion escalonada y dos tubos de barro
    b = B("Ext_Chimney", 0.5)
    cx, cy, z0, z1 = 5.0, 2.2, 10.0, 13.9
    b.box((cx, cy, (z0 + z1) / 2), (1.15, 0.95, z1 - z0), "M_Museum_Stone", bev=0.04, amp=0.012, cuts=3)
    for zz in (11.75, 12.45, 13.15):
        b.box((cx, cy, zz), (1.21, 1.01, 0.07), "M_Path_StoneWarm", bev=0.015, amp=0.003, cuts=1)
    for k, (dw, hh) in enumerate(((0.12, 0.1), (0.24, 0.1), (0.14, 0.1))):
        b.box((cx, cy, z1 + 0.05 + k * 0.1), (1.15 + dw, 0.95 + dw, hh), "M_Museum_Stone", bev=0.02, amp=0.004, cuts=0)
    for dx in (-0.26, 0.26):
        zt_ = z1 + 0.3
        b.cyl((cx + dx, cy, zt_ + 0.27), 0.15, 0.54, "M_Museum_Roof", seg=14, r2=0.11, bev=0, amp=0.004)
        b.cyl((cx + dx, cy, zt_ + 0.4), 0.14, 0.05, "M_Museum_Roof", seg=14, bev=0, amp=0.002)
        b.cyl((cx + dx, cy, zt_ + 0.56), 0.135, 0.06, "M_Museum_Roof", seg=14, bev=0, amp=0.002)
        b.cyl((cx + dx, cy, zt_ + 0.595), 0.1, 0.012, "M_Floor_Dark", seg=12, bev=0, amp=0.0)
    b.finish(cA)

    # veleta: PINCEL sobre la cumbrera (firma de la silueta)
    b = B("Ext_Brush_Vane", 0.5)
    zr = 0.0
    b.cyl((0, 0, zr + 0.35), 0.1, 0.7, "M_Museum_Stone", seg=10, r2=0.07, bev=0, amp=0.006)
    b.cyl((0, 0, zr + 1.35), 0.04, 1.3, "M_Museum_Metal", seg=8, bev=0, amp=0.003)
    b.cyl((0, 0, zr + 2.0), 0.075, 0.3, "M_Museum_Brass", seg=10, r2=0.06, bev=0, amp=0.004)  # virola
    b.cyl((0, 0, zr + 2.35), 0.08, 0.5, "M_Museum_WoodDark", seg=10, r2=0.1, bev=0, amp=0.005)  # mango (cabeza abajo)
    b.blob((0, 0, zr + 2.78), 0.12, "M_Flower_Yellow", squash=(1, 1, 1.9), sub=1, amp=0.012)  # punta con pintura
    b.box((0.35, 0, zr + 1.6), (0.7, 0.02, 0.28), "M_Museum_Metal", bev=0, amp=0.004, cuts=0)  # aleta
    ob = b.finish(cA)
    from mathutils import Matrix
    ob.data.transform(Matrix.Scale(1.7, 4))
    ob.location = (0, 0, ridge_z + 0.16)


IVY_MATS = ["M_Leaf_Dark", "M_Leaf_Dark", "M_Plant_Leaf", "M_Ivy_Light"]


def ivy_leaf(b, pos, out, up, size):
    """Hoja de hiedra plana y lobulada, mirando hacia fuera y algo hacia arriba, con la punta caida."""
    n = (out * 0.85 + up * 0.35 + Vector((random.uniform(-0.3, 0.3), random.uniform(-0.3, 0.3), random.uniform(-0.15, 0.15)))).normalized()
    t = (-up * 0.7 + Vector((random.uniform(-0.6, 0.6), random.uniform(-0.6, 0.6), 0)) + out * 0.2)
    t = (t - n * t.dot(n)).normalized()
    b.leaf(pos, n, t, size, random.choice(IVY_MATS))
    b.seg(pos - out * 0.02, pos + t * size * 0.15, 0.005, "M_Bark")  # peciolo


def ivy_wall(b, F, u0, umin, umax, ztop, seed, stems=3):
    """Hiedra que trepa por una pared: tallos que serpentean y se ramifican, hojas densas abajo."""
    random.seed(seed)
    out = (Vector(F.P(0, 1, 0)) - Vector(F.P(0, 0, 0))).normalized()
    along = (Vector(F.P(1, 0, 0)) - Vector(F.P(0, 0, 0))).normalized()
    up = Vector((0, 0, 1))

    def vof(z):  # separacion de la pared: rodea zocalo e imposta
        if z < 1.08:
            return 0.17
        if 4.05 < z < 4.58:
            return 0.2
        return 0.035

    tips = [(u0 + random.uniform(-0.15, 0.15), 0.05, ztop * random.uniform(0.75, 1.0)) for _ in range(stems)]
    for k in range(stems + 3):
        if k < stems:
            u, z, zt = tips[k]
        else:  # ramas laterales mas cortas
            u, z, zt = u0 + random.uniform(-0.3, 0.3), random.uniform(0.8, ztop * 0.6), 0
            zt = z + random.uniform(1.2, 2.4)
        prev = Vector(F.P(u, vof(z), z))
        du = random.uniform(-0.03, 0.03)
        while z < zt:
            du = max(-0.06, min(0.06, du + random.gauss(0, 0.025)))
            u = max(umin, min(umax, u + du))
            z += 0.09
            cur = Vector(F.P(u, vof(z), z))
            b.seg(prev, cur, 0.014 if k < stems else 0.01, "M_Bark")
            prev = cur
            dens = 1.0 - 0.5 * (z / ztop)
            big = 1.0 + 0.35 * (1.0 - z / ztop)
            for _ in range(3 if random.random() < dens else 2):
                ou = random.uniform(-0.16, 0.16)
                p = Vector(F.P(max(umin, min(umax, u + ou)), vof(z) + 0.02 + random.uniform(0, 0.03), z + random.uniform(-0.05, 0.05)))
                ivy_leaf(b, p, out, up, random.uniform(0.06, 0.095) * big)


def ivy_column(b, cx, cy, z0, z1, phase, seed):
    random.seed(seed)
    up = Vector((0, 0, 1))
    prev = None
    z = z0
    while z < z1:
        a = phase + (z - z0) * 2.2
        r = 0.19
        cur = Vector((cx + math.cos(a) * r, cy + math.sin(a) * r, z))
        if prev:
            b.seg(prev, cur, 0.011, "M_Bark")
        prev = cur
        out = Vector((math.cos(a), math.sin(a), 0))
        if random.random() < 0.95 - 0.35 * (z - z0) / (z1 - z0):
            for s in (-1, 0, 1):
                aa = a + s * 0.45 + random.uniform(-0.15, 0.15)
                p = Vector((cx + math.cos(aa) * 0.21, cy + math.sin(aa) * 0.21, z + random.uniform(-0.03, 0.03)))
                ivy_leaf(b, p, Vector((math.cos(aa), math.sin(aa), 0)), up, random.uniform(0.05, 0.075))
        z += 0.055


def dormers(cA):
    """Buhardillas: rompen el gran faldon y dan escala al tejado."""
    b = B("Ext_Roof_Dormers", 0.5)
    a = math.radians(40)
    for (x, s) in ((-5.0, -1), (5.0, -1), (-4.5, 1), (1.5, 1)):
        yf, yb = s * 4.4, s * 1.8
        yc, dep = (yf + yb) / 2, abs(yf - yb)
        b.box((x, yc, 10.1), (1.7, dep, 1.6), "M_Museum_Plaster", bev=0.03, amp=0.012, cuts=1)
        for sx in (-1, 1):  # pilastrillas de esquina
            b.box((x + sx * 0.8, yf + s * 0.03, 10.4), (0.16, 0.12, 1.0), "M_Museum_Stone", bev=0.02, amp=0.008, cuts=0)
        b.box((x, yf + s * 0.02, 10.33), (0.72, 0.03, 0.62), "M_Museum_Glass", bev=0, amp=0, cuts=0)
        for (dx, dz, sx_, sz_) in ((-0.39, 10.33, 0.08, 0.78), (0.39, 10.33, 0.08, 0.78), (0, 9.99, 0.86, 0.08), (0, 10.67, 0.86, 0.08),
                                   (0, 10.33, 0.035, 0.62), (0, 10.33, 0.7, 0.035)):
            b.box((x + dx, yf + s * 0.05, dz), (sx_, 0.07, sz_), "M_Museum_Wood", bev=0.008, amp=0.004, cuts=0)
        b.box((x, yf + s * 0.1, 9.93), (1.0, 0.2, 0.06), "M_Museum_Stone", bev=0.015, amp=0.006, cuts=0)
        ycr = yc + s * 0.15
        L2 = 1.05 / math.cos(a)
        top = 10.9 + 0.85 * math.tan(a)
        for sx in (-1, 1):
            b.box((x + sx * 0.5, ycr, 10.9 + 0.85 * math.tan(a) / 2 + 0.12), (L2, dep + 0.3, 0.14), "M_Museum_Roof",
                  rot=(0, sx * math.degrees(a), 0), bev=0.02, amp=0.01, cuts=2)
        b.prism([(x - 0.85, yf, 10.9), (x + 0.85, yf, 10.9), (x, yf, top)], (0, -s * 0.3, 0), "M_Museum_Plaster", amp=0.008)
        b.box((x, ycr, top + 0.14), (0.2, dep + 0.32, 0.12), "M_Museum_Roof", bev=0.02, amp=0.008, cuts=2)
    b.finish(cA)


def facade_details(cA, cP):
    random.seed(44)
    b = B("Ext_Facade_Details", 0.5)
    # respiraderos enrejados del sotano en el zocalo
    vents = [('F', x) for x in (-6.8, -3.9, 3.9, 6.8)] + [('B', x) for x in (-6.0, -3.4, 3.4, 6.0)] + \
            [('W', y) for y in (-1.5, 2.2)] + [('E', y) for y in (-1.6, 2.0)]
    for key, u in vents:
        F = faces(b)[key]
        F.box(u, 0.15, 0.55, 0.56, 0.03, 0.26, "M_Floor_Dark", bev=0, amp=0.004, cuts=0)
        for k in range(5):
            F.box(u - 0.22 + k * 0.11, 0.17, 0.55, 0.025, 0.025, 0.28, "M_Museum_Metal", bev=0, amp=0.003, cuts=0)
        F.box(u, 0.2, 0.38, 0.74, 0.12, 0.06, "M_Museum_Stone", bev=0.015, amp=0.006, cuts=0)
    # hiedra de verdad: tallos ramificados + hojas lobuladas planas
    ivy_wall(b, faces(b)['E'], -0.85, -1.45, -0.28, 7.4, seed=7, stems=4)
    for cx, ph in ((-2.25, 0.0), (2.25, 2.0)):
        ivy_column(b, cx, -7.4, D.FL0 + 0.32, D.FL0 + 2.7, ph, seed=int(ph * 10) + 3)
    b.finish(cA)

    def watering_can(b):
        """Regadera: cuerpo pintado con aros de cinc, cuello, asa superior en arco, asa trasera y cano con alcachofa."""
        b.cyl((0, 0, 0.14), 0.11, 0.24, "M_Museum_Shutter", seg=18, r2=0.105, bev=0, amp=0.002)
        for zz in (0.025, 0.255):
            b.cyl((0, 0, zz), 0.116, 0.022, "M_Museum_Metal", seg=18, bev=0, amp=0.001)
        b.cyl((0, 0, 0.285), 0.105, 0.04, "M_Museum_Shutter", seg=18, r2=0.07, bev=0, amp=0.001)
        b.cyl((-0.02, 0, 0.315), 0.055, 0.03, "M_Museum_Metal", seg=14, bev=0, amp=0.001)
        arc = [Vector((-0.09 + 0.15 * t, 0, 0.3 + 0.14 * math.sin(math.pi * t))) for t in [k / 10 for k in range(11)]]
        for p0, p1 in zip(arc, arc[1:]):
            b.seg(p0, p1, 0.011, "M_Museum_Metal", seg=6)
        rear = [Vector((-0.105 - 0.07 * math.sin(math.pi * t), 0, 0.22 - 0.14 * t)) for t in [k / 8 for k in range(9)]]
        for p0, p1 in zip(rear, rear[1:]):
            b.seg(p0, p1, 0.011, "M_Museum_Metal", seg=6)
        sp0, sp1 = Vector((0.09, 0, 0.07)), Vector((0.36, 0, 0.33))
        b.seg(sp0, sp1, 0.017, "M_Museum_Shutter", seg=8)
        b.seg(sp0, sp0 + (sp1 - sp0) * 0.15, 0.03, "M_Museum_Shutter", seg=8)
        d = (sp1 - sp0).normalized()
        b.seg(sp1, sp1 + d * 0.05, 0.032, "M_Museum_Brass", seg=10)
        b.leaf(sp1 + d * 0.055, d, Vector((0, 1, 0)), 0.04, "M_Museum_Brass", thick=0.006, res=14, shape='disc')

    def crates(b):
        """Cajas de fruta de listones (con huecos), apiladas; la de arriba con macetitas de barro."""
        def crate(cx, cy, cz, yaw, w=0.5, d=0.34, h=0.28):
            ca, sa = math.cos(math.radians(yaw)), math.sin(math.radians(yaw))
            def P(x, y, z):
                return (cx + x * ca - y * sa, cy + x * sa + y * ca, cz + z)
            for sx in (-1, 1):
                for sy in (-1, 1):
                    b.box(P(sx * (w / 2 - 0.02), sy * (d / 2 - 0.02), h / 2), (0.04, 0.04, h), "M_Museum_WoodDark",
                          rot=(0, 0, yaw), bev=0.004, amp=0.001, cuts=0)
            for zz in (0.045, 0.14, 0.235):
                for sy in (-1, 1):
                    b.box(P(0, sy * d / 2, zz), (w, 0.014, 0.075), "M_Museum_Wood", rot=(0, 0, yaw), bev=0.003, amp=0.001, cuts=0)
                for sx in (-1, 1):
                    b.box(P(sx * w / 2, 0, zz), (0.014, d, 0.075), "M_Museum_Wood", rot=(0, 0, yaw), bev=0.003, amp=0.001, cuts=0)
            for yy in (-d / 3, 0, d / 3):
                b.box(P(0, yy, 0.012), (w - 0.02, 0.08, 0.014), "M_Museum_Wood", rot=(0, 0, yaw), bev=0.003, amp=0.001, cuts=0)
            return P
        crate(0.0, 0.0, 0.0, 6)
        crate(0.55, 0.04, 0.0, -5)
        P = crate(0.28, 0.02, 0.285, 14)
        for (x, y) in ((-0.13, -0.06), (0.0, 0.07), (0.13, -0.05)):
            q = P(x, y, 0.03)
            b.cyl((q[0], q[1], q[2] + 0.06), 0.06, 0.12, "M_Museum_Roof", seg=12, r2=0.045, bev=0, amp=0.002)
            b.cyl((q[0], q[1], q[2] + 0.125), 0.065, 0.02, "M_Museum_Roof", seg=12, bev=0, amp=0.001)
    to_col(L.prop("Prop_WateringCan", (1.8, 7.0, 0.0), -20, watering_can), cP)
    to_col(L.prop("Prop_Crates", (-2.3, 7.05, 0.0), 0, crates), cP)


# ----------------------------------------------------------------- entorno
def path_x(y):
    """Eje del sendero: sale recto de la escalinata (x=0) y entra en el centro del porton con una S muy suave."""
    y0, y1 = -8.5, FENCE[2] + 0.55
    s = min(max((y0 - y) / (y0 - y1), 0.0), 1.0)
    gx = math.sin((FENCE[2] + 9) * 0.22) * 1.2   # misma formula que el porton en stone_fence
    return gx * s * s * (3 - 2 * s)


def path_w(y):
    """Semiancho: ensancha al pie de la escalinata (plazoleta) y se queda en ~1 m."""
    t = min(max((-8.5 - y) / 2.4, 0.0), 1.0)
    return 1.0 + 0.8 * (1.0 - t * t * (3 - 2 * t)) + 0.06 * math.sin(y * 1.7)


def ground(cG):
    b = B("Env_Terrain", 0.25)
    b.box((0, -4, -0.2), (48, 44, 0.4), "M_Ground_Grass", bev=0, amp=0.045, cuts=24)
    b.finish(cG)
    # sendero: cinta continua de tierra + losas irregulares escalonadas; arranca ancho al pie de la escalinata y
    # se estrecha hasta el centro del porton (antes: ondulaba +-1.2 m, desalineado con escalera y porton)
    import bmesh
    rnd = random.Random(5)
    b = B("Env_Path", 0.5)
    bm = b.bm
    yA, yB = -8.5, FENCE[2] + 0.55
    n = int((yA - yB) / 0.3)
    ys = [yA - (yA - yB) * i / n for i in range(n + 1)]
    mi_earth = b._mi("M_Ground_Earth")
    rows = []
    for y in ys:
        cx, w = path_x(y), path_w(y)
        row = []
        for f, z in ((-1.0, 0.012), (-0.5, 0.035), (0.0, 0.045), (0.5, 0.035), (1.0, 0.012)):
            wob = rnd.uniform(-0.07, 0.07) if abs(f) == 1.0 else rnd.uniform(-0.02, 0.02)
            row.append(bm.verts.new((cx + f * (w + wob), y + rnd.uniform(-0.03, 0.03), z)))
        rows.append(row)
    fs = []
    for i in range(len(rows) - 1):
        for k in range(4):
            f = bm.faces.new((rows[i][k], rows[i + 1][k], rows[i + 1][k + 1], rows[i][k + 1]))
            f.material_index = mi_earth
            f.smooth = False
            fs.append(f)
    bmesh.ops.recalc_face_normals(bm, faces=fs)
    mats = ["M_Path_Stone", "M_Path_StoneWarm", "M_Path_StoneWarm", "M_Museum_Stone"]

    def slab(x, y, sx, sy):
        nv = rnd.choice((6, 7, 8))
        yaw = rnd.uniform(-0.2, 0.2)
        pts = []
        for k in range(nv):
            a = k * math.tau / nv + rnd.uniform(-0.15, 0.15)
            px_, py_ = math.cos(a) * sx * rnd.uniform(0.88, 1.1), math.sin(a) * sy * rnd.uniform(0.88, 1.1)
            pts.append((x + px_ * math.cos(yaw) - py_ * math.sin(yaw), y + px_ * math.sin(yaw) + py_ * math.cos(yaw), 0.035))
        b.prism(pts, (0, 0, 0.055), rnd.choice(mats), bev=0.015, amp=0.01)

    y, row_i = yA - 0.4, 0
    while y > yB + 0.35:
        cx, w = path_x(y), path_w(y)
        cnt = 3 if w > 1.3 else 2
        cnt = cnt if row_i % 2 == 0 else cnt - 1
        step = min(0.9, (2 * w - 0.5) / max(cnt, 1))
        for i in range(cnt):
            slab(cx + (i - (cnt - 1) / 2) * step + rnd.uniform(-0.06, 0.06), y + rnd.uniform(-0.05, 0.05),
                 rnd.uniform(0.28, 0.37), rnd.uniform(0.2, 0.27))
        y -= rnd.uniform(0.56, 0.66)
        row_i += 1
    y = yA - 0.2     # piedras pequenas en los bordes: unen el sendero con la hierba
    while y > yB:
        cx, w = path_x(y), path_w(y)
        for sd in (-1, 1):
            if rnd.random() < 0.7:
                r = rnd.uniform(0.1, 0.16)
                b.blob((cx + sd * (w + rnd.uniform(-0.04, 0.08)), y + rnd.uniform(-0.15, 0.15), 0.03), r, rnd.choice(mats),
                       squash=(1.2, 0.9, 0.45), sub=1, amp=0.01, rot=(0, 0, rnd.uniform(0, 180)))
        y -= rnd.uniform(0.45, 0.7)
    b.finish(cG)


def bush(b, c, r, n=4, big=False):
    """Rosal (silueta reconocible): copa ordenada + rosas."""
    G.rose_bush(b, c, r, roses=int(5 + r * 7))


def flower(b, c, h=0.45, m="M_Flower_Yellow"):
    x, y, z = c
    b.cyl((x, y, z + h / 2), 0.012, h, "M_Plant_Leaf", seg=5, bev=0, amp=0.006)
    b.blob((x + 0.04, y, z + h * 0.35), 0.05, "M_Plant_LeafLight", squash=(1.6, 0.5, 0.35), sub=1, amp=0.006)
    for k in range(6):
        a = k * math.tau / 6
        b.blob((x + math.cos(a) * 0.065, y + math.sin(a) * 0.065, z + h), 0.045, m, squash=(1, 1, 0.45), sub=1, amp=0.006)
    b.blob((x, y, z + h + 0.01), 0.035, "M_Soil", squash=(1, 1, 0.6), sub=1, amp=0.004)


def cypress(b, tx, ty, hgt):
    """Cipres en llama: UNA sola piel continua (tronco + copa + punta) con mechones que suben en espiral.
    Antes eran ~26 bolas sueltas y una punta separada; ahora los anillos comparten vertices de abajo a arriba."""
    import bmesh
    rng = random.Random(int(tx * 100) * 7919 + int(ty * 100))   # propio: no altera la secuencia aleatoria global
    N = 12                              # lados por anillo
    zf0, zf1 = 0.9, 0.9 + hgt           # tramo de copa llena
    top = zf1 + 0.7                     # apice
    R = int(top / 0.22) + 1
    lean = rng.uniform(-0.25, 0.25)
    sm = lambda x: 0.0 if x <= 0 else 1.0 if x >= 1 else x * x * (3 - 2 * x)
    bm = b.bm
    mi_bark, mi_a, mi_b = b._mi("M_Bark"), b._mi("M_Leaf_Dark"), b._mi("M_Plant_Leaf")
    rings = []
    for i in range(R - 1):                # el ultimo anillo (r=0) se sustituye por el apice
        z = top * i / (R - 1)
        t = min(max((z - zf0) / hgt, 0.0), 1.0)
        trunk = 0.2 - 0.05 * min(z / 0.9, 1.0)
        rf = 0.85 * math.sin(math.pi * (0.1 + 0.9 * t)) ** 0.7 * (1.0 - 0.5 * t) + 0.1
        w = sm((z - 0.55) / 0.5)                       # 0 en el tronco, 1 en la copa
        r = trunk * (1 - w) + rf * w
        if z > zf1:                                    # punta: afina hasta cerrar en un punto
            r *= 1.0 - sm((z - zf1) / 0.7)
        a = t * 4.0
        off = (0.1 + 0.08 * math.sin(i * 1.7)) * w
        cx, cy = tx + math.cos(a) * off + lean * t * t, ty + math.sin(a) * off
        ring = []
        for j in range(N):
            th = j * math.tau / N
            lobe = 1.0 + 0.22 * w * math.sin(3 * th + 5.5 * t * math.tau / 2) + rng.uniform(-0.07, 0.07) * w
            rr = r * lobe
            ring.append(bm.verts.new((cx + math.cos(th) * rr, cy + math.sin(th) * rr, z)))
        rings.append(ring)
    apex = bm.verts.new((tx + lean, ty, top + 0.1))
    patch = {}
    new = []
    for i in range(R - 1):
        zm = top * (i + 0.5) / (R - 1)
        for j in range(N):
            key = (i // 2, ((j + (i // 2) * 2) % N) // 2)   # parches que se desplazan en espiral
            if key not in patch:
                patch[key] = mi_a if rng.random() < 0.62 else mi_b
            mi = mi_bark if zm < 0.8 else patch[key]
            j1 = (j + 1) % N
            if i < R - 2:
                f = bm.faces.new((rings[i][j], rings[i][j1], rings[i + 1][j1], rings[i + 1][j]))
            else:
                f = bm.faces.new((rings[i][j], rings[i][j1], apex))
            f.material_index = mi
            f.smooth = False
            new.append(f)
    bmesh.ops.recalc_face_normals(bm, faces=new)


def dab_flower(b, c, h, m):
    """Florecita suelta (cerco, macizos): ahora con petalos, centro de color y hojas en el tallo."""
    G.meadow_flower(b, c, h, G.SPECIES_BY_MAT.get(m, "daisy"))


def grass_tuft(b, c, h, n=7):
    """Mata de hierba: hojas planas inclinadas en abanico."""
    x, y, z = c
    for k in range(n):
        a = random.uniform(0, math.tau)
        lean = random.uniform(0.15, 0.55)
        d = Vector((math.cos(a) * lean, math.sin(a) * lean, 1.0))
        base = Vector((x + math.cos(a) * 0.03, y + math.sin(a) * 0.03, z - 0.01))
        b.blade(base, d, h * random.uniform(0.6, 1.1), random.uniform(0.03, 0.045),
                random.choice(["M_Plant_Leaf", "M_Plant_LeafLight", "M_Plant_Leaf", "M_Ivy_Light"]))


FENCE = (-20.5, 20.5, -21.5, 15.0)   # cerco de piedra: x0, x1, y0, y1


BUSH_SPOTS = [(-9.4, -7.6, 0.8), (9.4, -7.6, 0.8), (-9.6, 6.9, 0.9), (9.6, 6.9, 0.9),
              (-9.5, 0.0, 0.7), (9.5, -1.5, 0.7), (-6.8, 7.3, 0.6), (5.4, 7.2, 0.62), (-3.3, 7.25, 0.5), (3.3, 7.25, 0.5),
              (-8.85, -4.8, 0.42), (-8.85, 3.0, 0.42), (8.85, -4.6, 0.42), (8.85, 1.9, 0.42), (-8.85, -1.6, 0.38),
              (-14.5, -18.0, 0.8), (14.0, -18.5, 0.8), (-18.0, -2.0, 1.0), (18.0, -4.0, 0.9)]
CYPRESSES = [(13.5, 8.0, 9.5), (-10.5, 11.0, 7.5), (15.2, 5.6, 6.0), (-15.0, 9.0, 8.5), (-18.0, 4.0, 8.0),
             (12.5, -12.0, 7.0), (-7.0, 13.5, 6.5),
             # jardin delantero: flanquean el sendero sin taparlo (asimetricos a proposito)
             (-9.5, -13.5, 7.0), (8.5, -15.0, 8.0), (-15.5, -12.0, 6.5), (16.5, -14.5, 7.5), (-12.0, -17.5, 6.0)]
PROPS_XY = [(-3.3, -11.2), (3.3, -11.2), (-5.0, 6.9), (-2.6, -9.05), (2.6, -9.05), (0.9, -17.5), (-3.6, -7.7), (3.6, -7.7),
            (-1.2, -9.8), (7.15, 6.8), (1.8, 7.0), (-2.0, 7.05)]


def free_spot(x, y):
    """Fuera del edificio, sendero, escalinata, parterres, rosales, cipreses, mobiliario y muro."""
    if -9.2 < x < 9.2 and -8.6 < y < 7.8:
        return False
    for (bx, by, r) in BUSH_SPOTS:
        if math.hypot(x - bx, y - by) < r * 1.45 + 0.25:
            return False
    for (tx, ty, _) in CYPRESSES:
        if math.hypot(x - tx, y - ty) < 1.4:
            return False
    for (px_, py_) in PROPS_XY:
        if math.hypot(x - px_, y - py_) < 1.2:
            return False
    px = path_x(y)
    if y < -7.5 and abs(x - px) < 2.0:
        return False
    if abs(abs(x) - 4.4) < 2.2 and abs(y + 9.4) < 1.6:
        return False
    fx0, fx1, fy0, fy1 = FENCE
    if abs(x - fx0) < 1.3 or abs(x - fx1) < 1.3 or abs(y - fy0) < 1.3 or abs(y - fy1) < 1.3:
        return False
    return fx0 < x < fx1 and fy0 < y < fy1


def vegetation(cV):
    random.seed(21)
    b = B("Veg_Bushes", 0.5)
    # cada rosal ocupa ~1.25*r: separados del zocalo (|x|<8.1, |y|<6.1), escalinata, bajantes, banco, barril y urnas
    spots = BUSH_SPOTS
    for (x, y, r) in spots:
        bush(b, (x, y, 0.0), r)
    b.finish(cV)

    random.seed(22)   # los rosales usan su propio generador; esto fija el reparto de parterres y pradera
    b = B("Veg_FlowerBeds", 0.5)
    for sx in (-1, 1):   # parterres redondos con bordillo de piedra: girasoles al centro, corona de lavanda
        cx, cy = sx * 4.4, -9.4
        for k in range(24):
            a = k * math.tau / 24
            b.blob((cx + math.cos(a) * 1.45, cy + math.sin(a) * 0.95, 0.05), 0.13, random.choice(["M_Path_Stone", "M_Path_StoneWarm"]),
                   squash=(1.5, 0.8, 0.55), sub=1, amp=0.012, rot=(0, 0, math.degrees(a) + 90))
        b.blob((cx, cy, 0.0), 1.38, "M_Soil", squash=(1.0, 0.64, 0.09), sub=2, amp=0.015)
        for k, (dx, dy, hh, ln_) in enumerate(((0.0, 0.15, 1.55, 0.0), (-0.35, -0.1, 1.05, -0.25), (0.37, -0.12, 1.25, 0.25))):
            G.sunflower(b, (cx + dx, cy + dy, 0.08), hh, Vector((0, -1, 0)), lean=ln_)
        for k in range(7):
            a = k * math.tau / 7 + 0.3
            G.lavender(b, (cx + math.cos(a) * 0.95, cy + math.sin(a) * 0.6, 0.06), sc=0.9)
    # franja de lavanda al pie de la fachada principal
    for sx in (-1, 1):
        b.box((sx * 5.55, -6.55, 0.06), (2.6, 0.55, 0.14), "M_Soil", bev=0.03, amp=0.015, cuts=4)
        for i in range(5):
            G.lavender(b, (sx * (4.5 + i * 0.52), -6.55, 0.12), sc=0.95)
    b.finish(cV)

    b = B("Veg_Meadow", 0.5)
    # parches de flores silvestres repartidos por todo el jardin, como en la naturaleza
    placed = 0
    tries = 0
    kinds = ["daisy", "daisy", "buttercup", "cornflower", "pink", "buttercup"]
    while placed < 85 and tries < 1500:
        tries += 1
        cx, cy = random.uniform(-19.5, 19.5), random.uniform(-20.5, 14.0)
        if not free_spot(cx, cy):
            continue
        placed += 1
        G.flower_patch(b, cx, cy, random.randint(22, 42), random.choice(kinds), free_spot, spread=(0.5, 1.1))
        for k in range(2):
            gx_, gy_ = cx + random.uniform(-0.9, 0.9), cy + random.uniform(-0.7, 0.7)
            if free_spot(gx_, gy_):
                grass_tuft(b, (gx_, gy_, 0.0), random.uniform(0.3, 0.5))
    placed = 0
    while placed < 70:
        x, y = random.uniform(-20, 20), random.uniform(-23, 12)
        if free_spot(x, y):
            grass_tuft(b, (x, y, 0.0), random.uniform(0.25, 0.45))
            placed += 1
    b.finish(cV)

    b = B("Veg_Cypresses", 0.5)
    for (tx, ty, hgt) in CYPRESSES:
        cypress(b, tx, ty, hgt)
    b.finish(cV)


def stone_fence(cG, cV):
    """Cerramiento: muro macizo de mamposteria (laterales y fondo), cerca de estacas blanca sobre zocalo
    de piedra al frente, pilares en las esquinas y portada gotica de hierro en la entrada del patio."""
    random.seed(41)
    b = B("Env_StoneWall", 0.5)
    pf = B("Env_PicketFence", 0.5)
    gt = B("Env_GothicGate", 0.5)
    g = B("Veg_FenceGrass", 0.5)
    fx0, fx1, fy0, fy1 = FENCE
    gate = math.sin((fy0 + 9) * 0.22) * 1.2
    half = 1.25
    walls = [((fx0, fy0 + 0.25, 0), (fx0, fy1 - 0.25, 0)), ((fx0 + 0.25, fy1, 0), (fx1 - 0.25, fy1, 0)),
             ((fx1, fy1 - 0.25, 0), (fx1, fy0 + 0.25, 0))]
    for (A, C) in walls:
        G.stone_wall(b, A, C, h=1.15, th=0.5)
    pickets = [((fx0 + 0.32, fy0, 0), (gate - half - 0.8, fy0, 0)), ((gate + half + 0.8, fy0, 0), (fx1 - 0.32, fy0, 0))]
    for (A, C) in pickets:
        G.picket_run(pf, A, C)
    for (x, y) in ((fx0, fy0), (fx1, fy0), (fx0, fy1), (fx1, fy1)):
        G.pier(b, x, y, h=1.45, w=0.66)

    def leaves(cx, y, half, spring):
        W = half - 0.07   # cerrada: las dos hojas se tocan justo en el eje del porton

        def top(x):
            return 1.75 + 0.42 * (x / W) ** 1.6

        def leaf(lb):
            I = "M_Iron"
            lb.seg((0.03, 0, 0.1), (0.03, 0, top(0.03) + 0.05), 0.03, I, seg=6)
            lb.seg((W, 0, 0.1), (W, 0, top(W) + 0.05), 0.03, I, seg=6)
            lb.seg((0.03, 0, 0.15), (W, 0, 0.15), 0.025, I, seg=6)
            lb.seg((0.03, 0, 0.95), (W, 0, 0.95), 0.022, I, seg=6)
            lb.seg((0.03, 0, 1.3), (W, 0, 1.3), 0.018, I, seg=6)
            xs = [W * k / 14 for k in range(15)]
            for x0, x1 in zip(xs, xs[1:]):
                lb.seg((x0, 0, top(x0)), (x1, 0, top(x1)), 0.026, I, seg=6)
            x = 0.13
            while x < W - 0.04:
                lb.seg((x, 0, 0.15), (x, 0, top(x) + 0.1), 0.012, I, seg=5)
                lb.cyl((x, 0, top(x) + 0.16), 0.028, 0.1, "M_Museum_Brass", seg=4, r2=0.002, bev=0, amp=0.0)
                x += 0.11
            for k in range(int((W - 0.05) / 0.34)):   # anillos que tocan ambos largueros (0.95 y 1.3)
                xc = 0.2 + k * 0.34
                ring = [(xc + 0.165 * math.cos(j * math.tau / 20), 1.125 + 0.165 * math.sin(j * math.tau / 20)) for j in range(21)]
                for (u0, z0), (u1, z1) in zip(ring, ring[1:]):
                    lb.seg((u0, 0, z0), (u1, 0, z1), 0.009, I, seg=4)
            for zz in (0.4, 1.5):
                lb.cyl((0.0, 0, zz), 0.035, 0.14, "M_Museum_Brass", seg=8, bev=0, amp=0.0)
            lb.box((W - 0.09, 0.0, 1.05), (0.1, 0.06, 0.16), "M_Museum_Brass", bev=0.01, amp=0.001, cuts=0)
        # Bisagra pegada a la cara interior de cada pilar (pilar: |x-cx| >= half). Origen = bisagra, 0 deg = CERRADA.
        # La derecha es el espejo exacto de la izquierda (malla espejada), asi abrir/cerrar es +ang / -ang para animar.
        hl = L.prop("Gate_Leaf_L", (cx - half + 0.04, y, 0.0), 0, leaf)
        hr = L.prop("Gate_Leaf_R", (cx + half - 0.04, y, 0.0), 0, leaf)
        import bmesh
        from mathutils import Matrix
        bm = bmesh.new()
        bm.from_mesh(hr.data)
        bmesh.ops.transform(bm, matrix=Matrix.Scale(-1, 4, (1, 0, 0)), verts=bm.verts)
        bmesh.ops.reverse_faces(bm, faces=bm.faces)
        bm.to_mesh(hr.data)
        bm.free()
        hl.rotation_euler.z = math.radians(90)    # abierta hacia el jardin, simetrica
        hr.rotation_euler.z = math.radians(-90)
        to_col(hl, cG)
        to_col(hr, cG)
    G.gothic_gate(gt, leaves, gate, fy0, half=half)
    # hierba al pie del muro y de la cerca, y algun mechon sobre la albardilla
    for (A, C) in walls + pickets:
        A, C = Vector(A), Vector(C)
        ln, dv = (C - A).length, (C - A).normalized()
        nv = Vector((-dv.y, dv.x, 0))
        t = 0.9   # lejos de los extremos: en las esquinas esta el otro muro
        while t < ln - 1.3:
            for side in (-1, 1):
                q = A + dv * (t + random.uniform(0, 0.4)) + nv * side * random.uniform(0.72, 0.9)
                G.grass(g, (q.x, q.y, 0.0), random.uniform(0.3, 0.5), n=random.randint(6, 9))
            if random.random() < 0.1:
                q = A + dv * (t + random.uniform(0, 0.5)) + nv * random.choice((-1, 1)) * 0.45
                dab_flower(g, (q.x, q.y, 0.0), random.uniform(0.3, 0.45), random.choice(["M_Flower_Yellow", "M_Flower_White", "M_Flower_Lavender"]))
            t += 0.6
    for b_, c_ in ((b, cG), (pf, cG), (gt, cG), (g, cV)):
        b_.finish(c_)


def benches_and_lamps(cP):
    def bench(b):
        for z, y in ((0.46, 0), ):
            for k in range(3):
                b.box((0, -0.14 + k * 0.14, 0.46), (1.6, 0.12, 0.05), "M_Museum_Wood", bev=0.012, amp=0.008, cuts=1)
        for k in range(3):
            b.box((0, 0.24, 0.62 + k * 0.14), (1.6, 0.04, 0.1), "M_Museum_Wood", bev=0.01, amp=0.008, cuts=1)
        for sx in (-0.7, 0.7):
            b.box((sx, 0, 0.22), (0.07, 0.5, 0.44), "M_Museum_Metal", bev=0.01, amp=0.006, cuts=1)
            b.box((sx, 0.24, 0.55), (0.07, 0.06, 0.62), "M_Museum_Metal", bev=0.01, amp=0.006, cuts=1)

    def lamp(b):
        b.cyl((0, 0, 0.08), 0.2, 0.16, "M_Museum_Stone", seg=10, r2=0.16, bev=0, amp=0.008)
        b.cyl((0, 0, 1.6), 0.05, 3.0, "M_Museum_Metal", seg=8, r2=0.035, bev=0, amp=0.004)
        b.box((0, 0, 3.2), (0.3, 0.3, 0.36), "M_Lamp_Glow", bev=0.02, amp=0.004, cuts=0)
        b.cyl((0, 0, 3.5), 0.26, 0.14, "M_Museum_Metal", seg=4, r2=0.04, bev=0, amp=0.004, rot=(0, 0, 45))
        b.box((0, 0, 3.0), (0.36, 0.36, 0.04), "M_Museum_Metal", bev=0.01, amp=0.003, cuts=0)

    def pot(b):
        zs_ = G.urn(b, (0, 0, 0), 1.0)
        for k, (dx, dy, hh, ln_) in enumerate(((0.0, 0.06, 1.35, 0.0), (-0.12, -0.06, 0.85, -0.3), (0.13, -0.05, 1.05, 0.32))):
            G.sunflower(b, (dx, dy, zs_ - 0.02), hh, Vector((0, -1, 0)), lean=ln_)
        for k in range(3):   # un par de hojas bajas sobre la tierra, sin abarrotar
            a = k * 2.1 + 0.4
            rad = Vector((math.cos(a), math.sin(a), 0))
            tip = (rad - Vector((0, 0, 0.15))).normalized()
            b.leaf(Vector((0, 0, zs_ + 0.03)) + rad * 0.17, (Vector((0, 0, 1)) - tip * tip.z).normalized(), tip, 0.13,
                   "M_Plant_Leaf", thick=0.005, res=20, shape='heart')

    def easel(b):
        for sx in (-0.4, 0.4):
            b.box((sx, 0, 0.55), (0.05, 0.05, 1.1), "M_Museum_Wood", rot=(0, 0, 0), bev=0.01, amp=0.006, cuts=1)
        b.box((0, 0.2, 0.55), (0.05, 0.05, 1.1), "M_Museum_Wood", rot=(18, 0, 0), bev=0.01, amp=0.006, cuts=1)
        b.box((0, -0.04, 0.78), (0.95, 0.04, 0.6), "M_Sign_Board", bev=0.015, amp=0.006, cuts=1)
        b.text("OPEN", (0, -0.08, 0.8), 0.22, "M_Sign_Letters", ext=0.02)
        b.box((0, -0.05, 0.3), (0.9, 0.06, 0.05), "M_Museum_Wood", bev=0.01, amp=0.006, cuts=1)

    items = [("Prop_Bench_W", (-3.3, -11.2, 0.0), 0, bench), ("Prop_Bench_E", (3.3, -11.2, 0.0), 0, bench),
             ("Prop_Bench_Back", (-5.0, 6.9, 0.0), 180, bench),
             ("Prop_Lamppost_W", (-2.6, -9.05, 0.0), 0, lamp), ("Prop_Lamppost_E", (2.6, -9.05, 0.0), 0, lamp),
             ("Prop_Lamppost_Far", (0.9, -17.5, 0.0), 0, lamp),
             ("Prop_Pot_W", (-3.6, -7.7, 0.0), 0, pot), ("Prop_Pot_E", (3.6, -7.7, 0.0), 0, pot),
             ("Prop_Sign_Open", (-1.2, -9.8, 0.0), 12, easel)]
    for (n, pos, rot, fn) in items:
        ob = L.prop(n, pos, rot, fn)
        ob.rotation_euler.z = math.radians(rot + (180 if n.startswith("Prop_Bench_") and n != "Prop_Bench_Back" else 0))
        to_col(ob, cP)


# ----------------------------------------------------------------- presentacion
def presentation(cS):
    sc = bpy.context.scene
    try:
        sc.render.engine = 'BLENDER_EEVEE'
    except Exception:
        pass
    w = bpy.data.worlds.get("World") or bpy.data.worlds.new("World")
    sc.world = w
    w.use_nodes = True
    bg = next(n for n in w.node_tree.nodes if n.type == 'BACKGROUND')
    bg.inputs["Color"].default_value = (0.30, 0.42, 0.62, 1)
    bg.inputs["Strength"].default_value = 0.9
    sun = bpy.data.lights.new("Sun_Warm", 'SUN')
    sun.energy = 3.2
    sun.color = (1.0, 0.9, 0.74)
    sun.angle = math.radians(6)
    so = bpy.data.objects.new("Light_Sun", sun)
    so.rotation_euler = (math.radians(52), math.radians(8), math.radians(-38))
    cS.objects.link(so)
    fill = bpy.data.lights.new("Fill_Cool", 'SUN')
    fill.energy = 0.7
    fill.color = (0.65, 0.75, 1.0)
    fo = bpy.data.objects.new("Light_Fill", fill)
    fo.rotation_euler = (math.radians(70), 0, math.radians(140))
    cS.objects.link(fo)
    cams = {
        "Cam_Front": ((0, -30, 4.5), (0, 0, 5.5)),
        "Cam_ThreeQuarter": ((-22, -22, 9), (0, 0, 5.5)),
        "Cam_Side": ((-30, 0, 6), (0, 0, 5.5)),
        "Cam_Back": ((10, 28, 6), (0, 0, 5.5)),
        "Cam_Aerial": ((-17, -20, 24), (0, 0, 4)),
    }
    for n, (pos, tgt) in cams.items():
        cd = bpy.data.cameras.new(n)
        cd.lens = 35
        cd.clip_end = 200
        co = bpy.data.objects.new(n, cd)
        co.location = pos
        d = Vector(tgt) - Vector(pos)
        co.rotation_euler = d.to_track_quat('-Z', 'Y').to_euler()
        cS.objects.link(co)
    sc.camera = bpy.data.objects["Cam_ThreeQuarter"]


def _zroof(y):
    """Cara inferior aproximada del faldon principal (con margen para la deformacion)."""
    return EAVE_Z - 0.06 + (6.8 - abs(y)) * TAN - 0.25


def cull_hidden(colls):
    """Borra caras que el jugador nunca ve desde fuera:
    - todo lo que queda dentro del volumen interior del edificio (cara interior de muros, forros tras el cristal
      opaco, desvan): el interior real es otro modelo;
    - cara inferior del tejado sobre el desvan cerrado y techos de muro bajo el tejado;
    - lo enterrado: base del terreno, mitades bajo tierra de piedras y bases apoyadas en el suelo.
    Devuelve (caras antes, caras despues)."""
    import bmesh
    before = after = 0
    for c in colls:
        for ob in c.all_objects:
            if ob.type != 'MESH':
                continue
            me = ob.data
            bm = bmesh.new()
            bm.from_mesh(me)
            M = ob.matrix_world
            N = M.to_3x3().inverted().transposed()
            before += len(bm.faces)
            kill = []
            for f in bm.faces:
                ws = [M @ v.co for v in f.verts]
                n = (N @ f.normal).normalized()
                xs = [abs(w.x) for w in ws]
                ys = [abs(w.y) for w in ws]
                zs = [w.z for w in ws]
                inside = all(abs(w.x) < 7.72 and abs(w.y) < 5.72 and -0.05 < w.z < _zroof(w.y) for w in ws)
                zu = EAVE_Z + 0.12 + (6.8 * TAN) / 2 + (3.4 - max(ys)) * TAN - 0.18   # cara inferior del faldon
                under_roof = (ob.name == "Ext_Roof_Main" and n.z < -0.5 and max(xs) < 7.5 and max(ys) < 5.5
                              and max(zs) < zu + 0.12)
                wall_top = (ob.name == "Ext_Walls" and n.z > 0.5 and min(zs) > D.WT - 0.2
                            and max(zs) < D.WT + 0.25 and max(xs) < 8.05 and max(ys) < 6.05)
                buried = max(zs) < -0.06
                resting = (n.z < -0.9 and max(abs(z) for z in zs) < 0.03 and ob.name != "Env_Terrain")
                if inside or under_roof or wall_top or buried or resting:
                    kill.append(f)
            if kill:
                bmesh.ops.delete(bm, geom=kill, context='FACES')
                loose = [v for v in bm.verts if not v.link_faces]
                if loose:
                    bmesh.ops.delete(bm, geom=loose, context='VERTS')
            after += len(bm.faces)
            bm.to_mesh(me)
            bm.free()
            me.update()
    return before, after


def weld_clean(colls):
    """Limpieza final: quita caras degeneradas y suelda vertices duplicados (1e-5 m). Solo posicion: UVs y materiales no cambian."""
    import bmesh
    for c in colls:
        for ob in c.all_objects:
            if ob.type != 'MESH' or not len(ob.data.vertices):
                continue
            bm = bmesh.new()
            bm.from_mesh(ob.data)
            bmesh.ops.dissolve_degenerate(bm, dist=1e-6, edges=bm.edges)
            bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=1e-5)
            loose = [v for v in bm.verts if not v.link_faces and not v.link_edges]
            if loose:
                bmesh.ops.delete(bm, geom=loose, context='VERTS')
            bm.to_mesh(ob.data)
            bm.free()
            ob.data.update()


CULL_HIDDEN = True   # borra caras que nunca se ven desde fuera (ver cull_hidden)


def build():
    L.clear_scene()
    random.seed(3)
    cA, cP, cV, cG, cS = col("Exterior_Architecture"), col("Exterior_Props"), col("Exterior_Vegetation"), col("Exterior_Ground"), col("Presentation")
    body(cA)
    windows(cA)
    entrance(cA)
    roof(cA)
    dormers(cA)
    facade_details(cA, cP)
    ground(cG)
    stone_fence(cG, col("Exterior_Vegetation"))
    vegetation(cV)
    benches_and_lamps(cP)
    if CULL_HIDDEN:
        # sin esto matrix_world de los ultimos props sigue en identidad y cull_hidden los toma por "interior" (Prop_Sign_Open salia vacio)
        bpy.context.view_layer.update()
        bf, af = cull_hidden([cA, cP, cV, cG])
        print("caras ocultas borradas:", bf - af, "de", bf)
    weld_clean([cA, cP, cV, cG])
    presentation(cS)
    # sin objetos sueltos en la raiz
    for ob in bpy.context.scene.collection.objects:
        print("SUELTO:", ob.name)
    print("objetos:", len(bpy.data.objects), "materiales:", len(bpy.data.materials),
          "tris aprox:", sum(len(o.data.polygons) for o in bpy.data.objects if o.type == 'MESH'))
