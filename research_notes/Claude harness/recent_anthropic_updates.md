# Recent Anthropic / Claude updates for a Max-plan power user

Compiled 2026-10-16. Main window: Aug 1 to Oct 16, 2026, plus earlier 2026 items that still matter.

## How this was researched

**Primary sources read:**
- anthropic.com/news (first page only, Sep 23 to Oct 15)
- claude.com/blog (pages 1 and 2, Sep 28 to Oct 16)
- anthropic.com/engineering
- platform.claude.com/docs/en/release-notes/overview (Jun to Oct 15)
- support.claude.com release notes (Jan to Oct 7)
- The full Claude Code CHANGELOG.md from GitHub. It has no dates, so each version was dated from its npm publish time for `@anthropic-ai/claude-code`.
- code.claude.com docs pages: feature-availability, routines, channels, goal, advisor, artifacts, claude-projects, remote-control, computer-use, agent-teams, workflows, desktop-scheduled-tasks, chrome, mobile, model-config, fast-mode, auto-mode-config, legal-and-compliance, agent-sdk/overview
- Help Center articles on Fable models on your plan and on API credits for Max and Team

**Sites that failed or came back incomplete:**
- `anthropic.com/news/claude-fable-5-1` returned 404. Fable 5.1 details here come from the platform and support release notes plus secondary coverage.
- `docs.claude.com/...` returns a 301 redirect to `platform.claude.com/docs/...`.
- The news and blog index pages only show the most recent items. Older items came from the release notes.
- The changelog file is about 1 MB, so WebFetch truncates it. I downloaded it with curl and searched it locally.

**Version dating.** Claude Code version to date (npm), for reference:

| Version | Date |
|---|---|
| 2.1.221 | ~Aug 1 |
| 2.1.257 | Sep 1 |
| 2.1.280 | Sep 22 |
| 2.1.284 | Sep 28 |
| 2.1.293 | Oct 7 |
| 2.1.301 | Oct 15–16 |

---

## 1. Models and pricing (Claude 5 / 5.5 family)

All API prices are per million tokens (MTok).

| Model (API ID) | Date | API price in/out | Context | Notes |
|---|---|---|---|---|
| **Fable 5.1** (`claude-fable-5-1`) | Sep 1, 2026 | $10 / $50; cache read $0.25 | 1M | Mythos-class frontier model. Mythos 5.1 is the same model with fewer safeguards, for trusted-access programs only. Text and files carry watermarks and C2PA credentials. `tool_choice: any/tool` returns 400. Claude Code needs v2.1.257+ (Help Center says 2.1.255+). |
| **Opus 5.5** (`claude-opus-5-5`) | Sep 22, 2026 | $4 / $20; cache read $0.20, cache write $5 | 1M, 128k out | Default Opus in Claude Code from v2.1.280. Thinking is always on and can't be disabled. Fast mode is $8/$40, up to 2.5x speed, and left research preview on the API on Oct 15. Anthropic says typical workloads cost about 40% less than Opus 5. At launch: higher 5-hour limits on Pro, Max, Team and seat Enterprise, plus a one-time rate-limit reset you can save and use later. Some cyber tasks reroute to Opus 4.8. |
| **Sonnet 5.5** (`claude-sonnet-5-5`) | Sep 28, 2026 | $2 / $10; cache read $0.10 since Oct 7 (was $0.20) | 1M | 30%+ faster output than Sonnet 5. Close to Opus 5.5 on GDPval and OSWorld. Default effort is Medium in apps and Claude Code, High on the API. With Sonnet 5's thinking-off setup, migrating needs `thinking: {"type":"between_tools"}`. Default Sonnet from v2.1.284. |
| **Haiku 5.5** (`claude-haiku-5-5`) | Oct 7, 2026 | $0.10 / $0.50 (≤100K prompt); $0.50 / $2.50 above that | 1M, 128k out | First Haiku with an effort setting. Fastest model at standard speed. Anthropic suggests it as a subagent model, for compaction, and for classification. Default Haiku from v2.1.293. |
| Opus 5 (`claude-opus-5`) | Jul 24, 2026 | $5 / $25 | 1M | Superseded by Opus 5.5. |
| Sonnet 5 | Jun 30, 2026 | $2 / $10 (kept, not raised to $3/$15, per the Aug 10 note) | 1M | — |
| Fable 5 / Mythos 5 | Jun 9, 2026 | — | 1M | Access suspended Jun 12, restored Jul 1. |

