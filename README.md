# ezop-skills

5 skills for AI-driven development — from repo setup, through planning, to autonomous execution and review. Use standalone or together as a pipeline.

---

## Skills

| Skill | When to use |
|---|---|
| `$ezop-agent-ready-docs` | Create/update AGENTS.md, README.md, operational docs |
| `$ezop-delivery-planner` | Create roadmaps, backlogs, feature implementation plans |
| `$ezop-backlog-loop-orchestrator` | Autonomous backlog execution — loop slice by slice |
| `$ezop-slice-reviewer` | Review one slice before committing |
| `$ezop-repo-drift-auditor` | Audit docs/backlog vs. actual code for drift |

---

## Recommended flow

```
[new repo / returning after a break]
        │
        ▼
$ezop-repo-drift-auditor        ← check whether docs/backlog have drifted
        │
        ▼
$ezop-agent-ready-docs          ← prepare AGENTS.md and repo documentation
        │
        ▼
$ezop-delivery-planner          ← create backlog / roadmap / feature plan
        │
        ▼
$ezop-backlog-loop-orchestrator ← run loop: plan → implement → verify → commit
        │         ↑
        ▼         │
$ezop-slice-reviewer            ← (optional) accept each slice before committing
```

Each skill can be used standalone — the full pipeline is not required.

---

## How to invoke skills

### Claude Code (CLI)
The `$skill-name` prefix and slash commands are recognized automatically:
```
$ezop-delivery-planner create a backlog for feature X
```
```
/ezop-delivery-planner
```

### Claude (Anthropic) — Projects / API
Paste the contents of `SKILL.md` as a system prompt or attach it as a document in your Project. Then reference the skill by `$name` in your message.

### OpenAI Codex / Custom GPT
Each skill includes `agents/openai.yaml` — import it as an Action or paste the description into a GPT system prompt. The `default_prompt` field in the yaml is a ready-made starter.

### Copilot / Cursor / Windsurf
Paste `SKILL.md` into `.cursorrules`, `AGENTS.md`, or the conversation context. Then reference the skill via `$ezop-<name>` in your agent prompts.

### Any agent (generic)
Each skill is a self-contained prompt — just:
1. Paste `SKILL.md` content into the system / context
2. Call it via `$ezop-<name>` or the full skill name

---

## Example prompts

### Repo setup

```
# PL
Użyj $ezop-agent-ready-docs żeby przygotować AGENTS.md i README.md
dla tego repo — priorytet na bezpieczne instrukcje dla agentów,
zweryfikowane komendy i czytelne granice architektoniczne.

# EN
Use $ezop-agent-ready-docs to prepare AGENTS.md and README.md
for this repo — prioritize safe agent instructions, verified commands,
and clear architectural boundaries.
```

```
# EN
$ezop-agent-ready-docs -- tighten AGENTS.md, we added a new service layer
and the existing doc doesn't mention it at all
```

### Planning

```
# PL
$ezop-delivery-planner utwórz backlog dla migracji auth middleware
na nowy system sesji — podziel na bounded slices z weryfikacją dla każdego

# EN
$ezop-delivery-planner create a backlog for the auth middleware migration
to the new session system — split into bounded slices with explicit verification per slice
```

```
# EN
Use $ezop-delivery-planner to create a feature implementation plan for
adding rate limiting to the API — expose all open decisions before finalizing
```

### Autonomous execution

```
# PL
$ezop-backlog-loop-orchestrator uruchom pętlę backlogową — przeczytaj najpierw
AGENTS.md, prowadź log w .codex/ai-assisted-backlog-loop.md, jeden slice na raz

# EN
$ezop-backlog-loop-orchestrator run the backlog loop — read AGENTS.md first,
keep a log in .codex/ai-assisted-backlog-loop.md, one slice at a time
```

```
# EN
Resume the backlog loop — read the last entry in .codex/ai-assisted-backlog-loop.md
and continue from where we left off using $ezop-backlog-loop-orchestrator
```

### Slice review

```
# PL
$ezop-slice-reviewer przejrzyj ostatni diff względem zatwierdzonego planu,
sprawdź regressions, brakujące testy i docs drift — zakończ accept/needs-fix/blocked

# EN
$ezop-slice-reviewer review the latest diff against the approved plan,
check for regressions, missing tests, and docs drift — end with accept/needs-fix/blocked
```

```
# EN
Use $ezop-slice-reviewer to review the changes in the current branch against
backlog item #3 — findings first, severity order
```

### Drift audit

```
# PL
$ezop-repo-drift-auditor przeprowadź audyt przed wznowieniem pętli —
sprawdź czy AGENTS.md, backlog i komendy są nadal zgodne z kodem

# EN
$ezop-repo-drift-auditor run an audit before resuming the loop —
check whether AGENTS.md, backlog, and commands still match the code
```

```
# EN
Run $ezop-repo-drift-auditor — periodic check, we haven't touched this repo
in 2 weeks and want to make sure docs haven't drifted before planning next sprint
```

---

## Skill directory structure

```
ezop-<name>/
├── SKILL.md                  ← skill definition (system prompt / description)
├── agents/
│   └── openai.yaml           ← OpenAI / Custom GPT configuration
└── references/
    ├── checklist.md          ← quality gates for the skill
    ├── prompt-templates.md   ← ready-made prompt templates
    └── *.md                  ← additional references (taxonomy, types, routing...)
```

---

## Tips

- **Always start from the repo** — all skills require real repository context; they don't generate docs from thin air.
- **Bounded slices** — plan work in small, independently executable units with explicit verification; this is the core assumption of the whole system.
- **Append-only log** — the backlog loop writes to `.codex/ai-assisted-backlog-loop.md`; don't delete it between sessions, it's the resume point.
- **Drift audit before resuming** — after a break of more than a few days, run `$ezop-repo-drift-auditor` first.
- **Slice reviewer is optional** — the backlog loop has it built in; invoke it separately only when you want a manual review pass.
