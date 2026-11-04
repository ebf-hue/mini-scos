"""Author the attachment with native surface blending; sew its STEP boundaries.
Requires SolidCraft plus uv/CadQuery (Open CASCADE) for the sewing operation.
The rest's two source cylinders are retained outside the blend's trim loops.
"""
import json
import math
import subprocess
from pathlib import Path
from mcp_client import SolidCraft
ROOT=Path(__file__).resolve().parent
SRC=ROOT/'surface_source'
def unwrap(r):
    if r.get('isError'):raise RuntimeError(str(r))
    return json.loads('\n'.join(c['text'] for c in r.get('content',[]) if c.get('type')=='text'))
s=SolidCraft()
def run(command,**params):return unwrap(s.call('execute',command=command,params=params,verbose=False))
try:
    assert not unwrap(s.call('inspect_design',measure=False,sketches=False)).get('timeline')
    unwrap(s.call('batch',commands=json.loads((SRC/'setup_commands.json').read_text()),verbose=False))
    ends=[];seams=[]
    for body in ['Body1','Body2']:
        edges=unwrap(s.call('body_topology',body=body))['edges']
        closed=[e for e in edges if math.dist(e['start'],e['end'])<.001]
        assert len(closed)==1,closed
        ends.append({'body':body,'edges':[closed[0]['mid']]});seams.append(closed[0]['start'])
    blend=run('surface.blend',**{'from':ends[0],'to':ends[1],'continuity':['g2','g2'],'bulge':[0,0],'seam':seams,'name':'RestToCollarG2Blend','body_name':'CradleSkin'})
    (SRC/'blend_result.json').write_text(json.dumps(blend,indent=2)+'\n')
    run('face.delete',body='Rest',faces=[[-30,0,math.sqrt(48**2-30**2)]],heal=False)
    direction=[-math.sin(math.radians(25)),0,math.cos(math.radians(25))]
    collar_pick=[-19+direction[0]*-2.5-8.5*direction[2],0,60+direction[2]*-2.5+8.5*direction[0]]
    run('face.delete',body='Collar',faces=[collar_pick],heal=False)
    run('surface.stitch',bodies=['Rest','Body1','Body3','CradleSkin','Body2','Body4','Collar'],tolerance=.01)
    unwrap(s.call('save',path=str(SRC/'blend_joined.solidcraft')))
    unwrap(s.call('export',path=str(SRC/'native_blend.step'),bodies=['Rest']))
finally:s.close()
subprocess.run(['uv','run','--python','3.12','--with','cadquery','python',str(ROOT/'sew_surface.py')],check=True)
s=SolidCraft()
try:
    unwrap(s.call('inspect_design',measure=False,sketches=False))
    unwrap(s.call('open',path=str(SRC/'healed_blend.step')))
    body=unwrap(s.call('measure'))['bodies'][0]['name'];run('body.rename',body=body,name='Rest')
    unwrap(s.call('batch',commands=json.loads((SRC/'finish_commands.json').read_text()),verbose=False))
    unwrap(s.call('save',path=str(SRC/'native_rest_finished.solidcraft')))
    unwrap(s.call('export',path=str(SRC/'RestFinished.step'),bodies=['Rest']))
finally:s.close()

subprocess.run(["uv","run","--python","3.12","--with","cadquery","python",str(ROOT/"validate_surface.py")],check=True)
