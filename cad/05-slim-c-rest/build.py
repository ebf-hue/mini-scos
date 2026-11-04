"""Slim C-rest with one swept spine, integral laser cradle and concealed printed key."""

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


def vol(s):
    return sum(x.Volume() for x in s.solids().vals())


def laser_pose(s):
    return s.rotate((0, 0, 0), (0, 1, 0), -25).translate((-19, 0, 60))


def bed(shape, axis=None):
    if axis == "rear":
        shape = shape.rotate((0, 0, 0), (1, 0, 0), -90)
    b = shape.val().BoundingBox()
    return shape.translate((-b.xmin, -b.ymin, -b.zmin))


# Smooth open shell, no strap, enclosure or separate laser pedestal.
shell = cq.Workplane("XZ").circle(48).circle(43).extrude(70).translate((0, 35, 0))
shell = shell.intersect(box(110, 72, 70, (0, 0, -8))).edges("|Y").fillet(1.2)
shell = shell.cut(box(34, 30, 30, (0, 0, 29)).edges("|Z").fillet(3))
socket = box(32, 12, 17, (0, 29, 38)).edges("|Z").fillet(2)
rest = shell.union(socket)
# Low blended shoulder supports a 12 mm long open laser collar.
shoulder = (
    cq.Workplane("XY", origin=(-25, -6, 36))
    .rect(16, 10)
    .workplane(offset=22)
    .center(4, 0)
    .rect(10, 4)
    .loft()
)
collar = laser_pose(cyl(7, 12, (0, 0, -6)).cut(box(3, 12, 16, (0, 6, -8))))
rest = rest.union(shoulder).union(collar)
rest = rest.cut(cq.Workplane("XZ").circle(43).extrude(74).translate((0, 37, 0)))
rest = rest.cut(laser_pose(cyl(5, 85, (0, 0, -45))))
# Single deep socket, with a small transverse flat-key opening hidden behind the rest.
rest = rest.cut(box(20.4, 6.4, 12, (0, 29, 45)))
rest = rest.cut(box(44, 4, 2.4, (0, 29, 49)))


def spine_camera(distance):
    pcb = 43 + distance + 7.43
    level = pcb + 5.5
    # A solid tapered fin sweeps forward into the tray instead of forming a portal.
    s = (
        cq.Workplane("XY", origin=(0, 29, 55))
        .rect(32, 8)
        .workplane(offset=10)
        .center(0, -1)
        .rect(30, 7.5)
        .workplane(offset=level + 3 - 65)
        .center(0, -13.5)
        .rect(26, 6)
        .loft()
    )
    s = s.union(box(20, 6, 9.7, (0, 29, 45.3)))
    s = s.cut(box(44, 4, 2.4, (0, 29, 49)))
    # Slim camera hood/edge tray. The upper frame protects rather than clamps the PCB.
    tray = box(31, 32, 3, (0, -2.4, level)).edges("|Z").fillet(1.5)
    tray = tray.cut(box(22, 25, 6, (0, -2.4, level - 1)))
    for sign in (-1, 1):
        tray = tray.union(box(2.8, 29, 9.9, (sign * 14.1, -1.5, pcb - 1.4)))
        tray = tray.union(box(4, 29, 1.2, (sign * 13.5, -1.5, pcb - 1.4)))
        tray = tray.union(box(4, 29, 1.2, (sign * 13.5, -1.5, pcb + 1.52)))
    tray = tray.union(box(30, 1.2, 4.12, (0, -15.2, pcb - 1.4)))
    tray = tray.cut(box(40, 2.8, 2.4, (0, 11.4, pcb + 0.1)))
    s = s.union(tray)
    # Cable is free to exit backwards through a low horizontal slot in the single spine.
    s = s.cut(box(17, 45, 2.1, (0, 28, pcb + 2.0)))
    return s


wide_pcb = 43 + 55 + 7.43
keeper = box(35, 2.4, 2, (0, 11.4, wide_pcb + 0.3))
keeper = keeper.union(box(3, 5, 3, (-18, 11.4, wide_pcb - 0.2)))
keeper = keeper.union(box(1.5, 2.4, 0.7, (16.75, 11.4, wide_pcb + 2.3)))
# Small flat friction key, printed flat; no round bolt heads or knobs.
key = (
    cq.Workplane("XY", origin=(0, 29, 49.2))
    .polyline([(-17, -2.15), (17, -1.85), (17, 1.85), (-17, 2.15)])
    .close()
    .extrude(2)
)
key = key.union(box(2, 6, 2, (-18, 29, 49.2)))

# First-print coupon: actual socket/key slot plus a short slit laser bore.
coupon = box(44, 28, 4)
coupon = coupon.union(box(26, 12, 12, (-5, 0, 4)).cut(box(20.4, 6.4, 13, (-5, 0, 4))))
coupon = coupon.cut(box(40, 4, 2.4, (-5, 0, 8)))
coupon = coupon.union(
    cyl(7, 8, (14, 4, 4)).cut(cyl(5, 10, (14, 4, 3))).cut(box(3, 10, 10, (14, 10, 3)))
)
printed = {
    "rest_with_laser_clip": rest,
    "spine_camera_wide_55mm": spine_camera(55),
    "spine_camera_standard_105mm": spine_camera(105),
    "camera_keeper": keeper,
    "flat_locking_key": key,
    "fit_coupon": coupon,
}
laser = laser_pose(
    importers.importStep(
        str(R.parent / "03-c-rest-module3/sources/laser_1054.step")
    ).translate((0, 0, -15.5))
)


