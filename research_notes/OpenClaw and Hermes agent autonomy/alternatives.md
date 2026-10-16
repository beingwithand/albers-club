# Alternatives to OpenClaw / Hermes Agent for Autonomous, Always-On Agents (as of Oct 2026)

Method note: research date 2026-10-15. Many third-party sites (The Register, DataCamp, aimagicx, lushbinary, amux, openalternative, nanoclaw.dev, Hacker News, prommer.net) failed to fetch (DNS errors from the research sandbox), and GitHub API access to the repos was blocked. So many findings below come from search-result summaries, not full-page reads. Anthropic's official Claude Code docs (code.claude.com) were fetched in full and are the most reliable source here. Figures from comparison blogs (stars, RAM, prices) conflict often and are flagged.

## Which tools genuinely support long-running unattended operation (cron/heartbeat, event triggers, persistent memory, messaging interfaces)?

### Takeaway
Three tiers support real unattended operation. (1) Self-hosted "Claw-family" personal agents (NanoClaw, nanobot, ZeroClaw, PicoClaw, IronClaw, Moltis) give messaging channels, schedulers and memory on your own box. (2) Cloud coding agents with schedule and event triggers: Claude Code Routines, Cursor Automations, Devin, and (schedule-only, per one source) Codex Automations. (3) Workflow platforms (n8n, Zapier Agents, Lindy) where triggers are first-class. General computer-use agents (ChatGPT agent, Manus, Comet) have only limited scheduled tasks and are still best supervised.

### Cited Findings

