"""Prepare only the three printed wrist parts, then slice one A1 mini plate locally."""
import argparse, json, shutil, subprocess, zipfile
from pathlib import Path
import cadquery as cq
import trimesh

ROOT=Path(__file__).resolve().parent
parser=argparse.ArgumentParser()
parser.add_argument('--output-dir',type=Path,default=ROOT/'print')
args=parser.parse_args()
OUT=args.output_dir.resolve(); OUT.mkdir(parents=True,exist_ok=True)
MESH=OUT/'stl'; MESH.mkdir(exist_ok=True)
PROFILES=Path('/Applications/BambuStudio.app/Contents/Resources/profiles/BBL')
APP='/Applications/BambuStudio.app/Contents/MacOS/BambuStudio'
NAMES=['WristSaddle','LaserCap','CameraKeeper']
report={}
for name in NAMES:
    shape=cq.importers.importStep(str(ROOT/'parts'/f'{name}.step')).val()
    if name=='LaserCap':
        shape=shape.rotate((0,0,0),(0,1,0),45)
        orientation='Flat annular end on bed; cradle axis vertical'
    else:
        shape=shape.rotate((0,0,0),(1,0,0),90)
        orientation='Flat Y end on bed' if name=='WristSaddle' else 'Broad XZ face on bed'
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
filament['filament_colour']=['#000000']
process=resolve('process','0.20mm Standard @BBL A1M')
overrides={'enable_support':'1','support_type':'tree(auto)','support_on_build_plate_only':'1',
 'wall_loops':'4','sparse_infill_density':'30%','brim_type':'auto_brim','brim_width':'5',
 'support_top_z_distance':'0.2','support_bottom_z_distance':'0.2','support_object_xy_distance':'0.4',
 'curr_bed_type':'Textured PEI Plate','enable_timelapse':'0'}
process.update(overrides)
for name,data in [('a1_mini_machine',machine),('generic_pla',filament),('pla_process',process)]:
    (OUT/f'{name}.json').write_text(json.dumps(data,indent=2))
job='wrist-inward-fit-test';d=OUT/job;d.mkdir(exist_ok=True)
args=[APP,'--load-settings',str(OUT/'a1_mini_machine.json')+';'+str(OUT/'pla_process.json'),
 '--load-filaments',str(OUT/'generic_pla.json'),'--slice','0','--arrange','1','--orient','0',
 '--ensure-on-bed','--export-3mf',job+'.3mf','--outputdir',str(d)]
args.extend(str(MESH/f'{n}.stl') for n in NAMES)
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

release=OUT/'wrist-mount-black-pla.3mf'
shutil.copy2(project,release)
print('Release plate:',release,flush=True)
