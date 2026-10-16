# Capture layer for a personal-data vault (status as of Oct 16, 2026)

Method note: 15 web searches/fetches. Direct fetches of developers.google.com and some blogs failed (DNS errors in the sandbox), so several claims rest on search-result summaries of official pages. Items labelled "[background, unverified this session]" come from prior knowledge (cutoff around mid-2026). They are kept out of Cited Findings and listed under Inferences or Gaps so the report writer can weigh them.

## 1. Browser capture (extensions, profile files, mobile, share sheet, existing tools)

### Takeaway
Browser history and bookmarks are still the easiest source to capture. The vault can use a desktop extension or read the SQLite profile files directly. The "read-later" and "lifelog" market has consolidated hard. Pocket (July 2025), Omnivore (2024) and Rewind/Limitless (Dec 2025, bought by Meta) are all gone, which leaves self-hosted tools like Karakeep and Linkwarden, plus Screenpipe and Microsoft Recall for screen capture. Each shutdown makes the case for user-owned capture.

### Cited Findings
- **Pocket:** shut down on July 8, 2025 and then went export-only. Mozilla's dates for the export cutoff changed over time: an early version said Oct 8, 2025, later versions say export stayed live until Nov 12, 2025, after which "all user data has been queued for permanent deletion." — [Mozilla Support: Pocket has shut down](https://support.mozilla.org/en-US/kb/future-of-pocket); [CyberInsider](https://cyberinsider.com/mozilla-to-shut-down-pocket-service-in-july-to-allow-exports-until-october/)
- **Pocket export format:** a CSV file, not per-article HTML. Karakeep can import that CSV. — [Android Authority](https://www.androidauthority.com/export-pocket-library-3564819/)
- **Limitless (formerly Rewind):** Meta acquired it in early December 2025 and moved the team into Reality Labs. The $99 pendant is no longer sold. Existing users get support for at least one year on a free Unlimited plan. — [TechCrunch via scour.ing, Dec 5, 2025](https://scour.ing/@emschwartz/p/https://techcrunch.com/2025/12/05/meta-acquires-ai-device-startup-limitless); [BetaNews, Dec 8, 2025](https://betanews.com/2025/12/08/meta-has-acquired-limitless-a-startup-that-produces-ai-powered-wearables/)
- **Rewind/Limitless shutdown details:** the Rewind desktop app's recording features were disabled on Dec 19, 2025, along with recording in Limitless's own web and desktop apps. Service ended in the EU, UK, Brazil, Israel, South Korea, Turkey and China, with Dec 19, 2025 as the export deadline. — [usecarly blog](https://www.usecarly.com/blog/meta-limitless-acquisition/); [Sacra](https://sacra.com/research/why-meta-bought-limitless/) (secondary sources; I did not see Limitless's own notice)
- **Screenpipe:** MIT-licensed, local-first, runs 24/7 and captures screen and audio on macOS, Windows and Linux. It stores data in local SQLite and reads text through accessibility APIs, with OCR as a fallback. Access is through a desktop UI, a REST API and an MCP server. A directory listing put it at about 19k GitHub stars (June 2026). The managed app is sold as a roughly $400 lifetime license. These figures come mostly from the vendor's own blog. Resource-use claims conflict: the vendor says 1–3% CPU and about 2 GB/day, while a review says 5–10% CPU and 5–10 GB/month. — [screenpi.pe blog](https://www.screenpi.pe/blog/best-rewind-ai-alternative-2026); [aicoolies review](https://aicoolies.com/reviews/screenpipe-review); [enterprisedna directory](https://enterprisedna.co/directories/apps/screenpipe)
- **Microsoft Recall export (EEA only):**
  - Users can export snapshots from the last 7 days, the last 30 days, or all time, or turn on continuous export. Setup is in Settings > Recall & Snapshots and needs Windows Hello.
  - A one-time export code is shown when saving is first enabled. It decrypts the export, and Microsoft does not store or recover it. Losing it means resetting Recall, which deletes all snapshots.
  - Third-party apps can read exports only when given both the code and the folder path.
  - Export is per user, and admins cannot start it on someone else's behalf.
  - [Microsoft Support: Export Recall snapshots](https://support.microsoft.com/windows/export-recall-snapshots-680bd134-4aaa-4bf5-8548-a8e2911c8069); [The Register, Jun 16, 2025](https://theregister.com/2025/06/16/microsoft_snapshot_export_recall)
- **Recall in the EEA:** it reached the EEA in 2025, with export arriving in Release Preview build 26100.4762 (July 2025). — [Windows Insider Blog](https://blogs.windows.com/windows-insider/2025/07/10/releasing-windows-11-build-26100-4762-to-the-release-preview-channel)

### Inferences
- **Recall as a vault source:** Recall's encrypted export to a folder, readable by third parties, is an official way to pull Windows activity into a vault. It exists only in the EEA, which is likely a DMA/GDPR-driven feature.
- **Chrome extension APIs [background, unverified this session]:**
  - `chrome.history` gives search and getVisits. It returns about 90 days of history, matching Chrome's own retention.
  - `chrome.bookmarks` gives the full tree. `chrome.tabs` and `chrome.tabGroups` give open tabs. `chrome.sessions` gives recently closed tabs and tabs on other synced devices (`getDevices`).
  - Under Manifest V3, background pages are replaced by service workers that are terminated when idle, so continuous capture needs `chrome.alarms` or event wake-ups. Remotely hosted code is banned. `webRequestBlocking` is gone for most extensions. Page-content capture uses `chrome.scripting` with host permissions. Native messaging can hand data to a local vault daemon.
  - Firefox supports MV3 but keeps blocking webRequest and event pages. Safari Web Extensions (macOS and iOS) support a WebExtensions subset including tabs and bookmarks (read-only on iOS), but history access is limited.
- **Profile files on disk [background]:** this is the most complete source and needs no extension.
  - Chrome/Edge/Brave keep `History` (SQLite: urls, visits), `Bookmarks` (JSON), `Login Data` (encrypted) and `Sessions/`. The database is locked while the browser runs, so tools copy it first.
  - Firefox keeps `places.sqlite` (history and bookmarks) and `sessionstore-backups/*.jsonlz4`.
  - Safari keeps `~/Library/Safari/History.db`, which needs Full Disk Access on macOS.
  - HPI (karlicoss) and promnesia already parse all of these.
- **Mobile [background]:**
  - Chrome on Android and iOS has no extensions.
  - Firefox for Android supports the full add-on catalog (since late 2023).
  - Safari on iOS supports Safari Web Extensions distributed through the App Store.
  - Mobile capture otherwise has to use the iOS and Android share sheet (a share extension or intent), which is the main capture path in Raindrop, mymind, Karakeep and Linkwarden.
  - Some third-party Android browsers (e.g. Kiwi, discontinued in 2025, and Edge Canary) experimented with extensions.
- **Other existing tools [background]:**
  - ArchiveBox: self-hosted; uses SingleFile, wget, Chromium and yt-dlp; imports browser history and bookmarks.
  - SingleFile: extension that saves a page as a single HTML file.
  - Karakeep (formerly Hoarder, renamed in 2025): self-hosted, AI tagging, mobile apps and extension.
  - Linkwarden: self-hosted with page preservation.
  - Omnivore: shut down Nov 2024 after the team joined ElevenLabs.
  - Memex/WorldBrain: still exists but is low-activity.
  - Raindrop and mymind: cloud SaaS, with export available.

### Gaps
- I could not fetch current Chrome MV3 docs (developers.chrome.com was not tried because of fetch failures on Google domains). Exact 2026 limits are unverified: history retention, `sessions` device data, and any new limits on extension service workers.
- No 2026 primary source on the Limitless pendant past the one-year support window (that floor ends around Dec 2026).
- I did not verify current GitHub status for ArchiveBox (v0.8/v0.9 progress), Karakeep, Linkwarden or Memex.
- No 2026 Recall changes were found. The 2025 note about broken export on Entra-joined EEA devices may be out of date.

## 2. Cloud accounts (Google, Apple, Microsoft, DTI, DMA, tools)

### Takeaway
Google cut off third-party backup of Google Photos libraries on March 31, 2025, so Photos now needs Takeout or the Data Portability API. That API was officially limited to the EEA/UK as of 2025, so outside Europe, scheduled Takeout plus file sync (rclone, Drive API) is the realistic path. Timelinize and HPI are the main open-source tools that pull exports into one local timeline.

### Cited Findings
- **Google Photos API change** (announced Sept 2024, effective March 31, 2025):
  - The `photoslibrary.readonly`, `photoslibrary.sharing` and `photoslibrary` scopes were removed, and calls relying on them return 403 PERMISSION_DENIED.
  - The Library API now only works on media and albums the app itself created or uploaded.
  - Apps should use the new Picker API, where the user selects items in the Google Photos UI.
  - [Google Developers Blog](https://developers.googleblog.com/en/google-photos-picker-api-launch-and-library-api-updates/); [Google Photos API updates page](https://developers.google.cn/photos/support/updates?hl=en)
- **Effect on rclone and similar tools:** maintainers found the Picker API a poor fit for a backup backend, and users said they could no longer back up their libraries with these tools. — [rclone forum](https://forum.rclone.org/t/add-the-new-google-photos-picker-api-to-rclone/47938)
- **Google Data Portability API availability:** features went GA on Feb 20, 2025, but the API is limited to a country list. Per a DTI report, "some portability APIs are only available in select jurisdictions, notably the EU and UK." Google said it is "exploring additional availability" with no timeline. — [Data Portability API release notes](https://developers.google.cn/data-portability/docs/release-notes?hl=en); [DTI blog, Mar 3, 2025](https://dtinit.org/blog/2025/03/03/report-out-portability-in-practice)
- **Timelinize:**
  - Open source (AGPL-3.0) and local-first, written in Go with SQLite. Runs on Windows, macOS and Linux.
  - Ingests photos, videos, messages, location history and social-media exports into one timeline, with deduplication, an HTTP API and a CLI.
  - Still pre-1.0, and schema changes can require re-ingesting data. A listing reports v0.0.28 (2025-10-17), with the listing itself updated May 2026.
  - [Gigazine, Oct 8, 2025](https://gigazine.net/gsc_news/en/20251008-timelinize); [dev.co listing](https://dev.co/devops/open-source/timelinize); [feedbagel](https://feedbagel.com/post/timelinize-local-data-management-for-personal-digital-archives)

### Inferences
- **Google Photos workarounds:** the 2025 change ended the gphotos-sync and rclone-gphotos model of full-library sync. The options now are:
  - Takeout, which can be scheduled every 2 months for a year [background] and delivered to Drive, Dropbox, OneDrive or Box.
  - The Data Portability API (EEA/UK) with time-based, recurring access [background: it supports a `time_based` 30/180-day access type and incremental exports for some resources].
  - Device-side upload (the phone's own photo roll).
  - The rclone Google Photos backend is now effectively write-and-app-uploaded-only [inference from the scope removal].
- **Drive API v3 [background]:** with `drive.readonly`, it can still list and download all files, using `changes.list` for incremental sync. Google Docs formats must be exported via `files.export`, and the 10 MB export limit applies. `drive.readonly` is a restricted scope that needs a CASA security assessment for public apps. That is a real cost for a vault app; the alternative is to let users bring their own OAuth client.
- **Apple [background]:** privacy.apple.com lets users request a data copy (manual, takes days). Apple's transfer service moves iCloud Photos to Google Photos (and, since 2025, other destinations). There is no general consumer iCloud API: CloudKit only covers the app's own container, and iCloud Drive is reachable only through a Files/File Provider on-device sync. Tools like icloudpd scrape iCloud Photos through the web API.
- **Microsoft [background]:** Microsoft Graph gives OneDrive (delta queries), Outlook mail, calendar and contacts with user-delegated OAuth, which is the friendliest big-tech API. There is also a privacy dashboard export.
- **DMA [background]:** Article 6(9) requires gatekeepers to provide effective, continuous, real-time portability for end users and authorized third parties free of charge. That is what drove Google's Data Portability API, Meta's DYI/transfer tool and others, and why many of these features are EEA-only.
- **DTI [background]:** the Data Transfer Initiative (successor to the Data Transfer Project) runs trust registries and coordinates photo-transfer partners (Apple, Google, Meta).
- **HPI [background]:** karlicoss's HPI is a Python library of parsers for Takeout, browser databases, Reddit, Twitter and others, with promnesia on top.

### Gaps
- The current (2026) country list for the Google Data Portability API was not verifiable; developers.google.com fetch failed. I could not confirm whether the US was added.
- No verified 2026 detail on Takeout scheduling options or Apple transfer-service destinations.
- The gphotos-sync project's status after 2025 was not checked.

## 3. Social media (Meta, Instagram, TikTok, X, Reddit, YouTube, Bluesky)

### Takeaway
Consumer social APIs keep closing. Instagram's personal-account API ended in Dec 2024. X moved to paid per-request pricing in Feb 2026. Reddit said in Sept 2026 that its public API ends in March 2027. Platform export files ("Download your information") are becoming the only dependable capture path. Bluesky/AT Protocol is the counter-example: a signed, user-exportable repo that can move to a self-hosted PDS.

### Cited Findings
- **Instagram Basic Display API:** ended Dec 4, 2024. Meta said "there will no longer be a set of Instagram APIs for consumer developer apps." Only business and creator accounts keep API access, through Instagram API with Instagram Login or Facebook Login. — [Meta developer blog, Sept 4, 2024](https://developers.facebook.com/blog/post/2024/09/04/update-on-instagram-basic-display-api); [Day One notice](https://dayoneapp.com/?p=77355)
- **Reddit (announced Sept 30, 2026):**
  - Oct 31, 2026: no new public API access requests accepted.
  - Nov 13, 2026: RSS feeds end, with "no replacement" outside mod tools.
  - Jan 12, 2027: access removed for apps that have not registered or engaged with the Developer Platform team.
  - March 2027: remaining public Data API access ends.
  - Reddit cites scraping. Coverage links the move to AI-licensing revenue ($43M "other revenue" in Q2 2026, up 24%).
  - [TechRepublic](https://www.techrepublic.com/article/news-reddit-rss-public-api-shutdown/); [Slashdot/TechCrunch, Sept 30, 2026](https://tech.slashdot.org/story/26/09/30/1841213/reddit-is-killing-rss-feeds-ending-public-api-access); [TechWyse](https://www.techwyse.com/news/social-media/reddit-rss-feeds-ending-public-api-shutdown-2027). These are secondary reports of r/modnews and r/redditdev posts that I did not read directly.
  - Reddit's own data request (GDPR/CCPA archive) still produces a copy of the user's activity. — [takeoutday.org guide](https://takeoutday.org/guides/how-to-export-reddit-data)
- **X API (from Feb 6, 2026):**
  - Pay-per-use credits replace the $200/month entry plan.
  - Reported rates: $0.005 per post read, $0.015 to create a post, $0.20 for a post with a URL. Reads are capped at about 2M posts/month before Enterprise.
  - Remaining Basic subscribers were auto-migrated from June 1, 2026.
  - Enterprise pricing is reported inconsistently, from about $2.5k to $42k+/month.
  - [Open Terms Archive memo](https://opentermsarchive.org/en/memos/x-replaces-its-dollar200-entry-level-api-plan-with-a-pay-per-use-model/); [Gigazine, Feb 9, 2026](https://www.gigazine.net/gsc_news/en/20260209-x-api-pay-per-use); [bundle.social, Jul 2026](https://bundle.social/blog/x-api-pricing-2026-costs-limits). Rates come from secondary and vendor sources.
- **Bluesky/AT Protocol:**
  - A user's repo can be exported as a signed CAR file, and blobs (media) downloaded incrementally with the `goat` CLI.
  - Migrating to another PDS takes a PLC token and a PLC operation that repoints the DID. A September 2026 write-up describes a successful migration to a third-party PDS, with a minor blob-count mismatch.
  - [jola.dev migration post](https://preview-main-joladev-fsumcs-37alh5.preview.jola.dev/posts/migrating-atproto-account-hard-way)
- **Bluesky risks and two-way migration:** Bluesky's 2024 guidance warned that migration involves "possibly destructive identity operations" and was one-way back then. A later summary says migration back to Bluesky's PDS has been possible since Sept 26, 2025 (not verified against Bluesky docs). — [atproto.com self-host federation](https://atproto.com/blog/self-host-federation); [Sacra](https://sacra.com/chat/h/d514840f-2097-472d-b497-186e4b961680)
- **Bluesky backup tools:** independent services such as bsky.storage offer automated account backups and identity recovery. — [feedbagel](https://feedbagel.com/post/bskystorage-an-independent-tool-for-automated-bluesky-account-backups-and-identi)
- **PDS custom domain:** the PDS hostname becomes part of the identity setup, so use a custom domain. — [Sliplane guide](https://sliplane.io/blog/self-hosting-bluesky-pds-the-easy-way)

### Inferences
- **Recommended pattern:** for Meta, X, Reddit and TikTok, a vault should ingest user-requested export archives ("Download your information" JSON/HTML, the X archive zip, Reddit's GDPR CSVs, TikTok's JSON) instead of relying on APIs.
- **Meta [background]:** Accounts Center's "Download your information" can be set up as scheduled or recurring and delivered to Google Drive or Dropbox. Meta's "Transfer your information" sends photos and posts directly to Google Photos, Dropbox, Koofr and others.
- **TikTok [background]:** has in-app data download (JSON or TXT) and, for EEA users, a Data Portability API under the DMA.
- **YouTube [background]:** the Data API v3 can list your playlists and uploads, but watch history is only available through Takeout or the Data Portability API.
- **AT Protocol:** the only major network where the user's data is a portable, cryptographically signed repo by design. A vault can run or mirror a PDS and continuously sync with `com.atproto.sync.getRepo` / `subscribeRepos` [background].

### Gaps
- No 2026 verification of TikTok's export or Data Portability API, YouTube watch-history access, or Meta's DYI scheduling and transfer destinations. Those searches were not run because of the tool budget.
- The X rate figures are not from docs.x.com directly.

## 4. Whole-computer backup (OS tools, cloud, open source, P2P, immutability)

### Takeaway
Open-source deduplicating, encrypted snapshot tools (restic, Kopia, Borg, Duplicacy, Duplicati) are a mature basis for the vault's full-device layer. They pair with S3-compatible storage that supports Object Lock (e.g. Backblaze B2) for ransomware-resistant immutability. I found no 2026-specific releases that change this picture.

### Cited Findings
- **Backblaze B2 Object Lock:** makes objects immutable for a retention period. Governance mode allows authorized overrides; compliance mode blocks shortening or removing retention until it expires. — [Backblaze docs](https://www.backblaze.com/docs/cloud-storage-configure-immutable-storage-for-reseller-and-msp-customers)
- **restic + rclone on B2:** 2026 tutorials describe immutable restic/rclone pipelines on B2 with Object Lock and scoped application keys that cannot delete locked files. — [Tech Insider (2026)](https://tech-insider.org/au/?p=1235)
- **Kopia:** users report that Kopia supports Object Lock on B2, locking each snapshot's objects for a configurable period (2024 community report). — [Lemmy thread](https://deddit.petersanchez.com/g/selfhosted@lemmy.world/p/9QJD7w5Sp11N3Lx8b2-Immutable-backup-for-important-data)
- **Limits of Object Lock:** it protects against logical deletion, not physical media failure, so offline or air-gapped copies are still recommended. — [hometechops guide](https://hometechops.com/guides/immutable-air-gapped-backups)

### Inferences
- **Tool landscape [background, unverified this session]:**
  - **restic** (BSD-2): content-defined chunking, AES-256 encryption, many backends including rclone. Supports compression since v0.14. No built-in GUI (Backrest is a common UI).
  - **Kopia** (Apache-2): GUI plus CLI, compression, encryption, a repository server, and Object Lock retention.
  - **Borg** (BSD): borg 2.0 still in beta/RC for a long time. Needs SSH or BorgBase, not native S3 in 1.x.
  - **Duplicacy:** lock-free dedup, so several machines can share one storage. Commercial GUI.
  - **Duplicati 2.x:** finally stable after years of beta, with a 2.1 release around 2024–25.
  - **Arq 7:** commercial, Mac and Windows, any cloud, encrypted.
  - **Backblaze Personal:** unlimited, $9/month or more, keeps file versions for 30 days by default (1 year or forever as paid options). Its private-key encryption is decrypted on Backblaze servers for restores.
  - **Time Machine:** APFS snapshots, local disk or SMB NAS. Encrypted target disks.
  - **Windows Backup app:** syncs folders, settings and apps to OneDrive. It is not a full image; full images use the deprecated "Backup and Restore (Windows 7)".
- **P2P-capable options [background]:**
  - Syncthing: sync, not backup, but versioning helps.
  - restic, Borg or Kopia to a friend's machine over SSH, SFTP or Tailscale.
  - Duplicacy to an SFTP peer.
  - Historical CrashPlan-to-friend (discontinued 2016).
  - Storj and Sia as decentralized S3 backends.
- **Vault design suggestion:** for a vault app, wrapping restic or Kopia (embed or shell out) on Object-Lock-capable storage, with an append-only server key, is the low-risk choice.

### Gaps
- No verified 2026 release notes for restic, Kopia, Borg 2.0, Duplicati, Arq, Time Machine or Windows Backup.
- No verified 2026 Backblaze Personal pricing.

## 5. Phone backup (iOS/Android limits for third-party apps)

### Takeaway
Phones are the most closed source. Third-party apps cannot read the OS backup or other apps' data on either platform. A vault app can only capture what the user grants: photos, contacts, calendar, files, health, plus share-sheet items. Full-device backups stay with iCloud or Google One, or need a desktop-tethered iTunes/Finder backup that the desktop agent then ingests.

### Cited Findings
- I found no sources in this session's searches on 2025–2026 iOS or Android backup API changes. The tool budget ran out before this section.

### Inferences
- **iOS [background, unverified this session]:**
  - A sandboxed app can read PhotoKit (full or limited library), Contacts, EventKit, HealthKit (per type) and files picked through UIDocumentPicker. It can run background uploads via BGProcessingTask, which is time-limited and opportunistic.
  - It cannot read iMessage/SMS, call history, other apps' data or the iCloud backup.
  - Local encrypted Finder/iTunes or libimobiledevice (`idevicebackup2`) backups on a desktop are the only full-copy path a vault could ingest. Their Manifest.db is SQLite, and iMessage chat.db is extractable from them.
- **Android [background]:**
  - Auto Backup goes to Google Drive, with a 25 MB per-app limit for app data. Android 12+ blocks `adb backup` for most apps.
  - Third-party apps can read MediaStore photos (with the granular photo picker since Android 14), contacts, calendar and call log/SMS. SMS needs default-SMS-app status for Play policy.
  - Health Connect has a backup/export feature.
  - Seedvault (open-source backup in GrapheneOS/CalyxOS/LineageOS) is the only full-device, user-controlled option, and only on custom ROMs.
  - Syncthing-fork, Immich, Ente and Nextcloud apps are common photo auto-upload paths. Immich self-hosted is a popular Google Photos replacement.

### Gaps
- All phone-backup claims above are unverified this session and need checking. This includes any 2025–2026 changes: iOS 26 backup and transfer features, Android 16 backup changes, and the EU DMA-mandated iOS data export to non-Apple devices.
