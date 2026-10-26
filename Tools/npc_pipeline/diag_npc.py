"""Diagnostico SOLO LECTURA de un NPC (no guarda el .blend). Uso: blender -b X.blend --python diag_npc.py -- Stu [outdir]
Auditoria estructural + barrido de penetracion piel/ropa + clipping entre capas + estiramiento de aristas. Reusa penetration_sweep/layer_clip_scan/edge_stretch redirigiendo la salida a outdir."""
import bpy, sys, os, json, collections
sys.path.insert(0, r'D:\TheLivingCanvas\Tools\npc_pipeline')
a = sys.argv[sys.argv.index('--') + 1:]; pref = a[0]
out = a[1] if len(a) > 1 else r'D:\TheLivingCanvas\ArtSource\_Exports\NPC_Validation\%s\reports' % pref
os.makedirs(out, exist_ok=True)
import penetration_sweep as PS
PS.OUT = out
ob = bpy.data.objects[pref + '_Mesh']; arm = bpy.data.objects[pref + '_Rig']; me = ob.data
infl = collections.Counter(len([g for g in v.groups if g.weight > 1e-6]) for v in me.vertices)
wsum = [sum(g.weight for g in v.groups) for v in me.vertices]
rep = dict(verts=len(me.vertices), faces=len(me.polygons), ngons=sum(1 for p in me.polygons if len(p.vertices) > 4), mats=[m.name for m in me.materials],
           uv=[u.name for u in me.uv_layers], colors=[c.name for c in me.color_attributes], vgroups=len(ob.vertex_groups), influences=dict(infl),
           wsum_min=min(wsum), wsum_max=max(wsum), no_weight=sum(1 for w in wsum if w < 1e-6),
           bones=len(arm.data.bones), deform=sum(b.use_deform for b in arm.data.bones), eye=[b for b in ('eye_L', 'eye_R', 'eye_aim') if b in arm.data.bones],
           keys=[k.name for k in me.shape_keys.key_blocks] if me.shape_keys else [], drivers=len(me.shape_keys.animation_data.drivers) if me.shape_keys and me.shape_keys.animation_data else 0,
           constraints=sum(len(pb.constraints) for pb in arm.pose.bones), action=arm.animation_data.action.name if arm.animation_data and arm.animation_data.action else None,
           actions=sorted(x.name for x in bpy.data.actions if ('_' + PS.NAMES[pref] + '_') in x.name), modifiers=[m.type for m in ob.modifiers])
json.dump(rep, open(out + '/audit.json', 'w'), indent=1, default=str)
print('AUDIT', json.dumps(rep, default=str))
rows, rest_max, ncov = PS.run_npc(pref)
by = {}
for r in rows:
    if r[4] and r[5] > by.get((r[1], r[4]), (0,))[0]: by[(r[1], r[4])] = (r[5], r[2], r[3])
w = sorted(by.items(), key=lambda kv: -kv[1][0])
json.dump({'rest_max_mm': rest_max * 1000, 'covered': ncov, 'worst': [[k[0], k[1], v[0], v[1], v[2]] for k, v in w]}, open(out + '/penetration.json', 'w'), indent=1)
print('PEN rest_max_mm', round(rest_max * 1000, 2), 'covered', ncov)
for k, v in w[:20]: print('PEN', k, v)
import layer_clip_scan as LC
LC.PS.OUT = out
LC.run(pref)
print('DIAGDONE')
