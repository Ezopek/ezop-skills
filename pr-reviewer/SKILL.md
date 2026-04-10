---
name: pr-reviewer
description: >-
  Review pull requests and merge requests for code quality, security,
  performance, test coverage, and maintainability. Use when the user wants
  a thorough, findings-first quality review that goes beyond plan compliance
  to cover correctness, safety, and engineering standards.
---

# PR Reviewer

## Overview

Use this skill when the user wants a thorough code quality review of a pull request or merge request.
This is a general-purpose review skill. It is different from `$slice-reviewer`, which reviews one bounded slice against its approved plan.

This skill answers:

- Is the code correct?
- Is it safe?
- Is it performant?
- Is it maintainable?
- Is it well-tested?
- Does it follow project conventions?

It works as a standalone quality gate for any PR, or as a final quality pass after `$backlog-loop-orchestrator` completes a batch of work.

This skill fits into the ezop workflow pipeline:

- `$agent-ready-docs` makes repo guidance trustworthy
- `$delivery-planner` produces bounded slices or feature plans
- `$backlog-loop-orchestrator` runs plan -> implement -> verify cycles
- `$slice-reviewer` checks each slice against its approved plan
- `$repo-drift-auditor` can periodically confirm docs and backlog still match reality
- `$pr-reviewer` performs a broad quality, security, and maintainability review before merge
- `$cicd-guardian` can validate pipeline health and deployment readiness
- `$security-scanner` can do deep security-focused analysis of changes

## Announce At Start

When this skill activates, tell the user:

> Using **pr-reviewer** to [specific purpose based on the request].

## Quick Start

1. Read the diff and all changed files in the PR.
2. Read project conventions if present: `AGENTS.md`, linter configs, style guides, `.editorconfig`.
3. Check test output and verification results if available.
4. Review for correctness, security, performance, testing, and maintainability.
5. Report findings first, ordered by severity.
6. End with a clear decision: `approve`, `request-changes`, or `blocked`.

## Invocation Examples

Recommended Polish invocation:

```text
$pr-reviewer zrob review tego PR-a pod katem jakosci kodu, bezpieczenstwa, wydajnosci, testow i utrzymywalnosci.
Przeczytaj diff, konwencje projektu i wyniki testow.
Chce findings-first review z jasna decyzja `approve`, `request-changes` albo `blocked`.
```

Recommended English invocation:

```text
$pr-reviewer review this pull request for code quality, security, performance, test coverage, and maintainability.
Read the diff, project conventions, and test output.
I want a findings-first review with a clear `approve`, `request-changes`, or `blocked` decision.
```

Minimal invocation:

```text
$pr-reviewer review this PR
```

Paired invocation with security scanner:

```text
$pr-reviewer review this PR for quality and maintainability, then use $security-scanner for a deep security pass on the same diff.
```

## When To Use

Use this skill when:

- a PR or MR is ready for review before merging
- `$backlog-loop-orchestrator` has finished a batch and the result needs a broad quality check
- the user wants a manual code review covering more than plan compliance
- a quality gate is needed before release or deployment

Do not use this skill when:

- the task is plan compliance review for a bounded slice (use `$slice-reviewer`)
- there are no code changes to review
- the PR contains only documentation changes with no code impact

## Core Principles

- Findings first, ordered by severity.
- Review what is actually in the diff, not imagined code.
- Check security at every trust boundary.
- Verify tests cover changed behavior.
- Respect existing project conventions; do not impose external style.
- Separate blocking findings from nice-to-haves.
- If you cannot run verification, state the limitation.
- Prefer concrete evidence over subjective judgment.

## Review Dimensions

Read [references/review-dimensions.md](references/review-dimensions.md) for detailed guidance and examples.

### Correctness

- Logic errors, off-by-one, wrong conditions
- Edge cases and boundary conditions
- Error handling completeness
- Type safety and null/undefined handling
- Race conditions in concurrent code

### Security

- Injection vulnerabilities: SQL, XSS, command injection
- Authentication and authorization checks
- Hardcoded secrets or credentials
- Input validation at trust boundaries
- OWASP Top 10 patterns

### Performance

- N+1 queries and unnecessary database round-trips
- Unbounded loops or collections
- Memory leaks and resource cleanup
- Missing or broken caching
- Blocking operations on hot paths

### Testing

- Coverage of changed behavior
- Edge case and error path tests
- Regression tests for fixed bugs
- Test quality: meaningful assertions, not just coverage
- Integration tests where unit tests are insufficient

