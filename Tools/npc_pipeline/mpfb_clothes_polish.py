"""Polish pass for the Rose NPC clothes. Run after mpfb_clothes.py (exec in Blender).
Collar with lapels, ribbed hem/cuffs/placket, buttons, and a few folds at elbows, knees and trouser hems.
"""
import bpy, bmesh, math
from mathutils import Vector, Matrix
from mathutils.bvhtree import BVHTree

for n in ('Rose_Collar', 'Rose_Buttons'):
    ob = bpy.data.objects.get(n)
    if ob:
        bpy.data.objects.remove(ob)


def mat(name, col, rough=0.9):
    m = bpy.data.materials.get(name) or bpy.data.materials.new(name)
    m.use_nodes = True
    b = next(n for n in m.node_tree.nodes if n.type == 'BSDF_PRINCIPLED')
    b.inputs['Base Color'].default_value = col
    b.inputs['Roughness'].default_value = rough
    return m


cream = bpy.data.materials['Blouse_Cream']
rib = mat('Cardigan_Rib', (0.10, 0.13, 0.04, 1))        # dark olive trim
ivory = mat('Button_Ivory', (0.80, 0.72, 0.52, 1), 0.5)

# ---------------------------------------------------------------- collar: snug stand collar + two lapel points, following the neck surface
low = bpy.data.objects['Rose_Low']
bvh_body = BVHTree.FromObject(low, bpy.context.evaluated_depsgraph_get())
NECK_C = Vector((0, -0.030, 0))


def neck_pt(phi, z, off):
    d = Vector((math.sin(phi), -math.cos(phi), 0))
    o = NECK_C + d * 0.16
    o.z = z
    hit = bvh_body.ray_cast(o, -d, 0.16)
    return None if hit[0] is None else hit[0] + hit[1].normalized() * off


bm = bmesh.new()
NT = 40
levels = [(1.386, 0.0140), (1.402, 0.0160), (1.416, 0.0150)]        # a simple round neckline trim: flat, even, closed circle
ring = []
for z, off in levels:
    row = []
    for i in range(NT):
        phi = 2 * math.pi * i / NT                                  # 0 = front
        p = neck_pt(phi, z, off)
        row.append(bm.verts.new(p) if p is not None else None)
    ring.append(row)
for k in range(len(levels) - 1):
    for i in range(NT):
        q = (ring[k][i], ring[k][(i + 1) % NT], ring[k + 1][(i + 1) % NT], ring[k + 1][i])
        if all(v is not None for v in q):
            bm.faces.new(q).smooth = False
for _ in range(4):                                                   # relax around the circle so the edge is a clean round line
    for r in range(len(levels)):
        pos = [ring[r][i].co.copy() for i in range(NT)]
        for i in range(NT):
            ring[r][i].co = pos[i].lerp((pos[i - 1] + pos[(i + 1) % NT]) / 2, 0.5)
bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
me = bpy.data.meshes.new('Rose_Collar')
bm.to_mesh(me)
bm.free()
col = bpy.data.objects.new('Rose_Collar', me)
bpy.context.collection.objects.link(col)
me.materials.append(cream)
s_m = col.modifiers.new('s', 'SOLIDIFY')
s_m.thickness = 0.003
s_m.offset = 0

# ---------------------------------------------------------------- cardigan: ribbed hem, cuffs and front band
card = bpy.data.objects['Rose_Cardigan']
me = card.data
if len(me.materials) < 2:
    me.materials.append(rib)
bm = bmesh.new()
bm.from_mesh(me)
bm.normal_update()
J_wr = {1: Vector((0.431, -0.176, 1.065)), -1: Vector((-0.431, -0.176, 1.065))}
J_el = {1: Vector((0.313, -0.013, 1.169)), -1: Vector((-0.313, -0.013, 1.169))}
ribbed = set()
for f in bm.faces:
    c = f.calc_center_median()
    zt = max(0, min(1, (c.z - 0.90) / 0.485))
    near_hem = c.z < 0.905 and abs(c.x) < 0.22
    near_front = c.y < -0.01 and abs(c.x) < 0.22 and 0.0 < (abs(c.x) - (0.012 + 0.038 * zt)) < 0.018
    near_cuff = False
    for s in (1, -1):
        d = (J_wr[s] - J_el[s]).normalized()
        w = J_wr[s] + d * 0.025
        if c.x * s > 0.2 and -0.045 < (c - w).dot(d) < 0:
            near_cuff = True
    if near_hem or near_cuff:
        f.material_index = 1
        ribbed.add(f)
