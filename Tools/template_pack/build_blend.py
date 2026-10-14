"""Genera los .blend de plantillas de The Living Canvas a partir de spec.py.

Uso:  blender -b --python Tools/template_pack/build_blend.py -- <carpeta_salida_blender> [--preview <carpeta_previews>]

Convenciones (las mismas que usa el export a Unity, ver export_fbx.py):
  - 1 unidad de Blender = 1 metro.  Cada asset es una coleccion "SM_<Nombre>" con un Empty "SM_<Nombre>" que es el origen/pivote.
  - Unity (x, y, z) -> Blender (-x, -z, y):  el FRENTE del objeto (+Z en Unity) mira a -Y en Blender (vista Front, numpad 1); +Z es ARRIBA.
  - Los materiales se llaman IGUAL que en Unity (M_Floor_Wood...) y leen la textura  //textures/T_<Familia>.png
"""
import math
import os
import sys

import bmesh
import bpy
from mathutils import Euler, Matrix, Vector

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import spec  # noqa: E402

argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
OUT = argv[0]
PREVIEW = argv[argv.index("--preview") + 1] if "--preview" in argv else None
TEX_DIR = os.path.join(OUT, "textures")


def srgb_to_linear(c):
    return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4


def hex_color(h):
    h = h.lstrip("#")
    return tuple(srgb_to_linear(int(h[i:i + 2], 16) / 255.0) for i in (0, 2, 4)) + (1.0,)


_mats = {}


def get_material(name):
    if name in _mats:
        return _mats[name]
    hexc, family = spec.MATERIALS[name]
    mat = bpy.data.materials.new(name)
    mat.diffuse_color = hex_color(hexc)
    mat.use_nodes = True
    nt = mat.node_tree
    bsdf = nt.nodes.get("Principled BSDF")
    bsdf.inputs["Base Color"].default_value = hex_color(hexc)
    bsdf.inputs["Roughness"].default_value = 0.85
    if family == "Glow":
        bsdf.inputs["Emission Color"].default_value = hex_color(hexc)
        bsdf.inputs["Emission Strength"].default_value = 1.0
    tex = os.path.join(TEX_DIR, f"T_{family}.png") if family else None
    if tex and os.path.exists(tex):
        img = bpy.data.images.load(tex, check_existing=True)
        img.filepath = "//textures/" + os.path.basename(tex)
        node = nt.nodes.new("ShaderNodeTexImage")
        node.image = img
        node.location = (-400, 300)
        nt.links.new(node.outputs["Color"], bsdf.inputs["Base Color"])
    _mats[name] = mat
    return mat


# ---------------------------------------------------------------- geometria (se construye en ejes de Unity)
def planar_uv(bm, tile=1.0):
    """UV en metros: cada cara se proyecta sobre el plano de su normal dominante (1 unidad UV = `tile` m)."""
    uv = bm.loops.layers.uv.verify()
    for f in bm.faces:
        n = f.normal
        ax = max(range(3), key=lambda i: abs(n[i]))
        for l in f.loops:
            p = l.vert.co
            if ax == 0:
                l[uv].uv = (p.z / tile, p.y / tile)
            elif ax == 1:
                l[uv].uv = (p.x / tile, p.z / tile)
            else:
                l[uv].uv = (p.x / tile, p.y / tile)


def axis_z_to_y(bm):
    for v in bm.verts:
        v.co = Vector((v.co.x, v.co.z, -v.co.y))


