# Community "best setup" for Claude Code (as of 2026-10-16)

Research date: 2026-10-16. Method: WebSearch snippets, WebFetch of GitHub READMEs and official docs (code.claude.com), and GitHub repo search.

**Source access notes**
- Reddit (reddit.com) **blocks fetching**: WebFetch returns "unable to fetch from www.reddit.com". `site:reddit.com` searches also returned zero Reddit threads. Reddit mirror snapshots (reddit.sentinel-team.org) came up in results, but their hosts didn't resolve. **No Reddit thread content was verified directly.** Any "Reddit says" claim below is secondhand, via blogs that cite Reddit.
- Hacker News: `site:news.ycombinator.com` returned no HN pages, and hn.algolia.com didn't resolve (DNS). **No HN thread content was verified.**
- YouTube: searches returned no video descriptions. The only video material is a few dated videos listed in the shanraisshan repo (Dex 2026-03-24, Matt Pocock 2026-04-24).
- So most "community" signal here comes from GitHub config repos, practitioner blogs and newsletters, and secondhand summaries of Boris Cherny (creator of Claude Code) threads. Official docs were used to check that key names are real.

Legend: **[CONSENSUS]** = 3+ independent sources agree. **[COMMON]** = 2 sources. **[SINGLE]** = one source. **[OFFICIAL]** = confirmed in code.claude.com docs. **[RISK]** / **[OUTDATED]** = flags.

---

## 1. Most-starred / most-forked config repos (stars likely inflated; many 2026 repos show star counts that look botted)

| Repo | Stars / forks | Last push | What it is | Signal quality |
|---|---|---|---|---|
| affaan-m/ECC ("everything-claude-code") | 281k / 41.8k | 2026-10-16 (release 2.2.3, 2026-10-01) | Big harness: skills, "instincts", memory, hooks, security | Star count is implausible, so treat it as inflated. It's a full framework, not a dotfile. |
| shanraisshan/claude-code-best-practice | 67.6k / 6.7k | 2026-10-16 | Curated tips, including dated Boris Cherny / Thariq tip collections, plus a settings report | Useful as an index of Boris/Anthropic-staff tips |
| trailofbits/claude-code-config | 2.1k / 162 | 2026-10-15 | Opinionated security-firm defaults | **Highest-credibility community config.** Realistic star count, security-focused. |
| feiskyer/claude-code-settings | 1.7k / 242 | 2026-10-15 | Skills, sub-agents, config templates | medium |
| fcakyon/claude-codex-settings | 1.2k / 111 | 2026-10-16 | Claude Code, Codex, and Cursor configs, hooks, plugins | medium |
| jarrodwatts/claude-code-config | 1.1k / 122 | 2026-10-16 | Personal rules, hooks, agents, skills. Same author as the claude-hud statusline. | medium |
| rohitg00/awesome-claude-code-toolkit | 2.7k / 1.0k | 2026-10-16 | Catalog | Catalog, not a config |
| UfoMiao/zcf | 6.1k / 425 | 2026-10-16 | "Zero-config" installer (Chinese community) | medium |
| 0xquinto/bcherny-claude | n/a | n/a | Template based on Boris Cherny's threads (Jan 2026, May 2026) | secondhand |
| Token-savers: rtk-ai/rtk (83.6k), JuliusBrussee/caveman (113k), headroomlabs-ai/headroom (75.5k) | | 2026-10 | CLI/output compression proxies | Viral and inflated. Install with caution (see Risk). |
| Memory: thedotmack/claude-mem (101k) | | 2026-10-16 | Cross-session memory plugin | Overlaps with built-in auto memory |
| Skills: addyosmani/agent-skills (107k), ComposioHQ/awesome-claude-skills (77k), obra/superpowers | | 2026-10 | Skill packs | superpowers is the most-cited skill pack in blog setups |

Takeaway: if you copy one community config, **trailofbits/claude-code-config** is the one most aligned with "full autonomy + hardening".

---

## 2. settings.json: concrete, copyable recommendations

### 2a. Composite `~/.claude/settings.json` (assembled from the sources below; check each key against your version)

