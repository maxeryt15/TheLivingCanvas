"""Valida correctivas (una o varias keys con prefijo comun): Idle exacto, fracciones 0.1..1.0 con/sin keys, y bateria completa (efectos secundarios).
Metricas: A = piel que asoma (mm), B2 = prenda mas hundida en la piel que en reposo (incluye labios/axila) (mm).
Uso: blender -b WORK.blend --python verify_corrective.py -- Pref PrefijoKeys PoseObjetivo
"""
import bpy, sys
sys.path.insert(0, r'D:\TheLivingCanvas\Tools\npc_pipeline')
import pose_lib as PL, corrective_battery as CB, penetration_sweep as PS
O = bpy.data.objects
pref, kpre, target = sys.argv[sys.argv.index('--') + 1:][:3]
arm, ob = O[pref + '_Rig'], O[pref + '_Mesh']
keys = [k for k in ob.data.shape_keys.key_blocks if k.name.startswith(kpre)]
cal = PL.calibrate(arm); c = CB.prepare(pref)


def mute(m):
    for k in keys: k.mute = m


def posed():
    ev = ob.evaluated_get(bpy.context.evaluated_depsgraph_get()); me = ev.to_mesh()
    co = [v.co.copy() for v in me.vertices]; ev.to_mesh_clear(); return co


me0 = ob.data; base = me0.shape_keys.key_blocks[0]
_edges = sorted({tuple(sorted((p.vertices[k], p.vertices[(k + 1) % len(p.vertices)]))) for i in c['cloth_f'] for p in [me0.polygons[i]] for k in range(len(p.vertices))})
_L0 = {e: (base.data[e[0]].co - base.data[e[1]].co).length for e in _edges}
_edges = [e for e in _edges if _L0[e] > 0.003]


def stretch():
    co = posed(); n = 0; mx = 0
    for e in _edges:
        r = (co[e[0]] - co[e[1]]).length / _L0[e]
        r = max(r, 1 / r) if r > 0 else 99
        if r > 1.8: n += 1
        mx = max(mx, r)
    return n, round(mx, 1)


def metric():
    A = PS.measure(ob, c['skin_v'], c['cloth_f'], c['covered'])
    mA = max([d for d in A.values()] + [0]) * 1000
    Bd = PS.measure(ob, c['cloth_v'], c['skin_f'], c['trackedB2'])
    mB = max([max(0.0, min(0.003, c['restB'][v]) - d) for v, d in Bd.items()] + [0]) * 1000
    return round(mA, 1), round(mB, 1), stretch()


vals = lambda: [round(k.value, 2) for k in keys]
PL.reset(arm); mute(False); a = posed(); mute(True); b = posed(); mute(False)
print('V_IDLE max diff con/sin keys (mm):', max((p - q).length for p, q in zip(a, b)) * 1000)
print('V_FRAC fraccion | OFF (A,B2) | ON (A,B2) | valores keys', [k.name.split('_')[-1] for k in keys])
for f in (0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0):
    PL.apply(arm, cal[target], f); mute(True); off = metric(); mute(False); PL.apply(arm, cal[target], f); on = metric()
    print(f'V_FRAC {f:.1f}  OFF {off}  ON {on}  {vals()}')
print('V_BATT efectos secundarios:')
for pose, steps in cal.items():
    PL.apply(arm, steps); mute(True); off = metric(); mute(False); PL.apply(arm, steps); on = metric()
    flag = '  <-- EMPEORA' if on[0] > off[0] + 1 or on[1] > off[1] + 1 else ''
    if pose == target or flag or max(vals()) > 0: print(f'V_BATT {pose:18s} OFF {off} ON {on} {vals()}{flag}')
PL.reset(arm)
