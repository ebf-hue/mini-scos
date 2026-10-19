"""Generate the mini-scos bench fixture as STEP solids and STL parts (millimetres)."""
from pathlib import Path
import json, math
import cadquery as cq
from cadquery import exporters, importers

ROOT = Path(__file__).resolve().parent
P = json.loads((ROOT / 'parameters.json').read_text())
OUT = ROOT / 'exports'
OUT.mkdir(exist_ok=True)

def box(x,y,z,at=(0,0,0)):
    return cq.Workplane('XY').box(x,y,z,centered=(True,True,False)).translate(at)

def cylinder(r,length,at,axis='z'):
    shape=cq.Workplane('XY').circle(r).extrude(length)
    if axis=='x': shape=shape.rotate((0,0,0),(0,1,0),90)
    if axis=='y': shape=shape.rotate((0,0,0),(1,0,0),-90)
    return shape.translate(at)

def hole(part,r,length,at,axis='z'):
    return part.cut(cylinder(r,length,at,axis))

def carrier():
    s=box(50,84,6)
    for y in (-30,30): s=hole(s,2.8,10,(0,y,-1))
    return s

L=P['rail_segment_length']; W=P['rail_width']; axis=P['axis_height_above_rail']
rail=box(L,W,8,(L/2,0,0))
for y in (-30,30):
    slot=cq.Workplane('XY').center(L/2,y).slot2D(L-34,6).extrude(10).translate((0,0,-1))
    rail=rail.cut(slot)
for x in (20,L-20):
    for y in (-48,48):
        rail=hole(rail,2.3,10,(x,y,-1))
        # Feet provide clearance for rail-fastener nuts. No fastener under the foot.
        rail=rail.union(box(16,16,8,(x, y-10 if y<0 else y+10,-8)))
# Join holes on each segment's ends, independent of the feet.
for x in (8,L-8):
    for y in (-48,48): rail=hole(rail,2.3,10,(x,y,-1))
join=box(32,14,4)
for x in (-8,8): join=hole(join,2.3,6,(x,0,-1))

# Rear camera bracket: nominal 30 x 30 mm corner pattern from official drawing.
cam=carrier().union(box(6,50,axis+27,(0,0,6)))
cam=hole(cam,16,10,(-5,0,axis),'x')
for y in (-P['camera_hole_pitch']/2,P['camera_hole_pitch']/2):
    for z in (axis-P['camera_hole_pitch']/2,axis+P['camera_hole_pitch']/2):
        cam=hole(cam,P['camera_hole_clearance']/2,10,(-5,y,z),'x')
# Side gussets stay below the camera PCB.
for y in (-22,22):
    gusset=cq.Workplane('XZ').polyline([(3,6),(21,6),(3,axis-24)]).close().extrude(4).translate((0,y+2,0))
    cam=cam.union(gusset)
spacer=cylinder(3.2,P['camera_standoff'],(0,0,0))
spacer=hole(spacer,P['camera_hole_clearance']/2,P['camera_standoff']+2,(0,0,-1))

# Yaw is adjusted about a vertical M4 bolt; tilt about a horizontal M4 bolt.
laser_base=carrier()
laser_base=hole(laser_base,2.3,8,(0,P['laser_y'],-1))
nut=cq.Workplane('XY').polygon(6,8.4).extrude(3.4)
laser_base=laser_base.cut(nut.translate((0,P['laser_y'],0)))
clevis=cylinder(18,6,(0,0,0))
clevis=hole(clevis,2.3,8,(0,0,-1))
# Clamp axle is 20 mm below laser bore. Base thickness is 6 mm.
axle=axis-20-6
for y in (-9,9):
    clevis=clevis.union(box(20,6,axle,(0,y,6)))
clevis=hole(clevis,2.3,34,(0,-17,axle),'y')
clamp_full=box(32,30,20,(0,0,-10))
clamp_full=hole(clamp_full,(P['laser_diameter']+P['laser_diametral_clearance'])/2,36,(-18,0,0),'x')
for x in (-9,9):
    for y in (-11,11): clamp_full=hole(clamp_full,1.7,24,(x,y,-12))
lower=clamp_full.intersect(box(40,40,10,(0,0,-10)))
upper=clamp_full.intersect(box(40,40,10,(0,0,0)))
lower=lower.union(box(12,8,18,(0,0,-28)))
lower=hole(lower,2.3,12,(0,-6,-20),'y')

# Top-loading filter cassette. Film is sandwiched between two separate frames.
outer=P['filter_frame_outer']; aperture=P['filter_aperture']; slot=P['filter_slot']
frame=box(2,outer,outer,(0,0,axis-outer/2))
frame=hole(frame,aperture/2,6,(-3,0,axis),'x')
for y in (-outer/2+4,outer/2-4):
    for z in (axis-outer/2+4,axis+outer/2-4): frame=hole(frame,1.15,6,(-3,y,z),'x')
