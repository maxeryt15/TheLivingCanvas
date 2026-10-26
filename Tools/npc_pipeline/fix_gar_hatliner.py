"""Gardener: el sombrero de paja es de una sola capa en la copa (solo caras hacia fuera): con backface culling (Unity) el interior es invisible y se ve hueco/transparente desde abajo.
Se duplica la copa (caras Gar_HatStraw/Gar_HatStrawB con centro a r<0.14 del eje del sombrero y normal hacia fuera/arriba), se voltean y se hunden INSET m hacia dentro (normales suavizadas)
formando un forro interior visible desde abajo; los vertices nuevos heredan pesos (cabeza), UV, colores y shape keys del origen (desplazados igual). Material Gar_HatStrawB.
Uso: blender -b WORK.blend --python fix_gar_hatliner.py -- [--inset 0.004 --save]   (sin --save solo en memoria; sirve como --fix de hat_rv.py)"""
import bpy, bmesh, sys, math, collections
from mathutils import Vector
a = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else []
def opt(k, d): return float(a[a.index(k) + 1]) if k in a else d
INSET = opt('--inset', 0.004); CX, CY, RCORE = -0.003, -0.045, 0.14
ob = bpy.data.objects['Gar_Mesh']; me = ob.data; mats = [m.name for m in me.materials]; assert not ob.get('tlc_hat_liner'), 'ya aplicado'
LIN = mats.index('Gar_HatStrawB')
bm = bmesh.new(); bm.from_mesh(me); bm.verts.ensure_lookup_table(); bm.faces.ensure_lookup_table()
crown = []
for f in bm.faces:
    if mats[f.material_index] not in ('Gar_HatStraw', 'Gar_HatStrawB'): continue
    c = f.calc_center_median(); r = math.hypot(c.x - CX, c.y - CY); n = f.normal
    radial = ((c.x - CX) * n.x + (c.y - CY) * n.y) / max(r, 1e-6)
    if r < RCORE and (n.z > 0.6 or (abs(n.z) <= 0.6 and radial > 0)): crown.append(f)
cs = set(crown); bnd = set()
for f in crown:
    for e in f.edges:
        if sum(1 for lf in e.link_faces if lf in cs) == 1: bnd.update(e.verts)
vn = collections.defaultdict(Vector)
for f in crown:
    for v in f.verts: vn[v.index] += f.normal
r = bmesh.ops.duplicate(bm, geom=crown)
nf = [g for g in r['geom'] if isinstance(g, bmesh.types.BMFace)]; nv = [g for g in r['geom'] if isinstance(g, bmesh.types.BMVert)]
src = {v: r['vert_map'][v] for v in []}
vm = r['vert_map']   # origen -> copia
bmesh.ops.reverse_faces(bm, faces=nf)
shp = list(bm.verts.layers.shape.values())
for ov, cv in vm.items():
    if not isinstance(ov, bmesh.types.BMVert): continue
    d = -vn[ov.index].normalized() * INSET if (vn[ov.index].length > 0 and ov not in bnd) else Vector()   # el aro inferior no se mueve: se suelda al original
    cv.co = ov.co + d
    for l in shp: cv[l] = ov[l] + d
for f in nf: f.material_index = LIN
ring = [ov for ov in bnd] + [vm[ov] for ov in bnd]
bmesh.ops.remove_doubles(bm, verts=ring, dist=1e-5)
bm.to_mesh(me); bm.free(); me.update(); ob['tlc_hat_liner'] = INSET
print('LINER crown faces', len(crown), 'verts', len(nv), 'faces', len(nf))
if '--save' in a:
    bpy.ops.wm.save_mainfile(); print('LINER saved')
