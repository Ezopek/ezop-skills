---
name: backlog-loop-orchestrator
description: >-
  Orchestrate long multi-session backlog delivery loops using planner and worker
  sub-agents, one bounded slice at a time, with append-only log entries,
  verification, commits, and resume-friendly handoff. Use when the user wants
  autonomous repeated plan, implement, verify, commit cycles over a roadmap or
  backlog file such as ROADMAP.md or docs/*backlog*.md.
---

# Backlog Loop Orchestrator

## Overview

Use this skill when the user wants an agent to run an iterative delivery loop over a backlog or roadmap across one or many sessions.
The core pattern is: pick one bounded slice, plan it, implement it in a worker sub-agent, verify it, commit it, log it, then continue.

This skill works best inside a five-skill workflow:

1. `$agent-ready-docs` makes the repo instructions, command surface, and doc ownership trustworthy
2. `$delivery-planner` creates or refreshes the roadmap, backlog, or feature plan
3. `$backlog-loop-orchestrator` executes that plan one slice at a time
4. `$slice-reviewer` can act as the optional pre-commit acceptance gate for each implemented slice
5. `$repo-drift-auditor` can periodically verify that docs, backlog, and workflow assumptions still match the repo

## Announce At Start

When this skill activates, tell the user:

> Using **backlog-loop-orchestrator** to [specific purpose based on the request].

## Quick Start

At the start of the run:

1. Read the repo instruction file if present, such as `AGENTS.md`.
2. Read the backlog source and the few highest-signal docs it depends on.
3. Create or continue an append-only orchestration log.
4. Pick exactly one next bounded slice.
5. Assess slice complexity — choose full planner sub-agent or fast planning path (see **Planning Mode Selection** below).
6. Sanity-check the returned plan yourself before handing to the worker.
7. Spawn a worker sub-agent to implement only that slice using the structured worker prompt format.
8. Run `$slice-reviewer` if the slice touches 3+ services/packages, introduces new interfaces or migrations, or the worker made non-obvious decisions. Skip for small bug fixes and test gaps.
9. Review, verify, commit, update backlog/docs, and then continue to the next iteration.

## Invocation Examples

Recommended Polish invocation:

```text
$backlog-loop-orchestrator zaorkiestruj dluga petle developerska dla zadan opisanych w `docs/operations/ai-assisted-development-backlog.md`.
Czytaj najpierw `AGENTS.md`, `README.md` i `docs/operations/ai-assisted-development.md`.
Prowadz append-only log w `.codex/ai-assisted-backlog-loop.md`.
Pracuj jeden bounded slice naraz: planner sub-agent -> worker sub-agent -> verify -> commit -> kolejny slice.
Zatrzymuj sie tylko przy realnym blockerze albo waznej decyzji architektonicznej.
```

Recommended English invocation:

```text
$backlog-loop-orchestrator orchestrate a long developer delivery loop for the tasks described in `docs/operations/ai-assisted-development-backlog.md`.
Read `AGENTS.md`, `README.md`, and `docs/operations/ai-assisted-development.md` first.
Keep an append-only log in `.codex/ai-assisted-backlog-loop.md`.
Work one bounded slice at a time: planner sub-agent -> worker sub-agent -> verify -> commit -> next slice.
Stop only for a real blocker or an important architectural decision.
```

Minimal invocation also works when the backlog path is already clear:

```text
$backlog-loop-orchestrator run the backlog loop for `ROADMAP.md`
```

Recommended resume invocation:

```text
$backlog-loop-orchestrator wznow dluga petle developerska z logu `.codex/ai-assisted-backlog-loop.md` dla backlogu `docs/operations/ai-assisted-development-backlog.md`.
Najpierw przeczytaj ostatnie wpisy z logu, ustal ostatni zakonczony commit i kontynuuj od pierwszego niezamknietego albo nastepnego sensownego bounded slice'a.
```

Recommended English resume invocation:

```text
$backlog-loop-orchestrator resume the long developer delivery loop from `.codex/ai-assisted-backlog-loop.md` for the backlog in `docs/operations/ai-assisted-development-backlog.md`.
Read the latest log entries first, identify the last completed commit, and continue from the first unfinished or next sensible bounded slice.
```

Recommended paired invocation when the backlog may still need planning help:

```text
$backlog-loop-orchestrator start only after checking whether the backlog in `ROADMAP.md` or `docs/**/backlog*.md` is already execution-ready.
If it is not bounded enough, say so and recommend `$delivery-planner` first. If the docs behind it are too stale to trust, recommend `$agent-ready-docs` before that.
```

