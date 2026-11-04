"""Parametric open C-rest; millimetres. Run with the adjacent requirements.txt."""

import json
from pathlib import Path

import cadquery as cq
import vtk
from cadquery import exporters, importers
from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parent
OUT = ROOT / "exports"
OUT.mkdir(exist_ok=True)
P = json.loads((ROOT / "parameters.json").read_text())


def box(x, y, z, at=(0, 0, 0)):
    return cq.Workplane("XY").box(x, y, z, centered=(True, True, False)).translate(at)


def cyl(r, h, at=(0, 0, 0)):
    return cq.Workplane("XY").circle(r).extrude(h).translate(at)


def yhole(x, y, z, diameter, length):
    return (
        cyl(diameter / 2, length).rotate((0, 0, 0), (1, 0, 0), -90).translate((x, y, z))
    )


def laser_pose(s):
    return s.rotate((0, 0, 0), (0, 1, 0), -P["laser_angle_degrees"]).translate(
        tuple(P["laser_center_mm"])
    )


ri = P["rest_inner_radius_mm"]
ro = ri + P["rest_wall_mm"]
width = P["rest_width_mm"]
# Open underside: about 199 degrees of a circular shell, no closed cuff.
rest = (
    cq.Workplane("XZ").circle(ro).circle(ri).extrude(width).translate((0, width / 2, 0))
)
rest = rest.intersect(box(110, width + 2, 70, (0, 0, P["rest_lower_edge_z_mm"])))
rest = rest.edges("|Y").fillet(1.2)
# A 32 x 30 window exposes the target beneath the camera.
rest = rest.cut(box(32, 30, 30, (0, 0, 30)).edges("|Z").fillet(3))
# Rear portal is one printable piece with the shell; two slots resist rotation.
for x in (-21, 21):
    post = box(10, 7, 162, (x, 29, 38)).edges("|Z").fillet(1)
    slot = cq.Workplane("XZ", origin=(x, 34, 155)).slot2D(80, 3.4, angle=90).extrude(10)
    rest = rest.union(post.cut(slot))
rest = rest.union(box(52, 7, 8, (0, 29, 196)).edges("|Z").fillet(2))
# Raised landing for the separate laser holder, with through-bolts accessible inside.
landing = box(23, 34, 18, (-29, 0, 30)).edges("|Z").fillet(2)
rest = rest.union(landing)
inner_clearance = (
    cq.Workplane("XZ").circle(ri).extrude(width + 2).translate((0, width / 2 + 1, 0))
)
rest = rest.cut(inner_clearance)
for y in (-11, 11):
    rest = rest.cut(cyl(1.7, 35, (-29, y, 22)))

# Camera coordinates are centred on the optical axis, not the PCB outline.
front_z = P["nominal_target_z_mm"] + P["camera_working_distance_mm"]
pcb_z = front_z + 7.43  # 11.3 overall minus 2.75 rear connector and 1.12 PCB
frame_z = pcb_z + 1.12 + 6  # clearance for rear components and FFC connector
holes = [(x, y) for x in P["camera_hole_x_mm"] for y in P["camera_hole_y_mm"]]
carrier = box(34, 34, 4, (0, -2.4, frame_z)).edges("|Z").fillet(2)
carrier = carrier.cut(box(17, 18, 8, (0, -3.4, frame_z - 1)))
for x, y in holes:
    carrier = carrier.union(cyl(2.5, 6, (x, y, pcb_z + 1.12)))
    carrier = carrier.cut(
        cyl(P["camera_mount_clearance_diameter_mm"] / 2, 15, (x, y, pcb_z))
    )
for x in (-21, 21):
    carrier = carrier.union(box(8, 24, 4, (x, 12, frame_z)))
    tab = box(9, 5, 14, (x, 23, frame_z - 4))
    tab = tab.cut(yhole(x, 19, frame_z + 4, 3.4, 12))
    carrier = carrier.union(tab)