rv = {v for f in ribbed for v in f.verts}
for v in rv:
    v.co += v.normal * 0.0045                                 # raised knit band
# hem: a ribbed, rolled band that rests on the hips. Lower at the back, curving up into rounded front corners.
low = bpy.data.objects['Rose_Low']
bvh_body = BVHTree.FromObject(low, bpy.context.evaluated_depsgraph_get())


def sstep(a, b, x):
    t = max(0, min(1, (x - a) / (b - a)))
    return t * t * (3 - 2 * t)


bmesh.ops.delete(bm, geom=[f for f in bm.faces if f.calc_center_median().z < 0.9449 and abs(f.calc_center_median().x) < 0.22], context='FACES')
bmesh.ops.delete(bm, geom=[v for v in bm.verts if not v.link_faces], context='VERTS')
body_set = set(bm.verts)                                   # everything that exists before the hem band is built
CEN = Vector((0, -0.012, 0))
GAP = 0.115


def hem_z(phi):
    a = abs(phi)
    back = 0.020 * sstep(1.6, math.pi, a)                       # a little longer at the back
    return 0.848 - back + 0.062 * sstep(1.25, GAP, a)           # rises smoothly into rounded front corners


# the hem band is EXTRUDED from the body's lower cut edge (no separate strip), so it is welded to the body by construction
def _is_hem_edge(e):
    a, b = e.verts[0].co, e.verts[1].co
    m = (a + b) / 2
    return (e.is_boundary and 0.92 < m.z < 0.975 and abs(m.x) < 0.24
            and not (m.y < -0.03 and abs(m.x) < 0.07))             # the front V edges are not part of the hem


hem_edges = [e for e in bm.edges if _is_hem_edge(e)]
for v in {v for e in hem_edges for v in e.verts}:
    v.co.z = 0.945                                                   # level the lower cut edge (normal offsets had made it stepped)
ROWS_H = [(0.30, 0.0300), (0.58, 0.0275), (1.00, 0.0235)]        # (how far down toward the hem line, offset above the body)
z0map = {v: v.co.z for e in hem_edges for v in e.verts}            # each chain remembers the height of its top edge
for frac, off in ROWS_H:
    prev_row = {v for e in hem_edges for v in e.verts}
    ext = bmesh.ops.extrude_edge_only(bm, edges=hem_edges)
    nv = [g for g in ext['geom'] if isinstance(g, bmesh.types.BMVert)]
    ne = [g for g in ext['geom'] if isinstance(g, bmesh.types.BMEdge) and g.is_boundary]
    for v in nv:
        src = next((e.other_vert(v) for e in v.link_edges if e.other_vert(v) in prev_row), None)
        z0 = z0map.get(src, 0.945)
        z0map[v] = z0
        phi = math.atan2(v.co.x, -(v.co.y - CEN.y))
        z = z0 + (hem_z(phi) - z0) * frac
        loc, nor, idx, dist = bvh_body.find_nearest(Vector((v.co.x, v.co.y, z)))
        v.co = loc + nor * (off + 0.0014 * math.cos(math.atan2(v.co.x, v.co.y) * 40.0))     # soft vertical rib
        v.co.z = max(z, 0.0)
    for f in [g for g in ext['geom'] if isinstance(g, bmesh.types.BMFace)]:
        f.material_index = 1
        f.smooth = False
    hem_edges = ne
bmesh.ops.recalc_face_normals(bm, faces=bm.faces)

# front/neck trim: round the neck opening, then extrude ONE rolled band straight from the cut edge of the garment.
# Because the band grows out of the existing boundary there is no separate strip to line up, so no gaps or torn flaps.
def vopen_c(c):
    return c.y < -0.01 and abs(c.x) < 0.012 + 0.038 * max(0.0, min(1.0, (c.z - 0.90) / 0.485))


NECK_C = Vector((0, -0.028, 0))
bmesh.ops.delete(bm, geom=[f for f in bm.faces if f.calc_center_median().z > 1.30 and
                           ((f.calc_center_median().x / 0.056) ** 2 + ((f.calc_center_median().y - NECK_C.y) / 0.054) ** 2) < 1.0],
                 context='FACES')                                  # clean elliptical neck hole (the circle the user asked for)
bmesh.ops.delete(bm, geom=[v for v in bm.verts if not v.link_faces], context='VERTS')
bm.edges.ensure_lookup_table()
def on_trim(m):
    if m.z > 1.30:
        return True
    return m.y < -0.01 and m.z > 0.955 and abs(abs(m.x) - (0.012 + 0.038 * max(0.0, min(1.0, (m.z - 0.90) / 0.485)))) < 0.012      # the V edge only, never the hem seam