### Fable on a Max plan

Source: support.claude.com/en/articles/15424964, dated Sep 2, 2026.

- Fable 5 and 5.1 are included on Max, premium Team seats and premium seat Enterprise.
- Fable can use up to 50% of your weekly limit at no extra cost. It also burns through limits faster than other models.
- Past that share, Fable runs on usage credits (extra usage), or you switch models.
- On Pro and standard seats, Fable always bills to usage credits.
- Claude Code shows a consent prompt before it bills Fable to credits. In `-p` mode or the Agent SDK it bills without asking. Check `/usage` if you script with Fable.
- In Claude Code, use the `/model fable` or `best` aliases.

### Retirements and deprecations

- Opus 4 and Sonnet 4 retired Jun 15.
- Opus 4.1 retired Aug 5.
- Sonnet 4.5 retires Nov 30, 2026.
- Fast mode is removed from Opus 4.6 and 4.7.

### Default-model changes in Claude Code

- 2.1.280: Pro and Team Standard default to Opus, matching Max.
- New models start at their own default effort. `/effort` is saved per model.

**URLs:**
- https://www.anthropic.com/news/claude-opus-5-5
- https://www.anthropic.com/news/claude-sonnet-5-5
- https://www.anthropic.com/claude-haiku-5-5
- https://platform.claude.com/docs/en/release-notes/overview
- https://support.claude.com/en/articles/15424964-claude-fable-models-on-your-plan

---

## 2. Plans, usage limits, credits

### Monthly API credits for Max (Oct 7, 2026)

- **What it is:** $100 a month on Max 5x and $200 a month on Max 20x. Team plans pool up to $500.
- **How to claim:** claude.ai → Settings → Billing → API credits, then link one Claude Console organization. You need Owner, Admin or Billing role there. You must have been on the plan for 7 days. No card is needed. Rollout takes a few days.
- **What it covers:** Claude API, Managed Agents, the Agent SDK with an API key, and the Console playground.
- **What it doesn't cover:** interactive Claude Code, or extra usage in the apps.
- **Expiry:** credits don't roll over.
- **URLs:**
  - https://support.claude.com/en/articles/17154008-api-credits-for-max-and-team-plans
  - https://platform.claude.com/docs/en/about-claude/api-credits-for-subscribers
- **Why it matters for a harness:** it gives you a legitimate API-key budget for Agent SDK scripts, third-party tools and Managed Agents, without breaking the OAuth rules in section 8.

### Limits structure

- A rolling 5-hour session limit.
- Two weekly limits: one across all models, and a separate Sonnet weekly limit.
- Your reset time is shown in Settings → Usage.
- Reported but not checked against an Anthropic page:
  - May 2026: 5-hour limits doubled for Pro, Max, Team and seat Enterprise, and the peak-hour reduction was removed for Pro and Max.
  - Sep 22: 5-hour limits raised again with Opus 5.5, plus a one-time saveable reset.
- A class action over how Max limits were advertised was filed around Sep 8 (news coverage only).
- The Claude Code docs say advertised limits "assume ordinary, individual usage of Claude Code and the Agent SDK".

### Claude Code usage tooling

| Version | Feature |
|---|---|
| 2.1.234 | Auto-continue when a claude.ai usage limit resets. Toggle it in `/config`. |
| 2.1.243 | `/usage` gains a Loops breakdown. |
| 2.1.284 | `/rate-limit-options` command. |
| 2.1.299 | `/usage` warnings for max effort, workflows, always-on context and large tool results. |
| 2.1.251, 2.1.260 | `/cost` shows prompt-cache hit ratio and likely miss causes. |
| 2.1.299 | Idle compaction: a 200K+ token session idle about 54 minutes is compacted before the 1-hour cache expires. |

**Usage credits (extra usage):** turn them on at claude.ai/settings/usage. Routines and Fable fall back to credits when limits run out.

---

## 3. Claude Code features

Plan availability is from code.claude.com/docs/en/feature-availability. "Subscription" means signed in with claude.ai on Pro, Max, Team or Enterprise.

### Autonomy and long-running work

