"""Painter: woman in her 50s. Sage sweater with paint stains, plum harem trousers, flats, grey-streaked bob, red beret, round glasses, bracelet."""
import sys
sys.path.insert(0, r'D:\TheLivingCanvas\Tools\npc_pipeline')
import npc_props as P
import npc_accessories as A


def accessories(ctx, D):
    p, Z = ctx['prefix'], ctx['Z']
    out = []
    out.append((P.beret(p, p + '_Hair', color=(0.62, 0.10, 0.14), extra=0.012).name, 'head'))
    import npc_props2 as P2, npc_props5 as P5
    sw = p + '_Shirt'
    out.append((P2.apron2(p, [sw, ctx['low']], Z(0.74), Z(0.38), Z(0.855), color=(0.62, 0.52, 0.37), trim=(0.34, 0.22, 0.12), band=(0.30, 0.19, 0.10), strap_w=0.028, back_straps=True).name, 'skin'))
    out.append((P5.brushes_in_apron(p, [p + '_Apron'], 0.06, Z(0.66)).name, 'skin'))
    out.append((P.neckerchief(p, [sw, ctx['low']], Z(0.845), color=(0.10, 0.42, 0.48), off=0.010).name, 'skin'))
    out.append((A.round_glasses(p + '_Eyes', p + '_Glasses', color=(0.60, 0.15, 0.20, 1), radius=0.0185, tube=0.0016, shape='rect', drop=0.007, out=0.009).name, 'head'))
    out.append((P.bracelet(p, ctx['low'], ctx['joints'], side=1, color=(0.78, 0.55, 0.18), back=0.03, second=((0.12, 0.45, 0.55), 0.055)).name, 'lowerarm_l'))
    return out


STRIPE = 0.020      # half period of the Breton stripes: bands are real geometry (cut planes) with flat materials, so edges stay crisp and nothing is stretched


def _arm(ctx):
    from mathutils import Vector
    sh, wr = Vector(ctx['joints']['shoulder']), Vector(ctx['joints']['wrist'])
    return sh, (wr - sh).normalized(), (wr - sh).length


def STRIPE_PLANES(ctx):
    sh, ax, L = _arm(ctx)
    z0, z1 = ctx['Z'](0.525) + 0.03, ctx['Z'](0.865)
    out = []
    n = int((z1 - z0) / STRIPE)
    for k in range(1, n + 1):
        out.append(((0, 0, z0 + k * STRIPE), (0, 0, 1), lambda c: abs(c.x) < 0.17))
    for side in (1, -1):
        for k in range(1, int((L - 0.03) / STRIPE)):
            co = (side * (sh.x + ax.x * (0.05 + k * STRIPE)), sh.y + ax.y * (0.05 + k * STRIPE), sh.z + ax.z * (0.05 + k * STRIPE))
            nr = (side * ax.x, ax.y, ax.z)
            out.append((co, nr, lambda c: abs(c.x) >= 0.17))
    return out


def STRIPE_ODD(ctx, c):
    from mathutils import Vector
    z0 = ctx['Z'](0.525) + 0.03
    if abs(c.x) < 0.17:
        if not (z0 < c.z < ctx['Z'](0.865)):
            return False
        return int((c.z - z0) / STRIPE) % 2 == 1
    sh, ax, L = _arm(ctx)
    m = Vector((abs(c.x), c.y, c.z)) - sh
    t = m.dot(ax) - 0.05
    return t > 0 and int(t / STRIPE) % 2 == 1 and t < L - 0.03


