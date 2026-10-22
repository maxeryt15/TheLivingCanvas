"""Rig facial ligero para los NPCs de NPCs_Shell_Face.blend (copia de trabajo de NPCs_Shell_Test.blend).
- Huesos de ojo eye_L / eye_R (hijos de 'head', deform) con los vertices de cada globo ocular pesados 100% a su hueso.
- Hueso de apuntado eye_aim (NO deform -> no se exporta con use_armature_deform_only=True) + restricciones Damped Track con influencia 0 (solo autoria en Blender).
- Shape keys (blend shapes en Unity): blink, mouth_open, mouth_smile, mouth_frown, mouth_round, mouth_wide, brow_raise, brow_lower, brow_worry.
No toca el esqueleto de 53 huesos ni los pesos del cuerpo. Uso: exec(open(...).read()); build_face(p) para p en NPCS.
"""
import bpy, re, json
import numpy as np
from mathutils import Vector, Matrix

NPCS = ['Gar', 'Caf', 'Cou', 'Cur', 'Doc', 'Gen', 'Grd', 'Pnt', 'Stu', 'Tou', 'Rose']
EYER = re.compile(r'Eye(White|Iris|Pupil|Blind)|Iris2|^Eye_(White|Iris|Pupil)$')
SKINR = re.compile(r'skin|Lipstick|Mustache|Mole|Freckle|LipScar', re.I)
BROWR = re.compile(r'Brows', re.I)
KEYS = ['blink', 'mouth_open', 'mouth_smile', 'mouth_frown', 'mouth_round', 'mouth_wide', 'brow_raise', 'brow_lower', 'brow_worry']
MOUTH_DZ = 0.064      # distancia ojos -> boca medida en los 6 NPC con labial (0.062-0.065)


def _mats(m):
    return [s.material.name for s in m.material_slots]


def landmarks(m):
    me = m.data
    eye_idx = {i for i, n in enumerate(_mats(m)) if EYER.search(n)}
    isl = {}
    for f in me.polygons:
        if f.material_index in eye_idx:
            for v in f.vertices:
                isl[v] = None
    # componentes por conectividad de caras
    adj = {v: set() for v in isl}
    for f in me.polygons:
        if f.material_index in eye_idx:
            vs = list(f.vertices)
            for a in vs:
                adj[a].update(vs)
    side = {'L': set(), 'R': set()}
    for v in isl:
        side['L' if me.vertices[v].co.x > 0 else 'R'].add(v)
    out = {}
    for s, vs in side.items():
        co = np.array([me.vertices[v].co[:] for v in vs])
        c = (co.max(0) + co.min(0)) / 2
        out['eye_' + s] = dict(verts=sorted(vs), center=(float(c[0]), float(co.max(0)[1]), float(c[2])), front=float(co.min(0)[1]),
                               width=float(co.max(0)[0] - co.min(0)[0]), height=float(co.max(0)[2] - co.min(0)[2]))
    ez = (out['eye_L']['center'][2] + out['eye_R']['center'][2]) / 2
    ey = min(out['eye_L']['front'], out['eye_R']['front'])
    mz = ez - MOUTH_DZ
    ys = []
    for f in me.polygons:
        if SKINR.search(_mats(m)[f.material_index]) and not f.material_index in eye_idx:
            for v in f.vertices:
                c = me.vertices[v].co
                if abs(c.x) < 0.012 and mz - 0.012 < c.z < mz + 0.004:
                    ys.append(c.y)
    yf = min(ys) if ys else ey - 0.016        # superficie real del labio / cara en la boca
    out['mouth'] = dict(z=mz, y=yf + 0.014, y_front=yf, eye_z=ez)
    return out


