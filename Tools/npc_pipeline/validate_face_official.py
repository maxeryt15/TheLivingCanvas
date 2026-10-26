"""Validador del staging de export_face_official.py. SOLO LECTURA: abre Face (no lo guarda), reimporta el FBX de staging en una escena vacia y compara.
Uso: blender -b ArtSource/NPC/NPCs_Shell_Face.blend --python Tools/npc_pipeline/validate_face_official.py -- --npc Gen [--ref <otro.fbx>] [--staging <dir>]
Comprueba: manifest/hash, vertices, caras, UVs, pesos (por posicion), huesos, vertex groups, shape keys (nombres, valores = 0), materiales,
y que la pose exportada es el REPOSO (la malla del FBX coincide con la malla de Face en reposo y NO con la malla en la pose guardada de Face).
Con --ref compara ademas el FBX contra otro FBX (p. ej. el Gentleman validado) por datos (vertices, pesos, UVs, keys, huesos, materiales)."""
import bpy, os, sys, json, hashlib, re
import numpy as np
from mathutils.kdtree import KDTree
ROOT = r'D:\TheLivingCanvas'
sys.path.insert(0, os.path.join(ROOT, 'Tools', 'npc_pipeline'))
import pose_lib as PL
a = sys.argv[sys.argv.index('--') + 1:]
npc = a[a.index('--npc') + 1]
ref = a[a.index('--ref') + 1] if '--ref' in a else None
stg = a[a.index('--staging') + 1] if '--staging' in a else os.path.join(ROOT, 'ArtSource', '_Exports', 'FaceOfficial')
FOLD = {'Cur': ('Curator', 'Curator'), 'Grd': ('Guard', 'Guard'), 'Stu': ('Student', 'Student'), 'Gar': ('Gardener', 'Gardener'), 'Caf': ('Cafe', 'Cafe'),
        'Tou': ('Tourist', 'Tourist'), 'Gen': ('Gentleman', 'Gentleman'), 'Cou': ('Courier', 'Courier'), 'Doc': ('Docent', 'Docent'), 'Pnt': ('Painter', 'Painter'),
        'Rose': ('Rose', 'Rose_Receptionist')}
folder, fbxn = FOLD[npc]
d = os.path.join(stg, folder); fbx = os.path.join(d, fbxn + '.fbx')
O = bpy.data.objects
res = {}; fails = []


def chk(name, ok, detail=''):
    res[name] = (bool(ok), detail)
    if not ok: fails.append(name)


def sha(path):
    h = hashlib.sha256()
    with open(path, 'rb') as f: h.update(f.read())
    return h.hexdigest()


def sig(me, obj):
    """firma por datos de una malla importada o de origen"""
    nv = len(me.vertices)
    co = np.empty(nv * 3); me.vertices.foreach_get('co', co); co = co.reshape(-1, 3)
    names = [g.name for g in obj.vertex_groups]
    W = [{names[g.group]: g.weight for g in v.groups if g.weight > 1e-6} for v in me.vertices]
    uv = np.empty(len(me.loops) * 2); me.uv_layers.active.data.foreach_get('uv', uv)
    keys = [(k.name, round(k.value, 6)) for k in me.shape_keys.key_blocks] if me.shape_keys else []
    return dict(co=co, W=W, nv=nv, npoly=len(me.polygons), uvsum=float(uv.reshape(-1, 2).sum()), keys=keys, mats=[re.sub(r'\.\d{3}$', '', m.name) for m in me.materials], vg=sorted(names))


man = json.load(open(os.path.join(d, 'manifest.json')))
chk('manifest_fbx_hash', sha(fbx) == man['files']['fbx']['sha256'], man['files']['fbx']['sha256'][:12])
src = O[npc + '_Mesh']; arm = O[npc + '_Rig']
# 1) malla de Face en la pose GUARDADA (no neutra) y en REPOSO
dg = bpy.context.evaluated_depsgraph_get()


def eval_co():
    bpy.context.view_layer.update()
    dgl = bpy.context.evaluated_depsgraph_get(); dgl.update(); ev = src.evaluated_get(dgl); em = ev.to_mesh()
    c = np.empty(len(em.vertices) * 3); em.vertices.foreach_get('co', c); ev.to_mesh_clear(); c = c.reshape(-1, 3)
    M = np.array(src.matrix_world); return c @ M[:3, :3].T + M[:3, 3]


