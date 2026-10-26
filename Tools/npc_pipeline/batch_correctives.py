"""Genera varias familias de correctivas (con relajacion de aristas) para un NPC y las vuelca a JSON (NO guarda el .blend, asi se pueden
lanzar varios NPC en paralelo). Despues merge_correctives.py las fusiona en la copia de trabajo.
Uso: blender -b WORK.blend --python batch_correctives.py -- Pref spec.json salida.json
spec.json: {"Pref": [["PoseCalibrada", "Corrective_Nombre", "hueso_driver"], ...]}
"""
import bpy, sys, json
sys.path.insert(0, r'D:\TheLivingCanvas\Tools\npc_pipeline')
import make_corrective as MC
a = sys.argv[sys.argv.index('--') + 1:]
pref, spec, out = a[0], json.load(open(a[1]))[a[0]], a[2]
ob = bpy.data.objects[pref + '_Mesh']
for pose, name, bone in spec:
    try:
        MC.build(pref, pose, name, bone, do_relax=True)
    except Exception as e:
        print('BATCHFAIL', pref, pose, repr(e))
sk = ob.data.shape_keys
basis = sk.key_blocks[0]
data = {}
for kb in sk.key_blocks:
    if kb.name in MC.SPECS:
        d = [[i, *(kb.data[i].co - basis.data[i].co)] for i in range(len(kb.data)) if (kb.data[i].co - basis.data[i].co).length > 1e-7]
        data[kb.name] = dict(deltas=d, spec=MC.SPECS[kb.name])
json.dump({'pref': pref, 'keys': data}, open(out, 'w'))
print('BATCHDONE', pref, len(data), 'keys')
