"""Exporta las islas UV de los materiales pintados de un NPC (ropa, pelo) para que paint.py no cruce sus bordes.

Uso (Blender en segundo plano):
    blender -b --python engine/uv_islands.py -- <ruta.fbx> <salida.json>
Salida: {"<material>": [[[u, v], ...], ...]} = poligonos UV por isla (lista de caras, cada una lista de UV).
Una isla = caras unidas por una arista cuyos dos extremos comparten UV en ambas caras (union-find).
"""
import json
import sys

import bpy
import bmesh

KINDS = ("clothes", "hair")   # piel, ojos y cejas no se re-trazan


def islands(bm, uv, faces):
    parent = {f.index: f.index for f in faces}

    def find(i):
        while parent[i] != i:
            parent[i] = parent[parent[i]]
            i = parent[i]
        return i

    key = lambda l: (round(l[uv].uv.x, 5), round(l[uv].uv.y, 5))  # noqa: E731
    for f in faces:
        for l in f.loops:
            o = l.link_loop_radial_next
            if o == l or o.face.index not in parent:
                continue
            # misma arista en la otra cara: el vertice de l es el siguiente de o y viceversa
            if key(l) == key(o.link_loop_next) and key(l.link_loop_next) == key(o):
                a, b = find(f.index), find(o.face.index)
                if a != b:
                    parent[a] = b
    out = {}
    for f in faces:
        out.setdefault(find(f.index), []).append([[l[uv].uv.x, l[uv].uv.y] for l in f.loops])
    return list(out.values())


def main():
    fbx, dst = sys.argv[sys.argv.index("--") + 1:][:2]
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.ops.import_scene.fbx(filepath=fbx)
    result = {}
    for ob in bpy.data.objects:
        if ob.type != "MESH" or not ob.data.uv_layers:
            continue
        bm = bmesh.new()
        bm.from_mesh(ob.data)
        bm.faces.ensure_lookup_table()
        uv = bm.loops.layers.uv.active
        for mi, slot in enumerate(ob.material_slots):
            if slot.material is None or not any(k in slot.material.name.lower() for k in KINDS):
                continue
            faces = [f for f in bm.faces if f.material_index == mi]
            if faces:
                result.setdefault(slot.material.name, []).extend(islands(bm, uv, faces))
        bm.free()
    with open(dst, "w", encoding="utf-8") as fh:
        json.dump(result, fh)
    print("UVISLANDS", {k: len(v) for k, v in result.items()})


main()
