"""Courier: woman in her 30s, athletic. Orange hi-vis tee, dark cargo trousers, tan Bobcat-style construction boots, tool belt (hammer, wrench, nail pouch), wristband."""
import sys
sys.path.insert(0, r'D:\TheLivingCanvas\Tools\npc_pipeline')
import npc_props as P


def accessories(ctx, D):
    p, Z = ctx['prefix'], ctx['Z']
    top, pants = p + '_Tee', p + '_Pants'
    out = []
    import npc_props5 as P5
    out.append((P5.work_boot_details(p, p + '_Boots').name, 'skin'))
    import npc_props2 as P2
    out.append((P2.hand_gloves(p, ctx['low'], ctx['joints'], Z(0.525), x=0.215, y=0.03, base_name=p + '_Base', pair_side=-1, color=(0.72, 0.50, 0.16), cuff=(0.12, 0.12, 0.14)).name, 'skin'))
    out.append((P5.tool_belt(p, [top, pants], Z(0.525)).name, 'skin'))
    out.append((P.bracelet(p, ctx['low'], ctx['joints'], side=1, color=(0.10, 0.10, 0.12), back=0.03, width=0.03, thick=0.0035, name='Wristband').name, 'lowerarm_l'))
    out.append((D.watch(ctx['low'], p, ctx['joints'], side=-1, back=0.075, band=(0.08, 0.08, 0.09), face=(0.10, 0.45, 0.35), metal=(0.50, 0.52, 0.55)).name, 'lowerarm_r') if False else (P.bracelet(p, ctx['low'], ctx['joints'], side=-1, color=(0.85, 0.40, 0.05), back=0.03, width=0.014, thick=0.003, name='Bracelet').name, 'lowerarm_r'))
    return out


SPEC = dict(
    prefix='Cou', folder='Courier', target_height=1.72, clear=0.009, hide_below=(0.255, ['Pants']),
    skin_scars=[dict(side=1, part='forearm', t=(0.25, 0.48), lat=(-0.010, 0.012), dir=(0, 0, 1)), dict(side=1, part='forearm', t=(0.62, 0.78), lat=(0.012, 0.004), dir=(0, -1, 0)),
                dict(side=-1, part='forearm', t=(0.15, 0.40), lat=(0.012, -0.008), dir=(0, 0, 1)), dict(side=-1, part='forearm', t=(0.55, 0.64), lat=(-0.012, -0.006), dir=(0, -1, 0)),
                dict(side=1, part='upper', t=(0.45, 0.62), lat=(-0.006, 0.006), dir=(0, 0, 1)), dict(side=-1, part='upper', t=(0.30, 0.48), lat=(0.008, -0.004), dir=(0, -1, 0)),
                dict(side=1, part='hand', t=(1.08, 1.30), lat=(-0.010, -0.002), dir=(0, 0, 1)), dict(side=-1, part='hand', t=(1.14, 1.34), lat=(0.008, 0.012), dir=(0, 0, 1))], lipstick=(0.52, 0.20, 0.20),
    macros=dict(gender=0.0, age=0.45, muscle=0.5, weight=0.40, proportions=0.5, height=0.5, cupsize=0.5, firmness=0.5,
                race=dict(asian=0.25, caucasian=0.35, african=0.4)),
    targets={'head-oval': 0.55, 'mouth-angles-up': 0.5, 'l-cheek-bones-incr': 0.25, 'r-cheek-bones-incr': 0.25, 'chin-width-decr': 0.4, 'chin-prominent-decr': 0.15, 'neck-scale-horiz-decr': 0.35,
             'l-eye-scale-incr': 0.35, 'r-eye-scale-incr': 0.35, 'l-eye-height1-incr': 0.2, 'r-eye-height1-incr': 0.2, 'mouth-upperlip-volume-incr': 0.4, 'mouth-lowerlip-volume-incr': 0.4,
             'nose-scale-horiz-decr': 0.3, 'nose-scale-vert-decr': 0.15, 'eyebrows-angle-up': 0.2, 'eyebrows-trans-up': 0.15, 'l-cheek-volume-incr': 0.2, 'r-cheek-volume-incr': 0.2},
    brows='eyebrow003', brow_color=(0.04, 0.03, 0.03), eyes=(0.10, 0.05, 0.02),
    skin=dict(base=(0.36, 0.22, 0.15), lips=(0.34, 0.15, 0.14), blush=(0.50, 0.24, 0.17), shadow=(0.26, 0.15, 0.11)),
    hair=dict(asset='elvs_braid_bun', tris=1400, tones=[(0.015, 0.012, 0.012), (0.035, 0.03, 0.03), (0.07, 0.06, 0.055)], scale=dict(x=1.0, y=1.0, zu=1.0, zd=1.0)),
    clothes=[
        dict(key='Pants', asset='toigo_wool_pants', tris=1500, cut_above=0.915, split_z=lambda ctx: [ctx['Z'](0.525) - 0.02], default=('Cargo', (0.05, 0.065, 0.07)),
             rules=lambda ctx: [('Waistband', (0.03, 0.04, 0.045), lambda c, n: c.z > ctx['Z'](0.525) - 0.02),
                                ('Pocket', (0.03, 0.04, 0.045), lambda c, n: abs(c.x) > 0.10 and 0.62 * ctx['Z'](0.525) < c.z < 0.9 * ctx['Z'](0.525) and abs(c.y) < 0.06)]),
        dict(key='Tee', asset='joepal_crude_t-shirt_female', tris=1000, hem_extend=0.04, split_z=lambda ctx: [ctx['Z'](0.66) - 0.012, ctx['Z'](0.66) + 0.012, ctx['Z'](0.60) - 0.012, ctx['Z'](0.60) + 0.012, ctx['Z'](0.855) - 0.03], default=('Hivis', (0.85, 0.28, 0.02)),
             rules=lambda ctx: [('Reflect', (0.80, 0.80, 0.72), lambda c, n: abs(ctx['Z'](0.66) - c.z) < 0.012 and abs(c.x) < 0.2),
                                ('Reflect2', (0.80, 0.80, 0.72), lambda c, n: abs(ctx['Z'](0.60) - c.z) < 0.012 and abs(c.x) < 0.2),
                                ('Collar', (0.05, 0.065, 0.07), lambda c, n: c.z > ctx['Z'](0.855) - 0.03 and abs(c.x) < 0.1)]),
        dict(key='Boots', asset='toigo_ankle_boots_male', tris=900, shaft_up=(0.07, 0.27), shaft_flare=0.08, split_z=lambda ctx: [0.232, 0.024, 0.032], default=('Nubuck', (0.68, 0.47, 0.20)),
             rules=lambda ctx: [('ToeCap', (0.52, 0.34, 0.14), lambda c, n: c.z < 0.075 and c.y < -0.12),
                                ('Collar', (0.27, 0.15, 0.07), lambda c, n: c.z > 0.235),
                                ('Midsole', (0.80, 0.72, 0.50), lambda c, n: 0.024 <= c.z < 0.032),
                                ('Sole', (0.05, 0.045, 0.04), lambda c, n: n.z < -0.45 or c.z < 0.024)]),
    ],
    accessories=accessories,
)
