"""Render Workbench de una pose calibrada (pose_lib) de un NPC, camara centrada en un hueso. Piel rosa, ropa azul.
Uso: blender -b X.blend --python render_pose_shot.py -- Pref Pose Hueso SalidaPNG distancia angulos,coma [fraccion]
Angulo 0 = espalda (NPC mira a +Y), 180 = frente, 90/270 = lados.
"""
import bpy, sys, math, json
sys.path.insert(0, r'D:\TheLivingCanvas\Tools\npc_pipeline')
import pose_lib as PL
from mathutils import Vector
a = sys.argv[sys.argv.index('--') + 1:]
pref, pose, bone, out, dist = a[0], a[1], a[2], a[3], float(a[4])
angs = [float(x) for x in a[5].split(',')]
frac = float(a[6]) if len(a) > 6 and a[6] != 'nokey' else 1.0
nokey = 'nokey' in a
O = bpy.data.objects
arm = O[pref + '_Rig']
cal = PL.calibrate(arm)
if pose == 'Idle': PL.reset(arm)
else: PL.apply(arm, cal[pose], frac)
sk = O[pref + '_Mesh'].data.shape_keys
for kb in sk.key_blocks:
    if kb.name.startswith('Corrective_'): kb.mute = nokey
bpy.context.view_layer.update()
sc = bpy.context.scene
for o in O:
    if o.type in ('MESH', 'ARMATURE') and o.name not in (pref + '_Mesh',): o.hide_render = True
for m in O[pref + '_Mesh'].data.materials:
    n = m.name.lower() if m else ''
    if m: m.diffuse_color = (0.95, 0.62, 0.5, 1) if n.endswith('skin_paint') else (0.15, 0.3, 0.85, 1) if any(k in n for k in ('clothes_paint', 'suit_', 'aproncloth', 'blouse', 'scarfcloth')) else (0.6, 0.6, 0.6, 1)
c = arm.matrix_world @ arm.pose.bones[bone].head
cam = bpy.data.objects.new('cam', bpy.data.cameras.new('cam')); sc.collection.objects.link(cam); sc.camera = cam
sc.render.engine = 'BLENDER_WORKBENCH'; sc.display.shading.light = 'STUDIO'; sc.display.shading.color_type = 'MATERIAL'
sc.render.resolution_x = sc.render.resolution_y = 640
sc.world = sc.world or bpy.data.worlds.new('w')
for i, ang in enumerate(angs):
    d = Vector((math.sin(math.radians(ang)), -math.cos(math.radians(ang)), 0.15)).normalized()
    cam.location = c + d * dist
    cam.rotation_euler = (c - cam.location).to_track_quat('-Z', 'Y').to_euler()
    sc.render.filepath = out.replace('.png', f'_v{i}.png')
    bpy.ops.render.render(write_still=True)
print('RENDERED', out)
