"""OCC construction of the wrist packaging study; inspection/rendering through SolidCraft MCP.

The fit-test plate must be regenerated after geometry changes.
Run: uv run --python 3.12 --with cadquery python build.py
"""
import json, math
from pathlib import Path
import cadquery as cq
from mcp_client import SolidCraft
ROOT=Path(__file__).resolve().parent
SRC=ROOT/'sources'
OUT=ROOT/'parts';OUT.mkdir(exist_ok=True)
def block(w,d,h,x,y,z):
    return cq.Workplane('XY').box(w,d,h,centered=(True,True,False)).val().translate((x,y,z))
def wire(w,d,x,y,z,oval=False):
    wp=cq.Workplane('XY').workplane(offset=z).center(x,y)
    return (wp.ellipse(w,d) if oval else wp.rect(w,d)).val()
def arm(rx,rz,y=-32,length=64):
    plane=cq.Plane(origin=(0,y,36),xDir=(1,0,0),normal=(0,1,0))
    return cq.Workplane(plane).ellipse(rx,rz).extrude(length).val()
outer=arm(38,28,-28,56)
body=outer.cut(arm(35.3,25.3,-29,58)).cut(block(100,64,70,0,0,-20))
for x in [-4.85,24.85]:
    cheek=cq.Solid.makeLoft([wire(w,d,x,3,z) for z,w,d in [(49,9,36),(66,7,33),(85,4.95,30)]])
    body=body.fuse(cheek)
body=body.fuse(block(33.5,8,7.4,10,20,85))
for side in [-1,1]:
    body=body.fuse(block(3.8,30,7.4,10+side*14.85,3,85))
    body=body.fuse(block(4.95,30,1.95,10+side*14.275,3,85))
    body=body.fuse(block(4.95,30,1.95,10+side*14.275,3,88.35))
body=body.cut(block(28,32,30,10,0,40))
for side in [-1,1]:
    ear=block(11,22,4,side*32.5,15,50)
    body=body.fuse(ear)
    body=body.cut(block(3,16,6,side*34,15,49))
keeper=block(33.5,2.2,3.2,10,-13.3,85)
for x in [-4.85,24.85]:
    # Raised ends leave the ribbon connector accessible above the low centre bar.
    keeper=keeper.fuse(block(3.8,2.2,7.4,x,-13.3,85))
    keeper=keeper.fuse(cq.Solid.makeCone(1.025,.9,3.5,cq.Vector(x,-12.3,89.7),cq.Vector(0,1,0)))
    body=body.cut(cq.Solid.makeCylinder(1.1,4,cq.Vector(x,-12.05,89.7),cq.Vector(0,1,0)))
keeper=keeper.clean()
q=math.sqrt(.5)
# +X points across the wrist toward the camera at X=10. The old +Y direction
# pointed along the wrist instead. Aim at skin, never at the camera lens.
axis=cq.Vector(q,0,-q)
skin_target=cq.Vector(0,0,61)
beam_length=10
tip=skin_target-axis*beam_length
laser_length=32.8  # Actual barrel extent in the licensed supplier STEP.
center=tip-axis*(laser_length/2)
back=tip-axis*laser_length
# A broad foot turns into an inclined pad following the cradle underside.
# The previous vertical oval pedestal terminated below the angled cradle.
up=cq.Vector(q,0,q)
root_sections=[]
for position,angle,rx,ry in [
    ((center.x,0,54),0,14,12),
    ((center.x-1,0,62),12,13.5,11.5),
    ((center.x-2,0,70),28,12,10.5),
    ((center-up*5).toTuple(),45,10.3,9.1),
    (center.toTuple(),45,10.5,8.5),
]:
    a=math.radians(angle)
    section_plane=cq.Plane(origin=position,xDir=(math.cos(a),0,-math.sin(a)),normal=(math.sin(a),0,math.cos(a)))
    root_sections.append(cq.Workplane(section_plane).ellipse(rx,ry).val())
