# Pack de plantillas de textura del museo (The Living Canvas)

Plantillas estilo **libro para colorear** para pintar a mano las texturas del museo. Cada textura trae:

- `krita/T_<Familia>.ora`: capas, de arriba abajo: `GUIDE (ocultar al exportar)`, `LINEART (libro para colorear)`, `paint_here` (transparente) y `base_flat_color`.
- `colorear/T_<Familia>_colorear.png`: linea negra sobre blanco, para imprimir y colorear a mano.
- `blender/T_<Familia>.png`: color base plano con el dibujo de lineas al ~35 %, para pintar encima.
- `preview/T_<Familia>_guia.png`: vista previa con la guia ya fusionada.
- `lienzos/`: lo mismo para los cuadros (ver mas abajo).
- `inventario.csv`: una fila por familia y por hueco de cuadro.

## Hechos importantes de las UV

Los modelos del museo tienen **UV por proyeccion de caja a escala real**:

- Arquitectura (paredes, suelos, tejado, escaleras, ventanas, marcos de puerta): **1 repeticion = 2 m**.
- Props y mobiliario (marcos, pedestales, plantas, bancos, carteles, hojas de puerta): **1 repeticion = 1 m**.
- Terreno exterior: **1 repeticion = 4 m**.

Por eso casi todas las texturas deben ser **SEAMLESS / REPETIBLES**. En Krita activa el *Wrap Around Mode* (tecla **W**) y pinta sin ver costuras. El dibujo de lineas de las familias repetibles ya encaja (lo que cruza un borde reaparece en el opuesto). Excepciones (diseno completo, no repetibles): `Rug_Hall` y los lienzos de los cuadros.

## Direccion artistica (recordatorio corto)

- Pictorico: pinceladas del **MISMO tono** que el material (varia luminosidad y saturacion, no el tono).
- Trazos que se solapan, sin huecos. **Nada de remolinos tipo Van Gogh** en las texturas de material.
- Los trazos siguen la forma: veta a lo largo en la madera, a lo largo de la hoja, en hileras en el tejado.
- Las familias marcadas **TENIDA** se pintan en grises/cremas neutros y CLAROS: Unity las tine con el color de cada material (una sola textura sirve para muchas paredes, telas o maderas). Base neutra `#DDD6CA`.

## Uso en Krita

1. Abre el `.ora` de `krita/`. Activa **Wrap Around Mode** (tecla `W`).
2. Pinta en la capa `paint_here`, usando `LINEART` como guia de formas. Puedes ocultar `base_flat_color` si quieres pintar sobre transparente, pero lo normal es dejarlo.
3. Antes de exportar, **oculta** la capa `GUIDE (ocultar al exportar)` (y `LINEART` si no quieres las lineas en el resultado).
4. Exporta como PNG con el **nombre exacto** `T_<Familia>.png` y el **tamano exacto** de la plantilla, a `Assets/_TheLivingCanvas/Art/Textures/Painted/Museum/`.

## Uso en Blender

Abre el PNG de `blender/` en el **Image Editor** (modo *Paint*) o usa *Texture Paint* sobre el modelo, y guarda encima (Image > Save As con el nombre `T_<Familia>.png`). El dibujo de lineas va al ~35 % para que se vea pero se pueda cubrir.

## Familias de textura

