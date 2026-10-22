"""QA one NPC in the live Blender and compose a contact sheet. Usage: python qa.py Guard Grd"""
import json, os, subprocess, sys, tempfile
from PIL import Image
N, P = sys.argv[1], sys.argv[2]
T = tempfile.gettempdir(); here = os.path.dirname(os.path.abspath(__file__))
extra = json.loads(sys.argv[3]) if len(sys.argv) > 3 else []
json.dump({'folder': N, 'prefix': P, 'extra': extra}, open(T + '/qa_job.json', 'w'))
open(T + '/qa_run.py', 'w').write("exec(open(r'%s').read())" % (here + '/npc_qa_blender.py').replace(chr(92), '/'))
r = subprocess.run([sys.executable, here + '/bl.py', T + '/qa_run.py'], capture_output=True, text=True)
print(r.stdout.replace(chr(92) + 'n', chr(10))[:6000], r.stderr[-300:])
d = 'D:/TheLivingCanvas/Docs/NPC_Preview/'
def sheet(tags, name, w=420, h=700):
    ims = [Image.open(d + 'qa_%s_%s.png' % (N, t)).convert('RGB') for t in tags]
    s = Image.new('RGB', (w * len(ims), h)); [s.paste(im, (i * w, 0)) for i, im in enumerate(ims)]
    s.save(d + 'qa_%s_%s.png' % (N, name))
sheet(['front', 'q3', 'side', 'back', 'pose'], 'sheetA')
sheet(['head_f', 'head_q', 'torso', 'feet'], 'sheetB')
