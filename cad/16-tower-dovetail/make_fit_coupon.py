"""Extract the actual right-front joint and its release tab for a physical fit test."""
from pathlib import Path
import json
import cadquery as cq
ROOT=Path(__file__).resolve().parent;OUT=ROOT/'fit-coupon';OUT.mkdir(exist_ok=True)
def region(w,d,h,x,y,z):return cq.Workplane('XY').box(w,d,h,centered=(True,True,False)).val().translate((x,y,z))
frame=cq.importers.importStep(str(ROOT/'parts/BracedFrame.step')).val()
base=cq.importers.importStep(str(ROOT/'parts/WristBase.step')).val()
shapes={
 'MaleRailAndLatch':frame.intersect(region(15,28,18,30.5,-28,60)),
 'FemaleRailAndCatch':base.intersect(region(17,30,12,29.5,-25,58)),
}
report={'purpose':'Physical test of actual 0.25 mm per-side rail allowance and integral release tab; no strength/fatigue claim','hard_stop':'The cropped receiver is open at its rear; this coupon tests fit and latch only','parts':{}}
for n,s in shapes.items():
 s=s.clean()
 assert s.isValid() and len(s.Solids())==1,(n,len(s.Solids()))
 cq.exporters.export(s,str(OUT/f'{n}.step'))
 b=s.BoundingBox();onbed=s.translate((-b.xmin,-b.ymin,-b.zmin))
 onbed.exportStl(str(OUT/f'{n}.stl'),tolerance=.01,angularTolerance=.05)
 report['parts'][n]={'valid':True,'solids':1,'volume_mm3':s.Volume(),'dimensions_mm':[b.xlen,b.ylen,b.zlen]}
(OUT/'coupon-check.json').write_text(json.dumps(report,indent=2))
print(report)
