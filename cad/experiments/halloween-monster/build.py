"""Removable Halloween mask for the current wrist saddle; no saddle edits."""
import json, math
from pathlib import Path
import cadquery as cq
import trimesh
from mcp_client import SolidCraft
ROOT=Path(__file__).resolve().parent
BASE=ROOT.parents[1]/'14-wrist-architecture'/'parts'
OUT=ROOT/'parts';OUT.mkdir(exist_ok=True)
def box(w,d,h,x,y,z):
 return cq.Workplane('XY').box(w,d,h,centered=(True,True,False)).val().translate((x,y,z))
def ellipse(rx,rz,y,length):
 return cq.Workplane(cq.Plane(origin=(0,y,36),xDir=(1,0,0),normal=(0,1,0))).ellipse(rx,rz).extrude(length).val()
def ball(r,x,y,z): return cq.Solid.makeSphere(r,cq.Vector(x,y,z),angleDegrees1=-90,angleDegrees2=90)
# Facial arch stays just ahead of the saddle, around rather than inside the arm.
face=ellipse(43,37,-47,6).cut(ellipse(36.8,27,-48,8)).cut(box(110,20,80,0,-44,-35))
# Two outer C-shoes slide over the existing strap ears from the front.
# Their open inner sides avoid the saddle wall; through-slots preserve the straps.
shoes=[]
for side in [-1,1]:
 x=side*35.15
 shoe=box(7.4,22,2.4,side*37.1,15,47.2).fuse(box(7.4,22,2.4,side*37.1,15,54.4))
 shoe=shoe.fuse(box(2.4,22,9.6,side*39.6,15,47.2))
 shoe=shoe.cut(box(4.2,17.2,14,side*34,15,46))
 # Trailing shoulder stops against the ear front after the open shoes slide on.
 shoe=shoe.fuse(box(4.6,2.4,4.8,side*38.5,2.4,49.6))
 shoes.append(shoe)
 # Broad side rail; teeth are decoration, the shoes carry the attachment.
 rail=box(3,61,4.8,side*39.9,-15.5,50)
 face=face.fuse(shoe).fuse(rail)
# Eyes merge into the upper lip. Keep everything below the camera loading plane.
eyes=[];pupils=[];brows=[]
for side in [-1,1]:
 x=side*23
 # Explicit stalk connects the elevated eye socket to the brow of the mouth.
 stalk=cq.Solid.makeLoft([cq.Workplane('XY').workplane(offset=z).center(x,-44).ellipse(rx,ry).val() for z,rx,ry in [(64,5,3),(70,4.3,3),(76,5,3.5)]])
 face=face.fuse(stalk)
 socket=ball(7.6,x,-44.5,76.6)
 face=face.fuse(socket)
 eye=ball(5.6,x,-49,77.2)
 eyes.append(eye)
 pupil=ball(2.3,x-side*.8,-53.7,77.2)
 pupils.append(pupil)
 # Heavy sloping brows give the little monster an expression.
 brow=box(13,4,3,x,-50.2,81).rotate((x,-50.2,82.5),(x,-49.2,82.5),side*10)
 brows.append(brow)
 face=face.fuse(brow)
# Six short blunt teeth end outside the nominal arm, not in its surface.
teeth=[]
for x in [-29,-19,-8,8,19,29]:
 skin=36+25*math.sqrt(1-(x/35)**2)
 tip_z=skin+3.2
 root_z=36+37*math.sqrt(1-(x/43)**2)-1.5
 tip_radius=1.6
 cone=cq.Solid.makeCone(3.5,tip_radius,root_z-tip_z,cq.Vector(x,-47,root_z),cq.Vector(0,0,-1))
 tooth=cone.fuse(ball(tip_radius,x,-47,tip_z))
 teeth.append(tooth)
# Fuse overlapping tools before partitioning the single attachment into colours.
def union(shapes):
 result=shapes[0]
 for item in shapes[1:]:result=result.fuse(item,tol=0.001)
 return result
