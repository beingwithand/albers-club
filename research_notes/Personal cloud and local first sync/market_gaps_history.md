# Personal Middleman Server / Personal Cloud: Market, Demand, History and Gaps (as of Oct 16, 2026)

Scope note: about 20 searches, but immich.app could not be fetched (DNS failure), so Immich facts come from search snippets of its blog. Items marked [OLDER] are from before 2024. Items marked [UNVERIFIED-BACKGROUND] come from the researcher's prior knowledge, were not confirmed in this session, and are kept to Inferences or Gaps only.

## 1. Historical attempts: what happened and why

### Takeaway
Most failures came from four causes: (a) VC-funded companies that got attention but no revenue (Sandstorm, Lima, Urbit/Tlon); (b) hardware tied to a vendor's cloud relay, which strands users when the company dies or gets breached (Lima, Helm, WD); (c) a product left to stall after an acqui-hire (Keybase); (d) the vendor's own security failures (WD). The clearest current success, Umbrel, sells polished hardware with an app store on top of open-source apps. It started in the Bitcoin-node niche and moved out into general self-hosting.

### Cited Findings
**Sandstorm.io [OLDER]**
- Sandstorm "mostly shut down" as a company in 2017. It had "run out of investor money while having achieved essentially no revenue". It was "popular on Hacker News" but that "never really converted into paying users". It made "no real progress" in enterprise, the market where it expected the profit. It found neither new investors nor an acquirer, and most of the team joined Cloudflare. Source: Kenton Varda, "Shutting down Oasis", Sep 2019 — [Sandstorm blog](https://sandstorm.io/news/2019-09-15-shutting-down-oasis)
- The open-source project then stagnated. A 2020 post by Ian Denhardt says development "wasn't going anywhere fast". The project is now community-run, and Varda is no longer the maintainer — [Sandstorm news index](https://sandstorm.io/news/); [HN thread](https://hn.svelte.dev/item/44844394)

**Lima (Kickstarter personal cloud) [OLDER]**
- The Kickstarter closed Sep 2013 with about $1.2M from 12,840 backers against a $69K goal. Shipping slipped repeatedly from the promised Dec 2013 date — [Crowdfund Insider](https://www.crowdfundinsider.com/tag/lima/)
- Lima raised about $3.7M in VC, including $2.5M from Partech, and reached about 80,000 users. It ran out of money, and its servers shut down on Mar 1, 2019. Afterward devices still worked on the local network, but adding devices, resetting passwords, sharing and remote access stopped working — [Goodbye Lima (ex-employee blog)](https://blog.separateconcerns.com/2019-02-15-goodbye-lima.html); [Next INpact](https://next.ink/brief-article/lima-ferme-ses-portes-plus-de-80-000-utilisateurs-sur-le-carreau/); [StorageNewsletter](https://www.storagenewsletter.com/?p=198193)

**Helm personal server [OLDER]**
- Helm launched in 2018 as a designer home server for email, calendar and contacts. The company was Privacy Labs, with CEO Giri Sreenivas. At launch it promised that the software would let people "run their own gateways with their own AWS account in the event Helm has to shut down". Parts of the stack were proprietary — [Dezeen](https://www.dezeen.com/2018/11/07/helm-personal-server-new-deal-design-data-security/amp/); [Dave Peck](https://davepeck.org/2018/10/19/the-helm/)
- It apparently shut down around Dec 2022. The only source is a forum comment; no official notice was found — [Tildes](https://tildes.net/~tech/1du6/in_major_gaffe_hacked_microsoft_test_account_was_assigned_admin_privileges)

**Western Digital My Book Live / My Cloud**
- 2021 [OLDER]: My Book Live and Live Duo NAS devices, which were out of support, were mass-wiped remotely, and an estimated petabytes of user data were lost. WD offered data recovery and a trade-in program — [PetaPixel/aggregated coverage](https://petapixel.com/2023/04/03/western-digitals-network-breached-multiple-services-taken-down)
- 2023 [OLDER]: WD detected a network breach on Mar 26, 2023 and took My Cloud services offline itself for about 10 days. Users with local NAS boxes could not reach their own data remotely. The attackers claimed about 10TB stolen and an 8-figure ransom — [TechRadar](https://www.techradar.com/news/western-digital-reveals-more-on-potential-cyber-attack); [APH Networks](https://aphnetworks.com/news/27032-after-10-days-western-digitals-my-cloud-finally-restored-following-hack); [PCWorld](https://www.pcworld.com/article/1681254/western-digitals-my-cloud-goes-down-after-hack.html)

**Keybase [OLDER]**
- Zoom acquired Keybase in May 2020. Development stopped, but the service stays up. Users "revolted", and community figures called the deal an acqui-hire — [Wikipedia](https://en.wikipedia.org/wiki/Keybase); [Decrypt](https://decrypt.co/28121/keybase-users-revolt-following-zoom-acquisition); [Peergos](https://peergos.org/posts/keybase-left-building)

**Urbit / Tlon**
- Tlon cut staff in early 2023 and dropped Port, its self-hosting tool. In Aug 2024 the Urbit Foundation reported it had run out of capital, and its board fired the head (Lehmann). Curtis Yarvin returned in 2024 as "wartime CEO" — [Compact](https://www.compactmag.com/article/the-rise-and-fall-of-urbit/); [Wikipedia: Yarvin](https://en.wikipedia.org/wiki/Curtis_Yarvin)
- In 2025 the Foundation had "scaled way down". Tlon's focus is now its messaging app plus hosted planets, which had a waitlist; this means it pivoted to hosting rather than home servers — [Martian Computing](https://martiancomputing.substack.com/p/urbit-update-2025)

**Solid / Inrupt**
- Inrupt was co-founded by Tim Berners-Lee and raised about $30M Series A in 2021 (Forté Ventures, Akamai, Hearst, Allstate and others). It positions itself as enterprise and government "user data platform" infrastructure, not a consumer product — [Pulse 2.0](https://pulse2.com/user-data-platform-company-inrupt-raises-30-million/); [Silicon Republic](https://siliconrepublic.com/?p=955572)

**Umbrel (success case)**
- Seed round of $3M in Oct 2021 from Village Global, Slow Ventures, OSS Capital, Naval Ravikant and others, pitched as "a server in every home". At the time it had more than 13,000 people running Umbrel. No later round is public — [Umbrel blog](https://blog.getumbrel.com/seed-6d09aa08f8ac); [VCBacked](https://www.vcbacked.co/company/umbrel)
- The upgraded Umbrel Home shipped in Feb 2024 at $399 (Intel N100, 16GB, 2TB SSD); a forum user later saw it listed at $429. umbrelOS 1.0 (Mar 2024) was a ground-up rebuild, and the current version is 1.4+. Umbrel's model is one-time hardware sales plus a free OS and app store that runs on Raspberry Pi and other boxes — [Umbrel community](https://community.umbrel.com/t/introducing-the-new-upgraded-umbrel-home-now-more-affordable-than-ever/15197); [nobsbitcoin](https://nobsbitcoin.com/umbrelos-v1-0); [isitreallyfoss](https://isitreallyfoss.com/projects/umbrel)

**Synology (incumbent NAS, 2025 lesson)**
- In 2025 Synology restricted Plus-series NAS features to Synology-branded drives. After reported sales declines it reversed the policy in DSM 7.3 (Oct 7–8, 2025); M.2 pool creation still requires drives on its list — [Guru3D](https://guru3d.com/story/synology-reverses-policy-banning-thirdparty-hdds-after-nas-sales-plummet/); [Slashdot/Ars](https://tech.slashdot.org/story/25/10/08/1723232); [LowEndBox](https://lowendbox.com/blog/synology-reverses-policy-on-synology-branded-hard-drives-only-with-dsm-7-3/)
- Synology also removed Video Station and other multimedia packages in DSM 7.2.2. The source is a competing vendor (ZimaSpace), so it is biased — [ZimaSpace blog](https://shop.zimaspace.com/pl/blogs/zima-campaign-hub/zimaos-vs-synology-dsm-nas-os-comparison)

### Inferences
- The recurring failure is **dependence on a relay or cloud run by the vendor** (Lima, WD, Helm). A new product should keep core functions working with no vendor servers and should make the relay replaceable, either open-source or bring-your-own (for example Tailscale, Cloudflare Tunnel or a self-run relay). Saying so openly in marketing is itself a trust feature.
- **HN popularity is not revenue** (Sandstorm). Developers who self-host are vocal but do not pay much. Paying users are more likely to be families or "prosumer but not sysadmin" buyers who will pay for hardware or a backup service.
- Umbrel succeeded with a narrow, motivated niche at launch (Bitcoin node operators), polished hardware and a curated app store. It did not try to be a new protocol (Solid, Urbit, Sandstorm grains) and instead packaged existing open-source apps.
- The Synology episode shows that buyers in this market punish lock-in quickly.
- [UNVERIFIED-BACKGROUND] Cloudron (paid open-core, about $15/month for more than 2 apps), YunoHost (volunteer, French, Debian-based), FreedomBox (Debian, with the Olimex "Pioneer" hardware) and Amahi (home server, wound down around 2020–2022) all survived as niche projects or faded. None broke into the mainstream. Perkeep (formerly Camlistore, Brad Fitzpatrick) and Upspin (Google engineers, 2017) were technically admired but became dormant hobby projects with no consumer UX.

### Gaps
- No sources were retrieved on Cloudron, YunoHost, FreedomBox, Amahi, Perkeep or Upspin, including their current status. Amahi's shutdown date is not verified.
- There is no official Helm shutdown notice or stated reason.
- No Umbrel unit sales, revenue, or 2025–26 funding were found. Whether WD was sued over the 2021 wipe was not confirmed.
- Inrupt's 2024–26 status (layoffs, new funding) was not found.

## 2. Current venture and indie activity (2024–2026) and demand data

### Takeaway
Funding in the space is small and patchy. The main players are FUTO's patronage of Immich, a few seed and Series A rounds, and Nextcloud on the enterprise side; no large consumer "personal cloud" round appears in 2024–26. Demand signals are real but niche: r/selfhosted has about 725K–790K members, Nextcloud is growing about 50% on a European sovereignty push, and the public broadly distrusts AI and data handling.

### Cited Findings
- **Immich / FUTO:** The core team went full-time under FUTO in May 2024. v2.0.0, the stable release, shipped in Oct 2025, later than the Q1 2025 target. At v2 the project had 271 releases, about 78K GitHub stars, 1,558 contributors and 31.5K Discord members. Its stated plan is paid services, starting with **end-to-end encrypted off-site backup and restore built into Immich**, and it says it will "never paywall features". A June 2026 retrospective post exists but was not read — [Immich blog: v2.0.0](https://immich.app/blog/v2.0.0-release); [Linuxiac](https://linuxiac.com/immich-team-goes-full-time/); [Immich 2024 review](https://immich.app/blog/2024-year-in-review)
- **Ente** (E2EE photos, open source): Crunchbase lists one round, from Appreciate Capital, with no amount or date. Tracxn lists about 83 employees (Sep 2026), but that figure seems high and is unconfirmed. Ente says "500 million memories preserved" and ships features such as Library Sharing (Sep 2026) and a family plan — [Crunchbase](https://www.crunchbase.com/organization/ente-technologies); [Tracxn](https://tracxn.com/d/companies/ente/__C-WQjshq6TQzDPYVFj0rV6sIcwCHPP3LRoj9gHAT030); [Ente news](https://ente.com/news/); [Ente blog](https://ente.com/blog/)
- **Anytype:** About $13.4M led by Balderton (Aug 2023), with Protocol Labs and others, earmarked for multi-user collaboration. Aggregator totals vary, up to about $29M — [TechFlow](https://www.techflowpost.com/en-US/newsletter/29870); [Seedtable](https://seedtable.com/companies/anytype/funding-rounds/series-a-2023-08); [CB Insights](https://www.cbinsights.com/company/anytype/financials)
- **Rocicorp (Zero/Replicache):** Latest known round is $7M early-stage (Jan 2022), with about 8 employees per PitchBook in 2026 — [PitchBook](https://pitchbook.com/profiles/company/509669-29)
- Commentary says local-first sync engines (Zero, ElectricSQL, TanStack DB, Jazz) "went mainstream in 2025" as a developer stack — [Kanopy Labs](https://kanopylabs.com/blog/tanstack-db-vs-electricsql-vs-zero-sync); [lofi.so directory](https://lofi.so/directory)
- **Nextcloud:** Added more than 2M professional users in a year, with bookings up more than 50% vs 2024. The CEO says interest "tripled" because customers see "dependency on big tech as a risk". Fastest growth is in the Netherlands, Brazil and Denmark. The company plans more than €250M investment by 2030 ("Sovereignty 2030"). All figures are company-reported — [Nextcloud blog](https://nextcloud.com/es/blog/digital-sovereignty-gains-momentum-millions-of-new-enterprise-users/); [Nextcloud press](https://nextcloud.com/blog/press_releases/nextcloud-invests-in-digital-sovereignty/)
- **r/selfhosted:** About 724,594 subscribers as of Aug 2, 2026 per Redpulse. DreamHost claims more than 790K; the two figures conflict. GummySearch-derived data shows about 18–24K joins per month from late 2025 to Sep 2026, but that data is internally inconsistent — [Redpulse](https://redpulse.io/subreddit-search/r/selfhosted/); [DreamHost](https://www.dreamhost.com/blog/self-hosting/); [Hive Index](https://thehiveindex.com/communities/r-selfhosted/)
- **selfh.st survey:** In 2025, 98.3% of respondents used containers, up from 97%. The 2026 survey closes Oct 31, with results due in early November 2026 — [DreamHost](https://www.dreamhost.com/blog/self-hosting/); [Lemmy.World](https://lemmy.world/post/52832227)
- One vendor-cited projection puts the self-hosting market at $15.6B (2024) growing to $85.2B (2034). This is a commercial forecast and the definition is loose — [DreamHost](https://www.dreamhost.com/blog/self-hosting/)
- **Pew (2025):** 50% of US adults are more concerned than excited about AI (June 2025, n=5,023). About 71% expect AI to make their personal information less secure, vs 3% who expect it to be more secure. 61% want more control over AI in their lives. 59% have little or no confidence in companies to use AI responsibly — [Pew topic page](https://pewresearch.org/topic/internet-technology/emerging-technology/page/2); [Decrypt summary](https://decrypt.co/340511/americans-want-ai-benefits-fear-losing-makes-human?amp=1)
- [OLDER] Pew 2019: 79% of US adults were concerned about how companies use their data, and 81% felt they had little or no control — [Fortune](https://fortune.com/2019/11/15/pew-survey-state-of-data-privacy)
- **EU Data Act:** Cloud-switching obligations apply from Sep 12, 2025 to IaaS, PaaS and SaaS offered to EU customers, wherever the provider is based. Customers can switch to another provider **or to on-premises** with at most 2 months' notice, and switching fees are being phased out. On-prem and private cloud are excluded from the provider obligations — [Morgan Lewis](https://www.morganlewis.com/blogs/sourcingatmorganlewis/2025/09/eu-data-act-begins-september-12-impacting-cloud-services-connected-products-and-other-data-industries); [Alston & Bird](https://www.alston.com/en/insights/publications/2025/09/eu-data-act-switching-requirements-cloud-services); [Mishcon](https://www.mishcon.com/news/eu-data-act-what-cloud-service-vendors-need-to-know-about-new-switching-rights)

### Inferences
- The most sustainable patterns appear to be: **non-profit or patron funding plus a paid encrypted backup add-on** (Immich/FUTO), **consumer E2EE subscription** (Ente), **hardware margin plus a free OS** (Umbrel), and **enterprise sovereignty licensing** (Nextcloud). Pure-VC consumer personal-server plays have a poor record.
- Local-first sync engines are maturing as building blocks (Zero, ElectricSQL, Jazz, Automerge/Yjs). An indie developer can now build the "sync all devices" layer from existing parts rather than inventing a protocol.
- Demand is broad (general distrust of AI and data use) but conversion is shallow. The proven buyers are the roughly 0.7–0.8M r/selfhosted members and adjacent prosumers. Products need to win the non-technical family member who is "concerned but won't run Docker".
- The EU Data Act's "switch to on-premises" right is aimed mainly at B2B, but it strengthens the legitimacy of import and export tooling.

### Gaps
- Funding details were not found for Jazz (Garden Computing), ElectricSQL (a 2023 seed of about $5M is [UNVERIFIED-BACKGROUND]), Ente's round size, or any 2025–26 Umbrel or Anytype raise.
- No data was found on Google Takeout usage, DMA Article 6(9) portability APIs (Google's Data Portability API launched around 2024 [UNVERIFIED-BACKGROUND]), or Google Trends for "de-Google".
- No consumer-specific survey (as opposed to enterprise) was found on willingness to pay for a personal cloud.

## 3. Regulatory and trust triggers

### Takeaway
The strongest emotional triggers are **account lockout with total data loss** (the Google CSAM false positives) and **governments weakening encryption** (UK ADP removal). Price is a weaker trigger than expected: in 2025–26 Google cut prices and added storage by bundling it with AI plans. That bundling raises "my files are an AI upsell vehicle" concerns but lowers the price-shock motivation.

### Cited Findings
- **Google CSAM false positives [OLDER, 2022]:** NYT reported that "Mark" sent photos of his toddler's infection to a doctor and lost his entire Google account. Police found "no crime occurred", but Google kept the account permanently disabled. A second father in Texas lost his account. In 2021 Google filed more than 600K CSAM reports and disabled more than 270K accounts — [PetaPixel](https://petapixel.com/2022/08/22/google-flags-photos-of-fathers-sick-son-as-child-abuse-informs-police); [Gizmodo](https://gizmodo.com/google-csam-photodna-1849440471); [MediaNama](https://www.medianama.com/2022/08/223-google-disables-accounts-flags-parents-csam-privacy/)
- **UK ADP:** In Feb 2025 Apple stopped offering Advanced Data Protection to new UK users after a reported Investigatory Powers Act order, and existing users must eventually disable it — [Six Colors](https://sixcolors.com/post/2025/02/apple-is-removing-its-advanced-data-protection-feature-in-the-uk/); [MacStories](https://www.macstories.net/linked/apple-to-eliminate-advanced-data-protection-for-icloud-accounts-in-the-uk/). In 2026 there are reports of a second, UK-only order and a new Apple complaint to the Investigatory Powers Tribunal in July 2026, with ADP still unavailable in the UK. These come from a single German source and are unconfirmed — [drweb.de](https://www.drweb.de/icloud-verschluesselung-apple-klage-grossbritannien/)
- **Storage pricing trend:** Google renamed AI Premium to AI Pro ($19.99/month) and raised its storage from 2TB to 5TB at no extra cost. AI Plus dropped to $4.99 with 400GB. AI Ultra costs $249.99/month with 30TB. New subscribers in 2026 get 50% off annual plans — [Android Authority](https://www.androidauthority.com/google-ai-pro-plan-5tb-3654227/); [Nasdaq](https://www.nasdaq.com/articles/google-one-cuts-2-tb-and-ai-pro-annual-plans-50-new-2026-subscribers); [BGR](https://www.bgr.com/2060318/google-one-cloud-storage-plans-new-year-discount/)
- **Vendor-outage trust hit:** WD's self-imposed 10-day My Cloud shutdown in 2023 made users' local data unreachable remotely — [APH Networks](https://aphnetworks.com/news/27032-after-10-days-western-digitals-my-cloud-finally-restored-following-hack)
- AI distrust (Pew 2025: 71% expect AI to make their personal information less secure) — see section 2 — [Pew](https://pewresearch.org/topic/internet-technology/emerging-technology/page/2)

### Inferences
- Marketing should lead with **"you can't be locked out of your own photos"** and **"no one can scan or train on them"**, not "cheaper than Google". At about $20/month for 5TB plus AI features, Big Tech storage is hard to beat on price per TB.
- Cost does win in one place: a one-time home box ($300–500 including disks) against cumulative cloud fees over 3–5 years for families with more than 2TB. This needs a clear TCO calculator.
- The UK ADP case shows that E2EE in a vendor cloud is a policy choice the vendor can lose. A box in the home with user-held keys is a stronger story, with the caveat that it is also subject to local law.

### Gaps
- Specific 2024–26 AI-training controversies (Adobe ToS June 2024, Meta EU AI training using public posts from 2025, Dropbox/OpenAI rumors, WeTransfer ToS July 2025) were not searched or verified; they are [UNVERIFIED-BACKGROUND] candidates to confirm.
- Whether iCloud prices rose in 2025–26 was not found.
- Recent (2024–26) Google lockout cases were not found.

## 4. Product gaps and business models

### Takeaway
No one ships a **phone-first, family-ready, single box** that replaces Photos, Drive, Docs and browser sync, includes **automatic off-site encrypted backup of the box**, offers **optional relay-based remote access that survives the vendor dying**, and can be set up by a non-technical user. Today's options split three ways: polished but single-purpose (Ente, Immich), broad but technical (Nextcloud, Umbrel, YunoHost, Cloudron), or proprietary and vendor-cloud-dependent NAS (Synology, WD).

### Cited Findings
- Immich's first planned paid product is **E2EE off-site backup of the self-hosted server**, which confirms that "who backs up the home box" is an acknowledged gap and a revenue line — [Immich blog](https://immich.app/blog/v2.0.0-release)
- Umbrel's selling points are plug-and-play hardware, browser-only setup and automatic updates — [Simplify jobs listing](https://simplify.jobs/c/Umbrel)
- Ente added a family plan and Library Sharing (Sep 2026), showing that family sharing is a competitive feature in demand — [Ente blog](https://ente.com/blog/)
- Lima showed the risk of the "device plus vendor relay" model: when the company died, remote access, sharing and new-device onboarding all broke — [Goodbye Lima](https://blog.separateconcerns.com/2019-02-15-goodbye-lima.html)
- Helm promised self-run gateways as a mitigation for shutdown, an early example of designing for vendor failure — [Dezeen](https://www.dezeen.com/2018/11/07/helm-personal-server-new-deal-design-data-security/amp/)
- Anytype raised Series A money specifically for **multi-user collaboration** on local-first data, which suggests that collaborative local-first documents were still unsolved in 2023 — [TechFlow](https://www.techflowpost.com/en-US/newsletter/29870)
- Container-based self-hosting (98% of surveyed self-hosters) remains a power-user workflow — [DreamHost/selfh.st](https://www.dreamhost.com/blog/self-hosting/)

### Inferences (gap list for an indie developer)
1. **One box, one app, everything:** a unified phone app for photos, files, docs, contacts/calendar and browser data instead of 6 separate self-hosted apps with separate logins. Nextcloud tries this but is widely seen as heavy (inference).
2. **Phone-first setup:** setup by QR code, with no terminal, Docker or port forwarding.
3. **Family sharing:** separate accounts and shared albums for each member, plus parental and "grandparent" UX.
4. **Off-site backup of the home box:** E2EE, ideally to a friend's box or a cheap S3-compatible bucket, with restore that actually gets tested. Immich is moving here, so it is a probable revenue line.
5. **Browser data sync (tabs, history, bookmarks, passwords) to your own server:** no mainstream self-hosted equivalent to Chrome or Firefox Sync exists. Firefox Sync's server can be self-hosted but is technical, and xBrowserSync was discontinued around 2023 [UNVERIFIED-BACKGROUND]. This is a real differentiator.
6. **Collaborative docs on your own server with local-first sync:** CRDT libraries (Yjs, Automerge) and engines (Zero, ElectricSQL, Jazz) make this possible, but no consumer product packages it.
7. **Vendor-death-proof remote access:** open, swappable relay or bring-your-own (Tailscale, WireGuard, Cloudflare Tunnel), stated as an explicit promise.
8. **Import from Big Tech:** one-click Google Takeout and iCloud import, which can lean on DMA/Data Act portability.

**Business models with evidence:**
- One-time hardware sale (Umbrel, about $399–429).
- Free OSS plus a paid E2EE off-site backup or relay subscription (Immich's plan; Tailscale-style relay).
- Consumer E2EE storage subscription with a family plan (Ente).
- Enterprise sovereignty licenses (Nextcloud, Inrupt).
- Patronage from a non-profit or individual (FUTO for Immich).
- Purely VC-funded consumer personal-server plays failed (Sandstorm, Lima, Helm, Urbit Foundation).
- [UNVERIFIED-BACKGROUND] Cloudron runs open-core and per-app licensing; FUTO also sold optional Immich "supporter licenses" ($25 per user, $100 per server) starting in 2024.

### Gaps
- No quantitative data was found on demand for specific gaps (browser sync, collaborative docs).
- Unit economics for relay subscriptions (bandwidth cost per user) were not researched.
- Pricing and adoption of Immich supporter licenses were not verified this session, because the immich.app fetch failed.
