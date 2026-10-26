# Rose — hand-painting guide

Rose now has UVs and three paint-ready texture sheets (the current flat colours baked in as a starting point).

| Sheet | Size | Covers | Guide (UV wireframe, paint under it) |
|---|---|---|---|
| `ArtSource/NPC/Textures/T_Rose_skin.png` | 2048 | face, neck, hands, forearms (face has ~3.5x the texel density of the hands) | `UVGuide_Rose_skin.png` |
| `ArtSource/NPC/Textures/T_Rose_hair.png` | 1024 | hair, bun | `UVGuide_Rose_hair.png` |
| `ArtSource/NPC/Textures/T_Rose_clothes.png` | 2048 | cardigan (olive + dark trim), blouse, collar, trousers, shoes | `UVGuide_Rose_clothes.png` |

Not on a sheet (flat colours, tiny): gold items, glasses, eyes, brows, buttons, badge, sunflower pin, shoe buckles.

## Workflow
1. Open `ArtSource/NPC/MPFB/Rose_MPFB_66_uv_textured.blend` in Blender → Texture Paint mode. Each group already uses a material (`Rose_Skin_Paint`, `Rose_Hair_Paint`, `Rose_Clothes_Paint`) with the sheet loaded, so you can paint straight on the 3D model, or in any 2D tool using the UV guide as a layer.
2. Save the PNG over the same file in `ArtSource/NPC/Textures/`.
3. Copy it over `Assets/_TheLivingCanvas/Art/Textures/NPC/Rose/T_Rose_<name>.png` (same filename). Unity picks it up; the materials `M_Rose_Skin_Paint`, `M_Rose_Hair_Paint`, `M_Rose_Clothes_Paint` already point to these files.
4. Do not move or rescale UV islands after painting; if the model changes, the UVs must be regenerated and the paint would not match.

## Notes
- Layout was made by direction-based projection (front/back/side islands per part), so the face is one large front island: easy to paint.
- Seams are where the garment pieces split (visible in the guide). Paint across seams carefully or paint in 3D mode.
- Texture style target: subtle Post-Impressionist brush variation; the `TLC/Painterly` shader's brush map adds light breakup on top.
