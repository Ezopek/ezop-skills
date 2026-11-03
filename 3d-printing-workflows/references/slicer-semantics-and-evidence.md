# Slicer semantics and evidence

How to avoid confident wrong answers about slicer settings, and how to audit a project or G-code. Examples use OrcaSlicer 2.4.x behaviour; versions change, so re-verify.

## 1. Verify what a setting does

- Do not infer meaning from the label. Check documentation or source for the exact slicer, fork and version. Orca/Bambu-derived settings are often unintuitive.
- Prove outcomes with emitted G-code or tool commands, or in the real UI after a restart. Exit code `0`, parseable JSON or a launched app are not evidence.
- One variable per round. Use a named sibling copy of the project; never mutate the source.

## 2. Artifact identity gate

A correct analysis of the wrong file is invalid. Before extraction or slicing:

1. Repeat the exact path or basename; check existence, size, modification time and SHA-256 on the host where the file lives.
2. If base, `*_fixes`, `*_final` or review siblings exist, compare their metadata before choosing.
3. After context compaction, failed session persistence or a handoff, revalidate the target directly. An older summary is not the artifact authority.
4. If a same-named file changed, pin and slice the new revision; do not reuse old G-code.
5. Keep the source immutable and make clearly named temporary siblings for A/B slicing.

## 3. Embedded project audit and slice

Treat a complete Orca/Bambu 3MF as a ZIP. Inspect at least `Metadata/project_settings.config`, `Metadata/model_settings.config`, `Metadata/slice_info.config`, plate JSON and previews. Verify **resolved values**, not preset names: printer and process IDs; per-tool `filament_type`, vendor profile, temperature, flow, max volumetric speed, pressure advance and colour; support filament versus support-interface filament; interface counts, Z gaps, spacing, pattern and speed; support style, threshold angle, XY distance, expansion and build-plate-only routing; seam, retraction, wipe and lift settings.

Slice a complete project from its **embedded settings first**. For Orca 2.4.2:

```bash
OrcaSlicer --slice 0 --outputdir <dir> project.3mf     # do not add --no-check
```

The release used here has no `--slice-result` option; the machine-readable result is written to `<dir>/result.json`. Require `return_code == 0` and `error_string == "Success."`, then parse the actual G-code (tool commands, roles, warnings). Capture slicer stderr and gate on missing G-code and critical warnings such as repeated `Potentially lost branch!` messages even when the exit code is zero. `--info <file>` reports manifold status and dimensions for STL or 3MF.

Do not force an older CLI through a newer project (it may reject the file or crash). A missing temporary profile is a gate-environment failure, not evidence that the project is invalid. If external profile files are used, archive the resolved files and hashes with the evidence.

## 4. Nozzle swaps, flow and Orca `Nozzle volume`

Standard checklist when changing nozzle diameter:
1. Set `Nozzle diameter` to the installed diameter.
2. Adjust line width and layer height around the new diameter.
3. Check and limit max volumetric speed per filament; larger nozzles hit flow limits quickly.
4. Recalibrate or sanity-check first layer and Z offset, flow ratio, pressure advance, temperature for higher throughput, and retraction if stringing or seams change.
5. Run a small validation print before long jobs.

For a 0.6 mm nozzle reasonable starting points (to be validated): wall line width about 0.62–0.66 mm; layer height about 0.24–0.32 mm for normal use, about 0.20 mm for nicer parts, about 0.36 mm for fast functional parts; temperature often 5–15 °C higher with higher volumetric flow; let max volumetric speed constrain speed instead of guessing each speed. A 0.6 mm nozzle is faster, stronger, better for large functional and filled parts and less clog-prone; 0.4 mm is better for detail, small text and holes.

**`Nozzle volume`** in Orca/Bambu-derived slicers is **not** the nozzle's geometric volume and is not scaled by diameter. The Orca source tooltip (version-specific: verify the exact fork and version before transferring this behaviour, because not every Bambu-derived fork inherits it) describes the volume between the filament cutter and the nozzle end, in mm³, used for flush/purge accounting and the remaining volume reset at a tool change. When swapping 0.4 to 0.6 mm on the same hotend and the same nozzle family (this narrower advice does not cover other nozzle families that merely share one hotend) change `Nozzle diameter` and normally leave `Nozzle volume`. Tune it only for filament-change purge behaviour (colour bleed, insufficient purge, waste). Sanity check: 200 mm³ is about 83 mm of 1.75 mm filament, far more than a nozzle bore.

## 5. Multi-3MF packages and shared downloads

If the geometry skill (`cad-modeling-and-reverse-engineering`) is installed, its painted-3MF reference has a package-audit section. In short: map plate instances to object names, inspect embedded printer, nozzle and filament settings, extract plate previews, slice headless from embedded settings, never print an add-on file wholesale, preserve supplied placement for parts near the bed limit, replace author filament profiles with your calibrated ones, and check mutually exclusive template objects.

## 6. Preserving user profiles

Do not erase profiles as a first response to a rendering or input problem. When comparing profiles resolve each selected machine, filament and process through every `inherits` parent; distinguish a saved custom bundle from a system bundle and from unsaved UI edits. Do not claim a remembered UI value is stored until the file proves it. See `slicer-forks-builds-and-runtime.md` for fork migration gates.
