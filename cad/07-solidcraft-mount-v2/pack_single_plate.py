from pathlib import Path
import xml.etree.ElementTree as ET,zipfile,json,subprocess
root=Path(__file__).resolve().parent/'bambu'
ns='http://schemas.microsoft.com/3dmanufacturing/core/2015/02';prod='http://schemas.microsoft.com/3dmanufacturing/production/2015/06'
ET.register_namespace('',ns);ET.register_namespace('p',prod);ET.register_namespace('BambuStudio','http://schemas.bambulab.com/package/2021')
q=lambda t:'{'+ns+'}'+t
for variant in ['wide','standard']:
 name='mount_'+variant;src=root/name/(name+'.3mf');d=root/(name+'_single');d.mkdir(exist_ok=True)
 with zipfile.ZipFile(src) as z:
  model=ET.fromstring(z.read('3D/3dmodel.model'));settings=ET.fromstring(z.read('Metadata/model_settings.config'))
  names={o.attrib['id']:next(m.attrib['value'] for m in o.findall('metadata') if m.attrib.get('key')=='name') for o in settings.findall('object')}
  bounds={};ids={}
  for obj in model.find(q('resources')).findall(q('object')):
   oid=obj.attrib['id'];c=obj.find(q('components')).find(q('component'));leaf=ET.fromstring(z.read(c.attrib['{'+prod+'}path'].lstrip('/')))
   transform=list(map(float,c.attrib.get('transform','1 0 0 0 1 0 0 0 1 0 0 0').split()))
   verts=[tuple(float(v.attrib[k])+transform[9+i] for i,k in enumerate(['x','y','z'])) for v in leaf.findall('.//'+q('vertex'))]
   part=names[oid];rotate=part.startswith('SpineCamera')
   points=[(-y,x,zv) if rotate else (x,y,zv) for x,y,zv in verts]
   lo=[min(v[k] for v in points) for k in range(3)];hi=[max(v[k] for v in points) for k in range(3)]
   xy=(12,8) if part=='Rest.stl' else (18,125) if rotate else (120,100) if part=='Keeper.stl' else (16,105) if part=='LockingKey.stl' else (150,52)
   offset=[xy[0]-lo[0],xy[1]-lo[1],-lo[2]]
   matrix=[0,1,0,-1,0,0,0,0,1] if rotate else [1,0,0,0,1,0,0,0,1]
   ids[oid]=matrix+offset
   bounds[part]=[[xy[0],xy[1],0],[xy[0]+hi[0]-lo[0],xy[1]+hi[1]-lo[1],hi[2]-lo[2]]]
   assert all(v<=175 for v in bounds[part][1][:2]),bounds[part]
  for item in model.find(q('build')).findall(q('item')):item.set('transform',' '.join(map(str,ids[item.attrib['objectid']])))
  plates=settings.findall('plate');instances=[i for plate in plates for i in plate.findall('model_instance')]
  for i in list(plates[0].findall('model_instance')):plates[0].remove(i)
  for i in instances:plates[0].append(i)
  for plate in plates[1:]:settings.remove(plate)
  changes={'3D/3dmodel.model':ET.tostring(model,encoding='utf-8',xml_declaration=True),'Metadata/model_settings.config':ET.tostring(settings,encoding='utf-8',xml_declaration=True)}
  packed=d/'layout.3mf'
  with zipfile.ZipFile(packed,'w',zipfile.ZIP_DEFLATED) as out:
   for item in z.infolist():
    if item.filename.endswith('.gcode') or item.filename=='Metadata/slice_info.config':continue
    out.writestr(item,changes.get(item.filename,z.read(item.filename)))
 (d/'layout_bounds.json').write_text(json.dumps(bounds,indent=2))
 args=['/Applications/BambuStudio.app/Contents/MacOS/BambuStudio','--load-settings',str(root/'a1_mini_machine.json')+';'+str(root/'pla_process.json'),'--load-filaments',str(root/'generic_pla.json'),'--slice','0','--arrange','0','--orient','0','--ensure-on-bed','--export-3mf',name+'_single.3mf','--outputdir',str(d),str(packed)]
 r=subprocess.run(args,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True,timeout=240);(d/'slice.log').write_text(r.stdout);print(variant,r.returncode,r.stdout[-1000:],flush=True);assert r.returncode==0
 final=d/(name+'_single.3mf');tmp=d/'fixed.3mf'
 with zipfile.ZipFile(final) as z,zipfile.ZipFile(tmp,'w',zipfile.ZIP_DEFLATED) as out:
  for item in z.infolist():
   data=z.read(item.filename)
   if item.filename=='Metadata/project_settings.config':
    st=json.loads(data);st['different_settings_to_system'][0]=';'.join(['enable_support','support_type','support_on_build_plate_only','wall_loops','sparse_infill_density','brim_type','brim_width']);data=json.dumps(st,indent=2).encode()
   out.writestr(item,data)
 tmp.replace(final)
