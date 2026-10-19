# Bench fixture v0.1

First CAD layout for the official Raspberry Pi IMX296 Global Shutter Camera, selected 16 mm C-mount lens, and Adafruit 1054 laser. Units are millimetres. This is an unprinted prototype; actual fit, focus, and light exclusion still need testing.

## Open in Fusion 360

Upload `exports/bench_fixture.step` through Fusion's Data Panel, then open the translated design. `bench_fixture_with_hood.step` adds the optional camera hood. Each individual part also has a STEP file for editing and an STL for slicing. The assembly contains printed parts only: electronics, lens, bolts, target material, and filter film are omitted.

STEP preserves solid geometry and assembly names, but does not transfer a native Fusion feature timeline or constrain moving components. Use direct editing or add Fusion features/joints after import. The editable parametric source is `build.py` with dimensions in `parameters.json`. No native `.f3d` file has been generated or Fusion-import test performed.

[Autodesk STEP import guidance](https://www.autodesk.com/products/fusion-360/blog/import-step-file-into-fusion-360/) · [Design-history limitations](https://help.autodesk.com/view/fusion360/ENU/?caas=caas/sfdcarticles/sfdcarticles/Imported-files-do-not-contain-timeline-features-in-Fusion-360.html)

## What is modeled

| Part | Print quantity | Purpose |
|---|---:|---|
| rail_segment | 2 | 180 mm sections joined into a 360 mm rail; parallel 6 mm slots, raised feet for nut access |
| rail_join_plate | 2 | Bridge the rail joint at its edges using four M4 bolts total |
| camera_bracket | 1 | Rear camera mounting plate, nominal 30 × 30 mm corner-hole pattern, 32 mm centre opening and side braces |
| camera_spacer | 4 | Nominal 5 mm standoffs between printed plate and camera; clearance must be measured |
| laser_carrier | 1 | Slides on rail; off-centre captive M4 nut pocket for yaw pivot |
| laser_yaw_clevis | 1 | Rotates around vertical M4 pivot and supports horizontal M4 tilt axle |
| laser_clamp_lower / upper | 1 each | Split 10.4 mm bore for nominal 10 mm laser; four M3 clamp bolts; lower part has tilt lug |
| filter_holder | 1 | Slides on rail; top-loading 4.6 mm cassette channel |
| filter_frame | 2 | Two 2 mm frames sandwich red gel; 48 mm clear opening and four small retention holes |
| target_holder | 1 | Backing, lower ledge, and tape/strap slots for scattering target |
| camera_hood | optional 1 | Three-sided camera/lens shade with rail-fastening feet; open ends and bottom |
| laser_fit_coupon | first 1 | Check the 10.4 mm laser bore on the actual printer/module |
| camera_hole_coupon | first 1 | Check camera mounting-hole alignment before printing the bracket |

Largest rail footprint including feet is 180 × 132 mm. Other parts fit within that footprint. Reserve printer margins and check orientations in the slicer.

## Geometry and adjustment

- Default rail length: 360 mm; rail top at Z = 8 mm and feet bottom at Z = -8 mm in the assembly.
- Planned optical axis: Z = 75 mm. Camera mount at X = 28; filter at X = 126; laser at X = 235, Y = 22; target at X = 330.
- A **planning allowance**, not a measured lens position, puts the lens front 70 mm ahead of the camera bracket: nominal front-to-target spacing about 230 mm. Measure the installed lens and adjust the sliding target to retain at least the supplier's 200 mm minimum focusing distance.
- The laser is offset from the viewing axis. Aim it toward the target by rotating the yaw mount and adjusting tilt. The exported assembly is at zero yaw/tilt; it is not already optically aligned. Test angular clearance before tightening; no calibrated angles or hard stops are provided.
- Sliding parts use paired M5 bolts/washer/nut sets through the rail slots. Position cannot be reconstructed from a number yet: mark locations or measure and record them before repeats.
- Hood mounting feet sit ahead of the camera carrier. The hood shades the camera; it is **not a full target enclosure or certified laser containment**. Add an opaque cover around the target region and test leakage separately.

## Confirm before a full print

The [official camera drawing](https://datasheets.raspberrypi.com/gs-camera/gs-camera-mechanical-drawing.pdf) shows the 30 mm corner pattern and 2.5 mm camera holes. The bracket uses 2.8 mm printed clearances. Test the coupon against the actual module and confirm which holes are accessible without damaging the board or cover. Nominal M2 through-bolts are a starting option where accessible; select actual screw lengths from the measured stack and leave cable clearance. Do not force hardware into the camera.

The 5 mm standoff, mounting orientation, lens-front allowance, and planned optical height need confirmation on the actual assembly. The [lens](https://www.pishop.us/product/16mm-telephoto-lens-for-raspberry-pi-hq-camera-cs/) is listed as 39 × 50 mm and 133.7 g. The CAD does not grip its focusing rings or provide a lens-specific weight support. Assess bracket flex before use; add an adjustable support under a non-moving lens barrel surface if necessary.

The [laser module](https://www.adafruit.com/product/1054) is listed as 10 mm diameter × 31 mm length. Start with the fit coupon, then confirm that the clamp clears wires and optical adjustments. The current clamp occupies 32 mm axially, so module ends may be slightly recessed; verify it does not block the emitted beam. Do not overtighten a printed clamp around the laser housing.

Film fits between the two frames. Use four small screws/bolts or tape outside the clear aperture after a fit check. The 4.6 mm holder slot assumes a 4 mm frame pair plus thin film. Print a short slot sample or test the frames first; film thickness and printer tolerance may require adjustment.

## Hardware to gather

- Eight M5 rail-carrier bolts with washers and nuts, plus two for the optional hood. Rail+carrier stack is 14 mm; select lengths to engage the nuts while clearing the table.
- Four M4 join bolts with washers/nuts (12 mm plate+rail stack).
- One M4 yaw bolt, washer, and nut; nut must fit the 8.4 mm corner-to-corner hex pocket. Insert nut before attaching carrier to rail.
- One M4 tilt bolt with washers/nut; clevis outer width is 24 mm.
- Four M3 clamp bolts with washers/nuts (20 mm clamp stack).
- Camera fasteners and four cassette-frame fasteners selected after actual fit checks.
- Matte scattering target, red gel if used, opaque covering material, and a separate switched laser power supply.

Threads are not printed into these parts. Hole diameters and nominal clearances are in the source. Printer calibration determines final fits.

## Printing and validation

Print the two coupons first. For the full parts, orient tall brackets on a side where appropriate and inspect support needs. The provided STL files sit on Z = 0 but are **not guaranteed to be in optimal print orientation**. The hood is usually best upside down so its top panel is on the bed. Round bores, clamp halves, and camera spacers need slicer review; do not print the assembled STEP as one object.

`exports/validation.json` records solid validity, volume, bounding boxes, STEP re-import checks, and a pairwise interference check for the default assembly including the hood. These checks establish geometric integrity, not successful printing, mechanical strength, screw accessibility, camera fit, laser containment, or optical performance. After assembling, verify focus and camera settings, then repeat a stationary-target trial before making performance claims.

## Rebuild

Use Python 3.12 and an isolated environment outside the repository:

```sh
uv venv --python 3.12 /tmp/mini-scos-cad-env
uv pip install --python /tmp/mini-scos-cad-env/bin/python -r requirements.txt
/tmp/mini-scos-cad-env/bin/python build.py
```

Run from this folder. Change `parameters.json`, rebuild, and inspect the updated files. The model generator includes geometric checks and a preview from the actual exported CAD geometry.
