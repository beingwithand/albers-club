# Continuous capture of email and messaging history into user-controlled storage (as of Oct 2026)

Method note: about 20 searches and fetches. Direct fetches to google.com, signal.org and knowledge.workspace.google.com failed (DNS errors in the sandbox), so several facts rely on search-engine summaries of official pages, or on secondary sources. Those are flagged. Where a source was a standards document (an RFC) that I cite from background knowledge and did not fetch in this session, it is marked "(not fetched)".

## 1. Email: protocols, auth hurdles per provider, tools, formats, incremental sync

### Takeaway
Password-based IMAP is effectively dead for the two biggest providers. Google cut legacy-password IMAP, CalDAV and CardDAV on 14 Mar 2025, though app passwords survive for 2SV accounts. Microsoft consumer Outlook.com needs OAuth2 (XOAUTH2), and app passwords are not a workaround. Exchange Online SMTP AUTH Basic is now scheduled to be off by default at the end of Dec 2026. A self-hosted capture tool that each user runs with their own OAuth client avoids Google's CASA assessment. A hosted SaaS that pulls Gmail through restricted scopes on its servers triggers CASA and an annual reassessment. Korean providers (Daum/Kakao since 2 Jan 2025, Naver since about Jun 2025) require 2-step verification plus an app password for IMAP.

