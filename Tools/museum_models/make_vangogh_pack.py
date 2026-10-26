"""Genera el PACK VAN GOGH de texturas para Krita (guias de pincelada tenues, formas, paleta y fichas).

Uso (desde la raiz del proyecto):  python Tools/museum_models/make_vangogh_pack.py

Reutiliza el dibujo de formas (lineart) de make_texture_templates.py y anade, por familia:
  - capa GUIA_pinceladas: trazos tenues que siguen un campo de flujo (ritmo, direccion, remolino suave)
  - capa UNDERPAINT_color: manchas de color tileables con la paleta de la familia (opcional)
  - ficha PNG con vista previa, forma, movimiento, pasos y paleta
Salida (se borra y recrea): ArtSource/Museum/VanGogh_Pack/  y  ArtSource/Museum/TheLivingCanvas_VanGogh_Pack.zip
"""
import io
import math
import os
import shutil
import sys
import textwrap
import zipfile
import zlib

import numpy as np
from PIL import Image, ImageDraw

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(ROOT, "Tools"))
import make_texture_templates as T  # noqa: E402
from make_prototype_textures import FONT, FONT_S, new_layer, write_ora  # noqa: E402

OUT = os.path.join(ROOT, "ArtSource", "Museum", "VanGogh_Pack")
ZIP = os.path.join(ROOT, "ArtSource", "Museum", "TheLivingCanvas_VanGogh_Pack.zip")
EXPORT_DIR = T.EXPORT_DIR

# Paleta base del proyecto (ART_DIRECTION.md)
CORE = [("Azul cerúleo", "#526A83"), ("Amarillo cálido", "#D4A72C"), ("Verde oliva", "#65785A"),
        ("Terracota", "#A85F47"), ("Azul grisáceo", "#747983"), ("Crema envejecida", "#E0CDB0")]

# ------------------------------------------------------------------ SOLO EXTERIOR: familias, materiales y objetos (leido del .blend del exterior)
EXT_USE = {
    "Plaster": ("M_Museum_Plaster", "paredes (Ext_Walls), buhardillas, marcos de ventana, frontispicio de la entrada"),
    "Stone_Blocks": ("M_Museum_Stone", "zócalo (Ext_Plinth), molduras (Ext_Trim_Stone), esquinas, chimenea, pilares del portón, muro y cerca de piedra, farolas"),
    "Roof_Tiles": ("M_Museum_Roof, M_Museum_AwningA", "tejado principal y frontón cruzado, buhardillas, chimenea, toldos rayados, cubierta del pórtico"),
    "Wood_Grain": ("M_Museum_Wood, M_Museum_WoodDark", "marcos de ventanas y puerta, bancos, cajas, caballete del cartel OPEN, vigas del alero"),
    "Painted_Boards": ("M_Museum_Shutter, M_Museum_Door, M_Sign_Board", "contraventanas verdes, puerta azul de la entrada, cartel MUSEUM y cartel OPEN, jardineras"),
    "Metal": ("M_Museum_Metal, M_Iron", "canalones, farolas, patas de bancos, barandilla del balcón, hierro del portón y de las ventanas"),
    "Gilded": ("M_Museum_Brass", "pomos y bisagras, puntas doradas del portón, pincel de la veleta, regadera"),
    "Fabric": ("M_Fabric_Mustard, M_Rug_Terracotta, M_Paper", "cortinas vistas a través de las ventanas, centros de flores amarillas"),
    "Leaves": ("M_Plant_Leaf, M_Plant_LeafLight, M_Leaf_Dark, M_Ivy_Light, M_Leaf_Sage", "arbustos, cipreses, hiedra de la fachada, jardineras, hierba y macetas"),
    "Petals": ("M_Flower_* (amarilla, rosa, blanca, iris, lavanda, geranio), M_Sunflower_Disc", "pradera, parterres, jardineras de ventana, macetas de girasol"),
    "Grass_Ground": ("M_Ground_Grass, M_Ground_Earth, M_Soil", "todo el césped del jardín, tierra del sendero, tierra de jardineras y parterres"),
    "Path_Stone": ("M_Path_Stone, M_Path_StoneWarm", "losas del sendero, escalones de la entrada, piedras del muro y la cerca, bordillo de parterres"),
    "Bark": ("M_Bark", "troncos de los cipreses, tallos de macetas y jardineras"),
    "Glass": ("M_Museum_Glass", "ventanas, cristal de la entrada, ojos de buey y buhardillas"),
    "Paper_Canvas": ("M_Museum_AwningB, M_Picket, M_Paper", "rayas crema de los toldos, estacas blancas de la cerca"),
}
EXT_ORDER = ["Plaster", "Roof_Tiles", "Stone_Blocks", "Grass_Ground", "Path_Stone", "Painted_Boards", "Wood_Grain",
             "Leaves", "Bark", "Petals", "Glass", "Metal", "Gilded", "Paper_Canvas", "Fabric"]