## When To Use

Use this skill when:

- the user explicitly wants an autonomous backlog loop
- the work should continue across multiple commits or sessions
- the backlog is already written down in a tracked file
- one-slice-at-a-time discipline matters more than raw speed
- a persistent log would help resume the work later

Do not use this skill when:

- the user only wants a single change
- there is no stable backlog source yet
- the next step depends on unresolved product or architecture decisions
- the task is mostly exploratory research without implementation

## Core Rules

- Always take exactly one bounded slice at a time.
- Prefer the smallest high-signal slice with low blast radius.
- Do not merge unrelated backlog items into one rollout unless the backlog explicitly requires it.
- The main agent owns orchestration, sanity-checks, verification, commit decisions, and loop control.
- The planner sub-agent plans only.
- The worker sub-agent implements only the chosen slice.
- Update docs and backlog in the same slice when the change materially affects them.
- Commit only after green verification.
- Continue autonomously unless there is a real blocker or a high-impact tradeoff.

## Logging

Keep an append-only log outside normal repo history unless the user explicitly wants it tracked.
Default location: `.codex/orchestration-log.md`.

Use `scripts/append_orchestration_log.py` to create the file if missing and append structured entries with ISO timestamps.

Before the first iteration, read [references/log-format.md](references/log-format.md).
When preparing planner and worker prompts, use [references/prompt-templates.md](references/prompt-templates.md).

## Workflow

### 1. Start Or Resume

- Identify the backlog file, stop conditions, and default verification path.
- If the log file exists, read its latest iteration entries before choosing the next slice.
- If the prior session stopped on a blocker, resume from that exact point instead of re-planning the entire backlog.
- If the backlog is too vague or too broad for one-slice-at-a-time execution, stop and recommend `$delivery-planner` instead of improvising a new planning artifact mid-loop.
- If the repo instructions or workflow docs are too stale to trust, stop and recommend `$agent-ready-docs` before continuing.
- If the loop is resuming after a long gap or after many repo-wide changes, consider running `$repo-drift-auditor` before taking the next slice.

### 2. Choose The Next Slice

- Re-read the current backlog file and recent commits if needed.
- Pick one slice that is bounded, decision-light, and valuable.
- Reject slices that silently combine multiple big themes.
- If the remaining work is low-value or stale, log that explicitly instead of forcing more implementation.

### 3. Planning Mode Selection

Choose the planning path based on slice complexity before spawning any sub-agent.

**Use a full planner sub-agent when any of these is true:**
- The slice touches 4 or more files or two or more services
- New interfaces, contracts, schemas, or migration are introduced
- The backlog description is vague about implementation details
- Architectural tradeoffs need to be resolved (e.g., where ownership lives, how services interact)
- The slice might need to be split further

**Use fast planning (no planner sub-agent) when ALL of these are true:**
- Scope is < 4 files, all named explicitly in the backlog or clearly implied
- No new interfaces or contracts — only changes to existing code
- The backlog description already names the approach and the exact change
- The slice is a bug fix, test gap, or isolated improvement with no structural decisions

For fast planning: read the relevant files yourself, write a brief inline plan (5–10 bullet points), and proceed directly to the worker with that plan embedded in the worker prompt.

**Either way:** always sanity-check the plan before the worker starts. The planner or your inline plan must be decision-complete before implementation begins.

### 4. Docs-Impact Awareness

Before finalizing any plan, check explicitly:

