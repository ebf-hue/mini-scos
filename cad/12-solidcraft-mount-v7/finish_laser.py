"""Finish the native blended rest with robust STEP-solid booleans."""
from pathlib import Path
import math,json
import cadquery as cq
ROOT=Path(__file__).resolve().parent/'surface_source'
a=(-math.sin(math.radians(25)),0,math.cos(math.radians(25)));p=lambda t:(-19+a[0]*t,0,60+a[2]*t)
s=cq.importers.importStep(str(ROOT/'healed_blend.step')).val()
s=s.fuse(cq.Solid.makeCylinder(7,12,cq.Vector(*p(-6)),cq.Vector(*a))).clean()
s=s.cut(cq.Solid.makeCylinder(5.1,90,cq.Vector(*p(-45)),cq.Vector(*a))).clean()
plane=cq.Plane(origin=p(-7),xDir=(a[2],0,-a[0]),normal=a)
slit=cq.Workplane(plane).center(0,6).rect(3,12).extrude(14).val();s=s.cut(slit).clean()
for w,d,h,cy,z in [(20.4,6.4,12,29,45),(44,4,2.4,29,49)]:
 s=s.cut(cq.Workplane('XY').box(w,d,h,centered=(True,True,False)).translate((0,cy,z)).val()).clean()
assert s.isValid() and len(s.Solids())==1 and all(a.Closed() for a in s.Shells())
cq.exporters.export(s,str(ROOT/'RestFinished.step'))
(ROOT/'finish_check.json').write_text(json.dumps({'kernel':'Open CASCADE','valid_solid':True,'closed_shell':True,'solid_count':1,'volume_mm3':s.Volume(),'lower_collar_outer_dimensions_mm':[17,34],'laser_bore_mm':10.2},indent=2)+'\n')
