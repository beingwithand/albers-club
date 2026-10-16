# AI Computer-Use / Phone-Use Agents and Browser Automation for Personal Data Retrieval (as of Oct 2026)

Note on method: researched 2026-10-16 using web search. Several primary pages (brave.com, yutori.com, android-developers.googleblog.com, retail-insight-network.com) could not be fetched from the research environment because of DNS failures, so some findings rely on search snippets and secondary coverage. These are flagged. Several 2026 leaderboard rows name models (e.g. "Claude Fable 5", "Claude Mythos 5", "Claude Opus 4.8", "Qwen3.8 Max", "GPT-5.4") that come only from third-party aggregators. I could not verify them against vendor pages, so treat them as unverified.

## Computer-use agents: products, open-source frameworks, and benchmark scores (2025-2026)

### Takeaway
On OSWorld-style desktop tasks, frontier agents now reportedly score about 85-86%, above the roughly 72% human baseline. Browser agents score about 65-90% on web benchmarks, though the methods vary from one leaderboard to the next. The product landscape is still changing quickly. OpenAI shut down its standalone Atlas browser in August 2026 and folded it into the ChatGPT desktop app. Claude for Chrome, Gemini in Chrome, Comet and Copilot in Edge/Windows remain the main consumer agents. Benchmark success does not mean a run will work reliably on real, logged-in, bot-protected sites, and the security results below show this.

