"""Segunda pasada de pesos: elimina el estiramiento al animar.

Medido en Unity (BakeMesh con el ciclo de caminar vs. reposo): aristas que se alargan x10-x20 entre vertices ligados a 'pelvis' y 'thigh_*'
(guantes del cinturon, bolsillos, bajo de chaqueta), bolsas, botones, parches.

1) rigidify(ob): cada isla conexa de la malla pasa a UN solo hueso (el de mayor peso total) -> la pieza se mueve rigida, sin estirarse.
   Para accesorios: botones, parches, guantes, herramientas, bolsos, reloj de bolsillo, hombreras, radio, medalla, pinceles, cordones.
2) smooth_weights(ob): suaviza los pesos sobre la malla (promedio con los vecinos) para quitar saltos bruscos pelvis -> muslo en prendas
   (chaqueta, pantalon, vestido, camiseta, delantal). Se limita a 4 influencias y se normaliza.
Uso (Blender): exec(open(r"D:/TheLivingCanvas/Tools/npc_pipeline/fix_weights2.py").read()); run_all()
"""
import bpy
import bmesh

PREFIXES = ['Cur', 'Grd', 'Stu', 'Gar', 'Caf', 'Tou', 'Gen', 'Cou', 'Doc', 'Pnt']
RIGID = ('_Buttons', '_SuitDetails', '_Patches', '_SleevePatch', '_Epaulettes', '_Gloves', '_ToolBelt', '_PocketWatch', '_Bag',
         '_Brushes', '_Radio', '_Medal', '_BootLaces', '_ShoeBows', '_Camera', '_Lanyard', '_Brooch')
SMOOTH = ('_Suit', '_Pants', '_Tee', '_Shirt', '_Dress', '_Apron', '_Top', '_Shorts')


def _components(bm):
    seen, comps = set(), []
    for v in bm.verts:
        if v in seen:
            continue
        st, comp = [v], []
        seen.add(v)
        while st:
            c = st.pop()
            comp.append(c)
            for e in c.link_edges:
                o = e.other_vert(c)
                if o not in seen:
                    seen.add(o)
                    st.append(o)
        comps.append(comp)
    return comps


def rigidify(ob, deform_names):
    me = ob.data
    names = {g.index: g.name for g in ob.vertex_groups}
    bm = bmesh.new()
    bm.from_mesh(me)
    comps = _components(bm)
    plan = []
    for comp in comps:
        tot = {}
        for v in comp:
            for g in me.vertices[v.index].groups:
                n = names.get(g.group)
                if n in deform_names:
                    tot[n] = tot.get(n, 0.0) + g.weight
        if tot:
            plan.append(([v.index for v in comp], max(tot, key=tot.get)))
    bm.free()
    for idx, bone in plan:
        for g in ob.vertex_groups:
            g.remove(idx)
        vg = ob.vertex_groups.get(bone) or ob.vertex_groups.new(name=bone)
        vg.add(idx, 1.0, 'REPLACE')
    return len(plan)


def smooth_weights(ob, deform_names, iters=3, factor=0.5, max_inf=4):
    me = ob.data
    names = {g.index: g.name for g in ob.vertex_groups}
    n = len(me.vertices)
    w = []
    for v in me.vertices:
        w.append({names[g.group]: g.weight for g in v.groups if names.get(g.group) in deform_names and g.weight > 1e-4})
    nb = [set() for _ in range(n)]
    for e in me.edges:
        a, b = e.vertices
        nb[a].add(b)
        nb[b].add(a)
    for _ in range(iters):
        new = []
        for i in range(n):
            cur = w[i]
            if not nb[i] or not cur:
                new.append(cur)
                continue
            acc = {}
            for j in nb[i]:
                for k, val in w[j].items():
                    acc[k] = acc.get(k, 0.0) + val / len(nb[i])
            mix = {}
            for k in set(cur) | set(acc):
                mix[k] = (1 - factor) * cur.get(k, 0.0) + factor * acc.get(k, 0.0)
            top = sorted(mix.items(), key=lambda kv: -kv[1])[:max_inf]
            s = sum(val for _, val in top) or 1.0
            new.append({k: val / s for k, val in top})
        w = new
    for i, d in enumerate(w):
        for g in ob.vertex_groups:
            g.remove([i])
        for k, val in d.items():
            vg = ob.vertex_groups.get(k) or ob.vertex_groups.new(name=k)
            vg.add([i], val, 'REPLACE')


def run_all(verbose=True):
    O = bpy.data.objects
    res = {}
    for pre in PREFIXES:
        arm = O[pre + '_Rig']
        deform = {b.name for b in arm.data.bones if b.use_deform}
        for ob in arm.children:
            if ob.type != 'MESH':
                continue
            nm = ob.name
            if nm.endswith(RIGID):
                res[nm] = ('rigid', rigidify(ob, deform))
            elif nm.endswith(SMOOTH):
                smooth_weights(ob, deform)
                res[nm] = ('smooth', len(ob.data.vertices))
    if verbose:
        print(res)
    return res
