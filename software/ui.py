"""Image workspace with live spatial contrast, preview and region selection."""

from pathlib import Path
import queue
import threading
import tkinter as tk
from tkinter import filedialog, font, ttk
import numpy as np
from PIL import Image, ImageTk
from analyze import load_frame, measure, save_results
from roi import fit_image, drag_roi

ROOT = Path(__file__).resolve().parent
INK, MUTED, ACCENT, PAPER = "#21343C", "#536772", "#16767E", "#FFFFFF"
DEMOS = [
    ("high", "High contrast", "One coherent speckle realization."),
    ("medium", "Medium contrast", "Average of four independent realizations."),
    ("low", "Low contrast", "Average of sixteen independent realizations."),
    ("uniform", "Uniform reference", "Constant intensity; expected contrast is zero."),
]


def preview_image(frame, gain=2):
    # Shared linear scale; never changes the pixels used for statistics.
    return Image.fromarray(
        np.clip(frame.astype(float) * gain / 16, 0, 255).astype("uint8")
    )


class App:
    def __init__(self, root):
        self.root, self.items, self.current = root, {}, None
        self.mapping = self.drag_start = None
        self.messages, self.exporting = queue.SimpleQueue(), False
        self.output = ROOT / "results/ui"
        self.roi_values = [tk.StringVar() for _ in range(4)]
        self.metrics = {
            k: tk.StringVar(value="—") for k in ("contrast", "mean", "std", "pixels")
        }
        self.title, self.description, self.dimensions = (
            tk.StringVar(),
            tk.StringVar(),
            tk.StringVar(),
        )
        self.status, self.gain = tk.StringVar(value="Ready."), tk.DoubleVar(value=2)
        root.title("mini-scos — Image workspace")
        root.geometry("1140x780")
        root.minsize(980, 700)
        root.configure(bg="#F1F4F5")
        family = font.nametofont("TkDefaultFont").actual("family")
        style = ttk.Style(root)
        style.theme_use("clam")
        style.configure(".", font=(family, 11), foreground=INK, background=PAPER)
        style.configure("TLabel", background=PAPER)
        style.configure("Muted.TLabel", foreground=MUTED)
        style.configure("Heading.TLabel", font=(family, 15, "bold"))
        style.configure("Title.TLabel", font=(family, 21, "bold"))
        style.configure("TButton", padding=(12, 8), background="#EAF0F2", borderwidth=0)
        style.map("TButton", background=[("active", "#DCE7EA")])
        style.configure("Accent.TButton", background=ACCENT, foreground="white")
        style.map(
            "Accent.TButton",
            background=[("disabled", "#A7B9BC"), ("active", "#105E65")],
        )
        style.configure("Treeview", rowheight=54, fieldbackground=PAPER, borderwidth=0)
        style.map(
            "Treeview",
            background=[("selected", "#DCECEE")],
            foreground=[("selected", INK)],
        )
        style.configure("Results.Treeview", rowheight=28)
        style.configure("Treeview.Heading", background="#EAF0F2", padding=(8, 6))
        header = ttk.Frame(root, padding=(22, 16))
        header.pack(fill="x")
        ttk.Label(header, text="mini-scos", style="Title.TLabel").pack(side="left")
        ttk.Label(header, text="Image workspace", style="Muted.TLabel").pack(
            side="left", padx=20
        )
        self.export = ttk.Button(
            header,
            text="Export results…",
            style="Accent.TButton",
            command=self.export_results,
        )
        self.export.pack(side="right")
        ttk.Button(header, text="Open images…", command=self.choose).pack(
            side="right", padx=10
        )
        body = ttk.Frame(root, padding=(16, 12))
        body.pack(fill="both", expand=True, pady=(1, 0))
        body.columnconfigure(1, weight=1)
        body.rowconfigure(0, weight=1)
        library = ttk.Frame(body, padding=(4, 8, 16, 8))
        library.grid(row=0, column=0, sticky="nsew")
        ttk.Label(library, text="Images", style="Heading.TLabel").pack(anchor="w")
        ttk.Label(library, text="Demo set · simulated", style="Muted.TLabel").pack(
            anchor="w", pady=(4, 12)
        )
        self.library = ttk.Treeview(library, show="tree", selectmode="browse", height=8)
        self.library.column("#0", width=176, minwidth=140)
        self.library.pack(fill="both", expand=True)
        self.library.bind("<<TreeviewSelect>>", self.select)
        ttk.Label(
            library,
            text="High, medium and low share the same mean intensity. Uniform is a zero-contrast control.",
            style="Muted.TLabel",
            wraplength=178,
        ).pack(anchor="w", pady=12)
        center = ttk.Frame(body, padding=(0, 8, 16, 0))
        center.grid(row=0, column=1, sticky="nsew")
        ttk.Label(center, textvariable=self.title, style="Heading.TLabel").pack(
            anchor="w"
        )
        ttk.Label(center, textvariable=self.dimensions, style="Muted.TLabel").pack(
            anchor="w", pady=(4, 12)
        )
        self.canvas = tk.Canvas(
            center,
            background="#19282F",
            highlightthickness=0,
            cursor="crosshair",
            height=350,
        )
        self.canvas.pack(fill="both", expand=True)
        self.canvas.bind("<Configure>", lambda event: self.draw())
        for event, callback in [
            ("<ButtonPress-1>", self.start_drag),
            ("<B1-Motion>", self.move_drag),
            ("<ButtonRelease-1>", self.end_drag),
        ]:
            self.canvas.bind(event, callback)
        ttk.Label(
            center, text="Drag on the image to select a region.", style="Muted.TLabel"
        ).pack(anchor="w", pady=(8, 0))
        ttk.Label(center, text="Image comparison", style="Heading.TLabel").pack(
            anchor="w", pady=(16, 8)
        )
        self.table = ttk.Treeview(
            center,
            columns=("name", "roi", "mean", "k"),
            show="headings",
            height=4,
            style="Results.Treeview",
        )
        for key, label, width in [
            ("name", "Image", 145),
            ("roi", "Region", 105),
            ("mean", "Mean", 85),
            ("k", "Contrast K", 85),
        ]:
            self.table.heading(key, text=label)
            self.table.column(key, width=width, minwidth=60)
        self.table.pack(fill="x")
        self.table.bind("<<TreeviewSelect>>", self.select_table)
        inspector = ttk.Frame(body, padding=(4, 8))
        inspector.grid(row=0, column=2, sticky="nsew")
        ttk.Label(inspector, text="Selected region", style="Heading.TLabel").pack(
            anchor="w"
        )
        fields = ttk.Frame(inspector)
        fields.pack(fill="x", pady=(14, 10))
        for i, (label, variable) in enumerate(
            zip(("X", "Y", "Width", "Height"), self.roi_values)
        ):
            slot = ttk.Frame(fields)
            slot.grid(row=i // 2, column=i % 2, sticky="w", padx=(0, 12), pady=(0, 8))
            ttk.Label(slot, text=label, style="Muted.TLabel").pack(anchor="w")
            entry = ttk.Entry(slot, textvariable=variable, width=8)
            entry.pack(pady=(4, 0))
            entry.bind("<Return>", lambda event: self.apply_roi())
        buttons = ttk.Frame(inspector)
        buttons.pack(fill="x")
        ttk.Button(buttons, text="Apply", command=self.apply_roi).pack(side="left")
        ttk.Button(buttons, text="Full frame", command=lambda: self.set_roi(None)).pack(
            side="left", padx=6
        )
        ttk.Separator(inspector).pack(fill="x", pady=20)
        for key, label in [
            ("contrast", "Contrast K"),
            ("mean", "Mean intensity"),
            ("std", "Standard deviation"),
            ("pixels", "Pixels in region"),
        ]:
            line = ttk.Frame(inspector)
            line.pack(fill="x", pady=7)
            ttk.Label(line, text=label, style="Muted.TLabel").pack(side="left")
            ttk.Label(
                line, textvariable=self.metrics[key], font=("TkFixedFont", 12)
            ).pack(side="right")
        ttk.Separator(inspector).pack(fill="x", pady=20)
        ttk.Label(inspector, text="Preview brightness").pack(anchor="w")
        ttk.Scale(
            inspector,
            from_=0.5,
            to=4,
            variable=self.gain,
            command=lambda value: self.draw(),
        ).pack(fill="x", pady=8)
        ttk.Label(
            inspector,
            text="Display only. Measurements use the original pixels.",
            style="Muted.TLabel",
            wraplength=218,
        ).pack(anchor="w")
        ttk.Label(
            inspector,
            textvariable=self.description,
            style="Muted.TLabel",
            wraplength=218,
        ).pack(anchor="w", pady=(24, 0))
        footer = ttk.Frame(root, padding=(22, 12))
        footer.pack(side="bottom", fill="x", before=body, pady=(1, 0))
        self.status_label = ttk.Label(
            footer, textvariable=self.status, style="Muted.TLabel", wraplength=1000
        )
        self.status_label.pack(anchor="w")
        ttk.Label(
            footer,
            text="Uncorrected spatial contrast · K = standard deviation / mean · no camera connected",
            style="Muted.TLabel",
        ).pack(anchor="w", pady=(4, 0))
        for name, title, description in DEMOS:
            self.add(
                ROOT / "examples/images" / f"{name}.png",
                title,
                "Simulated image. " + description,
            )
        if self.items:
            self.library.selection_set(next(iter(self.items)))

    def status_message(self, text, error=False):
        self.status.set(text)
        self.status_label.configure(foreground="#9B3030" if error else MUTED)

    def add(self, path, title=None, description="Imported single-channel image."):
        try:
            frame = load_frame(path)
            stats = measure(frame)
        except Exception as error:
            self.status_message(f"{path.name}: {error}", True)
            return
        key = str(path.resolve())
        if key in self.items:
            self.library.selection_set(key)
            return
        thumb = preview_image(frame)
        thumb.thumbnail((38, 38))
        photo = ImageTk.PhotoImage(thumb)
        self.items[key] = dict(
            path=path,
            title=title or path.name,
            description=description,
            frame=frame,
            roi=None,
            stats=stats,
            photo=photo,
        )
        self.library.insert(
            "", "end", iid=key, text="  " + (title or path.name), image=photo
        )
        self.table.insert(
            "",
            "end",
            iid=key,
            values=(
                title or path.name,
                "Full frame",
                f"{stats['mean']:.1f}",
                f"{stats['contrast']:.4f}",
            ),
        )

    def choose(self):
        paths = filedialog.askopenfilenames(
            title="Open single-channel images",
            filetypes=[
                ("Supported images", "*.png *.tif *.tiff *.npy"),
                ("All files", "*"),
            ],
        )
        for value in paths:
            path = Path(value)
            self.add(path)
            if str(path.resolve()) in self.items:
                self.library.selection_set(str(path.resolve()))

    def select(self, event=None):
        selected = self.library.selection()
        if not selected:
            return
        self.current = selected[0]
        item = self.items[self.current]
        h, w = item["frame"].shape
        self.title.set(item["title"])
        self.dimensions.set(
            f"{w} × {h} pixels  /  {item['frame'].dtype}  /  single channel"
        )
        self.description.set(item["description"])
        self.update_stats()
        self.draw()

    def select_table(self, event=None):
        selected = self.table.selection()
        if selected and selected[0] != self.current:
            self.library.selection_set(selected[0])

    def update_stats(self):
        item = self.items[self.current]
        s = item["stats"]
        region = item["roi"] or (0, 0, s["width"], s["height"])
        for variable, value in zip(self.roi_values, region):
            variable.set(str(value))
        for key in ("contrast", "mean", "std"):
            self.metrics[key].set(
                f"{s[key]:.4f}" if key == "contrast" else f"{s[key]:.1f}"
            )
        self.metrics["pixels"].set(f"{region[2] * region[3]:,}")
        region_text = (
            "Full frame"
            if item["roi"] is None
            else f"{region[2]} × {region[3]} @ {region[0]},{region[1]}"
        )
        self.table.item(
            self.current,
            values=(
                item["title"],
                region_text,
                f"{s['mean']:.1f}",
                f"{s['contrast']:.4f}",
            ),
        )
        self.table.selection_set(self.current)
        self.status_message(
            "Region updated. Each image keeps its own region; export includes the coordinates."
        )

    def set_roi(self, roi):
        if self.current is None:
            return
        item = self.items[self.current]
        try:
            stats = measure(item["frame"], roi)
        except ValueError as error:
            self.status_message(str(error), True)
            self.draw()
            return
        item["roi"], item["stats"] = roi, stats
        self.update_stats()
        self.draw()

    def apply_roi(self):
        try:
            roi = tuple(int(value.get()) for value in self.roi_values)
        except ValueError:
            self.status_message(
                "Enter whole pixel coordinates for X, Y, Width and Height.", True
            )
            return
        self.set_roi(roi)

    def draw(self):
        self.canvas.delete("all")
        if self.current is None:
            return
        item = self.items[self.current]
        h, w = item["frame"].shape
        scale, ox, oy = fit_image(
            w, h, max(1, self.canvas.winfo_width()), max(1, self.canvas.winfo_height())
        )
        self.mapping = scale, ox, oy, w, h
        view = preview_image(item["frame"], self.gain.get()).resize(
            (max(1, round(w * scale)), max(1, round(h * scale))),
            Image.Resampling.BILINEAR,
        )
        self.photo = ImageTk.PhotoImage(view)
        self.canvas.create_image(ox, oy, image=self.photo, anchor="nw")
        if item["roi"]:
            x, y, width, height = item["roi"]
            self.canvas.create_rectangle(
                ox + x * scale,
                oy + y * scale,
                ox + (x + width) * scale,
                oy + (y + height) * scale,
                outline="#6CE1D6",
                width=2,
            )

    def start_drag(self, event):
        if self.mapping:
            scale, ox, oy, w, h = self.mapping
            if ox <= event.x < ox + w * scale and oy <= event.y < oy + h * scale:
                self.drag_start = event.x, event.y

    def move_drag(self, event):
        if self.drag_start:
            self.canvas.delete("drag")
            self.canvas.create_rectangle(
                *self.drag_start,
                event.x,
                event.y,
                outline="#6CE1D6",
                width=2,
                tags="drag",
            )

    def end_drag(self, event):
        if self.drag_start:
            roi = drag_roi(self.drag_start, (event.x, event.y), *self.mapping)
            self.drag_start = None
            if roi:
                self.set_roi(roi)
            else:
                self.draw()

    def export_results(self):
        if self.exporting or not self.items:
            return
        folder = filedialog.askdirectory(
            title="Export CSV and comparison plot", initialdir=self.output.parent
        )
        if not folder:
            return
        self.output = Path(folder)
        rows = [
            dict(source=str(item["path"].resolve()), **item["stats"])
            for item in self.items.values()
        ]
        output = self.output
        self.exporting = True
        self.export.state(["disabled"])
        self.status_message("Saving measurements.csv and measurements.png…")

        def work():
            try:
                save_results(rows, output)
                self.messages.put((output, None))
            except Exception as error:
                self.messages.put((None, str(error)))

        threading.Thread(target=work, daemon=True).start()
        self.root.after(100, self.poll)

    def poll(self):
        try:
            output, error = self.messages.get_nowait()
        except queue.Empty:
            self.root.after(100, self.poll)
            return
        self.exporting = False
        self.export.state(["!disabled"])
        self.status_message(
            f"Export failed: {error}" if error else f"Saved CSV and plot to {output}",
            bool(error),
        )


if __name__ == "__main__":
    root = tk.Tk()
    App(root)
    root.mainloop()
