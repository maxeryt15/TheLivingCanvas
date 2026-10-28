# Parámetros del generador de pinceladas (`engine/paint.py`)

`styles/<tema>.json` se **reescribe** con `profile.py`. Para retocar a mano, crea `styles/<tema>.overrides.json`
con solo las claves que quieras cambiar, por ejemplo `{"impasto": 0.8, "swirls": 2}`. `paint.py` las aplica encima.

| Clave | Qué hace | Sale de |
|---|---|---|
| `stroke_width_rel` | ancho del trazo / lado de la textura (0.0135 → 14 px en 1024) | medido |
| `width_jitter` | variación del ancho entre trazos | a ojo |
| `aspect` | largo / ancho del trazo | medido (×0.8, calibrado) |
| `length_jitter` | variación del largo (log-normal) | a ojo |
| `bend_radius_rel_width` | radio de la curva propia del trazo, en anchos (más alto = más recto) | medido |
| `bend_same_side` | 0 = curvas a ambos lados, 1 = todas hacia el mismo lado | medido |
| `jitter_deg` | cuánto se desvía cada trazo del flujo | medido |
| `swirls` | remolinos por textura | medido |
| `swirl_radius_rel` | radio de influencia del remolino / lado | medido (×1.6) |
| `swirl_same_spin` | probabilidad de que giren igual que el principal | a ojo |
| `drift_scale` | ondas del flujo de fondo por textura (entero: si no, no tilea) | a ojo |
| `coverage` | capas de trazos (1 = cubre una vez, más = se pisan) | medido |
| `neighbour_dE` | contraste de color entre trazos vecinos (color roto) | medido |
| `palette` | colores en Lab, de más presente a menos; **paleta del proyecto, no la del cuadro** | ART_DIRECTION §6 |
| `palette_scale` | manchas grandes de color por textura (entero) | a ojo |
| `impasto` | grosor de la pasta (relieve) | a ojo: no se mide en fotos |
| `bristles` | marca de cerdas dentro del trazo y pincel seco en la cola | a ojo |

## Flujo de re-trazado (pasos 1-7, 2026-10-27/28)

El juego **re-traza** las texturas pintadas (no las sustituye): `paint.py --base` conserva color y composición del original
y le añade trazos medidos de Van Gogh. Los originales se guardan antes de sobrescribir; las salidas pesadas
(`ArtSource/BrushStyle/`) no van al repo porque se pueden regenerar.

| Qué | Cómo | Ajustes aprobados |
|---|---|---|
| Museo (texturas con imagen) | `restroke_all.py` lee `families.json` (textura → tema y ajustes); `apply_museum.py Int\|Ext` copia a `Textures/Painted/Museum/BrushStyle` y edita `Museum_<lote>_Painted.json`; en Unity, menú *TheLivingCanvas/Museum/Apply Painted Materials* | por familia en `families.json`; paredes con `brush_strength` 0.08 y `brush_breakup` 0.2 |
| Ropa y pelo de NPC (atlas UV) | `uv_islands.py` (Blender `-b`, FBX → JSON de islas) y `paint.py --base T_<Pre>_<kind>.png --islands <Pre>_islands.json --material <Pre>_<kind>_Paint` | ropa: `hatch --follow 0.6 --amount 1.0 --set impasto=0.35 bristles=0.6 aspect=4 neighbour_dE=16`; pelo: `cypress --follow 0.9 --amount 0.6 --match 0.5 --set impasto=0.25` |
| Materiales sin textura (color plano) | `paint.py <tema> --name <Nombre> --set palette=[...]` con la paleta derivada del color base (base, ±valor, variante cálida y fría); entrada `painterly` con `tint` 1 en el JSON del museo | cuadros de galería por tema (`sky_dash`, `field`, `scattered_dash`); los grises siguen grises (Descoloración) |
| UI | `paint.py <tema> --base <imagen rectangular>`: se rellena en espejo a cuadrado, se pinta y se recorta; conserva el alfa | solo las portadas pequeñas `T_UI_Cover_<Var>`; la carga y el fondo del menú ya tenían pincelada y re-trazarlos perdía detalle |

Opciones de `paint.py` con `--base`:

| Opción | Qué hace |
|---|---|
| `--follow` | 0 = flujo del tema, 1 = dirección de los trazos de la propia textura |
| `--amount` | opacidad de los trazos nuevos sobre el original |
| `--edge-de` | salto de color que el trazo no cruza (juntas, bordes de prenda) |
| `--match` | acerca largo, curva, desvío y ancho del trazo a lo medido en la textura (vetas: madera, corteza, metal) |
| `--islands` / `--material` / `--margin` | atlas UV: el trazo no sale de su isla; islas solapadas se unen; el borde se extiende `--margin` px contra costuras |
| `--name` | sin `--base`: nombre de salida propio (no pisa las texturas del tema) |

Trampas conocidas:
- Re-importar un NPC con `NpcImportTool` conserva las texturas pero **no** pone `_BrushMap` (se pierde el relieve del trazo).
- Re-ejecutar `PaintedUiBake` sobrescribe las portadas re-trazadas.
- Re-exportar `Museum_*_Painted.json` desde Blender pierde `shader`, `brush`, `brush_strength` y `brush_breakup`.
- Las mediciones de contraste del analizador no sirven en atlas UV (el fondo negro domina): juzgar por render.
