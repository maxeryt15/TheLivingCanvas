"""Copia la pose guardada (modo de rotacion, rotaciones, location, scale de cada hueso) del rig <Pref>_Rig de OTRO .blend al .blend abierto y guarda.
Uso: blender -b WORK.blend --python restore_pose_from.py -- Stu <ruta al .blend origen>   (solo toca la pose; nada de geometria ni pesos)"""
import bpy, sys
pref, other = sys.argv[sys.argv.index('--') + 1:][:2]
with bpy.data.libraries.load(other) as (df, dt): dt.objects = [pref + '_Rig']
src = dt.objects[0]; dst = bpy.data.objects[pref + '_Rig']
for pb in dst.pose.bones:
    s = src.pose.bones[pb.name]
    pb.rotation_mode = s.rotation_mode
    pb.rotation_quaternion = s.rotation_quaternion; pb.rotation_euler = s.rotation_euler; pb.rotation_axis_angle = s.rotation_axis_angle
    pb.location = s.location; pb.scale = s.scale
bpy.context.view_layer.update()
bpy.data.objects.remove(src)
bpy.ops.wm.save_mainfile(); print('POSE_RESTORED')
