"""Render the actual camera insertion sequence without changing printable geometry."""
from pathlib import Path
import json
import cadquery as cq
from PIL import Image, ImageDraw, ImageFont
from mcp_client import SolidCraft
ROOT=Path(__file__).resolve().parent
OUT=ROOT/'insertion'; OUT.mkdir(exist_ok=True)
colors={'WristSaddle':'#8b9da9','CameraKeeper':'#d1a262','LaserCap':'#d1a262','LaserHousing':'#465058','LaserWireRed':'#cc3c39','LaserWireBlack':'#25292e','OfficialCM3_PCB':'#168f59','OfficialCM3_LensHousing':'#22272c','OfficialCM3_Connector':'#e3ddc9','OfficialCM3_Detail':'#bca66c'}
def check(r):
    if r.get('isError'): raise RuntimeError(str(r)[:2000])
for frame,travel,keepertravel in [(1,-35,-49),(2,-14,-49),(3,0,0)]:
    server=SolidCraft()
    try:
        commands=[]
        for name,color in colors.items():
            source=ROOT/'parts'/f'{name}.step'
            dy=travel if name.startswith('OfficialCM3') else keepertravel if name=='CameraKeeper' else 0
            if dy:
                source_out=OUT/f'{frame}-{name}.step'
                cq.exporters.export(cq.importers.importStep(str(source)).val().translate((0,dy,0)),str(source_out))
                source=source_out
            commands += [{'command':'file.insert_step','params':{'path':str(source),'name':name}}, {'command':'appearance.assign','params':{'components':[name],'color':color}}]
        commands.append({'command':'browser.visibility','params':{'folder':'origin','visible':False}})
        check(server.call('batch',commands=commands,verbose=False))
        check(server.call('screenshot',source='model',camera={'target':[0,-17,77],'yaw':-.35,'pitch':.22,'distance':165,'fov':.65},grid=False,axes=False,width=1000,height=850,path=str(OUT/f'step-{frame}.png')))
        print('Rendered insertion step',frame,flush=True)
    finally: server.close()
font=ImageFont.truetype('/System/Library/Fonts/Supplemental/Arial Bold.ttf',27)
small=ImageFont.truetype('/System/Library/Fonts/Supplemental/Arial.ttf',21)
canvas=Image.new('RGB',(1800,650),'#f4f6f8');d=ImageDraw.Draw(canvas)
labels=[('1  Remove the front keeper','Lens stays attached; lens faces down.'),('2  Slide into the side grooves','Move the PCB straight toward the back stop.'),('3  Refit the keeper','Two pegs locate in the front sockets.')]
for i,(title,sub) in enumerate(labels):
    im=Image.open(OUT/f'step-{i+1}.png').convert('RGB').resize((600,510))
    canvas.paste(im,(i*600,0));d.text((i*600+20,530),title,font=font,fill='#1d2932');d.text((i*600+20,575),sub,font=small,fill='#425361')
canvas.save(OUT/'camera-insertion.png')
