# Community Skills

Third-party skills referenced by ezop-* skills. Copied here for convenience so the full toolkit lives in one repo.

## Source

- **superpowers/** — from [superpowers](https://github.com/anthropics/claude-code-plugins) plugin v5.0.7
- **feature-dev/** — from [feature-dev](https://github.com/anthropics/claude-code-plugins) plugin

## Included Skills

### superpowers

| Skill | Used by |
|---|---|
| brainstorming | `$ezop-delivery-planner`, `$ezop-agent-ready-docs` |
| test-driven-development | `$ezop-backlog-loop-orchestrator` (worker TDD discipline) |
| systematic-debugging | All skills (when verification fails) |
| verification-before-completion | All skills (evidence before claims) |
| dispatching-parallel-agents | `$ezop-backlog-loop-orchestrator` (concurrent slices) |
| finishing-a-development-branch | `$ezop-backlog-loop-orchestrator` (loop completion) |
| writing-plans | `$ezop-delivery-planner` (task-level detail) |
| requesting-code-review | `$ezop-pr-reviewer` (self-review) |
| receiving-code-review | `$ezop-pr-reviewer` (handling feedback) |

### feature-dev

| Component | Used by |
|---|---|
| feature-dev (command) | `$ezop-delivery-planner` (feature discovery) |
| code-explorer (agent) | `$ezop-agent-ready-docs` (codebase understanding) |
| code-reviewer (agent) | `$ezop-pr-reviewer` (architecture-level review) |
| code-architect (agent) | `$ezop-delivery-planner` (architecture exploration) |

## Updates

These are point-in-time copies. To update, re-copy from `~/.claude/plugins/cache/claude-plugins-official/`.
