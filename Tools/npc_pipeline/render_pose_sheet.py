"""Render de poses (Workbench) de un NPC, SOLO LECTURA (no guarda el .blend). Uso: blender -b X.blend --python render_pose_sheet.py -- Stu outdir pose1,pose2 [view=front|back|side] [zoom=waist|full]
Poses: nombres de pose_lib (Idle, Sit, Crouch, ...) o Walk@N."""
import bpy, sys, os, math
sys.path.insert(0, r'D:\TheLivingCanvas\Tools\npc_pipeline')
import pose_lib as PL
from mathutils import Vector
a = sys.argv[sys.argv.index('--') + 1:]
pref, out, poses = a[0], a[1], a[2].split(','); views = (a[3] if len(a) > 3 else 'front').split(','); zoom = a[4] if len(a) > 4 else 'full'
os.makedirs(out, exist_ok=True)
if os.environ.get('FIX_ARGS') is not None:   # aplica en memoria el script de correccion (sin --save) antes de renderizar
    import runpy; _argv = sys.argv; sys.argv = ['x', '--'] + os.environ['FIX_ARGS'].split(); runpy.run_path(os.environ['FIX_SCRIPT']); sys.argv = _argv
O = bpy.data.objects; ob = O[pref + '_Mesh']; arm = O[pref + '_Rig']; S = bpy.context.scene
for o in O:
    if o.type in ('MESH', 'ARMATURE') and o not in (ob, arm): o.hide_viewport = True; o.hide_render = True
arm.hide_viewport = False; arm.hide_render = True
arm.location = (0, 0, 0)
cal = PL.calibrate(arm)
name = {'Stu': 'Student', 'Grd': 'Guard', 'Gen': 'Gentleman', 'Cur': 'Curator', 'Gar': 'Gardener', 'Caf': 'Cafe', 'Tou': 'Tourist', 'Cou': 'Courier', 'Doc': 'Docent', 'Pnt': 'Painter'}.get(pref, pref)
walk = next((x for x in bpy.data.actions if x.name.startswith('U_') and f'_{name}_Walk' in x.name), None)
S.render.engine = 'BLENDER_WORKBENCH'; sh = S.display.shading; sh.light = 'STUDIO'; sh.color_type = 'MATERIAL'; sh.show_cavity = False; sh.show_backface_culling = bool(os.environ.get('CULL'))
S.render.resolution_x = 480; S.render.resolution_y = 640; S.render.film_transparent = False
w = S.world or bpy.data.worlds.new('w'); S.world = w; w.color = (0.55, 0.55, 0.6)
cam = bpy.data.objects.new('cam', bpy.data.cameras.new('cam')); S.collection.objects.link(cam); S.camera = cam; cam.data.type = 'ORTHO'
for m in list(ob.data.materials):
    if m: m.diffuse_color = (0.8, 0.8, 0.8, 1) if 'skin' in m.name.lower() else ((0.25, 0.4, 0.8, 1) if 'clothes' in m.name.lower() else (0.8, 0.5, 0.2, 1))
if os.environ.get('DBG_LAYERS'):   # solo en memoria: pinta la prenda inferior de otro color para ver penetraciones entre capas
    import layer_clip_scan as LC
    r = LC.setup(pref)
    if r:
        _, me, U, L, fu, fl = r
        dm = bpy.data.materials.new('dbg_bottom'); dm.diffuse_color = (0.9, 0.2, 0.2, 1); me.materials.append(dm); di = len(me.materials) - 1
        for pl in fl: pl.material_index = di
        for m in me.materials:
            if m and 'clothes' in m.name.lower(): m.diffuse_color = (0.2, 0.8, 0.3, 1)
def setpose(p):
    if p.startswith('Walk@'):
        PL.reset(arm); ad = arm.animation_data or arm.animation_data_create(); ad.action = walk
        try: ad.action_slot = walk.slots[0]
        except Exception: pass
        S.frame_set(int(p[5:]))
    elif p == 'Idle': PL.reset(arm)
    else: PL.reset(arm); PL.apply(arm, cal[p])
    bpy.context.view_layer.update()
for p in poses:
    setpose(p)
    ev = ob.evaluated_get(bpy.context.evaluated_depsgraph_get()); m = ev.to_mesh(); zs = [v.co.z for v in m.vertices]; ev.to_mesh_clear()
    cz = (min(zs) + max(zs)) / 2; h = max(zs) - min(zs)
    for v in views:
        if zoom == 'chest': cz2, sc = 1.25, 0.7
        elif zoom == 'crotch': cz2, sc = 0.72, 0.5
        elif zoom == 'hem': cz2, sc = 0.98, 0.4
        elif zoom == 'waist': cz2, sc = 0.98, 0.9
        elif zoom == 'skirt': cz2, sc = 0.75, 0.8
        elif zoom == 'feet': cz2, sc = 0.12, 0.55
        else: cz2, sc = cz, h * 1.1
        d = {'front': (0, -4, cz2), 'back': (0, 4, cz2), 'side': (4, 0, cz2)}[v]
        cam.location = d; cam.data.ortho_scale = sc
        look = Vector((0, 0, cz2)) - Vector(d); cam.rotation_euler = look.to_track_quat('-Z', 'Y').to_euler()
        S.render.filepath = os.path.join(out, f'{pref}_{p.replace("@", "")}_{v}_{zoom}.png'); bpy.ops.render.render(write_still=True)
print('RENDERDONE')
