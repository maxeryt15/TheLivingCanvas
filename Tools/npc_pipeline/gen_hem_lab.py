"""Laboratorio de pesos del dobladillo de Gen (variantes setw)."""
import bpy,sys,collections,itertools,json
sys.path.insert(0,r'D:\TheLivingCanvas\Tools\npc_pipeline')
import pose_lib as PL, layer_clip_scan as LC, penetration_sweep as PS
ob,me,U,L,fu,fl=LC.setup('Gen'); arm=bpy.data.objects['Gen_Rig']
hem=[i for i in U if me.vertices[i].co.z<0.97]; hemset=set(hem)
orig={i:{ob.vertex_groups[g.group].name:g.weight for g in me.vertices[i].groups} for i in hem}
co={i:me.vertices[i].co.copy() for i in hem}
zmin=min(c.z for c in co.values())
E=[(e.vertices[0],e.vertices[1]) for e in me.edges if e.vertices[0] in hemset and e.vertices[1] in hemset]
L0={e:(co[e[0]]-co[e[1]]).length for e in E}
def setw(ztop,tmax,xs,cf):
    for i in hem:
        c=co[i]; z=c.z
        cur=orig[i]
        if z>=ztop: w=cur
        else:
            x=(ztop-z)/(ztop-zmin); t=tmax*(x*x*(3-2*x))
            u=min(1.0,abs(c.x)/max(cf,1e-6)) if cf>0 else 1.0; t*= (0.3+0.7*(u*u*(3-2*u)))   # menos influencia en el centro
            wl=0.5+0.5*max(-1,min(1,c.x/xs)); wr=1-wl
            new=collections.Counter()
            for b,v in cur.items(): new[b]+=(1-t)*v
            new['thigh_l']+=t*wl; new['thigh_r']+=t*wr
            top=sorted(new.items(),key=lambda kv:-kv[1])[:4]; s=sum(v for _,v in top); w={b:v/s for b,v in top if v/s>0.01}
        for g in list(me.vertices[i].groups): ob.vertex_groups[g.group].remove([i])
        for b,v in w.items(): ob.vertex_groups[b].add([i],v,'REPLACE')
