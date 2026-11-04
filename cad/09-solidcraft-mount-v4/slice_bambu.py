"""Prepare local A1 mini / 0.4 mm / PLA projects; never connects to a printer."""
import json
import math
import struct
import subprocess
import sys
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent
OUT = ROOT / 'bambu'
BASE = Path('/Applications/BambuStudio.app/Contents/Resources/profiles/BBL')
APP = '/Applications/BambuStudio.app/Contents/MacOS/BambuStudio'
OUT.mkdir(exist_ok=True)
ORIENTED=OUT/'oriented'
ORIENTED.mkdir(exist_ok=True)

def rear_face_down(source, destination, working_distance):
    """Rigidly rotate the spine so its planar broad rear face rests on the bed."""
    data=bytearray(source.read_bytes())
    count=struct.unpack_from('<I',data,80)[0]
    angle=-math.pi/2-math.atan2(15.5,working_distance+3.93)
    c,s=math.cos(angle),math.sin(angle)
    def rotate(v):return (v[0],v[1]*c-v[2]*s,v[1]*s+v[2]*c)
    triangles=[]
    for i in range(count):
        p=84+50*i
        normal=rotate(struct.unpack_from('<3f',data,p))
        vertices=[rotate(struct.unpack_from('<3f',data,p+12+12*j)) for j in range(3)]
        triangles.append((normal,vertices))
    minimum=[min(v[k] for _,vs in triangles for v in vs) for k in range(3)]
    contact=0
    for i,(normal,vertices) in enumerate(triangles):
        p=84+50*i;struct.pack_into('<3f',data,p,*normal)
        vertices=[tuple(v[k]-minimum[k] for k in range(3)) for v in vertices]
        for j,v in enumerate(vertices):struct.pack_into('<3f',data,p+12+12*j,*v)
        if max(v[2] for v in vertices)<.01:
            a,b,d=vertices
            contact+=abs((b[0]-a[0])*(d[1]-a[1])-(b[1]-a[1])*(d[0]-a[0]))/2
    assert contact>1000,('Rear face did not land flat',contact)
    destination.write_bytes(data)
    return {'x_rotation_degrees':math.degrees(angle),'bed_contact_mm2':contact}

orientation={}
for filename,distance in [('SpineCamera',55),('SpineCamera_standard',105)]:
    orientation[filename]=rear_face_down(ROOT/'exports'/(filename+'.stl'),ORIENTED/(filename+'.stl'),distance)
(OUT/'orientations.json').write_text(json.dumps(orientation,indent=2)+'\n')
def resolved(group, name, seen=None):
    seen = set() if seen is None else seen
    assert name not in seen, name
    seen.add(name)
    data=json.loads((BASE/group/(name+'.json')).read_text())
    parent=data.get('inherits')
    merged=resolved(group,parent,seen.copy()) if parent else {}
    for include in data.get('include',[]):
        merged.update(resolved(group,include,seen.copy()))
    merged.update(data)
    merged.pop('inherits',None)
    merged.pop('include',None)
    return merged

machine=resolved('machine','Bambu Lab A1 mini 0.4 nozzle')
filament=resolved('filament','Generic PLA @BBL A1M')
p = resolved('process','0.20mm Standard @BBL A1M')
p.update({'enable_support':'1','support_type':'tree(auto)','support_on_build_plate_only':'1',
          'wall_loops':'4','sparse_infill_density':'30%','brim_type':'auto_brim','brim_width':'5',
          'curr_bed_type':'Textured PEI Plate','enable_timelapse':'0'})
(OUT/'a1_mini_machine.json').write_text(json.dumps(machine,indent=2)+'\n')
(OUT/'generic_pla.json').write_text(json.dumps(filament,indent=2)+'\n')
(OUT/'pla_process.json').write_text(json.dumps(p,indent=2)+'\n')
jobs = {

    'mount_wide':['Rest','SpineCamera'],
    'mount_standard':['Rest','SpineCamera_standard'],
}
results={}
for name,parts in jobs.items():
    d=OUT/name;d.mkdir(exist_ok=True)
    args=[APP,'--load-settings',str(OUT/'a1_mini_machine.json')+';'+str(OUT/'pla_process.json'),
          '--load-filaments',str(OUT/'generic_pla.json'),
          '--slice','0','--arrange','1','--orient','0','--ensure-on-bed',
          '--export-3mf',name+'.3mf','--outputdir',str(d)]
    args += [str((ORIENTED if part.startswith('SpineCamera') else ROOT/'exports')/f'{part}.stl') for part in parts]
    r=subprocess.run(args,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True,timeout=240)
    (OUT/f'{name}.log').write_text(r.stdout)
    results[name]={'exit_code':r.returncode,'parts':parts,'project':str((d/f'{name}.3mf').relative_to(ROOT))}
    (OUT/'slice_results.json').write_text(json.dumps(results,indent=2)+'\n')
    print(name,'exit:',r.returncode,flush=True)
    if r.returncode:raise RuntimeError(r.stdout[-2500:])
    # Studio reloads the named stock preset on open. Mark project overrides so it
    # retains the very same support/wall/infill settings used for CLI slicing.
    project=d/(name+'.3mf')
    temporary=d/(name+'.fixed.3mf')
    with zipfile.ZipFile(project) as source, zipfile.ZipFile(temporary,'w',zipfile.ZIP_DEFLATED) as target:
        for item in source.infolist():
            data=source.read(item.filename)
            if item.filename=='Metadata/project_settings.config':
                settings=json.loads(data)
                changes=settings.get('different_settings_to_system',['','',''])
                changes[0]=';'.join(['enable_support','support_type','support_on_build_plate_only','wall_loops','sparse_infill_density','brim_type','brim_width'])
                settings['different_settings_to_system']=changes
                data=json.dumps(settings,indent=2).encode()
            target.writestr(item,data)
    temporary.replace(project)

subprocess.run([sys.executable, str(ROOT / "pack_single_plate.py")], check=True)
