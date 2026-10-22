"""Exporta los 11 NPCs de ArtSource/NPC/NPCs_Shell_Test.blend a Unity (10 + Rose).
Uso: blender -b NPCs_Shell_Test.blend --python export_shell11.py
Por NPC: FBX (rig en el origen, pose de reposo, colores LINEAR), materials.json y texturas T_<prefijo>_*.png.
"""
import bpy, os, json, shutil
MODELS = r'D:\TheLivingCanvas\Assets\_TheLivingCanvas\Art\Models\NPC'
TEX = r'D:\TheLivingCanvas\Assets\_TheLivingCanvas\Art\Textures\NPC'
SRC = r'D:\TheLivingCanvas\ArtSource\NPC'
NPCS = [('Cur', 'Curator'), ('Grd', 'Guard'), ('Stu', 'Student'), ('Gar', 'Gardener'), ('Caf', 'Cafe'),
        ('Tou', 'Tourist'), ('Gen', 'Gentleman'), ('Cou', 'Courier'), ('Doc', 'Docent'), ('Pnt', 'Painter')]
O = bpy.data.objects

import bmesh
for _o in O:
    if _o.type == 'MESH' and _o.name.endswith('_Mesh'):   # Unity descarta los ngons autointersectados: se triangulan al exportar
        _bm = bmesh.new(); _bm.from_mesh(_o.data)
        _ng = [f for f in _bm.faces if len(f.verts) > 4]
        if _ng:
            bmesh.ops.triangulate(_bm, faces=_ng, quad_method='BEAUTY', ngon_method='BEAUTY')
            _bm.to_mesh(_o.data); _o.data.update()
        _bm.free()

def flat(objs):
    out = {}
    for o in objs:
        for m in o.data.materials:
            b = next((n for n in m.node_tree.nodes if n.type == 'BSDF_PRINCIPLED'), None)
            if b is None or any(n.type == 'TEX_IMAGE' for n in m.node_tree.nodes):
                continue
            c = b.inputs['Base Color'].default_value
            out[m.name] = dict(name=m.name, r=round(c[0], 4), g=round(c[1], 4), b=round(c[2], 4), metal=round(b.inputs['Metallic'].default_value, 2),
                               vc=any(n.type == 'VERTEX_COLOR' for n in m.node_tree.nodes))
    return list(out.values())

for p, folder in NPCS:
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
    d = os.path.join(MODELS, folder)
    os.makedirs(d, exist_ok=True)
    bpy.ops.export_scene.fbx(filepath=os.path.join(d, folder + '.fbx'), use_selection=True, object_types={'ARMATURE', 'MESH'}, use_mesh_modifiers=True,
        mesh_smooth_type='FACE', add_leaf_bones=False, bake_anim=False, axis_forward='-Z', axis_up='Y', apply_unit_scale=True,
        apply_scale_options='FBX_SCALE_UNITS', use_armature_deform_only=True, primary_bone_axis='Y', secondary_bone_axis='X',
        path_mode='COPY', embed_textures=False, colors_type='LINEAR')
    arm.location = loc
    data = dict(folder=folder, prefix=p, fbx=folder, flat=flat(game), paint=[p + '_skin_Paint', p + '_hair_Paint', p + '_clothes_Paint'])
    with open(os.path.join(d, 'materials.json'), 'w') as f:
        json.dump(data, f)
    td = os.path.join(TEX, folder)
    os.makedirs(td, exist_ok=True)
    for g in ('skin', 'hair', 'clothes'):
        # las texturas pintadas (Van Gogh v2) viven en Painted_Textures; el export NO debe pisar las de Unity con las originales de <Npc>/Textures
        shutil.copy(os.path.join(SRC, 'Painted_Textures', folder, 'T_%s_%s_VG2.png' % (p, g)), os.path.join(td, 'T_%s_%s.png' % (p, g)))
    print('EXPORT', folder, len(game), 'meshes', len(data['flat']), 'flat mats')


# Rose: mismo FBX que ya usa Unity (Models/NPC/Rose/Rose_Receptionist.fbx); materiales y texturas de Rose ya existen en Unity (se conservan los nombres)
arm = O['Rose_Rig']
loc = arm.location.copy()
arm.location = (0, 0, 0)
bpy.context.view_layer.update()
game = [o for o in arm.children if o.type == 'MESH' and o.visible_get()]
bpy.ops.object.select_all(action='DESELECT')
arm.select_set(True)
for o in game:
    o.select_set(True)
bpy.context.view_layer.objects.active = arm
d = os.path.join(MODELS, 'Rose')
bpy.ops.export_scene.fbx(filepath=os.path.join(d, 'Rose_Receptionist.fbx'), use_selection=True, object_types={'ARMATURE', 'MESH'}, use_mesh_modifiers=True,
    mesh_smooth_type='FACE', add_leaf_bones=False, bake_anim=False, axis_forward='-Z', axis_up='Y', apply_unit_scale=True,
    apply_scale_options='FBX_SCALE_UNITS', use_armature_deform_only=True, primary_bone_axis='Y', secondary_bone_axis='X',
    path_mode='COPY', embed_textures=False, colors_type='LINEAR')
arm.location = loc
print('EXPORT Rose', len(game), 'meshes')
