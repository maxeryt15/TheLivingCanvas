"""Render Workbench de una pose desde varias camaras (SOLO LECTURA salvo FIX_SCRIPT en memoria). Uso:
blender -b X.blend --python render_views.py -- Caf outdir Sit az:el:dist:cz,az:el:dist:cz,...   (az grados: 0=frente, 90=lado derecho del NPC en +x; el = elevacion; dist=escala ortografica; cz=altura del objetivo)
Env: CULL=1 (backface culling), FIX_SCRIPT/FIX_ARGS (aplica script antes), POSES separadas por coma en el 3er arg."""
import bpy, sys, os, math
sys.path.insert(0, r'D:\TheLivingCanvas\Tools\npc_pipeline')
import pose_lib as PL
from mathutils import Vector
a = sys.argv[sys.argv.index('--') + 1:]; pref, out, poses, views = a[0], a[1], a[2].split(','), a[3].split(',')
os.makedirs(out, exist_ok=True)
if os.environ.get('FIX_SCRIPT'):
    import runpy; _argv = sys.argv; sys.argv = ['x', '--'] + os.environ.get('FIX_ARGS', '').split(); runpy.run_path(os.environ['FIX_SCRIPT']); sys.argv = _argv
O = bpy.data.objects; ob = O[pref + '_Mesh']; arm = O[pref + '_Rig']; S = bpy.context.scene
for o in O:
    if o.type in ('MESH', 'ARMATURE') and o not in (ob, arm): o.hide_viewport = True; o.hide_render = True
arm.hide_render = True; arm.location = (0, 0, 0)
cal = PL.calibrate(arm)
name = {'Stu': 'Student', 'Grd': 'Guard', 'Gen': 'Gentleman', 'Cur': 'Curator', 'Gar': 'Gardener', 'Caf': 'Cafe', 'Tou': 'Tourist', 'Cou': 'Courier', 'Doc': 'Docent', 'Pnt': 'Painter'}.get(pref, pref)
walk = next((x for x in bpy.data.actions if x.name.startswith('U_') and f'_{name}_Walk' in x.name), None)
S.render.engine = 'BLENDER_WORKBENCH'; sh = S.display.shading; sh.light = 'STUDIO'; sh.color_type = 'MATERIAL'; sh.show_cavity = False; sh.show_backface_culling = bool(os.environ.get('CULL'))
S.render.resolution_x = 560; S.render.resolution_y = 560
w = S.world or bpy.data.worlds.new('w'); S.world = w; w.color = (0.15, 0.45, 0.3)
cam = bpy.data.objects.new('cam', bpy.data.cameras.new('cam')); S.collection.objects.link(cam); S.camera = cam; cam.data.type = 'ORTHO'
for m in list(ob.data.materials):
    if m and not m.name.endswith('Lining') and not m.name.endswith('Lining_Mat'): m.diffuse_color = (0.92, 0.66, 0.52, 1) if 'skin' in m.name.lower() else ((0.25, 0.4, 0.8, 1) if 'clothes' in m.name.lower() else (0.8, 0.5, 0.2, 1))
def setpose(p):
    if p.startswith('Walk@'):
        PL.reset(arm); ad = arm.animation_data or arm.animation_data_create(); ad.action = walk; ad.action_slot = walk.slots[0]; S.frame_set(int(p[5:]))
    elif p.startswith('U_'):
        PL.reset(arm); ad = arm.animation_data or arm.animation_data_create(); ad.action = bpy.data.actions[p]; ad.action_slot = ad.action.slots[0]; S.frame_set(1)
    elif p == 'Idle': PL.reset(arm)
    else: PL.reset(arm); PL.apply(arm, cal[p])
    bpy.context.view_layer.update()
for p in poses:
    setpose(p)
    for vi, v in enumerate(views):
        az, el, sc, cz = [float(x) for x in v.split(':')]
        d = Vector((math.sin(math.radians(az)) * math.cos(math.radians(el)), -math.cos(math.radians(az)) * math.cos(math.radians(el)), math.sin(math.radians(el))))
        tgt = Vector((0, 0, cz)); cam.location = tgt + d * 6; cam.data.ortho_scale = sc
        cam.rotation_euler = (tgt - cam.location).to_track_quat('-Z', 'Y').to_euler()
        S.render.filepath = os.path.join(out, f'{pref}_{p.replace("@", "")}_v{vi}.png'); bpy.ops.render.render(write_still=True)
print('RENDERDONE')
