# Doc Map

Use this map to decide where a rule or explanation should live.

## `AGENTS.md`

Best for:

- repo-specific instructions for developer agents
- coding, testing, verification, and docs-update expectations
- architecture guardrails and service ownership
- warnings about risky or low-quality implementation choices
- instructions to challenge weak user requests and ask for confirmation before weaker paths

Do not overload `AGENTS.md` with:

- long human onboarding walkthroughs
- detailed product background
- large architecture narratives better suited to ADRs

## `README.md`

Best for:

- project overview
- setup and first-run commands
- canonical repo-root workflows
- high-level documentation map

Do not use `README.md` as the only place for:

- nuanced agent behavior rules
- detailed architecture decisions
- long operational policy

## `docs/operations/`

Best for:

- delivery workflows
- AI-assisted development practices
- contract sync and verification flows
- CI expectations and operational runbooks

Keep these docs procedural and current.

## `docs/adr/`

Best for:

- meaningful architecture decisions with tradeoffs
- changes that should remain understandable months later
- decisions that should not be re-explained in procedural docs every time

## Service-Level Docs

Best for:

- service-specific commands, constraints, or integration rules
- local patterns that would be too noisy in root docs

Avoid service-level docs when the rule is actually repo-wide.

## Choosing The Smallest Correct Surface

Before editing, ask:

1. Which file should become the source of truth for this guidance?
2. Can another doc simply link to that source instead of duplicating it?
3. Does this change affect humans, agents, or both?
4. Is the guidance a process rule, an architecture decision, or a local service note?
