"""Security guard: man in his 50s, stocky. Dark uniform jacket, chest radio, gold badge, belt, watch."""
import sys
sys.path.insert(0, r'D:\TheLivingCanvas\Tools\npc_pipeline')
import npc_props as P
import npc_details as D


def accessories(ctx, D):
    p, Z = ctx['prefix'], ctx['Z']
    suit = p + '_Suit'
    out = []
    out.append((D.buttons(suit, p, [Z(0.665), Z(0.62), Z(0.575)], 0.0, color=(0.80, 0.66, 0.30), radius=0.0095).name, 'skin'))
    out.append((P.chest_radio(p, [suit], 0.095, Z(0.745)).name, 'skin'))
    out.append((P.tie(p, [suit], Z(0.862), Z(0.70), v_limit=(Z(0.70), Z(0.86), 0.06)).name, 'skin'))
    out.append((D.watch(ctx['low'], p, ctx['joints'], side=1, back=0.02, band=(0.04, 0.04, 0.05), face=(0.10, 0.12, 0.14), metal=(0.55, 0.57, 0.60)).name, 'lowerarm_l'))
    import npc_accessories as A
    out.append((P.medal(p, suit, -0.088, Z(0.752)).name, 'skin'))
    out.append((P.shoulder_boards(p, suit).name, 'skin'))
    out.append((P.sleeve_patch(p, suit, Z(0.797), Z(0.734)).name, 'skin'))
    out.append((A.beauty_mark(ctx['low'], p + '_Base', p + '_Mole').name, 'head'))
    return out


SPEC = dict(
    prefix='Grd', folder='Guard', target_height=1.76,
    macros=dict(gender=1.0, age=0.72, muscle=0.70, weight=0.92, proportions=0.5, height=0.50, cupsize=0.5, firmness=0.5,
                race=dict(asian=0.1, caucasian=0.7, african=0.2)),
    targets={'head-square': 0.4, 'head-age-incr': 0.4, 'chin-prominent-incr': 0.3, 'nose-scale-horiz-incr': 0.2, 'l-eye-bag-incr': 0.35, 'r-eye-bag-incr': 0.35,
             'mouth-angles-down': 0.1, 'neck-scale-horiz-incr': 0.35, 'l-cheek-volume-incr': 0.2, 'r-cheek-volume-incr': 0.2},
    brows='eyebrow007', brow_color=(0.30, 0.30, 0.31), eyes=(0.14, 0.09, 0.05),
    skin=dict(base=(0.44, 0.27, 0.19), lips=(0.40, 0.19, 0.16), blush=(0.50, 0.25, 0.19), shadow=(0.34, 0.22, 0.18)),
    hair=dict(asset='elvs_grump_hair', tris=1400, tones=[(0.22, 0.22, 0.23), (0.42, 0.42, 0.43), (0.62, 0.62, 0.62)], scale=dict(x=1.0, y=1.0, zu=1.0, zd=1.0)),
    clothes=[
        dict(key='Suit', asset='toigo_male_suit_3', tris=1900, sleeve_trim=0.10, flat_regions=['Shirt'], split_planes=lambda ctx: D.v_planes(ctx['Z'](0.86), ctx['Z'](0.70), 0.06), default=('Jacket', (0.04, 0.05, 0.09)),
             rules=lambda ctx: [('Trousers', (0.03, 0.035, 0.06), lambda c, n: c.z < ctx['Z'](0.525)),
                                ('Shirt', (0.80, 0.80, 0.78), lambda c, n: c.y < -0.03 and abs(c.x) < 0.06 / (ctx['Z'](0.86) - ctx['Z'](0.70)) * (c.z - ctx['Z'](0.70)) + 0.0002 and ctx['Z'](0.70) < c.z < ctx['Z'](0.87))]),
        dict(key='Boots', asset='toigo_ankle_boots_male', tris=420, default=('Upper', (0.03, 0.025, 0.025)),
             rules=lambda ctx: [('Sole', (0.12, 0.08, 0.05), lambda c, n: n.z < -0.45 or c.z < 0.02)]),
    ],
    accessories=accessories,
)
