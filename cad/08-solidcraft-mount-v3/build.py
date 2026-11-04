"""V3: rounded laser cradle and front-load camera, with continuous insertion checks."""

import json
import math
from pathlib import Path

from mcp_client import SolidCraft

ROOT = Path(__file__).resolve().parent
OUT = ROOT / "exports"
OUT.mkdir(exist_ok=True)
stages = [[], [], [], []]
stage = 0


def cmd(command, **params):
    stages[stage].append({"command": command, "params": params})


def polygon(name, points, plane="XY", offset=None):
    kw = {"name": name, "plane": plane}
    if offset is not None:
        kw["offset"] = offset
    cmd("sketch.create", **kw)
    cmd("sketch.line", points=points, closed=True, connect=False, infer=False)
    cmd(
        "sketch.constraint.fix",
        entities=[f"l{i + 1}" for i in range(len(points))],
        fixed=True,
    )
    cmd("sketch.solve")
    cmd("sketch.finish")


def rectangle(name, w, h, cx=0, cy=0, z=0):
    polygon(
        name,
        [
            [cx - w / 2, cy - h / 2],
            [cx + w / 2, cy - h / 2],
            [cx + w / 2, cy + h / 2],
            [cx - w / 2, cy + h / 2],
        ],
        offset=z,
    )


def circle(name, r, plane="XY", offset=None):
    kw = {"name": name, "plane": plane}
    if offset is not None:
        kw["offset"] = offset
    cmd("sketch.create", **kw)
    cmd("sketch.circle.center", center=[0, 0], radius=r, connect=False)
    cmd("sketch.constraint.fix", entities=["c1"], fixed=True)
    cmd("sketch.solve")
    cmd("sketch.finish")


def extrude(name, d, op="new", body=None, targets=None):
    kw = {"name": name, "distance": d, "operation": op}
    if body:
        kw["body_name"] = body
    if targets:
        kw["targets"] = targets
    cmd("solid.extrude", **kw)


def block(name, w, d, h, cx, cy, z, op="new", body=None, target=None):
    kw = {
        "name": name,
        "length": w,
        "width": d,
        "height": h,
        "corner": [cx - w / 2, cy - d / 2, z],
        "operation": op,
    }
    if body:
        kw["body_name"] = body
    if target:
        kw["targets"] = [target]
    cmd("solid.box", **kw)


def rect_cut(name, w, d, h, cx, cy, z, target):
    rectangle(name + "Sketch", w, d, cx, cy, z)
    extrude(name, h, "cut", targets=[target])


def unwrap(result):
    if result.get("isError"):
        raise RuntimeError(json.dumps(result)[:3500])
    text = "\n".join(
        c.get("text", "") for c in result.get("content", []) if c.get("type") == "text"
    )
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        return text


# First stage has an independently calculable volume, bbox and centroid.
cmd(
    "parameters.add",
    name="working_distance",
    expression="55 mm",
    comment="Mechanical range 55..105 mm. Use 55 for Wide; 105 for Standard. Focus requires bench testing.",
    favorite=True,
)
cmd(
    "parameters.add",
    name="board_z",
    expression="43 mm + working_distance + 7.43 mm",
    comment="Derived nominal board front Z",
)
cmd(
    "parameters.add",
    name="tray_z",
    expression="board_z + 5.5 mm",
    comment="Derived tray underside Z",
)
cmd(
    "sketch.create",
    name="RestCProfile",
    plane={"origin": [0, 35, 0], "x_dir": [1, 0, 0], "y_dir": [0, 0, 1]},
)
a = math.radians(-10)
outer = [48 * math.cos(a), 48 * math.sin(a)]
inner = [43 * math.cos(a), 43 * math.sin(a)]
cmd("sketch.arc.center_point", center=[0, 0], start=outer, sweep=200, connect=False)
cmd(
    "sketch.arc.center_point",
    center=[0, 0],
    start=[-inner[0], inner[1]],
    sweep=-200,
    connect=False,
)
cmd(
    "sketch.line",
    points=[[-outer[0], outer[1]], [-inner[0], inner[1]]],
    connect=False,
    infer=False,
)
cmd("sketch.line", points=[inner, outer], connect=False, infer=False)
cmd("sketch.constraint.fix", entities=["a1", "a2", "l1", "l2"], fixed=True)
cmd("sketch.solve")
cmd("sketch.finish")
extrude("WideOpenRest", 70, body="Rest")

