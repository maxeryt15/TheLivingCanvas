"""Cafe worker: woman in her 30s. Teal shift dress, cream apron with pocket, ballet flats, ponytail, name pin, watch."""
import sys
sys.path.insert(0, r'D:\TheLivingCanvas\Tools\npc_pipeline')
import npc_props as P
import npc_accessories as A


def accessories(ctx, D):
    p, Z = ctx['prefix'], ctx['Z']
    dress = p + '_Dress'
    import npc_props2 as P2
    import npc_props as P
    out = []
    out.append((P2.apron2(p, [dress, ctx['low']], Z(0.78), Z(0.37), Z(0.855)).name, 'skin'))
    out.append((P2.shoe_bows(p, p + '_Shoes').name, 'skin'))
    import npc_accessories as A
    out.append((A.wart(ctx['low'], p + '_Wart', p + '_Eyes').name, 'head'))
    out.append((P.bracelet(p, ctx['low'], ctx['joints'], side=-1, color=(0.85, 0.65, 0.22), back=0.03, width=0.016, thick=0.0035, name='BraceletR', second=((0.12, 0.45, 0.50), 0.06)).name, 'lowerarm_r'))
    out.append((A.lipstick(ctx['low'], p + '_Base', p + '_Lipstick').name, 'head'))
    out.append((D.watch(ctx['low'], p, ctx['joints'], side=1, back=0.02, band=(0.55, 0.20, 0.12), face=(0.90, 0.88, 0.80), metal=(0.85, 0.70, 0.35)).name, 'lowerarm_l'))
    return out


SPEC = dict(
    prefix='Caf', folder='Cafe', target_height=1.64, clear=0.009,
    macros=dict(gender=0.0, age=0.40, muscle=0.2, weight=0.30, proportions=0.5, height=0.5, cupsize=0.5, firmness=0.5,
                race=dict(asian=0.3, caucasian=0.5, african=0.2)),
    targets={'head-oval': 0.5, 'head-age-incr': 0.22, 'l-cheek-volume-decr': 0.85, 'r-cheek-volume-decr': 0.85, 'l-cheek-bones-incr': 0.55, 'r-cheek-bones-incr': 0.55,
             'l-eye-bag-incr': 1.0, 'r-eye-bag-incr': 1.0, 'l-eye-height1-decr': 0.3, 'r-eye-height1-decr': 0.3, 'l-eye-eyefold-angle-down': 0.35, 'r-eye-eyefold-angle-down': 0.35,
             'mouth-angles-down': 0.35, 'mouth-upperlip-volume-decr': 0.2, 'mouth-lowerlip-volume-decr': 0.15, 'nose-scale-vert-incr': 0.2, 'nose-scale-horiz-decr': 0.25, 'chin-prominent-incr': 0.2,
             'chin-width-decr': 0.3, 'eyebrows-trans-down': 0.2, 'neck-scale-horiz-decr': 0.3},
    brows='eyebrow004', brow_color=(0.20, 0.09, 0.05), eyes=(0.10, 0.20, 0.10),
    skin=dict(base=(0.44, 0.28, 0.22), lips=(0.40, 0.20, 0.18), blush=(0.46, 0.25, 0.21), shadow=(0.22, 0.12, 0.13)),
    hair=dict(asset='rehmanpolanski_hair_bun_brown', tris=1100, tones=[(0.18, 0.07, 0.03), (0.32, 0.14, 0.06), (0.50, 0.26, 0.12)], scale=dict(x=1.0, y=1.0, zu=1.0, zd=1.0)),
    clothes=[
        dict(key='Dress', asset='toigo_shift_dress', tris=1500, sleeve_trim=None, split_z=lambda ctx: [ctx['Z'](0.36) + 0.04, ctx['Z'](0.855) - 0.03], default=('Cloth', (0.05, 0.28, 0.30)),
             rules=lambda ctx: [('Hem', (0.03, 0.18, 0.20), lambda c, n: c.z < ctx['Z'](0.36) + 0.04),
                                ('Neckline', (0.80, 0.78, 0.70), lambda c, n: c.z > ctx['Z'](0.855) - 0.03 and abs(c.x) < 0.1)]),
        dict(key='Shoes', asset='toigo_ballet_flats', tris=700, split_z=lambda ctx: [0.017], default=('Upper', (0.34, 0.05, 0.07)),
             rules=lambda ctx: [('Sole', (0.60, 0.50, 0.36), lambda c, n: c.z < 0.0165)]),
    ],
    accessories=accessories,
)
