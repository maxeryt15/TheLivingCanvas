"""Tourist: piel de la cadera que asoma sobre el short al caminar en Unity (los correctivos con driver, p. ej. Corrective_*_Hip_Flex_*, no exportan y valen 0 alli).
Metodo: con los correctivos silenciados se trazan rayos en frontal/3-4 sobre frames de Walk; los vertices de PIEL de la zona de la cintura/cadera cuyas caras se ven (y que en reposo estan
cubiertos por la ropa) se hunden INSET m a lo largo de -normal (los vecinos a la mitad). El mismo desplazamiento se suma a TODAS las shape keys para no cambiar los correctivos.
Uso: blender -b WORK.blend --python fix_tou_hip.py -- [--inset 0.010 --save]   (sin --save solo modifica en memoria; sirve como FIX_SCRIPT de render_views)"""
import bpy, bmesh, sys, math, collections
sys.path.insert(0, r'D:\TheLivingCanvas\Tools\npc_pipeline')
import pose_lib as PL
from mathutils import Vector
from mathutils.bvhtree import BVHTree
a = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else []
def opt(k, d): return float(a[a.index(k) + 1]) if k in a else d
INSET = opt('--inset', 0.010)
O = bpy.data.objects; ob = O['Tou_Mesh']; arm = O['Tou_Rig']; S = bpy.context.scene; me = ob.data
assert not ob.get('tlc_hip_fix'), 'ya aplicado'
sk = me.shape_keys
muted = []
for k in sk.key_blocks:
    if k.name.startswith('Corrective_'): muted.append((k, k.mute)); k.mute = True
PL.calibrate(arm)
walk = next(x for x in bpy.data.actions if x.name.startswith('U_') and '_Tourist_Walk' in x.name)
mats = [m.name for m in me.materials]; CL = mats.index('Tou_clothes_Paint'); SKI = mats.index('Tou_skin_Paint')
rest = [v.co.copy() for v in me.vertices]; rnor = [v.normal.copy() for v in me.vertices]
exposed = set()
def visible_skin_faces():
    ev = ob.evaluated_get(bpy.context.evaluated_depsgraph_get()); m = ev.to_mesh(); polys = [tuple(p.vertices) for p in m.polygons]
    bvh = BVHTree.FromPolygons([v.co.copy() for v in m.vertices], polys); out = set()
    for az in (-35, 0, 35):
        t = math.radians(az); d = Vector((math.sin(t), -math.cos(t), 0)); right = Vector((math.cos(t), math.sin(t), 0))
        for iu in range(-22, 23):
            for iz in range(0, 36):
                o = right * (iu * 0.01) + Vector((0, 0, 0.82 + iz * 0.01)) + d * 3
                loc, nor, idx, dist = bvh.ray_cast(o, -d)
                if idx is not None and m.polygons[idx].material_index == SKI: out.add(idx)
    ev.to_mesh_clear(); return out
base_polys = [tuple(p.vertices) for p in me.polygons]
for fr in range(1, 41, 3):
    PL.reset(arm); ad = arm.animation_data or arm.animation_data_create(); ad.action = walk; ad.action_slot = walk.slots[0]; S.frame_set(fr); bpy.context.view_layer.update()
    for pi in visible_skin_faces(): exposed.update(base_polys[pi])
PL.reset(arm)
# solo vertices que en reposo estan cubiertos por ropa (excluye manos, brazos, piernas desnudas)
cl_polys = [tuple(p.vertices) for p in me.polygons if p.material_index == CL]
bvh_r = BVHTree.FromPolygons(rest, cl_polys)
sel = set()
for v in exposed:
    c = rest[v]
    if not (0.80 < c.z < 1.12 and abs(c.x) < 0.20): continue
    loc, nor, idx, d = bvh_r.find_nearest(c)
    if loc is not None and d < 0.05 and (c - loc).dot(nor) < 0.01: sel.add(v)
bm = bmesh.new(); bm.from_mesh(me); bm.verts.ensure_lookup_table()
ring = set()
for v in sel:
    for e in bm.verts[v].link_edges:
        o = e.other_vert(bm.verts[v]).index
        if o not in sel and me.vertices[o].groups is not None: ring.add(o)
bm.free()
delta = {}
for v in sel: delta[v] = -rnor[v].normalized() * INSET
for v in ring:
    c = rest[v]
    if 0.78 < c.z < 1.14 and abs(c.x) < 0.22: delta[v] = -rnor[v].normalized() * INSET * 0.5
print('HIPFIX exposed', len(exposed), 'sel', len(sel), 'ring', len(ring), 'moved', len(delta), 'zrange', (min(rest[v].z for v in sel), max(rest[v].z for v in sel)) if sel else None)
for k in sk.key_blocks:
    for v, dv in delta.items(): k.data[v].co += dv
for v, dv in delta.items(): me.vertices[v].co += dv
me.update(); bpy.context.view_layer.update()
rest2 = [v.co.copy() for v in me.vertices]; ex2 = set()
for fr in range(1, 41, 3):
    PL.reset(arm); ad = arm.animation_data or arm.animation_data_create(); ad.action = walk; ad.action_slot = walk.slots[0]; S.frame_set(fr); bpy.context.view_layer.update()
    for pi in visible_skin_faces(): ex2.update(base_polys[pi])
PL.reset(arm)
left = [v for v in ex2 if 0.80 < rest2[v].z < 1.12 and abs(rest2[v].x) < 0.20 and (lambda r: r[0] is not None and r[3] < 0.03 and (rest2[v] - r[0]).dot(r[1]) < 0)(BVHTree.FromPolygons(rest2, cl_polys).find_nearest(rest2[v]))]
print('HIPFIX after: still visible covered-skin verts', len(left), sorted(left)[:20])
# segunda pasada: los que siguen asomando se hunden un poco mas
n2 = {v: me.vertices[v].normal.copy() for v in left}
for k in sk.key_blocks:
    for v in left: k.data[v].co += -n2[v].normalized() * 0.02
for v in left: me.vertices[v].co += -n2[v].normalized() * 0.02
me.update()
for k, mu in muted: k.mute = mu
ob['tlc_hip_fix'] = INSET
if '--save' in a:
    bpy.ops.wm.save_mainfile(); print('HIPFIX saved')
