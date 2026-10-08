# The Living Canvas — Fase 0: Diseño técnico y plan

> Estado: **BORRADOR para revisión**. Nada de esto está implementado todavía.
> Las secciones marcadas con 🟡 **DECISIÓN** necesitan tu elección antes de avanzar.

---

## 1. Análisis del concepto

**Pilar central:** *"No plantas semillas. Pintas lo que quieres que crezca."*

El juego vive o muere por un único momento: **la pintura cobrando vida y convirtiéndose en un objeto 3D**. Todo lo demás (economía, NPCs, estaciones, galería) es un sistema de soporte que ya existe resuelto en otros farming games. Lo que es único, y por tanto lo arriesgado, es:

1. **Pintar debe ser divertido por sí mismo**, incluso para alguien que "no sabe dibujar".
2. **La pintura debe importar**: lo que pintas y *cómo* lo pintas tiene que cambiar el resultado (calidad, variante, color). Si cualquier garabato da el mismo girasol, la pintura se vuelve un minijuego decorativo, que es justo lo que quieres evitar.
3. **La transición 2D → 3D debe ser espectacular** y legible.

El bucle **PAINT → GROW → HARVEST → CREATE** es sólido porque la cosecha alimenta directamente la pintura (pigmentos, pinceles, lienzos). Así la economía queda subordinada al acto creativo en lugar de competir con él.

**Mi lectura del juego en una frase:** un farming game donde la "semilla" es una pintura evaluada, y donde la habilidad artística (asistida) determina la calidad de la cosecha.

---

## 2. Mayores riesgos técnicos

| # | Riesgo | Por qué es difícil | Mitigación propuesta |
|---|--------|--------------------|----------------------|
| T1 | **Reconocer qué pintó el jugador** | Reconocer dibujos libres (ML, visión por computador) es caro, frágil y fuera de alcance. | **No reconocer: evaluar.** El jugador elige qué va a pintar (una "receta"/plantilla) y el sistema mide qué tan bien la cumplió: cobertura por zona y color. El dibujo libre real se deja para mucho después. |
| T2 | **Pintar sobre una superficie 3D con buena respuesta** | Raycast → UV → textura. Hay que cuidar la interpolación de trazos (si el mouse va rápido, salen puntos sueltos), el rendimiento y la nitidez. | Interpolar entre muestras del cursor, estampar el pincel (stamp) a intervalos fijos y usar una resolución moderada (512×512 al inicio). |
| T3 | **La transición pintura → cultivo 3D** | Requiere shaders (disolución, "vibración" de la pintura), partículas, raíces que crecen y un modelo que emerge. Es más arte técnico que programación. | Secuencia por fases controlada por un único parámetro `growth` (0→1) que alimentan shaders y animaciones. Empezar con primitivas y shaders simples, iterar el *feel* después. |
| T4 | **Assets 3D** (girasol, raíces, lienzo, estudio) | Sin modelos, el momento "mágico" no se ve mágico. | Placeholders con primitivas y ProBuilder al principio. 🟡 Hay que decidir el origen del arte (ver §11). |
| T5 | **Undo/redo y guardado de pinturas** | Las texturas pesan; guardar cada estado de la pintura es caro. | Undo con instantáneas por trazo (con límite, ej. 20). El guardado se hace en PNG por lienzo + metadatos JSON. |
| T6 | **Mando y tablet** | Pintar con stick es incómodo; la presión de la tablet necesita el Input System nuevo. | Usar el **Input System nuevo** desde el día 1. Con mando: cursor virtual + asistencia de plantillas. La presión de tablet llega gratis vía `Pen`. |
| T7 | **Cámara al pintar** | En 3D, pintar en ángulo es frustrante. | Al interactuar con el lienzo, la cámara pasa a un "modo pintura" frontal y fija (con Cinemachine). |

## 3. Mayores riesgos de diseño

