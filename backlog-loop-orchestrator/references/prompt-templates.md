# Prompt Templates

Use these as short skeletons, not rigid scripts.
Replace placeholders with repo-specific details.

## Planner Prompt

```text
Plan exactly one next bounded slice from `<BACKLOG_FILE>`.

Do not implement.
Do only discovery and planning.

Read first:
- <REPO_INSTRUCTIONS>
- <CORE_DOC_1>
- <CORE_DOC_2>
- <BACKLOG_FILE>

Context:
- last completed commit: <COMMIT>
- current loop goal: <GOAL>
- out of scope for this slice: <OUT_OF_SCOPE>

Tasks:
- identify the remaining candidate slices relevant now
- recommend exactly one next bounded slice
- explain why it is the best next candidate
- produce a decision-complete implementation plan
- identify files, checks, docs updates, and explicit deferred items

The plan must stay scoped to one slice only.
```

## Worker Prompt

```text
Implement exactly the approved slice below and nothing broader.

Approved slice:
<SLICE_SUMMARY>

Required context:
- <REPO_INSTRUCTIONS>
- <BACKLOG_FILE>
- <PLAN_SUMMARY>

Rules:
- keep scope bounded
- update docs/tests when the slice requires it
- run the agreed verification checks
- do not silently widen the slice
- if blocked by a real decision, stop and explain clearly
```

## Session Bootstrap Prompt

```text
Use $backlog-loop-orchestrator.

Run the long multi-session backlog loop for this repo.
Backlog source: <BACKLOG_FILE>
Read first: <DOC_LIST>
Log file: <LOG_FILE>

Work one bounded slice at a time:
planner sub-agent -> worker sub-agent -> verify -> commit -> continue.

Stop only for a real blocker, important ambiguity, or high-impact architecture tradeoff.
```

If the backlog is not execution-ready, do not silently repair it yourself. Recommend $delivery-planner first.
If the documentation foundation is too stale or too ambiguous to trust, recommend $agent-ready-docs first.

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
planner sub-agent -> worker sub-agent -> verify -> commit -> continue.
```

## Optional Reviewer Prompt

```text
Use $slice-reviewer.

Review the just-implemented bounded slice before commit.
Read the approved slice plan first, then inspect the changed files, verification output, and any touched docs.

Return findings first, call out scope creep or missing verification, and finish with `accept`, `needs-fix`, or `blocked`.
```

## Optional Drift Audit Prompt

```text
Use $repo-drift-auditor.

Before continuing this multi-session backlog loop, audit whether the docs, backlog, and workflow assumptions behind it still match the current repo.
If they do, say the loop can continue.
If not, recommend the smallest correct next step.
```
