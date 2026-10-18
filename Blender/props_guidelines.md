# The Living Canvas — Props & Interactive Assets Guidelines

## Purpose

This document defines how to create props and interactive objects.

Props should reinforce the museum's identity and the player's sense of place.

---

## 1. Prop Categories

Think of props as:

### Hero props
Important, memorable, close to the player.

Examples:

- special paintings
- important frames
- protagonist tools
- significant objects related to the cat
- major interactive objects

These deserve more modeling attention.

### Supporting props
Objects that make the museum believable.

Examples:

- chairs
- lamps
- buckets
- carts
- signs
- boxes
- small decorations

### Background props
Objects mainly providing visual density.

These should remain simple.

---

## 2. Prop Modeling Priority

Always prioritize:

1. silhouette
2. function
3. recognizable structure
4. important details
5. surface treatment

---

## 3. Interactivity

For interactive objects, model around gameplay requirements.

Consider:

- player approach
- interaction point
- readable affordance
- pivot
- animation
- collision
- first-person visibility

Do not model complex mechanisms that gameplay never exposes.

---

## 4. Museum Frames

Frames are especially important in The Living Canvas.

They should feel:

- handcrafted
- slightly imperfect
- artistic
- coherent with the museum architecture

Avoid identical factory-perfect frames everywhere.

However, variations should remain controlled.

---

## 5. Paintings

Paintings are hero assets.

Consider:

- canvas thickness
- frame
- mounting
- silhouette
- wall relationship
- close-up readability

Do not automatically model brush strokes as geometry.

Painterly surface detail should primarily come from textures/materials.

---

## 6. Cleaning Equipment

Cleaning objects are important because they connect the protagonist to the museum job.

Examples:

- mop
- bucket
- cleaning cart
- cloth
- gloves
- broom
- maintenance tools

These can be simple but should feel functional.

---

## 7. Cat-Related Objects

Objects connected to the protagonist's cat may carry emotional significance.

Examples could include:

- a small photograph
- old toy
- bowl
- flower-related object
- personal keepsake

These should be modeled more intentionally than generic background props when they are story-relevant.

Avoid excessive ornamentation.

---

## 8. Scale

Use existing museum and NPCs as scale references.

Do not invent dimensions independently.

---

## 9. Variation

Repeated props should not look copied if they are visually prominent.

Use subtle:

- rotation
- scale
- material variation
- shape variation

Do not randomize objects that need precise alignment.

---

## 10. Unity Preparation

Interactive props should have:

- logical origin
- clean naming
- clean hierarchy
- predictable transforms
- separate movable components when necessary

Example:

`Prop_CleaningCart`

with children:

`Handle`

`Wheel_L`

`Wheel_R`

`Bucket`

---

## 11. Detail Rule

If a detail cannot be seen, interacted with, or contribute to silhouette/lighting, strongly consider omitting it.

---

## 12. Final Rule

Props should make the world feel **lived in**, not merely filled.