| # | Riesgo | Mitigación |
|---|--------|------------|
| D1 | **Castigar a quien no sabe dibujar** | Plantillas con siluetas y zonas sugeridas. La calidad se mide por *cobertura y color dentro de zonas*, no por precisión de línea. Un resultado mediocre igual produce un cultivo; la calidad solo afecta al bonus. |
| D2 | **Que pintar se vuelva repetitivo** (pintar 40 girasoles) | Esto es CRÍTICO a medio plazo. Ideas: lienzos grandes que generan varios cultivos, "re-pintar" sobre una pintura guardada, pinceles que cubren más área, y que la variedad venga de colores/estilos (un girasol pintado en azul produce una variante). Hay que validarlo pronto con el prototipo. |
| D3 | **Que se convierta en farming tradicional con capa de pintura** | Regla de diseño: todo sistema nuevo debe responder a *"¿cómo cambia esto lo que pinto o cómo pinto?"*. Si no lo cambia, no entra. |
| D4 | **Que la pintura no tenga consecuencias** | La evaluación debe producir datos que afecten de verdad al cultivo: calidad, color dominante → variante, cobertura → rendimiento. |
| D5 | **Alcance (scope)** | El plan de fases ya lo mitiga. Lo mantenemos estrictamente: nada fuera del vertical slice hasta que el girasol se sienta mágico. |
| D6 | **Identidad visual demasiado pegada a Van Gogh** | Usar el postimpresionismo como *técnica* (pinceladas visibles, contornos, colores saturados) y no como referencia de obras concretas. Definiremos una paleta y un lenguaje de trazo propios en la Fase 19 / dirección de arte. |

---

## 4. Arquitectura mínima inicial (Unity)

### Decisiones base propuestas

- **Unity 6 (6000.x LTS)** con **URP**. URP nos da Shader Graph (indispensable para la transición pintura→3D), buen rendimiento y post-processing para el look cálido. 🟡 *DECISIÓN: versión de Unity.*
- **Input System nuevo** (mouse, mando y tablet con presión).
- **Cinemachine 3** para la cámara de exploración y la de modo pintura.
- **Sin frameworks externos** (nada de DI, ni Zenject, ni assets de pago) al inicio.

### Principios

- **ScriptableObjects para datos** (definiciones de cultivos, plantillas, pinceles y colores).
- **MonoBehaviours pequeños para comportamiento.**
- **Comunicación por eventos C# simples** (`event Action<...>`) entre sistemas. No hace falta un event bus global hasta que lo necesitemos.
- **Un solo `GameManager` mínimo** solo si hace falta. Evitar singletons para todo.

### Sistemas del vertical slice (y nada más)

```
Player
 ├── PlayerMovement        (CharacterController + Input System)
 ├── PlayerInteractor      (raycast/trigger → IInteractable más cercano)
 └── CameraModeController  (cambia la prioridad entre cámaras virtuales Cinemachine:
                            ThirdPerson = por defecto · FirstPerson = pintar,
                            inspeccionar pinturas y acciones puntuales)

Canvas3D (prefab: caballete + lienzo)
 ├── CanvasInteractable    (implementa IInteractable → entra al modo pintura)
 ├── PaintSurface          (textura, raycast → UV, estampado de pincel)
 ├── PaintHistory          (undo/redo)
 └── PaintEvaluator        (compara la pintura con la plantilla → PaintingResult)

PaintModeController        (cámara de pintura, cursor, UI de herramientas, entrada/salida)

GrowthSequence             (recibe PaintingResult → anima la transición → instancia Crop)
Crop                       (planta 3D: etapas de crecimiento, luego cosechable en Fase 5)
```

Son unos **10–12 scripts** para todo el vertical slice. Si pasamos de ~15, algo está sobrediseñado.

### Lo que NO vamos a construir todavía

- Sistema de guardado general (solo lo mínimo para depurar).
- Inventario, economía, tienda.
- Sistema de tiempo, días o estaciones.
- Reconocimiento de dibujo libre.
- NPCs, diálogo, encargos.
- Múltiples escenas o carga de zonas.
- Object pooling (no hay nada que *poolear* todavía).
- Sistema de estilos artísticos.
- Localización y opciones.

---

## 5. Estructura de carpetas propuesta

