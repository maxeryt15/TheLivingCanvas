"""Tourist: manguito interior de piel sobre el borde superior del short. Al plegarse el cuerpo (sentada, agachada, inclinada) la camiseta sube respecto al short y se ve a traves
del cuerpo (no hay piel en la espalda bajo la ropa). Se extruye el lazo superior del short H hacia arriba (bajo la camiseta), metido INSET hacia el eje; los vertices nuevos heredan los
pesos y las shape keys de su vertice de origen (desplazados igual), asi acompanan al short y rellenan el hueco cuando la camiseta sube. Material Tou_clothes_Paint (se funde con la ropa), UV/colores del vertice
de origen. Uso: blender -b WORK.blend --python fix_tou_band.py -- [--h 0.07 --inset 0.008 --save]"""
import bpy, bmesh, sys, collections
from mathutils import Vector
a = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else []
def opt(k, d): return float(a[a.index(k) + 1]) if k in a else d
H = opt('--h', 0.07); INSET = opt('--inset', 0.008)
ob = bpy.data.objects['Tou_Mesh']; me = ob.data; mats = [m.name for m in me.materials]; assert not ob.get('tlc_waist_band'), 'ya aplicado'
SK = mats.index('Tou_clothes_Paint')
bm = bmesh.new(); bm.from_mesh(me); bm.verts.ensure_lookup_table(); bm.edges.ensure_lookup_table(); bm.faces.ensure_lookup_table()
cl = [f for f in bm.faces if mats[f.material_index] == 'Tou_clothes_Paint']
par = {}
def fd(x):
    while par[x] != x: par[x] = par[par[x]]; x = par[x]
    return x
for f in cl:
    for v in f.verts: par.setdefault(v.index, v.index)
for f in cl:
    vs = [v.index for v in f.verts]
    for v in vs[1:]: par[fd(v)] = fd(vs[0])
isl = collections.defaultdict(set)
for v in par: isl[fd(v)].add(v)
up = max(isl.values(), key=lambda c: sum(bm.verts[v].co.z for v in c) / len(c)); lo = max((c for c in isl.values() if c is not up), key=len)
top = [e for e in bm.edges if e.is_boundary and all(v.index in lo for v in e.verts) and all(0.93 < v.co.z < 1.05 for v in e.verts)]
tv = {v for e in top for v in e.verts}; ctr = sum((v.co for v in tv), Vector()) / len(tv); ctr.z = 0
r = bmesh.ops.extrude_edge_only(bm, edges=top)
nv = [x for x in r['geom'] if isinstance(x, bmesh.types.BMVert)]; nf = [x for x in r['geom'] if isinstance(x, bmesh.types.BMFace)]
shp = list(bm.verts.layers.shape.values())
for v in nv:
    rad = Vector((v.co.x - ctr.x, v.co.y - ctr.y, 0)); d = Vector((0, 0, H)) - (rad.normalized() * INSET if rad.length > 1e-6 else Vector())
    v.co += d
    for l in shp: v[l] = v[l] + d
uvl = bm.loops.layers.uv.values(); cll = list(bm.loops.layers.float_color.values()) + list(bm.loops.layers.color.values())
fl = 0
for f in nf:
    f.material_index = SK; f.smooth = True
    c = f.calc_center_median(); rad = Vector((c.x - ctr.x, c.y - ctr.y, 0))
    if f.normal.dot(rad) < 0: f.normal_flip(); fl += 1
bm.to_mesh(me); bm.free(); me.update(); ob['tlc_waist_band'] = len(nf)
print('BAND verts', len(nv), 'faces', len(nf), 'flipped', fl)
if '--save' in a: bpy.ops.wm.save_mainfile(); print('SAVED')
