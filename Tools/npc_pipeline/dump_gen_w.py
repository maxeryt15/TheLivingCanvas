import bpy,sys,json
ob=bpy.data.objects['Gen_Mesh']; out=sys.argv[sys.argv.index('--')+1]
d={i:{ob.vertex_groups[g.group].name:g.weight for g in v.groups} for i,v in enumerate(ob.data.vertices)}
json.dump(d,open(out,'w')); print('DUMPED',len(d))
