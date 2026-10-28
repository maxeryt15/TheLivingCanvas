# Guía: sustituir el arte de la UI por pintura a mano

Todo el arte de la UI es provisional (generado por código) y se reemplaza **sin tocar código**: pinta el PNG, ponlo en la carpeta
indicada y asígnalo en el asset. Complementa `Docs/Guia_Texturas_Painterly.md` y `Docs/UI_Direction.md`.
Paleta y reglas: `ART_DIRECTION.md` (pinceladas con dirección y tamaños variados, nada de ruido uniforme, bordes legibles).

## Dónde se asigna
- `Assets/_TheLivingCanvas/Resources/UITheme.asset`: paneles, botones, barras, tooltip, tarjeta, casilla, mira, prompt, fondo de menú.
- `Assets/_TheLivingCanvas/Resources/LoadingScreenSettings.asset`: ilustraciones de carga.
- Fuentes: `Assets/_TheLivingCanvas/Art/Fonts/` (Caveat Brush títulos, Lora cuerpo; ambas OFL).

## Piezas 9-slice (se estiran sin deformar las esquinas)
Importar como Sprite (Single), `Mesh Type: Full Rect`, filtro Bilinear, sin mipmaps. Definir el **Border** en el Sprite Editor
(las esquinas, en píxeles de la textura). Tamaño recomendado 128–256 px, fondo transparente, borde ya dibujado en el propio PNG.

| Campo en UITheme | Uso | Tamaño sugerido | Border (px) |
|---|---|---|---|
| `panel` | Paneles, menús, pausa | 256×256 | 48 |
| `buttonNormal / Hover / Pressed / Disabled` | Botones (4 estados, mismo tamaño) | 256×96 | 40 |
| `barBack / barFill` | Barras de progreso, sliders | 128×32 | 14 |
| `tooltip` | Fichas pequeñas | 128×128 | 24 |
| `card` | Tarjetas de papel (notas, objetos) | 256×256 | 40 |
| `slot` | Casilla de inventario/pigmento | 128×128 | 24 |

## Piezas sin 9-slice
| Campo | Uso | Tamaño sugerido |
|---|---|---|
| `reticle` | Mira del centro (mancha pequeña, blanca/clara para que se tiña) | 128×128 |
| `keyBlot` | Mancha tras la tecla del prompt | 160×112 |
| `promptStroke` | Pincelada de fondo del prompt | 512×96 |
| `menuBackground` | Fondo del menú principal | 1920×1080 |
| `promptSkins[]` / `transitionCovers[]` | Variantes del prompt / cubiertas de transición (mismo índice) | prompt: como arriba; cubierta: 1920×1080 |

## Pantalla de carga (`LoadingScreenSettings`)
Cada **Variant**: papel, boceto a carbón, paisaje pintado y versión apagada; 960×540 o más, proporción 16:9. Más detalle en `Docs/LoadingScreen.md`.
No reproducir la pintura de la flor amarilla ni el campo gris del Maestro (contenido narrativo que el jugador debe descubrir).

## Reglas
- Texto sobre pintura siempre con contorno (`UIFactory.ContrastOnPaint`): pinta zonas legibles o claras bajo el texto.
- Amarillo intenso solo como acento. La Descoloración no griza la UI.
- Mantén los nombres de los PNG con el prefijo `T_UI_` al guardarlos en `Assets/_TheLivingCanvas/UI/`.
- Para volver a los placeholders: menú `TheLivingCanvas/UI/2 Create Theme (placeholders)` (sobrescribe los sprites del tema; las fuentes se conservan).
