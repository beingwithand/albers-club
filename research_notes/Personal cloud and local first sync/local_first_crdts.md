# Local-first software and CRDT-based sync (state as of October 2026)

> Method note: these notes come from about 17 web searches and fetches on 2026-10-16. Several primary sites failed to fetch in this environment (automerge.org, infoq.com, kanopylabs.com returned DNS errors), so some 2026 facts rest on search-result summaries of those pages and are marked as such. Items labelled **[background, not re-verified]** come from the researcher's prior knowledge, which runs to about mid-2026. Each carries the canonical URL, but this session did not re-confirm them; the report writer should treat them as lower confidence.

## 1. Concept: Ink & Switch principles and later work; Local-First Conf and the community, 2024-2026

### Takeaway
The 2019 Ink & Switch essay is still the reference definition. Ink & Switch's later work goes after the hardest remaining gaps. Keyhive (successor to "Beehive") covers access control and E2EE without a trusted server. Automerge 3.0 cut memory use. Subduction is a new Rust peer-to-peer sync protocol bridged into automerge-repo 2.6 alphas (mid-2026). The community has grown into a yearly Berlin conference (3rd edition July 2026; 2027 already scheduled).

### Cited Findings
- **Original essay [background, not re-verified]:** "Local-first software: You own your data, in spite of the cloud" by Kleppmann, Wiggins, van Hardenberg and McGranaghan (Ink & Switch, Onward! 2019). It sets out seven ideals: fast (no spinners), multi-device, offline, seamless collaboration, longevity, privacy, and user control. It names CRDTs as the most promising foundation. — [Ink & Switch essay](https://www.inkandswitch.com/local-first/)
- **Keyhive (local-first access control):** Ink & Switch describes Keyhive as "a project exploring local-first access control" that aims to give collaboration security guarantees "similar to the guarantees of private chat." — [Keyhive notebook](https://www.inkandswitch.com/keyhive/notebook/)
- Core problem framing: cloud apps enforce access through a guard server. Local-first apps have no such network boundary, so access control has to travel with the data. — [Keyhive notebook 00/01](https://www.inkandswitch.com/keyhive/notebook/01/)
- Design (lab note 05): capabilities control write access, and a group key-agreement protocol encrypts writes, which gives read control. The sync focus is a server that only ever holds ciphertext. — [Keyhive notebook 05](https://www.inkandswitch.com/keyhive/notebook/05/)
- Open problems Ink & Switch names: two admins who concurrently revoke each other, and back-dated operations from revoked agents. — [Keyhive notebook](https://www.inkandswitch.com/keyhive/notebook/)
- Predecessor "Beehive" notebook; its latest entry covers group key agreement via "BeeKEM". — [Beehive notebook](https://inkandswitch.com/beehive/notebook)
- **Automerge Repo 2.0** shipped alongside the Automerge 3.0 beta. Ink & Switch calls automerge-repo "the networking and storage adapter library for Automerge." — [Ink & Switch Dispatch 011](https://inkandswitch.com/newsletter/dispatch-011)
- **Subduction:** an Ink & Switch Rust sync protocol for "true peer-to-peer synchronization via pluggable transports (WebSocket, HTTP long-poll, Iroh/QUIC)". The CLI (v0.17.0 on docs.rs) warns "DO NOT use for production use cases at this time." — [GitHub inkandswitch/subduction](https://github.com/inkandswitch/subduction); [docs.rs subduction_cli](https://docs.rs/subduction_cli)
- An npm bridge `@automerge/automerge-repo-subduction-bridge` (version 2.6.0-subduction.0) lets automerge-repo storage and network adapters run over Subduction. — [jsDelivr package](https://www.jsdelivr.com/package/npm/@automerge/automerge-repo-subduction-bridge)
- The "This Month in Automerge: July '26" post (seen via search summary only; the page did not fetch) says the work is available in automerge-repo v2.6.0 alphas. It also covers hardening for long-running sync servers: bounded storage and sync fan-out with configurable concurrency limits. — [Automerge blog, July 2026](https://automerge.org/blog/2026-july/)
- **Patchwork [background, not re-verified]:** Ink & Switch's research into version control (branches, diffs, history) for Automerge-based documents and writing. No 2026 status was found in this session. — [Ink & Switch Patchwork notebook](https://www.inkandswitch.com/patchwork/notebook/)
- Ink & Switch marked its 10th anniversary ("Tenfold") on its site in 2025-26. — [Ink & Switch](https://www.inkandswitch.com/keyhive/notebook/)
- **Local-First Conf 2026:** July 12-14, 2026, Festsaal Kreuzberg, Berlin. July 12-13 were main conference days and day 3 was a lab day hosted by Ink & Switch. Adam Wiggins replaced Chad Fowler as MC. The schedule went live in a June 18, 2026 newsletter. — [Local-First newsletter: schedule live](https://buttondown.com/local-first/archive/conf-schedule-now-live/); [bmann notes](https://bmannconsulting.com/notes/local-first-conf-2026/); [wal.sh](https://wal.sh/events/localfirst-conf-2026)
- Bluesky sponsored the 2026 conference and Paul Frazee spoke, which links the AT Protocol and local-first communities. Tangled (a git-on-ATProto project) also sponsored. — [bmann notes](https://bmannconsulting.com/notes/local-first-conf-2026/) (per search summary)
- Day-3 recordings were published by September 24, 2026. **Local-First Conf 2027 is set for May 25-26, 2027, in Berlin.** — [Local-First newsletter: Day 3 videos & 2027 dates](https://buttondown.com/local-first/archive/day-3-videos-and-2027-conf-dates/)
- A "Local-First Film" was announced in the community newsletter. — [Local-First newsletter](https://buttondown.com/local-first/archive/local-first-film-2026-conf-dates/)
- FOSDEM 2026 included a local-first track or session with a Jazz talk. — [FOSDEM 2026 transcript mirror](https://ftp.fau.de/fosdem/2026/k3201/TDGH7X-local-first.vtt)
- The community directory lofi.so lists projects. — [lofi.so directory](https://lofi.so/directory/projects)
- **Podcast [background, not re-verified]:** localfirst.fm is hosted by Johannes Schickling (also the author of LiveStore). — [localfirst.fm](https://www.localfirst.fm/)

### Inferences
- The research frontier has moved from "can CRDTs merge text?" (largely solved) to infrastructure. Current work targets access control and E2EE (Keyhive), sync protocols and servers (Subduction, hardening long-running sync servers), and version control (Patchwork).
- The Bluesky/ATProto presence at the conference points to "credible exit" and account portability becoming part of the local-first conversation.

### Gaps
- Full 2026 Local-First Conf talk list not retrieved.
- Keyhive release status (whether it ships in automerge-repo production builds yet) and Patchwork's 2026 status not confirmed. The Keyhive notebook pages carry no dates in the results.

## 2. Libraries and frameworks: maturity and adoption

### Takeaway
Two families have split apart. **CRDT document libraries** (Automerge, Yjs, Loro, Diamond Types) are mature for documents and text. **Database sync engines** (Zero, ElectricSQL, PowerSync, Triplit, InstantDB, LiveStore, Jazz) mostly use a server-authoritative or last-write-wins model over Postgres or SQLite rather than true peer-to-peer CRDTs. In 2026, Zero reached 1.0 (June) and Supabase consolidated the space, buying Triplit (Oct 2025) and Turso (Oct 2026).

### Cited Findings
**CRDT libraries**
- **Automerge 3.0:** described as a memory release that cut memory use "by over 10x", in some cases 100x, by keeping the compressed columnar format in memory. It keeps the same file format as Automerge 2. The main breaking change removes the old `Text` class: strings are collaborative by default, and `ImmutableString` is for non-collaborative strings. — [Automerge 3.0 blog](https://automerge.org/blog/automerge-3/); [Dispatch 011](https://inkandswitch.com/newsletter/dispatch-011); [Migration guide](https://automerge.org/docs/guides/migrating-from-automerge-2-to-automerge-3/)
- Secondary report: pasting a novel used about 700 MB in Automerge 2 and about 1.3 MB in 3.0. — [SegmentFault summary](https://segmentfault.com/p/1210000047080269) (secondary)
- **Loro:** v1.0 released October 2024 (blog dated 2024-10-23). It brought a stable encoding format, about 10x faster loading via a new storage format, shallow snapshots, rich text, a Fugue-based text/list CRDT (avoids interleaving), movable list and movable tree types, and Rust/JS (WASM)/Swift bindings. npm showed 1.5.x as a later release. — [Loro v1.0 blog](https://loro.dev/blog/v1.0); [changelog](https://loro.dev/changelog/v1.0.0-beta); [npm loro-crdt](https://npmjs.com/package/loro-crdt)
- **Yjs [background, not re-verified]:** Kevin Jahns's CRDT. It is the most widely deployed in editors, with bindings for ProseMirror/Tiptap, CodeMirror, Monaco, Quill, and Lexical. Hosted services such as Liveblocks and Tiptap Cloud, and self-hosted y-websocket and Hocuspocus, run on it. — [Yjs GitHub](https://github.com/yjs/yjs)
- **Diamond Types / Eg-walker [background, not re-verified]:** Joseph Gentle's Rust text CRDT. The Eg-walker algorithm (Gentle & Kleppmann, arXiv 2024; EuroSys 2025) stores a plain event graph and builds CRDT state only when merging concurrent edits, which gives very low memory and load cost. — [Diamond Types GitHub](https://github.com/josephg/diamond-types); [Eg-walker paper](https://arxiv.org/abs/2409.14252)
- **cr-sqlite [background, not re-verified]:** Matt Wonlaw's CRDT extension for SQLite (convergent replicated tables). Its author joined Rocicorp (Zero), and development of cr-sqlite slowed a lot afterwards. Treat it as low-activity. — [vlcn-io/cr-sqlite](https://github.com/vlcn-io/cr-sqlite)

**Sync engines / "local-first databases"**
- **Zero (Rocicorp):** reached 1.0, its first stable release, in June 2026 after about two years of development. 1.0 was a minor update over 0.26.2, with a mostly symbolic version bump. Its headline addition was a schema-change hook for Supabase. Version 1.8.0 was out by July 13, 2026. Architecture: a stateful "zero-cache" server replicates Postgres through logical replication into a SQLite replica, and the client runs queries in ZQL. Query-driven partial sync with server-authoritative resolution. — [InfoQ, June 2026](https://www.infoq.com/news/2026/06/zero-version-1/) (via search summary; fetch failed); [Star History July 2026](https://www.star-history.com/blog/building-blocks/); [Zero roadmap](https://zero.rocicorp.dev/docs/roadmap); [local-first.com on Zero](https://local-first.com/articles/zero-sync-engine/)
- **ElectricSQL:** Postgres-centric. It streams subsets ("shapes") to clients. Sources disagree on its conflict model: one says CRDT-like, another says last-write-wins. — [trybuildpilot comparison](https://trybuildpilot.com/648-electric-sql-vs-powersync-vs-zero-2026); [Kanopy Labs](https://kanopylabs.com/blog/electric-sql-vs-powersync-vs-livestore-local-first) (secondary, conflicting)
  - [background, not re-verified] In 2024 Electric dropped its earlier CRDT/SQLite "rich-CRDT" system and rewrote itself as a read-path-only HTTP shape-sync engine ("Electric Next"). Electric 1.0 shipped around March 2025, and writes go through the app's own API. It is co-developing TanStack DB as the client-side reactive store. — [electric-sql.com blog](https://electric-sql.com/blog)
- **PowerSync:** reads the Postgres WAL and filters changes through declarative sync rules into client SQLite. It supports Postgres, MongoDB and MySQL backends. Sources disagree on whether it defaults to LWW or developer-defined conflict handling: client writes go to an upload queue that the app's backend applies. One guide calls it "the most production-tested." — [trybuildpilot](https://trybuildpilot.com/648-electric-sql-vs-powersync-vs-zero-2026); [Kanopy Labs](https://kanopylabs.com/blog/electric-sql-vs-powersync-vs-livestore-local-first) (secondary)
- **Triplit:** acquired by Supabase on October 8, 2025. Co-founder Matt Linkous joined Supabase to work on offline-first and third-party integrations. Supabase said it would *not* integrate Triplit directly into its platform and would further open-source and document the codebase. — [Supabase blog: Triplit joins Supabase](https://supabase.com/blog/triplit-joins-supabase); [PitchBook](https://pitchbook.com/profiles/company/463303-99)
- **Supabase acquires Turso (adjacent):** announced October 2, 2026, with a $150M round led by GIC and CapitalG participating. This followed a $500M Series F in June 2026 at a $10.5B valuation. Turso is a Rust rewrite of SQLite plus a platform for millions of small databases, with embedded replicas and offline sync. Turso keeps operating, and founder Glauber Costa joins Supabase. Supabase says about 70% of its new databases are created by agents or AI tools. — [SiliconANGLE](https://siliconangle.com/database-startup-supabase-raises-150m-acquires-turso); [Pulse 2.0](https://pulse2.com/supabase-raises-150-million-and-acquires-turso/); [Verdict](https://www.verdict.co.uk/?p=404137)
- **LiveStore:** an event-sourcing model (an event log materialized into client SQLite). Described as "CRDT-like" in one comparison. — [PkgPulse](https://www.pkgpulse.com/guides/tanstack-db-vs-zero-vs-livestore-sync-engines-2026) (secondary)
- **Jazz:** open-source toolkit for "distributed state", copyright Garden Computing, Inc., created by Anselm Eickhoff. It combines CRDTs ("CoValues") with local-first identity, permissions, and cryptography (group-based E2EE). A 2025 podcast covered a backend shift to direct disk storage. No 2026 version or release was confirmed. — [GitNation talk](https://gitnation.com/contents/local-first-a-crazy-new-way-to-build-apps/video); [JS Jabber 663](https://topenddevs.com/podcasts/javascript-jabber/episodes/revolutionizing-api-syntax-and-schema-management-with-jazz-framework-jsj-663)
- **Recommendations in 2026 comparison blogs:** Zero, Triplit, or InstantDB for new collaborative SaaS. PowerSync or ElectricSQL for existing Postgres backends. TanStack DB as the "safest" reactive client store. — [trybuildpilot](https://trybuildpilot.com/648-electric-sql-vs-powersync-vs-zero-2026); [PkgPulse](https://www.pkgpulse.com/guides/tanstack-db-vs-zero-vs-livestore-sync-engines-2026) (low-authority secondary sources)
- **InstantDB, Evolu, DXOS [background, not re-verified]:**
  - InstantDB: a Firebase-like relational/graph client DB with offline cache and real-time sync, open source, YC-backed. — [instantdb.com](https://www.instantdb.com/)
  - Evolu: TypeScript local-first SQLite with E2EE sync and a self-hostable relay. — [evolu.dev](https://www.evolu.dev/)
  - DXOS: ECHO database plus HALO identity and the "Composer" app, built on Automerge. — [dxos.org](https://dxos.org/)

### Inferences
- What developers now call "local-first" in practice is mostly "sync engine over Postgres" (Zero, Electric, PowerSync). That gives instant UI and offline reads, but the server still owns the data. It falls short of the 2019 essay's longevity and user-control ideals.
- True CRDT, server-optional stacks (Automerge plus repo or Subduction, Yjs, Loro, Jazz) are the ones that can serve user-owned or self-hosted sync.
- Supabase buying Triplit and Turso signals consolidation into BaaS vendors. The AI-agent framing (many small per-agent SQLite DBs) is now a commercial driver alongside offline UX.

### Gaps
- No confirmed 2026 versions for Yjs, ElectricSQL, PowerSync, LiveStore, Jazz, InstantDB, Evolu or DXOS. No adoption metrics such as downloads or production customers were retrieved.
- Licenses for PowerSync and Zero (open source vs source-available) not verified this session.

## 3. End-user apps

### Takeaway
Few mainstream "Google Docs replacements" are truly CRDT local-first. In 2026, Logseq's DB version (beta 2.0.x, July 2026, with E2EE sync and a self-hostable server option) and Anytype (any-sync, self-hostable) are the clearest consumer examples. Obsidian is local-files-first with a proprietary E2EE sync that is not CRDT-based. AFFiNE and AppFlowy are Yjs-based (AppFlowy uses a Rust port) with heavier self-hosting and licensing caveats.

### Cited Findings
- **Logseq DB version:** first public beta on July 13, 2026, tagged 2.0.1. It replaces flat Markdown files with a canonical SQLite store. File-based "Logseq OG" gets maintenance only. — [Kompozy review](https://kompozy.io/reviews/logseq-2-0); [GitClear 2.0.1](https://www.gitclear.com/open_repos/logseq/logseq/release/2.0.1); [Releasebot](https://releasebot.io/updates/logseq/logseq)
- Sync: the March 2026 changelog says a worker-based sync engine with end-to-end encryption replaced the legacy RTC sync. An April 2026 release added a custom sync-server URL, which allows self-hosting. Sync is open to Open Collective sponsors for testing. — [Logseq DB changelog Jan-Mar 2026](https://discuss.logseq.com/t/logseq-db-changelog/30013/35); [Mar-Apr 2026](https://discuss.logseq.com/t/logseq-db-changelog/30013/36)
- "Markdown Mirror" (May 2026): a read-only on-disk Markdown projection of DB graphs. Two-way sync is still in development. Logseq calls the release an early beta, and reviewers warn of data-loss risk and advise backups. — [What's new May 16 2026](https://discuss.logseq.com/t/whats-new-with-logseq-db-may-16th-2026/35020); [Kompozy](https://kompozy.io/reviews/logseq-2-0)
- **Anytype:** local-first, peer-to-peer-capable sync (any-sync, IPFS lineage), released under the "Any Source Available License 1.0", which is source-available rather than OSI open source. — [AFFiNE comparison blog](https://affine.pro/blog/affine-vs-appflowy-vs-anytype) (competitor-authored); [selfhostyourself](https://selfhostyourself.com/alternative-to/anytype)
  - [background, not re-verified] Users can run their own any-sync network (coordinator, sync nodes, file nodes, consensus) via `any-sync-dockercompose`. Spaces are E2EE. — [anyproto/any-sync-dockercompose](https://github.com/anyproto/any-sync-dockercompose)
- **AFFiNE / AppFlowy:**
  - One listing says AFFiNE's self-host edition is MIT and AppFlowy is AGPL-3.0. — [AFFiNE comparison](https://affine.pro/blog/affine-vs-appflowy-vs-anytype)
  - Another claims AFFiNE's backend server is under an Enterprise Edition license with user limits for self-hosted instances. — [quizandsurveymaster](https://quizandsurveymaster.com/8-best-open-source-notion-alternatives-self-hosted-2026/)
  - These licensing claims conflict, so verify them with primary sources. AppFlowy self-hosting is reported to be heavy. — [sliplane](https://sliplane.io/blog/5-awesome-appflowy-alternatives)
  - [background] AFFiNE is built on Yjs (via its "OctoBase"/y-octo Rust port), and AppFlowy uses yrs/Yjs-compatible "collab". — [AFFiNE GitHub](https://github.com/toeverything/AFFiNE); [AppFlowy GitHub](https://github.com/AppFlowy-IO/AppFlowy)
- **[background, not re-verified] Obsidian:** plain Markdown files on local disk. Obsidian Sync is a paid add-on with E2EE (AES-256) and version history, using file-level diff/merge rather than CRDTs. Free for commercial use since early 2025. — [obsidian.md/sync](https://obsidian.md/sync)
- **[background, not re-verified] Actual Budget:** open-sourced in 2022 and community-maintained. It uses a CRDT-style message log with hybrid logical clocks over local SQLite, a self-hostable sync server, and optional E2EE. — [actualbudget.org](https://actualbudget.org/)
- **[background, not re-verified] Excalidraw:** live collaboration rooms are E2EE, with the key held in the URL fragment so the relay server never sees it. — [Excalidraw blog](https://blog.excalidraw.com/end-to-end-encryption/)
- **[background, not re-verified] tldraw:** "tldraw sync" (2024) is a server-authoritative sync engine on Cloudflare Durable Objects rather than a CRDT. The SDK is commercially licensed for production use. — [tldraw.dev](https://tldraw.dev/)
- **[background, not re-verified] Linear:** a proprietary sync engine (an IndexedDB object graph with server-ordered transactions), described in talks by CTO Tuomas Artman. It is the canonical "sync engine" UX inspiration for Zero and others, but not user-owned data. — [Linear sync talk (localfirst.fm ep. with Tuomas Artman)](https://www.localfirst.fm/)
- **[background, not re-verified] Notion offline mode (2025):** pages can be marked for offline availability. Apple Notes syncs via iCloud with offline editing. Neither is local-first in the Ink & Switch sense, because the vendor's cloud remains the authority. — [Notion help: offline](https://www.notion.com/help/guides/working-offline-in-notion-everything-you-need-to-know)

### Inferences
- For a user replacing Google Docs today, the realistic options are:
  - Obsidian with Sync, or a third-party/self-hosted sync plugin, for solo notes.
  - Anytype or Logseq DB (beta) for E2EE plus self-hostable sync.
  - AFFiNE or AppFlowy for Notion-style real-time collaboration.
- None matches Google Docs-grade multi-user rich-text collaboration with comments, suggestions and permissions without a vendor or self-run server.

### Gaps
- No 2026-dated primary confirmation for Obsidian, Anytype, AFFiNE, AppFlowy, Excalidraw, tldraw, Actual or Linear specifics.
- Anytype any-sync 2026 version and self-hosting status not retrieved.

## 4. Hard problems

### Takeaway
Text merging is largely solved: Fugue/Peritext/Eg-walker avoid interleaving, and Automerge 3.0 cut memory. The open problems are systems problems: access control and revocation without a server, E2EE with group keys, schema migration across divergent clients, history and memory growth, data loss in young apps, and the practical need for an always-on relay or sync peer.

### Cited Findings
- **Access control without a server:** there is no network boundary, so access control must travel with the data. Unresolved cases include concurrent mutual revocation by admins and back-dated writes by revoked agents. — [Keyhive notebook](https://www.inkandswitch.com/keyhive/notebook/)
- **E2EE plus sync:** Keyhive pairs capability-based write authorization with group key agreement (BeeKEM) so that sync servers only see ciphertext. — [Keyhive notebook 05](https://www.inkandswitch.com/keyhive/notebook/05/); [Beehive notebook](https://inkandswitch.com/beehive/notebook)
- **Memory and history growth:** Automerge 2 histories "could reach gigabytes" for long-running docs, which motivated 3.0's in-memory compression. — [Automerge 3.0 blog](https://automerge.org/blog/automerge-3/); [Dispatch 011](https://inkandswitch.com/newsletter/dispatch-011)
- Loro answers the same problem with shallow snapshots, which drop old history. — [Loro v1.0](https://loro.dev/blog/v1.0)
- **Rich-text semantics:** Loro's Fugue-based text avoids interleaving of concurrent inserts. — [Loro v1.0](https://loro.dev/blog/v1.0)
  - [background, not re-verified] Ink & Switch's Peritext (2021-22) defined merge semantics for formatting spans (bold, links, comments), and Automerge adopted Peritext-style marks. — [Peritext](https://www.inkandswitch.com/peritext/)
- **Always-on relay/sync peer:** even P2P-first stacks invest in servers. Automerge's July 2026 work hardens "long-running sync servers" (bounded storage, sync fan-out, concurrency limits). Logseq added custom sync-server URLs. Zero needs a stateful zero-cache node. — [Automerge July 2026](https://automerge.org/blog/2026-july/) (via summary); [Logseq changelog](https://discuss.logseq.com/t/logseq-db-changelog/30013/36); [local-first.com on Zero](https://local-first.com/articles/zero-sync-engine/)
- **Data loss / maturity:** the Logseq DB beta carries explicit data-loss warnings, and Subduction is marked not for production. — [Kompozy](https://kompozy.io/reviews/logseq-2-0); [docs.rs subduction_cli](https://docs.rs/subduction_cli)
- **Conflict-model confusion in sync engines:** comparison sources disagree on whether ElectricSQL and PowerSync use CRDT merging, LWW, or app-defined resolution. In practice many engines are server-authoritative, not CRDT. — [trybuildpilot](https://trybuildpilot.com/648-electric-sql-vs-powersync-vs-zero-2026); [Kanopy Labs](https://kanopylabs.com/blog/electric-sql-vs-powersync-vs-livestore-local-first)
- **Schema migration:** Zero 1.0's headline feature was a schema-change hook (for Supabase), which shows schema evolution is still an active pain point. — [InfoQ Zero 1.0](https://www.infoq.com/news/2026/06/zero-version-1/) (via summary)
  - [background, not re-verified] Ink & Switch's Cambria project (2020) explored bidirectional "lenses" for schema evolution between divergent clients. It never became a production library. — [Cambria](https://www.inkandswitch.com/cambria/)

### Inferences
- The "no server needed" ideal has given way to "servers are dumb, replaceable, and ideally can't read your data." Keyhive plus Subduction is the clearest attempt to make that rigorous.
- Revocation in an eventually-consistent system remains fundamentally hard. Expect policy choices (for example, seniority or ordering rules) rather than a universal answer.

### Gaps
- No 2026 primary data on real-world data-loss incidents in CRDT apps.
- No source found on undo/redo semantics or on CRDT handling of comments and suggestions (track changes) in 2026 production editors.

## 5. "Personal sync server you own" for many apps at once

### Takeaway
The "one personal data store for all apps" vision (Solid, remoteStorage, Urbit) still has little consumer traction in 2026. Inrupt focuses on enterprise (joined Accenture's Project Spotlight, June 2026). The more practical routes are per-app self-hostable sync servers (Anytype any-sync, Logseq custom sync URL, Actual server, Evolu relay, Automerge sync servers), plus P2P runtimes like Holepunch Pear/Keet.

### Cited Findings
- **Solid / Inrupt:** Solid is a specification for storing personal data in decentralized "pods". Inrupt joined Accenture's Project Spotlight (startups paired with Global 2000 clients) in an investment of undisclosed size, reported around June 2026. — [ComputerWoche](https://www.computerwoche.de/article/2811637/wie-internet-nutzer-die-volle-datenkontrolle-bekommen-sollen.html)
- Inrupt was founded by Tim Berners-Lee and John Bruce. Its Enterprise Solid Server launched in 2020, with early customers including the UK NHS (older info). — [CSO Online (2020)](https://www.csoonline.com/article/3608928/inrupt-offers-a-standard-for-controlling-data-and-identity-on-the-web.html); [Solid project feed](https://solidproject.org/feed.xml)
- **Per-app self-hosting as the de facto "own your sync server":** Logseq lets users set a custom sync-server URL (April 2026). Automerge is hardening generic sync servers that any Automerge app can share. — [Logseq changelog](https://discuss.logseq.com/t/logseq-db-changelog/30013/36); [Automerge July 2026](https://automerge.org/blog/2026-july/) (via summary)
- **[background, not re-verified] Generic personal servers:**
  - **remoteStorage:** an IETF Internet-Draft protocol where apps store per-user data on a server of the user's choice (unhosted web apps). Low adoption. — [remotestorage.io](https://remotestorage.io/)
  - **Urbit:** a personal-server OS ("ship") hosting many apps. Niche. — [urbit.org](https://urbit.org/)
  - **Holepunch:** builds the Hypercore stack, Keet (P2P video and chat with no servers), and Pear (a P2P app runtime launched 2024 for distributing and running serverless apps). Persistent availability depends on peers or "blind" seeders/relays. — [holepunch.to](https://holepunch.to/); [pears.com](https://pears.com/)
  - **Automerge's sync server:** a generic store-and-forward peer that any automerge-repo app can point at. It is the closest CRDT-native analogue to a "personal sync server". — [automerge-repo-sync-server](https://github.com/automerge/automerge-repo-sync-server)

### Inferences
- An always-on peer is unavoidable when devices are rarely online at the same time. The market answer in 2026 is either vendor relays that can be E2EE (Obsidian Sync, Anytype, Logseq), self-hosted per-app servers, or protocol-generic relays (Automerge sync server, Keyhive-encrypted Subduction peers).
- A single cross-app personal sync server remains unrealized at consumer scale. Automerge plus Keyhive is the most credible technical path, but it was still pre-production as of mid-2026.

### Gaps
- No 2026 sources retrieved on Holepunch/Keet/Pear, remoteStorage, or Urbit. The search for Holepunch returned irrelevant hole-punch product pages.
- No adoption numbers for Solid pods.
