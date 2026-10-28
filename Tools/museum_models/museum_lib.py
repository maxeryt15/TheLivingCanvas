"""Libreria comun para los modelos del museo (Blender 5.x, modo comando).

Criterios de ART_DIRECTION.md aplicados aqui:
  - Siluetas con irregularidad artesanal: ruido suave en coordenadas locales + biseles (ni low poly ni realista).
  - Materiales COMPARTIDOS (M_Museum_*) con colores de la paleta como PLACEHOLDER: el usuario pinta las texturas.
  - UVs por proyeccion de caja con densidad fija (1 tile = 1/uvscale metros) -> texturas pintadas tileables.
Unidades: 1 unidad = 1 metro. Eje Z arriba. Fachada principal mira a -Y.
"""
import bpy, bmesh, math, os
from mathutils import Vector, Matrix, Euler, noise

ROOT = r"D:\TheLivingCanvas"

# nombre: (hex, rugosidad, emision, alpha)
MATS = {
    # --- exterior / arquitectura ---
    "M_Museum_Plaster":    ("#E0CDB0", 0.95, 0, 1),   # crema envejecida
    "M_Museum_Stone":      ("#747983", 0.95, 0, 1),   # azul grisaceo
    "M_Museum_Roof":       ("#A85F47", 0.90, 0, 1),   # terracota
    "M_Museum_Wood":       ("#8A6347", 0.90, 0, 1),
    "M_Museum_WoodDark":   ("#5B4030", 0.90, 0, 1),
    "M_Museum_Shutter":    ("#65785A", 0.90, 0, 1),   # verde oliva
    "M_Museum_Door":       ("#526A83", 0.85, 0, 1),   # azul cerulo
    "M_Museum_Glass":      ("#456F88", 0.55, 0.25, 1),
    "M_Museum_Metal":      ("#4A4F5A", 0.55, 0, 1),
    "M_Museum_Brass":      ("#C49A3A", 0.45, 0, 1),
    "M_Museum_AwningA":    ("#A85F47", 0.95, 0, 1),
    "M_Museum_AwningB":    ("#E0CDB0", 0.95, 0, 1),
    "M_Plant_Leaf":        ("#65785A", 0.95, 0, 1),
    "M_Plant_LeafLight":   ("#86996A", 0.95, 0, 1),
    "M_Flower_Yellow":     ("#D4A72C", 0.90, 0, 1),
    "M_Flower_Rose":       ("#C97B6B", 0.90, 0, 1),
    "M_Lamp_Glow":         ("#FFD890", 0.50, 6.0, 1),
    "M_Soil":              ("#4E3A2C", 1.00, 0, 1),
    # --- interior ---
    "M_Interior_Wallpaper": ("#E8D8B8", 0.95, 0, 1),
    "M_Interior_Wainscot":  ("#65785A", 0.90, 0, 1),
    "M_Interior_FloorWood": ("#9A6E4A", 0.80, 0, 1),
    "M_Interior_FloorTile": ("#8FA3A8", 0.55, 0, 1),
    "M_Floor_WearTile":     ("#83969B", 0.50, 0, 1),   # huella de paso sobre el baldosin (algo mas oscura y apagada)
    "M_Floor_WearWood":     ("#A27350", 0.66, 0, 1),   # huella de paso sobre la tarima (algo mas clara y pulida)
    "M_Interior_Ceiling":   ("#EFE3CB", 0.95, 0, 1),
    "M_Interior_Concrete":  ("#7B7D82", 1.00, 0, 1),
    "M_Rug_Terracotta":     ("#A85F47", 1.00, 0, 1),
    "M_Fabric_Blue":        ("#526A83", 1.00, 0, 1),
    "M_Rug_Navy":           ("#3A4A62", 1.00, 0, 1),   # campo de la alfombra del hall (lana azul marino apagada)
    "M_Rug_Cream":          ("#D8C9A8", 1.00, 0, 1),   # motivos y flecos de alfombra
    "M_Rug_Gold":           ("#B3924C", 1.00, 0, 1),   # filetes dorados apagados de alfombra
    # alfombra del hall: colores lisos SIN pincelada (NO_STROKES), mismos tonos que M_Rug_* / M_Fabric_Blue
    "M_RugSolid_Navy":      ("#3A4A62", 1.00, 0, 1),
    "M_RugSolid_Cream":     ("#D8C9A8", 1.00, 0, 1),
    "M_RugSolid_Gold":      ("#B3924C", 1.00, 0, 1),
    "M_RugSolid_Terracotta": ("#A85F47", 1.00, 0, 1),
    "M_RugSolid_Blue":      ("#526A83", 1.00, 0, 1),
    "M_Fabric_Olive":       ("#65785A", 1.00, 0, 1),
    "M_Fabric_Mustard":     ("#D4A72C", 1.00, 0, 1),
    "M_Canvas_Slot":        ("#E8DCC0", 0.95, 0, 1),   # lienzo vacio: aqui van las pinturas del usuario
    "M_Frame_Gold":         ("#B58B3A", 0.45, 0, 1),
    "M_Ceramic":            ("#F0E8D8", 0.25, 0, 1),
    "M_Mirror":             ("#B8C8D0", 0.05, 0, 1),
    "M_Paper":              ("#EFE6CF", 0.95, 0, 1),
    "M_Ground_Grass":       ("#6E8157", 1.00, 0, 1),
    "M_Ground_Earth":       ("#6B5642", 1.00, 0, 1),
    "M_Path_Stone":         ("#9A9A98", 0.95, 0, 1),
    "M_Path_StoneWarm":     ("#B3A48C", 0.95, 0, 1),
    "M_Bark":               ("#5B4030", 1.00, 0, 1),
    "M_Leaf_Dark":          ("#4F6446", 0.95, 0, 1),
    "M_Hatch_Metal":        ("#5E6068", 0.60, 0, 1),
    "M_Floor_Dark":         ("#3E3A3A", 0.90, 0, 1),
    "M_Glass_Mirror":       ("#BFD0D4", 0.05, 0, 1),
    "M_Sign_Board":         ("#2F3F52", 0.85, 0, 1),
    "M_Sign_Letters":       ("#E8D9A8", 0.80, 0, 1),
    "M_Flower_Iris":        ("#4E58A8", 0.90, 0, 1),
    "M_Flower_White":       ("#EDE6D3", 0.90, 0, 1),
    "M_Ivy_Light":          ("#6F8A55", 0.90, 0, 1),
    "M_Flower_Lavender":    ("#7E6BA8", 0.90, 0, 1),
    "M_Leaf_Sage":          ("#8C9C7C", 0.95, 0, 1),
    "M_Flower_Geranium":    ("#B8483A", 0.90, 0, 1),
    "M_Sunflower_Disc":     ("#5A3B22", 1.00, 0, 1),
    "M_Picket":             ("#EAE3D2", 0.90, 0, 1),
    "M_Iron":               ("#2E3036", 0.55, 0, 1),
    # paredes de sala (identidad por sala, misma familia)
    "M_Wall_Ochre":         ("#D9BC7E", 0.95, 0, 1),
    "M_Wall_Cerulean":      ("#93A3B4", 0.95, 0, 1),
    "M_Wall_Terracotta":    ("#B98A72", 0.95, 0, 1),
    "M_Wall_Olive":         ("#A7AF8F", 0.95, 0, 1),
    "M_Wall_Grey":          ("#A9AAAE", 0.95, 0, 1),
    # ala nueva (galeria contemporanea): blanco calido + volumenes de color
    "M_Wall_White":         ("#E9E3D8", 0.95, 0, 1),
    "M_Wall_Mint":          ("#A9C8B6", 0.95, 0, 1),
    "M_Wall_Rose":          ("#D69C8E", 0.95, 0, 1),
    "M_Wall_Coral":         ("#C9775F", 0.95, 0, 1),
    "M_Floor_StoneA":       ("#CDBDA3", 0.80, 0, 1),
    "M_Floor_StoneB":       ("#C3B296", 0.80, 0, 1),
    "M_Track_White":        ("#E4E0D8", 0.50, 0, 1),
    "M_Frame_Silver":       ("#B9BDC2", 0.40, 0, 1),
    "M_Pot":                ("#B36B4C", 0.90, 0, 1),   # terracota de maceta
    "M_Grout":              ("#B9B2A6", 0.95, 0, 1),   # juntas de azulejo
    # lienzos de PRUEBA (provisionales; se borran por material M_Paint_* al poner las obras reales)
    "M_Paint_Sky":          ("#8FA9C4", 0.95, 0, 1),
    "M_Paint_Field":        ("#9DA86A", 0.95, 0, 1),
    "M_Paint_Ochre":        ("#D3A855", 0.95, 0, 1),
    "M_Paint_Rose":         ("#C98A7C", 0.95, 0, 1),
    "M_Paint_Deep":         ("#3E4A5E", 0.95, 0, 1),
    "M_Paint_Green":        ("#5F7A55", 0.95, 0, 1),
    "M_Paint_Cream":        ("#E8D9B5", 0.95, 0, 1),
    "M_Paint_GreySky":      ("#A2A3A6", 0.95, 0, 1),
    "M_Paint_GreyField":    ("#86887F", 0.95, 0, 1),
    "M_Vitrine_Glass":      ("#CFE0E6", 0.05, 0, 0.18),
    "M_Bulb_Warm":          ("#FFE2A8", 0.50, 8.0, 1),
    "M_Bulb_Cool":          ("#E8F0FF", 0.50, 6.0, 1),
    # servicio / limpieza (plasticos, fregona, cerdas)
    "M_Plastic_Yellow":     ("#E3B62E", 0.45, 0, 1),
    "M_Plastic_Blue":       ("#3F6C9E", 0.45, 0, 1),
    "M_Plastic_Green":      ("#5E8A5A", 0.45, 0, 1),
    "M_Plastic_Red":        ("#B8483A", 0.50, 0, 1),
    "M_Plastic_Grey":       ("#9BA1A8", 0.50, 0, 1),
    "M_Plastic_White":      ("#E9E6DD", 0.45, 0, 1),
    "M_Plastic_Orange":     ("#D9782F", 0.45, 0, 1),
    "M_Plastic_Black":      ("#282B31", 0.50, 0, 1),
    "M_Mop_Cotton":         ("#E6DFCB", 1.00, 0, 1),
    "M_Bristle":            ("#B8995A", 1.00, 0, 1),
    "M_Rubber":             ("#25262A", 0.80, 0, 1),
    "M_Steel":              ("#B7BCC4", 0.35, 0, 1),
    "M_Copper":             ("#B4714F", 0.38, 0, 1),   # tuberias vistas (radiadores)
    "M_Glass_Emerald":      ("#2F6B4E", 0.15, 0, 1),   # pantalla de la lampara de banquero
}

