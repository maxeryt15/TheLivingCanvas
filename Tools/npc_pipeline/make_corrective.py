"""Crea UNA corrective shape key en la malla de un NPC para una pose problematica, con driver por rotacion de hueso.
No toca armature, pesos ni acciones. Trabajar SIEMPRE sobre la copia de trabajo (CORRECTIVES_WORK.blend).
Metodo: pose extrema -> vertices de prenda que cruzan la piel (B) o que dejan salir piel (A) -> desplazamiento minimo en espacio de pose
(holgura CLEAR) -> se extiende 3 anillos con caida 0.6 -> se pasa a espacio de reposo con la inversa de la matriz de skinning por vertice
(los shape keys se aplican ANTES del skinning) -> shape key relativa a Basis. Driver: TRANSFORMS (rotacion local de un hueso), 0..1 suave.
Uso: blender -b WORK.blend --python make_corrective.py -- Pref Pose NombreKey HuesoDriver [inicio_fraccion=0.35]
"""
import bpy, sys, math
sys.path.insert(0, r'D:\TheLivingCanvas\Tools\npc_pipeline')
import pose_lib as PL
import penetration_sweep as PS
import corrective_battery as CB
from mathutils import Vector, Matrix
from mathutils.bvhtree import BVHTree

CLEAR = 0.003
RINGS, FALL = 3, 0.6
MAXD = 0.06
RAMP_END = 0.6   # el driver llega a 1 al 60 % del angulo de la pose extrema (el cruce empieza antes que la pose extrema)
WORK = r'D:\TheLivingCanvas\ArtSource\NPC\NPCs_Shell_Face_CORRECTIVES_WORK.blend'
O = bpy.data.objects
SPECS = {}   # nombre de key -> parametros del driver (los ShapeKey no admiten propiedades personalizadas)


def skin_matrices(arm, ob):
    return {n: (arm.pose.bones[n].matrix @ arm.data.bones[n].matrix_local.inverted()).to_3x3() for n in arm.data.bones.keys() if n in ob.vertex_groups}


def offenders(pref, ob, arm, c, co_posed, cloth_polys, skin_polys):
    """Desplazamientos minimos (espacio de pose) para que la prenda no cruce la piel: B = prenda dentro de la piel, A = piel fuera de prenda."""
    disp = {}
    def put(v, vec):
        if v not in disp or vec.length > disp[v].length: disp[v] = vec
    bs = BVHTree.FromPolygons(co_posed, skin_polys); bc = BVHTree.FromPolygons(co_posed, cloth_polys)
    nB = nA = 0
    for v in c['trackedB2']:
        loc, nor, idx, dist = bs.find_nearest(co_posed[v])
        if loc is None or dist > 0.03: continue
        d = (co_posed[v] - loc).dot(nor)
        target = min(CLEAR, c['restB'][v])   # un labio que en reposo esta 2 mm bajo la piel no debe quedar mas hondo que en reposo
        if d < target - 0.0005: put(v, nor * (target - d)); nB += 1
    for v in c['covered']:
        loc, nor, idx, dist = bc.find_nearest(co_posed[v])
        if loc is None or dist > PS.COVER_MAX_DIST: continue
        d = (co_posed[v] - loc).dot(nor)
        if d > 0.001:
            for u in cloth_polys[idx]: put(u, nor * (d + CLEAR))
            nA += 1
    return disp, nB, nA


STRETCH_HI, STRETCH_LO = 1.5, 0.5   # aristas de prenda fuera de este rango (pose/reposo) se consideran estiradas/aplastadas
RELAX_ITERS, RELAX_K = 40, 0.5


