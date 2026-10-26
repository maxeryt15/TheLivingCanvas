"""Tourist: la camiseta queda 3-4 mm hundida en la banda del short (lado izquierdo de la cadera) al caminar sin correctivos (Unity). Se saca la camiseta DELTA m hacia fuera en la zona
z 0.93-1.12 (peso 1 hasta 1.06, baja a 0 en 1.12), con el mismo desplazamiento en todas las shape keys. Uso: blender -b WORK.blend --python fix_tou_tank.py -- [--delta 0.007 --save]"""
import bpy, sys, collections
a = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else []
def opt(k, d): return float(a[a.index(k) + 1]) if k in a else d
DELTA = opt('--delta', 0.007)
ob = bpy.data.objects['Tou_Mesh']; me = ob.data; mats = [m.name for m in me.materials]; CL = mats.index('Tou_clothes_Paint'); assert not ob.get('tlc_tank_out'), 'ya aplicado'
cf = [p for p in me.polygons if p.material_index == CL]; par = {}
def fd(x):
    while par[x] != x: par[x] = par[par[x]]; x = par[x]
    return x
for p in cf:
    for v in p.vertices: par.setdefault(v, v)
for p in cf:
    vs = list(p.vertices)
    for v in vs[1:]: par[fd(v)] = fd(vs[0])
isl = collections.defaultdict(set)
for v in par: isl[fd(v)].add(v)
big = sorted(isl.values(), key=len, reverse=True)[:2]; up = max(big, key=lambda c: sum(me.vertices[v].co.z for v in c))
delta = {}
for v in up:
    z = me.vertices[v].co.z
    if 0.93 <= z <= 1.12:
        w = 1.0 if z <= 1.06 else (1.12 - z) / 0.06
        delta[v] = me.vertices[v].normal.normalized() * DELTA * w
for k in me.shape_keys.key_blocks:
    for v, d in delta.items(): k.data[v].co += d
for v, d in delta.items(): me.vertices[v].co += d
me.update(); ob['tlc_tank_out'] = DELTA
print('TANK moved', len(delta))
if '--save' in a: bpy.ops.wm.save_mainfile(); print('TANK saved')
