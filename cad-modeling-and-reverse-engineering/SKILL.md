---
name: cad-modeling-and-reverse-engineering
description: "Use when designing, editing or reverse-engineering 3D-printable geometry: CAD source, STEP, STL or project 3MF (including painted or multi-part files), measuring a physical part or scan, or checking fit, clearance and retention. Covers geometry only, not slicer settings or printer operation."
compatibility: "Client-neutral guidance. The two bundled scripts need Python 3 (standard library only). Optional tools named in references: CadQuery, OpenSCAD, FreeCAD, ScanRuler, a slicer command line. None is mandatory."
metadata:
  scope: "geometry, 3MF project integrity, fit"
  companion: "3d-printing-workflows (slicer, material, printer), optional"
---

# CAD modeling and reverse engineering

Owns **geometry**: designing printable parts, rebuilding a part from a sample or scan, editing STL, STEP or project 3MF (including painted and multi-part files), and proving that geometry is correct and fits. Depth is optional: open only the reference your task needs. A one-dimension edit to a known feature does not need the full checklist (see Quick paths).

Slicer settings, materials, supports, calibration and printer operation belong to a printing workflow. So does colouring or support-painting done in a slicer UI: that is print-side tool assignment and remains with printing. This skill owns native geometry edits, standalone 3MF archive mesh or paint repair, and the geometry of any new-solid insertion (building, aligning and positioning it). If a skill named `3d-printing-workflows` is installed, use it; if not, hand over orientation and support expectations explicitly and say which slicer questions remain open.

## Route by task

| Task | Open |
|---|---|
| Unsure what file or tool to use; units, frames, reversible editing | `references/choosing-representation-and-editing.md` |
| Edit an existing STL (bore, feature, edge repair, inserts, unions) | `references/stl-feature-audit-and-edit.md` |
| Painted, multicolour or multi-part 3MF file-level edits (not slicer-UI painting) | `references/painted-3mf-editing.md` |
| Fix wrong colour labels on a dense painted mesh | `references/paint-label-repair.md`, then `references/vision-model-review.md` only if a vision model is used |
| Printable design, tolerance, export and readback gates | `references/design-and-fit-gates.md` |
| Holder, insert, cradle, clip: clearance and retention | `references/fit-clearance-and-retention.md` |
| Measure and rebuild a part from a sample (caps, threads, gears) | `references/physical-reverse-engineering.md` |
| Physical part or scan with a live ScanRuler session | `references/scanruler-workflow.md` |
| Logo or artwork to geometry | `references/logo-artwork-to-geometry.md` |
| Parametric insert prototyping, or preparing a model for public release | `references/parametric-prototyping-and-release.md` |
| A video or tip that claims a modelling technique | Use the intake procedure in the printing skill if installed; otherwise treat the claim as a candidate and test it on a copy |

## Core rules (always on)

1. **Representation first.** Native editable source or STEP B-rep beats a mesh. A triangle mesh cannot return original history or exact surface types, so large or fit-critical changes mean re-modelling from fitted measurements, not patching facets. A project 3MF is a container with paint, parts, transforms and metadata, not just a mesh.
2. **Tool choice is not fixed.** Choose by input representation, deliverable and what is reachable. ScanRuler suits physical parts, scans and saved parametric projects; CadQuery, OpenSCAD and FreeCAD suit scripted or numeric designs. Keep one source of truth for the final geometry and record which it is.
3. **Never modify originals.** Edit a named sibling; record SHA-256 of source and output; diff outside the intended edit region.
4. **Units and frames are explicit.** State units and the frame (local, assembled, plate, scan) with every number. Tools may display inches while their API uses millimetres and degrees.
5. **Verify a feature geometrically before editing it.** Fit the actual faces and report centre, diameter, span and residual. Name parameters after the physical surface.
6. **No silent loss.** Never discard paint, parts, assembly transforms or project metadata. A flattened geometry-only 3MF or STL is a diagnostic or alternative sibling, never the completed delivery of a coloured or painted request. If colour-preserving delivery fails, report **NOT DONE (colour-preserving)** with the blocker.
7. **Manifold is not functional.** Closed, positive volume and one component are necessary for a single-solid part, not sufficient. Assemblies and multi-part files need the specified solid count and per-solid validity; a surface is never labelled a print-ready solid. Insertion path, retention, seated state and slicer layer preview of thin features are separate gates.
8. **Different judgements stay different.** Kernel validity, scan match, export readback, slicer acceptance, physical fit and visual quality are separate claims. Say which you ran and which are pending. Static instructions are not exercised behaviour.
9. **Measure, then model.** Measurements carry uncertainty; a scan shows the as-made, possibly worn part, not the design. Label figures measured, partly supported or inferred. Use a coupon for the critical interface before the full part and change one fit variable per iteration. Do not assume universal tolerances or promise a fit.
10. **Finish the loop.** When asked for a finished artifact, own diagnosis, implementation and validation, and report once with evidence. Do not narrate every obstacle.

## Quick paths

- **Tiny dimensional edit (known STL feature):** hash source, audit the feature geometrically, edit a sibling, re-read the export and re-measure the same quantity, confirm bounds and other geometry unchanged, report.
- **New printable part from numbers:** parameters, then CadQuery, OpenSCAD or ScanRuler headless, STEP and STL export, independent readback, coupon for any physical interface.
- **Reproduce a physical part:** request orthographic photos with scale and calipers, annotate what to measure, build a provisional parametric model, fit coupon, iterate.
- **Scan-based reconstruction:** needs a connected ScanRuler page session; discover live tools and guides, protect existing session state, checkpoint, then follow `references/scanruler-workflow.md`. A headless session cannot qualify a scan reconstruction.
- **Painted 3MF edit:** `references/painted-3mf-editing.md`; verify paint-token counts, parts, transforms and metadata values before claiming colour-preserving delivery.

## Hard safeguards

- Never run dense point-in-mesh rasterisation, voxelisation or unbounded Boolean or render workloads on a shared host. A small 2D slice can allocate tens of GiB when every sample runs mesh containment. Estimate grid or voxel counts first and use a strict resource cap or an isolated workstation. Prefer sparse sections, sampled surface queries and bounded-resolution previews.
- An out-of-memory kill or heavy memory pressure is a hard stop: cancel remaining geometry work and report it. Do not retry on that host without the operator's approval.
- Do not touch printers, firmware, services or the operator's real desktop as part of geometry work. Capturing a real desktop needs prior warning and approval.
- Do not change a live ScanRuler page beyond the agreed scope, and never discard someone's unsaved session.

## Bundled helpers

`scripts/apply_reviewed_paint_cleanup.py` and `scripts/verify_3mf_paint_cleanup.py` apply and independently verify a reviewed set of whole-face paint relabels on a 3MF sibling (standard library only, tested on synthetic files). Read the source and `--help`, and confirm the file layout matches before use; see `references/paint-label-repair.md` for the supported case and limits. Nothing else is scripted: other procedures describe what to compute, not code to run blindly.
