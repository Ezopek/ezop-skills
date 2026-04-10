# Installation Guide

This guide covers two environments:

- **GitHub Copilot** in VS Code or IntelliJ on Windows — primary audience, most detailed
- **Claude Code** on Linux / macOS / WSL — personal / secondary setup

---

## GitHub Copilot (Windows — VS Code / IntelliJ)

GitHub Copilot does not have a plugin system. Skills are activated by pasting their content into an instructions file that Copilot reads automatically on every conversation. No installation is needed — only a file in the right place.

### How it works

Copilot reads `.github/copilot-instructions.md` from the root of the open repository. Whatever you put in that file becomes part of Copilot's context in every Chat session for that project. Both VS Code and IntelliJ respect this file.

### Step 1 — Get a copy of this repo

Download a ZIP or clone the repo somewhere on your Windows machine. You do **not** need to add it to your project — you only need to copy files from it.

**Option A — Download ZIP (no git required)**

1. Open the repo page on GitHub
2. Click **Code → Download ZIP**
3. Extract it, e.g. to `C:\tools\openai-skills\`

**Option B — Clone with git (PowerShell)**

```powershell
git clone https://github.com/ezopek/openai-skills.git C:\tools\openai-skills
```

---

### Step 2 — Create the instructions file in your project

Open **your project** in File Explorer. Check whether a `.github` folder exists at the root. If not, create it.

In File Explorer you cannot create a folder named `.github` directly — use PowerShell:

```powershell
# Run this in PowerShell, from your project root
# Replace C:\projects\my-project with your actual project path
cd C:\projects\my-project
New-Item -ItemType Directory -Force -Path .github
New-Item -ItemType File    -Force -Path .github\copilot-instructions.md
```

Then open `.github\copilot-instructions.md` in VS Code or any text editor.

---

### Step 3 — Paste the system prompt

Copy the block below and paste it into `.github\copilot-instructions.md`. This is the minimum required — Copilot will understand all skills and use them automatically.

```markdown
## AI Development Skills

You have access to the following skills. When a user request matches a skill's purpose,
activate that skill: follow its workflow, ask the questions it prescribes, and produce
the outputs it defines. Do not approximate — follow the workflow exactly.

### Planning and execution pipeline

- **$agent-ready-docs** — create or update AGENTS.md, README.md, and operational
  docs so this repo is safe and clear for AI agents to work in
- **$delivery-planner** — create a roadmap, backlog, or feature implementation plan
  that is repo-grounded and executable by AI agents in bounded slices
- **$backlog-loop-orchestrator** — run an autonomous backlog loop: plan one slice,
  implement it, verify, commit, and repeat until all items are done
- **$slice-reviewer** — review one completed implementation slice against its
  approved plan; report findings in severity order; end with accept / needs-fix / blocked
- **$repo-drift-auditor** — audit whether docs, backlog items, workflow descriptions,
  and commands still match actual code and repo state

### Quality and security

- **$pr-reviewer** — general-purpose PR / MR code quality review: correctness,
  safety, performance, maintainability, test coverage
- **$cicd-guardian** — audit, improve, and secure CI/CD pipelines: correctness,
  security, efficiency, and compliance with standards
- **$security-scanner** — deep security audit: code vulnerabilities, dependency
  risks, exposed secrets, insecure config, infra weaknesses

### Feature development

- **feature-dev** — full guided feature development: discover the codebase, clarify
  requirements, design architecture options, implement, then review quality

> **Note for Copilot users:** In Claude Code, `feature-dev` dispatches parallel sub-agents
> for codebase exploration and architecture design. In Copilot, the same workflow runs
> as a guided multi-phase conversation — Copilot explores the codebase, clarifies
> requirements, proposes architecture options, and reviews quality itself, in sequence.
> The phases and outputs are identical; only the parallel execution is not available.

---

### When to use which skill

| User says... | Use |
|---|---|
| "create a plan / backlog / roadmap" | `$delivery-planner` |
| "run the backlog / continue the loop" | `$backlog-loop-orchestrator` |
| "review this PR / review the code" | `$pr-reviewer` |
| "did we follow the plan / review the slice" | `$slice-reviewer` |
| "update AGENTS.md / update docs" | `$agent-ready-docs` |
| "scan for security / check for vulnerabilities" | `$security-scanner` |
| "audit CI/CD / fix the pipeline" | `$cicd-guardian` |
| "check if docs are stale / drift audit" | `$repo-drift-auditor` |
| "implement feature X" | `feature-dev` |

