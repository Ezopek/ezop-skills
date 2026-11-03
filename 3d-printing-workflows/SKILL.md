---
name: 3d-printing-workflows
description: "Use when slicing, tuning or diagnosing FDM 3D printing: slicer settings and what they really do, materials and calibration, supports and multicolour tool behaviour, G-code or project audits, filament storage and inventory, or operating a networked printer. Not for editing or designing the geometry itself."
compatibility: "Client-neutral guidance. The two bundled analysers need Python 3 (standard library only). Vendor-specific references (OrcaSlicer, Snapmaker U1, Klipper/Moonraker, Spoolman) are optional and version-dependent; none is required for general FDM questions."
metadata:
  scope: "slicing, materials, calibration, printer operation, storage, inventory"
  companion: "cad-modeling-and-reverse-engineering (geometry), optional"
---

# 3D printing workflows

Owns **printing**: slicer settings and semantics, nozzle, flow and material choices, calibration, supports and multicolour behaviour, G-code and 3MF *print* diagnostics, filament storage and inventory, and printer operation.

**Geometry is not here.** CAD design, native STL/STEP/3MF geometry editing, standalone 3MF archive mesh or paint repair (editing the file's own data outside a slicer), creating or positioning new solids, reverse engineering from samples or scans, and fit and printable-design gates belong to a geometry workflow. Colouring or support-painting done in a slicer UI is different: it is print-side tool assignment and stays here. If a skill named `cad-modeling-and-reverse-engineering` is installed, use it; otherwise say what geometry work is needed and keep to the printing side.

## Response style

- Be practical and direct: what to change, what to leave alone, and why. Prefer a rule of thumb plus one or two concrete starting values, clearly labelled as starting values.
- Separate **physical printer facts** from **slicer-specific parameter names**. Labels are often misleading. If the user names a setting, verify what it actually does in the exact slicer, fork and version before answering confidently.
- Put copy-paste deliverables (support text, macros, configuration fragments) in fenced code blocks.

## Standing safeguards

These stay in force for every task; case detail lives in the references.

- **Setup-type changes need a current idle check and separate authorisation.** Before changing a printer or firmware setting, starting a scan, homing, calibrating or running a mesh test, toggling a remote screen, SSH or video stream, or restarting any service or printer: read the live state (for Klipper-based printers, `print_stats`), require a non-printing state, change one thing at a time, read back, and require the service healthy afterwards. Details: `references/printer-control-and-safety.md`.
- **Active or paused jobs are read-only by default.** While a job prints, investigation is read-only (no restart of Klipper, Moonraker, camera or printer; no firmware work). A *paused* job is still a job: no service, firmware or printer restart. The one supported exception is an **explicitly authorised paused-job recovery** (for example the filament-runout recovery in `references/snapmaker-u1-operations.md`) run strictly under its scoped procedure (paused state, named target, its gates and post-checks). It does not make a generic resume, remap or tool change acceptable, and the idle checks above do not forbid it. A restart is a separate, explicit device-control action that needs idle confirmation and the operator's consent.
- **Remote control is control, not monitoring.** Enabling touch injection, a remote screen, SSH, a video stream or any write endpoint needs the operator's authorisation; record the impact first. Do not enable wildcard CORS, and do not attempt credentialed logins unprompted.
- **Slicer semantics are verified, not inferred.** Check what a setting does in the exact slicer, fork and version (docs or source). Prove outcomes with emitted G-code or tool commands, or the real UI after restart: exit code `0`, parseable JSON or a launched app are not evidence. Identify the exact artifact (path, size, modification time, SHA-256, which sibling) before auditing a project; keep sources immutable and test in named copies.
- **Material tuning is measured, not copied.** Starting values are starting values. Calibrate flow, pressure advance and temperature on the user's own profile, change one variable per round, and treat vendor claims and community presets as unverified until corroborated. No universal magic tolerances, and no print, fit or reliability guarantees.
- **Resource containment.** Do not start heavy slicer-fork builds on the user's workstation or a shared service host without approval and explicit CPU, memory and process limits. An out-of-memory kill or lost responsiveness is a hard stop and must be reported (`references/slicer-forks-builds-and-runtime.md`). Dense mesh or voxel analysis limits live in the geometry skill.
- **Tips are candidates until validated.** Never turn a video claim into a standing rule from its title or caption; follow `references/video-and-tip-intake.md`.
- **Secrets stay out of reports.** Redact hosts, passwords, tokens and API keys (including camelCase variants) before writing shareable logs, settings or bundles. Never record real access data for a printer fleet in a skill or report.
- **Do not erase user profiles** as a first response to a rendering or input problem.

## Route by task

| Situation | Open |
|---|---|
| Nozzle swap, line width, flow limits, Orca `Nozzle volume`; verifying a slicer setting; auditing a 3MF project or G-code | `references/slicer-semantics-and-evidence.md` |
| General FDM material, slicer and diagnostic baseline; pressure-advance and flow calibration | `references/fdm-material-and-diagnostics.md` |
| Seam gaps or pits, short-hop retraction, Z-hop, sparse-infill scrape | `references/orca-seam-retraction-and-scrape.md` (analysers: `scripts/`) |
| First-layer colour, PLA/PETG support interfaces, tree supports, support roots, painted-top opacity | `references/orca-support-interfaces-and-first-layer.md` |
| Slicer forks, profile migration, build hosts, Linux runtime and input problems | `references/slicer-forks-builds-and-runtime.md` |
| Automated project and G-code audit reports | `references/orca-audit-tooling.md` |
| Printer purchase, multicolour architectures, prime tower principles | `references/multicolor-printer-architecture.md` |
| Networked printer control, observation, remote services | `references/printer-control-and-safety.md` |
| Snapmaker U1 operations: probes, runout recovery, toolchange wait, bed mesh, Extended firmware, timelapse | `references/snapmaker-u1-operations.md` |
| Snapmaker U1 Wi-Fi, wired fallback, firmware staging | `references/snapmaker-u1-network-and-firmware.md` |
| Snapmaker U1 prime tower, pressure advance, enclosure, package audit | `references/snapmaker-u1-multicolor-tuning.md` |
| Spoolman inventory, OpenRFID or OpenSpool tags | `references/filament-inventory-and-rfid.md` |
| Dry storage, desiccant sizing, monitoring, containers, hygrometer mounts | `references/filament-storage-and-desiccant.md` |
| A video, article or tip claiming a technique | `references/video-and-tip-intake.md` |
| Geometry, standalone 3MF archive edits, new-solid insertion, fit, reverse engineering (not slicer-UI painting) | The geometry skill, if installed |

## Bundled analysers

`scripts/analyze_orca_seam_gcode.py` and `scripts/analyze_orca_sparse_scrape.py` are standard-library, read-only G-code analysers paired with their references. Read the source and `--help` before use, and qualify the actual input and output for the task. They expect OrcaSlicer-style comments (`;TYPE:`, `;Z:`, `;LAYER_CHANGE`). Both require absolute XY positioning (`G90` or the default) and relative extrusion declared with `M83` before any E word; they refuse XYZ motion under `G91`, extrusion under `M82` or before `M83`, and unsupported non-extruding arcs. The sparse analyser also stops with NOT DONE for an input beyond its fixed per-invocation work budget. See `references/orca-audit-tooling.md` for the exact supported scope and its limits.

## Provenance and limits

Most detailed references record dated sessions on specific hardware, firmware and slicer versions. They are starting hypotheses, not live authority: re-check the current printer state, firmware and slicer version, and prefer fresh primary documentation when a version-sensitive detail matters.
