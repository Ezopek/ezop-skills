---
name: cicd-guardian
description: >-
  Audit, improve, create, and secure CI/CD pipelines for any platform.
  Use when the user wants pipeline correctness verification, security
  hardening, performance optimization, or creation of new pipelines
  following current best practices for GitHub Actions, GitLab CI,
  Jenkins, or other CI/CD systems.
---

# CI/CD Guardian

## Overview

Use this skill when the user wants to audit, improve, create, or secure CI/CD pipelines.
Covers GitHub Actions, GitLab CI, Jenkins, Azure DevOps, Bitbucket Pipelines, CircleCI, and generic script-based CI/CD systems.

This skill works standalone or pairs with other workflow skills:

- `$agent-ready-docs` — document pipeline conventions and update docs after pipeline changes
- `$delivery-planner` — plan pipeline changes as bounded slices
- `$slice-reviewer` — review pipeline-related slices before commit
- `$repo-drift-auditor` — detect when pipeline definitions have drifted from documented CI/CD expectations
- `$security-scanner` — deep supply chain and dependency security analysis beyond pipeline scope

## Announce At Start

When this skill activates, tell the user:

> Using **cicd-guardian** to [specific purpose based on the request].

## Quick Start

1. Read existing pipeline files (`.github/workflows/`, `.gitlab-ci.yml`, `Jenkinsfile`, `azure-pipelines.yml`, `bitbucket-pipelines.yml`, `.circleci/config.yml`, `Makefile`, or equivalent).
2. Read `AGENTS.md`, `README.md`, and any docs that describe pipeline conventions or deployment expectations.
3. Identify the pipeline platform(s) in use and the project's build/test/deploy tooling.
4. Audit, create, or improve pipelines based on the user's request.
5. Verify pipeline syntax locally when possible (e.g., `actionlint`, `gitlab-ci-lint`, `jenkins-cli`).
6. Report findings or deliver changes with clear explanations.

## Invocation Examples

Recommended Polish invocation:

```text
$cicd-guardian zaudytuj pipeline'y CI/CD w tym repo pod katem bezpieczenstwa, poprawnosci i wydajnosci.
Najpierw przeczytaj istniejace pliki pipeline'ow, `AGENTS.md`, `README.md` i docs zwiazane z CI/CD.
Chce findings-first raport z priorytetem: bezpieczenstwo > poprawnosc > wydajnosc > styl.
```

Recommended English invocation:

```text
$cicd-guardian audit the CI/CD pipelines in this repo for security, correctness, and performance.
Read the existing pipeline files, `AGENTS.md`, `README.md`, and CI/CD-related docs first.
I want a findings-first report prioritized as: security > correctness > performance > style.
```

Minimal invocation for audit:

```text
$cicd-guardian audit this repo's CI/CD pipelines
```

Creation invocation:

```text
$cicd-guardian create a GitHub Actions pipeline for this project with lint, test, build, and deploy stages.
Follow current best practices for security, caching, and permissions.
```

Optimization invocation:

```text
$cicd-guardian optimize the CI/CD pipeline build times in this repo.
Focus on caching, parallelism, matrix strategies, and conditional execution.
```

Security hardening invocation:

```text
$cicd-guardian harden the CI/CD pipelines in this repo.
Pin all action versions to SHA, enforce least-privilege permissions, audit third-party actions, and check for injection risks.
```

## When To Use

Use this skill when:

- auditing existing CI/CD pipelines for correctness, security, or performance
- creating new pipelines for a project
- optimizing build and deployment times
- hardening pipeline security (permissions, secrets, supply chain)
- verifying that pipeline definitions match documented CI/CD expectations

Do not use this skill when:

- no CI/CD exists and the user does not want it
- the task is pure code review without pipeline involvement (use `$pr-reviewer`)
- the task is incident response or runtime debugging

## Core Principles

- Start from actual pipeline files, not assumptions.
- Verify syntax and structure before recommending changes.
- Prefer platform-native features over custom scripts where possible.
- Security by default: least privilege, pinned versions, secret management.
- Optimize for both speed and reliability, not just one.
- Pipeline changes should be tested before merge.
- Keep pipelines readable and maintainable.
- Document non-obvious pipeline decisions in comments.

## Supported Platforms

This skill covers platform-specific best practices for:

- **GitHub Actions** — `.github/workflows/*.yml`
- **GitLab CI** — `.gitlab-ci.yml`
- **Jenkins** — `Jenkinsfile` (declarative and scripted)
- **Azure DevOps** — `azure-pipelines.yml`
- **Bitbucket Pipelines** — `bitbucket-pipelines.yml`
- **CircleCI** — `.circleci/config.yml`
- **Generic** — `Makefile`, shell scripts, or other script-based CI/CD

Read [references/platform-patterns.md](references/platform-patterns.md) for platform-specific best practices and examples.

## Audit Workflow

### 1. Inventory

Find all pipeline definitions in the repo. Check standard locations for each platform.
Note any pipeline files referenced in docs but missing, or present but undocumented.

### 2. Structure Review

- Jobs, stages, and their dependencies
- Trigger conditions (push, PR, schedule, manual)
- Branch and path filters
- Reusable workflows, templates, or shared libraries
- Environment and variable declarations

### 3. Security Review

- Permissions scope (least privilege check)
- Secret handling (no hardcoded secrets, proper masking)
- Supply chain (pinned action/image versions, trusted sources)
- Trigger safety (`pull_request_target` injection risks, fork behavior)
- Third-party action/plugin audit
- OIDC and credential management

