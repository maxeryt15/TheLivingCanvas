# Prompt: texturizar objetos al estilo Van Gogh / Munch (The Living Canvas)

Copia y pega el bloque de abajo, rellenando lo que está entre `[corchetes]`.

---

```
You are texturing a 3D asset for "The Living Canvas", a first-person painterly game. Goal: make every surface look hand-painted in the style of Van Gogh (primary) with Munch-style ribbons only for Descoloración zones.
Read first: ART_DIRECTION.md, and Blender/blender_modeling_guidelines.md. Do not rebuild or remodel existing geometry unless I say so.

ASSET: [object name / group, e.g. "Prop_Bench_W", "interior corridor walls"]
LOCATION / CONTEXT: [exterior garden / interior gallery / basement ...; mood: cozy, lonely, uneasy ...]
LIGHT: [warm daylight / cold night / lamp-lit ...]
STATE: [normal / affected by Descoloración (reduce saturation + contrast, keep warm/cool differences, do NOT grey-filter)]

HOW TO PAINT (stroke engine in Tools/museum_models/make_painted_textures.py; reuse it, add a maker per new family):
1. Stroke = a bundle of parallel bristle lines with their own tone and height. Height becomes impasto relief (lateral light) and also a bump map. Always export a colour map T_<Family>.png and a height map H_<Family>.png, 1024 px, seamless (wrap-around).
2. Stroke direction follows the form, never random noise:
   - grass, hair, fur: long upward waves in an S, like wind in a wheat field
   - foliage, bushes: short curved strokes spiralling in vortices (Starry Night village trees)
   - cypress / tall dark forms: long flame tongues with thin brown contour lines
   - stone, brick, tiles: one block or tile per region, strokes follow each block's top-to-bottom light; dark blue-violet outline in the joints
   - wood: broad, calm, parallel strokes along the grain; few tones
   - plaster, fabric, paper: wide soft trowel-like dabs, very low contrast
   - metal: thin horizontal drags, dark, with a few rust touches
   - sky / water / Descoloración zones: long flowing ribbons, thinner paint, dark outlines (Munch)
3. Stroke size scales with the object, not the texture: a stroke should be roughly 1-3 cm on props, 5-10 cm on walls, 10-20 cm on ground and foliage. Set the UV mapping scale to get that (1 UV unit = 2 m in the exterior model).
4. Palette per material, 5 colours: dark, base, light, highlight, one accent.
   - base the palette on the project palette (cerulean #526A83, warm yellow #D4A72C, olive #65785A, terracotta #A85F47, grey-blue #747983, aged cream #E0CDB0)
   - keep warm/cool contrast inside every surface; use complementary accents sparingly (<= 3% of strokes)
   - keep saturation moderate; the focal points get the colour, the background stays quiet
   - never fill a surface with random colour noise
5. Calm vs lively: surfaces the player touches or looks at closely (doors, props, frames) get calm, larger strokes and close tones. Large background surfaces (ground, roof, trees) may be livelier. Avoid anything "disruptive" next to the entrance or a focal object.
6. Material logic: wood = grain direction, stone = courses, metal = brushed + rust, glass/emissive/letters = leave procedural. Do not make everything the same brush size.
7. Blend: final colour = mix(painted texture, material base colour modulated by stroke luminance, tint). Use a low tint for things that should keep the painting palette (stone, roof, foliage) and a high tint for things whose colour is defined by the material (doors, signs, flowers).

PIPELINE:
- Generate the textures with the stroke engine, save in ArtSource/Museum/Painted_Textures/.
- In Blender, connect them via UV -> Mapping (scale) -> Image Texture -> Mix (tint) -> Principled Base Color, and the H map -> Bump -> Normal. Keep node names PT_uv, PT_map, PT_col, PT_hgt, PT_mix, PT_bump so values can be tweaked.
- Do not touch materials I did not list. Do not overwrite existing .blend files: save as a new file.
- Show me a render (close-up + whole object) and wait for approval before exporting to Unity.

CHECK BEFORE FINISHING: seamless tile? stroke size matches the object? direction follows the form? palette readable from first-person distance? not too saturated? consistent with the neighbouring objects?
```

---

## Notas de uso
- Para un material nuevo, añade su paleta en `PAL` y su generador en `make_painted_textures.py`; los demás valores (escala, tinte, bump) se ajustan en los nodos `PT_*`.
- Valores que han funcionado en el exterior: césped escala 1.3 / tinte 0.75; madera escala 1.5 / tinte 0.75–0.9; piedra y tejado tinte 0 (textura pura); arbustos y cipreses UV cilíndricas, tile ≈ 3 m.
- Referencias de estilo: `ArtSource/Museum/Style_References/Munch/` y las pinturas de Van Gogh del paquete `Strokes.rar`.
