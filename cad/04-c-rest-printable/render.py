"""Portable orthographic CAD rendering without a native OpenGL window."""

import numpy as np
from PIL import Image, ImageDraw


def render(items, path, position, focal, scale):
    size, aa = 1500, 2
    canvas = Image.new("RGB", (size * aa, size * aa), "#F2F5F7")
    draw = ImageDraw.Draw(canvas)
    forward = np.asarray(focal, float) - np.asarray(position, float)
    forward /= np.linalg.norm(forward)
    right = np.cross(forward, [0, 0, 1])
    right /= np.linalg.norm(right)
    up = np.cross(right, forward)
    basis = np.stack([right, up, forward], axis=1)
    light = np.array([-0.4, -0.6, 1.0])
    light /= np.linalg.norm(light)
    faces = []
    for _, shape, colour in items:
        vertices, triangles = shape.val().tessellate(0.15, 0.1)
        xyz = np.array([(v.x, v.y, v.z) for v in vertices])
        projected = (xyz - np.asarray(focal)) @ basis
        rgb = np.array([int(colour[i : i + 2], 16) for i in (1, 3, 5)])
        for tri in triangles:
            p = xyz[list(tri)]
            normal = np.cross(p[1] - p[0], p[2] - p[0])
            length = np.linalg.norm(normal)
            if length < 1e-10:
                continue
            normal /= length
            if normal @ forward > 0.001:
                continue
            q = projected[list(tri)]
            coords = [
                (
                    float((size / 2 + x * size / (2 * scale)) * aa),
                    float((size / 2 - y * size / (2 * scale)) * aa),
                )
                for x, y, _ in q
            ]
            shade = 0.48 + 0.52 * max(0, float(normal @ light))
            fill = tuple(np.clip(rgb * shade, 0, 255).astype(int))
            faces.append((float(q[:, 2].mean()), coords, fill))
    for _, coords, fill in sorted(faces, key=lambda f: f[0], reverse=True):
        draw.polygon(coords, fill=fill)
    canvas.resize((size, size), Image.Resampling.LANCZOS).save(path)
