"""Auditoria de los modelos de NPC (Blender, sin tocar nada). Escribe ArtSource/NPC/_audit.json y imprime un resumen.
blender -b All10_Review_VanGogh.blend --python Tools/npc_pipeline/audit_models.py

Mide por NPC:
  zfight   pares de caras de mallas distintas, misma orientacion, casi coplanares (<1.5 mm) y solapadas  -> parpadeo
  poke     vertices del cuerpo (Low) por fuera de una prenda (>0.5 mm) -> piel atravesando la ropa
  sliver   caras diminutas plegadas/degeneradas (<3e-5 m2 con vecino a >120 grados)                  -> puntos/lineas de sutura
  smallhole bucles de borde abiertos de <= 8 aristas en piel/ropa                                       -> grietas
  uvstretch caras cuya area UV / area 3D se desvia > x6 de la mediana de su malla                        -> textura estirada
  loose    vertices sueltos / aristas sueltas / duplicados exactos
"""
import json
import math
import statistics

import bmesh
import bpy
from mathutils import Vector
from mathutils.bvhtree import BVHTree

PREFIXES = ['Cur', 'Grd', 'Stu', 'Gar', 'Caf', 'Tou', 'Gen', 'Cou', 'Doc', 'Pnt']
GARMENT = ('_Suit', '_Pants', '_Tee', '_Shirt', '_Dress', '_Top', '_Shorts', '_Apron', '_Shoes', '_Boots', '_Gloves')
SKIP_Z = ('_Eyes', '_Brows', '_Lipstick', '_Freckles', '_LipScar', '_Wart', '_Mole', '_Glasses', '_Hair')
O = bpy.data.objects


def world_bvh(ob):
    bm = bmesh.new()
    bm.from_mesh(ob.data)
    bmesh.ops.triangulate(bm, faces=bm.faces[:])
    bm.transform(ob.matrix_world)
    bm.normal_update()
    bm.faces.ensure_lookup_table()
    return bm, BVHTree.FromBMesh(bm, epsilon=1e-4)


def audit(pre):
    arm = O[pre + '_Rig']
    meshes = [o for o in arm.children if o.type == 'MESH' and len(o.data.polygons)]
    res = {'zfight': {}, 'poke': {}, 'sliver': {}, 'smallhole': {}, 'uvstretch': {}, 'loose': {}}
    data = {}
    for o in meshes:
        data[o.name] = world_bvh(o)
    names = [o.name for o in meshes]
    # z-fight entre mallas distintas
    for i, a in enumerate(names):
        if a.endswith(SKIP_Z):
            continue
        for b in names[i + 1:]:
            if b.endswith(SKIP_Z):
                continue
            bma, bva = data[a]
            bmb, bvb = data[b]
            n = 0
            for ia, ib in bva.overlap(bvb):
                fa, fb = bma.faces[ia], bmb.faces[ib]
                if fa.normal.dot(fb.normal) > 0.99 and abs((fb.calc_center_median() - fa.calc_center_median()).dot(fa.normal)) < 1.5e-3:
                    n += 1
            if n >= 3:
                res['zfight'][a + ' x ' + b] = n
    # piel por fuera de la prenda
    low = O[pre + '_Low']
    lw = low.matrix_world
    for g in names:
        if not g.endswith(GARMENT):
            continue
        bmg, bvg = data[g]
        n = 0
        for v in low.data.vertices:
            p = lw @ v.co
            loc, nrm, idx, dist = bvg.find_nearest(p, 0.008)
            if loc is not None and dist < 0.008 and (p - loc).dot(bmg.faces[idx].normal) > 5e-4:
                n += 1
        if n >= 4:
            res['poke'][g] = n
    # el resto por malla
    for o in meshes:
        me = o.data
        bm = bmesh.new()
        bm.from_mesh(me)
        bm.normal_update()
        sl = 0
        for f in bm.faces:
            if f.calc_area() > 3e-5:
                continue
            for e in f.edges:
                if len(e.link_faces) == 2:
                    oo = e.link_faces[0] if e.link_faces[1] == f else e.link_faces[1]
                    if f.normal.length < 1e-9 or oo.normal.length < 1e-9 or math.degrees(f.normal.angle(oo.normal)) > 120:
                        sl += 1
                        break
        if sl:
            res['sliver'][o.name] = sl
        # bucles pequenos
        be = [e for e in bm.edges if len(e.link_faces) == 1]
        seen, small = set(), 0
        for e in be:
            if e in seen:
                continue
            comp, st = [], [e]
            seen.add(e)
            while st:
                c = st.pop()
                comp.append(c)
                for v in c.verts:
                    for nb in v.link_edges:
                        if len(nb.link_faces) == 1 and nb not in seen:
                            seen.add(nb)
                            st.append(nb)
            if len(comp) <= 8:
                small += 1
        if small and not o.name.endswith(('_Hair', '_Eyes', '_Brows', '_Bracelet', '_Wristband', '_Watch', '_Lanyard', '_Glasses')):
            res['smallhole'][o.name] = small
        loose = sum(1 for v in bm.verts if not v.link_faces) + sum(1 for e in bm.edges if not e.link_faces)
        if loose:
            res['loose'][o.name] = loose
        # estiramiento UV
        if 'UV_Paint' in me.uv_layers and not o.name.endswith(('_Eyes',)):
            uv = me.uv_layers['UV_Paint'].data
            ratios = []
            for p in me.polygons:
                if len(p.loop_indices) < 3:
                    continue
                us = [uv[l].uv for l in p.loop_indices]
                a2 = 0.0
                for k in range(1, len(us) - 1):
                    a2 += abs((us[k][0] - us[0][0]) * (us[k + 1][1] - us[0][1]) - (us[k + 1][0] - us[0][0]) * (us[k][1] - us[0][1])) / 2
                if p.area > 1e-6 and a2 > 0:
                    ratios.append((a2 / p.area, p.index))
            if len(ratios) > 20:
                med = statistics.median(r for r, _ in ratios)
                bad = [i for r, i in ratios if r > med * 6 or r < med / 6]
                if len(bad) > 0.02 * len(ratios):
                    res['uvstretch'][o.name] = len(bad)
        bm.free()
    for bm, _ in data.values():
        bm.free()
    return res


out = {}
for p in PREFIXES:
    out[p] = audit(p)
    print(p, json.dumps({k: v for k, v in out[p].items() if v}))
with open(r'D:\TheLivingCanvas\ArtSource\NPC\_audit.json', 'w') as f:
    json.dump(out, f, indent=1)
print('AUDIT DONE')
