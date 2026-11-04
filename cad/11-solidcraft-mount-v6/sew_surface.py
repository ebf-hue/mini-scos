"""Sew the native surface export without altering its surface definitions."""
import json
from pathlib import Path
import cadquery as cq
from OCP.BRepBuilderAPI import BRepBuilderAPI_Sewing
ROOT=Path(__file__).resolve().parent/'surface_source'
shape=cq.importers.importStep(str(ROOT/'native_blend.step')).val()
sew=BRepBuilderAPI_Sewing(.01);sew.Add(shape.wrapped);sew.Perform()
assert sew.NbFreeEdges()==0 and sew.NbMultipleEdges()==0
shell=cq.Shape.cast(sew.SewedShape()).Shells()
assert len(shell)==1 and shell[0].Closed()
solid=cq.Solid.makeSolid(shell[0]);assert solid.isValid() and solid.Volume()>50000
cq.exporters.export(solid,str(ROOT/'healed_blend.step'))
(ROOT/'sewing_check.json').write_text(json.dumps({'tolerance_mm':.01,'free_edges':sew.NbFreeEdges(),'multiple_edges':sew.NbMultipleEdges(),'closed_shell':True,'valid_solid':True,'volume_mm3':solid.Volume()},indent=2)+'\n')