_mats = {}
NO_STROKES = {"M_Museum_Glass", "M_Mirror", "M_Glass_Mirror", "M_Lamp_Glow", "M_Sign_Letters",
              "M_RugSolid_Navy", "M_RugSolid_Cream", "M_RugSolid_Gold", "M_RugSolid_Terracotta", "M_RugSolid_Blue", "M_Mop_Cotton"}   # lisos: alfombra y fregona


def _lin(h):
    h = h.lstrip("#")
    return tuple((int(h[i:i + 2], 16) / 255.0) ** 2.2 for i in (0, 2, 4))


def get_mat(name):
    if name in _mats:
        return _mats[name]
    hexv, rough, emit, alpha = MATS[name]
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    b = m.node_tree.nodes["Principled BSDF"]
    b.inputs["Base Color"].default_value = (*_lin(hexv), 1)
    b.inputs["Roughness"].default_value = rough
    try:
        b.inputs["Specular IOR Level"].default_value = 0.15
    except Exception:
        pass
    if emit:
        b.inputs["Emission Color"].default_value = (*_lin(hexv), 1)
        b.inputs["Emission Strength"].default_value = emit
    if alpha < 1:
        b.inputs["Alpha"].default_value = alpha
        try:
            m.surface_render_method = 'BLENDED'
        except Exception:
            pass
    m.diffuse_color = (*_lin(hexv), alpha)
    if alpha >= 1 and not emit and name not in NO_STROKES:
        _stroke_preview(m, b)
    if name == "M_Museum_Glass":
        _glass_preview(m, b)
    _mats[name] = m
    return m


