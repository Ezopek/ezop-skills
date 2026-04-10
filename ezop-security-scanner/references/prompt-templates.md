# Prompt Templates

Use these as starting points and adapt them to the repo and security concern.

## Full Repository Security Audit

```text
Use $ezop-security-scanner.

Perform a full security audit of this repository.
Scan all six surfaces: code patterns, dependencies, secrets, configuration, infrastructure as code, and access control.

Return:
- findings first, ordered by severity
- file references and evidence for each finding
- scan coverage summary
- recommended fixes prioritized by severity
- one-paragraph security posture summary
```

## Dependency Vulnerability Scan

```text
Use $ezop-security-scanner.

Scan this repo's dependencies for security vulnerabilities.
Check package.json, requirements.txt, go.mod, Gemfile, pom.xml, or equivalent manifests.
Look for known CVEs, outdated packages with security patches, unmaintained dependencies, and license compliance risks.

Return findings with:
- CVE identifiers where applicable
- affected package name and version
- whether the vulnerable code path is actually used
- recommended upgrade path or alternative
```

## Pre-Release Security Gate

```text
Use $ezop-security-scanner.

Perform a pre-release security review of this repository.
Focus on critical and high severity findings that would block a production release.
Check for exposed secrets, injection vulnerabilities, auth bypasses, and insecure infrastructure.

Return:
- findings first, with severity and evidence
- a clear go/no-go recommendation for release
- blocking issues that must be fixed before release
- non-blocking issues that should be tracked for follow-up
```

## Targeted Area Security Review

```text
Use $ezop-security-scanner.

Audit the [target area, e.g., authentication module, payment processing, API gateway] for security vulnerabilities.
Focus on:
- [area-specific concerns, e.g., auth bypass, session management, token handling]
- input validation at trust boundaries
- error handling that might expose internals
- any hardcoded credentials or secrets

Return findings first with file references and recommended fixes.
```

## Post-Incident Security Assessment

```text
Use $ezop-security-scanner.

After a security incident involving [brief description], audit this repository for related vulnerabilities.
Focus on:
- the attack vector and whether similar patterns exist elsewhere
- whether the fix is complete and does not introduce new issues
- related weaknesses in the same code area or module
- secrets that may have been exposed and need rotation

Return:
- findings related to the incident first
- broader findings that the incident exposed
- remediation completeness assessment
- recommended follow-up actions
```
