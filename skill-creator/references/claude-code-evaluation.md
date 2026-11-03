# Optional Claude automation: not supplied, not qualified

> **Adapted and changed from the Anthropic skill-creator.** This document is original text adapted from, and changed from, the skill-creator in <https://github.com/anthropics/skills> (path `skills/skill-creator`, pinned commit `ca45fc496a3436251f191354091d557da31c15b5`, licensed Apache-2.0). It is not an upstream file. The licence text is [LICENSE.txt](../LICENSE.txt) and the attribution is [UPSTREAM.md](../UPSTREAM.md) in the skill root. The upstream automation it discusses is **not supplied** and **not qualified** by this release.

The upstream skill-creator comes with automation written for one client (a command-line coding agent): a trigger-test runner, a description optimiser, a benchmark and report generator, a local review viewer and grader/comparator/analyzer agent prompts. **This release does not supply that automation and does not qualify it.** Nothing in this folder runs it, wraps it, patches it or depends on it, and this skill does not tell you to download or run it. The manual method in `portable-evaluation.md` is complete without it.

See `UPSTREAM.md` for the pinned commit and the pinned tree URL, which is where the upstream code can be read as source history.

## Why it is not shipped

Reading the pinned upstream source (not executing it) showed problems that would have to be fixed and re-tested before anyone could rely on it:

- the review server terminates whatever process is listening on the port it is asked to use, and it places data into page script with plain JSON encoding;
- the viewer inserts data into the page without escaping and ignores HTTP error responses;
- the format validator accepts blank required strings, and the packaging script can include its own output archive;
- benchmark metadata hard-codes a run count;
- the description optimiser reuses the same held-out set for selection, so its best score is selection-validation, not an untouched final test;
- the trigger runner launches the client's command line once per query, writes temporary command files into a project directory, and can report "not triggered" if an unrelated tool call happens first. Even when it works it measures only whether the skill was invoked, not whether the result was better.

Shipping a patched fork would mean owning that code, its security review and its upkeep, which is out of scope for a portable method. Omitting it avoids shipping unsafe or unreliable automation; it is not a claim that these defects were fixed.

## What to do instead

1. **Trigger and discovery:** run realistic natural-language prompts and should-not-trigger prompts by hand in each client you care about, and record whether the skill was actually loaded (a load record or a visible behaviour difference, not the agent's claim). Procedure: `portable-evaluation.md` sections 2–4.
2. **Behaviour:** compare baseline and candidate on real task artifacts, review the outputs yourself, keep untouched final cases (sections 4–6).
3. **Description quality:** write the description in users' words, test it on cases that were never used to choose it, and treat any automated or repeated selection as a draft.
4. **Structure:** check names, frontmatter and links with whatever validator your repository trusts. A format check is not a behaviour test.
5. **No quantitative claims you did not measure.** If you cannot run something, say so and use the static review in `portable-evaluation.md` section 7.

## If someone wants upstream automation anyway

That is a separately scoped decision for the operator, not part of this skill. It needs: an explicit go-ahead to use that client and account (it spends that account's usage and must not bypass an existing payer or model restriction), a code and security review of the specific scripts at a pinned commit, a throwaway project directory so temporary files cannot land in a shared checkout, small bounded runs, and the operator's usual governance for adopting third-party code. Never run it against a different model or payer than the one the operator authorised, and never adopt, publish or install its output automatically.
