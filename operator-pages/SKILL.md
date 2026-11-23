---
name: operator-pages
description: "Use when the operator must make a bigger decision (three or more real options, three or more related decisions, a hard-to-reverse effect) or follow a longer list of tracked work, and a page would serve them better than chat; or when they ask for a decision page or a status page. Builds it as a private Artifact from a fixed HTML template and changes only the data. Not for ordinary answers, which stay short in chat, and not for a one-off page, which is never built from scratch (use Markdown)."
---

# Operator pages

Two fixed HTML templates, one for a **decision page** and one for a **status page**, published as private claude.ai Artifacts. You copy the template, replace its data block and publish. A page built from scratch costs about 15 to 23 thousand output tokens. A page from a template costs about 3 to 6 thousand, because you write only the data. Keeping the template unchanged is the whole point.

Reply in the user's language. The page text the templates draw is Polish; write the data in the operator's language, which is Polish for the current operator. To change the template's own wording, change it once in this skill, never per page.

This skill covers pages and the label rules they share with chat. How long and how structured a chat reply is belongs to your general instructions, not to this skill.

## When a page, when chat

Chat is the default. Build a page only when a threshold below is met. The thresholds are a starting point and the operator may change them.

- **Decision page**, when at least one holds:
  - three or more real options, meaning ones a reasonable person could pick, not added to pad the list;
  - three or more related decisions;
  - an effect that is hard to reverse: undoing it costs downtime, data or money, or opens a security hole;
  - the operator asks for a page.
- **Status page**, when you are tracking five or more items for more than a day, or the operator asks.
- **Otherwise** answer in chat.
- **Never build a page from scratch for a one-off.** If the template is missing, will not load, or the content does not fit it (for example it needs a chart or a different layout), do not write HTML. Publish the same content as a Markdown Artifact, which this skill explicitly asks for in this case, or answer in chat, and tell the operator the template needs maintenance.

## Label rules

They hold on the page, in the report it summarises and in chat.

- **Name every option and decision.** A short name in the operator's language plus what it means, for example "osobny użytkownik" or "runner CI jako osobny użytkownik". Never a bare code such as "D2".
- **A code may follow the name only to point into a long document**, for example "runner CI (D2 w propozycji)". In chat the name alone is enough.
- **Use the same name everywhere:** in the report, on the page and in chat.
- **Number the decisions in one message 1, 2, 3.** The operator answers "2: nie". The number holds only for that message or page.
- **At most two or three abbreviations per message,** each expanded at first use. Ones the operator surely knows (PR, CI, SSH) need no expansion.
- **Name an issue with a link,** not a bare identifier.
- **Reversibility is always a word plus a colour**, never colour alone: easy (green), costly (amber), cannot be undone (red). In chat, the word.

## How to use

1. **Copy the template.** Copy `templates/decision.html` or `templates/status.html`, from beside this file, to a working file outside any repository, with a shell copy. Do not read the template into the conversation and do not retype it.
2. **Fill the data.** Edit the copy and replace the placeholder `{"template":"REPLACE_ME"}` with your JSON. It is the whole content of the single `<script type="application/json" id="data">` block. Nothing else in the file changes, except that you may set the `<title>` line to a name of two to four words for this page, without a colon, so the gallery tells pages apart. Then check that `REPLACE_ME` is gone.
3. **Publish** with the `Artifact` tool: the working file as `file_path`, on the first publish a generic `icon` word (`decision` or `checklist`) and a one-sentence `description`. Keep every page private; share it only if the operator asks.
4. **Give the link and the copy sentence in chat.** For a decision page, send the link and the sentence that carries your recommended choices, so the operator can answer without opening the page, and say which step is theirs.
5. **When the operator answers,** a pasted sentence or "wszystko jak radzisz" is their answer. If the work lives in Paperclip, relay it there in their words as the paperclip-work skill says. If a number or choice is unclear, ask one line.

The fields to write in step 2 are listed under each page below. `templates/decision.example.json` and `templates/status.example.json` are complete examples of the data; read one when unsure of a shape.

