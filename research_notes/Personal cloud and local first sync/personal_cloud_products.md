# Self-hosted "personal cloud" products as Google Drive/Photos/Docs and phone-backup alternatives (as of Oct 2026)

Method note: these notes come from about 16 web searches and fetches, run on 2026-10-16. Direct fetches of immich.app, nextcloud.com, selfh.st, linuxiac.com and help.nextcloud.com failed because of DNS errors in the research sandbox. GitHub API access to the project repos was also blocked. As a result, many facts below come from search-engine summaries of those pages rather than full reads. Facts that rely on third-party or affiliate sites are marked as such.

## Software stacks: Nextcloud, Immich, PhotoPrism, Seafile, oCIS/OpenCloud, Paperless (latest versions and 2025-26 developments)

### Takeaway
The photo side has matured quickly. Immich went stable at v2.0 in October 2025, shipped v3.0 in mid-2026 and was at v3.3.3 on 14 Oct 2026, so it is now a credible Google Photos replacement for technically capable households. Nextcloud has moved to year-based "Hub 26" releases (Spring in June 2026, Summer in September 2026). Its pitch is now aimed squarely at organizations leaving Microsoft and Google ("sovereignty", governance, Euro-Office) rather than at home users. Paperless-ngx reached 3.0 in July 2026. I could not confirm current versions of PhotoPrism or Seafile.

