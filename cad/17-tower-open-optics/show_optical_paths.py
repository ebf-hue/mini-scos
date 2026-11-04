"""SolidCraft inspection views; colored volumes are guides, not printed parts."""
from pathlib import Path
import cadquery as cq
from mcp_client import SolidCraft
ROOT=Path(__file__).resolve().parent
OUT=ROOT/'guides';OUT.mkdir(exist_ok=True)
tip=cq.Vector(-20,0,81);target=cq.Vector(0,0,61)
cone=cq.Solid.makeCone(8,14.8,98.574-58,cq.Vector(0,0,58),cq.Vector(0,0,1))
beam=cq.Solid.makeCylinder(.65,(target-tip).Length,tip,(target-tip).normalized())
# Visible pupil-to-skin boundary rays, supplementing the transparent volume.
rays=[]
import math
for a in range(8):
 t=a*math.pi/4;x=8*math.cos(t);y=8*math.sin(t)
 end=cq.Vector(x,y,36+25*math.sqrt(1-(x/35)**2))
 origin=cq.Vector(14.8*math.cos(t),14.8*math.sin(t),98.574)
 rays.append(cq.Solid.makeCylinder(.2,(end-origin).Length,origin,(end-origin).normalized()))
for n,s in [('CameraClearance',cone),('CameraBoundaryRays',cq.Compound.makeCompound(rays)),('LaserCenterline',beam)]:cq.exporters.export(s,str(OUT/f'{n}.step'))
def check(r):
 if r.get('isError'):raise RuntimeError(str(r)[:1800])
srv=SolidCraft()
try:
 cmds=[]
 colors={'WristBase':'#73818d','LaserBracket':'#8998a1','LaserCap':'#bd9052','LaserReference':'#494f57','ArmReference':'#c7ac91','Strap0':'#303840','Strap1':'#303840'}
 for n,col in colors.items():
  cmds.extend([{'command':'file.insert_step','params':{'path':str(ROOT/'parts'/f'{n}.step'),'name':n}},{'command':'appearance.assign','params':{'components':[n],'color':col}}])
 cmds.append({'command':'browser.visibility','params':{'folder':'origin','visible':False}})
 check(srv.call('batch',commands=cmds,verbose=False))
 check(srv.call('screenshot',source='model',camera={'target':[0,0,62],'yaw':-.6,'pitch':.8,'distance':205,'fov':.65},grid=False,axes=False,width=1600,height=1200,path=str(ROOT/'open-base.png')))
 # Glass and lower rim give a real location for the start of the camera ray bundle.
 cmds=[]
 for n,col in [('FrontRim','#30373e'),('FrontGlass','#173d39')]:
  cmds.extend([{'command':'file.insert_step','params':{'path':str(ROOT/'parts'/f'{n}.step'),'name':n}},{'command':'appearance.assign','params':{'components':[n],'color':col}}])
 for n,col,opacity in [('CameraClearance','#28ad91',.18),('CameraBoundaryRays','#159e7c',1),('LaserCenterline','#e53935',1)]:
  cmds.extend([{'command':'file.insert_step','params':{'path':str(OUT/f'{n}.step'),'name':n}},{'command':'appearance.assign','params':{'components':[n],'color':col,'opacity':opacity}}])
 check(srv.call('batch',commands=cmds,verbose=False))
 check(srv.call('save',path=str(ROOT/'optical-path-inspection.solidcraft')))
 for name,yaw,pitch,distance in [('optical-paths',-.4,.38,205),('optical-paths-side',1.57,.10,205)]:
  check(srv.call('screenshot',source='model',camera={'target':[-4,0,76],'yaw':yaw,'pitch':pitch,'distance':distance,'fov':.65},grid=False,axes=False,width=1600,height=1200,path=str(ROOT/f'{name}.png')))
  print('rendered',name,flush=True)
finally:srv.close()