```
Assets/
└── _TheLivingCanvas/            ← todo lo nuestro aquí, separado de paquetes/plugins
    ├── Art/
    │   ├── Materials/
    │   ├── Models/
    │   ├── Shaders/             (Shader Graphs: pintura, disolución, crecimiento)
    │   ├── Textures/
    │   │   └── PaintTemplates/  (máscaras de zonas de las plantillas)
    │   └── VFX/
    ├── Audio/
    ├── Data/                    ← instancias de ScriptableObjects (.asset)
    │   ├── Crops/
    │   ├── Templates/
    │   ├── Brushes/
    │   └── Pigments/
    ├── Prefabs/
    │   ├── Player/
    │   ├── Canvas/
    │   ├── Crops/
    │   └── Environment/
    ├── Scenes/
    │   ├── Studio.unity         (escena del vertical slice)
    │   └── Sandbox/             (escenas de pruebas aisladas por sistema)
    ├── Scripts/
    │   ├── Core/                (interfaces, utilidades)
    │   ├── Player/
    │   ├── Interaction/
    │   ├── Painting/
    │   ├── Growth/
    │   └── Data/                (clases ScriptableObject)
    ├── Settings/                (URP assets, Input Actions)
    └── UI/
Docs/                            ← fuera de Assets: diseño, decisiones, notas
```

Proponemos un **assembly definition** solo para `Scripts/` (compila más rápido y evita dependencias raras). No haremos más asmdefs hasta que hagan falta.

---

## 6. Primeros ScriptableObjects

Solo los que necesita el vertical slice:

```csharp
// Qué es un cultivo y cómo crece
CropDefinition : ScriptableObject
    string   id, displayName
    GameObject cropPrefab          // modelo 3D final
    float    growthDuration        // segundos (en el slice, tiempo real corto)
    PaintTemplate template         // qué hay que pintar para obtenerlo

// Qué debe pintar el jugador y cómo se evalúa
PaintTemplate : ScriptableObject
    Texture2D silhouette           // guía visual que se muestra tenue en el lienzo
    Texture2D zoneMask             // máscara RGB: cada canal/color = una zona
    ZoneRequirement[] zones        // por zona: color esperado, cobertura mínima, peso
    float    minScoreToGrow        // umbral para que "cobre vida"

// Un color pintable
PigmentDefinition : ScriptableObject
    string id, displayName
    Color  color

// Un pincel
BrushDefinition : ScriptableObject
    Texture2D stampShape           // forma del pincel (suave, duro, cerdas…)
    float minSize, maxSize, spacing
    float opacity
```

`ZoneRequirement` es una clase `[Serializable]` normal, no un SO.
`PaintingResult` es una clase/struct en runtime (score, cobertura por zona, color dominante, calidad) y **no** un SO.

---

## 7. Cómo implementaría el sistema de pintura 3D

### 7.1 Detección y proyección
1. El lienzo es un **Quad** con un `MeshCollider` (o `BoxCollider` + cálculo manual de UV).
2. Cada frame en modo pintura: `Camera.ScreenPointToRay(cursor)` → `Physics.Raycast` contra la capa `PaintSurface`.
3. `RaycastHit.textureCoord` nos da la **UV (0–1)** del punto. Esto requiere `MeshCollider`. Con un quad es barato y exacto.
4. UV × resolución = píxel en la textura de pintura.

### 7.2 Registro y renderizado de trazos
- **Trazo = lista de puntos** `(uv, presión, tiempo)` + pincel + color.
- Entre dos muestras del cursor **interpolamos** y estampamos el pincel cada `spacing × tamaño` píxeles. Así no quedan huecos aunque el mouse vaya rápido.
- **Renderizado** 🟡 *DECISIÓN TÉCNICA (recomiendo A para empezar):*
  - **A) CPU con `Texture2D` (512×512):** estampar con un array `Color32[]` y `SetPixels32` + `Apply()`. Simple, fácil de depurar, y leer la cobertura es trivial porque los datos ya están en CPU. Rinde bien a 512².
  - **B) GPU con `RenderTexture` + shader de pincel:** más rápido y escalable a 2048², con mezclas de color avanzadas. Leer la cobertura requiere `AsyncGPUReadback`. Más complejo.
  - **Plan:** empezar con **A**, aislado detrás de la clase `PaintSurface`, y migrar a **B** si el rendimiento o la calidad lo piden (probablemente en Fase 9, cuando lleguen los pinceles avanzados).
- El material del lienzo muestra la textura de pintura encima de una textura de tela, con la silueta de la plantilla tenue debajo.

### 7.3 Undo/redo
- Antes de cada trazo se guarda una **instantánea** del buffer (`Color32[]` de 512² ≈ 1 MB).
- Pila de undo con límite (20) y pila de redo que se vacía al pintar.
- El borrador es simplemente un pincel que escribe el color base/transparente.

