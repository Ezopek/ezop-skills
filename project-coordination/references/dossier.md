# Dossier

The dossier is the coordination record of one topic: what was asked, answered, decided, verified and changed, which no other artifact holds. Do not copy project knowledge into it; link it.

## Location and layout

- One directory per topic, named `<YYYYMMDD>-<slug>` (a date needs no shared counter).
- Put it where the project already keeps coordination notes, or in the operator's dedicated dossier repository if there is one; otherwise ask once, with a recommendation. A session-temporary folder is not a durable handoff; say so. Writing to a shared place is a write: check that the grant allows it.
- Create only the files the topic needs; the README says which are skipped.

| File | Holds |
|---|---|
| README.md | header (goal; ticket link or "none - <reason>"; dossier URL), card, reading order, ID legend, rules for resuming |
| 00-goal-and-constraints.md | goal, done for the current phase, C entries verbatim with source, non-goals, maintenance appetite, standing authorisation (what may be done without asking, what is reserved to whom) and current pauses; a change to either is also recorded as a D |
| 01-decisions-and-questions.md | D, Q, FU |
| 02-change-map.md | M, from planning on |
| 03-facts.md | F |
| 04-options.md | options against constraints, proposals |
| 05-plan.md | S, G, A; frozen once accepted |
| 06-worklog.md | append-only, one entry per step |
| costs.md | optional, see below |
| `research/` | one report per research question, written by its worker |
| `reviews/` | one file per review round: findings plus the coordinator's disposition of each |
| `evidence/` | raw outputs that support a decision; never secrets |

**ID legend:** C constraint, F fact, D decision, Q open question, FU follow-up, M change-map element, S slice, G gate, A acceptance criterion.

## One owner per fact

Each changing fact lives in exactly one owner file; elsewhere only its ID or a link. The card is a projection, rewritten whole from the owner files on every dossier commit, never patched line by line. Card versus owner file: the owner wins. Owner files versus live state: live state wins and the owner file is corrected.

## IDs, anchors and links

Every ID row starts with an HTML anchor named by the lowercase ID, for example `| <a id="d3"></a>D3 | ... |`; slice headings carry one too. Every mention of an ID in text the operator or a stakeholder reads (chat messages, the card, PR descriptions, ticket text) is a link to its anchor in the pushed dossier: an absolute URL outside the dossier, a relative link inside it. The first mention in a text carries a gloss of a few words:

```text
[D3](https://example.org/dossiers/20260303-invoice-sync/01-decisions-and-questions.md#d3) (keep the existing proxy)
```

Never make the reader hunt for an ID.

## Record formats

Short rows; one example each, synthetic.

- **C**: id, constraint as stated, who, date, verbatim quote.
  `| <a id="c1"></a>C1 | No schema change | data owner | 2026-03-02 | "we do not touch the schema this quarter" |`
- **F**: id, fact, evidence (file:line, URL or command), status (verified with who, when, how / documented / inferred / unverified).
  `| <a id="f2"></a>F2 | Queue library v4 is deployed | deploy manifest line 12 | verified, coordinator, 2026-03-02, read |`
- **D**: id, date, decision, why, status (Proposed / Accepted by whom / Rejected / Superseded by D-n).
  `| <a id="d3"></a>D3 | 2026-03-03 | Keep the existing queue library | C1, F2 | Accepted by operator |`
- **Q**: id, question, owner, how it will be closed. Close in place: strike it through and add the answer and the D id. Every operator answer is recorded as a D.
- **FU**: id, follow-up, owner.
- **M**: id, element, where (repository, path or resource), new, changed or removed, why (C or D ids), depends on, status per environment, PR, who maintains, how to check, how to undo. Names of secrets only, never values.
- **Worklog entry**: date and short title; what was checked and how; what was found; operator inputs and decisions. Every outward or state-changing effect (branch pushed, PR opened, comment posted, ticket changed, job started, deploy, message sent) is recorded here with its identifier when it happens, before the step ends; in-flight items are also on the card.

