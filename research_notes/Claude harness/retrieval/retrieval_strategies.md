# Retrieval strategies for the harness: the right method per query (research notes, 2026-10-16)

Scope: how Claude Code agents in the personal harness should *find* things in its stores without flooding
their context: append-only JSONL events with intent labels, patterns, decisions, the research ledger,
project knowledge wikis converted from PDFs (some Korean), the message vault, and style pairs. This note
gives a query-type → method decision matrix, a layered retrieval stack with token budgets, and an eval
plan with a small gold set.

Read first: `claude-harness/schema/STORAGE.md`, `schema/event.md`,
`research_notes/Claude harness/organization/data_architecture.md` (bronze JSONL → silver Parquet →
`index.sqlite` with FTS5 trigram + sqlite-vec), `intent/realtime_labeling_stack.md` §4 (bge-m3 +
sqlite-vec + RRF already sketched) and `abstraction/ai_abstraction.md` §1.12–1.14 (RAPTOR, GraphRAG,
Letta). This note **builds on those** and changes three things in them (see §0, items 4, 5 and 7).

Evidence tags: **[V]** checked this session (cloned source, an official page fetched, or a README table);
**[measured]** I ran it here, on a 4-core Linux cloud VM with SQLite 3.45.1, *not* a Mac, so treat
absolute times as rough; **[S]** search snippets or third-party pages only; **[M]** memory or my own
inference; **[est]** estimate to measure before relying on it.

Repos cloned read-only (nothing installed from them, nothing run) under
`/tmp/claude-0/-home-user-albers-club/1397d302-c3cb-5329-ad06-e45b2c66c6d1/scratchpad/retrieval/`:
`KURE` (nlpai-lab, 2026-10-13), `LightRAG` (2026-10-14), `graphiti` (2026-10-15), `HippoRAG` (2026-10-06),
`LongMemEval` (2026-05-11), `LLMLingua` (2026-09-10), `kiwipiepy` (2026-10-17), `qmd` (tobi, 2026-10-14),
`sqlite-vec` (2026-05-17), `FlagEmbedding` (2026-08-24), `locomo` (2024-08-12), `mem0` (2026-10-14),
`graphrag` (microsoft, 2026-10-08), `raptor` (2024-09-03), `beir` (2025-10-16), `Qwen3-Embedding`.
Test scripts I wrote and ran: `.../scratchpad/retrtest/{ko_fts.py,vec_bench.py,vec_bench2.py,fts_bench.py,duck.py}`
(scratch venv with `kiwipiepy 0.24.0`, `sqlite-vec`, `duckdb`).

**Unreachable:** the proxy returned 403 for `arxiv.org`, `export.arxiv.org` and `huggingface.co`
(so no paper PDFs, model cards or HF leaderboards were read directly; their numbers come from repo
READMEs [V] or search snippets [S]). The `anthropic.com/engineering/building-agents-with-the-claude-agent-sdk`
URL redirects to `claude.com/blog/...`, which was fetched.

---

## 0. TL;DR (the decisions)

1. **Route by query type, not one retriever for everything.** Most harness questions are *exact* (an id,
   a filename, a phrase, a date range, a facet like client or scope). For those, `rg`/Glob and SQL over
   the silver tables are faster, cheaper and more accurate than any embedding. Anthropic's own guidance
   is "start with agentic search, and only add semantic search if you need faster results"; semantic
   search is "usually faster than agentic search, but less accurate, more difficult to maintain, and less
   transparent" [V, claude.com blog]. Boris Cherny: early Claude Code "used RAG + a local vector db, but
   we found pretty quickly that agentic search generally works better", and it avoids "security,
   privacy, staleness, and reliability" problems [S, X post].
2. **Default stack = 4 layers + 2 special-purpose ones**, cheapest first, each escalated only on a miss:
   - **L0 catalog** (always loaded, about 300–600 tokens): what stores exist, their counts, date range,
     the facet vocabularies (scopes, clients, kinds), and the `recall` commands. This is progressive
     disclosure step 1.
   - **L1 exact**: `rg` / Glob on bronze, and **parameterized SQL** (DuckDB over silver Parquet, or SQLite
     `index.sqlite`) for ids, phrases, facets, counts and "as of" queries.
   - **L2 hybrid lexical + dense**: FTS5 (trigram **plus** a Kiwi-morpheme column for Korean) + sqlite-vec
     KNN, fused with RRF, with structured filters applied *before* ranking.
   - **L3 rerank**: a local cross-encoder over the top 30–50 fused candidates, only when L2 returns more
     plausible hits than the budget allows.
   - **G graph** (multi-hop, "which patterns relate", "everything about client Y"): a *deterministic*
     edge table built from ids the harness already writes (`pointers`, `corrects`, `labels_for`,
     `parent_event`, pattern evidence, client/project refs) plus Personalized-PageRank-style expansion.
     No LLM entity-extraction graph (GraphRAG/LightRAG) for logs; consider LightRAG only for big
     document wikis.
   - **S summaries** (global questions: "what are my recurring problems this quarter"): the reflection
     tree from `ai_abstraction.md` §4.5 (RAPTOR-style, with evidence pointers) plus weekly/monthly
     rollups, searched *alongside* leaves.
3. **Return hit lists, not documents.** Every retrieval call returns at most ~1.5k tokens: id, ts, type,
   scope, score, a ≤200-character snippet and a pointer. The agent expands individual ids on demand
   (`recall get <id>`, ≤2k tokens). A question's total retrieval budget is **8k tokens soft, 15k hard**;
   subagents doing bulk retrieval return a 1–2k distilled summary, which matches Anthropic's
   "often 1,000-2,000 tokens" for sub-agent returns [V, effective-context-engineering post].
4. **Korean needs two lexical indexes, not one.** I measured (toy corpus, §2.4) that FTS5 `trigram`
   **silently returns nothing** for 2-syllable queries such as 납기, 보험, 말투, 변환, and a Kiwi morpheme
   index fixes particles (보험금을 → 보험금) but misses sub-compounds (계약 inside 계약서). Use
   `trigram` + a Kiwi-morpheme `unicode61` column, and a `LIKE '%..%'` fallback for queries under 3
   characters. This corrects `data_architecture.md` §2.4, which treats trigram as enough.
5. **Embedding model for Korean+English: keep bge-m3 as the default, but plan KURE.** On the nine
   MTEB(kor, v2) retrieval tasks: bge-m3 0.7509 nDCG@10, KURE-v1 (bge-m3 fine-tune, same size) 0.7616,
   Qwen3-Embedding-0.6B only 0.7140, Qwen3-Embedding-8B 0.7826, and the 154M late-interaction
   **KURE-v2 0.8160, the best of every model listed, including 8B dense models** [V, KURE README].
   For the harness's mixed Korean/English text, start with bge-m3 (also strong in English, 8K context)
   and A/B test KURE-v1 (drop-in) and KURE-v2 (multi-vector) on the gold set.
6. **Reranker: KURE-Reranker-nano or bge-reranker-v2-m3 locally.** On Korean, KURE-Reranker-nano (149M)
   scores 0.8757 nDCG@10 at 482 pairs/s versus bge-reranker-v2-m3 (568M) 0.8518 at 413 pairs/s, and
   Qwen3-Reranker-8B 0.8990 at 15 pairs/s (A6000) [V, KURE README]. LightRAG's README recommends
   bge-reranker-v2-m3 locally and notes reranking "typically introduces a 1–2 second delay" [V].
   Cohere/Voyage rerankers are cloud services; they are excluded for vault data and unnecessary for
   harness-data.
7. **sqlite-vec brute force is slower than the earlier note assumed.** I measured k=20 KNN at **47 ms
   for 20k × 1024-d** and **244 ms for 100k × 1024-d** float vectors; **58 ms at 100k × 256-d**; and
   **19 ms for 100k binary-quantized 1024-d vectors** [measured, Linux VM]. The labeling note's
   "5–15 ms at 100K" [3p] is optimistic. Plan: float32 below ~30k vectors; above that, Matryoshka
   truncation (Qwen3/EmbeddingGemma support MRL; bge-m3 does not [M]) or binary candidates + float
   rescoring.
8. **Temporal and "how did my preference change" questions are SQL, not similarity.** The harness's
   append-only, newest-wins records are already a transaction-time log. Add an explicit **valid-time**
   (`valid_from`, `valid_to`) to derived facts, as Graphiti does (`valid_at`, `invalid_at`, `expired_at`
   on every edge [V, `graphiti_core/edges.py`]), and answer "as of June" with an as-of SQL view.
9. **Do not adopt a hosted memory product.** Mem0, Zep and the LongMemEval/LoCoMo leaderboard numbers
   are vendor-reported and disputed (§2.14). Borrow three ideas instead: fact extraction with
   supersession (Mem0), bitemporal edges (Graphiti), and time-aware query expansion (LongMemEval).
