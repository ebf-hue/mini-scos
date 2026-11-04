# A1 mini print preparation

Open [tower-dovetail-a1-mini-black.3mf](tower-dovetail-a1-mini-black/tower-dovetail-a1-mini-black.3mf) in Bambu Studio. All six printed parts are on one plate; hardware and arm references are excluded. Saved and checked in Bambu Studio 2.8.2.61 with embedded toolpaths.

A1 mini, stock 0.4 mm nozzle, Generic PLA in black, Textured PEI plate, 0.20 mm layers, four walls, 30% infill, automatic tree supports from the build plate. GUI estimate: 6h30m and 143.31 g including supports. No print was sent.

See `mesh-and-orientation-check.json` for the individual orientations and mesh checks. The frame rests on its rear brace; base and camera plate stand on flat ends to keep the rail channels vertical; retainer rests on its broad top face. Laser cap stands on its axial end. Brims/supports require careful removal near the release tabs. Physical fit and latch strength remain untested. The small joint coupons in `../fit-coupon/` can be printed first.

Recreate using `uv run --python 3.12 --with cadquery --with trimesh python cad/16-tower-dovetail/prep_print.py` from the repository root. The script uses Bambu Studio profiles bundled with the macOS application and a fixed single-plate layout.
