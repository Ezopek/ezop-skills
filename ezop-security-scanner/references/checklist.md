# Checklist

Use this checklist before finishing a security audit.

## Scan Coverage

- I scanned all applicable surfaces: code patterns, dependencies, secrets, configuration, IaC, access control.
- For each surface not scanned, I stated why (not applicable, out of scope, or could not be audited).
- I did not skip dependency scanning because it takes effort.
- I checked both the current HEAD and considered git history for secrets.

## Evidence Quality

- Every finding references a specific file, line, or configuration.
- I did not report theoretical risks without checking the actual code path.
- I checked whether reported CVEs affect code paths actually used by the project.
- I did not include actual secret values — only redacted placeholders.

## Severity Accuracy

- I used the severity classification consistently (critical, high, medium, low, informational).
- I considered the project's threat model when assigning severity.
- I did not inflate severity to seem thorough.
- I did not downplay findings to avoid alarming the user.
- When in doubt, I erred on the side of caution.

## Safety

- No actual secrets, tokens, passwords, or keys appear in my report.
- I did not attempt destructive remediation without user approval.
- I separated verified findings from suspected risks.
- I flagged any findings requiring immediate action with urgency.

## Output Quality

- Findings come first, ordered by severity.
- Each finding includes severity, description, file reference, evidence, and recommended fix.
- Scan coverage section lists all surfaces checked.
- Recommendations are prioritized by severity and effort.
- Security posture summary is honest and proportionate to the threat model.
- If no findings were found, I said so clearly.
