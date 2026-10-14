# Inventario de placeholders — The Living Canvas

Generado el 2026-10-12 a partir de `Studio.unity` y los prefabs. Medidas en metros (Unity: X ancho, Y alto, Z fondo).

## 3D (Blender)

### `blender/TLC_Characters.blend`

| Asset | Tamaño aprox. (X·Y·Z) | Dónde está en Unity | Materiales | Notas |
|---|---|---|---|---|
| **Player** | 0.7 · 1.8 · 0.72 | Prefabs/Player/Player.prefab | M_Player_Body, M_Player_Visor | Capsula de 1,8 m. En Unity el collider/controlador es independiente de la malla; no cambies la altura sin avisar. |
| **Npc_OttilieVane** | 0.55 · 1.75 · 0.55 | StudioSceneBuilder (galeria) | M_Npc_Coat, M_Npc_Hat, M_Npc_Scarf, M_Npc_Skin | Coleccionista excentrica. |
| **Npc_ArtDealer** | 0.55 · 1.6 · 0.59 | StudioSceneBuilder (pueblo) | M_Dealer_Cap, M_Dealer_Coat, M_Dealer_Cravat, M_Dealer_Skin | Marchante de arte. |

### `blender/TLC_Props.blend`

| Asset | Tamaño aprox. (X·Y·Z) | Dónde está en Unity | Materiales | Notas |
|---|---|---|---|---|
| **Easel** | 2.5 · 1.75 · 1.98 | Prefabs/Canvas/Easel.prefab | M_Canvas_Blank, M_Easel_Wood | El lienzo (Canvas) recibe la pintura del jugador en runtime: mantener un quad 0,98 x 0,79 con UV 0-1 completo. |
| **Table** | 2.0 · 0.8 · 1.0 | StudioSceneBuilder (estudio) | M_Accent_Terracotta | Mesa de pruebas (volumen macizo). |
| **TestLamp** | 0.22 · 0.59 · 0.22 | StudioSceneBuilder (estudio) | M_Lamp_Bulb, M_Player_Visor | Lampara de sobremesa; el foco es una Light aparte. |
| **SellCrate** | 0.9 · 0.55 · 0.7 | StudioSceneBuilder (estudio) | M_SellCrate_Wood | Caja donde se vende la cosecha. |
| **ShopStall** | 2.0 · 3.45 · 2.0 | StudioSceneBuilder (estudio) | M_Accent_Terracotta, M_Easel_Wood, M_Shop_Counter | Tienda de pigmentos y mejoras. |
| **Mortar** | 0.6 · 0.94 · 0.6 | StudioSceneBuilder (estudio) | M_Easel_Wood, M_Mortar_Stone | Mortero donde se muele la cosecha para obtener pigmento. |
| **PaintingPlot** | 1.06 · 0.03 · 0.86 | Prefabs/Crops/PaintingPlot.prefab | M_Easel_Wood, M_PaintingPlot | Parcela: la pintura tumbada. 'Painting' recibe la pintura del jugador (UV 0-1 completo, 1,0 x 0,8 m). |
| **ArtDealerStall** | 1.45 · 3.33 · 1.45 | StudioSceneBuilder (pueblo) | M_Easel_Wood, M_Gallery_Canvas, M_Gallery_Frame, M_Town_Awning | Puesto del marchante. |
| **CommissionBoard** | 2.2 · 3.4 · 2.2 | StudioSceneBuilder (pueblo) | M_Easel_Wood, M_Gallery_Board, M_Town_Note, M_Town_Roof | Tablon de encargos. |
| **Bench** | 1.6 · 1.05 · 0.5 | StudioSceneBuilder (pueblo, x3) | M_Easel_Wood | Banco del pueblo. |
| **Lamp_Post** | 0.3 · 3.2 · 0.3 | StudioSceneBuilder (pueblo, x4) | M_Town_Lamp, M_Town_Lantern | Farola. |
| **Fence_Section** | 2.12 · 0.8 · 0.12 | StudioSceneBuilder (jardin) | M_Easel_Wood | Tramo de valla de 2 m (el jardin usa 18 tramos). |
| **GardenGate** | 2.0 · 2.0 · 2.18 | StudioSceneBuilder (jardin) | M_Easel_Wood | Puerta del jardin (abre con el nivel). La hoja gira sobre Post_L: mantener el pivote. |
| **Bush** | 1.3 · 0.9 · 1.3 | StudioSceneBuilder (jardin, x2) | M_Garden_Bush | Arbusto. |
| **Stone** | 0.6 · 0.3 · 0.6 | StudioSceneBuilder (jardin, x2) | M_Mortar_Stone | Piedra decorativa. |
| **Tree** | 2.5 · 4.3 · 2.4 | StudioSceneBuilder (pueblo, x6, con escala 0,9-1,2) | M_Easel_Wood, M_Garden_Bush | Arbol del pueblo. |