white=union(eyes+teeth)
allshape=union([face]+eyes+teeth)
cleaned=allshape.clean()
if cleaned.isValid():allshape=cleaned
assert allshape.isValid() and len(allshape.Solids())==1
# Partition eye colours with a shared plane, avoiding intersecting spherical tools.
front_colour=box(100,20,50,0,-63.7,50)  # front face ends at Y=-53.7
black=cq.Compound.makeCompound([e.intersect(front_colour) for e in eyes])
cream=cq.Compound.makeCompound([e.cut(front_colour) for e in eyes]+teeth)
green=allshape.cut(*eyes,*teeth)
regions={'MonsterShell':green,'EyesAndTeeth':cream,'Pupils':black}
# Check both separate colour regions and every solid inside each region.
region_overlaps={}
from itertools import combinations
for name,shape in regions.items():
 assert shape.isValid(),name
 for i,j in combinations(range(len(shape.Solids())),2):
  v=shape.Solids()[i].intersect(shape.Solids()[j]).Volume()
  assert v<1e-5,(name,i,j,v)
for (a,x),(b,y) in combinations(regions.items(),2):
 v=sum(sx.intersect(sy).Volume() for sx in x.Solids() for sy in y.Solids());region_overlaps[a+' / '+b]=v
 assert v<1e-5,(a,b,v)
assert abs(sum(s.Volume() for s in regions.values())-allshape.Volume())<.01
checks={'valid':allshape.isValid(),'solids':len(allshape.Solids()),'volume_mm3':allshape.Volume(),
 'attachment':'Front-loading C-shoes over both existing strap ears; 0.4 mm top/bottom/outer clearance',
 'tooth_tip_radius_mm':1.6,'physical_fit':'Unverified; no slicing or print submission'}
checks['colour_region_overlap_mm3']=region_overlaps
arm=cq.importers.importStep(str(BASE/'ArmReference.step')).val()
checks['arm_overlap_mm3']=allshape.intersect(arm).Volume()
# Existing assembly and source optical references all remain unchanged.
obstacle_shapes={}
obstacles=['WristSaddle','CameraKeeper','LaserCap','LaserHousing','LaserInsert','LaserAperture','LaserWireRed','LaserWireBlack','BeamReference']
checks['assembly_overlap_mm3']={}
for name in obstacles:
 obj=cq.importers.importStep(str(BASE/f'{name}.step')).val()
 obstacle_shapes[name]=obj
 checks['assembly_overlap_mm3'][name]=allshape.intersect(obj).Volume()
assert checks['arm_overlap_mm3']<1e-5,checks
assert all(v<1e-5 for v in checks['assembly_overlap_mm3'].values()),checks
# Full camera component-box sweep, keeper removed, same insertion as base design.
source=ROOT.parents[1]/'13-bench-architecture'/'sources'/'Camera_module_3_std_model_simple.stp'
camera=cq.importers.importStep(str(source)).val()
pose=cq.Location(cq.Vector(-2.5,14.4,88),cq.Vector(0,0,1),-90)
hits=[]
for i,s in enumerate(camera.Solids()):
 b=s.moved(pose).BoundingBox()
 swept=cq.Solid.makeBox(max(b.xlen,1e-5),b.ylen+35,max(b.zlen,1e-5),cq.Vector(b.xmin,b.ymin-35,b.zmin))
 v=allshape.intersect(swept).Volume()
 if v>1e-5:hits.append({'component':i,'overlap_mm3':v})
assert allshape.BoundingBox().zmax<86.95
checks['camera_insertion']={'source_solids':len(camera.Solids()),'travel_mm':35,'intersections':hits}
assert not hits,hits
# Conservative attachment-motion check against the unmodified saddle.
saddle=cq.importers.importStep(str(BASE/'WristSaddle.step')).val()
checks['slide_on_samples']=[]
for travel in range(0,81,2):
 moved=allshape.translate((0,-travel,0))
 overlaps={name:moved.intersect(shape).Volume() for name,shape in obstacle_shapes.items()}
 assert all(v<1e-5 for v in overlaps.values()),(travel,overlaps)
 checks['slide_on_samples'].append({'forward_offset_mm':travel,'overlaps_mm3':overlaps})