```jsonc
{
  "cleanupPeriodDays": 365,                 // ToB: a year of history for /insights. Default 30, min 1; 0 fails validation [OFFICIAL]
  "autoMemoryEnabled": true,                // default true [OFFICIAL]; set false in CI or if you want only versioned memory
  "enableAllProjectMcpServers": false,      // ToB: a repo's .mcp.json could ship malicious servers
  "preferredNotifChannel": "auto",          // "auto" | "terminal_bell" | "iterm2" | "iterm2_with_bell" | "kitty" | "ghostty" | "notifications_disabled" [OFFICIAL]
  "statusLine": { "type": "command", "command": "~/.claude/statusline.sh" },   // ToB (needs jq); or `npx ccstatusline@latest` / claude-hud
  "attribution": { "commit": "", "pr": "" }, // shanraisshan: hide attribution deterministically. includeCoAuthoredBy is DEPRECATED [OFFICIAL]
  "effortLevel": "high",                    // ToB: high default; /effort xhigh for hard work, low/medium for routine
  "permissions": {
    "defaultMode": "auto",                  // see 2b; "acceptEdits" is the conservative choice
    "deny": [
      "Read(./.env*)", "Read(./secrets/**)",
      "Read(~/.ssh/**)", "Edit(~/.ssh/**)",
      "Read(~/.aws/**)", "Read(~/.config/gh/**)", "Read(~/.npmrc)", "Read(~/.git-credentials)",
      "Edit(~/.zshrc)", "Edit(~/.bashrc)",
      "Bash(sudo *)", "Bash(rm -rf *)"
    ],
    "ask": ["Bash(git push *)", "Bash(npm publish *)"]
  },
  "env": {
    "DISABLE_TELEMETRY": "1",
    "DISABLE_ERROR_REPORTING": "1",
    "CLAUDE_CODE_DISABLE_FEEDBACK_SURVEY": "1",
    "CLAUDE_CODE_MAX_SUBAGENT_SPAWN_DEPTH": "3"
  },
  "hooks": { /* see 2d */ }
}
```

### 2b. defaultMode / permission mode
- **auto mode** is now the **default for Pro, Max, and Team since Aug 14, 2026** (The Register). It's still opt-in on Enterprise and the API. A Sonnet 4.6 classifier gates each tool call. After 3 consecutive blocks, or 20 blocks in a session, it falls back to manual approvals. Anthropic still recommends isolated environments. **[OFFICIAL + press, 2026-03 launch]**
- Boris Cherny: avoids `--dangerously-skip-permissions`, pre-approves safe commands via `/permissions`, and commits them to `.claude/settings.json` for the team. A May 2026 post (via the 0xquinto template, **[SINGLE]**, unverified) recommends auto mode via `defaultMode`. **[COMMON]**
- Trail of Bits: `alias claude-yolo="claude --dangerously-skip-permissions"`, **but only paired with `/sandbox`** (Seatbelt/bubblewrap) or a devcontainer. **[SINGLE, high credibility]**
- `acceptEdits` is described as the "practical middle ground" (file edits auto, Bash checked against the lists). **[COMMON, blogs]**
- Lock-down keys: `disableBypassPermissionsMode`, `disableAutoMode`, `skipDangerousModePermissionPrompt` (user/local/managed only). **[OFFICIAL]**

### 2c. Deny lists **[CONSENSUS]**
- Deny `.env*`, `secrets/**`, SSH/GPG keys, cloud and registry tokens, git credentials, shell rc files, keychains, and wallets (ToB, petefreitag, fast.io, rajiv.com 2026-03-31).
- Deny beats ask beats allow, at every scope. **[OFFICIAL]**
- **[RISK] Deny rules on Read/Edit don't cover Bash** (`cat .env` still works) unless `/sandbox` is on or a PreToolUse hook also blocks it. ToB: "use both". **[CONSENSUS]**
- **[RISK, patched]** Adversa found deny rules could be bypassed by padding a command with 50 no-op subcommands. Fixed in v2.1.90. eesel.ai reports "Reddit and Stack Overflow" complaints that deny rules get ignored (secondhand).
- A Bash prefix blocklist (`Bash(curl *)`) is easy to evade (`/usr/bin/curl`, `python -c`). Treat it as friction, not a boundary.

