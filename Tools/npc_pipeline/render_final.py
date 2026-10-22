"""Render close-ups from a saved _06_final.blend (Base hidden), side by side.
usage: python render_final.py Gardener '[[tag,ang,tx,ty,tz,dist,lens],...]' out_name"""
import json, os, subprocess, sys, tempfile
from PIL import Image
N, shots, out = sys.argv[1], json.loads(sys.argv[2]), sys.argv[3]
T = tempfile.gettempdir(); here = os.path.dirname(os.path.abspath(__file__)); D = 'D:/TheLivingCanvas/Docs/NPC_Preview/'
code = """import bpy, math
from mathutils import Vector
bpy.ops.wm.open_mainfile(filepath=r'D:/TheLivingCanvas/ArtSource/NPC/%s/%s_06_final.blend')
sc = bpy.context.scene
for o in bpy.data.objects:
    if o.type == 'MESH': o.hide_render = o.name.endswith('_Base') or '_Base.' in o.name
sc.render.engine = [e.identifier for e in bpy.types.RenderSettings.bl_rna.properties['engine'].enum_items if 'EEVEE' in e.identifier][0]
sc.world = sc.world or bpy.data.worlds.new('W'); sc.world.use_nodes = True
sc.world.node_tree.nodes['Background'].inputs[1].default_value = 2.2
for n in [o.name for o in bpy.data.objects if o.type == 'LIGHT']: bpy.data.objects.remove(bpy.data.objects[n])
sun = bpy.data.objects.new('S9', bpy.data.lights.new('S9', 'SUN')); sc.collection.objects.link(sun); sun.data.energy = 3; sun.rotation_euler = (math.radians(55), 0, math.radians(30))
cam = bpy.data.objects.new('C9', bpy.data.cameras.new('C9')); sc.collection.objects.link(cam); sc.camera = cam
sc.render.resolution_x, sc.render.resolution_y = 420, 560
for tag, ang, tx, ty, tz, dist, lens in %s:
    cam.data.lens = lens
    a = math.radians(ang); t = Vector((tx, ty, tz)); cam.location = Vector((t.x + math.sin(a) * dist, t.y - math.cos(a) * dist, t.z))
    cam.rotation_euler = (t - cam.location).to_track_quat('-Z', 'Y').to_euler()
    sc.render.filepath = r'%s' + 'rf_' + tag + '.png'
    bpy.ops.render.render(write_still=True)
""" % (N, N, json.dumps(shots), D)
open(T + '/rf.py', 'w').write(code)
r = subprocess.run([sys.executable, os.path.join(here, 'bl.py'), T + '/rf.py'], capture_output=True, text=True)
print(r.stdout[-200:], r.stderr[-200:])
ims = [Image.open(D + 'rf_%s.png' % s[0]).convert('RGB') for s in shots]
sh = Image.new('RGB', (420 * len(ims), 560))
for i, im in enumerate(ims): sh.paste(im, (i * 420, 0))
sh.save(D + out + '.png')
