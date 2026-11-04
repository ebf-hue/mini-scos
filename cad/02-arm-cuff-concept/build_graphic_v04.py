"""CAD-derived arm cuff illustration. Geometry in mm; compact optics are conceptual."""
from pathlib import Path
import math,json,hashlib
import cadquery as cq
from cadquery import exporters,importers
import vtk
import numpy as np
from vtk.util.numpy_support import vtk_to_numpy, numpy_to_vtk
from PIL import Image,ImageDraw,ImageFont
R=Path(__file__).resolve().parent; E=R/'exports/v04'; E.mkdir(exist_ok=True,parents=True)
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

# Smooth tapered forearm reference without a hand: nominal geometry, not a person scan.
arm=cq.Workplane('YZ').workplane(offset=-160).ellipse(30,25)
for step,ry,rz in [(55,33,28),(55,37,32),(50,40,35),(50,42,36),(50,43,36)]:
 arm=arm.workplane(offset=step).ellipse(ry,rz)
arm=arm.loft(combine=True)
# One-sided shallow saddle only across the top; underside and sides remain open.
saddle=arm_ellipse(46,41,82).cut(arm_ellipse(43,38,86)).intersect(box(90,100,40,(0,0,25)))
platform=box(106,58,6,(0,0,40)).edges('|Z').fillet(5)
saddle=saddle.union(platform)
for x in (-22,22):saddle=saddle.cut(cyl(13,32,(x,0,24)))
# Thin contact pads on the two curved margins, with an exposed central optical region.
pad=arm_ellipse(43,38,72).cut(arm_ellipse(41,36,76)).intersect(box(80,100,40,(0,0,25)))
pad=pad.cut(box(78,26,45,(0,0,10)))
# Two exposed slotted rear uprights; no surrounding box or lid.
posts=[]
for x in (4,40):
 post=box(8,8,87,(x,26,46)).edges('|Z').fillet(1)
 post=post.cut(box(3.5,12,59,(x,26,61)))
 posts.append(post)
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
# Open adjustable camera plate carried by the two slotted uprights.
cam_mount=box(58,60,3,(22,0,130)).edges('|Z').fillet(3).cut(cyl(17,5,(22,0,129)))
for x in (4,40):
 tab=box(7,5,18,(x,20,115)).cut(cyl(1.7,12).rotate((0,0,0),(1,0,0),90).translate((x,27,117)))
 cam_mount=cam_mount.union(tab)
for x in (7,37):
 for y in (-15,15):cam_mount=cam_mount.cut(cyl(1.4,5,(x,y,129)))
# Bent FFC ribbon, rendered as a thin band with a blue stiffener on its free end.
t=np.linspace(0,1,45)
p0=np.array([23,130]);p1=np.array([23,181]);p2=np.array([65,166]);p3=np.array([83,147])
curve=np.array([(1-u)**3*p0+3*(1-u)**2*u*p1+3*(1-u)*u*u*p2+u**3*p3 for u in t])
deriv=np.gradient(curve,axis=0);normal=np.column_stack([-deriv[:,1],deriv[:,0]]);normal/=np.linalg.norm(normal,axis=1)[:,None]
def ribbon_band(points,normals,width=16,thickness=.55):
 a=points+normals*thickness/2;b=points-normals*thickness/2
 return cq.Workplane('YZ').polyline([tuple(p) for p in np.vstack([a,b[::-1]])]).close().extrude(width).translate((22-width/2,0,0))
cable=ribbon_band(curve,normal)
stiffener=ribbon_band(curve[-8:]+normal[-8:]*.5,normal[-8:],16,.45)
parts=[('forearm_reference',arm,'#C7A68F'),('open_saddle',saddle,'#237A83'),('contact_padding',pad,'#555D62'),
 ('camera_housing_HQ_proxy',cam_housing,'#27323A'),('camera_PCB_HQ_proxy',cam_pcb,'#408154'),
 ('16mm_lens_drawing_reconstruction',lens,'#27323A'),('lens_glass',glass,'#79A8BD'),
 ('macro_spacer_UNRESOLVED',macro,'#A98BC5'),('filter_frame',filter_frame,'#A9BDC1'),('red_gel',gel,'#DC5060'),
 ('laser_clamp',clamp,'#D49B54'),('laser_clamp_support',clamp_base,'#D49B54'),
 ('camera_mount',cam_mount,'#237A83'),('ribbon_reference',cable,'#EEECE3'),('FFC_blue_stiffener',stiffener,'#3878A3'),
 ('cyan_lens_index_ring',lens_accent,'#37AEB7'),('filter_pull_tab',box(12,14,3,(22,-28,46)),'#A9BDC1')]
