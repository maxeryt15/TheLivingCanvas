"""Helpers de validacion visual del dobladillo de Gen en Blender vivo: V.variant('orig'|'v1'|'final'); V.pose(nombre); V.stretch()"""
import bpy, sys, json
sys.path.insert(0, r'D:\TheLivingCanvas\Tools\npc_pipeline')
import pose_lib as PL
R = r'D:\TheLivingCanvas\ArtSource\NPC\_Reports\gen_hem\w_%s.json'
ob = bpy.data.objects['Gen_Mesh']; arm = bpy.data.objects['Gen_Rig']; me = ob.data
W = {n: {int(k): v for k, v in json.load(open(R % n)).items()} for n in ('orig', 'v1', 'final')}
changed = [i for i in W['orig'] if W['orig'][i] != W['v1'][i] or W['orig'][i] != W['final'][i]]
cal = PL.calibrate(arm)
walk = next(a for a in bpy.data.actions if a.name.startswith('U_') and 'Gentleman_Walk' in a.name)
for o in bpy.data.objects:
    if o.type == 'ARMATURE': o.hide_set(True); o.hide_viewport = True
    elif o.type == 'MESH' and o.name != 'Gen_Mesh': o.hide_set(True)
def variant(n):
    for i in changed:
        for g in list(me.vertices[i].groups): ob.vertex_groups[g.group].remove([i])
        for b, v in W[n][i].items(): ob.vertex_groups[b].add([i], v, 'REPLACE')
    me.update(); bpy.context.view_layer.update()
def pose(name):
    if name.startswith('Walk@'):
        PL.reset(arm); ad = arm.animation_data or arm.animation_data_create(); ad.action = walk
        try: ad.action_slot = walk.slots[0]
        except Exception: pass
        bpy.context.scene.frame_set(int(name[5:]))
    elif name == 'Idle': PL.reset(arm)
    else: PL.apply(arm, cal[name])
    bpy.context.view_layer.update()
print('READY', walk.name, len(changed), [k for k in cal if k in ('Sit','Crouch','BendForward','Twist_A','Twist_B','LegKick_L','LegKick_R')])
