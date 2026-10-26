"""Re-pesa SOLO accesorios (no toca cuerpo/prendas/armature/shape keys). Uso:
blender -b WORK.blend --python acc_reweight.py -- Pref rigid:MatA,MatB hug:MatC [--save]
rigid = cada isla de malla (o, con 'A+B+C', todas esas mallas juntas como una sola pieza) recibe los pesos medios de la prenda/piel vecina (pieza rigida que sigue la zona).
hug   = cada vertice copia los pesos (ponderados por 1/d) de los K vertices de prenda mas cercanos (pieza deformable, p.ej. corbata).
Fuente de pesos: vertices de prenda (CLOTH_KEYS) a <4 cm; si no hay, piel. Maximo 4 influencias, normalizadas."""
import bpy, sys, collections
sys.path.insert(0, r'D:\TheLivingCanvas\Tools\npc_pipeline')
import penetration_sweep as PS
from mathutils.kdtree import KDTree
O = bpy.data.objects
K, MAXD = 6, 0.04


def reweight(pref, rigid, hug):
    ob = O[pref + '_Mesh']; me = ob.data
    mats = [m.name if m else '' for m in me.materials]
    cloth, skin, mv = set(), set(), collections.defaultdict(set)
    for pl in me.polygons:
        n = mats[pl.material_index]
        if n.lower().endswith('skin_paint'): skin.update(pl.vertices)
        elif PS.is_cloth(n): cloth.update(pl.vertices)
        else: mv[n].update(pl.vertices)
    skin -= cloth
    protected = cloth | skin
    co = [v.co.copy() for v in me.vertices]   # reposo (basis)
    def kd_of(S):
        S = sorted(S); kd = KDTree(len(S))
        for k, i in enumerate(S): kd.insert(co[i], i)
        kd.balance(); return kd
    kdc, kds = kd_of(cloth), kd_of(skin)
    def src_weights(p):
        res = kdc.find_n(p, K); res = [r for r in res if r[2] <= MAXD]
        if not res: res = [r for r in kds.find_n(p, K) if r[2] <= MAXD] or [kdc.find(p)]
        acc = collections.Counter(); tot = 0
        for _, i, d in res:
            w = 1.0 / (d + 0.003); tot += w
            for g in me.vertices[i].groups:
                if g.weight > 0.001: acc[ob.vertex_groups[g.group].name] += g.weight * w
        return {b: x / tot for b, x in acc.items()}
    def norm4(w):
        top = sorted(w.items(), key=lambda kv: -kv[1])[:4]; s = sum(v for _, v in top) or 1
        return {b: v / s for b, v in top if v / s > 0.01}
    def assign(i, w):
        for g in list(me.vertices[i].groups): ob.vertex_groups[g.group].remove([i])
        for b, v in norm4(w).items(): ob.vertex_groups[b].add([i], v, 'REPLACE')
    def islands(vs):
        vs = set(vs); adj = collections.defaultdict(set)
        for e in me.edges:
            a, b = e.vertices
            if a in vs and b in vs: adj[a].add(b); adj[b].add(a)
        seen, out = set(), []
        for s in vs:
            if s in seen: continue
            comp, st = [], [s]; seen.add(s)
            while st:
                v = st.pop(); comp.append(v)
                for n in adj[v]:
                    if n not in seen: seen.add(n); st.append(n)
            out.append(comp)
        return out
    log = []
    for mode, names in (('rigid', rigid), ('hug', hug)):
        for n in names:
            vs = set().union(*[mv.get(x, set()) for x in n.split('+')]) - protected   # 'A+B' = una sola pieza rigida
            if not vs: log.append((n, 'sin verts')); continue
            if mode == 'hug':
                for i in vs: assign(i, src_weights(co[i]))
                log.append((n, mode, len(vs)))
            else:
                isl = [sorted(vs)] if '+' in n else islands(vs)
                for comp in isl:
                    acc = collections.Counter()
                    for i in comp[::max(1, len(comp) // 12)]:
                        for b, w in src_weights(co[i]).items(): acc[b] += w
                    t = sum(acc.values()) or 1
                    w = {b: x / t for b, x in acc.items()}
                    for i in comp: assign(i, w)
                log.append((n, mode, len(vs), f'{len(isl)} islas'))
    return log


if __name__ == '__main__':
    a = sys.argv[sys.argv.index('--') + 1:]; pref = a[0]; rigid, hug = [], []
    for x in a[1:]:
        if x.startswith('rigid:'): rigid += x[6:].split(',')
        elif x.startswith('hug:'): hug += x[4:].split(',')
    for l in reweight(pref, rigid, hug): print('RW', pref, l)
    if '--save' in a: bpy.ops.wm.save_mainfile(); print('SAVED')
