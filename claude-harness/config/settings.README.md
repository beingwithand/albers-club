# `config/settings.json`: recommended `~/.claude/settings.json`

This is a template for your **user** settings file. It gives Claude wide permissions inside clear limits: auto mode, a sandbox for Bash, and a strong deny list.

Key names were checked against the official settings reference on 2026-10-16. Anything still marked **verify** below should be checked at https://code.claude.com/docs/en/settings before you rely on it.

For a credible outside reference, compare with Trail of Bits' config: https://github.com/trailofbits/claude-code-config

JSON has no comments, so every explanation lives in this file.

## How it gets installed: merged, never overwritten

`mac/bootstrap.sh` (the `settings` step) does the merge. `install.sh` should copy the same logic.

1. **Back up first:** `cp ~/.claude/settings.json ~/.claude/settings.json.bak.<timestamp>`.
2. **Fill in the placeholder:** replace `__HOME__` with the real `$HOME`. Settings values are not shell-expanded.
3. **Deep-merge.** Existing values win for scalars and objects, and the `allow`/`ask`/`deny` lists are unioned:
   ```bash
   jq -s '.[0] as $old | .[1] as $new | ($new * $old)
     | .permissions.allow = ((($old.permissions.allow // []) + ($new.permissions.allow // [])) | unique)
     | .permissions.deny  = ((($old.permissions.deny  // []) + ($new.permissions.deny  // [])) | unique)
     | .permissions.ask   = ((($old.permissions.ask   // []) + ($new.permissions.ask   // [])) | unique)' \
     ~/.claude/settings.json <(sed "s#__HOME__#$HOME#g" config/settings.json) > /tmp/s.json \
   && jq -e . /tmp/s.json >/dev/null && mv /tmp/s.json ~/.claude/settings.json
   ```
   Because existing values win, a `defaultMode` already in your file is **kept**. Change it by hand if you want `auto`.
4. **Check the result** with `claude doctor` and `/permissions` inside Claude Code.

Do **not** symlink this file into `~/.claude/`. Claude Code and `/config` write to `settings.json`, and those writes would land in the repo.

## Keys

### `$schema`
Gives your editor autocomplete and validation (SchemaStore). Claude Code ignores it.

### `permissions.defaultMode: "auto"`
In auto mode, a classifier approves routine actions and stops for risky ones.
- `auto` works **only in user settings**. Project and local settings files ignore `auto` and `bypassPermissions`.
- **Alternative: `bypassPermissions`** (`--dangerously-skip-permissions`). It skips every prompt.
  - The docs say to use it only in isolated containers or VMs. On your main Mac, with your password manager, browser sessions and GitHub token, one prompt injection could delete or leak data with no checkpoint.
  - **Deny rules still apply in every mode**, but they are pattern matches and easy to get around (see "Limits" below).
  - Recommendation: keep `auto` plus the sandbox. Use bypass only in a throwaway VM or devcontainer.
- Optional hard lock: `"permissions": {"disableBypassPermissionsMode": "disable"}` stops bypass mode from being turned on at all (**verify** the key).

### `permissions.allow`
These are **read-only** commands: ls, cat, rg, grep, find, jq, and git or gh commands that only view things.
- `Bash(cmd *)` is the prefix form. A bare `Bash(cmd)` matches that exact command only.
- `WebSearch` is allowed. `WebFetch` is in `ask`, because fetched pages are the main way prompt injection gets in. In auto mode it is usually approved anyway. Move it to `allow` if prompts get annoying.

### `permissions.ask`
These always prompt, even in auto mode:
- pushes and history rewrites: `git push`, `reset --hard`, `clean`, `rebase`, `branch -D`
- publishing and releases
- `sudo`
- the 1Password CLI (`op`)
- system changes: `pmset`, `launchctl`, `defaults write`, `crontab`
- AppleScript (`osascript`), which can drive any app

Rules are evaluated **deny first, then ask, then allow**.

### `permissions.deny`: the fences

