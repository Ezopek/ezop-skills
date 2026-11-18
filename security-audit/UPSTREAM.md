# Upstream attribution and status

This folder vendors the `security-audit` skill from Cloudflare's security-audit-skill repository.

- Source: <https://github.com/cloudflare/security-audit-skill>, path `skills/security-audit`
- Pinned commit: `c1c8a8c1471069fb0e188eeaff69b8e8db6564a8` (2026-09-14)
- Pinned tree (provenance and history only): <https://github.com/cloudflare/security-audit-skill/tree/c1c8a8c1471069fb0e188eeaff69b8e8db6564a8/skills/security-audit>
- License: MIT, Copyright (c) 2025-2026 Cloudflare, Inc. The upstream license text is shipped here as `LICENSE.txt`, byte for byte (sha256 `e598e694aa506650c7192d5ea3be0e50aca0d356ea00551c53429f0b01eb6391`). Keep it when redistributing.

## What ships in this folder

- `LICENSE.txt`: the upstream repository's `LICENSE`, unchanged.
- Every other file of the upstream skill folder except the two validator test files, byte for byte, with one exception: the `description` line in the `SKILL.md` frontmatter.
- `UPSTREAM.md`: this note.

## The one local change

The upstream description invites the skill for any security question ("Use for security questions, focused reviews, vulnerability research, security audits, or pen tests"). Installed in a shared skills directory, that would load the whole guidance into every agent and session that touches security in passing. The description here asks for the skill only for an explicit full audit or when it is named. The body, including its guidance mode, is unchanged.

## What is not supplied

`validate-findings.test.cjs` and `validate-coverage-ledger.test.cjs` are the upstream tests of the two validators. The skill does not use them, so they are not copied. The upstream `README.md` is not copied either; this note and the repository README describe the folder.

## Notes from reading the pinned source

Nothing was executed to confirm these:

- `validate-findings.cjs` and `validate-coverage-ledger.cjs` need only Node.js. They use the `fs`, `path` and `util` modules to read the file they are given. They make no network calls, start no processes and write no files.
- The skill executes code of the audited target only inside an OS-enforced sandbox (no external network, read-only target, writes only to scratch). Without one, it reports such leads as `needs_validation` instead of running anything.
- It writes its run artifacts to a new directory outside the target, by default `~/security-audit-skill/<repo>/run-<N>`.

Updating to a newer upstream commit is a deliberate re-vendor: copy the folder again, re-apply the description change, update the pinned commit here, and review the diff.
