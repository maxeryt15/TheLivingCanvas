"""Laboratorio (solo memoria): aplica layer_weights.reweight(pref, ztop, tmax, xs). Uso como FIX_SCRIPT de render_pose_sheet.py con FIX_ARGS='Doc 1.0 0.8 0.08'."""
import sys
sys.path.insert(0, r'D:\TheLivingCanvas\Tools\npc_pipeline')
import layer_weights as LW
a = sys.argv[sys.argv.index('--') + 1:]
print('LAB reweight', LW.reweight(a[0], float(a[1]), float(a[2]), float(a[3])))
