# Texture_VanGogh_Analizer

Mide cómo pinta Van Gogh (ancho, largo, curva y dirección del trazo, remolinos, contraste entre trazos vecinos) en
recortes de sus cuadros y usa esa medida para **generar** texturas de pinceladas o **re-trazar** texturas ya pintadas,
conservando su color y su composición. Funciona solo, sin Unity ni este proyecto.

## Instalación
```
pip install -r requirements.txt
```
Python 3.10 o superior. Blender solo hace falta para `islands`.

## Flujo
```
python texture_vangogh_analizer.py refs                 # 1. hojas para revisar las regiones de data/refs.json
python texture_vangogh_analizer.py analyze sky_swirl    # 2. mide un tema -> data/profiles/vangogh_sky_swirl.json
python texture_vangogh_analizer.py profile sky_swirl    # 3. perfil -> estilo -> data/styles/sky_swirl.json
python texture_vangogh_analizer.py paint sky_swirl      # 4a. textura tileable nueva -> out/sky_swirl/
python texture_vangogh_analizer.py paint foliage --base mi_textura.png   # 4b. re-traza una textura -> out/restroke/<nombre>/
```
Los estilos ya medidos vienen en `data/styles/`, así que se puede ir directo al paso 4. `themes` los lista.
`<comando> -h` muestra todas las opciones de cada comando.

Opciones globales, antes del comando: `--data DIR` (otra carpeta de datos), `--out DIR` (otra salida),
`--blender EXE` (o variable `BLENDER`).

## Comandos

| Comando | Qué hace | Escribe |
|---|---|---|
| `refs` | miniaturas de las referencias con sus regiones marcadas | `data/_sheets/` |
| `analyze <tema>` | mide el trazo en las regiones del tema (structure tensor, segmentación de trazos) | `data/profiles/<artista>_<tema>.json` y hoja de verificación |
| `profile <tema> [--mix vangogh=0.9,monet=0.1]` | mezcla perfiles en los parámetros del generador | `data/styles/<tema>.json` |
| `paint <tema>` | textura nueva, tileable | albedo, relieve 16 bit, normal, brush map, `.ora` para Krita, hoja de comparación |
| `paint <tema> --base img.png` | re-traza una textura existente (cuadrada o rectangular, conserva el alfa) | lo mismo en `out/restroke/<nombre>/` (rectangular: solo albedo) |
| `islands modelo.fbx islas.json` | islas UV de los materiales cuyo nombre contiene `clothes` o `hair` | JSON para `paint --islands` |
| `themes` | lista los estilos disponibles | — |

## Opciones de `paint`

| Opción | Qué hace |
|---|---|
| `--size N` | lado en px (por defecto 1024, o el de `--base`) |
| `--seed N` | semilla: mismo valor, mismo resultado |
| `--set clave=valor ...` | retoca el estilo solo en esta corrida (`impasto=0.3`, `palette=["#526A83","#D4A72C"]`) |
| `--name X` | sin `--base`: nombre de salida propio |
| `--follow 0..1` | con `--base`: 0 = flujo del tema, 1 = dirección de los trazos de la propia textura |
| `--amount 0..1` | con `--base`: opacidad de los trazos nuevos |
| `--edge-de N` | con `--base`: salto de color que el trazo no cruza (juntas, bordes) |
| `--match 0..1` | con `--base`: acerca el trazo al medido en la textura (vetas de madera, corteza, metal) |
| `--islands J --material M --margin N` | atlas UV: el trazo no sale de su isla y el borde se extiende N px contra costuras |
| `--no-compare` | no genera la hoja de comparación |

Para retocar un estilo a mano sin perderlo al volver a medir, crea `data/styles/<tema>.overrides.json` con solo las
claves a cambiar. Qué hace cada clave y el flujo completo usado en The Living Canvas: `PARAMETROS.md`.

## Datos
- `data/refs.json`: imágenes de referencia por artista y regiones por tema (`box` normalizado 0..1, `weight`, `use`).
- `data/vangogh/`: las imágenes. **No van al repo** (pesadas): pon las tuyas con los nombres de `refs.json`.
- `data/profiles/`, `data/styles/`: medidas y estilos ya calculados con las referencias de The Living Canvas.

## Ajustes probados (The Living Canvas)
- Ropa de NPC: `paint hatch --base T_x_clothes.png --islands islas.json --material x_clothes_Paint --follow 0.6 --amount 1.0 --set impasto=0.35 bristles=0.6 aspect=4 neighbour_dE=16`
- Pelo de NPC: `paint cypress --base T_x_hair.png --islands ... --follow 0.9 --amount 0.6 --match 0.5 --set impasto=0.25`
- Material de color plano: `paint <tema> --name X --set palette=[...]` con la paleta derivada de su color.
- Imágenes que ya tienen mucha pincelada (ilustraciones grandes): re-trazarlas pierde detalle; mejor no.
- Las medidas de contraste de la hoja no sirven en atlas UV (el fondo negro domina): juzgar por render.

## Origen
Copia independiente de `Tools/brushstyle` (pasos 1-8 del plan BrushStyle). Los scripts del proyecto
(`restroke_all.py`, `apply_museum.py`) siguen allí porque dependen de Unity y del museo.
