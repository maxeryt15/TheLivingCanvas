"""Comprobacion sin MCP: reconstruye el interior en Blender en consola, busca choques y renderiza camaras.

blender -b --factory-startup --python Tools/museum_models/render_check.py -- <carpeta_salida> [Cam_Int_A,Cam_Int_B|all] [--save]

- Escribe <salida>/clashes.txt (pares de objetos que se penetran > 3 mm, salvo estructura con estructura)
  y <salida>/<camara>.jpg (EEVEE, 1100x620).
- --save guarda ArtSource/Museum/Museum_Interior.blend y la copia museo_interior.blend.
"""
import bpy, bmesh, itertools, os, sys
from mathutils.bvhtree import BVHTree
from mathutils import Vector

argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
out = argv[0] if argv else os.path.join(os.environ.get("TEMP", "."), "museum_check")
cams = argv[1] if len(argv) > 1 and not argv[1].startswith("--") else "all"
save = "--save" in argv
os.makedirs(out, exist_ok=True)

P = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, P)
import museum_int as I  # noqa: E402

I.build()

# ---------------------------------------------------------------- choques
S = {'Int_Shell_Walls', 'Int_Slabs', 'Int_GF_Floors', 'Int_UF_Floors', 'Int_GF_Partitions', 'Int_UF_Partitions',
     'Int_GF_WallFinish', 'Int_UF_WallFinish', 'Int_Door_Casings', 'Int_Window_Frames', 'Int_Window_Glass',
     'Int_Ceiling_Features', 'Int_Wing_Shell', 'Int_Wing_Floor', 'Int_Wing_WallFinish', 'Int_Wing_Volumes',
     'Int_Wing_Tracks', 'Int_Stairs', 'Int_Basement_Access', 'Int_Restroom_Tiles'}
S |= {o.name for o in bpy.data.objects if o.get("structure")}   # objetos marcados como estructura desde el script
dg = bpy.context.evaluated_depsgraph_get()
data, bbs = {}, {}
for o in bpy.data.objects:
    if o.type != 'MESH':
        continue
    bm = bmesh.new(); bm.from_object(o, dg); bm.transform(o.matrix_world)
    bmesh.ops.triangulate(bm, faces=bm.faces)
    vs = [v.co.copy() for v in bm.verts]
    if not vs:
        bm.free(); continue
    data[o.name] = (BVHTree.FromBMesh(bm), vs)
    bbs[o.name] = (tuple(min(v[i] for v in vs) for i in range(3)), tuple(max(v[i] for v in vs) for i in range(3)))
    bm.free()


def depth(a, b):
    t = data[b][0]; md = 0; worst = None
    lo, hi = bbs[b]
    for p in data[a][1]:
        if any(p[i] < lo[i] - 0.001 or p[i] > hi[i] + 0.001 for i in range(3)):
            continue
        loc, n, i, d = t.find_nearest(p)
        if loc is None or (p - loc).dot(n) >= 0 or d <= md:
            continue
        inside = True
        for dv in (Vector((0.0, 0.0, 1.0)), Vector((0.31, 0.77, 0.55)).normalized()):
            cnt = 0; q = p.copy()
            for _ in range(50):
                h = t.ray_cast(q, dv)
                if h[0] is None:
                    break
                cnt += 1; q = h[0] + dv * 1e-4
            if cnt % 2 == 0:
                inside = False
        if inside:
            md = d; worst = p
    return md, worst


res = []
for a, b in itertools.combinations(sorted(data), 2):
    if a in S and b in S:
        continue
    A, Bb = bbs[a], bbs[b]
    if any(A[1][i] < Bb[0][i] - 0.01 or Bb[1][i] < A[0][i] - 0.01 for i in range(3)):
        continue
    if not data[a][0].overlap(data[b][0]):
        continue
    d1, w1 = depth(a, b); d2, w2 = depth(b, a)
    d, w = (d1, w1) if d1 >= d2 else (d2, w2)
    if d > 0.003:
        res.append((round(d, 3), a, b, tuple(round(x, 2) for x in w)))
res.sort(reverse=True)
with open(os.path.join(out, "clashes.txt"), "w", encoding="utf-8", newline="\n") as f:
    f.write("TOTAL %d\n" % len(res))
    for r in res:
        f.write("%s\n" % (r,))
print("CLASHES", len(res))
for r in res[:40]:
    print("  ", r)

# ---------------------------------------------------------------- renders
sc = bpy.context.scene
try:
    sc.render.engine = 'BLENDER_EEVEE'
except TypeError:
    pass
sc.render.resolution_x, sc.render.resolution_y, sc.render.resolution_percentage = 1100, 620, 100
try:
    sc.eevee.taa_render_samples = 32
except Exception:
    pass
sc.render.image_settings.file_format = 'JPEG'
names = sorted(o.name for o in bpy.data.objects if o.type == 'CAMERA') if cams == "all" else cams.split(",")
for n in names:
    ob = bpy.data.objects.get(n)
    if ob is None:
        print("NO CAM", n); continue
    sc.camera = ob
    sc.render.filepath = os.path.join(out, n + ".jpg")
    bpy.ops.render.render(write_still=True)
    print("RENDER", n)

if save:
    sc.camera = bpy.data.objects.get("Cam_Int_Hall") or sc.camera
    for lib in list(bpy.data.libraries):
        bpy.data.libraries.remove(lib)
    root = os.path.dirname(os.path.dirname(P))
    bpy.ops.wm.save_as_mainfile(filepath=os.path.join(root, "ArtSource", "Museum", "Museum_Interior.blend"))
    bpy.ops.wm.save_as_mainfile(filepath=os.path.join(root, "ArtSource", "Museum", "museo_interior.blend"), copy=True)
    print("SAVED")
