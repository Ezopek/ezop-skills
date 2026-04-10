# Prompt Templates

Use these as skeletons, not rigid scripts. Replace placeholders with repo-specific details.

---

## Planner Prompt (full sub-agent)

Use when the slice needs repo-grounded discovery and architectural decisions.

```text
Plan exactly one next bounded slice from `<BACKLOG_FILE>`.

Do not implement. Do only discovery and planning.

Read first:
- <REPO_INSTRUCTIONS>
- <CORE_DOC_1>
- <BACKLOG_FILE>

Context:
- last completed commit: <COMMIT>
- current loop goal: <GOAL>
- out of scope for this slice: <OUT_OF_SCOPE>

Tasks:
- identify the remaining candidate slices relevant now
- recommend exactly one next bounded slice
- explain why it is the best next candidate
- produce a decision-complete implementation plan:
  - exact files to change and what to do in each
  - new files to create, if any
  - which docs must be updated (check if the repo has a docs-impact gate
    in CI or verify-fast — if so, treat docs updates as mandatory, not optional)
  - explicit deferred items that are out of scope for this slice
  - verification path (canonical fast path first unless a narrower path is more truthful)
  - known risks or tricky spots the worker should watch for

The plan must stay scoped to one slice only.
If the slice is too large to implement in one iteration, say so explicitly and propose a split.
```

---

## Fast Planning (inline, no sub-agent)

Use when the slice is < 4 files, scope is fully explicit in the backlog, and no new interfaces or architecture decisions are needed.

Instead of spawning a planner sub-agent, read the relevant files yourself and write an inline plan directly in the worker prompt. The plan should be 5–10 bullet points:

```text
Inline plan for <SLICE_NAME>:

- Read <FILE_1> to understand <X>
- Change <FILE_2>: <exact change>
- Change <FILE_3>: <exact change>
- Add test in <FILE_4> covering <scenario>
- Docs impact: update <DOC> because <reason> [or: no docs impact]
- Verification: <command>
```

Embed this inline plan in the worker prompt rather than in a separate sub-agent call.

---

## Worker Prompt (structured format)

Use sections instead of narrative prose. Sections reduce token waste, scope ambiguity, and the likelihood that the worker will add unrequested features.

```text
You are implementing exactly one bounded slice: **<SLICE_NAME>**.

Working directory: <REPO_ROOT>

## Scope

<2–3 sentence description of what this slice covers and why. Include what it explicitly does NOT cover.>

## Files to read first

Before writing anything, read these files to understand the current state:
- `<file_1>` — <why: what you need to understand from it>
- `<file_2>` — <why>
- `<file_3>` — <why>

## Exact changes

<numbered list of specific changes — one item per file or logical unit>

1. `<file>`: <what to add/change/remove>
2. `<file>`: <what to add/change/remove>
3. New file `<path>`: <what it should contain>

## Docs impact

<either: list which docs must be updated and why — treat these as mandatory if the repo has a docs-impact gate>
<or: "No docs impact — this slice does not change contracts, config, service boundaries, or workflow docs.">

## Verification

Run after implementation:
```
<verification commands>
```
All checks must pass before declaring done.

## Out of scope

Do NOT do any of the following in this slice:
- <item 1>
- <item 2>

## Report back

When done, report:
- Files created or changed
- Exit code of verification
- Any unexpected decisions you made and why
```

---

## Session Bootstrap Prompt

```text
Use $backlog-loop-orchestrator.

Run the long multi-session backlog loop for this repo.
Backlog source: <BACKLOG_FILE>
Read first: <DOC_LIST>
Log file: <LOG_FILE>

Work one bounded slice at a time:
planner sub-agent (or fast planning for simple slices) -> worker sub-agent -> verify -> commit -> continue.

Stop only for a real blocker, important ambiguity, or high-impact architecture tradeoff.
```

If the backlog is not execution-ready, do not silently repair it yourself. Recommend $delivery-planner first.
If the documentation foundation is too stale or too ambiguous to trust, recommend $agent-ready-docs first.

---

## Resume Prompt

```text
Use $backlog-loop-orchestrator.

Resume the long multi-session backlog loop for this repo.
Backlog source: <BACKLOG_FILE>
Log file: <LOG_FILE>

Before choosing the next slice:
- read the newest relevant log entries
- identify the last completed commit
- identify the first unfinished or blocked iteration
- continue from there instead of re-planning the whole backlog

Keep the same loop:
planning (full planner or fast) -> worker sub-agent -> verify -> commit -> continue.
```

---

## Optional Reviewer Prompt

```text
Use $slice-reviewer.

Review the just-implemented bounded slice before commit.
Read the approved slice plan first, then inspect the changed files, verification output, and any touched docs.

Return findings first, call out scope creep or missing verification, and finish with `accept`, `needs-fix`, or `blocked`.
```

---

## Optional Drift Audit Prompt

```text
Use $repo-drift-auditor.

Before continuing this multi-session backlog loop, audit whether the docs, backlog, and workflow assumptions behind it still match the current repo.
If they do, say the loop can continue.
If not, recommend the smallest correct next step.
```
