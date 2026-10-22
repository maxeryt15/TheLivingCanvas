"""Rebuild an NPC from zero on the live Blender (new scene, base, lowpoly, colour, accessories, rig, bake/export). Usage: python full_build.py Gentleman gentleman"""
import os, subprocess, sys, tempfile
N, l = sys.argv[1], sys.argv[2]
T = tempfile.gettempdir(); here = os.path.dirname(os.path.abspath(__file__))
pre = "import bpy, sys\nsys.path.insert(0,r'D:/TheLivingCanvas/Tools/npc_pipeline'); sys.path.insert(0,r'D:/TheLivingCanvas/Tools/npc_pipeline/specs')\nfor m in [m for m in sys.modules if m.startswith('npc_') or m == '%s']: del sys.modules[m]\nimport npc_factory as F, %s\nS=%s.SPEC\n" % (l, l, l)
steps = [pre + "F.new_scene(S)\n",
         pre + "F.stage_base(S); F.stage_lowpoly(S); F.stage_color(S)\nfor n in [o.name for o in bpy.data.objects if o.type=='EMPTY']: bpy.data.objects.remove(bpy.data.objects[n])\nF.stage_accessories(S); F.stage_rig(S); F.stage_bake_export(S)\n"]
for i, c in enumerate(steps):
    open(T + '/fb%d.py' % i, 'w').write(c)
    r = subprocess.run([sys.executable, os.path.join(here, 'bl.py'), T + '/fb%d.py' % i], capture_output=True, text=True)
    print(N, i, 'FAILED ' + r.stdout[:600] if 'exception_type' in r.stdout else r.stdout[-200:], r.stderr[-200:])
