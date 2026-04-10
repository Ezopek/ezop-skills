# Checklist

Use this checklist before finishing a PR quality review.

## Context Understanding

- I read the PR description, title, and linked issues.
- I read `AGENTS.md` or equivalent repo guidance if present.
- I understand the purpose and scope of the change.
- I identified which modules, layers, and services are affected.

## Correctness

- I inspected every changed function and method.
- I traced data flow through changed code paths.
- I looked for logic errors, off-by-one, and wrong conditions.
- I checked error handling and edge cases.
- I considered race conditions in concurrent code when relevant.
- I verified type safety and null/undefined handling.

## Security

- I checked for hardcoded secrets or credentials.
- I looked for injection vulnerabilities: SQL, XSS, command injection.
- I verified authentication and authorization checks on changed paths.
- I checked input validation at trust boundaries.
- I looked for sensitive data in log statements.
- I checked for overly permissive CORS, CSP, or access control.
- I verified destructive operations have confirmation gates.

## Testing

- I checked whether tests cover the changed behavior.
- I looked for edge case and error path tests.
- I verified that changed behavior triggered test updates.
- I checked test quality: meaningful assertions, not just coverage.
- I reviewed verification output if available.

## Conventions

- I confirmed the code matches existing project patterns.
- I checked naming, structure, and style consistency.
- I looked for unnecessary duplication.
- I verified complexity is reasonable for the task.
- I checked for breaking changes to APIs, configs, or contracts.

## Output Quality

- Findings come first.
- Findings are ordered by severity.
- File references are included where useful.
- The final decision is explicit: `approve`, `request-changes`, or `blocked`.
- If there are no findings, I say that clearly with any residual risk noted.
