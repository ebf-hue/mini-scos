"""Prepare only the five updated replacement parts, then slice one A1 mini plate locally."""
import argparse, json, subprocess, zipfile
from pathlib import Path
import cadquery as cq
import trimesh

ROOT=Path(__file__).resolve().parent
parser=argparse.ArgumentParser()
parser.add_argument('--output-dir',type=Path,default=ROOT/'bambu')
args=parser.parse_args()
OUT=args.output_dir.resolve(); OUT.mkdir(parents=True,exist_ok=True)
MESH=OUT/'oriented'; MESH.mkdir(exist_ok=True)
PROFILES=Path('/Applications/BambuStudio.app/Contents/Resources/profiles/BBL')
APP='/Applications/BambuStudio.app/Contents/MacOS/BambuStudio'
NAMES=['WristBase','CameraPlate','CameraClipLeft','CameraClipRight','LaserBracket']
report={}
for name in NAMES:
    shape=cq.importers.importStep(str(ROOT/'parts'/f'{name}.step')).val()
    rotations={'WristBase':('x',-90),'BracedFrame':('x',-90),'CameraPlate':('x',90),'CameraClipLeft':('x',180),'CameraClipRight':('x',180),'LaserBracket':('x',90),'LaserCap':('y',45)}
    axis,angle=rotations[name]
    shape=shape.rotate((0,0,0),(1,0,0) if axis=='x' else (0,1,0),angle)
    orientation={
      'WristBase':'Flat rear end on bed; dovetail tracks run vertically',
      'BracedFrame':'Broad rear X-brace face on bed; avoid loading the release tab against bed',
      'CameraPlate':'Flat front end on bed; rail channels run vertically',
      'CameraClipLeft':'Broad top face on bed; dovetail groove upward; support release tongue',
      'CameraClipRight':'Broad top face on bed; dovetail groove upward; support release tongue',
      'LaserBracket':'Flat side of foot on bed; support accessible cradle overhangs',
      'LaserCap':'Flat axial end on bed; dovetail channels run vertically',
    }[name]
    b=shape.BoundingBox(); shape=shape.translate((-b.xmin,-b.ymin,-b.zmin))
    b=shape.BoundingBox()
    contact=sum(f.Area() for f in shape.Faces() if f.BoundingBox().zmax<.001)
    assert contact>50,(name,contact)
    path=MESH/f'{name}.stl'
    shape.exportStl(str(path),tolerance=.01,angularTolerance=.05,relative=False)
    mesh=trimesh.load_mesh(path,process=True)
    assert mesh.is_watertight,(name,'open STL')
    assert mesh.is_winding_consistent,(name,'inconsistent normals')
    assert len(mesh.split(only_watertight=False))==1,(name,'disconnected STL')
    assert abs(mesh.bounds[0][2])<.02,(name,'not on bed')
    report[name]={'orientation':orientation,'size_mm':[b.xlen,b.ylen,b.zlen],'bed_contact_mm2':contact,'triangles':len(mesh.faces),'watertight':True,'one_connected_mesh':True}
    print(name,report[name],flush=True)
(OUT/'mesh-and-orientation-check.json').write_text(json.dumps(report,indent=2))

def resolve(group,name,seen=None):
    seen=set() if seen is None else seen
    assert name not in seen
    seen.add(name)
    data=json.loads((PROFILES/group/(name+'.json')).read_text())
    merged=resolve(group,data['inherits'],seen.copy()) if data.get('inherits') else {}
    for include in data.get('include',[]): merged.update(resolve(group,include,seen.copy()))
    merged.update(data);merged.pop('inherits',None);merged.pop('include',None)
    return merged
machine=resolve('machine','Bambu Lab A1 mini 0.4 nozzle')
filament=resolve('filament','Generic PLA @BBL A1M')
process=resolve('process','0.20mm Standard @BBL A1M')
overrides={'enable_support':'1','support_type':'tree(auto)','support_on_build_plate_only':'1',
 'wall_loops':'4','sparse_infill_density':'30%','brim_type':'auto_brim','brim_width':'5',
 'support_top_z_distance':'0.2','support_bottom_z_distance':'0.2','support_object_xy_distance':'0.4',
 'curr_bed_type':'Textured PEI Plate','enable_timelapse':'0','filament_colour':['#D03030'],'enable_prime_tower':'0'}
