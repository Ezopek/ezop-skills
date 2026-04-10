# Prompt Templates

Use these as starting points and adapt them to the repo and current concern.

## Pipeline Audit

```text
Use $ezop-cicd-guardian.

Audit the CI/CD pipelines in this repo for security, correctness, and performance.
Read all pipeline files, `AGENTS.md`, `README.md`, and CI/CD-related docs first.

Return:
- findings ordered by severity (security > correctness > performance > style)
- actionable recommendations for each finding
- a summary of overall pipeline health
```

## New Pipeline Creation

```text
Use $ezop-cicd-guardian.

Create a CI/CD pipeline for this project.
Read the project structure first: build system, test framework, deployment target.

Requirements:
- stages: lint, test, build, deploy
- pin all action/image versions to SHA
- use least-privilege permissions
- configure dependency caching
- include a manual approval gate for production deployment
- document required secrets and setup instructions
```

## Security Hardening

```text
Use $ezop-cicd-guardian.

Harden the CI/CD pipelines in this repo.
Focus on:
- pinning all action/image versions to SHA (replace tag references)
- enforcing least-privilege permissions on every job
- auditing all third-party actions for trustworthiness
- checking for injection risks in triggers and expressions
- verifying secret management practices
- enabling OIDC where long-lived credentials are currently used

Deliver a findings report and a hardened version of each pipeline file.
```

## Performance Optimization

```text
Use $ezop-cicd-guardian.

Optimize the CI/CD pipeline build times in this repo.
Focus on:
- dependency caching (correct cache keys, cache hit rates)
- job parallelism (split sequential jobs that can run in parallel)
- matrix strategies (multi-version testing)
- conditional execution (skip unnecessary jobs based on changed files)
- artifact management (upload only what is needed)
- runner resource allocation

Deliver specific time-saving recommendations with estimated impact.
```

## Pipeline Documentation Refresh

```text
Use $ezop-cicd-guardian.

Review the CI/CD pipelines in this repo and refresh the related documentation.
Compare pipeline definitions against what docs currently claim about CI/CD.

Deliver:
- a list of documentation gaps or inaccuracies
- updated documentation text for pipeline stages, required secrets, and deployment process
- inline comment suggestions for non-obvious pipeline decisions

If documentation drift is severe, recommend $ezop-agent-ready-docs for a broader docs refresh.
```
