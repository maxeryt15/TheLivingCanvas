# NPC lessons learned (from Rose, the first NPC)

Read this before starting any new NPC. Each item is a mistake made on Rose, how the user corrected it, and the rule to follow next time.

## 1. Process and communication
- **Looked at the wrong thing and called it done.** Several times I reported a change as finished when the user then saw a flaw (gaps, floating hair, holes, bald spot, jagged edges). Rule: after every change, zoom into the exact area from at least 4 angles (front, 3/4 both sides, back, side) before saying it is done. Check material shading, not only wireframe. Say plainly what was NOT checked.
- **Ignored or half-followed what the user drew.** The user sent annotated screenshots (red outlines for hair shape, hairline, holes, neck trim). Rule: treat the outline as the spec, rebuild to match it, and compare against it after.
- **Piled patches instead of re-diagnosing.** Hair went through about 15 rebuilds (strips, curls, shell, patches) before using MPFB's own hair asset. Rule: if two attempts fail, stop and change approach (try a library asset or a different method) instead of stacking more patches.
- **Did not offer references early.** The user eventually asked "don't you have examples from MPFB?" Rule: at the start, show a contact sheet of MPFB hair, clothes and eye options and let the user choose.
- **Made destructive changes to approved work.** Cut the hair when adding the bun; user: "you changed her hair... the original shape". Rule: keep a backup of any approved part before editing nearby parts; never alter approved pieces without asking. When a change might be disliked, save a backup and tell the user how to revert (the forehead change worked well this way).
- **Switched the open Blender file by accident.** The user had another .blend open, my script failed on it and left a stray copy. Rule: check `bpy.data.filepath` and `is_dirty` before running scripts; never assume the open file.
- **Long silent stretches.** The user had to wait with no update. Rule: one short status line before multi-step runs.

## 2. Style direction (what the user wanted)
- Low-poly faceted look, but never so low that it looks like a "tinfoil hat". Keep the face expressive.
- Face: an old woman, not a "generic male model". Needed hair, eyes and brows to read as female.
- Hair: soft, smooth, organic, rooted on the scalp, no floating shells, no spiky strands ("looks like a hobo"). Colour as flat low-poly tones.
- Glasses: round, below the eyebrows, not touching eyebrows, nose or hair.
- Clothes: simple clean shapes. Rounded, symmetrical hems; smooth continuous trims; no "cut with scissors" edges. Dark olive tone for trims.
- Accessories asked for: pearl collar (rejected) then gold chain with small cross, sunflower pin as a flat 2D enamel pin, silver badge at heart height, gold earrings, hair bun with pin.
- Pockets: the first attempt was "awful"; the user asked to delete them. Do not add details without a clear reference image.

## 3. Technical mistakes
- **MPFB target changes did nothing at first**: shape-key targets must be loaded before values can be set. Check that a value actually changed.
- **Decimating the whole body made the face a lump.** Decimate head and body separately, head denser.
- **Hair/ear placement**: ears were covered, earrings hidden, then the user wanted a notch, then a swept-back shape. Ask where the ears and earrings should show.
- **Clothes made by offsetting the body surface** gave jagged cuts, torn flaps at the neck, gaps at the hem, hem slits, light slivers. Fix that worked: bisect planes for clean cuts, then EXTRUDE trims straight from the cut edge (never separate strips), smooth the boundary chain, weld seams.
- **Layer order clipping**: body < blouse < trousers < cardigan. Push each outer layer out from the inner ones; do not scale clothes up. Re-run the overlap check (BVH) after every clothes change.
- **Shoes copied from the foot shape** looked bad; a lofted shoe with a sole worked.
- **Weights**: stale vertex-group indices after removing groups crashed the weight code. Rebuild groups cleanly (read names first, rewrite after). Data Transfer needs destination groups pre-created.
- **Vertex colours exported as sRGB** washed out skin and hair in Unity. Export as LINEAR. Blender colour values are linear; pastel values look washed out.
- **Idle clip with only a few muscle curves collapsed the humanoid.** Build the clip from the avatar's own rest pose (all 95 muscles plus RootT/RootQ).
- **UV unwrap**: smart-project at 66° and a joint multi-object pack both produced unusable specks. Use direction-based (cube) projection per part with real-scale UVs, extra density for the face, then area-weighted tiles for each object in a shared atlas.
- **Unity**: `GameObject.Find` skips inactive objects; the museum interior is only active after the player enters, so the NPC looked "missing" in Play. Test by travelling through the door.
- **Placement**: the NPC stood on the customer side of the desk facing away. Check position and facing from the player's view and from above.

