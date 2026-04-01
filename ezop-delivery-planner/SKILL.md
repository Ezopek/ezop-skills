---
name: ezop-delivery-planner
description: >-
  Create or update roadmap, backlog, and feature implementation planning docs
  for AI-driven software projects. Use when the user wants repo-grounded plans
  that are executable by developer agents, broken into bounded slices, explicit
  about verification and docs impact, and strong about surfacing unresolved
  decisions before finalizing the plan.
---

# Delivery Planner

## Overview

Use this skill when the user wants planning documents that are meant to drive real implementation work in an AI-native repo.
This includes:

- `ROADMAP.md`
- backlog files such as `docs/**/backlog*.md`
- feature implementation plans
- milestone plans
- architecture-adjacent execution plans

The goal is not to produce generic strategy prose.
The goal is to produce planning docs that:

- match the real state of the repo
- can be executed by developer agents one bounded slice at a time
- make dependencies, verification, docs impact, and risks explicit
- surface high-impact unresolved decisions early

This skill pairs especially well with:

- `$ezop-agent-ready-docs` when the documentation surface itself needs tightening
- `$ezop-backlog-loop-orchestrator` when the resulting backlog should be executed in an autonomous delivery loop
- `$ezop-repo-drift-auditor` when the current roadmap or backlog may no longer match the repo

Think of the intended handoff as:

1. `$ezop-agent-ready-docs` makes the repo instructions and doc map trustworthy
2. `$ezop-delivery-planner` turns that grounded context into roadmap, backlog, or feature-plan artifacts
3. `$ezop-backlog-loop-orchestrator` executes those artifacts one bounded slice at a time
4. `$ezop-slice-reviewer` can review each finished slice against the approved plan before commit
5. `$ezop-repo-drift-auditor` can periodically confirm that the docs and planning artifacts still match repo reality

## Quick Start

1. Read the repo instructions first, usually `AGENTS.md`, `README.md`, and the relevant operational docs.
2. Read the current plan documents that already exist.
3. Read the canonical code and workflow sources needed to verify the plan.
4. Identify whether the user needs a roadmap, backlog, or feature implementation plan.
5. Ask concise follow-up questions only for decisions that materially change scope, ordering, interfaces, architecture, or validation.
6. Write or update the smallest correct planning document instead of creating overlapping new files.

## Invocation Examples

Recommended Polish invocation:

```text
$ezop-delivery-planner przygotuj albo zaktualizuj plan wdrozenia dla tego repo.
Najpierw przeczytaj `AGENTS.md`, `README.md`, aktualne roadmapy i backlogi, a potem zweryfikuj obecny stan repo.
Jesli wykryjesz decyzje, ktore realnie zmieniaja scope, architekture, interfejsy albo kolejnosc prac, dopytaj mnie o nie przed finalizacja planu.
Plan ma byc repo-grounded, gotowy do wykonania przez agentow AI, i rozpisany na bounded slices z weryfikacja, docs impact i deferred items.
```

Recommended English invocation:

```text
$ezop-delivery-planner create or update an implementation plan for this repo.
Read `AGENTS.md`, `README.md`, the current roadmap and backlog docs, and then verify the current repo state.
If you detect decisions that materially change scope, architecture, interfaces, or sequencing, ask me about them before finalizing the plan.
The plan should be repo-grounded, executable by AI developer agents, and broken into bounded slices with verification, docs impact, and deferred items.
```

Minimal invocation:

```text
$ezop-delivery-planner turn this feature idea into a bounded implementation plan
```

Recommended paired invocation for backlog creation that will later be executed in a loop:

```text
$ezop-delivery-planner przygotuj backlog gotowy do wykonania przez `$ezop-backlog-loop-orchestrator`.
Jesli dokumentacja repo nie daje jeszcze stabilnego source-of-truth, zatrzymaj sie i powiedz, ze najpierw warto uzyc `$ezop-agent-ready-docs`.
```

## When To Use

Use this skill when:

- the user wants a roadmap or backlog created from the current repo state
- an existing backlog needs to be re-sliced into cleaner bounded steps
- a feature needs a decision-complete implementation plan before coding
- the repo needs planning docs that AI agents can execute safely
- the user wants explicit open questions and tradeoffs, not just a polished narrative

Do not use this skill when:

- the user only wants implementation with no planning artifact
- the repo context is unavailable
- the task is tiny enough that a planning doc would be overhead

## Core Principles

- Start from the repo, not from assumptions.
- Do not invent systems, commands, workflows, or architecture that do not exist.
- Prefer the smallest planning artifact that truthfully fits the work.
- Make plans executable by agents: bounded slices, explicit verification, explicit docs impact, explicit deferred scope.
- Ask the user only about decisions that are both high-impact and not discoverable from the repo.
- If a fact is discoverable locally, inspect first instead of asking.
- If external tooling, vendor APIs, or current best practices matter, verify from official or primary sources before encoding them into the plan.
- Do not hide uncertainty. Use `Assumptions`, `Open Questions`, and `Deferred` sections instead.
- Produce plans that future execution agents can follow without re-deciding the same fundamentals.

