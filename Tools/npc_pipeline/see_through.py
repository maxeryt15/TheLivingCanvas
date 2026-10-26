"""Detector de huecos por backface culling (SOLO LECTURA). Con los correctivos silenciados (como en Unity) renderiza el NPC caminando desde abajo/frente/3-4 con y sin culling;
los pixeles que son opacos SIN culling y transparentes CON culling son sitios donde Unity deja ver a traves (interior de ropa de una sola capa, sombreros huecos...).
Uso: blender -b X.blend --python see_through.py -- Pref outdir [--frames 1,8,16,24,32] [--fix script [args]]   Salida: lineas ST (por vista) y STTOTAL; PNG de la mascara de las peores vistas."""
import bpy, sys, os, math, runpy
sys.path.insert(0, r'D:\TheLivingCanvas\Tools\npc_pipeline')
import pose_lib as PL
import numpy as np
from mathutils import Vector
a = sys.argv[sys.argv.index('--') + 1:]; pref, out = a[0], a[1]; os.makedirs(out, exist_ok=True)
frames = [int(x) for x in a[a.index('--frames') + 1].split(',')] if '--frames' in a else [1, 8, 16, 24, 32]
if '--fix' in a:
    i = a.index('--fix'); sys.argv = ['x', '--'] + a[i + 2:]; runpy.run_path(a[i + 1])
O = bpy.data.objects; ob = O[pref + '_Mesh']; arm = O[pref + '_Rig']; S = bpy.context.scene
for o in O:
    if o.type in ('MESH', 'ARMATURE') and o not in (ob, arm): o.hide_viewport = True; o.hide_render = True
arm.hide_render = True; arm.location = (0, 0, 0)
if ob.data.shape_keys:
    for k in ob.data.shape_keys.key_blocks:
        if k.name.startswith('Corrective_'): k.mute = True
cal = PL.calibrate(arm)
name = {'Stu': 'Student', 'Grd': 'Guard', 'Gen': 'Gentleman', 'Cur': 'Curator', 'Gar': 'Gardener', 'Caf': 'Cafe', 'Tou': 'Tourist', 'Cou': 'Courier', 'Doc': 'Docent', 'Pnt': 'Painter', 'Rose': 'Rose'}.get(pref, pref)
walk = next((x for x in bpy.data.actions if x.name.startswith('U_') and f'_{name}_Walk' in x.name), None)
S.render.engine = 'BLENDER_WORKBENCH'; S.render.film_transparent = True; S.render.image_settings.color_mode = 'RGBA'
sh = S.display.shading; sh.light = 'FLAT'; sh.color_type = 'SINGLE'; sh.single_color = (1, 1, 1)
S.render.resolution_x = 360; S.render.resolution_y = 720
cam = bpy.data.objects.new('cam', bpy.data.cameras.new('cam')); S.collection.objects.link(cam); S.camera = cam; cam.data.type = 'ORTHO'; cam.data.ortho_scale = 2.2
views = [(0, -25), (35, -25), (-35, -25), (0, -10), (90, -20)]
def alpha(path):
    img = bpy.data.images.load(path); w, h = img.size; px = np.empty(w * h * 4, dtype=np.float32); img.pixels.foreach_get(px); bpy.data.images.remove(img)
    return px.reshape(h, w, 4)[:, :, 3] > 0.5
res = []; tot = 0
for fr in frames:
    PL.reset(arm)
    if walk:
        ad = arm.animation_data or arm.animation_data_create(); ad.action = walk; ad.action_slot = walk.slots[0]; S.frame_set(fr)
    bpy.context.view_layer.update()
    ev = ob.evaluated_get(bpy.context.evaluated_depsgraph_get()); m = ev.to_mesh(); zs = [v.co.z for v in m.vertices]; ev.to_mesh_clear()
    tgt = Vector((0, 0, (min(zs) + max(zs)) / 2))
    for vi, (az, el) in enumerate(views):
        d = Vector((math.sin(math.radians(az)) * math.cos(math.radians(el)), -math.cos(math.radians(az)) * math.cos(math.radians(el)), math.sin(math.radians(el))))
        cam.location = tgt + d * 6; cam.rotation_euler = (tgt - cam.location).to_track_quat('-Z', 'Y').to_euler()
        al = []
        for cull in (0, 1):
            sh.show_backface_culling = bool(cull); p = os.path.join(out, 'tmp_%d.png' % cull); S.render.filepath = p; bpy.ops.render.render(write_still=True); al.append(alpha(p))
        diff = al[0] & ~al[1]
        # ignorar el borde de la silueta: solo cuentan pixeles con al menos 3 vecinos opacos con culling en cada eje (rodeados)
        k = np.zeros_like(diff)
        op = al[1]; pad = np.pad(op, 2)
        nb = sum(pad[2 + dy:2 + dy + op.shape[0], 2 + dx:2 + dx + op.shape[1]] for dy, dx in ((-2, 0), (2, 0), (0, -2), (0, 2)))
        diff = diff & (nb >= 2)
        n = int(diff.sum()); tot += n; res.append((n, fr, az, el, diff))
        print('ST', pref, 'fr', fr, 'view', az, el, 'px', n)
res.sort(key=lambda r: -r[0])
for n, fr, az, el, diff in res[:3]:
    img = np.zeros(diff.shape + (4,), dtype=np.float32); img[..., 3] = 1; img[..., :3] = 0.15; img[diff] = (1, 0.2, 0.2, 1)
    im = bpy.data.images.new('m', diff.shape[1], diff.shape[0], alpha=True); im.pixels.foreach_set(img.ravel()); im.filepath_raw = os.path.join(out, '%s_mask_fr%d_az%d_el%d.png' % (pref, fr, az, el)); im.file_format = 'PNG'; im.save()
print('STTOTAL', pref, tot, 'worst', res[0][0], 'fr', res[0][1], 'view', res[0][2], res[0][3])
