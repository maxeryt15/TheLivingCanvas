"""Rose_Recepcionist: NPC de la recepcionista (mujer ~60 anios). Blender 4.x, ejecutar en consola:
  blender -b --factory-startup --python npc_rose.py -- <out_dir> [stage]
Escala: metros, pies en z=0, mira hacia -Y (frente de Blender), pose A para rig Humanoid de Unity.
Paso 2: body_blockout() = cuerpo continuo (Skin + Subsurf). Cabeza/pelo/ropa llegan en pasos siguientes.
"""
import bpy, bmesh, sys, os
from mathutils import Vector

HEIGHT = 1.65


def clear():
    bpy.ops.wm.read_factory_settings(use_empty=True)


def _skin_body():
    """Esqueleto de aristas con radios; mismo grafo a izq/der (x espejo)."""
    pts = {}   # nombre -> (pos, rx, ry)
    P = pts.__setitem__
    # eje central
    P('pelvis', ((0, 0.01, 0.93), 0.185, 0.130))
    P('waist',  ((0, 0.00, 1.09), 0.150, 0.105))
    P('chest',  ((0, -0.005, 1.22), 0.160, 0.120))
    P('upper',  ((0, 0.00, 1.33), 0.125, 0.095))
    edges = [('pelvis', 'waist'), ('waist', 'chest'), ('chest', 'upper')]
    for s, sg in (('L', 1), ('R', -1)):
        P('clav' + s,  ((sg * 0.12, 0.0, 1.355), 0.060, 0.060))
        P('shou' + s,  ((sg * 0.215, 0.0, 1.335), 0.062, 0.062))
        P('elb' + s,   ((sg * 0.39, 0.02, 1.15), 0.048, 0.048))
        P('wri' + s,   ((sg * 0.55, 0.03, 0.98), 0.034, 0.030))
        P('hand' + s,  ((sg * 0.635, 0.03, 0.90), 0.040, 0.022))
        P('hip' + s,   ((sg * 0.105, 0.0, 0.85), 0.100, 0.105))
        P('knee' + s,  ((sg * 0.100, 0.01, 0.48), 0.068, 0.068))
        P('calf' + s,  ((sg * 0.098, 0.03, 0.31), 0.062, 0.066))
        P('ank' + s,   ((sg * 0.095, 0.01, 0.09), 0.046, 0.046))
        P('toe' + s,   ((sg * 0.095, -0.14, 0.04), 0.055, 0.038))
        edges += [('upper', 'clav' + s), ('clav' + s, 'shou' + s), ('shou' + s, 'elb' + s),
                  ('elb' + s, 'wri' + s), ('wri' + s, 'hand' + s),
                  ('pelvis', 'hip' + s), ('hip' + s, 'knee' + s), ('knee' + s, 'calf' + s), ('calf' + s, 'ank' + s), ('ank' + s, 'toe' + s)]
    return pts, edges


def body_blockout():
    pts, edges = _skin_body()
    names = list(pts)
    me = bpy.data.meshes.new('Rose_Body')
    me.from_pydata([pts[n][0] for n in names], [(names.index(a), names.index(b)) for a, b in edges], [])
    ob = bpy.data.objects.new('Rose_Body', me)
    bpy.context.scene.collection.objects.link(ob)
    bpy.context.view_layer.objects.active = ob
    ob.select_set(True)
    sk = ob.modifiers.new('Skin', 'SKIN')
    sk.branch_smoothing = 0.8
    sk.use_smooth_shade = True
    for i, n in enumerate(names):
        v = me.skin_vertices[0].data[i]
        v.radius = (pts[n][1], pts[n][2])
        v.use_root = (n == 'pelvis')
    ob.modifiers.new('Subsurf', 'SUBSURF').levels = 1
    ob.modifiers['Subsurf'].render_levels = 1
    return ob


HEAD_C = Vector((0, 0.015, 1.535))
HR = (0.076, 0.098, 0.116)   # semiejes x,y,z de la cabeza base (cabeza ~15 x 19.6 x 23 cm)


def _g(dx, sx, dz, sz):
    import math
    return math.exp(-((dx / sx) ** 2 + (dz / sz) ** 2))


