# Choosing a representation and tool, and editing safely

Read this when the request is more than a one-dimension tweak, or when you are unsure what kind of file you were given.

## 1. What do you have? (representation decides the method)

| You have | What it is | Typical correct move |
|---|---|---|
| Native editable source (CadQuery or OpenSCAD script, FreeCAD, Fusion or Onshape document, ScanRuler project) | Parametric history and named parameters | Edit the parameter or feature and re-export. Preferred over touching meshes. |
| STEP / B-rep | Exact analytic faces but **no feature history** | Direct-modelling edits (move or offset a face, cut, add) in a B-rep-capable tool, or re-model the few features that change. |
| STL / triangle mesh | Triangulation only. History, parameters and exact surface types cannot be recovered from triangles; a fitted cylinder is an estimate | Small isolated change: audited vertex-level or Boolean edit on a sibling (`stl-feature-audit-and-edit.md`). Dimension-critical or many changes: rebuild parametrically from fitted measurements. |
| Project 3MF (painted, multi-part, plates, settings) | A container: meshes, transforms, paint and slicer metadata | Treat as a project, not a mesh: `painted-3mf-editing.md`. Never flatten silently. |
| Physical sample or scan | Evidence about an as-made, possibly worn or warped object, not the design | `physical-reverse-engineering.md`; `scanruler-workflow.md` when a live ScanRuler session fits. |

If someone says "edit this STL" and a native or STEP source exists or can be found, say so and offer it. Do not polish facets when a parameter would do.

## 2. Choosing the tool (no absolute default)

- **ScanRuler** (optional, live connector): suited to a physical part or scan, a parametric B-rep held in a saved project with measured deviation against the scan, or STEP plus editable project plus mesh from one source. Scan work needs a connected page session (`scanruler-workflow.md`). It is not a converter: it does not turn an arbitrary mesh or STEP into history automatically.
- **CadQuery:** scripted, reproducible, parametric B-rep with STEP and STL export; good for fully numeric designs, asymmetric or tapered containers and fit-coupon families.
- **OpenSCAD:** fast CSG for simple prismatic, gear or thread-like parts and quick previews; exports meshes, not a B-rep STEP.
- **FreeCAD:** scripting and GUI B-rep modelling and import/export; distinguish headless from GUI capabilities and check the installed version's API before relying on examples.
- **Mesh libraries and slicer tools:** inspection, sectioning and repair of existing triangles, within the resource limits in `SKILL.md`.

Pick by (input representation) × (deliverable) × (what is installed and reachable). Combining is fine, for example numbers measured in one tool feeding a script for printable variants. Keep **one source of truth** for the final geometry and record which it is. Discover what is actually available (installed tools, versions, headless or GUI) instead of assuming.

## 3. Scale the process to the request

- **Tiny edit** (one dimension of a known feature): hash source, identify the feature geometrically, change a sibling copy, re-read the exported file and measure the same quantity, check bounds and other geometry unchanged.
- **Moderate or risky edit** (several features, fit-critical, painted or multi-part, unknown provenance): write a scope (what may change, what must not), add a fit coupon for the critical interface, and use the deliverable gates in `design-and-fit-gates.md`.
- **From scratch or reverse engineering:** parameters first, evidence labelled, coupon before the full part.

## 4. Reversible, scoped editing

1. Never modify the original. Edit a clearly named sibling (`..._rev2`, `..._geometry-only-diagnostic`). Record SHA-256 of the source and each output.
2. State the edit region and invariants before editing (feature, axis, extents; "everything else unchanged").
3. After editing, diff against the original outside the region: bounds, volume, triangle or face counts, component count, transforms. Unexplained change outside the scope means stop and find out.
4. Change one fit variable per iteration when fitting to a physical part.
5. Keep superseded versions rather than overwriting them, and record which version physical feedback refers to.

## 5. Units and coordinate frames

- State units on every number. STL has none: confirm, never assume. 3MF declares a unit. Tools differ (a UI may show inches while its API is millimetres and degrees); trust the tool documentation and replies and convert explicitly.
- Name the frame: local mesh, assembled or instance, build plate, scan frame, part datums. A build-item or component transform (even a Z flip) changes which way "up" is. Compute and report distances in one declared frame and never mix frames in one calculation.
- When someone quotes a dimension, resolve what it is measured from (plane, face, edge, motion axis) before editing, and keep the clarified meaning as a named parameter.

## 6. Exact dimensional features

- Verify a nominal-diameter claim geometrically (least-squares fit of the actual faces; report centre, diameter, span, residual) before choosing faces to move (`stl-feature-audit-and-edit.md`).
- Name parameters after the physical surface (`bore_id`, `tube_od`, `thread_crest_od`, `pitch`).
- Keep the **measured** value, the **nominal/design** value and the **compensated print** value as three different things. Do not round a fitted value to a standard one without evidence (a mating-part or centre-distance test).
- A scan of a worn or shrunk part measures the part, not the designer's number. Label each figure measured (M), partly supported (P) or inferred (I).

## 7. Hand-off

Name the representation delivered (source, STEP, STL, 3MF), the tool and version used, what was verified independently, and what remains unverified (usually physical fit and print behaviour). "Manifold" and "STEP verified" are not "fits".
