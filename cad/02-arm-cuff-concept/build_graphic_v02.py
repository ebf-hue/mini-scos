"""CAD-derived arm cuff illustration. Geometry in mm; compact optics are conceptual."""
from pathlib import Path
import math,json,hashlib
import cadquery as cq
from cadquery import exporters,importers
import vtk
import numpy as np
from vtk.util.numpy_support import vtk_to_numpy, numpy_to_vtk
from PIL import Image,ImageDraw,ImageFont
R=Path(__file__).resolve().parent; E=R/'exports/v02'; E.mkdir(exist_ok=True,parents=True)
def box(a,b,c,loc=(0,0,0)):
 return cq.Workplane('XY').box(a,b,c,centered=(True,True,False)).translate(loc)
def cyl(r,h,loc=(0,0,0)):
 return cq.Workplane('XY').circle(r).extrude(h).translate(loc)
def annulus(ro,ri,h,loc): return cyl(ro,h,loc).cut(cyl(ri,h+2,(loc[0],loc[1],loc[2]-1)))
def arm_ellipse(ry,rz,length):
 return cq.Workplane('YZ').ellipse(ry,rz).extrude(length).translate((-length/2,0,0))

# Derivative of online HQ reference: remove its bundled lens, retain camera housing/PCB.
raw=importers.importStep(str(R/'sources/hq_camera_reference.step'))
camera=raw.intersect(box(50,80,80,(276,213.27,53.72)))
# x=251 is an approximate cut boundary; same downloaded reference, no claim of exact GS geometry.
cam_pcb=camera.intersect(box(20,80,80,(274.06,213.27,53.72)))
cam_housing=camera.cut(cam_pcb)
def camera_position(s):
 return s.translate((-252.66,-213.27,-93.72)).rotate((0,0,0),(0,1,0),-90).translate((22,0,114))
cam_pcb=camera_position(cam_pcb);cam_housing=camera_position(cam_housing)
laser_raw=importers.importStep(str(R/'sources/laser_1054.step'))
laser_solids=laser_raw.solids().vals()
def laser_position(s):
 return cq.Workplane(obj=s).rotate((0,0,0),(0,1,0),-25).translate((-22,0,52))

# Forearm-sized concept only: ellipse is an anatomy/phantom reference, not a measured person.
# CC0 Smithsonian life-cast scan, inches converted to mm. PCA alignment is reproducible.
reader=vtk.vtkOBJReader();reader.SetFileName(str(R/'sources/forearm_scan/life-cast-of-left-forearm-and-hand-150k.obj'));reader.Update()
arm_mesh=vtk.vtkPolyData();arm_mesh.DeepCopy(reader.GetOutput())
vertices=vtk_to_numpy(arm_mesh.GetPoints().GetData()).astype(float)*25.4
center=vertices.mean(axis=0); ev,axes=np.linalg.eigh(np.cov((vertices-center).T)); axes=axes[:,np.argsort(ev)[::-1]]
vertices=(vertices-center)@axes
# Cuff centred 80 mm from scan centre, on the proximal forearm, with local cross-section centred.
band=vertices[np.abs(vertices[:,0]-80)<30]
local_center=(band[:,1:].max(axis=0)+band[:,1:].min(axis=0))/2
vertices-=np.array([80,*local_center])
arm_mesh.GetPoints().SetData(numpy_to_vtk(vertices,deep=True));arm_mesh.Modified()
writer=vtk.vtkOBJWriter();writer.SetFileName(str(E/'forearm_reference_mm.obj'));writer.SetInputData(arm_mesh);writer.Write()
arm=arm_ellipse(40,41,76) # hidden simplified fit envelope; scan is supplied as a separate mesh.
ring=arm_ellipse(46,48,76).cut(arm_ellipse(42,44,80))
upper=ring.intersect(box(100,110,70,(0,0,0)))
lower=ring.intersect(box(100,110,70,(0,0,-70)))
for y in (-49,49):
 for x in (-25,25):
  upper=upper.union(box(14,15,5,(x,y,0)))
  lower=lower.union(box(14,15,5,(x,y,-5)))
  upper=upper.cut(cyl(2.3,12,(x,y,-6)));lower=lower.cut(cyl(2.3,12,(x,y,-6)))
platform=box(108,65,7,(0,0,45))
upper=upper.union(platform)
for x in (-22,22): upper=upper.cut(cyl(12,30,(x,0,30)))
# Exterior optical pod; one shell for illustration, needs print-ready joint design later.
pod=box(102,62,92,(0,0,52)).edges('|Z').fillet(5)
pod=pod.cut(box(92,52,94,(0,0,50)))
# Ribbon-cable notch on back edge.
pod=pod.cut(box(26,14,8,(22,36,132)))
lid=box(102,62,4,(0,0,144)).edges('|Z').fillet(5)
# In front cutaway, remove near wall and half the cuff, leaving real contents visible.
cutaway=box(160,70,200,(0,-40,0))
pod_cut=pod.cut(cutaway)
upper_cut=upper.cut(box(125,60,38,(0,-43,0)))

