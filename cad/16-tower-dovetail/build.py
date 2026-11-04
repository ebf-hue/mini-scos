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
# Profile-extruded dovetails. Clearance is per side, not diametral.
def dt_y(x,y0,length,z0,z1,neck,head,upward=False):
    # Positive z1-z0; bottom is wide for base feet, top is wide for carrier rails.
    bottom,top=(neck,head) if upward else (head,neck)
    plane=cq.Plane(origin=(x,y0,0),xDir=(1,0,0),normal=(0,-1,0))
    return cq.Workplane(plane).polyline([(-bottom/2,z0),(bottom/2,z0),(top/2,z1),(-top/2,z1)]).close().extrude(-length).val()
def dt_x(y,x0,length,z0,z1,neck,head):
    plane=cq.Plane(origin=(x0,y,0),xDir=(0,1,0),normal=(1,0,0))
    return cq.Workplane(plane).polyline([(-head/2,z0),(head/2,z0),(neck/2,z1),(-neck/2,z1)]).close().extrude(length).val()
def tooth_y(x,y0,z0,width=2.4,reverse=False):
    plane=cq.Plane(origin=(x,0,0),xDir=(0,1,0),normal=(1,0,0))
    pts=[(y0,z0),(y0,z0+1.7),(y0+3,z0+1.7)] if not reverse else [(y0,z0+1.7),(y0+3,z0),(y0+3,z0+1.7)]
    return cq.Workplane(plane).polyline(pts).close().extrude(width/2,both=True).val()
base=arm(39,28,-40,80).cut(arm(35.5,25.5,-41,82)).cut(box(110,84,70,z=-20))
for x in [-SIDE_X,SIDE_X]:base=base.fuse(box(15,80,15,x,0,55))
# Separate laser docking land; its lateral key can enter through the open frame bay.
base=base.fuse(box(24,28,12,-30,0,58))
for x in [-SIDE_X,SIDE_X]:
    base=base.cut(dt_y(x,-40.2,69.5,60.75,66.25,6.5,10.5))
    base=base.cut(box(6.5,69.5,4.2,x,-5.45,66))
for y in [-30,30]:
 for x in [-37,37]:
    base=base.fuse(box(13,14,4,x,y,51))
    base=base.cut(box(3.5,10,6,x,y,50))
# Catch pocket for the frame's integral cantilever, beside the right rail mouth.
base=base.cut(box(3,3.6,2,34.8,-36.5,68.4))
base=base.cut(arm(35.5,25.5,-41,82)).clean()
frame=None
for x in [-SIDE_X,SIDE_X]:
 side=box(6,60,8,x,0,FRAME_BOTTOM)
 for y in [-26,26]:side=side.fuse(box(6,8,FRAME_TOP-FRAME_BOTTOM,x,y,FRAME_BOTTOM))
 side=side.fuse(box(6,60,8,x,0,FRAME_TOP-8))
 side=side.fuse(bar((x,-22,108 if x<0 else 78),(x,22,FRAME_TOP-8),7,6,(1,0,0)))
 for y in [-FOOT_Y,FOOT_Y]:
    side=side.fuse(dt_y(x,y-7,14,61,66,6,10))
    side=side.fuse(box(6,14,4.1,x,y,65.9))
 # Short upward-facing dovetail rail at each side of the top bridge.
 side=side.fuse(dt_y(x,-28,56,FRAME_TOP,FRAME_TOP+3.5,6,10,True))
 frame=side if frame is None else frame.fuse(side)
for p1,p2 in [((-29,27,78),(29,27,FRAME_TOP-8)),((29,27,78),(-29,27,FRAME_TOP-8))]:
 frame=frame.fuse(bar(p1,p2,7,6,(0,1,0)))
frame=frame.cut(box(8,32,8.5,-SIDE_X,0,FRAME_BOTTOM)).clean()
# The frame's release tab sits outside the rail; lift its front end to withdraw.
frame_tooth=tooth_y(34.8,-38,69)
frame=frame.fuse(box(6.2,5,3,33.5,-18.5,70.7))
frame=frame.fuse(box(2.4,21,1.4,34.8,-28.5,70.7)).fuse(box(3.2,3,1.4,34.8,-39.5,70.7)).clean()
frame_rigid=frame
frame=frame.fuse(frame_tooth).clean()
# Plate catch boss is attached to the right front post, outside the plate rail.
frame=frame.fuse(box(13,8,5,37.5,-28,FRAME_TOP-5))
frame=frame.cut(box(3,3.6,2,41.5,-29.5,FRAME_TOP-1.6)).clean()
# The receiver enters the fixed frame rails from the front and closes against a stop.
plate=box(78,70,6,z=PLATE_BOTTOM).cut(cq.Solid.makeCylinder(21,8,cq.Vector(0,0,PLATE_BOTTOM-1)))
for x in [-SIDE_X,SIDE_X]:
    plate=plate.cut(dt_y(x,-28.3,63.5,PLATE_BOTTOM-.25,PLATE_BOTTOM+3.75,6.5,10.5,True))