# ------------------------------------------------------------------ paletas por familia: oscuro, base, claro, luz, acento
PAL = {
    "Plaster": ["#B9AE98", "#DDD6CA", "#EDE5D3", "#F6F0E0", "#C8B79A"],
    "Stone_Blocks": ["#4C5563", "#747983", "#8B909A", "#A59F97", "#526A83"],
    "Roof_Tiles": ["#6F3A2E", "#A85F47", "#C0725A", "#D98B63", "#526A83"],
    "Wood_Planks": ["#5E4029", "#9A6E4A", "#B58459", "#C9A06B", "#526A83"],
    "Wood_Grain": ["#B59C78", "#DDD6CA", "#E8D9BC", "#F0E4CC", "#C9A06B"],
    "Painted_Boards": ["#3F5240", "#65785A", "#7A8F69", "#93A97A", "#D4A72C"],
    "Floor_Tiles_Hall": ["#6E8387", "#8FA3A8", "#A8BABD", "#C9D3D2", "#D4A72C"],
    "Flagstones": ["#A8977C", "#CDBDA3", "#DDCFB6", "#EBDFC8", "#747983"],
    "Concrete": ["#5E6066", "#7B7D82", "#9A9CA0", "#B3B4B6", "#526A83"],
    "Ceramic_Glaze": ["#CFC6B2", "#F0E8D8", "#F8F2E6", "#FFFFFF", "#526A83"],
    "Metal": ["#2F333C", "#4A4F5A", "#626874", "#7E8590", "#A85F47"],
    "Gilded": ["#9A7428", "#C49A3A", "#D4A72C", "#F3DC96", "#A85F47"],
    "Fabric": ["#B9AE98", "#DDD6CA", "#EDE5D3", "#F6F0E0", "#C8B79A"],
    "Rug_Hall": ["#6F3A2E", "#A85F47", "#C0725A", "#D98B63", "#526A83"],
    "Leaves": ["#4F6347", "#65785A", "#7F9467", "#93A97A", "#D4A72C"],
    "Petals": ["#B8851A", "#D4A72C", "#E8C44F", "#F2DC8A", "#A85F47"],
    "Grass_Ground": ["#566A44", "#6E8157", "#869A6B", "#9CAE7B", "#D4A72C"],
    "Path_Stone": ["#6F727A", "#9A9A98", "#B0ADA5", "#C6B79A", "#A85F47"],
    "Bark": ["#2F2119", "#5B4030", "#745440", "#8A6A52", "#65785A"],
    "Glass": ["#2D4A5E", "#456F88", "#5B87A0", "#C8DCE6", "#D4A72C"],
    "Paper_Canvas": ["#CFC4A8", "#EFE6CF", "#F6EEDC", "#FFFBEF", "#C8B79A"],
}

