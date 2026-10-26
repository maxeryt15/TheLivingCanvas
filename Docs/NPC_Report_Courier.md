# Informe Fase 2 — Courier (2026-10-26)

Estado: reparado en copia de trabajo, validado Blender/FBX/Unity aislado. NO promovido. Espera aprobación.

Fuente: `ArtSource/NPC/NPCs_Shell_Face_COURIER_WORK.blend` (copia de Face; Face intacto 0f32b66ac969cf7e; pose guardada restaurada). FBX staging: `ArtSource/_Exports/NPC_Validation/Courier/Courier.fbx` (sha 40399f52efca7de1).

## Diagnóstico
- Audit: 6802 v, 9839 caras, 0 ngons, 21 materiales, 14 keys (9 faciales + 5 correctivas). Penetración piel/ropa en reposo −4,5 mm; stress/clip de brazo (hasta 12 mm) = poses extremas.
- **Defecto A (pesos) 1: cinturón.** Los vértices delanteros de `Cou_BeltLeather` (spine_03 100 %) no siguen a la ropa: al caminar la cintura se desplaza y el cinturón se hunde hasta 78 mm en la ropa (Walk 5/29/33), 63 mm sentada.
- **Defecto A (pesos) 2: bolsa, herramientas y guantes** colgados del cinturón (pelvis 100 %): al sentarse quedan flotando bajo el muslo y al levantar la pierna la atraviesan.
- Sin defectos de geometría/topología/rig/export.

## Reparación (`Tools/npc_pipeline/fix_cou_props.py`, solo Courier; marca `tlc_props_reweight`)
1. Cinturón (346 verts): pesos = los del triángulo de ropa más cercano (top 4) → sigue a la cadera. Hundimiento: 78→10 mm (como en reposo, 8,6 mm); Sit 63→10 mm.
2. Bolsa/herramientas/guantes: por isla rígida (20 de 26 islas), mezcla hacia thigh_l/thigh_r (según x) con t=(0,92−z)/0,22 (máx. 0,9), mismos pesos en toda la isla → se mueven rígidos con el muslo. Sentada, los guantes/herramientas apoyan en el muslo en vez de colgar.
- Solo pesos (1196 verts distintos vs Face); posiciones, UV y keys sin cambio.
- Residuo: las piezas colgantes siguen rozando el muslo (hasta ~60 mm en Sit/Crouch en la métrica; apoyo visual aceptable) y 8,6 mm de cinturón en reposo (preexistente).

## Validación
- Validador: único FAIL `weights` = esperado (compara contra Face; los pesos cambiaron a propósito). Resto OK (6802/9839, UV, 21 materiales).
- Blender↔FBX: Rest 0 mm; poses ≤0,001 mm; Walk ≤0,03 mm; ArmsUp_R 47 mm = correctiva con driver (no se exporta; igual que otros NPCs).
- Unity aislado (`Assets/_Dev/NpcValidation/Courier/`): importa sin errores/warnings, Humanoid válido, 55 bones, 14 blendshapes, 21 slots sin nulos (remap a `M_Cou_*` de producción y `M_NPC_MouthInside` compartido). No hice render en Unity.

## Regresión
Face, Test, Gentleman, Student, Guard, Docent, Cafe y FBX/prefab/.meta de producción de Courier sin cambios. Nuevo: `fix_cou_props.py`.

