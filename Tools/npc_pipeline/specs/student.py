"""Art student: young woman (22). Mustard tee, olive cargo pants, red T-bar shoes, purple messy hair, satchel with pins, headphones round the neck, bracelets, freckles, lip scar, heterochromia."""
import sys
sys.path.insert(0, r'D:\TheLivingCanvas\Tools\npc_pipeline')
import npc_props as P


def accessories(ctx, D):
    p, Z = ctx['prefix'], ctx['Z']
    top, pants = p + '_Tee', p + '_Pants'
    out = []
    out.append((P.headphones_on_neck(p, [top, ctx['low']], Z(0.855), color=(0.10, 0.10, 0.12), accent=(0.10, 0.55, 0.60)).name, 'skin'))
    out.append((P.satchel(p, [top, pants, ctx['low']], 0.115, Z(0.50), Z(0.82), bag_w=0.25, bag_h=0.22, bag_d=0.075, side=-1, hip_x=0.15).name, 'skin'))
    out.append((P.bracelet(p, ctx['low'], ctx['joints'], side=1, color=(0.85, 0.18, 0.25), back=0.03, second=((0.15, 0.55, 0.62), 0.055)).name, 'lowerarm_l'))
    import npc_accessories as A
    out.append((A.freckles(ctx['low'], p + '_Eyes', p + '_Freckles').name, 'head'))
    out.append((A.lip_scar(ctx['low'], p + '_Base', p + '_LipScar').name, 'head'))
    return out


SPEC = dict(
    lipstick=(0.7, 0.09, 0.16),
    prefix='Stu', folder='Student', target_height=1.62,
    macros=dict(gender=0.0, age=0.38, muscle=0.35, weight=0.38, proportions=0.5, height=0.5, cupsize=0.45, firmness=0.6,
                race=dict(asian=0.35, caucasian=0.4, african=0.25)),
    targets={'head-round': 0.4, 'l-cheek-volume-incr': 0.25, 'r-cheek-volume-incr': 0.25, 'mouth-angles-up': 0.5, 'mouth-upperlip-volume-incr': 0.25,
             'mouth-lowerlip-volume-incr': 0.2, 'l-eye-scale-incr': 0.3, 'r-eye-scale-incr': 0.3, 'nose-scale-vert-decr': 0.2, 'chin-prominent-decr': 0.1},
    brows='eyebrow002', brow_color=(0.12, 0.07, 0.10), eyes=(0.20, 0.12, 0.05), eyes2=(0.06, 0.62, 0.68),
    skin=dict(base=(0.46, 0.30, 0.22), lips=(0.38, 0.24, 0.22), blush=(0.60, 0.29, 0.26), shadow=(0.38, 0.23, 0.26)),
    hair=dict(asset='elvs_short_daisy_hair', tris=750, tones=[(0.10, 0.04, 0.16), (0.24, 0.08, 0.34), (0.42, 0.18, 0.52)], scale=dict(x=1.0, y=1.0, zu=1.0, zd=1.0)),
    clothes=[
        dict(key='Pants', asset='toigo_harem_pants', tris=1500, default=('Harem', (0.13, 0.17, 0.06)),
             rules=lambda ctx: [('Waist', (0.07, 0.09, 0.03), lambda c, n: c.z > ctx['Z'](0.50) - 0.03),
                                ('Cuff', (0.07, 0.09, 0.03), lambda c, n: c.z < 0.10)]),
        dict(key='Tee', asset='toigo_basic_tucked_t-shirt', tris=1000, hem_extend=0.065, default=('Cotton', (0.62, 0.36, 0.03)),
             rules=lambda ctx: [('Collar', (0.30, 0.16, 0.02), lambda c, n: c.z > ctx['Z'](0.855) - 0.035 and abs(c.x) < 0.1),
                                ('Hem', (0.30, 0.16, 0.02), lambda c, n: ctx['Z'](0.48) < c.z < ctx['Z'](0.50) and abs(c.x) < 0.25)]),
        dict(key='Shoes', asset='cortu_t-bar', tris=380, default=('Upper', (0.45, 0.04, 0.05)),
             rules=lambda ctx: [('Sole', (0.80, 0.78, 0.72), lambda c, n: n.z < -0.45 or c.z < 0.018)]),
    ],
    accessories=accessories,
)