- Does the repo have a docs-impact gate in CI or the fast verification path (e.g., a script that fails when contracts, config, or workflow files change without corresponding doc updates)?
- If yes: identify which docs must be updated as part of the slice — do not treat docs as a follow-up. Include them in the worker's file list.
- Common triggers: changes to `packages/contracts`, shared API schemas, environment variables, startup behavior, service boundaries, or migration files.

If the plan misses required docs updates, the verify step will fail. Catching this in the plan is cheaper than fixing it after the worker runs.

### 5. Implement With A Worker Sub-Agent

- Give the worker a narrow, structured implementation target using the worker prompt format in [references/prompt-templates.md](references/prompt-templates.md).
- Use sections (`## Files to read`, `## Exact changes`, `## Docs impact`, `## Verification`, `## Out of scope`) rather than narrative prose — this reduces worker token waste and scope ambiguity.
- Assign ownership clearly if file scope matters.
- Do not let the worker redefine the slice.
- Review the result yourself before accepting it.

### 6. Verify And Commit

- Run the smallest verification set that honestly covers the slice.
- If the repo has a pipeline (turbo, nx, make) that runs checks in parallel, prefer it over sequential manual steps — it is faster and gives the same coverage.
- If running checks manually and Python and TypeScript checks are independent, run them in parallel (separate tool calls) rather than sequentially.
- If verification fails, either fix it in-slice or stop and log the blocker.
- Run `$slice-reviewer` before commit when ANY of these is true:
  - the slice touches 3 or more services or packages
  - a new interface, contract, schema, or DB migration was introduced
  - the slice was split mid-loop from a larger item (sub-slice pattern)
  - the worker made non-obvious decisions or workarounds
- Skip `$slice-reviewer` only when ALL of these are true: scope is < 3 files, no new interfaces, and the change is a bug fix or test gap with no structural decisions.
- Commit with a scoped message once the slice is green.

### 7. Close The Iteration

- Append a log entry with the chosen slice, results, checks, and commit hash.
- Update the backlog/docs if that slice changes the official repo state.
- Then re-enter slice selection for the next iteration.

## Stop Conditions

Stop and ask the user only if:

- the next backlog item is ambiguous or requires an architectural choice
- two reasonable paths have materially different tradeoffs
- the backlog item is already obsolete and needs reframing
- the worktree contains conflicting external edits
- verification keeps failing and needs a human decision
- the remaining backlog is only low-value cleanup and the loop should be reconsidered

## Red Flags

Stop and reconsider if you catch yourself:

- Implementing multiple slices without committing between them
- Letting a worker redefine the slice scope
- Skipping verification to move faster
- Ignoring test failures and committing anyway
- Resuming a loop without reading the log first
- Silently repairing the backlog mid-loop instead of recommending `$delivery-planner`
- Spawning a full planner sub-agent for a 2-file bug fix
- Skipping docs impact when the slice changes contracts or commands
- Treating `accept` as the default decision instead of earning it through evidence

## Safety Checks

- Never commit secrets, tokens, or credentials — check staged files before every commit
- Run verification before every commit, not after
- Do not execute destructive database operations without explicit user approval
- If a worker touches auth, permissions, or security-critical paths, flag for review before committing
- Keep the orchestration log outside version control when it contains sensitive operational detail

## Community Skill Integration

Use these community skills inside the loop when appropriate:

- `superpowers:test-driven-development` — instruct workers to follow TDD for new features and bug fixes
- `superpowers:systematic-debugging` — when verification fails, use structured debugging before attempting fixes
- `superpowers:verification-before-completion` — verify before every commit; evidence before claims
- `superpowers:dispatching-parallel-agents` — when two independent slices can be implemented concurrently
- `superpowers:finishing-a-development-branch` — when the loop completes all backlog items and needs merge or PR decision
- `$pr-reviewer` — for a thorough quality review before merging the accumulated work
- `$security-scanner` — when a slice touches auth, data handling, or infrastructure

## Resources

- `scripts/append_orchestration_log.py`: append-only markdown log helper
- `references/log-format.md`: durable log structure for long sessions
- `references/prompt-templates.md`: reusable planner and worker prompt skeletons
