# Information organization for a lifelong personal AI harness

Research note, 2026-10-16. Question: how should a person who logs *everything* (AI-agent conversations, decisions, corrections, documents, messages, and work across translation, annotation, app development, design and job search) organize it so it stays findable and composable across fields for decades? Like Canopy, where one thought can belong to several families, an item here must be able to cross fields.

Read first (current design): `claude-harness/schema/ontology.yaml` (v0.2.0), `schema/STORAGE.md`, `schema/event.md`, `templates/project/`, `docs/MESSAGING.md`, `docs/BACKUP.md`, `BLUEPRINT.md` §5–6, `scripts/kb.py`, and `research_notes/Claude harness/abstraction/canopy_model.md`.

Evidence markers: **[src]** is backed by a source fetched or searched today (listed at the end). **[known]** comes from established professional literature I know but could not re-fetch today, so check it before you rely on the wording. **[harness]** comes from reading this repo.

---

## 0. The recommendation in one page

1. **Three layers, never mixed** (the OAIS idea, scaled down):
   - **Bits** are immutable and content-addressed (`sha256`).
   - **Records** are typed, carry stable IDs, are append-only, and point at bits.
   - **Views** are generated and disposable: indexes, per-field pages, dashboards, `CLAUDE.md` digests.

   Only records are the source of truth. Views are rebuilt and never hand-edited.
2. **One home, many memberships.** Every item has exactly one *home*, which is its provenance: where it was created or received. The home never changes. An item can carry any number of *fields* (facet values) and *typed links*. Cross-field means more facet values, never copies or moved files.
3. **Separate three things that `scope` now conflates.** These are three different questions:
   - **provenance**: where it came from (fixed, single)
   - **fields**: what domain(s) of work it belongs to (multi)
   - **applies_to**: where a rule or preference should be used (multi)

   Keep `scope` as the legacy single value and add the other two.
4. **Few controlled facets, with a living vocabulary.** There are 6 core facets:
   - `kind` (the type)
   - `fields`
   - `activity`
   - `sensitivity`
   - `status`
   - `retention`

   On top of them sit context refs (`project`, `parties`), linguistic facets (`lang`, `direction`, `register`), and one open `topics` facet whose terms are proposed by the LLM and approved by you, then managed SKOS-style. A term is never deleted: you deprecate it and point to its replacement (`replaced_by`).
5. **IDs:** new records use `<prefix>_<ULID>`, which is opaque, time-sortable and filename-safe. Bits use `sha256:<hex>` (show `sha8` to humans). Legacy IDs stay valid forever. An ID never encodes a classification.
6. **Shallow folders, at most 3 levels below a root.** Folders express only provenance and record streams, never topic. Topic and field navigation comes from generated views.
7. **Retention schedule plus disposition records.** Every record class has a retention rule. Deleting something is itself an event: a tombstone that keeps the ID, the hash, the reason and the authority, and is never silent.
8. **Fixity:** SHA-256 at ingest; a BagIt-style manifest per vault folder; hashes stored apart from the content; a sample checked monthly in the existing restore drill and a full check every quarter; `git fsck` for the repos.
9. **Vocabulary evolution:** the ontology and each vocabulary carry a semver number. Data written under an old vocabulary is mapped at read time (the existing `value_aliases` / `renamed:` pattern, generalized) and never rewritten.
10. **The Canopy rule carries over:** *"The LLM produces claims; deterministic code decides what becomes structural."* Classifiers *propose* facet values as `label` events, and `schema_check` and you *admit* them.

---

## 1. What the current harness already does well, and where it will break

**Already right [harness]:**
- **The record stores are append-only, with explicit `supersedes` / `corrects`.** This is the records-management idea of a fixed record, and the archival idea of never altering evidence.
- **`kb.py register` is a real OAIS ingest.** It runs fingerprint (sha256) → copy to `raw/` → convert → verify (PASS in `log.md`) → archive (Drive link) → `safe-to-delete` only when verified *and* archived.
- **Privacy roots** (`vault` / `harness-data` / `repo` / `local`) are a security classification at the storage level.
- **Derived records point to the vault by ID** and never copy message bodies. This is "single source plus pointers".
- **The ontology is versioned**, has a `renamed:` mapping, and `value_aliases` that are accepted on read while canonical values are written. This is the start of vocabulary-evolution practice.

**Will hurt over decades [harness]:**

| Problem | Where | Why it matters |
|---|---|---|
| `scope` is single-valued: `global \| <area> \| <area>/<project>` | Event, Preference, Lesson, StylePair | A translation test that is *part of* a job application, or a lesson from annotation that applies to translation QA, has to pick one. |
| The area is encoded in the folder path (`<area>/<project>/`), and `weekly_report.py` derives scope from cwd components | BLUEPRINT §6, `scripts/weekly_report.py` | When a classification is in a path, reclassifying means moving files, which breaks every pointer. Classification in paths is the classic deep-tree failure. |
| `areas` mixes kinds of facet: `translation`, `annotation` (activities and markets), `job-search` (a life process), `art`, `code` (crafts), `research`, `personal` (a sphere of life) | `ontology.yaml areas:` | When a facet's values are not mutually exclusive by one principle, Ranganathan's canon of exclusiveness is broken and items fall between values. |
| About 20 ID conventions with mixed separators: `evt_YYYYMMDD_HHMMSS_xxxx`, `D-YYYYMMDD-n`, `L-`, `A-`, `R-`, `INV-`, `app-`, `jl-`, `org-`, `ct-`, `plat-`, `client-`, `acct_`, `msg_`, `pref_`, `rn_`, `pat_`, `sp_`, `ss_`, and `sha8` for documents | `ontology.yaml` | They are hard to parse generically, and some are not unique across machines. An `evt_` ID has only 16 random bits per second, and `D-…-n` needs a counter. |
| Document ID = the first 8 hex digits of sha256 | `kb.py` | That is 32 bits. It is fine per project, but across decades and every project, the chance of a clash reaches 50% at about 77k documents. Keep the full hash as the identity and `sha8` as a display handle only. `kb.py` already stores the full `sha256`. |
| No retention or disposition rules, and no scheduled fixity checks for the vault or Drive originals | STORAGE.md, BACKUP.md | "Log everything" without disposition means that third-party personal data and NDA material accumulate forever, and bit rot goes unseen. |
| Session notes have two homes | STORAGE.md "Known gaps" | Two homes means two sources of truth. |
| Facet values can only be *added*. There are no `deprecated` or `replaced_by` markers on enum values (only `renamed:` for types) | `ontology.yaml enums:` | The vocabulary will drift, and old data will silently mean something different. |

---

## 2. Survey: each discipline, what it would change, and its anti-patterns

### 2.1 Ranganathan: faceted classification, PMEST, Colon Classification

**Core ideas.**
- Colon Classification appeared in 1933. It does not enumerate every compound subject in advance. Instead it breaks a subject into **facets** and synthesizes a class number from them. [src]
- It has five fundamental categories, **PMEST**: [src]
  - **P**ersonality: the focal thing
  - **M**atter: material or property
  - **E**nergy: process or action
  - **S**pace
  - **T**ime
- An example is *"Medicine, Lungs; Tuberculosis: Treatment; X-ray: Research. India '1950"*. [src]
- **Citation order** (a fixed facet order) decides the *one* shelf position, while every facet remains searchable. [known]
- Ranganathan's canons require that values within a facet are **mutually exclusive** and come from **one characteristic of division** (consistency), and that new values can be added without renumbering (hospitality). [known]
- Faceted analysis shaped BC2, PRECIS and faceted thesauri. [src]

**Modern faceted search (Hearst / Flamenco).**
- Expose *hierarchical faceted metadata* both to guide choices and to organize the results of a search. [src]
- Query previews let users *recognize rather than recall* terms, and they avoid empty result sets. [src]
- Users dislike groupings of inconsistent granularity, and strictly hierarchical organization is "impoverished" for this use. [src]

**What it changes here.**
- Map PMEST onto the harness:
  - **P** = `topics` / `project` (what it is about)
  - **M** = `lang` / `direction` / `register` / `format`
  - **E** = `activity` (translate, annotate, review, build, apply…)
  - **S** = source system or place (`provenance.channel`)
  - **T** = `ts`
