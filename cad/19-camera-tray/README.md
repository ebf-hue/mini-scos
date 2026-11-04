# Integrated camera tray with two independent clips

**Physical feedback, November 4:** the 39 mm lens envelope omitted the protruding focus/aperture knobs. The attached lens does not pass through the opening with those controls installed, and the frame obstructs adjustment. The upper retainers also pass too close to board components. The existing geometric insertion checks do not cover this delivered lens or establish component clearance. Preserve this revision as the tested baseline; revise the carrier, holders and height support before another print.

The carrier starts as a single 92 × 70 × 10 mm tray blank, with R5 outside corners and an R1 upper perimeter. Stepped seat recesses, clip-track channels, header wells, a cable route, underside frame interfaces and an internal latch relief are cut into that carrier. The recessed guide ribs are integral to the same solid. This replaces the arch and the earlier wall-and-stop additions with a coherent tray. The wrist base, frame, camera elevation, lens position, and laser aim remain the same as the optical-window revision.

The PCB drops into a 39.6 × 39.6 mm locating pocket, with 0.30 mm nominal clearance at each edge of its 39 mm envelope. Its support plane remains at Z = 162.5 mm. Pocket rims rise 2.1 mm above that plane, placing the 1.6 mm board 0.5 mm below the rims. The central lens opening and relieved underside clear the modeled lens and camera components; only clear perimeter/corner areas support the board.

The remaining front and rear pocket shoulders control Y. The front shoulder is split around a 25 mm ribbon opening; its clip-lip lanes are relieved to PCB upper-face elevation so the clips pass over it. A 1.5 mm deep cable relief continues out through the front edge. The rear stop sits between the header areas. Side walls control X. Two 2 mm overlapping clip lands prevent upward Z motion, with 0.25 mm clearance above the PCB. The support plate prevents downward Z motion.

Each clip is made from a closed, rounded plan profile with an integral hooked section. A rounded-ended slot frees its release tongue, which has a 0.8 mm fillet at its thickness transition and chamfered upper edges. Each clip has its own dovetail and release tab. Guide centers are at X = ±27.5 mm, leaving at least 1.7 mm of material between the rim-clearance channel and the dovetail cavity. Remove both clips, lower the camera vertically with its lens attached, then slide the clips in from the ribbon side. Leave the loose ribbon end free and guide it through the central opening. No arch connects the clips. The latch geometry requires a physical fit/deflection test.

## Geometry evidence and limits

The original user-supplied camera STEP is preserved. Both rear headers are explicitly modeled, but their locations, pitch orientation and dimensions are estimates from the photo and typical 2.54 mm headers. Independent 10 × 10 × 11 mm checking envelopes give extra clearance. Measure the physical headers before treating the model as confirmed camera fit. Mating plugs and flexible ribbon bend radius are not established.

The lens visual reconstruction and its 39 mm cylindrical envelope are checked during insertion; this is not supplier optical CAD. Free-space paths are checked, but optical focus and strength remain unvalidated.

- `build.py`: seven valid connected printed solids, static collisions, 21 drop-in samples, 66 samples per sliding joint (either clip inserted while the other is installed), optical obstruction checks, and native SolidCraft/STEP export.
- `check_loading.py`: continuous conservative vertical sweeps for supplied camera solids, PCB, both enlarged header regions, attached lens and adapter; header clearance during sliding; front ribbon corridor; containment of the reconstructed lens in its checking envelope.
- `check_pcb_restraint.py`: expected free play followed by geometric restraint in positive/negative X, Y and Z, using the documented PCB envelope. No rotational or force validation.

Build with `uv run --python 3.12 --with cadquery python cad/19-camera-tray/build.py`, then run both checking scripts with the same environment. No slicing or print submission is included.

Replacement camera parts: CameraPlate, CameraClipLeft and CameraClipRight. The former CameraRetainer is omitted from this assembly.
