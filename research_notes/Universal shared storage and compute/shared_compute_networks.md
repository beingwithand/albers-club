# Shared / Decentralized / Peer-to-Peer Compute Networks (state as of Oct 2026)

Method note: 18 web searches; direct fetches of blockeden.xyz and wikipedia.org failed (DNS), so many figures come from search-result summaries of secondary sources (crypto blogs, aggregators, vendor blogs). The most rigorous sources found: Messari "State of Akash Q1 2026", arXiv papers (INTELLECT-2, Verde, TEE-rollups, Hollow-LLM), Nous/Prime Intellect primary posts, Hugging Face model cards. Items marked [PRIOR KNOWLEDGE, unverified this session] come from model background and should be checked before publication. Items marked [OLDER] predate 2025.

## 1. Volunteer computing: BOINC, Folding@home, and why it plateaued

### Takeaway
Volunteer computing is alive but small and shrinking: BOINC is ~25K active participants / ~131K active hosts (Aug 2026), a fraction of its 2000s peak; Folding@home is still maintained (Penn, Greg Bowman; release 8.5.6, July 2026) but has no reliable current volunteer count. The model plateaued because it has no payment, depends on altruism and attention spikes, and competes with crypto mining / paid DePIN for the same idle GPUs.

### Cited Findings
- BOINC: 25,314 active participants using 130,853 active computers (hosts) worldwide as of August 2026 — [Wikipedia: BOINC](https://en.wikipedia.org/wiki/Berkeley_Open_Infrastructure_for_Network_Computing)
- Informal community estimate of long-run decline: "from a high of maybe 700K, it's down to 60K, and falling" (2023 forum; counting basis unclear, conflicts with Wikipedia figure, likely registered vs active) — [Linus Tech Tips forum, "The slow death of citizen science"](https://linustechtips.com/topic/1524943-the-slow-death-of-citizen-science-boinc/); [A brief history of BOINC](https://continuum-hypothesis.com/boinc_history.php)
- Same history essay claims "while BOINC is declining, F@h is holding steady" (dated, unsourced) — [continuum-hypothesis.com](https://continuum-hypothesis.com/boinc_history.php)
- BOINC has cumulatively processed >10^20 FLOPs across >5 million volunteer computers (cited in an Acurast/mobile-DePIN context) — [CVVC blog](https://www.cvvc.com/blogs/ais-appetite-for-compute-and-the-rise-of-decentralized-mobile-compute)
- Folding@home: stable release 8.5.6 (13 July 2026); project now based at University of Pennsylvania, led by Greg Bowman — [Wikipedia: Folding@home](https://en.wikipedia.org/wiki/Folding@home)
- Community still runs competitions (e.g., "Formula BOINC 2026") and asks about BOINC Central project status — [LTT Formula BOINC 2026](https://linustechtips.com/topic/1638870-formula-boinc-2026); [LTT BOINC Central status](https://linustechtips.com/topic/1612239-boinc-central-project-status/)

### Inferences
- [PRIOR KNOWLEDGE, unverified this session, OLDER] Folding@home started at Stanford (Vijay Pande) in 2000; PS3 client (2007-2012) gave large boosts; in March-April 2020 COVID-19 drove it past ~1 exaFLOPS (reported ~2.4 x86 exaFLOPS at peak), first "exascale" system, then participation fell back sharply. Moved through Washington University in St. Louis (Bowman) before Penn. BOINC originated at UC Berkeley (David Anderson) from SETI@home (1999); SETI@home stopped distributing work in March 2020.
- Plateau reasons (synthesis): (a) no economic incentive vs. GPU mining (2017-2022) and now paid DePIN; (b) attention-driven spikes (COVID) decay; (c) desktops replaced by laptops/phones with power, thermal, and OS background limits; (d) electricity cost borne by volunteer; (e) science workloads mostly embarrassingly parallel and can be met cheaply by HPC/cloud grants; (f) aging volunteer base and declining project count/funding.
- Volunteer computing solved verification with redundancy (replicate work units, compare) and credit systems — the same technique DePIN networks reuse.

### Gaps
- No primary 2025-2026 Folding@home active-user or FLOPS figure found (stats.foldingathome.org not fetched).
- BOINCstats time series not retrieved; peak active-host number not verified.

## 2. Marketplaces / DePIN compute: scale, real usage, pricing, 2025-2026 developments

### Takeaway
Real paid usage exists but is small relative to token valuations and hyperscalers. Aethir claims the largest revenue (~$128M FY2025; disputed/self-reported); Render has demand exceeding supply in 2026 with ~35-40% AI workloads; io.net ~$20M annualized (self-reported); Akash is shrinking on supply side (Messari: 334 avg available GPUs, ~$1M annualized lease revenue in Q1 2026) while pivoting to AkashML inference. Prices on consumer/marketplace GPUs are well below hyperscaler list (RTX 4090 $0.16-0.48/hr; H100 $0.90-2.27/hr on Vast.ai vs ~$3-4+/hr hyperscaler list-equivalent), but come without SLAs.

### Cited Findings
**Sector**
- Leading DePIN networks (all sectors, not just compute) generated ~$150M on-chain revenue in January 2026 (record) — [DePINscan](https://depinscan.io/news/2026-02-06/depin-sector-sees-record-revenue-surge-in-january-2026)
- 2026 narrative across crypto research: "revenue pivot" from token emissions to real enterprise overflow demand — [BlockEden Mar 2026](https://blockeden.xyz/blog/2026/03/12/depin-compute-revenue-pivot-akash-ionet-aethir/); [BlockEden Apr 2026](https://blockeden.xyz/blog/2026/04/12/depin-revenue-pivot-token-subsidies-ai-compute-akash-render-ionet/); [Bex.co Apr 2026](https://bex.co/blog/2026/04/03/depin-revenue-inflection-enterprise-cloud-overflow-akash-ionet)
- A Sept 2026 independent DePIN research report titled "When Marketing Metrics Met Machine Reality" critiques reported vs actual figures — [GitHub Ricosworks1/depin-research-reports](https://github.com/Ricosworks1/depin-research-reports/releases/tag/depin-dispatch-marketing-metrics-machine-reality-20260916)
- Low-authority claim: ~500K GPUs "across Akash, Render, io.net and Golem" (aggregated listed supply, not utilized) — [misar.blog](https://www.misar.blog/@synor/articles/decentralized-gpu-networks-compute)

**Aethir** (enterprise GPUs, cloud gaming + AI; uses enterprise-grade H100/H200 clusters run by "Cloud Hosts")
- $127.8M revenue FY2025; annualized run rate $166M by Q3 2025; another source gives $147M Q3 2025 annualized; 150+ active compute clients (AI training, Web3, cloud gaming); described as largest verifiable revenue among decentralized GPU networks — [rzlt.io](https://www.rzlt.io/blog/7-depin-projects-generating-10m-revenue-(and-what-you-can-learn-from-them)); [BlockEden](https://blockeden.xyz/blog/2026/03/12/depin-compute-revenue-pivot-akash-ionet-aethir/)

**io.net**
- ~139,000 GPUs listed on network; pushing toward ~$20M annualized revenue; revenue is self-reported, not reconciled on-chain — [rzlt.io](https://www.rzlt.io/blog/7-depin-projects-generating-10m-revenue-(and-what-you-can-learn-from-them))
- Claims up to 90% cost reduction vs centralized clouds (vendor claim); IO token ~$0.17, market cap ~$71M (5 Oct 2026) — [hoge.gg](https://hoge.gg/akash-vs-io-net-render-depin-gpu-race-2026/)

**Akash Network** (Cosmos-based reverse-auction marketplace)
- Messari Q1 2026: avg active leases 583 (−4.4% QoQ, −32.9% YoY from 868); new leases 43,540 (+27.1% QoQ); lease revenue ~$253K for quarter (~$1M annualized, −45%); avg active providers 58 (record low); avg available GPUs 334 (−57.5% QoQ); utilization ~34% (84 of 334 GPUs rented) — [Messari: State of Akash Q1 2026](https://messari.io/report/state-of-akash-q1-2026-final)
- Conflicting secondary figures: "record $5M compute spend Q1 2026"; May 2026 ~250 active GPUs / 73 providers / ~$4.3M annualized; GPU peak ~897 in Q1 2025 — [Go2Mars Medium](https://medium.com/@Go2Mars/2026-real-progress-and-investment-opportunities-in-decentralized-compute-networks-depin-5791ceed802a); [cache256](https://www.cache256.com/ecosystem/akash-network-depin-gpu-marketplace-business/)
- Akash dashboard mid-July 2026: ~121 GPU providers, ~253 active GPU leases (real-time methodology, not comparable to Messari) — [stats.akash.network](https://stats.akash.network/) via [ownyourmind.ai](https://ownyourmind.ai/projects/akash/)
- AkashML inference: ~5B tokens/day (May 2026) to >10B/day (early July 2026); users include Venice, ElizaOS, Morpheus, Gensyn — [ownyourmind.ai](https://ownyourmind.ai/projects/akash/)
- Starcluster: protocol-owned GPU effort financed via "Starbonds" (up to $75M), targeting ~7,200 NVIDIA GB200 run by vetted "Nodekeepers"; criticized as centralizing; no adoption metrics yet — [ownyourmind.ai](https://ownyourmind.ai/projects/akash/); [hoge.gg](https://hoge.gg/akash-network-gpu-marketplace-explained-2026/)
- Token mechanics in 2026: "BME" (burn-mint equilibrium) and a Cosmos migration discussed — [ownyourmind.ai](https://ownyourmind.ai/projects/akash/)

**Render Network** (OctaneRender/Otoy origin, Solana)
- Negative GPU supply availability in Q2 2026 (demand > available nodes), first since 2018 — [Crypto Briefing](https://cryptobriefing.com/render-network-negative-gpu-supply-2026/)
- Job-related burns: 530,171 RENDER Jan-Sep 2025 vs 139,924 same 2024 period (+279%) — [hoge.gg](https://hoge.gg/render-token-2026-ai-compute-pivot/); [Crypto Briefing](https://cryptobriefing.com/render-network-negative-gpu-supply-2026/)
- AI workloads ~35-40% of network activity, vs <10% in 2024 — [Crypto Briefing](https://cryptobriefing.com/render-network-negative-gpu-supply-2026/)
- Render claims some AI tasks run on its "Dispersed" nodes at ~$0.69/GPU-hr (vendor claim); ~5,600 active GPU nodes cited; RENDER ~$2.01 (5 Oct 2026) — [hoge.gg](https://hoge.gg/render-network-gpu-crunch-ai-inference/)
- 65 million frames rendered milestone (Jan 2026) — [bex.co](https://bex.co/blog/2026/01/12/render-network-decentralized-gpu-compute-ai-hollywood)

**Marketplace pricing (mostly from Spheron, a competitor; treat cautiously)**
- Vast.ai: verified datacenter H100 PCIe ~$1.50-2.27/hr; unverified hosts ~$0.90-1.60/hr — [Spheron Vast.ai pricing 2026](https://www.spheron.network/blog/vastai-pricing-2026/); [Runpod vs Vast.ai](https://www.spheron.network/blog/gpu-cloud-pricing-comparison-runpod-vs-vastai-2026/)
- Spheron (aggregator of datacenter + community GPUs): H100 SXM ~$2.20/hr spot, $2.98/hr on-demand; RTX 4090 $0.48-0.72/hr — [Spheron pricing comparison 2026](https://www.spheron.network/blog/gpu-cloud-pricing-comparison-2026/)
- SaladCloud (consumer gaming PCs): RTX 4090 $0.33/hr high priority, $0.16/hr lowest/batch tier, no formal SLA — [Spheron on SaladCloud](https://www.spheron.network/blog/saladcloud-pricing-2026-gpu-cost-vs-spheron/)
- Theta EdgeCloud: 95 configs across 29 GPU types, cheapest $0.05/hr, avg $0.46/GPU-hr (another snapshot: avg $0.72/hr over 47 configs) — [gpus.io Theta](https://gpus.io/en/providers/theta-edgecloud); [gpus.io Theta vs Vast](https://gpus.io/en/providers/compare/theta-edgecloud-vs-vast-ai)

**Gensyn** (decentralized ML training; Ethereum L2)
- Several sources: mainnet live 22 April 2026 with "Delphi" (AI-oracle-settled prediction/information market) as first app; $AI token listed Coinbase/OKX 29 April, Binance 14 May 2026 — [panewslab](https://www.panewslab.com/en/articles/019e4980-5ed7-7553-9d84-ae2e5468e0fc); [akta.pro](https://akta.pro/company-profiles/0000b5n/gensyn); [LBank](https://www.lbank.com/academy/what-is-gensyn-aigensyn)
- Contradiction: a review ~Aug 2026 says training-network mainnet still pending, no live economic security; RL Swarm and hosted nodes paused to focus on Delphi — [ownyourmind.ai Gensyn](https://ownyourmind.ai/projects/gensyn/)
- RL Swarm: P2P RL testnet, ~12,000 nodes mid-2025 (outdated) — [despread guide](https://research.despread.io/gensyn-guide/); [bex.co](https://bex.co/blog/2026/05/05/gensyn-rl-swarm-decentralized-ml-training-ethglobal)
- Verde: dispute-resolution verification that recomputes only the disputed operation (arXiv 2502.19405); "REE" (reproducible execution environment) for deterministic computation — [panewslab](https://www.panewslab.com/en/articles/eaulwlvx); [arXiv 2502.19405](https://arxiv.org/abs/2502.19405)

**Bittensor (TAO) subnets / Templar (SN3)**
- Covenant-72B completed 10 March 2026 by Templar (a.k.a. Covenant AI) on Subnet 3: 72B params, ~1.1T tokens, >70 permissionless nodes on commodity internet; MMLU zero-shot 67.1 (vs LLaMA-2-70B 65.6, LLM360 K2 65.5; below Qwen2.5-72B); Apache weights; arXiv paper 9 March 2026 — [tao.media](https://www.tao.media/templar-makes-history-with-72b-decentralized-ai-training-run/); [Opentensor Foundation on X](https://x.com/opentensor/status/2032567840189096404); [Grey Area Labs](https://greyarealabs.co/2026/03/23/covenant-72b-decentralized-training/); [simplytao](https://simplytao.ai/blog/covenant-72b-the-largest-decentralized-llm-training-run)
- Unverified single-source: Covenant AI publicly exited Bittensor 10 April 2026 over governance disputes, TAO fell ~15%; still runs SN3, SN39, SN81 — [ownyourmind.ai](https://ownyourmind.ai/tokenomics/templar-bittensor-covenant-exit/)

**Prime Intellect**
- INTELLECT-1 (10B) trained across three continents (2024) [OLDER]; INTELLECT-2 (32B, launched April 2025, released May 2025): fully asynchronous RL over permissionless heterogeneous swarm; components: inference rollout workers, TOPLOC validators, GRPO trainers, weight broadcast via "shardcast" — [Prime Intellect blog](https://www.primeintellect.ai/blog/intellect-2); [arXiv 2505.07291](https://arxiv.org/pdf/2505.07291); [X launch](https://x.com/PrimeIntellect/status/1912266266137764307)
- INTELLECT-3 (Nov 2025): 106B MoE, AIME24 90.8, trained on centralized 512 H200 InfiniBand cluster (~2 months) with prime-rl — i.e., flagship not decentralized — [Techmeme](https://www.techmeme.com/251128/p17); [implicator.ai](https://www.implicator.ai/prime-intellects-intellect-3-open-source-ambition-meets-centralized-reality/)
- Commentary: RL post-training decentralizes better than pretraining (many communication-light rollouts + small heavy update step); PI now straddles marketplace + centralized flagship training — [implicator.ai](https://www.implicator.ai/prime-intellects-intellect-3-open-source-ambition-meets-centralized-reality/)

**Nous Research (Psyche / DisTrO)**
- Psyche launched May 2025, coordinated on Solana; first run "Consilience": 40B MLA model over 20T tokens — [Nous: Psyche](https://nousresearch.com/nous-psyche); [X announcement](https://x.com/NousResearch/status/1922744483571171605?lang=en); [Import AI 413](https://importai.substack.com/p/import-ai-413-40b-distributed-training)
- Consilience-40B still "ongoing" per HF card (checkpoint every 500 steps, duration TBD); third-party review says no published trained-token count — [HF PsycheFoundation/consilience-40b](https://huggingface.co/PsycheFoundation/consilience-40b-CqX3FUm4); [ownyourmind.ai Nous](https://ownyourmind.ai/projects/nous-research/)
- Hermes 4.3 (36B, Dec 2025) described as first Hermes trained decentralized over internet on Psyche — [aiwiki Nous Research](https://aiwiki.ai/wiki/nous_research); see also [Nous: Next Phase of Psyche](https://nousresearch.com/the-next-phase-of-psyche)
- DisTrO earlier achieved 15B distributed run [OLDER, Dec 2024] — [tokenintel landscape](https://tokenintel.org/learn/protocols/decentralized-training-landscape)

**Pluralis Research**
- "Protocol Learning": decentralized, communication-efficient model-parallel training where no participant holds full weights; $7.6M seed (Mar 2025) led by USV and CoinFund; ran ICML 2026 Protocol Learning workshop (Seoul, 10 July 2026) — [Pluralis](https://pluralis.ai/); [Third Path blog](https://pluralis.ai/blog/a-third-path-protocol-learning/); [AI Insider](https://theaiinsider.tech/2025/03/24/pluralis-research-pioneers-protocol-learning-to-scale-decentralized-ai-announces-7-6m-seed-round-led-by-usv-and-coinfund/); [ICML workshop](https://pluralis.ai/events/icml-protocol-learning-workshop/)

**Other decentralized RL research**
- AuroraRL (arXiv 2602.11456) and weight-update-sparsity work (arXiv 2602.03839) on communication-efficient decentralized RL; survey of decentralized LLM training (arXiv 2503.11023) — [AuroraRL](https://arxiv.org/pdf/2602.11456); [Sparsity](https://arxiv.org/pdf/2602.03839); [Survey](https://arxiv.org/pdf/2503.11023)

### Inferences
- Two tiers: (1) "decentralized" networks that are really aggregators of datacenter GPUs (Aethir, io.net, Spheron, much of Akash, Vast.ai verified) — where most real revenue sits; (2) true consumer/idle-device networks (Salad, Render dispersed, Vast unverified, Nosana community nodes) — cheap, batch/inference-oriented, no SLA.
- Akash shows the hazard: token-subsidy-era supply leaves when incentives drop; Messari data shows provider and GPU counts at historic lows in Q1 2026 even as lease counts rose (smaller, shorter jobs).
- Decentralized training frontier as of Oct 2026: 72B pretraining (Covenant-72B, roughly Llama-2-70B quality, i.e., ~2-3 years behind frontier) and 32-36B RL/post-training; flagship-quality runs (INTELLECT-3) still done centrally.
- [PRIOR KNOWLEDGE, unverified this session] Golem (2016, Ethereum, CPU-oriented, GPU beta), Nosana (Solana, consumer GPU inference), Fluence (CPU cloud with "compute-to-data" pivot), Spheron (aggregator), Theta EdgeCloud (hybrid edge+cloud GPUs from Theta video network), Salad (paying gamers in rewards; claimed tens of thousands of daily active GPUs) all exist; no reliable 2026 usage figures found for Golem, Nosana, Fluence.
- [PRIOR KNOWLEDGE] Hyperscaler on-demand H100 (8-GPU instance) list prices were ~$3-4+/GPU-hr after AWS cut P5 prices ~44% in June 2025; neoclouds ~$2-3/hr. So DePIN discounts vs neoclouds are much smaller than "90% vs AWS" marketing implies.

### Gaps
- No verified 2026 usage/revenue for Golem, Nosana, Fluence, Salad, Vast.ai, Theta EdgeCloud, Spheron.
- Bittensor network-wide stats (number of subnets post-dTAO, emissions, real revenue) not retrieved.
- Gensyn mainnet scope (training vs Delphi only) unresolved — sources conflict.
- Aethir/io.net revenue not independently audited; no primary disclosures fetched.
- No Epoch AI or Galaxy research on decentralized training compute retrieved this session.

## 3. Pooling personal devices for local AI (Exo, Petals, llama.cpp RPC, Apple PCC)

### Takeaway
Pooling works best as a small, trusted, high-bandwidth cluster (e.g., 2-4 Apple Silicon Macs over Thunderbolt 5 RDMA via exo) to fit large models in aggregate memory; it does not work well across the open internet because pipeline/tensor parallelism is latency-bound (Petals: ~4-6 tok/s on 70-180B, stalled project). Apple PCC is the reference for private remote inference: stateless nodes, no admin access, attested software in a transparency log — now extending to Google Cloud NVIDIA GPUs.

### Cited Findings
- exo (EXO Labs): auto device discovery, topology-aware model placement, MLX backend, OpenAI/Claude/Ollama-compatible APIs; macOS Apple Silicon is the primary tested platform, Linux CPU-only (GPU "under development"), no Windows — [toolhalla](https://toolhalla.ai/blog/exo-framework-distributed-inference-guide-2026); [starlog.is](https://starlog.is/articles/developer-tools/exo-explore-exo/)
- macOS 26.2 added RDMA over Thunderbolt 5; exo uses it; EXO's "~99% latency reduction" claim from own benchmarks, not audited — [lobsterpack](https://www.lobsterpack.com/blog/exo-distributed-ai-cluster-macs/); [virge.io](https://virge.io/en/blog/exo-mac-studio-cluster-llm/)
- EXO benchmarks with 4x M3 Ultra Mac Studio: Qwen3-235B, DeepSeek V3.1 671B, Kimi K2 Thinking — [virge.io](https://virge.io/en/blog/exo-mac-studio-cluster-llm/); [stridenote](https://stridenote.net/how-exo-clusters-macs-to-run-a-671b-model-locally/)
- Entry cluster 4x M4 Pro Mac mini (~$5,600) ~12-15 tok/s on ~70B-class model (single blog) — [compute-market](https://www.compute-market.com/blog/mac-mini-cluster-local-ai-2026)
- Unconfirmed: Apple removed 512GB Mac Studio config, 256GB max as of March 2026 — [toolhalla](https://toolhalla.ai/blog/exo-framework-distributed-inference-guide-2026)
- Petals: load part of a model and join a swarm serving other layers; claims up to 6 tok/s Llama-2-70B, 4 tok/s Falcon-180B single-batch (2023-era); repo largely inactive (~800+ days since update per search metadata); resurfaced on HN in 2026 with bandwidth skepticism — [Petals GitHub](https://github.com/bigscience-workshop/petals); [petals.dev](https://petals.dev/); [HN 2026](https://news.ycombinator.com/item?id=49015735); [explainx July 2026](https://explainx.ai/blog/petals-distributed-llm-inference-revisited-july-2026)
- Petals reportedly supported >800 active contributor nodes, with no incentive layer — [CVVC](https://www.cvvc.com/blogs/ais-appetite-for-compute-and-the-rise-of-decentralized-mobile-compute)
- 2026 comparison of SharedLLM vs Petals vs Exo vs Kalavai — [sharedllm.org](https://sharedllm.org/blog/sharedllm-vs-petals-vs-exo.html)
- Apple PCC: stateless computation, enforceable guarantees, no privileged runtime access (no SSH/shells/debug), non-targetability, verifiable transparency; Virtual Research Environment boots PCC software in a VM with virtual SEP, verifies against transparency log (needs macOS 15.1, ≥16GB) — [SC World](https://scworld.com/news/apple-publishes-its-1st-ever-virtual-research-environment-for-private-cloud-compute); [SimpleMDM](https://simplemdm.com/blog/apple-intelligence-how-secure-is-private-cloud-compute-for-enterprise/); [The Apple Wiki pccvre](https://theapplewiki.com/wiki/Pccvre)
- Runtime properties like data deletion remain Apple claims checkable only via source review/VRE — [DEV Community](https://dev.to/nagayu/i-verified-apples-private-cloud-compute-from-my-own-device-export-2hm3)
- June 2026: Apple extending PCC to Google Cloud NVIDIA GPUs, summer 2026 preview, dual roots of trust (low-quality sources; verify) — [WebProNews](https://www.webpronews.com/apples-private-cloud-compute-faces-scrutiny-as-it-expands-beyond-its-own-servers/); [mer.vin](https://mer.vin/2026/06/apple-private-cloud-compute-on-google-cloud-nvidia-gpus-with-verifiable-privacy/)

### Inferences
- Latency physics: autoregressive decode with pipeline parallelism requires one network hop per stage per token; at 20-100 ms WAN RTTs and several stages, decode caps at a few tok/s (consistent with Petals' numbers). LAN/Thunderbolt (µs-scale RDMA) makes tensor parallelism viable, which is why exo's credible results are all same-desk clusters.
- [PRIOR KNOWLEDGE, unverified this session] llama.cpp's RPC backend (rpc-server) lets one host offload layers to remote ggml backends over TCP; it is marked experimental/insecure (no auth/encryption, LAN only) and throughput is bounded by network and per-token round trips.
- PCC is the inverse of DePIN: one trusted operator, hardware attestation, and public software images — the privacy bar a "strangers' devices" network would have to meet.

### Gaps
- No measured llama.cpp RPC latency/throughput figures retrieved.
- No independent exo benchmarks over WAN or mixed hardware.
- Apple PCC primary docs (security.apple.com) not fetched.

## 4. Hard problems: verification, privacy, scheduling, bandwidth, churn

### Takeaway
No cheap, general, trustless verification exists for large-model work: production systems use redundancy/spot-checks, cheap commitments (TOPLOC), optimistic fraud proofs (Verde, opML) or TEEs (H100/H200 confidential computing, ~5-20% overhead, trust in NVIDIA). zkML remains 100-10,000x overhead and has new attacks (Hollow-LLM). Privacy on strangers' hardware is essentially only solvable with TEEs. Bandwidth is addressed by DiLoCo-style low-communication training and RL's rollout/update split.

### Cited Findings
- TOPLOC: locality-sensitive hashing commitments over final hidden states during decoding; validators check up to 100x faster than original inference — [arXiv 2505.07291 (INTELLECT-2)](https://arxiv.org/pdf/2505.07291)
- Verde (Gensyn): refereed delegation — only the disputed operation recomputed; relies on reproducible/deterministic execution (REE) — [panewslab](https://www.panewslab.com/en/articles/eaulwlvx); [arXiv 2502.19405](https://arxiv.org/abs/2502.19405)
- NVIDIA confidential computing on H100/H200: ~5% overhead per one overview; trust anchored in hardware vendor — [hoge.gg verifiable compute](https://hoge.gg/verifiable-compute-ai-agent-trust-layer-2026/); another model estimates ~15-20% degradation vs bare metal — [arXiv 2512.20176](https://arxiv.org/pdf/2512.20176)
- zkML: 100-10,000x overhead, "practical at LLM scale: no (small models only)" — [prompt20 blog](https://blog.prompt20.com/posts/verifiable-inference/); counterpoint: recent work verifies a 13B model in <15 min with <200KB proof — [chainofthought.xyz](https://chainofthought.xyz/p/don-t-trust-verify-the-emerging-stack-for-ai-verification-e18a)
- Hollow-LLM attack: computationally trivial weights can pass zero-knowledge verification of LLM inference (i.e., proving "a model ran" is not proving "the right/useful model ran") — [arXiv 2607.28884](https://arxiv.org/pdf/2607.28884)
- Optimistic ML (ORA opML): post result, challenge window, fraud proofs — [chainofthought.xyz](https://chainofthought.xyz/p/don-t-trust-verify-the-emerging-stack-for-ai-verification-e18a)
- Optimistic TEE-Rollups hybrid: H100 TEE + fraud proofs; simulated 1400x speedup vs zkML and 99% latency reduction vs opML (simulation, not production) — [arXiv 2512.20176](https://arxiv.org/pdf/2512.20176)
- "Trust, but verify" survey: even with TEEs you cannot verify a server actually uses that LLM to serve internet requests; key distribution to permissionless TEEs is a major challenge — [arXiv 2504.13443](https://arxiv.org/pdf/2504.13443)
- TEE side channels (Foreshadow, Spectre) remain a risk — [arXiv 2512.20176](https://arxiv.org/pdf/2512.20176)
- Cost-aware Proof-of-Quality for decentralized LLM inference (judge output quality rather than recompute) — [arXiv 2512.16317](https://arxiv.org/pdf/2512.16317)
- Verification of edge/DePIN devices: existing schemes "either insecure or inefficient", vulnerable to malicious device owners; low-end devices can't support large LLMs — [PolyLink arXiv 2510.02395](https://arxiv.org/pdf/2510.02395); [arXiv 2407.19401](https://arxiv.org/pdf/2407.19401)
- Churn/fault tolerance: INTELLECT-2 used async RL across dynamic swarm; AuroraRL targets fault tolerance and cost efficiency over decentralized networks — [Prime Intellect](https://www.primeintellect.ai/blog/intellect-2); [AuroraRL](https://arxiv.org/pdf/2602.11456)
- Communication: weight-update sparsity exploited to cut RL comms — [arXiv 2602.03839](https://arxiv.org/pdf/2602.03839); Covenant-72B trained over commodity internet links — [tao.media](https://www.tao.media/templar-makes-history-with-72b-decentralized-ai-training-run/)

### Inferences
- Practical stack in 2026: reputation + staking/slashing + sampled redundancy for cheap work; TOPLOC-like commitments for inference/rollouts; TEEs for anything private; zk only for small models or narrow claims.
- Data privacy: without TEEs, any prompt/data sent to a stranger's GPU is visible to that operator; confidential GPUs exist mainly in datacenters (H100/H200/Blackwell), so consumer-GPU networks cannot offer meaningful privacy — a structural ceiling on enterprise use of the "idle home GPU" tier.
- [PRIOR KNOWLEDGE, unverified] DiLoCo (DeepMind, 2023) / OpenDiLoCo (Prime Intellect, 2024) / DeMo-DisTrO (Nous) reduce sync frequency/volume by ~100-1000x, enabling training over internet links; scheduling heterogeneity (mixed GPU types, NAT, residential bandwidth asymmetry) still caps utilization.

### Gaps
- No production measurements of TEE overhead on Blackwell; no data on how often DePIN networks detect fraud.
- Atoma/Phala/Nillion specific verification designs and usage not retrieved.

## 5. Phones as participants

### Takeaway
Phones are marginal compute contributors. The only established phone-native network found is Acurast (phones as TEE-backed serverless processors), plus small experiments (Destra Edge; Pocket Network/NodeGhost AI-gateway pilot on Acurast). Constraints — battery, thermal throttling, iOS/Android background-execution limits, tiny RAM vs LLM sizes, and verification — make phones suitable for light, verifiable, latency-tolerant tasks, not LLM serving.

### Cited Findings
- Acurast: decentralized compute network of smartphones as "Processors"; workloads run in hardware-backed TEEs; "Processor Lite" (everyday phone app) and "Processor Core" (dedicated phone) — [Acurast blog](https://acurast.com/blog/network-and-tech/what-is-crypto-ai-acurasts-role-in-decentralized-ai-compute/)
- Acurast + Pocket Network + NodeGhost: exploratory full AI gateway running entirely on TEE-secured smartphones, no cloud server — [Acurast partnerships](https://acurast.com/blog/partnerships/decentralized-confidential-ai-inference-powered-by-smartphones/)
- Destra Edge: app turning opted-in phones into inference nodes (company Medium post, unverified) — [Destra Medium](https://medium.com/@destranetwork/destra-edge-turning-smartphones-into-a-decentralized-gpu-inference-network-75d8ac042cca)
- Limited compute on low-end devices makes it hard for DePINs to support large LLMs; verification against dishonest device owners is unsolved — [PolyLink arXiv 2510.02395](https://arxiv.org/pdf/2510.02395)
- Mobile-compute thesis pieces (VC/advocacy) — [CVVC](https://www.cvvc.com/blogs/ais-appetite-for-compute-and-the-rise-of-decentralized-mobile-compute); [KuCoin ACU insight](https://www.kucoin.com/news/insight/ACU/6acc943444c2130007894a39)

### Inferences
- [PRIOR KNOWLEDGE, unverified, OLDER] Historical phone volunteer efforts: BOINC for Android (2013+, charging + Wi-Fi + battery-threshold rules), Samsung "Power Sleep" (2014, Rosetta/U. Vienna), IBM World Community Grid Android app; none scaled, and iOS never allowed sustained background compute. Federated learning (Google Gboard) is the one mass-scale "phones as compute" success, but it runs only when idle/charging/unmetered and trains small models under the platform owner's control.
- Phones' real role in shared AI is as clients of private cloud (PCC) or on-device small models, not as servers to others.

### Gaps
- No verified device counts, job volumes, or revenue for Acurast or Destra.
- No measurements of phone-node uptime/churn found.