for i,screw in enumerate(lens_screws):parts.append((f'lens_lock_screw_{i}',screw,'#C8CFD1'))
for i,post in enumerate(posts):parts.append((f'slotted_camera_upright_{i}',post,'#237A83'))
for i,s in enumerate(laser_solids):parts.append((f'Adafruit1054_{i}',laser_position(s),['#B8BFC3','#C2A05D','#ACD7E7','#282E33','#D75C55'][i]))
for x in (7,37):
 for y in (-15,15):parts.append((f'camera_screw_{x}_{y}',cyl(1.25,6,(x,y,127)).union(cyl(2.5,1.5,(x,y,133))),'#C3CCD1'))
# Illustrative hand knobs on adjustable camera supports.
for x in (4,40):
 knob=cyl(4.5,3).union(cyl(1.5,10,(0,0,3))).rotate((0,0,0),(1,0,0),-90).translate((x,14,117))
 parts.append((f'height_adjustment_knob_{x}',knob,'#303B42'))
for j in range(5):parts.append((f'PCB_component_{j}',box(4,3,1.8,(8+j*6,17,129)),'#242B30'))
parts.append(('FFC_connector',box(20,5,3,(22,23,129)),'#ECE6D8'))
A=cq.Assembly(name='open_arm_saddle_OPTICS_UNRESOLVED')
validation={}
for name,s,color in parts:
 assert s.val().isValid(),name
 if name!='forearm_reference':A.add(s,name=name,color=cq.Color(color))
 b=s.val().BoundingBox();validation[name]={'valid':True,'bbox_mm':[round(v,2) for v in (b.xlen,b.ylen,b.zlen)]}
A.save(str(E/'open_arm_saddle.step'))
reimported=importers.importStep(str(E/'open_arm_saddle.step')).solids().vals()
assert reimported and all(s.isValid() for s in reimported), 'STEP reimport failed'
(E/'import_validation.json').write_text(json.dumps({
 'solid_count':len(reimported), 'all_solids_valid':True,
 'checks':'Individual shape validity and STEP reimport only.'
},indent=2)+'\n')
for name,s in [('open_saddle',saddle),('slotted_camera_upright',posts[0]),('camera_mount',cam_mount),('filter_frame',filter_frame),('laser_clamp',clamp),('forearm_reference',arm)]:exporters.export(s,str(E/f'{name}.step'))
(E/'validation.json').write_text(json.dumps(validation,indent=2)+'\n')

# CAD render using smooth VTK normals, parallel projection, and ambient lighting.
def mesh(s):
 vertices,triangles=s.val().tessellate(0.10,0.05)
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
def surface_texture(pd,kind):
 # Render-only UV material textures; machining/print detail is not added to STEP geometry.
 rng=np.random.default_rng(601)
 size=512;yy,xx=np.mgrid[:size,:size]
 if kind=='print':
  value=.95+.014*rng.normal(size=(size,size))-.10*np.exp(-((yy-24)/13)**2)-.035*np.exp(-((yy-300)/65)**2)
 elif kind=='skin':
  value=.98+.025*rng.normal(size=(size,size))+.012*np.sin(xx/43)*np.sin(yy/52)
 elif kind=='foam':
  value=.94+.09*rng.normal(size=(size,size))
 else:
  # Fine conductors run along the ribbon. Bright substrate and a soft metallic trace pattern.
  value=np.ones((size,size))*.98
  value[(xx%32)<4]=.78
 arr=np.repeat((np.clip(value,.55,1)*255).astype(np.uint8)[...,None],3,axis=2)
 pixels=vtk.vtkImageData();pixels.SetDimensions(size,size,1)
 pixels.GetPointData().SetScalars(numpy_to_vtk(arr.reshape(-1,3),deep=True,array_type=vtk.VTK_UNSIGNED_CHAR))
 texture=vtk.vtkTexture();texture.SetInputData(pixels);texture.RepeatOn();texture.InterpolateOn()
 points=vtk_to_numpy(pd.GetPoints().GetData())
 if kind=='print':uv=np.column_stack([points[:,0]/22,points[:,2]/.32])
 elif kind=='skin':uv=np.column_stack([points[:,0]/30,(points[:,1]+points[:,2])/30])
 elif kind=='foam':uv=np.column_stack([points[:,0]/14,(points[:,1]+points[:,2])/14])
 else:uv=np.column_stack([(points[:,0]-14)/16,points[:,2]/35])
 coords=numpy_to_vtk(uv.astype(np.float32),deep=True);coords.SetName('surface_uv');pd.GetPointData().SetTCoords(coords)
 return texture