### 2d. Hooks people actually run
| Hook | Purpose | Sources |
|---|---|---|
| `PostToolUse` matcher `Write\|Edit` → formatter, with `\|\| true` | Auto-format so CI doesn't fail on style | Boris Cherny (via paddo.dev, skillsmp), shanraisshan **[CONSENSUS]** |
| `PreToolUse` on Bash: block `rm -rf` (suggest `trash`) and direct push to main/master | Safety | ToB; morphllm; kjetilfuras **[CONSENSUS]** |
| `Stop` hook: verify the work / "keep going" / anti-rationalization prompt hook | Long autonomous runs | Boris, ToB, shanraisshan **[CONSENSUS]**. ToB gotcha: the prompt must demand raw JSON only, or the hook silently breaks. Prompt hooks time out after 30s. |
| `PostToolUse` Bash logger: `jq -r '"[" + (now\|todate) + "] " + .tool_input.command' >> ~/.claude/bash-commands.log` | Audit trail | ToB **[SINGLE]** |
| `Notification` hook → ntfy / osascript / OSC 9 | Phone or desktop alerts | many (see §5) |
| `PermissionRequest` routed to Opus to auto-approve safe commands | "Do not babysit" | shanraisshan (Boris) **[SINGLE]**. Mostly superseded by auto mode. |
| Enforce the package manager (pnpm over npm) | | ToB **[SINGLE]** |
- Hooks are snapshotted at session start, so changes need a review in `/hooks`. **[COMMON]**
- ToB: "hooks are guardrails, not a security boundary". Prompt injection can route around them.

### 2e. Model, effort, thinking
- ToB: **don't** set `alwaysThinkingEnabled`. Use `/effort` instead: `high` by default, `xhigh` for the hardest work. Since v2.1.251, `/effort` saves the level under `modelSettings` per model rather than writing `effortLevel`. **[OFFICIAL]**
- Pin with `CLAUDE_CODE_EFFORT_LEVEL` if you want remote devices unable to change it. **[OFFICIAL]**
- Routing pattern: an Opus main session, Sonnet or Haiku subagents (`CLAUDE_CODE_SUBAGENT_MODEL`), Opus for plan mode and Sonnet for implementation (shanraisshan, morphllm, analyticsvidhya). **[CONSENSUS]**
- `/fast` / `"fastMode": true`: ToB says turn it **off for autonomous runs**, and toggle it at session start, not mid-session (a cache reason). **[SINGLE]**

### 2f. env vars that recur
- `DISABLE_TELEMETRY`, `DISABLE_ERROR_REPORTING`, `CLAUDE_CODE_DISABLE_FEEDBACK_SURVEY` (ToB, getvoibe). **[COMMON]**
- **[RISK] Avoid `CLAUDE_CODE_DISABLE_NONESSENTIAL_TRAFFIC`**: it also disables auto-updates (ToB) and feature-flag fetches, which can break Remote Control ("Remote Control isn't enabled" error, official docs).
- **[OUTDATED bug]** A Threads post says `DISABLE_TELEMETRY=1` once dropped the prompt-cache TTL to 5 minutes. It's said to be patched now; just stay updated. **[SINGLE]**
- `CLAUDE_AUTOCOMPACT_PCT_OVERRIDE` = 70 for normal work, 50 for noisy workflows (one guide). **[SINGLE]**
- `CLAUDE_CODE_MAX_SUBAGENT_SPAWN_DEPTH=3` (or `1` to stop subagents spawning their own). Leave `CLAUDE_CODE_MAX_CONCURRENT_SUBAGENTS` (default 20) unset (ToB). **[SINGLE]**
- `CLAUDE_CODE_NO_FLICKER=1` or `/tui fullscreen` (shanraisshan, beta). **[SINGLE]**
- `CLAUDE_CODE_DISABLE_AUTO_MEMORY=1` for CI. It outranks the setting. **[OFFICIAL]**
- `ENABLE_PROMPT_CACHING_1H=1` for API-key users (see §8).
- `CLAUDE_CLIENT_PRESENCE_FILE`: suppresses phone pushes while a marker file exists. Wire it to screen lock/unlock. **[OFFICIAL]**

