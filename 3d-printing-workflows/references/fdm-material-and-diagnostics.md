# FDM material, slicer and diagnostic baseline, flow and pressure-advance calibration

Reusable principles, not a profile to copy. Printer-specific references, the active slicer version and profile, and a controlled test override this file.

## 1. First-pass operating order

1. Select the actual printer, nozzle and filament profile.
2. Validate bed cleanliness and first-layer adhesion before deep troubleshooting.
3. Let geometry set the trade-off: layer height or adaptive layers, walls, infill, support, orientation.
4. Change one causal layer at a time and validate with a small print or known-good benchmark.

## 2. Materials and bed

- PLA is the normal low-friction default. PETG is a sensible next option when heat or UV resistance matters. The filament maker's drying guidance and the spool's actual condition control any drying decision.
- Filled materials are abrasive; check nozzle and hotend suitability and flow limits instead of assuming.
- Adhesion: start with a clean plate (wash with dish soap and water when appropriate for the plate), avoid finger oils, inspect lift or warp before changing unrelated settings. Escalate footprint support in order: clean the surface, suitable adhesion or release method, brim for a small contact area, local corner tabs for a broad part lifting only at corners.

## 3. Slicer principles

- Layer height is a surface-versus-time decision; adaptive layers help where vertical regions can stay coarse while curves gain resolution.
- For strength add **walls before global infill**. Infill percentage is not a universal strength dial; load path, shell thickness, orientation and material dominate. Use local modifiers for bolt zones instead of globally densifying.
- A larger nozzle or wider extrusion saves time only if the real hotend and filament have volumetric-flow headroom and the geometry still meets needs.
- Consider reorientation and a support-free CAD change before adding support. Tree versus normal or snug support is geometry-dependent; slice preview is the authority.

## 4. Cheap causal diagnosis

| Symptom | First boundary to test |
|---|---|
| Lifting, part breaks loose | Plate cleanliness, first layer, footprint, local warp, ambient conditions |
| Spaghetti | Failure height: immediate means adhesion; at a local height means unsupported geometry; later collision means lift, warp or instability |
| Gaps or underfill | Requested volumetric flow versus filament capability; then a partial clog or nozzle condition |
| Unknown-origin quality problem | A known-good benchmark: failing benchmark points to printer or material; clean benchmark points to model, project or profile |

A benchmark result narrows the failing boundary; it does not prove every setting.

These baselines were distilled in part from a public practitioner video, "Everything I know about 3D Printing" (<https://www.youtube.com/watch?v=gPW_mitgosw>); treat them as heuristics.

## 5. Flow-cap sanity check

`volumetric flow ≈ line width × layer height × speed`. For a 0.42 mm line at 0.20 mm layer: 100 mm/s is 8.4 mm³/s, 150 mm/s is 12.6, 200 mm/s is 16.8. Keep tests comfortably below the filament's verified max volumetric speed; otherwise starvation contaminates the result and you calibrate hotend throughput failure instead of pressure response.

## 6. Pressure-advance (PA) calibration

Sequence: dry the filament and use its real print temperature; calibrate the flow ratio before PA; use a PA pattern unless first-layer quality is unreliable (a tower is slower but less first-layer-sensitive); test at conditions resembling the user's normal **outer-wall** speed and acceleration, with the real nozzle temperature, line width, layer height and process, not the printer's headline maximum; if normal prints span very different regimes validate a second point or use the slicer's adaptive PA workflow instead of forcing one value; save the result in the filament profile and label it by material and nozzle.

Generic starting points for a direct-drive extruder (to be validated): about 100 mm/s at 5000 mm/s²; a faster PLA validation point about 150 mm/s at 8000 mm/s², only if max volumetric speed leaves headroom.

Orca PA pattern, empty fields (verify in your version): empty `Accelerations` uses the active outer-wall acceleration, then inner-wall, then default acceleration; empty `Speeds` triggers an optimal PA speed calculation constrained by the active configuration and max volumetric speed; comma-separated lists create a speed × acceleration matrix. Leaving both empty is a good default when the printer, filament and process profiles reflect real printing. Use explicit values when comparing profiles, reproducing a test or deliberately validating high speed.

Pitfalls: do not calibrate at the machine's maximum speed merely because it can move that fast; do not change temperature, flow, speed, acceleration and PA together; do not reuse PA blindly across brands, hotend replacement or major temperature changes; an automatic on-printer flow calibration may be stored in firmware per loaded filament and never written back to the slicer, so do not present it as a durable slicer-profile calibration.
