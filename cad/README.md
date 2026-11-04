# CAD

Start with **[19 — Camera tray](19-camera-tray/README.md)**, the current IMX296 wrist-mounted design. It includes the recessed camera seat, two independent retaining clips, clearance for the headers and ribbon cable, and an open base for the optical paths.

The numbered folders follow the design sequence. **These are CAD iterations, not print counts**: the team has completed four physical print revisions. Earlier folders remain available for comparison and reuse.

## Design history

| Order | Design | Main change |
| --- | --- | --- |
| 01 | [Bench fixture](01-bench-fixture/README.md) | Adjustable camera, laser and filter positions for target experiments |
| 02 | [Arm-cuff concept](02-arm-cuff-concept/README.md) | Early one-sided arm saddle and component layout |
| 03 | [Camera Module 3 C-rest](03-c-rest-module3/README.md) | Wide rest with an adjustable Module 3 carrier |
| 04 | [Printable C-rest](04-c-rest-printable/README.md) | Printed joints and camera cassette |
| 05 | [Slim C-rest](05-slim-c-rest/README.md) | Slimmer rest and support study |
| 06 | [SolidCraft mount V1](06-solidcraft-mount-v1/README.md) | First SolidCraft mount, later revised after print feedback |
| 07 | [SolidCraft mount V2](07-solidcraft-mount-v2/README.md) | Revised laser support and front camera loading |
| 08 | [SolidCraft mount V3](08-solidcraft-mount-v3/README.md) | Rounded laser cradle |
| 09 | [SolidCraft mount V4](09-solidcraft-mount-v4/README.md) | Lofted cradle and broader attachment |
| 10 | [SolidCraft mount V5](10-solidcraft-mount-v5/README.md) | Intermediate junction and blending study |
| 11 | [SolidCraft mount V6](11-solidcraft-mount-v6/README.md) | Surface-blended laser attachment |
| 12 | [SolidCraft mount V7](12-solidcraft-mount-v7/README.md) | Camera attachment blends and thicker laser support |
| 13 | [Bench architecture study](13-bench-architecture/README.md) | Architecture reset before returning to a wrist mount |
| 14 | [Wrist architecture](14-wrist-architecture/README.md) | Wrist-mounted layout and component placement |
| 15 | [Mechanical tower](15-tower-mechanical/README.md) | Braced tower sized around the supplied IMX296 camera and lens |
| 16 | [Dovetail tower](16-tower-dovetail/README.md) | Sliding dovetails replace loose structural pins |
| 17 | [Open optical paths](17-tower-open-optics/README.md) | Open wrist base, header clearance and retention revisions |
| 18 | [Recessed clips](18-tower-recessed-clips/README.md) | Recessed camera seat and separate sliding clips |
| **19** | **[Camera tray — current](19-camera-tray/README.md)** | **Integrated tray with independent clips and checked insertion paths** |

Original V1–V7 names remain in the descriptions to connect the folders to earlier discussion. [revision-map.json](revision-map.json) maps every old folder name to its new location.

## Current design

- [Native SolidCraft assembly](19-camera-tray/camera-tray.solidcraft)
- [STEP assembly](19-camera-tray/camera-tray.step) for Fusion and other CAD tools
- [Assembly screenshot](19-camera-tray/assembly.png)
- [Camera insertion view](19-camera-tray/camera-drop-in.png)
- [Five-part replacement print plate](19-camera-tray/bambu/scos-five-replacements-a1-mini-red/scos-five-replacements-a1-mini-red.3mf)
- [Build and check instructions](19-camera-tray/README.md)

The latest replacement set contains the wrist base, laser bracket, camera plate and two clips. Reuse the frame and laser cap. It was sliced, but physical feedback on November 4 identified blocked lens knobs and focus access, plus holders too close to board components. Earlier insertion checks omitted the protruding controls. The latest plate is not a corrected print release.

## Files within each design

Layouts vary because the prototypes developed over time. Typically:

- `build.py` and other scripts generate or check the geometry.
- `.solidcraft` files open in SolidCraft. STEP files preserve solids but do not provide a native Fusion feature timeline.
- `parts/` or `exports/` contain individual components and portable assemblies.
- PNG files show assemblies, details or insertion studies.
- `bambu/` contains print preparation and 3MF plates where available.
- `sources/` contains reference geometry and source attributions.
- Check reports record the geometry that was tested. Historical reports and native model files retain their original names and recorded paths.

Units are millimetres. Read each design's README before rebuilding or printing.

## Experiments

[experiments/](experiments/README.md) holds surface-blending scratch work and Halloween accessories. They are outside the numbered SCOS design sequence.

## Verification limits

CAD clearance checks do not prove physical fit, latch strength, optical focus or blood-flow measurement. Header dimensions include estimates, and focus at the modeled camera-to-wrist distance remains unverified. The older [validation report](VALIDATION.md) covers the initial bench and arm concepts only; later designs have their own checks.
