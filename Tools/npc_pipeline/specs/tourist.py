"""Tourist: woman in her 30s. White-and-coral top, denim shorts, sneakers-style shoes, long hair, camera on a strap, sunglasses on head, crossbody bag, bracelet."""
import sys
sys.path.insert(0, r'D:\TheLivingCanvas\Tools\npc_pipeline')
import npc_props as P


def accessories(ctx, D):
    p, Z = ctx['prefix'], ctx['Z']
    top, shorts = p + '_Top', p + '_Shorts'
    import npc_props3 as P3
    out = []
    out.append((P3.travel_camera(p, [top, ctx['low']], Z(0.855), Z(0.70), strap_col=(0.72, 0.12, 0.12)).name, 'skin'))
    out.append((P.sunglasses_on_head(p, p + '_Hair').name, 'head'))
    out.append((P.satchel(p, [top, shorts, ctx['low']], 0.115, Z(0.50), Z(0.82), bag_w=0.24, bag_h=0.20, bag_d=0.07, side=1, hip_x=0.15, canvas=(0.10, 0.22, 0.42), flap=(0.85, 0.62, 0.15),
                         strap_col=(0.85, 0.30, 0.22), leather=(0.45, 0.22, 0.10),
                         stars=dict(count=22, colors=[(0.95, 0.78, 0.15), (0.90, 0.25, 0.25), (0.20, 0.75, 0.55), (0.95, 0.55, 0.15), (0.85, 0.85, 0.90)])).name, 'skin'))
    out.append((P.bracelet(p, ctx['low'], ctx['joints'], side=1, color=(0.95, 0.80, 0.20), back=0.03, second=((0.90, 0.30, 0.20), 0.055)).name, 'lowerarm_l'))
    out.append((P3.sandals(p, ctx['low']).name, 'skin'))
    return out


SPEC = dict(
    lipstick=(0.66, 0.13, 0.2),
    prefix='Tou', folder='Tourist', target_height=1.66,
    eye_look=(-14.0, 0.0),
    macros=dict(gender=0.0, age=0.30, muscle=0.35, weight=0.42, proportions=0.5, height=0.5, cupsize=0.5, firmness=0.55,
                race=dict(asian=0.6, caucasian=0.2, african=0.2)),
    targets={'head-oval': 0.45, 'l-cheek-volume-incr': 0.35, 'r-cheek-volume-incr': 0.35, 'l-cheek-bones-incr': 0.2, 'r-cheek-bones-incr': 0.2,
             'mouth-angles-up': 1.0, 'mouth-scale-horiz-incr': 0.4, 'mouth-upperlip-volume-incr': 0.25, 'mouth-lowerlip-volume-incr': 0.2,
             'l-eye-scale-incr': 0.4, 'r-eye-scale-incr': 0.4, 'l-eye-height1-incr': 0.2, 'r-eye-height1-incr': 0.2, 'l-eye-eyefold-angle-up': 0.45, 'r-eye-eyefold-angle-up': 0.45,
             'eyebrows-trans-up': 0.25, 'eyebrows-angle-up': 0.3, 'nose-scale-horiz-decr': 0.2, 'nose-scale-vert-decr': 0.1, 'chin-prominent-incr': 0.3, 'chin-width-decr': 0.2,
             'forehead-scale-vert-incr': 0.2},
    brows='eyebrow003', brow_color=(0.05, 0.03, 0.03), eyes=(0.04, 0.24, 0.62),
    skin=dict(base=(0.46, 0.30, 0.21), lips=(0.38, 0.22, 0.20), blush=(0.62, 0.27, 0.22), shadow=(0.38, 0.23, 0.20)),
    hair=dict(asset='braid01', tris=1100, cut_z=0.705, tones=[(0.015, 0.012, 0.012), (0.04, 0.03, 0.03), (0.09, 0.07, 0.06)], scale=dict(x=1.0, y=1.0, zu=1.0, zd=1.0)),
    clothes=[
        dict(key='Shorts', asset='cortu_jeans_shorts', tris=900, split_z=lambda ctx: [ctx['Z'](0.40) + 0.035, ctx['Z'](0.50) - 0.03], default=('Denim', (0.07, 0.15, 0.30)),
             stains=lambda ctx: [dict(zmin=ctx['Z'](0.40), zmax=ctx['Z'](0.50), count=16, r=(0.02, 0.05), color=(0.18, 0.30, 0.50), alpha=0.35),
                                 dict(zmin=ctx['Z'](0.42), zmax=ctx['Z'](0.50), count=7, r=(0.015, 0.03), color=(0.03, 0.08, 0.20), alpha=0.35)],
             rules=lambda ctx: [('Cuff', (0.20, 0.31, 0.50), lambda c, n: c.z < ctx['Z'](0.40) + 0.034 and abs(c.x) > 0.04),
                                ('Waist', (0.03, 0.08, 0.20), lambda c, n: c.z > ctx['Z'](0.50) - 0.029)]),
        dict(key='Top', asset='toigo_camisole_top', tris=900, default=('Cloth', (0.88, 0.85, 0.76)),
             motifs=lambda ctx: [dict(zmin=ctx['Z'](0.56), zmax=ctx['Z'](0.80), count=34, size=0.050, trunk=(0.30, 0.15, 0.07), leaf=(0.10, 0.52, 0.22), nut=(0.30, 0.15, 0.07))],
             rules=lambda ctx: [('Hem', (0.82, 0.30, 0.24), lambda c, n: c.z < ctx['Z'](0.56) + 0.012)]),
    ],
    accessories=accessories,
)
