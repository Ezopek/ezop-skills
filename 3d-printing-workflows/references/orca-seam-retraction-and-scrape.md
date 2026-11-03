# OrcaSlicer seam, retraction and scrape diagnostics

Applies to OrcaSlicer 2.4.x-class behaviour (verify the version). Values from the validated Snapmaker U1 cases are examples, never presets. Analysers are in `../scripts/`.

## 1. Seam gaps and post-retraction under-extrusion

First separate visually similar failures:
- **Regular, vertically aligned pits on otherwise clean walls** are seam start or end defects.
- **Large ragged voids beside unsupported ledges, bridges or dissimilar-material support interfaces** are support or overhang failures or removal damage. A seam fix will not repair them.
- **Global thin walls away from the seam** point to flow, temperature, volumetric-flow or mechanical trouble.

Do not diagnose from photos alone. Establish the artifact identity gate (`slicer-semantics-and-evidence.md`), audit the embedded settings and the exact emitted G-code. Check whether a nonzero `seam_gap`, zero `retraction_minimum_travel`, full retract and wipe cycles on tiny inner-to-outer hops, and unstaggered seams across only two walls compound each other.

Settings to inspect (do not infer from labels): seam (`seam_gap`, `seam_position`, `staggered_inner_seams`, scarf settings); walls (`wall_loops`, `wall_sequence`, `wall_generator`, outer-wall speed and acceleration); retraction (`retraction_minimum_travel`, `retraction_length`, speeds, `retract_restart_extra`, `retract_when_changing_layer`); wipe; extrusion control (pressure advance, flow ratio, max volumetric speed, temperature); multicolour context (toolchange G-code, prime tower, interface filament, flush volumes).

Semantics worth knowing:
- `seam_gap` is a physical gap in mm, or a percentage of **nozzle diameter**, between loop ends. 10 % of a 0.4 mm nozzle leaves 0.04 mm.
- `retraction_minimum_travel` is the travel distance below which retraction is skipped; 0 means nearly every eligible travel retracts.
- `wipe` moves backward along the last extrusion while retracting; on very short paths much of the retraction may become a fast move.
- Excessive pressure advance can under-extrude the end of a loop; too little leaves pressure, ooze and bulges. Calibrate PA instead of using the seam gap as a generic knob.
- An `Inner/Outer` wall order is already seam-friendly. Staggered inner seams avoid one through-thickness weak line.

Prove what was emitted:
1. Slice the complete project with the same slicer version and embedded settings.
2. Run `scripts/analyze_orca_seam_gcode.py` (needs `;TYPE:` role comments, absolute XY positioning and relative extrusion declared with `M83` before any E word; it refuses XYZ motion under `G91`, extrusion under `M82` or before `M83`, non-extruding arcs, full-circle arcs, and malformed or nonfinite motion numbers; the complete refusal list is in `orca-audit-tooling.md`, and anything outside it is not detected). It counts outer and inner extrusion paths, loop-end gaps, short pre-path travels and retract or de-retract activity. Useful options: `--short-travel-mm`, `--target-gap-mm`, `--expected-retraction-mm`.
3. Inspect one representative loop directly: the XY before the first positive-extrusion move is the loop start, the last positive-extrusion endpoint is the loop end, and their distance is the emitted seam gap. Compare the previous wall's endpoint with the new loop start to see whether a tiny hop caused a full retract, wipe and de-retract.
4. Build only a temporary sibling project for A/B slicing, patch one causal cluster at a time, reslice, rerun the analyser and compare footer time and material.

## 2. Choosing the first A/B without disabling intentional Z-hop

Independent controls: `retraction_length` (filament pulled back), `retraction_minimum_travel` (threshold), `wipe_distance`, `z_hop` or lift height, and travel slope or Auto Lift. A user who raised lift height and slope usually did so because the nozzle scraped; do not read that as excess retraction and do not silently undo it.

In Orca 2.4.2 `needs_retraction()` is false for travel shorter than `retraction_minimum_travel` before lift selection, so suppressing retraction also suppresses Z-hop for that travel. `reduce_infill_retraction=1` can independently suppress retraction (and so lift) on long travels kept inside infill. Inspect actual XY and Z G-code; do not reason from the UI value.

When the profile has a nonzero seam gap, zero travel threshold and aligned inner seams:
- if Z-hop has no proven anti-scrape role, a 2.0 mm threshold is a useful diagnostic A/B;
- if Z-hop is deliberate, compute the exact short-travel histogram and begin around 0.6–1.0 mm, or just above the recurring inner-to-outer hop, so tiny seam-adjacent moves stop retracting while longer collision-prone travels keep lift;
- keep the user's validated lift height, type and slope; set seam gap to 0 % (retry at 5 % if it bulges); enable staggered inner seams; keep an already correct Inner/Outer order; leave retraction length, wipe, flow and temperature unchanged at first; keep scarf seam off until a conventional seam is stable (scarf can mask a cosmetic seam but does not cure pressure loss).
- Validate scraping as well as seam quality. If a conservative threshold removes the defect without contact, do not raise it without a reason.

