"""Renderiza fotos de un NPC (caminar + 2 poses) desde frente/lado/espalda a ArtSource/NPC/_tmp_<prefijo>_<tag>_<vista>.png.
Uso: exec(open(r"D:/TheLivingCanvas/Tools/npc_pipeline/render_sheet.py").read()); render_npc('Caf', 'Cafe')"""
import bpy
from mathutils import Vector


def render_npc(prefix, npc, width=520, height=700, dist=3.4):
    sc = bpy.context.scene
    cam_d = bpy.data.cameras.new('tmpcam'); cam = bpy.data.objects.new('tmpcam', cam_d); sc.collection.objects.link(cam)
    old_cam = sc.camera; sc.camera = cam
    sc.render.resolution_x = width; sc.render.resolution_y = height; sc.render.engine = 'BLENDER_WORKBENCH'
    sc.display.shading.light = 'STUDIO'; sc.display.shading.color_type = 'TEXTURE'
    hid = []
    for o in bpy.data.objects:
        if o.type == 'MESH' and not o.name.startswith(prefix + '_') and not o.hide_render:
            hid.append(o); o.hide_render = True
        if o.type == 'ARMATURE': o.hide_render = True
    arm = bpy.data.objects[prefix + '_Rig']
    c = Vector((arm.location.x, arm.location.y, 0.95))
    base = r"D:/TheLivingCanvas/ArtSource/NPC/_tmp_%s_" % prefix
    walk = 'U_%s_Walk_%s' % (npc, 'Female' if prefix in ('Cur', 'Stu', 'Caf', 'Tou', 'Cou', 'Pnt', 'Rose') else 'Male')
    jobs = [('walk', walk, 6), ('hoh', 'U_Pose_%s_HandsOnHips' % npc, 1), ('behind', 'U_Pose_%s_HandsBehind' % npc, 1)]
    for tag, act, f in jobs:
        arm.animation_data.action = bpy.data.actions[act]; sc.frame_set(f); bpy.context.view_layer.update()
        for view, d in (('front', (0, 1, 0.05)), ('side', (1, 0, 0.05)), ('back', (0, -1, 0.05))):
            d = Vector(d).normalized()
            cam.location = c + d * dist; cam.rotation_euler = (-d).to_track_quat('-Z', 'Y').to_euler()
            sc.render.filepath = base + tag + '_' + view + '.png'
            bpy.ops.render.render(write_still=True)
    arm.animation_data.action = None
    for pb in arm.pose.bones: pb.location = (0, 0, 0); pb.rotation_quaternion = (1, 0, 0, 0)
    for o in hid: o.hide_render = False
    for o in bpy.data.objects:
        if o.type == 'ARMATURE': o.hide_render = False
    sc.camera = old_cam; bpy.data.objects.remove(cam)
