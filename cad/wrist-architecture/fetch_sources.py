"""Download the pinned official CM3 Standard STEP for rebuilding (stdlib only)."""
import hashlib
import io
from pathlib import Path
from urllib.request import urlopen
import zipfile

URL = 'https://datasheets.raspberrypi.com/camera/camera-module-3-step.zip'
NAME = 'Camera_module_3_std_model_simple.stp'
SHA256 = 'ecbc4b091e51f31c6186b81ad68d4205b8dceec0d90c116cd7fd699e1f1c5702'
DEST = Path(__file__).resolve().parent / 'sources' / NAME

def verify(data):
    if hashlib.sha256(data).hexdigest() != SHA256:
        raise ValueError('Official camera source changed; review it before updating the hash')
    return data

if DEST.exists():
    verify(DEST.read_bytes())
else:
    with urlopen(URL, timeout=60) as response:
        archive = response.read()
    with zipfile.ZipFile(io.BytesIO(archive)) as package:
        members = [n for n in package.namelist() if Path(n).name == NAME]
        if len(members) != 1:
            raise ValueError('Expected exactly one Standard camera STEP in the official archive')
        data = verify(package.read(members[0]))
    DEST.parent.mkdir(parents=True, exist_ok=True)
    DEST.write_bytes(data)
print('Verified official CM3 Standard source:', DEST)
