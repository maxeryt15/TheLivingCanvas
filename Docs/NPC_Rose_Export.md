# Rose (museum receptionist) — Blender → Unity export

## Files
- Native project: `ArtSource/NPC/MPFB/Rose_MPFB_63_ready_to_export.blend` (full-res `Rose_Base` kept hidden as the MPFB source of truth)
- Unity FBX: `Assets/_TheLivingCanvas/Art/Models/NPC/Rose/Rose_Receptionist.fbx`
- Scripts (rebuild pipeline): `Tools/npc_pipeline/` — `mpfb_lowpoly.py` → `mpfb_clothes.py` → `mpfb_clothes_polish.py` → `mpfb_resolve_clipping.py` → `mpfb_finish.py` → `mpfb_necklace.py` → `mpfb_badge.py` → `mpfb_pockets_buckles.py` (buckles only; pockets were removed by request)

## Verified in Unity (2026-10-19)
- Import as **Humanoid, Create From This Model**: avatar valid, `isHuman = true`.
- 18 SkinnedMeshRenderers, standing height 1.637 m, ~23.7k triangles total (includes the 2.7k-tri enamel pin).
- Not yet verified: an animation clip played on her; materials look in URP.

## Rig
MPFB `game_engine` skeleton, 53 deform bones (`Root`, `pelvis`, `spine_01..03`, `neck_01`, `head`, clavicles/arms/hands/fingers, `thigh/calf/foot/ball`). A-pose bind, no leaf bones.
Weights: body from MPFB (max 4 influences, normalised); clothes copied from the body by nearest surface; hair, bun, hair pin, earrings, glasses, eyes and brows are 100% `head`.

## Materials (flat colours, no image textures yet)
`Skin` and `Hair_Painted` use the vertex-colour attribute `Col` (soft make-up and hair streaks). The Unity material for those two must read vertex colour, otherwise they appear flat grey/white. Blender colours are linear values.

## Unity setup (done 2026-10-19)
- Scene: `NPC_Rose_Receptionist` under `Museum_Interior` at (-2.55, -59.5, 4.15), yaw 90, behind the reception desk. The interior is only active after the player passes `Door_Enter_Museum` (`AreaTransition`), so she is not visible from outside; this is expected.
- Materials: `Assets/_TheLivingCanvas/Art/Materials/NPC/Rose/M_Rose_*.mat`, shader `TLC/Painterly`. The shader got an opt-in `_UseVertexColor` toggle, ON only for `M_Rose_Skin` and `M_Rose_Hair_Painted`.
- FBX must be exported with vertex colours as LINEAR (`colors_type='LINEAR'`); sRGB makes skin and hair look washed lilac.
- Animation: `Rose_Idle.anim` + `AC_Rose.controller`. The clip is built from the avatar's own rest pose (root curves + all 95 muscles). A clip with only a few muscle curves makes the humanoid collapse to the floor.
- Checked in Play mode from the player's spawn: she reads clearly at desk distance.

## UVs and textures (done 2026-10-19)
- Rose now has UVs (`UV_Paint`) in three shared atlases (skin, hair, clothes) and baked starting textures; see `Docs/NPC_Rose_Painting.md`. Skin and hair no longer use vertex colour in Unity (`_UseVertexColor` off on the `*_Paint` materials).
- Current file: `ArtSource/NPC/MPFB/Rose_MPFB_66_uv_textured.blend`.

## Known limits
- Textures are the baked flat colours, not yet hand-painted.
- The reception chair overlaps her legs slightly (invisible from the player's side).

## Validation checklist
1. Select the FBX → Rig → Humanoid → Configure: all required bones green.
2. Drop a Humanoid idle/walk clip on an Animator and watch the shoulders, elbows, hips and knees.
3. Check the `Skin` and `Hair_Painted` materials show vertex colour.
4. Check scale: she must stand 1.65 m against the 1.8 m player.
5. Known small flaws: a pink skin peek at the hip crease when the thigh is raised high; arms raised above ~150° make the cardigan sleeve touch the blouse.
