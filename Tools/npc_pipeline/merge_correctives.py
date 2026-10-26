"""Fusiona en la copia de trabajo las correctivas volcadas por batch_correctives.py (recrea shape keys + drivers).
Uso: blender -b WORK.blend --python merge_correctives.py -- json1 [json2 ...]   (guarda sobre el mismo WORK; hacer backup antes)
"""
import bpy, sys, json
from mathutils import Vector
a = sys.argv[sys.argv.index('--') + 1:]
import importlib.util
sys.path.insert(0, r'D:\TheLivingCanvas\Tools\npc_pipeline')
import make_corrective as MC
for path in a:
    j = json.load(open(path)); pref = j['pref']
    ob = bpy.data.objects[pref + '_Mesh']; arm = bpy.data.objects[pref + '_Rig']; sk = ob.data.shape_keys
    basis = sk.key_blocks[0]
    for kb in list(sk.key_blocks):
        if kb.name in j['keys']: ob.shape_key_remove(kb)
    for name, d in j['keys'].items():
        key = ob.shape_key_add(name=name, from_mix=False); key.relative_key = basis; key.value = 0.0
        for i, x, y, z in d['deltas']: key.data[i].co = basis.data[i].co + Vector((x, y, z))
        s = d['spec']
        MC.hat_driver(ob, arm, key, s['bone'], s['ax'], s['sg'], s['full_rad'], s['c'], s['lo'], s['hi'], s['last'])
    print('MERGED', pref, len(j['keys']), 'keys')
bpy.ops.wm.save_as_mainfile(filepath=MC.WORK)
print('MERGEDONE')
