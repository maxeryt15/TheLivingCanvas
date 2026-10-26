"""Tourist: la tira del bolso (Tou_BagStrap) en Face es una cinta de una sola capa con 28 de 37 caras orientadas HACIA la camiseta (normal contraria), por lo que con
backface culling (Unity) desaparece casi entera; en Blender (sin culling) no se nota. Correccion minima: voltear SOLO las caras de la cinta a < 10 mm de la camiseta
cuya normal apunta hacia ella. No cambia vertices, UV, pesos ni shape keys. Uso: blender -b WORK.blend --python fix_tou_strap.py -- [--save]"""
import bpy, bmesh, sys, json
from mathutils.bvhtree import BVHTree
ob = bpy.data.objects['Tou_Mesh']; me = ob.data; mats = [m.name for m in me.materials]
bm = bmesh.new(); bm.from_mesh(me); bm.faces.ensure_lookup_table()
cl = [f for f in bm.faces if mats[f.material_index] == 'Tou_clothes_Paint']
P = [v.co.copy() for v in bm.verts]; tris = []
for f in cl:
    vs = [v.index for v in f.verts]
    for k in range(1, len(vs) - 1): tris.append((vs[0], vs[k], vs[k + 1]))
bvh = BVHTree.FromPolygons(P, tris)
flipped = []; kept = []
for f in bm.faces:
    if mats[f.material_index] != 'Tou_BagStrap': continue
    loc, nor, idx, dist = bvh.find_nearest(f.calc_center_median(), 0.08)
    if loc is not None and dist < 0.010 and f.normal.dot(nor) < 0: flipped.append(f.index)
    else: kept.append((f.index, round(dist * 1000, 1) if loc else None))
for i in flipped: bm.faces[i].normal_flip()
bm.to_mesh(me); bm.free(); me.update()
print('STRAPFIX flipped', len(flipped), flipped, 'kept', kept)
json.dump({'flipped_faces': flipped, 'kept': kept}, open(r'D:\TheLivingCanvas\ArtSource\_Exports\NPC_Validation\Tourist\reports\fix_strap.json', 'w'))
if '--save' in sys.argv: bpy.ops.wm.save_mainfile(); print('SAVED')