def relax(co, base_co, edges, adj, zcut=None):
    """Relajacion tipo PBD de las aristas estiradas/aplastadas (dientes de manga): mueve solo los vertices de la region (aristas malas + 1 anillo),
    el resto queda fijo. Devuelve {vertice: desplazamiento en espacio de pose}."""
    L0 = {e: (base_co[e[0]] - base_co[e[1]]).length for e in edges}
    bad = [e for e in edges if L0[e] > 0.003 and not (STRETCH_LO <= (co[e[0]] - co[e[1]]).length / L0[e] <= STRETCH_HI)]
    R = {v for e in bad for v in e}
    R |= {u for v in list(R) for u in adj.get(v, ())}
    if zcut is not None: R = {v for v in R if base_co[v].z < zcut}   # cuello/hombro por encima de la articulacion no se relaja (no se mueve el escote)
    if not bad or not R: return {}, 0
    p = {v: co[v].copy() for v in R}
    work = [e for e in edges if (e[0] in R or e[1] in R) and L0[e] > 0.0015]
    for _ in range(RELAX_ITERS):
        for e in work:
            a, b = e
            pa = p.get(a, co[a]); pb = p.get(b, co[b])
            d = pb - pa; L = d.length
            if L < 1e-9: continue
            corr = d * ((L - L0[e]) / L) * RELAX_K
            fa, fb = a in p, b in p
            if fa and fb: p[a] = pa + corr * 0.5; p[b] = pb - corr * 0.5
            elif fa: p[a] = pa + corr
            elif fb: p[b] = pb - corr
    return {v: p[v] - co[v] for v in R if (p[v] - co[v]).length > 1e-5}, len(bad)


def spread(disp, adj):
    cur = dict(disp)
    for r in range(RINGS):
        nxt = {}
        for v, vec in cur.items():
            for u in adj.get(v, ()):
                if u not in disp and (u not in nxt or vec.length * FALL > nxt[u].length): nxt[u] = vec * FALL
        for u, vec in nxt.items(): disp[u] = vec
        cur = nxt
    return disp


def to_rest(ob, arm, disp):
    Rb = skin_matrices(arm, ob); vg = ob.vertex_groups; out = {}
    for v, vec in disp.items():
        Bm = Matrix(((0, 0, 0), (0, 0, 0), (0, 0, 0)))
        for g in ob.data.vertices[v].groups:
            n = vg[g.group].name
            if n in Rb: Bm += Rb[n] * g.weight
        try: out[v] = Bm.inverted() @ vec
        except ValueError: out[v] = vec
    return out