arm.location = (0, 0, 0)                 # solo en memoria (este script no guarda): el rig de Face esta desplazado en X
posed_world = eval_co()                  # pose GUARDADA (no neutra) de Face, rig en el origen
PL.reset(arm)
rest_world = eval_co()
sk = sig(src.data, src)
src_dev = float(np.abs(posed_world - rest_world).max())
# 2) importar el FBX en escena aparte (se importa en el mismo archivo; se borra al final)
before = set(O.keys())
bpy.ops.import_scene.fbx(filepath=fbx, axis_forward='-Z', axis_up='Y', automatic_bone_orientation=False, primary_bone_axis='Y', secondary_bone_axis='X')
new = [O[k] for k in O.keys() if k not in before]
iarm = next(o for o in new if o.type == 'ARMATURE'); im = next(o for o in new if o.type == 'MESH')
isg = sig(im.data, im)
chk('verts', isg['nv'] == sk['nv'], '%d vs %d' % (isg['nv'], sk['nv']))
chk('faces', isg['npoly'] == sk['npoly'], '%d vs %d' % (isg['npoly'], sk['npoly']))
chk('uv_sum', abs(isg['uvsum'] - sk['uvsum']) < 1e-2, '%.3f vs %.3f' % (isg['uvsum'], sk['uvsum']))
chk('materials', sorted(isg['mats']) == sorted(sk['mats']), '%d vs %d; solo en FBX %s; solo en Face %s' % (len(isg['mats']), len(sk['mats']), sorted(set(isg['mats']) - set(sk['mats'])), sorted(set(sk['mats']) - set(isg['mats']))))
dbones = sorted(b.name for b in arm.data.bones if b.use_deform); ibones = sorted(b.name for b in iarm.data.bones)
chk('bones', dbones == ibones, '%d vs %d' % (len(ibones), len(dbones)))
chk('vertex_groups', [g for g in isg['vg']] == [g for g in sk['vg'] if g != 'Root'], '%d' % len(isg['vg']))
kn = [k for k, _ in isg['keys']]; sn = [k for k, _ in sk['keys']]
chk('shape_key_names', kn == sn, '%d vs %d' % (len(kn), len(sn)))
chk('shape_key_values_zero', all(abs(v) < 1e-6 for n, v in isg['keys'] if n != 'Basis'), str([x for x in isg['keys'] if abs(x[1]) > 1e-6 and x[0] != 'Basis']))
# pesos y posicion: emparejar por posicion (mundo) con KD
kd = KDTree(isg['nv'])
imw = np.array([tuple(im.matrix_world @ v.co) for v in im.data.vertices])
for i, p in enumerate(imw): kd.insert(p, i)
kd.balance()
maxd_rest = 0.0; maxd_posed = 0.0; maxw = 0.0; nbad = 0
for i in range(sk['nv']):
    co, idx, dist = kd.find(rest_world[i]); maxd_rest = max(maxd_rest, dist)
    wa = sk['W'][i]; wb = isg['W'][idx]
    dw = max([abs(wa.get(k, 0) - wb.get(k, 0)) for k in set(wa) | set(wb) if k != 'Root'] + [0]); maxw = max(maxw, dw); nbad += dw > 0.02
# distancia a la malla POSADA (debe ser grande: demuestra que no se horneo la pose guardada)
for i in range(0, sk['nv'], 7):
    co, idx, dist = kd.find(posed_world[i]); maxd_posed = max(maxd_posed, dist)
chk('rest_pose_exported', maxd_rest < 1e-4, 'FBX vs Face-en-reposo max %.2e m' % maxd_rest)
chk('saved_pose_not_baked', src_dev > 0.005 and maxd_posed > 0.005, 'pose guardada de Face difiere %.3f m del reposo; FBX difiere %.3f m de la pose guardada' % (src_dev, maxd_posed))
chk('weights', maxw < 0.026 and nbad <= 2, 'max dif %.4f, verts >0.02: %d' % (maxw, nbad))
# 3) comparacion contra otro FBX (referencia)
if ref:
    for o in new: bpy.data.objects.remove(o)
    bpy.ops.import_scene.fbx(filepath=ref, axis_forward='-Z', axis_up='Y', automatic_bone_orientation=False, primary_bone_axis='Y', secondary_bone_axis='X')
    n2 = [O[k] for k in O.keys() if k not in before]
    rm = next(o for o in n2 if o.type == 'MESH')
    rs = sig(rm.data, rm)
    cd = float(np.abs(rs['co'] - isg['co']).max()) if rs['nv'] == isg['nv'] else -1
    wd = max([max([abs(a.get(k, 0) - b.get(k, 0)) for k in set(a) | set(b)] + [0]) for a, b in zip(rs['W'], isg['W'])]) if rs['nv'] == isg['nv'] else -1
    chk('ref_verts_faces', rs['nv'] == isg['nv'] and rs['npoly'] == isg['npoly'], '%d/%d vs %d/%d' % (isg['nv'], isg['npoly'], rs['nv'], rs['npoly']))
    chk('ref_vertex_positions', 0 <= cd < 1e-5, 'max %.3e m (indice a indice)' % cd)
    chk('ref_weights', 0 <= wd < 1e-4, 'max %.2e' % wd)
    chk('ref_uv', abs(rs['uvsum'] - isg['uvsum']) < 1e-3, '%.4f vs %.4f' % (rs['uvsum'], isg['uvsum']))
    chk('ref_keys_materials_vgroups', rs['keys'] == isg['keys'] and sorted(rs['mats']) == sorted(isg['mats']) and rs['vg'] == isg['vg'], 'keys %s mats %s vg %s' % (rs['keys'] == isg['keys'], sorted(rs['mats']) == sorted(isg['mats']), rs['vg'] == isg['vg']))
print('VAL ' + json.dumps({k: v for k, v in res.items()}, default=str))
print('VAL_FAILS', fails)
