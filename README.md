# ezop-skills

Zestaw 5 skilli do AI-driven development — od przygotowania repo, przez planowanie, po autonomiczne wykonanie i review. Działają samodzielnie lub razem jako pipeline.

---

## Skille

| Skill | Kiedy używać |
|---|---|
| `$ezop-agent-ready-docs` | Tworzenie/aktualizacja AGENTS.md, README.md, docs operacyjnych |
| `$ezop-delivery-planner` | Tworzenie roadmapy, backlogu, planu feature'a |
| `$ezop-backlog-loop-orchestrator` | Autonomiczne wykonanie backlogu — pętla slice po slice |
| `$ezop-slice-reviewer` | Review jednego slice'a przed commitem |
| `$ezop-repo-drift-auditor` | Audyt spójności docs/backlog vs. rzeczywisty kod |

---

## Rekomendowane flow

```
[nowe repo / powrót po przerwie]
        │
        ▼
$ezop-repo-drift-auditor       ← sprawdź czy docs/backlog nie zdryftowały
        │
        ▼
$ezop-agent-ready-docs         ← przygotuj AGENTS.md i dokumentację repo
        │
        ▼
$ezop-delivery-planner         ← utwórz backlog / roadmapę / feature plan
        │
        ▼
$ezop-backlog-loop-orchestrator ← wykonaj pętle: plan → implement → verify → commit
        │         ↑
        ▼         │
$ezop-slice-reviewer            ← (opcjonalnie) zaakceptuj każdy slice przed commitem
```

Każdy skill można używać solo — nie ma obowiązku przechodzenia całego pipeline'u.

---

## Jak wzywać skille

### Claude Code (CLI)
```
$ezop-delivery-planner utwórz backlog dla feature X
```
Prefiksy `$` w promptach i `ezop-` w nazwie skilla są rozpoznawane automatycznie. Skill jest dostępny jako slash command:
```
/ezop-delivery-planner
```

### Claude (Anthropic) — Projects / API
Wklej zawartość `SKILL.md` jako system prompt lub dołącz jako dokument w projekcie. Następnie wołaj przez `$nazwa-skilla` w wiadomości.

### OpenAI Codex / Custom GPT
Każdy skill zawiera `agents/openai.yaml` — zaimportuj go jako Action lub dodaj opis do system promptu GPT. Default prompt z yaml to gotowy starter.

### Copilot / Cursor / Windsurf
Wklej `SKILL.md` do `.cursorrules`, `AGENTS.md` lub kontekstu rozmowy. Następnie odwołuj się przez `$ezop-<nazwa>` w promptach do agenta.

### Dowolny agent (generic)
Każdy skill to self-contained prompt — wystarczy:
1. Wkleić treść `SKILL.md` do systemu / kontekstu
2. Wołać przez `$ezop-<nazwa>` lub pełną nazwę skilla

---

## Przykładowe prompty

### Przygotowanie repo

```
Użyj $ezop-agent-ready-docs żeby przygotować AGENTS.md i README.md
dla tego repo — priorytet na bezpieczne instrukcje dla agentów,
zweryfikowane komendy i czytelne granice architektoniczne.
```

```
$ezop-agent-ready-docs -- tighten AGENTS.md, we added a new service layer
and the existing doc doesn't mention it at all
```

### Planowanie

```
$ezop-delivery-planner utwórz backlog dla migracji auth middleware
na nowy system sesji — podziel na bounded slices z weryfikacją dla każdego
```

```
Use $ezop-delivery-planner to create a feature implementation plan for
adding rate limiting to the API — expose all open decisions before finalizing
```

### Autonomiczne wykonanie

```
$ezop-backlog-loop-orchestrator uruchom pętlę backlogową — przeczytaj najpierw
AGENTS.md, prowadź log w .codex/ai-assisted-backlog-loop.md, jeden slice na raz
```

```
Resume the backlog loop — read the last entry in .codex/ai-assisted-backlog-loop.md
and continue from where we left off using $ezop-backlog-loop-orchestrator
```

### Review slice'a

```
$ezop-slice-reviewer przejrzyj ostatni diff względem zatwierdzonego planu,
sprawdź regressions, brakujące testy i docs drift — zakończ accept/needs-fix/blocked
```

```
Use $ezop-slice-reviewer to review the changes in the current branch against
backlog item #3 — findings first, severity order
```

### Audyt driftu

```
$ezop-repo-drift-auditor przeprowadź audyt przed wznowieniem pętli —
sprawdź czy AGENTS.md, backlog i komendy są nadal zgodne z kodem
```

```
Run $ezop-repo-drift-auditor — periodic check, we haven't touched this repo
in 2 weeks and want to make sure docs haven't drifted before planning next sprint
```

---

## Struktura każdego skilla

```
ezop-<nazwa>/
├── SKILL.md              ← główna definicja skilla (system prompt / opis)
├── agents/
│   └── openai.yaml       ← konfiguracja dla OpenAI / Custom GPT
└── references/
    ├── checklist.md      ← kryteria jakości dla skilla
    ├── prompt-templates.md ← gotowe szablony promptów
    └── *.md              ← dodatkowe reference (taksonomia, typy, routing...)
```

---

## Wskazówki

- **Zawsze zaczynaj od repo** — wszystkie skille wymagają realnego kontekstu repozytorium, nie generują dokumentów z powietrza.
- **Bounded slices** — planuj pracę w małych, niezależnych kawałkach z jawną weryfikacją; to jest założenie całego systemu.
- **Append-only log** — backlog loop zapisuje log w `.codex/ai-assisted-backlog-loop.md`; nie kasuj go między sesjami, to punkt wznowienia.
- **Drift audyt przed wznowieniem** — po przerwie dłuższej niż kilka dni odpal najpierw `$ezop-repo-drift-auditor`.
- **Slice reviewer jest opcjonalny** — backlog loop ma go wbudowanego; wołaj osobno tylko gdy chcesz ręcznego przeglądu.
