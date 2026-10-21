# Contrast analysis

First software milestone: load a single-channel frame, select a rectangular region, calculate mean intensity and spatial contrast, and save CSV results and a plot. No camera is needed yet.

Raspberry Pi OS (64-bit) is the target for future Pi camera capture. This analysis tool also runs on a laptop with Python 3.10–3.13. The default development runtime is Python 3.12. It has not been tested on the physical Pi yet.

## Fresh clone setup

You need Git, uv, an internet connection for the first setup, and a desktop session to use the window. No camera, laser, API key or account configuration is needed for the demos.

### Install the tools

Install [Git](https://git-scm.com/downloads) if `git --version` is not recognized. uv is a free tool that installs the right Python version and this project's dependencies for you. Choose a uv installation method from its [official installation guide](https://docs.astral.sh/uv/getting-started/installation/):

- **macOS with Homebrew:** `brew install uv`.
- **Windows PowerShell:** `winget install --id=astral-sh.uv -e`.
- **Linux / Raspberry Pi OS:** the official installer is `curl -LsSf https://astral.sh/uv/install.sh | sh`.

After installing, reopen the terminal if needed and check `uv --version`. macOS users without Homebrew can use uv's official standalone installer too.

The commands below need a recent version of uv. If uv says it doesn't recognize `--managed-python`, update it with `uv self update` (or `brew upgrade uv` if you installed it with Homebrew).

### macOS, Windows and Linux desktop

In Terminal on macOS or Linux, or PowerShell on Windows:

```sh
git clone https://github.com/ebf-hue/mini-scos.git
cd mini-scos/software
uv run --locked --managed-python ui.py
```

If you already cloned the repo, open a terminal in its `software` folder and run only the last command. To get later updates from the repository, return to your checkout and use your normal Git update workflow; do not clone a second copy over existing work.

uv downloads its own Python 3.12 if needed, creates `.venv`, and installs dependencies from `uv.lock`. No environment activation is needed. `--managed-python` makes uv use its own Python instead of one already on your computer (Apple's, Homebrew's or Conda's), which can come with a broken or incompatible Tk window library. `--locked` makes everyone use the exact dependency versions recorded in `uv.lock`, without updating them.

Expected result: the **mini-scos — Image workspace** window opens with High contrast, Medium contrast, Low contrast and Uniform reference in its image list. The demo images ship with the repo; there is no download button or generation step.

### Raspberry Pi OS desktop

Use 64-bit Raspberry Pi OS with a desktop session. Install Git and the OS Python/Tk packages, then install uv as described above:

```sh
sudo apt update
sudo apt install git python3 python3-tk python3-venv
git clone https://github.com/ebf-hue/mini-scos.git
cd mini-scos/software
uv run --locked --python /usr/bin/python3 ui.py
```

This deliberately uses the Pi's own Python instead of uv's, because the Pi's Python comes with a Tk window library built for the Pi. A desktop/display session is required; physical Pi validation is still pending.

The app supports Python 3.10–3.13. Check the Pi's version with `python3 --version`. If it is 3.14 or newer, uv will refuse to run until the version limit in `pyproject.toml` (`requires-python`) is raised and the app is retested.

All remaining examples assume your terminal is in `software/`. On the Pi, replace `--managed-python` with `--python /usr/bin/python3` in uv commands below.

### Try it in a minute

1. Select **High contrast**, then **Low contrast**. Both have mean intensity about 1000; K is about 1.036 and 0.257 respectively.
2. Drag a rectangle on the image, or enter X, Y, Width and Height and click **Apply**. Measurements and the outlined region update together.
3. Select **Uniform reference**: K should be zero for any valid region. **Full frame** resets the selected image's region.
4. Move **Preview brightness**: the display changes, but the measured values stay the same.
5. Click **Export results**, choose a folder, and look for `measurements.csv` and `measurements.png`. All loaded images are exported with their individual region coordinates. Those two filenames are replaced if they already exist in the chosen folder.

To reopen the app later, return to `software/` and run the same uv launch command. Close the window to quit.

### macOS runtime aborts

An error such as `macOS 15 (1507) or later required, have instead 15 (1506)` is a native runtime abort, not a minimum macOS version declared by this app. It usually means a bare `python3 ui.py` picked up Apple's built-in Python, whose Tk window library refuses to start. Use the uv command above instead; you don't need to upgrade macOS. Do not set a fake macOS version or disable runtime checks.

To identify the interpreter and Tk version without launching the window:

```sh
uv run --locked --managed-python python -c "import sys, tkinter; print(sys.executable); print(sys.version); print(tkinter.TkVersion)"
```

### Other setup problems

| Symptom | What to check |
|---|---|
| `uv: command not found` / not recognized | Reopen the terminal after installation; use the PATH instructions printed by the official installer. |
| uv doesn't recognize `--managed-python` | Your uv is too old. Run `uv self update` (or `brew upgrade uv`). |
| `ui.py` or `pyproject.toml` not found | Change into the cloned repository's `software` folder. |
| `_tkinter` missing | On Mac/Windows use `--managed-python`. On the Pi install `python3-tk` and explicitly select `/usr/bin/python3`. Installing a package called tkinter with pip is not the fix. |
| uv says the Python version isn't supported | The app supports Python 3.10–3.13. On the Pi, see the version note above. |
| No display / `$DISPLAY` error over SSH | Use a desktop session for the window, or use the headless CLI below. |
| `--locked` reports an outdated lockfile | Check that `pyproject.toml` and `uv.lock` come from the same repository revision. Do not regenerate the lockfile just to hide a mismatched checkout. |
| Image rejected | Use a single-channel PNG/TIFF or unpacked 2D `.npy`; RGB, JPEG, packed RAW10 and DNG are unsupported. |

The managed workflow has been checked on macOS and Linux, and the Pi-style system-Python workflow on Linux. Windows and a physical Pi have not been validated yet. If reporting a problem, include the command, full error, OS, `uv --version`, and the interpreter/Tk diagnostic above (use the Pi interpreter override there too).

## Headless analysis (no window)

These commands also work over SSH without a display. They write files for you to inspect afterward.

From this folder:

With uv:

```sh
uv run --locked --managed-python examples/generate.py
uv run --locked --managed-python analyze.py examples/generated/high.npy examples/generated/low.npy --output results/demo
```

Or with a known working Python/Tk installation and pip:

```sh
python3 -m venv .venv
. .venv/bin/activate
python -m pip install -r requirements.txt
python examples/generate.py
python analyze.py examples/generated/high.npy examples/generated/low.npy --output results/demo
```

On Windows, activate with `.venv\Scripts\activate` instead of `. .venv/bin/activate`. On Raspberry Pi OS, install `python3-venv` with apt if creating the environment reports it is missing. Keep pip packages inside the virtual environment.

The example generates deterministic simulated coherent speckle fields. The low-contrast frame averages 16 independent realizations; both frames have mean intensity 1000 in arbitrary units. Expect high contrast near 1 and low contrast near 0.25. These are illustrative numerical inputs, not measured blood-flow data or a realistic camera/noise model.

Open `results/demo/measurements.png` and `results/demo/measurements.csv`. Each row records the input path, frame dimensions, ROI coordinates, mean, population standard deviation (`ddof=0`), and uncorrected contrast `K = std / mean`. Plot order follows argument order; it is not a time axis. Running again in the same output folder replaces those two result files. Input files are never changed.

## Analyze a frame

### Desktop window

Launch with the uv command for your platform above. If using the optional pip environment, activate it and run `python ui.py` instead. The workspace opens with four bundled demo images. Choose one in the image list, then drag a rectangle on the preview or enter pixel coordinates and press **Apply**. Contrast, mean and standard deviation update immediately. **Full frame** resets the region. Each image retains its own region, shown in the comparison table.

**Open images** adds your own single-channel PNG/TIFF or NumPy frames. **Preview brightness** changes only the displayed image, not measurements; it can clip bright spots on screen. **Export results** saves all loaded images' current measurements and ROI coordinates as `measurements.csv`, plus the comparison plot `measurements.png`. Existing files with those names in the chosen folder are replaced. Preview selections and brightness changes never alter source files.

The UI uses Python's Tkinter. On Raspberry Pi OS, install `python3-tk` using apt if needed. A desktop/display session is required; the CLI remains available for a headless Pi. The UI does not control the camera yet.

### Bundled demo images

The four [16-bit PNG images](examples/images/README.md) are included in the repository; no downloads or generation step is needed to try the UI. They are simulated inputs with mean intensity approximately 1000. High, medium and low contrast illustrate averaging 1, 4 and 16 independent realizations. The uniform reference has zero contrast. These are not prototype captures or physiological measurements.

### Command line

```sh
uv run --locked --managed-python analyze.py capture.npy --roi 20 30 100 80 --output results/trial01
```

(In an activated pip environment, use `python analyze.py ...` instead.)

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
uv run --locked --managed-python python -m unittest discover -s tests -v
```

Or in an activated environment:

```sh
python -m unittest discover -s tests -v
```

Checks use analytically known contrast values, a cropped ROI, high-bit-depth input, invalid frames, and an end-to-end CSV/plot run.

### Notes for contributors

- **Dependencies are listed in two places.** `pyproject.toml` (used by uv, with exact versions locked in `uv.lock`) is the main list; `requirements.txt` is kept for the pip workflow. If you add or change a dependency, update both and run `uv lock`, so pip users and uv users get the same packages.
- **Test UI changes on both Tk versions.** uv's Python on macOS, Windows and Linux uses Tk 9, while the Pi's system Python uses Tk 8.6. Run the window both ways (`--managed-python` and `--python /usr/bin/python3`) when changing `ui.py`.
