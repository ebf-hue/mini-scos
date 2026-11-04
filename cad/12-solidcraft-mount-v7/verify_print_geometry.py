"""Check print-mesh connectedness, winding, and volume against its CAD solid."""
from pathlib import Path
import collections,struct,json
import cadquery as cq
ROOT=Path(__file__).resolve().parent;report={}
for name,path in [('Rest','surface_source/RestFinished.step'),('SpineCamera','camera_source/wide/SpineCamera.step'),('SpineCamera_standard','camera_source/standard/SpineCamera.step')]:
 d=(ROOT/'exports'/(name+'.stl')).read_bytes();n=struct.unpack_from('<I',d,80)[0];parent=list(range(n));edges=collections.defaultdict(list);volume=0
 def find(i):
  while parent[i]!=i:parent[i]=parent[parent[i]];i=parent[i]
  return i
 for i in range(n):
  p=struct.unpack_from('<9f',d,96+50*i);ps=[tuple(p[j:j+3]) for j in [0,3,6]]
  for a,b in zip(ps,ps[1:]+ps[:1]):edges[tuple(sorted([a,b]))].append((i,a,b))
  a,b,c=ps;volume+=(a[0]*(b[1]*c[2]-b[2]*c[1])+a[1]*(b[2]*c[0]-b[0]*c[2])+a[2]*(b[0]*c[1]-b[1]*c[0]))/6
 for refs in edges.values():
  assert len(refs)==2
  (i,a,b),(j,c,e)=refs;assert a==e and b==c,(name,'inconsistent winding')
  ri,rj=find(i),find(j)
  if ri!=rj:parent[ri]=rj
 components=len({find(i) for i in range(n)});assert components==1,(name,components)
 cad=cq.importers.importStep(str(ROOT/path)).val();g=GProp_GProps();integration_error=BRepGProp.VolumePropertiesGK_s(cad.wrapped,g,1e-6,True,True,False,False,False);cad_volume=g.Mass();error=abs(volume-cad_volume)/cad_volume;bound=cad.Area()*(.005 if name=='Rest' else .02)*1.1;assert abs(volume-cad_volume)<bound,(name,error,bound)
 report[name]={'connected_components':components,'consistent_outward_winding':True,'mesh_volume_mm3':volume,'cad_volume_mm3':cad_volume,'adaptive_integration_error':integration_error,'relative_volume_error':error,'volume_error_bound_mm3':bound,'bound_basis':'CAD surface area times 0.02 mm STL deflection plus 10 percent margin'}
(ROOT/'exports/print_geometry_check.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2))
