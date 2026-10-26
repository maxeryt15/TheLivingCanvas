"""Restaura accesorios finos (placas/parches/hombreras) que shell_cull fragmento o que quedaron hundidos bajo la prenda.
1) Borra las caras actuales de esos materiales. 2) Re-crea las caras completas desde el JSON (accessory_extract.py, version sin cascara).
3) Pesos = los del vertice de prenda mas cercano (asi siguen los arreglos de pesos actuales). 4) Levanta cada vertice sobre la prenda
(holgura LIFT m, hacia fuera) para que no se hunda ni haga z-fighting. Shape keys: los vertices nuevos copian su posicion final en cada clave.
Uso: blender -b NPCs_Shell_Face.blend --python fix_accessories.py -- salida.blend Prefijo=acc.json[:weld] [Prefijo=acc.json ...]
':weld' funde vertices duplicados (cintas como una sola pieza continua).
"""
import bpy, bmesh, sys, json
from mathutils import Vector
from mathutils.kdtree import KDTree
from mathutils.bvhtree import BVHTree

LIFT = 0.004
WELD_DIST = 0.0015
CLOTH_KEYS = ('clothes_paint', 'suit_', 'aproncloth', 'blouse', 'scarfcloth')


def fix(pref, jpath, weld=False):
    ob = bpy.data.objects[pref + '_Mesh']; me = ob.data
    data = json.load(open(jpath))
    mats = {f['mat'] for f in data['faces']}
    midx = {m.name: i for i, m in enumerate(me.materials) if m}
    bm = bmesh.new(); bm.from_mesh(me)
    deform = bm.verts.layers.deform.verify()
    shapes = list(bm.verts.layers.shape)
    uvl = bm.loops.layers.uv.active
    bm.faces.ensure_lookup_table()
    old = [f for f in bm.faces if me.materials[f.material_index] and me.materials[f.material_index].name in mats]
    oldv = {tuple(round(c, 4) for c in v.co) for f in old for v in f.verts}
    new_keys = {tuple(round(c, 4) for c in co) for f in data['faces'] for co in f['co']}
    print(f'{pref}: caras actuales {len(old)} -> JSON {len(data["faces"])}; verts actuales que coinciden con JSON: {len(oldv & new_keys)}/{len(oldv)}')
    kdn = KDTree(len(new_keys)); [kdn.insert(Vector(k), i) for i, k in enumerate(new_keys)]; kdn.balance()
    ds = sorted(kdn.find(Vector(k))[2] for k in oldv)
    print(f'{pref}: dist. vertice actual -> JSON: mediana {ds[len(ds)//2]*1000:.2f} mm, max {ds[-1]*1000:.2f} mm')
    bmesh.ops.delete(bm, geom=old, context='FACES')
    bm.verts.ensure_lookup_table(); bm.faces.ensure_lookup_table()
    cloth_faces = [f for f in bm.faces if me.materials[f.material_index] and any(k in me.materials[f.material_index].name.lower() for k in CLOTH_KEYS)]
    cloth_verts = {v for f in cloth_faces for v in f.verts if len(v[deform]) > 0}
    cv = list(cloth_verts)
    kd = KDTree(len(cv)); [kd.insert(v.co, i) for i, v in enumerate(cv)]; kd.balance()
    cverts = [v.co.copy() for v in bm.verts]
    bvh = BVHTree.FromPolygons(cverts, [tuple(v.index for v in f.verts) for f in cloth_faces])
    cache = {}
    nf = 0
    for fd in data['faces']:
        vs = []
        for co in fd['co']:
            k = tuple(round(c, 5) for c in co)
            v = cache.get(k)
            if v is None:
                v = bm.verts.new(Vector(co))
                near = cv[kd.find(v.co)[1]]
                for g, w in near[deform].items():
                    v[deform][g] = w
                cache[k] = v
            vs.append(v)
        try:
            f = bm.faces.new(vs)
        except ValueError:
            continue
        f.material_index = midx[fd['mat']]
        for l, uv in zip(f.loops, fd['uv']):
            l[uvl].uv = uv
        f.smooth = False
        nf += 1
    if weld:  # une los vertices duplicados (cintas = tramos sueltos) en una sola pieza continua
        bmesh.ops.remove_doubles(bm, verts=list(cache.values()), dist=WELD_DIST)
    cache = {k: v for k, v in cache.items() if v.is_valid}
    lifted = 0
    for v in cache.values():
        loc, nor, idx, dist = bvh.find_nearest(v.co)
        if loc is None or dist > 0.03:
            continue
        d = (v.co - loc).dot(nor)
        if d < LIFT:
            v.co = loc + nor * LIFT; lifted += 1
    for v in cache.values():
        for s in shapes:
            v[s] = v.co.copy()
    bm.normal_update()
    bm.to_mesh(me); bm.free(); me.update()
    print(f'{pref}: caras creadas {nf}, verts nuevos {len(cache)}, levantados {lifted}')


a = sys.argv[sys.argv.index('--') + 1:]
for item in a[1:]:
    p, j = item.split('=')
    weld = j.endswith(':weld')
    fix(p, j[:-5] if weld else j, weld)
bpy.ops.wm.save_as_mainfile(filepath=a[0])
print('FIXDONE', a[0])
