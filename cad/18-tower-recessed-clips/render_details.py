"""Inspection renders; does not change saved assembly or printable parts."""
from pathlib import Path
from mcp_client import SolidCraft
ROOT=Path(__file__).resolve().parent
s=SolidCraft()
def call(name,**kwargs):
 r=s.call(name,**kwargs)
 if r.get('isError'):raise RuntimeError(str(r)[:1000])
 for c in r.get('content',[]):
  if c.get('type')=='text':print(c['text'][:600],flush=True)
try:
 call('open',path=str(ROOT/'tower-recessed-clips.solidcraft'))
 call('screenshot',source='model',camera={'target':[0,0,164],'yaw':-.55,'pitch':1.08,'distance':155,'fov':.65},grid=False,axes=False,width=1500,height=1100,path=str(ROOT/'camera-seat-assembled.png'))
 call('open',path=str(ROOT/'parts/CameraPlate.step'))
 call('screenshot',source='model',camera={'target':[0,0,162],'yaw':-.4,'pitch':1.05,'distance':150,'fov':.65},grid=False,axes=False,width=1500,height=1100,path=str(ROOT/'camera-seat-empty.png'))
finally:s.close()
