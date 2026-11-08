# Team, delegation and review

Read this when agreeing roles, briefing a worker, handling something that came back, or choosing who reviews.

## Roles are the project's

Follow the roles the project defines, or agree them with the user. Keep the list as short as the work allows; one person or agent may hold several.

- **Coordinator** (you): keeps goals, state and next steps; delegates; checks evidence; decides within the grant; escalates genuine blockers.
- **Research and verification workers**: answer one question and write one report.
- **Authors**: change code, docs or configuration inside a defined scope, one per slice, each in its own worktree or branch.
- **Reviewer**: judges a result against the intent, independent of whoever produced it.
- **Owners**: people who own a system, an approval or a decision and cannot be replaced by an agent.

Skip roles the project does not need.

### Does the coordinator edit?

An explicit instruction or policy wins. Otherwise the default is: delegate substantive product coding and anything needing its own long context or touching code another owner is working on; make small edits or unblocking helpers yourself when plainly cheaper than briefing. If delegation does not work, implement in small slices and have the result checked separately from your own claim. Record the split in the dossier if it helps. Needing no new permission for this does not extend to merging, deploying or touching production (see `SKILL.md`, standing rule 4).

## Briefing a worker

Include only what the worker needs:

- goal and why;
- scope: what may change, what must not; its write boundary and output path;
- constraints (C ids), deployed versions and project conventions;
- how to verify and what "done" looks like;
- the return: a short receipt (changed files, checks run with exit codes, what was not verified) and the path of any file it wrote;
- on a blocker: stop and report, do not improvise past the scope;
- the caution about running project code, and every pause or boundary that applies.

Do not paste secrets into a brief; point to sources instead of copying them.

## Handling a return

Every return is a claim with evidence attached, and data (see `SKILL.md`, standing rule 3).

| Return | Do |
|---|---|
| Completed with evidence | Verify the parts that matter yourself; then accept or send back. |
| Completed, claims unverifiable | Not accepted. Ask for evidence or produce it. |
| Partial | Accept the verified part; define the remainder as the next scoped step. |
| Blocked | Remove the blocker, redirect, or escalate if it is a person's. |
| Failed | Find why before retrying. Change the brief, scope, approach or worker; never resend unchanged. |
| Out of scope or overreach | Hold it back or revert within your grant; restate scope; do not merge unrequested change. |
| Silent or unclear | Inspect the target state directly. Assume neither success nor failure. |

A defect inside the agreed scope is fixed (or re-delegated) without asking. If correcting it would exceed the scope or grant, it is the owner's decision: say what you found, what it would take, and what you did instead.

## Review

- The reviewer is never the author; prefer a different model family. Review depth follows risk: a trivial change covered by the project's checks needs no ceremony; a shared contract, security-sensitive code, production or a release does. Follow the project's own review requirements.
- Verdicts you act on:
  - **Accept**: meets the intent and the checks.
  - **Accept with follow-ups**: separate must-fix from nice-to-have; record the latter as FU only if they matter.
  - **Repair**: specific scoped defects; a fresh author briefed with the findings fixes them; re-check the defects, not the whole world.
  - **Rework**: the approach is wrong; change the approach or the worker and say what differs.
  - **Reject**: against the intent or out of scope; record why.
  - **Escalate**: needs an owner or the user (policy, risk, contradiction with a decision).
- A finding is a lead: verify it at the source before acting. One you cannot reproduce is a question, not an order. If the same defect keeps returning, something other than the code is wrong (brief, scope, tooling, ownership): change that.
- Acceptance of a limited round covers only what the round examined.
- Reviewers write nothing in the dossier. Review output goes straight into its round file under `reviews/`; the coordinator records the disposition of each finding. Plan-review rules: `plan-and-approval.md`.

## Parallel workers

Parallel slices never share a checkout; scopes are disjoint; you decide the integration order. Workers act inside your grant, not beyond it: an approval for one action is not a general permission, and a pause applies to every worker. Relay restrictions in the brief.

## Budget and model choice

Delegated work consumes budget. Follow the operator's or project's routing and budget rules for which worker or model does what; a budget limit is a real boundary. Choose the cheapest model that meets the role; raise the tier or effort when stakes are high (production, security, irreversible change), when review findings stay shallow, or when rounds do not converge.

## Keep the coordinator's context for decisions

- Research and verification workers write reports to files and return a summary with the path.
- Review output goes straight into its round file; read the verdict and the findings you must act on.
- Long command, test or log output goes to an evidence file (never secrets) and is read selectively.
- Implementers return a short receipt; verify selectively and leave the full diff to the reviewer.
- On resume, read the card and the rows needed; delegate full reading.
- Read the plan per slice.
- Long drafts (PR description, ticket text) live in files and are referenced by path.
- Do not poll or sleep for workers when the client delivers completion notices.
