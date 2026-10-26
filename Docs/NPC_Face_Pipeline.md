# Pipeline oficial de NPCs desde Face (Fase 1)

Flujo: `ArtSource/NPC/NPCs_Shell_Face.blend` (maestro) → `export_face_official.py` → `ArtSource/_Exports/FaceOfficial/<NPC>/` (staging) → `validate_face_official.py` → (futuro, explícito) promoción → `Assets/`.

## Scripts (Tools/npc_pipeline)
- `export_face_official.py`: solo lee Face, solo escribe en staging (se niega a escribir en rutas con componente `assets`). Nunca guarda el .blend y comprueba que su hash no cambió.
  - `--npcs Gen,Stu` | `all --confirm-all`; `--out <dir>`; `--check-only`.
  - Guardas (abortan, no reparan): archivo exacto Face; 11 NPCs; 56 huesos/55 deform/eye_L/eye_R/eye_aim; 9 shape keys faciales; geometría (sin ngons, sin NaN/Inf, UVs, color attrs, ≤4 influencias, pesos válidos); materiales.
  - Pose: Face guarda una pose NO neutra. Se captura el estado, se hace `pose_lib.reset`, se verifica reposo, se exporta y se restaura el estado exacto (aborta con FATAL si no se puede garantizar).
  - Correctivas: se exportan al FBX con valor 0 (probado con Gardener: 29 keys = 9 faciales + 20 correctivas + Basis). Los drivers no viajan al FBX.
  - Salida por NPC: `<Fbx>.fbx`, `.fbm`, `Textures/`, `materials.json`, `manifest.json` (sha256 fuente y FBX, ajustes, checks, `promoted: false`).
- `validate_face_official.py` (solo lectura): compara el FBX de staging contra Face en reposo (vértices, caras, UV, pesos, huesos, grupos, keys, materiales), prueba que la pose guardada no se horneó, y con `--ref` compara contra otro FBX.

## Diseño de promoción (NO implementado)
Herramienta por NPC, nunca batch destructivo:
1. Precondiciones: manifest con `promoted:false`, hash del FBX = manifest, validador sin FAILs, hash de Face = el del manifest.
2. Diff contra producción (vértices, huesos, keys, materiales, slots) mostrado al usuario.
3. Confirmación explícita del usuario por NPC.
4. Backup de FBX + `.meta` de producción en `ArtSource/_Backups/<NPC>_prod_before_<fecha>/` con hashes.
5. Copiar FBX (y texturas VG2 si cambian) conservando el `.meta` existente (humanDescription, externalObjects).
6. Post-verificación en Unity: importa sin errores, avatar válido y humanoide, mismos huesos/slots, material remaps intactos, prefab sin overrides rotos.
7. Rollback: restaurar FBX + `.meta` desde el backup y reimportar.
8. Marcar `promoted: true` y fecha en el manifest solo tras 6.
Sin tocar `NpcImportTool` ni `export_shell11.py`.

## Política de `NPC_MouthInside`
- Todos los FBX de Face llevan el slot `NPC_MouthInside` (último). Unity debe usar UN solo material compartido `Art/Materials/NPC/Gentleman/M_NPC_MouthInside.mat` (hoy vive en la carpeta de Gentleman).
- El mapeo se hace con `externalObjects` en el `.meta` de cada FBX (remap `NPC_MouthInside` → ese material). Al promover otro NPC, hay que añadir esa entrada a su `.meta`; no crear un `.mat` por NPC.
- Riesgo: `NpcImportTool` ("Import Batch (10)") regenera materiales por prefijo y reescribe remaps y prefabs; podría crear un `M_NPC_MouthInside` duplicado por NPC o borrar la referencia ya existente de Gentleman. Por eso no se ejecuta el batch tras promover; la promoción por NPC copia el `.meta` correcto y no pasa por el batch. Cambiar `NpcImportTool` (fuera de esta fase) sería lo ideal: remap fijo al material compartido.
- Mover el material a una carpeta común (`Materials/NPC/Shared/`) es recomendable pero requiere actualizar el remap de Gentleman: decisión pendiente del usuario.
