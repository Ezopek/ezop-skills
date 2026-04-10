# Prompt Templates

Use these as starting points and adapt them to the repo and PR.

## Standard PR Review

```text
Use $pr-reviewer.

Review this pull request for code quality, security, performance, test coverage, and maintainability.
Read the diff, project conventions, and test output.

I want:
- findings first, ordered by severity
- focus on correctness, security, performance, testing, and maintainability
- file references where useful
- a final decision: `approve`, `request-changes`, or `blocked`
```

## Security-Focused PR Review

```text
Use $pr-reviewer.

Review this pull request with extra emphasis on security.
Check for injection vulnerabilities, auth issues, hardcoded secrets, input validation gaps, and unsafe defaults.

After the quality review, recommend whether $security-scanner should do a deeper security pass.

I want:
- security findings first, then other quality findings
- OWASP Top 10 coverage where relevant
- a final decision: `approve`, `request-changes`, or `blocked`
```

## Pre-Merge Quality Gate After Backlog Loop

```text
Use $pr-reviewer.

$backlog-loop-orchestrator just completed a batch of work. Review the resulting PR as a final quality gate before merge.
The individual slices were already reviewed by $slice-reviewer for plan compliance.

Focus on:
- cross-slice integration issues
- overall code quality and consistency
- security and performance across the full change set
- test coverage for the combined behavior

I want findings first and a clear `approve`, `request-changes`, or `blocked` decision.
```

## Quick Review For Small Changes

```text
Use $pr-reviewer.

This is a small PR. Do a focused review covering correctness, security, and test coverage.
Skip deep maintainability and performance analysis unless something stands out.

I want a concise findings-first review with a clear decision.
```
