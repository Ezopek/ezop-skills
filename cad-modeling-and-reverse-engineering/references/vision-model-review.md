# Vision-model and segmentation assistance for paint review

Optional. Use only if the operator wants a vision model or a segmentation model in the paint-review loop (see `paint-label-repair.md`). The loop works without them. This file records how to keep them from becoming the authority.

## 1. Responsibilities

- **Geometry code and solver** own mutations.
- **Segmentation models** (SAM2-style, GeoSAM2, similar) may propose regions from a point, box or 2D mask. Treat output as a proposal; map and verify its face labels against the original face order, compare to marker constraints, refine with graph cut or components, and require the same coverage and diff gates.
- **Vision-language models** only audit or localise visually. They never invent XYZ or face IDs and never commit labels.
- **A human** resolves abstentions through a compact review board.

## 2. Grounding

Never ask a model for 3D coordinates or triangle IDs. Use either:
- a **stable region ID**: code computes candidate face sets and overlays labels like `A1`, `B7` on every view; the model returns only the visible ID and a verdict; or
- a **screen-space point or polygon** on one named view, which code looks up in a machine-only face-ID buffer rendered with identical camera, culling, depth and resolution.

For meshes above 65,535 faces store at least 24-bit IDs (or a uint32 buffer). Keep ID, depth and normal buffers machine-readable; show the model ordinary shaded and diff images with visible labels.

## 3. Exact face-ID rendering

Beauty screenshots are not evidence of face identity (interpolation, anti-aliasing, lighting, colour management, compositor, encoding). For a VTK or PyVista renderer whose polydata has one triangle cell per mesh face in unchanged order:
1. Disable multisampling for the ID pass and use the hardware selector with cell field association over the inclusive area `(0, 0, width-1, height-1)`.
2. Capture both the actor pass and the low-24-bit cell ID; copy each raw buffer before clearing, never retain the pointer; decode little-endian `R | G<<8 | B<<16`.
3. Actor pass `0` is background; otherwise `render_face_id = vtk_cell_id + 1`, reserving zero for background. Validate the buffer wrapper's pointer syntax and a nonzero address, copy exactly `width*height*3` bytes, fail closed on missing passes, bad dimensions, capture failure, face-count ceiling or IDs above the cell count, and clear buffers in `finally`.
4. Acceptance fixture before production use: a mesh with the real cell count, most cells outside the camera, sentinels around encoding boundaries (`0`, `65534`, `65535`, the real maximum). Require exact sentinel round-trip, background zero, three identical hashes on a pinned backend, no Y-axis flip, interior pixels matching an independent picker or CPU oracle, unchanged order. Do not claim identity across GPUs, drivers, major versions or rasterisers; record backend, version and camera.
5. Persist exact uint32 buffers, camera and backend manifest, per-view SHA-256, threshold sweep, synthetic acceptance result, the actual production renderer wrapper and its tests with the exact source or commit reference used for qualification (a reference to archive; this does not claim a shipped renderer or a demonstrated qualification), and the list of faces never visible.

Prefer off-screen renderers when the task does not need the operator's live UI.

**GUI verification without surprises.** Native slicer GUI validation is a separate, privacy-sensitive gate. Announce before any operation that may show a screen-sharing or capture indicator, even when the intended scope is one application. Capturing the operator's real desktop or a real window must wait for the operator's approval after that announcement (the entry requires both a prior warning and approval); an announcement alone is not approval. This does not apply to an isolated virtual display or an offscreen synthetic render. Inspect window titles and state first, and do not close an existing profile or settings editor that may hold unsaved user changes. Prefer a fresh isolated virtual display with a separate application instance; if single-instance forwarding prevents isolation, do not force the user's live session. Prefer per-window capture over monitor or root-window capture and never capture a whole multi-monitor desktop merely to find a window. A black or compositor-blocked capture is `blocked`, not permission to escalate silently. If a clean isolated GUI gate cannot be obtained, record it as pending and ask the user to open the file manually instead of claiming success.

## 4. Coverage proof

