# Drift Surfaces

Use this guide to focus the audit on the places where drift creates the most delivery pain.

## Documentation Drift

Check whether:

- `AGENTS.md` still reflects current repo expectations
- `README.md` still points to real setup and verification commands
- `docs/operations/` still matches the active workflow
- service-level docs still match actual boundaries and commands

## Backlog And Roadmap Drift

Check whether:

- backlog items still describe work that is actually unfinished
- already-completed work is still listed as pending
- items have become too broad or stale after earlier slices landed
- roadmap sequencing still matches current priorities and dependencies

## Command And Workflow Drift

Check whether:

- documented commands still exist
- canonical paths in docs still match `package.json`, `Makefile`, `turbo.json`, or scripts
- CI expectations in docs still match `.github/workflows/`

## Architecture And Ownership Drift

Check whether:

- docs still assign responsibilities to the same service or module that now owns them
- new seams or migrations changed where source of truth lives
- ADRs or architecture notes are now contradicted by the code

## Contract Drift

Check whether:

- shared contract docs still match real schemas and generators
- source-of-truth claims still point to the right package or file
- generated artifacts mentioned in docs still exist and are current
