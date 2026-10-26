"""Barrido de penetracion piel-ropa de los NPCs (solo mide; no modifica el .blend).
Uso: blender -b NPCs_Shell_Face.blend --python penetration_sweep.py -- [Prefijos...]
Prefijos: Caf Cou Cur Doc Gar Gen Grd Pnt Rose Stu Tou (sin argumentos = todos).

Metodo A (kind clip/stress): vertices de piel "cubiertos" en reposo (bajo la prenda, d<=0 y cerca) -> en cada pose se mide la distancia con signo
al punto mas cercano de la prenda; d>0 = la piel asoma por fuera de la prenda. Se informa la profundidad maxima por hueso dominante.
Metodo B (kind *_clothin): vertices de prenda fuera de la piel en reposo y a <3 cm; d<0 respecto a la normal de la piel = la prenda entra en la piel.
Poses: acciones U_* del propio .blend ("clip") y poses de estres de un solo hueso a +-90/120 grados en cada eje ("stress";
algunas son anatomicamente imposibles: sirven para comparar antes/despues, no como fallo absoluto).
Salida: ArtSource/NPC/_Reports/penetration_<Pref>.csv + penetration_summary.json
"""
import bpy, sys, os, json, math
from mathutils import Euler, Quaternion
from mathutils.bvhtree import BVHTree

OUT = r'D:\TheLivingCanvas\ArtSource\NPC\_Reports'
NAMES = {'Caf': 'Cafe', 'Cou': 'Courier', 'Cur': 'Curator', 'Doc': 'Docent', 'Gar': 'Gardener', 'Gen': 'Gentleman',
         'Grd': 'Guard', 'Pnt': 'Painter', 'Rose': 'Rose', 'Stu': 'Student', 'Tou': 'Tourist'}
CLOTH_KEYS = ('clothes_paint', 'suit_', 'aproncloth', 'blouse', 'scarfcloth')
COVER_MAX_DIST = 0.04   # m: la piel cubierta en reposo esta a menos de esto de la prenda
EDGE_EXCL = 0.02      # m: piel a menos de esto de un borde abierto de prenda no se evalua (metodo A)
MIN_REPORT = 0.001      # m: por debajo se ignora (ruido de BVH)
STRESS = [  # (hueso, angulo grados) ; ejes X,Y,Z y signo +-
    ('upperarm_l', 90), ('upperarm_r', 90), ('lowerarm_l', 120), ('lowerarm_r', 120),
    ('thigh_l', 90), ('thigh_r', 90), ('calf_l', 120), ('calf_r', 120),
    ('spine_02', 45), ('neck_01', 40), ('clavicle_l', 25), ('clavicle_r', 25), ('hand_l', 60), ('hand_r', 60),
]
O = bpy.data.objects


def is_skin(name):
    return name.lower().endswith('skin_paint')


def is_cloth(name):
    n = name.lower()
    return any(k in n for k in CLOTH_KEYS)


def split_faces(mesh):
    skin_f, cloth_f = [], []
    for p in mesh.polygons:
        mat = mesh.materials[p.material_index]
        n = mat.name if mat else ''
        if is_skin(n):
            skin_f.append(p.index)
        elif is_cloth(n):
            cloth_f.append(p.index)
    return skin_f, cloth_f


def reset_pose(arm):
    for pb in arm.pose.bones:
        pb.rotation_mode = 'QUATERNION'
        pb.rotation_quaternion = Quaternion((1, 0, 0, 0))
        pb.location = (0, 0, 0)
        pb.scale = (1, 1, 1)


def evaluate(mobj):
    bpy.context.view_layer.update()
    dg = bpy.context.evaluated_depsgraph_get()
    ev = mobj.evaluated_get(dg)
    return ev, ev.to_mesh()


def measure(mobj, query_verts, cloth_polys, covered=None):
    """Devuelve {vert: d} con d = distancia con signo piel->prenda (>0 = fuera). Si covered, solo esos vertices."""
    ev, me = evaluate(mobj)
    verts = [v.co.copy() for v in me.vertices]
    bvh = BVHTree.FromPolygons(verts, [tuple(me.polygons[i].vertices) for i in cloth_polys])
    res = {}
    for vi in (covered if covered is not None else query_verts):
        loc, nor, idx, dist = bvh.find_nearest(verts[vi])
        if loc is None or dist > COVER_MAX_DIST:
            continue
        res[vi] = (verts[vi] - loc).dot(nor)
    ev.to_mesh_clear()
    return res


def dominant_bone(mobj, vi):
    v = mobj.data.vertices[vi]
    best, bw = '', -1.0
    for g in v.groups:
        if g.weight > bw:
            bw, best = g.weight, mobj.vertex_groups[g.group].name
    return best


