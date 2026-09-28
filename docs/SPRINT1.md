# Sprint 1: Hardware Research and Feasibility

## Mission and User

For students exploring optical blood-flow sensing, mini-scos is a low-cost experiment to determine whether hardware we already own, plus a small laser, can produce useful speckle measurements.

The primary user is a student experimenter who wants to explore optical sensing with affordable hardware and reproducible methods. Evidence of infeasibility is also a useful result.

## Sprint Goal

Research feasibility and decide what to purchase. Purchasing and physical experiments come afterward. A complete device remains a stretch goal.

We have a Raspberry Pi 5, power supply, and IMX296 global-shutter camera. We will document the setup, including the lens and cables, as evidence of access. Speckle capture is not yet demonstrated.

## Work This Sprint

- Confirm existing hardware specifications and compatibility.
- Research camera, laser, and lens requirements using papers and manufacturer documentation.
- Compare purchase options by price, availability, compatibility, and uncertainty.
- Outline the geometry for a skin-contact jig; detailed CAD and printing come later.
- Recommend a parts list and first experiment using an inanimate target.

Elena is sprint lead. We will agree on research assignments and track them on the [GitHub board](https://github.com/users/ebf-hue/projects/3).

## Project User Stories

These are the project backlog, not promises to finish the hardware this sprint. Acceptance criteria are in each issue.

1. [Capture images with known settings (#1)](https://github.com/ebf-hue/mini-scos/issues/1)
2. [Inspect speckle contrast and mean intensity (#8)](https://github.com/ebf-hue/mini-scos/issues/8)
3. [Compare stationary and moving conditions (#9)](https://github.com/ebf-hue/mini-scos/issues/9)
4. [Create a repeatable mounting arrangement (#10)](https://github.com/ebf-hue/mini-scos/issues/10)
5. [Document methods and results for reproducibility (#11)](https://github.com/ebf-hue/mini-scos/issues/11)

## Assumptions and Evaluation

| Assumption | Research check |
|---|---|
| Our camera can capture useful speckle data. | Confirm raw output, exposure control, sensor characteristics, and lens compatibility. |
| An affordable laser is sufficient for an initial experiment. | Compare documented source characteristics with published speckle experiments; identify specifications that remain unknown. |
| A simple jig can support a usable optical geometry. | Check focus distance, mounting dimensions, illumination position, and likely motion artifacts. |

Our biggest uncertainty is whether this camera and an inexpensive laser can resolve repeatable speckle. Research will inform the choice; the first physical test will use a stationary scattering target and documented camera settings.

Later, we will compare moving-target contrast against stationary baseline variability, recording intensity and saturation. Motion sensitivity alone does not establish blood-flow measurement.

We change direction if necessary components are incompatible or exceed our agreed budget. If evidence is inconclusive, we will identify the cheapest test needed before buying more hardware.

## Tools and Supporting Work

- **GitHub and Markdown:** issues, shared documentation, and teammate-reviewed changes.
- **Manufacturer documentation and research papers:** evidence for component selection and experimental requirements.
- **Python:** proposed for later image analysis; libraries and camera software will be selected after compatibility checks.
- **CAD software:** to be selected for the printed jig after we establish the geometry.

The [related-work shortlist](related-work.md) contains ten papers with their contributions and open questions (#6). Supporting work also includes 2–3 relevant BU faculty and specific questions (#5), and a crossed review of this plan by two different AI models (#4). Findings and review links will be saved under `docs/`.

## Risks and Deliverable

Laser exposure could harm an experimenter; source selection and any skin testing require an exposure assessment and confirmation of applicable campus requirements.
Motion, contact pressure, or camera noise could be mistaken for a physiological signal.
The setup is experimental and must not be used for diagnosis or blood-pressure decisions.

At the sprint review, we will show our hardware comparison, recommended parts list, and first-experiment plan, including unresolved blockers.

Success is a justified purchase recommendation or a supported decision to revise the approach. This is a research-first deliverable; we need to confirm with course staff that it meets the initial sprint's working-demo expectation.
