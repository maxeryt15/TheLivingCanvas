"""NPC factory: build a faceted, rigged, UV-unwrapped, hand-paint-ready NPC from a spec (method proven on Rose and the Curator).

Run the stages one per Blender call (so you can look at the result between them):
    new_scene()                      # in its own call; then in the next calls:
    stage_base(spec)                 # MPFB human + face targets + hair/clothes/eyes/brows assets
    stage_lowpoly(spec)              # faceted body + clothes, clipping fixed, hidden body trimmed
    stage_color(spec)                # skin make-up, hair tones, clothes colour regions, eyes, brows
    stage_accessories(spec)          # spec['accessories'](ctx) -> list of (object, bind) ; bind = 'skin' | 'head' | bone name
    stage_rig(spec)                  # MPFB game_engine rig + weights
    stage_bake_export(spec)          # UVs, baked paint sheets, UV guides, FBX, materials.json for Unity
"""
import bpy, bmesh, os, sys, math, json
from mathutils import Vector

sys.path.insert(0, os.path.dirname(__file__))
import mpfb_lowpoly as L
import npc_details as D
import npc_rig as R
import npc_uv_bake as U
import npc_export as E

MPFB = r"C:\Users\cesar\AppData\Roaming\Blender Foundation\Blender\5.2\extensions\.user\blender_org\mpfb\data"
ART = r'D:\TheLivingCanvas\ArtSource\NPC'
UNITY_MODELS = r'D:\TheLivingCanvas\Assets\_TheLivingCanvas\Art\Models\NPC'
UNITY_TEX = r'D:\TheLivingCanvas\Assets\_TheLivingCanvas\Art\Textures\NPC'


def _state_path(spec):
    return os.path.join(ART, spec['folder'], 'state.json')


def _save_state(spec):
    keys = ('_names', '_made', '_neck', '_acc')
    with open(_state_path(spec), 'w') as f:
        json.dump({k: spec[k] for k in keys if k in spec}, f)


def _load_state(spec):
    if os.path.exists(_state_path(spec)):
        spec.update(json.load(open(_state_path(spec))))


def new_scene(spec):
    bpy.ops.wm.read_homefile(use_empty=True)
    os.makedirs(os.path.join(ART, spec['folder']), exist_ok=True)
    bpy.ops.wm.save_as_mainfile(filepath=os.path.join(ART, spec['folder'], spec['folder'] + '_00_start.blend'))


def _mhclo(kind, key):
    d = os.path.join(MPFB, kind, key)
    return os.path.join(d, [f for f in os.listdir(d) if f.endswith('.mhclo')][0])


def _add_asset(base, kind, key, asset_type):
    from bl_ext.blender_org.mpfb.services.humanservice import HumanService as H
    before = set(o.name for o in bpy.data.objects)
    H.add_mhclo_asset(_mhclo(kind, key), base, asset_type=asset_type, material_type='MAKESKIN', set_up_rigging=False)
    new = [o for o in bpy.data.objects if o.name not in before and o.type == 'MESH']
    return new[0].name


