"""Helper de promote_npc.py (Blender en segundo plano): importa un FBX en escena vacia y vuelca un resumen JSON. SOLO LECTURA.
Uso: blender -b --python fbx_info.py -- <fbx> <out.json>"""
import bpy, sys, json
a = sys.argv[sys.argv.index('--') + 1:]; fbx, out = a[0], a[1]
bpy.ops.object.select_all(action='SELECT'); bpy.ops.object.delete()
bpy.ops.import_scene.fbx(filepath=fbx)
O = [o for o in bpy.data.objects]; meshes = [o for o in O if o.type == 'MESH']; arms = [o for o in O if o.type == 'ARMATURE']
ob = max(meshes, key=lambda o: len(o.data.vertices)); me = ob.data
sk = [k.name for k in me.shape_keys.key_blocks] if me.shape_keys else []
co = [v.co.copy() for v in me.vertices]
info = {'meshes': [m.name for m in meshes], 'mesh': ob.name, 'verts': len(me.vertices), 'faces': len(me.polygons),
        'bbox_min': [round(min(c[k] for c in co), 4) for k in range(3)], 'bbox_max': [round(max(c[k] for c in co), 4) for k in range(3)],
        'bones': sorted(b.name for b in arms[0].data.bones) if arms else [], 'shape_keys': sk,
        'materials': [m.name if m else None for m in me.materials], 'uv_layers': [u.name for u in me.uv_layers],
        'vgroups': len(ob.vertex_groups), 'roots': sorted(o.name for o in O if o.parent is None), 'mesh_parent': ob.parent.name if ob.parent else None}
json.dump(info, open(out, 'w'), indent=1); print('FBXINFO', info['verts'], info['faces'])
