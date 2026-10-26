"""Courier: rehace el martillo (de carpintero, con garra) y la llave inglesa con mas detalle y los separa del cuerpo (correa+anilla, 4 cm hacia fuera, inclinados ~9 deg).
Borra todas las caras de Cou_ToolSteel/Cou_ToolGrip (martillo+llave antiguos) y modela las nuevas con bmesh en Cou_Mesh. Pesos por herramienta (rigidas): pelvis (1-t) + thigh (t), mismo criterio que fix_cou_props.
Orden: aplicar DESPUES de fix_cou_props.py. Marca tlc_tools. Uso: blender -b NPCs_Shell_Face_COURIER_WORK.blend --python add_cou_tools.py -- [--save]   Registra reports/fix_tools.json"""
import bpy, sys, json, math, bmesh
sys.path.insert(0, r'D:\TheLivingCanvas\Tools\npc_pipeline')
import pose_lib as PL
from mathutils import Vector
a = sys.argv[sys.argv.index('--') + 1:]
ob = bpy.data.objects['Cou_Mesh']; arm = bpy.data.objects['Cou_Rig']; me = ob.data
assert ob.get('tlc_props_reweight'), 'aplicar fix_cou_props antes'
assert not ob.get('tlc_tools'), 'ya aplicado'
PL.reset(arm); bpy.context.view_layer.update()
mats = [m.name if m else None for m in me.materials]
M_ST, M_GR, M_LE, M_ME = (mats.index(n) for n in ('Cou_ToolSteel', 'Cou_ToolGrip', 'Cou_BeltLeather', 'Cou_BeltMetal'))
vgi = {g.name: g.index for g in ob.vertex_groups}
bm = bmesh.new(); bm.from_mesh(me); bm.verts.ensure_lookup_table()
dl = bm.verts.layers.deform.verify(); sk = list(bm.verts.layers.shape.values())
# --- posicion de los antiguos (para colocar los nuevos en el mismo sitio) y borrado
gr_vs = {v for f in bm.faces if f.material_index == M_GR for v in f.verts}
old_gr = sum((v.co for v in gr_vs), Vector()) / len(gr_vs)             # mango del martillo
steel_vs = {v for f in bm.faces if f.material_index == M_ST for v in f.verts}
wr_vs = [v for v in steel_vs if v.co.x < 0]; wr_c = sum((v.co for v in wr_vs), Vector()) / len(wr_vs)
cx0, cy0 = 0.0, -0.01
def radial(p, ang):
    u = Vector((math.cos(ang), math.sin(ang), 0)); return (p.x - cx0) * u.x + (p.y - cy0) * u.y
def _o(k, d): return float(a[a.index(k) + 1]) if k in a else d
ANG_H, ANG_W = math.radians(_o('--angh', 14)), math.radians(_o('--angw', -165)); NOFF_ = _o('--noff', 0.060); TFIX = _o('--t', 0)
R_H = radial(old_gr, math.radians(-30)) - 0.016; R_W = radial(wr_c, math.radians(-150)) - 0.010   # superficie de la correa
M_PO, M_NA = mats.index('Cou_PouchLeather'), mats.index('Cou_Nail'); M_CL = mats.index('Cou_clothes_Paint')
dead = [f for f in bm.faces if f.material_index in (M_ST, M_GR, M_LE, M_ME, M_PO, M_NA)]; dv = {v for f in dead for v in f.verts}
bmesh.ops.delete(bm, geom=dead, context='FACES')
bmesh.ops.delete(bm, geom=[v for v in dv if v.is_valid and not v.link_faces], context='VERTS')
bm.verts.ensure_lookup_table()
# --- helpers
NEW = []
class Frame:
    def __init__(s, ang, r0, zp, tilt, noff):
        s.u = Vector((math.cos(ang), math.sin(ang), 0)); s.t = Vector((-s.u.y, s.u.x, 0)); s.r0 = r0; s.zp = zp; s.c = math.cos(tilt); s.s = math.sin(tilt); s.noff = noff
    def W(s, n, t, z):   # n: hacia fuera desde la correa, t: tangencial, z: bajo el punto de cuelgue (z<0 abajo). Inclinacion alrededor del punto de cuelgue (n=noff).
        dn = n - s.noff; nn = s.noff + dn * s.c - z * s.s; zz = dn * s.s + z * s.c
        return Vector((cx0, cy0, s.zp + zz)) + s.u * (s.r0 + nn) + s.t * t
