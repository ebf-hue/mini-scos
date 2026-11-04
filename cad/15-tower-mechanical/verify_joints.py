import json
from pathlib import Path
import cadquery as cq
ROOT=Path(__file__).resolve().parent;P=ROOT/'parts'
allparts={p.stem:cq.importers.importStep(str(p)).val() for p in P.glob('*.step')}
main=['WristBase','BracedFrame','CameraPlate','CameraRetainer','LaserBracket','LaserCap']
pins=[n for n in allparts if 'Pin' in n]
issues=[]
for i,n in enumerate(pins):
 for m in main+pins[i+1:]:
  v=allparts[n].intersect(allparts[m]).Volume()
  if v>1e-4:issues.append([n,m,v])
# Nominal board support area at the carrier's top surface.
layer=cq.Workplane('XY').box(39,39,.1,centered=(True,True,False)).val().translate((0,0,162.4))
support_area=allparts['CameraPlate'].intersect(layer).Volume()/.1
r={'pin_count':len(pins),'pin_interferences_mm3':issues,'camera_board_nominal_support_area_mm2':support_area,'pin_pullout':'Not validated; headed pins need physical retention testing','load_case':'Scenario calculation, not FEA or tested capacity'}
(ROOT/'joint-check.json').write_text(json.dumps(r,indent=2))
print(json.dumps(r,indent=2),flush=True)
assert not issues
