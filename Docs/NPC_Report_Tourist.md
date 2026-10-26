# Informe Fase 2 — Tourist (2026-10-26)

Estado: diagnosticado, 1 reparación mínima, validado Blender/FBX/Unity aislado. NO promovido. Espera aprobación.
Fuente: `ArtSource/NPC/NPCs_Shell_Face_TOURIST_WORK.blend` (copia de Face; Face intacto; backup `..._TOURIST_WORK_BACKUP_before_strap.blend`). FBX staging: `ArtSource/_Exports/NPC_Validation/Tourist/Tourist.fbx` (sha ad4487b7cfc925b2).

## Diagnóstico
- Audit: 5383 v, 6698 caras, 0 ngons, 37 materiales (4 sin caras: BagPinA/B/C/Pom → 33 slots en Unity), 39 keys (9 faciales + 30 correctivas con driver), 55 huesos, pesos normalizados. Prendas: camiseta de tirantes + shorts (sin falda: no aplica cierre inferior), bolso, cámara.
- Penetración piel/ropa en reposo −3,7 mm. Barrido de poses: picos 20–33 mm en poses de estrés extremas (upperarm_l HandsOnHips frame 1, rotaciones de 90°), no visibles en renders.
- Bolso/cámara/sandalias vs prenda (`layer_scan`): Idle −5 mm, Walk ≤14 mm, Sit −27 mm (1 vértice), BendForward −28 mm (6 vértices). Sin hundimientos visibles; el bolso lateral queda junto a la cadera sentada.
- **Defecto A/E real:** `Tou_BagStrap` (tira del bolso): 34 de 37 caras orientadas hacia la camiseta → con backface culling (Unity) la tira desaparece casi entera (en Blender sin culling no se nota). Mismo defecto que Student.

## Reparación (única)
`fix_tou_strap.py`: voltea SOLO las 34 caras de la tira a <10 mm de la camiseta con normal hacia ella. No cambia vértices, UV, pesos ni shape keys. Verificado con render CULL=1 (tira visible en Idle y BendForward). Log `reports/fix_strap.json`.

## Sin modificar (residuos)
- Cintura en BendForward extremo: con culling se ve un hueco fino entre dobladillo de la camiseta y cintura del short (piel plegada). Pose extrema, no corregido.
- 81 caras duplicadas de signo opuesto en BagStar0-4 (calcomanías de estrellas): el FBX conserva una por par (en ~86 % la cara exterior) → el validador marca `faces 6617 vs 6698` como falso FAIL (mismo caso conocido).

## Validación
- Validador: único FAIL = `faces` (duplicados anteriores, falso). Resto OK: 5383 v, UV, 37 materiales, 55 huesos, pesos 0 dif, reposo exportado.
- Blender↔FBX: Rest 0 mm; ArmsUp_R/ElbowBend_R/ShoulderCross_L/Twist/HeadDown ≤0,003 mm; Sit/Crouch/Hip y Walk difieren 15–65 mm = correctivas Hip_Flex/Leg_Abduct/Shoulder_Up con driver que no se exportan a Unity (valor 0), mismo caso que Cafe.
- Unity aislado (`Assets/_Dev/NpcValidation/Tourist/`): Humanoid válido, 55 bones, 39 blendshapes, 33 slots sin nulos (remap a `M_Tou_*` + `M_NPC_MouthInside` compartido), consola sin errores. Sin render en Unity.

## Regresión
Face, Test, Gentleman y demás NPCs, y FBX/prefab/.meta de producción de Tourist sin cambios.

## Corrección 1 — residuos (2026-10-26)
Pedido del usuario: retocar los residuos. Backup previo: `NPCs_Shell_Face_TOURIST_WORK_BACKUP_before_residuals.blend`. FBX nuevo sha 19415cccaa69b66b.
- **Estrellas del bolso** (`fix_tou_stars.py`): 164 caras de BagStar0-4 estaban orientadas hacia dentro del bolso (87 sueltas + 77 mitades de pares duplicados) → invisibles con culling. Volteadas (solo las que están sobre la superficie y miran hacia dentro según la normal del bolso y su centro). Nº de caras/vértices intacto. En el FBX reimportado, 256/277 caras de estrella miran hacia fuera (antes ~58 %).
- **Cintura** (`fix_tou_waist.py --drop 0.04 --out 0.004 --wmix 0.6`): no hay piel en la espalda bajo la ropa y la camiseta y el short topaban sin solape → rendija visible ya en reposo desde atrás. El lazo inferior de la camiseta (58 vértices, ½ peso en el anillo vecino) baja 40 mm y queda ≥4 mm por fuera del short, con pesos mezclados 60 % con los del borde del short. Idle cerrado; Sit/BendForward/Crouch quedan con una rendija mínima (antes un hueco ancho).
- Validador: único FAIL = `faces` (duplicados, falso). Blender↔FBX: Rest 0 mm, mismas diferencias por correctivas que antes. Unity aislado: Humanoid válido, 55 bones, 39 blendshapes, 33 slots sin nulos, consola sin errores.

