"""Render the actual printable meshes and unmodified mount, not the concept image."""
from pathlib import Path
import cadquery as cq
import trimesh
import pyvista as pv
import numpy as np
ROOT=Path(__file__).resolve().parent
BASE=ROOT.parents[1]/'14-wrist-architecture'/'parts'
OUT=ROOT/'meshes'
scene=trimesh.Scene()
items=[]
colours={'SkinAndMount':'#759347','IvoryEyesAndFangs':'#efe0ba','Pupils':'#14171b','Gum':'#a15c50'}
for name,colour in colours.items():
 mesh=trimesh.load_mesh(OUT/f'{name}.ply',process=False)
 items.append((name,mesh,colour))
refs=[('WristSaddle','#252a2e'),('CameraKeeper','#31363b'),('LaserCap','#30363b'),('LaserHousing','#30353b'),('LaserWireRed','#a53432'),('LaserWireBlack','#202126'),('OfficialCM3_PCB','#206b48'),('OfficialCM3_LensHousing','#171c20'),('OfficialCM3_Connector','#e1d9bc'),('ArmReference','#cba889')]
for name,colour in refs:
 path=OUT/f'ref-{name}.stl'
 if not path.exists():
  s=cq.importers.importStep(str(BASE/f'{name}.step')).val()
  s.exportStl(str(path),tolerance=.04,angularTolerance=.12,relative=False)
 mesh=trimesh.load_mesh(path,process=True)
 items.append((name,mesh,colour))
for name,mesh,colour in items:
 visual=mesh.copy()
 visual.visual=trimesh.visual.TextureVisuals(material=trimesh.visual.material.PBRMaterial(baseColorFactor=trimesh.visual.color.hex_to_rgba(colour),roughnessFactor=.72,metallicFactor=0))
 scene.add_geometry(visual,node_name=name,geom_name=name)
scene.export(ROOT/'monster-on-mount.glb')
def render(name,position,target,scale=None):
 p=pv.Plotter(off_screen=True,window_size=[1800,1400],lighting='three lights')
 p.set_background('#eef0f2')
 for key,mesh,colour in items:
  poly=pv.PolyData(mesh.vertices,np.column_stack([np.full(len(mesh.faces),3),mesh.faces]).ravel())
  p.add_mesh(poly,color=colour,smooth_shading=True,split_sharp_edges=key not in colours,ambient=.23,diffuse=.72,specular=.15,specular_power=28,show_edges=False)
 p.camera_position=[position,target,(0,0,1)]
 p.camera.view_angle=31
 if scale is not None:p.enable_parallel_projection();p.camera.parallel_scale=scale
 p.enable_anti_aliasing('ssaa')
 p.enable_eye_dome_lighting()
 p.screenshot(str(ROOT/f'{name}.png'))
 p.close()
 print('Rendered actual mesh',name,flush=True)
render('sculpt-on-mount',(108,-207,145),(0,-18,63))
render('sculpt-front',(0,-240,105),(0,-33,63),66)
render('sculpt-side',(200,-85,112),(0,-9,62),72)
