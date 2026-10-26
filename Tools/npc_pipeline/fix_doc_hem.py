"""Docent: al caminar (Walk 9-37) el muslo que sube atraviesa el dobladillo de la chaqueta (dientes de pantalon por delante de la tela; layer_clip Walk hasta 23 mm / 49 mm).
Causa: el faldon de la chaqueta (isla superior bajo z=1.0) conserva pesos de torso/pelvis y no acompana al muslo. Correccion (solo pesos, ninguna posicion): layer_weights.reweight('Doc', ztop=1.0, tmax=0.8, xs=0.08)
sobre la isla de la chaqueta bajo ztop (mezcla suave hacia thigh_l/thigh_r). NO idempotente: se niega a aplicarse dos veces (propiedad tlc_hem_reweight en el objeto).
Uso: blender -b NPCs_Shell_Face_DOCENT_WORK.blend --python fix_doc_hem.py -- [--save]   Registra reports/fix_hem.json (pesos antes/despues de los vertices cambiados)."""
import bpy, sys, json
sys.path.insert(0, r'D:\TheLivingCanvas\Tools\npc_pipeline')
import pose_lib as PL, layer_clip_scan as LC, layer_weights as LW
a = sys.argv[sys.argv.index('--') + 1:]
ob = bpy.data.objects['Doc_Mesh']; me = ob.data
assert not ob.get('tlc_hem_reweight'), 'ya aplicado'
before = {v.index: {ob.vertex_groups[g.group].name: round(g.weight, 4) for g in v.groups} for v in me.vertices}
n = LW.reweight('Doc', 1.0, 0.8, 0.08)
ob['tlc_hem_reweight'] = 'ztop1.0 tmax0.8 xs0.08'
after = {v.index: {ob.vertex_groups[g.group].name: round(g.weight, 4) for g in v.groups} for v in me.vertices}
ch = {i: {'old': before[i], 'new': after[i]} for i in before if before[i] != after[i]}
print('FIX reweighted', n, 'changed verts', len(ch))
json.dump(ch, open(r'D:\TheLivingCanvas\ArtSource\_Exports\NPC_Validation\Docent\reports\fix_hem.json', 'w'))
if '--save' in a:
    bpy.ops.wm.save_mainfile(); print('SAVED')
