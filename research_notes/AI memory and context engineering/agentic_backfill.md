# Agentic Backfill: One-Time Import of a User's Own Account History via Consented Browser/App Driving, Then Ongoing Logging (as of October 2026)

Scope note: consent-based, user's own logged-in accounts only. Bot-detection evasion is deliberately out of scope; the design principle throughout is that automation should be identifiable and should not be disguised. About 16 searches were run. Many sources found are third-party guides, vendor pages or extension listings rather than platform documentation, and they are flagged as such. Several sub-questions (Kakao/Naver, agent throughput numbers, Mem/Heyday/Dot/Personal.ai onboarding) returned little or nothing reliable. They are listed under Gaps rather than filled from memory.

## Per platform: what the official export includes vs misses, and what an agent must do to fill gaps

### Takeaway
Official exports tend to give you identifiers and links: post URLs, video links, IDs and timestamps. They usually leave out the content itself (titles, captions, media), anything deleted or unavailable, and some categories entirely. The clearest example is X bookmarks, which are not in the X archive. That makes "export first, then enrich" the right default. An agent or extension in the logged-in session is mostly needed for: (a) categories the export omits (X bookmarks), (b) enriching link-only rows (Reddit, TikTok, likely Instagram saved), and (c) structure the export may flatten (Instagram collections, Pinterest private boards).

