"""Tercera pasada de pesos: las piernas de pantalones/trajes seguian al MUSLO (no a pantorrilla ni pie).

Medido en Unity: Grd_Suit, Gar_Pants, Cou_Pants... con cientos de vertices ligados a thigh_l/thigh_r a mas de 0.55 m del hueso.
Con la animacion real, el bajo del pantalon no acompanaba a la rodilla y se separaba de la bota / dejaba ver la piel.
legs_from_body(): para los vertices de la prenda por debajo de la cadera (z < pelvis - 0.22 m) copia los pesos del vertice mas cercano del cuerpo (*_Low),
luego suaviza un par de iteraciones para que la transicion con el torso sea gradual.
Uso: exec(open(r"D:/TheLivingCanvas/Tools/npc_pipeline/fix_weights3.py").read()); run_all()
"""
import bpy
import bmesh

exec(open(r"D:/TheLivingCanvas/Tools/npc_pipeline/fix_weights2.py", encoding='utf-8').read())  # smooth_weights, PREFIXES
TARGET = ('_Pants', '_Suit')
SKIP = ('Cur_Suit',)   # falda: no se parte por pierna


def legs_from_skeleton(ob, arm, drop=0.22, soft=0.03):
    """Pantalon/traje por debajo de la cadera: pesos segun la cercania a los segmentos de hueso de la pierna (thigh/calf/foot/ball).
    El cuerpo (*_Low) tiene las piernas recortadas bajo la ropa, asi que no sirve de referencia ahi."""
    import math
    mwa = arm.matrix_world
    pelvis_z = (mwa @ arm.data.bones['pelvis'].head_local).z
    leg = {}
    for side in ('l', 'r'):
        for part in ('thigh', 'calf', 'foot', 'ball'):
            b = arm.data.bones.get('%s_%s' % (part, side))
            if b:
                leg['%s_%s' % (part, side)] = (mwa @ b.head_local, mwa @ b.tail_local)
    mw = ob.matrix_world
    groups = {g.name: g for g in ob.vertex_groups}
    n = 0
    for v in ob.data.vertices:
        p = mw @ v.co
        if p.z > pelvis_z - drop:
            continue
        ds = {k: _sd(p, a, b) for k, (a, b) in leg.items()}
        dmin = min(ds.values())
        ws = {k: math.exp(-(d - dmin) / soft) for k, d in ds.items() if d - dmin < 0.08}
        s_ = sum(ws.values())
        for g in list(v.groups):
            ob.vertex_groups[g.group].remove([v.index])
        for k, val in ws.items():
            if k not in groups:
                groups[k] = ob.vertex_groups.new(name=k)
            groups[k].add([v.index], val / s_, 'REPLACE')
        n += 1
    deform = {b.name for b in arm.data.bones if b.use_deform}
    smooth_weights(ob, deform, iters=2, factor=0.5)
    return n


def _sd(p, a, b):
    ab = b - a
    t = max(0.0, min(1.0, (p - a).dot(ab) / max(ab.length_squared, 1e-12)))
    return (p - (a + ab * t)).length


def run_all3():
    O = bpy.data.objects
    res = {}
    for pre in PREFIXES:
        arm = O[pre + '_Rig']
        low = O[pre + '_Low']
        for ob in arm.children:
            if ob.type == 'MESH' and ob.name.endswith(TARGET) and ob.name not in SKIP:
                res[ob.name] = legs_from_skeleton(ob, arm)
    print('W3', res)
    return res
