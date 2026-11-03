# ezop-skills

A small, growing collection of portable agent skills. Each skill is a folder with a `SKILL.md` that follows the common Agent Skills layout (`name` and `description` frontmatter), so it can be copied into the skill locations that supported clients read.

## Current skills

| Skill | Purpose | Needs |
|---|---|---|
| [scope-discipline](scope-discipline/) | Keeps design and planning tied to what you asked for | Nothing |
| [cad-modeling-and-reverse-engineering](cad-modeling-and-reverse-engineering/) | Geometry: design, edit and reverse-engineer STL, STEP and project 3MF; fit and printability gates | Optional tools named in references; two stdlib Python helpers |
| [3d-printing-workflows](3d-printing-workflows/) | Printing: slicer semantics, materials, calibration, diagnostics, storage, printer operation | Optional vendor references; two stdlib Python analysers |
| [skill-creator](skill-creator/) | Author, test, review and iterate a skill; adapted from the Anthropic skill-creator (Apache-2.0) | Nothing: a manual method; no upstream automation is supplied |

Each skill is independent: install only the folders you want. The two 3D skills split ownership (geometry versus printing) and say what to do when the other is not installed. None requires a particular client, a private service or a specific CAD tool.

### scope-discipline

Keeps design and planning work tied to what you actually asked for. It targets the point where an agent quietly turns a simple request into roles, approvals, state machines and extra services nobody requested.

- **Coaching first.** For ambiguous or consequential design, the agent talks it through in short steps: outcome, normal user journey, what "done" means, non-goals, and how much complexity you want to own. It asks the most decision-relevant open question rather than handing over a large document for blanket approval.
- **Real alternatives only.** When a choice is material, you get the simplest complete approach, the heavier option that is actually relevant, what each costs, a recommendation, and whether the heavier one can be added later.
- **Small tasks stay fast.** A clear, small task is simply done: no interview, no design file, no extra approval step.
- **Review against intent.** Plans and diffs are checked against your original request: what is missing, what was added unasked, and what could go without losing a required guarantee.
- **Safety stays.** Existing policies, data-loss prevention, input validation and necessary security remain in force. This is not a ban on locks or approvals, only on adding them without a reason.

The skill is guidance that lowers risk. It does not enforce anything.

### Using it

Describe your task in natural language. A client that supports skills can pick the skill from its description when you are designing a tool or workflow, planning an implementation, or asking for a scope or overengineering review. Naming the skill explicitly is optional, and how (or whether) a client supports that depends on the client.

### cad-modeling-and-reverse-engineering

Owns geometry. It routes by what you have (native source, STEP, STL, project 3MF, physical part or scan) and keeps the safeguards that are easy to lose: never edit an original, state units and frames, verify a feature before editing it, never flatten a painted or multi-part 3MF and call it a colour-preserving delivery, and keep kernel validity, export readback, slicer acceptance and physical fit as separate claims. ScanRuler is one optional tool among CadQuery, OpenSCAD, FreeCAD and mesh tools. Two helpers apply and verify reviewed whole-face paint relabels on a 3MF sibling. It gives starting points to test, not universal tolerances, and it does not promise that a printed part fits.

### 3d-printing-workflows

Owns printing. Short standing safeguards (verify slicer semantics, measure instead of copying settings, read-only investigation during a job, authorised setup changes only when idle, an explicitly authorised paused-job recovery as the one scoped exception, redact secrets) with optional topical references: OrcaSlicer seams, supports and forks, FDM baselines, filament storage and inventory, and vendor-specific Snapmaker U1 material that is clearly version-dependent. Two helpers analyse OrcaSlicer G-code offline. It does not control a printer by itself.

### skill-creator

A method for writing a skill, proving it changes behaviour, and revising in proportion: baseline first, realistic and should-not-trigger cases, comparison, untouched final cases, and no automatic publication or adoption. It works by hand with any capable agent and needs no backend. Only the upstream Apache-2.0 license text ships inside the folder (see its `UPSTREAM.md` for the pinned source commit and attribution). The upstream Claude-specific automation (trigger tests, description optimiser, review viewer, agent prompts) is not supplied and not qualified by this release, and the skill does not tell you to download or run it; `UPSTREAM.md` and `references/claude-code-evaluation.md` explain why.

## Installation and updates

See [INSTALLATION.md](INSTALLATION.md). A checkout of this repository is only a source; it does not activate anything by itself, and copying a folder does not prove a client loads it.

## Checking the source

`python3 scripts/check_skills.py` runs offline structural checks (names, frontmatter, links, dependency closure, public-data boundaries) and `python3 -m unittest discover -s tests` exercises the checker and the bundled helpers on synthetic fixtures. These are structure and helper tests, not proof of behaviour in any client.

## Earlier packages

This repository used to hold eight other skill packages and a bundle of community material. They were removed from the current tree and remain recoverable from Git history. Removing them here does not uninstall copies you installed earlier; those stay wherever you put them until you remove them yourself.

## Adding skills later

Each skill lives in its own top-level folder, named after the skill, with a `SKILL.md` inside. Nothing else is required; optional `references/`, `scripts/` and `assets/` must ship inside the folder and resolve from where it is installed.
