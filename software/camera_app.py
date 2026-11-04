# camera_app.py is a rough work in progress. make sure to install the python3-pil.imagetk library before running.
import numpy as np
import tkinter as tk
from PIL import Image, ImageTk
from picamera2 import Picamera2

# settings
EXPOSURE_US = 2000  # exposure in µs, placeholder for now, sweep ~0.5–10 ms later
GAIN = 1.0          # keep low, only bump if it's too dim
ROI = 64            # box size in red pixels, might shrink/grow once we see real speckle
FIXED = {"AeEnable": False, "ExposureTime": EXPOSURE_US, "AnalogueGain": GAIN}

# camera setup: small color stream for preview, full-res raw stream for measuring
picam = Picamera2()
mode = picam.sensor_modes[0]  # full-res mode, check this is 1456x1088
W, H = mode["size"]
w, h = W // 2, H // 2                             # red plane size (also RGB preview size)
picam.configure(picam.create_preview_configuration(
    main={"size": (w, h), "format": "BGR888"},    # BGR888 gives R,G,B order for PIL
    raw={"format": mode["unpacked"], "size": (W, H)},
))
picam.set_controls(FIXED)

# figure out bayer layout and bit depth from the raw format
fmt = picam.camera_configuration()["raw"]["format"]
ry, rx = divmod(fmt[1:5].index("R"), 2)          # red site in the 2x2 Bayer tile
bits = int("".join(c for c in fmt if c.isdigit()))  # check vs max on a bright light, set to 16 if max goes way past 1023
FULL = 2**bits - 1
print(f"raw format {fmt}, {W}x{H}, full scale {FULL}")

# measurement box, centered
x0, y0 = (w - ROI) // 2, (h - ROI) // 2
job = None


# grabs a frame, updates the stats, draws it, then schedules itself again
def update():
    global job
    req = picam.capture_request()
    if rgb.get():  # color view
        img = Image.fromarray(req.make_array("main"))
        req.release()
        stats.config(text="RGB preview: auto exposure, not for measurement")
    else:  # raw red-only view
        raw = req.make_array("raw").view(np.uint16)[:, :W]
        black = req.get_metadata().get("SensorBlackLevels", [0])[0] >> (16 - bits)  # sanity check this against a dark frame later
        req.release()

        # pull out red pixels, then speckle contrast K = std / mean in the box
        red = raw[ry::2, rx::2].astype(np.float32) - black
        roi = red[y0:y0 + ROI, x0:x0 + ROI]
        mean = roi.mean()
        k = roi.std() / mean if mean > 0 else float("nan")
        sat = (roi + black >= 0.98 * FULL).mean() * 100  # 98% cutoff is a rough guess
        stats.config(text=f"K = {k:.3f}   mean = {mean:.0f}   saturated = {sat:.1f}%   max = {raw.max()}")

        top = max(np.percentile(red, 99.5), 1)  # display only, doesnt touch the numbers
        img = Image.fromarray((np.clip(red / top, 0, 1) * 255).astype(np.uint8))

    # show it
    photo = ImageTk.PhotoImage(img)
    canvas.itemconfig(img_item, image=photo)
    canvas.image = photo
    job = root.after(30, update)  # ms between redraws, bump up if the pi lags


# button handlers
def toggle_rgb():
    picam.set_controls({"AeEnable": True} if rgb.get() else FIXED)  # auto exposure for color, locked for raw


def start():
    if job is None:
        picam.start()
        update()


def stop():
    global job
    if job is not None:
        root.after_cancel(job)
        job = None
        picam.stop()


def close():
    stop()
    picam.close()
    root.destroy()


# window layout
root = tk.Tk()
root.title("mini-scos")
canvas = tk.Canvas(root, width=w, height=h, bg="black")
canvas.pack()
img_item = canvas.create_image(0, 0, anchor="nw")
canvas.create_rectangle(x0, y0, x0 + ROI, y0 + ROI, outline="cyan")
stats = tk.Label(root, font=("Courier", 12))
stats.pack()
rgb = tk.BooleanVar(value=False)
tk.Button(root, text="Start", command=start).pack(side="left", padx=5, pady=5)
tk.Button(root, text="Stop", command=stop).pack(side="left", padx=5, pady=5)
tk.Checkbutton(root, text="RGB preview", variable=rgb, command=toggle_rgb,
               indicatoron=False, padx=8, pady=4).pack(side="left", padx=5, pady=5)
root.protocol("WM_DELETE_WINDOW", close)
root.mainloop()
