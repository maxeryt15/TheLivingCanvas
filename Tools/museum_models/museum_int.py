"""Museo INTERIOR (Blender 5.x). Mismo edificio que museum_ext: huecos, muros y deformacion compartidos.

Planta baja (FL0=0.5, techo 4.1):
  Hall (recepcion) | Gallery I (oeste) | Gallery II (este) | Gallery III (oeste, fondo) | Stair Hall (escalera en U)
  Servicio: vestibulo de aseos (lavabos) + Restroom 1/2 + Maintenance (escotilla al sotano), separados por tabiques.
Planta alta (FL1=4.5, techo 8.1):
  Gallery IV (sala de luz, sobre el hall) | Gallery V (gris, cuadro destacado) | Gallery VI (esculturas) | Landing (mirador).
Los cuadros son HUECOS (ArtSlot_*: marco + lienzo vacio) para colocar las obras definitivas en Unity.
Puertas de servicio = objetos sueltos con el pivote en la bisagra (Door_*), abiertas.
"""
import bpy, bmesh, math, random, sys
from mathutils import Vector, Matrix, Quaternion

P = r"D:\TheLivingCanvas\Tools\museum_models"
if P not in sys.path:
    sys.path.insert(0, P)
import importlib, museum_lib as L, museum_dims as D, museum_ext as X
importlib.reload(L); importlib.reload(D); importlib.reload(X)
from museum_lib import B, Face, wall, col


class LB(B):
    """B con el biselado a 1 segmento (el de museum_lib usa 2): mismos cantos suavizados con la mitad de triangulos."""

    def _finish(s, bm, c, rot, mat, bev, amp, minsize, freq=0.45):
        if bev > 0:
            b = min(bev, minsize * 0.3)
            edges = [e for e in bm.edges if len(e.link_faces) == 2 and e.calc_face_angle(0) > 0.6]
            if edges:
                bmesh.ops.bevel(bm, geom=edges, offset=b, segments=1, affect='EDGES')
            bev = 0
        B._finish(s, bm, c, rot, mat, bev, amp, minsize, freq)

    def box(s, c, size, mat, rot=(0, 0, 0), bev=0.025, amp=0.018, cuts=None):
        if amp == 0:   # sin ondulacion las subdivisiones no aportan nada
            cuts = 0
        B.box(s, c, size, mat, rot=rot, bev=bev, amp=amp, cuts=cuts)


class WB(LB):
    """Capas finas de acabado de pared: solo se subdivide la arista mas larga (donde vive la ondulacion de la pintura); los cantos y
    las caras estrechas no necesitan la rejilla completa que genera museum_lib."""

    def box(s, c, size, mat, rot=(0, 0, 0), bev=0.025, amp=0.018, cuts=None):
        bm = bmesh.new()
        bmesh.ops.create_cube(bm, size=1.0)
        for v in bm.verts:
            v.co.x *= size[0]; v.co.y *= size[1]; v.co.z *= size[2]
        n = cuts if cuts is not None else int(max(size) / 1.5)
        if n > 0 and amp > 0:
            lg = max(size)
            bmesh.ops.subdivide_edges(bm, edges=[e for e in bm.edges if e.calc_length() > lg * 0.9], cuts=n, use_grid_fill=True)
        s._finish(bm, c, rot, mat, bev, amp, min(size))


class HB(LB):
    """B para los props de mobiliario: algo mas de segmentos en los cilindros y varillas visibles (nada facetado de cerca, pero sin disparar
    la malla) y un biselado fino en las cajas de tamano de mueble cuyos cantos serian cuchillas (bev=0). Las piezas deliberadamente
    facetadas (seg <= 7) se respetan."""

    def cyl(s, c, r, h, mat, rot=(0, 0, 0), seg=16, r2=None, bev=0.0, amp=0.01):
        rm = max(r, r2 or 0.0)
        if seg > 7:
            seg = min(seg, 24 if rm >= 0.04 else (14 if rm >= 0.02 else (10 if rm >= 0.008 else 6)))
        B.cyl(s, c, r, h, mat, rot=rot, seg=seg, r2=r2, bev=bev, amp=amp)

    def seg(s, p0, p1, r, mat, seg=5):
        B.seg(s, p0, p1, r, mat, seg=max(seg, 12 if r >= 0.012 else (8 if r >= 0.006 else seg)))

    def box(s, c, size, mat, rot=(0, 0, 0), bev=0.025, amp=0.018, cuts=None):
        if bev == 0 and min(size) >= 0.05 and 0.3 <= max(size) < 2.0:
            bev = min(0.004, min(size) * 0.12)
        LB.box(s, c, size, mat, rot=rot, bev=bev, amp=amp, cuts=cuts)


def prop(name, pos, rot, fn, uvscale=1.0):
    """Como museum_lib.prop pero con HB (cilindros suaves y cantos biselados)."""
    b = HB(name, uvscale, warp=False)
    fn(b)
    ob = b.finish()
    ob.location = pos
    ob.rotation_euler.z = math.radians(rot)
    return ob

FL0, FL1, C0, C1 = D.FL0, D.FL1, D.C0, D.C1
IX0, IX1, IY0, IY1 = D.IX0, D.IX1, D.IY0, D.IY1
FIN = 0.08  # grosor del acabado de suelo
HATCH_SEAT = (D.HATCH[0] - 0.085, D.HATCH[1] + 0.085, D.HATCH[2] - 0.085, D.HATCH[3] + 0.085)  # el marco de la escotilla encaja en el suelo
WING_STEP = 4   # fases del ala trasera: 2 = caja vacia; 3 = + volumenes y focos; 4 = + obras, pedestales y rotulo
STAIR_HOLE = (-3.0, -0.61, 1.3, IY1)   # hueco de escalera en el forjado (x0, x1, y0, y1); propio del interior (no usa museum_dims)

# Anexo del cuarto de mantenimiento: SOLO interior (el interior es una zona aparte, puede ser mayor que el exterior).
# Se abre el muro trasero en planta baja (ventana x 5.55 -> paso ancho con dintel) y se prolonga la sala hacia y 6.0..8.55.
ANNEX = (3.2, IX1, 6.0, 8.55)          # cara interior del anexo (x0, x1, y0, y1)
PASS_X0, PASS_X1 = 3.35, 7.45          # paso entre mantenimiento y anexo
PASS_Z0, PASS_Z1 = FL0 - FIN, 3.7      # el suelo del paso arranca bajo el acabado; dintel visto de 3.7 a 4.1
BACK_I = [((PASS_X0 + PASS_X1) / 2, PASS_X1 - PASS_X0, PASS_Z0, PASS_Z1) if (abs(o[0] - 5.55) < 0.01 and o[2] < C0) else o for o in D.BACK]
# las puertas de entrada y trasera bajan el dintel inferior 3 cm: sobre ese hueco va un umbral propio (saddle) y el muro no asoma al suelo
FRONT_I = [(o[0], o[1], FL0 - 0.03, o[3]) if (abs(o[0]) < 0.01 and o[2] < C0) else o for o in D.FRONT]
BACK_I = [(o[0], o[1], FL0 - 0.03, o[3]) if (abs(o[0]) < 0.01 and o[2] < C0) else o for o in BACK_I]
PASSAGES = [('x', D.Y1 - D.TH / 2, (PASS_X0 + PASS_X1) / 2, PASS_X1 - PASS_X0, PASS_Z0, PASS_Z1, "Maintenance_Passage", 'open')]

# tabiques: (nombre, eje, fijo, grosor, a0, a1, planta)
PARTS = [
    ("GF_P1_West", 'y', -3.1, 0.2, IY0, IY1, 0), ("GF_P2_East", 'y', 3.1, 0.2, IY0, IY1, 0),
    ("GF_P3", 'x', 0.3, 0.2, IX0, -3.2, 0), ("GF_P4", 'x', 0.3, 0.2, -3.0, 3.0, 0), ("GF_P5", 'x', 0.3, 0.2, 3.2, IX1, 0),
    ("GF_P6", 'y', 4.675, 0.15, 0.4, 3.425, 0), ("GF_P7", 'x', 1.85, 0.15, 4.75, IX1, 0), ("GF_P8", 'x', 3.5, 0.15, 3.2, IX1, 0),
    ("UF_Q1", 'y', -3.1, 0.2, IY0, IY1, 1), ("UF_Q2", 'y', 3.1, 0.2, IY0, IY1, 1), ("UF_Q3", 'x', 0.3, 0.2, -3.0, 3.0, 1),
]
# puertas en tabiques: (eje, fijo, centro, ancho, z_inf, z_sup, nombre, tipo)
DOORS = [
    ('y', -3.1, -2.9, 1.6, FL0, FL0 + 2.7, "Hall_GalleryI", 'open'),
    ('y', 3.1, -2.9, 1.6, FL0, FL0 + 2.7, "Hall_GalleryII", 'open'),
    ('x', 0.3, -5.4, 1.4, FL0, FL0 + 2.7, "GalleryI_GalleryIII", 'open'),
    ('x', 0.3, 0.0, 3.0, FL0, FL0 + 3.2, "Hall_StairHall", 'arch'),
    ('y', 3.1, 1.85, 1.0, FL0, FL0 + 2.2, "StairHall_Restrooms", 'leaf'),
    ('y', 4.675, 1.1, 0.8, FL0, FL0 + 2.1, "Restroom_1", 'leaf'),
    ('y', 4.675, 2.65, 0.8, FL0, FL0 + 2.1, "Restroom_2", 'leaf'),
    ('y', 3.1, 4.2, 1.0, FL0, FL0 + 2.2, "StairHall_Maintenance", 'leaf'),
    ('y', -3.1, -2.5, 1.4, FL1, FL1 + 2.7, "GalleryIV_GalleryV", 'open'),
    ('y', 3.1, -2.5, 1.4, FL1, FL1 + 2.7, "GalleryIV_GalleryVI", 'open'),
    ('y', 3.1, 3.0, 1.2, FL1, FL1 + 2.6, "Landing_GalleryVI", 'open'),
    ('x', 0.3, -2.0, 1.4, FL1, FL1 + 2.7, "Stair_GalleryIV", 'arch'),
    ('x', 0.3, 1.5, 1.4, FL1, FL1 + 2.7, "GalleryIV_Landing", 'open'),
]
# Ventanas que el INTERIOR oculta (el exterior las sigue mostrando; zonas aparte): (clave, centro, planta). Pasan a ser muro liso.
HIDDEN_WIN = {('W', 1.9, 0),                                              # Gallery III: queda la trasera y la oeste y=3.8
              ('F', -5.55, 1), ('B', -5.55, 1), ('W', -3.3, 1), ('W', 3.8, 1),   # Gallery V: solo queda la oeste y=0.6
              ('F', 5.55, 1), ('B', 5.55, 1), ('E', -3.0, 1), ('E', 3.8, 1)}     # Gallery VI: solo queda la este y=1.2


def _vis(key, lst):
    return [o for o in lst if (key, round(o[0], 2), 0 if o[2] < C0 else 1) not in HIDDEN_WIN]


FRONT_I, BACK_I = _vis('F', FRONT_I), _vis('B', BACK_I)
WEST_I, EAST_I = _vis('W', D.WEST), _vis('E', D.EAST)
PERIM = [('x', D.Y0 + D.TH / 2, FRONT_I, 'F'), ('x', D.Y1 - D.TH / 2, BACK_I, 'B'),
         ('y', D.X0 + D.TH / 2, WEST_I, 'W'), ('y', D.X1 - D.TH / 2, EAST_I, 'E')]
# un radiador por sala, bajo esta ventana: sala -> (clave, centro)
RAD_AT = {"Gallery_I": ('F', -5.55), "Gallery_II": ('F', 5.55), "Gallery_III": ('B', -5.55), "Gallery_IV": ('F', -2.35),
          "Gallery_V": ('W', 0.6), "Gallery_VI": ('E', 1.2), "Hall": ('F', -2.35), "Landing": ('B', 1.8)}
# salas: (x0, x1, y0, y1, planta, suelo, pintura, friso, alto_friso, moldura_de_cuadros)
ROOMS = {
    "Hall":             (-3.0, 3.0, IY0, 0.2, 0, "M_Interior_FloorTile", "M_Interior_Wallpaper", "M_Interior_Wainscot", 1.0, False),
    "Gallery_I":        (IX0, -3.2, IY0, 0.2, 0, "M_Interior_FloorWood", "M_Wall_Ochre", None, 0, True),
    "Gallery_II":       (3.2, IX1, IY0, 0.2, 0, "M_Interior_FloorWood", "M_Wall_Cerulean", None, 0, True),
    "Gallery_III":      (IX0, -3.2, 0.4, IY1, 0, "M_Interior_FloorWood", "M_Wall_Terracotta", None, 0, True),
    "Stair_Hall":       (-3.0, 3.0, 0.4, IY1, 0, "M_Interior_FloorTile", "M_Interior_Wallpaper", "M_Interior_Wainscot", 1.0, False),
    "Restroom_Lobby":   (3.2, 4.6, 0.4, 3.425, 0, "M_Interior_FloorTile", "M_Interior_Wallpaper", "M_Ceramic", 1.1, False),
    "Restroom_1":       (4.75, IX1, 0.4, 1.775, 0, "M_Interior_FloorTile", "M_Interior_Wallpaper", "M_Ceramic", 1.1, False),
    "Restroom_2":       (4.75, IX1, 1.925, 3.425, 0, "M_Interior_FloorTile", "M_Interior_Wallpaper", "M_Ceramic", 1.1, False),
    "Maintenance":      (3.2, IX1, 3.575, IY1, 0, "M_Interior_Concrete", "M_Wall_Grey", None, 0, False),
    "Maintenance_Annex": (ANNEX[0], ANNEX[1], ANNEX[2], ANNEX[3], 0, "M_Interior_Concrete", "M_Wall_Grey", None, 0, False),
    "Gallery_IV":       (-3.0, 3.0, IY0, 0.2, 1, "M_Interior_FloorWood", "M_Wall_Olive", None, 0, True),
    "Gallery_V":        (IX0, -3.2, IY0, IY1, 1, "M_Interior_FloorWood", "M_Wall_Grey", None, 0, True),
    "Gallery_VI":       (3.2, IX1, IY0, IY1, 1, "M_Interior_FloorWood", "M_Interior_Wallpaper", None, 0, True),
    "Landing":          (-3.0, 3.0, 0.4, IY1, 1, "M_Interior_FloorWood", "M_Interior_Wallpaper", "M_Interior_Wainscot", 1.0, False),
}


def to_col(ob, c):
    return X.to_col(ob, c)


def fz(r):
    return (FL0, C0) if r[4] == 0 else (FL1, C1)


# huecos indexados para cortar zocalos, frisos y molduras
OPEN = []


def build_open():
    OPEN.clear()
    for (ax, fx, lst, _) in PERIM:
        for (c, w, zs, zt) in lst:
            OPEN.append((ax, fx, D.TH, c, w, zs, zt))
    th = {(p[1], p[2]): p[3] for p in PARTS}
    for (ax, fx, c, w, zs, zt, _, _) in DOORS:
        OPEN.append((ax, fx, th[(ax, fx)], c, w, zs, zt))


def sides(r):
    x0, x1, y0, y1 = r[:4]
    return [('x', y0, 1, x0, x1), ('x', y1, -1, x0, x1), ('y', x0, 1, y0, y1), ('y', x1, -1, y0, y1)]


def side_openings(axis, face, a0, a1):
    res = []
    for (ax, fx, th, c, w, zs, zt) in OPEN:
        if ax == axis and abs(abs(face - fx) - th / 2) < 0.03 and c + w / 2 > a0 and c - w / 2 < a1:
            res.append((c, w, zs, zt))
    return res


def curtain_span(key, c, zs):
    """Limites (a lo largo del muro) de la sala donde cae la ventana: las cortinas no pasan del tabique."""
    lvl = 0 if zs < C0 else 1
    for r in ROOMS.values():
        if r[4] != lvl:
            continue
        if key in 'FB':
            edge = abs(r[2] - IY0) < 0.01 if key == 'F' else abs(r[3] - IY1) < 0.01
            if edge and r[0] <= c <= r[1]:
                return r[0], r[1]
        else:
            edge = abs(r[0] - IX0) < 0.01 if key == 'W' else abs(r[1] - IX1) < 0.01
            if edge and r[2] <= c <= r[3]:
                return r[2], r[3]
    return -99.0, 99.0


def room_at(key, c, zs):
    """Nombre de la sala donde cae una ventana del perimetro (misma logica que curtain_span)."""
    lvl = 0 if zs < C0 else 1
    for rn, r in ROOMS.items():
        if r[4] != lvl:
            continue
        if key in 'FB':
            edge = abs(r[2] - IY0) < 0.01 if key == 'F' else abs(r[3] - IY1) < 0.01
            if edge and r[0] <= c <= r[1]:
                return rn
        else:
            edge = abs(r[0] - IX0) < 0.01 if key == 'W' else abs(r[1] - IX1) < 0.01
            if edge and r[2] <= c <= r[3]:
                return rn
    return None


RAD_ROOMS = ("Gallery_I", "Gallery_II", "Gallery_III", "Gallery_IV", "Gallery_V", "Gallery_VI", "Hall", "Landing")


def radiator(rd, F, c, w, floor):
    """Radiador de hierro fundido bajo la ventana (v=-0.49: delante de friso y zocalo): columnas eliptico-torneadas, colectores redondeados, patas
    de fundicion, purgador y tapon arriba, valvula termostatica (derecha) y detentor (izquierda) abajo con tubos de cobre hasta el suelo y rosetas."""
    wr, v = w - 0.3, -0.49
    ax = F.axis
    ro = (0, 90, 0) if ax == 'x' else (90, 0, 0)               # eje de un cilindro a lo largo de la pared

    def sz(al, de, h):                                          # (largo en la pared, fondo, alto) -> ejes del mundo
        return (al, de, h) if ax == 'x' else (de, al, h)
    n = max(3, int(wr / 0.06))
    for k in range(n):
        u = c - wr / 2 + 0.0225 + k * (wr - 0.045) / (n - 1)
        ra, rdp = 0.0215, 0.044
        rr = [(floor + 0.14, 0.86), (floor + 0.215, 1.0), (floor + 0.70, 1.0)]       # arranque ahusado sobre el colector bajo; arriba entra en el colector alto
        loft(rd, [(z, (ra if ax == 'x' else rdp) * s_, (rdp if ax == 'x' else ra) * s_, 0.0) for (z, s_) in rr], "M_Museum_Metal", seg=8,
             xf=Matrix.Translation(F.P(u, v, 0.0)), raw=True, cap_bottom=False, cap_top=False)    # sin tapas: las ocultan los colectores
    for zz in (0.14, 0.70):                                     # colectores con los cantos redondeados
        rbox(rd, F.P(c, v, floor + zz), sz(wr, 0.1, 0.045), 0.014, "M_Museum_Metal", segs=2)
    for sg in (-1, 1):                                          # patas de fundicion
        rbox(rd, F.P(c + sg * (wr / 2 - 0.06), v, floor + 0.06), sz(0.05, 0.08, 0.12), 0.01, "M_Museum_Metal", segs=1)
    br, cu = "M_Museum_Brass", "M_Copper"
    uR, uL = c + wr / 2, c - wr / 2
    # arriba: purgador (derecha: tuerca hexagonal + tornillo) y tapon ciego (izquierda)
    rd.cyl(F.P(uR + 0.012, v, floor + 0.70), 0.016, 0.024, br, rot=ro, seg=6, bev=0, amp=0.0)
    rd.cyl(F.P(uR + 0.0285, v, floor + 0.70), 0.0075, 0.013, br, rot=ro, seg=8, bev=0, amp=0.0)
    rd.cyl(F.P(uL - 0.008, v, floor + 0.70), 0.016, 0.016, br, rot=ro, seg=6, bev=0, amp=0.0)
    # abajo: dos grifos de angulo con tubo de cobre al suelo; derecha = cabezal termostatico, izquierda = detentor con capuchon
    for sg in (1, -1):
        u0 = c + sg * wr / 2
        rd.cyl(F.P(u0 + sg * 0.006, v, floor + 0.14), 0.0165, 0.012, br, rot=ro, seg=6, bev=0, amp=0.0)        # tuerca de union
        rd.cyl(F.P(u0 + sg * 0.027, v, floor + 0.14), 0.0125, 0.03, br, rot=ro, seg=10, bev=0, amp=0.0)        # cuerpo del grifo
        up = u0 + sg * 0.027
        tube(rd, [F.P(up, v, floor + 0.006), F.P(up, v, floor + 0.14)], 0.0085, cu, seg=8)                     # tubo vertical
        rd.cyl(F.P(up, v, floor + 0.004), 0.021, 0.008, "M_Steel", seg=14, bev=0, amp=0.0)                      # roseta del suelo
        if sg == 1:
            rd.cyl(F.P(u0 + 0.052, v, floor + 0.14), 0.0095, 0.02, br, rot=ro, seg=8, bev=0, amp=0.0)         # vastago del cabezal
            rd.cyl(F.P(u0 + 0.077, v, floor + 0.14), 0.02, 0.044, "M_Plastic_White", rot=ro, seg=12, bev=0, amp=0.0)   # cabezal termostatico
            rd.cyl(F.P(u0 + 0.101, v, floor + 0.14), 0.013, 0.008, "M_Plastic_White", rot=ro, seg=10, bev=0, amp=0.0)
        else:
            rd.cyl(F.P(u0 - 0.0475, v, floor + 0.14), 0.0145, 0.025, br, rot=ro, seg=6, bev=0, amp=0.0)        # capuchon del detentor
            rd.cyl(F.P(u0 - 0.063, v, floor + 0.14), 0.0105, 0.012, br, rot=ro, seg=8, bev=0, amp=0.0)


def layer(b, sd, z0, z1, depth, mat, off=0.0, amp=0.003):
    axis, face, s, a0, a1 = sd
    wall(b, axis, face + s * (off + depth / 2), a0, a1, z0, z1, depth, mat, side_openings(axis, face, a0, a1), amp=amp)


def slab(b, x0, x1, y0, y1, z0, z1, mat, hole=None, amp=0.004):
    def bx(a, b_, c, d):
        if b_ - a > 0.01 and d - c > 0.01:
            b.box(((a + b_) / 2, (c + d) / 2, (z0 + z1) / 2), (b_ - a, d - c, z1 - z0), mat, bev=0.0, amp=amp, cuts=max(1, int(max(b_ - a, d - c) / 1.5)))
    if not hole:
        bx(x0, x1, y0, y1)
        return
    hx0, hx1, hy0, hy1 = hole
    bx(x0, x1, y0, hy0)
    bx(x0, x1, hy1, y1)
    bx(x0, hx0, hy0, hy1)
    bx(hx1, x1, hy0, hy1)


def saddle(b, x, y, sx, sy, z, mat):
    """Umbral en saddle: bloque con la cara superior SADDLE (5 mm) por encima del suelo terminado z y biselado; baja 6 cm bajo el suelo
    para que ninguna superficie quede coplanar con los acabados de las salas ni asome el muro de debajo."""
    b.box((x, y, z - 0.03 + SADDLE / 2), (sx, sy, 0.06 + SADDLE), mat, bev=0.004, amp=0.0, cuts=0)


# ======================================================================= estructura
def structure(cS):
    b = B("Int_Shell_Walls", 0.5)
    for (ax, fx, lst, _) in PERIM:
        a0, a1 = (D.X0, D.X1) if ax == 'x' else (IY0, IY1)
        wall(b, ax, fx, a0, a1, 0.2, C1 + 0.3, D.TH, "M_Interior_Wallpaper", lst, amp=0.01)
    b.finish(cS)
    b = B("Int_Slabs", 0.5)
    slab(b, IX0, IX1, IY0, IY1, 0.2, FL0 - FIN, "M_Interior_Concrete", hole=D.HATCH)
    slab(b, IX0, IX1, IY0, IY1, C0, FL1 - FIN, "M_Interior_Ceiling", hole=STAIR_HOLE)
    slab(b, IX0, IX1, IY0, IY1, C1, C1 + 0.3, "M_Interior_Ceiling")
    b.finish(cS)
    for lvl, nm in ((0, "Int_GF_Floors"), (1, "Int_UF_Floors")):
        b = B(nm, 0.5)
        for rn, r in ROOMS.items():
            if r[4] != lvl:
                continue
            f, _ = fz(r)
            hole = HATCH_SEAT if rn == "Maintenance" else (STAIR_HOLE if rn == "Landing" else None)
            if rn == "Landing":
                hole = (STAIR_HOLE[0] - 0.1, STAIR_HOLE[1], STAIR_HOLE[2], min(STAIR_HOLE[3] + 0.1, IY1))
            slab(b, r[0], r[1], r[2], r[3], f - FIN, f, r[5], hole=hole, amp=0.0)
        if lvl == 0:   # umbrales de las puertas perimetrales (entrada, trasera) y del paso al anexo: saddle propio, 5 mm sobre el suelo
            W = "M_Museum_WoodDark"
            saddle(b, 0.0, D.Y0 + D.TH / 2 + 0.1, 2.42, D.TH / 2 + 0.16 + 0.0, FL0, W)                 # entrada: mitad interior del muro + 3 cm de suelo
            saddle(b, 0.0, D.Y1 - D.TH / 2, 1.42, D.TH + 0.06, FL0, W)                                  # puerta trasera
            saddle(b, (PASS_X0 + PASS_X1) / 2, D.Y1 - D.TH / 2, PASS_X1 - PASS_X0, D.TH + 0.06, FL0, "M_Interior_Concrete")   # paso al anexo
        # umbrales bajo las puertas de tabique (saddle: cara superior 5 mm sobre el acabado, ligeramente mas ancho que el hueco)
        for (ax, fx, c, w, zs, zt, nm2, kind) in DOORS:
            if (zs < C0) != (lvl == 0):
                continue
            th = next(p[3] for p in PARTS if p[1] == ax and p[2] == fx)
            if ax == 'x':
                saddle(b, c, fx, w + 0.02, th + 0.06, zs, "M_Museum_WoodDark")
            else:
                saddle(b, fx, c, th + 0.06, w + 0.02, zs, "M_Museum_WoodDark")
        b.finish(cS)
    for lvl, nm in ((0, "Int_GF_Partitions"), (1, "Int_UF_Partitions")):
        b = B(nm, 0.5)
        for (pn, ax, fx, th, a0, a1, pl) in PARTS:
            if pl != lvl:
                continue
            z0, z1 = (FL0 - FIN, C0) if lvl == 0 else (FL1 - FIN, C1)
            ops = [(c, w, zs, zt) for (dax, dfx, c, w, zs, zt, _, _) in DOORS if dax == ax and dfx == fx and (zs < C0) == (lvl == 0)]
            wall(b, ax, fx, a0, a1, z0, z1, th, "M_Interior_Wallpaper", ops, amp=0.008)
        b.finish(cS)


def annex_shell(cS):
    """Envolvente del anexo del cuarto de mantenimiento (solo interior): losa de suelo y de techo y muros oeste, este y norte.
    Enlucido por fuera como el ala trasera; los acabados interiores los ponen trims() y el suelo structure() (Maintenance_Annex en ROOMS)."""
    ax0, ax1, ay0, ay1 = ANNEX
    zt = C0 + 0.3
    b = B("Int_Annex_Shell", 0.5)
    slab(b, ax0 - 0.2, ax1 + 0.4, ay0, ay1 + 0.15, 0.2, FL0 - FIN, "M_Interior_Concrete")                   # forjado del suelo
    slab(b, ax0 - 0.2, ax1 + 0.4, ay0, ay1 + 0.15, C0, zt, "M_Interior_Ceiling")                            # techo
    wall(b, 'y', ax0 - 0.1, ay0, ay1, 0.2, C0, 0.2, "M_Museum_Plaster", amp=0.01)                           # oeste (x 3.0..3.2)
    wall(b, 'y', ax1 + 0.2, ay0, ay1, 0.2, C0, 0.4, "M_Museum_Plaster", amp=0.01)                           # este (x 7.6..8.0)
    wall(b, 'x', ay1 + 0.075, ax0 - 0.2, ax1 + 0.4, 0.2, C0, 0.15, "M_Museum_Plaster", amp=0.01)            # norte (y 8.55..8.7)
    ob = b.finish(cS)
    ob["structure"] = True     # render_check lo trata como estructura (no cuenta choques contra otra estructura)


# ======================================================================= acabados de sala
def trims(cT):
    for lvl, nm in ((0, "Int_GF_WallFinish"), (1, "Int_UF_WallFinish")):
        b = WB(nm, 0.5)
        for rn, r in ROOMS.items():
            if r[4] != lvl:
                continue
            f, c = fz(r)
            for sd in sides(r):
                layer(b, sd, f + 0.12, c - 0.1, 0.012, r[6])
                layer(b, sd, f - 0.01, f + 0.15, 0.028, "M_Museum_WoodDark", off=0.0)
                if r[7]:
                    layer(b, sd, f + 0.15, f + r[8], 0.02, r[7], off=0.012)
                    layer(b, sd, f + r[8], f + r[8] + 0.06, 0.045, "M_Museum_Wood", off=0.012)
                if r[9]:
                    layer(b, sd, f + 2.9, f + 2.95, 0.035, "M_Museum_Brass", off=0.012)
                if rn not in ("Maintenance", "Maintenance_Annex"):
                    layer(b, sd, c - 0.16, c, 0.07, "M_Interior_Ceiling", off=0.0)
        b.finish(cT)


def restroom_tiles(cT):
    """Juntas de azulejo (lechada) sobre el friso ceramico de los aseos: lineas cada 0.15 m, respetando los huecos."""
    b = B("Int_Restroom_Tiles", 0.5)
    for rn in ("Restroom_Lobby", "Restroom_1", "Restroom_2"):
        r = ROOMS[rn]
        f, _ = fz(r)
        z0, z1 = f + 0.15, f + r[8]
        for sd in sides(r):
            axis, face, s, a0, a1 = sd
            z = z0 + 0.15
            while z < z1 - 0.02:    # horizontales (cortadas por los huecos igual que el friso)
                layer(b, sd, z - 0.002, z + 0.002, 0.002, "M_Grout", off=0.032, amp=0.0)
                z += 0.15
            ops = side_openings(axis, face, a0, a1)
            Fc = Face(b, axis, face, s)
            u = a0 + 0.15
            while u < a1 - 0.05:    # verticales, saltando puertas y ventanas que cruzan el friso
                if not any(abs(u - c) < w / 2 + 0.004 and zs < z1 and zt > z0 for (c, w, zs, zt) in ops):
                    Fc.box(u, 0.033, (z0 + z1) / 2, 0.004, 0.002, z1 - z0, "M_Grout", bev=0, amp=0.0, cuts=0)
                u += 0.15
    b.finish(cT)


def door_casings(cO):
    b = LB("Int_Door_Casings", 0.5)
    for (ax, fx, c, w, zs, zt, nm, kind) in DOORS + PASSAGES:
        th = next((p[3] for p in PARTS if p[1] == ax and p[2] == fx), D.TH)   # el paso del anexo esta en el muro perimetral
        mat = "M_Museum_Wood"
        for s in (-1, 1):   # arquitrabe moldurado en ambas caras: zocalos, jambas planas con junquillo, cabecero, cornisa y remate
            F = Face(b, ax, fx + s * th / 2, s)
            zj0 = zs + 0.2                      # las jambas arrancan sobre el zocalo (se hunden 1 cm en el bloque) y suben dentro del cabecero
            for sg in (-1, 1):
                uj = c + sg * (w / 2 + 0.05)
                F.box(c + sg * (w / 2 + 0.06), 0.02, zs + 0.1, 0.12, 0.04, 0.2, mat, bev=0.008, amp=0.0, cuts=0)                 # zocalo
                F.box(uj, 0.0125, (zj0 - 0.01 + zt + 0.06) / 2, 0.1, 0.025, zt + 0.07 - zj0, mat, bev=0.006, amp=0.0, cuts=0)     # jamba plana
            F.box(c, 0.014, zt + 0.06, w + 0.2, 0.028, 0.12, mat, bev=0.006, amp=0.0, cuts=0)                            # cabecero plano (3 mm mas saliente que las jambas)
            F.box(c, 0.03, zt + 0.1375, w + 0.3, 0.06, 0.035, mat, bev=0.008, amp=0.0, cuts=0)                           # cornisa
            F.box(c, 0.022, zt + 0.1675, w + 0.26, 0.044, 0.025, mat, bev=0.006, amp=0.0, cuts=0)                        # remate
            rr, u0, u1, zb_ = 0.04, c - (w / 2 + 0.011), c + (w / 2 + 0.011), zt + 0.011
            ar = [(math.cos(math.pi / 2 * k / 4), math.sin(math.pi / 2 * k / 4)) for k in range(1, 4)]
            path = [(u0, zj0 - 0.005), (u0, zb_ - rr)] + [(u0 + rr * (1 - ca), zb_ - rr + rr * sa) for (ca, sa) in ar] + [(u0 + rr, zb_), (u1 - rr, zb_)]
            path += [(u1 - rr * (1 - ca), zb_ - rr + rr * sa) for (ca, sa) in ar[::-1]] + [(u1, zb_ - rr), (u1, zj0 - 0.005)]
            tube(b, [F.P(u, 0.025, z) for (u, z) in path], 0.011, mat, seg=6)                                          # junquillo continuo en el canto del hueco (sube, gira en las esquinas y cruza bajo el cabecero)
            if kind == 'arch':   # clave de piedra: cuna que arranca a ras del intradós y sube hasta la cornisa (antes colgaba 22 cm dentro del hueco)
                kp = [F.P(c - 0.08, 0.0, zt - 0.025), F.P(c + 0.08, 0.0, zt - 0.025), F.P(c + 0.12, 0.0, zt + 0.118), F.P(c - 0.12, 0.0, zt + 0.118)]
                b.prism(kp, tuple(Vector(F.P(0, 0.07, 0)) - Vector(F.P(0, 0, 0))), "M_Museum_Stone", bev=0.005, amp=0.0)
        F = Face(b, ax, fx, 1)
        F.box(c - w / 2 + 0.02, 0.0, (zs + zt) / 2, 0.04, th + 0.02, zt - zs, mat, bev=0.006, amp=0.0, cuts=0)
        F.box(c + w / 2 - 0.02, 0.0, (zs + zt) / 2, 0.04, th + 0.02, zt - zs, mat, bev=0.006, amp=0.0, cuts=0)
        F.box(c, 0.0, zt - 0.02, w, th + 0.02, 0.04, mat, bev=0.006, amp=0.0, cuts=0)
        if kind == 'arch':  # arco rebajado: perfil curvo continuo en las esquinas superiores
            rise, n = 0.55, 14
            Fa = Face(b, ax, fx - th / 2, 1)
            ext = tuple(Vector(Fa.P(0, th, 0)) - Vector(Fa.P(0, 0, 0)))
            zsp = zt - rise
            for sg in (-1, 1):
                pts = [Fa.P(c + sg * w / 2, 0, zsp)]
                for k in range(1, n + 1):
                    z = zsp + rise * k / n
                    e = (w / 2) * 0.5 * (1 - math.sqrt(max(0.0, 1 - ((z - zsp) / rise) ** 2)))
                    pts.append(Fa.P(c + sg * (w / 2 - e), 0, z))
                pts.append(Fa.P(c + sg * w / 2, 0, zt))
                b.prism(pts, ext, "M_Interior_Wallpaper", amp=0.002)
    for dn in HINGE:
        hinge_plates(b, leaf_spec(dn))
    b.finish(cO)


# ----------------------------------------------------------------------- cortinas y estores
def _ss(x):
    x = max(0.0, min(1.0, x))
    return x * x * (3 - 2 * x)


def _keyed(t, keys):
    """Interpolacion suave (smoothstep) entre claves ordenadas (t, valor)."""
    if t <= keys[0][0]:
        return keys[0][1]
    for (t0, v0), (t1, v1) in zip(keys, keys[1:]):
        if t <= t1:
            return v1 if t1 <= t0 else v0 + (v1 - v0) * _ss((t - t0) / (t1 - t0))
    return keys[-1][1]


def _axis_xf(origin, direction):
    """Matriz que lleva el eje Z local (eje de revolucion de loft) a 'direction' y el origen a 'origin'."""
    q = Vector((0, 0, 1)).rotation_difference(Vector(direction).normalized())
    return Matrix.Translation(Vector(origin)) @ q.to_matrix().to_4x4()


def band_loop(b, pts, ht, thick, mat):
    """Cinta cerrada de seccion rectangular (alto ht en Z, grosor thick) que sigue un lazo plano horizontal (lista de puntos 3D)."""
    P = [Vector(p) for p in pts]
    n = len(P)
    cen = sum(P, Vector()) / n
    bm = bmesh.new()
    rv = []
    for i in range(n):
        t = P[(i + 1) % n] - P[(i - 1) % n]
        nr = Vector((t.y, -t.x, 0)).normalized()
        if nr.dot(P[i] - cen) < 0:
            nr = -nr
        rv.append([bm.verts.new(P[i] + nr * so * thick / 2 + Vector((0, 0, sz * ht / 2))) for (so, sz) in ((1, 1), (1, -1), (-1, -1), (-1, 1))])
    for i in range(n):
        a, c = rv[i], rv[(i + 1) % n]
        for k in range(4):
            bm.faces.new((a[k], a[(k + 1) % 4], c[(k + 1) % 4], c[k]))
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    b._finish(bm, (0, 0, 0), (0, 0, 0), mat, 0, 0, 1)


WALL_V = -0.4125   # cara visible del acabado de pared (muro interior v = -0.4 + 12 mm de acabado)


def wall_arm(b, F, u, z, v_tip, mat, knob=False, r_arm=0.0075):
    """Soporte de laton atornillado a la pared (v = -0.4): roseta torneada + brazo recto hasta v_tip (+ boton redondeado si knob).
    Un solo loft con eje perpendicular a la pared."""
    d_tip = WALL_V - v_tip
    rings = [(0.0, 0.030), (0.004, 0.032), (0.008, 0.022), (0.011, 0.012), (0.014, r_arm + 0.001), (d_tip * 0.6, r_arm)]
    if knob:   # boton torneado en la punta
        rings += [(d_tip - 0.034, r_arm), (d_tip - 0.026, r_arm + 0.002), (d_tip - 0.018, 0.0155), (d_tip - 0.008, 0.0185), (d_tip, 0.0165), (d_tip + 0.006, 0.010), (d_tip + 0.0085, 0.0015)]
    else:
        rings += [(d_tip, r_arm), (d_tip + 0.001, 0.0015)]
    o = Vector(F.P(u, WALL_V, z))
    dr = Vector(F.P(u, WALL_V - 1.0, z)) - o
    loft(b, [(d, r, r, 0.0) for (d, r) in rings], mat, seg=8, xf=_axis_xf(o, dr))


def finial(b, F, u_end, sgn, v, z, mat="M_Museum_Brass"):
    """Remate torneado de barra de cortina (loft con eje a lo largo de la barra, sgn = sentido hacia fuera)."""
    prof = [(-0.004, 0.0125), (0.0, 0.0155), (0.006, 0.0155), (0.010, 0.010), (0.016, 0.0085), (0.022, 0.0115), (0.030, 0.0195),
            (0.037, 0.0205), (0.044, 0.0175), (0.052, 0.008), (0.0575, 0.0015)]
    o = Vector(F.P(u_end, v, z))
    dr = Vector(F.P(u_end + sgn, v, z)) - o
    loft(b, [(d, r, r, 0.0) for (d, r) in prof], mat, seg=8, xf=_axis_xf(o, dr))