## Choose The Right Planning Artifact

Read [references/plan-types.md](references/plan-types.md) before drafting.

In general:

- use a roadmap for multi-milestone direction and ordering
- use a backlog for bounded delivery slices that are ready to be picked up
- use a feature implementation plan for one concrete change area that needs design and execution detail

If the user asks for a roadmap but really needs an implementation plan, say so and choose the tighter artifact.

## Discovery Workflow

### 1. Read The Existing Truth

Read:

- repo instruction files such as `AGENTS.md`
- top-level overview docs such as `README.md`
- the current roadmap/backlog/plan files
- canonical command and workflow sources such as `package.json`, `Makefile`, `turbo.json`, `.github/workflows/`
- the code or schema areas directly affected by the plan

### 2. Classify What Kind Of Plan Is Needed

Decide whether the user really needs:

- direction and prioritization
- bounded execution slices
- a decision-complete feature implementation plan
- or a combination where one doc should link to another instead of duplicating it

### 3. Detect High-Value Questions

Ask concise follow-up questions only when the answer changes one of these:

- scope boundary
- ownership between services or modules
- public API or contract shape
- migration strategy
- verification bar
- order of operations
- whether work should be split into multiple slices

Read [references/question-triggers.md](references/question-triggers.md) before asking.

### 4. Draft A Plan That Agents Can Execute

Make sure the plan includes only the level of detail that the artifact needs, but always keep it operational.
A good plan usually names:

- the exact objective
- current state
- bounded slices or phases
- files or systems likely to change
- verification path
- docs impact
- risks
- explicit deferred scope

For backlog artifacts intended for `$ezop-backlog-loop-orchestrator`, prefer items that already answer:

- why this slice is next
- what exact seam or area it covers
- what does not belong in the slice
- which verification path is enough
- which docs must move with the code

### 5. Finish With A Review Pass

Read [references/checklist.md](references/checklist.md) before finalizing.
Tighten vague language, remove hidden assumptions, and ensure the plan is still grounded in the actual repo.

## Writing Guidance By Artifact

### Roadmaps

Roadmaps should:

- show milestone ordering and rationale
- avoid pretending to be implementation-complete
- call out dependencies and sequencing constraints
- stay stable enough to guide multiple future slices

### Backlogs

Backlog items should:

- be independently executable
- avoid bundling multiple large themes
- describe acceptance and verification clearly
- be good inputs for `$ezop-backlog-loop-orchestrator`

### Feature Implementation Plans

Feature plans should:

- be decision-complete enough for a worker to execute
- spell out API, schema, testing, observability, and docs implications when relevant
- say what is in scope and out of scope
- call out architectural risks before implementation starts

## Relationship To Other Skills

Use `$ezop-agent-ready-docs` first or recommend it explicitly when:

- repo instructions are too weak to trust
- canonical docs are stale or duplicated
- command or ownership guidance is unclear enough to distort planning

Use `$ezop-repo-drift-auditor` first or recommend it explicitly when:

- the user suspects the backlog or roadmap is stale but the source of drift is unclear
- several slices landed since the last serious planning pass
- you need to know whether to repair docs first or re-plan the backlog first

When the user wants execution after planning:

- produce slices that are easy for `$ezop-backlog-loop-orchestrator` to run one at a time
- favor backlog wording that a planner sub-agent can turn directly into a decision-complete slice plan
- make deferred items explicit so the orchestrator does not accidentally widen scope
- make scope boundaries explicit enough that `$ezop-slice-reviewer` can judge whether implementation stayed inside them

When planning work exposes bad or stale documentation structure:

- update the relevant docs directly if the current task includes docs work
- or recommend `$ezop-agent-ready-docs` if the repo needs a broader documentation cleanup

## Output Expectations

Strong output from this skill usually includes:

- a short context summary
- the recommended artifact shape
- the proposed plan itself
- open questions only where they matter
- a clear `Now`, `Later`, and `Not now` boundary

Avoid:

- huge undifferentiated task dumps
- backlogs full of non-bounded items
- plans that skip verification and docs updates
- vague “future improvements” with no ordering logic

## Resources

- [references/plan-types.md](references/plan-types.md): choose the right planning document shape
- [references/question-triggers.md](references/question-triggers.md): when to ask the user before finalizing
- [references/checklist.md](references/checklist.md): quality bar for final plans
- [references/prompt-templates.md](references/prompt-templates.md): reusable prompts for roadmap, backlog, and feature-plan work