### `blender/TLC_Crops.blend`

| Asset | Tamaño aprox. (X·Y·Z) | Dónde está en Unity | Materiales | Notas |
|---|---|---|---|---|
| **Sunflower** | 0.58 · 1.54 · 0.54 | Prefabs/Crops/Sunflower.prefab | M_Plant_Center, M_Plant_Petal, M_Plant_Stem | Mostrado ya crecido. En Unity el script SunflowerPlant crece/anima cada parte por separado (Stem, Leaf, Head, Petal): conserva las partes separadas y sus pivotes. Los colores de pintura (zonas) se aplican por material. |
| **Tomato** | 0.31 · 1.1 · 0.42 | Prefabs/Crops/Tomato.prefab | M_Plant_Stake, M_Plant_Stem, M_Plant_Tomato | Partes animadas por TomatoPlant: Stem, Leaf, Fruit, Calyx, Stake. Conserva partes y pivotes. |
| **Glowbell** | 0.45 · 0.99 · 0.46 | Prefabs/Crops/Glowbell.prefab | M_Plant_Bell, M_Plant_Glow, M_Plant_Stem | Partes animadas por GlowbellPlant: Stem, Leaf, Branch, Bell (Body/Rim/Glow). La luz es un GameObject aparte. |

### `blender/TLC_Architecture.blend`

| Asset | Tamaño aprox. (X·Y·Z) | Dónde está en Unity | Materiales | Notas |
|---|---|---|---|---|
| **Studio_Shell** | 12.1 · 3.2 · 12.1 | StudioSceneBuilder (estudio) | M_Floor_Wood, M_Wall_Cream | Estudio de 12x12 m: abierto por el frente y el lado derecho (puerta al jardin en x=6, z=0). Vano de 2 m hacia la galeria en el muro del fondo. |
| **Gallery_Shell** | 12.2 · 3.2 · 8.1 | StudioSceneBuilder (galeria) | M_Gallery_Floor, M_Wall_Cream | Sala de 12x8 m detras del estudio. |
| **Gallery_Frame** | 1.7 · 1.78 · 0.08 | StudioSceneBuilder (galeria, x6) | M_Gallery_Canvas, M_Gallery_Frame, M_Gallery_Plaque | Marco para colgar una pintura. 'Picture' (1,4 x 1,1 m, UV 0-1 completo) recibe la pintura del jugador. Origen en la pared, el marco sale hacia +Z. |
| **CollectionBoard** | 2.2 · 1.5 · 0.08 | StudioSceneBuilder (galeria) | M_Gallery_Board, M_Gallery_Card_1, M_Gallery_Card_2, M_Gallery_Card_3, M_Gallery_Card_4, M_Gallery_Frame | Tablero de coleccion. Las tarjetas se tiñen por codigo segun lo descubierto. |
| **Garden_Lawn** | 12.0 · 0.2 · 12.0 | StudioSceneBuilder (jardin) | M_Grass | Jardin de 12x12 m junto al estudio. |
| **Town_Ground** | 30.0 · 0.22 · 20.0 | StudioSceneBuilder (pueblo) | M_Town_Grass, M_Town_Path, M_Town_Plaza | Suelo del pueblo, camino de entrada (+Z) y plaza. |
| **Fountain** | 2.6 · 1.83 · 2.6 | StudioSceneBuilder (pueblo) | M_Mortar_Stone, M_Town_Water | Fuente de la plaza. |
| **House_A** | 4.6 · 4.1 · 5.5 | StudioSceneBuilder (pueblo, 'House_West_A') | M_Town_Door, M_Town_Roof, M_Town_Wall, M_Town_Window | Casa oeste A. |
| **House_B** | 4.2 · 4.65 · 5.0 | StudioSceneBuilder (pueblo, 'House_West_B') | M_Town_Door, M_Town_Roof, M_Town_Wall, M_Town_Window | Casa oeste B. |
| **House_South** | 4.6 · 4.3 · 6.0 | StudioSceneBuilder (pueblo) | M_Town_Door, M_Town_Roof, M_Town_Wall, M_Town_Window | Casa sur (en Unity esta girada 90 grados). |
| **House_East** | 4.8 · 4.95 · 5.5 | StudioSceneBuilder (pueblo) | M_Town_Door, M_Town_Roof, M_Town_Wall, M_Town_Window | Casa este. |