# Detailed supplier-drawing reconstruction: 39 mm max body diameter, 50 mm length.
# Narrow rear mount and stepped control rings replace the oversized uniform envelope.
lens=annulus(19.5,14.7,7,(22,0,55))
for ro,z,h in [(17,62,5),(18.5,67,12),(16.8,79,5),(18.8,84,10),(16,94,5),(12.7,99,6)]:
 lens=lens.union(annulus(ro,11,h,(22,0,z)))
# Fine grip ribs on focus and aperture controls, all within the 39 mm body envelope.
for z,h,rad in [(68,9,18.5),(85,7,18.8)]:
 for j in range(56):
  angle=j*360/56
  rib=box(.45,.55,h,(rad,0,z)).rotate((0,0,0),(0,0,1),angle).translate((22,0,0))
  lens=lens.union(rib)
lens_accent=annulus(17.2,16.9,1,(22,0,63))
lens_screws=[]
for z in (74,89):
 # radial locking thumbscrew facing the cutaway viewer
 screw=cyl(1.2,4).union(cyl(2.5,2,(0,0,4))).rotate((0,0,0),(1,0,0),90).translate((22,-17,z))
 lens_screws.append(screw)
glass=cyl(14.7,1,(22,0,55))
# This spacer is an unresolved close-focus/macro design allowance, not a selected accessory.
macro=annulus(15,12,9,(22,0,105))
filter_frame=box(48,48,3,(22,0,46)).cut(cyl(14,5,(22,0,45)))
for x in (4,40):
 for y in (-18,18): filter_frame=filter_frame.cut(cyl(1.3,5,(x,y,45)))
gel=cyl(13.8,0.35,(22,0,47.1))
# Printed laser clamp aligned with imported module, split clamp detail schematic.
clamp=annulus(9,5.4,25,(0,0,3)).rotate((0,0,0),(0,1,0),-25).translate((-22,0,52))
clamp=clamp.cut(box(22,2,45,(-30,0,50)))
clamp_base=box(20,24,8,(-37,0,42))
# Clamp support reaching rear of laser; model intentionally separate for adjustment.
clamp_base=clamp_base.union(box(10,24,24,(-44,0,50)))
# Rear camera mount and removable cover.
cam_mount=box(48,48,3,(22,0,130)).cut(cyl(17,5,(22,0,129)))
for x in (7,37):
 for y in (-15,15): cam_mount=cam_mount.cut(cyl(1.4,5,(x,y,129)))
# Illustrative ribbon cable routes through notch toward external Pi 5.
cable=box(16,1.0,44,(22,24,105))

# All visible solid geometry has corresponding STEP assembly bodies.
parts=[('lower_cuff',lower,'#237A83'),('upper_cuff',upper,'#237A83'),
 ('optical_pod',pod,'#24434B'),('pod_lid',lid,'#24434B'),('camera_housing_HQ_proxy',cam_housing,'#27323A'),
 ('camera_PCB_HQ_proxy',cam_pcb,'#408154'),('16mm_lens_drawing_reconstruction',lens,'#27323A'),('lens_glass',glass,'#79A8BD'),
 ('macro_spacer_UNRESOLVED',macro,'#A98BC5'),('filter_frame',filter_frame,'#A9BDC1'),('red_gel',gel,'#DC5060'),
 ('laser_clamp',clamp,'#D49B54'),('laser_clamp_support',clamp_base,'#D49B54'),('camera_mount',cam_mount,'#237A83'),('ribbon_reference',cable,'#B5BABC')]
for i,s in enumerate(laser_solids): parts.append((f'Adafruit1054_{i}',laser_position(s),['#B8BFC3','#C2A05D','#ACD7E7','#282E33','#D75C55'][i]))
# Cuff foam, fasteners, sensor board details and removable filter pull tab.
foam=arm_ellipse(42,44,70).cut(arm_ellipse(40,42,74))
foam=foam.cut(box(80,32,30,(0,0,28)))
parts.extend([('cuff_padding',foam,'#555D62'),('cyan_lens_index_ring',lens_accent,'#37AEB7'),('filter_pull_tab',box(12,14,3,(22,-28,46)),'#A9BDC1')])
for i,screw in enumerate(lens_screws):parts.append((f'lens_lock_screw_{i}',screw,'#C8CFD1'))
for x in (-25,25):
 for y in (-49,49):
  screw=cyl(2,13,(x,y,-7)).union(cyl(3.5,3,(x,y,6)))
  screw=screw.cut(cq.Workplane('XY').polygon(6,3).extrude(2).translate((x,y,7.5)))
  parts.append((f'cuff_bolt_{x}_{y}',screw,'#BCC5CC'))
  nut=cq.Workplane('XY').polygon(6,7).extrude(3).translate((x,y,-9)).cut(cyl(2,5,(x,y,-10)))
  parts.append((f'cuff_nut_{x}_{y}',nut,'#939FA7'))