def build_level(pref, pose, name, frac, passes=6, do_relax=False, zcut=None):
    """Crea una shape key (valor 0, sin driver) corregida para la pose a `frac` de su angulo. Devuelve (key, n_vertices)."""
    arm, ob = O[pref + '_Rig'], O[pref + '_Mesh']; me = ob.data
    sk = me.shape_keys
    cal = PL.calibrate(arm); c = CB.prepare(pref); steps = cal[pose]
    skin_polys = [tuple(me.polygons[i].vertices) for i in c['skin_f']]
    cloth_polys = [tuple(me.polygons[i].vertices) for i in c['cloth_f']]
    adj = {}
    for p in cloth_polys:
        for k in range(len(p)):
            a_, b_ = p[k], p[(k + 1) % len(p)]
            adj.setdefault(a_, set()).add(b_); adj.setdefault(b_, set()).add(a_)
    def posed_co():
        ev = ob.evaluated_get(bpy.context.evaluated_depsgraph_get()); m = ev.to_mesh()
        co = [v.co.copy() for v in m.vertices]; ev.to_mesh_clear(); return co
    basis = sk.key_blocks[0]
    key = ob.shape_key_add(name=name, from_mix=False); key.relative_key = basis; key.value = 1.0
    edges = sorted({tuple(sorted((p[k], p[(k + 1) % len(p)]))) for p in cloth_polys for k in range(len(p))})
    base_co = [basis.data[i].co.copy() for i in range(len(me.vertices))]
    acc = {}
    for ps_ in range(passes):
        PL.apply(arm, steps, frac)
        co = posed_co()
        rdisp, nbad = (relax(co, base_co, edges, adj, zcut) if (do_relax and ps_ < passes // 2) else ({}, 0))
        co2 = [co[i] + rdisp[i] if i in rdisp else co[i] for i in range(len(co))]
        disp, nB, nA = offenders(pref, ob, arm, c, co2, cloth_polys, skin_polys)
        disp = spread(disp, adj)
        for v, vec in rdisp.items(): disp[v] = disp.get(v, Vector()) + vec
        print(f'  {name} pasada {ps_ + 1}: ofensores B={nB} A={nA}, aristas estiradas={nbad}', flush=True)
        if not disp: break
        rest = to_rest(ob, arm, disp)
        for v, dv in rest.items():
            acc[v] = acc.get(v, Vector()) + dv
            if acc[v].length > MAXD: acc[v] = acc[v].normalized() * MAXD
            key.data[v].co = basis.data[v].co + acc[v]
    key.value = 0.0
    PL.reset(arm)
    print(f'{pref}: key {name} (pose al {frac*100:.0f} %): {len(acc)} vertices, mov. max {max([d.length for d in acc.values()] + [0])*1000:.1f} mm')
    return key, len(acc)


def hat_driver(ob, arm, key, bone, ax, sg, full_rad, c, lo, hi, last=False):
    """Driver triangular: 0 en lo, 1 en c, 0 en hi (si last: 1 desde c en adelante). Posiciones en fraccion del angulo total (full_rad)."""
    sk = ob.data.shape_keys
    if sk.animation_data:
        for fc in list(sk.animation_data.drivers):
            if fc.data_path == f'key_blocks["{key.name}"].value': sk.driver_remove(fc.data_path)
    fc = key.driver_add('value'); d = fc.driver; d.type = 'SCRIPTED'
    var = d.variables.new(); var.name = 'r'; var.type = 'TRANSFORMS'
    t = var.targets[0]; t.id = arm; t.bone_target = bone
    t.transform_type = 'ROT_' + 'XYZ'[ax]; t.transform_space = 'LOCAL_SPACE'; t.rotation_mode = 'AUTO'
    ph = f'({sg}*r/{full_rad:.5f})'                  # fraccion del angulo total
    up = f'({ph}-{lo:.4f})/{c - lo:.4f}'
    down = f'({hi:.4f}-{ph})/{hi - c:.4f}'
    d.expression = f'max(0,min(1,{up}))' if last else f'max(0,min(1,{up},{down}))'
    import json as _j
    SPECS[key.name] = dict(bone=bone, ax=ax, sg=sg, full_rad=full_rad, c=c, lo=lo, hi=hi, last=last)


def build(pref, pose, name, bone, levels=(0.2, 0.4, 0.6, 0.8, 1.0), do_relax=False):
    arm, ob = O[pref + '_Rig'], O[pref + '_Mesh']; me = ob.data
    R = (arm.matrix_world.inverted() @ ob.matrix_world).to_3x3()
    assert all(abs(x) < 1e-6 for r in (R - Matrix.Identity(3)) for x in r), 'malla y armature con rotacion distinta'
    sk = me.shape_keys
    for kb in list(sk.key_blocks):
        if kb.name.startswith(name): ob.shape_key_remove(kb)
    for kb in sk.key_blocks: kb.value = 0
    cal = PL.calibrate(arm)
    bone_step = [st for st in cal[pose] if st[0] == bone]
    assert bone_step, f'{bone} no participa en {pose}'
    _, ax, sg, deg = bone_step[0]
    full = math.radians(deg)
    info = []
    for i, f in enumerate(levels):
        key, n = build_level(pref, pose, f'{name}_{int(round(f * 100))}', f, do_relax=do_relax, zcut=(arm.data.bones[bone].head_local.z if bone.startswith('upperarm') else None))
        lo = levels[i - 1] if i > 0 else max(0.0, f - (levels[1] - levels[0]))
        hi = levels[i + 1] if i + 1 < len(levels) else f
        hat_driver(ob, arm, key, bone, ax, sg, full, f, lo, hi, last=(i == len(levels) - 1))
        info.append(dict(key=key.name, level_deg=round(deg * f, 1), verts=n))
        print(f'{pref}: driver {key.name}: {bone} rot {"XYZ"[ax]} signo {sg:+d}, pico a {deg * f:.0f} deg (0 en {deg * lo:.0f}{"" if i + 1 == len(levels) else f", 0 en {deg * hi:.0f}"})')
    return dict(pref=pref, pose=pose, bone=bone, axis='XYZ'[ax], sign=sg, full_deg=deg, keys=info)


if __name__ == '__main__':
    a = sys.argv[sys.argv.index('--') + 1:]
    info = build(a[0], a[1], a[2], a[3], do_relax=('relax' in a[4:]))
    bpy.ops.wm.save_as_mainfile(filepath=WORK)
    print('CORRECTIVEDONE', info)
