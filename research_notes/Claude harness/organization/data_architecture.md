# Data architecture for the "log everything" harness (research notes, 2026-10-16)

Scope: the storage, query, privacy and sync design for `$HARNESS_DATA` (git-synced) and `~/msg-vault`
(local-only), as used by Claude Code agents on a Mac. This proposes a target design and a migration path
from the layout described in `claude-harness/schema/STORAGE.md` and `schema/ontology.yaml` (v0.2.0).

Harness files read first: `schema/ontology.yaml`, `schema/STORAGE.md`, `schema/event.md`,
`scripts/autocommit_data.sh`, `hooks/_common.py` (`append_event`), `hooks/log_event.py`, `docs/BACKUP.md`,
`research_notes/Claude harness/intent/live_hook_id_test.md`.

Verification legend: **[V]** checked this session (package registry or git tag, cloned source, or an
official page in search results); **[S]** search snippets or third-party pages only; **[M]** from memory
or my own inference, so check before relying on it.

Repos cloned read-only (nothing run) under
`/tmp/claude-0/-home-user-albers-club/1397d302-c3cb-5329-ad06-e45b2c66c6d1/scratchpad/dataarch/`:
`timelinize` (last commit 2026-05-21), `HPI` (karlicoss, 2026-10-10), `ducklake` (duckdb/ducklake, 2026-10-16).

Could not reach: WebFetch failed with a DNS error for duckdb.org, ducklake.select, openlineage.io,
beepb00p.xyz and dourish.com (MyLifeBits PDF). The proxy rejected formulae.brew.sh and git.joeyh.name
(git-annex). The `gh` API was not enabled for these repos, so I read version tags with `git ls-remote`
instead. Facts from those sites come from search snippets ([S]) or memory ([M]).

---

## 0. TL;DR (the decisions)

1. **Two kinds of truth, one rule.** Everything that cannot be recomputed is an *append-only log*. That
   covers hook observations, Claude Code transcripts, message exports, and also the assertions people and
   agents make: labels, preferences, pattern status claims, applications and ledger rows. Logs are bronze.
   Everything else (silver tables, gold aggregates, search indexes) is a **projection**. It is never synced
   and never hand-edited, and one command rebuilds it from bronze.
2. **Keep JSONL as the bronze format.** At this scale (MBs per month) JSONL is the right source format.
   It is greppable, diffs and merges line by line in git, and humans and agents can read it. Parquet and
   DuckDB are for *derived* layers only. Do not commit Parquet or `.duckdb` files to git.
3. **Partition bronze by month and host:** `log/YYYY-MM/<host>.jsonl`. Each machine then appends only
   to its own file, so git merges never touch the same file and `merge=union` becomes a safety net rather
   than the mechanism. Git documents that union merge "tends to leave the added lines in random order" and
   can silently re-add or duplicate lines [S].
4. **Each bronze line gets an envelope:** `v` (schema version), `host`, `ik` (an idempotency key from
   source ids, e.g. `cc:<session_id>:<prompt_id>:<hook>:<tool_use_id>`) and `ch` (a content hash).
   Projections dedupe on `ik`. Together with cursors, this gives "exactly-once-ish" ingestion:
   at-least-once append, then dedupe.
