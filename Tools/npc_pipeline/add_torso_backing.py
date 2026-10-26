"""Torso interior de respaldo (piel, oculto bajo la ropa). El cuerpo de los NPCs solo tiene cuello/cabeza/brazos/manos/piernas: bajo la ropa NO hay torso, asi que por el cuello, el
dobladillo o cualquier costura fina se ve el suelo/fondo. Se anade una malla cerrada (anillos elipticos de 16 vertices entre ZTOP y ZBOT, tapas arriba y abajo), metida INSET m
dentro de la ropa de cada franja, con pesos copiados del vertice de ropa/piel mas cercano, material de piel, UV/colores del vertice de piel mas cercano y shape keys = reposo.
Uso: blender -b WORK.blend --python add_torso_backing.py -- Pref [--ztop 1.46 --zbot 0.80 --inset 0.014 --save]   (sin --save solo memoria; sirve como --fix de see_through.py)"""
import bpy, bmesh, sys, math
from mathutils import Vector
from mathutils.kdtree import KDTree
a = sys.argv[sys.argv.index('--') + 1:]
pref = a[0]
def opt(k, d): return float(a[a.index(k) + 1]) if k in a else d
ZTOP, ZBOT, INSET, NR, NS = opt('--ztop', 1.46), opt('--zbot', 0.80), opt('--inset', 0.014), 16, int(opt('--slices', 12))
ob = bpy.data.objects[pref + '_Mesh']; me = ob.data; mats = [m.name if m else '' for m in me.materials]
assert not ob.get('tlc_torso_backing'), 'ya aplicado'
skin_i = [i for i, m in enumerate(mats) if 'skin' in m.lower()][0]
GARM = ('cloth', 'suit', 'apron', 'dress', 'shirt', 'blouse', 'jacket')
bm = bmesh.new(); bm.from_mesh(me); bm.verts.ensure_lookup_table(); bm.faces.ensure_lookup_table()
cv = set(); sv = set()
for f in bm.faces:
    n = mats[f.material_index].lower()
    if any(g in n for g in GARM): cv.update(v.index for v in f.verts)
    elif f.material_index == skin_i: sv.update(v.index for v in f.verts)
body = sorted(cv | sv)
bvs = [bm.verts[i] for i in body]; svs = [bm.verts[i] for i in sorted(sv)]
rings = []
for k in range(NS):
    z = ZTOP - (ZTOP - ZBOT) * k / (NS - 1)
    t = max(0.0, min(1.0, (z - 1.30) / (ZTOP - 1.30)))            # 0 en torso, 1 en el cuello
    xlim = 0.21 * (1 - t) + 0.075 * t
    pts = [bm.verts[i].co for i in body if abs(bm.verts[i].co.z - z) < 0.025 and abs(bm.verts[i].co.x) < xlim]
    if len(pts) < 6: print('TORSO slice', round(z, 3), 'sin puntos'); rings.append(None); continue
    x0, x1 = min(p.x for p in pts), max(p.x for p in pts); y0, y1 = min(p.y for p in pts), max(p.y for p in pts)
    rings.append((z, (x0 + x1) / 2, (y0 + y1) / 2, max((x1 - x0) / 2 - INSET, 0.035), max((y1 - y0) / 2 - INSET, 0.035)))
rings = [r for r in rings if r]
kd = KDTree(len(body)); [kd.insert(bm.verts[i].co, j) for j, i in enumerate(body)]; kd.balance()
ks = KDTree(len(sv)); sl = sorted(sv); [ks.insert(bm.verts[i].co, j) for j, i in enumerate(sl)]; ks.balance()
dl = bm.verts.layers.deform.verify(); shp = list(bm.verts.layers.shape.values())
uvl = list(bm.loops.layers.uv.values()); col = list(bm.loops.layers.float_color.values()) + list(bm.loops.layers.color.values())
vloop = {}
for f in bm.faces:
    if f.material_index == skin_i:
        for l in f.loops: vloop.setdefault(l.vert.index, l)
def newvert(co):
    v = bm.verts.new(co)
    for l in shp: v[l] = co.copy()
    _, j, _ = kd.find(co); src = bvs[j]
    wts = sorted(((g, w) for g, w in src[dl].items()), key=lambda gw: -gw[1])[:4]; s = sum(w for _, w in wts) or 1.0
    for g, w in wts: v[dl][g] = w / s
    return v
grid = []
for (z, cx, cy, rx, ry) in rings:
    grid.append([newvert(Vector((cx + rx * math.cos(2 * math.pi * i / NR), cy + ry * math.sin(2 * math.pi * i / NR), z))) for i in range(NR)])
top_c = newvert(Vector((rings[0][1], rings[0][2], rings[0][0] + 0.01))); bot_c = newvert(Vector((rings[-1][1], rings[-1][2], rings[-1][0] - 0.01)))
faces = []
for r in range(len(grid) - 1):
    for i in range(NR):
        j = (i + 1) % NR; faces.append((grid[r][i], grid[r][j], grid[r + 1][j], grid[r + 1][i]))
for i in range(NR): faces.append((top_c, grid[0][(i + 1) % NR], grid[0][i])); faces.append((bot_c, grid[-1][i], grid[-1][(i + 1) % NR]))
nf = []
for fv in faces:
    f = bm.faces.new(fv); f.material_index = skin_i; f.smooth = True; nf.append(f)
bmesh.ops.recalc_face_normals(bm, faces=nf)
cz = Vector((0, 0, 1)); mid = Vector((rings[0][1], rings[0][2], (rings[0][0] + rings[-1][0]) / 2))
for f in nf:       # normales hacia fuera del eje del torso
    if f.normal.dot(f.calc_center_median() - Vector((mid.x, mid.y, f.calc_center_median().z))) < 0 and abs(f.normal.z) < 0.9: f.normal_flip()
for f in nf:
    for l in f.loops:
        _, j, _ = ks.find(l.vert.co); src = vloop.get(sl[j])
        if src:
            for u in uvl: l[u].uv = src[u].uv
            for c in col: l[c] = src[c]
bm.to_mesh(me); bm.free(); me.update(); ob['tlc_torso_backing'] = len(nf)
print('TORSO', pref, 'anillos', len(rings), 'caras', len(nf), 'z', round(rings[0][0], 3), round(rings[-1][0], 3), 'ancho max', round(max(r[3] for r in rings) * 2, 3))
if '--save' in a: bpy.ops.wm.save_mainfile(); print('TORSO saved')
