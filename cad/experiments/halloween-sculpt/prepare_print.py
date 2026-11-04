"""Prepare one-colour and four-region AMS plates; never send a printer job."""
from pathlib import Path
import json,subprocess,zipfile,shutil
from xml.sax.saxutils import escape
import numpy as np
import trimesh
ROOT=Path(__file__).resolve().parent
OUT=ROOT/'print';OUT.mkdir(exist_ok=True)
APP='/Applications/BambuStudio.app/Contents/MacOS/BambuStudio'
PROFILES=Path('/Applications/BambuStudio.app/Contents/Resources/profiles/BBL')
NAMES=['SkinAndMount','IvoryEyesAndFangs','Pupils','Gum']
COLORS=['#759347','#EFE0BA','#14171B','#A15C50']
def resolve(group,name,seen=None):
 seen=set() if seen is None else seen
 assert name not in seen;seen.add(name)
 data=json.loads((PROFILES/group/(name+'.json')).read_text())
 merged=resolve(group,data['inherits'],seen.copy()) if data.get('inherits') else {}
 for include in data.get('include',[]):merged.update(resolve(group,include,seen.copy()))
 merged.update(data);merged.pop('inherits',None);merged.pop('include',None)
 return merged
full=trimesh.load_mesh(ROOT/'monster-attachment.stl',process=True)
R=trimesh.transformations.rotation_matrix(np.pi/2,[1,0,0])
full.apply_transform(R)
shift=-full.bounds[0]
full.apply_translation(shift)
assert full.is_watertight and len(full.split())==1
full.export(OUT/'monster-face-down.stl')
meshes=[]
for name in NAMES:
 m=trimesh.load_mesh(ROOT/'meshes'/f'{name}.ply',process=False)
 m.apply_transform(R);m.apply_translation(shift);meshes.append(m)
# One standard 3MF object with four material parts; all parts share the same origin.
ns='http://schemas.microsoft.com/3dmanufacturing/core/2015/02'
resources=[]
for ident,(name,m) in enumerate(zip(NAMES,meshes),1):
 vertices=''.join(f'<vertex x="{v[0]:.7f}" y="{v[1]:.7f}" z="{v[2]:.7f}"/>' for v in m.vertices)
 faces=''.join(f'<triangle v1="{f[0]}" v2="{f[1]}" v3="{f[2]}"/>' for f in m.faces)
 resources.append(f'<object id="{ident}" type="model" name="{name}" pid="10" pindex="{ident-1}"><mesh><vertices>{vertices}</vertices><triangles>{faces}</triangles></mesh></object>')
resources.append('<basematerials id="10">'+''.join(f'<base name="{n}" displaycolor="{c}FF"/>' for n,c in zip(NAMES,COLORS))+'</basematerials>')
resources.append('<object id="5" type="model" name="SculptedMonster"><components>'+''.join(f'<component objectid="{i}"/>' for i in range(1,5))+'</components></object>')
model=f'<?xml version="1.0" encoding="UTF-8"?><model unit="millimeter" xmlns="{ns}"><metadata name="Application">BambuStudio</metadata><metadata name="BambuStudio:3mfVersion">1</metadata><resources>'+''.join(resources)+'</resources><build><item objectid="5" transform="1 0 0 0 1 0 0 0 1 35 50 0"/></build></model>'
settings='<config><object id="5"><metadata key="name" value="SculptedMonster"/><metadata key="extruder" value="1"/>'
for ident,name in enumerate(NAMES,1):
 settings+=f'<part id="{ident}" subtype="normal_part"><metadata key="name" value="{name}"/><metadata key="extruder" value="{ident}"/></part>'
settings+='</object><plate><metadata key="plater_id" value="1"/><metadata key="locked" value="false"/><model_instance><metadata key="object_id" value="5"/><metadata key="instance_id" value="0"/><metadata key="identify_id" value="1"/></model_instance></plate></config>'
source=OUT/'monster-four-colour-source.3mf'
with zipfile.ZipFile(source,'w',zipfile.ZIP_DEFLATED) as z:
 z.writestr('[Content_Types].xml','<?xml version="1.0"?><Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types"><Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/><Default Extension="model" ContentType="application/vnd.ms-package.3dmanufacturing-3dmodel+xml"/><Default Extension="config" ContentType="application/xml"/></Types>')
 z.writestr('_rels/.rels','<?xml version="1.0"?><Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships"><Relationship Id="rel0" Target="/3D/3dmodel.model" Type="http://schemas.microsoft.com/3dmanufacturing/2013/01/3dmodel"/></Relationships>')
 z.writestr('3D/3dmodel.model',model)
 z.writestr('Metadata/model_settings.config',settings)
machine=resolve('machine','Bambu Lab A1 mini 0.4 nozzle')
process=resolve('process','0.20mm Standard @BBL A1M')
overrides={'enable_support':'1','support_type':'tree(auto)','support_on_build_plate_only':'1',
 'support_remove_small_overhang':'0','support_threshold_angle':'35','wall_loops':'4',
 'sparse_infill_density':'20%','brim_type':'auto_brim','brim_width':'5',
 'support_top_z_distance':'0.2','support_bottom_z_distance':'0.2','support_object_xy_distance':'0.4',
 'curr_bed_type':'Textured PEI Plate','enable_timelapse':'0',
 'wipe_tower_x':['135'],'wipe_tower_y':['100']}
process.update(overrides)
for name,data in [('machine',machine),('process',process)]:
 (OUT/f'{name}.json').write_text(json.dumps(data,indent=2))
filament_paths=[]
for i,color in enumerate(COLORS):
 f=resolve('filament','Generic PLA @BBL A1M');f['filament_colour']=[color]
 path=OUT/f'pla-{i+1}.json';path.write_text(json.dumps(f,indent=2));filament_paths.append(path)
for job,inputfile,filaments in [('monster-single-colour',OUT/'monster-face-down.stl',filament_paths[:1]),('monster-four-colour',source,filament_paths)]:
 d=OUT/job;d.mkdir(exist_ok=True)
 command=[APP,'--load-settings',str(OUT/'machine.json')+';'+str(OUT/'process.json'),
  '--load-filaments',';'.join(str(p) for p in filaments),'--slice','0','--arrange','1','--orient','0',
  '--ensure-on-bed','--export-3mf',job+'.3mf','--outputdir',str(d),str(inputfile)]
 run=subprocess.run(command,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True,timeout=240)
 (d/'slice.log').write_text(run.stdout)
 print(job,'slice result',run.returncode,flush=True)
 if run.returncode:raise RuntimeError(run.stdout[-5000:])
 project=d/(job+'.3mf');temp=d/'patched.3mf'
 with zipfile.ZipFile(project) as src,zipfile.ZipFile(temp,'w',zipfile.ZIP_DEFLATED) as dest:
  for item in src.infolist():
   data=src.read(item.filename)
   if item.filename=='Metadata/project_settings.config':
    s=json.loads(data);changed=s.get('different_settings_to_system',['','','']);changed[0]=';'.join(overrides)
    s['different_settings_to_system']=changed;data=json.dumps(s,indent=2).encode()
   dest.writestr(item,data)
 temp.replace(project)
 shutil.copy2(project,OUT/(job+'.3mf'))
 print('Saved',OUT/(job+'.3mf'),flush=True)