def stage_base(spec):
    from bl_ext.blender_org.mpfb.services.humanservice import HumanService as H
    from bl_ext.blender_org.mpfb.services.targetservice import TargetService as T
    from bl_ext.blender_org.mpfb.entities.objectproperties import HumanObjectProperties as P
    m = T.get_default_macro_info_dict()
    m.update({k: v for k, v in spec['macros'].items() if k != 'race'})
    m['race'] = spec['macros']['race']
    base = H.create_human(macro_detail_dict=m, scale=0.1)
    base.name = spec['prefix'] + '_Base'
    th = spec.get('target_height')
    if th:                                                    # tune the macro 'height' until the body is the wanted height (race/weight change it)
        lo, hi = 0.0, 1.0
        for _ in range(9):
            mid = (lo + hi) / 2
            P.set_value('height', mid, entity_reference=base)
            T.reapply_macro_details(base)
            bpy.context.view_layer.update()
            if base.dimensions.z < th:
                lo = mid
            else:
                hi = mid
        print('height macro', round(mid, 3), 'ended at', round(base.dimensions.z, 3))
    for k, v in spec['targets'].items():
        p = T.target_full_path(k)
        if p:
            T.load_target(base, p, weight=v, name=k)
        else:
            print('missing target', k)
    bpy.context.view_layer.update()
    names = {}
    H.add_mhclo_asset(os.path.join(MPFB, 'eyes', 'low-poly', 'low-poly.mhclo'), base, asset_type='Eyes', material_type='MAKESKIN', set_up_rigging=False)
    H.add_mhclo_asset(os.path.join(MPFB, 'eyebrows', spec['brows'], spec['brows'] + '.mhclo'), base, asset_type='Eyebrows', material_type='MAKESKIN', set_up_rigging=False)
    names['hair'] = _add_asset(base, 'hair', spec['hair']['asset'], 'Hair')
    names['clothes'] = []
    for c in spec['clothes']:
        names['clothes'].append(_add_asset(base, 'clothes', c['asset'], 'Clothes'))
    spec['_names'] = names
    _save_state(spec)
    for o in bpy.data.objects:
        if o.name.startswith(base.name + '.'):
            o.hide_set(True)
    print('height', round(base.dimensions.z, 3), names)
    bpy.ops.wm.save_as_mainfile(filepath=os.path.join(ART, spec['folder'], spec['folder'] + '_01_mpfb.blend'))
    return names


def _joint(base, name):
    """World position of an MPFB joint, from the shape-key MIX (the raw vertex coordinates are the unshaped default human)."""
    vg = base.vertex_groups[name]
    idx = [v.index for v in base.data.vertices if any(g.group == vg.index and g.weight > 0.5 for g in v.groups)]
    sk = base.data.shape_keys
    pts = []
    for i in idx:
        co = base.data.vertices[i].co.copy()
        if sk:
            basis = sk.key_blocks[0].data[i].co
            for kb in sk.key_blocks[1:]:
                if kb.mute or kb.value == 0:
                    continue
                co += (kb.data[i].co - basis) * kb.value
        pts.append(base.matrix_world @ co)
    return sum(pts, Vector()) / len(pts)