def drapes(cu, F, cm, c, w, zt, zhem, z_tb, gap):
    """Cortinas de ventana: barra de laton sobre soportes cortos (8-10 cm de la pared), remates torneados, anillas y un par SIMETRICO de
    paneles de tela (una sola lamina ondulada con cabecera fruncida, abocinada hacia el bajo, recogida con alzapano y gancho de pared)."""
    brass = "M_Museum_Brass"
    G = Face(cu, F.axis, F.fixed, F.sign)
    er = min(0.30, gap - 0.015)                 # vuelo de la barra a cada lado del hueco
    vr, rr = -0.50, 0.0125                      # eje y radio de la barra
    zr = zt + 0.22
    if abs(zr - (zhem - 0.04 + 2.925)) < 0.07:    # la barra no debe coincidir con la moldura de cuadros (f+2.9..2.95): sube por encima
        zr = zhem - 0.04 + 3.02
    Rm, rt = 0.0225, 0.003                      # anilla: radio mayor y del alambre
    zc = zr - (Rm - rt - rr)                    # la anilla cuelga de la barra (su cara interior toca la parte alta)
    z_top = zc - Rm                             # arranque de la tela (centro del alambre inferior de la anilla)
    ext = w / 2 + er
    tube(cu, [F.P(c - ext, vr, zr), F.P(c + ext, vr, zr)], rr, brass, seg=14)
    for sg in (-1, 1):
        finial(cu, F, c + sg * ext, sg, vr, zr)
    brs = [sg * (ext - 0.03) for sg in (-1, 1)] + ([0.0] if w > 1.5 else [])
    for ub in brs:   # soportes: roseta + brazo + copa que abraza la barra
        wall_arm(cu, F, c + ub, zr, vr + 0.0165 - 0.002, brass)
        tube(cu, [F.P(c + ub, vr + 0.0165 * math.cos(a_), zr + 0.0165 * math.sin(a_)) for a_ in [math.tau * q / 8 for q in range(8)]], 0.004, brass, seg=4, closed=True)
    L_ = z_top - zhem
    t_tb = (z_top - z_tb) / L_
    eo0 = w / 2 + er - 0.06                     # borde exterior del panel en la cabecera
    ei0 = w / 2 - 0.05
    wt0 = eo0 - ei0
    wtb = 0.36 * wt0                            # ancho del fardo recogido
    k = max(3, int(round(wt0 / 0.045)))         # pliegues del panel
    t1, t2 = max(0.05, t_tb - 0.035), min(0.95, t_tb + 0.035)
    eo_keys = [(0.0, eo0), (t1, eo0 + 0.01), (t2, eo0 + 0.015), (1.0, eo0 + 0.03)]
    ei_keys = [(0.0, ei0), (t1, eo0 + 0.01 - wtb), (t2, eo0 + 0.015 - wtb), (1.0, max(w / 2 - 0.08, eo0 + 0.03 - 1.7 * wt0))]
    nc = k * 4                                  # 4 columnas por pliegue (la onda queda suave con sombreado liso)
    hd = 0.04 / L_                              # cinta de cabecera
    hm = 0.045 / L_                             # dobladillo
    ts = sorted({round(j / 5, 4) for j in range(6)} | {round(x, 4) for x in (hd, t1, t2, 1 - hm * 2) if 0.0 < x < 1.0})
    ts = [t for i_, t in enumerate(ts[:-1]) if i_ == 0 or t - ts[i_ - 1] > 0.015] + [1.0]   # filas: uniformes + densas en el alzapano (donde cambia el ancho)
    nr = len(ts)

    def prof(t):
        eo, ei = _keyed(t, eo_keys), _keyed(t, ei_keys)
        wd = eo - ei
        am = max(0.40 * wd / k, 0.014 if t1 - 0.02 < t < t2 + 0.02 else 0.010)
        am = min(am, 0.040) * (1 + 0.12 * math.sin(2 * math.pi * 1.7 * t + 0.7)) * (0.65 if t < hd else 1.0)
        vm = vr - 0.062 * _ss((t - 0.04) / 0.8)
        return ei, wd, am, vm, 0.6 * math.sin(math.pi * 2.3 * t)
    def fold(a_, s_, t):   # pliegue de tela: seno con segundo armonico y amplitud que varia de un pliegue a otro (no tubos de organo)
        return math.sin(a_) * (1 + 0.24 * math.sin(math.tau * k * 0.37 * s_ + 1.3 + 2.0 * t)) + 0.2 * math.sin(2 * a_ + 1.1 + 3 * t)
    toward = Vector(F.P(0, 0, 0)) - Vector(F.P(0, 1, 0))      # hacia la pared
    for sg in (-1, 1):
        grid, th = [], []
        for j in range(nr):
            t = ts[j]
            ei, wd, am, vm, ph = prof(t)
            z = z_top - t * L_
            grid.append([Vector(F.P(c + sg * (ei + wd * i / nc), vm + am * fold(math.tau * k * i / nc + ph, i / nc, t), z)) for i in range(nc + 1)])
            th.append(0.004 + 0.005 * (1 - _ss(t / hd)) + 0.004 * _ss((t - 1 + hm * 2) / hm))
        cloth(cu, grid, th, cm, toward)
        for i in range(0, k + 1, 2):   # anillas de la cabecera (una de cada dos pliegues)
            ei, wd, am, vm, ph = prof(0.0)
            ur = c + sg * (ei + wd * i / k)
            tube(cu, [F.P(ur, vr + Rm * math.cos(a_), zc + Rm * math.sin(a_)) for a_ in [math.tau * q / 10 for q in range(10)]], rt, brass, seg=4, closed=True)
        # alzapano: banda de tela de seccion rectangular alrededor del fardo + tira hasta el gancho de laton
        ei, wd, am, vm, ph = prof(t_tb)
        a_, b_ = wd / 2 + 0.012, am + 0.014
        cen = ei + wd / 2
        z_b = z_top - t_tb * L_
        loop = []
        for q in range(18):
            ang = math.tau * q / 18
            ca, sa = math.cos(ang), math.sin(ang)
            loop.append(F.P(c + sg * (cen + a_ * math.copysign(abs(ca) ** (1 / 3), ca)), vm + b_ * math.copysign(abs(sa) ** (1 / 3), sa), z_b))
        band_loop(cu, loop, 0.04, 0.008, cm)
        uh = w / 2 + er - 0.01
        wall_arm(cu, F, c + sg * uh, z_b, vm - 0.045, brass, knob=True)
        ln = uh - (cen + a_) + 0.004
        G.box(c + sg * (uh + cen + a_ - 0.004) / 2, vm, z_b, ln, 0.008, 0.04, cm, bev=0.0, amp=0.0, cuts=0)


def roman_blind(cu, F, cm, c, w, zs, z_rail, arched):
    """Estor romano montado DENTRO del derrame (entre las jambas), recogido en 3 pliegues blandos en lo alto y con el resto de la
    tela colgando plana hasta una barra inferior: deja libre la mayor parte del cristal. Cabecera de madera, cordon con bellota."""
    G = Face(cu, F.axis, F.fixed, F.sign)
    bw = w - 0.12 + 0.002                       # entre las jambas del derrame (que llegan a w/2 - 0.06)
    vf = -0.335                                 # plano de la tela (entre la pared interior -0.4 y la cuadricula -0.27)
    G.box(c, vf, z_rail - 0.0175, bw, 0.05, 0.035, "M_Museum_WoodDark", bev=0.007, amp=0.0, cuts=0)       # cabecera
    for sg in (-1, 1):   # tapas de laton en los extremos de la cabecera
        G.box(c + sg * (bw / 2 - 0.004), vf, z_rail - 0.0175, 0.008, 0.052, 0.037, "M_Museum_Brass", bev=0.003, amp=0.0, cuts=0)
    z0 = z_rail - 0.035                         # arranque de la tela bajo la cabecera
    drop = min(0.60, 0.36 * (z_rail - zs))      # largo total del estor recogido a medias
    nf, hf = 3, 0.105                           # 3 pliegues de 10,5 cm apilados
    amp = 0.030
    nrw = 5                                     # filas por pliegue
    rows = [(0.0, 0.0)]                         # (profundidad z desde z0, saliente hacia la sala)
    for f_ in range(nf):
        for q in range(1, nrw + 1):
            fr_ = q / nrw
            rows.append(((f_ + fr_) * hf, amp * math.sin(math.pi * fr_) ** 0.85))
    for q in range(1, 4):                       # tela plana colgando
        zz = nf * hf + (drop - nf * hf) * q / 3
        rows.append((zz, 0.0))
    ncl = 6
    toward = Vector(F.P(0, 0, 0)) - Vector(F.P(0, 1, 0))
    grid, th = [], []
    for (dz, sal) in rows:
        gp = []
        for i in range(ncl + 1):
            x = (i / ncl - 0.5) * (bw - 0.012)
            gp.append(Vector(F.P(c + x, vf - sal * (1 - 0.06 * math.cos(math.pi * x / bw * 2) ** 2), z0 - dz)))
        grid.append(gp)
        th.append(0.004 + (0.006 if dz > drop - 0.045 else 0.0))
    cloth(cu, grid, th, cm, toward)
    zb = z0 - drop
    G.box(c, vf - 0.002, zb - 0.004, bw - 0.012, 0.014, 0.022, "M_Museum_WoodDark", bev=0.005, amp=0.0, cuts=0)   # varilla del bajo
    # cordon de tiro con bellota de madera, junto a la jamba derecha y por delante de los pliegues
    uc, vc = c + (bw / 2 - 0.03), vf - amp - 0.012
    z_end = zb - 0.20
    tube(cu, [F.P(uc, vc, z_rail - 0.0175), F.P(uc, vc, z_end + 0.03)], 0.0025, "M_Paper", seg=8)
    ac = [(0.0, 0.0015), (0.002, 0.007), (0.009, 0.0125), (0.018, 0.0135), (0.027, 0.0105), (0.033, 0.0055), (0.036, 0.0035), (0.040, 0.004), (0.043, 0.0015)]
    o = Vector(F.P(uc, vc, z_end))
    loft(cu, [(d, r, r, 0.0) for (d, r) in ac], "M_Museum_Wood", seg=12, xf=_axis_xf(o, (0, 0, 1)))
    # (acorn: z crece hacia arriba desde la punta inferior; el casquete queda arriba)


def windows_int(cO):
    fr, gl, cu = LB("Int_Window_Frames", 0.5), B("Int_Window_Glass", 0.5), LB("Int_Curtains", 0.5)
    rd = HB("Int_Radiators", 0.5)
    for (ax, fx, lst, key) in PERIM:
        for (c, w, zs, zt) in lst:
            F, G, CU = X.faces(fr)[key], X.faces(gl)[key], X.faces(cu)[key]
            h, zm = zt - zs, (zs + zt) / 2
            if zs < FL0 + 0.01:  # puerta exterior / paso al anexo (lo resuelven door_casings y la puerta trasera)
                continue
            arched = X.is_arched(c, w, zs, zt)
            zsp = zt - (X.arch_rise(w) if arched else 0.0)
            for sg in (-1, 1):   # jambas del derrame (suben 3 cm dentro del cabecero/arco) y guarniciones exteriores (nacen dentro del alfeizar y suben hasta el cabecero/arco)
                F.box(c + sg * (w / 2 - 0.03), -0.3, (zs + zsp) / 2 + 0.015, 0.06, 0.2, zsp - zs + 0.03, "M_Museum_Wood", bev=0.006, amp=0.003, cuts=0)
                F.box(c + sg * (w / 2 + 0.05), -0.42, (zs + 0.02 + zsp + 0.06) / 2, 0.1, 0.04, zsp + 0.04 - zs, "M_Museum_Wood", bev=0.012, amp=0.0, cuts=1)
            bead = [(c + (w / 2 + 0.012), zs + 0.03), (c + (w / 2 + 0.012), zsp)]   # junquillo continuo en el canto interior de la guarnicion
            if arched:   # mismo arco rebajado que el exterior: enjutas, banda curva de la guarnicion (misma seccion que las jambas), derrame curvo y abanico
                rise = X.arch_rise(w)
                X.arch_spandrels(fr, F, c, w, zt, -0.4, 0.0, "M_Interior_Wallpaper")
                rn_ = room_at(key, c, zs)   # piel de pintura de la sala sobre las enjutas (antes asomaba el papel crema en las esquinas del arco)
                X.arch_spandrels(fr, F, c, w, zt, -0.412, -0.4, ROOMS[rn_][6] if rn_ else "M_Interior_Wallpaper")
                for (v0, v1, ra, rb, wd_, dp) in ((-0.4, -0.44, w / 2, rise, 0.1, 0.04), (-0.2, -0.4, w / 2 - 0.06, rise - 0.06, 0.06, 0.2)):
                    inner = X.arch_pts(c, zsp, ra, rb, 18)
                    outer = X.arch_pts(c, zsp, ra + wd_, rb + wd_, 18)
                    pol = [F.P(u, v0, z) for (u, z) in inner] + [F.P(u, v0, z) for (u, z) in outer[::-1]]
                    ext = tuple(Vector(F.P(0, v1, 0)) - Vector(F.P(0, v0, 0)))
                    fr.prism(pol, ext, "M_Museum_Wood", bev=(0.012 if dp < 0.1 else 0.006), amp=0.0)
                bead += [(u, z) for (u, z) in X.arch_pts(c, zsp, w / 2 + 0.012, rise + 0.012, 18)][1:]
                F.box(c, -0.25, zsp, w - 0.1, 0.06, 0.07, "M_Museum_Wood", bev=0.01, amp=0.003, cuts=0)
                for k in range(1, 6):
                    a_ = math.pi * k / 6
                    fr.seg(F.P(c, -0.25, zsp + 0.03), F.P(c + (w / 2 - 0.09) * math.cos(a_), -0.25, zsp + (rise - 0.09) * math.sin(a_)), 0.014, "M_Museum_Wood", seg=5)
                bead += [(c - (w / 2 + 0.012), zs + 0.03)]
            else:
                F.box(c, -0.3, zt - 0.03, w, 0.2, 0.06, "M_Museum_Wood", bev=0.006, amp=0.003, cuts=0)
                F.box(c, -0.42, zt + 0.07, w + 0.24, 0.05, 0.12, "M_Museum_Wood", bev=0.012, amp=0.0, cuts=1)
                rr, zb_ = 0.035, zt + 0.012
                bead = [(c + (w / 2 + 0.012), zs + 0.03), (c + (w / 2 + 0.012), zb_ - rr)]
                bead += [(c + (w / 2 + 0.012) - rr * (1 - math.cos(math.pi / 2 * k / 5)), zb_ - rr + rr * math.sin(math.pi / 2 * k / 5)) for k in range(1, 6)]
                bead += [(c - (w / 2 + 0.012) + rr * (1 - math.cos(math.pi / 2 * k / 5)), zb_ - rr + rr * math.sin(math.pi / 2 * k / 5)) for k in range(5, 0, -1)]
                bead += [(c - (w / 2 + 0.012), zb_ - rr), (c - (w / 2 + 0.012), zs + 0.03)]
            tube(fr, [F.P(u, -0.441, z) for (u, z) in bead], 0.012, "M_Museum_Wood", seg=6)
            F.box(c, -0.45, zs + 0.02, w + 0.24, 0.14, 0.045, "M_Museum_Wood", bev=0.012, amp=0.0, cuts=1)            # alfeizar
            F.box(c, -0.42, zs - 0.081, w + 0.2, 0.03, 0.158, "M_Museum_Wood", bev=0.008, amp=0.0, cuts=0)            # faldon bajo el alfeizar (mismo ancho que las guarniciones)
            G.box(c, -0.2, zm, w - 0.08, 0.03, h - 0.08, "M_Museum_Glass", bev=0, amp=0, cuts=0)
            h_s = zsp - zs   # cuadricula solo bajo el arranque del arco
            zm, h = (zs + zsp) / 2, h_s
            iw, ih = w - 0.2, h - 0.2
            for (uu, zz, su, sz) in ((c - iw / 2, zm, 0.06, ih), (c + iw / 2, zm, 0.06, ih), (c, zm - ih / 2, iw, 0.06), (c, zm + ih / 2, iw, 0.06)):
                F.box(uu, -0.245, zz, su, 0.05, sz, "M_Museum_Wood", bev=0.008, amp=0.003, cuts=0)
            cols = 3 if w > 1.5 else (2 if w >= 1.0 else 1)
            rows = 3 if h > 1.3 else (2 if h > 0.6 else 1)
            for i in range(1, cols):
                F.box(c - iw / 2 + i * iw / cols, -0.24, zm, 0.035, 0.03, ih, "M_Museum_Wood", bev=0, amp=0.003, cuts=0)
            for j in range(1, rows):
                F.box(c, -0.24, zm - ih / 2 + j * ih / rows, iw, 0.03, 0.035, "M_Museum_Wood", bev=0, amp=0.003, cuts=0)
            high = (zs - (FL0 if zs < FL1 else FL1)) > 1.5
            behind_stair = key == 'B' and zs < C0 and STAIR_HOLE[0] <= c <= STAIR_HOLE[1]   # rellano delante
            floor = FL0 if zs < C0 else FL1
            over_void = key == 'B' and zs > C0 and STAIR_HOLE[0] <= c <= STAIR_HOLE[1]   # ventana alta sobre el hueco de escalera: sin suelo para el radiador
            if abs((zs - floor) - 0.9) < 0.05 and RAD_AT.get(room_at(key, c, zs)) == (key, c) and not over_void:
                radiator(rd, X.faces(rd)[key], c, w, floor)
            if not high and not behind_stair:
                cm = L.curtain_mat(key, c, zs)
                # holgura hasta el tabique mas cercano (igual a ambos lados: cortinas simetricas)
                a0, a1 = curtain_span(key, c, zs)
                dist = min(a1 - (c + w / 2), (c - w / 2) - a0)
                lvl = 0 if zs < C0 else 1
                for (c2, w2, zs2, zt2) in lst:   # casing de los huecos vecinos del mismo muro y planta
                    if (c2, zs2) != (c, zs) and (0 if zs2 < C0 else 1) == lvl:
                        dist = min(dist, abs(c2 - c) - w2 / 2 - 0.12 - w / 2)
                axw, fw_ = {'F': ('x', IY0), 'B': ('x', IY1), 'W': ('y', IX0), 'E': ('y', IX1)}[key]
                for (ax2, f2, u2, w2, zc2, h2, sc2) in ART_WALL:   # cuadros del mismo muro y planta (cartela en un lado)
                    if ax2 == axw and abs(f2 - fw_) < 0.05 and (0 if zc2 < C0 else 1) == lvl:
                        lo, hi = u2 - (w2 / 2 + 0.14 + (0.2 if sc2 < 0 else 0.0)), u2 + (w2 / 2 + 0.14 + (0.2 if sc2 > 0 else 0.0))
                        if lo >= c + w / 2:
                            dist = min(dist, lo - (c + w / 2))
                        elif hi <= c - w / 2:
                            dist = min(dist, (c - w / 2) - hi)
                gap = dist - 0.07
                if gap < 0.2:   # sin sitio para cortinas junto al tabique: estor romano dentro del derrame
                    roman_blind(cu, F, cm, c, w, zs, zsp if arched else zt - 0.06, arched)
                else:
                    drapes(cu, F, cm, c, w, zt, floor + 0.04, zs + 0.25 * (zt - zs), gap)
    # puertas exteriores vistas desde dentro (mismas medidas que el exterior)
    X.door(fr, 'F', 0.0, 2.4, FL0, D.FRONT[0][3], "M_Museum_Door", leaves=2, transom=True)
    X.faces(gl)['F'].box(0.0, -0.2, D.FRONT[0][3] - 0.375, 2.1, 0.03, 0.66, "M_Museum_Glass", bev=0, amp=0, cuts=0)
    # puerta trasera: ahora da al enlace con el ala nueva -> solo el marco; la hoja es Door_GalleryVII (abierta)
    Fb, zb = X.faces(fr)['B'], D.BACK[0][3]
    for sg in (-1, 1):
        Fb.box(sg * (0.7 - 0.07), -0.1, (FL0 + zb) / 2, 0.14, 0.5, zb - FL0, "M_Museum_Wood", bev=0.02, amp=0.01, cuts=1)
    Fb.box(0.0, -0.1, zb - 0.07, 1.4, 0.5, 0.14, "M_Museum_Wood", bev=0.02, amp=0.01, cuts=1)
    hinge_plates(fr, GV_SPEC)
    for key, c, w, zt, hs in (('F', 0.0, 2.4, D.FRONT[0][3], (-0.16, 0.16)), ('B', 0.0, 1.4, D.BACK[0][3], ())):
        F = X.faces(fr)[key]
        for sg in (-1, 1):
            F.box(c + sg * (w / 2 + 0.05), -0.42, (FL0 + zt) / 2, 0.12, 0.04, zt - FL0 + 0.06, "M_Museum_Wood", bev=0.012, amp=0.004, cuts=1)
        F.box(c, -0.42, zt + 0.07, w + 0.3, 0.05, 0.14, "M_Museum_Wood", bev=0.012, amp=0.004, cuts=1)
        for hu in hs:
            F.box(c + hu, -0.2, FL0 + 1.15, 0.05, 0.07, 0.3, "M_Museum_Brass", bev=0.01, amp=0.003, cuts=0)
    for b in (fr, gl, cu, rd):
        b.finish(cO)


# ======================================================================= escalera en U
# Dos tramos paralelos de 10 huellas (0.27) + rellano: tramo 1 (bajo, x -1.75..-0.63) sube hacia +y desde y=1.3; el rellano ocupa y 4.0..5.6
# (retranqueado junto a la puerta trasera); tramo 2 (alto, x -3.0..-1.85) sube hacia -y y llega a la planta alta en y=1.3 (borde del hueco).
# Entre los dos tramos va un muro medianero (tabique de 0.1) con zanca de madera oscura.
ST_TY = 0.27                      # huella
ST_R = (FL1 - FL0) / 22           # contrahuella (22 desde FL0 hasta FL1)
ST_S = ST_R / ST_TY               # pendiente
ST_YB = 1.3                       # arranque del tramo 1 / llegada del tramo 2
ST_YL = ST_YB + 10 * ST_TY        # 4.0: inicio del rellano
ST_ZL = FL0 + 11 * ST_R           # cota del rellano
ST_X2 = (-3.0, -1.85)             # tramo 2 (alto)
ST_X1 = (-1.75, -0.63)            # tramo 1 (bajo); faldon de cierre en x -0.63..-0.61
ST_NOSE = 0.03                    # vuelo del bocel de cada huella
ST_TK = 0.04                      # grosor de la tabla de la huella
ST_H = 0.9                        # alto del pasamanos sobre la linea de las narices
ST_XR1, ST_XR2 = -0.705, -1.905   # eje de balaustres del tramo 1 (lado abierto) y del tramo 2 (lado del medianero)
ST_XW = -2.885                    # eje del pasamanos de pared del tramo 2


def zn1(y):
    """Linea de las narices del tramo 1 (cota z) en la coordenada y."""
    return FL0 + ST_R + (y - (ST_YB - ST_NOSE)) * ST_S


def zn2(y):
    """Linea de las narices del tramo 2 (cota z) en la coordenada y."""
    return ST_ZL + ST_R + (ST_YL + ST_NOSE - y) * ST_S


def stairs(cS):
    b = B("Int_Stairs", 0.5)
    r, ty = ST_R, ST_TY
    wp, wd = "M_Interior_Wallpaper", "M_Museum_Wood"
    x1a, x1b = ST_X1
    x2a, x2b = ST_X2
    for i in range(10):    # tramo 1: masa de contrahuellas + tabla de la huella con bocel
        y0, top = ST_YB + i * ty, FL0 + (i + 1) * r
        b.box(((x1a + x1b) / 2, y0 + ty / 2, (FL0 + top - ST_TK) / 2), (x1b - x1a, ty, top - ST_TK - FL0), wp, bev=0, amp=0.0, cuts=0)
        b.box(((x1a + x1b) / 2, y0 + ty / 2 - ST_NOSE / 2, top - ST_TK / 2), (x1b - x1a, ty + ST_NOSE, ST_TK), wd, bev=0.008, amp=0.0, cuts=1)
    for j in range(10):    # tramo 2
        y1, top = ST_YL - j * ty, ST_ZL + (j + 1) * r
        b.box(((x2a + x2b) / 2, y1 - ty / 2, (FL0 + top - ST_TK) / 2), (x2b - x2a, ty, top - ST_TK - FL0), wp, bev=0, amp=0.0, cuts=0)
        b.box(((x2a + x2b) / 2, y1 - ty / 2 + ST_NOSE / 2, top - ST_TK / 2), (x2b - x2a, ty + ST_NOSE, ST_TK), wd, bev=0.008, amp=0.0, cuts=1)
    # rellano: cuerpo en L (se retranquea junto al hueco de la puerta trasera: libre 0.1 hasta su jamba) + tablero de madera
    ya, yb = ST_YL, 5.6
    b.box(((-3.0 - 0.8) / 2, (ya + yb) / 2, (FL0 + ST_ZL - ST_TK) / 2), (2.2, yb - ya, ST_ZL - ST_TK - FL0), wp, bev=0, amp=0.0, cuts=0)
    b.box((-0.715, (ya + 5.3) / 2, (FL0 + ST_ZL - ST_TK) / 2), (0.17, 5.3 - ya, ST_ZL - ST_TK - FL0), wp, bev=0, amp=0.0, cuts=0)
    b.box((-1.9, (ST_YL - ST_NOSE + yb) / 2, ST_ZL - ST_TK / 2), (2.2, yb - ST_YL + ST_NOSE, ST_TK), wd, bev=0.008, amp=0.0, cuts=2)
    b.box((-0.715, (ST_YL - ST_NOSE + 5.3) / 2, ST_ZL - ST_TK / 2), (0.17, 5.3 - ST_YL + ST_NOSE, ST_TK), wd, bev=0.008, amp=0.0, cuts=1)
    # nariz de la llegada a la planta alta (sobre el borde del hueco)
    b.box(((x2a + x2b) / 2, ST_YB + 0.015, FL1 - 0.02), (x2b - x2a, 0.03, 0.04), wd, bev=0.008, amp=0.0, cuts=1)
    # faldon liso del lado abierto del tramo 1 y del rellano (papel pintado) con zanca de madera oscura encima
    xs = -0.63
    zt0 = zn1(ST_YB) + 0.05
    b.prism([(xs, ST_YB, FL0), (xs, 5.3, FL0), (xs, 5.3, ST_ZL + 0.05), (xs, ST_YL - ST_NOSE, ST_ZL + 0.05), (xs, ST_YB, zt0)], (0.02, 0, 0), wp, amp=0.0)
    ln1 = math.hypot(ST_YL - ST_NOSE - ST_YB, ST_ZL + 0.05 - zt0)
    b.box((-0.62, (ST_YL - ST_NOSE + ST_YB) / 2, (ST_ZL + 0.05 + zt0) / 2), (0.07, ln1 + 0.01, 0.04), "M_Museum_WoodDark", rot=(math.degrees(math.atan(ST_S)), 0, 0), bev=0.008, amp=0.0, cuts=2)
    b.box((-0.62, (ST_YL - ST_NOSE + 5.3) / 2, ST_ZL + 0.05), (0.07, 5.3 - ST_YL + ST_NOSE, 0.04), "M_Museum_WoodDark", bev=0.008, amp=0.0, cuts=1)
    # medianero entre los dos tramos (x -1.85..-1.75): perfil de la linea de narices del tramo 2; recortado al nivel de la planta alta
    xm = ST_X2[1]
    ztop = lambda y: zn2(y) + 0.05
    yc = ST_YB + (ztop(ST_YB) - FL1) / ST_S
    b.prism([(xm, ST_YB, FL0), (xm, ST_YL, FL0), (xm, ST_YL, ztop(ST_YL)), (xm, yc, FL1), (xm, ST_YB, FL1)], (0.1, 0, 0), wp, amp=0.0)
    ln2 = math.hypot(ST_YL - yc, FL1 - ztop(ST_YL))
    b.box((-1.8, (ST_YL + yc) / 2, (ztop(ST_YL) + FL1) / 2), (0.11, ln2, 0.04), "M_Museum_WoodDark", rot=(-math.degrees(math.atan(ST_S)), 0, 0), bev=0.008, amp=0.0, cuts=2)
    b.finish(cS)

    # ---------------------------------------------------------------- barandillas (todo apoyado en suelo / huellas / rellano)
    rl = HB("Int_Stair_Railings", 0.5)
    dk, mt, br = "M_Museum_WoodDark", "M_Museum_Metal", "M_Museum_Brass"

    def newel(x, y, z0, zr):
        zt = zr + 0.08
        rl.box((x, y, (z0 + zt) / 2), (0.09, 0.09, zt - z0), dk, bev=0.012, amp=0.0, cuts=0)
        rl.box((x, y, z0 + 0.06), (0.11, 0.11, 0.12), dk, bev=0.012, amp=0.0, cuts=0)           # zocalo del poste
        rl.cyl((x, y, zt + 0.015), 0.05, 0.03, br, seg=12, bev=0, amp=0.001)                      # remate torneado: base, cuello ahusado y copete
        rl.cyl((x, y, zt + 0.06), 0.03, 0.06, br, seg=10, r2=0.02, bev=0, amp=0.001)
        rl.cyl((x, y, zt + 0.1), 0.045, 0.02, br, seg=12, bev=0, amp=0.001)

    def handrail(p0, p1):
        tube(rl, [p0, p1], 0.03, dk, seg=10)

    def baluster(x, y, z0, z1):
        rl.seg((x, y, z0), (x, y, z1), 0.0125, mt, seg=6)

    # lado abierto del tramo 1 + rellano
    zr1 = lambda y: zn1(y) + ST_H
    yb0, yl1, ye = 1.2, ST_YL + 0.09, 5.2
    newel(ST_XR1, yb0, FL0, zr1(yb0))
    newel(ST_XR1, yl1, ST_ZL, zr1(yl1))
    newel(ST_XR1, ye, ST_ZL, zr1(yl1))
    handrail((ST_XR1, yb0, zr1(yb0)), (ST_XR1, yl1, zr1(yl1)))
    handrail((ST_XR1, yl1, zr1(yl1)), (ST_XR1, ye, zr1(yl1)))
    for i in range(10):
        for off in (0.06, 0.2):
            y = ST_YB + i * ST_TY + off
            baluster(ST_XR1, y, FL0 + (i + 1) * ST_R, zr1(y))
    n = 10
    for k in range(1, n):
        baluster(ST_XR1, yl1 + (ye - yl1) * k / n, ST_ZL, zr1(yl1))
    # lado del medianero del tramo 2 + guardacuerpos de la planta alta alrededor del hueco
    zr2 = lambda y: zn2(y) + ST_H
    yt = ST_YB - 0.05                   # poste superior sobre el suelo de la planta alta, justo antes del borde del hueco
    yl2 = ST_YL + 0.09
    newel(ST_XR2, yl2, ST_ZL, zr2(yl2))
    newel(ST_XR2, yt, FL1, zr2(yt))
    handrail((ST_XR2, yl2, zr2(yl2)), (ST_XR2, yt, zr2(yt)))
    for j in range(10):
        for off in (0.06, 0.2):
            y = ST_YL - j * ST_TY - off
            baluster(ST_XR2, y, ST_ZL + (j + 1) * ST_R, zr2(y))
    zg = zr2(yt)                        # el guardacuerpos arranca a la altura del poste superior
    xc, yn = -0.56, 5.45
    newel(xc, yt, FL1, zg)
    newel(xc, yn, FL1, zg)
    handrail((ST_XR2, yt, zg), (xc, yt, zg))
    handrail((xc, yt, zg), (xc, yn, zg))
    n = 11
    for k in range(1, n):
        baluster(ST_XR2 + (xc - ST_XR2) * k / n, yt, FL1, zg)
    n = 34
    for k in range(1, n):
        baluster(xc, yt + (yn - yt) * k / n, FL1, zg)
    # pasamanos de pared del tramo 2 con ménsulas de latón (placa en el muro + brazo)
    ya, yz = ST_YL + 0.3, yt - 0.25
    rr_ = 0.07        # los dos extremos del pasamanos de pared giran contra el muro (remate de retorno, sin cabo suelto)
    zA, zB = zn2(ST_YL + ST_NOSE) + ST_H, zr2(yt)
    pa = [(-2.99, ya + rr_, zA)] + [(ST_XW - rr_ + rr_ * math.cos(math.radians(a_)), ya + rr_ * math.sin(math.radians(a_)), zA) for a_ in (90, 72, 54, 36, 18, 0)]
    pz = [(ST_XW - rr_ + rr_ * math.cos(math.radians(a_)), yz - rr_ * math.sin(math.radians(a_)), zB) for a_ in (0, 18, 36, 54, 72, 90)] + [(-2.99, yz - rr_, zB)]
    tube(rl, pa + [(ST_XW, ST_YL + ST_NOSE, zA), (ST_XW, yt, zB)] + pz, 0.025, dk, seg=10)
    for (yy, zz) in ((ST_YL + 0.18, zn2(ST_YL + ST_NOSE) + ST_H), (3.7, zr2(3.7)), (2.95, zr2(2.95)), (2.2, zr2(2.2)), (1.45, zr2(1.45)), (yz + 0.05, zr2(yt))):
        rl.box((-2.979, yy, zz), (0.01, 0.05, 0.07), br, bev=0.002, amp=0.0, cuts=0)
        rl.seg((-2.975, yy, zz), (ST_XW, yy, zz - 0.02), 0.008, br, seg=6)
    rl.finish(cS)


# ======================================================================= escotilla y sotano
def hatch(cU):
    hx0, hx1, hy0, hy1 = D.HATCH
    cx, cy = (hx0 + hx1) / 2, (hy0 + hy1) / 2
    b = B("Hatch_Frame", 0.5)
    for (x, y, sx, sy) in ((cx, hy0 - 0.04, hx1 - hx0 + 0.16, 0.08), (cx, hy1 + 0.04, hx1 - hx0 + 0.16, 0.08),
                           (hx0 - 0.04, cy, 0.08, hy1 - hy0), (hx1 + 0.04, cy, 0.08, hy1 - hy0)):
        b.box((x, y, FL0 - 0.03), (sx, sy, 0.1), "M_Hatch_Metal", bev=0.012, amp=0.002, cuts=1)
    for (bx_, by_) in ((hx0 - 0.04, hy0 - 0.04), (hx1 + 0.04, hy0 - 0.04), (hx0 - 0.04, hy1 + 0.04), (hx1 + 0.04, hy1 + 0.04)):
        b.cyl((bx_, by_, FL0 + 0.0215), 0.011, 0.007, "M_Museum_Brass", seg=10, bev=0, amp=0.0)        # tornillos de esquina del marco
    for (x, y, sx, sy) in ((cx, hy0 + 0.02, hx1 - hx0, 0.04), (cx, hy1 - 0.02, hx1 - hx0, 0.04),
                           (hx0 + 0.02, cy, 0.04, hy1 - hy0), (hx1 - 0.02, cy, 0.04, hy1 - hy0)):
        b.box((x, y, FL0 - 0.076), (sx, sy, 0.03), "M_Hatch_Metal", bev=0, amp=0.0, cuts=0)  # pestana de apoyo (la tapa descansa encima)
    b.finish(cU)

    def lid(b):  # local: bisagra en el origen, la tapa se extiende hacia -y (cara superior de la tapa en z=0; el labio del marco sube a z=0.02)
        w, d = hx1 - hx0 - 0.02, hy1 - hy0 - 0.02
        hm, br = "M_Hatch_Metal", "M_Museum_Brass"
        for k in range(3):   # tablones de madera con canto biselado y una junta entre ellos
            b.box((-w / 2 + w / 6 + k * w / 3, -d / 2, -0.03), (w / 3 - 0.01, d, 0.06), "M_Museum_WoodDark", bev=0.01, amp=0.004, cuts=1)
        for yy in (-0.18, -d + 0.18):   # flejes de acero con remaches
            b.box((0, yy, 0.005), (w - 0.04, 0.06, 0.012), hm, bev=0.003, amp=0.002, cuts=0)
            for xx in [-w / 2 + 0.05 + q * (w - 0.1) / 7 for q in range(8)]:
                b.cyl((xx, yy, 0.0125), 0.0075, 0.006, br, seg=8, bev=0, amp=0.0)
        # dos bisagras de piano con nudillos alternos y pasador, y sus placas atornilladas (tapa y labio del marco)
        for xx in (-w / 2 + 0.15, w / 2 - 0.15):
            for kn in range(5):
                b.cyl((xx - 0.05 + 0.025 + kn * 0.02, 0.0, 0.011), 0.0105, 0.0196, hm if kn % 2 == 0 else br, rot=(0, 90, 0), seg=10, bev=0, amp=0.0)
            b.box((xx, -0.052, 0.0035), (0.1, 0.09, 0.005), hm, bev=0.002, amp=0.0, cuts=0)            # placa en la tapa
            b.box((xx, 0.055, 0.022), (0.1, 0.09, 0.005), hm, bev=0.002, amp=0.0, cuts=0)              # placa sobre el labio del marco
            for (sx_, sy_, zz_) in ((-0.035, -0.08, 0.006), (0.035, -0.08, 0.006), (-0.035, 0.08, 0.0245), (0.035, 0.08, 0.0245)):
                b.cyl((xx + sx_, sy_, zz_), 0.0055, 0.004, br, seg=8, bev=0, amp=0.0)
        # tirador de anilla abatible en un cajeado de laton (a ras de la tapa)
        hy = -d + 0.13
        b.box((0, hy, 0.0035), (0.15, 0.15, 0.005), br, bev=0.004, amp=0.0, cuts=0)                     # placa del cajeado
        b.box((0, hy, 0.0065), (0.11, 0.11, 0.002), "M_Floor_Dark", bev=0, amp=0.0, cuts=0)           # fondo oscuro del hueco
        tube(b, [(0.034 * math.cos(q * math.tau / 20), hy + 0.034 * math.sin(q * math.tau / 20), 0.0105) for q in range(20)], 0.0042, br, seg=8, closed=True)   # anilla
        b.box((0, hy - 0.056, 0.0085), (0.042, 0.016, 0.006), br, bev=0.002, amp=0.0, cuts=0)         # charnela de la anilla
        for sx_ in (-0.062, 0.062):
            for sy_ in (-0.062, 0.062):
                b.cyl((sx_, hy + sy_, 0.0075), 0.006, 0.004, br, seg=8, bev=0, amp=0.0)
    # el marco sigue la deformacion (warp) de la arquitectura; la tapa es un prop: se desplaza igual que el centro del hueco
    wv = L.warp(Vector((cx, cy, FL0))) - Vector((cx, cy, FL0))
    ob = prop("Hatch_Lid", (cx + wv.x, hy1 - 0.01 + wv.y, FL0 + wv.z), 0, lid)
    to_col(ob, cU)

    # SIN sotano modelado: en el juego la escotilla es un punto de interaccion (teletransporte al sotano).
    # Solo un fondo oscuro poco profundo bajo el hueco para que no se vea el vacio si se abre la tapa.
    b = B("Hatch_Pit", 0.5)
    for (x, y, sx, sy) in ((cx, hy0 - 0.03, hx1 - hx0 + 0.06, 0.06), (cx, hy1 + 0.03, hx1 - hx0 + 0.06, 0.06),
                           (hx0 - 0.03, cy, 0.06, hy1 - hy0), (hx1 + 0.03, cy, 0.06, hy1 - hy0)):
        b.box((x, y, 0.2 - 0.25), (sx, sy, 0.5), "M_Floor_Dark", bev=0, amp=0.0, cuts=0)
    b.box((cx, cy, -0.32), (hx1 - hx0 + 0.12, hy1 - hy0 + 0.12, 0.04), "M_Floor_Dark", bev=0, amp=0.0, cuts=0)
    b.finish(cU)


