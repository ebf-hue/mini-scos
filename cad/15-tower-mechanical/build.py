"""Mechanical tower study: keyed frame, camera support plate and removable retainer.
All rigid custom parts printed; this is not a sliced or validated optical instrument.
"""
import json, math
from pathlib import Path
import cadquery as cq
from mcp_client import SolidCraft
ROOT=Path(__file__).resolve().parent;OUT=ROOT/'parts';OUT.mkdir(exist_ok=True)
SKIN_Z=61
CAM_Z=165
FRAME_BOTTOM=70
PLATE_BOTTOM=CAM_Z-8.5
PLATE_TOP=CAM_Z-2.5
FRAME_TOP=PLATE_BOTTOM
PIN_CLEARANCE=.2
SIDE_X=29
FOOT_Y=22
parts={}
def box(w,d,h,x=0,y=0,z=0):return cq.Workplane('XY').box(w,d,h,centered=(True,True,False)).val().translate((x,y,z))
def arm(rx,rz,y,length):return cq.Workplane(cq.Plane(origin=(0,y,36),xDir=(1,0,0),normal=(0,1,0))).ellipse(rx,rz).extrude(length).val()
def bar(p1,p2,width,thickness,normal):
 p1,p2=cq.Vector(*p1),cq.Vector(*p2)
 v=p2-p1
 plane=cq.Plane(origin=p1,xDir=v.normalized(),normal=normal)
 return cq.Workplane(plane).center(v.Length/2,0).rect(v.Length,width).extrude(thickness/2,both=True).val()
def xhole(x,y,z,r=2.2,length=20):return cq.Solid.makeCylinder(r,length,cq.Vector(x,y,z),cq.Vector(1,0,0))
def pin_x(name,x,y,z,d,length,direction=1):
 shaft=cq.Solid.makeCylinder(d/2,length,cq.Vector(x,y,z),cq.Vector(direction,0,0))
 head=cq.Solid.makeCylinder(d*.85,2,cq.Vector(x,y,z),cq.Vector(-direction,0,0))
 parts[name]=shaft.fuse(head).clean()
 return parts[name]
# Broad saddle with two straps; flat structural pads above the curved skin relief.
base=arm(39,28,-40,80).cut(arm(35.5,25.5,-41,82)).cut(box(110,84,70,z=-20))
for x in [-SIDE_X,SIDE_X]:
 base=base.fuse(box(15,64,15,x,0,55))
 for y in [-FOOT_Y,FOOT_Y]:
  base=base.cut(box(6.4,14.4,10.2,x,y,59.9))
  base=base.cut(xhole(x-10,y,65))
for y in [-30,30]:
 for x in [-37,37]:
  base=base.fuse(box(13,14,4,x,y,51))
  base=base.cut(box(3.5,10,6,x,y,50))
base=base.cut(arm(35.5,25.5,-41,82)).clean()
# Two matching side trusses and an integral rear X brace. All webs have defined
# section sizes. Keys locate the top and bottom joints; cross-pins stop withdrawal.
frame=None
for x in [-SIDE_X,SIDE_X]:
 side=box(6,60,8,x,0,FRAME_BOTTOM)
 for y in [-26,26]:side=side.fuse(box(6,8,FRAME_TOP-FRAME_BOTTOM,x,y,FRAME_BOTTOM))
 side=side.fuse(box(6,60,8,x,0,FRAME_TOP-8))
 side=side.fuse(bar((x,-22,78),(x,22,FRAME_TOP-8),7,6,(1,0,0)))
 for y in [-FOOT_Y,FOOT_Y]:
  side=side.fuse(box(6,14,10,x,y,60))
  side=side.cut(xhole(x-5,y,65))
  side=side.fuse(box(6,14,6,x,y,FRAME_TOP))
  side=side.cut(xhole(x-5,y,FRAME_TOP+3,1.8))
 frame=side if frame is None else frame.fuse(side)
for p1,p2 in [((-29,27,78),(29,27,FRAME_TOP-8)),((29,27,78),(-29,27,FRAME_TOP-8))]:
 frame=frame.fuse(bar(p1,p2,7,6,(0,1,0)))
# Open the left lower bay for the independent base-mounted laser bracket.
frame=frame.cut(box(8,32,8.5,-SIDE_X,0,FRAME_BOTTOM)).clean()
# Camera carrier has a 42 mm through aperture: lens passes through from above.
plate=box(70,70,6,z=PLATE_BOTTOM).cut(cq.Solid.makeCylinder(21,8,cq.Vector(0,0,PLATE_BOTTOM-1)))
for x in [-SIDE_X,SIDE_X]:
 for y in [-FOOT_Y,FOOT_Y]:
  plate=plate.cut(box(6.4,14.4,7,x,y,PLATE_BOTTOM-.5))
  plate=plate.cut(xhole(x-9,y,FRAME_TOP+3,1.8))
# Retainer feet are outside the camera board; holes are independent of its tiny holes.
for x in [-23,23]:
 for y in [-10,10]:
  plate=plate.cut(box(6.4,6.4,7,x,y,PLATE_BOTTOM-.5))
  plate=plate.cut(xhole(-40,y,PLATE_BOTTOM+3,1.8,80))
