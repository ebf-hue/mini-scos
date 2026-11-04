from pathlib import Path
import cadquery as cq
from mcp_client import SolidCraft
ROOT=Path(__file__).resolve().parent; OUT=ROOT/'fit-coupon'
# Separate the real mating parts along their actual sliding axis for inspection.
s=cq.importers.importStep(str(OUT/'MaleRailAndLatch.step')).val().translate((0,-28,0))
cq.exporters.export(s,str(OUT/'MaleRailAndLatch-exploded.step'))
server=SolidCraft()
try:
 cmds=[]
 for n,file,col in [('Receiver','FemaleRailAndCatch.step','#8c9aa5'),('RailAndReleaseTab','MaleRailAndLatch-exploded.step','#bd9052')]:
  cmds.extend([{'command':'file.insert_step','params':{'path':str(OUT/file),'name':n}},{'command':'appearance.assign','params':{'components':[n],'color':col}}])
 cmds.append({'command':'browser.visibility','params':{'folder':'origin','visible':False}})
 r=server.call('batch',commands=cmds,verbose=False)
 if r.get('isError'):raise RuntimeError(r)
 r=server.call('screenshot',source='model',camera={'target':[30,-40,67],'yaw':-.65,'pitch':.6,'distance':125,'fov':.65},grid=False,axes=False,width=1400,height=1000,path=str(ROOT/'dovetail-detail.png'))
 if r.get('isError'):raise RuntimeError(r)
 print('Rendered real mating dovetail and release tab')
finally:server.close()
