# Installation

This is a manual, selective process. There is no installer, and none is needed for one skill folder.

## Source versus installation

Cloning or downloading this repository gives you a source copy. It is not an active installation. A client only uses a skill that sits in a location that client reads. Keep the source checkout somewhere neutral and copy the skill folder you want from it.

## Install

The unit to install is a single folder: `scope-discipline/` (containing `SKILL.md`). Copy that folder, not the whole repository.

1. Get the source (clone or download a ZIP) into a directory that is not a skills directory.
2. Choose the skills directory your client reads. Locations differ by client and version, and by whether you want the skill for one project or for yourself everywhere. Check the official documentation for your client rather than relying on a guess:
   - [Hermes Agent skills](https://hermes-agent.nousresearch.com/docs/user-guide/features/skills)
   - [Claude Code skills](https://code.claude.com/docs/en/skills)
   - [Codex skills](https://developers.openai.com/codex/skills)
   - [GitHub Copilot agent skills](https://docs.github.com/en/copilot/concepts/agents/about-agent-skills)
3. Copy the one folder into that directory, so the result is `<skills-dir>/scope-discipline/SKILL.md`. The folder name should match the `name` in the frontmatter.

Example for a Unix-like shell, where `<source>` is your checkout and `<skills-dir>` is the directory from the client's documentation:

```bash
mkdir -p "<skills-dir>"
cp -R "<source>/scope-discipline" "<skills-dir>/"
```

If `<skills-dir>/scope-discipline` already exists, do not overwrite it blindly. See the next section.

## Update and sync

`git fetch` refreshes remote-tracking references; it does not change the checked-out skill files. Review and integrate the intended revision using your normal Git workflow, preserving local changes. Neither fetching nor integrating updates installed copies. Updating an installation is a separate, deliberate step:

1. Update the source checkout.
2. Look at what changed in `scope-discipline/` (for example `git log` and `git diff` for that folder), and decide whether you want it.
3. Compare the installed copy with the source (for example `diff -r`). If you edited the installed copy, keep your edits or merge them by hand before replacing anything.
4. Copy over only the skill folder you want to update.

Avoid copying everything in the repository into a skills directory, and avoid mirroring commands that delete files in the destination (such as `rsync --delete`). They can remove skills or local edits that did not come from this repository.

Each client and each place (project, personal, IDE, CLI, cloud) is its own installation. Installing in one does not install in the others, so repeat the steps and keep track of where the skill lives. Several copies can drift apart.

## Check that it works

Loader behavior depends on the client and its version: where it looks, when it rescans, and whether it needs a restart or a new session. A copied file is not proof of activation. Verify in the client you actually use:

1. Start a new session, restarting the client if its documentation says to.
2. Use the client's native skill list or loader diagnostics to look for `scope-discipline`, and inspect an actual skill-load/tool trace where available. An agent saying it sees or followed the skill is not proof by itself.
3. Give it a small design request, such as "I want a script that backs up my notes folder; help me think it through", and check that it coaches in short steps instead of producing a large unrequested plan.

If the skill does not appear, check the folder location, that `SKILL.md` is directly inside the skill folder, that the frontmatter is valid, and the client's documentation for your version. Do not assume that working in one client means it works in another.

## Optional standing instruction

If you want the skill considered more reliably, you can add a short pointer through your own client's instruction mechanism (user-level or project-level instructions that you are allowed to edit), for example:

```text
For tool, product or workflow design, implementation planning, and scope or
overengineering review, use the scope-discipline skill if it is available.
```

This is optional. Keep it short, since such instructions are usually loaded into every conversation. Do not add it to a shared project unless the people who own that project agree.
