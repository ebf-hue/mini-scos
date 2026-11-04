# Hardware and Filter Prototype

Shortlist originally checked October 5, 2026. The delivered IMX296 CS-mount camera matches the user-supplied STEP used in the current CAD. Earlier official Raspberry Pi camera specifications below describe the original purchase assumption and should not be treated as confirmed specifications for this module. The camera, lens and laser have since arrived. Prices are historical shortlist figures.

## First purchase

| Part | Listed price, USD | Reason and limitation |
|---|---:|---|
| [Adafruit 1054: 650 nm, 5 mW laser module](https://www.adafruit.com/product/1054) | $5.95, in stock | Integrated driver; 2.8–5.2 V input, 25 mA maximum. Cheap visible-light source for an enclosed inanimate-target experiment. Spectral linewidth/coherence length is unspecified, so suitability for diffuse SCOS remains unverified. |
| [PiShop 782-1: 16 mm C-mount telephoto lens](https://www.pishop.us/product/16mm-telephoto-lens-for-raspberry-pi-hq-camera-cs/) | $62.50, in stock | Compatible using the camera's C-to-CS adapter; manual focus and F1.4–16 aperture. Minimum object distance is 0.20 m. Narrower field of view than the 6 mm option at the same distance. This is a bench-test lens, not a confirmed solution for a compact skin-contact jig. |
| Optional [Rosco #27 Medium Red sheet, 20 × 24 inches](https://www.bhphotovideo.com/c/product/43960-REG/Rosco_RS2711_27_Filter_Medium.html) | $11.50, in stock | Cut small samples for a removable camera-side filter holder. Broad red transmission, not a narrow 650 nm bandpass or a protective laser filter. |

Laser plus lens: **$68.45**. With the gel: **$79.95**, before shipping, tax, power accessories, and mounting materials. Prices and stock can change.

The [official camera specification](https://www.raspberrypi.com/products/raspberry-pi-global-shutter-camera/) confirms RAW10 output, a color sensor, 3.45 micrometre pixels, and an integrated IR-cut filter. Start with visible red illumination while retaining that filter. Near-infrared work would require a separate compatibility decision.

Fit the 16 mm C-mount lens with the camera's included C-to-CS spacer. Despite the product page title ending in "CS," its specifications identify a C-mount lens. Start at a target distance of at least 20 cm and verify focus on the actual assembly. Use a small illuminated region of interest. Sweep the F1.4–16 iris to determine whether the speckle is adequately sampled; mount compatibility alone does not establish useful measurements. Close-focus extensions or another lens may be needed for a later compact geometry.

Power the laser module from a suitable regulated supply through a manual switch. Do not drive its power from a GPIO signal pin. The supplier labels it Class IIIa: use a contained beam path and an inanimate target, prevent eye exposure and specular reflections, and assess exposure and campus requirements before any skin test. A printed enclosure or red gel is not certified laser protection.

## Filter prototype

1. **Establish the unfiltered baseline.** Hold the camera and target fixed, enclose the viewing region with a light-blocking hood, and record laser-off and laser-on captures. Check the actual hood for light leakage.
2. **Add a removable red-gel insert.** Place a flat, tensioned sample in front of the camera lens. Use a separate cartridge so nothing presses on the lens. Keep wrinkles, adhesive, and printed edges outside the viewing aperture. Include an empty cartridge as a control.
3. **Compare under room lighting.** With exposure, gain, iris, target, and geometry fixed, collect five repeats each for hood only, hood plus empty cartridge, and hood plus gel. Record laser-off and laser-on data for each condition.
4. **Measure the tradeoff.** Compare laser-off background, laser-on minus laser-off mean intensity as a simple signal proxy, saturation fraction, and repeatability of contrast. Also test whether inserting the gel changes contrast under enclosed conditions. Do not assume a prettier image indicates a better measurement.
5. **Buy a narrowband filter only if justified.** If room light remains limiting after the hood, investigate a documented 650 nm bandpass whose bandwidth covers the actual source wavelength/tolerance. For context, [Edmund #65-170, 25 mm, 650 nm/10 nm bandpass](https://www.edmundoptics.com/p/650nm-cwl-25mm-dia-hard-coated-od-4-10nm-bandpass-filter/19819/) is listed at $278. Its bandwidth is not automatically appropriate for the unspecified low-cost source. Include clear aperture, incidence angle, blocking, and signal loss in the decision.

[Rosco's filter guide](https://jp.rosco.com/sites/default/files/content/resource/2022-10/Rosco_Guide_to_Color_Filters_22.pdf) explains that R27 passes red and absorbs blue/green. It will also pass some unwanted red illumination. The gel experiment tests whether cheap broad filtering is useful; it does not reproduce a laboratory bandpass filter.

## Capture and analysis

Use raw sensor data and fixed exposure/gain for comparisons. The official camera is color: treat the Bayer mosaic explicitly, such as analyzing a consistent red-site grid with its larger sampling pitch. Assess speckle sampling on that grid. Demosaicing, denoising, sharpening, or smoothing can change the variance being measured.

Start with spatial contrast K = standard deviation / mean in a documented ROI and record mean intensity alongside it. Preserve dark frames and original captures; low light and sensor noise can bias contrast. Software filtering cannot remove in-band ambient photons or their shot noise. The [camera-selection SCOS paper](https://pmc.ncbi.nlm.nih.gov/articles/PMC11126420/) provides the next reference for sensor characterization and noise corrections.

An observed response to moving paper would establish motion-sensitive speckle, not validated blood flow. Failure with this source also would not rule out SCOS: first investigate coherence, sampling, exposure, focus, ambient light, and noise.

## Jig direction

First prototype: rigid camera support, adjustable laser clamp sized around its 10 mm diameter, target holder at 20 cm or farther, light-blocking hood, and interchangeable filter cartridges. The selected lens is listed as 39 × 50 mm and 133.7 g; allow clearance and support its weight. Confirm the delivered lens's front dimensions before making a snap-fit holder. Do not lock in a skin-contact geometry until the focus and speckle tests pass.

## Delivered lens and mount feedback — November 4

The delivered 16 mm lens has protruding manual adjustment knobs omitted from the cylindrical CAD envelope. They obstruct lens-attached insertion and focus adjustment in the current frame. The board retainers also need relief above surface-mount components. The requested next revision uses a 5 × 5 mm radial insertion notch, holders contacting verified bare PCB areas, and an adjustable support with open access to the lens controls. Dimensions and physical fit remain to be checked.