# ------------------------------------------------------------------ textos por familia: forma, movimiento, pasos
HOW = {
    "Plaster": ("Manchas anchas y planas, como pasadas de llana: parches redondeados de 15-30 cm que se solapan.",
                "Pasadas cortas y suaves, algo inclinadas, con un leve giro (como una S muy abierta).",
                ["Rellena con la base crema y marca 3-4 zonas más claras y más oscuras muy suaves.",
                 "Sigue las líneas tenues: un toque por trazo, sin retocar. Que se vea la pasada.",
                 "Mezcla cálido (crema) y frío (gris azulado) en el mismo trazo; nada de tonos saturados.",
                 "Está en gris/crema CLARO: Unity la tiñe con el color de cada pared."]),
    "Stone_Blocks": ("Bloques rectangulares en hiladas (filas de ~30 cm), cada uno con su propio tono.",
                     "Trazos horizontales cortos y ligeramente curvos que siguen cada bloque. Un contorno azul oscuro entre bloques.",
                     ["Pinta cada bloque de un gris-azul algo distinto (más claro, más oscuro, uno cálido).",
                      "Dentro de cada bloque: 3-5 trazos horizontales con un tono más claro arriba y más oscuro abajo.",
                      "Marca las juntas con un trazo fino de azul cerúleo oscuro (estilo Van Gogh: contorno visible).",
                      "Un par de golpes de cincel (rayitas diagonales) en algunos bloques."]),
    "Roof_Tiles": ("Tejas de barro con borde festoneado (0,25 x 0,33 m), colocadas al tresbolillo.",
                   "Un trazo curvo hacia abajo por cada teja (como una coma larga). Hileras ordenadas.",
                   ["Base terracota; a cada teja dale un tono distinto (más naranja, más rojiza, alguna violácea).",
                    "Un trazo de arriba a abajo por teja, empezando por el punto amarillo de la guía.",
                    "Sombra azul-grisácea en el borde inferior de cada teja; luz cálida en el superior.",
                    "Rompe el orden: alguna teja casi amarilla y alguna oscura."]),
    "Wood_Planks": ("Tablas largas de 20 cm en una sola dirección, con juntas a tope alternadas.",
                    "Trazos largos y casi rectos, uno por tabla, con una ligera ondulación (veta).",
                    ["Cada tabla un marrón algo distinto; la junta, un trazo fino oscuro.",
                     "Pasa 2-3 trazos largos por tabla con tonos claro/oscuro alternados.",
                     "En uno o dos nudos: círculos concéntricos pequeños, los trazos rodean el nudo."]),
    "Wood_Grain": ("Vetas largas en un solo eje, con 'arcos de catedral' y algún nudo.",
                   "Trazos largos y ondulantes, paralelos, que rodean los nudos como un remolino pequeño.",
                   ["Base crema cálida (TENIDA: Unity la tiñe a madera clara u oscura).",
                    "Trazos largos en vaivén: claro, medio, oscuro, repitiendo el ritmo.",
                    "En los nudos, que los trazos se curven alrededor (aquí sí un pequeño remolino).",
                    "Mantén los valores CLAROS; el oscuro de la madera lo pone el color del material."]),
    "Painted_Boards": ("Tablas verticales de 12 cm con una ranura en V entre ellas (contraventanas, puerta, carteles).",
                       "Trazos largos verticales, de arriba abajo, con una pequeña variación de tono por tabla.",
                       ["Base verde oliva; cada tabla un verde algo distinto.",
                        "Un trazo vertical largo por tabla; pasa el pincel casi seco para que quede una veta.",
                        "Descascarillado: 3-4 toques cortos de madera marrón o crema donde la pintura se cae.",
                        "Una línea azul oscura fina en cada ranura."]),
    "Floor_Tiles_Hall": ("Baldosas cuadradas de 40 cm con juntas finas y un rombo en cada cruce de 4 baldosas.",
                         "Dentro de cada baldosa: 2-3 trazos diagonales cortos, como un barniz esmaltado.",
                         ["Cada baldosa de un gris-azul algo distinto.",
                          "Trazos diagonales (45°) siempre en el mismo sentido: da ritmo al suelo.",
                          "Rombo del cruce: amarillo apagado o terracota para romper el frío."]),
    "Flagstones": ("Piedra moteada, SIN juntas (la geometría ya trae las losas).",
                   "Manchas redondeadas y toques cortos curvos, sin dirección fija.",
                   ["Base arena; manchas suaves más claras y más oscuras.",
                    "Toques cortos curvos (media luna) que se solapan.",
                    "Un poco de azul grisáceo en las zonas de sombra."]),
    "Concrete": ("Superficie de cemento con arcos de llana y alguna grieta fina.",
                 "Arcos anchos de llana (abanicos) y una o dos grietas finas que serpentean.",
                 ["Base gris; zonas más claras y más oscuras muy suaves.",
                  "Arcos de abanico solapados siguiendo las líneas tenues.",
                  "Una grieta: una línea fina oscura que zigzaguea, sin retocarla."]),
    "Ceramic_Glaze": ("Esmalte liso casi blanco, con brillos largos y alguna gota.",
                      "Pocos trazos largos y suaves (brillos) y pequeñas gotas.",
                      ["Base crema muy clara.",
                       "Brillos: 2-3 trazos largos y finos más claros, casi blancos.",
                       "Un toque cálido y uno frío (azul) en las esquinas para que no sea plano."]),
    "Metal": ("Metal cepillado horizontal con alguna mancha de óxido o abolladura.",
              "Trazos horizontales finos y largos, casi rectos.",
              ["Base gris azulado oscuro.",
               "Pasadas horizontales finas alternando más claro y más oscuro.",
               "Óxido: 2-3 manchas pequeñas terracota, con toques cortos."]),
    "Gilded": ("Láminas de oro cuadradas (6 cm) algo solapadas, con trazos de bruñido.",
               "Toques pequeños y cuadrados, y algunas pasadas alargadas de brillo.",
               ["Base ocre dorado.",
                "Toques cuadrados pequeños con amarillo cálido y amarillo claro.",
                "Sombras terracota o marrón en los bordes; la luz, casi crema."]),
    "Fabric": ("Tejido en cuadrícula cruzada con pliegues verticales.",
               "Pasadas horizontales y luego verticales, finas, que se cruzan (tejido).",
               ["Base crema/gris claro (TENIDA: Unity la tiñe al color de cada tela).",
                "Primero pasadas horizontales finas, luego verticales por encima.",
                "Pliegues: 2-3 trazos verticales más oscuros y anchos, suaves."]),
    "Rug_Hall": ("Medallón circular: anillo-borde con motivo repetido, campo medio y roseta central (NO repetible).",
                 "Trazos que rodean el centro en círculos concéntricos.",
                 ["Pinta primero los anillos de color por zonas (terracota, azul, mostaza).",
                  "Sigue los círculos: un trazo curvo por tramo, como pétalos en el borde.",
                  "Roseta central: pétalos radiales amarillos y terracota."]),
    "Leaves": ("Patrón repetido de hojas con nervio central y nervios en espina de pez.",
               "Desde el nervio central hacia el borde de cada hoja, trazos curvados (como pelo).",
               ["Cada hoja de un verde distinto (oliva oscuro, claro, algún amarillo-verde).",
                "Un trazo largo por el nervio central, y trazos laterales cortos hacia el borde.",
                "Toques de amarillo cálido en las puntas; azul cerúleo en las sombras."]),
    "Petals": ("Pétalos radiales saliendo de pequeños centros repartidos.",
               "Cada pétalo un trazo corto de dentro hacia fuera, como los rayos de un sol (girasol).",
               ["Base amarillo cálido.",
                "Desde cada centro: 6-8 trazos radiales cortos, algunos más claros, otros más anaranjados.",
                "Centros: toques marrones oscuros y terracota."]),
    "Grass_Ground": ("Césped y tierra: matas de trazos cortos con dirección y algún parche de tierra.",
                     "Trazos largos y curvos que suben y se ondulan como un campo de trigo bajo el viento (Van Gogh).",
                     ["Base verde; 3-4 manchas grandes más claras, más oscuras y alguna amarillenta.",
                      "Sigue las líneas de flujo: trazos largos hacia arriba que se curvan en olas.",
                      "Algún trazo amarillo cálido suelto (paja) y azul cerúleo en las zonas de sombra.",
                      "Tierra (parches): marrón con trazos horizontales cortos."]),
    "Path_Stone": ("Losas/adoquines irregulares (polígonos) con juntas.",
                   "Trazos curvos cortos dentro de cada losa, siguiendo su contorno.",
                   ["Cada losa un tono distinto (gris azulado, beige cálido, uno rosado).",
                    "3-4 trazos curvos por losa que siguen su forma; más claro arriba.",
                    "Juntas: trazo fino oscuro. Un poco de verde en algunas juntas (musgo)."]),
    "Bark": ("Corteza con fisuras y crestas verticales (troncos de ciprés).",
             "Trazos largos verticales algo ondulados, con grietas oscuras entre ellos.",
             ["Base marrón oscuro.",
              "Crestas: trazos verticales más claros (marrón medio y cálido).",
              "Fisuras: líneas finas casi negras entre crestas; toques de verde en la sombra."]),
    "Glass": ("Cristal con 2-3 bandas de reflejo diagonales (paralelogramos suaves).",
              "Trazos largos y rectos a 45°, suaves; degradado de cielo (claro arriba, cálido abajo).",
              ["Base azul; degradado más claro arriba y un toque cálido abajo.",
               "Bandas de reflejo: 2-3 pasadas anchas y largas, casi transparentes.",
               "Un par de toques amarillos pequeños (luz de farol) en una esquina."]),
    "Paper_Canvas": ("Trama fina de lienzo en cuadrícula, suave (toldos, valla, etiquetas).",
                     "Pasadas finas horizontales y verticales que se cruzan, muy sutiles.",
                     ["Base crema.",
                      "Pasadas finas casi secas en dos direcciones.",
                      "Muy poco contraste: es un fondo, no protagonista."]),
}

