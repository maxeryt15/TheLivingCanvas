# Pantalla de carga

Concepto: un lienzo sin terminar sobre papel. El boceto a carbón está siempre; el paisaje pintado se descubre con una
pincelada según el progreso real de la carga. Ilustración provisional "ventana al jardín del museo" (luz de Monet,
pincelada de Van Gogh). No reproduce la pintura de la flor amarilla ni el campo gris del Maestro: son contenido
narrativo que el jugador debe descubrir (ver `LORE_BIBLIA_DEL_JUEGO.md` §7). El amarillo solo aparece como luz suave.

## Piezas (`Assets/_TheLivingCanvas/Scripts/Ui/`)
| Archivo | Responsabilidad |
|---|---|
| `SceneLoader.cs` | Lógica: estados, progreso honesto, timeout, errores. API: `SceneLoader.Load("Escena")`. |
| `LoadingScreenView.cs` | Presentación: papel, lienzo, boceto, pintura revelada, título, barra, mensaje, movimiento ambiente. |
| `LoadingScreenSettings.cs` | ScriptableObject `Resources/LoadingScreenSettings.asset`: ilustraciones, mensajes, tiempos. |
| `ScreenTransition.cs` | Cubre/descubre la pantalla (pincelada, tinta, disolución, papel, fundido). |
| `Editor/LoadingArtBake.cs` | Menú `TheLivingCanvas/UI/7 Bake Loading Screen Art`: genera papel, boceto, paisaje y versión apagada en `UI/Loading/`. |

## Estados (`LoadingState`)
Preparing → Loading → Activating → Completing → Revealing (+ Failed). Cada estado tiene su lista de mensajes.

## Progreso
- 0–40 % de la barra = `AsyncOperation.progress` real (Unity lo detiene en 0,9 hasta activar).
- Luego, con la escena ya cargada pero sin activar, hay una espera de presentación `postLoadSeconds` (5 s por defecto): la barra y
  la pintura avanzan linealmente del 40 % al 95 %. Es presentación, no carga; se puede dejar en 0.
- 100 % solo cuando la escena nueva ya está activa y asentada (2 fotogramas).
- La barra se suaviza hacia el valor y nunca retrocede.
- Una carga muy rápida no produce un destello: la pantalla se cubre con papel antes de mostrar nada.

## Errores y fallbacks
- Escena no incluida en Build Settings: `Debug.LogError` y no se inicia la carga.
- `LoadSceneAsync` nulo o carga sin avanzar durante `timeoutSeconds`: estado Failed, mensaje al jugador, vuelve a la escena actual.
- `finally` garantiza que la pantalla nunca queda tapada y `Time.timeScale` vuelve a 1.
- Sprites que falten: la pintura usa la cubierta pintada de transición; sin boceto no hay boceto; sin asset de settings se usan los valores por defecto.
- Peticiones duplicadas mientras se carga se ignoran.

## Cambiar el arte sin tocar código
1. Pinta las capas (papel, boceto, pintado, pintado apagado) a 960×540 o más, con proporción 16:9.
2. Crea un `Variant` en `LoadingScreenSettings` y asigna los sprites. Varias variantes rotan sin repetir seguidas.
3. `Use Faded` (manual a propósito) cambia a la versión apagada: no debe adelantar la historia.

## Accesibilidad
- `GameSettings.ReducedMotion`: sin movimiento ambiente, fundidos cortos; el progreso se sigue viendo.
- `GameSettings.HighContrastText`: mensaje en negro con contorno blanco y mayor tamaño.
- Sin parpadeos ni sacudidas. Texto oscuro sobre papel claro.

## Ilustraciones incluidas
"Garden window" (día) y "Garden at dusk" (volteada y al atardecer). Cada carga elige una distinta de la anterior.
Layout proporcional: el lienzo mantiene 16:9 dentro de una zona que escala con la pantalla (título arriba, barra y mensaje abajo).

## Verificado (2026-10-27, Play en el editor)
- Flujo completo MainMenu ↔ Museum: Preparing → Loading → Activating → Completing → Revealing, sin dejar la pantalla tapada.
- Escena inexistente: `Debug.LogError`, no empieza ninguna carga, `timeScale` sigue en 1.
- Fallo (ruta `Fail`, invocada a mano porque una carga real no se queda quieta): mensaje "We couldn't open that room…", la pantalla se destapa, `timeScale` 1.
- HighContrastText: texto negro y mayor; normal: gris y menor. ReducedMotion activo: la carga completa sin problemas.
- 16:10 (1600×1000): título arriba, pintura 16:9 dentro, barra y mensaje debajo, sin solapes.
- Ajustes ReducedMotion/HighContrast: ya tienen interruptor en Settings → Accessibility.

## Sin verificar todavía
Timeout real (una carga que se queda sin avanzar `timeoutSeconds`; solo se probó la ruta de fallo), 16:9 real y mando.
No hay audio asignado: los ganchos `UISound.LoadingStart / LoadingBrush / LoadingComplete` existen pero nada suena aún.
