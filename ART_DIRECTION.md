# DIRECCIÓN ARTÍSTICA PERMANENTE — The Living Canvas

Referencia permanente del proyecto. Consultarla antes de proponer o hacer cambios visuales importantes
(arte, materiales, shaders, iluminación, postprocesado, escenas). Son **criterios permanentes**, no una orden
de construirlo todo a la vez. Todo el texto visible para el jugador sigue en inglés (ver `Docs/Decisiones.md`).

## 1. Rol
Actuar como director artístico, technical artist de Unity, experto en shaders estilizados y asesor de producción.
Ayudar a lograr una identidad visual coherente, original y viable. Nada de soluciones visuales genéricas: cada
decisión de modelado, textura, material, shader, luz y composición debe contribuir a una dirección reconocible.

## 2. Identidad visual
Experiencia 3D explorable, tranquila, contemplativa y emocional, con estética artesanal que combina pintura,
naturaleza, exploración y misterio.

> El mundo no tiene que parecer una pintura perfecta. Tiene que parecer que alguien lo ha pintado porque todavía le importa.

Jerarquía de influencias (no mezclarlas indiscriminadamente; cada escena con una intención visual clara):
1. **Van Gogh / postimpresionismo** (principal): pinceladas expresivas, formas orgánicas, color intenso, movimiento.
2. **Monet / impresionismo**: luz, atmósfera, jardines, reflejos, variaciones cromáticas, sensación de aire.
3. **Expresionismo** (selectivo): deformación de formas, composición y contraste para lo subjetivo, sobre todo en zonas afectadas por la Descoloración.

Se estudian *principios* (ritmo de pincelada, contrastes, luz, deformación expresiva, composición, detalle vs.
legibilidad). No se copian pinturas famosas, composiciones, diseños protegidos ni assets ajenos. Debe funcionar
como videojuego 3D, no como pintura estática ni como escena realista con filtro.

## 3. Reglas visuales innegociables
**Geometría y siluetas**
- Mundo completamente 3D y explorable (no 2D/2.5D disfrazado).
- Siluetas claras, orgánicas, ligeramente exageradas; irregularidad artesanal en árboles, flores, rocas, muebles, edificios.
- Evitar realismo físico excesivo si debilita la identidad pictórica; mantener claridad para distinguir y explorar objetos.

**Texturas pintadas a mano** (el usuario pinta sus propias texturas y quiere participar en la creación visual)
- Diseñar materiales pensando en texturas originales pintadas a mano.
- Pinceladas con dirección, escala y propósito (no ruido aleatorio): vetas en la madera, curvatura en hojas, volumen en rocas, movimiento en pétalos.
- Manchas cromáticas + variación tonal + trazos visibles sin destruir la lectura del material; la textura conserva su personalidad bajo la luz del juego.
- Priorizar reutilización: materiales compartidos, atlas cuando tengan sentido, paletas coherentes, parámetros configurables. No exigir texturas enormes.

**Imperfección controlada**: humana y artesanal, no descuidada. Painterly NO es: texturas borrosas, ruido de color en todo,
bordes ilegibles, pinceladas del mismo tamaño en todos los objetos, saturación máxima permanente, ni un shader que
deforma/ensucia todo lo que aparece en pantalla.

## 4. Narrativa que afecta al arte
- **La Descoloración**: el color desaparece o se vuelve menos perceptible; ligada a percepción subjetiva, sufrimiento emocional y la historia del protagonista.
- Protagonista en duelo por la muerte de su gata: dolor, culpa, creación y seguir viviendo sin borrar lo perdido.
- Ciclo: **PAINT → GROW → HARVEST → CREATE**. La dirección artística debe apoyarlo.
- **NO** implementar la Descoloración como filtro de grises global. Combinar de forma controlada: saturación reducida, contraste selectivo,
  relación cálido/frío, menor intensidad de ciertos colores, luz y atmósfera, composición/espacio negativo, cambios sutiles en la expresividad de las formas.
  Debe variar por escena/lugar/necesidad narrativa; localizada y gradual; sin espectáculo. El color no es una cura mágica ni una alegoría rígida.
- **La flor amarilla**: pintura antigua de un campo bajo un cielo arremolinado casi gris, con una pequeña flor amarilla intensa. Elemento narrativo clave:
  destaca por contraste cromático, composición y control de luz (no por brillo mágico exagerado) y sigue siendo parte de una obra pictórica.

## 5. Estrategia técnica (Unity)
Inspeccionar siempre pipeline y versión antes de escribir código. No cambiar de pipeline por iniciativa propia. No asumir que el shader más complejo es el mejor.
Los shaders **complementan** las texturas pintadas a mano, no las sustituyen. Sistema modular, según utilidad y presupuesto:
- **A. Material painterly base**: integra texturas pintadas, conserva detalle cromático bajo la luz, variación tonal controlada, intensidad de pincelada ajustable, reutilizable por familias.
- **B. Pinceladas**: patrones direccionales que respetan forma/UV; control de escala, intensidad, contraste, orientación; uso selectivo. Evaluar si vienen de textura, patrón procedimental, luz o combinación; sin solución universal.
- **C. Control de la Descoloración**: parámetros reutilizables (saturación, contraste, tratamiento tonal), variación por material/objeto/zona, transiciones suaves, preservación selectiva (amarillo de la flor), sin cambios bruscos ni pérdida de legibilidad. Evaluar material / `MaterialPropertyBlock` / Volume de postproceso / máscaras locales y explicar pros y contras antes de elegir.
- **D. Iluminación**: la luz da volumen sin borrar pinceladas; sombras que ayudan a leer forma y atmósfera; luz cálida en espacios acogedores pero no uniforme en todo el juego; controlar bloom, especulares realistas y sobreexposición; evaluar luz + niebla + ambiente + materiales.
- **E. Naturaleza**: hojas, tallos, pétalos y árboles con siluetas reconocibles; variación cromática y pinceladas direccionales; el viento/animación no debe volver las plantas gelatinosas; el crecimiento se integra con lo artesanal, sin abusar de partículas genéricas.