# Two-piece cylindrical clamp, not a press-fit: actual 10 mm module + 0.4 mm bore allowance.
tube = cyl(8.5, 20, (0, 0, -10)).cut(
    cyl(P["laser_bore_diameter_mm"] / 2, 24, (0, 0, -12))
)
for x in (-10, 10):
    tube = tube.union(box(7, 10, 8, (x, 0, -4)))
    tube = tube.cut(yhole(x, -12, 0, 3.4, 24))
lower = laser_pose(tube.intersect(box(40, 20, 30, (0, -10.25, -15))))
cap = laser_pose(tube.intersect(box(40, 20, 30, (0, 10.25, -15))))
foot = box(23, 34, 5, (-29, 0, 48)).edges("|Z").fillet(2)
web = box(12, 5, 29, (-28, -8, 52))
lower = lower.union(web).union(foot)
for x in (-10, 10):
    lower = lower.cut(laser_pose(yhole(x, -15, 0, 3.4, 30)))
    lower = lower.cut(laser_pose(yhole(x, -14, 0, 7, 5.5)))
for y in (-11, 11):
    lower = lower.cut(cyl(1.7, 10, (-29, y, 46)))

# Dimension-based camera reference: shared board pattern, standard lens envelope.
pcb = (
    box(
        P["camera_pcb_width_mm"],
        P["camera_pcb_length_mm"],
        1.12,
        (0, P["camera_pcb_length_mm"] / 2 - 14.4, pcb_z),
    )
    .edges("|Z")
    .fillet(1)
)
for x, y in holes:
    pcb = pcb.cut(cyl(1.1, 4, (x, y, pcb_z - 1)))
sensor = box(10.8, 10.8, 3.875, (0, 0, front_z + 3.105))
sensor = sensor.union(cyl(2.875, 3.105, (0, 0, front_z)))
sensor = sensor.union(box(10.8, 10.8, 0.45, (0, 0, front_z + 6.98)))
glass = cyl(2.35, 0.3, (0, 0, front_z - 0.1))
connector = box(19.61, 5.71, 2.75, (0, 9.462 - 5.71 / 2, pcb_z + 1.12))
cable = box(15, 30, 0.3, (0, 9.462 + 15, pcb_z + 2.5))

# Use the existing licensed manufacturer laser STEP as the visual reference.
laser_raw = importers.importStep(str(ROOT / "sources" / "laser_1054.step"))
laser_bb = laser_raw.val().BoundingBox()
# Supplier front is Z=0; the 31 mm barrel centre is Z=15.5 (rear wires extend beyond it).
laser = laser_pose(laser_raw.translate((0, 0, -15.5)))

printed = {
    "c_rest": rest,
    "camera_carrier": carrier,
    "laser_cradle": lower,
    "laser_cap": cap,
}
parts = [(n, s, "#526B73") for n, s in printed.items()]
parts += [
    ("camera_module3_PCB_reference", pcb, "#28704A"),
    ("camera_lens_reference", sensor, "#242C32"),
    ("lens_glass_reference", glass, "#5896B6"),
    ("FFC_connector_reference", connector, "#DED9CA"),
    ("ribbon_reference", cable, "#D9DDE1"),
]
for i, s in enumerate(laser.solids().vals()):
    parts.append(
        (
            f"Adafruit1054_reference_{i}",
            cq.Workplane(obj=s),
            ["#B5BDC0", "#B99B55", "#9EBAC4", "#303438", "#C84B48"][i % 5],
        )
    )
# Metal hardware is illustrative; the passages and clamp interfaces are modelled.
for x in (-21, 21):
    screw = yhole(x, 19, frame_z + 4, 3, 20).union(yhole(x, 18, frame_z + 4, 8, 3))
    parts.append((f"camera_height_M3_{x}", screw, "#343C42"))
for x, y in holes:
    screw = cyl(1, 18, (x, y, pcb_z - 1)).union(cyl(2, 1.3, (x, y, pcb_z - 1.3)))
    parts.append((f"camera_M2_{x}_{y}", screw, "#C0C4C7"))
for x in (-10, 10):
    screw = yhole(x, -8, 0, 3, 16).union(yhole(x, -10, 0, 3.2 * 2, 2))
    parts.append((f"laser_clamp_M3_{x}", laser_pose(screw), "#BFC5C8"))