def stage_lowpoly(spec):
    _load_state(spec)
    p = spec['prefix']
    base = bpy.data.objects[p + '_Base']
    base.hide_set(False)
    for m in base.modifiers:
        if m.name.startswith('Delete.'):
            m.show_viewport = False
            m.show_render = False
    neck = _joint(base, 'joint-neck').z - 0.04
    L.HEAD_RATIO = spec.get('head_ratio', 0.30)
    body = L.build(p + '_Base', p + '_Low', neck_z=neck)
    base.hide_set(True)
    # clothes (inner to outer, as listed in the spec)
    made = []
    for c, src in zip(spec['clothes'], spec['_names']['clothes']):
        o = bpy.data.objects[src]
        o.hide_set(False)
        L.lowpoly_object(src, p + '_' + c['key'], c['tris'], symmetric=c.get('sym', True))
        o.hide_set(True)
        if any(k in c['key'].lower() for k in ('shoe', 'boot')):
            _bm = bmesh.new(); _bm.from_mesh(bpy.data.objects[p + '_' + c['key']].data)
            bmesh.ops.recalc_face_normals(_bm, faces=_bm.faces[:])
            _bm.to_mesh(bpy.data.objects[p + '_' + c['key']].data); _bm.free()
        made.append(p + '_' + c['key'])
        if c.get('cut_above') is not None:      # drop thin parts above the shoe rim (heel pull loops, tongues sticking up)
            bo_ = bpy.data.objects[p + '_' + c['key']]
            bmq = bmesh.new()
            bmq.from_mesh(bo_.data)
            bmesh.ops.bisect_plane(bmq, geom=bmq.verts[:] + bmq.edges[:] + bmq.faces[:], dist=0.0001, plane_co=Vector((0, 0, c['cut_above'])), plane_no=Vector((0, 0, 1)))
            bmesh.ops.delete(bmq, geom=[f_ for f_ in bmq.faces if f_.calc_center_median().z > c['cut_above'] + 0.0005], context='FACES')
            bmesh.ops.delete(bmq, geom=[v_ for v_ in bmq.verts if not v_.link_faces], context='VERTS')
            bmq.to_mesh(bo_.data)
            bmq.free()
        if c.get('shaft_up'):      # taller boot shaft that swallows the trouser hem
            z0, ztarget = c['shaft_up']
            bo = bpy.data.objects[p + '_' + c['key']]
            ztop = max(v.co.z for v in bo.data.vertices)
            k = (ztarget - z0) / max(ztop - z0, 1e-4)
            cen = {}
            for sd in (-1, 1):
                pts = [v.co for v in bo.data.vertices if v.co.x * sd > 0 and 0.05 < v.co.z < 0.10]
                cen[sd] = (sum(q.x for q in pts) / len(pts), sum(q.y for q in pts) / len(pts)) if pts else (0.0, 0.0)
            for v in bo.data.vertices:
                if v.co.z > z0:
                    f_ = min(1.0, (v.co.z - z0) / 0.06)
                    cx_, cy_ = cen[1 if v.co.x > 0 else -1]
                    sc_ = 1.0 + c.get('shaft_flare', 0.16) * f_
                    v.co.x = cx_ + (v.co.x - cx_) * sc_
                    v.co.y = cy_ + (v.co.y - cy_) * sc_
                    v.co.z = z0 + (v.co.z - z0) * k
                    if v.co.z > ztarget - 0.012:
                        v.co.z = ztarget          # flat, even rim
        if c.get('hem_extend'):
            L.extend_hem(p + '_' + c['key'], c['hem_extend'])
        if c.get('sleeve_trim') is not None:
            D.trim_sleeves(p + '_' + c['key'], dict(elbow=_joint(base, 'joint-l-elbow'), wrist=_joint(base, 'joint-l-hand')), c['sleeve_trim'])
    # hair
    hsrc = spec['_names']['hair']
    bpy.data.objects[hsrc].hide_set(False)
    h = L.lowpoly_object(hsrc, p + '_Hair', spec['hair']['tris'], symmetric=False)
    bpy.data.objects[hsrc].hide_set(True)
    cutf = spec['hair'].get('cut_z')
    if cutf:      # end the hair (braid tail) with a clean horizontal cut and a closed cap, as fraction of body height
        zc_ = cutf * max(v.co.z for v in bpy.data.objects[p + '_Base'].data.vertices) if False else cutf * 1.6695
        bmc = bmesh.new()
        bmc.from_mesh(h.data)
        bmesh.ops.bisect_plane(bmc, geom=bmc.verts[:] + bmc.edges[:] + bmc.faces[:], dist=0.0001, plane_co=Vector((0, 0, zc_)), plane_no=Vector((0, 0, 1)))
        bmesh.ops.delete(bmc, geom=[f_ for f_ in bmc.faces if f_.calc_center_median().z < zc_ - 0.0005 and f_.calc_center_median().y > -0.02], context='FACES')
        bmesh.ops.delete(bmc, geom=[v_ for v_ in bmc.verts if not v_.link_faces], context='VERTS')
        edges_ = [e_ for e_ in bmc.edges if e_.is_boundary and all(abs(v_.co.z - zc_) < 0.002 for v_ in e_.verts)]
        if edges_:
            bmesh.ops.holes_fill(bmc, edges=edges_, sides=24)
        bmc.to_mesh(h.data)
        bmc.free()
    sm = spec['hair'].get('smooth')
    if sm:     # (iterations, factor): relax vertices towards their neighbours so shards become soft, more homogeneous locks
        bmh = bmesh.new()
        bmh.from_mesh(h.data)
        for _ in range(sm[0]):
            new = {}
            for v in bmh.verts:
                if v.link_edges:
                    avg = sum((e.other_vert(v).co for e in v.link_edges), Vector()) / len(v.link_edges)
                    new[v] = v.co.lerp(avg, sm[1])
            for v, c in new.items():
                v.co = c
        bmh.to_mesh(h.data)
        bmh.free()
    sc = spec['hair'].get('scale')
    if sc:
        ctr = Vector(sc.get('centre', (0, -0.07, neck + 0.19)))
        for v in h.data.vertices:
            d = v.co - ctr
            v.co = ctr + Vector((d.x * sc['x'], d.y * sc['y'], d.z * (sc['zu'] if d.z > 0 else sc['zd'])))
    eo = D.make_eyes(p + '_Base', p, spec['eyes'], iris2=spec.get('eyes2'), blind=spec.get('blind_eye'))
    if spec.get('eye_look'):      # glance: turn each eyeball about its own centre (yaw, pitch in degrees)
        yaw, pitch = spec['eye_look']
        from mathutils import Matrix
        R_ = Matrix.Rotation(math.radians(yaw), 3, 'Z') @ Matrix.Rotation(math.radians(pitch), 3, 'X')
        for side in (True, False):
            vs_ = [v for v in eo.data.vertices if (v.co.x < 0) == side]
            c_ = sum((v.co for v in vs_), Vector()) / len(vs_)
            for v in vs_:
                v.co = c_ + R_ @ (v.co - c_)
    D.make_brows(p + '_Base', p, spec['brow_color'])
    lift = spec['hair'].get('fringe_lift')
    if lift:   # raise the lower edge of the front fringe so frames and brows have air
        el, er = D.eye_centres_world(p + '_Eyes')
        ez, ey = el.z, el.y
        for v in h.data.vertices:
            if v.co.y < ey + 0.02 and ez + 0.0 < v.co.z < ez + 0.045:
                v.co.z += lift * (1.0 if v.co.z < ez + 0.02 else (ez + 0.045 - v.co.z) / 0.025)
    # clipping: each layer clears the body and every layer inside it
    inner = [p + '_Low']
    report = {}
    for n in made:
        report[n] = L.push_out(n, inner, spec.get('clear', 0.004))
        inner.append(n)
    report['hair'] = L.push_out(p + '_Hair', [p + '_Low'], spec['hair'].get('clear', 0.004), reach=spec['hair'].get('reach'))
    fz = spec['hair'].get('filler_zmin')      # long hair: only close the gap at the scalp, never sheets from the hem down to the neck/shoulders
    report['hair_filler'] = D.hair_filler(p + '_Hair', p + '_Low', where=(lambda co: co.z > fz) if fz else None, lift=spec['hair'].get('filler_lift', 0.004))
    trimmed = L.trim_hidden_body(p + '_Low', [n for c, n in zip(spec['clothes'], made) if not c.get('no_trim')])
    if spec.get('hide_below'):      # drop everything under the boot rim that is not the boot (skin + trousers hidden inside the boots): no overlap, fewer tris
        zcut, keys = spec['hide_below']
        for n in [p + '_Low'] + [p + '_' + k for k in keys]:
            ob = bpy.data.objects[n]
            bmx = bmesh.new()
            bmx.from_mesh(ob.data)
            bmesh.ops.bisect_plane(bmx, geom=bmx.verts[:] + bmx.edges[:] + bmx.faces[:], dist=0.0001, plane_co=Vector((0, 0, zcut)), plane_no=Vector((0, 0, 1)))   # clean straight cut
            bmesh.ops.delete(bmx, geom=[f_ for f_ in bmx.faces if f_.calc_center_median().z < zcut - 0.0005], context='FACES')
            bmesh.ops.delete(bmx, geom=[e_ for e_ in bmx.edges if not e_.link_faces], context='EDGES')
            bmesh.ops.delete(bmx, geom=[v_ for v_ in bmx.verts if not v_.link_edges], context='VERTS')
            bmx.to_mesh(ob.data)
            bmx.free()
    for c, n in zip(spec['clothes'], made):
        if c.get('close_notches'):
            print('notches closed', D.close_notches(n))
    spec['_made'] = made
    spec['_neck'] = neck
    _save_state(spec)
    print('push', report, 'trimmed', trimmed, 'neck', round(neck, 3))
    bpy.ops.wm.save_as_mainfile(filepath=os.path.join(ART, spec['folder'], spec['folder'] + '_02_lowpoly.blend'))


