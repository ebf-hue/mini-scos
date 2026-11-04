# Open optical window revision

Revision of the dovetail wrist tower. Not sliced or released for printing.

The base has a true 40 × 44 mm through-window with R4 corners. The two side tracks, end bridges and strap anchors remain around the exposed wrist patch. The laser module and its cradle move 6 mm outward and 6 mm upward along the existing 45-degree axis, keeping the same aim point at the camera axis. Its supporting gussets extend to the revised cradle. The front of the bracket foot is relieved against the camera and laser clearance volumes.

## Optical checks

`optical-path-check.json` tests the entire continuous free-space volume from the reconstructed front glass disk (radius 14.8 mm, Z=98.574 mm) to a 16 mm diameter wrist patch, with an extra 1 mm radial clearance against the mount. The volume extends below the curved skin surface. It also tests a 4 mm diameter laser corridor from the actual CAD laser front-face center to the wrist, extended 6 mm past the center target to cover the curved skin surface.

81 camera rays (nine points across the lens disk to nine points across the wrist patch) plus the laser centerline are traced against the assembly solids. Their first positive intersection must be the wrist, at the expected endpoint. These ray samples supplement the continuous volume checks; they are not a lens ray-tracing simulation.

The IMX296 camera is the user-confirmed STEP. The lens geometry is a dimensioned visualization, not an optical prescription. The roughly 32 mm rim-to-skin distance still conflicts with the lens's listed 0.20 m minimum object distance: unobstructed sightlines do not prove useful focus or SCOS performance.

## Files

- `tower-open-optics.solidcraft` and `.step`: full revised assembly.
- `assembly.png`: full assembly view.
- `open-base.png`: upper camera support hidden to reveal the window.
- `parts/`: separate components; hardware references are not printable parts.
- `mechanical-check.json`: validity, nominal intersections and sampled insertion paths.
- `optical-path-check.json`: obstruction volumes and first-hit ray results.
- `build.py`, `check_optical_paths.py`, `mcp_client.py`: self-contained rebuild and validation.

From the repository root, run `uv run --python 3.12 --with cadquery python cad/17-tower-open-optics/build.py`. Requires SolidCraft CLI installed at its usual macOS path or set with `SOLIDCRAFT_CLI`. No slicing or printer commands are included.

For the inspection view, run `uv run --python 3.12 --with cadquery python cad/17-tower-open-optics/show_optical_paths.py`. In `optical-paths.png`, the upper support and lens barrel are hidden; the front rim/glass stay in their installed position. Green is the camera clearance volume and boundary rays; red is the laser centerline. These colored guides are not printable components.
