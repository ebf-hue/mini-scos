"""Validate the rest solid and the retained compression-band interference."""
from pathlib import Path
import json,hashlib
import cadquery as cq
ROOT=Path(__file__).resolve().parent/'surface_source'
path=ROOT/'RestFinished.step'
rest=cq.importers.importStep(str(path)).val()
band=cq.importers.importStep(str(ROOT/'LaserBand_reference.step')).val()
assert rest.isValid() and len(rest.Solids())==1 and all(s.Closed() for s in rest.Shells()) and band.isValid()
v=rest.intersect(band).Volume();assert 14<v<16
report={'pair':['Rest','LaserBand'],'method':'Open CASCADE solid intersection of STEP exports','intersection_volume_mm3':v,'expected':'Intentional reused printed compression-band press fit','rest_valid':True,'rest_shells_closed':True,'band_valid':True,'rest_sha256':hashlib.sha256(path.read_bytes()).hexdigest()}
(ROOT/'band_intersection.json').write_text(json.dumps(report,indent=2)+'\n')
