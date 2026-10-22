"""UV + baked texture sheets for a faceted NPC (method proven on Rose).
Direction-based (cube) projection per part at real scale, extra density for the head, tiles in a shared atlas per group,
then Cycles diffuse-colour bake into PNGs for hand painting. Run with the NPC in rest pose and the clothes/hair already final.
"""
import bpy, bmesh, math, os


def project(o, regions, density=None):
    """regions: list of (predicate(face_centre)->bool, mode 'cube'|'smart', scale). Faces not matched get smart project."""
    if bpy.context.object and bpy.context.object.mode != 'OBJECT':
        bpy.ops.object.mode_set(mode='OBJECT')
    bpy.ops.object.select_all(action='DESELECT')
    o.select_set(True)
    bpy.context.view_layer.objects.active = o
    me = o.data
    for l in list(me.uv_layers):
        me.uv_layers.remove(l)
    me.uv_layers.new(name='UV_Paint')
    me.uv_layers.active = me.uv_layers[0]
    bpy.ops.object.mode_set(mode='EDIT')
    bm = bmesh.from_edit_mesh(me)
    bm.faces.ensure_lookup_table()
    uvl = bm.loops.layers.uv.verify()
    assigned = set()
    for pred, mode, scale in regions:
        for f in bm.faces:
            f.select_set(False)
        sel = []
        for f in bm.faces:
            if f.index not in assigned and pred(f.calc_center_median()):
                f.select_set(True)
                assigned.add(f.index)
                sel.append(f)
        bmesh.update_edit_mesh(me)
        if not sel:
            continue
        if mode == 'cube':
            bpy.ops.uv.cube_project(cube_size=1.0, correct_aspect=True, clip_to_bounds=False, scale_to_bounds=False)
        else:
            bpy.ops.uv.smart_project(angle_limit=math.radians(89), island_margin=0.002, correct_aspect=True, scale_to_bounds=False)
        if scale != 1.0:
            pts = [l[uvl].uv.copy() for f in sel for l in f.loops]
            cx = sum(p.x for p in pts) / len(pts)
            cy = sum(p.y for p in pts) / len(pts)
            for f in sel:
                for l in f.loops:
                    l[uvl].uv = (cx + (l[uvl].uv.x - cx) * scale, cy + (l[uvl].uv.y - cy) * scale)
    for f in bm.faces:
        f.select_set(f.index not in assigned)
    bmesh.update_edit_mesh(me)
    if any(f.select for f in bm.faces):
        bpy.ops.uv.smart_project(angle_limit=math.radians(89), island_margin=0.002, correct_aspect=True, scale_to_bounds=False)
    bpy.ops.mesh.select_all(action='SELECT')
    bpy.ops.uv.select_all(action='SELECT')
    bpy.ops.uv.pack_islands(margin=0.004, rotate=False, scale=True, shape_method='CONCAVE')
    bpy.ops.object.mode_set(mode='OBJECT')


def _area(o):
    bm = bmesh.new()
    bm.from_mesh(o.data)
    a = sum(f.calc_area() for f in bm.faces)
    bm.free()
    return a


def _shelf(sides, pad=0.006):
    order = sorted(range(len(sides)), key=lambda i: -sides[i])
    pos = {}
    x = y = rowh = 0
    for i in order:
        s = sides[i]
        if x + s > 1:
            x = 0
            y += rowh + pad
            rowh = 0
        if y + s > 1:
            return None
        pos[i] = (x, y)
        x += s + pad
        rowh = max(rowh, s)
    return pos


def tile_atlas(names):
    objs = [bpy.data.objects[n] for n in names]
    if len(objs) == 1:
        return
    ar = [_area(o) for o in objs]
    tot = sum(ar)
    k = 1.0
    while True:
        sides = [math.sqrt(a / tot) * k for a in ar]
        pos = _shelf(sides)
        if pos:
            break
        k *= 0.97
    for i, o in enumerate(objs):
        uv = o.data.uv_layers[0].data
        us = [d.uv[0] for d in uv]
        vs = [d.uv[1] for d in uv]
        u0, v0 = min(us), min(vs)
        span = max(max(us) - u0, max(vs) - v0)
        sc = sides[i] / span
        for d in uv:
            d.uv[0] = pos[i][0] + (d.uv[0] - u0) * sc
            d.uv[1] = pos[i][1] + (d.uv[1] - v0) * sc


def bake_groups(prefix, groups, outdir):
    """groups: {name: ([objects], size)}. Bakes current material colours into T_<prefix>_<name>.png and swaps each group to one paint material."""
    os.makedirs(outdir, exist_ok=True)
    sc = bpy.context.scene
    sc.render.engine = 'CYCLES'
    sc.cycles.device = 'CPU'
    sc.cycles.samples = 4
    sc.cycles.use_denoising = False
    imgs = {}
    for g, (names, size) in groups.items():
        img = bpy.data.images.new('T_%s_%s' % (prefix, g), size, size, alpha=False)
        img.generated_color = (0, 0, 0, 1)
        imgs[g] = img
        for n in names:
            o = bpy.data.objects[n]
            for m in o.data.materials:
                nt = m.node_tree
                t = nt.nodes.new('ShaderNodeTexImage')
                t.name = 'BAKE_' + g
                t.image = img
                nt.nodes.active = t
            for mod in o.modifiers:
                if mod.type == 'SOLIDIFY':
                    mod.show_render = False
    for g, (names, size) in groups.items():
        bpy.ops.object.select_all(action='DESELECT')
        for n in names:
            bpy.data.objects[n].select_set(True)
        bpy.context.view_layer.objects.active = bpy.data.objects[names[0]]
        bpy.ops.object.bake(type='DIFFUSE', pass_filter={'COLOR'}, margin=16, margin_type='EXTEND', use_clear=True)
        imgs[g].filepath_raw = os.path.join(outdir, 'T_%s_%s.png' % (prefix, g))
        imgs[g].file_format = 'PNG'
        imgs[g].save()
    for g, (names, size) in groups.items():
        m = bpy.data.materials.new('%s_%s_Paint' % (prefix, g))
        m.use_nodes = True
        nt = m.node_tree
        for n in list(nt.nodes):
            if n.type != 'OUTPUT_MATERIAL':
                nt.nodes.remove(n)
        out = next(n for n in nt.nodes if n.type == 'OUTPUT_MATERIAL')
        b = nt.nodes.new('ShaderNodeBsdfPrincipled')
        t = nt.nodes.new('ShaderNodeTexImage')
        t.image = imgs[g]
        b.inputs['Roughness'].default_value = 0.9
        nt.links.new(t.outputs['Color'], b.inputs['Base Color'])
        nt.links.new(b.outputs['BSDF'], out.inputs['Surface'])
        for n in names:
            o = bpy.data.objects[n]
            o.data.materials.clear()
            o.data.materials.append(m)
            for p in o.data.polygons:
                p.material_index = 0
            for mod in o.modifiers:
                if mod.type == 'SOLIDIFY':
                    mod.show_render = True
    return imgs
