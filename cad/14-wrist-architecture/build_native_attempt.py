"""Compact wrist-mounted architecture study. Optical spacing and retention details remain experimental."""
import json, math
from pathlib import Path
from mcp_client import SolidCraft
ROOT=Path(__file__).resolve().parent
SRC=ROOT.parent/'13-bench-architecture'/'sources'
def unwrap(r):
    if r.get('isError'): raise RuntimeError(str(r)[:2200])
    t='\n'.join(c.get('text','') for c in r.get('content',[]) if c.get('type')=='text')
    try:return json.loads(t)
    except json.JSONDecodeError:return t
commands=[]
def c(command,**params):commands.append({'command':command,'params':params})
def box(name,w,d,h,x,y,z,op='new',target=None):
    p=dict(name=name,length=w,width=d,height=h,corner=[x-w/2,y-d/2,z],operation=op)
    if op=='new':p['body_name']=name
    if target:p['targets']=[target]
    c('solid.box',**p)
def ellipse(name,rx,ry,plane='XY',offset=0,center=None):
    c('sketch.create',name=name,plane=plane,offset=offset)
    center=center or [0,0]
    c('sketch.ellipse',center=center,major=[center[0]+rx,center[1]],minor_radius=ry)
    c('sketch.finish')
def rect_sketch(name,w,d,x,y,z):
    c('sketch.create',name=name,plane='XY',offset=z)
    c('sketch.rectangle.two_point',p0=[x-w/2,y-d/2],p1=[x+w/2,y+d/2])
    c('sketch.finish')
def cut_rect(name,w,d,h,x,y,z,target):
    rect_sketch(name+'Profile',w,d,x,y,z)
    c('solid.extrude',distance=h,operation='cut',targets=[target],name=name)
def flush(label):
    global commands
    (ROOT/f'{label}-commands.json').write_text(json.dumps(commands,indent=2))
    r=unwrap(server.call('batch',commands=commands,verbose=False))
    (ROOT/f'{label}-result.json').write_text(json.dumps(r,indent=2))
    if isinstance(r,dict) and r.get('failed'):raise RuntimeError(str(r['failed']))
    print(label,len(commands),'operations',flush=True);commands=[]
