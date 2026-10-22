"""Render extra shots in the scene currently open in Blender (after preview_build.py). usage: python render_shots.py '[[tag,ang,tx,ty,tz,dist,lens],...]' out_name"""
import json, os, subprocess, sys, tempfile
from PIL import Image
shots = json.loads(sys.argv[1]); out_name = sys.argv[2]
T = tempfile.gettempdir(); here = os.path.dirname(os.path.abspath(__file__)); D = 'D:/TheLivingCanvas/Docs/NPC_Preview/'
code = """import bpy, math
from mathutils import Vector
sc = bpy.context.scene
cam = bpy.data.objects.get('C') or bpy.data.objects.get('QA_Cam')
sc.camera = cam
for tag, ang, tx, ty, tz, dist, lens in %s:
    cam.data.lens = lens
    a = math.radians(ang); t = Vector((tx, ty, tz)); cam.location = Vector((t.x + math.sin(a) * dist, t.y - math.cos(a) * dist, t.z))
    cam.rotation_euler = (t - cam.location).to_track_quat('-Z', 'Y').to_euler()
    sc.render.filepath = r'%s' + 'pv_' + tag + '.png'
    bpy.ops.render.render(write_still=True)
""" % (json.dumps(shots), D)
open(T + '/rs.py', 'w').write(code)
r = subprocess.run([sys.executable, os.path.join(here, 'bl.py'), T + '/rs.py'], capture_output=True, text=True)
print(r.stdout[-200:], r.stderr[-200:])
ims = [Image.open(D + 'pv_%s.png' % s[0]).convert('RGB') for s in shots]
sheet = Image.new('RGB', (420 * len(ims), 700))
for i, im in enumerate(ims):
    sheet.paste(im, (i * 420, 0))
sheet.save(D + out_name + '.png')
