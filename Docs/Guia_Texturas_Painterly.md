# Guía de texturas pintadas a mano (Krita → Unity)

Complementa `ART_DIRECTION.md`. Explica cómo encajan modelo, UVs, textura, material y shader, y cómo sustituir los placeholders por tus texturas.

## 1. Cómo se relacionan las piezas
| Pieza | Qué es | Dónde se ajusta |
|---|---|---|
| **Modelo (malla)** | La forma 3D. Cada vértice guarda además una coordenada **UV** (u, v), un punto de la textura. | Blender (o `PrototypeMeshes.cs` para el prototipo). |
| **UVs** | El "desplegado" del modelo sobre la imagen. Deciden *qué parte de tu pintura cae en cada sitio* y en qué dirección van los trazos. | Blender (Edit Mode → UV Editing). |
| **Textura** | Tu pintura (PNG). Es la fuente del carácter: color, trazo, manchas. | Krita. |
| **Material** | Una "receta" que apunta a una textura y guarda valores (tinte, intensidad de pincelada…). | Unity: `Art/Materials/Prototype/*.mat`. |
| **Shader** | El programa que dibuja el píxel: mezcla tu textura con la luz. `TLC/Painterly` deja tu textura casi intacta, rompe el borde de la sombra con el mapa de pincelada y aplica la Descoloración. | `Art/Shaders/TLC_Painterly.shader` (parámetros en el Inspector del material). |

Regla práctica: **el trazo vive en la textura y el UV lo orienta.** Si la veta de la madera sale torcida, el problema es del UV (rota/escala la isla en Blender), no del shader.

## 2. Flujo con las plantillas
1. Abre una plantilla de `ArtSource/Templates/*.ora` en **Krita** (File → Open). Capas:
   - `GUIDE (ocultar antes de exportar)`: tamaño, dirección de las vetas, silueta real (hoja/pétalo), tercios (cuadro). No se exporta.
   - `paint_here`: capa vacía para pintar.
   - `base_flat_color`: color base de la paleta.
2. Pinta **con la dirección de las flechas** y a escala variada (pinceladas grandes + medianas + toques pequeños).
3. Oculta `GUIDE` y exporta: *File → Export* como PNG, con **el mismo nombre y tamaño** que el placeholder, en `Assets/_TheLivingCanvas/Art/Textures/Painted/`:

| Plantilla | Exportar como | Tamaño | ¿Repetible (tileable)? |
|---|---|---|---|
| `T_Wood_Floor_TEMPLATE.ora` | `T_Wood_Floor.png` | 1024×1024 | Sí |
| `T_Wall_Plaster_TEMPLATE.ora` | `T_Wall_Plaster.png` | 1024×1024 | Sí |
| `T_Wood_Frame_TEMPLATE.ora` | `T_Wood_Frame.png` | 1024×1024 | Sí |
| `T_Leaf_TEMPLATE.ora` | `T_Leaf.png` | 512×1024 | No (silueta propia) |
| `T_Petal_TEMPLATE.ora` | `T_Petal.png` | 512×1024 | No (silueta propia) |
| `T_Brush_Dir_TEMPLATE.ora` | `T_Brush_Dir.png` | 512×512 (gris) | Sí |
| `T_Painting_GreyField_TEMPLATE.ora` | `T_Painting_GreyField.png` | 1024×768 | No |

4. Vuelve a Unity: la textura se recarga sola y los materiales ya apuntan a ella. No hay que tocar nada más.

**Tileable en Krita:** activa *Wrap Around Mode* (tecla `W`). Lo que sale por un borde entra por el opuesto, así pintas sin costuras.

## 3. Qué hace cada parámetro del material (`TLC/Painterly`)
- **Painted texture / Tint**: tu textura y un tinte multiplicativo (blanco = sin cambio).
- **Brush map + Brush value variation**: textura gris auxiliar que añade variación de valor. 0 la apaga.
- **Brush breaks shadow edge**: el borde luz/sombra se desplaza según los trazos del mapa → la sombra "se pinta" en vez de ser lisa.
- **Brush tiling / rotation / space**: escala y ángulo de esa pincelada. *World* la proyecta por mundo (útil si el UV no es bueno); *MeshUV* la pega al UV.
- **Shadow tint / strength, Light threshold, Ramp softness**: color frío de las sombras, dónde cae el corte luz/sombra y cuán suave es.
- **Descolor response**: 0 = inmune a la Descoloración, 1 = totalmente afectado. **Cold shift / Contrast change**: enfriamiento y contraste al descolorar.
- **Preserved colour / range / amount**: un color (ej. el amarillo de la flor) que resiste la Descoloración.

## 4. Probar la Descoloración
En `Prototype_Museum`, pulsa **F** en Play para alternar normal ↔ Descoloración (transición suave). En edición, mueve el slider *Amount* del objeto `Descoloration Controller`. El volume `Descolor Atmosphere` añade el ajuste atmosférico (saturación, frío, contraste); los materiales aportan la parte local.

## 5. Limitaciones conocidas
- Las texturas dependen de las UVs. Los modelos del prototipo son cajas con UV en metros; para formas más orgánicas, modela y desenvuelve en Blender.
- La Descoloración usa un único valor global: para zonas distintas habrá que pasar a valores por zona (se decide tras aprobar el prototipo).
- Sin reflejos ni lightmaps: la luz es una rampa suave, a propósito.
- `Tools/make_prototype_textures.py` genera los placeholders **sin pisar** los PNG existentes (usa `--force` solo si quieres regenerarlos).