**Auto mode** (permission classifier)
- Introduced in 2026; engineering post Mar 25.
- 2.1.284 (Sep 28): auto mode is now the default permission mode for interactive and VS Code sessions on every plan when no mode is set.
- 2.1.246: Auto mode tab in `/permissions`.
- 2.1.257: one-time prompt before reads outside the working directory; block them with `permissions.blockReadsOutsideWorkingDirectories`.
- 2.1.271: per-command `allowed_domains`.
- 2.1.278 / 2.1.282: server-side classifier by default.
- Rules go in `autoMode` in user settings. Project settings are ignored for this. CLAUDE.md also steers the classifier.
- Docs: https://code.claude.com/docs/en/auto-mode-config

**/goal** (2.1.139, May 11)
- Set a completion condition, and Claude keeps taking turns until a separate evaluator model judges it met or impossible.
- Works interactively, with `-p`, and over Remote Control.
- Docs: https://code.claude.com/docs/en/goal

**/loop** (2.1.71, Mar)
- Recurring prompt inside a session, interval of 1 minute or more.
- Self-paced dynamic mode is always available (2.1.248).

**Routines** (research preview, Apr 14, 2026)
- Saved prompt + repos + connectors that run on Anthropic's cloud.
- Triggers: schedule (hourly or longer, or one-off), API POST, or GitHub events.
- Pro, Max, Team and Enterprise.
- Create at https://claude.ai/code/routines or with `/schedule daily PR review at 9am`.
- Runs draw on plan limits, then usage credits if they're on. Routines can publish artifacts.
- Docs: https://code.claude.com/docs/en/routines

**Desktop local scheduled tasks**
- Code tab → Routines → New routine → Local.
- The machine must be on. Minimum interval 1 minute. Optional per-run worktree.
- Docs: https://code.claude.com/docs/en/desktop-scheduled-tasks

**Channels** (research preview, 2.1.80, Mar)
- MCP servers that push events into a running session. Plugins ship for Telegram, Discord and iMessage. They need Bun.
- `--channels` can relay permission prompts to your phone.
- Subscription or Console only.
- Docs: https://code.claude.com/docs/en/channels

**Remote Control**
- Drive a local session from claude.ai/code or the mobile app.
- Start it with `claude --remote-control` or `/remote-control`.
- Pro and Max; no API keys. It breaks if `ANTHROPIC_BASE_URL` is non-default or `CLAUDE_CODE_DISABLE_NONESSENTIAL_TRAFFIC` is set.
- 2.1.273: fork a Remote Control session from the app.
- 2.1.251: subagent tool calls stream live to Remote Control clients.
- Docs: https://code.claude.com/docs/en/remote-control

**Cloud sessions** (Claude Code on the web)
- Set up with `/web-setup` (connects GitHub). Move a session local with `/teleport`.
- Oct 6 field-guide blog post.
- 2.1.271: fast mode works in cloud sessions.

**Projects** (Claude Code, public beta, Pro and Max only)
- One coordinating conversation that spawns parallel cloud threads, with shared instructions, memory and a Library tab.
- Threads default to Opus at high effort, which draws limits fast. Lower it in Project settings.
- Docs: https://code.claude.com/docs/en/claude-projects

**Dispatch**
- Message a task from your phone to the Desktop app.
- Pro and Max.

### Multi-agent

**Dynamic workflows / Workflow tool** (2.1.154, May 28)
- Claude writes an orchestration script that runs tens to hundreds of subagents.
- Trigger it with the keyword `ultracode` (renamed from `workflow` in 2.1.160) or by asking. See runs with `/workflows`.
- Bundled workflow: `/deep-research`.
- All paid plans. On Pro, enable it in `/config`.
- Related settings: Dynamic workflow size in `/config`, `CLAUDE_CODE_WORKFLOW_SUBAGENT_MODEL` (2.1.296), `CLAUDE_CODE_WORKFLOW_MAX_CONCURRENT_AGENTS` (2.1.269).
- Docs: https://code.claude.com/docs/en/workflows

**Agent teams** (experimental since 2.1.32, Feb)
- Enable with `CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS=1`.
- Uses a lot of tokens. Once enabled, Claude may form teams without being asked.
- Docs: https://code.claude.com/docs/en/agent-teams

**Agent view** (`claude agents`, research preview, 2.1.139)
- One list of all sessions.
- Background sessions with `claude --bg`, `claude attach`, `claude logs`.
- Docs: https://code.claude.com/docs/en/agent-view

