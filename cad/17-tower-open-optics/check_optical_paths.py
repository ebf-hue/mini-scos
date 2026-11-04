"""Geometric line-of-sight tests, not lens focus or a laser exposure assessment.
Run directly against exported STEP files, or from build.py against in-memory solids.
"""
from pathlib import Path
import json, math
import cadquery as cq
from OCP.IntCurvesFace import IntCurvesFace_ShapeIntersector
from OCP.gp import gp_Pnt, gp_Dir, gp_Lin
ROOT=Path(__file__).resolve().parent if 'ROOT' not in globals() else ROOT
if 'parts' not in globals():
 parts={p.stem:cq.importers.importStep(str(p)).val() for p in (ROOT/'parts').glob('*.step')}
 tip=cq.Vector(-20,0,81);axis=cq.Vector(1,0,-1).normalized()
 target=cq.Vector(0,0,61)
# Emitting face is the transformed laser source's front planar annulus center.
# Camera rays start on the reconstructed glass FRONT face, z=98.574, radius14.8.
glass_z=98.574
camera_bundle=cq.Solid.makeCone(8,14.8,glass_z-58,cq.Vector(0,0,58),cq.Vector(0,0,1))
camera_margin=cq.Solid.makeCone(9,15.8,glass_z-58,cq.Vector(0,0,58),cq.Vector(0,0,1))
laser_bundle=cq.Solid.makeCylinder(2,(target-tip).Length+6,tip,axis)
printed=['WristBase','BracedFrame','CameraPlate','CameraRetainer','LaserBracket','LaserCap']
mount_obstacles=printed+['LaserReference','Strap0','Strap1']
lens_parts=['LensRearBody','ApertureRing','FocusRing','BlueTrim','FrontBarrel','FrontRim','FrontGlass','CameraReference','CAdapterEnvelope']
report={'scope':'Exact-solid free-space obstruction test. No measured focus, real lens prescription, beam divergence, tissue transport, structural strength or exposure validation.',
 'base_window_mm':{'width_x':40,'length_y':44,'corner_radius':4,'through':True},
 'laser_front_face_center_mm':list(tip.toTuple()),'laser_unit_direction':list(axis.toTuple()),
 'laser_target_mm':list(target.toTuple()),'laser_clearance_radius_mm':2,'laser_corridor_extension_past_target_mm':6,
 'camera_front_glass_mm':{'z':glass_z,'radius':14.8,'source':'Dimensioned visual lens reconstruction, not exact supplier optical CAD'},
 'wrist_patch_diameter_mm':16,'camera_extra_radial_margin_mm':1,
 'solid_volume_obstructions_mm3':{'camera_bundle':{},'camera_margin_against_mount':{},'laser_corridor':{}},
 'first_hit_rays':{'camera':[],'laser':[]}}
def record(group,shape,names):
 for n in names:
  v=parts[n].intersect(shape).Volume()
  if v>1e-5:report['solid_volume_obstructions_mm3'][group][n]=v
record('camera_bundle',camera_bundle,mount_obstacles+lens_parts)
record('camera_margin_against_mount',camera_margin,mount_obstacles)
record('laser_corridor',laser_bundle,printed+['Strap0','Strap1']+lens_parts)
# Trace finite rays through all solids; the nearest positive hit must be wrist.
obstacles={n:s for n,s in parts.items() if n!='FrontGlass'}
intersectors={}
for n,s in obstacles.items():
 q=IntCurvesFace_ShapeIntersector();q.Load(s.wrapped,1e-7);intersectors[n]=q

def trace(origin,end,exclude=()):
 d=end-origin;length=d.Length;direction=d.normalized();hits=[]
 for n,q in intersectors.items():
  if n in exclude:continue
  q.Perform(gp_Lin(gp_Pnt(*origin.toTuple()),gp_Dir(*direction.toTuple())),1e-4,length+3)
  for i in range(1,q.NbPnt()+1):
   t=q.WParameter(i)
   if t>1e-4:hits.append((t,n))
 first=min(hits) if hits else None
 return {'origin_mm':list(origin.toTuple()),'target_mm':list(end.toTuple()),'first_body':first[1] if first else None,'first_distance_mm':first[0] if first else None,'expected_target_distance_mm':length}
def skin(x,y):return cq.Vector(x,y,36+25*math.sqrt(1-(x/35)**2))
endpoints=[skin(0,0)]+[skin(8*math.cos(a*math.pi/4),8*math.sin(a*math.pi/4)) for a in range(8)]
pupils=[cq.Vector(0,0,glass_z)]+[cq.Vector(14.8*math.cos(a*math.pi/4),14.8*math.sin(a*math.pi/4),glass_z) for a in range(8)]
for pupil in pupils:
 for endpoint in endpoints:report['first_hit_rays']['camera'].append(trace(pupil,endpoint))
report['first_hit_rays']['laser'].append(trace(tip,target,exclude=['LaserReference']))
report['failures']=[r for group in report['first_hit_rays'].values() for r in group if r['first_body']!='ArmReference' or abs(r['first_distance_mm']-r['expected_target_distance_mm'])>1e-3]
report['passed']=not report['failures'] and not any(report['solid_volume_obstructions_mm3'].values())
(ROOT/'optical-path-check.json').write_text(json.dumps(report,indent=2))
print('optical obstructions',report['solid_volume_obstructions_mm3'],flush=True)
print('first-hit failures',len(report['failures']),flush=True)
assert report['passed'],report['solid_volume_obstructions_mm3']
