"""Re-run colour..export for an NPC from its _02_lowpoly.blend on the live Blender. Usage: python run_stages.py Guard guard"""
import os, subprocess, sys, tempfile
N, l = sys.argv[1], sys.argv[2]
T = tempfile.gettempdir()
open(T + '/o.py', 'w').write("import bpy\nbpy.ops.wm.open_mainfile(filepath=r'D:/TheLivingCanvas/ArtSource/NPC/%s/%s_02_lowpoly.blend')\n" % (N, N))
open(T + '/s.py', 'w').write("""import bpy, sys
sys.path.insert(0,r'D:/TheLivingCanvas/Tools/npc_pipeline'); sys.path.insert(0,r'D:/TheLivingCanvas/Tools/npc_pipeline/specs')
for m in [m for m in sys.modules if m in ('npc_details','npc_props','npc_accessories','npc_factory','npc_rig','npc_uv_bake','npc_export','%s')]: del sys.modules[m]
import npc_factory as F, %s
S=%s.SPEC
F.stage_color(S)
for n in [o.name for o in bpy.data.objects if o.type=='EMPTY']: bpy.data.objects.remove(bpy.data.objects[n])
F.stage_accessories(S); F.stage_rig(S); F.stage_bake_export(S)
""" % (l, l, l))
here = os.path.dirname(os.path.abspath(__file__))
for f in ('o', 's'):
    r = subprocess.run([sys.executable, os.path.join(here, 'bl.py'), T + '/%s.py' % f], capture_output=True, text=True)
    print(N, f, r.stdout[-250:], r.stderr[-200:])
