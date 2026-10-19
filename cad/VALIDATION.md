# CAD validation

Checked October 19, 2026 from a clean copy of the staged contribution, using a fresh Python 3.12 environment and the pinned requirements.

- Both generators completed, including their previews.
- Bench generator: 14 valid parts; individual STEP reimports and volume checks passed; no printed-part interferences in the default assembly.
- Arm generator: individual solid checks and assembly STEP reimport passed (38 solids).
- All 23 included exported STEP files were reimported successfully and matched the regenerated solid counts and volumes within 0.01 mm³.
- Four imported reference/license file hashes matched the manifest. All 11 relative README links resolved in the staged contribution. Text whitespace checks passed.

Fusion import, physical printing, mechanical fit, camera/lens focus and optical performance have not been tested. The arm assembly has not had a whole-assembly collision check. See the design READMEs for the remaining limitations.
