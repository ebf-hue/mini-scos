from pathlib import Path
import itertools,json
import cadquery as cq
R=Path(__file__).resolve().parent
regions={p.stem:cq.importers.importStep(str(p)).val() for p in (R/'parts').glob('*.step')}
for n,s in regions.items():
 print(n,'valid',s.isValid(),'solids',len(s.Solids()),flush=True)
 for i,j in itertools.combinations(range(len(s.Solids())),2):
  v=s.Solids()[i].intersect(s.Solids()[j]).Volume()
  if v>1e-5:print('INTERNAL OVERLAP',n,i,j,round(v,4),flush=True)
for (a,x),(b,y) in itertools.combinations(regions.items(),2):
 print('REGION OVERLAP',a,b,x.intersect(y).Volume(),flush=True)