## 3b. Added while building the Curator (second NPC)
- **Never enter Unity Play mode without asking the user first.** Test in Edit mode with a temporary camera. (User correction.)
- MPFB clothes add a `Delete.<asset>` MASK modifier on the base that hides the body under them. Switch those off (`show_viewport=False`) before building the low-poly body or the torso vanishes.
- Open strips (lanyard strap) must be double-sided or Unity back-face culling hides them.
- `materials.clear()` resets every face's material index to 0; reassign indices (eyes: white/iris/pupil) afterwards. Copied meshes keep the MPFB material slot; clear it or Unity gets `Cur_Base.*` materials.
- Re-importing an FBX in Unity resets the scene instance (renamed, moved to the origin, animator cleared): re-place and re-assign the controller afterwards.
- In Edit mode the Animator does not pose the model, so the idle pose can't be judged without Play mode: ask first.
- Reusable scripts now in `Tools/npc_pipeline/`: `mpfb_lowpoly.py` (`build`, `lowpoly_object`, `push_out`, `trim_hidden_body`), `npc_accessories.py` (round glasses, lanyard with card, brooch), `npc_rig.py` (`rig_npc`), `npc_uv_bake.py` (`project`, `tile_atlas`, `bake_groups`), `npc_export.py` (`export_npc`).

## 3c. Added during the 10-NPC batch QA pass
- **QA renders must hide the `<prefix>_Base` body.** It is a hidden full-res copy with no material; rendering it z-fights with the low-poly body and looks like speckled skin. `Tools/npc_pipeline/qa.py <Folder> <prefix>` does it right (front/3-4/side/back/pose + head/torso/feet closeups, plus bone-weight, unweighted, influence and overlap checks).
- **Unity Humanoid fails with "Required human bone 'LeftFoot' not found" when no vertex is weighted to `foot_l`/`foot_r`.** Ankle boots were weighted from the low body (feet trimmed) so only `calf` got weight. Footwear now takes weights from the full base body (`npc_rig.rig_npc`).
- **Colour regions chosen by face-centre thresholds leave saw-tooth borders** (shirt V, hems, cuffs, reflective stripes). Cut the mesh first: `split_z` (horizontal planes), `split_planes` / `v_planes` (V openings). Then the region rule follows a clean edge.
- **Layer order in the spec is inner to outer.** List trousers before the top that covers them or the trousers poke through the hem. Boots/shoes use `clear=0.009` when trouser hems overlap them.
- **Hair assets with a fringe cover an eye** (bob02, short03, cortu_short_messy_hair); check the face closeup and swap the asset. `o4saken_curly01` is a long wig, not curls.
- **Icosphere caps/berets need margin** (+0.024 radius, subdivision 3) or hair/skin pokes through the facets; derive size from the hair that is actually used.
- **Apron grid needs a finer ray grid and a bigger offset** (9x16, 0.011) or the dress bulges through at the bust.
- Extreme pose test (arms 70 deg up) still pulls the hem of jackets and tees upward. Not a problem for idle poses; keep arm motion small.
- Tools added: `bl.py` (send code to the live Blender socket on port 9876 when the MCP tools are not connected), `run_stages.py`, `full_build.py`, `qa.py`.

## 3d. Batch of 10 NPCs: review workflow, user corrections, bugs found (2026-10-19)

### Where the batch stands
- Reviewed, approved and exported one by one with the user: Curator, Guard, Student, Gardener, Cafe, Tourist (6 of 10).
- Still to review: Gentleman, Courier, Docent, Painter. Their FBX files exist but were built BEFORE many fixes below, so rebuild each (`python Tools/npc_pipeline/full_build.py <Folder> <spec>`) before reviewing.
- Unity side for the batch (materials from `materials.json`, Humanoid avatar, idle, placement, Play-mode test) is NOT done except the first import test; the user said: do not import into Unity and do not enter Play mode until all 10 models are functional and he says so. Unity materials, FBX importer settings and idle controllers were created for 9 of them during a test and may need redoing after the re-exports.

