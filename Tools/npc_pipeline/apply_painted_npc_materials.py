"""Aplica las texturas Van Gogh a los NPC en la escena abierta de Blender (All10_Review.blend u otra con los mismos materiales).

Uso (en Blender, via MCP):
    exec(open(r"D:/TheLivingCanvas/Tools/npc_pipeline/apply_painted_npc_materials.py", encoding="utf-8").read()); apply()
1) <Pre>_skin_Paint / _clothes_Paint / _hair_Paint: cambia el atlas por T_<Pre>_<kind>_VG.png (mismos colores, mas pincelada) y anade relieve H_.
2) Materiales planos de accesorios: textura pintada en coordenadas de OBJETO (proyeccion cubica, no necesitan UV), mezclada con su color
   (tinte alto: el color manda, la textura solo da la pincelada). Ojos, cejas, labios, lunares, cristales, pantallas y detalles diminutos no se tocan.
"""
import os
import re

import bpy
import numpy as np

ROOT = r"D:\TheLivingCanvas\ArtSource"
NPC = ROOT + r"\NPC"
TEX = ROOT + r"\Museum\Painted_Textures"
FOLDERS = {"Caf": "Cafe", "Cou": "Courier", "Cur": "Curator", "Doc": "Docent", "Gar": "Gardener", "Gen": "Gentleman",
           "Grd": "Guard", "Pnt": "Painter", "Stu": "Student", "Tou": "Tourist"}
BUMP = {"skin": 0.06, "clothes": 0.08, "hair": 0.10}
SKIP = re.compile(r"Eye|Brows|Lip|Mole|Wart|Freckle|Scar|Face$|Hole|Lens|Glass|Glint|Screen|Thread|Pin[A-C]|Star|Pupil|Ink|Stone|Dots|Stripe|Button$|Key|Grille|Mustache|Nail|Pom|Knot$", re.I)
LEATHER = re.compile(r"Leather|Strap|Band$|Belt|Pouch|Flap|Glove|Tongue|Lace|Sole|Foot$|Patch(?!Gold)|Trim$", re.I)
CLOTH = re.compile(r"Cloth|Canvas|Silk|Wool|Shirt|Blouse|Pocket|Scarf|Cuff|Bow|Apron|Beret|Piping", re.I)
STRAW = re.compile(r"Straw|Stalk|BrushWood", re.I)


def _img(path, srgb):
    im = bpy.data.images.load(path, check_existing=True)
    if im.has_data and im.is_dirty is False:
        im.reload()
    im.colorspace_settings.name = 'sRGB' if srgb else 'Non-Color'
    return im


def _avg(im):
    a = np.array(im.pixels[:]).reshape(-1, 4)[:, :3]
    return float((a @ np.array([.2126, .7152, .0722])).mean())


def paint_atlases():
    n = 0
    for pre, fol in FOLDERS.items():
        for kind in ("skin", "clothes", "hair"):
            m = bpy.data.materials.get(f"{pre}_{kind}_Paint")
            if not m:
                continue
            tp = os.path.join(NPC, "Painted_Textures", fol, f"T_{pre}_{kind}_VG.png")
            hp = os.path.join(NPC, "Painted_Textures", fol, f"H_{pre}_{kind}.png")
            if not (os.path.exists(tp) and os.path.exists(hp)):
                continue
            nt = m.node_tree
            N, Lk = nt.nodes, nt.links
            for x in [x for x in N if x.name.startswith("PT_")]:
                N.remove(x)
            tex = next(x for x in N if x.type == 'TEX_IMAGE' and not x.name.startswith("PT_"))
            tex.image = _img(tp, True)
            bsdf = next(x for x in N if x.type == 'BSDF_PRINCIPLED')
            h = N.new('ShaderNodeTexImage'); h.name = "PT_hgt"; h.image = _img(hp, False)
            if tex.inputs['Vector'].links:
                Lk.new(tex.inputs['Vector'].links[0].from_socket, h.inputs['Vector'])
            bp = N.new('ShaderNodeBump'); bp.name = "PT_bump"; bp.inputs['Strength'].default_value = BUMP[kind]; bp.inputs['Distance'].default_value = 0.004
            Lk.new(h.outputs['Color'], bp.inputs['Height'])
            for l in list(bsdf.inputs['Normal'].links):
                Lk.remove(l)
            Lk.new(bp.outputs['Normal'], bsdf.inputs['Normal'])
            n += 1
    print("atlas pintados:", n)


