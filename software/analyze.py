"""Spatial speckle contrast for single-channel images and unpacked NumPy frames."""
import argparse
import csv
from pathlib import Path

import numpy as np
from PIL import Image


def load_frame(path):
    path = Path(path)
    if path.suffix.lower() == '.npy':
        return np.load(path, allow_pickle=False)
    with Image.open(path) as image:
        if image.format not in {'PNG', 'TIFF'}:
            raise ValueError('Use lossless PNG/TIFF or an unpacked .npy frame.')
        if getattr(image, 'n_frames', 1) != 1:
            raise ValueError('Export one frame at a time; image stacks are unsupported.')
        if image.mode not in {'L', 'I', 'I;16', 'I;16B', 'I;16L', 'F'}:
            raise ValueError('Use a single-channel image; RGB/palette images are unsupported.')
        return np.array(image)


def measure(frame, roi=None):
    """Return full-frame or ROI statistics; std uses population normalization."""
    if frame.ndim != 2 or frame.dtype.kind not in 'uif':
        raise ValueError('Expected a two-dimensional numeric intensity array.')
    height, width = frame.shape
    x, y, w, h = roi if roi is not None else (0, 0, width, height)
    if min(x, y) < 0 or min(w, h) <= 0 or x + w > width or y + h > height:
        raise ValueError('ROI must have positive size and lie entirely inside the frame.')
    pixels = frame[y:y+h, x:x+w].astype(np.float64)
    if pixels.size < 2 or not np.isfinite(pixels).all() or (pixels < 0).any():
        raise ValueError('ROI must contain at least two finite, nonnegative intensities.')
    mean = float(pixels.mean())
    if mean <= 0:
        raise ValueError('Contrast is undefined when mean intensity is zero.')
    std = float(pixels.std(ddof=0))
    return dict(width=width, height=height, x=x, y=y, roi_width=w, roi_height=h,
                mean=mean, std=std, contrast=std/mean)


def save_results(rows, output):
    # Select a noninteractive backend so the same CLI works on a headless Pi.
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt

    output.mkdir(parents=True, exist_ok=True)
    with (output / 'measurements.csv').open('w', newline='') as file:
        writer = csv.DictWriter(file, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    fig, axes = plt.subplots(1, 2, figsize=(10, 4))
    labels = [f'{i+1}: {Path(row["source"]).name}' for i, row in enumerate(rows)]
    for axis, key, label in zip(axes, ['mean', 'contrast'],
                               ['Mean intensity (input units)', 'Uncorrected contrast K = std / mean']):
        axis.bar(range(len(rows)), [row[key] for row in rows], color='#1A7E84')
        axis.set_xticks(range(len(rows)), labels, rotation=30, ha='right')
        axis.set_ylabel(label)
        axis.set_ylim(bottom=0)
    fig.tight_layout()
    fig.savefig(output / 'measurements.png', dpi=150)
    plt.close(fig)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('images', type=Path, nargs='+')
    parser.add_argument('--roi', type=int, nargs=4, metavar=('X', 'Y', 'WIDTH', 'HEIGHT'),
                        help='Pixel coordinates in each input array; default is the full frame.')
    parser.add_argument('--output', type=Path, default=Path('results'))
    args = parser.parse_args()
    rows = []
    for path in args.images:
        try:
            rows.append(dict(source=str(path.resolve()), **measure(load_frame(path), args.roi)))
        except (ValueError, OSError) as error:
            parser.error(f'{path}: {error}')
    save_results(rows, args.output)
    print(f'Saved {len(rows)} measurements to {args.output}')


if __name__ == '__main__':
    main()
