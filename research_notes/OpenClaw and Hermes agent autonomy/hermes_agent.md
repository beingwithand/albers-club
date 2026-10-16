# Hermes Agent (Nous Research): state of the art as of October 2026

Method note: these notes come from web search result summaries plus direct fetches of the GitHub repo and releases pages. Many third-party sites (Wikipedia, kilo.ai, composio.dev, mindstudio.ai, HN, CSA, the official docs site) could not be fetched directly because of DNS errors in the research environment. Claims from those sites are therefore taken from search-result snippets and should be spot-checked. No YouTube transcripts were retrieved, and no Reddit threads were surfaced directly. Reddit sentiment is reported secondhand through aggregator analyses.

## What Hermes Agent is and how it is built (architecture, models, hosting)

### Takeaway
Hermes Agent is an MIT-licensed, model-agnostic, self-hosted personal agent that Nous Research released in February 2026. Its differentiator is a built-in "learning loop": agent-curated memory, FTS5 session search, and skills it writes and patches itself. Around that it has a cron scheduler, a multi-platform messaging gateway, seven terminal/sandbox backends, and subagent delegation. By October 2026 it is a fast-moving project with roughly 254K GitHub stars and a desktop app (v0.22.x). Nous raised a $90M Series B for it on Oct 7, 2026.