# Parametros de pincelada por familia.
#   escala = trazos por unidad UV (UV = 1/uvscale metros; muros 2 m, props 1 m, terreno 4 m)
STROKES = {   # (escala, alargamiento, remolino, relieve, variacion de tono, angulo base en grados)
    "default":            (7.0, 3.2, 0.5, 0.55, 0.16, 0),
    "M_Museum_Plaster":   (7.0, 3.6, 0.5, 0.60, 0.14, 75),
    "M_Museum_Stone":     (7.5, 2.4, 0.4, 0.75, 0.16, 10),
    "M_Museum_Roof":      (9.0, 3.2, 0.3, 0.70, 0.18, 90),
    "M_Museum_Wood":      (8.0, 5.5, 0.15, 0.55, 0.16, 0),
    "M_Museum_WoodDark":  (8.0, 5.5, 0.15, 0.55, 0.16, 0),
    "M_Museum_Shutter":   (8.0, 4.5, 0.15, 0.55, 0.18, 90),
    "M_Museum_Door":      (8.0, 4.5, 0.15, 0.55, 0.18, 90),
    "M_Museum_AwningA":   (8.0, 4.0, 0.1, 0.45, 0.10, 0),
    "M_Museum_AwningB":   (8.0, 4.0, 0.1, 0.45, 0.10, 0),
    "M_Sign_Board":       (8.0, 4.0, 0.1, 0.35, 0.08, 0),
    "M_Floor_Dark":       (8.0, 4.0, 0.1, 0.35, 0.08, 0),
    "M_Ground_Grass":     (26.0, 3.8, 1.5, 0.85, 0.22, 0),
    "M_Ground_Earth":     (14.0, 3.2, 1.2, 0.70, 0.20, 0),
    "M_Plant_Leaf":       (6.0, 4.0, 1.5, 0.90, 0.20, 90),
    "M_Plant_LeafLight":  (6.0, 4.0, 1.5, 0.90, 0.20, 90),
    "M_Leaf_Dark":        (6.0, 4.0, 1.5, 0.90, 0.20, 90),
    "M_Bark":             (9.0, 5.5, 0.3, 0.85, 0.18, 90),
    "M_Soil":             (10.0, 2.6, 1.2, 0.80, 0.18, 0),
    "M_Path_Stone":       (7.0, 2.4, 0.8, 0.75, 0.18, 0),
    "M_Path_StoneWarm":   (7.0, 2.4, 0.8, 0.75, 0.18, 0),
    "M_Floor_StoneA":     (7.0, 2.4, 0.6, 0.55, 0.12, 0),
    "M_Floor_StoneB":     (7.0, 2.4, 0.6, 0.55, 0.12, 0),
    "M_Flower_Yellow":    (10.0, 3.0, 1.2, 0.60, 0.14, 0),
    "M_Interior_FloorWood": (8.0, 6.0, 0.1, 0.45, 0.14, 0),
    "M_Floor_WearWood":   (8.0, 6.0, 0.1, 0.45, 0.14, 0),
}


