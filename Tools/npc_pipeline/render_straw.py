"""Primeros planos de la brizna de paja de Gardener (SOLO LECTURA salvo FIX_SCRIPT en memoria). Uso: blender -b X.blend --python render_straw.py -- outdir [--fix script]"""
import bpy, sys, os, math, runpy
sys.path.insert(0, r'D:\TheLivingCanvas\Tools\npc_pipeline')
import pose_lib as PL
from mathutils import Vector
a = sys.argv[sys.argv.index('--') + 1:]; out = a[0]; os.makedirs(out, exist_ok=True)
if '--fix' in a: sys.argv = ['x', '--']; runpy.run_path(a[a.index('--fix') + 1])
O = bpy.data.objects; ob = O['Gar_Mesh']; arm = O['Gar_Rig']; S = bpy.context.scene
for o in O:
    if o.type in ('MESH', 'ARMATURE') and o not in (ob, arm): o.hide_viewport = True; o.hide_render = True
arm.hide_render = True; arm.location = (0, 0, 0); PL.reset(arm)
S.render.engine = 'BLENDER_WORKBENCH'; sh = S.display.shading; sh.light = 'STUDIO'; sh.color_type = 'MATERIAL'; sh.show_cavity = False; sh.show_backface_culling = True
S.render.resolution_x = 560; S.render.resolution_y = 560
w = S.world or bpy.data.worlds.new('w'); S.world = w; w.color = (0.15, 0.45, 0.3)
for m in ob.data.materials:
    if m: m.diffuse_color = (0.85, 0.7, 0.6, 1) if 'skin' in m.name.lower() else ((0.25, 0.4, 0.8, 1) if 'clothes' in m.name.lower() else ((0.95, 0.8, 0.35, 1) if 'Straw' in m.name and 'Hat' not in m.name else (0.55, 0.38, 0.2, 1)))
cam = bpy.data.objects.new('cam', bpy.data.cameras.new('cam')); S.collection.objects.link(cam); S.camera = cam; cam.data.type = 'ORTHO'; cam.data.ortho_scale = 0.13
tgt = Vector((0.055, -0.195, 1.563))
for i, (az, el) in enumerate(((0, 5), (40, 25), (90, 0), (0, 80), (-35, 15))):
    d = Vector((math.sin(math.radians(az)) * math.cos(math.radians(el)), -math.cos(math.radians(az)) * math.cos(math.radians(el)), math.sin(math.radians(el))))
    cam.location = tgt + d * 3; cam.rotation_euler = (tgt - cam.location).to_track_quat('-Z', 'Y').to_euler()
    S.render.filepath = os.path.join(out, 'straw_v%d.png' % i); bpy.ops.render.render(write_still=True)
print('STRAWDONE')