## 2D — texturas de material (Krita)

Hoy **todos los materiales de Unity son colores planos**. Cada familia de textura sustituirá a uno o varios materiales.

| Plantilla (`krita/textures/`) | Tamaño | ¿Repetible? | Materiales que cubre | Se ve en |
|---|---|---|---|---|
| `T_Wood_Floor_TEMPLATE.ora` | 1024×1024 | sí | M_Floor_Wood | Studio_Shell — Suelo del estudio (tablones). |
| `T_Floor_Gallery_TEMPLATE.ora` | 1024×1024 | sí | M_Gallery_Floor | Gallery_Shell — Suelo de la galeria (hoy gris calido; puede ser parquet, piedra o baldosa). |
| `T_Plaster_Wall_TEMPLATE.ora` | 1024×1024 | sí | M_Wall_Cream, M_Town_Wall | Gallery_Shell, House_A, House_B, House_East, House_South, Studio_Shell — Paredes del estudio, la galeria y las casas del pueblo. |
| `T_Wood_Dark_TEMPLATE.ora` | 1024×1024 | sí | M_Easel_Wood, M_Gallery_Frame, M_Plant_Stake | ArtDealerStall, Bench, CollectionBoard, CommissionBoard, Easel, Fence_Section, Gallery_Frame, GardenGate, Mortar, PaintingPlot, ShopStall, Tomato, Tree — Caballete, marcos, vallas, bancos, troncos, tutor del tomate. |
| `T_Wood_Crate_TEMPLATE.ora` | 512×512 | sí | M_SellCrate_Wood | SellCrate — Caja de venta. |
| `T_Wood_Painted_TEMPLATE.ora` | 512×512 | sí | M_Shop_Counter, M_Town_Door, M_Accent_Terracotta | House_A, House_B, House_East, House_South, ShopStall, Table — Madera pintada de color: mostrador, puertas, mesa. |
| `T_Fabric_Awning_TEMPLATE.ora` | 512×512 | sí | M_Town_Awning | ArtDealerStall — Toldos de los puestos. |
| `T_Cork_Board_TEMPLATE.ora` | 512×512 | sí | M_Gallery_Board | CollectionBoard, CommissionBoard — Corcho del tablero de coleccion y del tablon de encargos. |
| `T_Brass_Plaque_TEMPLATE.ora` | 256×256 | no | M_Gallery_Plaque | Gallery_Frame — Placas de los cuadros. |
| `T_Canvas_Paper_TEMPLATE.ora` | 512×512 | sí | M_Canvas_Blank, M_Gallery_Canvas, M_Town_Note, M_Gallery_Card_1, M_Gallery_Card_2, M_Gallery_Card_3, M_Gallery_Card_4 | ArtDealerStall, CollectionBoard, CommissionBoard, Easel, Gallery_Frame — Lienzo en blanco, notas y tarjetas (el tinte de las tarjetas lo pone el material). |
| `T_Grass_TEMPLATE.ora` | 1024×1024 | sí | M_Grass, M_Town_Grass | Garden_Lawn, Town_Ground — Cesped del jardin y del pueblo. |
| `T_Foliage_TEMPLATE.ora` | 512×512 | sí | M_Garden_Bush | Bush, Tree — Arbustos y copas de arboles. |
| `T_Stone_TEMPLATE.ora` | 512×512 | sí | M_Mortar_Stone | Fountain, Mortar, Stone — Piedras, mortero, fuente. |
| `T_Path_Stone_TEMPLATE.ora` | 1024×1024 | sí | M_Town_Path, M_Town_Plaza | Town_Ground — Camino y plaza del pueblo. |
| `T_Roof_Tiles_TEMPLATE.ora` | 512×512 | sí | M_Town_Roof | CommissionBoard, House_A, House_B, House_East, House_South — Tejados. |
| `T_Water_TEMPLATE.ora` | 512×512 | sí | M_Town_Water | Fountain — Agua de la fuente. |
| `T_Glass_TEMPLATE.ora` | 256×256 | no | M_Town_Window | House_A, House_B, House_East, House_South — Ventanas de las casas. |
| `T_Metal_Dark_TEMPLATE.ora` | 256×256 | sí | M_Town_Lamp, M_Player_Visor, M_Lamp_Bulb | Lamp_Post, Player, TestLamp — Farolas, visor del jugador. |
| `T_Glow_TEMPLATE.ora` | 256×256 | no | M_Town_Lantern, M_Plant_Glow | Glowbell, Lamp_Post — Linternas y brillo de la glowbell (emisivos). |
| `T_Fabric_Clothes_TEMPLATE.ora` | 512×512 | sí | M_Npc_Coat, M_Dealer_Coat, M_Player_Body, M_Npc_Scarf, M_Dealer_Cravat | Npc_ArtDealer, Npc_OttilieVane, Player — Ropa del jugador y de los NPC. |
| `T_Skin_TEMPLATE.ora` | 256×256 | no | M_Npc_Skin, M_Dealer_Skin | Npc_ArtDealer, Npc_OttilieVane — Piel de los NPC. |
| `T_Hat_Felt_TEMPLATE.ora` | 256×256 | sí | M_Npc_Hat, M_Dealer_Cap | Npc_ArtDealer, Npc_OttilieVane — Sombreros y gorras. |
| `T_Plant_Green_TEMPLATE.ora` | 512×512 | no | M_Plant_Stem | Glowbell, Sunflower, Tomato — Tallos y hojas de todos los cultivos. |
| `T_Plant_Petal_TEMPLATE.ora` | 512×512 | no | M_Plant_Petal | Sunflower — Petalos del girasol. |
| `T_Plant_Center_TEMPLATE.ora` | 256×256 | no | M_Plant_Center | Sunflower — Centro del girasol. |
| `T_Plant_Fruit_TEMPLATE.ora` | 256×256 | no | M_Plant_Tomato | Tomato — Tomates. |
| `T_Plant_Bell_TEMPLATE.ora` | 256×256 | no | M_Plant_Bell | Glowbell — Campanas de la glowbell. |

