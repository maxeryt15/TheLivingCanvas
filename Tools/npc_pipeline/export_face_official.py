"""Exportador OFICIAL de NPCs: lee EXCLUSIVAMENTE ArtSource/NPC/NPCs_Shell_Face.blend y escribe SOLO en staging
(ArtSource/_Exports/FaceOfficial/<Folder>/). Nunca escribe en Assets/ ni guarda el .blend.

Uso (Blender en segundo plano, con Face abierto):
  blender -b ArtSource/NPC/NPCs_Shell_Face.blend --python Tools/npc_pipeline/export_face_official.py -- --npcs Gen,Stu
  ... -- --npcs Gen --check-only        (solo guardas, no exporta)
  ... -- --npcs all --confirm-all        (los 11; exige confirmacion explicita)
  ... -- --npcs Gen --out <carpeta>      (carpeta alternativa; nunca dentro de Assets)

Por NPC genera: <Fbx>.fbx (+ .fbm de Blender), materials.json (mismo esquema que export_shell11.py), manifest.json (hashes, huesos,
malla, shape keys, pesos, materiales, estado de pose) y Textures/T_<p>_<g>.png (copias de Painted_Textures/*_VG2.png, solo para la promocion).

Pose: Face guarda los rigs en una pose NO neutra. Antes de exportar se captura el estado completo de cada rig, se lleva al reposo con
pose_lib.reset (el mismo mecanismo que export_gen_test.py; pose_lib.calibrate NO hace falta: solo resuelve ejes para la bateria de poses),
se VERIFICA el reposo (huesos identidad, correctivas a 0, malla evaluada == malla base), se exporta y se restaura el estado exacto
(tambien verificado). Si no se puede garantizar el reposo o la restauracion se ABORTA. Este script no guarda nunca el .blend."""
import bpy, os, sys, json, hashlib, time, shutil, math, re
import numpy as np

SCRIPT_VERSION = '1.0'
ROOT = r'D:\TheLivingCanvas'
SRC_DIR = os.path.join(ROOT, 'ArtSource', 'NPC')
SRC_NAME = 'NPCs_Shell_Face.blend'
DEFAULT_OUT = os.path.join(ROOT, 'ArtSource', '_Exports', 'FaceOfficial')
PAINT_DIR = os.path.join(SRC_DIR, 'Painted_Textures')
sys.path.insert(0, os.path.join(ROOT, 'Tools', 'npc_pipeline'))
import pose_lib as PL

# prefijo -> (carpeta de Unity / Painted_Textures, nombre del FBX). Los nombres de FBX son los de produccion.
NPCS = {'Cur': ('Curator', 'Curator'), 'Grd': ('Guard', 'Guard'), 'Stu': ('Student', 'Student'), 'Gar': ('Gardener', 'Gardener'),
        'Caf': ('Cafe', 'Cafe'), 'Tou': ('Tourist', 'Tourist'), 'Gen': ('Gentleman', 'Gentleman'), 'Cou': ('Courier', 'Courier'),
        'Doc': ('Docent', 'Docent'), 'Pnt': ('Painter', 'Painter'), 'Rose': ('Rose', 'Rose_Receptionist')}
FACE_KEYS = ['blink', 'mouth_open', 'mouth_smile', 'mouth_frown', 'mouth_round', 'mouth_wide', 'brow_raise', 'brow_lower', 'brow_worry']
EYE_BONES = ['eye_L', 'eye_R', 'eye_aim']
N_BONES, N_DEFORM = 56, 55
MOUTH_MAT = 'NPC_MouthInside'
# Ajustes FBX: IDENTICOS a export_shell11.py / export_gen_test.py (los que produjeron el Gentleman validado).
FBX_ARGS = dict(use_selection=True, object_types={'ARMATURE', 'MESH'}, use_mesh_modifiers=True, mesh_smooth_type='FACE', add_leaf_bones=False,
                bake_anim=False, axis_forward='-Z', axis_up='Y', apply_unit_scale=True, apply_scale_options='FBX_SCALE_UNITS',
                use_armature_deform_only=True, primary_bone_axis='Y', secondary_bone_axis='X', path_mode='COPY', embed_textures=False,
                colors_type='LINEAR')