def head_face():
    """Cabeza mid-poly: elipsoide + rasgos como bultos/hundimientos gaussianos elipticos.
    Coordenadas locales: x lateral, z arriba (0 = linea de los ojos aprox.), cara hacia -Y."""
    import math
    bm = bmesh.new()
    bmesh.ops.create_cube(bm, size=2.0)
    bmesh.ops.subdivide_edges(bm, edges=list(bm.edges), cuts=40, use_grid_fill=True)
    for v in bm.verts:                      # cubo -> esfera: cuadros uniformes, sin polos en la cara
        v.co.normalize()
    F = []
    def add(x, z, sx, sz, amp, mirror=True):
        F.append((x, z, sx, sz, amp))
        if mirror and x != 0:
            F.append((-x, z, sx, sz, amp))
    # ojos
    add(0.032, 0.008, 0.017, 0.013, -0.016)      # cuenca
    add(0.033, 0.019, 0.019, 0.0055, 0.0100)      # parpado superior
    add(0.032, -0.005, 0.015, 0.004, 0.0055)     # parpado inferior
    add(0.032, -0.016, 0.015, 0.004, 0.0030)     # bolsa bajo el ojo (edad)
    add(0.030, 0.040, 0.026, 0.008, 0.0035)      # ceja / arco superciliar
    add(0.0, 0.032, 0.010, 0.012, 0.0050)        # entrecejo
    add(0.056, 0.008, 0.009, 0.012, -0.0020)     # patas de gallo
    # nariz
    add(0.0, 0.010, 0.007, 0.018, 0.0090)        # puente
    add(0.0, -0.022, 0.007, 0.024, 0.0060)       # dorso
    add(0.0, -0.046, 0.010, 0.009, 0.0150)       # punta
    add(0.019, -0.052, 0.007, 0.007, 0.0065)     # alas
    add(0.0, -0.062, 0.012, 0.004, -0.0050)      # base / filtrum
    # mejillas y surcos (cara madura)
    add(0.047, -0.025, 0.022, 0.018, 0.0090)     # pomulo
    add(0.045, -0.052, 0.018, 0.020, -0.0040)    # mejilla hundida
    add(0.028, -0.066, 0.008, 0.016, -0.0030)    # surco nasolabial alto
    add(0.034, -0.082, 0.008, 0.015, -0.0030)    # surco nasolabial bajo
    # boca
    add(0.0, -0.077, 0.023, 0.0065, 0.0095, False)  # labio superior
    add(0.0, -0.094, 0.021, 0.0080, 0.0125, False)  # labio inferior
    add(0.0, -0.0845, 0.024, 0.0042, -0.0065, False)  # linea de la boca
    add(0.0, -0.101, 0.015, 0.0065, -0.0035, False)   # surco bajo el labio
    add(0.027, -0.086, 0.008, 0.008, -0.0030)    # comisuras
    add(0.0, -0.108, 0.020, 0.010, 0.0090, False)    # menton
    add(0.0, 0.085, 0.045, 0.030, 0.0030, False)     # frente
    for v in bm.verts:
        d = v.co.copy()
        p = Vector((d.x * HR[0], d.y * HR[1], d.z * HR[2]))
        n = Vector((d.x / HR[0], d.y / HR[1], d.z / HR[2])).normalized()
        if p.z < 0.0:                                  # mandibula mas estrecha
            k = min(1.0, -p.z / HR[2])
            p.x *= 1.0 - 0.22 * k ** 1.6
            if p.y < 0:
                p.y *= 1.0 + 0.11 * k
        if p.y < 0.0:
            front = min(1.0, -p.y / 0.04)
            for cx, cz, sx, sz, amp in F:
                w = _g(p.x - cx, sx, p.z - cz, sz)
                if w > 0.01:
                    p += n * (amp * w * front)
            # sonrisa leve: comisuras suben un poco
            if abs(p.x) > 0.012:
                p.z += 0.0070 * min(1.0, (abs(p.x) - 0.012) / 0.016) * _g(0, 1, p.z + 0.085, 0.012) * front
        v.co = p
    mesh = bpy.data.meshes.new('Rose_Head')
    bm.to_mesh(mesh); bm.free()
    ob = bpy.data.objects.new('Rose_Head', mesh)
    bpy.context.scene.collection.objects.link(ob)
    ob.location = HEAD_C
    for poly in mesh.polygons:
        poly.use_smooth = True
    return ob


def neck():
    bpy.ops.mesh.primitive_cylinder_add(vertices=20, radius=1, depth=1, location=(0, 0.015, 1.395))
    o = bpy.context.object; o.name = 'Rose_Neck'
    o.scale = (0.041, 0.045, 0.130)
    bpy.ops.object.shade_smooth()
    return o


