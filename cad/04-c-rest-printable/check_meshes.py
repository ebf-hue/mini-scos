"""Check binary STL closure and bed placement without a slicer dependency."""

import collections
import json
import struct
from pathlib import Path

root = Path(__file__).resolve().parent / "exports"
report = {}
for path in sorted(root.glob("*.stl")):
    data = path.read_bytes()
    count = struct.unpack_from("<I", data, 80)[0]
    assert len(data) == 84 + count * 50, path
    edges = collections.Counter()
    min_z = float("inf")
    for i in range(count):
        values = struct.unpack_from("<9f", data, 84 + i * 50 + 12)
        points = [tuple(round(v, 4) for v in values[j : j + 3]) for j in (0, 3, 6)]
        min_z = min(min_z, *(p[2] for p in points))
        assert len(set(points)) == 3, (path, "collapsed triangle")
        for a, b in zip(points, points[1:] + points[:1]):
            edges[tuple(sorted((a, b)))] += 1
    bad = sum(n != 2 for n in edges.values())
    assert bad == 0, (path, "non-manifold edges", bad)
    assert abs(min_z) < 0.05, (path, "off bed beyond meshing tolerance", min_z)
    report[path.name] = {
        "triangles": count,
        "non_manifold_edges": bad,
        "min_z_mm": min_z,
    }
assert len(report) == 9, len(report)
(root / "mesh_validation.json").write_text(json.dumps(report, indent=2) + "\n")
print(json.dumps(report, indent=2))