### Review workflow the user wants (follow it for every remaining NPC)
1. Open `<Folder>_06_final.blend` in the user's Blender (script `$TEMP/show.py` pattern: open file, hide `_Base` meshes, Material Preview, front view) and send the QA sheets (`qa.py`).
2. Give a short list of what I see wrong, then wait for the user's list of changes.
3. PREVIEW BEFORE APPLYING: for any change, build it in a scratch scene (`preview_build.py`, `preview_hair.py`, `render_shots.py`; scratch folder `_Preview_<Folder>`), send the render, say what changed and the doubts, and apply to the real files only after "ok". Exception: when the user says "apply it", or "apply without asking and show me", apply directly and show the result.
4. After applying: rebuild with `full_build.py` (or `run_stages.py`), run `qa.py`, confirm required bones are weighted and nothing is unweighted, show images, report what was not checked.
5. Order inside one NPC that worked: face and body shape, small accessories/props, clothes and colour, hair last (offer 4 candidates with `preview_hair.py`, user picks, then tune).
6. Hair candidates: show 4 assets from the MPFB library with the hat or glasses on, recommend one. Asset names that worked: `littleright_bobcut_hair` (Curator), `elvs_grump_hair` (Guard), `culturalibre_hair_14` (Gardener), `rehmanpolanski_hair_bun_brown` (Cafe), `braid01` (Tourist). Hairs that look like helmets or tinfoil: bob02, short04, blunt bobs. Smoothing vertices of strip hair makes it shrink and go bald; pick another asset instead.
7. Keep answers short, in the user's language (Spanish), caveman style.
8. Never send more than what was asked; ask one question at the end ("apply?" or "next?").

### Corrections the user made (what I did wrong, what he wanted)
- Face: red halo over the upper lip (lipstick done as vertex colour) -> lipstick must be a separate lifted copy of the lip faces (`A.lipstick`), natural skin colour on the lips otherwise.
- Face: wanted unique faces per NPC (tired young woman, hard-jawed old gardener with wrinkles, young cheerful ambitious tourist with a sideways glance, round librarian glasses frames that are small and do not touch face or hair).
- Accessories must fit the character and be well modelled: real tourist camera with lens rings and strap lugs, military medal and rank patches copied from a reference photo, satchel with stars/pins/keychain, gloves modelled from the character's own hand, sandals built around the real foot.
- Straps must connect to the object, rest on the body and never clip. Both sides of a symmetric strap must be identical (mirror one side).
- Boots must cover the trouser hem; delete skin and trousers below the boot rim so nothing overlaps.
- Dirt must read as soft stains, not coloured triangles: paint blurred blobs into the baked texture (`D.paint_stains`).
- Jagged colour borders (shirt V, hems) are not acceptable: they came from the baked texture, so keep that region as its own flat material (`flat_regions`) or cut the mesh first.
- Hair must sit on the head with no gap (hair filler strip), forehead gap, hair covering an eye, braid with a frayed tail (cut it, `cut_z`).
- Wrinkles belong in the texture (`D.paint_wrinkles`), subtle.
- Clipping through the back (skin visible through the dress strap): raise `clear` (0.009) for dresses and suits.

### Bugs found in the pipeline and how they were fixed (do not repeat)
- QA renders showed speckled skin: the hidden full-res `_Base` body must be hidden in renders.
- `Operator ... poll() failed` / `Context has no attribute object` when scripts run after `open_mainfile`: scripts need an active object; `new_scene` and `stage_base` must run in separate calls.
- MPFB coordinates: `base.data.vertices` hold UNSHAPED coordinates. Mixing the active shape keys is required before any nearest-point lookup (lips group, joints, wart/mole placement). Skipping it put the lips, the mole and the lipstick on the wrong spot of the face.
- Humanoid avatar invalid ("LeftFoot not found"): shoes weights come from the full base body.
- Garments took arm weights near the hands and legs weights on the chest: transfer weights with vertex-normal projection (fallback nearest), then `limit_arms` and a "nothing above the hips follows a leg" rule. The extreme pose test (arms 70 degrees up, one leg up) must look right.
- Texture bake showed black holes on the old Curator export: always rebuild through the current factory, never trust old exports.
- Face-centre colour rules leave stair-stepped borders: use `split_z`, `split_planes`, `v_planes`.
- `bmesh` `faces.new` raises "face already exists" for double-sided strips: build the back face from NEW vertices.
- Python heredocs in bash with Windows backslashes break: write helper files with `cat` and forward slashes, or use the Write tool; use `chr(92)` where a backslash is needed in a one-liner.
- Never assume a hair/clothing asset behaves as its name says; look at the render.
- `GameObject.Find`, Play mode: unchanged (never enter Play mode without asking).

