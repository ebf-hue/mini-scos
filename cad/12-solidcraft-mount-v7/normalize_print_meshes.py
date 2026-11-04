"""Normalize bounded STL export artifacts without changing the CAD design.
Cancel opposite coincident facets and remove zero-area facets. Permit only a
single triangular tessellation gap below 0.05 mm span / 0.0001 mm² area.
No vertices are moved, and no larger opening is filled.
"""
import collections,json,math,struct
from pathlib import Path
ROOT=Path(__file__).resolve().parent;OUT=ROOT/'exports'
def cross(a,b,c):
 u=[b[i]-a[i] for i in range(3)];v=[c[i]-a[i] for i in range(3)]
 return [u[1]*v[2]-u[2]*v[1],u[2]*v[0]-u[0]*v[2],u[0]*v[1]-u[1]*v[0]]
def volume(faces):
 return sum((a[0]*(b[1]*c[2]-b[2]*c[1])+a[1]*(b[2]*c[0]-b[0]*c[2])+a[2]*(b[0]*c[1]-b[1]*c[0]))/6 for a,b,c in faces)
def edges(faces):
 result=collections.defaultdict(list)
 for i,ps in enumerate(faces):
  for a,b in zip(ps,ps[1:]+ps[:1]):result[tuple(sorted([a,b]))].append((i,a,b))
 return result
report={}
for name in ['Rest','SpineCamera','SpineCamera_standard']:
 p=OUT/(name+'.stl');data=p.read_bytes();count=struct.unpack_from('<I',data,80)[0];groups=collections.defaultdict(lambda:[[],[]]);degenerate=0;original=[]
 for i in range(count):
  v=struct.unpack_from('<9f',data,96+50*i);ps=[tuple(v[j:j+3]) for j in [0,3,6]];original.append(ps)
  if len(set(ps))<3 or sum(v*v for v in cross(*ps))==0:degenerate+=1;continue
  order=sorted(ps);perm=[order.index(v) for v in ps];parity=sum(perm[a]>perm[b] for a in range(3) for b in range(a+1,3))%2
  groups[tuple(order)][parity].append(ps)
 faces=[];opposite=0;t_splits=0
 for group in groups.values():
  cancel=min(map(len,group));opposite+=2*cancel
  faces.extend(group[0][cancel:]);faces.extend(group[1][cancel:])
 es=edges(faces);bad={e:refs for e,refs in es.items() if len(refs)!=2};patches=[]
 if bad:
  assert len(bad)==3 and all(len(r)==1 for r in bad.values()),(name,'unexpected nonmanifold mesh',len(bad))
  vertices=set(v for edge in bad for v in edge);assert len(vertices)==3
  _,a,b=next(iter(bad.values()))[0];c=next(v for v in vertices if v!=a and v!=b)
  patch=[b,a,c];span=max(math.dist(a,b) for a,b in bad);area=math.sqrt(sum(v*v for v in cross(*patch)))/2
  assert span<.05 and area<.0001,(name,span,area)
  if area==0:
   # A zero-area export facet leaves a T-junction: split its opposite
   # adjacent face at the already existing, exactly collinear vertex.
   long=max(bad,key=lambda e:math.dist(*e));mid=next(v for v in vertices if v not in long)
   idx,a,c=bad[long][0];d=next(v for v in faces[idx] if v!=a and v!=c)
   faces[idx]=[a,mid,d];faces.append([mid,c,d]);t_splits+=1
  else:
   faces.append(patch);patches.append({'span_mm':span,'area_mm2':area})

 assert all(len(r)==2 for r in edges(faces).values()),name
 assert all(len(set(p))==3 and sum(v*v for v in cross(*p))>0 for p in faces),name
 drift=abs(volume(faces)-volume(original));assert drift<.001,(name,drift)
 original_bounds=[[min(p[k] for ps in original for p in ps) for k in range(3)],[max(p[k] for ps in original for p in ps) for k in range(3)]]
 final_bounds=[[min(p[k] for ps in faces for p in ps) for k in range(3)],[max(p[k] for ps in faces for p in ps) for k in range(3)]]
 assert final_bounds==original_bounds,name
 blob=bytearray(data[:80])+struct.pack('<I',len(faces))
 for ps in faces:
  n=cross(*ps);length=math.sqrt(sum(v*v for v in n));n=[v/length for v in n]
  blob.extend(struct.pack('<12fH',*n,*[v for p in ps for v in p],0))
 p.write_bytes(blob)
 report[name]={'input_triangles':count,'output_triangles':len(faces),'zero_area_triangles_removed':degenerate,'opposite_coincident_triangles_cancelled':opposite,'collinear_t_junctions_split':t_splits,'micro_tessellation_closures':patches,'vertex_positions_changed':False,'bounds_changed':False,'signed_volume_drift_mm3':drift,'all_edges_two_sided':True}
(OUT/'mesh_normalization.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2))
