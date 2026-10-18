# The Living Canvas

Unity 6 (6000.3.25f1) + URP 17.3. Escena construida por código con `Assets/_TheLivingCanvas/Editor/StudioSceneBuilder.cs`.
Decisiones de diseño en `Docs/Decisiones.md`; plan de fases en `Docs/PromptMaestro.md`. Texto del juego visible al jugador: siempre en inglés.
**El juego es solo en primera persona** (sin 3ª persona ni cámara contextual): tenlo en cuenta en cámara, interacción, UI y arte.

## Dirección artística (OBLIGATORIO)
Antes de trabajar en **arte, materiales, shaders, iluminación, postprocesado o escenas**, lee `ART_DIRECTION.md` (raíz del repo) y úsalo como criterio.
Reglas clave: texturas pintadas a mano por el usuario, shaders que las complementan (no las sustituyen), Descoloración ≠ filtro de grises,
fases pequeñas con aprobación del usuario entre fases importantes, sin framework grande antes de validar en una escena pequeña.

## Referencia narrativa (OBLIGATORIO)
Antes de trabajar en **historia, personajes, diálogos, niveles, dirección artística o música**, lee `LORE_BIBLIA_DEL_JUEGO.md` (raíz del repo) y úsalo como criterio para mantener la continuidad narrativa. Distingue siempre entre hechos establecidos, propuestas narrativas y detalles todavía abiertos. No conviertas ideas sugeridas en canon sin aprobación del usuario.

## Blender (OBLIGATORIO)
Before performing any Blender modeling task, read `Blender/blender_modeling_guidelines.md`. When the task involves NPCs, also read `Blender/npc_modeling_guidelines.md`. When it involves props, read `Blender/props_guidelines.md`. When it involves environment/scene dressing, read `Blender/environment_guidelines.md`. The existing museum interior and exterior are already modeled and must be treated as the source of truth. Do not rebuild or redesign them unless explicitly instructed.
