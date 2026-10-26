"""Render close-up de las shape keys faciales (solo lectura, no guarda). Uso: blender -b X.blend --python render_face_keys.py -- Stu outdir"""
import bpy, sys, os
sys.path.insert(0, r'D:\TheLivingCanvas\Tools\npc_pipeline')
from mathutils import Vector
a = sys.argv[sys.argv.index('--') + 1:]; pref, out = a[0], a[1]; os.makedirs(out, exist_ok=True)
O = bpy.data.objects; ob = O[pref + '_Mesh']; arm = O[pref + '_Rig']; S = bpy.context.scene
for o in O:
    if o.type in ('MESH', 'ARMATURE') and o not in (ob, arm): o.hide_viewport = True; o.hide_render = True
arm.hide_render = True; arm.location = (0, 0, 0)
import pose_lib as PL; PL.reset(arm)
hz = arm.pose.bones['head'].head.z + 0.05
S.render.engine = 'BLENDER_WORKBENCH'; S.display.shading.light = 'STUDIO'; S.display.shading.color_type = 'MATERIAL'
S.render.resolution_x = 360; S.render.resolution_y = 360
for m in ob.data.materials:
    if m: m.diffuse_color = (0.85, 0.7, 0.6, 1) if 'skin' in m.name.lower() else (0.5, 0.4, 0.3, 1)
cam = bpy.data.objects.new('cam', bpy.data.cameras.new('cam')); S.collection.objects.link(cam); S.camera = cam; cam.data.type = 'ORTHO'; cam.data.ortho_scale = 0.4
cam.location = (0, -3, hz); cam.rotation_euler = (Vector((0, 0, 0)) - Vector((0, 1, 0))).to_track_quat('-Z', 'Y').to_euler()
cam.rotation_euler = (1.5707963, 0, 0)
kb = ob.data.shape_keys.key_blocks
for name in ['neutral', 'blink', 'mouth_open', 'mouth_smile', 'mouth_frown', 'mouth_round', 'mouth_wide', 'brow_raise', 'brow_lower', 'brow_worry']:
    for k in kb: 
        if k.name != 'Basis': k.value = 0
    if name != 'neutral': kb[name].value = 1.0
    S.render.filepath = os.path.join(out, f'{pref}_face_{name}.png'); bpy.ops.render.render(write_still=True)
print('FACEDONE')
