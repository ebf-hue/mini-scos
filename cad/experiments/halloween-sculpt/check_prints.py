"""Audit the packaged 3MFs after slicing; do not contact a printer."""
from pathlib import Path
import json,zipfile
import xml.etree.ElementTree as ET
ROOT=Path(__file__).resolve().parent
reports={}
for job,colours in [('monster-single-colour',1),('monster-four-colour',4)]:
 with zipfile.ZipFile(ROOT/'print'/(job+'.3mf')) as z:
  config=ET.fromstring(z.read('Metadata/slice_info.config'))
  plates=config.findall('plate');assert len(plates)==1
  plate=plates[0];meta={e.attrib['key']:e.attrib['value'] for e in plate.findall('metadata')}
  assert meta['outside']=='false' and meta['support_used']=='true'
  assert len(plate.findall('object'))==1
  assert len(plate.findall('filament'))==colours
  warnings=[w.attrib for w in plate.findall('warning')]
  assert all(w['msg']=='not_support_traditional_timelapse' for w in warnings),warnings
  settings=json.loads(z.read('Metadata/project_settings.config'))
  assert settings['printer_model']=='Bambu Lab A1 mini'
  assert settings['nozzle_diameter']==['0.4']
  assert settings['layer_height']=='0.2' and settings['wall_loops']=='4'
  assert settings['sparse_infill_density']=='20%'
  assert settings['support_type']=='tree(auto)' and settings['support_on_build_plate_only']=='1'
  assert len(z.read('Metadata/plate_1.gcode'))>1000
  objects=ET.fromstring(z.read('Metadata/model_settings.config')).findall('object')
  assert len(objects)==1
  parts=objects[0].findall('part');assert len(parts)==colours
  for p in parts:
   stat=p.find('mesh_stat')
   assert stat is not None
   assert all(int(v)==0 for k,v in stat.attrib.items() if k!='face_count'),stat.attrib
  if colours==4:
   assigned=[]
   for p in parts:
    assigned.extend(m.attrib['value'] for m in p.findall('metadata') if m.attrib.get('key')=='extruder')
   assert assigned==['1','2','3','4'],assigned
  reports[job]={'estimate_seconds':int(meta['prediction']),'weight_g':float(meta['weight']),
   'plate_count':1,'physical_objects':1,'material_parts':len(parts),'outside_print_area':False,
   'supports':True,'mesh_repairs':0,'warnings':warnings,
   'material_colors':[f.attrib['color'] for f in plate.findall('filament')],
   'sha256':__import__('hashlib').sha256((ROOT/'print'/(job+'.3mf')).read_bytes()).hexdigest()}
(ROOT/'print/validation.json').write_text(json.dumps(reports,indent=2))
print(json.dumps(reports,indent=2))
