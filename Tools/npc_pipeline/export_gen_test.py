"""Export de PRUEBA de Gen (solo) a ArtSource/_Exports/GenHemTest (no toca Assets/) y comparacion con el .blend: huesos, grupos, shape keys, pesos y deformacion.
Uso: blender -b <copia_de_prueba>.blend --python export_gen_test.py"""
import bpy, os, sys, json
from mathutils import Vector, Quaternion
sys.path.insert(0, r'D:\TheLivingCanvas\Tools\npc_pipeline')
import pose_lib as PL
_D = sys.argv[sys.argv.index('--') + 1] if '--' in sys.argv else r'D:\TheLivingCanvas\ArtSource\_Exports\GenHemTest'
OUT = _D; os.makedirs(OUT, exist_ok=True)
O = bpy.data.objects
arm = O['Gen_Rig']; mesh = O['Gen_Mesh']
cal = PL.calibrate(arm); PL.reset(arm)
loc = arm.location.copy(); arm.location = (0, 0, 0); bpy.context.view_layer.update()
game = [o for o in arm.children if o.type == 'MESH' and o.visible_get() and not o.name.endswith('_Base')]
for o in bpy.context.view_layer.objects: o.select_set(False)
arm.select_set(True)
for o in game: o.select_set(True)
bpy.context.view_layer.objects.active = arm
fbx = os.path.join(OUT, 'Gentleman.fbx')
bpy.ops.export_scene.fbx(filepath=fbx, use_selection=True, object_types={'ARMATURE', 'MESH'}, use_mesh_modifiers=True,
    mesh_smooth_type='FACE', add_leaf_bones=False, bake_anim=False, axis_forward='-Z', axis_up='Y', apply_unit_scale=True,
    apply_scale_options='FBX_SCALE_UNITS', use_armature_deform_only=True, primary_bone_axis='Y', secondary_bone_axis='X',
    path_mode='COPY', embed_textures=False, colors_type='LINEAR')
print('EXPORTED', [o.name for o in game])
before = set(O.keys())
bpy.ops.import_scene.fbx(filepath=fbx, axis_forward='-Z', axis_up='Y', automatic_bone_orientation=False, primary_bone_axis='Y', secondary_bone_axis='X')
new = [O[k] for k in O.keys() if k not in before]
iarm = next(o for o in new if o.type == 'ARMATURE'); imesh = [o for o in new if o.type == 'MESH']
im = next(o for o in imesh if len(o.data.vertices) >= 5000) if imesh else None
print('IMPORTED', [(o.name, o.type, len(o.data.vertices) if o.type == 'MESH' else '') for o in new])
# huesos / grupos / keys
ob = set(b.name for b in arm.data.bones if b.use_deform); ib = set(b.name for b in iarm.data.bones)
print('BONES orig deform', len(ob), 'fbx', len(ib), 'diff', sorted(ob ^ ib)[:10])
og = set(g.name for g in mesh.vertex_groups); ig = set(g.name for g in im.vertex_groups)
print('GROUPS only_orig', sorted(og - ig)[:10], 'only_fbx', sorted(ig - og)[:10])
ok = [k.name for k in mesh.data.shape_keys.key_blocks]; ik = [k.name for k in im.data.shape_keys.key_blocks] if im.data.shape_keys else []
print('KEYS orig', len(ok), 'fbx', len(ik), 'same', ok == ik)
# pesos por vertice (emparejando por posicion). Tras FBX el mesh importado esta en espacio Blender igual (ejes inversos).
from mathutils.kdtree import KDTree
ev = mesh.evaluated_get(bpy.context.evaluated_depsgraph_get()).to_mesh()
PL.reset(arm)
kd = KDTree(len(im.data.vertices))
for v in im.data.vertices: kd.insert(im.matrix_world @ v.co, v.index)
kd.balance()
maxd = 0; maxw = 0; bad = 0; hem = 0
def w(ob_, v): return {ob_.vertex_groups[g.group].name: g.weight for g in v.groups}
for v in mesh.data.vertices:
    p = mesh.matrix_world @ v.co
    # para la comparacion usamos la posicion de reposo; el mesh original esta en arm.location (0)
    co, idx, d = kd.find(p)
    maxd = max(maxd, d)
    a = w(mesh, v); b = w(im, im.data.vertices[idx])
    dw = max([abs(a.get(k, 0) - b.get(k, 0)) for k in set(a) | set(b)] + [0])
    if dw > 0.02: bad += 1
    maxw = max(maxw, dw)
print('MATCH max pos dist (m)', round(maxd, 5), 'max weight diff', round(maxw, 4), 'verts weight diff>0.02', bad, 'of', len(mesh.data.vertices))
# deformacion: huesos con mismo reposo?
dh = max((arm.data.bones[n].head_local - iarm.data.bones[n].head_local).length for n in ob & ib)
print('REST bone head max diff', round(dh, 5))
arm.location = loc