def add_eye_bones(p, lm):
    rig = bpy.data.objects[p + '_Rig']
    bpy.context.view_layer.objects.active = rig
    bpy.ops.object.mode_set(mode='EDIT')
    eb = rig.data.edit_bones
    head = eb['head']
    for s in ('L', 'R'):
        n = 'eye_' + s
        if n in eb:
            eb.remove(eb[n])
        b = eb.new(n)
        c = Vector(lm[n]['center'])
        b.head = c
        b.tail = c + Vector((0, -0.02, 0))
        b.roll = 0
        b.parent = head
        b.use_connect = False
        b.use_deform = True
    if 'eye_aim' in eb:
        eb.remove(eb['eye_aim'])
    a = eb.new('eye_aim')
    ez = lm['mouth']['eye_z']
    ey = min(lm['eye_L']['front'], lm['eye_R']['front'])
    a.head = Vector((0, ey - 0.6, ez))
    a.tail = a.head + Vector((0, 0, 0.04))
    a.parent = eb['Root']
    a.use_deform = False
    bpy.ops.object.mode_set(mode='OBJECT')
    # restricciones de autoria (influencia 0 por defecto; Unity usa el LookAt de Humanoid, ver Docs)
    for s in ('L', 'R'):
        pb = rig.pose.bones['eye_' + s]
        for c in list(pb.constraints):
            pb.constraints.remove(c)
        t = pb.constraints.new('DAMPED_TRACK')
        t.target = rig
        t.subtarget = 'eye_aim'
        t.track_axis = 'TRACK_Y'
        t.influence = 0.0
        t.name = 'LookAt_eye_aim'
        pb.rotation_mode = 'XYZ'
        lr = pb.constraints.new('LIMIT_ROTATION')
        lr.use_limit_x = lr.use_limit_y = lr.use_limit_z = True
        lr.min_x, lr.max_x = np.radians(-18), np.radians(18)
        lr.min_z, lr.max_z = np.radians(-25), np.radians(25)
        lr.min_y = lr.max_y = 0
        lr.owner_space = 'LOCAL'
        lr.name = 'Limit_gaze'


def weight_eyes(p, lm):
    m = bpy.data.objects[p + '_Mesh']
    vgs = m.vertex_groups
    nm = {g.index: g.name for g in vgs}
    for s in ('L', 'R'):
        n = 'eye_' + s
        g = vgs.get(n) or vgs.new(name=n)
        vs = lm[n]['verts']
        for v in vs:
            for gr in list(m.data.vertices[v].groups):
                if nm[gr.group] != n:
                    vgs[nm[gr.group]].remove([v])
        g.add(vs, 1.0, 'REPLACE')
    return len(lm['eye_L']['verts']) + len(lm['eye_R']['verts'])


def _smooth(t):
    t = np.clip(t, 0, 1)
    return t * t * (3 - 2 * t)



CARD_MAT = 'NPC_MouthInside'


def add_mouth_card(m, lm):
    """Quad oscuro detras de los labios: se ve solo al abrir la boca. Pesado 100% a 'head'."""
    import bmesh
    me = m.data
    mat = bpy.data.materials.get(CARD_MAT)
    if mat is None:
        mat = bpy.data.materials.new(CARD_MAT)
        mat.use_nodes = True
        b = next(n for n in mat.node_tree.nodes if n.type == 'BSDF_PRINCIPLED')
        b.inputs['Base Color'].default_value = (0.11, 0.025, 0.03, 1.0)
        b.inputs['Roughness'].default_value = 0.9
    if CARD_MAT not in [s.material.name for s in m.material_slots if s.material]:
        m.data.materials.append(mat)
    mi = [s.material.name for s in m.material_slots].index(CARD_MAT)
    bm = bmesh.new(); bm.from_mesh(me)
    old = [f for f in bm.faces if f.material_index == mi]
    if old:
        bmesh.ops.delete(bm, geom=old, context='FACES')
    mz, my = lm['mouth']['z'], lm['mouth']['y']
    y = lm['mouth']['y_front'] + 0.013
    pts = [(-0.011, y, mz - 0.006), (0.011, y, mz - 0.006), (0.011, y, mz + 0.002), (-0.011, y, mz + 0.002)]
    vs = [bm.verts.new(p) for p in pts]
    f = bm.faces.new(vs)
    f.material_index = mi
    bm.normal_update()
    if f.normal.y > 0:
        f.normal_flip()
    bm.to_mesh(me); me.update(); bm.free()
    head = m.vertex_groups.get('head')
    new = [v.index for v in me.vertices if not [g for g in v.groups if g.weight > 0]]
    head.add(new, 1.0, 'REPLACE')
    return len(new)


