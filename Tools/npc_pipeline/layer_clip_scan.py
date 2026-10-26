"""Mide clipping entre prenda superior e inferior (solo mide). Uso: blender -b X.blend --python layer_clip_scan.py -- Pref [Pref..]
Islas de prenda: superior = zmax>1.3 y zmin>0.45 (mayor); inferior = isla con zmin<0.7 y zmax en [0.88,1.12] (pantalon/falda/short).
V1 = vertices de la superior hundidos en la inferior (dist con signo a la inferior < 0) dentro de la zona de solape;
V2 = vertices de la inferior que quedan por fuera de la superior (dist con signo > 0) cerca de ella.
Se reporta reposo (estatico) y, por pose (24 + Walk), el empeoramiento respecto al reposo. Salida: JSON + lineas LC."""
import bpy, sys, json, collections
sys.path.insert(0, r'D:\TheLivingCanvas\Tools\npc_pipeline')
import pose_lib as PL, penetration_sweep as PS
from mathutils.bvhtree import BVHTree
O = bpy.data.objects; S = bpy.context.scene
NEAR = 0.05


def islands(me, cf):
    adj = collections.defaultdict(set)
    for pl in cf:
        for a in pl.vertices:
            for b in pl.vertices:
                if a != b: adj[a].add(b)
    seen, out = set(), []
    for s in list(adj):
        if s in seen: continue
        comp, st = [], [s]; seen.add(s)
        while st:
            v = st.pop(); comp.append(v)
            for q in adj[v]:
                if q not in seen: seen.add(q); st.append(q)
        out.append(set(comp))
    return out


def setup(pref):
    ob = O[pref + '_Mesh']; me = ob.data; mats = [m.name if m else '' for m in me.materials]
    cf = [pl for pl in me.polygons if PS.is_cloth(mats[pl.material_index]) and 'apron' not in mats[pl.material_index].lower() and 'scarf' not in mats[pl.material_index].lower()]
    isl = islands(me, cf); info = []
    for c in isl:
        z = [me.vertices[v].co.z for v in c]; info.append((len(c), min(z), max(z), c))
    up = [i for i in info if i[2] > 1.3 and i[1] > 0.45 and i[0] > 150]
    lo = [i for i in info if i[1] < 0.7 and 0.88 <= i[2] <= 1.12 and i[0] > 150]
    if not up or not lo: return None
    up = max(up, key=lambda i: i[0]); lo = max(lo, key=lambda i: i[0])
    U, L = up[3], lo[3]
    fu = [pl for pl in cf if pl.vertices[0] in U]; fl = [pl for pl in cf if pl.vertices[0] in L]
    return ob, me, U, L, fu, fl


def pts(ob):
    ev = ob.evaluated_get(bpy.context.evaluated_depsgraph_get()); m = ev.to_mesh(); P = [v.co.copy() for v in m.vertices]; ev.to_mesh_clear(); return P


def measure(ob, me, U, L, fu, fl, zlo, zhi):
    P = pts(ob)
    bl = BVHTree.FromPolygons(P, [tuple(p.vertices) for p in fl]); bu = BVHTree.FromPolygons(P, [tuple(p.vertices) for p in fu])
    v1, v2 = {}, {}
    for i in U:
        if not (zlo <= P[i].z <= zhi): continue
        loc, nor, idx, d = bl.find_nearest(P[i])
        if loc is not None and d < NEAR: v1[i] = (P[i] - loc).dot(nor)      # <0: hundida en el pantalon
    for i in L:
        if not (zlo <= P[i].z <= zhi): continue
        loc, nor, idx, d = bu.find_nearest(P[i])
        if loc is not None and d < NEAR: v2[i] = (P[i] - loc).dot(nor)      # >0: pantalon por fuera de la camisa
    return P, v1, v2


def run(pref):
    r = setup(pref)
    if not r: print('LC', pref, 'sin par superior/inferior separable'); return
    ob, me, U, L, fu, fl = r; arm = O[pref + '_Rig']
    zU = sorted(me.vertices[i].co.z for i in U)[0]; zL = max(me.vertices[i].co.z for i in L)
    zlo, zhi = zU - 0.02, zL + 0.05
    PL.reset(arm); P0, a0, b0 = measure(ob, me, U, L, fu, fl, zlo, zhi)
    bone = lambda i: max(me.vertices[i].groups, key=lambda g: g.weight).group
    vg = lambda i: ob.vertex_groups[bone(i)].name
    stat1 = sorted(((-d, i) for i, d in a0.items() if d < -0.002), reverse=True)
    stat2 = sorted(((d, i) for i, d in b0.items() if d > 0.002), reverse=True)
    res = {'zone': (round(zlo, 2), round(zhi, 2)), 'rest_V1': (len(stat1), round(stat1[0][0] * 1000, 1) if stat1 else 0), 'rest_V2': (len(stat2), round(stat2[0][0] * 1000, 1) if stat2 else 0), 'poses': {}}
    cal = PL.calibrate(arm); walk = next((a for a in bpy.data.actions if f'_{PS.NAMES[pref]}_Walk' in a.name), None)
    def ev(tag):
        P, a, b = measure(ob, me, U, L, fu, fl, zlo, zhi)
        g1 = [(a0.get(i, 0) - d, i) for i, d in a.items() if a0.get(i, 0) - d > 0.003]   # empeoramiento respecto a reposo
        g2 = [(d - b0.get(i, 0), i) for i, d in b.items() if d - b0.get(i, 0) > 0.003]
        g1.sort(reverse=True); g2.sort(reverse=True)
        def loc(lst):
            if not lst: return None
            i = lst[0][1]; return dict(mm=round(lst[0][0] * 1000, 1), n=len(lst), bone=vg(i), x='L' if P[i].x > 0.02 else ('R' if P[i].x < -0.02 else 'C'), z=round(P[i].z, 2), y='front' if P[i].y < 0 else 'back')
        return dict(V1=loc(g1), V2=loc(g2))
    for name, st in cal.items():
        PL.apply(arm, st); res['poses'][name] = ev(name)
    if walk:
        PL.reset(arm); ad = arm.animation_data or arm.animation_data_create(); ad.action = walk; ad.action_slot = walk.slots[0]
        for f in range(1, 41, 4): S.frame_set(f); res['poses'][f'Walk@{f}'] = ev(f'Walk@{f}')
        ad.action = None
    PL.reset(arm)
    json.dump(res, open(PS.OUT + f'/layer_clip_{pref}.json', 'w'), indent=1)
    print('LC', pref, 'zone', res['zone'], 'rest V1', res['rest_V1'], 'V2', res['rest_V2'])
    for k, v in res['poses'].items():
        if (v['V1'] and v['V1']['mm'] > 8 and v['V1']['n'] >= 3) or (v['V2'] and v['V2']['mm'] > 8 and v['V2']['n'] >= 3): print('LC_BAD', pref, k, v)


if __name__ == '__main__':
    for p in (sys.argv[sys.argv.index('--') + 1:] or list(PS.NAMES)): run(p)
    print('LCDONE')
