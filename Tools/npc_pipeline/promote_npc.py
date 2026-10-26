"""Promocion de UN NPC de staging (ArtSource/_Exports/NPC_Validation/<Folder>/) a produccion (Assets/_TheLivingCanvas/Art/Models/NPC/<Folder>/). Nunca en lote.
Por defecto es una PRUEBA EN SECO: solo lee y escribe el informe ArtSource/_Exports/NPC_Validation/<Folder>/promotion_plan.json/.md (y reports/fbxinfo_*.json).
  python promote_npc.py --npc Student                            # prueba en seco (precondiciones + diff + plan de remaps)
  python promote_npc.py --npc Student --apply --confirm Student  # backup + copia del FBX (conserva el .meta). Exige la confirmacion del usuario en el chat.
  python promote_npc.py --npc Student --mark-promoted            # SOLO tras verificar en Unity (avatar, huesos, slots, remaps, prefab): marca promoted:true en el manifest
  python promote_npc.py --npc Student --rollback <carpeta_backup>   # restaura FBX + .meta desde el backup
No toca prefabs, animaciones, controllers, NpcImportTool, export_shell11.py, ni los .blend. Tras --apply hay que refrescar Unity y verificar (paso 6 de Docs/NPC_Face_Pipeline.md).
--apply y --rollback estan escritos pero SIN PROBAR (solo se ha probado la prueba en seco)."""
import ast, sys, os, json, hashlib, shutil, subprocess, argparse, datetime, re
ROOT = r'D:\TheLivingCanvas'; PIPE = os.path.join(ROOT, 'Tools', 'npc_pipeline')
BLENDER = r'D:\SteamLibrary\steamapps\common\Blender\blender.exe'
STAGE = os.path.join(ROOT, 'ArtSource', '_Exports', 'NPC_Validation'); PROD = os.path.join(ROOT, 'Assets', '_TheLivingCanvas', 'Art', 'Models', 'NPC')
PREF = {'Student': 'Stu', 'Guard': 'Grd', 'Docent': 'Doc', 'Cafe': 'Caf', 'Courier': 'Cou', 'Curator': 'Cur', 'Painter': 'Pnt', 'Tourist': 'Tou', 'Gardener': 'Gar', 'Rose': 'Rose'}
WORK = {k: 'NPCs_Shell_Face_%s_WORK.blend' % k.upper() for k in PREF}
KNOWN_FALSE_FAILS = {'Tourist': {'faces'}, 'Guard': {'faces', 'weights'}, 'Docent': {'weights'}}   # 81 caras duplicadas de signo opuesto (BagStar0-4) que el FBX deduplica
SHARED_MOUTH = 'Assets/_TheLivingCanvas/Art/Materials/NPC/Gentleman/M_NPC_MouthInside.mat'


def sha(p):
    h = hashlib.sha256()
    with open(p, 'rb') as f:
        for b in iter(lambda: f.read(1 << 20), b''): h.update(b)
    return h.hexdigest()


def run(cmd):
    r = subprocess.run(cmd, capture_output=True, text=True, errors='replace'); return r.returncode, (r.stdout or '') + (r.stderr or '')


def meta_remaps(meta):   # nombres de material remapeados en externalObjects del .meta
    t = open(meta, encoding='utf-8', errors='replace').read()
    return sorted(set(re.findall(r'type: UnityEngine:Material\s+assembly: UnityEngine.CoreModule\s+name: (\S+)', t)))


def mat_guid(path):
    t = open(path + '.meta', encoding='utf-8').read(); return re.search(r'guid: ([0-9a-f]{32})', t).group(1)


