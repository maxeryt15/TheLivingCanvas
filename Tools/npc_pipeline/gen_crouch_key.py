"""Corrective shape key EXPERIMENTAL de Gen para Crouch (faldon delantero/lateral del abrigo). Solo anade UNA key relativa a Basis + su driver; no toca pesos, geometria base ni otras keys.
Uso: blender -b <copia_de_la_version_aprobada>.blend --python gen_crouch_key.py -- <salida.blend> [ramp_start=0.55]
Metodo: pose Crouch (frac 1) -> region R = vertices del abrigo con z<ZMAX e y<YMAX (frente y laterales; la abertura trasera no se toca) ->
relajacion PBD solo de aristas COMPRIMIDAS (ratio<RMIN) hacia RESTORE*L0 -> comprobacion contra el pantalon (no hundir mas un vertice que ya esta dentro) ->
desplazamiento a espacio de reposo con la inversa de la matriz de skinning por vertice -> key 'Corrective_Gen_Crouch_Hem'.
Driver: min(rot thigh_l, rot thigh_r)/110 deg, rampa ramp_start..1 (las patadas = un solo muslo => inactiva)."""
import bpy, sys, json, math
sys.path.insert(0, r'D:\TheLivingCanvas\Tools\npc_pipeline')
import pose_lib as PL, layer_clip_scan as LC
import make_corrective as MC
from mathutils import Vector, Matrix
from mathutils.bvhtree import BVHTree
ZMAX, YMAX, RMIN, RESTORE, ITERS, K, MAXD, CLEAR = 1.0, 0.05, 0.75, 0.7, 60, 0.5, 0.04, 0.002
ZB, BIT, LAM = 0.93, 12, 0.5
a = sys.argv[sys.argv.index('--') + 1:]
OUT = a[0]; RAMP = float(a[1]) if len(a) > 1 else 0.55
ob, me, U, L, fu, fl = LC.setup('Gen'); arm = bpy.data.objects['Gen_Rig']
sk = me.shape_keys
assert 'Corrective_Gen_Crouch_Hem' not in sk.key_blocks, 'ya existe: no aplicar dos veces'
cal = PL.calibrate(arm); steps = cal['Crouch']
basis = sk.key_blocks[0]
base = [basis.data[i].co.copy() for i in range(len(me.vertices))]
region = {i for i in U if base[i].z < ZMAX and base[i].y < YMAX}
polysU = [tuple(p.vertices) for p in me.polygons if all(v in set(U) for v in p.vertices)]
edges = sorted({tuple(sorted((p[k], p[(k + 1) % len(p)]))) for p in polysU for k in range(len(p))})
adj = {}
for e in edges: adj.setdefault(e[0], set()).add(e[1]); adj.setdefault(e[1], set()).add(e[0])
ring = {u for v in region for u in adj.get(v, ())} | region
L0 = {e: (base[e[0]] - base[e[1]]).length for e in edges}
PL.apply(arm, steps, 1.0)
def posed():
    ev = ob.evaluated_get(bpy.context.evaluated_depsgraph_get()); m = ev.to_mesh(); co = [v.co.copy() for v in m.vertices]; ev.to_mesh_clear(); return co
co = posed()
fl_polys = [tuple(p.vertices) if hasattr(p, 'vertices') else tuple(me.polygons[p].vertices) for p in fl]
bvh = BVHTree.FromPolygons(co, fl_polys)
def sd(v, c): 
    loc, nor, idx, d = bvh.find_nearest(c); return (c - loc).dot(nor) if loc else 9
work = [e for e in edges if (e[0] in region or e[1] in region) and L0[e] > 0.003]
p = {v: co[v].copy() for v in region}
for _ in range(ITERS):
    for e in work:
        x, y = e; pa = p.get(x, co[x]); pb = p.get(y, co[y]); d = pb - pa; Ln = d.length
        if Ln < 1e-9 or Ln / L0[e] >= RMIN: continue
        corr = d * ((Ln - RESTORE * L0[e]) / Ln) * K
        fa, fb = x in p, y in p
        if fa and fb: p[x] = pa + corr * 0.5; p[y] = pb - corr * 0.5
        elif fa: p[x] = pa + corr
        elif fb: p[y] = pb - corr
# suavizado de la curva del borde inferior (puntas): Laplaciano solo a lo largo del borde abierto z<ZB, y 1 anillo interior sigue la mitad
ecnt = {}
for pl in polysU:
    for k in range(len(pl)):
        e = tuple(sorted((pl[k], pl[(k + 1) % len(pl)]))); ecnt[e] = ecnt.get(e, 0) + 1
badj = {}
for e, c in ecnt.items():
    if c == 1 and all(base[v].z < ZB for v in e): badj.setdefault(e[0], set()).add(e[1]); badj.setdefault(e[1], set()).add(e[0])
bv = [v for v in badj if v in region]
for _ in range(BIT):
    q = {}
    for v in bv:
        nb = list(badj[v])
        if len(nb) < 2: continue
        tgt = sum((p.get(u, co[u]) for u in nb), Vector()) / len(nb)
        q[v] = p[v] * (1 - LAM) + tgt * LAM
    p.update(q)
inner = {}
for v in bv:
    for u in adj.get(v, ()):
        if u in region and u not in badj: inner.setdefault(u, []).append(p[v] - co[v])
for u, l in inner.items(): p[u] = p[u] + sum(l, Vector()) / len(l) * 0.5
disp = {}; clipped = 0
for v in region:
    dv = p[v] - co[v]
    if dv.length < 1e-4: continue
    if dv.length > MAXD: dv = dv.normalized() * MAXD
    new = co[v] + dv
    if sd(v, new) < min(sd(v, co[v]), CLEAR) - 0.0005: dv *= 0.5; clipped += 1   # no hundir mas en el pantalon
    disp[v] = dv
rest = MC.to_rest(ob, arm, disp)
key = ob.shape_key_add(name='Corrective_Gen_Crouch_Hem', from_mix=False); key.relative_key = basis; key.value = 0.0
for v, dv in rest.items(): key.data[v].co = basis.data[v].co + dv
PL.reset(arm)
# driver: min(rotacion thigh_l, thigh_r) / angulo, rampa RAMP..1
st = {s[0]: s for s in steps}
fc = key.driver_add('value'); d = fc.driver; d.type = 'SCRIPTED'
for nm, bone in (('tl', 'thigh_l'), ('tr', 'thigh_r')):
    var = d.variables.new(); var.name = nm; var.type = 'TRANSFORMS'; t = var.targets[0]
    t.id = arm; t.bone_target = bone; t.transform_type = 'ROT_' + 'XYZ'[st[bone][1]]; t.transform_space = 'LOCAL_SPACE'; t.rotation_mode = 'AUTO'
full = math.radians(st['thigh_l'][3])
d.expression = f'max(0,min(1,(min({st["thigh_l"][2]}*tl,{st["thigh_r"][2]}*tr)/{full:.5f}-{RAMP:.3f})/{1 - RAMP:.3f}))'
rep = dict(key='Corrective_Gen_Crouch_Hem', ramp_start=RAMP, region_verts=len(region), moved_verts=len(disp), clipped=clipped,
           max_mm=round(max(v.length for v in rest.values()) * 1000, 1), driver=d.expression, verts=sorted(disp))
json.dump(rep, open(r'D:\TheLivingCanvas\ArtSource\NPC\_Reports\gen_hem\crouch_key_report.json', 'w'), indent=1)
print('KEY', {k: v for k, v in rep.items() if k != 'verts'})
bpy.ops.wm.save_as_mainfile(filepath=OUT); print('SAVED')
