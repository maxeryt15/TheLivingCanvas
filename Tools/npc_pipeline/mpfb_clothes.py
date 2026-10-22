"""Faceted clothes for the Rose NPC, built from the low-poly body (Rose_Low).
Run inside Blender: exec(open(path).read()). Clean cuts come from bisect planes, so hems and cuffs are straight.
Garments: cardigan (V opening, sleeves end before the wrist), blouse, collar, trousers, shoes.
"""
import bpy, bmesh, math
from mathutils import Vector

NAMES = ('Rose_Trousers', 'Rose_Blouse', 'Rose_Cardigan', 'Rose_Shoes', 'Rose_Collar')
for n in NAMES:
    ob = bpy.data.objects.get(n)
    if ob:
        bpy.data.objects.remove(ob)

low = bpy.data.objects['Rose_Low']
J = {'neck': Vector((0, -0.007, 1.409)), 'pelvis': Vector((0, -0.012, 0.868)),
     'sh': Vector((0.168, -0.015, 1.344)), 'el': Vector((0.313, -0.013, 1.169)), 'wr': Vector((0.431, -0.176, 1.065)),
     'ul': Vector((0.11, -0.012, 0.868)), 'kn': Vector((0.158, -0.032, 0.45)), 'an': Vector((0.22, 0.001, 0.075))}


def mir(v):
    return Vector((-v.x, v.y, v.z))


def seg(p, a, b):
    ab = b - a
    t = max(0, min(1, (p - a).dot(ab) / ab.length_squared))
    return (a + ab * t - p).length


bones = [('torso', J['neck'], J['pelvis'], 0.19)]
for s, mm in ((1, lambda v: v), (-1, mir)):
    k = 'armR' if s > 0 else 'armL'
    bones += [(k, mm(J['sh']), mm(J['el']), 0.06), (k, mm(J['el']), mm(J['wr']), 0.05),
              ('leg', mm(J['ul']), mm(J['kn']), 0.10), ('leg', mm(J['kn']), mm(J['an']), 0.07)]


def label(p):
    if abs(p.x) > 0.21 and p.z > 0.8:           # anything out at arm distance is arm or hand, never torso
        return min(((seg(p, a, b) / r), n) for n, a, b, r in bones if n.startswith('arm'))[1]
    return min(((seg(p, a, b) / r), n) for n, a, b, r in bones)[1]


fdir = {'armR': (J['wr'] - J['el']).normalized(), 'armL': (mir(J['wr']) - mir(J['el'])).normalized()}
SLEEVE_END = 0.025                                   # metres past the wrist joint: sleeves cover the wrist bone
wpt = {'armR': J['wr'] + fdir['armR'] * SLEEVE_END, 'armL': mir(J['wr']) + fdir['armL'] * SLEEVE_END}

bm = bmesh.new()
bm.from_mesh(low.data)


def cut(co, no):
    bmesh.ops.bisect_plane(bm, geom=bm.verts[:] + bm.edges[:] + bm.faces[:], dist=0.0001, plane_co=co, plane_no=no)


for z in (0.075, 0.86, 0.90, 0.93, 0.945, 0.96, 0.985, 1.40):
    cut(Vector((0, 0, z)), Vector((0, 0, 1)))
for k in ('armR', 'armL'):
    cut(wpt[k], fdir[k])
for s in (1, -1):                                 # V opening of the cardigan
    d = Vector((s * 0.040, 0, 0.485))
    n = Vector((d.z, 0, -d.x)).normalized() * (1 if s > 0 else -1)
    cut(Vector((s * 0.012, 0, 0.90)), n)
bm.faces.ensure_lookup_table()
bm.verts.ensure_lookup_table()
bm.normal_update()
vn = {v: v.normal.copy() for v in bm.verts}
lab = {f: label(f.calc_center_median()) for f in bm.faces}


def mat(name, col, rough=0.9):
    m = bpy.data.materials.get(name) or bpy.data.materials.new(name)
    m.use_nodes = True
    b = next(n for n in m.node_tree.nodes if n.type == 'BSDF_PRINCIPLED')
    b.inputs['Base Color'].default_value = col
    b.inputs['Roughness'].default_value = rough
    return m


olive = mat('Cardigan_Olive', (0.30, 0.34, 0.12, 1))
cream = mat('Blouse_Cream', (0.84, 0.78, 0.64, 1))
gray = mat('Trousers_Gray', (0.20, 0.20, 0.22, 1))
brown = mat('Shoes_Brown', (0.22, 0.11, 0.06, 1), 0.6)


def vopen(c):
    zt = max(0, min(1, (c.z - 0.90) / 0.485))
    return c.y < -0.01 and abs(c.x) < 0.012 + 0.038 * zt


def sleeve(c, l):
    if l not in ('armR', 'armL') or c.z < 0.80:
        return False
    return (c - wpt[l]).dot(fdir[l]) < 0


def torso(c, l):
    return l == 'torso' and abs(c.x) < 0.21


SEL = {
    'Rose_Cardigan': lambda c, l: (torso(c, l) and 0.86 <= c.z <= 1.40 and not vopen(c)) or sleeve(c, l),
    'Rose_Blouse': lambda c, l: torso(c, l) and 0.96 <= c.z <= 1.40,      # tucked into the waistband, so it never overlaps the trousers
    'Rose_Collar': lambda c, l: False,
    'Rose_Trousers': lambda c, l: (torso(c, l) and 0.075 < c.z <= 0.985) or (l == 'leg' and c.z > 0.075),
    'Rose_Shoes': lambda c, l: l == 'leg' and c.z <= 0.115}
OFF = {'Rose_Cardigan': 0.026, 'Rose_Blouse': 0.010, 'Rose_Collar': 0.015, 'Rose_Trousers': 0.012, 'Rose_Shoes': 0.018}   # layer order: body < blouse < trousers < cardigan
MAT = {'Rose_Cardigan': olive, 'Rose_Blouse': cream, 'Rose_Collar': cream, 'Rose_Trousers': gray, 'Rose_Shoes': brown}
for name, sel in SEL.items():
    b2 = bmesh.new()
    vm = {}
    for f in bm.faces:
        if not sel(f.calc_center_median(), lab[f]):
            continue
        vs = []
        for v in f.verts:
            if v not in vm:
                vm[v] = b2.verts.new(v.co + vn[v] * OFF[name])
            vs.append(vm[v])
        try:
            b2.faces.new(vs).smooth = False
        except ValueError:
            pass
    me = bpy.data.meshes.new(name)
    b2.to_mesh(me)
    b2.free()
    o = bpy.data.objects.new(name, me)
    bpy.context.collection.objects.link(o)
    me.materials.append(MAT[name])
    sm = o.modifiers.new('s', 'SOLIDIFY')
    sm.thickness = 0.005
    sm.offset = -1
    print(name, len(me.polygons))