### 2g. outputStyle / CLAUDE.md / rules
- Keep CLAUDE.md under about 200 lines (one author: about 60 works). Another guide caps memory at about 100 lines. **[CONSENSUS on "short"]**
- Move long procedures into skills and path-scoped `.claude/rules/*.md` (`paths:` frontmatter). **[CONSENSUS]**
- **Gotcha (ToB):** path-scoped rules are **not re-injected after auto-compaction**. Put must-hold rules in CLAUDE.md and enforce them with hooks.
- Put the build/test/run commands in CLAUDE.md. Wrap domain rules in `<important if="...">` (shanraisshan). **[SINGLE]**
- Use `settings.json`, not CLAUDE.md, for anything that must be deterministic (attribution, permissions, model). **[COMMON]**
- ToB: set `outputStyle` in the **user** file. `/config` writes to project `.claude/settings.local.json`.
- Run `/insights` weekly and turn its findings into rules, hooks, or skills (ToB).

---

## 3. MCP servers people treat as essential
| Server | Consensus | Notes |
|---|---|---|
| **Context7** (upstash) | **[CONSENSUS]**, the #1 pick everywhere | Current library docs. Also ships as a plugin: `/plugin marketplace add upstash/context7`, then `/plugin install context7-plugin@context7-marketplace` |
| **Playwright** (or agent-browser / chrome-devtools) | **[CONSENSUS]** | Lets Claude verify UI fixes itself. ToB prefers vercel-labs **agent-browser** (context-efficient snapshots). ECC ships chrome-devtools. |
| **GitHub MCP** | **[COMMON]** (Techsy, July 2026 starter trio: GitHub + Context7 + Playwright) | Many people use the `gh` CLI instead to save context |
| **Exa** (web search) | **[COMMON]** (ToB, ranked lists) | Needs `EXA_API_KEY` |
| Claude in Chrome | **[SINGLE]** ToB | For authenticated pages |
| Serena (symbol-level editing) | [SINGLE] ToB, optional | |
| Sequential Thinking, Filesystem | lists only | **[OUTDATED]** Anthropic archived 13 of its 20 original reference servers in 2025. Built-in thinking and file tools make these redundant. |
| Supabase, Sentry | domain-specific | |

**Context cost [CONSENSUS]:** tool schemas load on every turn, so keep fewer than about 10 enabled per project and avoid overlap (CodeConductor, analyticsvidhya, okhlopkov). ToB: Context7 + Exa globally (in `~/.mcp.json`), everything else per project.

---

## 4. Plugins / skills worth installing
- **obra/superpowers** (`/superpowers:brainstorm`, `write-plan`, `execute-plan`, `systematic-debugging`, TDD). **[CONSENSUS]**, the most-cited skill pack.
- **trailofbits/skills** marketplace (`claude plugin marketplace add trailofbits/skills`): `ask-questions-if-underspecified`, `differential-review`. **[SINGLE]**
- Official marketplace: `feature-dev`, `commit-commands`, `frontend-design`, `typescript-lsp` (medium.com 2026 list, dev.to). **[COMMON]**
- Statusline plugins: **claude-hud** (jarrodwatts), **ccstatusline** (`npx ccstatusline@latest`, about 3.1k stars, 5-hour block timer), **ccstatus** (Rust, 5-hour and 7-day bars). Claude Code now passes `rate_limits.five_hour` / `seven_day` (`used_percentage`, `resets_at`) on stdin for Pro/Max, after the first response. **[CONSENSUS on wanting a usage-aware statusline]**
- Skill-authoring tips (Thariq, 2026-03-17, via shanraisshan): write the description as a trigger, add a Gotchas section, use `context: fork` for isolation, and use `!command` for live shell output.
- **[RISK]** ECC warns that third-party re-uploads of popular skill packs "may contain malware", and that stacking install methods duplicates hooks and skills. Don't copy plugin `hooks.json` into settings.json too (it runs twice).

---

## 5. Terminal setup and notifications
- **Ghostty** is the community-default terminal on Mac (ToB: `brew install --cask ghostty`; kjetilfuras: GPU/Metal). WezTerm on Windows. **[COMMON]**
- Native desktop notifications work out of the box only in **Ghostty, Kitty, and iTerm2**. Elsewhere, use `"preferredNotifChannel": "terminal_bell"` or a Notification hook. **[OFFICIAL]**
- **tmux:** enable passthrough (`set -g allow-passthrough on`) so OSC 9 notifications reach the outer terminal. Newer hooks can return a `terminalSequence` field to emit escapes that work inside tmux. **[COMMON]** Gap: there's no dedicated event for "waiting on approval" (GH issue #36850).
- Boris Cherny runs several terminal sessions plus many web sessions in parallel and relies on notifications to see which ones need input. **[COMMON, secondhand]**