5. **Schema evolution is upcasting on read.** Bronze is never rewritten. A versioned upcaster chain
   (`v0→v1→v2`) runs inside the silver build. Additive changes need no new version. A changed meaning
   needs a new version or a new event type (Greg Young's rule) [S].
6. **Query stack:** DuckDB 1.5.6 reads bronze JSONL and writes silver/gold Parquet plus one
   `lake.duckdb`. SQLite 3.53+ serves agents: FTS5 with the `trigram` tokenizer (handles Korean) and
   sqlite-vec 0.1.9 for vectors. DuckLake 1.0 is *optional*, for the vault later, and not needed now.
7. **"Right to forget" inside append-only logs** combines three mechanisms:
   (a) *forgettable payloads*: third-party or sensitive text lives in a deletable vault store, and the
   log keeps an id and hash;
   (b) *crypto-shredding*: per-subject keys for sensitive fields that must sit in git-synced data;
   (c) *redaction tombstones* in `governance/redactions.jsonl`, which every projection applies.
   Plaintext already pushed to GitHub can only be removed by rewriting history, so classify **before**
   the first commit.
8. **Privacy tiers decide sync:** `repo` (harness code), `harness-data` (private GitHub), `vault`
   (local, plus encrypted backup only), `derived` (local cache, rebuildable, not backed up). Keys and
   secrets go in Keychain or 1Password, never in a file tree.
9. **Size budget:** keep the `harness-data` repo under 1 GB packed (GitHub's rule of thumb) and every
   file under 50 MB (GitHub warns at 50 MB and blocks at 100 MB) [S]. Large tool outputs and
   transcripts are vault bronze, and harness-data keeps only digests.
10. **The migration is additive and can be stopped at any phase** (§10). Phase 0 fixes two real bugs
    today: unlocked concurrent appends, and 16-bit id randomness.

---

## 1. What the current design already gets right, and its gaps

**Right:** append-only logs with corrections as new records (`corrects`, `label` events, newest-wins
lines for Pattern, Application and LedgerEntry); a typed ontology that a validator (`schema_check.py`)
enforces; a strict split between the git-synced `harness-data` and the never-synced `msg-vault`;
vault references by id instead of copied bodies; the hourly autocommit with a lock and a rebase guard;
a monthly restore drill. In medallion terms this is already a sound bronze layer plus a contract.
What is missing are the projection layers and the governance mechanics.

**Gaps found while reading the code:**

| # | Gap | Where | Risk | Fix (phase) |
|---|---|---|---|---|
| G1 | `append_event` opens `log/YYYY-MM.jsonl` with `"a"` and **no lock**. Parallel subagents run hooks concurrently, and a line over the stdio buffer (a long pasted prompt) can take several `write()` calls, so lines can interleave [M]. | `hooks/_common.py:170` | Corrupt JSONL lines | `fcntl.flock(LOCK_EX)` around one `os.write` of the encoded line (P0) |
| G2 | The id `evt_YYYYMMDD_HHMMSS_<4 hex>` has only 16 random bits per second. In fan-out bursts of 10+ events in one second, collisions become plausible over a year (birthday bound ≈ n²/2·65536) [M]. | `hooks/log_event.py:121`, `id_pattern` | Two events share one id, and `unique_id` breaks | 8 hex chars (or a ULID); accept `{4,8}` in `id_pattern` (P0) |
| G3 | No idempotency key. A re-run of an importer or a union-merge duplicate gives a new `evt_` id, or the same line twice. | all writers | Double counts in weekly_report and pattern support | `ik` + `ch` envelope fields; dedupe in silver (P1/P3) |
| G4 | One file per month shared by all machines, merged with `union`. Order is random and duplicates or re-added lines are silent [S]. | `autocommit_data.sh` | Wrong order, duplicates | Per-host files (P2); keep union only as a safety net |
| G5 | Full prompt text goes to GitHub. Prompts often carry pasted client text, names, emails. | `log_event.py prompt` | Third-party PII in git history (hard to forget) | Payload routing to the vault (P4) |
| G6 | No projections. Each script (`weekly_report`, `patterns`, `label_events`, `schema_check`, `recent_events`) re-parses raw JSONL its own way, and label folding is re-implemented. | scripts | Inconsistent answers, slow later | One silver build (P3) |
| G7 | No schema version on records. "Old ids with HHMM", `verdict` aliases and `scope_hint` vs `scope` are handled ad hoc. | ontology `value_aliases` | Logic for evolution is spread across readers | `v` field + an upcaster chain (P1) |
| G8 | Nothing captures Claude Code transcripts. `docs/BACKUP.md` says they are covered only by Time Machine and Backblaze. Claude Code deletes old transcripts after `cleanupPeriodDays` (default 30 days, I believe) [M, verify]. | — | The richest bronze source quietly expires | Vault ingest of `~/.claude/projects/**/*.jsonl` with byte-offset cursors (P5), or raise `cleanupPeriodDays` now |
| G9 | No fixity. A file silently truncated or edited in git history is only noticed by chance. | — | Undetected loss | Sealed month manifests + a drill step (P0/P5) |

---

## 2. Research findings that shape the design

### 2.1 Medallion architecture, adapted to one person
Databricks defines the layers as quality levels: bronze (raw), silver (validated), gold (enriched).
The pattern is "a recommended best practice but not a requirement" [S, docs.databricks.com]. Practitioner
guides add that bronze is append-only with load metadata and no transformation, silver dedupes and
validates, and gold holds business-level aggregates [S]. For a personal system the important twist is that
**human and LLM assertions (labels, approvals) are source data, not silver**. A label event cannot be
recomputed from the prompt it labels, so it belongs in bronze next to the observation. Silver is the
*join* of observation and its latest assertions. This matches Perkeep's model (below), where state is a
replay of claims.

### 2.2 Event sourcing and CQRS projections
- *Projections are disposable read models.* Rebuild them by replaying the log. This only stays cheap if
  the build is deterministic (sorted input, stable dedupe rule), so the design requires
  `rebuild twice → identical hashes` as a test.
- **Versioning (Greg Young, *Versioning in an Event Sourced System*, free on Leanpub):** adding a field is
  safe if the new version can be produced from the old. If it cannot, make a new event type. *Upcasting*
  converts old events to the newest shape at read time, so handlers know only one shape. Weak schema
  (tolerate unknown fields, default missing ones) avoids most version bumps [S, InfoQ summary;
  event-driven.io].
- **Forgettable payloads (Verraes 2019):** take the sensitive data out of the event and keep it in a
  separate, access-controlled store referenced by id. Deleting the payload leaves the log intact
  [S, verraes.net]. **Crypto-shredding:** encrypt per-subject data with a per-subject key and delete the
  key to make it unreadable. One caveat: encrypted personal data may still count as personal data under
  GDPR, so the safest option is not to put PII in the log at all [S, multiple]. For a personal system the
  legal question matters less than the *practical* one. A GitHub repo's history, forks, caches and
  backups all keep plaintext, so shredding only works if the data was encrypted before it first left
  the machine.

### 2.3 Local lakehouse: DuckDB, Parquet, DuckLake
- **DuckDB** latest stable is **1.5.6** (2026-09-28) [V, PyPI]. **v2.0** was branched (feature freeze) and
  "projected for the second half of October" 2026. It brings server mode (Quack), a new default storage
  format and "a small number of carefully chosen breaking changes" [S, duckdb.org preview, InfoQ]. Pin
  1.5.x and adopt 2.0 a month after release, once the derived DB can simply be rebuilt.
- **DuckDB encryption:** since 1.4, `ATTACH ... (ENCRYPTION_KEY ...)` encrypts the DB file, the WAL and
  temp files with AES-256-GCM. CVE-2025-64429 (GCM→CTR downgrade by editing the header) affects
  versions before 1.4.2. The DuckDB team says it "does not yet meet the official NIST requirements".
  `LOAD httpfs` uses OpenSSL for speed [S, duckdb.org 2025-11-19 blog, SentinelOne].
- **DuckLake 1.0** shipped 2026-04-13 with DuckDB 1.5.2. It promises backward compatibility, keeps
  catalog metadata in SQL (SQLite, PostgreSQL or DuckDB catalogs) and data in Parquet, and adds *data
  inlining* for small writes, sorted tables, bucket partitioning, deletion vectors and an `ENCRYPTED` flag
  (a Parquet key per file, stored in the catalog) [S, duckdb.org/ducklake.select, InfoQ]. The cloned source
  confirms the maintenance functions `ducklake_merge_adjacent_files`, `ducklake_expire_snapshots`,
  `ducklake_cleanup_old_files`, `ducklake_rewrite_data_files` and `ducklake_flush_inlined_data`, and an
  inlining default of **10 rows** (`ducklake_default_data_inlining_row_limit`, 0 disables it) [V, source
  2026-10-16]. Spec 1.1 / extension 2.0 is penciled in for 2026-10-21 (tentative) [S].
  **Verdict:** DuckLake gives snapshots and time travel over *tables you mutate*. Our silver and gold are
  rebuilt rather than mutated, and bronze is JSONL in git, so DuckLake adds moving parts for little gain
  today. Revisit it for the vault silver layer, where encrypted Parquet and time travel over
  ingested-message tables could pay off (Phase 6).
- **Parquet** via DuckDB `COPY ... (FORMAT parquet, PARTITION_BY (...))`. pyarrow is at **26.0.0** and
  polars at **2.0.0** [V, PyPI]. Neither is needed if DuckDB does the work.

### 2.4 SQLite as the serving layer (FTS5 + sqlite-vec)
- SQLite 3.53.x is current (3.53.3 on 2026-06-26), and a 3.54.0 entry dated 2026-10-15 appears on a draft
  page [S, sqlite.org]. Note that the WAL-reset corruption bug was fixed in 3.51.3 and 3.53.0. Use the
  Python that ships SQLite ≥ 3.51.3 [S].
- **FTS5 `trigram` tokenizer** (SQLite ≥ 3.34 [M]) does substring matching that works for Korean, which
  `unicode61` does not segment well. Trigram needs at least 3 characters per query term [M]. Many Korean
  words are 2 syllables, so fall back to `LIKE '%..%'` for 2-char terms. That scan is fine at
  100k–1M rows.
- **sqlite-vec** stable **0.1.9** (2026-03-31). 0.1.10 alphas add ivf/diskann index options [V PyPI; S
  GitHub]. SQLite's own `vec1` is not released yet [S, sqlite forum].
- **Screenpipe** (2026, YC S26) is a working proof of this stack for agent memory: local SQLite + FTS5 +
  media files on disk, exposed to Claude through an MCP server [S].
- **Embeddings leak content.** Text can be partly reconstructed from embeddings [M]. Vault-derived
  embeddings must stay in the vault index.

### 2.5 Schema evolution and data contracts
`ontology.yaml` is already a data contract: types, required fields, enums, refs and formats. What is
missing is a **version per record** plus a **compatibility policy** (§6). CloudEvents 1.0, which I propose
to mirror only loosely, makes `id, source, specversion, type` required and treats `source + id` as the
uniqueness key for dedupe [S]. Our `ik` plays the same role.

### 2.6 Lineage and provenance (OpenLineage)
OpenLineage models a **RunEvent** (`eventType` START/RUNNING/COMPLETE/ABORT/FAIL/OTHER, `eventTime`,
`run.runId` UUID, `job{namespace,name}`, `inputs[]`/`outputs[]` datasets `{namespace,name,facets}`,
`producer`, `schemaURL`) with facets such as `parent` [M; openlineage.io unreachable]. The spec and client
version is **1.54.0** (2026-10-12) [V, PyPI and git tag]. You do not need a lineage server (Marquez) for one
person. **Write OpenLineage-shaped JSONL** for every ingest or build run, so you could adopt the tooling
later, and add **row-level provenance columns** (`_src_file`, `_src_line`, `_run_id`) to every silver row.
The ontology's `coverage.provenance` is already the right idea at type level.

### 2.7 Idempotent ingestion and dedupe
- **Cursor + idempotency key + content hash.** Append first, then advance the cursor (at-least-once).
  A crash between the two re-appends lines, and silver drops them by `ik`. Timelinize does the same at
  scale: `UNIQUE(data_source_id, original_id)`, an `initial_content_hash` for dedupe that survives user
  edits, and a resumable job `checkpoint` (= cursor) [V, `timeline/schema.sql`].
- **Canonical JSON for hashing:** sort keys, use compact separators, UTF-8, and exclude envelope fields
  (`ch`, ingest timestamps). RFC 8785 (JCS) is the formal version [M]. `json.dumps(obj, sort_keys=True,
  separators=(",",":"), ensure_ascii=False)` is enough when floats are rare.
- **Hash choice:** sha256 (stdlib, what Document/Attachment already use). BLAKE3 is faster (Timelinize uses
  it, `blake3` 1.0.11 on PyPI [V]) but not needed at MB scale.

### 2.8 Tombstones and the "resurrection" problem
Timelinize erases a deleted item's columns but **keeps `original_id_hash` so a later re-import does not
bring it back** [V, schema.sql]. This is easy to miss. If you forget a Gmail thread and next month's
backfill re-reads it, it comes back. So every tombstone must keep a *keyed* hash
(HMAC-SHA256 with a vault-held secret) of the source natural key, and ingestors must check it.

### 2.9 Encryption at rest
| Tool | Version [V unless noted] | Use here |
|---|---|---|
| FileVault (APFS) | macOS built-in | Baseline for the whole disk. Protects only when the Mac is off or locked at boot, not against a running agent or malware |
| age | **v1.3.2** (git tag); 1.3 added built-in post-quantum hybrid keys (`age-keygen -pq`, very long `age1pq1…` recipients) and `age-inspect` [S] | Encrypt vault backups and exports; per-subject keys for crypto-shredding of whole files |
| sops | **v3.13.3** (git tag) | Encrypt *values* in YAML/JSON config with age recipients. Good for small structured secrets-adjacent files. Not for logs |
| SQLCipher | **v4.19.0** (git tag; 4.16.0 is on SQLite 3.53.1 [S]) | Optional for `vault/index.sqlite` if the vault is ever on an unencrypted volume |
| DuckDB native | 1.5.x (AES-GCM; needs ≥1.4.2) | `vault/silver/vault.duckdb` with the key from Keychain |
| restic / kopia | **restic v0.19.1**, **kopia v0.23.1** (git tags) | Encrypted, deduplicated offsite backup of the vault with built-in verify (`restic check --read-data-subset`) |

### 2.10 Git for data: limits and alternatives
- **GitHub:** files over 50 MB warn, over 100 MB are blocked; keep repos around 1 GB ("rule of thumb";
  secondary sources cite 5 GB as "strongly recommended" max) [S].
- **Git LFS v3.8.0** [V tag]: needed for binaries only, has a quota, and adds no encryption. Avoid it. There
  should be no binaries in harness-data.
- **git-annex:** content-addressed large files with *encrypted special remotes* (including a git-lfs
  remote combined with gcrypt) [S]. It is powerful but has a learning curve. This is the right tool *if*
  the vault ever needs multi-machine sync. Until then, restic is simpler. (The git-annex host was
  unreachable here.)
- **DVC 3.67.1** [V PyPI]: an ML-pipeline tool. Its stage graph is nice, but it duplicates what `lake.py`
  plus Make would do. Skip it.
- **Dolt v1.88.2** [V tag]: git semantics for SQL tables (branch, merge, diff by row). Interesting for
  *mutable* curated tables (contacts, organizations) if they ever get large. Overkill now.
- **Datasette** stable **0.65.5** (2026-09-17), 1.0 still in alpha (1.0a36) [V PyPI, S]. **sqlite-utils
  4.2.1** [V]. Datasette is the best zero-code browser for `index.sqlite` on localhost.

### 2.11 Lifelogging and personal-data systems: what they learned
- **MyLifeBits (Gordon Bell, Jim Gemmell, MSR 1998–2009; *Total Recall*):** Bell's own verdict on the
  early years was a "big mess … he couldn't do much with". Capture was easy, and retrieval, linking and
  annotation were the real problem. Non-video data grew about 0.5 GB/month by 2006 and nonlinearly, as
  attachments and photo resolution grew [S]. **Lesson:** spend effort on labels, links and retrieval
  (silver/gold, FTS) rather than more capture. Budget for growth.
- **Perkeep (Camlistore):** an immutable content-addressed blob store whose protocol has *no delete
  operation*. Mutable objects are *permanodes* (stable signed anchors) changed by signed *claims*
  (set-, add-, del-attribute), and the state is the ordered replay of claims [S, perkeep.org].
  **Lessons:** (1) our newest-wins lines for Pattern, Application and Encoding are claims, so make the
  replay rule explicit and shared (silver `fold_latest`); (2) deletion bolted on later is hard, so design
  redaction now.
- **Timelinize (Matt Holt, alpha v0.0.27; repo active through 2026-05):** a SQLite index plus files on disk
  "organized by date — no obfuscation or proprietary formats". It warns that the schema changes force
  starting over, so "Always keep your original source data". It dedupes by source id and initial content
  hash, uses tombstones that keep an id hash, and records explicit time uncertainty (`time_offset`,
  `time_uncertainty`) [V, cloned README and schema]. **Lesson:** bronze originals plus rebuildable indexes
  is exactly what lets an unstable schema survive.
- **HPI (karlicoss, "my life in a Python package"):** don't force everything into one database. Keep raw
  exports on the filesystem, put a code layer (one module per source) on top, and cache with `cachew`
  (0.25.20260820 [V]). Accept lag behind real time to gain speed and resilience: "the data is lagging
  behind the 'realtime'. I consider it a necessary sacrifice" [V, cloned README]. **Lesson:** the
  per-source *parser/upcaster code* is the real asset, and the DB is a cache.
- **Solid / Inrupt pods:** I found no evidence of 2025–2026 personal adoption. Coverage is mostly from
  2019–2021 pilots (BBC, NHS, NatWest, Flanders) and skeptical economics [S]. **Lesson:** don't build on
  it. An RDF/JSON-LD *export* of the knowledge graph is enough for interoperability.
- **Rewind → Limitless → (reportedly) Meta; Microsoft Recall; Screenpipe:** cloud lifelog products get
  acquired or change terms, while local-first ones (Screenpipe: SQLite + FTS5 + MCP) give agents
  memory without giving up custody [S; the Meta acquisition is single-source].
- **Personal knowledge graphs (Balog & Kenter 2019; Skjæveland, Balog et al., *AI Open* 2024):** the
  research agenda splits into *population* (extracting personal facts), *representation and management*
  (provenance, access control, evolution) and *utilization* [S, arXiv 2304.09572]. **Lesson:** our
  ontology `relations:` already is a PKG schema. Materialize it as an `edges` table in silver (from `refs`
  fields, `labels_for`, `supersedes` and `derived_from`) with `evidence` and `ts`. No graph DB is needed.

---

## 3. Target layered architecture

```
                 SOURCES                       BRONZE (truth, append-only)              SILVER / GOLD / SERVE (projections)
 Claude Code hooks ─────────────┐   harness-data/log/YYYY-MM/<host>.jsonl ───┐
 Claude Code transcripts ─┐     │   harness-data/{labels,preferences,         │   lake.py build silver  → $LAKE/silver/*.parquet
 Gmail/Viber/Lark/Slack ──┤     └─▶   patterns,applications,research,...}   ├─▶ lake.py build gold    → $LAKE/gold/*.parquet
 Files/Drive (intake) ────┤         harness-data/governance/redactions.jsonl  │   lake.py index         → $LAKE/index.sqlite (FTS5+vec)
                          └───────▶ msg-vault/bronze/<source>/<acct>/YYYY/MM/ ┘   (vault twins of all three live inside msg-vault/)
                                    msg-vault/blobs/sha256/..  payloads.sqlite
```

### 3.1 Directory layout

**`$HARNESS_DATA` (`~/harness-data`, private GitHub, autocommit hourly): bronze + contracts only**
```
log/
  2026-10.jsonl                  # legacy v0 partition, frozen at cutover (never moved or edited)
  2026-11/<host>.jsonl           # bronze events v1: one file per machine per month
labels/                          # existing transient label batches (same privacy as the log)
preferences.jsonl  applications.jsonl  research/ledger.jsonl  style/pairs.jsonl
patterns/{patterns,encodings,meta}.jsonl   finance/ledger.csv   evals/...
                                 # assertion logs: bronze, newest-wins folds defined in the ontology
governance/
  redactions.jsonl               # tombstones (§7.3); small, applied first by every build
lineage/2026-11/<host>.jsonl     # OpenLineage-shaped run events for ingest/build jobs
_manifests/2026-10.sha256        # fixity seal per closed month (sha256sum format)
.gitattributes                   # *.jsonl merge=union (safety net only), finance/*.csv merge=union
.gitignore                       # .autocommit.log, .derived/, *.parquet, *.duckdb, *.sqlite
```

**`$HARNESS_LAKE` (default `~/Library/Caches/harness-lake/`): derived from harness-data, local, rebuildable**
```
staging/events.v1.jsonl          # upcast + validated + deduped (input to DuckDB)
quarantine/YYYY-MM.jsonl         # lines that failed parse/validation, with error and source position
silver/events/month=2026-11/*.parquet
silver/labels_latest.parquet  silver/patterns_latest.parquet  silver/applications_latest.parquet
silver/edges.parquet             # PKG edges (src, rel, dst, ts, evidence, _src_*)
gold/weekly_metrics.parquet  gold/correction_hotspots.parquet  gold/pattern_support.parquet
lake.duckdb                      # views over silver/gold, plus macros
index.sqlite                     # FTS5 (trigram) + sqlite-vec for agent lookup / MCP
build.json                       # input manifest hash, tool versions, output hashes
```
I chose `~/Library/Caches` because derived data should not be backed up or synced. Time Machine skips
some cache locations by default, but which ones I have not verified [M]. Either way, losing this folder
costs one rebuild.

**`~/msg-vault` (mode 700, FileVault; never a git remote): vault bronze plus its own projections**
```
bronze/<source>/<account>/YYYY/MM/   # raw exports as received: .eml, platform JSON, Viber db dumps (zstd ok)
bronze/claude-transcripts/<host>/<project-slug>/<session>.jsonl   # mirrored append-only (G8)
blobs/sha256/ab/cd/<sha256>          # content-addressed attachments and large payloads (write-once)
payloads.sqlite                      # forgettable payloads: id → text (deletable rows; VACUUM after delete)
keys/subjects/<kid>.key              # crypto-shredding keys (one random 32-byte key per subject)
keys/tombstone_hmac.key              # secret for tombstone natural-key HMACs
cursors/<source>-<account>.json      # SyncCursor records (ontology type, already declared)
messages.jsonl threads.jsonl attachments.jsonl   # typed records per ontology (or per <source>/)
silver/vault.duckdb                  # DuckDB-encrypted (ENCRYPTION_KEY from Keychain)
index/vault.sqlite                   # FTS5 + vec over message text (embeddings never leave the vault)
_manifests/                          # fixity seals for bronze months and blob shards
```

### 3.2 File formats and partitioning rules

| Layer | Format | Partition | Write rule |
|---|---|---|---|
| Bronze events | JSONL, UTF-8, one object per line, `\n` | `log/YYYY-MM/<host>.jsonl` (UTC month of `ts`) | `flock` + a single `os.write`; lines ≤ 64 KB (bigger content goes to the vault payload or a blob); never edit |
| Bronze assertions | JSONL / CSV (existing files) | unpartitioned until a file reaches 20 MB, then `name/YYYY.jsonl` | same lock rule |
| Vault bronze | original bytes (eml/json/db) | `<source>/<account>/YYYY/MM/` | write-once; filename = source id, or sha256 when there is none |
| Blobs | raw bytes | `sha256/<2>/<2>/<64>` | write-once; verify the hash after write |
| Silver/Gold | Parquet (zstd) | `month=YYYY-MM` for events; others unpartitioned | full rebuild or month-scoped rebuild; never edited |
| Serving | SQLite (WAL) | single file | rebuilt from silver; agents open it read-only (`mode=ro`) |
| Lineage/manifests | JSONL / `sha256sum` text | by month | append-only / write-once |

Partitioning by **month × host** keeps every bronze file small (target < 20 MB). Merges are free because
each host only writes its own file. Sealing is natural: a month closes at UTC month end plus a 3-day grace
for late writers. A *source* dimension is not needed in harness-data, because almost everything there is
hook- or skill-written. In the vault, source is the first path segment.

### 3.3 Bronze event envelope v1 (additive to `schema/event.md`)
```json
{"v":1, "id":"evt_20261116_143205_ab12cd34", "ts":"2026-11-16T14:32:05Z", "tz":"+09:00",
 "host":"mbp-jw", "src":"cc-hook", "ik":"cc:7f1c..:bd5c4757:UserPromptSubmit:-",
 "ch":"sha256:9b2e...", "type":"prompt", "actor":"me", "session_id":"...", "prompt_id":"bd5c4757",
 "agent_id":null, "tool_use_id":null, "content":null, "content_ref":"vault:payload/pl_01J...",
 "content_len":2381, "content_sha256":"...", "...existing fields...": "..."}
```
- `v`: envelope/schema version (absent = v0 legacy).
- `tz`: the host's offset at write time, kept for time-of-day patterns (Timelinize keeps `time_offset`).
- `src`: the producer (`cc-hook | cc-transcript | skill:<name> | script:<name> | import:<source>`).
- `ik`: the idempotency key from source-native ids. For hooks:
  `cc:<session_id>:<prompt_id>:<hook_event>:<tool_use_id|->`. The live hook test confirmed `prompt_id` is
  on every event and that `tool_use_id` pairs Pre and Post. For skills: `skill:<name>:<session_id>:<seq>`.
  For imports: `<source>:<account>:<native_id>`.
- `ch`: sha256 of the canonical JSON of the record without `ch`. It detects byte-identical duplicates
  from union merges or replays.
- `prompt_id`, `agent_id`, `tool_use_id`: promoted to first-class fields. They give the causal tree
  (prompt → tool → subagent), which `parent_event` can never reconstruct reliably.
- `content_ref`: set when the content was routed to the vault (§7.1). `content` is then null or a short
  redacted excerpt.

---

## 4. Projections and how to rebuild them

One CLI, proposed as `claude-harness/scripts/lake.py` (it does not exist yet), with Make-like targets.
Every target is **deterministic**: it sorts inputs by `(ts, id, _src_file, _src_line)`, records an input
manifest hash in `build.json`, and skips the work when the hash is unchanged.

| Command | Reads | Writes | What it does |
|---|---|---|---|
| `lake.py ingest cc-transcripts` | `~/.claude/projects/**/*.jsonl` | `msg-vault/bronze/claude-transcripts/...`, cursor | Byte-offset cursor per (inode, path); copies new bytes only; detects truncation or rotation by inode or size |
| `lake.py ingest gmail --account acct_x` | connector/API | vault bronze + `messages.jsonl` + cursor | at-least-once append; checks tombstone HMACs before writing |
| `lake.py stage` | bronze (harness-data) + `governance/redactions.jsonl` | `staging/`, `quarantine/` | parse → upcast to the latest `v` → validate (ontology / JSON Schema) → apply redactions → dedupe on `ik` (first `ts` wins), then on `ch` |
| `lake.py build silver` | staging | `silver/*.parquet`, `lake.duckdb` | typed tables; `labels_latest` = newest label per `labels_for`; `fold_latest` for newest-wins stores; `edges` from refs |
| `lake.py build gold` | silver | `gold/*.parquet` | weekly metrics, correction hotspots, pattern support counts and windows, cost by scope/model, fan-out stats |
| `lake.py index` | silver/gold | `index.sqlite` | FTS5 over content/intent/situation/labels; sqlite-vec over embeddings (optional); `events_by_id` lookup |
| `lake.py rebuild [--month YYYY-MM]` | — | all of the above | `rm -rf` the derived output (or the month), then stage → silver → gold → index |
| `lake.py verify` | bronze + manifests | report + `drill` event | recompute sha256 of sealed months and blob shards; diff against `_manifests/`; rebuild twice and compare output hashes |
| `lake.py seal YYYY-MM` | closed month | `_manifests/YYYY-MM.sha256` | run after the grace period; afterwards any byte change to that month is a fixity failure |

Core DuckDB statements (sketch; staging is done in Python so that upcasting, validation and quarantine
stay readable and testable):
```sql
-- silver.events from the upcast, deduped staging file
CREATE OR REPLACE TABLE events AS
SELECT *, strftime(ts::TIMESTAMPTZ, '%Y-%m') AS month
FROM read_json('staging/events.v1.jsonl', format='newline_delimited', union_by_name=true)
WHERE type <> 'label';

-- latest label per event (Perkeep-style claim replay: newest assertion wins)
CREATE OR REPLACE TABLE labels_latest AS
SELECT labels_for AS event_id,
       arg_max(intent, ts) AS intent, arg_max(situation, ts) AS situation,
       arg_max(meta, ts) AS meta, arg_max(labels, ts) AS labels,
       bool_or(is_correction) AS is_correction, max(ts) AS labeled_at
FROM read_json('staging/events.v1.jsonl', format='newline_delimited', union_by_name=true)
WHERE type = 'label' GROUP BY labels_for;

COPY events TO 'silver/events' (FORMAT parquet, COMPRESSION zstd, PARTITION_BY (month), OVERWRITE_OR_IGNORE true);
```
Serving index (SQLite):
```sql
CREATE VIRTUAL TABLE event_fts USING fts5(id UNINDEXED, scope UNINDEXED, content, intent, situation, labels,
                                          tokenize = 'trigram');
-- optional, once an embedding model is chosen (dimension must match the model):
CREATE VIRTUAL TABLE event_vec USING vec0(embedding float[768]);   -- rowid = events rowid
```
Consumers switch from re-parsing raw JSONL to reading silver: `weekly_report.py`, `patterns.py
ladder|meta`, `label_events.py` (unlabeled = events left-anti-join labels_latest) and `recent_events`.
Each keeps its bronze fallback while silver is missing, so a fresh machine still works.

---

## 5. Idempotency, cursors and dedupe (the "exactly-once-ish" contract)

1. **Writers** compute `ik` from source ids and append under `flock`. Retries are always safe.
2. **Ingestors** follow: read from the cursor → append to bronze → `fsync` → write the cursor atomically
   (`write_json_atomic`, already in `_common.py`). A crash in between causes a re-append, and dedupe
   removes it.
3. **Cursors** live with the data they describe: vault sources in `msg-vault/cursors/`, transcript cursors
   per host in `msg-vault/cursors/cc-transcripts-<host>.json`. Cursors are per machine and never in git,
   because a cursor synced from another machine would skip local data.
4. **Dedupe in `stage`:** first on `ik` (keep the earliest `ts`, then the lowest `_src_file,_src_line`),
   then on `ch` (exact duplicates without `ik`, i.e. legacy v0). The counts go to `build.json` and the
   lineage COMPLETE event, so a jump in duplicates is visible.
5. **Legacy v0 lines** get a synthetic `ik = "v0:" + id`. Exact duplicates are caught by `ch`.

---

## 6. Schema versioning policy

- **Two version numbers.** `ontology.yaml version` (semver) describes the contract. The record field `v`
  (an integer) changes **only** when an existing field changes meaning, type or name. Adding an optional
  field is a minor ontology bump and keeps `v`.
- **Compatibility rule:** readers must ignore unknown fields (weak schema) and default missing optional
  ones. Writers must never reuse a field or event-type name with a new meaning. Use a new name and record
  the mapping in `renamed:`.
- **Upcasters** live in one module (`scripts/upcast.py`), one pure function per step
  (`v0_to_v1(rec) -> rec`), with golden-file tests (`tests/upcast/v0/*.jsonl → expected v1`). The
  `stage` step always runs the chain up to the latest version, so silver contains only the latest shape.
  **Bronze is never rewritten.** The one exception is a redaction history rewrite (§7.4), which is a
  governance action, not a schema migration.
- **v0 → v1 (first upcaster):** normalize `verdict` and other `value_aliases`; derive `scope` from
  `scope_hint`; set `host="legacy"`, `src` from the type and writer, `ik="v0:"+id`; parse old `HHMM` ids;
  canonicalize `direction` spellings per store.
- **JSON Schema generation:** `schema_check.py --emit-jsonschema` writes `schema/jsonschema/<type>.v<N>.json`
  from the ontology, so non-Python tools (DuckDB checks, editors) can validate. `jsonschema` 4.26.0 /
  `pydantic` 2.14.1 [V] are options, but the existing hand-written validator is fine.
- **Breaking-change checklist:** new `v`, upcaster, golden test, rebuild in CI on a sample
  (`lake.py rebuild` against `tests/fixtures/harness-data`), STORAGE.md table updated, and a
  `decision` event with the justification.

---

## 7. Privacy: encryption, redaction, forgetting

### 7.1 Classification at write time (forgettable payloads)
The prompt hook (and any skill that writes free text) routes `content` by rule:

| Condition | harness-data line gets | Vault gets |
|---|---|---|
| ≤ 2,000 chars, and no PII detector hit (emails, phone numbers, Korean RRN pattern, IBAN/card, `NDA`/client names from a deny-list) | `content` as now | — |
| otherwise | `content: null`, `content_ref: vault:payload/<id>`, `content_len`, `content_sha256`, an optional redacted excerpt (≤ 200 chars, PII masked) | row in `payloads.sqlite` |

Labeling (`label_events.py`) then reads payloads from the vault locally. The *labels* (intent,
situation, meta) are written by the user or an LLM, are about the user's own work, and go to
harness-data. The labeler prompt must say "no quotes from content". The labels inherit the payload's
privacy only if they quote it.

### 7.2 Crypto-shredding where data must sit in git
For derived records that must sync but mention third parties (Contact, Client, Application
`status_detail`, reviewer quotes), encrypt the sensitive *fields* with a **per-subject** key:
`{"enc":{"kid":"ct-0042","alg":"xchacha20poly1305","aad":"<record id>|<field>","ct":"base64..."}}`.
The keys live in `msg-vault/keys/subjects/<kid>.key`, and one machine-wide Keychain item wraps them. Per
subject, not per record, means "forget client X" is one key deletion. Per-record keys are only for one-off
sensitive notes. Use `cryptography` or PyNaCl in-process. age suits whole files (backups, exports), not
field-level encryption at line rate.
**Honest limit:** copies of the key in Time Machine and Backblaze survive until those backups are pruned
(Backblaze's default retention is 30 days [M]). A shred is complete only after the retention window.
Record that date in the tombstone.

### 7.3 Redaction tombstones
`governance/redactions.jsonl` (append-only, git-synced, no sensitive content in it):
```json
{"id":"red_20261116_ab12cd34","ts":"...","target":"evt_20261003_101500_9f3a",
 "fields":["content"],"method":"payload-delete|shred|mask|history-rewrite",
 "kid":"ct-0042","nk_hmac":"hmac-sha256:...","reason":"right-to-forget: client request",
 "complete_after":"2026-12-16"}
```
`stage` applies these before anything else: it masks or drops the fields and keeps the row skeleton
(type, ts, scope), so counts and patterns survive. Ingestors check `nk_hmac` (the HMAC of the source
natural key) so the item is not re-imported. That is the Timelinize resurrection guard.

### 7.4 When plaintext already reached GitHub
Run `git filter-repo --replace-text` or `--path ... --invert-paths`, then force-push, re-clone on every
machine, and ask GitHub Support to purge cached views if the data was ever in a PR or a fork [M]. That
breaks the append-only promise, so it is reserved for real leaks and logged as a `redaction` with
`method: history-rewrite`. **Do a one-time PII audit of the existing `log/*.jsonl` history now (Phase 4),
while the repo is small** and a rewrite is cheap.

### 7.5 Encryption at rest summary
- Whole disk: FileVault (required; recovery key in 1Password, per BACKUP.md).
- Vault DB files: DuckDB `ENCRYPTION_KEY` for `vault.duckdb` (≥1.4.2), and SQLCipher 4.19.0 *or* plain
  SQLite for `vault.sqlite`. Plain SQLite is acceptable while the vault sits on FileVault, and SQLCipher
  is required if it is ever copied elsewhere.
- Vault backups: restic 0.19.1 (or kopia 0.23.1) to an offsite bucket, with the repository password in
  1Password. That gives a second, independent copy alongside Backblaze's private-key backup.
- Exports and hand-offs: `age -r age1…` (v1.3.2), or `age-keygen -pq` keys for long-lived archives [S].
- Keys from Keychain at run time: `security find-generic-password -s harness-vault -w`. Never in env
  files or the repo.

---

## 8. Sync rules per privacy level

| Level | Location | Git | Cloud | Time Machine / Backblaze | Agents may read | May contain |
|---|---|---|---|---|---|---|
| `repo` | `claude-harness/` | GitHub (private) | — | yes | yes | code, ontology, rubrics, seed patterns; **no personal data** |
| `harness-data` | `~/harness-data` | private GitHub, hourly autocommit, **per-host files** | — | yes | yes | own prompts ≤ rule §7.1, labels, assertions, derived ids, encrypted fields, redaction tombstones, lineage, manifests |
| `vault` | `~/msg-vault` | **never** | only as restic/age ciphertext | yes (encrypted destination) | yes, local only; never paste into a cloud trigger payload | raw messages, transcripts, payloads, attachments, keys, cursors, embeddings of vault text |
| `derived` | `$HARNESS_LAKE`, `msg-vault/{silver,index}` | never (`.gitignore`) | never | not needed (rebuildable) | yes (`index.sqlite` read-only) | projections; inherits the highest privacy of its inputs |
| `local` | `~/.claude/harness-state.json` | never | never | yes | yes | per-machine runtime state |
| secrets | Keychain / 1Password | never | password-manager cloud only | — | via `op read` / `security` at run time | keys, tokens |

Extra rules:
- **A projection inherits its inputs' privacy.** Anything built from vault data stays in the vault tree.
  `lake.py` refuses to write vault-derived tables under `$HARNESS_LAKE`.
- **Autocommit guard:** before `git add -A`, `autocommit_data.sh` should refuse files matching
  `*.parquet|*.duckdb|*.sqlite|*.eml|blobs/` and any single file over 20 MB, plus a fast PII regex over
  the staged diff (the `rg` from BACKUP.md's secrets audit, extended). Exit code 4 means "blocked,
  needs a human".
- Google Drive must never sync `~/harness-data`, `~/msg-vault` or `$HARNESS_LAKE` (BACKUP.md already
  forbids this for git repos).

---

## 9. Size budgets and monitoring

Rough volumes [M; measure in Phase 0 with `du` and `wc -l`]: a prompt event is about 0.5–3 KB; a
session_end is about 0.3 KB; logging every Pre/PostToolUse with digests instead of bodies costs about
0.4 KB each. At 40 sessions/day × 60 tool calls, harness-data grows by roughly 1–1.5 MB/day, which is
about 30–45 MB/month raw and maybe 5–8 MB/month packed in git (JSONL compresses about 6–10× [M]).

| Item | Budget | Action when exceeded |
|---|---|---|
| One bronze file (`log/YYYY-MM/<host>.jsonl`) | < 20 MB (hard stop 45 MB) | roll over to `<host>.2.jsonl` |
| One bronze line | < 64 KB | content → vault payload or blob; the line keeps a digest |
| `harness-data` packed repo (`git count-objects -vH` size-pack) | < 500 MB target, 1 GB ceiling | move closed years to `archive-YYYY` repos (read-only) + keep their manifests |
| Tool responses in harness-data | digest only: `{tool, ok, bytes, sha256}` | full bodies only in vault transcripts |
| `$HARNESS_LAKE` | < 2 GB | it is a cache: `lake.py rebuild` |
| Vault | disk-bound; alert at 50 GB | sealed months → restic; old raw exports zstd-compressed |
| Embeddings | 768 float32 = 3 KB/row → 1M rows ≈ 3 GB | int8/bit quantization in sqlite-vec [M], or embed only labeled/decision events |

`lake.py verify` also prints these numbers and writes them into the `drill` event, so `/retro` sees growth.

---

## 10. Migration plan from the current JSONL layout

Every phase is additive: readers keep working at every step, and each phase can ship alone.

**Phase 0: safety fixes (≈1 hour, no format change)**
1. Tag `pre-lake-v1` in harness-data. Write `_manifests/legacy.sha256` with
   `sha256sum log/*.jsonl *.jsonl patterns/*.jsonl ...`.
2. `_common.append_event`: `fcntl.flock(fd, LOCK_EX)`, then build the full line as bytes and do one
   `os.write`, then unlock. Do the same in every other JSONL writer (patterns.py, style_pairs.py,
   label_events.py, invoice.py csv).
3. Id randomness from 4 to 8 hex (`uuid4().hex[:8]`); ontology `id_pattern` becomes `[0-9a-f]{4,8}$`.
4. `.gitignore` gets `.derived/ *.parquet *.duckdb *.sqlite`. Add the size guard to `autocommit_data.sh`.
5. Claude Code settings: raise `cleanupPeriodDays` (e.g. 3650) so transcripts stop expiring before Phase 5
   [M: verify the setting name and default in the current docs].

**Phase 1: envelope v1 (writers only, additive)**
6. Writers add `v:1, host, tz, src, ik, ch` and promote `prompt_id/agent_id/tool_use_id` from the hook
   payload. Add the fields to the ontology `Event.fields` (minor bump to 0.3.0) and to `event.md`.
7. `scripts/upcast.py` with `v0_to_v1` + golden tests. `schema_check.py` validates through the upcaster.

**Phase 2: per-host partitions**
8. New writes go to `log/YYYY-MM/<host>.jsonl`, with `host` from `scutil --get LocalHostName`, slugified.
9. Readers glob both `log/*.jsonl` (legacy) and `log/*/*.jsonl`: `_common.recent_events`,
   `weekly_report.py`, `label_events.py`, `schema_check.py`, `patterns.py`, and `STORAGE.md` /
   ontology `path` (it becomes `log/YYYY-MM/<host>.jsonl`, with legacy `log/YYYY-MM.jsonl`).
10. Leave the legacy files in place, frozen. Keep `merge=union` as a safety net only.

**Phase 3: projections**
11. `lake.py stage|build silver|build gold|index|rebuild|verify` with DuckDB 1.5.x pinned in
    `requirements-lake.txt` (`duckdb==1.5.6`, `sqlite-vec==0.1.9`).
12. Port the consumers to silver with a bronze fallback. Add a test that a double rebuild gives
    identical output hashes. Make `lineage/` JSONL a side effect of every build.
13. Optional: `datasette $HARNESS_LAKE/index.sqlite` (0.65.5) on localhost for browsing, or a tiny MCP
    tool over `index.sqlite` (read-only) so agents query history instead of grepping JSONL.

**Phase 4: privacy mechanics**
14. A one-time PII audit of the harness-data history (`git log -p | rg` for emails, phone numbers, RRN,
    client deny-list). If anything is found, `git filter-repo` now and log a `redaction`.
15. Payload routing in the prompt hook (§7.1), `payloads.sqlite` in the vault, `governance/redactions.jsonl`
    and its application in `stage`; per-subject field encryption for Contact, Client and Application
    details when those stores move from `planned` to `active`.

**Phase 5: vault bronze**
16. `lake.py ingest cc-transcripts`, then Gmail and the others per `docs/MESSAGING.md`, into
    `msg-vault/bronze/...` with cursors, blobs/CAS, tombstone checks and an encrypted `vault.duckdb` and
    `vault.sqlite` index.
17. restic to an offsite bucket. Monthly `lake.py verify` + `restic check --read-data-subset=5%` join the
    BACKUP.md drill and are logged as a `drill` event.

**Phase 6: optional, when needed**
18. DuckLake (ENCRYPTED, SQLite catalog) for vault silver, if time travel over ingested tables becomes
    useful. Wait at least a month after spec 1.1 / extension 2.0 (tentatively 2026-10-21).
19. DuckDB 2.0 about a month after release. The derived DBs are rebuilt, never migrated.
20. git-annex with an encrypted special remote, only if the vault must exist on a second Mac.

**Rollback:** phases 1–3 can be undone by reverting the code. Bronze stays readable by the old readers
(new fields are ignored), and derived folders can be deleted.

---

## 11. Reference tool versions (checked 2026-10-16)

| Tool | Version | Date | Check | Role |
|---|---|---|---|---|
| DuckDB (Python) | 1.5.6 | 2026-09-28 | [V PyPI] | build silver/gold; 2.0 due late Oct 2026 [S] |
| DuckLake | 1.0 spec (DuckDB ≥1.5.2) | 2026-04-13 | [S]; source [V] | optional (Phase 6) |
| SQLite | 3.53.3 (3.54.0 draft) | 2026-06-26 / 10-15 | [S] | serving index |
| sqlite-vec | 0.1.9 (0.1.10-alpha.4) | 2026-03-31 | [V PyPI] | vectors |
| SQLCipher | v4.19.0 | — | [V tag] | optional vault index encryption |
| age | v1.3.2 | — | [V tag] | file encryption, backups |
| sops | v3.13.3 | — | [V tag] | encrypted config values |
| restic / kopia | v0.19.1 / v0.23.1 | — | [V tag] | vault offsite + fixity |
| rclone | v1.75.2 | — | [V tag] | optional transport |
| OpenLineage (python) | 1.54.0 | 2026-10-12 | [V PyPI + tag] | lineage event shape |
| Datasette / sqlite-utils | 0.65.5 (1.0a36) / 4.2.1 | 2026-09-17 / 08-13 | [V PyPI] | browse/build SQLite |
| Dolt | v1.88.2 | — | [V tag] | not now |
| DVC | 3.67.1 | 2026-03-31 | [V PyPI] | not now |
| Git LFS | v3.8.0 | — | [V tag] | avoid |
| pyarrow / polars | 26.0.0 / 2.0.0 | 2026-10 | [V PyPI] | not required |
| blake3 / jsonschema / pydantic | 1.0.11 / 4.26.0 / 2.14.1 | 2026 | [V PyPI] | optional |
| Timelinize | v0.0.27 alpha | ~2025-10; repo active 2026-05 | [S]; repo [V] | reference design |
| HPI / cachew | repo 2026-10-10 / 0.25.20260820 | — | [V] | reference design |

---

## 12. Open questions for the user
1. Should *your own* prompts with client text go to the vault (as §7.1 proposes), or do you accept them
   on private GitHub as today? This is the biggest privacy lever.
2. How many Macs will write logs at the same time? (One Mac means per-host partitioning is cheap insurance.
   Two or more means it is required.)
3. Should the vault ever exist on a second machine? (No: restic only. Yes: consider git-annex.)
4. Embeddings: is a local model (e.g. a multilingual E5 via Ollama) acceptable for vault text? Never send
   vault text to a cloud embedding API.

## Sources
- Databricks, medallion architecture: https://docs.databricks.com/aws/lakehouse/medallion
- DuckLake 1.0: https://duckdb.org/2026/04/13/ducklake-10 · https://www.infoq.com/news/2026/05/ducklake-sql-catalog/ · release calendar https://ducklake.select/release_calendar
- DuckDB 1.5.6: https://duckdb.org/2026/09/28/announcing-duckdb-156 · 2.0 preview https://duckdb.org/2026/08/17/duckdb-20-highlights · https://duckdb.org/2026/09/02/try-duckdb-20-alpha · https://www.infoq.com/news/2026/08/duckdb-v2-distributed/
- DuckDB encryption: https://duckdb.org/2025/11/19/encryption-in-duckdb · CVE-2025-64429 https://www.sentinelone.com/vulnerability-database/cve-2025-64429/ · DuckLake encryption https://ducklake.select/docs/stable/duckdb/advanced_features/encryption
- sqlite-vec: https://pypi.org/project/sqlite-vec/ · https://github.com/asg017/sqlite-vec/releases · vec1 status https://sqlite.org/forum/info/4977084c38fec29bcc1ac9e80ad4aaffbdcd5a34daf31bc8fb2530729ed654fa
- SQLite releases: https://sqlite.org/releaselog/3_53_3.html · https://sqlite.org/releaselog/3_53_0.html · https://sqlite.org/draft/changes.html
- SQLCipher: https://www.zetetic.net/blog/2026/05/12/sqlcipher-4.16.0-release/
- age 1.3: https://pkg.go.dev/filippo.io/age@v1.3.1 · https://discuss.privacyguides.net/t/age-v1-3-0-post-quantum-and-more-released/34254
- Greg Young, Versioning in an Event Sourced System: https://leanpub.com/read/esversioning · https://www.infoq.com/news/2017/07/versioning-event-sourcing · https://event-driven.io/en/simple_events_versioning_patterns/
- Verraes, Forgettable Payloads: https://verraes.net/2019/05/eventsourcing-patterns-forgettable-payloads/ · crypto-shredding https://www.kurrent.io/blog/protecting-sensitive-data-in-event-sourced-systems-with-crypto-shredding-1 · https://medium.com/@przemyslaw.rafal.jez/you-cant-delete-an-event-so-how-do-you-honor-gdpr-erasure-84445bdaf2ec
- CloudEvents attributes (secondary): https://jdriven.com/blog/2024/07/A-first-look-at-CloudEvents/
- git union merge caveats: https://phabricator.wikimedia.org/T201514 · https://apache.googlesource.com/calcite/+/refs/heads/site/.gitattributes
- GitHub size limits (secondary): https://fast.io/resources/github-file-size-limit-guide.md · https://gitprotect.io/blog/?p=2355
- git-annex encryption: https://ayakael.net/mirrors/git-annex/src/branch/database/doc/encryption.mdwn
- Datasette 1.0a36: https://simonwillison.net/2026/Jul/7/datasette/
- MyLifeBits / Total Recall: https://www.microsoft.com/en-us/research/?p=184614 · https://www.dourish.com/classes/readings/Gemmell-MyLifeBits.pdf (unreachable here)
- Perkeep: https://perkeep.org/doc/terms · https://perkeep.org/doc/schema/permanode · https://perkeep.org/doc/schema/keep
- Timelinize: https://github.com/timelinize/timelinize (cloned; `timeline/schema.sql`, README) · releases https://github.com/timelinize/timelinize/releases
- HPI: https://github.com/karlicoss/HPI (cloned; README.org "Why don't you just put everything in a massive database?")
- Solid (dated coverage): https://www.csoonline.com/article/570399/inrupt-offers-a-standard-for-controlling-data-and-identity-on-the-web.html
- Screenpipe: https://screenpipe.com/blog/personal-ai-memory-2026 · https://medium.com/@trelvek/screenpipe-review-2026-a-limitations-first-look-at-always-on-desktop-memory-f21d2497d88c
- PKG: https://arxiv.org/abs/2304.09572 · https://research.google/pubs/pub48375/
- Package registries checked live: pypi.org JSON API (duckdb, sqlite-vec, datasette, sqlite-utils, openlineage-python, dvc, pyarrow, polars, pydantic, jsonschema, blake3, cachew); `git ls-remote --tags` (sops, age, restic, kopia, rclone, dolt, git-lfs, OpenLineage, sqlcipher).
