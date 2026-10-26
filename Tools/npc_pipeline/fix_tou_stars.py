"""Tourist: las calcomanias de estrellas del bolso (Tou_BagStar0-4) tienen 168 de 358 caras orientadas hacia DENTRO del bolso (87 sueltas + 81 mitades de pares duplicados de
signo opuesto) -> invisibles con backface culling, y el FBX descarta una de cada par al azar. Correccion minima: voltear (normal_flip) SOLO las caras de estrella que estan
>0 mm por encima de la superficie del bolso (Canvas/Flap/Leather), cuya normal apunta hacia dentro segun la normal de la superficie Y segun el centro del bolso.
Mantiene numero de vertices/caras (guardas del exportador); no cambia posiciones, UV, pesos ni keys. Uso: blender -b WORK.blend --python fix_tou_stars.py -- [--save]"""
import bpy, bmesh, sys, json
from mathutils import Vector
from mathutils.bvhtree import BVHTree
ob = bpy.data.objects['Tou_Mesh']; me = ob.data; mats = [m.name for m in me.materials]
assert not ob.get('tlc_star_fix'), 'ya aplicado'
bm = bmesh.new(); bm.from_mesh(me); bm.faces.ensure_lookup_table()
P = [v.co.copy() for v in bm.verts]; tr = []
for f in bm.faces:
    if mats[f.material_index] in ('Tou_BagCanvas', 'Tou_BagFlap', 'Tou_BagLeather'):
        vs = [v.index for v in f.verts]
        for k in range(1, len(vs) - 1): tr.append((vs[0], vs[k], vs[k + 1]))
bvh = BVHTree.FromPolygons(P, tr)
cv = {v.index for f in bm.faces if mats[f.material_index] == 'Tou_BagCanvas' for v in f.verts}; C = sum((P[i] for i in cv), Vector()) / len(cv)
flip = []
for f in bm.faces:
    if 'BagStar' not in mats[f.material_index]: continue
    loc, nor, i, d = bvh.find_nearest(f.calc_center_median(), 0.1)
    if loc is None: continue
    c = f.calc_center_median()
    if (c - loc).dot(nor) > 0 and f.normal.dot(nor) < 0 and (c - C).dot(f.normal) < 0: flip.append(f.index)
for i in flip: bm.faces[i].normal_flip()
bm.to_mesh(me); bm.free(); me.update(); ob['tlc_star_fix'] = len(flip)
print('STARFIX flipped', len(flip))
json.dump({'flipped_faces': flip}, open(r'D:\TheLivingCanvas\ArtSource\_Exports\NPC_Validation\Tourist\reports\fix_stars.json', 'w'))
if '--save' in sys.argv: bpy.ops.wm.save_mainfile(); print('SAVED')
