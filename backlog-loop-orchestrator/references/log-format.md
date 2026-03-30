# Log Format

Use an append-only markdown log.
Default path: `.codex/orchestration-log.md`.

## Principles

- Never rewrite prior entries unless the user explicitly asks.
- Prefer one entry per meaningful event over one giant summary.
- Always include an ISO timestamp with timezone offset.
- Keep entries short and factual.
- Record enough detail that a future session can resume without rereading the whole chat.

## Suggested File Structure

```md
# Orchestration Log

## Session Start
- timestamp: 2026-03-30T12:34:56+02:00
- repo: /abs/path/to/repo
- backlog_source: docs/operations/ai-assisted-development-backlog.md
- log_owner: codex-main-agent
- stop_conditions: blocker | ambiguity | user_pause

## Iteration 001 Selected
- timestamp:
- slice:
- why_now:
- planned_with:

## Iteration 001 Planned
- timestamp:
- planner_agent:
- summary:
- risks:
- verification_plan:

## Iteration 001 Implemented
- timestamp:
- worker_agent:
- summary:
- files:

## Iteration 001 Verified
- timestamp:
- checks:
- result:

## Iteration 001 Committed
- timestamp:
- commit:
- summary:
- next_candidate:
```

## Minimum Fields Per Event

Every appended event should include:

- `timestamp`
- `iteration`
- `event`
- `slice`
- `summary`

Include these when relevant:

- `planner_agent`
- `worker_agent`
- `checks`
- `result`
- `commit`
- `next_candidate`
- `blocker`

## Event Names

Use short stable event names:

- `session-start`
- `resume`
- `slice-selected`
- `plan-accepted`
- `implementation-accepted`
- `verification-passed`
- `verification-failed`
- `committed`
- `stopped`

## Resume Guidance

When resuming:

1. Read the latest `session-start`, `resume`, `slice-selected`, `plan-accepted`, and `stopped` entries.
2. Trust the newest successful `committed` entry as the last completed slice.
3. If the newest incomplete event is `verification-failed` or `stopped`, resume from there instead of picking a new slice.