10. **Expose it as one CLI first (`scripts/recall.py`), then a thin MCP server over the same code.**
    `qmd` (BM25 + vector + reranker, local GGUF models, MCP server) is the closest off-the-shelf tool for
    the *knowledge wikis*, but its FTS uses `porter unicode61` by default, which breaks CJK (issue #617,
    closed in May 2026 with a JS-side CJK normalization) [V], so verify Korean before adopting it.

---

## 1. What is being searched (and what that implies)

| Corpus | Store (STORAGE.md) | Size/year [est] | Shape | Typical questions | Retrieval implication |
|---|---|---|---|---|---|
| Events + labels | `log/YYYY-MM.jsonl` (→ `log/YYYY-MM/<host>.jsonl`) | 50k–200k lines, 20–100 MB | short text + facets + ids + ts | "what was I doing when…", "corrections last week", "events like this" | facets/SQL first; hybrid on `content`+`intent`; embeddings of `intent` for similarity |
| Decisions | project `decisions.md` (`D-…`) + `decision` events | hundreds | claim + justification + proof | "what did I decide about X" | small: grep + LLM read; hybrid only across all projects |
| Patterns / encodings / meta | `patterns/*.jsonl` (newest per id wins) | hundreds | structured, evidence pointers, levels | "which patterns relate", "is there a pattern for…" | fold-latest view + edge graph + embeddings of descriptions |
| Preferences | `preferences.jsonl` | hundreds | assertion log | "how has my preference changed" | as-of/temporal SQL over the assertion log |
| Research ledger | `research/ledger.jsonl` | hundreds–thousands | claim + source + status | "did I already check X" | exact + hybrid; dedupe on URL |
| Knowledge wikis | project `knowledge/wiki/*.md` + `manifest.json` + `raw/` | 10s–1000s of pages, Korean PDFs | Markdown with `raw/...#p.N` anchors | "find the passage about …", "what does doc D say on page 3" | chunked hybrid + rerank; page anchors; optional ColPali for scans/tables |
| Message vault | `~/msg-vault/<source>/messages.jsonl` | 10k–100k msgs | third-party text, Korean+English | "everything with client Y", "when did they ask for…" | **separate local index inside the vault**; never leaves the Mac |
| Style pairs | `style/pairs.jsonl` | hundreds–thousands | (draft, my edit) pairs | "how do I usually phrase…" | embeddings for nearest examples (few-shot), plus filters by register/language |
| Clients/contacts/applications | `clients.jsonl`, `applications.jsonl`, … | small | entity records | "everything about client Y" | entity-id join across stores (graph layer) |

Three properties shape everything below:

- **Most of it is small.** Anthropic's contextual-retrieval post says that for knowledge bases under
  200,000 tokens (about 500 pages) you can skip RAG and include the whole thing in the prompt; with
  prompt caching that is "over 2x lower latency" and "up to 90% lower cost" [V]. A single project's
  `decisions.md`, `glossary.md` or pattern store usually fits that bound, so the right "retrieval" there is
  *read the file*. (It still costs context, so only load what the question needs.)
- **It is id-rich.** Events, patterns, decisions and documents all carry ids and pointers. Exact joins over
  those ids beat any learned retriever for "everything about Y".
- **It is bilingual and partly private.** Korean text needs morphological care (§2.4). Vault text and its
  embeddings must stay in the vault (embeddings partly leak text, `data_architecture.md` §2.4).

---

## 2. Evidence by technique

### 2.1 Agentic search (grep / ripgrep / Glob / Read)
- **What it is:** the model issues `rg`, Glob and Read calls iteratively, refining terms, instead of
  querying a pre-built index. Claude Code ships Grep (ripgrep), Glob and Read tools for this.
- **Why Claude Code dropped vector RAG:** quoted in §0.1 [V/S]. Reported secondhand from a Latent Space
  interview: agentic search "outperformed everything. By a lot." [S, not verified against the audio].
- **Independent evidence:** AWS researchers ("Keyword search is all you need", arXiv 2602.23368, Claude 3
  Sonnet + ReAct over keyword/regex tools) report "over 90% of the performance metrics compared to
  traditional RAG systems without using a standing vector database", and note it suits frequently
  updated knowledge bases [S; arXiv unreachable].
- **Where it fails:** (a) vocabulary mismatch ("tone too stiff" vs "딱딱하다"), (b) Korean inflection
  (a grep for 보험금을 misses 보험금은), (c) **token floods**: in my 200k-line synthetic log, `rg -c 보험금`
  matched 191,018 lines in 63 ms [measured]. Speed is never the problem; output volume is. Every grep
  must run with `-m`/`--max-count`, `-c` first, `--max-columns 200`, or through `recall` which caps it.
- **Cost on a Mac:** `rg` over 100 MB of JSONL is tens of milliseconds [measured on VM; Macs with NVMe are
  similar or faster, est]. The real cost is the LLM turns: each search round-trip is one model turn
  (a few hundred to a few thousand tokens).
- **Verdict:** default for exact strings, ids, filenames, code, and small stores. Wrap it so results are
  capped and Korean variants are expanded (§4.4).

