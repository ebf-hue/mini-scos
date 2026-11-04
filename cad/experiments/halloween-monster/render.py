from pathlib import Path
import json
from mcp_client import SolidCraft
ROOT=Path(__file__).resolve().parent
BASE=ROOT.parents[1]/'14-wrist-architecture'/'parts'
OUT=ROOT/'parts'
server=SolidCraft()
def checked(r):
 if r.get('isError'):raise RuntimeError(str(r)[:2000])
try:
 commands=[]
 display={name:(BASE/f'{name}.step',color) for name,color in [('WristSaddle','#32383e'),('CameraKeeper','#545961'),('LaserCap','#545961'),('LaserHousing','#41464b'),('LaserWireRed','#b33437'),('LaserWireBlack','#202326'),('OfficialCM3_PCB','#168f59'),('OfficialCM3_LensHousing','#23262b'),('OfficialCM3_Connector','#ded9c7'),('ArmReference','#d1ae8e')]}
 display.update({n:(OUT/f'{n}.step',c) for n,c in [('MonsterShell','#76a94b'),('EyesAndTeeth','#f4e8c7'),('Pupils','#20232b')]})
 for name,(path,color) in display.items():
  before=json.loads(server.call('inspect_design',measure=False,sketches=False)['content'][0]['text'])
  old={b['name'] for b in before['bodies']}
  checked(server.call('execute',command='file.insert_step',params={'path':str(path),'name':name},verbose=False))
  after=json.loads(server.call('inspect_design',measure=False,sketches=False)['content'][0]['text'])
  new=[b['name'] for b in after['bodies'] if b['name'] not in old]
  checked(server.call('execute',command='appearance.assign',params={'bodies':new,'color':color},verbose=False))
 checked(server.call('execute',command='browser.visibility',params={'folder':'origin','visible':False},verbose=False))
 checked(server.call('save',path=str(ROOT/'monster-wrist.solidcraft')))
 for name,target,yaw,pitch,distance in [('monster-wrist',[0,-16,59],-.38,.29,270),('monster-face',[0,-38,61],0,.12,215),('monster-side',[0,-15,63],1.2,.18,240)]:
  checked(server.call('screenshot',source='model',camera={'target':target,'yaw':yaw,'pitch':pitch,'distance':distance,'fov':.65},grid=False,axes=False,width=1400,height=1000,path=str(ROOT/f'{name}.png')))
 print('Rendered monster wrist attachment',flush=True)
finally:server.close()
