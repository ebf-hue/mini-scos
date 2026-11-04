"""Bench architecture study, not a print release. Native SolidCraft fixture with official CM3 reference solids."""
import json
import math
from pathlib import Path
from mcp_client import SolidCraft

ROOT = Path(__file__).resolve().parent
def unpack(r):
    if r.get('isError'): raise RuntimeError(str(r)[:3000])
    value='\n'.join(x.get('text','') for x in r.get('content',[]) if x.get('type')=='text')
    try: return json.loads(value)
    except json.JSONDecodeError: return value

commands=[]
def cmd(c,**p): commands.append({'command':c,'params':p})
def box(name,dx,dy,dz,cx,cy,z,op='new',target=None):
    p=dict(length=dx,width=dy,height=dz,corner=[cx-dx/2,cy-dy/2,z],operation=op,name=name)
    if op=='new': p['body_name']=name
    if target: p['targets']=[target]
    cmd('solid.box',**p)
def ellipse(name,y,rx,rz):
    cmd('sketch.create',name=name,plane={'origin':[0,y,36],'x_dir':[1,0,0],'y_dir':[0,0,-1]})
    cmd('sketch.ellipse',center=[0,0],major=[rx,0],minor_radius=rz)
    cmd('sketch.finish')
def tint(names,color,opacity=1): cmd('appearance.assign',bodies=names,color=color,opacity=opacity)
def flush(label):
    global commands
    (ROOT/f'{label}-commands.json').write_text(json.dumps(commands,indent=2))
    r=unpack(server.call('batch',commands=commands,verbose=False))
    (ROOT/f'{label}-result.json').write_text(json.dumps(r,indent=2))
    if isinstance(r,dict) and r.get('failed'): raise RuntimeError(str(r.get('failed')))
    print(label,'built',len(commands),'operations',flush=True)
    commands=[]