def _ctx(spec):
    p = spec['prefix']
    base = bpy.data.objects[p + '_Base']
    low = bpy.data.objects[p + '_Low']
    head = [v.co for v in low.data.vertices if v.co.z > spec['_neck'] + 0.02]
    top = max(v.z for v in head)
    ctx = dict(prefix=p, base=base, low=low.name, cloth=spec['_made'], height=max(v.co.z for v in low.data.vertices),
               head_top=top, neck=spec['_neck'],
               joints=dict(elbow=_joint(base, 'joint-l-elbow'), wrist=_joint(base, 'joint-l-hand'), shoulder=_joint(base, 'joint-l-shoulder'),
                           pelvis=_joint(base, 'joint-pelvis'), knee=_joint(base, 'joint-l-knee'), ankle=_joint(base, 'joint-l-ankle')),
               eyes=D.eye_centres_world(p + '_Eyes') if hasattr(D, 'eye_centres_world') else None)
    ctx['Z'] = lambda f: f * ctx['height']
    return ctx


def eye_centres_world(name):
    o = bpy.data.objects[name]
    L_, R_ = [], []
    for v in o.data.vertices:
        (L_ if v.co.x < 0 else R_).append(v.co)
    return sum(L_, Vector()) / len(L_), sum(R_, Vector()) / len(R_)