def nv(co):
    v = bm.verts.new(co)
    for l in sk: v[l] = co.copy()
    NEW.append(v); return v
def face(vs, mi, smooth):
    try: f = bm.faces.new(vs)
    except ValueError: return None
    f.material_index = mi; f.smooth = smooth; return f
def loft(secs, mi, smooth=True, caps=(True, True)):
    rows = [[nv(p) for p in s] for s in secs]; n = len(rows[0])
    for i in range(len(rows) - 1):
        for k in range(n):
            face((rows[i][k], rows[i][(k + 1) % n], rows[i + 1][(k + 1) % n], rows[i + 1][k]), mi, smooth)
    for end, cap in ((0, caps[0]), (-1, caps[1])):
        if cap:
            r = rows[end]; c = nv(sum((v.co for v in r), Vector()) / n)
            for k in range(n): face((c, r[(k + 1) % n], r[k]) if end == 0 else (c, r[k], r[(k + 1) % n]), mi, False)
    return rows
def ell(F, n0, t0, z0, an, at, N=10, rot=0.0):   # seccion eliptica en el plano n-t a altura z0
    return [F.W(n0 + an * math.cos(2 * math.pi * k / N + rot), t0 + at * math.sin(2 * math.pi * k / N + rot), z0) for k in range(N)]
def box(F, c, h, mi, smooth=False):   # c=(n,t,z), h=(hn,ht,hz) semiejes
    n, t, z = c; hn, ht, hz = h
    P = [(n + sn * hn, t + st * ht, z + sz * hz) for sz in (-1, 1) for st in (-1, 1) for sn in (-1, 1)]
    vs = [nv(F.W(*p)) for p in P]
    for idx in ((0, 1, 3, 2), (4, 6, 7, 5), (0, 4, 5, 1), (2, 3, 7, 6), (0, 2, 6, 4), (1, 5, 7, 3)): face([vs[j] for j in idx], mi, smooth)
def tube_path(F, path, radii, mi, N=8, smooth=True):   # tubo a lo largo de una curva (n,t,z); radii por punto (r1,r2)
    secs = []
    for i, p in enumerate(path):
        p0 = Vector(path[max(0, i - 1)]); p1 = Vector(path[min(len(path) - 1, i + 1)]); d = (p1 - p0).normalized()
        ref = Vector((0, 0, 1)) if abs(d.z) < 0.9 else Vector((0, 1, 0)); e1 = d.cross(ref).normalized(); e2 = d.cross(e1).normalized()
        r1, r2 = radii[i]
        secs.append([F.W(*(Vector(p) + e1 * r1 * math.cos(2 * math.pi * k / N) + e2 * r2 * math.sin(2 * math.pi * k / N))) for k in range(N)])
    return loft(secs, mi, smooth)
def torus(F, c, axis, R, r, mi, Nm=12, Nr=6):   # axis: 'n' (anillo en plano t-z), 'z' (plano n-t)
    n0, t0, z0 = c; rows = []
    for i in range(Nm):
        th = 2 * math.pi * i / Nm; sec = []
        for k in range(Nr):
            ph = 2 * math.pi * k / Nr; rr = R + r * math.cos(ph)
            if axis == 'n': sec.append(nv(F.W(n0 + r * math.sin(ph), t0 + rr * math.cos(th), z0 + rr * math.sin(th))))
            else: sec.append(nv(F.W(n0 + rr * math.cos(th), t0 + rr * math.sin(th), z0 + r * math.sin(ph))))
        rows.append(sec)
    for i in range(Nm):
        for k in range(Nr): face((rows[i][k], rows[i][(k + 1) % Nr], rows[(i + 1) % Nm][(k + 1) % Nr], rows[(i + 1) % Nm][k]), mi, True)
def finish(name, side):
    global NEW
    cz = sum(v.co.z for v in NEW) / len(NEW); t = TFIX if TFIX >= 0 else min(0.9, max(0.0, (0.92 - cz) / 0.22))
    for v in NEW:
        v[dl].clear(); v[dl][vgi['pelvis']] = 1 - t; v[dl][vgi['thigh_l' if side > 0 else 'thigh_r']] = t
    rec[name] = {'verts': len(NEW), 'cz': round(cz, 3), 't': round(t, 2)}; NEW = []