| Archivo | px | Repetible | m/rep | Materiales | Donde se ve |
|---|---|---|---|---|---|
| T_Plaster (TENIDA) | 1024 | si (W) | 2 | M_Museum_Plaster, M_Interior_Wallpaper, M_Interior_Ceiling, M_Wall_Ochre, M_Wall_Cerulean, M_Wall_Terracotta, M_Wall_Olive, M_Wall_Grey, M_Wall_White, M_Wall_Mint, M_Wall_Rose, M_Wall_Coral | fachada, todas las paredes y techos interiores, volumenes de galeria de color |
| T_Stone_Blocks | 1024 | si (W) | 2 | M_Museum_Stone | zocalo, dovelas/claves de ventanas, piedra de puerta, escultura del gato |
| T_Roof_Tiles | 1024 | si (W) | 2 | M_Museum_Roof, M_Museum_AwningA | tejado, buhardillas, toldos |
| T_Wood_Planks | 1024 | si (W) | 2 | M_Interior_FloorWood | suelos de las galerias |
| T_Wood_Grain (TENIDA) | 1024 | si (W) | 1 | M_Museum_Wood, M_Museum_WoodDark | muebles, marcos de ventanas/puertas, bancos, peldanos, zocalos de pedestal, caballetes |
| T_Painted_Boards | 1024 | si (W) | 1 | M_Museum_Shutter, M_Museum_Door, M_Interior_Wainscot, M_Sign_Board | contraventanas, puerta principal, paneles de friso, carteles |
| T_Floor_Tiles_Hall | 1024 | si (W) | 2 | M_Interior_FloorTile | suelos de hall, hueco de escalera, aseos y vestibulo |
| T_Flagstones | 1024 | si (W) | 2 | M_Floor_StoneA, M_Floor_StoneB | suelo de la Galeria VII (la geometria ya trae losas de 0.8 x 0.5 m) |
| T_Concrete | 512 | si (W) | 2 | M_Interior_Concrete, M_Floor_Dark | sala de mantenimiento, losas, huecos de sombra |
| T_Ceramic_Glaze | 512 | si (W) | 1 | M_Ceramic | inodoros, lavabos, azulejos de aseos, jarrones |
| T_Metal | 512 | si (W) | 1 | M_Museum_Metal, M_Iron, M_Hatch_Metal, M_Track_White, M_Frame_Silver | radiadores, barandillas, escotilla, railes de luz, taquillas, marcos plateados |
| T_Gilded | 512 | si (W) | 1 | M_Museum_Brass, M_Frame_Gold | marcos dorados, tiradores de laton, bisagras, postes, arana de luces |
| T_Fabric (TENIDA) | 512 | si (W) | 1 | M_Fabric_Blue, M_Fabric_Olive, M_Fabric_Mustard, M_Rug_Terracotta, cortinas (M_Paper, M_Flower_White como color) | cojines de banco, cortinas, cuerda de poste, anillos de alfombra |
| T_Rug_Hall | 1024 | NO | - | alfombra del hall (ahora M_Fabric_Blue / M_Rug_Terracotta / M_Fabric_Mustard en anillos) | hall |
| T_Leaves | 512 | si (W) | 1 | M_Plant_Leaf, M_Plant_LeafLight, M_Leaf_Dark, M_Ivy_Light, M_Leaf_Sage | plantas de interior, hiedra, follaje del jardin |
| T_Petals | 512 | si (W) | 1 | M_Flower_Yellow, M_Flower_Rose, M_Flower_Iris, M_Flower_White, M_Flower_Lavender, M_Flower_Geranium, M_Sunflower_Disc | flores del jardin, girasoles |
| T_Grass_Ground | 1024 | si (W) | 4 | M_Ground_Grass, M_Ground_Earth, M_Soil | cesped del jardin, parterres, tierra de macetas |
| T_Path_Stone | 1024 | si (W) | 2 | M_Path_Stone, M_Path_StoneWarm | caminos del jardin, escalones |
| T_Bark | 512 | si (W) | 1 | M_Bark | troncos de cipres y del ficus |
| T_Glass | 512 | si (W) | 1 | M_Museum_Glass, M_Vitrine_Glass, M_Glass_Mirror | ventanas, vitrinas, espejos |
| T_Paper_Canvas | 512 | si (W) | 1 | M_Paper, M_Canvas_Slot, M_Museum_AwningB, M_Picket | etiquetas, passe-partout, lienzos en blanco, rayas de toldo, valla |

## Lienzos (cuadros)

Cada plantilla de lienzo mide 1536 px en el lado largo e incluye regla de tercios (cian) y margen de seguridad del 5 % (magenta). Se exporta **un PNG por hueco** a `Assets/_TheLivingCanvas/Art/Textures/Paintings/` con el nombre del hueco, p. ej. `T_Painting_GalleryI_West.png`; la misma plantilla se puede reutilizar para varios huecos. No son repetibles.