# ======================================================================= props (coordenadas locales, base z=0, frente hacia -y)
def bench_gallery(b, ln=1.5, cushion="M_Fabric_Olive"):
    """Banco clasico de galeria: cuatro patas torneadas (pie, anillos, huso con vientre, collarin y bloque de ensamble), cenefa y travesanos
    redondos, tablero de asiento y cojin tapizado de cantos redondeados con vivo (cordon dorado) arriba y abajo. Asiento a 0.50 m."""
    wd = "M_Museum_WoodDark"
    leg = [(0.0, 0.020), (0.006, 0.0235), (0.014, 0.0235), (0.024, 0.0165), (0.05, 0.0135), (0.066, 0.0165), (0.074, 0.0225), (0.082, 0.0165), (0.094, 0.0135),
           (0.16, 0.0145), (0.24, 0.0195), (0.282, 0.0185), (0.30, 0.0145), (0.312, 0.0225), (0.322, 0.0225), (0.332, 0.0175)]
    ex, ey = ln / 2 - 0.1, 0.15
    for sx in (-1, 1):
        for sy in (-1, 1):
            loft(b, [(z, r, r, 0.0) for (z, r) in leg], wd, seg=10, xf=Matrix.Translation((sx * ex, sy * ey, 0.0)), raw=True)
            b.box((sx * ex, sy * ey, 0.3575), (0.046, 0.046, 0.055), wd, bev=0.004, amp=0.0, cuts=0)             # bloque de ensamble (sube hasta el tablero)
    for sy in (-1, 1):   # cenefa: dos largueros entre bloques (a ras de su cara exterior) y dos cabeceros
        b.box((0, sy * (ey + 0.0105), 0.3575), (2 * ex - 0.044, 0.025, 0.055), wd, bev=0.003, amp=0.0, cuts=0)
    for sx in (-1, 1):
        b.box((sx * (ex + 0.0105), 0, 0.3575), (0.025, 2 * ey - 0.044, 0.055), wd, bev=0.003, amp=0.0, cuts=0)
    for sx in (-1, 1):   # travesanos redondos a la altura de los anillos, y uno largo central
        b.seg((sx * ex, -ey, 0.1), (sx * ex, ey, 0.1), 0.009, wd, seg=12)
    b.seg((-ex, 0, 0.1), (ex, 0, 0.1), 0.0095, wd, seg=12)
    rbox(b, (0, 0, 0.4), (ln - 0.04, 0.4, 0.03), 0.007, wd, segs=2)                                           # tablero (z 0.385 - 0.415)
    zc = 0.415 + 0.0425
    rbox(b, (0, 0, zc), (ln - 0.08, 0.37, 0.085), 0.028, cushion, segs=3)                                    # cojin (z 0.415 - 0.50)
    hw, hh = (ln - 0.08) / 2 - 0.0085, 0.37 / 2 - 0.0085
    for zz in (0.5 - 0.0085, 0.415 + 0.0085):                                                                 # vivos del cojin (arriba y abajo)
        path = [(x_, y_, zz) for (x_, y_) in rrect(hw, hh, 0.022, 3)]
        tube(b, path, 0.0052, "M_Rug_Gold", seg=5, closed=True)


def _ring(b, w, h, io, lw, d, mat, bev=0.008):
    """Moldura rectangular alrededor de un hueco w x h (io = separacion interior, lw = ancho, d = profundidad desde la pared):
    UNA sola malla con las esquinas a inglete (sin juntas a tope) y el bisel continuo por todo el perimetro."""
    a, c = w / 2 + io, h / 2 + io
    A, C = a + lw, c + lw
    bm = bmesh.new()
    rings = {}
    for nm, (hx, hz) in (("o", (A, C)), ("i", (a, c))):
        for y in (0.0, -d):
            rings[(nm, y)] = [bm.verts.new(q) for q in ((-hx, y, -hz), (hx, y, -hz), (hx, y, hz), (-hx, y, hz))]
    for k in range(4):
        k2 = (k + 1) % 4
        for y in (0.0, -d):   # cara frontal y trasera (4 trapecios a inglete)
            bm.faces.new((rings[("o", y)][k], rings[("o", y)][k2], rings[("i", y)][k2], rings[("i", y)][k]))
        for nm in ("o", "i"):   # cantos exterior e interior
            bm.faces.new((rings[(nm, 0.0)][k], rings[(nm, 0.0)][k2], rings[(nm, -d)][k2], rings[(nm, -d)][k]))
    b._finish(bm, (0, 0, 0), (0, 0, 0), mat, bev, 0.0, lw)


PAINT_SKY = ("M_Paint_Sky", "M_Paint_Cream", "M_Paint_Rose", "M_Paint_Sky")
PAINT_LAND = ("M_Paint_Field", "M_Paint_Green", "M_Paint_Ochre")


def placeholder(b, w, h, yf, seed, kind=None, zc=0.0):
    """LIENZO DE PRUEBA: manchas planas de color delante del lienzo (materiales M_Paint_*). Provisional:
    al poner las obras reales se borran esas caras y queda M_Canvas_Slot. zc = desplazamiento en z de todo lo generado."""
    r = random.Random(seed)
    hw, hh = w / 2 - 0.004, h / 2 - 0.004

    def rect(x0, z0, x1, z1, m, k=0, rot=0.0):
        x0, x1, z0, z1 = max(x0, -hw), min(x1, hw), max(z0, -hh), min(z1, hh)
        if x1 - x0 > 0.004 and z1 - z0 > 0.004:
            b.box(((x0 + x1) / 2, yf - 0.001 - 0.0012 * k, (z0 + z1) / 2 + zc), (x1 - x0, 0.002, z1 - z0), m, rot=(0, rot, 0), bev=0, amp=0.0, cuts=0)

    def poly(pts, m, k=1):
        b.prism([(x, yf - 0.001 - 0.0012 * k, z + zc) for (x, z) in pts], (0, -0.002, 0), m, amp=0.0)

    def disc(x, z, rr, m, k=1, sq=1.0):
        poly([(x + rr * math.cos(t * math.tau / 18), z + rr * sq * math.sin(t * math.tau / 18)) for t in range(18)], m, k)
    m_ = min(w, h)
    kind = kind or r.choice(("land", "land", "still", "portrait", "abstract"))
    if kind == "grey":     # la obra clave: campo gris bajo un cielo casi gris, una flor amarilla pequena
        hz = -hh + h * 0.4
        rect(-hw, hz, hw, hh, "M_Paint_GreySky")
        rect(-hw, -hh, hw, hz, "M_Paint_GreyField")
        for k in range(7):   # cielo en bandas, sin color
            zz = hz + (hh - hz) * (0.2 + 0.11 * k)
            rect(-hw + w * 0.05 * (k % 3), zz - 0.006, hw - w * 0.06 * ((k + 1) % 3), zz + 0.006, "M_Paint_GreyField" if k % 2 else "M_Paint_Deep", 1, rot=r.uniform(-4, 4))
        for k in range(6):
            zz = -hh + (hz + hh) * (0.15 + 0.13 * k)
            rect(-hw, zz - 0.004, hw, zz + 0.004, "M_Paint_GreySky", 1, rot=r.uniform(-2, 2))
        fx, fz = hw * 0.32, -hh + h * 0.2
        rect(fx - 0.003, fz - h * 0.12, fx + 0.003, fz, "M_Paint_Green", 2)
        for t in range(6):
            a = t * math.tau / 6
            disc(fx + m_ * 0.016 * math.cos(a), fz + m_ * 0.016 * math.sin(a), m_ * 0.012, "M_Flower_Yellow", 3)
        disc(fx, fz, m_ * 0.009, "M_Paint_Ochre", 4)
        return
    if kind == "land":
        hz = -hh + h * r.uniform(0.35, 0.55)
        rect(-hw, hz, hw, hh, r.choice(PAINT_SKY))
        rect(-hw, -hh, hw, hz, r.choice(PAINT_LAND))
        disc(r.uniform(-hw * 0.6, hw * 0.6), hz + (hh - hz) * 0.55, m_ * 0.07, "M_Paint_Ochre", 1)
        for k in range(5):
            zz = -hh + (hz + hh) * (0.12 + 0.17 * k)
            rect(-hw * r.uniform(0.6, 1), zz - 0.006, hw * r.uniform(0.3, 1), zz + 0.006, r.choice(PAINT_LAND), 1, rot=r.uniform(-6, 6))
        for k in range(r.randint(1, 2)):   # cipreses
            cx_, ch = r.uniform(-hw * 0.7, hw * 0.7), h * r.uniform(0.3, 0.5)
            poly([(cx_ - m_ * 0.035, hz - h * 0.05), (cx_ + m_ * 0.035, hz - h * 0.05), (cx_ + m_ * 0.01, min(hz + ch, hh)), (cx_ - m_ * 0.01, min(hz + ch, hh))], "M_Paint_Deep", 2)
    elif kind == "still":
        tz = -hh + h * 0.3
        rect(-hw, -hh, hw, hh, r.choice(("M_Paint_Deep", "M_Paint_Cream", "M_Paint_Green")))
        rect(-hw, -hh, hw, tz, "M_Paint_Ochre", 1)
        vx = r.uniform(-hw * 0.3, hw * 0.1)
        poly([(vx - m_ * 0.08, tz), (vx + m_ * 0.08, tz), (vx + m_ * 0.11, tz + h * 0.25), (vx + m_ * 0.05, tz + h * 0.42), (vx - m_ * 0.05, tz + h * 0.42), (vx - m_ * 0.11, tz + h * 0.25)], "M_Paint_Sky", 2)
        for k in range(3):
            disc(vx + m_ * (0.22 + 0.13 * k), tz + m_ * 0.07, m_ * 0.06, r.choice(("M_Paint_Rose", "M_Paint_Ochre", "M_Paint_Field")), 3)
    elif kind == "portrait":
        rect(-hw, -hh, hw, hh, r.choice(("M_Paint_Deep", "M_Paint_Green")))
        poly([(-hw * 0.75, -hh), (hw * 0.75, -hh), (hw * 0.45, -hh + h * 0.3), (-hw * 0.45, -hh + h * 0.3)], r.choice(("M_Paint_Rose", "M_Paint_Sky")), 1)
        disc(0, -hh + h * 0.52, m_ * 0.17, "M_Paint_Cream", 2, sq=1.3)
    else:
        rect(-hw, -hh, hw, hh, "M_Paint_Cream")
        for k in range(4):
            x0_, z0_ = r.uniform(-hw, hw * 0.3), r.uniform(-hh, hh * 0.3)
            rect(x0_, z0_, x0_ + w * r.uniform(0.25, 0.5), z0_ + h * r.uniform(0.25, 0.5), r.choice(PAINT_SKY + PAINT_LAND + ("M_Paint_Deep",)), k + 1)
        disc(r.uniform(-hw * 0.5, hw * 0.5), r.uniform(-hh * 0.5, hh * 0.5), m_ * 0.1, "M_Paint_Rose", 5)


ART_WALL = []   # (eje, cara, u, ancho, zc, alto, sentido de la cartela) de cada cuadro: las cortinas dejan sitio a los cuadros vecinos


def art_slot(name, axis, face, s, u, zc, w, h, frame="M_Frame_Gold", parent=None):
    """Hueco para obra: marco moldurado + lienzo (M_Canvas_Slot) con lienzo de prueba delante + cartela.
    Pivote en el centro, contra la pared. Marcos: dorado (escalonado con rosetas), madera oscura, plata (con paspartu)."""
    def fn(b):
        mat_border = 0.0
        if frame == "M_Frame_Silver" or w * h < 0.4:
            mat_border = max(0.05, 0.09 * min(w, h))
        pw, ph = w - 2 * mat_border, h - 2 * mat_border
        if mat_border:
            b.box((0, -0.02, 0), (w, 0.028, h), "M_Paper", bev=0, amp=0.0, cuts=0)                 # paspartu
        b.box((0, -0.024, 0), (pw, 0.03, ph), "M_Canvas_Slot", bev=0, amp=0.0, cuts=1)
        placeholder(b, pw, ph, -0.039, sum(ord(ch) * (i + 1) for i, ch in enumerate(name)), "grey" if "GreyField" in name else None)
        if frame == "M_Frame_Gold":
            fw = 0.1 if w > 1.2 else 0.08
            _ring(b, w, h, 0.0, fw, 0.045, frame)                       # plano exterior
            _ring(b, w, h, fw * 0.25, fw * 0.45, 0.07, frame, 0.012)      # moldura alta
            _ring(b, w, h, 0.0, 0.016, 0.058, frame, 0.005)               # junquillo junto al lienzo
            for sx in (-1, 1):
                for sz in (-1, 1):   # rosetas en las esquinas
                    b.cyl((sx * (w / 2 + fw / 2), -0.074, sz * (h / 2 + fw / 2)), fw * 0.3, 0.012, frame, rot=(90, 0, 0), seg=10, bev=0, amp=0.0)
                    b.cyl((sx * (w / 2 + fw / 2), -0.082, sz * (h / 2 + fw / 2)), fw * 0.14, 0.008, frame, rot=(90, 0, 0), seg=8, bev=0, amp=0.0)
        elif frame == "M_Frame_Silver":
            fw = 0.035
            _ring(b, w, h, 0.0, fw, 0.04, frame, 0.006)
            _ring(b, w, h, 0.0, 0.012, 0.052, frame, 0.003)                  # filete interior en relieve
        else:
            fw = 0.075 if w > 1.2 else 0.06
            _ring(b, w, h, 0.0, fw, 0.05, frame, 0.01)
            _ring(b, w, h, fw * 0.3, fw * 0.4, 0.066, "M_Museum_WoodDark", 0.01)   # escalon alto de la moldura
            _ring(b, w, h, 0.0, 0.018, 0.04, "M_Museum_Wood", 0.004)     # filete interior mas claro
        lx = w / 2 + fw + 0.13
        b.box((lx, -0.006, -h / 2 + 0.06), (0.16, 0.012, 0.11), "M_Paper", bev=0.003, amp=0.0, cuts=0)    # cartela
        for k, ln in enumerate((0.11, 0.12, 0.07)):   # lineas que sugieren texto (sin texto real pequeno)
            b.box((lx - (0.12 - ln) / 2 - 0.01, -0.0125, -h / 2 + 0.085 - k * 0.022), (ln, 0.001, 0.007), "M_Floor_Dark", bev=0, amp=0.0, cuts=0)
    rot = {('x', 1): 180, ('x', -1): 0, ('y', 1): 90, ('y', -1): -90}[(axis, s)]
    pos = (u, face, zc) if axis == 'x' else (face, u, zc)
    ART_WALL.append((axis, face, u, w, zc, h, 1 if (axis, s) in (('x', -1), ('y', 1)) else -1))
    ob = prop("ArtSlot_" + name, pos, rot, fn)
    return to_col(ob, parent) if parent else ob


def pedestal(b, h=1.0, w=0.5, top=True):
    """Pedestal clasico: zocalo escalonado, fuste con cuarterones en las 4 caras y cornisa moldurada. Tapa en z=h."""
    wd = "M_Museum_WoodDark"
    b.box((0, 0, 0.03), (w + 0.12, w + 0.12, 0.06), wd, bev=0.01, amp=0.0, cuts=0)
    b.box((0, 0, 0.09), (w + 0.06, w + 0.06, 0.06), wd, bev=0.008, amp=0.0, cuts=0)
    b.box((0, 0, (0.12 + h - 0.1) / 2), (w, w, h - 0.22), "M_Interior_Ceiling", bev=0.008, amp=0.002, cuts=1)
    pw, z0, z1 = w - 0.12, 0.2, h - 0.18
    for k in range(4):   # cuarterones: marco fino en relieve en cada cara
        a = k * math.pi / 2
        n, t = Vector((math.cos(a), math.sin(a), 0)), Vector((-math.sin(a), math.cos(a), 0))
        o = n * (w / 2 + 0.004)
        for sg in (-1, 1):
            b.box(tuple(o + t * sg * pw / 2 + Vector((0, 0, (z0 + z1) / 2))), (0.008, 0.02, z1 - z0) if k % 2 == 0 else (0.02, 0.008, z1 - z0), wd, bev=0, amp=0.0, cuts=0)
        for zz in (z0, z1):
            b.box(tuple(o + Vector((0, 0, zz))), (0.008, pw + 0.02, 0.02) if k % 2 == 0 else (pw + 0.02, 0.008, 0.02), wd, bev=0, amp=0.0, cuts=0)
    b.box((0, 0, h - 0.085), (w + 0.03, w + 0.03, 0.03), wd, bev=0.006, amp=0.0, cuts=0)      # cuello
    b.box((0, 0, h - 0.045), (w + 0.08, w + 0.08, 0.05), wd, bev=0.012, amp=0.0, cuts=0)      # cornisa
    if top:
        b.box((0, 0, h - 0.01), (w + 0.12, w + 0.12, 0.02), wd, bev=0.006, amp=0.0, cuts=0)   # tapa: misma proyeccion que el zocalo



def vitrine(b):
    """Urna sobre pedestal: plataforma, marco inferior y superior de laton del mismo tamano y cuatro montantes cuadrados que encajan exactos
    entre ambos marcos; el cristal ocupa justo el hueco entre montantes y marcos."""
    pedestal(b, 0.9, 0.7)                                                                      # tapa del pedestal: z 0.88..0.90 (0.82 de lado)
    b.box((0, 0, 0.915), (0.76, 0.76, 0.03), "M_Museum_WoodDark", bev=0.008, amp=0.0, cuts=0)     # plataforma 0.90..0.93
    zb, zt = 0.95, 1.42                                                                         # entre el marco inferior (0.93..0.95) y el superior (1.42..1.45)
    b.box((0, 0, 0.94), (0.72, 0.72, 0.02), "M_Museum_Brass", bev=0.004, amp=0.0, cuts=0)
    b.box((0, 0, 1.435), (0.72, 0.72, 0.03), "M_Museum_Brass", bev=0.006, amp=0.0, cuts=0)
    b.box((0, 0, (zb + zt) / 2), (0.682, 0.682, zt - zb), "M_Vitrine_Glass", bev=0, amp=0, cuts=0)
    for sx in (-0.341, 0.341):
        for sy in (-0.341, 0.341):
            b.box((sx, sy, (zb + zt) / 2), (0.026, 0.026, zt - zb), "M_Museum_Brass", bev=0.003, amp=0.0, cuts=0)
    b.box((0, 0, 0.965), (0.5, 0.35, 0.03), "M_Rug_Terracotta", bev=0.01, amp=0.002, cuts=0)    # cojin de exposicion sobre el marco inferior


def stanchions(b, ln=2.0):
    """Postes de laton torneados (pie abombado, fuste, remate en loft) unidos por una cuerda con ojales de laton."""
    br = "M_Museum_Brass"
    foot = [(0.0, 0.13), (0.005, 0.13), (0.014, 0.122), (0.026, 0.095), (0.036, 0.055), (0.044, 0.032), (0.052, 0.0265)]
    fin = [(0.918, 0.0255), (0.925, 0.03), (0.931, 0.0335), (0.939, 0.0335), (0.945, 0.026), (0.953, 0.020), (0.963, 0.027), (0.976, 0.0375),
           (0.990, 0.0405), (1.002, 0.034), (1.011, 0.020), (1.017, 0.008), (1.0195, 0.002)]
    for x in (-ln / 2, 0, ln / 2):
        T = Matrix.Translation((x, 0, 0))
        loft(b, [(z, r, r, 0.0) for (z, r) in foot], br, seg=32, xf=T)
        b.cyl((x, 0, 0.48), 0.025, 0.92, br, seg=28, bev=0, amp=0.0)
        loft(b, [(z, r, r, 0.0) for (z, r) in fin], br, seg=32, xf=T)
        for zz in (0.86,):   # ojal de laton que sujeta la cuerda
            tube(b, [Vector((x + 0.0285 * math.cos(a_), 0.0285 * math.sin(a_), zz)) for a_ in [math.tau * q / 20 for q in range(20)]], 0.0035, br, seg=8, closed=True)
    # cuerda de terciopelo con terminales de laton: casquillo + mosqueton (anilla que abraza el ojal del poste)
    rr_ = 0.0145            # radio de la anilla del mosqueton
    for x0 in (-ln / 2, 0):
        xa, xb = x0 + 0.0725, x0 + ln / 2 - 0.0725            # extremos de la cuerda (metidos 2 cm dentro de los casquillos)
        for (xe, sg) in ((x0, 1), (x0 + ln / 2, -1)):
            xc_ = xe + sg * (0.0285 + 0.006)                                  # centro de la anilla (el ojal del poste pasa por dentro)
            tube(b, [(xc_ + rr_ * math.cos(a_), 0.0, 0.86 + rr_ * math.sin(a_)) for a_ in [math.tau * q / 16 for q in range(16)]], 0.0025, br, seg=6, closed=True)
            xf_ = xc_ + sg * (rr_ + 0.0025)                                   # casquillo cilindrico sobre la cuerda, pegado a la anilla
            b.cyl((xf_ + sg * 0.012, 0.0, 0.86), 0.0215, 0.024, br, rot=(0, 90, 0), seg=14, bev=0, amp=0.0)
        pts = [Vector((xa + 0.0, 0, 0.86))] + [Vector((xa + (xb - xa) * k / 12, 0, 0.86 - 0.13 * math.sin(math.pi * k / 12))) for k in range(1, 12)] + [Vector((xb, 0, 0.86))]
        tube(b, pts, 0.018, "M_Rug_Terracotta", seg=12)


def loft(b, rings, mat, seg=20, closed=False, cap_bottom=True, cap_top=True, smooth=True, xf=None, raw=False):
    """Superficie de revolucion elíptica: rings = [(z, rx, ry, cy)], cada anillo es una elipse a altura z centrada en (0, cy).
    closed=True une el último anillo con el primero (perfil tipo toro); si no, tapas opcionales. xf = Matrix opcional aplicada a los vértices."""
    mr = max(max(r[1], r[2]) for r in rings)
    if not raw:   # raw=True respeta `seg` tal cual (columnas de radiador, muchas copias)
        seg = max(seg, 16 if mr >= 0.04 else 8)
    bm = bmesh.new()
    rv = []
    for (z, rx, ry, cy) in rings:
        rv.append([bm.verts.new((rx * math.cos(k * math.tau / seg), cy + ry * math.sin(k * math.tau / seg), z)) for k in range(seg)])
    n = len(rv)
    for i in range(n if closed else n - 1):
        a, c = rv[i], rv[(i + 1) % n]
        for k in range(seg):
            bm.faces.new((a[k], a[(k + 1) % seg], c[(k + 1) % seg], c[k]))
    if not closed:
        if cap_bottom:
            bm.faces.new(rv[0][::-1])
        if cap_top:
            bm.faces.new(rv[-1])
    if xf is not None:
        bmesh.ops.transform(bm, matrix=xf, verts=bm.verts)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    if smooth:
        b._finish(bm, (0, 0, 0), (0, 0, 0), mat, 0, 0, 1)
    else:
        b._push(bm, mat)


def tube(b, pts, r, mat, seg=8, closed=False, cap=True):
    """Tubo continuo: barre un círculo de radio r (seg lados) a lo largo de la polilínea pts con marcos de transporte paralelo.
    r puede ser un float o una lista con un radio por punto (afilado). closed=True cierra el aro (toro); si el último punto
    repite el primero se descarta. Si no es cerrado y cap=True, tapa ambos extremos."""
    P = [Vector(p) for p in pts]
    rads = list(r) if isinstance(r, (list, tuple)) else [r] * len(P)
    seg = max(seg, 16 if max(rads) >= 0.02 else (8 if max(rads) >= 0.012 else seg))
    if closed and len(P) > 2 and (P[0] - P[-1]).length < 1e-6:
        P.pop()
        rads = rads[:len(P)]
    n = len(P)
    if n < 2:
        return

    def tan(i):
        if closed:
            d = P[(i + 1) % n] - P[(i - 1) % n]
        else:
            d = P[min(i + 1, n - 1)] - P[max(i - 1, 0)]
        return d.normalized()

    T = [tan(i) for i in range(n)]
    ref = Vector((1, 0, 0)) if abs(T[0].z) > 0.9 else Vector((0, 0, 1))   # evita la tangente paralela a Z
    nrm = T[0].cross(ref).normalized()
    bm = bmesh.new()
    rv = []
    for i in range(n):
        if i > 0:
            nrm = (T[i - 1].rotation_difference(T[i]) @ nrm).normalized()
        bin_ = T[i].cross(nrm).normalized()
        rv.append([bm.verts.new(P[i] + (nrm * math.cos(k * math.tau / seg) + bin_ * math.sin(k * math.tau / seg)) * rads[i]) for k in range(seg)])
    for i in range(n if closed else n - 1):
        a, c = rv[i], rv[(i + 1) % n]
        for k in range(seg):
            bm.faces.new((a[k], a[(k + 1) % seg], c[(k + 1) % seg], c[k]))
    if not closed and cap:
        bm.faces.new(rv[0][::-1])
        bm.faces.new(rv[-1])
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    b._finish(bm, (0, 0, 0), (0, 0, 0), mat, 0, 0, 1)


def rbox(b, c, size, rad, mat, segs=3, rot=(0, 0, 0)):
    """Caja de cantos redondeados (bisel de `segs` segmentos en TODAS las aristas): cojines, tapas, losas de piedra suaves.
    Solo para B/HB reales (no para Sh)."""
    bm = bmesh.new()
    bmesh.ops.create_cube(bm, size=1.0)
    for v in bm.verts:
        v.co.x *= size[0]; v.co.y *= size[1]; v.co.z *= size[2]
    bmesh.ops.bevel(bm, geom=bm.edges[:], offset=min(rad, min(size) * 0.45), segments=segs, affect='EDGES')
    b._finish(bm, c, rot, mat, 0, 0.0, min(size))


def rrect(hw, hh, r, n=4):
    """Contorno de rectangulo redondeado (semiancho hw, semialto hh, radio r, n puntos por esquina) como lista (u, v) antihoraria."""
    r = min(r, hw, hh)
    pts = []
    for (cx, cy, a0) in ((hw - r, hh - r, 0.0), (-hw + r, hh - r, 90.0), (-hw + r, -hh + r, 180.0), (hw - r, -hh + r, 270.0)):
        for k in range(n + 1):
            a = math.radians(a0 + 90.0 * k / n)
            pts.append((cx + r * math.cos(a), cy + r * math.sin(a)))
    return pts


def sweep(b, pts, cross, mat, sc=None, closed=False, cap=True, side=None):
    """Barrido de un contorno 2D `cross` [(u, v)] a lo largo de la polilinea `pts` con marcos de transporte paralelo.
    sc = lista (su, sv) por punto (escala del contorno); side = direccion de referencia del eje u en el primer punto."""
    P = [Vector(p) for p in pts]
    n = len(P)
    if n < 2:
        return

    def tan(i):
        d = (P[(i + 1) % n] - P[(i - 1) % n]) if closed else (P[min(i + 1, n - 1)] - P[max(i - 1, 0)])
        return d.normalized()
    T = [tan(i) for i in range(n)]
    ref = Vector(side) if side is not None else (Vector((1, 0, 0)) if abs(T[0].z) > 0.9 else Vector((0, 0, 1)))
    nrm = (ref - T[0] * ref.dot(T[0])).normalized()
    bm = bmesh.new()
    rv = []
    m = len(cross)
    for i in range(n):
        if i > 0:
            nrm = (T[i - 1].rotation_difference(T[i]) @ nrm).normalized()
        bn = T[i].cross(nrm).normalized()
        su, sv = (sc[i] if sc else (1.0, 1.0))
        rv.append([bm.verts.new(P[i] + nrm * (u * su) + bn * (v * sv)) for (u, v) in cross])
    for i in range(n if closed else n - 1):
        a, c = rv[i], rv[(i + 1) % n]
        for k in range(m):
            bm.faces.new((a[k], a[(k + 1) % m], c[(k + 1) % m], c[k]))
    if not closed and cap:
        bm.faces.new(rv[0][::-1])
        bm.faces.new(rv[-1])
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    b._finish(bm, (0, 0, 0), (0, 0, 0), mat, 0, 0, 1)


def twisted(b, outline, z0, z1, n, twist, mat, scale=None, center=None):
    """Columna retorcida de seccion constante (o variable): `outline` [(x, y)] girado `twist` grados de z0 a z1 en n pasos; scale(t) y
    center(t) -> (cx, cy) opcionales. Tapas planas arriba y abajo."""
    bm = bmesh.new()
    rv = []
    for i in range(n + 1):
        t = i / n
        a = math.radians(twist * t)
        ca, sa = math.cos(a), math.sin(a)
        s = scale(t) if scale else 1.0
        cx, cy = center(t) if center else (0.0, 0.0)
        rv.append([bm.verts.new((cx + s * (x * ca - y * sa), cy + s * (x * sa + y * ca), z0 + (z1 - z0) * t)) for (x, y) in outline])
    m = len(outline)
    for i in range(n):
        for k in range(m):
            bm.faces.new((rv[i][k], rv[i][(k + 1) % m], rv[i + 1][(k + 1) % m], rv[i + 1][k]))
    bm.faces.new(rv[0][::-1])
    bm.faces.new(rv[-1])
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    b._finish(bm, (0, 0, 0), (0, 0, 0), mat, 0, 0, 1)


def smooth_prof(pts, sub=4):
    """Catmull-Rom por puntos (z, r): perfil suave de piezas torneadas. Los extremos se duplican (no se pasan de largo)."""
    P = [Vector(p) for p in pts]
    Q = [P[0]] + P + [P[-1]]
    out = [tuple(P[0])]
    for i in range(1, len(Q) - 2):
        p0, p1, p2, p3 = Q[i - 1], Q[i], Q[i + 1], Q[i + 2]
        for k in range(1, sub + 1):
            t = k / sub
            q = 0.5 * ((2 * p1) + (-p0 + p2) * t + (2 * p0 - 5 * p1 + 4 * p2 - p3) * t * t + (-p0 + 3 * p1 - 3 * p2 + p3) * t ** 3)
            out.append((q.x, max(q.y, 0.0005)))
    return out


def arc_band(b, c, axis, R, th, a0, a1, ln, mat, n=14):
    """Franja curva (tubo abierto de pared fina th) de radio exterior R entre los angulos a0..a1 (grados) en el plano perpendicular a `axis`
    ('x' o 'y'), de longitud ln centrada en c. En el plano: angulo 0 = +horizontal (y para axis 'x', x para axis 'y'), 90 = +z."""
    pts = []
    for (rr, order) in ((R, 1), (R - th, -1)):
        seq = [math.radians(a0 + (a1 - a0) * k / n) for k in range(n + 1)]
        for a in (seq if order == 1 else seq[::-1]):
            pts.append((rr * math.cos(a), rr * math.sin(a)))
    if axis == 'x':
        P3 = [(c[0] - ln / 2, c[1] + u, c[2] + v) for (u, v) in pts]
        ext = (ln, 0, 0)
    else:
        P3 = [(c[0] + u, c[1] - ln / 2, c[2] + v) for (u, v) in pts]
        ext = (0, ln, 0)
    b.prism(P3, ext, mat, amp=0.0)


# ----------------------------------------------------------------------- plantas de interior
# Hojas como laminas CON grosor (malla de nodos s x w, con celdas retiradas para las hendiduras), nervio central en relieve y peciolo
# que nace SOBRE la superficie del tallo y termina exactamente donde empieza la lamina.
Z_UP = Vector((0, 0, 1))


def grid_solid(b, P, mat, th, keep=None, toward=None, mat_fn=None):
    """Lamina con grosor a partir de nodos P[j][i] (j x i). keep(j, i) decide si la celda entre nodos (j..j+1, i..i+1) existe
    (permite recortes: hendiduras, agujeros). Cara frontal en P, cara trasera desplazada th (float o lista por fila j) a lo largo de la normal
    hacia 'toward', y cantos cerrados en todo el perimetro (incluido el de los recortes). mat_fn(j, i) -> material por celda."""
    nj, ni = len(P), len(P[0])
    ok = lambda j, i: 0 <= j < nj - 1 and 0 <= i < ni - 1 and (keep is None or keep(j, i))
    bm = bmesh.new()
    fv, bv = {}, {}
    thj = th if isinstance(th, (list, tuple)) else [th] * nj
    tw = Vector(toward) if toward is not None else None

    def vt(j, i):
        if (j, i) not in fv:
            fv[(j, i)] = bm.verts.new(P[j][i])
            du = P[j][min(i + 1, ni - 1)] - P[j][max(i - 1, 0)]
            dv = P[min(j + 1, nj - 1)][i] - P[max(j - 1, 0)][i]
            n = du.cross(dv)
            n = n.normalized() if n.length > 1e-12 else (tw if tw is not None else Z_UP)
            if tw is not None and n.dot(tw) < 0:
                n = -n
            bv[(j, i)] = bm.verts.new(P[j][i] + n * thj[j])
        return fv[(j, i)], bv[(j, i)]
    for j in range(nj - 1):
        for i in range(ni - 1):
            if not ok(j, i):
                continue
            m = b._mi(mat_fn(j, i) if mat_fn else mat)
            a, bb, c, d = vt(j, i), vt(j, i + 1), vt(j + 1, i + 1), vt(j + 1, i)
            fs = [bm.faces.new((a[0], bb[0], c[0], d[0])), bm.faces.new((a[1], d[1], c[1], bb[1]))]
            if not ok(j - 1, i):   # cantos: arriba, abajo, izquierda, derecha
                fs.append(bm.faces.new((a[0], a[1], bb[1], bb[0])))
            if not ok(j + 1, i):
                fs.append(bm.faces.new((d[0], c[0], c[1], d[1])))
            if not ok(j, i - 1):
                fs.append(bm.faces.new((a[0], d[0], d[1], a[1])))
            if not ok(j, i + 1):
                fs.append(bm.faces.new((bb[0], bb[1], c[1], c[0])))
            for f in fs:
                f.material_index = m
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    for f in bm.faces:
        f.smooth = True
    bm.to_mesh(b._tmp)
    bm.free()
    b.bm.from_mesh(b._tmp)
    b._tmp.clear_geometry()


def cloth(b, grid, th, mat, toward):
    """Tela de cortina/estor: lamina continua con grosor por fila."""
    grid_solid(b, grid, mat, th, toward=toward)


class LeafFrame:
    """Eje de una hoja: curva de la nervadura central (curvada por 'bend' radianes, + = cae) y marco local (lat = eje de curvatura, h = normal)."""

    def __init__(s, p0, d, L, up=Z_UP, roll=0.0, bend=0.0, steps=40):
        d = Vector(d).normalized()
        n = up - d * up.dot(d)
        if n.length < 1e-3:
            n = Vector((1, 0, 0)) - d * d.x
        n.normalize()
        side = d.cross(n)
        if roll:
            q = Quaternion(d, roll)
            n, side = q @ n, q @ side
        s.d, s.n, s.side, s.L, s.p0 = d, n, side, L, Vector(p0)
        s.tab = []
        C, prev = Vector(p0), None
        for k in range(steps + 1):
            u = k / steps
            q = Quaternion(side, -bend * u ** 1.4)
            T, N = q @ d, q @ n
            if prev is not None:
                C = C + (prev + T) * 0.5 * (L / steps)
            prev = T
            s.tab.append((C.copy(), T, N))
        s.steps = steps

    def place(s, along, lat, h):
        u = along / s.L
        if u <= 0.0:
            C, T, N = s.tab[0]
            return C + T * along + s.side * lat + N * h
        if u >= 1.0:
            C, T, N = s.tab[-1]
            return C + T * (along - s.L) + s.side * lat + N * h
        x = u * s.steps
        k = min(int(x), s.steps - 1)
        f = x - k
        C = s.tab[k][0].lerp(s.tab[k + 1][0], f)
        N = s.tab[k][2].lerp(s.tab[k + 1][2], f).normalized()
        return C + s.side * lat + N * h


def blade3d(b, p0, d, L, H, hwf, mat, up=Z_UP, roll=0.0, bend=0.0, fold=0.0, bow=0.0, wave=0.0, wave_n=4.0, wave_ph=0.0, back=0.0, shear=0.0,
            slits=(), w0=0.3, ns=24, nw=10, thick=0.003, rib=0.0035, rib_mat="M_Plant_LeafLight", lift=0.0, mat_fn=None, rib_n=14):
    """Hoja de largo L y semiancho maximo H cuyo contorno es H*hwf(s) (s: 0 base, 1 punta).
    fold: pliegue en V a lo largo del nervio (bordes mas bajos); bow: copa (bordes mas altos); wave: ondulacion del borde.
    back: lobulos de la base que se retrasan (hoja acorazonada); shear: hendiduras inclinadas hacia la punta.
    slits: (s_centro, semiancho_s, lado) recortes desde el borde hasta |w| = w0 (lado = -1, +1 o 0 para ambos).
    Devuelve el LeafFrame (para colocar cosas en la punta)."""
    fr = LeafFrame(p0, d, L, up, roll, bend)
    Sv = {round(k / ns, 5) for k in range(ns + 1)}
    for (sc, hw_, sd) in slits:
        Sv |= {round(max(0.0, sc - hw_), 5), round(min(1.0, sc + hw_), 5)}
    S = sorted(Sv)
    Wv = {round(-1 + 2 * k / nw, 5) for k in range(nw + 1)}
    if slits:
        Wv |= {round(w0, 5), round(-w0, 5)}
    W = sorted(Wv)

    def node(s, w):
        lat = w * H * max(hwf(s), 0.02)
        al = s * L + shear * L * abs(w) ** 1.2 * 4 * s * (1 - s) - back * abs(w) ** 1.5 * (1 - s) ** 1.2
        h = -fold * abs(lat) + bow * lat * lat / max(H, 1e-3) + wave * abs(w) ** 2 * math.sin(wave_n * math.tau * s + wave_ph) + lift
        return fr.place(al, lat, h)
    P = [[node(s, w) for w in W] for s in S]

    def keep(j, i):
        sm, wm = (S[j] + S[j + 1]) / 2, (W[i] + W[i + 1]) / 2
        for (sc, hw_, sd) in slits:
            if abs(sm - sc) < hw_ and abs(wm) > w0 and (sd == 0 or (wm > 0) == (sd > 0)):
                return False
        return True
    grid_solid(b, P, mat, thick, keep=keep if slits else None, toward=-fr.n, mat_fn=(lambda j, i: mat_fn(S[j], W[i])) if mat_fn else None)
    if rib > 0:
        ss = [k / rib_n for k in range(rib_n + 1)]
        pts = [fr.place(s * L, 0.0, rib * 0.35 + lift) for s in ss]
        tube(b, pts, [rib * (1 - 0.8 * s) for s in ss], rib_mat, seg=4)
    return fr