### Cited Findings
**Google / Gmail**
- Per Google's Workspace admin page "Transition from less secure apps to OAuth" (seen via search summary, because a direct fetch failed): from summer 2024, new LSA connection attempts were blocked and the admin/user IMAP toggles were removed. On 14 Mar 2025, LSA access was turned off for all Google accounts, so CalDAV, CardDAV, IMAP, SMTP and POP stopped working with legacy passwords. App passwords are named as the remaining exception. — [Google Workspace Admin Help](https://knowledge.workspace.google.com/admin/sync/transition-from-less-secure-apps-to-oauth)
- A third-party blog claims a different cutoff ("September 30th"). It conflicts with Google's official March 2025 date, and the official date should be preferred. — [Mailbird blog](https://www.getmailbird.com/gmail-oauth-authentication-changes-user-guide/)
- No 2026-specific Google change to app passwords or IMAP turned up in search. — (search gap, same query as above)
- Gmail restricted scopes such as `gmail.readonly` and `gmail.modify` trigger a CASA security assessment when the data is accessed, stored or transmitted via a server. Sensitive-only scopes like `gmail.send` do not trigger CASA Tier 2. Reassessment is required at least every 12 months after the assessor's Letter of Assessment. — [Nango docs: Google security review](https://docs.nango.dev/integrations/google-security-review); [Nylas scopes reference](https://developer.nylas.com/docs/cookbook/use-cases/build/google-oauth-scopes/)
- CASA cost estimates conflict. Vendor pages cite US$15k–75k for the legacy track, roughly US$540–1k/yr via self-serve labs, or "a few hundred to a few thousand dollars". Budget 4–8 weeks. These are all from vendors selling alternatives, and I found no official Google pricing. — [Unipile 2026](https://www.unipile.com/integrating-google-oauth-2-0-user-authentication-into-your-app/); [Truto](https://www.truto.one/google/); [DeepStrike CASA 2025](https://deepstrike.io/blog/google-casa-security-assessment-2025)
- IMAP with XOAUTH2 using the scope `https://mail.google.com/` is itself a restricted scope. Using IMAP instead of the Gmail API therefore does not avoid verification for a multi-user hosted app. — (inference from Nylas scopes reference above; verify)

**Microsoft**
- Exchange Online SMTP AUTH (Client Submission) Basic Auth: the original plan was to reject from 1 Mar 2026 with full enforcement by 30 Apr 2026. The plan was revised on 27 Jan 2026 (MC786329): Basic Auth is disabled by default for existing tenants at the end of Dec 2026, admins can re-enable it, new tenants won't have it, and the final removal date is to be announced in H2 2027. The failure error is `550 5.7.30 Basic authentication is not supported for Client Submission`. — [itelio mirror of MC786329](https://www.itelio.com/en/microsoft-message-center/MC786329); [ChangePilot MC786329](https://portal.changepilot.cloud/MC786329); [CaptainDNS](https://www.captaindns.com/en/blog/microsoft-exchange-basic-auth-smtp-end); older and superseded timeline at [o365reports](https://o365reports.com/deprecation-of-smtp-authentication-client-submission-in-exchange-online/)
- Outlook.com (consumer): Microsoft's Feb 2024 support article says Basic auth will be retired and that classic Outlook using POP/IMAP to Outlook.com doesn't support OAuth. — [Microsoft Support](https://support.microsoft.com/office/outlook-and-other-apps-are-unable-to-connect-to-outlook-com-f4202ebf-89c6-4a8a-bec3-3d60cf7deaef)
- Basic auth for IMAP is deprecated in Exchange Online and Outlook.com, and "App passwords are not a workaround". — [n8n docs](https://docs.n8n.io/integrations/builtin/credentials/imap/outlook/)
- BlueMail (a secondary source) says basic auth for personal Outlook.com was switched off on 16 Sep 2024. Microsoft Q&A says Basic is disabled for IMAP, POP and SMTP across enterprise and consumer services. — [BlueMail](https://bluemail.me/app-password/outlook/); [Microsoft Q&A](https://learn.microsoft.com/en-us/answers/questions/5649919/cannot-sign-in-programmatically-with-app-password)
- Consumer OAuth endpoints: IMAP `outlook.office365.com:993` SSL, SMTP `smtp-mail.outlook.com:587` STARTTLS with OAuth2. — [Prospeo 2026 guide](https://prospeo.io/s/smtp-settings-outlook)

**Korean providers**
- Daum/Kakao Mail: an IMAP/POP3 security change effective Thu 2 Jan 2025 requires an app password, created under 2-Step Verification in Kakao account security and different from the account password. It applies to new and existing users. — [Kakao notice 79](https://mail-notice.kakao.com/mboard/en/notice/79); [Kakao CS](https://cs.kakao.com/helps_html/1073209281?locale=en)
- Daum servers: `imap.daum.net:993` SSL and `smtp.daum.net:465` SSL. — [SMTPedia Daum (verified Jul 2026)](https://smtpedia.com/daum-net-email-settings-pop3-imap-smtp/)
- Naver: third-party guides say IMAP/POP3/SMTP require 2-step verification plus an application password from about 24 Jun 2025. 2SV needs the Naver app on a phone registered in the user's own name, which may block users abroad. IMAP must also be enabled in the mail environment settings. Servers are `imap.naver.com:993` and `smtp.naver.com:587/465`. I did not confirm this against Naver's official help. — [SMTPedia Naver](https://smtpedia.com/naver-com-email-settings-pop3-imap-smtp/); [emailchaser](https://www.emailchaser.com/smtp-settings/naver); [univik](https://univik.com/email-settings/naver.html)

**Tools**
- Bichon: a Rust, self-hosted IMAP archiver. It is archive-only and never sends mail. It does UID-based incremental fetch on a schedule and supports password and OAuth2 with refresh for Gmail and Microsoft. Credentials are encrypted at rest with AES-256-GCM. It has Tantivy full-text search, a web UI and a REST API, multi-user RBAC, compressed storage with dedup, and CLI import of EML, MBOX and PST. It needs no external DB, and Docker and Unraid packages exist. It has about 1.4k GitHub stars. These details come largely from marketplace and review listings. — [Hostinger listing](https://www.hostinger.com/applications/bichon); [selfhostyourself](https://selfhostyourself.com/services/bichon); [Unraid CA](https://ca.unraid.net/apps/bichon-0rn31st1tuchp5)

**Protocol standards (not fetched; standard references)**
- CONDSTORE/QRESYNC (RFC 7162) provides MODSEQ-based incremental flag sync and VANISHED expunge reporting. — [RFC 7162](https://www.rfc-editor.org/rfc/rfc7162) (not fetched)
- JMAP core and mail (RFC 8620/8621) offer `/changes` state strings for delta sync. Fastmail is the main consumer JMAP provider. — [RFC 8621](https://www.rfc-editor.org/rfc/rfc8621) (not fetched)
- Gmail API partial sync uses `history.list` from a stored `historyId`. An out-of-range historyId returns HTTP 404, which requires a full resync, and Google documents history as typically available for at least a week. Push notifications use `users.watch` with Cloud Pub/Sub, and the watch must be renewed at least every 7 days. — [Gmail API sync guide](https://developers.google.com/workspace/gmail/api/guides/sync) (fetch failed; from background knowledge, verify)

### Inferences
- **Architecture choice for Gmail.** If capture runs on the user's own machine or server with a user-created Google Cloud OAuth client in "testing" or personal use, CASA is avoided. Note that testing-mode refresh tokens expire after 7 days unless the app is published, which is a known gotcha (verify). Alternatively, use an app password over IMAP for users with 2SV. A hosted multi-tenant service needs CASA plus annual reassessment.
- **Gmail over IMAP.** Labels appear as folders, so the same message shows up in several folders. Use `X-GM-MSGID`/`X-GM-LABELS` (Gmail IMAP extensions) or the Gmail API to dedupe, and archive "[Gmail]/All Mail" only. Background knowledge; verify.
- **Storage formats.** Maildir (one file per message, safe for concurrent sync, works with notmuch/mu/Xapian indexing) is the safest canonical store. mbox is fragile (From_-line quoting, single-file corruption) but is the format of Google Takeout. EML equals one RFC 5322 file. A good pattern is raw RFC 822 bytes as content-addressed blobs (SHA-256 of the raw message) plus a SQLite metadata/FTS5 index. Dedupe attachments by hashing the decoded MIME parts. These are design inferences.
- **Tools landscape (from background knowledge, not re-verified this session).** mbsync/isync supports XOAUTH2 via a SASL plugin and `PassCmd`. OfflineIMAP is in maintenance, with offlineimap3 as the Python 3 fork. imapsync is for server-to-server migration. GYB (Got Your Back) uses the Gmail API to back up to local EML plus SQLite. Mail-Archiver is a .NET/Postgres web archiver. MailStore Home is a free Windows tool. Thunderbird ImportExportTools NG exports to EML, mbox and HTML.
- **Yahoo and iCloud** (background knowledge, not verified this session). Both still accept app-specific passwords over IMAP. iCloud requires 2FA and an app-specific password, with IMAP at `imap.mail.me.com:993`. Yahoo uses "Generate app password" with IMAP at `imap.mail.yahoo.com`.

### Gaps
- I could not fetch Google's or Microsoft's primary pages directly (DNS failures). Dates come from search summaries of official pages and from mirrors of the Microsoft message center.
- I found no authoritative 2026 statement on whether Google plans to restrict app passwords further.
- I did not verify Yahoo or iCloud app-password status in 2026.
- I did not verify the exact Naver 2SV/app-password effective date from Naver itself.
- I found no official CASA pricing.
- I did not verify the current READMEs for mbsync, GYB, Mail-Archiver or MailStore this session.

## 2. Messaging capture per platform

### Takeaway
Capture options split into three tiers:
1. **Local databases you can read.** iMessage `chat.db` on a Mac, Signal Desktop's SQLCipher DB, Telegram via the official API or Desktop export.
2. **Official but manual or partial exports.** WhatsApp "Export chat", KakaoTalk text export, Messenger secure-storage download, Slack export (free-plan limits), Instagram and Facebook "Export your information".
3. **Reverse-engineered live clients.** whatsmeow/mautrix bridges, DiscordChatExporter with a user token, Beeper/Matrix bridges. These carry ban/ToS risk.

Only Telegram (MTProto/TDLib with the user's own api_id) and iMessage-on-Mac (a SQLite file) allow robust, ToS-tolerable continuous capture.

### Cited Findings
**iMessage**
- imessage-exporter is a Rust library plus a read-only binary that exports TXT or HTML and runs diagnostics. It runs on macOS, Linux and Windows. It reads `~/Library/Messages/chat.db` by default. For iOS, point `-p` at the root of an *unencrypted* backup directory. The platform is auto-detected since v1.5, and `-a iOS` was used in older versions. It covers iMessage, RCS, SMS and MMS, and preserves image, video and audio attachments. — [README (raw)](https://raw.githubusercontent.com/ReagentX/imessage-exporter/develop/README.md); [crates docs 1.4.0](https://crates-io.ganymede-static.progval.net/crates/imessage-exporter/1.4.0)
- The README currently claims support "as of macOS … 27.0 (26A428) and iOS 27.0 (24A437)". A search summary separately mentioned iOS 26.5.1 as tested. Version strings conflict across fetches and are worth re-checking. — [README](https://raw.githubusercontent.com/ReagentX/imessage-exporter/develop/README.md)

**WhatsApp**
- whatsmeow is the Go multi-device library behind the mautrix-whatsapp Matrix bridge (MPL-2.0, maintained by Tulir Asokan). All such libraries are unofficial and reverse-engineered, and using them on a personal number can violate the ToS and risk a ban. "Architecture does not grant ban immunity; behavior does." The only sanctioned API is the WhatsApp Business Cloud API, which does not apply to personal history. — [checkleaked 2026 library comparison](https://whatsapp.checkleaked.cc/blog/best-open-source-whatsapp-libraries) (secondary source)

**Telegram**
- Telegram Desktop has an official export at Settings > Advanced > Export Telegram data. It writes JSON (`result.json` plus a chats folder) or HTML (`export_results.html`, or `messages.html` per chat), and a per-chat "Export chat history" option exists. The schema is documented by Telegram. — [core.telegram.org/import-export](https://core.telegram.org/import-export); [Telegram blog](https://telegram.org/blog/export-and-more/kk?setln=en)
- Lite clients such as the native macOS app lack export, so Telegram Desktop is required. — [LangChain Telegram loader docs](https://reference.langchain.com/python/langchain-community/chat_loaders/telegram)

**Signal**
- Signal Desktop's SQLCipher DB key was moved from plaintext `config.json` into Electron safeStorage in July 2024. On macOS it is in the Keychain with per-app restriction. On Windows and Linux, any process running as the same user can still decrypt it. — [SandboxAQ: Protecting Signal Keys on Desktop](https://cryptographycaffe.sandboxaq.com/posts/protecting-signal-desktop-keys/); [mjtsai 2024](https://mjtsai.com/blog/2024/07/08/signal-for-macs-encrypted-database)
- On Linux, safeStorage uses the freedesktop Secrets API. Switching between GNOME and KDE keyrings breaks DB decryption. The workaround is to extract the key with signalbackup-tools and edit `config.json`. — [yingtongli.me 2025](https://www.yingtongli.me/blog/2025/08/13/signal-secrets.html)
- Signal Secure Backups launched in Sep 2025, Android first. They are E2EE with a 64-character recovery key generated on device and never shared with Signal. — [AlternativeTo](https://alternativeto.net/news/2025/9/signal-introduces-secure-backups-with-encrypted-message-history-across-devices/); [BleepingComputer](https://bleepingcomputer.com/news/security/signal-adds-secure-cloud-backups-to-save-and-restore-chats)
- Later rollout: hosted Secure Backups and on-device backups can be created and restored across Android, iOS, Linux, macOS and Windows. Hosted backups also use a TEE-held second key. On-device backups can be stored on any drive, so they cannot use the TEE. This comes from press reports, since I could not fetch signal.org. — [Help Net Security](https://www.helpnetsecurity.com/?p=386262); [mjtsai Nov 2025](https://mjtsai.com/blog/2025/11/28/secure-signal-backups/)

**KakaoTalk**
- The official chat backup is text only. It excludes photos, videos and messages over 1,000 characters, must be restored within 14 days, and needs the same Kakao Account. It is not a durable archive. — [Kakao CS: back up and restore](https://cs.kakao.com/helps_html/1073182729?locale=en)
- A per-chat export (text, or "save all messages") is available via the chat menu, and attachments need separate handling. Unofficial extraction tools violate Kakao's ToS. — [braindetox guide](https://braindetox.kr/en/posts/kakaotalk_backup_setup_guide.html); [Tenorshare (vendor)](https://4ddig.tenorshare.com/kr/sns-tips/export-and-recover-kakaotalk-conversation-history.html)
- Kakao's marketing for "Talk Cloud" covers paid storage for chats and media. Its relation to the current "Talk Drive" product is unconfirmed. — [Kakao Corp](https://www.kakaocorp.com/page/detail/11658)

**Discord**
- DiscordChatExporter exports HTML, TXT, CSV and JSON and accepts user or bot tokens. Its README warns that "automating user accounts is against Discord TOS and may result in you getting banned" and recommends bot tokens where possible. The project status is "maintenance". — [DiscordChatExporter README](https://raw.githubusercontent.com/Tyrrrz/DiscordChatExporter/master/Readme.md)

**Slack**
- Free plan: only 90 days are visible in the app. Since Aug 2024, messages and files older than one year are deleted on a rolling basis. Exports on free plans include more than the 90 visible days but cover public channels only. Private channels and DMs require Business+ plus Slack approval, and month-long upgrade attempts to extract data have reportedly been denied. — [Zulip blog Jul 2025](https://blog.zulip.com/2025/07/24/who-owns-your-slack-history/); [CNCF Jun 2025](https://www.cncf.io/blog/2025/06/16/cncf-slack-workspace-changes-coming-on-friday-june-20/); [PhoneArena](https://www.phonearena.com/news/slack-removes-free-lifetime-message-history_id159953)
- Conflict: ViewExport says older messages are "hidden, not deleted". Official-notice reporting supports deletion. — [ViewExport](https://viewexport.com/post/slack-free-plan-limitations)

**Facebook Messenger and Instagram**
- E2EE chat history is kept in "secure storage", accessed via a 6-digit PIN or a key in Google Drive or iCloud. Without it, history can be lost with the device. — [Meta newsroom, Mar 2024](https://about.fb.com/news/2024/03/end-to-end-encryption-on-messenger)
- The standard Accounts Center "Export your information" does not include E2EE chats. A separate "Download secure storage data" path exists on Messenger web (Privacy & safety > End-to-end encrypted chats > Message storage), requires the PIN, and yields JSON in `messages.zip`. These menu steps are from third-party guides. — [macmyths](https://macmyths.com/how-to-export-facebook-messenger-messages/); [Decipher Tools](https://deciphertools.com/support/knowledge-base/missing-newer-facebook-messages/)

**Beeper and Matrix bridges**
- Automattic acquired Beeper in April 2024, reportedly for about US$125M, following its acquisition of Texts.com (Oct 2023). Migicovsky became Automattic's Head of Messaging, and Texts is being folded into Beeper. — [TechCrunch](https://techcrunch.com/?p=2688488); [AlternativeTo](https://alternativeto.net/news/2024/4/beeper-is-now-open-to-all-after-removing-its-waitlist-and-has-been-acquired-by-automattic); [mjtsai](https://mjtsai.com/blog/2024/04/11/automattic-acquires-beeper/)
- Official bridges run on-device or in Beeper Cloud. Users can self-host them via Beeper Bridge Manager (`bbctl`), so re-encryption happens on hardware the user controls. Self-hosted bridged accounts are free and don't count toward limits, but they get reduced support, and `bbctl` runs in the foreground (use tmux or screen). Community bridges are self-host-only. — [Beeper self-hosting docs](https://developers.beeper.com/bridges/self-hosting/); [bridge-manager](https://pkg.go.dev/github.com/beeper/bridge-manager); [Beeper open source](https://developers.beeper.com/open-source)
- iMessage in Beeper (2026) works on Mac only, and a Sep 2026 release fixed macOS iMessage issues by requiring Full Disk Access, which means it reads `chat.db` locally. — [Releasebot Beeper notes](https://releasebot.io/updates/beeper); [Yahoo Finance](https://finance.yahoo.com/news/beeper-one-messaging-app-relaunches-220000245.html)

### Inferences
- **Unified capture layer.** Self-hosted mautrix bridges (WhatsApp, Signal, Telegram, Meta, Discord, Slack, LINE, etc.) writing into a self-hosted Matrix homeserver is the most practical "single pipe". Matrix becomes the canonical event log. The risks are ToS and ban exposure on WhatsApp, Meta and Discord, plus limited history backfill: WhatsApp multi-device history sync sends only a recent window at link time. The backfill limit is from background knowledge; verify.
- **iMessage.** Continuous capture needs an always-on Mac with Full Disk Access reading `chat.db`, or periodic unencrypted iOS backups (Finder or libimobiledevice) parsed with imessage-exporter. Encrypted backups must be decrypted first with tools like iphone_backup_decrypt. Background knowledge.
- **Signal.** Continuous capture works by reading the Desktop SQLCipher DB with the key from safeStorage or the Keychain (signal-export / sigexport does this). The new on-device backup files are a periodic full-history source.
- **WhatsApp.** The ToS-safe options are manual "Export chat" (a .txt plus media zip, which has historically been capped per chat) or decrypting the local Android crypt15 backup with the 64-digit E2E backup key (wa-crypt-tools). Background knowledge; verify.
- **LINE, WeChat and Instagram DMs.** Only official data downloads and per-chat text exports are realistic. WeChat has no sanctioned export. Unverified this session.

### Gaps
- I could not fetch signal.org for the official Secure Backups pricing and retention (for example the free tier's text history and 45-day media).
- I found no reliable 2026 source on WhatsApp ban rates for whatsmeow, or on the history-sync window.
- Not researched: LINE, WeChat, Instagram DM export specifics, and TDLib userbot ToS.
- Beeper's 2026 product changes (on-device model relaunch, Matrix-room joining) were reported but not deeply verified.

## 3. Calendar/contacts and notes

### Takeaway
CalDAV and CardDAV remain the standard pull protocols. For Google they now require OAuth or an app password, since legacy passwords were cut on 14 Mar 2025.

### Cited Findings
- Google's 14 Mar 2025 LSA shutdown explicitly covered CalDAV and CardDAV with legacy passwords. — [Google Workspace Admin Help](https://knowledge.workspace.google.com/admin/sync/transition-from-less-secure-apps-to-oauth)

### Inferences
- vdirsyncer (CalDAV/CardDAV to local .ics/.vcf directories) is the standard sync tool. iCloud CalDAV/CardDAV uses app-specific passwords. Microsoft 365/Outlook.com has no CardDAV/CalDAV, so it needs the Graph API. Notes (Apple Notes, Google Keep) have no open sync protocol, so use Takeout or an export. All of this is background knowledge.

### Gaps
- Not verified this session: vdirsyncer's 2026 status, Graph-only access for Outlook calendars, and Apple Notes export tooling.

## 4. Phone-side capture (Android SMS/call log, notification listener, iOS)

### Takeaway
On Google Play, SMS and Call Log permissions are restricted to the default SMS, Phone or Assistant handler, with narrow exceptions granted by declaration form. A sideloaded or F-Droid app avoids that policy. NotificationListenerService is a viable but lossy capture channel. On iOS there is no third-party access to messages, so capture goes through a Mac's `chat.db` or a device backup.

### Cited Findings
- Apps must be the registered default SMS, Phone or Assistant handler before requesting SMS or Call Log permission groups, and must stop using them when no longer default. Play may grant temporary exceptions for listed core functions via the Permissions Declaration Form. The data must not be used for ads. — [Play Console Help 9047303](https://support.google.com/googleplay/android-developer/answer/9047303?authuser=6); [Play Console Help 16558241](https://support.google.com/googleplay/android-developer/answer/16558241?hl=en)
- "Backup and restore" was historically listed as an eligible exception (2018 rollout). It is unconfirmed in the current policy text. — [MobileSyrup 2018](https://mobilesyrup.com/2018/11/19/google-tasker-call-log-sms-permissions-restriction/)
- NotificationListenerService requires `BIND_NOTIFICATION_LISTENER_SERVICE` and the `SERVICE_INTERFACE` intent filter. It is unavailable on low-RAM devices running Android Q or below and is ignored in work profiles. Access is granted via a special settings screen. — [Android developer reference](https://developer.android.com/reference/android/service/notification/NotificationListenerService); [ptkd.com](https://ptkd.com/journal/android-notification-listener-service-security)

### Inferences
- Notification capture gets only what the notification shows. It truncates long messages, collapses grouped chats, misses messages read in-app before notifying, and misses media and own outgoing messages. Treat it as a real-time supplement, not a system of record.
- Since Android 13 or so, sideloaded apps face "restricted settings" gating for notification-listener and accessibility access, which needs a manual allow. Background knowledge; verify.

### Gaps
- I did not retrieve the current Play policy text on notification-listener use, or the 2026 status of the backup exception.
- iOS limits (no SMS or iMessage API, Shortcuts-only automations) were not verified this session.
