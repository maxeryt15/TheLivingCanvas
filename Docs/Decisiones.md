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
| 2026-10-08 | Se descarta la animación pintura → cultivo (4C/4D). Al terminar, la pintura se recoge del caballete con Interact y va al inventario (placeholder); el caballete recibe un lienzo nuevo | Decisión del usuario. Qué se hace con las pinturas del inventario queda por definir. |