# Upper rails carry a rear-loading U retainer, clear of the camera board's edges.
for x in [-26.5,26.5]:plate=plate.fuse(dt_y(x,-23,46,PLATE_TOP,PLATE_TOP+3.5,5,8,True))
plate=plate.cut(box(3,3.6,2,36.2,28.5,PLATE_TOP-1.6))
plate=plate.fuse(box(6,5,3,39.5,-10,PLATE_BOTTOM+.7))
plate=plate.fuse(box(2.4,21,1.4,41.5,-20.5,PLATE_BOTTOM+.7)).fuse(box(3.2,3,1.4,41.5,-32.5,PLATE_BOTTOM+.7)).clean()
plate_tooth=tooth_y(41.5,-31,PLATE_BOTTOM-1)
plate_rigid=plate
plate=plate.fuse(plate_tooth).clean()
# Retainer slides from the rear toward the front. The rear bar stays behind the
# ribbon connector and its open notch leads the motion.
retainer=box(66,54,4,z=CAM_Z-.65).cut(box(31,31,6,z=CAM_Z-1.65))
retainer=retainer.cut(box(25,15,6,0,-21,CAM_Z-1.65))
for x in [-26.5,26.5]:
    retainer=retainer.fuse(box(12,56,5.65,x,0,PLATE_TOP+.2))
    retainer=retainer.cut(dt_y(x,-28.2,51.5,PLATE_TOP-.25,PLATE_TOP+3.75,5.5,8.5,True))
retainer=retainer.fuse(box(6.2,5,4,34.3,9.5,CAM_Z-.65))
retainer=retainer.fuse(box(2.4,21,1.4,36.2,20.5,PLATE_TOP+.7)).fuse(box(3.2,3,1.4,36.2,32.5,PLATE_TOP+.7)).clean()
retainer_tooth=tooth_y(36.2,27,PLATE_TOP-1,reverse=True)
retainer_rigid=retainer
retainer=retainer.fuse(retainer_tooth).clean()
parts.update({'WristBase':base,'BracedFrame':frame,'CameraPlate':plate,'CameraRetainer':retainer})
# Laser clamp on a flat foot and two triangular gussets; no arbitrary pedestal.
q=math.sqrt(.5);axis=cq.Vector(q,0,-q);up=cq.Vector(q,0,q)
tip=cq.Vector(-14,0,75);target=cq.Vector(0,0,61);lc=tip-axis*16.4
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
# Lateral sliding dovetail for the laser bracket: no locating pegs.
base=base.cut(dt_x(0,-42.2,22.5,60.75,66.25,6.5,10.5)).cut(box(22.5,6.5,4.2,-30.95,0,66))
clamp=clamp.fuse(dt_x(0,-40,20,61,66,6,10)).fuse(box(20,6,4.1,-30,0,65.9))
# Free a cantilever from the bracket's flat foot; latch lies inside the frame bay.
clamp=clamp.cut(box(24,4.4,5,-29,10,69.7))
clamp=clamp.fuse(box(22,2.4,1.4,-28,10,70.7)).fuse(box(3,3.2,1.4,-39.5,10,70.7)).clean()
# Same tooth profile, rotated from a +Y slide to the +X laser docking direction.
laser_tooth=tooth_y(-10,-38,69).rotate((0,0,0),(0,0,1),-90)
laser_tooth=laser_tooth.translate((0,0,0))
clamp_rigid=clamp
clamp=clamp.fuse(laser_tooth)
base=base.cut(box(3.6,3,2,-36.5,10,68.4)).clean()
# Miniature dovetail rails hold the laser cap. It slides axially from the rear;
# an end stop locates it. Its printed fit still requires a coupon/grip test.
cp=cq.Plane(origin=start,xDir=(0,1,0),normal=axis)
for side in [-1,1]:
    yc=side*6.8
    male=cq.Workplane(cp).polyline([(yc-.8,0),(yc+.8,0),(yc+1.3,2.5),(yc-1.3,2.5)]).close().extrude(18).val().translate(axis)
    clamp=clamp.fuse(male)
    flange=cq.Workplane(cp).center(yc,2.15).rect(5,4).extrude(20).val()
    cap=cap.fuse(flange)
    female=cq.Workplane(cp).polyline([(yc-1,.0),(yc+1,.0),(yc+1.5,2.75),(yc-1.5,2.75)]).close().extrude(19.5).val().translate(axis*.7)
    cap=cap.cut(female)