### Cited Findings
**Instagram**
- No official Meta schema for `saved_posts.json` turned up. Third-party guides list the general export contents: posts, reels, stories, comments, likes, followers/following, DMs, search activity, ad info, login history, settings. Exports come as JSON or HTML. — [Redact](https://redact.dev/blog/instagram-data-file-download); [MultCloud](https://www.multcloud.com/explore/what-is-included-in-instagram-data-download-0121-ac.html)
- One guide reports that the liked-posts file in `your_instagram_activity` includes links to the posts. This suggests activity files carry links, but it was not confirmed for saved posts or collections. — [Redact](https://redact.dev/blog/instagram-data-file-download)
- Deleted posts, deleted messages, profile viewers and old story viewers are "not reliably included." — [Redact](https://redact.dev/blog/instagram-data-file-download)
- Timelinize's Instagram importer recognizes an export by paths such as `personal_information/personal_information/instagram_profile_information.json` and a `your_instagram_activity` folder. That is useful as a reference parser. — [Timelinize source (mirror)](https://gitdab.com/cobertos/timelinize/src/branch/main/datasources/instagram/instagram.go)
- Logged-in browser extensions fill the collection and media gap. "Instagram Exporter" (rxliuli) exports saved posts *including saved collections* to CSV with an optional media ZIP. It runs locally and requires the user to be logged in to Instagram in the browser. — [Chrome Web Store](https://chromewebstore.google.com/detail/aegonmaomboambpppdbbekomkmehplln); [Firefox listing](https://firefox.marketplace.browsertotal.com/de/firefox/addon/instagram-exporter/)
- Other extensions: "Instagram Saved Media Exp" (local, captures images/videos/reels/carousels with metadata); "Saved Posts Exporter" (captions, likes, comments, user info, timestamps as CSV/JSON/Excel); SaveVault (free tier capped at 250 saved posts, 50/day). The 50/day cap is a vendor-imposed pacing signal. — [chromeboard: Saved Media Exp](https://chromeboard.com/extension/instagram-saved-media-exp-hllpcahjefcijlmlnhlmhjemcgkgdghh); [chromeboard: Saved Posts Exporter](https://chromeboard.com/extension/saved-posts-exporter-opgclnehegaekpalmclkdaomgljpbadp); [SaveVault on hunted.space](https://webmail.hunted.space/product/savevault)
- `instagram-export` (npm) archives the all-saved page and individual saved-collection URLs into version-controlled archives. — [npm](https://npmjs.com/package/instagram-export)

**X (Twitter)**
- Bookmarks are excluded from the official X data archive. This comes from a vendor guide, so it is secondary. — [ContextBolt](https://contextbolt.com/blog/export-twitter-bookmarks/)
- Readwise imports X bookmarks through X's API after the user connects their account. It can optionally import all past bookmarks and then sync new ones once a day. Readwise labels the feature "experimental" and "relies on the stability of Twitter's API," and it cannot mark items as threads. — [Readwise docs](https://docs.readwise.io/readwise/docs/importing-highlights/twitter); [Readwise changelog](https://readwise.io/changelog/twitter-bookmarks)
- Session-based alternatives: an Obsidian plugin uses "your existing browser session (no API key or OAuth)"; the `bmarxs` CLI uses cookies imported from Chrome and exports CSV/JSON. — [Obsidian x-bookmarks-sync](https://community.obsidian.md/plugins/x-bookmarks-sync); [bmarxs on PyPI](https://pypi.org/project/bmarxs/)

**Reddit**
- The GDPR/data request is made at reddit.com/settings/data-request. `saved_posts.csv` rows contain an ID and a link only, with no titles, dates or content. Deleted posts leave dead links. — [ContextBolt export guide](https://contextbolt.com/blog/export-reddit-saved-posts/)
- Reddit surfaces only about 1,000 saves in the UI, so older saves may be missing from what an in-UI agent can see. Turnaround reports conflict: "up to 30 days" and one request per 30 days in one source, "a couple of days" in another. — [ContextBolt 1000 limit](https://contextbolt.com/blog/reddit-save-limit-workaround/); [ContextBolt oldest save](https://contextbolt.com/blog/oldest-reddit-save/)
- `reddit-stash` processes the GDPR export and fetches the full posts. — [reddit-stash](https://awesome.ecosyste.ms/projects/github.com%2Frhnfzl%2Freddit-stash)

**YouTube (Google Takeout)**
- Community tools report that Takeout watch history may cover only the last few years. Different exports contain different entry counts. Entries visible on the YouTube History page can be missing from Takeout, mostly for videos that are no longer available. Timestamps use ambiguous timezone abbreviations (EDT/PST), which can cause duplicates across archives. — [youtube-watched (GitHub)](https://github.com/VldmrB/youtube-watched); [youtubewatched (PyPI)](https://pypi.org/project/youtubewatched/)
- Takeout exports expire after 7 days and allow at most 5 downloads. — [takeoutday.org](https://takeoutday.org/guides/how-to-export-youtube-data)

**TikTok**
- The export is requested at Settings → Account → Download your data, in TXT or JSON. Delivery takes 24 hours to 4 days. It contains metadata and URLs, not MP4s. — [takeoutday.org](https://takeoutday.org/guides/how-to-export-tiktok-data); [TechCrunch](https://techcrunch.com/2025/01/17/tiktok-ban-how-to-download-your-videos-and-data)
- Browsing-history entries contain only a link and a date. Browsing history was missing when the user chose a custom export instead of "All data." — [Portmap/DTI](https://portmap.dtinit.org/articles/watch-history3.md/)
- `tikfav` downloads favorites from the export via a third-party RapidAPI service (free tier: 150 requests/month, 1 req/s). — [npm tikfav](https://www.npmjs.com/package/tikfav)

**Pinterest**
- No official Pinterest export documentation was found. The userscript "Pinback Next" exports pin links to HTML and notes that private boards must be exported individually. — [Greasy Fork](https://greasyfork.org/scripts/489596-pinback-next)

**Facebook / Google Takeout ingestion reference**
- Timelinize has file-based Facebook and Instagram importers and accepts Google Takeout. It copies data into a local folder with a SQLite DB. Its Facebook importer has a username option because "with multi-archive exports, there's no guarantee that the profile information is in the first archive." — [Timelinize Facebook source](https://gitdab.com/cobertos/timelinize/src/branch/main/datasources/facebook/facebook.go); [dsebastien notes](https://notes.dsebastien.net/30+Areas/33+Permanent+notes/33.02+Content/Timelinize)

**Rate limits / account safety (Instagram)**
- Instaloader tracks its own request count and retries after an assumed temporary ban (HTTP 429) expires. Frequent restarts are "prone to cause a 429" because the rate controller assumes a fresh budget. Cloud, VPN and proxy IPs face stricter anonymous limits, while logged-in access "do[es] not seem to be affected." — [Instaloader troubleshooting (mirror)](https://git.sudo.is/mirrors/Instaloader/src/branch/master/docs/troubleshooting.rst)
- The Instaloader changelog records rate-control retuning to match Instagram's limits and warns that logged-in limits can be stricter. This contradicts the troubleshooting doc's note above, so the evidence is mixed. — [pyup changelog](https://pyup.io/packages/pypi/instaloader/changelog?page=13)

### Inferences
- Per-platform plan:
  - **Instagram:** export first for likes and saved links, then open the Saved page once per collection for collection membership, captions and media.
  - **X:** bookmarks must come from the logged-in session or API, since the export has none. Paginate the Bookmarks timeline.
  - **Reddit:** the GDPR CSV gives the complete ID list beyond the 1,000-item UI cap. Then enrich each ID by opening the permalink, or via Reddit's JSON endpoints in the user's session.
  - **YouTube:** Takeout first, then optionally scroll myactivity or the History page for recent entries Takeout missed.
  - **TikTok:** export gives the links. Opening each link only adds captions and author info, and is costly.
  - **Pinterest:** walk each board, including each private board individually.
- Session-bound extensions (Instagram Exporter, the Obsidian X plugin, bmarxs) show the dominant pattern for gap-filling. They read the platform's own internal data as the logged-in page loads it, rather than reading pixels. This is roughly 10–100x cheaper than a vision agent per item. That is an estimate from architecture, not a measured figure.
- Account-safety design: pace slowly, run from the user's normal residential IP and browser profile, and avoid restart storms (the Instaloader lesson). Checkpoint so a resume does not re-fetch. Cap daily volume; SaveVault's 50/day is one conservative reference point.

### Gaps
- No primary Meta documentation was found confirming whether `saved_posts.json` includes collection names or media; it is unverified whether collections appear in the export.
- **Kakao (KakaoTalk, KakaoStory) and Naver (blog, cafe, bookmarks/MY):** no sources were retrieved on export contents or tools.
- **Facebook "Saved" items export details, Google (Chrome history, Maps saved) Takeout specifics, and the Pinterest official export:** not researched in depth or not found.
- No user-reported concrete thresholds (items/hour before a block) for Instagram, X or Pinterest were found from gallery-dl or yt-dlp issue trackers in this pass.

## Agent tech for long-running backfills: throughput, cost, failure modes, resume

### Takeaway
No credible published benchmark measures items per hour or cost per 1,000 items for consumer-account backfills. Available figures are self-reported success rates on WebVoyager and per-step estimates. The pragmatic architecture is a deterministic, cached extraction script running in the user's own persistent browser profile. A vision or LLM agent handles only exceptions: layout changes, login/2FA, "load more" quirks.

### Cited Findings
- Claude in Chrome reached general availability on August 26, 2026, for paid plans (Pro, Max, Team, Enterprise; not Free) at no extra charge. A per-action safety classifier checks that actions match the user's instructions, and it asks for approval at sensitive moments. These come from third-party coverage. An earlier review said Pro users were limited to Haiku 4.5, which may have changed. — [Gigazine](https://gigazine.net/gsc_news/en/20260827-claude-chrome-available/); [ai-toolbox pricing](https://www.ai-toolbox.co/claude-models/claude-pricing-plans-2026); [Composite review](https://composite.com/blog/claude-chrome-reviews-pricing-alternatives)
- browser-use reports 89.1% on WebVoyager (self-measured, December 2024, 586 tasks). Skyvern reports 85.8% (635 tasks). The denominators differ, so the numbers are not directly comparable. — [Skyvern blog](https://www.skyvern.com/blog/browser-use-vs-stagehand-which-is-better/); [awesomeagents](https://awesomeagents.ai/tools/best-ai-browser-automation-tools-2026/)
- Stagehand caching: "first run uses LLM inference and caches; subsequent runs reuse cached action (no LLM cost)." This is the main cost lever for repetitive flows. — [Stagehand docs: cost optimization](https://docs.stagehand.dev/v3/best-practices/cost-optimization)
- Per-action LLM agents take 2–5 s per step with high token consumption. A 10-step browser-use task costs about $0.07 (single unverified review). Hosted browser-hours are billed on wall-clock time, not compute. — [devtoollab](https://devtoollab.com/blog/best-ai-browser-automation-tools); [agenticwire](https://www.agenticwire.news/article/browser-use-vs-stagehand)
- Skyvern's Web Bench capped agents at 50 steps per execution. Long tasks need decomposition. — [Fondo on Web Bench](https://fondo.com/blog/web-bench-by-skyvern-launches-4b64a)

### Inferences
- Rough throughput arithmetic, an inference to be validated:
  - **Pure screenshot agent:** at 2–5 s/step and about 2–4 steps per item (scroll, open, read, back), it runs at roughly 300–900 items/hour. At about $0.007/step, that is about $15–30 per 1,000 items.
  - **Cached or deterministic DOM extraction:** list pages yield 10–50 items per scroll with near-zero LLM cost. In that case platform pacing, not the model, is the throughput limit.
- Failure modes to plan for:
  - virtualized infinite-scroll lists that unmount earlier items, so de-duplicate by post ID
  - session expiry or 2FA mid-run
  - soft rate limits or "try again later" pages
  - deleted or unavailable items
  - UI A/B variants
  - prompt injection from page content (captions, comments) steering the agent
- Checkpoint and resume design:
  - Keep a cursor per platform/collection: last seen item ID and timestamp.
  - Use an append-only local store keyed by canonical item ID.
  - Make every write idempotent.
  - Treat the newest-first order as the resume anchor: backfill walks downward until it reaches the export's oldest ID, or the end.
  - Ongoing logging walks from the top until it meets an already-seen ID.
- Local models (UI-TARS, Qwen-VL) suit the exception-handling role on-device for privacy. No throughput data was found.

### Gaps
- No primary data was found on OpenAI ChatGPT agent or Gemini computer-use pricing per step in 2026, or on UI-TARS/Qwen-VL throughput.
- No published items/hour figures were found for any of these tools on social-feed backfills.

## Legitimate agent identification vs evasion; ToS and legal context

### Takeaway
Web Bot Auth, now an IETF Standards Track draft (September 2026), gives agents a cryptographic, non-deceptive way to identify themselves. However, it is designed for cloud/remote browsers, and a local agent in the user's own Chrome generally sends ordinary user traffic. Platform ToS (e.g., Instagram's "automated means" clause) still prohibit automated collection without permission, even for one's own account. The Ninth Circuit's August 2026 Amazon v. Perplexity ruling favors user-directed agents under the CFAA, but it does not resolve contract/ToS exposure.

### Cited Findings
- `draft-ietf-webbotauth-httpsig-protocol-00` (September 2026, authors from Cloudflare and Google, Standards Track) defines a `Signature-Agent` header, a JWKS key directory and a well-known URI. It is built on HTTP Message Signatures (RFC 9421). — [IETF datatracker](https://datatracker.ietf.org/doc/html/draft-ietf-webbotauth-httpsig-protocol)
- Cloudflare "signed agents": the agent's infrastructure or remote browser platform signs requests, and Cloudflare validates them. — [Cloudflare blog](https://blog.cloudflare.com/zh-tw/signed-agents)
- Reported adoption: ChatGPT's cloud browser signs as `https://chatgpt.com`; a subset of Google-Agent requests sign as `https://agent.bot.goog`; AWS Bedrock AgentCore Browser has a preview. These are secondary reports. — [contextbolt](https://contextbolt.com/blog/web-bot-auth/); [ppc.land](https://ppc.land/web-bot-auth/)
- Instagram terms bar collecting information "in an automated way without our express permission," and Instagram's help center defines scraping as automated access and collection that it works to detect and block. — [Instagram Help](https://help.instagram.com/581066165581870); [court-hosted copy of terms](https://www.lb7.uscourts.gov/documents/19-1861URL1Termsofuse.pdf); [Open Terms Archive memo](https://opentermsarchive.org/en/memos/instagram-blocks-data-retrieval-and-clarifies-what-information-it-retrieves/)
- One third-party page reports Meta Automated Data Collection Terms effective October 7, 2024, but this was not verified against Meta's own page. — [vorplabs](https://vorplabs.com/agent-tools/instagram-api)
- **Amazon v. Perplexity (9th Cir., reported early August 2026):** the court vacated the March 2026 preliminary injunction against the Comet agent. It found the district court abused its discretion on the CFAA and California CDAFA likelihood-of-success analysis. Judge Milan Smith Jr. wrote that it is the *user* who "accesses" Amazon's computers with the Assistant's help. The opinion said an injunction would impair consumer choice and limit a nascent technology. The case is remanded and still pending. Reports call it the first federal appellate ruling on AI agents accessing platforms for users. — [Courthouse News](https://courthousenews.com/ninth-circuit-lifts-block-on-ai-powered-shopping-assistant/); [MediaPost](https://www.mediapost.com/publications/article/417007/appeals-court-sides-against-amazon-lifts-perplexi.html?edition=); [Northeast Times](https://northeasttimes.com/2026/08/06/appeals-court-sides-with-perplexity-ai-in-amazon-shopping-dispute/)
- **Meta v. Bright Data (N.D. Cal., Judge Chen, 2024):** summary judgment for Bright Data on breach of contract. The court found Meta's terms govern account holders' use, so logged-off scraping of public data was not "use." Meta dropped the case and waived appeal. The ruling's logic cuts the other way for logged-in access, where the terms do bind the account holder. — [Farella Braun + Martel](https://www.fbm.com/post/102kqw7/); [Zyte](https://www.zyte.com/blog/california-court-meta-ruling); [MediaPost](https://www.mediapost.com/publications/article/393996/None)

### Inferences
- **Legal posture for a consent-based, own-account backfill:** CFAA/CDAFA risk looks reduced after Perplexity, since the user is the accessor. Contract risk remains, because the user is bound by the ToS while logged in (the Bright Data logic). The realistic consequence is account action (temporary block or checkpoint) rather than litigation against an individual.
- **Design rules:**
  - Prefer the official export and official APIs.
  - Keep agent volume human-scale.
  - Never spoof user agents or fingerprints.
  - When running in a cloud or remote browser, use Web Bot Auth signing.
  - Disclose to the user that platform ToS may prohibit automated collection, and let them choose per platform.
- The district court's March 2026 theory, "with the user's permission but without the platform's authorization," is the counter-argument that could return on remand.

### Gaps
- The exact case number and date of the Ninth Circuit opinion were not verified from the primary opinion.
- Not researched: the X, Reddit, TikTok, Pinterest, YouTube, Kakao and Naver ToS clauses on automation of one's own account, and the EU GDPR Art. 20 / DMA data-portability angle.

## Prior products doing onboarding backfill

### Takeaway
The evidence found shows two main ingestion patterns. One is file import of official exports: Timelinize, Readwise-style connectors, reddit-stash. The other is continuous capture going forward without historical backfill: Rewind/Limitless, Screenpipe. Little reliable information was found on Mem, Recall, Heyday, Dot, Personal.ai or Vana onboarding flows.

### Cited Findings
- Rewind (macOS, 2022) rebranded to Limitless in April 2024 and shifted to cloud plus the Pendant. Meta acquired Limitless on December 5, 2025. Rewind Mac screen and audio capture was disabled on December 19, 2025, and EU/UK users had to export data before deletion. — [stork.ai](https://www.stork.ai/en/rewind-ai); [the-web-radar](https://the-web-radar.com/companies/limitless.ai)
- Screenpipe is an open-source alternative that captures screen and audio continuously with local indexing (vendor-adjacent pages). — [memx alternatives](https://memx.app/alternatives/rewind-ai/)
- Timelinize workflow: export from services, import into Timelinize, data is copied into a local SQLite plus folder. The project warns the schema may change and recommends keeping original exports. — [dsebastien notes](https://notes.dsebastien.net/30+Areas/33+Permanent+notes/33.02+Content/Timelinize); [zeabur listing](https://bunny.zeabur.com/templates/0998TB)
- Vana: an EVM L1 with Data Liquidity Pools and Proof-of-Contribution validation of uploaded user data, per a non-official crypto site. No connector or extension flow was confirmed. — [OneKey](https://onekey.so/ar/cryptos/vana-30237a/)
- Readwise: OAuth/API connect, a one-time historical import, then daily sync. This is the model "backfill then ongoing" pattern. — [Readwise docs](https://docs.readwise.io/readwise/docs/importing-highlights/twitter)

### Inferences
- Rewind/Limitless shows that "capture from now on" alone gives a cold start. The Meta acquisition and shutdown also show the importance of letting users keep raw exports locally, which Timelinize explicitly advises.

### Gaps
- No sources were retrieved on Mem.ai, Recall (getrecall.ai), Heyday, Dot (New Computer), or Personal.ai ingestion. Vana's official data-connector docs were not found.

## UX: progress, user presence for login/2FA, pausing, visible indicator

### Takeaway
There is little published UX research, but existing tools suggest a pattern:
- **Approval and visibility:** an explicit approval at sensitive moments (Claude in Chrome) and work done locally in the user's visible, logged-in browser (extensions).
- **Pacing:** caps on daily volume (SaveVault 50/day).
- **Incremental sync:** a one-time historical import followed by scheduled sync (Readwise daily).

### Cited Findings
- Claude in Chrome asks for approval at sensitive moments and runs a classifier on each action. — [Composite](https://composite.com/blog/claude-chrome-reviews-pricing-alternatives); [tygartmedia](https://tygartmedia.com/claude-in-chrome/)
- Extensions emphasize "runs locally in your browser" and require the user to be logged in. — [Instagram Exporter listing](https://chromewebstore.google.com/detail/aegonmaomboambpppdbbekomkmehplln)
- Readwise offers an opt-in "import all past bookmarks" and then a daily sync. — [Readwise docs](https://docs.readwise.io/readwise/docs/importing-highlights/twitter)
- Export latency sets user expectations: TikTok takes 24 h–4 d, Reddit "days to 30 days," and Takeout links expire after 7 days or 5 downloads. — [takeoutday TikTok](https://takeoutday.org/guides/how-to-export-tiktok-data); [ContextBolt Reddit](https://contextbolt.com/blog/export-reddit-saved-posts/); [takeoutday YouTube](https://takeoutday.org/guides/how-to-export-youtube-data)

### Inferences (recommended hybrid design)
1. **Day 0, request exports.** Request every official export in parallel: Takeout, Meta Accounts Center, Reddit, TikTok "All data", X archive. Show a per-platform card ("requested, ETA 1–4 days"). Remind the user before Takeout links expire.
2. **Day 0, immediate gap-fill for categories no export covers (X bookmarks, Instagram collections).** Run in the user's visible browser tab group with a persistent "Agent is reading your Instagram Saved" banner and a per-platform pause/stop button. Show a counter with items captured, the current collection and the estimated remaining.
3. **On export arrival, parse locally** (Timelinize-style parsers), then compute the diff: IDs present in the export but lacking content, plus categories absent from the export. Queue the enrichment jobs at a human-scale pace with a daily cap. Persist checkpoints so the job is resumable across reboots.
4. **User presence.** Pause and notify on login, 2FA or checkpoint screens; never automate credentials or CAPTCHA. Stop the platform entirely on any rate-limit or "suspicious activity" interstitial, and surface it to the user.
5. **Switch to ongoing logging.** Prefer official APIs where they exist (e.g., Readwise-style daily X sync), then lightweight "top-of-feed until seen ID" checks, then on-device capture.
6. **Transparency.** Keep a per-platform ToS risk note at consent time, a local audit log of every page the agent visited, and raw exports retained locally.

### Gaps
- No user studies or published UX patterns were found specifically for long-running agent backfills (progress estimates, interruption tolerance).
