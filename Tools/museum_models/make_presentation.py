"""Regenera ArtSource/Museum/Museum_Presentation.blend: exterior final (museo_exterior.blend) + interior al lado (x+40), sin techo.

blender -b ArtSource/Museum/museo_exterior.blend --python Tools/museum_models/make_presentation.py
"""
import bpy, bmesh, os

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
MUS = os.path.join(ROOT, "ArtSource", "Museum")

with bpy.data.libraries.load(os.path.join(MUS, "Museum_Interior.blend"), link=False) as (df, dt):
    dt.collections = [c for c in df.collections if not c.startswith("Presentation")]
root = bpy.data.collections.new("Interior_x40")
bpy.context.scene.collection.children.link(root)
for c in dt.collections:
    if not any(c.name in [ch.name for ch in p.children] for p in dt.collections):
        root.children.link(c)
seen = set()
for c in dt.collections:
    for o in c.objects:
        if o.parent is None and o.name not in seen:
            o.location.x += 40
            seen.add(o.name)


def strip(name, zmin):
    """Quita las caras por encima de zmin (techo) para ver el interior desde arriba."""
    o = bpy.data.objects.get(name)
    if o is None:
        return
    bm = bmesh.new(); bm.from_mesh(o.data)
    bmesh.ops.delete(bm, geom=[f for f in bm.faces if all(v.co.z > zmin for v in f.verts)], context='FACES')
    bm.to_mesh(o.data); bm.free()


strip("Int_Slabs", 8.05)
strip("Int_Wing_Shell", 5.45)
for n in ("Int_Wing_Tracks",):
    o = bpy.data.objects.get(n)
    if o:
        o.hide_render = True
        o.hide_viewport = True
for lib in list(bpy.data.libraries):
    bpy.data.libraries.remove(lib)
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(MUS, "Museum_Presentation.blend"))
print("PRESENTATION", len(seen))