D.eye_centres_world = eye_centres_world


def stage_color(spec):
    _load_state(spec)
    p = spec['prefix']
    ctx = _ctx(spec)
    sk = spec['skin']
    scar_ = None
    if spec.get('scar'):
        sc_ = spec['scar']
        scar_pts = D.carve_scar(p + '_Low', p + '_Eyes', side=sc_.get('side', 1), depth=sc_.get('depth', 0.003), radius=sc_.get('radius', 0.0036))
        scar_ = (scar_pts, sc_.get('radius', 0.0036) * 1.15, sc_.get('color', (0.50, 0.36, 0.31)))
    D.skin_makeup(p + '_Low', p + '_Base', p, sk['base'], sk['lips'], sk.get('blush'), sk.get('shadow'), ctx['eyes'], lip_strength=sk.get('lip_strength', 1.0), scar=scar_)
    D.hair_tones(bpy.data.objects[p + '_Hair'], p, spec['hair']['tones'], spec['hair'].get('bands', 7))
    if spec['hair'].get('back_layers'):
        D.hair_layers(p + '_Hair', **spec['hair']['back_layers'])
    if spec['hair'].get('strands'):
        D.hair_strands(p + '_Hair', **spec['hair']['strands'])
    if spec['hair'].get('gap_sheet'):
        gs = spec['hair']['gap_sheet'](ctx)
        D.hair_filler(p + '_Hair', p + '_Low', max_gap=gs.get('max_gap', 0.06), where=gs['where'], color=gs.get('color', (0.03, 0.026, 0.024)))
    for c in spec['clothes']:
        o = bpy.data.objects[p + '_' + c['key']]
        if c.get('split_planes'):
            D.split_planes(p + '_' + c['key'], c['split_planes'](ctx))
        if c.get('split_regions'):
            D.split_planes_region(p + '_' + c['key'], c['split_regions'](ctx))
        if c.get('split_z'):
            D.split_at_z(p + '_' + c['key'], c['split_z'](ctx))
        if c.get('leg_trim') is not None:
            D.trim_leg_shell(p + '_' + c['key'], c['leg_trim'](ctx))
        if c.get('smooth'):
            D.smooth_region(p + '_' + c['key'], c['smooth'](ctx), iters=c.get('smooth_iters', 6))
        rules = c['rules'](ctx) if callable(c.get('rules')) else c.get('rules', [])
        D.region_materials(o, p + '_' + c['key'], c['default'], rules, c.get('leg_rule'))
    print('coloured', ctx['height'])


def stage_accessories(spec):
    _load_state(spec)
    ctx = _ctx(spec)
    spec['_acc'] = spec['accessories'](ctx, D) if spec.get('accessories') else []
    if spec.get('lipstick'):      # lipstick lives on the lips only: a lifted copy of the lip faces, not a vertex-colour halo
        import npc_accessories as _A
        spec['_acc'].append((_A.lipstick(ctx['low'], ctx['prefix'] + '_Base', ctx['prefix'] + '_Lipstick', color=tuple(spec['lipstick']) + (1,)).name, 'head'))
    _save_state(spec)
    print('accessories', [(a, b) for a, b in spec['_acc']])
    bpy.ops.wm.save_as_mainfile(filepath=os.path.join(ART, spec['folder'], spec['folder'] + '_03_accessories.blend'))


