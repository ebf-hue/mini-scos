import csv
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

import numpy as np
from PIL import Image

from analyze import load_frame, measure


class AnalysisTests(unittest.TestCase):
    def test_known_contrast_and_roi(self):
        frame = np.array([[0, 2, 100], [0, 2, 100]], dtype=np.uint16)
        result = measure(frame, (0, 0, 2, 2))
        self.assertEqual(result['mean'], 1)
        self.assertEqual(result['std'], 1)
        self.assertEqual(result['contrast'], 1)
        self.assertEqual(measure(np.full((2, 2), 60000, dtype=np.uint16))['contrast'], 0)

    def test_invalid_measurements(self):
        for frame, roi in [(np.zeros((2, 2)), None),
                           (np.array([[1., np.nan]]), None),
                           (np.array([[-1., 2.]]), None),
                           (np.ones((2, 2, 3)), None),
                           (np.ones((2, 2)), (1, 0, 2, 2)),
                           (np.ones((2, 2)), (0, 0, 1, 1))]:
            with self.subTest(frame=frame, roi=roi), self.assertRaises(ValueError):
                measure(frame, roi)

    def test_lossless_inputs_and_cli(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            high = np.array([[0, 2], [0, 2]], dtype=np.uint16)
            Image.fromarray(high).save(root/'high.png')
            np.save(root/'low.npy', np.array([[.8, 1.2], [.8, 1.2]]))
            self.assertEqual(load_frame(root/'high.png').tolist(), high.tolist())
            Image.new('RGB', (2, 2)).save(root/'color.png')
            with self.assertRaises(ValueError):
                load_frame(root/'color.png')
            subprocess.run([sys.executable, 'analyze.py', str(root/'high.png'),
                            str(root/'low.npy'), '--output', str(root/'results')], check=True,
                           cwd=Path(__file__).resolve().parents[1], capture_output=True)
            with (root/'results/measurements.csv').open() as file:
                rows = list(csv.DictReader(file))
            self.assertAlmostEqual(float(rows[0]['contrast']), 1)
            self.assertAlmostEqual(float(rows[1]['contrast']), .2)
            self.assertTrue((root/'results/measurements.png').is_file())


if __name__ == '__main__':
    unittest.main()
