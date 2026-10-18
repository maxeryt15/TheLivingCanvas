# The Living Canvas — Blender Modeling Guidelines

## Purpose

This document defines the general modeling rules for Blender assets in **The Living Canvas**.

Read this before creating, modifying, or reviewing any Blender asset.

The museum **interior and exterior already exist**. Do not rebuild, replace, redesign, or substantially remodel them unless explicitly instructed. New assets must integrate with the existing museum rather than forcing the environment to conform to them.

These are strong defaults, not absolute restrictions. If the user explicitly requests an exception, follow the user.

---

## 1. Visual Identity

The game is a cozy, contemplative first-person 3D experience.

The visual language should feel:

- painterly
- handcrafted
- cozy
- slightly stylized
- expressive
- imperfect in a controlled way
- artistic
- atmospheric

Avoid:

- generic low-poly aesthetics
- mobile-game low-poly
- photorealism
- hyper-realistic PBR
- sterile CAD-like modeling
- overly smooth procedural assets
- excessive cartoon exaggeration

The intended feeling is:

> A handmade painting translated into explorable 3D.

---

## 2. Artistic Influences

### Primary: Post-Impressionism

Use as the main influence for:

- expressive silhouettes
- visible artistic intent
- simplified forms
- controlled irregularity
- color relationships
- handcrafted surfaces

Van Gogh is an important inspiration, but do NOT literally copy Van Gogh paintings or reproduce his paintings as geometry.

### Secondary: Impressionism

Primarily influences:

- light
- atmosphere
- environmental color
- soft transitions

### Secondary: Expressionism

Primarily influences:

- emotionally uncomfortable spaces
- psychologically important locations
- distorted or unstable areas

---

## 3. Modeling Philosophy

Prioritize:

1. silhouette
2. proportions
3. major forms
4. important secondary forms
5. surface preparation
6. small details

A simple model with an excellent silhouette is better than a detailed model with poor proportions.

Do not add detail to compensate for a weak base shape.

---

## 4. Stylization Level

The project is **stylized mid-poly / handcrafted painterly 3D**.

It is not strict low-poly.

It is not realistic.

Geometry should be dense enough for:

- clean silhouettes
- readable forms
- appropriate lighting
- close-range first-person viewing

But geometry should not be used for every tiny surface detail.

Use textures/materials/shaders for surface-level information whenever possible.

---

## 5. Controlled Imperfection

Perfect symmetry and repetition should be avoided when they make an asset look procedural.

Appropriate variation:

- subtle asymmetry
- slight rotations
- small scale differences
- mild surface deformation
- irregular silhouettes

Important:

> handcrafted ≠ randomly distorted

Do not make objects look broken unless that is intentional.

---

## 6. Edges

Use bevels selectively.

Do not bevel every edge automatically.

Edges should generally feel:

- soft
- intentional
- slightly stylized

Avoid:

- razor-sharp CAD edges everywhere
- excessive bevels
- extremely rounded toy-like edges

---

## 7. First-Person Perspective

The final game uses a first-person camera.

Evaluate assets from approximately player eye height.

Consider:

- close-range readability
- silhouette
- interaction
- visibility from normal gameplay angles
- whether details are actually visible

Do not spend geometry on details that are effectively invisible from gameplay.

---

## 8. Scale

Use real-world scale as a starting point.

Blender units should approximately correspond to meters.

Use existing museum architecture as the primary scale reference.

Do not arbitrarily change the museum's scale.

When creating new assets, compare them against:

- existing doors
- furniture
- walls
- displays
- NPCs
- player-scale references

---

## 9. Existing Museum Rule

The museum interior and exterior are already modeled.

Therefore:

### DO

- inspect the existing museum before creating related assets
- match its scale
- match its proportions
- match its visual language
- build additions around the existing architecture
- use existing architectural assets as references
- reuse existing components when appropriate

### DO NOT

- rebuild the museum
- replace the museum
- create a second incompatible museum
- change room dimensions without instruction
- redesign the floor plan
- move major architectural elements without instruction
- introduce a completely different architectural style

If something appears imperfect in the existing museum, do not "fix" it automatically. Ask first if it is a meaningful design issue.

---

## 10. Reuse Existing Assets

