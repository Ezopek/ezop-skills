# Capabilities and continuation

Read this before you rely on any way of getting work done or getting results back, and before you tell the user that anything will happen later.

## Four separate statements

| Level | Meaning | Example evidence |
|---|---|---|
| **Claimed** | Someone or something says it works | documentation, a card, memory, a worker's report |
| **Available** | The capability is visible in this session | the tool is in your tool list, the command exists, the host is reachable |
| **Tested** | Seen to work in this session, or earlier verified evidence recorded with its date | a dry run, a read-only query, a trivial task that returned; a dated note of a verified result |
| **Continuation** | A result or wake is observed to come back to you here | a completion, callback or scheduled run you have seen actually arrive in this project |

Only tested capabilities justify a plan that depends on them. Only observed continuation justifies "I will be notified" or "this will continue on its own". Claimed or available is enough to try, not to promise.

Run no probe ceremony. Evidence you already have counts: a dated, verified earlier result, and real work such as a worker that returned a substantive result you inspected. Otherwise a direct look is enough (list the tools, read the command's help, check that the host answers). Run a separate trivial test only if the capability is uncertain, matters for the plan, and a harmless test is cheap. Record what you learned with its date; re-check when the environment changed or a result contradicts the record.

## Mechanisms and their honest limits

Names vary by client and host; describe the capability, not a vendor command.

| Mechanism | What it truly gives | Honest limit |
|---|---|---|
| Tools you call yourself, synchronous | Work completes inside the turn | Bounded by the turn; slice large work |
| Delegated worker returning in the same turn | A result you can inspect now | A launch is not a return; check how it ends |
| Asynchronous worker with a completion event | A real signal when it finishes, if observed | A started job is not an observed callback |
| Command-line process or remote session | Work may survive the turn if the host keeps it alive | A process id proves a start, not survival or that anyone reads the output |
| Shared board or tracker | A durable record for people and later sessions | Nothing moves until someone looks, unless a consumer is verified |
| Scheduled or queued job | Something may run later | A queue entry is not a run; check that a runner exists and fired |
| Notes, cards, dossier | Memory for the next session | They create no wake and no delivery |
| No delegation at all | Full control, direct verification | Context fills faster; keep slices small and have results checked separately |

Use the strongest verified mechanism that fits. An available but unproven worker mechanism may get a real, modest, well-scoped task; its first inspected result is the evidence. Do not create setup or infrastructure you were not asked to create; tell the user what would improve continuity. Never fall back silently: if delegation is unusable, say so and work in small checked slices or name what blocks it.

## Terminal results

A terminal result ends a unit of work: success, partial result, failure, a blocked worker, a review verdict, a timeout, a user's answer. Handle it in the same turn: inspect the evidence, decide accept, repair, re-delegate or escalate (`team-and-review.md`); update the card if state changed; take the next authorised step. Stop only at a genuine blocker, an explicit pause, a practical limit or when everything authorised is done; end as `SKILL.md` describes under "Ending a turn".

A result that never arrives is also terminal: record the finding, check the target state directly, and do not wait for it.

## When no wake exists

You cannot "wait" or "check later". In order: do it inside this turn if it fits, including polling a short job; advance everything else authorised; then end with a plain statement of what is in flight, that nothing will wake or notify you, and the resume command. Example: "The test run was started on the remote host. Nothing will notify me when it ends. Use the resume line below and I will read its result first." One manual prompt per boundary is an acceptable, honest cost; do not make the user maintain new infrastructure for continuity.

Do not say: "I'll wait for it" or "I'll get back to you" without a verified mechanism; "it is scheduled" as if scheduled meant done; "it has been handed off" when nobody reads the board.