for x in (7,37):
 for y in (-15,15):
  parts.append((f'camera_screw_{x}_{y}',cyl(1.25,6,(x,y,127)).union(cyl(2.5,1.5,(x,y,133))),'#C3CCD1'))
for j in range(5):
 parts.append((f'PCB_component_{j}',box(4,3,1.8,(8+j*6,17,129)),'#242B30'))
parts.append(('FFC_connector',box(20,5,3,(22,23,129)),'#ECE6D8'))
# Raise optics together to clear the anatomical forearm and its padded cuff.
parts=[(n,s.translate((0,0,10)) if n not in ('upper_cuff','lower_cuff','optical_pod','pod_lid','cuff_padding') and not n.startswith('cuff_') else s,c) for n,s,c in parts]
pod_cut=pod.cut(cutaway)
upper_cut=upper.cut(box(125,60,48,(0,-43,0)))
A=cq.Assembly(name='arm_cuff_compact_OPTICS_UNRESOLVED')
validation={}
for name,s,color in parts:
 assert s.val().isValid(),name
 A.add(s,name=name,color=cq.Color(color))
 b=s.val().BoundingBox();validation[name]={'valid':True,'bbox_mm':[round(v,2) for v in (b.xlen,b.ylen,b.zlen)]}
A.save(str(E/'arm_cuff_concept.step'))
for name,s in [('upper_cuff',upper),('lower_cuff',lower),('optical_pod',pod),('filter_frame',filter_frame),('laser_clamp',clamp)]: exporters.export(s,str(E/f'{name}.step'))
(E/'validation.json').write_text(json.dumps(validation,indent=2)+'\n')

# CAD render using smooth VTK normals, parallel projection, and ambient lighting.
def mesh(s):
 vertices,triangles=s.val().tessellate(0.12,0.12)
 pts=vtk.vtkPoints()
 for v in vertices: pts.InsertNextPoint(v.x,v.y,v.z)
 cells=vtk.vtkCellArray()
 for t in triangles:
  cells.InsertNextCell(3)
  for j in t: cells.InsertCellPoint(j)
 pd=vtk.vtkPolyData();pd.SetPoints(pts);pd.SetPolys(cells)
 normal=vtk.vtkPolyDataNormals();normal.SetInputData(pd);normal.SetFeatureAngle(40);normal.SplittingOn();normal.ConsistencyOn();normal.Update()
 return normal.GetOutput()
def rgb(h): return tuple(int(h[i:i+2],16)/255 for i in (1,3,5))
def render(scene,path,pos,focal,scale):
 ren=vtk.vtkRenderer();ren.SetBackground(0.95,0.965,0.97)
 for name,s,color in scene:
  mapper=vtk.vtkPolyDataMapper();mapper.SetInputData(s if isinstance(s,vtk.vtkPolyData) else mesh(s))
  actor=vtk.vtkActor();actor.SetMapper(mapper)
  prop=actor.GetProperty();prop.SetColor(*rgb(color));prop.SetInterpolationToPhong();prop.SetAmbient(.28);prop.SetDiffuse(.72);prop.SetSpecular(.22);prop.SetSpecularPower(42)
  if name=='forearm_scan':prop.SetSpecular(.07);prop.SetAmbient(.25)
  if name in ('red_gel','lens_glass'): prop.SetOpacity(.78)
  ren.AddActor(actor)
 cam=ren.GetActiveCamera();cam.SetPosition(*pos);cam.SetFocalPoint(*focal);cam.SetViewUp(0,0,1);cam.ParallelProjectionOn();cam.SetParallelScale(scale)
 win=vtk.vtkRenderWindow();win.SetOffScreenRendering(1);win.SetSize(1400,1150);win.AddRenderer(ren);win.SetMultiSamples(8)
 win.Render()
 w=vtk.vtkWindowToImageFilter();w.SetInput(win);w.SetScale(1);w.SetInputBufferTypeToRGB();w.ReadFrontBufferOff();w.Update()
 writer=vtk.vtkPNGWriter();writer.SetFileName(str(path));writer.SetInputConnection(w.GetOutputPort());writer.Write();win.Finalize()

