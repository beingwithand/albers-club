# Consumer P2P Shared Storage/Backup: Economics, History, Consumer Products (as of Oct 2026)

Method note: about 25 web searches; direct page fetches failed (DNS errors on several hosts), so many citations rest on search-result snippets from the cited pages. Confidence is flagged where it matters. Items labeled [HISTORICAL] describe events before 2020.

## 1. History and fate of consumer P2P storage efforts

### Takeaway
Every consumer "trade your disk space" product either dropped the P2P component or shut down. The common causes were (a) technical: node churn and the bandwidth needed for repair, and unreliable home uptime, as the academic literature predicted (Blake and Rodrigues 2003); (b) business: acquirers (LaCie, Quantum, Vivint, Code42's own pivot) moved to enterprise or to centralized storage, which was cheaper to operate and support. The ideas that survived either went enterprise/centralized (Dropbox Magic Pocket, Resilio Connect) or reappeared as token-incentivized networks (Storj, Sia, Filecoin), and Tahoe-LAFS survived as open source.

### Cited Findings
**Wuala (LaCie) [HISTORICAL]**
- Storage trading (give up local free disk space in exchange for online quota) was removed in build 368. Wikipedia dates the discontinuation to 28 Sept 2011, and StorageNewsletter reported it on 6 Oct 2011 — [Wikipedia](https://en.wikipedia.org/wiki/Wuala); [StorageNewsletter](https://www.storagenewsletter.com/?p=114021)
- Reason reported by BetaNews: a switch from UDP to TCP networking "makes trading storage impossible for security reasons." Storage already earned stayed free for 12 months, then a "generous rebate" was offered — [BetaNews via search](https://betanews.com/topic/lacie/page/2) (secondary; Wuala never published a fuller rationale)
- The whole service shut in 2015, not 2017 as the assignment brief says: announced 17 Aug 2015, read-only from 30 Sep 2015, data deleted 15 Nov 2015. Users were pointed to Tresorit. TechMonitor said "no reason has been given" — [Wikipedia](https://en.wikipedia.org/wiki/Wuala); [TechCrunch](https://techcrunch.com/?p=1196480); [TechMonitor](https://techmonitor.ai/?p=102909)

**CrashPlan for Home (Code42) [HISTORICAL]**
- Code42 stopped new and renewed Home subscriptions on 22 Aug 2017. Service was shut off 23 Oct 2018. The stated reason was to focus solely on business and education. Home users were offered Small Business at 75% off for 12 months, or Carbonite — [Slashdot](https://tech.slashdot.org/story/17/08/22/1633220/code42-says-crashplan-backup-service-will-discontinue-all-personal-backup-plans); [Thurrott](https://www.thurrott.com/cloud/133185/crashplan-shutting-consumer-backup-service); [mjtsai](https://mjtsai.com/blog/2017/08/22/crashplan-discontinues-consumer-backups)
- The free "back up to a friend's computer" feature (encrypted, P2P to a friend's disk) went away with Home. UrBackup was suggested as an open-source replacement — [SLR Lounge](https://www.slrlounge.com/crashplan-halts-their-home-cloud-backup-service-what-you-need-to-know/); [PeerSpot](https://www.peerspot.com/questions/what-alternative-are-you-going-to-use-now-that-the-home-version-of-crashplan-is-being-discontinued)

**Space Monkey [HISTORICAL]**
- Vivint acquired it in Sept 2014. Google Ventures was an investor and exited. By 2024 Space Monkey had no public presence, but its technology lives on in Vivint Smart Drive (home camera video storage and the "Playback" feature). In 2019, former Vivint insiders spun the technology out as CrowdStorage, majority-owned by Vivint — [Wikipedia](https://en.wikipedia.org/wiki/Space_Monkey_(company)); [Global Venturing](https://globalventuring.com/blog/2014/10/06/google-exits-as-vivint-captures-space-monkey/)

**Symform [HISTORICAL]**
- Quantum acquired it in Aug 2014. At that point it had about 45,000 individual and SMB users in 170 countries. Quantum discontinued it in mid-2016 (23 months later) to "concentrate on enterprise." It was read-only in July 2016 and files were deleted after 31 July 2016 — [The Register](https://www.theregister.com/2016/06/17/quantum_file_sync_and_share_sinks/); [StorageNewsletter](https://www.storagenewsletter.com/?p=164124)

**Bitcasa [HISTORICAL]**
- Bitcasa ended its consumer Bitcasa Drive in 2016 ("to focus on its platform business") and deleted accounts on 20 May 2016. The company wound down entirely in Jan 2017 — [PCWorld](https://www.pcworld.com/article/414575/cloud-storage-pioneer-bitcasa-is-killing-its-cloud-storage.html); [Fortune](https://www.fortune.com/2017/01/06/bitcasa-calls-it-quits/); [Channel Futures](https://channelfutures.com/cloud/cloud-storage-firm-bitcasa-shuts-down). (Note: Bitcasa was centralized "infinite" cloud storage with client-side convergent encryption, not P2P.)

**AllMyData / Tahoe-LAFS [HISTORICAL]**
- Tahoe-LAFS began in 2006 as the back end for the personal-backup company Allmydata. Allmydata stopped funding Tahoe R&D in early 2009 and closed around 2009. The code lives on as free software — [Wikipedia](https://en.wikipedia.org/wiki/Tahoe-LAFS); [LWN](https://lwn.net/Articles/345179/)
- A Tahoe developer wrote in 2011 that the team had worked on Mojo Nation, Mnet and Allmydata, "which each attempted to support something like that [P2P storage trading] and failed." The thread is titled "'BitTorrent for storage' is a bad idea" — [tahoe-dev list](https://www.tahoe-lafs.org/pipermail/tahoe-dev/2011-February/006150.html) (snippet only; the page could not be fetched)

**Academic lineage [HISTORICAL]**
- Blake and Rodrigues, HotOS 2003, "High Availability, Scalable Storage, Dynamic Peer Networks: Pick Two." Using Gnutella churn data, they found that when redundancy, data scale and churn are all high, "the requisite cross-system bandwidth is beyond reasonable expectations." Delayed failure response, admission control and load-shifting do not change this — [USENIX](https://www.usenix.org/events/hotos03/tech/full_papers/blake/blake_html/index.html); [MIT PMG](https://pmg.csail.mit.edu/iris/blake03high-abstract.html)
- Storj's counter-argument: bandwidth is much less scarce than in 2003, and Reed-Solomon erasure coding lets a network be available, scalable and dynamic at once — [Storj blog](https://www.storj.io/blog/four-advancements-that-led-to-decentralized-cloud-storage) (vendor opinion)
- Pastiche (Cox et al., OSDI 2002): administration-free backup in spare disk of untrusted, unreliable peers. It cuts redundancy by pairing peers with similar data — [Microsoft Research](https://www.microsoft.com/en-us/research/?p=184194)
- Samsara (SOSP 2003): enforces fairness without trusted third parties, money or certified identities. It uses "storage claims," placeholders that a requesting peer must hold in return — [SOSP paper](https://www.cs.rochester.edu/meetings/sosp2003/papers/p135-cox.pdf)
- Friendstore (ACM TOS 2012): backs up only to trusted friends and colleagues. This avoids defending against malicious nodes, at the price of imperfect storage utilization — [Crossref](https://api.crossref.org/works/10.1145%2F2339118.2339119)
- PeerStore (P2P 2004): symmetric pairwise storage trading — [paper](https://www.ida.liu.se/conferences/p2p/p2p2004/papers/landers.pdf)
- An economics paper asks whether imposed fairness in a P2P backup system outperforms a "revenue-driven monopoly" — [HAL](https://hal.archives-ouvertes.fr/hal-02164426)

**BitTorrent Sync → Resilio [HISTORICAL]**
- BitTorrent spun Sync out into Resilio (CEO Eric Klinker) and renamed it Resilio Sync 2.4 on 4 Nov 2016. The business line became Resilio Connect, enterprise-focused. A free "Sync Home" edition existed in 2017 — [Resilio blog](https://www.resilio.com/blog/bittorrent-sync-now-resilio-sync); [Fox Business](https://foxbusiness.com/features/bittorrent-sync-now-a-separate-enterprise-focused-biz); [Impress Watch](https://forest.watch.impress.co.jp/docs/news/1059334.html)

**Dropbox Magic Pocket [HISTORICAL]**
- In 2016 Dropbox announced it had moved about 90% of user storage off AWS S3 onto its own exabyte-scale infrastructure (more than 500 PB at the time). It cited cost, performance and control — [InfoQ](https://www.infoq.com/news/2016/03/Dropbox-AWS/); [The Register](https://www.theregister.com/2016/03/14/dropbox_moves_data_from_aws); [Computerworld](https://www.computerworld.com/article/1660162/dropbox-quits-amazon-aws-s3-itbwcw.html)
- A secondary source citing the 2018 S-1 reports $74.6M cumulative savings over the two years after migration — [Level Up / gitconnected](https://levelup.gitconnected.com/how-did-magic-pocket-help-dropbox-save-millions-2f744c643194) (secondary; "90%" refers to the share of data moved, not cost savings)

### Inferences
- Pattern: P2P was used as a customer-acquisition or cost gimmick. Once a company scaled or was acquired, support load, security and predictable SLAs favored centralized storage, and acquirers (LaCie, Quantum, Vivint) pivoted to enterprise or captive uses. Only Space Monkey's tech survived, inside a captive appliance fleet (Vivint), where the operator controls the hardware.
- Dropbox shows the opposite pole: at scale, owning dense centralized hardware beats renting. That makes stranger-sourced home disks even less competitive on cost per reliable TB.
- The academic designs split into two answers to the incentive problem: accounting/fairness among strangers (Samsara, PeerStore) and social trust (Friendstore, CrashPlan-to-friends). The social-trust model is the one that still ships in consumer products today (see section 3).

### Gaps
- OceanStore (Berkeley, about 2000) was not researched in this pass. It was a research prototype (Pond) with no commercial product, based on training knowledge only.
- No primary source found for Wuala's internal rationale beyond the UDP→TCP explanation.
- No usage or retention data found for CrashPlan's friend-backup feature, or for how many Wuala users actually traded storage.

## 2. Economics today (2025–2026)

### Takeaway
Raw disk is cheap, but its price rose sharply in late 2025–2026 because AI and hyperscaler demand sold out HDD supply. Even so, decentralized networks pay home operators only about $1.50/TB-month for storage (Storj), which barely covers electricity for a lightly filled node. Retail decentralized storage ($2–5/TB-mo) undercuts B2/Wasabi (about $7–8) and R2 ($15), but the DePIN sector as a whole earned only about $72M of on-chain revenue in 2025 against about $10B market cap. Storage networks like Filecoin show near-zero on-chain revenue relative to emissions.

### Cited Findings
**Hardware supply and prices**
- Western Digital's CEO said on the earnings call (Feb 2026): "we're pretty much sold out for calendar 2026." Two top customers reportedly signed agreements covering 2027–2028. Seagate is reportedly sold out too. Cloud customers take most HDD revenue — [HotHardware](https://hothardware.com/news/wd-out-of-hdd-storage-production-for-2026); [PCWorld](https://www.pcworld.com/article/3063473/western-digital-is-out-of-hard-drives-because-ai-data-centers.html); [Touchpoint](https://www.touchpoint.com.au/resources/insights/hdd-shortage-2026); [Gigazine](https://gigazine.net/gsc_news/en/20260216-western-digital-2026-hdd-capacity-runs-out)
- Price rise estimates conflict. Some trade press say about 46–50% in roughly four months (Sep 2025–Jan 2026), while DigiTimes data show contract prices up only about 4% QoQ in Q4 2025. Nearline lead times are reported above 52 weeks. DRAM-cache shortages add pressure — [Club386](https://www.club386.com/hard-drive-prices/); [Touchpoint](https://www.touchpoint.com.au/resources/insights/hdd-shortage-2026) (treat the percentages cautiously)
- Backblaze 2025 Drive Stats: 344,196 drives, 1.36% AFR (down from 1.55% in 2024). 14–16TB drives make up 52% of the fleet and 20TB+ about 23%. Cost per GB is falling and small enterprise drives are harder to source — [BusinessWire, Feb 2026](https://www.businesswire.com/news/home/20260212236512/en/Backblaze-Publishes-2025-Drive-Stats-Report-13-Years-of-Data-Show-a-Growing-Healthier-Drive-Fleet)

**Bandwidth and caps**
- Comcast dropped data caps on its four new national Xfinity plans (300M/500M/1G/2G) in June 2025, after losing 199k broadband subscribers in Q1 2025. Legacy plans keep their terms until customers repackage — [Cord Cutters News](https://cordcuttersnews.com/comcast-removes-data-caps-on-its-new-internet-packages-adds-a-five-year-price-guarantee-starting-at-55-month/); [MediaPost](https://mediapost.com/publications/article/407031/comcasts-new-plans-scrap-controversial-data-caps.html); [Android Authority](https://androidauthority.com/comcast-xfinity-new-internet-plans-3571524)
- Upload remains the bottleneck. Starlink's 2025 US median upload was 16.91 Mbps, below the FCC 20 Mbps standard. The US ranks last of 22 markets for uplink share of mobile throughput (5.1%). Cable uploads are around 30–40 Mbps per an unofficial source — [Telecompetitor/Ookla](https://www.telecompetitor.com/starlink-median-u-s-speeds-still-short-of-federal-minimums-ookla-report/); [Telecompetitor/Ookla 5G](https://www.telecompetitor.com/is-5g-ready-for-ai-ookla-report/); [POTs and PANs](https://potsandpansbyccg.com/tag/upload-speeds/)

**Node operator payouts**
- Storj: $1.50/TB-month stored, $20/TB egress (historical), $10/TB repair/audit egress. Storj cut egress and repair payouts in 2023 (effective Dec 1 2023 on all satellites) and said it would hold storage at $1.50 "for the foreseeable future." No 2025 change was found — [Storj forum: Dec 2023 changes](https://forum.storj.io/t/announcement-changes-to-node-payout-rates-as-of-december-1st-2023-closed/24125); [Storj forum: payout update](https://forum.storj.io/t/update-on-storage-node-payouts/22190); [Storj forum: economic model thread](https://forum.storj.io/t/lets-talk-about-the-elephant-in-the-room-the-storj-economic-model-node-operator-payout-model/20127)
- Operator-reported realized earnings are about $2.9–4.8 per TB used per month, including egress. These are undated forum posts — [Storj forum](https://forum.storj.io/t/lets-talk-about-the-elephant-in-the-room-the-storj-economic-model-node-operator-payout-model/20127). Operators also openly debate whether the network can be profitable — [Storj forum 2025–26 thread](https://forum.storj.io/t/helping-the-network-become-profitable-what-can-operators-contribute-while-staying-viable-calculator-inside/32104?page=3)
- Sia: hosts set their own prices and post collateral. Docs say network pricing "usually works out to around $2 per TB per month." Filebase resold Sia storage at $5/TB — [Sia docs](https://docs.sia.tech/provide-storage/about-hosting-on-sia); [Autoize](https://autoize.com/filebase-and-sia-decentralized-storage/) (undated)
- Filecoin: Messari Q1 2025 reported network fees down 65% QoQ to $457K, 1,300 PiB active storage, and about 30% utilization. Q3 2025: about 1,110 PiB active data, 35.2M deals, daily new deals down 19% QoQ (3.4 to 2.8 PiB). FilecoinTLDR: "on-chain revenue is near zero" because payments are off-chain — [Tron Weekly/Messari](https://www.tronweekly.com/messari-filecoins-bold-shift-to-enterprise/); [MEXC/Messari](https://www.mexc.com/news/167561); [FilecoinTLDR](https://filecointldr.io/blog/state-of-filecoin-2025)

**Retail price comparison (per TB-month)**
- Storj about $4 storage, plus a $5/month minimum from 1 Jul 2025. Backblaze B2 at $6.95 (raised from $6; $5→$6 happened in Oct 2023), with free egress up to 3x storage. Wasabi at $6.99, reportedly $7.99 from 1 Jul 2026, with a 90-day minimum. Cloudflare R2 at $15 with free egress — [agentdeals](https://agentdeals.dev/storage-comparison-2026); [Backblaze 2023](https://backblaze.com/blog/2023-product-announcement); [Backblaze pricing update](https://backblaze.com/blog/backblaze-pricing-and-product-updates/); [tech-insider](https://tech-insider.org/backblaze-b2-vs-wasabi-vs-s3-2026/) (the 2026 Wasabi and B2 claims are unverified against vendor pages)

**DePIN sector**
- Messari and Escape Velocity "State of DePIN 2025": about $10B circulating market cap, about $72M on-chain revenue in 2025, possibly $100M+ in 2026. The 2018–2022 cohort of tokens is down 94–99% from all-time highs. Leading revenue networks trade at 10–25x revenue, compared with more than 1,000x in 2021. The report frames the sector as moving from subsidy/inflation-driven growth to usage revenue — [Cointelegraph](https://cointelegraph.com/news/depin-revenues-grow-despite-token-losses); [Decrypt](https://decrypt.co/356349/depin-tokens-lag-revenues-rise-fundamentals); [Forklog](https://forklog.com/en/news/depin-after-the-boom-revenue-is-king-as-energy-and-ai-set-the-pace); [BlockEden Mar 2026](https://blockeden.xyz/blog/2026/03/21/depin-march-2026-reality-check-650-projects-19b-market-cap-revenue/)
- Helium as the analogy: Messari put Helium Mobile at about $18.3M annualized revenue in Q3 2025 (Sept about $1.5M/month), and about $20M by Nov 2025. Since Aug 2025, 100% of subscriber revenue goes to HNT buy-and-burn, and annual emissions were halved from 15M to 7.5M HNT. Advocacy sources claim burns now exceed emissions (unverified). Subscriber figures run from about 311k (Q3 2025) to more than 600k (Dec 2025), with many free users — [MEXC/Messari](https://www.mexc.com/news/163503); [Sarson Funds](https://sarsonfunds.com/depins-leading-edge-why-heliums-growth-metrics-demand-attention/); [BlockEden](https://blockeden.xyz/blog/2026/02/26/helium-burn-mint-equilibrium-depin-wireless/)

### Inferences
- Unit economics for a home node (rough arithmetic, not sourced): an always-on box drawing 10–30W uses about 7–22 kWh/month, which costs about $1–4/month at $0.15/kWh. At $1.50/TB-month, a node holding fewer than about 2 TB of paid data barely covers power, before disk depreciation. Storage DePIN therefore only works for operators with already-sunk, already-on hardware such as a NAS or spare drives. This is the same "spare capacity" premise Wuala and Pastiche relied on.
- With HDDs sold out and up to about 46% more expensive, idle consumer disk becomes slightly more valuable, which strengthens the "use what you already own" pitch. But hyperscalers locking in 2027–28 supply widens their cost advantage at scale.
- Removing data caps (Comcast 2025) eases one historic barrier. Upload speeds of about 17–40 Mbps make initial seeding of multi-TB backups take days to weeks (1 TB at 20 Mbps is about 4.6 days). That cost falls on users of "backup to a friend" just as it did in 2011.
- Decentralized retail prices ($2–5) are lower mainly because of thin operator payouts plus token subsidies. The DePIN ratio of $72M revenue to $10B market cap shows that emissions, not customers, still fund most supply.

### Gaps
- No verified 2026 consumer $/TB retail figure for HDDs or SSDs. The SSD price trajectory in 2025–26 (NAND tightness) was not quantified.
- No primary Messari figures for storage-sector emissions versus revenue (Filecoin FIL emissions in USD, Storj token treasury drawdown).
- No 2026 Storj payout change found. Arweave/AR.IO was not covered.
- Hetzner Storage Box/Object Storage pricing and AWS S3 Standard (about $23/TB-mo list, from training knowledge) were not verified this pass.
- No national Ookla fixed-broadband median upload for 2025 found.

## 3. Consumer-facing shared storage/backup products and demand signals (2025–2026)

### Takeaway
No mainstream consumer product in 2026 does "trade disk with strangers." What survives is (a) trusted-peer backup: Synology Hyper Backup Vault to a friend's NAS, the Nextcloud Backup app, and Syncthing/Resilio/UrBackup-style self-hosting; (b) centralized E2EE clouds (Internxt, Filen, Ente, Peergos, Tresorit) that sell privacy rather than P2P; and (c) family-sharing tiers from Apple and Google. On demand, iCloud's US tiers appear unchanged in 2026, while Google One raised prices in several emerging markets (July 2026). Consumer cloud keeps growing toward large photo/video tiers (iCloud's 6TB and 12TB plans).

### Cited Findings
- **Synology Hyper Backup Vault**: the receiving package that lets another Synology run Hyper Backup jobs into this NAS. This is the de facto "backup to a friend's NAS." It needs ports or a VPN, a dedicated user, and client-side encryption (a lost key means lost data). The initial seed is slow over home upload — [WunderTech](https://www.wundertech.net/how-to-backup-a-synology-nas-to-a-remote-synology-nas); [Marius Hosting](https://mariushosting.com/synology-hyper-backup-vs-hyper-backup-vault/); [Blackvoid](https://www.blackvoid.club/synology-101-hyper-backup-to-a-remote-synology-nas/)
- **UGREEN**: no Hyper Backup Vault equivalent found. Community workarounds use rsync or Docker (Duplicati, Restic, Rclone) — [NAScompares forum](https://ask.nascompares.com/showthread.php?tid=11998); [StarryHope](https://www.starryhope.com/nas/ugreen-vs-synology/)
- **Nextcloud Backup app**: P2P backup to "the Nextcloud server of a friend or family member," compressed, encrypted and incremental — [Techzine](https://www.techzine.eu/news/data-management/67795/nextcloud-introduces-peer-to-peer-backup-app-for-private-instances)
- **Older buddy-backup apps** (BuddyBackup, Cucku, LeanOnMe) show the long tail of friend-backup attempts. Their dates are unclear and none appear active — [AlternativeTo](https://alternativeto.net/software/buddybackup/); [TechCrunch](https://techcrunch.com/?p=20543)
- **Internxt**: zero-knowledge E2EE cloud sold heavily through lifetime deals (2TB/5TB/20TB). Reviewers cite slow uploads and no virtual-drive mapping. It is centralized E2EE today, though it began with a P2P/X Cloud story (training knowledge, unverified) — [StackSocial listing](https://shop.macworld.com/sales/internxt-cloud-storage-lifetime-subscription-2tb-plan)
- **Backblaze Computer Backup** (centralized, unlimited): $99/year, or $189 for two years, with one-year version history. Promotions as low as $69.30 (Nov 2025) — [Backblaze](https://www.backblaze.com/cloud-backup/business/landing/ad/use-cases/branded-cloudbackup-v1); [Slickdeals](https://slickdeals.net/f/18898882-1-year-backblaze-unlimited-online-personal-backup-subscription-69-30); [Toolradar](https://toolradar.com/tools/backblaze/pricing)
- **Space Monkey's legacy**: Vivint Smart Drive, a captive appliance P2P mesh for camera video — [Wikipedia](https://en.wikipedia.org/wiki/Space_Monkey_(company))
- **Google One**: price increases from 27 Jul 2026 in Algeria, Egypt, Nigeria, Pakistan and Turkey (Nigeria 100GB up 55.3%). No US change was found — [Google support](https://support.google.com/googleone/answer/17251824); [Legit.ng](https://www.legit.ng/business-economy/technology/1724223-google-announces-5526-subscription-price-nigerians/)
- **iCloud+ US** (third-party lists): 50GB $0.99, 200GB $2.99, 2TB $9.99, 6TB $29.99, 12TB $59.99 per month. No 2026 increase found — [fdaytalk](https://www.fdaytalk.com/apple-icloud-pricing/)

### Inferences
- The consumer niche that remains viable is trusted, symmetric backup between owned devices (NAS-to-NAS, or between family members). It avoids the stranger-incentive problem Friendstore identified but inherits the seeding-bandwidth and "friend's NAS is offline" problems. Vendors offer it as a feature to sell hardware, not as a business.
- At 12TB for $59.99 a month (about $5/TB-mo), iCloud pricing sits right at the B2/Wasabi wholesale tier. This puts a ceiling on what a P2P consumer service could charge, and it suggests mesh storage among family devices could compete on price only if its operating costs are near zero.
- Rising HDD prices plus Google's emerging-market increases point to modest upward price pressure. That improves the relative appeal of reusing idle disks, but no consumer startup capitalizing on it was found.

### Gaps
- No credible 2025–2026 startup doing consumer personal-device mesh storage was found (searched generically). Keet (Holepunch) file sharing, Peergos, Filen, Ente, Duplicati/Kopia P2P targets, and Syncthing-as-backup were not individually verified this pass.
- No quantified per-person data growth or photo/video storage growth figures found (e.g., IDC, Google Photos stats).
- Apple/Google family-sharing details were not verified, nor whether Google One AI Premium tiers changed storage bundling in 2025–26.
- Whether Resilio Sync Home is still sold in 2026 is unverified.
