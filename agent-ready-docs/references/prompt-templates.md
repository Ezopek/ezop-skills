# Prompt Templates

Use these as starting points and adapt them to the repo.

## Full Documentation Refresh

```text
Use $agent-ready-docs.

Refresh this repo's AI-native documentation.
Focus on `AGENTS.md`, `README.md`, and the most relevant files under `docs/`.

Goals:
- make the repo easier for developer agents to manage
- keep commands and workflows grounded in the actual repo
- encode clear guardrails around tests, docs, contracts, observability, and architecture
- ensure agents warn about weak or non-best-practice choices
- verify external guidance when it matters

Read the current docs first, then verify commands and workflows from the repo before editing.
Update only the smallest set of source-of-truth docs needed.
```

## AGENTS.md Tightening

```text
Use $agent-ready-docs.

Tighten `AGENTS.md` for this repo.
Make it explicit that developer agents should keep the repo easy for AI tools to manage, verify commands and docs against reality, prefer best practices, and warn the user when a requested path is weaker than a better alternative.

Read the current `AGENTS.md`, `README.md`, root workflow files, and the most relevant operational docs before editing.
```

## Documentation Audit Before Editing

```text
Use $agent-ready-docs.

Audit the current repo documentation for AI-native development quality before making changes.
Identify:
- stale or invented commands
- duplicated or conflicting instructions
- missing agent guardrails
- missing best-practice warnings
- missing guidance about verifying external documentation

Then recommend the smallest doc updates that would fix the biggest problems.
```

## Foundation For Planner And Orchestrator

```text
Use $agent-ready-docs.

Prepare this repo's documentation foundation for later use with $delivery-planner and $backlog-loop-orchestrator.
Tighten `AGENTS.md`, `README.md`, and the smallest relevant set of operational docs so they clearly define:
- canonical commands
- source-of-truth docs
- architecture and ownership boundaries
- documentation-update expectations
- how agents should respond to weak, risky, or non-best-practice requests

Verify the guidance from the repo before editing, and keep the result concise enough for future agents to rely on quickly.
```
