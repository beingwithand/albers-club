# Record your own life on your own hardware

As of October 2026, it is technically feasible to build **Relic** (working name) on desktops: a consumer app that keeps a private, searchable record of a person's own digital activity entirely on hardware they own. The design is now fairly clear. A signed capture engine takes snapshots only when something changes on screen. It reads exact text from the operating system's accessibility layer and falls back to on-device OCR, and it can transcribe the user's own audio locally. Screenpipe, the closest existing tool, reports that this kind of event-driven capture uses **about 5–10 GB a month**, against about 30 GB at a fixed one frame per second ([Screenpipe](https://screenpi.pe/about); [Screenpipe docs](https://docs.screenpi.pe/architecture)). Everything is indexed in SQLite full-text search plus a vector index, the same pattern Microsoft's Recall uses ([TotalRecall analysis](https://github.com/xaitax/TotalRecall)). A local model answers questions over the archive. Local agents act on the user's behalf, for example requesting exports and filing AI-training objections, but they run mostly as deterministic scripts, with a local model called only to repair a step that broke.

The hard limits are platform limits:

- **macOS** asks the user to re-approve screen recording roughly every month.
- **Android** requires fresh consent for each capture session, and Google Play bans using accessibility services for autonomous AI actions.
- **iOS** allows no continuous background capture of other apps.

The hard risks are security risks:

- **Prompt injection is unsolved.** Every major agentic browser was hijacked through ordinary content in August 2026.
- **Recall's redesigned vault still leaked.** Code running as the same user got the data from the process that displays it.

So Relic has to be built around four rules: the model never sees credentials; the agents are confined in code, not just told what to do in a prompt; the viewer process is hardened, not only the database; and no hidden or remote-viewing mode exists. The market is open. Rewind's capture was switched off after Meta bought its parent company. Bee went to Amazon. Screenpipe is now source-available, sold under a commercial license and aimed at company workflows. Recall runs on fewer than 10% of Windows 11 PCs. No local, open, consumer product combines capture, memory and agents.

## The machine on your desk is the last place you can still take your data back

The case for Relic is that the cloud routes for getting your own data back are narrowing, while the tools for capturing it locally have matured.

On the cloud side:

- **Google Photos:** since 31 March 2025 the Photos Library API can no longer read a user's whole library. It sees only what the app itself created ([Google Developers Blog](https://developers.googleblog.com/en/google-photos-picker-api-launch-and-library-api-updates/)).
- **Instagram:** personal accounts have no official API since the Basic Display API was retired in December 2024 ([deprecated-api.io](https://deprecated-api.io/en/apis/2024-12-04-meta-instagram-basic-display-api/)).
- **Reddit:** will close public Data API access in March 2027 ([TechCrunch](https://techcrunch.com/2026/09/30/reddit-is-killing-rss-feeds-ending-public-api-access-because-of-ai-bots/)).
- **Continuous official feeds** come mostly from the EU's Digital Markets Act. That makes them real for users in the EEA, and sometimes the UK and Switzerland, and largely absent for everyone else ([EC DMA portal](https://digital-markets-act.ec.europa.eu/developer-portal/end-user-data-portability_en)).

Meanwhile, AI training on user data has become the default nearly everywhere, and the opt-outs work only going forward:

- Anthropic switched consumer chats to opt-out training in September 2025, with retention of 5 years for users who opt in versus 30 days for those who don't ([Goldfarb](https://www.goldfarb.com/updates-to-anthropics-claude-ai-terms-and-privacy-policy-what-you-need-to-know/)).
- Meta began training on EU users' public posts on 27 May 2025, under a "legitimate interest" legal basis ([The Hacker News](https://thehackernews.com/2025/05/meta-to-train-ai-on-eu-user-data-from.html)).

The "own your memory" products themselves keep disappearing. Rewind's capture was disabled on 19 December 2025, after Meta bought its parent Limitless ([9to5Mac](https://9to5mac.com/2025/12/05/rewind-limitless-meta-acquisition/)). Users want these tools: Pew found that **57% of Americans feel they have little or no control over AI in their lives, and 61% want more** ([Engadget on Pew](https://www.engadget.com/americans-growing-anxious-as-ai-adoption-expands-pew-research-finds-204500137.html)). Plaud sold more than a million AI note-taking devices without venture funding ([Forbes](https://www.forbes.com/sites/iainmartin/2025/09/02/how-an-ai-notetaker-became-one-of-the-few-profitable-ai-startups/)). What users don't trust is whoever holds the data.

The answer is to invert the usual architecture. Everything the person sees and does already passes through their own screen, keyboard, browser and microphone, so Relic captures it there, with the operating system's explicit permission and the person's ongoing consent. Official exports and APIs then become a supporting layer that backfills history from before Relic was installed. The rest of this report follows the user's priorities in order: capture engine, on-device AI, local agents, vault security, lessons from the data harvesters, supporting imports, open-source parts, law, market, and finally an architecture and roadmap.

## The capture engine reads text first, pixels second and audio last

### Each operating system sets a different ceiling

On desktops, continuous capture is possible but more and more gated by the operating system. On phones it is mostly blocked. The table below summarizes what is achievable on each platform as of October 2026.

| Platform | Pixel capture | Text source | Hard constraints | Verdict |
|---|---|---|---|---|
| **macOS** | ScreenCaptureKit stream under the Screen Recording permission (TCC); the per-share SCContentSharingPicker is not enough for continuous capture ([Apple Dev Forums](https://developer.apple.com/forums/thread/849969)) | Accessibility API (AXUIElement); Apple Vision OCR as fallback | Re-consent prompt roughly monthly since Sequoia, applying to ScreenCaptureKit apps too ([9to5Mac](https://9to5mac.com/2024/08/14/macos-sequoia-screen-recording-prompt-monthly/); [TidBITS](https://talk.tidbits.com/t/apple-reduces-excessive-sequoia-permission-requests-shifts-to-monthly/28621)); unbundled command-line daemons broke on macOS 26.1, so ship a signed .app ([Apple Dev Forums](https://developer.apple.com/forums/thread/807898)); the macOS 27 beta hides other apps' window-owner names unless Screen Recording is granted ([Apple Dev Forums](https://developer.apple.com/forums/thread/839069)) | Fully feasible; design onboarding around the monthly prompt |
| **Windows** | Windows.Graphics.Capture | UI Automation; Windows.Media.Ocr as fallback | Apps can hide windows with `WDA_EXCLUDEFROMCAPTURE`, which Microsoft says is "not a security feature" ([Microsoft Learn](https://learn.microsoft.com/en-us/windows/win32/api/winuser/nf-winuser-setwindowdisplayaffinity)); Signal sets it by default against Recall ([TechRadar](https://www.techradar.com/computing/windows/signal-blasts-microsoft-over-recall-privacy-failings-as-secure-messaging-app-is-forced-to-fudge-a-way-of-blocking-the-controversial-windows-11-feature)) | Fully feasible; a black frame means "the user or an app opted out", so Relic honors it and records nothing |
| **Linux** | PipeWire through the xdg-desktop-portal ScreenCast picker on Wayland | AT-SPI accessibility (patchy); OCR | Portal details (a "remember this choice" token in portal v4+) are **unverified** in the notes | Feasible on X11; on Wayland it works through the portal, needs testing |
| **Android** | MediaProjection, with consent per session; reusing the consent token throws an error on Android 14+ ([Android Developers](https://developer.android.com/media/grow/media-projection)) | NotificationListenerService (lossy); AccessibilityService is a policy risk | Play allows `isAccessibilityTool` only for disability tools and bans using accessibility to autonomously plan and execute actions ([Play Console Help](https://support.google.com/googleplay/android-developer/answer/10964491?hl=en)) | Partial: notifications, usage, location, and screen capture only during sessions the user starts |
| **iOS** | ReplayKit broadcast extension, started by the user, with a red indicator and a ~50 MB memory cap ([Apple Dev Forums](https://developer.apple.com/forums/thread/651367)) | None for other apps | No background capture of other apps | Not feasible as continuous capture; rely on the share sheet, imports and the user's Mac |

Three design consequences follow. First, **the desktop is the product and the phone is a satellite.** An earlier report reached the same conclusion for sync: no iOS app can run continuously in the background ([Möbius Sync FAQ](https://mobiussync.com/faq/)). Second, Relic should treat every OS signal that a user or app has opted out as binding: `WDA_EXCLUDEFROMCAPTURE`, macOS secure text fields (`AXSecureTextField`), UI Automation's `IsPassword` property, and DRM content. IOActive published a bypass of Signal's capture protection in August 2026 ([IOActive](https://www.ioactive.com/signal-windows-desktop-contentprotection-bypass)). That is exactly the kind of technique Relic must never use. Third, Relic's iOS story is honest: this is "the agentic stuff Apple should be doing". Apple's own on-device semantic index and App Intents already cover part of it ([Wing VC](https://www.wing.vc/content/unpacking-apple-intelligence-apples-vision-for-personalized-ai)), and Apple does not open it to third parties. For EEA users, Relic can import Recall's own export. Recall offers an encrypted, user-initiated export, available only in the EEA, which a third-party app can read once the user supplies a one-time code and the folder path ([Microsoft Support](https://support.microsoft.com/en-us/Accessibility/windows/copilot/use-a-screen-reader-to-export-recall-snapshots-in-windows)).

### Event-driven capture cuts storage roughly sixfold

Fixed-rate capture wastes most of its frames on a screen that hasn't changed. Screenpipe's own numbers show the gap: **about 30 GB a month at one frame per second, against about 5–10 GB a month when frames are saved only on screen change** ([Screenpipe docs](https://docs.screenpi.pe/architecture); [Screenpipe](https://screenpi.pe/about)). That roughly sixfold spread shows that capture policy, not the video codec, decides storage.

Relic should trigger a snapshot on meaningful events: an app or window switch, the end of a scroll, a pause in typing, a clipboard change, or a page navigation in the companion browser extension. Each candidate frame then passes a cheap perceptual-hash or similarity check, and near-duplicates are dropped before any expensive processing runs. Typing should trigger a snapshot after the user pauses, never per keystroke. Relic records what the screen showed, not a keystroke log, and that line matters for the anti-stalkerware design discussed later.

Published resource figures are rough. Screenpipe's documentation cites about 10% CPU and about 600 MB of RAM, and other listings give 5–15% CPU and 0.5–3 GB ([Screenpipe docs](https://docs.screenpi.pe/architecture); [Mintlify guide](https://www.mintlify.com/screenpipe/screenpipe/advanced/performance)). No tool has published battery-impact measurements, and that is a gap Relic should close with its own benchmarks before launch.

### Accessibility text beats OCR, and small vision models are a seasoning

The most important engineering choice is where the text comes from. The accessibility tree, the structured description of on-screen elements that screen readers use, gives exact strings, roles and often URLs, at almost no cost. Screenpipe reads the accessibility tree first and uses OCR only as a fallback ([Screenpipe README](https://github.com/screenpipe/screenpipe)). Relic should follow the same order:

1. **Accessibility text** (macOS AX, Windows UI Automation, Linux AT-SPI) whenever the app exposes it.
2. **Native OCR** (Apple Vision, Windows.Media.Ocr) for canvases, images, remote desktops and games. Both run on-device and are fast.
3. **Cross-platform OCR** (RapidOCR or PaddleOCR via ONNX, or Tesseract) as the portable fallback.
4. **A small vision-language model** (Florence-2, Moondream or Qwen-VL class) used occasionally to caption or summarize a work session, never per frame.

This ordering is an engineering inference from the notes. **No reliable published benchmark compares these OCR engines and small vision models on screen text**, so accuracy and speed claims need Relic's own test set. That set should include Korean, because Korean text breaks many OCR pipelines that were tuned on Latin script.

### Local speech recognition is fast, but language coverage decides the model

Audio transcription is now cheap enough to run locally. NVIDIA's **Parakeet TDT 0.6B v3** reportedly transcribes about 7–10 times faster than Whisper large-v3-turbo. In one test on an M4 Pro, a 5-minute clip took 2.91 seconds with Parakeet against 20.92 seconds with Whisper. Parakeet also has a slightly lower English word error rate (about 6.3% vs 7.8%) and reportedly doesn't hallucinate text during silence ([Parakeety](https://www.parakeety.com/resources/parakeet-v3-vs-whisper-large-v3-turbo); [WhisperNotes](https://whispernotes.app/blog/parakeet-v3-default-mac-model); [Northflank](https://northflank.com/blog/best-open-source-speech-to-text-stt-model-in-2026-benchmarks)). The catch is coverage: **Parakeet handles 25 European languages, while Whisper handles 99+** ([Arun Baby](https://www.arunbaby.com/speech-tech/0073-whisper-vs-parakeet-asr-decision/)). These are vendor or blog benchmarks, not independent ones.

So Relic should route by language: Parakeet for English and European languages, and Whisper turbo (through whisper.cpp or MLX) for Korean and everything else. A voice-activity detector should gate both, to save battery and avoid transcribing silence. Telling speakers apart (diarization) would use pyannote-class models, but the notes contain no benchmarks for them. Audio capture is also where the legal exposure sits (see the legal section), so **microphone capture defaults to off, and when the user turns it on, it records only their own microphone and not the other side of calls**.

### Tiered retention keeps years of history affordable

At 5–10 GB a month, a year of full-fidelity capture is about 60–120 GB. That is affordable on a NAS but heavy on a laptop. Microsoft's Recall defaults to 90 days or 75 GB, whichever comes first ([TotalRecall analysis](https://github.com/xaitax/TotalRecall)). Relic should use tiers:

- **Recent tier:** full frames, stored as short (about 1–5 minute) H.265 or AV1 segments. Use screen-content coding modes where the encoder supports them, and force a keyframe on every app switch so the timeline can jump there quickly.
- **Middle tier:** keyframes and thumbnails only.
- **Deep tier:** text and metadata only (window, app, URL, dwell time, transcript), which costs a tiny fraction of the video.

Text and thumbnails are always stored separately from video, so search never needs to decode video. Perceptual hashes dedupe frames, and hashes of window plus content dedupe text. These tier boundaries are design inferences, since the notes found no primary benchmarks on codec choice for screen recordings. The user should be able to set tier lengths per app, for example keeping design tools at full fidelity for a year and chat apps as text only after a week.

## A local AI stack turns the archive into memory

The search layer is settled. Recall stores OCR text, window titles, URLs, file paths and dwell time in an encrypted SQLite database with an **FTS5** full-text index. It also keeps separate semantic stores for text and images, built on DiskANN vector graphs ([TotalRecall analysis](https://github.com/xaitax/TotalRecall)). Screenpipe uses SQLite with FTS5 and keeps media files on disk ([Screenpipe README](https://github.com/screenpipe/screenpipe)). Timelinize, the import-based personal timeline, also indexes in SQLite and stores files on disk by date in non-proprietary formats ([Timelinize README](https://github.com/timelinize/timelinize)). The GitHub survey found the same pattern across Screenpipe, Timelinize, Promnesia/HPI and Datasette: immutable raw files, normalized into SQLite with FTS, then a timeline UI, then an LLM layer on top.

For Relic, the proposed stack is an inference from those designs:

- **Exact search:** SQLite FTS5 with the trigram tokenizer. Trigrams tolerate OCR noise and Korean (CJK) text, which have no reliable word boundaries.
- **Semantic search:** an embedding index (sqlite-vec or LanceDB) using a small multilingual text embedding model, plus an optional CLIP/SigLIP-class model for "find the screen that looked like this".
- **Summaries and answers:** a local **3–8B** language model served through llama.cpp, MLX or Ollama, for daily summaries, "what was I doing when…" questions and timeline narration.

The notes found **no benchmarks of sqlite-vec versus LanceDB at the scale of millions of snippets**, so that choice should be made on a synthetic year of captured data. Indexing should run in a separate process with no network access, following Android's Private Compute Core model. There, ambient-data features run in an isolated sandbox, and all network traffic goes through a narrow, open-source service ([Google PCC paper](https://arxiv.org/pdf/2209.10317)).

MCP (the Model Context Protocol, a standard way to connect AI assistants to tools and data sources) is how the archive reaches the user's assistants. Screenpipe already ships an MCP server, listed in public MCP directories ([Glama](https://glama.ai/mcp/servers/isb2i5urdu)). This is also the most dangerous interface in the product. Every web page the user ever viewed becomes possible input to a language model, so an attacker can plant instructions in content and wait for the user to ask a question that retrieves it. Relic's MCP server should follow four rules:

1. **Read-only by default.**
2. **Scoped by time range and app** for each session.
3. **Redacted** before any result leaves the vault, removing card numbers, ID numbers including Korean resident registration numbers (주민등록번호), API keys and tokens.
4. **Approved by the user** for each session, with every query written to the audit log.

A local assistant should be the default. A cloud assistant connecting over MCP should get only redacted, summarized results unless the user explicitly widens access.

## Local agents act for you only inside a cage of code

### Agent capability is no longer the bottleneck

Computer-use agents are good at clicking through known flows.

- **Desktop benchmark (OSWorld-Verified):** aggregators put frontier agents at **about 85–86%**, above the roughly 72% human baseline ([a16z](https://a16z.com/can-agents-use-a-computer-yet-weve-got-the-data/); [Steel leaderboard](https://leaderboard.steel.dev/leaderboards/osworld/)). The rows conflict and mix self-reported with verified results. Several model names that appear in them could not be verified against vendor pages.
- **Open-weights agents trail:** ByteDance's UI-TARS-2 scores 47.5% ([Codesota](https://codesota.com/model/ui-tars-2)). The open Agent S3 framework reports 72.6% with best-of-N sampling ([gui-agents](https://pypi.org/project/gui-agents)).
- **Small local models on phones:** the 4-billion-parameter **Holo3.1-4B reportedly reaches 71% on AndroidWorld** (aggregator data) ([BenchLM](https://benchlm.ai/benchmarks/androidworld)). That suggests narrow agents that run entirely on-device are realistic.

The hard parts are reliability on real logged-in sites, security, and platform pushback. Consumer agent products also churn. OpenAI discontinued its standalone Atlas browser in August 2026, about ten months after launch ([BGR](https://bgr.com/2212396/openai-chatgpt-browser-atlas-discontinued/)). Relic should therefore never depend on a vendor's agent browser.

### Scripts first, with a local model only to repair

The consensus pattern is hybrid. Most automation stays as plain Playwright browser scripts. A language model is called only when a step fails or an element is fragile, and successful fixes are cached so repeat runs make no model calls at all. Stagehand's guidance keeps roughly 90% of logic in Playwright, and its v3 (February 2026) caches action mappings so that later runs cost close to nothing ([Noqta](https://noqta.tn/blog/ai-browser-agents-browser-use-stagehand-web-automation-2026)). By contrast, Browser Use, which calls a model on every step, costs about $0.02–0.30 per task at 2–5 seconds per action ([Massive](https://www.joinmassive.com/blog/browser-use-vs-stagehand-vs-skyvern-choosing-an-agent-browser-framework)).

For Relic, each service gets a versioned **recipe**: deterministic steps that check whether the user is logged in, navigate to the export page, press "request", and watch for the "your export is ready" message. When a recipe step breaks because the site's interface changed, Relic sends a scrubbed version of the page structure (DOM) or a screenshot to a local vision-language model. It then proposes a repaired step, the user approves it, and the fix is promoted into the recipe. This keeps ongoing cost near zero, makes behavior auditable, and **shrinks the prompt-injection surface, because the model reads very little untrusted content**. A frontier cloud model can be an opt-in option for working out a brand-new flow, but only on scrubbed inputs and never by default.

### Prompt injection is unsolved, so limit what a hijacked agent can do

Prompt injection means hidden instructions in ordinary content that an AI model treats as the user's own commands. At Black Hat USA on 5 August 2026, Zenity Labs showed **zero-click exploit chains ("PleaseFix") against Claude in Chrome, Gemini in Chrome, Perplexity Comet, ChatGPT Atlas and Copilot in Edge**. Hidden instructions in an email, a calendar invite or a web page were treated as the user's intent. The reported impact ranged from data theft to account takeover. In Claude in Chrome, a built-in JavaScript tool became the way to run arbitrary code on any site ([Dark Reading](https://darkreading.com/cyber-risk/ai-browsers-zero-click-agent-hijacking); [Zenity](https://zenity.io/blog/ai-agent-security-black-hat-recap)). Brave showed injections hidden in faint text that people cannot see but OCR and vision models read ([Brave](https://brave.com/blog/unseeable-prompt-injections/)). That matters directly for a screen-capture product. Anthropic's best published figure is **about 1% attack success against an adaptive attacker, which it still calls "meaningful risk"** ([Anthropic](https://www.anthropic.com/research/prompt-injection-defenses)), and OpenAI says the problem may never be fully solved ([IndiaNIC](https://signal.indianic.com/openai-hardens-atlas-browser-security-as-prompt-injection-threats-persist/)).

The engineering answer is to make a hijacked model harmless rather than trying to make the model unhijackable. Microsoft's operating-system design for Copilot Actions is the reference. Agents run under their own standard Windows account in a separate "agent workspace", can reach only known folders without further authorization, are digitally signed so they can be revoked, and are off by default ([Microsoft Learn](https://learn.microsoft.com/en-us/windows/security/book/operating-system-agentic-security)). Relic's agent rules follow the same idea and are enforced in code, not in prompts:

- **Credentials:**
  - The model never receives passwords, one-time codes, TOTP seeds or cookies.
  - The user logs in themselves in a visible browser window, with their passkey, password manager and two-factor approval.
  - The agent then works inside that already-signed-in session, in a **dedicated, isolated browser profile** that is never the user's everyday profile.
  - Any re-authentication or CAPTCHA pauses the run and hands control back to the human.
- **Navigation:** each recipe carries a domain allowlist (for example only `takeout.google.com` and `accounts.google.com`).
- **Blocked actions:** the tool layer blocks composing email, payments, settings changes and deletion. A purge recipe that legitimately deletes something needs a separate, explicit user confirmation for each action.
- **No dangerous tools:** no arbitrary JavaScript evaluation and no shell access. The PleaseFix vector in Claude in Chrome was exactly such a tool.
- **Narrow inbox access:** the agent never reads the inbox broadly. It searches only for a specific "export ready" message from a known sender.
- **Audit log:** every action is logged with a screenshot, URL and timestamp, and the user can replay a run.
- **Local by default:** agents run on the user's machine, so sessions never leave the device.

### Phones: Android allows some automation, iOS almost none

On Android, Google's **AppFunctions** (Android 16+) lets apps expose functions that agents can call locally on the device. Google compares it to MCP. Gemini's integration was in private preview as of May 2026 ([Android Developers Blog](https://android-developers.googleblog.com/2026/02/the-intelligent-os-making-ai-agents.html); [9to5Google](https://9to5google.com/2026/02/25/android-appfunctions-gemini/)). It only helps if the target app exposes an export function, which most social apps won't. Open-source agents such as DroidRun drive apps through accessibility services or ADB. In an independent test of 65 real-world tasks, DroidRun had the highest success rate of the agents tested, at 43% ([AIMultiple](https://research.aimultiple.com/mobile-ai-agent)). But Play policy bans using the Accessibility API to autonomously plan and execute actions, while allowing deterministic rule-based automation ([Play Console Help](https://support.google.com/googleplay/android-developer/answer/10964491?hl=en)). So an LLM-driven phone agent can ship only outside Play, through F-Droid or direct download, where Android's restricted-settings gate adds friction. On iOS, there is no general way for a third-party agent to drive other apps. Automation is limited to App Intents and Shortcuts, and reports conflict on how far Apple's own personal-context Siri had shipped by mid-2026 ([9to5Mac](https://9to5mac.com/2026/02/08/ios-26-4-heres-when-apple-will-release-the-first-beta/); [PlainAI](https://plainai.aguidetocloud.com/changes/apple-intelligence-siri-shipped/)). Because nearly every export flow also exists on the web, **Relic's agents should run on the desktop and treat phones as notification and approval devices.**

### Platforms push back, but the law currently favors the user's own agent

US case law has narrowed the anti-hacking theories:

- **Van Buren (2021):** the Supreme Court read the federal Computer Fraud and Abuse Act (CFAA) as a "gates-up-or-down" question of access, not a question of misuse ([Farella Braun + Martel](https://www.fbm.com/raven-quesenberry/publications/what-recent-rulings-in-hiq-v-linkedin-and-other-cases-say-about-the-legality-of-data-scraping/)).
- **Meta v. Bright Data (January 2024):** logged-off scraping of public data did not breach Meta's terms. The ruling turned on being logged off, and a logged-in user is bound by the terms of service ([Farella Braun + Martel](https://www.fbm.com/technology/publications/major-decision-affects-law-of-scraping-and-online-data-collection-meta-platforms-v-bright-data/)).
- **Amazon v. Perplexity:** a district court enjoined Perplexity's Comet agent from password-protected Amazon accounts in March 2026. **News reports say a Ninth Circuit panel vacated that injunction in August 2026**, finding Amazon unlikely to succeed on its CFAA and state-law claims because the agent acts on the user's behalf. The ruling is preliminary and limited to the current record, and the notes did not read the opinion itself ([Gigazine](https://gigazine.net/gsc_news/en/20260311-amazon-win-court-perplexity-comet); [Law360](https://law360.com/articles/2468857)).

Even so, platforms enforce their terms with account locks, and disguise is what provokes them. Amazon's suit alleged that Comet posed as ordinary Chrome. Cloudflare removed Perplexity from its Verified Bots program after accusing it of spoofing a Chrome user agent and rotating IP addresses ([Decrypt](https://decrypt.co/333479/cloudflare-perplexity-ai-stealth-crawlers-website-blocks?amp=1)). The industry's answer is **Web Bot Auth**: agents sign their requests with RFC 9421 HTTP Message Signatures, using a key published at a well-known URL. Cloudflare supports it, and AWS WAF added support in November 2025. It is still an IETF draft ([Stellagent](https://stellagent.ai/insights/web-bot-auth-cloudflare-ietf); [PPC Land](https://ppc.land/cloudflare-unveils-registry-format-for-bot-and-agent-authentication/)).

Relic's position:

- **Strongest legal footing:** the user's own account, the user's own data, the user's own device and home IP address, and only the official export flows, run at human pace.
- **No disguise:** Relic never spoofs. When an agent runs in the user's real browser, it is the user acting. If Relic ever runs anything from a cloud server, it identifies itself with Web Bot Auth.
- **Official routes first:** Relic prefers official APIs and data-portability endpoints wherever they exist, and uses UI agents only as a fallback.

## The vault must survive malware already running as you

Microsoft's Recall is the case study for securing this kind of archive. It was announced in 2024 with a database that could be read without decryption. Alex Hagenah's TotalRecall tool demonstrated this, and Microsoft delayed the feature ([Malwarebytes](https://www.malwarebytes.com/blog/news/2024/06/microsoft-recall-snapshots-can-be-easily-grabbed-with-totalrecall-tool)). The redesign made it opt-in. Keys are held in the TPM (the PC's hardware security chip) and bound to Windows Hello Enhanced Sign-in Security. Processing runs inside a VBS enclave, a hypervisor-isolated area, and Hello is required to view snapshots ([Windows Blog](https://blogs.windows.com/windowsexperience/2024/09/27/update-on-recall-security-and-privacy-architecture/)).

It still leaked. Kevin Beaumont reported that "you can just read the database as a user process", with no antivirus or EDR alert ([CSO Online](https://www.csoonline.com/article/4159643/microsofts-windows-recall-still-allows-silent-data-extraction.html)). **TotalRecall Reloaded (April 2026) obtained decrypted screenshots and OCR text by targeting the timeline-rendering process after the user had unlocked it with Hello.** Microsoft's security response center (MSRC) closed the report as "Not a Vulnerability… within the current, documented security design" ([TotalRecall](https://github.com/xaitax/TotalRecall)). The write-up is internally inconsistent on some process-protection details, and Microsoft disputes the framing. Testers also found Recall capturing credit-card and Social Security numbers despite its filters ([Engadget](https://engadget.com/ai/brave-and-adguard-now-block-microsoft-recall-by-default-152601475.html)).

The lesson is that **encrypting data at rest does not stop code running as the user once the data is decrypted for display.** So the viewer, not just the disk, is the asset to protect.

Relic's threat model, in priority order:

1. **Infostealers running as the user.** The macOS stealer AMOS alone accounted for nearly 40% of Sophos's macOS protection updates in 2025 ([Sophos](https://www.sophos.com/en-us/blog/why-amos-matters-the-macos-malware-stealing-data-at-scale)).
2. **Someone close to the user who knows the device password.**
3. **Prompt injection through MCP or the agents.**
4. **Leaks from sync or backup.**
5. **Policy change after an acquisition** (the Rewind precedent).

The countermeasures map onto those threats:

- **Keys and storage:**
  - Vault keys are bound to hardware and to biometric unlock (Secure Enclave and Keychain on macOS, TPM and Hello on Windows, Android Keystore).
  - Data is encrypted per segment, so only what the user is viewing gets decrypted.
  - Decrypted data lives briefly in memory and is never written as plaintext temporary files.
- **Separated processes:**
  - Capture, indexing and viewing run as separate processes.
  - The capture process can write to the vault but not read it.
  - The indexer has no network access.
  - The viewer is a small, signed process that uses the platform's hardening (hardened runtime and library validation on macOS, process mitigation policies on Windows), re-authenticates the user for sensitive scopes, and locks when idle.
- **Redact before indexing:** pattern matching plus a named-entity recognition model removes card numbers, national IDs (including Korean resident registration numbers), API keys and tokens before anything is indexed.
- **Exclude sensitive sources by default:** password managers, banking apps, private or incognito windows, secure text fields, and any window that has opted out of capture.
- **Local-first behavior:** no telemetry of content, a one-click wipe, and export in open formats. Screenpipe ships PostHog and Sentry telemetry on by default ([Screenpipe README](https://github.com/screenpipe/screenpipe)), which is a contrast Relic can market.

Storage follows the user's stated preference: **the user's own drive or NAS plus an encrypted offsite copy, not trusted circles.**

- **On the LAN:** the laptop's vault replicates to a NAS or home box as encrypted, content-addressed segments.
- **Offsite:** the NAS pushes client-side-encrypted snapshots to any S3-compatible bucket, so the provider holds only ciphertext.
- **Remote access:** devices can reach the home box through Tailscale or Iroh-style hole-punched connections ([Tailscale blog](https://tailscale.com/blog/peer-relays-ga); [iroh blog](https://iroh.computer/blog/the-road-to-iroh-1-0)).

The earlier storage research identified **key loss as the main way users lose data under end-to-end encryption**. So Relic needs a printed recovery code and a tested restore drill, not just encryption. Restores should be tested regularly, because a backup that has never been restored is only a hope.

## Harvesters map the territory, and Relic takes only the consented routes

The data-collection industry has already shown which categories of activity data exist on a person's own device and which collection methods work. Relic's job is to keep the categories, discard the covert methods, and choose the route the operating system grants openly to the device owner. This section stays at the architectural level on purpose. **Relic never reads credentials, cookies, session tokens, saved passwords or keys, and never defeats encryption or capture protections.**

### What exists on your device, and the consented route to a copy

| Activity category | How the harvesting industry gets it | Relic's consented route |
|---|---|---|
| Web browsing and AI chats | All-sites extensions that override page network functions. Urban VPN Proxy (6M+ users, Google "Featured" badge) captured full chats on ChatGPT, Claude, Gemini and others, whether or not its VPN was on ([CSO Online](https://www.csoonline.com/article/4106949/featured-urban-vpn-caught-stealing-private-ai-chats.html); [CyberInsider](https://cyberinsider.com/free-vpn-chrome-extensions-with-8-million-downloads-log-ai-chats/)) | An open-source companion extension with optional host permissions requested **per site at runtime**, a visible badge, per-site pause, and output only to the local app (native messaging) |
| Clickstream | Panel extensions such as Similarweb's, which disclose "domains you browse" ([Firefox Add-ons](https://addons.mozilla.org/fr/firefox/addon/10548)) | The extension history, tabs and navigation APIs; or a read-only copy of the browser's history database, made with the user's grant. Never the cookie or login stores |
| Location | Advertising SDKs and the bid stream. The Gravy Analytics breach exposed tens of millions of timestamped points tied to device IDs ([TechCrunch](https://techcrunch.com/2025/01/13/gravy-analytics-data-broker-breach-trove-of-location-data-threatens-privacy-millions/)) | Relic's own foreground location permission with a persistent notification, or imports such as OwnTracks or Google Timeline exports |
| Notifications and messages | Stalkerware abusing Android accessibility services ([arXiv 2508.02454](https://arxiv.org/html/2508.02454v1)) | NotificationListenerService (a special grant the user approves; lossy); macOS `chat.db` with Full Disk Access; official chat exports |
| Network activity | Panel VPNs, and the 2019 Facebook Research app's root certificate, which exposed private messages and web activity ([Gizmodo](https://gizmodo.com/facebook-is-paying-teens-to-install-a-research-app-that-1832182370)) | A **metadata-only** on-device VPN (the TrackerControl model: no root, no external server, no decryption of TLS) for a "who talks to whom" ledger ([TrackerControl](https://trackercontrol.org/)). No man-in-the-middle certificate, ever |
| Screen content | Employee monitors with interval screenshots, OCR and live view ([TechRadar](https://www.techradar.com/reviews/teramind)); Recall | The capture engine above, run by the owner, with no live view and no remote viewer |
| Cross-app identity | Meta and Yandex apps listening on localhost ports to link web browsing to app identities ([IMDEA Networks](https://networks.imdea.org/research-co-led-by-imdea-networks-discovers-a-privacy-abuse-involving-meta-and-yandex-bridging-persistent-identifiers-to-browsing-histories/)) | None. Relic does no identity bridging or fingerprinting. Instead, the Gravy record format (device ID, coordinates, time, app, IP) is a checklist of what to **request back** from companies through data-subject requests |
| OS-vendor indexes | Recall's database, Apple's semantic index, Android System Intelligence | Not readable by third parties, and deliberately so ([Google PCC paper](https://arxiv.org/pdf/2209.10317)). Relic replicates the capture with its own consented pipeline, and imports Recall's official EEA export where available |
| Authenticators | Infostealers such as Lumma and AMOS target browser credential stores, the macOS Keychain, wallets and messaging session tokens ([Red Canary](https://redcanary.com/threat-detection-report/threats/lummac2); [Sophos](https://www.sophos.com/en-us/blog/why-amos-matters-the-macos-malware-stealing-data-at-scale)) | **Never touched.** Messaging history comes from official exports, not from copying session tokens |

The rule this table encodes: **Relic reads content and activity stores (history, messages, notes) only with explicit OS-level grants such as Full Disk Access or a file picker, and never reads authenticators.** A tool that crosses that line behaves like AMOS or Lumma, and security software should treat it that way. Relic should aim to be classified as legitimate because of how it is designed, never by evading detection.

### Consent failures Relic must not repeat

Each of the industry's scandals points to a specific product rule:

- **Hidden collection:** Urban VPN's capture ran on a hard-coded flag that users could not switch off, and was added in a silent update ([BankInfoSecurity](https://www.bankinfosecurity.com/urban-vpn-proxy-spies-on-ai-chatbot-conversations-a-30368)). **Rule:** Relic has no hidden collection flags and no remotely enabled capture.
- **Collection beyond the stated purpose:** Honey is alleged to have replaced creators' affiliate tags even when it found no coupon. These are allegations, not findings ([Android Authority](https://www.androidauthority.com/honey-extension-scamming-users-3510942)). **Rule:** collect only for the feature the user turned on.
- **Inherited trust after a sale:** "Save image as Type" (1M+ users) became spyware after it was sold ([PCWorld](https://www.pcworld.com/article/3092299/my-most-useful-chrome-extension-was-stealing-my-data-for-years.html)), and the QuickLens extension turned malicious after its sale ([BleepingComputer](https://www.bleepingcomputer.com/news/security/quicklens-chrome-extension-steals-crypto-shows-clickfix-attack/amp/)). Updates install silently, so a new owner inherits the users' trust. **Rule:** a public non-transfer pledge and reproducible builds.
- **Developer accounts as an attack surface:** in the Cyberhaven compromise (December 2024), attackers phished a developer and pushed a malicious update to about 2.6 million users across roughly 35 extensions ([GovInfoSecurity](https://www.govinfosecurity.com/36-chrome-extensions-compromised-in-supply-chain-attack-a-27207)). **Rule:** hardware security keys on every publishing account, and a vault encrypted to a key held only by the native app, so a hijacked extension update cannot read the archive.
- **Consent obtained badly:** Facebook Research recruited 13–17-year-olds and got around App Store review with enterprise certificates ([TechCrunch](https://techcrunch.com/2019/02/21/facebook-removes-onavo/amp)). Google's Screenwise used the same certificate route and apologized ([EFF](https://www.eff.org/deeplinks/2019/02/google-screenwise-unwise-trade-all-your-privacy-cash)). **Rule:** no minors, no getting around app-store policy, and a plain-language explanation of what each capture method can see.
- **Data leaving the user's control:** the FTC fined Avast $16.5M for selling re-identifiable browsing data collected through its antivirus and extensions ([Perkins Coie](https://perkinscoie.com/insights/blog/ftc-obtains-165m-avast-sale-sensitive-data)). Gravy's breach shows what happens to centralized troves ([TechCrunch](https://techcrunch.com/2025/01/13/gravy-analytics-data-broker-breach-trove-of-location-data-threatens-privacy-millions/)). **Rule:** no server-side copy exists to sell or breach.
- **Default-on capture:** Recall's original default-on design caused a backlash that still shapes how people see it. Signal, Brave and AdGuard now block it by default ([Engadget](https://engadget.com/ai/brave-and-adguard-now-block-microsoft-recall-by-default-152601475.html)). **Rule:** every capture source is opt-in.

### Anti-stalkerware design requirements

The capture methods Relic uses are the same ones monitoring software uses. Teramind logs screenshots, screen recordings, OCR and live view ([TechRadar](https://www.techradar.com/reviews/teramind)). What separates a personal tool from stalkerware is **who installs it, whether the recorded person knows, and whether the data can reach someone else**. The Coalition Against Stalkerware, founded in 2019 by EFF, antivirus vendors and advocacy groups, maintains a shared definition and detection criteria ([EFF](https://www.eff.org/press/releases/eff-antivirus-companies-and-human-rights-groups-launch-coalition-combat-stalkerware)). Relic should engage with the Coalition before launch.

Relic's non-negotiable requirements:

1. **No hidden mode.** A persistent menu-bar or tray indicator and a launcher icon are always present, and the app cannot be renamed or disguised.
2. **Owner-only setup.** Setup happens on the device itself, gated by the device owner's biometric or passcode, and is re-confirmed periodically. The macOS monthly prompt helps here.
3. **No remote viewing.** No dashboard lets one person view another person's record. The archive opens only on the owner's own authenticated devices, and Relic has no feature for sharing a live view.
4. **No keystroke logging.** Snapshots are triggered after the user pauses typing, never per keystroke.
5. **Easy removal.** A single, discoverable uninstall wipes the app, its keys and its vault.
6. **No marketing for watching others.** Relic is never marketed to monitor partners, children or employees.
7. **Visible on Android.** No sideload-only accessibility capture.

## Official exports fill in the past but cannot drive the product

Imports matter for backfill, meaning the years before Relic was installed, and for data that never appears on screen. A compact map follows. Many details come from search summaries rather than primary pages, so exact numbers should be re-checked on each service's own documentation.

| Source | Best official route (Oct 2026) | Key limits |
|---|---|---|
| Google (all) | Takeout scheduled every 2 months for a year ([Google Help](https://support.google.com/accounts/answer/3024190?hl=en)); Data Portability API with 30- or 180-day consent and daily exports, filterable by date ([Google DPA](https://developers.google.com/data-portability/user-guide/time-based)) | API limited to EEA/UK/CH (US not confirmed); Takeout links expire in about 7 days |
| Google Photos | Takeout, with recurring incremental exports since June 2026 ([WinBuzzer](https://winbuzzer.com/2026/06/07/google-photos-makes-takeout-exports-recurring-backups-xcxwbn/)) | No full-library API since March 2025 |
| Meta (FB/IG) | Accounts Center export in JSON, via deep link ([Meta changelog](https://developers.facebook.com/docs/data-portability/changelog)) | Must download within 4 days ([Meta Help](https://www.meta.com/help/artificial-intelligence/1314808549771571/)); no personal-account API; end-to-end encrypted Messenger chats need a separate PIN-gated download |
| TikTok / LinkedIn | DMA portability APIs ([TikTok](https://developers.tiktok.com/products/data-portability-api/); [Microsoft Learn](https://learn.microsoft.com/en-us/linkedin/dma)) | EEA/UK (TikTok) and EEA/CH (LinkedIn) only; developer review required |
| X | Pay-per-use API; reading your own data costs about $0.001 per resource ([opentweet.io](https://opentweet.io/how-to/x-api-pay-per-use-explained)) | Third-party pricing figures, partly conflicting |
| Spotify | Extended streaming history (whole account lifetime) | Up to 30 days to arrive ([mystats.music](https://mystats.music/guides/spotify-extended-history)) |
| Korea (Naver, Kakao, etc.) | PIPA right to request transmission of personal data, extended to all sectors; large private companies are covered from 20 Feb 2027 ([ETNews](https://www.etnews.com/20260210000384); [Nate News](https://m.news.nate.com/view/20260811n27612)) | API-based; agents that scrape may only receive data in ways agreed in advance; the route for an app to become a recipient is unclear |
| Email | Gmail through OAuth (or an app password) **with the user's own OAuth client running locally**, which avoids Google's CASA security assessment required of hosted apps ([Nango](https://docs.nango.dev/integrations/google-security-review)); Outlook.com through OAuth only ([n8n docs](https://docs.n8n.io/integrations/builtin/credentials/imap/outlook/)); Daum and Naver need two-step verification plus an app password ([Kakao notice](https://mail-notice.kakao.com/mboard/en/notice/79)) | Legacy-password IMAP to Google ended 14 March 2025 ([Google Admin Help](https://knowledge.workspace.google.com/admin/sync/transition-from-less-secure-apps-to-oauth)); OAuth clients in "testing" mode may expire refresh tokens after 7 days (**unverified**) |
| iMessage | Read `chat.db` on the user's Mac with Full Disk Access (the imessage-exporter approach) ([README](https://raw.githubusercontent.com/ReagentX/imessage-exporter/develop/README.md)) | Needs a Mac; for iOS-only users, an unencrypted backup |
| Telegram | Telegram Desktop's official JSON export ([Telegram](https://core.telegram.org/import-export)) | Desktop app required |
| Signal | Signal's own on-device backups, which can be stored on any drive ([mjtsai](https://mjtsai.com/blog/2025/11/28/secure-signal-backups/)) | Relic does not read Signal's database key |
| WhatsApp / KakaoTalk | Per-chat "Export chat"; KakaoTalk's per-chat text export ([Kakao CS](https://cs.kakao.com/helps_html/1073182729?locale=en)) | Manual; KakaoTalk's built-in backup is text-only and expires after 14 days; live reverse-engineered clients risk bans |
| Slack (free plan) | Workspace export (public channels only) | Messages older than one year are deleted on a rolling basis ([Zulip](https://blog.zulip.com/2025/07/24/who-owns-your-slack-history/)) |

Two automation facts shape this layer. **No platform pushes "your export is ready" to a webhook.** So the agent's job is limited to deep-linking the user into the request page, watching for one specific email from a known sender, and prompting the user to complete the logged-in download before the link expires. **For US users, continuous official feeds barely exist**, which is why on-device capture has to be the engine and imports the supplement.

## Reuse permissive parts, use copyleft projects as references, and compete with Screenpipe

The GitHub landscape on 16 October 2026 offers good building blocks, but **licenses constrain reuse more than code quality does**. Most of the strong products are AGPL or GPL, and **Screenpipe is now source-available under the "Screenpipe Commercial License", not MIT**. This corrects an earlier report. Personal and non-commercial use is free, and commercial use needs a paid license ([Screenpipe README](https://github.com/screenpipe/screenpipe)). Older third-party blogs still call it MIT. They are outdated.

| Use | Projects (license) | Notes |
|---|---|---|
| **Reuse directly (permissive)** | ActivityWatch (MPL-2.0) ([GitHub](https://github.com/ActivityWatch/activitywatch)); Dayflow (MIT) ([GitHub](https://github.com/JerryZLiu/Dayflow)); HPI and karlicoss exporters, Promnesia (MIT) ([GitHub](https://github.com/karlicoss/HPI)); browserexport, google_takeout_parser (MIT) ([GitHub](https://github.com/purarue/browserexport)); Datasette (Apache-2.0); Got Your Back (Apache-2.0) ([GitHub](https://github.com/GAM-team/got-your-back)); osxphotos, icloudpd, rclone, instaloader (MIT); yt-dlp (Unlicense); monolith (CC0); ArchiveBox (MIT) | ActivityWatch's watcher-plus-local-server event model is a proven foundation. Dayflow is the modern macOS reference, but its storage format and whether its LLM is local are unverified |
| **Call as a separate process or treat as reference (copyleft)** | imessage-exporter (GPL-3.0); gallery-dl (GPL-2.0); tdl (AGPL); Windrecorder (GPL-2.0); Timelinize (AGPL, "still unstable") ([GitHub](https://github.com/timelinize/timelinize)); Khoj, Karakeep, SingleFile, Immich, Dawarich (AGPL); Bichon, OpenArchiver (AGPL), Mail-Archiver (GPL-3.0) | A closed or commercial Relic would have to run these as separate command-line processes or reimplement them. An AGPL Relic could embed them |
| **Competitor / reference only** | Screenpipe (source-available, commercial) | Best-in-class technically: accessibility tree plus OCR, FTS5, MCP and "pipes". Now describes itself as a YC S26 company focused on "company computer work" and agent context |
| **Avoid** | Selfspy (dead since 2019), rem and Memento (dormant since 2024), OpenRecall (near-dormant), twitter-archive-parser (2022), Gmvault (2022), gphotos-sync (archived), GooglePhotosTakeoutHelper (dormant) | Formats have drifted, and the APIs some of them used are gone |
| **Avoid for policy reasons** | Tools that work by copying user session tokens or decrypting other apps' local databases with extracted keys (for example the token-based mode of DiscordChatExporter, whose README warns that automating user accounts breaks Discord's ToS ([README](https://raw.githubusercontent.com/Tyrrrz/DiscordChatExporter/master/Readme.md))) | They conflict with Relic's rule against touching authenticators. Use official data packages instead |

The open gaps are as useful as the building blocks. There is **no permissive, polished, cross-platform unified timeline**: Timelinize is AGPL and unstable, and HPI is for developers only. No maintained parsers exist for Meta's "Download Your Information" archives or for current X archives. Korean platforms (KakaoTalk, Naver) have almost no tooling, and mobile-first capture is missing. Each of these is a place where Relic can contribute upstream and earn community trust.

## Law favors capturing your own screen but restricts your microphone

**Screen capture of your own activity, for your own use, is low legal risk.** Under GDPR's household exemption it generally stays outside data-protection obligations as long as it remains personal. The notes did not retrieve the case law on that exemption, so counsel should confirm it, especially for anything shared or synced to an employer's cloud. **Audio is different.**

- **United States:** federal law requires the consent of one party to a recording. But about 11–13 states require every party's consent, commonly listed as CA, CT, DE, FL, IL, MD, MA, MT, NV, NH, PA and WA, with Michigan and Oregon disputed or partial. Interstate calls usually follow the stricter rule ([Layer3 Labs](https://www.layer3labs.io/guides/two-party-consent-states)).
- **South Korea:** under the Communications Privacy Protection Act (통신비밀보호법), recording a conversation you take part in is not a crime but can create civil liability under the "right of voice" (음성권). **Recording a conversation you are not part of carries 1–10 years in prison even if one party consented.** A 2022 bill to require all-party consent was proposed, and whether it passed is unconfirmed ([Segye Ilbo](https://www.segye.com/newsView/20220822516779)).

Relic's defaults follow from this:

- Audio is off.
- When turned on, it records only the user's own microphone.
- Each meeting gets a consent prompt or announcement helper.
- Warnings are location-aware.
- Relic never records a room while the user is away from the device.

Relic should actively use people's legal rights:

- **EU (GDPR):** access (Art. 15), erasure (Art. 17), portability (Art. 20) and the right to object (Art. 21) are the hooks for backfill and purge ([gdpr-info.eu](https://gdpr-info.eu/art-20-gdpr/)). Timing matters for Art. 21: noyb says Meta treated AI-training objections as effective only if filed before training started ([noyb](https://noyb.eu/sites/default/files/2025-05/noyb_cease%20and%20desist%20letter_Meta%20AI_pub.pdf)).
- **EU (DMA):** Art. 6(9) obliges gatekeepers to provide free, continuous, real-time portability to the user or to third parties the user authorizes ([EC DMA portal](https://digital-markets-act.ec.europa.eu/developer-portal/end-user-data-portability_en)).
- **California:** the CCPA/CPRA lets an app act as the user's **authorized agent** under 11 CCR §7063, though companies may still require the consumer to verify directly ([Cornell LII](https://law.cornell.edu/regulations/california/11-CCR-7063)). Consumer Reports' Permission Slip uses this model ([CR Innovation](https://innovation.consumerreports.org/?p=9066)). California's free **DROP** platform has handled data-broker deletions since January 2026, and brokers must process them every 45 days from 1 August 2026 ([CPPA](https://www.cppa.ca.gov/data_brokers/)). DROP covers data brokers only, not Google or Meta.
- **Korea (PIPA):** Art. 35-2 adds the transmission right described above. Third-party recipients may need to be authorized institutions, so a Korean Relic would likely have users download data to themselves rather than act as a recipient ([Mondaq](https://www.mondaq.com/data-protection/1295960/south-korea-passes-major-overhaul-of-data-protection-law)).

For agents, the risk lies in terms-of-service contracts and account enforcement, not in criminal hacking law, as discussed above.

**Purge should be a short, honest workflow, not a promise.** Relic should:

1. Confirm the local copy is complete.
2. Set each platform's AI-training toggles. These are fragmented: Gemini's "Keep Activity", LinkedIn's "Data for Generative AI Improvement", X's Grok setting, and ChatGPT's "Improve the model for everyone" ([humandatarights.org](https://www.humandatarights.org/guides/how-to-opt-out-of-ai-training/)).
3. File deletion or objection requests.
4. **Re-run an access request 90–180 days later to check that the deletion happened.**

Deletion is a multi-stage process. Google cites about 2 months to remove data from active systems and about 6 months for backups to expire, in a cloud context ([Google Cloud](https://docs.cloud.google.com/security/deletion)). Companies have also failed to honor it: the FTC fined Amazon $25M over Alexa recordings it said were deleted but kept ([MediaPost](https://www.mediapost.com/publications/article/385888/ftc-fines-amazon-25m-over-childrens-voice-record.html)). Users should be told plainly that opt-outs apply only going forward and that deletion cannot remove what a model already learned.

## Rewind's exit left a gap that only a local, open product can fill

Companies in this category have tended to end up inside a big platform:

- **Rewind/Limitless → Meta** (December 2025): capture switched off, and continuing users had to accept a new privacy policy ([TechCrunch](https://www.techcrunch.com/2025/12/05/meta-acquires-ai-device-startup-limitless/)).
- **Bee → Amazon** (July 2025): Amazon did not confirm that Bee's no-audio-storage protections would remain ([Entrepreneur](https://www.entrepreneur.com/business-news/amazon-acquires-bee-startup-behind-eavesdropping-wearable/494971)).
- **Humane → HP** (about $116M): the AI Pin was bricked in February 2025 ([Axios](https://www.axios.com/2025/02/18/humane-ai-pin-shut-down-hp)).
- **Consumer privacy apps:** Jumbo (to Coalition) and SayMine (to McAfee) were absorbed into security suites ([TechCrunch](https://techcrunch.com/2023/07/12/cyber-insurance-startup-coalition-acquires-privacy-assistant-jumbo/); [Jerusalem Post](https://www.jpost.com/business-and-innovation/article-875099)).

The remaining field:

| Product | What it is (Oct 2026) | Gap Relic fills |
|---|---|---|
| **Screenpipe** | Source-available; YC; about $3.4M raised ([startups.fm](https://startups.fm/startups/screenpipe)); telemetry on by default; aimed at company workflows. Its pricing is reported inconsistently (lifetime license vs subscriptions) ([MemX](https://memx.app/alternatives/rewind-ai/)) | A consumer product with open code and no telemetry |
| **Microsoft Recall** | Built into the OS; requires a Copilot+ PC, so **fewer than 10% of Windows 11 PCs can run it** ([GeekWire](https://www.geekwire.com/2026/one-year-after-its-rocky-launch-microsofts-windows-recall-still-raises-security-red-flags/)); export only in the EEA | Cross-platform, with agents, and the user owns the data |
| **Dayflow** | MIT; macOS; a timeline-style work journal with about 7.3k GitHub stars ([GitHub](https://github.com/JerryZLiu/Dayflow)) | Search, agents, imports and a vault |
| **Timelinize** | AGPL; imports exports into a timeline; unstable schema | Live capture and a consumer-grade experience |
| **Plaud / Omi** | Wearable note-takers; Plaud is profitable with 2M+ users ([Bloomberg](https://www.bloomberg.com/news/articles/2026-06-16/plaud-plans-new-wearable-as-ai-note-taking-startup-eyes-500-million-in-sales)) | Screen activity, and no cloud dependency |
| **Vana** | Pools user data to license for AI training ([Vana](https://vana.org/posts/vana-raises-funding-to-build-user-owned-ai-and-overcome-the-data-wall)) | The opposite stance: Relic withholds data from training |

Relic's positioning: **"Your memory, on your machine. Nobody else gets a copy."** It is aimed at the people the Pew numbers describe: they want AI memory, and they distrust whoever holds it.

The business model should follow the lesson of the earlier storage research: a free, open app plus paid encrypted offsite backup and sync, an optional preconfigured home box, and no venture-driven growth without revenue. A maintained library of agent recipes is a natural recurring add-on, because platforms change their export flows constantly. The acquisition pattern is also Relic's own risk. Open code, open formats, a non-transfer pledge for the browser extension, and data that never touches Relic's servers are what make "you own it" credible even if the company is sold.

## A reference architecture and an 18-month roadmap

| Layer | Components | Key design rule |
|---|---|---|
| Capture | Per-OS capture daemon (signed app); event triggers; perceptual-hash dedupe; accessibility text → native OCR → ONNX OCR; optional small VLM; mic-only ASR (Parakeet / Whisper turbo, VAD-gated); browser extension (per-site permissions); Android companion (notifications, location, usage) | Honor every opt-out signal; visible indicator; never touch authenticators |
| Storage | Raw segments (H.265/AV1 video, JSON events, raw export files) as immutable, content-addressed blobs; tiered retention | Raw data is the source of truth; formats are open |
| Index | SQLite + FTS5 (trigram); sqlite-vec or LanceDB embeddings; redaction before indexing | Indexer runs with no network access |
| Intelligence | Local 3–8B LLM (llama.cpp/MLX/Ollama); daily summaries; Q&A | Local by default; cloud only opt-in, on redacted data |
| Access | Hardened viewer; read-only MCP server with scopes and approval; audit log | Protect the viewer, not just the disk |
| Agents | Playwright recipes + local VLM repair; isolated profile; domain allowlist; blocked destructive actions; human-handled login and 2FA; replayable log | Hijacked model ⇒ bounded damage |
| Vault & backup | Hardware-bound keys (Secure Enclave/TPM/Keystore); NAS replication; client-encrypted offsite snapshots to S3-compatible storage; recovery code | Key loss is the main way users lose data, so practice recovery |
| Rights | Export importers; AI-opt-out inventory; deletion requests with re-verification | "Request + verify + re-check", not "deleted" |

The roadmap, with rough timings:

| Phase | Timing | Scope |
|---|---|---|
| **Phase 0** (spike) | Months 0–2 | Benchmark accessibility-text coverage and OCR on a Korean+English test set. Measure CPU, battery and storage of event-driven capture on Apple Silicon and on a mid-range Windows laptop. Threat-model the viewer. |
| **Phase 1** (MVP) | Months 2–6 | macOS app with event-driven capture, accessibility text plus Vision OCR, tiered storage, encrypted vault with Touch ID, timeline and search, local LLM Q&A, and a read-only MCP server. Browser extension for chosen sites. Imports for iMessage, email (via the user's own OAuth client) and Takeout/Meta/Spotify archives. **Three agent recipes**: request Google Takeout, request a Meta export, request Spotify extended history. |
| **Phase 2** | Months 6–12 | Windows build (Windows.Graphics.Capture, UI Automation). NAS replication and encrypted offsite backup (the first paid tier). Opt-in mic-only transcription with consent tooling. AI-opt-out inventory and purge workflow with re-verification. EEA Data Portability API connectors and Recall-export import. |
| **Phase 3** | Months 12–18 | Linux (Wayland portal). Android companion: notifications, location and usage, with screen capture only in sessions the user starts. Recipe marketplace and Korean connectors timed for the PIPA expansion on 20 February 2027. External security audit and engagement with the Coalition Against Stalkerware. |

The MVP's success test is concrete: one person can search everything they saw and read last month in under a second, on a laptop with no network access, with credentials provably never captured, at a storage cost under about 10 GB a month.

## Conclusion

Building Relic is now mostly a security problem. The capture problem has largely been solved, and the agent problem has become a question of containment. The project that wins will not be the one with the best OCR. It will be the one that can show, with open code and a design that limits damage, that its archive is useless to an infostealer, its agents are harmless when hijacked, and nobody can quietly use it to watch someone else. Recall's experience shows that operating-system privileges don't settle these questions. Screenpipe's experience shows that commercial pressure pulls this category toward enterprise surveillance of work. That leaves room for a consumer tool that treats owning the data and constraining itself as the product.

The deeper implication is that Relic's moat is a structural incentive, not a technology. Meta, Amazon, Microsoft and Apple all want the same personal context, and each has commercial reasons to keep a copy. A local-first product with no server copy is the only kind that can credibly promise not to. Until Apple opens iOS to this kind of agent, the desktop is where that promise can be kept. Relic should own that position before the platforms close it.
