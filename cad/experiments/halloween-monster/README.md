# Halloween Monster Attachment

A removable monster face for the current wrist saddle. Six blunt teeth frame the arm, with raised cartoon eyes above the mouth. The face sits forward of the camera/laser hardware. The render uses green, cream, and black to distinguish the face, teeth/eyes, and pupils; the STL is a single-colour fused part. This is decorative, not an optical enclosure or laser shield.

The two outer C-shaped shoes slide onto the existing strap ears from the front. Front stop shoulders limit how far it can slide on. The shoes leave the strap slots open, and the base saddle is not modified. Nominal top, bottom, and outer shoe clearance is 0.4 mm. The teeth have 1.6 mm rounded tips and remain outside the nominal arm reference. Physical fit, pressure, and retention have not been tested.

- `monster-wrist.png`: attachment on the camera/laser mount.
- `monster-face.png`: front view.
- `monster-wrist.solidcraft`: coloured assembly with hardware and arm references.
- `monster-attachment.step`: fused attachment only.
- `monster-attachment.stl`: one-piece attachment, oriented with the face downward.
- `checks.json`: CAD clearance, sampled slide-on travel, and mesh checks.

The generator checks for nominal intersections with the arm and existing assembly, sweeps the official camera component boxes through its 35 mm loading path, and samples the attachment sliding onto the existing saddle/laser/cap/keeper assembly at 2 mm intervals over 80 mm. Separate colour regions and their individual solids are also checked for overlap. Sampled attachment checks are not a continuous collision proof. The print mesh must be watertight, consistently wound, and connected. No support, slicing, or print-success claim is made yet.

Requires the current `14-wrist-architecture/parts/` and the official camera source in `13-bench-architecture/sources/` from this workspace. Build with:

```sh
uv run --python 3.12 --with cadquery --with trimesh python cad/experiments/halloween-monster/build.py
```

Rendering and the native assembly use the SolidCraft MCP through the included isolated client. No existing mount or print plate is overwritten.

## Collision revision

The original colour export contained overlapping solids. The current version moves the face 12 mm forward, raises and separates the eyes from the teeth, adds slide-on stop shoulders, and partitions pupil colour using a common plane. All exported colour regions are reimported and every cross-region solid pair is checked. Exported colour overlap, arm overlap, and mount/laser/keeper overlap are zero at nominal CAD dimensions. Camera insertion is checked using all 590 official camera solids without the earlier height shortcut. Attachment travel is sampled against the existing saddle and laser assembly at 2 mm intervals. Physical fit and slicing remain pending.