SPEC = dict(
    lipstick=(0.5, 0.14, 0.16), wrinkles=0.45,
    skin_scars=[dict(pts=[(0.050, 0.0, 1.50), (0.062, 0.0, 1.488)], dir=(0, -1, 0), color=(0.72, 0.13, 0.13), width_px=11.0, alpha=0.17, falloff=2.0),
                dict(pts=[(0.032, 0.0, 1.60), (0.040, 0.0, 1.597)], dir=(0, -1, 0), color=(0.30, 0.20, 0.16), width_px=3.0, alpha=0.6),
                dict(pts=[(-0.028, 0.0, 1.505), (-0.022, 0.0, 1.50)], dir=(0, -1, 0), color=(0.30, 0.20, 0.16), width_px=2.6, alpha=0.6)], hide_below=(0.075, []),
    prefix='Pnt', folder='Painter', target_height=1.66,
    macros=dict(gender=0.0, age=0.72, muscle=0.3, weight=0.45, proportions=0.5, height=0.5, cupsize=0.5, firmness=0.4,
                race=dict(asian=0.15, caucasian=0.7, african=0.15)),
    targets={'head-rectangular': 0.45, 'head-triangular': 0.45, 'head-scale-vert-incr': 0.3, 'head-age-incr': 0.9, 'l-eye-bag-incr': 0.7, 'r-eye-bag-incr': 0.7, 'mouth-angles-up': 0.4, 'nose-scale-vert-incr': 0.8, 'nose-hump-incr': 1.0, 'nose-point-down': 0.7, 'nose-greek-incr': 0.4, 'nose-width1-decr': 0.4,
             'nose-scale-horiz-decr': 0.2, 'l-cheek-bones-incr': 0.8, 'r-cheek-bones-incr': 0.8, 'l-cheek-volume-decr': 1.0, 'r-cheek-volume-decr': 1.0, 'chin-prominent-incr': 0.8, 'chin-height-incr': 0.5, 'chin-jaw-drop-incr': 0.3,
             'chin-width-decr': 0.5, 'mouth-laugh-lines-out': 0.8, 'mouth-scale-horiz-decr': 0.4, 'eyebrows-angle-up': 0.4, 'eyebrows-trans-up': 0.2, 'l-eye-height1-decr': 0.45, 'r-eye-height1-decr': 0.45, 'l-eye-scale-decr': 0.2, 'r-eye-scale-decr': 0.2, 'mouth-upperlip-volume-decr': 0.5, 'mouth-lowerlip-volume-decr': 0.3, 'eyebrows-trans-down': 0.0},
    brows='eyebrow004', brow_color=(0.35, 0.33, 0.32), eyes=(0.10, 0.18, 0.12),
    skin=dict(base=(0.55, 0.36, 0.28), lips=(0.36, 0.22, 0.20), blush=(0.62, 0.30, 0.26), shadow=(0.44, 0.27, 0.24)),
    hair=dict(asset='elvs_witchy_lil_bob', tris=1100, tones=[(0.30, 0.29, 0.29), (0.52, 0.50, 0.50), (0.72, 0.71, 0.70)], scale=dict(x=1.0, y=1.0, zu=1.0, zd=0.72), clear=0.004, reach=0.06, filler_zmin=1.50, filler_lift=0.004),
    clothes=[
        dict(key='Pants', asset='toigo_harem_pants', tris=1500, hem_extend=0.025, default=('Harem', (0.30, 0.10, 0.22)),
             stains=lambda ctx: [dict(zmin=ctx['Z'](0.28), zmax=ctx['Z'](0.48), count=5, r=(0.012, 0.03), color=(0.12, 0.30, 0.62), alpha=0.55),
                                 dict(zmin=ctx['Z'](0.30), zmax=ctx['Z'](0.48), count=4, r=(0.010, 0.024), color=(0.70, 0.14, 0.14), alpha=0.5),
                                 dict(zmin=ctx['Z'](0.24), zmax=ctx['Z'](0.40), count=3, r=(0.010, 0.022), color=(0.88, 0.74, 0.16), alpha=0.5)],
             rules=lambda ctx: [('Waist', (0.18, 0.06, 0.13), lambda c, n: c.z > ctx['Z'](0.50) - 0.03),
                                ('Cuff', (0.18, 0.06, 0.13), lambda c, n: c.z < 0.10)]),
        dict(key='Shirt', asset='janexx_old_female_sweater', tris=1500, sleeve_trim=0.10, split_z=lambda ctx: [ctx['Z'](0.525) + 0.03], default=('Cream', (0.88, 0.84, 0.72)),
             split_regions=lambda ctx: STRIPE_PLANES(ctx),
             stains=lambda ctx: [dict(zmin=ctx['Z'](0.54), zmax=ctx['Z'](0.62), count=4, r=(0.012, 0.026), color=(0.12, 0.30, 0.64), alpha=0.5, x_abs=(0.0, 0.14)),
                                 dict(zmin=ctx['Z'](0.54), zmax=ctx['Z'](0.62), count=3, r=(0.010, 0.022), color=(0.72, 0.13, 0.13), alpha=0.45, x_abs=(0.0, 0.14))],
             rules=lambda ctx: [('Stripe', (0.06, 0.09, 0.20), lambda c, n: STRIPE_ODD(ctx, c)),
                                ('Hem', (0.06, 0.09, 0.20), lambda c, n: c.z < ctx['Z'](0.525) + 0.03)]),
        dict(key='Shoes', asset='mindfront_shoes_monk_strap_female', tris=800, no_trim=True, cut_above=0.075, split_z=lambda ctx: [0.017], default=('Leather', (0.32, 0.12, 0.08)),
             rules=lambda ctx: [('Sole', (0.05, 0.04, 0.035), lambda c, n: c.z < 0.0165),
                                ('Welt', (0.50, 0.36, 0.16), lambda c, n: 0.0165 <= c.z < 0.024)]),
    ],
    accessories=accessories,
)