root=cq.Solid.makeLoft(root_sections,ruled=False)
body=body.fuse(root)
origin=center-axis*9
ring=cq.Solid.makeCylinder(8.5,18,origin,axis).cut(cq.Solid.makeCylinder(5.2,18,origin,axis))
plane=cq.Plane(origin=origin,xDir=(0,-1,0),normal=axis)
lower_tool=cq.Workplane(plane).center(0,20).rect(60,40).extrude(18).val()
lower=ring.intersect(lower_tool)
cap=ring.cut(lower_tool)
# The loft itself forms the lower cradle exterior; no ring shoulder is fused on.
body=body.cut(cap)
body=body.cut(cq.Solid.makeCylinder(5.2,laser_length+beam_length+2,back,axis))
body=body.cut(arm(35.3,25.3)).clean()
cap=cap.translate((q*.15,0,q*.15))
# The cap's clearance offset also moves its outer surface toward the camera cheek.
# Clear that final placed envelope, not only the unshifted cap.
body=body.cut(cap).clean()
# Two short tapered pegs register the removable cap in its lower cradle.
up=cq.Vector(q,0,q)
for side in [-1,1]:
    p=center+cq.Vector(0,side*6.85,0)
    cap=cap.fuse(cq.Solid.makeCone(.85,.72,2.9,p+up*.25,-up))
    body=body.cut(cq.Solid.makeCylinder(.95,3.1,p+up*.05,-up))
cap=cap.clean();body=body.clean()
# The manufacturer's model has its emitting aperture at Z=0 and rear wires at +Z.
# Rotate +Z toward the rear/upward end, then put the actual aperture at `tip`.
laser_original=cq.importers.importStep(str(SRC/'laser_1054.step')).val()
laser_parts=[s.rotate((0,0,0),(0,1,0),-45).translate(tip) for s in laser_original.Solids()]
laser=cq.Compound.makeCompound(laser_parts)
beam=cq.Solid.makeCylinder(.22,beam_length,tip,axis)
spot=cq.Solid.makeCylinder(.8,.12,skin_target,cq.Vector(0,0,1))
camera_skin_z=36+25*math.sqrt(1-(10/35)**2)
sightline=cq.Solid.makeCylinder(.13,80.35-camera_skin_z,cq.Vector(10,0,80.35),cq.Vector(0,0,-1))
reference=arm(35,25,-90,180)
parts={'WristSaddle':body,'CameraKeeper':keeper,'LaserCap':cap,'BeamReference':beam,'SpotReference':spot,'CameraAxisReference':sightline,'ArmReference':reference}
parts.update(dict(zip(['LaserHousing','LaserInsert','LaserAperture','LaserWireRed','LaserWireBlack'],laser_parts)))
checks={}
for name,shape in parts.items():
    b=shape.BoundingBox()
    checks[name]={'valid':shape.isValid(),'solids':len(shape.Solids()),'volume':shape.Volume(),'bbox':[b.xmin,b.ymin,b.zmin,b.xmax,b.ymax,b.zmax]}
    assert shape.isValid() and len(shape.Solids())==1,(name,checks[name])
    cq.exporters.export(shape,str(OUT/f'{name}.step'))
print('valid curved wrist assembly',flush=True)

# Use the same official source for the reference render and insertion check.
full=cq.importers.importStep(str(SRC/'Camera_module_3_std_model_simple.stp')).val()
full_pose=cq.Location(cq.Vector(-2.5,14.4,88),cq.Vector(0,0,1),-90)
source_solids=full.Solids()
assert len(source_solids)==590, 'Unexpected camera source; fetch the pinned official model'
for name,indices in {
    'OfficialCM3_PCB':[442],
    'OfficialCM3_LensHousing':[537,538,540,541],
    'OfficialCM3_Connector':[566],
    'OfficialCM3_Detail':[542,567],
}.items():
    shape=cq.Compound.makeCompound([source_solids[i].moved(full_pose) for i in indices])
    cq.exporters.export(shape,str(OUT/f'{name}.step'))
    parts[name]=shape

# Conservative swept boxes contain every position along the 35 mm slide.
# Include all 590 source solids; remove the keeper before insertion.
hits=[]
for i,shape in enumerate(full.Solids()):
    b=shape.moved(full_pose).BoundingBox()
    swept=cq.Solid.makeBox(max(b.xlen,1e-5),b.ylen+35,max(b.zlen,1e-5),cq.Vector(b.xmin,b.ymin-35,b.zmin))
    # The keeper is removed for insertion. Include the newly turned laser and cap.
    for name,obstacle in [('saddle',body),('laser',laser),('laser_cap',cap)]:
        ob=obstacle.BoundingBox()
        if b.xmax<ob.xmin or b.xmin>ob.xmax or b.zmax<ob.zmin or b.zmin>ob.zmax:continue
        overlap=obstacle.intersect(swept).Volume()
        if overlap>1e-5:hits.append({'component':i,'obstacle':name,'overlap_mm3':overlap})
