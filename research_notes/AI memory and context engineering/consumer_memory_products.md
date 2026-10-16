# Consumer AI products: personal memory and context architectures (as of October 16, 2026)

Method note: In this session WebFetch failed with a DNS error on every primary domain I tried (openai.com, about.fb.com, research.meta.ai, techcrunch.com). As a result, every finding below comes from **web-search result summaries**. Where a summary cited a primary page, I link that page, but I did not read its full text. Each finding is labelled with the kind of source behind it:
- **[OFFICIAL]**: the company's own page or help center
- **[PRESS]**: reputable news coverage
- **[BLOG/RE]**: third-party blog, reverse-engineering or vendor content
- **[BACKGROUND]**: my prior knowledge, not re-verified this session

The report writer should treat [BLOG/RE] and [BACKGROUND] items accordingly.

---

## 1. "Dots" = OpenAI dots (primary), with Dot by New Computer as a side note

### Takeaway
Per the user's correction, "Dots" means **OpenAI's "dots"**. OpenAI announced them at DevDay on **September 29, 2026** ([OpenAI: Introducing dots](https://openai.com/index/introducing-dots/)). Dots are always-on ChatGPT agents running GPT-6 Astra. Each dot gets its own cloud computer and browser, and keeps working between chats.

Dots memory has four defining properties:
- **Write path:** memory is seeded from the user's existing ChatGPT memories. The dot then accumulates its own context from conversations and from connected apps.
- **No visibility:** per-dot memory currently **cannot be viewed or edited**.
- **Deletion:** deleting a dot removes the dot's own context only. Files and ChatGPT memories need separate deletion.
- **Retention:** **revoking an app stops future access but does not erase what the dot already learned from it.**

### Cited Findings
- **Launch:** OpenAI officially announced dots ("Introducing dots") at DevDay, September 29, 2026. [OFFICIAL] [OpenAI](https://openai.com/index/introducing-dots/); [PRESS] [TechCrunch](https://techcrunch.com/2026/09/29/openai-launches-dots-its-bubbly-agentic-avatar/); [MarkTechPost](https://www.marktechpost.com/2026/09/29/openai-launches-dots-always-on-gpt-6-astra-agents-that-work-from-their-own-cloud-computers/); [Unite.AI](https://www.unite.ai/openai-rolls-out-dots-agents-powered-by-gpt-6-astra-in-chatgpt/)
- **What a dot is:** it runs on GPT-6 Astra, has its own cloud computer and browser, works toward the user's goals around the clock, and connects to 4,000+ apps through OpenAI's plugin ecosystem. TechCrunch describes it as a "bubbly agentic avatar." Engadget reports that users will later be able to control several dots, and VentureBeat covers "ChatGPT Space," where dots collaborate with human teams. [PRESS] [MarkTechPost](https://www.marktechpost.com/2026/09/29/openai-launches-dots-always-on-gpt-6-astra-agents-that-work-from-their-own-cloud-computers/); [Engadget](https://www.engadget.com/2272230/dots-are-openais-new-personal-agents-and-soon-youll-be-able-to-control-several-of-them/); [VentureBeat](https://venturebeat.com/technology/openai-launches-dots-always-on-ai-agent-coworkers-and-chatgpt-space-where-they-can-collaborate-with-human-teams)
- **Memory sources:**
  - Context comes from conversations, ChatGPT memories and connected apps.
  - A dot receives the user's existing ChatGPT memories, then forms its own, including from connected apps the user has not asked it about.
  - [BLOG] [Vellum](https://www.vellum.ai/blog/official-openai-dots-breakdown); [Codersera](https://codersera.com/blog/openai-chatgpt-dots-guide-2026/); [iGeeksBlog](https://www.igeeksblog.com/openai-launches-dots/)
- **Memory controls:**
  - Individual dot memories cannot currently be viewed or edited.
  - Deleting a dot removes its own context. Separately stored files and ChatGPT memories need their own controls.
  - Disconnecting an app stops future access but keeps information already gathered.
  - [BLOG] [Vellum](https://www.vellum.ai/blog/official-openai-dots-breakdown); [NeuralTrust](https://neuraltrust.ai/blog/chatgpt-agent-security)
- **Permissions and safety:**
  - App permissions are shared across Dots, ChatGPT, Work and Codex.
  - Local computer access is off by default.
  - Background "proactive research" uses read-only tools that cannot send messages, edit connected apps or control a browser or desktop.
  - "Custom Rules" allow, block or require approval for specific actions, and sensitive steps such as password changes stay with the user.
  - [BLOG] [NeuralTrust](https://neuraltrust.ai/blog/chatgpt-agent-security); [kingy.ai](https://kingy.ai/blog/openai-dots-guide/); [AlphaSignal](https://alphasignal.ai/news/openai-s-dots-turns-chatgpt-into-a-persistent-agent-that-works-while-you-sleep)
- **Where data lives:** Enterprise, Edu and Healthcare workspaces need an admin to enable dots, with three key settings off by default. Dots **do not support data residency**, and they exclude FedRAMP and EKM workspaces. [BLOG] [NeuralTrust](https://neuraltrust.ai/blog/chatgpt-agent-security)
- **Availability:** the first dot is included with ChatGPT Pro or Business Premium, users must be 18+, and rollout is gradual in select markets. Introductory usage limits do not establish long-run cost. [BLOG] [MindStudio](https://www.mindstudio.ai/blog/openai-dots-agent-pricing); [Codersera](https://codersera.com/blog/openai-chatgpt-dots-guide-2026/)
- **Unverified claim:** one source says Astra shipped after OpenAI scrapped "GPT-6.1 Astra" over safety concerns. I could not corroborate this. [BLOG] (from search summary, source unclear)

### Inferences
- Dots are the agentic consumer of ChatGPT's memory stack (Dreaming summary plus saved memories, section 3). They add a new **ambient write path**: background ingestion from connected apps. Per-dot memory stores, however, sit *outside* the inspectable memory summary that OpenAI introduced in June 2026, which is a regression in transparency.
- The way revocation fails to erase learned context mirrors Meta Muse's "forget doesn't delete source" issue (section 2). The industry pattern is that derived memory and source data have independent lifecycles.
- Dots are a natural evolution of ChatGPT Pulse (asynchronous background research, 2025) into a persistent agent with its own compute.

### Gaps
- I could not read the full OpenAI announcement or help pages because WebFetch was DNS-blocked in this session. Most privacy and retention specifics come from secondary blogs and need verifying against OpenAI's "Introducing dots" post, its getting-started guide and its safety post.
- Unknown: how a dot's memory is extracted and stored (summary, files or vector store), whether dot memories ever flow back into the main ChatGPT memory, and how memory is isolated between multiple dots.

### Side note: Dot by New Computer (not the target product)
- New Computer's long-term-memory companion app "Dot" announced its shutdown on September 5, 2025 and closed on October 5, 2025. Co-founders Sam Whitmore and Jason Yuan cited diverging product visions, and users had a month to export their data. Appfigures estimated about 24.5k lifetime iOS downloads, against the company's claim of "hundreds of thousands" of users. [PRESS] [TechCrunch](https://techcrunch.com/2025/09/05/personalized-ai-companion-app-dot-is-shutting-down); [Vaizle](https://insights.vaizle.com/news/popular-ai-companion-chatbot-dot-shuts-down-afters-founders-disagree/)
- "Dots Memories: your story" on Google Play is an unrelated photo-journaling app. [Google Play](https://play.google.com/store/apps/details?id=social.onelife&hl=en_US)

---

## 2. Meta: Muse (agent and models), Meta AI memory, Limitless

### Takeaway
"Muse" is a **Meta Superintelligence Labs family of models and a consumer agent**:
- Muse Spark, April 2026: the first model under Alexandr Wang
- The **Muse personal AI agent app**, September 2026
- **Muse Wonder / Wonder Full models**, October 12, 2026, featuring "Active Memory" and "Active Focus"

Muse memory is a user-editable **Memory file** plus supporting files. It can draw on Instagram and other Meta data. Forgetting is best-effort: a TIME investigation found that "forget" does not delete the source messages. Training on interactions is on by default (opt-out).

### Cited Findings
- **Muse Spark:** Meta's first AI model under Alexandr Wang, April 8, 2026. [PRESS] [Axios](https://www.axios.com/2026/04/08/meta-muse-alexandr-wang)
- **Muse agent:** Meta announced "Muse: The World's First Personal AI Agent Built for Everyone" in September 2026. [OFFICIAL] [Meta Newsroom](https://about.fb.com/news/2026/09/introducing-muse-personal-ai-agent/)
- **Agent capabilities:**
  - Remembers what matters to a person, so it can make unprompted suggestions and act on details mentioned only once. [PRESS] [AndroidHeadlines](https://www.androidheadlines.com/2026/10/meta-muse-wonder-ai-model-long-term-memory-upgrade.html)
  - A hands-on test found it reads Instagram data, prepares follower exports (capped at 749 accounts in the test), drafts Marketplace messages, uses a cloud browser, and suggests recurring work based on the user's interests. [BLOG] [joaoqueiros hands-on](https://www.ai.joaoqueiros.com/blog/meta-muse-free-ai-agent-instagram-whatsapp-cloud-computer)
- **Muse Wonder / Wonder Full (October 12, 2026):**
  - "Active Memory" keeps context across conversations over days, weeks and months, so users don't re-explain themselves (Alexandr Wang). "Active Focus" handles multi-step work.
  - Muse Wonder is available through the Meta Model API and Muse Code. Wonder Full is for Muse Code subscribers. Wonder will power the Muse assistant, initially for paid subscribers.
  - Meta claims SOTA results on memory and agentic benchmarks (self-reported).
  - [OFFICIAL/PRESS] [Meta research blog](https://research.meta.ai/blog/muse-wonder); [Axios](https://www.axios.com/2026/10/12/meta-new-ai-models-anthropic-openai); [PYMNTS](https://www.pymnts.com/news/artificial-intelligence/2026/meta-adds-memory-focus-new-frontier-models-agents/); [MindStudio](https://www.mindstudio.ai/blog/meta-muse-wonder-launch)
- **User controls (Meta help center):**
  - You can ask Muse to forget a topic or set of interactions. It searches its memories and supporting files and removes matching information "as well as it can."
  - Meta states that after you delete something, Muse "may still remember information it learned from what you deleted."
  - Data download is under Settings > Data controls, and the Memory file can be edited or deleted directly.
  - [OFFICIAL] [Meta Help: How to manage your Muse data](https://www.meta.com/help/artificial-intelligence/2225571704857152/); summarized in [aiagentslibrary](https://www.aiagentslibrary.com/blog/meta-muse-memory/)
- **TIME investigation (October 6, 2026):** asking Muse to forget something does not necessarily erase the message where it was shared. Muse's internal instructions appear to tell the agent not to point this out. Meta told TIME that users "stay in control." [PRESS] [TIME](https://time.com/article/2026/10/06/meta-muse-ai-agent-privacy/)
- **Training and encryption:** training on interactions is opt-out. Meta has said encryption will come later in 2026 and is not yet available. [BLOG] [toolscout](https://toolscout.ai/news/meta-muse-free-ai-agent-privacy); [notis.ai](https://www.notis.ai/blog/meta-muse-privacy/)
- **Limitless:** Meta acquired Limitless (formerly Rewind) on December 5, 2025, and the team joined Reality Labs wearables. Rewind's screen and audio capture was disabled from December 19, 2025. EU and UK users had to export before deletion. Pendant sales stopped, with about a year of support for existing devices. [BLOG] [luci.memories.ai](https://luci.memories.ai/blog/rewind-ai-shut-down-on-device-replacement); [becomefluent](https://becomefluent.io/blog/2026-05/what-happened-to-limitless-pendant/)
- **Manus:** Manus is now "part of Meta," per a banner on Manus's own blog. [OFFICIAL] [Manus blog](https://manus.im/en/blog/Context-Engineering-for-AI-Agents-Lessons-from-Building-Manus)

### Inferences
- Muse's memory appears to be **file-based** (a "Memory file" plus "supporting files"), not an opaque vector store. That is similar in spirit to Claude's file-based memory and Manus's "file system as context."
- The decoupling between deleting a message and deleting the derived memory is the central privacy issue. Meta documents it officially in one direction (deleted messages may persist as memory), and TIME found it in the other (forgotten memories persist as messages).
- I found no evidence that Limitless pendant or Rewind data feeds Muse. The acquisition looks aimed at glasses and wearables.

### Gaps
- I found no source confirming whether Muse uses Facebook and Instagram activity (likes, follows) as *implicit* memory by default, as opposed to on-demand tool access.
- Meta AI app memory (2025) is uncorroborated this session. From [BACKGROUND]: in 2025 the Meta AI app could remember user-shared details and could personalize using Facebook and Instagram profile data and engagement for linked accounts. I also recall a 2025 "Discover feed" incident in which users inadvertently published chats.
- No independent replication of the Muse Wonder memory benchmarks.

---

## 3. OpenAI: ChatGPT memory, Dreaming (2026), Projects, Pulse, Atlas

### Takeaway
ChatGPT memory went through four main stages:
- **February 2024 [BACKGROUND]:** saved memories, a list of explicit facts.
- **April 2025:** "reference chat history."
- **June 4, 2026:** a rebuilt background-synthesis system, **"Dreaming" (V3)**. It reviews chat history after conversations end and rewrites a user-visible, editable **memory summary**. That summary is injected into context on every turn. Responses now show the source behind each memory.
- **August 2026:** Projects gained editable project-only memory.

Reverse-engineering from 2025 describes the injected context as four blocks. Treat this as dated.

### Cited Findings
- **Dreaming rollout:** started June 4, 2026 for Plus and Pro users in the US, with Free, Go and more countries to follow. It "automatically curate[s] memories in the background by referencing chat history" and "synthesize[s] its memory state" across conversations. [OFFICIAL/PRESS] [OpenAI: Dreaming](https://openai.com/index/chatgpt-memory-dreaming/); [PCWorld](https://www.pcworld.com/article/3158111/chatgpt-new-dreaming-feature-makes-it-way-better-at-remembering-you.html); [Neowin](https://www.neowin.net/news/openai-is-rolling-out-a-major-upgrade-to-chatgpt-memory/)
- **Memory summary page:** users can view an AI-generated summary of everything ChatGPT remembers, edit or correct it, and instruct which topics to bring up and when. On June 12, 2026, more memory-summary controls were added. [OFFICIAL] [ChatGPT release notes](https://help.openai.com/en/articles/6825453-chatgpt-release-notes); [webiano](https://webiano.digital/chatgpt-memory-summary-turns-personalization-into-something-users-can-inspect/)
- **Memory sources shown in answers:** when an answer uses memory, ChatGPT shows which past chat, saved detail, custom instruction or uploaded file it drew on. Secondary coverage dates this to a May 2026 release. [BLOG] [findskill](https://findskill.ai/blog/chatgpt-dreaming-memory-explained/); [knightli](https://knightli.com/en/2026/05/07/chatgpt-release-notes-memory-gpt-5-5-sheets/)
- **Performance claims:** recall is reported at 82.8%, up from 67.9% in 2025 (another source says up from 41.5%), and the system is said to be about 5x more efficient. **This 82.8% figure appears only in secondary sources.** [BLOG] [tech-insider](https://tech-insider.org/chatgpt-dreaming-v3-memory-update-2026/); [digitalapplied](https://www.digitalapplied.com/blog/chatgpt-memory-dreaming-v3-openai-2026-guide)
- **Retrieval mechanics (analysis, not official):** mem0 argues that ChatGPT does not search old chats per query. Instead, a summary of who you are, built from past chats, is loaded into context on every message. A GitHub research issue says it is unknown whether retrieval also happens at response time. **This is disputed.** [BLOG/RE] [mem0 on X](https://x.com/mem0ai/article/2071990201531118063); [theseus-research issue #26](https://github.com/TeaShaman-cyber/theseus-research/issues/26)
- **Projects:** with "project-only memory," ChatGPT uses chats from the same project but no memories or conversations from outside it. Since August 14, 2026, the setting can be edited after the project is created. [OFFICIAL] [ChatGPT release notes](https://help.openai.com/en/articles/6825453-chatgpt-release-notes)
- **Reverse-engineered 2025 architecture (dated):** four context blocks are appended to the system prompt.
  1. Interaction metadata (device, usage patterns)
  2. Recent conversation content: about 40 recent chats, user messages only
  3. Model set context: the explicit saved memories
  4. User knowledge memories: dense AI-generated summaries regenerated periodically from history, not visible or editable in settings at the time

  The analysis argued this is "bitter lesson"-style: no RAG over chats, just compressed summaries in a large context. [BLOG/RE] [Shlok Khemani, "ChatGPT Memory and the Bitter Lesson"](https://www.shloked.com/writing/chatgpt-memory-bitter-lesson); [Moh Yassin](https://mohyassin.substack.com/p/chatgpts-hidden-memory-layer-the)
- **Atlas browser memories (October 2025):** opt-in "browser memories" let ChatGPT recall pages and topics you have visited. They can be reviewed, archived or deleted, and a per-site toggle in the address bar blocks visibility, so no memories are created from blocked pages. One OpenAI page reportedly now says Atlas is deprecated (**unverified**). [OFFICIAL/PRESS] [Introducing ChatGPT Atlas](https://openai.com/index/introducing-chatgpt-atlas/); [Atlas release notes](https://help.openai.com/en/articles/12591856-chatgpt-atlas-release-notes); [Unite.AI](https://www.unite.ai/openai-launches-chatgpt-atlas-browser-with-agent-mode-and-memory/)

### Inferences
- OpenAI's trajectory runs from explicit fact lists, to opaque periodic summaries, to an **inspectable, editable synthesized profile with provenance**. Dreaming makes the previously hidden "user knowledge memories" layer visible, and it addresses the main transparency criticism from 2025.
- Dreaming's name and its offline, post-conversation synthesis resemble "sleep-time compute" and memory consolidation. Writes happen asynchronously, outside the live turn.

### Gaps
- **ChatGPT Pulse (September 2025)** came up in no search this session. From [BACKGROUND], unverified: Pulse was a Pro-first mobile feature that did asynchronous overnight research using memory, chat history, feedback and optional Gmail and Calendar connectors, delivering visual cards each morning.
- Whether Dreaming has fully replaced the "saved memories" list or coexists with it: sources conflict.
- The status of Atlas deprecation.

---

## 4. Anthropic Claude memory

### Takeaway
Claude has two mechanisms:
- **Memory:** a synthesized summary of the user, editable in Settings > Memory. [BACKGROUND] It is project-scoped, with per-project memory separate from general memory.
- **Chat search:** on-demand retrieval over past chats via tools.

Memory reached the **free plan on March 2, 2026**, together with an experimental **import tool** for memories from ChatGPT, Gemini and Grok.

### Cited Findings
- **Free plan and import (March 2, 2026):** memory came to free users along with an import tool. Users run a prompt in another assistant and paste its output into Claude's memory settings. The import is labelled experimental and produces a re-interpretation, not an exact copy. [PRESS/BLOG] [MacRumors](https://www.macrumors.com/2026/03/02/anthropic-memory-import-tool/); [PCWorld](https://www.pcworld.com/article/3076376/claude-can-now-import-chat-histories-from-chatgpt-and-other-ais.html); [YouMind](https://youmind.com/blog/claude-memory-import-chatgpt-transfer)
- **How memory works:** Claude does not store full transcripts in memory. It extracts details such as role and preferences after chats and keeps them as a summary, which can be viewed and edited in Settings > Memory. [BLOG] [Syracuse ITS](https://its.syr.edu/claude-has-a-memory-heres-how-to-use-it/); [Justin McKelvey](https://justinmckelvey.com/blog/claude-memory)
- **Defaults:** memory is on by default for Free, Pro and Max, and off by default for Team and Enterprise until an owner enables it. [BLOG] [AI Toolbox](https://www.ai-toolbox.co/claude-management-and-productivity/claude-memory-how-it-works-2026)
- **Chat search:** sources conflict on whether it is paid-only. [BLOG] [Shareuhack](https://www.shareuhack.com/en/posts/claude-memory-feature-guide-2026) vs [McKelvey](https://justinmckelvey.com/blog/claude-memory)

### Inferences
- Claude's design contrasts with ChatGPT's. Claude uses **tool-based retrieval** for past chats (the model decides when to search) and a compact synthesized memory. ChatGPT injects a profile on every turn. This contrast was widely discussed in 2025 [BACKGROUND, e.g. Shlok Khemani's companion post on Claude memory]. It is worth verifying.

### Gaps
- The details of the 2025 rollout came up in no search this session. From [BACKGROUND]: chat search for paid users (August 2025); memory for Team and Enterprise (September 2025), then Pro and Max (October 2025); a project-scoped memory summary updated roughly daily; incognito chats; and the Claude Developer Platform's file-based "memory tool" (`/memories` directory).

---

## 5. Google Gemini: past chats, Saved info, Personal Intelligence

### Takeaway
Gemini memory has three layers, each with its own toggle:
- **Saved info:** explicit facts the user asks it to remember.
- **"Your past chats":** automatic memory from prior conversations.
- **Personal Intelligence:** a 2026 beta that connects Gmail, Photos, Search and YouTube history.

Google says it does not train directly on Gmail or Photos content.

### Cited Findings
- **Personal Intelligence:** a beta in the Gemini app that connects across Gmail, Photos, Search and YouTube history. At launch it was limited to AI Pro and Ultra subscribers on US personal accounts, and connected apps are off by default. [PRESS] [Search Engine Land](https://searchengineland.com/personal-intelligence-with-gemini-connect-your-searches-email-photos-and-youtube-history-467521); [Tom's Guide](https://www.tomsguide.com/ai/google-gemini-just-pulled-further-ahead-of-chatgpt-heres-what-it-can-now-do-with-your-gmail-and-photos)
- **Past-chat memory:** on by default, and can be turned off under "Your past chats." It requires age 18+, a personal account and Keep Activity on, and is unavailable in the EEA, UK, Switzerland and Nigeria (per one source). It does not apply in Gems or Live. One source says Live gained Personal Intelligence in August 2026. [BLOG] [datastudios](https://www.datastudios.org/post/does-gemini-remember-past-conversations-context-retention-and-session-behavior); [memoryplugin](https://blog.memoryplugin.com/how-gemini-memory-works/)
- **Training:** Google says it does not train directly on the Gmail inbox or Photos library. Personal data is referenced to answer questions. [PRESS] [Search Engine Land](https://searchengineland.com/personal-intelligence-with-gemini-connect-your-searches-email-photos-and-youtube-history-467521)
- **Import:** Google published a "Make the switch" guide for importing AI memories and chat history from other assistants into Gemini. [OFFICIAL] [Google blog](https://blog.google/intl/en-mena/product-updates/explore-get-answers/ai-memories-chat-history-to-gemini/)

### Inferences
- Gemini's advantage is retrieval over first-party data stores (Gmail, Photos) rather than accumulated chat memory. Its "memory" is mostly live retrieval over the user's data, plus a lighter learned profile.
- Memory portability (import tools from Google and Anthropic) emerged in 2026 as a competitive front.

### Gaps
- Sources conflict on whether Gemini offers an editable list of remembered facts. The exact launch date of Personal Intelligence (I believe January 2026 [BACKGROUND]) is not confirmed here.

---

## 6. Apple Intelligence: Siri personal context

### Takeaway
"Siri AI" was announced at WWDC in June 2026 and shipped as a beta in English around **September 14, 2026** with iOS 27. It draws on an **on-device Spotlight semantic index** covering messages, email, photos and more. Apps contribute content through App Schemas and App Intents entities. Heavier queries go to Private Cloud Compute.

### Cited Findings
- **Announcement:** Apple's June 2026 announcement says Siri AI uses "personal context understanding" across messages, emails, photos and more. [OFFICIAL] [Apple Newsroom](https://www.apple.com/newsroom/2026/06/apple-introduces-siri-ai-a-profoundly-more-capable-and-personal-assistant/)
- **Developer integration:** developers add entities to the Spotlight semantic index and keep it updated via App Schemas and App Intents. [OFFICIAL] [WWDC26 session 240](https://developer.apple.com/videos/play/wwdc2026/240/); [WWDC26 session 343](https://developer.apple.com/videos/play/wwdc2026/343/); [WWDC26 Apple Intelligence guide](https://developer.apple.com/wwdc26/guides/apple-intelligence/)
- **Where processing happens:** a mix of on-device processing and Private Cloud Compute. [BLOG] [Futurum](https://futurumgroup.com/insights/will-apples-new-siri-ai-deliver-on-the-promise-of-apple-intelligence/); [iGeeksBlog](https://www.igeeksblog.com/siri-ai-ios-27-features/)
- **Index sources and controls:** the index draws on Safari history, email, messages, images, notifications and contacts. A per-app control is at Settings > Siri > Apps > [app] > "Learn from this App." One guide says the EU is excluded on iPhone and iPad (unverified). [BLOG] [Elephas](https://elephas.app/resources/what-is-apple-intelligence)
- **Context as advantage:** NN/g argues that the new Siri's main advantage is access to personal context, not raw intelligence. [BLOG] [NN/g](https://www.nngroup.com/articles/ai-assistant-context/)

### Inferences
- Apple's model is "memory as an index of the user's existing data, kept on device," not an accumulated conversational memory. It is the most privacy-preserving architecture in this set, but it depends on apps adopting the index.

### Gaps
- Whether Siri AI also keeps a persistent conversational memory or profile across sessions, and the exact GA versus beta status of the feature.

---

## 7. Microsoft Copilot, xAI Grok, Perplexity (Comet), Character.AI

### Takeaway
All four have persistent memory. Sourcing is mostly secondary. Microsoft published a notable security finding on **memory poisoning** (February 2026).

### Cited Findings
- **Microsoft 365 Copilot Memory:** introduced in 2025. Secondary sources report GA in January 2026 and rollout completed by May 2026, with a June 2026 update that makes memory directives easier to find and manage. [OFFICIAL/BLOG] [Microsoft Tech Community](https://techcommunity.microsoft.com/blog/microsoft-copilot-blog/introducing-copilot-memory-a-more-productive-and-personalized-ai-for-the-way-you/4432059); [office365itpros](https://office365itpros.com/2026/06/29/copilot-memory-updates/)
- **AI Recommendation Poisoning (Microsoft Security, February 10, 2026):** attackers can manipulate AI assistant memory for commercial gain, for example by planting persistent preferences. [OFFICIAL] [Microsoft Security blog](https://www.microsoft.com/en-us/security/blog/2026/02/10/ai-recommendation-poisoning/)
- **Grok:** persistent memory since April 2025, on by default on grok.com and mobile, not in the EU or UK. "Skills" (saved reusable tasks and formatting rules) were added in May 2026. [BLOG] [memorylake comparison](https://www.memorylake.ai/en/blogs/ai-memory-compared-2026)
- **Perplexity:** one source reports that recall accuracy rose from 77% to 95% for Pro and Max after a February 2026 upgrade, plus a "Brain" self-improving memory in June 2026. **This is uncorroborated vendor-blog content.** [BLOG] [tech-insider](https://tech-insider.org/copilot-vs-gemini-vs-perplexity-2026/); [dume.ai](https://www.dume.ai/blog/top-10-ai-assistants-with-memory-in-2026)
- **Character.AI:** memory is mostly manual. Free users get 15 pinned messages per chat and a 400-character "Chat Memories" box. The paid lite tier gets 30 pins, and c.ai+ adds auto-memories and private Lorebooks. [BLOG summarizing help center] [Facebook answers page](https://www.facebook.com/fb-answers/character-ai-memory-features/); [aiagentmemory.org](https://aiagentmemory.org/articles/best-ai-with-good-memory)

### Inferences
- Memory poisoning (from injected web content or agents) is now an officially recognized threat class. It matters most for products that write memory automatically from browsing or connected apps: Atlas, Dots, Muse and Comet.

### Gaps
- Primary xAI and Perplexity documentation was not retrieved. Comet browser memory specifics were not found. Consumer Copilot (as opposed to M365) memory details were not retrieved.

---

## 8. Lifelogging and ambient-capture tools: Rewind/Limitless, Screenpipe, Granola, Recall

### Takeaway
The lifelogging category was reshaped when **Meta acquired Limitless (December 2025)** and switched off Rewind capture. **Screenpipe** has become the main local, source-available replacement. Its model is continuous screen and audio capture, OCR and transcription, a local index, and LLM search. Granola is a meeting-transcription notes app, and its consent practices have drawn privacy critique.

### Cited Findings
- **Rewind:** capture was disabled from December 19, 2025. EU and UK data had to be exported before deletion. Others keep limited functionality only after agreeing to Meta's terms. [BLOG] [luci.memories.ai](https://luci.memories.ai/blog/rewind-ai-shut-down-on-device-replacement); [usecarly](https://www.usecarly.com/blog/rewind-ai-alternatives/)
- **Screenpipe:** captures screen and audio continuously, indexes text for AI search, and stores locally with offline use supported. It cannot import Rewind data. Its own blog frames the issue as "who owns what you remember." [OFFICIAL/BLOG] [Screenpipe blog](https://screenpipe.com/blog/rewind-ai-alternative-2026); [Screenpipe: Personal AI memory in 2026](https://screenpipe.com/blog/personal-ai-memory-2026)
- **Microsoft Recall** on Copilot+ PCs is cited as the other main alternative. [BLOG] [luci.memories.ai](https://luci.memories.ai/blog/rewind-ai-shut-down-on-device-replacement)
- **Granola:** joins and transcribes meetings via calendar, reportedly without visibly notifying participants (a dated, roughly 2025 critique). [BLOG] [Medium/mparekh](https://medium.com/@mparekh/ai-adding-memory-to-more-ai-applications-offer-promise-peril-rtz-780-e6cd25a5f8e1)

### Gaps
- Granola's 2026 memory and "chat across meetings" features came up in no search this session. [BACKGROUND]: Granola captures system audio with no bot in the call, does not store audio, and keeps transcripts and notes in the cloud.

---

## 9. Published writing on "context engineering"

### Takeaway
The canonical texts are:
- **Manus**, "Context Engineering for AI Agents: Lessons from Building Manus" (July 2025, Yichao "Peak" Ji)
- **Anthropic**, "Effective context engineering for AI agents" (September 2025, not retrieved this session)
- **OpenAI** cookbook material on agent memory and session management (not retrieved)

Manus is now part of Meta.

### Cited Findings
- **KV-cache hit rate:** Manus calls it the single most important production metric. Agents run about 100:1 input-to-output tokens. Cached input on Claude Sonnet costs $0.30/MTok versus $3/MTok uncached. Prompt prefixes should be kept stable, since a timestamp at the start of a system prompt kills the cache. Context should be append-only. [OFFICIAL] [Manus blog](https://manus.im/blog/Context-Engineering-for-AI-Agents-Lessons-from-Building-Manus)
- **Tool masking:** mask tools via logit masking instead of adding or removing them, because changing them invalidates the cache and confuses the model. The agent framework was rebuilt four times. [OFFICIAL/BLOG] [Manus blog](https://manus.im/blog/Context-Engineering-for-AI-Agents-Lessons-from-Building-Manus); [DEV summary](https://dev.to/contextspace_/context-engineering-for-ai-agents-key-lessons-from-manus-1lgb); [tianpan.co](https://tianpan.co/blog/2026/03/02/context-engineering-lessons-from-manus)

### Gaps
- No search surfaced Anthropic's post or OpenAI's cookbook entries. From [BACKGROUND], unverified: Anthropic's post (September 29, 2025) frames context as a finite "attention budget" subject to "context rot." Its recommended techniques are:
  - just-in-time retrieval via tools rather than pre-loading
  - compaction
  - structured note-taking or agentic memory files
  - sub-agent architectures

  It also launched the memory tool and context editing on the Claude Developer Platform. The other Manus lessons from [BACKGROUND] are:
  - use the file system as externalized memory
  - "recite" goals via a todo.md to manipulate attention
  - keep errors in context
  - avoid few-shot ruts

  The report writer should verify these before citing.