## Adenda: martillo y llave inglesa rehechos (petición del usuario)
- `Tools/npc_pipeline/add_cou_tools.py` (tras `fix_cou_props.py`; marca `tlc_tools`; backup `NPCs_Shell_Face_COURIER_WORK_BACKUP_before_tools.blend`): borra el martillo y la llave antiguos (cajas) y modela nuevos en Cou_Mesh con las guías de props (silueta + detalles visibles).
- Martillo de carpintero: mango eliptico con pomo y 4 estrías (ToolGrip), cuello/ojo, cabeza con collar y cara de golpeo, garra de dos puntas curvas (ToolSteel), presilla de cuero. Llave inglesa: ojal, mango que se ensancha, cuello, cabeza con mandíbula fija y móvil, placa graduada, tornillo sin fin moleteado.
- Separados del cuerpo: cuelgan de una correa de cuero + anilla metálica a 6 cm del cinturón e inclinados 9° hacia fuera.
- Vértices del NPC: 6802→7693; polys 9839→10686. Export (1d24a9e79dee0839): poses ≤0,001 mm, Walk ≤0,03 mm (ArmsUp_R 47 mm = correctiva con driver, como antes). Unity aislado: importa bien (21 slots, humanoide válido).
- Colisión al sentarse (petición): una malla skinneada no puede tener colisión física en el FBX; se resuelve por colocación y pesos. Martillo a 14° (cadera izquierda) y llave a −165° (cadera derecha), 100 % pelvis (rígidos, sin seguir al muslo) y 6 cm hacia fuera: el muslo pasa por dentro de ellos al sentarse en vez de atravesarlos. Medido con `layer_scan.py` (herramientas vs ropa): Sit/Crouch/KneeBend/LegKick_R/Walk 0 vértices dentro (peor Walk13 −5 mm); LegKick_L (patada extrema) 4 vértices, −38 mm. Antes (posición previa, pesos a muslo): Sit −38 mm en 305 vértices.
- Limitación: si se quiere que las herramientas se amolden dinámicamente (rebote, balanceo, colisión real) hace falta un componente en Unity con herramientas como objetos separados; no es posible con la malla fusionada actual. Pendiente de decisión.
- Export final 68fba5d54f61b970; poses ≤0,001 mm, Walk ≤0,03 mm; Unity aislado: 21 slots, humanoide válido.

## Adenda 2: cinturón, bolsa y detalles (petición del usuario)
- `add_cou_tools.py` ahora también rehace el cinturón: banda lisa de 96 segmentos con sección redondeada que sigue la silueta de la ropa (radio por rayos, dilatado y suavizado; ya no queda facetado ni escalonado), hebilla frontal con marco, lengüeta, pasador y cola, y la bolsa de clavos nueva (cuerpo, solapa, broche, clavos con cabeza), movida a la cadera trasera (125°) para no solaparse con el martillo; pesos de bolsa/hebilla 100 % pelvis, cinturón con los pesos de la capa exterior (camiseta) a su altura.
- Medido (herramientas+cinturón+bolsa): Idle −2,5 mm; Sit cinturón 2 vértices < −15 mm (peor −39 mm, pliegue de la propia camiseta delante), bolsa/clavos 0 dentro en todas las poses medidas; Walk ≤ −15 mm.
- Limitación: sentada, el frente de la camiseta se pliega sobre el cinturón y lo tapa en parte (es la deformación de la ropa, no de las piezas).
- Export ab84755a448d9acb (8199 v, 11308 polys); poses ≤0,001 mm, Walk ≤0,03 mm. Unity aislado: 21 slots, humanoide válido.

## Promoción a producción (2026-10-26)

- Hash FBX: ab84755a448d9acb. Backup original: `ArtSource/_Backups/Courier_prod_before_20261026_173719/`; backup del .meta: `Courier_meta_before_20261026_173652/`.
- Se añadió el remap de `NPC_MouthInside` al material compartido (Gentleman/M_NPC_MouthInside.mat).
- Unity: Cou_Mesh 32990 vértices, 14 blendshapes (9 de cara + 5 correctivas sin driver en Unity, valen 0), 55 huesos sin nulos (con eye_L), 21 slots sin nulos, avatar Humanoid válido, prefab NPC_Courier válido con AC_Courier (6 clips). Consola sin errores.

## Torso interior (2026-10-26)

- Mismo arreglo que Docent: `add_torso_backing.py` (208 caras de piel bajo la ropa, z 1.46 a 0.80, 14 mm por dentro) en la copia de trabajo (backup `..._WORK_BACKUP_before_torso.blend`), re-exportado y promovido. Verificado con `backing_check.py` (el torso no asoma por la ropa; hay vertices sin tela por fuera donde la prenda es abierta: escote, hombros descubiertos).
- Unity: prefab con huesos/slots/avatar validos, sin nulos, consola sin errores. Sin probar en Play.
