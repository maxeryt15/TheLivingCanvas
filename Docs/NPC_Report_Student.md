# Informe Fase 2 — Student (2026-10-26)

Estado: reparado en copia de trabajo, validado Blender/FBX/Unity aislado. NO promovido. Espera aprobación.

Fuente: `ArtSource/NPC/NPCs_Shell_Face_STUDENT_WORK.blend` (copia de Face; Face intacto, hash 0f32b66ac969cf7e).
Copia final: hash 3aab62c76d8215d1. FBX staging: `ArtSource/_Exports/NPC_Validation/Student/Student.fbx` (sha e7f81f921aa70013, 633068 bytes).

## Problemas reparados (los dos son reales y medidos)
1. Dobladillo de la camiseta: anillo de 15 vértices (v4630,31,32,37,38,39,40,46,47,48,49,50,53,54,55) 22–38 mm DENTRO del pantalón por detrás y a los lados
   (punta verde visible en la espalda, dientes en el paseo). Clasificación: B (geometría). Reparación: esos 15 vértices movidos a lo largo de la normal del pantalón
   hasta 3 mm por fuera (en Basis y las 9 shape keys por igual). Además 77 vértices del pantalón bajo la camiseta hundidos 6 mm (zona por encima del dobladillo local).
   Pesos sin cambios. Resultado en reposo: camiseta-dentro-pantalón 18→1 verts, pantalón-fuera-camiseta 58→1; Walk (frames 1,9,17,25,33): de 9–21/42–54 a 0–3/0–4.
2. Tira del bolso (Stu_BagStrap): cinta de una sola capa con 28 de 37 caras orientadas hacia la camiseta; con backface culling (Unity) casi desaparece. En Blender sin culling no se veía.
   Clasificación: B (normales/winding). Reparación: 26 caras volteadas (las que están a <10 mm de la camiseta y apuntan hacia ella). Sin cambios de vértices/UV/pesos/keys.

## No modificado deliberadamente
- Capas camiseta/pantalón en poses extremas (BendForward 43/22 verts, Twist_A 39/18, Crouch 3/33 → hasta ~35 mm): inherente a dos capas de baja poli en poses de 90°; mejoró respecto a antes (64/81, 61/79).
- Estiramiento 6x de aristas del pantalón en la entrepierna en Walk (frame 4): sin defecto visible en render; preexistente, igual que en Test/Face.
- Penetración piel/ropa: sin cambios (clip ≤2.1 mm; stress calf 34 mm = pose imposible).
- Esquinas del bolso/auriculares/pulseras: sin defecto.

## Validación
- Blender: audit (4823 v, 6469 caras, 0 ngons, 4 influencias máx., suma pesos 1.0, 0 sin peso, 55 deform, eye_L/eye_R/eye_aim, 9 keys, 0 correctivas).
  Diff Face→copia: 92 vértices movidos, 0 pesos, UV 0, key-deltas sin cambio. Pose guardada de Face restaurada exacta (0 de 56 huesos distintos).
- FBX: 55 huesos, 9 blendshapes, 25 materiales, validador sin FAIL. Blender vs FBX en 12 poses + Walk 1/3/15/35/40 + 9 keys: máx 0.026 mm.
- Unity aislado (`Assets/_Dev/NpcValidation/Student/`): importa sin errores/warnings, Humanoid válido, 55 bones, 9 blendshapes, 25 materiales TLC/Painterly (remap a materiales de producción, solo lectura),
  render bind/Walk prod vs nuevo: tira completa, dobladillo limpio, blink/open/smile/frown correctos. Sin Play mode; iluminación del museo NO usada (luz de preview).

## Regresión
Sin cambios en: Face, Test, Gentleman, FBX/prefab/.meta de producción de Student, materiales, shader, NpcImportTool, export_shell11.py, build_shell_test.py.
Sin probar: Descoloración/iluminación real del museo con Student; correctivas (Student tiene 0).

## Addendum — correa del bolso reconstruida (2026-10-26)
Pedido del usuario: la correa debe ser un modelo uniforme, no bloques cuadrados. Los 37 quads planos (sombreado flat) se reemplazaron por una cinta continua de 74 quads (75 peldaños, ancho 30 mm constante):
spline Catmull-Rom sobre los bordes originales x2, suavizado con extremos (bolso) fijos, separación mínima 3 mm con la camiseta, caras lisas, normales hacia fuera.
Pesos: de la camiseta más cercana (100 % a <8 mm, mezcla hasta los originales a >20 mm en los extremos del bolso); máx. 4 influencias.
Resultado (strap_scan): caras de la correa dentro de la camiseta en Walk 9–11/37 → 0–2/73; poses extremas (BendForward) hundimiento máx. 46 mm → 4.6 mm. Script: `Tools/npc_pipeline/fix_stu_strap_rebuild.py --shirtw`.
Backup previo: `ArtSource/NPC/NPCs_Shell_Face_STUDENT_WORK_BACKUP_before_strap_rebuild.blend` (3aab62c76d8215d1). Copia de trabajo ahora fc1876826059eba6; FBX staging 1f778cd077c8b300 (4897 verts, 6506 caras).
Validación: validador sin FAIL, Blender vs FBX ≤0.026 mm en poses/Walk/keys, Unity aislado y museo (patio, Descoloración 0/1) correctos, producción sin tocar.

## Promoción a producción (2026-10-26)
- Herramienta: `promote_npc.py --npc Student` (`--prepare-meta`, `--apply --confirm Student`, `--mark-promoted`). FBX de producción = staging (sha 1f778cd077c8b300).
- Backup original: `ArtSource/_Backups/Student_prod_before_20261026_172727/` (FBX 957174936493c52f + .meta; **usar este para rollback**). Existe un segundo backup redundante `..._172739` (ejecución repetida accidental; contiene ya el FBX nuevo) y `Student_meta_before_20261026_172609/` (.meta antes del remap).
- Cambio en el .meta: remap `NPC_MouthInside` → `M_NPC_MouthInside.mat` compartido (Gentleman).
- Verificación en Unity: malla `Stu_Mesh` 18707 v, 9 blendshapes, 55 bones (incl. eye_L/eye_R), 25 slots sin nulos (boca = material compartido), avatar Humanoid válido; prefab `NPC_Student` con mesh/Animator/AC_Student (6 clips)/avatar válidos, 55 bones sin nulos, root `Root`; consola sin errores.

## Torso interior (2026-10-26)

- Mismo arreglo que Docent: `add_torso_backing.py` (208 caras de piel bajo la ropa, z 1.46 a 0.80, 14 mm por dentro) en la copia de trabajo (backup `..._WORK_BACKUP_before_torso.blend`), re-exportado y promovido. Verificado con `backing_check.py` (el torso no asoma por la ropa; hay vertices sin tela por fuera donde la prenda es abierta: escote, hombros descubiertos).
- Unity: prefab con huesos/slots/avatar validos, sin nulos, consola sin errores. Sin probar en Play.
