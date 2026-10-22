"""Cuello/trapecios que asoman por la prenda al mover la cabeza: los vertices de la prenda cuyo vertice de piel mas cercano esta pesado
al hueso neck_01 se empujan EXTRA a lo largo de su normal (proporcional al peso de neck_01), como margen para el cuello.
Uso: exec(open(r"D:/TheLivingCanvas/Tools/npc_pipeline/fix_neck.py").read()); run_neck()"""
import bpy, bmesh
from mathutils.bvhtree import BVHTree

PREFIXES = ['Caf', 'Cou', 'Cur', 'Doc', 'Gar', 'Gen', 'Grd', 'Pnt', 'Stu', 'Tou']
GARMENT = ('_Suit', '_Pants', '_Tee', '_Shirt', '_Dress', '_Top', '_Shorts', '_Apron')
NEAR = 0.05
EXTRA = 0.008
O = bpy.data.objects


def bone_push(ob, low, bones, extra, near=NEAR, min_w=0.2):
    """Igual que neck_push pero para una lista de huesos (p. ej. clavicle_l/r, calf_l/r)."""
    bm = bmesh.new(); bm.from_mesh(low.data); bm.transform(low.matrix_world); bm.faces.ensure_lookup_table()
    bvh = BVHTree.FromBMesh(bm); bm.free()
    lg = {g.index: g.name for g in low.vertex_groups}
    bw = [max([g.weight for g in v.groups if lg.get(g.group) in bones] or [0.0]) for v in low.data.vertices]
    me = ob.data; mw = ob.matrix_world
    moved = 0
    for v in me.vertices:
        loc, nrm, fi, dist = bvh.find_nearest(mw @ v.co, near)
        if loc is None:
            continue
        w = max(bw[k] for k in low.data.polygons[fi].vertices)
        if w < min_w:
            continue
        d = (mw @ v.co) - loc
        if d.length < 1e-6:
            continue
        v.co += mw.inverted().to_3x3() @ (d.normalized() * (extra * min(1.0, w))); moved += 1
    me.update()
    return moved


def run_extra(neck=0.006, clavicle=0.008, calf=0.006):
    res = {}
    for pre in PREFIXES:
        low = O[pre + '_Low']; arm = O[pre + '_Rig']
        for ob in arm.children:
            if ob.type == 'MESH' and ob.name.endswith(GARMENT):
                res[ob.name] = (bone_push(ob, low, {'neck_01'}, neck), bone_push(ob, low, {'clavicle_l', 'clavicle_r'}, clavicle),
                                bone_push(ob, low, {'calf_l', 'calf_r'}, calf))
    print('EXTRA', res)
    return res


def neck_push(ob, low, extra=EXTRA):
    return bone_push(ob, low, {'neck_01'}, extra)


def run_neck(extra=EXTRA):
    res = {}
    for pre in PREFIXES:
        low = O[pre + '_Low']
        arm = O[pre + '_Rig']
        for ob in arm.children:
            if ob.type == 'MESH' and ob.name.endswith(GARMENT):
                res[ob.name] = neck_push(ob, low, extra)
    print('NECK', res)
    return res


def run_suits(head=0.008, upperarm=0.005, lowerarm=0.004):
    """Pasada solo para trajes: collar contra la cabeza, mangas contra brazos."""
    res = {}
    for pre in PREFIXES:
        low = O[pre + '_Low']; arm = O[pre + '_Rig']
        for ob in arm.children:
            if ob.type == 'MESH' and ob.name.endswith('_Suit'):
                res[ob.name] = (bone_push(ob, low, {'head'}, head), bone_push(ob, low, {'upperarm_l', 'upperarm_r'}, upperarm), bone_push(ob, low, {'lowerarm_l', 'lowerarm_r'}, lowerarm))
    print('SUITS', res)
    return res
