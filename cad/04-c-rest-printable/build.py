"""Printed-joint C-rest. Millimetres; STEP in assembly coordinates, STLs on bed."""

import json
from pathlib import Path

import cadquery as cq
from cadquery import exporters, importers
from render import render

R = Path(__file__).resolve().parent
E = R / "exports"
E.mkdir(exist_ok=True)


def box(x, y, z, p=(0, 0, 0)):
    return cq.Workplane("XY").box(x, y, z, centered=(True, True, False)).translate(p)


def cyl(r, h, p=(0, 0, 0)):
    return cq.Workplane("XY").circle(r).extrude(h).translate(p)


def yh(x, y, z, d, h):
    return cyl(d / 2, h).rotate((0, 0, 0), (1, 0, 0), -90).translate((x, y, z))


def lp(s):
    return s.rotate((0, 0, 0), (0, 1, 0), -25).translate((-24, 0, 78))


def volume(s):
    return sum(v.Volume() for v in s.solids().vals())


def pin(length):
    # Split tapered shaft gives a printable compliant press fit; print with head on bed.
    head = cyl(4.5, 3)
    shaft = (
        cq.Workplane("XY", origin=(0, 0, 3))
        .circle(2.25)
        .workplane(offset=length)
        .circle(2)
        .loft()
    )
    return head.union(shaft).cut(box(0.8, 7, length + 1, (0, 0, 4)))


# Smooth open C shell. Print on an axial end: its circular profile is vertical in assembly.
rest = cq.Workplane("XZ").circle(48).circle(43).extrude(70).translate((0, 35, 0))
rest = rest.intersect(box(110, 72, 70, (0, 0, -8))).edges("|Y").fillet(1)
rest = rest.cut(box(32, 30, 35, (0, 0, 29)).edges("|Z").fillet(3))
for x in (-20, 20):
    socket = box(14, 12, 18, (x, 29, 34)).edges("|Z").fillet(1)
    socket = socket.cut(box(8.4, 6.4, 14, (x, 27, 42)))
    socket = socket.cut(yh(x, 20, 47, 4.3, 24))
    rest = rest.union(socket)
landing = (
    cq.Workplane("YZ")
    .polyline([(-35, 30), (-17, 48), (17, 48), (35, 30)])
    .close()
    .extrude(16)
    .translate((-37, 0, 0))
)
rest = rest.union(landing)
rest = rest.cut(cq.Workplane("XZ").circle(43).extrude(74).translate((0, 37, 0)))
for x in (-20, 20):
    rest = rest.cut(box(8.4, 6.4, 14, (x, 27, 42)))
    rest = rest.cut(yh(x, 20, 47, 4.3, 24))
for y in (-11, 11):
    rest = rest.cut(cyl(2.15, 23, (-29, y, 33)))

# One-piece removable PETG laser clip: short contact length and a compliant open jaw.
# Bore matches nominal module; print a coupon before choosing the final bore compensation.
clip = lp(
    cyl(7, 12, (0, 0, -6)).cut(cyl(5, 16, (0, 0, -8))).cut(box(3, 12, 16, (0, 6, -8)))
)
laser_holder = clip.union(box(12, 4.5, 29, (-28, -7.5, 52))).union(
    box(23, 34, 5, (-29, 0, 48))
)
for y in (-11, 11):
    laser_holder = laser_holder.cut(cyl(2.15, 8, (-29, y, 47)))


def tower(distance):
    pcb = 43 + distance + 7.43
    level = pcb + 5.5
    s = None
    for x in (-20, 20):
        leg = box(12, 10, level + 12 - 52, (x, 29, 52)).edges("|Z").fillet(0.8)
        leg = leg.union(box(8, 6, 9.7, (x, 27, 42.3)))
        leg = leg.cut(yh(x, 20, 47, 4.3, 24)).cut(yh(x, 20, level + 4, 4.3, 24))
        s = leg if s is None else s.union(leg)
    return s.union(box(52, 10, 8, (0, 29, level + 8)).edges("|Z").fillet(1))