scene=[('forearm_scan',arm_mesh,'#C7A68F')]
for name,s,color in parts:
 if name=='pod_lid':continue
 if name=='optical_pod':s=pod_cut
 if name=='upper_cuff':s=upper_cut
 scene.append((name,s,color))
render(scene,R/'cutaway_v02.png',(290,-460,290),(-55,0,42),158)
# Exploded stack separates camera, macro spacer, lens/filter, pod, and cuff.
exploded=[]
for name,s,color in parts:
 if name=='arm_reference':continue
 shift=(0,0,0)
 if name=='lower_cuff':shift=(0,0,-20)
 elif name=='upper_cuff':shift=(0,0,0)
 elif name=='optical_pod':shift=(0,0,18);s=pod_cut
 elif name=='pod_lid':shift=(0,0,148)
 elif name in ('camera_housing_HQ_proxy','camera_PCB_HQ_proxy','camera_mount','ribbon_reference'):shift=(0,0,120)
 elif name=='macro_spacer_UNRESOLVED':shift=(0,0,90)
 elif name.startswith('16mm_lens') or name in ('lens_glass','cyan_lens_index_ring') or name.startswith('lens_lock_screw'):shift=(0,0,60)
 elif name in ('filter_frame','red_gel','filter_pull_tab'):shift=(0,0,34)
 elif name.startswith('Adafruit1054_') or name.startswith('laser_clamp'):shift=(-45,0,30)
 exploded.append((name,s.translate(shift),color))
render(exploded,R/'exploded_v02.png',(260,-440,240),(0,0,138),198)

fontpath='/System/Library/Fonts/Supplemental/Arial.ttf'
def font(size,bold=False):
 return ImageFont.truetype('/System/Library/Fonts/Supplemental/Arial Bold.ttf' if bold else fontpath,size)
canvas=Image.new('RGB',(2600,1750),'#F2F6F8');d=ImageDraw.Draw(canvas)
d.text((100,60),'mini-scos | arm-cuff concept',font=font(66,True),fill='#17343B')
d.text((102,145),'Anatomical scan + sourced STEP hardware · detailed lens at actual scale',font=font(28),fill='#52656D')
left=Image.open(R/'cutaway_v02.png').resize((1400,1150));right=Image.open(R/'exploded_v02.png').resize((1150,945))
canvas.paste(left,(10,230));canvas.paste(right,(1410,250))
d.text((100,210),'01  CUTAWAY — FIT AROUND FOREARM',font=font(27,True),fill='#237A83')
d.text((1490,210),'02  EXPLODED OPTICAL POD',font=font(27,True),fill='#237A83')
# Numbered legend identifies colors without relying on obscuring small components.
legend=[('TEAL','Printed split cuff, camera mount & pod','#237A83'),('GOLD','Laser clamp + imported Adafruit 1054 laser','#B88B4C'),('GREEN','Pi camera PCB — HQ STEP used as visual proxy','#408154'),('RED','Removable camera-side red filter','#DC5060'),('PURPLE','Close-focus spacer — design unresolved','#A98BC5')]
for i,(tag,label,c) in enumerate(legend):
 y=1230+i*50;d.rounded_rectangle((100,y,120,y+20),radius=5,fill=c);d.text((140,y-5),label,font=font(27),fill='#253C44')
d.text((1500,1460),'Lens body: Ø39 × 50 mm; 16 mm focal length.',font=font(24),fill='#52656D')
# Footer captures actual optical limitation prominently, not just in documentation.
d.rounded_rectangle((100,1520,2500,1680),radius=18,fill='#E6DEF0')
d.text((130,1543),'PACKAGING CONCEPT — CLOSE FOCUS STILL NEEDS TESTING',font=font(30,True),fill='#543B6E')
d.text((130,1592),'The selected 16 mm lens is specified for ≥200 mm object distance. This close layout needs a tested',font=font(27),fill='#543B6E')
d.text((130,1630),'macro/close-focus adapter or different lens. Cuff fit, exposure and mechanical joints remain untested.',font=font(27),fill='#543B6E')
d.text((1500,1270),'Sourced STEP geometry:',font=font(27,True),fill='#253C44')
d.text((1500,1320),'Adafruit 1054 laser — exact module model',font=font(25),fill='#52656D')
d.text((1500,1360),'SRD-1 HQ camera — housing/PCB reference',font=font(25),fill='#52656D')
d.text((1500,1420),'Arm: Smithsonian CC0 scan; lens: drawing reconstruction.',font=font(24),fill='#52656D')
canvas.save(R/'arm_cuff_graphic_v02.png')
print('Created arm cuff graphic and valid STEP assembly.')
