"""Preview several shoe assets on an NPC: python shoe_variants.py gentleman Gentleman Gen '[["shoes02",700],...]' (needs the Shoes clothes entry)"""
import json, os, subprocess, sys, tempfile
from PIL import Image
l, N, P, cands = sys.argv[1], sys.argv[2], sys.argv[3], json.loads(sys.argv[4])
T = tempfile.gettempdir(); here = os.path.dirname(os.path.abspath(__file__)); D = 'D:/TheLivingCanvas/Docs/NPC_Preview/'
def run(code):
    open(T + '/sv.py', 'w').write(code)
    r = subprocess.run([sys.executable, os.path.join(here, 'bl.py'), T + '/sv.py'], capture_output=True, text=True)
    return r.stdout[-300:] + r.stderr[-200:]
pre = "import bpy, sys, math\nsys.path.insert(0,r'D:/TheLivingCanvas/Tools/npc_pipeline'); sys.path.insert(0,r'D:/TheLivingCanvas/Tools/npc_pipeline/specs')\nfor m in [m for m in sys.modules if m.startswith('npc_') or m == '%s']: del sys.modules[m]\nimport npc_factory as F, %s\nS = dict(%s.SPEC)\nS['folder'] = '_Preview_%s'\n" % (l, l, l, N)
rows = []
for i, (asset, tris) in enumerate(cands):
    print(run(pre + "F.new_scene(S)\n")[:40])
    code = pre + "S['clothes'] = [dict(c) for c in S['clothes']]\nfor c in S['clothes']:\n    if 'shoe' in c['key'].lower() or 'boot' in c['key'].lower():\n        c['asset'] = %r; c['tris'] = %d\nF.stage_base(S); F.stage_lowpoly(S); F.stage_color(S)\nfor n in [o.name for o in bpy.data.objects if o.type=='EMPTY']: bpy.data.objects.remove(bpy.data.objects[n])\nF.stage_accessories(S)\n" % (asset, tris)
    code += """
from mathutils import Vector
sc = bpy.context.scene
sc.render.engine = [e.identifier for e in bpy.types.RenderSettings.bl_rna.properties['engine'].enum_items if 'EEVEE' in e.identifier][0]
sc.world = sc.world or bpy.data.worlds.new('W'); sc.world.use_nodes = True
sc.world.node_tree.nodes['Background'].inputs[1].default_value = 2.2
for ang_, en in ((55, 2.5), (-130, 1.5)):
    sun = bpy.data.objects.new('S%%d' %% ang_, bpy.data.lights.new('S%%d' %% ang_, 'SUN')); sc.collection.objects.link(sun); sun.data.energy = en; sun.rotation_euler = (math.radians(55), 0, math.radians(ang_))
for o in bpy.data.objects:
    if o.type == 'MESH': o.hide_render = o.name.endswith('_Base') or '_Base.' in o.name
sc.render.resolution_x, sc.render.resolution_y = 420, 700
cam = bpy.data.objects.new('C', bpy.data.cameras.new('C')); sc.collection.objects.link(cam); sc.camera = cam; cam.data.lens = 60
for tag, ang in (('a', 25), ('b', 90), ('c', 155)):
    a = math.radians(ang); t = Vector((0, -0.04, 0.10)); cam.location = Vector((t.x + math.sin(a) * 0.9, t.y - math.cos(a) * 0.9, t.z))
    cam.rotation_euler = (t - cam.location).to_track_quat('-Z', 'Y').to_euler()
    sc.render.filepath = r'%s' + 'sv%d_' + tag + '.png'
    bpy.ops.render.render(write_still=True)
""" % (D, i)
    print(run(code)[:150])
    rows.append([Image.open(D + 'sv%d_%s.png' % (i, t)).convert('RGB').crop((0, 250, 420, 600)) for t in 'abc'])
s = Image.new('RGB', (1260, 350 * len(rows)))
for r, row in enumerate(rows):
    for c, im in enumerate(row):
        s.paste(im, (c * 420, r * 350))
s.save(D + 'preview_shoes_%s.png' % N)
print('saved')
