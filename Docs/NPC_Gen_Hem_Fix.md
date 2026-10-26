# Gentleman: corrección del dobladillo del abrigo (2026-10-26)

Estado: **aprobada técnicamente, NO integrada** en `NPCs_Shell_Face.blend`. Sin validar en Unity.

## Versión aprobada
- Archivo: `ArtSource/NPC/NPCs_Shell_Face_ACCESSORIES_WORK.blend` (18 708 152 bytes)
- SHA-256: `783aa0b545b6da199af63a8d356e3c1c20c21e4cf1e440d794d45a5f0bdf7e1a`
- Línea base original: `..._ACCESSORIES_WORK_BACKUP_before_layerw.blend` (SHA `6cab2b5c…f0895573`, idéntico a `NPCs_Shell_Face.blend`).
- Versión v1 anterior (descartada): `..._BACKUP_before_layerw2.blend`.
- Copia de validación: `..._VALIDATION_TEST.blend` (mismo SHA que la aprobada).
- Export de prueba (fuera de `Assets/`): `ArtSource/_Exports/GenHemTest/Gentleman.fbx`.

## Qué contiene
- Objeto: `Gen_Mesh` (malla fusionada de Gentleman). Nada más cambia (armature, huesos, shape keys, otros NPCs, geometría).
- Región: vértices de la isla superior (abrigo) con z < 1.05 (selección de `layer_clip_scan.setup('Gen')`): 317 vértices, 301 con pesos distintos del original. Tabla de pesos por vértice: `ArtSource/NPC/_Reports/gen_hem/w_{orig,v1,final}.json`.
- Pesos: `t = 0.95 * smoothstep((1.05 - z) / (1.05 - zmin))`; nuevo = (1-t)·actual + t·(thigh_l·wl + thigh_r·wr), `wl = 0.5 + 0.5·clamp(x / 0.06, -1, 1)`, máx. 4 influencias, normalizado. Parámetros por defecto de `Tools/npc_pipeline/layer_weights.reweight('Gen')`.

## Reproducir con seguridad
`apply_gen_hem.py` NO es idempotente (mezcla sobre los pesos actuales). Solo sobre la línea base original y a un archivo NUEVO:

```
blender -b NPCs_Shell_Face_ACCESSORIES_WORK_BACKUP_before_layerw.blend --python Tools/npc_pipeline/apply_gen_hem.py -- <salida_nueva>.blend
```
Comprobaciones que imprime: solo cambia `Gen_Mesh`, shape keys iguales, máx. 4 influencias.

## Resultados
- Estiramiento máx. de arista en Crouch: 24,7× (original) → 2,7× (final); aristas >2×: 52 → 14. Caminar 1,5×.
- Las 14 aristas están en la abertura trasera (x −0,05…0,06, z 0,80…0,97), donde se cruzan los pesos de ambos muslos (diagnóstico C).
- Efecto visual: la abertura trasera se abre en Sit, Crouch y patadas y deja ver el asiento del pantalón. Veredicto estético: **dudoso**, pendiente de revisión manual.

## Unity
FBX validado técnicamente fuera de Unity: huesos (55), 10 shape keys y reposo idénticos; pesos ≤0,024 de diferencia; deformación FBX = .blend (0,0 mm en 7 poses). El grupo `Root` no viaja. **Pendiente**: importador, Animator y clips reales dentro de Unity. Unity MCP no conectó en esta sesión (ECONNREFUSED); no se tocó el proyecto.