rec = {}
# ================= MARTILLO (cabeza arriba, mango abajo; carpintero con garra) =================
ZP = 0.905; NOFF = NOFF_; TILT = math.radians(9)
F = Frame(ANG_H, R_H, ZP, TILT, NOFF)
box(F, (NOFF / 2, 0, 0), (NOFF / 2 + 0.002, 0.013, 0.020), M_LE)                    # correa de cuero desde el cinturon
torus(F, (NOFF + 0.004, 0, -0.002), 'n', 0.011, 0.0028, M_ME)                         # anilla metalica
HN = NOFF + 0.020   # eje del mango (n)
torus(F, (HN, 0, -0.035), 'z', 0.0150, 0.0034, M_LE)                                  # presilla alrededor del mango
box(F, ((NOFF + HN) / 2 - 0.003, 0, -0.020), (0.012, 0.0045, 0.018), M_LE)
hz = [(0.012, 1.0), (0.0, 0.80), (-0.05, 0.80), (-0.10, 0.84), (-0.16, 0.92), (-0.21, 0.98), (-0.25, 1.06), (-0.275, 1.18), (-0.285, 1.0)]
loft([ell(F, HN, 0, z, 0.0085 * s, 0.0125 * s, 10) for z, s in hz], M_GR, True)       # mango (seccion eliptica, pomo ensanchado)
for z in (-0.12, -0.145, -0.17, -0.195):                                               # estrias de agarre
    loft([ell(F, HN, 0, z - 0.0035, 0.0082, 0.0120, 10), ell(F, HN, 0, z, 0.0093, 0.0138, 10), ell(F, HN, 0, z + 0.0035, 0.0082, 0.0120, 10)], M_GR, True, (False, False))
loft([ell(F, HN, 0, 0.012, 0.0098, 0.0135, 10), ell(F, HN, 0, 0.040, 0.0130, 0.0178, 10), ell(F, HN, 0, 0.056, 0.0125, 0.0172, 10)], M_ST, True)   # cuello + ojo
HZ = 0.036
def hsec(t, r, zc=HZ): return [F.W(HN + r * math.cos(2 * math.pi * k / 10 + 0.31), t, zc + r * math.sin(2 * math.pi * k / 10 + 0.31)) for k in range(10)]
loft([hsec(0.016, 0.0125), hsec(0.026, 0.0150), hsec(0.040, 0.0160), hsec(0.044, 0.0185), hsec(0.049, 0.0185), hsec(0.0505, 0.0150), hsec(0.0535, 0.0148)], M_ST, True)   # cabeza + cara de golpeo
for sg in (-1, 1):                                                                     # garra: dos puntas curvas hacia abajo
    path = [(HN + sg * 0.0045, -0.012 - 0.012 * i, HZ - 0.0018 * i ** 2 + 0.002) for i in range(7)]
    tube_path(F, path, [(0.0042 - 0.0004 * i, 0.0125 - 0.0014 * i) for i in range(7)], M_ST, 8, True)
loft([hsec(-0.014, 0.0100), hsec(0.016, 0.0125)], M_ST, True)
finish('hammer', +1)
# ================= LLAVE INGLESA (colgada de la anilla, cabeza abajo) =================
FW = Frame(ANG_W, R_W, ZP, TILT, NOFF)
box(FW, (NOFF / 2, 0, 0), (NOFF / 2 + 0.002, 0.012, 0.020), M_LE)
torus(FW, (NOFF + 0.004, 0, -0.002), 'n', 0.011, 0.0028, M_ME)
WN = NOFF + 0.004; TH = 0.0034
def slab(prof_t, prof_z, mi=M_ST):   # extrusion en n de un contorno convexo (t,z)
    pts = list(zip(prof_t, prof_z)); L1 = [nv(FW.W(WN - TH, t, z)) for t, z in pts]; L2 = [nv(FW.W(WN + TH, t, z)) for t, z in pts]; m = len(pts)
    for k in range(m): face((L1[k], L1[(k + 1) % m], L2[(k + 1) % m], L2[k]), mi, False)
    c1 = nv(sum((v.co for v in L1), Vector()) / m); c2 = nv(sum((v.co for v in L2), Vector()) / m)
    for k in range(m): face((c1, L1[(k + 1) % m], L1[k]), mi, False); face((c2, L2[k], L2[(k + 1) % m]), mi, False)