**Cross-session messaging** (2.1.224, Aug 7)
- `SendMessage` / `ListAgents` between your sessions across machines on a subscription.
- 2.1.236 adds `notify_when_idle`.

**Subagents**
- Agent tool takes an `effort` parameter (2.1.292).
- Frontmatter: `omitClaudeMd` (2.1.271), `autoCompactWindow` (2.1.296), `experimental.cacheTtl` (2.1.248).
- `CLAUDE_CODE_SUBAGENT_MODEL` is the default subagent model, and `_FORCE` overrides per-agent choices.
- Haiku 5.5 is a cheap choice for Explore-type subagents.

### Model and quality controls

**Advisor tool** (experimental, 2.1.117 Apr; text form 2.1.260)
- A stronger model, typically Fable or Opus, is consulted at key points.
- Turn it on with `/advisor`, `/advisor <model>`, `advisorModel` or `--advisor`. Turn it off with `/advisor off` or `CLAUDE_CODE_DISABLE_ADVISOR_TOOL=1`.
- Subscription or Anthropic API only.
- Fable as advisor may need usage-credit consent.
- The API rejects Opus 4.7, Opus 4.8 and Sonnet 5 as advisors (Sep 28).
- Docs: https://code.claude.com/docs/en/advisor

**Fast mode** (`/fast`)
- Opus 5.5, Opus 5 and Opus 4.8. Up to 2.5x faster at a higher token price.
- Available on subscriptions.
- Docs: https://code.claude.com/docs/en/fast-mode

**/effort**
- Saved per model (2.1.251).
- `s` sets it for this session only (2.1.257).
- `maxEffortLevel` caps it (2.1.267). `toggleUltracode` keybinding (2.1.284).

**Model aliases and defaults**
- Aliases: `best`, `fable`, `opus`, `sonnet`, `haiku`.
- `ANTHROPIC_DEFAULT_MODEL` sets the default for new sessions (2.1.236).
- `modelPicker` curates the picker (2.1.243).
- Docs: https://code.claude.com/docs/en/model-config

**Code review**
- `/code-review` runs locally and takes `--max-findings` (2.1.288).
- `/ultrareview` is a cloud multi-agent review (2.1.111) and works on subscriptions.
- Managed **Code Review** went GA Oct 15, but for Team and Enterprise only, not Max.
- Docs: https://code.claude.com/docs/en/ultrareview

**/doctor prompt-audit** (2.1.283)
- Audits CLAUDE.md, skills, agents and commands for prompting patterns written for older models.
- Worth running after a model upgrade.

**/skill-doctor** (2.1.261)
- Shows skills that go unused and what they cost in context.

### Extensibility

**Plugins and marketplaces**
- One-step install: `claude plugin install <p> --marketplace <src>` (2.1.292).
- `claude plugin init` scaffolds a plugin; `plugin eval` (2.1.269) and `plugin validate --json` test it.
- `archive` zip source (2.1.224). GitLab marketplaces (2.1.232).
- `--plugin-dir` can point at a folder of plugins (2.1.265).
- `claude plugin configure` (2.1.285).
- Sep 25: a portal for submitting plugins to the Claude directory.
- Docs: https://code.claude.com/docs/en/plugins/overview

**Claude Mods** (2.1.287, about Oct 1)
- TypeScript plugins that change deeper behavior and the UI: prompt decorations, notifications, `agent.spawn` hooks, and more.
- Built-in mod "You should know": a side agent that flags things you might miss. Enable it with `/plugin enable cc-plugin-you-should-know@builtin`.
- Blog posts: "Getting started with Claude Code mods" and "Customize Claude Code with mods" (Oct 1).
- Docs: https://code.claude.com/docs/en/plugins/mods/overview

**Skills and plugins sync**
- Skills and plugins enabled on your claude.ai account sync to terminal sessions (2.1.275).
- Opt out with `syncClaudeAiSkills: false` or `syncClaudeAiPlugins: false`.
- `/reload-skills` and `/reload-plugins` reload without a restart.

**Hooks**
- `PreModelSwitch` and `PostModelSwitch` (2.1.251).
- `onFailure: "block"` (2.1.295).
- `PermissionDenied` with retry.
- Notification hook for background agents (`agent_needs_input` / `agent_completed`).

**AGENTS.md**
- Read when a project has no CLAUDE.md (2.1.277).

