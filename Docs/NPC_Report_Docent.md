# Informe Fase 2 — Docent (2026-10-26)

Estado: reparado en copia de trabajo, validado Blender/FBX/Unity aislado. NO promovido. Espera aprobación.

Fuente: `ArtSource/NPC/NPCs_Shell_Face_DOCENT_WORK.blend` (copia de Face; hash 11b0c5d43113bf85; Face intacto 0f32b66ac969cf7e; pose guardada restaurada, 0 huesos distintos). Backup previo al arreglo: `..._DOCENT_WORK_BACKUP_before_hem.blend`.
FBX staging: `ArtSource/_Exports/NPC_Validation/Docent/Docent.fbx` (sha 2102083c134c7641).

## Problema reparado (1)
Al caminar (Walk 9–37) el muslo que sube atraviesa el dobladillo de la chaqueta: dientes de pantalón por delante de la tela (render con culling, Walk 13/33/37). Medida layer_clip: chaqueta-en-pantalón hasta 23 mm / pantalón-fuera 49 mm. En reposo el dobladillo está limpio.
Clase A (pesos): el faldón de la chaqueta (isla superior bajo z=1.0) conserva pesos de torso/pelvis y no acompaña al muslo.
Reparación (`Tools/npc_pipeline/fix_doc_hem.py`, usa `layer_weights.reweight('Doc', 1.0, 0.8, 0.08)`): 258 vértices del faldón mezclan suavemente sus pesos hacia thigh_l/thigh_r. Solo pesos; posiciones, UV, keys sin cambio (diff Face→copia: 258 con pesos, 0 movidos). Elegida entre 5 variantes (1.05/0.95/0.06, 1.0/0.8/0.08, 1.0/0.6/0.12, 0.5/0.2, 0.35/0.15) comparando renders del hem en Walk 13/33/37: las suaves dejaban dientes; esta es la más limpia.
Efecto: Walk 33 chaqueta-en-pantalón 23→9 mm; estiramiento de aristas >1.6x: 54→48 (peor arista 7.3x, igual que antes, preexistente).

## No modificado deliberadamente
- Capas chaqueta/pantalón en poses extremas (Sit/Crouch/BendForward: 40–50 mm) y huecos pequeños bajo el dobladillo al sentarse/patada (ya existían; ahora algo más abiertos en el centro delantero con la pierna levantada).
- Métrica V2 en reposo (48 vértices/44 mm): son vértices del pantalón bajo el dobladillo (z 0.77–0.81), falso positivo; V1 en reposo = 2 vértices en la abertura trasera de la chaqueta.
- Penetración piel/ropa: sin cambios respecto a la línea base (reposo −2.2 mm; stress cuello/antebrazo = poses imposibles; "clip head 33 mm" OneHipRight f91 y "upperarm 17.6 mm" Walk f13 revisados con render: son pelo/gafas/pajarita y manga, sin piel asomando).
- Vértices coincidentes 6547/6572 de la chaqueta con pesos distintos (dif 0.047): preexistente; el validador los empareja mal → falso FAIL `weights` (Guard igual).

## Validación
- Audit: 6820 v, 7382 caras, 0 ngons, 4 influencias máx., 55 deform, eye_L/eye_R/eye_aim, 9 keys, 0 correctivas, 15 materiales.
- FBX: validador sin FAIL salvo `weights` (falso, explicado). Blender vs FBX (Rest, 12 poses, Walk 1/3/15/35/40, 9 keys): máx 0.033 mm.
- Unity aislado (`Assets/_Dev/NpcValidation/Docent/`): importa sin errores/warnings, Humanoid válido, 55 bones, 9 blendshapes, 15 materiales Painterly (remap a producción, solo lectura), sin nulos. Render prod vs nuevo (bind y Walk 0.25–0.95, delante/detrás/zoom dobladillo): sin diferencias visibles ni regresión (el clip Walk de producción levanta poco el muslo, así que la mejora se ve sobre todo en Blender). Sin Play mode ni luz del museo.

## Regresión
Face, Test, Gentleman, Student, Guard, FBX/prefab/.meta de producción de Docent sin cambios (mtime anterior a hoy); sin tocar materiales, shader, NpcImportTool, export_shell11.py, build_shell_test.py. Nuevo: `lab_hem_metric.py`, `lab_apply_reweight.py` (laboratorio en memoria).
Sin probar: correctivas (0), iluminación/Descoloración del museo con Docent.

## Promoción a producción (2026-10-26)

- Hash FBX: 2102083c134c7641. Backup original: `ArtSource/_Backups/Docent_prod_before_20261026_173246/`; backup del .meta: `Docent_meta_before_20261026_173119/`.
- Se añadió el remap de `NPC_MouthInside` al material compartido (Gentleman/M_NPC_MouthInside.mat).
- Unity: Doc_Mesh 22361 vértices, 9 blendshapes, 55 huesos (sin nulos, con eye_L), 15 slots sin nulos, avatar Humanoid válido, prefab NPC_Docent válido con AC_Docent (6 clips). Consola sin errores.
- El FAIL `weights` del validador es falso positivo conocido (vértices coincidentes de la chaqueta); añadido a la lista de falsos FAIL de promote_npc.py.

## Torso interior (2026-10-26)

- Problema: el cuerpo no tiene torso bajo la ropa; el cuello de piel termina en un borde irregular y por el cuello/costuras de la chaqueta podia verse el fondo.
- Arreglo: `Tools/npc_pipeline/add_torso_backing.py -- Doc` en `NPCs_Shell_Face_DOCENT_WORK.blend` (backup `..._DOCENT_WORK_BACKUP_before_torso.blend`). Malla cerrada de piel, 208 caras, z 1.46 a 0.80, 14 mm por dentro de la ropa, pesos/UV copiados del vertice mas cercano, shape keys = reposo. Vertices 6820 a 7014.
- Re-exportado y promovido: hash FBX b8356cf94bc16136. Backup de produccion: `ArtSource/_Backups/Docent_prod_before_20261026_185754/`.
- Unity: 9 blendshapes, 55 huesos, 15 slots sin nulos, avatar Humanoid valido, consola sin errores/warnings. Sin probar en Play (lo prueba el usuario en NpcLineup).
- El torso no llega a los brazos: queda un espacio entre torso y manga, oculto bajo la chaqueta.