O = bpy.data.objects


class Abort(Exception):
    pass


def sha256(path):
    h = hashlib.sha256()
    with open(path, 'rb') as f:
        for ch in iter(lambda: f.read(1 << 20), b''):
            h.update(ch)
    return h.hexdigest()


def log(*a):
    print('FO', *a, flush=True)


# ---------------------------------------------------------------- argumentos y guarda de fuente
def parse_args():
    a = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else []
    opt = dict(npcs=None, out=DEFAULT_OUT, check_only=False, confirm_all=False)
    i = 0
    while i < len(a):
        if a[i] == '--npcs': opt['npcs'] = a[i + 1]; i += 2
        elif a[i] == '--out': opt['out'] = a[i + 1]; i += 2
        elif a[i] == '--work-copy': opt['work_copy'] = True; i += 1   # permite NPCs_Shell_Face_<TAG>_WORK.blend (copia de trabajo de Face) como fuente; queda anotado en el manifest
        elif a[i] == '--check-only': opt['check_only'] = True; i += 1
        elif a[i] == '--confirm-all': opt['confirm_all'] = True; i += 1
        else: raise Abort('argumento desconocido: ' + a[i])
    if not opt['npcs']:
        raise Abort('falta --npcs (p. ej. Gen,Stu o all --confirm-all)')
    if opt['npcs'].lower() == 'all':
        if not opt['confirm_all']:
            raise Abort('--npcs all exige --confirm-all')
        sel = list(NPCS)
    else:
        sel = [s.strip() for s in opt['npcs'].split(',') if s.strip()]
        for s in sel:
            if s not in NPCS: raise Abort('NPC desconocido: %s (validos: %s)' % (s, ', '.join(NPCS)))
    opt['sel'] = sel
    out = os.path.normcase(os.path.abspath(opt['out']))
    parts = out.replace('\\', '/').split('/')
    if 'assets' in parts:
        raise Abort('el destino no puede estar dentro de Assets: ' + out)
    opt['out'] = os.path.abspath(opt['out'])
    return opt


def check_source(work_copy=False):
    fp = bpy.data.filepath
    if not fp: raise Abort('el .blend no tiene ruta (no esta guardado)')
    base = os.path.basename(fp)
    ok_name = base.lower() == SRC_NAME.lower() or (work_copy and re.fullmatch(r'NPCs_Shell_Face_[A-Za-z0-9]+_WORK\.blend', base) is not None)
    if not ok_name or os.path.normcase(os.path.dirname(os.path.abspath(fp))) != os.path.normcase(SRC_DIR):
        raise Abort('fuente incorrecta: %s (se exige exactamente %s)' % (fp, os.path.join(SRC_DIR, SRC_NAME)))
    if 'test' in base.lower():
        raise Abort('NPCs_Shell_Test.blend no es una fuente valida')
    return fp


