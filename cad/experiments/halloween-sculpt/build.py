"""Implicit-surface monster sculpt with exact mechanical mounting shoes.

Organic shape: blended distance fields -> marching cubes -> manifold booleans.
Mechanical fits: CadQuery/OCC -> mesh; collision checks on exported meshes.
"""
from pathlib import Path
import json, math, hashlib
import numpy as np
from scipy.ndimage import gaussian_filter
from skimage.measure import marching_cubes
import cadquery as cq
import trimesh

ROOT=Path(__file__).resolve().parent
BASE=ROOT.parents[1]/'14-wrist-architecture'/'parts'
OUT=ROOT/'meshes';OUT.mkdir(exist_ok=True)
STEP=.24
origin=np.array([-46.,-61.,42.],dtype=np.float32)
xs=np.arange(-46,46+STEP,STEP,dtype=np.float32)
ys=np.arange(-61,-33+STEP,STEP,dtype=np.float32)
zs=np.arange(42,82+STEP,STEP,dtype=np.float32)
x,y,z=xs[:,None,None],ys[None,:,None],zs[None,None,:]
shape=(len(xs),len(ys),len(zs))
def ellipsoid(c,r):
 q=((x-c[0])/r[0])**2+((y-c[1])/r[1])**2+((z-c[2])/r[2])**2
 return (np.sqrt(q)-1)*min(r)
def smin(a,b,k=1.0):
 h=np.maximum(k-np.abs(a-b),0)/k
 return np.minimum(a,b)-h*h*k*.25
def smax(a,b,k=1.0):return -smin(-a,-b,k)
def sphere(c,r):return np.sqrt((x-c[0])**2+(y-c[1])**2+(z-c[2])**2)-r
def bezier(points,t):
 p=np.array(points)
 return (1-t)**3*p[0]+3*(1-t)**2*t*p[1]+3*(1-t)*t*t*p[2]+t**3*p[3]
def curve_field(points,radii,blend=.25):
 result=np.full(shape,100,dtype=np.float32)
 for p,r in zip(points,radii):result=smin(result,sphere(p,r),blend)
 return result
# A thick upper jaw: a rounded extruded arch, shaped around an enlarged wrist opening.
outer=(np.sqrt((x/43)**2+((z-36)/43)**2)-1)*43
inner=(np.sqrt((x/36.8)**2+((z-36)/31.7)**2)-1)*31.7
skin=smax(outer,np.abs(y+43.8)-4.2,1.6)
skin=smax(skin,-inner,1.0)
skin=smax(skin,45-z,1.2)
# Continuous upper lip, cheek folds and a low broad bridge for the nose.
theta=np.linspace(-1.29,1.29,67)
lip=[(38*np.sin(t),-48.4,36+33.7*np.cos(t)) for t in theta]
skin=smin(skin,curve_field(lip,np.full(len(lip),2.25)),1.7)
for side in [-1,1]:
 skin=smin(skin,ellipsoid((side*29,-46.8,61.5),(6.3,3.8,7.0)),2.1)
 # Socket is part of the head, not a separate ball on a stalk.
 skin=smin(skin,ellipsoid((side*19,-46.7,73.6),(8.1,4.9,6.0)),1.9)
 browpoints=[(side*26,-48.2,75.4),(side*23,-52.0,78.0),(side*16,-52.4,75.8),(side*10,-49.4,73.0)]
 brow=np.full(shape,100,dtype=np.float32)
 for t in np.linspace(0,1,30):
  point=bezier(browpoints,t)
  factor=.65+.55*np.sin(np.pi*t)
  brow=smin(brow,ellipsoid(point,(3.0*factor,2.3*factor,1.65*factor)),.9)
 skin=smin(skin,brow,1.6)
 # Subtle cheek bumps, all grown into the cheek rather than loose beads.
 for px,pz,r in [(32.5,61.9,1.7),(35.2,57.6,1.6),(29.3,65.8,1.5)]:
  skin=smin(skin,ellipsoid((side*px,-49.0,pz),(r,r*.8,r*1.1)),1.1)
