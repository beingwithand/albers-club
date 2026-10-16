# GitHub OSS Landscape: Capturing, Archiving and Owning One's Personal Digital Life (as of 16 Oct 2026)

**Method note.** Repo metadata (stars, primary language, license SPDX, last push date, creation date, archived flag, description) was pulled on 2026-10-16 from the GitHub Search API through the GitHub MCP tool, using batched `repo:` queries. Every metadata line below cites the repo URL as its source. Several things were checked by fetching the README: Screenpipe's license and architecture, Omnivore's status, Timelinize's status and architecture, and why gphotos-sync was archived. Architecture notes not confirmed in this session come from prior knowledge and are marked **[PK]**. The report writer should treat those as likely but not re-verified.

Activity legend: **Active** = pushed within about 60 days of 2026-10-16. **Slow** = pushed 2 to 12 months ago. **Dormant** = no push for more than 12 months. **Archived** = GitHub read-only flag is set.

Note on "pushed_at": it reflects any branch push, including dependabot and CI. It is a ceiling on staleness, not proof of real feature development.

---

## Q1. Screen/activity lifelogging (Recall/Rewind-style capture and time trackers)

### Takeaway
Screenpipe dominates this category (about 22k stars, very active). It is now **source-available under a commercial license, not OSI open source**, so it is not a freely reusable building block. Dayflow (MIT, about 7.3k stars, created Sept 2025) is the breakout new macOS entrant. ActivityWatch (MPL-2.0, about 19k stars) remains the best permissively licensed foundation for activity and time tracking. The first generation of 2023–24 Recall clones (rem, Memento, OpenRecall) is largely dormant. Windrecorder (Windows) and Pensieve are still maintained.

