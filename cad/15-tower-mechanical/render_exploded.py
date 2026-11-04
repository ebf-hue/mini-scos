from pathlib import Path
from mcp_client import SolidCraft
import cadquery as cq
ROOT=Path(__file__).resolve().parent; OUT=ROOT/'exploded';OUT.mkdir(exist_ok=True)
def check(r):
 if r.get('isError'):raise RuntimeError(r)
s=SolidCraft()
try:
 cmds=[]
 for p in (ROOT/'parts').glob('*.step'):
  n=p.stem
  if n.startswith('Strap') or n=='ArmReference':continue
  v=(0,0,0)
  if n=='BracedFrame':v=(0,0,20)
  elif n=='CameraPlate':v=(0,0,50)
  elif n=='CameraRetainer':v=(0,0,165)
  elif n.startswith('BasePin'):v=(-25 if '-1_' in n else 25,0,10)
  elif n.startswith('PlatePin'):v=(-25 if '-1_' in n else 25,0,50)
  elif n.startswith('RetainerPin'):v=(-25 if '-1_' in n else 25,0,165)
  elif n in ['LaserBracket','LaserReference']:v=(-55,0,0)
  elif n=='LaserCap':v=(-55,0,16)
  elif n!='WristBase':v=(0,0,125)
  shape=cq.importers.importStep(str(p)).val().translate(v)
  output=OUT/f'{n}.step';cq.exporters.export(shape,str(output))
  color='#bd9052' if ('Pin' in n or n in ['CameraRetainer','LaserCap']) else '#d4dade' if n=='BracedFrame' else '#737e89' if n=='WristBase' else '#8c9aa5' if n in ['CameraPlate','LaserBracket'] else '#29a4b7' if n=='BlueTrim' else '#30373e'
  cmds.extend([{'command':'file.insert_step','params':{'path':str(output),'name':n}},{'command':'appearance.assign','params':{'components':[n],'color':color}}])
 cmds.append({'command':'browser.visibility','params':{'folder':'origin','visible':False}})
 check(s.call('batch',commands=cmds,verbose=False))
 check(s.call('screenshot',source='model',camera={'target':[-10,0,190],'yaw':-.55,'pitch':.24,'distance':610,'fov':.65},grid=False,axes=False,width=1600,height=1500,path=str(ROOT/'exploded.png')))
 print('rendered exploded assembly',flush=True)
finally:s.close()
