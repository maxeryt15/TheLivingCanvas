"""Cipreses en llama estilo 'La noche estrellada' (Van Gogh): sustituye SOLO la malla del objeto Veg_Cypresses en la escena abierta.

Uso (en Blender, p. ej. via MCP):  exec(open(r"D:/TheLivingCanvas/Tools/museum_models/museum_cypress_flame.py").read()); build()
Cada arbol = UNA piel continua: tronco corto, base ancha, cuerpo que sube en tres lenguas de llama que giran en espiral,
borde con muescas, eje en S y punta que se curva. Material copa: M_Cypress (textura T_Cypress). UV cilindricas (2 vueltas, v = z / 1.6).
"""
import math
import random

import bmesh
import bpy

CYPRESSES = [(13.5, 8.0, 9.5), (-10.5, 11.0, 7.5), (15.2, 5.6, 6.0), (-15.0, 9.0, 8.5), (-18.0, 4.0, 8.0),
             (12.5, -12.0, 7.0), (-7.0, 13.5, 6.5),
             (-9.5, -13.5, 7.0), (8.5, -15.0, 8.0), (-15.5, -12.0, 6.5), (16.5, -14.5, 7.5), (-12.0, -17.5, 6.0)]
N = 20          # lados por anillo
STEP = 0.18     # separacion entre anillos (m)


def sm(x):
    return 0.0 if x <= 0 else 1.0 if x >= 1 else x * x * (3 - 2 * x)


def flame(bm, uvl, tx, ty, hgt):
    rng = random.Random(int(tx * 100) * 7919 + int(ty * 100))
    top = hgt + 1.6
    R = int(top / STEP) + 1
    rmax = 0.75 + 0.05 * top
    ph = rng.uniform(0, math.tau)
    lean_a = rng.uniform(0, math.tau)
    lean = rng.uniform(0.1, 0.3)
    turns = rng.uniform(5.0, 7.0) * rng.choice([-1, 1])
    rings = []
    for i in range(R):
        z = top * i / (R - 1)
        u = z / top
        trunk = 0.2 - 0.05 * min(z / 0.9, 1.0)
        rise = sm((u - 0.05) / 0.25) ** 0.8
        fall = max(0.0, 1.0 - max(0.0, (u - 0.30) / 0.70)) ** 1.5
        env = rmax * rise * fall
        w = sm((z - 0.5) / 0.7)
        # eje en S + punta curvada
        sx = 0.10 * math.sin(u * math.pi * 1.5 + ph) * u + lean * u ** 3 * math.cos(lean_a)
        sy = 0.08 * math.cos(u * math.pi * 1.3 + ph) * u + lean * u ** 3 * math.sin(lean_a)
        phi = u * turns + ph
        ring = []
        for j in range(N):
            th = j * math.tau / N
            c = math.cos(3 * (th - phi))
            lob = 1.0 + 0.68 * math.copysign(abs(c) ** 0.7, c) * w + 0.10 * math.cos(7 * th - 2 * phi) * w
            flick = 1.0 + 0.16 * math.sin(z * 5.5 + 3 * th + ph) * w
            r = trunk * (1 - w) + env * w * lob * flick
            r = max(r, 0.015 if i < R - 1 else 0.0)
            ring.append(bm.verts.new((tx + sx + math.cos(th) * r, ty + sy + math.sin(th) * r, z)))
        rings.append(ring)
    apex = bm.verts.new((tx + lean * math.cos(lean_a), ty + lean * math.sin(lean_a), top + 0.25))
    faces = []
    for i in range(R - 1):
        zm = top * (i + 0.5) / (R - 1)
        mi = 0 if zm < 0.8 else 1
        for j in range(N):
            j1 = (j + 1) % N
            if i < R - 2:
                vs = (rings[i][j], rings[i][j1], rings[i + 1][j1], rings[i + 1][j])
                uvs = ((j / N * 2, zm * 0 + top * i / (R - 1) / 1.6), ((j + 1) / N * 2, top * i / (R - 1) / 1.6),
                       ((j + 1) / N * 2, top * (i + 1) / (R - 1) / 1.6), (j / N * 2, top * (i + 1) / (R - 1) / 1.6))
            else:
                vs = (rings[i][j], rings[i][j1], apex)
                uvs = ((j / N * 2, top * i / (R - 1) / 1.6), ((j + 1) / N * 2, top * i / (R - 1) / 1.6), ((j + 0.5) / N * 2, (top + 0.25) / 1.6))
            f = bm.faces.new(vs)
            f.material_index = mi
            f.smooth = True
            for lp, uv in zip(f.loops, uvs):
                lp[uvl].uv = uv
            faces.append(f)
    return faces


def ensure_material():
    if "M_Cypress" in bpy.data.materials:
        return bpy.data.materials["M_Cypress"]
    m = bpy.data.materials["M_Leaf_Dark"].copy()
    m.name = "M_Cypress"
    nt = m.node_tree
    N_, Lk = nt.nodes, nt.links
    for n in [n for n in N_ if n.name.startswith("PT_")]:
        N_.remove(n)
    bsdf = next(n for n in N_ if n.type == "BSDF_PRINCIPLED")
    uv = N_.new("ShaderNodeUVMap"); uv.name = "PT_uv"
    mp = N_.new("ShaderNodeMapping"); mp.name = "PT_map"
    Lk.new(uv.outputs["UV"], mp.inputs["Vector"])
    t = N_.new("ShaderNodeTexImage"); t.name = "PT_col"
    h = N_.new("ShaderNodeTexImage"); h.name = "PT_hgt"
    D = r"D:\TheLivingCanvas\ArtSource\Museum\Painted_Textures"
    t.image = bpy.data.images.load(D + r"\T_Cypress.png", check_existing=True)
    h.image = bpy.data.images.load(D + r"\H_Cypress.png", check_existing=True)
    h.image.colorspace_settings.name = "Non-Color"
    Lk.new(mp.outputs["Vector"], t.inputs["Vector"]); Lk.new(mp.outputs["Vector"], h.inputs["Vector"])
    bp = N_.new("ShaderNodeBump"); bp.name = "PT_bump"; bp.inputs["Strength"].default_value = 0.8; bp.inputs["Distance"].default_value = 0.02
    Lk.new(h.outputs["Color"], bp.inputs["Height"])
    for l in list(bsdf.inputs["Base Color"].links) + list(bsdf.inputs["Normal"].links):
        Lk.remove(l)
    Lk.new(t.outputs["Color"], bsdf.inputs["Base Color"]); Lk.new(bp.outputs["Normal"], bsdf.inputs["Normal"])
    return m


def build(positions=None):
    o = bpy.data.objects["Veg_Cypresses"]
    mat = ensure_material()
    bm = bmesh.new()
    uvl = bm.loops.layers.uv.new("Float2")
    for (tx, ty, h) in (positions or CYPRESSES):
        flame(bm, uvl, tx, ty, h)
    bmesh.ops.recalc_face_normals(bm, faces=list(bm.faces))
    o.data.clear_geometry()
    for uvn in list(o.data.uv_layers):
        o.data.uv_layers.remove(uvn)
    o.data.materials.clear()
    o.data.materials.append(bpy.data.materials["M_Bark"])
    o.data.materials.append(mat)
    bm.to_mesh(o.data)
    bm.free()
    o.data.update()
    print("cipreses:", len(o.data.vertices), "verts")
