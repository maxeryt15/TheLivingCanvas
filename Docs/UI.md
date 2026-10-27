# Interfaz (UI)

Todo se construye por código con uGUI + TextMeshPro (`Assets/_TheLivingCanvas/Scripts/Ui/`). Texto visible al jugador: siempre en inglés.
Juego solo en primera persona: ninguna pantalla requiere cámara contextual. Estética: pintura (Van Gogh / Monet); las texturas
actuales se generan en editor y se sustituyen por pintura a mano sin tocar código (ver "Cambiar el arte").

## Piezas
| Archivo | Qué hace |
|---|---|
| `UIFactory.cs`, `UITheme.cs` | Fábrica de elementos (canvas, panel, botón, slider, toggle, etiqueta) y paleta/tamaños/sprites. `UITheme.Current` es el tema activo. |
| `Hud.cs` | Mira y prompt de interacción con 7 pieles (Classic + 6 cuadros de Van Gogh) que se alternan con fundido. |
| `ScreenTransition.cs` | Cubre y descubre la pantalla (fundido, pincelada, papel, tinta, disolución). Con Reduced Motion solo funde. |
| `SceneLoader.cs`, `LoadingScreenView.cs`, `LoadingScreenSettings.cs` | Pantalla de carga. Detalle en `Docs/LoadingScreen.md`. |
| `MainMenu.cs` | Continue / New Game (con confirmación) / Settings / Quit. |
| `PauseScreen.cs` | Esc / Start. Resume, Settings, Main Menu (segundo clic para confirmar, guarda antes) y Quit. |
| `SettingsPanel.cs` | Ajustes en pestañas, compartido por menú y pausa. Todo se guarda en `GameSettings`. |
| `DialogueBox.cs` | Diálogo en primera persona y subtítulos sueltos. |
| `Notifications.cs` | Avisos arriba a la derecha. |
| `ObjectiveTracker.cs` | Objetivos arriba a la izquierda. |
| `JournalScreen.cs` | Cuaderno (I / Tab / Y): Satchel y Notes. |

Editor: `PaintedUiBake.cs` (menú `TheLivingCanvas/UI/6 Bake Painted Prompt Textures` y `.../Prompt Skin/...`),
`LoadingArtBake.cs` (`.../7 Bake Loading Screen Art`). `MuseumSceneBuilder.cs` crea los objetos de UI al reconstruir Museum.

## Ajustes (`Core/GameSettings.cs`, PlayerPrefs)
Audio: Master (`Volume`), `MusicVolume`, `SfxVolume`. Video: resolución, `Fullscreen`, `VSync`, `Quality`, `UiScale` (se aplica al soltar el slider).
Gameplay: `Sensitivity`, `InvertY`. Accesibilidad: `Subtitles`, `ReducedMotion`, `HighContrastText`.
La música (`Audio/MusicPlaylist.cs`) y los efectos (`SfxPlayer`) multiplican su volumen por el de los ajustes. La resolución solo
tiene efecto real en un build.

## API para el resto del juego
- `DialogueBox.Instance.Open(nombre, líneas[], alCerrar)` y `.ShowSubtitle(nombre, texto, segundos)`. E / Espacio / clic / A completan la línea y avanzan; Esc / B cierran. No libera el cursor.
- `Notifications.Show(texto, Kind.Info | Reward | Place | Saved, segundos)`.
- `ObjectiveTracker.Set(id, texto)`, `.Complete(id)`, `.Remove(id)`.
- `JournalScreen.AddNote(título, texto)` (las notas no se guardan en la partida todavía).
- `ScreenTransition.Cover(kind, segundos)` / `Uncover(segundos)`; `SceneLoader.Load("Escena")`.
- `UIEvents.Play(UISound.X)`: punto único de sonido de UI; hoy solo abrir/cerrar menú suena (vía `SfxPlayer`).

## Orden de canvas
Notificaciones 250 · Objetivos 240 · Diálogo 300 · Cuaderno 400 · Pausa 500 · Transición 900. La pausa no se abre si hay otro panel con el cursor,
si se está pintando o colocando, ni con el mismo Esc que cierra un diálogo o el cuaderno.

## Cambiar el arte
Sprites en `UITheme` (panel, botones, barras) y en `LoadingScreenSettings` (ilustraciones de carga). Mientras no haya pintura a mano, los bake
de editor generan texturas procedurales. Reglas: ningún texto va sobre pintura sin contorno (`UIFactory.ContrastOnPaint`); la paleta es la de `ART_DIRECTION.md`.

## Qué falta
- Paso 8 del plan (UI de pintura): sin hacer. Museum no tiene todavía caballete, pincel ni modo pintar; el sistema vive en el Studio archivado con UI vieja
  (`PaintToolsUI`, `CropPickerUI`, `PaintFeedbackUI`, `CoverageReadoutUI`). Se hará cuando exista la pintura en Museum.
- Rediseño pintado del menú principal (hoy botones con sprites provisionales).
- Ficha de cuadro al mirarlo y página de partida (se descartaron en el paso 7).
- Objetivos reales: el mostrador existe pero la historia aún no define ninguno.
- Fuentes: sin elegir; se usa la de TMP por defecto.
- Audio de UI: los ganchos existen, casi ninguno suena.

## Sin verificar
Probado con llamadas desde editor (no con teclado, ratón ni mando reales): pausa, ajustes, diálogo, avisos, objetivos, cuaderno, música.
No probado: Esc real y flujo Main Menu → New Game → Museum, cambio de resolución en un build, fundido entre piezas de música,
carga con timeout/fallo, Reduced Motion y High Contrast en la carga, 16:9 y 16:10, mando.

## Fase 4 del revamp (2026-10-27): menú principal y pausa
- `MenuButtons.Create` (Scripts/Ui): botón de menú compartido (texto + trazo pintado al seleccionar) para MainMenu y PauseScreen.
- MainMenu: versión (`v` + Application.version) abajo a la izquierda. PauseScreen: título "Paused" con contorno y botones-pincelada centrados.
- SettingsPanel ya usaba UITheme/sliders pintados; sin cambios.
- Retirado `Core/PauseMenu.cs` (legacy) y su `BuildPauseMenu`/`BuildControlsPanel` en `StudioSceneBuilder`.
- Verificado en Play (capturas): menú, ajustes y pausa en Museum.

## Fase 6 del revamp (2026-10-27): coherencia y audio
- `UIButtonSound` (en `UIFactory.Button` y `MenuButtons`): Hover/Select/Confirm. `Notifications` anuncia `UISound.Notification`. Lista en `Docs/UI_Sonidos.md`.
- Colores fijos restantes en `Scripts/Ui` movidos al tema (contorno claro, sombra, transición Ink, objetivo completado). Quedan solo tintes blancos neutros.
- Fase 5 (migrar paneles legacy) en espera: ninguno está en Museum; se migra cada uno cuando su sistema llegue.
