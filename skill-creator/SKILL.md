---
name: skill-creator
description: "Use when creating a new agent skill, changing an existing one, or checking whether a skill changes behaviour: drafting SKILL.md, writing realistic test prompts, comparing with and without the skill, reviewing results, reviewing a skill's description for discovery."
license: Apache-2.0
compatibility: "Needs only a capable agent and a file system. No script, viewer or backend is bundled or required."
metadata:
  upstream: "anthropics/skills skills/skill-creator, commit pinned in UPSTREAM.md"
  adaptation: "portable author, test, review, iterate method"
---

# Skill creator

A method for writing a skill, proving that it changes behaviour, and improving it in proportion to the change. It adapts the Anthropic skill-creator (Apache-2.0; see `UPSTREAM.md` and `LICENSE.txt`) so that any capable agent can follow it by hand. Only the upstream licence text ships here; the upstream scripts, viewer and agent prompts are not supplied (see `UPSTREAM.md`).

This skill is guidance. It does not publish, install, adopt or harvest anything, and it does not decide local policy.

## What this skill does not decide

Scope, security review, provenance and licensing checks, release, installation, and which skills a person or organisation adopts belong to the operator's own policy. Apply that policy alongside this method. Never fetch or run upstream automation, publish or install a result, or copy material from other people's sessions because this skill mentions them.

## Route by task

| Situation | Do |
|---|---|
| New skill or a behaviour change | Follow the loop below. Read `references/portable-evaluation.md` for how to run and judge test cases without special tooling. |
| Typo, wording, link or formatting fix | Fix it, run the structural check, stop. No behaviour test. |
| Someone asks for automated trigger tests, a benchmark viewer or description optimisation | Read `references/claude-code-evaluation.md`: that automation is not supplied or qualified by this release; use the manual route. |
| Want the original upstream method and its provenance | `UPSTREAM.md` (pinned commit and links). |

## The loop

1. **Capture intent.** What should the skill make an agent do that it would not do reliably unaided? What does a good result look like, in artifacts a person can inspect? Ask for real examples. If the conversation already contains the workflow the person wants captured, extract it before asking again.
2. **Check the baseline first.** Run two or three realistic tasks without the skill (or with the current version). Write down what went wrong or was skipped. A skill that fixes nothing observed is not needed; say so.
3. **Write the minimum.** Frontmatter `name` and `description`, a short body, and optional `references/`, `scripts/`, `assets/` that really ship with the skill. Put the "when to use" signal in the description, not the body. Explain why a rule matters instead of shouting it. Keep the main file short and move optional depth into references that are linked from it.
4. **Test on real artifacts.** Run the prepared tasks with the skill. Judge outputs by inspecting them (files, diffs, measured numbers), not by the agent's description of what it did.
5. **Compare.** Candidate versus baseline (or versus the previous version, snapshotted before editing). Note what improved, what regressed, and what did not matter. Keep a human review of the outputs in the loop; automated assertions alone miss real problems.
6. **Revise in proportion.** Change the instruction that matches the observed failure. Generalise from the failure to the principle rather than patching one example. Remove text that did not help.
7. **Repeat** until the observed problems are gone or further change stops paying for itself.
8. **Final acceptance on untouched cases.** Keep a few cases you did not use while iterating. Run them once on the final version. Do not tune the skill on them and then reuse them as proof.

## Test case design

Include all three kinds:

- **Natural discovery cases.** A request phrased the way a person would actually ask, with no skill name and no hint. These show whether the description is enough for an unaided agent to select the skill. Prefer concrete, slightly messy prompts (file names, context, typos) over tidy abstract ones.
- **Should-not-trigger cases.** Near misses that share keywords but need a different tool or skill. A skill that fires on everything is a defect.
- **Task cases with real artifacts.** Inputs and expected outputs that can be inspected. Use visibly synthetic or user-approved data, never someone's private files or credentials.

Where behaviour is objectively checkable, add small assertions. Where it is a matter of taste (writing style, design), review by reading the outputs instead of forcing a score.

## Proportion

- A format validator checks structure (names, frontmatter, links). It is not a behaviour test. Report them separately.
- Tiny edits need no benchmark. Behaviour changes need a baseline and candidate comparison on realistic tasks. Large rewrites deserve a fresh round of the whole loop.
- Do not report numbers you did not measure. When a quantitative run is not available (no parallel agents, no timing data, no permission to run tools), say so and fall back to manual review of outputs, or a static review against the checklist in `references/portable-evaluation.md`.
- Repeated model runs cost time and money. Ask before launching many of them, and never run evaluations through a payer, model or account the operator has not authorised for that purpose.

## Description discovery

The description is the only text most clients see before deciding to load a skill. Make it say what the skill does and when to use it, in the words people use. Check it with the natural-discovery and should-not-trigger cases above. Do not stuff keywords, and do not claim that a client will select the skill: selection is the client's decision. Any automated description search (see `references/claude-code-evaluation.md` for why none is supplied) selects text with a score it also reuses across iterations, so treat a selected description as a draft and confirm it on cases never used for selection.

## Layout reminders

```text
skill-name/
  SKILL.md          required: name, description, short body
  references/       optional depth, loaded when linked and needed
  scripts/          optional deterministic helpers; review before running
  assets/           optional templates and static files
```

Every file the skill points to must ship inside the folder and resolve from the installed location. Do not rely on private paths, other unshipped skills, or a fixed tool name that only one client provides; describe the capability instead (read a file, search the repository, run a command) and let the client map it.

## Handoff

Report: what changed and why, the cases run (including discovery and should-not-trigger), what the baseline did, what the candidate did, what you did not test, and any step that needs the operator's decision. Leave publication, installation and adoption to them.
