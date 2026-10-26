"""Mide el estiramiento de aristas de la prenda durante los clips U_* de un NPC (pose / reposo). Valores altos = triangulos pellizcados o desgarrados.
Uso: blender -b X.blend --python edge_stretch.py -- Pref   -> imprime los 8 peores (ratio, clip, frame) y cuantas aristas pasan de 1.6x
"""
import bpy, sys
NAMES = {'Caf': 'Cafe', 'Cou': 'Courier', 'Cur': 'Curator', 'Doc': 'Docent', 'Gar': 'Gardener', 'Gen': 'Gentleman', 'Grd': 'Guard',
         'Pnt': 'Painter', 'Rose': 'Rose', 'Stu': 'Student', 'Tou': 'Tourist'}
CK = ('clothes_paint', 'suit_', 'aproncloth', 'blouse', 'scarfcloth')
pref = sys.argv[sys.argv.index('--') + 1]
WORST_FRAME = None
arm, ob = bpy.data.objects[pref + '_Rig'], bpy.data.objects[pref + '_Mesh']; me = ob.data
edges = set()
for p in me.polygons:
    if any(k in (me.materials[p.material_index].name.lower() if me.materials[p.material_index] else '') for k in CK):
        vs = p.vertices
        for k in range(len(vs)):
            edges.add(tuple(sorted((vs[k], vs[(k + 1) % len(vs)]))))
edges = [e for e in edges if (me.vertices[e[0]].co - me.vertices[e[1]].co).length > 0.004]
rest = {e: (me.vertices[e[0]].co - me.vertices[e[1]].co).length for e in edges}
ad = arm.animation_data or arm.animation_data_create()
res = []
for act in sorted(bpy.data.actions, key=lambda a: a.name):
    if not act.name.startswith('U_') or f'_{NAMES[pref]}_' not in act.name: continue
    ad.action = act; ad.action_slot = act.slots[0]
    f0, f1 = int(act.frame_range[0]), int(act.frame_range[1])
    for f in range(f0, f1 + 1, 3 if f1 - f0 <= 60 else 15):
        bpy.context.scene.frame_set(f); bpy.context.view_layer.update()
        ev = ob.evaluated_get(bpy.context.evaluated_depsgraph_get()); m = ev.to_mesh()
        mx, n = 0, 0
        for e in edges:
            r = (m.vertices[e[0]].co - m.vertices[e[1]].co).length / rest[e]
            r = max(r, 1 / r) if r > 0 else 99
            if r > mx: mx = r
            if r > 1.6: n += 1
        res.append((round(mx, 2), n, act.name, f))
        if '--detail' in sys.argv and act.name.endswith('Walk_Male') and f == 31:
            lst = sorted(((max((m.vertices[e[0]].co - m.vertices[e[1]].co).length / rest[e], rest[e] / max((m.vertices[e[0]].co - m.vertices[e[1]].co).length, 1e-9)), e) for e in edges), reverse=True)[:12]
            for r, e in lst:
                gw = lambda v: {ob.vertex_groups[x.group].name: round(x.weight, 2) for x in me.vertices[v].groups}
                print('WORSTEDGE', round(r, 1), 'rest_mm', round(rest[e]*1000,1), tuple(round(c, 3) for c in me.vertices[e[0]].co), gw(e[0]), gw(e[1]))
        ev.to_mesh_clear()
    if WORST_FRAME is not None: pass
res.sort(reverse=True)
print('STRETCH', pref, 'aristas', len(edges))
for r in res[:8]: print('STRETCH', r)
print('STRETCH_MEAN_over1.6', round(sum(r[1] for r in res) / len(res), 1))
