"""Preview hair candidates on an NPC without touching its files (scratch folder _Preview_<Folder>, no FBX export).
usage: python preview_hair.py curator Curator Cur '[["toigo_curled_under_bob_with_bangs",1400],...]'"""
import json, os, subprocess, sys, tempfile
from PIL import Image
l, N, P, cands = sys.argv[1], sys.argv[2], sys.argv[3], json.loads(sys.argv[4])
T = tempfile.gettempdir(); here = os.path.dirname(os.path.abspath(__file__))
D = 'D:/TheLivingCanvas/Docs/NPC_Preview/'

def run(code):
    open(T + '/ph.py', 'w').write(code)
    r = subprocess.run([sys.executable, os.path.join(here, 'bl.py'), T + '/ph.py'], capture_output=True, text=True)
    return r.stdout[-300:] + r.stderr[-200:]

pre = "import bpy, sys, math\nsys.path.insert(0,r'D:/TheLivingCanvas/Tools/npc_pipeline'); sys.path.insert(0,r'D:/TheLivingCanvas/Tools/npc_pipeline/specs')\nfor m in [m for m in sys.modules if m.startswith('npc_') or m == '%s']: del sys.modules[m]\nimport npc_factory as F, %s\nS = dict(%s.SPEC); S['hair'] = dict(S['hair'])\nS['folder'] = '_Preview_%s'\n" % (l, l, l, N)
tiles = []
for i, cand in enumerate(cands):
    asset, tris = cand[0], cand[1]
    smooth = cand[2] if len(cand) > 2 else None
    scale = cand[3] if len(cand) > 3 else None
    print(run(pre + "F.new_scene(S)\n")[:80])
    code = pre + "S['hair']['asset'] = %r; S['hair']['tris'] = %d; S['hair']['smooth'] = %r\nS['hair'].update(%r)\nF.stage_base(S); F.stage_lowpoly(S); F.stage_color(S)\nfor n in [o.name for o in bpy.data.objects if o.type=='EMPTY']: bpy.data.objects.remove(bpy.data.objects[n])\nF.stage_accessories(S)\n" % (asset, tris, smooth, scale or {})
    code += """
from mathutils import Vector
sc = bpy.context.scene
eng = [e.identifier for e in bpy.types.RenderSettings.bl_rna.properties['engine'].enum_items if 'EEVEE' in e.identifier][0]
sc.render.engine = eng
sc.world = sc.world or bpy.data.worlds.new('W'); sc.world.use_nodes = True
sc.world.node_tree.nodes['Background'].inputs[1].default_value = 2.2
sun = bpy.data.objects.new('S', bpy.data.lights.new('S', 'SUN')); sc.collection.objects.link(sun); sun.data.energy = 2.5; sun.rotation_euler = (math.radians(55), 0, math.radians(30))
for o in bpy.data.objects:
    if o.type == 'MESH': o.hide_render = o.name.endswith('_Base') or '_Base.' in o.name or o.name.endswith('_Hat')
sc.render.resolution_x, sc.render.resolution_y = 420, 700
cam = bpy.data.objects.new('C', bpy.data.cameras.new('C')); sc.collection.objects.link(cam); sc.camera = cam; cam.data.lens = 70
H = max(v.co.z for v in bpy.data.objects['%s_Low'].data.vertices)
for tag, ang in (('f', 0), ('q', 40), ('s', 90), ('b', 160)):
    a = math.radians(ang); t = Vector((0, -0.07, H - 0.11)); cam.location = Vector((t.x + math.sin(a) * 0.9, t.y - math.cos(a) * 0.9, t.z))
    cam.rotation_euler = (t - cam.location).to_track_quat('-Z', 'Y').to_euler()
    sc.render.filepath = r'%s' + 'h%d_' + tag + '.png'
    bpy.ops.render.render(write_still=True)
""" % (P, D, i)
    print(run(code)[:200])
    tiles.append([Image.open(D + 'h%d_%s.png' % (i, t)).convert('RGB') for t in 'fqsb'])
W, Hh = 420, 700
s = Image.new('RGB', (W * 4, Hh * len(cands)))
for r, row in enumerate(tiles):
    for c, im in enumerate(row):
        s.paste(im, (c * W, r * Hh))
s.save(D + 'preview_hair_%s.png' % N)
print('saved')
