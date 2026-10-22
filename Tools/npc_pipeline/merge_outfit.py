"""Une un NPC en UNA sola malla: borra la piel (y las prendas interiores) que quedan tapadas por otra prenda y junta todo (piel, ropa, zapatos,
accesorios, pelo, rasgos de la cara) en un unico objeto skineado con sus materiales como submallas. Asi la ropa nunca atraviesa la piel
porque la piel tapada ya no existe, y los accesorios rigidos viajan con el hueso al que estan pegados.
Uso: exec(open(r"D:/TheLivingCanvas/Tools/npc_pipeline/merge_outfit.py").read()); merge_npc('Caf')
"""
import bpy, bmesh
from mathutils import Vector
from mathutils.bvhtree import BVHTree
from mathutils.kdtree import KDTree

O = bpy.data.objects
COVER_DIST = 0.06       # solo se borra lo que la prenda cubre a menos de 6 cm; lo mas lejano (faldas muy amplias) se conserva
BORDER_MARGIN = 0.02    # se conserva la piel a menos de 2 cm del borde abierto de una prenda (cuello, punos, bajos): sin huecos
GARMENT_SUFFIX = ('_Suit', '_Pants', '_Tee', '_Shirt', '_Dress', '_Top', '_Shorts', '_Apron', '_Shoes', '_Boots', '_Gloves')
OUTER = ('_Apron', '_Suit')                              # prendas que tapan a otras
INNER = ('_Tee', '_Shirt', '_Top', '_Dress', '_Pants', '_Shorts')   # prendas que pueden quedar tapadas por una OUTER


def _world_bm(ob):
    bm = bmesh.new(); bm.from_mesh(ob.data); bm.transform(ob.matrix_world); bm.faces.ensure_lookup_table()
    return bm


def _cover(ob):
    bm = _world_bm(ob)
    bvh = BVHTree.FromBMesh(bm)
    border = [v.co.copy() for v in bm.verts if any(len(e.link_faces) < 2 for e in v.link_edges)]
    kd = KDTree(max(1, len(border)))
    for i, p in enumerate(border):
        kd.insert(p, i)
    kd.balance()
    bm.free()
    return bvh, kd, bool(border)


def _rays(n):
    """normal + 4 rayos inclinados 35 grados: un vertice cuenta como tapado si la prenda lo cubre en al menos 4 de 5 direcciones."""
    t = n.cross(Vector((0, 0, 1)))
    if t.length < 1e-4:
        t = n.cross(Vector((1, 0, 0)))
    t.normalize(); b = n.cross(t).normalized()
    k = 0.7002; c = 0.8192   # tan/cos de 35 grados aprox.
    return [n, (n * c + t * k * c).normalized(), (n * c - t * k * c).normalized(), (n * c + b * k * c).normalized(), (n * c - b * k * c).normalized()]


def remove_covered(target, covers, dist=COVER_DIST, margin=BORDER_MARGIN, need=4):
    """Borra de `target` las caras cuyos vertices estan todos tapados por alguna malla de `covers` (rayos a < dist), salvo cerca del borde de la cubierta."""
    infos = [_cover(c) for c in covers]
    bm = bmesh.new(); bm.from_mesh(target.data); bm.verts.ensure_lookup_table(); bm.faces.ensure_lookup_table()
    mw = target.matrix_world; nm = mw.to_3x3()
    bm.normal_update()
    covered = set()
    for v in bm.verts:
        p = mw @ v.co
        n = (nm @ v.normal).normalized()
        for bvh, kd, has_border in infos:
            if has_border:
                _, _, bd = kd.find(p)
                if bd < margin:
                    continue
            hits = 0
            for d in _rays(n):
                loc, nrm, idx, dd = bvh.ray_cast(p + n * 0.0005, d, dist)
                if loc is not None:
                    hits += 1
            if hits >= need:
                covered.add(v.index); break
    kill = [f for f in bm.faces if all(v.index in covered for v in f.verts)]
    n_removed = len(kill)
    if kill:
        bmesh.ops.delete(bm, geom=kill, context='FACES')
        loose = [v for v in bm.verts if not v.link_faces]
        if loose:
            bmesh.ops.delete(bm, geom=loose, context='VERTS')
    bm.to_mesh(target.data); bm.free(); target.data.update()
    return n_removed


def merge_npc(prefix, name=None, dry=False):
    arm = O[prefix + '_Rig']
    kids = [o for o in arm.children if o.type == 'MESH']
    low = O[prefix + '_Low']
    garments = [o for o in kids if o.name.endswith(GARMENT_SUFFIX)]
    report = {}
    # 1) piel tapada por ropa y calzado
    skin_covers = [o for o in garments]
    report['skin_removed'] = remove_covered(low, skin_covers)
    # 2) prendas interiores tapadas por otras (p. ej. vestido bajo delantal): la que esta mas fuera tapa a la de dentro
    outers = [o for o in garments if o.name.endswith(OUTER)]
    for inner in [o for o in garments if o.name.endswith(INNER)]:
        cov = [o for o in outers if o is not inner]
        if cov:
            report[inner.name + '_removed'] = remove_covered(inner, cov)
    if dry:
        return report
    # 3) unir todo en una malla
    for o in bpy.context.view_layer.objects:
        o.select_set(False)
    for o in kids:
        o.select_set(True)
    with bpy.context.temp_override(active_object=low, selected_objects=kids, selected_editable_objects=kids, object=low):
        bpy.ops.object.join()
    merged = low
    merged.name = name or (prefix + '_Mesh')
    merged.data.name = merged.name
    # 4) pesos: maximo 4 huesos por vertice y normalizados
    with bpy.context.temp_override(active_object=merged, selected_objects=[merged], selected_editable_objects=[merged], object=merged):
        bpy.ops.object.vertex_group_limit_total(group_select_mode='ALL', limit=4)
        bpy.ops.object.vertex_group_normalize_all(group_select_mode='ALL', lock_active=False)
    report['merged'] = (merged.name, len(merged.data.vertices), len(merged.data.polygons), [m.name for m in merged.data.materials if m])
    return report


def triangulate_ngons(ob):
    """Unity descarta los poligonos de mas de 4 lados que se autointersectan: los ngons se triangulan antes de exportar."""
    bm = bmesh.new(); bm.from_mesh(ob.data)
    ng = [f for f in bm.faces if len(f.verts) > 4]
    if ng:
        bmesh.ops.triangulate(bm, faces=ng, quad_method='BEAUTY', ngon_method='BEAUTY')
    bm.to_mesh(ob.data); bm.free(); ob.data.update()
    return len(ng)
