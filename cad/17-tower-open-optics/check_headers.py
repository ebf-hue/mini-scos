"""Continuous header keepout sweeps. Header locations/dimensions are estimates."""
import json
from pathlib import Path
import cadquery as cq
ROOT=Path(__file__).resolve().parent
parts={p.stem:cq.importers.importStep(str(p)).val() for p in (ROOT/'parts').glob('*.step')}
def box(w,d,h,x,y,z):
 return cq.Workplane('XY').box(w,d,h,centered=(True,True,False)).val().translate((x,y,z))
headers=[parts[n] for n in ['TriggerJ3Housing','TriggerJ3Pins','StrobeJ2Housing','StrobeJ2Pins']]
old=cq.importers.importStep(str(ROOT/'before-headers/CameraRetainer.step')).val()
r={'scope':'Estimated headers with enlarged keepouts. Continuous rectangular sweeps for header clearance only; full hardware motion sampled separately. Not measured camera fit.', 'old_retainer_header_overlap_mm3':sum(old.intersect(h).Volume() for h in headers),'new_retainer_header_overlap_mm3':sum(parts['CameraRetainer'].intersect(h).Volume() for h in headers),'continuous_header_sweeps':[], 'failures':[]}
# Posed x coordinates reverse the raw source's x coordinates.
for x in [-14,14]:
 for name,sweep,obstacles in [
  ('retainer_slide',box(10,75,11,x,46.5,164.1),['CameraRetainer']),
  ('camera_top_loading',box(10,10,111,x,14,164.1),['WristBase','BracedFrame','CameraPlate','LaserBracket','LaserCap']),
 ]:
  for n in obstacles:
   v=parts[n].intersect(sweep).Volume()
   entry={'motion':name,'header_x_mm':x,'obstacle':n,'overlap_mm3':v};r['continuous_header_sweeps'].append(entry)
   if v>1e-4:r['failures'].append(entry)
r['passed']=not r['failures'] and r['new_retainer_header_overlap_mm3']<1e-4
(ROOT/'header-clearance-check.json').write_text(json.dumps(r,indent=2))
print(json.dumps(r,indent=2))
assert r['passed']