def build_bm(kind, size):
    bm = bmesh.new()
    sx, sy, sz = size
    if kind == "box":
        bmesh.ops.create_cube(bm, size=1.0)
        for v in bm.verts:
            v.co = Vector((v.co.x * sx, v.co.y * sy, v.co.z * sz))
        bm.normal_update()
        planar_uv(bm)
    elif kind == "cyl":
        bmesh.ops.create_cone(bm, cap_ends=True, cap_tris=False, segments=24, radius1=0.5, radius2=0.5, depth=1.0, calc_uvs=True)
        axis_z_to_y(bm)
        for v in bm.verts:
            v.co = Vector((v.co.x * sx, v.co.y * sy, v.co.z * sz))
    elif kind == "sph":
        bmesh.ops.create_uvsphere(bm, u_segments=24, v_segments=14, radius=0.5, calc_uvs=True)
        axis_z_to_y(bm)
        for v in bm.verts:
            v.co = Vector((v.co.x * sx, v.co.y * sy, v.co.z * sz))
    elif kind == "cap":
        d = min(sx, sz)
        bmesh.ops.create_uvsphere(bm, u_segments=24, v_segments=15, radius=0.5, calc_uvs=True)
        axis_z_to_y(bm)
        half_cyl = (sy - d) / 2.0
        for v in bm.verts:
            y = v.co.y * d
            v.co = Vector((v.co.x * d, y + (half_cyl if v.co.y > 1e-6 else -half_cyl if v.co.y < -1e-6 else 0.0), v.co.z * d))
    elif kind in ("quad", "quadh"):
        w, h = sx, sy
        if kind == "quad":
            pts = [(-w / 2, -h / 2, 0), (w / 2, -h / 2, 0), (w / 2, h / 2, 0), (-w / 2, h / 2, 0)]
        else:
            pts = [(-w / 2, 0, h / 2), (w / 2, 0, h / 2), (w / 2, 0, -h / 2), (-w / 2, 0, -h / 2)]
        vs = [bm.verts.new(p) for p in pts]
        f = bm.faces.new(vs)
        uv = bm.loops.layers.uv.verify()
        for l, (u, v) in zip(f.loops, ((0, 0), (1, 0), (1, 1), (0, 1))):
            l[uv].uv = (u, v)
    elif kind == "gable":
        w, h, ln = sx, sy, sz
        a = [bm.verts.new(p) for p in ((-w / 2, 0, -ln / 2), (w / 2, 0, -ln / 2), (0, h, -ln / 2),
                                         (-w / 2, 0, ln / 2), (w / 2, 0, ln / 2), (0, h, ln / 2))]
        for idx in ((0, 1, 2), (3, 5, 4), (0, 2, 5, 3), (1, 4, 5, 2), (0, 3, 4, 1)):
            bm.faces.new([a[i] for i in idx])
        bm.normal_update()
        planar_uv(bm)
    bm.normal_update()
    return bm


def make_part(asset_empty, coll, part):
    name, kind, mat, size, pos, rot = part
    bm = build_bm(kind, size)
    rmat = Euler([math.radians(a) for a in rot], "ZXY").to_matrix().to_4x4()
    bmesh.ops.transform(bm, matrix=Matrix.Translation(Vector(pos)) @ rmat, verts=bm.verts)
    for v in bm.verts:  # Unity (x, y, z) -> Blender (-x, -z, y): el frente (+Z en Unity) queda en -Y (vista Front)
        v.co = Vector((-v.co.x, -v.co.z, v.co.y))
    bmesh.ops.reverse_faces(bm, faces=bm.faces[:])  # el cambio de ejes es un espejo: se invierten las caras
    mesh = bpy.data.meshes.new(f"{asset_empty.name}.{name}")
    bm.to_mesh(mesh)
    bm.free()
    mesh.shade_smooth() if kind in ("cyl", "sph", "cap") else None
    obj = bpy.data.objects.new(name, mesh)
    obj.data.materials.append(get_material(mat))
    obj.parent = asset_empty
    coll.objects.link(obj)
    return obj


def part_extent_x(parts):
    lo, hi = 1e9, -1e9
    for p in parts:
        sx = p[3][0]
        if p[1] in ("cyl", "sph", "cap"):
            sx = max(p[3][0], p[3][2]) if p[1] != "cap" else p[3][0]
        r = max(sx, p[3][1], p[3][2]) * 0.5 if p[5] != (0, 0, 0) else sx * 0.5
        lo, hi = min(lo, p[4][0] - r), max(hi, p[4][0] + r)
    return lo, hi


def add_label(text, loc, parent_coll):
    curve = bpy.data.curves.new("lbl", "FONT")
    curve.body = text
    curve.size = 0.35
    curve.align_x = "CENTER"
    obj = bpy.data.objects.new("LABEL_" + text, curve)
    obj.location = loc
    obj.rotation_euler = (math.radians(90), 0, 0)
    parent_coll.objects.link(obj)