assembly = cq.Assembly(name="mini_scos_C_rest_Camera_Module_3")
validation = {
    "units": "mm",
    "parts": {},
    "printed_intersections_mm3": {},
    "laser_source_bbox_mm": [
        laser_bb.xmin,
        laser_bb.ymin,
        laser_bb.zmin,
        laser_bb.xmax,
        laser_bb.ymax,
        laser_bb.zmax,
    ],
    "camera_hole_pattern_mm": [21, 12.5],
    "nominal_lens_to_target_mm": front_z - P["nominal_target_z_mm"],
    "standard_lens_adjustment_range_mm": [
        116.7 - (7.43 + 1.12 + 6 + 4 + P["nominal_target_z_mm"]),
        193.3 - (7.43 + 1.12 + 6 + 4 + P["nominal_target_z_mm"]),
    ],
    "checks": "Solid validity, connected printed parts, STEP reimport and printed part interference; no physical or optical validation.",
}
for name, shape, colour in parts:
    solids = shape.solids().vals()
    assert solids and all(s.isValid() for s in solids), name
    if name in printed:
        assert len(solids) == 1, f"Disconnected printable part: {name}: {len(solids)}"
    assembly.add(shape, name=name, color=cq.Color(colour))
    bb = shape.val().BoundingBox()
    validation["parts"][name] = {
        "valid": True,
        "solids": len(solids),
        "bbox_mm": [bb.xlen, bb.ylen, bb.zlen],
    }
for i, (a, sa) in enumerate(printed.items()):
    for b, sb in list(printed.items())[i + 1 :]:
        overlap = sum(s.Volume() for s in sa.intersect(sb).solids().vals())
        validation["printed_intersections_mm3"][f"{a}/{b}"] = overlap
        assert overlap < 0.01, (a, b, overlap)
validation["reference_intersections_mm3"] = {}
arm_clearance_reference = (
    cq.Workplane("XZ").circle(41).extrude(230).translate((0, 115, 0))
)
for name, shape in printed.items():
    for ref_name, ref in [
        ("laser", laser),
        ("PCB", pcb),
        ("lens", sensor),
        ("rear_connector", connector),
        ("nominal_arm_R41", arm_clearance_reference),
    ]:
        overlap = sum(s.Volume() for s in shape.intersect(ref).solids().vals())
        validation["reference_intersections_mm3"][f"{name}/{ref_name}"] = overlap
        assert overlap < 0.01, (name, ref_name, overlap)
assembly.export(str(OUT / "assembly.step"))
for name, shape in printed.items():
    exporters.export(shape, str(OUT / f"{name}.step"))
    exporters.export(
        shape, str(OUT / f"{name}.stl"), tolerance=0.05, angularTolerance=0.1
    )
reimported = importers.importStep(str(OUT / "assembly.step")).solids().vals()
assert reimported and all(s.isValid() for s in reimported)
validation["STEP_reimport"] = {"solid_count": len(reimported), "all_valid": True}
(OUT / "validation.json").write_text(json.dumps(validation, indent=2) + "\n")


