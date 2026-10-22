"""Export an NPC to Unity: FBX (LINEAR vertex colours, rest pose) + textures. Excludes the hidden full-res base."""
import bpy, os, shutil


def export_npc(prefix, rig_name, base_name, fbx_dir, tex_src_dir=None, tex_dst_dir=None, fbx_name=None):
    arm = bpy.data.objects[rig_name]
    if bpy.context.object and bpy.context.object.mode != 'OBJECT':
        bpy.ops.object.mode_set(mode='OBJECT')
    bpy.context.view_layer.objects.active = arm
    bpy.ops.object.mode_set(mode='POSE')
    for b in arm.pose.bones:
        b.rotation_mode = 'XYZ'
        b.rotation_euler = (0, 0, 0)
        b.location = (0, 0, 0)
    bpy.ops.object.mode_set(mode='OBJECT')
    game = [o for o in bpy.data.objects if o.parent == arm and o.type == 'MESH' and o.name != base_name]
    bpy.ops.object.select_all(action='DESELECT')
    arm.select_set(True)
    for o in game:
        o.select_set(True)
    bpy.context.view_layer.objects.active = arm
    os.makedirs(fbx_dir, exist_ok=True)
    path = os.path.join(fbx_dir, (fbx_name or prefix) + '.fbx')
    bpy.ops.export_scene.fbx(filepath=path, use_selection=True, object_types={'ARMATURE', 'MESH'}, use_mesh_modifiers=True,
        mesh_smooth_type='FACE', add_leaf_bones=False, bake_anim=False, axis_forward='-Z', axis_up='Y', apply_unit_scale=True,
        apply_scale_options='FBX_SCALE_UNITS', use_armature_deform_only=True, primary_bone_axis='Y', secondary_bone_axis='X',
        path_mode='COPY', embed_textures=False, colors_type='LINEAR')
    if tex_src_dir and tex_dst_dir:
        os.makedirs(tex_dst_dir, exist_ok=True)
        for f in os.listdir(tex_src_dir):
            if f.startswith('T_') and f.endswith('.png'):
                shutil.copy(os.path.join(tex_src_dir, f), tex_dst_dir)
    return path, [o.name for o in game]
