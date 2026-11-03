# Printable design, tolerance and deliverable gates

Scale the gates to the deliverable. A one-dimension STL tweak needs the "Print-ready mesh" row only; do not impose the whole table.

## 1. Design for the process (starting points, not standards)

- Orient for the load path: layer interfaces are the weak direction, so avoid critical tensile or bending load across layers when another orientation is feasible.
- Design supports away before adding them: orientation, splitting, or a 45°-class chamfer. Validate any more aggressive overhang or bridge with the actual material and printer.
- At a base that touches the plate, a chamfer gives a predictable printable slope where a bottom fillet would start with a difficult overhang.
- FDM favours simple, blocky functional forms. Decorative "weight-saving" cut-outs can reduce stiffness and add slow perimeters without saving meaningful material once infill is counted.
- Print the edited mating region or critical feature as a coupon before a large assembly. Calibrate tolerance, hole size and clearance in the **target material and orientation**. A quoted clearance (for example a roughly 0.2 mm moving-fit starting heuristic) is a hypothesis, not a reusable standard.
- Horizontal round holes have an unsupported upper arc. For a larger precise hole use a teardrop or roofed profile where function permits, or deliberately designed thin sacrificial bridges. For a precision hole consider undersizing and reaming, then verify tolerance and surface.
- Prefer ordinary hardware where it makes the part simpler and more reliable (bolts, nuts, dowels, heat-set inserts). Design nut pockets for the actual nut and insertion direction. Print-in-place flexures and captured mechanisms need their own clearance, fatigue and material test, not visual plausibility.
- Multicolour and text: put a colour boundary at few layer transitions when possible (side-wall colour or text can cost many swaps, time and purge waste). For small high-contrast text, test the inverse construction (printed field, glyph as gap), and confirm the actual line-width result in the slicer preview.

These heuristics come from practitioner material, for example the public video "Everything I know about 3D Printing" (<https://www.youtube.com/watch?v=gPW_mitgosw>). They do not replace fit coupons, strength calculations or slicer preview; printer, material and a controlled test override them.

Receiving-object geometry: `fit-clearance-and-retention.md`. Threaded or sealing parts, gears: `physical-reverse-engineering.md`. Slicer settings, materials, supports and printer behaviour belong to a printing workflow; hand over orientation and support expectations explicitly.

## 2. Tolerance and physical measurement

- Measure the real object with the right instrument (calipers, not a ruler, for fits), repeat, note flexible or worn surfaces and record uncertainty next to each value. Prefer several samples.
- The CAD number is nominal. **Compensation for the print process is a separate, measured quantity** (hole shrink, elephant foot, material, nozzle). Do not bake a remembered offset into the geometry without a coupon that supports it.
- Start unknown fits with a coupon family (for example nominal, loose, extra loose) covering only the critical interface. Change one dimension per iteration and log which printed revision each observation refers to.
- A successful PLA fit coupon is not a service qualification: heat, creep, water, pressure and load need their own tests and material choice.

## 3. Functional correctness is not manifoldness

A watertight, positive-volume mesh of the intended components can still be useless (for a part meant to be one solid, that means one component). For anything that inserts, snaps, threads, seals or retains, additionally prove:

1. **Insertion path:** clear width, height and depth along the whole path, including every lip, latch and shelf, against the *exact target mesh or object*, not its bounding box.
2. **Seated state and retention:** the object is held in every orientation it will see; a guide or a gravity shelf is not retention. State any deliberately open direction as a limit.
3. **Printability of the feature itself:** thin features may be manifold yet slice into ribbons; check the slicer layer preview.
4. **Declared support-free or orientation requirements** as an explicit geometry gate.

## 4. Gates by deliverable

| Deliverable | Independent readback (re-open the exported file from disk, ideally with a different reader than the producer) | Slicer gate | Other |
|---|---|---|---|
| Print-ready STL or 3MF (single material) | Units, scale and bounds as intended; intended component count (one for a single part), each printed part a closed volume; watertight; consistent winding; positive volume; requested dimension re-measured on the *export* | Imports and slices without repair prompts; layer preview shows thin features solid | Hash source and output |
| Parametric source plus exports | Re-run the generator from its parameters and compare; effective parameters recorded | As above for each exported mesh | Package source, parameters and tests or validator with the deliverable |
| STEP (exact geometry for another CAD) | Re-import and verify: solids closed with no free edges and the expected solid count (one for a single part; the specified count and per-solid validity for assemblies and multi-body; intentionally open reference surfaces are checked as surfaces, not rejected); volume and bounds against source | n/a | History is not included |
| Painted or multi-part project 3MF | Paint-token counts, part count, transforms and metadata values: `painted-3mf-editing.md` | Embedded-settings slice; tool commands in G-code checked | Never claim colour-preserving without these |
| Fit prototype for a physical interface | Dimensions of the exported coupon | Layer preview of the critical feature | Physical result recorded separately from CAD assumptions |
| Public release | Export-readback tests, preview cleanup | Slicer or CI check as needed | Licence, attribution, disclosure: `parametric-prototyping-and-release.md` |

Status words: *structurally validated* when only file and mesh checks ran; *slicer-accepted* only after a real import and slice; *fit-verified* only after a physical test.

## 5. Safe analysis

Use sparse sections, sampled surface queries and bounded-resolution previews. Estimate grid or voxel counts before any dense containment, voxel or Boolean workload and stay inside the resource safeguards in `SKILL.md`.
