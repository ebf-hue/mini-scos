# CAD concepts

CAD prototypes for exploring mini-scos hardware. Units are millimetres.

The current wrist-mount prototype is below. Its camera insertion and assembly geometry have been checked and its three parts have been sliced for the A1 mini; physical fit and optical performance remain unverified.

| Design | Use | Open in Fusion |
|---|---|---|
| [Wrist-mounted Camera Module 3 prototype](wrist-architecture/README.md) | One-sided wrist saddle, slide-in camera, lofted laser cradle, and printed keepers | [Assembly STEP](wrist-architecture/wrist-inward.step) / [SolidCraft](wrist-architecture/wrist-inward.solidcraft) / [black PLA plate](wrist-architecture/print/wrist-mount-black-pla.3mf) |
| [Bench fixture](bench-fixture/README.md) | First inanimate-target experiments with adjustable camera, laser and filter positions | [Assembly STEP](bench-fixture/exports/bench_fixture.step) |
| [Open arm saddle](arm-cuff-concept/README.md) | One-sided mounting concept shown in the presentation | [Assembly STEP](arm-cuff-concept/exports/v04/open_arm_saddle.step) |

![Bench fixture](bench-fixture/preview.png)

![Open arm saddle concept](arm-cuff-concept/open_saddle_assembled_v04.png)

STEP files preserve solids and component names, but not a native Fusion feature timeline. Generators and rebuild instructions are included in each folder. Open the assembly first; individual parts are provided separately.

The bench fixture is the starting point. The compact arm concept has an unresolved close-focus spacer, and its camera is an HQ-camera visual proxy rather than exact IMX296 geometry. Both assume the selected 16 mm lens; the existing hardware shortlist still describes the earlier 6 mm option.

Geometric checks do not establish printability, measured fit, optical focus, laser containment or blood-flow sensing. No measured optical performance is claimed. These designs contribute to [mounting issue #10](https://github.com/ebf-hue/mini-scos/issues/10); repeated-placement measurements remain outstanding.
