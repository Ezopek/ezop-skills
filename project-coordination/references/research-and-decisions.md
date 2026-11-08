# Research and decisions

Read this when starting a topic, taking over a running project, briefing research workers, or preparing options for the operator. Do only as much as the topic needs; a small repository needs a quick look, a long-running system needs a real survey.

## Intake

Start from what the user already said. Fill the following from the conversation and the sources first; ask only what remains unknown and would change the first slice:

- **Goal and done criterion**, and what "done" means for this phase: research only, proposals, plan or execution.
- **Hard constraints**: deadlines, compatibility, budget, forbidden areas, mandatory policies or reviews. Record each verbatim as a C entry, hard or preference.
- **Maintenance appetite**: what the team does not want to own or operate, and known blockers.
- **Who decides what**: the user, a maintainer, a reviewer, an owner of a system.
- **Standing authorisation**: ordinary steps the task needs (read, delegate, edit working files) are covered. For consequential or outward actions, find out what was actually granted. Do not invent a permission, and do not treat a missing mention of an ordinary step as a ban.
- **Existing pauses**: anything the user said to hold.

Ask few questions at once, in order of how much the answer changes the work, each with your default so a one-line answer is enough. Start once the questions that change the first slice are answered or the operator accepted your stated defaults; meanwhile do the work that does not depend on them. An assumption you wrote down stays yours until someone with authority confirms it.

For a new project there may be nothing to read; the intake is the whole discovery. Then pick the smallest first slice that produces something checkable.

## Researching an existing project

Order is a suggestion; follow the trail the project has.

1. **Repository**: layout, README and contributing guides, build and test commands, CI definitions, recent history, open branches and pull requests. Run the project's own checks to learn the baseline once you have looked at what they execute.
2. **Documentation**: design notes, decision records, runbooks, earlier coordination notes or handoffs.
3. **Tracker**: open and recently closed issues, who is assigned, what is blocked or in review.
4. **Decisions and current work**: what was decided and why, what is mid-flight, what someone else owns right now. Do not start work that collides with an owner's active work.
5. **Owners**: who owns which area, who reviews, who may approve what.

Note for each class of fact where the authoritative version lives and who owns it; link it, do not copy it. Stop researching when the next decision is no longer uncertain; record the rest as open questions with an owner and a way to resolve them. Authority follows ownership and evidence: a newer unreviewed note does not override an owner's recorded decision, and an old note does not override what the code and checks show now. Never silently overwrite someone else's record to make sources agree.

## Research workers

Split the topic into independent questions, typically: the current state of each system involved, the external options, and the constraints every option must meet. One worker per question. Brief each with:

- the question and why it matters;
- the constraints (C ids) and deployed versions;
- its write boundary: only its own report file, at the path you give (`research/<question>.md`);
- the return contract: a short summary with the report path, each claim marked verified, documented or inferred, with evidence;
- the caution about running project code, and any pause that applies.

While workers run, frame the topic, make small direct checks and forward any new constraint to the running workers. Treat what comes back as claims; see `team-and-review.md`.

## Facts register

Record decisive facts in the dossier with evidence and a status:

| Status | Meaning |
|---|---|
| verified | checked at the source by a named person or agent, with date and method |
| documented | stated in a document or by an owner, not checked |
| inferred | concluded from other facts |
| unverified | claimed, not checked |

A fact that would change a decision must be verified at the source: the code at the deployed version, a live read-only query, the actual configuration. Prefer a small real experiment over more reading. Environment access (hosts, accounts, endpoints) comes from the team's knowledge base, never from memory; if it is not there, ask. Every name you will later put into a command is checked against the system that consumes it (identifiers versus display names).

## Options, proposals and decisions

1. **State each option first in its simplest complete form.** Every mechanism added on top (approval, gate, role, lock, durable state, recovery step, new service or background component) names its source (a C or D id, or a binding rule) and takes the narrowest scope. If the `scope-discipline` skill is installed, load it here.
2. **Evaluate every option against every constraint**, with a verdict and a reason citing F ids. Include an option that violates a constraint when that constraint may be worth negotiating, with its pros and cons.
3. **Proposals for the viable options**: what each requires per repository or system, who must agree, risk, cost in plain terms (effort, upkeep, money where known), and rollback.
4. **Recommend**; the operator chooses; record a D with status Accepted and by whom. Every operator answer is a D.
5. When asked for an opinion, give one with reasons, not a menu. If the evidence contradicts the operator's assumption, say so plainly and show the evidence.
6. **Stop at the depth asked.** Do not plan or implement before the operator has chosen.

Questions to the operator: close what a read-only check can close first, then ask few, each with your recommendation and labelled options (`1A 2B`). A decision above the operator's authority goes to whoever holds it; say so.

## Choosing a method

1. If the project has a working process (branching, review, release, definition of done), follow it.
2. Otherwise use the lightest thing that works: small slices, each with a done criterion and one real check, reviewed before acceptance.
3. Add structure only for a symptom you can name (repeated scope disputes, unclear ownership, lost work, late-review rework), and remove it when the symptom is gone.
4. Do not impose a named framework, board or recurring meeting, and do not ask the user to choose one unless the choice changes what they must do.
