"""Aplica a un armature del .blend las animaciones de Unity volcadas por NpcAnimExport (ArtSource/NPC/Anims/<Npc>.json).
Crea una accion por clip ('U_<clip>', con fake user). Mapeo Blender->Unity verificado por minimos cuadrados: (x, y, z) -> (-x, z, -y).
Uso: exec(open(r"D:/TheLivingCanvas/Tools/npc_pipeline/apply_unity_anims.py").read()); apply_npc('Caf', 'Cafe')"""
import bpy, json
from mathutils import Matrix, Quaternion, Vector

MU = Matrix(((-1, 0, 0), (0, 0, 1), (0, -1, 0)))   # Blender -> Unity
MUT = MU.transposed()
ANIMS = r"D:/TheLivingCanvas/ArtSource/NPC/Anims/%s.json"


def _uq(a):
    return Quaternion((a[6], a[3], a[4], a[5]))   # Unity (x,y,z,w) -> mathutils (w,x,y,z)


def apply_npc(prefix, npc, only=None):
    d = json.load(open(ANIMS % npc))
    arm = bpy.data.objects[prefix + '_Rig']
    names = d['bones']
    rest = d['rest']
    pbs = {n: arm.pose.bones.get(n) for n in names}
    idx = [i for i, n in enumerate(names) if pbs[n] is not None]
    rest_p = {i: Vector(rest[i][:3]) for i in idx}
    rest_q = {i: _uq(rest[i]) for i in idx}
    if arm.animation_data is None:
        arm.animation_data_create()
    for pb in arm.pose.bones:
        pb.rotation_mode = 'QUATERNION'
    out = []
    for cname, clip in d['clips'].items():
        if only and cname not in only:
            continue
        aname = 'U_' + (cname if cname.startswith('Pose_') else npc + '_' + cname)   # una accion por NPC (Blender 5: la ranura de la accion va ligada al objeto)
        act = bpy.data.actions.get(aname)
        if act:
            bpy.data.actions.remove(act)
        act = bpy.data.actions.new(aname)
        act.use_fake_user = True
        arm.animation_data.action = act
        step = 30.0 / clip['fps']
        for fi, fr in enumerate(clip['frames']):
            frame = 1 + fi * step
            target = {}
            for i in idx:
                n = names[i]; pb = pbs[n]
                rec = fr[i]
                dq = _uq(rec) @ rest_q[i].inverted()
                dp_u = Vector(rec[:3]) - rest_p[i]
                Rb = MUT @ dq.to_matrix() @ MU
                dp_b = MUT @ dp_u
                ml = pb.bone.matrix_local
                m3 = Rb @ ml.to_3x3()
                M = Matrix.Translation(ml.translation + dp_b) @ m3.to_4x4()
                target[n] = M
                par = pb.parent
                if par is None:
                    basis = ml.inverted() @ M
                else:
                    rel = par.bone.matrix_local.inverted() @ ml
                    basis = rel.inverted() @ target[par.name].inverted() @ M   # pose = parent_pose @ rel @ basis
                pb.location = basis.to_translation()
                pb.rotation_quaternion = basis.to_quaternion()
                pb.keyframe_insert('location', frame=frame)
                pb.keyframe_insert('rotation_quaternion', frame=frame)
        out.append((cname, len(clip['frames']), act.frame_range[:]))
    # vuelve al reposo para no dejar la pose de la ultima animacion
    for pb in arm.pose.bones:
        pb.location = (0, 0, 0); pb.rotation_quaternion = (1, 0, 0, 0)
    arm.animation_data.action = None
    return out