### 4. Performance Review

- Caching strategy (dependencies, build artifacts)
- Parallelism and matrix strategies
- Conditional execution (skip unnecessary jobs)
- Resource allocation (runner size, timeout settings)
- Artifact management (upload only what is needed)

### 5. Report Findings

Order findings by severity:

1. **Security** — vulnerabilities, overly broad permissions, unpinned actions
2. **Correctness** — broken triggers, missing steps, wrong dependencies
3. **Performance** — missing caching, sequential jobs that could parallelize
4. **Style** — naming, organization, readability

## Creation Workflow

When the user wants a new pipeline:

### 1. Identify Project Type And Platform

- Determine programming language, framework, and build system
- Confirm target CI/CD platform with the user if not obvious

### 2. Read Existing Project Structure

- Build system (`package.json`, `pom.xml`, `Cargo.toml`, `go.mod`, `Makefile`, etc.)
- Test framework and test commands
- Deployment target (cloud provider, container registry, static hosting)
- Existing scripts or automation

### 3. Design Pipeline Stages

Standard progression: **lint > test > build > deploy**

- Add security scanning stages when appropriate
- Include environment-specific deployment stages (staging, production)
- Add manual approval gates for production deployments

### 4. Apply Security Best Practices From The Start

- Pin all action/image versions to SHA
- Set least-privilege permissions
- Use platform secret management
- Enable dependency review where available

### 5. Include Caching And Parallelism

- Cache dependency directories
- Run independent jobs in parallel
- Use matrix strategies for multi-version testing

### 6. Document Pipeline In Repo Docs

- Update `README.md` with pipeline overview if appropriate
- Add comments in pipeline files for non-obvious decisions
- Document required secrets and environment setup

## Security Checklist

Critical items to verify on every audit or creation:

- Pin action/image versions to SHA, not tags (tags are mutable)
- Use least-privilege permissions (not `contents: write` when only `contents: read` is needed)
- Never hardcode secrets; use platform secret management
- Audit third-party actions/orbs/plugins before use (check maintainer, popularity, source)
- Protect deployment branches with required reviews
- Enable dependency review and vulnerability scanning
- Use OIDC for cloud authentication where possible (avoid long-lived credentials)
- Review workflow trigger conditions for injection risks (`pull_request_target` with PR checkout is dangerous)
- Ensure `GITHUB_TOKEN` permissions are scoped per job, not globally
- Verify that artifacts do not leak sensitive data

## Red Flags

Stop and reconsider if you catch yourself:

- Recommending pipeline changes without reading the existing pipelines first
- Using `permissions: write-all` or overly broad permissions
- Not pinning action versions to SHA
- Skipping syntax validation
- Suggesting secrets be stored in repo files
- Ignoring existing pipeline conventions in the repo
- Over-engineering pipelines for simple projects

## Safety Checks

- Never include real secrets or tokens in pipeline file examples
- Verify that recommended permissions are the minimum needed
- Flag any `pull_request_target` triggers with checkout of PR code (injection risk)
- Ensure deployment steps have appropriate environment protection rules
- Check for proper artifact signing and provenance where applicable
- Do not recommend removing security controls without explicit justification

## Community Skill Integration

Use these community skills alongside this one when appropriate:

- `superpowers:verification-before-completion` — verify pipeline syntax and test runs before claiming changes are complete
- `$agent-ready-docs` — when pipeline docs need updating after pipeline changes
- `$security-scanner` — for deep supply chain and dependency security beyond pipeline scope
- `$repo-drift-auditor` — when pipeline definitions have drifted from documented CI/CD expectations
- `$delivery-planner` — when pipeline changes should be planned as bounded slices

## Relationship To Other Skills

This skill is the CI/CD specialist in the broader workflow:

- `$agent-ready-docs` prepares the documentation foundation; this skill ensures pipeline docs within that foundation are accurate
- `$delivery-planner` may produce slices that involve pipeline changes; this skill verifies those changes are correct and secure
- `$backlog-loop-orchestrator` may execute slices that modify pipelines; this skill can audit the result
- `$repo-drift-auditor` detects drift broadly; this skill provides deep CI/CD-specific drift analysis and remediation
- `$slice-reviewer` reviews completed slices; this skill provides pipeline-specific review expertise
- `$security-scanner` handles broad security analysis; this skill focuses on pipeline and supply chain security specifically

When another skill detects a CI/CD issue, it should route to this skill for deep pipeline analysis.
When this skill detects issues outside CI/CD scope (code quality, broad security posture, documentation structure), it should route to the appropriate skill.

## Output Expectations

### For Audits

1. **Findings** — ordered by severity (security > correctness > performance > style), each with: what was found, why it matters, and the specific file and line where applicable
2. **Recommendations** — actionable fixes for each finding, with code examples when helpful
3. **Summary** — overall pipeline health assessment and prioritized next steps

### For Creation

1. **Pipeline files** — complete, working pipeline definitions ready to commit
2. **Documentation updates** — suggested changes to repo docs reflecting the new pipeline
3. **Verification instructions** — how to test the pipeline before merging

## Resources

- [references/checklist.md](references/checklist.md): pre-completion checklist for pipeline work
- [references/prompt-templates.md](references/prompt-templates.md): reusable prompts for audit, creation, hardening, and optimization
- [references/platform-patterns.md](references/platform-patterns.md): platform-specific best practices and examples
