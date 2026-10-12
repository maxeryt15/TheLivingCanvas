# Registro de decisiones

| Fecha | Decisión | Motivo |
|-------|----------|--------|
| 2026-10-08 | Unity 6 LTS + URP | Shader Graph para la transición pintura→3D, post-processing cálido y buen rendimiento. |
| 2026-10-08 | Cámara contextual: 3ª persona por defecto, 1ª persona al pintar, al inspeccionar pinturas y en acciones puntuales | Explorar el mundo en 3D y pintar cómodo y frontal. |
| 2026-10-08 | Crecimiento híbrido (opción C): se pinta en el caballete y el lienzo se tumba como parcela | Pintar en vertical es cómodo, el lienzo hace de parcela y el momento visual es extra. |
| 2026-10-08 | Plantillas con zonas para evaluar la pintura (sin reconocimiento libre) | Evita ML/visión por computador y no castiga a quien no sabe dibujar. |
| 2026-10-08 | Pintura en CPU (`Texture2D` 512²) primero, detrás de `PaintSurface` | Simple y fácil de leer para la cobertura. Migrable a GPU si hace falta. |
| 2026-10-08 | Arte placeholder (primitivas y ProBuilder) | Validar el *feel* antes de invertir en modelos. |
| 2026-10-08 | Git en la carpeta del proyecto | Historial y poder revertir cada fase. |
| 2026-10-08 | Todo el texto del juego en inglés | Pedido del usuario. Comentarios y docs siguen en español. |
| 2026-10-08 | Evaluación indulgente: ≥50 % de cobertura por zona; el color no bloquea. Masterpiece exige color ≥60 % en todas las zonas | No castigar a quien no sabe dibujar, pero premiar el buen color. |
| 2026-10-08 | La pintura del inventario se coloca en el suelo como parcela y de ella crece el girasol 3D procedural, con los colores pintados por zona y tamaño según la calidad | Mantiene "pintas lo que crece" sin la transición cinemática. |
| 2026-10-08 | Cosecha: Sunflower ×(1–4 según calidad) + 1 semilla que guarda la pintura y la recrea al plantarla; la parcela se consume | Decisión del usuario. Ojo: con semillas una pintura rinde para siempre; revisar en la economía (Fase 6). |
| 2026-10-08 | Se descarta la animación pintura → cultivo (4C/4D). Al terminar, la pintura se recoge del caballete con Interact y va al inventario (placeholder); el caballete recibe un lienzo nuevo | Decisión del usuario. Qué se hace con las pinturas del inventario queda por definir. |
| 2026-10-09 | Semillas que se desvanecen: cada replantado baja la pintura un nivel de calidad; una cosecha Normal no da semilla | Resuelve que una pintura rinda para siempre y premia volver a pintar bien. |
| 2026-10-09 | Los lienzos en blanco cuestan monedas (baratos); se empieza con algunos | Mete la pintura en la economía y da motivo para vender. |
| 2026-10-09 | Precio de venta fijo por cultivo (Sunflower: 10); la calidad ya decide cuántas unidades se cosechan | Pilas simples en el inventario. |
| 2026-10-09 | Primer upgrade: pigmentos en la tienda. Se empieza con los 3 colores del girasol (amarillo, ocre, verde); azul, rojo y blanco se compran uno a uno (15 monedas, placeholder) | Decisión del usuario. Cambia lo que se pinta (regla de oro D3) y tiñe el girasol 3D. |
| 2026-10-09 | Venta (6A): una caja de venta vende toda la cosecha al interactuar, sin panel | Mínimo para el slice; el panel llega con la tienda si hace falta. |
| 2026-10-09 | Fase 7: los cultivos nuevos se desbloquean comprando su boceto (sketch) en la tienda; al poner un lienzo se elige qué pintar | Da un objetivo a las monedas y reutiliza la tienda. |
| 2026-10-09 | 2º cultivo: tomate (fruto rojo, hojas verdes, tutor ocre). 3º cultivo: flor fantástica luminosa (campanilla azul que brilla) | El tomate usa el rojo comprado; la flor muestra pronto que no es una granja normal. |
| 2026-10-09 | Variantes por color: pintar una zona clave en un color concreto da una variante con nombre y rareza fija (sube el precio). Las mutaciones aleatorias quedan para la Fase 17 | Lo decide lo que pintas, no el azar. |
| 2026-10-09 | Variantes (7D): girasol pétalos rojo/azul/blanco = Red (Uncommon) / Blue (Rare) / Moon (Rare); tomate amarillo/azul/blanco = Golden (Uncommon) / Indigo (Rare) / Ghost (Rare); glowbell esferas amarillo/rojo = Sun (Uncommon) / Ember (Rare). El color tiene que parecerse de verdad (distancia RGB² ≤ 0.06); las mezclas dan el cultivo normal | Propuesta aceptada por el usuario. |
| 2026-10-09 | Una variante bien pintada puede ser Masterpiece: el color de la variante cuenta como color correcto en su zona | Decisión del usuario (opción b): pintar con cuidado siempre se premia. |
| 2026-10-09 | Fase 8: el pigmento se gasta al terminar la pintura según el área pintada de cada color (pintar, deshacer y borrar es gratis); si falta, Finish lo dice | Sin frustración a mitad de pintura y sin reembolsos por deshacer. |
| 2026-10-09 | Pigmento: se compra en la tienda (recargas) y se muele la cosecha en un mortero (cada cultivo da su color; las variantes, el suyo) | Cierra el bucle PAINT → GROW → HARVEST → CREATE. |
| 2026-10-09 | Se empieza con amarillo, ocre y verde para ~3 girasoles; sin límite de almacenamiento por ahora (capacidad, en la Fase 11) | Sin gestión extra hasta que haga falta. |
| 2026-10-09 | Fase 9: pinceles que cambian cómo se pinta: Fill (rellena una zona de la plantilla) y Glaze (veladura semitransparente que mezcla colores, ej. amarillo sobre rojo = naranja). Se compran una vez en la tienda | Mezclar colores abre posibilidades; rellenar combate la repetición (riesgo D2). |
| 2026-10-09 | Pincel Fill: una pintura hecha sobre todo (>50 %) con Fill llega como mucho a Excellent, y lo rellenado cuesta 1.5× de pigmento | Decisión del usuario (b + c): Fill acelera, pero la Masterpiece se gana pintando a mano. |
| 2026-10-11 | Fase 10A (por defecto, a revisar): tipos de lienzo como datos (CanvasType). Lienzo estándar (5) y lienzo grande (15): cosecha ×2, pigmento ×2, parcela más grande. Si se tiene más de un tipo, al cargar el caballete se elige primero el lienzo y luego el cultivo | El usuario pidió avanzar; se toma la opción recomendada y se revisa al terminar la 10A. |
| 2026-10-11 | 10B: sin lienzos especiales por ahora (quedan para la Fase 17) | Decisión del usuario. |
| 2026-10-11 | 10C: mejora "lienzo de trama fina" (compra única): el lienzo del caballete pasa de 640×512 a 960×768 para pintar con más detalle; pigmento y cosecha se normalizan al área (no cambian) | Decisión del usuario; no pisa al lienzo grande de la 10A. |
| 2026-10-11 | Fase 11: nivel de artista con XP por pintar (más por mejor calidad y un extra al descubrir por primera vez un cultivo o una variante) | Premia pintar bien y explorar colores. |
| 2026-10-11 | Cada oferta de la tienda pide un nivel mínimo; lo bloqueado se ve con "Level N" como meta | Aprovecha todos los desbloqueos que ya existen. |
| 2026-10-11 | Primera zona nueva: el Jardín (exterior junto al estudio, más espacio para parcelas), que se abre a cierto nivel | Zona 2 del prompt maestro. |
| 2026-10-11 | Herramientas nuevas: cuentagotas (toma cualquier color de la pintura, incluidas las mezclas del Glaze, y lo usa como color opaco) y simetría (espejo vertical, cuenta como pintado a mano) | Cambian cómo se pinta (regla de oro D3). |
| 2026-10-11 | Fase 12: la galería es una sala nueva detrás del estudio (puerta en la pared del fondo), con marcos vacíos en las paredes | Cerca de donde se pinta y se puede agrandar después. |
| 2026-10-11 | Las pinturas se cuelgan y descuelgan en un marco desde el inventario; mientras cuelgan no se pueden plantar | Decisión real (exhibir o plantar) sin perder nada. |
| 2026-10-11 | La galería muestra una placa por cuadro (nombre con variante, calidad, lienzo) y un tablero de colección con cultivos y variantes descubiertos y por descubrir. Logros, más adelante | Usa lo que ya registra el nivel de artista. |
| 2026-10-11 | La galería no da beneficios de juego por ahora; los visitantes y encargos llegan con los NPCs (Fase 13) | Lugar cozy para disfrutar lo pintado. |
| 2026-10-11 | Fase 13: el primer NPC es una coleccionista excéntrica que está en la galería, con preferencias de color y rareza | Le da función a la galería; el pueblo llega en la Fase 14. |
| 2026-10-11 | Primer encargo: una pintura concreta (cultivo + calidad mínima) que se entrega desde el inventario y se consume | La pintura sigue siendo el centro del juego. |
| 2026-10-11 | Recompensa de encargos: monedas (más que vendiendo) + XP, y en algunos algo único que no está en la tienda (ej. un pigmento nuevo) | Motiva sin romper la economía. |
| 2026-10-11 | Plan: 13A NPC + diálogo (SO con líneas, panel que avanza); 13B encargo y entrega; 13C recompensa y cadena de 2–3 encargos | Pasos pequeños y revisables. |
| 2026-10-11 | Arte: shader painterly en HLSL (`TLC/Painterly`) en vez de Shader Graph; Descoloración = global `_TLC_Descolor` + Volume de atmósfera; prototipo en escena aparte | HLSL es verificable y legible en texto; el global permite comparar normal/descolor y proteger el amarillo por material. Ver `ART_DIRECTION.md`. |
| 2026-10-11 | Fase 14: el pueblo está al sur del estudio y del jardín (x -12..18, z -26..-6), se sale por un hueco en el frente del estudio y está abierto desde el inicio | Queda a mano y es el centro social; nada que desbloquear. |
| 2026-10-11 | Pueblo en greybox con materiales planos (como el resto de Studio.unity) hasta aprobar el prototipo painterly | `ART_DIRECTION.md`: no montar muchos assets antes de validar el estilo. |
| 2026-10-11 | La tienda se queda en el estudio. En la plaza hay un puesto con un marchante de arte que compra pinturas (precio según cultivo, calidad y rareza) | Decisión del usuario: nueva elección entre plantar, colgar o vender; la pintura sigue siendo el centro. |
| 2026-10-11 | 14C: encargos del pueblo en un tablón de anuncios en la plaza (notas firmadas por vecinos, de a una, en cadena), recompensa monedas + XP | Decisión del usuario: abre los encargos a más gente del pueblo sin crear NPCs nuevos. |
| 2026-10-11 | Plan: 14A espacio (suelo, camino, plaza, fuente, casas de fachada, límites); 14B marchante de arte; 14C encargos del pueblo | Pasos pequeños y revisables. |
| 2026-10-11 | Fase 15: las estaciones (Spring → Summer → Autumn → Winter) pasan por tiempo de juego, ~8 min cada una (placeholder); el HUD muestra la estación y lo que falta | Simple y acorde a un crecimiento de 20 s; sin ciclo de días ni cama. |
| 2026-10-11 | Cada cultivo tiene una estación favorita: en ella da +1 de cosecha; fuera de ella no cambia nada | Cozy: premia sin bloquear. |
| 2026-10-11 | 15C: un pigmento de temporada que solo se vende en su estación, y líneas de saludo de los NPCs según la estación. El marchante no cambia; eventos de temporada a la Fase 17 | Decisión del usuario. |
| 2026-10-11 | Plan: 15A reloj de estaciones + HUD + paisaje (sol y tintes greybox); 15B cultivos de temporada; 15C pigmento de temporada + diálogos | Pasos pequeños y revisables. |
