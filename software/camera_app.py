# work in progress

import os
import re
import signal
import time
import threading
import concurrent.futures
import numpy as np
import tkinter as tk
from PIL import Image, ImageTk
from picamera2 import Picamera2

# settings
EXPOSURE_US = 2000  # exposure in µs, placeholder for now, sweep ~0.5–10 ms later
GAIN = 1.0          # keep low, only bump if it's too dim
ROI = 24            # box size in red pixels, small so it fits inside the even part of the laser spot
FPS = 15            # camera frame rate cap, also limits exposure to 1/FPS (66 ms)
REDRAW_MS = 100     # ms between redraws, raised from 30 to cut lag over pi connect
STALL_S = 3         # give up and show Error after this long waiting on one frame
FIXED = {"AeEnable": False, "ExposureTime": EXPOSURE_US, "AnalogueGain": GAIN}
LIMIT = {"FrameDurationLimits": (1000000 // FPS, 1000000 // FPS)}
if EXPOSURE_US > 1000000 // FPS:
    print(f"warning: exposure {EXPOSURE_US} us is longer than one frame at {FPS} fps, the camera will cap it")


# runs a camera call in a side thread with a time limit, a stuck camera could otherwise freeze the window
def limited(fn, secs=3):
    def run():
        try:
            fn()
        except Exception as e:
            print("camera call failed:", e)
    t = threading.Thread(target=run, daemon=True)
    t.start()
    t.join(secs)
    return not t.is_alive()


# placeholder sizes so the window still opens without a camera
W, H = 1456, 1088
w, h = W // 2, H // 2
picam = None

# camera setup: small color stream for preview, full-res raw stream for measuring
connected = False
setup_error = False
try:
    connected = bool(Picamera2.global_camera_info())  # check for a camera before touching it
    if connected:
        picam = Picamera2()
        mode = picam.sensor_modes[0]  # full-res mode, check this is 1456x1088
        W, H = mode["size"]
        w, h = W // 2, H // 2                             # red plane size (also RGB preview size)
        if "FrameDurationLimits" not in picam.camera_controls:
            LIMIT = {}
        picam.configure(picam.create_preview_configuration(
            main={"size": (w, h), "format": "BGR888"},    # BGR888 gives R,G,B order for PIL
            raw={"format": mode["unpacked"], "size": (W, H)},
            # cap the frame rate: uncapped it runs ~60 fps and the pi processes frames we never show
            controls=LIMIT,
        ))

        # figure out bayer layout and bit depth from the raw format
        fmt = picam.camera_configuration()["raw"]["format"]
        if not fmt.startswith("S") or "_" in fmt:
            raise RuntimeError(f"unexpected raw format {fmt}")  # eg a packed or compressed format we can't read
        ry, rx = divmod(fmt[1:5].index("R"), 2)          # red site in the 2x2 Bayer tile
        bits = int(re.search(r"\d+", fmt).group())     # check vs max on a bright light, set to 16 if max goes way past 1023
        FULL = 2**bits - 1
        print(f"raw format {fmt}, {W}x{H}, full scale {FULL}")
except Exception as e:  # eg camera busy because rpicam-hello is still open
    print("camera setup failed:", e)
    if picam:
        limited(picam.close)
    connected = False
    setup_error = True

# measurement box, starts centered, click the preview while stopped to move it
x0, y0 = (w - ROI) // 2, (h - ROI) // 2
job = None
pending = None    # frame request that hasn't come back yet
asked = 0.0       # when that request was made, to spot a stalled camera
responding = True # false after a stall, until frames come back
closing = False
settle = 0        # frames to skip stats on after switching back from RGB
dead = False      # camera refused to stop, app needs a restart
photos = {}       # one reusable tk image per mode (gray / color)


# grabs a frame, updates the stats, draws it, then schedules itself again
def update():
    global job, pending, asked, responding, settle
    try:
        if pending is None:
            pending = picam.capture_request(wait=False)  # ask for a frame without blocking the window
            asked = time.monotonic()
        try:
            req = pending.get_result(timeout=0)
        except concurrent.futures.TimeoutError:  # not ready yet, check again shortly
            # timed from the request, not the last frame, so a slow or frozen window can't look like a stall
            if time.monotonic() - asked > STALL_S:  # camera stalled, stop instead of waiting forever
                responding = False
                raise RuntimeError("camera stopped sending frames")
            job = root.after(10, update)
            return
        pending = None
        responding = True
        try:
            if rgb.get():  # color view
                img = Image.fromarray(req.make_array("main"))
                stats.config(text="RGB preview: auto exposure, not for measurement")
            else:  # raw red-only view
                raw = req.make_array("raw").view(np.uint16)[:, :W]
                black = req.get_metadata().get("SensorBlackLevels", [0])[0] >> (16 - bits)  # sanity check this against a dark frame later

                # pull out red pixels, then speckle contrast K = std / mean in the box
                red = raw[ry::2, rx::2].astype(np.float32) - black
                if settle > 0:  # first frames after leaving RGB still have the auto exposure, K would be wrong
                    settle -= 1
                    stats.config(text="settling exposure...")
                else:
                    roi = red[y0:y0 + ROI, x0:x0 + ROI]
                    mean = roi.mean()
                    k = roi.std() / mean if mean > 0 else float("nan")
                    sat = (roi + black >= 0.98 * FULL).mean() * 100  # 98% cutoff is a rough guess
                    stats.config(text=f"K = {k:.3f}   mean = {mean:.0f}   saturated = {sat:.1f}%   max = {raw.max()}")

                # display only, doesnt touch the numbers; every 4th pixel is plenty and ~16x less work
                top = max(np.percentile(red[::4, ::4], 99.5), 1)
                img = Image.fromarray((np.clip(red / top, 0, 1) * 255).astype(np.uint8))
        finally:
            req.release()  # always hand the buffer back or the camera runs out and stalls

        # show it, reusing the same tk image instead of building a new one each frame
        photo = photos.get(img.mode)
        if photo is None:
            photo = photos[img.mode] = ImageTk.PhotoImage(img)
        else:
            photo.paste(img)
        canvas.itemconfig(img_item, image=photo)
    except Exception as e:  # covers drawing too, so nothing can kill the loop silently
        fail(e)
        return
    job = root.after(REDRAW_MS, update)


# stop cleanly and say why, instead of silently freezing
def fail(e):
    print("camera error:", e)
    stop()
    stats.config(text=f"error: {str(e)[:40]} (press Start to retry)")  # cut long messages so the window can't balloon, full text is in the terminal
    set_state("Error", "red")


# running/stopped/error label in the preview corner
def set_state(text, color):
    canvas.itemconfig(state_item, text=text, fill=color)


# auto exposure for color, locked for raw, frame rate cap either way
def controls():
    # newer libcamera ignores AeEnable alone; picamera2 only switches back to auto when exposure and gain are set to 0
    auto = {"AeEnable": True, "ExposureTime": 0, "AnalogueGain": 0}
    return {**(auto if rgb.get() else FIXED), **LIMIT}


# button handlers
def toggle_rgb():
    global settle
    if connected and not dead:
        picam.set_controls(controls())
        settle = 5


def start():
    if job is None and connected and not dead and not closing:
        try:
            picam.set_controls(controls())  # re-sent on every start, they aren't guaranteed to survive a stop
            picam.start()
        except Exception as e:  # eg camera still in a bad state after a stall
            fail(e)
            return
        set_state("Running", "lime")
        update()


def stop():
    global job, pending, dead
    if job is not None:
        root.after_cancel(job)
        job = None
    if pending is not None:  # tidy up a frame request that's still waiting so stop can't hang
        try:
            # a healthy camera delivers within one frame, so wait briefly and hand the buffer back cleanly
            pending.get_result(timeout=0.2 if responding else 0).release()
        except Exception:
            # not coming: cancel it, then release it anyway in case it landed at the last instant
            for tidy in (picam.cancel_all_and_flush, lambda: pending.get_result(timeout=0).release()):
                try:
                    tidy()
                except Exception:
                    pass
        pending = None
    if picam and picam.started and not dead:  # stop the camera even if the loop already died
        if not limited(picam.stop):
            dead = True
            print("camera would not stop, restart the app")
    set_state("Stopped", "gray")


# click on the preview to recenter the box there, only while stopped to keep things simple
def move_box(event):
    global x0, y0
    if job is None:
        x0 = min(max(event.x - ROI // 2, 0), w - ROI)  # clamped so the box stays inside the image
        y0 = min(max(event.y - ROI // 2, 0), h - ROI)
        canvas.coords(box_item, x0, y0, x0 + ROI, y0 + ROI)


def close():
    global closing
    if closing:
        return
    closing = True
    stop()
    ok = not dead and (not connected or limited(picam.close))
    root.destroy()
    if not ok:
        os._exit(1)  # camera is stuck, a normal exit could hang


# window layout
root = tk.Tk()
root.title("mini-scos")
canvas = tk.Canvas(root, width=w, height=h, bg="black")
canvas.pack()
img_item = canvas.create_image(0, 0, anchor="nw")
box_item = canvas.create_rectangle(x0, y0, x0 + ROI, y0 + ROI, outline="cyan")
canvas.bind("<Button-1>", move_box)
canvas.create_rectangle(0, 0, 80, 22, fill="black", outline="")  # dark backing so the label is readable
state_item = canvas.create_text(8, 4, anchor="nw", text="Stopped", fill="gray", font=("Courier", 11, "bold"))
stats = tk.Label(root, font=("Courier", 12))
stats.pack()
rgb = tk.BooleanVar(value=False)
tk.Button(root, text="Start", command=start).pack(side="left", padx=5, pady=5)
tk.Button(root, text="Stop", command=stop).pack(side="left", padx=5, pady=5)
tk.Checkbutton(root, text="RGB preview", variable=rgb, command=toggle_rgb,
               indicatoron=False, padx=8, pady=4).pack(side="left", padx=5, pady=5)

# camera status: green dot if found, red if not
status = tk.Canvas(root, width=14, height=14, highlightthickness=0)
status_dot = status.create_oval(2, 2, 12, 12, outline="")
status.pack(side="left", padx=(15, 2))
status_label = tk.Label(root)
status_label.pack(side="left")


# rechecks 4x a second: while running, frames should keep arriving
def check_camera():
    if setup_error:
        ok, text = False, "Camera setup failed, see terminal"
    elif not connected:
        ok, text = False, "No camera detected"
    elif dead:
        ok, text = False, "Camera stuck, restart the app"
    elif not responding or (pending is not None and time.monotonic() - asked > 1.0):  # 1 s with no frame
        ok, text = False, "Camera not responding"
    else:
        ok, text = True, "Camera detected"
    status.itemconfig(status_dot, fill="green" if ok else "red")
    status_label.config(text=text)
    root.after(250, check_camera)


check_camera()

root.protocol("WM_DELETE_WINDOW", close)
# ctrl+c in the terminal closes cleanly (tk would otherwise swallow it or leave the preview frozen)
signal.signal(signal.SIGINT, lambda *a: root.after(0, close))
root.mainloop()
