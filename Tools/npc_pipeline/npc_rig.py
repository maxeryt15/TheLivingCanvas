"""Rig a faceted NPC: MPFB game_engine skeleton on the full-res base, weights copied to the low-poly meshes, rigid parts bound to a bone.
usage: rig_npc(prefix='Cur', base='Cur_Base', body='Cur_Low', cloth=[...], head_rigid=[...], rigid_other={obj: bone})
"""
import bpy


def _transfer_all(dst, src, mapping='POLYINTERP_NEAREST'):
    bpy.ops.object.select_all(action='DESELECT')
    bpy.context.view_layer.objects.active = dst
    dst.vertex_groups.clear()
    for vg in src.vertex_groups:
        dst.vertex_groups.new(name=vg.name)
    m = dst.modifiers.new('wt', 'DATA_TRANSFER')
    m.object = src
    m.use_vert_data = True
    m.data_types_verts = {'VGROUP_WEIGHTS'}
    m.vert_mapping = mapping
    m.layers_vgroup_select_src = 'ALL'
    m.layers_vgroup_select_dst = 'NAME'
    while dst.modifiers[0] != m:
        bpy.ops.object.modifier_move_up(modifier=m.name)
    bpy.ops.object.modifier_apply(modifier='wt')


def _read_weights(o, bones, maxinf=4):
    names = {i: vg.name for i, vg in enumerate(o.vertex_groups)}
    data = []
    for v in o.data.vertices:
        d = {names[g.group]: g.weight for g in v.groups if names.get(g.group) in bones and g.weight > 0}
        top = sorted(d.items(), key=lambda kv: -kv[1])[:maxinf]
        s_ = sum(w for _, w in top)
        data.append({k: w / s_ for k, w in top} if s_ else {})
    return data


def _write_weights(o, bones, data):
    o.vertex_groups.clear()
    vgs = {n: o.vertex_groups.new(name=n) for n in bones}
    miss = 0
    for vi, d in enumerate(data):
        if not d:
            miss += 1
        for k, w in d.items():
            vgs[k].add([vi], w, 'REPLACE')
    return miss


def _rebuild(o, bones, maxinf=4):
    names = {i: vg.name for i, vg in enumerate(o.vertex_groups)}
    data = []
    for v in o.data.vertices:
        d = {names[g.group]: g.weight for g in v.groups if names.get(g.group) in bones and g.weight > 0}
        top = sorted(d.items(), key=lambda kv: -kv[1])[:maxinf]
        s = sum(w for _, w in top)
        data.append({k: w / s for k, w in top} if s else {})
    o.vertex_groups.clear()
    vgs = {n: o.vertex_groups.new(name=n) for n in bones}
    missing = 0
    for vi, d in enumerate(data):
        if not d:
            missing += 1
        for k, w in d.items():
            vgs[k].add([vi], w, 'REPLACE')
    return missing


def _seg_dist(p, a, b):
    ab = b - a
    t = max(0.0, min(1.0, (p - a).dot(ab) / max(ab.length_squared, 1e-12)))
    return (p - (a + ab * t)).length


def limit_arms(o, arm, r0=0.055, r1=0.095):
    """Garment vertices far from the arm axis must not carry arm weights (hems next to the hands, the torso side of the armpit):
    scale the arm weights down with the distance to the shoulder-elbow-wrist polyline and give the rest to the nearest torso bone."""
    B = arm.data.bones
    arm_prefix = ('upperarm', 'lowerarm', 'hand', 'thumb', 'index', 'middle', 'ring', 'pinky')
    torso = [n for n in ('pelvis', 'spine_01', 'spine_02', 'spine_03') if n in B]
    poly = {}
    for sd in ('l', 'r'):
        poly[sd] = [B['upperarm_' + sd].head_local, B['lowerarm_' + sd].head_local, B['hand_' + sd].head_local, B['hand_' + sd].tail_local]
    names = {i: vg.name for i, vg in enumerate(o.vertex_groups)}
    data = []
    for v in o.data.vertices:
        d = {names[g.group]: g.weight for g in v.groups if g.weight > 0}
        sd = 'l' if v.co.x > 0 else 'r'          # MPFB left side is +x
        pts = poly[sd]
        dist = min(_seg_dist(v.co, a, b) for a, b in zip(pts, pts[1:]))
        f = 1.0 if dist < r0 else max(0.0, (r1 - dist) / (r1 - r0))
        if f < 1.0:
            moved = 0.0
            for k in list(d):
                if k.startswith(arm_prefix):
                    moved += d[k] * (1 - f)
                    d[k] *= f
            if moved > 0:
                tb = min(torso, key=lambda n: abs(B[n].head_local.z - v.co.z))
                d[tb] = d.get(tb, 0.0) + moved
        if v.co.z > B['pelvis'].head_local.z + 0.15:        # nothing above the hips may follow a leg
            moved = 0.0
            for k in list(d):
                if k.startswith(('thigh', 'calf', 'foot', 'ball')):
                    moved += d.pop(k)
            if moved > 0:
                tb = min(torso, key=lambda n: abs(B[n].head_local.z - v.co.z))
                d[tb] = d.get(tb, 0.0) + moved
        top = sorted(((k, w) for k, w in d.items() if w > 1e-4), key=lambda kv: -kv[1])[:4]
        tot = sum(w for _, w in top)
        data.append({k: w / tot for k, w in top} if tot else {})
    o.vertex_groups.clear()
    vgs = {n: o.vertex_groups.new(name=n) for n in [b.name for b in B if b.use_deform]}
    for vi, d in enumerate(data):
        for k, w in d.items():
            vgs[k].add([vi], w, 'REPLACE')