def cassette(distance):
    pcb = 43 + distance + 7.43
    level = pcb + 5.5
    s = box(34, 34, 3, (0, -2.4, level)).edges("|Z").fillet(1)
    s = s.cut(box(22, 25, 6, (0, -2.4, level - 1)))
    # PCB slides along Y between edge tracks, no force on lens or electronics.
    for sign in (-1, 1):
        s = s.union(box(2.8, 30, 9.9, (sign * 14.1, -1, pcb - 1.4)))
        s = s.union(box(4, 30, 1.2, (sign * 13.5, -1, pcb - 1.4)))
        s = s.union(box(4, 30, 1.2, (sign * 13.5, -1, pcb + 1.52)))
        s = s.union(box(8, 22, 3, (sign * 20, 12, level)))
        ear = box(10, 5, 14, (sign * 20, 21.5, level - 4)).cut(
            yh(sign * 20, 16, level + 4, 4.3, 14)
        )
        s = s.union(ear)
    s = s.union(box(30, 1.2, 4.12, (0, -15.2, pcb - 1.4)))
    # Printed keeper slides across the entrance behind the PCB edge.
    s = s.cut(box(40, 2.8, 2.4, (0, 11.4, pcb + 0.1)))
    return s


wide_pcb = 43 + 55 + 7.43
keeper = box(35, 2.4, 2, (0, 11.4, wide_pcb + 0.3)).union(
    box(3, 5, 3, (-18, 11.4, wide_pcb - 0.2))
)
keeper = keeper.union(box(1.5, 2.4, 0.7, (16.75, 11.4, wide_pcb + 2.3)))
parts = {
    "rest": rest,
    "laser_clip": laser_holder,
    "tower_wide_55mm": tower(55),
    "tower_standard_105mm": tower(105),
    "camera_cassette": cassette(55),
    "camera_keeper": keeper,
    "locking_pin_20mm": pin(20),
    "laser_pin_19mm": pin(19),
}

# Fit coupon: socket/tenon clearance, PCB track and representative nominal laser bore.
coupon = box(40, 28, 4)
coupon = coupon.union(box(14, 12, 14, (-10, 0, 4)).cut(box(8.4, 6.4, 15, (-10, 0, 4))))
coupon = coupon.union(cyl(7, 8, (10, 0, 4)).cut(cyl(5, 10, (10, 0, 3))))
coupon = coupon.cut(cyl(2.15, 6, (0, -9, -1)))
parts["fit_coupon"] = coupon


def placed_pin(x, y, z, length=20):
    return (
        pin(length)
        .translate((0, 0, -3))
        .rotate((0, 0, 0), (1, 0, 0), -90)
        .translate((x, y, z))
    )


def scene(distance):
    dz = distance - 55
    pcb_z = wide_pcb + dz
    fixed = [
        ("rest", rest, "#6E8991"),
        ("laser_clip", laser_holder, "#CC985A"),
        ("tower", tower(distance), "#6E8991"),
        ("cassette", cassette(distance), "#6E8991"),
        ("keeper", keeper.translate((0, 0, dz)), "#CC985A"),
    ]
    for x in (-20, 20):
        fixed.append((f"base_pin_{x}", placed_pin(x, 22, 47), "#CC985A"))
        fixed.append((f"camera_pin_{x}", placed_pin(x, 18, pcb_z + 9.5), "#CC985A"))
    for y in (-11, 11):
        p = (
            pin(19)
            .translate((0, 0, -3))
            .rotate((0, 0, 0), (1, 0, 0), 180)
            .translate((-29, y, 53))
        )
        fixed.append((f"laser_pin_{y}", p, "#CC985A"))
    pcb = box(25, 23.862, 1.12, (0, -2.469, pcb_z)).edges("|Z").fillet(1)
    sensor = box(10.8, 10.8, 4.325, (0, 0, pcb_z - 4.325)).union(
        cyl(3.475, 3.105, (0, 0, pcb_z - 7.43))
    )
    conn = box(19.61, 5.71, 2.75, (0, 6.607, pcb_z + 1.12))
    laser = lp(
        importers.importStep(
            str(R.parent / "03-c-rest-module3/sources/laser_1054.step")
        ).translate((0, 0, -15.5))
    )
    refs = [
        ("PCB", pcb, "#2D7952"),
        ("lens_envelope", sensor, "#26333C"),
        ("connector", conn, "#E6DFCB"),
        ("laser", laser, "#B8B7A2"),
        ("ribbon", box(15, 30, 0.3, (0, 24.462, pcb_z + 2.5)), "#D9DDE1"),
    ]
    return fixed, refs