### 7.4 Evaluación (convertir pintura en datos de gameplay)
Para cada zona de la plantilla (ej. girasol: **pétalos**, **centro**, **tallo/hojas**):
- **Cobertura** = píxeles pintados dentro de la zona / píxeles de la zona.
- **Acierto de color** = distancia media entre el color pintado y el esperado (en espacio HSV o Lab, más tolerante que RGB).
- **Derrame** = pintura fuera de toda zona (penalización suave, nunca bloqueante).
- `score = Σ(peso × cobertura × acierto)` → **calidad** (ej. Normal / Buena / Excelente / Obra maestra).
- El **color dominante** de cada zona se guarda en `PaintingResult`. Más adelante decidirá las variantes (un girasol con pétalos azules = variante azul).

Este enfoque **no castiga a quien no sabe dibujar**: rellenar las zonas con colores razonables ya da un buen resultado. Al artista experto le da margen (las variantes vienen del color y, más adelante, de pinceles y estilos).

### 7.5 Guardado (más adelante)
PNG por pintura (`EncodeToPNG`) + JSON con metadatos (plantilla, resultado, fecha). El diseño ya lo permite, pero no se implementa hasta la Fase 18.

---

## 8. Cómo conectar la pintura con el crecimiento

```
Jugador pulsa "Terminar"
   → PaintEvaluator.Evaluate(surface, template) → PaintingResult
   → si score < umbral: feedback amable ("le falta color a los pétalos…"), puede seguir pintando
   → si score ≥ umbral: el lienzo se bloquea y se lanza GrowthSequence(result, cropDefinition)
```

**`GrowthSequence`** es una corrutina o línea de tiempo con fases. Todas están dirigidas por un parámetro `t` y se pueden ajustar desde el Inspector:

| Fase | Duración aprox. | Qué ocurre | Técnica |
|------|----------------|------------|---------|
| 1. Despertar | 1.0 s | La pintura vibra y respira | Shader del lienzo: distorsión de UV con ruido + brillo |
| 2. Chispas | 0.8 s | Partículas de pigmento con los colores *reales* pintados | VFX/Particle System coloreado con los colores dominantes del resultado |
| 3. Raíces | 1.5 s | Raíces se dibujan en la pintura y atraviesan el lienzo | Malla de raíces con shader de "crecimiento por máscara" (alpha clip que avanza) |
| 4. Emergencia | 1.5 s | El tallo sale de la superficie del lienzo | Modelo con el shader de crecimiento + escala/curva de animación |
| 5. Florecer | 1.0 s | Hojas y flor se abren y la pintura del lienzo se "vacía" | Animación/blendshape + disolución de la pintura del lienzo |
| 6. Crecimiento | `growthDuration` | El girasol crece hasta su tamaño final | Escala por etapas. Luego se marca como cosechable (Fase 5) |

**Detalle clave para la magia:** los materiales del girasol 3D toman los **colores que el jugador pintó**. Si pintó pétalos naranja oscuro, el girasol 3D es naranja oscuro. Ese es el vínculo visible entre "lo que pinté" y "lo que creció".

🟡 **DECISIÓN DE DISEÑO IMPORTANTE — ¿dónde crece la planta?**
- **A) Lienzo vertical en caballete:** la planta brota *del* lienzo hacia el suelo de delante (o el lienzo se tumba y se convierte en tierra). Es muy teatral, pero ¿qué pasa con el lienzo después? ¿Queda ocupado?
- **B) Lienzo horizontal en el suelo, como una parcela:** pintas mirando desde arriba y la planta brota hacia arriba atravesando la tela. Es coherente con "el lienzo ES la parcela" y crecer hacia arriba es natural, pero pierde la imagen icónica del caballete.
- **C) Híbrido:** pintas en un caballete y, al terminar, el lienzo "vuela" y se tumba sobre un hueco de parcela, donde echa raíces y la planta brota hacia arriba. Pintar en vertical resulta cómodo, el lienzo hace de parcela y el momento visual es extra.
- ✅ **Elegida: C.** Para el vertical slice lo simplificamos: caballete + lienzo que se inclina hacia el suelo justo delante.

---

## 9. Vertical Slice mínimo