# ------------------------------------------------------------------ campos de flujo (angulos en grados; 90 = hacia abajo, -90 = arriba)
S = math.sin
TAU = math.tau


def wave(px, kx, ky, ph=0.0):
    return lambda x, y: S(TAU * (kx * x + ky * y) / px + ph)


def specs(name, px, ppm):
    """Lista de capas de trazos: (modo, sx, sy, stagger, len_m, angulo_fn, curvatura_rad, ancho, extra)."""
    w = lambda kx, ky, ph=0.0: wave(px, kx, ky, ph)
    if name == "Plaster":
        return [("grid", .17, .17, .5, .22, lambda x, y: 20 + 35 * w(1.3, .7)(x, y), .5, 5)]
    if name == "Stone_Blocks":
        return [("grid", .38, .3, .5, .30, lambda x, y: 4 * w(3, 1)(x, y), .25, 5)]
    if name == "Roof_Tiles":
        return [("grid", .25, .33, .5, .26, lambda x, y: 90, .5, 6)]
    if name == "Wood_Planks":
        return [("grid", 1.0, .2, .5, .9, lambda x, y: 3 * w(1, 3)(x, y), .15, 5)]
    if name == "Wood_Grain":
        return [("grid", .5, .075, .5, .45, lambda x, y: 5 * w(2, 5)(x, y), .12, 4)]
    if name == "Painted_Boards":
        return [("grid", .12, .5, .5, .45, lambda x, y: 90 + 3 * w(4, 2)(x, y), .1, 5)]
    if name == "Floor_Tiles_Hall":
        return [("grid", .4, .4, 0.0, .26, lambda x, y: 45, .4, 6)]
    if name == "Flagstones":
        return [("grid", .24, .24, .5, .2, lambda x, y: 35 * w(2, 3)(x, y), .6, 5)]
    if name == "Concrete":
        return [("grid", .3, .3, .5, .3, lambda x, y: 20 + 50 * w(1.5, 1)(x, y), .8, 5)]
    if name == "Ceramic_Glaze":
        return [("grid", .32, .2, .5, .3, lambda x, y: -25, .3, 4)]
    if name == "Metal":
        return [("grid", .4, .06, .5, .38, lambda x, y: 0, .05, 3)]
    if name == "Gilded":
        return [("grid", .09, .09, .5, .08, lambda x, y: 25 + 20 * w(2, 2)(x, y), .3, 3)]
    if name == "Fabric":
        return [("grid", .07, .07, .5, .2, lambda x, y: 0, .02, 3), ("grid", .07, .07, .5, .2, lambda x, y: 90, .02, 3)]
    if name == "Rug_Hall":
        c = px / 2
        return [("grid", .1, .1, .5, .1, lambda x, y: math.degrees(math.atan2(y - c, x - c)) + 90, .0, 5, dict(maxr=.47 * px, tile=False, norm=True))]
    if name == "Leaves":
        return [("grid", .24, .24, .5, .2, lambda x, y: (55 if int(x / (.24 * ppm)) % 2 == 0 else -55) + 25 * w(2, 1)(x, y), .5, 4)]
    if name == "Petals":
        return [("radial", .34, .34, 0, .09, None, 0, 4)]
    if name == "Grass_Ground":
        return [("grid", .3, .35, .5, .6, lambda x, y: -90 + 38 * w(3, 2)(x, y) + 15 * w(1, 5, 1.3)(x, y), .6, 7)]
    if name == "Path_Stone":
        return [("grid", .26, .26, .5, .22, lambda x, y: 40 * w(2, 2)(x, y), .6, 5)]
    if name == "Bark":
        return [("grid", .09, .35, .5, .45, lambda x, y: 90 + 8 * w(5, 2)(x, y), .2, 4)]
    if name == "Glass":
        return [("grid", .22, .22, .5, .5, lambda x, y: 45, .1, 4)]
    if name == "Paper_Canvas":
        return [("grid", .06, .06, .5, .12, lambda x, y: 0, .02, 3), ("grid", .06, .06, .5, .12, lambda x, y: 90, .02, 3)]
    return [("grid", .2, .2, .5, .2, lambda x, y: 0, .2, 4)]


