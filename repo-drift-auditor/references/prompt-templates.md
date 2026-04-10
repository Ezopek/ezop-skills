# Prompt Templates

Use these as starting points and adapt them to the repo and current concern.

## Periodic Repo Audit

```text
Use $repo-drift-auditor.

Audit whether this repo's docs, backlog, workflows, and actual implementation state have drifted apart.
Read the repo instructions, the main docs, the current roadmap or backlog files, and the canonical workflow sources first.

Return:
- findings first
- a short explanation of each drift mismatch
- a routing recommendation for the next skill
```

## Pre-Planning Audit

```text
Use $repo-drift-auditor.

Before I update the roadmap or backlog, audit whether the current docs and planning artifacts still match the repo.
If they do not, tell me whether I should run $agent-ready-docs or $delivery-planner next.
If they do, say that clearly.
```

## Pre-Resume Loop Audit

```text
Use $repo-drift-auditor.

Before resuming a long delivery loop, audit whether the docs, backlog, and workflow expectations still match the repo after recent commits.
If the repo is still aligned, say that $backlog-loop-orchestrator can proceed.
If not, route me to the smallest correct repair step first.
```
