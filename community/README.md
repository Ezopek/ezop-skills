# Community Skills

Third-party skills referenced by the skills in this repo. Copied here for convenience so the full toolkit lives in one place.

## Source

- **superpowers/** — from [superpowers](https://github.com/anthropics/claude-code-plugins) plugin v5.0.7
- **feature-dev/** — from [feature-dev](https://github.com/anthropics/claude-code-plugins) plugin

## Included Skills

### superpowers

| Skill | Used by |
|---|---|
| brainstorming | `$delivery-planner`, `$agent-ready-docs` |
| test-driven-development | `$backlog-loop-orchestrator` (worker TDD discipline) |
| systematic-debugging | All skills (when verification fails) |
| verification-before-completion | All skills (evidence before claims) |
| dispatching-parallel-agents | `$backlog-loop-orchestrator` (concurrent slices) |
| finishing-a-development-branch | `$backlog-loop-orchestrator` (loop completion) |
| writing-plans | `$delivery-planner` (task-level detail) |
| requesting-code-review | `$pr-reviewer` (self-review) |
| receiving-code-review | `$pr-reviewer` (handling feedback) |

### feature-dev

| Component | Used by |
|---|---|
| feature-dev (command) | `$delivery-planner` (feature discovery) |
| code-explorer (agent) | `$agent-ready-docs` (codebase understanding) |
| code-reviewer (agent) | `$pr-reviewer` (architecture-level review) |
| code-architect (agent) | `$delivery-planner` (architecture exploration) |

## Updates

These are point-in-time copies. To update, re-copy from `~/.claude/plugins/cache/claude-plugins-official/`.
