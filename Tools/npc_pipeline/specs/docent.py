"""Docent: man, 28, slim. Burgundy jacket with bowtie, cream shirt, olive trousers, dark skin, afro hair, small hexagonal glasses, oxford shoes, watch."""
import sys
sys.path.insert(0, r'D:\TheLivingCanvas\Tools\npc_pipeline')
import npc_props as P
import npc_details as DD
import npc_accessories as A


def accessories(ctx, D):
    p, Z = ctx['prefix'], ctx['Z']
    suit = p + '_Suit'
    out = []
    out.append((D.buttons(suit, p, [Z(0.64), Z(0.595)], 0.0, color=(0.80, 0.66, 0.30), radius=0.0095).name, 'skin'))
    out.append((A.round_glasses(p + '_Eyes', p + '_Glasses', color=(0.06, 0.18, 0.30, 1), radius=0.0165, tube=0.0014, shape='hex', drop=0.007, out=0.008).name, 'head'))
    out.append((D.watch(ctx['low'], p, ctx['joints'], side=1, back=0.02, band=(0.04, 0.04, 0.05), face=(0.85, 0.85, 0.80), metal=(0.72, 0.72, 0.75)).name, 'lowerarm_l'))
    return out


SPEC = dict(
    prefix='Doc', folder='Docent', target_height=1.75, clear=0.009, hide_below=(0.055, ['Suit']),
    macros=dict(gender=1.0, age=0.4, muscle=0.3, weight=0.3, proportions=0.5, height=0.5, cupsize=0.5, firmness=0.5,
                race=dict(asian=0.1, caucasian=0.1, african=0.8)),
    targets={'head-oval': 0.5, 'mouth-angles-up': 0.6, 'l-eye-scale-incr': 0.25, 'r-eye-scale-incr': 0.25, 'chin-prominent-decr': 0.1, 'nose-scale-vert-decr': 0.15,
             'l-cheek-volume-incr': 0.15, 'r-cheek-volume-incr': 0.15},
    brows='eyebrow011', brow_color=(0.05, 0.03, 0.03), eyes=(0.12, 0.08, 0.03),
    skin=dict(base=(0.20, 0.115, 0.08), lips=(0.30, 0.12, 0.11), blush=(0.30, 0.15, 0.11), shadow=(0.15, 0.085, 0.065)),
    hair=dict(asset='afro01', tris=1500, smooth=(10, 0.6), tones=[(0.02, 0.015, 0.015), (0.03, 0.022, 0.02), (0.04, 0.03, 0.026)], scale=dict(x=1.0, y=1.0, zu=1.0, zd=1.0)),
    clothes=[
        dict(key='Suit', close_notches=True, leg_trim=lambda ctx: ctx['Z'](0.46) + 0.05, leg_rule='Trousers', asset='toigo_suit_with_jacket_and_bowtie', tris=1900, sleeve_trim=0.10, flat_regions=['Shirt'], split_planes=lambda ctx: DD.v_planes(ctx['Z'](0.86), ctx['Z'](0.72), 0.055), split_z=lambda ctx: [ctx['Z'](0.46)], default=('Jacket', (0.28, 0.04, 0.07)),
             rules=lambda ctx: [('Trousers', (0.26, 0.34, 0.08), lambda c, n: c.z < ctx['Z'](0.46)),
                                ('Shirt', (0.025, 0.045, 0.13), lambda c, n: c.y < -0.03 and abs(c.x) < 0.055 / (ctx['Z'](0.86) - ctx['Z'](0.72)) * (c.z - ctx['Z'](0.72)) + 0.0002 and ctx['Z'](0.72) < c.z < ctx['Z'](0.87)),
                                ('Bowtie', (0.80, 0.55, 0.05), lambda c, n: c.y < -0.03 and abs(c.x) < 0.04 and ctx['Z'](0.80) < c.z < ctx['Z'](0.86))]),
        dict(key='Shoes', asset='mindfront_shoes_oxford_male', tris=900, no_trim=True, cut_above=0.075, split_z=lambda ctx: [0.017], default=('Leather', (0.09, 0.045, 0.03)),
             rules=lambda ctx: [('Sole', (0.03, 0.025, 0.025), lambda c, n: c.z < 0.0165),
                                ('Welt', (0.05, 0.03, 0.02), lambda c, n: 0.0165 <= c.z < 0.024)]),
    ],
    accessories=accessories,
)
