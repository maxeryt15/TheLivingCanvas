"""Painter: quita la bufanda celeste (Pnt_ScarfCloth): 27 quads sueltos (108 vertices sin conectar) que se ven como un volante dentado alrededor del cuello.
Borra esas caras y sus vertices; el slot queda con 0 caras (Unity lo descarta). Uso: blender -b WORK.blend --python fix_pnt_scarf_remove.py -- [--save]"""
import bpy, bmesh, sys
a = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else []
ob = bpy.data.objects['Pnt_Mesh']; me = ob.data; mats = [m.name for m in me.materials]; si = mats.index('Pnt_ScarfCloth')
assert not ob.get('tlc_scarf_removed'), 'ya aplicado'
bm = bmesh.new(); bm.from_mesh(me)
fs = [f for f in bm.faces if f.material_index == si]; n = len(fs)
bmesh.ops.delete(bm, geom=fs, context='FACES')
orph = [v for v in bm.verts if not v.link_faces]; bmesh.ops.delete(bm, geom=orph, context='VERTS')
bm.to_mesh(me); bm.free(); me.update(); ob['tlc_scarf_removed'] = n
print('SCARF removed faces', n, 'orphan verts', len(orph))
if '--save' in a: bpy.ops.wm.save_mainfile(); print('SCARF saved')