# ------------------------------------------------------------------ trazos
def draw_stroke(d, pts, w0, px, tile):
    offs = [(0, 0)]
    if tile:
        xs, ys = [p[0] for p in pts], [p[1] for p in pts]
        offs = [(dx, dy) for dx in (-px, 0, px) for dy in (-px, 0, px)
                if max(xs) + dx >= -8 and min(xs) + dx <= px + 8 and max(ys) + dy >= -8 and min(ys) + dy <= px + 8]
    n = len(pts)
    for dx, dy in offs:
        for col, k in (((35, 30, 60, 70), 1.9), ((255, 247, 224, 125), 1.0)):
            for i in range(n):
                t = i / max(1, n - 1)
                r = max(1.0, w0 * (1.0 - 0.65 * t) * k / 2.0)
                x, y = pts[i][0] + dx, pts[i][1] + dy
                d.ellipse([x - r, y - r, x + r, y + r], fill=col)
        # punto de inicio (amarillo): por donde se empieza el trazo
        x, y = pts[0][0] + dx, pts[0][1] + dy
        d.ellipse([x - 3, y - 3, x + 3, y + 3], fill=(255, 205, 70, 215))


def trace(x, y, ang_fn, length, step, curv):
    pts = [(x, y)]
    n = max(3, int(length / step))
    for i in range(n):
        a = math.radians(ang_fn(x, y)) + curv * (i / n - 0.5)
        x += math.cos(a) * step
        y += math.sin(a) * step
        pts.append((x, y))
    return pts


def flow_layer(name, px, tile, ppm, rng):
    lay = new_layer(px, px)
    d = ImageDraw.Draw(lay)
    for sp in specs(name, px, ppm):
        mode, sx, sy, stag, ln, ang, curv, wd = sp[:8]
        ex = sp[8] if len(sp) > 8 else {}
        step = max(2.0, ln * ppm / 45)   # paso fino: la linea sale continua, no como cuentas
        if mode == "radial":
            cell = sx * ppm
            n = int(px / cell)
            for i in range(n):
                for j in range(n):
                    cx = (i + .5) * cell + rng.uniform(-.2, .2) * cell
                    cy = (j + .5) * cell + rng.uniform(-.2, .2) * cell
                    for k in range(7):
                        a = k * TAU / 7 + rng.uniform(-.15, .15)
                        r0, r1 = .035 * ppm, (.035 + ln) * ppm
                        draw_stroke(d, [(cx + math.cos(a) * r0, cy + math.sin(a) * r0), (cx + math.cos(a) * (r0 + r1) / 2, cy + math.sin(a) * (r0 + r1) / 2),
                                        (cx + math.cos(a) * r1, cy + math.sin(a) * r1)], wd, px, tile)
            continue
        cw, ch = sx * ppm, sy * ppm
        nx, ny = max(1, int(round(px / cw))), max(1, int(round(px / ch)))
        cw, ch = px / nx, px / ny
        for j in range(ny):
            for i in range(nx):
                x = (i + .5 + (stag if j % 2 else 0.0)) * cw + rng.uniform(-.12, .12) * cw
                y = (j + .5) * ch + rng.uniform(-.12, .12) * ch
                if "maxr" in ex and math.hypot(x - px / 2, y - px / 2) > ex["maxr"]:
                    continue
                if ex.get("norm"):
                    if math.hypot(x - px / 2, y - px / 2) < .06 * px:
                        continue
                x0, y0 = x - math.cos(math.radians(ang(x, y))) * ln * ppm / 2, y - math.sin(math.radians(ang(x, y))) * ln * ppm / 2
                draw_stroke(d, trace(x0, y0, ang, ln * ppm, step, curv), wd, px, tile and ex.get("tile", True))
    return lay


# ------------------------------------------------------------------ underpaint (manchas tileables)
def tile_noise(px, cycles, rng):
    n = rng.standard_normal((px, px))
    F = np.fft.rfft2(n)
    ky = np.fft.fftfreq(px)[:, None] * px
    kx = np.fft.rfftfreq(px)[None, :] * px
    F *= np.exp(-(kx ** 2 + ky ** 2) / (2.0 * cycles ** 2))
    a = np.fft.irfft2(F, s=(px, px))
    a -= a.min()
    return a / max(a.max(), 1e-6)


def hex2rgb(h):
    h = h.lstrip("#")
    return np.array([int(h[i:i + 2], 16) for i in (0, 2, 4)], np.float32)


def underpaint(name, px, rng):
    dark, base, light, high, acc = [hex2rgb(h) for h in PAL[name]]
    n1 = tile_noise(px, 3, rng)
    n2 = tile_noise(px, 7, rng)
    t = np.clip(0.65 * n1 + 0.35 * n2, 0, 1)
    t = (t - t.min()) / max(np.ptp(t), 1e-6)
    out = np.zeros((px, px, 3), np.float32)
    lo = t < 0.5
    k = np.where(lo, t / 0.5, (t - 0.5) / 0.5)[..., None]
    out = np.where(lo[..., None], dark * (1 - k) + base * k, base * (1 - k) + light * k)
    ac = np.clip((n2 - 0.80) / 0.12, 0, 1)[..., None] * 0.55
    out = out * (1 - ac) + acc * ac
    hl = np.clip((n1 - 0.86) / 0.1, 0, 1)[..., None] * 0.5
    out = out * (1 - hl) + high * hl
    mix = 0.55   # sutil: no sustituye a tu pintura, solo reparte color
    out = base * (1 - mix) + out * mix
    return Image.fromarray(np.clip(out, 0, 255).astype(np.uint8), "RGB").convert("RGBA")