def _vg_group():
    """Grupo de nodos compartido: pinceladas cortas y alargadas a lo Van Gogh.
    Trazos (celdas Voronoi estiradas) con orientacion POR TRAZO tomada de un campo de flujo (ruido lento en el centro de cada celda),
    empaste en relieve (cupula por trazo + surcos de cerdas), variacion calido/frio y de valor POR TRAZO,
    y capa inferior mas oscura entre trazos. SOLO PREVIEW EN BLENDER: para Unity hay que hornearlo a textura."""
    ng = bpy.data.node_groups.get("NG_VanGogh_Strokes")
    if ng:
        return ng
    ng = bpy.data.node_groups.new("NG_VanGogh_Strokes", "ShaderNodeTree")
    I = ng.interface
    I.new_socket("Base Color", in_out='INPUT', socket_type='NodeSocketColor')
    for nm, dv in (("Scale", 7.0), ("Elongation", 3.0), ("Swirl", 0.5), ("Bump", 0.6), ("Jitter", 0.18), ("Angle", 0.0)):
        sk = I.new_socket(nm, in_out='INPUT', socket_type='NodeSocketFloat')
        sk.default_value = dv
    I.new_socket("Color", in_out='OUTPUT', socket_type='NodeSocketColor')
    I.new_socket("Normal", in_out='OUTPUT', socket_type='NodeSocketVector')
    I.new_socket("Roughness", in_out='OUTPUT', socket_type='NodeSocketFloat')
    N, Lk = ng.nodes, ng.links
    gi, go = N.new("NodeGroupInput"), N.new("NodeGroupOutput")

    def math(op, a=None, b=None, va=0.0, vb=0.0):
        n = N.new("ShaderNodeMath"); n.operation = op
        n.inputs[0].default_value = va; n.inputs[1].default_value = vb
        if a is not None: Lk.new(a, n.inputs[0])
        if b is not None: Lk.new(b, n.inputs[1])
        return n.outputs[0]

    def mixc(fac, a, b, blend='MIX', fv=0.0):
        n = N.new("ShaderNodeMix"); n.data_type = 'RGBA'; n.blend_type = blend
        n.inputs[0].default_value = fv
        if fac is not None: Lk.new(fac, n.inputs[0])
        if isinstance(a, tuple): n.inputs[6].default_value = a
        else: Lk.new(a, n.inputs[6])
        if isinstance(b, tuple): n.inputs[7].default_value = b
        else: Lk.new(b, n.inputs[7])
        return n.outputs[2]

    tc = N.new("ShaderNodeTexCoord")
    base = gi.outputs["Base Color"]
    # espacio de trazos isotropo: una celda ~ una pincelada
    sv = N.new("ShaderNodeVectorMath"); sv.operation = 'SCALE'
    Lk.new(tc.outputs["UV"], sv.inputs[0]); Lk.new(gi.outputs["Scale"], sv.inputs["Scale"])

    def layer(offset):
        ov = N.new("ShaderNodeVectorMath"); ov.operation = 'ADD'
        ov.inputs[1].default_value = offset
        Lk.new(sv.outputs[0], ov.inputs[0])
        P = ov.outputs[0]
        vo = N.new("ShaderNodeTexVoronoi"); vo.feature = 'F1'
        vo.inputs["Scale"].default_value = 1.0; vo.inputs["Randomness"].default_value = 0.9
        Lk.new(P, vo.inputs["Vector"])
        sp = N.new("ShaderNodeSeparateColor"); Lk.new(vo.outputs["Color"], sp.inputs[0])
        # orientacion por trazo: angulo base del material + flujo lento + algo de mano
        nz = N.new("ShaderNodeTexNoise"); nz.inputs["Scale"].default_value = 0.09; nz.inputs["Detail"].default_value = 1.0
        Lk.new(vo.outputs["Position"], nz.inputs["Vector"])
        ang = math('MULTIPLY', math('MULTIPLY', math('SUBTRACT', nz.outputs["Fac"], vb=0.5), gi.outputs["Swirl"]), vb=3.0)
        ang = math('ADD', ang, math('MULTIPLY', math('SUBTRACT', sp.outputs[2], vb=0.5), vb=0.35))
        ang = math('ADD', ang, gi.outputs["Angle"])
        d = N.new("ShaderNodeVectorMath"); d.operation = 'SUBTRACT'
        Lk.new(P, d.inputs[0]); Lk.new(vo.outputs["Position"], d.inputs[1])
        vr = N.new("ShaderNodeVectorRotate"); vr.rotation_type = 'Z_AXIS'; vr.invert = True
        Lk.new(d.outputs[0], vr.inputs["Vector"]); Lk.new(ang, vr.inputs["Angle"])
        ld = vr.outputs[0]
        cx = N.new("ShaderNodeCombineXYZ")
        cx.inputs[0].default_value = 1.0; cx.inputs[2].default_value = 0.0
        Lk.new(gi.outputs["Elongation"], cx.inputs[1])
        el = N.new("ShaderNodeVectorMath"); el.operation = 'MULTIPLY'
        Lk.new(ld, el.inputs[0]); Lk.new(cx.outputs[0], el.inputs[1])
        ln = N.new("ShaderNodeVectorMath"); ln.operation = 'LENGTH'
        Lk.new(el.outputs[0], ln.inputs[0])
        mr = N.new("ShaderNodeMapRange"); mr.interpolation_type = 'SMOOTHSTEP'
        mr.inputs["From Min"].default_value = 0.55; mr.inputs["From Max"].default_value = 1.25
        mr.inputs["To Min"].default_value = 1.0; mr.inputs["To Max"].default_value = 0.0
        Lk.new(ln.outputs["Value"], mr.inputs["Value"])
        dome = mr.outputs["Result"]
        # cerdas: surcos finos a lo largo del trazo
        sx = N.new("ShaderNodeSeparateXYZ"); Lk.new(ld, sx.inputs[0])
        br = math('ADD', math('MULTIPLY', math('SINE', math('MULTIPLY', sx.outputs[1], vb=48.0)), vb=0.5), vb=0.5)
        h = math('ADD', math('MULTIPLY', dome, vb=0.8), math('MULTIPLY', math('MULTIPLY', br, dome), vb=0.15))
        # color del trazo: MISMO tono que el material; solo cambian luminosidad y saturacion
        hs = N.new("ShaderNodeHueSaturation")
        Lk.new(math('ADD', math('MULTIPLY', math('SUBTRACT', sp.outputs[2], vb=0.5), vb=0.015), vb=0.5), hs.inputs["Hue"])
        Lk.new(math('ADD', math('MULTIPLY', math('SUBTRACT', sp.outputs[0], vb=0.5), gi.outputs["Jitter"]), vb=1.0), hs.inputs["Saturation"])
        Lk.new(math('ADD', math('MULTIPLY', math('SUBTRACT', sp.outputs[1], vb=0.5), math('MULTIPLY', gi.outputs["Jitter"], vb=1.5)), vb=1.0), hs.inputs["Value"])
        Lk.new(base, hs.inputs["Color"])
        # la cresta de las cerdas recoge un poco mas de luz (del mismo color)
        c = N.new("ShaderNodeHueSaturation")
        c.inputs["Hue"].default_value = 0.5; c.inputs["Saturation"].default_value = 1.0
        Lk.new(math('ADD', math('MULTIPLY', br, vb=0.06), vb=0.97), c.inputs["Value"])
        Lk.new(hs.outputs["Color"], c.inputs["Color"])
        return dome, h, c.outputs["Color"]

    # capa inferior = color base: nunca quedan huecos entre trazos
    d1, h1, c1 = layer((0.0, 0.0, 0.0))
    d2, h2, c2 = layer((17.31, 9.13, 0.0))
    col = mixc(math('MINIMUM', math('MULTIPLY', d1, vb=2.5), vb=1.0), base, c1)
    col = mixc(math('MINIMUM', math('MULTIPLY', d2, vb=2.5), vb=1.0), col, c2)
    h = math('MAXIMUM', h1, h2)
    bp = N.new("ShaderNodeBump"); bp.inputs["Distance"].default_value = 0.03
    Lk.new(gi.outputs["Bump"], bp.inputs["Strength"]); Lk.new(h, bp.inputs["Height"])
    Lk.new(col, go.inputs["Color"])
    Lk.new(bp.outputs["Normal"], go.inputs["Normal"])
    Lk.new(math('SUBTRACT', None, math('MULTIPLY', h, vb=0.2), va=0.9), go.inputs["Roughness"])
    return ng