report = {
    "units": "mm",
    "parts": {},
    "configurations": {},
    "fit": "Unprinted; friction fits and flexible jaws require coupon testing.",
    "PCB_slot_height_mm": 1.72,
    "PCB_nominal_thickness_mm": 1.12,
    "joint_socket_clearance_per_side_mm": 0.2,
    "pin_fit": "4.5 to 4.0 tapered split shaft, 4.3 hole; interference is intentional.",
}


def bed(shape, axis=None):
    if axis == "YR":
        shape = shape.rotate((0, 0, 0), (1, 0, 0), -90)
    if axis == "Y":
        shape = shape.rotate((0, 0, 0), (1, 0, 0), 90)
    if axis == "X":
        shape = shape.rotate((0, 0, 0), (0, 1, 0), 90)
    b = shape.val().BoundingBox()
    return shape.translate((-b.xmin, -b.ymin, -b.zmin))


bed_items = []
for i, (name, shape) in enumerate(parts.items()):
    solids = shape.solids().vals()
    assert len(solids) == 1 and solids[0].isValid(), (name, len(solids))
    axis = (
        "YR"
        if name == "rest"
        else "Y"
        if name.startswith("tower")
        else "X"
        if name == "laser_clip"
        else None
    )
    oriented = bed(shape, axis)
    exporters.export(
        oriented, str(E / f"{name}.stl"), tolerance=0.05, angularTolerance=0.1
    )
    exporters.export(shape, str(E / f"{name}.step"))
    b = oriented.val().BoundingBox()
    report["parts"][name] = {
        "valid": True,
        "connected_solids": 1,
        "bed_z_min": b.zmin,
        "bed_dimensions_mm": [b.xlen, b.ylen, b.zlen],
    }
    assert max(b.xlen, b.ylen, b.zlen) < 220, (name, "exceeds 220 mm envelope")
    bed_items.append(
        (name, oriented.translate(((i % 3) * 160, (i // 3) * 160, 0)), "#6E8991")
    )

for d, label in [(55, "wide"), (105, "standard")]:
    fixed, refs = scene(d)
    # Pins intentionally interfere by a small amount to grip; check rigid structural parts.
    rigid = fixed[:5]
    collisions = {}
    for i, (n, s, _) in enumerate(rigid):
        for nn, ss, _ in rigid[i + 1 :]:
            overlap = volume(s.intersect(ss))
            collisions[n + "/" + nn] = overlap
            assert overlap < 0.01, (label, n, nn, overlap)
        for nn, ss, _ in refs[:3]:
            overlap = volume(s.intersect(ss))
            collisions[n + "/" + nn] = overlap
            assert overlap < 0.01, (label, n, nn, overlap)
    a = cq.Assembly(name=f"C_rest_printed_{label}")
    for n, s, c in fixed + refs:
        a.add(s, name=n, color=cq.Color(c))
    a.export(str(E / f"assembly_{label}.step"))
    imported = importers.importStep(str(E / f"assembly_{label}.step")).solids().vals()
    assert imported and all(s.isValid() for s in imported)
    report["configurations"][label] = {
        "working_distance_mm": d,
        "rigid_intersections_mm3": collisions,
        "STEP_solids_valid": len(imported),
    }
    render(
        fixed + refs,
        R / f"assembly_{label}.png",
        (250, -380, 220),
        (0, 0, 75 if d == 55 else 95),
        100 if d == 55 else 120,
    )
render(bed_items, R / "print_parts.png", (400, -500, 500), (120, 120, 0), 230)
(E / "validation.json").write_text(json.dumps(report, indent=2) + "\n")
print(json.dumps(report, indent=2))