server=SolidCraft()
try:
    state=unpack(server.call('inspect_design',measure=False,sketches=False))
    assert not state.get('bodies'), 'Isolated modeling session must start empty'
    box('Base',160,150,6,0,0,0)
    cmd('solid.fillet',body='Base',edges=[[x,y,3] for x in [-80,80] for y in [-75,75]],radius=7,name='BaseCorners')
    box('BridgeFrame',18,26,174,-66,30,6)
    box('BridgeCrossbar',150,20,16,0,30,164,'join','BridgeFrame')
    box('BridgeRightPost',18,26,174,66,30,6,'join','BridgeFrame')
    # Broad sockets receive the short carriers; there are no thin stalks.
    box('CameraCarrierSocket',34,6.4,8,0,22,166.8,'cut','BridgeFrame')
    box('LaserCarrierSocket',24.4,6.4,12.4,-44,23,167.8,'cut','BridgeFrame')
    for j,y in enumerate([-49,49]):
        name=f'ArmCradle{j+1}'
        box(name,78,24,24,0,y,6)
        cmd('solid.fillet',body=name,edges=[[x,y+dy,18] for x in [-39,39] for dy in [-12,12]],radius=3,name=name+'Corners')
        ellipse(name+'Opening',y-13,35.3,25.3)
        cmd('solid.extrude',distance=26,operation='cut',targets=[name],name=name+'ConcaveSupport')
    ellipse('ArmReferenceProfile',-104,35,25)
    cmd('solid.extrude',distance=208,operation='new',body_name='ArmReference',name='ForearmReference')
    tint(['Base'],'#d7dbdf')
    tint(['BridgeFrame'],'#707b86')
    tint(['ArmCradle1','ArmCradle2'],'#abb5be')
    tint(['ArmReference'],'#d7b18c')
    flush('frame')

    # U-shaped carrier, open in front (-Y) and underneath for the whole insertion.
    box('CameraCarrier',33.5,8,7.4,0,20,167)
    for side in [-1,1]:
        box(f'GuideWall{side}',3.8,30,7.4,side*14.85,3,167,'join','CameraCarrier')
        box(f'GuideLowerLip{side}',4.95,30,1.95,side*14.275,3,167,'join','CameraCarrier')
        box(f'GuideUpperLip{side}',4.95,30,1.95,side*14.275,3,170.35,'join','CameraCarrier')
    box('CameraKeeper',33.5,2.2,3.2,0,-10.9,167)
    # Removable filter prototype sits below the camera's insertion envelope.
    box('FilterDrawer',36,36,3,0,0,152)
    box('FilterWindow',28,28,5,0,0,151,'cut','FilterDrawer')
    box('FilterPullTab',12,12,3,23,0,152,'join','FilterDrawer')
    box('FilterReference',27.5,27.5,.6,0,0,153)
    for side in [-1,1]:
        box(f'FilterSupport{side}',3,6,12,side*16.5,13,155,'join','CameraCarrier')
    tint(['CameraCarrier'],'#547c89')
    tint(['CameraKeeper'],'#d39b51')
    tint(['FilterDrawer'],'#596570')
    tint(['FilterReference'],'#6ac5da',.28)
    flush('camera-carrier')

    a=[math.sin(math.radians(12)),0,-math.cos(math.radians(12))]
    center=[-44,0,170]
    start=[center[i]-a[i]*15.5 for i in range(3)]
    box('LaserSaddle',24,25.8,24,-44,13.1,158)
    box('SaddleLowerRelief',26,16,11,-44,20,157,'cut','LaserSaddle')
    box('SaddleUpperRelief',26,16,4,-44,20,180,'cut','LaserSaddle')
    box('LaserCap',24,9.8,24,-44,-5.1,158)
    for target in ['LaserSaddle','LaserCap']:
        cmd('solid.cylinder',radius=5.2,height=43,base=[center[i]-a[i]*21.5 for i in range(3)],axis=a,operation='cut',targets=[target],name=target+'Bore')
    cmd('solid.fillet',body='LaserSaddle',edges=[[-56,.2,170],[-32,.2,170]],radius=3,name='SaddleFrontRounding')
    cmd('solid.fillet',body='LaserCap',edges=[[-56,-10,170],[-32,-10,170]],radius=3,name='LaserCapRounding')
    cmd('solid.cylinder',radius=5,height=31,base=start,axis=a,operation='new',body_name='LaserReference',name='Adafruit1054Envelope')
    tip=[center[i]+a[i]*15.5 for i in range(3)]
    cmd('solid.cylinder',radius=.22,height=92,base=tip,axis=a,operation='new',body_name='BeamReference',name='IllustrativeLaserPath')
    tint(['LaserSaddle'],'#707b86')
    tint(['LaserCap'],'#a2abb4')
    tint(['LaserReference'],'#bd4941')
    tint(['BeamReference'],'#f04c42',.7)
    flush('laser-carrier')

    for name,color in [('OfficialCM3_PCB','#168f59'),('OfficialCM3_LensHousing','#22272c'),('OfficialCM3_Connector','#e3ddc9'),('OfficialCM3_Detail','#bca66c')]:
        cmd('file.insert_step',path=str(ROOT/'sources'/f'{name}.step'),name=name)
        cmd('appearance.assign',components=[name],color=color)
    cmd('browser.visibility',folder='sketches',visible=False)
    cmd('browser.visibility',folder='origin',visible=False)
    flush('official-camera')
    state=unpack(server.call('inspect_design',measure=False,sketches=False))
    issues=[x for x in state['timeline'] if x.get('error')]
    assert not issues,issues
    (ROOT/'model-check.json').write_text(json.dumps({'timeline_errors':issues,'body_count':len(state['bodies']),'classification':'architecture study; not sliced or physically fit-tested'},indent=2))
    unpack(server.call('save',path=str(ROOT/'bench-concept.solidcraft')))
    unpack(server.call('export',path=str(ROOT/'bench-concept.step')))
    print('saved model',flush=True)
    result=server.call('screenshot',source='model',camera={'target':[0,0,86],'yaw':-.7,'pitch':.35,'distance':350,'fov':.65},grid=False,axes=False,width=1400,height=1100,path=str(ROOT/'bench-concept.png'))
    if result.get('isError'): raise RuntimeError(str(result)[:1500])
    print('rendered overview',flush=True)
    result=server.call('screenshot',source='model',camera={'target':[-13,1,166],'yaw':-.7,'pitch':-.18,'distance':115,'fov':.65},grid=False,axes=False,width=1400,height=1000,path=str(ROOT/'camera-detail.png'))
    if result.get('isError'): raise RuntimeError(str(result)[:1500])
    print('rendered camera detail',flush=True)
finally:
    server.close()