plate=plate.clean()
retainer=box(54,54,3,z=CAM_Z-.65).cut(box(31,31,5,z=CAM_Z-1.65))
# Ribbon notch at the front: connector stays accessible without removing the board.
retainer=retainer.cut(box(25,15,5,0,-21,CAM_Z-1.65))
for x in [-23,23]:
 for y in [-10,10]:
  retainer=retainer.fuse(box(6,6,CAM_Z-.65-PLATE_BOTTOM,x,y,PLATE_BOTTOM))
  retainer=retainer.cut(xhole(x-4,y,PLATE_BOTTOM+3,1.8,8))
retainer=retainer.clean()
parts.update({'WristBase':base,'BracedFrame':frame,'CameraPlate':plate,'CameraRetainer':retainer})
# Reusable headed cross-pins. Clearance rather than friction establishes assembly;
# pullout retention of pins still needs a physical prototype/detent revision.
for side in [-1,1]:
 for j,y in enumerate([-FOOT_Y,FOOT_Y]):
  pin_x(f'BasePin{side}_{j}',side*39,y,65,4,20,-side)
  pin_x(f'PlatePin{side}_{j}',side*39,y,FRAME_TOP+3,3.2,19,-side)
 for j,y in enumerate([-10,10]):
  pin_x(f'RetainerPin{side}_{j}',side*36,y,PLATE_BOTTOM+3,3.2,18,-side)
# Laser clamp on a flat foot and two triangular gussets; no arbitrary pedestal.
q=math.sqrt(.5);axis=cq.Vector(q,0,-q);up=cq.Vector(q,0,q)
tip=cq.Vector(-8,0,69);target=cq.Vector(0,0,61);lc=tip-axis*16.4
start=lc-axis*10
ring=cq.Solid.makeCylinder(8.5,20,start,axis).cut(cq.Solid.makeCylinder(5.3,20,start,axis))
plane=cq.Plane(origin=start,xDir=(0,-1,0),normal=axis)
lower=cq.Workplane(plane).center(0,20).rect(60,40).extrude(20).val()
clamp=ring.intersect(lower)
cap=ring.cut(lower).translate(up*.15)
laser_foot=box(30,30,4,-25,0,70)
for y in [-8,8]:
 p=cq.Plane(origin=(0,y,0),xDir=(1,0,0),normal=(0,-1,0))
 gusset=cq.Workplane(p).polyline([(-39,74),(-13,74),(-28,87)]).close().extrude(2,both=True).val()
 laser_foot=laser_foot.fuse(gusset)
clamp=clamp.fuse(laser_foot)
# Registration keys to the base, inserted vertically; cap remains removable.
for y in [-12,12]:
 clamp=clamp.fuse(cq.Solid.makeCylinder(1.9,6,cq.Vector(-32,y,64)))
 base=base.cut(cq.Solid.makeCylinder(2.1,6.1,cq.Vector(-32,y,63.9)))
for side in [-1,1]:
 p=lc+cq.Vector(0,side*6.8,0)
 cap=cap.fuse(cq.Solid.makeCylinder(.85,3,p+up*.15,-up))
 clamp=clamp.cut(cq.Solid.makeCylinder(1,3.2,p+up*.05,-up))
clamp=clamp.cut(cq.Solid.makeCylinder(5.3,40,tip-axis*36,axis)).cut(cap).clean()
cap=cap.clean();base=base.clean()
parts['WristBase']=base
parts['BracedFrame']=frame
parts['LaserBracket']=clamp;parts['LaserCap']=cap
# Supplier references: complete camera including open board shells.
raw=cq.importers.importStep(str(ROOT/'sources/imx296-with-cs.step')).val()
def pose(s):return s.rotate((0,0,0),(0,1,0),180).translate((0,0,CAM_Z))
camera=pose(raw)
cb=pose(box(39,39,1.6,z=.9))
camera_check=cq.Compound.makeCompound([cb]+[pose(s) for s in raw.Solids()])
adapter=cq.Solid.makeCylinder(15.5,5.026,cq.Vector(0,0,CAM_Z-17.2),cq.Vector(0,0,-1))
lens_front=CAM_Z-72.226
lens_envelope=cq.Solid.makeCylinder(19.5,50,cq.Vector(0,0,CAM_Z-22.226),cq.Vector(0,0,-1))
parts['CameraReference']=camera;parts['CAdapterEnvelope']=adapter
for name in ['LensRearBody','ApertureRing','FocusRing','BlueTrim','FrontBarrel','FrontRim','FrontGlass']:
 s=cq.importers.importStep(str(ROOT/'sources/lens-visual'/f'{name}.step')).val()
 s=s.translate((0,32,-93)).rotate((0,0,0),(1,0,0),98)
 parts[name]=pose(s)
