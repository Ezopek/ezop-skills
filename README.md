# ezop-skills

8 skills for AI-driven development — from repo setup, through planning, to autonomous execution, review, security, and CI/CD. Use standalone or together as a pipeline.

Works with Claude Code, GitHub Copilot, Cursor, Windsurf, OpenAI Codex, and any LLM agent that accepts system prompts.

---

## Skills

### Core Pipeline

| Skill | When to use |
|---|---|
| `$agent-ready-docs` | Create/update AGENTS.md, README.md, operational docs |
| `$delivery-planner` | Create roadmaps, backlogs, feature implementation plans |
| `$backlog-loop-orchestrator` | Autonomous backlog execution — loop slice by slice |
| `$slice-reviewer` | Review one slice against its approved plan before committing |
| `$repo-drift-auditor` | Audit docs/backlog vs. actual code for drift |

### Quality And Security

| Skill | When to use |
|---|---|
| `$pr-reviewer` | General-purpose PR/MR code quality review |
| `$cicd-guardian` | Audit, improve, create, and secure CI/CD pipelines |
| `$security-scanner` | Security audit — code, deps, secrets, config, infra |

---

## Recommended flow

```
[new repo / returning after a break]
        │
        ▼
$repo-drift-auditor        ← check whether docs/backlog have drifted
        │
        ▼
$agent-ready-docs          ← prepare AGENTS.md and repo documentation
        │
        ▼
$security-scanner          ← (optional) baseline security posture check
        │
        ▼
$delivery-planner          ← create backlog / roadmap / feature plan
        │
        ▼
$backlog-loop-orchestrator ← run loop: plan → implement → verify → commit
        │         ↑
        ▼         │
$slice-reviewer            ← (optional) accept each slice before committing
        │
        ▼
$pr-reviewer               ← quality gate before merge
        │
        ▼
$cicd-guardian             ← (optional) verify CI/CD is correct and secure
```

Each skill can be used standalone — the full pipeline is not required.

### When to use which reviewer

- **`$slice-reviewer`** — reviews one slice against its approved plan. Focus: did the implementation match the agreement?
- **`$pr-reviewer`** — reviews for general code quality. Focus: is the code correct, safe, performant, and maintainable?
- **`$security-scanner`** — deep security audit. Focus: are there vulnerabilities, exposed secrets, or insecure patterns?
- **`$cicd-guardian`** — CI/CD pipeline review. Focus: is the pipeline correct, secure, and optimized?

---

## Setup

See **[INSTALLATION.md](INSTALLATION.md)** for step-by-step setup instructions:

- **GitHub Copilot** — copy skill folders to `.github/skills/` in your project (native Agent Skills support)
- **Claude Code** — copy to `~/.claude/skills/` or install via plugins
- Works with VS Code, IntelliJ, and any tool that supports the [Agent Skills standard](https://agentskills.io)

---

## Example prompts

### Repo setup

```
# PL
Użyj $agent-ready-docs żeby przygotować AGENTS.md i README.md
dla tego repo — priorytet na bezpieczne instrukcje dla agentów,
zweryfikowane komendy i czytelne granice architektoniczne.

# EN
Use $agent-ready-docs to prepare AGENTS.md and README.md
for this repo — prioritize safe agent instructions, verified commands,
and clear architectural boundaries.
```

```
# EN
$agent-ready-docs -- tighten AGENTS.md, we added a new service layer
and the existing doc doesn't mention it at all
```

### Planning

```
# PL
$delivery-planner utwórz backlog dla migracji auth middleware
na nowy system sesji — podziel na bounded slices z weryfikacją dla każdego

# EN
$delivery-planner create a backlog for the auth middleware migration
to the new session system — split into bounded slices with explicit verification per slice
```

```
# EN
Use $delivery-planner to create a feature implementation plan for
adding rate limiting to the API — expose all open decisions before finalizing
```

### Autonomous execution

```
# PL
$backlog-loop-orchestrator uruchom pętlę backlogową — przeczytaj najpierw
AGENTS.md, prowadź log w .codex/ai-assisted-backlog-loop.md, jeden slice na raz

# EN
$backlog-loop-orchestrator run the backlog loop — read AGENTS.md first,
keep a log in .codex/ai-assisted-backlog-loop.md, one slice at a time
```

```
# EN
Resume the backlog loop — read the last entry in .codex/ai-assisted-backlog-loop.md
and continue from where we left off using $backlog-loop-orchestrator
```

### Slice review

```
# PL
$slice-reviewer przejrzyj ostatni diff względem zatwierdzonego planu,
sprawdź regressions, brakujące testy i docs drift — zakończ accept/needs-fix/blocked

# EN
$slice-reviewer review the latest diff against the approved plan,
check for regressions, missing tests, and docs drift — end with accept/needs-fix/blocked
```

```
# EN
Use $slice-reviewer to review the changes in the current branch against
backlog item #3 — findings first, severity order
```

### Drift audit

```
# PL
$repo-drift-auditor przeprowadź audyt przed wznowieniem pętli —
sprawdź czy AGENTS.md, backlog i komendy są nadal zgodne z kodem

# EN
$repo-drift-auditor run an audit before resuming the loop —
check whether AGENTS.md, backlog, and commands still match the code
```

```
# EN
Run $repo-drift-auditor — periodic check, we haven't touched this repo
in 2 weeks and want to make sure docs haven't drifted before planning next sprint
```

---

## Community skill integration

These ezop skills work well alongside community skills. The most valuable pairings:

| Community skill | When to use with ezop skills |
|---|---|
| `superpowers:brainstorming` | Before `$delivery-planner` for creative design exploration |
| `superpowers:writing-plans` | For detailed task-level plans within a single slice |
| `superpowers:test-driven-development` | Inside `$backlog-loop-orchestrator` for worker TDD discipline |
| `superpowers:systematic-debugging` | When verification fails in any skill |
| `superpowers:verification-before-completion` | Before every commit or acceptance claim |
| `superpowers:dispatching-parallel-agents` | When independent slices can run concurrently |
| `superpowers:finishing-a-development-branch` | After `$backlog-loop-orchestrator` completes all items |
| `feature-dev:feature-dev` | For full feature discovery before planning |
| `feature-dev:code-explorer` | For deep codebase understanding before docs or plans |
| `feature-dev:code-reviewer` | For architecture-level code analysis alongside `$pr-reviewer` |

Each ezop skill includes a **Community Skill Integration** section with specific recommendations.

---

## Tips

- **Always start from the repo** — all skills require real repository context; they don't generate docs from thin air.
- **Bounded slices** — plan work in small, independently executable units with explicit verification; this is the core assumption of the whole system.
- **Append-only log** — the backlog loop writes to `.codex/ai-assisted-backlog-loop.md`; don't delete it between sessions, it's the resume point.
- **Drift audit before resuming** — after a break of more than a few days, run `$repo-drift-auditor` first.
- **Slice reviewer is optional** — the backlog loop has it built in; invoke it separately only when you want a manual review pass.
- **PR reviewer vs. slice reviewer** — use slice-reviewer for plan compliance, pr-reviewer for general quality.
- **Security scanner early** — run `$security-scanner` early in the pipeline to establish a baseline; run again before releases.
- **CI/CD guardian** — run `$cicd-guardian` after significant pipeline changes or periodically to catch drift and security issues.