# ---------------------------------------------------------------- guardas de estructura, geometria y materiales
def check_structure(p, folder):
    info = {}
    arm = O.get(p + '_Rig'); mesh = O.get(p + '_Mesh')
    if arm is None or arm.type != 'ARMATURE': raise Abort('%s: falta el armature %s_Rig' % (p, p))
    if mesh is None or mesh.type != 'MESH': raise Abort('%s: falta el mesh %s_Mesh' % (p, p))
    if mesh.parent is not arm: raise Abort('%s: %s_Mesh no es hijo de %s_Rig' % (p, p, p))
    bones = arm.data.bones
    nb = len(bones); nd = sum(1 for b in bones if b.use_deform)
    if nb != N_BONES or nd != N_DEFORM: raise Abort('%s: huesos %d/%d deform (se esperan %d/%d)' % (p, nb, nd, N_BONES, N_DEFORM))
    for e in EYE_BONES:
        if e not in bones: raise Abort('%s: falta el hueso %s' % (p, e))
    if bones['eye_aim'].use_deform or not bones['eye_L'].use_deform or not bones['eye_R'].use_deform:
        raise Abort('%s: flags deform de los ojos inesperados' % p)
    roots = [b.name for b in bones if b.parent is None]
    if roots != ['Root']: raise Abort('%s: raices de hueso inesperadas %s' % (p, roots))
    game = [o for o in arm.children if o.type == 'MESH' and o.visible_get() and not o.name.endswith('_Base')]
    if [o.name for o in game] != [p + '_Mesh']: raise Abort('%s: meshes exportables inesperados %s' % (p, [o.name for o in game]))
    mods = [(m.type, m.object.name if getattr(m, 'object', None) else None) for m in mesh.modifiers]
    if mods != [('ARMATURE', p + '_Rig')]: raise Abort('%s: modificadores inesperados %s' % (p, mods))
    if not mesh.modifiers[0].use_vertex_groups: raise Abort('%s: el modificador Armature no usa vertex groups' % p)
    # shape keys
    sk = mesh.data.shape_keys
    if sk is None or not sk.key_blocks or sk.key_blocks[0].name != 'Basis': raise Abort('%s: sin shape keys / Basis' % p)
    names = [k.name for k in sk.key_blocks]
    missing = [k for k in FACE_KEYS if k not in names]
    if missing: raise Abort('%s: faltan shape keys faciales %s' % (p, missing))
    correctives = [n for n in names[1:] if n not in FACE_KEYS]
    info.update(bones=nb, deform=nd, shape_keys=names, face_keys=len(FACE_KEYS), correctives=correctives,
                drivers=len(sk.animation_data.drivers) if sk.animation_data else 0)
    return arm, mesh, info


def check_geometry(p, mesh, arm, info):
    me = mesh.data
    nv = len(me.vertices); npoly = len(me.polygons)
    co = np.empty(nv * 3, dtype=np.float64); me.vertices.foreach_get('co', co)
    if not np.isfinite(co).all(): raise Abort('%s: vertices NaN/Inf' % p)
    for k in me.shape_keys.key_blocks:
        a = np.empty(nv * 3, dtype=np.float64); k.data.foreach_get('co', a)
        if not np.isfinite(a).all(): raise Abort('%s: shape key %s con NaN/Inf' % (p, k.name))
    sizes = np.array([len(poly.vertices) for poly in me.polygons])
    if (sizes > 4).any(): raise Abort('%s: %d ngons (>4 vertices); Face debe estar triangulado/quads' % (p, int((sizes > 4).sum())))
    if (sizes < 3).any(): raise Abort('%s: poligonos degenerados (<3 vertices)' % p)
    bad = 0
    for poly in me.polygons:
        vs = poly.vertices
        if len(set(vs)) != len(vs) or poly.area < 1e-12: bad += 1
    if bad: raise Abort('%s: %d poligonos con vertices repetidos o area cero' % (p, bad))
    if not me.uv_layers or me.uv_layers.active is None: raise Abort('%s: sin UVs' % p)
    uvn = []
    for u in me.uv_layers:
        a = np.empty(len(me.loops) * 2); u.data.foreach_get('uv', a)
        if not np.isfinite(a).all(): raise Abort('%s: UV %s con NaN/Inf' % (p, u.name))
        uvn.append(u.name)
    if not me.color_attributes: raise Abort('%s: sin vertex colors' % p)
    dn = {b.name for b in arm.data.bones if b.use_deform}
    badvg = [g.name for g in mesh.vertex_groups if g.name not in dn]
    if badvg: raise Abort('%s: vertex groups que no son huesos deform: %s' % (p, badvg))
    maxinf = 0; minsum = 9.0; maxsum = 0.0; nlow = 0
    for v in me.vertices:
        ws = [g.weight for g in v.groups if g.weight > 1e-6]
        if not ws: raise Abort('%s: vertice %d sin pesos validos' % (p, v.index))
        if len(ws) > 4: raise Abort('%s: vertice %d con %d influencias (>4)' % (p, v.index, len(ws)))
        s = sum(ws); maxinf = max(maxinf, len(ws)); minsum = min(minsum, s); maxsum = max(maxsum, s)
        if s < 0.999: nlow += 1
    if minsum < 0.9 or maxsum > 1.0001: raise Abort('%s: suma de pesos fuera de rango [%.4f, %.4f]' % (p, minsum, maxsum))
    tris = int(sum(1 if s == 3 else 2 for s in sizes))
    info.update(verts=nv, polys=npoly, tris=tris, uv_layers=uvn, color_attrs=[a.name for a in me.color_attributes], vgroups=len(mesh.vertex_groups),
                max_influences=maxinf, weight_sum_min=round(minsum, 5), weight_sum_max=round(maxsum, 5), verts_weight_sum_below_0999=nlow)