# ------------------------------------------------------------------ ficha
def swatch_row(d, x, y, cols, size=44):
    for i, h in enumerate(cols):
        d.rectangle([x + i * (size + 70), y, x + i * (size + 70) + size, y + size], fill=h, outline="#222222")
        d.text((x + i * (size + 70) - 2, y + size + 4), h, fill="#222222", font=FONT_S)


def ficha(fam, px, ppm, preview, tile):
    name, _, _, mpr, mats, where, stroke, base, tenida, arrows, fn = fam
    forma, mov, pasos = HOW[name]
    W, H = 1500, 960
    im = Image.new("RGB", (W, H), "#F4EFE4")
    d = ImageDraw.Draw(im)
    pv = preview.convert("RGB").resize((820, 820), Image.LANCZOS)
    im.paste(pv, (30, 110))
    d.rectangle([30, 110, 850, 930], outline="#222222", width=3)
    d.text((30, 30), "T_%s" % name, fill="#222222", font=FONT)
    d.text((30, 70), "%dx%d px  |  %s  |  %s" % (px, px, "REPETIBLE (tecla W en Krita)" if tile else "NO repetible (diseño completo)",
                                                 ("1 repetición = %g m" % mpr) if tile else "ocupa toda la pieza"), fill="#444444", font=FONT_S)
    x, y = 890, 36

    def block(title, text, y, col="#222222"):
        d.text((x, y), title, fill="#8A4B2E", font=FONT_S)
        y += 26
        for ln in textwrap.wrap(text, 52):
            d.text((x, y), ln, fill=col, font=FONT_S)
            y += 24
        return y + 8

    y = block("SE VE EN EL EXTERIOR:", EXT_USE[name][1], y)
    y = block("MATERIALES:", EXT_USE[name][0], y, "#444444")
    y = block("FORMA:", forma, y)
    y = block("MOVIMIENTO:", mov, y)
    d.text((x, y), "PASOS:", fill="#8A4B2E", font=FONT_S)
    y += 26
    for i, p in enumerate(pasos, 1):
        for k, ln in enumerate(textwrap.wrap(p, 50)):
            d.text((x if k == 0 else x + 24, y), ("%d. " % i if k == 0 else "") + ln, fill="#222222", font=FONT_S)
            y += 24
        y += 4
    y += 6
    d.text((x, y), "PALETA (oscuro, base, claro, luz, acento):", fill="#8A4B2E", font=FONT_S)
    swatch_row(d, x, y + 28, PAL[name][:5])
    y += 110
    ex = "Exportar: T_%s.png en %s" % (name, EXPORT_DIR)
    for ln in textwrap.wrap(ex, 52):
        d.text((x, y), ln, fill="#444444", font=FONT_S)
        y += 24
    for k, ln in enumerate(textwrap.wrap("Líneas tenues = por dónde pasa el pincel. Punto amarillo = dónde EMPIEZA el trazo.", 52)):
        d.text((x, y + 6 + k * 24), ln, fill="#444444", font=FONT_S)
    return im


