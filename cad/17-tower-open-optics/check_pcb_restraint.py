"""Check that modeled PCB free play is bounded in all six directions.
Uses the documented board envelope, not a force/strength or flexible-board test.
"""
from pathlib import Path
import json
import cadquery as cq
ROOT=Path(__file__).resolve().parent
board=cq.Workplane('XY').box(39,39,1.6,centered=(True,True,False)).val().translate((0,0,162.5))
parts={n:cq.importers.importStep(str(ROOT/'parts'/f'{n}.step')).val() for n in ['CameraPlate','CameraRetainer']}
r={'scope':'Rectangular PCB envelope translation test; geometric stops only. Does not validate physical tolerances, rotation, board flexibility, latch strength or component placement.','tests':[],'failures':[]}
for axis,delta,blocked in [('X+',(.31,0,0),True),('X-',(-.31,0,0),True),('Y+',(0,.31,0),True),('Y-',(0,-.31,0),True),('Z+',(0,0,.26),True),('Z-',(0,0,-.01),True),('seated',(0,0,0),False),('X+ free',(.29,0,0),False),('X- free',(-.29,0,0),False),('Y+ free',(0,.29,0),False),('Y- free',(0,-.29,0),False),('Z+ free',(0,0,.24),False)]:
 overlaps={n:s.intersect(board.translate(delta)).Volume() for n,s in parts.items()}
 actual=any(v>1e-4 for v in overlaps.values())
 t={'direction':axis,'translation_mm':delta,'expected_blocked':blocked,'blocked':actual,'overlap_mm3':overlaps};r['tests'].append(t)
 if actual!=blocked:r['failures'].append(t)
r['passed']=not r['failures'];(ROOT/'pcb-restraint-check.json').write_text(json.dumps(r,indent=2))
print(json.dumps(r,indent=2));assert r['passed']
