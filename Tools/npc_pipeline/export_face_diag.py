"""Exporta los 11 NPCs de NPCs_Shell_Face.blend a una carpeta de DIAGNOSTICO (no toca Assets/).
Mismos ajustes que export_shell11.py (add_leaf_bones=False, -Z/Y, FBX_SCALE_UNITS, deform-only, FACE smoothing, sin animacion).
Uso: blender -b NPCs_Shell_Face.blend --python export_face_diag.py   (o exec desde el Blender vivo)
"""
import bpy, os
OUT = r'D:\TheLivingCanvas\ArtSource\_Exports\FaceDiag'
FOLDERS = {'Cur': 'Curator', 'Grd': 'Guard', 'Stu': 'Student', 'Gar': 'Gardener', 'Caf': 'Cafe', 'Tou': 'Tourist',
           'Gen': 'Gentleman', 'Cou': 'Courier', 'Doc': 'Docent', 'Pnt': 'Painter', 'Rose': 'Rose_Receptionist'}
O = bpy.data.objects
os.makedirs(OUT, exist_ok=True)
for p, name in FOLDERS.items():
    arm = O[p + '_Rig']
    loc = arm.location.copy()
    arm.location = (0, 0, 0)
    bpy.context.view_layer.update()
    game = [o for o in arm.children if o.type == 'MESH' and o.visible_get() and not o.name.endswith('_Base')]
    for o in bpy.context.view_layer.objects:
        o.select_set(False)
    arm.select_set(True)
    for o in game:
        o.select_set(True)
    bpy.context.view_layer.objects.active = arm
    bpy.ops.export_scene.fbx(filepath=os.path.join(OUT, name + '.fbx'), use_selection=True, object_types={'ARMATURE', 'MESH'}, use_mesh_modifiers=True,
        mesh_smooth_type='FACE', add_leaf_bones=False, bake_anim=False, axis_forward='-Z', axis_up='Y', apply_unit_scale=True,
        apply_scale_options='FBX_SCALE_UNITS', use_armature_deform_only=True, primary_bone_axis='Y', secondary_bone_axis='X',
        path_mode='COPY', embed_textures=False, colors_type='LINEAR')
    arm.location = loc
    print('EXPORTED', name, [o.name for o in game])
