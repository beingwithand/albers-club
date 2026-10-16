# Official setup facts: Remote Control, computer use, permissions, sandbox, scheduling (fetched 2026-10-16)

Sources: code.claude.com/docs/en/{remote-control, mobile, desktop, computer-use, chrome, permission-modes, permissions, sandboxing, devcontainer, settings-reference, model-config, memory, scheduled-tasks, desktop-scheduled-tasks, routines, channels}, plus support.claude.com article 13947068 (Dispatch).
Run `claude --version` first: several of these features need v2.1.283 or later.

## Remote Control (phone drives the Mac)
**Starting it**
- Server mode, one process for many sessions: `claude remote-control`. Flags:
  - `--name`
  - `--capacity` (default 32)
  - `--permission-mode`
  - `-c` / `--continue`
  - `--session-id`
- Inside a session: `/remote-control` (or `/rc`).
- The first run asks interactively to enable Remote Control and to trust the folder, so run it by hand once.

**Keeping it on**
- To turn it on for every session, open `/config` and choose "Enable Remote Control for all sessions". The settings key is `remoteControlAtStartup` (verify).
- In the Desktop app: Settings > Claude Code > "Connect new sessions to Remote Control".
- The `claude` process has to keep running, for example inside tmux.
- If the Mac sleeps, the session reconnects when it wakes, but the phone can't drive it while it's asleep.
- After stopping it, `--continue` or `--session-id` can restore the session for about 4 hours.
- There is no official launchd or auto-start recipe.

**Requirements and limits**
- You must sign in with a claude.ai account (Pro, Max, Team or Enterprise). API keys don't work.
- It doesn't work with Bedrock, Vertex, Foundry or a custom `ANTHROPIC_BASE_URL`.
- `CLAUDE_CODE_DISABLE_NONESSENTIAL_TRAFFIC` turns it off.
- Bypass permissions can't be selected from the phone app.

**Security**
- Outbound HTTPS only: no ports are opened on your Mac.
- Commands and files stay on the Mac, but the transcript is stored on Anthropic's servers while connected.
- Optional "Require trusted devices" setting: an enrolled device plus a biometric sign-in within the last 18 hours.

**Phone notifications**
- In `/config`: "Push when actions required" and "Push when Claude decides".
- `/mobile` shows a QR code for pairing the phone app.

## Computer use
**Desktop app** (Pro/Max, research preview)
- Turn it on in Settings > This computer > System > Computer use.
- Grant macOS Accessibility and Screen Recording permissions.
- You can keep a list of apps it's never allowed to touch. Approvals for individual apps last only for the current session.

**Command line** (macOS)
- Run `/mcp`, pick `computer-use`, and choose Enable. This sticks per project.
- Only one session can control the screen at a time.
- It needs an interactive session, not `-p`.

**What it's allowed to do depends on the app**
- Browsers and trading apps: it can look but not click.
- Terminals and IDEs: it can click, which is effectively the same as shell access.
- Everything else: full control.

To stop it: Esc anywhere, or Ctrl+C in the terminal.

**Claude in Chrome**
- Install the Chrome extension (v1.0.36 or later).
- Use `claude --chrome` for one session, or `/chrome` > "Enabled by default" for all of them.
- Requires `/login`. A project's settings can't enable it.

## Permissions
**Modes**
- The modes are default, acceptEdits, plan, auto, dontAsk and bypassPermissions.
- Auto is the default starting mode from v2.1.283.
- The docs say bypassPermissions is only for isolated containers or VMs.
- Set `permissions.defaultMode: "auto"` in **user** settings. Project and local settings ignore auto and bypass.

**Rule syntax**
- `Bash(cmd *)`, `Read(~/.ssh/**)`, `Read(**/.env)`, `Edit(/src/**)`, `Read(//abs)`, `WebFetch(domain:x)`, `mcp__server__*`.
- Deny beats ask, which beats allow.
- Deny rules apply in every mode, including bypass.
- A Read deny also blocks Edit and Write on that path.
- Chained commands are split apart, and each part must match a rule.
- Rules that match Bash arguments are easy to get around. Restrict network access with the sandbox instead.
- There is no official recommended deny list.

## Sandbox
- Turn it on with `/sandbox`, or `"sandbox": {"enabled": true}` in settings.
- It covers Bash commands only.
- Network access goes through a proxy that checks `sandbox.network.allowedDomains`.
- Other keys:
  - `autoAllowBashIfSandboxed`: default true.
  - `allowUnsandboxedCommands`: set false to make the sandbox mandatory.
  - `excludedCommands`.
- The strongest setup on a personal Mac: auto mode, sandbox on with unsandboxed commands turned off, plus deny rules.
- Devcontainer: use the feature `ghcr.io/anthropics/devcontainer-features/claude-code:1.0`. Don't mount `~/.ssh`.

## Settings worth setting
- **`effortLevel`:** accepts low, medium, high or xhigh (not max). Opus 5.5 defaults to medium.
- **`model`:** leave it unset. Max plans default to Opus 5.5.
- **`autoMemoryEnabled`:** on by default.
- **`statusLine`:** use `/statusline <description>` to generate one.
- **`outputStyle`.**
- **`attribution.commit` and `attribution.pr`:** `includeCoAuthoredBy` is deprecated.
- **`cleanupPeriodDays`, `autoUpdatesChannel`, `env`.**
- **Notification hook:** matcher `permission_prompt` or `idle_prompt`, then run `osascript display notification`.
- **Keybindings:** `/keybindings` creates `~/.claude/keybindings.json`, which reloads live.

## Scheduling and phone access
- **`/loop`:** tied to the session. Expires after 7 days, at most 50 per session.
- **Desktop scheduled tasks:**
  - Run only while the Desktop app is open and the Mac is awake. The "Keep computer awake" setting helps.
  - Minimum interval of 1 minute.
  - A missed run gets one catch-up, within 7 days.
- **Cloud Routines:**
  - Run with the Mac off.
  - Start on a schedule (minimum 1 hour), from the API `/fire` endpoint, or from GitHub events.
  - Set up with `/schedule` or at claude.ai/code/routines.
  - Up to 100 runs per hour.
- **Channels:** Telegram, Discord or iMessage messages into a running session (`claude --channels plugin:telegram@claude-plugins-official`).
  - Requires Bun.
  - iMessage also needs Full Disk Access.
- **Dispatch (Desktop):** send tasks from your phone.

## Couldn't confirm
- A launchd or auto-start recipe, and an official way to keep the Mac awake for Remote Control.
- Whether the auto-mode switch lives at `permissions.disableAutoMode` or a top-level `disableAutoMode`.
- Which settings keys map to the push-notification toggles.
- Cloud sessions linked to the computer (the `remote-devices` tools).