def _az(a, face, spread):
    """Comprime los acimuts de las hojas a un arco (face +- spread rad) para plantas junto a paredes y radiadores (face=None: sin limite)."""
    if face is None:
        return a
    d = (a - face + math.pi) % math.tau - math.pi
    return face + d * spread / math.pi


def _hw(keys):
    return lambda s: _keyed(s, keys)


def stalk(b, pts, r0, r1, mat, seg=10):
    """Tallo/peciolo ahusado (tubo) a lo largo de pts."""
    n = len(pts)
    tube(b, pts, [r0 + (r1 - r0) * k / (n - 1) for k in range(n)], mat, seg=seg)


def bezier(p0, p1, p2, n=12):
    return [(1 - t) ** 2 * Vector(p0) + 2 * (1 - t) * t * Vector(p1) + t * t * Vector(p2) for t in [k / n for k in range(n + 1)]]


def pot(b, r=0.2, h=0.42, seed=7):
    """Maceta de terracota ahusada con borde enrollado, plato, tierra abombada y unas piedrecitas planas.
    Devuelve la z de la superficie de la tierra (donde nacen los tallos). Apoya en z = 0."""
    rnd = random.Random(seed)
    R, H = r, h
    zb = 0.012                                   # suelo del plato: el pie de la maceta apoya aqui
    saucer = [(0.0, 0.70 * R), (0.0, 0.74 * R), (0.004, 0.80 * R), (0.016, 1.10 * R), (0.026, 1.15 * R), (0.031, 1.15 * R), (0.034, 1.13 * R),
              (0.031, 1.10 * R), (0.016, 1.04 * R), (zb - 0.002, 0.74 * R), (zb, 0.70 * R)]
    loft(b, [(z, r_, r_, 0.0) for (z, r_) in saucer], "M_Pot", seg=18, cap_bottom=True, cap_top=True)
    wall = [(zb, 0.60 * R), (zb + 0.006, 0.66 * R), (zb + H * 0.62, 0.84 * R), (zb + H * 0.86, 0.96 * R), (zb + H * 0.88, 0.995 * R),
            (zb + H * 0.905, 1.06 * R), (zb + H * 0.955, 1.095 * R), (zb + H, 1.075 * R), (zb + H + 0.004, 1.03 * R), (zb + H, 0.98 * R),
            (zb + H * 0.93, 0.92 * R), (zb + H * 0.80, 0.905 * R)]
    loft(b, [(z, r_, r_, 0.0) for (z, r_) in wall], "M_Pot", seg=18, cap_bottom=True, cap_top=False)
    zs = zb + H * 0.80                           # nivel de la tierra
    rs = 0.905 * R
    soil = [(zs - 0.03, rs * 0.995), (zs, rs * 0.995), (zs + 0.006, rs * 0.9), (zs + 0.012, rs * 0.6), (zs + 0.016, rs * 0.25), (zs + 0.017, 0.0)]
    loft(b, [(z, r_, r_, 0.0) for (z, r_) in soil], "M_Soil", seg=18, cap_bottom=True, cap_top=True)
    for k in range(7):   # piedrecitas planas (cajas biseladas) sobre la tierra, sin tocar el centro donde salen los tallos
        a = rnd.uniform(0, math.tau)
        rr = rs * rnd.uniform(0.45, 0.78)
        sx, sy = rnd.uniform(0.022, 0.04), rnd.uniform(0.016, 0.028)
        zz = zs + 0.012 * (1 - (rr / rs) ** 1.5) + 0.004
        b.box((math.cos(a) * rr, math.sin(a) * rr, zz), (sx, sy, 0.009), "M_Path_Stone" if k % 2 else "M_Path_StoneWarm", rot=(0, 0, rnd.uniform(0, 180)), bev=0.0, amp=0.0, cuts=0)
    return zs + 0.012


# --- Ficus lyrata -------------------------------------------------------------
FICUS_HW = [(0.0, 0.42), (0.08, 0.50), (0.28, 0.38), (0.42, 0.36), (0.60, 0.76), (0.80, 1.0), (0.90, 0.92), (1.0, 0.0)]


def _ficus_leaf(b, rnd, ps, out, el, L, mat, pl=0.05, bend=0.4):
    """Hoja en violin + peciolo corto y grueso que nace en el tallo (ps = punto de la superficie del tallo). La base de la lamina esta en la punta del peciolo."""
    out = Vector(out).normalized()
    d = (out * math.cos(el) + Z_UP * math.sin(el)).normalized()
    pdir = (out * math.cos(el * 0.55) + Z_UP * math.sin(el * 0.55)).normalized()
    p1 = Vector(ps) + pdir * pl
    stalk(b, [Vector(ps), Vector(ps) + pdir * pl * 0.5 + Z_UP * 0.004, p1], 0.0058, 0.0045, "M_Plant_Leaf", seg=6)
    H = 0.34 * L
    ph = rnd.uniform(0, 6.28)
    blade3d(b, p1, d, L, H, lambda s: _keyed(s, FICUS_HW) * (math.sqrt(max(0.0, 1 - ((s - 0.86) / 0.14) ** 2)) if s > 0.86 else 1.0), mat,
            roll=rnd.uniform(-0.2, 0.2), bend=bend, fold=0.22, bow=0.0, wave=0.006, wave_n=3.0, wave_ph=ph, back=0.10 * L, ns=10, nw=2, thick=0.0035, rib=0.0036, rib_n=4)


def plant_ficus(b, seed=1, hgt=1.55, face=None, spread=math.pi):
    """Ficus lyrata: tronco leñoso con ligera curva, hojas grandes en violin (cintura estrecha, copa ancha y ondulada) en espiral por la parte
    alta del tronco, con peciolo corto grueso, nervio central en relieve y una yema terminal de hojas pequeñas. Un segundo tronco menor."""
    rnd = random.Random(seed)
    R = 0.18
    zs = pot(b, R, 0.34, seed)
    z0 = zs - 0.03

    def trunk(ox, oy, top, rb, rt, ph):
        pts = []
        for k in range(11):
            f = k / 10
            pts.append(Vector((ox + 0.018 * math.sin(2.2 * f + ph) + 0.02 * f * f, oy + 0.012 * math.cos(1.7 * f + ph), z0 + (top - z0) * f)))
        rr = [rb + (rt - rb) * (k / 10) ** 0.8 + 0.004 * math.exp(-k * 2.25) for k in range(11)]
        tube(b, pts, rr, "M_Bark", seg=12)
        return pts, rr

    def at(pts, rr, f):   # punto y radio del tronco a la fraccion f
        x = f * (len(pts) - 1)
        k = min(int(x), len(pts) - 2)
        t = x - k
        return pts[k].lerp(pts[k + 1], t), rr[k] + (rr[k + 1] - rr[k]) * t
    top1 = zs + hgt - 0.30
    pts1, rr1 = trunk(0.0, 0.0, top1, 0.017, 0.0075, seed)
    ang = rnd.uniform(0, math.tau)
    N1 = 23
    for k in range(N1):
        f = 0.34 + 0.62 * k / (N1 - 1)
        fp = (f - 0.34) / 0.62
        ang += 2.399963 + rnd.uniform(-0.12, 0.12)
        p, rt = at(pts1, rr1, f)
        a_ = _az(ang, face, spread)
        out = Vector((math.cos(a_), math.sin(a_), 0))
        L = (0.36 - 0.16 * fp) * rnd.uniform(0.92, 1.08)
        _ficus_leaf(b, rnd, p + out * rt * 0.8, out, math.radians(32 + 28 * fp), L, "M_Leaf_Dark" if k % 3 else "M_Plant_Leaf", pl=0.045 + 0.01 * (1 - fp), bend=0.50 - 0.25 * fp)
    top1p = pts1[-1]
    for q in range(3):   # yema terminal: hojas jovenes erguidas
        a = _az(ang + q * 2.1, face, spread)
        out = Vector((math.cos(a), math.sin(a), 0))
        _ficus_leaf(b, rnd, top1p + out * rr1[-1] * 0.7, out, math.radians(68), 0.12, "M_Plant_LeafLight", pl=0.022, bend=0.15)
    aw = math.atan2(-pts1[-1].y, -pts1[-1].x) + 0.9 if face is None else face + 1.2
    ox, oy = 0.10 * math.cos(aw), 0.10 * math.sin(aw)
    top2 = zs + hgt * 0.62
    pts2, rr2 = trunk(ox, oy, top2, 0.011, 0.0055, seed + 2)
    for k in range(8):
        f = 0.50 + 0.50 * k / 7
        fp = (f - 0.50) / 0.50
        ang += 2.399963
        p, rt = at(pts2, rr2, f)
        a_ = _az(ang, aw, math.radians(105)) if face is None else _az(ang, face + 1.2, math.radians(95))
        out = Vector((math.cos(a_), math.sin(a_), 0))
        _ficus_leaf(b, rnd, p + out * rt * 0.8, out, math.radians(36 + 22 * fp), 0.26 - 0.08 * fp, "M_Plant_Leaf" if k % 2 else "M_Leaf_Dark", pl=0.04, bend=0.45)


# --- Sansevieria ----------------------------------------------------------------
SNAKE_HW = [(0.0, 0.55), (0.10, 0.90), (0.45, 1.0), (0.80, 0.70), (0.96, 0.18), (1.0, 0.0)]


def plant_snake(b, seed=2):
    """Sansevieria trifasciata: hojas en espada, rigidas y erguidas, de distinta altura, desde una roseta apretada. Cada hoja = lamina clara de borde
    (margen amarillento) + lamina central mas oscura con bandas transversales; algo acanaladas y con la punta afilada."""
    rnd = random.Random(seed)
    R = 0.16
    zs = pot(b, R, 0.30, seed)
    N = 13
    ang = rnd.uniform(0, math.tau)
    for k in range(N):
        ang += 2.399963 + rnd.uniform(-0.1, 0.1)
        rr = 0.02 + 0.085 * (k / (N - 1)) ** 0.8          # las primeras (centrales) son las mas altas
        out = Vector((math.cos(ang), math.sin(ang), 0))
        Lh = (0.80 - 0.40 * (k / (N - 1)) ** 0.9) * rnd.uniform(0.9, 1.08)
        p0 = Vector((out.x * rr, out.y * rr, zs - 0.012))
        d = (out * (0.10 + 0.12 * k / (N - 1)) + Z_UP).normalized()
        up = out                                           # la cara superior de la hoja mira hacia fuera de la roseta
        Hh = 0.034 * (1.0 - 0.15 * (k / (N - 1)))
        roll = rnd.uniform(-0.25, 0.25)
        dark = "M_Plant_Leaf" if k % 3 else "M_Leaf_Dark"
        bnd = -rnd.uniform(0.05, 0.22)                     # la punta se inclina hacia fuera
        blade3d(b, p0, d, Lh, Hh, _hw(SNAKE_HW), "M_Plant_LeafLight", up=up, roll=roll, bend=bnd, fold=0.0, bow=0.9, ns=6, nw=2, thick=0.0022, rib=0.0, lift=0.0)
        blade3d(b, p0, d, Lh * 0.985, Hh * 0.80, _hw(SNAKE_HW), dark, up=up, roll=roll, bend=bnd, fold=0.0, bow=0.9, ns=9, nw=2, thick=0.0026, rib=0.0, lift=0.0026,
                mat_fn=lambda s, w: "M_Leaf_Dark" if int(s * 9) % 2 else dark)


# --- Kentia (Howea forsteriana) ----------------------------------------------------
LFLET_HW = [(0.0, 0.35), (0.15, 0.85), (0.40, 1.0), (0.75, 0.55), (0.95, 0.12), (1.0, 0.0)]


def plant_kentia(b, seed=3, face=None, spread=math.pi):
    """Kentia: varios peciolos largos que arquean desde la maceta; cada fronda lleva muchos foliolos largos y estrechos, en PARES a lo largo del
    raquis, plegados en V y colgantes, mas cortos hacia la base y la punta."""
    rnd = random.Random(seed)
    R = 0.21
    zs = pot(b, R, 0.38, seed)
    NF = 8
    for k in range(NF):
        a = _az(k * math.tau / NF + rnd.uniform(-0.15, 0.15), face, spread)
        out = Vector((math.cos(a), math.sin(a), 0))
        base = Vector((out.x * 0.03, out.y * 0.03, zs - 0.015))
        reach, top = rnd.uniform(0.5, 0.78), rnd.uniform(0.95, 1.2)
        pts = [base + out * (reach * (t / 8) ** 1.35) + Z_UP * (top * math.sin(math.pi * 0.5 * (t / 8) ** 0.8) - 0.20 * (t / 8) ** 3) for t in range(9)]
        rad = [0.0085 - 0.0060 * (t / 8) ** 0.7 for t in range(9)]
        tube(b, pts, rad, "M_Plant_LeafLight" if k % 2 else "M_Plant_Leaf", seg=8)
        nl = 16
        for q in range(nl):
            u = 0.30 + 0.68 * q / (nl - 1)
            x = u * 8
            i0 = min(int(x), 7)
            ft = x - i0
            P = pts[i0].lerp(pts[i0 + 1], ft)
            T = (pts[i0 + 1] - pts[i0]).normalized()
            rr = rad[i0] + (rad[i0 + 1] - rad[i0]) * ft
            sv = T.cross(Z_UP)
            sv = sv.normalized() if sv.length > 1e-3 else out.cross(Z_UP).normalized()
            ln = max(0.09, 0.40 * (1 - ((u - 0.62) / 0.45) ** 2) ** 0.7)
            for sg in (-1, 1):
                pbase = P + sv * sg * rr * 0.8
                dd = (sv * sg * 0.85 + T * 0.50 - Z_UP * 0.18).normalized()
                blade3d(b, pbase, dd, ln * rnd.uniform(0.93, 1.05), 0.0135, _hw(LFLET_HW), "M_Plant_Leaf" if (q + k) % 2 else "M_Leaf_Dark", up=Z_UP,
                        bend=0.55 + 0.25 * rnd.random(), fold=0.55, ns=3, nw=1, thick=0.0022, rib=0.0, roll=sg * 0.0)


# --- Monstera deliciosa ----------------------------------------------------------
MONS_HW = [(0.0, 0.45), (0.08, 0.80), (0.28, 1.0), (0.55, 0.88), (0.82, 0.48), (0.95, 0.15), (1.0, 0.0)]


def plant_monstera(b, seed=4, face=None, spread=math.pi):
    """Monstera: hojas grandes acorazonadas con hendiduras (fenestraciones) profundas desde el borde hacia el nervio, sobre peciolos largos y
    arqueados que salen de la base. Lamina inclinada hacia fuera, con nervio central en relieve; la base de la lamina empieza en la punta del peciolo."""
    rnd = random.Random(seed)
    R = 0.21
    zs = pot(b, R, 0.36, seed)
    N = 9
    ang = rnd.uniform(0, math.tau)
    for k in range(N):
        ang += 2.399963 + rnd.uniform(-0.15, 0.15)
        a_ = _az(ang, face, spread)
        out = Vector((math.cos(a_), math.sin(a_), 0))
        plen = rnd.uniform(0.62, 0.98) * (1.0 if k < 7 else 0.7)
        base = Vector((out.x * 0.035, out.y * 0.035, zs - 0.012))
        end = base + out * plen * 0.40 + Z_UP * plen * 0.92
        ctl = base + Z_UP * plen * 1.0 + out * plen * 0.06
        pts = bezier(base, ctl, end, 5)
        stalk(b, pts, 0.0095, 0.0055, "M_Plant_Leaf", seg=8)
        Tend = (pts[-1] - pts[-2]).normalized()
        L = rnd.uniform(0.36, 0.46) * (1.0 if k < 7 else 0.7)
        th = math.radians(rnd.uniform(18, 35))
        d = (out * math.cos(th) - Z_UP * math.sin(th)).normalized()
        sl = [(0.27, 0.020, -1), (0.48, 0.020, -1), (0.68, 0.018, -1),
              (0.32, 0.020, 1), (0.53, 0.020, 1), (0.73, 0.018, 1)]
        sl = [(sc + rnd.uniform(-0.02, 0.02), hw_, sd) for (sc, hw_, sd) in sl]
        blade3d(b, pts[-1], d, L, 0.52 * L, _hw(MONS_HW), "M_Plant_Leaf" if k % 2 else "M_Leaf_Dark", up=Z_UP, roll=rnd.uniform(-0.15, 0.15),
                bend=0.35 + 0.2 * rnd.random(), fold=0.28, wave=0.004, wave_n=3, wave_ph=rnd.uniform(0, 6), back=0.22 * L, shear=0.12,
                slits=sl, w0=0.34, ns=6, nw=4, thick=0.0035, rib=0.0045, rib_n=4)


def standoffs(b, w, h, d=0.02, T=0.035, inset=0.0175):
    """Cuatro separadores de laton que alejan una placa de espesor T de la pared: barrilete entre pared y placa (su cara trasera queda en y=0,
    que es lo que settle() apoya contra el muro real) y cabeza redonda en la cara delantera de la placa (que empieza en y=-d)."""
    for sx in (-1, 1):
        for sz in (-1, 1):
            x_, z_ = sx * (w / 2 - inset), sz * (h / 2 - inset)
            b.cyl((x_, -(d + 0.004) / 2, z_), 0.0065, d + 0.004, "M_Museum_Brass", rot=(90, 0, 0), seg=10, bev=0, amp=0.0)
            b.cyl((x_, -(d + T) - 0.0025, z_), 0.0115, 0.007, "M_Museum_Brass", rot=(90, 0, 0), seg=12, bev=0, amp=0.0)


def sign(text, size, w, h=0.26, board="M_Sign_Board", letters="M_Sign_Letters"):
    """Rotulo de pared: tablero oscuro con canto biselado y panel central en relieve con filete claro, sobre cuatro separadores de laton."""
    def fn(b):
        d = 0.02                                                                      # separacion con la pared
        rbox(b, (0, -d - 0.0175, 0), (w, 0.035, h), 0.009, board, segs=2)             # tablero biselado
        rbox(b, (0, -d - 0.0385, 0), (w - 0.07, 0.008, h - 0.07), 0.003, board, segs=1)   # panel central en relieve
        b.box((0, -d - 0.0428, h / 2 - 0.045), (w - 0.1, 0.0012, 0.006), letters, bev=0, amp=0.0, cuts=0)   # filetes claros arriba y abajo
        b.box((0, -d - 0.0428, -h / 2 + 0.045), (w - 0.1, 0.0012, 0.006), letters, bev=0, amp=0.0, cuts=0)
        standoffs(b, w, h, d, 0.035, 0.0175)
        b.text(text, (0, -0.066, 0), size, letters, ext=0.0045)
    return fn


def wall_sign(name, text, axis, face, s, u, z, size=0.11, w=1.2, coll=None, h=0.26):
    rot = {('x', 1): 180, ('x', -1): 0, ('y', 1): 90, ('y', -1): -90}[(axis, s)]
    pos = (u, face, z) if axis == 'x' else (face, u, z)
    ob = prop("Sign_" + name, pos, rot, sign(text, size, w, h))
    return to_col(ob, coll)


# ---------------------------------------------------------------- recepcion (antecamara con mostrador en L) y directorio
RX, RY = 2.2, -4.45     # origen del mostrador (coordenadas del mundo; el prop va sin girar: local = mundo - origen)


def reception_desk(b):
    """Mostrador de hotel en L junto a la puerta de la Gallery II: tramo largo a lo largo de Y (frente hacia -x, con cuarterones),
    retorno corto contra la fachada, encimera en L con labio, riel de pies de laton y encima: libro de visitas, campanilla,
    expositor de folletos y lampara de despacho."""
    wd, wo, br = "M_Museum_WoodDark", "M_Museum_Wood", "M_Museum_Brass"

    def bx(x0, x1, y0, y1, z0, z1, mat, bev=0.006):
        b.box(((x0 + x1) / 2 - RX, (y0 + y1) / 2 - RY, (z0 + z1) / 2), (x1 - x0, y1 - y0, z1 - z0), mat, bev=bev, amp=0.0, cuts=0)

    def lshape(g, z0, z1, mat, bev):   # encimera en L (g = vuelo extra respecto al cuerpo)
        pts = [(1.5 - g, -4.99 - g), (2.86 + g, -4.99 - g), (2.86 + g, -4.46 + g), (2.2 + g, -4.46 + g), (2.2 + g, -3.91 + g), (1.5 - g, -3.91 + g)]
        b.prism([(x - RX, y - RY, z0) for (x, y) in pts], (0, 0, z1 - z0), mat, bev=bev, amp=0.0)
    # cuerpo: zocalo retranqueado + caja
    bx(1.62, 2.13, -4.92, -3.98, 0.0, 0.1, wd)
    bx(2.13, 2.82, -4.92, -4.53, 0.0, 0.1, wd)
    bx(1.58, 2.17, -4.95, -3.95, 0.1, 1.0, wo, 0.004)
    bx(2.17, 2.84, -4.95, -4.5, 0.1, 1.0, wo, 0.004)
    # frente del tramo largo (cara -x): montantes y travesanos + cuarterones hundidos con junquillo
    ys = [-4.92 + k * 0.94 / 3 for k in range(4)]       # ejes de los montantes
    for y in ys:
        bx(1.558, 1.58, y - 0.03, y + 0.03, 0.1, 1.0, wo)
    for z0, z1 in ((0.1, 0.16), (0.92, 1.0)):
        bx(1.558, 1.58, -4.95, -3.95, z0, z1, wo)
    for y0, y1 in zip(ys, ys[1:]):
        bx(1.568, 1.58, y0 + 0.03, y1 - 0.03, 0.16, 0.92, wd, 0.003)                                  # cuarteron
        for (c0, c1) in ((0.16, 0.18), (0.9, 0.92)):
            bx(1.562, 1.574, y0 + 0.03, y1 - 0.03, c0, c1, wo, 0.002)                                # junquillos horizontales
        for yy in (y0 + 0.03, y1 - 0.05):
            bx(1.562, 1.574, yy, yy + 0.02, 0.18, 0.9, wo, 0.002)                                    # junquillos verticales
    # frente del retorno (cara -y): dos cuarterones
    xs = [2.22 + k * 0.29 for k in range(3)]
    for x in xs:
        bx(x - 0.03, x + 0.03, -4.973, -4.95, 0.1, 1.0, wo)
    for z0, z1 in ((0.1, 0.16), (0.92, 1.0)):
        bx(2.19, 2.83, -4.973, -4.95, z0, z1, wo)
    for x0, x1 in zip(xs, xs[1:]):
        bx(x0 + 0.03, x1 - 0.03, -4.962, -4.95, 0.16, 0.92, wd, 0.003)
    # riel de pies de laton con soportes (delante del tramo largo)
    for yy in ys:
        b.seg((1.564 - RX, yy - RY, 0.21), (1.527 - RX, yy - RY, 0.21), 0.007, br, seg=8)
    tube(b, [(1.527 - RX, -4.94 - RY, 0.21), (1.527 - RX, -3.96 - RY, 0.21)], 0.018, br, seg=12)
    # encimera en L: labio inferior + tablero
    lshape(0.035, 0.995, 1.022, wo, 0.006)
    lshape(0.0, 1.022, 1.06, wd, 0.008)
    TZ = 1.06 - 0.0006   # cota de la encimera (los objetos se hunden 0.6 mm: nada flota)
    # --- libro de visitas abierto (lomo a lo largo de X: las dos paginas quedan a izquierda y derecha de quien lo lee)
    S = Sh(b, (1.82 - RX, -4.18 - RY, TZ), 0.0)
    S.box((0, 0, 0.006), (0.30, 0.44, 0.012), "M_Fabric_Blue", bev=0.004, amp=0.0, cuts=0)
    for sg in (-1, 1):
        S.box((0, sg * 0.104, 0.0145), (0.27, 0.205, 0.005), "M_Paper", bev=0.0015, amp=0.0, cuts=0)
        S.box((0, sg * 0.1, 0.0235), (0.26, 0.19, 0.012), "M_Paper", rot=(sg * 3.0, 0, 0), bev=0.0015, amp=0.0, cuts=0)
    S.box((0.07, 0.0, 0.0165), (0.012, 0.012, 0.024), "M_Plastic_Red", bev=0.002, amp=0.0, cuts=0)    # marcapaginas
    b.seg((2.02 - RX, -4.38 - RY, TZ + 0.005), (2.08 - RX, -4.05 - RY, TZ + 0.005), 0.004, "M_Plastic_Black", seg=6)   # pluma
    # --- campanilla de recepcion: base + cupula torneada + boton
    bell = Sh(b, (1.74 - RX, -4.55 - RY, TZ), 0.0)
    prof = [(0.0, 0.05), (0.008, 0.05), (0.011, 0.044)]
    for k in range(1, 9):
        a = k / 8 * math.pi / 2
        prof.append((0.011 + 0.04 * math.sin(a), 0.044 * math.cos(a) + 0.004))
    loft(bell, [(z, r, r, 0.0) for (z, r) in prof], br, seg=24)
    bell.cyl((0, 0, 0.0575), 0.005, 0.014, br, seg=10, bev=0, amp=0.0)
    bell.cyl((0, 0, 0.066), 0.014, 0.01, br, seg=14, r2=0.011, bev=0, amp=0.0)
    # --- expositor de folletos de madera con tres bandejas escalonadas, laterales trapezoidales, travesano de laton y folletos con franja y foto
    st = Sh(b, (1.9 - RX, -4.78 - RY, TZ), -90.0)
    st.box((0, 0, 0.007), (0.30, 0.14, 0.014), wd, bev=0.004, amp=0.0, cuts=0)                                   # peana
    st.box((0, 0.045, 0.16), (0.28, 0.012, 0.3), wo, rot=(-8, 0, 0), bev=0.003, amp=0.0, cuts=0)                  # respaldo inclinado
    for sx in (-1, 1):   # laterales trapezoidales
        st.prism([(sx * 0.146 - sx * 0.004, -0.062, 0.012), (sx * 0.146 - sx * 0.004, 0.062, 0.012), (sx * 0.146 - sx * 0.004, 0.097, 0.305), (sx * 0.146 - sx * 0.004, 0.058, 0.305)],
                 (sx * 0.008, 0, 0), wo, bev=0.001, amp=0.0)
    cols = ("M_Paint_Sky", "M_Paint_Rose", "M_Paint_Ochre", "M_Paint_Green", "M_Paint_Cream", "M_Paint_Field")
    for j, (zz, yf, dp) in enumerate(((0.04, -0.06, 0.12), (0.12, -0.04, 0.09), (0.2, -0.02, 0.065))):
        st.box((0, yf + 0.006, zz + 0.016), (0.28, 0.012, 0.05), wo, bev=0.002, amp=0.0, cuts=0)                  # labio frontal de la bandeja
        st.box((0, yf + dp / 2, zz + 0.004), (0.28, dp, 0.008), wo, rot=(-6, 0, 0), bev=0.002, amp=0.0, cuts=0)  # fondo de la bandeja (inclinado hacia el respaldo)
        for k in range(3):
            c1, c2, c3 = cols[(j * 3 + k) % 6], cols[(j * 3 + k + 2) % 6], cols[(j * 3 + k + 4) % 6]
            xk = -0.09 + 0.09 * k
            yk = yf + 0.032 + 0.006 * k
            st.box((xk, yk, zz + 0.054), (0.07, 0.003, 0.098), c1, rot=(-9, 0, 0), bev=0.0008, amp=0.0, cuts=0)    # folleto
            st.box((xk, yk - 0.0022, zz + 0.083), (0.07, 0.0016, 0.034), c2, rot=(-9, 0, 0), bev=0, amp=0.0, cuts=0)   # franja de cabecera
            st.box((xk, yk - 0.0022, zz + 0.05), (0.048, 0.0016, 0.036), c3, rot=(-9, 0, 0), bev=0, amp=0.0, cuts=0)   # recuadro de imagen
    st.seg((-0.14, 0.06, 0.305), (0.14, 0.06, 0.305), 0.005, br, seg=8)                                               # travesano de laton arriba
    # --- lampara de banquero: base torneada de laton, columna con anillos, pantalla semicilindrica de cristal esmeralda con testeros de laton,
    #     bombilla tubular dentro y cadenita de encendido con perla
    lp = Sh(b, (2.56 - RX, -4.78 - RY, TZ), 0.0)
    loft(lp, [(z, r, r, 0.0) for (z, r) in ((0.0, 0.075), (0.006, 0.076), (0.014, 0.068), (0.022, 0.05), (0.03, 0.036), (0.04, 0.025), (0.052, 0.0165), (0.07, 0.0115), (0.09, 0.009))], br, seg=28)
    b.seg(lp.p((0, 0, 0.088)), lp.p((0, 0, 0.372)), 0.0075, br, seg=10)
    for zz in (0.14, 0.22, 0.3):
        lp.cyl((0, 0, zz), 0.0125, 0.008, br, seg=12, bev=0, amp=0.0)                                                # anillos de la columna
    arc_band(lp, (0, 0, 0.3), 'y', 0.072, 0.005, 0, 180, 0.30, "M_Glass_Emerald", n=16)                             # pantalla (abierta por abajo)
    for sg in (-1, 1):
        lp.prism([(0.072 * math.cos(math.radians(a_)), sg * 0.151, 0.3 + 0.072 * math.sin(math.radians(a_))) for a_ in range(0, 181, 15)], (0, sg * 0.004, 0), br, amp=0.0)   # testeros
    lp.cyl((0, 0, 0.374), 0.0145, 0.012, br, seg=12, bev=0, amp=0.0)                                                 # collarin sobre la pantalla
    lp.cyl((0, 0.0, 0.287), 0.014, 0.17, "M_Bulb_Warm", rot=(90, 0, 0), seg=10, bev=0, amp=0.0)                      # bombilla tubular
    lp.cyl((0, -0.1, 0.287), 0.012, 0.02, br, rot=(90, 0, 0), seg=8, bev=0, amp=0.0)                                # portalamparas
    lp.seg((0.0, 0.1, 0.287), (0.0, 0.1, 0.19), 0.0016, br, seg=4)                                                   # cadenita
    lp.cyl((0.0, 0.1, 0.184), 0.0055, 0.012, br, seg=8, bev=0, amp=0.0)                                              # perla


def reception_chair(b):
    """Silla de madera con respaldo de travesanos y asiento tapizado. Frente -y, base z=0."""
    wo, wd = "M_Museum_Wood", "M_Museum_WoodDark"
    yb = lambda z: 0.19 + 0.0532 * z      # eje de los montantes traseros (inclinados hacia atras)
    for sx in (-1, 1):
        b.cyl((sx * 0.2, -0.19, 0.2), 0.02, 0.4, wo, seg=10, r2=0.014, bev=0, amp=0.0)                 # patas delanteras
        b.seg((sx * 0.2, yb(0.0), 0.0), (sx * 0.2, yb(0.94), 0.94), 0.019, wo, seg=10)                  # patas traseras = montantes del respaldo
        b.seg((sx * 0.2, -0.19, 0.14), (sx * 0.2, yb(0.14), 0.14), 0.009, wd, seg=6)                    # travesanos laterales
    b.seg((-0.2, -0.19, 0.14), (0.2, -0.19, 0.14), 0.009, wd, seg=6)
    b.seg((-0.2, yb(0.14), 0.14), (0.2, yb(0.14), 0.14), 0.009, wd, seg=6)
    b.box((0, 0.0, 0.405), (0.46, 0.42, 0.05), wo, bev=0.008, amp=0.0, cuts=0)                           # bastidor del asiento
    b.box((0, -0.01, 0.455), (0.42, 0.4, 0.055), "M_Fabric_Blue", bev=0.02, amp=0.0, cuts=0)              # cojin
    for zz in (0.62, 0.72, 0.82):                                                                      # travesanos del respaldo
        b.box((0, yb(zz), zz), (0.4, 0.02, 0.06), wo, rot=(-3, 0, 0), bev=0.006, amp=0.0, cuts=0)
    b.box((0, yb(0.9), 0.9), (0.44, 0.03, 0.08), wd, rot=(-3, 0, 0), bev=0.008, amp=0.0, cuts=0)         # cresta


def key_cabinet(b):
    """Casillero de llaves de hotel para colgar en la pared: marco con cornisa, fondo, 4x3 casillas con ganchos y llaves de laton.
    Trasera en y=0, frente -y, centrado en z=0."""
    wd, wo, br = "M_Museum_WoodDark", "M_Museum_Wood", "M_Museum_Brass"
    b.box((0, -0.01, 0), (0.9, 0.02, 0.8), wd, bev=0.003, amp=0.0, cuts=0)
    for sx in (-1, 1):
        b.box((sx * 0.42, -0.05, 0), (0.06, 0.1, 0.8), wo, bev=0.006, amp=0.0, cuts=0)
    for sz in (-1, 1):
        b.box((0, -0.05, sz * 0.37), (0.78, 0.1, 0.06), wo, bev=0.006, amp=0.0, cuts=0)
        b.box((0, -0.06, sz * 0.4125), (0.96, 0.12, 0.025), wo, bev=0.006, amp=0.0, cuts=0)           # cornisa / zocalo del casillero
    ix, iz = 0.78, 0.68
    nc, nr = 4, 3
    for i in range(1, nc):
        b.box((-ix / 2 + i * ix / nc, -0.05, 0), (0.012, 0.08, iz), wo, bev=0.002, amp=0.0, cuts=0)
    for j in range(1, nr):
        b.box((0, -0.05, -iz / 2 + j * iz / nr), (ix, 0.08, 0.012), wo, bev=0.002, amp=0.0, cuts=0)
    fobs = ("M_Plastic_Red", "M_Plastic_Blue", "M_Plastic_Green", "M_Plastic_Orange")
    for j in range(nr):
        for i in range(nc):
            cx, cz = -ix / 2 + (i + 0.5) * ix / nc, -iz / 2 + (j + 0.5) * iz / nr
            b.cyl((cx, -0.03, cz + 0.06), 0.006, 0.03, br, rot=(90, 0, 0), seg=8, bev=0, amp=0.0)    # gancho
            if (i + j) % 4 != 3:   # casillas sin llave (huespedes fuera)
                b.box((cx, -0.04, cz - 0.01), (0.034, 0.007, 0.075), br, bev=0.002, amp=0.0, cuts=0)  # llave colgada: etiqueta
                b.box((cx, -0.0455, cz - 0.03), (0.026, 0.004, 0.034), fobs[(i + j * 2) % 4], bev=0.001, amp=0.0, cuts=0)


def directory_board(b):
    """Directorio de pared 1.0 x 1.1: marco de madera, tablero oscuro con filete claro, titulo y plantas con flechas.
    Trasera en y=0, frente -y, centrado en z=0."""
    wo, bd, lt = "M_Museum_Wood", "M_Sign_Board", "M_Sign_Letters"
    b.box((0, -0.02, 0), (0.88, 0.03, 0.98), bd, bev=0.004, amp=0.0, cuts=0)
    for sx in (-1, 1):
        b.box((sx * 0.47, -0.03, 0), (0.06, 0.06, 1.1), wo, bev=0.008, amp=0.0, cuts=0)
        b.box((0, -0.03, sx * 0.52), (0.88, 0.06, 0.06), wo, bev=0.008, amp=0.0, cuts=0)
    yf = -0.0365
    for sx in (-1, 1):   # filete claro interior
        b.box((sx * 0.40, yf, 0), (0.012, 0.004, 0.9), lt, bev=0, amp=0.0, cuts=0)
        b.box((0, yf, sx * 0.45), (0.8, 0.004, 0.012), lt, bev=0, amp=0.0, cuts=0)
    tx = -0.040
    b.text("GALLERIES", (0, tx, 0.385), 0.13, lt, ext=0.008)
    for zz in (0.285, -0.14):
        b.box((0, yf, zz), (0.7, 0.004, 0.008), "M_Museum_Brass", bev=0, amp=0.0, cuts=0)
    for (zh, zl, head, nums) in ((0.205, 0.075, "GROUND FLOOR", "I   II   III   VII"), (-0.225, -0.355, "UPPER FLOOR", "IV   V   VI")):
        b.text(head, (-0.04, tx, zh), 0.075, lt, ext=0.008)
        b.text(nums, (0, tx, zl), 0.12, lt, ext=0.008)
        ax, y0 = 0.32, -0.034     # flecha hacia la derecha (hacia el arco de la escalera y la puerta de la Gallery I)
        b.prism([(ax - 0.06, y0, zh - 0.006), (ax + 0.012, y0, zh - 0.006), (ax + 0.012, y0, zh - 0.024), (ax + 0.07, y0, zh), (ax + 0.012, y0, zh + 0.024),
                 (ax + 0.012, y0, zh + 0.006), (ax - 0.06, y0, zh + 0.006)], (0, -0.006, 0), lt, amp=0.0)


def cat_sculpture(b):
    """Escultura de gata sentada, tallada en facetas (sin bolas): guino narrativo. Base en z=0, mira a -y. Peana, torso troncococico apoyado
    en dos ancas, dos patas delanteras rectas con zarpas, cuello, cabeza facetada con hocico y orejas triangulares, y cola ahusada
    que rodea las ancas y termina junto a la zarpa derecha (todo dentro de la peana)."""
    m = "M_Museum_Stone"
    b.box((0, 0.02, 0.02), (0.3, 0.36, 0.04), m, bev=0.01, amp=0.0, cuts=0)                                   # peana
    for sx in (-1, 1):
        b.cyl((sx * 0.085, 0.075, 0.14), 0.095, 0.2, m, seg=6, r2=0.07, bev=0.0, amp=0.0)                    # anca
    b.cyl((0, 0.05, 0.22), 0.125, 0.36, m, rot=(-4, 0, 0), seg=7, r2=0.072, bev=0.0, amp=0.0)               # torso
    for sx in (-1, 1):
        b.cyl((sx * 0.052, -0.07, 0.19), 0.03, 0.3, m, rot=(-3, 0, 0), seg=6, r2=0.026, bev=0.0, amp=0.0)   # pata delantera
        b.box((sx * 0.052, -0.108, 0.054), (0.062, 0.092, 0.028), m, bev=0.008, amp=0.0, cuts=0)           # zarpa
    b.cyl((0, -0.03, 0.4), 0.062, 0.05, m, seg=7, r2=0.056, bev=0.0, amp=0.0)                                 # cuello
    b.cyl((0, -0.03, 0.47), 0.088, 0.12, m, rot=(-6, 0, 0), seg=7, r2=0.07, bev=0.0, amp=0.0)               # cabeza
    b.box((0, -0.108, 0.445), (0.058, 0.04, 0.04), m, rot=(-8, 0, 0), bev=0.006, amp=0.0, cuts=0)           # hocico
    for sx in (-1, 1):   # orejas: prismas triangulares rectos sobre la cabeza
        b.prism([(sx * 0.024, -0.045, 0.515), (sx * 0.086, -0.045, 0.515), (sx * 0.068, -0.045, 0.6)], (0, 0.03, 0), m, amp=0.0)
    pts = [Vector(q) for q in ((0.07, 0.14, 0.062), (0.125, 0.085, 0.062), (0.132, -0.01, 0.062), (0.115, -0.09, 0.062), (0.1, -0.13, 0.068))]
    sweep(b, pts, [(0.024 * math.cos(k * math.tau / 6), 0.024 * math.sin(k * math.tau / 6)) for k in range(6)], m, sc=[(q, q) for q in (1.0, 0.92, 0.84, 0.76, 0.64)])   # cola facetada (hexagono ahusado)


