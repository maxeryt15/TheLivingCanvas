"""Experimento A (variante B4): sobre la LINEA BASE original aplica el arreglo aprobado (layer_weights.reweight('Gen')) y despues, solo donde sel_strength>0,
sustituye por gen_front.buildB (reparto lateral thigh_l/thigh_r mas ancho en el centro delantero). NO idempotente: usar solo sobre la linea base.
Uso: blender -b <copia_de_la_linea_base>.blend --python apply_gen_front.py -- <salida.blend> <json_pesos_salida>"""
import bpy, sys, json
sys.path.insert(0, r'D:\TheLivingCanvas\Tools\npc_pipeline')
R = r'D:\TheLivingCanvas\ArtSource\NPC\_Reports\gen_hem\w_%s.json'
W = {n: {int(k): v for k, v in json.load(open(R % n)).items()} for n in ('orig', 'final')}
ob = bpy.data.objects['Gen_Mesh']
cur = lambda i: {ob.vertex_groups[g.group].name: g.weight for g in ob.data.vertices[i].groups}
assert all(abs(cur(i).get(b, 0) - v) < 1e-5 for i in range(0, 9030, 7) for b, v in W['orig'][i].items()), 'no es la linea base original'
import layer_weights as LW
LW.reweight('Gen')
import gen_front as GF
bad = max(abs(cur(i).get(b, 0) - v) for i in GF.hem for b, v in W['final'][i].items())
print('CHECK reweight == final json, max diff', round(bad, 5))
P = dict(x0=0.12, x1=0.24, ys=0.04, zt=1.05, xsf=0.3)
wd = GF.buildB(P, W)
n = 0
for i in GF.hem:
    if GF.sel_strength(i, P) > 0: GF.apply({i: wd[i]}); n += 1
print('FRONT verts modified', n)
dump = {i: cur(i) for i in range(len(ob.data.vertices))}
json.dump(dump, open(sys.argv[sys.argv.index('--') + 2], 'w'))
bpy.ops.wm.save_as_mainfile(filepath=sys.argv[sys.argv.index('--') + 1]); print('SAVED')