### 2.2 Contextual retrieval (Anthropic, Sept 2024)
Numbers from the post [V, fetched]: top-20 retrieval failure rate (1 − recall@20), baseline 5.7%.
| Method | Failure rate | Reduction |
|---|---|---|
| Contextual embeddings | 3.7% | −35% |
| Contextual embeddings + contextual BM25 | 2.9% | −49% |
| + reranking (Cohere; top-150 → top-20) | 1.9% | −67% |
Context per chunk is 50–100 generated tokens; the cost was about **$1.02 per million document tokens**
one-time with prompt caching (2024 Claude 3 Haiku pricing; recompute for Haiku 5.5). Passing 20 chunks
beat 5 or 10. Gemini and Voyage embeddings did best in their tests.
- **Harness use:** for **wiki chunks from PDFs**, prepend a 1–2 sentence context ("This chunk is from
  <doc title>, section <h2>, page N, about …") before embedding *and* before FTS indexing. For events,
  the existing `intent` / `situation` labels already play this role: index `content` together with
  `intent`, `situation`, `scope` and `type`. That is contextual BM25 for free.

### 2.3 Long context instead of retrieval
- Below ~200k tokens, include the whole store (cached) [V, Anthropic]. But the user's premise holds:
  agents degrade with irrelevant context, and LongMemEval shows long-context chat assistants drop about
  30% versus oracle retrieval [S]. A secondary summary lists full-context GPT-4o-mini at 55.4% on
  LongMemEval_S (~115k tokens) versus Zep at 63.8% with ~1.6k tokens [S, unverified].
- **Rule:** load a whole file only when it is (a) under ~8k tokens and (b) the question is *about* that
  file. Otherwise retrieve.

### 2.4 BM25 / SQLite FTS5, and Korean tokenization
- **FTS5 tokenizers:** `unicode61` (word split on spaces/punctuation), `porter` (English stemming
  wrapper), `trigram` (substring matching, SQLite ≥ 3.34, query terms ≥ 3 characters) [V, sqlite.org
  via search; S for the 3-char rule]. BM25 ranking works with all of them via `bm25()`.
- **Measured (toy corpus of 7 Korean/English sentences, `retrtest/ko_fts.py`):**

  | Query | unicode61 | trigram | LIKE `%q%` | Kiwi-morpheme column |
  |---|---|---|---|---|
  | 납기 (2 syllables) | – | **– (silent miss)** | 2 hits | 2 hits |
  | 보험 | – | **–** | 2 hits (보험금, 금융보험) | 1 hit (보험금 is one morpheme) |
  | 보험금을 (with particle) | – | – | – | **1 hit** (query → 보험금) |
  | 말투 | – | **–** | 1 hit | 1 hit |
  | 변환했다 (inflected) | 1 hit | 1 hit | 1 hit | 1 hit (변환 하) |
  | 변환 | – | **–** | 1 hit | 1 hit |
  | 계약 (inside 계약서) | – | **–** | 1 hit | **– (miss)** |
  | deadline | 1 | 1 | 1 | 1 |

  Also measured on a 200k-line synthetic log (`fts_bench.py`): an FTS5 trigram index over `content` +
  `intent` took 13.8 s to build and was **264 MB for 109 MB of JSONL (2.4×)**; the query
  `"glossary" AND "말투"` returned **0 rows with no error**, because 말투 is 2 characters [measured].
  Kiwi tokenizes at about **0.8 ms per sentence** [measured].
- **Conclusions:**
  - `trigram` alone is unsafe for Korean: many key words are 2 syllables, and the miss is silent.
  - `unicode61` alone fails on particles (보험금을, 보험금은 are different tokens) [S, Korean Wikipedia test].
  - Kiwi (kiwipiepy, LGPL-3.0, pure local, has typo correction modes [V README]) gives morpheme
    tokens; mecab-ko is the older alternative [M]. Neither is an FTS5 tokenizer out of the box, so
    **pre-tokenize in Python and store the morphemes in a second column** (`content_ko`) indexed with
    `unicode61`. Query side: run the same Kiwi analysis on the query.
  - Union the two indexes (trigram for ≥3-char substrings and English; Kiwi column for words) and add a
    `LIKE` scan for <3-character terms (fine at ≤1M rows). Fuse with RRF.
  - I found **no rigorous Korean benchmark of Kiwi vs mecab-ko vs trigram under BM25** [S search came up
    empty]; the ranx-k README's ROUGE gain (0.234 → 0.421) is self-reported and not a retrieval metric
    [S]. The gold set (§6) will settle it for this corpus.
- **Learned sparse (newer alternative to BM25 for Korean):** KURE-Sparse-base (593M) scores 0.7984
  nDCG@10 on MTEB(kor) and KURE-Sparse-nano (149M) 0.7716, both above dense bge-m3 (0.7509) [V, KURE
  README]. It needs a model at index and query time, so treat it as a phase-3 option for the vault and
  wikis, not the logs.

### 2.5 Dense embeddings (multilingual, Korean)
**Korean (MTEB(kor, v2), 9 retrieval tasks incl. MIRACL-ko, AutoRAG parsed-PDF, LawIRKo; nDCG@10 /
Recall@10)** [V, `KURE/README.md`, dense rows taken from the official MTEB results repo]:

| Model | Type | Params | nDCG@10 | Recall@10 | MIRACL-ko nDCG@10 | AutoRAG (PDF) |
|---|---|---:|---:|---:|---:|---:|
| nlpai-lab/KURE-v2 | late-interaction | 154M | **0.8160** | 0.8921 | 0.7237 | **0.9718** |
| nvidia/Nemotron-3-Embed-8B | dense | 8.0B | 0.8127 | 0.8934 | 0.7363 | 0.9311 |
| lightonai/mLateOn | late-interaction | 307M | 0.7906 | 0.8740 | 0.7135 | 0.9392 |
| Qwen3-Embedding-8B | dense | 7.6B | 0.7826 | 0.8815 | 0.6783 | 0.8276 |
| Qwen3-Embedding-4B | dense | 4.0B | 0.7737 | 0.8753 | 0.6803 | 0.8431 |
| KURE-v1 (bge-m3 fine-tune) | dense | 568M | 0.7616 | 0.8629 | 0.6816 | 0.8708 |
| BAAI/bge-m3 | dense | 568M | 0.7509 | 0.8588 | 0.7015 | 0.8301 |
| KoE5 (mE5-large fine-tune) | dense | 560M | 0.7337 | 0.8300 | 0.6235 | 0.8434 |
| Qwen3-Embedding-0.6B | dense | 596M | 0.7140 | 0.8222 | – | – |

(EmbeddingGemma-300m is not on this board; a single community Belebele-ko test put it at ~0.72 vs
bge-m3 0.926 [3p, from the labeling note].)

**Multilingual (MMTEB, mid-2025 snapshot from the Qwen3-Embedding README)** [S/V]: Qwen3-Embedding-8B
70.58, 4B 69.45, 0.6B 64.33, multilingual-e5-large-instruct 63.22, EmbeddingGemma-300m 61.15 [S],
bge-m3 59.56. Note the Korean ranking differs: the 0.6B Qwen model is *below* bge-m3 on Korean retrieval.

**Other properties**
- **Instructions:** Qwen3-Embedding queries take a one-sentence task instruction; "using instructions
  typically yields an improvement of 1% to 5%", and instructions should be in English even for
  multilingual use [V, Qwen3-Embedding README]. bge-m3 needs no instruction; multilingual-e5/KoE5 need
  `query:` / `passage:` prefixes [V, KURE README].
- **Matryoshka (MRL):** Qwen3-Embedding supports custom output dimensions (MRL) [V README];
  EmbeddingGemma supports 768 → 128 [3p, labeling note]. Retention numbers like "95–97% nDCG at 256-d"
  are unsourced vendor-guide figures [S]; measure on the gold set. bge-m3 is not MRL-trained [M], so do
  not truncate it; use binary quantization + rescoring instead.
- **bge-m3 hybrid outputs:** bge-m3 can emit dense, sparse and multi-vector representations at once;
  on MIRACL (18 languages) dense 67.8 and "all" 70.0 nDCG@10 [S, M3 paper table via search].
- **Latency/storage on the Mac [est]:** a 568M encoder on Apple-silicon GPU (MPS/MLX/Ollama) embeds
  roughly 50–300 short passages per second and one query in 20–60 ms. I found no measured bge-m3
  throughput for M3/M4 [S, search empty]; run the §8 bench. Storage: 1024-d float32 = 4 KB per vector,
  so 100k events = 400 MB; binary = 128 B (12.8 MB).
- **sqlite-vec KNN (brute force) [measured, 4-core Linux VM, k=20]:** 20k×1024 float 47 ms; 100k×1024
  float 244 ms; 100k×256 float 58 ms; 100k×1024 **bit** 19 ms (k=100). A personal log of 50k–200k events
  a year therefore needs either a time/scope pre-filter (sqlite-vec supports partition and metadata
  columns [V, labeling note]), MRL truncation, or binary candidates + float rescoring once it passes
  ~30k vectors.

### 2.6 Hybrid search and reciprocal rank fusion
- **RRF:** `score(d) = Σ_lists 1 / (k + rank_d)`. The classic constant is k = 60 (Cormack et al. 2009 [M]);
  `qmd` uses `1/(k+rank+1)` with k = 60 [V, qmd README], while **Graphiti's `rrf()` uses
  `rank_const=1`** [V, `graphiti_core/search/search_utils.py`], which weights the top ranks much more.
  The choice matters little with two lists of 20–50; tune it on the gold set.
- **qmd's refinements worth copying** [V]: a top-rank bonus so a document that is #1 for the original
  query is not diluted by expanded queries; and *position-aware blending* of retrieval and reranker
  scores (ranks 1–3: 75% retrieval / 25% reranker; ranks 4–10: 60/40; 11+: 40/60) so the reranker
  cannot destroy high-confidence exact matches. qmd reranks the top 30 candidates by default (MCP
  `candidateLimit` default 40).
- **Filters first.** Apply `scope`, `type`, `client`, date range and privacy tier as SQL `WHERE` clauses
  before KNN/BM25 (sqlite-vec metadata/partition columns; FTS5 joined to the facet table). This is the
  single biggest precision gain for logs [M].
- **Evidence that hybrid helps:** Anthropic's −49% failure (embeddings + BM25 vs embeddings alone, §2.2)
  [V]; LightRAG made `mix` (graph + vector) with reranking its default mode [V].

### 2.7 Rerankers (cross-encoders)
**Korean (same 9 tasks; candidates = gold + BM25 top-50; nDCG@10; throughput on one RTX A6000)**
[V, KURE README]:

| Reranker | Params | nDCG@10 | Pairs/s (A6000) |
|---|---:|---:|---:|
| Qwen3-Reranker-8B | 8.2B | 0.8990 | 15 |
| Qwen3-Reranker-4B | 4.0B | 0.8916 | 24 |
| KURE-Reranker-base (Qwen3-1.7B) | 1.7B | 0.8800 | 55 |
| **KURE-Reranker-nano** | 149M | **0.8757** | **482** |
| mxbai-rerank-large-v2 | 1.5B | 0.8607 | 65 |
| Qwen3-Reranker-0.6B | 596M | 0.8528 | 101 |
| **BAAI/bge-reranker-v2-m3** | 568M | 0.8518 | 413 |

**English (independent BEIR-style, BM25 top-30)** [S, hevmind.com, Sept 2026]: Voyage rerank-3 0.504,
Cohere rerank-v3.5 0.486, Qwen3-Reranker-0.6B 0.478, bge-reranker-v2-m3 0.471. Voyage reports
rerank-2.5 beating Cohere v3.5 by 12.7% on its MAIR evaluation [S, vendor]. Cohere has a Rerank 4 [S].

- **Mac cost [est]:** Apple-silicon throughput for a 149M–568M cross-encoder is plausibly 5–10× below
  an A6000, so 40 pairs ≈ 0.3–1 s. That fits an interactive budget only when L2 is ambiguous.
- **Verdict:** use a reranker for wiki passages and vault messages (long, fuzzy) and for "similar past
  situations"; skip it for id/facet/temporal queries. Pick KURE-Reranker-nano if its license permits
  (check the model card; HF unreachable today), else bge-reranker-v2-m3. An LLM reranker (Haiku, a
  0–10 relevance score as in qmd) is a fallback for harness-data only, never for vault content (§7 of
  the labeling note: no vault data to third parties).

### 2.8 Late interaction (ColBERT, ColPali)
- **Text:** KURE-v2 (154M, ColBERT-style via PyLate) is the best Korean retriever on the board above,
  beating 4–8B dense models [V]. Its deploy benchmark: hierarchical token pooling ×2 halves the index
  "with no measurable nDCG loss"; pooling ×3 + 1-bit document tokens fits all nine corpora in 1.7 GB,
  smaller than any single-vector HNSW index; query encoding 13.8 ms vs 38–40 ms for 4–8B dense models
  (A100) [V, `KURE/deploy/late-interaction/README.md`]. At the harness's scale (≤100k chunks) an
  exhaustive MaxSim scan is fine; PLAID only pays off on large corpora (their 720-doc demo was slower
  with PLAID) [V].
- **PDF pages as images:** ColPali scores 81.3 nDCG@5 on ViDoRe v1 and current leaders exceed 90, which
  is why ViDoRe v2 was made [S]. A single-vector BiPali is 27.1 nDCG@5 points worse than late-interaction
  ColPali [S, reproducibility study]. The ColPali OCR baseline was Tesseract, which is weak; a strong
  converter narrows the gap [S].
- **Verdict:** the harness already converts PDFs to Markdown with page anchors (`kb.py convert`, kordoc
  for Korean/HWP, Docling/Marker/markitdown). Text retrieval over good Markdown + page anchors covers
  most passage lookups. Add ColPali/ColQwen (or Qwen3-VL-Embedding [S]) only for scanned, table- or
  figure-heavy PDFs where `confidence: low` was recorded at intake. BLUEPRINT already says "cleaning
  the Markdown matters more than which retriever is used".

### 2.9 Knowledge-graph retrieval (GraphRAG, LightRAG, HippoRAG 2, entity linking)
- **GraphRAG (Microsoft):** LLM entity/relation extraction → hierarchical Leiden communities → bottom-up
  community summaries. *Local search* (entity neighborhood + linked text), *global search* (map-reduce
  over community summaries), *DRIFT* (start global, drill local) [M + `ai_abstraction.md` §1.13].
  Indexing is expensive. **LazyGraphRAG** defers summarization to query time: indexing costs "identical
  to vector RAG and 0.1% of the costs of full GraphRAG", and comparable global-query quality at ">700
  times lower query cost" [S, Microsoft Research blog].
- **LightRAG** (HKUDS): flat entity/relation graph with dual-level keys; query modes `local` (entities and
  their attributes), `global` (relationship chains, cross-document themes), `hybrid`, `naive` (plain
  vector chunks) and `mix` (all of them, default), with optional reranking [V, README]. Extraction runs an
  LLM over **every chunk**; the README recommends a non-thinking model (Claude Haiku or local
  Qwen3-30B-A3B as minimum) [V]. Third-party re-runs put LightRAG below naive RAG on MuSiQue in some setups
  [S, arXiv 2609.19622], so claimed wins are setup-dependent.
- **HippoRAG 2** ("From RAG to Memory", ICML 2025): OpenIE triples + passage nodes + Personalized
  PageRank seeded by query-matched facts; Llama-3.3-70B extraction + NV-Embed-v2 retrieval. It beats
  NV-Embed-v2 by about 9.5 F1 on 2Wiki, with the largest gains on associative multi-hop (MuSiQue);
  NV-Embed-v2 alone gets passage recall@5 of 69.7 (MuSiQue) and 76.5 (2Wiki) [S, paper via search;
  README confirms the setup, V]. GraphRAG/LightRAG produce no passage rankings, so the paper gives no
  recall numbers for them [S].
- **Entity linking:** the hard part of any KG. For the harness, most entities already have ids
  (`client-`, `org-`, `ct-`, `pat_`, `D-`, `A-`, `INV-`, document sha8) or controlled vocabularies
  (scopes, areas, glossary terms). Linking free text to those ids needs only alias tables (glossary,
  `clients.jsonl` names in Korean and English) + exact/trigram matching, with an LLM only for leftovers.
- **Verdict:** for logs, patterns, decisions and clients, build a **deterministic edge table**
  (`silver/edges.parquet`, already proposed in `data_architecture.md` §3.1) from existing ids, then do
  HippoRAG-style **Personalized PageRank** (or 2-hop BFS) seeded by the L1/L2 hits. It costs no LLM
  calls, is rebuildable, and is auditable. Consider LightRAG (with Haiku extraction, kept local-only for
  client docs) only if a single project's wiki grows past ~1,000 pages and gold queries show multi-hop
  failures.

### 2.10 Hierarchical summaries (RAPTOR) and global questions
- RAPTOR: embed → UMAP → GMM (BIC-selected k, soft assignment) → summarize clusters recursively;
  retrieve over the *collapsed tree* (all levels together); +20% absolute on QuALITY with GPT-4 [R, see
  `ai_abstraction.md` §1.12].
- The harness already plans a reflection tree with evidence pointers (`ai_abstraction.md` §4.5) and
  weekly/monthly reports (`weekly_report.py`, `review-week`). Those *are* the summary layer. Index every
  summary node in the same FTS+vector tables with `level` = 1..3, and let L2 return nodes from any
  level (collapsed-tree retrieval). A global question ("what keeps going wrong in translation jobs")
  hits L2/L3 summaries first, then drills down through their evidence pointers.
- Rule from `ai_abstraction.md`: summaries are views over raw episodes, never replacements; every
  answer drawn from a summary should cite at least one leaf id.

### 2.11 Structured queries (SQL / DuckDB over facets; "text-to-SQL for logs")
- Counting, grouping, filtering and time windows ("how many corrections in translation/acme since
  August", "cost by model last month") are exact SQL questions. Embeddings cannot count.
- **Text-to-SQL accuracy is good on small schemas and bad on large ones:** o1-preview 91.2% on Spider 1.0
  and 73.0% on BIRD but 17–21% on enterprise Spider 2.0 [S]; schema linking is the main failure.
  Benchmarks are noisy: annotation error rates of 52.8% (BIRD Mini-Dev) and 62.8% (Spider 2.0-Snow) were
  reported, and fixing 100 BIRD examples moved agent scores −7% to +31% relative [S, UIUC/CIDR 2026].
- **Harness design:** keep the schema tiny and documented (5–10 views: `events`, `labels_latest`,
  `patterns_latest`, `preferences_asof`, `decisions`, `edges`, `docs`, `chunks`) with a 300–500 token
  schema card in L0. Provide **named, parameterized query templates** for the common questions
  (`recall sql corrections --scope X --since Y`) and allow free SQL only read-only (`mode=ro`,
  `duckdb -readonly`) with a row limit. DuckDB scanned my 109 MB synthetic JSONL with a filter + group-by
  in about **300 ms** [measured], so querying bronze directly is acceptable before the silver build exists.

### 2.12 Temporal retrieval (recency, as-of, bitemporal)
- **Two times:** *transaction time* (when the harness recorded it: the `ts` of the line) and *valid
  time* (when the fact was true in the world). The append-only logs give transaction time for free;
  "newest wins" folds (patterns, preferences, applications) are an *as-of-now* view of them.
- **Graphiti** stores `valid_at` ("when the fact became true"), `invalid_at` ("when the fact stopped
  being true"), `expired_at` (when the record was invalidated) and `reference_time` on each edge, and its
  search config offers RRF, MMR, cross-encoder, node-distance and episode-mention rerankers combined with
  BM25 + embeddings + graph traversal [V, source]. Contradicting new facts invalidate old edges rather
  than deleting them.
- **LongMemEval** includes temporal reasoning and knowledge-update question types plus abstention
  (500 questions; `_s` ≈ 115k tokens / ~40 sessions; `_m` ≈ 500 sessions) and ships a **time-aware query
  expansion**: extract timestamped events, infer the time range from the query, and prune the search
  space with it; plus index-key expansion with session summaries, keyphrases or user facts [V, README].
  "Multi-session" is the lowest-scoring category for almost every vendor [S].
- **Harness design:**
  1. Parse time expressions in the query ("as of June", "지난주", "since the Acme job") with a small rule
     table + Haiku fallback into `[t0, t1]` and a mode (`asof`, `during`, `changed`).
  2. `asof T`: for newest-wins stores, `arg_max(value, ts) WHERE ts <= T` per id (SQL view
     `preferences_asof(T)`); for derived facts with valid time, `valid_from <= T AND (valid_to IS NULL OR
     valid_to > T)`.
  3. `changed`: return the *sequence* of assertions for a key ordered by `ts`, with the supersession chain
     (`supersedes`, `corrects`), not the top-k similar ones.
  4. Recency as a *ranking feature* only for "recent situation" questions:
     `score = rrf + w·exp(−Δdays/τ)` with τ ≈ 30 days [M; Generative Agents used recency × relevance ×
     importance, see `ai_abstraction.md`]. Never apply recency decay to "what did I decide" (old
     decisions remain binding until superseded).

### 2.13 Memory systems (Mem0, Zep/Graphiti, Letta)
- **Mem0:** extracts facts from conversations and ADD/UPDATE/DELETE/NOOPs them against existing
  memories. README (Oct 2026) claims LoCoMo 92.5 (was 71.4), LongMemEval 94.4 (was 67.8) with about 7k
  tokens and ~1 s p50 per query, and 64.1 on BEAM-1M [V, README, vendor-reported]. The 2025 paper's
  table (as reproduced by a third party): full context 72.9% J vs Mem0 66.9% with 1.8k tokens and 1.44 s
  p95, Zep 66.0% [S]. An independent reproduction of the hosted product on LongMemEval got 57.5% [S].
- **Zep/Graphiti:** temporal KG (above). Reported LongMemEval 71.2% (GPT-4o judge) and LoCoMo figures
  from 75% to 94.7% depending on who ran it [S]. Graph construction needs several async LLM calls per
  episode [S, Mem0 paper's critique].
- **Letta:** core / recall / archival memory paged by the agent, plus sleep-time consolidation
  [`ai_abstraction.md` §1.14].
- **Verdict:** the numbers are not comparable across vendors (different readers, judges and
  configurations), and all of these products want to own the store. The harness's bronze-log +
  projections design already gives what they give, with better provenance. Borrow: fact supersession
  (Mem0's UPDATE → a new assertion with `supersedes`), bitemporal fields (Graphiti), time-aware query
  expansion (LongMemEval), and Letta's "core block always in context" = the L0 catalog + CLAUDE.md.

### 2.14 MCP retrieval servers
- **qmd** (tobi): local markdown search; BM25 (FTS5) + vector + LLM reranker + fine-tuned 1.7B query
  expander, all GGUF via node-llama-cpp (`embeddinggemma-300M` default embedding, `qwen3-reranker-0.6b`
  reranker; README suggests Qwen3-Embedding for CJK); collections + hierarchical "context" strings; MCP
  over stdio or HTTP daemon (`qmd mcp --http`) that keeps models loaded [V]. Korean caveat: FTS was
  `porter unicode61`, which returns zero hits for CJK; fixed in May 2026 with a JS-side CJK normalization,
  but a rename path was still reported broken afterwards [V, issue #617].
- **Others** [S]: `basic-memory` (Markdown KB + semantic search + graph context, `uvx basic-memory mcp`),
  `claude-mem` (session hooks → compressed observations, SQLite + Chroma), `claude-mem-lite` (FTS5 +
  TF-IDF, single SQLite), `mcp-memory-service` (sqlite-vec backend), and the reference Memory server
  (entity/relation/observation JSON graph).
- **Verdict:** none of them knows the harness ontology (ids, scopes, newest-wins folds, privacy tiers,
  vault separation). Write `scripts/recall.py` over `index.sqlite` + DuckDB and wrap it in a ~100-line
  MCP server later. Trial qmd for the `knowledge/wiki/` folders of one project as a quick win (after a
  Korean check against §6 gold queries).

### 2.15 Context compression
- **LLMLingua** family: up to 20× prompt compression with a small LM; LongLLMLingua improves RAG "by up
  to 21.4% using only 1/4 of the tokens"; LLMLingua-2 (BERT-size token classifier) is 3–6× faster [V,
  README]. Training data was mostly English (MeetingBank) [M], so Korean behavior is unverified.
- **For an agent harness, structural compression beats token deletion:** return snippets and ids
  (progressive disclosure), use `intent`/`situation` labels as one-line summaries of events, and have a
  Haiku subagent summarize large result sets to 1–2k tokens with cited ids. Token-level compression
  produces text that is hard to cite and audit. Keep LLMLingua as an optional final pass for very long
  passages (wiki sections > 2k tokens), and only after a gold-set check.

### 2.16 Progressive disclosure (index → summary → full record)
- Anthropic's context-engineering guidance: agents "maintain lightweight identifiers (file paths, stored
  queries, web links, etc.)", load data just in time, "incrementally discover relevant context through
  exploration", optionally retrieve "some data up front for speed", write notes outside the window, and
  have sub-agents return "a condensed, distilled summary of its work (often 1,000-2,000 tokens)" [V].
  Agent Skills load the same way: name/description, then SKILL.md, then referenced files [S].
- **Harness mapping:** the L0 catalog (always) → hit lists with snippets (≤1.5k tokens) → `recall get`
  of individual records (≤2k tokens each) → the raw file or vault payload only on explicit need.
  `knowledge/index.md` is already the wiki's L0.

---

## 3. Decision matrix: query type → method

Legend: ● primary, ○ secondary/fallback, – not useful. "Budget" is the maximum returned to the main agent
for that step.

| # | Query type (example) | grep/Glob | SQL facets | FTS5 (trigram + Kiwi) | Dense vec | Rerank | Graph (edges/PPR) | Summaries | Temporal as-of | Recommended recipe | Budget |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | **Exact id / string** ("evt_20261014_…", "D-20261002-1", "INV-0042", a filename, an error message) | ● | ● | ○ | – | – | – | – | – | Regex-detect id prefixes → `recall get <id>` (SQL by id, or `rg -m5` on bronze). Strings: `rg -F -m20 --max-columns 200`. | 1 record ≤2k; ≤20 lines |
| 2 | **"What did I decide about X"** | ○ | ● `type=decision`, scope | ● | ○ | ○ | ○ follow `supersedes`/`corrects` | – | ● newest valid | Filter decisions (events + project `decisions.md`) → FTS on claim/justification (+vec if FTS < 3 hits) → follow supersession chain → return latest + its predecessors. If one project's `decisions.md` < 8k tokens, just read it. | ≤10 hits, ≤1.5k |
| 3 | **"Similar past situations"** ("have I been stuck like this before?") | – | ○ scope/type pre-filter | ○ | ● on `intent`+`situation` | ● | ○ expand to outcomes | ○ L1 pattern nodes | ○ recency feature | Step-back query (principle-level intent) → vec KNN over intent/situation embeddings + FTS, RRF → rerank top 40 → attach `outcome`, linked corrections, matching pattern. | top 5–8, ≤1.5k |
| 4 | **"Everything about client Y across fields"** | ○ | ● entity id joins | ● aliases (KO/EN names) | ○ | ○ | ● 1–2 hops | ○ client summary | ○ | Resolve Y → `client-…` via alias table → SQL join over events/projects/applications/invoices/ledger/messages-metadata → graph 2-hop for decisions, mishaps, patterns → group by store, counts first. Vault text only via the vault index, local. | counts + top 3 per store, ≤2.5k |
| 5 | **"How has my preference changed"** (on tone, on file layout) | – | ● | ○ find the key | ○ find the key | – | ○ | – | ● sequence | Find the preference key(s) (FTS/vec over `preferences.jsonl`, style guide, corrections) → return the ordered assertion history with ts, `supersedes`, and the evidence events; summarize the trend in 3 lines. | ≤12 rows, ≤1.5k |
| 6 | **"Which patterns relate"** (to pat_x, or to this failure) | – | ● fold-latest patterns | ○ | ● pattern description embeddings | ○ | ● shared evidence, parent/child, meta-patterns (PPR) | ● L2/L3 nodes | – | Seed = pat_x or vec hits → PPR over edges (shared evidence events, `mp_` membership, encodings) → union with vec neighbors → rank. | ≤10 patterns, ≤1.5k |
| 7 | **Korean phrase search** ("말투가 딱딱", "보험금") | ○ `rg` for exact | ○ | ● trigram ∪ Kiwi column ∪ LIKE(<3 chars) | ● bge-m3/KURE | ○ (Korean reranker) | – | – | – | Kiwi-analyze query → FTS on both columns + LIKE for short terms → vec KNN → RRF → rerank if > budget. Report which index matched (helps debugging silent misses). | ≤10 hits, ≤1.5k |
| 8 | **PDF passage lookup** ("where does the contract say the payment terms", "doc 3fa2c1d0 p.12") | ○ Glob wiki, `rg` anchors | ● `manifest.json` (doc id, title, pages) | ● contextualized chunks | ● contextual embeddings | ● | – | ○ doc summary | – | Doc-level filter (manifest / wiki frontmatter) → hybrid over contextualized chunks (title+section+page prefix) → rerank top 40 → return passage + `raw/<file>#p.N` anchor. Scans/tables with low intake confidence: ColPali/ColQwen page retrieval (phase 3). | ≤5 passages, ≤2.5k |
| 9 | **Temporal "as of June"** ("what was my rate as of June", "open applications on 2026-06-30") | – | ● | – | – | – | ○ | ○ monthly rollup | ● | Parse time → `asof` view (`arg_max(...) WHERE ts <= T`, or valid-time interval) → return the state + the record that set it. | ≤20 rows, ≤1.5k |
| 10 | **Counts / trends** ("how many corrections per week in translation") | – | ● | – | – | – | – | ○ weekly report | ○ | Parameterized SQL template or read-only free SQL with LIMIT; return a table, not records. | ≤40 rows |
| 11 | **Global / thematic** ("what are my recurring problems this quarter") | – | ○ | ○ | ○ | – | ○ communities | ● L2/L3 nodes, weekly reports | ○ window | Collapsed-tree search over summary nodes in the window → drill into ≤3 nodes' evidence. | ≤3k |
| 12 | **"Did I already research X"** | ○ | ● ledger by URL/claim | ● | ○ | – | – | – | ○ status as of now | Ledger FTS + URL exact match → latest status row per note. | ≤8 hits |
| 13 | **Style exemplars** ("how do I usually phrase a polite refusal in Korean") | – | ● language/register filter | ○ | ● on draft side | ○ | – | ○ style guide | – | Filter pairs → vec KNN on the draft text → return 3 (draft → my edit) pairs as few-shot. | 3 pairs, ≤1k |

**Routing rules (cheap, before any model call)**
- Contains an id pattern (`evt_`, `D-`, `pat_`, `enc_`, `mp_`, `rn_`, `pref_`, `sp_`, `app-`, `client-`,
  `INV-`, 8-hex doc id, `msg_`, `thr_`) → type 1.
- Contains a time expression (`as of`, `in June`, `지난달`, a date) → add the temporal filter; `as of` /
  `at the time` → type 9.
- "changed", "evolved", "used to", "바뀌" → type 5. "decide", "decision", "결정" → type 2.
- "similar", "like this", "before", "비슷한" → type 3. "everything", "all about", a known client alias → type 4.
- "how many", "count", "per week", "trend" → type 10. "pattern" + "relate/connected" → type 6.
- Hangul in the query → enable the Kiwi column and Korean reranker.
- Otherwise: L1 (rg/FTS) first, escalate to L2 hybrid on fewer than 3 hits, then L3 rerank if more than
  the budget, then graph/summaries if the question is multi-hop or global. A Haiku classifier is only a
  fallback for queries no rule matches.

---

## 4. Recommended layered retrieval stack

### 4.1 Layers and escalation
```
query ─▶ router (regex rules; Haiku fallback) ─▶ filters {scope, type, client, time, tier}
   L0  catalog card (always in context, ≤600 tok): stores, counts, date ranges, facet vocab, commands
   L1  exact: id lookup │ rg -F/-e (capped) │ parameterized SQL │ as-of views          ~10–300 ms
   L2  hybrid: FTS5 trigram ∪ FTS5 Kiwi ∪ LIKE(<3ch) ∪ vec KNN (filtered) → RRF       ~50–400 ms
   L3  rerank top 30–50 (KURE-Reranker-nano / bge-reranker-v2-m3), position-aware blend ~0.3–1 s [est]
   G   graph expansion: edges from ids, 2-hop / PPR seeded by L1–L3 hits             ~10–100 ms
   S   summaries: reflection-tree nodes + weekly/monthly rollups, collapsed-tree search  same as L2
   ─▶ hit list (id, ts, type, scope, score, why-matched, ≤200-char snippet, pointer)
   ─▶ agent expands chosen ids: recall get <id> (≤2k tok) ─▶ raw file / vault payload only if needed
```
Escalate only on these signals: L1 returned 0 hits, or > budget unranked hits; L2 top-1 and top-5
scores are close (ambiguous); the question is multi-hop (needs a second entity) or global.

### 4.2 Token budgets
| Step | Max returned | Notes |
|---|---|---|
| L0 catalog card | 600 tokens | Generated by `recall catalog`; loaded by SessionStart hook or CLAUDE.md pointer |
| One `recall search` call | 20 hits / 1,500 tokens | ≤200 chars of snippet per hit; truncation is explicit ("+137 more, refine with --scope") |
| One `rg` call via `recall grep` | 30 lines × 200 chars | `-c` count first when the term is common |
| One `recall get <id>` | 2,000 tokens | Long `content` → head + tail + `content_ref` pointer |
| SQL result | 40 rows / 1,500 tokens | Aggregates preferred over raw rows |
| Graph expansion | 15 nodes / 1,500 tokens | Node = id + label + edge type |
| Summary nodes | 3 nodes / 3,000 tokens | Each node cites ≥1 leaf id |
| **Per question, main agent** | **8,000 soft / 15,000 hard** | Over soft → delegate to a Haiku subagent that returns ≤2,000 tokens with ids |
| Subagent return | 1,000–2,000 tokens | Anthropic's sub-agent guidance [V] |

### 4.3 Index schema (extends `data_architecture.md` §4 `index.sqlite`)
```sql
-- facets and lookup (one row per searchable unit: event, decision, pattern, pref, ledger row, chunk, summary node)
CREATE TABLE units(
  uid TEXT PRIMARY KEY,          -- evt_..., D-..., pat_..., chunk:<sha8>:<n>, node:<id>
  kind TEXT, store TEXT, scope TEXT, client TEXT, type TEXT, lang TEXT,   -- lang: ko|en|mixed
  ts TEXT, valid_from TEXT, valid_to TEXT, level INTEGER DEFAULT 0,      -- level>0 = summary node
  supersedes TEXT, tier TEXT,    -- tier: harness-data | repo  (vault units live in the vault's own index)
  title TEXT, snippet TEXT, pointer TEXT);
CREATE INDEX units_f ON units(store, scope, type, ts);
-- lexical: trigram over raw text, unicode61 over Kiwi morphemes (pre-tokenized in Python)
CREATE VIRTUAL TABLE fts_tri USING fts5(uid UNINDEXED, ctx, body, tokenize='trigram');
CREATE VIRTUAL TABLE fts_ko  USING fts5(uid UNINDEXED, body_morph, tokenize='unicode61');
-- dense: filtered KNN; scope/store as partition/metadata columns
CREATE VIRTUAL TABLE vec_units USING vec0(uid TEXT PRIMARY KEY, store TEXT partition key,
  scope TEXT, embedding float[1024] distance_metric=cosine);
-- optional coarse pass once > ~30k vectors
CREATE VIRTUAL TABLE vec_bits USING vec0(uid TEXT PRIMARY KEY, embedding bit[1024]);
-- graph: deterministic edges from ids already in the records
CREATE TABLE edges(src TEXT, rel TEXT, dst TEXT, ts TEXT, evidence TEXT);  -- rel: points_to|corrects|labels|supersedes|evidence_of|member_of|about_client|in_doc|cites
CREATE INDEX edges_s ON edges(src); CREATE INDEX edges_d ON edges(dst);
-- alias table for entity linking (Korean + English names, glossary terms)
CREATE TABLE aliases(alias TEXT, norm TEXT, entity TEXT, PRIMARY KEY(alias, entity));
```
`ctx` holds the contextual prefix (for events: `type | scope | intent | situation`; for chunks: doc
title, section, page). Build is part of `lake.py index`; deterministic, rebuildable, never synced.
The vault gets a twin `index/vault.sqlite` with the same schema, built and queried only on the Mac.

### 4.4 The `recall` CLI (proposal; does not exist yet)
| Command | Layer | Does |
|---|---|---|
| `recall catalog` | L0 | prints the ≤600-token card |
| `recall get <id> [--full]` | L1 | one record by id from silver (bronze fallback), truncated to 2k tokens |
| `recall grep <pattern> [--store S] [--since D]` | L1 | `rg` with caps; Hangul input → also greps common particle variants [M: build from Kiwi analysis] |
| `recall sql <template> [args]` / `recall sql --raw "<SELECT…>"` | L1 | named templates (corrections, decisions, asof, costs, applications_open) or read-only raw SQL with LIMIT |
| `recall asof <store> <key> <T>` / `recall history <store> <key>` | L1 temporal | as-of state / ordered assertion history with supersession |
| `recall search "<q>" [--store --scope --since --until --k 20 --rerank auto]` | L2/L3 | hybrid with filters, RRF, optional rerank; prints `why` (which index matched) |
| `recall related <id> [--hops 2]` | G | edges + PPR from a seed |
| `recall summary "<q>" [--window]` | S | collapsed-tree search over summary nodes |
| `recall eval [--set evals/retrieval]` | eval | runs the gold set, writes `evals/results/retrieval/*.json` |

Output: one compact line per hit, e.g.
`evt_20261003_101500_ab12cd34 | 2026-10-03 | correction | translation/acme | 0.83 | fts_ko+vec | "용어집 '보험금' 통일…" | log/2026-10/mbp.jsonl:1832`.
Wrap the same functions in an MCP server (`recall-mcp`, stdio) once the CLI is stable; the CLI alone
already works from Claude Code through Bash and is easier to test.

### 4.5 Models and settings (initial)
| Role | Default | Alternative to A/B | Why |
|---|---|---|---|
| Embedding (harness-data, mixed KO/EN) | bge-m3 (Ollama or sentence-transformers, 1024-d) | KURE-v1 (drop-in), Qwen3-Embedding-4B with MRL 512–1024 + English instruction | strong in both languages, already in the labeling plan |
| Embedding (Korean-heavy wikis, vault) | KURE-v1 | KURE-v2 multi-vector (PyLate), KURE-Sparse-nano | best Korean scores per parameter [V] |
| Reranker | KURE-Reranker-nano (license check) | bge-reranker-v2-m3 | Korean nDCG 0.876 at 149M [V] |
| Korean analyzer | kiwipiepy 0.24 | mecab-ko | local, LGPL, typo modes [V] |
| RRF | k = 60, top-rank bonus, position-aware blend | k = 1 (Graphiti) | tune on gold set |
| Vector precision | float32 ≤30k units; else bit candidates (k=100) → float rescore | MRL 256–512 (Qwen3) | §2.5 measurements |
| Chunking (wiki) | 300–500 tokens on Markdown headings, page anchor kept, contextual prefix | — | Anthropic used chunks of a few hundred tokens [V] |

---

## 5. Cost and latency on the Mac

| Operation | Expected on Apple silicon | Basis |
|---|---|---|
| `rg` over one year of bronze (≤100 MB) | 10–70 ms | [measured VM: 35–63 ms over 109 MB] |
| DuckDB filter + group-by over bronze JSONL (109 MB) | 0.2–0.4 s; over silver Parquet ≪100 ms | [measured VM 301 ms]; Parquet [M] |
| FTS5 trigram query (selective term) | 1–50 ms; very common terms up to ~0.4 s | [measured VM, worst case on a synthetic corpus where every row matches] |
| FTS5 trigram index size | ~2–3× text | [measured 2.4×; qmd issue estimate 2–3×] |
| Kiwi tokenization | ~1 ms per sentence; 100k events ≈ 1–2 min one-time | [measured VM 0.77 ms] |
| Query embedding (568M) | 20–60 ms | [est] |
| Bulk embedding, 100k short units (568M) | 10–30 min one-time, then incremental | [est]; run §8 bench |
| sqlite-vec KNN, 20k × 1024 float | ~50 ms | [measured VM 47 ms] |
| sqlite-vec KNN, 100k × 1024 float / bit | ~250 ms / ~20 ms | [measured VM 244 / 19 ms] |
| Rerank 40 pairs (149M–568M) | 0.3–1 s | [est from A6000 PPS ÷ 5–10] |
| Contextual chunk prefixes (Haiku) | ~$1 per million doc tokens (2024 price; recompute) | [V, Anthropic] |
| Graph PPR over ≤200k edges | 10–100 ms in Python/NumPy | [M] |
| Memory: models resident | bge-m3 ~1.1 GB fp16; reranker 0.3–1.1 GB | [M] |

Typical interactive question: L1 (≤100 ms) answers most; L2 + rerank ≈ 0.5–1.5 s; the LLM turns dominate
both latency and cost. Run embedding/reranker models in one long-lived local daemon (Ollama, or an
HTTP server like `qmd mcp --http`) so they are not reloaded per call (qmd reports ~1 s to recreate an idle
context) [V].

---

## 6. Evaluation plan

### 6.1 Metrics
- **Retrieval (per query, against gold ids):** Recall@k (k = 5, 10, 20), nDCG@10, MRR, and **"silent
  miss" rate** (gold exists, method returned 0 hits). For list answers (type 4) use set recall/precision.
  For temporal queries (type 9), exact-match of the returned state.
- **Context cost:** tokens returned to the main agent per query, number of tool calls / turns, and
  wall-clock latency (p50/p95).
- **End-to-end:** answer correctness judged against a short gold answer (the harness's rubric-judge
  pattern; Haiku or Sonnet judge, human spot checks), plus citation validity (every claimed id exists and
  supports the claim) and abstention correctness for questions with no answer (LongMemEval style).
- **Ablations to run:** (a) rg-only agentic, (b) FTS trigram only, (c) trigram + Kiwi + LIKE,
  (d) vec only (bge-m3 / KURE-v1 / Qwen3-4B), (e) hybrid RRF, (f) hybrid + rerank, (g) + graph,
  (h) + summaries. Report each metric per query type; the decision matrix should be revised from these.

### 6.2 External sanity benchmarks (run once, small subsets)
- **Korean:** MTEB(kor, v2) retrieval tasks via the `mteb` package (includes MIRACL-ko, AutoRAG parsed-PDF
  retrieval, Ko-StrategyQA, LawIRKo); KURE's `eval/` scripts are a ready harness [V]. Use them only to
  confirm a local install reproduces published numbers, not to choose models for the harness.
- **English/general:** a BEIR subset (SciFact, FiQA, NFCorpus are small) via `beir` [V cloned].
- **Memory/temporal:** LongMemEval_S (500 questions, ~115k tokens each; retrieval eval skips the 30
  abstention items) [V README] and LoCoMo [V repo]; run 50-question subsets with the harness's `recall`
  as the retriever to check temporal and knowledge-update handling.
- **PDF pages:** ViDoRe v2 subset only if ColPali is piloted.

### 6.3 The harness gold set (`evals/retrieval/`)
Follow the existing eval layout (`evals/<area>/tasks/<area>-NNN.yaml`, `locked: true`, splits). Each task:
```yaml
id: retrieval-001
area: retrieval
split: train            # train | heldout (keep ≥30% heldout; never tune RRF/weights on heldout)
locked: true
query_type: exact_id    # one of the 13 matrix rows
query: "evt_20261014_093011_7c1e  무슨 일이었지?"
filters: {}             # optional: scope, since, until, store
gold_ids: [evt_20261014_093011_7c1e]
gold_answer: "Haiku 라벨러가 커밋 프롬프트를 correction으로 잘못 분류함"   # short, for end-to-end judge
must_not: []            # ids that would be wrong (e.g. a superseded decision)
k: 5
budget_tokens: 1500
notes: "picked from the log by hand on 2026-10-20"
```
Seed set: **26 queries** (2–3 per type), written by the user from real data during the first
`review-week` after the index exists. Placeholders below show what each should test; fill gold ids by
hand.

| id | type | query (template) | What it tests |
|---|---|---|---|
| retrieval-001 | 1 exact id | "evt_<real id> 무슨 일이었지?" | id routing, `recall get` |
| retrieval-002 | 1 exact string | an exact error message pasted from a past session | `rg -F` caps |
| retrieval-003 | 1 exact string | a filename fragment of a converted PDF | Glob + manifest |
| retrieval-004 | 2 decision | "what did I decide about invoice numbering?" | decisions filter + latest |
| retrieval-005 | 2 decision | "Acme 용어집 표기 기준 어떻게 하기로 했지?" (Korean) | Korean + supersession (`must_not` = old decision) |
| retrieval-006 | 2 decision | a decision later reversed | supersession chain correctness |
| retrieval-007 | 3 similar | paraphrase of a past stuck situation, no shared keywords | dense > lexical |
| retrieval-008 | 3 similar | Korean description of an English-logged situation | cross-lingual dense |
| retrieval-009 | 3 similar | "when did a subagent fan-out blow the budget?" | intent embeddings + outcome |
| retrieval-010 | 4 client | "everything about <client> (Korean name)" | alias linking KO→id, cross-store join |
| retrieval-011 | 4 client | "everything about <client> since July" | join + time filter |
| retrieval-012 | 5 pref change | "how has my preference on email tone changed?" | ordered history, not top-k |
| retrieval-013 | 5 pref change | "파일명 규칙 선호가 언제 바뀌었지?" | Korean + history |
| retrieval-014 | 6 patterns | "which patterns relate to pat_<id>?" | edges/PPR |
| retrieval-015 | 6 patterns | "is there a pattern for repeated deadline renegotiation?" | vec over pattern descriptions + graph |
| retrieval-016 | 7 Korean | a 2-syllable Korean term (e.g. 납기) | trigram silent miss → Kiwi/LIKE |
| retrieval-017 | 7 Korean | inflected form with particle (e.g. 보험금을) | Kiwi query analysis |
| retrieval-018 | 7 Korean | sub-compound (e.g. 계약 inside 계약서) | trigram/LIKE vs Kiwi miss |
| retrieval-019 | 8 PDF | "payment terms clause in <contract doc>" | doc filter + chunk hybrid + rerank + page anchor |
| retrieval-020 | 8 PDF | Korean passage in a kordoc-converted HWP/PDF | Korean chunks |
| retrieval-021 | 8 PDF | table value from a low-confidence scan | known-hard; ColPali pilot candidate |
| retrieval-022 | 9 as-of | "what was my per-word rate as of June 30?" | as-of view |
| retrieval-023 | 9 as-of | "which applications were open on 2026-06-30?" | newest-wins fold at T |
| retrieval-024 | 10 count | "corrections per week in translation since August" | SQL template |
| retrieval-025 | 11 global | "what were my recurring problems last quarter?" | summary nodes + citations |
| retrieval-026 | abstain | a plausible question with no answer in the data | abstention, no hallucinated id |

**Gate:** a retrieval change (new model, weights, tokenizer, layer) ships only if heldout Recall@10 does
not drop for any query type and the mean tokens returned does not rise more than 10%; this mirrors the
harness's existing `eval_gate.py` rule ("no area regresses"). Grow the set by turning every real
retrieval miss the user notices into a new task (the review-week loop).

---

## 7. Build order

| Phase | Work | Unblocks |
|---|---|---|
| R0 (now) | `recall get/grep/sql` over bronze with caps; L0 catalog card; route rules; write the 26 gold queries | types 1, 2, 9, 10 at near-zero cost |
| R1 (with `lake.py index`) | `units` + `fts_tri` + `fts_ko` (Kiwi) + LIKE fallback; contextual `ctx` column; as-of views | types 2, 7, 12; Korean safety |
| R2 | bge-m3 embeddings of `content`, `intent`, pattern descriptions, wiki chunks; RRF; `recall eval` ablations | types 3, 6, 8, 13 |
| R3 | reranker daemon; edges table + PPR; summary nodes indexed with `level` | types 3, 4, 6, 11 |
| R4 | vault twin index (local only); KURE-v1/v2 A/B; MCP wrapper; qmd trial on one wiki | vault queries, Korean quality |
| R5 (only if gold set shows need) | ColPali for scanned PDFs; LightRAG/LazyGraphRAG for a large wiki; LLMLingua for long passages | the remaining hard cases |

---

## 8. Benchmarks to run on the new Mac (20 minutes)
```bash
# 1) rg + DuckDB over the real bronze
time rg -c '보험금' "$HARNESS_DATA"/log ; time duckdb -c "select type,count(*) from read_json('$HARNESS_DATA/log/*.jsonl') group by 1"
# 2) Korean tokenizer check on real prompts (adapt retrtest/ko_fts.py to read 2,000 real prompts)
# 3) embedding throughput: 1,000 real events, batch 32, bge-m3 via Ollama /api/embed vs sentence-transformers MPS; record passages/s and query ms
# 4) sqlite-vec KNN at the real N, float vs bit (retrtest/vec_bench*.py with N set to the real count)
# 5) reranker: 40 (query, passage) pairs, bge-reranker-v2-m3 and KURE-Reranker-nano on MPS; record ms
# 6) recall eval on the 26 gold queries, all ablations; save to evals/results/retrieval/
```
The scripts under `/tmp/claude-0/-home-user-albers-club/1397d302-c3cb-5329-ad06-e45b2c66c6d1/scratchpad/retrtest/`
are scratch copies; move the useful ones into `claude-harness/scripts/bench/` if adopted.

---

## 9. Open questions for the user
1. Is a ~1 GB local model daemon (embeddings + reranker) acceptable always-on, or only on demand?
2. Should the vault index use KURE (Korean-first) even if harness-data uses bge-m3, given the two
   indexes never mix?
3. Which client aliases (Korean/English names, abbreviations) should seed the `aliases` table?
4. Are there PDFs where tables/figures matter enough to pilot ColPali (phase R5)?
5. Is a Haiku LLM reranker acceptable for harness-data queries (it sends snippets to Anthropic, as the
   labeler already does), or local-only everywhere?

---

## Sources
Fetched or read directly [V]:
- Anthropic, Introducing Contextual Retrieval: https://www.anthropic.com/news/contextual-retrieval
- Anthropic, Effective context engineering for AI agents: https://www.anthropic.com/engineering/effective-context-engineering-for-ai-agents
- Claude blog, Building agents with the Claude Agent SDK: https://claude.com/blog/building-agents-with-the-claude-agent-sdk
- qmd CJK issue #617: https://github.com/tobi/qmd/issues/617
- Cloned READMEs/source: github.com/nlpai-lab/KURE (MTEB-kor, sparse, reranker and late-interaction deploy tables), github.com/HKUDS/LightRAG, github.com/getzep/graphiti (`edges.py`, `search_config_recipes.py`, `search_utils.py`), github.com/OSU-NLP-Group/HippoRAG, github.com/xiaowu0162/LongMemEval, github.com/microsoft/LLMLingua, github.com/bab2min/kiwipiepy, github.com/tobi/qmd, github.com/asg017/sqlite-vec, github.com/mem0ai/mem0, github.com/QwenLM/Qwen3-Embedding, github.com/microsoft/graphrag, github.com/parthsarthi03/raptor, github.com/snap-research/locomo, github.com/beir-cellar/beir, github.com/FlagOpen/FlagEmbedding

Search results only [S]:
- Boris Cherny on X: https://x.com/bcherny/status/2017824286489383315
- SmartScope, why Claude Code dropped vector RAG: https://smartscope.blog/en/ai-development/practices/rag-debate-agentic-search-code-exploration/
- vadim.blog, Claude Code doesn't index your codebase: https://vadim.blog/claude-code-no-indexing/
- Keyword search is all you need (arXiv 2602.23368): https://arxiv.org/abs/2602.23368v1 ; https://www.amazon.science/publications/keyword-search-is-all-you-need-achieving-rag-level-performance-without-vector-databases-using-agentic-tool-use
- Qwen3 Embedding (arXiv 2506.05176): https://arxiv.org/pdf/2506.05176 ; https://github.com/QwenLM/Qwen3-Embedding
- MTEB embeddings overview (Morph): https://www.morphllm.com/ollama-embedding-models
- M3-Embedding (bge-m3) paper: https://arxiv.org/pdf/2402.03216
- dragonkue/BGE-m3-ko: https://huggingface.co/dragonkue/BGE-m3-ko
- HippoRAG 2 (arXiv 2502.14802): https://arxiv.org/pdf/2502.14802 ; re-runs: https://arxiv.org/pdf/2609.19622 , https://arxiv.org/pdf/2607.11683
- LazyGraphRAG: https://www.microsoft.com/en-us/research/blog/lazygraphrag-setting-a-new-standard-for-quality-and-cost/
- Mem0 benchmarks: https://mem0.ai/blog/ai-memory-benchmarks-in-2026 ; Mem0 paper https://arxiv.org/pdf/2504.19413 ; claimed vs observed: https://www.maximem.ai/blog/state-of-ai-memory-2026-claimed-vs-observed
- Zep vs Mem0: https://atlan.com/know/zep-vs-mem0/ ; LongMemEval-S summary: https://www.emergentmind.com/topics/longmemeval-s-benchmark
- Rerankers: https://blog.voyageai.com/2025/08/11/rerank-2-5/ ; https://hevmind.com/writing/jev-as-a-reranker/ ; LAMAR https://arxiv.org/pdf/2607.22042
- ColPali / ViDoRe: https://arxiv.org/pdf/2407.01449 ; https://arxiv.org/pdf/2505.17166 ; reproducibility https://arxiv.org/pdf/2505.07730 ; Lost in OCR Translation https://arxiv.org/pdf/2505.05666
- SQLite FTS5: https://www.sqlite.org/fts5.html ; fts5-cjk: https://github.com/Ray0907/fts5-cjk
- Kiwi + BM25 (Korean tutorial): https://wikidocs.net/251980 ; ranx-k: https://pypi.org/project/ranx-k/
- Text-to-SQL: Spider 2.0 https://huggingface.co/papers/2411.07763 ; benchmark errors https://github.com/uiuc-kang-lab/text_to_sql_benchmarks , https://www.cidrdb.org/cidr2026/slides/Kang-16.pdf
- Matryoshka/quantization: https://docs.voyageai.com/docs/flexible-dimensions-and-quantization ; https://mixpeek.com/guides/embedding-quantization-compression
- MCP memory servers: https://github.com/sdsrss/claude-mem-lite ; https://www.datacamp.com/tutorial/claude-mem-guide ; https://heyclau.de/compare/memory-mcp-servers ; https://wavect.io/blog/mcp-memory-service-claude-code-cursor/
- Progressive disclosure / skills: https://rubinlake.com/en/technology-radar/ai-and-data-engineering/progressive-context-disclosure ; https://www.newsletter.swirlai.com/p/state-of-context-engineering-in-2026

Unreachable this session: arxiv.org and export.arxiv.org (proxy 403), huggingface.co (proxy 403; no model
cards, no live MTEB leaderboard).