def classify(m, base, metal, rough):
    nm = m.name.split("_", 1)[1] if "_" in m.name else m.name
    if SKIP.search(nm):
        return None
    if re.search(r"Beret", nm):     # boina: casi plana (color manda)
        return ("Fabric", 3.0, 0.97, 0.03)
    if metal > 0.5:
        warm = base[0] > base[2] * 1.25
        return ("Gilded" if warm else "Metal", 2.0, 0.45, 0.25)
    if STRAW.search(nm):
        return ("Wood_Grain", 1.5, 0.65, 0.2)
    if LEATHER.search(nm):
        return ("Wood_Grain", 2.0, 0.9, 0.15)
    if CLOTH.search(nm):
        return ("Fabric", 1.5, 0.93, 0.08)
    if rough <= 0.6 or re.search(r"Phones|Radio|Cam|Bracelet|Watch|Brush", nm):
        return ("Wall_Soft", 3.0, 0.92, 0.1)
    return ("Fabric", 1.5, 0.9, 0.15)


def paint_accessories():
    imgs, avg = {}, {}
    done = []
    for m in bpy.data.materials:
        if m.name.endswith("_Paint") or not m.use_nodes or not re.match(r"^(Caf|Cou|Cur|Doc|Gar|Gen|Grd|Pnt|Stu|Tou)_", m.name):
            continue
        N, Lk = m.node_tree.nodes, m.node_tree.links
        for x in [x for x in N if x.name.startswith("PT_")]:   # permite reaplicar: quita lo anterior (el color base original queda en el valor por defecto)
            N.remove(x)
        bsdf = next((x for x in N if x.type == 'BSDF_PRINCIPLED'), None)
        if not bsdf or bsdf.inputs['Base Color'].links:
            continue
        base = tuple(bsdf.inputs['Base Color'].default_value)
        spec = classify(m, base, bsdf.inputs['Metallic'].default_value, bsdf.inputs['Roughness'].default_value)
        if not spec:
            continue
        fam, sc, tint, bump = spec
        if fam not in imgs:
            imgs[fam] = (_img(os.path.join(TEX, f"T_{fam}.png"), True), _img(os.path.join(TEX, f"H_{fam}.png"), False))
            avg[fam] = _avg(imgs[fam][0])
        for x in [x for x in N if x.name.startswith("PT_")]:
            N.remove(x)
        tc = N.new('ShaderNodeTexCoord'); tc.name = "PT_uv"
        mp = N.new('ShaderNodeMapping'); mp.name = "PT_map"; mp.inputs['Scale'].default_value = (sc, sc, sc); Lk.new(tc.outputs['Object'], mp.inputs['Vector'])
        t = N.new('ShaderNodeTexImage'); t.name = "PT_col"; t.image = imgs[fam][0]; t.projection = 'BOX'; t.projection_blend = 0.25
        h = N.new('ShaderNodeTexImage'); h.name = "PT_hgt"; h.image = imgs[fam][1]; h.projection = 'BOX'; h.projection_blend = 0.25
        Lk.new(mp.outputs['Vector'], t.inputs['Vector']); Lk.new(mp.outputs['Vector'], h.inputs['Vector'])
        bw = N.new('ShaderNodeRGBToBW'); bw.name = "PT_bw"; Lk.new(t.outputs['Color'], bw.inputs['Color'])
        nm = N.new('ShaderNodeMath'); nm.name = "PT_norm"; nm.operation = 'MULTIPLY'; nm.inputs[1].default_value = 1.0 / max(avg[fam], 0.05); Lk.new(bw.outputs['Val'], nm.inputs[0])
        c = N.new('ShaderNodeCombineColor'); c.name = "PT_g"
        for i in range(3):
            Lk.new(nm.outputs['Value'], c.inputs[i])
        mul = N.new('ShaderNodeMix'); mul.name = "PT_mul"; mul.data_type = 'RGBA'; mul.blend_type = 'MULTIPLY'
        mul.inputs[0].default_value = 1.0; mul.inputs[6].default_value = base; Lk.new(c.outputs['Color'], mul.inputs[7])
        fin = N.new('ShaderNodeMix'); fin.name = "PT_mix"; fin.data_type = 'RGBA'; fin.blend_type = 'MIX'; fin.inputs[0].default_value = tint
        Lk.new(t.outputs['Color'], fin.inputs[6]); Lk.new(mul.outputs[2], fin.inputs[7])
        bp = N.new('ShaderNodeBump'); bp.name = "PT_bump"; bp.inputs['Strength'].default_value = bump; bp.inputs['Distance'].default_value = 0.004
        Lk.new(h.outputs['Color'], bp.inputs['Height'])
        for l in list(bsdf.inputs['Normal'].links):
            Lk.remove(l)
        Lk.new(fin.outputs[2], bsdf.inputs['Base Color']); Lk.new(bp.outputs['Normal'], bsdf.inputs['Normal'])
        done.append(m.name)
    print("accesorios pintados:", len(done))
    return done


def apply():
    print("archivo:", bpy.data.filepath, "| sucio:", bpy.data.is_dirty)
    paint_atlases()
    return paint_accessories()
