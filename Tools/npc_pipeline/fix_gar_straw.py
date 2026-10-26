"""Gardener: brizna de paja de la boca mas detallada. Sustituye Gar_StrawStalk/Gar_StrawTip (14+47 caras, tallo de seccion cuadrada de 3 mm y espiga corta) por:
tallo redondo (6 lados) y ligeramente curvado, mas grueso en la boca y afinado hacia fuera, con dos nudos, extremo masticado deshilachado (3 astillas) dentro de la comisura,
y espiga de trigo (raquis + 7 pares de granos alternos en bipiramide + aristas finas). Misma ruta y largo (P0 en la boca, P1 fuera); todo pesado 100 % a 'head'; UV/colores a 0 como el original;
shape keys = reposo. Materiales: tallo/nudos/astillas -> Gar_StrawStalk; raquis/granos/aristas -> Gar_StrawTip.
Uso: blender -b WORK.blend --python fix_gar_straw.py -- [--save]   (sin --save solo en memoria)"""
import bpy, bmesh, sys, math
from mathutils import Vector, Matrix
ob = bpy.data.objects['Gar_Mesh']; me = ob.data; mats = [m.name for m in me.materials]; assert not ob.get('tlc_straw_v2'), 'ya aplicado'
iS, iT = mats.index('Gar_StrawStalk'), mats.index('Gar_StrawTip')
bm = bmesh.new(); bm.from_mesh(me); bm.verts.ensure_lookup_table(); bm.faces.ensure_lookup_table()
old = {v for f in bm.faces if f.material_index in (iS, iT) for v in f.verts}
P0 = Vector((0.0152, -0.1525, 1.5600)); P1 = Vector((0.0935, -0.2375, 1.5655))   # extremos del tallo original (boca / fuera)
d = (P1 - P0).normalized(); L = (P1 - P0).length
u = d.cross(Vector((0, 0, 1))).normalized(); w = u.cross(d).normalized()      # u horizontal, w ~ arriba
bmesh.ops.delete(bm, geom=list(old), context='VERTS')
head = ob.vertex_groups['head'].index; dl = bm.verts.layers.deform.verify(); shp = list(bm.verts.layers.shape.values())
def V(p):
    v = bm.verts.new(p); v[dl][head] = 1.0
    for l in shp: v[l] = p.copy()
    return v
def F(vs, mi):
    try: f = bm.faces.new(vs)
    except ValueError: return None
    f.material_index = mi; f.smooth = False; return f
def centre(t):   # eje curvado: arco suave hacia arriba y caida leve hacia la espiga
    return P0 + d * (L * t) + w * (0.004 * math.sin(math.pi * t) - 0.012 * max(0.0, t - 0.62) ** 2 / 0.14) + u * (0.0015 * math.sin(2 * math.pi * t))
def tang(t): return (centre(min(1, t + 0.01)) - centre(max(0, t - 0.01))).normalized()
def frame(t):
    tg = tang(t); uu = tg.cross(Vector((0, 0, 1))).normalized(); ww = uu.cross(tg).normalized(); return tg, uu, ww
def ring(t, r, n=6, rot=0.0):
    c = centre(t); tg, uu, ww = frame(t)
    return [V(c + (uu * math.cos(rot + 2 * math.pi * k / n) + ww * math.sin(rot + 2 * math.pi * k / n)) * r) for k in range(n)]
def bridge(a, b, mi):
    n = len(a)
    for k in range(n): F([a[k], a[(k + 1) % n], b[(k + 1) % n], b[k]], mi)