def utility(b):
    """Cuadro electrico de pared (con prensaestopas)."""
    b.box((0, -0.06, 0), (0.45, 0.12, 0.6), "M_Hatch_Metal", bev=0.012, amp=0.002, cuts=0)
    b.box((0.15, -0.125, 0.0), (0.04, 0.02, 0.1), "M_Museum_Brass", bev=0.004, amp=0.001, cuts=0)


def lockers(b):
    """Taquillas metalicas de dos puertas (0.5 x 0.5 x 1.9): pies, cuerpo, puerta con panel en relieve, dos rejillas de ventilacion con lamas
    inclinadas sobre fondo oscuro, placa de numero LISA (en blanco) con tornillos, tirador de pestillo con cerradura y tres bisagras de nudillo;
    remate comun con pendiente hacia atras."""
    sh, mt, dk, br = "M_Museum_Shutter", "M_Museum_Metal", "M_Floor_Dark", "M_Museum_Brass"
    for k in range(2):
        x = -0.26 + k * 0.52
        b.box((x, 0, 0.975), (0.5, 0.5, 1.85), sh, bev=0.012, amp=0.003, cuts=1)                              # cuerpo (z 0.05 - 1.90)
        for fx in (-1, 1):
            for fy in (-1, 1):
                b.box((x + fx * 0.205, fy * 0.205, 0.025), (0.05, 0.05, 0.05), mt, bev=0.004, amp=0.0, cuts=0)   # pies
        b.box((x, -0.2535, 0.975), (0.44, 0.006, 1.76), sh, bev=0.004, amp=0.0, cuts=0)                       # panel de la puerta en relieve
        for (zc_, hh_, nl) in ((1.64, 0.2, 7), (0.26, 0.12, 4)):                                              # rejillas: fondo oscuro + lamas inclinadas
            b.box((x, -0.2565, zc_), (0.3, 0.003, hh_), dk, bev=0, amp=0.0, cuts=0)
            for j in range(nl):
                zz = zc_ - hh_ / 2 + (j + 0.6) * hh_ / nl
                b.box((x, -0.262, zz), (0.3, 0.016, 0.011), sh, rot=(38, 0, 0), bev=0.002, amp=0.0, cuts=0)
        b.box((x, -0.2575, 1.42), (0.075, 0.003, 0.04), br, bev=0.001, amp=0.0, cuts=0)                       # placa de numero en blanco
        for sx in (-1, 1):
            b.cyl((x + sx * 0.0325, -0.2595, 1.42), 0.0035, 0.003, mt, rot=(90, 0, 0), seg=8, bev=0, amp=0.0)
        b.box((x + 0.16, -0.2585, 1.0), (0.05, 0.004, 0.17), mt, bev=0.002, amp=0.0, cuts=0)                  # placa del tirador
        b.box((x + 0.16, -0.2665, 1.04), (0.024, 0.016, 0.1), mt, bev=0.004, amp=0.0, cuts=0)                  # asa de pestillo
        b.cyl((x + 0.16, -0.262, 0.93), 0.0135, 0.008, br, rot=(90, 0, 0), seg=12, bev=0, amp=0.0)             # cerradura
        b.box((x + 0.16, -0.2665, 0.93), (0.003, 0.002, 0.014), dk, bev=0, amp=0.0, cuts=0)                    # ojo de la llave
        for zz in (0.42, 0.975, 1.53):                                                                         # bisagras de nudillo
            b.cyl((x - 0.2265, -0.2535, zz), 0.0075, 0.09, mt, seg=8, bev=0, amp=0.0)
    ysl = [(-0.255, 1.9), (0.25, 1.9), (0.25, 1.958)]                                                           # remate comun con pendiente
    b.prism([(-0.53, y_, z_) for (y_, z_) in ysl], (1.06, 0, 0), mt, bev=0.003, amp=0.0)
    b.box((0, -0.2535, 1.9085), (1.06, 0.01, 0.017), mt, bev=0.002, amp=0.0, cuts=0)


def workbench(b):
    for sx in (-0.72, 0.72):
        for sy in (-0.24, 0.24):
            b.box((sx, sy, 0.43), (0.07, 0.07, 0.86), "M_Museum_WoodDark", bev=0.008, amp=0.003, cuts=0)
    b.box((0, 0, 0.88), (1.6, 0.62, 0.06), "M_Museum_Wood", bev=0.012, amp=0.004, cuts=2)
    b.box((0, 0, 0.2), (1.5, 0.55, 0.03), "M_Museum_Wood", bev=0.006, amp=0.003, cuts=1)
    b.box((0.6, -0.3, 0.95), (0.16, 0.1, 0.1), "M_Hatch_Metal", bev=0.008, amp=0.002, cuts=0)  # tornillo de banco
    b.box((-0.3, -0.05, 0.925), (0.3, 0.03, 0.02), "M_Museum_Metal", rot=(0, 0, 20), bev=0.003, amp=0.001, cuts=0)  # martillo
    b.box((-0.18, -0.01, 0.94), (0.05, 0.08, 0.05), "M_Hatch_Metal", rot=(0, 0, 20), bev=0.006, amp=0.001, cuts=0)
    b.cyl((0.1, 0.12, 0.99), 0.06, 0.16, "M_Ceramic", seg=10, bev=0, amp=0.002)  # bote de pinceles
    for k in range(5):
        a = k * 1.25
        p0 = Vector((0.1 + math.cos(a) * 0.025, 0.12 + math.sin(a) * 0.025, 1.0))
        p1 = p0 + Vector((math.cos(a) * 0.05, math.sin(a) * 0.05, 0.22))
        b.seg(p0, p1, 0.007, "M_Museum_WoodDark", seg=5)
        dv = (p1 - p0).normalized()                                  # virola + penacho de cerdas cargado de pintura, en loft (sin bolas)
        loft(b, [(z_, r_, r_, 0.0) for (z_, r_) in ((0.0, 0.0075), (0.016, 0.0078), (0.018, 0.0105), (0.032, 0.0112), (0.044, 0.0085), (0.052, 0.003), (0.056, 0.0008))],
             random.choice(["M_Flower_Yellow", "M_Fabric_Blue", "M_Rug_Terracotta"]), seg=16, xf=_axis_xf(p1 - dv * 0.004, dv))
    for k, m in enumerate(("M_Fabric_Blue", "M_Flower_Yellow", "M_Rug_Terracotta")):  # botes de pintura
        b.cyl((-0.55 + k * 0.17, 0.15, 0.97), 0.07, 0.13, "M_Museum_Metal", seg=12, bev=0, amp=0.002)
        b.cyl((-0.55 + k * 0.17, 0.15, 1.04), 0.06, 0.012, m, seg=12, bev=0, amp=0.001)


class Sh:
    """Proxy de B que desplaza y gira (alrededor de Z) todo lo que se dibuja: permite montar subconjuntos
    (botellas, herramientas, bolsas) dentro de otro prop. Admite loft() y tube()."""

    def __init__(s, b, off=(0, 0, 0), rz=0.0):
        s.b, s.rz = b, rz
        s.M = Matrix.Translation(Vector(off)) @ Matrix.Rotation(math.radians(rz), 4, 'Z')

    def p(s, c):
        return tuple(s.M @ Vector(c))

    def box(s, c, size, mat, rot=(0, 0, 0), **kw):
        s.b.box(s.p(c), size, mat, rot=(rot[0], rot[1], rot[2] + s.rz), **kw)

    def cyl(s, c, r, h, mat, rot=(0, 0, 0), **kw):
        s.b.cyl(s.p(c), r, h, mat, rot=(rot[0], rot[1], rot[2] + s.rz), **kw)

    def seg(s, p0, p1, r, mat, seg=5):
        s.b.seg(s.p(p0), s.p(p1), r, mat, seg=seg)

    def prism(s, pts, ext, mat, bev=0.0, amp=0.012):
        s.b.prism([s.p(q) for q in pts], tuple(s.M.to_3x3() @ Vector(ext)), mat, bev=bev, amp=amp)

    def _finish(s, bm, c, rot, mat, bev, amp, minsize, freq=0.45):
        bmesh.ops.transform(bm, matrix=s.M, verts=bm.verts)
        s.b._finish(bm, (0, 0, 0), (0, 0, 0), mat, bev, amp, minsize, freq)

    def _push(s, bm, mat):
        bmesh.ops.transform(bm, matrix=s.M, verts=bm.verts)
        s.b._push(bm, mat)


def bottle(b, pos=(0, 0, 0), h=0.26, r=0.04, mat="M_Plastic_Blue", cap="M_Plastic_White", oy=1.0, rz=0.0):
    """Botella de producto: cuerpo torneado (loft) con hombro, cuello y tapon. Base en pos."""
    prof = ((0.0, 0.84), (0.015, 0.97), (0.04, 1.0), (0.6, 1.0), (0.7, 0.82), (0.77, 0.5), (0.82, 0.36), (0.87, 0.36))
    loft(b, [(z * h, f * r, f * r * oy, 0.0) for (z, f) in prof], mat, seg=16, xf=Matrix.Translation(pos) @ Matrix.Rotation(math.radians(rz), 4, 'Z'))
    b.cyl((pos[0], pos[1], pos[2] + h * 0.935), r * 0.5, h * 0.13, cap, seg=12, bev=0, amp=0.0)


def jug(b, pos=(0, 0, 0), mat="M_Plastic_Blue", cap="M_Plastic_White", h=0.3):
    """Garrafa de producto con asa lateral."""
    prof = ((0.0, 0.8), (0.02, 0.95), (0.05, 1.0), (0.62, 1.0), (0.74, 0.9), (0.84, 0.55), (0.9, 0.28), (0.97, 0.28))
    rx, ry = 0.085, 0.06
    loft(b, [(z * h, f * rx, f * ry, 0.0) for (z, f) in prof], mat, seg=18, xf=Matrix.Translation(pos))
    b.cyl((pos[0], pos[1], pos[2] + h * 0.985), 0.028, 0.03, cap, seg=12, bev=0, amp=0.0)
    hp = [(-0.04, 0.0, 0.87), (-0.075, 0.0, 0.93), (-0.105, 0.0, 0.75), (-0.095, 0.0, 0.58), (-0.08, 0.0, 0.5)]
    tube(b, [(pos[0] + x, pos[1] + y, pos[2] + z * h) for (x, y, z) in hp], 0.007, mat, seg=6)


def spray_bottle(b, pos=(0, 0, 0), mat="M_Plastic_Green", rz=0.0):
    """Botella con pulverizador de gatillo: cuerpo oval (loft), collar, cabezal, boquilla y gatillo. Base en pos, boquilla hacia -y."""
    S = Sh(b, pos, rz)
    loft(S, [(0.0, 0.028, 0.019, 0), (0.012, 0.034, 0.024, 0), (0.17, 0.034, 0.024, 0), (0.2, 0.026, 0.019, 0), (0.222, 0.015, 0.015, 0), (0.232, 0.015, 0.015, 0)], mat, seg=18)
    S.cyl((0, 0, 0.241), 0.019, 0.02, "M_Plastic_White", seg=14, bev=0, amp=0.0)                # collar
    S.box((0, -0.012, 0.272), (0.036, 0.07, 0.04), "M_Plastic_White", bev=0.008, amp=0.0, cuts=0)  # cabezal
    S.cyl((0, -0.058, 0.274), 0.008, 0.026, "M_Plastic_White", rot=(90, 0, 0), seg=10, bev=0, amp=0.0)   # boquilla
    S.cyl((0, -0.073, 0.274), 0.005, 0.006, "M_Floor_Dark", rot=(90, 0, 0), seg=8, bev=0, amp=0.0)       # orificio
    S.prism([(-0.008, -0.026, 0.262), (-0.008, -0.046, 0.25), (-0.008, -0.052, 0.218), (-0.008, -0.041, 0.215), (-0.008, -0.033, 0.246), (-0.008, -0.016, 0.262)],
            (0.016, 0, 0), "M_Plastic_White", amp=0.0)                                               # gatillo


def mop_head(b, ctr, d=(0, 0, 1), n=44, seed=1, zlow=0.0, reach=0.13):
    """Hebras de una fregona de cuerda: nacen en un aro perpendicular al mango (eje d), cuelgan y se tumban hacia fuera hasta zlow.
    ctr = centro del aro de sujecion."""
    rnd = random.Random(seed)
    ctr, d = Vector(ctr), Vector(d).normalized()
    e1 = d.cross(Vector((1, 0, 0))).normalized()
    e2 = d.cross(e1).normalized()
    zf = zlow + 0.004
    for k in range(n):
        a = k * math.tau / n + rnd.uniform(-0.08, 0.08)
        rin = 0.032 if k % 2 else 0.018
        st = ctr + (e1 * math.cos(a) + e2 * math.sin(a)) * rin
        uh = Vector((st.x - ctr.x, st.y - ctr.y, 0))
        uh = uh.normalized() if uh.length > 1e-4 else Vector((1, 0, 0))
        ln = reach * rnd.uniform(0.75, 1.1)
        zr = max(st.z - zf, 0.0)
        pts = [st, Vector((st.x, st.y, zf + zr * 0.55)) + uh * 0.012,
               Vector((st.x, st.y, zf + zr * 0.1)) + uh * (0.02 + ln * 0.35),
               Vector((st.x, st.y, zf)) + uh * (0.02 + ln)]
        tube(b, pts, 0.0036, "M_Mop_Cotton", seg=3)


def wring_mop_bucket(b):
    """Cubo de fregona amarillo con escurridor de prensa, ruedas y asa; fregona apoyada en el borde y trapo doblado sobre el.
    Local: base z=0, el escurridor al fondo (+y), la fregona se inclina hacia el frente (-y)."""
    Y = "M_Plastic_Yellow"
    zr, zb = 0.475, 0.09    # borde y fondo exterior
    outer = [(zb, .145, .205), (0.10, .16, .222), (0.30, .188, .255), (0.46, .205, .272), (zr, .208, .276)]
    inner = [(zr, .19, .258), (0.46, .188, .256), (0.30, .172, .239), (0.14, .135, .195), (0.13, .13, .19)]
    loft(b, [(z, rx, ry, 0.0) for (z, rx, ry) in outer + inner], Y, seg=28, cap_bottom=True, cap_top=True)
    loft(b, [(0.308, .171, .237, 0.0), (0.314, .171, .237, 0.0)], "M_Glass_Mirror", seg=24)    # agua
    for sx in (-1, 1):   # ruedas con horquilla
        for sy in (-1, 1):
            cx, cy = sx * 0.115, sy * 0.15
            b.box((cx, cy, 0.121), (0.05, 0.05, 0.008), "M_Steel", bev=0.002, amp=0.0, cuts=0)
            for fx in (-0.016, 0.016):
                b.box((cx + fx, cy, 0.083), (0.004, 0.034, 0.075), "M_Steel", bev=0.001, amp=0.0, cuts=0)
            b.cyl((cx, cy, 0.045), 0.045, 0.022, "M_Rubber", rot=(0, 90, 0), seg=16, bev=0, amp=0.0)
            b.cyl((cx, cy, 0.045), 0.008, 0.04, "M_Steel", rot=(0, 90, 0), seg=8, bev=0, amp=0.0)
    # escurridor: dos placas laterales apoyadas en el borde, cestillo y palanca
    for sx in (-1, 1):
        b.box((sx * 0.135, 0.205, zr + 0.065), (0.012, 0.2, 0.13), "M_Plastic_Grey", bev=0.004, amp=0.0, cuts=0)
    b.box((0, 0.125, zr + 0.065), (0.258, 0.014, 0.13), "M_Plastic_Grey", bev=0.004, amp=0.0, cuts=0)
    b.box((0, 0.29, zr + 0.065), (0.258, 0.014, 0.13), "M_Plastic_Grey", bev=0.004, amp=0.0, cuts=0)
    b.cyl((0, 0.29, zr + 0.09), 0.01, 0.31, "M_Steel", rot=(0, 90, 0), seg=8, bev=0, amp=0.0)          # eje de la palanca
    b.box((0, 0.2, zr + 0.14), (0.25, 0.1, 0.012), "M_Steel", bev=0.002, amp=0.0, cuts=0)              # placa de prensa elevada
    tube(b, [(0.0, 0.29, zr + 0.09), (0.0, 0.31, zr + 0.28), (0.0, 0.37, zr + 0.42), (0.0, 0.43, zr + 0.5)], 0.011, "M_Steel", seg=8)   # palanca
    b.cyl((0, 0.45, zr + 0.52), 0.019, 0.17, "M_Plastic_Black", rot=(0, 90, 0), seg=12, bev=0, amp=0.0)   # empunadura
    # asa de alambre apoyada contra los costados (con sus orejetas)
    hp = [(0.205 * math.cos(math.pi * k / 10), 0.0, 0.43 + 0.17 * math.sin(math.pi * k / 10)) for k in range(11)]
    tube(b, hp, 0.006, "M_Steel", seg=6)
    for sx in (-1, 1):
        b.box((sx * 0.203, 0.0, 0.43), (0.016, 0.034, 0.03), "M_Plastic_Grey", bev=0.003, amp=0.0, cuts=0)
    # fregona: aro de hebras al fondo y mango apoyado en el canto interior del borde delantero
    th = math.radians(35)
    d = Vector((0, -math.sin(th), math.cos(th)))
    rh = 0.0135
    R = Vector((0, -0.258, zr))
    zb0 = 0.30
    ay = R.y + ((R.z - zb0) * math.sin(th) + rh) / math.cos(th)
    A = Vector((0, ay, zb0))
    base = A - d * 0.07
    mop_head(b, base, d, n=44, seed=3, zlow=0.133, reach=0.035)
    b.cyl(tuple(A - d * 0.035), 0.03, 0.07, "M_Steel", rot=(math.degrees(th), 0, 0), seg=12, r2=0.022, bev=0, amp=0.0)
    tube(b, [tuple(A), tuple(A + d * 1.18)], rh, "M_Museum_Wood", seg=8)
    b.cyl(tuple(A + d * 1.18), 0.0165, 0.02, "M_Museum_Wood", rot=(math.degrees(th), 0, 0), seg=10, bev=0, amp=0.0)
    # trapo doblado sobre el borde (lado -x, delante-izquierda), con caida por fuera y por dentro
    phi = math.pi + 0.55
    rxr, ryr = 0.199, 0.267
    P = Vector((rxr * math.cos(phi), ryr * math.sin(phi), 0))
    nrm = Vector((math.cos(phi) / rxr, math.sin(phi) / ryr, 0)).normalized()
    t = Vector((-nrm.y, nrm.x, 0))
    C = Sh(b, (P.x, P.y, 0), math.degrees(math.atan2(t.y, t.x)))
    cl = "M_Fabric_Blue"
    C.box((0, 0.002, zr + 0.0075), (0.11, 0.075, 0.007), cl, bev=0.0025, amp=0.0, cuts=0)                         # sobre el borde
    C.box((0, -0.0165 + 0.0035, zr - 0.075 - 0.004), (0.11, 0.007, 0.16), cl, rot=(6, 0, 0), bev=0.0025, amp=0.0, cuts=0)    # cae por fuera
    C.box((0, 0.0275, zr - 0.05 - 0.004), (0.11, 0.007, 0.1), cl, rot=(-5, 0, 0), bev=0.0025, amp=0.0, cuts=0)      # cae por dentro


def mop_lean(b):
    """Fregona de cuerda apoyada en la pared: el cabezal tumbado en el suelo y el mango inclinado hacia +y (la pared)."""
    th = math.radians(13)
    d = Vector((0, math.sin(th), math.cos(th)))
    ctr = Vector((0, 0, 0.05))
    mop_head(b, ctr, d, n=52, seed=7, zlow=0.0, reach=0.16)
    b.cyl(tuple(ctr + d * 0.035), 0.03, 0.07, "M_Steel", rot=(-math.degrees(th), 0, 0), seg=12, r2=0.022, bev=0, amp=0.0)
    tube(b, [tuple(ctr + d * 0.07), tuple(ctr + d * 1.35)], 0.0135, "M_Museum_Wood", seg=8)
    b.cyl(tuple(ctr + d * 1.35), 0.0165, 0.02, "M_Museum_Wood", rot=(-math.degrees(th), 0, 0), seg=10, bev=0, amp=0.0)


def broom(b):
    """Escoba de casa apoyada en la pared: cabezal de madera con cerdas (muchas hebras), mango largo. Inclinada hacia +y."""
    th = math.radians(10)
    cs, sn = math.cos(th), math.sin(th)

    def lean(p):
        return (p[0], p[1] * cs + p[2] * sn, -p[1] * sn + p[2] * cs)
    ang = (-math.degrees(th), 0, 0)
    b.box(lean((0, 0, 0.1)), (0.3, 0.05, 0.1), "M_Bristle", rot=ang, bev=0.004, amp=0.0, cuts=0)                  # nucleo de cerdas
    rnd = random.Random(5)
    for i in range(15):
        for j in range(3):
            x, y = -0.14 + i * 0.02, -0.016 + j * 0.016
            b.seg(lean((x, y, 0.06)), lean((x + rnd.uniform(-0.006, 0.006), y + rnd.uniform(-0.006, 0.006), 0.0 + rnd.uniform(0.0, 0.012))), 0.006, "M_Bristle", seg=3)
    b.box(lean((0, 0, 0.165)), (0.32, 0.06, 0.05), "M_Museum_Wood", rot=ang, bev=0.008, amp=0.0, cuts=0)           # cabezal
    b.box(lean((0, 0, 0.145)), (0.325, 0.065, 0.012), "M_Steel", rot=ang, bev=0.002, amp=0.0, cuts=0)             # fleje
    b.cyl(lean((0, 0, 0.215)), 0.026, 0.07, "M_Museum_Wood", rot=ang, seg=10, r2=0.014, bev=0, amp=0.0)          # casquillo conico
    tube(b, [lean((0, 0, 0.2)), lean((0, 0, 1.38))], 0.0125, "M_Museum_Wood", seg=8)
    b.cyl(lean((0, 0, 1.385)), 0.0145, 0.016, "M_Museum_Wood", rot=ang, seg=10, bev=0, amp=0.0)
    b.cyl(lean((0, 0, 1.28)), 0.016, 0.03, "M_Plastic_Red", rot=ang, seg=10, bev=0, amp=0.0)                      # anilla para colgar


def dustpan(b):
    """Recogedor de plastico rojo: pala con labio fino, bordes laterales, tope trasero y mango. Plano sobre el suelo, mango hacia +y."""
    c = "M_Plastic_Red"
    b.prism([(-0.125, -0.17, 0.0), (-0.125, 0.1, 0.0), (-0.125, 0.1, 0.012), (-0.125, -0.12, 0.012), (-0.125, -0.17, 0.004)], (0.25, 0, 0), c, amp=0.0)
    for sx in (-1, 1):
        b.box((sx * 0.1175, -0.02, 0.0375), (0.015, 0.24, 0.05), c, bev=0.004, amp=0.0, cuts=0)
    b.box((0, 0.1075, 0.04), (0.25, 0.015, 0.056), c, bev=0.004, amp=0.0, cuts=0)
    for sx in (-1, 1):
        tube(b, [(sx * 0.07, 0.1, 0.035), (sx * 0.07, 0.17, 0.085), (sx * 0.07, 0.25, 0.12)], 0.0085, c, seg=6)
    b.cyl((0, 0.25, 0.12), 0.011, 0.16, "M_Plastic_Black", rot=(0, 90, 0), seg=10, bev=0, amp=0.0)


def cleaning_cart(b):
    """Carrito de limpieza amarillo: dos bandejas con borde, montantes de acero, barra de empuje, soporte de bolsa de basura
    (aro + bolsa negra), ruedas con horquilla, botellas, pulverizador y trapos doblados. Largo en x, fondo y (trasera +y)."""
    Y, G = "M_Plastic_Yellow", "M_Steel"
    L, W = 0.95, 0.45

    def tray(z0, rim):
        b.box((0, 0, z0 + 0.007), (L, W, 0.014), Y, bev=0.004, amp=0.0, cuts=0)
        for sy in (-1, 1):
            b.box((0, sy * (W / 2 - 0.007), z0 + 0.007 + rim / 2), (L, 0.014, rim), Y, bev=0.004, amp=0.0, cuts=0)
        for sx in (-1, 1):
            b.box((sx * (L / 2 - 0.007), 0, z0 + 0.007 + rim / 2), (0.014, W - 0.028, rim), Y, bev=0.004, amp=0.0, cuts=0)
    tray(0.13, 0.05)
    tray(0.74, 0.07)
    for sx in (-1, 1):
        for sy in (-1, 1):
            px, py = sx * 0.44, sy * 0.19
            b.seg((px, py, 0.13), (px, py, 1.0 if sy > 0 else 0.92), 0.0185, G, seg=10)
            b.cyl((px, py, 0.13 - 0.004), 0.03, 0.012, G, seg=12, bev=0, amp=0.0)
            cx, cy = sx * 0.4, sy * 0.17
            b.box((cx, cy, 0.117), (0.05, 0.05, 0.008), G, bev=0.002, amp=0.0, cuts=0)
            for fx in (-0.016, 0.016):
                b.box((cx + fx, cy, 0.079), (0.004, 0.034, 0.075), G, bev=0.001, amp=0.0, cuts=0)
            b.cyl((cx, cy, 0.05), 0.05, 0.022, "M_Rubber", rot=(0, 90, 0), seg=18, bev=0, amp=0.0)
            b.cyl((cx, cy, 0.05), 0.009, 0.04, G, rot=(0, 90, 0), seg=8, bev=0, amp=0.0)
    b.seg((-0.44, 0.19, 1.0), (0.44, 0.19, 1.0), 0.0165, G, seg=10)                                  # barra de empuje
    b.seg((-0.44, -0.19, 0.92), (0.44, -0.19, 0.92), 0.012, G, seg=8)                                # barra delantera
    for sx in (-1, 1):
        b.cyl((sx * 0.36, 0.19, 1.0), 0.0215, 0.16, "M_Rubber", rot=(0, 90, 0), seg=12, bev=0, amp=0.0)   # puños
    # soporte de bolsa: aro de acero sujeto a los montantes del extremo +x y bolsa negra colgada
    hc = Vector((0.66, 0.0, 0.88))
    hr = 0.15
    ring = [hc + Vector((hr * math.cos(k * math.tau / 28), hr * math.sin(k * math.tau / 28), 0)) for k in range(29)]
    tube(b, ring, 0.006, G, seg=6, closed=True)
    for sy in (-1, 1):
        a = math.radians(55)
        tp = hc + Vector((-hr * math.cos(a), sy * hr * math.sin(a), 0))
        tube(b, [(0.44, sy * 0.19, 0.88), tuple(tp)], 0.007, G, seg=6)
    loft(b, [(0.34, 0.07, 0.06, 0.0), (0.4, 0.125, 0.115, 0.0), (0.55, 0.155, 0.145, 0.0), (0.75, 0.163, 0.153, 0.0), (0.9, 0.167, 0.157, 0.0), (0.925, 0.172, 0.162, 0.0)],
         "M_Plastic_Black", seg=24, cap_top=False, xf=Matrix.Translation((hc.x, 0.0, 0.0)))
    # bandeja superior: botellas y pulverizador
    zt = 0.74 + 0.014
    bottle(b, (-0.36, -0.05, zt), 0.27, 0.04, "M_Plastic_Blue")
    bottle(b, (-0.26, 0.08, zt), 0.24, 0.036, "M_Plastic_Green", "M_Plastic_Black", oy=0.7)
    bottle(b, (-0.12, -0.08, zt), 0.2, 0.045, "M_Plastic_Orange", "M_Plastic_White", oy=0.75)
    spray_bottle(b, (0.08, 0.04, zt), "M_Plastic_Green", rz=12)
    spray_bottle(b, (0.2, -0.04, zt), "M_Plastic_Blue", rz=-8)
    b.box((0.34, 0.0, zt + 0.06), (0.17, 0.13, 0.12), "M_Paper", bev=0.006, amp=0.0, cuts=0)           # caja de panos
    b.box((0.34, 0.0, zt + 0.121), (0.1, 0.05, 0.002), "M_Floor_Dark", bev=0, amp=0.0, cuts=0)         # ranura
    # bandeja inferior: pila de trapos y rollo
    zl = 0.13 + 0.014
    for k, (m, dx) in enumerate((("M_Fabric_Blue", 0.0), ("M_Fabric_Mustard", 0.01), ("M_Paper", -0.005), ("M_Fabric_Blue", 0.005))):
        b.box((-0.25 + dx, 0.0, zl + 0.012 + k * 0.024), (0.28, 0.2, 0.022), m, rot=(0, 0, 3 * k), bev=0.004, amp=0.0, cuts=0)
    b.cyl((0.12, 0.0, zl + 0.08), 0.07, 0.16, "M_Plastic_Black", seg=14, bev=0, amp=0.0)            # rollo de bolsas
    b.cyl((0.3, 0.0, zl + 0.07), 0.06, 0.14, "M_Plastic_Grey", seg=14, bev=0, amp=0.0)


def product_shelf(b, ln=1.5, h=1.9, d=0.4):
    """Estanteria metalica de almacen con productos de limpieza (garrafas, botellas, pulverizadores, cajas, rollos). Trasera en +y."""
    G = "M_Steel"
    for sx in (-ln / 2, ln / 2):
        for sy in (-d / 2 + 0.02, d / 2 - 0.02):
            b.box((sx, sy, h / 2), (0.04, 0.04, h), G, bev=0.004, amp=0.0, cuts=0)
    zs = [0.12, 0.56, 0.96, 1.36, 1.76]
    for z in zs:
        b.box((0, 0, z), (ln, d, 0.022), "M_Plastic_Grey", bev=0.004, amp=0.0, cuts=0)
        b.box((0, -d / 2 + 0.008, z + 0.02), (ln - 0.04, 0.012, 0.03), "M_Plastic_Grey", bev=0.003, amp=0.0, cuts=0)    # labio delantero
    for z in (0.2, 1.1, 1.65):                                                                          # travesanos traseros
        b.box((0, d / 2 - 0.02, z), (ln, 0.012, 0.025), G, bev=0.002, amp=0.0, cuts=0)
    t = lambda k: zs[k] + 0.011
    x0 = -ln / 2 + 0.1
    # estante 0: garrafas
    for k, m in enumerate(("M_Plastic_Blue", "M_Plastic_Green", "M_Plastic_Yellow", "M_Plastic_Blue", "M_Plastic_Orange")):
        jug(b, (x0 + 0.19 * k + 0.03, 0.0, t(0)), m)
    # estante 1: cajas y botellas
    b.box((x0 + 0.13, 0.0, t(1) + 0.1), (0.3, 0.3, 0.2), "M_Museum_AwningB", bev=0.006, amp=0.0, cuts=0)
    b.box((x0 + 0.13, 0.0, t(1) + 0.3), (0.26, 0.28, 0.2), "M_Paper", rot=(0, 0, 4), bev=0.006, amp=0.0, cuts=0)
    for k, (h_, r_, m) in enumerate(((0.3, 0.045, "M_Plastic_Red"), (0.28, 0.045, "M_Plastic_Blue"), (0.3, 0.045, "M_Plastic_Green"), (0.26, 0.042, "M_Plastic_Orange"))):
        bottle(b, (x0 + 0.5 + 0.2 * k, 0.0, t(1)), h_, r_, m)
    # estante 2: pulverizadores y botellas ovaladas
    for k, m in enumerate(("M_Plastic_Green", "M_Plastic_Blue", "M_Plastic_Red", "M_Plastic_Yellow")):
        spray_bottle(b, (x0 + 0.1 * k + 0.02, 0.0, t(2)), m, rz=0)
    for k, m in enumerate(("M_Plastic_Blue", "M_Plastic_Green", "M_Plastic_Grey")):
        bottle(b, (x0 + 0.55 + 0.17 * k, 0.0, t(2)), 0.25, 0.05, m, "M_Plastic_Black", oy=0.62)
    # estante 3: rollos de papel y de bolsas
    for k in range(4):
        b.cyl((x0 + 0.1 + 0.2 * k, 0.0, t(3) + 0.12), 0.07, 0.24, "M_Paper", seg=16, bev=0, amp=0.0)
    for k in range(2):
        b.cyl((x0 + 0.95 + 0.17 * k, 0.0, t(3) + 0.07), 0.075, 0.14, "M_Plastic_Black", seg=16, bev=0, amp=0.0)
    # estante 4: trapos y esponjas
    for k, m in enumerate(("M_Fabric_Blue", "M_Fabric_Mustard", "M_Fabric_Blue", "M_Paper")):
        b.box((x0 + 0.15, 0.0, t(4) + 0.011 + 0.022 * k), (0.34, 0.26, 0.02), m, rot=(0, 0, 2 * k), bev=0.004, amp=0.0, cuts=0)
    for k in range(3):
        b.box((x0 + 0.62 + 0.12 * k, 0.0, t(4) + 0.03), (0.1, 0.07, 0.06), "M_Plastic_Yellow", bev=0.006, amp=0.0, cuts=0)
        b.box((x0 + 0.62 + 0.12 * k, 0.0, t(4) + 0.068), (0.1, 0.07, 0.016), "M_Plastic_Green", bev=0.004, amp=0.0, cuts=0)


def utility_sink(b):
    """Pila profunda de laboreo con patas de acero, salpicadero, grifo mural de cuello de cisne, sifon a la pared. Trasera en y=0, frente -y."""
    C, G = "M_Ceramic", "M_Steel"
    W, D, zr, zb = 0.62, 0.46, 0.86, 0.52
    h = zr - zb
    b.box((0, -D + 0.0125, zb + h / 2), (W, 0.025, h), C, bev=0.004, amp=0.0, cuts=0)
    b.box((0, -0.0125, zb + h / 2), (W, 0.025, h), C, bev=0.004, amp=0.0, cuts=0)
    for sx in (-1, 1):
        b.box((sx * (W / 2 - 0.0125), -D / 2, zb + h / 2), (0.025, D - 0.05, h), C, bev=0.004, amp=0.0, cuts=0)
    b.box((0, -D / 2, zb + 0.015), (W - 0.05, D - 0.05, 0.03), C, bev=0.004, amp=0.0, cuts=0)
    b.box((0, -D - 0.0075, zr - 0.01), (W + 0.03, 0.03, 0.02), C, bev=0.006, amp=0.0, cuts=0)       # borde delantero
    for sx in (-1, 1):
        b.box((sx * (W / 2 + 0.0075), -D / 2, zr - 0.01), (0.03, D + 0.03, 0.02), C, bev=0.006, amp=0.0, cuts=0)
    b.box((0, -0.0125, zr - 0.01), (W + 0.03, 0.03, 0.02), C, bev=0.006, amp=0.0, cuts=0)
    b.box((0, -0.015, zr + 0.09), (W + 0.03, 0.03, 0.18), C, bev=0.006, amp=0.0, cuts=0)           # salpicadero
    b.cyl((0, -D / 2, zb + 0.032), 0.04, 0.004, "M_Floor_Dark", seg=20, bev=0, amp=0.0)             # desague
    b.cyl((0, -D / 2, zb + 0.0345), 0.047, 0.004, G, seg=20, bev=0, amp=0.0)
    for sx in (-1, 1):
        for sy in (-0.045, -D + 0.045):
            b.seg((sx * (W / 2 - 0.035), sy, 0.0), (sx * (W / 2 - 0.035), sy, zb), 0.0215, G, seg=10)
            b.cyl((sx * (W / 2 - 0.035), sy, 0.006), 0.032, 0.012, G, seg=12, bev=0, amp=0.0)
    for sy in (-0.045, -D + 0.045):
        b.seg((-(W / 2 - 0.035), sy, 0.2), (W / 2 - 0.035, sy, 0.2), 0.011, G, seg=8)
    for sx in (-1, 1):
        b.seg((sx * (W / 2 - 0.035), -0.045, 0.2), (sx * (W / 2 - 0.035), -D + 0.045, 0.2), 0.011, G, seg=8)
    # sifon a la pared
    tube(b, [(0, -D / 2, zb + 0.03), (0, -D / 2, 0.36), (0, -D / 2 + 0.05, 0.31), (0, -0.2, 0.31), (0, -0.04, 0.34), (0, -0.0, 0.34)], 0.017, G, seg=10)
    # grifo mural
    zt = 1.26
    b.box((0, -0.01, zt), (0.2, 0.02, 0.07), G, bev=0.005, amp=0.0, cuts=0)
    for sx in (-1, 1):
        b.cyl((sx * 0.07, -0.03, zt), 0.017, 0.03, G, rot=(90, 0, 0), seg=12, bev=0, amp=0.0)
        b.box((sx * 0.07, -0.05, zt), (0.05, 0.016, 0.014), "M_Plastic_Blue" if sx < 0 else "M_Plastic_Red", bev=0.003, amp=0.0, cuts=0)
    tube(b, [(0, -0.015, zt), (0, -0.09, zt + 0.02), (0, -0.16, zt + 0.0), (0, -0.19, zt - 0.06), (0, -0.19, zt - 0.1)], 0.0125, G, seg=10)


