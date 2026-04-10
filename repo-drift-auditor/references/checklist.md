# Checklist

Use this checklist before finishing a drift audit.

## Evidence Quality

- I checked both the documented claim and the repo reality.
- I used concrete file or workflow evidence where possible.
- I avoided calling something drift when it is really just an open decision.

## Coverage

- I checked the highest-value docs first.
- I checked the canonical command and workflow sources.
- I checked the planning artifacts relevant to the requested area.
- I checked the most relevant code or schema seams behind those docs.

## Findings Quality

- Findings come first.
- Each finding explains the claim, the reality, and why the mismatch matters.
- Findings are ordered by severity or impact.
- If there is no meaningful drift, I say that clearly.

## Routing Quality

- I recommend the smallest correct next skill.
- I do not route to planning when the real issue is docs drift.
- I do not route to execution when backlog or workflow drift is still unresolved.