- Each facet answers *one* question, and `fields` is kept separate from `activity`. "Translation" is both a field and an activity, which is fine because they are different facets.
- Use a **citation order** only to choose the home *folder* of new projects (primary field first). Everything else is query-time.

**Anti-patterns.**
- Facets that mix principles. Today's `areas` is one.
- Too many facets: once there are more than about 7 core facets, people stop filling them in.
- Facets whose values vary wildly in granularity, such as `code` next to `job-search`.
- A notation that encodes facets into IDs: Colon numbers changed with each edition, which is exactly what you must not do with identifiers.

### 2.2 Archival science: provenance, original order, the fonds/series hierarchy, ISAD(G)

**Core ideas.**
- **Respect des fonds / provenance:** keep records grouped by the agent that created or accumulated them, and never mix fonds. [known/src]
- **Original order:** keep the arrangement the creator gave the records, because the order is itself evidence. [src]
- **ISAD(G)** (2nd edition, 2000, still current) has 26 elements in 7 areas, 6 of them essential. [src] Its multilevel rules are:
  - describe from the general to the specific (fonds → series → file → item)
  - give only information relevant to each level
  - link every unit to its parent
  - **non-repetition**: put shared information at the highest level that applies [src]
- **The Australian series system** (Peter Scott, 1966) breaks the single tree. A *series* is described separately from its *agencies*, so one series can have **multiple provenance** and appear in several inventories. This is "becoming even more prevalent with digital records". [src]

**What it changes here.**
- **The home is provenance, not topic.** A message's home is `msg-vault/<source>/<account>`. A session's home is the project or cwd where it ran. The home is recorded once (`provenance:`) and never edited.
- **Raw exports keep their original order.** That means mbox, Takeout, `slackdump` and Viber exports. You never restructure raw bits; you build views. This already matches the vault design.
- **Non-repetition becomes inheritance.** Project `CLAUDE.md` frontmatter declares `fields`, `client`, `sensitivity` and `retention` once, and every record under it inherits them unless it overrides them. That cuts per-record tagging to near zero, which is the main defence against tag fatigue.
- **The series = a record stream.** Examples are `log/`, `style/pairs`, `applications`, and `<source>/messages`. Folders in `harness-data` should be series, not subjects. This mostly already holds.
- **The series system's lesson is that multiple provenance is normal.** A project can serve two fields and two parties. Model this with relations, not by duplicating folders.

**Anti-patterns.**
- Re-filing originals by topic, which destroys evidence.
- Repeating client and sensitivity on every record, so that they drift.
- Forcing one parent when reality has many (the record-group model the series system rejected).

### 2.3 Records in Contexts (RiC-CM 1.0 / RiC-O 1.1)

**Core ideas.**
- The ICA's successor to the ISAD(G) family is a **graph, not a tree**. RiC-CM 1.0 was published 2023-11-30, and RiC-O 1.1 (OWL 2) was released in May 2025 and is recommended for new implementations. [src]
- Entities **[known]**:
  - **RecordResource** (Record, RecordSet, RecordPart)
  - **Instantiation** (a particular carrier or format of a record)
  - **Agent** (Person, Group, Mechanism, which covers software and AI)
  - **Activity**, **Mandate**, **Event**, **Place**, **Date**, **Rule**
- Relations are first-class, can carry dates, and can be reified as `rico:Relation`. 1.1's changes concentrate on RecordResource, Proxy, Instantiation, Date and Relation. [src]
- A record can be included in several record sets, and every relation is "is or was" (time-aware). An example is `isOrWasIncludedIn`. [known]

**What it changes here.**
- **Take the RiC split of record vs instantiation.** A Document record (an intellectual unit) has one or more instantiations: the original `.hwp`, the converted `.md`, the Drive copy, each with its own sha256. `kb.py` today conflates the record with its first file hash.
- **Make relations typed and dated.** Use `{rel, target, since, until, by}`, which says *who* asserted the link: you, or `agent:<name>` with a confidence.
- **Agents include AI.** `rico:Mechanism` is the precedent for treating `agent:librarian`, `claude-opus-…` and hooks as agents with provenance. The `actor` field already does this, so extend it to links.
- **Do not adopt RDF/OWL storage.** Keep JSONL, but use RiC/PROV names in a crosswalk (§4.10) so that an export to a real archive is possible later.

**Anti-pattern.** Building a triple store for one person. The value is in the *concepts*, not the stack.

### 2.4 Records management: ISO 15489-1:2016, retention schedules, disposition

**Core ideas.**
- Create and capture records as evidence of activity. [src]
- Keep their **authenticity, reliability, integrity and useability** as contexts change. [src]
- Records differ from other information through their evidential role and their dependence on metadata. [src]
- Records **[known]**:
  - **appraisal**: decide what to keep, and how long, based on business, legal and community needs
  - **disposition authorities / retention schedules**: rules per record class, not per item
  - **disposition actions**: destroy, transfer, or keep permanently, each documented
  - **legal or administrative holds** suspend disposition
- Records systems should be reliable, secure, compliant, comprehensive and systematic. [src]

**External constraints that apply to this user.**
- **Korean tax records:** books and evidence must be kept **5 years from the statutory filing deadline** of the tax year, and **7 years for 역외거래** (offshore transactions) (국세기본법 §85의3). [src, secondary; confirm on law.go.kr]
  - Income from foreign clients and platforms may count. Ask a tax adviser whether 7 years applies, and default to 7 to be safe.
- **Other people's personal data** (messages, contacts) falls under storage-limitation principles where GDPR or Korea's PIPA reach. Keep data no longer than its purpose needs, and document the retention criteria. Keeping data "just in case" for unspecified purposes is not allowed. [src: ICO, Helbing]
  - A purely personal, household archive may be exempt, but job-search and freelance work are *professional* activity. Treat third-party data as regulated.
- **NDA and platform terms:** annotation platforms often forbid keeping task content at all (already in `docs/LOCAL_ONLY.md`).

**What it changes here.** Add a `retention` facet that is inherited from the record class and the project, plus a `disposition` event type and a `tombstones.jsonl` (§4.8). "Log everything" becomes "capture everything, *keep by schedule*". Derived learning (lessons, style pairs, corrections, decisions) is kept permanently. Raw third-party and client content expires.

**Anti-patterns.**
- Per-item retention decisions, which never get made.
- Silent deletion.
- Keeping everything forever. That is a liability, and it makes search worse.

### 2.5 OAIS (ISO 14721:2025), PREMIS 3.0, NDSA Levels, BagIt, OCFL

**Core ideas.**
- **OAIS** reached its third edition as CCSDS 650.0-M-3 (December 2024) and ISO 14721:2025. [src]
  - Content arrives as a **SIP** (Submission Information Package), is stored as an **AIP** (Archival Information Package: content plus Preservation Description Information, meaning reference, provenance, context, fixity and access rights), and is served as a **DIP** (Dissemination Information Package). [known]
  - The 3rd edition adds **Preservation Objectives**, which make "independently understandable" testable: you state *for whom* and *for what use* each item must stay understandable. [src]
- **PREMIS 3.0** defines four entities: **Object, Event, Agent, Rights**. Fixity is held in `messageDigest`, `messageDigestAlgorithm` and `messageDigestOriginator`. [src]
- **NDSA Levels v2.0:**
  - storage: 2 copies in separate locations, then 3 with one geographically separate [src]
  - fixity: check or generate on ingest → back the fixity information up separately → check on a schedule → repair from copies [src]
  - keep fixity information on storage other than the content [src]
- **BagIt (RFC 8493):** a folder with `data/`, `manifest-sha256.txt` (the payload) and `tagmanifest-sha256.txt` (the metadata), all plain text. [src]
- **OCFL 1.1:** versioned objects, an `inventory.json` per object, content-addressed and self-describing. Fedora 6 uses it. [src]

