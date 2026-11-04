from pathlib import Path
import json
ROOT=Path(__file__).resolve().parents[1]
client=ROOT/'mcp_client.py'
namespace={'__file__':str(client),'__name__':'solidcraft_live_client'}
code=client.read_text().replace('"--headless",','"--connect", "127.0.0.1:7878",')
exec(compile(code,str(client),'exec'),namespace)
s=namespace['SolidCraft']()
def unpack(r):
 if r.get('isError'): raise RuntimeError(str(r)[:1500])
 texts='\n'.join(c.get('text','') for c in r.get('content',[]) if c.get('type')=='text')
 try:return json.loads(texts)
 except json.JSONDecodeError:return texts
try:
 state=unpack(s.call('inspect_design',measure=False,sketches=False,joints=False))
 print('Live connection:',str(state)[:450],flush=True)
finally:s.close()