def stage_rig(spec):
    _load_state(spec)
    p = spec['prefix']
    skin_objs = [a for a, b in spec['_acc'] if b == 'skin']
    head_objs = [a for a, b in spec['_acc'] if b == 'head'] + [p + '_Eyes', p + '_Brows', p + '_Hair']
    other = {a: b for a, b in spec['_acc'] if b not in ('skin', 'head')}
    for n in [o.name for o in bpy.data.objects if o.name.startswith(p + '_Base.')]:
        bpy.data.objects[n].hide_set(True)
    arm, rep = R.rig_npc(p, p + '_Base', p + '_Low', spec['_made'] + skin_objs, head_objs, other)
    print(rep)
    bpy.ops.wm.save_as_mainfile(filepath=os.path.join(ART, spec['folder'], spec['folder'] + '_04_rigged.blend'))


def _flat_materials(objs):
    out = {}
    for o in objs:
        for m in o.data.materials:
            b = next((n for n in m.node_tree.nodes if n.type == 'BSDF_PRINCIPLED'), None)
            if b is None or any(n.type == 'TEX_IMAGE' for n in m.node_tree.nodes):
                continue
            c = b.inputs['Base Color'].default_value
            out[m.name] = dict(name=m.name, r=round(c[0], 4), g=round(c[1], 4), b=round(c[2], 4), metal=round(b.inputs['Metallic'].default_value, 2), vc=any(n.type == 'VERTEX_COLOR' for n in m.node_tree.nodes))
    return list(out.values())