# ------------------------------------------------------------------ hoja de referencia de pinceladas
def cheatsheet(path):
    W, H = 1500, 1000
    im = Image.new("RGB", (W, H), "#F4EFE4")
    d = ImageDraw.Draw(im)
    d.text((30, 24), "Hoja de pinceladas estilo Van Gogh (practica cada una antes de pintar)", fill="#222222", font=FONT)
    rng = np.random.default_rng(7)

    def brush(pts, w, col):
        n = len(pts)
        for i, (x, y) in enumerate(pts):
            r = max(1.5, w * (1 - 0.6 * i / max(1, n - 1)) / 2)
            d.ellipse([x - r, y - r, x + r, y + r], fill=col)

    cols = ["#526A83", "#D4A72C", "#65785A", "#A85F47", "#747983", "#8A6A52"]
    items = [("TOQUE CORTO", "Pulsa y arrastra poco. Para planos de color, piedra, yeso.",
              lambda ox, oy, c: [brush([(ox + k * 4 + j * 28, oy + j * 3 + i * 26 + k * 2) for k in range(7)], 14, c) for i in range(4) for j in range(4)]),
             ("COMA", "Trazo con cola que se afina: tejas, pétalos, hojas.",
              lambda ox, oy, c: [brush([(ox + 20 + i * 80 + 24 * math.sin(k / 13 * 2.6), oy + j * 82 + k * 4.6) for k in range(14)], 18, c) for i in range(5) for j in range(3)]),
             ("TRAZO LARGO", "Un gesto continuo de lado a lado. Madera, metal, hierba alta.",
              lambda ox, oy, c: [brush([(ox + k * 6, oy + j * 34 + 4 * math.sin(k / 3.0 + j)) for k in range(30)], 11, c) for j in range(6)]),
             ("MEDIA LUNA", "Arcos cortos solapados, como escamas. Cemento, llana, pizarra.",
              lambda ox, oy, c: [brush([(ox + 40 + i * 70 + 28 * math.cos(a), oy + j * 52 + 22 * math.sin(a)) for a in np.linspace(0.2, 2.9, 12)], 10, c) for i in range(5) for j in range(4)]),
             ("OLA / REMOLINO", "Trazos largos que serpentean: cielo y campo de Van Gogh. Úsalo en césped.",
              lambda ox, oy, c: [brush([(ox + k * 5 + 8 * j, oy + j * 34 + 22 * math.sin(k / 4.0 + j * 0.8)) for k in range(34)], 11, c) for j in range(6)]),
             ("PUNTEADO", "Toques redondos sueltos. Flores, musgo, luz sobre hojas.",
              lambda ox, oy, c: [brush([(ox + rng.uniform(0, 200), oy + rng.uniform(0, 160))], rng.uniform(8, 16), c) for _ in range(60)])]
    for idx, (title, desc, fn) in enumerate(items):
        ox = 40 + (idx % 3) * 480
        oy = 90 + (idx // 3) * 460
        d.rectangle([ox - 10, oy - 6, ox + 440, oy + 410], outline="#222222")
        d.text((ox, oy), title, fill="#8A4B2E", font=FONT)
        for ln_i, ln in enumerate(textwrap.wrap(desc, 46)):
            d.text((ox, oy + 34 + ln_i * 22), ln, fill="#222222", font=FONT_S)
        fn(ox + 8, oy + 130, cols[idx % len(cols)])
    im.save(path)


# ------------------------------------------------------------------ main
def gpl(path):
    seen, rows = set(), []
    for n, h in CORE:
        rows.append((h, n))
    for fam, pal in PAL.items():
        for i, h in enumerate(pal):
            rows.append((h, "%s %s" % (fam, ["oscuro", "base", "claro", "luz", "acento"][i])))
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        f.write("GIMP Palette\nName: TheLivingCanvas_VanGogh\nColumns: 5\n#\n")
        for h, n in rows:
            r, g, b = [int(h.lstrip("#")[i:i + 2], 16) for i in (0, 2, 4)]
            f.write("%3d %3d %3d %s\n" % (r, g, b, n))


README = """# Pack Van Gogh de texturas para Krita — The Living Canvas

Este pack tiene **solo las texturas del EXTERIOR del museo** (fachada, tejado, jardín, camino, portón, vegetación y mobiliario exterior), para pintarlas a mano con estética Van Gogh aunque nunca hayas pintado texturas. Son 15 plantillas; cada una cubre varios materiales del modelo (ver la tabla del final).
Hay una carpeta por tipo de archivo:

- `krita/` → un `.ora` por textura (ábrelos con Krita). **Empieza aquí.**
- `fichas/` → una imagen por textura con: forma, movimiento, pasos y paleta. Ábrela al lado mientras pintas.
- `referencia/Hoja_de_pinceladas.png` → los 6 tipos de trazo con los que se pinta todo. Practica 10 minutos antes.
- `paleta/TheLivingCanvas_VanGogh.gpl` → paleta para importar en Krita (ver abajo).
- `preview/` → cómo se ve cada plantilla con las guías encendidas.

## Cómo está construido cada .ora (capas, de arriba a abajo)

1. `AYUDA texto` — oculta por defecto. Un recordatorio de dónde se exporta.
2. `GUIA_pinceladas (sutil)` — líneas **tenues** que te dicen por dónde pasar el pincel. **El punto amarillo marca dónde empieza el trazo.**
3. `FORMAS (lineart tenue)` — la forma del material (bloques de piedra, tejas, tablas, hojas…).
4. `paint_here` — **aquí pintas tú**. Está vacía y transparente.
5. `UNDERPAINT_color (opcional)` — manchas de color ya repartidas con la paleta de ese material. Puedes pintar encima, bajarla de opacidad o ocultarla.
6. `base_flat_color` — color base plano.

## Primera vez en Krita (5 minutos)

1. Abre un `.ora` de `krita/`. Pulsa **W** (Wrap Around Mode): la imagen se repite en los bordes y verás si hay costuras. Casi todas las texturas son **repetibles**.
2. Elige un pincel de cerdas u óleo. Sirven: *Basic-5 Size Opacity*, o cualquiera de la familia *Bristles*. No uses pincel de aerógrafo suave: Van Gogh se ve en el trazo duro y con borde.
3. Tamaño: aprox. 1/12 del lienzo (para 1024 px → 70-90 px). En la barra de pincel activa **Opacidad = Presión** si tienes tableta.
4. Importa la paleta: *Configuración → Administrar recursos → Importar recursos* y elige `TheLivingCanvas_VanGogh.gpl`. Abre el docker *Paletas* (Ajustes → Dockers → Paleta).
5. Selecciona la capa `paint_here` y pinta siguiendo las líneas tenues de la guía.

## Receta de 4 pasadas (sirve para todas las texturas)

1. **Manchas** (grande, rápido): 3-4 zonas de color con un pincel gordo; no busques detalle.
2. **Trazos con dirección**: sigue las líneas tenues. **Un gesto = un trazo**. No retoques ni difumines: el trazo visible es el estilo.
3. **Contraste**: alterna dos o tres tonos de la paleta (oscuro, base, claro) en trazos vecinos.
4. **Acentos**: 5-10 toques del color complementario (azul contra naranja/terracota, violeta contra amarillo). Pocos y pequeños.

Truco de Van Gogh: trazos **cortos y gruesos**, ritmo repetido, y a veces un **contorno oscuro azul** entre formas (útil en piedras, tejas, tablas).

## Reglas del proyecto que hay que mantener

- Los trazos siguen la forma (veta en la madera, hilada en la piedra, hilera en el tejado). Nada de ruido sin intención.
- Las texturas marcadas **TENIDA** (Plaster, Wood_Grain, Fabric) se pintan en **crema/gris CLARO**: Unity las tiñe con el color de cada material.
- No conviertas la Descoloración en gris: conserva diferencias cálido/frío en cada textura.
- Los remolinos fuertes solo en césped (`Grass_Ground`) y, suave, en el yeso. En piedra, madera y metal, mejor ritmo que remolino.

## Antes de exportar

1. Oculta `AYUDA texto`, `GUIA_pinceladas`, y `FORMAS` si no quieres las líneas (normalmente se ocultan).
2. Comprueba con **W** que no se ven costuras. Si se ven: *Imagen → Desplazar imagen (Shift+Ctrl+O)* a la mitad y retoca el centro; luego desplaza de vuelta.
3. Exporta como PNG con el **nombre exacto** `T_<Familia>.png` y el **tamaño exacto** de la plantilla a:
   `Assets/_TheLivingCanvas/Art/Textures/Painted/Museum/`
4. Avisa a Claude para conectarlas al shader TLC/Painterly.

## Orden recomendado

1. `Plaster` — la fachada es lo que más se ve.
2. `Roof_Tiles` — tejado y toldos.
3. `Stone_Blocks` — zócalo, esquinas, marcos, pilares del portón, muro.
4. `Grass_Ground` — suelo del jardín (aquí sí Van Gogh a tope).
5. `Path_Stone` — camino y escalones.
6. `Painted_Boards` — contraventanas, puerta, carteles.
7. `Wood_Grain` — marcos, bancos.
8. `Leaves`, `Bark`, `Petals` — cipreses, arbustos, flores.
9. `Glass`, `Metal`, `Gilded`, `Paper_Canvas`, `Fabric` — ventanas, hierro del portón, latón, toldos y valla, cortinas.

No hay plantilla para `M_Lamp_Glow` (luz emisiva) ni `M_Sign_Letters` (letras de color liso): se quedan como están. `M_Floor_Dark` (chimenea) es muy pequeño y no merece plantilla.

## Cuando termines

Pásame los PNG con el nombre exacto `T_<Familia>.png` (por ejemplo `T_Plaster.png`) y yo los conecto al shader TLC/Painterly y al modelo del exterior en Unity. Puedes pasarme solo algunas: no hace falta tenerlas todas para empezar a verlas.

## Lista de texturas

| Archivo | px | Repetible | m/rep | Materiales del exterior y dónde se ven |
|---|---|---|---|---|
"""


def main():
    if os.path.isdir(OUT):
        shutil.rmtree(OUT)
    for sub in ("krita", "fichas", "preview", "paleta", "referencia"):
        os.makedirs(os.path.join(OUT, sub), exist_ok=True)
    rows = []
    fams = {f[0]: f for f in T.FAMILIES}
    for fam in [fams[n] for n in EXT_ORDER]:
        name, px, tile, mpr, mats, where, stroke, base, tenida, arrows, fn = fam
        rng = np.random.default_rng(zlib.crc32(name.encode()))
        ppm = px / mpr if mpr else px
        g = T.D(px, px, tile)
        fn(g, rng, px, ppm)
        lineL = g.img
        a = lineL.point(lambda v: int((255 - v) * 0.5))
        form = Image.new("RGBA", (px, px), (40, 40, 70, 0))
        form.putalpha(a)
        flow = flow_layer(name, px, tile, ppm, np.random.default_rng(zlib.crc32(name.encode()) + 5))
        under = underpaint(name, px, np.random.default_rng(zlib.crc32(name.encode()) + 9))
        base_img = Image.new("RGBA", (px, px), T.hex2rgb(T.NEUTRAL if tenida else base) + (255,))
        help_l = new_layer(px, px)
        d = ImageDraw.Draw(help_l)
        d.rectangle([0, 0, px - 1, 80], fill=(0, 0, 0, 170))
        d.text((12, 8), "T_%s  |  Exportar: %sT_%s.png" % (name, EXPORT_DIR, name), fill=(255, 255, 255, 255), font=FONT_S)
        d.text((12, 40), "Ocultar esta capa y las guías antes de exportar", fill=(255, 255, 255, 255), font=FONT_S)
        write_ora(os.path.join(OUT, "krita", "VG_%s.ora" % name), (px, px),
                  [("(hidden)AYUDA texto", help_l), ("GUIA_pinceladas (sutil)", flow), ("FORMAS (lineart tenue)", form),
                   ("paint_here", new_layer(px, px)), ("UNDERPAINT_color (opcional)", under), ("base_flat_color", base_img)])
        pv = Image.alpha_composite(Image.alpha_composite(Image.alpha_composite(base_img, under), form), flow)
        pv.convert("RGB").save(os.path.join(OUT, "preview", "VG_%s_guia.png" % name))
        ficha(fam, px, ppm, pv, tile).save(os.path.join(OUT, "fichas", "VG_%s_ficha.png" % name))
        rows.append("| VG_%s.ora → T_%s.png%s | %d | %s | %s | %s |" % (name, name, " (TENIDA)" if tenida else "", px, "sí" if tile else "no", mpr if tile else "-", EXT_USE[name][0] + " — " + EXT_USE[name][1]))
        print("familia:", name)
    cheatsheet(os.path.join(OUT, "referencia", "Hoja_de_pinceladas.png"))
    gpl(os.path.join(OUT, "paleta", "TheLivingCanvas_VanGogh.gpl"))
    with open(os.path.join(OUT, "LEEME.md"), "w", encoding="utf-8", newline="\n") as f:
        f.write(README + "\n".join(rows) + "\n")
    if os.path.exists(ZIP):
        os.remove(ZIP)
    with zipfile.ZipFile(ZIP, "w", zipfile.ZIP_DEFLATED) as z:
        for dp, _, fs in os.walk(OUT):
            for fn_ in sorted(fs):
                full = os.path.join(dp, fn_)
                z.write(full, "TheLivingCanvas_VanGogh_Pack/" + os.path.relpath(full, OUT).replace(os.sep, "/"))
    print("zip:", ZIP, os.path.getsize(ZIP))


if __name__ == "__main__":
    main()