# Intensidad global: pinceladas del MISMO color del material (variacion de luminosidad/saturacion, no de tono)
STROKE_JITTER = 1.0
STROKE_BUMP = 0.3
STROKE_SWIRL = 0.4


def _stroke_preview(m, bsdf):
    """Engancha el grupo Van Gogh al material (solo preview en Blender)."""
    nt = m.node_tree
    g = nt.nodes.new("ShaderNodeGroup")
    g.node_tree = _vg_group()
    g.label = "VanGogh strokes (preview; hornear para Unity)"
    key = "M_Museum_Plaster" if (m.name.startswith("M_Wall_") or m.name == "M_Interior_Wallpaper") else m.name
    sc, el, sw, bu, ji, an = STROKES.get(key, STROKES["default"])
    g.inputs["Base Color"].default_value = tuple(bsdf.inputs["Base Color"].default_value)
    g.inputs["Scale"].default_value = sc
    g.inputs["Elongation"].default_value = el
    g.inputs["Swirl"].default_value = sw * STROKE_SWIRL
    g.inputs["Bump"].default_value = bu * STROKE_BUMP
    g.inputs["Jitter"].default_value = ji * STROKE_JITTER
    g.inputs["Angle"].default_value = math.radians(an)
    nt.links.new(g.outputs["Color"], bsdf.inputs["Base Color"])
    nt.links.new(g.outputs["Normal"], bsdf.inputs["Normal"])
    if bsdf.inputs["Roughness"].default_value >= 0.7:
        nt.links.new(g.outputs["Roughness"], bsdf.inputs["Roughness"])


def curtain_mat(key, c, zs):
    """Color de cortina determinista por ventana: el exterior y el interior coinciden."""
    opts = ["M_Paper", "M_Rug_Terracotta", "M_Paper", "M_Fabric_Mustard", "M_Flower_White"]
    # simetrico: depende de |c| (las ventanas gemelas a ambos lados del eje comparten color);
    # los dos laterales (W/E) usan la misma regla entre si
    side = {'W': 'E'}.get(key, key)
    return opts[(int(round(abs(c) * 3.7 + zs * 1.9)) + ord(side)) % len(opts)]


def _glass_preview(m, bsdf):
    """SOLO PREVIEW: reflejo del cielo en bandas diagonales pintadas sobre el cristal."""
    nt = m.node_tree
    N, Lk = nt.nodes, nt.links
    tc = N.new("ShaderNodeTexCoord")
    wv = N.new("ShaderNodeTexWave")
    wv.wave_type = 'BANDS'; wv.bands_direction = 'DIAGONAL'
    wv.inputs["Scale"].default_value = 1.6
    wv.inputs["Distortion"].default_value = 1.5
    wv.inputs["Detail"].default_value = 1.0
    Lk.new(tc.outputs["Object"], wv.inputs["Vector"])
    ramp = N.new("ShaderNodeValToRGB")
    ramp.color_ramp.elements[0].position = 0.8
    ramp.color_ramp.elements[0].color = (0, 0, 0, 1)
    ramp.color_ramp.elements[1].position = 0.9
    ramp.color_ramp.elements[1].color = (0.45, 0.45, 0.45, 1)
    Lk.new(wv.outputs["Fac"], ramp.inputs["Fac"])
    mix = N.new("ShaderNodeMix"); mix.data_type = 'RGBA'
    mix.inputs[6].default_value = tuple(bsdf.inputs["Base Color"].default_value)
    mix.inputs[7].default_value = (0.42, 0.58, 0.7, 1)
    Lk.new(ramp.outputs["Color"], mix.inputs[0])
    Lk.new(mix.outputs[2], bsdf.inputs["Base Color"])
    Lk.new(mix.outputs[2], bsdf.inputs["Emission Color"])


def clear_scene():
    """Vacia la escena SIN recargar ajustes de fabrica (no mata el addon MCP)."""
    for ob in list(bpy.data.objects):
        bpy.data.objects.remove(ob, do_unlink=True)
    for coll in (bpy.data.meshes, bpy.data.materials, bpy.data.curves, bpy.data.lights,
                 bpy.data.cameras, bpy.data.images):
        for d in list(coll):
            coll.remove(d)
    for g in list(bpy.data.node_groups):
        bpy.data.node_groups.remove(g)
    for c in list(bpy.data.collections):
        bpy.data.collections.remove(c)
    _mats.clear()


def col(name, parent=None):
    c = bpy.data.collections.get(name) or bpy.data.collections.new(name)
    p = parent or bpy.context.scene.collection
    if c.name not in p.children:
        p.children.link(c)
    return c