Do not use a universal per-triangle pixel threshold. On a 929,870-face mesh at 1024² most correct triangles covered 1–4 pixels, so a blanket 12-pixel rule marked nearly everything uncovered. Instead:
- exact `>=1` pixel presence establishes visibility; require at least two independent views where geometry permits (three for thin or self-occluding parts);
- judge projected area at deterministic region or component level;
- classify zero-view faces explicitly as topology-inherited or structurally occluded, with trusted-core and marker lineage; one-view faces are weak proof;
- use adaptive component cameras (head-on along the mean normal and two ±30° variants, tight close-up filling roughly 40–60 % of the frame) before accepting occlusion.

Never relabel hidden faces as visually proven to turn a gate green, and never let a model approve an invisible face. Per face persist the views where it is front-visible and the pixel counts.

Canonical rig for vessel-like objects (an upper bound, not one prompt): 8 azimuths at +20°, 8 at +55°, 4 at −15°, top and bottom, orthographic. Send only the smallest relevant subset per region.

## 5. Atomic review cards

One region per call, at most: a geometry or normal close-up, the final coloured close-up, a before, after and diff card. The prompt states the semantic rule, defines the diff colours and the hue→class mapping, names the one region, and permits `uncertain`, which is the abstention.

Response schema (one JSON object per call):

```json
{
  "schema_version": "boundary-critic/1",
  "region_id": "existing stable ID",
  "status": "clean | defect | uncertain",
  "observed_object": "an object named in the semantic contract | unclear",
  "defects": [
    {
      "type": "A_into_B | B_into_A | missing_coverage | jagged_seam | ambiguous_geometry",
      "panel_id": "existing panel ID",
      "normalized_points": [[0.0, 0.0]],
      "confidence": 0.0,
      "visible_evidence": "short factual description"
    }
  ],
  "views_consistent": true,
  "next_view": "none | wider_context | closer | tangent | underside | opposite | geometry_only | selective_wireframe | label_only | slicer_preview",
  "reason": "short rationale tied to visible evidence"
}
```

The same schema appears in `../templates/boundary-critic-prompt.md`; a repository test fails if the two diverge. One verdict vocabulary everywhere (cards, template, qualification gate, validator): `status` is `clean`, `defect` or `uncertain`. `uncertain` is the conservative abstention and may request exactly one `next_view` (for example a closer or opposite view); there is no separate accept, reject or abstain word. `clean` requires both label directions to have been checked and carries no defects; `defect` carries at least one concrete defect. `clean` also requires `views_consistent` true and `next_view` `none`; `views_consistent` false means `uncertain`; a `defect` may still request another view, and `uncertain` may carry possible defects. Point coordinates are normalised to the named panel and stay inside `[0,1]`; two opposite corners of the panel (either diagonal, in any order, with or without other points) are a whole-panel placeholder, not localisation; the model never supplies face IDs or XYZ. Use constrained decoding where available, one repair retry on a parse failure, and if that also fails record `uncertain` and treat the answer as a gate failure, not an approval. No production response validator is supplied by this package; the repository fixture checks this documented contract only. Before using any model response, the consuming implementation must supply and qualify a validator that checks: exactly these keys, known `region_id` and `panel_id`, values inside the vocabularies above, the cross-field rules stated above (`clean` carries no defects, an empty `defects` list; `defect` carries at least one concrete defect; `clean` also requires `views_consistent` true and `next_view` `none`; `views_consistent` false means `uncertain`), and the rules in section 6.

## 6. Qualification before a model can influence anything

Raw confidence is not evidence. Qualify the exact model, quantisation, context, offload, prompt and output validator before generating or applying proposals. The fixed gate must include: known defects in **both** label directions, known-clean traps, a **display-hue trap** (a vivid debug colour that represents a semantic class), and deliberately occluded or ambiguous regions that must return `uncertain`. Score defect recall, false-positive rate, abstention, localisation and semantic consistency separately.

Hard failures: invalid JSON or unknown IDs; coordinates outside the image or crop; whole-crop placeholder boxes; `clean` carrying a spill direction; direction, object, rationale and semantic contract disagreeing; semantic-role reversal; literal-hue confusion; overcalling clean or ambiguous regions as defects; templated all-OK answers. A model that finds every obvious defect but overcalls clean or ambiguous regions is **not qualified**, because false positives cause destructive edits.