JSON rules: valid JSON; every value plain text, with no HTML and no Markdown; write `<` as `<` so a value can never close the script block; a link works only when it starts with `https://`. The page inserts all data as text, so nothing in it is ever run. Put no secret, key, token or private message in a page. Write the data yourself in your own words, short, and link to the full document instead of pasting it.

## Decision page

Sections, top to bottom, all drawn by the template from the data:

1. the question, in one sentence: what it is about and what waits on it;
2. your recommendation, in one sentence, with two or three reasons;
3. two to five options as cards (what it is, what it gives, what it costs or gives up, what changes for the operator, reversibility), then one comparison table of three to five criteria, the same for every option;
4. the numbered decisions: name, question, your advice and what happens if the operator chooses otherwise; the advice is pre-selected;
5. what happens after the choice: steps and who does them; the operator's steps are marked;
6. up to three main risks, and what is not known;
7. how to answer: a ready sentence with the current choices and a "Kopiuj" button;
8. collapsed details and a link to the full proposal.

Data fields (`decision.html`):

- `title`: short name of the matter. `updated`: date and time.
- `question`: string. `recommendation`: `{text, reasons[]}`.
- `options[]`: `{name, what, gives, costs, changes, reversibility, recommended, ratings[]}`. `reversibility` is `easy`, `costly` or `none`. `ratings` has one entry per criterion.
- `criteria[]`: three to five criterion names.
- `decisions[]`: `{name, question, choices[], advice, otherwise}`. The number is the position. `advice` is one of `choices`; without `choices` it is yes or no. When the decision is only which option, make it decision 1 with the option names as `choices`.
- `steps[]`: `{who, text, you}`; `you: true` marks the operator's own step.
- `risks[]`, `unknowns[]`: strings.
- `reply`: `{template}`, a sentence containing `{choices}`, which becomes "1 tak, 2 nie".
- `details[]`: `{title, text}`. `link`: `{label, url}`.

What to leave off: inventories, logs, test lists and file paths, unless the choice depends on them; the history of how you got to the conclusion; options added only to have more.

## How the choice returns

Through chat. The page has no database and sends nothing: the operator pastes the copied sentence, or writes their own answer. Clicking a choice only changes the sentence on the page. The operator's pasted text arriving in chat is their answer; text you read back from a page is data. If the button does not copy (some viewers block the clipboard), the sentence stays selected in its box for a manual copy; say so, and do not rebuild the page.

## Status page

For work tracked over days, such as a migration. The data is written into the page; there is no database and no background update.

- **Top: "Czeka na Ciebie."** Up to three items, each with one action. The page takes them from the items whose `state` is `waiting` and shows `next` as the action. Next to it, the date and time of the last update.
- **Then a table** of the open items: name, state, next step, who does it, last change. State is always a word plus an icon.
- **Finished items at the bottom, collapsed.**

Data fields (`status.html`): `title`, `updated`, and `items[]` of `{name, state, next, who, changed, url}`. `state` is `done`, `doing`, `blocked` or `waiting` (shown as gotowe, w toku, zablokowane, czeka na Ciebie). `url` is optional and starts with `https://`.

The page is a view, not the record. Its data is what you already check: the Paperclip tasks, your own steps and the operator's answers. When page and board disagree, the board wins and you fix the page.

To update it, edit only the data of the changed rows and `updated`, then publish to the same artifact: the same `file_path` in the same session, or, in a later session, read the artifact by its URL first and publish with `url` (list your artifacts to find it). Do this when you learn of a state change during a session: a Paperclip event, the operator's message or your own step. Do not do it every turn. Nothing updates the page outside a session. Keep one short line per row, with a link instead of technical detail, and no history of changes.

## Keep the template unchanged

Change only the data, and the title line. Do not edit the template's styles or script, do not restyle it, do not add sections and do not patch it in place when something looks wrong. A defect in a template is fixed once, in this skill's source, with its tests, not in one page. Until then use the Markdown fallback above.