def reset():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    _mats.clear()


# Deformacion expresiva a lo Van Gogh (Iglesia de Auvers / Casa amarilla): muros que se inclinan y
# respiran, cumbrera que cede. Funcion determinista de la posicion -> exterior e interior encajan igual.
# WARP = 0 la desactiva. Amplitudes en metros.
WARP = 0.5


def warp(co):
    if not WARP:
        return co
    x, y, z = co
    h = max(0.0, z) / 8.0
    dx = (0.07 * math.sin(0.33 * z + 0.21 * y) + 0.05 * h * math.sin(0.4 * y + 1.3)) * WARP
    dy = (0.06 * math.sin(0.29 * z + 0.25 * x + 0.8) + 0.04 * h * math.sin(0.35 * x)) * WARP
    dz = -0.18 * math.cos(math.pi * max(-1.0, min(1.0, x / 10.0)) / 2) * max(0.0, min(1.0, (z - 8.2) / 4.5)) * WARP
    dz += 0.025 * math.sin(0.5 * x + 0.3 * y) * min(1.0, h) * WARP
    return Vector((x + dx, y + dy, z + dz))


class B:
    """Acumula geometria en UN mesh con varios material slots."""

    def __init__(s, name, uvscale=0.5, warp=True):
        s.warp = warp
        s.name = name
        s.bm = bmesh.new()
        s.mats = []
        s.uvscale = uvscale
        s._tmp = bpy.data.meshes.new("_tmp")

    # ---- nucleo -------------------------------------------------------
    def _mi(s, m):
        if m not in s.mats:
            s.mats.append(m)
        return s.mats.index(m)

    def _finish(s, bm, c, rot, mat, bev, amp, minsize, freq=0.45):
        if bev > 0:
            b = min(bev, minsize * 0.3)
            edges = [e for e in bm.edges if len(e.link_faces) == 2 and e.calc_face_angle(0) > 0.6]
            if edges:
                bmesh.ops.bevel(bm, geom=edges, offset=b, segments=2, affect='EDGES')
        M = Matrix.Translation(Vector(c)) @ Euler([math.radians(a) for a in rot]).to_matrix().to_4x4()
        bmesh.ops.transform(bm, matrix=M, verts=bm.verts)
        if amp > 0:
            for v in bm.verts:
                v.co += noise.noise_vector(v.co * freq) * amp
        bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
        mi = s._mi(mat)
        for f in bm.faces:
            f.material_index = mi
            f.smooth = not getattr(s, '_flat', False)
        bm.to_mesh(s._tmp)
        bm.free()
        s.bm.from_mesh(s._tmp)
        s._tmp.clear_geometry()

    # ---- primitivas ---------------------------------------------------
    def box(s, c, size, mat, rot=(0, 0, 0), bev=0.025, amp=0.018, cuts=None):
        bm = bmesh.new()
        bmesh.ops.create_cube(bm, size=1.0)
        for v in bm.verts:
            v.co.x *= size[0]; v.co.y *= size[1]; v.co.z *= size[2]
        n = cuts if cuts is not None else int(max(size) / 1.5)
        if n > 0:
            bmesh.ops.subdivide_edges(bm, edges=bm.edges[:], cuts=n, use_grid_fill=True)
        s._finish(bm, c, rot, mat, bev, amp, min(size))

    def cyl(s, c, r, h, mat, rot=(0, 0, 0), seg=16, r2=None, bev=0.0, amp=0.01):
        bm = bmesh.new()
        bmesh.ops.create_cone(bm, cap_ends=True, segments=seg, radius1=r, radius2=(r if r2 is None else r2), depth=h)
        s._finish(bm, c, rot, mat, bev, amp, min(r * 2, h))

    def blob(s, c, r, mat, squash=(1, 1, 1), sub=2, amp=None, rot=(0, 0, 0)):
        bm = bmesh.new()
        bmesh.ops.create_icosphere(bm, subdivisions=sub, radius=r)
        for v in bm.verts:
            v.co.x *= squash[0]; v.co.y *= squash[1]; v.co.z *= squash[2]
        s._finish(bm, c, rot, mat, 0, (r * 0.18 if amp is None else amp), r * 2, freq=1.3)

    def prism(s, pts, ext, mat, bev=0.0, amp=0.012, flat=False):
        """Poligono (puntos 3D coplanares) extruido en el vector ext."""
        bm = bmesh.new()
        vs = [bm.verts.new(Vector(p)) for p in pts]
        f = bm.faces.new(vs)
        r = bmesh.ops.extrude_face_region(bm, geom=[f])
        nv = [g for g in r["geom"] if isinstance(g, bmesh.types.BMVert)]
        bmesh.ops.translate(bm, vec=Vector(ext), verts=nv)
        s._flat = flat
        try:
            s._finish(bm, (0, 0, 0), (0, 0, 0), mat, bev, amp, 0.5)
        finally:
            s._flat = False

    def seg(s, p0, p1, r, mat, seg=5):
        """Cilindro fino entre dos puntos (tallos, cables)."""
        p0, p1 = Vector(p0), Vector(p1)
        d = p1 - p0
        if d.length < 1e-4:
            return
        bm = bmesh.new()
        bmesh.ops.create_cone(bm, cap_ends=False, segments=seg, radius1=r, radius2=r * 0.9, depth=d.length)
        q = Vector((0, 0, 1)).rotation_difference(d.normalized())
        M = Matrix.Translation((p0 + p1) / 2) @ q.to_matrix().to_4x4()
        bmesh.ops.transform(bm, matrix=M, verts=bm.verts)
        s._push(bm, mat)

    def leaf(s, c, n, t, size, mat, thick=0.006, res=20, shape=None):
        """Hoja plana lobulada (hiedra): 5 lobulos, punta en direccion t, cara mirando a n."""
        c, n, t = Vector(c), Vector(n).normalized(), Vector(t).normalized()
        bv = n.cross(t).normalized()
        pts = []
        for k in range(res):   # res=20: hiedra de 5 lobulos; res<10: hoja ovalada apuntada (barata)
            a = k * math.tau / res
            if shape == 'round':      # circulo festoneado (geranio, disco)
                r = size * (0.9 + 0.1 * math.cos(5 * a))
            elif shape == 'petal':    # petalo lanceolado: estrecho, punta marcada
                r = size * (0.14 + 0.86 * abs(math.cos(a)) ** 2.4) * (1.0 + 0.12 * math.cos(a))
            elif shape == 'lance':    # petalo de girasol: ancho, punta aguda (como las referencias)
                ca = abs(math.cos(a))
                r = size * (0.26 + 0.74 * ca ** 3.2) * (1.0 + 0.1 * math.cos(a))
            elif shape == 'heart':    # hoja acorazonada: punta aguda y escotadura en la base
                r = size * (0.62 + 0.38 * math.cos(a)) * (1.0 + 0.3 * max(0.0, math.cos(a)) ** 6)
                r *= 1.0 - 0.45 * max(0.0, -math.cos(a)) ** 10
            elif shape == 'disc':
                r = size
            elif res >= 10:
                r = size * (0.74 + 0.26 * math.cos(5 * a)) * (1.0 + 0.18 * math.cos(a))
            else:
                r = size * (0.55 + 0.45 * abs(math.cos(a)) ** 1.5) * (1.0 + 0.25 * math.cos(a))
            pts.append(c + t * (math.cos(a) * r) + bv * (math.sin(a) * r * 0.95))
        bm = bmesh.new()
        f = bm.faces.new([bm.verts.new(p) for p in pts])
        if thick > 0:   # thick=0: cara simple (barata, para florecitas de pradera)
            res = bmesh.ops.extrude_face_region(bm, geom=[f])
            nv = [g for g in res["geom"] if isinstance(g, bmesh.types.BMVert)]
            bmesh.ops.translate(bm, vec=-n * thick, verts=nv)
        s._push(bm, mat)

    def blade(s, p0, d, ln, w, mat, thick=0.004):
        """Hoja de hierba plana, ahusada y algo curvada (no bolas)."""
        p0, d = Vector(p0), Vector(d).normalized()
        side = d.cross(Vector((0, 0, 1)))
        if side.length < 1e-3:
            side = Vector((1, 0, 0))
        side.normalize()
        flat = Vector((d.x, d.y, 0))
        mid = p0 + d * ln * 0.5
        tip = p0 + (d + flat * 0.7).normalized() * ln
        pts = [p0 - side * w / 2, mid - side * w * 0.35, tip, mid + side * w * 0.35, p0 + side * w / 2]
        n = side.cross(d).normalized()
        bm = bmesh.new()
        f = bm.faces.new([bm.verts.new(q) for q in pts])
        res = bmesh.ops.extrude_face_region(bm, geom=[f])
        nv = [g for g in res["geom"] if isinstance(g, bmesh.types.BMVert)]
        bmesh.ops.translate(bm, vec=n * thick, verts=nv)
        s._push(bm, mat)

    def _push(s, bm, mat):
        bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
        mi = s._mi(mat)
        for f in bm.faces:
            f.material_index = mi
            f.smooth = False
        bm.to_mesh(s._tmp)
        bm.free()
        s.bm.from_mesh(s._tmp)
        s._tmp.clear_geometry()

    def text(s, body, c, size, mat, rot=(90, 0, 0), ext=0.03):
        cu = bpy.data.curves.new("t", 'FONT')
        cu.body = body; cu.size = size; cu.extrude = ext
        cu.align_x = 'CENTER'; cu.align_y = 'CENTER'
        ob = bpy.data.objects.new("t", cu)
        bpy.context.scene.collection.objects.link(ob)
        dg = bpy.context.evaluated_depsgraph_get()
        me = bpy.data.meshes.new_from_object(ob.evaluated_get(dg))
        bm = bmesh.new(); bm.from_mesh(me)
        bpy.data.objects.remove(ob); bpy.data.curves.remove(cu); bpy.data.meshes.remove(me)
        s._finish(bm, c, rot, mat, 0, 0, 1)

    # ---- cierre -------------------------------------------------------
    def _uv(s):
        uv = s.bm.loops.layers.uv.verify()
        k = s.uvscale
        for f in s.bm.faces:
            n = f.normal
            ax, ay, az = abs(n.x), abs(n.y), abs(n.z)
            for l in f.loops:
                p = l.vert.co
                if az >= ax and az >= ay:
                    l[uv].uv = (p.x * k, p.y * k)
                elif ay >= ax:
                    l[uv].uv = (p.x * k, p.z * k)
                else:
                    l[uv].uv = (p.y * k, p.z * k)

    def finish(s, collection=None):
        s._uv()   # UVs antes de deformar: la densidad de pincelada no se estira
        if s.warp:
            for v in s.bm.verts:
                v.co = warp(v.co)
        me = bpy.data.meshes.new(s.name)
        s.bm.to_mesh(me)
        s.bm.free()
        bpy.data.meshes.remove(s._tmp)
        for m in s.mats:
            me.materials.append(get_mat(m))
        ob = bpy.data.objects.new(s.name, me)
        (collection or bpy.context.scene.collection).objects.link(ob)
        return ob


