"""NO idempotente: mezcla sobre los pesos actuales; aplicar SOLO sobre la linea base original (_BACKUP_before_layerw), nunca sobre su propio resultado. Aplica layer_weights.reweight('Gen') a una copia con los pesos originales y verifica que nada mas cambio. Uso: blender -b <baseline>.blend --python apply_gen_hem.py -- <salida.blend>"""
import bpy, sys, hashlib
sys.path.insert(0, r'D:\TheLivingCanvas\Tools\npc_pipeline')
import layer_weights as LW
def snap():
    d = {}
    for ob in bpy.data.objects:
        if ob.type != 'MESH': continue
        d[ob.name] = {i: tuple(sorted((ob.vertex_groups[g.group].name, round(g.weight, 5)) for g in v.groups)) for i, v in enumerate(ob.data.vertices)}
    return d
def keys():
    return {ob.name: [k.name for k in ob.data.shape_keys.key_blocks] if ob.data.shape_keys else [] for ob in bpy.data.objects if ob.type == 'MESH'}
before, k0 = snap(), keys()
n = LW.reweight('Gen')
after, k1 = snap(), keys()
chg = {o: [i for i in after[o] if after[o][i] != before[o][i]] for o in before}
print('HEMVERTS', n)
for o, l in chg.items():
    if l: print('CHANGED', o, len(l))
print('KEYS_SAME', k0 == k1)
print('MAXINF', max(len(w) for w in after['Gen_Mesh'].values()))
bpy.ops.wm.save_as_mainfile(filepath=sys.argv[sys.argv.index('--') + 1])
print('SAVED')