### Cited Findings
- **Screenpipe** (screenpipe/screenpipe): about 21,958 stars, Rust, license NOASSERTION, pushed 2026-10-16, created 2024-06. The description now reads "YC (S26) | Open Computer History | Continuously record your company computer work, map your workflows… power your agents' context". Topics include mcp, rewind, screen-recording and speech-to-text — [GitHub](https://github.com/screenpipe/screenpipe)
  - The README says it is "source-available" under the "Screenpipe Commercial License". Personal, non-commercial, educational and research use is free; commercial use needs a license. The desktop app has Free, Basic and Business tiers, and lifetime licenses are no longer sold — [GitHub README](https://github.com/screenpipe/screenpipe)
  - Architecture: it captures the accessibility tree first and falls back to OCR. Audio goes through local Whisper or Deepgram. Data is stored in local SQLite with FTS5, with media files on disk. It exposes a local REST API, an MCP server, and "pipes" (scheduled agents defined in markdown). Telemetry (PostHog and Sentry) is on by default. It runs on macOS, Windows and Linux (AppImage) — [GitHub README](https://github.com/screenpipe/screenpipe)
  - Third-party comparisons disagree on its license: older blogs still call it MIT, while a later comparison notes the move to source-available — [WebSearch summary of screenpi.pe / usecarly blogs](https://www.usecarly.com/blog/rewind-ai-alternatives/); [screenpi.pe blog](https://screenpi.pe/blog/rewind-ai-alternative-2026)
- **Context: Rewind is gone.** Meta acquired Limitless (Rewind's parent) on 5 Dec 2025, and Rewind's screen and audio capture was disabled on 19 Dec 2025. This comes from vendor blog content, so it is a secondary source — [screenpi.pe blog](https://screenpi.pe/blog/rewind-ai-alternative-2026)
- **Dayflow** (JerryZLiu/Dayflow): about 7,276 stars, Swift (macOS), MIT, pushed 2026-10-15, created 2025-09-23. "Automatic work journal/time tracker. Privately turns your screen into a timeline… Open-source and local-first." — [GitHub](https://github.com/JerryZLiu/Dayflow)
- **ActivityWatch** (ActivityWatch/activitywatch): about 19,253 stars, Python (plus Rust server [PK]), MPL-2.0, pushed 2026-10-16, created 2016. "The best free and open-source automated time tracker. Cross-platform, extensible, privacy-focused." — [GitHub](https://github.com/ActivityWatch/activitywatch)
  - [PK] Architecture: client/server design. "Watchers" (window, AFK, browser-extension and editor watchers) post heartbeat events to a local REST server (aw-server-rust) backed by SQLite. Events use a simple bucket/event JSON model. It runs on Windows, macOS and Linux.
- **Windrecorder** (yuka-friends/Windrecorder): about 3,957 stars, Python, GPL-2.0, pushed 2026-09-25, created 2023-07. It records the screen "in small size", lets you query through OCR text or image description, and targets Windows — [GitHub](https://github.com/yuka-friends/Windrecorder)
- **OpenRecall** (openrecall/openrecall): about 2,959 stars, Python, AGPL-3.0, **last push 2025-09-24** (Slow/near-dormant), created 2024-05 — [GitHub](https://github.com/openrecall/openrecall)
- **rem** (jasonjmcghee/rem): about 2,489 stars, Swift (macOS), MIT, **last push 2024-05-30 (Dormant)** — [GitHub](https://github.com/jasonjmcghee/rem)
- **Memento** (apirrone/Memento): about 660 stars, Python, MIT, **last push 2024-04-23 (Dormant)**. It records everything and lets you chat with an LLM over it — [GitHub](https://github.com/apirrone/Memento)
- **Pensieve** (arkohut/pensieve): about 1,392 stars, Python, Apache-2.0, pushed 2026-07-19 (Slow). It takes passive screenshots of all screens, indexes them and stores them locally — [GitHub](https://github.com/arkohut/pensieve)
- **MineContext** (volcengine/MineContext, ByteDance/Volcengine): about 5,537 stars, Python, Apache-2.0, pushed 2026-05-07 (Slow), created 2025-06. "Proactive context-aware AI partner (Context-Engineering + ChatGPT Pulse)" — [GitHub](https://github.com/volcengine/MineContext)
- **TotalRecall** (xaitax/TotalRecall): about 169 stars, C++, no license, pushed 2026-04. It extracts and displays data from the Windows 11 Recall feature, so it is a forensic and extraction tool for Microsoft's own store — [GitHub](https://github.com/xaitax/TotalRecall)
- **Selfspy** (selfspy/selfspy): about 2,499 stars, Python, GPL-3.0, **last push 2019-03-06 (Dead)** — [GitHub](https://github.com/selfspy/selfspy)
- **arbtt** (nomeata/arbtt): about 363 stars, Haskell, GPL-2.0, pushed 2026-08-31. It is a rule-based automatic time tracker, niche but maintained — [GitHub](https://github.com/nomeata/arbtt)
- **LightMem-Ego** (zjunlp/LightMem-Ego): about 112 stars, created 2026-05, "[EMNLP 2026] Your AI Memory for Everyday Life". Smart-glasses and wearable egocentric lifelogging research code — [GitHub](https://github.com/zjunlp/LightMem-Ego)

### Inferences
- **Reuse candidates:** ActivityWatch (MPL-2.0; its event schema and watcher architecture are a proven, permissive base) and Dayflow (MIT, modern Swift, active). Windrecorder is a reference design for Windows but GPL-2.0.
- **Screenpipe:** best in class technically (accessibility tree plus OCR, SQLite FTS5, MCP). Its license now blocks commercial reuse, so treat it as a competitor or reference, not a dependency. It has pivoted toward "company computer work" and agent context, away from personal lifelogging.
- **Dead or dormant:** Selfspy, rem, Memento. OpenRecall is close to dormant.
- **The Rewind shutdown (Dec 2025)** left a gap in the consumer market for a polished, local, private screen-memory app.

### Gaps
- I did not find GitHub repos for apps named "Memento" other than apirrone/Memento. Other 2025–26 Recall clones under 300 stars were not exhaustively enumerated, because GitHub keyword search returned noise from AI-agent repos.
- Dayflow's storage format (SQLite or files) and its LLM backend (local or cloud) were not verified.
- Microsoft Recall itself is not open source. "Recall clones" other than OpenRecall were not individually verified.

---

## Q2. Personal data hubs / timelines / personal data warehouses

### Takeaway
The active "hub" projects are Timelinize (Go, AGPL, SQLite plus files on disk, explicitly unstable), Karlicoss's HPI and Promnesia (Python, MIT, both still maintained), Perkeep (Go, Apache-2.0, still pushed after 15 years) and Datasette/Dogsheep (Apache-2.0). Datasette is active, but most of the per-source Dogsheep importers are dormant. Khoj (about 38k stars, AGPL) is the largest "AI second brain" over personal docs. Dawarich (about 10.7k stars) is the Google Timeline replacement for location data.

### Cited Findings
- **Timelinize** (timelinize/timelinize): about 3,686 stars, Go, AGPL-3.0, pushed 2026-05-22 (Slow), created 2024-08 — [GitHub](https://github.com/timelinize/timelinize)
  - The README says it "is in active development and is still unstable". The schema still changes, so users may need to start a new timeline when upgrading. It imports Google Takeout, Apple iCloud, Facebook, Twitter/X, Strava, Instagram, Google Location History and more, and archives don't need extracting. Data is indexed in SQLite and stored on disk by date with "no proprietary formats" — [GitHub README](https://github.com/timelinize/timelinize)
- **HPI** (karlicoss/HPI): about 1,643 stars, Python, MIT, pushed 2026-10-10. Topics: data-liberation, lifelogging, personal-api, quantified-self — [GitHub](https://github.com/karlicoss/HPI)
  - [PK] Architecture: a Python package of modules (`my.reddit`, `my.google.takeout` and so on) that read raw exports lazily from disk with no central DB. It relies on per-service exporters (rexport, ghexport, pockexport, kobuddy, fbmessengerexport, all by karlicoss) and caches through cachew (SQLite).
  - Karlicoss's exporters are all still pushed in Sept–Oct 2026: rexport (about 189 stars), pockexport (about 203), kobuddy (about 184), fbmessengerexport (about 75) and ghexport (about 59) — [GitHub topic:data-liberation search](https://github.com/karlicoss/rexport); [pockexport](https://github.com/karlicoss/pockexport); [kobuddy](https://github.com/karlicoss/kobuddy)
- **Promnesia** (karlicoss/promnesia): about 1,904 stars, Python, MIT, pushed 2026-09-12. "Another piece of your extended mind." [PK] It is a browser extension plus an indexer that merges browser history and other HPI sources into SQLite, showing context and visit history for the current URL — [GitHub](https://github.com/karlicoss/promnesia)
- **Perkeep** (perkeep/perkeep, formerly Camlistore): about 7,247 stars, Go, Apache-2.0, pushed 2026-10-16, created 2011. "Your personal storage system for life: storing, syncing, sharing, modelling and backing up content." [PK] It uses content-addressed blob storage with JSON "permanode" claims and a pluggable index (SQLite, LevelDB and others), with importers for Twitter, Flickr, Foursquare and other services. Historically it has had a small community and complex UX — [GitHub](https://github.com/perkeep/perkeep)
- **Datasette** (simonw/datasette): about 11,515 stars, Python, Apache-2.0, pushed 2026-10-13 — [GitHub](https://github.com/simonw/datasette)
- **Dogsheep tools** (all Apache-2.0):
  - twitter-to-sqlite: about 417 stars, last push 2022-12-28 (Dormant) — [GitHub](https://github.com/dogsheep/twitter-to-sqlite)
  - google-takeout-to-sqlite: about 122 stars, last push 2023-09-06 (Dormant) — [GitHub](https://github.com/dogsheep/google-takeout-to-sqlite)
  - healthkit-to-sqlite: about 249 stars, last push 2023-01-01 (Dormant) — [GitHub](https://github.com/dogsheep/healthkit-to-sqlite)
  - dogsheep-photos: about 188 stars, last push 2024-01-05 (Dormant) — [GitHub](https://github.com/dogsheep/dogsheep-photos)
  - dogsheep-beta (cross-table search index): about 211 stars, pushed 2026-04-08 — [GitHub](https://github.com/dogsheep/dogsheep-beta)
- **Memex** (WorldBrain/Memex): about 4,721 stars, TypeScript, **no license detected**, pushed 2025-12-02 (Slow). It is a browser extension to curate, annotate and discuss web content — [GitHub](https://github.com/WorldBrain/Memex)
- **Khoj** (khoj-ai/khoj): about 37,710 stars, Python, AGPL-3.0, pushed 2026-08-02. "Your AI second brain. Self-hostable… from the web or your docs" — [GitHub](https://github.com/khoj-ai/khoj)
- **Dawarich** (Freika/dawarich): about 10,685 stars, Ruby, AGPL-3.0, pushed 2026-10-16. A "self-hostable alternative to Google Timeline (Google Location History)" — [GitHub](https://github.com/Freika/dawarich)
- **OwnTracks Recorder** (owntracks/recorder): about 1,216 stars, C, pushed 2026-09-08. It stores location data from the OwnTracks mobile apps — [GitHub](https://github.com/owntracks/recorder)
- **chronicle-etl** (chronicle-app/chronicle-etl): about 200 stars, Ruby. "A CLI toolkit for extracting and working with your digital history" — [GitHub](https://github.com/chronicle-app/chronicle-etl)
- **qs_ledger** (markwk/qs_ledger): about 1,080 stars, Jupyter notebooks for aggregating QS data — [GitHub](https://github.com/markwk/qs_ledger)
- **flow-dashboard** (onejgordon/flow-dashboard): about 1,688 stars, self-described "[UNMAINTAINED]" — [GitHub](https://github.com/onejgordon/flow-dashboard)
- **Data Transfer Project** (dtinit/data-transfer-project): about 3,626 stars, Java, Apache-2.0, pushed 2026-10-16. A framework for platform-to-platform data portability — [GitHub](https://github.com/dtinit/data-transfer-project)
- **greenbubbles** (bojieli/greenbubbles): about 382 stars, Rust, created 2026-08. "Enable your AI agents to access your WeChat history in real time" (SQLCipher, macOS). It is a sign of the 2026 trend of exposing personal message stores to agents — [GitHub](https://github.com/bojieli/greenbubbles)
- **textileio/photos**, a "personal data wallet", is deprecated and archived — [GitHub](https://github.com/textileio/photos)

### Inferences
- The architecture most products converge on is **raw export files kept as the source of truth, normalized into SQLite (often with FTS5), with a timeline UI and now an MCP/LLM layer**. Timelinize, Screenpipe, Datasette and Promnesia all follow this pattern.
- **Best building blocks:** HPI and karlicoss's exporters (MIT) for parsing logic, and Datasette and sqlite-utils (Apache-2.0) for storage and exploration. Timelinize is the closest product-level analogue, but AGPL plus "unstable" makes it a reference rather than a dependency.
- **Dogsheep importers are stale.** They are useful as code references, but the export formats they parse (for example Twitter's pre-X API) have drifted.
- No mature **mobile-first** OSS personal-data hub surfaced in searches. Location (OwnTracks, Dawarich) is the exception.

### Gaps
- I found no actively maintained Logseq or Obsidian "life importer" with significant stars in this session. Obsidian plugins were not searched specifically.
- Perkeep's recent commit substance (feature work or maintenance only) was not verified.

---

## Q3. Platform-specific exporters / scrapers

### Takeaway
Media downloaders (yt-dlp about 198k stars, gallery-dl about 20k, instaloader about 13.6k) and the messaging exporters (DiscordChatExporter about 12k, tdl about 8k, imessage-exporter about 5.7k, WhatsApp-Chat-Exporter about 1.3k, signal-export about 0.8k) are healthy and very active, which makes them the best reusable building blocks. Twitter/X archive tooling is dead (twitter-archive-parser last pushed Nov 2022). Facebook/Meta "Download Your Information" parsers are fragmented, with no project above a few stars. Korean-platform tools (Kakao, Naver) are tiny and scattered.

### Cited Findings
- **yt-dlp** (yt-dlp/yt-dlp): about 198,444 stars, Python, Unlicense, pushed 2026-10-10 — [GitHub](https://github.com/yt-dlp/yt-dlp)
- **gallery-dl** (mikf/gallery-dl): about 20,121 stars, Python, GPL-2.0, pushed 2026-10-09. Downloads image galleries from "several image hosting sites" (in practice hundreds of extractors, including Instagram, Twitter/X, Reddit and Pixiv [PK]) — [GitHub](https://github.com/mikf/gallery-dl)
- **Instaloader** (instaloader/instaloader): about 13,597 stars, Python, MIT, pushed 2026-10-14 — [GitHub](https://github.com/instaloader/instaloader)
- **DiscordChatExporter** (Tyrrrz/DiscordChatExporter): about 12,198 stars, C#, MIT, pushed 2026-10-09. [PK] Exports to HTML, JSON, CSV or TXT; has a GUI and CLI; cross-platform through .NET. Uses a user token, which is against Discord's ToS — [GitHub](https://github.com/Tyrrrz/DiscordChatExporter)
- **tdl** (iyear/tdl): about 8,167 stars, Go, AGPL-3.0, pushed 2026-10-15. "A Telegram toolkit written in Golang" (download, export, forward [PK]) — [GitHub](https://github.com/iyear/tdl)
- **imessage-exporter** (ReagentX/imessage-exporter): about 5,681 stars, Rust, GPL-3.0, pushed 2026-09-20. [PK] Reads macOS `chat.db` and iOS backups and exports HTML or TXT — [GitHub](https://github.com/ReagentX/imessage-exporter)
- **WhatsApp-Chat-Exporter** (KnugiHK/WhatsApp-Chat-Exporter): about 1,273 stars, Python, MIT, pushed 2026-10-13. Parses WhatsApp databases from Android (.crypt12/14/15) and iOS backups — [GitHub](https://github.com/KnugiHK/WhatsApp-Chat-Exporter)
- **signal-export** (carderne/signal-export): about 794 stars, Python, license NOASSERTION, pushed 2026-09-02. Exports Signal Desktop chats to markdown with attachments — [GitHub](https://github.com/carderne/signal-export)
- **twitter-archive-parser** (timhutton/twitter-archive-parser): about 2,436 stars, Python, GPL-3.0, **last push 2022-11-29 (Dead)** — [GitHub](https://github.com/timhutton/twitter-archive-parser)
- **Reddit:**
  - karlicoss/rexport (about 189 stars, active) — [GitHub](https://github.com/karlicoss/rexport)
  - xavdid/reddit-user-to-sqlite (about 231 stars, last push 2023-07, Dormant) — [GitHub](https://github.com/xavdid/reddit-user-to-sqlite)
  - Watchful1/PushshiftDumps (about 510 stars, pushed 2026-09; scripts for Pushshift dump files) — [GitHub](https://github.com/Watchful1/PushshiftDumps)
- **Google Takeout:**
  - purarue/google_takeout_parser (about 141 stars, MIT, pushed 2026-07-03; parses History, Activity, YouTube and Locations) — [GitHub](https://github.com/purarue/google_takeout_parser)
  - dogsheep/google-takeout-to-sqlite (Dormant, see Q2) — [GitHub](https://github.com/dogsheep/google-takeout-to-sqlite)
- **Facebook/Meta DYI:** a search for "download your information" parsers returned only repos with 0 to 3 stars, for example kr3t3n/igmd (created 2026-08; Meta DYI ZIP to markdown per chat) and bushidocodes/hatchling (DYI to SOLID Turtle) — [igmd](https://github.com/kr3t3n/igmd); [hatchling](https://github.com/bushidocodes/hatchling)
- **KakaoTalk:**
  - jiru/kakaodecrypt (about 91 stars; decrypts the Android KakaoTalk local DB) — [GitHub](https://github.com/jiru/kakaodecrypt)
  - AidanKR/kakao-auto (about 58 stars, created 2026-07; a Windows KakaoTalk PC auto-collector that cycles rooms, exports with Ctrl+S, and stores SQLite plus daily TXT with search) — [GitHub](https://github.com/AidanKR/kakao-auto)
  - realdeveloperongithub/chat-history-manager (about 18 stars; parsers for Line, KakaoTalk, WhatsApp, Instagram, Messenger, WeChat and Google Chat) — [GitHub](https://github.com/realdeveloperongithub/chat-history-manager)
- **Naver:** search found only small blog crawlers (for example xotrs/naver-blog-crawler, about 32 stars) and automation or MCP tools. There is no dedicated personal-data backup tool — [GitHub](https://github.com/xotrs/naver-blog-crawler)

### Inferences
- **Best-in-class reusable building blocks:** yt-dlp, gallery-dl, instaloader, DiscordChatExporter, imessage-exporter, tdl and WhatsApp-Chat-Exporter. Each wraps a constantly changing platform surface, and a product should depend on them, not rewrite them. Mind the licenses: gallery-dl is GPL-2.0, imessage-exporter GPL-3.0 and tdl AGPL-3.0, while yt-dlp (Unlicense) and DiscordChatExporter and instaloader (MIT) are permissive.
- **Gaps an app could fill:** Twitter/X archive parsing (current archive format), Meta DYI (Facebook and Instagram JSON) parsing, and KakaoTalk and Naver. All of these lack a maintained, popular OSS parser.

### Gaps
- `expectocode/telegram-export`, `aliparlakci/bulk-downloader-for-reddit` and `pesos/browser-history` did not resolve in the batch `repo:` search. They may be renamed, moved or deleted, and their status is unverified.
- Twitter/X archive tools newer than 2022 (for example forks of twitter-archive-parser) were not enumerated.
- No dedicated Naver (blog, cafe, mail) personal-backup tool was found. That absence is itself a finding, but small repos may exist under Korean-language names.

---

## Q4. Web archiving, bookmarks and read-it-later

### Takeaway
This category is crowded and healthy. Karakeep (formerly Hoarder, about 29.7k stars), ArchiveBox (about 28.8k), SingleFile (about 22.6k), Linkwarden (about 20.1k), monolith (about 15.5k), wallabag (about 13k), Shiori and linkding (about 11k+ each) are all active. Omnivore's cloud service shut down in Nov 2024, but the repo continues as a self-host-only project. Readeck lives on Codeberg, not GitHub; its GitHub repo is a stale mirror.

### Cited Findings
- **Karakeep**, formerly Hoarder (karakeep-app/karakeep): about 29,708 stars, TypeScript, AGPL-3.0, pushed 2026-10-15. "Bookmark-everything app (links, notes and images) with AI-based automatic tagging and full text search" — [GitHub](https://github.com/karakeep-app/karakeep)
- **ArchiveBox** (ArchiveBox/ArchiveBox): about 28,795 stars, Python, MIT, pushed 2026-10-16. "Takes URLs/browser history/bookmarks/Pocket/Pinboard… saves HTML, JS, PDFs, media". [PK] It stores data as plain files per snapshot plus an index in SQLite (Django) — [GitHub](https://github.com/ArchiveBox/ArchiveBox)
- **SingleFile** (gildas-lormeau/SingleFile): about 22,615 stars, JavaScript, AGPL-3.0, pushed 2026-10-13. A web extension that saves a complete page as a single HTML file — [GitHub](https://github.com/gildas-lormeau/SingleFile)
- **Linkwarden** (linkwarden/linkwarden): about 20,125 stars, TypeScript, AGPL-3.0, pushed 2026-10-13 — [GitHub](https://github.com/linkwarden/linkwarden)
- **Omnivore** (omnivore-app/omnivore): about 16,283 stars, AGPL-3.0, pushed 2026-10-16. The README says: "Omnivore is now a completely Self-Hosted application. The Cloud application was deprecated in November of 2024… we endeavour to keep things updated and bug-fixes ongoing." — [GitHub README](https://github.com/omnivore-app/omnivore)
- **monolith** (Y2Z/monolith): about 15,520 stars, Rust, CC0-1.0, pushed 2026-10-16. A CLI/GUI/library for saving pages as a single HTML file — [GitHub](https://github.com/Y2Z/monolith)
- **wallabag** (wallabag/wallabag): about 13,014 stars, PHP, MIT, pushed 2026-10-13 — [GitHub](https://github.com/wallabag/wallabag)
- **Shiori** (go-shiori/shiori): about 11,668 stars, Go, MIT, pushed 2026-10-11 — [GitHub](https://github.com/go-shiori/shiori)
- **linkding** (sissbruecker/linkding): about 11,307 stars, Python, MIT, pushed 2026-10-01 — [GitHub](https://github.com/sissbruecker/linkding)
- **Webrecorder:**
  - archiveweb.page (about 1,598 stars, AGPL-3.0, pushed 2026-09; a high-fidelity WARC/WACZ archiving extension) — [GitHub](https://github.com/webrecorder/archiveweb.page)
  - browsertrix-crawler (about 1,168 stars, AGPL-3.0, pushed 2026-10-15) — [GitHub](https://github.com/webrecorder/browsertrix-crawler)
- **grab-site** (ArchiveTeam/grab-site): about 1,616 stars, pushed 2025-05 (Slow). A WARC-output crawler — [GitHub](https://github.com/ArchiveTeam/grab-site)
- **Readeck:** the GitHub repo readeck/readeck has about 284 stars, no description, and a last push of 2023-12-18, which suggests the project's active home is elsewhere ([PK]: Codeberg, codeberg.org/readeck/readeck) — [GitHub](https://github.com/readeck/readeck)

### Inferences
- **Reuse:** SingleFile (AGPL) and monolith (CC0, Rust, embeddable as a library) handle single-file page capture. Webrecorder's WACZ is the standards-grade archive format. ArchiveBox (MIT) is the most permissive full-stack archiver.
- **Karakeep** is the momentum leader for "save everything plus AI tagging".
- **Omnivore** is effectively a community-maintained self-host project now. Its "dead" status applies to the hosted service only.

### Gaps
- Readeck's Codeberg activity and star count were not verified.

---

## Q5. Email archiving

### Takeaway
Classic sync tools persist: imapsync (active), offlineimap3 (Slow), imap-backup (Slow), and isync/mbsync and notmuch, which are both developed off GitHub. Gmvault is dead (last push May 2022). Got Your Back (GYB) is the maintained Gmail-API backup tool. Since 2025 a wave of self-hosted web-UI archivers has appeared: Mail-Archiver (May 2025), OpenArchiver (July 2025) and Bichon (Nov 2025, Rust). Each reached 2k+ stars quickly.

### Cited Findings
- **Got Your Back / GYB** (GAM-team/got-your-back): about 3,136 stars, Python, Apache-2.0, pushed 2026-10-11. Backs up Gmail through the Gmail API over HTTPS — [GitHub](https://github.com/GAM-team/got-your-back)
- **Gmvault** (gaubert/gmvault): about 3,640 stars, Python, AGPL-3.0, **last push 2022-05-01 (Dead)** — [GitHub](https://github.com/gaubert/gmvault)
- **imapsync** (imapsync/imapsync): about 4,180 stars, Perl/Shell, pushed 2026-09-24 — [GitHub](https://github.com/imapsync/imapsync)
- **offlineimap3** (OfflineIMAP/offlineimap3): about 634 stars, Python, pushed 2026-06-15 (Slow) — [GitHub](https://github.com/OfflineIMAP/offlineimap3)
- **imap-backup** (joeyates/imap-backup): about 1,717 stars, Ruby, MIT, pushed 2026-03-30 (Slow) — [GitHub](https://github.com/joeyates/imap-backup)
- **isync/mbsync:** the only GitHub hit is a stale 2013 mirror (gburd/isync, about 60 stars). [PK] Upstream development is on SourceForge — [GitHub](https://github.com/gburd/isync)
- **notmuch:** the GitHub repo is a mirror ("mirror of the http://git.notmuchmail.org/git/notmuch repository"), about 214 stars, pushed 2026-10-16. [PK] It is a Xapian-indexed Maildir tag and search engine — [GitHub](https://github.com/notmuch/notmuch)
- **Mail-Archiver** (s1t5/mail-archiver): about 2,211 stars, C#, GPL-3.0, pushed 2026-10-11, created 2025-05. A web app to archive, search and export emails from multiple accounts, with folder sync and mailbox migration — [GitHub](https://github.com/s1t5/mail-archiver)
- **OpenArchiver** (LogicLabs-OU/OpenArchiver): about 2,416 stars, TypeScript, AGPL-3.0, pushed 2026-10-16, created 2025-07. "Legally compliant email archiving" — [GitHub](https://github.com/LogicLabs-OU/OpenArchiver)
- **Bichon** (rustmailer/bichon): about 2,017 stars, Rust, AGPL-3.0, pushed 2026-10-16, created 2025-11-18. "Lightweight, high-performance Rust email archiver with WebUI" — [GitHub](https://github.com/rustmailer/bichon)
- **Piler** (jsuto/piler): about 353 stars, PHP, pushed 2026-10-07. The GitHub repo was created in 2024; [PK] the project is older, previously hosted on Bitbucket — [GitHub](https://github.com/jsuto/piler)
- **Stalwart** (stalwartlabs/stalwart): about 15,128 stars, Rust, license not detected by GitHub ([PK]: AGPL-3.0 plus a commercial SEL license), pushed 2026-10-15. An all-in-one mail and collaboration server (IMAP, JMAP, SMTP, CalDAV, CardDAV, WebDAV). It is a mail server, not an archiver. It appears to be the renamed stalwartlabs/mail-server, which did not resolve separately — [GitHub](https://github.com/stalwartlabs/stalwart)

### Inferences
- **For a personal app:** GYB (Apache-2.0) for Gmail via API, imapsync or mbsync for generic IMAP, and Maildir or EML as the canonical storage format. notmuch (Xapian) is the proven local index.
- **The 2025–26 web archivers** (Bichon, OpenArchiver, Mail-Archiver) show strong demand for "own your email archive" UIs. All are copyleft (AGPL or GPL).
- **Stalwart** only fits if the goal is self-hosting the mailbox itself. It is overkill for archiving.

### Gaps
- Storage backends of Bichon, OpenArchiver and Mail-Archiver (for example Postgres, embedded KV, or Meilisearch/Tantivy) were not verified in this session.

---

## Q6. Photo / media pulling

### Takeaway
Immich (about 116k stars, AGPL) is the de facto self-hosted Google Photos replacement. immich-go (about 7k) is the preferred importer for Google Photos Takeout. icloudpd (about 12.3k, MIT) remains the iCloud Photos puller, and osxphotos (about 3.9k, MIT) handles the local Apple Photos library. **gphotos-sync is archived and dead**: development stopped in Oct 2024 and the repo was made read-only on 17 Mar 2026. rclone (about 60k, MIT) is the universal cloud-storage mover.

### Cited Findings
- **Immich** (immich-app/immich): about 116,424 stars, TypeScript, AGPL-3.0, pushed 2026-10-16 — [GitHub](https://github.com/immich-app/immich)
- **immich-go** (simulot/immich-go): about 7,048 stars, Go, AGPL-3.0, pushed 2026-06-25 (Slow). An alternative to the Immich CLI that doesn't need Node.js and "tries its best for importing google photos takeout archives" — [GitHub](https://github.com/simulot/immich-go)
- **icloudpd** (icloud-photos-downloader/icloud_photos_downloader): about 12,325 stars, Python, MIT, pushed 2026-05-30 (Slow) — [GitHub](https://github.com/icloud-photos-downloader/icloud_photos_downloader)
  - boredazfcuk/docker-icloudpd (about 2,958 stars, pushed 2026-09) is its Docker wrapper — [GitHub](https://github.com/boredazfcuk/docker-icloudpd)
- **gphotos-sync** (gilesknap/gphotos-sync): about 2,083 stars, **archived = true**. The README says the project "was archived on Oct 4th 2024", and the repo was set to read-only on Mar 17, 2026 — [GitHub](https://github.com/gilesknap/gphotos-sync)
  - [PK] The cause is Google Photos Library API changes that removed read access to the full library, effective March 2025.
- **GooglePhotosTakeoutHelper** (TheLastGimbus/GooglePhotosTakeoutHelper): about 5,958 stars, Dart, Apache-2.0, **last push 2025-01-29 (Dormant)**. A fork, Xentraxx/GooglePhotosTakeoutHelper, did not resolve in search — [GitHub](https://github.com/TheLastGimbus/GooglePhotosTakeoutHelper)
- **osxphotos** (RhetTbull/osxphotos): about 3,911 stars, Python, MIT, pushed 2026-10-12. Exports and queries the Apple Photos library on macOS — [GitHub](https://github.com/RhetTbull/osxphotos)
- **rclone** (rclone/rclone): about 60,345 stars, Go, MIT, pushed 2026-10-16 — [GitHub](https://github.com/rclone/rclone)
- **PhotoPrism**: about 40,307 stars, Go, pushed 2026-10-16 — [GitHub](https://github.com/photoprism/photoprism)
- **LibrePhotos**: about 8,106 stars, Python, MIT, pushed 2026-10-16 — [GitHub](https://github.com/LibrePhotos/librephotos)

### Inferences
- Since Google closed full-library API access, **Google Takeout plus immich-go (or a Takeout JSON sidecar fixer)** is the only practical path for Google Photos. This is a known pain point: GPTH is dormant.
- **Reusable (MIT):** icloudpd, osxphotos and rclone. Immich and immich-go are AGPL.

### Gaps
- The gphotos-sync discussion thread (gilesknap/gphotos-sync-discussion#1) was not read, so the exact stated reason is from prior knowledge.

---

## Q7. Browser history tools

### Takeaway
Small but maintained: purarue/browserexport (about 215 stars, MIT) and karlicoss/promnesia (about 1.9k). Histre is a commercial SaaS, not OSS. ArchiveBox can ingest browser history for archiving.

### Cited Findings
- **browserexport** (purarue/browserexport): about 215 stars, Python, MIT, pushed 2026-08-09. Backs up and parses browser history databases (Chrome, Firefox, Safari and their derivatives) — [GitHub](https://github.com/purarue/browserexport)
- **Promnesia:** see Q2 — [GitHub](https://github.com/karlicoss/promnesia)
- **ArchiveBox** accepts "browser history/bookmarks" as input — [GitHub](https://github.com/ArchiveBox/ArchiveBox)
- **ActivityWatch's browser watcher**: see Q1 — [GitHub](https://github.com/ActivityWatch/activitywatch)

### Inferences
- Browser history capture is a solved, low-star niche. browserexport (MIT) is the obvious parser to reuse.

### Gaps
- pesos/browser-history did not resolve in search, so its status is unknown. Histre's non-OSS status is from prior knowledge.

---

## Cross-category summary: building blocks to reuse vs. dead

### Takeaway
Reuse the actively maintained, permissively licensed extractors and storage tools. Use the large copyleft or source-available products as references or competitors. Avoid the dormant and dead projects listed below.

### Cited Findings (summary of the data above; see the per-category sources)
- **Best-in-class, active, permissive (MIT, Apache, Unlicense, MPL, CC0):**
  - Lifelogging and activity: ActivityWatch (MPL-2.0) and Dayflow (MIT)
  - Hubs, parsers and storage: HPI and its exporters (MIT), browserexport (MIT), google_takeout_parser (MIT) and Datasette (Apache-2.0)
  - Exporters: yt-dlp (Unlicense), instaloader (MIT), DiscordChatExporter (MIT) and WhatsApp-Chat-Exporter (MIT)
  - Email and photos: GYB (Apache-2.0), icloudpd (MIT), osxphotos (MIT) and rclone (MIT)
  - Web archiving: ArchiveBox (MIT) and monolith (CC0)
- **Best-in-class, active, copyleft:**
  - Exporters: gallery-dl (GPL-2.0), imessage-exporter (GPL-3.0) and tdl (AGPL)
  - Web archiving and bookmarks: SingleFile, Karakeep, Linkwarden and Webrecorder (all AGPL)
  - Photos: Immich and immich-go (AGPL)
  - Hubs, lifelogging and location: Timelinize (AGPL, unstable), Khoj (AGPL), Dawarich (AGPL) and Windrecorder (GPL-2.0)
  - Email: Bichon, OpenArchiver (AGPL) and Mail-Archiver (GPL-3.0)
- **Source-available or commercial:** Screenpipe (Screenpipe Commercial License)
- **Dead, dormant or archived:**
  - Lifelogging: Selfspy (2019), rem (2024-05), Memento (2024-04) and OpenRecall (last push 2025-09)
  - Exporters: twitter-archive-parser (2022-11), reddit-user-to-sqlite (2023)
  - Email: Gmvault (2022-05)
  - Photos: gphotos-sync (archived), GooglePhotosTakeoutHelper original (2025-01)
  - Dogsheep importers: twitter-, google-takeout- and healthkit-to-sqlite (2022–23)
  - Other: Omnivore cloud (shut down Nov 2024; the self-host repo continues), flow-dashboard (unmaintained) and textile photos (archived)

### Inferences
- **The common architectural core** is: platform exporters, then raw archive files kept immutable, then normalization into SQLite with FTS (plus vector search), then a timeline or search UI, then MCP or local LLM access. This is visible in Screenpipe, Timelinize, Promnesia/HPI and Datasette.
- **Whitespace a new app could fill:**
  - A permissive, polished, cross-platform unified timeline. Timelinize is AGPL and unstable; HPI is developer-only.
  - Maintained Meta DYI and X archive parsers
  - Korean platforms (KakaoTalk and Naver)
  - Mobile-first capture
  - A consumer Rewind replacement now that Rewind is gone and Screenpipe has pivoted to enterprise and commercial
- **Licensing is the main constraint on reuse.** Many top projects are AGPL or GPL, so a closed-source or commercial app would have to call them as separate processes (CLI or subprocess) or reimplement them.

### Gaps
- Star counts are point-in-time snapshots from 2026-10-16. "Pushed" dates do not distinguish feature work from bot commits.
- The awesome-selfhosted, awesome-quantified-self and awesome-lifelogging lists and HN "Show HN" threads were not fetched directly because of the tool-call budget. Projects listed only there and not covered above may be missing.
