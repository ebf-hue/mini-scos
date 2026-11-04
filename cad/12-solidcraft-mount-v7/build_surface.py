"""Build the wider laser attachment from the retained native blend reference.
The reference's native surface-blend history is saved alongside its STEP solid.
Open CASCADE widens the attachment along the rest's invariant Y axis, then
finishes the bore, slit and printed-key interface. No rest dimensions change.
"""
import subprocess
from pathlib import Path
ROOT=Path(__file__).resolve().parent
for script in ['strengthen_laser.py','finish_laser.py','validate_surface.py']:
 subprocess.run(['uv','run','--python','3.12','--with','cadquery','python',str(ROOT/script)],check=True)
