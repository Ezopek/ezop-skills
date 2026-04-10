# Prompt Templates

Use these as starting points and adapt them to the repo and planning artifact.

## Roadmap Prompt

```text
Use $delivery-planner.

Create or update the roadmap for this repo.
Read `AGENTS.md`, `README.md`, the current roadmap docs, and the key operational docs first.
Then verify the current repo state before writing.

I want:
- a milestone-level roadmap
- realistic dependencies and ordering
- explicit deferred scope
- a shape that stays friendly for later AI-agent execution

Ask me only about the decisions that materially change milestones, architecture, or sequencing.
```

## Backlog Prompt

```text
Use $delivery-planner.

Create or update the backlog for this repo.
Read the existing backlog docs, repo instructions, and the canonical workflow files first.
Then inspect the relevant code and docs so the backlog matches the real current state.

I want:
- bounded slices
- explicit verification per slice
- clear docs impact
- output that works well with $backlog-loop-orchestrator

Ask me only about decisions that materially change slice boundaries, ownership, contracts, or rollout order.
```

## Planner For Later Orchestration

```text
Use $delivery-planner.

Create or update a backlog that is meant to be executed later by $backlog-loop-orchestrator.
Read the repo instructions, the current docs, and the existing backlog or roadmap first.
If the documentation foundation is too weak or too stale to support reliable planning, say so and recommend running $agent-ready-docs first.

I want:
- one bounded slice per backlog item
- explicit scope and non-goals
- clear verification
- clear docs impact
- explicit deferred follow-ups

Ask only the questions that materially change slice boundaries, interfaces, ownership, or rollout order.
```

## Feature Implementation Prompt

```text
Use $delivery-planner.

Turn this feature into a decision-complete implementation plan.
Read the repo instructions, current docs, and the relevant code paths first.
Then verify the current state before planning.

The plan should include:
- current state
- recommended approach
- affected files or systems
- interfaces and contracts
- verification
- docs impact
- deferred scope

Ask concise questions if unresolved choices materially change scope, architecture, interfaces, or migration strategy.
```

## Planning Audit Prompt

```text
Use $delivery-planner.

Audit the current roadmap/backlog/feature plan before changing it.
Check whether it is still grounded in the repo, whether slices are actually bounded, and whether the plan is executable by AI developer agents.

Then recommend the smallest plan updates needed.
```