def add_shape_keys(p, lm):
    m = bpy.data.objects[p + '_Mesh']
    me = m.data
    if me.shape_keys:
        # OJO: quitar Basis el primero hornea la siguiente key en la malla base (deriva acumulada). Se quitan en orden inverso, Basis al final.
        for k in list(me.shape_keys.key_blocks)[::-1]:
            m.shape_key_remove(k)
    add_mouth_card(m, lm)
    n = len(me.vertices)
    base = np.empty(n * 3)
    me.vertices.foreach_get('co', base)
    base = base.reshape(-1, 3)
    mats = _mats(m)
    skin_v = np.zeros(n, bool)
    brow_v = np.zeros(n, bool)
    eye_v = np.zeros(n, bool)
    for f in me.polygons:
        nmat = mats[f.material_index]
        for v in f.vertices:
            if SKINR.search(nmat):
                skin_v[v] = True
            if BROWR.search(nmat):
                brow_v[v] = True
            if EYER.search(nmat):
                eye_v[v] = True
    skin_v &= ~eye_v
    mz, my = lm['mouth']['z'], lm['mouth']['y']
    x, y, z = base[:, 0], base[:, 1], base[:, 2]
    front = y < my + 0.03                                  # solo la cara, no la nuca
    # --- boca: peso radial alrededor del centro de la boca
    r = np.sqrt((x / 0.042) ** 2 + ((z - mz) / 0.038) ** 2)
    fw = _smooth(1 - r) * skin_v * front
    lower = _smooth((mz + 0.004 - z) / 0.012)               # 1 por debajo del labio inferior, 0 en el labio superior
    corner = np.clip(np.abs(x) / 0.026, 0, 1.3)
    sgn = np.sign(x)
    D = {}
    gx = np.exp(-(x / 0.03) ** 2)                                     # solo el labio inferior baja; el menton casi no se mueve (evita abrir un hueco bajo la mandibula)
    gl = np.exp(-((z - (mz - 0.010)) / 0.011) ** 2) * gx * skin_v * front
    gu = np.exp(-((z - (mz + 0.008)) / 0.008) ** 2) * gx * skin_v * front
    d = np.zeros_like(base); d[:, 2] = -0.010 * gl + 0.002 * gu; d[:, 1] = 0.002 * gl; D['mouth_open'] = d
    d = np.zeros_like(base); d[:, 2] = 0.0234 * fw * corner ** 1.5; d[:, 0] = sgn * 0.0072 * fw * corner; d[:, 1] = 0.0036 * fw * corner; D['mouth_smile'] = d
    d = np.zeros_like(base); d[:, 2] = -0.0198 * fw * corner ** 1.5; d[:, 0] = -sgn * 0.0018 * fw * corner; D['mouth_frown'] = d
    d = np.zeros_like(base); d[:, 0] = -x * 0.38 * fw; d[:, 1] = -0.008 * fw; d[:, 2] = -0.003 * fw * lower; D['mouth_round'] = d
    d = np.zeros_like(base); d[:, 0] = x * 0.28 * fw; d[:, 2] = -0.004 * fw * lower; D['mouth_wide'] = d
    # --- parpado: la piel alrededor de cada ojo se comprime hacia la linea central y sale por delante de la cupula
    d = np.zeros_like(base)
    for s in ('eye_L', 'eye_R'):
        cx, cy, cz = lm[s]['center']
        front_y = lm[s]['front']
        rr = np.sqrt(((x - cx) / 0.027) ** 2 + ((z - cz) / 0.024) ** 2)
        w = _smooth(1.15 - rr) * skin_v * (y < cy + 0.02)
        d[:, 2] += (cz - z) * 0.92 * w
        d[:, 1] += (front_y - 0.002 - y) * w * (rr < 1.15)
    for s in ('eye_L', 'eye_R'):
        cx, cy, cz = lm[s]['center']
        vs = np.array(lm[s]['verts'])
        d[vs, 2] += (cz - z[vs]) * 0.85      # el globo se aplasta: solo queda una rendija
        d[vs, 1] += 0.004
    D['blink'] = d
    # --- cejas
    bx = x; bz = z
    d = np.zeros_like(base); d[:, 2] = 0.009 * brow_v; D['brow_raise'] = d
    d = np.zeros_like(base); d[:, 2] = -0.007 * brow_v; d[:, 1] = -0.001 * brow_v; D['brow_lower'] = d
    inner = _smooth(1 - np.abs(np.abs(x) - 0.012) / 0.02)
    d = np.zeros_like(base); d[:, 2] = (0.009 * inner - 0.004 * (1 - inner)) * brow_v; D['brow_worry'] = d
    m.shape_key_add(name='Basis', from_mix=False)
    for k in KEYS:
        kb = m.shape_key_add(name=k, from_mix=False)
        co = (base + D[k]).ravel()
        kb.data.foreach_set('co', co)
        kb.slider_min, kb.slider_max, kb.value = 0.0, 1.0, 0.0
    return {k: int((np.abs(D[k]).sum(1) > 1e-6).sum()) for k in KEYS}


