"""Exploded loading illustration using saved hardware and parts; not printable."""
from pathlib import Path
import cadquery as cq
from mcp_client import SolidCraft
ROOT=Path(__file__).resolve().parent;OUT=ROOT/'inspection';OUT.mkdir(exist_ok=True)
hardware=['CameraReference','CAdapterEnvelope','LensRearBody','ApertureRing','FocusRing','BlueTrim','FrontBarrel','FrontRim','FrontGlass','TriggerJ3Housing','TriggerJ3Pins','StrobeJ2Housing','StrobeJ2Pins']
names=['CameraPlate','CameraClipLeft','CameraClipRight']+hardware
for n in names:
 s=cq.importers.importStep(str(ROOT/'parts'/f'{n}.step')).val()
 if n in hardware:s=s.translate((0,0,100))
 elif n.startswith('CameraClip'):s=s.translate((0,-60,0))
 cq.exporters.export(s,str(OUT/f'{n}.step'))
srv=SolidCraft()
def call(name,**args):
 r=srv.call(name,**args)
 if r.get('isError'):raise RuntimeError(str(r)[:1000])
 for c in r.get('content',[]):
  if c.get('type')=='text':print(c['text'][:400],flush=True)
try:
 cmds=[]
 for n in names:
  color='#bd9052' if n.startswith('CameraClip') else '#8c9aa5' if n=='CameraPlate' else '#228459' if n=='CameraReference' else '#30373e'
  cmds.extend([{'command':'file.insert_step','params':{'path':str(OUT/f'{n}.step'),'name':n}},{'command':'appearance.assign','params':{'components':[n],'color':color}}])
 cmds.append({'command':'browser.visibility','params':{'folder':'origin','visible':False}})
 call('batch',commands=cmds,verbose=False)
 call('save',path=str(OUT/'drop-in-inspection.solidcraft'))
 call('screenshot',source='model',camera={'target':[0,-13,214],'yaw':-.62,'pitch':.42,'distance':300,'fov':.65},grid=False,axes=False,width=1400,height=1300,path=str(ROOT/'camera-drop-in.png'))
finally:srv.close()
