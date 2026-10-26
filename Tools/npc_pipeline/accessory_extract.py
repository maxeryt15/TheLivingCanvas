"""Extrae a JSON las caras de ciertos materiales de una malla NPC (posiciones locales, material, UV) para restaurarlas en otro .blend.
Uso: blender -b <source.blend> --python accessory_extract.py -- Prefijo Mat1,Mat2 salida.json
"""
import bpy, sys, json
a = sys.argv[sys.argv.index('--') + 1:]
pref, mats, out = a[0], set(a[1].split(',')), a[2]
ob = bpy.data.objects[pref + '_Mesh']; me = ob.data
uv = me.uv_layers.active.data
faces = []
for p in me.polygons:
    m = me.materials[p.material_index]
    if m and m.name in mats:
        faces.append({'mat': m.name, 'co': [list(me.vertices[v].co) for v in p.vertices],
                      'uv': [list(uv[l].uv) for l in p.loop_indices]})
json.dump({'pref': pref, 'matrix': [list(r) for r in ob.matrix_world], 'faces': faces}, open(out, 'w'))
print('EXTRACTED', pref, len(faces))
