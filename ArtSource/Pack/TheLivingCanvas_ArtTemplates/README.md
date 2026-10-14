# The Living Canvas — pack de plantillas de arte

Contiene **todos los placeholders del juego** como plantillas para que los rehagas con tu estética.
Lista completa con medidas: `INVENTORY.md` (y `inventory.csv`). Dirección artística: `ART_DIRECTION.md`.

## Contenido
```
blender/     4 archivos .blend (3D) + textures/ (las PNG que leen los .blend) + scripts/
fbx/         un .fbx por asset (para arrastrar a Unity)
krita/       plantillas .ora: textures/ (27 familias de material), ui/, icons/, gameplay_masks/
reference/   previews/ (render de cada .blend)
```

## 3D en Blender (Blender 4.2+; probado en 5.2)
- Hay **33 assets** en 4 archivos: `TLC_Characters`, `TLC_Props`, `TLC_Crops`, `TLC_Architecture`.
  Cada asset es una colección `SM_<Nombre>` con un Empty del mismo nombre (= **pivote/origen**, en el centro de la base) y sus partes como objetos separados.
- Son **bloqueos a escala real** (1 unidad = 1 m) con las medidas exactas que tiene hoy el juego. Reemplázalos con tus modelos manteniendo: tamaño aproximado, pivote y nombres de las colecciones/partes.
- Los materiales se llaman igual que en Unity (`M_Floor_Wood`…), muestran el color actual y leen `//textures/T_<Familia>.png`.
  Pinta en Krita, exporta a `blender/textures/` y en Blender: *Image → Reload*.
- Las colecciones `_REFERENCE` (persona de 1,8 m y cubo de 1 m) y `_LABELS` no se exportan.
- **UVs**: los bloques usan 1 unidad UV = 1 metro (para texturas repetibles). Para tus modelos finales desenvuelve a tu gusto;
  la textura pintada sigue al UV (ver `Docs/Guia_Texturas_Painterly.md` del proyecto).
- **Ejes**: estándar Blender → Unity: el **frente** del objeto mira a **−Y** en Blender (vista *Front*, numpad 1) y arriba es +Z. Así llega a Unity con el frente en +Z y sin giros.
- **Partes que el código anima** (no las fusiones): cultivos (`Stem`, `Leaf_*`, `Petal_*`/`Fruit_*`/`Bell_*`…), `GardenGate` (el pivote de la hoja es `Post_L`)
  y `Easel`/`PaintingPlot`/`Gallery_Frame` (el quad `Canvas`/`Painting`/`Picture` recibe la pintura del jugador: UV 0–1 completos).

### Exportar a Unity
Dos opciones:
1. Usar los `.fbx` ya generados en `fbx/` (uno por asset, origen en 0).
2. Regenerarlos tras editar: `blender -b TLC_Props.blend --python scripts/export_fbx.py -- TLC_Props.blend ../fbx`
   (ejes `-Z` adelante / `Y` arriba, transformaciones aplicadas, escala 1; es lo estándar y llega a Unity sin rotación).

## 2D en Krita (Krita 5.x)
Cada `.ora` se abre directamente en Krita y trae capas: `GUIDE` (tamaño, dirección de pincelada, para qué sirve; **ocúltala antes de exportar**),
`paint_here` y `base_flat_color` (el color actual de Unity).
1. Pinta siguiendo las flechas (la dirección del trazo acompaña la forma: vetas, curvatura…). En las repetibles activa *Wrap Around Mode* (tecla `W`).
2. Oculta `GUIDE`, exporta como PNG **con el mismo nombre y tamaño** que indica la guía.
3. **Máscaras de juego** (`gameplay_masks/`): no son arte; los canales R/G/B puros definen las zonas que puntúa el juego. Edita las formas con pincel sin antialias y no cambies los colores.
4. **Pinturas del jugador** (lienzo, parcela, marcos de galería): se generan en el juego, no tienen plantilla.

## Pasar tus assets a Unity
- Modelos: `.fbx` a `Assets/_TheLivingCanvas/Art/Models/`; texturas PNG a `Assets/_TheLivingCanvas/Art/Textures/Painted/`.
- Hoy los materiales de Unity son colores planos; cuando tengas listas las texturas, el siguiente paso es asignarlas con el shader `TLC/Painterly`
  (ya existe, ver `ART_DIRECTION.md`). Avísame y lo hago por familia, empezando por el rincón del prototipo.
- Si cambias el tamaño de algo (casas, puertas, altura del jugador…) avisa: el código de colisiones, cámara y el builder de la escena usan estas medidas.