**Artifacts from Claude Code**
- Publishes private claude.ai pages. Pro, Max, Team and Enterprise.
- Browser-tab icons (2.1.268).
- Docs: https://code.claude.com/docs/en/artifacts

**MCP**
- Default protocol is 2026-07-28 (2.1.292 / 2.1.295).
- URL elicitation, so a server can open a sign-in flow.
- `/mcp reconnect all` (2.1.284).
- claude.ai connectors load in Claude Code only when you are signed in with the subscription.

### Desktop, IDE, browser, computer

**Claude Desktop Code tab**
- `claude --desktop` opens the current directory or a session in the app (2.1.285).
- Desktop runs on macOS and Windows. Linux is in beta.
- iOS simulator testing.
- Docs: https://code.claude.com/docs/en/desktop

**Claude in Chrome**
- GA in Claude Code July 1 (2.1.198).
- Needs extension v1.0.36+ and `/login`. It does not work with API keys or `setup-token`.
- Start it with `claude --chrome` or `/chrome`.
- Docs: https://code.claude.com/docs/en/chrome

**Computer use from the CLI**
- Research preview, macOS, **Pro and Max only**.
- Enable the built-in `computer-use` MCP server in `/mcp`, then grant Accessibility and Screen Recording.
- Docs: https://code.claude.com/docs/en/computer-use

**Voice dictation**
- `/voice`. Needs a claude.ai account.

**Mobile**
- Run `/mobile` for a QR code. The Code tab reaches cloud sessions and Remote Control.

### Quality-of-life (Aug to Oct)

| Version | Feature |
|---|---|
| 2.1.237 | Built-in "Concise" output style. |
| 2.1.269 | `/output-style` command. |
| 2.1.282 | `maxProseWidth`. |
| 2.1.257 | `timeFormat` / `timeZone`. |
| 2.1.235 | `spellcheck`. |
| 2.1.260 | Diff panel, toggled with `/diff`. |
| 2.1.288 | Ctrl+C prompt recovery with Up. |
| 2.1.275 | Send-now key (ctrl+enter). |
| 2.1.247 | `SendFeedback` drafts. |
| 2.1.248 | `--restricted` mode. |
| 2.1.170 | `--safe-mode` for troubleshooting. |
| 2.1.301 | Unattended retry watchdog (`CLAUDE_CODE_RETRY_WATCHDOG`) with a usage-limit wait cap. |

---

## 4. Claude apps (web, desktop, mobile)

**Cowork**
- Timeline:
  - Jan 12: research preview on Max.
  - Apr 9: GA on macOS and Windows.
  - Jul 7: web and mobile (Max first), with remote sessions that keep running with the laptop closed.
  - Sep 16: "Cowork in every conversation". Chat and Cowork merged, rolling out to Pro and Max.
- Scheduled tasks since Feb 25. Computer use in Cowork since Mar 23 (Pro and Max).
- Dispatch is a persistent agent thread you message from your phone.
- Fable in Cowork needs the latest Desktop.

**Memory**
- Mar 2: memory from chat history, all plans.
- Jul 10: categorized entries replace the daily summary.
- Aug 25: memory works in Cowork, with editable Topics and a sensitive-topics setting. On by default for Free, Pro and Max.
- Jul 9: monthly recap (Settings → Reflect, beta) and break reminders.

**Claude Design, Slides and Docs**
- Design launched Apr 17 (Labs).
- Sep 16: Design, Slides and Docs available in any conversation.
- Oct 8: out of beta on every plan, including Free.
- Docs export to Word (Oct 8).

**Claude Dashboards** (beta, Oct 8, paid plans)
- Live dashboards built on a data warehouse or a connector like Salesforce.
- Claude Motion (animated explainers exported as MP4) is Team and Enterprise only.
- https://claude.com/resources/articles/dashboards-and-motion

**Connectors**
- Google Docs, Sheets and Slides: Workspace add-on plus beta connectors (Oct 6).
- Microsoft 365 write tools (Jul 7, admin consent needed).
- Salesforce plugin (Sep 15, beta).
- Plugin directory submissions (Sep 25).

**Other app features**
- Edit drafts in place by highlighting (Jun 12).
- Inline charts and diagrams (Mar 12).
- Interactive apps on mobile (Mar 25).
- Health data on iOS and Android (US, Pro and Max).

**Claude Tag** (tag Claude in Slack)
- Team and Enterprise only.
- Claude Code in Slack is available on Pro and Max.

