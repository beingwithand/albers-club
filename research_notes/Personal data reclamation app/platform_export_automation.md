# Platform Data Export Automation Playbook (as of Oct 16, 2026)

> Method note: direct page fetches failed in this environment (DNS and proxy blocks on developers.google.com, developers.facebook.com, dtinit.org and others). All findings below come from web-search result summaries that cite the listed URLs. Treat exact numbers as "verify on the primary page". Older items are marked **[older]**. Many requested platforms (Microsoft, Amazon, Snapchat, Discord, Telegram, Slack, Naver/Kakao product flows, and most consumer startups) returned no usable 2026 sources and are listed under Gaps rather than filled in from memory.

## Google: Takeout, Data Portability API, Gmail/Photos/YouTube APIs

### Takeout
Takeout is the consumer bulk export. It can run on a schedule (every 2 months for one year), but its archive links expire. The Data Portability API is the only official programmatic route: it supports 30- or 180-day recurring authorization with daily exports and time filters, but it is limited to the EEA, UK and Switzerland (US not confirmed). Since March 31, 2025, the Photos Library API can no longer read a user's whole library, and Gmail restricted scopes require a yearly CASA assessment.

### Cited Findings
- **Takeout scheduling:** scheduled archives are created every 2 months for one year, and the first runs immediately. Users enrolled in the Advanced Protection Program cannot use scheduled exports. — [Google Account Help: How to download your Google data](https://support.google.com/accounts/answer/3024190?hl=en)
- **Takeout link expiry:** an export download expires after 7 days. — [Wikipedia: Google Takeout](https://en.wikipedia.org/wiki/Google_Takeout)
- **Photos incremental Takeout (June 2026):** Google Photos now supports recurring exports that send only changed media after an initial full archive. It is still an archive workflow, not live sync. — [WinBuzzer, 2026-06-07](https://winbuzzer.com/2026/06/07/google-photos-makes-takeout-exports-recurring-backups-xcxwbn/)
- **Data Portability API (DPA) status:** the API reached GA on March 6, 2024. Time-based access went GA on February 20, 2025. — [DPA release notes](https://developers.google.com/data-portability/docs/release-notes)
- **DPA time-based access:** users choose a one-time export, 30 days or 180 days. With time-based access an app can export every 24 hours, and users can renew for another 6 months before the grant expires. — [DPA: Use time-based access](https://developers.google.com/data-portability/user-guide/time-based); [release notes](https://developers.google.com/data-portability/docs/release-notes)
- **DPA rate limit:** calling `InitiatePortabilityArchive` again within 24 hours returns `FAILED_PRECONDITION`. — [DPA release notes](https://developers.google.com/data-portability/docs/release-notes)
- **DPA time filters:** a request can be limited to a date window, for example the last 6 months, which enables incremental pulls. — [DPA: Apply time filters](https://developers.google.com/data-portability/user-guide/time-filter)
- **DPA geography:** a secondary source quotes Alphabet's DMA compliance report as saying the API is available to end users in all EEA countries, the UK and Switzerland. The same report says Pixel and Nest data were added on Dec 11, 2025. — [GitHub PR quoting Alphabet DMA report](https://github.com/Robbes/Ownpace/pull/1313)
- **DPA policy wording:** Google's policy describes the API as giving users in the EEA more control over their data. — [DPA user data & developer policy](https://developers.google.com/data-portability/policy)
- **Official country list:** Google's release notes point to the "Common Questions" section of the "Share a copy of your data with a third party" help page. I could not retrieve that list. — [release notes](https://developers.google.com/data-portability/docs/release-notes)
- **UK:** a CMA consultation says the DMA does not cover UK users and that Google offers the API in the UK voluntarily. — [CMA Data Portability Conduct Requirement consultation](https://assets.publishing.service.gov.uk/media/6979d0915da1fd4ddea98c73/_Data_portability_conduct_requirement_v2.pdf)
- **CMA conduct requirement (unconfirmed):** a single secondary source reports that the CMA imposed a Data Portability Conduct Requirement on June 17, 2026, with compliance due around mid-September 2026. — [anythingengineoptimization.com, 2026-10-01](https://anythingengineoptimization.com/item/2026-10-01-cma-google-must-extend-its-eu-data-portability-api-to-the-uk/)
- **Expansion timeline [older, ~Mar 2025]:** Google said it had no specific timeline for expanding the API beyond its current regions. — [DTI: Portability in Practice, a discussion with Google](https://dtinit.org/blog/2025/03/03/report-out-portability-in-practice)
- **Unverified apps:** a community GitHub issue investigates whether an unverified personal app keeps a 180-day DPA grant. It is not authoritative. — [GitHub issue](https://github.com/Atomtomate/constellate/issues/11)
- **Photos Library API (effective March 31, 2025):** the `photoslibrary.readonly`, `photoslibrary.sharing` and `photoslibrary` scopes were removed. Only `appendonly` and app-created-data access remain. Listing and reading now work only on content the app created. The Picker API replaces library-wide selection, and a new Photos API User Data and Developer Policy applies. — [Google Developers Blog](https://developers.googleblog.com/en/google-photos-picker-api-launch-and-library-api-updates/); [Photos API updates](https://developers.google.cn/photos/support/updates?hl=en)
- **Photos impact:** backup tools such as rclone lost full-library read access. Commentary notes the Picker API does not cover all earlier Library API uses, so Photos export effectively stays with Takeout. — [rclone forum](https://forum.rclone.org/t/add-the-new-google-photos-picker-api-to-rclone/47938); [GitHub PR](https://github.com/Robbes/Ownpace/pull/1313)
- **Gmail restricted scopes:** `gmail.modify`, `gmail.readonly` and full `mail.google.com` access trigger restricted-scope verification plus a CASA Tier 2 security assessment that renews every year. — [Nylas scopes reference](https://developer.nylas.com/docs/cookbook/use-cases/build/google-oauth-scopes/); [Unipile 2026 guide](https://www.unipile.com/integrating-google-oauth-2-0-user-authentication-into-your-app/)
- **CASA cost (vendor and secondhand figures):**
  - About $540 to $1k per year through self-serve labs; one developer reported paying $540 in January 2026. — [singhamandeep.com](https://singhamandeep.com/category/google-youtube-api/)
  - Leviathan Security lists Tier 2 at $3,000, $4,500 or $6,000 depending on turnaround. — [Leviathan](https://leviathansecurity.com/programs/google-casa-cloud-application-security-assessment)
  - The legacy track is cited at $15k to $75k. — [Unipile](https://www.unipile.com/integrating-google-oauth-2-0-user-authentication-into-your-app/)
  - One source says the App Defense Alliance self-scan path has been deprecated. — [singhamandeep.com](https://singhamandeep.com/category/google-youtube-api/)

### Inferences
- **EEA/UK/CH users:** the most robust automation is the Data Portability API with 180-day time-based consent, a daily or weekly cron and `start_time` filters for incremental pulls. Re-consent is needed every 180 days.
- **US users:** the realistic path is scheduled Takeout delivered to Drive, Dropbox, OneDrive or Box, with the app then reading the archive from that cloud via the cloud's own API. Google Drive itself requires a sensitive or restricted scope. Takeout scheduling stops after one year, so users must re-schedule.
- **Takeout as an automation target:** Takeout has no API. Scraping it hits Google sign-in risk challenges and 2FA, so it is impractical to automate.
- **Gmail:** Gmail read access through the Gmail API needs CASA every year. A DPA Gmail resource, where available, may avoid this cost; this needs verifying.

### Gaps
- The official 2026 DPA country list, including whether the US is covered, could not be retrieved.
- The full list of DPA resource groups and scopes for 2026 (for example `myactivity.*`, `youtube.*`, `mail`) could not be fetched. The DPA reference page should be checked.
- Takeout delivery destinations (Drive, Dropbox, OneDrive and Box are expected) and archive limits (2/4/10/50 GB splits) were not confirmed from a 2026 source.
- I found no source on whether My Activity or YouTube have standalone export APIs beyond Takeout and the DPA. The YouTube Data API does not expose watch history; this is from memory and was not verified in this pass.

## Meta: Facebook, Instagram, Threads, WhatsApp

### Takeaway
Meta's "Download/Export your information" in Accounts Center lets users pick a date range, HTML or JSON format and media quality. There is no confirmed self-serve schedule. The archive must be downloaded within 4 days of being ready. "Transfer your information" sends data only to approved destinations, most of them cloud storage, through Meta's Data Transfer Project integration. There is no third-party read API for personal Instagram or Facebook accounts.

### Cited Findings
- **Export options:** date range ("All time" for a full backup), HTML or JSON, and media quality. JSON is the format for programmatic parsing. — [Facebook Help: Export a copy of your information](https://www.facebook.com/help/212802592074644); [socialguardian.app 2026 guide](https://socialguardian.app/blog/backup-facebook-before-deleting-account/)
- **Download window:** once an export is ready, the user has 4 days to download it. — [Meta help: Meta AI/AI glasses export](https://www.meta.com/help/artificial-intelligence/1314808549771571/)
- **Delivery time:** a news report says it can take up to 30 days to receive an Instagram download link by email. — [Yahoo Tech tip](https://tech.yahoo.com/social-media/articles/one-tech-tip-delete-facebook-114258494.html)
- **Transfer destinations:** the transfer tool lists Google Photos, Dropbox, Backblaze B2, Koofr and Photobucket for photos and videos. Availability varies by country. Albums can arrive as "Copy of [album]". — [socialguardian.app: Facebook data transfer 2026](https://socialguardian.app/blog/facebook-data-transfer/); [Consumer Reports](https://www.consumerreports.org/digital-cameras-photography/how-to-transfer-facebook-photos-videos)
- **Becoming a destination:** developers apply through an onboarding form. Meta's infrastructure then authenticates to the partner's API using OAuth 2.0 Authorization Code and pushes data through the open-source Data Transfer Project. The docs were updated May 19, 2026. — [Meta Data Portability onboarding guide](https://developers.facebook.com/documentation/data-portability/onboarding-guide); [overview](https://developers.facebook.com/documentation/data-portability/overview)
- **Deep linking:** an April 2026 changelog entry added a locale parameter to the deep-linking integration, so third parties can send users straight into a localized export/transfer flow. — [Meta Data Portability changelog](https://developers.facebook.com/docs/data-portability/changelog)
- **Criticism [2025]:** all destinations Meta offers are cloud storage services and none are rival social platforms. — [Tech Policy Press](https://techpolicy.press/can-data-portability-shift-power-in-europes-digital-ecosystem)
- **No automatic transfer [older, ~early 2025]:** one source says Meta had not yet implemented an API or other automatic transfer for some data. — [Tech Policy Press: Building trust for data portability](https://www.techpolicy.press/building-trust-for-data-portability-within-the-dma-framework/)
- **Instagram Basic Display API:** it reached end of life on Dec 4, 2024. Only Business and Creator accounts are supported, through the Instagram Platform API. Personal accounts have no official API. — [Meta deprecations timeline](https://postgate.studio/blog/meta-api-deprecations); [deprecated-api.io](https://deprecated-api.io/en/apis/2024-12-04-meta-instagram-basic-display-api/); [DEV Community](https://dev.to/nick_johnson/instagram-basic-display-api-is-dead-build-what-works-instead-4ifm)
  - One GitHub gist says the API was fully sunset in September 2025, which conflicts with the other sources. — [gist](https://gist.github.com/jameschapman2c/65eff9f54a2d350b17a6ce5127b9fe42)

### Inferences
- **Practical automation:** use the deep link to send users into Accounts Center to request a JSON export, then have them upload the ZIP, or forward the email link before the 4-day expiry. The download requires a logged-in session and possibly re-authentication, so it cannot be fetched headlessly without risking account security checks.
- **Destination route:** becoming an approved transfer destination (a DTP-style receiving API) is the only official server-to-server path. It currently suits storage-like or media-centric receivers.

### Gaps
- No source confirmed whether Accounts Center now offers scheduled or recurring exports.
- Threads export specifics were not found.
- WhatsApp export details were not found: the "Request account info" report (about 3 days) and per-chat "Export chat" (.txt with or without media) are from memory and unverified.
- The full 2026 destination list, including any text or post destinations such as WordPress or Blogger, was not retrieved.

## Other Global Platforms: Apple, Microsoft, Amazon, TikTok, X, Reddit, LinkedIn, Snapchat, Spotify, Discord, Telegram, Slack

### Takeaway
Only TikTok and LinkedIn offer genuine user-consented programmatic portability APIs, and both are limited to EEA-plus users (TikTok: EEA and UK; LinkedIn: EEA and Switzerland). Everyone else is a manual request with a delay of days to 30 days and an expiring download. X sells access to the owner's own data cheaply through pay-per-use. Reddit is closing its public Data API by March 2027.

### Cited Findings
- **Apple:**
  - privacy.apple.com transfers of iCloud Photos to other services (for example Google Photos) take 3 to 7 days in most cases and up to 30 days. Apple uses the time to verify the request and run the transfer. — [Apple Support 118257](https://support.apple.com/en-us/118257)
  - The reverse direction, Google Photos to iCloud Photos, takes hours to a few days. — [Apple Support 120924](https://support.apple.com/en-us/120924)
  - The service launched in March 2021 **[older]**. — [MacRumors](https://www.macrumors.com/2021/03/03/apple-transfer-icloud-photos-google-photos/)
- **TikTok:**
  - The Data Portability API is available to qualified applicants globally, but it covers only users in the EEA and UK and returns no data for others. — [TikTok Data Portability API product page](https://developers.tiktok.com/products/data-portability-api/)
  - The launch in March 2024 covered the EEA only **[older]**. — [TechCrunch 2024](https://techcrunch.com/2024/03/04/tiktok-rolls-out-data-portability-api-ahead-of-europes-dma-regulatory-deadline/amp)
  - Users grant one-time or ongoing access through Login Kit. Scopes include `portability.activity.ongoing` and single-request variants, covering posts/profile, activity, DMs and the full archive. — [TikTok scopes reference](https://developers.tiktok.com/docs/en/tiktok-api-scopes); [TikTok blog](https://developers.tiktok.com/blog/2024-introducing-tiktok-data-portability-api)
  - Apps must pass a privacy and security review. — [TikTok product page](https://developers.tiktok.com/products/data-portability-api/)
  - UK coverage was confirmed. — [codepolicy.org](https://www.codepolicy.org/post/tiktok-confirms-data-portability-api-for-uk-users-three-down-three-to-go)
  - The 2026 DMA report says ByteDance further developed the API and the Download Your Data portal, and users can make one-off or recurring requests. — [SCiDA, 2026-04-02](https://scidaproject.com/2026/04/02/dma-compliance-reports-in-year-three-reading-between-the-many-lines/)
- **LinkedIn (Microsoft):**
  - The DMA Member Data Portability APIs have two parts:
    - the Member Snapshot API, a point-in-time export by domain;
    - the Member Changelog API, which records activity from consent onward and reaches back at most 28 days.
    — [Microsoft Learn: Member Data Portability](https://learn.microsoft.com/en-us/linkedin/dma/member-data-portability/member-data-portability-member); [Member Changelog API](https://learn.microsoft.com/en-us/linkedin/dma/member-data-portability/shared/member-changelog-api)
  - The APIs are available only to members in the EEA and Switzerland. — [Microsoft Learn: LinkedIn DMA](https://learn.microsoft.com/en-us/linkedin/dma)
  - Scope names differ between sources (`r_dma_portability_self_serve` vs `r_dma_portability_member`), and requests use the header `LinkedIn-Version: 202312`. — [Microsoft Learn](https://learn.microsoft.com/en-us/linkedin/dma/member-data-portability/shared/member-changelog-api); [singhamandeep.com](https://singhamandeep.com/?p=1558)
  - A developer used the API in March 2026 to retrieve CV data. — [NetEye blog 2026-03-18](https://www.neteye-blog.com/blog/2026/03/18/thanks-eu-linkedin-finally-gave-me-my-cv-data/)
- **X:**
  - Pay-per-use became the default on Feb 6, 2026, and the free tier closed to new signups. — [opentweet.io](https://opentweet.io/how-to/x-api-pay-per-use-explained); [postproxy.dev](https://postproxy.dev/blog/x-api-pricing-2026/)
  - Basic subscribers were migrated from June 1, 2026. — [opentweet.io](https://opentweet.io/how-to/x-api-pay-per-use-explained)
  - Reading a post costs $0.005, and owned reads (your own data) cost $0.001 per resource. — [opentweet.io](https://opentweet.io/how-to/x-api-pay-per-use-explained)
  - Full-archive search requires an upgrade or Enterprise (about $42k/month). — [xpoz.ai](https://www.xpoz.ai/blog/comparisons/twitter-x-data-access-options-compared-2026/)
  - These are third-party figures and some disagree.
- **Reddit:**
  - On Sep 30, 2026 Reddit announced it will:
    - stop new public API access requests after Oct 31, 2026;
    - turn off RSS on Nov 13, 2026;
    - cut unregistered apps from Jan 12, 2027;
    - close public Data API access in March 2027.
    — [TechCrunch 2026-09-30](https://techcrunch.com/2026/09/30/reddit-is-killing-rss-feeds-ending-public-api-access-because-of-ai-bots/); [PPC Land](https://ppc.land/reddit-to-halt-public-data-api-access-in-march-2027-as-14-000-apps-register/)
  - Developers are pushed to Devvit, which does not support Python, or to commercial agreements. Self-service OAuth app creation closed in late 2025 under the Responsible Builder Policy. — [looot.ai](https://looot.ai/blog/reddit-api-shutdown); [redditapis.com](https://www.redditapis.com/blogs/reddit-data-api-2026)
- **Spotify:**
  - Two export types: "Account data" covers roughly the last year of streaming; "Extended streaming history" covers the account's lifetime. — [mystats.music guide](https://mystats.music/guides/spotify-extended-history)
  - Delivery can take up to 30 days; users report anywhere from 1 to 14 days. — [mystats.music guide](https://mystats.music/guides/spotify-extended-history); [theodorehq](https://www.theodorehq.com/echo/blog/posts/download-spotify-streaming-history)
  - The archive is a ZIP of JSON files such as `Streaming_History_Audio_YYYY-YYYY_N.json`. — [mystats.music guide](https://mystats.music/guides/spotify-extended-history)
  - Many third-party analyzers accept uploads of these files. — [ListenStats](https://listenstats.com/)

### Inferences
- **No platform pushes exports to a webhook.** For every manual-request platform (Apple, Spotify, Meta, Snapchat, Discord and so on), an app's automation boundary is: deep-link the user to the request page, watch the user's email (with consent) for the "ready" message, and have the user download and upload the file, or forward it, before the link expires. The download step requires the user's logged-in session and 2FA.
- **A US-facing product will rely on file uploads** of DYI ZIPs for most platforms. Real-time APIs exist only for EEA/UK/CH users of Google, TikTok and LinkedIn, and for Meta only as a transfer destination.

### Gaps
- **Microsoft:** no 2026 sources were found on the privacy dashboard export, Graph-based export or Microsoft's DMA portability for Windows/Bing.
- **Amazon:** the "Request Your Data" flow and timing were not found (from memory: up to about 30 days; unverified). Amazon is a DMA gatekeeper, but I found no portability API details.
- **Snapchat, Discord, Telegram, Slack:** no sources were retrieved. From memory and unverified:
  - Snapchat "My Data" offers JSON/HTML with a date range.
  - Discord's data package takes up to 30 days.
  - Telegram Desktop exports locally in JSON or HTML.
  - Slack export depends on plan and workspace-admin role.
- **Apple portability:** Apple's DMA portability API (reportedly launched for EU users) was not found in this pass. The services covered by its transfer tool beyond Photos (for example Apple Music playlists to YouTube Music) were not confirmed.
- **Reddit personal data requests:** the GDPR/CCPA request process was not covered by the results.

## Korea: Naver, Kakao, MyData expansion

### Takeaway
Korea's PIPA "right to request transmission of personal information" took effect March 13, 2025 for medical and telecom data. A February 2026 decree amendment expands it to all sectors: from Aug 20, 2026 for public bodies, and from Feb 20, 2027 for large private processors. Naver and Kakao would plausibly be covered, but no company-specific export flows were found.

### Cited Findings
- **Original scope:** the right took effect March 13, 2025, limited to medical and telecom. — [Digital Today (JP)](https://www.digitaltoday.co.kr/jp/view/35788/mydata-right-to-request-personal-data-transfer-expanded-to-all-sectors-to-take-effect-in-august)
- **Expansion:** the State Council passed the PIPA Enforcement Decree amendment expanding the right to all sectors, announced Feb 10, 2026. — [korea.kr press release](https://www.korea.kr/briefing/pressReleaseView.do?newsId=156743965&call_from=rsslink); [Money Today 2026-02-10](https://www.mt.co.kr/tech/2026/02/10/2026021013342433758); [ETNews](https://www.etnews.com/20260210000384)
- **Phase-in:**
  - Public-system operators and third-party transmitters get a 6-month grace period.
  - Large private processors (average revenue over ₩180bn and either 1M+ data subjects or 50k+ subjects with sensitive or unique-ID data) get 1 year.
  - SMEs are exempt.
  — [ETNews](https://www.etnews.com/20260210000384); [byline.network](https://byline.network/2026/02/10-613/)
  - An August 2026 report says public coverage expands from the 20th (Aug 20, 2026) and large private firms follow on Feb 20, 2027. — [Nate News 2026-08-11](https://m.news.nate.com/view/20260811n27612); [datalaw.kr](https://datalaw.kr/posts/mydata-transfer-right-who-and-when/)
- **Delivery methods:**
  - Data subjects can download encrypted copies of information viewable on a website. — [Money Today](https://www.mt.co.kr/tech/2026/02/10/2026021013342433758)
  - Transfers should primarily use APIs.
  - Agents using scraping may only receive data in ways agreed in advance with the transmitter.
  - Scraping is being phased out. — [Digital Today](https://www.digitaltoday.co.kr/jp/view/35788/mydata-right-to-request-personal-data-transfer-expanded-to-all-sectors-to-take-effect-in-august); [Nate News](https://m.news.nate.com/view/20260811n27612)
- **Guidance:** PIPC published a revised guide on June 25, 2026. — [Digital Policy Alert](https://digitalpolicyalert.org/event/41001-personal-information-protection-commission-issued-revised-guide-on-right-to-request-transfer-of-personal-information-system); [korea.kr guide](https://www.korea.kr/archive/expDocView.do?docId=41320)
- **Pilot:** PIPC and KISA launched a MyData intermediary pilot for employment and education on July 14, 2026. — [PIPC notice](https://www.pipc.go.kr/eng/user/ltn/new/noticeDetail.do?nttId=3121)
- **"On MyData" portal:** a public "온마이데이터" portal lets individuals manage their information. — [korea.kr](https://www.korea.kr/briefing/pressReleaseView.do?newsId=156740495&call_from=rsslink)
- **Who must comply (opinion):** an op-ed says Naver, Kakao, Google/YouTube and Meta would all have to answer transfer requests. — [ETNews op-ed 2025-11-25](https://www.etnews.com/20251125000405)

### Inferences
- **Naver/Kakao timing:** they likely meet the large-processor thresholds, so API-based transmission duties would apply from about Feb 2027. A Korean-market app could register as a MyData intermediary or receiver, the 개인정보관리 전문기관 route.

### Gaps
- Naver's and Kakao's current self-download menus (내 정보 내려받기), formats and timing were not found.
- The exact data categories in scope per sector, and the intermediary registration requirements, were not retrieved.

## EU DMA Art. 6(9) Real-Time Portability APIs

### Takeaway
Art. 6(9) requires gatekeepers to give end users, and third parties they authorise, free, continuous and real-time portability. In practice:
- Google, TikTok and LinkedIn offer consented OAuth APIs.
- Meta acts mainly as a sender to approved destinations.

All of these APIs require developer vetting or security review, and they serve only users located in the EEA (plus the UK and CH in some cases). Developers report heavy verification friction.

### Cited Findings
- **The obligation:** Art. 6(9) requires effective portability of data provided or generated by end users, free of charge, including continuous and real-time access, both for users and for third parties they authorise. — [EC DMA developer portal: End user data portability](https://digital-markets-act.ec.europa.eu/developer-portal/end-user-data-portability_en)
- **Gatekeepers:** Alphabet, Amazon, Apple, Booking, ByteDance, Meta and Microsoft. LinkedIn is covered as Microsoft's designated core platform service. — [Tech Policy Press](https://www.techpolicy.press/building-trust-for-data-portability-within-the-dma-framework/)
- **Joint guidelines:** the Commission and EDPB draft guidelines (Oct 2025) say gatekeepers must authenticate authorised third parties and secure transmission, but are not responsible for downstream processing. — [EDPB joint guidelines PDF](https://www.edpb.europa.eu/system/files/2025-10/joint_com-edpb_gls_interplay_dma_gdpr_for_public_consultation_en.pdf); [Baker Botts](https://ourtake.bakerbotts.com/post/102lqcf/edpb-and-european-commission-issue-joint-guidelines-on-intersection-of-dma-and-gd)
- **Developer friction [Nov 2024]:** developers report cumbersome verification, unsuitable security assessments and poor communication from gatekeepers. — [MyData Global study](https://mydata.org/wp-content/uploads/2024/11/Interoperability-and-the-DMA-in-Action-Developers-Experiences-of-Data-Portability-API-Access.pdf)
- **No onboarding rules:** the DMA does not specify how or when gatekeepers must establish relationships with receiving parties. — [IPC paper 2024](https://www.informationpolicycentre.com/wp-content/uploads/2024/05/data_sharing_obligations_under_the_dma_-_challenges_and_opportunities_-_may24.pdf)
- **Per-gatekeeper status:** see the Google, TikTok, LinkedIn and Meta findings above.
- **Year-three compliance reports (2026):** an analysis of the year-three reports notes TikTok's recurring requests. — [SCiDA 2026](https://scidaproject.com/2026/04/02/dma-compliance-reports-in-year-three-reading-between-the-many-lines/)

### Inferences
- **US availability:** effectively none through the DMA APIs. A US consumer app cannot rely on them except for UK users (CMA pressure) and EEA/CH users.

### Gaps
- Apple's, Booking's, Amazon's and Microsoft's (Windows/Bing) Art. 6(9) API specifics for 2026 were not found.
- No usage statistics were found.

## Data Transfer Initiative / Data Transfer Project

### Takeaway
The DTI is a 501(c)(4) non-profit (launched in 2023) that houses the open-source Data Transfer Project. Its current focus is a "Data Trust Registry" and a badge of accreditation for trusted receivers, which addresses the vetting friction of DMA APIs.

### Cited Findings
- **Origins:** the DTP was announced in 2018 by Facebook, Google, Microsoft and Twitter. DTI launched on Mar 28, 2023 to house it **[older]**. — [DTI launch post](https://dtinit.org/blog/2023/03/28/launch); [DTI one-pager](https://dtinit.org/assets/dti-onepager.pdf)
- **Recent activity:** the DTI blog lists a Badge of Accreditation for services on its Data Trust Registry after a 6-month pilot, plus a 2025 annual report. Post dates were not visible. — [DTI blog](https://dtinit.org/blog/)
- **Regulatory roundup:** a June 2026 DTI global regulatory roundup exists; contents were not retrieved. — [DTI roundup June 2026](https://dtinit.org/blog/2026/06/09/global-roundup-june-2026)
- **Meta's use of DTP:** Meta's destination transfers run on DTP. — [Meta onboarding guide](https://developers.facebook.com/documentation/data-portability/onboarding-guide)
- **Google's DTP whitepaper:** Google has published a whitepaper on DTP. — [Google DTP whitepaper](https://services.google.com/fh/files/blogs/data-transfer-project-google-whitepaper-v4.pdf)

### Inferences
- **Accreditation as a shortcut:** DTI accreditation may become a shortcut for passing gatekeeper verification. This is worth pursuing for any receiving app.

### Gaps
- Whether Google, Meta or TikTok accept DTI accreditation in place of their own reviews is unconfirmed.

## Consumer Services Automating Export or Data Rights

### Takeaway
Existing services fall into three types:
1. **Authorized-agent request filers** (Permission Slip, which now works with DeleteMe; Incogni-style deletion services). These file deletion and opt-out requests; they do not retrieve data.
2. **Upload-based data pools** (Vana DataDAOs). These rely on users manually running Takeout or DYI exports and uploading them.
3. **Consented-API aggregators** (digi.me). No current 2026 status was found.

None of them fully automates downloading the export itself.

### Cited Findings
- **Permission Slip (Consumer Reports):**
  - It acts as a CCPA "authorized agent": the user signs an authorization and supplies email addresses, then CR files and follows up on requests. — [CR press release 2023](https://www.consumerreports.org/media-room/press-releases/2023/10/consumer-reports-introduces-free-permission-slip-by-cr-app-to-empower-consumers-to-take-back-control-of-their-personal-data/); [Techlicious](https://www.techlicious.com/blog/permission-slip-the-new-app-streamlining-data-privacy-requests/)
  - CR reports nearly 5 million requests processed.
  - A paid Plus tier sends opt-outs to 100+ data brokers. — [Google Play listing](https://play.google.com/store/apps/details?id=org.consumerreports.permissionslip.production)
  - The product has moved into a "Next Chapter with DeleteMe". — [CR Innovation blog](https://innovation.consumerreports.org/permission-slips-next-chapter-with-deleteme/)
- **Vana:**
  - DataDAOs collect user-contributed data, for example YouTube data via Takeout plus a browser extension, and anonymize it in TEEs. — [Medium post](https://medium.com/@deeptanshu.sankhwar/your-youtube-data-just-made-someone-50-000-this-month-and-it-wasnt-you-9ddb4347e000)
  - Users can be paid in tokens, and their data is encrypted with keys the DAO controls. — [Vana blog](https://vana.org/blog/accelerating-ai-data-revolution)
  - The `create-datadao` tooling includes data validation and contribution UIs. — [GitHub vana-com/create-datadao](https://github.com/vana-com/create-datadao)
- **Agent-based requests outside the US:** the Cornell research spotlight on CR studies how companies handle agent-submitted data-rights requests. — [Cornell PI](https://www.pi.tech.cornell.edu/spotlight/pegah)

### Inferences
- **Market gap:** no player combines automated request initiation, export retrieval and parsing across platforms. The bottlenecks are the authenticated download step and expiring links. An app could watch the user's inbox (with consent) for "your data is ready" emails and prompt a one-tap download and upload.

### Gaps
- No 2026 sources were found for digi.me, Gener8, Ethos, Datacoup (shut down around 2019 **[older, from memory]**), Cluster, Pogo, Mine (Saymine), Incogni or the "Data Rights Protocol" (CR-led standard for authorized-agent APIs). Their mechanisms and status need separate verification.