process.update(overrides)
filament['filament_colour']=['#D03030']
for name,data in [('a1_mini_machine',machine),('generic_pla',filament),('pla_process',process)]:
    (OUT/f'{name}.json').write_text(json.dumps(data,indent=2))
job='scos-five-replacements-a1-mini-red';d=OUT/job;d.mkdir(exist_ok=True)
# Fixed layout keeps all five replacement parts on one 180 x 180 mm plate.
import xml.etree.ElementTree as ET
NS='http://schemas.microsoft.com/3dmanufacturing/core/2015/02'
ET.register_namespace('',NS)
model=ET.Element('{'+NS+'}model',unit='millimeter')
resources=ET.SubElement(model,'{'+NS+'}resources');build=ET.SubElement(model,'{'+NS+'}build')
layout={'WristBase':(8,8),'CameraPlate':(8,43),'CameraClipLeft':(110,8),'CameraClipRight':(140,8),'LaserBracket':(111,94)}
for i,n in enumerate(NAMES,1):
    m=trimesh.load_mesh(MESH/f'{n}.stl',process=True)
    obj=ET.SubElement(resources,'{'+NS+'}object',id=str(i),type='model',name=n)
    mesh=ET.SubElement(obj,'{'+NS+'}mesh');vs=ET.SubElement(mesh,'{'+NS+'}vertices');ts=ET.SubElement(mesh,'{'+NS+'}triangles')
    for v in m.vertices:ET.SubElement(vs,'{'+NS+'}vertex',x=str(v[0]),y=str(v[1]),z=str(v[2]))
    for f in m.faces:ET.SubElement(ts,'{'+NS+'}triangle',v1=str(f[0]),v2=str(f[1]),v3=str(f[2]))
    x,y=layout[n]
    assert x>=5 and y>=5 and x+m.extents[0]<=175 and y+m.extents[1]<=175,(n,'outside safe bed bounds')
    report[n]['layout_xy_mm']=[x,y]
    ET.SubElement(build,'{'+NS+'}item',objectid=str(i),transform=f'1 0 0 0 1 0 0 0 1 {x} {y} 0')
(OUT/'mesh-and-orientation-check.json').write_text(json.dumps(report,indent=2))
input_project=OUT/'one-plate-input.3mf'
with zipfile.ZipFile(input_project,'w',zipfile.ZIP_DEFLATED) as z:
    z.writestr('3D/3dmodel.model',ET.tostring(model,encoding='utf-8',xml_declaration=True))
    z.writestr('[Content_Types].xml','<?xml version="1.0"?><Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types"><Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/><Default Extension="model" ContentType="application/vnd.ms-package.3dmanufacturing-3dmodel+xml"/></Types>')
    z.writestr('_rels/.rels','<?xml version="1.0"?><Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships"><Relationship Target="/3D/3dmodel.model" Id="rel0" Type="http://schemas.microsoft.com/3dmanufacturing/2013/01/3dmodel"/></Relationships>')
args=[APP,'--load-settings',str(OUT/'a1_mini_machine.json')+';'+str(OUT/'pla_process.json'),
 '--load-filaments',str(OUT/'generic_pla.json'),'--slice','0','--arrange','0','--orient','0',
 '--ensure-on-bed','--export-3mf',job+'.3mf','--outputdir',str(d)]
args.append(str(input_project))
r=subprocess.run(args,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True,timeout=240)
(d/'slice.log').write_text(r.stdout)
print('Bambu slice exit',r.returncode,flush=True)
if r.returncode:raise RuntimeError(r.stdout[-3500:])
project=d/(job+'.3mf');temporary=d/'settings-fixed.3mf'
with zipfile.ZipFile(project) as source,zipfile.ZipFile(temporary,'w',zipfile.ZIP_DEFLATED) as target:
    for item in source.infolist():
        data=source.read(item.filename)
        if item.filename=='Metadata/project_settings.config':
            settings=json.loads(data)
            changes=settings.get('different_settings_to_system',['','',''])
            changes[0]=';'.join(overrides)
            settings['different_settings_to_system']=changes
            data=json.dumps(settings,indent=2).encode()
        target.writestr(item,data)
temporary.replace(project)
print('Project:',project,flush=True)
