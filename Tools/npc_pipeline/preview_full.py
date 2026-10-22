"""Build an NPC from its CURRENT spec into a scratch folder (no FBX, real files untouched) and render a preview sheet.
usage: python preview_build.py student Student Stu '[[tag,ang,tx,ty,tz,dist,lens],...]' out_name   (shots optional)"""
import json, os, subprocess, sys, tempfile
from PIL import Image
l, N, P = sys.argv[1], sys.argv[2], sys.argv[3]
shots = json.loads(sys.argv[4]) if len(sys.argv) > 4 else []
out_name = sys.argv[5] if len(sys.argv) > 5 else 'preview_%s' % N
T = tempfile.gettempdir(); here = os.path.dirname(os.path.abspath(__file__))
D = 'D:/TheLivingCanvas/Docs/NPC_Preview/'

def run(code):
    open(T + '/pb.py', 'w').write(code)
    r = subprocess.run([sys.executable, os.path.join(here, 'bl.py'), T + '/pb.py'], capture_output=True, text=True)
    return r.stdout[-400:] + r.stderr[-300:]

pre = "import bpy, sys, math\nsys.path.insert(0,r'D:/TheLivingCanvas/Tools/npc_pipeline'); sys.path.insert(0,r'D:/TheLivingCanvas/Tools/npc_pipeline/specs')\nfor m in [m for m in sys.modules if m.startswith('npc_') or m == '%s']: del sys.modules[m]\nimport npc_factory as F, %s\nS = dict(%s.SPEC)\nS['folder'] = '_Preview_%s'\n" % (l, l, l, N)
print(run(pre + "F.new_scene(S)\n")[:60])
code = pre + "F.stage_base(S); F.stage_lowpoly(S); F.stage_color(S)\nfor n in [o.name for o in bpy.data.objects if o.type=='EMPTY']: bpy.data.objects.remove(bpy.data.objects[n])\nF.stage_accessories(S); F.stage_rig(S); F.stage_bake_export(S)\n"
code += """
from mathutils import Vector
sc = bpy.context.scene
sc.render.engine = [e.identifier for e in bpy.types.RenderSettings.bl_rna.properties['engine'].enum_items if 'EEVEE' in e.identifier][0]
sc.world = sc.world or bpy.data.worlds.new('W'); sc.world.use_nodes = True
sc.world.node_tree.nodes['Background'].inputs[1].default_value = 2.2
sun = bpy.data.objects.new('S', bpy.data.lights.new('S', 'SUN')); sc.collection.objects.link(sun); sun.data.energy = 2.5; sun.rotation_euler = (math.radians(55), 0, math.radians(30))
fill = bpy.data.objects.new('F', bpy.data.lights.new('F', 'SUN')); sc.collection.objects.link(fill); fill.data.energy = 1.2; fill.rotation_euler = (math.radians(60), 0, math.radians(-130))
for o in bpy.data.objects:
    if o.type == 'MESH': o.hide_render = o.name.endswith('_Base') or '_Base.' in o.name
sc.render.resolution_x, sc.render.resolution_y = 420, 700
cam = bpy.data.objects.new('C', bpy.data.cameras.new('C')); sc.collection.objects.link(cam); sc.camera = cam
for tag, ang, tx, ty, tz, dist, lens in %s:
    cam.data.lens = lens
    a = math.radians(ang); t = Vector((tx, ty, tz)); cam.location = Vector((t.x + math.sin(a) * dist, t.y - math.cos(a) * dist, t.z))
    cam.rotation_euler = (t - cam.location).to_track_quat('-Z', 'Y').to_euler()
    sc.render.filepath = r'%s' + 'pv_' + tag + '.png'
    bpy.ops.render.render(write_still=True)
""" % (json.dumps(shots), D)
print(run(code)[:300])
ims = [Image.open(D + 'pv_%s.png' % s[0]).convert('RGB') for s in shots]
sheet = Image.new('RGB', (420 * len(ims), 700))
for i, im in enumerate(ims):
    sheet.paste(im, (i * 420, 0))
sheet.save(D + out_name + '.png')
print('saved', out_name)