skin=smin(skin,ellipsoid((0,-51.1,71.0),(7.8,5.3,4.3)),2.0)
skin=smin(skin,ellipsoid((0,-46.7,75.0),(8.4,3.5,3.2)),2.5)
# Recessed nostrils and two shallow forehead creases.
for side in [-1,1]:
 skin=np.maximum(skin,-ellipsoid((side*3.1,-55.1,70.1),(1.75,2.4,1.25)))
 # Thin sculpted crease separates brow from the nose bridge.
 crease=[(side*(7.2+2.4*t),-49.6-1.6*t,77.9-2*t) for t in np.linspace(0,1,12)]
 skin=np.maximum(skin,-curve_field(crease,np.full(len(crease),.43),.1))
# The forehead stays below the camera's lowest insertion envelope.
skin=np.maximum(skin,z-79.4)
# Ivory eyes: brow geometry occludes their upper edge naturally in the partition.
eye_field=np.full(shape,100,dtype=np.float32)
pupil_field=np.full(shape,100,dtype=np.float32)
for side in [-1,1]:
 eye_field=np.minimum(eye_field,ellipsoid((side*19,-49.5,73.9),(5.9,3.8,4.5)))
 pupil_field=np.minimum(pupil_field,ellipsoid((side*18.2,-52.7,73.6),(2.25,1.7,2.7)))
# One softly curved gum line behind the teeth.
gumpoints=[(37.8*np.sin(t),-49.0,36+32.5*np.cos(t)) for t in np.linspace(-1.15,1.15,60)]
gum=curve_field(gumpoints,np.full(len(gumpoints),1.95),.25)
# Swept, tapered fang shapes with spherical (blunt) tips; no cone caps.
teeth=np.full(shape,100,dtype=np.float32)
for px in [-27,-17,-6,6,17,27]:
 tipx=px*.97
 skinz=36+25*np.sqrt(1-(tipx/35)**2)
 tipz=skinz+2.8
 rootz=36+32.5*np.sqrt(1-(px/37.8)**2)+1.3
 controls=[(px,-44.0,rootz),(px,-49.0,rootz-1.0),(tipx,-53.7,tipz+2),(tipx,-51.5,tipz)]
 ts=np.linspace(0,1,28)
 points=[bezier(controls,t) for t in ts]
 base=3.35 if abs(px)>20 else 2.75
 radii=[1.15+(base-1.15)*(1-t)**.8 for t in ts]
 teeth=np.minimum(teeth,curve_field(points,radii,.22))
print('Sculpted distance fields',shape,flush=True)

def mesh_field(field,name):
 # Light subvoxel smoothing avoids stair-step detail without changing the mechanical fits.
 field=gaussian_filter(field.astype(np.float32),sigma=.42)
 # The implicit solid must be fully enclosed by the sampling box.
 assert min(field[0].min(),field[-1].min(),field[:,0].min(),field[:,-1].min(),field[:,:,0].min(),field[:,:,-1].min())>0,name
 vertices,faces,_,_=marching_cubes(field,0,spacing=(STEP,STEP,STEP),allow_degenerate=False)
 mesh=trimesh.Trimesh(vertices=vertices+origin,faces=faces,process=True)
 trimesh.repair.fix_normals(mesh)
 mesh.update_faces(mesh.nondegenerate_faces());mesh.remove_unreferenced_vertices()
 assert mesh.is_watertight and mesh.is_volume,(name,'invalid implicit mesh')
 # Keep curvature with a modest decimation, using manifold-safe simplification.
 if len(mesh.faces)>90000:
  reduced=mesh.simplify_quadric_decimation(face_count=90000)
  if reduced.is_watertight and reduced.is_volume:mesh=reduced
 mesh.export(OUT/f'raw-{name}.stl')
 print(name,len(mesh.faces),'triangles',flush=True)
 return mesh
