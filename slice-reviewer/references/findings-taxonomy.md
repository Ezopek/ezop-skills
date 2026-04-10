# Findings Taxonomy

Use this guide to classify findings and keep reviews consistent.

## Priority Order

Prefer this order:

1. correctness bugs
2. regression risks
3. missing or misleading verification
4. scope creep
5. docs drift
6. lower-priority cleanup

## Common Finding Types

### Correctness Bug

Use when the implementation is likely wrong or inconsistent with the intended behavior.

Examples:

- response shape no longer matches the contract
- an error path is broken
- a migration step is incomplete
- changed logic silently alters behavior outside the agreed slice

### Regression Risk

Use when the change is plausible but fragile or unsafe.

Examples:

- a known failure path is no longer covered
- state or config coupling increases risk
- a boundary between services or layers became less clear

### Missing Verification

Use when acceptance is unsupported by the checks that were run.

Examples:

- no targeted test for a new endpoint or contract change
- only typecheck was run for a runtime behavior change
- verification output is missing for the most relevant path

### Scope Creep

Use when the implemented change widened beyond the approved slice.

Examples:

- unrelated refactors in the same diff
- multiple backlog items effectively merged into one slice
- a narrow seam migration grew into a broader model-family rewrite

### Docs Drift

Use when the code changed in ways that should have updated source-of-truth docs.

Examples:

- commands changed without doc updates
- contract or architecture guidance is now stale
- the backlog item was completed but the official planning docs were not updated

### Security Concern

Use when the change introduces or exposes a security risk.

Examples:

- authentication bypass or weakened authorization check
- hardcoded secrets or credentials in source code
- SQL injection, XSS, command injection, or other injection vulnerabilities
- insecure default configurations or overly permissive CORS
- missing input validation at trust boundaries
- logging sensitive data such as tokens, passwords, or PII

## Severity Guidance

Mark as materially blocking when the finding:

- can break behavior
- makes the slice misleadingly “green”
- widens scope enough to invalidate the slice boundary
- leaves official docs clearly wrong

If a finding is real but non-blocking, say so directly instead of inflating severity.