def stage_bake_export(spec):
    _load_state(spec)
    p = spec['prefix']
    neck = spec['_neck']
    O = bpy.data.objects
    arm = O[p + '_Rig']
    bpy.context.view_layer.objects.active = arm
    if arm.mode != 'OBJECT':
        bpy.ops.object.mode_set(mode='OBJECT')
    bpy.ops.object.mode_set(mode='POSE')
    for b in arm.pose.bones:
        b.rotation_mode = 'XYZ'
        b.rotation_euler = (0, 0, 0)
        b.location = (0, 0, 0)
    bpy.ops.object.mode_set(mode='OBJECT')
    low = O[p + '_Low']
    U.project(low, [(lambda c: c.z > neck and abs(c.x) < 0.2, 'cube', 3.5), (lambda c: c.x > 0.2, 'smart', 1.0), (lambda c: c.x < -0.2, 'smart', 1.0), (lambda c: c.x >= 0, 'smart', 1.0), (lambda c: c.x < 0, 'smart', 1.0)])
    U.project(O[p + '_Hair'], [(lambda c: True, 'cube', 1.0)])
    cloth = spec['_made']
    for n in cloth:
        U.project(O[n], [(lambda c: abs(c.x) < 0.21 and c.z > spec['_neck'] - 0.9, 'cube', 1.0), (lambda c: c.x >= 0.21, 'smart', 1.0), (lambda c: c.x <= -0.21, 'smart', 1.0), (lambda c: c.x > 0, 'cube', 1.0), (lambda c: c.x <= 0, 'cube', 1.0)])
    U.tile_atlas(cloth)
    # regions kept as flat materials (shirt under a jacket): baked with the garment's default colour so the texture has no light fringe,
    # then given back their own flat material so the border is pure geometry (no texel stair-stepping)
    flat_keep = []
    for c in spec['clothes']:
        for rn in c.get('flat_regions', []):
            o = O[p + '_' + c['key']]
            mname = p + '_' + c['key'] + '_' + rn
            names = [m.name for m in o.data.materials]
            if mname not in names:
                continue
            slot = names.index(mname)
            faces = [pl.index for pl in o.data.polygons if pl.material_index == slot]
            flat_keep.append((o, faces, bpy.data.materials[mname]))
            for i in faces:
                o.data.polygons[i].material_index = 0
    outdir = os.path.join(ART, spec['folder'], 'Textures')
    imgs = U.bake_groups(p, {'skin': ([p + '_Low'], 2048), 'hair': ([p + '_Hair'], 1024), 'clothes': (cloth, 2048)}, outdir)
    for g_, names_ in (('skin', [p + '_Low']), ('hair', [p + '_Hair']), ('clothes', cloth)):      # fill black bake holes inside UV islands (dark specks/lines on the mesh)
        n_, left_ = D.fill_bake_holes(imgs[g_], names_)
        if n_:
            imgs[g_].filepath_raw = os.path.join(outdir, 'T_%s_%s.png' % (p, g_))
            imgs[g_].file_format = 'PNG'
            imgs[g_].save()
        print('bake holes', g_, n_, '->', left_)
    for c in spec['clothes']:      # procedural patterns (pinstripes ...) painted by world position
        if c.get('pattern'):
            import npc_props4 as P4
            P4.paint_pattern(imgs['clothes'], p + '_' + c['key'], c['pattern'](_ctx(spec)))
    for c in spec['clothes']:      # motifs (palm trees ...) stamped into the clothes texture
        if c.get('motifs'):
            import npc_props3 as P3
            P3.paint_motifs(imgs['clothes'], p + '_' + c['key'], c['motifs'](_ctx(spec)))
    for c in spec['clothes']:      # soft stains painted into the clothes texture
        if c.get('stains'):
            D.paint_stains(imgs['clothes'], p + '_' + c['key'], c['stains'](_ctx(spec)))
    if any(c.get('stains') or c.get('motifs') or c.get('pattern') for c in spec['clothes']):
        imgs['clothes'].filepath_raw = os.path.join(outdir, 'T_%s_clothes.png' % p)
        imgs['clothes'].file_format = 'PNG'
        imgs['clothes'].save()
    if spec.get('wrinkles'):
        D.paint_wrinkles(p + '_Low', imgs['skin'], p + '_Eyes', strength=spec['wrinkles'])
        imgs['skin'].filepath_raw = os.path.join(outdir, 'T_%s_skin.png' % p)
        imgs['skin'].file_format = 'PNG'
        imgs['skin'].save()
    if spec.get('skin_scars'):
        D.paint_skin_scars(p + '_Low', imgs['skin'], spec['skin_scars'], _ctx(spec)['joints'])
        imgs['skin'].filepath_raw = os.path.join(outdir, 'T_%s_skin.png' % p)
        imgs['skin'].file_format = 'PNG'
        imgs['skin'].save()
    for o, faces, m_ in flat_keep:
        o.data.materials.append(m_)
        for i in faces:
            o.data.polygons[i].material_index = len(o.data.materials) - 1
    for g, names in (('skin', [p + '_Low']), ('hair', [p + '_Hair']), ('clothes', cloth)):
        for o in list(bpy.data.objects):
            pass
        if bpy.context.object and bpy.context.object.mode != 'OBJECT':
            bpy.ops.object.mode_set(mode='OBJECT')
        bpy.ops.object.select_all(action='DESELECT')
        for n in names:
            O[n].select_set(True)
        bpy.context.view_layer.objects.active = O[names[0]]
        bpy.ops.object.mode_set(mode='EDIT')
        bpy.ops.mesh.select_all(action='SELECT')
        size = 1024 if g == 'hair' else 2048
        bpy.ops.uv.export_layout(filepath=os.path.join(outdir, 'UVGuide_%s_%s.png' % (p, g)), export_all=True, modified=False, mode='PNG', size=(size, size), opacity=0.6)
        bpy.ops.object.mode_set(mode='OBJECT')
    if os.path.exists(os.path.join(ART, 'NO_EXPORT')):      # review mode (file ArtSource/NPC/NO_EXPORT exists): bake and save the blend only, no FBX / textures into Unity
        bpy.ops.wm.save_as_mainfile(filepath=os.path.join(ART, spec['folder'], spec['folder'] + '_06_final.blend'))
        print('saved blend only (no export)')
        return
    path, game = E.export_npc(p, p + '_Rig', p + '_Base', os.path.join(UNITY_MODELS, spec['folder']), outdir, os.path.join(UNITY_TEX, spec['folder']), fbx_name=spec['folder'])
    meshes = [O[n] for n in game]
    data = dict(folder=spec['folder'], prefix=p, fbx=spec['folder'], flat=_flat_materials(meshes),
                paint=[p + '_skin_Paint', p + '_hair_Paint', p + '_clothes_Paint'])
    with open(os.path.join(UNITY_MODELS, spec['folder'], 'materials.json'), 'w') as f:
        json.dump(data, f)
    bpy.ops.wm.save_as_mainfile(filepath=os.path.join(ART, spec['folder'], spec['folder'] + '_06_final.blend'))
    print(path, game, len(data['flat']))