def check_materials(p, folder, mesh, info):
    mats = list(mesh.data.materials)
    if not mats or any(m is None for m in mats): raise Abort('%s: slots de material vacios' % p)
    names = [m.name for m in mats]
    if len(set(names)) != len(names): raise Abort('%s: materiales duplicados en slots' % p)
    if MOUTH_MAT not in names: raise Abort('%s: falta el material %s' % (p, MOUTH_MAT))
    paint = [p + '_skin_Paint', p + '_hair_Paint', p + '_clothes_Paint']
    tex = {}
    if p != 'Rose':
        for pm in paint:
            if pm not in names: raise Abort('%s: falta el material pintado %s' % (p, pm))
            m = bpy.data.materials[pm]
            if not any(n.type == 'TEX_IMAGE' and n.image for n in m.node_tree.nodes): raise Abort('%s: %s sin imagen' % (p, pm))
        for g in ('skin', 'hair', 'clothes'):
            f = os.path.join(PAINT_DIR, folder, 'T_%s_%s_VG2.png' % (p, g))
            if not os.path.isfile(f): raise Abort('%s: falta la textura fuente %s' % (p, f))
            tex[g] = f
    info.update(materials=names, paint_materials=paint if p != 'Rose' else [], texture_sources=tex)


# ---------------------------------------------------------------- estado del rig: captura, reposo, verificacion, restauracion
def capture(arm, mesh):
    s = dict(loc=tuple(arm.location), rot=tuple(arm.rotation_euler), scale=tuple(arm.scale), action=arm.animation_data.action if arm.animation_data else None,
             has_ad=arm.animation_data is not None, pose_position=arm.data.pose_position, frame=bpy.context.scene.frame_current,
             sel=[o.name for o in bpy.context.view_layer.objects if o.select_get()], active=bpy.context.view_layer.objects.active.name if bpy.context.view_layer.objects.active else None)
    s['bones'] = {pb.name: (pb.rotation_mode, tuple(pb.rotation_quaternion), tuple(pb.rotation_euler), tuple(pb.rotation_axis_angle), tuple(pb.location),
                            tuple(pb.scale), tuple(c.influence for c in pb.constraints)) for pb in arm.pose.bones}
    s['keys'] = {k.name: (k.value, k.mute, k.slider_min, k.slider_max) for k in mesh.data.shape_keys.key_blocks}
    return s


def restore(arm, mesh, s):
    arm.location = s['loc']; arm.rotation_euler = s['rot']; arm.scale = s['scale']
    if s['has_ad']:
        arm.animation_data.action = s['action']
    for pb in arm.pose.bones:
        mode, q, e, aa, loc, sc, infl = s['bones'][pb.name]
        pb.rotation_mode = mode; pb.rotation_quaternion = q; pb.rotation_euler = e; pb.rotation_axis_angle = aa; pb.location = loc; pb.scale = sc
    for o in bpy.context.view_layer.objects: o.select_set(False)
    for n in s['sel']:
        if n in O: O[n].select_set(True)
    bpy.context.view_layer.objects.active = O[s['active']] if s['active'] else None
    bpy.context.view_layer.update(); bpy.context.evaluated_depsgraph_get()