| Plantilla | px | Huecos que la usan |
|---|---|---|
| Lienzo_Paisaje_3x2 (Paisaje 3:2) | 1536x1024 | GalleryI_West (1.60 x 1.10 m), GalleryIV_North (1.50 x 1.00 m), GalleryVII_South_W (1.60 x 1.10 m), GalleryVII_North_2 (1.80 x 1.20 m) |
| Lienzo_Paisaje_4x3 (Paisaje 4:3) | 1536x1152 | GalleryI_East (1.00 x 0.75 m), GalleryVI_West_M (1.40 x 1.00 m), Landing_South (1.00 x 0.80 m), GalleryVII_Wall_S2 (0.60 x 0.50 m), GalleryVII_Wall_N1 (1.20 x 0.90 m), GalleryVII_Mint_N (1.40 x 1.00 m), GalleryVII_West_3 (0.90 x 0.70 m), GalleryVII_East_2 (1.20 x 0.90 m), GalleryVII_East_3 (1.60 x 1.20 m) |
| Lienzo_Retrato_3x4 (Retrato 3:4) | 1152x1536 | GalleryI_North_A (0.80 x 1.05 m), GalleryI_North_B (0.70 x 0.90 m), GalleryI_South (0.75 x 0.95 m), GalleryII_Panel_West (0.90 x 1.15 m), GalleryII_Panel_East (0.90 x 1.15 m), GalleryII_North_A (1.00 x 1.30 m), GalleryII_North_B (1.00 x 1.30 m), GalleryII_East (0.80 x 1.00 m), GalleryIII_North (0.70 x 0.90 m), GalleryIII_West (0.45 x 0.60 m), GalleryIV_West_Front (0.80 x 1.00 m), GalleryIV_East_Front (0.80 x 1.00 m), GalleryV_East_N (0.80 x 1.00 m), GalleryV_East_S (0.70 x 0.90 m), GalleryV_North (0.70 x 0.90 m), GalleryV_South (0.70 x 0.90 m), GalleryVI_West_S (0.90 x 1.10 m), GalleryVI_West_N (0.80 x 1.00 m), GalleryVI_East (0.80 x 1.00 m), Restroom_1_Print (0.35 x 0.45 m), Restroom_2_Print (0.35 x 0.45 m), GalleryVII_South_E (1.20 x 1.40 m), GalleryVII_Wall_S1 (0.75 x 1.00 m), GalleryVII_Wall_S3 (1.00 x 1.35 m), GalleryVII_Wall_N2 (0.90 x 1.10 m), GalleryVII_Mint_S (0.80 x 1.05 m), GalleryVII_Mint_E1 (0.50 x 0.62 m), GalleryVII_Mint_E2 (0.50 x 0.62 m), GalleryVII_Mint_E3 (0.50 x 0.62 m), GalleryVII_West_1 (1.00 x 1.20 m), GalleryVII_West_2 (0.80 x 1.00 m), GalleryVII_North_1 (1.00 x 1.30 m), GalleryVII_North_3 (0.90 x 1.10 m), GalleryVII_East_1 (0.90 x 1.20 m), GalleryVII_East_4 (0.80 x 1.00 m) |
| Lienzo_Cuadrado_1x1 (Cuadrado 1:1) | 1536x1536 | GalleryIV_West_Back (0.80 x 0.90 m), GalleryIV_East_Back (0.80 x 0.90 m) |
| Lienzo_Destacado_CampoGris (Destacado 3:2 (2.4 x 1.6 m)) | 1536x1024 | GalleryV_Featured_GreyField (2.40 x 1.60 m) |

`Lienzo_Destacado_CampoGris` (hueco `GalleryV_Featured_GreyField`, 2.4 x 1.6 m): horizonte al 40 % desde abajo, cielo casi gris arremolinado y la pequena flor amarilla en la interseccion inferior derecha de los tercios. La flor destaca por **contraste, no por brillo ni glow**.

## Orden de prioridad sugerido

1. Plaster
2. Wood_Grain
3. Wood_Planks
4. Floor_Tiles_Hall
5. Stone_Blocks
6. Roof_Tiles
7. Gilded
8. Lienzo_Destacado_CampoGris
9. El resto de familias y lienzos.

## Nota sobre Rug_Hall

`Rug_Hall` es un medallon circular completo (no repetible). El modelo necesita un **cambio de UV** para mapearla como una sola pieza; lo hace Claude cuando exista la textura.

## Cuando termines

Cuando tengas texturas listas, avisale a Claude para conectarlas al shader **TLC/Painterly** en Unity.
