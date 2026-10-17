# GrokBot and agents that scroll and analyze short-video feeds (as of Oct 17, 2026)

Method note: every page fetch (WebFetch and curl) was refused at the network layer (DNS failure / proxy CONNECT 403) except github.com. Findings below therefore come from search-engine result summaries of the cited pages plus one GitHub repo read locally. Treat numbers as "reported by the cited page" and re-verify against the primary page before quoting. See "Blocked sources" at the end of the last section.

## 0. Name resolution: what "GrokBot" means

### Takeaway
"GrokBot" almost certainly means **xAI's "Grok Bot"** (often written "Grokbot"), an early-beta agent product launched Aug 11, 2026. Each Bot works on a persistent cloud computer (browser + filesystem + terminal), built with Cursor. It is a separate product from the Grok chatbot, Grok Imagine and Grok Build. Grok Bot has no native "scroll TikTok" feature. TikTok access comes through third-party connectors (Hermoso, Composio) or, in principle, through generic browser computer-use.

### Cited Findings
- Candidate 1 (most likely): xAI **Grok Bot**, early beta launched **Aug 11, 2026**, "built with Cursor". Users create named AI teammates, each on a cloud computer with browser, filesystem and terminal, signed in to apps the user authorizes — [i-scoop](https://www.i-scoop.eu/what-is-grok-bot-how-xais-ai-teammates-finish-real-work-in-your-apps/); [Gigazine](https://gigazine.net/gsc_news/en/20260812-spacexai-grok-bot/); [Analytics Vidhya](https://www.analyticsvidhya.com/blog/2026/09/grok-bot-automation-tutorial/)
- Plans: per xAI, as of Aug 21, 2026 it is included with all SuperGrok Plus, Cursor Pro+ and Cursor Teams plans — [xAI news](https://x.ai/news/grok-bot-more-plans). An earlier rollout listed SuperGrok Heavy / Cursor Ultra / Cursor Teams Premium — [Gigazine](https://gigazine.net/gsc_news/en/20260812-spacexai-grok-bot/). (Conflict: reflects staged rollout.)
- Grok Bot is distinct from consumer Grok (grok.com / X), the xAI API and Grok Build — [nocodefounders](https://www.nocodefounders.com/guides/grokbot-explained-simply); [Wikipedia: Grok Build](https://en.wikipedia.org/wiki/Grok_Build)
- Candidate 2: "GrokBot" as a **web-crawler user-agent** (patterns "GrokBot/1.0; xAI-Grok/1.0; Grok-DeepSearch/1.0"). The listing site itself rates this identification unverified / low confidence — [botcrawl](https://botcrawl.com/bots/grokbot)
- Candidate 3: Consumer **Grok "watch videos"**. Musk reportedly said (dated Aug 2, 2026 by one source) that Grok can now analyze videos from across the web: summarize, transcribe, and answer questions from a video link — [remio](https://www.remio.ai/post/grok-can-analyze-any-video-but-the-hard-part-is-proving-it-understands-one); [basenor](https://www.basenor.com/blogs/news/grok-can-now-watch-and-make-videos-what-it-means)
- Candidate 4: **Grok Imagine** (grok-imagine-video-1.5) is video *generation* (native 1080p, lip-synced speech), not feed understanding — [xAI docs: Video overview](https://docs.x.ai/developers/model-capabilities/video/overview)
- I found no third-party product literally named "GrokBot" that scrolls TikTok. "hermoso.ai/grokbot/tiktok" is a connector *for* xAI's Grok Bot — [Hermoso](https://hermoso.ai/grokbot/tiktok/)
- One guide says a Grok Bot is not a general video summarizer for YouTube/Bilibili/TikTok/podcasts. It sells a third-party "skill" (BibiGPT) to add that — [BibiGPT blog](https://bibigpt.co/en/blog/posts/grok-bot-video-summarizer-agent-skill) (vendor-interested source)

### Inferences
- The user most likely saw Grok Bot demos ("AI teammate with its own computer") combined with TikTok connector marketing or consumer Grok's new video analysis. The answer should cover Grok Bot (agent mechanics) and Grok video analysis (understanding) together.

### Gaps
- No primary xAI statement that Grok Bot can scroll a TikTok For You feed. The X posts ([mvanhorn article](https://x.com/mvanhorn/article/2087941850456076696), [maverickecom](https://x.com/maverickecom/article/2091917353781023031)) could not be opened.

## 1. How does it scroll TikTok (or other feeds)?

### Takeaway
Grok Bot runs in **xAI/Cursor-hosted cloud VMs with a real browser**. The user logs in once and the session persists, shared across all of the account's Bots. It uses **connectors where available, computer use otherwise**. For TikTok, the documented paths are **API-style connectors**: Composio uses TikTok's official API, scoped to the user's own account; Hermoso offers public search plus analysis. No source documents a phone emulator or a TikTok-feed-scrolling mode. Open-source hobby agents that do scroll TikTok drive a **real Android device or emulator over ADB** with screenshot-to-vision-LLM loops.

### Cited Findings
- Official docs: each Bot works on a persistent cloud computer with browser, filesystem and terminal, and keeps running after your laptop closes — [docs.x.ai Grok Bot overview](https://docs.x.ai/grok-bot/overview)
- Bots on one account share files, browser sessions and app logins, so a login made for one Bot is usable by the others. Vellum calls these workflow boundaries, not security boundaries — [Vellum](https://www.vellum.ai/blog/official-grok-bot-breakdown); [docs.x.ai security](https://docs.x.ai/grok-bot/security)
- The cloud machines are reportedly small Linux instances running in Cursor's cloud (third-party claim) — [mindstudio](https://www.mindstudio.ai/blog/what-is-grok-bot); [tryfriday](https://www.tryfriday.ai/blog/grok-bot-launch)
- Users can open the shared desktop from a conversation. The live preview shows clicks, typing, navigation and status. Passwords, 2FA, CAPTCHAs and payments can prompt the user to take over — [docs.x.ai computer-and-apps](https://docs.x.ai/grok-bot/computer-and-apps)
- "Bots use connectors where available and computer use otherwise". Built-in connectors include Gmail, Google Calendar, Drive, OneDrive, Outlook, Teams, SharePoint and Salesforce. Connector tokens reportedly stay on the backend, not on the Bot's computer — [docs.x.ai computer-and-apps](https://docs.x.ai/grok-bot/computer-and-apps); [Vellum](https://www.vellum.ai/blog/official-grok-bot-breakdown)
- Approvals can be required for actions like sending messages, purchasing or deleting data. Local-computer access is a separate permission set — [Composio guide](https://composio.dev/content/guide-to-frok-bot); [Vellum](https://www.vellum.ai/blog/official-grok-bot-breakdown)
- Composio TikTok connector for Grok Bot (over MCP): upload videos, and list the authenticated user's own public videos, newest first. These are account-scoped API actions, not feed browsing — [Composio TikTok × Grok Bot](https://composio.dev/toolkits/tiktok/framework/grok-bot)
- Hermoso connector: `search_tiktok` (keyword search across public TikTok), `list_tiktok_videos` (recent posts with views/likes/comments/shares), `analyze_video` (hook, beats, on-screen text). It covers search and analysis, not endless scrolling — [Hermoso](https://hermoso.ai/grokbot/tiktok/) (via search summary; data-access method not confirmed)
- Open-source example (read locally): **Hormold/tiktok-warmup** drives physical Android phones or emulators over **ADB**. Its stages are: launch TikTok; "learning", where it screenshots the UI and asks a vision LLM for like/comment button coordinates; and a "working" loop that watches a video, analyzes it, then swipes up via `adb` swipe. The author calls it a "3-hours hack project mostly written by an LLM". It is an engagement/"warm-up" bot (inauthentic likes and comments), so it is a counter-example ethically — [GitHub](https://github.com/Hormold/tiktok-warmup) (src/stages/working.ts, src/tools/interaction.ts)
- Other device-agent frameworks: minitap-ai/mobile-use (Apache-2.0, NL control of real Android/iOS apps, emulator quickstart); callstack/agent-device (MIT, works from accessibility snapshots, not only screenshots); TencentQQGYLab/AppAgent (MIT, multimodal smartphone agent); masterFuf/taktik-bot (GPL-3.0, ADB + uiautomator2, For You workflow, engagement automation) — [mobile-use](https://github.com/minitap-ai/mobile-use); [agent-device](https://github.com/callstack/agent-device); [AppAgent](https://github.com/TencentQQGYLab/AppAgent); [taktik-bot](https://github.com/masterFuf/taktik-bot)

### Inferences
- Consent model of the cloud agents: the user hands credentials or an OAuth token to the vendor's cloud. The session lives on the vendor's VM, and the user watches via a live preview with take-over for sensitive steps. Relic's local-first version inverts this: the "browser session" is the user's own device, and capture is passive (what the user actually watched) rather than agent-driven scrolling. That is both lower-risk under TikTok's ToS and closer to Relic's "own activity" purpose.
- Reusable local mechanics: (a) on Android, an AccessibilityService or uiautomator-style UI tree to read caption/author/hashtags/sound text, plus MediaProjection screenshots; (b) on desktop web, a browser extension reading the DOM of the currently playing video (caption, @handle, URL) plus a tab capture. Both rely on the user's own session with explicit OS-level consent prompts. This is an inference, not documented for any product above.

### Gaps
- Whether Grok Bot's browser can or does load tiktok.com and scroll it is undocumented. No source shows it, and xAI docs pages could not be opened.
- Hermoso's data source (official API vs. third-party scraping) is unknown.

## 2. How does it analyze videos?

### Takeaway
Grok's video-understanding internals (frame rate, audio handling, model) are **not publicly documented**. Gemini is the best-documented reference: **1 fps default sampling** (configurable), **~300 tokens/sec** of video at default resolution (~100 at low), audio at **32 tokens/sec**, direct YouTube URL input, and a newer "agentic video" mode that re-scans selectively. Hobby feed agents analyze **one screenshot per video** with a vision LLM rather than true video.

### Cited Findings
- xAI has disclosed few operational details about Grok's consumer video-analysis workflow (user gives a link, asks questions). The internal method is unconfirmed — [remio](https://www.remio.ai/post/grok-can-analyze-any-video-but-the-hard-part-is-proving-it-understands-one)
- One article claims Grok responds to video input, including in some contexts live camera feeds. The claim is vague and comes from a low-quality source — [suneelmaghani](https://suneelmaghani.com/grok-adds-real-time-video-understanding-as-x-pushes-multimodal-ai-in-2026/)
- Gemini API: default **1 FPS** sampling. Use low FPS (<1) for long videos and higher FPS for fast motion — [Gemini API video understanding](https://ai.google.dev/gemini-api/docs/video-understanding)
- Gemini token cost: ~**300 tokens/sec** at default media resolution, ~**100 tokens/sec** at low. Per frame: 258 tokens (default) or 66 (low), plus **32 tokens/sec audio** — [Gemini API video understanding](https://ai.google.dev/gemini-api/docs/video-understanding)
- Gemini YouTube URL input is in preview and free for now, with pricing and rate limits likely to change. On Vertex, the video must be public or owned by the signed-in account — [Gemini API](https://ai.google.dev/gemini-api/docs/video-understanding); [Google Cloud docs](https://docs.cloud.google.com/gemini-enterprise-agent-platform/models/capabilities/video-understanding)
- Gemini "agentic video understanding": the model searches and re-scans the video instead of using a fixed rate. Google reports up to 66% lower analysis cost, up to 88% fewer tokens and up to 7% better accuracy (vendor-reported). Model names differ across Google pages (one says "Gemini 3.7 Flash", Cloud docs list 3.1 Pro / 3 Flash) — [Google blog](https://blog.google/innovation-and-ai/models-and-research/gemini-models/introducing-agentic-video-in-gemini/)
- Hermoso `analyze_video` decomposes a clip into hook, beats and on-screen text. Model and sampling are undisclosed — [Hermoso](https://hermoso.ai/grokbot/tiktok/)
- tiktok-warmup: per video, it takes one ADB screenshot and asks a vision LLM (via Vercel AI SDK structured output) for "main subject, mood/tone". There is no audio, no multi-frame sampling and no metadata API — [GitHub tiktok-warmup](https://github.com/Hormold/tiktok-warmup) (src/stages/working.ts L96–133, L172)

### Inferences
- Rough local budget, using Gemini's numbers as a yardstick: a 30-second TikTok at 1 fps is ~30 frames, or ~9k tokens at default resolution (~2k at low) plus ~1k audio tokens. A cheap local pipeline for Relic: keyframes at 0.5–1 fps + on-device OCR for on-screen text + on-device ASR (Whisper-class) on captured audio + caption/hashtag text from the UI tree, feeding a small local VLM or text LLM for the summary. "Screenshot once per video plus UI text" is the minimum viable version that hobby agents use.

### Gaps
- No source gave Grok model names, fps, latency or per-video cost for Grok video analysis or for Grok Bot.
- No latency figures for any feed agent.

## 3. Outputs: summaries, trends, collections, memory

### Takeaway
Grok Bot's outputs are general agent outputs: files on the shared computer, messages, and scheduled or recurring "routines", with per-Bot memory/learned context. TikTok connectors return structured per-video metrics and hook/beat breakdowns, suited to trend or competitor reports. Meta's Muse demonstrates "reel → actionable artifact" (recipe reels → grocery lists).

### Cited Findings
- Per-Bot conversations and learned context stay separate, while files and browser sessions are shared across an account's Bots — [Vellum](https://www.vellum.ai/blog/official-grok-bot-breakdown)
- Bots can run on schedules or event triggers. Where enabled, the user performs a browser workflow once while the Bot watches, and the Bot drafts a reviewable "skill" — [Composio guide](https://composio.dev/content/guide-to-frok-bot)
- Hermoso returns views/likes/comments/shares per post plus hook/beats/on-screen text analysis — [Hermoso](https://hermoso.ai/grokbot/tiktok/)
- Meta Muse (announced Sep 8, 2026; runs on the Muse Spark multimodal model) can turn recipe reels into grocery lists. Connect 2026 (Sep 23) added real-time voice/video avatars, which is video *chat*, not video analysis — [TechCrunch Sep 8](https://techcrunch.com/2026/09/08/meta-debuts-its-muse-ai-agent-will-consumers-trust-it/); [The Decoder](https://the-decoder.com/meta-gives-its-muse-ai-agent-video-avatars-email-addresses-and-mac-control/); [Wikipedia: Muse](https://en.wikipedia.org/wiki/Muse_(AI_agent))

### Inferences
- For Relic, the useful output pattern is "watch-once → structured record" (who, what, caption, transcript snippet, on-screen text, topics) stored in the user's local memory, with later "turn this reel into X" actions. This mirrors the Muse and Hermoso outputs but applied to what the user actually watched.

### Gaps
- No source documents a "saved collection" or trend-report feature specific to Grok Bot + TikTok.

## 4. Comparable agents and how they handle video

### Takeaway
Only **Gemini** documents true native video understanding (frames + audio, YouTube URLs). Browser agents (Perplexity Comet, ChatGPT's agent/Atlas, Claude for Chrome) mostly rely on **transcripts and page context or screenshots**, with no documented continuous frame analysis. Meta Muse can act on Reels within Meta's own platforms, but its analysis mechanics are undocumented.

### Cited Findings
- Gemini: native video (1 fps default, audio tokens, YouTube URL input, agentic re-scan mode) — see Section 2 — [Gemini API](https://ai.google.dev/gemini-api/docs/video-understanding); [Google blog](https://blog.google/innovation-and-ai/models-and-research/gemini-models/introducing-agentic-video-in-gemini/)
- Perplexity Comet: "knows what you're looking at", including follow-up questions on a PDF or a **YouTube video transcript** (transcript-based) — [aixsociety](https://aixsociety.com/manus-ai-vs-perplexity-comet-vs-autoglm-ai-agents-for-everyday-tasks/); [Everyday AI ep. 638](https://www.youreverydayai.com/ep-638-agentic-browser-showdown-chatgpt-atlas-vs-perplexity-comet/)
- ChatGPT: one 2026 guide says the consumer app doesn't analyze YouTube URLs directly. The common workaround is pasting a transcript, which misses on-screen text and visuals. Another source says the former "agent mode" has been folded into "ChatGPT Work". Both are low-quality SEO sources, so verify — [ekamoira](https://www.ekamoira.com/blog/chatgpt-summarize-youtube-videos); [builts.ai](https://builts.ai/blog/manus-vs-chatgpt-vs-claude-vs-perplexity/)
- Claude for Chrome: an extension in the user's existing browser, using the user's own logged-in session. No source found on its video handling — [clickforest](https://www.clickforest.com/en/blog/ai-tools-comparison)
- Manus: orchestrates multiple models for autonomous tasks in a cloud sandbox. No source found on video support — [builts.ai](https://builts.ai/blog/manus-vs-chatgpt-vs-claude-vs-perplexity/)
- Meta Muse: see Section 3 — [TechCrunch Sep 25](https://techcrunch.com/2026/09/25/meta-is-putting-its-muscle-behind-muse-as-the-ai-app-takes-off/)

### Inferences
- There are two architectural camps: (a) **cloud VM agents** (Grok Bot, Manus, ChatGPT agent) that run their own browser with the user's delegated logins; (b) **in-user-browser agents** (Claude for Chrome, Comet, Atlas) that act in the user's own session on their device. Camp (b) is the closer template for Relic's local-first capture.

### Gaps
- No primary documentation found for video handling in ChatGPT agent/Atlas, Comet, Claude for Chrome or Manus, because the vendor pages were unreachable. These claims rest on secondary comparison blogs.

## 4b. Mechanics in depth: documented vs. inferred, plus how Relic can do it locally

### Takeaway
Grok Bot is a **cloud-VM agent**. A managed, router-selected Grok model plans and acts. It uses structured tool calls (built-in OAuth connectors, OAuth app catalog, remote MCP) where they exist, and falls back to visual computer use in a persistent cloud browser/desktop. Coding sub-tasks are delegated to a Cursor Cloud Agent. Perception internals (screenshots vs. accessibility tree, video fps, OCR) are **not officially documented**. There is **no TikTok partnership**: TikTok reaches Grok Bot only via third-party remote MCP servers using TikTok's OAuth/API. Hobby feed agents show the device-control alternative: ADB screenshot → vision LLM → swipe.

### Cited Findings
**(1) Agentic architecture (cloud VM vs. device, model loop, tools, planning)**
- DOCUMENTED: persistent cloud computer per account (browser, filesystem, terminal), shared by the account's Bots; keeps running when the user's devices are off; live desktop preview; user take-over for passwords, 2FA, CAPTCHA and payments — [docs.x.ai overview](https://docs.x.ai/grok-bot/overview); [docs.x.ai computer-and-apps](https://docs.x.ai/grok-bot/computer-and-apps)
- DOCUMENTED: "connectors where available, computer use otherwise" — [docs.x.ai computer-and-apps](https://docs.x.ai/grok-bot/computer-and-apps)
- SECONDARY: model routing is managed for the user, who doesn't pick the model. Grok Bot is separate from the Grok 4.6 model; Wikipedia lists Grok 4.7 (Sep 21, 2026) as the latest release; Grok 4.5+ is reportedly co-developed with Cursor's parent — [learncursor](https://www.learncursor.dev/learn/cursor-agents/cursor-grok-bot); [Wikipedia: Grok](https://en.wikipedia.org/wiki/Grok_(chatbot))
- SECONDARY: for coding, the Bot doesn't write code itself. It sends a prompt to a **Cursor Cloud Agent** harness on a separate computer, so it acts as an orchestrator with sub-agents — [codepick architecture guide](https://codepick.dev/en/guides/grok-bot-architecture/); [rohitghumare](https://rohitghumare.com/blog/grok-bot-shared-computer/)
- SECONDARY: schedules and event triggers; approval gates on send, purchase and delete; "watch me do it once → draft a reviewable skill" (learning by demonstration) — [Composio guide](https://composio.dev/content/guide-to-frok-bot)
- INFERRED / UNDOCUMENTED: whether actions are grounded on screenshots, the accessibility tree/DOM, or both. A reviewer saw the Bot return screenshots on request, which doesn't settle it — [codepick](https://codepick.dev/en/guides/grok-bot-architecture/)
- Device-control alternative (open source, documented in code): ADB launch → screenshot → vision LLM returns structured JSON (button coordinates, "is the feed visible") → tap or swipe → re-screenshot to verify — [tiktok-warmup](https://github.com/Hormold/tiktok-warmup). callstack/agent-device uses accessibility snapshots, which are token-efficient, instead of screenshots alone — [agent-device](https://github.com/callstack/agent-device)
- **Relic locally:** run a plan → act → observe loop on-device, but for Relic the "act" is mostly *passive observe*: hooks fire on app or video change; a local model decides what to capture or keep; anything active (e.g., "save this reel") goes through explicit user approval gates. Copy Grok Bot's approval gates, take-over UX and teach-by-demonstration skills, and keep them local.

**(2) How videos are analyzed**
- DOCUMENTED (Gemini only): 1 fps default (tunable), 258 tokens per frame (66 at low resolution), 32 tokens/sec audio, ~300 tokens/sec total, YouTube URL input, and an agentic re-scan mode — [Gemini API](https://ai.google.dev/gemini-api/docs/video-understanding); [Google blog](https://blog.google/innovation-and-ai/models-and-research/gemini-models/introducing-agentic-video-in-gemini/)
- NOT DOCUMENTED (Grok): fps, audio path, OCR and model for Grok's "watch videos" feature — [remio](https://www.remio.ai/post/grok-can-analyze-any-video-but-the-hard-part-is-proving-it-understands-one)
- DOCUMENTED IN CODE (hobby agent): a single screenshot per video goes to a vision LLM, with no audio — [tiktok-warmup](https://github.com/Hormold/tiktok-warmup)
- **Relic locally:** while a video is on screen, sample keyframes at ~0.5–1 fps with scene-change dedup; run on-device OCR (overlay text, captions) and on-device ASR on system or app audio where the OS permits it; send frames plus text to a small local VLM, or caption with the VLM and summarize with a text LLM. Escalate to more frames only on demand, mirroring Gemini's agentic re-scan.

**(3) Extracting structured information**
- DOCUMENTED IN CODE: Zod-schema structured outputs from the vision LLM (`result`, `confidence`, coordinates) — [tiktok-warmup src/tools/interaction.ts](https://github.com/Hormold/tiktok-warmup)
- SECONDARY: Hermoso `analyze_video` emits hook / beats / on-screen text; `list_tiktok_videos` returns views, likes, comments and shares — [Hermoso](https://hermoso.ai/grokbot/tiktok/)
- INFERRED: Grok Bot connectors return structured JSON from APIs, while its computer-use path must derive structure from pixels or the DOM. Neither is documented for video.
- **Relic locally:** prefer *text-native* sources first (accessibility/UI tree or DOM for @handle, caption, hashtags, sound name, URL), then fill visual and audio fields from OCR, ASR and the VLM. Write one schema-validated record per viewed video (timestamp, app, author, caption, transcript, OCR text, topics, embedding) into local memory.

**(4) How it accesses different apps**
- DOCUMENTED: built-in connectors authenticate via OAuth, and Grok discovers the tools a user's MCP server exposes — [docs.x.ai connectors](https://docs.x.ai/grok/connectors)
- SECONDARY: three tiers — 7 in-house built-in connectors, a catalog of pre-configured OAuth apps, and bring-your-own MCP. Connector tokens stay on the xAI backend, not the VM — [usecarly](https://www.usecarly.com/blog/grok-connectors/); [Vellum](https://www.vellum.ai/blog/official-grok-bot-breakdown)
- SECONDARY: Grok Bot only reaches **remote** (public-internet) MCP servers, not local stdio MCP. Local stdio MCP works only in Grok Build — [Posterly guide](https://www.poster.ly/guides/grokbot-guide)
- SECONDARY (single vendor blog, unverified): a built-in X connector, read-only (search posts, timeline, mentions), shipped Aug 29, 2026 — [OpenTweet](https://opentweet.io/how-to/give-grok-bot-the-ability-to-post-to-x)
- TikTok: no xAI–TikTok partnership found. Access is via third-party remote MCP with OAuth: Composio (own-account list/upload), Upload-Post (OAuth 2.1 or API key, posting) and Hermoso — [Composio](https://composio.dev/toolkits/tiktok/framework/grok-bot); [Upload-Post](https://www.upload-post.com/grok-bot-social-media/); [Hermoso](https://hermoso.ai/grokbot/tiktok/)
- Logged-in browser sessions: the cloud browser persists the user's logins, shared across Bots — [Vellum](https://www.vellum.ai/blog/official-grok-bot-breakdown)
- Mobile app control or emulators: not used by Grok Bot per any source. Used by open-source agents (ADB/uiautomator2, mobile-use, AppAgent) — [mobile-use](https://github.com/minitap-ai/mobile-use); [AppAgent](https://github.com/TencentQQGYLab/AppAgent)
- **Relic locally:** order access paths as (a) official OAuth/APIs and data-export files for the user's *own* data (e.g., TikTok "Download your data" watch history, if available — unverified here); (b) local stdio MCP servers on the user's machine; (c) the user's own logged-in browser via an extension (like Claude for Chrome or Comet); (d) OS-level screen and accessibility capture on the user's own phone or desktop with explicit permission prompts. Avoid cloud VMs holding the user's sessions, and avoid driving the TikTok app.

### Inferences
- The core difference: Grok Bot *delegates* the user's identity to a vendor VM and *acts*. Relic should *observe* on the user's own device and *remember*. The reusable pieces are the loop design, approval gates, tiered tool access, schema-validated extraction, and adaptive frame sampling.

### Gaps
- The Grok Bot perception stack, the exact model per task, latency and cost are undocumented.
- The xAI docs were known only through search summaries, since the pages could not be fetched.

## 5. Platform pushback: TikTok ToS, rate limits, legal status

### Takeaway
TikTok's terms prohibit automated access (bots, scrapers, scripts) without written permission. Enforcement is mostly civil and technical (account and IP blocks, cease-and-desist). The official Research API is limited to non-profit academic researchers, about 1,000 requests/day, with no commercial use. Engagement-automation bots also violate TikTok's authenticity rules. Most available sources are scraping-vendor blogs, not TikTok itself.

### Cited Findings
- TikTok terms bar automated access (bots, scrapers) without written permission. The contract binds logged-in account holders, and the argument is weaker for logged-out access — [tikliveapi](https://www.tikliveapi.com/blog/is-scraping-tiktok-legal-2026-developer-guide/); [sociavault](https://sociavault.com/blog/is-scraping-tiktok-legal-2026)
- Consequences are mostly civil and technical: IP and account blocks, cease-and-desist letters. The hiQ v. LinkedIn line protects scraping of public data in the US, but TikTok's terms are less litigated — [sociavault](https://sociavault.com/blog/is-scraping-tiktok-legal-2026)
- Research API: qualifying non-profit academics in specific regions; ~4-week approval; 1,000 requests/day cap; commercial use prohibited; requires a proposal, funding disclosure and ethics approval — [scrapebadger](https://scrapebadger.com/blog/tiktok-scraping-apis-in-2026-the-complete-deep-guide)
- One blog says the US terms were updated July 15, 2026, and that rest-of-world terms cover any automated scripts that "otherwise interact with" the service. Unverified against TikTok's own pages — [instantdm](https://instantdm.com/blog/is-tiktok-automation-allowed); [openhosst](https://openhosst.com/blog/tiktok-automation)

### Inferences
- An agent that *drives* the TikTok app or site (scrolls, likes) is automation under the ToS, even in the user's own account. Passive, on-device capture of what the user themselves watched (screen/accessibility capture for personal memory) does not send automated requests to TikTok, so it is in a different risk category. It may still touch ToS clauses on copying content, and creators' and third parties' privacy in stored recordings. Relic should keep captures local, avoid redistribution, and get legal review. This is an inference, not legal advice.

### Gaps
- TikTok's own ToS and Developer Terms pages could not be fetched to quote exact clause text.
- No reliable source on TikTok rate limits beyond the Research API cap.

### Blocked sources
All of the following failed (WebFetch: getaddrinfo ENOTFOUND; curl via proxy: CONNECT 403). Only github.com was reachable.
- https://x.ai/news/grok-bot-more-plans
- https://flaviocopes.com/grok-bot/
- https://hermoso.ai/grokbot/tiktok/
- https://www.layer3labs.io/guides/what-is-grok-bot
- https://bibigpt.co/en/blog/posts/grok-bot-video-summarizer-agent-skill
- https://docs.x.ai/grok-bot/overview (and /computer-and-apps, /security — not attempted individually after host block)
- https://ai.google.dev/gemini-api/docs/video-understanding
- https://www.tiktok.com/legal/page/us/terms-of-service/en
- https://blog.google/ (agentic video post)
- https://www.vellum.ai/blog/official-grok-bot-breakdown
- Also not fetched (search-summary only): https://docs.x.ai/grok/connectors, https://codepick.dev/en/guides/grok-bot-architecture/, https://www.learncursor.dev/learn/cursor-agents/cursor-grok-bot, https://www.poster.ly/guides/grokbot-guide, https://opentweet.io/how-to/give-grok-bot-the-ability-to-post-to-x, https://x.ai/bot/guides/grok-bot-101
- X posts: https://x.com/mvanhorn/article/2087941850456076696, https://x.com/maverickecom/article/2091917353781023031 (not attempted; X requires login and the host was assumed blocked)