torus(FW, (WN, 0, -0.012), 'n', 0.0105, 0.0030, M_ST, 14, 6)                      # ojal de colgar
slab([-0.0125, 0.0125, 0.0105, -0.0105], [-0.020, -0.020, -0.075, -0.075])          # mango superior
slab([-0.0105, 0.0105, 0.0120, -0.0120], [-0.075, -0.075, -0.145, -0.145])          # mango inferior (ensancha)
slab([-0.0120, 0.0120, 0.0185, -0.0185], [-0.145, -0.145, -0.172, -0.172])          # cuello hacia la cabeza
slab([-0.0185, 0.0185, 0.0240, -0.0240], [-0.172, -0.172, -0.200, -0.200])          # cuerpo de la cabeza
slab([0.0065, 0.0240, 0.0230, 0.0065], [-0.200, -0.200, -0.246, -0.246])            # mandibula fija (+t)
slab([-0.0240, -0.0065, -0.0065, -0.0220], [-0.200, -0.200, -0.238, -0.238])        # mandibula movil (-t)
box(FW, (WN + TH + 0.0010, 0.0, -0.1300), (0.0010, 0.0060, 0.0360), M_ME)           # placa graduada
loft([ell(FW, WN + TH + 0.0030, -0.0105, -0.186, 0.0055, 0.0055, 12), ell(FW, WN + TH + 0.0030, -0.0105, -0.226, 0.0055, 0.0055, 12)], M_ST, True)   # tornillo sin fin
for k in range(6):                                                                     # moleteado
    z = -0.190 - k * 0.0065
    loft([ell(FW, WN + TH + 0.0030, -0.0105, z - 0.0016, 0.0055, 0.0055, 12), ell(FW, WN + TH + 0.0030, -0.0105, z, 0.0066, 0.0066, 12), ell(FW, WN + TH + 0.0030, -0.0105, z + 0.0016, 0.0055, 0.0055, 12)], M_ST, True, (False, False))
finish('wrench', -1)

# ================= CINTURON NUEVO (banda lisa que sigue la silueta de la ropa) + hebilla + bolsa de clavos =================
from mathutils.bvhtree import BVHTree
clv = [f for f in bm.faces if f.material_index == M_CL and sum(v.co.z for v in f.verts) / len(f.verts) > 0.4]
cbm = {v for f in clv for v in f.verts}
bvh = BVHTree.FromBMesh(bm) if False else None
tl_ = []
for f in clv:
    vs_ = list(f.verts)
    for k in range(1, len(vs_) - 1): tl_.append((vs_[0], vs_[k], vs_[k + 1]))
vl = sorted(cbm, key=lambda v: v.index); vix = {v: i for i, v in enumerate(vl)}
cb = BVHTree.FromPolygons([v.co.copy() for v in vl], [(vix[a_], vix[b_], vix[c_]) for a_, b_, c_ in tl_])
ZB = 0.905; NB = 96; BH = 0.022   # BH: semialtura de la banda
def cloth_r(ang):
    d = Vector((math.cos(ang), math.sin(ang), 0)); best = 0.0
    for z in (ZB - 0.020, ZB, ZB + 0.020):
        h = cb.ray_cast(Vector((cx0, cy0, z)) + d * 0.6, -d)
        if h[0] is not None: best = max(best, (h[0] - Vector((cx0, cy0, z))).length)
    return best
rr = [cloth_r(2 * math.pi * i / NB) for i in range(NB)]
rr = [max(rr[(i + k) % NB] for k in range(-3, 4)) for i in range(NB)]           # dilatar (nunca hundirse)
for _ in range(6): rr = [(rr[i - 1] + 2 * rr[i] + rr[(i + 1) % NB]) / 4 for i in range(NB)]   # suavizar
BT = 0.0055   # semigrosor
BELT = []
secs = []
for i in range(NB):
    ang = 2 * math.pi * i / NB; u = Vector((math.cos(ang), math.sin(ang), 0)); r = rr[i] + BT + 0.002
    c = Vector((cx0, cy0, ZB)) + u * r
    prof = [(-BT * 0.55, -BH), (BT * 0.55, -BH), (BT, -BH * 0.6), (BT, BH * 0.6), (BT * 0.55, BH), (-BT * 0.55, BH), (-BT, BH * 0.6), (-BT, -BH * 0.6)]
    secs.append([c + u * dn + Vector((0, 0, dz)) for dn, dz in prof])
rows = [[nv(p) for p in sc] for sc in secs]
for i in range(NB):
    for k in range(8): face((rows[i][k], rows[i][(k + 1) % 8], rows[(i + 1) % NB][(k + 1) % 8], rows[(i + 1) % NB][k]), M_LE, True)
