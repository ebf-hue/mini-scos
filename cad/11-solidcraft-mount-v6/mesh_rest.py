"""Tessellate the sewn STEP solid with Open CASCADE for the print mesh.
SolidCraft's native STL tessellation collapses triangles on this surface blend.
No triangle patching or hole filling is performed.
"""
from pathlib import Path
import cadquery as cq
ROOT=Path(__file__).resolve().parent
shape=cq.importers.importStep(str(ROOT/'surface_source/RestFinished.step')).val()
assert shape.isValid() and len(shape.Solids())==1 and all(s.Closed() for s in shape.Shells())
shape=shape.rotate((0,0,0),(1,0,0),-90)
b=shape.BoundingBox();shape=shape.translate((-b.xmin,-b.ymin,-b.zmin))
cq.exporters.export(shape,str(ROOT/'exports/Rest.stl'),tolerance=.02,angularTolerance=.08)
