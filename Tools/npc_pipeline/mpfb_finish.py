"""Final tidy pass (run after mpfb_resolve_clipping.py): trouser cuffs become clean round cuts with an even height."""
import bpy, bmesh
from mathutils import Vector

o = bpy.data.objects['Rose_Trousers']
bm = bmesh.new()
bm.from_mesh(o.data)
bm.verts.ensure_lookup_table()
for side in (1, -1):
    cuff = [v for v in bm.verts if any(e.is_boundary for e in v.link_edges) and v.co.z < 0.13 and v.co.x * side > 0]
    cs = set(cuff)
    zavg = sum(v.co.z for v in cuff) / len(cuff)
    for v in cuff:
        v.co.z = zavg                                              # one level cut line around the ankle
    for _ in range(10):                                            # even out the spacing around the loop
        tgt = {}
        for v in cuff:
            nb = [e.other_vert(v) for e in v.link_edges if e.is_boundary and e.other_vert(v) in cs]
            if len(nb) == 2:
                tgt[v] = (nb[0].co + nb[1].co) / 2
        for v, p in tgt.items():
            v.co = v.co.lerp(Vector((p.x, p.y, zavg)), 0.5)
    ring2 = [v for v in bm.verts if v not in cs and zavg < v.co.z < zavg + 0.03 and v.co.x * side > 0]
    for _ in range(3):
        bmesh.ops.smooth_vert(bm, verts=ring2, factor=0.4, use_axis_x=True, use_axis_y=True, use_axis_z=True)
bm.to_mesh(o.data)
bm.free()
print('trouser cuffs tidied')
