# Wrist-Mounted Architecture Concept

This is the wrist-mounted direction requested after the bench concept was rejected. It is an architecture model, not a print release.

- Open curved saddle over the top of the wrist, with strap slots.
- Official Raspberry Pi Camera Module 3 Standard reference geometry, integrated lens attached. The camera slides in from the open front with the keeper removed.
- Broad laser support lofted through rotating sections from the curved saddle into the underside of the inclined cradle, with a separate cap. The laser points inward across the wrist toward the skin observed by the camera. Its nominal illumination point is 10 mm from the camera viewing centre.
- Current SolidCraft assembly: `wrist-inward.solidcraft`. Portable assembly: `wrist-inward.step`. `wrist-concept.*` preserves the earlier orientation.
- The supplier laser STEP is included with its emitting aperture at original Z=0 and rear wires at +Z. The supplied model has a 32.8 mm barrel; the product's nominal 31 mm dimension still requires a physical fit check.
- The keeper and cap have short tapered printed pegs with mating sockets. Their physical grip and ease of removal require the first fit-test print.

The display retains the official PCB, lens assembly, connector, and major details. Tiny components are omitted from the display only. The camera source is Raspberry Pi's [official STEP archive](https://datasheets.raspberrypi.com/camera/camera-module-3-step.zip).

`model-check.json` records valid single solids, zero nominal wrist/laser/cap/keeper interference, zero beam obstruction by the holder, and zero intersections for conservative component bounding boxes swept continuously along a 35 mm insertion path. The insertion check uses all 590 solids in the original official Standard model against the saddle, inward-facing laser, and laser cap, with the camera keeper removed. It does not establish printed tolerances, retention strength, ribbon installation ergonomics, laser-cap assembly motion, or compatibility with the Wide model.

`wrist-inward-closeup.png` shows the assembly. `wrist-inward-ray.png` makes the saddle transparent to expose the red illumination beam and blue camera axis. Both lines are explanatory references, not additional physical parts.

The compact model places the lens approximately 20 mm above the skin reference. Useful speckle measurement at this distance is **unverified**. Raspberry Pi lists conventional near focus at approximately 100 mm for Standard and 50 mm for Wide; that specification alone does not validate a close-range SCOS configuration. Optical performance must be tested before fixing this geometry for manufacture.

The curved construction was generated using Open CASCADE and imported, saved, and rendered through the SolidCraft MCP. The native construction attempt is retained separately; it timed out on curved boolean operations.

## Fit-Test Print

**Use the revised laser-loft plate:** `bambu/laser-loft-check/wrist-inward-fit-test/wrist-inward-fit-test.3mf`. The original plate below predates the blend. The revised plate slices successfully with three closed connected meshes, all inside the A1 mini build area; estimated 1 h 46 min and 32.84 g including supports. Physical print and fit remain unverified.

The single-plate project is `bambu/wrist-inward-fit-test/wrist-inward-fit-test.3mf`. It contains only the saddle, laser cap, and camera keeper, with their mating pegs. Hardware, arm, beam, and camera reference geometry are excluded.

Prepared for Bambu A1 mini, 0.4 mm nozzle, Generic PLA, textured PEI, 0.20 mm layers, four walls, 30% infill, and build-plate-only tree supports. The saddle rests on its flat end; the cap rests on an annular end; the keeper rests on its broad face. `prep_print.py` records the orientations, bed-contact areas, and closed connected mesh checks in `bambu/mesh-and-orientation-check.json`.

Remove the tree supports before trying the camera channel or laser cradle. Slide the complete camera in with its lens attached and the keeper removed, then fit the keeper pegs. Seat the laser with its aperture pointing inward/downward, then fit the cap pegs. Test fit gently; do not force the PCB, autofocus housing, or small pegs. This first print checks physical fit and retention. Optical performance remains unverified. No printer job has been sent.