def head_extras():
    """Orejas y ojos (objetos separados para poder animar los ojos)."""
    objs = []
    for sg, tag in ((1, 'L'), (-1, 'R')):
        bpy.ops.mesh.primitive_uv_sphere_add(segments=12, ring_count=8, radius=1, location=HEAD_C + Vector((sg * 0.075, 0.012, -0.010)))
        e = bpy.context.object; e.name = 'Rose_Ear_' + tag
        e.scale = (0.008, 0.019, 0.030); e.rotation_euler = (0, 0, sg * 0.25)
        bpy.ops.object.shade_smooth(); objs.append(e)
        eye_c = HEAD_C + Vector((sg * 0.032, -0.075, 0.008))
        bpy.ops.mesh.primitive_uv_sphere_add(segments=20, ring_count=14, radius=0.0108, location=eye_c)
        w = bpy.context.object; w.name = 'Rose_Eye_' + tag
        bpy.ops.object.shade_smooth(); objs.append(w)
        bpy.ops.mesh.primitive_uv_sphere_add(segments=16, ring_count=10, radius=0.0058, location=eye_c + Vector((0, -0.0082, 0)))
        i = bpy.context.object; i.name = 'Rose_Iris_' + tag; i.scale = (1, 0.5, 1)
        bpy.ops.object.shade_smooth(); objs.append(i)
    return objs


def mat(name, rgb, rough=0.8):
    m = bpy.data.materials.new(name); m.use_nodes = True
    b = m.node_tree.nodes['Principled BSDF']
    b.inputs['Base Color'].default_value = (*rgb, 1); b.inputs['Roughness'].default_value = rough
    m.diffuse_color = (*rgb, 1)
    return m


def assign(ob, m):
    ob.data.materials.clear(); ob.data.materials.append(m)


def render(out_dir, name):
    sc = bpy.context.scene
    sc.render.engine = 'BLENDER_WORKBENCH'
    sc.display.shading.light = 'STUDIO'
    sc.display.shading.color_type = 'MATERIAL'
    sc.render.resolution_x, sc.render.resolution_y = 700, 900
    cam = bpy.data.objects.new('cam', bpy.data.cameras.new('cam'))
    bpy.context.scene.collection.objects.link(cam)
    sc.camera = cam
    cam.data.type = 'ORTHO'
    cam.data.ortho_scale = 2.0
    for tag, loc, rot in (('front', (0, -5, 0.85), (90, 0, 0)), ('side', (5, 0, 0.85), (90, 0, 90))):
        cam.location = loc
        cam.rotation_euler = [r * 3.14159265 / 180 for r in rot]
        sc.render.filepath = os.path.join(out_dir, f'{name}_{tag}.png')
        bpy.ops.render.render(write_still=True)


def render_head(out_dir):
    sc = bpy.context.scene
    sc.render.resolution_x, sc.render.resolution_y = 800, 800
    cam = sc.camera; cam.data.ortho_scale = 0.42
    for tag, loc, rot in (('head_front', (0, -5, 1.54), (90, 0, 0)),
                          ('head_34', (3.5, -3.5, 1.54), (90, 0, 45)),
                          ('head_side', (5, 0, 1.54), (90, 0, 90))):
        cam.location = loc; cam.rotation_euler = [r * 3.14159265 / 180 for r in rot]
        sc.render.filepath = os.path.join(out_dir, f'rose_{tag}.png')
        bpy.ops.render.render(write_still=True)


if __name__ == '__main__':
    out = sys.argv[sys.argv.index('--') + 1]
    os.makedirs(out, exist_ok=True)
    clear()
    body_blockout()
    head = head_face(); extras = head_extras(); nk = neck()
    skin = mat('M_Rose_Skin', (0.80, 0.60, 0.48))
    assign(head, skin); assign(nk, skin); assign(bpy.data.objects['Rose_Body'], skin)
    for o in extras:
        assign(o, skin if 'Ear' in o.name else mat('M_Rose_Eye', (0.95, 0.93, 0.88)) if 'Eye' in o.name else mat('M_Rose_Iris', (0.22, 0.14, 0.08)))
    render(out, 'rose_blockout')
    render_head(out)
    bpy.ops.wm.save_as_mainfile(filepath=os.path.join(out, 'Rose_Recepcionist.blend'))
