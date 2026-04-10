---
name: slice-reviewer
description: >-
  Review one bounded implementation slice against its approved plan, backlog
  item, diff, verification results, and docs impact. Use when the user wants a
  findings-first acceptance review focused on regressions, missing tests,
  scope creep, docs drift, and whether the slice is ready to commit or needs
  more work.
---

# Slice Reviewer

## Overview

Use this skill when the user wants a focused review of one bounded implementation slice before merge or commit.
This skill is a specialized acceptance gate, not a planner and not a generic architecture brainstormer.

It works best when you have:

- an approved backlog item or feature plan
- the actual code changes or diff
- the verification output
- any touched docs

The main job is to answer:

- did the implementation actually match the agreed slice
- are there bugs or regression risks
- is verification honest and sufficient
- did docs, tests, or contracts move when they should have
- is this slice ready to accept, or does it still need fixes

This skill is the natural fourth step after the other workflow skills:

1. `$agent-ready-docs` makes repo guidance trustworthy
2. `$delivery-planner` produces bounded slices or feature plans
3. `$backlog-loop-orchestrator` runs plan -> implement -> verify
4. `$slice-reviewer` performs the final findings-first acceptance check before commit or merge

## Announce At Start

When this skill activates, tell the user:

> Using **slice-reviewer** to [specific purpose based on the request].

## Quick Start

1. Read the approved slice definition first, usually from a backlog item, feature plan, or prior accepted plan.
2. Read the changed files or diff.
3. Read the relevant test and verification output.
4. Compare implementation against the intended slice before judging style or polish.
5. Report findings first, ordered by severity.
6. End with a clear decision: `accept`, `needs-fix`, or `blocked`.

## Invocation Examples

Recommended Polish invocation:

```text
$slice-reviewer zrob review tego jednego bounded slice'a przed commitem.
Najpierw przeczytaj zaakceptowany plan albo backlog item, potem diff, zmienione pliki, testy i docs.
Chce findings-first review: bugi, regression risk, missing tests, docs drift, scope creep i jasna decyzja `accept`, `needs-fix` albo `blocked`.
```

Recommended English invocation:

```text
$slice-reviewer review this single bounded slice before commit.
Read the approved plan or backlog item first, then inspect the diff, changed files, tests, and docs.
I want a findings-first review covering bugs, regression risk, missing tests, docs drift, scope creep, and a clear `accept`, `needs-fix`, or `blocked` decision.
```

Minimal invocation:

```text
$slice-reviewer review this slice against the approved plan
```

## When To Use

Use this skill when:

- a single slice was just implemented and needs an acceptance pass
- the user asks for review with emphasis on correctness and risk
- `$backlog-loop-orchestrator` has a candidate slice that is almost ready to commit
- a worker output needs checking against the original scope

Do not use this skill when:

- the slice has not been planned yet
- the task is still mostly open design work
- there is no meaningful change set to review

## Core Principles

- Findings first. Lead with bugs, regressions, missing verification, docs drift, and scope problems.
- Review against the approved slice, not against an imagined larger ideal solution.
- Prefer correctness, safety, and boundedness over polish.
- If a fact is discoverable from the diff, tests, docs, or repo, inspect it before asking.
- If the approved slice is missing or too vague, say that review confidence is limited and recommend `$delivery-planner` first.
- If the surrounding docs are too stale to judge whether docs drift exists, say so and recommend `$agent-ready-docs`.
- If verification is too weak to justify acceptance, treat that as a real finding.

## Required Inputs

Read [references/checklist.md](references/checklist.md) before finalizing.
Read [references/findings-taxonomy.md](references/findings-taxonomy.md) when deciding severity and review shape.

Strong reviews usually look at:

- the approved slice or plan
- changed files or diff
- current repo context where needed
- tests or check outputs
- touched docs

If one of those is missing, state the limitation explicitly.

## Review Workflow

### 1. Reconstruct The Intended Slice

- Read the backlog item, feature plan, or approved slice summary first.
- Identify the real success criteria, non-goals, and verification expectations.
- Identify what explicitly should not have been touched.

### 2. Inspect The Change Set

- Read the changed files and diff carefully.
- Confirm the implementation matches the intended seam, endpoint, flow, or module boundary.
- Look for hidden broadening of scope.

### 3. Check Correctness And Risk

- Look for broken behavior, mismatch between interfaces and implementation, and likely regressions.
- Pay special attention to contracts, migrations, error paths, observability, and docs expectations when relevant.

### 4. Check Verification Honesty

- Were the right tests or checks run
- Were any important checks skipped
- Does the verification actually cover the changed behavior
- Are missing tests a real risk for this slice

### 5. Check Documentation And Scope Discipline

- If the slice changed architecture, contracts, commands, workflows, or public behavior, did the docs move with it
- If the change widened beyond the approved slice, call that out explicitly

### 6. Produce The Review

Use the repo's normal review style when one exists.
By default:

- findings first
- ordered by severity
- with file references when possible
- followed by assumptions or open questions
- then a short acceptability decision

## Decision Output

End the review with one of these:

- `accept`: no material findings; residual risk is low enough to proceed
- `needs-fix`: the slice is close, but one or more findings must be resolved first
- `blocked`: the slice cannot be judged or accepted without a missing decision, missing artifact, or major correction

Do not hide a `needs-fix` or `blocked` result behind soft language.

## Relationship To Other Skills

Use this skill after `$delivery-planner` when:

- the plan is approved and implementation happened
- you want to review the result against the original slice definition

Use this skill inside or alongside `$backlog-loop-orchestrator` when:

- a worker has finished a bounded slice
- the orchestrator wants a stronger pre-commit gate than a lightweight sanity check

Recommend `$delivery-planner` instead when:

- the slice is underspecified
- the review keeps uncovering planning gaps instead of implementation issues

Recommend `$agent-ready-docs` instead when:

- the code may be fine, but the repo docs are too stale or too weak to support trustworthy acceptance

Recommend `$repo-drift-auditor` instead when:

- review findings suggest repeated backlog drift, docs drift, or workflow drift beyond this one slice
- the right fix depends on whether the repo is broadly out of sync rather than this change alone

## Output Expectations

Strong output from this skill usually includes:

- `Findings`
- `Assumptions` or `Open Questions` only if needed
- `Decision`

If there are no findings, say so explicitly and mention any residual risk or test gap.

## Red Flags

Stop and reconsider if you catch yourself:

- Approving a slice you have not actually read the diff for
- Skipping verification output review and trusting claims at face value
- Rating severity based on gut feeling instead of evidence from the diff
- Reviewing against an imagined ideal rather than the approved plan
- Marking `accept` when verification was not run or was incomplete
- Inflating findings to seem thorough when the slice is genuinely clean
- Missing security implications in auth, data handling, or permission changes
- Ignoring docs impact because the code changes look correct

## Community Skill Integration

Use these community skills alongside this one when appropriate:

- `superpowers:verification-before-completion` — verify all acceptance claims are backed by evidence
- `superpowers:systematic-debugging` — when a finding needs root-cause investigation before judging severity
- `$security-scanner` — for deep security review of slices touching auth, data, or infrastructure
- `$pr-reviewer` — when the review scope is broader than plan compliance and includes general quality

## Resources

- [references/findings-taxonomy.md](references/findings-taxonomy.md): review categories and severity guidance
- [references/checklist.md](references/checklist.md): final acceptance checklist for one bounded slice
- [references/prompt-templates.md](references/prompt-templates.md): reusable prompts for pre-commit and post-worker review
