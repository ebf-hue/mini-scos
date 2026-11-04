"""Check the reimported printable attachment against the existing hardware meshes."""
from pathlib import Path
import json,itertools
import numpy as np
import cadquery as cq
import trimesh
ROOT=Path(__file__).resolve().parent
BASE=ROOT.parents[1]/'14-wrist-architecture'/'parts'
OUT=ROOT/'meshes'
report=json.loads((ROOT/'sculpt-check.json').read_text())
def common(a,b):
 c=trimesh.boolean.intersection([a,b],engine='manifold')
 return 0. if c.is_empty else max(0.,float(c.volume))
def cad_mesh(name):
 p=OUT/f'ref-{name}.stl'
 if not p.exists():
  s=cq.importers.importStep(str(BASE/f'{name}.step')).val()
  s.exportStl(str(p),tolerance=.01,angularTolerance=.05,relative=False)
 m=trimesh.load_mesh(p,process=True)
 m.update_faces(m.nondegenerate_faces());m.remove_unreferenced_vertices()
 return m
full=trimesh.load_mesh(ROOT/'monster-attachment.stl',process=True)
assert full.is_watertight and full.is_volume and len(full.split())==1
names=['WristSaddle','CameraKeeper','LaserCap','LaserHousing','LaserInsert','LaserAperture','LaserWireRed','LaserWireBlack','BeamReference','ArmReference']
objects={name:cad_mesh(name) for name in names}
report['assembly_overlap_mm3']={}
for name,mesh in objects.items():
 v=common(full,mesh);report['assembly_overlap_mm3'][name]=v
 print('Final clearance',name,v,flush=True)
 assert v<.001,(name,v)
# Every original source solid is checked against the camera's continuous Y sweep.
candidates=[ROOT.parents[1]/'14-wrist-architecture'/'sources'/'Camera_module_3_std_model_simple.stp',ROOT.parents[1]/'13-bench-architecture'/'sources'/'Camera_module_3_std_model_simple.stp']
source=next((p for p in candidates if p.exists()),None)
if source is None:raise FileNotFoundError('Fetch the official source using 14-wrist-architecture/fetch_sources.py')
camera=cq.importers.importStep(str(source)).val()
pose=cq.Location(cq.Vector(-2.5,14.4,88),cq.Vector(0,0,1),-90)
hits=[];minz=1e10
for i,s in enumerate(camera.Solids()):
 b=s.moved(pose).BoundingBox();minz=min(minz,b.zmin)
 if b.zmin>full.bounds[1,2] or b.zmax<full.bounds[0,2] or b.xmin>full.bounds[1,0] or b.xmax<full.bounds[0,0]:continue
 box=trimesh.creation.box(extents=[max(b.xlen,.00001),b.ylen+35,max(b.zlen,.00001)])
 box.apply_translation([b.center.x,b.center.y-17.5,b.center.z])
 v=common(full,box)
 if v>.001:hits.append({'component':i,'overlap_mm3':v})
report['camera_insertion']={'source_solids':len(camera.Solids()),'travel_mm':35,'method':'Conservative continuous swept component boxes','intersections':hits,'minimum_camera_z_mm':minz,'attachment_max_z_mm':float(full.bounds[1,2])}
assert not hits,hits
# The attachment approaches from the front. Check actual meshes, not the render.
report['installation_samples']=[]
for travel in range(0,81,2):
 moved=full.copy();moved.apply_translation([0,-travel,0])
 overlaps={}
 for name,mesh in objects.items():
  if name=='ArmReference':continue
  if np.any(moved.bounds[1]<mesh.bounds[0]) or np.any(mesh.bounds[1]<moved.bounds[0]):continue
  v=common(moved,mesh)
  if v>.001:overlaps[name]=v
 assert not overlaps,(travel,overlaps)
 report['installation_samples'].append({'forward_offset_mm':travel,'collisions':overlaps})
print('Camera sweep and all 41 installation poses clear',flush=True)
# Reimport every colour export before pairwise collision checks.
regions={name:trimesh.load_mesh(OUT/f'{name}.ply',process=False) for name in ['SkinAndMount','IvoryEyesAndFangs','Pupils','Gum']}
report['exported_colour_overlap_mm3']={}
report['exported_colour_components']={}
for name,m in regions.items():
 components=m.split()
 report['exported_colour_components'][name]={'components':len(components),'volumes_mm3':sorted([float(c.volume) for c in components],reverse=True)}
 print('Colour region',name,len(components),'smallest',min(c.volume for c in components),flush=True)
for (a,ma),(b,mb) in itertools.combinations(regions.items(),2):
 v=common(ma,mb);report['exported_colour_overlap_mm3'][a+' / '+b]=v
 assert v<.001,(a,b,v)
(ROOT/'fit-check.json').write_text(json.dumps(report,indent=2))
print('Exported geometry passes; physical fit remains unverified',flush=True)
