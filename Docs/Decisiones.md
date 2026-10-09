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
