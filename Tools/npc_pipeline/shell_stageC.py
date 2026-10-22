"""Etapa C: aplica las caras conservadas (etapa B) a NPCs_Shell_Pre.blend, anade las acciones de Unity y guarda NPCs_Shell_Test.blend.
Uso: blender -b NPCs_Shell_Pre.blend --python shell_stageC.py"""
import bpy, json, bmesh
T = r"D:/TheLivingCanvas/Tools/npc_pipeline/"
exec(open(T + 'apply_unity_anims.py', encoding='utf-8').read())
NPCS = [('Caf', 'Cafe'), ('Cur', 'Curator'), ('Grd', 'Guard'), ('Stu', 'Student'), ('Gar', 'Gardener'), ('Tou', 'Tourist'),
        ('Gen', 'Gentleman'), ('Cou', 'Courier'), ('Doc', 'Docent'), ('Pnt', 'Painter'), ('Rose', 'Rose')]
for p, n in NPCS:
    keep = set(json.load(open(r"D:/TheLivingCanvas/ArtSource/NPC/_shell_tmp/%s.json" % p)))
    ob = bpy.data.objects[p + '_Mesh']
    bm = bmesh.new(); bm.from_mesh(ob.data); bm.faces.ensure_lookup_table()
    kill = [f for f in bm.faces if f.index not in keep]
    before = len(bm.faces)
    bmesh.ops.delete(bm, geom=kill, context='FACES')
    loose = [v for v in bm.verts if not v.link_faces]
    if loose:
        bmesh.ops.delete(bm, geom=loose, context='VERTS')
    bm.to_mesh(ob.data); bm.free(); ob.data.update()
    print('CASCARA', p, before, '->', len(ob.data.polygons))
    apply_npc(p, n)
bpy.ops.wm.save_as_mainfile(filepath=r"D:/TheLivingCanvas/ArtSource/NPC/NPCs_Shell_Test.blend")
print('STAGEC ok')