stage = 1
rect_cut("OpticalWindow", 34, 30, 28, 0, 0, 29, "Rest")
# Pad starts above the inner radius, so no later coincident-bore recut is needed.
block("SpineSocketLanding", 32, 12, 11, 0, 29, 44, "join", target="Rest")
axis = [-math.sin(math.radians(25)), 0, math.cos(math.radians(25))]


def laser_point(t):
    return [-19 + axis[0] * t, 0, 60 + axis[2] * t]


# Rounded barrel cradle with generous edge radii and a broad root.
cmd("solid.cylinder", name="RoundedCradleRoot", radius=11, height=32,
    base=[-26,-16,48], axis="Y", operation="new", body_name="CradleTool")
cmd("solid.fillet", name="RoundedCradleEnds", edges=[[-15,-16,48],[-15,16,48]], radius=2)
cmd("solid.combine", target="Rest", tools=["CradleTool"], operation="join", keep_tools=False)
cmd("solid.cylinder", name="IntegratedLaserCollar", radius=7, height=12,
    base=laser_point(-6), axis=axis, operation="join", targets=["Rest"])
cmd("solid.cylinder", name="ReinforcedLowerCollar", radius=8.5, height=8,
    base=laser_point(-6.5), axis=axis, operation="join", targets=["Rest"])

laser_plane = {
    "origin": laser_point(-45),
    "x_dir": [axis[2], 0, -axis[0]],
    "y_dir": [0, 1, 0],
}
circle("LaserBoreSketch", 5.1, plane=laser_plane)
extrude("LaserBarrelBore", 90, "cut", targets=["Rest"])
slit_plane = {**laser_plane, "origin": laser_point(-7)}
polygon(
    "CollarComplianceSlit",
    [[-1.5, 0], [1.5, 0], [1.5, 12], [-1.5, 12]],
    plane=slit_plane,
)
extrude("OpenLaserCollar", 14, "cut", targets=["Rest"])
rect_cut("SpineTenonSocket", 20.4, 6.4, 12, 0, 29, 45, "Rest")
rect_cut("ConcealedKeySlotRest", 44, 4, 2.4, 0, 29, 49, "Rest")

stage = 2
rectangle("SpineBaseSection", 32, 8, 0, 29, 55)
rectangle("SpineTopSection", 26, 6, 0, 14.5, "tray_z + 3 mm")
cmd(
    "solid.loft",
    name="SingleTaperedSpine",
    sections=[{"sketch": "SpineBaseSection"}, {"sketch": "SpineTopSection"}],
    operation="new",
    body_name="SpineCamera",
)
block("ConcealedTenon", 20, 6, 10, 0, 29, 45.3, "join", target="SpineCamera")
rect_cut("ConcealedKeySlotSpine", 44, 4, 2.4, 0, 29, 49, "SpineCamera")
block("SlimTrayTop", 31, 32, 3, 0, -2.4, "tray_z", "join", target="SpineCamera")
rect_cut("TrayAccessWindow", 22, 25, 6, 0, -2.4, "tray_z - 1 mm", "SpineCamera")
for sign, label in [(-1, "Left"), (1, "Right")]:
    block(
        label + "BoardEdgeWall",
        2.8,
        29,
        9.9,
        sign * 14.3,
        -1.5,
        "board_z - 1.4 mm",
        "join",
        target="SpineCamera",
    )
    block(
        label + "BoardLowerLip",
        4,
        29,
        1.2,
        sign * 13.5,
        -1.5,
        "board_z - 1.4 mm",
        "join",
        target="SpineCamera",
    )
    block(
        label + "BoardUpperLip",
        4,
        29,
        1.2,
        sign * 13.5,
        -1.5,
        "board_z + 1.52 mm",
        "join",
        target="SpineCamera",
    )
for sign,label in [(-1,'Left'),(1,'Right')]:
    block(label+'RearBoardStop',3,1.2,2.1,sign*11.5,10.5,'board_z - 0.3 mm','join',target='SpineCamera')
