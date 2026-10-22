"""Staff badge (at heart height, her left chest) and a small sunflower pin above it. Run after mpfb_resolve_clipping.py."""
import bpy, bmesh, math
from mathutils import Vector, Matrix

for n in ('Rose_Badge', 'Rose_Sunflower'):
    o = bpy.data.objects.get(n)
    if o:
        bpy.data.objects.remove(o)


def mat(name, col, metal=0.0, rough=0.5):
    m = bpy.data.materials.get(name) or bpy.data.materials.new(name)
    m.use_nodes = True
    b = next(n for n in m.node_tree.nodes if n.type == 'BSDF_PRINCIPLED')
    b.inputs['Base Color'].default_value = col
    b.inputs['Metallic'].default_value = metal
    b.inputs['Roughness'].default_value = rough
    return m


gold = bpy.data.materials['Gold']
card = mat('Badge_Card', (0.80, 0.82, 0.85, 1), 0.3, 0.35)          # silver card
text = mat('Badge_Text', (0.12, 0.10, 0.08, 1))
petal = mat('Sunflower_Petal', (1.0, 0.55, 0.0, 1))
core = mat('Sunflower_Core', (0.30, 0.17, 0.06, 1))
dg = bpy.context.evaluated_depsgraph_get()
scene = bpy.context.scene


def place(x, z):
    hit = scene.ray_cast(dg, Vector((x, -0.6, z)), Vector((0, 1, 0)))
    if not hit[0] or hit[4].name not in ('Rose_Cardigan', 'Rose_Blouse'):
        raise RuntimeError('no cloth at %s %s (hit %s)' % (x, z, hit[4]))
    loc, nor = hit[1], hit[2].normalized()
    zax = nor
    xax = Vector((0, 0, 1)).cross(zax).normalized()
    yax = zax.cross(xax)
    M = Matrix(((xax.x, yax.x, zax.x), (xax.y, yax.y, zax.y), (xax.z, yax.z, zax.z))).to_4x4()
    return loc, nor, M


# ---- badge: heart height, left chest
loc, nor, M = place(0.085, 1.275)
b = bmesh.new()


def box(c, sx, sy, sz, mi):
    r = bmesh.ops.create_cube(b, size=1.0)
    for v in r['verts']:
        v.co = Vector((v.co.x * sx, v.co.y * sy, v.co.z * sz)) + c
    for f in b.faces:
        if all(v in r['verts'] for v in f.verts):
            f.material_index = mi
            f.smooth = False


box(Vector((0, 0, 0.0015)), 0.050, 0.022, 0.003, 0)           # gold frame
box(Vector((0, 0, 0.0033)), 0.045, 0.017, 0.0012, 1)           # silver card
box(Vector((-0.013, 0.0, 0.0042)), 0.012, 0.009, 0.0008, 2)    # logo block
for i in range(2):
    box(Vector((0.009, 0.003 - i * 0.006, 0.0042)), 0.024, 0.0016, 0.0008, 2)
for v in b.verts:
    v.co = M @ v.co + loc + nor * 0.002
me = bpy.data.meshes.new('Rose_Badge')
b.to_mesh(me)
b.free()
o = bpy.data.objects.new('Rose_Badge', me)
bpy.context.collection.objects.link(o)
for m in (gold, card, text):
    me.materials.append(m)

# ---- sunflower pin: flat enamel-pin look (gold metal outline, flat yellow petals, brown grid centre), about 2.8 cm across
petal = mat('Sunflower_Yellow', (0.85, 0.55, 0.0, 1), 0.0, 0.6)             # flat enamel (linear values, so this reads as sunflower yellow)
brown_d = mat('Sunflower_BrownDark', (0.025, 0.010, 0.003, 1), 0.0, 0.8)
brown_l = mat('Sunflower_BrownLight', (0.10, 0.038, 0.010, 1), 0.0, 0.8)
loc, nor, M = place(0.072, 1.325)
b = bmesh.new()
MAT_YELLOW, MAT_GOLD, MAT_BD, MAT_BL = 0, 1, 2, 3


