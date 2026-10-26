# Informe Fase 2 — Gardener (2026-10-26)

Estado: diagnosticado y validado Blender/FBX/Unity aislado. **Sin reparaciones.** NO promovido. Espera aprobación.
Fuente: `ArtSource/NPC/NPCs_Shell_Face_GARDENER_WORK.blend` (copia idéntica de Face; Face intacto). FBX staging: `ArtSource/_Exports/NPC_Validation/Gardener/Gardener.fbx` (sha bee2709fa25c673d).

## Diagnóstico
- Audit: 4673 v, 7365 caras, 0 ngons, 17 materiales (todos con caras), 29 keys (9 faciales + 20 correctivas con driver, hombros), 55 huesos, pesos normalizados. Prendas: camiseta de manga corta + pantalón, sombrero de paja, guante colgado de la cadera, brizna de paja, bigote.
- Penetración piel/ropa en reposo −4,0 mm; picos ≤18 mm solo en poses de estrés (hombros).
- Capas camiseta/pantalón (`layer_clip_scan`): reposo 27 vértices de la camiseta 24 mm dentro del pantalón y 22 vértices del pantalón 24 mm fuera de la camiseta (solape propio del modelado); Sit/Crouch/BendForward hasta 45–50 mm. Probé en memoria `layer_weights.reweight` (arreglo de Docent) con cuatro juegos de parámetros: empeora Sit/Crouch/Walk (p. ej. Sit 12→41-49 mm) → descartado. `fix_gar_hem.py` (plantilla Student) solo detecta 1 vértice <−15 mm en reposo: sin justificar.
- Renders con backface culling (Idle/Sit/Crouch/BendForward/Walk, frente/lado/espalda, primeros planos de cabeza y guante): sin caras volteadas, sin huecos ni piel visible bajo la ropa; camiseta sobre pantalón sin atravesarse a la vista. En Sit/Crouch la camiseta se arruga con aristas irregulares sobre la entrepierna (sin agujeros).
- Estiramiento de aristas: máx. 17x en Walk (cuadros 22–25), vértices duplicados de axila/costura; sin triángulos rotos a la vista.

## No modificado (residuos)
Solape camiseta/pantalón en poses extremas; arrugas de la camiseta sobre la entrepierna sentado/agachado; picos de estiramiento en la costura de la axila al caminar; guante colgante de cadera sin colisión (prop).

## Validación
- Validador: **sin FAIL** (4673/7365, UV, 17 materiales, 55 huesos, pesos 0 dif).
- Blender↔FBX: Rest 0 mm; Sit/Crouch/Twist/Bend ≤0,002 mm; ArmsUp_L/R 60 mm y ShoulderCross_L 40 mm y Walk 6–12 mm = correctivas de hombro con driver que no se exportan a Unity (valor 0).
- Unity aislado (`Assets/_Dev/NpcValidation/Gardener/`): Humanoid válido, 55 bones, 29 blendshapes (9 faciales + 20 correctivas a 0), 17 slots sin nulos (remap a `M_Gar_*` y `M_NPC_MouthInside` compartido), consola limpia. Sin render en Unity.

## Regresión
Face, Test, Gentleman y demás NPCs, y FBX/prefab/.meta de producción de Gardener sin cambios.

## Corrección 1 — brizna de paja detallada (2026-10-26)
Pedido del usuario: más detalle en la paja de la boca. Backup previo: `NPCs_Shell_Face_GARDENER_WORK_BACKUP_before_straw.blend`. FBX nuevo sha aa234e7480740fcc.
- `fix_gar_straw.py`: sustituye Gar_StrawStalk (14 caras) y Gar_StrawTip (47) por tallo redondo de 6 lados, afinado, curvado, con 2 nudos y extremo masticado de 3 astillas dentro de la comisura, y espiga de trigo (raquis + 7 pares de granos alternos en bipirámide + aristas finas) con caída al final. Misma ruta y largo; todo pesado 100 % a `head`; materiales StrawStalk/StrawTip; shape keys = reposo, UV/colores a 0 como el original. Totales: 4841 v, 7561 caras (+168 v, +196 caras).
- Previsualizado con `render_straw.py` (primeros planos con culling) y aprobado antes de aplicar.
- Validador sin FAIL; Blender↔FBX igual que antes (Rest 0 mm, correctivas de hombro sin driver); Unity aislado: Humanoid válido, 17 slots sin nulos, 29 blendshapes, consola limpia.

## Promoción a producción (2026-10-26)

- Hash FBX: aa234e7480740fcc. Backup original: `ArtSource/_Backups/Gardener_prod_before_20261026_174326/`; backup del .meta: `Gardener_meta_before_20261026_174305/`.
- Se añadió el remap de `NPC_MouthInside` al material compartido (Gentleman/M_NPC_MouthInside.mat).
- Unity: Gar_Mesh 21985 vértices, 29 blendshapes (9 de cara + 20 extra, probablemente correctivas sin driver en Unity), 55 huesos sin nulos (con eye_L), 17 slots sin nulos, avatar Humanoid válido, prefab NPC_Gardener válido con AC_Gardener (6 clips). Consola sin errores.

## Forro del sombrero y re-promoción (2026-10-26)

- Pedido del usuario: el sombrero se ve hueco por dentro (copa de una sola capa; con backface culling el interior es invisible).
- `Tools/npc_pipeline/fix_gar_hatliner.py --inset 0.004`: duplica las 124 caras de la copa, las voltea y las hunde 4 mm formando un forro interior; el aro inferior se suelda al original (sin rendija). Pesos, UV y shape keys heredados. Backup de la copia de trabajo: `NPCs_Shell_Face_GARDENER_WORK_BACKUP_before_hatliner.blend`.
- Nuevo hash FBX: e67371172988e14e. Backup del FBX anterior de producción: `ArtSource/_Backups/Gardener_prod_before_20261026_183517/`.
- Unity: Gar_Mesh 22354 vértices, 29 blendshapes, 55 huesos sin nulos, 17 slots sin nulos, avatar Humanoid válido, prefab con AC_Gardener (6 clips). Consola sin errores.

## Torso interior (2026-10-26)

- Mismo arreglo que Docent: `add_torso_backing.py` (208 caras de piel bajo la ropa, z 1.46 a 0.80, 14 mm por dentro) en la copia de trabajo (backup `..._WORK_BACKUP_before_torso.blend`), re-exportado y promovido. Verificado con `backing_check.py` (el torso no asoma por la ropa; hay vertices sin tela por fuera donde la prenda es abierta: escote, hombros descubiertos).
- Unity: prefab con huesos/slots/avatar validos, sin nulos, consola sin errores. Sin probar en Play.
