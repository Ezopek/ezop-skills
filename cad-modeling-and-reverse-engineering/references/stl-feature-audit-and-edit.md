# STL feature audit, bore edits, manifold repair, inserts and unions

Dated sessions in the source material are provenance only. Re-verify against the actual files, slicer and version.

## 1. Dimensional-feature audit before editing

When a feature (bore, sleeve, shaft or other circular part) is identified by nominal diameter, verify it geometrically before selecting or changing faces.

1. Preserve the original and hash it. Inspect bounds, connectivity, watertightness and orthographic projections. A silhouette can hide a bore behind another solid, so it is orientation evidence only.
2. For an axis-aligned cylindrical candidate, filter lateral faces whose normals are perpendicular to the axis, split face-adjacent groups, and least-squares fit a circle to each group's transverse vertices.
3. Report fitted centre, inner and adjacent outer diameters, axial span, residual, and whether the bore belongs to the intended sleeve rather than being another matching circle. This prevents a "first 2.1 mm feature" guess.
4. For a functional retention bore (for example filament grip), do not pick the new nominal diameter from the part it holds alone. Grip, dimensional variation, material, print orientation, line width and hole compensation all matter. Ask for the target fit or label the first coupon provisional. Create only a sibling and validate manifoldness, winding, dimensions and slicer acceptance.

## 2. Mutating blind bores and perforations

- For a clean, axis-aligned circular bore whose lateral wall is a complete shared vertex ring, change the diameter by moving that wall's radial vertices around the fitted axis. Those shared vertices also belong to the rim face and, for a blind bore, the bottom cap, so moving them necessarily moves the neighbouring rim and cap boundaries (their triangle connectivity is unchanged, their geometry is not). That connected transition is part of the requested diameter change, not a separate edit: admit it, and keep everything outside that admitted set unchanged (the outer shell, other features, and anything the operator told you to protect). Do not run a broad Boolean for a simple cylindrical wall.
- If the ring is also shared with a separately protected or unrelated feature (for example a chamfer or thread you were told to keep), that feature cannot change silently: stop and ask instead of moving it along.
- Re-read the exported file and remeasure the target diameter, the wall, rim and cap closure, and the original bore depth; prove unchanged external bounds and vertices outside that admitted set, one watertight component and consistent winding. For a blind cavity also confirm that horizontal cap triangles at the inner end still cover the axis; a silhouette or a manifold result alone does not prove the bore stays closed.
- Desiccant bins: determine the smallest actual bead before choosing an aperture. Keep the minimum slot width below that bead size with a print-tolerance margin, but keep airflow with a longer rounded slot instead of shrinking every perforation to a tiny circle. A starting point for roughly 2.5 mm beads on a 0.4 mm nozzle was a horizontal rounded 1.8 × 2.8 mm slot; treat this as a starting point to test, not a bead specification.
- To convert round holes to slots: union slightly overlapping fillers into the old holes, then subtract new capsule cutters. End fillers flush with the original wall faces, because overlong fillers change the outside bounds. Count every replaced opening and inspect both opposing perforated walls after export.

## 3. Binary STL manifold repair (T-junctions)

Use when a slicer reports a few open edges on an otherwise plausible binary STL, especially boundary loops that are zero-area and collinear.

Diagnosis:
1. Parse the binary STL deterministically: triangle count at byte 80, exact size `84 + 50*n`, finite vertices.
2. Count undirected edge multiplicities using the exact stored float coordinates. Closed surface: every edge twice; one means open; more than two means non-manifold overlap.
3. Record each bad edge's incident facet and directed orientation. Build connected components from multiplicity-1 edges and inspect coordinates and bounds.
4. A three-edge component with three distinct collinear vertices is usually a **T-junction**, not a missing triangle. Do not fill it; a zero-area facet only hides the edge count and creates invalid geometry.

Repair: for a long boundary edge `A→B` whose neighbouring surface already has `M` (exactly on `AB`) as a vertex and runs that edge the other way as `B→M` and `M→A`, replace triangle `(A,B,C)` with `(A,M,C)` and `(M,B,C)`. The new `A→M` and `M→B` edges then pair oppositely with the neighbour's `M→A` and `B→M`; if they were the same direction as a neighbour's edges, the winding is inconsistent. Keep winding consistent with the rest of the surface, recompute normals from the cross product, and reject zero-area output. Write a sibling atomically (temporary file, flush, rename) and keep the original until the repaired copy is independently verified.

Verification gate (deterministic audit and the slicer's own parser):
- exact binary size and finite coordinates; zero degenerate facets;
- every undirected edge multiplicity is 2, paired edges run opposite directions;
- unchanged bounding box and signed volume within float tolerance;
- the slicer's information command reports manifold with no open edges (for example OrcaSlicer's `--info`);
- the rendered model looks plausible before upload or printing.

More than one part is not itself a manifold error: separate closed shells can be intentional.

## 4. Functional inserts and STL unions

For a supplied mechanical insert (socket, snap-fit interface, bearing seat, threaded feature, connector):

1. Load insert and host independently. Record bounds, components, watertightness and volume.
2. Solve the rigid transform between the supplied insert and its instance in the host before designing a repair. Compare exact bounds and component geometry; do not infer a functional feature from an approximate cylinder or bounding box.
3. Treat the insert's internal profile and outer envelope as **immutable** unless the operator explicitly permits a named interface surface.
4. Classify the operation. *Structural fuse:* volumes already overlap at an authorised interface; union the exact solids without adding material around the functional envelope. *Gap filling:* material must occupy a clearance around the insert; this changes its envelope and needs explicit authorisation or a revised host.
5. If only a top or mounting face is authorised, attach only there. Do not substitute an exterior collar, a buttress or a bore fill.

Safe Boolean completion: keep only genuine solids and remove isolated degenerate triangles separately from the geometry operation. Use a robust mesh Boolean engine and union the host with the **unaltered** insert solids. Validate one watertight component, consistent winding, unchanged functional bounds and profile, and no new downward-facing shelves. Inspect a cross-section through the functional axis before calling the result printable. Keep rejected exports separately labelled non-printable; never overwrite the original or a validated candidate. A self-supporting slope does not authorise an insert modification: check fit preservation first, then overhangs in the intended print orientation.

## 5. Support-free repair of an undersized or disconnected insert

1. Split the source into connected solids; measure the insert, the clearance, the centreline and every bore that must stay functional. Keep the source immutable.
2. Fill a radial gap with a **bed-rooted** annular or solid buttress that rises from the print bed into the receiving body, avoiding a floating downward shelf. Preserve a central bore unless closing it is intended.
3. Make the exposed transition conservative. State both the angle above horizontal and the equivalent overhang from vertical; slicer and CAD conventions use both. Never say "30° support-free" without naming the reference axis.
4. Union the original solids and connector, remove degenerate fragments, require one watertight, consistently wound component.
5. Inspect a vertical section and examine downward faces above the bed. Do not infer support-free printability from watertightness. Measure and report any pre-existing small bridge span.
6. Deliver only the new output file, read back by size and SHA-256, and give the intended print orientation and support setting.

Pitfalls: preserve bores inside working cylindrical inserts; a watertight union can keep internal downward faces a slicer must bridge, so inspect the produced mesh and not just the Boolean result.
