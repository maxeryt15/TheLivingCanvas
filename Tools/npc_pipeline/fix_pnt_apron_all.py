"""Painter: fix_pnt_apron.py (pesos del delantal = pesos de la prenda cercana) + fix_pnt_apron_lap.py (bolsillo central 100 % pelvis). Solo pesos."""
import sys, runpy
a = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else []
sv = sys.argv; save = '--save' in a
sys.argv = ['x', '--'] + [x for x in a if x != '--save']; runpy.run_path(r'D:\TheLivingCanvas\Tools\npc_pipeline\fix_pnt_apron.py')
sys.argv = ['x', '--', '--t', '0'] + (['--save'] if save else []); runpy.run_path(r'D:\TheLivingCanvas\Tools\npc_pipeline\fix_pnt_apron_lap.py')