laser_raw=cq.importers.importStep(str(ROOT/'sources/laser_1054.step')).val()
laser=laser_raw.rotate((0,0,0),(0,1,0),-45).translate(tip)
parts['LaserReference']=laser
wrist=arm(35,25,-85,170);parts['ArmReference']=wrist
for i,y in enumerate([-30,30]):parts[f'Strap{i}']=arm(36.2,26.2,y-5,10).cut(arm(35.1,25.1,y-6,12))
# No drawing is released on appearance alone. Fixed contacts are allowed only at
# zero volume; full camera solids plus a board envelope check the open STEP shells.
printed=['WristBase','BracedFrame','CameraPlate','CameraRetainer','LaserBracket','LaserCap']
report={'study_only':True,'camera_source':'user confirmed IMX296 With CS.stp',
 'parameters_mm':{'camera_origin_z':CAM_Z,'wrist_top_z':61,'lens_front_gap':lens_front-61,'carrier_aperture_diameter':42,'source_board_width':39,'source_hole_spacing':34,'source_hole_diameter':2,'side_frame_spacing':58,'frame_section':6,'strap_spacing':60},
 'optics':'Compact fit position; 0.20 m listed lens minimum object distance not established. Measure before fixing optical height.',
 'load_case':{'assumed_total_top_mass_kg':.2,'lateral_acceleration_g':3,'lateral_force_N':.2*9.81*3,'overturning_moment_Nm':.2*9.81*3*(CAM_Z-61)/1000,'strap_couple_force_N':.2*9.81*3*(CAM_Z-61)/60,'meaning':'Design scenario only; no FEA or strength validation'},
 'printed_parts':{},'overlaps':[]}
for n in printed:
 s=parts[n];b=s.BoundingBox()
 report['printed_parts'][n]={'valid':s.isValid(),'solids':len(s.Solids()),'bbox_mm':[b.xmin,b.ymin,b.zmin,b.xmax,b.ymax,b.zmax]}
 assert s.isValid() and len(s.Solids())==1,(n,report['printed_parts'][n])
for i,n in enumerate(printed):
 for m in printed[i+1:]:
  v=parts[n].intersect(parts[m]).Volume()
  if v>1e-4:report['overlaps'].append([n,m,v])
 for m,h in [('camera',camera_check),('adapter',adapter),('lens envelope',lens_envelope),('laser',laser),('wrist',wrist)]:
  v=parts[n].intersect(h).Volume()
  if v>1e-4:report['overlaps'].append([n,m,v])
# A top-loading assembly path with the retainer and lens already on the camera.
# Retainer is removed first; frame and carrier remain installed.
report['camera_loading']={'method':'11 exact-solid samples across a 100 mm vertical insertion path, not a continuous sweep','retainer_removed':True,'collisions':[]}
for dz in range(0,101,10):
 for n in ['BracedFrame','CameraPlate','LaserBracket','LaserCap']:
  for m,h in [('camera',camera_check),('lens',lens_envelope),('adapter',adapter)]:
   v=parts[n].intersect(h.translate((0,0,dz))).Volume()
   if v>1e-4:report['camera_loading']['collisions'].append([dz,n,m,v])
(ROOT/'mechanical-check.json').write_text(json.dumps(report,indent=2))
print(json.dumps(report,indent=2),flush=True)
assert not report['overlaps'],report['overlaps']
assert not report['camera_loading']['collisions'],report['camera_loading']['collisions']
for n,s in parts.items():cq.exporters.export(s,str(OUT/f'{n}.step'))
colors={'WristBase':'#737e89','BracedFrame':'#d4dade','CameraPlate':'#8c9aa5','CameraRetainer':'#bd9052','LaserBracket':'#8c9aa5','LaserCap':'#bd9052','CameraReference':'#228459','LaserReference':'#494f57','ArmReference':'#c7ac91','BlueTrim':'#29a4b7','FrontGlass':'#173d39','Strap0':'#303840','Strap1':'#303840'}
def check(r):
 if r.get('isError'):raise RuntimeError(str(r)[:1500])
srv=SolidCraft()
try:
 cmds=[]
 for n in parts:
  cmds.extend([{'command':'file.insert_step','params':{'path':str(OUT/f'{n}.step'),'name':n}},{'command':'appearance.assign','params':{'components':[n],'color':colors.get(n,'#c49b58' if 'Pin' in n else '#30373e')}}])
 cmds.append({'command':'browser.visibility','params':{'folder':'origin','visible':False}})
 check(srv.call('batch',commands=cmds,verbose=False))
 check(srv.call('save',path=str(ROOT/'tower-mechanical.solidcraft')))
 check(srv.call('export',path=str(ROOT/'tower-mechanical.step')))
 for name,target_,yaw,pitch,distance in [('assembly',[0,0,100],-.64,.36,320),('front',[0,0,107],0,.10,300),('side',[0,0,106],1.57,.12,300)]:
  check(srv.call('screenshot',source='model',camera={'target':target_,'yaw':yaw,'pitch':pitch,'distance':distance,'fov':.65},grid=False,axes=False,width=1600,height=1200,path=str(ROOT/f'{name}.png')))
  print('rendered',name,flush=True)
finally:srv.close()