### Notification to phone
1. **Built-in (preferred, [OFFICIAL]):** with Remote Control active, open `/config` and enable **"Push when Claude decides"** and/or **"Push when actions required"**. Pushes go to the Claude iOS/Android app. If it shows "No mobile registered", open the app once. iOS Focus modes can suppress pushes. Use `CLAUDE_CLIENT_PRESENCE_FILE` to mute pushes while you're at the desk.
2. **ntfy.sh via Notification/Stop hook** (CodePing plugin "killernay-codeping", one topic per machine; `claude-notify` npm). Use a long random topic name, because public ntfy topics are guessable. **[COMMON]**
3. Third-party apps: Tactic Remote (tmux + iPhone, macOS 14+), Caffeinate AI (iCloud), Claude Code Notifier (menu bar). **[SINGLE each]** Mostly superseded by built-in Remote Control and push.

---

## 6. Always-on Mac: remote control, computer use, staying awake
**Official facts (code.claude.com/docs/en/remote-control):**
- `claude remote-control` (server mode; `--spawn worktree` gives each session its own worktree, `--capacity` defaults to 32, press spacebar for a QR code), `claude --rc` (an interactive session that's also remote), or `/remote-control` / `/rc` mid-session. Turn it on for every session in `/config` → "Enable Remote Control for all sessions".
- Requires a claude.ai login (Pro/Max/Team/Enterprise). API keys aren't supported. Team/Enterprise need an Owner toggle.
- **Outbound HTTPS only, no inbound ports**, so you don't need Tailscale or port forwarding for Remote Control.
- If the laptop sleeps, it **reconnects automatically on wake**, but nothing runs while it's asleep. Server mode exits after about 10 minutes of network outage. An interactive session drops after about 30 minutes of failed heartbeats. Forwarded non-permission dialogs expire after 5 minutes (`dialogExpiry`).
- Crashed server-mode sessions get revived when you message them from a device (v2.1.238+). `claude remote-control -c` resumes (v2.1.200+).
- `--chrome` passes Chrome integration through to remote sessions (v2.1.273+).

**Keeping the Mac awake [CONSENSUS on the need, mixed on the method]:**
- `caffeinate -dims claude ...` wraps the process so the assertion ends with the session. Or run `caffeinate -dims` in a separate tab (andrewbaker.ninja, 2026-04-11; page wouldn't fetch, so this is from the search snippet). **[COMMON]** On a laptop, `-s` only holds on AC power. Closing the lid still sleeps the Mac unless an external display is attached (clamshell mode) or you use a tool like Amphetamine.
- Dedicated Mac mini: `sudo pmset -a sleep 0 displaysleep 0 disksleep 0`, plus auto-login/screen-lock changes, plus `pmset autorestart 1` after a power cut (dev.to, martech.zone). **[COMMON]**
- **[RISK/UNVERIFIED]** `pmset disablesleep 1` is undocumented (Cloudzy). It works for lid-closed setups on some macOS versions, but verify it on yours.
- Dispatch / Cowork computer use (launched 2026-03-17 / 2026-03-23, Pro/Max, macOS): the Mac **must stay awake with the Claude desktop app running**. Turn on the app's keep-awake option. Computer use is under Settings → General → Computer Use. Claude asks per app, and sensitive apps are blocked by default. Reviews are mixed (about 50% success rate in early tests; a May 2026 review called it "clunky… still brilliant"). **[COMMON]**
- Use a **dedicated low-privilege macOS user** for unattended automation (dev.to). **[SINGLE]** Tailscale + key-only SSH is the fallback remote shell (mager.co). **[COMMON]**

---

## 7. Security hardening paired with full autonomy
1. **OS sandbox first** (`/sandbox`: Seatbelt on macOS, bubblewrap on Linux). Writes are limited to the CWD by default. Reads stay open unless you add deny rules. **[CONSENSUS]** ToB pairs bypass mode with the sandbox only.
2. **Permission rules are a gate, not a sandbox** (official secure-deployment docs). Read/Edit denies don't cover Bash.
3. **Devcontainer or disposable VM** for real YOLO (trailofbits/claude-code-devcontainer, trailofbits/dropkit). **[COMMON]**
4. `enableAllProjectMcpServers: false`. Review a repo's `.mcp.json` and hooks before trusting the workspace. **[SINGLE, high credibility]**
5. Deny credential paths (see §2c). Keep secrets out of the repo tree.
6. **Network exfiltration:** the "Claudy Day" research by Oasis Security (2026-03) exfiltrated data through the Anthropic Files API, which was on the sandbox's default allowlist. It's patched now, but the lesson is that allowlisted domains are exfil channels. **[SINGLE, patched]**
7. Pin `CLAUDE_CODE_MAX_SUBAGENT_SPAWN_DEPTH`. Watch out for `CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS`, which can form teams you didn't ask for (ToB).
8. Remote Control: for orgs, Trusted Devices (passkey/biometric step-up). Personally, `disableRemoteControl` if you don't use it. **[OFFICIAL]**
9. Treat auto-memory and memory plugins as "unreviewed context, not executable policy" (ECC). Prompt injection can persist through memory.
10. **[RISK]** Viral token-compression proxies (rtk, headroom, OmniRoute gateways) sit in the request path. Third-party gateways via `ANTHROPIC_BASE_URL` see all your code and tokens.

---

## 8. Cost and usage-limit tips
- **Prefer `/clear` (plus a written handoff brief) over `/compact`** when switching tasks. Use `/compact <focus instructions>` mid-task rather than waiting for auto-compact (ToB, shanraisshan/Thariq 2026-04-16, analyticsvidhya). **[CONSENSUS]**
- **`/rewind` (Esc Esc) instead of stacking corrections**. After 2 failed corrections, rewind and re-prompt (ToB, shanraisshan). **[CONSENSUS]**
- Context thresholds are heuristics and they disagree: a "dumb zone" from about 40%, wrap up near 60% (shanraisshan). Stay under 30% for complex work. Degradation from about 147K tokens on 200K windows. Context rot from 300-400K on 1M windows. **[SINGLE each, no consensus number]**
- Push exploration into **subagents** so only conclusions come back. Use cheaper subagent models. **[CONSENSUS]**
- **Prompt caching:** subscription sessions request a 1-hour TTL, which can drop to 5 minutes once you're on extra-usage credits. API keys default to 5 minutes (`ENABLE_PROMPT_CACHING_1H=1` opts into 1 hour; `FORCE_PROMPT_CACHING_5M=1` is for debugging). After a long idle gap, the next turn pays for a full re-write, so for big stale sessions `/clear` plus a handoff is cheaper. Toggling `/fast` or changing the model mid-session also busts the cache. **[COMMON]** **[DISPUTED]**: whether editing CLAUDE.md mid-session invalidates the cache. A later source says the change only applies after /clear, /compact, or a restart.
- Keep few MCP servers (schemas are paid on every turn). Keep CLAUDE.md short. Rules load on every turn. **[CONSENSUS]**
- Monitor: `/context`, `/usage`, `/cost`, a usage-aware statusline, and `ccusage` (mentioned in prior community lore; not surfaced in 2026 results). `/extra-usage` sets up overflow billing.
- Token-compression skills/proxies (caveman "talk like a caveman" ‑65%, rtk 60-90% on CLI output) are hugely starred but **[SINGLE-source claims, unverified]**. Caveman-style output can hurt quality.

---

## 9. Outdated / risky items to flag
- **[OUTDATED]** npm install (`npm i -g @anthropic-ai/claude-code`). The native installer is now the recommended method (April 2026 guide).
- **[OUTDATED]** `includeCoAuthoredBy`. Use `attribution`.
- **[OUTDATED]** `/effort` writing `effortLevel`. Since v2.1.251 it writes `modelSettings`.
- **[OUTDATED]** guides saying Remote Control isn't available on Team/Enterprise. It is, behind an Owner toggle.
- **[OUTDATED]** archived reference MCP servers (filesystem, sequential-thinking, etc.).
- **[OUTDATED]** "PermissionRequest hook → Opus auto-approve" hacks. Auto mode does this natively.
- **[RISK]** `--dangerously-skip-permissions` / bypassPermissions on the host without a sandbox.
- **[RISK]** `CLAUDE_CODE_DISABLE_NONESSENTIAL_TRAFFIC` silently kills auto-updates and feature flags (including Remote Control).
- **[RISK]** Public ntfy topics with guessable names leak session info.
- **[RISK]** `pmset disablesleep` is undocumented. Laptops with the lid closed in a bag can overheat.
- **[RISK]** Mega-frameworks (ECC 281k stars, etc.) inject large SessionStart context and many hooks. That costs tokens, gives you overlapping memory systems, and adds supply-chain surface.

---

## Sources (accessed 2026-10-16)
- Official: https://code.claude.com/docs/en/remote-control ; https://code.claude.com/docs/en/settings ; https://code.claude.com/docs/en/settings-reference.md ; https://code.claude.com/docs/en/terminal-config ; https://code.claude.com/docs/en/agent-sdk/secure-deployment ; https://support.claude.com/en/articles/14554000-claude-code-power-user-tips
- https://github.com/trailofbits/claude-code-config (pushed 2026-10-15)
- https://github.com/shanraisshan/claude-code-best-practice (pushed 2026-10-16; Boris tip collections dated 2026-01-03 through 2026-04-16)
- https://github.com/affaan-m/ECC (release 2.2.3, 2026-10-01)
- https://github.com/0xquinto/bcherny-claude ; https://paddo.dev/blog/how-boris-uses-claude-code ; https://getpushtoprod.substack.com/p/how-the-creator-of-claude-code-actually
- https://rajiv.com/blog/2026/03/31/stop-asking-me-configuring-claude-code-permissions-for-uninterrupted-flow ; https://www.petefreitag.com/blog/claude-code-permissions/ ; https://www.eesel.ai/blog/settings-json-claude-code ; https://www.morphllm.com/claude-code-hooks
- https://www.theregister.com/a/5285326 (auto mode default Aug 14) ; https://9to5mac.com/2026/03/24/claude-code-gives-developers-auto-mode-a-safer-alternative-to-skipping-permissions/ ; https://simonwillison.net/b/9394
- https://andrewbaker.ninja/2026/04/11/keep-your-mac-awake-while-claude-code-works/ (snippet only) ; https://dev.to/paradane/claude-code-mac-setup-tutorial-spare-mac-automation-server-2cij ; https://cloudzy.com/de/blog/move-ai-agents-from-mac-to-vps/ ; https://mager.co/blog/2026-02-22-openclaw-mac-mini-tailscale/
- https://claudepluginhub.com/plugins/killernay-codeping ; https://tacticremote.com/blog/2026-02-28-how-to-run-claude-code-from-iphone ; https://agentpatterns.ai/tool-engineering/terminal-sequence-hook-notifications/ ; https://github.com/anthropics/claude-code/issues/36850
- https://www.techloy.com/anthropic-just-let-claude-control-your-mac-heres-how-to-set-it-up/ ; https://pub.towardsai.net/claude-can-now-control-your-computer-how-dispatch-works-what-it-can-do-and-its-honest-f405a07829c1 ; https://app.therundown.ai/guides/let-claude-use-your-computer-remotely-with-dispatch
- https://www.heyuan110.com/posts/ai/2026-03-05-best-mcp-servers-claude-code/ ; https://techsy.io/en/blog/best-mcp-servers-2026 (July 2026) ; https://codeconductor.ai/blog/claude-code-mcp-servers/
- https://medium.com/@hii_mohit/9-claude-code-plugins-every-developer-should-install-in-2026-9a35b8fe5a83 ; https://dev.to/chand1012/the-best-way-to-do-agentic-development-in-2026-14mn ; https://mayalekhi.substack.com/p/my-current-claude-code-setup
- https://claudelog.com/claude-code-mcps/ccstatusline ; https://wmedia.es/en/tips/claude-code-usage-limit-status-line ; https://docs.rs/crate/ccstatus/0.6.0
- https://www.analyticsvidhya.com/?p=254658 ; https://www.morphllm.com/claude-code-context-window ; https://prosperinai.substack.com/p/claude-code-prompt-caching-explained ; https://wmedia.es/es/tips/claude-code-prompt-caching-turno-lento-consumo ; https://www.threads.com/@tommy585/post/DXRjszyGMje
- https://www.truefoundry.com/es/blog/claude-code-prompt-injection (Adversa bypass, Claudy Day) ; https://www.getvoibe.com/resources/claude-code-privacy-settings/ ; https://github.com/anthropics/claude-code/issues/23544 (auto memory)
