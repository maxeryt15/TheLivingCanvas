"""Aplica las texturas pintadas (Van Gogh) a los materiales del INTERIOR en la escena abierta de Blender.

Uso (en Blender, via MCP) tras construir con museum_int_polish.py:
    exec(open(r"D:/TheLivingCanvas/Tools/museum_models/apply_painted_materials_interior.py", encoding="utf-8").read()); apply()
Texturas: ArtSource/Museum/Painted_Textures/T_<Familia>.png + H_<Familia>.png (las genera make_painted_textures.py).
Nodos por material: PT_uv -> PT_map (escala) -> PT_col / PT_hgt; PT_mix (tinte); PT_bump.
Tinte 0 = textura pintada pura; 1 = color del material modulado por la luminosidad de las pinceladas.
No toca: cuadros (M_Paint_*, M_Canvas_Slot, M_Paper), cristales, bombillas, letras de carteles, M_Floor_Dark, M_Grout, M_Track_White.
"""
import os

import bpy
import numpy as np

D = r"D:\TheLivingCanvas\ArtSource\Museum\Painted_Textures"
W = 'Wall_Soft'
# material -> (familia, escala UV, tinte, bump)
MAP = {
    'M_Interior_Wallpaper': (W, 1, 0.7, 0.12), 'M_Interior_Ceiling': (W, 1, 0.8, 0.1), 'M_Museum_Plaster': (W, 1, 0.7, 0.12), 'M_Wall_White': (W, 1, 0.8, 0.1),
    'M_Wall_Cerulean': (W, 1, 0.85, 0.12), 'M_Wall_Coral': (W, 1, 0.85, 0.12), 'M_Wall_Grey': (W, 1, 0.85, 0.12), 'M_Wall_Mint': (W, 1, 0.85, 0.12),
    'M_Wall_Ochre': (W, 1, 0.85, 0.12), 'M_Wall_Olive': (W, 1, 0.85, 0.12), 'M_Wall_Rose': (W, 1, 0.85, 0.12), 'M_Wall_Terracotta': (W, 1, 0.85, 0.12),
    'M_Interior_Wainscot': (W, 1, 0.9, 0.12), 'M_Interior_Concrete': (W, 1, 0.9, 0.1),
    'M_Interior_FloorWood': ('Wood_Grain', 1.0, 0.5, 0.15), 'M_Interior_FloorTile': ('Floor_Tile', 1, 0.3, 0.25),
    'M_Floor_StoneA': ('Path_Stone', 1, 0.45, 0.3), 'M_Floor_StoneB': ('Path_Stone', 1, 0.45, 0.3),
    'M_Museum_Wood': ('Wood_Grain', 1.0, 0.6, 0.12), 'M_Museum_WoodDark': ('Wood_Grain', 1.0, 0.88, 0.12),
    'M_Museum_Brass': ('Gilded', 1, 0.35, 0.25), 'M_Frame_Gold': ('Gilded', 1, 0.35, 0.25), 'M_Frame_Silver': ('Metal', 1, 0.7, 0.2),
    'M_Museum_Metal': ('Metal', 1, 0.7, 0.2), 'M_Steel': ('Metal', 1, 0.75, 0.2), 'M_Hatch_Metal': ('Metal', 1, 0.75, 0.2), 'M_Copper': ('Gilded', 1, 0.8, 0.2),
    'M_Museum_Stone': ('Path_Stone', 1.5, 0.3, 0.3), 'M_Ceramic': ('Ceramic', 1, 0.85, 0.1),
    'M_Fabric_Blue': ('Fabric', 1, 0.9, 0.15), 'M_Fabric_Mustard': ('Fabric', 1, 0.9, 0.15), 'M_Fabric_Olive': ('Fabric', 1, 0.9, 0.15),
    'M_Rug_Gold': ('Fabric', 1, 0.9, 0.15), 'M_Rug_Terracotta': ('Fabric', 1, 0.9, 0.15), 'M_RugSolid_Blue': ('Fabric', 0.7, 0.9, 0.15),
    'M_RugSolid_Cream': ('Fabric', 0.7, 0.9, 0.15), 'M_RugSolid_Gold': ('Fabric', 0.7, 0.9, 0.15), 'M_RugSolid_Navy': ('Fabric', 0.7, 0.9, 0.15),
    'M_RugSolid_Terracotta': ('Fabric', 0.7, 0.9, 0.15),
    'M_Mop_Cotton': ('Fabric', 1.5, 0.8, 0.1), 'M_Bristle': ('Wood_Grain', 1.5, 0.85, 0.1),
    'M_Plant_Leaf': ('Leaves', 1.5, 0.55, 0.3), 'M_Plant_LeafLight': ('Leaves', 1.5, 0.45, 0.3), 'M_Leaf_Dark': ('Leaves', 1.5, 0.8, 0.3), 'M_Ivy_Light': ('Leaves', 1.5, 0.5, 0.3),
    'M_Bark': ('Bark', 1.5, 0.4, 0.4), 'M_Pot': (W, 1.5, 0.7, 0.2), 'M_Soil': ('Path_Stone', 1.5, 0.9, 0.3), 'M_Path_Stone': ('Path_Stone', 1.5, 0.2, 0.3),
    'M_Path_StoneWarm': ('Path_Stone', 1.5, 0.45, 0.3),
    'M_Flower_Rose': (W, 2, 0.9, 0.1), 'M_Flower_White': (W, 2, 0.6, 0.1), 'M_Flower_Yellow': (W, 2, 0.9, 0.1), 'M_Sunflower_Disc': ('Bark', 2, 0.8, 0.2),
    'M_Sign_Board': ('Painted_Boards', 2, 0.95, 0.15), 'M_Museum_Shutter': ('Painted_Boards', 1.5, 0.4, 0.2), 'M_Museum_Door': ('Painted_Boards', 2, 0.9, 0.2),
    'M_Museum_AwningB': (W, 2, 0.55, 0.1), 'M_Ground_Earth': ('Path_Stone', 1.5, 0.9, 0.2),
    'M_Plastic_Black': (W, 2, 0.95, 0.08), 'M_Plastic_Blue': (W, 2, 0.92, 0.08), 'M_Plastic_Green': (W, 2, 0.92, 0.08), 'M_Plastic_Grey': (W, 2, 0.92, 0.08),
    'M_Plastic_Orange': (W, 2, 0.92, 0.08), 'M_Plastic_Red': (W, 2, 0.92, 0.08), 'M_Plastic_White': (W, 2, 0.85, 0.08), 'M_Plastic_Yellow': (W, 2, 0.92, 0.08),
    'M_Rubber': (W, 2, 0.97, 0.05),
}