def prop(name, pos, rot, fn, uvscale=1.0):
    """Objeto independiente con pivote en la base. fn(b) construye en coordenadas locales."""
    b = B(name, uvscale, warp=False)
    fn(b)
    ob = b.finish()
    ob.location = pos
    ob.rotation_euler.z = math.radians(rot)
    return ob


# ---- muros con huecos (compartido por exterior e interior) ----------------
def wall(b, axis, fixed, a0, a1, z0, z1, th, mat, openings=(), amp=0.02):
    """Muro recto. axis 'x': corre a lo largo de X en y=fixed. 'y': a lo largo de Y en x=fixed.
    openings: (centro, ancho, z_inferior, z_superior) absolutos."""
    OV = 0.03   # solape lateral entre tramos: cada tramo rodea un hueco y se mete OV bajo la columna vecina; asi no queda rendija donde las mallas
                # (con distinto reparto de cortes y ondulacion propia) no coinciden. La zona solapada es coplanar y con el mismo UV: no se ve.

    def solid_ranges(ua, ub, za, zb):
        """Subrangos z de za..zb en los que la columna entre ua y ub tiene muro (sin huecos)."""
        um_ = (ua + ub) / 2
        holes_ = sorted((max(zs, za), min(zt, zb)) for (c, w, zs, zt) in openings if c - w / 2 < um_ < c + w / 2 and zs < zb and zt > za)
        res, z_ = [], za
        for hs, ht in holes_:
            if hs - z_ > 0.01:
                res.append((z_, hs))
            z_ = max(z_, ht)
        if zb - z_ > 0.01:
            res.append((z_, zb))
        return res

    def box_uz(ua, ub, za, zb):
        # amp=0: la ondulacion por ruido hacia que dos tramos vecinos (distinta malla) no coincidieran en la junta; la deformacion expresiva
        # la sigue dando warp() (continua) y la textura pintada
        uc, zc = (ua + ub) / 2, (za + zb) / 2
        if axis == 'x':
            b.box((uc, fixed, zc), (ub - ua, th, zb - za), mat, bev=0, amp=0.0, cuts=max(1, int((ub - ua) / 1.2)))
        else:
            b.box((fixed, uc, zc), (th, ub - ua, zb - za), mat, bev=0, amp=0.0, cuts=max(1, int((ub - ua) / 1.2)))

    def piece(u0, u1, za, zb, nb_l=None, nb_r=None):
        if u1 - u0 < 0.01 or zb - za < 0.01:
            return
        box_uz(u0, u1, za, zb)
        # tiras de solape bajo las columnas vecinas, solo donde la vecina tiene muro (no invaden los huecos)
        if nb_l is not None:
            for (a, b_) in solid_ranges(nb_l[0], nb_l[1], za, zb):
                box_uz(u0 - min(OV, (nb_l[1] - nb_l[0]) * 0.5), u0 + 0.02, a, b_)
        if nb_r is not None:
            for (a, b_) in solid_ranges(nb_r[0], nb_r[1], za, zb):
                box_uz(u1 - 0.02, u1 + min(OV, (nb_r[1] - nb_r[0]) * 0.5), a, b_)

    # columnas entre todos los bordes de hueco: admite varios huecos apilados en la misma vertical
    us = sorted({a0, a1} | {min(max(c - w / 2, a0), a1) for (c, w, _, _) in openings}
                | {min(max(c + w / 2, a0), a1) for (c, w, _, _) in openings})
    cols = list(zip(us, us[1:]))
    for i, (u0, u1) in enumerate(cols):
        um = (u0 + u1) / 2
        holes = sorted((zs, zt) for (c, w, zs, zt) in openings if c - w / 2 < um < c + w / 2)
        nl = cols[i - 1] if i > 0 else None
        nr = cols[i + 1] if i + 1 < len(cols) else None
        z = z0
        for zs, zt in holes:
            piece(u0, u1, z, min(zs, z1), nl, nr)
            z = max(z, zt)
        piece(u0, u1, z, z1, nl, nr)