```

Commit this file so all team members share the same skill context:

```powershell
git add .github\copilot-instructions.md
git commit -m "add Copilot skill instructions"
```

---

### Step 4 — (Optional) Add full skill detail

The system prompt from Step 3 is enough for Copilot to activate and follow each skill at a high level. If you want Copilot to apply a skill's complete workflow — all questions, output sections, and quality gates — paste the full `SKILL.md` content below the system prompt.

**Size limit:** Keep `.github\copilot-instructions.md` under approximately 8 000 tokens (~32 KB). All 8 SKILL.md files combined are ~90 KB — pasting all of them will exceed the limit and content will be silently truncated. **Paste only the 1–3 skills your team uses most.**

**Example — adding the PR reviewer in full:**

1. Open `C:\tools\openai-skills\pr-reviewer\SKILL.md`
2. Copy the entire contents
3. Append to `.github\copilot-instructions.md` after the system prompt:

```markdown
---

<!-- Full workflow for $pr-reviewer -->

<paste SKILL.md content here>
```

**For the `feature-dev` workflow**, paste the file at:

```
C:\tools\openai-skills\community\feature-dev\commands\feature-dev.md
```

This file describes the 7-phase guided workflow (Discovery → Codebase Exploration →
Clarifying Questions → Architecture Design → Implementation → Quality Review → Summary).
In Copilot it runs sequentially in a single chat — Copilot reads the codebase itself
instead of dispatching parallel agents, but follows the same phases, asks the same
questions, and produces the same outputs.

```markdown
---

<!-- Full workflow for feature-dev -->

<paste community/feature-dev/commands/feature-dev.md content here>
```

**Recommended combination** — system prompt (Step 3) + these two full workflows fits
well under the size limit and covers the most common daily tasks:

| File to paste | Size | Covers |
|---|---|---|
| system prompt block (Step 3) | ~2 KB | all 8 skills, trigger routing |
| `pr-reviewer/SKILL.md` | ~10 KB | detailed PR review workflow |
| `community/feature-dev/commands/feature-dev.md` | ~4 KB | feature development workflow |
| **Total** | **~16 KB** | well within the ~32 KB limit |

---

### Step 5 — Verify it works in VS Code

1. Open the project folder in VS Code (`File → Open Folder`)
2. Open Copilot Chat (sidebar or `Ctrl+Alt+I`)
3. Type: `Review the last commit — findings in severity order`
4. Copilot should recognize the intent, activate the pr-reviewer workflow, and list findings by severity without you naming the skill

**If Copilot ignores the instructions:**

- Open VS Code Settings (`Ctrl+,`) and search for `useInstructionFiles`
- Make sure **GitHub Copilot › Chat › Code Generation: Use Instruction Files** is enabled
- This setting is on by default in VS Code 1.93 and later

---

### IntelliJ (JetBrains)

IntelliJ also reads `.github\copilot-instructions.md` automatically when the GitHub Copilot plugin is installed. No additional setup is needed beyond Steps 1–3 above.

To verify:

1. Open the project in IntelliJ
2. Open Copilot Chat (`Tools → GitHub Copilot → Open GitHub Copilot Chat`)
3. Type: `Create a backlog for feature X`
4. Copilot should recognize the intent, activate the delivery-planner workflow, and ask the appropriate planning questions

---

### How skills activate

You do not need to name the skill. Just describe what you want — Copilot reads the trigger mapping in the instructions and activates the right workflow automatically.

```
Create a backlog for the auth migration, split into bounded slices.
→ Copilot activates: delivery-planner

Review this PR — findings in severity order.
→ Copilot activates: pr-reviewer

Scan the codebase for security issues before the release.
→ Copilot activates: security-scanner

Check whether our docs still match the code before we resume work.
→ Copilot activates: repo-drift-auditor

We need to implement a rate-limiting middleware for the API.
→ Copilot activates: feature-dev
```

Explicit invocation by skill name (`$delivery-planner`, `$pr-reviewer`, etc.) also works as a fallback if Copilot does not pick up the intent automatically.

---

### Keeping skills up to date (Windows)

When this repo is updated, you need to update the `.github\copilot-instructions.md` in each of your projects. There is no auto-sync — it is a manual copy.

**Quick update with PowerShell** (if you chose Option B — full SKILL.md content):

```powershell
# Re-copy a specific SKILL.md into your instructions file
# Run this from your project root

