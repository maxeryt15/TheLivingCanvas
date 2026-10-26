# Informe Fase 2 — Rose (Receptionist) (2026-10-26)

Estado: diagnosticada y validada Blender/FBX/Unity aislado. **Sin reparaciones.** NO promovida. Espera aprobación.
Fuente: `ArtSource/NPC/NPCs_Shell_Face_ROSE_WORK.blend` (copia idéntica de Face; Face intacto). FBX staging: `ArtSource/_Exports/NPC_Validation/Rose/Rose_Receptionist.fbx` (sha 072c5acd7935e14d).

## Diagnóstico
- Audit: 9269 v, 10561 caras, 0 ngons, 18 materiales (todos con caras), 30 keys (9 faciales + 20 correctivas con driver: hombros y codos), 55 huesos, pesos normalizados. Prendas: chaqueta de manga larga + pantalón, zapatos con hebilla, gafas, pendientes, cruz, insignia, coletero con girasol.
- Penetración piel/ropa en reposo: ningún vértice de piel asoma (los 12 vértices a 5–25 mm dentro de la ropa están cubiertos, en codos/antebrazos); picos de estrés ≤18 mm en poses de 90–120° (antebrazos), no visibles.
- Capas chaqueta/pantalón (`layer_clip_scan`): reposo V1 19 vértices 24 mm / V2 208 vértices 43 mm; Sit/Crouch hasta 35–49 mm. Es el solape propio de la chaqueta abierta sobre el pantalón; en renders con backface culling no hay hundimientos ni huecos a la vista (frente/lado/espalda de Idle, Sit, Crouch, BendForward, Walk). No se probó reponderado: no hay defecto visible que lo justifique (en Painter y Gardener empeoraba).
- Culling: sin caras volteadas en cabeza (gafas, pendientes, cruz, coletero con girasol), insignia, botones, zapatos.

## No modificado (residuos)
Solape chaqueta/pantalón en poses extremas (métrica, no visible). Nada más.

## Validación
- Validador: **sin FAIL** (9269/10561, UV, 18 materiales, 55 huesos, pesos 0 dif, reposo exportado).
- Blender↔FBX: Rest 0 mm; Sit/Crouch/Twist/Bend/HeadDown ≤0,001 mm; Walk ≤0,018 mm; ArmsUp_L/R 55–57 mm y ElbowBend_R 35 mm = correctivas de hombro/codo con driver que no se exportan a Unity (valor 0).
- Unity aislado (`Assets/_Dev/NpcValidation/Rose/Rose_Receptionist.fbx`): Humanoid válido, 55 bones, 29 blendshapes, 18 slots sin nulos (remap a `M_Rose_*` y `M_NPC_MouthInside` compartido), consola limpia. Sin render en Unity.

## Regresión
Face, Test, Gentleman y demás NPCs, y FBX/prefab/.meta de producción de Rose sin cambios.

## Promoción a producción (2026-10-26)

- Hash FBX: 072c5acd7935e14d (`Rose_Receptionist.fbx`). Backup original: `ArtSource/_Backups/Rose_prod_before_20261026_174453/`; backup del .meta: `Rose_meta_before_20261026_174431/`.
- Se añadió el remap de `NPC_MouthInside` al material compartido (Gentleman/M_NPC_MouthInside.mat).
- Unity: Rose_Mesh 34268 vértices, 29 blendshapes (9 de cara + 20 extra, probablemente correctivas sin driver en Unity), 55 huesos sin nulos (con eye_L), 18 slots sin nulos, avatar Humanoid válido, AC_Rose con 6 clips. Consola sin errores.
- Rose no tiene prefab en `Prefabs/NPC`: `Museum.unity` referencia el FBX directamente. No se comprobó la instancia en escena (no había ninguna Rose en la escena abierta).

## Torso interior (2026-10-26)

- Mismo arreglo que Docent: `add_torso_backing.py` (208 caras de piel bajo la ropa, z 1.46 a 0.80, 14 mm por dentro) en la copia de trabajo (backup `..._WORK_BACKUP_before_torso.blend`), re-exportado y promovido. Verificado con `backing_check.py` (el torso no asoma por la ropa; hay vertices sin tela por fuera donde la prenda es abierta: escote, hombros descubiertos).
- Unity: prefab con huesos/slots/avatar validos, sin nulos, consola sin errores. Sin probar en Play.