def run_npc(pref):
    arm, mobj = O[pref + '_Rig'], O[pref + '_Mesh']
    me0 = mobj.data
    skin_f, cloth_f = split_faces(me0)
    cloth_v = {v for i in cloth_f for v in me0.polygons[i].vertices}
    skin_v = sorted({v for i in skin_f for v in me0.polygons[i].vertices} - cloth_v)
    bones = {v: dominant_bone(mobj, v) for v in skin_v}
    if arm.animation_data:
        arm.animation_data.action = None
    reset_pose(arm)
    rest = measure(mobj, skin_v, cloth_f)
    # excluir piel cercana a bordes abiertos de la prenda (sisas, cuello, puños): ahi la piel asoma por diseno
    from mathutils.kdtree import KDTree
    ecount = {}
    for i in cloth_f:
        vs = me0.polygons[i].vertices
        for k in range(len(vs)):
            e = tuple(sorted((vs[k], vs[(k + 1) % len(vs)])))
            ecount[e] = ecount.get(e, 0) + 1
    bverts = {v for e, c in ecount.items() if c == 1 for v in e}
    kd = KDTree(len(bverts)); [kd.insert(me0.vertices[v].co, v) for v in bverts]; kd.balance()
    covered = [v for v, d in rest.items() if d <= 0.0005 and (not bverts or kd.find(me0.vertices[v].co)[2] > EDGE_EXCL)]
    rest_max = max([rest[v] for v in covered], default=0.0)
    print(f'{pref}: skin={len(skin_v)} cloth_faces={len(cloth_f)} covered={len(covered)} rest_max={rest_max * 1000:.2f}mm', flush=True)

    # direccion B: vertices de prenda que entran en la piel (prenda fuera de la piel en reposo y cerca de ella)
    cloth_vl = sorted(cloth_v)
    for v in cloth_vl:
        bones[v] = dominant_bone(mobj, v)
    restB = measure(mobj, cloth_vl, skin_f)
    trackedB = [v for v, d in restB.items() if d >= -0.0005 and abs(d) < 0.03]
    print(f'{pref}: cloth_verts={len(cloth_vl)} trackedB={len(trackedB)}', flush=True)

    rows = []  # (npc, kind, pose, frame, bone, max_mm, count)

    def measure_both(kind, pose, frame):
        record(kind, pose, frame, measure(mobj, skin_v, cloth_f, covered))
        resB = measure(mobj, cloth_vl, skin_f, trackedB)
        record(kind + '_clothin', pose, frame, {v: -d for v, d in resB.items()})

    def record(kind, pose, frame, res):
        worst = {}
        cnt = {}
        for v, d in res.items():
            if d > MIN_REPORT:
                b = bones[v]
                cnt[b] = cnt.get(b, 0) + 1
                if d > worst.get(b, 0):
                    worst[b] = d
        for b, d in worst.items():
            rows.append((pref, kind, pose, frame, b, round(d * 1000, 2), cnt[b]))
        if not worst:
            rows.append((pref, kind, pose, frame, '', 0.0, 0))

    # clips U_* del NPC
    ad = arm.animation_data or arm.animation_data_create()
    nm = NAMES[pref]
    for act in sorted(bpy.data.actions, key=lambda a: a.name):
        if not act.name.startswith('U_') or f'_{nm}_' not in act.name:
            continue
        reset_pose(arm)
        ad.action = act
        try:
            ad.action_slot = act.slots[0]
        except Exception:
            pass
        f0, f1 = int(act.frame_range[0]), int(act.frame_range[1])
        step = 3 if (f1 - f0) <= 60 else 15
        for f in list(range(f0, f1 + 1, step)) + ([f1] if (f1 - f0) % step else []):
            bpy.context.scene.frame_set(f)
            measure_both('clip', act.name, f)
    ad.action = None
    reset_pose(arm)

    # poses de estres
    for bone, ang in STRESS:
        pb = arm.pose.bones.get(bone)
        if not pb:
            continue
        for axis in range(3):
            for sign in (1, -1):
                reset_pose(arm)
                e = [0.0, 0.0, 0.0]
                e[axis] = sign * math.radians(ang)
                pb.rotation_mode = 'XYZ'
                pb.rotation_euler = Euler(e, 'XYZ')
                measure_both('stress', f'{bone}_{"XYZ"[axis]}{"+" if sign > 0 else "-"}{ang}', 0)
    reset_pose(arm)

    os.makedirs(OUT, exist_ok=True)
    with open(os.path.join(OUT, f'penetration_{pref}.csv'), 'w', encoding='utf-8') as fh:
        fh.write('npc,kind,pose,frame,bone,max_mm,verts\n')
        for r in rows:
            fh.write(','.join(str(x) for x in r) + '\n')
    return rows, rest_max, len(covered)


def main():
    argv = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else []
    prefs = argv or list(NAMES)
    summary = {}
    for p in prefs:
        rows, rest_max, ncov = run_npc(p)
        by_bone = {}
        for r in rows:
            if r[4] and r[5] > by_bone.get((r[1], r[4]), (0,))[0]:
                by_bone[(r[1], r[4])] = (r[5], r[2], r[3])
        summary[p] = {
            'rest_max_mm': round(rest_max * 1000, 2), 'covered_verts': ncov,
            'worst': {f'{k[0]}:{k[1]}': {'mm': v[0], 'pose': v[1], 'frame': v[2]} for k, v in sorted(by_bone.items(), key=lambda kv: -kv[1][0])[:12]},
        }
    os.makedirs(OUT, exist_ok=True)
    path = os.path.join(OUT, 'penetration_summary.json' if not argv else 'penetration_summary_' + '_'.join(argv) + '.json')
    with open(path, 'w', encoding='utf-8') as fh:
        json.dump(summary, fh, indent=1)
    print('SWEEPDONE', path)


if __name__ == "__main__":
    main()