def render(items, path, position, focal, scale):
    ren = vtk.vtkRenderer()
    ren.SetBackground(0.95, 0.96, 0.97)
    for name, shape, colour in items:
        verts, faces = shape.val().tessellate(0.12, 0.08)
        points = vtk.vtkPoints()
        for v in verts:
            points.InsertNextPoint(v.x, v.y, v.z)
        cells = vtk.vtkCellArray()
        for face in faces:
            cells.InsertNextCell(3)
            for n in face:
                cells.InsertCellPoint(n)
        poly = vtk.vtkPolyData()
        poly.SetPoints(points)
        poly.SetPolys(cells)
        normals = vtk.vtkPolyDataNormals()
        normals.SetInputData(poly)
        normals.SetFeatureAngle(35)
        normals.Update()
        mapper = vtk.vtkPolyDataMapper()
        mapper.SetInputConnection(normals.GetOutputPort())
        actor = vtk.vtkActor()
        actor.SetMapper(mapper)
        prop = actor.GetProperty()
        prop.SetColor(*(int(colour[i : i + 2], 16) / 255 for i in (1, 3, 5)))
        prop.SetAmbient(0.25)
        prop.SetDiffuse(0.75)
        prop.SetSpecular(0.15)
        prop.SetSpecularPower(35)
        ren.AddActor(actor)
    cam = ren.GetActiveCamera()
    cam.SetPosition(*position)
    cam.SetFocalPoint(*focal)
    cam.SetViewUp(0, 0, 1)
    cam.ParallelProjectionOn()
    cam.SetParallelScale(scale)
    win = vtk.vtkRenderWindow()
    win.SetOffScreenRendering(1)
    win.SetSize(1500, 1500)
    win.SetMultiSamples(8)
    win.AddRenderer(ren)
    win.Render()
    shot = vtk.vtkWindowToImageFilter()
    shot.SetInput(win)
    shot.SetInputBufferTypeToRGB()
    shot.ReadFrontBufferOff()
    shot.Update()
    writer = vtk.vtkPNGWriter()
    writer.SetFileName(str(path))
    writer.SetInputConnection(shot.GetOutputPort())
    writer.Write()
    win.Finalize()


render(parts, ROOT / "assembly.png", (280, -430, 250), (0, 0, 95), 120)
render(parts, ROOT / "front.png", (0, -500, 120), (0, 0, 95), 120)
arm = cq.Workplane("XZ").circle(41).extrude(230).translate((0, 115, 0))
render(
    parts + [("nominal_arm_reference", arm, "#C8AA94")],
    ROOT / "on_arm.png",
    (280, -430, 250),
    (0, 0, 85),
    140,
)
exploded = []
for name, shape, colour in parts:
    offset = (
        (0, 0, 22)
        if name == "camera_carrier"
        or name.startswith(("camera_", "lens_", "FFC_", "ribbon_"))
        else (0, -45, 0)
        if name == "laser_cradle"
        else (0, 45, 0)
        if name == "laser_cap"
        else (0, 0, 0)
    )
    exploded.append((name, shape.translate(offset), colour))
render(exploded, ROOT / "exploded.png", (280, -430, 250), (0, 0, 95), 140)
font_path = "/System/Library/Fonts/Supplemental/Arial.ttf"
font_bold = "/System/Library/Fonts/Supplemental/Arial Bold.ttf"


def font(size, bold=False):
    p = Path(font_bold if bold else font_path)
    return (
        ImageFont.truetype(str(p), size)
        if p.exists()
        else ImageFont.load_default(size=size)
    )


sheet = Image.new("RGB", (2600, 1750), "#F2F5F7")
d = ImageDraw.Draw(sheet)
d.text((100, 60), "mini-scos / open C-rest", font=font(64, True), fill="#253F49")
d.text(
    (100, 145),
    "Camera Module 3 + Adafruit 1054  |  adjustable prototype",
    font=font(30),
    fill="#566A72",
)
sheet.paste(Image.open(ROOT / "assembly.png").resize((1400, 1400)), (0, 230))
sheet.paste(Image.open(ROOT / "front.png").resize((1060, 1060)), (1480, 300))
d.text((1510, 250), "FRONT / OPEN UNDERSIDE", font=font(27, True), fill="#526B73")
for i, line in enumerate(
    [
        "70 mm wide rest / 86 mm nominal inside diameter",
        "Shared Module 3 hole pattern: 21 x 12.5 mm",
        "Slotted support for standard or wide focus trials",
        "10.4 mm split clamp / removable M3 fasteners",
    ]
):
    d.text((1490, 1350 + i * 55), line, font=font(25), fill="#3A4D55")
d.line((100, 1650, 2500, 1650), fill="#B2C0C6", width=2)
d.text(
    (100, 1680),
    "CAD concept — fit, printing and optical performance still need bench testing.",
    font=font(27),
    fill="#566A72",
)
sheet.save(ROOT / "design_overview.png")
print(json.dumps(validation, indent=2))