## Corrección 2 — huecos de cintura rellenados (2026-10-26)
Pedido: rellenar los huecos de la cintura en vez de dejar rendija al sentarse/agacharse/inclinarse. Backup: `..._TOURIST_WORK_BACKUP_before_band.blend`. FBX sha f659e0d27f822a6a.
- `fix_tou_band.py --h 0.06 --inset 0.014`: se extruye el borde superior del short (34 vértices) 60 mm hacia arriba, bajo la camiseta, metido 14 mm hacia el eje. Los 34 vértices nuevos (+34 caras, material `Tou_clothes_Paint`) heredan pesos y shape keys de su vértice de origen, acompañan al short y tapan el hueco cuando la camiseta sube. Probé primero un puente (bridge_loops, sobresalían triángulos) y un manguito de piel (parches color piel visibles sobre el short): descartados.
- Renders con culling (Idle, BendForward, Sit, Crouch, desde atrás): sin hueco en ninguna.
- Totales ahora: 5417 v, 6732 caras. Validador: único FAIL `faces` (81 duplicados de estrellas, falso). Blender↔FBX igual que antes (Rest 0 mm; diferencias solo por correctivas). Unity aislado: 33 slots sin nulos, 39 blendshapes, Humanoid válido, consola limpia.

## Promoción a producción (2026-10-26)

- Hash FBX: f659e0d27f822a6a. Backup original: `ArtSource/_Backups/Tourist_prod_before_20261026_174149/`; backup del .meta: `Tourist_meta_before_20261026_174117/`.
- Se añadió el remap de `NPC_MouthInside` al material compartido (Gentleman/M_NPC_MouthInside.mat).
- Los slots `Tou_BagPinA/B/C` y `Tou_BagPom` no tienen material en disco ni remap. Ya existían en el FBX de producción anterior; Unity los descarta (0 caras), no salen en la lista de materiales del renderer y no hacen daño.
- Unity: Tou_Mesh 19641 vértices, 39 blendshapes (9 de cara + 30 extra, probablemente correctivas sin driver en Unity), 55 huesos sin nulos (con eye_L), 33 slots sin nulos, avatar Humanoid válido, prefab NPC_Tourist válido con AC_Tourist (6 clips). Consola sin errores.
- El FAIL `faces` del validador es el falso positivo conocido (caras duplicadas de sentido opuesto).

## Corrección de cadera y re-promoción (2026-10-26)

- Problema (visto por el usuario en Unity): al caminar, la piel de la cadera derecha asoma sobre el short junto a la correa de la cámara. Causa: los correctivos con driver (`Corrective_*_Hip_Flex_*`) no se exportan y valen 0 en Unity; en Blender tapaban el fallo.
- Arreglo: `Tools/npc_pipeline/fix_tou_hip.py --inset 0.025` hunde ~56 vértices de piel bajo la ropa (28 + vecinos a mitad, más una segunda pasada de 2 cm para los que seguían asomando), con el mismo desplazamiento en todas las shape keys. Backup de la copia de trabajo: `ArtSource/NPC/NPCs_Shell_Face_TOURIST_WORK_BACKUP_before_hip.blend`.
- Nuevo hash FBX: 86ebf137a159e339. Backup del FBX anterior de producción: `ArtSource/_Backups/Tourist_prod_before_20261026_182325/`.
- Unity: Tou_Mesh 19667 vértices, 39 blendshapes, 55 huesos sin nulos, 33 slots sin nulos, avatar Humanoid válido, prefab con AC_Tourist (6 clips). Consola sin errores.
- Lección: validar cada NPC también con los correctivos silenciados (`Corrective_*` mute), que es lo que se ve en Unity.

## Camiseta hacia fuera y re-promoción (2026-10-26)

- Medición con correctivos silenciados: 1-2 vértices de la camiseta quedaban 3-4 mm hundidos en la banda del short al caminar. `Tools/npc_pipeline/fix_tou_tank.py --delta 0.007` saca la camiseta 7 mm en z 0.93-1.12 (206 vértices, mismo desplazamiento en todas las shape keys); tras el arreglo la medición da 0 hundidos en todos los frames. Backup de la copia de trabajo: `NPCs_Shell_Face_TOURIST_WORK_BACKUP_before_tank.blend`.
- Nuevo hash FBX: 135de1a3bae0b29c. Backup del FBX anterior: `ArtSource/_Backups/Tourist_prod_before_20261026_183634/`.
- Unity: Tou_Mesh 19673 vértices, 39 blendshapes, 55 huesos sin nulos, 33 slots sin nulos, avatar Humanoid válido, prefab con AC_Tourist (6 clips). Consola sin errores.

## Torso interior (2026-10-26)

- Mismo arreglo que Docent: `add_torso_backing.py` (208 caras de piel bajo la ropa, z 1.46 a 0.80, 14 mm por dentro) en la copia de trabajo (backup `..._WORK_BACKUP_before_torso.blend`), re-exportado y promovido. Verificado con `backing_check.py` (el torso no asoma por la ropa; hay vertices sin tela por fuera donde la prenda es abierta: escote, hombros descubiertos).
- Unity: prefab con huesos/slots/avatar validos, sin nulos, consola sin errores. Sin probar en Play.
