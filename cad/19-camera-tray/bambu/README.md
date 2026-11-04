# Five replacement parts — one A1 mini plate

Open [scos-five-replacements-a1-mini-red.3mf](scos-five-replacements-a1-mini-red/scos-five-replacements-a1-mini-red.3mf) in Bambu Studio. Includes the optical-window WristBase and revised LaserBracket, plus the integrated CameraPlate tray and two independent CameraClip parts. Reuse the existing frame and laser cap. Camera, lens, laser electronics and arm references are excluded.

A1 mini, stock 0.4 mm nozzle, Generic PLA (red project color), textured PEI plate, 0.20 mm layers, four walls, 30% infill, tree supports from the build plate and 5 mm automatic brims. No printer/AMS slot assignment or print submission was performed.

Estimated 95 g, about 4h40m. Bambu Studio preview reported 4h36m and 94.81 g; CLI toolpath estimate is 4h40m47s. The single plate and tree supports were inspected in Bambu Studio. All five meshes are watertight, connected and on the bed. Mesh bounds stay inside a 5 mm bed margin.

Base and tray stand on flat ends to keep dovetail channels vertical; clips rest on their broad top faces for planar release tongues; laser bracket rests on a flat foot side. Carefully remove supports/brims around the release tongues and joint entrances. Printed fits and latch durability remain unverified.

Rebuild with `uv run --python 3.12 --with cadquery --with trimesh python cad/19-camera-tray/prep_print.py`. See `mesh-and-orientation-check.json` and `scos-five-replacements-a1-mini-red/print-validation.json` for the recorded checks.
