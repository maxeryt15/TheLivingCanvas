"""Blender (.blend abierto) vs FBX de staging: deformacion por pose (misma matrix_basis por hueso) y shape keys faciales. SOLO LECTURA (no guarda).
Uso: blender -b X.blend --python compare_fbx_poses.py -- Stu D:\ruta\Student.fbx [--ref D:\ruta\otro.fbx]"""
import bpy, sys
sys.path.insert(0, r'D:\TheLivingCanvas\Tools\npc_pipeline')
import pose_lib as PL
a = sys.argv[sys.argv.index('--') + 1:]; pref, fbx = a[0], a[1]
NAME = {'Stu': 'Student', 'Gen': 'Gentleman', 'Grd': 'Guard', 'Doc': 'Docent', 'Caf': 'Cafe', 'Cou': 'Courier', 'Cur': 'Curator', 'Pnt': 'Painter', 'Tou': 'Tourist', 'Gar': 'Gardener', 'Rose': 'Rose'}[pref]
O = bpy.data.objects; arm, mesh = O[pref + '_Rig'], O[pref + '_Mesh']; S = bpy.context.scene
cal = PL.calibrate(arm); PL.reset(arm); arm.location = (0, 0, 0); bpy.context.view_layer.update()
def imp(path):
    before = set(O.keys())
    bpy.ops.import_scene.fbx(filepath=path, axis_forward='-Z', axis_up='Y', automatic_bone_orientation=False, primary_bone_axis='Y', secondary_bone_axis='X')
    new = [O[k] for k in O.keys() if k not in before]
    return next(o for o in new if o.type == 'ARMATURE'), next(o for o in new if o.type == 'MESH')
iarm, im = imp(fbx)
bd = max(sum(abs(x) for r in (arm.data.bones[b.name].matrix_local - b.matrix_local) for x in r) for b in iarm.data.bones)
print('CMP bone matrix_local max abs diff', round(bd, 6))
def verts(o):
    ev = o.evaluated_get(bpy.context.evaluated_depsgraph_get()); m = ev.to_mesh(); r = [o.matrix_world @ v.co for v in m.vertices]; ev.to_mesh_clear(); return r
base = verts(mesh); assert len(base) == len(im.data.vertices)
walk = next(x for x in bpy.data.actions if x.name.startswith('U_') and f'_{NAME}_Walk' in x.name)
def sync():
    bpy.context.view_layer.update()
    for pb in iarm.pose.bones:
        if pb.name in arm.pose.bones: pb.rotation_mode = 'QUATERNION'; pb.matrix_basis = arm.pose.bones[pb.name].matrix_basis.copy()
    bpy.context.view_layer.update()
def cmp(tag):
    sync(); A = verts(mesh); B = verts(im)
    d = [(A[i] - B[i]).length for i in range(len(A))]; mv = max((A[i] - base[i]).length for i in range(len(A)))
    print('CMP %-16s moved %4.0fmm  max diff %.3f mm  mean %.4f mm  n>1mm %d' % (tag, mv * 1000, max(d) * 1000, sum(d) / len(d) * 1000, sum(1 for x in d if x > 0.001)))
cmp('Rest')
for p in ('ArmsUp_L', 'ArmsUp_R', 'ElbowBend_R', 'ShoulderCross_L', 'Crouch', 'Sit', 'KneeBend_L', 'LegKick_R', 'BendForward', 'Twist_A', 'Twist_B', 'HeadDown'):
    PL.reset(arm); PL.apply(arm, cal[p]); cmp(p)
PL.reset(arm); ad = arm.animation_data or arm.animation_data_create(); ad.action = walk; ad.action_slot = walk.slots[0]
for f in (1, 3, 15, 35, 40): S.frame_set(f); bpy.context.view_layer.update(); cmp('Walk@%d' % f)
ad.action = None; PL.reset(arm)
kb = mesh.data.shape_keys.key_blocks; ikb = im.data.shape_keys.key_blocks
for k in kb:
    if k.name == 'Basis': continue
    kb[k.name].value = 1.0; ikb[k.name].value = 1.0; bpy.context.view_layer.update(); cmp('key ' + k.name); kb[k.name].value = 0; ikb[k.name].value = 0
print('CMP_DONE')