filter_base=carrier()
# Outer retaining plates, separated by slot. Aperture larger than cassette's.
for x in (-slot/2-1,slot/2+1):
    ring=box(2,outer+8,outer+8,(x,0,axis-(outer+8)/2))
    ring=hole(ring,(aperture+4)/2,12,(-6,0,axis),'x')
    filter_base=filter_base.union(ring)
for y in (-(outer+6)/2,(outer+6)/2):
    filter_base=filter_base.union(box(slot,2,axis+(outer+8)/2-6,(0,y,6)))
filter_base=filter_base.union(box(slot,outer+8,axis-outer/2-6,(0,0,6)))

# Target backing with lower ledge and tape/strap slots around the test area.
target=carrier().union(box(4,84,92,(0,0,6)))
target=target.union(box(10,80,3,(-3,0,axis-40)))
for y in (-34,34):
    for z in (axis-25,axis+25): target=target.cut(box(8,10,3,(0,y,z)))

# Optional three-sided camera hood, around camera/lens only. Ends and bottom open.
hood_length=P['hood_length']; hood_width=76; hood_top=axis+46
hood=box(hood_length,hood_width,2,(hood_length/2,0,hood_top))
for y in (-hood_width/2+1,hood_width/2-1):
    hood=hood.union(box(hood_length,2,hood_top-14,(hood_length/2,y,14)))
# Feet fasten to the rail ahead of the camera carrier.
for y in (-30,30):
    foot=box(20,18,6,(hood_length-12,y,8))
    hood=hood.union(foot).union(box(20,abs((hood_width/2-1 if y>0 else -hood_width/2+1)-y),6,(hood_length-12,(y+(hood_width/2-1 if y>0 else -hood_width/2+1))/2,8)))
    hood=hole(hood,2.8,9,(hood_length-12,y,7))

# First prints should be small coupons, before committing to full fixture parts.
laser_coupon=box(12,18,18)
laser_coupon=hole(laser_coupon,(P['laser_diameter']+P['laser_diametral_clearance'])/2,16,(-8,0,9),'x')
camera_coupon=box(3,42,42)
for y in (-15,15):
    for z in (6,36): camera_coupon=hole(camera_coupon,P['camera_hole_clearance']/2,8,(-4,y,z),'x')

parts={'rail_segment':rail,'rail_join_plate':join,'camera_bracket':cam,
       'camera_spacer':spacer,'laser_carrier':laser_base,'laser_yaw_clevis':clevis,
       'laser_clamp_lower':lower,'laser_clamp_upper':upper,'filter_holder':filter_base,
       'filter_frame':frame,'target_holder':target,'camera_hood':hood,
       'laser_fit_coupon':laser_coupon,'camera_hole_coupon':camera_coupon}
colors={'rail_segment':(0.65,0.69,0.73),'rail_join_plate':(0.35,0.4,0.45),
        'camera_bracket':(0.16,0.43,0.65),'laser_carrier':(0.82,0.42,0.12),
        'laser_yaw_clevis':(0.82,0.42,0.12),'laser_clamp_lower':(0.93,0.58,0.22),
        'laser_clamp_upper':(0.93,0.58,0.22),'filter_holder':(0.19,0.60,0.40),
        'filter_frame':(0.85,0.18,0.22),'target_holder':(0.55,0.38,0.68),
        'camera_hood':(0.18,0.20,0.23)}
placements=[('rail_segment','rail_front',(0,0,0)),('rail_segment','rail_rear',(L,0,0)),
 ('rail_join_plate','join_left',(L,-48,8)),('rail_join_plate','join_right',(L,48,8)),
 ('camera_bracket','camera_bracket',(P['camera_x'],0,8)),
 ('laser_carrier','laser_carrier',(P['laser_x'],0,8)),
 ('laser_yaw_clevis','laser_yaw_clevis',(P['laser_x'],P['laser_y'],14)),
 ('laser_clamp_lower','laser_clamp_lower',(P['laser_x'],P['laser_y'],axis+8)),
 ('laser_clamp_upper','laser_clamp_upper',(P['laser_x'],P['laser_y'],axis+8)),
 ('filter_holder','filter_holder',(P['filter_x'],0,8)),
 ('filter_frame','filter_frame_back',(P['filter_x']-1.05,0,8)),
 ('filter_frame','filter_frame_front',(P['filter_x']+1.05,0,8)),
 ('target_holder','target_holder',(P['target_x'],0,8))]
# Spacers go between rear camera plate and PCB, along the optical axis.
for i,(y,z) in enumerate([(y,z) for y in (-15,15) for z in (axis-15,axis+15)]):
    spacer_x=spacer.rotate((0,0,0),(0,1,0),90)
    parts[f'camera_spacer_x_{i}']=spacer_x
    placements.append((f'camera_spacer_x_{i}',f'camera_spacer_{i}',(P['camera_x']+3,y,z+8)))

