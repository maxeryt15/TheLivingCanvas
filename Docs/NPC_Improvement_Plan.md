# Plan: mejora de modelos NPC, rigging y ropa que traspasa la piel

Fecha: 2026-10-26. Estado: propuesta, pendiente de aprobación paso a paso.

## Base de partida (según memoria y repo)

- Los 10 NPCs (+ Rose) están en `ArtSource/NPC/NPCs_Shell_Test.blend` (cáscara, lo que lee `export_shell11.py`) y `NPCs_Shell_Face.blend` (copia con rig facial: huesos `eye_L/eye_R` y 9 shape keys).
- Rig de 53 huesos, Humanoid en Unity. Máx. 4 pesos por vértice.
- Ya existen 26 clips Mixamo en `Desktop/Animations fbx` y acciones `U_<Npc>_Walk_*` / `U_Pose_<Npc>_*` creadas con `apply_unity_anims.py`. Sirven como banco de pruebas.
- Reparado hasta ahora: pesos de Gen, tiras de Grd. El resto quedó con pico de desplazamiento < 0.1 m, pero eso mide deformación general, no el cruce piel-ropa.
- No ejecutar `build_shell_test.py`: borra los arreglos.

## Causas probables del cruce ropa-piel

1. Pesos distintos entre piel y prenda en la misma zona (hombro, codo, cadera, rodilla): al animar, cada capa se mueve distinto.
2. Holgura estática mínima (capas separadas apenas 2.2 mm): cualquier diferencia de skinning la anula.
3. Skinning lineal (LBS) colapsa volumen en articulaciones muy dobladas; la prenda se hunde en la piel en el interior del codo/rodilla/axila.
4. Mallas fusionadas con labios (`add_lips.py`): los labios se mueven con los pesos de su borde y pueden quedar bajo la piel al flexionar.

## Fase 0 — Línea base (sin tocar nada)

1. Confirmar con el usuario cuál es el .blend de trabajo (propuesta: `NPCs_Shell_Face.blend`, la versión más nueva) y hacer backup `..._BACKUP_before_clip_fix.blend`.
2. Escribir `Tools/npc_pipeline/penetration_sweep.py` (headless, un Blender aparte del vivo):
   - Para cada NPC × clip de prueba, muestrear cada N fotogramas la malla evaluada.
   - Separar capas por material (piel vs prenda).
   - Para cada vértice de piel, buscar el punto más cercano de la prenda (BVH) y calcular la distancia con signo respecto a la normal de la prenda. Positivo = la piel sale por fuera de la prenda.
   - Agrupar por región (hombro, codo, muñeca, cadera, rodilla, cuello, tobillo) y devolver profundidad máx. y nº de vértices.
   - Guardar CSV en `ArtSource/NPC/_Reports/` y renderizar los 5 peores fotogramas por NPC (hoja de contacto).
3. Clips de prueba iniciales (cubren los casos duros):
   - Poses extremas: brazos arriba, codo a 120°+, sentadilla, sentado, agacharse.
   - Mixamo: walk, run, sit, kneel, reach, jump.
   - `U_Pose_*` existentes.
4. Entregable: tabla "NPC × región × profundidad máxima" para decidir dónde actuar. Aprobación del usuario antes de la Fase 1.

## Fase 1 — Pesos coherentes entre capas

1. Por cada prenda: transferir pesos desde la piel (Data Transfer, vértices más cercanos, interpolado) solo en las zonas ajustadas (mangas, pantalón, camisa). Las prendas holgadas (abrigos, faldas) mantienen pesos propios.
2. Suavizar pesos en articulaciones (Smooth, 1-2 iteraciones, solo hombro/codo/cadera/rodilla) y limitar a 4 influencias.
3. Repetir el barrido. Objetivo: profundidad máx. < 2 mm en todas las regiones, o la mejor posible sin romper el aspecto.
4. Probar primero con 2-3 NPCs (los peores del barrido) y mostrar render antes/después antes de aplicar al resto (regla de previsualizar antes de cambiar).

## Fase 2 — Holgura y empuje

1. Para los puntos que sigan cruzando tras la Fase 1: aumentar la holgura de reposo en esas zonas (empuje hacia fuera, dirección = alejarse de la piel, no la normal de la prenda; ya lo hace `fix_neck.py`).
2. Revisar `add_lips.py` en codos y rodillas: comprobar que los labios no quedan bajo la piel al flexionar.
3. No escalar la ropa. Capa exterior siempre empujada desde la interior.

## Fase 3 — Correctivos (solo si la Fase 2 no basta)

- Shape keys correctivas activadas por ángulo de hueso (hombro, codo, rodilla, cadera) con drivers en Blender.
- Aviso: las shape keys con drivers de hueso no viajan a Unity automáticamente. Opciones:
  - Exportar las shape keys y manejarlas con un script ligero en Unity que lea el ángulo del hueso.
  - Hornear el resultado en holgura extra (preferible: sin scripts en runtime).
- Huesos de twist (antebrazo, brazo): en Humanoid de Unity los huesos extra no se animan solos. Solo considerarlos si el usuario acepta añadir constraints o script en Unity.

## Fase 4 — Mejora de modelos NPC

Revisar con las guías `Blender/npc_modeling_guidelines.md` y `Docs/NPC_Lessons_Learned.md`:

1. Hoja de contacto de los 11 NPCs en T-pose y en 3 poses: silueta, cara, consistencia de proporciones y densidad de polígonos.
2. Lista de mejoras por NPC propuesta al usuario (silueta, cabello, ropa, cara). Nada se aplica sin visto bueno.
3. Rig facial: importar `_Exports/FaceDiag` en Unity (Humanoid), copiar a Assets, apuntar `export_shell11.py` al Face y probar parpadeo y boca. Unity MCP estaba desconectado; hay que reconectarlo.
4. Re-exportar a Unity solo cuando el barrido salga limpio. Verificar en Unity con el showcase `NPC_AnimShowcase` (37 clips, ciclo de 10 s). Pedir permiso antes de entrar en Play.

## Fase 5 — Regresión

- Guardar `penetration_sweep.py` y sus umbrales como prueba de regresión. Se ejecuta tras cualquier cambio de pesos, ropa o rig.
- Registrar resultados en `Docs/NPC_Lessons_Learned.md` y actualizar la memoria.

## Reglas de trabajo

- Pasos numerados; el usuario elige cuántos seguidos se ejecutan.
- Backup antes de cada fase; procesos pesados en Blender headless (en el vivo da timeout).
- Todo texto visible al jugador en inglés.
- Sin Play mode en Unity sin preguntar.

## Supuestos

- Blender 5.x (las acciones ligan ranura al objeto: nombres únicos por NPC).
- La fuente de verdad del export es `NPCs_Shell_Test.blend` hasta que se decida pasar al Face.
- La causa exacta del cruce se confirmará con el barrido de la Fase 0; las causas listadas son hipótesis ordenadas por probabilidad.