---

## 5. API / Agent SDK / Managed Agents

These are relevant if you use the Max API credits.

**GA on Aug 19:**
- Files API, now with expiry and pagination.
- Skills / `/v1/skills`.
- `computer_toolset_20260801`.
- New `browser_toolset_20260801`.

**Context management:**
- Compaction on demand (beta Sep 14, `compact-2026-09-04`): you get back a signed compaction block.
- Mid-conversation system messages (Jul 15).
- Per-message effort (beta Sep 1).
- Turn-scoped system messages (`clear_at`).
- Cache diagnostics GA (Sep 23).
- `thinking.display: "updates"` (beta).

**Code execution:**
- `code_execution_20260120`: REPL state persists, and it supports programmatic tool calling.
- `code_execution_20260521`: 90 s per-cell limit.

**Advisor tool (API):**
- `tools[].max_tokens` caps advisor output (Jun 2).

**Managed Agents:**
- Scheduled deployments, vault credentials and webhooks (Jun to Jul).
- Session budgets; skills loaded from GitHub (Aug 7).
- `auto` permission policy (Sep 10).
- Dynamic workflows (Oct 9): `"multiagent": {"type":"multiagent_20261001","workflows":{"type":"enabled"}}`.
- OpenTelemetry export (beta Oct 14).
- Memory stores use `agent-memory-2026-07-22`.
- "Dreams" (async memory consolidation) supports the 5.5 models (Oct 1).
- `/claude-api managed-agents-onboard` sets up Managed Agents from Claude Code (2.1.290).

**`ant` CLI:**
- `ant apply` manages resources as code with a lockfile (Sep 3).

**SDK changes:**
- Python SDK 1.0 (Aug 20): httpx2, Python 3.10+, removes `temperature`, `top_p` and `top_k`.
- `/claude-api upgrade` migrates projects to it.

**Fallbacks and refusals:**
- `fallbacks` parameter re-runs refused requests on another model.
- Refusals before output in some categories are billed again (Sep 24).

**claude-api skill commands:**
- `cost-optimize`, `prompt-audit`, `build-eval` / `hillclimb` (Oct 7 blog post).

**Release notes:** https://platform.claude.com/docs/en/release-notes/overview

---

## 6. Programs

**Claude Startups program, expanded Oct 6, 2026**
- Up to about $7,000 in Claude products and credits.
- Reported details: one year of Claude Team (up to 5 Premium seats) and a $1,000 one-time API credit.
- "Startup Stack" partner offers worth up to $45k at partner list price.
- Eligibility: founded within the last 5 years, or funded within the last 2.
- Apply at claude.com/programs/startups.
- https://claude.com/blog/were-expanding-the-claude-startups-program-to-help-founders-build

**Other programs**
- Cyber Verification Program, expanded Oct 6.
- Life Sciences Verification Program.
- These matter only if you hit cyber or bio safeguards.

**Not relevant to an individual:**
- $100M engineer-training fund (Oct 2).
- Claude for Government GA (Sep 30).

---

## 7. Engineering blog (2026)

Worth reading for harness design:
- "How we contain Claude across products" (May 25)
- "Scaling Managed Agents" (Apr 8)
- "How we built Claude Code auto mode" (Mar 25)
- "Harness design for long-running application development" (Mar 24)
- "Building a C compiler with a team of parallel Claudes" (Feb 5)

Recent claude.dev posts:
- "Building effective agent automations" (Oct 8)
- "How the Claude Code team does code review" (Oct 16)

---

## 8. Subscription use in third-party tools (important)

