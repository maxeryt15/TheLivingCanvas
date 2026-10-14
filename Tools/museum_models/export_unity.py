"""Exporta el museo a FBX para Unity (sin MCP): blender -b <archivo.blend> --python export_unity.py -- <prefijo> <carpeta_salida>

- Un FBX por coleccion de primer nivel (p. ej. Museum_Int_Structure.fbx), solo mallas + empties.
- Las luces de Blender NO se exportan como luces: se crean empties "Light_*" en su sitio y un JSON con
  tipo/energia/color/angulo para que el builder de Unity cree luces URP. Los focos llevan un empty hijo
  "<nombre>_Target" 1 m por delante (el builder hace LookAt).
- Ejes: -Z adelante, Y arriba, escala aplicada (igual que museum_lib.export).
"""
import bpy, sys, os, json
from mathutils import Vector

argv = sys.argv[sys.argv.index("--") + 1:]
prefix, out_dir = argv[0], argv[1]
only = argv[2] if len(argv) > 2 else None
os.makedirs(out_dir, exist_ok=True)
sc = bpy.context.scene

# coleccion de presentacion: camaras fuera
for ob in list(bpy.data.objects):
    if ob.type == 'CAMERA':
        bpy.data.objects.remove(ob, do_unlink=True)

# luces -> empties + JSON
lights = []
lc = bpy.data.collections.get("Unity_Markers") or bpy.data.collections.new("Unity_Markers")
if lc.name not in sc.collection.children:
    sc.collection.children.link(lc)
for ob in list(bpy.data.objects):
    if ob.type != 'LIGHT':
        continue
    ld = ob.data
    nm = ob.name.replace(".", "_")
    info = {"name": nm, "type": ld.type, "energy": ld.energy, "color": list(ld.color),
            "radius": getattr(ld, "shadow_soft_size", 0.25)}
    if ld.type == 'SPOT':
        info["spot_size_deg"] = ld.spot_size * 57.29578
        info["spot_blend"] = ld.spot_blend
    if ld.type == 'AREA':
        info["size"] = [ld.size, getattr(ld, "size_y", ld.size)]
    mw = ob.matrix_world.copy()
    bpy.data.objects.remove(ob, do_unlink=True)   # primero se borra la luz: si no, el empty saldria como "<nombre>.001"
    e = bpy.data.objects.new(nm, None)
    e.matrix_world = mw
    lc.objects.link(e)
    if ld.type in ('SPOT', 'AREA', 'SUN'):
        t = bpy.data.objects.new(nm + "_Target", None)
        t.location = mw @ Vector((0, 0, -1))
        lc.objects.link(t)
    lights.append(info)
if prefix.endswith("Int"):
    ps = bpy.data.objects.new("PlayerStart", None)   # puerta principal, mirando al interior (+Y en Blender)
    ps.location = (0.0, -4.9, 0.5)
    lc.objects.link(ps)
with open(os.path.join(out_dir, prefix + "_Lights.json"), "w", encoding="utf-8", newline="\n") as f:
    json.dump({"lights": lights}, f, indent=1)

# un FBX por coleccion de primer nivel
done = []
for col in list(sc.collection.children):
    obs = [o for o in col.all_objects if o.type in ('MESH', 'EMPTY') and o.visible_get()]   # lo oculto en el .blend no se exporta
    if not obs or col.name.startswith("Presentation"):
        continue
    if only and only not in col.name:   # tercer argumento opcional: exportar solo una coleccion (p. ej. "Markers")
        continue
    bpy.ops.object.select_all(action='DESELECT')
    for o in obs:
        o.select_set(True)
    name = prefix + "_" + col.name.replace("Interior_", "").replace("Exterior_", "")
    path = os.path.join(out_dir, name + ".fbx")
    bpy.ops.export_scene.fbx(
        filepath=path, use_selection=True, object_types={'MESH', 'EMPTY'},
        global_scale=1.0, apply_unit_scale=True, apply_scale_options='FBX_SCALE_ALL', bake_space_transform=True,
        axis_forward='-Z', axis_up='Y', mesh_smooth_type='FACE', use_mesh_modifiers=True,
        add_leaf_bones=False, path_mode='AUTO', use_custom_props=False)
    tris = sum(sum(len(p.vertices) - 2 for p in o.data.polygons) for o in obs if o.type == 'MESH')
    done.append((name, len(obs), tris))
for d in done:
    print("EXPORT", *d)
print("LIGHTS", len(lights))
