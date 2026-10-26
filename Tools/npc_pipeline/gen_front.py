"""Laboratorio del refinamiento delantero del dobladillo de Gen (experimento A). Usar en Blender vivo con gen_validate (V) cargado.
build(p) -> {vert: pesos}: parte de los pesos 'final' (arreglo aprobado) y los mezcla hacia los 'orig' en el centro delantero.
  s = sx * sy ; sx = smoothstep((x1 - |x|) / (x1 - x0)) ; sy = smoothstep(-y / ys) ; solo z < zt.  nuevo = (1-s)*final + s*orig  (max 4 inf., normalizado)
measure(variant_weights, poses) -> metricas de aristas del dobladillo (razon deformada/reposo)."""
import bpy, sys, collections
sys.path.insert(0, r'D:\TheLivingCanvas\Tools\npc_pipeline')
sys.modules.pop('layer_clip_scan', None)
import layer_clip_scan as LC
import numpy as np

ob, me, U, L, fu, fl = LC.setup('Gen')
co = {i: me.vertices[i].co.copy() for i in U}
HEM_Z = 1.05
hem = [i for i in U if co[i].z < HEM_Z]; hs = set(hem)
E = [(e.vertices[0], e.vertices[1]) for e in me.edges if e.vertices[0] in hs and e.vertices[1] in hs]
L0 = {e: (co[e[0]] - co[e[1]]).length for e in E}
MIN_L0 = 0.003   # aristas casi nulas en reposo se excluyen de las razones
EM = [e for e in E if L0[e] >= MIN_L0]


def ss(t):
    t = max(0.0, min(1.0, t)); return t * t * (3 - 2 * t)


def sel_strength(i, p):
    c = co[i]
    if c.z >= p['zt']: return 0.0
    return ss((p['x1'] - abs(c.x)) / max(p['x1'] - p['x0'], 1e-6)) * ss(-c.y / p['ys']) * p.get('amp', 1.0)


def build(p, W):
    out = {}
    for i in hem:
        s = sel_strength(i, p)
        fin, org = W['final'][i], W['orig'][i]
        if s <= 0: out[i] = dict(fin); continue
        new = collections.Counter()
        for b, v in fin.items(): new[b] += (1 - s) * v
        for b, v in org.items(): new[b] += s * v
        top = sorted(new.items(), key=lambda kv: -kv[1])[:4]; t = sum(v for _, v in top)
        out[i] = {b: v / t for b, v in top if v / t > 0.01}
    return out


def apply(wd):
    for i, w in wd.items():
        for g in list(me.vertices[i].groups): ob.vertex_groups[g.group].remove([i])
        for b, v in w.items(): ob.vertex_groups[b].add([i], v, 'REPLACE')
    me.update(); bpy.context.view_layer.update()


def ratios():
    ev = ob.evaluated_get(bpy.context.evaluated_depsgraph_get()); m = ev.to_mesh()
    r = {e: (m.vertices[e[0]].co - m.vertices[e[1]].co).length / L0[e] for e in EM}
    ev.to_mesh_clear(); return r


def stats(r):
    v = np.array(list(r.values()))
    lo = min(r, key=r.get); hi = max(r, key=r.get)
    pt = lambda e: tuple(round(x, 2) for x in ((co[e[0]] + co[e[1]]) / 2))
    return dict(c05=int((v < 0.5).sum()), c03=int((v < 0.3).sum()), s15=int((v > 1.5).sum()), s2=int((v > 2).sum()),
                mn=round(float(v.min()), 2), mx=round(float(v.max()), 2), mn_at=pt(lo), mx_at=pt(hi))


def buildB(p, W, ztop=1.05, tmax=0.95, xs=0.06):
    """Variante B: mismo reparto thigh_l/thigh_r que el arreglo aprobado, pero en el centro delantero el reparto lateral es mas ancho (xs -> xsf), asi los dos lados se mueven juntos."""
    zmin = min(co[i].z for i in U); out = {}
    for i in hem:
        c = co[i]; org = W['orig'][i]
        if c.z >= ztop: out[i] = dict(org); continue
        s = sel_strength(i, p)
        x = (ztop - c.z) / (ztop - zmin); t = tmax * (x * x * (3 - 2 * x))
        t *= 1 - s * p.get('tred', 0.0)
        xe = xs + s * (p['xsf'] - xs)
        wl = 0.5 + 0.5 * max(-1.0, min(1.0, c.x / xe)); wr = 1 - wl
        new = collections.Counter()
        for b, v in org.items(): new[b] += (1 - t) * v
        new['thigh_l'] += t * wl; new['thigh_r'] += t * wr
        top = sorted(new.items(), key=lambda kv: -kv[1])[:4]; tt = sum(v for _, v in top)
        out[i] = {b: v / tt for b, v in top if v / tt > 0.01}
    return out
