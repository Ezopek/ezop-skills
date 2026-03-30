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

Use this skill when the user wants Codex to run an iterative delivery loop over a backlog or roadmap across one or many sessions.
The core pattern is: pick one bounded slice, plan it in a planner sub-agent, implement it in a worker sub-agent, verify it, commit it, log it, then continue.

This skill works best inside a five-skill workflow:

1. `$agent-ready-docs` makes the repo instructions, command surface, and doc ownership trustworthy
2. `$delivery-planner` creates or refreshes the roadmap, backlog, or feature plan
3. `$backlog-loop-orchestrator` executes that plan one slice at a time
4. `$slice-reviewer` can act as the optional pre-commit acceptance gate for each implemented slice
5. `$repo-drift-auditor` can periodically verify that docs, backlog, and workflow assumptions still match the repo

## Quick Start

At the start of the run:

1. Read the repo instruction file if present, such as `AGENTS.md`.
2. Read the backlog source and the few highest-signal docs it depends on.
3. Create or continue an append-only orchestration log.
4. Pick exactly one next bounded slice.
5. Spawn a planner sub-agent for that slice.
6. Sanity-check the returned plan yourself.
7. Spawn a worker sub-agent to implement only that slice.
8. Optionally run `$slice-reviewer` for a stronger acceptance gate when the slice is non-trivial or autonomy is high.
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

### 3. Plan With A Sub-Agent

- Generate a planner prompt for exactly one slice.
- Require repo-grounded discovery before the plan.
- Require a decision-complete plan, not broad brainstorming.
- After the planner returns, sanity-check the plan yourself before implementation.
- Treat the backlog as the primary source of slice intent, but use repo docs and current code to catch stale or already-completed items.

### 4. Implement With A Separate Sub-Agent

- Give the worker a narrow implementation target.
- Assign ownership clearly if file scope matters.
- Do not let the worker redefine the slice.
- Review the result yourself before accepting it.

### 5. Verify And Commit

- Run the smallest verification set that honestly covers the slice.
- If the repo has a canonical fast path, prefer that unless a narrower truthful path is better.
- If verification fails, either fix it in-slice or stop and log the blocker.
- For non-trivial slices or highly autonomous runs, consider a `$slice-reviewer` pass before commit.
- Commit with a scoped message once the slice is green.

### 6. Close The Iteration

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

## Resources

- `scripts/append_orchestration_log.py`: append-only markdown log helper
- `references/log-format.md`: durable log structure for long sessions
- `references/prompt-templates.md`: reusable planner and worker prompt skeletons
