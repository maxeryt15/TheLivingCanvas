"""Curator: woman in her 40s, museum curator. Charcoal suit, ID lanyard, round glasses, brooch, watch."""
import sys
sys.path.insert(0, r'D:\TheLivingCanvas\Tools\npc_pipeline')
import npc_accessories as A
import npc_details as DD


def accessories(ctx, D):
    p, Z = ctx['prefix'], ctx['Z']
    suit = p + '_Suit'
    out = []
    out.append((D.buttons(suit, p, [Z(0.62), Z(0.575)], 0.0, color=(0.55, 0.42, 0.20), radius=0.0095).name, 'skin'))
    out.append((D.lanyard(suit, ctx['low'], p, card_z=Z(0.715), neck_z=Z(0.855), strap=(0.07, 0.30, 0.38), band=(0.62, 0.20, 0.10)).name, 'skin'))
    out.append((A.round_brooch(suit, p + '_Brooch', -0.085, Z(0.785)).name, 'skin'))
    out.append((D.watch(ctx['low'], p, ctx['joints'], side=1, back=0.02, band=(0.30, 0.10, 0.06), face=(0.92, 0.9, 0.82), metal=(0.80, 0.66, 0.36)).name, 'lowerarm_l'))
    out.append((A.fitted_glasses(p + '_Eyes', p + '_Glasses', ctx['low'], p + '_Hair', color=(0.08, 0.03, 0.03, 1)).name, 'head'))
    return out


SPEC = dict(
    lipstick=(0.36, 0.07, 0.09), hide_below=(0.035, []),
    prefix='Cur', folder='Curator', target_height=1.66,
    macros=dict(gender=0.0, age=0.62, muscle=0.4, weight=0.45, proportions=0.5, height=0.52, cupsize=0.5, firmness=0.5,
                race=dict(asian=0.15, caucasian=0.25, african=0.6)),
    targets={'head-oval': 0.5, 'head-age-incr': 0.25, 'l-cheek-bones-incr': 0.3, 'r-cheek-bones-incr': 0.3, 'nose-scale-vert-incr': 0.1,
             'chin-prominent-incr': 0.15, 'mouth-angles-up': 0.75, 'mouth-upperlip-volume-incr': 0.2, 'mouth-lowerlip-volume-incr': 0.1,
             'l-cheek-volume-incr': 0.35, 'r-cheek-volume-incr': 0.35, 'l-eye-eyefold-angle-up': 0.5, 'r-eye-eyefold-angle-up': 0.5,
             'l-eye-height1-incr': 0.25, 'r-eye-height1-incr': 0.25, 'l-eye-scale-incr': 0.25, 'r-eye-scale-incr': 0.25, 'neck-scale-horiz-decr': 0.3},
    brows='eyebrow004', brow_color=(0.03, 0.02, 0.02), eyes=(0.10, 0.05, 0.025),
    skin=dict(base=(0.30, 0.16, 0.10), lips=(0.28, 0.16, 0.14), blush=(0.33, 0.15, 0.11), shadow=(0.21, 0.11, 0.09), lip_strength=0.55),
    hair=dict(asset='littleright_bobcut_hair', tris=1500, fringe_lift=0.006, tones=[(0.025, 0.018, 0.018), (0.055, 0.038, 0.034), (0.10, 0.07, 0.06)],
              scale=dict(x=0.93, y=0.95, zu=0.97, zd=0.95)),
    clothes=[
        dict(key='Suit', asset='toigo_female_suit', tris=1500, sleeve_trim=0.075, flat_regions=['Blouse'], split_planes=lambda ctx: DD.v_planes(ctx['Z'](0.86), ctx['Z'](0.72), 0.055), default=('Jacket', (0.050, 0.055, 0.080)),
             rules=lambda ctx: [
                 ('Skirt', (0.070, 0.075, 0.100), lambda c, n: c.z < ctx['Z'](0.525)),
                 ('Blouse', (0.80, 0.72, 0.58), lambda c, n: c.y < -0.03 and abs(c.x) < 0.055 / (ctx['Z'](0.86) - ctx['Z'](0.72)) * (c.z - ctx['Z'](0.72)) + 0.0002 and ctx['Z'](0.72) < c.z < ctx['Z'](0.87)),
                 ('Cuff', (0.085, 0.09, 0.12), lambda c, n: abs(c.x) > 0.40 and c.z < ctx['Z'](0.68)),
             ]),
        dict(key='Shoes', asset='toigo_flats', no_trim=True, tris=1100, default=('Upper', (0.70, 0.06, 0.04)),
             rules=lambda ctx: [('Sole', (0.12, 0.02, 0.015), lambda c, n: c.z < 0.014)]),
    ],
    accessories=accessories,
)
