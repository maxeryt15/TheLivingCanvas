"""'Cascara': deja en la malla SOLO lo que se ve desde fuera. Una cara se conserva si desde alguno de sus puntos de muestra (centro y 3 puntos hacia
los vertices), por cualquiera de sus dos lados, escapa algun rayo hacia el exterior (direcciones de una esfera, sin las que vienen de debajo del suelo).
Lo que queda tapado por completo (piel bajo la ropa, ropa bajo otra, parte trasera de los ojos, interior de la boca) se borra. Despues se
conserva un anillo de seguridad (caras vecinas por arista de las visibles) para que no aparezcan huecos al animar.
Uso: exec(open(r"D:/TheLivingCanvas/Tools/npc_pipeline/shell_cull.py").read()); shell_cull(bpy.data.objects['Caf_Mesh'])"""
import bpy, bmesh, math
from mathutils import Vector
from mathutils.bvhtree import BVHTree

MIN_ELEVATION = -0.17     # no cuenta mirar desde mas de ~10 grados por debajo del horizonte (nadie ve a un NPC desde bajo el suelo)


def _dirs(n):
    out = []
    ga = math.pi * (3.0 - math.sqrt(5.0))
    for i in range(n):
        z = 1 - 2 * (i + 0.5) / n
        r = math.sqrt(max(0.0, 1 - z * z))
        out.append(Vector((math.cos(ga * i) * r, math.sin(ga * i) * r, z)))
    return [d for d in out if d.z > MIN_ELEVATION]


def shell_cull(ob, ndirs=96, eps=0.0006, maxd=30.0, ring=1):
    mw = ob.matrix_world
    bm = bmesh.new(); bm.from_mesh(ob.data)
    bm.faces.ensure_lookup_table(); bm.verts.ensure_lookup_table()
    wbm = bm.copy(); wbm.transform(mw); wbm.faces.ensure_lookup_table(); wbm.normal_update()
    bvh = BVHTree.FromBMesh(wbm)
    dirs = _dirs(ndirs)
    visible = set()
    for f in wbm.faces:
        n = f.normal
        c = f.calc_center_median()
        pts = [c] + [c * 0.4 + v.co * 0.6 for v in f.verts[:3]]
        found = False
        for p in pts:
            for sgn in (1, -1):
                nn = n * sgn
                o = p + nn * eps
                for d in dirs:
                    if d.dot(nn) < 0.15:
                        continue
                    if bvh.ray_cast(o, d, maxd)[0] is None:
                        found = True; break
                if found: break
            if found: break
        if found:
            visible.add(f.index)
    wbm.free()
    keep = set(visible)
    for _ in range(ring):
        add = set()
        for i in keep:
            for e in bm.faces[i].edges:
                for nf in e.link_faces:
                    add.add(nf.index)
        keep |= add
    kill = [f for f in bm.faces if f.index not in keep]
    before = len(bm.faces)
    if kill:
        bmesh.ops.delete(bm, geom=kill, context='FACES')
        loose = [v for v in bm.verts if not v.link_faces]
        if loose:
            bmesh.ops.delete(bm, geom=loose, context='VERTS')
    bm.to_mesh(ob.data); bm.free(); ob.data.update()
    return before, len(ob.data.polygons), len(visible)
