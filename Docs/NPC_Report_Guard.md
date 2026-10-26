# Informe Fase 2 — Guard (2026-10-26)

Estado: reparado en copia de trabajo, validado Blender/FBX/Unity aislado. NO promovido. Espera aprobación.

Fuente: `ArtSource/NPC/NPCs_Shell_Face_GUARD_WORK.blend` (copia de Face, hash a8ee0572566a68b7; Face intacto 0f32b66ac969cf7e, pose guardada restaurada: 0 huesos distintos).
FBX staging: `ArtSource/_Exports/NPC_Validation/Guard/Guard.fbx` (sha 553d10a494b863aa).

## Problema reparado
Hombreras (`Grd_BoardCloth`): 14 vértices del borde interior (lado cuello; 8 izq. + 6 der.) estaban a z 0.53–0.58 (altura del muslo) en vez de en el hombro (el rayo de construcción cayó por la abertura del cuello). En reposo quedaban ocultos dentro del torso; al animar (Walk) aparecía una tira naranja de ~25 cm cruzando la chaqueta y fragmentos en el muslo. Clase B (geometría) + A (pesos de muslo).
Reparación (`Tools/npc_pipeline/fix_grd_epaulette.py`): esos 14 vértices conservan (x,y) y suben a la z del vértice válido más cercano de la hombrera (1.52–1.56); pesos copiados de ese vértice (neck/spine/clavicle). Basis y 9 keys por igual. Nada más cambia (diff: 14 vértices, 14 con pesos, UV 0, key-deltas 0).

## No modificado deliberadamente
- Capas chaqueta/pantalón: en reposo 31/19 vértices (16/40 mm), Walk hasta ~48 mm y poses extremas hasta ~53 mm; en render con culling solo quedan motas de pocos píxeles en el borde del faldón y el pantalón asoma bajo el dobladillo. Sin defecto visible → documentado.
- Penetración piel/ropa: reposo 0.18 mm; stress (cuello 33 mm, antebrazo 24 mm) son poses imposibles; clips ≤8 mm en cabeza/cuello (OneHipRight f16, OneHipLeft f1).
- 5 caras traseras duplicadas del medallón (`Grd_MedalGold`, misma terna de vértices, winding opuesto, preexistentes en Face): el exportador FBX conserva la frontal y descarta la trasera (oculta contra la chaqueta). Por eso el validador marca `faces 7679 vs 7684` (Unity: 9867 tris vs 9872 en Blender).
- Vértices coincidentes 6806/6808 (chaqueta) con pesos distintos (dif 0.084): preexistente; el validador los confunde al emparejar por posición → falso FAIL `weights`. La deformación real coincide (ver abajo).
- Tie/radio difieren de producción actual (el FBX de producción es anterior); la corbata de Face es más limpia.

## Validación
- Audit: 6821 v, 7684 caras, 0 ngons, 4 influencias máx., 55 deform, eye_L/eye_R/eye_aim, 9 keys, 0 correctivas, 31 materiales usados.
- FBX: validador sin FAIL salvo los 2 explicados arriba (`faces`, `weights`: ambos por duplicados/coincidentes preexistentes).
- Blender vs FBX (Rest, 12 poses, Walk 1/3/15/35/40, 9 keys): máx 0.031 mm.
- Unity aislado (`Assets/_Dev/NpcValidation/Guard/`): importa sin errores/warnings, Humanoid válido, 55 bones, 9 blendshapes, 31 materiales Painterly (remap a producción, solo lectura), sin nulos. Renders prod vs nuevo (bind, Walk 0.25/0.6, delante/detrás): sin tira. Sin Play mode ni luz del museo.

## Regresión
Face, Test, Gentleman, Student, FBX/prefab/.meta de producción de Guard sin cambios (mtime anterior a hoy); sin tocar materiales, shader, NpcImportTool, export_shell11.py, build_shell_test.py. `render_pose_sheet.py` ampliado con nombres de acción para Grd y otros prefijos.
Sin probar: correctivas (0), iluminación/Descoloración del museo con Guard.

## Promoción a producción (2026-10-26)
- `promote_npc.py --npc Guard`: prueba en seco (falsos FAIL conocidos `faces`/`weights` aceptados), `--prepare-meta`, `--apply --confirm Guard`, `--mark-promoted`. FBX de producción = staging (sha 553d10a494b863aa).
- Backup original: `ArtSource/_Backups/Guard_prod_before_20261026_172951/` (rollback); `.meta` previo al remap: `Guard_meta_before_20261026_172907/`.
- Cambio en el .meta: remap `NPC_MouthInside` → material compartido. `Grd_TieStripe2` no tiene remap ni material: slot vacío (0 caras) que ya existía en producción; Unity lo descarta (31 slots).
- Verificación en Unity: `Grd_Mesh` 23230 v, 9 blendshapes, 55 bones (con eye_L), 31 slots sin nulos (todos M_*), avatar Humanoid válido; prefab `NPC_Guard` con mesh/Animator/AC_Guard (6 clips)/avatar válidos, 55 bones sin nulos; consola limpia.

## Torso interior (2026-10-26)

- Mismo arreglo que Docent: `add_torso_backing.py` (208 caras de piel bajo la ropa, z 1.46 a 0.80, 14 mm por dentro) en la copia de trabajo (backup `..._WORK_BACKUP_before_torso.blend`), re-exportado y promovido. Verificado con `backing_check.py` (el torso no asoma por la ropa; hay vertices sin tela por fuera donde la prenda es abierta: escote, hombros descubiertos).
- Unity: prefab con huesos/slots/avatar validos, sin nulos, consola sin errores. Sin probar en Play.
