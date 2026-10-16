# Official Claude Code harness features (fetched 2026-10-16 from code.claude.com/docs)

Items marked UNCONFIRMED were not verified. Check exact field names at the linked pages before relying on them.

## Subagents (`.claude/agents/*.md`)
Source: https://code.claude.com/docs/en/sub-agents

- **Frontmatter fields:**
  - `name` and `description` (both required).
  - `tools` and `disallowedTools`.
  - `model`: sonnet, opus, haiku, fable, a full model ID, or inherit.
  - `permissionMode`.
  - **`skills`:** the full content of each listed skill is injected into the agent at startup, up to 32 skills. Skills with `disable-model-invocation: true` cannot be preloaded.
  - **`memory`:** `user`, `project` (the recommended default) or `local`. Memory lives in `.claude/agent-memory/<name>/MEMORY.md`, and the first 200 lines or 25KB load at start.
  - `maxTurns`, `effort`, `background`, `isolation: worktree`, `initialPrompt`, `omitClaudeMd`.
- **Unknown fields are silently ignored**, so a typo fails without an error.
- **Model resolution order:**
  1. The model given when the agent is invoked.
  2. The frontmatter `model`.
  3. The `CLAUDE_CODE_SUBAGENT_MODEL` setting.
  4. The main conversation's model.
- **Precedence (highest first):** managed settings, then the CLI `--agents` flag, then project `.claude/agents/`, then user `~/.claude/agents/`, then plugin `agents/`.
- **What a subagent inherits:** not the parent conversation. A fork does inherit it.
- **Nesting and concurrency:** nesting goes 3 levels deep by default, and up to 20 subagents can run at once.

## Skills (`SKILL.md`)
Source: https://code.claude.com/docs/en/skills

- **Layout:** a folder with `SKILL.md` (keep it under 500 lines), plus optional `reference.md`, `examples.md` and `scripts/`. Scripts are executed, not loaded into context.
- **Frontmatter fields:**
  - `name` and `description`. Put the use case first; `description` and `when_to_use` together are capped at 1,536 characters.
  - `when_to_use`, `arguments`.
  - `disable-model-invocation`, `user-invocable`.
  - `allowed-tools`, `model`, `effort`.
  - `context: fork` together with `agent:`, which runs the skill as a subagent.
  - `hooks`, `paths` (a file glob that limits when the skill auto-loads).
- **Progressive disclosure:** only skill descriptions are always in context. The body loads when the skill is invoked. After compaction, recent skill bodies are re-attached: up to 5,000 tokens each, within a 25,000-token total.
- **Scopes:** managed, then personal `~/.claude/skills/`, then project `.claude/skills/`. Plugin skills are namespaced `plugin:skill`.

## Plugins (the way to package the harness)
Sources: https://code.claude.com/docs/en/plugins/create and the related plugin pages.

- **Layout:**
  - `.claude-plugin/plugin.json` (the manifest)
  - `skills/`, `agents/`
  - `hooks/hooks.json`
  - `.mcp.json`
  - `output-styles/`
  - `commands/` (the older form)
- **Testing:** `claude --plugin-dir ./x` loads a plugin for one session, and `claude plugin validate` checks it.
- **Private GitHub marketplace on a new machine:**
  1. Run `gh auth login`.
  2. Run `claude plugin marketplace add owner/repo`.
  3. Run `claude plugin install name@marketplace --scope user`.
- **Auto-update** is off by default for third-party marketplaces.
- **Limitation:** plugin subagents ignore their own `hooks` and `mcpServers` frontmatter. Put hooks in the plugin's `hooks.json` instead.

## Hooks
Sources: https://code.claude.com/docs/en/hooks and https://code.claude.com/docs/en/hooks-guide

- **33 events. The useful ones here:**
  - `SessionStart`: injects context.
  - `UserPromptSubmit`: sees your prompt text, and can add context or block.
  - `PreToolUse`: can allow, deny or ask, and can modify the tool's input.
  - `PostToolUse`.
  - `SubagentStop` and `Stop`: can block to make the agent keep going, and receive the agent's last message.
  - `PreCompact` and `PostCompact`.
  - `SessionEnd`.
  - `TaskCompleted`: exit code 2 blocks it.
  - `InstructionsLoaded`.
  - `FileChanged`.
- **Handler types:** `command`, `http`, `mcp_tool`, `prompt` (a single model call) and `agent` (experimental).
- **Inputs:** every hook gets `transcript_path`, which supports writing session retrospectives.
- **UNCONFIRMED:** the exact input fields for each event. The reference page was truncated when fetched.

## Memory
Source: https://code.claude.com/docs/en/memory

- **CLAUDE.md levels:** managed, project, user (`~/.claude/CLAUDE.md`) and local (gitignored). Keep each file under 200 lines.
- **Imports:** `@path` imports other files, up to 4 hops deep.
- **Rules:**
  - `.claude/rules/*.md` holds one topic per file.
  - `paths:` frontmatter limits a rule to matching files.
  - `~/.claude/rules/` holds global rules.
- **Auto memory:**
  - Stored at `~/.claude/projects/<project>/memory/MEMORY.md`, an index with the first 200 lines loaded, plus topic files.
  - Controlled by the `autoMemoryEnabled` and `autoMemoryDirectory` settings.

## Agent teams, settings, permissions, models

- **Agent teams** (experimental): turned on with `CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS=1`.
  - A lead runs teammates that share a task list and a mailbox.
  - Teammates do not apply the `skills` field.
  - They cost much more tokens than subagents.
- **Settings precedence:** managed, then CLI, then local, then project, then user.
- **Permission modes:** default (shown as "manual"), `acceptEdits`, `plan`, `auto`, `dontAsk`, `bypassPermissions`.
  - Deny rules apply in every mode.
  - `auto` cannot be set in project settings.
- **Model aliases:** `best`, `fable`, `opus`, `sonnet`, `haiku`, `[1m]` variants, and `opusplan` (Opus while planning, Sonnet while executing).
- **Effort levels:** low through max.

## Sync across machines

- There is no official dotfiles or sync feature.
- **What the docs do support:**
  - Commit the project `.claude/` folder.
  - Publish a personal plugin to a private GitHub marketplace.
  - claude.ai account sync of skills and plugins, via `syncClaudeAiSkills` and `syncClaudeAiPlugins`.
- Relocate the config folder with `CLAUDE_CONFIG_DIR`.
- **Common practice:** keep a git dotfiles repo for `~/.claude`. This is not an official recommendation.
