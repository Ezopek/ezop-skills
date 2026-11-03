# Portable evaluation: run, judge and iterate without special tooling

Adapted from the author, test, review and iterate method of the Anthropic skill-creator (Apache-2.0, see `../UPSTREAM.md`). Everything here works with a file system and any capable agent. Parallel agents, timing data and viewers are conveniences, not requirements, and no tooling for them is supplied here (see `claude-code-evaluation.md` for the status of the upstream automation).

## 1. Workspace

Keep evaluation material outside the skill folder so it is not shipped by accident, for example a sibling directory `<skill-name>-workspace/`:

```text
<skill-name>-workspace/
  cases.json                 prompts, expected behaviour, kinds
  skill-snapshot/            copy of the skill before this round's edits (for comparisons)
  iteration-1/
    <case-name>/
      candidate/outputs/     what the run produced
      baseline/outputs/      same prompt without the skill, or with the snapshot
      notes.md               your judgement, with evidence
```

Create directories as you go. Do not commit workspaces to the skill's repository unless the operator asks.

## 2. Case file

One small JSON list is enough:

```json
[
  {
    "name": "plain-request-no-skill-name",
    "kind": "discovery",
    "prompt": "<realistic request, as a person would type it>",
    "inputs": ["<synthetic or approved input file, if any>"],
    "expect": "<what a good outcome contains, in plain words>",
    "should_load_skill": true
  },
  {
    "name": "near-miss-other-tool",
    "kind": "should-not-trigger",
    "prompt": "<shares keywords but needs something else>",
    "should_load_skill": false
  },
  {
    "name": "task-with-artifact",
    "kind": "task",
    "prompt": "<task>",
    "inputs": ["<file>"],
    "expect": "<inspectable result>",
    "checks": ["<objective check, optional>"]
  }
]
```

`kind` is `discovery` (unaided selection), `should-not-trigger`, or `task` (real artifact). Mark a few cases `"holdout": true` and leave them unused until the end.

## 3. Running a case

1. Start a fresh session or a fresh sub-task with no memory of earlier cases.
2. For the candidate run, make the skill available the way a user would install it in that client, then give the bare prompt. Do not say the skill's name in discovery cases.
3. For the baseline run, give the same prompt without the skill (new skill) or with the snapshot of the previous version (changed skill).
4. Save the outputs and, when the client exposes it, a record of whether the skill was actually loaded. An agent claiming it used the skill is not evidence; a load record or a visible behavioural difference is.
5. If you cannot run cases in parallel or in fresh contexts, run them one after another and say so; contamination between cases is a limit on what you can conclude.

Do not call a model, service or account the operator has not authorised for evaluation.

## 4. Judging

For each case, read the outputs, not only the final message.

- **Objective checks** (file exists, command exits zero, numbers within a stated bound, links resolve) can be scripted or checked by hand. Record the check, the command, and the result.
- **Subjective qualities** (clarity, design, tone) are reviewed by a person or by you with a written rubric. Do not invent a score.
- **Comparison.** For a changed skill, put candidate and baseline side by side. Prefer a blind comparison when you have a second reviewer or can hide which output is which; otherwise note that you knew.
- **Look for regressions.** A change that fixes one case and breaks another is not an improvement.
- **Look for wasted text.** If runs spend effort on instructions that never mattered, remove them.

Write one `notes.md` per case: what happened, what you checked, verdict (`better`, `same`, `worse`, `unclear`), and the instruction you suspect.

## 5. Revising

- Change the instruction that corresponds to the observed failure. Prefer explaining why over adding capitalised rules.
- Generalise from the failing case to the underlying principle so the fix transfers.
- If every run independently rewrote the same helper script or repeated the same steps, bundle that helper inside the skill (after reviewing it) or add the steps to a reference.
- After editing, snapshot again and rerun the affected cases plus a few neighbours. Stop when the problems you recorded are gone or the remaining gains are small.

## 6. Final acceptance

Run the untouched holdout cases once on the final version. Report them separately from the iteration cases. If a holdout case fails, fix the cause, and treat that case as used; add a new untouched case before claiming acceptance again.

## 7. Static or manual review when running tests is not possible

When execution is not available (no permission, no safe fixtures, no budget), say so plainly and review statically:

- Does the description say what the skill does and when to use it, in the user's words, without hidden jargon?
- Could an unaided agent tell this skill apart from adjacent skills by description alone?
- Is each instruction tied to a failure or risk, and is anything speculative?
- Do all referenced files ship and resolve from the installed folder?
- Are claims about tools, versions or limits dated or marked verify-before-use?
- Are scripts reviewed, offline by default, and safe with synthetic inputs?
- Does the skill avoid fixed tool names that exist in only one client?

Label the result "static review, not exercised". Do not turn it into pass rates or timings.

## 8. Report

```text
Skill: <name>   Change: <what and why>
Cases: <n discovery, n should-not-trigger, n task>   Holdout: <n, untouched until the end?>
Baseline: <what it did wrong or right>
Candidate: <what it did>
Verdicts: <per case, one line>
Not tested: <explicit list>
Decisions for the operator: <publication, installation, adoption>
```

Structural validation (for example a name and link check) is reported as its own line and is never counted as a behaviour result.