# ---- helpers de coordenadas locales de pared -------------------------------
class Face:
    """Contexto de una cara de muro: u a lo largo, v hacia fuera (s=+1/-1), z absoluta."""

    def __init__(s, b, axis, fixed, sign):
        s.b, s.axis, s.fixed, s.sign = b, axis, fixed, sign

    def P(s, u, v, z):
        return (u, s.fixed + s.sign * v, z) if s.axis == 'x' else (s.fixed + s.sign * v, u, z)

    def box(s, u, v, z, su, sv, sz, mat, **kw):
        size = (su, sv, sz) if s.axis == 'x' else (sv, su, sz)
        s.b.box(s.P(u, v, z), size, mat, **kw)

    def blob(s, u, v, z, r, mat, **kw):
        s.b.blob(s.P(u, v, z), r, mat, **kw)

    def blobw(s, u, v, z, r, mat, squash, sub=1):
        """blob con aplastamiento en ejes LOCALES de la pared (u a lo largo, v hacia fuera, z)."""
        su, sv, sz = squash
        s.b.blob(s.P(u, v, z), r, mat, squash=((su, sv, sz) if s.axis == 'x' else (sv, su, sz)), sub=sub, amp=r * 0.12)


def export(objs_collection_name, name, blend_dir, fbx_dir):
    os.makedirs(blend_dir, exist_ok=True)
    os.makedirs(fbx_dir, exist_ok=True)
    bpy.ops.wm.save_as_mainfile(filepath=os.path.join(blend_dir, name + ".blend"))
    bpy.ops.object.select_all(action='SELECT')
    bpy.ops.export_scene.fbx(
        filepath=os.path.join(fbx_dir, name + ".fbx"),
        use_selection=True, global_scale=1.0, apply_unit_scale=True,
        apply_scale_options='FBX_SCALE_ALL', bake_space_transform=True,
        axis_forward='-Z', axis_up='Y', mesh_smooth_type='FACE',
        add_leaf_bones=False, path_mode='AUTO')