def state_equal(arm, mesh, s):
    t = capture(arm, mesh)
    for k in ('loc', 'rot', 'scale', 'pose_position', 'frame', 'sel', 'active', 'has_ad'):
        if t[k] != s[k]: return 'diferente: ' + k
    if t['action'] is not s['action']: return 'diferente: action'
    for n, v in s['bones'].items():
        if t['bones'][n] != v: return 'hueso distinto: ' + n
    for n, v in s['keys'].items():
        if abs(t['keys'][n][0] - v[0]) > 1e-9 or t['keys'][n][1:] != v[1:]: return 'shape key distinta: ' + n
    return None


def verify_rest(p, arm, mesh):
    PLmax = 0.0
    for pb in arm.pose.bones:
        if pb.rotation_mode != 'QUATERNION': raise Abort('%s: %s no esta en QUATERNION tras reset' % (p, pb.name))
        PLmax = max(PLmax, abs(pb.rotation_quaternion.w - 1), abs(pb.rotation_quaternion.x), abs(pb.rotation_quaternion.y), abs(pb.rotation_quaternion.z),
                    pb.location.length, abs(pb.scale.x - 1), abs(pb.scale.y - 1), abs(pb.scale.z - 1))
    if PLmax > 1e-9: raise Abort('%s: el rig no esta en reposo (desviacion %.3g)' % (p, PLmax))
    if arm.animation_data and arm.animation_data.action: raise Abort('%s: sigue asignada una accion' % p)
    if arm.data.pose_position != 'POSE': raise Abort('%s: pose_position=%s' % (p, arm.data.pose_position))
    dg = bpy.context.evaluated_depsgraph_get(); dg.update()
    nz = {k.name: k.value for k in mesh.data.shape_keys.key_blocks[1:] if abs(k.value) > 1e-6}
    if nz: raise Abort('%s: shape keys con valor != 0 en reposo (se hornearian): %s' % (p, nz))
    ev = mesh.evaluated_get(dg); em = ev.to_mesh()
    a = np.empty(len(em.vertices) * 3); em.vertices.foreach_get('co', a)
    b = np.empty(len(mesh.data.vertices) * 3); mesh.data.vertices.foreach_get('co', b)
    ev.to_mesh_clear()
    if a.shape != b.shape: raise Abort('%s: la malla evaluada cambia de tamano' % p)
    d = float(np.abs(a - b).max())
    if d > 1e-4: raise Abort('%s: malla evaluada != malla base en reposo (%.6f m)' % (p, d))
    return dict(bone_deviation=PLmax, shape_keys_nonzero=0, eval_vs_base_max_m=d)


# ---------------------------------------------------------------- materials.json (mismo esquema que export_shell11.py)
def flat(mesh):
    out = {}
    for m in mesh.data.materials:
        b = next((n for n in m.node_tree.nodes if n.type == 'BSDF_PRINCIPLED'), None)
        if b is None or any(n.type == 'TEX_IMAGE' for n in m.node_tree.nodes): continue
        c = b.inputs['Base Color'].default_value
        out[m.name] = dict(name=m.name, r=round(c[0], 4), g=round(c[1], 4), b=round(c[2], 4), metal=round(b.inputs['Metallic'].default_value, 2),
                           vc=any(n.type == 'VERTEX_COLOR' for n in m.node_tree.nodes))
    return list(out.values())


