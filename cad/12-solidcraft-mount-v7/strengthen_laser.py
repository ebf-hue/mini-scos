"""Double the proven blend's lateral section while retaining the circular band seat.
The arm rest cylinder is invariant along Y. An affine Y stretch preserves the
blend's tangent relationship to that cylinder and to the lower collar surface.
"""
from pathlib import Path
import cadquery as cq,json
ROOT=Path(__file__).resolve().parent/'surface_source'
base=cq.importers.importStep(str(ROOT/'RestBase.step')).val()
proven=cq.importers.importStep(str(ROOT/'proven_blend.step')).val()
region=cq.Workplane('XY').box(35,28,32).translate((-24.5,0,50)).val()
extra=proven.cut(base).intersect(region).clean()
parts=[x for x in extra.Solids() if x.Volume()>20]
assert len(parts)==1,[(x.Volume()) for x in parts]
wide=parts[0].transformGeometry(cq.Matrix([[1,0,0,0],[0,2,0,0],[0,0,1,0],[0,0,0,1]]))
s=base.fuse(wide).clean()
assert s.isValid() and len(s.Solids())==1 and all(x.Closed() for x in s.Shells())
cq.exporters.export(s,str(ROOT/'healed_blend.step'))
(ROOT/'strengthening_method.json').write_text(json.dumps({'method':'Affine lateral widening of the proven V6 surface blend and lower collar; rest and upper band seat retain their geometry','width_scale':2,'lower_collar_outer_dimensions_mm':[17,34],'arm_rest_width_mm':70,'original_extra_volume_mm3':parts[0].Volume(),'widened_extra_volume_mm3':wide.Volume(),'valid_closed_solid':True},indent=2)+'\n')
