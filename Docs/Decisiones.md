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