**Arquitectura**: centralizar parámetros artísticos compartidos; `ScriptableObject` para paletas/configuraciones si aporta valor; separar parámetros globales / de zona / de material; no duplicar shaders casi idénticos; exponer controles en el Inspector; documentar parámetros con valores iniciales razonables; mantener compatibilidad con materiales y sistemas existentes. **No construir un framework enorme antes de validar el estilo en una escena pequeña.**

## 6. Paleta inicial (punto de partida, no límite)
| Nombre | Hex |
|---|---|
| Azul cerúleo | `#526A83` |
| Amarillo cálido | `#D4A72C` |
| Verde oliva | `#65785A` |
| Terracota | `#A85F47` |
| Azul grisáceo | `#747983` |
| Crema envejecida | `#E0CDB0` |

Cada zona necesita jerarquía cromática comprensible. En escenas apagadas no convertir todo en el mismo gris: conservar diferencias de temperatura, valor, textura y contraste.
En escenas llenas de color no subir saturación indiscriminadamente: relaciones deliberadas y puntos focales. La flor amarilla destaca sobre todo por contraste con el entorno.

## 7. Herramientas
Blender (modelado, UVs), Krita/Photoshop (texturas a mano), Unity (materiales, shaders, luz, niebla, postproceso, composición), Shader Graph o HLSL según pipeline.
Inspeccionar lo ya disponible antes de añadir dependencias; justificar cualquier paquete nuevo. El usuario quiere **aprender**: explicar cómo se relacionan modelo, UVs, textura, material y shader; nada de cajas negras imposibles de ajustar artísticamente.

## 8. Prototipo artístico prioritario (validar antes de diseñar el mundo)
1. Rincón del museo con suelo, paredes y algunos elementos sencillos.
2. Marco con la pintura del campo gris y la flor amarilla.
3. Una flor 3D simple.
4. Materiales de madera y vegetación con texturas pintadas a mano.
5. Iluminación coherente con el estilo.
6. Un primer material painterly y, si aporta beneficio visible, un shader experimental.
7. Forma controlada de comparar apariencia normal vs. afectada por la Descoloración.

Objetivo: comprobar que la escena transmite **soledad, curiosidad y una pequeña posibilidad de esperanza** sin efectos exagerados. Implementación pequeña, funcional, fácil de revisar. No avanzar a un sistema completo de shaders ni a decenas de assets antes de validar.

## 9. Reglas de colaboración
1. Inspeccionar antes de modificar (estructura, materiales, escenas, shaders, pipeline).
2. Explicar decisiones importantes: qué problema resuelve y qué cuesta.
3. Fases pequeñas, cada una funcional y comprobable.
4. **Esperar aprobación del usuario antes de avanzar a la siguiente fase importante.**
5. No reemplazar sistemas existentes sin necesidad; comprobar dependencias y regresiones.
6. No inventar APIs de Unity: verificar propiedades, nodos y técnicas contra la versión del proyecto.
7. Priorizar resultados visibles sobre arquitectura sin validar.
8. Rendimiento: coste de shaders, transparencia, overdraw, variantes de materiales, operaciones por píxel.
9. Documentar limitaciones (dependencia de UVs, luz, cámara, pipeline).
10. Un shader técnicamente correcto no garantiza belleza: no confundir implementación con dirección artística.

Al proponer un cambio visual, indicar: qué aporta al estilo, qué materiales/escenas afecta, coste técnico, cómo se ajusta, cómo se valida visualmente.

## 10. Originalidad
No recomendar "un filtro de óleo / acuarela / shader painterly descargado y listo". Los recursos externos son referencia o punto de partida; deben evaluarse, adaptarse y complementarse con trabajo artístico propio.

---
## Estado de implementación (actualizar al avanzar)
- Fase 1 (auditoría y plan): hecha 2026-10-11.
- Fase 2 (prototipo): hecha 2026-10-11, pendiente de aprobación. `Scenes/Prototype_Museum.unity` (menú TheLivingCanvas/Build Art Prototype Scene),
  shader `TLC/Painterly` (HLSL URP, ver cabecera), `PainterlyDescolor` (tecla F en Play), texturas placeholder en `Art/Textures/Painted`,
  plantillas Krita en `ArtSource/Templates`. Guía: `Docs/Guia_Texturas_Painterly.md`. Studio.unity NO se ha tocado.
- BrushStyle (re-trazado Van Gogh, 2026-10-27/28, rama `brushstyle-museum-retexture`): museo (105 materiales, 93 en TLC/Painterly),
  ropa y pelo de los 11 NPC (piel, ojos y cejas sin tocar), 15 materiales planos del museo y 6 portadas de UI. Flujo y ajustes: `ArtSource/BrushRefs/styles/PARAMETROS.md`.
  Pendiente: accesorios planos de NPC (~210 materiales), brillo del cuadro gris destacado, trazo quizá grande en cuadros pequeños.
