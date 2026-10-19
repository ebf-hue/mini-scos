"""Small Tk desktop interface for the existing contrast-analysis pipeline."""
from pathlib import Path
import queue
import threading
import tkinter as tk
from tkinter import filedialog, messagebox, ttk

from PIL import Image, ImageTk

from analyze import load_frame, measure, save_results
from examples.generate import generate_frames

ROOT = Path(__file__).resolve().parent


class App:
    def __init__(self, root):
        self.root = root
        root.title('mini-scos — Contrast analysis')
        root.geometry('1000x820')
        root.minsize(760, 650)
        self.paths = []
        self.messages = queue.SimpleQueue()
        self.use_roi = tk.BooleanVar(value=False)
        self.roi = [tk.StringVar(value=v) for v in ('0', '0', '100', '100')]
        self.output = tk.StringVar(value=str(ROOT/'results/ui'))
        self.status = tk.StringVar(value='Choose frames or run the simulated demo.')
        self.files = tk.StringVar(value='No frames selected')

        frame = ttk.Frame(root, padding=16)
        frame.pack(fill='both', expand=True)
        ttk.Label(frame, text='mini-scos', font=('Arial', 22, 'bold')).pack(anchor='w')
        ttk.Label(frame, text='Spatial contrast analysis • camera capture is not connected').pack(anchor='w', pady=(0, 12))
        actions = ttk.Frame(frame)
        actions.pack(fill='x')
        self.buttons = []
        for text, command in [('Choose frames…', self.choose),
                              ('Run simulated demo', self.demo), ('Analyze', self.analyze)]:
            button = ttk.Button(actions, text=text, command=command)
            button.pack(side='left', padx=(0, 8))
            self.buttons.append(button)
        ttk.Label(frame, textvariable=self.files, wraplength=900).pack(anchor='w', pady=8)

        roi = ttk.Frame(frame)
        roi.pack(fill='x', pady=4)
        ttk.Checkbutton(roi, text='Use ROI', variable=self.use_roi).pack(side='left', padx=(0, 12))
        for name, value in zip(('X', 'Y', 'Width', 'Height'), self.roi):
            ttk.Label(roi, text=name).pack(side='left', padx=(0, 4))
            ttk.Entry(roi, textvariable=value, width=7).pack(side='left', padx=(0, 12))
        ttk.Label(frame, text='ROI uses input-array pixels; leave unchecked for the full frame.').pack(anchor='w')

        output = ttk.Frame(frame)
        output.pack(fill='x', pady=10)
        ttk.Label(output, text='Save to').pack(side='left', padx=(0, 8))
        ttk.Entry(output, textvariable=self.output).pack(side='left', fill='x', expand=True)
        browse = ttk.Button(output, text='Browse…', command=self.choose_output)
        browse.pack(side='left', padx=(8, 0))
        self.buttons.append(browse)
        ttk.Label(frame, text='Each run replaces measurements.csv and measurements.png in this folder.').pack(anchor='w')

        self.table = ttk.Treeview(frame, columns=('source', 'mean', 'std', 'contrast'),
                                  show='headings', height=4)
        for key, title in [('source', 'Frame'), ('mean', 'Mean'), ('std', 'Std dev'), ('contrast', 'Contrast K')]:
            self.table.heading(key, text=title)
            self.table.column(key, width=350 if key == 'source' else 140, anchor='w')
        self.table.pack(fill='x', pady=(12, 8))
        self.plot = ttk.Label(frame, anchor='center')
        self.plot.pack(fill='both', expand=True)
        ttk.Label(frame, textvariable=self.status, wraplength=900).pack(anchor='w', pady=(8, 0))
        ttk.Label(frame, text='Uncorrected spatial contrast; not a blood-flow or blood-pressure estimate.').pack(anchor='w')

    def clear(self):
        self.table.delete(*self.table.get_children())
        self.plot.configure(image='')
        self.plot.image = None

    def choose(self):
        paths = filedialog.askopenfilenames(title='Choose single-channel frames', filetypes=[
            ('Supported frames', '*.npy *.png *.tif *.tiff'), ('All files', '*')])
        if paths:
            self.paths = [Path(p) for p in paths]
            self.files.set(f'{len(paths)} frame(s): ' + ', '.join(p.name for p in self.paths))
            self.clear()
            self.status.set('Ready. PNG/TIFF must be single-channel; NumPy frames must be unpacked 2D arrays.')

    def choose_output(self):
        folder = filedialog.askdirectory(title='Choose results folder')
        if folder:
            self.output.set(folder)

    def demo(self):
        self.paths = generate_frames(ROOT/'examples/generated')
        self.files.set('SIMULATION: high.npy and low.npy • matched mean brightness')
        self.use_roi.set(False)
        self.analyze()

    def analyze(self):
        if not self.paths:
            messagebox.showinfo('No frames', 'Choose frames or run the simulated demo.')
            return
        try:
            roi = tuple(int(v.get()) for v in self.roi) if self.use_roi.get() else None
            if not self.output.get().strip():
                raise ValueError('Choose an output folder.')
            output = Path(self.output.get()).expanduser().resolve()
        except ValueError as error:
            messagebox.showerror('Check settings', str(error))
            return
        paths = list(self.paths)
        self.clear()
        for button in self.buttons:
            button.state(['disabled'])
        self.status.set('Analyzing…')

        def work():
            try:
                rows = []
                for path in paths:
                    try:
                        rows.append(dict(source=str(path.resolve()), **measure(load_frame(path), roi)))
                    except Exception as error:
                        raise ValueError(f'{path.name}: {error}') from error
                save_results(rows, output)
                self.messages.put((rows, output, None))
            except Exception as error:
                self.messages.put((None, None, str(error)))

        threading.Thread(target=work, daemon=True).start()
        self.root.after(100, self.poll)

    def poll(self):
        try:
            rows, output, error = self.messages.get_nowait()
        except queue.Empty:
            self.root.after(100, self.poll)
            return
        for button in self.buttons:
            button.state(['!disabled'])
        if error:
            self.status.set('Analysis failed. Check the frame and ROI settings.')
            messagebox.showerror('Analysis failed', error)
            return
        for row in rows:
            self.table.insert('', 'end', values=(Path(row['source']).name,
                f'{row["mean"]:.3f}', f'{row["std"]:.3f}', f'{row["contrast"]:.4f}'))
        try:
            with Image.open(output/'measurements.png') as image:
                image.thumbnail((900, 360))
                self.plot.image = ImageTk.PhotoImage(image)
            self.plot.configure(image=self.plot.image)
            self.status.set(f'Saved CSV and plot to {output}')
        except OSError as error:
            self.status.set(f'Results saved to {output}; could not display plot: {error}')


if __name__ == '__main__':
    root = tk.Tk()
    App(root)
    root.mainloop()
