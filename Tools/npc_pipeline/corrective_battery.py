"""Bateria de poses extremas sobre los NPCs: mide piel/ropa en cada pose (mismas metricas que penetration_sweep) y guarda la calibracion de poses.
Solo mide; no modifica el .blend. Uso: blender -b <work>.blend --python corrective_battery.py -- [Prefijos...]
Salida: ArtSource/NPC/_Reports/corrective_battery.json (+ pose_calibration.json) y tabla ordenada por peor caso.
Metricas: A = piel que asoma por fuera de la prenda (mm), B = prenda dentro de la piel (mm), por hueso dominante.
"""
import bpy, sys, os, json
sys.path.insert(0, r'D:\TheLivingCanvas\Tools\npc_pipeline')
import pose_lib as PL
import penetration_sweep as PS
from mathutils.kdtree import KDTree

OUT = PS.OUT
O = bpy.data.objects


def prepare(pref):
    mobj = O[pref + '_Mesh']; me0 = mobj.data
    skin_f, cloth_f = PS.split_faces(me0)
    cloth_v = {v for i in cloth_f for v in me0.polygons[i].vertices}
    skin_v = sorted({v for i in skin_f for v in me0.polygons[i].vertices} - cloth_v)
    bones = {v: PS.dominant_bone(mobj, v) for v in set(skin_v) | cloth_v}
    PL.reset(O[pref + '_Rig'])
    rest = PS.measure(mobj, skin_v, cloth_f)
    ecount = {}
    for i in cloth_f:
        vs = me0.polygons[i].vertices
        for k in range(len(vs)):
            e = tuple(sorted((vs[k], vs[(k + 1) % len(vs)]))); ecount[e] = ecount.get(e, 0) + 1
    bverts = {v for e, c in ecount.items() if c == 1 for v in e}
    kd = KDTree(max(1, len(bverts)))
    for v in bverts: kd.insert(me0.vertices[v].co, v)
    kd.balance()
    covered = [v for v, d in rest.items() if d <= 0.0005 and (not bverts or kd.find(me0.vertices[v].co)[2] > PS.EDGE_EXCL)]
    cl = sorted(cloth_v)
    restB = PS.measure(mobj, cl, skin_f)
    trackedB = [v for v, d in restB.items() if d >= -0.0005 and abs(d) < 0.03]
    trackedB2 = [v for v, d in restB.items() if abs(d) < 0.03]   # incluye labios/bordes que en reposo estan bajo la piel por diseno
    return dict(mobj=mobj, skin_v=skin_v, cloth_v=cl, skin_f=skin_f, cloth_f=cloth_f, covered=covered, trackedB=trackedB, bones=bones, restB=restB, trackedB2=trackedB2)


def measure_pose(c):
    A = PS.measure(c['mobj'], c['skin_v'], c['cloth_f'], c['covered'])
    B = {v: -d for v, d in PS.measure(c['mobj'], c['cloth_v'], c['skin_f'], c['trackedB']).items()}
    out = {}
    for tag, res in (('A', A), ('B', B)):
        w, n = {}, {}
        for v, d in res.items():
            if d > PS.MIN_REPORT:
                b = c['bones'][v]; n[b] = n.get(b, 0) + 1; w[b] = max(w.get(b, 0), d)
        out[tag] = {b: [round(d * 1000, 1), n[b]] for b, d in sorted(w.items(), key=lambda kv: -kv[1])[:6]}
    return out


def main():
    argv = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else []
    prefs = argv or list(PS.NAMES)
    res, calib = {}, None
    for p in prefs:
        arm = O[p + '_Rig']
        cal = PL.calibrate(arm)
        calib = calib or cal
        c = prepare(p)
        res[p] = {'Idle': measure_pose(c)}
        for pose, steps in cal.items():
            PL.apply(arm, steps)
            res[p][pose] = measure_pose(c)
        PL.reset(arm)
        worst = sorted(((max([v[0] for v in r['A'].values()] + [0]), max([v[0] for v in r['B'].values()] + [0]), k) for k, r in res[p].items()), reverse=True)[:3]
        print(f'{p}: idle={res[p]["Idle"]} top3(A,B,pose)={worst}', flush=True)
    os.makedirs(OUT, exist_ok=True)
    json.dump(res, open(os.path.join(OUT, 'corrective_battery.json'), 'w'), indent=1)
    json.dump(calib, open(os.path.join(OUT, 'pose_calibration.json'), 'w'), indent=1)
    print('BATTERYDONE')


if __name__ == "__main__":
    main()
