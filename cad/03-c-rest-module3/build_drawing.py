"""Create a separate metric CADCraft drawing without touching its desktop drawing."""

import json
import math
import shutil
import subprocess
from pathlib import Path

root = Path(__file__).resolve().parent
p = json.loads((root / "parameters.json").read_text())
cli = shutil.which("cadcraft-cli")
if not cli and (Path.home() / ".local/bin/cadcraft-cli").exists():
    cli = str(Path.home() / ".local/bin/cadcraft-cli")
if not cli:
    raise SystemExit("Install CADCraft CLI and put cadcraft-cli on PATH.")
commands = []


def add(command, **params):
    commands.extend(["--cmd", command + " " + json.dumps(params)])


def line(a, b):
    add("line", points=[a, b])


def label(x, y, text, height=3):
    add("text", at=[x, y], text=text, height=height)


ri = p["rest_inner_radius_mm"]
ro = ri + p["rest_wall_mm"]
z = p["rest_lower_edge_z_mm"]
for r in (ri, ro):
    angle = math.degrees(math.asin(z / r))
    add("arc", center=[0, 0], radius=r, start=angle, end=180 - angle)
for side in (-1, 1):
    line([side * math.sqrt(ri**2 - z**2), z], [side * math.sqrt(ro**2 - z**2), z])
label(-48, 66, "C-REST / SECTION", 4)
label(-48, -23, "R43 inside / 5 wall / 70 axial width")
label(-48, -31, "Open underside; generic arm clearance")
add("dimlinear", p1=[-ro, 0], p2=[ro, 0], at=[0, -15], text="96 overall")
# Shared Module 3 PCB hole pattern (optical centre is y = 0 in the 3D model).
cx, cy = 120, 15
add("rectang", p1=[cx - 12.5, cy - 14.4], p2=[cx + 12.5, cy + 9.462])
for x in p["camera_hole_x_mm"]:
    for y in p["camera_hole_y_mm"]:
        add("circle", center=[cx + x, cy + y], radius=1.1)
add("circle", center=[cx, cy], radius=2.875)
add(
    "dimlinear",
    p1=[cx - 10.5, cy + 0.1],
    p2=[cx + 10.5, cy + 0.1],
    at=[cx, 43],
    text="21 hole centres",
)
add(
    "dimlinear",
    p1=[cx + 10.5, cy - 12.4],
    p2=[cx + 10.5, cy + 0.1],
    at=[148, cy],
    text="12.5",
)
label(95, 66, "CAMERA MODULE 3 / PCB", 4)
label(95, -23, "25 x 23.862 board / four 2.2 holes")
label(95, -31, "Printed carrier uses 2.4 clearance")
label(-48, -51, "mini-scos | prototype geometry | all dimensions mm", 3.5)
label(-48, -60, "See 3D STEP for slots, optical window, clamp and assembly.")
label(-48, -68, "Supplier dimensions; physical fit and optics remain untested.")
out = root / "exports"
out.mkdir(exist_ok=True)
subprocess.run(
    [
        cli,
        "run",
        "--metric",
        *commands,
        "--save",
        str(out / "dimensions.dxf"),
        "--export",
        str(out / "dimensions.svg"),
    ],
    check=True,
)
