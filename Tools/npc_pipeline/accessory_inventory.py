"""Inventario de accesorios problematicos (solo mide; no modifica). Uso: blender -b WORK.blend --python accessory_inventory.py -- Pref [Pref...]
Por material no-cuerpo: peso dominante, huesos esperados (pesos de la prenda/piel mas cercana en reposo), y desplazamiento del material
respecto a la superficie vecina (distancia al punto mas cercano de prenda+piel, crecimiento vs reposo) en 24 poses + Walk.
Salida: ArtSource/NPC/_Reports/accessory_inventory_<Pref>.json"""
import bpy, sys, json, collections
sys.path.insert(0, r'D:\TheLivingCanvas\Tools\npc_pipeline')
import pose_lib as PL, penetration_sweep as PS
from mathutils.kdtree import KDTree
O = bpy.data.objects; S = bpy.context.scene
NAMES = PS.NAMES
HAIR = ('hair',)


def pts(ob):
    ev = ob.evaluated_get(bpy.context.evaluated_depsgraph_get()); m = ev.to_mesh(); P = [v.co.copy() for v in m.vertices]; ev.to_mesh_clear(); return P


def wvec(ob, i):
    return {ob.vertex_groups[g.group].name: g.weight for g in ob.data.vertices[i].groups if g.weight > 0.01}


def run(pref):
    ob, arm = O[pref + '_Mesh'], O[pref + '_Rig']; me = ob.data
    mats = [m.name if m else '' for m in me.materials]
    body, acc, accm = set(), {}, collections.defaultdict(set)
    for pl in me.polygons:
        n = mats[pl.material_index]; nl = n.lower()
        if nl.endswith('skin_paint') or PS.is_cloth(n): body.update(pl.vertices)
        else:
            for v in pl.vertices: accm[n].add(v)
    for n in list(accm): accm[n] -= body
    accm = {n: sorted(v) for n, v in accm.items() if v and not any(h in n.lower() for h in HAIR)}
    body = sorted(body)
    res = {'obj': dict(loc=list(ob.location), rot=list(ob.rotation_euler), scale=list(ob.scale), parent=ob.parent.name if ob.parent else None,
                       mods=[(m.type, m.object.name if getattr(m, 'object', None) else None) for m in ob.modifiers],
                       parent_inverse_identity=all(abs(ob.matrix_parent_inverse[i][j] - (1 if i == j else 0)) < 1e-6 for i in range(4) for j in range(4)),
                       groups_not_in_rig=[g.name for g in ob.vertex_groups if g.name not in arm.data.bones and not g.name.startswith(('Corrective',))][:10])}
    if arm.animation_data: arm.animation_data.action = None
    PL.reset(arm); P0 = pts(ob)

    def nearest(P):
        kd = KDTree(len(body)); [kd.insert(P[i], k) for k, i in enumerate(body)]; kd.balance(); return kd
    kd0 = nearest(P0)
    info = {}
    for n, vs in accm.items():
        c = sum((P0[i] for i in vs), P0[vs[0]] * 0) / len(vs)
        wsum = collections.Counter()
        for i in vs:
            for b, w in wvec(ob, i).items(): wsum[b] += w
        tot = sum(wsum.values()) or 1
        exp = collections.Counter()
        for i in vs[::max(1, len(vs) // 40)]:
            for _, k, d in kd0.find_n(P0[i], 4):
                for b, w in wvec(ob, body[k]).items(): exp[b] += w
        et = sum(exp.values()) or 1
        d0 = {i: kd0.find(P0[i])[2] for i in vs}
        info[n] = dict(n=len(vs), centroid=[round(x, 3) for x in c], bones={b: round(w / tot, 2) for b, w in wsum.most_common(3)},
                       expected={b: round(w / et, 2) for b, w in exp.most_common(3)}, d0=d0, worst=0.0, pose='')
    cal = PL.calibrate(arm)
    cl = [(k, v) for k, v in cal.items()]
    walk = next((a for a in bpy.data.actions if f'_{NAMES[pref]}_Walk' in a.name), None)
    def evaluate(tag):
        P = pts(ob); kd = nearest(P)
        for n, d in info.items():
            vs = accm[n]; g = sorted(kd.find(P[i])[2] - d['d0'][i] for i in vs)
            p90 = g[int(len(g) * 0.9)] if g else 0
            if p90 > d['worst']: d['worst'] = p90; d['pose'] = tag
    for name, st in cl:
        PL.apply(arm, st); evaluate(name)
    if walk:
        PL.reset(arm); ad = arm.animation_data or arm.animation_data_create(); ad.action = walk; ad.action_slot = walk.slots[0]
        for f in range(1, 41, 3): S.frame_set(f); evaluate(f'Walk@{f}')
        ad.action = None
    PL.reset(arm)
    for d in info.values(): d.pop('d0'); d['worst_mm'] = round(d.pop('worst') * 1000, 1)
    res['acc'] = info
    json.dump(res, open(PS.OUT + f'/accessory_inventory_{pref}.json', 'w'), indent=1)
    bad = sorted(((d['worst_mm'], n, d['pose'], d['bones'], d['expected']) for n, d in info.items() if d['worst_mm'] > 25), reverse=True)
    print(f'INV {pref} obj={res["obj"]}')
    for b in bad: print('INV_BAD', pref, b)


if __name__ == '__main__':
    for p in (sys.argv[sys.argv.index('--') + 1:] or list(NAMES)): run(p)
    print('INVDONE')
