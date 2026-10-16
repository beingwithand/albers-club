# Decentralized / Peer-to-Peer Storage Networks — State of the Art (as of 16 Oct 2026)

Method note: 16 searches/fetches. WebFetch failed with DNS errors on every primary domain I tried (sia.tech, arxiv.org, filecoin.io, ipshipyard.com, filecointldr.io), so most figures below come from search-result summaries of those pages, not full-page reads. Treat any number not marked "primary" as needing a check against the original. Where I list items under Gaps marked "background knowledge", they come from pre-2026 general knowledge and were NOT checked in this session. Do not cite them as verified.

## Per-network status: architecture, scale, real usage, pricing, durability, maturity, 2025-2026 developments

### Takeaway
The sector split in 2025-2026. Filecoin moved from cheap cold-storage capacity toward paid "warm" storage (Filecoin Onchain Cloud, mainnet in Q1 2026). Its actual paid revenue is still tiny: about $59K annualized run-rate by Aug 2026. Walrus is the fastest-growing newcomer, at roughly 0.45–0.69 PB stored on about 95 nodes. Sia rebuilt its software (renterd/hostd/walletd) and launched a consumer app. Autonomi launched in 2025 and shipped 2.0 in April 2026. The biggest structural shock was to IPFS: Protocol Labs stopped funding Shipyard, the main maintainers of Kubo, Helia, Boxo and the ipfs.io gateways, effective 30 Sep 2026.

### Cited Findings

