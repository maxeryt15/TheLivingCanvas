"""Bateria de poses de prueba para los NPCs (rig de 53 huesos, nombres tipo Unreal). No toca el armature ni las acciones.
Cada pose es una lista de pasos (hueso, angulo, funcion de puntuacion). El eje local y el signo de cada rotacion se CALIBRAN solos:
se prueban los 6 (eje, signo) y se elige el que maximiza la puntuacion (p. ej. 'la mano sube'). Asi no se adivinan ejes del rig.
Uso: import pose_lib as PL; cal = PL.calibrate(arm); PL.apply(arm, cal['ElbowBend_L'])
"""
import bpy, math
from mathutils import Quaternion, Vector


def reset(arm):
    if arm.animation_data:
        arm.animation_data.action = None
    for pb in arm.pose.bones:
        pb.rotation_mode = 'QUATERNION'
        pb.rotation_quaternion = Quaternion((1, 0, 0, 0))
        pb.location = (0, 0, 0)
        pb.scale = (1, 1, 1)
    bpy.context.view_layer.update()


def _p(arm, name, tail=False):
    pb = arm.pose.bones[name]
    return (pb.tail if tail else pb.head).copy()


def forward(arm):
    d = _p(arm, 'ball_l') - _p(arm, 'foot_l')
    d.z = 0
    return d.normalized()


def _yaw(arm):
    v = _p(arm, 'clavicle_r') - _p(arm, 'clavicle_l')
    return math.atan2(v.y, v.x)


# (hueso, grados, funcion(arm, F) -> puntuacion a maximizar)
def _poses():
    S = lambda s: (lambda a, F: s(a, F))
    P = {}
    for side in ('l', 'r'):
        S_ = side.upper()
        hand, upper, lower = f'hand_{side}', f'upperarm_{side}', f'lowerarm_{side}'
        other = 'r' if side == 'l' else 'l'
        thigh, calf, foot = f'thigh_{side}', f'calf_{side}', f'foot_{side}'
        P[f'ArmsUp_{S_}'] = [(upper, 150, lambda a, F, h=hand: _p(a, h).z)]
        P[f'ArmsForward_{S_}'] = [(upper, 90, lambda a, F, h=hand: _p(a, h).dot(F))]
        P[f'ArmsBack_{S_}'] = [(upper, 60, lambda a, F, h=hand: -_p(a, h).dot(F))]
        P[f'ElbowBend_{S_}'] = [(lower, 135, lambda a, F, h=hand, u=upper: -(_p(a, h) - _p(a, u)).length)]
        P[f'ShoulderCross_{S_}'] = [(upper, 100, lambda a, F, h=hand, o=f'upperarm_{other}': -(_p(a, h) - _p(a, o)).length)]
        P[f'ShoulderUpElbow_{S_}'] = [(upper, 150, lambda a, F, h=hand: _p(a, h).z), (lower, 100, lambda a, F, h=hand, u=upper: -(_p(a, h) - _p(a, u)).length)]
        P[f'LegKick_{S_}'] = [(thigh, 80, lambda a, F, f=foot: _p(a, f).dot(F))]
        P[f'LegAbduct_{S_}'] = [(thigh, 40, lambda a, F, f=foot: abs(_p(a, f).x - _p(a, 'pelvis').x))]
        P[f'KneeBend_{S_}'] = [(thigh, 60, lambda a, F, f=foot: _p(a, f).dot(F)), (calf, 120, lambda a, F, f=foot, p=thigh: -(_p(a, f) - _p(a, p)).length)]
    P['Crouch'] = [(f'thigh_{s}', 110, lambda a, F, s=s: _p(a, f'calf_{s}').dot(F)) for s in 'lr'] + \
                  [(f'calf_{s}', 130, lambda a, F, s=s: -(_p(a, f'foot_{s}') - _p(a, f'thigh_{s}')).length) for s in 'lr'] + \
                  [('spine_01', 25, lambda a, F: _p(a, 'head').dot(F))]
    P['Sit'] = [(f'thigh_{s}', 90, lambda a, F, s=s: _p(a, f'calf_{s}').dot(F)) for s in 'lr'] + \
               [(f'calf_{s}', 90, lambda a, F, s=s: -_p(a, f'foot_{s}').z) for s in 'lr']
    P['BendForward'] = [('spine_01', 35, lambda a, F: _p(a, 'head').dot(F)), ('spine_02', 35, lambda a, F: _p(a, 'head').dot(F)),
                        ('spine_03', 25, lambda a, F: _p(a, 'head').dot(F))]
    P['Twist_A'] = [('spine_02', 45, lambda a, F: _yaw(a)), ('spine_03', 30, lambda a, F: _yaw(a))]
    P['Twist_B'] = [('spine_02', 45, lambda a, F: -_yaw(a)), ('spine_03', 30, lambda a, F: -_yaw(a))]
    P['HeadDown'] = [('neck_01', 35, lambda a, F: -_p(a, 'head', True).z)]
    return P


POSES = _poses()


def calibrate(arm):
    """Devuelve {pose: [(hueso, eje 0-2, signo, grados), ...]} con la pose ya resuelta para este rig."""
    F = forward(arm)
    out = {}
    for name, steps in POSES.items():
        reset(arm)
        cal = []
        for bone, deg, fn in steps:
            pb = arm.pose.bones[bone]
            best = None
            for ax in range(3):
                for sg in (1, -1):
                    axis = Vector([1.0 if i == ax else 0.0 for i in range(3)])
                    pb.rotation_quaternion = Quaternion(axis, sg * math.radians(deg))
                    bpy.context.view_layer.update()
                    sc = fn(arm, F)
                    if best is None or sc > best[0] + 1e-6:
                        best = (sc, ax, sg)
            _, ax, sg = best
            axis = Vector([1.0 if i == ax else 0.0 for i in range(3)])
            pb.rotation_quaternion = Quaternion(axis, sg * math.radians(deg))
            bpy.context.view_layer.update()
            cal.append((bone, ax, sg, deg))
        out[name] = cal
    reset(arm)
    return out


def apply(arm, cal, fraction=1.0):
    reset(arm)
    for bone, ax, sg, deg in cal:
        axis = Vector([1.0 if i == ax else 0.0 for i in range(3)])
        arm.pose.bones[bone].rotation_quaternion = Quaternion(axis, sg * math.radians(deg) * fraction)
    bpy.context.view_layer.update()
