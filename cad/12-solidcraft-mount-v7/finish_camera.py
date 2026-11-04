"""Sew the native surface transitions, trim a flat print face, add camera guides."""
import math,json,sys
from pathlib import Path
import cadquery as cq
from OCP.BRepBuilderAPI import BRepBuilderAPI_Sewing
ROOT=Path(__file__).resolve().parent
for distance,label in [(55,'wide'),(105,'standard')]:
 r=ROOT/'camera_source'/label
 a=cq.importers.importStep(str(r/'native_camera.step')).val();solid=None
 for tol in [.01,.02,.03,.05]:
  sew=BRepBuilderAPI_Sewing(tol);sew.Add(a.wrapped);sew.Perform();b=cq.Shape.cast(sew.SewedShape())
  if sew.NbFreeEdges()==0 and sew.NbMultipleEdges()==0 and len(b.Shells())==1 and b.Shells()[0].Closed():
   solid=cq.Solid.makeSolid(b.Shells()[0]);break
 assert solid is not None and solid.isValid(),('surface sewing failed',label,sew.NbFreeEdges())
 board=43+distance+7.43;tray=board+5.5;alpha=15.5/(tray+3-55)
 plane=cq.Plane(origin=(0,32.2,55),xDir=(1,0,0),normal=(0,1,alpha))
 half=cq.Workplane(plane).rect(500,500).extrude(-500).val()
 s=solid.intersect(half).clean()
 def box(w,d,h,x,y,z):return cq.Workplane('XY').box(w,d,h,centered=(True,True,False)).translate((x,y,z)).val()
 s=s.fuse(box(20,6,10,0,29,45.3),box(31,32,3,0,-2.4,tray)).clean()
 s=s.cut(box(44,4,2.4,0,29,49),box(22,25,6,0,-2.4,tray-1)).clean()
 parts=[]
 for sign in [-1,1]:
  parts += [box(2.8,29,9.9,sign*14.3,-1.5,board-1.4),box(4,29,1.2,sign*13.5,-1.5,board-1.4),box(4,29,1.2,sign*13.5,-1.5,board+1.52),box(3,1.2,2.1,sign*11.5,10.5,board-.3)]
 s=s.fuse(*parts).clean()
 s=s.cut(box(40,2.8,2.4,0,-15.9,board+.1),box(17,45,2.1,0,28,board+2)).clean()
 axis=(-math.sin(math.radians(25)),0,math.cos(math.radians(25)))
 origin=(-19+axis[0]*-7.5,0,60+axis[2]*-7.5)
 lp=cq.Plane(origin=origin,xDir=(axis[2],0,-axis[0]),normal=axis)
 clearance=cq.Workplane(lp).ellipse(9.5,18).extrude(10).val()
 s=s.cut(clearance).clean()
 assert s.isValid() and len(s.Solids())==1 and all(a.Closed() for a in s.Shells()),('finished camera is not one solid',label,len(s.Solids()))
 cq.exporters.export(s,str(r/'SpineCamera.step'))
 report={'sewing_tolerance_mm':tol,'free_edges':sew.NbFreeEdges(),'multiple_edges':sew.NbMultipleEdges(),'valid_solid':True,'closed_shell':True,'solid_count':1,'volume_mm3':s.Volume(),'rear_print_plane':{'origin':[0,32.2,55],'normal':[0,1,alpha]},'board_clear_width_mm':25.8,'board_slot_height_mm':1.72}
 (r/'solid_check.json').write_text(json.dumps(report,indent=2)+'\n');print(label,report,flush=True)