If pits remain: calibrate PA at representative outer-wall speed and acceleration; reduce outer-wall speed and acceleration for a small validation print; only for starvation specifically after long retractions, test a very small positive restart extra. Do not start by raising global flow.

Validated example (one project, not a preset): a 750-layer four-tool project had 10 % seam gap, 0 minimum travel, 0.8 mm retraction, 2 mm wipe, aligned inner seams. 95.4 % of 7,629 outer paths began after a direct move shorter than 2 mm, 72.5 % had a full retract before them, a 0.475 mm hop still triggered the full cycle, and loops ended 0.040 mm short (exactly 10 % of 0.4 mm). A temporary A/B (2 mm threshold, 0 % gap, staggered inner seams) cut full outer-path retracts by 91.6 % and shortened estimated time by about 26 minutes, proving these settings shaped the G-code; it does not make 2 mm universal.

## 3. Sparse-infill and travel scrape

Use when a nozzle audibly rubs or clicks over sparse infill or during fast travels, especially after raising Z-hop or Auto Lift slope did not help.

Separate two classes first:
1. **Extrusion-on-extrusion crossing:** the active sparse move crosses a line already deposited on the layer. Z-hop cannot help. Grid, Cubic and Adaptive Cubic have many.
2. **Travel-on-extrusion crossing:** a non-extruding move crosses prior infill without lifting. Often reducible without changing the pattern.

If the user wants to keep the crossing pattern, do not substitute a non-crossing pattern and call it solved; treat pattern replacement as a separate option.

Configured Z-hop may not appear: lift selection follows retraction eligibility, so travels below `retraction_minimum_travel` and long travels under `reduce_infill_retraction=1` can cross several deposited lines at nominal Z.

One-variable A/B:
1. Freeze the exact 3MF by SHA-256 and slice it with retained G-code.
2. Create a sibling that changes only `reduce_infill_retraction` from `1` to `0` (verify only `Metadata/project_settings.config` changed).
3. Slice with the same slicer version and run `python3 scripts/analyze_orca_sparse_scrape.py plate_1.gcode report.json`.
4. Compare `no_hop_travels_cross_prior_sparse` (primary travel-scrape metric), `sparse_travels_hopped`, sparse and total retractions, `sparse_extrusions_cross_prior_sparse` (should stay unchanged), estimated time, material, toolchanges and layer count.

The analyser requires absolute XY positioning (`G90` or the default) and relative extrusion declared with `M83` before any E word. It refuses XYZ motion under `G91`, extrusion under `M82` or before `M83`, non-extruding arcs in sparse infill, full-circle arcs in any role, malformed or nonfinite motion numbers, and a report path that is the same file as the source (including a symlink or hardlink alias), which it refuses before writing; anything outside that list is not detected. It intersects straight `G1` sparse extrusion segments only; extruding arcs are omitted, so accepted-input crossing totals remain lower bounds. Sloped Auto Lift can split a logical travel into several moves, so compare crossings at nominal Z, not raw travel totals. The analyser also enforces a fixed budget of 1,000,000 spatial work units per invocation (cell visits, bucket entries, candidate checks, grid insertions; never reset per layer, no override): an input beyond it is NOT DONE by this probe (explicit message, no report, source untouched) and needs a separately qualified bounded backend, not an unsafe retry. The budget is an implementation guard, not OS containment or a timing claim, and a full real-plate G-code can exceed it. On full-circle arcs the two analysers differ and neither computes geometry: the sparse analyser treats an end point as the start when it is within 1e-9 mm per X and per Y (not exact equality), while the seam analyser compares its end point to the start exactly, with no tolerance. The seam analyser also refuses a nonfinite derived value (an overflowing difference, hypot, accumulated total or even-length median) by line before printing anything, and its numeric command-line options must be finite. Both analysers also refuse a declared layer-Z (`;Z:`) value that is malformed or not a finite number (NaN, infinity, overflow), by line and without echoing it, and the sparse report is written as strict JSON (no NaN or Infinity). If the sparse report path already exists but its identity cannot be determined relative to the source (a permission or I/O fault, a dangling link), the analyser refuses instead of writing; only a confirmed missing destination proceeds. That is a fail-closed check, not a lock, and it gives no guarantee against a concurrent rewrite.

Validated example: a 493-layer, 20 % Adaptive Cubic project with 0.6 mm Z-hop, Auto Lift 75° and 0.8 mm retraction changed only `reduce_infill_retraction`. No-hop travels crossing prior infill dropped 86 % (4,256 to 594); same-layer extrusion crossings were unchanged; sparse retractions rose from 2,044 to 10,167, logical retractions by 58 %, and estimated time by almost an hour. Report both benefit and cost, and the short-retraction warning.

**Live-print safety:** investigation stays read-only. Do not change Z offset in response to higher-layer rubbing. A brief light scrape limited to infill can be monitored; pause if impacts become regular or hard, the model or supports move, branches tear, or a layer shifts. A feedrate reduction lowers impact energy but creates no clearance and changes no generated lift decision.
