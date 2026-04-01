# Checklist

Use this checklist before finishing a bounded-slice review.

## Slice Alignment

- I read the approved plan, backlog item, or accepted slice summary first.
- I know what was in scope and out of scope.
- I checked whether the implementation silently widened the slice.

## Correctness

- I inspected the changed seam, flow, or module boundary directly.
- I looked for interface or contract mismatches.
- I considered likely error or regression paths when relevant.

## Verification

- I checked which tests and verification steps were actually run.
- I judged whether those checks cover the changed behavior.
- I called out any meaningful missing verification.

## Documentation

- I checked whether docs should have moved with the change.
- I called out stale source-of-truth docs if needed.

## Output Quality

- Findings come first.
- Findings are ordered by severity.
- The final decision is explicit: `accept`, `needs-fix`, or `blocked`.
- If there are no findings, I say that clearly.
