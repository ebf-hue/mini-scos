from pathlib import Path
import json
import cadquery as cq
ROOT=Path(__file__).resolve().parent
raw=cq.importers.importStep(str(ROOT/'sources/imx296-with-cs.step')).val()
plate=cq.importers.importStep(str(ROOT/'parts/CameraPlate.step')).val()
contacts=0;issues=[]
for i,f in enumerate(raw.Faces()):
 f=f.rotate((0,0,0),(0,1,0),180).translate((0,0,165))
 b=f.BoundingBox()
 if b.zmin>162.51 or b.zmax<156.49:continue
 area=f.intersect(plate).Area()
 if area<1e-5:continue
 if abs(b.zmin-162.5)<.001 and abs(b.zmax-162.5)<.001:
  contacts+=area
 else:issues.append({'source_face':i,'contact_area_mm2':area,'bbox_z':[b.zmin,b.zmax]})
r={'actual_board_face_contact_area_mm2':contacts,'source_face_penetrations':issues,'camera_source_faces':len(raw.Faces())}
(ROOT/'camera-surface-check.json').write_text(json.dumps(r,indent=2))
print(json.dumps(r,indent=2))
assert not issues