### Cited Findings
**Immich**
- Immich reached stable v2.0.0 in October 2025. That release removed the long-standing warning against using it as the only store for irreplaceable photos. — [search summary of Immich release coverage](https://wpde.org/thread/202787-immich-2-5-0-wurde-vor-wenigen-stunden-ver%C3%B6ffentlicht/) (secondary; the exact date was not verified from a primary source)
- The 2.x line continued in 2026. Immich 2.6 had more than 350 commits, with faster mobile performance, better playback and improved sharing. v2.6.2 followed around March 24, 2026, with fixes for shared-link uploads and mobile search filters. — [Linux.org/Linuxiac thread](https://www.linux.org/threads/linuxiac-immich-2-6-photo-and-video-management-solution-released-with-350-commits.64143/latest); [Renovate PR referencing v2.6.2](https://gitea.alexlebens.dev/alexlebens/infrastructure/pulls/5065)
- **Immich v3.0.0** was released mid-2026. The official blog post is dated July 1, 2026, though another copy is dated June 9, 2026. Most of the breaking changes affect the API: deprecated endpoints were removed, errors have a new format, video durations are now in milliseconds, and star ratings have a minimum of 1. Support for pgvecto.rs was dropped. Upgrading means changing IMMICH_VERSION to v3 and running `docker compose pull && up -d`. Some features were "temporarily removed": recoloring, live-photo editing and local asset editing. — [Immich v3.0.0 release blog](https://immich.app/blog/v3.0.0-release); [Linuxiac](https://linuxiac.com/immich-3-0-released-with-big-upgrades-for-self-hosted-photo-libraries/); [PixelUnion "Immich v3 is here"](https://pixelunion.eu/blog/2026/07/immich-v3/)
- Current line, from the GitHub releases page fetched 2026-10-16. The page shows day and month only; the year is inferred as 2026.
  - v3.2.0 on 10 Sep.
  - v3.3.0 on 7 Oct, with shared "people" management across users, birthday memories, automatic stacking of mobile edits over their originals, OAuth claims (quota, role, username) synced at every login, better thumbnails, opt-in ML speed and memory improvements (`MACHINE_LEARNING_MODEL_REVISION=v2`) and new PP-OCRv6 OCR models.
  - v3.3.1 on 8 Oct.
  - **v3.3.3 on 14 Oct**, with a faster people query and explore page.
  — [GitHub immich-app/immich releases](https://github.com/immich-app/immich/releases)
- Immich's feature set now mirrors Google Photos: face and people recognition, OCR, memories, map, sharing and mobile auto-backup (see the release features above). The fact that it still has release candidates and point fixes every few days shows how fast it is moving. — [GitHub releases](https://github.com/immich-app/immich/releases)

**Nextcloud**
- Nextcloud scheduled "Hub 26 Spring" for June 9, 2026 as its 10th-anniversary release. The marketing was about migrating away from Microsoft 365 and Google Workspace, optional AI, and retention and governance controls. — [Nextcloud event page](https://nextcloud.com/nl/?p=400297); [Hub 26 Spring press release](https://nextcloud.com/blog/press_releases/nextcloud-hub-26-spring-delivers-new-office-experience-lighter-ui-and-and-a-new-governance-tool/)
- "Hub 26 Summer" launched September 16, 2026. Its headline is a desktop client for **Euro-Office**, which Nextcloud describes as "the European Open Source office suite" and a sovereign alternative to Microsoft Office, with collaborative editing from desktop or browser. Euro-Office editing on iOS and Android was also announced. Other features: a new Teams app (team spaces, channels, announcements), Notes templates and version history, and **a reworked Photos app with a map view and automatic trip grouping**. — [Nextcloud blog: Hub 26 Summer](https://nextcloud.com/blog/nextcloud-hub26-summer/); [press release](https://nextcloud.com/blog/press_releases/hub-26-summer/); [community post](https://help.nextcloud.com/t/nextcloud-hub-26-summer-autonomy-for-teams-office-on-desktop-a-fresh-take-on-photos/249430)
- Collabora Online is still offered as "the traditional Nextcloud Office solution". A third-party write-up lists new Collabora features in Hub 26 Summer, such as Writer's multi-page view and the Calc Solver in the toolbar. That list is not verified against Nextcloud's own notes. — [Hub 26 Spring press release](https://nextcloud.com/blog/press_releases/nextcloud-hub-26-spring-delivers-new-office-experience-lighter-ui-and-and-a-new-governance-tool/); [E-Time summary](https://www.e-time.it/en/nextcloud-hub-26-summer-updates/)
- A third-party guide links server release 33.0.2 with Hub 26. This is unverified. — [tech-insider.org (Finnish)](https://tech-insider.org/fi/?p=595)

**ownCloud Infinite Scale / OpenCloud**
- Kiteworks owns ownCloud and runs it through an Open Source Program Office. That office relicensed the projects to Apache 2.0 and replaced the CLA with a DCO. — [Kiteworks press release](https://www.kiteworks.com/nl/company/press-releases/kiteworks-ospo-owncloud-digitale-datasoevereiniteit/)
- oCIS security release 8.0.3 came out around May 11, 2026 and fixed critical vulnerabilities. ownCloud Desktop 7.1.1 came out around Sep 1, 2026. Since desktop 7.0, the client connects only to Infinite Scale, not classic ownCloud Server. — [ownCloud sync clients page](https://owncloud.com/sync-clients/); [ownCloud news](https://owncloud.com/news/infinite-scale-release/) (secondary summaries)

**Paperless-ngx**
- Paperless-ngx 3.0.0 was released around July 22, 2026, with patches 3.0.1 to 3.0.3 by July 25. The v3 beta brought AI and OCR features, document versioning, a plugin parser framework and many breaking changes. — [Elestio catalog update, Jul 19–25 2026](https://blog.elest.io/elestio-catalog-updates-23-new-releases-this-week-july-19-25-2026/); [Releasebot](https://releasebot.io/updates/paperless-ngx) (third-party)

### Inferences
- "Can Immich replace Google Photos?" now has a credible yes on features and stability for people who can run Docker. The constant release churn (point releases every few days, API breaks at v3, features temporarily removed) still means ongoing upkeep.
- Nextcloud's strategy is aimed at public-sector and enterprise "digital sovereignty". Home users benefit, but they are not the target. Its stronger Photos app is a partial answer to Immich.
- Euro-Office appears to be a new office option inside Nextcloud alongside Collabora. Its lineage is unclear from these sources; it may be ONLYOFFICE-derived, but this is not verified.

### Gaps
- PhotoPrism and Seafile current versions and 2025-26 news: searches returned nothing usable, and GitHub and API access was blocked.
- Immich's paid "supporter" licence pricing and its FUTO backing: not re-verified in this session. My training knowledge is about $25 per user or $100 per server, optional, but this is unconfirmed for 2026.
- The exact Nextcloud server version number behind Hub 26 Summer is not confirmed.
- OpenCloud (the Heinlein-backed fork of oCIS) 2026 releases: no results found.
- Euro-Office's technical basis is unverified.

## Appliances and OSes: Synology, UGREEN, TerraMaster, Umbrel, Start9, CasaOS/ZimaOS, TrueNAS, Unraid (prices and target users)

### Takeaway
Synology's 2025 drive lock-in was partly reversed in DSM 7.3 on Oct 8, 2025. The reversal covers only 2025 Plus, Value and J models, and M.2 drives still need to be certified. The episode damaged trust and helped challengers such as UGREEN NASync (about $300–700 diskless). Consumer "app-store" home servers sit in roughly the $550–900 range: Umbrel Home at about $549–699 and the Start9 Server One at about $899. ZimaOS is free, with a paid tier. Most pricing evidence comes from affiliate sites.

### Cited Findings
**Synology**
- Synology announced DSM 7.3 on October 8, 2025. On 2025-model-year DiskStation Plus, Value and J series, it supports installing and building storage pools on non-validated third-party drives. — [Synology press release](https://www.synology.com/en-ca/company/news/article/dsm73)
- Limits of the reversal:
  - M.2 SSD pools and caches still need drives on Synology's compatibility list.
  - Business and enterprise models and previous-generation products stay under the old compatibility policy.
  - DSM may show informational warnings for third-party drives.
  — [AppleInsider "Synology caves... for now"](https://appleinsider.com/articles/25/10/08/synology-caves-allows-all-hard-drives-in-2025-nas-range---for-now); [nasstore.eu](https://nasstore.eu/dsm-7-3-synology-finally-reintroduces-support-for-third-party-hard-drives/); [Gigazine](https://www.gigazine.net/gsc_news/en/20251009-synology-third-party-hdd-support-returns)
- Reports link the reversal to a sharp fall in NAS sales, but this is not confirmed by Synology. — [Guru3D](https://guru3d.com/story/synology-reverses-policy-banning-thirdparty-hdds-after-nas-sales-plummet/); [TechSpot](https://www.techspot.com/news/109787-synology-reverses-course-non-certified-hdds-nas-systems.html)
- Commentators remain doubtful about trust ("Can we forgive and forget"). — [NASCompares](https://nascompares.com/news/are-synology-nas-ok-to-buy-now/); [Evetech](https://evezone.evetech.co.za/deep-dives/is-synology-still-worth-it-after-the-2025-drive-lock-in-controversy)

**UGREEN NASync**
- DXP4800 Plus: about $620–700 diskless list price. It was $583.99 in a June 2026 Prime Day sale, and refurbished units go from about $450. — [NASCompares deals 2026](https://nascompares.com/deals/ugreen-nas-prime-day-summer-deals-2026/); [tech-insider comparison](https://tech-insider.org/synology-vs-qnap-vs-ugreen-nas-2026/)
- DXP2800: $296.99 at Walmart. A 2-bay DH2300 deal was seen at $167.99. — [Walmart](https://www.walmart.com/c/kp/nas-ugreen); [Slickdeals](https://slickdeals.net/f/18835981-ugreen-nasync-dh2300-plus-2-bay-60tb-support-capacity-167-99-free-shipping)

**Umbrel, Start9, ZimaOS**
- **Umbrel Home** prices conflict:
  - One comparison says from $549, with the Umbrel Pro from $699.
  - A May 2026 two-year owner review says it starts at $599, with $699 for 2 TB and $949 for 4 TB.
  — [The Bitcoin Hole comparison](https://thebitcoinhole.com/vs/umbrel-vs-start9); [Initial Charge, "Two Years With Umbrel Home"](https://initialcharge.net/2026/05/umbrel-home-2-years/)
- **Start9 Server One**: about $899 (single third-party source). — [The Bitcoin Hole](https://thebitcoinhole.com/vs/umbrel-vs-start9)
- **ZimaOS**: free, or $29 lifetime for "Plus". Another source says it is free up to 4 disks and 3 users. You bring your own hardware, such as a ZimaBoard. — [The Bitcoin Hole: Umbrel vs ZimaOS](https://thebitcoinhole.com/vs/umbrel-vs-zimaos); [homeio.app](https://homeio.app/best-home-server-os)

**Self-hoster OS landscape (selfh.st 2025 survey, published Nov 2025)**
- 4,081 completed responses. Linux is the top host OS at 81%. Docker is the dominant container runtime; Podman is third at 11%. — [selfh.st 2025 results](https://selfh.st/survey/2025-results/); [Linuxiac write-up](https://linuxiac.com/self-hosters-confirm-it-again-linux-dominates-the-homelab-os-space/); [It's FOSS](https://itsfoss.com/opinion/self-hosting-rising.md)

### Inferences
- The market has split three ways:
  1. Traditional NAS (Synology, UGREEN, TerraMaster) for file and photo storage with vendor apps.
  2. "Appliance + app store" boxes (Umbrel, Start9, Zima) that copy the Home Assistant Green/Yellow model.
  3. DIY OSes (TrueNAS, Unraid, Proxmox) for enthusiasts.
- None of these removes the need to solve remote access and offsite backup.
- The demographics of the selfh.st survey (Linux, Docker) show the core audience is technical. It is not evidence of mainstream adoption.

### Gaps
- TerraMaster, TrueNAS (Community Edition / 25.x "Fangtooth" and later) and Unraid pricing and 2026 news were not researched. My training knowledge says Unraid moved to a subscription-style licence in 2024 (Starter/Unleashed/Lifetime, roughly $49–$249), but this is unverified here.
- No official manufacturer prices were confirmed for Umbrel or Start9.
- The CasaOS maintenance status (IceWhale has focused on ZimaOS) is unverified.

## Why ordinary people still rely on Google/iCloud: remote access, uptime, 3-2-1 backup, maintenance, security, power (adoption data)

### Takeaway
The structural barriers have not changed. Reaching a home server from outside is hard: CGNAT and ISP port blocking break simple port forwarding, and exposed ports are scanned constantly. That pushes users toward mesh VPNs like Tailscale, which can be slow when relayed. A home box is also not an offsite backup. Good quantitative data on how many non-technical people self-host was not found; the best survey data covers enthusiasts only.

### Cited Findings
- Tailscale is free for personal use, needs no open ports, and works through CGNAT and mobile networks. It is the default recommendation in 2026 beginner guides. — [termai.sh guide](https://termai.sh/blog/access-home-server-from-anywhere) (vendor-promotional); [hometechops explainer](https://hometechops.com/start/remote-access-explained)
- Port forwarding is "exposed-by-default, scanned constantly, and often blocked at the ISP anyway". — [hometechops](https://hometechops.com/start/remote-access-explained)
- One user behind CGNAT reported that Tailscale traffic always went through relays (DERP), with more than 100 ms latency, and moved to a VPS plus WireGuard. Guides describe VPS relays or Headscale as CGNAT workarounds. — [Lemmy/campfyre thread](https://campfyre.nickwebster.dev/post/242190); [corelab.tech](https://corelab.tech/running-plex-jellyfin-behind-cgnat/)
- The enthusiast-only scale indicator is the selfh.st survey: 4,081 respondents, overwhelmingly Linux and Docker users. — [selfh.st](https://selfh.st/survey/2025-results/)
- Release churn is itself a maintenance burden. Immich v3 broke third-party API tools and temporarily removed features. Paperless-ngx 3.0 needed three patches within three days. — [Linuxiac on Immich 3](https://linuxiac.com/immich-3-0-released-with-big-upgrades-for-self-hosted-photo-libraries/); [Elestio](https://blog.elest.io/elestio-catalog-updates-23-new-releases-this-week-july-19-25-2026/)
- Self-hosted server software regularly ships critical security fixes, for example oCIS 8.0.3 in May 2026. Users who do not patch stay exposed. — [ownCloud](https://owncloud.com/news/infinite-scale-release/)

### Inferences
- For non-technical users, the critical path is: buy box → set up remote access → set up offsite copy → apply updates. Each step is where self-hosting fails today. Umbrel and Synology-style appliances only automate the first and some of the last.
- Phone backup is the main use case. It needs reliable background upload on iOS, which is constrained for all third-party apps, and an always-reachable server.

### Gaps
- No 2025-26 data was found on NAS ransomware campaigns (for example DeadBolt or Qlocker successors). The search returned none.
- No quantified data on home-server power costs. A rough rule of thumb: a 10–30 W always-on box uses about 90–260 kWh per year. That is a calculation, not a sourced figure.
- No consumer-level adoption statistics were found, such as household NAS penetration or Immich user counts. The Google Photos and iCloud user base was not re-sourced.
- No 2026 r/selfhosted survey was found.

## E2EE commercial clouds as a middle ground: Proton, Ente, Cryptee, Tresorit, Filen, Apple ADP (incl. UK)

### Takeaway
End-to-end-encrypted (E2EE) consumer clouds are the realistic "middle ground". They avoid running hardware while keeping data unreadable to the provider. They are priced near Google One. Ente is also open-source and self-hostable. Apple ADP is still unavailable to new UK users as of Oct 2026, and the legal fight over the UK's secret Technical Capability Notices is unresolved: an Investigatory Powers Tribunal hearing took place in Sep 2026 and a substantive hearing is listed for Dec 2026.

### Cited Findings
**Apple Advanced Data Protection (ADP)**
- Feb 2025: Apple stopped offering ADP to new UK users, and existing UK users must eventually turn it off. iCloud Keychain, Health, iMessage and FaceTime stay end-to-end encrypted in the UK. Apple says it has never built a backdoor. — [Apple Support 122234](https://support.apple.com/en-ie/122234); [MacStories](https://www.macstories.net/linked/apple-to-eliminate-advanced-data-protection-for-icloud-accounts-in-the-uk/)
- Oct 2025: the FT reported a **second** notice targeting only British users' ADP data. Apple's initial tribunal challenge was dismissed in Oct 2025 because of a "change in circumstances". — [Privacy International case page](https://privacyinternational.org/legal-action/pi-apple-tcn-challenge); [PI Q&A](http://privacyinternational.org/long-read/5547/our-challenge-against-uks-secret-tcn-powers)
- 4 Aug 2026: Apple filed a new complaint at the Investigatory Powers Tribunal. On 17 Sep 2026, Apple challenged the government's "neither confirm nor deny" stance at a tribunal hearing, and Privacy International's counsel called that stance "farcical". The PI/Liberty claim (IPT/25/83/CH) is open, with a substantive hearing listed for Dec 2026. — [9to5Mac, 2026-09-17](https://9to5mac.com/2026/09/17/apple-pushes-uk-court-to-lift-secrecy-around-encryption-backdoor-order/); [MacDailyNews, 2026-08-03](https://macdailynews.com/2026/08/03/apple-launches-legal-challenge-to-uk-demand-for-access-to-encrypted-user-data/); [Privacy International](https://privacyinternational.org/legal-action/pi-apple-tcn-challenge)
- One source claims Apple expanded ADP's E2EE to more iCloud categories in 2026. This is unverified and from a low-reputation site. — [uinat.com](https://uinat.com/news/apple-advanced-data-protection-expansion-2026/)

**Ente**
- 10 GB free, then 50 GB for $2.49 per month, per Ente's own comparison page (verified Sep 2026). An Aug 2026 third-party blog cites $5 per month for 100 GB. The two may be different tiers. — [Ente vs Proton Drive Photos](https://ente.com/compare/ente-vs-proton-drive-photos/); [Stingle blog, Aug 2026](https://blog.stingle.org/2026/08/stingle-photos-vs-ente-vs-immich-vs-proton-drive-which-privacy-focused-photo-backup-is-right-for-you/)

**Proton Drive**
- Drive Plus is listed at €4.99 per month for 200 GB (a Sep 2026 review). Business "Drive Professional" is about $7.99 per user per month. — [Cloudwards review 2026](https://www.cloudwards.net/review/proton-drive/); [SaaSworthy](https://www.saasworthy.com/product/proton-drive/pricing)

**Tresorit**
- Premium pricing: about $14.50–19 per user per month for business, and "Personal Essential" at about $13.99 per month. — [ifeeltech Tresorit vs Proton 2026](https://ifeeltech.com/blog/tresorit-vs-proton-drive-business); [privacyon.com](https://www.privacyon.com/blog/best-privacy-focused-cloud-storage-2026)

**Filen**
- 10 GB free, with paid plans reportedly from $0.99 per month for 100 GB. Unconfirmed against first-party pricing. — [tech2geek](https://www.tech2geek.net/the-best-private-cloud-storage-services-in-2026-secure-alternatives-to-google-drive-and-dropbox/); [Privacy Guides forum](https://discuss.privacyguides.net/t/filen-or-mega-or-proton-drive/15653)

### Inferences
- For most people the most practical privacy upgrade is an E2EE cloud (Ente for photos, Proton for Drive, Docs and Pass), optionally mirrored to a local NAS. A fully self-hosted stack is a harder step.
- Ente's open-source, self-hostable server bridges both models. That point comes from general knowledge and was not re-verified this session.
- The UK ADP saga shows that a government can quietly remove even a big vendor's E2EE in one jurisdiction. That is an argument for vendor diversity and local copies.

### Gaps
- Proton Docs, Sheets and Pass 2025-26 feature news was not researched in this session.
- Cryptee status was not researched.
- Ente self-hosting documentation and changes were not verified.
- iCloud Keychain / Passwords app specifics beyond "remains E2EE in UK" were not researched.
- Pricing for Proton, Tresorit and Filen comes mostly from third-party review sites and conflicts; first-party pricing pages were not fetched.
