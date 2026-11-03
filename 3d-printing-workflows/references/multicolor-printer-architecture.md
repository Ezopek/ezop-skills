# Multicolour printer architectures and prime-tower principles

Prices, specifications and availability change quickly; use current vendor pages for those and independent reviews plus community threads for reliability and software maturity. Treat vendor "low waste, high speed" claims as marketing until hands-on reviews corroborate them. Snapmaker U1 specifics are in `snapmaker-u1-multicolor-tuning.md`.

## 1. Architectures

- **Single-nozzle filament changers** (AMS-style, CFS-style, MMU-style): can scale to many loaded colours, but pay in purge waste, swap time and material compatibility limits. With more units the loaded colour count can rise (sources cited 16 or more depending on model and configuration; verify the current figure).
- **Toolchangers and multi-toolhead printers** (U1, XL-class): usually fewer native tools and colours, but much lower purge waste and faster, cleaner transitions. A four-toolhead machine natively holds four colours or materials; more needs workarounds (manual swaps, virtual or mixed-colour slicer features, experimental external units) that are not equivalent to native high colour counts.
- Core trade-off: a toolchanger loses to multi-unit changers on maximum loaded colours and wins on waste and change time.

Recommend a toolchanger for colourful PLA/PETG prints, props, organisers and decorative parts, low waste and openness. Suggest waiting or alternatives when the priorities are the most polished phone and library ecosystem, more than the native colour count without workarounds, true actively heated engineering-material workflows, proven long-term toolchanger durability, quiet operation or a dry enclosed filament store out of the box. Describe an enclosure or top cover honestly: it helps drafts, dust, chamber stability and filtering, but does not turn the machine into an actively heated engineering-material printer. Verify current firmware and documentation before advising electrical modifications.

## 2. Prime towers on toolchangers

A one-nozzle-per-tool machine does not mainly flush an old colour from a shared nozzle; the tower re-primes a parked toolhead after pressure loss, ooze or slight heat degradation. Do not import changer-style colour-flush volumes blindly. Keep the tower for real multi-tool prints, because disabling it can cause stringing, debris, weak starts and intermittent extrusion after a swap.

Distinguish three controls that look related: the process-level `Prime volume`, each filament's `Minimal purge on wipe tower` (a high filament minimum can defeat a lower process prime volume, so check both), and a single-nozzle colour-flush matrix. Read the active process and each filament profile; defaults vary, so do not repeat 45 or 60 mm³ as universal.

Safe tuning (change one variable group at a time): set both volume controls to a moderate starting value (in one researched U1 workflow 20 mm³ for PLA/PETG on 0.4 mm nozzles), validate a representative multicolour model, reduce stepwise (15 mm³) only while every post-swap start is clean, treat 10–12 mm³ as experimental, then reduce width on short models, and tune geometry separately (use rib walls, footprint and brim for sway, nozzle strikes or poor adhesion; official guidance for tall towers recommended a rib wall type). Roll back by about 5 mm³ when the first lines after a swap are intermittent, contaminated or under-extruded; roll back geometry when the tower sways, curls, detaches or is struck. Keep experimental "no sparse layers" options off unless validated: skipping tower layers adds downward-travel and collision risk. Community values such as 5–10 mm³ are experiments, not presets; mixed community reports around 15 mm³ are a validation target, not a guarantee.

Evidence quality: do not call a forum participant vendor staff unless the forum visibly marks the account as staff. Never lead with an aggressive example as if it were a safe universal preset.
