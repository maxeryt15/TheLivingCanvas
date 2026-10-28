# Parámetros del generador de pinceladas (`Tools/brushstyle/paint.py`)

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