Rules:
- Prompt refinement belongs to qualification. After fixing the prompt and golden set, do not weaken expectations or reinterpret wrong answers.
- Compute the expected class deterministically from the semantic contract; do not let the model redefine it. State the hue→class mapping in every prompt.
- On failure, stop before any face mutation, keep outputs as hard negatives, unload the model and report the gate failure. Trying a different model or a remote vision service is a **new explicit decision** by the operator, not a silent fallback.
- If the same model fails to load because context, GPU offload and the vision projector exceed memory, one bounded retry of the **same** model with smaller sufficient context and partial offload is a configuration correction; record it. This applies only when the failure was a controlled load failure WITHOUT an out-of-memory kill and WITHOUT elevated memory pressure, there is positive read-only evidence of safe memory health and conditions (the absence of a warning is not evidence), and the retry keeps a context that is still sufficient for the task and uses bounded partial offload. Unknown or missing evidence is not permission to retry. If a kill or elevated pressure is observed, stop, cancel the remaining geometry work, report it, and do not retry without the operator's explicit approval (the entry's hard safeguard). This reference adds no monitor or service, and nothing here induces memory pressure or loads a model.
- A model that fails localisation may remain a coarse region proposer only if that narrower role is explicit and every mutation still needs deterministic projection plus human or geometric evidence.
- Observed in tested sessions (not permanent claims; re-run after any model, runtime or prompt change): small and mid-size local vision models produced valid-looking JSON with 0.95–1.0 confidence while missing the mesh, inverting the target rule, confusing overlay colours and failing to abstain; larger size did not fix precision or calibration.
- Remote vision may serve as an optional final independent sanity review after the local and deterministic gates pass. It cannot rescue a failed local loop, write or expand face IDs, or override a deterministic defect. Preserve disagreement explicitly.
- For a final pass, run the critic on fresh native-resolution renders including one target-slicer viewport. A batch of byte-identical templated "OK" results marks that pass unreliable; fall back to native or human inspection.
- Verify the model server separately from the launcher: a model-runtime CLI can exit successfully while reporting that the server is not running, so check the endpoint itself. That check is a read-only readiness check of the endpoint, never a start. If the endpoint is unavailable or the check times out, leave the model and GUI validation pending and report that. A timeout grants no authority: starting or restarting a server or an application, including inside an operator's existing desktop session, is an operator-environment action, not something to attempt silently. It is not part of this geometry reference and belongs to a separately scoped environment or runtime task, to be done only if the operator has explicitly approved that named action there; otherwise leave the verification pending and ask, as in the GUI-verification gate above. Starting the model server and validating the viewer are different actions, and approval for one does not cover the other. This reference starts nothing itself and defines no approval protocol.
- Unload local models after the audit unless the operator wants them resident. Keep API tokens out of prompts, reports and command lines; read them from an environment variable or a file the operator names. Any HTTP client for a local endpoint must be reviewed and configured with the operator's chosen base URL.

## 7. Stop rules

Stop automatic iterations when two full audit rounds produce no accepted new findings, only abstentions remain, the same region flips twice (freeze and escalate), changed area falls below the useful threshold, the iteration or area budget is exhausted, golden or trap reliability falls below threshold, or a structural, seed or coverage gate fails. Give humans only stable IDs, close-ups, direction-coloured diffs and one explicit question per contested region.

## 8. Related methods

- GeoSAM2 (CVPR 2026; Apache-2.0): marker-driven 3D part selection from 12 rendered views plus one click or mask; per-face labels; documented limits on thin or wire-like geometry. A good 2D mask and the right face count do not prove a correct 3D lift; in one test a good single-view mask lifted to many components with opposite-side false positives. Keep the geometry solver the final authority. <https://github.com/VAST-AI-Research/GeoSAM2>
- SAM2 (Apache-2.0): <https://github.com/facebookresearch/sam2>. SAMesh (reference baseline; check its licence before depending on it): <https://github.com/gtangg12/samesh>. SATR (MIT; zero-shot semantic segmentation): <https://github.com/Samir55/SATR>.
- Trusted-core component salvage: start from a trusted correctly painted core, collect adjacent opposite-label faces inside a local box or geodesic budget, split by adjacency and dihedral angle, render each as a diff from several views, render candidate-only topology cards for occluded contact surfaces, reject a component that touches a contradictory marker, accept only wholly semantic components and abstain on mixed or invisible ones.
- Not suited as the core: image-to-3D generators (they regenerate geometry and lose face IDs) and generative texturing (continuous textures, not discrete material labels).
