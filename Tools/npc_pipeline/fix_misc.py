"""Limpieza final: slivers en accesorios, vertices sueltos, z-fighting entre prendas y piel que atraviesa la ropa.
Uso: exec(open(r"D:/TheLivingCanvas/Tools/npc_pipeline/fix_misc.py").read()); run_misc()   (necesita fix_seams.py)"""
import bpy, bmesh
from mathutils import Vector
from mathutils.bvhtree import BVHTree

exec(open(r"D:/TheLivingCanvas/Tools/npc_pipeline/fix_seams.py", encoding='utf-8').read())   # kill_folded_slivers
PREFIXES = ['Cur', 'Grd', 'Stu', 'Gar', 'Caf', 'Tou', 'Gen', 'Cou', 'Doc', 'Pnt']
GARMENT = ('_Suit', '_Pants', '_Tee', '_Shirt', '_Dress', '_Top', '_Shorts', '_Apron', '_Shoes', '_Boots', '_Gloves')
SKIP_SLIVER = ('_Brows', '_Lipstick', '_Eyes', '_Hair', '_Low')
SKIP_Z = ('_Eyes', '_Brows', '_Lipstick', '_Freckles', '_LipScar', '_Wart', '_Mole', '_Glasses', '_Hair')
O = bpy.data.objects


def remove_loose(ob):
    me = ob.data
    bm = bmesh.new(); bm.from_mesh(me)
    dead = [v for v in bm.verts if not v.link_faces]
    n = len(dead)
    if dead:
        bmesh.ops.delete(bm, geom=dead, context='VERTS')
    loose_e = [e for e in bm.edges if not e.link_faces]
    n += len(loose_e)
    if loose_e:
        bmesh.ops.delete(bm, geom=loose_e, context='EDGES')
    bm.to_mesh(me); bm.free(); me.update()
    return n


def _wbvh(ob):
    bm = bmesh.new(); bm.from_mesh(ob.data)
    bmesh.ops.triangulate(bm, faces=bm.faces[:])
    bm.transform(ob.matrix_world); bm.normal_update(); bm.faces.ensure_lookup_table()
    return bm, BVHTree.FromBMesh(bm, epsilon=1e-4)


def fix_zfight(pre):
    """caras coplanares de dos mallas: la segunda se separa 1 mm a lo largo de la normal."""
    arm = O[pre + '_Rig']
    ms = [o for o in arm.children if o.type == 'MESH' and len(o.data.polygons) and not o.name.endswith(SKIP_Z)]
    moved = {}
    for i, a in enumerate(ms):
        for b in ms[i + 1:]:
            if len(a.data.polygons) < len(b.data.polygons):
                a, b = b, a      # se mueve siempre la malla con MENOS caras (el accesorio: botones, zapato...)
            bma, bva = _wbvh(a); bmb, bvb = _wbvh(b)
            hit = set()
            for ia, ib in bva.overlap(bvb):
                fa, fb = bma.faces[ia], bmb.faces[ib]
                if fa.normal.dot(fb.normal) > 0.99 and abs((fb.calc_center_median() - fa.calc_center_median()).dot(fa.normal)) < 1.5e-3:
                    hit.add(ib)
            if len(hit) >= 3:
                # mover b: vertices de las caras implicadas (en coordenadas locales de b)
                bm = bmesh.new(); bm.from_mesh(b.data); bm.normal_update(); bm.faces.ensure_lookup_table()
                tri_src = bmb  # triangulado: indices no coinciden con bm -> usar posicion
                inv = b.matrix_world.inverted()
                targets = set()
                for ib in hit:
                    c = bmb.faces[ib].calc_center_median()
                    cl = inv @ c
                    best = min(bm.faces, key=lambda f: (f.calc_center_median() - cl).length_squared)
                    targets.add(best.index)
                verts = {}
                for fi in targets:
                    f = bm.faces[fi]
                    for v in f.verts:
                        verts.setdefault(v.index, []).append(f.normal.copy())
                for vi, ns in verts.items():
                    n = sum(ns, Vector()) / len(ns)
                    if n.length > 0:
                        bm.verts.ensure_lookup_table(); bm.verts[vi].co += n.normalized() * 0.0015
                bm.to_mesh(b.data); bm.free(); b.data.update()
                moved[a.name + ' x ' + b.name] = len(targets)
            bma.free(); bmb.free()
    return moved


def fix_poke(pre):
    """vertices del cuerpo por fuera de la prenda: se hunden 1 mm por debajo de su superficie."""
    low = O[pre + '_Low']; lw = low.matrix_world; inv = lw.inverted()
    arm = O[pre + '_Rig']
    res = {}
    for g in [o for o in arm.children if o.type == 'MESH' and o.name.endswith(GARMENT)]:
        bmg, bvg = _wbvh(g)
        n = 0
        for v in low.data.vertices:
            p = lw @ v.co
            loc, nrm, idx, dist = bvg.find_nearest(p, 0.008)
            if loc is not None:
                ex = (p - loc).dot(bmg.faces[idx].normal)
                if ex > 5e-4:
                    v.co = inv @ (p - bmg.faces[idx].normal * (ex + 0.001)); n += 1
        bmg.free()
        if n:
            res[g.name] = n
    low.data.update()
    return res


def run_misc():
    out = {}
    for pre in PREFIXES:
        arm = O[pre + '_Rig']
        r = {'sliver': {}, 'loose': {}}
        for ob in arm.children:
            if ob.type != 'MESH':
                continue
            if not ob.name.endswith(SKIP_SLIVER):
                k = kill_folded_slivers(ob, zmax=None, iterations=15, verbose=False)
                if k:
                    r['sliver'][ob.name] = k
            k = remove_loose(ob)
            if k:
                r['loose'][ob.name] = k
        r['zfight'] = fix_zfight(pre)
        r['poke'] = fix_poke(pre)
        out[pre] = r
        print('MISC', pre, {k: v for k, v in r.items() if v})
    return out


def separate(a_name, b_name, pre, gap=0.0025, band=0.002):
    """vertices de A a menos de `band` de la superficie de B se colocan a `gap` por encima de B (a lo largo de la normal de B)."""
    a, b = O[a_name], O[b_name]
    bmb, bvb = _wbvh(b)
    aw = a.matrix_world; inv = aw.inverted(); n = 0
    for v in a.data.vertices:
        p = aw @ v.co
        loc, nrm, idx, dist = bvb.find_nearest(p, band * 1.5)
        if loc is None:
            continue
        nb = bmb.faces[idx].normal
        h = (p - loc).dot(nb)
        if -band <= h <= band:
            v.co = inv @ (loc + nb * gap); n += 1
    bmb.free(); a.data.update()
    return n
