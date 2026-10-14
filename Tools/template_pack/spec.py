"""Inventario de placeholders de The Living Canvas (fuente unica para Blender, Krita y la documentacion).

Medidas en metros, ejes de UNITY (Y arriba, +Z = frente del objeto), origen en el centro de la base.
Las medidas salen de la escena Studio.unity y de los prefabs reales (volcado hecho el 2026-10-12).
Cada parte: (nombre, tipo, material, tamano, posicion[, rotacion_euler_unity])
  tipo: box | cyl (eje Y) | sph (elipsoide) | cap (capsula, eje Y) | quad (plano vertical, mira a +Z) | quadh (plano horizontal, mira a +Y) | gable (tejado a dos aguas, cumbrera en Z)
  tamano: (x, y, z) del contenedor; para quad (ancho, alto, 0); para cyl el diametro es x (=z).
"""

# ---------------------------------------------------------------- materiales -> color Unity y familia de textura
# material: (color hex actual en Unity, familia de textura que lo sustituira)
MATERIALS = {
    "M_Floor_Wood": ("#8C613D", "Wood_Floor"),
    "M_Gallery_Floor": ("#BDAD99", "Floor_Gallery"),
    "M_Wall_Cream": ("#EDDEC2", "Plaster_Wall"),
    "M_Town_Wall": ("#E0CCB0", "Plaster_Wall"),
    "M_Easel_Wood": ("#6B472E", "Wood_Dark"),
    "M_Gallery_Frame": ("#402B1C", "Wood_Dark"),
    "M_Plant_Stake": ("#8C5421", "Wood_Dark"),
    "M_SellCrate_Wood": ("#9E7342", "Wood_Crate"),
    "M_Shop_Counter": ("#578575", "Wood_Painted"),
    "M_Town_Door": ("#526B82", "Wood_Painted"),
    "M_Accent_Terracotta": ("#CC734C", "Wood_Painted"),
    "M_Town_Awning": ("#526B82", "Fabric_Awning"),
    "M_Gallery_Board": ("#B88552", "Cork_Board"),
    "M_Gallery_Plaque": ("#C7A152", "Brass_Plaque"),
    "M_Canvas_Blank": ("#F5F0E0", "Canvas_Paper"),
    "M_Gallery_Canvas": ("#F2EDE0", "Canvas_Paper"),
    "M_Town_Note": ("#EDE3C7", "Canvas_Paper"),
    "M_Gallery_Card_1": ("#FAD959", "Canvas_Paper"),
    "M_Gallery_Card_2": ("#F28066", "Canvas_Paper"),
    "M_Gallery_Card_3": ("#8CBFE6", "Canvas_Paper"),
    "M_Gallery_Card_4": ("#99D180", "Canvas_Paper"),
    "M_Grass": ("#6B9E4C", "Grass"),
    "M_Town_Grass": ("#667859", "Grass"),
    "M_Garden_Bush": ("#3D7338", "Foliage"),
    "M_Mortar_Stone": ("#9E998F", "Stone"),
    "M_Town_Path": ("#CCB894", "Path_Stone"),
    "M_Town_Plaza": ("#B2A38F", "Path_Stone"),
    "M_Town_Roof": ("#A85E47", "Roof_Tiles"),
    "M_Town_Water": ("#526B82", "Water"),
    "M_Town_Window": ("#596673", "Glass"),
    "M_Town_Lamp": ("#292626", "Metal_Dark"),
    "M_Player_Visor": ("#261F19", "Metal_Dark"),
    "M_Lamp_Bulb": ("#59544C", "Metal_Dark"),
    "M_Town_Lantern": ("#F2CC80", "Glow"),
    "M_Plant_Glow": ("#FAFAF5", "Glow"),
    "M_Npc_Coat": ("#4C1F4C", "Fabric_Clothes"),
    "M_Dealer_Coat": ("#29333D", "Fabric_Clothes"),
    "M_Player_Body": ("#5C859E", "Fabric_Clothes"),
    "M_Npc_Scarf": ("#E6664C", "Fabric_Clothes"),
    "M_Dealer_Cravat": ("#B89E4C", "Fabric_Clothes"),
    "M_Npc_Skin": ("#EDBD99", "Skin"),
    "M_Dealer_Skin": ("#DBAD8C", "Skin"),
    "M_Npc_Hat": ("#D9B24C", "Hat_Felt"),
    "M_Dealer_Cap": ("#4C3829", "Hat_Felt"),
    "M_Plant_Stem": ("#4C8C38", "Plant_Green"),
    "M_Plant_Petal": ("#FAC726", "Plant_Petal"),
    "M_Plant_Center": ("#734C26", "Plant_Center"),
    "M_Plant_Tomato": ("#BF262B", "Plant_Fruit"),
    "M_Plant_Bell": ("#2B459E", "Plant_Bell"),
    "M_PaintingPlot": ("#FFFFFF", None),  # textura generada en runtime con la pintura del jugador
}

