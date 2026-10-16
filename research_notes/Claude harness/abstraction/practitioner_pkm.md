# Practitioner PKM and decision logs: multi-level abstraction and idea convergence (2026-10-16)

Scope: how practitioners and tools implement levels of abstraction, promotion between levels, linking, review cadence and decision quality in personal knowledge systems and decision logs, as of October 2026. The goal is to adapt them to the harness's JSONL/YAML ontology (`claude-harness/schema/ontology.yaml` v0.2, which already has the L0 to L5 pattern ladder, `Decision`, `Lesson`, `Preference` and `ResearchNote`) and its Claude skills.

## Method and source quality

- **Web.** Searches were run with WebSearch (standard and extended).
- **Unreachable sites.** WebFetch and curl could not reach most primary sites from this sandbox because DNS failed: notes.andymatuschak.org, zettelkasten.de, fortelabs.com, blog.linkingyourthinking.com, adr.github.io, fs.blog, hbr.org, docs.logseq.com, blacksmithgu.github.io (Dataview), help.obsidian.md and jsoncanvas.org. Claims about those sources come from search-result snippets and secondary write-ups, and are marked **(secondary)**. Only gist.github.com and github.com were reachable directly.
- **Repos.** Repos were read from shallow clones (`git clone --depth 1`) into `/tmp/claude-0/-home-user-albers-club/1397d302-c3cb-5329-ad06-e45b2c66c6d1/scratchpad/pkm/<name>`. Star counts come from the GitHub search API on 2026-10-16. Stars are inflated: these repos are promoted on X and through "10 free repos" listicles, so star counts measure exposure, not quality. A repo's ranking below weighs what is actually inside it (schemas, lifecycle rules, lint scripts) more than its stars.
- **Gaps.** I could not verify exact primary wording for Farnam Street's template, TC 25-20, Klein's HBR text, Sascha Fast's structure-note article or Forte's Progressive Summarization III. The content of each is consistent across 2 or more secondary sources.

---

## 1. Classic PKM methods: levels, promotion and failure modes

### 1.1 Zettelkasten (Luhmann, Ahrens's *How to Take Smart Notes*, zettelkasten.de)

**Levels.** There are four explicit note types:

| Level | Note type | Content | Lifetime |
|---|---|---|---|
| 0 | Fleeting | Raw capture | Process within 24 to 72 h, then promote or discard |
| 1 | Literature | A short summary of one source, in your own words, with its citation | Kept, tied to the source |
| 2 | Permanent (zettel) | One idea, written to stand alone, in your own words, linked | Kept for years |
| 3 | Structure / hub | A note that orders and annotates links to a cluster of permanent notes | Emerges after the cluster exists, never planned in advance |

