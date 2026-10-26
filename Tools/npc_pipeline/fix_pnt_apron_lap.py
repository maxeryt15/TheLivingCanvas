"""Painter: bolsillo central del delantal (z<ZMAX, |x|<XM, y<-0.17 en reposo) se hunde 20-40 mm en el regazo sentada: pelvis pesa demasiado.
Correccion (solo pesos): esos vertices pasan a pelvis (1-T) + muslos T repartidos por x (thigh_l en x>0, thigh_r en x<0, 50/50 en x=0). Posiciones intactas.
Uso: --fix en layer_scan/apron_where, o blender -b ..._PAINTER_WORK.blend --python fix_pnt_apron_lap.py -- [--t 0.7 --zmax 0.95 --xm 0.07 --save]"""
import bpy, sys, json
a = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else []
def opt(k, d): return float(a[a.index(k) + 1]) if k in a else d
T = opt('--t', 0.7); ZMAX = opt('--zmax', 0.95); XM = opt('--xm', 0.07)
ob = bpy.data.objects['Pnt_Mesh']; me = ob.data; assert not ob.get('tlc_apron_lap'), 'ya aplicado'
mats = [m.name if m else None for m in me.materials]; AP = {'Pnt_ApronCloth', 'Pnt_ApronTrim', 'Pnt_ApronBand'}
sel = sorted({v for p in me.polygons if mats[p.material_index] in AP for v in p.vertices
              if me.vertices[v].co.z < ZMAX and abs(me.vertices[v].co.x) < XM and me.vertices[v].co.y < -0.17})
rec = {}
for i in sel:
    x = me.vertices[i].co.x; f = min(1.0, max(0.0, 0.5 + x / (2 * XM)))   # f=peso muslo_l
    rec[i] = {ob.vertex_groups[g.group].name: round(g.weight, 3) for g in me.vertices[i].groups}
    for g in list(me.vertices[i].groups): ob.vertex_groups[g.group].remove([i])
    ob.vertex_groups['pelvis'].add([i], 1 - T, 'REPLACE'); ob.vertex_groups['thigh_l'].add([i], T * f, 'REPLACE'); ob.vertex_groups['thigh_r'].add([i], T * (1 - f), 'REPLACE')
ob['tlc_apron_lap'] = 't%.2f zmax%.2f xm%.2f' % (T, ZMAX, XM); me.update(); print('FIX lap verts', len(sel))
json.dump(rec, open(r'D:\TheLivingCanvas\ArtSource\_Exports\NPC_Validation\Painter\reports\fix_apron_lap.json', 'w'))
if '--save' in a: bpy.ops.wm.save_mainfile(); print('SAVED')
