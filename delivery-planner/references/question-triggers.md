# Question Triggers

Ask the user only when the answer is not discoverable from the repo and materially changes the plan.

## Ask When The Choice Changes

- service or module ownership
- public API or contract shape
- whether backward compatibility is required
- rollout or migration strategy
- whether work should be one slice or several
- the target verification bar
- whether a feature is optional, required, or experimental
- whether a docs artifact should be created or updated

## Do Not Ask When You Can Discover

- which commands exist
- which CI workflows run
- which files already own a concept
- whether a schema or contract already exists
- which service currently handles a given behavior

Inspect first.

## Good Question Style

Good questions are:

- short
- high-signal
- tied to a concrete consequence
- limited to the few decisions that really matter

Prefer:

- “Should this stay gateway-owned, or do we want to move ownership into agent-runtime? It changes both scope and contract shape.”
- “Do we need backward compatibility for the current endpoint payload, or can the plan assume a direct replacement?”

Avoid:

- long questionnaires
- asking for facts you can verify yourself
- asking about details that do not affect the current planning artifact

## If The User Does Not Answer

If you are blocked on a decision:

- write the plan with explicit assumptions
- mark the relevant section as `Open Question`
- state what cannot be finalized without the answer

If you are not blocked:

- proceed with the best repo-grounded recommendation
- clearly mark the assumption
