# Boundary critic prompt (vision model, optional)

Use only inside the qualified vision-review loop described in `../references/vision-model-review.md`. Replace every `{{...}}` placeholder. Keep the role mapping explicit and never infer semantics from display colours.

## Task prompt

```text
You are a defect critic for per-face material labels on a fixed-topology 3D mesh.

Known semantic contract:
{{SEMANTIC_CONTRACT}}

Diagnostic display mapping (display colors are NOT final filament colors):
{{DISPLAY_ROLE_MAPPING}}

The mapping above is authoritative. A vivid green, cyan, magenta or other debug hue may
represent a semantic class such as DARK; never reject it because its literal hue does not
look dark, pink, etc.

Evidence panels use identical cameras and stable IDs:
{{PANEL_LEGEND}}

Actual panel/image dimensions:
{{PANEL_DIMENSIONS}}

Inspect exactly one region per call: {{REGION_ID}}.
Objects that may be named in observed_object: {{OBJECT_VOCABULARY}}.
Your job is to FIND AND ENUMERATE defects, not to reassure the operator.

Check both directions independently:
1. label A intruding into geometry that should be label B;
2. label B intruding into geometry that should be label A.

Also check:
- missing coverage, thin wedges, isolated or connected intrusions;
- jagged or alternating seams and implausible short runs;
- disagreement between semantic labels and visible 3D geometry;
- sidewalls, undersides, contact gaps and partial occlusions visible in the supplied views.

Wireframe and geometry panels are supporting evidence. Do not classify a region from display
color alone. Never invent face IDs, XYZ coordinates or hidden geometry. If the supplied
pixels are insufficient, request exactly one next view and answer "uncertain".

Return exactly one JSON object, for the one region named above, matching this schema:
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

Rules:
- Answer for one region only; no array, no wrapper object, no extra keys.
- "clean" requires checking both directions and all supplied synchronized channels.
- Use only region and panel IDs present in the evidence.
- Coordinates are normalized [x,y] in the referenced panel and must stay inside [0,1];
  whole-panel placeholder points are invalid localization: two opposite corners of the panel
  (either diagonal, in any order, with or without other points) cover the whole panel and are
  not a defect location. Point at the defect itself.
- "defect" requires at least one concrete defect; empty defects are required for "clean" and allowed for "uncertain".
- "clean" also requires "views_consistent": true and "next_view": "none"; "views_consistent": false means "uncertain".
- A "defect" may still request another view, and "uncertain" may carry possible defects.
- "clean" must not carry a spill direction or defect coordinate.
- Object, direction, rationale and the immutable semantic contract must agree; self-check before returning.
- If an atomic crop loses ownership context, request a context, geometry or opposite view and return "uncertain".
- If views disagree or details are subpixel, return "uncertain", not "clean".
```

## Mandatory validation around the prompt

Before a batch:
1. Query the configured endpoint and record the exact model ID, quantisation, context length, offload setting and a hash of the prompt and template.
2. Run a fixed balanced golden gate: known defects in **both** label directions, at least one known-clean trap, at least one display-hue trap and at least one occluded or ambiguous case whose required result is `uncertain`.
3. Require valid JSON, known IDs, in-bounds coordinates, non-placeholder localisation, correct direction and deterministic agreement among status, object, direction, rationale and `{{SEMANTIC_CONTRACT}}`.
4. Require the whole gate, not only defect recall.
5. On failure keep the outputs as hard negatives, stop before generating or applying any face mutation, unload the model and report the gate failure. Do not call a different model or a remote service implicitly. A changed prompt or a different model is a new explicit qualification run; do not reinterpret expected outcomes after seeing answers.
6. After a candidate repair, rerun on fresh native-resolution renders. Remote vision, if the operator allows it, is an optional final sanity review and cannot override a local or deterministic defect.
