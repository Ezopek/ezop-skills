# Routing Guidance

Use this guide to choose the next skill after a drift audit.

## Route To `$agent-ready-docs`

Use this when the main problem is:

- stale or contradictory source-of-truth docs
- weak or unclear repo instructions
- command and workflow docs that need repair
- architecture guidance that no longer matches the repo

## Route To `$delivery-planner`

Use this when the main problem is:

- stale roadmap or backlog structure
- items that need re-slicing or re-prioritization
- planning artifacts that no longer match the repo or each other
- feature plans that are too vague to execute safely

## Route To `$backlog-loop-orchestrator`

Use this when:

- no material drift was found
- the backlog is execution-ready
- repo docs are trustworthy enough for autonomous delivery

## Route To `$slice-reviewer`

Use this when:

- the repo is broadly aligned
- the real concern is one just-finished slice
- acceptance confidence depends on reviewing a specific change set, not repo-wide drift

## Route To `$cicd-guardian`

Use this when the main problem is:

- CI/CD pipeline definitions that have drifted from documented expectations
- build or deployment configurations that need audit or optimization
- pipeline security issues such as overly permissive permissions or missing secret rotation

## Route To `$security-scanner`

Use this when the main problem is:

- security-related drift in dependencies, configs, or code patterns
- authentication or authorization implementations that no longer match docs
- secret management or access control that needs audit

## Route To `$pr-reviewer`

Use this when:

- the drift is localized to a specific set of recent changes that need quality review
- code quality concerns are the primary issue rather than doc or backlog drift
- the audit found no systemic drift but one recent PR introduced problems