# familia -> (tamano px, repetible, direccion de trazo, para que se usa)
FAMILIES = {
    "Wood_Floor": (1024, True, "h", "Suelo del estudio (tablones)."),
    "Floor_Gallery": (1024, True, "h", "Suelo de la galeria (hoy gris calido; puede ser parquet, piedra o baldosa)."),
    "Plaster_Wall": (1024, True, "free", "Paredes del estudio, la galeria y las casas del pueblo."),
    "Wood_Dark": (1024, True, "v", "Caballete, marcos, vallas, bancos, troncos, tutor del tomate."),
    "Wood_Crate": (512, True, "h", "Caja de venta."),
    "Wood_Painted": (512, True, "v", "Madera pintada de color: mostrador, puertas, mesa."),
    "Fabric_Awning": (512, True, "v", "Toldos de los puestos."),
    "Cork_Board": (512, True, "free", "Corcho del tablero de coleccion y del tablon de encargos."),
    "Brass_Plaque": (256, False, "h", "Placas de los cuadros."),
    "Canvas_Paper": (512, True, "free", "Lienzo en blanco, notas y tarjetas (el tinte de las tarjetas lo pone el material)."),
    "Grass": (1024, True, "free", "Cesped del jardin y del pueblo."),
    "Foliage": (512, True, "free", "Arbustos y copas de arboles."),
    "Stone": (512, True, "free", "Piedras, mortero, fuente."),
    "Path_Stone": (1024, True, "free", "Camino y plaza del pueblo."),
    "Roof_Tiles": (512, True, "h", "Tejados."),
    "Water": (512, True, "h", "Agua de la fuente."),
    "Glass": (256, False, "free", "Ventanas de las casas."),
    "Metal_Dark": (256, True, "v", "Farolas, visor del jugador."),
    "Glow": (256, False, "free", "Linternas y brillo de la glowbell (emisivos)."),
    "Fabric_Clothes": (512, True, "free", "Ropa del jugador y de los NPC."),
    "Skin": (256, False, "free", "Piel de los NPC."),
    "Hat_Felt": (256, True, "free", "Sombreros y gorras."),
    "Plant_Green": (512, False, "v", "Tallos y hojas de todos los cultivos."),
    "Plant_Petal": (512, False, "v", "Petalos del girasol."),
    "Plant_Center": (256, False, "free", "Centro del girasol."),
    "Plant_Fruit": (256, False, "free", "Tomates."),
    "Plant_Bell": (256, False, "free", "Campanas de la glowbell."),
}

# ---------------------------------------------------------------- helpers de definicion
def B(n, m, size, pos, rot=(0, 0, 0)): return (n, "box", m, size, pos, rot)
def C(n, m, size, pos, rot=(0, 0, 0)): return (n, "cyl", m, size, pos, rot)
def S(n, m, size, pos, rot=(0, 0, 0)): return (n, "sph", m, size, pos, rot)
def K(n, m, size, pos, rot=(0, 0, 0)): return (n, "cap", m, size, pos, rot)
def Q(n, m, size, pos, rot=(0, 0, 0)): return (n, "quad", m, size, pos, rot)
def QH(n, m, size, pos, rot=(0, 0, 0)): return (n, "quadh", m, size, pos, rot)
def G(n, m, size, pos, rot=(0, 0, 0)): return (n, "gable", m, size, pos, rot)