**Filecoin (+ Filecoin Onchain Cloud / FVM)**
- Raw capacity vs stored data is disputed across secondary sources:
  - One source: about 2.1 EiB of data secured on 7.6 EiB raw capacity — [securities.io / adipek summary via search](https://www.securities.io/decentralized-storage-filecoin-arweave-storj-comparison/).
  - Another source: "over 22 EiB across 60+ countries, early 2026", which looks like an outdated peak-era figure.
  - A third source: 1.8+ EiB — [coinlaw.io](https://coinlaw.io/decentralized-storage-statistics/).
  - These are unreconciled.
- Messari figures, cited secondhand (I did not verify them against Messari):
  - Q2 2025: about 1,100 PiB of active-deal data, down from 1,300 PiB in Q1 2025. Daily new deals were about 3.4–3.5 PiB — [coinstats.app](https://coinstats.app/ai/a/investment-analysis-filecoin).
  - Q3 2025: 1,110 PiB active data, with utilization rising from 32% to 36% — [OKX insight](https://www.okx.com/en-us/orbit/insight/88439256190336).
  - Messari's "State of Filecoin Q3 2025" was published 13 Nov 2025 — [fil.org](https://fil.org/blog/fresh-from-ff-december-2025).
- Filecoin Onchain Cloud (FOC) is live on mainnet. Filecoin's own launch post reported 49.41 TiB stored across 478 active datasets and 81 payer wallets at launch — [Filecoin blog (primary, via search summary)](https://www.filecoin.io/blog/filecoin-onchain-cloud-is-live-on-mainnet).
  - The launch date conflicts across sources: "Q1 2026" ([Filecoin TL;DR 2026 overview](https://wp.filecointldr.io/article/filecoin-network-2026-overview-update/)), Jan 2026 ([bex.co](https://bex.co/blog/2026/02/26/filecoin-onchain-cloud-transformation)), 26 Mar 2026 ([coinstats](https://coinstats.app/ai/a/investment-analysis-filecoin)), and an "April 11, 2026 rollout" ([laikalabs](https://laikalabs.ai/news/filecoin-onchain-cloud-launch-ai-storage-demand)).
- Filecoin Pay's annualized run-rate grew from $663 in January 2026 to $59,327 at the end of August 2026 — [Filecoin TL;DR 2026 overview (Foundation-sourced)](https://wp.filecointldr.io/article/filecoin-network-2026-overview-update/). This is the clearest independent-ish signal of actual paid demand, and it is very small relative to the exabyte-scale capacity.
- The 2026 network strategy prioritizes paid, onchain deals and makes FOC the default payment layer — [Filecoin 2026 strategy](https://www.filecoin.io/blog/the-2026-filecoin-network-strategy) / [fil.org mirror](https://fil.org/blog/the-2026-filecoin-network-strategy).
- With FVM maturing, "smart storage" (programmable storage) is promoted — [securities.io](https://www.securities.io/decentralized-storage-filecoin-arweave-storj-comparison/).

**IPFS (Kubo, Helia, Protocol Labs)**
- Protocol Labs declined to renew funding for Shipyard, the independent collective that maintained IPFS implementations and infrastructure. Shipyard announced in Aug 2026 that its final IPFS day would be 30 Sep 2026 — [Shipyard blog](https://ipshipyard.com/blog/2026-the-end-of-ipfs-at-shipyard/); [Cointelegraph](https://cointelegraph.com/news/shipyard-winds-down-ipfs-protocol-labs-funding); [CryptoBriefing](https://cryptobriefing.com/shipyard-ipfs-protocol-labs-funding-ends/).
- Projects losing dedicated maintainers: Kubo, Helia, Boxo, Rainbow, IPFS Desktop and IPFS Companion. Public infrastructure is also affected (ipfs.io, dweb.link, bootstrap nodes), and Protocol Labs, as owner of the domains, decides its future — [cryptorank](https://cryptorank.io/news/feed/fa7f4-shipyard-ipfs-operations-halt-september-30); [tokenpost](https://www.tokenpost.com/news/technology/25707).
- Molly Mackinlay (Protocol Labs) said IPFS moves to "lighter-weight stewardship" via IPFS Foundation grants to individual maintainers. The protocol is not shutting down, but the implementations most apps use enter "uncertain stewardship" — [Cointelegraph](https://cointelegraph.com/news/shipyard-winds-down-ipfs-protocol-labs-funding).
- Security side-effect: Netcraft reports IPFS phishing "entering a new phase" as Shipyard winds down. Public gateways have long been abused for phishing hosting — [Netcraft](https://www.netcraft.com/blog/as-shipyard-winds-down-ipfs-phishing-enters-a-new-phase).
- Discussion: [Hacker News "IPFS Maintainers Winding Down"](https://news.ycombinator.com/item?id=49421489).

**Walrus (Sui / Mysten Labs)**
- Academic paper (Danezis et al.), v4 updated Aug 2026 (primary but authored by Mysten):
  - Mainnet has been live since March 2025 and had "secured 686 TB of data by July 2026".
  - Mainnet comprises 95 storage nodes in 17 countries (observed 29 Jul 2026).
  - Testnet benchmarks show write latency under 20 s for blobs up to 135 MB, with latencies "orders of magnitude smaller" than Filecoin/Arweave thanks to separating consensus (Sui) from storage.
  - These are self-reported benchmarks — [arXiv 2505.05370](https://arxiv.org/pdf/2505.05370).
- BlockEden reports 450 TB stored at the one-year anniversary (about Mar 2026), 4.12 PB total capacity with about 39% used, and 100 nodes in 19 countries. It positions Walrus as the "default memory layer for AI agents". This is a secondary, promotional-leaning source — [BlockEden, Apr 2026](https://blockeden.xyz/blog/2026/04/18/walrus-protocol-ai-agent-memory-layer-sui-decentralized-storage/).
- Mid-Oct 2026: 94 storage nodes held all 1,000 shards. About 1B WAL is staked, around 38.3% of circulating supply (search-result summary). Blobs are Sui objects that smart contracts can own and renew — [Phemex academy](https://phemex.com/academy/walrus-wal-decentralized-storage-token-sui).
- Oct 2026: DATA Network migrates to Sui, and Walrus becomes the default storage layer for DATA Foundation apps (AI training-data supply chain) — [The Daily Hodl, 11 Oct 2026](https://dailyhodl.com/2026/10/11/data-network-joins-sui-and-walrus-to-scale-the-supply-chain-for-ai-training-data/).
- Early Oct 2026: Walrus Foundation launched "Walrus Console", a managed service for files and AI-agent memory (search summary). There is also a partnership with Veea for edge storage — [Barchart](https://www.barchart.com/story/news/33617706/walrus-and-veea-inc-announce-strategic-partnership-to-unlock-high-performance-edge-utility-for-decentralized-data-storage).
- Walrus raised about $140M (2025) — [bex.co](https://bex.co/blog/2026/01/10/walrus-protocol-sui-decentralized-storage-wars).

**Storj**
- Corporate history:
  - Acquired Valdi (GPU cloud, "over 16,000 GPUs") on 9 Jul 2024. Some 2026 articles wrongly say July 2025 — [PR Newswire](https://www.prnewswire.com/news-releases/storj-acquires-leading-ai-compute-provider-valdi-302192158.html); [TechTarget](https://www.techtarget.com/searchstorage/news/366593036/Storj-buys-Valdi-for-cloud-compute-to-bolster-storage-offers).
  - Acquired PetaGene (cunoFS) on 8 Oct 2024 — [Storj newsroom](https://www.prnewswire.com/news/storj/).
  - Colby Winegar became CEO in Oct 2024.
- Revenue: the "sevenfold" revenue growth headline refers to 2024 — [Storj newsroom](https://www.prnewswire.com/news/storj/). There is also a claim of 7x ARR and +25% paid data stored between Jan and Apr 2025 — [securities.io](https://www.securities.io/decentralized-storage-filecoin-arweave-storj-comparison/).
- A tracker claims Storj was acquired by Inveniam IO on 22 Oct 2025 — [Tracxn](https://tracxn.com/d/companies/storj/__-VbyDchg8Tjhuk2zNwc2F7Quv63DupRCpazFhZPoZcw). UNVERIFIED; I found it only in weak sources.
- Pricing cited at $0.004/GB-month ($4/TB-month) as of early 2025 — [securities.io](https://www.securities.io/decentralized-storage-filecoin-arweave-storj-comparison/). The 2026 price is not confirmed.
- One low-reliability 2026 article claims 20,000+ storage nodes — [Bitget news](https://www.bitget.com/news/detail/12560605363588).

**Sia (renterd / hostd / walletd)**
- After the v2 hardfork, the monolithic siad was replaced by renterd (renters), hostd (hosts) and walletd (wallets). The RHP4 protocol enables uploads and downloads directly in web browsers — [Sia Foundation GitHub](https://github.com/siafoundation); [State of Sia, Mar 2026](https://sia.tech/blog/the-state-of-sia-march-2026).
- 2026 releases:
  - renterd v2.9.0 (Feb 2026, instant-sync fixes) — [State of Sia, Feb 2026](https://sia.tech/blog/the-state-of-sia-february-2026).
  - hostd v2.8.0 (Apr 2026, contract-renewal reliability) — [State of Sia, Apr 2026](https://sia.tech/blog/the-state-of-sia-april-2026).
  - hostd v2.10.0 added corrupt-sector detection on reads and disk-write-failure alerts; renterd v2.9.2 added gouging checks — [State of Sia, Jun 2026](https://sia.tech/blog/the-state-of-sia-june-2026).
  - hostd v2.7.0 added experimental consensus pruning.
- The consumer "Sia Storage" app launched with 50 GB free and no crypto knowledge required. "indexd" (an indexing/search service) is in development with no date — search summary of [Sia blog](https://sia.tech/blog/the-state-of-sia-june-2026) / [CoinMarketCap AI summary](https://coinmarketcap.com/cmc-ai/siacoin/latest-updates/).
- Messari published a "State of Sia Q2 2025" report (contents not retrieved) — [Messari](https://messari.io/report/state-of-sia-q2-2025).

**Arweave + AO**
- The model is a one-time upfront payment, partly funding a storage Endowment, aiming for "permanent" storage — [securities.io](https://www.securities.io/decentralized-storage-filecoin-arweave-storj-comparison/).
- AO mainnet launched 8 Feb 2025 (per an explainer). The permaweb guide describes a move from "Legacynet" to a mainnet powered by AO-Core plus HyperBEAM (an Erlang reference implementation) — [HyperBEAM GitHub](https://github.com/permaweb/hyperBEAM); [Permaweb Journal AO 101](https://permaweb-journal.arweave.net/reference/ao.html).
- A Mar 2026 developer PR migrates off the "dead AO legacynet" onto self-hosted HyperBEAM — [anyone-protocol PR #186](https://github.com/anyone-protocol/smart-contracts/pull/186).
- Since Feb 2026, uploads through the primary arweave.app gateway are routed through HyperBEAM-based bundlers (secondary summary) — [CoinMarketCap AI](https://coinmarketcap.com/cmc-ai/arweave/latest-updates/).

**Autonomi (ex-MaidSafe / SAFE Network, token ANT)**
- Launched 11 Feb 2025. Autonomi 2.0 went live 7 Apr 2026. Emissions were paused on 20 Jan 2026 while the economic model was finalized. Circulating supply was about 300M ANT (Apr 2026) — [CoinMarketCap](https://coinmarketcap.com/currencies/autonomi/).
- Early-network snapshot (Jan 2025, company post): over 175K nodes, 5.35 PiB raw capacity, 130 TB stored. Node counts are cheap to inflate (many nodes per machine) — [Autonomi on X](https://x.com/WithAutonomi/status/1880323135209169331).
- Independent review (May 2026) — [Rex Bytes](https://rexbytes.com/2026/05/06/autonomi-network-review/).
- Name collision: Autonomys (AI3 token, Subspace-based, Nov 2024 mainnet, "2,000+ nodes, 140+ PiB pledged") is a different project — [Messari](https://messari.io/report/state-of-autonomys-network-q1-2025).

**Swarm (Ethereum / Bee)**
- Bee 2.0 was announced in 2024 — [Swarm blog](https://blog.ethswarm.org/foundation/2024/announcing-bee-2.0-pioneering-next-gen-decentralised-storage/).
- Bee v2.8.3 is a security release scheduled for 15 Oct 2026; it adds the ability to pause redistribution without a restart.
- The May 2026 update moves toward a published tokenomics roadmap (withdrawable stake, pullsync, rebalancing, bandwidth incentives, multi-chain testnets) — [Swarm May 2026 dev update](https://blog.ethswarm.org/foundation/2026/monthly-development-update-may-2026/); [dev updates index](https://blog.ethswarm.org/c/development-updates).
- The storage-incentives contracts repo was updated 3 Sep 2026 — [GitHub](https://github.com/ethersphere/storage-incentives).

**Codex → Logos Storage**
- Codex was folded into the unified "Logos" identity (Nov 2025 press release). Logos targets a public testnet in 2026 and mainnet in 2027 — [Decrypt/Chainwire](https://decrypt.co/349397/logos-unifies-under-one-identity-to-deliver-a-private-tech-stack-to-revitalise-civil-society).
- The team paused its testnet to redesign protocol parts (undated post) — [Logos Storage LinkedIn](https://www.linkedin.com/company/codexstorage).
- Design: erasure coding, lazy repair, ZK remote auditing, and incentives. Earlier targets (MVP testnet early 2024, mainnet 2025) have slipped — [free.technology](https://free.technology/codex); [Logos Storage design notes (HackMD)](https://hackmd.io/hC4RAzJ1TBiyuek8nqAP_A).

**BNB Greenfield, Crust, Jackal, 0G**
- Greenfield is still listed as active (Sep 2026 directory). Its price is about 0.00004 BNB/GB-month. Access control runs via BSC smart contracts, and storage providers hold the data — [Greenfield site](https://greenfield.bnbchain.org/en); [The Grid directory](https://thegrid.id/discovery/productType/decentralized-file-storage); [Greenfield whitepaper](https://github.com/bnb-chain/greenfield-whitepaper/blob/main/part1.md).
- Crust is still listed (Sep 2026) as an IPFS-compatible storage-order protocol with cross-chain integrations — [The Grid](https://thegrid.id/discovery/productType/decentralized-file-storage).

### Inferences
- **Paid vs raw capacity.** The gap is extreme on Filecoin. FOC run-rate revenue was about $59K/yr against roughly 1 EiB of active deals, which implies most stored data is still subsidized (Filecoin Plus / block rewards), not paid by customers.
- **Walrus price check.** At about 0.5–0.7 PB, Walrus's paid stored data is small in absolute terms. It is nonetheless one of the larger *paid* stored-data figures among the newer networks.
- **IPFS.** The Shipyard wind-down makes IPFS a protocol without a well-funded core team for the first time. It raises risk for anyone depending on ipfs.io/dweb.link gateways or public bootstrap nodes; NFT media pinned via those gateways is the most exposed. Commercial pinning firms (Pinata, Filebase) and Filecoin-integrated actors may absorb stewardship.
- **AI positioning.** Walrus (agent memory, DATA Network), Filecoin (FOC warm storage) and Storj (Valdi GPUs, cunoFS) all repositioned toward AI-data narratives in 2024–2026. Measured AI-driven paid usage was not found for any of them.
- **Consolidation and retreat.** Shipyard defunding, the Autonomi emission pause, the Codex→Logos rebrand with testnet pause, and the unverified Storj→Inveniam acquisition all point the same way.

### Gaps
- **Unreconciled Filecoin figures.** No primary 2026 Filecoin raw-capacity or active-deal figure was retrieved (Starboard/Filfox were not reachable). The 2.1 / 1.8 / 22 EiB claims conflict.
- **No Sia network stats.** No 2026 host count, stored-data figure, or price per TB was retrieved for Sia (SiaScan/Sia Central not fetched).
- **No 2026 Storj figures.** None found for node count, stored data, revenue or list price. The Inveniam acquisition is unverified.
- **No coverage at all:**
  - Arweave stored-data totals and AR/GB price.
  - Shadow Drive (GenesysGo), Jackal, 0G Storage mainnet, Tahoe-LAFS, Hyphanet, the new Freenet (Locutus), Peergos, Internxt, Filebase. No sources were found in this session.
- **Background knowledge, NOT verified this session; check before use:**
  - Freenet "Locutus" was renamed simply "Freenet", while the old Freenet became "Hyphanet" (2023).
  - Shadow Drive / GenesysGo pivoted toward Shadow/D.A.G.G.E.R. Status is unknown.
  - web3.storage (Storacha) and NFT.Storage moved to paid / Filecoin-backed models in 2024.
  - Internxt and Filebase market as consumer or S3 front ends. Filebase historically used Sia/Storj/Skynet/IPFS backends, and Skynet shut down in 2023.
  - Typical list prices circa 2024–2025: AWS S3 Standard about $23/TB-month; Backblaze B2 about $6/TB-month (raised to about $6.95 later); Wasabi about $6.99/TB-month; Storj about $4/TB-month (plus egress); Sia about $1–3/TB-month in market-driven host pricing.
- **No outages or data loss found.** No 2025–2026 data-loss or outage incidents surfaced in searches for any network. The absence of results is not evidence of none.
- **No independent durability tests.** No independent durability or retrieval benchmarks were found. Walrus latency claims are from its own authors.

## Who uses them, durability/retrieval claims, incidents, consumer apps

### Takeaway
Verified real-world usage is thin. Named adopters in 2026 sources are mostly crypto-native: DATA Network on Walrus, and AI-agent memory narratives. Filecoin's FOC had 81 payer wallets at launch. Sia shipped a consumer app with a 50 GB free tier. No independent durability or incident data was found.

### Cited Findings
- FOC at launch had 81 payer wallets and 478 datasets totalling 49.41 TiB — [Filecoin blog](https://www.filecoin.io/blog/filecoin-onchain-cloud-is-live-on-mainnet).
- DATA Foundation apps will default to Walrus for AI training-data storage (Oct 2026) — [The Daily Hodl](https://dailyhodl.com/2026/10/11/data-network-joins-sui-and-walrus-to-scale-the-supply-chain-for-ai-training-data/); [asksurf](https://asksurf.ai/pulse/en/walrus-ai-data-integration).
- Storj claims cunoFS integrations are being deployed with major media studios (Q1 2026; secondary, price-prediction article) — [MEXC/Bitget news](https://www.mexc.com/news/1024468).
- Sia Storage consumer app: 50 GB free, no crypto knowledge needed — [Sia blog](https://sia.tech/blog/the-state-of-sia-june-2026).
- Sia hostd v2.10.0 added corrupt-sector detection. This is a durability-hardening feature, which implies sector corruption was a real-world host issue — [State of Sia, Jun 2026](https://sia.tech/blog/the-state-of-sia-june-2026).
- IPFS gateway phishing abuse continues — [Netcraft](https://www.netcraft.com/blog/as-shipyard-winds-down-ipfs-phishing-enters-a-new-phase).

### Inferences
- Enterprise adoption claims, such as Storj media studios and Filecoin archives, rest mostly on company or token-marketing sources. Independently verified enterprise usage figures were not found.

### Gaps
- Named enterprise customers in 2026, NFT media dependence after Shipyard, and Internxt/Filebase/Peergos usage were not researched successfully.
- Market-size estimates are wildly inconsistent ($577M vs $8.4B for 2025) and should not be used — [CoinLaw](https://coinlaw.io/decentralized-storage-statistics/); [Marketintelo](https://marketintelo.com/report/decentralized-storage-market).

## Trends 2025-2026

### Takeaway
There are four main trends: AI-data repositioning, a shift from subsidized capacity to paid "warm/programmable" storage, funding retrenchment and consolidation, and token-economics resets.

### Cited Findings
- **Filecoin:** strategy pivot to paid onchain deals via FOC — [Filecoin 2026 strategy](https://www.filecoin.io/blog/the-2026-filecoin-network-strategy).
- **IPFS:** Protocol Labs defunded Shipyard, effective 30 Sep 2026 — [Cointelegraph](https://cointelegraph.com/news/shipyard-winds-down-ipfs-protocol-labs-funding).
- **Autonomi:** emissions paused Jan 2026, then 2.0 launched Apr 2026 — [CoinMarketCap](https://coinmarketcap.com/currencies/autonomi/).
- **Logos:** Codex merged into the Logos brand and its testnet was paused; mainnet is now targeted for 2027 — [Decrypt](https://decrypt.co/349397/logos-unifies-under-one-identity-to-deliver-a-private-tech-stack-to-revitalise-civil-society).
- **Walrus:** branded as an AI-agent memory layer, with a managed Console launched Oct 2026 — [BlockEden](https://blockeden.xyz/blog/2026/04/18/walrus-protocol-ai-agent-memory-layer-sui-decentralized-storage/).
- **Swarm:** tokenomics redesign under way (withdrawable stake, bandwidth incentives) — [Swarm blog](https://blog.ethswarm.org/foundation/2026/monthly-development-update-may-2026/).

### Inferences
- The networks with an L1 sponsor (Walrus/Sui, Greenfield/BNB) or a revenue-focused company (Storj) look more durable than foundation-grant-funded ones (IPFS implementations, Codex).

### Gaps
- No token-price data was gathered for FIL, AR, SC, STORJ, WAL or ANT in 2026, so the impact of token prices on host supply cannot be quantified here.