def apply(mapping=None):
    mapping = mapping or MAP
    imgs, avg = {}, {}

    def img(fam, kind):
        k = (fam, kind)
        if k not in imgs:
            im = bpy.data.images.load(os.path.join(D, f"{kind}_{fam}.png"), check_existing=True)
            if im.has_data:
                im.reload()
            im.colorspace_settings.name = 'sRGB' if kind == 'T' else 'Non-Color'
            imgs[k] = im
        return imgs[k]

    def avglum(fam):
        if fam not in avg:
            a = np.array(img(fam, 'T').pixels[:]).reshape(-1, 4)[:, :3]
            avg[fam] = float((a @ np.array([.2126, .7152, .0722])).mean())
        return avg[fam]

    done, missing = [], []
    for mn, (fam, sc, tint, bump) in mapping.items():
        m = bpy.data.materials.get(mn)
        if not m:
            missing.append(mn)
            continue
        nt = m.node_tree
        N, Lk = nt.nodes, nt.links
        for n in [n for n in N if n.name.startswith('PT_')]:
            N.remove(n)
        bsdf = next(n for n in N if n.type == 'BSDF_PRINCIPLED')
        grp = next((n for n in N if n.type == 'GROUP'), None)
        base = tuple(grp.inputs['Base Color'].default_value) if grp else tuple(bsdf.inputs['Base Color'].default_value)
        uv = N.new('ShaderNodeUVMap'); uv.name = 'PT_uv'
        mp = N.new('ShaderNodeMapping'); mp.name = 'PT_map'; mp.inputs['Scale'].default_value = (sc, sc, sc); Lk.new(uv.outputs['UV'], mp.inputs['Vector'])
        t = N.new('ShaderNodeTexImage'); t.name = 'PT_col'; t.image = img(fam, 'T'); t.extension = 'REPEAT'
        h = N.new('ShaderNodeTexImage'); h.name = 'PT_hgt'; h.image = img(fam, 'H'); h.extension = 'REPEAT'
        Lk.new(mp.outputs['Vector'], t.inputs['Vector']); Lk.new(mp.outputs['Vector'], h.inputs['Vector'])
        bw = N.new('ShaderNodeRGBToBW'); bw.name = 'PT_bw'; Lk.new(t.outputs['Color'], bw.inputs['Color'])
        nm = N.new('ShaderNodeMath'); nm.name = 'PT_norm'; nm.operation = 'MULTIPLY'; nm.inputs[1].default_value = 1.0 / max(avglum(fam), 0.05)
        Lk.new(bw.outputs['Val'], nm.inputs[0])
        c = N.new('ShaderNodeCombineColor'); c.name = 'PT_g'
        for i in range(3):
            Lk.new(nm.outputs['Value'], c.inputs[i])
        mul = N.new('ShaderNodeMix'); mul.name = 'PT_mul'; mul.data_type = 'RGBA'; mul.blend_type = 'MULTIPLY'
        mul.inputs[0].default_value = 1.0; mul.inputs[6].default_value = base
        Lk.new(c.outputs['Color'], mul.inputs[7])
        fin = N.new('ShaderNodeMix'); fin.name = 'PT_mix'; fin.data_type = 'RGBA'; fin.blend_type = 'MIX'; fin.inputs[0].default_value = tint
        Lk.new(t.outputs['Color'], fin.inputs[6]); Lk.new(mul.outputs[2], fin.inputs[7])
        bp = N.new('ShaderNodeBump'); bp.name = 'PT_bump'; bp.inputs['Strength'].default_value = bump; bp.inputs['Distance'].default_value = 0.02
        Lk.new(h.outputs['Color'], bp.inputs['Height'])
        for l in list(bsdf.inputs['Base Color'].links) + list(bsdf.inputs['Normal'].links):
            Lk.remove(l)
        Lk.new(fin.outputs[2], bsdf.inputs['Base Color']); Lk.new(bp.outputs['Normal'], bsdf.inputs['Normal'])
        done.append(mn)
    print(len(done), "materiales pintados; faltan:", missing)
