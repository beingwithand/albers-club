# Local Data Harvesting Techniques (defensive survey, as of Oct 2026) — what's reusable with consent for a personal "capture everything I do" app

Scope note: these notes describe mechanisms at an architectural level only. They are meant to help a consent-based tool record the user's OWN data on the user's OWN devices. Items marked [older] are from before 2024. Items marked [uncited/general knowledge] are background I could not source in this session; treat them as unverified.

## 1. Browser extensions as data harvesters (Urban VPN, Similarweb, Honey, sleeper/acquired extensions, Cyberhaven; MV3 impact)

### Takeaway
Extensions remain the richest local harvesting surface on desktop. The 2025–26 cases show that "free VPN/ad-blocker/privacy" extensions with all-sites host access can inject page scripts that override fetch()/XMLHttpRequest and capture full AI-chat prompts and responses. Manifest V3 did not stop this, because MV3 restricts *blocking* network interception, not content-script/page-script access to the DOM. The same mechanism (content script plus page-context hooks on sites the user chooses) is the single most valuable *legitimate* capture technique for a personal tool, as long as it is opt-in per site, visible, and local-first.

### Cited Findings
- **Urban VPN Proxy (Koi Security, Dec 2025):** Urban VPN Proxy had 6M+ users and a Google "Featured" badge. It and its siblings 1ClickVPN Proxy, Urban Browser Guard and Urban Ad Blocker (Chrome + Edge, ~8M users total) shipped per-platform "executor" scripts (e.g., chatgpt.js, claude.js). These override fetch() and XMLHttpRequest to read prompts and responses, conversation IDs and timestamps, model identifiers, and session data. Coverage: ChatGPT, Claude, Gemini, Copilot, Perplexity, DeepSeek, Grok and Meta AI. — [CSO Online](https://www.csoonline.com/article/4106949/featured-urban-vpn-caught-stealing-private-ai-chats.html); [Infosecurity Magazine](https://infosecurity-magazine.com/news/urban-vpn-proxy-harvesting-ai-chats); [The Register](https://www.theregister.com/2025/12/16/chrome_edge_privacy_extensions_quietly/)
- Urban VPN collection ran whether or not the VPN was on. It was enabled by a hard-coded flag with no opt-out (only uninstalling stopped it) and was introduced in v5.5.0 (~July 2025). Data went to analytics.urban-vpn.com and stats.urban-vpn.com. The operator, Urban Cyber Security Inc., is affiliated with BiScience, a firm that monetizes browsing data. — [CyberInsider](https://cyberinsider.com/free-vpn-chrome-extensions-with-8-million-downloads-log-ai-chats/); [BankInfoSecurity](https://www.bankinfosecurity.com/urban-vpn-proxy-spies-on-ai-chatbot-conversations-a-30368)
- **Similarweb panel extension:** installing it enrolls the user in the "Similarweb Panel". The listing discloses capture of "anonymized clickstream data… specifically the domains you browse" and permission to "access your data on all websites… tabs and browsing activity". (The Opera listing was last updated in 2019 [older].) — [Firefox Add-ons](https://addons.mozilla.org/fr/firefox/addon/10548); [Opera Add-ons](https://addons.opera.com/en/extensions/details/similarweb)
- **Honey (PayPal), Dec 2024 MegaLag investigation:** the allegation is that at checkout the extension replaced creators' affiliate cookies or tags with PayPal's own, even when it found no working coupon. Honey reportedly lost ~3M users and class actions followed. These are allegations, not findings. — [Android Authority](https://www.androidauthority.com/honey-extension-scamming-users-3510942); [MobileSyrup](https://mobilesyrup.com/2025/01/03/honey-loses-3-million-users-scam-allegations/); [ClassLawGroup](https://classlawgroup.com/honey-browser-extension-scam-lawsuit)
- **Cyberhaven compromise (Dec 2024):** attackers phished developers with fake "Chrome Web Store policy violation" emails and an OAuth/login lure, then pushed a malicious update. Cyberhaven v24.10.4 was live for less than 24 hours (Dec 25–26, 2024). The payload targeted cookies and auth tokens for social media and AI platforms, Facebook in particular. The campaign hit ~35–36 extensions and ~2.6M users (Internxt VPN, VPNCity, Uvoice, ParrotTalks, among others) and appears to have begun around Dec 5. — [GovInfoSecurity](https://www.govinfosecurity.com/36-chrome-extensions-compromised-in-supply-chain-attack-a-27207); [SOCRadar](https://socradar.io/blog/phishing-attack-cyberhaven-chrome-extension/); [Dark Reading](https://www.darkreading.com/application-security/chrome-extension-compromises-highlight-software-supply-challenges)
- **Sleeper and acquired extensions:**
  - Koi's "DarkSpectre"/ShadyPanda research covers ~8.8M users over 7+ years, including 85 dormant "sleepers" built to gather users before being weaponized. Malwarebytes reports 5 extensions that were clean for years and turned malicious in mid-2024 (~4.3M users). — [Malwarebytes](https://www.malwarebytes.com/?p=342868); [MalwareTips summary](https://malwaretips.com/threads/darkspectre-browser-extension-campaigns-exposed-after-impacting-8-8-million-users-worldwide.139177/post-1164828)
  - Koi, July 2025: 11 Chrome Web Store extensions (~1.7M downloads) that were initially safe and later updated with malicious code. — [Tribune](https://tribune.com.pk/story/2554951/malicious-google-chrome-extensions-with-over-17m-downloads-discovered)
  - QuickLens was sold via the ExtensionHub marketplace. The new owner's v5.8 update (Feb 17, 2026) stripped CSP and X-Frame-Options headers and polled a C2 server every 5 minutes. — [BleepingComputer](https://www.bleepingcomputer.com/news/security/quicklens-chrome-extension-steals-crypto-shows-clickfix-attack/amp/); [Hackmag](https://hackmag.com/news/quicklens-shotbird)
  - "Save image as Type" (1M+ users) became spyware and an affiliate hijacker after its sale. — [PCWorld, Mar 2026](https://www.pcworld.com/article/3092299/my-most-useful-chrome-extension-was-stealing-my-data-for-years.html)
  - Ownership transfer keeps the existing trust relationship, so updates install silently. — [Malwarebytes](https://www.malwarebytes.com/?p=342868)
- **MV3:** blocking webRequest was replaced by declarativeNetRequest (declared rules applied by the browser) and kept only for enterprise. Google's rationale was that extensions could quietly see all browsing traffic. Under MV3, extensions can still observe connections but cannot modify the content of the data in transit. — [Google Security Blog 2019](https://security.googleblog.com/2019/06/improving-security-and-privacy-for.html?hl=fr_CA) [older]; [MediaPost](https://www.mediapost.com/publications/article/337480/)
- A 2025 study found MV3 migration affects extension categories unevenly: some lose functionality or decline to update. — [SciTePress 2025](https://www.scitepress.org/Papers/2025/136690/136690.pdf)

### Inferences
- **MV3 did not touch the harvesting channel.** Urban VPN (July–Dec 2025, an MV3-era extension) shows that content scripts or main-world injected scripts with `<all_urls>` host permissions can still capture everything a page renders or fetches. MV3 reduced *network-layer* interception, not *DOM/JS-layer* access.
- **Reusable for a personal tool (with consent):**
  - A content-script extension that records the user's own AI chats, page visits, dwell time, selected text and form submissions on sites the user opts into.
  - Use optional host permissions (requested per site at runtime) rather than `<all_urls>` at install.
  - Show visible capture indicators (badge or icon state) and a per-site pause.
  - Write to local storage or a local companion app (native messaging) rather than a remote server.
  - Use the history, tabs and webNavigation APIs for a clickstream equivalent to Similarweb's panel.
- **Off-limits:**
  - hidden or hard-coded collection flags
  - collecting regardless of the advertised feature
  - affiliate or cookie replacement
  - remote-configurable code that turns capture on later
  - selling or transferring the extension (the trust-inheritance problem). Plan governance such as a non-transfer pledge, reproducible builds and open source.
- **Supply-chain lesson from Cyberhaven:** the developer's own Web Store account is an attack surface. Use phishing-resistant MFA (hardware keys), and if the tool holds a full activity log, design it so a malicious update can't silently exfiltrate the store, for example by keeping it encrypted to a key held by a separate native app.

### Gaps
- I did not read Koi's primary Urban VPN post (koi.ai). Details come from press summaries, and no Urban VPN or BiScience response was found.
- I found no 2025–26 source on the "Sky" extension acquisition named in the brief.
- I found no current (2025–26) independent audit of the Similarweb panel's collection scope.
- There is no primary source in these notes confirming that content scripts are unaffected by MV3. That claim is an inference supported by the Urban VPN case.

## 2. In-app SDKs & telemetry (Meta/Yandex localhost, location SDKs/Gravy, clipboard, keyboards, accessibility, fingerprinting)

### Takeaway
SDKs embedded in apps harvest inside another app's permission envelope: location from apps that have location permission, clipboard reads, and identifiers. Meta and Yandex went further, bridging web and app identities through localhost sockets on Android. The Gravy Analytics breach (Jan 2025) showed what bid-stream and SDK location data looks like in practice: tens of millions of timestamped coordinates tied to device IDs, sourced from mainstream apps. OS countermeasures (iOS paste banner, Chrome and Firefox localhost blocks, Android 14+ accessibility limits on sideloaded apps) are now the main limiting factor.

### Cited Findings
- **Localhost / "Local Mess" (disclosed June 3, 2025; researchers from IMDEA Networks, Radboud and KU Leuven):**
  - Facebook, Instagram and Yandex Android apps listened on fixed localhost ports. The Meta Pixel and Yandex Metrica scripts running in the mobile browser sent data to those ports, which let the apps tie the web _fbp cookie or browsing to a logged-in app identity and bypass cookie clearing and incognito mode. — [IMDEA Networks](https://networks.imdea.org/research-co-led-by-imdea-networks-discovers-a-privacy-abuse-involving-meta-and-yandex-bridging-persistent-identifiers-to-browsing-histories/); [localmess disclosure mirror](https://scriptagc.wasmer.app/https_localmess_github_io); [LWN](https://lwn.net/Articles/1024844)
  - Meta's use dates to ~late 2024, Yandex's to 2017. Meta switched to a WebRTC/TURN variant around May 17, 2025, after Chrome blocked SDP munging, and Meta's Pixel stopped localhost traffic shortly after disclosure. Chrome 137 added countermeasures and Firefox planned port blocking in v139. Yandex said it "does not de-anonymize user data". — [PPC Land](https://ppc.land/meta-halts-covert-android-tracking-following-research-disclosure/); [Yahoo Tech](https://tech.yahoo.com/articles/researchers-catch-meta-apps-abusing-193741210.html)
- **Gravy Analytics / Unacast breach (detected Jan 4, 2025):**
  - Access came via a misappropriated AWS key. The attacker claimed ~10 TB. A 1.4 GB sample held 30M+ location points, including points at the White House, the Kremlin, the Vatican and military bases. — [TechCrunch](https://techcrunch.com/2025/01/13/gravy-analytics-data-broker-breach-trove-of-location-data-threatens-privacy-millions/)
  - Points were attributed to apps such as Candy Crush, Tinder, Spotify, Vinted, and fitness, transit and dating apps. Researchers argued much of it was gathered via ad bid-stream rather than an SDK in each app. Fields included GPS coordinates, timestamps, IP addresses and device IDs. — [Computing](https://www.computing.co.uk/news/2025/security/data-breach-exposes-location-data-popular-apps); [GRC Report](https://www.grcreport.com/post/gravy-analytics-data-breach-exposes-precise-location-data-from-millions-of-users-2)
  - The FTC had already alleged that Gravy and Venntel unfairly sold sensitive location data. — [TechCrunch](https://techcrunch.com/2025/01/13/gravy-analytics-data-broker-breach-trove-of-location-data-threatens-privacy-millions/)
- **FTC location and browsing orders (2024):**
  - X-Mode (Jan 9, 2024) sold non-anonymized location data matchable to advertising IDs, including visits to clinics and places of worship. InMarket settled Jan 18, 2024. — [Proskauer](https://proskauer.com/blog/data-at-issue-ftc-focus-on-browsing-information-and-location-data); [JD Supra](https://www.jdsupra.com/legalnews/data-at-issue-ftc-focus-on-browsing-6187086)
  - Avast/Jumpshot (Feb 2024; $16.5M) sold re-identifiable browsing data, collected by Avast's antivirus and browser extensions, to 100+ third parties, some feeds with persistent device IDs. Avast must delete the data and derived models. — [WilmerHale](https://www.wilmerhale.com/en/insights/blogs/wilmerhale-privacy-and-cybersecurity-law/20240909-ftcs-enforcement-action-against-avast-signals-increased-focus-on-consumer-web-data); [Perkins Coie](https://perkinscoie.com/insights/blog/ftc-obtains-165m-avast-sale-sensitive-data)
- **Clipboard [older, 2020]:** Mysk and Haj Bakry showed iOS apps silently reading the clipboard. iOS 14's paste banner then exposed TikTok reading it every 1–3 keystrokes, plus 50+ other apps (AccuWeather, AliExpress, Google News, Patreon and others). TikTok removed the behavior. Universal Clipboard extends exposure to the user's other Apple devices. — [Sophos](https://www.sophos.com/en-us/blog/ios-14-flags-tiktok-53-other-apps-spying-on-iphone-clipboards); [iMore](https://imore.com/ios-14-reveals-clipboard-snooping-far-worse-we-thought)
- **Accessibility services:** Android stalkerware has used the accessibility service to capture screen content, toasts and notifications from social apps. Android can't simply restrict accessibility because people with disabilities depend on it. Android 14+ added stricter controls for sideloaded apps. — [arXiv 2508.02454](https://arxiv.org/html/2508.02454v1)

### Inferences
- **Reusable for a personal tool:**
  - Location: the tool can log the user's OWN location with its own foreground permission and a visible persistent notification, so it never needs third-party SDK data.
  - Clipboard history: a user-installed clipboard manager is legitimate on desktop. On iOS, explicit paste or paste-permission is required (iOS 16+ added a per-app "Allow Paste" prompt [uncited/general knowledge]).
  - Android: NotificationListenerService is a legitimate, user-granted way to log the user's own incoming notifications. AccessibilityService captures on-screen text but is high-risk: Play policy restricts non-accessibility use [uncited/general knowledge], and it is the stalkerware vector. It should be avoided or at least made very visible.
- **Off-limits:**
  - cross-context identity bridging (localhost or WebRTC side channels)
  - SDKs that collect beyond the host app's purpose
  - fingerprinting to defeat user resets
  - any resale
- **Reverse use:** the Gravy schema (device ID + lat/long + timestamp + app/bundle + IP) is a good template for what a user should request back through data-subject requests, and for what their own location log should capture.

### Gaps
- I found no sources for: Mobilewalla's FTC order (I believe it was Dec 2024, alongside Gravy [uncited]); keyboard-app data-collection cases; Meta SDK / Google SDK telemetry specifics; or recent device-fingerprinting research.
- I could not verify the iOS 16 paste prompt in this session.

## 3. Paid panel / meter apps (Onavo, Facebook Research, Google Screenwise, Nielsen/Kantar/Ipsos, Measure Protocol)

### Takeaway
Paid panels use the same capture primitives as malware: a device-wide VPN, an installed root certificate (MITM), a browser extension, a screen or accessibility meter, and even a household router. The difference is notional consent and payment ($5–$20/month). The 2019 Facebook Research and Google Screenwise scandals turned on recruiting teens, sidestepping App Store review via enterprise certificates, and the gap between "install this certificate" and an understanding that all encrypted traffic is now visible.

### Cited Findings
- **Facebook Research (exposed Jan 2019) [older]:**
  - It recruited people aged 13–35 via Applause, BetaBound and uTest, paying up to $20/month plus referrals.
  - It required installing a root certificate, enabling access to "private messages, chats, emails, web activity, and location" (Will Strafach). It was "essentially all Onavo code".
  - Apple revoked Facebook's enterprise certificates. Facebook shut down Onavo Protect in Feb 2019 and stopped new Research enrollments.
  - Sources: [Gizmodo](https://gizmodo.com/facebook-is-paying-teens-to-install-a-research-app-that-1832182370); [TechCrunch](https://techcrunch.com/2019/02/21/facebook-removes-onavo/amp); [Wikipedia: Onavo](https://wikipedia.com/wiki/Onavo)
- **Google Screenwise Meter [2019, still operating]:**
  - It used a VPN-based app and browser extension, plus a home router for panelists.
  - EFF noted Google didn't require a root certificate, so it couldn't decrypt HTTPS, but could "see anything on your screen" and all app usage.
  - Distributed on iOS through an enterprise certificate, which Google apologized for and pulled. Rewards were gift cards ($5 at install and per quarter in early versions).
  - The current app works only for registered panelists.
  - Sources: [EFF](https://www.eff.org/deeplinks/2019/02/google-screenwise-unwise-trade-all-your-privacy-cash); [9to5Google](https://9to5google.com/guides/screenwise/); [Androidworld](https://androidworld.nl/nieuws/google-screenwise-meter/); [Google support](https://support.google.com/screenwise-meter/answer/9791033)

### Inferences
- **Architecture template for a personal tool:**
  - extension (web)
  - on-device VPN for network metadata
  - usage-stats or screen meter (apps and screen time)
  - optionally a router (household devices)

  Panels prove the full stack is feasible on consumer hardware. For self-capture, a root-CA/MITM is the line most tools should not cross by default (see section 7).
- **Consent lessons:**
  - no minors
  - no store-policy circumvention (enterprise or side-loaded certificates)
  - plain-language disclosure of what each primitive exposes
  - the money and data flow reversed: the user keeps the data

### Gaps
- I found no sources on Nielsen, Kantar, Ipsos or Measure Protocol mobile meters, or on 2025–26 "get paid for your data" apps. Their capture methods (accessibility, VPN, usage-stats) remain unverified here.

## 4. Infostealers — map of "where your data lives on your own device" (RedLine, Lumma, Vidar, AMOS)

### Takeaway
Infostealers are effectively an inventory of the highest-value local data stores. On Windows: Chromium profile SQLite DBs (History, Cookies, Login Data, Web Data/autofill), Firefox profile, Discord tokens, Telegram tdata, wallet extensions and files, VPN configs. On macOS: also Keychain and Apple Notes. Chrome 127's App-Bound Encryption (mid-2024) raised the bar for cookies and passwords, but stealers claimed bypasses within weeks. Lumma's infrastructure was disrupted in May 2025 but resurged by July–Aug 2025, and a 64-bit successor ("Remus") appeared in Feb 2026. For a personal tool, the same map is a list of import sources, read with the user present and using OS-sanctioned decryption only.

### Cited Findings
- **Chrome App-Bound Encryption (ABE):**
  - Introduced in Chrome 127 (mid-2024) to bind cookie and password keys to Chrome's identity, mediated by an elevated service.
  - Lumma shipped a bypass around Sept 2024 (confirmed against Chrome 129).
  - Techniques documented: memory scanning for CookieMonster in chrome.dll, and abuse of the `--remote-debugging-port` feature into 2025.
  - Sources: [BleepingComputer](https://www.bleepingcomputer.com/news/security/infostealer-malware-bypasses-chromes-new-cookie-theft-defenses/); [CyberInsider](https://cyberinsider.com/this-is-how-infostealers-bypass-chromes-latest-cookie-security/); [Red Canary](https://redcanary.com/threat-detection-report/threats/lummac2)
- **Lumma takedown:** coordinated industry and law-enforcement disruption in May 2025 (low activity May–June), renewed distribution July–Aug 2025. The Remus variant (first campaigns Feb 2026) shares Lumma's rare ABE-bypass method. — [Red Canary](https://redcanary.com/threat-detection-report/threats/lummaC2/); [VPNCentral](https://vpncentral.com/remus-infostealer-emerges-as-a-64-bit-lumma-variant-with-new-browser-key-theft-tricks/)
- **AMOS (Atomic macOS Stealer):**
  - Malware-as-a-service tracked since April 2023, nearly 40% of Sophos' macOS protection updates in 2025.
  - Targets: Keychain, browser credentials, cookies and autofill, Apple Notes, crypto wallets, Telegram data and OpenVPN profiles. Data is zipped and exfiltrated over HTTP(S).
  - Persists via a LaunchDaemon and re-prompts for the macOS password until the user gives it.
  - Delivered by fake or cracked installers and "ClickFix" paste-into-Terminal lures, including poisoned ChatGPT/Grok shared chats (Huntress, Dec 2025).
  - Sources: [Sophos](https://www.sophos.com/en-us/blog/why-amos-matters-the-macos-malware-stealing-data-at-scale); [Trend Micro](https://trendmicro.com/en_us/research/25/i/an-mdr-analysis-of-the-amos-stealer-campaign.html); [CraftedSignal brief](https://feed.craftedsignal.io/briefs/2026-05-amos-stealer/)

**Local data-store map** (architectural; the paths are standard and publicly documented, but the store list is general knowledge except where cited above):

| Store | Contents | Legit personal-import route |
|---|---|---|
| Chromium `History` (SQLite) | URLs, visit times, transition types, downloads, search terms | Copy while the browser is closed, or use the extension history API |
| Chromium `Cookies` / `Login Data` / `Web Data` | Sessions, saved passwords, autofill, addresses, cards | Avoid. Use the browser's own password-export function only, with the user present. Do not defeat ABE. |
| Firefox `places.sqlite`, `formhistory.sqlite` | History, bookmarks, form entries | Read copy |
| Safari `History.db` (macOS) | History | Requires Full Disk Access granted by the user |
| macOS Keychain | Credentials | Do not touch |
| Apple Notes `NoteStore.sqlite` | Notes | Prefer export, or a Full Disk Access read with consent |
| Messages `chat.db` (macOS) | iMessage/SMS | Full Disk Access with consent (high value for personal archive) |
| Telegram `tdata`, Discord local storage | Session tokens | Never copy tokens; use the official data exports instead |
| Wallet extension vaults / wallet files | Keys | Never touch |
| VPN configs (OpenVPN) | Credentials | Never touch |

### Inferences
- **Hard line for a personal tool:** read *content and activity* stores (history, messages, notes) with explicit OS-level grants (Full Disk Access, file pickers). Never read *authenticators* (cookies, tokens, passwords, keys), never defeat ABE or Keychain, and never request the account password outside OS prompts. Doing any of these makes the tool functionally indistinguishable from AMOS or Lumma to EDR software and to users.
- **Security consequence:** a "capture everything" archive becomes the single richest target on the device for the next stealer. It must be encrypted at rest with OS-protected keys (DPAPI/ABE-like binding, Keychain, Secure Enclave or TPM) and should not store authenticators at all.

### Gaps
- I found no 2025–26 primary sources for RedLine (Operation Magnus, Oct 2024 [uncited]), Vidar, or Discord-token theft specifics.
- I found no source on whether Google shipped further ABE hardening in 2025–26.

## 5. Platform OS-level collection (Microsoft Recall, Apple Intelligence personal context, Android Private Compute Core, Samsung)

### Takeaway
The OS vendors now ship first-party "capture everything" features: Recall (periodic screenshots plus OCR and a semantic index), Apple Intelligence's on-device semantic index, and Android System Intelligence inside Private Compute Core. Their protection patterns are the reference design for a personal tool: opt-in, hardware-bound keys, isolated compute, authentication on every access, and no network egress except through narrow audited channels. Recall's 2024 backlash (originally default-on, with weakly protected storage) is the cautionary tale.

### Cited Findings
- **Microsoft Recall (redesigned Sept 2024, shipped 2025):**
  - Opt-in at setup and off unless the user turns it on.
  - Snapshots encrypted with keys protected by TPM and tied to Windows Hello Enhanced Sign-in Security.
  - Processing happens in a VBS Enclave (hypervisor-isolated from the kernel and admins), with attestation, and Windows Hello is required to access snapshots.
  - Only user-requested results leave the enclave, and Recall can be removed.
  - Sources: [Windows Blog](https://blogs.windows.com/windowsexperience/2024/09/27/update-on-recall-security-and-privacy-architecture); [PCWorld](https://www.pcworld.com/article/2470708/microsoft-now-confirms-you-can-opt-out-of-and-remove-windows-recall.html)
  - Critics note the original design was default-on with mostly plaintext storage, and a 2026 bypass claim (disputed by Microsoft, unverified). — [Vivian Voss](https://www.vivianvoss.net/blog/the-screenshot-diary)
- **Apple Intelligence:** an on-device semantic index of the meaning of the user's files, photos, emails and other content. It retrieves relevant personal data for a request and feeds it to (mostly on-device) models. App Intents expose app actions. — [Wing VC](https://www.wing.vc/content/unpacking-apple-intelligence-apples-vision-for-personalized-ai); [heyainews](https://heyainews.substack.com/p/how-apple-intelligence-works)
  - Status of personal-context Siri (mid-2026): only a vendor blog claims developer testing and a fall 2026 launch excluding the EU and China. Unverified. — [MemX blog](https://memx.app/blog/android-alternative-apple-personal-siri/)
- **Android Private Compute Core:**
  - An isolated sandbox for features (Live Caption, Now Playing, Smart Reply) that process ambient and OS data. Inferences stay inside Android System Intelligence.
  - All network traffic goes through the open-source Private Compute Services. ASI was formerly called "Device Personalization Services".
  - Sources: [Google PCC paper, arXiv 2209.10317](https://arxiv.org/pdf/2209.10317); [9to5Google](https://9to5google.com/2021/09/09/android-private-compute-services/)

### Inferences
- **Design to copy:** opt-in plus per-app exclusions (Recall filters private browsing and lets users exclude apps), hardware-bound encryption, re-authentication to view, an isolated indexing process with no network access, and an auditable egress path.
- **Self-export opportunity:** these OS stores are themselves rich personal data, but they are deliberately *not* exportable or accessible to third-party apps. A personal tool can't (and shouldn't) scrape Recall's DB or Apple's index. It should instead replicate the capture with its own consented pipeline.

### Gaps
- I found no sources on Windows diagnostic-data levels (Required/Optional) in 2025–26, Apple's Biome/knowledgeC store details, Samsung's on-device AI (Galaxy AI / Knox Vault) data handling, or Android 16/17 changes.

## 6. Stalkerware / parental-control / employee-monitoring (Teramind, ActivTrak, Hubstaff, mSpy, Bark)

### Takeaway
Monitoring software uses the techniques a "capture everything" app wants: keystrokes, interval screenshots or screen recording with OCR, app and URL usage, live view, and notifications via accessibility. What separates a personal tool from stalkerware is who installs and controls it, whether the monitored person knows, and whether data can leave the device to another party. The design must make covert third-party installation impractical.

### Cited Findings
- **Teramind:** logs keystrokes, screenshots, screen recordings, app usage, live view and session playback, OCR on screenshots, and rule-triggered automated actions. ActivTrak has no keylogger but offers screenshots (with redaction), live screen view and app termination. Comparison sources are vendor-biased. — [TechRadar Teramind](https://www.techradar.com/reviews/teramind); [TechRadar ActivTrak](https://www.techradar.com/reviews/activtrak); [People Managing People](https://peoplemanagingpeople.com/tools/activtrak-vs-teramind/)
- **Android stalkerware:** abuses the accessibility service to capture screen content, toasts and notifications. Android cannot ban accessibility outright, and Android 14+ restricts accessibility for sideloaded apps (2025 academic study, which evaluated Android 13 and earlier). — [arXiv 2508.02454](https://arxiv.org/html/2508.02454v1)
- **Coalition Against Stalkerware (founded 2019 by EFF, AV vendors and NGOs):** agreed a definition separating stalkerware from legitimate monitoring, and consensus detection criteria. — [EFF press release](https://www.eff.org/press/releases/eff-antivirus-companies-and-human-rights-groups-launch-coalition-combat-stalkerware); [Coalition leaflet](https://stopstalkerware.org/wp-content/uploads/2020/11/LEAFLET_2020_Coalition_against_Stalkerware_leaflet_partners.pdf)
- TechCrunch's guide to removing Android spyware describes users checking accessibility and device-admin grants and Play Protect warnings. — [TechCrunch 2025](https://techcrunch.com/2025/02/20/remove-android-spyware/)

### Inferences
- **Anti-stalkerware requirements for the personal tool:**
  1. No hidden mode: a persistent notification or icon, and the app appears in the launcher.
  2. No remote viewer: data is viewable only on-device or on the user's own authenticated devices, with no "dashboard for someone else".
  3. Set up on the device with the device owner's biometric or passcode, and re-confirm periodically.
  4. No sideload-only accessibility capture. If used at all, ship via app stores and keep it visible.
  5. Keystroke capture only within the tool's own input surfaces, or off by default.
  6. Easy full uninstall and wipe.
  7. Don't market to partners or parents for monitoring others.
  8. Seek a non-detection outcome from AV vendors by design, not by evasion.

  Screenshot or OCR cadence (Teramind/Recall-style) is reusable for self-capture with exclusions (password fields, private windows, banking apps).
- Employee-monitoring products show that the "capture everything" stack is commercially mature. The ethical delta is purely consent and control.

### Gaps
- I could not retrieve the Coalition's actual detection criteria text.
- I found no sources on mSpy (including its 2024 breach [uncited]), Bark, Hubstaff, Apple's Safety Check, or iOS/Android "app is monitoring you" notifications.

## 7. Local network/traffic capture (on-device VPN loggers, MITM certs, pcap)

### Takeaway
An on-device VPN (Android VpnService, iOS NEPacketTunnelProvider) gives per-app network *metadata* (DNS, destination IPs, SNI, volumes) without root and without a server. TrackerControl and NetGuard are the open-source references. Decrypting content requires a user-installed root CA (MITM), the same technique that sank Facebook Research. It breaks certificate-pinned apps and widens the attack surface. Metadata-only is the defensible default.

### Cited Findings
- **TrackerControl:**
  - Uses a local VPN with no root and no external server.
  - Parses plaintext DNS on-device to attribute connections to apps and tracker companies, and blocks by IP.
  - Blocklists: Disconnect, DuckDuckGo Tracker Radar, its own list, and Exodus signatures for in-app tracker libraries. It protects against DNS cloaking.
  - Deliberately avoids TLS interception. SNI/TLS parsing exists only in an opt-in research mode.
  - Incompatible with other VPNs and Android Private DNS, so it offers its own DoH.
  - Sources: [trackercontrol.org](https://trackercontrol.org/); [TrackerControl AGENTS.md](https://ithub.global.ssl.fastly.net/TrackerControl/tracker-control-android/blob/master/AGENTS.md); [F-Droid](https://f-droid.org/en/packages/net.kollnig.missioncontrol.fdroid/)
- Its network layer reportedly derives from NetGuard (Marcel Bokhorst), per a forum comment. — [/e/ forum](https://community.e.foundation/t/how-does-tracker-control-block-trackers/34376)
- Local VPN can break all traffic on some ROMs (older /e/ report). — [/e/ GitLab](https://gitlab.e.foundation/e/backlog/-/issues/3453)
- **MITM precedent:** Facebook Research's root certificate gave visibility into messages, email and web activity. Screenwise avoided a root CA and therefore couldn't decrypt HTTPS. — [Gizmodo](https://gizmodo.com/facebook-is-paying-teens-to-install-a-research-app-that-1832182370); [EFF](https://www.eff.org/deeplinks/2019/02/google-screenwise-unwise-trade-all-your-privacy-cash)

### Inferences
- **Yield vs risk:**

  | Capture level | Yield | Risk |
  |---|---|---|
  | Metadata via local VPN | Which apps talk to which companies, when, and how much. Useful for a "who's tracking me" ledger and for app-usage timelines. | Low; occupies the single VPN slot |
  | MITM decryption | Full content | High: breaks pinning, needs a CA the user must trust globally, and is a catastrophic key-compromise scenario |
  | Desktop pcap | Similar metadata | Needs admin rights |

- **Recommendation:** a metadata-only local VPN, plus content capture at the application layer (browser extension, OS exports) instead of MITM.

### Gaps
- No primary sources on Lockdown Privacy (iOS) architecture, desktop pcap tools, or 2025–26 changes to VpnService and NetworkExtension policies.
