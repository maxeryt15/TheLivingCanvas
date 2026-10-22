"""Etapa B: calcula las caras a conservar de UN NPC (prefijo tras '--') y las guarda en ArtSource/NPC/_shell_tmp/<prefijo>.json.
Uso: blender -b NPCs_Shell_Pre.blend --python shell_stageB.py -- Caf"""
import bpy, sys, json, os, time
T = r"D:/TheLivingCanvas/Tools/npc_pipeline/"
exec(open(T + 'shell_poses.py', encoding='utf-8').read())
prefix = sys.argv[sys.argv.index('--') + 1]
npc = {'Caf': 'Cafe', 'Cur': 'Curator', 'Grd': 'Guard', 'Stu': 'Student', 'Gar': 'Gardener', 'Tou': 'Tourist', 'Gen': 'Gentleman',
       'Cou': 'Courier', 'Doc': 'Docent', 'Pnt': 'Painter', 'Rose': 'Rose'}[prefix]
t = time.time()
keep = keep_faces(bpy.data.objects[prefix + '_Mesh'], bpy.data.objects[prefix + '_Rig'],
                  r"D:/TheLivingCanvas/ArtSource/NPC/AnimsAll/%s.json" % npc, log=lambda *a: print('B', prefix, *a))
os.makedirs(r"D:/TheLivingCanvas/ArtSource/NPC/_shell_tmp", exist_ok=True)
json.dump(keep, open(r"D:/TheLivingCanvas/ArtSource/NPC/_shell_tmp/%s.json" % prefix, 'w'))
print('BDONE', prefix, len(keep), round(time.time() - t), 's')