def scene(distance):
    pcb_z = 43 + distance + 7.43
    hardware = [
        ("rest", rest, "#6E858A"),
        ("spine_and_tray", spine_camera(distance), "#6E858A"),
        ("keeper", keeper.translate((0, 0, distance - 55)), "#6E858A"),
        ("hidden_key", key, "#AEB8BA"),
    ]
    board = box(25, 23.862, 1.12, (0, -2.469, pcb_z)).edges("|Z").fillet(1)
    lens = box(10.8, 10.8, 4.325, (0, 0, pcb_z - 4.325)).union(
        cyl(3.475, 3.105, (0, 0, pcb_z - 7.43))
    )
    conn = box(19.61, 5.71, 2.75, (0, 6.607, pcb_z + 1.12))
    ribbon = box(15, 34, 0.3, (0, 26.462, pcb_z + 2.5))
    refs = [
        ("PCB", board, "#387756"),
        ("lens", lens, "#253037"),
        ("connector", conn, "#DBD4C0"),
        ("ribbon", ribbon, "#D0D5D7"),
        ("Adafruit1054", laser, "#AEA993"),
    ]
    return hardware, refs


report = {
    "units": "mm",
    "printed_parts": {},
    "configurations": {},
    "expected_contact": "Flat key has intentional lateral taper interference at its socket. All other rigid pairs must have zero overlap.",
    "scope": "Nominal static geometry, beam/line-of-sight clearance, STEP and closed mesh checks. No physical print, strength or optical validation.",
}

for name, shape in printed.items():
    solids = shape.solids().vals()
    assert len(solids) == 1 and solids[0].isValid(), (name, len(solids))
    oriented = bed(shape, "rear" if name == "rest_with_laser_clip" else None)
    exporters.export(shape, str(E / f"{name}.step"))
    exporters.export(
        oriented, str(E / f"{name}.stl"), tolerance=0.05, angularTolerance=0.1
    )
    bb = oriented.val().BoundingBox()
    report["printed_parts"][name] = {
        "valid_solid": True,
        "bed_dimensions_mm": [bb.xlen, bb.ylen, bb.zlen],
        "min_z_mm": bb.zmin,
    }
    assert max(bb.xlen, bb.ylen, bb.zlen) < 180, (name, "exceeds 180 mm envelope")

arm = cq.Workplane("XZ").circle(41).extrude(180).translate((0, 90, 0))
beam = laser_pose(cyl(0.5, 9, (0, 0, -24.5)))
for distance, label in [(55, "wide"), (105, "standard")]:
    hardware, refs = scene(distance)
    collisions = {}
    intentional = {}
    for i, (n, s, _) in enumerate(hardware):
        for nn, ss, _ in hardware[i + 1 :]:
            overlap = vol(s.intersect(ss))
            if nn == "hidden_key" and n in ("rest", "spine_and_tray"):
                intentional[n + "/" + nn] = overlap
                assert overlap < 6, (label, "excessive key interference", n, overlap)
            else:
                collisions[n + "/" + nn] = overlap
                assert overlap < 0.01, (label, n, nn, overlap)
        for nn, ss, _ in refs + [
            ("nominal_arm", arm, ""),
            ("laser_center_beam", beam, ""),
            ("camera_line_of_sight", cyl(2, distance - 0.2, (0, 0, 43.1)), ""),
        ]:
            overlap = vol(s.intersect(ss))
            collisions[n + "/" + nn] = overlap
            assert overlap < 0.01, (label, n, nn, overlap)
    a = cq.Assembly(name=f"Slim_C_rest_{label}")
    for n, s, c in hardware + refs:
        a.add(s, name=n, color=cq.Color(c))
    a.export(str(E / f"assembly_{label}.step"))
    imported = importers.importStep(str(E / f"assembly_{label}.step")).solids().vals()
    assert imported and all(x.isValid() for x in imported)
    report["configurations"][label] = {
        "lens_to_target_mm": distance,
        "unintended_overlap_mm3": collisions,
        "intentional_key_interference_mm3": intentional,
        "STEP_valid_solids": len(imported),
    }
    render(
        hardware + refs,
        R / f"assembly_{label}.png",
        (235, -365, 205),
        (0, 0, 65 if distance == 55 else 85),
        95 if distance == 55 else 115,
    )
    if label == "wide":
        render(
            hardware + refs + [("arm_reference", arm, "#C6AE99")],
            R / "on_arm.png",
            (235, -365, 205),
            (0, 0, 50),
            112,
        )
        exploded = [
            (n, s.translate((0, 0, 25 if n == "spine_and_tray" else 0)), c)
            for n, s, c in hardware
        ]
        render(exploded, R / "exploded.png", (235, -365, 205), (0, 0, 75), 110)
(E / "collision_validation.json").write_text(json.dumps(report, indent=2) + "\n")
print(json.dumps(report, indent=2))