**What it changes here.**
- **SIP = `inbox/` and the raw ingests. AIP = `raw/` + `manifest.json` + the archived original + fixity. DIP = `wiki/`, `index.md` and views.** The harness already has this shape, so name it and make the AIP rules explicit.
- **Write Preservation Objectives per record class.** For example: "a translation deliverable must be re-openable *and* its glossary decisions traceable in 2045". This tells you which formats to normalize to: Markdown/UTF-8 text, PDF/A, PNG, FLAC, plus the original kept alongside.
- **Make PREMIS events the `log` events.** `intake`, `verification`, `fixity_check`, `migration`, `disposition` and `replication` should be event types with `agent` and `outcome`. Several already exist.
- **NDSA level 3 is the target.**
  - 3 copies: local, Drive or GitHub, and Backblaze. `BACKUP.md` already has this.
  - Fixity values stored separately: the hash manifests of vault content live in `harness-data` (hashes only, no content).
  - Scheduled checks: added to the monthly drill.
- **Use the BagIt layout for vault batches** (`bag-info.txt` plus manifests), so any tool can verify a folder decades from now without the harness.

**Anti-patterns.**
- Hashes stored next to the files they protect, and only there.
- Checking fixity never.
- Converting originals and deleting them without keeping the original instantiation.
- Proprietary-only formats with no normalized copy.

### 2.6 Dublin Core and PROV-O (minimal descriptive and provenance metadata)

**Core ideas.**
- **Dublin Core:** the 15 original elements of 1995 (title, creator, subject, description, publisher, contributor, date, type, format, identifier, source, language, relation, coverage, rights) and **DCMI Metadata Terms**, the recommended superset and basis of ISO 15836-2:2019. [src]
  - It includes refinements: `isPartOf`, `hasVersion` / `isVersionOf`, `replaces` / `isReplacedBy`, `references` and `provenance`. [src]
- **PROV-O:** Entity, Activity, Agent, with `wasGeneratedBy`, `wasAttributedTo`, `wasDerivedFrom`, `wasAssociatedWith` and `wasInformedBy`. [src]
- Note: `dct:isVersionOf` is *not* `prov:wasRevisionOf`; it is hierarchical and has no time direction. [src]

**What it changes here.** Do not add DC fields to records. Publish a **crosswalk** (§4.10) so every type maps onto DC and PROV for export, so that an outside archive, a future app, or Canopy can read the data. Adopt PROV verbs as the names of link types: `derived_from` (already in BLUEPRINT), `generated_by`, `attributed_to`.

**Anti-pattern.** Filling 15 DC fields per item by hand. Derive them instead.

### 2.7 BIBFRAME 2 (library linked data): Work, Instance, Item

**Core ideas.** BIBFRAME 2.0 dates from 2016. [src] It has three levels:
- **Work**: the intellectual content, its creators, language and subject
- **Instance**: a particular published form
- **Item**: a single physical or electronic copy

Around them sit Agents and Subjects, and **relationships between resources rather than monolithic records**. [src] A translation is its own Work, linked by `translationOf`. [known]

**What it changes here.** This is exactly the translation and design workflow:
- **Work** = the source text, or "the Canopy onboarding copy".
- A **translation** = a new Work, `translation_of` → the source Work.
- **Instance** = a version (`_v1`, `_v2`, delivered, client-revised).
- **Item** = a file (the local `.docx`, the Drive copy, the client portal upload), identified by sha256.

The current naming rule `YYYY-MM-DD_<project>_<what>_v<N>.<ext>` is the Instance label. Add `work_id` to Document and Asset so that all versions and translations of one text are found together, across projects and fields. A Korean UI string set for Canopy, its English source, and the job-application portfolio sample that reuses it then become one Work graph.

**Anti-pattern.** Treating each file as a new, unrelated document, which turns version folders and `final_final2` into the only link.

### 2.8 Johnny.Decimal

**Core ideas.**
- At most 10 areas × 10 categories × 100 IDs (`AC.ID`, e.g. `14.21`). [src]
- **Nothing is stored in areas or categories, only in IDs.** [src]
- A deliberately shallow structure (two levels). Granular categories are compressed into broader ones. [src]
- An **index** (the JDex) of every ID, and "standard zeros" such as `00.00` for the index itself. [src]
- You expand one area only when it is forced. [src]

**What it changes here.**
- Take the **constraints**: a hard cap on depth, a small fixed number of top-level buckets, one index file listing every container, and content only at the leaves.
- Do **not** take the numeric IDs. `14.21` *encodes the classification*, so moving an item across fields changes its ID. That is exactly the cross-field problem. Johnny.Decimal assumes one item has one place.
- Do use it for the human-facing Drive tree, where a person browses: there a stable, shallow, numbered top level helps (§4.6).

**Anti-pattern.** Numbering schemes as identity, and running out of room in a category.

### 2.9 PARA (Tiago Forte)

**Core ideas.**
- Four buckets organized by **actionability**: [src]
  - **Projects**: short, with a goal
  - **Areas**: ongoing responsibilities
  - **Resources**: topics of interest
  - **Archives**: anything inactive
- "Just-in-time organization": you file as a side effect of work, not in sessions set aside for it. [src]

**What it changes here.**
- PARA's axis is **lifecycle status**, which is a *facet*, not a folder.
- Use `status: active | dormant | closed | archived` (the existing `project_status` enum) and generate an "Active" view.
- **Don't move projects into an `Archive/` folder.** Moving breaks paths, and paths are pointers in this system.
- "Resources" maps to the knowledge wiki and the `topics` facet.
- Just-in-time filing maps to *inherit from context + LLM-proposed labels + weekly review*, which is the existing `label_events.py` loop.

**Anti-pattern.** Physical moves between P/A/R/A, which means the same item exists at different paths over time, and links rot.

### 2.10 Zettelkasten (Luhmann)

**Core ideas.**
- Each note has a **unique, fixed ID** that is independent of topic. [src]
- Folgezettel IDs such as `21/3d7a` encode *where a line of thought continues or branches*, so that a linear box holds a tree. [src]
- Atomic notes; links are the structure; **hub or structure notes** serve as entry points; the register (index) has few entries per keyword. [known]

**What it changes here.**
- The ID must be fixed and say nothing. Sequence and branching are explicit links (`continues`, `comments_on`, `branches_from`), not ID syntax.
- **Structure notes = generated or curated views.** Examples are `knowledge/index.md` and a per-field `index` page. These *are* the cross-field glue: a hub page "Korean honorifics" can transclude lessons from translation, annotation and Canopy NLP.
- Atomicity matters for composability. Lessons, decisions, preferences and glossary terms are already atomic records, so keep it that way and avoid omnibus notes.

**Anti-patterns.**
- Folgezettel-style semantic IDs in a digital system, because you can't re-parent them.
- Notes that are never linked (orphans). Lint for them.

### 2.11 Folksonomy vs controlled vocabulary (tags)

**Core ideas.**
- Folksonomies are flexible and current, but have **no synonym or homonym control**, and searches have low precision and recall. [src]
- Controlled vocabularies give a navigable semantic structure, but are "bound to a point in time and a point of view". [src]
- Studies find tags *complement* controlled indexing rather than replace it. [src]
- *The cited studies concern shared tagging; I found no study of tag sprawl in personal knowledge management tools.* [src gap]

**What it changes here.** Use a **hybrid with a gate**:
- Free text is allowed in `labels` (the existing field) as *candidates*.
- A weekly pass clusters candidates, including **ko/en synonyms** (`존댓말` ~ `honorifics`). You approve terms into `vocab/topics.yaml` with `pref_label` (en, ko), `alt_labels`, `broader` and `scope_note`.
- Facets other than `topics` are **closed lists**. Only `topics` grows.

**Anti-patterns.**
- **Tag sprawl:**
  - singletons
  - near-duplicates (`job-search`, `jobsearch`, `구직`)
  - a tag that equals the folder name
  - "misc", "todo", "important"
  - more than 5 tags on one item
- Write lint rules for each (§4.11).

### 2.12 Polyhierarchy, thesauri and crosswalks (ISO 25964, SKOS)

**Core ideas.**
- ISO 25964-1 covers thesauri; part 2 covers **mappings** to other vocabularies. [src]
- SKOS mapping properties are `exactMatch`, `closeMatch`, `broadMatch`, `narrowMatch` and `relatedMatch`. `exactMatch` is transitive and a sub-property of `closeMatch`; `closeMatch` is not transitive. [src]
- Polyhierarchy (a concept with two broader concepts) is allowed in thesauri. [known]
- **Deprecation practice:** mark `owl:deprecated true`, link `dct:isReplacedBy` to the successor, keep the concept so old data still resolves, hide it from browsing by default, and add a history note with the version. [src]
- `isReplacedBy` claims succession, not equivalence. [src]