| Group | Rules | Why |
|---|---|---|
| Mass delete | `rm -rf /`, `~`, `$HOME`, `__HOME__` (literal path), `rm -fr`, `sudo rm` | Unrecoverable. |
| History loss | `git push --force` / `-f` / `--force-with-lease` / `--mirror` | Rewrites remote history, so GitHub stops being a backup. If you truly need it, run it yourself. |
| GitHub | `gh repo delete`, visibility changes, `gh auth token` | Deleting a backup repo, making private data public, printing your token. |
| curl \| sh | `curl … \| sh/bash/zsh`, `wget … \| sh`, and bare `sh`/`bash`/`zsh` | Bash rules match each part of a pipeline separately, so the bare-shell rules catch the `\| sh` part (**verify** that compound-command splitting works this way in your version). |
| Disk / system | `diskutil erase*`, `dd`, `mkfs`, `chmod -R 777`, `tmutil delete`, `fdesetup disable`, `csrutil` | Wipes disks or backups, or weakens security. |
| Secrets via Bash | `security find-*-password`, `dump-keychain`, `op item get --reveal`, `cat ~/.ssh/*`, `cat .env` | Best effort only. See "Limits". |
| Secret files | `Read(~/.ssh/**)`, `~/.aws`, `~/.gnupg`, gcloud, `gh/hosts.yml`, 1Password/Bitwarden data, Keychains, `.netrc`, `.npmrc`, `.pypirc`, docker/kube config, `**/.env*`, `*.pem`, `*.key`, SSH keys, `**/secrets/**` | Credential theft. A Read deny also blocks Edit and Write on the same path. |
| Anti reward-hacking | `Edit`/`Write` on `/evals/**`, `**/evals/**`, `/rubrics/**`, `**/rubrics/**` | BLUEPRINT §0.5: producing agents must not edit tests, rubrics or eval sets. A leading `/` means relative to the project; `**/` matches at any depth. |
| Self-protection | `Edit`/`Write` on `~/.claude/settings.json` | Claude can't loosen its own fences. Edit the file yourself, or change the template and re-merge. |

**Evals and rubrics.** The deny rules apply to *every* session, including the main one, because user-level deny rules can't be scoped to "producing agents only."
- That is intentional. Agents **propose** eval and rubric changes, for example as a diff in `proposals/`, and you apply them by hand. This matches BLUEPRINT §0 rule 4.
- If that becomes too strict, move these four rules out of user settings and into each project's `.claude/settings.json`. Or add a `PreToolUse` hook that denies these paths only when `agent_type` is set (**verify** that the hook input includes the agent name).

Path syntax: `~/` is your home folder, `//abs/path` is an absolute path, `/x` is relative to the project, and `**` matches any depth.

### `sandbox`
- **`enabled: true`:** Bash runs inside the OS sandbox (Seatbelt on macOS). Writes are limited to the working folder, and network access only reaches allowed domains. The sandbox covers **Bash only**. Read, Edit and WebFetch are governed by the permission rules.
- **`autoAllowBashIfSandboxed: true`:** sandboxed Bash commands don't prompt. The sandbox is the safety net.
- **`allowUnsandboxedCommands: false`:** Claude cannot retry a command outside the sandbox. This is what makes the sandbox a real boundary.
- **`network.allowedDomains`:** GitHub, npm, PyPI, Homebrew and Supabase. Add domains as you need them. Restricting the network this way is far more robust than Bash deny patterns on `curl`.
  - **Verify** the wildcard syntax (`*.supabase.co`).
  - **Verify** whether the sandbox blocks `brew install` or `gh` in your setup. If it does, add those domains instead of turning the sandbox off.
- Optional: the sandbox may also support filesystem read restrictions, such as a deny-read list for `~/.ssh` (**verify** the key name). That would also cover `cat ~/.ssh/...` through Bash.

