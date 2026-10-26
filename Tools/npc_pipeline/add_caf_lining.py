"""Cafe: forro oscuro en forma de cono bajo la falda del vestido (tapa la entrepierna al sentarse). Cascaron unico, abierto abajo, DENTRO del vestido.
Apice cerca de la entrepierna (pesos pelvis/thigh_l/thigh_r); anillos hacia abajo; el anillo base toma pesos del triangulo de vestido mas cercano; intermedios = mezcla.
Material nuevo Caf_Lining_Mat (oscuro), insertado ANTES de NPC_MouthInside (que queda ultimo). Marca tlc_lining en el objeto (no reaplicable).
Uso: blender -b NPCs_Shell_Face_CAFE_WORK.blend --python add_caf_lining.py -- [--save]   Registra reports/fix_lining.json"""
import bpy, sys, json, math, collections, bmesh
sys.path.insert(0, r'D:\TheLivingCanvas\Tools\npc_pipeline')
import pose_lib as PL
from mathutils import Vector
from mathutils.bvhtree import BVHTree
from mathutils.interpolate import poly_3d_calc
a = sys.argv[sys.argv.index('--') + 1:]
ob = bpy.data.objects['Caf_Mesh']; arm = bpy.data.objects['Caf_Rig']; me = ob.data
assert not ob.get('tlc_lining'), 'ya aplicado'
N = 16; ZT = 0.90; ZB = 0.50; CB = (0.0, -0.03); RB = (0.17, 0.10)
PL.reset(arm); bpy.context.view_layer.update()
rest = [v.co.copy() for v in me.vertices]
mats = [m.name if m else None for m in me.materials]
CL = [p for p in me.polygons if mats[p.material_index] == 'Caf_clothes_Paint' and sum(rest[v].z for v in p.vertices) / len(p.vertices) > 0.4]
tl = []
for p in CL:
    vs = list(p.vertices)
    for k in range(1, len(vs) - 1): tl.append((vs[0], vs[k], vs[k + 1]))
bvh = BVHTree.FromPolygons(rest, tl)
vg = {g.name: g.index for g in ob.vertex_groups}
def gname(s): return next(n for n in vg if n.lower() == s)
PEL, TL_, TR_ = gname('pelvis'), gname('thigh_l'), gname('thigh_r')
def dress_w(pt):
    loc, nor, idx, dist = bvh.find_nearest(pt); t = tl[idx]; ws = poly_3d_calc([rest[k] for k in t], loc); acc = collections.Counter()
    for w, k in zip(ws, t):
        for g in me.vertices[k].groups: acc[ob.vertex_groups[g.group].name] += w * g.weight
    return acc
def norm(c, n=4):
    top = sorted(c.items(), key=lambda kv: -kv[1])[:n]; s = sum(v for _, v in top); return {k: v / s for k, v in top}
apexw = {PEL: .3, TL_: .35, TR_: .35}
# material
mat = bpy.data.materials.get('Caf_Lining_Mat') or bpy.data.materials.new('Caf_Lining_Mat')
mat.use_nodes = True
bsdf = next(n for n in mat.node_tree.nodes if n.type == 'BSDF_PRINCIPLED'); bsdf.inputs['Base Color'].default_value = (0.03, 0.03, 0.035, 1); bsdf.inputs['Roughness'].default_value = 1.0
mat.diffuse_color = (0.03, 0.03, 0.035, 1)
mouth = next(i for i, m in enumerate(me.materials) if m and m.name == 'NPC_MouthInside')
me.materials.append(mat)   # al final; luego se reordena
last = len(me.materials) - 1
# reordenar: lining antes de mouth -> intercambiar indices de poligonos
for p in me.polygons:
    if p.material_index == mouth: p.material_index = last
me.materials[mouth] = mat; me.materials[last] = bpy.data.materials['NPC_MouthInside']
lin_idx = mouth
bm = bmesh.new(); bm.from_mesh(me); bm.verts.ensure_lookup_table()
dl = bm.verts.layers.deform.verify(); sk = list(bm.verts.layers.shape.values()); uvl = list(bm.loops.layers.uv.values()); col = list(bm.loops.layers.float_color.values()) + list(bm.loops.layers.color.values())
# v3: tronco de cono abierto. Anillo superior (cadera, pesos pelvis) -> anillo inferior (z=ZB, pesos del vestido mas cercano: sigue al dobladillo)
RINGS = 4; RT = (0.13, 0.09); CT = (0.0, -0.017)
rings = []
for r in range(RINGS + 1):
    t = r / RINGS; z = ZT + (ZB - ZT) * t; rx = RT[0] + (RB[0] - RT[0]) * t; ry = RT[1] + (RB[1] - RT[1]) * t
    cx = CT[0] + (CB[0] - CT[0]) * t; cy = CT[1] + (CB[1] - CT[1]) * t
    rings.append([bm.verts.new((cx + math.cos(2 * math.pi * k / N) * rx, cy + math.sin(2 * math.pi * k / N) * ry, z)) for k in range(N)])
allv = [v for r in rings for v in r]
for v in allv:
    for l in sk: v[l] = v.co.copy()
def setw(v, w):
    v[dl].clear()
    for k, x in w.items(): v[dl][vg[k]] = x
base_w = [norm(dress_w(Vector(v.co))) for v in rings[-1]]
for r in range(RINGS + 1):
    t = (r / RINGS) ** 1.0
    for k, v in enumerate(rings[r]):
        c = collections.Counter()
        c[PEL] += 1 - t
        for b_, x in base_w[k].items(): c[b_] += t * x
        setw(v, norm(c))
faces = []
for r in range(RINGS):
    for k in range(N): faces.append((rings[r][k], rings[r][(k + 1) % N], rings[r + 1][(k + 1) % N], rings[r + 1][k]))
for f in faces:
    face = bm.faces.new(f); face.material_index = lin_idx; face.smooth = True
    for lp in face.loops:
        for l in uvl: lp[l].uv = (0.5, 0.5)
        for l in col: lp[l] = (0.04, 0.04, 0.045, 1.0)
bm.normal_update()
# comprobar que apuntan hacia fuera del eje; si no, voltear todas
cen = Vector((0, -0.03, 0.72)); bad = sum(1 for f in bm.faces if f.material_index == lin_idx and f.normal.dot(f.calc_center_median() - cen) < 0)
tot = sum(1 for f in bm.faces if f.material_index == lin_idx)
if bad > tot / 2:
    for f in bm.faces:
        if f.material_index == lin_idx: f.normal_flip()
bm.to_mesh(me); bm.free(); me.update()
ob['tlc_lining'] = 'cone N16 rings3'
rec = {'verts': len(allv), 'faces': len(faces), 'flipped': bad > tot / 2, 'zt': ZT, 'zb': ZB}
json.dump(rec, open(r'D:/TheLivingCanvas/ArtSource/_Exports/NPC_Validation/Cafe/reports/fix_lining.json', 'w'), indent=1)
print('LINING', rec)
if '--save' in a: bpy.ops.wm.save_mainfile(); print('SAVED')
