"""Actual YZ sections of the saved front and rear PCB end stops."""
from pathlib import Path
import cadquery as cq
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.collections import PolyCollection
ROOT=Path(__file__).resolve().parent
parts=[('Plate',cq.importers.importStep(str(ROOT/'parts/CameraPlate.step')).val(),'#8c9aa5'),('PCB',cq.Workplane('XY').box(39,39,1.6,centered=(True,True,False)).val().translate((0,0,162.5)),'#278459'),('Retainer',cq.importers.importStep(str(ROOT/'parts/CameraRetainer.step')).val(),'#bd9052')]
fig,axes=plt.subplots(1,2,figsize=(12,6.3),dpi=180)
fig.patch.set_facecolor('#fafaf7')
for ax,x,sign,title in zip(axes,[16,0],[-1,1],['Front stop — removable clip','Rear stop — fixed to plate']):
 slab=cq.Workplane('XY').box(.02,100,40,centered=(True,True,False)).val().translate((x,0,145))
 ax.set_facecolor('#fafaf7')
 for name,s,color in parts:
  cut=s.intersect(slab);polys=[]
  for f in cut.Faces():
   b=f.BoundingBox()
   if abs(b.xmin-(x-.01))<1e-5 and abs(b.xmax-(x-.01))<1e-5:
    v,ts=f.tessellate(.005);polys += [[(sign*v[i].y,v[i].z) for i in t] for t in ts]
    for e in f.Edges():
     points,_=e.sample(30);ax.plot([sign*p.y for p in points],[p.z for p in points],color='#353b3e',lw=.9)
  ax.add_collection(PolyCollection(polys,facecolors=color,edgecolors='none'))
 ax.set_xlim(14,26);ax.set_ylim(158.8,170);ax.set_aspect('equal');ax.axis('off');ax.set_title(title,fontsize=14,pad=20,fontweight='bold')
 ax.annotate('0.30 mm end clearance',xy=(19.65,163.3),xytext=(20,169),ha='center',fontsize=11,arrowprops=dict(arrowstyle='->',color='#28343a'))
 ax.annotate('PCB',xy=(18.4,163.3),xytext=(15.2,160),fontsize=12,color='#206b49',arrowprops=dict(arrowstyle='->',color='#206b49'))
 ax.annotate('End stop',xy=(20.5,163.6),xytext=(23.1,165.7),ha='center',fontsize=12,arrowprops=dict(arrowstyle='->',color='#28343a'))
fig.suptitle('PCB capture in Y — opposing end stops',fontsize=21,fontweight='bold',x=.06,ha='left',y=.97)
fig.text(.06,.085,'Actual sections: front at X = 16 mm; rear at X = 0 mm (between the headers).\nFront stop is split around the ribbon connector. Green: documented PCB envelope. Gray: plate. Gold: clip.',fontsize=10.5,color='#52616a',linespacing=1.7)
fig.subplots_adjust(left=.05,right=.96,top=.80,bottom=.20,wspace=.17)
fig.savefig(ROOT/'pcb-end-stops-section.png',facecolor=fig.get_facecolor())
print('Saved pcb-end-stops-section.png')
