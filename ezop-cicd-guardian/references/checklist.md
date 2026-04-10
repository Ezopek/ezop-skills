# Checklist

Use this checklist before finishing CI/CD pipeline work.

## Pipeline Structure

- All jobs have correct dependency declarations (needs, stages, depends_on).
- Triggers are appropriate for the pipeline purpose (push, PR, schedule, manual).
- Branch and path filters are set correctly.
- Pipeline stages follow a logical progression (lint > test > build > deploy).
- Reusable workflows or templates are used where duplication exists.
- Timeout values are set to prevent stuck jobs.

## Security

- All action/image versions are pinned to SHA, not mutable tags.
- Permissions follow least privilege (no `write-all`, no unnecessary `contents: write`).
- No secrets are hardcoded in pipeline files.
- Third-party actions and plugins have been reviewed for trustworthiness.
- `pull_request_target` triggers do not checkout PR code unsafely.
- OIDC is used for cloud authentication where available.
- `GITHUB_TOKEN` permissions are scoped per job.
- Deployment branches have required review protections.
- Artifacts do not contain or leak sensitive data.

## Performance

- Dependency caching is configured and cache keys are correct.
- Independent jobs run in parallel where possible.
- Matrix strategies are used for multi-version or multi-platform testing.
- Conditional execution skips unnecessary jobs (path filters, changed-files checks).
- Artifact uploads are limited to what downstream jobs or users need.
- Runner resources match workload requirements.

## Documentation

- Pipeline purpose and stages are documented in repo docs or pipeline comments.
- Required secrets and environment variables are listed (not the values, just names).
- Manual steps or prerequisites are documented.
- Non-obvious pipeline decisions have inline comments.
- Deployment process and environment promotion are documented.

## Output Quality

- Findings are ordered by severity (security > correctness > performance > style).
- Each finding includes: what, why it matters, and where (file and line).
- Recommendations are actionable with code examples when helpful.
- Pipeline files are syntactically valid.
- No real secrets or tokens appear in examples or pipeline files.
- Created pipelines have been tested or include verification instructions.