def tool_rack(b):
    """Panel de herramientas de pared: tablero de madera con listones, ganchos y herramientas (martillo, serrucho, llave, alicates,
    destornilladores, cuerda, cinta metrica). Trasera en y=0, frente -y, centro en z=0."""
    wd = "M_Museum_Wood"
    b.box((0, -0.01, 0), (1.0, 0.02, 0.7), wd, bev=0.004, amp=0.0, cuts=0)
    for sz in (-0.35, 0.35):
        b.box((0, -0.025, sz), (1.04, 0.05, 0.035), "M_Museum_WoodDark", bev=0.006, amp=0.0, cuts=0)
    for sx in (-0.5, 0.5):
        b.box((sx, -0.025, 0), (0.035, 0.05, 0.7), "M_Museum_WoodDark", bev=0.006, amp=0.0, cuts=0)
    for z in (0.22, -0.12):
        b.box((0, -0.0275, z), (0.94, 0.015, 0.03), "M_Steel", bev=0.002, amp=0.0, cuts=0)
    ty = -0.052     # plano de las herramientas

    def peg(x, z):
        b.cyl((x, -0.0475, z), 0.0065, 0.055, "M_Steel", rot=(90, 0, 0), seg=8, bev=0, amp=0.0)
    # martillo
    peg(-0.38, 0.2)
    b.box((-0.38, ty - 0.006, 0.02), (0.03, 0.012, 0.3), "M_Museum_Wood", bev=0.004, amp=0.0, cuts=0)
    b.box((-0.38, ty - 0.006, 0.19), (0.12, 0.014, 0.045), "M_Steel", bev=0.004, amp=0.0, cuts=0)
    b.prism([(-0.32, ty, 0.2125), (-0.3, ty, 0.21), (-0.285, ty, 0.19), (-0.32, ty, 0.19)], (0, -0.012, 0), "M_Steel", amp=0.0)     # orejas del martillo
    # serrucho (cuelga de la empunadura)
    peg(-0.16, 0.22)
    b.prism([(-0.2, ty, 0.2), (-0.12, ty, 0.2), (-0.14, ty, -0.22), (-0.185, ty, -0.22)], (0, -0.003, 0), "M_Steel", amp=0.0)
    for k in range(0, 14):    # dientes sobre el canto izquierdo de la hoja
        zz = 0.18 - k * 0.028
        xe = lambda z_: -0.2 + 0.015 * (0.2 - z_) / 0.42
        b.prism([(xe(zz), ty, zz), (xe(zz) - 0.011, ty, zz - 0.012), (xe(zz - 0.014), ty, zz - 0.014)], (0, -0.003, 0), "M_Steel", amp=0.0)
    for (x, z, sx, sz) in ((-0.16, 0.255, 0.1, 0.02), (-0.16, 0.185, 0.1, 0.02), (-0.205, 0.22, 0.02, 0.09), (-0.115, 0.22, 0.02, 0.09)):
        b.box((x, ty - 0.006, z), (sx, 0.012, sz), "M_Museum_WoodDark", bev=0.003, amp=0.0, cuts=0)
    # llave inglesa
    peg(0.08, 0.2)
    b.box((0.08, ty - 0.005, 0.0), (0.028, 0.01, 0.4), "M_Steel", bev=0.004, amp=0.0, cuts=0)
    b.box((0.08, ty - 0.005, 0.2), (0.07, 0.012, 0.06), "M_Steel", bev=0.004, amp=0.0, cuts=0)
    b.box((0.08, ty - 0.005, 0.238), (0.032, 0.012, 0.03), "M_Floor_Dark", bev=0, amp=0.0, cuts=0)
    # alicates
    peg(0.24, 0.2)
    for sg in (-1, 1):
        b.box((0.24 + sg * 0.014, ty - 0.005, 0.03), (0.022, 0.01, 0.34), "M_Plastic_Red", rot=(0, sg * 3, 0), bev=0.004, amp=0.0, cuts=0)
    b.box((0.24, ty - 0.005, 0.2), (0.06, 0.012, 0.06), "M_Steel", bev=0.004, amp=0.0, cuts=0)
    # destornilladores
    for k, (x, m) in enumerate(((0.36, "M_Plastic_Yellow"), (0.43, "M_Plastic_Blue"))):
        peg(x, 0.17)
        b.box((x, ty - 0.006, 0.08), (0.026, 0.026, 0.14), m, bev=0.008, amp=0.0, cuts=0)
        b.box((x, ty - 0.006, -0.1), (0.008, 0.008, 0.22), "M_Steel", bev=0.001, amp=0.0, cuts=0)
        b.box((x, ty - 0.006, -0.215), (0.012, 0.01, 0.014), "M_Steel", bev=0.001, amp=0.0, cuts=0)
    # fila inferior: cuerda en rollo y cinta metrica
    peg(-0.3, -0.04)
    ring = [(-0.3 + 0.075 * math.cos(k * math.tau / 20), ty - 0.006, -0.15 + 0.075 * math.sin(k * math.tau / 20)) for k in range(21)]
    tube(b, ring, 0.013, "M_Bristle", seg=6, closed=True)
    ring2 = [(-0.3 + 0.062 * math.cos(k * math.tau / 20), ty - 0.006, -0.15 + 0.062 * math.sin(k * math.tau / 20)) for k in range(21)]
    tube(b, ring2, 0.011, "M_Bristle", seg=6, closed=True)
    peg(0.1, -0.08)
    b.cyl((0.1, ty - 0.01, -0.2), 0.06, 0.03, "M_Plastic_Yellow", rot=(90, 0, 0), seg=18, bev=0, amp=0.0)
    b.box((0.1, ty - 0.01, -0.15), (0.034, 0.03, 0.05), "M_Steel", bev=0.003, amp=0.0, cuts=0)
    # llaves de hierro colgando de un gancho
    peg(0.36, -0.1)
    for k in range(2):
        b.box((0.36 + 0.02 * k, ty - 0.006, -0.19 - 0.02 * k), (0.012, 0.006, 0.17), "M_Steel", bev=0.002, amp=0.0, cuts=0)


def fluorescent(b, x, y, zc, ln=1.2, wd=0.2, axis='x'):
    """Luminaria fluorescente de superficie: chapa de montaje, bandeja con dos tubos, tapas y difusor prismatico estriado. zc = techo."""
    W = "M_Track_White"
    sx, sy = (ln, wd) if axis == 'x' else (wd, ln)

    u = (lambda a, c: (x + a, y + c)) if axis == 'x' else (lambda a, c: (x + c, y + a))
    def put(a, c, z, la, lc, lz, mat, **kw):
        px, py = u(a, c)
        b.box((px, py, zc + z), (la, lc, lz) if axis == 'x' else (lc, la, lz), mat, **kw)
    put(0, 0, -0.012, ln, wd, 0.024, W, bev=0, amp=0.0, cuts=0)                      # chapa de montaje
    for sg in (-1, 1):
        put(0, sg * (wd / 2 - 0.007), -0.05, ln, 0.014, 0.05, W, bev=0, amp=0.0, cuts=0)    # laterales de la bandeja
    for sg in (-1, 1):
        put(sg * (ln / 2 - 0.007), 0, -0.05, 0.014, wd, 0.05, W, bev=0, amp=0.0, cuts=0)    # tapas de los extremos
        for tc in (-0.045, 0.045):
            put(sg * (ln / 2 - 0.045), tc, -0.05, 0.03, 0.03, 0.03, "M_Plastic_Grey", bev=0, amp=0.0, cuts=0)   # portalamparas
    for tc in (-0.045, 0.045):
        px, py = u(0, tc)
        b.cyl((px, py, zc - 0.05), 0.0155, ln - 0.1, "M_Bulb_Cool", rot=((0, 90, 0) if axis == 'x' else (90, 0, 0)), seg=10, bev=0, amp=0.0)
    put(0, 0, -0.078, ln - 0.02, wd - 0.03, 0.008, "M_Bulb_Cool", bev=0, amp=0.0, cuts=0)       # difusor
    n = int((ln - 0.1) / 0.12)
    for k in range(n + 1):
        put(-ln / 2 + 0.05 + k * (ln - 0.1) / n, 0, -0.0845, 0.006, wd - 0.03, 0.005, W, bev=0, amp=0.0, cuts=0)    # estrias
    for sg in (-1, 1):
        put(0, sg * (wd / 2 - 0.011), -0.0775, ln, 0.008, 0.012, W, bev=0, amp=0.0, cuts=0)       # marco del difusor


def step_ladder(b):
    for sx in (-0.22, 0.22):
        b.seg((sx, -0.05, 0), (sx, 0.16, 1.5), 0.02, "M_Museum_Wood")
        b.seg((sx, 0.32, 0), (sx, 0.2, 1.48), 0.018, "M_Museum_Wood")
    for k in range(1, 5):
        t = k / 5
        b.box((0, -0.05 + 0.21 * t, 1.5 * t), (0.44, 0.08, 0.025), "M_Museum_Wood", bev=0.004, amp=0.002, cuts=0)


def toilet(b):
    """Inodoro clasico estilizado de ceramica. Local: la cisterna al fondo (+y), el frente hacia -y; base en z=0 (sin bolas)."""
    c = "M_Ceramic"
    # pedestal + taza en un solo loft: sube por fuera (pie oval, cuello estrecho, vuelo hasta el borde) y baja por dentro hasta el agua
    loft(b, [(0.0, 0.12, 0.16, -0.02), (0.12, 0.10, 0.14, -0.03), (0.25, 0.15, 0.21, -0.065), (0.38, 0.18, 0.24, -0.08), (0.40, 0.18, 0.24, -0.08),
             (0.40, 0.14, 0.19, -0.08), (0.35, 0.115, 0.155, -0.07), (0.30, 0.09, 0.12, -0.06)], c, seg=24)
    loft(b, [(0.302, 0.088, 0.118, -0.06), (0.306, 0.088, 0.118, -0.06)], "M_Glass_Mirror", seg=20)     # agua
    # asiento: aro plano oval sobre el borde, algo mas grande que la taza
    loft(b, [(0.401, 0.195, 0.25, -0.08), (0.421, 0.195, 0.25, -0.08), (0.421, 0.145, 0.195, -0.08), (0.401, 0.145, 0.195, -0.08)],
         "M_Museum_WoodDark", seg=24, closed=True)
    # tapa abierta: losa oval apoyada contra la cisterna (inclinada 10 grados, 5 mm de holgura con la cara frontal)
    loft(b, [(-0.01, 0.18, 0.19, 0.0), (0.01, 0.18, 0.19, 0.0)], c, seg=20,
         xf=Matrix.Translation((0, 0.1272, 0.619)) @ Matrix.Rotation(math.radians(80), 4, 'X'))
    b.box((0, 0.17, 0.375), (0.26, 0.16, 0.15), c, bev=0.01, amp=0.0, cuts=0)                       # conector taza-cisterna
    b.box((0, 0.26, 0.63), (0.38, 0.17, 0.36), c, bev=0.035, amp=0.0, cuts=0)                       # cisterna
    b.box((0, 0.26, 0.825), (0.41, 0.2, 0.03), c, bev=0.01, amp=0.0, cuts=0)                        # tapa de la cisterna
    b.cyl((0, 0.26, 0.845), 0.025, 0.01, "M_Museum_Metal", seg=12, bev=0, amp=0.0)                  # pulsador cromado


def mirror(b, w=0.55, h=0.75, fw=0.07):
    """Espejo con marco de madera. Local: cara trasera en y=0, frente hacia -y."""
    b.box((0, -0.01, 0), (w, 0.02, h), "M_Glass_Mirror", bev=0.004, amp=0.0, cuts=0)
    for (x, z, sx, sz) in ((-(w + fw) / 2, 0, fw, h + 2 * fw), ((w + fw) / 2, 0, fw, h + 2 * fw), (0, (h + fw) / 2, w, fw), (0, -(h + fw) / 2, w, fw)):
        b.box((x, -0.02, z), (sx, 0.04, sz), "M_Museum_Wood", bev=0.01, amp=0.002, cuts=0)


def paper_holder(b):
    """Portarrollos de pared: placa, dos brazos y rollo. Cara trasera en y=0."""
    b.box((0, -0.006, 0), (0.16, 0.012, 0.14), "M_Museum_Metal", bev=0.003, amp=0.0, cuts=0)
    for sx in (-0.06, 0.06):
        b.box((sx, -0.04, 0), (0.012, 0.06, 0.02), "M_Museum_Metal", bev=0.002, amp=0.0, cuts=0)
    b.cyl((0, -0.07, 0), 0.055, 0.108, "M_Paper", rot=(0, 90, 0), seg=16, bev=0, amp=0.0)


def coat_hook(b):
    b.box((0, -0.006, 0), (0.04, 0.012, 0.12), "M_Museum_Brass", bev=0.003, amp=0.0, cuts=0)
    b.seg((0, -0.012, -0.03), (0, -0.065, -0.03), 0.008, "M_Museum_Brass", seg=6)
    b.seg((0, -0.065, -0.03), (0, -0.065, 0.0), 0.008, "M_Museum_Brass", seg=6)
    b.cyl((0, -0.065, 0.008), 0.014, 0.016, "M_Museum_Brass", seg=8, bev=0, amp=0.0)


def toilet_brush(b):
    """Escobilla en su soporte de ceramica: vaso torneado (pie con anillo, cuerpo ligeramente abierto, labio redondeado, interior hueco), cabeza de
    cerdas dentro, varilla de acero y empunadura torneada con anilla para colgar (un solo aro)."""
    cup = [(0.0, 0.046), (0.004, 0.052), (0.012, 0.0535), (0.02, 0.05), (0.034, 0.0525), (0.08, 0.056), (0.13, 0.0595), (0.15, 0.0615), (0.158, 0.0635),
           (0.1625, 0.0615), (0.1625, 0.056), (0.156, 0.054), (0.12, 0.0515), (0.06, 0.047), (0.04, 0.0435)]
    loft(b, [(z, r, r, 0.0) for (z, r) in cup], "M_Ceramic", seg=24)                                                   # vaso hueco
    loft(b, [(z, r, r, 0.0) for (z, r) in ((0.041, 0.0415), (0.0415, 0.0412))], "M_Floor_Dark", seg=20)              # fondo oscuro del vaso
    loft(b, [(z, r, r, 0.0) for (z, r) in ((0.04, 0.012), (0.05, 0.03), (0.075, 0.036), (0.1, 0.031), (0.125, 0.018), (0.135, 0.007))], "M_Bristle", seg=14)   # cabeza de cerdas
    b.seg((0, 0, 0.12), (0, 0, 0.36), 0.0055, "M_Steel", seg=8)                                                        # varilla
    loft(b, [(z, r, r, 0.0) for (z, r) in ((0.34, 0.0085), (0.346, 0.0125), (0.356, 0.0135), (0.37, 0.0115), (0.40, 0.0125), (0.43, 0.014), (0.448, 0.0135),
                                           (0.456, 0.0095), (0.46, 0.006))], "M_Museum_WoodDark", seg=12)             # empunadura torneada
    n, rr, zc = 12, 0.015, 0.4755
    pts = [(rr * math.cos(k * math.tau / n), 0, zc + rr * math.sin(k * math.tau / n)) for k in range(n + 1)]
    tube(b, pts, 0.003, "M_Steel", seg=6, closed=True)                                                                 # anilla para colgar (plano x-z)


def pedal_bin(b, r=0.11, h=0.3):
    """Cubo con pedal de acero inoxidable: aro de goma, cuerpo ligeramente abierto con labio, tapa abombada con borde, bisagra trasera con soporte y
    nudillo, y pedal con varilla articulada al pie del cuerpo (el pedal sale por -y)."""
    st, rb = "M_Steel", "M_Rubber"
    loft(b, [(0.0, r * 0.9, r * 0.9, 0.0), (0.014, r * 0.92, r * 0.92, 0.0), (0.02, r * 0.95, r * 0.95, 0.0)], rb, seg=24)    # aro de goma
    prof = [(0.02, r * 0.97), (0.04, r * 0.985), (h * 0.55, r * 1.0), (h - 0.02, r * 1.04), (h - 0.008, r * 1.05), (h, r * 1.04), (h, r * 1.0), (h - 0.02, r * 0.98)]
    loft(b, [(z, rr, rr, 0.0) for (z, rr) in prof], st, seg=24, cap_top=False)                                          # cuerpo con labio (abierto por arriba)
    lid = [(h + 0.002, r * 1.075), (h + 0.01, r * 1.08), (h + 0.016, r * 1.06), (h + 0.026, r * 0.98), (h + 0.04, r * 0.82), (h + 0.05, r * 0.6), (h + 0.057, r * 0.36), (h + 0.06, r * 0.1)]
    loft(b, [(z, rr, rr, 0.0) for (z, rr) in lid], st, seg=24)                                                          # tapa abombada
    rbox(b, (0, r + 0.016, h - 0.012), (0.07, 0.026, 0.05), 0.006, st, segs=1)                                          # soporte de la bisagra en el cuerpo
    b.cyl((0, r + 0.03, h + 0.016), 0.0095, 0.07, st, rot=(0, 90, 0), seg=12, bev=0, amp=0.0)                          # nudillo de la bisagra
    rbox(b, (0, r + 0.018, h + 0.017), (0.056, 0.036, 0.012), 0.003, st, segs=1)                                       # oreja de la tapa
    b.box((0, -r - 0.006, 0.034), (0.052, 0.024, 0.045), st, bev=0.004, amp=0.0, cuts=0)                               # soporte del pedal pegado al cuerpo
    b.seg((0, -r - 0.014, 0.032), (0, -r - 0.058, 0.024), 0.0055, st, seg=8)                                           # varilla del pedal
    rbox(b, (0, -r - 0.07, 0.019), (0.075, 0.05, 0.014), 0.004, "M_Plastic_Black", segs=1)                              # pedal
    for sx in (-1, 1):
        b.box((sx * 0.026, -r - 0.02, 0.026), (0.006, 0.03, 0.02), st, bev=0.0015, amp=0.0, cuts=0)                    # costillas del pedal


def hand_dryer(b):
    """Secador de manos de pared (0.28 x 0.2 x 0.3). Cara trasera en y=0."""
    b.box((0, -0.1, 0), (0.28, 0.2, 0.3), "M_Ceramic", bev=0.03, amp=0.001, cuts=0)
    b.cyl((0, -0.1, -0.19), 0.03, 0.08, "M_Museum_Metal", seg=10, r2=0.04, bev=0, amp=0.0)
    b.box((0, -0.202, 0.06), (0.05, 0.006, 0.03), "M_Museum_Metal", bev=0.002, amp=0.0, cuts=0)


def vanity(b):
    """Tocador de un seno (0.7 x 0.47): zocalo, cuerpo con puerta, encimera ceramica con seno hundido, grifo y dosificador.
    Trasera en y=0, frente -y, base z=0."""
    W, D = 0.7, 0.47
    wd, wo = "M_Museum_WoodDark", "M_Museum_Wood"
    b.box((0, -D / 2 + 0.01, 0.04), (W - 0.04, D - 0.06, 0.08), wd, bev=0.004, amp=0.0, cuts=0)                  # zocalo retranqueado
    b.box((0, -D / 2, 0.43), (W, D, 0.7), wd, bev=0.006, amp=0.0, cuts=1)                                         # cuerpo
    b.box((0, -D - 0.01, 0.43), (W - 0.06, 0.02, 0.62), wo, bev=0.008, amp=0.0, cuts=0)                           # puerta
    b.box((0, -D - 0.0205, 0.43), (W - 0.18, 0.006, 0.5), wd, bev=0, amp=0.0, cuts=0)                              # entrepano hundido
    b.box((0.24, -D - 0.03, 0.62), (0.02, 0.02, 0.1), "M_Museum_Brass", bev=0.003, amp=0.0, cuts=0)               # tirador
    b.box((0, -(D + 0.02) / 2, 0.815), (W + 0.02, D + 0.02, 0.07), "M_Ceramic", bev=0.01, amp=0.0, cuts=1)        # encimera
    b.cyl((0, -0.29, 0.854), 0.17, 0.008, "M_Ceramic", seg=24, bev=0, amp=0.0)                                    # borde del seno
    b.cyl((0, -0.29, 0.86), 0.145, 0.004, "M_Floor_Dark", seg=24, bev=0, amp=0.0)                                 # fondo del seno (hundido)
    b.box((0, -0.01, 0.9), (W + 0.02, 0.02, 0.1), "M_Ceramic", bev=0.004, amp=0.0, cuts=0)                        # salpicadero
    b.cyl((0, -0.07, 0.88), 0.022, 0.06, "M_Museum_Brass", seg=8, bev=0, amp=0.0)                                 # base del grifo
    tube(b, [(0, -0.07, 0.9), (0, -0.07, 0.96), (0, -0.09, 0.995), (0, -0.14, 0.985), (0, -0.17, 0.95)], 0.0125, "M_Museum_Brass", seg=8)
    for sx in (-1, 1):
        b.box((sx * 0.055, -0.07, 0.905), (0.04, 0.02, 0.02), "M_Museum_Brass", bev=0.003, amp=0.0, cuts=0)       # manetas
    b.cyl((0.25, -0.1, 0.92), 0.028, 0.12, "M_Ceramic", seg=10, bev=0, amp=0.0)                                   # dosificador de jabon
    tube(b, [(0.25, -0.1, 0.98), (0.25, -0.1, 1.0), (0.25, -0.12, 1.0)], 0.005, "M_Museum_Metal", seg=5)


def pictogram_fig(b, kind, h, y, ox=0.0, oz=0.0, mat="M_Sign_Letters", t=0.004):
    """Figura de aseo en el plano x-z (cara en y): 'M' hombre (cabeza de 24 lados, torso rectangular, dos brazos, dos piernas rectas)
    o 'W' mujer (cabeza, vestido triangular, dos brazos, dos piernas). h = alto total; centrada en (ox, oz); espesor t hacia -y."""
    def poly(pts):
        b.prism([(ox + u * h, y, oz + v * h) for (u, v) in pts], (0, -t, 0), mat, amp=0.0)

    def rect(u0, v0, u1, v1):
        poly([(u0, v0), (u1, v0), (u1, v1), (u0, v1)])
    poly([(0.085 * math.cos(k * math.tau / 24), 0.415 + 0.085 * math.sin(k * math.tau / 24)) for k in range(24)])      # cabeza
    if kind == 'M':
        rect(-0.13, 0.0, 0.13, 0.30)                                                  # torso
        rect(0.145, 0.02, 0.22, 0.30)                                                 # brazos
        rect(-0.22, 0.02, -0.145, 0.30)
        rect(0.015, -0.5, 0.13, 0.0)                                                  # piernas
        rect(-0.13, -0.5, -0.015, 0.0)
    else:
        poly([(-0.10, 0.30), (0.10, 0.30), (0.23, -0.17), (-0.23, -0.17)])             # vestido triangular
        rect(0.125, 0.06, 0.19, 0.30)                                                 # brazos
        rect(-0.19, 0.06, -0.125, 0.30)
        rect(0.02, -0.5, 0.085, -0.17)                                                # piernas
        rect(-0.085, -0.5, -0.02, -0.17)


def pictogram_plate(b, kind, size, y=0.0, ox=0.0, oz=0.0):
    """Placa cuadrada de tablero oscuro con filete claro y la figura (70% del alto). Trasera en y."""
    b.box((ox, y - 0.009, oz), (size, 0.018, size), "M_Sign_Board", bev=0.004, amp=0.0, cuts=0)
    inset, lw = size * 0.05, size * 0.026
    a = size / 2 - inset
    for sg in (-1, 1):
        b.box((ox + sg * (a - lw / 2), y - 0.0195, oz), (lw, 0.003, 2 * a), "M_Sign_Letters", bev=0, amp=0.0, cuts=0)
        b.box((ox, y - 0.0195, oz + sg * (a - lw / 2)), (2 * a - 2 * lw, 0.003, lw), "M_Sign_Letters", bev=0, amp=0.0, cuts=0)
    pictogram_fig(b, kind, size * 0.7, y - 0.018, ox, oz, t=0.004)


def pictogram_sign(name, kind, axis, face, s, u, z, coll):
    """Placa de aseo de pared 0.30 x 0.30 (kind 'M' hombre / 'W' mujer) sobre cuatro separadores de laton."""
    rot = {('x', 1): 180, ('x', -1): 0, ('y', 1): 90, ('y', -1): -90}[(axis, s)]
    pos = (u, face, z) if axis == 'x' else (face, u, z)

    def fn(b):
        standoffs(b, 0.3, 0.3, 0.014, 0.018, 0.02)
        pictogram_plate(b, kind, 0.3, y=-0.014)
    return to_col(prop("Sign_" + name, pos, rot, fn), coll)


# Hojas de puerta: el pivote queda sobre la linea de la jamba (a LEAF_UOFF del forro) y a LEAF_STAND de la cara del muro (la hoja abierta
# pasa por delante del arquitrabe sin tocarlo); una placa de bisagra fija al forro (hinge_plates) une el nudillo con el marco.
LEAF_STAND, LEAF_UOFF, LEAF_CLR, SADDLE = 0.022, 0.0045, 0.004, 0.005
HINGE = {"StairHall_Restrooms": (-1, -1), "Restroom_1": (1, 1), "Restroom_2": (-1, 1), "StairHall_Maintenance": (1, 1)}   # (jamba con bisagra, lado del tabique de la hoja abierta)
LEAF_NAME = {"StairHall_Maintenance": "Maintenance"}


def leaf_spec(dn):
    """Pivote, angulo y medidas de la hoja abierta de una puerta de tabique (hueco = DOORS; el forro interior deja 0.04 por lado)."""
    ax, fx, c, w, zs, zt, nm, kind = next(d for d in DOORS if d[6] == dn)
    th = next(p[3] for p in PARTS if p[1] == ax and p[2] == fx)
    jam, side = HINGE[dn]
    ul = c + jam * (w / 2 - 0.04)                        # cara interior del forro en la jamba con bisagra
    pu, pn = ul - jam * LEAF_UOFF, fx + side * (th / 2 + LEAF_STAND)
    z0 = zs + SADDLE + 0.003
    sp = dict(ax=ax, jam=jam, side=side, ul=ul, z0=z0, wl=w - 0.08 - LEAF_CLR, hl=zt - 0.04 - z0 - 0.003, Lp=LEAF_STAND + 0.03,
              pivot=((pn, pu, z0) if ax == 'y' else (pu, pn, z0)))
    sp["ang"] = (0 if side > 0 else 180) if ax == 'y' else (90 if side > 0 else -90)
    return sp


def hinge_plates(b, sp):
    """Placas de bisagra del lado del marco: tira de laton atornillada al forro de la jamba que llega hasta el nudillo de la hoja."""
    px, py, z0 = sp["pivot"]
    Lp, t = sp["Lp"], 0.004
    ut = sp["ul"] - sp["jam"] * t / 2                    # centro de la placa (apoyada en el forro, del lado del hueco)
    for zz in (0.22, sp["hl"] / 2, sp["hl"] - 0.22):
        if sp["ax"] == 'y':
            c = (px - sp["side"] * Lp / 2, ut, z0 + zz)
            b.box(c, (Lp, t, 0.1), "M_Museum_Brass", bev=0.001, amp=0.0, cuts=0)
            for k in (0.4, 0.8):
                b.cyl((px - sp["side"] * Lp * k, ut - sp["jam"] * t / 2 - sp["jam"] * 0.0008, z0 + zz), 0.0045, 0.0026, "M_Museum_Brass", rot=(90, 0, 0), seg=8, bev=0, amp=0.0)
        else:
            c = (ut, py - sp["side"] * Lp / 2, z0 + zz)
            b.box(c, (t, Lp, 0.1), "M_Museum_Brass", bev=0.001, amp=0.0, cuts=0)
            for k in (0.4, 0.8):
                b.cyl((ut - sp["jam"] * t / 2 - sp["jam"] * 0.0008, py - sp["side"] * Lp * k, z0 + zz), 0.0045, 0.0026, "M_Museum_Brass", rot=(0, 90, 0), seg=8, bev=0, amp=0.0)


def door_leaf(name, hinge, w, h, ang, mat="M_Museum_Wood", coll=None, sign_text=None, lock=False, push=False, pictogram=None):
    """Hoja de puerta con el pivote en la bisagra (para animar en Unity). Local: se extiende hacia +x (w = ancho de la hoja, h = alto).
    Herrajes en ambas caras (maneta con roseta, escudo de llave, 3 bisagras); lock = pestillo/indicador; push = placa de empuje."""
    brass = "M_Museum_Brass"
    x0c = w / 2 - (LEAF_UOFF - 0.002)                  # centro de la hoja: su canto de bisagra queda a 2 mm del forro

    def fn(b):
        b.box((x0c, 0, h / 2), (w, 0.045, h), mat, bev=0.012, amp=0.003, cuts=2)
        for zz, hh in ((h * 0.27, h * 0.36), (h * 0.73, h * 0.34)):
            for s in (-1, 1):
                b.box((x0c, s * 0.025, zz), (w - 0.22, 0.012, hh), "M_Museum_WoodDark", bev=0.006, amp=0.002, cuts=0)
        hz, x0 = 1.05, w - 0.075            # altura y eje de la maneta
        for s in (-1, 1):
            b.cyl((x0, s * 0.036, hz), 0.028, 0.01, brass, rot=(90, 0, 0), seg=14, bev=0, amp=0.0)    # roseta
            b.cyl((x0, s * 0.049, hz), 0.009, 0.016, brass, rot=(90, 0, 0), seg=8, bev=0, amp=0.0)    # cuello
            b.box((x0 - 0.05, s * 0.064, hz), (0.12, 0.014, 0.02), brass, bev=0.004, amp=0.0, cuts=0)  # palanca hacia la bisagra
            b.box((x0, s * 0.034, hz - 0.1), (0.028, 0.006, 0.06), brass, bev=0.002, amp=0.0, cuts=0)  # escudo de llave
            b.box((x0, s * 0.038, hz - 0.1), (0.008, 0.003, 0.016), "M_Floor_Dark", bev=0, amp=0.0, cuts=0)
            for zz in (0.22, h / 2, h - 0.22):   # bisagra de mariposa: plato fino + nudillo vertical
                b.box((0.035, s * 0.0245, zz), (0.06, 0.004, 0.11), brass, bev=0.001, amp=0.0, cuts=0)
        for zz in (0.22, h / 2, h - 0.22):
            b.cyl((0.0, 0, zz), 0.011, 0.11, brass, seg=8, bev=0, amp=0.0)
        if lock:
            b.cyl((x0, -0.036, hz + 0.1), 0.024, 0.01, brass, rot=(90, 0, 0), seg=12, bev=0, amp=0.0)    # pomo del pestillo (cara -y)
            b.box((x0, -0.047, hz + 0.1), (0.05, 0.012, 0.014), brass, bev=0.003, amp=0.0, cuts=0)
            b.box((x0 - 0.011, 0.034, hz + 0.1), (0.022, 0.006, 0.034), "M_Rug_Terracotta", bev=0, amp=0.0, cuts=0)  # indicador ocupado/libre (cara +y)
            b.box((x0 + 0.011, 0.034, hz + 0.1), (0.022, 0.006, 0.034), "M_Paper", bev=0, amp=0.0, cuts=0)
        if push:
            b.box((x0 - 0.04, 0.034, hz + 0.3), (0.1, 0.006, 0.28), brass, bev=0.002, amp=0.0, cuts=0)    # placa de empuje (cara +y)
        if pictogram:   # placa de 0.18 con la figura, a la altura de los ojos, en la cara que da al vestibulo (-y)
            pictogram_plate(b, pictogram, 0.18, -0.031, w / 2, 1.55)
    # la hoja es un prop, pero los marcos estan deformados (warp): se deforma la malla igual que el muro para que la hoja siga
    # pegada a su jamba a cualquier altura (el objeto conserva el pivote en la bisagra y la rotacion de la hoja abierta)
    hv = Vector(hinge)
    hw = L.warp(hv)
    b = HB("Door_" + name, 1.0, warp=False)
    fn(b)
    ob = b.finish()
    ob.location = hw
    ob.rotation_euler.z = math.radians(ang)
    R = Matrix.Rotation(math.radians(ang), 3, 'Z')
    Ri = R.inverted()
    for v in ob.data.vertices:
        v.co = Ri @ (L.warp(hv + R @ v.co) - hw)
    return to_col(ob, coll)


def stack_slabs(b, mat, n=5):
    """Escultura: losas de piedra de cantos redondeados apiladas y giradas; cada losa apoya plana sobre la anterior. Base en z=0."""
    z = 0.0
    for k in range(n):
        sx, sy, sz = 0.34 - k * 0.035, 0.24 - k * 0.02, 0.07 + 0.012 * (k % 2)
        rbox(b, (0.02 * math.sin(k * 1.7), 0.02 * math.cos(k * 1.3), z + sz / 2), (sx, sy, sz), 0.02, mat, segs=3, rot=(0, 0, k * 23))
        z += sz


def sculpt_ribbon(b):
    """Cinta de bronce retorcida (una sola superficie continua de 210 grados) que nace de una peana baja."""
    rbox(b, (0, 0, 0.015), (0.26, 0.26, 0.03), 0.007, "M_Museum_Brass", segs=2)
    twisted(b, rrect(0.1, 0.011, 0.01, 3), 0.03, 0.70, 56, 210, "M_Museum_Brass", center=lambda t: (0.11 * math.sin(t * math.pi * 1.5), 0.0))


def sculpt_tower(b):
    """Torre de ceramica de seccion cuadrada redondeada que gira 84 grados y se afina un poco hacia arriba (superficie continua)."""
    twisted(b, rrect(0.085, 0.085, 0.014, 3), 0.0, 0.65, 52, 84, "M_Ceramic", scale=lambda t: 1.0 - 0.14 * t)


def sculpt_arch(b):
    """Arco de piedra de una pieza (seccion rectangular redondeada que se afina hacia la clave) sobre una losa base; los pies apoyan planos."""
    R, z0 = 0.36, 0.04
    rbox(b, (0, 0, z0 / 2), (0.94, 0.2, z0), 0.012, "M_Museum_Stone", segs=2)
    n = 40
    pts = [(R * math.cos(math.pi * k / n), 0.0, z0 - 0.0005 + R * math.sin(math.pi * k / n)) for k in range(n + 1)]
    sweep(b, pts, rrect(0.058, 0.075, 0.022, 3), "M_Museum_Stone", sc=[(1.0, 1.0 - 0.22 * math.sin(math.pi * k / n)) for k in range(n + 1)], side=(0, 1, 0))


def sculpt_helix(b):
    """Espiral de laton (una vuelta de tubo ahusado) sobre un disco de madera oscura: arranca y termina en vertical, con las tapas planas."""
    b.cyl((0, 0, 0.02), 0.17, 0.04, "M_Museum_WoodDark", seg=32, bev=0, amp=0.0)
    n = 72
    pts, sc = [], []
    for k in range(n + 1):
        t = k / n
        a = 6.6 * t * t * (3 - 2 * t)
        pts.append((0.15 * math.cos(a), 0.15 * math.sin(a), 0.0395 + 0.64 * t))
        sc.append((1.0 - 0.3 * t, 1.0 - 0.3 * t))
    sweep(b, pts, [(0.045 * math.cos(q * math.tau / 14), 0.045 * math.sin(q * math.tau / 14)) for q in range(14)], "M_Museum_Brass", sc=sc)


def plinth(b, h=1.0, w=0.5, d=None):
    """Pedestal contemporaneo: bloque blanco con junta de sombra en la base y tapa fina."""
    d = d or w
    b.box((0, 0, 0.02), (w - 0.03, d - 0.03, 0.04), "M_Floor_Dark", bev=0, amp=0.0, cuts=0)
    b.box((0, 0, 0.04 + (h - 0.012 - 0.04) / 2), (w, d, h - 0.012 - 0.04), "M_Wall_White", bev=0.006, amp=0.001, cuts=1)
    b.box((0, 0, h - 0.006), (w + 0.008, d + 0.008, 0.012), "M_Wall_White", bev=0.002, amp=0.0, cuts=0)


def bench_modern(b, ln=1.8):
    """Banco contemporaneo de roble con ensambles a la vista: tablero de dos tablas con testeros (espigas de clavija visibles), cuatro patas
    de seccion cuadrada ahusada, largueros bajo el tablero y travesano central con espiga pasante. Asiento a 0.46 m."""
    wo, wd = "M_Museum_Wood", "M_Museum_WoodDark"
    top_z, th = 0.4375, 0.045
    bw = (ln - 0.12) / 2
    for sy in (-1, 1):   # dos tablas con junta de 4 mm
        rbox(b, (0, sy * 0.1135, top_z), (ln - 0.12, 0.2225, th), 0.005, wo, segs=1)
    for sx in (-1, 1):   # testeros (grano cruzado) con tres espigas vistas sobre cada uno
        xe = sx * (ln / 2 - 0.03)
        rbox(b, (xe, 0, top_z), (0.06, 0.45, th), 0.005, wo, segs=1)
        for yy in (-0.16, 0.0, 0.16):
            b.cyl((xe, yy, top_z + th / 2 + 0.0008), 0.0065, 0.003, wd, seg=10, bev=0, amp=0.0)
    lx, ly = ln / 2 - 0.16, 0.17
    for sx in (-1, 1):
        for sy in (-1, 1):   # patas ahusadas (0.055 arriba, 0.035 abajo)
            b.cyl((sx * lx, sy * ly, 0.2), 0.0247, 0.4, wd, seg=4, r2=0.0389, rot=(0, 0, 45), bev=0, amp=0.0)
    for sy in (-1, 1):   # largueros bajo el tablero
        b.box((0, sy * ly, 0.38), (2 * lx, 0.036, 0.07), wd, bev=0.003, amp=0.0, cuts=0)
    for sx in (-1, 1):   # cabeceros bajos y espiga pasante del travesano central
        b.box((sx * lx, 0, 0.14), (0.04, 2 * ly, 0.05), wd, bev=0.003, amp=0.0, cuts=0)
    b.box((0, 0, 0.14), (2 * lx + 0.04 + 0.016, 0.04, 0.05), wd, bev=0.003, amp=0.0, cuts=0)
    for sx in (-1, 1):
        b.box((sx * (lx + 0.0275), 0, 0.14), (0.003, 0.034, 0.044), wo, bev=0.0008, amp=0.0, cuts=0)           # testa de la espiga pasante (madera clara)
    for sx in (-1, 1):
        for sy in (-1, 1):
            b.cyl((sx * lx, sy * (ly + 0.019), 0.38), 0.0055, 0.003, wo, rot=(90, 0, 0), seg=8, bev=0, amp=0.0)   # clavija del ensamble pata-larguero


# ======================================================================= ala trasera: galeria contemporanea
# Mas grande por dentro que el exterior: aceptado por el usuario (2026-10-13). No toca museum_dims ni el exterior.
WING = (-7.0, 7.0, 9.0, 21.0)        # interior de la galeria (x0, x1, y0, y1)
WING_H = 5.0                         # altura libre (techo plano, SIN lucernario)
WING_TH = 0.3
LINK = (-0.9, 0.9, D.Y1, WING[2] - WING_TH)     # pasillo de enlace desde la puerta trasera del Stair Hall
LINK_H = 2.9
WING_DOOR = (0.0, 1.8, FL0 - 0.03, FL0 + LINK_H)
# hoja de la puerta trasera (marco de madera: jambas con cara interior en x = +-0.7, cabecero a 0.14 bajo el dintel, cara trasera en y = 6.15)
_GV_Z0 = FL0 + SADDLE + 0.003
GV_SPEC = dict(ax='x', jam=-1, side=1, ul=-0.7, z0=_GV_Z0, wl=1.4 - LEAF_CLR, hl=(D.BACK[0][3] - 0.14) - _GV_Z0 - 0.003, Lp=0.07, ang=90,
               pivot=(-0.7 + LEAF_UOFF, 6.17, _GV_Z0))
MINT = (-6.0, -3.0, 15.0, 18.4)      # volumen exento verde menta
WALLW = (-1.6, 4.6, 13.55, 13.95)    # muro exento blanco con canto rosa
GOLD, DARK, SILV = "M_Frame_Gold", "M_Museum_WoodDark", "M_Frame_Silver"
WING_ART = [  # (nombre, eje, cara, sentido, u, z sobre el suelo, ancho, alto, marco)
    ("South_W", 'x', WING[2], 1, -4.0, 1.65, 1.6, 1.1, GOLD), ("South_E", 'x', WING[2], 1, 4.0, 1.7, 1.2, 1.4, DARK),
    ("Wall_S1", 'x', WALLW[2], -1, -0.4, 1.7, 0.75, 1.0, GOLD), ("Wall_S2", 'x', WALLW[2], -1, 1.3, 1.62, 0.6, 0.5, SILV),
    ("Wall_S3", 'x', WALLW[2], -1, 3.2, 1.75, 1.0, 1.35, DARK),
    ("Wall_N1", 'x', WALLW[3], 1, 0.0, 1.65, 1.2, 0.9, GOLD), ("Wall_N2", 'x', WALLW[3], 1, 2.6, 1.7, 0.9, 1.1, DARK),
    ("Mint_S", 'x', MINT[2], -1, -4.5, 1.7, 0.8, 1.05, GOLD), ("Mint_N", 'x', MINT[3], 1, -4.5, 1.65, 1.4, 1.0, GOLD),
    ("Mint_E1", 'y', MINT[1], 1, 15.75, 1.6, 0.5, 0.62, GOLD), ("Mint_E2", 'y', MINT[1], 1, 16.7, 1.6, 0.5, 0.62, DARK),
    ("Mint_E3", 'y', MINT[1], 1, 17.65, 1.6, 0.5, 0.62, SILV),
    ("West_1", 'y', WING[0], 1, 11.2, 1.7, 1.0, 1.2, GOLD), ("West_2", 'y', WING[0], 1, 13.0, 1.65, 0.8, 1.0, DARK),
    ("West_3", 'y', WING[0], 1, 19.7, 1.6, 0.9, 0.7, GOLD),
    ("North_1", 'x', WING[3], -1, -4.6, 1.75, 1.0, 1.3, GOLD), ("North_2", 'x', WING[3], -1, 1.4, 1.7, 1.8, 1.2, DARK),
    ("North_3", 'x', WING[3], -1, 4.8, 1.65, 0.9, 1.1, GOLD),
    ("East_1", 'y', WING[1], -1, 10.8, 1.7, 0.9, 1.2, GOLD), ("East_2", 'y', WING[1], -1, 13.2, 1.62, 1.2, 0.9, DARK),
    ("East_3", 'y', WING[1], -1, 16.4, 1.7, 1.6, 1.2, GOLD), ("East_4", 'y', WING[1], -1, 19.4, 1.6, 0.8, 1.0, DARK),
]
WING_PEDESTALS = [  # (x, y, alto, ancho, escultura)
    (1.4, 16.6, 1.05, 0.5, sculpt_ribbon), (4.4, 15.6, 0.8, 0.55, lambda b: stack_slabs(b, "M_Museum_Stone")),
    (5.0, 18.6, 1.1, 0.45, sculpt_tower), (-4.6, 12.2, 0.45, 1.1, sculpt_arch),
]
RAILS = [((-6.2, 11.4), (5.8, 11.4)), ((5.4, 11.4), (5.4, 19.6)), ((-6.4, 19.6), (5.4, 19.6)),
         ((-1.6, 14.5), (-1.6, 19.6)), ((-1.6, 15.4), (3.8, 15.4))]