**Una escena (`Studio`), un jugador, un caballete, un girasol.**

1. El jugador camina por un pequeño espacio cozy (habitación/patio con primitivas y luz cálida).
2. Se acerca al caballete → aparece el aviso "Pintar [E]".
3. Entra en modo pintura: la cámara se pone frontal, aparece una silueta tenue de girasol y una UI con **3 colores** (amarillo, marrón y verde), **1 pincel** con tamaño ajustable, **borrador** y **undo**.
4. Pinta. Pulsa "Terminar".
5. Si la cobertura es suficiente → secuencia de transición (§8) → un girasol 3D crece con los colores pintados.
6. Si no → mensaje amable indicando qué zona falta.

**Fuera del slice:** cosecha, inventario, dinero, guardado, más cultivos, NPCs y estaciones.

**Criterio de éxito:** que al verlo digas *"quiero volver a pintar otro"*.

---

## 10. Subtareas de FASE 0 y FASE 1

### FASE 0 — Diseño y arquitectura (este documento)
- **0.1** Revisar este documento y responder las 🟡 decisiones. ← *estamos aquí*
- **0.2** Ajustar el documento con tus respuestas y congelar la arquitectura v1.
- **0.3** Crear `Docs/Decisiones.md` (registro corto de decisiones tomadas y por qué).
- **0.4** Definir la "regla de oro" de diseño (D3) y el criterio de éxito del slice. ✅ (ya propuestos arriba)
- ⏸ **Parada: revisión.**

### FASE 1 — Proyecto Unity (sin agricultura)
**Grupo 1A — Proyecto base**
- **1.1** Crear el proyecto Unity 3D (URP) en esta carpeta.
- **1.2** Instalar los paquetes: Input System, Cinemachine y ProBuilder.
- **1.3** Crear la estructura de carpetas (§5) + `.gitignore` de Unity + repositorio git.
- **1.4** Crear la escena `Studio` con suelo, paredes simples, luz direccional cálida, skybox y post-processing básico (bloom suave y color grading cálido).
- ⏸ **Parada: revisión** (abres el proyecto y ves la escena).

**Grupo 1B — Jugador y cámara**
- **1.5** Crear el Input Actions asset (Move, Look, Interact, Sprint) con soporte de teclado/mouse y mando.
- **1.6** Crear `PlayerMovement` (CharacterController, caminar, girar hacia la dirección y gravedad).
- **1.7** Crear las cámaras Cinemachine: tercera persona (orbital, con colisión) + punto de vista en primera persona, y un `CameraModeController` que cambia entre ellas (probar con una tecla de depuración).
- **1.8** Crear un jugador placeholder (cápsula con "cara" para ver la orientación).
- ⏸ **Parada: revisión** (caminas por la escena).

**Grupo 1C — Interacción básica**
- **1.9** Crear la interfaz `IInteractable` (`Prompt`, `Interact(Interactor)`).
- **1.10** Crear `PlayerInteractor` (detecta el interactuable más cercano o al que mira).
- **1.11** Crear la UI de aviso ("[E] Interactuar") simple.
- **1.12** Crear un objeto de prueba interactuable (ej. una lámpara que se enciende y se apaga).
- ⏸ **Parada: revisión.** Fin de la Fase 1.

---

## 11. Decisiones (resueltas el 2026-10-08)

1. ✅ **Unity 6 LTS + URP.**
2. ✅ **Cámara contextual:** tercera persona casi siempre. **Primera persona** al pintar, al interactuar con las pinturas y en otras acciones puntuales.
3. ✅ **Crecimiento: opción C (híbrida).** Ver §8.
4. ✅ (por defecto) **Plantillas con zonas** para el slice. La pintura libre queda para el futuro.
5. ✅ (por defecto) **Pintura en CPU (`Texture2D` 512²)** primero, encapsulada en `PaintSurface`.
6. ✅ **Placeholders** (primitivas y ProBuilder) primero.
7. ✅ (por defecto) **Git** en la carpeta del proyecto.
8. **Cómo trabajamos con Unity:** yo puedo escribir scripts, assets y configuración por archivos y compilar en *batchmode* desde la línea de comandos para detectar errores. Pero **no puedo ver el editor ni jugar**, así que las pruebas visuales y de *feel* las harás tú y me contarás qué ves.