### `env`
These are set for every Claude Code session.
- **`HARNESS_CTX_BUDGET`:** your working context budget for the status line and usage guard (see `statusLine`).
- **`HARNESS_DATA`:** where the logging hooks write (`~/harness-data`). `__HOME__` is filled in at install, because settings values are not shell-expanded.
- **`CLAUDE_CODE_SUBAGENT_MODEL: "sonnet"`:** subagents with no `model:` use Sonnet instead of the expensive main model. Per BLUEPRINT §0.5, each agent file should still set `model:`.
- **`CLAUDE_CODE_MAX_SUBAGENT_SPAWN_DEPTH: "2"`:** limits how deep subagents can nest, to avoid runaway fan-out and cost. The default has been 3 levels since v2.1.219; `1` turns nesting off.
  - The main thread (or the orchestrator) is level 0 and fan-out workers are level 1.
  - Level 2 is kept only so that a worker can run a forked skill (e.g. `verify` → `verifier`, which has no `Agent` tool).
  - By policy (`docs/FANOUT.md` §6), fan-out workers never spawn agents themselves: worker agent files leave `Agent` out of `tools:`, or list it in `disallowedTools`.
- **Do not set `CLAUDE_CODE_DISABLE_NONESSENTIAL_TRAFFIC`.** It turns off Remote Control and auto-updates.
- Optional privacy settings. Set each one individually if you want it:
  - `"DISABLE_TELEMETRY": "1"`
  - `"DISABLE_ERROR_REPORTING": "1"`
  - `"CLAUDE_CODE_DISABLE_FEEDBACK_SURVEY": "1"`

### `enableAllProjectMcpServers: false`
A repo's `.mcp.json` can ship malicious MCP servers, so each one must be approved individually.

### `cleanupPeriodDays: 365`
Keeps local session transcripts for a year. They feed `/retro`, `/why` and the improvement loop. `0` fails validation. Transcripts are still only on this machine, so the hooks copy summaries into `$HARNESS_DATA`, which is backed up.

### `autoMemoryEnabled: true`
Turns on auto memory (`~/.claude/projects/<project>/memory/MEMORY.md`). Review it now and then, since memory files can be poisoned by injected content.

### `effortLevel: "high"`
Accepts `low`, `medium`, `high` or `xhigh` (not `max`). Note that `/effort` now saves a per-model value under `modelSettings`, which may override this.

`model` is left unset on purpose. On a Max plan the default is Opus 5.5. Don't switch models mid-session, because it throws away the prompt cache.

### `autoCompactWindow: 250000`
Auto-compaction triggers at 250K tokens instead of near the model's full window. Opus/Sonnet 5.5 have 1M-token windows by default, so without this key compaction happens around ~967K, long after quality and cost have degraded. 250K matches the working budget (you compact or hand off at 200–250K).
- **Env alternative:** `CLAUDE_CODE_AUTO_COMPACT_WINDOW` (integer, 100000–1000000).
- **Lower the trigger further:** `CLAUDE_AUTOCOMPACT_PCT_OVERRIDE` (1–100) compacts at that percentage of the window.
- **`/autocompact`** inside Claude Code shows or changes this interactively.
- **`idleCompaction`** (default `true`): a conversation over 200K that sits idle ~54 min gets compacted in the background, so a stale long session is cheap to resume. Set `"idleCompaction": false` if you always hand off instead.
- **Prefer handoff + `/clear`.** The harness hooks make compaction safe anyway: `PreCompact` writes `log/handoffs/auto_<ts>.md` (git state, PROGRESS tail, recent decisions; it never blocks, because blocking auto-compaction can fail the request), `PostCompact` appends the compact summary to it, and `SessionStart` (matcher `compact|clear`) re-injects HANDOFF.md, PROGRESS "Next" and the rules-file paths. `global/CLAUDE.md` carries a `# Compact instructions` section, and the `compact-prep` skill writes a precise `/compact <instructions>` string.