**No tienen plantilla (se generan en el juego):** `M_PaintingPlot`, el lienzo del caballete y las pinturas de los marcos de la galería usan la pintura del jugador (textura creada en runtime).

## 2D — interfaz, iconos y máscaras

| Plantilla | Tamaño | Qué es |
|---|---|---|
| `krita/ui/UI_Kit_TEMPLATE.ora` | 1536×1024 | Hoja con todos los elementos de UI (paneles, botones, slider, iconos de herramientas). Hoy usa el skin por defecto de Unity. `UI_Kit_slots.csv` da las coordenadas de cada recuadro. |
| `krita/icons/Icon_Sunflower_TEMPLATE.ora` | 128×128 | Icono del cultivo en inventario/tienda (trae el icono actual como referencia). |
| `krita/icons/Icon_Tomato_TEMPLATE.ora` | 128×128 | Icono del cultivo en inventario/tienda (trae el icono actual como referencia). |
| `krita/icons/Icon_Glowbell_TEMPLATE.ora` | 128×128 | Icono del cultivo en inventario/tienda (trae el icono actual como referencia). |
| `krita/gameplay_masks/Sunflower_Zones_TEMPLATE.ora` | 640×512 | **Máscara de juego** (R=Petalos, G=Tallo y hojas, B=Centro). Define por zonas qué se evalúa al pintar y qué color toma cada parte de la planta. Colores puros y sin antialias. |
| `krita/gameplay_masks/Tomato_Zones_TEMPLATE.ora` | 640×512 | **Máscara de juego** (R=Tomates, G=Tallo y hojas, B=Tutor). Define por zonas qué se evalúa al pintar y qué color toma cada parte de la planta. Colores puros y sin antialias. |
| `krita/gameplay_masks/Glowbell_Zones_TEMPLATE.ora` | 640×512 | **Máscara de juego** (R=Campanas, G=Tallo y ramas, B=Esferas de luz). Define por zonas qué se evalúa al pintar y qué color toma cada parte de la planta. Colores puros y sin antialias. |

## Audio / VFX

El proyecto aún no tiene audio ni efectos (`Art/VFX` y `Audio` están vacíos).