rawskin=mesh_field(skin,'skin')
raweyes=mesh_field(eye_field,'eyes')
rawpupil=mesh_field(pupil_field,'pupils')
rawteeth=mesh_field(teeth,'fangs')
rawgum=mesh_field(gum,'gum')
# Export the exact shoes/stop shoulders separately before combining with the sculpt.
def box(w,d,h,px,py,pz):
 return cq.Workplane('XY').box(w,d,h,centered=(True,True,False)).val().translate((px,py,pz))
mechanical=[]
for side in [-1,1]:
 shoe=box(7.4,22,2.4,side*37.1,15,47.2).fuse(box(7.4,22,2.4,side*37.1,15,54.4))
 shoe=shoe.fuse(box(2.4,22,9.6,side*39.6,15,47.2))
 shoe=shoe.cut(box(4.2,17.2,14,side*34,15,46))
 shoe=shoe.fuse(box(4.6,2.4,4.8,side*38.5,2.4,49.6))
 rail=box(3,61,4.8,side*39.9,-15.5,50)
 mechanical.append(shoe.fuse(rail))
mech=cq.Compound.makeCompound(mechanical)
cq.exporters.export(mech,str(ROOT/'mounting-shoes.step'))
mech.exportStl(str(OUT/'mounting-shoes.stl'),tolerance=.01,angularTolerance=.05,relative=False)
mechmesh=trimesh.load_mesh(OUT/'mounting-shoes.stl',process=True)
# Manifold booleans perform all material partitioning on actual mesh volumes.
def union(meshes):return trimesh.boolean.union(meshes,engine='manifold')
def diff(a,b):return trimesh.boolean.difference([a,b],engine='manifold')
def common(a,b):return trimesh.boolean.intersection([a,b],engine='manifold')
# Recess eye whites behind brows and leave fang roots grown into the skin.
green=union([rawskin,mechmesh])
cream=diff(union([raweyes,rawteeth]),green)
pupils=common(rawpupil,cream)
cream=diff(cream,pupils)
red=diff(rawgum,union([cream,pupils]))
green=diff(green,rawgum)
regions={'SkinAndMount':green,'IvoryEyesAndFangs':cream,'Pupils':pupils,'Gum':red}
# A single fused mesh is provided for ordinary one-colour printing.
full=union([rawskin,mechmesh,raweyes,rawteeth,rawgum])
print('Full mesh',full.is_watertight,full.is_volume,'components',len(full.split()),'largest volumes',sorted([c.volume for c in full.split()],reverse=True)[:12],flush=True)
assert full.is_watertight and full.is_volume and len(full.split())==1,('Attachment disconnected',len(full.split()))
for name,m in regions.items():
 assert m.is_watertight and m.is_volume,(name,'invalid region')
 m.export(OUT/f'{name}.ply')

full.export(ROOT/'monster-attachment.stl')
report={'method':'Implicit-surface sculpt, marching cubes, exact mounting shoes, manifold mesh booleans',
 'grid_mm':STEP,'shoe_clearance_mm':.4,'tooth_tip_radius_mm':1.15,
 'full_mesh':{'watertight':bool(full.is_watertight),'positive_volume':bool(full.is_volume),'connected_components':len(full.split()),'triangles':len(full.faces),'volume_mm3':full.volume,'bounds_mm':full.bounds.tolist()},
 'colour_overlap_mm3':{},'physical_fit':'Unverified; fit-test print required'}
from itertools import combinations
for (a,ma),(b,mb) in combinations(regions.items(),2):
 c=common(ma,mb);vol=0 if c.is_empty else abs(c.volume)
 report['colour_overlap_mm3'][a+' / '+b]=vol
 assert vol<.001,(a,b,vol)
(ROOT/'sculpt-check.json').write_text(json.dumps(report,indent=2))
print('Connected, watertight sculpt; all colour-region overlaps zero',flush=True)