cq.exporters.export(allshape,str(ROOT/'monster-attachment.step'))
# Flat face plane on the bed: front of monster down, slide rails build upwards.
printed=allshape.rotate((0,0,0),(1,0,0),90)
b=printed.BoundingBox();printed=printed.translate((-b.xmin,-b.ymin,-b.zmin))
printed.exportStl(str(ROOT/'monster-attachment.stl'),tolerance=.02,angularTolerance=.08,relative=False)
mesh=trimesh.load_mesh(ROOT/'monster-attachment.stl',process=True)
# OCC's spherical poles produce zero-area STL triangles; discard these only.
mesh.update_faces(mesh.nondegenerate_faces())
mesh.remove_unreferenced_vertices()
mesh.export(ROOT/'monster-attachment.stl')
checks['mesh']={'watertight':mesh.is_watertight,'consistent_winding':mesh.is_winding_consistent,'connected_components':len(mesh.split()),'size_mm':mesh.extents.tolist()}
print(checks['mesh'],flush=True)
assert checks['mesh']['watertight'] and checks['mesh']['consistent_winding'] and checks['mesh']['connected_components']==1
(ROOT/'checks.json').write_text(json.dumps(checks,indent=2))
for name,s in regions.items():cq.exporters.export(s,str(OUT/f'{name}.step'))
# Reimport exported STEP regions and verify every solid pair, not compounds only.
exported={n:cq.importers.importStep(str(OUT/f'{n}.step')).val() for n in regions}
checks['exported_colour_overlap_mm3']={}
for (a,x),(b,y) in combinations(exported.items(),2):
 v=sum(sx.intersect(sy).Volume() for sx in x.Solids() for sy in y.Solids())
 checks['exported_colour_overlap_mm3'][a+' / '+b]=v
 assert v<1e-5,(a,b,'exported overlap',v)
(ROOT/'checks.json').write_text(json.dumps(checks,indent=2))
print('Mask geometry, attachment travel, arm and camera clearances checked',flush=True)
server=SolidCraft()
def checked(r):
 if r.get('isError'):raise RuntimeError(str(r)[:2000])
try:
 commands=[]
 display={name:(BASE/f'{name}.step',color) for name,color in [('WristSaddle','#32383e'),('CameraKeeper','#545961'),('LaserCap','#545961'),('LaserHousing','#41464b'),('LaserWireRed','#b33437'),('LaserWireBlack','#202326'),('OfficialCM3_PCB','#168f59'),('OfficialCM3_LensHousing','#23262b'),('OfficialCM3_Connector','#ded9c7'),('ArmReference','#d1ae8e')]}
 display.update({n:(OUT/f'{n}.step',c) for n,c in [('MonsterShell','#76a94b'),('EyesAndTeeth','#f4e8c7'),('Pupils','#20232b')]})
 for name,(path,color) in display.items():
  before=json.loads(server.call('inspect_design',measure=False,sketches=False)['content'][0]['text'])
  old={b['name'] for b in before['bodies']}
  checked(server.call('execute',command='file.insert_step',params={'path':str(path),'name':name},verbose=False))
  after=json.loads(server.call('inspect_design',measure=False,sketches=False)['content'][0]['text'])
  new=[b['name'] for b in after['bodies'] if b['name'] not in old]
  checked(server.call('execute',command='appearance.assign',params={'bodies':new,'color':color},verbose=False))
 checked(server.call('execute',command='browser.visibility',params={'folder':'origin','visible':False},verbose=False))
 checked(server.call('save',path=str(ROOT/'monster-wrist.solidcraft')))
 for name,target,yaw,pitch,distance in [('monster-wrist',[0,-16,59],-.38,.29,270),('monster-face',[0,-38,61],0,.12,215),('monster-side',[0,-15,63],1.2,.18,240)]:
  checked(server.call('screenshot',source='model',camera={'target':target,'yaw':yaw,'pitch':pitch,'distance':distance,'fov':.65},grid=False,axes=False,width=1400,height=1000,path=str(ROOT/f'{name}.png')))
 print('Rendered monster wrist attachment',flush=True)
finally:server.close()
