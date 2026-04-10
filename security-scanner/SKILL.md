---
name: security-scanner
description: >-
  Audit repository security covering code patterns, dependency vulnerabilities,
  secret exposure, configuration weaknesses, and infrastructure security.
  Use when the user wants a findings-first security review before release,
  after incidents, during onboarding, or as a periodic health check.
---

# Security Scanner

## Overview

Use this skill when the user wants a systematic security audit of a repository's static content and configuration.
This is a security-auditing skill focused on static analysis of code, configuration, and dependencies. It does not perform penetration testing, dynamic analysis, or general code quality review.

It covers six scan surfaces:

- code patterns (injection, auth issues, insecure crypto, unsafe deserialization, SSRF)
- dependencies (CVEs, outdated packages, unmaintained libraries, license risks)
- secrets and credentials (hardcoded secrets, API keys, tokens, passwords, `.env` files)
- configuration (insecure defaults, CORS/CSP, debug mode, rate limiting, TLS)
- infrastructure as code (Terraform, Pulumi, CloudFormation, Kubernetes misconfigs)
- access control (file permissions, branch protection, repo permissions, MFA)

This skill works standalone or alongside related workflow skills:

- `$pr-reviewer` for PR-scoped security as part of broader quality review
- `$cicd-guardian` for pipeline-specific security (supply chain, action permissions, secrets management)
- `$slice-reviewer` for slice acceptance with security focus
- `$repo-drift-auditor` for detecting security posture drift over time

This skill does NOT do penetration testing or runtime analysis — it reviews static repo content and configuration.

## Announce At Start

When this skill activates, tell the user:

> Using **security-scanner** to [specific purpose based on the request].

## Quick Start

1. Identify the scan scope: full repository or a targeted area.
2. Read security-relevant configs, dependency manifests, and code.
3. Scan each surface systematically — do not skip surfaces.
4. Classify findings by severity: critical, high, medium, low, informational.
5. Report findings first with evidence (file paths, line references, config excerpts).
6. End with a security posture summary.

## Invocation Examples

Recommended Polish invocation:

```text
$security-scanner przeprowadz pelny audyt bezpieczenstwa tego repo.
Przeskanuj wzorce kodu, zaleznosci, sekrety, konfiguracje, IaC i kontrole dostepu.
Chce findings-first raport z severity, dowodami z plikow i rekomendacjami napraw.
```

Recommended English invocation:

```text
$security-scanner perform a full security audit of this repository.
Scan code patterns, dependencies, secrets, configuration, infrastructure as code, and access control.
I want a findings-first report with severity levels, file references, and recommended fixes.
```

Dependency-focused invocation:

```text
$security-scanner scan dependencies for known vulnerabilities, outdated packages, and license risks.
Check package.json, requirements.txt, go.mod, or equivalent manifests.
```

Pre-release security gate:

```text
$security-scanner perform a pre-release security review.
Focus on critical and high findings that would block a production release.
Include a go/no-go recommendation.
```

Targeted area scan (e.g., auth module):

```text
$security-scanner audit the authentication and authorization module for security vulnerabilities.
Focus on auth bypass, session management, token handling, and privilege escalation risks.
```

Minimal invocation:

```text
$security-scanner audit this repo for security vulnerabilities
```

## When To Use

Use this skill when:

- performing a pre-release security gate
- running a periodic security health check
- responding after a security incident to find related weaknesses
- onboarding to a new repo and assessing its security posture
- auditing dependencies for vulnerabilities and license risks
- preparing to publish code as open source

Do not use this skill when:

- the task is runtime debugging or performance investigation (use `superpowers:systematic-debugging`)
- the task is CI/CD pipeline audit (use `$cicd-guardian`)
- the task requires active penetration testing or dynamic analysis
- the task is a general code quality review without security focus (use `$pr-reviewer`)

## Core Principles

