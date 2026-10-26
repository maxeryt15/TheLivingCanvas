"""Arbustos de 'La noche estrellada' (rizos de follaje del pueblo): modifica SOLO el objeto Veg_Bushes de la escena abierta.

Uso (en Blender, via MCP):  exec(open(r"D:/TheLivingCanvas/Tools/museum_models/museum_bush_swirl.py").read()); build()
Cada cupula (caras con M_Leaf_Dark / M_Plant_Leaf) se subdivide y se desplaza hacia fuera con crestas en espiral (rizos);
las rosas se mueven con la superficie. Material cupula: M_Bush (textura T_Bush_Swirl). Solo se puede ejecutar UNA vez
sobre la malla original (si ya esta aplicado, abre el .blend sin guardar o restaura desde Museum_Exterior_Polish.blend).
"""
import math
import random

import bmesh
import bpy
from mathutils import Vector

BUSH_SPOTS = [(-9.4, -7.6, 0.8), (9.4, -7.6, 0.8), (-9.6, 6.9, 0.9), (9.6, 6.9, 0.9),
              (-9.5, 0.0, 0.7), (9.5, -1.5, 0.7), (-6.8, 7.3, 0.6), (5.4, 7.2, 0.62), (-3.3, 7.25, 0.5), (3.3, 7.25, 0.5),
              (-8.85, -4.8, 0.42), (-8.85, 3.0, 0.42), (8.85, -4.6, 0.42), (8.85, 1.9, 0.42), (-8.85, -1.6, 0.38),
              (-14.5, -18.0, 0.8), (14.0, -18.5, 0.8), (-18.0, -2.0, 1.0), (18.0, -4.0, 0.9)]
TILE = 3.0   # metros por repeticion de la textura


def sm(x):
    return 0.0 if x <= 0 else 1.0 if x >= 1 else x * x * (3 - 2 * x)


def crest(a):
    return (0.5 + 0.5 * math.cos(a)) ** 1.1


def ensure_material():
    if "M_Bush" in bpy.data.materials:
        return bpy.data.materials["M_Bush"]
    m = bpy.data.materials["M_Leaf_Dark"].copy()
    m.name = "M_Bush"
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
    t.image = bpy.data.images.load(D + r"\T_Bush_Swirl.png", check_existing=True)
    h.image = bpy.data.images.load(D + r"\H_Bush_Swirl.png", check_existing=True)
    h.image.colorspace_settings.name = "Non-Color"
    Lk.new(mp.outputs["Vector"], t.inputs["Vector"]); Lk.new(mp.outputs["Vector"], h.inputs["Vector"])
    bp = N_.new("ShaderNodeBump"); bp.name = "PT_bump"; bp.inputs["Strength"].default_value = 0.8; bp.inputs["Distance"].default_value = 0.02
    Lk.new(h.outputs["Color"], bp.inputs["Height"])
    for l in list(bsdf.inputs["Base Color"].links) + list(bsdf.inputs["Normal"].links):
        Lk.remove(l)
    Lk.new(t.outputs["Color"], bsdf.inputs["Base Color"]); Lk.new(bp.outputs["Normal"], bsdf.inputs["Normal"])
    return m


def which(x, y):
    best, bd = 0, 1e9
    for k, (bx, by, r) in enumerate(BUSH_SPOTS):
        d = math.hypot(x - bx, y - by) / (r + 0.3)
        if d < bd:
            best, bd = k, d
    return best