### Cited Findings
**Benchmarks**
- OSWorld-Verified: aggregators put the frontier at about 85-86% (Aug-Sep 2026). Yutori (updated 2026-08-07) lists an "Intelligence-Indeed Agent" at 90.2% on the full board and a top general model at 86.0%. Other aggregators list Qwen3.8 Max at 86.1%, with Anthropic models at about 85%. These sources conflict, and they mix self-reported rows with independently verified rows — [Yutori leaderboard](https://yutori.com/leaderboards/osworld-verified.md); [BenchLM OSWorld-Verified](https://www.benchlm.ai/benchmarks/osworld-verified); [Steel leaderboard](https://leaderboard.steel.dev/leaderboards/osworld/); [LLM Reference](https://www.llmreference.com/benchmark/osworld-verified)
- BenchLM (dated 2026-07-23) ranks "Claude Opus 4.8" at 85.2, "GPT-5.4" at 79.2 and "Claude Opus 4.6" at 76.9 for computer use (unverified model names) — [BenchLM computer use](https://www.benchlm.ai/best/computer-use)
- The OSWorld human baseline is about 72%. An a16z analysis (June 2026 data) says the best agents score about 85%, above humans on the same tasks — [a16z](https://a16z.com/can-agents-use-a-computer-yet-weve-got-the-data/)
- Agent S3 (Simular, open-source framework): 66% on OSWorld alone (100 steps), and 72.6% with Behavior Best-of-N, which its authors say is the first result above human level. arXiv 2510.02250 (late 2025) — [gui-agents PyPI / README](https://pypi.org/project/gui-agents)
- UI-TARS-2 (ByteDance Seed, arXiv 2509.02544, Sept 2025): 47.5% on OSWorld. The original UI-TARS (Jan 2025) was an open-weights native GUI agent — [Codesota UI-TARS-2](https://codesota.com/model/ui-tars-2); [UI-TARS paper](https://huggingface.co/papers/2501.12326)
- Gemini 2.5 Computer Use (Oct 2025, preview via Gemini API / Vertex AI; browser-focused): 65.7% on Online-Mind2Web in Browserbase's harness, against 61.0% for Claude Sonnet 4 and 44.3% for the OpenAI agent. Google cites the lowest latency. Earlier versions powered Project Mariner and AI Mode — [Google blog](https://blog.google/technology/google-deepmind/gemini-computer-use-model/); [VentureBeat](https://venturebeat.com/ai/googles-ai-can-now-surf-the-web-for-you-click-on-buttons-and-fill-out-forms); [InfoQ](https://www.infoq.com/news/2025/10/gemini-computer-use)
- WebVoyager: Browser Use reports 89.1% (with Claude) and Skyvern reports 85.8%. Both figures are vendor-reported, and reviewers warn they are not measured comparably — [Massive comparison](https://www.joinmassive.com/blog/browser-use-vs-stagehand-vs-skyvern-choosing-an-agent-browser-framework); [DevToolLab](https://devtoollab.com/blog/best-ai-browser-automation-tools)

**Products**
- Claude for Chrome launched as a research preview in Aug 2025. Anthropic said its defenses cut prompt-injection success from 23.6% to 11.2%. By Nov 24, 2025, with Opus 4.5, it had moved to beta for all Max users. Anthropic cites about 1% attack success against an adaptive Best-of-N attacker (100 attempts per environment) and calls that "meaningful risk" — [TechCrunch](https://techcrunch.com/2025/08/26/anthropic-launches-a-claude-ai-agent-that-lives-in-chrome/); [Simon Willison](https://feeds.simonwillison.net/2025/Aug/26/piloting-claude-for-chrome); [Anthropic prompt-injection defenses](https://www.anthropic.com/research/prompt-injection-defenses)
- OpenAI: ChatGPT Atlas (launched Oct 2025) offered agent mode and a "logged-out mode" that keeps the agent away from the user's authenticated sessions. In July 2026 OpenAI announced that Atlas would be discontinued, with a target date of 2026-08-09 (one source says Aug 13). Its features moved into the ChatGPT desktop app, which has a built-in browser, password management and autofill. OpenAI has not committed to security updates after shutdown — [Gigazine](https://gigazine.net/gsc_news/en/20260710-openai-chatgpt-atlas-end/); [BGR](https://bgr.com/2212396/openai-chatgpt-browser-atlas-discontinued/); [Wikipedia](https://en.wikipedia.org/wiki/ChatGPT_Atlas); [Simon Willison on OpenAI CISO](https://simonwillison.net/2025/Oct/22/openai-ciso-on-atlas/)
- Microsoft Copilot Actions on Windows (preview from Oct 2025): off by default and turned on under Settings > System > AI components > Agent tools. Agents run in a separate "agent workspace" under their own standard Windows account, can reach only known folders (Documents, Downloads, etc.) without further authorization, and must be digitally signed so they can be revoked. Edge's Copilot uses open tabs, cookies and site permissions. Its "Balanced" mode asks before acting on sites the user visits less often — [Microsoft Learn: agentic security](https://learn.microsoft.com/en-us/windows/security/book/operating-system-agentic-security); [Windows blog, 2025-10-16](https://blogs.windows.com/windowsexperience/2025/10/16/securing-ai-agents-on-windows/); [TheWindowsClub](https://www.thewindowsclub.com/enable-disable-use-copilot-actions-in-windows)
- Open-source frameworks:
  - Browser Use makes one LLM call per action, at about 2-5 s per action and about $0.02-$0.30 per task.
  - Stagehand (MIT, built on Playwright) calls the LLM only from its act/extract/observe methods. v3 (Feb 2026) added action caching, so repeat runs skip the LLM.
  - Skyvern is vision-based. Its cloud plan charges per step: 50 free steps, then $0.05 per step overage.
  — [Skyvern blog: Browser Use vs Stagehand](https://www.skyvern.com/blog/browser-use-vs-stagehand-which-is-better/); [Noqta](https://noqta.tn/blog/ai-browser-agents-browser-use-stagehand-web-automation-2026); [Massive](https://www.joinmassive.com/blog/browser-use-vs-stagehand-vs-skyvern-choosing-an-agent-browser-framework)

### Inferences
- For a data-export app, the hard part is no longer the agent's raw ability to click through a known export flow. The constraints are security, logged-in session handling, and bot and legal friction.
- Consumer agent products churn a lot: Atlas lasted about 10 months. An app should not depend on any single vendor's agent browser. Build on an abstraction such as Playwright/CDP plus a pluggable model.
- Self-reported leaderboard numbers vary by ±5-10 points. Compare models on a private evaluation of the actual export flows (Google Takeout, Meta "Download your information", Amazon "Request my data", etc.).

### Gaps
- I could not confirm the official OSWorld-Verified leaderboard (os-world.github.io) directly, and I could not confirm the 2026 model names.
- No primary data on Perplexity Comet's or Gemini in Chrome's agent benchmark scores in 2026. No current status for Project Mariner (it may have been merged into Gemini in Chrome / Gemini Agent; unverified).
- Nanobrowser and OpenInterpreter: no 2026 data gathered.
- WebArena 2026 SOTA was not retrieved.

## Phone agents: Android and iOS

### Takeaway
Android is the more open platform. It has structured AppFunctions (Android 16+, MCP-like, on-device) plus Gemini's UI automation, and open-source AccessibilityService/ADB agents (DroidRun, Minitap mobile-use) report near-saturated AndroidWorld scores. iOS allows no general UI-driving agent without a jailbreak. Automation is limited to App Intents, Shortcuts and Apple's own Siri/Apple Intelligence, and the rollout of third-party in-app actions in 2026 is reported inconsistently.

### Cited Findings
- AndroidWorld (Google, ICLR 2025): at launch the best agent completed 30.6% of tasks — [ICLR 2025](https://iclr.cc/virtual/2025/poster/28677); [Google Research](https://research.google/pubs/androidworld-an-open-world-for-autonomous-agents/)
- 2026 AndroidWorld scores conflict. Minitap claims 100% for its mobile-use agent (self-reported). One aggregator shows 97.4% pass@1 without naming a model. BenchLM (2026-07-29) lists Qwen3.7 Plus at 81.0% and Holo3.1-35B-A3B at 79.3%, and a later BenchLM page lists Qwen3.8-Omni-Flash at 87.1% — [Minitap](https://minitap.ai/benchmark); [BenchLM](https://benchlm.ai/benchmarks/androidworld); [benchmarklist](https://benchmarklist.com/benchmarks/androidworld/)
- DroidRun (open source, raised $2.1M) claimed the top AndroidWorld ranking in 2025. In an independent AIMultiple test of 65 real-world tasks, it had the highest success rate of the agents tested (43%), but at a high cost per task — [Vestbee](https://vestbee.com/insights/articles/droidrun-secures-2-1-m); [AIMultiple](https://research.aimultiple.com/mobile-ai-agent)
- Android AppFunctions is a platform API plus Jetpack library. Apps expose functions as tools for agents, and Google compares it to MCP, except that the functions run locally on the device. Callers need the EXECUTE_APP_FUNCTIONS permission. It targets Android 16+. Google's Feb 2026 post used Samsung Gallery on the Galaxy S26 with Gemini as its showcase. As of May 2026 the Gemini integration was in private preview with trusted testers. One secondary source says Gemini task automation grew to more than 40 apps (unverified) — [Android Developers Blog, Feb 2026](https://android-developers.googleblog.com/2026/02/the-intelligent-os-making-ai-agents.html); [9to5Google](https://9to5google.com/2026/02/25/android-appfunctions-gemini/); [DEV](https://dev.to/mr_manushukla/make-your-android-app-agent-ready-in-2026-appfunctions-app-actions-and-geminis-40-app-wave-22a6)
- iOS: the delayed Siri upgrade was built on personal context, in-app and cross-app actions via App Intents, and on-screen awareness, with a target of iOS 26.4 (spring 2026). Reports conflict. One says it shipped in March 2026 but most intents worked only with Apple's own apps. Another says 26.4 was partial and the substantive upgrade was expected in 26.5 (around May 2026) — [9to5Mac](https://9to5mac.com/2026/02/08/ios-26-4-heres-when-apple-will-release-the-first-beta/); [Macworld](https://www.macworld.com/article/2958711/apple-confirms-its-next-gen-siri-is-on-track-to-launch-in-2026.html); [PlainAI](https://plainai.aguidetocloud.com/changes/apple-intelligence-siri-shipped/)

### Inferences
- On Android, a third-party data-reclamation app could drive other apps through an AccessibilityService or ADB (as DroidRun and mobile-use do). Google Play restricts AccessibilityService use, which is a policy risk I did not verify in this research. AppFunctions only helps if the target app (e.g. Instagram) exposes an export function, which is unlikely.
- On iOS, the realistic paths are: (a) guide the user through each service's export flow manually or with Shortcuts, or (b) run the agent in a cloud or desktop browser and not on the phone itself. Most data-export flows also exist on the web, so a web-first design avoids the phone-platform limits.

### Gaps
- Google Play's 2026 policy on AccessibilityService for AI agents was not researched.
- Gemini's on-device "computer use for Android" screen-automation feature: its details and safety controls (confirmations, live view) could not be fetched.
- Apple's official iOS 26.x release notes on third-party App Intents with Siri were not verified.

## Deterministic automation vs AI agents: cost, reliability, local models

### Takeaway
The consensus pattern is a hybrid. Ordinary Playwright scripts handle stable, known flows. An LLM is called only to find fragile elements or to recover from errors, and successful actions are cached so repeat runs cost almost nothing. A full agent loop that calls the LLM on every step is better kept for discovering new flows. Open models (UI-TARS, Qwen-VL family, Holo) can run locally for privacy, but they trail frontier models on OSWorld.

### Cited Findings
- The Stagehand guidance is to keep most logic in Playwright code. One source estimates about 90% of automation stays plain Playwright. Inference runs only when AI methods are invoked or a cached action fails — [Noqta](https://noqta.tn/blog/ai-browser-agents-browser-use-stagehand-web-automation-2026); [Skyvern blog](https://www.skyvern.com/blog/browser-use-alternatives/)
- Stagehand v3 (Feb 2026) caches action mappings locally, which reportedly brings the cost per action close to zero after the first run — [Noqta](https://noqta.tn/blog/ai-browser-agents-browser-use-stagehand-web-automation-2026)
- Browser Use with an LLM on every step costs about $0.02-$0.30 per task at 2-5 s per action. Skyvern estimates about $0.50 for a 10-step task on its cloud — [Massive](https://www.joinmassive.com/blog/browser-use-vs-stagehand-vs-skyvern-choosing-an-agent-browser-framework)
- There are two perception approaches: DOM/accessibility tree (Browser Use, Stagehand) and vision (Skyvern, UI-TARS, Claude/Gemini computer use) — [Massive](https://www.joinmassive.com/blog/browser-use-vs-stagehand-vs-skyvern-choosing-an-agent-browser-framework)
- Open/local options: UI-TARS-2 scores 47.5% on OSWorld. Holo3.1-4B, a small model, reportedly scores 71% on AndroidWorld (aggregator) — [Codesota](https://codesota.com/model/ui-tars-2); [BenchLM](https://benchlm.ai/benchmarks/androidworld)

### Inferences
- Recommended architecture for a data-reclamation app:
  - Maintain a per-service "recipe" (deterministic Playwright steps for login detection, the navigation path to the export page, the request button, and polling the email or notification for "export ready").
  - When a recipe step fails because of UI drift, fall back to an LLM call on the scrubbed DOM or screenshot.
  - Record and promote the corrected step. This keeps steady-state cost low (likely cents or less per run), makes behavior auditable, and lowers prompt-injection exposure because the LLM sees less untrusted content.
- Local models are a reasonable choice for a privacy-first fallback on a narrow set of known export flows. Frontier cloud models are better for discovering new flows, ideally on scrubbed inputs.

### Gaps
- I found no independent, like-for-like study of the cost and success rates of agents against scripts on personal data-export flows specifically.

## Safety: prompt injection, credentials, sandboxing, audit

### Takeaway
Indirect prompt injection remains unsolved across every major agentic browser. Zenity's "PleaseFix" zero-click chains (Black Hat USA, Aug 5, 2026) hijacked Claude in Chrome, Gemini in Chrome, Comet, Atlas and Copilot Edge through an email, a calendar invite or a web page. OpenAI says the problem may never be fully solved, and Anthropic's best published number is about 1% attack success against adaptive attackers. An agent acting on a user's accounts has to be designed so that a hijacked model cannot do much harm.

### Cited Findings
- Zenity Labs' "PleaseFix" research (Black Hat USA 2026, Aug 5) used zero-click exploit chains against Claude in Chrome, Gemini in Chrome, Perplexity Comet, ChatGPT Atlas and Copilot Edge. Hidden instructions in ordinary content (an email, a calendar invite, a web page) were treated as the user's own intent ("Intent Collision"). Reported impacts ranged from data theft and account takeover to remote machine control. In Claude in Chrome, the built-in javascript_tool was turned into a way to run arbitrary JavaScript on any site. Full machine takeover was claimed on Comet, Gemini in Chrome and Edge. Some vendors patched and others called the behavior intended — [BusinessWire press release](https://www.businesswire.com/news/home/20260805803998/en/); [Dark Reading](https://darkreading.com/cyber-risk/ai-browsers-zero-click-agent-hijacking); [Zenity blog](https://zenity.io/blog/ai-agent-security-black-hat-recap); [Notebookcheck](https://www.notebookcheck.net/Claude-Gemini-Comet-five-AI-browsers-hijacked-by-a-single-email.1362568.0.html)
- Zenity first showed the flaw on Comet in March 2026. WIRED reported more than a dozen Atlas flaws, including an unauthorized Amazon purchase induced through Atlas — [Let's Data Science](https://letsdatascience.com/news/zenity-researchers-identify-agentic-browser-exploit-chains-4d70ee31)
- Brave (2025) showed injections hidden in screenshots, using faint text that people cannot see but OCR or the vision model reads, against Comet and other agentic browsers. Reported Oct 2025, and Perplexity said it was fixed (snippet only; brave.com could not be fetched) — [Brave blog](https://brave.com/blog/unseeable-prompt-injections/); [Shivan Kaul Sahib](https://shivankaul.com/blog/prompt-injections-in-agentic-browsers)
- An Aug 2026 analysis says Atlas, Comet, Dia and Edge Copilot remain vulnerable to indirect injection after several rounds of guardrails — [Security Arsenal](https://securityarsenal.com/blog/ai-browser-prompt-injection-why-openai-atlas-perplexity-comet-and-copilot-still-leak-and-how-to-defend-your-enterprise)
- OpenAI shipped an adversarially trained Atlas update with an automated RL attacker (Dec 2025) and said prompt injection is unlikely ever to be fully solved. Logged-out mode separates untrusted browsing from authenticated accounts — [Folio3](https://www.folio3.ai/ai-pulse/openai-fortifies-chatgpt-atlas-against-cyber-threats); [IndiaNIC Signal](https://signal.indianic.com/openai-hardens-atlas-browser-security-as-prompt-injection-threats-persist/); [Zenity: Hardening Atlas](https://labs.zenity.io/p/hardening-atlas-the-relentless-challenge-of-securing-an-untrusted-browser-agent)
- Anthropic's defenses are RL training against injections, classifiers that scan all untrusted content for hidden text, manipulated images and deceptive UI, and continuous red teaming. Attack success is about 1% against a Best-of-N adaptive attacker, still "meaningful risk" (Nov 2025) — [Anthropic](https://www.anthropic.com/research/prompt-injection-defenses)
- Simon Willison argues it is unreasonable to expect end users to judge these risks for themselves — [Simon Willison](https://feeds.simonwillison.net/2025/Aug/26/piloting-claude-for-chrome)
- Microsoft's OS-level model: a separate agent account, an isolated agent desktop, folder-scoped access, signed and revocable agents, and off by default — [Microsoft Learn](https://learn.microsoft.com/en-us/windows/security/book/operating-system-agentic-security)

### Inferences
Design rules for a consent-based data-retrieval agent:
1. **Never give passwords or TOTP seeds to the LLM.** Let the user log in themselves in a visible browser or webview, using passkeys, the password manager and 2FA. The agent then reuses that session's cookies in a dedicated, isolated browser profile. The model only ever sees redacted DOM or screenshots. Pause for human-in-the-loop on any re-authentication or CAPTCHA.
2. **Separate profiles per task.** Keep the agent's profile apart from the user's everyday browser, one site per profile where practical. This is the same principle as Atlas's logged-out mode and the Windows agent workspace.
3. **Allowlist navigation.** Restrict the agent to the domains in the recipe (for example, takeout.google.com and accounts.google.com only). Block email compose, payments, settings changes and deletion actions at the tool layer, not just in the prompt.
4. **Minimize untrusted content in context.** Deterministic recipes mean the LLM reads less arbitrary web content. Never let the agent read the user's inbox broadly; search only for the specific "export ready" message from a known sender.
5. **Turn off dangerous tools.** No arbitrary JavaScript evaluation tool (the Claude in Chrome javascript_tool was the PleaseFix vector) and no shell.
6. **Confirm irreversible actions.** Require explicit confirmation for anything that is not read-only or the export request itself.
7. **Keep an audit log.** Log each action with screenshots, URL and timestamp. Store downloads encrypted locally, and give the user a replay view.
8. **Run locally.** Prefer local or on-device execution so session cookies never leave the device. If a cloud browser is used, treat its cookie store as highly sensitive.

### Gaps
- Zenity's technical write-ups and per-vendor patch status (as of Oct 2026) were not read directly.
- No primary OpenAI page on agent "watch mode" or confirmation policy in the ChatGPT desktop app after Atlas.
- Guardio and LayerX 2025-2026 reports were not retrieved in this pass. Guardio's "Scamlexity" research on Comet (Aug 2025) is known from secondary memory only and is not cited here.

## Platform pushback: bot detection, ToS, legal, and agent identity standards

### Takeaway
The law has moved toward allowing user-authorized agents. The Ninth Circuit (Aug 2026) vacated Amazon's preliminary injunction against Perplexity Comet, reasoning that the agent acts on the user's behalf. Earlier, Van Buren, hiQ and Meta v. Bright Data narrowed the CFAA and contract theories. Platforms still enforce ToS and detect bots, so accounts can be locked or banned. The industry answer is cryptographic agent identity: Web Bot Auth, based on RFC 9421 HTTP Message Signatures, with Cloudflare "signed agents" in production and AWS WAF support. Disguising an agent as a human Chrome user is the behavior that triggered the Amazon suit and Cloudflare's delisting of Perplexity.

### Cited Findings
- Van Buren v. US (2021): the Supreme Court read the CFAA's "exceeds authorized access" narrowly, as a "gates-up-or-down" inquiry — [Farella Braun + Martel on hiQ](https://www.fbm.com/raven-quesenberry/publications/what-recent-rulings-in-hiq-v-linkedin-and-other-cases-say-about-the-legality-of-data-scraping/)
- hiQ v. LinkedIn (9th Cir. 2022): scraping publicly available data is not "without authorization" under the CFAA (older, 2022) — [Morgan Lewis](https://www.morganlewis.com/blogs/sourcingatmorganlewis/2022/04/data-scraping-deemed-legal-in-certain-circumstances)
- Meta v. Bright Data (N.D. Cal., Jan 2024): summary judgment for Bright Data. Logged-off scraping of public data did not breach Meta's terms, and only a tortious-interference claim remained. This turned on being logged off; logged-in access binds the user to the ToS — [Farella Braun + Martel](https://www.fbm.com/technology/publications/major-decision-affects-law-of-scraping-and-online-data-collection-meta-platforms-v-bright-data/)
- Amazon v. Perplexity:
  - Nov 2025: Amazon sued under the CFAA and California's computer access law (Penal Code 502), alleging that Comet disguised its agent as ordinary Chrome to get past blocks.
  - 2026-03-06: Judge Maxine Chesney granted a preliminary injunction barring Comet from password-protected Amazon accounts.
  - Reported 2026-08-05: a Ninth Circuit panel vacated the injunction, finding Amazon unlikely to succeed on the CFAA and state claims because the agent acts on the user's behalf. The ruling is limited to the current record and sets no broad rule. The case returned to the district court.
  - Sources are news reports; I did not read the opinion.
  — [Gigazine](https://gigazine.net/gsc_news/en/20260311-amazon-win-court-perplexity-comet); [SentiSense](https://app.sentisense.ai/stories/amazon-gets-relief-from-perplexitys-ai-03132026); [Retail Insight Network](https://www.retail-insight-network.com/news/us-court-overturns-amazon-injunction-perplexity/); [Law360](https://law360.com/articles/2468857)
- Cloudflare vs Perplexity (Aug 2025): Cloudflare accused Perplexity of "stealth crawling". It said Perplexity rotated to unlisted IPs and ASNs and spoofed a Chrome 124 on macOS user agent when blocked. Cloudflare removed Perplexity from its Verified Bots program and added blocking. Perplexity disputed this and blamed BrowserBase traffic — [Decrypt](https://decrypt.co/333479/cloudflare-perplexity-ai-stealth-crawlers-website-blocks?amp=1); [Search Engine Journal](https://www.searchenginejournal.com/cloudflare-delists-and-blocks-perplexity-from-crawling-websites/552899/)
- Web Bot Auth:
  - The operator publishes an Ed25519 public key at a well-known HTTPS directory and signs each request using RFC 9421 HTTP Message Signatures.
  - Cloudflare added signatures to Verified Bots on 2025-07-01, the same day it began blocking AI crawlers by default for new domains.
  - Cloudflare and Browserbase launched it for agents. A registry format followed on 2025-10-30, built with Amazon Bedrock AgentCore. AWS WAF added support on 2025-11-21.
  - Reported adopters include Anthropic, OpenAI, Perplexity, Vercel, Shopify and Visa.
  - It is still an IETF draft, and sources disagree on its working-group status. Google says not all of its agents sign requests and recommends keeping IP and reverse-DNS checks.
  - Sources are mostly secondary.
  — [Crawlbase](https://crawlbase.com/blog/web-bot-auth-signed-agents/); [Stellagent](https://stellagent.ai/insights/web-bot-auth-cloudflare-ietf); [CXO Digital Pulse](https://www.cxodigitalpulse.com/cloudflare-and-browserbase-launch-web-bot-auth-to-verify-ai-agents/); [PPC Land](https://ppc.land/cloudflare-unveils-registry-format-for-bot-and-agent-authentication/); [Deepak Gupta guide](https://guptadeepak.com/guides/verify-an-ai-agent/)

### Inferences
- Legal posture for a personal data-retrieval agent: the user's own account, the user's own data, explicit consent, and acting at the user's direction. This is the strongest available position, consistent with the Ninth Circuit's Comet reasoning and the "gates" framing in Van Buren. Contract (ToS) claims and account-level enforcement remain the main practical risk. Courts have not settled logged-in agent use (Bright Data was a logged-off case).
- The regulatory tailwind is that GDPR Art. 15/20 and CCPA access and portability rights mean most large platforms already provide official export tools. The agent should only drive those official flows (Takeout, DYI, etc.) at human-like rates, from the user's own IP and device, not scrape whole sites. That reduces both detection and legal exposure.
- Do not spoof. Run in the user's real browser, or an honestly identified, signed agent (Web Bot Auth) if running from the cloud. Cloud datacenter IPs plus headless fingerprints are the profile most likely to trip Cloudflare and Google defenses and lead to locks.
- Prefer official APIs and data-portability endpoints where they exist (e.g. Google Data Portability API, the DTI/Data Transfer Project). Use UI agents only as a fallback.

### Gaps
- Primary text of the Ninth Circuit's Amazon v. Perplexity opinion; whether Amazon sought rehearing.
- Whether the Meta v. Bright Data appeal proceeded (Meta reportedly dropped it in 2024; not verified here).
- Specific documented cases of consumer accounts banned for personal-agent use in 2025-2026; none found in this pass.
- Google's own agent-identity scheme and how Google login treats agent-driven browsers in 2026; not researched.
