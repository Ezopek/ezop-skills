# Resume card

A resume card is a short living summary of the live state of a project: enough for a fresh session to continue from one prompt, provided that session can read it. It is not a log, a dossier or a duplicate of the tracker. It is optional where writing it is not allowed (see below); the project still gets coordinated.

## Where it lives

- **Writing a card is a write.** A tracker issue, comment, wiki page or file in a shared repository can be visible to others, notify people or end up in history. Write it only where the user's grant, the project's norms and the platform's rules allow. If you are unsure whether a shared place is acceptable, ask once, or use a place that is plainly yours to write (a scratch file the user asked for, your own working notes).
- Prefer where the project already keeps coordination notes: a tracker issue or pinned comment, a docs page, an existing handoff file. Use what exists; do not create a parallel structure to host it.
- **Persistence is not assumed.** Your own notes space or a temporary directory may not exist for a fresh session, may be cleared, or may be unreadable to it. A successful write proves only that the text was saved; it does not prove that a later session can find or read it. Check what you reasonably can (same repository or tracker, a path the user confirms) and say what you could not establish.
- **User-held fallback.** If no durable place is authorised or accessible, keep the card in the conversation, show it to the user at natural stopping points and in any practical-limit ending, and give them the continuation prompt with the card text included so they can paste it into a new session. Coordination continues; only the one-line resume depends on the user holding the text.
- Link to authoritative artifacts (decisions, design, backlog, runbooks) instead of copying them. Keep stable knowledge in those sources and only live state in the card.
- Never put credentials, secrets or private personal data in it.

## What it holds

Include only what a successor needs:

- **Objective** and **done when**
- **Decisions and constraints**, each with a link or reason
- **Sources**, pointing at the owners of each fact class
- **Authority**: what you may do without asking, explicit pauses, genuine boundaries
- **Team and, if explicit, the coordinator-edit arrangement**
- **Capabilities verified**: what was tested or observed, with the date; what is only claimed
- **Active work**: item, owner, mechanism, identifier of any in-flight effect, how completion will be observed
- **Next step**: one line
- **Blocker or continuation**: the precise question, or the statement that work resumes only on the next prompt, with the prompt
- **Open uncertainties**: each with an owner and how to resolve it

Update it when something real changes (decision, hand-off, result, blocker), not on a schedule. Shorten it when it grows; move history into the project's own log or let it go.

## Minimal example

Synthetic project, synthetic values.

```markdown
## Resume: invoice-sync          updated: 2026-03-02

Objective: nightly sync finishes inside the batch window; retry bug fixed.
Done when: two consecutive nightly runs finish in time; retry test in CI is green.
Decisions / constraints: keep the existing queue library (decision record in the repo);
  no schema change without the data owner; window is a hard limit per the ops runbook.
Sources: code and CI = repo; priorities = tracker milestone "Q1 sync"; window = ops runbook.
Authority: may delegate, run tests, push working branches, open pull requests.
  May not merge, deploy or touch the billing account. Pause: none.
Team: coordinator edits = small fixes and test helpers only; implementer and reviewer
  agents for everything else; maintainer approves merges.
Capabilities: delegated worker returns in-turn (tested 2026-03-02);
  remote shell available, background result NOT observed; no scheduler used.
Active work: retry fix, owner = implementer-A, branch fix/retry, pull request #57 opened
  (identifier recorded, do not reopen). Review pending.
Next step: verify the review result on #57 against the diff, then start the batch-window profile.
Blocker / continuation: none now. Nothing wakes me when review ends; resume with
  "Continue project invoice-sync, card in the tracker issue 42."
Open uncertainties: is the window shared with the reporting job? owner = ops; ask in runbook thread.
```

## Recovery procedure

1. **Locate** the card from the user's prompt (a reference or pasted text) or the project's usual place. If several candidates exist, prefer the one the project designates; do not guess between conflicting cards.
2. **Skim, then check**. Verify only the facts the next step rests on against their real sources: branch state, pull request status, check results, tracker status.
3. **Check for effects before repeating them**: does the branch, comment, ticket, job or message already exist? Is each in-flight item finished, running, failed or lost? Use the recorded identifiers.
4. **Reconcile differences** by ownership and evidence: update the card to what the sources show. Do not reconcile by overwriting someone else's record.
5. **Honour pauses and boundaries** as recorded, unless the user lifted them.
6. **Continue** with the next authorised step. Do not ask the user to re-explain what the card and sources answer.

## Prompt examples

First invocation, with discovery needed:

```text
Coordinate the docs-site project for me. Repo is checked out in the current
directory. I want the broken link report cleaned up and the build time halved.
Decide the plan and run it; ask only if something truly blocks you.
```

Expected shape: read the repo, docs and issues without asking; ask at most the unresolved material questions (for example, is a dependency upgrade acceptable); create the card; start the first slice.

Continuation after the first session, using the reference that was discovered or created (or the card text the user kept, pasted after the prompt):

```text
Continue project docs-site; card is the pinned comment on issue 18.
```

Continuation with an explicit pause carried in the card:

```text
Continue project docs-site. Card on issue 18. Skip the deployment work, I'm still checking with ops.
```

Expected shape: record the new pause in the card, continue with everything else authorised.