rect_cut("FrontLoadingGateGuide", 40, 2.8, 2.4, 0, -15.9, "board_z + 0.1 mm", "SpineCamera")
rect_cut("RearRibbonExit", 17, 45, 2.1, 0, 28, "board_z + 2 mm", "SpineCamera")
block("SlidingBoardKeeper", 35, 2.4, 2, 0, -15.9, "board_z + 0.3 mm", body="Keeper")
block("KeeperEndStop", 3, 5, 2, -18, -15.9, "board_z + 0.3 mm", "join", target="Keeper")
block(
    "KeeperRetentionNib",
    1.5,
    2.4,
    0.7,
    16.75,
    -15.9,
    "board_z + 2.3 mm",
    "join",
    target="Keeper",
)
polygon(
    "FlatKeySketch", [[-17, 26.85], [17, 27.15], [17, 30.85], [-17, 31.15]], offset=49.2
)
extrude("FlatFrictionKey", 2, body="LockingKey")
block("KeyPullTab", 2, 6, 2, -18, 29, 49.2, "join", target="LockingKey")

stage = 3
# Separate small compression band over the free end of the slit collar. Nominal
# overlap with the outside of the flexible collar is intentional, not laser intrusion.
band_plane = {**laser_plane, "origin": laser_point(3.5)}
cmd("sketch.create", name="LaserBandProfile", plane=band_plane)
cmd("sketch.circle.center", center=[0, 0], radius=8.5, connect=False)
cmd("sketch.circle.center", center=[0, 0], radius=6.85, connect=False)
cmd("sketch.constraint.fix", entities=["c1", "c2"], fixed=True)
cmd("sketch.solve")
cmd("sketch.finish")
extrude("LaserCompressionBand", 3, body="LaserBand")
cmd(
    "sketch.create",
    name="FitCollarProfile",
    plane={"origin": [120, 0, 0], "x_dir": [1, 0, 0], "y_dir": [0, 1, 0]},
)
cmd("sketch.circle.center", center=[0, 0], radius=7, connect=False)
cmd("sketch.circle.center", center=[0, 0], radius=5.1, connect=False)
cmd("sketch.constraint.fix", entities=["c1", "c2"], fixed=True)
cmd("sketch.solve")
cmd("sketch.finish")
extrude("FirstPrintFitCollar", 12, body="FitCollar")
rect_cut("FitCollarSlit", 3, 12, 14, 120, 6, -1, "FitCollar")
block("CameraPCBReference", 25, 23.862, 1.12, 0, -2.469, "board_z", body="CameraPCB")
block(
    "LensHousingReference",
    10.8,
    10.8,
    4.325,
    0,
    0,
    "board_z - 4.325 mm",
    body="CameraLens",
)
cmd(
    "solid.cylinder",
    name="WideLensClearanceEnvelope",
    radius=3.475,
    height=3.3,
    base=[0, 0, "board_z - 7.43 mm"],
    operation="join",
    targets=["CameraLens"],
)
block(
    "RearConnectorReference",
    19.61,
    5.71,
    2.75,
    0,
    6.607,
    "board_z + 1.12 mm",
    body="CameraConnector",
)
block("RibbonReference", 15, 34, 0.3, 0, 26.462, "board_z + 2.5 mm", body="Ribbon")
cmd(
    "solid.cylinder",
    name="Adafruit1054Envelope",
    radius=5,
    height=31,
    base=laser_point(-15.5),
    axis=axis,
    operation="new",
    body_name="LaserModule",
)
cmd(
    "solid.cylinder",
    name="ForearmClearanceGauge",
    radius=41,
    height=180,
    base=[0, -90, 0],
    axis="Y",
    operation="new",
    body_name="ArmGauge",
)
# Exact box sweeps for the PCB/housing/connector and a conservative box sweep
# around the circular lens. Camera loads from -Y with gate and ribbon removed.
path_names=['PathPCB','PathHousing','PathLens','PathConnector']
block('PCBFrontInsertionSweep',25.4,64.262,1.32,0,-22.469,'board_z - 0.1 mm',body='PathPCB')
block('HousingFrontInsertionSweep',11.2,51.2,4.525,0,-20,'board_z - 4.425 mm',body='PathHousing')
block('LensFrontInsertionSweep',7.35,47.35,3.5,0,-20,'board_z - 7.53 mm',body='PathLens')
block('ConnectorFrontInsertionSweep',20.01,46.11,2.95,0,-13.393,'board_z + 1.02 mm',body='PathConnector')
for bodies, color in [
    (["Rest", "SpineCamera", "Keeper"], "#6E858A"),
    (["LockingKey", "LaserBand"], "#ABB5B7"),
    (["CameraPCB"], "#337650"),
    (["CameraLens"], "#252D32"),
    (["CameraConnector"], "#D8CFB6"),
    (["Ribbon"], "#D1D6D9"),
    (["LaserModule"], "#AE9D70"),
    (["ArmGauge"], "#C7AB94"),
]:
    cmd("appearance.assign", bodies=bodies, color=color)