def build():
    o = bpy.data.objects["Veg_Bushes"]
    me = o.data
    mat = ensure_material()
    if mat.name not in [m.name for m in me.materials if m]:
        me.materials.append(mat)
    slot = [m.name if m else None for m in me.materials].index("M_Bush")
    leaf = {i for i, m in enumerate(me.materials) if m and m.name in ("M_Leaf_Dark", "M_Plant_Leaf")}
    bm = bmesh.new()
    bm.from_mesh(me)
    dome = [f for f in bm.faces if f.material_index in leaf]
    dverts = {v for f in dome for v in f.verts}
    bmesh.ops.subdivide_edges(bm, edges=list({e for f in dome for e in f.edges}), cuts=2, use_grid_fill=True)
    dome = [f for f in bm.faces if f.material_index in leaf]       # incluye las caras nuevas
    dverts = list({v for f in dome for v in f.verts})
    rest = [f for f in bm.faces if f.material_index not in leaf]
    pre = {v.index: v.co.copy() for v in dverts}
    bush_of = {v.index: which(v.co.x, v.co.y) for v in dverts}
    phases = [random.Random(k * 977 + 5).uniform(0, math.tau) for k in range(len(BUSH_SPOTS))]
    for _ in range(5):   # redondea la cupula original (era facetada) antes de ondularla
        bmesh.ops.smooth_vert(bm, verts=dverts, factor=0.6, use_axis_x=True, use_axis_y=True, use_axis_z=True)
    smoothed = {v.index: v.co.copy() for v in dverts}
    delta = {}
    for v in dverts:
        k = bush_of[v.index]
        bx, by, r = BUSH_SPOTS[k]
        ph = phases[k]
        rel = Vector((v.co.x - bx, v.co.y - by, 0))
        th = math.atan2(rel.y, rel.x)
        t = min(max(v.co.z / (1.65 * r), 0.0), 1.0)
        w = sm(t / 0.14) * (1.0 - 0.5 * sm((t - 0.85) / 0.15))
        f = w * (0.17 * crest(5 * th - 6.0 * t + ph) + 0.07 * crest(9 * th + 8.0 * t + 2 * ph) + 0.03)
        new = Vector((bx + rel.x * (1 + f), by + rel.y * (1 + f), v.co.z + 0.10 * r * f))
        delta[v.index] = new - pre[v.index]
        v.co = new
    # rosas: acompanan a la superficie (desplazamiento del vertice de cupula mas cercano a cada isla)
    seen = set()
    for f0 in rest:
        if f0.index in seen:
            continue
        isl, stack = [], [f0]
        seen.add(f0.index)
        while stack:
            f = stack.pop()
            isl.append(f)
            for e in f.edges:
                for g in e.link_faces:
                    if g.index not in seen and g.material_index not in leaf:
                        seen.add(g.index)
                        stack.append(g)
        vs = list({v for f in isl for v in f.verts})
        cen = sum((v.co for v in vs), Vector()) / len(vs)
        k = which(cen.x, cen.y)
        cand = [v for v in dverts if bush_of[v.index] == k]
        nv = min(cand, key=lambda v: (pre[v.index] - cen).length_squared)
        bx, by, r = BUSH_SPOTS[k]
        out = Vector((cen.x - bx, cen.y - by, 0))
        out = out.normalized() * (0.015 * r) if out.length > 1e-6 else Vector()
        for v in vs:
            v.co += delta[nv.index] + out
    # material + UV cilindricas (envolvente entera por cupula)
    uvl = bm.loops.layers.uv.verify()
    for f in dome:
        f.material_index = slot
        f.smooth = True
        us = []
        for lp in f.loops:
            v = lp.vert
            k = bush_of[v.index]
            bx, by, r = BUSH_SPOTS[k]
            wraps = max(1, round(math.tau * r * 1.2 / TILE))
            th = math.atan2(v.co.y - by, v.co.x - bx)
            us.append(th / math.tau * wraps)
            lp[uvl].uv = (us[-1], v.co.z * wraps / (math.tau * r * 1.2))
        ref = us[0]
        wraps_f = max(1, round(math.tau * BUSH_SPOTS[bush_of[f.loops[0].vert.index]][2] * 1.2 / TILE))
        for lp, u in zip(f.loops, us):
            while u - ref > wraps_f / 2:
                u -= wraps_f
            while u - ref < -wraps_f / 2:
                u += wraps_f
            uv = lp[uvl].uv
            lp[uvl].uv = (u, uv[1])
    bmesh.ops.recalc_face_normals(bm, faces=list(bm.faces))
    bm.to_mesh(me)
    bm.free()
    me.update()
    print("arbustos:", len(me.vertices), "verts", len(me.polygons), "caras")
