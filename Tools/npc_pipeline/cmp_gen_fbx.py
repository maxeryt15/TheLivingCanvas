"""Compara la deformacion del FBX de prueba de Gen contra el .blend en varias poses (misma rotacion por hueso)."""
import bpy, sys
from mathutils import Matrix
sys.path.insert(0, r'D:\TheLivingCanvas\Tools\npc_pipeline')
import pose_lib as PL
from mathutils.kdtree import KDTree
_D = sys.argv[sys.argv.index('--') + 1] if '--' in sys.argv else r'D:\TheLivingCanvas\ArtSource\_Exports\GenHemTest'
O = bpy.data.objects
arm, mesh = O['Gen_Rig'], O['Gen_Mesh']
cal = PL.calibrate(arm); PL.reset(arm); arm.location = (0, 0, 0); bpy.context.view_layer.update()
before = set(O.keys())
bpy.ops.import_scene.fbx(filepath=_D + '/Gentleman.fbx', axis_forward='-Z', axis_up='Y', automatic_bone_orientation=False, primary_bone_axis='Y', secondary_bone_axis='X')
new = [O[k] for k in O.keys() if k not in before]
iarm = next(o for o in new if o.type == 'ARMATURE'); im = next(o for o in new if o.type == 'MESH')
# hueso: rotacion de las bases -> misma rotacion LOCAL; solo valido si los ejes locales coinciden
roll = max((arm.data.bones[b.name].matrix_local.to_3x3() - b.matrix_local.to_3x3()).median_absolute_deviation if False else sum(abs(x) for r in (arm.data.bones[b.name].matrix_local - b.matrix_local) for x in r) for b in iarm.data.bones if b.name in arm.data.bones)
print('BONE matrix_local max abs diff', round(roll, 5))
def verts(o):
    ev = o.evaluated_get(bpy.context.evaluated_depsgraph_get()); m = ev.to_mesh(); r = [o.matrix_world @ v.co for v in m.vertices]; ev.to_mesh_clear(); return r
base = verts(mesh); kd = KDTree(len(im.data.vertices))
for i, p in enumerate(verts(im)): kd.insert(p, i)
kd.balance(); idx = [kd.find(p)[1] for p in base]
for pose in ('Crouch', 'Sit', 'LegKick_L', 'LegKick_R', 'BendForward', 'Twist_A', 'Twist_B'):
    PL.apply(arm, cal[pose]); PL.apply(iarm, cal[pose])
    a = verts(mesh); b = verts(im)
    d = [(a[i] - b[idx[i]]).length for i in range(len(a))]
    mv = max((a[i] - base[i]).length for i in range(len(a))); mvi = max((b[idx[i]] - base[i]).length for i in range(len(a)))
    print('MOVED blend', round(mv * 1000), 'fbx', round(mvi * 1000), 'mm', [m.type for m in im.modifiers])
    print('POSE', pose, 'max mm', round(max(d) * 1000, 2), 'mean mm', round(sum(d) / len(d) * 1000, 3), 'n>5mm', sum(1 for x in d if x > 0.005))
