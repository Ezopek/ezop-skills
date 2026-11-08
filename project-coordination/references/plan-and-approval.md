# Plan and approval

Read this when writing or reviewing a plan, before executing a slice, and before asking the operator to approve or perform an action.

## Plan

A plan exists only after the operator chose an option (a D). Keep it short; its length follows the change, not the ceremony. It is frozen once accepted: later changes are D entries.

Slices are independently verifiable and reversible, or named one-way behind their own gate. Each slice has:

- **Changes**, and what is deliberately not changed.
- **Local checks** to run before anything leaves the workspace.
- **Operator steps** as exact copy-paste commands. Every name in a command is checked against the system that consumes it (identifiers versus display names).
- **Post-checks** that show the change took effect.
- **Rollback** that is tested or at least read at the source.
- **Done when** it is true, in terms someone else can check.

**Acceptance criteria (A ids)** are measurable, and an empty result counts as failure.

**Gates (G ids)** exist only where work stops for a decision of its own: the first production action, another team's dependency, a scope choice. Never create a gate for a step an approval card already covers.

## Change map

The change map lists every element the topic adds, changes or removes, and is created with the plan. Each row (M id) says: where (repository, path or resource), new, changed or removed, why (C or D ids), depends on, status per environment, PR, who maintains it, how to check it, how to undo it. Secrets appear by name only, never by value. Update it with each slice, PR and rollout; it is the answer to "what is live".

## Plan review

An independent reviewer, never the author, preferably from a different model family. The reviewer writes nothing in the dossier; the coordinator records the verdict, or routes the review output straight into the round file.

- Findings are leads. Verify each at the source, then fix it or push back with evidence, and record the disposition.
- Effort follows rollback cost: cheap rollback, one full round plus one confirmation round limited to the fixes; otherwise rounds until accepted.
- Wording, cross-reference and map-versus-plan mismatches are minor: fix them without a new round.
- A finding whose fix would add a mechanism that no C, D or binding rule requires is a question to the operator first, with "accept or document the risk" as the first option. A defect found only inside such an unrequested mechanism is answered by removing the mechanism, not hardening it.
- Acceptance of a limited round covers only what that round examined.

## Execution

Per slice: an author worker in its own worktree or branch; independent code review until accepted, each rework round going to a fresh author briefed with the findings; the real-data check below before production; then you verify the outcome yourself with tests and read-only post-checks, because the author's word is not enough. Update the change map. Details of roles and returns: `team-and-review.md`.

## Real-data check before production

Run it where the data is. Choose one:

- an execution test outside production on production data or a copy;
- the change applied to one target before the rest;
- a read-only simulation over recent production data, counting what the change would have done.

It passes only with a **positive control**: a known event (a past incident, an existing alert firing) is reproduced, and every extra or missing result is explained. Zero results is not a pass. A rendered output (dashboard, notification) is checked as rendered, not by counts. If no known event exists, no test is possible, or there is no authorised access to the data, say why and what risk remains; the operator decides (a D).

## Approval card

Before every action the operator approves or performs (merge, apply or deploy, sync, a command on a live system, creating a key or secret, publishing), give a card in the turn's final message, in the operator's language:

1. **Action** and target system or environment.
2. **Effect** in one sentence, with M ids.
3. **Also applied**, only for a shared repository applied whole: other topics' merged-but-unapplied changes that go out with it.
4. **Risk**, and reversible: yes, no or partly.
5. **Second pair of eyes**: the review verdict with the reviewer's model family, or "no review - operator decision"; a human reviewer or "none".
6. **Real-data check** result, or why none is possible and what risk remains.
7. **Post-check.**
8. **Rollback.**

A reversible action outside production and pre-production gets the short card: action, effect, second pair of eyes, rollback. The same card opens the description of every pull request you open for the topic. Ordinary steps the grant already covers need no card. Never ask for approval per step, per comment or per edit.

Example (short card, synthetic):

```text
Action: merge PR 57 into main of invoice-sync (no deploy).
Effect: retry limit raised from 3 to 5 ([M2](https://example.org/dossiers/20260303-invoice-sync/02-change-map.md#m2)).
Second pair of eyes: review APPROVE, model family B; human reviewer none.
Rollback: revert the merge commit.
```

Cards are read by the operator, so IDs in them are links; see `dossier.md`.