- Findings first, ordered by severity (critical, high, medium, low, informational).
- Evidence-based: every finding must reference a specific file, line, or configuration.
- No false confidence: if a surface cannot be fully audited, say so explicitly.
- Prefer verifiable findings over theoretical risks.
- Respect the threat model: a personal project needs different rigor than a financial API.
- Do not downplay findings; do not inflate them either.
- When in doubt about severity, err on the side of caution.
- Never expose or log actual secrets found during scanning.

## Scan Surfaces

Read [references/scan-surfaces.md](references/scan-surfaces.md) before large audits.
Read [references/checklist.md](references/checklist.md) before finalizing.

### Code Patterns

Look for:

- injection vulnerabilities: SQL injection, XSS, command injection, path traversal
- authentication and authorization issues: missing auth checks, broken access control, privilege escalation
- insecure cryptography: weak algorithms, hardcoded keys, improper random number generation
- unsafe deserialization: untrusted data deserialized without validation
- race conditions: time-of-check-to-time-of-use, concurrent state mutations without locks
- SSRF: server-side request forgery via user-controlled URLs

### Dependencies

Look for:

- known vulnerabilities (CVEs) in direct and transitive dependencies
- outdated packages with available security patches
- unmaintained dependencies (no updates in 2+ years, archived repos)
- license compliance risks (copyleft in proprietary code, incompatible licenses)
- typosquatting risk (package names similar to popular packages)

### Secrets And Credentials

Look for:

- hardcoded secrets, API keys, tokens, and passwords in code or config files
- `.env` files committed to the repository
- secrets visible in git history (even if removed from current HEAD)
- overly permissive `.gitignore` that fails to exclude sensitive files
- private keys, certificates, or credential files in the repo

### Configuration

Look for:

- insecure defaults left in production configurations
- overly permissive CORS or missing CSP headers
- debug mode enabled in production configs
- missing rate limiting on public endpoints
- weak TLS settings or outdated cipher suites
- verbose error messages exposing internals

### Infrastructure As Code

Look for:

- Terraform/Pulumi/CloudFormation/Kubernetes misconfigurations
- overly permissive IAM policies (wildcard permissions, admin access)
- public S3 buckets or storage with no access control
- missing encryption at rest or in transit
- security group issues (open ports, unrestricted ingress)
- missing logging and monitoring configuration

### Access Control

Look for:

- overly broad file permissions in the repo
- missing branch protection rules on main/production branches
- excessive GitHub/GitLab permissions for collaborators or tokens
- missing MFA requirements for repository access
- overly permissive CODEOWNERS or missing required reviewers

## Scan Workflow

### 1. Scope

- Identify what to scan: full repo, specific area, or specific surface.
- Understand the project type and threat model before starting.
- Check for existing security documentation or policies.

### 2. Inventory

- Map security-relevant files: auth modules, API endpoints, configs, IaC definitions, dependency manifests.
- Identify the tech stack and relevant vulnerability patterns.
- Note which surfaces are present and which are absent.

### 3. Systematic Scan

- Go through each applicable surface in order.
- Do not skip surfaces — if a surface has no findings, note that it was checked.
- Use language-specific and framework-specific patterns from [references/scan-surfaces.md](references/scan-surfaces.md).

### 4. Classify And Prioritize

- Assign severity to each finding: critical, high, medium, low, informational.
- Use the severity classification below consistently.
- Consider exploitability, impact, and the project's threat model.

### 5. Report

- Findings first, ordered by severity.
- Each finding includes: severity, description, file reference, evidence, recommended fix.
- End with scan coverage summary and security posture assessment.

## Severity Classification

### Critical

Actively exploitable, data breach risk, credential exposure.

Examples:

- hardcoded production database password in source code
- exposed AWS root credentials in `.env` committed to public repo
- authentication bypass allowing unauthenticated admin access
- SQL injection on a public endpoint with direct DB access

### High

Exploitable with moderate effort, significant impact.

Examples:

- SQL injection requiring specific input crafting
- missing authentication on admin API endpoint
- deserialization of untrusted data with known gadget chains
- overly permissive IAM policy with `*:*` on production resources

### Medium

Exploitable in specific conditions, moderate impact.

Examples:

