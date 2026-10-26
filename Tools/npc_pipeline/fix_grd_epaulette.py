"""Guard: las 2 hombreras (Grd_BoardCloth) tienen 8+6 vertices del borde interior (lado cuello) del faldon en z 0.53-0.58 (al nivel del muslo) en vez de en el hombro:
el rayo de construccion cayo por la abertura del cuello. Resultado: una tira que cruza el torso y fragmentos en el muslo en cuanto se anima (pesos de muslo/pierna).
Correccion minima: esos vertices (BoardCloth con z<1.4 en reposo) se reubican conservando (x,y) con z = la del vertice valido mas cercano de la hombrera,
en Basis y todas las shape keys; pesos = los del vertice valido mas cercano de la misma hombrera.
Uso: blender -b NPCs_Shell_Face_GUARD_WORK.blend --python fix_grd_epaulette.py -- [--save]   Registra reports/fix_epaulette.json"""
import bpy, sys, json, collections
sys.path.insert(0, r'D:\TheLivingCanvas\Tools\npc_pipeline')
import pose_lib as PL
a = sys.argv[sys.argv.index('--') + 1:]
ob = bpy.data.objects['Grd_Mesh']; arm = bpy.data.objects['Grd_Rig']; me = ob.data
PL.reset(arm)
mats = [m.name if m else None for m in me.materials]
bi = mats.index('Grd_BoardCloth'); ci = mats.index('Grd_clothes_Paint')
rest = [v.co.copy() for v in me.vertices]
bad = sorted({i for p in me.polygons if p.material_index == bi for i in p.vertices if rest[i].z < 1.4})
good = sorted({i for p in me.polygons if p.material_index == bi for i in p.vertices if rest[i].z >= 1.4})
assert len(bad) == 14, len(bad)
import numpy as np
shape = me.shape_keys.key_blocks
rec = {}
G = np.array([[rest[j].x, rest[j].y, rest[j].z] for j in good])
for i in bad:
    c = rest[i]
    d = np.hypot(G[:, 0] - c.x, G[:, 1] - c.y)
    near = np.argsort(d)[:1]                                   # la superficie bajo el borde del cuello no existe (abertura): z del vertice valido mas cercano en XY
    new = c.copy(); new.z = float(G[near[0], 2])
    delta = new - c
    old_w = {ob.vertex_groups[x.group].name: round(x.weight, 3) for x in me.vertices[i].groups}
    for kb in shape: kb.data[i].co = kb.data[i].co + delta
    me.vertices[i].co = me.vertices[i].co + delta
    gj = good[int(near[0])]                                    # pesos del vertice valido mas cercano de la misma hombrera
    ws = {x.group: x.weight for x in me.vertices[gj].groups}
    for x in list(me.vertices[i].groups): ob.vertex_groups[x.group].remove([i])
    for gi, x in ws.items(): ob.vertex_groups[gi].add([i], x, 'REPLACE')
    rec[i] = {'from': [round(x, 4) for x in c], 'to': [round(x, 4) for x in new], 'old_w': old_w, 'weights_from_vert': gj, 'new_w': {ob.vertex_groups[gi].name: round(x, 3) for gi, x in ws.items()}}
me.update(); bpy.context.view_layer.update()
print('FIXED', len(bad), 'moved max mm', round(max((rest[i] - me.vertices[i].co).length for i in bad) * 1000))
json.dump(rec, open(r'D:\TheLivingCanvas\ArtSource\_Exports\NPC_Validation\Guard\reports\fix_epaulette.json', 'w'), indent=1)
if '--save' in a:
    bpy.ops.wm.save_mainfile(); print('SAVED')
