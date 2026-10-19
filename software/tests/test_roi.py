import unittest
from roi import drag_roi, fit_image


class RoiTests(unittest.TestCase):
    def test_letterbox_and_reverse_drag(self):
        scale, x, y = fit_image(200, 100, 400, 400)
        self.assertEqual((scale, x, y), (2, 0, 100))
        self.assertEqual(
            drag_roi((300, 250), (20, 120), scale, x, y, 200, 100), (10, 10, 140, 65)
        )

    def test_bounds_and_empty_drag(self):
        self.assertEqual(
            drag_roi((-20, -20), (500, 500), 2, 0, 100, 200, 100), (0, 0, 200, 100)
        )
        self.assertIsNone(drag_roi((10, 20), (20, 40), 2, 0, 100, 200, 100))
