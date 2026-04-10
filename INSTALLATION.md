# Installation Guide

This guide covers two environments:

- **GitHub Copilot** in VS Code or IntelliJ on Windows — primary audience, most detailed
- **Claude Code** on Linux / macOS / WSL — personal / secondary setup

Requires **Copilot Business** or **Copilot Enterprise** (agent skills, custom instructions, and agent mode are available on all paid plans including Pro).

---

## GitHub Copilot (Windows — VS Code / IntelliJ)

Copilot supports **Agent Skills** — folder-based capability packages that Copilot discovers and activates automatically. Each skill in this repo is already in the right format (`SKILL.md` with `name` and `description` frontmatter). You copy skill folders into your project's `.github/skills/` directory, and Copilot loads them on demand when the user's prompt matches the skill's description.

This follows the [Agent Skills open standard](https://agentskills.io), supported by Copilot, Claude Code, and other LLM agents.

### How it works

Copilot reads skill folders from `.github/skills/<skill-name>/SKILL.md` in your repository. Each skill has a `description` field in its frontmatter — Copilot uses this to decide whether to activate the skill based on the user's prompt. Skills can also be invoked manually as `/<skill-name>` slash commands in Copilot Chat.

Skills are loaded **on demand** (only when relevant to the current prompt), so there are no size limit concerns — unlike `copilot-instructions.md`, which is injected into every conversation.

### Step 1 — Get a copy of this repo

Download a ZIP or clone the repo somewhere on your Windows machine. You do **not** need to add it to your project — you only need to copy files from it.

**Option A — Download ZIP (no git required)**

1. Open the repo page on GitHub
2. Click **Code → Download ZIP**
3. Extract it, e.g. to `C:\tools\ezop-skills\`

**Option B — Clone with git (PowerShell)**

```powershell
git clone https://github.com/ezopek/ezop-skills.git C:\tools\ezop-skills
```

---

### Step 2 — Copy skills into your project

Create `.github/skills/` in your project and copy the skill folders you want:

```powershell
# Run this in PowerShell, from your project root
cd C:\projects\my-project

# Create the skills directory
New-Item -ItemType Directory -Force -Path .github\skills

# Copy all skills at once
$source = "C:\tools\ezop-skills"
Get-ChildItem -Path $source -Directory | Where-Object {
    Test-Path (Join-Path $_.FullName "SKILL.md")
} | ForEach-Object {
    Copy-Item -Path $_.FullName -Destination ".github\skills\$($_.Name)" -Recurse -Force
}
```

Or copy individual skills:

```powershell
# Copy only the skills you need
Copy-Item -Recurse -Force "C:\tools\ezop-skills\pr-reviewer" ".github\skills\pr-reviewer"
Copy-Item -Recurse -Force "C:\tools\ezop-skills\delivery-planner" ".github\skills\delivery-planner"
Copy-Item -Recurse -Force "C:\tools\ezop-skills\security-scanner" ".github\skills\security-scanner"
```

Commit the skills so all team members have access:

```powershell
git add .github\skills
git commit -m "add AI development skills for Copilot"
```

---

### Step 3 — (Optional) Add a trigger guide to copilot-instructions.md

The skills work without any additional configuration — Copilot reads each skill's `description` and activates it automatically. However, if you want to add a routing guide so Copilot has an overview of all available skills, you can add it to `.github/copilot-instructions.md`:

```powershell
New-Item -ItemType Directory -Force -Path .github
New-Item -ItemType File -Force -Path .github\copilot-instructions.md
```

Paste this into `.github/copilot-instructions.md`:

```markdown
## When to use which skill

| User says... | Use |
|---|---|
| "create a plan / backlog / roadmap" | `/delivery-planner` |
| "run the backlog / continue the loop" | `/backlog-loop-orchestrator` |
| "review this PR / review the code" | `/pr-reviewer` |
| "did we follow the plan / review the slice" | `/slice-reviewer` |
| "update AGENTS.md / update docs" | `/agent-ready-docs` |
| "scan for security / check for vulnerabilities" | `/security-scanner` |
| "audit CI/CD / fix the pipeline" | `/cicd-guardian` |
| "check if docs are stale / drift audit" | `/repo-drift-auditor` |
```

This is lightweight (~1 KB) and complements the full skill definitions in `.github/skills/`. Keep `copilot-instructions.md` short — it is injected into **every** Copilot conversation, so use it only for always-on context like coding standards and routing guides, not full skill workflows.

---

### Step 4 — Verify it works

**VS Code:**

1. Open the project folder in VS Code (`File → Open Folder`)
2. Open Copilot Chat (sidebar or `Ctrl+Alt+I`)
3. Switch to **Agent mode** (select "Agent" from the mode dropdown at the top of the chat panel)
4. Type: `Review the last commit — findings in severity order`
5. Copilot should recognize the intent, activate the pr-reviewer skill, and list findings by severity

**If skills don't activate:**

- Make sure you're using **Agent mode** in Copilot Chat (not "Ask" or "Edit" mode) — skills require agent mode
- Open VS Code Settings (`Ctrl+,`) and search for `useInstructionFiles` — confirm it is enabled
- Verify the skill folder exists at `.github/skills/<skill-name>/SKILL.md` (not nested deeper)
- Check that `SKILL.md` has valid `name` and `description` in its YAML frontmatter

**IntelliJ (JetBrains):**

1. Open the project in IntelliJ
2. Open Copilot Chat (`Tools → GitHub Copilot → Open GitHub Copilot Chat`)
3. Type: `Create a backlog for feature X`
4. Copilot should recognize the intent and activate the delivery-planner skill

---

### How skills activate

You do not need to name the skill. Just describe what you want — Copilot reads each skill's `description` and decides whether to load it.

```
Create a backlog for the auth migration, split into bounded slices.
→ Copilot activates: delivery-planner

Review this PR — findings in severity order.
→ Copilot activates: pr-reviewer

Scan the codebase for security issues before the release.
→ Copilot activates: security-scanner

Check whether our docs still match the code before we resume work.
→ Copilot activates: repo-drift-auditor
```

Explicit invocation as a slash command (`/delivery-planner`, `/pr-reviewer`, etc.) also works if Copilot does not pick up the intent automatically.

---

### Personal skills (cross-project)

If you want certain skills available in **all** your projects without copying them into each repo, place them in your personal skills directory:

```powershell
# Windows — personal skills directory
$skillsDir = "$env:USERPROFILE\.copilot\skills"
New-Item -ItemType Directory -Force -Path $skillsDir

# Copy a skill for personal use
Copy-Item -Recurse -Force "C:\tools\ezop-skills\pr-reviewer" "$skillsDir\pr-reviewer"
```

Personal skills are visible only to you and are not shared with the team.

---

### Other Copilot customization mechanisms

Beyond skills, Copilot supports several other customization primitives that can complement these skills:

| Mechanism | Location | Purpose |
|---|---|---|
| **Repository instructions** | `.github/copilot-instructions.md` | Always-on project-wide norms, coding standards |
| **Path-specific instructions** | `.github/instructions/*.instructions.md` | Rules that apply only to matching file patterns (via `applyTo` globs) |
| **Prompt files** | `.github/prompts/*.prompt.md` | Reusable prompt templates invoked via `/` slash commands |
| **Custom agents** | `.github/agents/*.agent.md` | Specialist personas with constrained tool access |

---

### Keeping skills up to date (Windows)

```powershell
# Pull latest from this repo
cd C:\tools\ezop-skills
git pull

# Re-copy into your project
cd C:\projects\my-project
$source = "C:\tools\ezop-skills"
Get-ChildItem -Path $source -Directory | Where-Object {
    Test-Path (Join-Path $_.FullName "SKILL.md")
} | ForEach-Object {
    Copy-Item -Path $_.FullName -Destination ".github\skills\$($_.Name)" -Recurse -Force
}

git add .github\skills
git commit -m "update AI development skills"
```

---

## Claude Code (Linux / macOS / WSL)

Claude Code uses a dedicated skills directory and a plugin system. Skills are loaded automatically at session start.

### Install skills

```bash
# Clone or update this repo
git clone https://github.com/ezopek/ezop-skills.git ~/repos/ezop-skills
# or: cd ~/repos/ezop-skills && git pull

# Copy all skills (any subdirectory that contains SKILL.md)
for skill in ~/repos/ezop-skills/*/; do
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
cd ~/repos/ezop-skills
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

**Copilot does not activate skills**
- Make sure you are in **Agent mode** (not "Ask" or "Edit" mode) — skills only work in agent mode
- Verify the folder structure: `.github/skills/<skill-name>/SKILL.md` (the directory name must match the `name` field in SKILL.md frontmatter)
- In VS Code: `Ctrl+,` → search `useInstructionFiles` → confirm it is enabled
- The `.github` folder must be at the repository root, not inside a subdirectory
- Try explicit invocation: type `/<skill-name>` (e.g. `/pr-reviewer`) to verify Copilot sees the skill

**Copilot ignores `copilot-instructions.md`**
- The file must be at the exact path `.github/copilot-instructions.md`
- Copilot Chat uses the instructions file; inline completions (ghost text) do not
- Keep this file short — it is injected into every conversation and competes for context space

**Skill not found in Claude Code**
- Confirm the directory exists: `ls ~/.claude/skills/delivery-planner/`
- Confirm `SKILL.md` is present inside it
- Restart Claude Code after copying new skills

**Skills are outdated**
- Pull the latest from this repo and re-copy, or re-download the ZIP and replace the files
