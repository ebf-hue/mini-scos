"""Tessellate the checked surface solids for printing; retain exact shared vertices."""
from pathlib import Path
import cadquery as cq,json
ROOT=Path(__file__).resolve().parent;OUT=ROOT/'exports';OUT.mkdir(exist_ok=True)
report={}
for source,name,turn in [(ROOT/'surface_source/RestFinished.step','Rest',True),(ROOT/'camera_source/wide/SpineCamera.step','SpineCamera',False),(ROOT/'camera_source/standard/SpineCamera.step','SpineCamera_standard',False)]:
 shape=cq.importers.importStep(str(source)).val()
 assert shape.isValid() and len(shape.Solids())==1 and all(s.Closed() for s in shape.Shells())
 if turn:shape=shape.rotate((0,0,0),(1,0,0),-90)
 b=shape.BoundingBox();shape=shape.translate((-b.xmin,-b.ymin,-b.zmin))
 shape.exportStl(str(OUT/(name+'.stl')),tolerance=(.005 if name=='Rest' else .02),angularTolerance=(.02 if name=='Rest' else .08),relative=False)
 report[name]={'valid_closed_solid':True,'source':str(source.relative_to(ROOT)),'volume_mm3':shape.Volume()}
(OUT/'print_solid_validation.json').write_text(json.dumps(report,indent=2)+'\n')