def build_file(name, assets):
    bpy.ops.wm.read_factory_settings(use_empty=True)
    _mats.clear()
    scene = bpy.context.scene
    scene.unit_settings.system = "METRIC"
    scene.unit_settings.scale_length = 1.0
    ref = bpy.data.collections.new("_REFERENCE")
    labels = bpy.data.collections.new("_LABELS")
    scene.collection.children.link(ref)
    scene.collection.children.link(labels)

    # Referencia de escala: persona de 1,8 m (el Player) y cubo de 1 m. No se exportan (empiezan por "_").
    bm = build_bm("cap", (0.7, 1.8, 0.7))
    for v in bm.verts:
        v.co = Vector((v.co.x, v.co.z, v.co.y + 0.9))
    me = bpy.data.meshes.new("_ref_human")
    bm.to_mesh(me)
    bm.free()
    human = bpy.data.objects.new("_REF_Human_1.8m", me)
    human.display_type = "WIRE"
    human.location = (-1.5, 0, 0)
    ref.objects.link(human)
    cube = bpy.data.objects.new("_REF_Cube_1m", bpy.data.meshes.new("_ref_cube"))
    bm = bmesh.new()
    bmesh.ops.create_cube(bm, size=1.0)
    bm.to_mesh(cube.data)
    bm.free()
    cube.display_type = "WIRE"
    cube.location = (-3.0, 0, 0.5)
    ref.objects.link(cube)

    cursor_x, cursor_y, row_h = 0.0, 0.0, 0.0
    all_objs = []
    for asset in assets:
        aname, cat, where, parts, notes = asset
        lo, hi = part_extent_x(parts)
        width = hi - lo
        depth = max((abs(p[4][2]) + max(p[3]) * 0.5) for p in parts) * 2.0
        if cursor_x > 30.0:
            cursor_x, cursor_y, row_h = 0.0, cursor_y + row_h + 3.0, 0.0
        loc = (cursor_x + hi, cursor_y, 0.0)  # en Blender x = -x_unity
        coll = bpy.data.collections.new("SM_" + aname)
        scene.collection.children.link(coll)
        empty = bpy.data.objects.new("SM_" + aname, None)
        empty.empty_display_type = "ARROWS"
        empty.empty_display_size = 0.4
        empty.location = loc
        empty["unity_where"] = where
        empty["notes"] = notes
        coll.objects.link(empty)
        for p in parts:
            all_objs.append(make_part(empty, coll, p))
        add_label(aname, (loc[0], loc[1] - 1.0 - depth * 0.0, 0.0), labels)
        cursor_x += width + 1.5
        row_h = max(row_h, depth)
    return all_objs


def render_preview(path, objs):
    scene = bpy.context.scene
    scene.render.engine = "BLENDER_WORKBENCH"
    scene.display.shading.color_type = "MATERIAL"
    scene.display.shading.light = "STUDIO"
    scene.render.resolution_x, scene.render.resolution_y = 1800, 900
    world = bpy.data.worlds.new("w")
    world.color = (0.92, 0.92, 0.9)
    scene.world = world
    for o in bpy.data.objects:
        if o.name.startswith("_REF"):
            o.hide_render = True
    bpy.context.view_layer.update()
    pts = [o.matrix_world @ Vector(c) for o in objs for c in o.bound_box]
    lo = Vector((min(p.x for p in pts), min(p.y for p in pts), min(p.z for p in pts)))
    hi = Vector((max(p.x for p in pts), max(p.y for p in pts), max(p.z for p in pts)))
    center = (lo + hi) / 2
    span = max((hi.x - lo.x) * 0.95 + (hi.y - lo.y) * 0.25, ((hi.y - lo.y) * 0.8 + (hi.z - lo.z) * 0.7) * 2.0)
    cam = bpy.data.objects.new("cam", bpy.data.cameras.new("cam"))
    cam.data.type = "ORTHO"
    cam.data.ortho_scale = span * 1.1 + 1.0
    cam.data.clip_end = 1000
    cam.location = center + Vector((-12.0, -60.0, 50.0))
    cam.rotation_euler = (center - cam.location).to_track_quat("-Z", "Y").to_euler()
    bpy.context.scene.collection.objects.link(cam)
    scene.camera = cam
    scene.render.filepath = path
    bpy.ops.render.render(write_still=True)
    bpy.data.objects.remove(cam)


for fname, assets in spec.BLEND_FILES.items():
    objs = build_file(fname, assets)
    os.makedirs(OUT, exist_ok=True)
    if PREVIEW:
        os.makedirs(PREVIEW, exist_ok=True)
        render_preview(os.path.join(PREVIEW, fname + ".png"), objs)
    bpy.ops.wm.save_as_mainfile(filepath=os.path.join(OUT, fname + ".blend"), compress=True)
    print("OK", fname, len(assets), "assets")
