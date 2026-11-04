"""Conservative continuous sweeps for drop-in and connector/header clearance.
The supplied source has open PCB shells; use the documented board envelope.
"""
from pathlib import Path
import json
import cadquery as cq
ROOT=Path(__file__).resolve().parent
parts={p.stem:cq.importers.importStep(str(p)).val() for p in (ROOT/'parts').glob('*.step')}
def box(w,d,h,x,y,z):return cq.Workplane('XY').box(w,d,h,centered=(True,True,False)).val().translate((x,y,z))
printed=['WristBase','BracedFrame','CameraPlate','CameraClipLeft','CameraClipRight','LaserBracket','LaserCap']
fixed=[n for n in printed if n not in ['CameraClipLeft','CameraClipRight']]
r={'scope':'Continuous conservative envelopes, not physical measurements. Header coordinates and dimensions remain estimated. Flexible ribbon bends and latch strength untested.','drop_height_mm':100,'continuous_drop':[],'header_slide_sweeps':[],'ribbon_corridor':[],'lens_envelope_containment':[],'failures':[]}
def test(group,shape,names,label):
 for n in names:
  v=parts[n].intersect(shape).Volume();t={'envelope':label,'obstacle':n,'overlap_mm3':v}
  r[group].append(t)
  if v>1e-3:r['failures'].append(t)
# Bounding boxes of every supplied solid swept upward 100 mm are conservative.
raw=cq.importers.importStep(str(ROOT/'sources/imx296-with-cs.step')).val()
for i,s in enumerate(raw.Solids()):
 s=s.rotate((0,0,0),(0,1,0),180).translate((0,0,165));b=s.BoundingBox()
 test('continuous_drop',box(b.xlen,b.ylen,b.zlen+100,(b.xmin+b.xmax)/2,(b.ymin+b.ymax)/2,b.zmin),fixed,f'camera solid {i} swept AABB')
test('continuous_drop',box(39,39,101.6,0,0,162.5),fixed,'PCB envelope swept vertically')
for x in [-14,14]:
 test('continuous_drop',box(10,10,111,x,14,164.1),fixed,'enlarged header envelope swept vertically')
 test('header_slide_sweeps',box(10,75,11,x,46.5,164.1),['CameraClipLeft','CameraClipRight'],'header sweep relative to sliding clips')
# Axial lens and adapter cylinders extruded in Z are exact sweeps of their envelopes.
lens=cq.Solid.makeCylinder(19.5,50,cq.Vector(0,0,92.774))
for n in ['LensRearBody','ApertureRing','FocusRing','BlueTrim','FrontBarrel','FrontRim','FrontGlass']:
 v=parts[n].cut(lens).Volume();t={'part':n,'outside_envelope_mm3':v};r['lens_envelope_containment'].append(t)
 if v>1e-3:r['failures'].append(t)
test('continuous_drop',cq.Solid.makeCylinder(19.5,150,cq.Vector(0,0,92.774)),fixed,'lens attached, diameter 39 mm swept vertically')
test('continuous_drop',cq.Solid.makeCylinder(15.5,105.026,cq.Vector(0,0,142.774)),fixed,'C adapter swept vertically')
# Clearance for the connector and outgoing ribbon. Does not assert bend radius.
test('ribbon_corridor',box(25,22,10,0,-25,164.1),printed,'25 mm front cable opening')
r['passed']=not r['failures'];(ROOT/'loading-check.json').write_text(json.dumps(r,indent=2));print('Continuous loading passed:',r['passed']);print('Failures:',r['failures']);assert r['passed']
