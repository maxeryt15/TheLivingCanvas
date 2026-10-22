"""Gardener: man in his 50s, tanned and strong. Faded green tee, brown work trousers, high socks, boots, straw hat, belt with gloves, wristband."""
import sys
sys.path.insert(0, r'D:\TheLivingCanvas\Tools\npc_pipeline')
import npc_props as P


def accessories(ctx, D):
    p, Z = ctx['prefix'], ctx['Z']
    out = []
    import npc_props2 as P2
    out.append((P2.straw_hat(p, p + '_Hair', tilt_back=8).name, 'head'))
    out.append((P2.mustache(ctx['low'], p, ctx['low'], p + '_Base') if False else P2.mustache(p, ctx['low'], p + '_Base', color=(0.46, 0.45, 0.43)).name, 'head'))
    out.append((P2.straw_in_mouth(p, ctx['low'], p + '_Base').name, 'head'))
    out.append((P2.hand_gloves(p, ctx['low'], ctx['joints'], Z(0.50), x=0.215, y=-0.02, base_name=p + '_Base', pair_side=-1).name, 'skin'))
    out.append((P.bracelet(p, ctx['low'], ctx['joints'], side=1, color=(0.82, 0.32, 0.12), back=0.03, width=0.03, thick=0.0035, name='Wristband').name, 'lowerarm_l'))
    return out


SPEC = dict(
    wrinkles=0.34, hide_below=(0.255, ['Pants']),
    prefix='Gar', folder='Gardener', clear=0.009, target_height=1.74,
    macros=dict(gender=1.0, age=0.68, muscle=0.75, weight=0.62, proportions=0.5, height=0.5, cupsize=0.5, firmness=0.5,
                race=dict(asian=0.2, caucasian=0.3, african=0.5)),
    targets={'head-square': 1.0, 'head-age-incr': 1.0, 'chin-width-incr': 0.55, 'chin-prominent-incr': 0.45, 'chin-cleft-incr': 0.35, 'chin-height-decr': 0.25,
             'l-cheek-bones-incr': 0.6, 'r-cheek-bones-incr': 0.6, 'l-cheek-volume-decr': 0.7, 'r-cheek-volume-decr': 0.7,
             'l-eye-bag-incr': 1.0, 'r-eye-bag-incr': 1.0, 'l-eye-height1-decr': 0.35, 'r-eye-height1-decr': 0.35, 'l-eye-eyefold-angle-down': 0.4, 'r-eye-eyefold-angle-down': 0.4,
             'nose-scale-vert-incr': 0.4, 'nose-hump-incr': 0.65, 'nose-scale-horiz-incr': 0.2, 'forehead-nubian-incr': 0.4, 'eyebrows-trans-down': 0.45,
             'mouth-laugh-lines-out': 1.0, 'mouth-scale-horiz-incr': 0.25, 'mouth-angles-down': 0.3, 'neck-scale-horiz-incr': 0.5},
    brows='eyebrow005', brow_color=(0.16, 0.12, 0.10), eyes=(0.05, 0.024, 0.011),
    skin=dict(base=(0.42, 0.24, 0.15), lips=(0.34, 0.14, 0.12), blush=(0.52, 0.24, 0.16), shadow=(0.30, 0.17, 0.12)),
    hair=dict(clear=0.008, reach=0.06, asset='culturalibre_hair_14', tris=1300, tones=[(0.20, 0.18, 0.16), (0.34, 0.32, 0.30), (0.52, 0.50, 0.47)], scale=dict(x=1.0, y=1.0, zu=1.0, zd=1.0)),
    clothes=[
        dict(key='Pants', asset='toigo_wool_pants', tris=1500, default=('Work', (0.20, 0.13, 0.07)),
             stains=lambda ctx: [dict(zmin=0.02, zmax=ctx['Z'](0.30), count=26, r=(0.018, 0.045), color=(0.165, 0.105, 0.055), alpha=0.5),
                                 dict(zmin=ctx['Z'](0.22), zmax=ctx['Z'](0.32), count=9, r=(0.022, 0.05), color=(0.15, 0.095, 0.05), alpha=0.48, front=True),
                                 dict(zmin=ctx['Z'](0.32), zmax=ctx['Z'](0.52), count=10, r=(0.015, 0.035), color=(0.19, 0.125, 0.065), alpha=0.35)],
             rules=lambda ctx: [('Waistband', (0.14, 0.09, 0.05), lambda c, n: c.z > ctx['Z'](0.525) - 0.02)]),
        dict(key='Tee', asset='elvs_crude_t-shirt_male', tris=1000, hem_extend=0.04, default=('Cotton', (0.12, 0.30, 0.13)),
             stains=lambda ctx: [dict(zmin=ctx['Z'](0.47), zmax=ctx['Z'](0.62), count=15, r=(0.016, 0.04), color=(0.20, 0.20, 0.08), alpha=0.42),
                                 dict(zmin=ctx['Z'](0.62), zmax=ctx['Z'](0.84), count=10, r=(0.014, 0.03), color=(0.16, 0.22, 0.08), alpha=0.3),
                                 dict(zmin=ctx['Z'](0.55), zmax=ctx['Z'](0.80), count=5, r=(0.03, 0.06), color=(0.09, 0.22, 0.09), alpha=0.3)],
             rules=lambda ctx: [('Collar', (0.07, 0.17, 0.08), lambda c, n: c.z > ctx['Z'](0.855) - 0.03 and abs(c.x) < 0.1),
                                ('Hem', (0.07, 0.17, 0.08), lambda c, n: ctx['Z'](0.47) < c.z < ctx['Z'](0.50) and abs(c.x) < 0.25),
                                ('Sweat', (0.09, 0.22, 0.10), lambda c, n: c.y > 0.02 and ctx['Z'](0.68) < c.z < ctx['Z'](0.78) and abs(c.x) < 0.1)]),
        dict(key='Boots', asset='toigo_ankle_boots_male', tris=900, shaft_up=(0.07, 0.27), shaft_flare=0.2, split_z=lambda ctx: [0.232], default=('Leather', (0.30, 0.15, 0.07)),
             rules=lambda ctx: [('ToeCap', (0.22, 0.105, 0.05), lambda c, n: c.z < 0.075 and c.y < -0.12),
                                                                ('Cuff', (0.14, 0.07, 0.03), lambda c, n: c.z > 0.235),
                                ('Sole', (0.06, 0.045, 0.035), lambda c, n: n.z < -0.45 or c.z < 0.02)]),
    ],
    accessories=accessories,
)
