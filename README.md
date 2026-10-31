# ezop-skills

A small, growing collection of portable agent skills. Each skill is a folder with a `SKILL.md` that follows the common Agent Skills layout (`name` and `description` frontmatter), so it can be copied into the skill locations that supported clients read.

## Current skill

### scope-discipline

Keeps design and planning work tied to what you actually asked for. It targets the point where an agent quietly turns a simple request into roles, approvals, state machines and extra services nobody requested.

- **Coaching first.** For ambiguous or consequential design, the agent talks it through in short steps: outcome, normal user journey, what "done" means, non-goals, and how much complexity you want to own. It asks the most decision-relevant open question rather than handing over a large document for blanket approval.
- **Real alternatives only.** When a choice is material, you get the simplest complete approach, the heavier option that is actually relevant, what each costs, a recommendation, and whether the heavier one can be added later.
- **Small tasks stay fast.** A clear, small task is simply done: no interview, no design file, no extra approval step.
- **Review against intent.** Plans and diffs are checked against your original request: what is missing, what was added unasked, and what could go without losing a required guarantee.
- **Safety stays.** Existing policies, data-loss prevention, input validation and necessary security remain in force. This is not a ban on locks or approvals, only on adding them without a reason.

The skill is guidance that lowers risk. It does not enforce anything.

### Using it

Describe your task in natural language. A client that supports skills can pick the skill from its description when you are designing a tool or workflow, planning an implementation, or asking for a scope or overengineering review. Naming the skill explicitly is optional, and how (or whether) a client supports that depends on the client.

## Installation and updates

See [INSTALLATION.md](INSTALLATION.md). A checkout of this repository is only a source; it does not activate anything by itself.

## Earlier packages

This repository used to hold eight other skill packages and a bundle of community material. They were removed from the current tree and remain recoverable from Git history. Removing them here does not uninstall copies you installed earlier; those stay wherever you put them until you remove them yourself.

## Adding skills later

Each skill lives in its own top-level folder, named after the skill, with a `SKILL.md` inside. Nothing else is required.
