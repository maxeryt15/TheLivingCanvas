# Informe Fase 2 — Painter (2026-10-26)

Estado: diagnosticado y validado Blender/FBX/Unity aislado. **Sin reparaciones.** NO promovido. Espera aprobación.
Fuente: `ArtSource/NPC/NPCs_Shell_Face_PAINTER_WORK.blend` (copia idéntica de Face, Face intacto). FBX staging: `ArtSource/_Exports/NPC_Validation/Painter/Painter.fbx` (sha 1d4455bf551dc13c).

## Diagnóstico (sin cambios aplicados)
- Audit: 7384 v, 9780 caras, 0 ngons, 24 materiales (`Pnt_ScarfDots` sin caras: el FBX no lo exporta → 23 slots en Unity, igual que Blender), 24 keys (9 faciales + 15 correctivas con driver). Penetración piel/ropa en reposo −2,3 mm.
- Prendas: chaqueta larga + pantalón bombacho + delantal + bufanda + boina; no lleva falda (no aplica cierre inferior).
- Capas chaqueta/pantalón (`layer_clip_scan`): en reposo ya hay 11 mm / 45 mm; los renders con culling (Idle, Walk 13/33/37, Sit, Crouch, front/side/back) muestran el faldón de la chaqueta sobre el pantalón sin atravesarse. Probé en memoria `layer_weights.reweight('Pnt', 1.0, 0.8, 0.08)` (el arreglo de Docent): no mejora las métricas (empeora Sit/LegKick_R) → descartado. Esas medidas son solape de superficie del propio modelado, no se ven.
- Delantal/bufanda vs chaqueta (`layer_scan.py`): Walk ≤22 mm en pocos vértices; Sit/BendForward 40–47 mm en 11–19 vértices (poses de flexión); renders sin hundimientos visibles. El bolsillo del delantal asoma bajo el borde sentada (poca altura) sin atravesar.
- Estiramiento de aristas: máx. 14x en Walk, en vértices duplicados de la axila/hombro (costura de la manga, pesos distintos en vértices coincidentes) y del pliegue; no hay triángulos rotos a la vista en los renders.

## No modificado (decisión)
Nada: ningún defecto reproducible a simple vista con justificación mínima. Residuos documentados: costura de axila (picos 14x), bolsillo del delantal bajo el dobladillo sentada, solape chaqueta/pantalón en poses extremas.

## Validación
- Validador: **sin FAIL** (7384/9780, UV, 24 materiales, 55 huesos, keys).
- Blender↔FBX: Rest 0 mm; poses ≤0,002 mm; Walk ≤1,3 mm; ElbowBend_R 36 mm y HeadDown 28 mm = correctivas con driver (no se exportan).
- Unity aislado (`Assets/_Dev/NpcValidation/Painter/`): sin errores/warnings, Humanoid válido, 55 bones, 24 blendshapes (9 faciales + 15 correctivas a 0), 23 slots sin nulos (remap a `M_Pnt_*` y `M_NPC_MouthInside` compartido). Sin render en Unity.

## Regresión
Face, Test, Gentleman, Student, Guard, Docent, Cafe, Courier, Curator y FBX/prefab/.meta de producción de Painter sin cambios.

## Corrección 1 — delantal sentada (2026-10-26)
Pedido del usuario: el delantal (bolsillo central) debe descansar sobre las piernas sentada, sin atravesarlas.
- Medido (`layer_scan.py`, base chaqueta/pantalón): Sit 60 vértices del delantal >1 mm dentro, 19 >15 mm, mín −40 mm (bolsillo central z 0.90–0.93, y −0.19, pesados a pelvis+muslo mezclados) y bordes laterales del dobladillo (~−25 mm).
- Reparación (solo pesos, posiciones intactas): `fix_pnt_apron.py` (pesos del delantal = baricéntricos de la prenda cercana, z<1.0) + `fix_pnt_apron_lap.py --t 0` (bolsillo central z<0.95, |x|<0.07: 100 % pelvis). Combinado en `fix_pnt_apron_all.py`. Backup: `NPCs_Shell_Face_PAINTER_WORK_BACKUP_before_apron.blend`.
- Resultado: Sit >5 mm 36→3 vértices, >15 mm 19→1 (mín −21,5 mm = tirante de hombro, ya en reposo). LegKick/Crouch mejoran. Empeora algo BendForward (extrema, >15 mm 11→18) y Walk@33 (mín −21,9→−25,6 mm).
- No se usó simulación de tela: Unity no importa cloth bakeado de un FBX skinned; el componente Cloth de Unity exige malla propia y no encaja en el pipeline.
- Re-export: sha 11bbfbc2ec86786a; validador sin FAIL (tras `restore_pose_from.py`); Blender↔FBX Sit 0,001 mm, Walk ≤1,3 mm; Unity aislado: 23 slots, 24 blendshapes, 55 bones, Humanoid válido, consola sin errores.

## Promoción a producción (2026-10-26)

- Hash FBX: 11bbfbc2ec86786a. Backup original: `ArtSource/_Backups/Painter_prod_before_20261026_174011/`; backup del .meta: `Painter_meta_before_20261026_173949/`.
- Se añadió el remap de `NPC_MouthInside` al material compartido (Gentleman/M_NPC_MouthInside.mat).
- Unity: Pnt_Mesh 28238 vértices, 24 blendshapes (9 de cara + 15 extra, probablemente correctivas sin driver en Unity), 55 huesos sin nulos (con eye_L), 23 slots sin nulos, avatar Humanoid válido, prefab NPC_Painter válido con AC_Painter (6 clips). Consola sin errores.

## Torso interior (2026-10-26)

- Mismo arreglo que Docent: `add_torso_backing.py` (208 caras de piel bajo la ropa, z 1.46 a 0.80, 14 mm por dentro) en la copia de trabajo (backup `..._WORK_BACKUP_before_torso.blend`), re-exportado y promovido. Verificado con `backing_check.py` (el torso no asoma por la ropa; hay vertices sin tela por fuera donde la prenda es abierta: escote, hombros descubiertos).
- Unity: prefab con huesos/slots/avatar validos, sin nulos, consola sin errores. Sin probar en Play.

## Bufanda celeste quitada (2026-10-26)

- Pnt_ScarfCloth eran 27 quads sueltos (108 vertices sin conectar) que se veian como un volante celeste dentado en el cuello. Pedido del usuario: arreglar o quitar. Se quitaron con `Tools/npc_pipeline/fix_pnt_scarf_remove.py` (backup `NPCs_Shell_Face_PAINTER_WORK_BACKUP_before_scarf.blend`; parte de la copia SIN torso interior).
- Re-exportado y promovido: hash FBX 001de58c5afc64fa; backup de produccion `Painter_prod_before_20261026_192315`. Unity: 22 slots (el de la bufanda desaparece), 24 blendshapes, 55 huesos, consola limpia.
