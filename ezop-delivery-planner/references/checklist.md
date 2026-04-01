# Checklist

Use this before finalizing a roadmap, backlog, or feature plan.

## Repo Grounding

- The plan reflects the current repo structure and current docs.
- Commands and verification paths were checked against the repo.
- Claimed service or module ownership matches the codebase.
- Existing contracts, schemas, and workflows were inspected before planning changes.

## Planning Quality

- The artifact type is correct for the request.
- Scope is bounded and explicit.
- The plan is actionable for AI developer agents.
- Verification is specific, not hand-wavy.
- Docs impact is explicit where relevant.
- Deferred items are clearly separated from now-scope.

## Decision Quality

- High-impact unknowns were surfaced.
- Low-impact unknowns were not turned into unnecessary questions.
- Assumptions are explicit.
- Risks and blast radius are named honestly.

## Execution Readiness

- Backlog items are one-slice-at-a-time friendly.
- Feature plans include affected interfaces and tests where relevant.
- Roadmaps explain ordering and dependencies.
- The resulting plan could be handed to `$ezop-backlog-loop-orchestrator` without major rewriting.

## Final Review

- The plan is concise enough to scan quickly.
- The plan avoids duplicate truths across multiple docs.
- The `Now`, `Later`, and `Not now` boundary is clear.