checks['camera_insertion']={'method':'conservative continuous swept component bounding boxes','source_solids':len(full.Solids()),'travel_mm':35,'keeper_removed':True,'intersections':hits}
checks['assembly']={'wrist_overlap_mm3':body.intersect(reference).Volume(),'laser_overlap_mm3':body.intersect(laser).Volume(),'cap_overlap_mm3':body.intersect(cap).Volume(),'keeper_overlap_mm3':body.intersect(keeper).Volume(),'beam_holder_overlap_mm3':body.intersect(beam).Volume(),'laser_wrist_overlap_mm3':laser.intersect(reference).Volume()}
checks['laser_aim']={'direction':axis.toTuple(),'emitting_aperture_mm':tip.toTuple(),'skin_target_mm':skin_target.toTuple(),'camera_skin_center_mm':[10,0,camera_skin_z],'lateral_source_camera_spacing_mm':10,'beam_length_mm':beam_length,'direction_toward_camera_in_X':axis.x>0 and abs(axis.y)<1e-9,'supplier_front':'original STEP Z=0 aperture; rear wires distinguish orientation'}
checks['retention']={'camera_keeper':'two tapered 2.05-to-1.8 mm pegs in 2.2 mm sockets','laser_cap':'two tapered 1.7-to-1.44 mm pegs in 1.9 mm sockets','physical_fit':'unverified; first print is a fit test'}
assert not hits,hits
assert all(abs(v)<1e-4 for v in checks['assembly'].values()),checks['assembly']
(ROOT/'model-check.json').write_text(json.dumps(checks,indent=2))
print('insertion check',len(hits),'candidate overlaps',checks['assembly'],flush=True)

def unwrap(r):
    if r.get('isError'):raise RuntimeError(str(r)[:2500])
    t='\n'.join(c.get('text','') for c in r.get('content',[]) if c.get('type')=='text')
    try:return json.loads(t)
    except json.JSONDecodeError:return t
colors={'WristSaddle':'#8b9da9','CameraKeeper':'#d1a262','LaserCap':'#d1a262','LaserHousing':'#465058','LaserInsert':'#b79c60','LaserAperture':'#171d23','LaserWireRed':'#cc3c39','LaserWireBlack':'#25292e','BeamReference':'#ee5145','SpotReference':'#ee5145','CameraAxisReference':'#2892c2','ArmReference':'#d6b594','OfficialCM3_PCB':'#168f59','OfficialCM3_LensHousing':'#22272c','OfficialCM3_Connector':'#e3ddc9','OfficialCM3_Detail':'#bca66c'}
server=SolidCraft()
try:
    assert not unwrap(server.call('inspect_design',measure=False,sketches=False)).get('bodies')
    commands=[]
    for name in parts:
        commands.append({'command':'file.insert_step','params':{'path':str(OUT/f'{name}.step'),'name':name}})
        commands.append({'command':'appearance.assign','params':{'components':[name],'color':colors[name]}})
    commands.append({'command':'browser.visibility','params':{'folder':'origin','visible':False}})
    unwrap(server.call('batch',commands=commands,verbose=False))
    unwrap(server.call('save',path=str(ROOT/'wrist-inward.solidcraft')))
    unwrap(server.call('export',path=str(ROOT/'wrist-inward.step')))
    for name,target,yaw,pitch,distance,size in [('wrist-inward',[0,-2,47],-.62,.48,295,[1400,1050]),('wrist-inward-closeup',[-3,-5,73],-.2,.25,155,[1400,1000])]:
        r=server.call('screenshot',source='model',camera={'target':target,'yaw':yaw,'pitch':pitch,'distance':distance,'fov':.65},grid=False,axes=False,width=size[0],height=size[1],path=str(ROOT/f'{name}.png'))
        if r.get('isError'):raise RuntimeError(str(r)[:1500])
        print('rendered',name,flush=True)
    unwrap(server.call('execute',command='appearance.assign',params={'components':['WristSaddle'],'color':'#8b9da9','opacity':.18},verbose=False))
    r=server.call('screenshot',source='model',camera={'target':[-4,0,75],'yaw':-.08,'pitch':.18,'distance':160,'fov':.65},grid=False,axes=False,width=1400,height=1000,path=str(ROOT/'wrist-inward-ray.png'))
    if r.get('isError'):raise RuntimeError(str(r)[:1500])
    print('rendered inward beam path',flush=True)
finally:server.close()