def house(body, door_side_x, door, wins, roof_h=1.8):
    """Casa: cuerpo + tejado a dos aguas + puerta + ventanas. door/wins: (z, y, tamano) sobre la cara +X."""
    bw, bh, bl = body
    parts = [
        B("Body", "M_Town_Wall", (bw, bh, bl), (0, bh / 2, 0)),
        G("Roof", "M_Town_Roof", (bw + 0.6, roof_h, bl + 0.5), (0, bh, 0)),
        B("Door", "M_Town_Door", (0.1, 2.0, 1.0), (bw / 2 + 0.03, 1.0, door)),
    ]
    for i, (z, y, h) in enumerate(wins):
        parts.append(B(f"Window_{'AB'[i]}", "M_Town_Window", (0.1, h, 0.9), (bw / 2 + 0.03, y, z)))
    return parts


def fence_section():
    return [
        B("Post_L", "M_Easel_Wood", (0.12, 0.8, 0.12), (-1.0, 0.4, 0)),
        B("Post_R", "M_Easel_Wood", (0.12, 0.8, 0.12), (1.0, 0.4, 0)),
        B("Rail_Low", "M_Easel_Wood", (2.0, 0.08, 0.06), (0, 0.35, 0)),
        B("Rail_High", "M_Easel_Wood", (2.0, 0.08, 0.06), (0, 0.70, 0)),
    ]


def sunflower():
    parts = [C("Stem", "M_Plant_Stem", (0.05, 1.2, 0.05), (0, 0.6, 0))]
    for i, y in enumerate((0.45, 0.8)):
        s = 1 if i == 0 else -1
        parts.append(S(f"Leaf_{i}", "M_Plant_Stem", (0.09, 0.02, 0.26), (0, y, s * 0.14), (-20 * s, 0, 0)))
    parts += [
        C("Head_Center", "M_Plant_Center", (0.22, 0.04, 0.22), (0, 1.25, 0.02), (90, 0, 0)),
        C("Head_Back", "M_Plant_Stem", (0.24, 0.04, 0.24), (0, 1.25, -0.02), (90, 0, 0)),
    ]
    import math
    for i in range(16):
        a = math.radians(i * 22.5)
        parts.append(S(f"Petal_{i}", "M_Plant_Petal", (0.06, 0.18, 0.01),
                       (math.sin(a) * 0.20, 1.25 + math.cos(a) * 0.20, 0.03), (0, 0, -i * 22.5)))
    return parts


def tomato():
    parts = [
        C("Stake", "M_Plant_Stake", (0.03, 1.1, 0.03), (0.16, 0.55, 0.06)),
        C("Stem", "M_Plant_Stem", (0.03, 0.9, 0.03), (0, 0.45, 0)),
    ]
    for i, y in enumerate((0.20, 0.35, 0.50, 0.62, 0.74, 0.84)):
        s = 1 if i % 2 == 0 else -1
        parts.append(S(f"Leaf_{i}", "M_Plant_Stem", (0.08, 0.01, 0.20), (0, y, s * 0.11), (-15 * s, 0, 0)))
    for i, (x, y, z) in enumerate(((0.07, 0.28, 0.05), (-0.07, 0.42, -0.04), (0.08, 0.55, -0.05), (-0.06, 0.66, 0.06), (0.05, 0.76, 0.07))):
        parts.append(S(f"Fruit_{i}", "M_Plant_Tomato", (0.13, 0.12, 0.13), (x, y, z)))
        parts.append(S(f"Calyx_{i}", "M_Plant_Stem", (0.07, 0.02, 0.07), (x, y + 0.06, z)))
    return parts


