"""Native surface blends at the camera spine's foot and tray attachment."""
import json,math,sys
from pathlib import Path
from mcp_client import SolidCraft
ROOT=Path(__file__).resolve().parent
DISTANCE=int(sys.argv[1]) if len(sys.argv)>1 else 55
LABEL='wide' if DISTANCE==55 else 'standard'
SRC=ROOT/'camera_source'/LABEL;SRC.mkdir(parents=True,exist_ok=True)
board=43+DISTANCE+7.43;tray=board+5.5;span=tray+3-55
rear=lambda z:33-15.5*(z-55)/span
s=SolidCraft();commands=[]
def unwrap(r):
 if r.get('isError'):raise RuntimeError(str(r))
 return json.loads('\n'.join(c['text'] for c in r.get('content',[]) if c.get('type')=='text'))
def run(c,**p):
 commands.append({'command':c,'params':p});r=unwrap(s.call('execute',command=c,params=p,verbose=False));print(c,str(r)[:450],flush=True);return r
def finish():run('sketch.solve');run('sketch.finish')
def rect(name,w,front,back,z,rad=None):
 run('sketch.create',name=name,plane='XY',offset=z)
 kw={'p0':[-w/2,front],'p1':[w/2,back],'connect':False}
 if rad is not None:kw['radius']=rad
 r=run('sketch.rectangle.rounded' if rad else 'sketch.rectangle.two_point',**kw)
 run('sketch.constraint.fix',entities=r['created']['curves'],fixed=True);finish()
def loft(name,a,b,body):run('solid.loft',name=name,sections=[{'sketch':a},{'sketch':b}],operation='new',body_name=body)
def oval(name,center,z,a,b):
 run('sketch.create',name=name,plane='XY',offset=z)
 run('sketch.ellipse',center=[0,center],major=[a,center],minor_radius=b)
 run('sketch.constraint.fix',entities=['e1'],fixed=True);finish()
def roundhole(name,cy,z,r):
 run('sketch.create',name=name,plane='XY',offset=z)
 run('sketch.circle.center',center=[0,cy],radius=r,connect=False)
 run('sketch.constraint.fix',entities=['c1'],fixed=True);finish()

def closed_loop(body):
 t=unwrap(s.call('body_topology',body=body));es=[e for e in t['edges'] if math.dist(e['start'],e['end'])<.001]
 assert len(es)==1,(body,es)
 return es[0]
try:
 assert not unwrap(s.call('inspect_design',measure=False,sketches=False)).get('timeline')
 rect('FootBottom',44,12,rear(55)+2,55);rect('FootTop',44,12,rear(58)+2,58);loft('CameraFoot','FootBottom','FootTop','Foot')
 rect('ApronBottom',44,10,52,tray);rect('ApronTop',44,10,52-15.5*3/span,tray+3);loft('CameraApron','ApronBottom','ApronTop','Apron')
 levels=[70,tray-10]
 alpha=15.5/span;norm=math.sqrt(1+alpha*alpha)
 cy=rear(levels[0])-.8+4*norm
 direction=[0,-alpha/norm,1/norm]
 length=(levels[1]-levels[0])*norm
 run('solid.cylinder',name='RoundCameraSpine',radius=12,height=length,base=[0,cy,levels[0]],axis=direction,body_name='SpineShell')
 run('face.delete',body='SpineShell',faces=[[0,cy,levels[0]],[0,rear(levels[1])-.8+4*norm,levels[1]]],heal=False)
 foot=run('surface.offset',body='Foot',faces=[[0,23,58]],distance=0)['created_bodies'][0]
 apron=run('surface.offset',body='Apron',faces=[[0,31,tray]],distance=0)['created_bodies'][0]
 roundhole('FootBlendBoundary',23,58,10)
 run('surface.trim',body=foot,curves={'sketch':'FootBlendBoundary'},keep=[21,14,58])
 roundhole('TrayBlendBoundary',31,tray,20)
 run('surface.trim',body=apron,curves={'sketch':'TrayBlendBoundary'},keep=[21,11,tray])
 t=unwrap(s.call('body_topology',body='SpineShell'))
 for i,(z,guide) in enumerate(zip(levels,[foot,apron])):
  station=(z-levels[0])*norm
  def at_end(p):return abs(sum((p[k]-[0,cy,levels[0]][k])*direction[k] for k in range(3))-station)<.001
  edges=[e['mid'] for e in t['edges'] if at_end(e['start']) and at_end(e['end'])]
  assert edges,(i,t['edges'])
  ge=closed_loop(guide)
  print('END',i,'edge_count',len(edges),flush=True)
  run('surface.blend',**{'from':{'body':guide,'edges':[ge['mid']]},'to':{'body':'SpineShell','edges':edges},'continuity':['g2','g2'],'bulge':[0,0],'seam':[[10 if i==0 else 20,23 if i==0 else 31,58 if i==0 else tray],[12,rear(z)-.8+4*norm,z]],'align':[[0,23 if i==0 else 31,58 if i==0 else tray],[0,rear(z)-.8+4*norm+(10*direction[1] if i==0 else -10*direction[1]),z+(10*direction[2] if i==0 else -10*direction[2])]],'name':['CameraFootSurfaceBlend','CameraTraySurfaceBlend'][i],'body_name':['LowerBlend','UpperBlend'][i]})

 run('face.delete',body='Foot',faces=[[0,23,58]],heal=False)
 run('face.delete',body='Apron',faces=[[0,31,tray]],heal=False)
 run('surface.stitch',bodies=['Foot',foot,'LowerBlend','SpineShell','UpperBlend',apron,'Apron'],tolerance=.01)
 run('body.rename',body='Foot',name='SpineCamera')
 unwrap(s.call('save',path=str(SRC/'camera_blended.solidcraft')))
 unwrap(s.call('export',path=str(SRC/'native_camera.step'),bodies=['SpineCamera']))
 run('browser.visibility',folder='sketches',visible=False)
 unwrap(s.call('screenshot',source='model',view='iso',width=1300,height=1000,grid=False,axes=False,path=str(SRC/'camera_blended.png')))
finally:
 (SRC/'commands.json').write_text(json.dumps(commands,indent=2)+'\n');s.close()