### Maintainability

- Readability and naming clarity
- Cyclomatic complexity
- Coupling between modules
- Code duplication
- Consistent patterns with the rest of the codebase

### Breaking Changes

- API compatibility: removed or renamed endpoints, fields, or parameters
- Database migration safety
- Configuration changes that affect existing deployments
- Deprecation notices and migration paths

### Documentation

- Docs that should move with the code: API docs, README updates, inline comments
- Changed behavior that users or operators need to know about
- New configuration options or environment variables

## Review Workflow

### 1. Understand Context

- Read the PR description, title, and linked issues.
- Read `AGENTS.md` or equivalent repo guidance if present.
- Identify the purpose and scope of the change.

### 2. Read The Full Diff

- Understand the full scope before judging individual details.
- Note which files, modules, and layers are touched.
- Identify the blast radius of the change.

### 3. Check Correctness And Security

- Inspect every changed function, method, or module.
- Trace data flow through changed code paths.
- Look for injection, auth bypass, and unsafe defaults.
- Check error handling and edge cases.

### 4. Check Testing And Coverage

- Are the right tests present for changed behavior?
- Do tests cover error paths and edge cases?
- Were existing tests updated when behavior changed?
- Is verification output available and honest?

### 5. Check Conventions And Maintainability

- Does the code match existing project patterns?
- Are naming, structure, and style consistent with the codebase?
- Is complexity reasonable for the task?
- Is there unnecessary duplication?

### 6. Produce The Review

- Findings first, ordered by severity.
- File references where useful.
- Assumptions or open questions if needed.
- Clear decision at the end.

## Decision Output

End the review with one of these:

- `approve`: no material findings; residual risk is low enough to merge
- `request-changes`: one or more findings must be resolved before merging
- `blocked`: the PR cannot be judged or merged without a missing decision, critical fix, or major correction

Do not hide a `request-changes` or `blocked` result behind soft language.

## Red Flags

Stop and reconsider if you catch yourself:

- Approving without reading the full diff
- Nitpicking style when there are correctness bugs
- Missing security issues in auth or data handling paths
- Suggesting rewrites that exceed the PR scope
- Rubber-stamping because the diff is small
- Reporting findings for code not changed in this PR
- Trusting test claims without checking verification output

## Safety Checks

Always check for these in every review:

- Flag any hardcoded secrets or credentials in the diff
- Flag SQL injection, XSS, command injection patterns
- Flag overly permissive CORS, CSP, or access control configurations
- Check for sensitive data in log statements
- Verify destructive operations have confirmation gates or rollback paths

## Community Skill Integration

Use these community skills alongside this one when appropriate:

- `superpowers:verification-before-completion` — verify claims before approving
- `superpowers:systematic-debugging` — when findings need root-cause investigation
- `superpowers:requesting-code-review` — for self-review before submitting
- `superpowers:receiving-code-review` — for handling review feedback
- `feature-dev:code-reviewer` — for deep architecture-level code analysis
- `$security-scanner` — for deep security-focused review
- `$slice-reviewer` — when review should also check plan compliance

## Relationship To Other Skills

Use this skill instead of `$slice-reviewer` when:

- the review should cover broad code quality, not just plan compliance
- there is no approved plan or backlog item to review against
- the PR includes multiple concerns beyond a single bounded slice

Use `$slice-reviewer` instead of this skill when:

- the focus is whether the implementation matches an approved plan
- scope creep and docs drift relative to a plan are the primary concerns

Recommend `$security-scanner` when:

- the PR touches authentication, authorization, data handling, or infrastructure
- security is the primary review concern rather than general quality

Recommend `$cicd-guardian` when:

- the PR changes CI/CD pipelines, deployment configs, or build scripts
- pipeline health and deployment readiness need validation

Recommend `$repo-drift-auditor` when:

- review findings suggest the repo docs or backlog are broadly out of sync
- the right fix depends on whether the repo is drifted, not just this PR

## Output Expectations

Strong output from this skill usually includes:

- `Findings` — ordered by severity, with file references
- `Assumptions` or `Open Questions` — only if needed
- `Decision` — explicit `approve`, `request-changes`, or `blocked`

If there are no findings, say so explicitly and mention any residual risk or limitation.

## Resources

- [references/checklist.md](references/checklist.md): pre-review checklist
- [references/prompt-templates.md](references/prompt-templates.md): reusable prompts for common review scenarios
- [references/review-dimensions.md](references/review-dimensions.md): detailed guide to review categories with examples