clamp=clamp.cut(cq.Solid.makeCylinder(5.3,40,tip-axis*36,axis)).cut(cap).clean()
cap=cap.cut(cq.Solid.makeCylinder(5.3,40,tip-axis*36,axis)).clean();base=base.clean()
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
 'parameters_mm':{'joint_clearance_per_side':.25,'camera_origin_z':CAM_Z,'wrist_top_z':61,'lens_front_gap':lens_front-61,'carrier_aperture_diameter':42,'source_board_width':39,'source_hole_spacing':34,'source_hole_diameter':2,'side_frame_spacing':58,'frame_section':6,'strap_spacing':60},
 'optics':'Compact fit position; 0.20 m listed lens minimum object distance not established. Measure before fixing optical height.',
 'load_case':{'assumed_total_top_mass_kg':.2,'lateral_acceleration_g':3,'lateral_force_N':.2*9.81*3,'overturning_moment_Nm':.2*9.81*3*(CAM_Z-61)/1000,'strap_couple_force_N':.2*9.81*3*(CAM_Z-61)/60,'meaning':'Design scenario only; no FEA or strength validation'},
 'printed_parts':{},'overlaps':[],'retention':'Three main joints and laser foot use integral release tabs; laser cap dovetail grip requires a physical fit test'}
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
report['joint_paths']={'method':'sampled rigid geometry; integral ramp teeth excluded because they intentionally deflect during engagement','required_tab_deflection_mm':1.0,'paths':{},'collisions':[]}
# Include the finished catch boss in the frame motion model, excluding its tooth.
frame_rigid=frame.cut(frame_tooth)
plate_rigid=plate.cut(plate_tooth)
retainer_rigid=retainer.cut(retainer_tooth)
clamp_rigid=clamp.cut(laser_tooth)
for name,moving,fixed,delta in [
 ('frame_into_base',frame_rigid,[base],(0,-80,0)),
 ('plate_onto_frame',plate_rigid,[frame],(0,-75,0)),
 ('retainer_over_camera',retainer_rigid,[plate,camera_check,frame],(0,65,0)),
 ('laser_bracket_side_entry',clamp_rigid.fuse(cap).fuse(laser),[base,frame],(-65,0,0)),
 ('laser_cap_axial_entry_before_installation',cap,[clamp,laser],tuple(-axis*25)),
]:
    report['joint_paths']['paths'][name]={'entry_offset_mm':delta,'samples':21}
    for k in range(21):
        offset=tuple(v*(1-k/20) for v in delta)
        sh=moving.translate(offset)
        for j,ob in enumerate(fixed):
            overlap=sh.intersect(ob).Volume()
            if overlap>1e-4:report['joint_paths']['collisions'].append([name,k,j,overlap])
(ROOT/'mechanical-check.json').write_text(json.dumps(report,indent=2))
print('overlaps',report['overlaps'],flush=True)
print('path collisions',report['joint_paths']['collisions'][:12],flush=True)
for n,m,v in report['overlaps']:
 if n in parts and m in parts:
  overlap=parts[n].intersect(parts[m]);bb=overlap.BoundingBox();print('overlap bounds',n,m,[bb.xmin,bb.ymin,bb.zmin,bb.xmax,bb.ymax,bb.zmax],flush=True)
for n,shape in parts.items():cq.exporters.export(shape,str(OUT/f'{n}.step'))
assert not report['overlaps'],report['overlaps']
assert not report['camera_loading']['collisions'],report['camera_loading']['collisions']
assert not report['joint_paths']['collisions'],report['joint_paths']['collisions']
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
 check(srv.call('save',path=str(ROOT/'tower-dovetail.solidcraft')))
 check(srv.call('export',path=str(ROOT/'tower-dovetail.step')))
 for name,target_,yaw,pitch,distance in [('assembly',[0,0,100],-.64,.36,320),('front',[0,0,107],0,.10,300),('side',[0,0,106],1.57,.12,300)]:
  check(srv.call('screenshot',source='model',camera={'target':target_,'yaw':yaw,'pitch':pitch,'distance':distance,'fov':.65},grid=False,axes=False,width=1600,height=1200,path=str(ROOT/f'{name}.png')))
  print('rendered',name,flush=True)
finally:srv.close()