**What it changes here.**
- **Polyhierarchy is how cross-field topics work.** For example, `topic:korean-honorifics` has broader concepts `field:translation` *and* `topic:korean-linguistics`, and is `relatedMatch` to Canopy's `register` axis.
- **Crosswalks are data**, kept in `schema/crosswalks/*.yaml`. They cover:
  - Gmail `kb/*` labels ↔ fields and topics
  - Drive folders ↔ projects
  - Canopy `NoteArchetype` / `ThoughtType` ↔ harness `kind` / `activity`
  - old `areas` ↔ new `fields`
  - platform job categories ↔ `fields`
- Each mapping row carries a SKOS relation, so a `closeMatch` is never treated as an equivalence.

**Anti-patterns.**
- Pretending mappings are 1:1.
- Deleting terms.
- Deep polyhierarchies. Cap the depth at about 3 `broader` hops.

### 2.13 Identifiers: stable IDs, ULID / UUIDv7, content addressing

**Core ideas.**
- *Cool URIs don't change*: leave dates, authors, subjects and extensions out of identifiers, because "URIs don't change: people change them". [src]
- ARK: **persistence is a matter of service**, not syntax; names should be **opaque** so they survive changes of title or owner; separate the stable name from the access location. [src]
- **ULID:** 48-bit millisecond time + 80 random bits; 26 characters in Crockford Base32 (no I, L, O, U); case-insensitive; sorts lexicographically by time; increments monotonically within a millisecond. [src]
- **UUIDv7 (RFC 9562, 2024):** the same 48-bit millisecond prefix, a 36-character hex form, native in databases (PostgreSQL 18 has `uuidv7()`). [src, secondary; the RFC sites were unreachable]
- Both are 128 bits, so a ULID converts to a UUID byte-for-byte for databases (it will not carry the v7 version bits). [known]
- **Content addressing** (git, OCFL, IPFS): the identity *of the bits* is their hash, so duplicates collapse and fixity comes for free. [src/known]
- **Merges and redirects** (Wikidata): merge duplicates, leave a **redirect** from the old ID, and fix links by bot. Splitting is harder than merging. [src]

**What it changes here.** See §4.2. Four rules:
- Record IDs are opaque ULIDs with a type prefix.
- Bits are sha256.
- Human handles (slugs, `D-20261016-1`, `INV-…`) are *aliases* in an `aka` list, never the primary key.
- Merges leave a redirect record.

**Anti-patterns.**
- Semantic IDs (`translation-acme-2026-…`).
- Truncated hashes used as identity.
- Counters that need a central lock (`-n`).
- Renaming an ID.

### 2.14 Single source of truth, many views; multi-membership without duplication

**Core ideas.** Every fact has one authoritative location. Everything else is a reference or a generated view (database normalization, transclusion). Obsidian-style embeds keep one source, but "deleting the source breaks them all". [src] The answer to that is stable IDs and tombstones, not copies.

**The three mechanisms, and when to use each:**

| Mechanism | Use when | Here |
|---|---|---|
| **Facet values** (multi-valued) | The item *belongs to* several fields or categories | `fields: [translation, app-dev]` |
| **Typed links** | The item is *related to* other items | `links: [{rel: derived_from, to: doc_…}]` |
| **Transclusion** (a reference rendered inline) | A view or page needs the item's *content* | `![[lsn_01J…]]` in a wiki or hub page; views render it |
| *(Copy)* | **Only** across a privacy boundary, as a redacted derivative, with `derived_from` | e.g. an Application in harness-data derived from a vault message |

**Anti-patterns.**
- Symlink farms as the *source*. They are fine as a generated view.
- Copy-paste between project wikis.
- Duplicated records that differ only in `scope`.

### 2.15 How taxonomies evolve: versioning, deprecation, mapping

**Core practice [src/known]:**
- Version the scheme.
- Never delete a concept; deprecate it, add `replaced_by`, and add a history note.
- Keep old data as it is and **map at read time**.
- Publish a changelog.
- Treat a split as N new concepts plus a note on the old one, since it cannot be auto-mapped. Treat a merge as a redirect.
- Review on a schedule, with usage evidence.

**What it changes here.** Generalize the existing `renamed:` and `value_aliases` into per-vocabulary entries with:
- `status` (`active` / `deprecated`)
- `since`
- `deprecated_in`
- `replaced_by`
- `split_into`
- `note`

`schema_check` accepts deprecated values with a warning, and views display the canonical value. The weekly report shows facet usage, singleton topics and deprecated-value writes.

---

## 3. Design principles distilled (the "constitution")

1. **Identity is opaque and permanent.** Names, folders, facets and titles can change; IDs cannot.
2. **Provenance is singular and fixed. Membership is plural and revisable.**
3. **Classify the context once, inherit everywhere, override rarely** (ISAD(G) non-repetition).
4. **Folders are for provenance and streams, never for subjects.** At most 3 levels below a root.
5. **Raw bits are never edited or re-arranged.** Derive, normalize, and keep the original instantiation.
6. **Every view is rebuildable from records.** Deleting `views/` loses nothing.
7. **Closed facets are small and principled. The one open facet (`topics`) is gated.**
8. **Nothing disappears silently.** Supersede, deprecate, redirect, or tombstone.
9. **Retention is set by record class.** Delete by schedule, and keep the learning that was derived from what you delete.
10. **Machines propose, deterministic code and you dispose** (the Canopy rule).

---

## 4. The recommended organization system

### 4.1 Layers and the OAIS mapping

```
            ┌──────────────────────── VIEWS (DIP, generated, disposable) ───────────────────────┐
            │ per-field indexes · hub pages · active-projects · CLAUDE.md digests · dashboards  │
            └───────────────▲───────────────────────────────────────────────▲───────────────────┘
                            │ built by scripts/views.py (deterministic)      │
┌───────────────── RECORDS (source of truth, append-only JSONL/MD, ULID ids) ─────────────────┐
│ events · decisions · lessons · preferences · corrections · style pairs · documents · assets │
│ registries (projects, parties, accounts, works) · links · tombstones · fixity results      │
└───────────────▲─────────────────────────────────────────────────────────────────────────────┘
                │ point at bits by sha256 (never copy third-party content across privacy roots)
┌──────────────── BITS (AIP payload, immutable, content-addressed) ───────────────────────────┐
│ msg-vault blobs · project raw/ · Drive originals · deliverable files   (+ BagIt manifests)  │
└─────────────────────────────────────────────────────────────────────────────────────────────┘
   SIP = inbox/, Takeout/mbox drops, export batches  →  ingest (kb.py register / vault ingest)
```

### 4.2 ID scheme

| What | Form | Example | Notes |
|---|---|---|---|
| Any **new** record | `<prefix>_<ULID>` | `lsn_01JA7Q3M8Z9X4K2V6B1C0D5E7F` | Prefix: 2–4 lowercase letters naming the type. The ULID in canonical upper case. Generated locally, needs no coordination, sorts by creation time. |
| **Bits** (any file) | `sha256:<64 hex>` | `sha256:9f2c…` | Identity of content. Display `sha8` (`9f2c41ab`) only in UIs, and resolve it to the full hash. |
| **Human handle** | free, unique within type, listed in `aka: []` | `D-20261016-1`, `INV-2026-014`, `acme-contract` | Kept for readability and for documents that clients see. Never used as a foreign key in new data. |
| **Legacy IDs** | unchanged, valid forever | `evt_20261016_143205_ab12`, `app-…`, `ct-…` | `schema_check` accepts each type's old `id_pattern` *or* the new one. IDs are never rewritten. |
| **Merged duplicates** | redirect record | `{"id":"ct_01…","redirect_to":"ct_01…","ts":…,"by":"me"}` | Readers follow redirects (Wikidata practice). |
| **Projects** | `prj_<ULID>` + slug | `prj_01J… / slug: canopy-ko-l10n` | The folder uses the slug, and the registry maps slug ↔ id. A rename changes the slug and adds the old slug to `aka`. |