trim = [e for e in bm.edges if e.is_boundary and on_trim((e.verts[0].co + e.verts[1].co) / 2) and abs((e.verts[0].co.x + e.verts[1].co.x) / 2) < 0.2]
# smooth the cut edge itself (it follows a jagged planar cut): Laplacian along the boundary chain, kept on the garment surface
chain_v = {v for e in trim for v in e.verts}
for _ in range(10):
    tgt = {}
    for v in chain_v:
        nb = [e.other_vert(v) for e in v.link_edges if e.is_boundary and e.other_vert(v) in chain_v]
        if len(nb) == 2:
            tgt[v] = (nb[0].co + nb[1].co) / 2
    for v, pt in tgt.items():
        v.co = v.co.lerp(pt, 0.5)
        loc, nor, idx, dist = bvh_body.find_nearest(v.co)
        v.co = loc + nor * 0.0265
ext = bmesh.ops.extrude_edge_only(bm, edges=trim)
new_v = [g for g in ext['geom'] if isinstance(g, bmesh.types.BMVert)]
old_v = {v for e in trim for v in e.verts}
for v in new_v:
    # direction away from the garment interior, along the surface
    fc = Vector()
    n = 0
    for e in v.link_edges:
        for f in e.link_faces:
            fc += f.calc_center_median()
            n += 1
    out = Vector((0, 0, 0))
    if n:
        fc /= n
        out = (v.co - fc)
        out.z *= 0.6
    if out.length > 1e-6:
        v.co += out.normalized() * 0.008
    loc, nor, idx, dist = bvh_body.find_nearest(v.co)
    v.co = loc + nor * 0.0345                                       # rests on the body, raised like a rolled edge
for f in [g for g in ext['geom'] if isinstance(g, bmesh.types.BMFace)]:
    f.material_index = 1
    f.smooth = False
band_v = set(new_v)
for _ in range(14):                                                   # relax the rolled edge into a smooth round line
    nbr = {}
    for v in band_v:
        nb = [e.other_vert(v) for e in v.link_edges if e.other_vert(v) in band_v]
        if nb:
            nbr[v] = sum((q.co for q in nb), Vector()) / len(nb)
    for v, pcen in nbr.items():
        v.co = v.co.lerp(pcen, 0.5)
        loc, nor, idx, dist = bvh_body.find_nearest(v.co)
        if (v.co - loc).dot(nor) < 0.030:
            v.co = loc + nor * 0.030
bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
bm.to_mesh(me)
bm.free()

# ---------------------------------------------------------------- folds: elbows, knees, trouser hems
def fold_zone(obj, centre, radius, axis, freq, amp, ridge_dir=None, hem_flare=0.0):
    me = obj.data
    bm = bmesh.new()
    bm.from_mesh(me)
    zone = [f for f in bm.faces if (f.calc_center_median() - centre).length < radius]
    edges = list({e for f in zone for e in f.edges})
    bmesh.ops.subdivide_edges(bm, edges=edges, cuts=1, use_grid_fill=True)
    bm.normal_update()
    for v in bm.verts:
        dv = v.co - centre
        d = dv.length
        if d >= radius:
            continue
        fall = (1 - d / radius) ** 0.8
        along = dv.dot(axis)
        v.co += v.normal * amp * fall * math.sin(along * freq)
    for f in bm.faces:
        f.smooth = False
    bm.to_mesh(me)
    bm.free()


for s in (1, -1):
    ax = (J_wr[s] - J_el[s]).normalized()
    fold_zone(card, J_el[s] + Vector((0, 0, 0)), 0.075, ax, 120, 0.0035)           # sleeve creases at the elbow
trou = bpy.data.objects['Rose_Trousers']
for s in (1, -1):
    fold_zone(trou, Vector((0.158 * s, -0.02, 0.45)), 0.09, Vector((0, 0, 1)), 95, 0.0040)   # knee folds
    fold_zone(trou, Vector((0.215 * s, 0.0, 0.13)), 0.07, Vector((0, 0, 1)), 140, 0.0030)    # fabric stacking at the ankle
# trouser cuff: flares around the ankle so it sits outside the shoe instead of cutting through it
me = trou.data
for v in me.vertices:
    if v.co.z < 0.13:
        cx = 0.19 if v.co.x > 0 else -0.19
        d = Vector((v.co.x - cx, v.co.y + 0.02, 0))
        if d.length > 1e-6:
            k = 0.014 * (1 - max(0.0, (v.co.z - 0.075)) / 0.055)
            v.co += d.normalized() * k