$skillContent = Get-Content "C:\tools\openai-skills\pr-reviewer\SKILL.md" -Raw

# Append or replace as needed in .github\copilot-instructions.md
```

For the system prompt block from Step 3, updates are rare — only needed if new skills are added to this repo.

---

## Claude Code (Linux / macOS / WSL)

Claude Code uses a dedicated skills directory and a plugin system. Skills are loaded automatically at session start.

### Install skills

```bash
# Clone or update this repo
git clone https://github.com/ezopek/openai-skills.git ~/repos/openai-skills
# or: cd ~/repos/openai-skills && git pull

# Copy all skills (any subdirectory that contains SKILL.md)
for skill in ~/repos/openai-skills/*/; do
  [ -f "${skill}SKILL.md" ] && cp -r "$skill" ~/.claude/skills/
done
```

### Install community plugins

```bash
claude plugins install superpowers@claude-plugins-official
claude plugins install feature-dev@claude-plugins-official
```

These plugins add additional skills: `superpowers:brainstorming`, `superpowers:writing-plans`, `superpowers:systematic-debugging`, `superpowers:test-driven-development`, `superpowers:verification-before-completion`, and `feature-dev:feature-dev`.

### Verify

```bash
ls ~/.claude/skills/
# Expected output includes: delivery-planner  pr-reviewer  security-scanner  ...
```

Claude Code discovers skills automatically. The `superpowers` plugin instructs Claude to check for relevant skills before every response — no additional configuration needed.

### Add skills to global CLAUDE.md (optional)

If you want Claude Code to mention skills proactively even without the `superpowers` plugin, paste the same system prompt block from Step 3 above into `~/.claude/CLAUDE.md`:

```bash
cat >> ~/.claude/CLAUDE.md << 'EOF'

## Available AI Development Skills

[paste the system prompt block from Step 3 here]
EOF
```

### Keeping skills up to date (Linux / macOS)

```bash
cd ~/repos/openai-skills
git pull

for skill in */; do
  [ -f "${skill}SKILL.md" ] && cp -r "$skill" ~/.claude/skills/
done
```

---

## Recommended workflow

Once installed, the skills work together as a pipeline. You do not need to use all of them — start with the ones relevant to your current task.

```
[new repo or returning after a break]
        │
        ▼
$repo-drift-auditor        ← check whether docs still match the code
        │
        ▼
$agent-ready-docs          ← prepare AGENTS.md and repo documentation
        │
        ▼
$delivery-planner          ← create backlog / roadmap / feature plan
        │
        ▼
$backlog-loop-orchestrator ← execute plan slice by slice
        │          ↑
        ▼          │
$slice-reviewer            ← (optional) accept each slice before committing
        │
        ▼
$pr-reviewer               ← quality gate before merge
        │
        ▼
$security-scanner          ← (optional) before releases
$cicd-guardian             ← (optional) after pipeline changes
```

---

## Troubleshooting

**Copilot ignores `.github\copilot-instructions.md`**
- In VS Code: `Ctrl+,` → search `useInstructionFiles` → confirm it is enabled
- The file must be at the exact path `.github\copilot-instructions.md` (not `.github\instructions.md` or anywhere else)
- The `.github` folder must be at the repository root, not inside a subdirectory

**Copilot follows instructions inconsistently**
- The file may be too long. Try keeping it under 32 KB. If you have multiple full SKILL.md files pasted in, remove the ones you use least and keep only the system prompt block.
- Copilot Chat uses the instructions file; inline Copilot suggestions (ghost text) do not

**`feature-dev` — Copilot skips phases or jumps straight to implementation**
- This usually means the instructions were truncated. Make sure the full `feature-dev.md` workflow is in the file, not just the system prompt description.
- Explicitly tell Copilot to follow the full workflow: `Use feature-dev workflow — start from Phase 1, do not skip phases`
- If Copilot still skips: paste the feature-dev.md content at the top of the file, before the system prompt block

**Skill not found in Claude Code**
- Confirm the directory exists: `ls ~/.claude/skills/delivery-planner/`
- Confirm `SKILL.md` is present inside it
- Restart Claude Code after copying new skills

**Skills are outdated**
- Pull the latest from this repo and re-copy, or re-download the ZIP and replace the files