Sources: [ernestchiang Ahrens summary](https://www.ernestchiang.com/en/posts/2025/sonke-ahrens-how-to-take-smart-notes/), [myflexnote 2026 guide](https://myflexnote.com/blog/zettelkasten-method-guide), [apragmaticmind](https://www.apragmaticmind.com/blog/zettelkasten-method).

**Promotion rules.**
- Fleeting to permanent happens in a daily processing pass, or the note is discarded.
- A note that holds several ideas gets split into atomic notes.
- Literature to permanent requires a rewrite in your own words plus at least one link into existing notes ("where does this fit?").
- A structure note is created when a cluster becomes hard to navigate, not up front.

**Linking.**
- Folgezettel (branching IDs such as 21/3a) was Luhmann's way of placing a new note next to its parent. zettelkasten.de argues it mainly served the physical card box (secondary: [zettelkasten hubs](https://zettelkasten.de/posts/zettelkasten-hubs/)).
- In digital practice, links plus structure notes replace Folgezettel. Forum users note that Folgezettel cannot rehome a later overarching topic, for example a "concurrency" overview that sits above earlier "deadlock" notes. Structure notes can ([forum.zettelkasten.de](https://forum.zettelkasten.de/discussion/comment/12565)).
- Links should carry a reason ("this contradicts X because…"), not just be bare.

**Cadence.** Fleeting notes are processed daily. Structure work is opportunistic, done when writing or when a cluster gets crowded.

**What works.**
- Atomicity and own-words rewriting. The rewriting is the learning.
- Structure notes as a second axis of order, alongside links.

**What fails.**
- Heavy upfront effort. Users report that the processing was "nearly impossible to stick with" ([HN](https://news.ycombinator.com/item?id=23386630)).
- Rabbit-holing on tooling.
- Poor fit for technical subjects you already understand.
- Some long-time users abandon hierarchy for "smart searches."
- The collector's fallacy: saving many literature notes and never promoting them.

### 1.2 Andy Matuschak: evergreen notes (secondary; his site was unreachable)

**Levels.** Evergreen notes sit inside a writing inbox, then a working note, then the evergreen note. The defining principles:
- Atomic.
- Concept-oriented, not organized by source, author or project.
- Densely linked.
- Associative ontologies preferred over hierarchical taxonomies.
- Written for yourself by default.

Sources: [concept-oriented note](https://notes.andymatuschak.org/Evergreen_notes_should_be_concept-oriented), [jarango](https://jarango.com/2023/02/02/evergreen-notes/), [fabric](https://fabric.so/learn/evergreen-notes).

**The promotion signal is the title.**
- "Evergreen note titles are like APIs": a sharp, complete-phrase claim title lets the note be referenced by its handle alone.
- "Prefer note titles with complete phrases to sharpen claims": the title often emerges while you write. Having a crisp claim title is the sign the note has matured.

Sources: [titles as APIs](https://notes.andymatuschak.org/Evergreen_note_titles_are_like_APIs), [complete-phrase titles](https://notes.andymatuschak.org/zLhoRUyjKU665EY16u4XXJy).

**Linking.** Links go inline in prose, as part of an argument. Notes accrete over time, and connections across books and domains surface through linking.

**Adaptation.** Make a claim-shaped `title` required at the permanent level ("X causes Y when Z", not "X"). A note whose title cannot be written as a claim is not yet a permanent note.

### 1.3 Tiago Forte: Building a Second Brain (CODE, PARA, Progressive Summarization, Intermediate Packets)

**PARA: organization by actionability, not topic.**
- **Projects:** a goal plus a deadline.
- **Areas:** ongoing responsibilities.
- **Resources:** interests.
- **Archives:** inactive items.

The same PDF can sit in any of the four depending on "when will I need it?", not "what is it about?" Organization is "just-in-time", done as a side effect of work. A finished project moves to Archives. Sources: [Thomas Frank book notes](https://thomasjfrank.com/productivity/books/the-para-method-by-tiago-forte-summary-and-book-notes/), [Workflowy PARA](https://workflowy.com/help/para-method). A weekly review is part of the method. I could not verify a monthly cadence.

**CODE.** Capture, Organize, Distill, Express. Progressive Summarization belongs to Distill.

**Progressive Summarization layers.**

| Layer | What it is |
|---|---|
| L0 | The source |
| L1 | Captured excerpt |
| L2 | Bold passages |
| L3 | Highlight within the bold |
| L4 | Executive summary in your own words |
| L5 | Remix: turn it into your own creative output (rare) |

The key rule is **opportunistic compression**: add a layer only when you revisit a note for a real reason. In Forte's words, it is "absolutely NOT the goal to stuff every single note through all the layers". Sources: [PS III guidelines](https://fortelabs.com/blog/progressive-summarization-iii-guidelines-and-principles/) (secondary), [dsebastien](https://concepts.dsebastien.net/concept/progressive-summarization/), [every.to PS II](https://every.to/forte-labs/progressive-summarization-ii-examples-538088).

**Intermediate Packets.** These are the units of reuse. There are five kinds: distilled notes, outtakes, work-in-process, final deliverables, and documents created by others ([medium summary](https://medium.com/@subin.khullar/summary-building-a-second-brain-dd80989b1f87), [Forte: IPs in the wild](https://fortelabs.com/blog/intermediate-packets-in-the-wild/)). Convergence happens at Express: projects get assembled from IPs.

**What works.**
- Actionability-based filing.
- The rule that compression is driven by use (each layer is earned by a revisit).
- Outtakes as a first-class kind.

**What fails.**
- Over-highlighting.
- Treating capture volume as progress, which is collecting rather than learning ([faafospecialist](https://faafospecialist.substack.com/p/a-practical-guide-to-building-an)).
- Resources piling up untouched.

**Adaptation.**
- Store `distill_layer` (0 to 5) per note. It increments only on a revisit tied to a live project or decision (`revisit_reason` required).
- Add `ip_kind` (distilled | outtake | wip | deliverable | external) so finished work and outtakes become reusable inputs.

### 1.4 Maps of Content: Nick Milo, LYT / Ideaverse (secondary; LYT site unreachable)

**Definitions.**
- An MOC is "a note that mainly has links to other notes," which maps their contents.
- The **mental squeeze point** is "the point in any endeavor where the amount of information begins to overwhelm you". It is the trigger to build an MOC.
- Milo says the ability to sense that anxiety and build an MOC "is oftentimes the difference between a finished project and an abandoned one".

Source: [LYT glossary](https://blog.linkingyourthinking.com/notes/lyt-glossary), [benefits of LYT](https://www.linkingyourthinking.com/ideaverse/benefits-of-lyt-frameworks).

**ACE folders.**
- Atlas holds knowledge.
- Calendar holds time-based records.
- Efforts holds work, at varying intensity.
- A community skill file adds `+ Extras` for templates and config ([smithery ideaverse skill](https://smithery.ai/skills/mrfelton/ideaverse)).

**Promotion rule.** Do not pre-build MOCs. Wait for the squeeze point. The community rule of thumb is about 10 or more notes on a topic, from a third-party skill file, not from Milo.

**Linking.** Notes carry `up:` links to their MOC and `related:` links to peers. A Home note links to the top MOCs.

**Adaptation.** Add a `squeeze` lint that proposes a structure note when 10 or more permanent notes share a scope or tag and no structure note covers them. The proposal is a suggestion, not an auto-created note.

---

## 2. Tools: how structure is encoded

| Tool | Level and structure primitive | Promotion / convergence mechanism | What users report |
|---|---|---|---|
| **Tana** | **Supertags** (node types) with **fields** (typed properties) and **inheritance** (`#bug-report` extends `#task`). Search nodes are saved queries such as "find nodes with tag X where field Y = Z". Table view uses fields as columns. Local API and MCP server shipped ([supertag-cli](https://github.com/jcfischer/supertag-cli), [Ness Labs](https://nesslabs.com/tana-task-management), [Tana fields docs](https://tana.inc/docs/fields)). | You promote by retagging (a #note becomes a #concept). Fields auto-initialize. A new field on an existing tag appears empty on old nodes. | Strong for typed queries. Users still report over-structuring risk, because designing tag hierarchies becomes the hobby. This is the closest analogue to a YAML ontology with inheritance. |
| **Heptabase** | Everything is a **card**. Cards are reused across **whiteboards**, and PDF highlights become cards linked back to their source page. | Convergence is spatial and manual. The official workflow says to "allocate some afternoons to organize [cards] into a structure that can best help you achieve your research goal", then write from a whiteboard of structured cards ([wiki: use case](https://wiki.heptabase.com/use-case-and-workflow), [writing workflow](https://wiki.heptabase.com/a-simple-method-to-convert-your-thinking-into-writing)). | Liked for synthesis by hand. The ordering is cards, then a whiteboard cluster, then a section of the draft. Reviews of its AI-suggested links are unconfirmed. |
| **Obsidian** | Notes with YAML **properties**. **Bases** (core plugin since 1.9: table, cards, list and map views, reads only frontmatter). **Dataview** (inline fields and a query language; last release 0.5.70 in April 2026, described as stalled; its output is invisible to the graph, backlinks and search). **Canvas** (the JSON Canvas 1.0 spec: `nodes[]` of type text, file, link or group with x/y/w/h, plus `edges[]`). **Graph** view. | Promotion is manual through property changes such as `status: seed→evergreen`. MOCs are notes. Canvas groups serve as the convergence surface. | 2026 consensus: use Bases for dashboards and Dataview for inline, task or computed queries ([dsebastien guide](https://www.dsebastien.net/the-complete-guide-to-dataview-in-obsidian/), [abdulkadersafi](https://abdulkadersafi.com/blog/dataview-vs-datacore-vs-bases)). The graph view is pretty but rarely used for retrieval. Canvas spec read from the `obsidianmd/jsoncanvas` repo. |
| **Roam** | Every **block** is addressable. Block refs and embeds keep transclusions live in both directions. Datalog queries. | Ideas converge by referencing blocks into a new page; the source block stays canonical. | Users who came from Roam miss granularity in Obsidian. Others question whether referencing raw journal blocks skips the thinking ([Logseq forum](https://discuss.logseq.com/t/is-the-ability-to-reference-embed-a-block-a-killer-feature/8002), [ponder.ing](https://ponder.ing/blog/logseq-vs-roam-research)). |
| **Logseq** | Outliner with block refs and embeds, block **properties** (`key:: value`), queries. The DB version moves toward typed properties. | The same as Roam. A daily journal is the default inbox. | It is easy to end up with everything living in journals and no permanent layer, which is the same failure as unprocessed fleeting notes. |

**Adaptation.**
- Tana's supertag-with-inheritance maps directly onto `ontology.yaml` types: give a `Note` base type and let `Concept`, `Claim`, `StructureNote` and `Decision` extend its fields.
- Roam's block address maps to a stable `id` per JSONL record, plus `anchor` pointers into Markdown (`file#^block`). obsidian-mind already uses this for `promoted:` markers.
- Treat Canvas as an optional *view* that a skill renders from records, never as the source of truth.

---

## 3. Decision journals and learning loops

### 3.1 Annie Duke, *Thinking in Bets* / *How to Decide*, and Farnam Street (secondary)

**Core distinction.** "Resulting" means judging decision quality by the outcome. A good decision can have a bad outcome through luck, and the reverse is also true. A journal preserves what you knew and believed *at the time*, before hindsight rewrites it ([grahammann notes](https://grahammann.net/book-notes/thinking-in-bets-annie-duke), [Crucible](https://readcrucible.com/articles/decision-journals-the-practice-the-science-the-templates), [Ben Meer](https://benmeer.com/newsletter/decision-journal/)).

**Farnam Street template fields (secondary).**
- Situation
- Options considered
- Decision
- Expected outcome
- A later review: what was expected, what happened, why the gap

Commonly added: mental and physical state, and a probability estimate.

**Review.** Score decision quality and outcome quality *separately*. The 2×2 grid is: good decision and good outcome = deserved; good decision and bad outcome = bad luck; bad decision and good outcome = dumb luck; bad decision and bad outcome = deserved.

### 3.2 Pre-mortem (Gary Klein, HBR 2007; secondary)

**Steps.**
1. Assume the plan has already failed.
2. Each person writes reasons independently.
3. Merge the reasons into one list.
4. Revise the plan.
5. Review the list periodically.

**The "30%" claim.** It comes from Mitchell, Russo and Pennington (1989). Prospective hindsight increased the *number* of reasons people generated by about 30%; the study did not measure their quality. Veinott et al. (2010) found that premortems reduced overconfidence more than other methods ([jasoncollins premortem](https://corporate.jasoncollins.blog/premortem), [uncertainty project](https://theuncertaintyproject.org/tools/pre-mortem)). Do not cite it as "30% more accurate."

### 3.3 Architecture Decision Records in practice

**Nygard's lifecycle** is deliberately small: proposed, accepted, deprecated, superseded.
- Accepted ADRs are immutable.
- A reversal is a **new** ADR that supersedes the old one, and the old one's status is updated.
- Superseded ADRs are kept.

**MADR 4.0.0** (2024-09-17; read from the `adr/madr` repo) adds:
- `decision-makers`, `consulted` and `informed` in YAML front matter
- Decision Drivers
- Considered Options
- Pros and Cons per option
- **Confirmation**: "how the implementation/compliance of the ADR can/will be confirmed… fitness function"

The joelparkerhenderson ADR guide (repo read) recommends being "Immutable: … amend… or supersede", and notes "it's typical for teams to review each ADR one month later, to compare the ADR information with what's happened in actual practice."

**Failure modes.**
- Stale "accepted" ADRs that nobody follows.
- Broken supersession links.
- Supersession that triggers only when someone happens to notice.
- "The ADR that rots isn't the decision, it's the assumption under it" ([dev.to](https://dev.to/andriiboyko/the-adr-that-rots-isnt-the-decision-its-the-assumption-under-it-3mnd)).
- The full MADR template discourages people from writing ADRs at all, so practitioners recommend a lean default ([hidekazu-konishi](https://hidekazu-konishi.com/entry/architecture_decision_records_templates_and_operations.html), [neilsherman](https://www.neilsherman.co.uk/blog/architecture-decision-records.html)).

**Adaptation.** Record each decision's load-bearing assumption as its own field with an `assumption_check` date. Revisit is triggered by the assumption, not just by the calendar.

### 3.4 After-Action Review (US Army; TC 25-20 not directly verified)

**Four questions.**
1. What was supposed to happen?
2. What actually happened?
3. Why were there differences? (causes, not blame)
4. What do we sustain, and what do we improve?

The AAR originated at the National Training Center in the 1970s with the opposing force (OPFOR) ([adi.org AAR guide](https://www.adi.org/downloads/After-Action-Review-Guide.pdf), [DTIC](https://apps.dtic.mil/sti/pdfs/ADA368651.pdf)). It runs immediately after the event, is short, and stays blame-free. Its outputs are "sustains" and "improves", which map onto lessons.

### 3.5 Toyota Kata and A3

**Improvement kata.** Set a direction, grasp the current condition, establish the next target condition, then run PDCA experiments toward it.

**Coaching kata: five questions** ([theleansixsigmacompany](https://www.theleansixsigmacompany.com/uk/library/coaching-kata/), [dsebastien](https://concepts.dsebastien.net/concept/coaching-kata/)):
1. What is the target condition?
2. What is the actual condition now?
3. What obstacles are in the way, and which one are you addressing now?
4. What is your next step, and **what do you expect**?
5. When can we go and see what we learned?

**A3.** One page: background, current condition, target, root-cause analysis, countermeasures, plan, follow-up. These are the usual headings; I could not find a primary source for them.

**Key mechanism.** Every step carries an explicit prediction that is compared with the result. Learning is the size of the gap.

### 3.6 What all of these share

Every serious practice records a **prediction before the fact** and compares it with the actual result at a scheduled point. The comparison has to separate **process quality** from **outcome**. The four practices express this differently:

| Practice | How it compares prediction with result |
|---|---|
| Duke | Resulting |
| AAR | Question 3, "why the differences?" |
| Kata | Question 4, "what do you expect?" |
| ADR | The Confirmation field |

The failure mode in every case is a log that is written and never revisited.

---

## 4. LLM and Claude-based PKM tools (2026 status)

| Tool | Status (Oct 2026) | Auto-synthesis model | Lesson for us |
|---|---|---|---|
| **Smart Connections** (Obsidian) | Active. Smart Environment v3 has more local embedding models and switches models without re-embedding. Core is free and local; Pro adds inline connections and semantic neighborhoods ([smartconnections.app](https://smartconnections.app/smart-connections/), [obsidianstats](https://www.obsidianstats.com/plugins/smart-connections)). | Embedding-based "related notes" shown beside the note you are writing. No rewriting. | Users value related-notes surfacing and rarely use the chat. Reported issues: misses nuanced links with small models, lag at 8,000 to 10,000 notes, indexing bugs ([GitHub #1379](https://github.com/brianpetro/obsidian-smart-connections/issues/1379)). Retrieval suggestions beat generated summaries. |
| **Khoj** | Hosted cloud **sunset 2026-04-15**. Open source (AGPL) continues, about 35.6K stars, latest release 2.0.0-beta.28 (March 2026) ([promptquorum](https://www.promptquorum.com/power-local-llm/khoj-ai-second-brain-review), [ideaproof](https://ideaproof.io/open-source/project/khoj)). | Chat and search over notes, PDFs and Notion, with local or cloud LLMs. | Hosted PKM products are fragile. Keep the store in local plain files. |
| **Mem** | Mem 2.0 is a full rebuild ("AI thought partner"); launch dates are inconsistent across sources ([Mem blog](https://get.mem.ai/blog/introducing-mem-2-0)). | Auto-organizing and proactive resurfacing, with no manual structure. | Earlier "no folders, the AI organizes" versions drew complaints about retrieval and trust. Proactive resurfacing is the part worth copying. |
| **Reflect** | Active. Backlinks, daily notes, end-to-end encryption, AI for editing and Q&A over your notes ([klickreflex](https://klickreflex.substack.com/p/pros-and-cons-of-reflect-notes-app)). | Light: the AI polishes text and answers from your notes. "Unlinked mentions" with accept/decline. | **Proposed links with accept/decline** is a good human-gated promotion pattern. |
| **NotebookLM** | Active. In 2026: auto-categorize sources, editable flashcards (June), EPUB, Drive sync, Studio outputs (mind map, briefing doc, reports) ([Workspace blog](https://workspaceupdates.googleblog.com/2026/04/expanded-notebooklm-capabilities-for-Education-Plus-and-Teaching-and-Learning-add-on-customers.html), [pasqualepillitteri](https://pasqualepillitteri.it/en/news/1391/notebooklm-april-2026-update-auto-label-flashcards)). | Answers grounded in a per-notebook source set, with citations. Outputs are derived, and sources remain the authority. | Source-grounded synthesis with citations is the trust model. Synthesis does not write back into the sources. |
| **Claude memory / Projects / Cowork** | Since 2026-08-25, memory is unified across chat and Cowork (cloud Cowork only). Memory updates during the conversation rather than in a daily batch. Items are listed under Topics in settings and can be edited or deleted. Each Cowork project has its own memory, plus optional account memory ([TechCrunch](https://techcrunch.com/2026/08/25/claude-cowork-finally-remembers-what-you-told-the-app-in-chat/), [Claude help: Cowork projects](https://support.claude.com/en/articles/14116274-organize-your-tasks-with-projects-in-claude-cowork)). | Implicit extraction of facts and preferences, scoped by project. | Built-in memory is a *flat* store with no levels, promotion or evidence. The harness should keep its own leveled ledger, and treat Claude memory as a capture source, like the `auto-memory` value in `evidence_source`. |
| **Karpathy "LLM Wiki"** (gist, April 2026; read directly) | The pattern behind most 2026 repos. | Three layers: **raw/** (immutable sources), **wiki/** (pages the LLM owns: summaries, entities, concepts, comparisons, overview), and a **schema** file (CLAUDE.md or AGENTS.md, co-evolved by human and LLM). Three operations: **ingest** (one source may touch 10 to 15 pages; supervised one source at a time), **query** (answers with citations; "good answers can be filed back into the wiki as new pages"), **lint** (contradictions, stale claims, orphans, missing concept pages and cross-references). `index.md` is the content catalog, read first. `log.md` is append-only, with entries like `## [YYYY-MM-DD] ingest \| Title`. The human curates, asks questions and decides meaning; the LLM does the bookkeeping. | Reported failures: at about 50 sources, silent staleness when sources change; the risk of fabricated pages; "a fancy name for a cache layer"; scale limits at a few hundred pages ([fdicostanzo](https://fdicostanzo.com/posts/2026/20260427_karpathy_llm_second), [innobu](https://www.innobu.com/en/articles/karpathy-llm-wiki-second-brain-enterprise-reality.html), [faafospecialist](https://faafospecialist.substack.com/p/a-practical-guide-to-building-an)). |

---

## 5. Community "second brain with Claude Code" repos, ranked

Ranked by stars, recency and substance (as of 2026-10-16). Inflated stars are discounted. All repos were pushed within the last week unless noted.

| # | Repo | Stars | Created | What is actually worth stealing (from reading the clone) |
|---|---|---|---|---|
| 1 | [AgriciDaniel/claude-obsidian](https://github.com/AgriciDaniel/claude-obsidian) | 15,580 | 2026-04 | Karpathy pattern with real **evidence discipline**: separate ledgers for ingestion (`.raw/.manifest.json`), sources (`source-ledger.json`) and claims (`claim-ledger.json`).<br>• Claim `assessment` values: accepted, provisional, contested, unsupported, deprecated.<br>• "Accepted claims need at least one fresh, active, non-synthetic source. High-risk accepted claims need two independent sources", where sources sharing an `independence_key` do not count as independent.<br>• "Do not treat a frontmatter confidence label as evidence."<br>• Note `status` runs `seed → developing → mature → evergreen`.<br>• A `wiki-fold` skill does **extractive, idempotent log roll-ups**: batch size is 2^k with k=4 by default, every outcome cites its entry, and a cross-entry theme needs 2 or more contributing entries. It never folds folds, is dry-run by default, and "adds no new factual evidence, so it does not upgrade claim assessments".<br>• `hot.md` is a bounded recent-context cache.<br>• Deterministic read-only lint.<br>• Mode templates for PARA, Zettel and LYT. |
| 2 | [eugeniughelbur/obsidian-second-brain](https://github.com/eugeniughelbur/obsidian-second-brain) | 4,783 | 2026-03 | 45+ commands, including `/obsidian-emerge` (names patterns you have not stated), `/obsidian-graduate` (idea to project; sets `status: graduated` and `graduated-from:`, and the idea note stays as "origin story"), `/obsidian-decide`, `/obsidian-reconcile` and `/obsidian-challenge`.<br>• An **OKM freshness policy** enforced by `freshness_lint.py`: "every stored fact must be timeless, dated, or a pointer"; a present-tense fast fact with no `(as of YYYY-MM-DD)` stamp is an error (FRESH-1); stamps older than 7 days warn (FRESH-2); dated containers are immutable (FRESH-4).<br>• "AI-first" notes have a `## For future agent` preamble.<br>• Anti-fabrication rule: "false absence is the most common failure mode." |
| 3 | [SamurAIGPT/llm-wiki-agent](https://github.com/SamurAIGPT/llm-wiki-agent) | 3,628 | (old repo, repurposed) | **Promotion gate `draft → stable`**: links the graph proposes start as DRAFT and are not written into the page body. A `promote` pass checks source grounding and consistency, and a page needs **2 or more outbound links** before promotion. Hard rule: never auto-create pages from broken links, because "LLM ingest produces hallucinated wikilinks". Uses NetworkX and Louvain communities to find structure candidates. |
| 4 | [alchaincyf/obsidian-ai-orange-book](https://github.com/alchaincyf/obsidian-ai-orange-book) | 1,468 | 2026-04 | A guide in Chinese (not cloned). |
| 5 | [huytieu/COG-second-brain](https://github.com/huytieu/COG-second-brain) | 1,287 | 2025-10 | `memory-hygiene` skill against "**stale-but-confident**" memory: monthly, it re-verifies environment-dependent claims (paths, URLs, IDs) with cheap checks, stamps `last_verified` and `confidence`, and proposes archiving. "Unverifiable ≠ drifted." `/harvest` puts session learnings in a staging area that **a human promotes** into `05-knowledge/`. The worker "never grades its own homework". |
| 6 | [undefined-ui/second-brain-os](https://github.com/undefined-ui/second-brain-os) | 1,096 | 2026-09 | A long guide and starter vault. "Atomic means it has one [idea]", not that it is short. A lineage page on Zettelkasten, PARA and evergreen notes. Weekly ritual: hand-grade 5 random real runs. |
| 7 | [coreyhaines31/makerskills](https://github.com/coreyhaines31/makerskills) | 864 | 2026-06 | `/decide` skill, based on 37signals' 38 questions plus a house Q39 (opportunity cost):<br>• Capture stakes (low/med/high), reversibility (easy / hard / one-way door) and deadline.<br>• Triage to **6 to 8 questions**, because more causes paralysis.<br>• Capture the **first instinct before analysis**.<br>• Five possible calls: decide / decide smaller / wait / don't decide / wrong person.<br>• **Revisit dates by type**: 30 days for tools and processes, 90 days for strategy, 90 to 180 days for hires and partnerships.<br>• An "Expected outcome" field and an INDEX line per decision. |
| 8 | [coleam00/second-brain-starter](https://github.com/coleam00/second-brain-starter) | 808 | 2026-03 | A PRD generator (not cloned). |
| 9 | [swarmclawai/swarmvault](https://github.com/swarmclawai/swarmvault) | 719 | 2026-04 | LLM wiki with a graph and MCP (not cloned). |
| 10 | [itechmeat/open-second-brain](https://github.com/itechmeat/open-second-brain) | 487 | 2026-05 | The best **promotion/decay state machine** found. Feedback signals go to the inbox. A deterministic "dream" pass (no LLM) makes a preference `Unconfirmed` once there are at least `candidate_threshold` same-sign signals. The first applied evidence makes it `Confirmed`. Retirement routes:<br>• Expired: no evidence before `unconfirmed_until`.<br>• Quarantine: violated ≥ applied.<br>• Stale: `last_evidence_at` is older than N days.<br>• Rebutted: opposite-sign signals arrive.<br>• Superseded: evidence marked "outdated".<br>• User-rejected, with a reason.<br><br>Records carry `_applied_count`, `_violated_count`, `_confidence_value` and `pinned`; pinned records skip natural decay. Corrections report a "blast radius". A retired record is served only beside its correction. Snapshots and a hash-chained log. |
| 11 | [anh-chu/llm-wiki-pm](https://github.com/anh-chu/llm-wiki-pm) | 6 | 2026-04 | Low stars but a strong design:<br>• **Supersession flow**: `supersedes`/`superseded_by`, the old page is archived and inbound links are rewritten; dry run first, and an explicit count is required for 10 or more rewrites.<br>• **Crystallize**: transcripts and multi-source threads become a digest of Context, Decisions, Action Items, Patterns and Contradictions; reusable lessons are extracted into separate concept pages.<br>• Writes require a read hash, so stale reads are refused.<br>• Every claim gets an inline `[source: …]`.<br>• "Never build a page only from other wiki pages."<br>• Unresolved conflicts keep both claims, each dated.<br>• Daily briefs rotate out after 5 days. |
| 12 | [keytechx/2nd-brain](https://github.com/keytechx/2nd-brain) | 13 | 2026-08 | The best decision-log skill found. Its stance is "clerk of the court, not advisor": **never improve the reasoning while recording it**. Six questions: decision; what forced it; alternatives; **load-bearing assumption**; expected outcome plus **confidence 1 to 10**; revisit date plus **tripwires**. It pushes once on vague rationale. Retrospective entries are dated to when the decision was actually taken and flagged as retrospective. A note with no alternative "was probably not a decision". Unfinished interviews are saved as `proposed` with blank answers. The decision log never contacts the web, because outside facts would contaminate the record of what was known that day. Weekly, monthly and strategy reviews read the decision log. The weekly review puts "the uncomfortable finding at the top" and "names missing days". |
| 13 | [breferrari/obsidian-mind](https://github.com/breferrari/obsidian-mind) | n/a | active | **Atomicity rule**: split a note once it has 3 or more independent sections. Graph roles: **evidence nodes** link out to concepts; **concept nodes** stay definitional and receive evidence via backlinks; **index nodes** curate links. A `promoted:` marker with a block anchor lets recall serve the promoted block. A SessionStart hook injects North Star, active work and drift flags. |
| 14 | [yuchenz27/wikigarden](https://github.com/yuchenz27/wikigarden) | 2 | 2026-07 | **Two layers with two owners**: `wiki/` is written by the AI (bookkeeping), and `garden/` holds atomic notes written by hand that the AI is **forbidden** to write, because restating an idea in your own words is the learning. `/morning` and `/sunset` rituals. |

**What all 14 repos share.**
- Everything is plain Markdown plus YAML, git-versioned, with a CLAUDE.md or AGENTS.md schema.
- They converge on the Karpathy ingest, query and lint loop.
- The mature ones add **provenance ledgers, supersession, freshness stamps, human-gated promotion and deterministic (non-LLM) lifecycle passes**.

**What none of them solves.** Retrieval quality beyond a few hundred pages; most rely on qmd or hybrid search plus an index note. Most also lack outcome scoring that separates decision quality from outcome quality.

---

## 6. Cross-cutting findings: what works and what fails

**What works (consistent across methods and repos).**
1. **Few, explicit levels with different owners and lifetimes.** Examples: fleeting to permanent to structure (Zettelkasten); raw to wiki to schema (Karpathy); wiki owned by the AI and garden owned by the human (wikigarden).
2. **Promotion is earned by use or evidence, not by time.** Examples: Forte's revisit-driven layers; open-second-brain's applied/violated counts; llm-wiki-agent's gate requiring 2 or more links plus grounding; Milo's squeeze point.
3. **Structure emerges bottom-up.** Structure notes and MOCs are built at the squeeze point and never planned up front.
4. **Immutability plus supersession.** Decisions are never edited. A new record supersedes the old one, the old one is kept as evidence, and links are rewritten (ADR, llm-wiki-pm, 2nd-brain).
5. **Predictions recorded before the fact, compared at a scheduled point** (Duke, AAR, Kata, ADR Confirmation, makerskills revisit dates).
6. **Freshness discipline.** Every fact is timeless, dated or a pointer (OKM). `last_verified` re-verification (COG).
7. **Deterministic hygiene.** Lint, fold and dream passes are scripts, not LLM judgment. The LLM proposes and the script or human disposes.
8. **Human-gated synthesis.** Reflect's accept/decline mentions, COG's harvest staging, and claude-obsidian's dry-run-then-apply.

**What fails.**
1. **Note bloat and the collector's fallacy.** Capture is cheap, promotion never happens, and literature notes pile up.
2. **Over-structuring.** The taxonomy becomes the hobby (Tana tag trees, Zettelkasten tooling rabbit holes), or a template is so heavy that nobody writes records (full MADR).
3. **No retrieval.** Notes exist but are never surfaced at decision time. The graph view is decorative, and Dataview output is invisible to search.
4. **Stale but confident.** AI-maintained pages drift silently when sources change (the Karpathy wiki at about 50 sources, COG's memory).
5. **Fabricated structure.** LLMs invent wikilinks and pages, and auto-created pages amplify the noise (llm-wiki-agent HG-WA-01).
6. **Logs nobody revisits.** Decision journals and ADRs without a scheduled revisit or tripwire become write-only.
7. **Hindsight contamination.** Reasoning gets tidied up at record time, or a decision is logged after the fact without being flagged as retrospective.
8. **Synthesis from synthesis.** Pages built only from other pages lose provenance (llm-wiki-pm rule; claude-obsidian folds do not upgrade claims).

---

## 7. Adaptations for the harness ontology and skills

The harness already has the L0 to L5 ladder (`pattern_level`), the `pattern_status` lifecycle, and types for `Decision`, `Lesson`, `Preference`, `ResearchNote`, `Principle` and `MetaPattern`. `ontology.yaml` leaves room for a separate `abstraction_level` axis, orthogonal to the ladder. The proposals below fill that axis and harden promotion rules and decision quality. They are **proposals for a reviewed PR**, not changes made.

### 7.1 A knowledge-note ladder (the `abstraction_level` axis)

This axis is for ideas and knowledge, the counterpart to the behavior-pattern ladder:

| Level | Name (PKM origin) | Example harness store | Owner | Lifetime / rule |
|---|---|---|---|---|
| K0 | **capture** (fleeting / Karpathy raw) | `Event` content, inbox jsonl, Claude memory exports | anyone | Triaged within 72 h or `expired`. Raw sources are immutable. |
| K1 | **source note** (literature / PS L1 to L3) | `ResearchNote` / `Document` digest | agent | Must cite a source. `distill_layer` 1 to 3. |
| K2 | **claim / concept** (permanent / evergreen) | new `Note{kind: claim\|concept}` | agent drafts, **user approves** | A claim title is required. One idea. At least 2 typed links. At least 1 grounded source; 2 independent sources if high-risk. |
| K3 | **structure** (structure note / MOC) | new `Note{kind: structure}` | agent proposes at squeeze | Created only when 10 or more K2 notes share a scope and none covers them. Ordered and annotated links. |
| K4 | **principle** | existing `Principle` | user | Distilled from 2 or more K2/K3 notes across 2 or more areas (already required). |

Proposed `Note` record (JSONL, append-only, event-sourced like `Pattern`):

```yaml
Note:
  id_prefix: note_
  unique_id: false            # latest line per id wins
  fields: [id, ts, abstraction_level, kind, title, body_path, anchor, status, scope, areas,
           sources, links, distill_layer, revisit_reason, ip_kind, assessment, risk,
           last_verified, stale_after, supersedes, superseded_by, promoted_from, origin,
           approved_on, review_by, applied_count, contradicted_count, intent, situation, meta]
  enums:
    abstraction_level: [K0, K1, K2, K3, K4]
    kind: [capture, source, claim, concept, question, structure, outtake]
    status: [seed, developing, approved, evergreen, stale, superseded, retired]
    assessment: [accepted, provisional, contested, unsupported, deprecated]   # claude-obsidian
    ip_kind: [distilled, outtake, wip, deliverable, external]                  # Forte IPs
  links: [{to: note_x, rel: supports|contradicts|refines|example-of|up|related, why: "…"}]
```

**Promotion criteria.** These are checked by a deterministic script (`scripts/notes.py lint/promote`). The LLM only drafts.

| Transition | Rule |
|---|---|
| K0 to K1 | It has a source pointer and a summary in our own words. |
| K1 to K2 | `title` is a claim (lint: contains a verb, ≤ 120 chars, not a bare noun phrase).<br>One idea (split if 3 or more independent sections).<br>`links` has 2 or more typed links, each with a `why`.<br>`sources` has at least 1 grounded source, not only other notes.<br>The user approves it (`approved_on`). |
| K2 to evergreen | `applied_count` is 2 or more: it was cited in a Decision, Lesson or deliverable in 2 or more sessions.<br>No unresolved `contradicts` link. |
| K2 to K3 proposal | The squeeze lint fires when 10 or more K2 notes share a scope or tag and none has an `up` link to a structure note. |
| Any to stale | Its `stale_after` date has passed, or a cited source changed hash. |
| Any to superseded | A new record carries `supersedes`. The old record is never edited (append a status line). Dry run first. |
| Distill layer +1 | Only with a `revisit_reason` that points to a live project or decision event (Forte's opportunistic rule). |

Add an **OKM-style freshness lint** for every K1 to K3 body: each fast fact must be stamped `(as of YYYY-MM-DD)` or be a pointer.

### 7.2 Decision v0.3: separate decision quality from outcome quality

Extend the existing `Decision` (current fields: `claim`, `reasons`, `evidence`, `alternatives`, `expected_outcome`, `review_date`). New fields, split into those recorded **at decision time** and those recorded **at review**:

```yaml
# at decision time (immutable after status: made)
status: [proposed, made, revisit, reviewed, superseded]
stakes: [low, medium, high]
reversibility: [two-way, hard, one-way]               # makerskills / Bezos doors
forced_by: "what changes if we do nothing"
alternatives: [{option, why_rejected}]                 # required >=1, else flag "not a decision"
first_instinct: "…"                                    # captured before analysis
load_bearing_assumption: "…"                           # 2nd-brain / ADR-rots
assumption_check: YYYY-MM-DD
expected_outcome: "…"                                  # falsifiable
p_success: 0.0-1.0                                     # or confidence 1-10
tripwires: ["evidence that it is going wrong"]
premortem: ["reasons it failed", …]                    # optional; only for stakes: high or one-way
confirmation: "how we will check it was implemented"   # MADR
retrospective: false                                   # true if logged after the fact
info_state: [pointers to notes/research known at the time]   # no web fetch at record time
review_date: YYYY-MM-DD                                # default by kind: tool/process 30d, strategy 90d, people 90-180d
# at review (append a review record, never edit the original)
actual_outcome: "…"
outcome_quality: [good, mixed, bad, unknown]
decision_quality: [sound, flawed, unclear]            # judged on info_state, NOT on outcome
luck_vs_skill: [deserved-success, bad-luck, dumb-luck, deserved-failure]   # Duke 2×2
gap_why: "…"                                          # AAR Q3
sustain: [...]; improve: [...]                         # AAR Q4 -> Lesson candidates
calibration_delta: actual(0/1) - p_success
```

Skill rules, taken from the best repos:
- **Clerk-of-the-court mode**: record the user's words, never improve the reasoning, and keep a thin rationale as thin.
- Push **once** on vague answers.
- Ask at most **6 to 8** questions.
- Save unfinished interviews as `proposed`.
- At review, **reread the original file** and score `decision_quality` against `info_state` before looking at `actual_outcome`.

### 7.3 Pattern and Preference lifecycle: adopt open-second-brain's counters

The harness `pattern_status` already has candidate, proposed, approved, encoded, decaying, retired and reopened. Make the transitions **countable and deterministic**:
- Add `applied_count`, `violated_count`, `last_evidence_at`, `pinned` and `retired_reason` (expired | stale | rebutted | quarantine | superseded | user-rejected).
- `candidate → proposed` when there are `support ≥ 3` same-sign episodes in 2 or more sessions.
- `encoded → decaying` when `violated ≥ applied` after N uses, or when there is no evidence for 60 days.
- `decaying → retired` when one more violation arrives or the stale window passes.
- Pinned records skip natural decay.
- Serve a retired record only beside its correction.
- The `review-week` skill shows the transitions; the script computes them.

### 7.4 Folding and convergence (L0 to L1 to L2, safely)

- Port claude-obsidian's **extractive fold** to `log/YYYY-MM.jsonl`:
  - Fixed batches (16 events).
  - A deterministic fold ID (`fold-k4-from-…-to-…-n16`).
  - Every theme cites 2 or more event ids, and numbers must trace back to events.
  - **Folds never upgrade evidence and never fold folds.**
  - Folds are where L2 pattern candidates come from.
- **Crystallize** (llm-wiki-pm): when a session holds decisions, `retro` emits a digest of Context, Decisions (to `Decision`), Actions (to `ProgressItem`), Patterns (to `Pattern` candidates) and Contradictions (to `contradicts` links). It extracts reusable lessons as separate `Lesson` or K2 notes and does not bury them in the digest.
- **Proposed links** (Reflect, llm-wiki-agent): the agent writes link proposals as `status: draft` with a `why`. They become real links only when the user accepts them or the promote gate passes. Never auto-create a target from a hallucinated link.

### 7.5 Retrieval, so notes get used

- Keep a short, bounded **`hot.md`** (claude-obsidian) or SessionStart injection (obsidian-mind) that carries:
  - open decisions with review dates in the next 14 days
  - tripwires
  - active K3 structure notes for the current scope
  - top evergreen claims by `applied_count`
- `index.md` is the catalog, read first for queries (Karpathy).
- Hybrid search (qmd or embeddings) is a fallback, not the primary path.
- "Related notes" are surfaced inline when drafting, as Smart Connections does, rather than as chat.

---

## 8. Recommended practice design (for the personal AI harness)

**Principle: few levels, earned promotion, deterministic hygiene, the human thinks, the agent keeps the books.**

1. **Two ladders, one store.** Keep the behavior ladder (L0 to L5: Event, episode, Pattern, Encoding, Principle, MetaPattern). Add the idea ladder K0 to K4 as the `abstraction_level` axis on a new `Note` type. Both are append-only JSONL in `harness-data`, and the Markdown bodies are views. Do not add more levels: Forte's five layers and Tana's tag trees show that extra levels become ceremony.

2. **Owners per level** (the wikigarden and Karpathy split).
   - K0 and K1: the agent writes freely, with sources required.
   - K2 claims: the agent drafts, the user approves with one keystroke (accept, edit or reject). Optionally, a `garden/` folder the agent may not write, for ideas the user wants to own by writing them.
   - K3 structure: the agent proposes only when the squeeze lint fires.
   - K4 principle: the user approves (this already exists).

3. **Promotion is evidence-gated and checked by scripts** (§7.1 and §7.3): claim title, one idea, 2 or more typed links with a `why`, a grounded source, and use counts. The LLM never changes `status`; `scripts/notes.py` and `scripts/patterns.py` do, after approval.

4. **Decision log as the convergence point.** Every Decision cites the K2 notes and Patterns it relied on (`info_state`). At review, `applied_count` increments for notes that informed sound decisions, and `contradicted_count` for notes that misled. This is how ideas converge toward evergreen, and how bad notes decay, using real use instead of rereading.

5. **Decision-quality fields** (§7.2) and **clerk mode**. Record the prediction (`p_success`), the load-bearing assumption and tripwires before the fact. At review, score decision quality on `info_state` before looking at the outcome, then fill in the Duke 2×2 and an AAR gap. Run a pre-mortem only for high-stakes or one-way-door decisions; otherwise it becomes friction.

6. **Review rituals, short and scheduled.**

   | Cadence | Ritual | Skill | Time |
   |---|---|---|---|
   | After any non-trivial task | AAR, 4 questions; sustain/improve become Lesson candidates | `retro` | ≤ 3 min |
   | Daily (morning) | `hot.md` refresh; K0 triage (promote, discard or expire after 72 h); decisions due | SessionStart hook plus a `morning` step | 2 min |
   | Weekly | Approve or reject K2 drafts and draft links; pattern transitions; decisions past `review_date` scored (decision quality vs outcome quality); "uncomfortable finding first"; name missing days | `review-week` | 15 min |
   | Monthly | Freshness lint, `last_verified` sweep (COG), squeeze-lint structure proposals, extractive folds, calibration report (Brier score / `calibration_delta` by area) | new `review-month` or `memory-hygiene` | 30 min |
   | Quarterly | Principle distillation from evergreen K2/K3; MetaPattern review (encodings unused or overridden); prune: archive K1 notes never promoted after 90 days | `distill-principles`, `pattern-review` | 1 h |

7. **Anti-bloat and anti-rot guards.**
   - K0 expires.
   - K1 notes that are never promoted are archived at 90 days.
   - Distill layers rise only on a revisit with a reason.
   - The freshness lint blocks unstamped fast facts.
   - Supersession, never an edit.
   - Never build a K2 note only from other notes.
   - No auto-created pages from broken links.
   - Fold outputs never upgrade evidence.

8. **Retrieval first.** Every stored item must be reachable by one of: the `hot.md` injection, the `index.md` catalog, a typed query (`scripts/notes.py query --scope … --kind claim --status evergreen`), or hybrid search. If a type is never retrieved in a quarter, the MetaPattern review flags it for removal. That catches over-structuring.

9. **Treat Claude's built-in memory as K0.** It is unified across chat and Cowork since 2026-08-25 and scoped by project, but it is flat. Import its topics periodically as `evidence_source: auto-memory` captures. Never treat it as the ledger.

10. **Start minimal.**
    - Phase 1: the `Note` type with K0 to K2 only, plus the Decision v0.3 fields, plus the weekly review.
    - Phase 2: add K3 squeeze proposals, folds and the freshness lint, but only after there are 30 or more K2 notes.
    - Phase 3: add the dream-style counters for Patterns and Preferences.

    Each phase ships behind the existing eval gate (D3).

---

## Sources (primary reads marked [read])

- Karpathy, LLM Wiki gist [read]: https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f
- Repos [read, shallow clone]: AgriciDaniel/claude-obsidian, eugeniughelbur/obsidian-second-brain, SamurAIGPT/llm-wiki-agent, huytieu/COG-second-brain, undefined-ui/second-brain-os, coreyhaines31/makerskills, itechmeat/open-second-brain, anh-chu/llm-wiki-pm, keytechx/2nd-brain, breferrari/obsidian-mind, yuchenz27/wikigarden, jessepinkman9900/claude-second-brain, adr/madr, joelparkerhenderson/architecture-decision-record, obsidianmd/jsoncanvas, khoj-ai/khoj
- Zettelkasten (secondary): https://www.ernestchiang.com/en/posts/2025/sonke-ahrens-how-to-take-smart-notes/ · https://myflexnote.com/blog/zettelkasten-method-guide · https://zettelkasten.de/posts/zettelkasten-hubs/ · https://forum.zettelkasten.de/discussion/comment/12565 · https://news.ycombinator.com/item?id=23386630
- Matuschak (secondary): https://notes.andymatuschak.org/Evergreen_notes_should_be_concept-oriented · https://notes.andymatuschak.org/Evergreen_note_titles_are_like_APIs · https://jarango.com/2023/02/02/evergreen-notes/
- Forte (secondary): https://fortelabs.com/blog/progressive-summarization-iii-guidelines-and-principles/ · https://concepts.dsebastien.net/concept/progressive-summarization/ · https://thomasjfrank.com/productivity/books/the-para-method-by-tiago-forte-summary-and-book-notes/ · https://workflowy.com/help/para-method · https://medium.com/@subin.khullar/summary-building-a-second-brain-dd80989b1f87
- LYT (secondary): https://blog.linkingyourthinking.com/notes/lyt-glossary · https://www.linkingyourthinking.com/ideaverse/benefits-of-lyt-frameworks · https://smithery.ai/skills/mrfelton/ideaverse
- Tana: https://tana.inc/docs/fields · https://nesslabs.com/tana-task-management · https://github.com/jcfischer/supertag-cli
- Heptabase: https://wiki.heptabase.com/use-case-and-workflow · https://wiki.heptabase.com/a-simple-method-to-convert-your-thinking-into-writing
- Obsidian Bases/Dataview: https://www.dsebastien.net/the-complete-guide-to-dataview-in-obsidian/ · https://abdulkadersafi.com/blog/dataview-vs-datacore-vs-bases
- Roam/Logseq: https://ponder.ing/blog/logseq-vs-roam-research · https://discuss.logseq.com/t/is-the-ability-to-reference-embed-a-block-a-killer-feature/8002
- Decisions: https://readcrucible.com/articles/decision-journals-the-practice-the-science-the-templates · https://grahammann.net/book-notes/thinking-in-bets-annie-duke · https://benmeer.com/newsletter/decision-journal/ · https://corporate.jasoncollins.blog/premortem · https://theuncertaintyproject.org/tools/pre-mortem
- ADR: https://hidekazu-konishi.com/entry/architecture_decision_records_templates_and_operations.html · https://dev.to/andriiboyko/the-adr-that-rots-isnt-the-decision-its-the-assumption-under-it-3mnd · https://www.neilsherman.co.uk/blog/architecture-decision-records.html
- AAR: https://www.adi.org/downloads/After-Action-Review-Guide.pdf · https://apps.dtic.mil/sti/pdfs/ADA368651.pdf
- Kata: https://www.theleansixsigmacompany.com/uk/library/coaching-kata/ · https://concepts.dsebastien.net/concept/coaching-kata/
- LLM tools: https://smartconnections.app/smart-connections/ · https://github.com/brianpetro/obsidian-smart-connections/issues/1379 · https://www.promptquorum.com/power-local-llm/khoj-ai-second-brain-review · https://get.mem.ai/blog/introducing-mem-2-0 · https://klickreflex.substack.com/p/pros-and-cons-of-reflect-notes-app · https://workspaceupdates.googleblog.com/2026/04/expanded-notebooklm-capabilities-for-Education-Plus-and-Teaching-and-Learning-add-on-customers.html · https://techcrunch.com/2026/08/25/claude-cowork-finally-remembers-what-you-told-the-app-in-chat/ · https://support.claude.com/en/articles/14116274-organize-your-tasks-with-projects-in-claude-cowork
- LLM-wiki criticism: https://fdicostanzo.com/posts/2026/20260427_karpathy_llm_second · https://www.innobu.com/en/articles/karpathy-llm-wiki-second-brain-enterprise-reality.html · https://faafospecialist.substack.com/p/a-practical-guide-to-building-an
