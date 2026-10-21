# Contrast analysis

First software milestone: load a single-channel frame, select a rectangular region, calculate mean intensity and spatial contrast, and save CSV results and a plot. No camera is needed yet.

Raspberry Pi OS (64-bit) is the target for future Pi camera capture. This analysis tool also runs on a laptop with Python 3.10–3.13. The default development runtime is Python 3.12. It has not been tested on the physical Pi yet.

## Launch with uv

From `software/`, with [uv installed](https://docs.astral.sh/uv/getting-started/installation/):

```sh
uv run --managed-python ui.py
```

uv downloads its own Python 3.12 if needed, creates `.venv`, and installs the dependencies from `uv.lock`. No environment activation is needed. `--managed-python` avoids accidentally selecting Apple's, Homebrew's or Conda's Python/Tk runtime. `pyproject.toml` is the dependency source of truth; `requirements.txt` is retained for the pip workflow below.

On Raspberry Pi OS, use the OS Python and its Tk package instead:

```sh
sudo apt install python3-tk
uv run --python /usr/bin/python3 ui.py
```

This deliberately overrides the development Python pin so the interpreter uses the OS-provided Tk installation. A desktop/display session is required; physical Pi validation is still pending.

### macOS runtime aborts

An error such as `macOS 15 (1507) or later required, have instead 15 (1506)` is a native runtime abort, not a minimum macOS version declared by this app. A bare `python3 ui.py` can select a different Python/Tk installation than expected. Try the managed uv command above rather than assuming an OS upgrade is needed. Do not set a fake macOS version or disable runtime checks.

To identify the interpreter and Tk version without launching the window:

```sh
uv run --managed-python python -c 'import sys, tkinter; print(sys.executable); print(sys.version); print("Tk", tkinter.TkVersion)'
```

## Run the example

From this folder:

With uv:

```sh
uv run --managed-python examples/generate.py
uv run --managed-python analyze.py examples/generated/high.npy examples/generated/low.npy --output results/demo
```

Or with a known working Python/Tk installation and pip:

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

### Desktop window

With the environment activated, run `python ui.py`. The workspace opens with four bundled demo images. Choose one in the image list, then drag a rectangle on the preview or enter pixel coordinates and press **Apply**. Contrast, mean and standard deviation update immediately. **Full frame** resets the region. Each image retains its own region, shown in the comparison table.

**Open images** adds your own single-channel PNG/TIFF or NumPy frames. **Preview brightness** changes only the displayed image, not measurements; it can clip bright spots on screen. **Export results** saves all loaded images' current measurements and ROI coordinates as `measurements.csv`, plus the comparison plot `measurements.png`. Existing files with those names in the chosen folder are replaced. Preview selections and brightness changes never alter source files.

The UI uses Python's Tkinter. On Raspberry Pi OS, install `python3-tk` using apt if needed. A desktop/display session is required; the CLI remains available for a headless Pi. The UI does not control the camera yet.

### Bundled demo images

The four [16-bit PNG images](examples/images/README.md) are included in the repository; no downloads or generation step is needed to try the UI. They are simulated inputs with mean intensity approximately 1000. High, medium and low contrast illustrate averaging 1, 4 and 16 independent realizations. The uniform reference has zero contrast. These are not prototype captures or physiological measurements.

### Command line

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

With uv:

```sh
uv run --managed-python python -m unittest discover -s tests -v
```

Or in an activated environment:

```sh
python -m unittest discover -s tests -v
```

Checks use analytically known contrast values, a cropped ROI, high-bit-depth input, invalid frames, and an end-to-end CSV/plot run.