def build_face(p):
    m = bpy.data.objects[p + '_Mesh']
    lm = landmarks(m)
    add_eye_bones(p, lm)
    ne = weight_eyes(p, lm)
    sk = add_shape_keys(p, lm)
    return dict(npc=p, eye_verts=ne, mouth=lm['mouth'], keys=sk)


def mouth_open_displacement(m, lm):
    """mouth_open v2: separa labio superior e inferior por la linea de la boca (z_s). El inferior baja ~1.2 cm y el superior sube ~2 mm."""
    me = m.data
    n = len(me.vertices)
    base = np.empty(n * 3); me.shape_keys.key_blocks['Basis'].data.foreach_get('co', base); base = base.reshape(-1, 3)
    mats = _mats(m)
    skin_v = np.zeros(n, bool); eye_v = np.zeros(n, bool); lip_v = np.zeros(n, bool)
    for f in me.polygons:
        nm_ = mats[f.material_index]
        for v in f.vertices:
            if SKINR.search(nm_): skin_v[v] = True
            if EYER.search(nm_): eye_v[v] = True
            if 'Lipstick' in nm_: lip_v[v] = True
    skin_v &= ~eye_v
    mz, yf = lm['mouth']['z'], lm['mouth']['y_front']
    x, y, z = base[:, 0], base[:, 1], base[:, 2]
    front = y < yf + 0.045
    zs = mz + 0.003
    gx = np.exp(-(x / 0.030) ** 2)
    low = _smooth((zs - z) / 0.004)
    below = np.where(z >= mz - 0.012, 1.0, np.exp(-((mz - 0.012 - z) / 0.014) ** 2))
    up = _smooth((z - zs) / 0.004) * np.exp(-np.clip((z - (mz + 0.012)) / 0.010, 0, None) ** 2)
    g = gx * skin_v * front
    d = np.zeros_like(base)
    d[:, 2] = -0.012 * low * below * g + 0.002 * up * g
    d[:, 1] = 0.0035 * low * below * g
    return d


def set_mouth_open_v2(p):
    m = bpy.data.objects[p + '_Mesh']
    lm = landmarks(m)
    kb = m.data.shape_keys.key_blocks
    d = mouth_open_displacement(m, lm)
    base = np.empty(len(m.data.vertices) * 3); kb['Basis'].data.foreach_get('co', base)
    kb['mouth_open'].data.foreach_set('co', (base.reshape(-1, 3) + d).ravel())
    # la tarjeta oscura se adelanta SOLO en la key mouth_open, a la altura de la comisura, para formar la ranura de la boca
    mz = lm['mouth']['z']
    zs = mz + 0.003
    mi = [sl.material.name for sl in m.material_slots].index(CARD_MAT)
    cv = sorted({v for f in m.data.polygons if f.material_index == mi for v in f.vertices})
    B = base.reshape(-1, 3)
    # 1) posicion de reposo de la tarjeta (igual que add_mouth_card), en TODAS las keys: idempotente
    yc = lm['mouth']['y_front'] + 0.013
    rest = [(-0.017, yc, mz - 0.014), (0.017, yc, mz - 0.014), (-0.017, yc, mz + 0.002), (0.017, yc, mz + 0.002)]
    order = sorted(cv, key=lambda v: (v,))
    # ordenar por la posicion que tenia al crearse: abajo-izq, abajo-der, arriba-der, arriba-izq (bm.faces.new con pts originales)
    pts0 = [(-0.017, mz - 0.014), (0.017, mz - 0.014), (0.017, mz + 0.002), (-0.017, mz + 0.002)]
    idx = {}
    for v in cv:
        idx[v] = len(idx)
    cvs = cv[:]    # los 4 vertices se crearon en el orden de pts0
    ys = lm['mouth']['y_front'] - 0.0015
    yb = lm['mouth']['y_front'] + 0.003     # el borde inferior sigue al labio inferior que retrocede
    openpos = [(-0.011, yb, zs - 0.011), (0.011, yb, zs - 0.011), (0.0135, ys, zs + 0.0005), (-0.0135, ys, zs + 0.0005)]
    restpos = [(-0.011, yc, mz - 0.006), (0.011, yc, mz - 0.006), (0.011, yc, mz + 0.002), (-0.011, yc, mz + 0.002)]
    for v, rp, op in zip(cvs, restpos, openpos):
        m.data.vertices[v].co = rp
        for k in kb:
            k.data[v].co = rp
        kb['mouth_open'].data[v].co = op
    return d
