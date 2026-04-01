# Log Format

Use an append-only markdown log.
Default path: `.codex/orchestration-log.md`.

## Principles

- Never rewrite prior entries unless the user explicitly asks.
- Prefer one entry per meaningful event over one giant summary.
- Always include an ISO timestamp with timezone offset.
- Keep entries short and factual — avoid multi-sentence narrative in structured fields.
- Record enough detail that a future session can resume without rereading the whole chat.
- Use consistent key-value format within each entry so entries are machine-readable and auditable.

## Suggested File Structure

```md
# Orchestration Log

## Session Start
- timestamp: 2026-03-30T12:34:56+02:00
- repo: /abs/path/to/repo
- backlog_source: docs/operations/ai-assisted-development-backlog.md
- log_owner: main-agent
- stop_conditions: blocker | ambiguity | user_pause

## Iteration 001 slice-selected
- timestamp: 2026-03-30T12:35:00+02:00
- iteration: 001
- event: slice-selected
- slice: <short slice name>
- why_now: <one sentence — what makes this the next right slice>
- planning_mode: full-planner | fast-planning

## Iteration 001 plan-accepted
- timestamp: 2026-03-30T12:40:00+02:00
- iteration: 001
- event: plan-accepted
- slice: <short slice name>
- summary: <2–3 sentences on what the plan covers>
- verification_plan: <command or pipeline>
- risks: <known tricky spots, or "none">

## Iteration 001 worker-started
- timestamp: 2026-03-30T12:41:00+02:00
- iteration: 001
- event: worker-started
- slice: <short slice name>
- worker_role: implementation

## Iteration 001 verification-passed
- timestamp: 2026-03-30T12:55:00+02:00
- iteration: 001
- event: verification-passed
- slice: <short slice name>
- verification: <command> — <result summary, e.g. "all 34 tests pass">
- fixes_applied: <any in-slice fixes needed, or "none">

## Iteration 001 committed
- timestamp: 2026-03-30T12:56:00+02:00
- iteration: 001
- event: committed
- slice: <short slice name>
- commit: <hash>
- summary: <one sentence on what landed>
- next_candidate: <name of next slice, or "backlog review needed">
```

## Minimum Fields Per Event

Every appended event should include:

- `timestamp`
- `iteration`
- `event`
- `slice`
- `summary`

Include these when relevant:

- `planning_mode` (full-planner or fast-planning)
- `verification_plan`
- `risks`
- `verification` (command + result)
- `fixes_applied`
- `commit`
- `next_candidate`
- `blocker`
- `architectural_decision` (when a planner identified a split or non-obvious tradeoff)

## Event Names

Use short stable event names:

- `session-start`
- `resume`
- `slice-selected`
- `plan-accepted`
- `worker-started`
- `verification-passed`
- `verification-failed`
- `committed`
- `stopped`
- `architectural-decision` (when the loop paused for a meaningful tradeoff)

## Field Style Rules

- Values must fit on one line — no multi-line narrative inside a field.
- If detail is needed, add it as a sub-key or a follow-up field, not a multi-sentence string.
- Boolean facts: `fixes_applied: none` or `fixes_applied: gateway test mock missing artifacts field`.
- Commit hashes: short form (7 chars), e.g. `commit: c7c7faf`.
- Slice names: stable short form matching the backlog, e.g. `Phase 3 / Slice 3: Artifact Manifests`.

## Resume Guidance

When resuming:

1. Read the latest `session-start`, `resume`, `slice-selected`, `plan-accepted`, and `stopped` entries.
2. Trust the newest successful `committed` entry as the last completed slice.
3. If the newest incomplete event is `verification-failed` or `stopped`, resume from there instead of picking a new slice.
4. If the last `committed` entry has `next_candidate`, use it as the default starting point — but still re-read the backlog to confirm it is still valid.
