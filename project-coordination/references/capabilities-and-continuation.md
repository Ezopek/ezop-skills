# Capabilities and continuation

Read this before you rely on any way of getting work done or getting results back, and before you tell the user that anything will happen later.

## Four separate statements

| Level | Meaning | Example evidence |
|---|---|---|
| **Claimed** | Someone or something says it works | documentation, a card, memory, a worker's report |
| **Available** | The capability is visible in this session | the tool is in your tool list, the command exists, the host is reachable |
| **Tested** | A cheap, harmless call succeeded in this session | a dry run, a read-only query, a trivial task that returned |
| **Continuation** | A result or wake is observed to come back to you here | you have seen a completion, callback or scheduled run actually arrive in this project |

Only tested capabilities justify a plan that depends on them. Only observed continuation justifies saying "I will be notified" or "this will continue on its own". Claimed or available is enough to try, not enough to promise.

Do not run a probe ceremony. Evidence you already have counts: reuse a verified earlier result (yours, with its date, not a bare claim), and count the real work itself, such as a worker that returned a substantive result you inspected. When you still need to know and it is safe, a direct look is enough (list the tools, read the command's help, check that the host answers). Run a separate trivial test only if the capability is uncertain, matters for the plan, and a harmless one is cheap. Record what you learned in the card with the date. Re-check when the environment changed or a result contradicts the record.

## Mechanisms and their honest limits

Names vary by client and host; describe the capability, not a vendor command.

| Mechanism | What it truly gives | Honest limit |
|---|---|---|
| Tools you call yourself, synchronous | Work completes inside the turn | Bounded by the turn; large work needs slicing |
| Delegated worker that returns to you in the same turn | A result you can inspect now | Check how it ends; a launch is not a return |
| Asynchronous worker with a callback or completion event | A real signal when it finishes, if that signal has been observed | A started job is not an observed callback |
| Command-line process or remote session | Work may survive the turn if the host keeps it alive | A process id proves a start, not survival or that anyone will read the output |
| Shared board or tracker | A durable record for people and later sessions | Without a verified consumer, nothing moves until someone looks |
| Scheduled or queued job | Something may run later | A queue entry is not a run; check that a runner exists and fired |
| Notes, cards, saved cursors | Memory for the next session | They create no wake and no delivery |
| No delegation at all | Full control and direct verification | Context fills faster, so keep slices small and have the result checked separately |

## What to do with what you found

- Use the strongest verified mechanism that fits the work. If a worker mechanism is only available and unproven, you may give it a real, modest, well-scoped task and inspect the result instead of inventing a throwaway test; the first result is then your evidence.
- If a mechanism needs setup or infrastructure that you were not asked to create, do not create it. Work with what exists, and tell the user what would improve continuity if they want it.
- Never fall back silently. If delegation is not usable, say so and either do the work yourself in small checked slices or tell the user what blocks it.

## Terminal results

A terminal result is anything that ends a unit of work: success, partial result, failure, a worker saying it is blocked, a review verdict, a timeout, a user's answer. When one reaches you:

1. Handle it now, in the same turn: inspect the evidence, decide accept, repair, re-delegate or escalate (see `team-and-review.md`).
2. Update the card if state changed.
3. Look for the next authorised step and take it. A finished item is a reason to start the next one, not to stop.
4. Stop only at a genuine blocker, an explicit pause, a practical limit (turn, context, tool, time or budget), or when everything authorised is done. For a practical limit, end as described under "Ending a turn" in the main file: what is done, what remains, the next step and the continuation prompt.

Results that never arrive are also terminal: a mechanism that was supposed to return and did not is a finding. Record it, check the target state directly, and do not wait for it.

## When no wake exists

If no verified mechanism will bring you back, you cannot "wait" or "check later". Choose, in this order:

1. **Do it inside this turn** if the work fits, including polling a short job and inspecting the result.
2. **Advance everything else that is authorised**, then end honestly.
3. **End with a plain statement**: what is in flight or queued, that nothing will wake or notify you, and the single prompt that resumes. For example: "The test run was started on the remote host. Nothing will notify me when it ends. Say 'Continue project invoice-sync' and I will read its result first."

Do not make the user maintain new infrastructure to get continuity. One manual prompt per boundary is an acceptable, honest cost.

## What not to say

- "I'll wait for it" or "I'll get back to you" without a verified mechanism.
- "The job is scheduled" as if scheduled meant done or delivered.
- "It has been handed off" when the board has no one reading it.
- "Nothing to do" while authorised work remains.