def glowbell():
    import math
    parts = [C("Stem", "M_Plant_Stem", (0.03, 0.86, 0.03), (0, 0.43, 0))]
    for i, (y, s) in enumerate(((0.2, 1), (0.4, -1))):
        parts.append(S(f"Leaf_{i}", "M_Plant_Stem", (0.08, 0.01, 0.22), (0, y, s * 0.12), (-15 * s, 0, 0)))
    for i in range(4):
        a = math.radians(i * 90 + 20)
        bx, bz = math.sin(a) * 0.16, math.cos(a) * 0.16
        parts.append(C(f"Branch_{i}", "M_Plant_Stem", (0.02, 0.30, 0.02), (bx / 2, 0.86 - 0.02, bz / 2), (math.cos(a) * 55, 0, -math.sin(a) * 55)))
        parts.append(S(f"Bell_{i}_Body", "M_Plant_Bell", (0.09, 0.12, 0.09), (bx, 0.74, bz)))
        parts.append(S(f"Bell_{i}_Rim", "M_Plant_Bell", (0.13, 0.03, 0.13), (bx, 0.68, bz)))
        parts.append(S(f"Bell_{i}_Glow", "M_Plant_Glow", (0.05, 0.05, 0.05), (bx, 0.64, bz)))
    return parts


def frame_wall(frame_w=1.7, frame_h=1.3, plaque=True):
    parts = [
        B("Backing", "M_Gallery_Canvas", (1.5, 1.2, 0.04), (0, 1.6, 0.02)),
        B("Border_Top", "M_Gallery_Frame", (1.7, 0.10, 0.08), (0, 2.25, 0.04)),
        B("Border_Bottom", "M_Gallery_Frame", (1.7, 0.10, 0.08), (0, 0.95, 0.04)),
        B("Border_Left", "M_Gallery_Frame", (0.10, 1.2, 0.08), (-0.80, 1.6, 0.04)),
        B("Border_Right", "M_Gallery_Frame", (0.10, 1.2, 0.08), (0.80, 1.6, 0.04)),
        Q("Picture", "M_Gallery_Canvas", (1.4, 1.1, 0), (0, 1.6, 0.05)),
    ]
    if plaque:
        parts.append(B("Plaque", "M_Gallery_Plaque", (1.2, 0.30, 0.04), (0, 0.67, 0.02)))
    return parts