- XSS in user input field with limited session access
- outdated dependency with known CVE that affects a used code path
- CORS configured to allow any origin on sensitive endpoints
- S3 bucket with public list permissions but no sensitive data

### Low

Minor risk, defense-in-depth concern.

Examples:

- verbose error messages exposing stack traces
- missing security headers on non-sensitive endpoints
- dependency with known low-severity CVE
- debug logging left enabled but not exposing secrets

### Informational

Best-practice recommendation, no direct risk.

Examples:

- CSP reporting could be enabled for better visibility
- dependency has a newer version available (no known CVE)
- security documentation could be more explicit
- rate limiting could be added to low-traffic internal endpoints

## Red Flags

Stop and reconsider if you catch yourself:

- Claiming the repo is secure without scanning all surfaces
- Reporting a CVE without checking if the vulnerable code path is actually used
- Logging or displaying actual secret values in findings
- Skipping dependency scanning because it takes effort
- Inflating severity to seem thorough
- Missing obvious hardcoded secrets because you focused only on code patterns
- Treating all repos the same regardless of their threat model
- Suggesting security fixes that break functionality without noting the tradeoff

## Safety Checks

- NEVER include actual secret values in the report — use redacted placeholders like `[REDACTED_API_KEY]`.
- If secrets are found in git history, warn about git history cleanup but do not attempt force-push.
- Do not run destructive remediation (like revoking tokens) without explicit user approval.
- Clearly separate verified findings from suspected risks.
- If a finding requires immediate action (exposed production credentials), flag it with urgency.

## Community Skill Integration

Use these community skills alongside this one when appropriate:

- `superpowers:systematic-debugging` — when a security finding needs root-cause investigation
- `superpowers:verification-before-completion` — verify that recommended fixes actually work before claiming resolution
- `$cicd-guardian` — for pipeline-specific security (supply chain, action permissions, secrets management)
- `$pr-reviewer` — for PR-scoped security review as part of broader quality check
- `$agent-ready-docs` — when security documentation or AGENTS.md security guidance needs updating
- `$repo-drift-auditor` — when security findings suggest documentation has drifted from actual security posture

## Relationship To Other Skills

Use this skill alongside `$pr-reviewer` when:

- a PR touches auth, data handling, or infrastructure and needs focused security review
- the PR reviewer wants a deeper security pass than a general quality check covers

Use this skill alongside `$cicd-guardian` when:

- pipeline security (supply chain attacks, action permissions, secrets in CI) needs dedicated audit
- the CI/CD pipeline handles deployment credentials or production access

Use this skill alongside `$slice-reviewer` when:

- a completed slice touches security-critical code and needs security-focused acceptance
- the slice introduces new auth flows, API endpoints, or infrastructure changes

Use this skill alongside `$repo-drift-auditor` when:

- security findings suggest the documented security posture no longer matches reality
- periodic security audit reveals drift from established security policies

Recommend `$agent-ready-docs` when:

- security policies or guidelines need to be documented or updated in AGENTS.md
- the repo lacks security documentation that agents should follow

Recommend `$delivery-planner` when:

- security remediation requires a multi-slice implementation plan
- findings are too numerous to fix in one pass and need prioritized backlog items

Recommend `$backlog-loop-orchestrator` when:

- a prioritized list of security fixes is ready for systematic execution

## Output Expectations

Strong output from this skill usually includes:

- `Findings` — severity-ordered, with file references and evidence for each finding
- `Scan Coverage` — which surfaces were checked and which were not applicable or skipped
- `Recommendations` — prioritized fixes, ordered by severity and effort
- `Security Posture Summary` — one-paragraph overall assessment of the repo's security state

If no findings are found: say so clearly and note which surfaces were scanned. Do not pad the report.

## Resources

- [references/scan-surfaces.md](references/scan-surfaces.md): detailed guide to each scan surface with language-specific patterns
- [references/checklist.md](references/checklist.md): pre-completion checklist for scan quality
- [references/prompt-templates.md](references/prompt-templates.md): reusable prompts for common security audit scenarios