def prepare_meta(f, p_meta, fbx_name):
    """Añade al .meta de PRODUCCION los remaps de los slots del FBX de staging que no tienen (NPC_MouthInside -> material compartido; resto -> M_<slot>.mat o M_<Prefijo>_<slot>.mat de
    Materials/NPC/<Folder>/). Hace backup del .meta antes. No copia el FBX. Slots sin material en disco se listan y NO se escriben."""
    info = os.path.join(STAGE, f, 'reports', 'fbxinfo_staging.json'); S = json.load(open(info)); have = set(meta_remaps(p_meta)); mdir = os.path.join(ROOT, 'Assets', '_TheLivingCanvas', 'Art', 'Materials', 'NPC', f)
    todo = []; absent = []
    for slot in S['materials']:
        if slot in have: continue
        cands = [os.path.join(ROOT, SHARED_MOUTH)] if slot == 'NPC_MouthInside' else [os.path.join(mdir, 'M_%s.mat' % slot), os.path.join(mdir, 'M_%s_%s.mat' % (f if f == 'Rose' else PREF[f], slot))]
        hit = next((c for c in cands if os.path.isfile(c) and os.path.isfile(c + '.meta')), None)
        (todo.append((slot, hit)) if hit else absent.append(slot))
    bk = os.path.join(ROOT, 'ArtSource', '_Backups', '%s_meta_before_%s' % (f, datetime.datetime.now().strftime('%Y%m%d_%H%M%S'))); os.makedirs(bk)
    shutil.copy2(p_meta, os.path.join(bk, os.path.basename(p_meta))); print('backup .meta en', bk)
    raw = open(p_meta, encoding='utf-8', newline='').read(); nl = '\r\n' if '\r\n' in raw else '\n'
    lines = raw.split(nl); i0 = next(i for i, l in enumerate(lines) if l.startswith('  externalObjects:'))
    end = next(i for i in range(i0 + 1, len(lines)) if re.match(r'^  [A-Za-z]', lines[i]))
    new = []
    for slot, path in todo:
        new += ['  - first:', '      type: UnityEngine:Material', '      assembly: UnityEngine.CoreModule', '      name: %s' % slot, '    second: {fileID: 2100000, guid: %s, type: 2}' % mat_guid(path)]
        print('remap añadido:', slot, '->', os.path.relpath(path, ROOT))
    lines[end:end] = new; open(p_meta, 'w', encoding='utf-8', newline='').write(nl.join(lines))
    print('slots sin material en disco (NO escritos):', absent or '—')


