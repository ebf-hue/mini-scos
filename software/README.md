# Contrast analysis

First software milestone: load a single-channel frame, select a rectangular region, calculate mean intensity and spatial contrast, and save CSV results and a plot. No camera is needed yet.

Raspberry Pi OS (64-bit) is the target for future Pi camera capture. This analysis tool also runs on a laptop with Python 3.10 or newer. It has not been tested on the physical Pi yet.

## Run the example

From this folder:

```sh
python3 -m venv .venv
. .venv/bin/activate
python -m pip install -r requirements.txt
python examples/generate.py
python analyze.py examples/generated/high.npy examples/generated/low.npy --output results/demo
```

On Raspberry Pi OS, install `python3-venv` with apt if creating the environment reports it is missing. Keep pip packages inside the virtual environment.

The example generates deterministic simulated coherent speckle fields. The low-contrast frame averages 16 independent realizations; both frames have mean intensity 1000 in arbitrary units. Expect high contrast near 1 and low contrast near 0.25. These are illustrative numerical inputs, not measured blood-flow data or a realistic camera/noise model.

Open `results/demo/measurements.png` and `results/demo/measurements.csv`. Each row records the input path, frame dimensions, ROI coordinates, mean, population standard deviation (`ddof=0`), and uncorrected contrast `K = std / mean`. Plot order follows argument order; it is not a time axis. Running again in the same output folder replaces those two result files. Input files are never changed.

## Analyze a frame

```sh
python analyze.py capture.npy --roi 20 30 100 80 --output results/trial01
```

ROI arguments are **x, y, width, height** in input-array pixels, with the origin at the top left. Omit them to use the entire frame. Out-of-bounds ROIs, fewer than two pixels, negative/nonfinite intensities and zero mean are rejected.

Supported inputs:

- Single-channel lossless PNG or TIFF, including 16-bit intensity images.
- Two-dimensional numeric `.npy` arrays containing unpacked sensor intensities. Packed RAW10 buffers and DNG files are not supported.

RGB, palette images, JPEG and multiframe stacks are rejected. Do not convert a processed color photo to greyscale and treat the result as calibrated sensor contrast. A lossless file can still contain processed or gamma-encoded pixels.

For the color IMX296 sensor, extract one consistent Bayer color-site grid before analysis; do not mix the whole Bayer mosaic or silently demosaic it. ROI coordinates then refer to that extracted grid. Camera capture, Bayer extraction, exposure/gain metadata and dark/noise correction are follow-up work.

This measures raw spatial intensity variation only. Exposure, sampling, illumination and sensor noise all affect contrast. It does not estimate blood flow or blood pressure. Preserve original captures separately and hold camera settings and geometry fixed when comparing real trials.

## Checks

```sh
python -m unittest discover -s tests -v
```

Checks use analytically known contrast values, a cropped ROI, high-bit-depth input, invalid frames, and an end-to-end CSV/plot run.