# ---------------------------------------------------------------- exportacion de un NPC
def export_npc(p, outroot, src_sha, check_only):
    folder, fbxname = NPCS[p]
    arm, mesh, info = check_structure(p, folder)
    check_geometry(p, mesh, arm, info)
    check_materials(p, folder, mesh, info)
    log(p, 'guardas OK', 'verts', info['verts'], 'polys', info['polys'], 'keys', len(info['shape_keys']) - 1, 'correctivas', len(info['correctives']))
    if check_only:
        return dict(npc=p, folder=folder, checks=info, exported=False)
    outdir = os.path.join(outroot, folder); os.makedirs(outdir, exist_ok=True)
    fbx = os.path.join(outdir, fbxname + '.fbx')
    state = capture(arm, mesh)
    rest_info = None
    try:
        PL.reset(arm)                       # mismo mecanismo que export_gen_test.py
        arm.location = (0, 0, 0)            # rig en el origen, como export_shell11.py
        bpy.context.view_layer.update()
        rest_info = verify_rest(p, arm, mesh)
        for o in bpy.context.view_layer.objects: o.select_set(False)
        arm.select_set(True); mesh.select_set(True)
        bpy.context.view_layer.objects.active = arm
        bpy.ops.export_scene.fbx(filepath=fbx, **FBX_ARGS)
    finally:
        restore(arm, mesh, state)
        err = state_equal(arm, mesh, state)
        if err: raise SystemExit('FO FATAL %s: la restauracion del estado fallo (%s); NO guardar el .blend' % (p, err))
    log(p, 'estado restaurado exactamente')
    if not os.path.isfile(fbx): raise Abort('%s: el FBX no se creo' % p)
    # textura(s) para la promocion + materials.json
    tdir = os.path.join(outdir, 'Textures'); tex_out = {}
    for g, f in info['texture_sources'].items():
        os.makedirs(tdir, exist_ok=True)
        dst = os.path.join(tdir, 'T_%s_%s.png' % (p, g)); shutil.copyfile(f, dst); tex_out[os.path.basename(dst)] = dict(source=os.path.relpath(f, ROOT), sha256=sha256(dst))
    mj = dict(folder=folder, prefix=p, fbx=fbxname, flat=flat(mesh), paint=[p + '_skin_Paint', p + '_hair_Paint', p + '_clothes_Paint'])
    with open(os.path.join(outdir, 'materials.json'), 'w') as f: json.dump(mj, f)
    man = dict(script='export_face_official.py', script_version=SCRIPT_VERSION, npc=p, folder=folder, fbx=fbxname + '.fbx', exported_utc=time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime()),
               source=dict(file=os.path.basename(bpy.data.filepath), kind='face-master' if os.path.basename(bpy.data.filepath).lower() == SRC_NAME.lower() else 'work-copy-of-face', sha256=src_sha, blender=bpy.app.version_string), fbx_settings={k: (sorted(v) if isinstance(v, set) else v) for k, v in FBX_ARGS.items()},
               rest_pose=dict(method='pose_lib.reset + verificacion', **rest_info, original_state_non_neutral=True),
               checks=info, blendshape_policy='correctivas exportadas como blend shapes (valor 0, sin drivers); 9 faciales siempre',
               files=dict(fbx=dict(sha256=sha256(fbx), bytes=os.path.getsize(fbx)), materials_json=sha256(os.path.join(outdir, 'materials.json')), textures=tex_out),
               promoted=False)
    with open(os.path.join(outdir, 'manifest.json'), 'w') as f: json.dump(man, f, indent=1)
    log(p, 'EXPORTADO', fbx, man['files']['fbx']['sha256'][:16])
    return man


def main():
    opt = parse_args()
    src = check_source(opt.get('work_copy', False))
    src_sha = sha256(src)
    log('fuente', src, src_sha[:16], 'salida', opt['out'], 'npcs', opt['sel'], 'check_only', opt['check_only'])
    missing = [p for p in NPCS if (p + '_Rig') not in O or (p + '_Mesh') not in O]
    if missing: raise Abort('faltan NPCs en el .blend: %s' % missing)
    results = []
    for p in opt['sel']:
        results.append(export_npc(p, opt['out'], src_sha, opt['check_only']))
    if sha256(src) != src_sha: raise SystemExit('FO FATAL: el .blend cambio en disco durante la exportacion')
    log('FIN', [r['npc'] for r in results], 'dirty=%s' % bpy.data.is_dirty)


try:
    main()
except Abort as e:
    print('FO ABORT', e, flush=True)
    sys.exit(1)