## Writers

One coordinator per topic at a time; a topic changes hands only by a session handoff. The coordinator owns the card and every register. A research or verification worker writes only its assigned report file and returns a short summary with the path. Reviewers write nothing in the dossier; the coordinator records the verdict, or routes review output straight into the round file. Each coordinator works in its own worktree or checkout of the dossier repository; topics live in separate directories, so rebasing onto other coordinators' pushes is routine. There is no shared index of topics: the directory listing plus each card's As of line is the index.

Commit and push at the end of each step (a decision, a review round's disposition, a slice, a handoff), not per edit and not only at the end. An unpushed dossier is not a handoff, except the operator-held copy described in SKILL.md standing rule 9. Follow the dossier repository's own rules for commit style and push.

**Language.** What the operator and stakeholders read (README and card, options, decisions, plan, change map, approval cards) is in the operator's language. Agent-facing records (facts, worklog, research reports, evidence) are in English unless the repository has its own convention; confirm once. Identifiers, commands and paths stay verbatim.

## The card

Each line is at most about 120 rendered characters; omit lines the phase does not have yet.

- **As of**: date and phase.
- **In the world**: one line from the change map, with a link.
- **Gates**: open G entries.
- **Slices**: worktree, branch and commit for work in progress.
- **Last review**: round and verdict.
- **In flight**: normally nothing; a handoff waits for workers.
- **Authority**: one line (e.g. "may open PRs; merge and deploy reserved; pause: deployment") linking to the goal-and-constraints file.
- **Waiting on**: who, what, and what it blocks.
- **Next step**: who, one action.
- **Resume**: the resume line naming the skill and the dossier location (repository plus path; not a commit, since the card cannot name its own).
- **Cost**: only if costs.md is kept.

Minimal example (synthetic):

```markdown
**As of** 2026-03-03 - phase: options
**In the world**: nothing changed yet ([M1](https://example.org/dossiers/20260303-invoice-sync/02-change-map.md#m1) planned)
**Authority**: may open PRs; merge and deploy reserved; pause: deployment
**Waiting on**: operator - choose option A or B; blocks the plan
**Next step**: coordinator - write the plan once [Q2](https://example.org/dossiers/20260303-invoice-sync/01-decisions-and-questions.md#q2) (retry policy) is answered
**Resume**: `Use the project-coordination skill: resume topic example-dossiers:topics/20260303-invoice-sync.`
```

Inside a real dossier these card links are relative; the example uses absolute URLs only because this file is not a dossier.

## Resume procedure

Whenever the next step needs a new session, give exactly one copy-paste line naming this skill, the dossier location (repository plus path) and the pushed commit, preceded by the client's own new-session command if it has one. The card carries the same line without the commit.

1. Open the location in the command; fetch (or clone, over the project's usual transport) its repository and work at the remote tip.
2. If the command names a commit, check that the remote tip contains it. If not, stop and say the previous session did not push its handoff.
3. Read the card, then the goal-and-constraints file (authority, constraints, pauses), then the decisions and questions and, from planning on, the change map. Open the plan only at the slice the next step needs. Delegate heavier reading to read-only workers where available.
4. Check every in-flight item and every effect in the worklog by its recorded identifier: finished, running or lost. Never repeat an effect that already happened. A worker recorded as in flight after a crash is presumed dead: its output counts only if complete; otherwise restart it from a brief rebuilt from the dossier.
5. Re-check read-only the live state the next action depends on.
6. Before acting, tell the operator in a few lines: phase, what is live, what waits on whom, the next action. Until that is said, change nothing but the local checkout.

A pause recorded in the card still holds.

## Cost register (optional)

Keep costs.md only if the client exposes usage data. One row per session that worked on the topic: session id, kind, what it did in about eight words, from, to, main model, measured amount. Add a total and the card's cost line. Use measured values only, never estimates from token counts; unknown values stay "?". A session counts whole, in the one topic it mostly served.
