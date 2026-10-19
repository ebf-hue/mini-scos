# Demo images

These 256 × 256, single-channel 16-bit PNGs are deterministic numerical simulations generated locally by `../generate.py`. They contain no participant or camera data. There are no external image dependencies.

| Image | Construction | Full-frame K, approximately |
|---|---|---|
| `high.png` | One coherent speckle realization | 1.0362 |
| `medium.png` | Mean of four independent realizations | 0.5005 |
| `low.png` | Mean of sixteen independent realizations | 0.2571 |
| `uniform.png` | All pixels equal 1000 | 0 |

All share a mean of approximately 1000 in arbitrary intensity units. Samples are rounded to unsigned 16-bit integers without per-image display normalization. The speckle fields use a circular aperture and random phase with seed 601. Averaging illustrates contrast reduction; it does not simulate calibrated flow, tissue scattering, exposure times or camera noise.

Open `python ui.py` from `software/` to compare images and draw regions. Try the same-sized region in each image, then reset to the full frame. Smaller regions can have different mean and contrast; ROI coordinates are retained in exported results. The uniform reference should retain K = 0 in every valid region.

To regenerate from `software/`:

```sh
python examples/generate.py --demo-images --output examples/images
```

Ordinary image viewers may display 16-bit values differently. The app uses one shared linear preview scale and a display-only brightness slider; analysis always uses the original integer intensities.
