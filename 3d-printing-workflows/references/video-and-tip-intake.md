# Video, article and tip intake

Use when someone shares a video, post, article or forum tip that claims a printing **or** modelling technique and asks whether it is true, useful or worth adopting. This is the single assessment-to-adoption procedure for both the printing and the geometry skills. It adds no watcher, scheduler or downloader.

## Base rules

- When a source is useful, retrieve timestamped notes first and extract its durable rules into the **narrowest relevant reference** in your own notes or skills. Do not store a generic summary as operating knowledge.
- Record provenance in the user's chosen knowledge system: source URL, title, intake date, review state, and which reference or project artifact absorbed the knowledge. Treat that record as a discovery index, not a validated procedure. Do not copy the same provenance into two places.
- Do not promote advice from a title, description or inaccessible transcript. Cross-check against current primary documentation, the exact printer, slicer and version, and physical validation when applicable. Keep source timestamps beside the normalised rule.

## Procedure

1. **Retrieve with the tools you have** (fetching, transcription, frames at decisive timestamps, original resolution where text matters). Do not build another downloader. Report what you actually inspected (transcript plus sampled frames, browser playback, or only a caption) and imply nothing more.
2. **State the claim as a testable sentence:** what changes, expected effect and size, the mechanism offered, and the stated conditions (printer, firmware, slicer and version, material, nozzle, geometry, environment) with the timestamp. Missing conditions are recorded as unknown, not assumed to match the operator's setup.
3. **Check existing coverage first** in your skills, references and notes. Already covered, or only a rewording of an adopted rule: reject as non-incremental and say where it is handled. A claim that *contradicts* an adopted rule is not rejected for that reason, since existing guidance can be stale: investigate (steps 4–5) and only if the evidence supports it correct or supersede just the affected rule and record why. Reject as false only if the claim contradicts current primary documentation or basic physics, or the demonstration does not show what the narrator says, and state the reason. An unsupported claim is unverified, not proven false.
4. **Check current primary sources** for decision-changing facts only: slicer and firmware documentation and release notes for the exact version, vendor pages, source code, standards or datasheets. Bind each statement to the version and date read. Marketing and review claims are not primary evidence.
5. **Grade the evidence you have** and name it in the verdict:
   - *Plausible experiment:* claim only, credible mechanism, a test designed but not run.
   - *Documented recommendation:* a current primary source states it for the relevant context (cite document and version or date).
   - *Computational reproduction:* re-slice, G-code or geometry analysis, or calculation reproduces the mechanism on the operator's files; no physical result yet.
   - *Physical validation:* a controlled print or test on the operator's setup, measured, one variable changed.
6. **Decide:** reject, park as a candidate (unadopted knowledge with its conditions; not a task, reminder or monitor), run a bounded experiment, or adopt. Match the evidence to the claimed outcome. Computational validation can support adopting a rule whose claim is itself geometric, algorithmic or about file operations, scoped to the conditions tested. It does **not** establish physical strength or fit, printer or material performance, or universal settings: for those, require documentation for the exact context or a physical test on the operator's setup. Computational reproduction alone leaves a conditional candidate. A single success does not make a universal rule.
7. **Experiments:** one variable at a time, a baseline, sibling files (never the source), a predefined success measure, and readback of the actual slicer output or measured part. Anything that touches a printer needs explicit operator authorisation and the idle and state checks in `printer-control-and-safety.md`.

## Where the result lives

| Content | Home |
|---|---|
| Actionable, reusable procedure or rule | The narrowest relevant reference, **with its conditions in the rule text** (printer, material, version), in a section labelled *Candidate* or *Adopted* |
| Evidence, rationale, source URL and title, intake date, timestamps, review state, pointer to the reference | The operator's notes or knowledge base (a discovery index, not a procedure) |
| Raw video, audio, frames, transcripts, project files and project-specific results | The research or project workspace; the notes hold only a pointer |

Keep candidate tips visibly separate from adopted rules: never write a candidate in the imperative voice of an adopted rule, and do not universalise printer-, material- or version-specific advice. Updating an adopted reference is a normal edit that the operator reviews; do not change installed copies automatically.

## Verdict format

Lead with the verdict (real, partly real, not incremental, false), then the decisive omitted difficulty, the evidence level reached (inspection, documentation, computation or physical test), and the smallest useful next test. Say explicitly what has not been verified.

No new monitoring is created by this procedure. A saved review date is not active watching; start a recurring check only when the operator separately asks and a real mechanism is set up and verified.
