"""Exporta un NPC desde la escena abierta (All10_Review*.blend) a Unity: FBX con el rig en el origen (misma config que export_all10.py).
Uso: exec(open(r"D:/TheLivingCanvas/Tools/npc_pipeline/export_live.py").read()); export_one('Cou','Courier')"""
import bpy, os
MODELS = r'D:\TheLivingCanvas\Assets\_TheLivingCanvas\Art\Models\NPC'


def export_one(p, folder):
    O = bpy.data.objects
    arm = O[p + '_Rig']
    loc = arm.location.copy()
    arm.location = (0, 0, 0)
    bpy.context.view_layer.update()
    game = [o for o in arm.children if o.type == 'MESH' and not o.name.endswith('_Base') and o.visible_get()]
    bpy.ops.object.select_all(action='DESELECT')
    arm.select_set(True)
    for o in game:
        o.select_set(True)
    bpy.context.view_layer.objects.active = arm
    path = os.path.join(MODELS, folder, folder + '.fbx')
    bpy.ops.export_scene.fbx(filepath=path, use_selection=True, object_types={'ARMATURE', 'MESH'}, use_mesh_modifiers=True,
        mesh_smooth_type='FACE', add_leaf_bones=False, bake_anim=False, axis_forward='-Z', axis_up='Y', apply_unit_scale=True,
        apply_scale_options='FBX_SCALE_UNITS', use_armature_deform_only=True, primary_bone_axis='Y', secondary_bone_axis='X',
        path_mode='COPY', embed_textures=False, colors_type='LINEAR')
    arm.location = loc
    return path
