# Plan Types

Use this guide to choose the smallest correct planning artifact.

## Roadmap

Use a roadmap when the user needs:

- milestone-level direction
- ordered initiatives across multiple phases
- dependency and sequencing visibility
- a stable medium-term delivery narrative

A roadmap should not pretend to be slice-complete.
It should point to deeper backlog or feature-plan artifacts when needed.

Recommended sections:

- Purpose
- Current State
- Milestones or Phases
- Dependencies
- Risks
- Deferred or Out of Scope

## Backlog

Use a backlog when the user needs:

- bounded slices ready for implementation
- explicit acceptance and verification per slice
- a queue that can be executed incrementally by agents

Backlog items should be small enough to reason about and large enough to matter.
They should usually be good inputs for `$ezop-backlog-loop-orchestrator`.

Recommended fields per item:

- Title
- Why now
- Scope
- Non-goals
- Likely files or systems touched
- Verification
- Docs impact
- Deferred follow-ups

## Feature Implementation Plan

Use a feature implementation plan when the user needs:

- design detail for one feature or seam
- a decision-complete implementation path
- explicit API, contract, schema, migration, test, and observability notes

Recommended sections:

- Context
- Goal
- Current State
- Recommended Approach
- Files or Areas Affected
- Public Interfaces and Contracts
- Verification
- Risks
- Deferred Scope

## Choosing Between Them

Ask:

1. Is the user choosing direction across multiple milestones? Use a roadmap.
2. Is the user preparing execution-ready slices? Use a backlog.
3. Is the user planning one concrete feature in detail? Use a feature implementation plan.
4. Would a smaller artifact be more truthful than a bigger one? Prefer the smaller one.
