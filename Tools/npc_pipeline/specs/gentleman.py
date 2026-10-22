"""Old gentleman: man in his 70s, slim. Brown tweed suit with waistcoat feel, round glasses, white hair, pocket watch with chain, pocket square, wrist watch."""
import sys
sys.path.insert(0, r'D:\TheLivingCanvas\Tools\npc_pipeline')
import npc_props as P
import npc_accessories as A
import npc_details as DD
from mathutils import Vector


def accessories(ctx, D):
    p, Z = ctx['prefix'], ctx['Z']
    suit = p + '_Suit'
    import npc_props4 as P4
    out = []
    out.append((P4.suit_buttons(suit, p, [Z(0.64), Z(0.595)], 0.0).name, 'skin'))
    out.append((P4.suit_details(p, suit, Z(0.735), Z(0.545), Z(0.72), Z(0.85), x_off=0.072, square_on=False).name, 'skin'))
    out.append((P4.pocket_watch2(p, suit, 0.0, Z(0.595), -0.085, Z(0.628)).name, 'skin'))
    import npc_props as P
    out.append((P.tie(p, [suit], Z(0.862), Z(0.62), color=(0.07, 0.20, 0.20), dots=(0.80, 0.62, 0.20), stripe2=(0.45, 0.07, 0.10), pattern='bands', v_limit=(Z(0.58), Z(0.86), 0.075)).name, 'skin'))
    import npc_props2 as P2
    out.append((P2.mustache(p, ctx['low'], p + '_Base', color=(0.035, 0.031, 0.029), width=0.046, curl=0.0095).name, 'head'))
    out.append((P4.leather_patches(p, suit, ctx['joints']).name, 'skin'))
    out.append((D.watch(ctx['low'], p, ctx['joints'], side=1, back=0.02, band=(0.20, 0.10, 0.05), face=(0.92, 0.90, 0.80), metal=(0.80, 0.66, 0.36)).name, 'lowerarm_l'))
    return out


SPEC = dict(
    hide_below=(0.055, ['Suit']),
    blind_eye=1, scar=dict(side=1, depth=0.0040, radius=0.0042, color=(0.88, 0.76, 0.70)),
    prefix='Gen', folder='Gentleman', target_height=1.70,
    macros=dict(gender=1.0, age=0.95, muscle=0.1, weight=0.06, proportions=0.5, height=0.5, cupsize=0.5, firmness=0.3,
                race=dict(asian=0.1, caucasian=0.8, african=0.1)),
    targets={'head-oval': 0.5, 'head-age-incr': 1.0, 'l-eye-bag-incr': 1.0, 'r-eye-bag-incr': 1.0, 'l-eye-height1-decr': 0.3, 'r-eye-height1-decr': 0.3,
             'nose-scale-vert-incr': 0.8, 'nose-trans-forward': 0.0, 'nose-hump-incr': 0.4, 'nose-scale-horiz-decr': 0.25, 'nose-point-up-decr': 0.0,
             'chin-prominent-incr': 0.2, 'chin-height-incr': 0.2, 'mouth-angles-down': 0.35, 'l-cheek-volume-decr': 1.0, 'r-cheek-volume-decr': 1.0,
             'l-cheek-bones-incr': 0.55, 'r-cheek-bones-incr': 0.55, 'mouth-laugh-lines-out': 0.8, 'neck-scale-horiz-decr': 0.5, 'l-ear-scale-incr': 0.4, 'r-ear-scale-incr': 0.4,
             'eyebrows-trans-down': 0.2},
    brows='eyebrow009', brow_color=(0.035, 0.031, 0.029), eyes=(0.18, 0.20, 0.25),
    skin=dict(base=(0.52, 0.36, 0.28), lips=(0.50, 0.34, 0.28), blush=(0.55, 0.28, 0.22), shadow=(0.28, 0.18, 0.17)),
    hair=dict(clear=0.008, reach=0.06, asset='culturalibre_hair_14', tris=1800, tones=[(0.030, 0.026, 0.024), (0.11, 0.10, 0.095), (0.62, 0.62, 0.60)],
              scale=dict(x=1.03, y=1.10, zu=1.0, zd=1.22),
              gap_sheet=lambda ctx: dict(where=lambda c: abs(c.x) > 0.03 and c.y < 0.0 and ctx['Z'](0.915) < c.z < ctx['Z'](0.99)), strands=dict(amp=0.007, freq=16.0, drift=6.0, cuts=2)),
    clothes=[
        dict(key='Suit', leg_rule='Trousers', smooth=lambda ctx: (lambda c: abs(c.x) < 0.13 and c.y < 0.0 and ctx['Z'](0.44) < c.z < ctx['Z'](0.56)), asset='toigo_male_suit_tie_and_jacket', tris=1900, sleeve_trim=0.10, flat_regions=['Shirt'],
             split_z=lambda ctx: [ctx['Z'](0.446)],
             pattern=lambda ctx: [dict(zmin=ctx['Z'](0.446), zmax=ctx['Z'](0.90), color=(0.40, 0.26, 0.12), fn=lambda X, Y, Z: ((((X / 0.021) % 1.0) < 0.075) * 0.55)),
                                  dict(zmin=0.0, zmax=ctx['Z'](0.446), color=(0.46, 0.36, 0.15), fn=lambda X, Y, Z: ((((X / 0.026) % 1.0) < 0.06) * 0.35))], split_planes=lambda ctx: DD.v_planes(ctx['Z'](0.86), ctx['Z'](0.72), 0.055), default=('Tweed', (0.17, 0.10, 0.045)),
             rules=lambda ctx: [('Trousers', (0.33, 0.25, 0.09), lambda c, n: c.z < ctx['Z'](0.446)),
                                ('Shirt', (0.85, 0.84, 0.78), lambda c, n: c.y < -0.03 and abs(c.x) < 0.055 / (ctx['Z'](0.86) - ctx['Z'](0.72)) * (c.z - ctx['Z'](0.72)) + 0.0002 and ctx['Z'](0.72) < c.z < ctx['Z'](0.87)),
                                ]),
        dict(key='Shoes', asset='mindfront_shoes_oxford_male', tris=900, no_trim=True, cut_above=0.075, split_z=lambda ctx: [0.017], default=('Leather', (0.012, 0.011, 0.012)),
             rules=lambda ctx: [('Sole', (0.03, 0.025, 0.025), lambda c, n: c.z < 0.0165),
                                ('Welt', (0.05, 0.04, 0.035), lambda c, n: 0.0165 <= c.z < 0.024)]),
    ],
    accessories=accessories,
)