# ---------------------------------------------------------------- inventario por archivo .blend
# asset: (nombre, categoria, donde esta en Unity, partes, notas)
BLEND_FILES = {
    "TLC_Characters": [
        ("Player", "Personaje", "Prefabs/Player/Player.prefab",
         [K("Body", "M_Player_Body", (0.7, 1.8, 0.7), (0, 0.9, 0)), B("Visor", "M_Player_Visor", (0.45, 0.14, 0.15), (0, 1.5, 0.3))],
         "Capsula de 1,8 m. En Unity el collider/controlador es independiente de la malla; no cambies la altura sin avisar."),
        ("Npc_OttilieVane", "Personaje", "StudioSceneBuilder (galeria)",
         [K("Coat", "M_Npc_Coat", (0.55, 1.2, 0.55), (0, 0.6, 0)), C("Scarf", "M_Npc_Scarf", (0.34, 0.08, 0.34), (0, 1.27, 0)),
          S("Head", "M_Npc_Skin", (0.26, 0.26, 0.26), (0, 1.43, 0)), C("Hat_Brim", "M_Npc_Hat", (0.5, 0.02, 0.5), (0, 1.55, 0)),
          C("Hat_Crown", "M_Npc_Hat", (0.2, 0.2, 0.2), (0, 1.65, 0))],
         "Coleccionista excentrica."),
        ("Npc_ArtDealer", "Personaje", "StudioSceneBuilder (pueblo)",
         [K("Coat", "M_Dealer_Coat", (0.55, 1.2, 0.55), (0, 0.6, 0)), B("Cravat", "M_Dealer_Cravat", (0.1, 0.18, 0.1), (0, 1.2, 0.2)),
          S("Head", "M_Dealer_Skin", (0.26, 0.26, 0.26), (0, 1.43, 0)), S("Cap", "M_Dealer_Cap", (0.41, 0.14, 0.41), (0, 1.53, 0)),
          B("Cap_Visor", "M_Dealer_Cap", (0.24, 0.02, 0.24), (0, 1.5, 0.2))],
         "Marchante de arte."),
    ],
    "TLC_Props": [
        ("Easel", "Prop", "Prefabs/Canvas/Easel.prefab",
         [B("Leg_Left", "M_Easel_Wood", (0.07, 1.6, 0.07), (-0.45, 0.8, 0.05), (8, 0, -3)), B("Leg_Right", "M_Easel_Wood", (0.07, 1.6, 0.07), (0.45, 0.8, 0.05), (8, 0, 3)),
          B("Leg_Back", "M_Easel_Wood", (0.07, 1.45, 0.07), (0, 0.72, -0.4), (-18, 0, 0)), B("Ledge", "M_Easel_Wood", (1.07, 0.04, 0.30), (0, 0.9, 0.12)),
          B("Board_Frame", "M_Easel_Wood", (1.05, 0.86, 0.05), (0, 1.32, 0.0)), Q("Canvas", "M_Canvas_Blank", (0.98, 0.79, 0), (0, 1.32, 0.03))],
         "El lienzo (Canvas) recibe la pintura del jugador en runtime: mantener un quad 0,98 x 0,79 con UV 0-1 completo."),
        ("Table", "Prop", "StudioSceneBuilder (estudio)", [B("Top", "M_Accent_Terracotta", (2.0, 0.8, 1.0), (0, 0.4, 0))], "Mesa de pruebas (volumen macizo)."),
        ("TestLamp", "Prop", "StudioSceneBuilder (estudio)",
         [C("Stand", "M_Player_Visor", (0.08, 0.4, 0.08), (0, 0.2, 0)), S("Bulb", "M_Lamp_Bulb", (0.22, 0.22, 0.22), (0, 0.48, 0))], "Lampara de sobremesa; el foco es una Light aparte."),
        ("SellCrate", "Prop", "StudioSceneBuilder (estudio)",
         [B("Base", "M_SellCrate_Wood", (0.9, 0.1, 0.7), (0, 0.05, 0)), B("Side_Front", "M_SellCrate_Wood", (0.9, 0.5, 0.04), (0, 0.30, -0.33)),
          B("Side_Back", "M_SellCrate_Wood", (0.9, 0.5, 0.04), (0, 0.30, 0.33)), B("Side_Left", "M_SellCrate_Wood", (0.04, 0.5, 0.62), (-0.43, 0.30, 0)),
          B("Side_Right", "M_SellCrate_Wood", (0.04, 0.5, 0.62), (0.43, 0.30, 0))], "Caja donde se vende la cosecha."),
        ("ShopStall", "Prop", "StudioSceneBuilder (estudio)",
         [B("Counter", "M_Shop_Counter", (1.8, 0.9, 0.6), (0, 0.45, 0)), B("Post_Left", "M_Easel_Wood", (0.08, 2.5, 0.08), (-0.85, 1.25, 0.25)),
          B("Post_Right", "M_Easel_Wood", (0.08, 2.5, 0.08), (0.85, 1.25, 0.25)), B("Awning", "M_Accent_Terracotta", (2.0, 0.27, 0.9), (0, 2.45, 0.05), (-8, 0, 0))],
         "Tienda de pigmentos y mejoras."),
        ("Mortar", "Prop", "StudioSceneBuilder (estudio)",
         [C("Stump", "M_Easel_Wood", (0.6, 0.6, 0.6), (0, 0.3, 0)), S("Bowl", "M_Mortar_Stone", (0.36, 0.2, 0.36), (0, 0.66, 0)),
          C("Pestle", "M_Mortar_Stone", (0.05, 0.27, 0.05), (0.08, 0.8, 0), (0, 0, -25))], "Mortero donde se muele la cosecha para obtener pigmento."),
        ("PaintingPlot", "Prop", "Prefabs/Crops/PaintingPlot.prefab",
         [B("Frame", "M_Easel_Wood", (1.06, 0.03, 0.86), (0, 0.015, 0)), QH("Painting", "M_PaintingPlot", (1.0, 0.8, 0), (0, 0.032, 0))],
         "Parcela: la pintura tumbada. 'Painting' recibe la pintura del jugador (UV 0-1 completo, 1,0 x 0,8 m)."),
        ("ArtDealerStall", "Prop", "StudioSceneBuilder (pueblo)",
         [B("Counter", "M_Easel_Wood", (1.2, 0.9, 1.2), (0, 0.45, 0), (0, 45, 0)), B("Post_Left", "M_Easel_Wood", (0.11, 2.5, 0.11), (0.6, 1.25, 0.6)),
          B("Post_Right", "M_Easel_Wood", (0.11, 2.5, 0.11), (-0.6, 1.25, -0.6)), B("Awning", "M_Town_Awning", (1.45, 0.27, 1.45), (0, 2.45, 0), (0, 45, 0)),
          B("Frame_1", "M_Gallery_Frame", (0.35, 0.30, 0.05), (0.2, 1.05, 0.25)), B("Canvas_1", "M_Gallery_Canvas", (0.28, 0.23, 0.06), (0.2, 1.05, 0.25))],
         "Puesto del marchante."),
        ("CommissionBoard", "Prop", "StudioSceneBuilder (pueblo)",
         [B("Post_Left", "M_Easel_Wood", (0.10, 2.2, 0.10), (0, 1.1, -0.9)), B("Post_Right", "M_Easel_Wood", (0.10, 2.2, 0.10), (0, 1.1, 0.9)),
          B("Cork", "M_Gallery_Board", (0.06, 1.1, 1.7), (0.02, 1.4, 0)), B("Roof", "M_Town_Roof", (0.6, 0.17, 2.2), (0.0, 2.3, 0), (0, 0, 12)),
          B("Note_1", "M_Town_Note", (0.01, 0.53, 0.42), (0.06, 1.55, 0.5)), B("Note_2", "M_Town_Note", (0.01, 0.53, 0.41), (0.06, 1.30, -0.1)),
          B("Note_3", "M_Town_Note", (0.01, 0.54, 0.44), (0.06, 1.60, -0.55)), B("Note_4", "M_Town_Note", (0.01, 0.54, 0.43), (0.06, 1.68, 0.1))],
         "Tablon de encargos."),
        ("Bench", "Prop", "StudioSceneBuilder (pueblo, x3)",
         [B("Seat", "M_Easel_Wood", (1.6, 0.10, 0.5), (0, 0.45, 0)), B("Back", "M_Easel_Wood", (1.6, 0.5, 0.06), (0, 0.80, -0.22)),
          B("Leg_L", "M_Easel_Wood", (0.1, 0.4, 0.4), (-0.7, 0.2, 0)), B("Leg_R", "M_Easel_Wood", (0.1, 0.4, 0.4), (0.7, 0.2, 0))], "Banco del pueblo."),
        ("Lamp_Post", "Prop", "StudioSceneBuilder (pueblo, x4)",
         [C("Post", "M_Town_Lamp", (0.10, 2.8, 0.10), (0, 1.4, 0)), B("Lantern", "M_Town_Lantern", (0.3, 0.4, 0.3), (0, 3.0, 0))], "Farola."),
        ("Fence_Section", "Prop", "StudioSceneBuilder (jardin)", fence_section(), "Tramo de valla de 2 m (el jardin usa 18 tramos)."),
        ("GardenGate", "Prop", "StudioSceneBuilder (jardin)",
         [B("Post_L", "M_Easel_Wood", (0.18, 1.1, 0.18), (0, 0.55, -1.0)), B("Post_R", "M_Easel_Wood", (0.18, 1.1, 0.18), (0, 0.55, 1.0)),
          B("Rail_1", "M_Easel_Wood", (0.06, 0.10, 1.8), (0, 0.30, 0)), B("Rail_2", "M_Easel_Wood", (0.06, 0.10, 1.8), (0, 0.60, 0)),
          B("Rail_3", "M_Easel_Wood", (0.06, 0.10, 1.8), (0, 0.90, 0)), B("Brace", "M_Easel_Wood", (0.06, 0.06, 2.0), (0, 0.6, 0), (-27, 0, 0))],
         "Puerta del jardin (abre con el nivel). La hoja gira sobre Post_L: mantener el pivote."),
        ("Bush", "Prop", "StudioSceneBuilder (jardin, x2)", [S("Body", "M_Garden_Bush", (1.3, 0.9, 1.3), (0, 0.4, 0))], "Arbusto."),
        ("Stone", "Prop", "StudioSceneBuilder (jardin, x2)", [S("Body", "M_Mortar_Stone", (0.6, 0.3, 0.6), (0, 0.1, 0))], "Piedra decorativa."),
        ("Tree", "Prop", "StudioSceneBuilder (pueblo, x6, con escala 0,9-1,2)",
         [C("Trunk", "M_Easel_Wood", (0.35, 2.2, 0.35), (0, 1.1, 0)), S("Crown_A", "M_Garden_Bush", (2.4, 2.4, 2.4), (0, 2.8, 0)),
          S("Crown_B", "M_Garden_Bush", (1.6, 1.6, 1.6), (0.5, 3.5, 0.2))], "Arbol del pueblo."),
    ],
    "TLC_Crops": [
        ("Sunflower", "Cultivo", "Prefabs/Crops/Sunflower.prefab", sunflower(),
         "Mostrado ya crecido. En Unity el script SunflowerPlant crece/anima cada parte por separado (Stem, Leaf, Head, Petal): conserva las partes separadas y sus pivotes. Los colores de pintura (zonas) se aplican por material."),
        ("Tomato", "Cultivo", "Prefabs/Crops/Tomato.prefab", tomato(),
         "Partes animadas por TomatoPlant: Stem, Leaf, Fruit, Calyx, Stake. Conserva partes y pivotes."),
        ("Glowbell", "Cultivo", "Prefabs/Crops/Glowbell.prefab", glowbell(),
         "Partes animadas por GlowbellPlant: Stem, Leaf, Branch, Bell (Body/Rim/Glow). La luz es un GameObject aparte."),
    ],
    "TLC_Architecture": [
        ("Studio_Shell", "Arquitectura", "StudioSceneBuilder (estudio)",
         [B("Floor", "M_Floor_Wood", (12, 0.2, 12), (0, -0.1, 0)), B("Wall_Back_Left", "M_Wall_Cream", (5, 3, 0.2), (-3.5, 1.5, 6)),
          B("Wall_Back_Right", "M_Wall_Cream", (5, 3, 0.2), (3.5, 1.5, 6)), B("Wall_Back_Lintel", "M_Wall_Cream", (2, 0.6, 0.2), (0, 2.7, 6)),
          B("Wall_Left", "M_Wall_Cream", (0.2, 3, 12), (-6, 1.5, 0))],
         "Estudio de 12x12 m: abierto por el frente y el lado derecho (puerta al jardin en x=6, z=0). Vano de 2 m hacia la galeria en el muro del fondo."),
        ("Gallery_Shell", "Arquitectura", "StudioSceneBuilder (galeria)",
         [B("Floor", "M_Gallery_Floor", (12, 0.2, 8), (0, -0.1, 0)), B("Wall_Left", "M_Wall_Cream", (0.2, 3, 8), (-6, 1.5, 0)),
          B("Wall_Right", "M_Wall_Cream", (0.2, 3, 8), (6, 1.5, 0)), B("Wall_Back", "M_Wall_Cream", (12.2, 3, 0.2), (0, 1.5, 4))],
         "Sala de 12x8 m detras del estudio."),
        ("Gallery_Frame", "Arquitectura", "StudioSceneBuilder (galeria, x6)", frame_wall(),
         "Marco para colgar una pintura. 'Picture' (1,4 x 1,1 m, UV 0-1 completo) recibe la pintura del jugador. Origen en la pared, el marco sale hacia +Z."),
        ("CollectionBoard", "Arquitectura", "StudioSceneBuilder (galeria)",
         [B("Cork", "M_Gallery_Board", (2.0, 1.3, 0.04), (0, 1.6, 0.02)), B("Border_Top", "M_Gallery_Frame", (2.2, 0.10, 0.08), (0, 2.3, 0.04)),
          B("Border_Bottom", "M_Gallery_Frame", (2.2, 0.10, 0.08), (0, 0.9, 0.04)), B("Border_Left", "M_Gallery_Frame", (0.10, 1.3, 0.08), (-1.05, 1.6, 0.04)),
          B("Border_Right", "M_Gallery_Frame", (0.10, 1.3, 0.08), (1.05, 1.6, 0.04)),
          B("Card_1", "M_Gallery_Card_1", (0.34, 0.43, 0.01), (-0.8, 2.0, 0.045)), B("Card_2", "M_Gallery_Card_2", (0.33, 0.42, 0.01), (0.8, 2.02, 0.045)),
          B("Card_3", "M_Gallery_Card_3", (0.33, 0.42, 0.01), (-0.85, 1.2, 0.045)), B("Card_4", "M_Gallery_Card_4", (0.35, 0.43, 0.01), (0.85, 1.22, 0.045))],
         "Tablero de coleccion. Las tarjetas se tiñen por codigo segun lo descubierto."),
        ("Garden_Lawn", "Arquitectura", "StudioSceneBuilder (jardin)", [B("Lawn", "M_Grass", (12, 0.2, 12), (0, -0.1, 0))], "Jardin de 12x12 m junto al estudio."),
        ("Town_Ground", "Arquitectura", "StudioSceneBuilder (pueblo)",
         [B("Ground", "M_Town_Grass", (30, 0.2, 20), (0, -0.1, 0)), B("Path", "M_Town_Path", (3, 0.2, 5), (0, -0.09, 7.5)), B("Plaza", "M_Town_Plaza", (10, 0.2, 10), (0, -0.08, 0))],
         "Suelo del pueblo, camino de entrada (+Z) y plaza."),
        ("Fountain", "Arquitectura", "StudioSceneBuilder (pueblo)",
         [C("Basin", "M_Mortar_Stone", (2.6, 0.6, 2.6), (0, 0.3, 0)), C("Water", "M_Town_Water", (2.2, 0.04, 2.2), (0, 0.61, 0)),
          C("Column", "M_Mortar_Stone", (0.4, 1.8, 0.4), (0, 0.9, 0)), C("Bowl", "M_Mortar_Stone", (0.9, 0.16, 0.9), (0, 1.75, 0))], "Fuente de la plaza."),
        ("House_A", "Arquitectura", "StudioSceneBuilder (pueblo, 'House_West_A')", house((4.0, 3.2, 5.0), 1, 1.2, [(1.4, 1.7, 0.9), (1.2, 2.4, 0.7)]), "Casa oeste A."),
        ("House_B", "Arquitectura", "StudioSceneBuilder (pueblo, 'House_West_B')", house((3.6, 3.8, 4.5), 1, 1.0, [(-1.2, 1.7, 0.9)], 1.7), "Casa oeste B."),
        ("House_South", "Arquitectura", "StudioSceneBuilder (pueblo)", house((4.0, 3.4, 5.5), 1, -1.3, [(0.8, 1.7, 0.9), (-1.3, 2.6, 0.7)]), "Casa sur (en Unity esta girada 90 grados)."),
        ("House_East", "Arquitectura", "StudioSceneBuilder (pueblo)", house((4.2, 4.0, 5.0), -1, 1.1, [(-1.4, 1.7, 0.9), (1.1, 3.2, 0.7)], 1.9), "Casa este."),
    ],
}

# ---------------------------------------------------------------- 2D no-material
GAMEPLAY_MASKS = {
    "Sunflower_Zones": {"R": "Petalos", "G": "Tallo y hojas", "B": "Centro"},
    "Tomato_Zones": {"R": "Tomates", "G": "Tallo y hojas", "B": "Tutor"},
    "Glowbell_Zones": {"R": "Campanas", "G": "Tallo y ramas", "B": "Esferas de luz"},
}
ICONS = ["Icon_Sunflower", "Icon_Tomato", "Icon_Glowbell"]