SPOTS = [  # (punto del carril, objetivo x, y, z sobre el suelo)
    ((-4.0, 11.4), (-4.0, WING[2], 1.65)), ((4.0, 11.4), (4.0, WING[2], 1.7)),
    ((-0.4, 11.4), (-0.4, WALLW[2], 1.7)), ((1.3, 11.4), (1.3, WALLW[2], 1.62)), ((3.2, 11.4), (3.2, WALLW[2], 1.75)),
    ((-4.6, 11.4), (-4.6, 12.2, 0.7)), ((-3.4, 11.4), (-4.5, MINT[2], 1.7)),
    ((-5.8, 11.4), (WING[0], 11.2, 1.7)), ((-6.2, 11.4), (WING[0], 13.0, 1.65)),
    ((5.4, 10.8), (WING[1], 10.8, 1.7)), ((5.4, 13.2), (WING[1], 13.2, 1.62)), ((5.4, 16.4), (WING[1], 16.4, 1.7)),
    ((5.4, 19.0), (WING[1], 19.4, 1.6)), ((5.4, 15.0), (4.4, 15.6, 1.0)), ((5.4, 17.8), (5.0, 18.6, 1.3)),
    ((-4.9, 19.6), (-4.6, WING[3], 1.75)), ((-4.1, 19.6), (-4.5, MINT[3], 1.65)), ((1.4, 19.6), (1.4, WING[3], 1.7)),
    ((4.8, 19.6), (4.8, WING[3], 1.65)), ((-6.4, 19.6), (WING[0], 19.7, 1.6)), ((2.2, 19.6), (1.4, 16.6, 1.3)),
    ((-1.6, 16.2), (MINT[1], 16.2, 1.6)), ((-1.6, 17.4), (MINT[1], 17.4, 1.6)),
    ((0.0, 15.4), (0.0, WALLW[3], 1.65)), ((2.6, 15.4), (2.6, WALLW[3], 1.7)),
]


def wing(cS, cT, cE, cF, cLt):
    x0, x1, y0, y1 = WING
    t, zc = WING_TH, FL0 + WING_H
    lx0, lx1, ly0, ly1 = LINK
    # ---- envolvente: enlucido por fuera (como la fachada), losas
    b = B("Int_Wing_Shell", 0.5)
    wall(b, 'x', y0 - t / 2, x0 - t, x1 + t, 0.2, zc, t, "M_Museum_Plaster", [WING_DOOR], amp=0.01)
    wall(b, 'x', y1 + t / 2, x0 - t, x1 + t, 0.2, zc, t, "M_Museum_Plaster", amp=0.01)
    wall(b, 'y', x0 - t / 2, y0, y1, 0.2, zc, t, "M_Museum_Plaster", amp=0.01)
    wall(b, 'y', x1 + t / 2, y0, y1, 0.2, zc, t, "M_Museum_Plaster", amp=0.01)
    for xx in (lx0 - 0.075, lx1 + 0.075):
        wall(b, 'y', xx, ly0, ly1, 0.2, FL0 + LINK_H, 0.15, "M_Museum_Plaster", amp=0.008)
    slab(b, x0, x1, y0, y1, 0.2, FL0 - 0.03, "M_Interior_Concrete")
    slab(b, lx0, lx1, ly0, y0, 0.2, FL0 - 0.03, "M_Interior_Concrete")
    slab(b, x0 - t, x1 + t, y0 - t, y1 + t, zc, zc + 0.3, "M_Wall_White")
    slab(b, lx0 - 0.15, lx1 + 0.15, ly0, ly1, FL0 + LINK_H, FL0 + LINK_H + 0.25, "M_Wall_White")
    b.finish(cS)
    # ---- suelo de losas de piedra (aparejo a matajunta)
    b = B("Int_Wing_Floor", 0.5)
    rnd = random.Random(21)

    def tiles(ax0, ax1, ay0, ay1, tl=0.8, tw=0.5):
        j, y = 0, ay0
        while y < ay1 - 0.01:
            y2 = min(y + tw, ay1)
            x = ax0 - (tl / 2 if j % 2 else 0.0)
            while x < ax1 - 0.01:
                xa, xb = max(x, ax0), min(x + tl, ax1)
                if xb - xa > 0.02:
                    m = "M_Floor_StoneA" if rnd.random() < 0.6 else "M_Floor_StoneB"
                    b.box(((xa + xb) / 2, (y + y2) / 2, FL0 - 0.015), (xb - xa - 0.005, y2 - y - 0.005, 0.03), m, bev=0, amp=0.0, cuts=0)
                x += tl
            y, j = y2, j + 1
    tiles(x0, x1, y0, y1)
    tiles(lx0, lx1, ly0, y0)
    b.finish(cS)
    # ---- acabados: pintura con junta de sombra (sin rodapie de madera)
    OPEN.append(('x', y0 - t / 2, t, WING_DOOR[0], WING_DOOR[1], WING_DOOR[2], WING_DOOR[3]))
    b = WB("Int_Wing_WallFinish", 0.5)

    def paint(sd, mat, top):
        layer(b, sd, FL0 + 0.05, top, 0.012, mat)
        layer(b, sd, FL0 - 0.01, FL0 + 0.05, 0.004, "M_Floor_Dark")
    for sd in sides((x0, x1, y0, y1)):
        if sd[0] == 'x' and abs(sd[1] - y1) < 0.01:      # muro del fondo: tramo oeste en coral
            paint(('x', y1, -1, x0, -1.0), "M_Wall_Coral", zc)
            paint(('x', y1, -1, -1.0, x1), "M_Wall_White", zc)
        else:
            paint(sd, "M_Wall_White", zc)
    for sd in sides((lx0, lx1, ly0, ly1)):
        paint(sd, "M_Wall_White", FL0 + LINK_H)
    b.finish(cT)
    door_leaf("GalleryVII", GV_SPEC["pivot"], GV_SPEC["wl"], GV_SPEC["hl"], GV_SPEC["ang"], coll=cF)
    # luz general + "rebote" hacia el techo (Blender; en Unity lo dara la GI)
    # rebotes: rectangulos mirando al techo solo en zonas libres (no deben cortar los volumenes exentos)
    for nm, pos, en, sz, up in (("Light_GalleryVII_Fill", ((x0 + x1) / 2, (y0 + y1) / 2, zc - 0.25), 1800, (11.0, 9.0), False),
                                ("Light_GalleryVII_Bounce_Front", (0.0, 11.2, FL0 + 2.6), 260, (10.0, 2.6), True),
                                ("Light_GalleryVII_Bounce_East", (5.6, 17.5, FL0 + 2.6), 130, (2.2, 6.0), True),
                                ("Light_GalleryVII_Bounce_Mid", (1.0, 17.0, FL0 + 2.6), 120, (4.0, 3.0), True),
                                ("Light_GalleryVII_Bounce_NW", (-4.5, 19.7, FL0 + 2.6), 90, (4.5, 2.0), True),
                                ("Light_Link", (0.0, (ly0 + ly1) / 2, FL0 + LINK_H - 0.3), 140, None, False)):
        ld = bpy.data.lights.new(nm, 'AREA' if sz else 'POINT')
        ld.energy, ld.color = en, (1.0, 0.94, 0.86)
        if sz:
            ld.shape, ld.size, ld.size_y = 'RECTANGLE', sz[0], sz[1]
        lo = bpy.data.objects.new(nm, ld)
        lo.location = pos
        if up:
            lo.rotation_euler = (math.pi, 0, 0)
        cLt.objects.link(lo)
    if WING_STEP < 3:
        return
    # ---- volumenes exentos de color (hasta el techo, como en la referencia)
    b = B("Int_Wing_Volumes", 0.5)

    def volume(v, mat, caps=()):
        vx0, vx1, vy0, vy1 = v
        cx, cy = (vx0 + vx1) / 2, (vy0 + vy1) / 2
        b.box((cx, cy, FL0 + 0.025), (vx1 - vx0 - 0.02, vy1 - vy0 - 0.02, 0.05), "M_Floor_Dark", bev=0, amp=0.0, cuts=0)
        h = zc - (FL0 + 0.05)
        b.box((cx, cy, FL0 + 0.05 + h / 2), (vx1 - vx0, vy1 - vy0, h), mat, bev=0.008, amp=0.002)
        for sd, cm in caps:
            layer(b, sd, FL0 + 0.05, zc, 0.006, cm)
    volume(MINT, "M_Wall_Mint")
    volume(WALLW, "M_Wall_White", caps=[(('y', WALLW[1], 1, WALLW[2], WALLW[3]), "M_Wall_Rose")])
    # rejilla de ventilacion baja en la cara sur del muro blanco (como en la referencia)
    Fg = Face(b, 'x', WALLW[2], -1)
    Fg.box(1.5, 0.006, FL0 + 0.16, 5.4, 0.012, 0.16, "M_Museum_Metal", bev=0.003, amp=0.0, cuts=2)
    for k in range(5):
        Fg.box(1.5, 0.0135, FL0 + 0.104 + k * 0.028, 5.3, 0.003, 0.012, "M_Floor_Dark", bev=0, amp=0.0, cuts=0)
    b.finish(cS)
    # ---- carriles de focos (siguen el techo)
    b = HB("Int_Wing_Tracks", 0.5)
    for (pa, pb) in RAILS:
        cx, cy = (pa[0] + pb[0]) / 2, (pa[1] + pb[1]) / 2
        ln = math.hypot(pb[0] - pa[0], pb[1] - pa[1]) + 0.05
        sz = (ln, 0.045, 0.035) if abs(pb[1] - pa[1]) < 0.01 else (0.045, ln, 0.035)
        b.box((cx, cy, zc - 0.0175), sz, "M_Track_White", bev=0.004, amp=0.0, cuts=max(1, int(ln / 1.5)))
    for (rp, tg) in SPOTS:
        # mismo foco detallado que las galerias de la planta principal (adaptador, vastago, horquilla, cuerpo con aletas, bisel y lente)
        Hc, d = spot_head(b, rp, zc - 0.005, (tg[0], tg[1], FL0 + tg[2]))
        ld = bpy.data.lights.new("Spot_GalleryVII", 'SPOT')
        ld.energy, ld.color, ld.spot_size, ld.spot_blend = 160, (1.0, 0.92, 0.8), math.radians(34), 0.5
        ld.shadow_soft_size = 0.05
        lo = bpy.data.objects.new("Spot_GalleryVII", ld)
        lo.location = L.warp(Hc + d * 0.1)   # la malla del carril se deforma (warp): la luz sigue al foco
        lo.rotation_euler = d.to_track_quat('-Z', 'Y').to_euler()
        cLt.objects.link(lo)
    dome_light(b, 0.0, (ly0 + ly1) / 2, FL0 + LINK_H, plate="M_Wall_White")      # plafon del pasillo de enlace (hasta ahora solo tenia luz, sin luminaria)
    b.finish(cS)
    if WING_STEP < 4:
        return
    # ---- obras, pedestales, banco, puerta y rotulos
    for (nm, ax, face, s, u, z, w, h, fr) in WING_ART:
        art_slot("GalleryVII_" + nm, ax, face, s, u, FL0 + z, w, h, frame=fr, parent=cE)
    for i, (x, y, h, w, fn) in enumerate(WING_PEDESTALS):
        to_col(prop("GalleryVII_Pedestal_%d" % i, (x, y, FL0), 0, lambda b, h=h, w=w: plinth(b, h, w)), cE)
        to_col(prop("GalleryVII_Sculpture_%d" % i, (x, y, FL0 + h), 15 * i, fn), cE)
    to_col(prop("GalleryVII_Bench", (1.4, 11.0, FL0), 0, bench_modern), cF)
    wall_sign("GalleryVII", "GALLERY VII", 'x', IY1, -1, 0.0, FL0 + 3.3, coll=cF)
    to_col(prop("GalleryVII_Plant_0", (-6.3, 9.75, FL0), 0, lambda b: plant_monstera(b, 4, face=math.radians(45), spread=math.radians(85))), cF)
    to_col(prop("GalleryVII_Plant_1", (6.45, 9.6, FL0), 0, lambda b: plant_ficus(b, 9, face=math.radians(135), spread=math.radians(120))), cF)


# ======================================================================= asentar props
SNAP_WALL = ("ArtSlot_", "Sign_", "Restroom_1_Toilet", "Restroom_2_Toilet", "Restroom_1_PaperHolder", "Restroom_2_PaperHolder",
             "Restroom_1_Hook", "Restroom_2_Hook", "Restroom_Lobby_Mirror", "Restroom_Lobby_Dryer", "Restroom_Lobby_Counter",
             "Maintenance_FuseBox", "Maintenance_Sink", "Maintenance_ToolRack", "Maintenance_MopLean", "Maintenance_Broom", "Maintenance_Cart",
             "Maintenance_Shelves", "Maintenance_Workbench", "Maintenance_Lockers", "GalleryV_Featured_Plaque", "Hall_Reception_Cabinet", "Hall_Directory")
SNAP_GROUND = ("Hall_Plant_", "Hall_Rug", "Hall_Reception_Desk", "Hall_Reception_Chair", "StairHall_Plant", "Landing_Plant", "GalleryVI_Pedestal_", "GalleryIII_Pedestal_", "StairHall_Pedestal",
               "GalleryVII_Pedestal_", "GalleryVII_Plant_", "GalleryV_Stanchions", "Maintenance_MopBucket", "Maintenance_Broom", "Maintenance_MopLean", "Maintenance_DustPan", "Maintenance_Cart", "Maintenance_Sink",
               "Maintenance_Lockers", "Maintenance_Workbench", "Maintenance_Shelves", "Maintenance_Boxes", "Landing_Bench", "GalleryIV_Bench",
               "Restroom_1_Brush", "Restroom_2_Brush", "Restroom_1_Bin", "Restroom_2_Bin", "Restroom_Lobby_Bin")
SNAP_FLOOR = ("GalleryVI_Sculpture_", "StairHall_CatSculpture", "GalleryVII_Sculpture_", "GalleryIII_NicheVase_")


def _bvh(names):
    from mathutils.bvhtree import BVHTree
    dg = bpy.context.evaluated_depsgraph_get()
    vs, ps = [], []
    for n in names:
        ob = bpy.data.objects[n]
        me = ob.evaluated_get(dg).to_mesh()
        mw, base = ob.matrix_world, len(vs)
        vs += [mw @ v.co for v in me.vertices]
        ps += [[base + i for i in p.vertices] for p in me.polygons]
        ob.evaluated_get(dg).to_mesh_clear()
    return BVHTree.FromPolygons(vs, ps)


