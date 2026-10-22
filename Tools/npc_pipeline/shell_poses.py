"""Cascara robusta a las animaciones: una cara se conserva si es visible desde fuera en el reposo O en CUALQUIERA de las poses muestreadas
(JSON de ArtSource/NPC/AnimsAll/<Npc>.json: 37 clips x 6 fotogramas), mas todo lo que va pesado a cabeza/cuello (nunca se borra) y un anillo de seguridad.
Devuelve la lista de indices de cara a conservar."""
import bpy, json, math, numpy as np
from mathutils import Vector, Matrix, Quaternion
from mathutils.bvhtree import BVHTree

MIN_ELEVATION = -0.17     # ~ -10 grados: nadie ve a un NPC desde bajo el suelo
MAX_ELEVATION = 0.87      # ~ +60 grados: la camara en primera persona no mira de arriba abajo por el escote
PROTECT_BONES = ('neck_01',)   # el cuello nunca se borra (la cabeza si puede perder su interior: boca, trasera de los ojos)
MU = Matrix(((-1, 0, 0), (0, 0, 1), (0, -1, 0)))
MUT = MU.transposed()


def _dirs(n):
    out = []
    ga = math.pi * (3.0 - math.sqrt(5.0))
    for i in range(n):
        z = 1 - 2 * (i + 0.5) / n
        r = math.sqrt(max(0.0, 1 - z * z))
        out.append(Vector((math.cos(ga * i) * r, math.sin(ga * i) * r, z)))
    return [d for d in out if MIN_ELEVATION < d.z < MAX_ELEVATION]


def _uq(a):
    return Quaternion((a[6], a[3], a[4], a[5]))


def set_pose(arm, names, pbs, idx, rest_p, rest_q, fr):
    target = {}
    for i in idx:
        n = names[i]; pb = pbs[n]; rec = fr[i]
        dq = _uq(rec) @ rest_q[i].inverted()
        dp_b = MUT @ (Vector(rec[:3]) - rest_p[i])
        ml = pb.bone.matrix_local
        M = Matrix.Translation(ml.translation + dp_b) @ (MUT @ dq.to_matrix() @ MU @ ml.to_3x3()).to_4x4()
        target[n] = M
        par = pb.parent
        basis = ml.inverted() @ M if par is None else (par.bone.matrix_local.inverted() @ ml).inverted() @ target[par.name].inverted() @ M
        pb.location = basis.to_translation(); pb.rotation_quaternion = basis.to_quaternion()


def visible_faces(polys, wco, test_faces, dirs, eps=0.0006, maxd=30.0):
    """Subconjunto de test_faces visible desde fuera con las posiciones mundiales wco (lista de listas)."""
    bvh = BVHTree.FromPolygons(wco, polys)
    out = set()
    for fi in test_faces:
        vs = polys[fi]
        pts = [Vector(wco[v]) for v in vs]
        c = sum(pts, Vector()) / len(pts)
        n = Vector()
        for k in range(len(pts)):   # normal de Newell
            a, b = pts[k], pts[(k + 1) % len(pts)]
            n += Vector(((a.y - b.y) * (a.z + b.z), (a.z - b.z) * (a.x + b.x), (a.x - b.x) * (a.y + b.y)))
        if n.length < 1e-12:
            out.add(fi); continue
        n.normalize()
        samples = [c] + [c * 0.4 + p * 0.6 for p in pts[:3]]
        found = False
        for p in samples:
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
            out.add(fi)
    return out


def keep_faces(ob, arm, anims_json, ndirs=96, ring=1, log=print):
    me = ob.data; mw = ob.matrix_world
    polys = [tuple(p.vertices) for p in me.polygons]
    nf = len(polys)
    dirs = _dirs(ndirs)
    R = np.array(mw.to_3x3()); t = np.array(mw.translation)
    d = json.load(open(anims_json))
    names = d['bones']; pbs = {n: arm.pose.bones.get(n) for n in names}
    idx = [i for i, n in enumerate(names) if pbs[n] is not None]
    rest_p = {i: Vector(d['rest'][i][:3]) for i in idx}; rest_q = {i: _uq(d['rest'][i]) for i in idx}
    for pb in arm.pose.bones:
        pb.rotation_mode = 'QUATERNION'; pb.location = (0, 0, 0); pb.rotation_quaternion = (1, 0, 0, 0)

    def world_coords():
        bpy.context.view_layer.update()
        ev = ob.evaluated_get(bpy.context.evaluated_depsgraph_get())
        m = ev.to_mesh()
        co = np.empty(len(m.vertices) * 3); m.vertices.foreach_get('co', co)
        ev.to_mesh_clear()
        return (co.reshape(-1, 3) @ R.T + t).tolist()

    visible = visible_faces(polys, world_coords(), range(nf), dirs)
    log('reposo visibles', len(visible), 'de', nf)
    hidden = set(range(nf)) - visible
    total = 0
    for cname, clip in d['clips'].items():
        for fi_, fr in enumerate(clip['frames']):
            if not hidden:
                break
            set_pose(arm, names, pbs, idx, rest_p, rest_q, fr)
            newly = visible_faces(polys, world_coords(), sorted(hidden), dirs)
            hidden -= newly; visible |= newly; total += 1
        log(cname, 'ocultas restantes', len(hidden))
    for pb in arm.pose.bones:
        pb.location = (0, 0, 0); pb.rotation_quaternion = (1, 0, 0, 0)
    # proteccion: caras cuyos vertices van (en media) mas del 50% a cabeza/cuello
    vg = {g.index: g.name for g in ob.vertex_groups}
    prot = set()
    for p in me.polygons:
        w = 0.0
        for v in p.vertices:
            w += sum(g.weight for g in me.vertices[v].groups if vg.get(g.group) in PROTECT_BONES)
        if w / len(p.vertices) >= 0.5:
            prot.add(p.index)
    keep = visible | prot
    emap = {}
    for p in me.polygons:
        for k in p.edge_keys:
            emap.setdefault(k, []).append(p.index)
    for _ in range(ring):
        add = set()
        for p in me.polygons:
            if p.index in keep:
                for k in p.edge_keys:
                    add.update(emap[k])
        keep |= add
    log('poses usadas', total, 'visibles', len(visible), 'protegidas', len(prot - visible), 'conservadas', len(keep), 'de', nf)
    return sorted(keep)