Before creating a new asset, inspect the scene for related existing objects.

Prefer:

- reusing meshes
- duplicating existing modular pieces
- modifying existing assets when appropriate
- matching established proportions

Do not create a new version of an object if an existing version can be appropriately reused.

Consistency is more important than novelty.

---

## 11. Props

Props should be modeled around:

1. recognizable silhouette
2. major structure
3. gameplay relevance
4. important secondary details
5. painterly surface treatment

Example:

A chair does not need modeled screws.

A museum frame does not need microscopic wood grain geometry.

A cleaning cart should prioritize:

- readable silhouette
- wheels
- handles
- containers
- functional components visible to the player

---

## 12. Detail Budget

### High priority

- paintings
- frames
- furniture
- doors
- windows
- NPCs
- interactive objects
- hero props

### Medium priority

- lamps
- signs
- decorative objects
- small furniture details
- wall decorations

### Low priority

- hidden geometry
- unseen backsides
- microscopic hardware
- internal structures invisible to the player

Always ask:

> Will the player actually see this?

---

## 13. Materials and Painterly Surfaces

Geometry provides form.

Materials, textures, lighting, and shaders provide much of the painterly character.

Avoid making every surface physically realistic.

Prefer:

- subtle color variation
- handmade-looking texture
- controlled roughness variation
- brush-like surface information
- non-uniform color

Do not rely on generic procedural noise as the main artistic identity.

---

## 14. Unity Compatibility

Assets must be practical for Unity.

Use:

- meaningful object names
- clean hierarchy
- useful pivots
- consistent scale
- reasonable geometry
- logical separation of independent objects

Avoid names such as:

- Cube.001
- Plane.037
- Object_Final_Final2

Prefer:

- Museum_DisplayCase_01
- Museum_Frame_Large_01
- Prop_CleaningBucket
- NPC_Receptionist
- Plant_Potted_01

---

## 15. Origins and Pivots

Place origins intentionally.

Examples:

- doors → hinge
- drawers → movement origin
- rotating objects → rotation center
- furniture → logical base/center
- modular pieces → useful connection point

This is important for Unity interaction and animation.

---

## 16. Modeling Workflow

For any non-trivial asset:

### Phase 1 — Inspect

Inspect:

- existing related assets
- museum scale
- nearby objects
- materials
- scene hierarchy

### Phase 2 — Blockout

Create only:

- primary shapes
- proportions
- silhouette

### Phase 3 — Validate

Check:

- scale
- proportions
- first-person readability
- compatibility with nearby assets

### Phase 4 — Secondary Forms

Add:

- structural components
- functional components
- important decorative shapes

### Phase 5 — Stylization

Add:

- controlled asymmetry
- softened edges
- intentional irregularity

### Phase 6 — Detail

Add only visible/relevant details.

### Phase 7 — Cleanup

Check:

- transforms
- normals
- hierarchy
- naming
- pivots
- unnecessary geometry

### Phase 8 — Unity Readiness

Ensure the asset is practical to export/import.

---

## 17. MCP Workflow

Do not attempt a large environment or complex asset in one enormous operation.

Break work into stages.

After each significant stage:

1. inspect the result
2. verify proportions
3. verify placement
4. correct mistakes
5. continue only when the previous stage is sound

If an operation produces unexpected geometry, stop and correct it instead of building additional geometry on top.

---

## 18. Ambiguity

If a missing decision would substantially affect:

- proportions
- architecture
- gameplay
- character identity
- object functionality

ask before making a major assumption.

For minor details, use the established project style and choose the simplest coherent solution.

---

## 19. Final Quality Test

Before considering an asset complete:

### Shape
- Is the silhouette readable?
- Are proportions coherent?

### Style
- Does it belong to The Living Canvas?
- Does it feel handcrafted?

### Consistency
- Does it match nearby assets?
- Does its detail density match?

### Gameplay
- Does it read correctly from first-person?
- Is the player likely to see the important details?

### Technical
- Are names clean?
- Are pivots useful?
- Is the hierarchy logical?
- Is the geometry reasonable?

---

## Most Important Rule

When choosing between:

**more detail**

and

**better shape + stronger artistic identity**

choose:

**better shape + stronger artistic identity.**