Suggested prefixes, extending the current ones and keeping short forms:
- `evt` event
- `dec` decision
- `lsn` lesson
- `prf` preference
- `cor` correction (a correction can stay an `evt`)
- `doc` document (the intellectual unit; its files are sha256)
- `wrk` work (the BIBFRAME Work)
- `ast` asset
- `prj` project
- `pty` party (person, org, client, platform: one registry with a `kind`, see below)
- `acc` account
- `msg` message
- `thr` thread
- `app` application
- `jl` job lead
- `inv` invoice
- `rn` research note
- `pat` / `enc` / `mp` patterns
- `sp` style pair
- `tmb` tombstone
- `lnk` link (only when a link needs its own identity)

*Why ULID over UUIDv7:*
- It is 26 characters and filename-safe without dashes.
- It is easier to read aloud and paste.
- It needs no database.
- It converts to a 128-bit UUID if you ever put it in Postgres or Supabase.

UUIDv7 is the right choice if a database becomes primary.

*One caution:* both forms leak the creation time. Don't put record IDs in anything you show a client or employer when that would reveal timing. Use the human handle there.

*Consolidation option:* Client, Organization, Contact and Platform are four "planned" types. Make them one **Party** registry (`pty_`, `kind: person|org|platform|client-role`) with roles as relations (`client_of`, `employer_of`, `works_at`). An org that is both a platform and a client is then one record, not two. This is the RiC/PROV Agent idea.

### 4.3 Facets and controlled values

Facets live in `claude-harness/schema/vocab/<facet>.yaml`, which is versioned with the ontology. Every value is an entry:

```yaml
# schema/vocab/fields.yaml
version: 1.0.0
facet: fields
cardinality: many          # one | many
values:
  - id: translation
    label: {en: Translation & localization, ko: 번역·현지화}
    scope_note: Producing target-language text from a source; includes L10n, subtitling, transcreation, QA of translations.
    status: active
    since: 1.0.0
  - id: code
    status: deprecated
    deprecated_in: 1.0.0
    replaced_by: app-dev
    note: "v0.2 area `code` -> field `app-dev` (broader: also design-to-code, scripts)."
```

**Core facets (every record has them, mostly inherited):**