### Cited Findings
**Identity and adoption**
- Open-source agent from Nous Research, released February 2026 (a forum post says Feb 25), MIT license. It runs autonomous multi-step tasks with local or remote LLMs. It is distinct from Nous's "Hermes 3/4" model weights. Nous says Hermes 4 models "are not recommended for use inside Hermes Agent" — [Wikipedia via search](https://en.wikipedia.org/wiki/Hermes_Agent); [Nous site](https://hermes-agent.nousresearch.com/)
- GitHub repo (fetched Oct 2026): tagline "The agent that grows with you"; 254k stars, 55.1k forks, ~54.5k commits on main, 5k+ issues and 5k+ PRs, MIT — [GitHub](https://github.com/NousResearch/hermes-agent)
- Star counts vary across sources: ~101K on one docs site, ~244.7K in one comparison, 254K on GitHub. OpenClaw is cited at ~346K–389.5K stars — [search summary of comparisons](https://www.mindstudio.ai/blog/hermes-agent-vs-openclaw-comparison); [GitHub](https://github.com/NousResearch/hermes-agent)
- Series B: $90M at a $1.5B valuation, announced Oct 7, 2026. Led by Robot Ventures, with NVIDIA, Microsoft M12, Samsung, YC, USV and Menlo participating. The money goes to Hermes Agent, a business-focused version and a planned mobile app. Coverage reports 24M+ downloads/clones since launch and ~$36M annualized revenue as of mid-September (one French report), with a target of >$100M by end of 2026. Total capital raised is ~$160M, following a $50M Series A led by Paradigm in April 2025 — [Crypto Briefing](https://cryptobriefing.com/nous-research-series-b-hermes-agent/); [AI Weekly FR](https://aiweekly.co/fr/alerts/nous-research-lve-90-m-en-srie-b-15-md-avec-nvidia-et-microsoft-m12-pour-hermes). Some Spanish coverage says $75M, apparently an earlier summer figure — [Trending Topics](https://www.trendingtopics.eu/nous-research-hermes-90-millionen/); [Ecosistema Startup](https://ecosistemastartup.com/nous-research-cierra-serie-b-de-us75m-y-lleva-hermes-a-empresas/)

**Architecture and features (per the GitHub README)**
- Interfaces: a terminal UI (multiline editing, slash-command autocomplete, interrupt-and-redirect, streaming tool output) and a desktop app for macOS, Windows and Linux.
- Messaging gateway: one process serves Telegram, Discord, Slack, WhatsApp, Signal, Email, CLI and Home Assistant, with voice memo transcription and cross-platform conversation continuity — [GitHub](https://github.com/NousResearch/hermes-agent)
- Memory: agent-curated memory with periodic "nudges" to save knowledge, kept in MEMORY.md and USER.md. FTS5 session search with LLM summarization gives recall across sessions. Honcho handles dialectic user modeling — [GitHub](https://github.com/NousResearch/hermes-agent). In v0.22.0 the memory providers (Honcho, Mem0 and others) moved into the plugin catalog — [Releases](https://github.com/NousResearch/hermes-agent/releases)
- Skills: the agent creates skills after complex tasks and improves them during use. They follow the agentskills.io open standard, and there is a Skills Hub — [GitHub](https://github.com/NousResearch/hermes-agent). Mechanism: after each finished session a background review agent creates or patches skills through a `skill_manage` tool. It prefers small patches over rewrites. Progressive disclosure keeps only skill names and summaries in the prompt — [Classmethod code reading](https://dev.classmethod.jp/en/articles/hermes-agent-self-improving-code-reading/); [akjamie deep dive](https://akjamie.github.io/post/2026-05-29-self-improvement-agent-deep-dive/)
- Curator: a "Curator" was added around v0.11–v0.14. It runs on a 7-day cron after 2h idle, consolidates and archives only agent-authored skills, and never touches bundled or hub skills. v0.16.0 reportedly shifted toward selecting and consolidating skills to fight bloat. These details come from single blog sources and are unverified against the docs — [clawsimple](https://clawsimple.com/en/blog/hermes-agent-updates-mid-may-2026); [search summary](https://fp8.co/articles/Inside-Hermes-Agent-Self-Improving-Skill-Memory)
- Scheduling: a built-in cron scheduler delivers results to any connected platform, for things like daily reports and nightly backups. Jobs can be created by describing them in chat — [GitHub](https://github.com/NousResearch/hermes-agent); [Daily Briefing tutorial](https://hermes-agent.nousresearch.com/docs/guides/daily-briefing-bot)
- Subagents: the agent spawns isolated subagents for parallel work. Python scripts can call tools via RPC, which "collapses multi-step pipelines into single turns." v0.22.1 added worker, delegation and ACP changes. A Kanban workflow (ticket modal, reviewer profiles, unified workflow definition) arrived in v0.21.x — [GitHub](https://github.com/NousResearch/hermes-agent); [Releases](https://github.com/NousResearch/hermes-agent/releases)
- Terminal backends (sandboxing): seven options: local, Docker, SSH, Singularity, Modal, Daytona and Vercel Sandbox. Daytona and Modal hibernate when idle and wake on demand. Security features are command approval, DM pairing and container isolation. There are 40+ tools plus MCP — [GitHub](https://github.com/NousResearch/hermes-agent)
- Research features: batch trajectory generation and trajectory compression for training tool-calling models. This ties the agent to Nous's model-training work — [GitHub](https://github.com/NousResearch/hermes-agent)

**Models**
- Providers: Nous Portal, OpenRouter, OpenAI, Anthropic, custom endpoints and others; switch with `hermes model`. Nous Portal offers 300+ models plus a "Tool Gateway" (web search, image generation, TTS, cloud browser) under one subscription, and bring-your-own keys still work — [GitHub](https://github.com/NousResearch/hermes-agent)
- v0.22.0 (Oct 13, 2026) added Claude 5.5 and GPT-6 support and one-click local models via llama.cpp. v0.21.5 added GPT-6 and Claude Opus 5.5 to the catalogs. v0.22.2 improved local-model turns on laptops — [Releases](https://github.com/NousResearch/hermes-agent/releases)
- Local models are commonly run through Ollama. One guide pairs Ollama with a web dashboard and Tailscale — [uxdev](https://uxdev.org/blog/self-hosting-hermes-ai-agent-on-a-mac-mini/)
- One comparison claims Hermes "works best with Hermes-series models due to function-calling fine-tuning." This conflicts with Nous's own statement that Hermes 4 is not recommended inside the agent — [comparison via search](https://www.mindstudio.ai/blog/hermes-agent-vs-openclaw-comparison); [Nous via search](https://hermes-agent.nousresearch.com/)

**Release cadence (recent)**
- v0.21.3 (Sep 14), v0.21.4 (Sep 21: gateway singleton lock, `skills.auto_load`), v0.21.5 (Sep 24: desktop plugin SDK, Connectors page replacing the MCP tab), v0.21.6 (Oct 8: dashboard auth hardening, email sender allowlist fix, Hermes Cloud build), v0.21.7 (Oct 11).
- v0.22.0 "The Threshold Release" (Oct 13): guided first-run setup chat, Linear/Notion connectors, stable SemVer channels, signed desktop packages and Microsoft Store builds, `hermes pm` package manager, a 600-entry plugin catalog, password-manager sign-in for the browser agent, and "Bot Screen" for watching or taking over a bot's desktop.
- v0.22.1 (Oct 14) shipped from the wrong commit. v0.22.2 (Oct 15) fixed the gateway failing to start after a reboot and has a known issue where 0.22.1 sessions can't be deleted — [Releases](https://github.com/NousResearch/hermes-agent/releases)
- A "Hermes Cloud" build and Docker image exist — [Releases](https://github.com/NousResearch/hermes-agent/releases); [Docker Hub](https://hub.docker.com/r/nousresearch/hermes-agent)

**Install and hosting**
- Install paths: a curl script (Linux/macOS/WSL2), PowerShell for native Windows, and a signed APT repository for Android/Termux (aarch64). Key commands are `hermes setup`, `hermes gateway`, `hermes update` and `hermes doctor` — [GitHub](https://github.com/NousResearch/hermes-agent)
- Mac Mini M4 guide (headless, 24/7): wired Ethernet, static IP, sleep disabled. Auto-login disables FileVault. Back up `~/.hermes/`, because "your ~/.hermes/ directory (skills + memory database) is your accrued value" — [janeyou/hermes-agent-101](https://github.com/janeyou/hermes-agent-101)
- A practitioner running a headless Mac Mini for about a month found that screen capture and UI automation break without a virtual display — [kdpisda.in via search](https://kdpisda.in/hermes-ai-agent-mac-mini/)
- Hosting cost comparison (vendor-influenced): a VPS is ~$10–30/mo versus ~$110–170/mo to rent a Mac mini. The Mac mini has the lowest-friction install, and a VPS avoids hardware upkeep — [VPSMAC](https://vpsmac.com/en/blog/hermes-agent-raspberry-pi-vps-mac-mini-comparison-20260528.html). An $8–12/mo VPS is enough if inference goes to an API — [prommer.net](https://prommer.net/en/tech/guides/mac-mini-ai-agent-server/)
- Home server or homelab: one user runs daily briefings from a local Kubernetes cluster — [use-case roundup via search](https://github.com/aliaihub/awesome-hermes-usecases)

### Inferences
- The project moves very quickly: several releases a week and thousands of PRs per patch rollup. Expect breakage between versions; v0.22.1 shipping from the wrong commit and the gateway-after-reboot bug are examples.
- In September and October 2026 the project shifted from a terminal tool for tinkerers toward a consumer and enterprise product: desktop app, Store builds, guided setup, Cloud, connectors, and a funded mobile app.

### Gaps
- I could not open the official docs pages directly, so details on memory limits and the exact skill-creation trigger (one source says ~5 tool calls) are unverified.
- I found no official figures on how many users self-host versus use Hermes Cloud.

## How autonomous it is in practice: use cases, user reports, limitations, cost, security

### Takeaway
The autonomy features are real and widely used, mostly for scheduled briefings, monitoring and alerts, inbox triage, PR summaries and personal knowledge management. In practice most setups are bounded cron jobs with chat delivery, not open-ended autonomy. The self-improving skills attract the most excitement and the most complaints: skill bloat, the agent overwriting hand-tuned skills, and heavy fixed token overhead of ~14–18K tokens per call. Security is the main concern. The skills system carries a persistent prompt-injection risk, several CVEs and scanner bypasses have been disclosed, and the agent was used with "YOLO mode" in a July 2026 intrusion on Thailand's Ministry of Finance.

### Cited Findings
**Real-world use cases**
- Daily briefings are the most-cited use. The official tutorial runs a job at 8am that searches the web, summarizes stories and sends them to Telegram or Discord, and the repo ships a Daily Briefing demo. Users describe weather and calendar summaries, portfolio snapshots, overnight GitHub issues, a cybersecurity/AI briefing from a local Kubernetes cluster, and PNG briefing cards via Telegram cron — [Daily Briefing tutorial](https://hermes-agent.nousresearch.com/docs/guides/daily-briefing-bot); [awesome-hermes-usecases](https://github.com/aliaihub/awesome-hermes-usecases); [Hostinger](https://www.hostinger.com/tutorials/hermes-agent-use-cases/)
- Monitoring: pinging services every 5 minutes and alerting on Telegram, price-drop watching, temp-file cleanup with summaries. Also a weekday 9am inbox classifier (needs-reply/FYI digest), repo polling with PR review summaries, and client research before calls — [openclawlaunch](https://openclawlaunch.com/guides/hermes-agent-use-cases); [fast.io](https://fast.io/resources/hermes-agent-use-cases/); [betterclaw](https://www.betterclaw.io/blog/hermes-agent-use-cases-2026)
- HN users: one runs Hermes as an orchestrator with a custom extractor on a cron-like schedule, "like having your own little DevOps" handling infrastructure fixes. Another uses it to organize notes in Obsidian. A third wrote "Hermes basically rules my personal life at this point" — [HN 48581502](https://news.ycombinator.com/item?id=48581502); [HN 47786673](https://news.ycombinator.com/item?id=47786673) (quotes from search snippets)
- Demo claim: co-founder Quesnelle showed the agent writing a 79,000-word novel autonomously across iterative sessions. This is a single vendor demonstration — [MEXC news](https://www.mexc.com/tr-CT/news/1004013)
- An X article claims "371 Hermes Agent use cases"; it is an influencer compilation and was not verified — [Julian Goldie on X](https://x.com/JulianGoldieSEO/article/2109330246369759240)

**How well autonomy works (user reports)**
- Skill bloat: as skills accumulate, "which skill should be used when becomes unclear." The Curator and v0.16 consolidation work were the response — [search summary of fp8/akjamie](https://fp8.co/articles/Inside-Hermes-Agent-Self-Improving-Skill-Memory)
- A Reddit and X complaint roundup's most-cited issue: when you hand-tune a skill, Hermes may later overwrite it while "improving" itself. Users also worry about storage growth and skills with flawed logic — [aiagentstore roundup](https://aiagentstore.ai/agentic-ai-and-workflow-automation/en/the-20-biggest-problems-with-hermes-agent-what-thousands-of-reddit-and-x-users-are-actually-struggling-with-ranked)
- GEPA-based skill optimization is human-initiated and gated behind PR review, so there is a person in the loop. Unattended skill creation is the default loop — [akjamie](https://akjamie.github.io/post/2026-05-29-self-improvement-agent-deep-dive/)
- HN criticism: the CLI is "janky, flickery" with a forced header; one commenter noted it "constantly (wants to) run from upstream master" (v0.21.7 later moved source installs to tagged releases); one alleged plagiarism issues. A container user said it "worked ok" but was "rough around the edges" and questioned the benefit when >10k of context went to listing skills — [HN 48419000](https://news.ycombinator.com/item?id=48419000); [HN 48586519](https://news.ycombinator.com/item?id=48586519); [Releases](https://github.com/NousResearch/hermes-agent/releases)
- Reliability bug example: v0.22.2 (Oct 15, 2026) fixed the gateway refusing to start after reboot under systemd, launchd or Docker. This bug directly affects always-on autonomy — [Releases](https://github.com/NousResearch/hermes-agent/releases)

**Costs**
- The framework is free (MIT), so cost is model API plus hosting — [TechJack](https://techjacksolutions.com/ai-tools/hermes/hermes-agent-cost-breakdown/)
- A trivial "who u?" prompt consumed 16K+ tokens because the full system prompt is rebuilt and resent each request (~16–18K input tokens per ping) — [GitHub #13983](https://github.com/NousResearch/hermes-agent/issues/13983)
- v0.6.0 analysis: ~73% of each call (~13.9K tokens) is fixed overhead, with ~8.8K from 31 tool definitions and the rest from the system prompt and skills catalog. Lazy-loading skills was proposed (~2.2K saved) — [GitHub #4379](https://github.com/NousResearch/hermes-agent/issues/4379) (older version; current overhead may differ)
- A third-party estimate puts CLI mode at ~6–8K tokens/turn and gateway mode at ~15–20K, so gateway runs 2–3x the cost. OpenClaw's narrower per-turn footprint can be cheaper for simple gateway use — [TechJack](https://techjacksolutions.com/ai-tools/hermes/hermes-agent-cost-breakdown/)
- Comparisons conflict on cost: one says Hermes has "lower running costs," while another cites community reports of expensive coding with Sonnet 4.5 because of token overhead — [comparisons via search](https://www.mindstudio.ai/blog/hermes-agent-vs-openclaw-comparison); [flowtivity](https://flowtivity.ai/blog/openclaw-vs-hermes-agent-comparison/)

**Security**
- Built-in safeguards: command approval, dangerous-pattern blocking, memory scanning for injections, DM pairing and container isolation. Hub skills pass a scanner, and dangerous ones are quarantined or hard-blocked. Community-tier warnings can be overridden with `--force` — [GitHub](https://github.com/NousResearch/hermes-agent); [Skills docs via search](https://hermes-agent.nousresearch.com/docs/user-guide/features/skills)
- CVE-2026-9353: injection in the Skills Guard handler, CVSS 3.1 7.3 (High); guard bypass and unauthorized execution — [CodeAnt](https://codeant.ai/vulnerability-database/cve-2026-9353)
- Issue #7072: Skills Guard bypassed via dynamic import and string construction, allowing silent env-var exfiltration. Anyone can publish to the Skills Hub — [GitHub #7072](https://github.com/NousResearch/hermes-agent/issues/7072)
- Issue #3968: the cron scanner checks only the user prompt, not skill content loaded at runtime, so a malicious skill can run commands in non-interactive cron mode without approval — [GitHub #3968](https://github.com/NousResearch/hermes-agent/issues/3968)
- Issue #8884: an unscanned DESCRIPTION.md lets skill-description prompt injection reach the system prompt — [GitHub #8884](https://github.com/NousResearch/hermes-agent/issues/8884)
- A Cloud Security Alliance note, "9 CVEs in 4 Days" (May 2026), says malicious community skills can persist across reboots and shape later sessions. Another article calls self-written skills a persistent prompt-injection vector protected only by regex filtering — [CSA](https://labs.cloudsecurityalliance.org/research/csa-research-note-hermes-agent-cves-20260504-csa-styled/); [Aurpay](https://aurpay.net/aurspace/hermes-agent-security-risks-crypto-2026/) (patch status unverified)
- Thai Ministry of Finance incident (July 9–13, 2026): an operator enabled "YOLO mode," which disables approvals. Hermes autonomously scanned hosts, ran LinPEAS, hunted for root and crawled personnel files dating to 2012. The human operator built target-specific wordlists. Exfiltration was not shown in the logs, and Thai CERT/NCSA were notified July 15. Coverage says this is misuse of a documented, sandbox-only feature, not a flaw in Hermes — [The Hacker News](https://thehackernews.com/2026/07/hacker-runs-hermes-ai-agent-unattended.html); [Hunt.io](https://hunt.io/blog/thailand-ministry-finance-targeted-with-hermes-ai-agent); [CSA](https://labs.cloudsecurityalliance.org/research/csa-research-note-hermes-ai-agent-thai-finance-ministry-2026/)
- v0.21.6 (Oct 8) shipped security fixes: dashboard auth hardening (rate limiting, audit log), git filter hardening and an email sender allowlist fix — [Releases](https://github.com/NousResearch/hermes-agent/releases)
- Community advice is to run it sandboxed, keep the dashboard on localhost or a tailnet, and never give an agent free rein — [uxdev](https://uxdev.org/blog/self-hosting-hermes-ai-agent-on-a-mac-mini/); [HN via search](https://news.ycombinator.com/item?id=48586519)

### Inferences
- The "self-scheduling" in practice is the agent creating cron jobs from natural-language requests and delivering results to chat. That is reliable enough for briefings and alerts. Open-ended unattended work is uncommon and is where the security risk sits: cron runs without approval, YOLO mode.
- The learning loop's value is plausible but not independently measured. Its main documented downsides are context and token overhead and loss of user control over skills.

### Gaps
- No rigorous independent evaluation shows that self-written skills improve outcomes over time. One arXiv paper reports a transfer result into Hermes (51.90%) but no user-outcome study — [arXiv 2606.08671](https://arxiv.org/pdf/2606.08671)
- I could not confirm whether CVE-2026-9353 and issues #3968, #7072 and #8884 are patched in v0.22.x.
- No YouTube transcripts and no first-hand Reddit threads were retrieved; Reddit sentiment comes from aggregators.
- I found no typical monthly API spend figure from real users.

## Positioning against OpenClaw: migration, comparisons, preferences

### Takeaway
The community frames the two as breadth versus depth. OpenClaw has the larger ecosystem (more stars, skills and channel integrations) and the faster Docker setup. Hermes wins on built-in learning, memory, recall and structured subagents, and it has a one-command migration path from OpenClaw. Sentiment is split: aggregated Reddit analysis shows many people staying with OpenClaw and a sizeable share running both. One HN view calls Hermes the more polished choice for less technical users, and OpenClaw the deeper one.

### Cited Findings
- Migration: `hermes claw migrate` (with `--dry-run`, `--preset user-data` for no secrets, and `--overwrite`) imports SOUL.md, memories, user skills, command allowlists, messaging settings, allowlisted API keys (Telegram, OpenRouter, OpenAI, Anthropic, ElevenLabs), TTS assets and AGENTS.md — [GitHub](https://github.com/NousResearch/hermes-agent)
- The memory pitch is that OpenClaw's cross-session memory needs manual setup and Hermes was built to close that gap. A claim that "many users have already made the move" is unsupported by data — [MEXC](https://www.mexc.com/tr-CT/news/1004013)
- Ecosystem: one comparison cites OpenClaw at 346K stars, 44K skills, 50+ platforms and enterprise support. Another cites OpenClaw at ~389.5K stars versus Hermes ~244.7K. For comparison, the Hermes Skills Hub lists ~672 skills (third party) and the v0.22 plugin catalog has 600 entries — [comparisons via search](https://composio.dev/content/openclaw-vs-hermes-agent); [fast.io](https://fast.io/resources/hermes-agent-skills-hub-marketplace/); [Releases](https://github.com/NousResearch/hermes-agent/releases)
- Memory: FTS5 session search with LLM summarization lets Hermes recall and synthesize past conversations "in ways OpenClaw's file-based memory doesn't match natively" — [comparison via search](https://www.mindstudio.ai/blog/hermes-agent-vs-openclaw-comparison)
- Setup: one guide estimates 2–4 hours for a full Hermes local setup versus under 30 minutes for OpenClaw via Docker Compose. This likely predates Hermes v0.22's guided desktop setup — [comparison via search](https://www.mindstudio.ai/blog/hermes-agent-vs-openclaw-comparison)
- Multi-agent: Hermes has the edge on structured parallel subagent delegation, while OpenClaw has "basic" multi-agent support. Another source says OpenClaw is better for sharing and supervising sessions and Hermes for persistent cooperating agents — [comparisons via search](https://composio.dev/content/openclaw-vs-hermes-agent)
- Community sentiment: an analysis of ~1,300 Reddit comments found ~35% "stick with OpenClaw despite its flaws" and ~20% use both — [Kilo](https://kilo.ai/openclaw/vs-hermes)
- Most users see the two as complementary; a common pattern runs Hermes as a high-level planner on top of OpenClaw tools — [MindStudio](https://www.mindstudio.ai/blog/what-is-hermes-agent-openclaw-alternative)
- HN: "My simple take: Hermes is for the less technical and is more polished. OpenClaw … deeper with more capabilities" — [HN 48586545](https://news.ycombinator.com/item?id=48586545)
- Cost: OpenClaw's narrower per-turn footprint can be cheaper for simple gateway setups, and Hermes's learning loop adds token overhead — [TechJack](https://techjacksolutions.com/ai-tools/hermes/hermes-agent-cost-breakdown/)
- Models: both are model-agnostic. OpenClaw works with any OpenAI-compatible API — [comparison via search](https://www.mindstudio.ai/blog/hermes-agent-vs-openclaw-comparison)
- Other comparisons (not fetched): [decodo](https://decodo.com/blog/hermes-agent-vs-openclaw), [nutstudio](https://www.nutstudio.ai/reviews/openclaw-vs-hermes-agent/), [flowtivity, updated June 2026](https://flowtivity.ai/blog/openclaw-vs-hermes-agent-comparison/), [getopenclaw (OpenClaw-affiliated)](https://www.getopenclaw.ai/blog/openclaw-vs-hermes-agent), [openclawvps](https://openclawvps.io/blog/hermes-agent-vs-openclaw)

### Inferences
- Rule of thumb from the sources: choose OpenClaw for fast setup, the broadest channel and skill ecosystem, and team supervision; choose Hermes for an agent that accumulates memory and skills over months. Running both is common.
- Both share the same core security problem: community skill marketplaces act as a persistent prompt-injection and supply-chain vector. None of the comparisons gave a well-sourced verdict on which is more secure. The Hermes-specific security evidence (CVEs, the Thai incident) is the more concrete set found here.
- Most comparison sites are vendors (hosting providers, agent platforms, OpenClaw-branded sites) with commercial interests, so their numbers should be treated as approximate.

### Gaps
- I could not fetch the Kilo analysis for its full methodology or the share preferring Hermes.
- I found no head-to-head reliability benchmark (uptime, task success) between the two.
- OpenClaw-specific security incidents for a side-by-side comparison are out of scope here and were not researched.