# ---------------------------------------------------------------- buttons on the left front panel
dg = bpy.context.evaluated_depsgraph_get()
scene = bpy.context.scene
bb = bmesh.new()
for z in (0.94, 1.02, 1.10, 1.18):
    zt = max(0, min(1, (z - 0.90) / 0.485))
    x = 0.012 + 0.038 * zt + 0.024
    hit = scene.ray_cast(dg, Vector((x, -0.6, z)), Vector((0, 1, 0)))
    if not hit[0] or hit[4].name != 'Rose_Cardigan':
        continue
    loc, nor = hit[1], hit[2].normalized()
    r = bmesh.ops.create_cone(bb, cap_ends=True, segments=8, radius1=0.0075, radius2=0.0068, depth=0.0045)
    z_ax = nor
    x_ax = Vector((0, 0, 1)).cross(z_ax).normalized()
    y_ax = z_ax.cross(x_ax)
    M = Matrix(((x_ax.x, y_ax.x, z_ax.x), (x_ax.y, y_ax.y, z_ax.y), (x_ax.z, y_ax.z, z_ax.z))).to_4x4()
    for v in r['verts']:
        v.co = M @ v.co + loc + nor * 0.002
for f in bb.faces:
    f.smooth = False
mb = bpy.data.meshes.new('Rose_Buttons')
bb.to_mesh(mb)
bb.free()
ob = bpy.data.objects.new('Rose_Buttons', mb)
bpy.context.collection.objects.link(ob)
mb.materials.append(ivory)
print('polish done')

# ---------------------------------------------------------------- shoes: a proper low-poly shoe (lofted sections) with a sole
old = bpy.data.objects.get('Rose_Shoes')
if old:
    bpy.data.objects.remove(old)
brown = bpy.data.materials['Shoes_Brown']
sole_m = mat('Shoes_Sole', (0.07, 0.045, 0.035, 1), 0.7)
# (y, half-width, top height): heel -> ankle -> instep -> ball -> toe. Sized from the foot with ~5 mm of clearance.
PROFILE = [(0.036, 0.028, 0.062), (0.024, 0.034, 0.082), (0.000, 0.038, 0.092), (-0.040, 0.040, 0.096),
           (-0.080, 0.045, 0.096), (-0.120, 0.052, 0.066), (-0.160, 0.050, 0.047), (-0.195, 0.040, 0.036), (-0.220, 0.020, 0.026)]
NR = 14                                                          # points per section ring
bm = bmesh.new()
rings_all = {}
for side in (1, -1):
    cx = 0.190 * side
    rings = []
    for y, hw, top in PROFILE:
        ring = []
        for k in range(NR):
            a_ = 2 * math.pi * k / NR
            c_, s_ = math.cos(a_), math.sin(a_)
            ex = math.copysign(abs(c_) ** 0.55, c_)                 # squarer than an ellipse: a shoe, not a sausage
            ez = math.copysign(abs(s_) ** 0.45, s_)
            x = cx + hw * ex
            z = top * 0.5 + top * 0.5 * ez
            if ez < -0.5:
                x = cx + (x - cx) * 1.05                               # sole sticks out a little
            if ez < -0.7:
                z = 0.0                                                 # flat sole
            ring.append(bm.verts.new((x, y, z - 0.003)))        # a hair below the floor so the foot never shows under the sole
        rings.append(ring)
    for i in range(len(rings) - 1):
        for k in range(NR):
            k2 = (k + 1) % NR
            f = bm.faces.new((rings[i][k], rings[i][k2], rings[i + 1][k2], rings[i + 1][k]))
            ez = math.sin(2 * math.pi * (k + 0.5) / NR)
            f.material_index = 1 if ez < -0.55 else 0
            f.smooth = False
    for end, idx in ((rings[0], 0), (rings[-1], -1)):               # close heel and toe
        c = Vector((sum(v.co.x for v in end) / NR, sum(v.co.y for v in end) / NR, sum(v.co.z for v in end) / NR))
        cv = bm.verts.new(c + Vector((0, 0.004 if idx == 0 else -0.006, 0)))
        for k in range(NR):
            try:
                f = bm.faces.new((end[k], end[(k + 1) % NR], cv) if idx == 0 else (end[(k + 1) % NR], end[k], cv))
            except ValueError:
                continue
            f.material_index = 0
            f.smooth = False
bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
me = bpy.data.meshes.new('Rose_Shoes')
bm.to_mesh(me)
bm.free()
shoes = bpy.data.objects.new('Rose_Shoes', me)
bpy.context.collection.objects.link(shoes)
me.materials.append(brown)
me.materials.append(sole_m)
print('shoes built')