def settle():
    """Los muros estan deformados (warp) y los props no: apoya cuadros, rotulos y sanitarios contra el muro real
    y las esculturas sobre su base real (sin huecos ni penetraciones)."""
    bpy.context.view_layer.update()
    meshes = [o for o in bpy.data.objects if o.type == 'MESH']
    Tw = _bvh([o.name for o in meshes if o.name.startswith(("Int_Shell", "Int_Wing_Shell", "Int_Wing_WallFinish", "Int_Wing_Volumes", "Int_Door_Casings", "Int_Restroom_Tiles", "Int_Annex_Shell"))
               or o.name.endswith(("_Partitions", "_WallFinish")) or o.name == "GalleryII_DisplayPanel"])
    floors = [o.name for o in meshes if o.name.endswith("_Floors") or o.name == "Int_Wing_Floor"]

    def drop(ob, T):
        mw = ob.matrix_world
        ws = [mw @ v.co for v in ob.data.vertices]
        zmin = min(p.z for p in ws)
        pts = [p for p in ws if p.z < zmin + 0.01]
        gaps = []
        for p in pts[::max(1, len(pts) // 80)]:
            h = T.ray_cast(p + Vector((0, 0, 0.05)), Vector((0, 0, -1)), 0.5)
            if h[0] is not None:
                gaps.append((h[0] - p).length * (1 if h[0].z < p.z else -1))
        if gaps:
            ob.location.z -= min(gaps) - 0.0005
    Tg = _bvh(floors)
    for ob in meshes:
        if ob.name.startswith(SNAP_GROUND):
            drop(ob, Tg)
    bpy.context.view_layer.update()
    Tf = _bvh(floors + [o.name for o in meshes if "_Pedestal" in o.name or o.name == "GalleryIII_Niches"])
    for ob in meshes:
        mw = ob.matrix_world
        if ob.name.startswith(SNAP_WALL):
            fwd = (mw.to_3x3() @ Vector((0, 1, 0))).normalized()
            ymax = max(v.co.y for v in ob.data.vertices)
            pts = [mw @ v.co for v in ob.data.vertices if v.co.y > ymax - 0.003]
            gaps = []
            for p in pts[::max(1, len(pts) // 80)]:
                o = p - fwd * 0.2
                h = Tw.ray_cast(o, fwd, 0.6)
                if h[0] is not None:
                    gaps.append((h[0] - o).length - 0.2)
            if gaps:
                ob.location += fwd * (min(gaps) - 0.0005)
        elif ob.name.startswith(SNAP_FLOOR):
            drop(ob, Tf)
    bpy.context.view_layer.update()


# ======================================================================= salas
def hall_rug(b):
    """Alfombra de lana rectangular 2,0 x 3,0 m (lado largo a lo largo de Y), 1,2 cm de alto: campo azul marino apagado, banda interior,
    filetes crema, banda exterior terracota con greca de rombos, motivos de esquina, medallon central y flecos cortos en los lados cortos.
    Origen en el centro y apoyada en z = 0."""
    HX, HY = 1.0, 1.5
    H0 = 0.0098                    # altura de la lana; las incrustaciones suman hasta 1,2 cm
    IL = 0.0007                    # grosor de cada capa de incrustacion

    def rect(x0, x1, y0, y1, z0, z1, mat, bev=0.0):
        b.box(((x0 + x1) / 2, (y0 + y1) / 2, (z0 + z1) / 2), (x1 - x0, y1 - y0, z1 - z0), mat, bev=bev, amp=0.0, cuts=0)

    def frame(i0, i1, mat, z1=H0):   # marco entre dos insets del borde (4 tiras sin solapar en las esquinas)
        rect(-HX + i0, HX - i0, -HY + i0, -HY + i1, 0.0, z1, mat)
        rect(-HX + i0, HX - i0, HY - i1, HY - i0, 0.0, z1, mat)
        rect(-HX + i0, -HX + i1, -HY + i1, HY - i1, 0.0, z1, mat)
        rect(HX - i1, HX - i0, -HY + i1, HY - i1, 0.0, z1, mat)

    def diamond(cx, cy, rx, ry, layer, mat):   # rombo fino incrustado
        z0 = H0 + (layer - 1) * IL - 0.0001
        b.prism([(cx + rx, cy, z0), (cx, cy + ry, z0), (cx - rx, cy, z0), (cx, cy - ry, z0)], (0, 0, IL + 0.0001), mat, bev=0.0, amp=0.0)
    OE, OL, BD, IL1, IB = 0.045, 0.065, 0.255, 0.275, 0.335     # insets: filete de borde, banda ancha, filete interior, banda interior
    rect(-HX + IB, HX - IB, -HY + IB, HY - IB, 0.0, H0, "M_Rug_Navy")           # campo
    frame(0.0, OE, "M_Rug_Gold")                                                # canto de la alfombra (sin biselar: 1 cm de alto)
    frame(OE, OL, "M_Rug_Cream")
    frame(OL, BD, "M_Rug_Terracotta")                                           # banda exterior (lleva la greca)
    frame(BD, IL1, "M_Rug_Cream")
    frame(IL1, IB, "M_Fabric_Blue")                                             # banda interior
    # greca: rombos crema con rombo interior azul marino y cuadritos dorados entre ellos
    cx_, cy_ = HX - (OL + BD) / 2, HY - (OL + BD) / 2                           # eje de la banda ancha
    half = (BD - OL) / 2
    ry_ = half - 0.025                                                          # semidiagonal del rombo de la greca
    cs = half * 2                                                               # cuadrado de la esquina
    for (axis, ctr, ln) in (('y', cx_, cy_), ('x', cy_, cx_)):
        usable = ln - cs
        n = 11 if axis == 'y' else 6
        for q in range(n):
            u = -usable + (q + 0.5) * 2 * usable / n
            for sg in (-1, 1):
                if axis == 'y':
                    x, y = sg * ctr, u
                else:
                    x, y = u, sg * ctr
                diamond(x, y, ry_, ry_, 1, "M_Rug_Cream")
                diamond(x, y, ry_ * 0.5, ry_ * 0.5, 2, "M_Rug_Navy")
                su = usable / n
                nx, ny = (x, y + su) if axis == 'y' else (x + su, y)
                if q < n - 1:
                    diamond(nx, ny, 0.026, 0.026, 1, "M_Rug_Gold")             # cuadrito dorado entre rombos (a mitad entre dos rombos)
    for sx in (-1, 1):   # motivos de esquina: rombos concentricos
        for sy in (-1, 1):
            x, y = sx * cx_, sy * cy_
            diamond(x, y, half - 0.012, half - 0.012, 1, "M_Rug_Cream")
            diamond(x, y, half - 0.04, half - 0.04, 2, "M_Rug_Gold")
            diamond(x, y, half - 0.07, half - 0.07, 3, "M_Rug_Navy")
    # medallon central: rombos alargados concentricos
    my, mx = 0.95, 0.52
    diamond(0.0, 0.0, mx, my, 1, "M_Rug_Gold")
    diamond(0.0, 0.0, mx - 0.03, my - 0.058, 2, "M_Rug_Navy")
    diamond(0.0, 0.0, mx - 0.12, my - 0.23, 3, "M_Rug_Terracotta")
    # flecos: hebras finas en los dos lados cortos (y = +-HY), ligeramente abiertas en abanico y de largo irregular
    rnd = random.Random(21)
    nfr = 120
    for sgy in (-1, 1):
        for q in range(nfr):
            x = -HX + 0.012 + (q + 0.5) * (2 * HX - 0.024) / nfr
            ln = 0.07 + rnd.uniform(-0.008, 0.008)
            ang = rnd.uniform(-5, 5) + x * 3.0
            yc = sgy * (HY + ln / 2 - 0.004)
            b.box((x, yc, 0.0017), (0.0042, ln + 0.008, 0.0034), "M_Rug_Cream", rot=(0, 0, ang), bev=0.0, amp=0.0, cuts=0)


def furnish(cE, cF, cSv):
    random.seed(9)
    # ---------------- Hall
    to_col(prop("Hall_Reception_Desk", (RX, RY, FL0), 0, reception_desk), cF)
    to_col(prop("Hall_Reception_Chair", (2.52, -4.2, FL0), -90, reception_chair), cF)
    to_col(prop("Hall_Reception_Cabinet", (3.0, -4.45, FL0 + 1.65), -90, key_cabinet), cF)
    to_col(prop("Hall_Bench", (-2.68, -1.15, FL0), 90, lambda b: bench_gallery(b, 1.3, "M_Fabric_Blue")), cF)
    for i, (x, y, fn) in enumerate(((-2.45, -4.8, lambda b: plant_ficus(b, 1, face=math.radians(55), spread=math.radians(110))), (2.45, -1.0, lambda b: plant_ficus(b, 5, face=math.radians(180), spread=math.radians(120))), (-2.38, -0.3, plant_snake))):
        to_col(prop("Hall_Plant_%d" % i, (x, y, FL0), 0, fn), cF)

    to_col(prop("Hall_Rug", (0, -2.8, FL0), 0, hall_rug), cF)

    to_col(prop("Hall_Directory", (-3.0, -4.6, FL0 + 1.7), 90, directory_board), cF)
    wall_sign("GalleryI", "GALLERY I", 'y', -3.0, 1, -2.9, FL0 + 3.05, coll=cF)
    wall_sign("GalleryII", "GALLERY II", 'y', 3.0, -1, -2.9, FL0 + 3.05, coll=cF)
    wall_sign("Reception", "RECEPTION", 'y', 3.0, -1, -4.45, FL0 + 2.38, size=0.16, w=1.2, h=0.3, coll=cF)

    # ---------------- Stair Hall
    to_col(prop("StairHall_Bench", (1.8, 5.25, FL0), 0, lambda b: bench_gallery(b, 1.3, "M_Fabric_Olive")), cF)
    to_col(prop("StairHall_Pedestal", (1.3, 2.2, FL0), 0, lambda b: pedestal(b, 0.95, 0.5)), cE)
    to_col(prop("StairHall_CatSculpture", (1.3, 2.2, FL0 + 0.95), 200, cat_sculpture), cE)
    to_col(prop("StairHall_Plant", (2.55, 3.05, FL0), 0, lambda b: plant_snake(b, 6)), cF)
    wall_sign("Restrooms", "RESTROOMS", 'y', 3.0, -1, 1.85, FL0 + 2.6, size=0.09, w=1.0, coll=cF)
    wall_sign("StaffOnly", "STAFF ONLY", 'y', 3.0, -1, 4.2, FL0 + 2.6, size=0.08, w=0.85, coll=cSv)

    # ---------------- Gallery I (ocre, paisajes)
    art_slot("GalleryI_West", 'y', IX0, 1, -1.1, FL0 + 1.65, 1.6, 1.1, parent=cE)
    art_slot("GalleryI_North_A", 'x', 0.2, -1, -3.95, FL0 + 1.6, 0.8, 1.05, parent=cE)
    art_slot("GalleryI_North_B", 'x', 0.2, -1, -6.85, FL0 + 1.6, 0.7, 0.9, parent=cE)
    art_slot("GalleryI_East", 'y', -3.2, -1, -0.95, FL0 + 1.6, 1.0, 0.75, parent=cE)
    art_slot("GalleryI_South", 'x', IY0, 1, -3.68, FL0 + 1.6, 0.6, 0.8, frame="M_Museum_WoodDark", parent=cE)   # deja sitio a las cortinas de la ventana sur
    to_col(prop("GalleryI_Bench", (-5.4, -2.4, FL0), 90, bench_gallery), cE)

    # ---------------- Gallery II (ceruleo, panel exento)
    def panel(b):
        b.box((0, 0, 1.35), (2.2, 0.2, 2.5), "M_Wall_Cerulean", bev=0.02, amp=0.004, cuts=2)
        b.box((0, 0, 0.06), (2.3, 0.3, 0.12), "M_Museum_WoodDark", bev=0.01, amp=0.003, cuts=1)
        b.box((0, 0, 2.62), (2.26, 0.26, 0.06), "M_Museum_WoodDark", bev=0.01, amp=0.003, cuts=1)
    to_col(prop("GalleryII_DisplayPanel", (5.5, -2.5, FL0), 90, panel), cE)
    art_slot("GalleryII_Panel_West", 'y', 5.4, -1, -2.5, FL0 + 1.55, 0.9, 1.15, parent=cE)
    art_slot("GalleryII_Panel_East", 'y', 5.6, 1, -2.5, FL0 + 1.55, 0.9, 1.15, parent=cE)
    art_slot("GalleryII_North_A", 'x', 0.2, -1, 4.45, FL0 + 1.65, 1.0, 1.3, parent=cE)
    art_slot("GalleryII_North_B", 'x', 0.2, -1, 6.45, FL0 + 1.65, 1.0, 1.3, parent=cE)
    art_slot("GalleryII_East", 'y', IX1, -1, -0.95, FL0 + 1.6, 0.8, 1.0, parent=cE)
    to_col(prop("GalleryII_Vitrine", (4.15, -0.95, FL0), 0, vitrine), cE)

    # ---------------- Gallery III (terracota, obras pequenas, nichos)
    nb = B("GalleryIII_Niches", 0.5)
    F = Face(nb, 'y', -3.2, -1)
    br_ = "M_Museum_Brass"
    for yy in (1.5, 3.0, 4.5):
        F.box(yy, 0.057, FL0 + 1.6, 0.95, 0.08, 1.3, "M_Museum_WoodDark", bev=0.015, amp=0.003, cuts=1)
        F.box(yy, 0.097, FL0 + 1.6, 0.75, 0.01, 1.1, "M_Wall_Cerulean", bev=0, amp=0.001, cuts=0)
        F.box(yy, 0.212, FL0 + 1.15, 0.8, 0.3, 0.04, "M_Museum_Wood", bev=0.008, amp=0.002, cuts=0)
        # luminaria de nicho tipo "luz de cuadro": carcasa semicilindrica de laton con testeros, tubo luminoso visible bajo ella y dos brazos
        # atornillados con placa al canto superior del marco; el tubo mira hacia el nicho (hacia abajo)
        zc_, vc_ = FL0 + 2.22, 0.15
        xc_ = F.P(yy, vc_, 0)[0]
        arc_band(nb, (xc_, yy, zc_), 'y', 0.03, 0.004, 0, 180, 0.62, br_, n=12)
        for sg in (-1, 1):
            nb.prism([(xc_ + 0.03 * math.cos(math.radians(a_)), yy + sg * 0.311, zc_ + 0.03 * math.sin(math.radians(a_))) for a_ in range(0, 181, 20)],
                     (0, sg * 0.004, 0), br_, amp=0.0)
            F.box(yy + sg * 0.2, 0.1235, zc_ + 0.0, 0.014, 0.0555, 0.012, br_, bev=0.002, amp=0.0, cuts=0)              # brazo hasta el marco
            F.box(yy + sg * 0.2, 0.0995, zc_ + 0.0, 0.03, 0.004, 0.05, br_, bev=0.001, amp=0.0, cuts=0)                  # placa en el marco
        nb.cyl((xc_, yy, zc_ - 0.002), 0.011, 0.58, "M_Bulb_Warm", rot=(90, 0, 0), seg=10, bev=0, amp=0.0)
    nb.finish(cE)
    # jarrones sobre las baldas de los nichos (altura <= 0.32, radio <= 0.08): pie, vientre, cuello y labio; huecos por dentro. El primero lleva asas
    def vase(b, rings, mat, handles=None):
        loft(b, [(z, r, r, 0.0) for (z, r) in rings], mat, seg=18, raw=True)
        if handles:
            for sg in (-1, 1):
                pr = smooth_prof([(sg * r_, z_) for (r_, z_) in handles], 3)
                tube(b, [(0.0, r_, z_) for (r_, z_) in pr], 0.0085, mat, seg=8)
    foot0 = [(0.0, 0.031), (0.0035, 0.0385), (0.0115, 0.0395)]
    body0 = smooth_prof([(0.0125, 0.0285), (0.03, 0.0255), (0.06, 0.052), (0.1, 0.0745), (0.14, 0.0745), (0.18, 0.054), (0.215, 0.0325), (0.238, 0.0255),
                         (0.262, 0.0265), (0.28, 0.0345), (0.292, 0.0425), (0.296, 0.045)], 3)
    rim0 = [(0.2985, 0.0455), (0.3, 0.043), (0.3, 0.0385)]
    in0 = smooth_prof([(0.3, 0.0385), (0.29, 0.031), (0.27, 0.0225), (0.22, 0.017), (0.15, 0.0135)], 3)
    foot1 = [(0.0, 0.03), (0.003, 0.037), (0.010, 0.038), (0.0115, 0.0365)]
    body1 = smooth_prof([(0.0115, 0.0365), (0.035, 0.051), (0.075, 0.0565), (0.12, 0.049), (0.16, 0.0335), (0.19, 0.0215), (0.22, 0.0165), (0.26, 0.0155),
                         (0.29, 0.0165), (0.306, 0.0215), (0.314, 0.026)], 3)
    rim1 = [(0.318, 0.0265), (0.32, 0.0245), (0.32, 0.0195)]
    in1 = smooth_prof([(0.32, 0.0195), (0.31, 0.0155), (0.28, 0.0115), (0.2, 0.0095)], 3)
    foot2 = [(0.0, 0.031), (0.003, 0.036), (0.010, 0.0365)]
    body2 = smooth_prof([(0.0115, 0.033), (0.03, 0.052), (0.065, 0.0735), (0.1, 0.0815), (0.13, 0.0765), (0.152, 0.062), (0.164, 0.0525)], 3)
    rim2 = [(0.168, 0.0545), (0.173, 0.0585), (0.175, 0.0575), (0.175, 0.0535)]
    in2 = smooth_prof([(0.175, 0.0535), (0.165, 0.049), (0.14, 0.0445), (0.09, 0.04), (0.05, 0.033)], 3)
    vases = ((foot0 + body0 + rim0 + in0, "M_Rug_Terracotta", [(0.0225, 0.256), (0.058, 0.268), (0.075, 0.244), (0.072, 0.205), (0.06, 0.17), (0.05, 0.158)]),
             (foot1 + body1 + rim1 + in1, "M_Fabric_Blue", None),
             (foot2 + body2 + rim2 + in2, "M_Ceramic", None))
    for i, (yy, (prof, vm, hd)) in enumerate(zip((1.5, 3.0, 4.5), vases)):
        to_col(prop("GalleryIII_NicheVase_%d" % i, (-3.2 - 0.212, yy, FL0 + 1.17), 0, lambda b, prof=prof, vm=vm, hd=hd: vase(b, prof, vm, hd)), cE)
    for i, (x, y) in enumerate(((-5.3, 2.2), (-5.3, 4.0))):
        to_col(prop("GalleryIII_Pedestal_%d" % i, (x, y, FL0), 0, lambda b: pedestal(b, 0.85, 0.45)), cE)
    to_col(prop("GalleryIII_Vitrine", (-6.6, 1.0, FL0), 0, vitrine), cE)
    art_slot("GalleryIII_North", 'x', IY1, -1, -3.9, FL0 + 1.6, 0.7, 0.9, parent=cE)
    art_slot("GalleryIII_West", 'y', IX0, 1, 5.0, FL0 + 1.6, 0.45, 0.6, frame="M_Museum_WoodDark", parent=cE)

    # ---------------- Gallery IV (sala de luz: banco frente al ventanal)
    to_col(prop("GalleryIV_Bench", (0.0, -4.4, FL1), 0, lambda b: bench_gallery(b, 1.6, "M_Fabric_Mustard")), cE)
    art_slot("GalleryIV_North", 'x', 0.2, -1, -0.25, FL1 + 1.65, 1.5, 1.0, parent=cE)
    for s, x in ((1, -3.0), (-1, 3.0)):
        art_slot("GalleryIV_%s_Front" % ("West" if s > 0 else "East"), 'y', x, s, -4.4, FL1 + 1.6, 0.8, 1.0, parent=cE)
        art_slot("GalleryIV_%s_Back" % ("West" if s > 0 else "East"), 'y', x, s, -0.8, FL1 + 1.6, 0.8, 0.9, frame="M_Museum_WoodDark", parent=cE)

    # ---------------- Gallery V (gris: obra destacada = campo gris con la flor amarilla)
    art_slot("GalleryV_Featured_GreyField", 'y', -3.2, -1, 1.6, FL1 + 1.75, 2.4, 1.6, parent=cE)

    def plaque(b):
        b.box((0, -0.01, 0), (0.42, 0.02, 0.16), "M_Museum_Brass", bev=0.004, amp=0.0, cuts=0)
    to_col(prop("GalleryV_Featured_Plaque", (-3.2, 1.6, FL1 + 0.72), -90, plaque), cE)
    to_col(prop("GalleryV_Stanchions", (-4.2, 1.6, FL1), 90, lambda b: stanchions(b, 2.4)), cE)
    to_col(prop("GalleryV_Bench", (-6.0, 1.6, FL1), 90, lambda b: bench_gallery(b, 1.6, "M_Fabric_Blue")), cE)
    art_slot("GalleryV_East_N", 'y', -3.2, -1, 4.4, FL1 + 1.6, 0.8, 1.0, parent=cE)
    art_slot("GalleryV_East_S", 'y', -3.2, -1, -4.6, FL1 + 1.6, 0.7, 0.9, frame="M_Museum_WoodDark", parent=cE)
    art_slot("GalleryV_North", 'x', IY1, -1, -3.9, FL1 + 1.6, 0.7, 0.9, parent=cE)
    art_slot("GalleryV_South", 'x', IY0, 1, -3.75, FL1 + 1.6, 0.7, 0.9, parent=cE)
    art_slot("GalleryV_North_B", 'x', IY1, -1, -6.3, FL1 + 1.6, 0.9, 1.1, frame="M_Museum_WoodDark", parent=cE)   # paredes lisas (ventanas ocultas en el interior)
    art_slot("GalleryV_South_B", 'x', IY0, 1, -6.3, FL1 + 1.6, 0.9, 1.1, parent=cE)
    art_slot("GalleryV_West_S", 'y', IX0, 1, -2.2, FL1 + 1.6, 1.0, 1.2, parent=cE)                               # a cada lado de la unica ventana oeste (y 0.6)
    art_slot("GalleryV_West_N", 'y', IX0, 1, 3.3, FL1 + 1.6, 0.9, 1.1, frame="M_Museum_WoodDark", parent=cE)

    # ---------------- Gallery VI (esculturas)
    for i, (y, h) in enumerate(((-4.1, 1.0), (-1.0, 0.8), (1.5, 1.1), (4.3, 0.9))):
        to_col(prop("GalleryVI_Pedestal_%d" % i, (5.4, y, FL1), 0, lambda b, h=h: pedestal(b, h, 0.55)), cE)

    def sculpt_a(b):   # losas apiladas y giradas (sin bolas), apoyada en el pedestal
        stack_slabs(b, "M_Museum_Stone")

    to_col(prop("GalleryVI_Sculpture_A", (5.4, -4.1, FL1 + 1.0), 0, sculpt_a), cE)
    to_col(prop("GalleryVI_Sculpture_B", (5.4, 1.5, FL1 + 1.1), 0, sculpt_helix), cE)
    to_col(prop("GalleryVI_Vitrine", (6.8, -1.0, FL1), 0, vitrine), cE)
    art_slot("GalleryVI_West_S", 'y', 3.2, 1, -4.6, FL1 + 1.6, 0.9, 1.1, frame="M_Frame_Silver", parent=cE)
    art_slot("GalleryVI_West_M", 'y', 3.2, 1, 0.3, FL1 + 1.6, 1.4, 1.0, parent=cE)
    art_slot("GalleryVI_West_N", 'y', 3.2, 1, 4.6, FL1 + 1.6, 0.8, 1.0, frame="M_Museum_WoodDark", parent=cE)
    art_slot("GalleryVI_East", 'y', IX1, -1, -0.9, FL1 + 1.6, 0.8, 1.0, frame="M_Frame_Silver", parent=cE)
    art_slot("GalleryVI_East_S", 'y', IX1, -1, -3.5, FL1 + 1.6, 1.0, 1.2, parent=cE)                              # a cada lado de la unica ventana este (y 1.2)
    art_slot("GalleryVI_East_N", 'y', IX1, -1, 3.6, FL1 + 1.6, 0.9, 1.1, frame="M_Museum_WoodDark", parent=cE)
    art_slot("GalleryVI_South", 'x', IY0, 1, 6.7, FL1 + 1.6, 0.9, 1.1, frame="M_Frame_Silver", parent=cE)        # paredes lisas (ventanas ocultas en el interior)
    art_slot("GalleryVI_North", 'x', IY1, -1, 6.7, FL1 + 1.6, 0.9, 1.1, parent=cE)

    # ---------------- Landing (mirador)
    to_col(prop("Landing_Bench", (2.68, 4.6, FL1), -90, lambda b: bench_gallery(b, 1.3, "M_Fabric_Olive")), cF)
    to_col(prop("Landing_Plant", (0.9, 4.6, FL1), 0, lambda b: plant_kentia(b, 3, face=math.radians(215), spread=math.radians(140))), cF)
    art_slot("Landing_South", 'x', 0.4, 1, -0.25, FL1 + 1.6, 1.0, 0.8, parent=cE)
    wall_sign("GalleryIV", "GALLERY IV", 'x', 0.4, 1, -2.0, FL1 + 3.05, coll=cF)
    wall_sign("GalleryV", "GALLERY V", 'y', -3.0, 1, -2.5, FL1 + 3.05, coll=cF)
    wall_sign("GalleryVI_A", "GALLERY VI", 'y', 3.0, -1, -2.5, FL1 + 3.05, coll=cF)
    wall_sign("GalleryVI_B", "GALLERY VI", 'y', 3.0, -1, 3.0, FL1 + 2.95, coll=cF)

    # ---------------- servicio: vestibulo de aseos (lavabos) y dos aseos
    # dos tocadores de un seno en el muro oeste (frente a +x), uno al sur y otro al norte de la entrada: el paso a los aseos queda libre
    for tag, yv in (("S", 0.85), ("N", 2.95)):
        to_col(prop("Restroom_Lobby_Counter_" + tag, (3.2, yv, FL0), 90, vanity), cSv)
        to_col(prop("Restroom_Lobby_Mirror_" + tag, (3.2, yv, FL0 + 1.65), 90, lambda b: mirror(b, 0.5, 0.7, 0.07)), cSv)
    to_col(prop("Restroom_Lobby_Dryer", (4.6, 1.875, FL0 + 1.25), -90, hand_dryer), cSv)
    to_col(prop("Restroom_Lobby_Bin", (4.4, 1.875, FL0), -90, pedal_bin), cSv)
    pictogram_sign("Restroom_1", 'W', 'y', 4.6, -1, 1.1, FL0 + 2.5, cSv)      # Restroom_1 = mujeres
    pictogram_sign("Restroom_2", 'M', 'y', 4.6, -1, 2.65, FL0 + 2.5, cSv)     # Restroom_2 = hombres
    for n, (y0, y1) in ((1, (0.4, 1.775)), (2, (1.925, 3.425))):
        cy = (y0 + y1) / 2
        to_col(prop("Restroom_%d_Toilet" % n, (7.23, cy, FL0), -90, toilet), cSv)
        to_col(prop("Restroom_%d_PaperHolder" % n, (7.15, y0, FL0 + 0.7), 180, paper_holder), cSv)     # pared sur, junto al inodoro
        to_col(prop("Restroom_%d_Brush" % n, (7.25, cy - 0.36, FL0), 0, toilet_brush), cSv)
        to_col(prop("Restroom_%d_Bin" % n, (7.3, cy + 0.36, FL0), -90, pedal_bin), cSv)
        to_col(prop("Restroom_%d_Hook" % n, (5.0, y1, FL0 + 1.6), 0, coat_hook), cSv)                 # pared norte, junto a la puerta
        art_slot("Restroom_%d_Print" % n, 'x', y1, -1, 5.9, FL0 + 1.5, 0.35, 0.45, frame="M_Frame_Silver", parent=cSv)
    # puertas de servicio abiertas 90 grados (pivote en la bisagra, la hoja queda a lo largo de +x)
    for dn, kw in (("StairHall_Restrooms", dict(push=True)), ("Restroom_1", dict(lock=True, pictogram="W")),
                   ("Restroom_2", dict(lock=True, pictogram="M")), ("StairHall_Maintenance", dict(push=True))):
        sp = leaf_spec(dn)
        door_leaf(LEAF_NAME.get(dn, dn), sp["pivot"], sp["wl"], sp["hl"], sp["ang"], coll=cSv, **kw)

    # ---------------- servicio: mantenimiento (sala principal + anexo detras del paso ancho)
    to_col(prop("Maintenance_Lockers", (4.55, 3.85, FL0), 180, lockers), cSv)
    to_col(prop("Maintenance_FuseBox", (5.7, 3.575, FL0 + 1.5), 180, utility), cSv)
    to_col(prop("Maintenance_Sink", (6.95, 3.575, FL0), 180, utility_sink), cSv)
    to_col(prop("Maintenance_ToolRack", (7.6, 4.45, FL0 + 1.5), -90, tool_rack), cSv)
    to_col(prop("Maintenance_MopBucket", (4.7, 5.05, FL0), 0, wring_mop_bucket), cSv)
    to_col(prop("Maintenance_MopLean", (3.55, 5.3, FL0), 90, mop_lean), cSv)
    to_col(prop("Maintenance_Broom", (7.33, 5.35, FL0), -90, broom), cSv)
    to_col(prop("Maintenance_DustPan", (6.9, 5.0, FL0), -90, dustpan), cSv)
    to_col(prop("Maintenance_Cart", (3.47, 7.1, FL0), 90, cleaning_cart), cSv)
    to_col(prop("Maintenance_Shelves", (4.35, 8.35, FL0), 0, product_shelf), cSv)
    to_col(prop("Maintenance_Workbench", (6.55, 8.2, FL0), 0, workbench), cSv)

    def boxes(b):
        b.box((0, 0, 0.18), (0.45, 0.35, 0.36), "M_Museum_AwningB", bev=0.01, amp=0.0, cuts=0)
        b.box((0.02, 0.01, 0.5), (0.36, 0.3, 0.28), "M_Paper", rot=(0, 0, 9), bev=0.01, amp=0.0, cuts=0)
    to_col(prop("Maintenance_Boxes", (7.2, 6.4, FL0), 0, boxes), cSv)

# ======================================================================= luminarias (modelos)
def _profile(b, zs_rs, mat, cx=0.0, cy=0.0, seg=24, **kw):
    """Loft de revolucion con el eje en (cx, cy): zs_rs = [(z absoluta, radio)]."""
    loft(b, [(z, r, r, 0.0) for (z, r) in zs_rs], mat, seg=seg, xf=Matrix.Translation((cx, cy, 0.0)), **kw)


def chandelier(b, cx, cy, zc):
    """Arana clasica de laton: florón de escayola + dosel, cadena, columna torneada, dos pisos de brazos en S (4 + 8) con
    palmatoria (bobeche), manguito de vela y bombilla en llama, y remate colgante. Simetrica; diametro ~1.3 m; la pieza mas baja a zc - 1.08."""
    br = "M_Museum_Brass"
    z0 = zc                                                    # techo
    # florón de escayola con molduras concentricas y dosel de laton
    _profile(b, [(z0, 0.40), (z0 - 0.008, 0.40), (z0 - 0.012, 0.385), (z0 - 0.018, 0.385), (z0 - 0.022, 0.35), (z0 - 0.028, 0.34), (z0 - 0.03, 0.30),
                 (z0 - 0.038, 0.28), (z0 - 0.04, 0.2), (z0 - 0.05, 0.15), (z0 - 0.05, 0.09)], "M_Interior_Ceiling", cx, cy, seg=24)
    _profile(b, [(z0 - 0.045, 0.085), (z0 - 0.056, 0.095), (z0 - 0.07, 0.08), (z0 - 0.085, 0.05), (z0 - 0.098, 0.03), (z0 - 0.1, 0.02)], br, cx, cy, seg=16)
    # cadena: eslabones alternos en planos perpendiculares
    for i in range(7):
        zl = z0 - 0.14 - i * 0.07
        pts = []
        for k in range(12):
            t = k * math.tau / 12
            u, v = 0.0175 * math.cos(t), 0.042 * math.sin(t)
            pts.append((cx + (u if i % 2 == 0 else 0.0), cy + (0.0 if i % 2 == 0 else u), zl + v))
        tube(b, pts, 0.0035, br, seg=4, closed=True)
    # columna torneada
    zt = z0 - 0.64                                             # parte alta de la columna
    col_prof = [(zt, 0.028), (zt - 0.02, 0.03), (zt - 0.04, 0.05), (zt - 0.055, 0.07), (zt - 0.075, 0.078), (zt - 0.095, 0.066), (zt - 0.11, 0.04),   # urna alta
                (zt - 0.125, 0.03), (zt - 0.14, 0.046), (zt - 0.15, 0.046), (zt - 0.16, 0.03),                                                              # anillos
                (zt - 0.175, 0.05), (zt - 0.2, 0.095), (zt - 0.24, 0.12), (zt - 0.28, 0.108), (zt - 0.31, 0.075), (zt - 0.335, 0.04),                       # bulbo grande
                (zt - 0.35, 0.026), (zt - 0.365, 0.03), (zt - 0.39, 0.05), (zt - 0.41, 0.032), (zt - 0.425, 0.014), (zt - 0.44, 0.0035)]                    # remate colgante
    _profile(b, col_prof, br, cx, cy, seg=14)
    # brazos en S: salen horizontales de la columna, bajan y suben hasta rematar vertical bajo la palmatoria
    def arm(a, z_start, rho0, reach, rise, dip, r_tube):
        ca, sa = math.cos(a), math.sin(a)
        pts, rads = [], []
        n = 10
        for k in range(n + 1):
            t = k / n
            rho = rho0 + (reach - rho0) * math.sin(math.pi / 2 * t) - 0.05 * math.sin(math.tau * t) * (reach / 0.65)
            z = z_start - dip * math.sin(math.pi * t) + rise * t * t
            pts.append((cx + rho * ca, cy + rho * sa, z))
            rads.append(r_tube * (1.0 - 0.35 * t))
        tube(b, pts, rads, br, seg=8)
        ex, ey, ez = pts[-1]
        # palmatoria (bobeche), manguito de vela, aro y llama
        _profile(b, [(ez - 0.02, 0.01), (ez - 0.008, 0.018), (ez, 0.046), (ez + 0.008, 0.052), (ez + 0.012, 0.03), (ez + 0.014, 0.02)], br, ex, ey, seg=10)
        b.cyl((ex, ey, ez + 0.014 + 0.05), 0.016, 0.1, "M_Ceramic", seg=8, bev=0, amp=0.0)
        b.cyl((ex, ey, ez + 0.114 + 0.005), 0.0205, 0.01, br, seg=6, bev=0, amp=0.0)
        zb = ez + 0.119
        _profile(b, [(zb, 0.013), (zb + 0.012, 0.0165), (zb + 0.03, 0.0155), (zb + 0.046, 0.0095), (zb + 0.06, 0.0045), (zb + 0.07, 0.0016)], "M_Bulb_Warm", ex, ey, seg=8)
    for k in range(8):   # piso bajo
        arm(k * math.tau / 8, zt - 0.2, 0.09, 0.65, 0.22, 0.07, 0.0095)
    for k in range(4):   # piso alto, entre los brazos bajos
        arm(math.tau / 16 + k * math.tau / 4, zt - 0.07, 0.07, 0.38, 0.16, 0.05, 0.0085)


def pendant_lamp(b, x, y, zc):
    """Lampara colgante: dosel de laton, varilla fina, pantalla campana de esmalte blanco (doble piel con aro de laton) y bombilla de pera. Borde de la pantalla a zc - 0.54."""
    br = "M_Museum_Brass"
    _profile(b, [(zc, 0.075), (zc - 0.012, 0.075), (zc - 0.02, 0.06), (zc - 0.03, 0.035), (zc - 0.04, 0.02)], br, x, y, seg=14)
    b.seg((x, y, zc - 0.03), (x, y, zc - 0.28), 0.006, br, seg=8)
    zs_ = zc - 0.28
    _profile(b, [(zs_, 0.026), (zs_ - 0.012, 0.03), (zs_ - 0.024, 0.026)], br, x, y, seg=10)                    # casquillo superior
    outer = [(zs_ - 0.02, 0.034), (zs_ - 0.04, 0.07), (zs_ - 0.09, 0.12), (zs_ - 0.16, 0.17), (zs_ - 0.22, 0.2), (zs_ - 0.26, 0.21)]
    inner = [(z + 0.003 if k == len(outer) - 1 else z, r - 0.006) for k, (z, r) in enumerate(outer)][::-1]
    _profile(b, outer + inner, "M_Ceramic", x, y, seg=20, closed=True)
    tube(b, [(x + 0.2085 * math.cos(k * math.tau / 24), y + 0.2085 * math.sin(k * math.tau / 24), zs_ - 0.26) for k in range(24)], 0.0055, br, seg=4, closed=True)   # aro de laton del borde
    b.cyl((x, y, zs_ - 0.065), 0.019, 0.07, br, seg=8, bev=0, amp=0.0)                                     # portalamparas dentro de la pantalla
    zb = zs_ - 0.1
    _profile(b, [(zb, 0.015), (zb - 0.02, 0.026), (zb - 0.05, 0.034), (zb - 0.09, 0.034), (zb - 0.12, 0.024), (zb - 0.14, 0.008), (zb - 0.145, 0.002)], "M_Bulb_Warm", x, y, seg=12)


def dome_light(b, x, y, zc, plate="M_Interior_Ceiling"):
    """Plafon redondo a ras de techo: placa de escayola, aro de laton, cupula de vidrio opal (loft) y boton central."""
    br = "M_Museum_Brass"
    _profile(b, [(zc, 0.25), (zc - 0.01, 0.25), (zc - 0.014, 0.23), (zc - 0.016, 0.215)], plate, x, y, seg=28)
    tube(b, [(x + 0.212 * math.cos(k * math.tau / 28), y + 0.212 * math.sin(k * math.tau / 28), zc - 0.02) for k in range(28)], 0.011, br, seg=6, closed=True)
    _profile(b, [(zc - 0.02, 0.205), (zc - 0.04, 0.2), (zc - 0.06, 0.18), (zc - 0.08, 0.145), (zc - 0.097, 0.1), (zc - 0.108, 0.05), (zc - 0.112, 0.012)], "M_Bulb_Warm", x, y, seg=20)
    b.cyl((x, y, zc - 0.118), 0.016, 0.012, br, seg=10, bev=0, amp=0.0)


def lantern(b, x, y, zc):
    """Farol clasico de laton colgado del techo (zc): florón, cadena de eslabones, anilla, remate torneado, tejado de dos pisos con chimenea,
    cuerpo troncopiramidal con cuatro montantes, tres bastidores y CUATRO cristales, vela con llama dentro, base con peana invertida y gota.
    Altura total ~1.07 m: pieza mas baja a zc - 1.07."""
    br = "M_Museum_Brass"
    zt = zc - 0.55                                   # arriba del cuerpo (cornisa)
    zb = zc - 0.955                                  # abajo del cuerpo (placa de base)
    hb, ht = 0.115, 0.165                            # semiancho abajo / arriba (ejes de los montantes)
    # florón del techo
    _profile(b, [(zc, 0.08), (zc - 0.008, 0.08), (zc - 0.016, 0.062), (zc - 0.03, 0.034), (zc - 0.042, 0.02)], br, x, y, seg=16)
    # anilla de suspension (a traves del remate) y cadena de eslabones alternos hasta ella
    za = zt + 0.225
    tube(b, [(x + 0.024 * math.cos(q * math.tau / 16), y, za + 0.024 * math.sin(q * math.tau / 16)) for q in range(16)], 0.0045, br, seg=6, closed=True)
    z_top, z_bot = zc - 0.033, za + 0.02
    n = max(3, int(round((z_top - z_bot - 0.068) / 0.05)) + 1)
    pitch = (z_top - z_bot - 0.068) / (n - 1)
    for k in range(n):
        zl = z_top - 0.034 - k * pitch
        pts = []
        for q in range(12):
            t = q * math.tau / 12
            u, v = 0.0165 * math.cos(t), 0.034 * math.sin(t)
            pts.append((x + (u if k % 2 == 0 else 0.0), y + (0.0 if k % 2 == 0 else u), zl + v))
        tube(b, pts, 0.0032, br, seg=4, closed=True)
    # remate torneado, chimenea y tejado a cuatro aguas en dos pisos
    _profile(b, [(zt + 0.13, 0.04), (zt + 0.142, 0.044), (zt + 0.15, 0.03), (zt + 0.158, 0.026), (zt + 0.166, 0.034), (zt + 0.178, 0.03), (zt + 0.19, 0.022),
                 (zt + 0.198, 0.012), (zt + 0.205, 0.006)], br, x, y, seg=14)
    b.cyl((x, y, zt + 0.1075), 0.034, 0.045, br, seg=14, r2=0.04, bev=0, amp=0.0)                          # chimenea
    b.cyl((x, y, zt + 0.0675), 0.1273, 0.055, br, seg=4, r2=0.0566, rot=(0, 0, 45), bev=0, amp=0.0)        # tejado alto
    b.cyl((x, y, zt + 0.020), 0.2687, 0.040, br, seg=4, r2=0.1273, rot=(0, 0, 45), bev=0, amp=0.0)         # tejado bajo (voladizo)
    b.box((x, y, zt - 0.003), (2 * ht + 0.05, 2 * ht + 0.05, 0.012), br, bev=0.003, amp=0.0, cuts=0)       # cornisa del cuerpo

    def frame(zz, c_, r_=0.0065):
        rr = 0.012
        path = []
        for (sx, sy, a0) in ((1, 1, 0), (-1, 1, 90), (-1, -1, 180), (1, -1, 270)):
            for j in range(4):
                a = math.radians(a0 + 90 * j / 3)
                path.append((x + sx * (c_ - rr) + rr * math.cos(a), y + sy * (c_ - rr) + rr * math.sin(a), zz))
        tube(b, path, r_, br, seg=6, closed=True)
    frame(zt - 0.014, ht - 0.002)
    frame(zb + 0.016, hb - 0.002)
    zmid = (zt + zb) / 2 + 0.03
    frame(zmid, hb + (ht - hb) * ((zmid - zb) / (zt - zb)) - 0.002, 0.0045)
    for sx in (-1, 1):
        for sy in (-1, 1):
            b.seg((x + sx * hb, y + sy * hb, zb), (x + sx * ht, y + sy * ht, zt), 0.0095, br, seg=10)
    for (nx, ny) in ((1, 0), (-1, 0), (0, 1), (0, -1)):   # cuatro cristales (trapecios inclinados dentro de los montantes)
        tx, ty = -ny, nx

        def corner(sg, h_, zz):
            return (x + nx * h_ + tx * sg * (h_ - 0.012), y + ny * h_ + ty * sg * (h_ - 0.012), zz)
        pts = [corner(-1, hb, zb + 0.025), corner(1, hb, zb + 0.025), corner(1, ht, zt - 0.025), corner(-1, ht, zt - 0.025)]
        nv = Vector((nx, ny, -(ht - hb) / (zt - zb))).normalized() * 0.004
        b.prism(pts, tuple(nv), "M_Vitrine_Glass", amp=0.0)
    # vela sobre un platillo, con la llama dentro
    b.cyl((x, y, zb + 0.012), 0.05, 0.008, br, seg=14, r2=0.044, bev=0, amp=0.0)
    b.cyl((x, y, zb + 0.06), 0.0185, 0.088, "M_Ceramic", seg=12, bev=0, amp=0.0)
    zf = zb + 0.104
    _profile(b, [(zf, 0.004), (zf + 0.008, 0.0095), (zf + 0.02, 0.0085), (zf + 0.032, 0.0045), (zf + 0.042, 0.0008)], "M_Bulb_Warm", x, y, seg=8)
    # base: placa, peana invertida y gota
    b.box((x, y, zb), (2 * hb + 0.05, 2 * hb + 0.05, 0.016), br, bev=0.003, amp=0.0, cuts=0)
    b.cyl((x, y, zb - 0.037), 0.052, 0.058, br, seg=4, r2=0.1556, rot=(0, 0, 45), bev=0, amp=0.0)
    _profile(b, [(zb - 0.115, 0.001), (zb - 0.104, 0.0035), (zb - 0.094, 0.01), (zb - 0.086, 0.017), (zb - 0.074, 0.02), (zb - 0.066, 0.012)], br, x, y, seg=12)


def track_loop(b, xa, xb, ya, yb, ztop, w=0.045, t=0.03, mat="M_Track_White"):
    """Carril de focos rectangular (una sola malla, esquinas a inglete) pegado por arriba a ztop."""
    bm = bmesh.new()
    rings = {}
    for nm, (hx, hy) in (("o", ((xb - xa) / 2 + w / 2, (yb - ya) / 2 + w / 2)), ("i", ((xb - xa) / 2 - w / 2, (yb - ya) / 2 - w / 2))):
        for z in (ztop, ztop - t):
            rings[(nm, z)] = [bm.verts.new(q) for q in ((xa + (xb - xa) / 2 - hx, ya + (yb - ya) / 2 - hy, z), (xa + (xb - xa) / 2 + hx, ya + (yb - ya) / 2 - hy, z),
                                                        (xa + (xb - xa) / 2 + hx, ya + (yb - ya) / 2 + hy, z), (xa + (xb - xa) / 2 - hx, ya + (yb - ya) / 2 + hy, z))]
    for k in range(4):
        k2 = (k + 1) % 4
        for z in (ztop, ztop - t):
            bm.faces.new((rings[("o", z)][k], rings[("o", z)][k2], rings[("i", z)][k2], rings[("i", z)][k]))
        for nm in ("o", "i"):
            bm.faces.new((rings[(nm, ztop)][k], rings[(nm, ztop)][k2], rings[(nm, ztop - t)][k2], rings[(nm, ztop - t)][k]))
    b._finish(bm, (0, 0, 0), (0, 0, 0), mat, 0.004, 0.0, w)


def spot_head(b, P, ztop, T):
    """Foco de carril: adaptador, vastago, horquilla con pivotes, cuerpo cilindrico con aletas de refrigeracion, bisel y lente (M_Bulb_Warm).
    P = (x, y) del carril, ztop = cota del techo/viga, T = punto al que apunta."""
    W, Mt = "M_Track_White", "M_Museum_Metal"
    zb = ztop - 0.03
    b.box((P[0], P[1], zb - 0.011 + 0.002), (0.05, 0.05, 0.022), Mt, bev=0, amp=0.0, cuts=0)                  # adaptador bajo el carril
    zcb = zb - 0.022 - 0.05
    b.seg((P[0], P[1], zb - 0.02), (P[0], P[1], zcb), 0.011, Mt, seg=8)                                             # vastago
    Hc = Vector((P[0], P[1], zcb - 0.1))
    d = (Vector(T) - Hc).normalized()
    e = [math.degrees(q) for q in d.to_track_quat('Z', 'Y').to_euler()]
    a = d.cross(Vector((0, 0, 1))).normalized()
    A = Vector((P[0], P[1], zcb))
    b.seg(tuple(A + a * 0.058), tuple(A - a * 0.058), 0.0065, Mt, seg=8)                                           # travesano de la horquilla
    for sg in (-1, 1):
        b.seg(tuple(A + a * 0.058 * sg), tuple(Hc + a * 0.058 * sg), 0.0055, Mt, seg=5)                             # brazos
        b.seg(tuple(Hc + a * 0.05 * sg), tuple(Hc + a * 0.068 * sg), 0.011, Mt, seg=8)                              # pivote
    b.cyl(tuple(Hc), 0.044, 0.17, W, rot=e, seg=10, r2=0.05, bev=0, amp=0.0)                                         # cuerpo
    for s in (-0.058, -0.012):                                                                                      # aletas de refrigeracion
        b.cyl(tuple(Hc + d * s), 0.0545 + 0.004 * s / 0.085, 0.006, Mt, rot=e, seg=6, bev=0, amp=0.0)
    b.cyl(tuple(Hc + d * 0.079), 0.056, 0.016, Mt, rot=e, seg=10, bev=0, amp=0.0)                                   # bisel
    b.cyl(tuple(Hc + d * 0.0855), 0.045, 0.006, "M_Bulb_Warm", rot=e, seg=10, bev=0, amp=0.0)                        # lente
    return Hc, d


def gallery_tracks(b, rn, ztop, ins=1.0):
    """Carril rectangular a `ins` de las paredes de la sala y un foco por cuadro (y por escultura/vitrina) apuntando a la obra."""
    r = ROOMS[rn]
    f = fz(r)[0]
    xa, xb, ya, yb = r[0] + ins, r[1] - ins, r[2] + ins, r[3] - ins
    if rn == "Gallery_IV":
        xa, xb = -2.0, 2.0
    track_loop(b, xa, xb, ya, yb, ztop)
    pre = {"Gallery_I": "GalleryI_", "Gallery_II": "GalleryII_", "Gallery_IV": "GalleryIV_", "Gallery_V": "GalleryV_", "Gallery_VI": "GalleryVI_"}[rn]
    tg = []
    for ob in bpy.data.objects:
        if ob.name.startswith("ArtSlot_" + pre):
            th = ob.rotation_euler.z
            n = Vector((math.sin(th), -math.cos(th), 0.0))      # normal de la pared hacia la sala (el frente del cuadro es -y local)
            tg.append((Vector(ob.location) + n * 0.04, n))
        elif ob.name.startswith(pre) and any(k in ob.name for k in ("Pedestal", "Vitrine")):
            tg.append((Vector(ob.location) + Vector((0, 0, 0.9 if "Vitrine" in ob.name else 1.15)), Vector((0, 0, 0))))
    used = []
    for (T, n) in tg:
        q = Vector((T.x, T.y, 0)) + n * ins
        x = min(max(q.x, xa), xb)
        y = min(max(q.y, ya), yb)
        dx0, dx1, dy0, dy1 = abs(x - xa), abs(x - xb), abs(y - ya), abs(y - yb)
        m = min(dx0, dx1, dy0, dy1)        # proyecta sobre el lado mas cercano del carril
        if m == dx0:
            x = xa
        elif m == dx1:
            x = xb
        elif m == dy0:
            y = ya
        else:
            y = yb
        for _ in range(6):                  # separa focos que caerian casi en el mismo punto
            if any(abs(x - ux) < 0.3 and abs(y - uy) < 0.3 for (ux, uy) in used):
                if m in (dx0, dx1):
                    y += 0.35 if y + 0.35 < yb - 0.1 else -0.35
                else:
                    x += 0.35 if x + 0.35 < xb - 0.1 else -0.35
            else:
                break
        used.append((x, y))
        spot_head(b, (x, y), ztop, (T.x, T.y, T.z))


# ======================================================================= techos y luminarias
def ceilings_and_lights(cS, cU, cLt):
    b = HB("Int_Ceiling_Features", 0.5)
    # Gallery III: falso techo con cornisa de luz
    r = ROOMS["Gallery_III"]
    b.box(((r[0] + r[1]) / 2, (r[2] + r[3]) / 2, C0 - 0.42), (r[1] - r[0] - 0.7, r[3] - r[2] - 0.7, 0.12), "M_Interior_Ceiling", bev=0.02, amp=0.004, cuts=3)
    for (x, y, sx, sy) in (((r[0] + r[1]) / 2, r[2] + 0.37, r[1] - r[0] - 0.74, 0.03), ((r[0] + r[1]) / 2, r[3] - 0.37, r[1] - r[0] - 0.74, 0.03),
                           (r[0] + 0.37, (r[2] + r[3]) / 2, 0.03, r[3] - r[2] - 0.74), (r[1] - 0.37, (r[2] + r[3]) / 2, 0.03, r[3] - r[2] - 0.74)):
        b.box((x, y, C0 - 0.34), (sx, sy, 0.04), "M_Bulb_Warm", bev=0, amp=0.0, cuts=0)
    for (x, y) in (((r[0] + r[1]) / 2 - 1.0, (r[2] + r[3]) / 2), ((r[0] + r[1]) / 2 + 1.0, (r[2] + r[3]) / 2)):
        pendant_lamp(b, x, y, C0 - 0.48)       # cuelga del falso techo; el borde de la pantalla queda a 2.9 m sobre el suelo
    # Gallery IV: casetones
    r = ROOMS["Gallery_IV"]
    for k in range(1, 4):
        x = r[0] + k * (r[1] - r[0]) / 4
        b.box((x, (r[2] + r[3]) / 2, C1 - 0.12), (0.16, r[3] - r[2], 0.24), "M_Interior_Ceiling", bev=0.02, amp=0.004, cuts=3)
    for k in range(1, 4):
        y = r[2] + k * (r[3] - r[2]) / 4
        b.box(((r[0] + r[1]) / 2, y, C1 - 0.12), (r[1] - r[0], 0.16, 0.24), "M_Interior_Ceiling", bev=0.02, amp=0.004, cuts=3)
    # Gallery V y VI: techo plano con cornisa de escayola (la pone trims() en todo el perimetro) y un panel rectangular moldurado centrado, sin madera
    for rn in ("Gallery_V", "Gallery_VI"):
        r = ROOMS[rn]
        cx, cy = (r[0] + r[1]) / 2, (r[2] + r[3]) / 2
        for (hx, hy, bw, th) in ((1.65, 4.9, 0.1, 0.04), (1.43, 4.68, 0.04, 0.02)):   # marco exterior y junquillo interior (nacen del techo hacia abajo)
            zc_ = C1 - th / 2
            for sgn in (-1, 1):
                b.box((cx + sgn * hx, cy, zc_), (bw, 2 * hy + bw, th), "M_Interior_Ceiling", bev=0.006, amp=0.001, cuts=0)
                b.box((cx, cy + sgn * hy, zc_), (2 * hx - bw, bw, th), "M_Interior_Ceiling", bev=0.006, amp=0.001, cuts=0)
    # Hall: florón + lampara de arana de laton
    chandelier(b, 0.0, -2.8, C0)
    # carriles de focos en galerias: un carril rectangular a 1 m de las paredes y un foco por obra
    for rn, zt_ in (("Gallery_I", C0), ("Gallery_II", C0), ("Gallery_IV", C1 - 0.24), ("Gallery_V", C1), ("Gallery_VI", C1)):
        gallery_tracks(b, rn, zt_)
    # servicio: tubos fluorescentes / plafones
    for rn in ("Restroom_Lobby", "Restroom_1", "Restroom_2", "Maintenance", "Maintenance_Annex"):
        r = ROOMS[rn]
        fluorescent(b, (r[0] + r[1]) / 2, (r[2] + r[3]) / 2, C0, 1.2, 0.2, 'x')
    for x in (4.0, 5.5, 7.0):
        b.seg((x, 5.45, C0 - 0.3), (x, 3.7, C0 - 0.3), 0.04, "M_Museum_Metal")
    b.seg((3.3, 5.45, C0 - 0.3), (7.5, 5.45, C0 - 0.3), 0.05, "M_Museum_Metal")
    # farol colgante en el hueco de la escalera (pieza mas baja a C1 - 1.07 = 7.03: mas de 2.3 m sobre cualquier suelo transitable y fuera de escalera y barandillas)
    lantern(b, -1.85, 3.0, C1)
    dome_light(b, 1.0, 3.0, C1)
    b.finish(cU)

    # luces de trabajo (Blender)
    def light(nm, pos, energy, colr, kind='POINT', size=0.3, rot=None, spot=None):
        ld = bpy.data.lights.new(nm, kind)
        ld.energy = energy
        ld.color = colr
        try:
            ld.shadow_soft_size = size
        except Exception:
            pass
        if spot:
            ld.spot_size = math.radians(spot)
            ld.spot_blend = 0.4
        ob = bpy.data.objects.new(nm, ld)
        ob.location = pos
        if rot:
            ob.rotation_euler = rot
        cLt.objects.link(ob)
    warm, neutral, cool = (1.0, 0.82, 0.62), (1.0, 0.9, 0.78), (0.86, 0.92, 1.0)
    light("Light_Hall", (0, -2.8, C0 - 1.0), 650, warm, size=0.6)
    light("Light_Hall_Front", (0, -4.6, C0 - 0.6), 250, warm, size=0.8)
    light("Light_StairHall", (1.0, 3.0, C0 - 0.4), 450, warm, size=0.6)
    light("Light_StairVoid", (-1.85, 3.0, 7.3), 300, warm, size=0.3)
    light("Light_GalleryI", (-5.4, -2.7, C0 - 0.5), 550, neutral, size=0.8)
    light("Light_GalleryII", (5.4, -2.7, C0 - 0.5), 550, neutral, size=0.8)
    light("Light_GalleryIII", (-5.4, 3.0, C0 - 0.75), 380, warm, size=0.8)
    light("Light_GalleryIV", (0, -2.7, C1 - 0.5), 550, neutral, size=0.8)
    light("Light_GalleryV_N", (-5.4, 3.2, C1 - 0.6), 420, neutral, size=0.8)
    light("Light_GalleryV_S", (-5.4, -3.2, C1 - 0.6), 420, neutral, size=0.8)
    light("Light_GalleryVI_N", (5.4, 3.0, C1 - 0.6), 450, neutral, size=0.8)
    light("Light_GalleryVI_S", (5.4, -3.0, C1 - 0.6), 450, neutral, size=0.8)
    light("Light_Landing", (1.0, 3.0, C1 - 0.25), 300, warm, size=0.6)
    light("Light_Restroom_1", (6.175, 1.0875, C0 - 0.3), 110, cool, size=0.4)
    light("Light_Restroom_2", (6.175, 2.675, C0 - 0.3), 110, cool, size=0.4)
    light("Light_Restroom_Lobby", (3.9, 1.9125, C0 - 0.3), 160, warm, size=0.4)
    light("Light_Maintenance", (5.4, 4.6, C0 - 0.3), 260, cool, size=0.5)
    light("Light_Maintenance_Annex", (5.4, 7.3, C0 - 0.3), 260, cool, size=0.5)
    d = Vector((-3.2, 1.6, FL1 + 1.75)) - Vector((-5.2, 1.6, C1 - 0.35))
    light("Spot_GalleryV_Featured", (-5.2, 1.6, C1 - 0.35), 350, neutral, kind='SPOT', size=0.1, rot=d.to_track_quat('-Z', 'Y').to_euler(), spot=38)


def presentation(cP):
    sc = bpy.context.scene
    w = bpy.data.worlds.get("World") or bpy.data.worlds.new("World")
    sc.world = w
    w.use_nodes = True
    bg = next(n for n in w.node_tree.nodes if n.type == 'BACKGROUND')
    bg.inputs["Color"].default_value = (0.3, 0.38, 0.5, 1)
    bg.inputs["Strength"].default_value = 0.4
    cams = {
        "Cam_Int_Hall": ((0.0, -5.2, FL0 + 1.65), (0.0, 0.5, FL0 + 1.4)),
        "Cam_Int_Hall_B": ((-0.6, -0.9, FL0 + 1.65), (2.3, -4.4, FL0 + 1.35)),
        "Cam_Int_Hall_C": ((1.3, -2.4, FL0 + 1.65), (-3.0, -4.6, FL0 + 1.7)),
        "Cam_Int_GalleryI": ((-3.6, -0.2, FL0 + 1.7), (-6.6, -4.2, FL0 + 1.3)),
        "Cam_Int_GalleryII": ((3.6, -5.1, FL0 + 1.7), (6.8, -0.4, FL0 + 1.3)),
        "Cam_Int_GalleryIII": ((-4.0, 0.9, FL0 + 1.6), (-6.5, 4.8, FL0 + 1.2)),
        "Cam_Int_StairHall": ((1.9, 0.9, FL0 + 1.7), (-1.7, 3.4, FL0 + 2.0)),
        "Cam_Int_RestroomLobby": ((4.45, 3.3, FL0 + 1.7), (3.3, 1.2, FL0 + 1.1)),
        "Cam_Int_Maintenance": ((5.0, 6.6, FL0 + 1.9), (5.6, 3.8, FL0 + 0.8)),
        "Cam_Int_MaintenanceAnnex": ((7.3, 6.2, FL0 + 1.8), (4.4, 8.4, FL0 + 0.9)),
        "Cam_Int_Restroom1": ((4.95, 1.2, FL0 + 1.7), (7.4, 1.0, FL0 + 0.7)),
        "Cam_Int_GalleryIV": ((0.0, 0.0, FL1 + 1.7), (0.0, -5.5, FL1 + 1.6)),
        "Cam_Int_GalleryV": ((-3.6, -4.6, FL1 + 1.7), (-7.6, 1.2, FL1 + 1.9)),
        "Cam_Int_GalleryVI": ((3.8, -5.0, FL1 + 1.8), (7.6, 1.6, FL1 + 2.0)),
        "Cam_Int_Landing": ((1.7, 0.9, FL1 + 1.7), (-1.6, 3.8, FL1 + 0.4)),
        "Cam_Int_GalleryVII": ((-2.4, 9.5, FL0 + 1.65), (3.0, 14.8, FL0 + 1.9)),
        "Cam_Int_GalleryVII_B": ((6.4, 20.5, FL0 + 1.7), (-3.0, 12.0, FL0 + 1.4)),
    }
    for n, (pos, tgt) in cams.items():
        cd = bpy.data.cameras.new(n)
        cd.lens = 20
        cd.clip_start = 0.05
        co = bpy.data.objects.new(n, cd)
        co.location = pos
        co.rotation_euler = (Vector(tgt) - Vector(pos)).to_track_quat('-Z', 'Y').to_euler()
        cP.objects.link(co)
    sc.camera = bpy.data.objects["Cam_Int_Hall"]


def build():
    L.clear_scene()
    ART_WALL.clear()
    build_open()
    random.seed(5)
    cS = col("Interior_Structure")
    cO = col("Interior_Doors_Windows")
    cT = col("Interior_Wall_Finish")
    cE = col("Interior_Exhibition_Rooms")
    cF = col("Interior_Furniture")
    cSv = col("Interior_Service_Areas")
    cU = col("Interior_Utilities")
    cLt = col("Interior_Lighting")
    cP = col("Presentation")
    structure(cS)
    annex_shell(cS)
    trims(cT)
    restroom_tiles(cT)
    door_casings(cO)
    stairs(cS)
    hatch(cU)
    furnish(cE, cF, cSv)
    ceilings_and_lights(cS, cU, cLt)
    wing(cS, cT, cE, cF, cLt)
    windows_int(cO)     # despues de colgar los cuadros: las cortinas se apartan de ellos
    presentation(cP)
    settle()
    for ob in bpy.context.scene.collection.objects:
        print("SUELTO:", ob.name)
    print("objetos:", len(bpy.data.objects), "materiales:", len(bpy.data.materials),
          "tris aprox:", sum(len(o.data.polygons) for o in bpy.data.objects if o.type == 'MESH'))


if __name__ == "__main__":
    build()
