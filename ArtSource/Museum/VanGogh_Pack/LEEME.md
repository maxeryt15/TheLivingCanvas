# Pack Van Gogh de texturas para Krita — The Living Canvas

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
| VG_Plaster.ora → T_Plaster.png (TENIDA) | 1024 | sí | 2 | M_Museum_Plaster — paredes (Ext_Walls), buhardillas, marcos de ventana, frontispicio de la entrada |
| VG_Roof_Tiles.ora → T_Roof_Tiles.png | 1024 | sí | 2 | M_Museum_Roof, M_Museum_AwningA — tejado principal y frontón cruzado, buhardillas, chimenea, toldos rayados, cubierta del pórtico |
| VG_Stone_Blocks.ora → T_Stone_Blocks.png | 1024 | sí | 2 | M_Museum_Stone — zócalo (Ext_Plinth), molduras (Ext_Trim_Stone), esquinas, chimenea, pilares del portón, muro y cerca de piedra, farolas |
| VG_Grass_Ground.ora → T_Grass_Ground.png | 1024 | sí | 4 | M_Ground_Grass, M_Ground_Earth, M_Soil — todo el césped del jardín, tierra del sendero, tierra de jardineras y parterres |
| VG_Path_Stone.ora → T_Path_Stone.png | 1024 | sí | 2 | M_Path_Stone, M_Path_StoneWarm — losas del sendero, escalones de la entrada, piedras del muro y la cerca, bordillo de parterres |
| VG_Painted_Boards.ora → T_Painted_Boards.png | 1024 | sí | 1 | M_Museum_Shutter, M_Museum_Door, M_Sign_Board — contraventanas verdes, puerta azul de la entrada, cartel MUSEUM y cartel OPEN, jardineras |
| VG_Wood_Grain.ora → T_Wood_Grain.png (TENIDA) | 1024 | sí | 1 | M_Museum_Wood, M_Museum_WoodDark — marcos de ventanas y puerta, bancos, cajas, caballete del cartel OPEN, vigas del alero |
| VG_Leaves.ora → T_Leaves.png | 512 | sí | 1 | M_Plant_Leaf, M_Plant_LeafLight, M_Leaf_Dark, M_Ivy_Light, M_Leaf_Sage — arbustos, cipreses, hiedra de la fachada, jardineras, hierba y macetas |
| VG_Bark.ora → T_Bark.png | 512 | sí | 1 | M_Bark — troncos de los cipreses, tallos de macetas y jardineras |
| VG_Petals.ora → T_Petals.png | 512 | sí | 1 | M_Flower_* (amarilla, rosa, blanca, iris, lavanda, geranio), M_Sunflower_Disc — pradera, parterres, jardineras de ventana, macetas de girasol |
| VG_Glass.ora → T_Glass.png | 512 | sí | 1 | M_Museum_Glass — ventanas, cristal de la entrada, ojos de buey y buhardillas |
| VG_Metal.ora → T_Metal.png | 512 | sí | 1 | M_Museum_Metal, M_Iron — canalones, farolas, patas de bancos, barandilla del balcón, hierro del portón y de las ventanas |
| VG_Gilded.ora → T_Gilded.png | 512 | sí | 1 | M_Museum_Brass — pomos y bisagras, puntas doradas del portón, pincel de la veleta, regadera |
| VG_Paper_Canvas.ora → T_Paper_Canvas.png | 512 | sí | 1 | M_Museum_AwningB, M_Picket, M_Paper — rayas crema de los toldos, estacas blancas de la cerca |
| VG_Fabric.ora → T_Fabric.png (TENIDA) | 512 | sí | 1 | M_Fabric_Mustard, M_Rug_Terracotta, M_Paper — cortinas vistas a través de las ventanas, centros de flores amarillas |