### Pipeline tools and spec options added today (all in `Tools/npc_pipeline/`)
- Drivers: `bl.py` (send code to Blender on port 9876), `run_stages.py`, `full_build.py`, `qa.py` (+ extra closeup shots argument), `preview_build.py`, `preview_hair.py`, `render_shots.py`.
- Props: `npc_props.py` (radio, tie, medal, shoulder boards, sleeve patch, satchel, headphones, lapel fold), `npc_props2.py` (straw hat, mustache, straw stalk, hand gloves, apron2, shoe bows), `npc_props3.py` (travel camera, sandals, palm motifs), `npc_accessories.py` (fitted glasses, beauty mark, freckles, lip scar, wart, lipstick), `npc_details.py` (paint_wrinkles, paint_stains, hair_filler, split_planes, make_eyes heterochromia).
- Spec keys: `split_z`, `split_planes`, `flat_regions`, `no_trim`, `shaft_up`, `hide_below`, `stains`, `motifs`, `wrinkles`, `lipstick`, `eye_look`, `eyes2`, `hair.cut_z`, `hair.smooth`, `hair.fringe_lift`, `clear`.

### Known remaining issues (open)
- Guard is not stocky; Tourist shorts are plain; Cafe sole slightly thick at the heel; Gardener boot rim has a small notch on the inner leg.
- Body trim: Painter, Gentleman, Courier, Docent not yet reviewed with the user.
- The Student satchel strap and Cafe apron straps can still be tuned.

## 4. Order that worked (reuse it)
1. Inspect Blender, MPFB and project files first. 2. Base human with MPFB macro values; set height. 3. Face targets (age, eyes, nose, mouth). 4. Low-poly mesh by separate head/body decimation. 5. Eyes, brows, hair from an MPFB library asset, then adapt. 6. Clothes by bisect cuts, extrude trims, resolve clipping. 7. Accessories. 8. Shading pass (normals, duplicates, materials). 9. Rig (MPFB `game_engine` skeleton), weights, pose tests. 10. UVs and baked texture sheets. 11. FBX export (LINEAR vertex colours), Unity import as Humanoid, materials, idle, placement, Play-mode check.
Scripts for steps 4-8 live in `Tools/npc_pipeline/`; see `Docs/NPC_Rose_Export.md` and `Docs/NPC_Rose_Painting.md`.

## 5. Before each NPC: ask the user
- Reference images for face, hair, silhouette and accessories (and where ears, earrings, brows and glasses sit).
- Whether clothes are open or closed, and what details are wanted. No extra details unasked.
- Where the NPC stands and which way she or he faces in the scene.


## 3e. Segunda tanda de revision (Gentleman, Courier, Docent, Painter)
- Modo revision sin exportar: archivo `ArtSource/NPC/NO_EXPORT` => `stage_bake_export` solo guarda `_06_final.blend`. Borrarlo para exportar.
- `preview_full.py` = preview con rig+bake (necesario para ver texturas pintadas: cicatrices de piel, manchas, patrones). `preview_build.py` no hornea.
- Textura con UV proyectadas se solapa: la malla del pantalon que sube dentro del saco mezcla colores (verde/rojo). Solucion: `leg_trim` (corta la parte oculta) y `leg_rule` (toda la pieza = pantalon).
- Rayas: no pintarlas en textura (se estiran, lineas punteadas). Usar cortes de geometria (`split_regions` con planos por region) + materiales planos (specs/painter.py).
- Hueco en V en tobillos del pantalon: `close_notches`. Piel de pies: `hide_below` a la altura del borde del zapato.
- Pelo largo: `hair.filler_zmin/filler_lift` (el relleno de hueco atravesaba la piel), `hair.clear/reach`, `scale.zd` para acortar; `hair_filler(where=, color=)` para lamina negra plana en un hueco (gap_sheet).
- Props nuevos: tool_belt, work_boot_details, brushes_in_apron (npc_props5), mustache(curl=), round_glasses(shape='hex'|'rect', drop=, out=), apron2(back_straps=), neckerchief(off=), paint_skin_scars (cicatrices/manchas en textura de piel), smooth_region.
- Cuerpo clipping: medir con BVH overlap por zona (z/x/y) antes de decidir; no fiarse solo del render.

## 3f. Revision final de irregularidades (los 10)
- Pesos: `limit_legs` (npc_rig.py) mueve a la pierna del mismo lado los pesos de la pierna contraria => adios cunas en pantalones/faldas al levantar una pierna. `limit_arms` ahora r0=0.055,r1=0.095; bolsos/correas/lanyard 0.012/0.035; parches y hombreras 0.03/0.06 (siguen la manga).
- Bake: `fill_bake_holes` rellena texels negros DENTRO de islas UV (triangulos que el bake no pinta); se aplica a skin/hair/clothes en stage_bake_export.
- Pelo: `filler_lift` por defecto 0.004 (el relleno de hueco atravesaba la piel), `hair.clear/reach` empujan el casco de pelo fuera de la cabeza.
- Una 'linea oscura' en el cuello del Gardener era la SOMBRA de la paja en el render, no un defecto del modelo: comprobar con raycast/textura antes de arreglar.
