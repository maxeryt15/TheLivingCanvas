"""Exporta cada coleccion SM_<Nombre> de un .blend a un FBX listo para Unity (origen en 0, escala 1).

Uso:  blender -b <archivo.blend> --python export_fbx.py -- <archivo.blend> <carpeta_fbx>
Ejes: -Z adelante / Y arriba, con las transformaciones aplicadas (bake_space_transform). Ver README del pack.
"""
import os
import sys

import bpy

argv = sys.argv[sys.argv.index("--") + 1:]
blend, out = argv[0], argv[1]
bpy.ops.wm.open_mainfile(filepath=blend)
os.makedirs(out, exist_ok=True)

for coll in list(bpy.data.collections):
    if not coll.name.startswith("SM_"):
        continue
    empty = bpy.data.objects.get(coll.name)
    saved = empty.location.copy()
    empty.location = (0, 0, 0)
    bpy.context.view_layer.update()
    bpy.ops.object.select_all(action="DESELECT")
    for o in coll.all_objects:
        o.select_set(True)
    bpy.ops.export_scene.fbx(
        filepath=os.path.join(out, coll.name + ".fbx"),
        use_selection=True,
        object_types={"EMPTY", "MESH"},
        apply_scale_options="FBX_SCALE_ALL",
        axis_forward="-Z",
        axis_up="Y",
        bake_space_transform=True,
        mesh_smooth_type="FACE",
        add_leaf_bones=False,
        path_mode="AUTO",
    )
    empty.location = saved
    print("FBX", coll.name)
