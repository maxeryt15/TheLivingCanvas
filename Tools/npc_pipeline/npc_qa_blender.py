"""Runs INSIDE Blender (sent by qa.py). Opens the NPC's latest final .blend, prints automated checks and renders views to Docs/NPC_Preview/qa_<Folder>_*.png."""
import bpy, bmesh, json, math, glob, os, re
from mathutils import Vector
from mathutils.bvhtree import BVHTree

job = json.load(open(os.path.join(os.environ.get('TEMP', '/tmp'), 'qa_job.json')))
N, P = job['folder'], job['prefix']
files = sorted(glob.glob('D:/TheLivingCanvas/ArtSource/NPC/%s/%s_0*_final.blend' % (N, N)), key=os.path.getmtime)
bpy.ops.wm.open_mainfile(filepath=files[-1])
print('FILE', files[-1])
arm = bpy.data.objects[P + '_Rig']
meshes = [o for o in bpy.data.objects if o.type == 'MESH' and o.parent == arm]
print('MESHES', [o.name for o in meshes])
print('BONES', len(arm.data.bones), 'deform', sum(1 for b in arm.data.bones if b.use_deform))
req = ['pelvis', 'spine_01', 'spine_02', 'spine_03', 'neck_01', 'head', 'clavicle_l', 'upperarm_l', 'lowerarm_l', 'hand_l', 'thigh_l', 'calf_l', 'foot_l', 'ball_l', 'thigh_r', 'calf_r', 'foot_r', 'ball_r', 'upperarm_r', 'lowerarm_r', 'hand_r', 'clavicle_r']
used = {}
for o in meshes:
    names = {vg.index: vg.name for vg in o.vertex_groups}
    for v in o.data.vertices:
        for g in v.groups:
            if g.weight > 0.001:
                used[names[g.group]] = used.get(names[g.group], 0) + 1
print('REQUIRED BONES WITHOUT WEIGHTS', [b for b in req if used.get(b, 0) == 0])
for o in meshes:
    names = {vg.index: vg.name for vg in o.vertex_groups}
    unw = sum(1 for v in o.data.vertices if not any(g.weight > 0.001 for g in v.groups))
    mx = max((sum(1 for g in v.groups if g.weight > 0.001) for v in o.data.vertices), default=0)
    bm = bmesh.new(); bm.from_mesh(o.data)
    nm = sum(1 for e in bm.edges if not e.is_manifold)
    loose = sum(1 for v in bm.verts if not v.link_edges)
    bm.free()
    mats = [m.name for m in o.data.materials]
    print('MESH %-18s v=%5d f=%5d unweighted=%d maxinf=%d nonmanifoldEdges=%d loose=%d mats=%d' % (o.name, len(o.data.vertices), len(o.data.polygons), unw, mx, nm, loose, len(mats)))

# overlap checks between body and each other mesh (vertices of outer inside inner)
dg = bpy.context.evaluated_depsgraph_get()
def world_bvh(o):
    bm = bmesh.new(); bm.from_mesh(o.data); bm.transform(o.matrix_world)
    t = BVHTree.FromBMesh(bm); bm.free(); return t
body = bpy.data.objects[P + '_Low']
bt = world_bvh(body)
for o in meshes:
    if o == body or o.name.endswith(('_Eyes', '_Brows', '_Base')):
        continue
    bad = 0
    ot = world_bvh(o)
    pairs = ot.overlap(bt)
    print('OVERLAP body-vs-%s tri-pairs=%d' % (o.name, len(pairs)))

# renders
sc = bpy.context.scene
eng = [e.identifier for e in bpy.types.RenderSettings.bl_rna.properties['engine'].enum_items if 'EEVEE' in e.identifier][0]
sc.render.engine = eng
sc.world = sc.world or bpy.data.worlds.new('W'); sc.world.use_nodes = True
sc.world.node_tree.nodes['Background'].inputs[1].default_value = 2.2
for o in list(bpy.data.objects):
    if o.name == 'QA_Sun': bpy.data.objects.remove(o)
sun = bpy.data.objects.new('QA_Sun', bpy.data.lights.new('QA_Sun', 'SUN')); sc.collection.objects.link(sun)
sun.data.energy = 2.5; sun.rotation_euler = (math.radians(55), 0, math.radians(30))
for o in bpy.data.objects:
    if o.type in ('MESH', 'ARMATURE') and o not in meshes and o != arm:
        o.hide_render = True
    elif o in meshes: o.hide_render = o.name.endswith('_Base')
sc.render.resolution_x, sc.render.resolution_y = 420, 700
cam = bpy.data.objects.new('QA_Cam', bpy.data.cameras.new('QA_Cam')); sc.collection.objects.link(cam); sc.camera = cam
out = 'D:/TheLivingCanvas/Docs/NPC_Preview/'
def shot(tag, ang, target, dist, lens=60):
    cam.data.lens = lens
    a = math.radians(ang)
    cam.location = Vector((target.x + math.sin(a) * dist, target.y - math.cos(a) * dist, target.z))
    cam.rotation_euler = (target - cam.location).to_track_quat('-Z', 'Y').to_euler()
    sc.render.filepath = out + 'qa_%s_%s.png' % (N, tag)
    bpy.ops.render.render(write_still=True)
H = max(v.co.z for v in body.data.vertices)
for tag, ang in (('front', 0), ('q3', 40), ('side', 90), ('back', 180)):
    shot(tag, ang, Vector((0, 0, H * 0.5)), 5.0)
hz = H - 0.1
shot('head_f', 0, Vector((0, 0, hz)), 1.1, 85); shot('head_q', 55, Vector((0, 0, hz)), 1.1, 85)
shot('torso', 0, Vector((0, 0, H * 0.66)), 1.7, 70)
shot('feet', 35, Vector((0, 0, 0.15)), 1.5, 70)
for tag, ang, tx, ty, tz, dist, lens in job.get('extra', []):
    shot(tag, ang, Vector((tx, ty, tz)), dist, lens)
# pose test
def rot(bn, e):
    pb = arm.pose.bones[bn]; pb.rotation_mode = 'XYZ'; pb.rotation_euler = [math.radians(x) for x in e]
rot('upperarm_l', (0, 0, 70)); rot('lowerarm_l', (0, 0, 70)); rot('upperarm_r', (0, 0, -70)); rot('lowerarm_r', (0, 0, -70))
rot('thigh_l', (-55, 0, 0)); rot('calf_l', (70, 0, 0)); rot('thigh_r', (35, 0, 0))
bpy.context.view_layer.update()
shot('pose', 35, Vector((0, 0, H * 0.5)), 5.0)
for pb in arm.pose.bones: pb.rotation_euler = (0, 0, 0)
print('DONE')
