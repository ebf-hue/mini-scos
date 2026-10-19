"""Coordinate mapping for a fitted image preview; independent of Tk."""

import math


def fit_image(width, height, canvas_width, canvas_height):
    scale = min(canvas_width / width, canvas_height / height)
    return (
        scale,
        (canvas_width - width * scale) / 2,
        (canvas_height - height * scale) / 2,
    )


def drag_roi(start, end, scale, offset_x, offset_y, width, height):
    x0, x1 = sorted((start[0], end[0]))
    y0, y1 = sorted((start[1], end[1]))
    x0 = max(0, min(width, math.floor((x0 - offset_x) / scale)))
    y0 = max(0, min(height, math.floor((y0 - offset_y) / scale)))
    x1 = max(0, min(width, math.ceil((x1 - offset_x) / scale)))
    y1 = max(0, min(height, math.ceil((y1 - offset_y) / scale)))
    if x1 <= x0 or y1 <= y0:
        return None
    return x0, y0, x1 - x0, y1 - y0