BELT += list(NEW); NEW = []
def bw(vs):
    for v in vs:
        dv_ = Vector((v.co.x - cx0, v.co.y - cy0, 0)); dv_.normalize()
        loc, nor, idx, dist = cb.ray_cast(Vector((cx0, cy0, v.co.z)) + dv_ * 0.6, -dv_)       # capa EXTERIOR (camiseta) a la misma altura
        if loc is None: loc, nor, idx, dist = cb.find_nearest(v.co)
        t_ = tl_[idx]; ws = [0, 0, 0]
        from mathutils.interpolate import poly_3d_calc
        ws = poly_3d_calc([vl[vix[x]].co for x in t_], loc); acc = {}
        for w_, x in zip(ws, t_):
            for g_, ww in x[dl].items(): acc[g_] = acc.get(g_, 0) + w_ * ww
        top = sorted(acc.items(), key=lambda kv: -kv[1])[:4]; ss = sum(x for _, x in top)
        v[dl].clear()
        for g_, x in top: v[dl][g_] = x / ss
bw(BELT)
rec['belt'] = {'verts': len(BELT)}
# hebilla frontal (-y): marco metalico + lengueta + pasador + cola de la correa
FB = Frame(math.radians(-90), rr[int(NB * 0.75)] + 2 * BT + 0.002, ZB, 0.0, 0.0)
box(FB, (0.0020, 0, 0), (0.0030, 0.0270, 0.0250), M_ME); box(FB, (0.0045, 0, 0), (0.0015, 0.0195, 0.0170), M_LE)   # marco + hueco relleno de cuero oscuro
box(FB, (0.0050, 0, 0), (0.0012, 0.0030, 0.0200), M_ME)                                                           # lengueta
box(FB, (0.0030, 0.0420, 0), (0.0035, 0.0200, 0.0195), M_LE)                                                       # cola de la correa
box(FB, (0.0030, -0.0300, 0), (0.0033, 0.0050, 0.0225), M_LE)                                                      # pasador de cuero
BK = list(NEW); NEW = []
for v in BK: v[dl].clear(); v[dl][vgi['pelvis']] = 1.0
rec['buckle'] = {'verts': len(BK)}
# bolsa de clavos en la cadera trasera derecha, bien separada del martillo
PA = math.radians(125)
FP = Frame(PA, rr[int(NB * (PA % (2 * math.pi)) / (2 * math.pi)) % NB] + 2 * BT, ZB, math.radians(10), 0.0)
box(FP, (0.0015, 0, 0.0), (0.0035, 0.034, 0.022), M_LE)
loft([[FP.W(0.010 + 0.036 * (1 if k in (1, 2) else 0) * 0 + dn, dt, dz) for dn, dt, dz in ((-0.004, -0.046, 0.0), (0.0, -0.046, 0.0), (0.0, 0.046, 0.0), (-0.004, 0.046, 0.0))]], M_PO, False, (False, False)) if False else None
box(FP, (0.0170, 0, -0.056), (0.0150, 0.0450, 0.0440), M_PO)                                                        # cuerpo
box(FP, (0.0330, 0, -0.030), (0.0030, 0.0420, 0.0200), M_PO)                                                        # solapa
box(FP, (0.0345, 0, -0.012), (0.0020, 0.0060, 0.0050), M_ME)                                                        # broche
for k, dt in enumerate((-0.030, -0.014, 0.002, 0.018, 0.032)):                                                       # clavos asomando
    h = 0.020 + 0.006 * (k % 3); nn = 0.012 + 0.004 * (k % 2)
    loft([ell(FP, nn, dt, -0.010, 0.0016, 0.0016, 6), ell(FP, nn, dt, 0.010 + h * 0.5, 0.0013, 0.0013, 6), ell(FP, nn, dt, 0.010 + h, 0.0005, 0.0005, 6)], M_NA, True)
    loft([ell(FP, nn, dt, 0.010 + h, 0.0010, 0.0046, 6), ell(FP, nn, dt, 0.0122 + h, 0.0010, 0.0046, 6)], M_NA, False)
for v in NEW: v[dl].clear(); v[dl][vgi['pelvis']] = 1.0
rec['pouch'] = {'verts': len(NEW)}; NEW = []
bm.normal_update()
bm.to_mesh(me); bm.free(); me.update(); ob['tlc_tools'] = 'hammer+wrench v1'
print('TOOLS', rec, 'R_H', round(R_H, 3), 'R_W', round(R_W, 3))
json.dump(rec, open(r'D:/TheLivingCanvas/ArtSource/_Exports/NPC_Validation/Courier/reports/fix_tools.json', 'w'), indent=1)
if '--save' in a: bpy.ops.wm.save_mainfile(); print('SAVED')