### `statusLine`
`scripts/statusline.py` prints one line: model, context tokens and % of the working budget (⚠ at 160K, ⛔ at 200K), 5-hour and 7-day usage with time to reset, prompt cache warm/cold, session cost. Example: `Opus 5.5 │ ctx 172k 69%⚠ │ 5h 41% ↻2h13m │ 7d 78% ↻3d11h │ cache warm 4m │ $3.12`.
- **Path:** `__HOME__/code/claude-harness/...` assumes the repo lives at `~/code/claude-harness` (where `mac/bootstrap.sh` puts it). Plugins can't set `statusLine`, so this key points at the repo directly. Change the path if your clone lives elsewhere. Because the merge keeps existing values, an existing `statusLine` of yours wins; remove it first if you want this one.
- **`refreshInterval: 30`** (seconds, minimum 1) keeps the reset countdowns current while the session is idle. Claude Code also re-runs it on events, when a rate-limit window resets and when a warm cache expires.
- **Why it writes a file:** no hook input carries rate limits or context size, so the script persists `${HARNESS_STATE:-~/.claude/harness-state.json}` (atomic tmp+rename) and `hooks/usage_guard.py` (UserPromptSubmit) reads it to tell Claude when to wrap up: a heads-up once at 160K, "finish the step, `/handoff`, then `/clear`" at 200K, and "use cheaper models, no fan-out" when 5h or 7d reaches 90%. State older than 10 minutes or from another session is ignored for context; usage is account-wide, so any fresh session's numbers count.
- **Rate-limit fields** only exist for Pro/Max subscribers and appear after the first API response; each window may be absent. The line simply omits what's missing.
- **Tuning (env):** `HARNESS_CTX_BUDGET` (default 250000, set in `env` above), `HARNESS_CTX_WARN` (160000), `HARNESS_CTX_STOP` (200000), `HARNESS_STATE`, `HARNESS_USAGE_GUARD=0` (turn the guard off), `NO_COLOR`.
- **`/usage`** (and `/cost`) inside Claude Code show the same limits on demand.

### Phone alerts for usage (ntfy)
There is **no GitHub-side or claude.ai-side usage alert** you can subscribe to, so the status line pushes to your phone itself:
- Set `"HARNESS_NTFY_TOPIC": "<30+ random chars>"` in `env` and subscribe to that topic in the ntfy app. Optional `HARNESS_NTFY_SERVER` (default `https://ntfy.sh`).
- It pushes when the 7-day window crosses **75%** and **90%**, and when the 5-hour window crosses **90%**, at most once per threshold per window (recorded in the state file under `ntfy_sent`). Sending happens in a detached child with a 2 s timeout, so the status line never stalls.
- Anyone who knows the topic can read it, and messages contain only percentages and reset times.

### `autoContinueAtUsageLimit` (not set)
When a usage limit is hit mid-task, this setting lets Claude Code resume automatically once the window resets. It's left **off** on purpose: a long autonomous run that silently restarts after a reset can burn the next window too. Turn it on (`"autoContinueAtUsageLimit": true`) for unattended overnight jobs whose plan you trust (**verify** the key in the settings reference before relying on it).

### `hooks.Notification`
Shows a macOS notification when Claude needs you.
- **Phone push:** inside Claude Code, open `/config` and turn on "Push when actions required" and/or "Push when Claude decides".
- **Alternative:** a hook that posts to `ntfy.sh/<long-random-topic>`. Anyone who knows the topic can read it, so use 30+ random characters and never put secrets in the message.
- The harness's own logging hooks live in the plugin's `hooks/hooks.json`, not here.

## Limits (read this)

- **Read/Edit deny rules don't stop Bash.**
  - `Read(**/.env)` blocks the Read tool, but `cat .env`, `python -c open('.env')` or `cp .env /tmp` through Bash still work unless the sandbox blocks them.
  - The `Bash(cat …)` denies are a speed bump, not a wall.
  - **The real defense** is the sandbox (with `allowUnsandboxedCommands: false`) plus not keeping secrets in files at all. Use `op run` or `op read` at runtime.
- **Bash pattern rules are fragile.** They are easy to get around with flags in a different order, variables, `xargs` or scripts. They catch accidents, not attackers.
- **Hooks are guardrails, not a security boundary.** A `PreToolUse` hook can add checks, such as scanning commands for secret paths, but it is code that can have bugs.
- **Precedence:** managed > CLI flags > local > project > user. A project's `.claude/settings.json` can add rules but cannot remove your user-level deny rules, because deny rules are combined across all scopes.