def color(names,value,opacity=1):c('appearance.assign',bodies=names,color=value,opacity=opacity)
section=lambda y:{'origin':[0,y,36],'x_dir':[1,0,0],'y_dir':[0,0,-1]}
server=SolidCraft()
try:
    assert not unwrap(server.call('inspect_design',measure=False,sketches=False)).get('bodies')
    # An open upper saddle, not a complete cuff.
    c('sketch.create',name='WristShellSection',plane=section(-28))
    c('sketch.ellipse',center=[0,0],major=[38,0],minor_radius=28)
    c('sketch.ellipse',center=[0,0],major=[35.3,0],minor_radius=25.3)
    c('sketch.finish')
    c('solid.extrude',distance=56,operation='new',body_name='WristSaddle',name='CurvedWristSaddle')
    cut_rect('OpenUnderside',100,60,70,0,0,-20,'WristSaddle')
    # Two short flared cheeks carry the camera. Their feet merge with the curved saddle.
    for i,x in enumerate([-4.85,24.85]):
        names=[]
        for j,(z,w,d) in enumerate([(49,9,36),(66,7,33),(85,4.95,30)]):
            n=f'CameraCheek{i}Section{j}';rect_sketch(n,w,d,x,3,z);names.append(n)
        c('solid.loft',sections=[{'sketch':n} for n in names],operation='join',targets=['WristSaddle'],name=f'CameraCheek{i}')
    # Camera slides in from -Y. Its original integrated lens stays attached.
    box('CameraRearBridge',33.5,8,7.4,10,20,85,'join','WristSaddle')
    for side in [-1,1]:
        box(f'CameraGuideWall{side}',3.8,30,7.4,10+side*14.85,3,85,'join','WristSaddle')
        box(f'CameraGuideLower{side}',4.95,30,1.95,10+side*14.275,3,85,'join','WristSaddle')
        box(f'CameraGuideUpper{side}',4.95,30,1.95,10+side*14.275,3,88.35,'join','WristSaddle')
    # Optical window through the saddle, below the open carrier.
    cut_rect('CameraSkinWindow',28,32,30,10,0,40,'WristSaddle')
    # Simple strap slots, separate from the optical window.
    for side in [-1,1]:
        box(f'StrapEar{side}',11,22,4,side*32.5,15,50,'join','WristSaddle')
        cut_rect(f'StrapSlot{side}',3,16,6,side*34,15,49,'WristSaddle')
    box('CameraKeeper',33.5,2.2,3.2,10,-13.3,85)
    flush('saddle-camera')

    # A broad, very short loft supports the inclined laser cradle directly on the saddle.
    q=math.sqrt(.5)
    skin_z=36+25*math.sqrt(1-(18/35)**2)
    tip=[-18,-4,skin_z+4]
    axis=[0,q,-q]
    center=[tip[i]-axis[i]*15.5 for i in range(3)]
    laser_back=[tip[i]-axis[i]*31 for i in range(3)]
    sections=[]
    for j,(z,rx,ry) in enumerate([(55,11,14),(61,10,12),(68,7,9)]):
        n=f'LaserRootSection{j}';ellipse(n,rx,ry,offset=z,center=[-18,center[1]]);sections.append(n)
    c('solid.loft',sections=[{'sketch':n} for n in sections],operation='join',targets=['WristSaddle'],name='BroadLaserRoot')
    origin=[center[i]-axis[i]*9 for i in range(3)]
    laser_plane={'origin':origin,'x_dir':[1,0,0],'y_dir':[0,-q,-q]}
    for name,upper in [('LowerLaserCradle',False),('LaserCap',True)]:
        c('sketch.create',name=name+'Section',plane=laser_plane)
        sign=-1 if upper else 1
        c('sketch.arc.center_point',center=[0,0],start=[sign*8.5,0],sweep=180)
        c('sketch.line',points=[[-sign*8.5,0],[-sign*5.2,0]])
        c('sketch.arc.center_point',center=[0,0],start=[-sign*5.2,0],sweep=-180)
        c('sketch.line',points=[[sign*5.2,0],[sign*8.5,0]])
        c('sketch.finish')
        if upper:c('solid.extrude',distance=18,operation='new',body_name='LaserCap',name='RemovableLaserCap')
        else:c('solid.extrude',distance=18,operation='join',targets=['WristSaddle'],name='LaserCradle')
    # Clear the bore through the solid root as well as the curved saddle.
    c('sketch.create',name='LaserBoreProfile',plane={'origin':laser_back,'x_dir':[1,0,0],'y_dir':[0,-q,-q]})
    c('sketch.circle.center',center=[0,0],radius=5.2)
    c('sketch.finish')
    c('solid.extrude',distance=45,operation='cut',targets=['WristSaddle'],name='LaserBoreAndSkinPort')
    # Clean all fused attachment feet against the same inner wrist envelope.
    ellipse('WristClearanceProfile',35.3,25.3,plane=section(-32))
    c('solid.extrude',distance=64,operation='cut',targets=['WristSaddle'],name='ContinuousWristClearance')
    c('solid.cylinder',radius=5,height=31,base=laser_back,axis=axis,operation='new',body_name='LaserReference',name='Laser1054Envelope')
    c('solid.cylinder',radius=.18,height=4/q,base=tip,axis=axis,operation='new',body_name='BeamReference',name='IllustrativeLaserBeam')
    color(['WristSaddle'],'#8b9da9')
    color(['CameraKeeper','LaserCap'],'#d1a262')
    color(['LaserReference'],'#bd4941')
    color(['BeamReference'],'#ee5145')
    flush('laser-cradle')

    ellipse('ForearmReferenceSection',35,25,plane=section(-90))
    c('solid.extrude',distance=180,operation='new',body_name='ArmReference',name='WristReference')
    color(['ArmReference'],'#d6b594')
    for name,value in [('OfficialCM3_PCB','#168f59'),('OfficialCM3_LensHousing','#22272c'),('OfficialCM3_Connector','#e3ddc9'),('OfficialCM3_Detail','#bca66c')]:
        c('file.insert_step',path=str(SRC/f'{name}.step'),name=name,matrix=[1,0,0,10,0,1,0,0,0,0,1,-82])
        c('appearance.assign',components=[name],color=value)
    c('browser.visibility',folder='sketches',visible=False)
    c('browser.visibility',folder='origin',visible=False)
    flush('hardware-reference')
    state=unwrap(server.call('inspect_design',measure=False,sketches=False))
    errors=[f for f in state['timeline'] if f.get('error')]
    assert not errors,errors
    unwrap(server.call('save',path=str(ROOT/'wrist-concept.solidcraft')))
    unwrap(server.call('export',path=str(ROOT/'wrist-concept.step')))
    (ROOT/'model-check.json').write_text(json.dumps({'timeline_errors':errors,'body_count':len(state['bodies']),'classification':'wrist-mounted architecture study; no slicing or optical validation','camera':'Official Raspberry Pi CM3 standard STEP, lightweight reference geometry','camera_pose':[10,0,-82],'nominal_camera_to_skin_gap_mm':20,'focus_note':'Stock standard conventional focus starts approximately 100 mm away; useful speckle at this compact distance remains unverified. This is a mechanical packaging concept.'},indent=2))
    for name,target,yaw,pitch,distance,size in [
        ('wrist-concept',[0,-2,47],-.62,.48,295,[1400,1050]),
        ('wrist-closeup',[-3,-5,73],-.65,.38,145,[1400,1000])]:
        r=server.call('screenshot',source='model',camera={'target':target,'yaw':yaw,'pitch':pitch,'distance':distance,'fov':.65},grid=False,axes=False,width=size[0],height=size[1],path=str(ROOT/f'{name}.png'))
        if r.get('isError'):raise RuntimeError(str(r)[:1500])
        print('rendered',name,flush=True)
finally:server.close()