**Official text** (https://code.claude.com/docs/en/legal-and-compliance, read Oct 16):
- OAuth (Free, Pro, Max, Team, Enterprise) is "designed to support ordinary use of Claude Code and other native Anthropic applications."
- Developers building products, **including with the Agent SDK**, should use API keys.
- Third parties may not offer Claude.ai login, route requests through Free, Pro or Max credentials for their users, or collect or intermediate Claude.ai tokens.
- The Agent SDK docs say: "Unless previously approved, Anthropic does not allow third party developers to offer claude.ai login or rate limits for their products, including agents built on the Claude Agent SDK."
- Allowed: an end user signing in to the **unmodified Claude Code binary** with their own subscription, even when a platform hosts that binary.
- The docs also say Pro and Max limits "assume ordinary, individual usage of Claude Code and the Agent SDK."

**Timeline** (secondary sources):
- Jan 9, 2026: enforcement against third-party OAuth clients began.
- Feb 2026: the rule was written into the docs.
- About Apr 4, 2026: full cutoff, with a one-time $200 credit for Max subscribers redeemable to Apr 17.

**In practice:**
- Use your Max login only in Claude Code (CLI, desktop, IDE extensions, web, mobile) and the Claude apps.
- Use the new monthly Max API credit with a Console API key for OpenClaw-style or other third-party harnesses, Agent SDK apps and scripts.
- Wrapping the real `claude` binary (for example tmux, `claude -p` scripts, ACP adapters that spawn the official CLI) is the grey-but-tolerated zone. Never extract or proxy OAuth tokens.

---

## 9. Set these up first (new Mac, translator / annotator / freelancer / coder)

1. **Install Claude Code natively and sign in with Max.** Run `claude update` to get 2.1.30x. Run `/login` with claude.ai, not an API key, because Chrome, Remote Control, routines, artifacts, computer use and voice all need the subscription login. Install Claude Desktop with `claude --desktop`, and the mobile app with `/mobile`.
2. **Claim the Max API credit** ($100 or $200 a month). Go to Settings → Billing → API credits and link a Console organization. Create an API key and store it in Keychain. Use it for Agent SDK scripts, third-party tools, batch translation jobs and Managed Agents. Keep it separate from Claude Code's OAuth login.
3. **Set model, effort and auto mode in user settings** (`~/.claude/settings.json`):
   - Default to Opus 5.5 (`opus`) at medium or high effort.
   - Keep `fable` / `best` for hard problems. Fable can use up to 50% of the weekly limit, then bills to credits.
   - Use Haiku 5.5 for cheap subagents via `CLAUDE_CODE_SUBAGENT_MODEL`.
   - Accept auto mode as the default. Put `autoMode` rules and `permissions.ask` rules for anything client-sensitive in user settings, since project files are ignored for these.
   - Optionally set `permissions.blockReadsOutsideWorkingDirectories`.
   - Decide whether to turn on usage credits (extra usage).
4. **Write CLAUDE.md / AGENTS.md, then run `/doctor prompt-audit` and `/skill-doctor`.** Put translation style guides, glossaries, annotation schemas and client rules into user-level CLAUDE.md and skills. Prune skills that waste context.
5. **Recreate skills and plugins and sync them.** Enable skills on claude.ai so they sync to the terminal. Install marketplace plugins with `claude plugin install <p> --marketplace <src>`. Consider the built-in "You should know" mod and the Concise output style.
6. **Connect connectors:** Google Docs, Sheets and Slides (new Oct 6), Gmail, Calendar and Drive in claude.ai. They load in Claude Code under the subscription login. Run `/mcp reconnect all` after setup.
7. **Set up Remote Control and mobile.** Launch long sessions with `claude --remote-control` to steer them from your phone. Use cloud sessions (`/web-setup` connects GitHub) or Claude Code Projects (beta) for work that should keep going with the laptop closed.
8. **Automate recurring work:**
   - Routines (`/schedule`, claude.ai/code/routines) for cloud jobs.
   - Desktop local scheduled tasks for anything that needs local files, such as a daily client-inbox triage or invoice and timesheet summaries.
   - `/loop` and `/goal` for in-session persistence.
9. **Browser and computer use:** install the Claude in Chrome extension (v1.0.36+) for web research, portal form-filling and CAT-tool web UIs. Enable the `computer-use` MCP (macOS, Pro and Max) for GUI-only apps. Grant the Accessibility and Screen Recording permissions.
10. **Heavy-lift tools when needed:**
    - Dynamic workflows (`ultracode`, `/deep-research`) for large audits or research.
    - `/advisor` with Opus or Fable for long refactors.
    - `/ultrareview` before shipping client code.
    - `/fast` when latency matters.
    - Enable agent teams only if you really need them, since they use a lot of tokens.
11. **Optional:** Channels (Telegram or Discord bridge, needs Bun) to ping or answer a running session. Cowork in the app for non-code document work: memory, Docs, Slides and Design artifacts, Dashboards. Turn on `/usage` monitoring and the auto-continue-at-limit setting.

**Skip on Max** (Team and Enterprise only): managed Code Review, Claude Tag in Slack, Claude Motion, self-hosted runners.
