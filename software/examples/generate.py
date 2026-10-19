"""Create idealized high/low contrast frames; these are not camera measurements."""

import argparse
from pathlib import Path

import numpy as np
from PIL import Image


def speckle_frames():
    rng = np.random.default_rng(601)
    n = 256
    fx, fy = np.meshgrid(np.fft.fftfreq(n), np.fft.fftfreq(n))
    aperture = fx**2 + fy**2 < 0.06**2
    frames = []
    for _ in range(16):
        field = np.fft.ifft2(aperture * np.exp(1j * rng.uniform(0, 2 * np.pi, (n, n))))
        intensity = np.abs(field) ** 2
        frames.append(intensity / intensity.mean())
    return frames


def generate_frames(output):
    output = Path(output)
    frames = speckle_frames()
    output.mkdir(parents=True, exist_ok=True)
    paths = []
    # Averaging independent realizations illustrates temporal averaging during exposure.
    for name, frame in [("high", frames[0]), ("low", np.mean(frames, axis=0))]:
        frame = (1000 * frame / frame.mean()).astype(np.float32)
        path = output / f"{name}.npy"
        np.save(path, frame)
        paths.append(path)
    return paths


def generate_demo_images(output):
    """Lossless 16-bit samples on one shared linear intensity scale."""
    output = Path(output)
    output.mkdir(parents=True, exist_ok=True)
    frames = speckle_frames()
    for name, data in [
        ("high", frames[0]),
        ("medium", np.mean(frames[:4], axis=0)),
        ("low", np.mean(frames, axis=0)),
        ("uniform", np.ones_like(frames[0])),
    ]:
        pixels = np.rint(1000 * data / data.mean()).astype(np.uint16)
        Image.fromarray(pixels).save(output / f"{name}.png")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=Path("examples/generated"))
    parser.add_argument(
        "--demo-images",
        action="store_true",
        help="Write the four 16-bit PNG samples instead.",
    )
    args = parser.parse_args()
    if args.demo_images:
        generate_demo_images(args.output)
        print(f"Saved four simulated PNG images to {args.output}")
        return
    for path in generate_frames(args.output):
        frame = np.load(path)
        print(
            f"{path.stem}: mean={frame.mean():.1f}, K={frame.std() / frame.mean():.3f} (simulation)"
        )


if __name__ == "__main__":
    main()
