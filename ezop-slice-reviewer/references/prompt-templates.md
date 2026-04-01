# Prompt Templates

Use these as starting points and adapt them to the repo and slice.

## Pre-Commit Acceptance Review

```text
Use $ezop-slice-reviewer.

Review this single bounded slice before commit.
Read the approved backlog item or plan first, then inspect the changed files or diff, the verification output, and any touched docs.

I want:
- findings first
- focus on bugs, regressions, missing tests or checks, docs drift, and scope creep
- file references where useful
- a final decision: `accept`, `needs-fix`, or `blocked`
```

## Review Worker Output In A Loop

```text
Use $ezop-slice-reviewer.

Review the result of this worker-completed bounded slice for use inside $ezop-backlog-loop-orchestrator.
Check the implementation against the approved slice, then judge whether it is truly ready for commit.

If the slice definition is too weak, say so and recommend $ezop-delivery-planner.
If docs drift prevents trustworthy acceptance, say so and recommend $ezop-agent-ready-docs.
```

## Review Against A Feature Plan

```text
Use $ezop-slice-reviewer.

Review this implementation against its approved feature plan.
Focus first on whether the code actually matches the agreed design and boundaries, then on whether verification and docs are sufficient.

Return findings first and end with `accept`, `needs-fix`, or `blocked`.
```
