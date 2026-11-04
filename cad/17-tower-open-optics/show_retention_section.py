"""Render an actual XZ cut through the saved mount, without changing parts."""
from pathlib import Path
import json
import cadquery as cq
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.collections import PolyCollection
ROOT=Path(__file__).resolve().parent
Y=-12.0
plate=cq.importers.importStep(str(ROOT/'parts/CameraPlate.step')).val()
retainer=cq.importers.importStep(str(ROOT/'parts/CameraRetainer.step')).val()
# Source STEP contains open PCB shells. Use the same explicitly documented
# 39 x 39 x 1.6 mm board envelope used for mechanical checking.
board=cq.Workplane('XY').box(39,39,1.6,centered=(True,True,False)).val().translate((0,0,162.5))
slab=cq.Workplane('XY').box(100,.02,40,centered=(True,True,False)).val().translate((0,Y,145))
fig,ax=plt.subplots(figsize=(12,7),dpi=180)
fig.patch.set_facecolor('#fafaf7');ax.set_facecolor('#fafaf7')
colors={'Camera plate':'#8c9aa5','PCB envelope':'#278459','Retaining lip':'#bd9052'}
for name,s in [('Camera plate',plate),('PCB envelope',board),('Retaining lip',retainer)]:
 cut=s.intersect(slab)
 # Triangulate one exact planar section face on the front of the thin slice.
 polys=[]
 for f in cut.Faces():
  b=f.BoundingBox()
  if abs(b.ymin-(Y-.01))<1e-5 and abs(b.ymax-(Y-.01))<1e-5:
   verts,tris=f.tessellate(.005)
   polys.extend([[(verts[i].x,verts[i].z) for i in t] for t in tris])
 ax.add_collection(PolyCollection(polys,facecolors=colors[name],edgecolors='none',label=name))
 # Section outlines from exact cut edges, sampled for curved intersections.
 for f in cut.Faces():
  b=f.BoundingBox()
  if abs(b.ymin-(Y-.01))<1e-5 and abs(b.ymax-(Y-.01))<1e-5:
   for e in f.Edges():
    pts,_=e.sample(30)
    ax.plot([p.x for p in pts],[p.z for p in pts],color='#353b3e',lw=.8)

def dim(a,b,label,text=None):
 ax.annotate('',xy=b,xytext=a,arrowprops=dict(arrowstyle='<->',color='#28343a',lw=1.2,shrinkA=0,shrinkB=0))
 mid=((a[0]+b[0])/2,(a[1]+b[1])/2)
 ax.text(*(text or mid),label,ha='center',va='center',fontsize=11,bbox=dict(facecolor='#fafaf7',edgecolor='none',pad=3))
# Upper lip extends 4 mm over the board's side edge.
for x in [15.5,19.5]:ax.plot([x,x],[168.5,171],color='#607078',lw=.8,ls=':')
dim((15.5,170.4),(19.5,170.4),'4.00 mm overlap',(17.5,171.05))
# Actual vertical gap between board upper face and lip underside.
ax.plot([14,20.2],[164.1,164.1],color='#607078',lw=.8,ls=':')
ax.plot([14,20.2],[164.35,164.35],color='#607078',lw=.8,ls=':')
ax.annotate('0.25 mm clearance',xy=(17,164.225),xytext=(11.9,166.9),fontsize=12,ha='left',arrowprops=dict(arrowstyle='->',connectionstyle='angle,angleA=0,angleB=90,rad=0',color='#28343a'))
ax.annotate('1.60 mm PCB',xy=(18.9,163.3),xytext=(11.8,160.0),fontsize=12,arrowprops=dict(arrowstyle='->',color='#28343a'))
ax.annotate('Lower support ledge',xy=(18.5,162.5),xytext=(21.5,154.6),fontsize=12,arrowprops=dict(arrowstyle='->',color='#28343a'))
ax.annotate('90° return around PCB edge',xy=(20.6,163.25),xytext=(26,159.5),fontsize=11,ha='center',arrowprops=dict(arrowstyle='->',color='#28343a'))
ax.annotate('0.30 mm side gap',xy=(19.65,163.2),xytext=(26,157.7),fontsize=11,ha='center',arrowprops=dict(arrowstyle='->',color='#28343a'))
ax.annotate('Printed retainer',xy=(23,167),xytext=(25,171),fontsize=12,ha='center',arrowprops=dict(arrowstyle='->',color='#28343a'))
ax.set_xlim(11,34);ax.set_ylim(153.5,172.4);ax.set_aspect('equal');ax.axis('off')
fig.suptitle('Camera PCB retention — section through the L-shaped lip',x=.08,y=.95,ha='left',fontsize=20,fontweight='bold')
fig.text(.08,.885,'Actual mount geometry at Y = −12 mm  •  right edge enlarged',fontsize=12,color='#52616a')
fig.text(.08,.055,'Green: PCB envelope used for clearance checks; original STEP board is an open shell.\nGray: lower plate   •   Gold: removable retainer   •   Assembly slides perpendicular to this section.',fontsize=10,color='#52616a',linespacing=1.5)
fig.subplots_adjust(left=.06,right=.98,bottom=.15,top=.85)
fig.savefig(ROOT/'camera-retention-section.png',facecolor=fig.get_facecolor())
# Save a separate inspection STEP; do not alter the assembly or printable parts.
cq.exporters.export(cq.Compound.makeCompound([plate.intersect(slab),retainer.intersect(slab),board.intersect(slab)]),str(ROOT/'camera-retention-section.step'))
print('Saved camera-retention-section.png and .step')