def render(scene,path,pos,focal,scale):
 ren=vtk.vtkRenderer();ren.SetBackground(0.95,0.965,0.97)
 ren.AutomaticLightCreationOff()
 for light_pos,intensity in [((100,-250,350),.85),((-230,-80,170),.45),((80,250,200),.55)]:
  light=vtk.vtkLight();light.SetLightTypeToSceneLight();light.SetPosition(*light_pos);light.SetFocalPoint(0,0,60);light.SetIntensity(intensity);ren.AddLight(light)
 for name,s,color in scene:
  pd=s if isinstance(s,vtk.vtkPolyData) else mesh(s)
  mapper=vtk.vtkPolyDataMapper();mapper.SetInputData(pd)
  actor=vtk.vtkActor();actor.SetMapper(mapper)
  prop=actor.GetProperty();prop.SetColor(*rgb(color));prop.SetInterpolationToPhong();prop.SetAmbient(.28);prop.SetDiffuse(.72);prop.SetSpecular(.22);prop.SetSpecularPower(42)
  printed=name in ('open_saddle','camera_mount','laser_clamp','laser_clamp_support') or name.startswith('slotted_camera')
  if printed:actor.SetTexture(surface_texture(pd,'print'));prop.SetSpecular(.08);prop.SetSpecularPower(12)
  if name=='forearm_reference':actor.SetTexture(surface_texture(pd,'skin'));prop.SetSpecular(.06)
  if name=='contact_padding':actor.SetTexture(surface_texture(pd,'foam'));prop.SetSpecular(.015)
  if name=='ribbon_reference':actor.SetTexture(surface_texture(pd,'ribbon'));prop.SetSpecular(.12)
  if name.startswith('Adafruit1054_') or name.startswith('camera_screw') or name.startswith('lens_lock_screw'):
   prop.SetSpecular(.65);prop.SetSpecularPower(90);prop.SetAmbient(.18)
  if name.startswith('16mm_lens'):prop.SetSpecular(.32);prop.SetSpecularPower(55)
  if name in ('red_gel','lens_glass'): prop.SetOpacity(.78)
  ren.AddActor(actor)
 cam=ren.GetActiveCamera();cam.SetPosition(*pos);cam.SetFocalPoint(*focal);cam.SetViewUp(0,0,1);cam.ParallelProjectionOn();cam.SetParallelScale(scale)
 win=vtk.vtkRenderWindow();win.SetOffScreenRendering(1);win.SetSize(1400,1150);win.AddRenderer(ren);win.SetMultiSamples(8)
 win.Render()
 w=vtk.vtkWindowToImageFilter();w.SetInput(win);w.SetScale(1);w.SetInputBufferTypeToRGB();w.ReadFrontBufferOff();w.Update()
 writer=vtk.vtkPNGWriter();writer.SetFileName(str(path));writer.SetInputConnection(w.GetOutputPort());writer.Write();win.Finalize()

# Views show the actual open assembly, without hiding enclosure walls.
render(parts,R/'open_saddle_assembled_v04.png',(290,-460,270),(0,0,52),160)
detail=[(n,s,c) for n,s,c in parts if n!='forearm_reference']
render(detail,R/'open_saddle_detail_v04.png',(180,-360,210),(0,0,87),88)
fontpath='/System/Library/Fonts/Supplemental/Arial.ttf'
def font(size,bold=False):
 path=Path('/System/Library/Fonts/Supplemental/Arial Bold.ttf' if bold else fontpath)
 return ImageFont.truetype(str(path),size) if path.exists() else ImageFont.load_default(size=size)
canvas=Image.new('RGB',(2600,1650),'#F2F6F8');d=ImageDraw.Draw(canvas)
d.text((100,60),'mini-scos | open arm saddle',font=font(66,True),fill='#17343B')
d.text((102,145),'Open prototype · print-layer texture, metal hardware, padded contacts and bent camera cable',font=font(28),fill='#52656D')
canvas.paste(Image.open(R/'open_saddle_assembled_v04.png').resize((1400,1150)),(10,230))
canvas.paste(Image.open(R/'open_saddle_detail_v04.png').resize((1150,945)),(1410,250))
d.text((100,210),'01  RESTS ON TOP OF THE FOREARM',font=font(27,True),fill='#237A83')
d.text((1490,210),'02  OPEN PROTOTYPE HARDWARE',font=font(27,True),fill='#237A83')
for i,(label,c) in enumerate([('Shallow curved saddle + removable contact pads','#237A83'),('Angled laser in a simple printed clamp','#B88B4C'),('Slotted rear supports for camera-height trials','#237A83'),('Slide-out filter below the lens','#DC5060')]):
 y=1240+i*48;d.rounded_rectangle((100,y,120,y+20),radius=5,fill=c);d.text((140,y-5),label,font=font(26),fill='#253C44')
d.text((1490,1240),'White / blue ribbon: camera cable to the Pi.',font=font(25),fill='#52656D')
d.text((1490,1290),'Lens body: Ø39 × 50 mm, at actual scale.',font=font(25),fill='#52656D')
d.text((1490,1340),'Material texture is illustrative; camera is HQ proxy.',font=font(25),fill='#52656D')
d.rounded_rectangle((100,1470,2500,1590),radius=16,fill='#E6DEF0')
d.text((130,1490),'PROTOTYPE PACKAGING — FOCUS AND FIT NEED TESTING',font=font(28,True),fill='#543B6E')
d.text((130,1540),'The purple close-focus spacer is a placeholder. Start with an inanimate arm-shaped target.',font=font(26),fill='#543B6E')
canvas.save(R/'open_arm_saddle_textured.png')
print('Created open saddle graphic and STEP assembly.')