def limit_legs(o, arm, xdead=0.012):
    """Garment vertices must not carry the weights of the OPPOSITE leg (an inner-thigh / hem vertex whose nearest base surface is the other leg shoots out when one leg lifts):
    move such weights onto the same-side counterpart bone."""
    B = arm.data.bones
    leg_prefix = ('thigh', 'calf', 'foot', 'ball')
    names = {i: vg.name for i, vg in enumerate(o.vertex_groups)}
    data = []
    for v in o.data.vertices:
        d = {names[g.group]: g.weight for g in v.groups if g.weight > 0}
        if abs(v.co.x) > xdead:
            want = '_l' if v.co.x > 0 else '_r'
            other = '_r' if v.co.x > 0 else '_l'
            for k in list(d):
                if k.startswith(leg_prefix) and k.endswith(other):
                    tgt = k[:-2] + want
                    if tgt in B:
                        d[tgt] = d.get(tgt, 0.0) + d.pop(k)
        top = sorted(((k, w) for k, w in d.items() if w > 1e-4), key=lambda kv: -kv[1])[:4]
        tot = sum(w for _, w in top)
        data.append({k: w / tot for k, w in top} if tot else {})
    o.vertex_groups.clear()
    vgs = {n: o.vertex_groups.new(name=n) for n in [b.name for b in B if b.use_deform]}
    for vi, d in enumerate(data):
        for k, w in d.items():
            vgs[k].add([vi], w, 'REPLACE')


def rig_npc(prefix, base, body, cloth, head_rigid, rigid_other=None, rig_type='game_engine'):
    from bl_ext.blender_org.mpfb.services.humanservice import HumanService as H
    b = bpy.data.objects[base]
    b.hide_set(False)
    b.hide_viewport = False
    bpy.ops.object.select_all(action='DESELECT')
    b.select_set(True)
    bpy.context.view_layer.objects.active = b
    arm = H.add_builtin_rig(b, rig_type, import_weights=True)
    arm.name = prefix + '_Rig'
    arm.data.name = prefix + '_Rig'
    bones = [x.name for x in arm.data.bones if x.use_deform]
    low = bpy.data.objects[body]
    _transfer_all(low, b)
    miss = _rebuild(low, bones)
    report = {body: miss}
    for n in cloth:
        o = bpy.data.objects[n]
        # footwear must read the full base body: the low body has its feet trimmed, which leaves foot/ball bones without weights and breaks the Unity Humanoid avatar
        if any(k in n.lower() for k in ('shoe', 'boot')):
            _transfer_all(o, b)
        else:
            # project along the garment's own vertex normals onto the body: a hem hanging next to the hand/forearm must take the TORSO weights,
            # not the weights of the nearest surface (which is the arm and makes the tee/jacket sides shoot up when the arms rise)
            _transfer_all(o, low, 'POLYINTERP_NEAREST')
            near = _read_weights(o, bones)
            _transfer_all(o, low, 'POLYINTERP_VNORPROJ')
            proj = _read_weights(o, bones)
            _write_weights(o, bones, [pr if pr else nr for pr, nr in zip(proj, near)])   # normal projection where it hits, nearest surface elsewhere
        report[n] = _rebuild(o, bones)
        if not any(k in n.lower() for k in ('shoe', 'boot')):
            if any(k in n.lower() for k in ('bag', 'strap', 'phone', 'lanyard', 'camera', 'medal', 'radio', 'badge', 'brooch')):
                limit_arms(o, arm, 0.012, 0.035)   # props hanging across the chest/shoulder follow the torso, not the arm
            elif any(k in n.lower() for k in ('patch', 'epaulet')):
                limit_arms(o, arm, 0.03, 0.06)     # elbow / sleeve patches and shoulder boards stay with the sleeve
            else:
                limit_arms(o, arm)
            limit_legs(o, arm)
    for n in head_rigid:
        o = bpy.data.objects[n]
        o.vertex_groups.clear()
        o.vertex_groups.new(name='head').add(list(range(len(o.data.vertices))), 1.0, 'REPLACE')
    for n, bone in (rigid_other or {}).items():
        o = bpy.data.objects[n]
        o.vertex_groups.clear()
        o.vertex_groups.new(name=bone).add(list(range(len(o.data.vertices))), 1.0, 'REPLACE')
    for n in [body] + cloth + head_rigid + list((rigid_other or {}).keys()):
        o = bpy.data.objects[n]
        for m in list(o.modifiers):
            if m.type == 'ARMATURE':
                o.modifiers.remove(m)
        am = o.modifiers.new('Armature', 'ARMATURE')
        am.object = arm
        bpy.context.view_layer.objects.active = o
        while o.modifiers[0] != am:
            bpy.ops.object.modifier_move_up(modifier=am.name)
        o.parent = arm
        o.matrix_parent_inverse = arm.matrix_world.inverted()
    b.hide_set(True)
    b.hide_viewport = True
    return arm, report
