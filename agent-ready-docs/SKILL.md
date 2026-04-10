---
name: agent-ready-docs
description: >-
  Create or update AI-native repository documentation such as AGENTS.md,
  README.md, operational docs, and ADR-adjacent guidance so the repo stays easy
  for developer agents like Codex, Copilot, and Claude to manage. Use when the
  user wants docs that favor deterministic workflows, explicit architecture
  boundaries, verified commands, source-backed guidance, and clear warnings
  against inefficient or non-best-practice choices.
---

# Agent-Ready Docs

## Overview

Use this skill when the user wants to create, tighten, or refresh repository documentation for AI-driven development.
The main goal is to make the repo easy for developer agents to understand, verify, and evolve safely.

Strong output from this skill does four things:

- tells agents how to work in the repo with minimal ambiguity
- keeps commands, workflows, and architecture claims grounded in the actual repo
- tells agents to challenge weak, risky, or low-signal user instructions instead of silently following them
- tells agents to verify external guidance and prefer current best practices and sound architecture

This skill is the documentation foundation for the broader workflow:

- `$delivery-planner` should be able to trust the repo's doc map, workflow docs, and agent instructions after this skill runs
- `$backlog-loop-orchestrator` should be able to execute backlog slices with fewer hidden assumptions because the canonical docs are clear
- `$repo-drift-auditor` should be able to compare documented truth against repo reality without tripping over duplicated or ambiguous source-of-truth docs

## Announce At Start

When this skill activates, tell the user:

> Using **agent-ready-docs** to [specific purpose based on the request].

## Quick Start

1. Read the current repo instructions first, usually `AGENTS.md`, `README.md`, and the most relevant `docs/` files.
2. Read the canonical command and workflow sources before drafting docs, such as `package.json`, `Makefile`, `turbo.json`, `.github/workflows/`, service manifests, and contract definitions.
3. Identify which docs are the right source of truth for agent instructions, human overview, operational workflow, and architecture decisions.
4. Update only the smallest set of docs needed to make the guidance complete and consistent.
5. Keep the docs concise, operational, and easy for agents to search.

## Invocation Examples

Recommended Polish invocation:

```text
$agent-ready-docs zbuduj lub odswiez dokumentacje tego repo tak, aby bylo maksymalnie latwe do prowadzenia przez agentow developerskich.
Najpierw przeczytaj `AGENTS.md`, `README.md`, `package.json`, `Makefile` i najwazniejsze pliki z `docs/`.
Uaktualnij tylko te dokumenty, ktore naprawde powinny byc source of truth, zweryfikuj komendy z repo, i dopisz jasne zasady, ze agenci maja ostrzegac przed slabymi decyzjami i trzymac sie best practices.
```

Recommended English invocation:

```text
$agent-ready-docs create or refresh this repo's AI-native documentation so it is easy for developer agents to manage.
Read `AGENTS.md`, `README.md`, `package.json`, `Makefile`, and the key `docs/` files first.
Only update the documents that should be source of truth, verify commands against the repo, and add clear guidance that agents should warn about weak decisions and follow current best practices.
```

Minimal invocation:

```text
$agent-ready-docs tighten `AGENTS.md` and related workflow docs for AI-native development
```

Recommended paired invocation when preparing a repo for the full workflow:

```text
$agent-ready-docs przygotuj dokumentacyjny fundament pod `$delivery-planner` i `$backlog-loop-orchestrator`.
Uporzadkuj `AGENTS.md`, `README.md` i kluczowe docs operacyjne tak, aby backlogi, roadmapy i bounded slice execution mialy jasne source-of-truth.
```

## When To Use

Use this skill when:

- the user wants to create or improve `AGENTS.md`
- the repo needs AI-native workflow docs or a better documentation map
- the current docs are stale, vague, duplicated, or not grounded in real commands
- the repo should become easier for agentic tools to navigate and verify
- the user wants stronger architecture and best-practice guidance encoded into docs

Do not use this skill when:

- the task is only a tiny typo fix
- the user only wants code changes without documentation work
- there is no real repo context to inspect

## Core Principles

- Do not invent commands, workflows, service ownership, or architecture claims. Verify them from the repo first.
- Prefer a small set of canonical docs over duplicated instructions scattered across many files.
- Keep agent-facing instructions explicit about testing, docs updates, observability, contracts, and boundaries.
- Tell agents to challenge technically weak, risky, or inefficient requests and ask for explicit confirmation before taking the weaker path.
- When docs depend on external product or framework guidance, verify that guidance from official or primary sources before encoding it.
- Favor deterministic, non-interactive workflows that agents can run without guesswork.
- Keep docs concise enough that agents can load and apply them quickly.

## What Good Docs Usually Need

Most AI-native repos benefit from clearly separated responsibilities:

- `AGENTS.md` for repo-specific agent behavior, guardrails, verification habits, and architecture boundaries
- `README.md` for human-facing overview, setup, and canonical root commands
- `docs/operations/` for delivery workflow, operational practices, and agent collaboration patterns
- `docs/adr/` for durable architecture decisions that should not be buried in procedural docs
- service-level READMEs only when service-specific rules would otherwise clutter the root docs

