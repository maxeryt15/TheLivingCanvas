# Informe Fase 2 — Cafe (2026-10-26)

Estado: diagnosticado y validado Blender/FBX/Unity aislado. **Sin reparaciones: no se encontró ningún defecto que justifique modificar la malla o los pesos.** NO promovido. Espera aprobación.

Fuente: `ArtSource/NPC/NPCs_Shell_Face_CAFE_WORK.blend` = copia idéntica de Face (hash 0f32b66ac969cf7e, Face intacto). FBX staging: `ArtSource/_Exports/NPC_Validation/Cafe/Cafe.fbx` (sha d2a909579b5db28f).

## Diagnóstico (sin cambios aplicados)
- Audit: 5149 v, 7116 caras, 0 ngons, 4 influencias máx., suma pesos 1.0, 0 sin peso, 55 deform, eye_L/eye_R/eye_aim, 9 keys faciales + 20 correctivas (R/L_Shoulder_Up, R_Shoulder_Forward, L_Leg_Abduct…), 20 drivers, 20 materiales.
- Penetración piel/ropa: reposo −3.5 mm (nada penetra); stress (muslo 27 mm, etc.) = poses imposibles; clips: zapato 22/17 mm en Walk f1/f19 y torso 10 mm → revisados con render (pies, hombros, pecho): sin defecto visible.
- Vestido+delantal (sin par superior/inferior): medido delantal vs vestido (`layer_scan.py`): Walk 11–28 de 505 vértices por dentro del vestido, peor 18 mm (un puñado de vértices del borde inferior del delantal al levantar la pierna; 5 vértices de la tira del cuello ocultos 5–19 mm bajo el tirante del vestido, ya en reposo). Probadas 3 variantes de repesado (solo pesos) → mejora marginal (Walk@33 24→22/13→11 vértices) y sin diferencia visible en render; descartadas por no estar justificadas.
- Render con culling (Idle, Walk 1/13/19/33, Sit, Crouch, BendForward, LegKick, Twist; frente/espalda/lado; hombros, falda, pies; y sin vestido para ver las tiras): delantal limpio, tiras y lazo coherentes (las tiras pasan sobre el hombro y terminan en un muñón oculto: diseño), pies limpios. Solo se aprecia el faldón del vestido solapando una esquina del delantal en LegKick_L (pose extrema).
- Correctivas con drivers activos en Walk: efecto máx. 0.8–3.8 mm (sin distorsión).
- Estiramiento de aristas: sin picos nuevos.

## No modificado (decisión)
Nada. Residuos documentados: solape faldón/delantal en patada extrema; tiras del delantal hundidas bajo el tirante (invisibles).

## Validación
- FBX: validador **sin FAIL** (5149/7116, UV, 20 materiales, 55 huesos, 30 keys con valor 0, reposo exportado exacto, pesos máx dif 0.0000).
- Blender vs FBX: Rest 0.000 mm; 12 poses ≤0.001 mm (salvo ArmsUp_L/R 29–32 mm y Walk 1–2.4 mm = efecto de las correctivas con drivers, que NO se exportan al FBX: sin drivers en Blender coincide); 9 keys faciales 0.000 mm.
- Unity aislado (`Assets/_Dev/NpcValidation/Cafe/`): importa sin errores/warnings, Humanoid válido, 55 bones, 29 blendshapes (9 faciales + 20 correctivas, todas a 0), 20 materiales Painterly (remap a producción, solo lectura), sin nulos. Render prod vs nuevo (bind y Walk 0.3/0.8, frente/falda/espalda): idéntico. Sin Play mode ni luz del museo.

## Atención para la promoción
El FBX de producción de Cafe tiene 0 blendshapes; el nuevo trae 29 (incl. 20 correctivas sin driver en Unity: valdrán 0 hasta que un script las mueva, igual que Gardener/Tourist/Curator/Painter/Courier/Rose).

## Regresión
Face, Test, Gentleman, Student, Guard, Docent y FBX/prefab/.meta de producción de Cafe sin cambios. Nuevos: `layer_scan.py` (medida delantal/pieza vs prenda, opción `--fix`), `fix_caf_apron.py` (laboratorio, NO aplicado), zooms `skirt`/`feet` en `render_pose_sheet.py`.
Sin probar: iluminación/Descoloración del museo con Cafe.

## Adenda: cierre del vestido por abajo (sustituye al forro oscuro)
Petición del usuario: tras probar un forro oscuro en cono (3 iteraciones, descartado), cerrar el vestido desde abajo con la misma textura y quitar el forro.
- Forro eliminado (copia de trabajo restaurada desde `NPCs_Shell_Face_CAFE_WORK_BACKUP_before_lining.blend`; `add_caf_lining.py`/`check_caf_lining.py` quedan solo como referencia, no aplicados). No existe `Caf_Lining_Mat` ni slot extra (20 slots).
- `Tools/npc_pipeline/add_caf_hemcap.py` (solo Cafe WORK; marca `tlc_hemcap`): tapa el borde del dobladillo de la falda (47 verts, z≈0.49) con un disco de 188 caras (3 anillos interiores 75/50/25 %, pesos: reparto lateral thigh_l/thigh_r (franja central ±0,02 m) mezclado con los del dobladillo hacia el centro => al sentarse descansa sobre los muslos con pliegue recto en L siguiendo el ángulo de las piernas; antes 94 caras, anillo al 50 % + centro), material `Caf_clothes_Paint` (misma textura), UV/color copiados del dobladillo, pesos = los del dobladillo mezclados con el promedio (≤4 influencias). Las piernas atraviesan el disco por abajo.
- Export staging nuevo (da3629b8d7db9ff5; 5197 verts, 7210 polys); Blender↔FBX: poses ≤0,001 mm, Walk ≤2,6 mm (drivers de correctivas, como antes). Unity aislado: importa bien, humanoide válido, 20 slots sin nulos. No promovido.
- Ajuste del pliegue sentada (2026-10-26): `add_caf_hemcap.py` además repondera falda y delantal por delante (y<0, z<0.95, degradado hasta z=0.70) hacia thigh_l/thigh_r según x (401 verts); así al sentarse la falda queda como una lámina plana sobre ambos muslos, simétrica de frente, y cae en L en la rodilla. Cambia pesos de vestido/delantal (solo Cafe). Walk/Idle revisados en render.

## Promoción a producción (2026-10-26)

- Hash FBX: 04462b14279c6aba. Backup original: `ArtSource/_Backups/Cafe_prod_before_20261026_173439/`; backup del .meta: `Cafe_meta_before_20261026_173418/`.
- Se añadió el remap de `NPC_MouthInside` al material compartido (Gentleman/M_NPC_MouthInside.mat).
- Unity: Caf_Mesh 21539 vértices, 29 blendshapes (9 de cara + 20 correctivas, estas sin driver en Unity, valen 0), 55 huesos sin nulos (con eye_L), 20 slots sin nulos, avatar Humanoid válido, prefab NPC_Cafe válido con AC_Cafe (6 clips). Consola sin errores.

## Torso interior (2026-10-26)

- Mismo arreglo que Docent: `add_torso_backing.py` (208 caras de piel bajo la ropa, z 1.46 a 0.80, 14 mm por dentro) en la copia de trabajo (backup `..._WORK_BACKUP_before_torso.blend`), re-exportado y promovido. Verificado con `backing_check.py` (el torso no asoma por la ropa; hay vertices sin tela por fuera donde la prenda es abierta: escote, hombros descubiertos).
- Unity: prefab con huesos/slots/avatar validos, sin nulos, consola sin errores. Sin probar en Play.