| Facet | Card. | Question it answers | Controlled values (v1) | Default source |
|---|---|---|---|---|
| `kind` | 1 | What sort of record is this? | the ontology type (Event, Decision, Lesson, Document, Message, …) | the writer |
| `fields` | 1..n | Which domain(s) of practice is this part of? | `translation`, `annotation`, `app-dev`, `design`, `job-search`, `research`, `writing`, `business` (admin, finance, clients, invoices), `harness` (meta: the system itself), `personal` | the project registry, else the cwd, else the classifier proposal |
| `activity` | 0..n | What was being done? (PMEST Energy) | `capture`, `draft`, `translate`, `review`, `annotate`, `design`, `build`, `test`, `research`, `decide`, `correct`, `communicate`, `apply`, `negotiate`, `invoice`, `plan`, `learn`, `maintain` | the skill or agent that wrote it |
| `sensitivity` | 1 | Who may see it, and where may it travel? | `public`, `private` (yours), `client-confidential` (NDA or client content), `third-party-personal` (other people's personal data), `secret` (credentials: must never be stored; the value exists only so that detection can flag it) | inherited from the store root and the project, and may only be *raised* below that level |
| `status` | 1 | What is its lifecycle state? (the PARA axis) | `active`, `dormant`, `closed`, `superseded`, `archived` | projects explicitly; records inherit |
| `retention` | 1 | How long is it kept? | a class from §4.8 (`permanent`, `tax-7y`, `client-term`, `vault-3y`, `transient-90d`, …) | the record class plus the project |

**Context references (refs, not tags):**
- `project`: `prj_…`, 0..n. One is usually the home; extra ones are "also serves". A translation test is `project: [prj_application_acme, prj_translation_portfolio]`.
- `parties`: a list of `{role, pty_…}`, e.g. `client`, `employer`, `platform`, `recipient`, `author`.
- `work`: `wrk_…`, which groups versions and translations.

**Linguistic facets (when relevant):**
- `lang`
- `direction`: the existing enum and aliases
- `register`: the existing `registers`
- `domain`: the subject domain of a text (legal, tech, medical, game, …), which the glossary already uses

**Open, gated facet:**
- `topics`: 0..5 terms from `vocab/topics.yaml`. Terms carry `broader` (polyhierarchy allowed, at most 3 hops), `related`, `alt_labels` in ko and en, and crosswalk matches.
- New terms enter as `labels` candidates and are promoted weekly.

**Provenance block (fixed at capture, never edited):**

```json
"provenance": {"channel": "claude-code|claude-ai|gmail|viber|lark|slack|drive|manual|...",
               "home": "prj_… | msg-vault/gmail/acc_… | harness",
               "actor": "me|harness|agent:<name>", "model": "opus|…|null",
               "session_id": "…", "captured_at": "2026-10-16T14:32:05Z",
               "source_ref": "sha256:… | msg_… | url"}
```

**Applicability (for rules, preferences, lessons, style pairs):**
- `applies_to: ["field:translation", "task:translation-email", "prj_…", "global"]`, many values.
- This replaces the overloaded meaning of `scope` for Preference and Lesson. `scope` stays readable as legacy, and `schema_check` derives `applies_to: [scope]` when the new field is missing.

**Mapping old `areas` to new `fields`** (to record in `vocab/fields.yaml` as deprecations and aliases):

| v0.2 area | v1 field | Relation |
|---|---|---|
| translation | translation | exactMatch |
| annotation | annotation | exactMatch |
| job-search | job-search | exactMatch |
| art | design | closeMatch (fine art may later become its own value; keep a `topics:` term `fine-art` until it does) |
| code | app-dev | closeMatch (one-off scripts → `harness` or `app-dev`) |
| research | research | exactMatch |
| personal | personal | exactMatch |
| *(none)* | writing, business, harness | new |

There are 10 field values, which is inside the Johnny.Decimal-style cap of 10. If an 11th seems needed, it is probably a `topic`.

### 4.4 Hierarchy vs links: the rule

- **Hierarchy (containment) is used only for provenance and storage:** `root / series (record stream) / partition (time or source)` and `project / standard folder`. A record has exactly one container.
- **Everything semantic is links or facets.** Membership, aboutness, reuse, derivation, sequence and supersession are expressed this way.
- **Link vocabulary** (closed, PROV/DC/RiC-aligned; extend it only through the ontology):
  - `part_of`
  - `derived_from`
  - `translation_of`
  - `version_of`
  - `supersedes`
  - `corrects`
  - `evidence_for`
  - `learned_from`
  - `prevents`
  - `applies_to`
  - `continues`
  - `related`
  - `same_as` (dedupe across sources)
  - `reuses` (transclusion or a portfolio sample)
  - `for_party`
  - `produced_by`
- **Where links live:** as a `links: [{rel, to, since?, by, conf?}]` field on the *newer* record (append-only friendly). A link added later goes in as a `label`/`link` event, so old lines are never edited. `views.py` builds the inverse index.

### 4.5 Representing cross-field items (worked examples)

**A. The Korean UI strings for Canopy, done as translation work and later used as a job-application sample.**

```json
{"id":"doc_01JA…","kind":"Document","title":"Canopy onboarding ko strings v3",
 "work":"wrk_01JA…(Canopy onboarding copy, ko)", "links":[{"rel":"translation_of","to":"wrk_01J9…(en source)"}],
 "fields":["translation","app-dev"], "activity":["translate"], "project":["prj_canopy"],
 "lang":"ko","direction":"en-ko","register":"client-deliverable",
 "sensitivity":"private","status":"active","retention":"permanent",
 "instantiations":[{"sha256":"…","path":"knowledge/raw/9f2c41ab_onboarding_ko_v3.md"},
                   {"sha256":"…","drive":"https://drive…"}],
 "provenance":{"channel":"claude-code","home":"prj_canopy","actor":"me","captured_at":"…"}}
```

Later, the job application records `{"rel":"reuses","to":"doc_01JA…"}` with `fields: ["job-search"]`. The Document gets **no** new copy. Its `fields` can gain `job-search` through a `label` event if you want it to show in that field's view.

**B. A lesson learned in annotation that should guide translation QA.**

- `lsn_…` with:
  - `provenance.home: prj_<annotation platform>`
  - `fields: [annotation]`
  - `applies_to: ["field:annotation","field:translation","task:translation-qa"]`
  - `learned_from: [evt_…]`
- The translation QA skill queries `applies_to ∋ field:translation`.
- The lesson is written once, has one home, and is used in two places.

**C. One email thread with a platform recruiter about a translation-annotation hybrid role.**

- `thr_…` lives in the vault (`sensitivity: third-party-personal`, `retention: vault-3y`).
- Derived `app_…` in harness-data with:
  - `fields: [job-search, annotation, translation]`
  - `parties: [{role: platform, to: pty_…}]`
  - `links: [{rel: derived_from, to: thr_…}]`
- The derived record contains no message text.

**D. Canopy thought ↔ harness item.** The crosswalk maps Canopy `ThoughtType.plan` → `activity: plan`, `NoteArchetype.reference` → `kind: Document`, and `familyScores` → `topics` *proposals* with confidence. Soft membership stays in views; hard facets enter only through approval. This keeps Canopy's probabilistic layer apart from the harness's evidential layer, mirroring Canopy's own split between "ontological" and "organizational" layers.

### 4.6 Folder layouts

**Repo `claude-harness/`** (no personal data): add the vocabulary and crosswalk folders.

```
schema/
  ontology.yaml            # types, links, id patterns (v1.0.0)
  vocab/                   # one file per controlled facet: fields, activity, sensitivity, status, retention, topics
  crosswalks/              # areas->fields, gmail-labels, drive-folders, canopy, dublin-core+prov export
  retention.yaml           # §4.8 schedule (machine-readable)
  CHANGELOG.md             # every vocab/ontology change: what, why, mapping
```

**`~/harness-data/`**: series at the top, time partitions below. Depth is at most 3.

```
harness-data/
  log/YYYY/YYYY-MM.jsonl        # events (move to a year folder once > ~5 years of months; old paths kept by redirect note)
  registry/                     # entity registries, newest-line-wins
    projects.jsonl  parties.jsonl  accounts.jsonl  works.jsonl  redirects.jsonl
  learn/                        # derived learning: kept permanently
    preferences.jsonl  style/pairs.jsonl  style/guide.md  patterns/…  research/ledger.jsonl
  work/                         # derived work records
    applications.jsonl  jobleads.jsonl  finance/ledger.csv
  evals/…
  fixity/                       # hash manifests of vault + Drive originals (hashes only) and check results
    vault-<source>.sha256  drive-originals.jsonl  checks.jsonl
  disposition/tombstones.jsonl  # what was deleted, when, why, under which retention rule
  labels/                       # transient batches (retention transient-90d)
  views/                        # GENERATED; .gitignored or regenerated in CI; never hand-edited
    by-field/<field>.md  active.md  topics/<term>.md  timeline/YYYY.md
```

(Moving today's top-level files into `registry/`, `learn/` and `work/` is optional. If you do it, do it once, in one commit, with `STORAGE.md` and the ontology `store.path` updated together. If you don't, keep the current paths. The other rules matter more than these folder names.)

**`~/msg-vault/`**: provenance first (source / account), original order kept, blobs content-addressed.

```
msg-vault/                         # mode 700, never synced
  <source>/<acc_id>/               # gmail/acc_…, viber/acc_…, lark/acc_…
    exports/<YYYY-MM-DD>_<kind>/   # raw export batches exactly as received, as BagIt bags
      bag-info.txt  manifest-sha256.txt  tagmanifest-sha256.txt  data/…
    messages.jsonl  threads.jsonl  attachments.jsonl   # records (msg_/thr_/att_), point to blobs
  blobs/sha256/<2>/<2>/<64hex>     # every attachment/body stored once, by hash (dedupe across sources)
  style/samples.jsonl
  cursors.json
```

**Projects**: flat, keyed by slug, and classification moves into metadata.

```
~/projects/<slug>/                 # e.g. ~/projects/canopy-ko-l10n/, ~/projects/acme-contract/
  CLAUDE.md                        # frontmatter: id: prj_…, fields, client, sensitivity, retention, status
  PROGRESS.md  decisions.md  HANDOFF.md
  inbox/         # SIP
  work/
  deliverables/  # YYYY-MM-DD_<slug>_<what>_v<N>.<ext>  (the Instance label)
  assets/        # assets.yaml
  knowledge/     # raw/ (AIP payload, <sha8>_<name>) · manifest.json · wiki/ · index.md · log.md
  log/           # sessions/ (the ONE home for session notes) · mishaps.md · handoffs/
```

- **Why flat, not `<area>/<project>`:** a project's fields can change (a translation job becomes a portfolio piece), and a path that encodes the field would have to move. `scripts/weekly_report.py` today derives scope from cwd components that are areas. It should look the cwd slug up in `registry/projects.jsonl` instead, and fall back to the old rule for legacy folders.
- **Minimal-change alternative:** keep `<area>/<project>/` for existing projects and treat the area in the path as *the home field only*, frozen at creation. Never move a folder; add more fields in frontmatter.
- **Google Drive** (human browsing, originals): a Johnny.Decimal-style shallow top level helps people:
  - `10 Projects/<slug>/`
  - `20 Originals/<YYYY>/`
  - `30 Portfolio/`
  - `40 Admin & Tax/<YYYY>/`
  - `90 Archive-exports/`

  Each project folder mirrors the slug, and `kb.py archive` records the Drive file ID *and* Drive's `md5Checksum` beside the local sha256.

**Naming rules:**
- Lowercase-kebab slugs, ASCII.
- Korean appears in titles and labels, not paths.
- Dates are ISO `YYYY-MM-DD` at the front.
- Versions use `_v<N>`.
- No spaces or special characters in paths that scripts touch.

### 4.7 Inheritance (non-repetition)

The facet value a record gets is resolved in this order:
1. the record itself
2. the project's `CLAUDE.md` frontmatter or registry entry
3. the store's defaults in `ontology.yaml` (privacy root → `sensitivity`, type → `retention`)
4. the classifier proposal (a `label` event, `by: agent:librarian`, `conf`)

Views show inherited values. Records store only overrides. `sensitivity` may only be *raised* below the project level, never lowered.

### 4.8 Retention and disposition

`schema/retention.yaml`, applied by record class and overridable per project:

| Class | Applies to | Keep | Then | Basis |
|---|---|---|---|---|
| `permanent` | decisions, lessons, principles, preferences, corrections, patterns, style pairs (your own text), ontology and vocab, research notes, your own original work and deliverables, eval tasks and results | forever | — | Core learning and evidence: the reason the harness exists |
| `tax-7y` | invoices, finance ledger, contracts, payment records, withholding receipts | 7 years after the filing deadline of that tax year | review → destroy, tombstone | 국세기본법 §85의3: 5 years, and 7 for offshore transactions. Default to 7 because of foreign clients and platforms; confirm with a tax adviser. |
| `client-term` | client source files, client TMs and termbases, NDA material (`client-confidential`) | per contract. Default: until the deliverable is accepted + 12 months, or the NDA term if longer | destroy raw; **keep** derived glossary rows *only* if they are your own generic terms, and lessons *without* client text | NDA and client agreements, `docs/LOCAL_ONLY.md` |
| `platform-none` | annotation task content where the ToS forbids retention | 0 (never stored) | — | Platform ToS |
| `vault-3y` | third-party messages, threads, attachments, contacts' personal details | 3 years from the last activity in the thread or with the party | review: keep the thread ID + derived records, destroy bodies, or extend with a reason | Storage limitation (GDPR / PIPA principles); purpose = job search and client work |
| `job-3y` | applications, job leads | 3 years after closure | keep an anonymised summary row (company, role, outcome, dates) permanently | Usefulness for pattern learning; limits personal data |
| `transcript-2y` | raw Claude Code transcripts (`~/.claude/projects/`), claude.ai exports | 2 years | keep session notes and events (permanent); drop raw transcripts | The events already capture intent, situation and decisions |
| `transient-90d` | label batches, auto handoffs, caches, fan-out scratch | 90 days | delete (no tombstone needed: no record ID) | operational |
| `secret` | credentials | never stored | detection → rotate + purge | `docs/SECURITY.md` |

**The disposition process.** Run it quarterly as `scripts/disposition.py due`, in the same rhythm as the drill:
1. List the records and bits that are past their retention, excluding those on `hold: true`, a legal or tax hold.
2. You approve.
3. Delete the bits and blank or remove the records in the vault.
4. Append a **tombstone** `{id: tmb_…, target: <id or sha256>, class, rule_version, reason, approved_by: me, ts}`.
5. Log a `disposition` event.

Tombstones keep links resolvable ("deleted on 2029-…, rule vault-3y") instead of breaking silently.

### 4.9 Fixity and preservation

| Item | Fixity source | Where the hash lives | Check |
|---|---|---|---|
| git repos (harness, harness-data, projects) | git object hashes | in git and on the remote | `git fsck --full` in the monthly drill |
| project `knowledge/raw/` | sha256 in `manifest.json` | the manifest (in the project repo) + a copy in `harness-data/fixity/` | monthly: a random 5% sample; quarterly: everything |
| vault export bags and blobs | `manifest-sha256.txt` per bag; the blob path *is* its hash | the bag + `harness-data/fixity/vault-<source>.sha256` (hashes only: no content, OK to sync) | as above; `bagit.py --validate` |
| Drive originals | Drive API `md5Checksum` + the local sha256 recorded at archive | `harness-data/fixity/drive-originals.jsonl` | quarterly: list via the Drive connector and compare md5 |
| Backblaze / Time Machine | the tool's own | — | restore one file (already in the drill) |

- **Log every check as a `fixity_check` event** with `outcome`. A failure triggers repair from another copy (NDSA level 4) and a `mishap`.
- **Normalization for long-term readability:** keep the original *and* a normalized instantiation:
  - text: UTF-8 Markdown
  - documents: PDF/A
  - images: PNG / TIFF
  - layered design: PSD plus the exported PNG layers (the `psd_layers.py` output), plus SVG where possible
  - audio: FLAC
  - mail: mbox / EML
- **Write Preservation Objectives in `retention.yaml`**, one line per class. For example: "deliverables: re-openable and diff-able by me without the original app".

### 4.10 Crosswalk to standards (for export and future apps)

| Harness | Dublin Core | PROV-O | RiC-O | PREMIS |
|---|---|---|---|---|
| `id` / `aka` | identifier | — | identifier | objectIdentifier |
| `title` | title | — | title | — |
| `provenance.actor` | creator | wasAttributedTo | hasOrHadCreator / Agent (Mechanism for AI) | Agent |
| `provenance.captured_at` / `ts` | date / created | generatedAtTime | Date | eventDateTime |
| `kind` | type | — | RecordResource subclass / DocumentaryFormType | objectCategory |
| `fields`, `topics` | subject | — | hasOrHadSubject | — |
| `activity` | — | Activity (wasGeneratedBy) | Activity | eventType |
| `lang` | language | — | hasOrHadLanguage | — |
| `sensitivity` | accessRights | — | Rule / conditions of access | Rights |
| `instantiations[].sha256` | format + identifier | — | Instantiation | messageDigest (sha256) |
| `links: derived_from` | source | wasDerivedFrom | (Relation) | relationship |
| `links: version_of / supersedes` | isVersionOf / replaces | wasRevisionOf | — | — |
| `project` | isPartOf | — | isOrWasIncludedIn (RecordSet) | — |
| `parties` | contributor / publisher | wasAssociatedWith | Agent relations | linkingAgent |

### 4.11 Anti-pattern guardrails (lint rules for `schema_check` / `weekly_report`)

| Rule | Threshold | Action |
|---|---|---|
| Folder depth below any root | > 3 | warn; suggest using a facet instead |
| `topics` per record | > 5 | warn |
| Singleton topic terms (used once in 180 days) | any | propose a merge or delete in the weekly review |
| Near-duplicate terms (edit distance ≤ 2, or the same after ko↔en `alt_labels`) | any | propose a merge (`same_as` / `replaced_by`) |
| A term equal to a field or project name | any | reject (redundant with a facet) |
| Records with `fields` unresolved after inheritance | > 5% per week | fix the project registry or cwd mapping |
| `misc`, `other`, `todo`, `important` as a topic | any | reject; use `status` or a task |
| Writes using a deprecated vocab value | any | warn and show `replaced_by` |
| Orphan wiki pages or lessons (no inbound link, no `applies_to`) | any | list in the review |
| Same sha256 at two record IDs | any | propose a `same_as` / redirect |
| Copies of content across privacy roots | any (vault text in harness-data) | **error** |
| Facet value count | `fields` > 12 or `activity` > 20 | block: the ontology needs review |

### 4.12 Vocabulary and ontology evolution procedure

1. **Proposals** come from the weekly `label_events` / `pattern-review` cycle, from new candidate terms, or from you.
2. **A change is a PR** to `schema/vocab/*.yaml` with a semver bump:
   - patch: labels or notes
   - minor: a new value
   - major: a deprecation, split or merge
3. **The PR also carries** a `CHANGELOG.md` entry and any crosswalk update.
4. **Never rewrite data.** Old values resolve through `replaced_by` or `value_aliases` at read time.
5. **Splits** (one value becoming two) are marked `split_into: [a, b]`. Affected records get a reclassification *proposal* batch, not an automatic edit.
6. **Each record may carry `vocab_version`.** Otherwise the version is inferred from `ts` and the changelog date.
7. **Review all facets every 6 months** with usage counts. Unused values for a year → deprecate.

---

## 5. Concrete changes to the harness, in priority order

1. **Add `schema/vocab/` with the `fields`, `activity`, `sensitivity`, `status`, `retention` and `topics` files**, and the `areas → fields` deprecation map. Teach `schema_check.py` to read the files and to support `status: deprecated` / `replaced_by`.
2. **Add the optional fields `fields`, `applies_to`, `project` (list), `links`, `provenance`, `sensitivity`, `retention`, `aka` and `work`** to the common field set in `ontology.yaml`. Derive them from legacy `scope` when absent.
3. **Add a ULID helper** (stdlib, around 20 lines) to `hooks/_common.py`. New types and new records use `<prefix>_<ULID>`. Add the legacy `id_pattern` *or* the ULID pattern per type, and a `registry/redirects.jsonl`.
4. **Add the project registry** (`registry/projects.jsonl`, with `prj_` IDs, slug, fields, client, sensitivity, retention and status), written by `skills/new-project`. Add frontmatter to `templates/project/CLAUDE.md`. Switch `weekly_report.py` scope resolution to slug → registry, keeping the legacy fallback.
5. **Close the session-notes gap:** the project `log/sessions/` is the only home, and remove `sessions/` from the `autocommit_data.sh` header.
6. **Fixity:** add `scripts/fixity.py` with `scan|check|drive`, and add "fixity sample + git fsck" to the monthly drill in `docs/BACKUP.md`.
7. **Retention:** add `schema/retention.yaml`, plus `scripts/disposition.py due|apply` (requires approval) and `tombstones.jsonl`. Then add `retention` to `STORAGE.md`'s table.
8. **Document-record split** in `kb.py`: `doc_` record ID, `instantiations[]` (original + converted + Drive), and an optional `work`. Keep `sha8` as the display handle.
9. **Generated views** (`scripts/views.py`): `by-field/*.md`, `active.md` and `topics/*.md`, built from records and never edited by hand.
10. **Crosswalks:** `areas-fields.yaml`, `canopy.yaml` and `dc-prov-export.yaml`.
11. **Party consolidation** (Client, Organization, Contact and Platform → Party with roles), before any of those planned stores get a writer.

---

## 6. Sources

Fetched or searched 2026-10-16:
- RiC-O 1.1 / RiC-CM 1.0:
  - [ICA RiC-O page](https://www.ica.org/standards/RiC/ontology)
  - [ICA Records in Contexts](https://www.ica.org/ica-network/expert-groups/egad/records-in-contexts-ric/)
  - [RiC-O GitHub](https://github.com/ica-egad/ric-o)
  - [RiC-O releases](https://github.com/ICA-EGAD/RiC-O/releases)
- OAIS 3rd edition:
  - [CCSDS 650.0-M-3 PDF](https://ccsds.org/Pubs/650x0m3.pdf)
  - [ISO 14721:2025 sample](https://cdn.standards.iteh.ai/samples/87471/14a5ffd9492e443f86440952aabecf69/ISO-14721-2025.pdf)
  - [oais.info standards process](http://www.oais.info/standards-process/)
  - [NARA fixity blog on 16363](https://fixity-check.blogs.archives.gov/2025/03/06/16363-reasons-to-trust/)
- PREMIS 3.0:
  - [Library of Congress PREMIS v3](https://loc.gov/standards/premis/v3/)
  - [PREMIS DD mirror: messageDigest](https://sbs.uniroma1.it/data/premisDataDictionary/dlcmrc-vocs_2016-PREMISDD_2017_Object_messageDigest)
- NDSA Levels and fixity:
  - [NDSA Fixity Guidance Report](https://www.digitalpreservation.gov/ndsa/working_groups/documents/NDSA-Fixity-Guidance-Report-final100214.pdf)
  - [LOCKSS commentary](https://www.lockss.org/node/286)
  - [AVP: NDSA levels across cloud vendors](https://weareavp.com/?p=1877)
- BagIt: [RFC 8493](https://www.rfc-editor.org/rfc/rfc8493) (taken from search results; the page itself was unreachable).
- OCFL: [Zenodo OCFL 1.1](https://zenodo.org/record/7157195), [DCMI MSI: OCFL](https://msi.dublincore.org/standards/ocfl)
- ISO 15489-1:2016:
  - [iTeh catalogue](https://iteh.es/catalog/standards/iso/baf32a1d-182a-428d-aca9-74f0e33d01a7/iso-15489-1-2016)
  - [ISO news 2016](https://www.iso.org/es/contents/news/2016/04/Ref2072.html)
  - [SafetyCulture guide](https://safetyculture.com/topics/iso-15489)
- ISAD(G):
  - [ICA ISAD(G) 2nd edition PDF](https://www.archives.go.jp/thinktank/pdf/ISADG_2nd_EN.pdf)
  - [ISAD(G), Wikipedia (as a search result)](https://en.wikipedia.org/wiki/ISAD(G))
  - [DCMI MSI: ISAD(G)](https://msi.dublincore.org/standards/isad-g)
- Provenance and the series system:
  - [ICA 2012 paper on Peter Scott](http://ica2012.ica.org/files/pdf/Full%20papers%20upload/ica12Final00414.pdf)
  - [Clive Smith, Archivaria](https://archivaria.ca/index.php/archivaria/article/download/12098/13086/0)
  - [ISKO: Provenance](https://www.isko.org/cyclo/provenance)
- Colon Classification:
  - [Colon classification, Wikipedia (as a search result)](https://en.wikipedia.org/wiki/Colon_classification)
  - [Gnoli 2024, ALIS](https://or.niscpr.res.in/index.php/ALIS/article/view/8996)
  - [historyofinformation.com entry](https://www.historyofinformation.com/detail.php?id=4384)
- Faceted search:
  - [Flamenco 2002 paper](https://flamenco.berkeley.edu/papers/flamenco02.pdf)
  - [Hearst, CACM 2006](https://flamenco.ischool.berkeley.edu/papers/cacm06.pdf)
  - [CHI 2007 course](https://flamenco.berkeley.edu/chi_course.html)
- Dublin Core / PROV:
  - [DCMI MSI: DCMI Metadata Terms](https://msi.dublincore.org/standards/dcmi-metadata-terms)
  - [W3C PROV-DC draft](https://www.w3.org/TR/2012/WD-prov-dc-20121211)
  - [PROV-O vocabulary listing](https://hexdocs.pm/rdf_vocab/RDF.Vocab.PROV.html)
- BIBFRAME: [LoC BIBFRAME 2.0 model](https://www.loc.gov/bibframe/docs/bibframe2-model.html)
- Johnny.Decimal:
  - [Areas and categories](https://johnnydecimal.com/documentation/areas-and-categories)
  - [Expand an area](https://johnnydecimal.com/documentation/expand-an-area-overview.md)
  - [The numbers](https://business.johnnydecimal.com/documentation/the-numbers)
- PARA: [Workflowy: PARA method](https://workflowy.com/help/para-method), [ClickUp: PARA method](https://clickup.com/blog/para-method/)
- Zettelkasten:
  - [Forum comment 13299](https://forum.zettelkasten.de/discussion/comment/13299)
  - [Forum comment 14638 (Lengyel formalization)](https://forum.zettelkasten.de/discussion/comment/14638)
- Folksonomy vs controlled vocabulary:
  - [ISKO: Tagging](https://www.isko.org/cyclo/tagging)
  - [Folksonomies: (Un)Controlled Vocabulary?](https://www.researchgate.net/publication/28807454_Folksonomies_UnControlled_Vocabulary)
  - [Information Research 16(3) paper 482](https://informationr.net/ir/16-3/paper482.html)
- SKOS deprecation and mapping:
  - [Skosmos data model](https://github.com/NatLibFi/Skosmos/wiki/Data-Model)
  - [W3C wiki: SKOS scheme versioning](https://www.w3.org/wiki/SkosDev/SkosCore/SchemeVersioning)
  - [Deprecation workflows](https://theconnectedlayer.com/posts/deprecation-workflows-for-obsolete-ontology-classes-and-properties)
  - [LOKF issue #112](https://github.com/nicholsn/lokf/issues/112)
  - [metadataetc: KOS mapping models](https://metadataetc.org/LOD/interoperability_KOS_mapping_models.html)
  - [NISO: ISO 25964](https://www.niso.org/standards-committees/iso-25964)
- IDs:
  - [ULID spec](https://github.com/ulid/spec)
  - [UUIDv7 vs ULID](https://norvilis.com/uuid-v7-vs-ulid-which-sortable-id-should-you-choose/)
  - [ULID primary keys](https://blog.daveallie.com/ulid-primary-keys)
  - [ARK draft](https://www.ietf.org/archive/id/draft-kunze-ark-35.html)
  - [BnF identifier guidance](https://www.bnf.fr/fr/centre-d-aide/identifiants-internationaux)
  - [W3C mailing-list post on persistence](https://lists.w3.org/Archives/Public/public-prov-wg/2011Jun/0388.html)
  - [Wikidata merge tickets](https://phabricator.wikimedia.org/T127213), [codethecity on Wikidata duplicates](https://codethecity.org/category/wikidata/)
- Transclusion: [Obsidian forum: block reference](https://forum.obsidian.md/t/block-reference/674?page=7), [dsebastien: Obsidian embeds](https://www.dsebastien.net/obsidian-embeds/)
- Retention law:
  - [Tax retention: 5 years and the 7-year exception (thecheck)](https://thecheck.co.kr/?p=6181)
  - [Ruling on 국세기본법 §85의3 (nepla)](https://www.nepla.ai/wiki/세금/조세행정-및-절차/-유권해석-국세기본법-제85조의3-장부-등의-비치와-보존-ov59r11ln063) (secondary: confirm on law.go.kr)
  - [ICO: storage limitation](https://ico.org.uk/for-organisations/uk-gdpr-guidance-and-resources/data-protection-principles/a-guide-to-the-data-protection-principles/storage-limitation/)
  - [Helbing: Article 5(1)(e)](https://www.thomashelbing.com/en/wissen/dsgvo-hub/einzelthemen/grundsaetze-der-verarbeitung/1.3.3.7-speicherbegrenzung)

**Unreachable today (DNS failures from this container):** `www.rfc-editor.org` and `datatracker.ietf.org` (the RFC 9562 and RFC 8493 full text), `ica-egad.github.io` (the RiC-O HTML documentation), and `en.wikipedia.org` (WebFetch; search snippets only).
- The UUIDv7 details therefore come from secondary sources.
- The RiC-O class and relation names (RecordResource, Instantiation, Agent/Mechanism, `isOrWasIncludedIn`) are **[known]**, not re-verified.
- The disposition and appraisal wording of ISO 15489 is **[known]**. The standard is paywalled, and only its summaries were reachable.
- I found no empirical study of tag sprawl in personal knowledge-management tools.