**OpenClaw-family open-source alternatives (personal, multi-channel agents)**
- The comparison sources agree on each project's niche. NanoClaw is the security-first pick (container isolation per session/chat group, TypeScript, about 700 lines, "Agent Swarms"). ZeroClaw is the efficiency pick (Rust, about a 3.4MB single binary, approvals and OS sandbox on by default). nanobot is the Python learner's pick (about 4,000 readable lines, sandboxing opt-in). PicoClaw is a Go binary using under 10MB RAM on $10 embedded boards, with a pre-1.0 security warning. IronClaw is the security maximalist (WebAssembly sandbox plus TEE-backed execution, few channels, one source lists only Telegram and Discord). — [OpenAlternative](https://openalternative.co/blog/best-openclaw-alternatives); [aimagicx](https://www.aimagicx.com/blog/openclaw-alternatives-comparison-2026); [lushbinary](https://lushbinary.com/blog/zeroclaw-openclaw-personal-ai-agents-compared-2026/); [MEXC news](https://www.mexc.com/news/1048343) (search-summary level only)
- ZeroClaw's status is contested. One source warns its GitHub repo was taken down as of March 2026, but newer comparisons list recent releases. — [search summary of aimagicx/atomicagent comparisons](https://atomicagent.io/blog/openclaw-alternatives/); verify before recommending
- Reported nanobot star counts range from about 13k to 49k depending on the article, so treat them as relative only. — [Taskade](https://www.taskade.com/blog/best-openclaw-alternatives); [OpenAlternative](https://openalternative.co/blog/best-openclaw-alternatives)
- Moltis is listed as another competitor alongside NanoClaw and ZeroClaw. — [aimagicx](https://www.aimagicx.com/blog/openclaw-alternatives-comparison-2026)
- NanoClaw is built on the Claude Agent SDK, so Claude is the "brain." Each agent group runs in its own container containing just the agentic loop, so a compromised agent can't see the rest of the host. — [The Register, 2026-03-01](https://www.theregister.com/2026/03/01/nanoclaw_container_openclaw/); [Trending Topics](https://www.trendingtopics.eu/nanoclaw-challenges-openclaw-with-container-isolated-ai-agents-for-enhanced-security/)
- On scope, NanoClaw has "a few hundred lines" against OpenClaw's "hundreds of thousands." Its out-of-the-box integrations are minimal compared with OpenClaw's ecosystem, and it expects you to customize your own fork using Claude Code. — [DataCamp](https://www.datacamp.com/blog/nanoclaw-vs-openclaw); [ScreenshotOne](https://screenshotone.com/blog/nanoclaw-versus-openclaw/); [EveryDev](https://www.everydev.ai/tools/compare/nanoclaw-vs-openclaw)

**Claude Code's native autonomy features (official docs)**
- Claude Code has three scheduling tiers:
  - Cloud **Routines** run on Anthropic infrastructure. They don't need your machine on, persist across restarts, use a fresh repo clone (no local files), get connectors per task, run with no permission prompts, and have a 1-hour minimum interval.
  - **Desktop scheduled tasks** run on your machine with local file access. Permissions are configurable, and the minimum interval is 1 minute.
  - **`/loop`** is session-scoped with a 1-minute minimum and needs an open session.
  — [Claude Code docs: scheduled tasks](https://code.claude.com/docs/en/scheduled-tasks)
- Session `/loop` and Cron tasks expire after 7 days and do no catch-up for missed fires. A session can hold up to 50 tasks. Recurring tasks are jittered up to half the interval, capped at 30 minutes. A bare `/loop` runs a built-in "maintenance prompt" (finish unfinished work, tend the PR, cleanup), or `.claude/loop.md` if one exists. In self-paced mode Claude picks a 1-minute to 1-hour delay itself. — [Claude Code docs: scheduled tasks](https://code.claude.com/docs/en/scheduled-tasks)
- Routines are a **research preview**, launched around April 2026. They are a saved prompt plus repos plus connectors with three trigger types: Schedule (presets, custom cron via `/schedule update`, one-off runs), API (an HTTP POST `/fire` endpoint with a bearer token, beta header `experimental-cc-routine-2026-04-01`) and GitHub events (PR and release, with filters). They are available on Pro, Max, Team and Enterprise, and are created at claude.ai/code/routines or with `/schedule`. — [Claude Code docs: routines](https://code.claude.com/docs/en/routines); [The Register, 2026-04-14](https://www.theregister.com/software/2026/04/14/claude-code-routines-promise-mildly-clever-cron-jobs/5222046) ("mildly clever cron jobs")
- Routine limits (official): 100 scheduled runs per hour per account; 30 Run-now/API fires per hour per routine; 100 API fires per hour per account. Runs draw down normal subscription usage, with optional metered overage via usage credits. Third-party guides citing "5/15/25 runs per day" by plan conflict with the current official docs and look outdated. — [Claude Code docs: routines](https://code.claude.com/docs/en/routines); contradicted by [Alex Dunlop](https://www.alexdunlop.com/writing/claude-code-scheduled-tasks) and [MakerKit](https://makerkit.dev/blog/tutorials/claude-code-routines-guide)
- A routine's status shows green if the session merely exited without an infrastructure error, which "does not mean the task in your prompt succeeded." If GitHub auth lapses, runs are skipped for up to 72 hours and then the routine turns off. — [Claude Code docs: routines](https://code.claude.com/docs/en/routines)
- **Channels** (research preview) is the messaging interface. An MCP server pushes events into a *running* local session, and it can be two-way. Official plugins cover Telegram, Discord and iMessage (macOS, which reads chat.db and needs Full Disk Access), plus a localhost "fakechat" demo. It requires Bun. "Events only arrive while the session is open, so for an always-on setup you run Claude in a background process or persistent terminal." — [Claude Code docs: channels](https://code.claude.com/docs/en/channels)
- Related Anthropic surfaces: Remote Control (drive a local session from the claude.ai mobile app), Claude in Slack (an @Claude mention spawns a cloud session), and cloud sessions on the web. — [Claude Code docs: channels, "How channels compare"](https://code.claude.com/docs/en/channels)

**Cloud autonomous coding agents**
- **Cursor Automations** launched 2026-03-05. Agents run on schedules or on events (Slack message, new Linear issue, merged GitHub PR, PagerDuty incident, custom webhooks), each launching a cloud sandbox. — [noqta.tn](https://noqta.tn/en/blog/cursor-automations-always-on-ai-coding-agents-2026); [Pulse 2.0](https://pulse2.com/cursor-automations-launched-for-always-on-agentic-coding-workflows/amp/); [TestingCatalog](https://www.testingcatalog.com/cursor-debuts-automations-for-scheduled-coding-agents.md)
- **Codex Automations** is reported as schedule-only, with event triggers "on the roadmap." Per the same source, Claude Code Routines and Cursor Automations both ship schedule, API and event triggers. This is a single source, unverified against OpenAI docs. — [AI Catchup](https://aicatchup.com/comparisons/claude-code-routines-vs-cursor-automations)
- **Codex cloud** is a hosted sandbox that runs tasks and reviews PRs. — [SSOJet](https://ssojet.com/blog/best-cloud-coding-agents); [Firecrawl](https://www.firecrawl.dev/blog/best-ai-coding-agents)
- **Devin** is described as the most autonomous coding agent, running many agents in parallel. — [techsy.io](https://techsy.io/en/blog/background-coding-agents-compared); [amux](https://amux.io/guides/background-agents-compared/)
- **Jules** (Google) is the most GitHub-native, built around a delegate-and-review workflow. No scheduled-task feature was found. — [SSOJet](https://ssojet.com/blog/background-coding-agents)
- **OpenHands** is open-source (MIT) and self-hostable, with about 72% on SWE-bench Verified when run with Claude. No scheduled-task feature was found in sources. — [techsy.io OpenHands vs Devin vs Manus](https://techsy.io/en/blog/openhands-vs-devin-vs-manus); [Spheron](https://www.spheron.network/blog/deploy-openhands-gpu-cloud/)

**General computer-use agents**
- **Manus** takes a goal and plans, executes and delivers on its own. You can watch it in a virtual desktop and intervene. Its free tier reportedly includes 300 daily refresh credits, 1 concurrent task and **2 scheduled tasks**. — [Manus blog](https://manus.im/blog/best-ai-agents); [futureagi](https://futureagi.com/blog/manus-ai-comparison-2025/); [builts.ai](https://builts.ai/blog/manus-vs-chatgpt-vs-claude-vs-perplexity/)
- Meta reportedly acquired Manus in December 2025. This comes from a single comparison site and was not confirmed against news reports. — [futureagi](https://futureagi.com/blog/manus-ai-comparison-2025/)
- **ChatGPT agent** (the successor to Operator) is described as a general agent with browsing, scheduled tasks and app connections on individual plans. — [webnet.com.au](https://webnet.com.au/cpanel-cloud-hosting/10-best-manus-alternatives-in-2026/)
- **Perplexity Comet**'s Max tier reportedly offers autonomous tasks that run on a schedule, but the same review says it is "best treated as a planner you supervise, not an autopilot you walk away from." Perplexity also has a separate "Perplexity Computer" agent. — [The Creators AI](https://thecreatorsai.com/p/perplexity-comet-review); [Sliq](https://getsliq.com/blog/perplexity-computer-vs-manus-ai)

**Workflow automation platforms with agents**
- **n8n** is self-hostable with unlimited executions and has an MCP Server Trigger. Its drawback is fewer one-click native integrations than Make or Zapier. **Zapier Agents** has the strongest app coverage. **Lindy** is "describe a job role" rather than draw a flow, has no self-hosting, and targets non-technical users. — [frankx.ai](https://www.frankx.ai/blog/best-no-code-ai-agent-builders-2026); [aiagentchooser](https://aiagentchooser.com/for-automation/); [planetarylabour](https://planetarylabour.com/articles/no-code-ai-agents)

### Inferences
- For a "Mac Mini always-on Claude" setup, Claude Code natively covers every primitive: a messaging interface via Channels, durable local schedules via Desktop scheduled tasks, cloud schedules and webhooks via Routines, and in-session heartbeats via `/loop`. What it lacks against OpenClaw/Hermes-style agents is a single long-lived daemon with a built-in cross-session memory layer. Channels only work while a session process stays alive, and Routines start a fresh session for every fire, with no memory beyond repo files and connectors.
- NanoClaw is the closest "OpenClaw-like but Claude-native" option, since it sits on the Agent SDK. That makes it sensitive to Anthropic's Agent SDK billing policy (see the third question).
- The persistent memory implementations of nanobot, ZeroClaw, PicoClaw and IronClaw (file-based, SQLite, vector) could not be verified from the fetched material.

### Gaps
- Primary GitHub READMEs and current star counts or release dates for NanoClaw, nanobot, ZeroClaw, PicoClaw, IronClaw and Moltis were not retrievable (GitHub API access was blocked and the project sites wouldn't fetch). ZeroClaw's March 2026 takedown versus its active status is unresolved.
- Official OpenAI docs on Codex Automations triggers, and ChatGPT agent scheduled-task limits, were not fetched.
- Official Jules and OpenHands Cloud scheduling features were not confirmed.
- Desktop scheduled tasks (local, Claude Desktop) behaviour, such as whether they need the app open, was not fetched in detail.

## How do they compare on reliability, safety/sandboxing, and cost?

### Takeaway
Sandboxing is strongest in IronClaw (WASM/TEE), NanoClaw (per-group containers), ZeroClaw (default OS sandbox and approvals) and the cloud coding agents (fresh VM or sandbox per run). It is weakest where the agent runs with your full local credentials (OpenClaw itself, `--dangerously-skip-permissions` setups). Cost is the less clear-cut axis. Self-hosted agents are free but pay model API costs. Coding agents run from about $20/month subscriptions up to usage-metered $100–$200+ per developer. Every vendor has moved to credit or usage billing, so headline prices are floors.

### Cited Findings

**Safety and sandboxing**
- OpenClaw has a growing CVE history as its codebase scales. NanoClaw's small, auditable codebase and container isolation are its main selling points. — [DataCamp](https://www.datacamp.com/blog/nanoclaw-vs-openclaw); [modemguides security-first picks](https://www.modemguides.com/blogs/ai-infrastructure/openclaw-alternatives-2026-secure-ai-agents)
- Claude Code Routines run with **no permission prompts**, and every tool from an included connector can be used, "including writes, without asking." All connectors are included by default, so you should remove the ones a routine doesn't need. Actions appear as you: commits carry your GitHub user, Slack messages your account. — [Claude Code docs: routines](https://code.claude.com/docs/en/routines)
- Routine network defaults to "Trusted": an allowlist of package registries and similar hosts, where other hosts get a 403 `host_not_allowed`. Pushes go to `claude/`-prefixed branches by default. Branch protection is the recommended control. Secrets should be stored as network secrets rather than env vars, which are visible to anyone using the environment. — [Claude Code docs: routines](https://code.claude.com/docs/en/routines)
- Prompt-injection mitigations in Routines:
  - API `/fire` text arrives wrapped in a `<routine-fire-payload>` block marked untrusted. The routine prompt must opt in to acting on it, so text sent with a leaked token stays inert.
  - The fired prompt itself "can't act as approval or consent for actions during the run."
  — [Claude Code docs: routines](https://code.claude.com/docs/en/routines)
- Channel security:
  - Each plugin keeps a sender allowlist bootstrapped by pairing codes.
  - A server must be named in `--channels`, so being in `.mcp.json` isn't enough.
  - Anyone allowlisted can approve tool use via permission relay.
  - Team and Enterprise have channels disabled until an Owner enables them.
  - The docs warn that `--dangerously-skip-permissions` for unattended use should be used "only in environments you trust."
  — [Claude Code docs: channels](https://code.claude.com/docs/en/channels)
- Cloud coding agents isolate work in cloud VMs or sandboxes. Cursor's cloud agents run in isolated VMs and can work across multiple repos in parallel. — [SSOJet](https://ssojet.com/blog/background-coding-agents); [noqta.tn](https://noqta.tn/en/blog/cursor-automations-always-on-ai-coding-agents-2026)

**Reliability**
- Routines run on cloud infrastructure, so they "keep working when your laptop is closed." Schedules on the hour can start several minutes late. A green run status ≠ task success. — [Claude Code docs: routines](https://code.claude.com/docs/en/routines)
- Session schedules give no catch-up after missed fires and stop when the terminal closes, unless the session is backgrounded. — [Claude Code docs: scheduled tasks](https://code.claude.com/docs/en/scheduled-tasks)
- An older hands-on test found ChatGPT Operator required constant supervision and often failed to complete tasks. This predates ChatGPT agent and is flagged as old. In the same comparison space, one reviewer found Manus completed tasks the others couldn't. — [LinkedIn test](https://www.linkedin.com/pulse/manus-vs-chatgpt-perplexity-i-tested-all-3-see-who-actually-goldie-lnooe); [builts.ai](https://builts.ai/blog/manus-vs-chatgpt-vs-claude-vs-perplexity/)
- Comet is "a planner you supervise, not an autopilot." — [The Creators AI](https://thecreatorsai.com/p/perplexity-comet-review)

**Cost** (third-party figures that frequently conflict; verify with vendors)
- Codex cloud is bundled with ChatGPT Plus ($20/month) and Pro ($200/month). Codex moved to token-based pricing aligned with the API on 2026-04-02. Active use is estimated at $100–$200 per developer per month (secondary estimate). — [amux pricing](https://amux.io/blog/ai-coding-tools-pricing-2026/); [Firecrawl](https://www.firecrawl.dev/blog/best-ai-coding-agents)
- Cursor Cloud Agents bill separately from subscription credits, on top of the $20/month Pro plan. — [amux pricing](https://amux.io/blog/ai-coding-tools-pricing-2026/)
- Devin pricing:
  - Sources disagree on tiers. One gives a $20/month base plus $2.25 per ACU, where 1 ACU is about 15 minutes, so a bug fix costs about $4.50–$6.75. Others list Pro at $20, Max at $200, and Teams at $80 plus $40 per seat, or a Core $20 and Team $500 (250 ACU).
  - Work is estimated at about $9 per active hour.
  — [techsy.io](https://techsy.io/en/blog/background-coding-agents-compared); [toolhalla](https://toolhalla.ai/blog/devin-vs-openhands-vs-swe-agent-2026); [futureagi](https://futureagi.com/blog/manus-ai-comparison-2025/)
- Jules has a free tier (about 15 tasks per day), with paid capacity via Google AI Pro ($19.99/month) and AI Ultra (about $250). — [SSOJet](https://ssojet.com/blog/background-coding-agents); [webnet.com.au](https://webnet.com.au/cpanel-cloud-hosting/10-best-manus-alternatives-in-2026/)
- OpenHands is free (MIT). Self-hosting on an H100 is estimated at about $1–$2 per task, plus model API fees. — [Spheron](https://www.spheron.network/blog/deploy-openhands-gpu-cloud/)
- Manus starts at $20/month on Pro, with an Extended plan at $200/month (40,000 credits), and is credit-based. — [futureagi](https://futureagi.com/blog/manus-ai-comparison-2025/)
- Comet: the browser is free, Pro is $20/month and Max is $200/month (Max is needed for scheduled autonomous tasks). — [The Creators AI](https://thecreatorsai.com/p/perplexity-comet-review); [aiagentstore](https://aiagentstore.ai/ai-agent/comet-perplexity)
- n8n cloud entry is listed as €24/month and as $20/month, or free self-hosted. Lindy entry is listed as $19.99 or $49.99/month. Zapier per-task pricing "becomes brutal" at volume. The industry trend is credit or execution billing, with busy agent workflows consuming 10–50x the credits of simple automations. — [dev.to (Costa)](https://dev.to/dr_hernani_costa/zapier-vs-make-n8n-lindy-2026-pricing-platform-guide-48co); [ayautomate](https://www.ayautomate.com/blog/best-ai-workflow-automation-platforms); [commercepundit](https://www.commercepundit.com/blog/ai-agent-builders/)
- The self-hosted Claw-family agents are free and open-source. PicoClaw runs on about $10 boards. Real costs are model API usage plus hardware. — [OpenAlternative](https://openalternative.co/blog/best-openclaw-alternatives); [MEXC news](https://www.mexc.com/news/1048343)

### Inferences
- On safety per unit of autonomy, cloud sandboxed runs (Routines, Cursor Automations, Codex cloud, Devin) limit the blast radius to a cloned repo and scoped connectors. A local always-on daemon with full disk, messaging and email access (OpenClaw-style, or Claude Code with skip-permissions on a Mac Mini) has a far larger blast radius. NanoClaw and IronClaw are attempts to get the local multi-channel experience with cloud-like isolation.
- For a solo user already paying for Claude Max, Routines plus Desktop tasks plus Channels have near-zero marginal cost, because usage counts against the subscription. Most alternatives add a second bill.

### Gaps
- No independent reliability benchmarks (uptime, task success rate over weeks) for any always-on agent were found. Evidence is anecdotal.
- No verified official 2026 price sheets were fetched for Devin, Jules, ChatGPT agent, Zapier Agents or Lindy.
- No security audits or CVE lists were found for nanobot, ZeroClaw, PicoClaw or IronClaw.

## What patterns do power users recommend for making Claude itself more autonomous?

### Takeaway
The established pattern is a layered stack: headless `claude -p` or the Agent SDK driven by cron, launchd or GitHub Actions (with `--allowedTools`, `--max-turns` and `--max-budget-usd` caps); Desktop scheduled tasks or Routines for durable schedules; Channels (Telegram, Discord, iMessage) for a chat interface to a persistent local session; MCP connectors for reach; and flat-Markdown memory files. Alternatively, Claude can serve as the brain inside NanoClaw or OpenClaw/Hermes. The live risk is Anthropic's billing policy for Agent SDK and `claude -p` use under subscriptions, which has changed several times in 2026.

### Cited Findings
- Cron plus headless pattern: run `claude -p` with scoped tools (`--allowedTools`), a turn cap (`--max-turns`) and a budget cap (`--max-budget-usd`), logging output to a file. — [wmedia.es "Claude Code Can Work While You Sleep"](https://wmedia.es/en/tips/claude-code-headless-mode-autonomous-agent)
- An always-on Mac Mini M4 running Claude Code publishes content, manages files and runs scheduled tasks. It uses an external scheduler (Make.com webhooks on cron) and keeps memory in flat Markdown files. The author reports that autonomous operation burns through usage limits faster than interactive use. — [DEV Community (clawlabs)](https://dev.to/clawlabs/how-to-run-claude-code-as-an-autonomous-agent-on-a-mac-mini-52n8)
- Open-source helpers:
  - `agent-cron` runs Claude Agent SDK tasks on a cron schedule, with tasks defined as `.md` files. It needs an API key.
  - An hourly HN digest project runs Claude Code on cron and emails the result.
  — [GitHub T0UGH/agent-cron](https://github.com/T0UGH/agent-cron); [GitHub hacker-news-agent](https://github.com/wjcwjc77/hacker-news-agent)
- Official pattern, from Anthropic's docs: use Routines for "work that should run reliably without your machine," Desktop tasks when you need local files, `/loop` for quick polling, Channels to react to pushed events (CI failures, chat), and `/goal` to keep working turn after turn toward a condition. Persistent sessions can be backgrounded to keep `/loop` tasks running without a terminal. — [Claude Code docs: scheduled tasks](https://code.claude.com/docs/en/scheduled-tasks); [Claude Code docs: channels](https://code.claude.com/docs/en/channels)
- Other official patterns:
  - Use `loop.md` as a standing "heartbeat" instruction file, editable live.
  - Use GitHub Actions with a `schedule` trigger for CI-based cron.
  - Use Routine API triggers from monitoring or alerting tools (Sentry, deploy pipelines).
  — [Claude Code docs: scheduled tasks](https://code.claude.com/docs/en/scheduled-tasks); [Claude Code docs: routines](https://code.claude.com/docs/en/routines)
- For unattended Channels use, permission prompts pause the session unless the channel supports permission relay to your phone, or you use `--dangerously-skip-permissions` in a trusted environment. With `-p`, interactive tools are disabled so the session never stalls. — [Claude Code docs: channels](https://code.claude.com/docs/en/channels)
- **Billing policy for Agent SDK and `claude -p` (critical for "Claude as brain" setups):**
  - May 13, 2026: Anthropic announced that from June 15, 2026, Agent SDK and `claude -p` usage would move off subscription limits into a separate monthly credit ($20/$100/$200 by plan) metered at API rates. One analysis calls this a 12x–175x effective price increase depending on workload.
  - Anthropic paused the change on the day it was due to take effect.
  - The support article says that for now nothing has changed. An October 7, 2026 note (seen only as a search snippet) says Max and Team plans now include monthly API credits covering the Agent SDK and `claude -p`, and that you can still use them and third-party apps with subscription limits.
  — [The New Stack](https://thenewstack.io/anthropic-pauses-claude-agent-sdk-subscription-change/); [GitHub gist analysis](https://gist.github.com/MagnaCapax/d9177e35b355853f03c730dfcaa693ef); [Claude support](https://support.claude.com/en/articles/15036540-use-the-claude-agent-sdk-with-your-claude-plan); [digitalapplied](https://www.digitalapplied.com/blog/anthropic-claude-credit-overhaul-june-15-2026)
- Related report: Anthropic is to lift its ban on third-party agents using subscriptions, with monthly usage caps, starting June 2026. This bears on running Claude inside OpenClaw/Hermes on a subscription. — [KuCoin news flash](https://www.kucoin.com/news/flash/anthropic-unbans-third-party-agents-with-monthly-usage-caps-starting-june-2026) (low-quality source; verify)
- HN sentiment is mixed and wary. Commenters see the credit plan as "sneaking in taking the Claude Agent SDK (claude -p) off of subscription," note that Anthropic "backpedaled after huge backlash," and are unsure whether personal use of the Agent SDK inside a third-party harness is allowed. — [HN 49997143](https://news.ycombinator.com/item?id=49997143); [HN 48125552](https://news.ycombinator.com/item?id=48125552)
- Claude as brain in a Claw-family agent: NanoClaw is natively built on the Claude Agent SDK. — [The Register](https://www.theregister.com/2026/03/01/nanoclaw_container_openclaw/)

### Inferences
- The recommended decision split, assembled from the official docs:
  - **Cloud Routines** suit repo- and connector-centric jobs (PR triage, digests, alert triage). They need no machine and are the safest.
  - **Desktop scheduled tasks** suit local-file jobs.
  - **Channels on a persistent session** (tmux, launchd or a background process on a Mac Mini) give a chat-driven assistant.
  - **NanoClaw** or OpenClaw/Hermes add multi-channel breadth plus long-term memory and a heartbeat beyond what Claude Code offers natively.
- Because billing for `claude -p` and the Agent SDK on subscriptions has changed several times in 2026, any always-on design that relies on a subscription rather than API keys should be rechecked against the current support article before you commit to it.

### Gaps
- No direct Reddit threads (r/ClaudeAI, r/selfhosted, r/LocalLLaMA, r/AI_Agents) were returned by search, and Reddit and HN pages could not be fetched. Community sentiment here comes from HN snippets and blog posts only.
- No YouTube comparison videos or transcripts were retrieved.
- Claude Code hooks (e.g. Stop or SessionStart hooks to chain autonomous work) as a power-user pattern were not covered by sources fetched in this pass.
- The exact wording of the October 7, 2026 support-page update was not confirmed from a full page fetch.
