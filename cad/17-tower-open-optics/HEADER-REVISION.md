# Camera header clearance revision

The original user-supplied STEP is preserved unchanged in `sources/imx296-with-cs.step`. The added reference, `sources/imx296-with-headers-estimated.step`, includes both rear headers in the original camera coordinate system. The assembly also exposes separate trigger/strobe housing and pin components.

The supplied photo matches the INNOMAKER IMX296 family. It establishes the presence of trigger J3 and strobe J2, but does not establish measured dimensions or mono/color variant. Header labels by corner, pin orientation, and coordinates are illustrative until checked on the physical board.

## Assumptions and clearance

- Estimated header centers in original camera coordinates: X = -14 / +14, Y = +14 mm; ribbon connector is on the opposite (-Y) edge.
- Typical 2.54 mm pitch, 2.54 × 5.08 × 2.54 mm housings; 0.64 mm square pins extending 6 mm beyond the housings.
- Each independent checking envelope is 10 × 10 mm, extending 11 mm behind the board. These deliberately exceed the illustrated headers. Bare pins only; mating plugs/wires are not modeled.
- Retainer opens around the two header corners. Its rear bridge is above the checking envelopes; low side lands hold the PCB with the existing clearance.
- Retainer slides from the ribbon-connector side (-Y). Its guide grooves are through slots, and its latch ramp is reversed to suit that entry direction. Route the ribbon through the central notch, with its loose end free during insertion. Flexible cable bends are not validated.

## Validation

`build.py` checks each printed part is one valid solid, static intersections, 11 camera insertion positions, and 66 positions per sliding joint. `check_headers.py` additionally checks continuous rectangular sweeps for header clearance during retainer sliding and camera top loading, and compares the former retainer with the augmented camera. `check_camera_surfaces.py` checks the original open-shell STEP against the camera plate. Optical free-space checks remain in `check_optical_paths.py`.

The geometric results are conditional on the estimated header locations and sizes. They do not establish measured physical fit, latch durability, optical focus or safety. Check the real headers against the enlarged envelopes before printing. No slicing or printer submission is part of this revision.

Only CameraRetainer changes in this header revision. The earlier optical-opening revision separately changed WristBase and LaserBracket.

## L-shaped side returns

The removable retainer now has two 1.8 mm thick vertical returns alongside the PCB, joining the existing upper lips at 90 degrees. The inside faces are at X = ±19.8 mm, leaving 0.30 mm against the 39 mm board envelope. They extend down to Z = 162.7 mm, 0.20 mm above the plate, and cover Y = -16 to +8 mm. The rear header keepouts begin at Y = +9 mm. Their length runs along the slide direction, so no end wall has to pass through the PCB during insertion. The frame and lower plate are unchanged.

## Fore/aft PCB stops

A fixed rear stop on CameraPlate now has its inner face at Y = +19.8 mm, centered across X = -8 to +8 mm between the header zones. Two front returns on CameraRetainer have their inner faces at Y = -19.8 mm, leaving a 25 mm opening around the ribbon connector. This gives 0.30 mm clearance at each board end. The front returns trail the sliding retainer and approach the board from outside; they do not pass through the board on insertion.

`check_pcb_restraint.py` translates the PCB envelope in all six directions to confirm geometric stops and the specified free play. This is a geometric check, not a strength test or a physical fit claim. Both CameraPlate and CameraRetainer now change, in addition to the earlier WristBase/LaserBracket optical revision.