def prism(pts, z0, h, mi):
    """Flat shape as a thin solid: bottom face + top face + side wall."""
    bot = [b.verts.new((x, y, z0)) for x, y in pts]
    top = [b.verts.new((x, y, z0 + h)) for x, y in pts]
    n = len(pts)
    faces = [b.faces.new(top), b.faces.new(bot[::-1])]
    for i in range(n):
        j = (i + 1) % n
        faces.append(b.faces.new((bot[i], bot[j], top[j], top[i])))
    for f in faces:
        f.material_index = mi
        f.smooth = False


def ellipse(cx, cy, ang, L, W, n=14):
    ca, sa = math.cos(ang), math.sin(ang)
    out = []
    for k in range(n):
        t = 2 * math.pi * k / n
        u, v = math.cos(t) * L, math.sin(t) * W * (1 - 0.15 * math.cos(t))           # slightly fuller toward the tip like the reference
        out.append((cx + u * ca - v * sa, cy + u * sa + v * ca))
    return out[::-1] if False else out


def disc(r, n=28):
    return [(math.cos(2 * math.pi * k / n) * r, math.sin(2 * math.pi * k / n) * r) for k in range(n)]


NPET = 20
RC, LHALF, WHALF = 0.0102, 0.0072, 0.0019
for i in range(NPET):
    a = 2 * math.pi * i / NPET
    cx, cy = math.cos(a) * RC, math.sin(a) * RC
    prism(ellipse(cx, cy, a, LHALF + 0.0005, WHALF + 0.0005), 0.0, 0.0006, MAT_GOLD)            # gold outline
for i in range(NPET):
    a = 2 * math.pi * i / NPET
    cx, cy = math.cos(a) * RC, math.sin(a) * RC
    prism(ellipse(cx, cy, a, LHALF, WHALF), 0.0006, 0.0003, MAT_YELLOW)                          # flat yellow enamel
    ca_, sa_ = math.cos(a), math.sin(a)
    for off in (-0.0009, 0.0, 0.0009):                                                           # fine gold lines running out from the centre
        x0, y0 = ca_ * 0.0085 - sa_ * off, sa_ * 0.0085 + ca_ * off
        x1, y1 = ca_ * 0.0120 - sa_ * off * 0.7, sa_ * 0.0120 + ca_ * off * 0.7
        w = 0.00012
        px, py = -sa_ * w, ca_ * w
        prism([(x0 - px, y0 - py), (x1 - px, y1 - py), (x1 + px, y1 + py), (x0 + px, y0 + py)], 0.0009, 0.00018, MAT_GOLD)
prism(disc(0.0082), 0.0006, 0.0003, MAT_GOLD)                                                   # gold ring around the centre
prism(disc(0.0076), 0.0009, 0.0003, MAT_BD)                                                     # dark brown seed bed
STEP, TILE = 0.00165, 0.00115
g = int(0.0076 / STEP) + 1
for ix in range(-g, g + 1):
    for iy in range(-g, g + 1):
        x, y = ix * STEP, iy * STEP
        if math.hypot(x, y) + TILE * 0.75 < 0.0074:
            h = TILE / 2
            prism([(x - h, y - h), (x + h, y - h), (x + h, y + h), (x - h, y + h)], 0.0012, 0.00022, MAT_BL)   # lighter brown seed squares
# pin back plate (hidden behind the petals)
prism(disc(0.0070, 12), -0.0010, 0.0010, MAT_GOLD)
bmesh.ops.recalc_face_normals(b, faces=b.faces)
for v in b.verts:
    v.co = M @ v.co + loc + nor * 0.0016
me = bpy.data.meshes.new('Rose_Sunflower')
b.to_mesh(me)
b.free()
o = bpy.data.objects.new('Rose_Sunflower', me)
bpy.context.collection.objects.link(o)
for m in (petal, gold, brown_d, brown_l):
    me.materials.append(m)
for p in me.polygons:
    p.use_smooth = False
for _m in (petal, brown_d, brown_l):
    _b = next(n for n in _m.node_tree.nodes if n.type == 'BSDF_PRINCIPLED')
    if 'Specular IOR Level' in _b.inputs:
        _b.inputs['Specular IOR Level'].default_value = 0.1
print('badge and flat enamel sunflower placed')
