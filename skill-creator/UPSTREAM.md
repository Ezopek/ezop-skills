# Upstream attribution and status

This folder adapts the `skill-creator` skill from the Anthropic skills repository.

- Source: <https://github.com/anthropics/skills>, path `skills/skill-creator`
- Pinned commit: `ca45fc496a3436251f191354091d557da31c15b5`
- Pinned tree (provenance and history only): <https://github.com/anthropics/skills/tree/ca45fc496a3436251f191354091d557da31c15b5/skills/skill-creator>
- License: Apache License 2.0. The upstream license text is shipped here as `LICENSE.txt`, byte for byte (sha256 `bc6b3af2f331cbc7fb0da1344efb2cbe5877a31498b4d70dbc7000f3405a1362`). Copyright in the upstream work belongs to its authors; keep their notices when redistributing.

## What ships in this folder

- `LICENSE.txt` (the upstream license, unchanged).
- `SKILL.md`, `UPSTREAM.md`, `references/portable-evaluation.md` and `references/claude-code-evaluation.md`: an adaptation. They re-express the author, test, review and iterate method for any capable agent, add proportionality, untouched-final-acceptance and no-automatic-adoption rules, and keep the method separate from local governance. They derive from the upstream method and are released under the same Apache-2.0 license.

## What is not supplied

The upstream entry document, the grader, comparator and analyzer agent prompts, the review viewer and its page, the trigger-test, benchmark, report, packaging and description-optimisation scripts, and the format validator are **not supplied** by this release and **not qualified** by it. They are not copied here, not patched here, and this skill does not tell anyone to download or run them. The portable, manual method in `SKILL.md` and `references/portable-evaluation.md` is the capability this folder provides, and it needs no backend.

Reasons, from reading the pinned source (nothing was executed to confirm them), so the omission is not mistaken for an endorsement:

- the review-server script terminates whatever process listens on the port it is given and embeds data in page script with plain JSON encoding; the viewer inserts data into HTML without escaping and ignores HTTP error status;
- the format validator accepts blank required strings, the packaging script can include its own output archive, and the benchmark metadata hard-codes a run count;
- the description optimiser reuses its held-out set for selection, so its score is not an untouched final test;
- the trigger detector can report "not triggered" when an unrelated tool call comes first, and it launches a command-line client and writes temporary project command files.

These observations are notes, not fixes: nothing in this release claims the upstream tools are corrected or safe. Any future adoption of upstream automation is a separately scoped decision that still goes through the operator's code review, security and governance process.
