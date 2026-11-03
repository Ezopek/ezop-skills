# Logo artwork to multicolour model geometry

Use when a logo must become an embedded, embossed or separate-colour body in STL or 3MF, especially when only a small raster exists.

## 1. Source discovery

1. Prefer an authoritative vector source (SVG, AI, EPS, vector PDF). Ask the owner for it.
2. Inspect the original web page's DOM and referenced assets before guessing filenames. Record the exact asset URL, format, pixel size and alpha, and whether the page uses inline SVG. Probe only a short list of plausible SVG paths; do not claim an SVG exists without fetching it.
3. Treat a reconstruction from a web raster as provisional until compared with the owner's vector. Keep a faithful reconstruction separate from any print-simplified variant.

## 2. Raster-to-vector

1. Preserve the downloaded original unchanged. Inspect the alpha channel: a transparent logo can look as if it contains gray bars when transparency renders badly; composite onto white before deciding what is artwork.
2. Upscale the alpha mask (Lanczos), threshold to a clean binary silhouette, remove speckles, and trace with a spline-capable tracer (for example VTracer with binary colour mode, stacked hierarchy, spline mode, moderate speckle filtering, enough corner sensitivity for stylised lettering).
3. The SVG stays path-only: no embedded raster, no font dependency. Add `viewBox`, `preserveAspectRatio`, `<title>` and a note that it is reconstructed. Give it a practical default physical size while keeping the aspect ratio.
4. Compare an enlarged raster against an SVG render, not merely the XML. Check noses and tails, cusps, counters, narrow strokes and small subtitle text where low-resolution rasters create blobs.

## 3. Artwork and typography are separate problems

- Trace organic artwork independently. Auto-tracing is a scaffold for silhouettes; traced text keeps tiny contour bumps and a wobbly baseline.
- Isolate each text line by connected components when nearby artwork overlaps its bounding rectangle. Crop each line separately, black on white, with padding, enlarged with a good resampler (this eases matching, it does not create detail).
- Run more than one font matcher (several web services exist) and treat results as candidates: render the exact words and compare glyph by glyph (weight, slant, spacing, counters, terminals). Low-resolution metrics only shortlist; a tiny sans tagline can look serifed after thresholding, so inspect smooth enlargements and the full-logo context.
- Check for customised glyphs and intentional cuts, gaps or slant. A detached bar may be a stylised letter, not noise; do not delete detached strokes blindly.
- Rebuild text from the chosen font (adjust tracking, shear, scale), repair intentional custom glyphs and convert to true glyph outlines (for example with FontTools) rather than tracing newly rendered text. Fit runs to measured bounds. Verify the font's licence with the logo owner even when a visually matching font exists.
- Preserve each path's `transform` as well as its `d` data; copying only path data displaces the artwork.

## 4. Print-oriented variant

At the intended physical size check minimum stroke and counter widths. Remove details below the nozzle and line-width capability, thicken fragile strokes, close tiny gaps, or omit a tagline that is unprintable at the target size. Keep the fidelity-oriented SVG untouched beside the print-ready one.

## 5. Slicer SVG-emboss importers that require a single path

Some importers reject an SVG with several `<path>` elements, even inside one `<g>`, because the check concerns XML structure, not visual connectivity. A single compound `<path>` can hold many disconnected subpaths and holes.

1. Preserve the source and write a named sibling (for example `*-single-path.svg`).
2. Inventory `<path>`, `<text>`, `<use>`, primitives, groups, clipping, masks and per-element transforms. Convert text, primitives and `use` references to paths; do not discard them.
3. **Bake each path's transform into its coordinates before combining path data.** Concatenating `d` strings while dropping `translate`, `scale`, `rotate` or matrix silently relocates or distorts artwork.
4. Combine into exactly one `<path>` only when every path's effective fill rule (its own `fill-rule` or the inherited one) matches AND the compound fill semantics are preserved: concatenation can change which regions are filled where paths overlap or cancel each other, even under the same rule. If the effective rules differ, or overlap or cancellation could change the result, do not concatenate. Use a qualified, semantics-preserving geometry conversion that resolves the shapes first, or fail closed and keep the source, and compare renders either way. Keep `viewBox`, useful physical size and fill colour. Remove empty groups only after flattening. When flattening a group or an inherited style, apply the effective (resolved) fill rule to the output compound path by copying it as an explicit attribute or style on that path (for example an inherited `evenodd`), and fail closed if it cannot be preserved. With the actual selected conversion tool, run a qualification render with counters that inherit `evenodd` as a control before trusting it; this is a workflow instruction, not a shipped converter. Primary reference: [SVG 2 painting, `fill-rule`](https://www.w3.org/TR/SVG2/painting.html#FillRuleProperty) (initial value `nonzero`, inherited, and `nonzero` and `evenodd` give different interiors).
5. Verify the XML parses, path count is 1, no unsupported visual elements or transforms remain, and a before and after render at identical size shows no moved components, filled counters or missing strokes (antialiasing-only differences are fine).
6. A constrained fallback converter is valid only when the source inventory proves its supported command and transform set is complete (for example absolute `M/L/C/Z` plus `translate()`); fail closed on anything else. Prefer a mature SVG geometry tool for arbitrary curves and matrices.

## 6. Verification gate and 3D integration

- Parse the SVG as XML; render at a large fixed size; compare with the source for shape, counters, smoothness and missing parts; confirm vector paths only and a transparent background; deliver both SVG and rendered preview; label it a first reconstruction when no authoritative vector exists.
- Before the 3D conversion, import the SVG into the intended CAD and check that the closed profiles and holes arrive intact; this is a geometry gate only, with no new software dependency and no qualification claim for any tool.
- In CAD turn each colour region into a separate solid. Prefer a recessed inlay of roughly 0.4–0.8 mm or an emboss of roughly 0.4–1.0 mm for typical 0.2 mm layers (starting points to test). Keep bodies separate in 3MF so the slicer assigns tools or colours deterministically. STL cannot retain multi-body colour assignments; keep the 3MF.
- Test-slice the final multibody 3MF.
