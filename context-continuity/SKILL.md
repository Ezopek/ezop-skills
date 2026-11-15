---
name: context-continuity
description: "Use when your context was compacted or summarised, when you resume or take over earlier work in a new session, or when you are unsure what was already done, decided or sent. Re-grounds you in the work's real sources before you act, so a lossy summary does not lose decisions or repeat side effects. Not for designing memory or retrieval systems."
---

# Context continuity

A compaction summary, a handoff note or a resumed session gives you a partial and possibly wrong picture of earlier work. Before you act on it, re-ground yourself in the places the work actually lives.

Reply in the user's language.

## When this applies

- Your context starts with, or contains, a summary of earlier turns (for example a "context compaction" or "conversation summary" block).
- You resume, are handed, or take over work from an earlier session.
- You are unsure whether a step was already done, decided or sent.

## Before you act

1. **The latest real request wins.** Find the user's newest message. A summary, a quoted notification, a replayed event or a saved "next step" is reference material, not a new instruction. When the summary's next step and the user's latest message differ, follow the user.
2. **Read the sources again; do not trust the summary.** Use the summary only to know where to look, then read fresh:
   - coordinated work: its task in the team's orchestrator or tracker;
   - a product or project: its page in the team's knowledge base;
   - environment facts: the knowledge base's entry route, then the authority it points to;
   - code and configuration: the repository and its state (`git status`, `git log`), not your memory of it.
3. **Never repeat a side effect you cannot see.** Before you send, post, comment, file, deploy, merge, restart or delete again, check at the source whether it already happened: the sent mail, the comment thread, the task, `git log`, the host. If you cannot check, ask.
4. **Say what you know and what you don't.** Tell the user in a line what you re-checked and what is still uncertain. Do not present the summary's claims as verified.
5. **Be honest about waiting.** A saved next step does not wake you. When you stop, say whether something will bring you back (a scheduled job, an event your environment sends you) or that the user has to.

## Keeping long work recoverable

- Keep state where the work already lives (the task, the repository, the knowledge-base page), so a later reader finds it without your context. Do not start a private board or notes that become a second record.
- At a natural boundary in long work (a decision, a finished stage), make sure the decision and the next step are recorded there before you move on, following that record's own rules (for example, where a comment wakes other agents, record only what they need, and change a shared record only with the consent it requires).
- When the user asks for a handoff or resume note, write it before other work in that turn, from the sources you re-read, not from the summary.

## Not this skill

Designing memory, retrieval or compaction systems is ordinary research. This skill only covers acting safely after your own context was shortened.