def main():
    ap = argparse.ArgumentParser(); ap.add_argument('--npc', required=True, choices=sorted(PREF)); ap.add_argument('--apply', action='store_true'); ap.add_argument('--confirm')
    ap.add_argument('--prepare-meta', action='store_true'); ap.add_argument('--mark-promoted', action='store_true'); ap.add_argument('--rollback'); ap.add_argument('--skip-validate', action='store_true'); a = ap.parse_args()
    f = a.npc; sd = os.path.join(STAGE, f); man_p = os.path.join(sd, 'manifest.json'); man = json.load(open(man_p)); fbx_name = man['fbx']
    s_fbx = os.path.join(sd, fbx_name); p_dir = os.path.join(PROD, f); p_fbx = os.path.join(p_dir, fbx_name); p_meta = p_fbx + '.meta'
    if a.rollback:
        for n in (fbx_name, fbx_name + '.meta'): shutil.copy2(os.path.join(a.rollback, n), os.path.join(p_dir, n))
        print('ROLLBACK ok desde', a.rollback, '-> refresca Unity y verifica'); return
    if a.prepare_meta:
        prepare_meta(f, p_meta, fbx_name); return
    if a.mark_promoted:
        man['promoted'] = True; man['promoted_utc'] = datetime.datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%SZ'); json.dump(man, open(man_p, 'w'), indent=2); print('manifest promoted=true'); return
    pre = []; state = {'ok': True}

    def chk(name, cond, detail=''):
        pre.append({'check': name, 'ok': bool(cond), 'detail': detail}); state['ok'] = state['ok'] and bool(cond)
    chk('manifest promoted=false', man.get('promoted') is False, str(man.get('promoted')))
    chk('FBX staging existe', os.path.isfile(s_fbx)); sh = sha(s_fbx) if os.path.isfile(s_fbx) else ''
    chk('hash FBX == manifest', sh == man['files']['fbx']['sha256'], sh[:16] + ' vs ' + man['files']['fbx']['sha256'][:16])
    wb = os.path.join(ROOT, 'ArtSource', 'NPC', WORK[f]); wsha = sha(wb) if os.path.isfile(wb) else ''
    chk('copia de trabajo igual que al exportar (no editada despues)', wsha == man['source']['sha256'], (wsha[:16] or 'falta') + ' vs ' + man['source']['sha256'][:16])
    chk('produccion existe (FBX + .meta)', os.path.isfile(p_fbx) and os.path.isfile(p_meta))
    if not a.skip_validate and os.path.isfile(wb):
        rc, out = run([BLENDER, '-b', wb, '--python', os.path.join(PIPE, 'validate_face_official.py'), '--', '--npc', PREF[f], '--staging', STAGE])
        m = re.search(r'VAL_FAILS (\[.*?\])', out); fails = ast.literal_eval(m.group(1)) if m else ['sin salida']
        bad = [x for x in fails if x not in KNOWN_FALSE_FAILS.get(f, set())]
        chk('validador sin FAIL (falsos conocidos aparte)', not bad, 'FAILS=%s conocidos=%s' % (fails, sorted(KNOWN_FALSE_FAILS.get(f, set()))))
    tmp = os.path.join(sd, 'reports'); os.makedirs(tmp, exist_ok=True); diff = {}
    for tag, p in (('staging', s_fbx), ('production', p_fbx)):
        o = os.path.join(tmp, 'fbxinfo_%s.json' % tag)
        if os.path.isfile(o): os.remove(o)
        run([BLENDER, '-b', '--python', os.path.join(PIPE, 'fbx_info.py'), '--', p, o]); diff[tag] = json.load(open(o)) if os.path.isfile(o) else None
    S, P = diff['staging'], diff['production']; cmp = {}
    if S and P:
        cmp = {'verts': [P['verts'], S['verts']], 'faces': [P['faces'], S['faces']], 'bones_added': sorted(set(S['bones']) - set(P['bones'])), 'bones_removed': sorted(set(P['bones']) - set(S['bones'])),
               'shape_keys_added': sorted(set(S['shape_keys']) - set(P['shape_keys'])), 'shape_keys_removed': sorted(set(P['shape_keys']) - set(S['shape_keys'])),
               'slots': [len(P['materials']), len(S['materials'])], 'slots_added': sorted(set(S['materials']) - set(P['materials'])), 'slots_removed': sorted(set(P['materials']) - set(S['materials'])),
               'bbox_prod': [P['bbox_min'], P['bbox_max']], 'bbox_stage': [S['bbox_min'], S['bbox_max']], 'mesh_names': [P['mesh'], S['mesh']], 'roots': [P.get('roots'), S.get('roots')], 'mesh_parent': [P.get('mesh_parent'), S.get('mesh_parent')]}
        chk('mismo nombre de malla (el prefab la referencia por nombre)', P['mesh'] == S['mesh'], '%s vs %s' % (P['mesh'], S['mesh']))
        chk('misma jerarquia raiz (el prefab referencia nodos por nombre: raiz, Animator)', cmp['roots'][0] == cmp['roots'][1] and cmp['mesh_parent'][0] == cmp['mesh_parent'][1], '%s / %s' % (cmp['roots'], cmp['mesh_parent']))
        FACE_BONES = {'eye_L', 'eye_R', 'eye_aim'}   # rig facial: unico cambio de esqueleto esperado respecto a produccion anterior al rig facial
        chk('huesos: solo se pueden añadir los del rig facial (eye_*)', not cmp['bones_removed'] and set(cmp['bones_added']) <= FACE_BONES, 'añadidos %s quitados %s' % (cmp['bones_added'], cmp['bones_removed']))
    else:
        chk('FBX de produccion y staging legibles', False, 'staging=%s production=%s' % (bool(S), bool(P)))
    remaps = meta_remaps(p_meta) if os.path.isfile(p_meta) else []; mats = S['materials'] if S else []
    missing = [m for m in mats if m not in remaps]; obsolete = [r for r in remaps if r not in mats]; mouth = 'NPC_MouthInside' in remaps
    ok = state['ok']
    plan = {'npc': f, 'fbx': fbx_name, 'stage_sha': sh, 'preconditions': pre, 'ready': ok, 'diff': cmp,
            'meta_remaps': {'present': remaps, 'slots_without_remap': missing, 'remaps_without_slot': obsolete, 'mouth_inside_remapped': mouth, 'mouth_target': SHARED_MOUTH},
            'actions_if_apply': ['backup FBX+.meta a ArtSource/_Backups/%s_prod_before_<fecha>/' % f, 'copiar %s sobre produccion (el .meta existente se conserva)' % fbx_name,
                                 '(antes de copiar) --prepare-meta: backup del .meta + remaps de los slots nuevos; debe quedar "slots sin remap: —"', 'refrescar Unity y verificar avatar, huesos, slots, remaps, prefab', 'promote_npc.py --mark-promoted']}
    json.dump(plan, open(os.path.join(sd, 'promotion_plan.json'), 'w'), indent=1)
    L = ['# Plan de promoción — %s (prueba en seco)' % f, '', 'Listo para promover: **%s**' % ('SÍ' if ok else 'NO'), '', '## Precondiciones']
    L += ['- [%s] %s%s' % ('x' if c['ok'] else ' ', c['check'], (' — ' + c['detail']) if c['detail'] else '') for c in pre]
    if cmp:
        L += ['', '## Diff producción → staging', '- Vértices %d → %d, caras %d → %d, slots %d → %d' % (cmp['verts'][0], cmp['verts'][1], cmp['faces'][0], cmp['faces'][1], cmp['slots'][0], cmp['slots'][1]),
              '- Malla: %s → %s' % tuple(cmp['mesh_names']),
              '- Shape keys: +%d / −%d (añadidas: %s)' % (len(cmp['shape_keys_added']), len(cmp['shape_keys_removed']), ', '.join(cmp['shape_keys_added'][:8]) + ('…' if len(cmp['shape_keys_added']) > 8 else '')),
              '- Slots añadidos: %s; quitados: %s' % (cmp['slots_added'] or '—', cmp['slots_removed'] or '—'), '- bbox producción %s → staging %s' % (cmp['bbox_prod'], cmp['bbox_stage'])]
    L += ['', '## Remaps del .meta de producción', '- Slots de staging SIN remap (hay que añadirlos): %s' % (missing or '—'), '- Remaps sin slot (obsoletos, inofensivos): %s' % (obsolete or '—'),
          '- `NPC_MouthInside` remapeado al material compartido: %s' % ('sí' if mouth else '**NO: añadir** → ' + SHARED_MOUTH), '', '## Si se aplica']
    L += ['%d. %s' % (i + 1, x) for i, x in enumerate(plan['actions_if_apply'])]
    open(os.path.join(sd, 'promotion_plan.md'), 'w', encoding='utf-8').write('\n'.join(L) + '\n'); print('\n'.join(L))
    if not a.apply:
        print('\nPRUEBA EN SECO: no se copió nada. Informe:', os.path.join(sd, 'promotion_plan.json')); return
    if not ok: sys.exit('PROMOCION ABORTADA: precondiciones fallidas')
    if a.confirm != f: sys.exit('PROMOCION ABORTADA: falta --confirm %s (confirmación explícita del usuario)' % f)
    bk = os.path.join(ROOT, 'ArtSource', '_Backups', '%s_prod_before_%s' % (f, datetime.datetime.now().strftime('%Y%m%d_%H%M%S'))); os.makedirs(bk); hashes = {}
    for n in (fbx_name, fbx_name + '.meta'): shutil.copy2(os.path.join(p_dir, n), os.path.join(bk, n)); hashes[n] = sha(os.path.join(bk, n))
    json.dump(hashes, open(os.path.join(bk, 'hashes.json'), 'w'), indent=1); shutil.copy2(s_fbx, p_fbx)
    print('APLICADO: backup en', bk, '| FBX copiado, hash', sha(p_fbx)[:16], '| refresca Unity y verifica; rollback: --rollback', bk)


main()
