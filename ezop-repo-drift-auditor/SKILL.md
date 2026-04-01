---
name: ezop-repo-drift-auditor
description: >-
  Audit whether repository docs, backlog items, workflow descriptions, commands,
  and implementation reality have drifted apart. Use when the user wants a
  repo-grounded drift check before planning, before resuming a long autonomous
  loop, after several slices, or when documentation and backlog trust are in
  doubt.
---

# Repo Drift Auditor

## Overview

Use this skill when the user wants to know whether the repo's documented truth still matches the actual repo state.
This is a drift-auditing skill, not a code-review skill and not a planner.

Its main job is to find and classify mismatches such as:

- commands documented but no longer canonical
- workflows described in docs but not reflected in scripts or CI
- backlog or roadmap items that are stale, already done, or no longer sliced correctly
- architecture claims that no longer match code ownership
- contract or schema guidance that no longer matches the real source of truth

This skill is the cross-cutting integrity check around the other workflow skills:

1. `$ezop-agent-ready-docs` fixes repo source-of-truth docs
2. `$ezop-delivery-planner` creates or refreshes roadmap and backlog artifacts
3. `$ezop-backlog-loop-orchestrator` executes bounded slices
4. `$ezop-slice-reviewer` checks one finished slice
5. `$ezop-repo-drift-auditor` periodically checks whether those artifacts still match reality

## Quick Start

1. Read the repo instructions and the key docs first.
2. Read the canonical command, workflow, and code ownership sources next.
3. Compare documentation and planning artifacts against the actual repo state.
4. Report concrete drift findings, not vague impressions.
5. End with clear routing guidance about which follow-up skill should handle the fixes.

## Invocation Examples

Recommended Polish invocation:

```text
$ezop-repo-drift-auditor sprawdz, czy dokumentacja, backlog, workflowy i realny stan repo nie rozjechaly sie ze soba.
Najpierw przeczytaj `AGENTS.md`, `README.md`, backlogi lub roadmapy, a potem zweryfikuj komendy, CI, kluczowe docs i aktualny kod.
Chce findings-first audit driftu oraz jasne wskazanie, czy kolejnym krokiem powinien byc `$ezop-agent-ready-docs`, `$ezop-delivery-planner`, `$ezop-backlog-loop-orchestrator` czy `$ezop-slice-reviewer`.
```

Recommended English invocation:

```text
$ezop-repo-drift-auditor audit whether the docs, backlog, workflows, and actual repo state have drifted apart.
Read `AGENTS.md`, `README.md`, the roadmap or backlog docs, and then verify commands, CI, key docs, and the current code.
I want a findings-first drift audit plus a clear recommendation for whether `$ezop-agent-ready-docs`, `$ezop-delivery-planner`, `$ezop-backlog-loop-orchestrator`, or `$ezop-slice-reviewer` should handle the next step.
```

Minimal invocation:

```text
$ezop-repo-drift-auditor audit this repo for docs and backlog drift
```

## When To Use

Use this skill when:

- a backlog or roadmap may be stale
- a long-running autonomous loop is about to resume
- several slices landed and you want a repo-wide consistency check
- review findings suggest repeated docs drift or planning drift
- the user is not sure whether to plan, execute, or first repair docs

Do not use this skill when:

- the user already wants one specific fix and the drift question is irrelevant
- the repo has barely changed and a drift audit would add no value

## Core Principles

- Start from the actual repo, not from documented claims.
- Prefer concrete mismatches over broad “the docs feel stale” summaries.
- Separate drift findings from the remediation step.
- Route to the right follow-up skill instead of trying to solve every problem inside the audit.
- If a supposed drift issue is actually just a missing decision, say so clearly.
- If external guidance matters, verify from official or primary sources before claiming the repo is outdated.

## What To Audit

Read [references/drift-surfaces.md](references/drift-surfaces.md) before large audits.
Read [references/checklist.md](references/checklist.md) before finalizing.

High-value drift surfaces usually include:

- `AGENTS.md`
- `README.md`
- `docs/operations/`
- `docs/adr/`
- roadmap and backlog files
- `package.json`, `Makefile`, `turbo.json`
- `.github/workflows/`
- code areas that the docs or backlog describe as source of truth

## Audit Workflow

### 1. Build The Claimed Truth

- Read the docs and planning artifacts that currently define how the repo should work.
- Identify the claimed commands, workflows, ownership boundaries, and next steps.

### 2. Build The Actual Truth

- Read the real command surfaces, CI workflows, current code ownership seams, and recent commits where helpful.
- Check whether the documented behavior is still true.

### 3. Compare And Classify Drift

Look for drift in categories such as:

- docs drift
- workflow drift
- backlog drift
- contract drift
- architecture drift
- command drift

Read [references/routing-guidance.md](references/routing-guidance.md) before final routing.

### 4. Report Findings First

By default:

- report the most important drift first
- explain what the docs or backlog claim
- explain what the repo actually does
- say why the mismatch matters

### 5. Route To The Right Next Step

End by recommending the smallest correct follow-up:

- `$ezop-agent-ready-docs` when the source-of-truth docs need repair
- `$ezop-delivery-planner` when roadmap or backlog artifacts need re-planning
- `$ezop-backlog-loop-orchestrator` when the artifacts are sound and the repo is ready for execution
- `$ezop-slice-reviewer` when the real issue is acceptance of one specific completed slice, not repo-wide drift

## Output Expectations

Strong output from this skill usually includes:

- `Findings`
- `Routing Recommendation`
- `Assumptions` only if needed

If no meaningful drift is found, say so directly and recommend proceeding with the appropriate next skill instead of padding the answer.

## Resources

- [references/drift-surfaces.md](references/drift-surfaces.md): where high-value drift usually hides
- [references/checklist.md](references/checklist.md): final audit checklist
- [references/routing-guidance.md](references/routing-guidance.md): how to choose the next skill after the audit
- [references/prompt-templates.md](references/prompt-templates.md): reusable prompts for pre-planning, pre-resume, and periodic drift audits