assembly=cq.Assembly(name='mini_scos_bench_fixture_v01')
for key,name,loc in placements:
    assembly.add(parts[key],name=name,loc=cq.Location(cq.Vector(*loc)),color=cq.Color(*colors.get(key,(0.55,0.55,0.55))))
# Hood is exported individually; an optional assembly is generated separately.
assembly.save(str(OUT/'bench_fixture.step'))
assembly.add(hood,name='optional_camera_hood',loc=cq.Location(cq.Vector(P['camera_x']-8,0,0)),color=cq.Color(*colors['camera_hood']))
assembly.save(str(OUT/'bench_fixture_with_hood.step'))

validation={}
for name,part in parts.items():
    if name.startswith('camera_spacer_x_'): continue
    shape=part.val(); assert shape.isValid(), f'Invalid solid: {name}'
    assert len(part.solids().vals())==1, f'Disconnected part: {name}'
    assert shape.Volume()>0
    exporters.export(part,str(OUT/f'{name}.step'))
    # STL translated to build plate, same axes; orient tall brackets in slicer.
    bb=shape.BoundingBox()
    exporters.export(part.translate((0,0,-bb.zmin)),str(OUT/f'{name}.stl'),tolerance=0.08,angularTolerance=0.15)
    imported=importers.importStep(str(OUT/f'{name}.step')).val()
    assert imported.isValid()
    assert abs(imported.Volume()-shape.Volume())<0.01
    validation[name]={'valid':True,'solids':1,'volume_mm3':round(shape.Volume(),2),
       'bounding_box_mm':[round(v,2) for v in (bb.xlen,bb.ylen,bb.zlen)]}

# Verify unintended overlaps in the assembled printed parts. Contact faces are allowed.
interferences=[]
for i,(ka,na,la) in enumerate(placements):
    a=parts[ka].val().translate(cq.Vector(*la))
    for kb,nb,lb in placements[i+1:]:
        b=parts[kb].val().translate(cq.Vector(*lb))
        volume=a.intersect(b).Volume()
        if volume>0.05: interferences.append({'parts':[na,nb],'overlap_mm3':round(volume,3)})
hood_shape=hood.val().translate(cq.Vector(P['camera_x']-8,0,0))
for key,name,loc in placements:
    volume=hood_shape.intersect(parts[key].val().translate(cq.Vector(*loc))).Volume()
    if volume>0.05: interferences.append({'parts':['optional_camera_hood',name],'overlap_mm3':round(volume,3)})
validation['_assembly_interferences']=interferences
(OUT/'validation.json').write_text(json.dumps(validation,indent=2)+'\n')
assert not interferences, interferences

# Static preview from the actual CAD geometry, not an illustrative generated image.
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d.art3d import Poly3DCollection
from matplotlib.colors import LightSource
fig=plt.figure(figsize=(14,7)); ax=fig.add_subplot(111,projection='3d')
for key,name,loc in placements:
    s=parts[key].val().translate(cq.Vector(*loc)); vertices,triangles=s.tessellate(0.5)
    xyz=[(v.x,v.y,v.z) for v in vertices]
    poly=Poly3DCollection([[xyz[j] for j in t] for t in triangles],facecolors=colors.get(key,(0.55,0.55,0.55)),alpha=1,shade=True,lightsource=LightSource(azdeg=315,altdeg=45))
    poly.set_edgecolor('none')
    ax.add_collection3d(poly)
# Dashed references reserve the lens space and show the intended optical axis.
ax.plot([P['camera_x']+P['lens_front_offset'],P['target_x']-2],[0,0],[axis+8,axis+8],color='crimson',linestyle='--',linewidth=1.8)
ax.text(P['camera_x'],0,axis+50,'Camera bracket',fontsize=9)
ax.text(P['filter_x'],0,axis+50,'Filter cassette',fontsize=9)
ax.text(P['laser_x'],P['laser_y'],axis+37,'Laser clamp',fontsize=9)
ax.text(P['target_x'],0,axis+50,'Target',fontsize=9)
ax.set(xlim=(-5,2*L+5),ylim=(-W/2-15,W/2+15),zlim=(-8,axis+65),xlabel='Rail / X (mm)',ylabel='Y (mm)',zlabel='Z (mm)')
ax.set_box_aspect((2*L,W+30,axis+73));ax.view_init(elev=25,azim=-65)
fig.suptitle('mini-scos bench fixture · v0.1 · dimensions in mm\nHardware and fasteners omitted; dashed line is a planning reference',fontsize=14)
fig.tight_layout();fig.savefig(ROOT/'preview.png',dpi=160);plt.close(fig)
print(f'Exported {len(validation)-1} validated parts. No printed-part interferences.')
