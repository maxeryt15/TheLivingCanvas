# Dirección visual de la UI (Fase 0 del revamp)

Criterio para todo HUD, menú, pantalla de carga y panel. Complementa `ART_DIRECTION.md` (identidad), `Docs/UI.md` (arquitectura) y
`Docs/LoadingScreen.md`. Texto visible al jugador: siempre en inglés. Juego solo en primera persona.

## Idea rectora
La interfaz es el **cuaderno y el papel del pintor**, no una capa de software sobre el mundo: notas a lápiz, parches de lienzo,
pinceladas de tinta y manchas de pigmento. Debe parecer hecha a mano "porque todavía le importa", sin ser descuidada ni ilegible.

## Lenguaje de formas
| Elemento | Forma |
|---|---|
| Panel | Parche de papel/lienzo con borde irregular y una pincelada de tinta en una esquina; nunca rectángulo perfecto con sombra |
| Botón | Pincelada horizontal; hover = más pigmento y ligera inclinación; pressed = más oscuro; disabled = trazo seco (menos cubriente) |
| Tecla del prompt | Mancha de pigmento con la letra encima |
| Barras | Surco de carbón + relleno de pintura que avanza con borde desigual |
| Separadores | Línea de lápiz/pincel fina, nunca recta del todo |
| Iconos | Silueta simple de 1–2 trazos; el pigmento aporta el color |
| Mira | Mancha pequeña (ya existe `reticle`); activa = crece y se calienta |

## Color
- Base: paleta de `ART_DIRECTION.md` + `ink` (`UITheme`). Papel = crema, texto = ink.
- Texto sobre papel: ink. Texto sobre tinta/oscuro: crema. Texto sobre pintura: siempre `UIFactory.ContrastOnPaint`.
- Cerúleo = información/neutral · oliva = positivo/crecimiento · terracota = aviso/bloqueado · azul grisáceo = deshabilitado.
- **Amarillo cálido = solo acento** (foco, recompensa, selección). Lo guarda la flor amarilla.
- La Descoloración **no** grisea la UI. Máximo: tono algo más frío y trazos interrumpidos en el HUD dentro de zonas afectadas; nunca en menús ni accesibilidad.

## Tipografía
- Dos fuentes: **display** (títulos, nombres de sala, menú) y **cuerpo** (todo lo demás). Tamaños en `UITheme` (96 / 48 / 30 / 22 a 1920×1080).
- Cuerpo: muy legible a 22 px; display: carácter manuscrito/serif cálida, sin caer en caligrafía ilegible.
- HighContrastText: ink sobre crema con contorno, tamaño mayor. Licencia libre (OFL) obligatoria.

## Movimiento (`UIAnimator`)
- Entradas: fundido+pincelada/tinta/página según pieza; 120–150 ms en paneles. Sin rebotes ni sacudidas ni parpadeos.
- ReducedMotion: solo fundidos cortos, sin movimiento ambiente. El progreso sigue visible.
- Todo con tiempo no escalado (funciona con el juego pausado).

## Tono del texto
Sereno, íntimo, escueto. Sin culpa ni castigo por no producir. Vocabulario: room / gallery / museum, pigments, the Discoloration.
No decir que pintar "cura". Avisos cortos ("Saved", "New pigment"), no exclamativos.

## Jerarquía en pantalla (HUD)
1. Centro: mira + prompt (lo único siempre visible).
2. Arriba izquierda: objetivos (máx. 3). Arriba derecha: avisos temporales.
3. Esquina inferior/lateral: monedas, estación, nivel y pigmentos; discretos, ocultables y que se atenúan sin uso.
4. Paneles modales (tienda, cuaderno, pausa…) liberan el cursor y paran la interacción (`UIPanel`).

## Lo que NO se hace
Filtro de óleo genérico, sombras/brillos de UI de asset store, esquinas redondeadas uniformes, pinceladas del mismo tamaño en todo,
saturación máxima permanente, texto sin contorno sobre pintura, UI que tape el mundo sin motivo.

## Pendiente de aprobación del usuario
- Elección de fuentes (candidatas en el chat).
- Revisión de la hoja de estilo (`UI_Sandbox`) antes de la Fase 1.