# ---- tallo: t 0.06 .. 0.66 (la espiga ocupa 0.66..1.0), 12 anillos con 2 nudos
ts = [0.06, 0.12, 0.2, 0.26, 0.285, 0.31, 0.4, 0.46, 0.5, 0.515, 0.54, 0.6]
rs = [0.0036, 0.0036, 0.0033, 0.0031, 0.0042, 0.0030, 0.0029, 0.0027, 0.0026, 0.0036, 0.0025, 0.0023]
rings = [ring(t, r, 6, 0.3 * i) for i, (t, r) in enumerate(zip(ts, rs))]
for a, b in zip(rings, rings[1:]): bridge(a, b, iS)
# nudos: el anillo ancho ya forma el abultamiento; el extremo exterior del tallo se cierra con raquis
# ---- extremo masticado (dentro de la comisura): 3 astillas que parten del primer anillo
r0 = rings[0]; c0 = centre(0.06); tg0, u0, w0 = frame(0.06)
for k in range(3):
    ang = 2 * math.pi * k / 3 + 0.4; out = (u0 * math.cos(ang) + w0 * math.sin(ang))
    a = r0[(2 * k) % 6]; b = r0[(2 * k + 1) % 6]; c_ = r0[(2 * k + 2) % 6]
    tipc = c0 - tg0 * 0.012 + out * (0.0030 + 0.0010 * k)
    t1 = V(tipc); t2 = V(tipc + tg0 * 0.0010 + out * 0.0014)
    F([a, b, c_, t2, t1][:3] + [t1], iS) if False else None
    F([a, b, t1], iS); F([b, c_, t2], iS); F([b, t2, t1], iS)
# tapa del extremo hacia boca (cierra el anillo con un punto central desplazado) para que no quede abierto
cap = V(c0 - tg0 * 0.0035)
for k in range(6): F([r0[(k + 1) % 6], r0[k], cap], iS)
# ---- espiga: raquis t 0.66 .. 0.99 (3 anillos de 4 lados) + 7 pares de granos y aristas
rt = [0.6, 0.74, 0.88, 0.985]; rr = [0.0023, 0.0020, 0.0016, 0.0009]
rac = [ring(t, r, 4, 0.5) for t, r in zip(rt, rr)]
bridge(rings[-1][:0] or rings[-1], rac[0], iS) if len(rings[-1]) == len(rac[0]) else None
# union tallo(6)-raquis(4): abanico triangular
a = rings[-1]; b = rac[0]
for k in range(6): F([a[k], a[(k + 1) % 6], b[min(3, (k * 4) // 6)]], iS)
for x, y in zip(rac, rac[1:]): bridge(x, y, iT)
tipv = V(centre(1.0) + tang(1.0) * 0.003)
for k in range(4): F([rac[-1][k], rac[-1][(k + 1) % 4], tipv], iT)
def grain(t, side, i):
    c = centre(t); tg, uu, ww = frame(t)
    sd = (uu if side == 0 else -uu); lift = 0.5 + 0.1 * i
    base = c + sd * 0.0022; axis = (tg * 0.55 + sd * 0.55 + ww * 0.08).normalized(); perp1 = ww; perp2 = axis.cross(perp1).normalized()
    ln = 0.0105 - 0.0004 * i; wd = 0.0030
    mid = base + axis * ln * 0.45
    ring4 = [V(mid + (perp1 * math.cos(a_) + perp2 * math.sin(a_)) * wd) for a_ in (0, math.pi / 2, math.pi, 3 * math.pi / 2)]
    bt = V(base); tp = V(base + axis * ln)
    for k in range(4): F([ring4[k], ring4[(k + 1) % 4], bt][::-1], iT); F([ring4[k], ring4[(k + 1) % 4], tp], iT)
    aw = V(tp.co + (axis + tg * 0.35 + sd * 0.15).normalized() * 0.016); aw1 = V(tp.co + perp1 * 0.0007); aw2 = V(tp.co - perp1 * 0.0007)
    F([tp, aw1, aw], iT); F([tp, aw, aw2], iT); F([aw1, aw2, aw][::-1], iT)
for i in range(7):
    t = 0.66 + 0.043 * i
    grain(t, 0, i); grain(t + 0.021, 1, i)
bmesh.ops.recalc_face_normals(bm, faces=[f for f in bm.faces if f.material_index in (iS, iT)])
bm.normal_update(); bm.to_mesh(me); bm.free(); me.update(); ob['tlc_straw_v2'] = 1
print('STRAWFIX verts', len(me.vertices), 'faces', len(me.polygons))
if '--save' in sys.argv: bpy.ops.wm.save_mainfile(); print('SAVED')