Read [references/doc-map.md](references/doc-map.md) before large rewrites.
Use [references/checklist.md](references/checklist.md) as the review bar before finalizing docs.
Use [references/prompt-templates.md](references/prompt-templates.md) when the user wants a repeatable prompting pattern.

## Workflow

### 1. Build A Repo-Grounded Picture

- Read the current docs first.
- Read the actual command and workflow sources next.
- Identify stale, duplicated, or conflicting guidance.
- Identify which missing instructions are hurting agents the most.

### 2. Decide The Canonical Doc Surface

- Put stable repo-wide agent behavior in `AGENTS.md`.
- Put human onboarding and root command discovery in `README.md`.
- Put operational process in `docs/operations/`.
- Put big architecture decisions in ADRs when they deserve durable decision records.
- Avoid solving a documentation problem by adding three new files when one update is enough.

### 3. Encode AI-Native Guardrails

Make sure the docs tell agents to:

- keep the repo easy to search and verify
- prefer clear seams, versioned contracts, and modular service ownership
- update docs when workflows, architecture, contracts, config, or commands change
- add or update tests for behavior changes
- include observability expectations for new flows
- verify external docs when claims are time-sensitive, vendor-specific, or high-stakes
- warn the user when a requested path is weaker than an available best-practice alternative

### 4. Keep The Guidance Actionable

- Prefer explicit file paths, commands, and ownership statements.
- Prefer short rules over long essays.
- If a command is recommended, verify it exists.
- If a doc claims a service owns something, confirm the code layout supports it.
- If a workflow is described as canonical, confirm CI or scripts actually reflect that.

### 5. Finish With Consistency Checks

- Re-read the touched docs as a set, not one file at a time.
- Remove contradictions and low-value duplication.
- Make sure the doc map still makes sense.
- Make sure strong guidance did not drift into vague slogans.

## Collaboration With Other Skills

Use this skill to prepare the repo before heavier planning or looped execution when:

- `AGENTS.md` is too weak to guide agent behavior safely
- the canonical command surface is unclear
- backlog or roadmap files exist, but the surrounding docs are too stale to trust
- service ownership, architecture boundaries, or source-of-truth docs are ambiguous

After this skill finishes well:

- `$delivery-planner` should be able to create plans that rely on real doc ownership and real workflow entry points
- `$backlog-loop-orchestrator` should be able to read the backlog, trust the docs it depends on, and execute one slice at a time with fewer clarifying pauses
- `$repo-drift-auditor` should be able to confirm later that docs and workflows stayed aligned instead of first having to untangle the doc map

If the user asks for planning or orchestration but the documentation foundation is clearly not ready, say so directly and recommend starting with this skill first.

## External Verification

When documentation includes guidance tied to external tools, vendor APIs, current platform behavior, or evolving best practices:

- verify against official documentation or primary sources
- prefer current, stable recommendations over memory
- state when you are inferring rather than quoting a source
- avoid codifying outdated practices just because the repo used them before

## Output Expectations

Good edits from this skill usually:

- tighten `AGENTS.md` first when repo behavior needs better instructions
- update `README.md` only where human-facing command discovery or repo overview needs alignment
- update operations docs only where a workflow or process is truly canonical
- leave behind a repo that is easier for agents to navigate, not a bigger pile of prose

## Red Flags

Stop and reconsider if you catch yourself:

- Documenting commands you have not verified from the repo
- Writing long prose where a short rule would do
- Skipping the doc-map decision and dumping everything into one file
- Copying external documentation without checking if it is current
- Adding guidance that does not apply to this specific repo
- Improving docs the user did not ask you to touch
- Assuming a workflow exists without checking CI or scripts
- Generating an AGENTS.md from imagination instead of repo inspection

## Safety Checks

- Do not include secrets, tokens, passwords, or internal URLs in doc examples
- If docs reference destructive commands, add explicit warnings
- Verify recommended commands are safe to run repeatedly
- Do not expose private infrastructure details in public-facing docs

## Community Skill Integration

Use these community skills alongside this one when appropriate:

- `superpowers:brainstorming` — when doc restructuring involves creative decisions about information architecture
- `superpowers:verification-before-completion` — verify all documented commands actually work before claiming docs are complete
- `feature-dev:code-explorer` — when you need deep understanding of codebase architecture before writing architecture docs
- `$cicd-guardian` — when CI/CD pipeline documentation needs updating; let the guardian audit pipeline claims first
- `$security-scanner` — when security-related documentation needs grounding in actual security posture

## Resources

- [references/doc-map.md](references/doc-map.md): which doc should own which kind of guidance
- [references/checklist.md](references/checklist.md): review checklist for AI-native repo docs
- [references/prompt-templates.md](references/prompt-templates.md): reusable prompts for doc creation, refresh, and audit work
