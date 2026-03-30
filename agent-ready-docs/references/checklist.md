# Checklist

Use this checklist before finishing AI-native documentation work.

## Repo Grounding

- Commands mentioned in docs exist and are spelled correctly.
- Claimed workflow entry points match `package.json`, `Makefile`, scripts, or CI.
- Service ownership claims match the actual repo layout.
- Contract or schema guidance matches the current source of truth.

## Agent-Facing Quality

- Docs tell agents where to start reading.
- Docs favor deterministic, non-interactive commands.
- Docs explain when to update tests, docs, contracts, and observability.
- Docs make important repo boundaries explicit.
- Docs tell agents to warn about weak, risky, or non-best-practice paths.

## Best-Practice Bar

- Docs do not codify obviously outdated workflows without explanation.
- External guidance was verified when tool, vendor, or platform advice matters.
- Architecture guidance favors clear seams and low hidden coupling.
- Docs avoid blessing convenience shortcuts that will hurt automation later.

## Scope And Clarity

- The touched docs are the smallest sensible set.
- Guidance is concise and actionable.
- Duplicate truths were removed or cross-linked.
- The docs map is still easy to understand.

## Final Review

- Read the changed docs together, not in isolation.
- Check for contradictions between `AGENTS.md`, `README.md`, and `docs/operations/`.
- Confirm that a new agent could find the canonical workflow quickly.
