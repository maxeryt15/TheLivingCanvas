"""Render Workbench de un fotograma del barrido, con camara centrada en un hueso.
Uso: blender -b NPCs_Shell_Face.blend --python render_sweep_shot.py -- Prefijo Accion Frame Hueso SalidaPNG [distancia_m] [angulos,coma]
Angulo 0 = frente (desde -Y), 90 = lado, 180 = espalda.
"""
import bpy, sys, math
from mathutils import Vector, Quaternion
a = sys.argv[sys.argv.index('--') + 1:]
pref, act, frame, bone, out = a[0], a[1], int(a[2]), a[3], a[4]
dist = float(a[5]) if len(a) > 5 else 0.7
O = bpy.data.objects
arm = O[pref + '_Rig']
ad = arm.animation_data or arm.animation_data_create()
A = bpy.data.actions[act]
ad.action = A
try:
    ad.action_slot = A.slots[0]
except Exception:
    pass
sc = bpy.context.scene
sc.frame_set(frame)
for o in O:
    if o.type == 'MESH' and o.name != pref + '_Mesh':
        o.hide_render = True
    elif o.type == 'ARMATURE':
        o.hide_render = True
bpy.context.view_layer.update()
c = arm.matrix_world @ arm.pose.bones[bone].head
cam = bpy.data.objects.new('cam', bpy.data.cameras.new('cam'))
sc.collection.objects.link(cam)
sc.camera = cam
sc.render.engine = 'BLENDER_WORKBENCH'
sc.display.shading.light = 'STUDIO'
sc.display.shading.color_type = 'MATERIAL'
sc.render.resolution_x = sc.render.resolution_y = 640
for m in O[pref + '_Mesh'].data.materials:
    n = m.name.lower() if m else ''
    if m:
        m.diffuse_color = (0.95, 0.62, 0.5, 1) if n.endswith('skin_paint') else (0.15, 0.3, 0.85, 1) if any(k in n for k in ('clothes_paint', 'suit_', 'aproncloth', 'blouse', 'scarfcloth')) else (0.6, 0.6, 0.6, 1)
w = sc.world or bpy.data.worlds.new('w'); sc.world = w
ANGS = [float(x) for x in a[6].split(',')] if len(a) > 6 else [0, 90]
for i, ang in enumerate(ANGS):
    d = Vector((math.sin(math.radians(ang)), -math.cos(math.radians(ang)), 0.15)).normalized()
    cam.location = c + d * dist
    cam.rotation_euler = (c - cam.location).to_track_quat('-Z', 'Y').to_euler()
    sc.render.filepath = out.replace('.png', f'_v{i}.png')
    bpy.ops.render.render(write_still=True)
print('RENDERED', out)
