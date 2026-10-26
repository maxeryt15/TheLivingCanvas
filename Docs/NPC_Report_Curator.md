# Informe Fase 2 — Curator (2026-10-26)

Estado: reparado en copia de trabajo, validado Blender/FBX/Unity aislado. NO promovido. Espera aprobación.
Fuente: `ArtSource/NPC/NPCs_Shell_Face_CURATOR_WORK.blend` (copia de Face; Face intacto). FBX staging: `ArtSource/_Exports/NPC_Validation/Curator/Curator.fbx` (sha 6ea1947519dd8d09).

## Diagnóstico
- Audit: 5975 v, 7033 caras, 0 ngons, 23 materiales, 14 keys (9 faciales + 5 correctivas Spine_Bend con driver). Penetración piel/ropa en reposo +0,5 mm (nada penetra).
- **Defecto de topología (C) — falda abierta por abajo:** el dobladillo (42 vértices, z 0,52) es un borde abierto; al caminar/sentarse la falda se abre y se ve el interior (colas y astillas del forro en Walk 13/33, hueco entre piernas sentada).
- Clips piel/ropa y capas chaqueta-falda (hasta 47 mm en patadas, 15–23 mm caminando): poses extremas / solape normal chaqueta sobre falda, sin hundimientos visibles en los renders con culling. Estiramiento de aristas: máx. 5x en Walk (preexistente, similar a otros NPCs). Dos vértices coincidentes en la solapa (49x) = costura de la solapa, no visible.

## Reparación (`Tools/npc_pipeline/add_hemcap.py`, versión genérica de add_caf_hemcap; marca `tlc_hemcap`)
Pedido por el usuario para Cafe y extendido a Curator: tapa el dobladillo con un disco del mismo material (`Cur_clothes_Paint`): 3 anillos interiores + centro, UV/color copiados del dobladillo, pesos mezclados hacia thigh_l/thigh_r (reparto lateral), y la falda por delante (135 vértices) repondera hacia los muslos para que al sentarse repose plana sobre las piernas y de frente sea simétrica. 168 caras nuevas; posiciones existentes sin cambio.
Render: sentada (perfil/frente) cerrada sin ver el interior; Walk sin colas ni astillas.

## Validación
- Blender↔FBX: Rest 0 mm; poses ≤0,002 mm; Walk ≤0,024 mm; Crouch/BendForward 50–57 mm = corrective Spine_Bend con driver (no se exporta; igual que otros NPCs).
- Unity aislado (`Assets/_Dev/NpcValidation/Curator/`): sin errores/warnings, Humanoid válido, 55 bones, 14 blendshapes, 23 slots sin nulos (remap a `M_Cur_*` y `M_NPC_MouthInside` compartido). Sin render en Unity.

## Regresión
Face, Test, Gentleman, Student, Guard, Docent, Cafe, Courier y FBX/prefab/.meta de producción de Curator sin cambios. Nuevo: `add_hemcap.py`.

## Adenda: falda sentada recta (petición del usuario)
Al sentarse, el dobladillo frontal formaba una V con el disco convergiendo a un punto cerca del borde. `add_hemcap.py` ajustado: el reparto lateral muslo izq/der de la falda frontal es más ancho (`--bw` 0,10) y solo afecta a la falda (z<0,78, 95 vértices; antes tocaba también la chaqueta); el disco y sus anillos convergen al centroide de los pesos del anillo (en vez de a un muslo) y se sombrean planos. Resultado: línea de dobladillo frontal recta/continua sentada; Walk sin atravesar la pierna (probado también `--bw 50`: borde totalmente recto pero la pierna atraviesa la falda al caminar; descartado).
Export 62ea229506ff1673: Rest 0 mm, poses ≤0,002 mm, Walk ≤0,024 mm. Unity aislado importa bien (23 slots, humanoide válido). Sin promover.
- Corrección 2 (usuario: "todas las líneas se unen en un punto, quiero simetría y orgánico"): el centro del disco ya no es un abanico a un vértice polar; `add_hemcap.py` rellena el último anillo con `triangle_fill` (sin polo), pesos = promedio del dobladillo, sombreado plano. Export a328f694aa54bc72 (6101 v / 7199 polys): Rest 0 mm, Sit ≤0,001 mm, Walk ≤0,024 mm; Unity aislado OK (23 slots, humanoide válido). Nota: el mismo polo existe en el disco de Cafe (`add_caf_hemcap.py`, ya aprobado); no se tocó.
- Corrección 3 (usuario: "usa la misma que usaste en Cafe"): `add_hemcap.py -- Cur --cafe` = método idéntico al de Cafe (reparto lateral a muslos con ancho 0,04, falda delantera z<0,95, disco de 3 anillos + centro en abanico, sombreado suave). Sustituye a la versión sin polo. Export (ver manifest): Rest 0 mm, Sit ≤0,001 mm, Walk ≤0,024 mm.

## Promoción a producción (2026-10-26)

- Hash FBX: d4547ea3db768184. Backup original: `ArtSource/_Backups/Curator_prod_before_20261026_173838/`; backup del .meta: `Curator_meta_before_20261026_173816/`.
- Se añadió el remap de `NPC_MouthInside` al material compartido (Gentleman/M_NPC_MouthInside.mat).
- Unity: Cur_Mesh 22103 vértices, 14 blendshapes (9 de cara + 5 extra, probablemente correctivas sin driver en Unity), 55 huesos sin nulos (con eye_L), 23 slots sin nulos, avatar Humanoid válido, prefab NPC_Curator válido con AC_Curator (6 clips). Consola sin errores.

## Torso interior (2026-10-26)

- Mismo arreglo que Docent: `add_torso_backing.py` (208 caras de piel bajo la ropa, z 1.46 a 0.80, 14 mm por dentro) en la copia de trabajo (backup `..._WORK_BACKUP_before_torso.blend`), re-exportado y promovido. Verificado con `backing_check.py` (el torso no asoma por la ropa; hay vertices sin tela por fuera donde la prenda es abierta: escote, hombros descubiertos).
- Unity: prefab con huesos/slots/avatar validos, sin nulos, consola sin errores. Sin probar en Play.
