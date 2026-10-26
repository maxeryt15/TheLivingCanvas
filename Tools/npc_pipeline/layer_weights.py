"""Hace que el dobladillo de la prenda superior larga (abrigo/chaqueta) acompane a los muslos, para que el pantalon no lo atraviese al caminar/agacharse.
Solo toca vertices de la isla superior por debajo de ztop (el cuerpo, el pantalon y los demas materiales no se tocan).
t = tmax * smoothstep((ztop - z) / (ztop - zmin)); los pesos nuevos = (1-t) * actuales + t * (thigh_l / thigh_r repartidos por x: |x|>=xs -> un solo muslo).
Maximo 4 influencias, normalizado. Uso: layer_weights.reweight("Gen") (defecto ztop=1.05, tmax=0.95, xs=0.06; v1 era 0.95/0.85/0.08)"""
import bpy, sys, collections
sys.path.insert(0, r'D:\TheLivingCanvas\Tools\npc_pipeline')
import layer_clip_scan as LC


def reweight(pref, ztop=1.05, tmax=0.95, xs=0.06):
    ob, me, U, L, fu, fl = LC.setup(pref)
    zmin = min(me.vertices[i].co.z for i in U); n = 0
    for i in U:
        c = me.vertices[i].co; z = c.z
        if z >= ztop: continue
        x = (ztop - z) / (ztop - zmin); t = tmax * (x * x * (3 - 2 * x))
        wl = 0.5 + 0.5 * max(-1.0, min(1.0, c.x / xs)); wr = 1 - wl
        cur = {ob.vertex_groups[g.group].name: g.weight for g in me.vertices[i].groups}
        new = collections.Counter()
        for b, w in cur.items(): new[b] += (1 - t) * w
        new['thigh_l'] += t * wl; new['thigh_r'] += t * wr
        top = sorted(new.items(), key=lambda kv: -kv[1])[:4]; s = sum(v for _, v in top)
        for g in list(me.vertices[i].groups): ob.vertex_groups[g.group].remove([i])
        for b, v in top:
            if v / s > 0.01: ob.vertex_groups[b].add([i], v / s, 'REPLACE')
        n += 1
    return n
