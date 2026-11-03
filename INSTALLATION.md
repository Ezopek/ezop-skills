# Installation

This is a manual, selective process. There is no installer, and none is needed for one skill folder.

## Source versus installation

Cloning or downloading this repository gives you a source copy. It is not an active installation. A client only uses a skill that sits in a location that client reads. Keep the source checkout somewhere neutral and copy the skill folder you want from it.

## Install

The unit to install is a single skill folder (each contains `SKILL.md`). Copy only the folders you want, not the whole repository:

- `scope-discipline/`
- `cad-modeling-and-reverse-engineering/` (geometry; works alone)
- `3d-printing-workflows/` (printing; works alone)
- `skill-creator/` (authoring method; works alone)

The two 3D skills point at each other for the other half of the work, but each states what to do when its sibling is absent, so installing one is fine. Copy a whole folder including its `references/`, `scripts/`, `templates/` and `assets/`: the entry file links to them, and a partial copy leaves broken links. Do not install the repository's `scripts/` or `tests/` directories as skills; they are maintainer tooling for this source tree.

1. Get the source (clone or download a ZIP) into a directory that is not a skills directory.
2. Choose the skills directory your client reads. Locations differ by client and version, and by whether you want the skill for one project or for yourself everywhere. Check the official documentation for your client rather than relying on a guess:
   - [Hermes Agent skills](https://hermes-agent.nousresearch.com/docs/user-guide/features/skills)
   - [Claude Code skills](https://code.claude.com/docs/en/skills)
   - [Codex skills](https://developers.openai.com/codex/skills)
   - [GitHub Copilot agent skills](https://docs.github.com/en/copilot/concepts/agents/about-agent-skills)
3. Copy each chosen folder into that directory, so the result is `<skills-dir>/<skill-name>/SKILL.md`. The folder name should match the `name` in the frontmatter.

Example for a Unix-like shell, where `<source>` is your checkout, `<skills-dir>` is the directory from the client's documentation and `<skill-name>` is one of the folders above:

```bash
mkdir -p "<skills-dir>"
cp -R "<source>/<skill-name>" "<skills-dir>/"
```

If `<skills-dir>/<skill-name>` already exists, do not overwrite it blindly. See the next section.

Notes by skill:

- **Scripts need Python 3.** The helpers in the 3D skills use only the standard library and are not run by installing; read a script before running it. Some references name optional external tools (CadQuery, OpenSCAD, FreeCAD, a slicer command line, ScanRuler, Moonraker/Spoolman services). None is installed or configured by this repository.
- **Printer, firmware and network references** describe procedures for the operator's own equipment. Use your own addresses and credentials in your own environment, never in the skill files.
- **skill-creator** is a manual method with no scripts: nothing in its folder needs Python or a particular client. Only the upstream Apache-2.0 license text is included with attribution (`skill-creator/UPSTREAM.md`). The upstream Claude-specific automation is not supplied and not qualified by this release; do not expect the folder to contain it, and obtain or run upstream code only as a separate decision of your own, after your own review.
- Client-specific features such as invoking a skill by name, automatic activation, or which frontmatter fields are honoured differ by client and version; check the client's documentation.

## Update and sync

`git fetch` refreshes remote-tracking references; it does not change the checked-out skill files. Review and integrate the intended revision using your normal Git workflow, preserving local changes. Neither fetching nor integrating updates installed copies. Updating an installation is a separate, deliberate step:

1. Update the source checkout.
2. Look at what changed in the folders you installed (for example `git log` and `git diff` for each folder), and decide whether you want it.
3. Compare the installed copy with the source (for example `diff -r`). If you edited the installed copy, keep your edits or merge them by hand before replacing anything.
4. Copy over only the skill folder you want to update. If you added your own files to an installed copy, merge by hand instead of replacing the folder; nothing here syncs or updates installations automatically.

Avoid copying everything in the repository into a skills directory, and avoid mirroring commands that delete files in the destination (such as `rsync --delete`). They can remove skills or local edits that did not come from this repository.

Each client and each place (project, personal, IDE, CLI, cloud) is its own installation. Installing in one does not install in the others, so repeat the steps and keep track of where the skill lives. Several copies can drift apart.

## Check that it works

Loader behavior depends on the client and its version: where it looks, when it rescans, and whether it needs a restart or a new session. A copied file is not proof of activation. Verify in the client you actually use:

1. Start a new session, restarting the client if its documentation says to.
2. Use the client's native skill list or loader diagnostics to look for the skill (for example `scope-discipline`), and inspect an actual skill-load/tool trace where available. An agent saying it sees or followed the skill is not proof by itself.
3. Give it a small natural request without naming the skill and check the behaviour. For `scope-discipline`: "I want a script that backs up my notes folder; help me think it through" should produce short coaching steps instead of a large unrequested plan. For the 3D skills: ask a geometry question ("I need to widen a 6 mm hole in this STL by 0.3 mm") or a printing question ("what does this slicer setting do?") and check that the answer follows the skill's safeguards (hash the original and edit a sibling; verify the setting's meaning instead of guessing). Also try a request that should not trigger them.

If the skill does not appear, check the folder location, that `SKILL.md` is directly inside the skill folder, that the frontmatter is valid, and the client's documentation for your version. Do not assume that working in one client means it works in another.

## Optional standing instruction

If you want the skill considered more reliably, you can add a short pointer through your own client's instruction mechanism (user-level or project-level instructions that you are allowed to edit), for example:

```text
For tool, product or workflow design, implementation planning, and scope or
overengineering review, use the scope-discipline skill if it is available.
```

This is optional. Keep it short, since such instructions are usually loaded into every conversation. Do not add it to a shared project unless the people who own that project agree.