cmd("browser.visibility", items=["ArmGauge", "FitCollar",*path_names], visible=False)
cmd("browser.visibility", folder="sketches", visible=False)
cmd("browser.visibility", folder="origin", visible=False)

(ROOT / "build_commands.json").write_text(
    json.dumps(
        {"commands": [command for items in stages for command in items]}, indent=2
    )
    + "\n"
)


def check_timeline(design):
    bad = [f for f in design.get("timeline", []) if f.get("error") or f.get("warning")]
    if bad:
        raise RuntimeError("Timeline diagnostics: " + json.dumps(bad)[:2500])
    sketches = design.get("sketches", [])
    loose = [s for s in sketches if isinstance(s, dict) and s.get("dof", 0) != 0]
    if loose:
        raise RuntimeError("Unconstrained sketches: " + json.dumps(loose)[:1500])


def build():
    s = SolidCraft()
    try:
        initial = unwrap(s.call("inspect_design", measure=False, sketches=False))
        assert not initial.get("timeline"), (
            "Refusing to discard a nonempty SolidCraft design"
        )
        for i, commands in enumerate(stages):
            print("STAGE", i + 1, "commands", len(commands), flush=True)
            result = unwrap(s.call("batch", commands=commands, verbose=False))
            (OUT / f"stage_{i + 1}.json").write_text(
                json.dumps(result, indent=2) + "\n"
            )
            if isinstance(result, dict) and (
                result.get("failed") or result.get("ok") is False
            ):
                raise RuntimeError(json.dumps(result)[:3500])
            measured = unwrap(s.call("measure"))
            if i == 0:
                expected = 0.5 * (48**2 - 43**2) * math.radians(200) * 70
                actual = measured["bodies"][0]["volume_mm3"]
                assert abs(actual - expected) / expected < 0.001, (actual, expected)
            (OUT / f"measure_stage_{i + 1}.json").write_text(
                json.dumps(measured, indent=2) + "\n"
            )
            design = unwrap(s.call("inspect_design", measure=False, sketches=False))
            check_timeline(design)
        unwrap(s.call("save", path=str(ROOT / "mount.json"), format="json"))
        unwrap(s.call("save", path=str(ROOT / "mount.solidcraft")))
        checks = {}
        for distance, label in [(55, "wide"), (105, "standard"), (55, "wide_restored")]:
            unwrap(
                s.call("set_parameter", name="working_distance", value=f"{distance} mm")
            )
            design = unwrap(s.call("inspect_design", measure=False, sketches=False))
            check_timeline(design)
            r = unwrap(
                s.call(
                    "execute",
                    command="inspect.interference",
                    params={"budget_s": 120,'bodies':['Rest','SpineCamera','Keeper','LockingKey','LaserBand','FitCollar','CameraPCB','CameraLens','CameraConnector','Ribbon','LaserModule','ArmGauge']},
                    verbose=False,
                )
            )
            checks[label] = r
            (OUT / "collision_checks.json").write_text(
                json.dumps(checks, indent=2) + "\n"
            )
            print("COLLISIONS", label, json.dumps(r)[:1600], flush=True)
            assert (
                not r.get("unchecked")
                and not r.get("budget_exceeded")
                and not r.get("truncated")
            ), r
            allowed = {
                frozenset(["Rest", "LockingKey"]),
                frozenset(["SpineCamera", "LockingKey"]),
                frozenset(["Rest", "LaserBand"]),
            }
            for pair in r.get("interferences", []):
                names = frozenset([pair.get("a"), pair.get("b")])
                if names not in allowed:
                    raise RuntimeError("Unintended interference " + json.dumps(pair))
            path=unwrap(s.call('execute',command='inspect.interference',params={
                'bodies':['Rest','SpineCamera','LockingKey','LaserBand','LaserModule',*path_names],
                'budget_s':120},verbose=False))
            assert not path.get('unchecked') and not path.get('budget_exceeded') and not path.get('truncated'),path
            blocked=[p for p in path.get('interferences',[]) if
                     (p.get('a') in path_names) != (p.get('b') in path_names)]
            assert not blocked,('Continuous front insertion is blocked',blocked)
            evidence={'method':'40 mm straight translation from -Y to seated camera, gate/ribbon removed; conservative continuous envelopes for all module components',
                      'blocked_pairs':blocked,'native_result':path}
            (OUT/f'assembly_path_{label}.json').write_text(json.dumps(evidence,indent=2)+'\n')
            print('FRONT INSERTION CLEAR',label,flush=True)
            if label == "wide_restored":
                break
            if label == "standard":
                mm = unwrap(
                    s.call(
                        "execute",
                        command="inspect.measure",
                        params={"bodies": ["SpineCamera"]},
                        verbose=False,
                    )
                )
                xyz = mm["bodies"][0]["bbox"]["min"]
                unwrap(
                    s.call(
                        "execute",
                        command="solid.move",
                        params={
                            "bodies": ["SpineCamera"],
                            "translate": [-v for v in xyz],
                        },
                        verbose=False,
                    )
                )
                unwrap(
                    s.call(
                        "execute",
                        command="file.export",
                        params={
                            "path": str(OUT / "SpineCamera_standard.stl"),
                            "bodies": ["SpineCamera"],
                            "quality": "fine",
                        },
                        verbose=False,
                    )
                )
                unwrap(s.call("undo"))
            unwrap(
                s.call(
                    "export",
                    path=str(OUT / f"assembly_{label}.step"),
                    bodies=[
                        "Rest",
                        "SpineCamera",
                        "Keeper",
                        "LockingKey",
                        "LaserBand",
                        "CameraPCB",
                        "CameraLens",
                        "CameraConnector",
                        "Ribbon",
                        "LaserModule",
                    ],
                )
            )
            unwrap(
                s.call(
                    "screenshot",
                    source="model",
                    view="iso",
                    width=1400,
                    height=1100,
                    grid=False,
                    axes=False,
                    path=str(ROOT / f"assembly_{label}.png"),
                )
            )
        # Preserve the assembly before temporary, reversible print-orientation edits.
        unwrap(s.call("save", path=str(ROOT / "mount.json"), format="json"))
        unwrap(s.call("save", path=str(ROOT / "mount.solidcraft")))
        for body in [
            "Rest",
            "SpineCamera",
            "Keeper",
            "LockingKey",
            "LaserBand",
            "FitCollar",
        ]:
            unwrap(s.call("export", path=str(OUT / f"{body}.step"), bodies=[body]))
            if body == "Rest":
                unwrap(
                    s.call(
                        "execute",
                        command="solid.move",
                        params={
                            "bodies": [body],
                            "axis": [1, 0, 0],
                            "angle": "-90 deg",
                        },
                        verbose=False,
                    )
                )
            if body == "LaserBand":
                unwrap(
                    s.call(
                        "execute",
                        command="solid.move",
                        params={"bodies": [body], "axis": [0, 1, 0], "angle": "25 deg"},
                        verbose=False,
                    )
                )
            mm = unwrap(
                s.call(
                    "execute",
                    command="inspect.measure",
                    params={"bodies": [body]},
                    verbose=False,
                )
            )
            xyz = mm["bodies"][0]["bbox"]["min"]
            unwrap(
                s.call(
                    "execute",
                    command="solid.move",
                    params={"bodies": [body], "translate": [-v for v in xyz]},
                    verbose=False,
                )
            )
            unwrap(
                s.call(
                    "execute",
                    command="file.export",
                    params={
                        "path": str(OUT / f"{body}.stl"),
                        "bodies": [body],
                        "quality": "fine",
                    },
                    verbose=False,
                )
            )
            unwrap(s.call("undo"))
            if body in ("Rest", "LaserBand"):
                unwrap(s.call("undo"))
        print("SAVED NATIVE SOLIDCRAFT DESIGN", flush=True)
    finally:
        s.close()


if __name__ == "__main__":
    build()
