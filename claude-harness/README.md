# claude-harness

My personal Claude Code harness, packaged as a plugin. The design rationale is in `BLUEPRINT.md`.

## New machine setup (about 20 min)

```bash
# 1. Install Claude Code and the GitHub CLI, then:
gh auth login
claude plugin marketplace add beingwithand/claude-harness
claude plugin install harness@claude-harness --scope user

# 2. Clone this repo for editing + run the installer (global CLAUDE.md, data dirs)
git clone https://github.com/beingwithand/claude-harness ~/code/claude-harness
~/code/claude-harness/install.sh
```

## What's inside

| Path | Purpose |
|---|---|
| `global/CLAUDE.md` | Global rules, symlinked to `~/.claude/CLAUDE.md`. Hand-written, kept under 200 lines |
| `agents/` | Reusable subagents, each with its own `skills:`, `model:` and `memory:` |
| `skills/` | Small, curated skills: handoff (with cold-read test), compact-prep, intake, web-research, verify, retro, why, mishap |
| `hooks/` | Automatic logging of prompts and session ends; verification gate; per-edit syntax step check (`docs/VERIFICATION.md`); usage guard (context/5h/7d advice from the status-line state); pre-compaction snapshot and post-compaction/clear re-injection |
| `schema/` | Ontology plus the event/decision/mishap record formats |
| `templates/project/` | Standard skeleton for every new project |
| `rubrics/` | Self-eval sheets for each task type |

## Data (separate from code)

Logs and session notes are written to `$HARNESS_DATA` (default `~/harness-data`). That directory is its own private git repo, auto-committed, so nothing ever lives only on one laptop.

## Rules for changing the harness

- Agents may **propose** changes to rules and skills. I approve them, and each one is committed with its justification.
- A change merges only if the eval set doesn't regress (see `BLUEPRINT.md` §0.5).
- Treat every skill and hook as executable code. Never install third-party ones without reading them first.
