# Core Technical Building Blocks for Shared Storage/Compute on Untrusted Devices (state of the art, October 2026)

Method note: these notes come from about 15 web searches and fetches plus well-known seminal literature. Network fetches of the Storj whitepaper and of USENIX pages failed (DNS errors). For those, I cite the canonical URL and the claim comes from the established literature, marked "[seminal/known; not re-fetched]". Numbers that come from my own calculations are under Inferences. Seminal older work is labeled (SEMINAL, year).

---

## 1. Erasure coding, repair, and durability under churn

### Takeaway
With independent failures, erasure coding gives "11 nines" almost for free, even on churny home devices. What actually limits the system is (a) **availability**, because home devices are often offline, (b) **repair bandwidth**, because data must be re-created as nodes leave (Blake & Rodrigues 2003), and (c) **correlated failures**. Current designs therefore use (i) codes with low repair bandwidth (LRC, regenerating/Clay, or Walrus's 2D "Red Stuff" with O(|blob|/n) repair), (ii) lazy repair thresholds, and (iii) wide stripes (Storj ~29-of-80).

### Cited Findings
**Seminal results**
- (SEMINAL, 2003) Blake & Rodrigues, "High Availability, Scalable Storage, Dynamic Peer Networks: Pick Two" (HotOS IX). They used a resource model fed with Gnutella measurements and found that large-scale cooperative storage is limited by churn and cross-system bandwidth, not disk space. Delayed failure response, admission control, and load-shifting "do not alter the basic problem". When redundancy, data scale, and dynamics are all high, the cross-system bandwidth needed is "unreasonable". — [USENIX HotOS IX](https://usenix.org/conference/hotos-ix/high-availability-scalable-storage-dynamic-peer-networks-pick-two); [MIT PMG abstract](https://pmg.csail.mit.edu/iris/blake03high-abstract.html)
- (SEMINAL, 2010) Dimakis, Godfrey, Wu, Wainwright, Ramchandran, "Network Coding for Distributed Storage Systems". This paper defines regenerating codes: a failed node is repaired by contacting any d nodes and downloading β symbols from each, with dβ << file size B. It also gives the storage/repair-bandwidth tradeoff curve, whose endpoints are MSR (minimum storage) and MBR (minimum bandwidth). Illustration: for a lost node holding 100 MB, RS repair moves ~1 GB and MSR repair ~325 MB. — [IITH talk slides citing Dimakis et al.](https://people.iith.ac.in/mynav/pdfs/talks/Defence.pdf)
- (2018) Clay codes (Vajha et al., FAST '18) are MSR codes built by pairwise coupling of stacked layers of any MDS code, extending Ye–Barg. The authors call them the first practical MSR implementation, with optimal repair bandwidth and disk I/O and uniform repair of data and parity nodes. The plugin was merged into Ceph and shipped in Nautilus (March 2019). In Ceph, a 1.25x-overhead Clay code cut repair network traffic 2.9x, disk reads 3.4x, and repair time 3x versus RS (per the secondary summary). — [USENIX FAST'18](https://usenix.org/conference/fast18/presentation/vajha); [Morning Paper summary](https://blog.acolyer.org/2018/03/01/clay-codes-moulding-mds-codes-to-yield-an-msr-code/); [Rust crate clay-codes](https://docs.rs/crate/clay-codes/latest)
- (SEMINAL, 2012) Azure LRC (Huang et al., USENIX ATC 2012, "Erasure Coding in Windows Azure Storage"). The (12,2,2) LRC adds local parities per group of 6 data fragments, so the common single-fragment repair reads 6 fragments instead of 12. Overhead is 1.33x, with durability comparable to 3-way replication. [seminal/known; not re-fetched] — [USENIX ATC'12](https://www.usenix.org/conference/atc12/technical-sessions/presentation/huang)
- (SEMINAL) Facebook's HDFS-Xorbas "XORing Elephants" (VLDB 2013) is the other canonical LRC deployment paper. It cut repair disk I/O and network traffic about 2x for 14% extra storage. [seminal/known; not re-fetched] — [arXiv 1301.3791](https://arxiv.org/abs/1301.3791)
- Fountain codes. (SEMINAL) LT codes (Luby 2002) and Raptor codes (Shokrollahi 2006) are rateless, so any ~k(1+ε) symbols decode. RaptorQ (RFC 6330) recovers with very small overhead and allows up to 56,403 source symbols per block. Rateless coding suits churn because new repair symbols can be generated without coordinating fragment indices. [seminal/known; not re-fetched] — [RFC 6330](https://www.rfc-editor.org/rfc/rfc6330)

**Walrus "Red Stuff" (2025, current SOTA for decentralized blob storage)**
- The Walrus paper (Danezis et al., Mysten Labs, arXiv 2505.05370) presents Red Stuff, a 2D erasure code. It reaches high security at **~4.5x replication** while allowing **self-healing recovery with bandwidth O(|blob|/n)** instead of O(|blob|) as in classical RS-based systems. — [arXiv abs v1](https://arxiv.org/abs/2505.05370v1)
- Construction: the blob is laid out as a grid. Column encoding gives "primary slivers" and row encoding gives "secondary slivers". A node that lost its sliver rebuilds it from small symbols held by other nodes. — [arXiv PDF](https://arxiv.org/pdf/2505.05370)
- A Codex team analysis describes the grid as (f+1)×(2f+1), with RaptorQ used for the row and column extensions. — [Codex HackMD](https://hackmd.io/@codex-storage/HJcpg-7nlx)
- Red Stuff supports **storage challenges in asynchronous networks**, so adversaries cannot pass verification by using network delays to fetch data on demand. Recovery needs no central coordination. — [arXiv v2 HTML](https://arxiv.org/html/2505.05370v2); [Walrus blog](https://blog.walrus.xyz/how-walrus-red-stuff-encoding-works/)

**Storj (production erasure coding over untrusted nodes)**
- Storj's executive summary says erasure-coded systems reach "six 9s" of durability with about 5x less storage than replication. — [Storj exec summary PDF](https://static.storj.io/Storj-White-Paper-Executive-Summary.pdf)
- Storj splits each segment into 80 pieces by default, and any 29 rebuild it. — [blockeden blog (secondary)](https://blockeden.xyz/de/blog/tags/storj/); [Storj forum on 29/80 choice](https://forum.storj.io/t/node-selection-ratio/9042)
- Whitepaper v3.1 (March 2024) covers redundancy (§3.4), audits and reputation (§3.7), and durability, device failure, and churn (§2.5). Its RS parameter scheme, as I know it: k=29 minimum, m≈35 repair threshold, o=80 success threshold, n=110 uploads started, with the long tail cut off. [known; fetch of PDF failed, verify] — [Storj whitepaper v3](https://static.storj.io/storjv3.pdf)

### Inferences
- **Durability math (my own computation, binomial, independent failures).** Assumptions: nodes leave permanently with exponential lifetime L, and the system repairs every window w. Annual loss ≈ (365/w)·P(more than n−k of n fragments lost in w).
  - L=180 d, w=7 d: 20/10 (2x) ≈ 1.6e-9/yr. 30/10 (3x) ≈ 9e-22. 40/20 (2x) ≈ 5e-18. 80/29 (2.76x) ≈ 9e-52.
  - L=365 d, w=1 d: 20/10 ≈ 4e-21.
  - Under independence, 11 nines (1e-11) needs only ~2x overhead with k≥20 and weekly repair. Wider stripes (larger k at the same overhead) improve durability by many orders of magnitude.
  - The real risks are **correlated failures**: ISP or region outages, a bad client release, coordinated Sybil exit. These need placement diversity (one fragment per AS, household, or operator), not more parity.
- **Availability is the harder constraint for home devices (my calculation).** Let a be the per-node online fraction. P(fewer than k online), i.e. data unavailable:
  - a=0.5: 30/10 → 2e-2. 40/10 → 3e-4. 110/29 → 1.3e-7.
  - a=0.7: 30/10 → 7e-6. 80/29 → 1e-10.
  - a=0.9: 20/10 → 7e-7.
  - So mostly-offline phones and laptops (a≈0.3–0.5) need 3.5–4x+ expansion and wide stripes for interactive availability. Always-on boxes (NAS, routers, desktops left on; a≥0.9) can use ~2x. **Separate "durability nodes" (always-on) from "cache nodes" (intermittent).** Distinguishing transient offline from permanent loss (timeouts before repair, as in Carbonite/TotalRecall-era work) avoids wasted repair.
- **Repair bandwidth (Blake–Rodrigues style, my arithmetic).** A node storing S bytes with mean lifetime T forces ≈S/T of re-creation traffic. For S=1 TB and T=180 days, that is 64 KB/s ≈ 0.5 Mbps sustained per node. Naive RS repair multiplies this by k (e.g. ~5 Mbps for k=10), which competes with home upload links. Mitigations:
  - LRC local groups (cut the read factor to the group size),
  - MSR/Clay (~3x less),
  - Red Stuff (O(S/n) per lost sliver),
  - lazy repair (repair only at threshold m, then rebuild many fragments per stripe read, amortizing the k-fragment download).
- **Design implication.** Cap the storage per node relative to its expected lifetime and uplink (S/T must stay within a fraction of uplink). Require minimum uptime or tenure before a node holds durable fragments, as Storj vetting does.

### Gaps
- I could not fetch the exact Storj §2.5 durability derivation or Storj's published churn rates (fetch failed).
- I found no 2025–2026 measurement of home-device permanent-departure rates. Old Gnutella/Overnet/Kad studies (2002–2007) are the main data and are dated.
- I did not verify Walrus mainnet performance numbers (repair traffic observed in production).

---

## 2. Proofs of storage, retrievability, and data availability

### Takeaway
The proof spectrum runs from cheap private audits to expensive public proofs. Storj and Sia use cheap, verifier-private audits: random spot-checks, Merkle proofs, RS consistency. Filecoin uses heavy, publicly verifiable proofs: PoRep sealing plus WindowPoSt SNARKs, with NI-PoRep (FIP-0092) removing on-chain interaction. Arweave makes miners prove random access to archive chunks (SPoRA). Ethereum PeerDAS (live since Dec 2025) shows data availability sampling at scale. A consumer system with a semi-trusted coordinator can use Merkle/RS spot-check audits plus Walrus-style asynchronous challenges. SNARK-based proofs are only worth it if verification must be trustless and on-chain.

### Cited Findings
- (SEMINAL, 2007) Proofs of Retrievability (PoR): Juels & Kaliski, CCS 2007, using sentinels plus error correction. Provable Data Possession (PDP): Ateniese et al., CCS 2007, using homomorphic tags and spot-checking random blocks to detect deletion with high probability. Compact PoR: Shacham & Waters, Asiacrypt 2008, with BLS-based publicly verifiable aggregates. [seminal/known; not re-fetched] — [Shacham–Waters ePrint 2008/073](https://eprint.iacr.org/2008/073); [Ateniese et al. ePrint 2007/202](https://eprint.iacr.org/2007/202)
- Filecoin NI-PoRep (FIP-0092, accepted, supersedes FIP-0090):
  - Storage providers generate PoRep challenges locally instead of from on-chain randomness.
  - This needs more challenges per SDR layer (2268 vs 180) to keep the same security.
  - It applies only to Committed Capacity (no client data) sectors and is optional.
  - Goals: a simpler onboarding pipeline and outsourced proving.
  - — [FIP-0092](https://github.com/filecoin-project/FIPs/blob/master/FIPS/fip-0092.md)
- Filecoin background [known]: PoRep (Stacked DRG "SDR" sealing, which is slow and costly by design so a provider cannot re-seal on demand) proves a unique physical replica. WindowPoSt proves continued storage every 24h deadline window. WinningPoSt is used for leader election. Proofs are Groth16 SNARKs. — [Filecoin spec / FIPs repo](https://github.com/filecoin-project/FIPs)
- Arweave SPoRA (Succinct Proofs of Random Access): to mine, a node must prove access to random historical chunks, which rewards keeping as much of the archive as possible. One source estimates ~200 replicas of the dataset (2025 blog, possibly outdated). — [Arweave docs](https://docs.arweave.org/developers/development/overview); [blockeden comparison](https://blockeden.xyz/blog/2025/09/23/decentralized-storage-services/)
  - Arweave has since moved to "SPoRes" / Arweave 2.6+ with VDF-paced hashing to limit the advantage of fast storage. [known; not re-fetched]
- Ethereum PeerDAS (EIP-7594) activated with the Fusaka fork on mainnet at slot 13,164,544, Dec 3 2025:
  - Nodes custody a subset of erasure-extended blob columns ("custody groups") and sample random pieces instead of downloading whole blobs.
  - Blob-Parameter-Only (BPO) forks then raise the blob target/max (10/15, later 14/21).
  - Up to ~8x theoretical blob throughput.
  - — [Ethereum Foundation Fusaka announcement](https://blog.ethereum.org/2025/11/06/fusaka-mainnet-announcement); [Migalabs](https://www.migalabs.io/eth-academy/en/evolution/fusaka)
  - One secondary source dated activation "mid-2026", which conflicts with the EF announcement and Migalabs (likely an error). — [Ryder](https://ryder.id/blogs/post/ethereum-fusaka-upgrade-what-peerdas-changes-for-you)
- DAS (SEMINAL, 2018) Al-Bassam, Sonnino, Buterin, "Fraud and Data Availability Proofs": 2D RS plus light-client sampling. Celestia productionized it. [seminal/known] — [arXiv 1809.09044](https://arxiv.org/abs/1809.09044)
- Walrus storage challenges stay sound in asynchronous networks, so delay-based "fetch-on-challenge" cheating fails. — [arXiv v2](https://arxiv.org/html/2505.05370v2)
- Storj audits (whitepaper §3.7) [known; fetch failed]: satellites request random stripes and use Berlekamp–Welch RS error correction across pieces to find nodes returning bad data, with no per-piece tags. Failed audits and uptime feed reputation and disqualification. New nodes are "vetted" with a small share of traffic. Part of payouts is held back early in tenure as escrow. — [Storj whitepaper](https://static.storj.io/storjv3.pdf)
- Sia [known]: hosts submit Merkle storage proofs of a random segment at contract end. Hosts post collateral that is burned on a failed proof. — [Sia docs](https://docs.sia.tech)

### Inferences
- Defend against the "outsourcing/relay" attack (a node fetches data from elsewhere when challenged) with latency bounds (fragile on home links), with sealing (PoRep, costly), or with Walrus-style designs where the challenge itself needs data held locally at a threshold of honest nodes. With semi-trusted devices, plain Merkle spot-checks plus economic penalties are usually enough. **Sybil replication collusion** (one disk claiming to be 3 nodes) is the main threat, and only PoRep-style sealing or identity costs address it.
- PeerDAS's design (column custody plus random sampling plus erasure extension) transfers directly to "is my backup still retrievable" checks by light clients.

### Gaps
- I found no 2026 numbers on Filecoin NI-PoRep adoption or on the cost of sealing per TiB.
- I did not confirm the details of Arweave's current consensus revision.

---

## 3. Encryption, key management, and privacy

### Takeaway
Client-side encryption with random per-file keys is standard. Convergent encryption allows cross-user dedup but leaks file equality and is open to brute-force "learn-remaining-information" attacks. Server-aided MLE (DupLESS) or per-user/per-group dedup are the mitigations. Post-quantum migration in messaging is done in production (Signal PQXDH 2023 → SPQR Triple Ratchet Oct 2025, Apple PQ3 2024), and storage systems should use hybrid ML-KEM-768 + X25519 key wrapping now ("harvest now, decrypt later").

### Cited Findings
- Convergent encryption is vulnerable to:
  - **confirmation-of-file**: anyone holding the plaintext can test whether you store it,
  - **learn-remaining-information** (Perttula, 2008, Tahoe-LAFS): brute-force the low-entropy fields of a templated document.
  - The Tahoe-LAFS mitigation is an added secret ("convergence secret"), which trades away cross-user dedup.
  - — [Tahoe-LAFS write-up](https://tahoe-lafs.org/hacktahoelafs/drew_perttula.html); [Wikipedia](https://en.wikipedia.org/wiki/Convergent_encryption)
- (SEMINAL, 2013) Bellare, Keelveedhi, Ristenpart: message-locked encryption is "inherently subject to brute-force attacks that can recover files falling into a known set". **DupLESS** gets keys from a key server via an oblivious PRF, so brute force needs rate-limited online queries. — [ePrint 2013/429](https://eprint.iacr.org/2013/429); [USENIX Sec'13](https://usenix.org/conference/usenixsecurity13/technical-sessions/presentation/bellare)
- Signal SPQR (announced Oct 2 2025):
  - Adds a Sparse Post-Quantum Ratchet based on ML-KEM-768 alongside the Double Ratchet ("Triple Ratchet"), mixing both outputs in a KDF.
  - Large KEM keys and ciphertexts are chunked across messages with erasure coding.
  - Downgrades to old clients are authenticated.
  - Based on Eurocrypt 2025 and USENIX Security 2025 papers, formally analyzed by Cryspen.
  - — [Signal blog](https://signal.org/blog/spqr/); [ePrint 2025/078](https://eprint.iacr.org/2025/078.pdf); [PQShield](https://pqshield.com/?p=9081)
- Apple iMessage PQ3 (2024) mixes Kyber-768 secrets into the root key for ongoing rekeying. — [Dodis et al. analysis](https://cs.nyu.edu/~dodis/ps/migrating.pdf); [Quarkslab](https://blog.quarkslab.com/triple-threat-signals-ratchet-goes-post-quantum.html)
- (SEMINAL, 1979) Shamir secret sharing: t-of-n threshold over a finite field, information-theoretically secure. It is the basis of social-recovery schemes. [seminal/known] — [Shamir, CACM 1979](https://dl.acm.org/doi/10.1145/359168.359176)

### Inferences
- **Recommended crypto stack.**
  - Per-file random DEK (AES-256-GCM or XChaCha20-Poly1305, chunked/streaming as in age/STREAM).
  - DEKs wrapped by a per-user KEK using hybrid X25519+ML-KEM-768. Symmetric crypto at 256-bit is already PQ-safe.
  - Erasure-code *after* encryption, so fragments reveal nothing.
  - Use content addressing over ciphertext.
  - Dedup only within a user or trust group, or use DupLESS-style OPRF dedup if cross-user savings matter.
- **Consumer key recovery options** (layer several):
  - passkeys / platform-synced keys (WebAuthn PRF extension to derive a wrapping key),
  - a printed recovery code,
  - Shamir t-of-n among trusted contacts or devices (social recovery),
  - hardware-backed escrow with rate-limited HSM PIN guessing (Signal SVR / WhatsApp HSM backups / iCloud Advanced Data Protection model).
- **Metadata privacy is the weak point.** Sizes, access timing, and the device↔fragment graph leak. Mitigations: fixed-size padded chunks, mixing reads through relays, and PIR/ORAM for highly sensitive use cases (expensive).

### Gaps
- I did not search the 2026 status of passkey-PRF support across browsers, of Signal SVR3, or of Apple ADP rollout. These are worth checking for the consumer-recovery design.
- I did not retrieve 2025–2026 ORAM/PIR performance numbers (e.g. SimplePIR/YPIR).

---

## 4. Content addressing and sync

### Takeaway
Merkle DAGs with self-describing content IDs (IPFS CIDs/IPLD, BitTorrent v2 per-file SHA-256 Merkle trees) provide integrity against untrusted holders. For syncing replicas of large sets, range-based set reconciliation (Meyer 2022; Negentropy in Nostr NIP-77; Willow's 3D RBSR) is the 2024–2026 practical SOTA: communication is logarithmic in set size and proportional to the difference. Metadata (directory trees, ACLs) fits CRDTs.

### Cited Findings
- Range-Based Set Reconciliation (Meyer, arXiv 2212.13567, 2022/2023): computes set union over a network by recursively partitioning ranges and comparing fingerprints. — [arXiv](https://arxiv.org/pdf/2212.13567)
- Negentropy is the reference RBSR implementation, used in Nostr via NIP-77 for client–relay and relay–relay sync. A 2026 arXiv paper (2603.19820) studies RBSR using range-summarizable order-statistics stores. — [arXiv 2603.19820](https://arxiv.org/pdf/2603.19820); [NIP-77](https://nips.4rs.nl/nips/77)
- Willow uses "3D range-based set reconciliation" over (subspace, path, time). Peers compare fingerprints and split mismatched ranges, which allows sync without a linear log. — [Willow notes](https://jzhao.xyz/thoughts/Willow-Protocol); [Autonomi forum](https://forum.autonomi.community/t/willow-a-p2p-decentralization-protocol/39093)
- [known; not re-fetched]
  - CIDv1 = multibase(version, multicodec, multihash), so hashes and codecs can be upgraded. — [multiformats CID spec](https://github.com/multiformats/cid)
  - BitTorrent v2 (BEP 52) uses per-file SHA-256 Merkle trees with 16 KiB leaves, so identical files dedup across torrents and pieces verify individually. — [BEP 52](https://www.bittorrent.org/beps/bep_0052.html)
  - CRDTs (SEMINAL, Shapiro et al. 2011) converge without coordination. Automerge and Yjs are the mature 2025-era implementations. — [Shapiro et al. INRIA RR-7687](https://inria.hal.science/inria-00609399)

### Inferences
- Use chunk-level content addressing over *ciphertext* (with content-defined chunking such as FastCDC for dedup of edits).
- Use a Merkle DAG for the file manifest, and a signed CRDT log or Willow-style namespace for mutable metadata.
- Use RBSR to sync "which fragments does each node hold" between nodes and the coordinator cheaply.

### Gaps
- I did not verify Willow's spec maturity or implementation status (iroh-willow) as of October 2026.

---

## 5. Incentives and Sybil resistance

### Takeaway
Free-riding is endemic without enforcement. BitTorrent's tit-for-tat works for short-lived swarms but is gameable (BitTyrant). Storage needs *long-term* commitments, so working systems rely on collateral/escrow (Sia, Filecoin, Storj held-back payouts), audits plus reputation with vetting periods, or a trusted coordinator enforcing barter ("give X GB to get Y GB"). Sybil resistance needs an identity cost (stake, sealing, verified accounts, device attestation). Reputation alone does not provide it.

### Cited Findings
- (SEMINAL, 2000) Adar & Huberman, "Free Riding on Gnutella": ~70% of users shared no files, and the top 1% served ~37% of responses. [known] — [First Monday](https://firstmonday.org/ojs/index.php/fm/article/view/792)
- (SEMINAL, 2002) Douceur, "The Sybil Attack": without a central certifying authority, Sybil attacks are always possible except under unrealistic resource-parity assumptions. [known] — [IPTPS 2002 / Microsoft Research](https://www.microsoft.com/en-us/research/publication/the-sybil-attack/)
- (SEMINAL, 2003/2007) Cohen's BitTorrent tit-for-tat with optimistic unchoking. BitTyrant (Piatek et al., NSDI 2007) showed strategic clients gain large speedups by exploiting it. [known] — [NSDI'07 BitTyrant](https://www.usenix.org/conference/nsdi-07/do-incentives-build-robustness-bittorrent)
- (SEMINAL, 2002–2003) Samsara (Cox & Noble, SOSP 2003) and Pastiche/Friendstore-style systems used symmetric storage claims (barter). Samsara used "storage claims" (incompressible placeholder data) that a partner can check, to enforce reciprocal storage. [known] — [SOSP'03 Samsara](https://dl.acm.org/doi/10.1145/945445.945451)
- Storj's held-back payouts and node vetting, and Sia's host collateral burned on failed proofs: see §2 citations — [Storj whitepaper](https://static.storj.io/storjv3.pdf); [Sia docs](https://docs.sia.tech)

### Inferences
- **"Give X GB to get Y GB" barter** is incentive-compatible only if:
  - (a) contributed storage is audited continuously,
  - (b) credits vest over time, which counters "take then leave",
  - (c) the exchange rate accounts for availability and overhead. A node online 50% with expansion 3.5x contributes much less useful capacity than its raw GB, so a sensible rate is credits = raw GB × availability factor ÷ expansion factor.
  - Wuala (2008–2015) ran this model (trade local storage for cloud storage weighted by online time) and later dropped it. [known; not re-fetched; verify]
- For Sybil resistance, cheapest to strongest: verified account plus device attestation (Play Integrity / App Attest) < stake/escrow < PoRep sealing. Placement should spread fragments across distinct ASes, IP prefixes, and accounts so that one Sybil operator holds fewer than n−k fragments of any stripe.

### Gaps
- I did not retrieve current data on Storj node counts or on BitTorrent seeding-ratio economics in 2026.

---

## 6. Verifiable and confidential compute

### Takeaway
As of 2026, TEEs are the only practical way to run arbitrary confidential compute on someone else's hardware. But 2025's physical memory-bus interposer attacks (Battering RAM, WireTap on DDR4; TEE.Fail on DDR5, Oct 2025) broke SGX, TDX, and SEV-SNP against an attacker with physical access and root. That is exactly the "untrusted home device owner" threat model. zkVMs reached real-time Ethereum block proving on ~16 consumer GPUs (2025). This makes verifiable (not confidential) outsourced compute practical, with prover overhead still about 10^4–10^6x. FHE is ~1 ms per TFHE bootstrap on GPUs: practical for narrow workloads, not general compute.

### Cited Findings
- **TEE.Fail (Oct 2025)**:
  - Georgia Tech/Purdue/Synkhronix built a DDR5 memory-bus interposer from off-the-shelf parts for under $1,000.
  - With it they extracted secrets, including **attestation keys**, from fully updated Intel SGX/TDX and AMD SEV-SNP (even with Ciphertext Hiding).
  - The stolen keys also undermine NVIDIA GPU Confidential Computing attestation.
  - Root cause: deterministic AES-XTS memory encryption without integrity/freshness.
  - Requires physical access plus root.
  - Battering RAM and WireTap were the DDR4 predecessors, published weeks earlier.
  - — [The Hacker News](https://thehackernews.com/2025/10/new-teefail-side-channel-attack.html); [BleepingComputer](https://www.bleepingcomputer.com/news/security/teefail-attack-breaks-confidential-computing-on-intel-amd-nvidia-cpus/amp/)
- **SP1 Hypercube (Succinct)**:
  - Proves 99.7% of a random sample of 954 L1 Ethereum blocks in under 12 s and 95.4% in under 10 s, on 16 RTX 5090 GPUs (self-reported).
  - It is a multilinear-polynomial proof system, not univariate STARKs, and is live on mainnet.
  - The EF target (July 2025): under 10 s for 99% of blocks on a rig of at most $100k.
  - — [Succinct: real-time with 16 GPUs](https://blog.succinct.xyz/real-time-proving-16-gpus/); [SP1 Hypercube](https://blog.succinct.xyz/sp1-hypercube/); [mainnet](https://blog.succinct.xyz/sp1-hypercube-is-now-live-on-mainnet/)
- Third-party 2026 overview: OpenVM 2.0 reports 9.8 s P99 Ethereum proving on 8 RTX 5090s. Jolt is still alpha. (I could not verify these against a primary source.) — [Wavect 2026](https://wavect.io/blog/zero-knowledge-proofs-production-2026.md)
- Fenbushi 2025 zkVM benchmark (pre-Hypercube): proving 100 ETH transfers took 7.3 s on RISC Zero GPU vs 13 s on SP1 GPU. — [Fenbushi](https://fenbushi.vc/?p=795)
- **FHE**:
  - TFHE bootstrapping has dropped below 1 ms on H100.
  - Reported throughput is ~189k bootstraps/s across 8×H100 (secondary source).
  - An FHE.org 2026 poster attributes the speedup to multi-bit bootstrapping and GPU thread-block clusters.
  - Zama presented sorting-based bootstrapping speedups at FHE.org 2026 (Taipei).
  - Zama Protocol claims 20+ TPS on CPU, with a roadmap of 500–1,000 TPS on GPU by end-2026 (projection).
  - Intel's HERACLES FHE accelerator was demonstrated in 2026 but remains a research prototype.
  - — [Wavect FHE 2026](https://wavect.io/blog/fully-homomorphic-encryption-practical-2026.md); [FHE.org 2026 poster](https://fhe.org/conferences/conference-2026/resources/posters/%5B07%5D%20-%20Sub-Millisecond%20TFHE%20Bootstrapping%20on%20GPU.pdf?raw=true); [Zama FHE.org 2026](https://www.zama.org/post/zama-at-fhe-org-2026-eight-contributions-from-taipei); [blockeden Zama](https://blockeden.xyz/blog/2026/01/05/zama-protocol/)

### Inferences
- **Do not rely on TEEs on consumer-owned devices against their owners.** The physical attacker is the adversary, and consumer client SGX has been deprecated since 11th-gen Core [known]. TEEs remain reasonable for semi-trusted *datacenter* operators (coordinator, key server for DupLESS/OPRF, recovery HSM).
- **Practical compute ladder for untrusted volunteer devices:**
  1. Redundant execution plus majority vote (BOINC style) for deterministic jobs.
  2. Spot-check verification.
  3. zkVM proofs when the verifier must be trustless. The ~10^4–10^6x prover overhead (my estimate, not sourced) makes this suitable only where verification cost matters more than compute cost.
  4. FHE/MPC only for small kernels (private set intersection, simple aggregates).
- Confidentiality of compute on untrusted devices is essentially unsolved at general-purpose scale. Restrict shared compute to public or encrypted-at-rest data, or to embarrassingly parallel tasks over non-sensitive inputs.

### Gaps
- I found no source on vendor mitigations for TEE.Fail (e.g. integrity-protected memory encryption in future CPUs).
- I found no independent head-to-head zkVM benchmark from 2026.
- I did not retrieve 2026 MPC performance data.

---

## 7. Discovery, routing, and NAT traversal

### Takeaway
Kademlia DHTs (libp2p/IPFS, BitTorrent Mainline) remain standard for decentralized lookup. Direct connectivity between home devices is the practical bottleneck. The largest measurement to date (IMC '26) found libp2p DCUtR hole punching succeeds ~70% ±7% of the time when its prerequisites succeed, with TCP ≈ QUIC. A real system needs relays for the rest (≥30%) plus the prerequisite failures.

### Cited Findings
- "Challenging Tribal Knowledge": large-scale measurement of DCUtR on IPFS (arXiv 2510.27500, IMC '26).
  - Covered 4.4M+ traversal attempts from 85k+ networks in 167 countries.
  - Conditional success was **70% ± 7.1%**, given that relay reservation and public address discovery succeeded. ~29% of data was excluded, so this is not an end-to-end rate.
  - TCP and QUIC success rates are statistically indistinguishable.
  - 97.6% of successes happen on the first attempt.
  - Success does not depend on which relay is chosen.
  - — [arXiv 2510.27500](https://arxiv.org/html/2510.27500v1); [ProbeLab publication](https://probelab.io/publications/large-scale-measurement-of-nat-traversal-for-the-decentralized-web-a-case-study-of-dcutr-in-ipfs/)
- Earlier ProbeLab data (2022): 60–70% success during heterogeneous deployment, ~80% for Go clients, and lower for Rust/TCP and VPN clients. A follow-up per-NAT-type campaign is underway. — [ProbeLab blog](https://probelab.io/blog/can-libp2p-punch-through-nats/); [IPFS þing talk](https://probelab.io/talks/libp2p-nat-hole-punching-success-rate/)
- (SEMINAL, 2002) Maymounkov & Mazières, Kademlia: XOR metric, k-buckets, O(log n) lookups, and a preference for long-lived peers, which suits churn. (SEMINAL, 2005) Ford, Srisuresh & Kegel, "Peer-to-Peer Communication Across NATs" (USENIX ATC 2005), measured UDP hole punching working on ~82% of NATs and TCP on ~64%. [known; not re-fetched] — [Kademlia IPTPS'02](https://pdos.csail.mit.edu/~petar/papers/maymounkov-kademlia-lncs.pdf); [Ford et al. ATC'05](https://www.usenix.org/legacy/event/usenix05/tech/general/full_papers/ford/ford.pdf)

### Inferences
- Budget for **≥30–40% of device pairs needing a relay**: TURN, libp2p circuit-relay-v2, Tailscale DERP-style, or iroh relays.
  - Put relays on always-on nodes or in coordinator infrastructure.
  - Relayed bulk transfer is expensive, so prefer pairing fragments with directly reachable holders and route repair traffic through publicly reachable "super-nodes".
- A pure DHT is slow and Sybil-prone (eclipse attacks). A hybrid with a coordinator/tracker for placement and a DHT as fallback is the pragmatic choice (Storj satellites, Walrus with Sui as control plane).
- IPv6 adoption reduces NAT problems but stateful firewalls still need hole punching.

### Gaps
- The per-NAT-class breakdown is not yet published. I found no 2026 data on CGNAT prevalence (mobile networks are predominantly CGNAT/symmetric, which lowers success).
- I did not search Kademlia variants (S/Kademlia, Double-hashing in IPFS) or 2026 DHT lookup latency measurements.
