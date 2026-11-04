"""Validate and record the packaged Bambu plate using only the standard library."""
import json
from pathlib import Path
import xml.etree.ElementTree as ET
import zipfile

ROOT=Path(__file__).resolve().parent
with zipfile.ZipFile(ROOT/'print/wrist-mount-black-pla.3mf') as z:
    settings=json.loads(z.read('Metadata/project_settings.config'))
    config=ET.fromstring(z.read('Metadata/slice_info.config'))
    plates=config.findall('plate')
    assert len(plates)==1, 'Expected one sliced plate'
    plate=plates[0]
    meta={m.attrib['key']:m.attrib['value'] for m in plate.findall('metadata')}
    objects=[o.attrib for o in plate.findall('object')]
    warnings=[w.attrib for w in plate.findall('warning')]
    assert {o['name'] for o in objects}=={'WristSaddle.stl','LaserCap.stl','CameraKeeper.stl'}
    assert all(o.get('skipped')=='false' for o in objects)
    assert meta['outside']=='false' and meta['support_used']=='true'
    assert settings['printer_model']=='Bambu Lab A1 mini'
    assert settings['nozzle_diameter']==['0.4']
    assert settings['filament_colour']==['#000000']
    assert settings['filament_type']==['PLA']
    assert settings['layer_height']=='0.2' and settings['wall_loops']=='4'
    assert settings['sparse_infill_density']=='30%'
    assert settings['support_type']=='tree(auto)' and settings['support_on_build_plate_only']=='1'
    assert all(w['msg']=='not_support_traditional_timelapse' for w in warnings), warnings
    assert len(z.read('Metadata/plate_1.gcode'))>1000
    report={'printer':settings['printer_model'],'nozzle_mm':settings['nozzle_diameter'],
        'material':settings['filament_type'],'color':settings['filament_colour'],
        'layer_height_mm':settings['layer_height'],'walls':settings['wall_loops'],
        'infill':settings['sparse_infill_density'],'support':settings['support_type'],
        'support_build_plate_only':settings['support_on_build_plate_only'],
        'plate':meta,'objects':objects,'warnings':warnings,
        'physical_fit':'Not measured; no hardware fit or optical performance claimed'}
    (ROOT/'print/print-validation.json').write_text(json.dumps(report,indent=2)+'\n')
    (ROOT/'print/plate.png').write_bytes(z.read('Metadata/plate_1.png'))
print('Verified: 3 parts, one A1 mini plate, black PLA, embedded G-code, no geometry warnings')
print('Estimate:',meta['prediction'],'seconds;',meta['weight'],'g')
