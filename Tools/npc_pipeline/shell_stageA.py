"""Etapa A de la cascara: respaldo fusionado sin labios -> labios cortos -> texturas VG2 -> Rose -> capas separadas -> guardar NPCs_Shell_Pre.blend (sin borrar nada).
Uso: blender -b ArtSource/NPC/All10_Review_VanGogh_BACKUP_before_lips.blend --python shell_stageA.py"""
import bpy, os
T = r"D:/TheLivingCanvas/Tools/npc_pipeline/"
for f in ('add_lips.py', 'separate_layers.py'):
    exec(open(T + f, encoding='utf-8').read())
NPCS = [('Caf', 'Cafe'), ('Cur', 'Curator'), ('Grd', 'Guard'), ('Stu', 'Student'), ('Gar', 'Gardener'), ('Tou', 'Tourist'),
        ('Gen', 'Gentleman'), ('Cou', 'Courier'), ('Doc', 'Docent'), ('Pnt', 'Painter')]
PAINT = r"D:/TheLivingCanvas/ArtSource/NPC/Painted_Textures/"
bpy.context.scene.render.engine = 'BLENDER_EEVEE'
rep = {}
for p, n in NPCS:
    rep[p + '_lips'] = add_lips_npc(p)
for p, n in NPCS:
    for g in ('skin', 'hair', 'clothes'):
        im = bpy.data.images.get('T_%s_%s_VG.png' % (p, g))
        if im is not None and os.path.exists(PAINT + '%s/T_%s_%s_VG2.png' % (n, p, g)):
            im.filepath = PAINT + '%s/T_%s_%s_VG2.png' % (n, p, g); im.reload(); im.name = 'T_%s_%s_VG2.png' % (p, g)
        hm = bpy.data.images.get('H_%s_%s.png' % (p, g))
        if hm is not None and os.path.exists(PAINT + '%s/H2_%s_%s.png' % (n, p, g)):
            hm.filepath = PAINT + '%s/H2_%s_%s.png' % (n, p, g); hm.reload(); hm.name = 'H2_%s_%s.png' % (p, g)
with bpy.data.libraries.load(r"D:/TheLivingCanvas/ArtSource/NPC/Rose_Retexture.blend", link=False, relative=False) as (s_, d_):
    d_.objects = list(s_.objects)
for o in d_.objects:
    if o is not None and o.name not in bpy.context.scene.collection.objects:
        bpy.context.scene.collection.objects.link(o)
rig = bpy.data.objects['Rose_Rig']; rig.location = (11.0, 0.0, 0.0)
kids = [o for o in rig.children if o.type == 'MESH']; low = bpy.data.objects['Rose_Low']
for o in bpy.context.view_layer.objects: o.select_set(False)
for o in kids: o.select_set(True)
with bpy.context.temp_override(active_object=low, selected_objects=kids, selected_editable_objects=kids, object=low):
    bpy.ops.object.join()
m = bpy.data.objects['Rose_Low']; m.name = 'Rose_Mesh'; m.data.name = 'Rose_Mesh'
with bpy.context.temp_override(active_object=m, selected_objects=[m], selected_editable_objects=[m], object=m):
    bpy.ops.object.vertex_group_limit_total(group_select_mode='ALL', limit=4)
    bpy.ops.object.vertex_group_normalize_all(group_select_mode='ALL', lock_active=False)
for p in [x[0] for x in NPCS] + ['Rose']:
    rep[p + '_layers'] = separate_layers_npc(p)
bpy.ops.wm.save_as_mainfile(filepath=r"D:/TheLivingCanvas/ArtSource/NPC/NPCs_Shell_Pre.blend")
print('STAGEA', {k: (v.get('lips') if 'lips' in k else v['moved']) for k, v in rep.items()})
