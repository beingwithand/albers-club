# Mem0 (incl. OpenMemory MCP) and LangMem: code-level teardown for Relic

Method: these notes come from shallow clones that were read only and never run.
- mem0 HEAD `0724291bd864cf807e88ee8981c8226644e8fb42` (2026-10-14, package `mem0ai` 2.2.1). Short name below: **M2**.
- mem0 tag `v1.0.11` (`144627c4ce5bc4db6acac17cbd158065f2b27a8d`, 2026-04-06). This is the last 1.x line, which still has the paper-era ADD/UPDATE/DELETE pipeline, graph memory and the `openmemory/` app. Short name below: **M1**.
- langmem HEAD `48e3c11f5bb527282c7d5339c6a87a0b35abccfc` (2026-10-02, version 0.0.30).

Licenses: mem0 is Apache-2.0 ([LICENSE](https://github.com/mem0ai/mem0/blob/0724291bd864cf807e88ee8981c8226644e8fb42/LICENSE)). LangMem is MIT, "Copyright (c) 2025 LangChain" ([LICENSE](https://github.com/langchain-ai/langmem/blob/48e3c11f5bb527282c7d5339c6a87a0b35abccfc/LICENSE)). Both are permissive, so their prompts and algorithms can be ported, provided attribution and the license notice are kept.

URL prefixes used below:
- M2 = `https://github.com/mem0ai/mem0/blob/0724291bd864cf807e88ee8981c8226644e8fb42/`
- M1 = `https://github.com/mem0ai/mem0/blob/144627c4ce5bc4db6acac17cbd158065f2b27a8d/`
- LM = `https://github.com/langchain-ai/langmem/blob/48e3c11f5bb527282c7d5339c6a87a0b35abccfc/`

**Headline finding:** Mem0 has **two different algorithms**. The arXiv paper (2504.19413) describes the M1 design: two LLM calls per add, an ADD/UPDATE/DELETE/NOOP decision, and an optional Neo4j graph. Current Mem0 (M2, "new memory algorithm", released as SDK v2.x, called "V3" in code comments) **removed UPDATE/DELETE and removed graph memory and OpenMemory from OSS**. It replaced them with:
- **one ADD-only LLM call** per add;
- **hybrid retrieval**: semantic plus BM25 plus a spaCy entity boost;
- an "entities" side collection.

Anyone citing "how Mem0 works" must say which version they mean.

---

## Q1. Mem0 add() pipeline, step by step (current M2 vs paper-era M1)

### Takeaway
Current Mem0 does the following on each add:
1. Makes one embedding of the whole new message batch.
2. Retrieves the top-10 existing memories.
3. Makes **one** LLM call with a long "ADD-only" extraction prompt.
4. Drops exact duplicates by MD5.
5. Batch-inserts the vectors.
6. Writes an SQLite history row for each memory.
7. Links spaCy-extracted entities into a side vector collection.

There is no LLM-based update or delete. The old M1 pipeline made two LLM calls instead: fact extraction, then an ADD/UPDATE/DELETE/NONE decision over up to 5 neighbours per fact. It also optionally ran a parallel three-to-four-call graph pipeline.

### Cited Findings

**M2 (current) `Memory.add` → `_add_to_vector_store`.** Source: [M2 mem0/memory/main.py L760-1220](https://github.com/mem0ai/mem0/blob/0724291bd864cf807e88ee8981c8226644e8fb42/mem0/memory/main.py#L760-L1220). The code labels this block `# === V3 PHASED BATCH PIPELINE ===`.
- **Input normalisation.** A string becomes `[{"role":"user","content":...}]`. Vision messages are optionally converted to text by the LLM. If `infer=False`, each non-system message is embedded and stored verbatim, with no LLM call (L881-912).
- **Phase 0, context gathering.** `session_scope` is a deterministic string such as `agent_id=..&run_id=..&user_id=..` (L412-420). The code calls `last_messages = self.db.get_last_messages(session_scope, limit=10)`, which reads from the SQLite `messages` table.
- **Phase 1, existing-memory retrieval.** The code calls `query_embedding = self.embedding_model.embed(parsed_messages, "search")` and then `vector_store.search(..., top_k=10, filters=search_filters)`. This is a *single* embedding of the whole concatenated new-message text, not one embedding per fact.
- **Anti-hallucination ID mapping.** Existing memory UUIDs are replaced by "0", "1", … before going into the prompt (comment: `# Map UUIDs to integers (anti-hallucination)`).
- **Phase 2, one LLM call.** The system prompt is `ADDITIVE_EXTRACTION_PROMPT`, plus `AGENT_CONTEXT_SUFFIX` if the add is agent-scoped. The user prompt comes from `generate_additive_extraction_prompt(existing_memories, new_messages, last_k_messages, custom_instructions)`. The call uses `response_format={"type":"json_object"}`. If the LLM call fails, an `LLMError` is raised. Earlier versions returned `[]` silently (code comment).
- **Phases 3-5, embedding and dedup.** All extracted texts are embedded in one batch (`embed_batch`). Dedup is `hashlib.md5(text.encode()).hexdigest()` compared against the hashes of the top-10 retrieved memories plus those within the batch. It is **exact string-hash only**.
- **What each record stores:**
  - `data`
  - `text_lemmatized`, from `lemmatize_for_bm25`
  - `hash`
  - `created_at` and `updated_at`
  - `attributed_to`
  - the scope IDs and metadata
- **Phase 6, persistence.** Batch `vector_store.insert`, falling back to per-item inserts. Then `db.batch_add_history`, with rows of the form `{memory_id, old_memory: None, new_memory, event: "ADD", ...}`.
- **Phase 7, entity linking.** `extract_entities_batch(texts)` uses spaCy (a regex-free NLP heuristic, not an LLM). Steps:
  - Entities are normalised and globally deduped, then batch-embedded.
  - Each entity is matched against the `{collection}_entities` store, first by exact text, then by semantic match `if matches[0].score >= 0.95`.
  - If there is a match, the memory ID is appended to `linked_memory_ids`. Otherwise a new entity record `{data, entity_type, linked_memory_ids, user_id/agent_id/run_id}` is inserted.
  - Any failure here is only logged as a warning.
- **Phase 8.** The raw messages are saved to the SQLite `messages` table. The return value is `[{"id","memory","event":"ADD"}]`.

**Mem0's own migration doc confirms the redesign.** Source: [M2 docs/migration/oss-v2-to-v3.mdx](https://github.com/mem0ai/mem0/blob/0724291bd864cf807e88ee8981c8226644e8fb42/docs/migration/oss-v2-to-v3.mdx); corroborated by search results for [docs.mem0.ai/migration/oss-v2-to-v3](https://docs.mem0.ai/migration/oss-v2-to-v3.md).
- "Extraction: Single-pass ADD-only (one LLM call, no UPDATE/DELETE)".
- "Graph memory moved to Platform: The external graph store integration is removed from OSS".
- `add()` events "Returns ADD only".
- `custom_fact_extraction_prompt` was renamed to `custom_instructions`, and `custom_update_memory_prompt` is "Deprecated".
- Defaults changed: `top_k` 100→20, `threshold` None→0.1, `rerank` True→False.
- The vendor claims "+20 point improvement on LoCoMo (71.4 → 91.6) and +26 point improvement on LongMemEval (67.8 → 93.4), while cutting extraction latency roughly in half".

**The M2 extraction prompt (`ADDITIVE_EXTRACTION_PROMPT`).** Source: [M2 mem0/configs/prompts.py L468-946](https://github.com/mem0ai/mem0/blob/0724291bd864cf807e88ee8981c8226644e8fb42/mem0/configs/prompts.py#L468). It is about 480 lines with 12 worked examples. Key verbatim lines:
- "You are a Memory Extractor — a precise, evidence-bound processor … Your sole operation is ADD: identify every piece of memorable information and produce self-contained, contextually rich factual statements."
- "You extract from BOTH user and assistant messages."
- "Concise but Complete (15-80 words, up to 100 for detail-rich content)"; "Contextually Rich, Not Atomic"; "Temporally Grounded".
- "**When in doubt, extract.** A slightly redundant memory is far less costly than a missing one. The deduplication system downstream will handle true duplicates".
- Linking rules: "Link when: Same entity/topic … Updated preference … Continuation … Contradiction: New information that conflicts with an existing memory".
- Date grounding: "Resolve ALL relative references against Observation Date … 'User went to Paris last week' is useless 6 months later."
- Recall checklist: "For conversations with 10+ messages, you should typically extract 5-15 memories. If you have fewer than 3, re-read the conversation".
- Output format: `{"memory":[{"id":"0","text":"...","attributed_to":"user","linked_memory_ids":["uuid-of-related-existing-memory"]}]}`.
- The code comment says the prompt was "Ported from platform/backend/shared/core/utils/prompt_builder.py".

**The OSS prompt builder sends fewer inputs than the prompt describes.** Source: [M2 prompts.py L1016-1062](https://github.com/mem0ai/mem0/blob/0724291bd864cf807e88ee8981c8226644e8fb42/mem0/configs/prompts.py#L1016) and [main.py `_add_to_vector_store`](https://github.com/mem0ai/mem0/blob/0724291bd864cf807e88ee8981c8226644e8fb42/mem0/memory/main.py#L881).
- The builder has sections for Summary, Last k Messages, Recently Extracted Memories, Existing Memories, New Messages, Observation Date, Current Date, Custom Instructions and an optional language block.
- In OSS, `add()` passes only `existing_memories`, `new_messages`, `last_k_messages` and `custom_instructions`.
- So Summary and Recently Extracted Memories are always empty. Observation Date falls back to today, because `timestamp` raises `ValueError` in OSS as a "Platform-only temporal parameter".
- Past messages are truncated to 300 characters (`PAST_MESSAGE_TRUNCATION_LIMIT = 300`).

**M1 (paper-era) `_add_to_vector_store`.** Source: [M1 mem0/memory/main.py L475-700](https://github.com/mem0ai/mem0/blob/144627c4ce5bc4db6acac17cbd158065f2b27a8d/mem0/memory/main.py#L475).
1. LLM call #1 uses `FACT_RETRIEVAL_PROMPT`, or `USER_MEMORY_EXTRACTION_PROMPT` / `AGENT_MEMORY_EXTRACTION_PROMPT` depending on agent_id and assistant role. It returns `{"facts":[...]}`.
2. For each fact: `embed(new_mem)` then `vector_store.search(..., limit=5, filters=search_filters)`. Results are unioned and deduped by ID.
3. UUIDs are mapped to integers ("mapping UUIDs with integers for handling UUID hallucinations").
4. LLM call #2 uses `get_update_memory_messages(retrieved_old_memory, new_retrieved_facts, custom_update_memory_prompt)` and returns `{"memory":[{id,text,event,old_memory}]}`.
5. Events are applied:
   - ADD → `_create_memory`
   - UPDATE → `_update_memory(temp_uuid_mapping[id])`
   - DELETE → `_delete_memory`
   - NONE → only refreshes agent_id/run_id on the existing record.
6. If graph is enabled, `_add_to_graph` runs in parallel on a thread pool (L460).

**M1 fact prompt, verbatim excerpts.** Source: [M1 prompts.py L14-60](https://github.com/mem0ai/mem0/blob/144627c4ce5bc4db6acac17cbd158065f2b27a8d/mem0/configs/prompts.py#L14).
- "You are a Personal Information Organizer, specialized in accurately storing facts, user memories, and preferences."
- Seven categories, starting "1. Store Personal Preferences … 2. Maintain Important Personal Details … 3. Track Plans and Intentions … 5. Monitor Health and Wellness Preferences … 6. Store Professional Details".
- Few-shot example: `Input: Hi, my name is John. I am a software engineer. Output: {"facts" : ["Name is John", "Is a Software engineer"]}`.
- "Today's date is {datetime.now().strftime("%Y-%m-%d")}", which is evaluated once in an f-string at import time.
- "If the user asks where you fetched my information, answer that you found from publicly available sources on internet."
- "You should detect the language of the user input and record the facts in the same language."
- `USER_MEMORY_EXTRACTION_PROMPT` adds: "GENERATE FACTS SOLELY BASED ON THE USER'S MESSAGES … YOU WILL BE PENALIZED IF YOU INCLUDE INFORMATION FROM ASSISTANT OR SYSTEM MESSAGES" ([L62](https://github.com/mem0ai/mem0/blob/144627c4ce5bc4db6acac17cbd158065f2b27a8d/mem0/configs/prompts.py#L62)).

**Default models and parameters.**
- M2 default LLM is `gpt-5-mini` ([M2 mem0/llms/openai.py L40](https://github.com/mem0ai/mem0/blob/0724291bd864cf807e88ee8981c8226644e8fb42/mem0/llms/openai.py#L40)).
- M1 default LLM is `gpt-4.1-nano-2025-04-14` ([M1 mem0/llms/openai.py L39](https://github.com/mem0ai/mem0/blob/144627c4ce5bc4db6acac17cbd158065f2b27a8d/mem0/llms/openai.py#L39)).
- Default embedder is `text-embedding-3-small` ([M2 embeddings/openai.py L15](https://github.com/mem0ai/mem0/blob/0724291bd864cf807e88ee8981c8226644e8fb42/mem0/embeddings/openai.py#L15)).
- LLM sampling defaults: `temperature=0.1`, `max_tokens=2000`, `top_p=0.1` ([M2 configs/llms/base.py L19-22](https://github.com/mem0ai/mem0/blob/0724291bd864cf807e88ee8981c8226644e8fb42/mem0/configs/llms/base.py#L19)).
- Default vector store is `qdrant` at `path="/tmp/qdrant"` with `on_disk=False` ([M2 vector_stores/configs.py L7-10](https://github.com/mem0ai/mem0/blob/0724291bd864cf807e88ee8981c8226644e8fb42/mem0/vector_stores/configs.py#L7); [configs/vector_stores/qdrant.py L16,23](https://github.com/mem0ai/mem0/blob/0724291bd864cf807e88ee8981c8226644e8fb42/mem0/configs/vector_stores/qdrant.py#L16)).
- History DB is `~/.mem0/history.db` ([M2 configs/base.py L42-44](https://github.com/mem0ai/mem0/blob/0724291bd864cf807e88ee8981c8226644e8fb42/mem0/configs/base.py#L42)).
- spaCy model is `en_core_web_sm`, auto-downloaded if missing ([M2 utils/spacy_models.py L30-60](https://github.com/mem0ai/mem0/blob/0724291bd864cf807e88ee8981c8226644e8fb42/mem0/utils/spacy_models.py#L30)).

**What the paper describes, from secondary sources (the arXiv PDF could not be fetched here).**
- Extraction is conditioned on a conversation summary plus the last *m* messages, and the top-s similar memories are retrieved.
- Update decisions are ADD/UPDATE/DELETE/NOOP made "through tool calls".
- One summary says the paper uses m=10, s=10 and GPT-4o-mini.

Sources: [medium.com/@zeng.m.c22381](https://medium.com/@zeng.m.c22381/mem0-overall-architecture-and-principles-8edab6bc6dc4); [viblo.asia](https://viblo.asia/p/mem0-kien-truc-long-term-memory-cho-he-thong-ai-agent-G24B88pOLz3); [juejin.cn](https://juejin.cn/post/7564660554049896474); [D-Mem arXiv 2603.18631](https://arxiv.org/pdf/2603.18631). The README headline claims "+26% Accuracy over OpenAI Memory on the LOCOMO benchmark", "91% Faster Responses than full-context" and "90% Lower Token Usage than full-context" ([M1 README.md L45-53](https://github.com/mem0ai/mem0/blob/144627c4ce5bc4db6acac17cbd158065f2b27a8d/README.md#L45)).

**Third-party evaluation findings.**
- A third-party benchmark reports Mem0 at about 1,534 tokens/query and 0.51 s, with F1 35.38 on LoCoMo ([GAM arXiv 2604.12285 via search](https://arxiv.org/pdf/2604.12285)).
- Another study reports that with the default `gpt-4.1-nano`, Mem0 shows "frequent JSON parse errors during UPDATE and DELETE operations" ([arXiv 2609.10413 via search](https://arxiv.org/pdf/2609.10413)).

### Inferences
- **The paper and the M1 code differ.** M1's fact extraction sees only the *new* messages (`parse_messages(messages)`), with no summary and no last-m window. It retrieves `limit=5` neighbours per fact rather than s=10, and uses JSON mode rather than tool calls. The paper's "summary" input appears to have existed only on the hosted platform. M2 finally adds the last-10 messages (from SQLite), but still no summary in OSS.
- **M2 moves work from the LLM to cheap deterministic CPU code:**
  - spaCy NER and lemmas;
  - MD5 dedup;
  - entity-vector matching at ≥0.95.

  That suits on-device use: one LLM call per turn plus embeddings.
- **The M2 prompt is very long**, roughly 35 KB, about 9-10k tokens of system prompt. That is costly on a small local model's context and prefill. Relic should distil it to a short prompt plus 3-4 examples.

### Gaps
- I could not fetch the arXiv PDF (arxiv.org is blocked). Paper hyperparameters (m, s, model) and the Mem0g ablation numbers come only from secondary summaries.
- The platform-side summary generator ("narrative summary of the user's profile") is not in OSS. Its prompt is unknown.

---

## Q2. Mem0 search() pipeline, ranking and scoring

### Takeaway
Current Mem0 search works as follows:
1. Over-fetch semantic candidates: `max(4*top_k, 60)`.
2. Fetch native BM25 keyword candidates over lemmatised text.
3. Squash BM25 scores through a sigmoid whose parameters depend on query length.
4. Add an entity boost of up to 0.5 from the entities collection.
5. Sum the three signals and normalise by the maximum possible score.
6. Gate on semantic score ≥ 0.1 and return the top-20.

There is no recency or importance decay, and search makes no LLM call. M1 was pure vector search, plus an optional parallel graph search that returned only the BM25-reranked top-5 triples.

### Cited Findings

**`_search_vector_store` (M2).** Source: [M2 main.py L1642-1745](https://github.com/mem0ai/mem0/blob/0724291bd864cf807e88ee8981c8226644e8fb42/mem0/memory/main.py#L1642).
1. `lemmatize_for_bm25(query)` and `extract_entities(query)`, both spaCy.
2. Embed the query.
3. `internal_limit = max(limit * 4, 60)`, then a semantic search.
4. `vector_store.keyword_search(query_lemmatized, top_k=internal_limit)`.
5. `normalize_bm25(raw, midpoint, steepness)`.
6. `_compute_entity_boosts`.
7. Drop expired memories (`expiration_date`).
8. `score_and_rank`.

**Important detail:** the candidate set is the *semantic* results only. BM25 and entity signals only re-score memories that vector search already found.

**Scoring code.** Source: [M2 mem0/utils/scoring.py L16-139](https://github.com/mem0ai/mem0/blob/0724291bd864cf807e88ee8981c8226644e8fb42/mem0/utils/scoring.py#L16).
- BM25 sigmoid parameters by number of lemmatised query terms: ≤3 → (5.0, 0.7); ≤6 → (7.0, 0.6); ≤9 → (9.0, 0.5); ≤15 → (10.0, 0.5); otherwise (12.0, 0.5).
- `normalize_bm25 = 1/(1+exp(-steepness*(raw-midpoint)))`.
- `ENTITY_BOOST_WEIGHT = 0.5`.
- `combined = min((semantic + bm25 + entity_boost) / max_possible, 1.0)`, where `max_possible` is 1.0, plus 1.0 if any BM25 hits, plus 0.5 if any entity boosts.
- "Threshold gates the semantic score BEFORE combining".

**Entity boost.** Source: [M2 main.py L1747-1827](https://github.com/mem0ai/mem0/blob/0724291bd864cf807e88ee8981c8226644e8fb42/mem0/memory/main.py#L1747).
- Take at most 8 query entities and embed them in a batch.
- Each entity searches the entity store with `top_k=500`. Matches with similarity < 0.5 are skipped.
- `memory_count_weight = 1/(1+0.001*(num_linked-1)**2)`, which down-weights hub entities.
- `boost = similarity * 0.5 * memory_count_weight`. Each memory keeps its maximum boost.
- Up to 4 searches run in a thread pool.

**spaCy entity extraction (no LLM).** Source: [M2 mem0/utils/entity_extraction.py](https://github.com/mem0ai/mem0/blob/0724291bd864cf807e88ee8981c8226644e8fb42/mem0/utils/entity_extraction.py).
- Types are PROPER, QUOTED, TOPIC and IDENTIFIER.
- Accepted NER labels: PERSON, ORG, GPE, LOC, FAC, PRODUCT, WORK_OF_ART, EVENT, NORP, LAW, LANGUAGE. DATE, TIME, CARDINAL, MONEY and similar are rejected.
- There are stop-lists of generic heads ("thing", "time", "experience", …) and generic single terms ("user", "assistant", "memory", …).

**Lemmatisation.** `en_core_web_sm` with NER and parser disabled. Stopwords and punctuation are dropped. The original "-ing" token is kept alongside its lemma ([M2 utils/lemmatization.py](https://github.com/mem0ai/mem0/blob/0724291bd864cf807e88ee8981c8226644e8fb42/mem0/utils/lemmatization.py)).

**Keyword-search backends.**
- Qdrant implements `keyword_search` with BM25 sparse vectors in the same collection (`using="bm25"`), encoded by fastembed. It returns `None` if fastembed is unavailable ([M2 vector_stores/qdrant.py L454-484](https://github.com/mem0ai/mem0/blob/0724291bd864cf807e88ee8981c8226644e8fb42/mem0/vector_stores/qdrant.py#L454)).
- Other stores with `keyword_search`: azure_ai_search, azure_mysql, baidu, databricks, elasticsearch, milvus, mongodb, opensearch, pgvector, pinecone, redis, upstash_vector, vertex_ai_vector_search, weaviate.
- **Not supported:** chroma and faiss, so those fall back to semantic-only.
- The docs warn: "Without it [fastembed], BM25 is silently disabled" ([migration doc](https://github.com/mem0ai/mem0/blob/0724291bd864cf807e88ee8981c8226644e8fb42/docs/migration/oss-v2-to-v3.mdx)).

**Optional reranker.** `rerank=False` by default. Providers are Cohere, HuggingFace, LLM-based, Sentence Transformer and Zero Entropy ([M2 main.py search](https://github.com/mem0ai/mem0/blob/0724291bd864cf807e88ee8981c8226644e8fb42/mem0/memory/main.py#L1393); [mem0/CLAUDE.md](https://github.com/mem0ai/mem0/blob/0724291bd864cf807e88ee8981c8226644e8fb42/mem0/CLAUDE.md)).

**M1 search.**
- `_search_vector_store` filters `mem.score >= threshold` only when a threshold is given. The default was `None` and the default limit 100.
- `graph.search` runs concurrently in a thread pool ([M1 main.py L867-960, L1063-1100](https://github.com/mem0ai/mem0/blob/144627c4ce5bc4db6acac17cbd158065f2b27a8d/mem0/memory/main.py#L938)).

### Inferences
- The M2 ranking needs no LLM at query time. It is fully replicable on-device:
  - SQLite FTS5 for BM25;
  - sqlite-vec or similar for vectors;
  - an entity table holding (entity text, embedding, linked memory IDs).
- The fixed sigmoid parameters are tuned for English BM25 score ranges. Relic would need to retune them for its own corpus size and tokenizer, especially for Korean or CJK text, since spaCy `en_core_web_sm` is English-only.
- There is no recency term at all. With ADD-only storage, the "current" answer to a changed preference depends on the answering LLM noticing dates in the returned texts. See Q3.

### Gaps
- I did not find any published ablation separating the BM25 and entity contributions in M2. The only figures are vendor aggregate benchmark numbers.

---

## Q3. How conflicts and updates are resolved (dedup, history, soft delete)

### Takeaway
- **M1** let the LLM decide UPDATE or DELETE against the top-5-per-fact neighbours. Updates overwrite in place; deletes hard-delete the vector. Both are logged to an SQLite `history` table.
- **M2** never updates or deletes automatically. Contradictions are only *linked* in the prompt's output, and the OSS code discards those links. Dedup is exact MD5. "Current truth" is left to retrieval and the downstream LLM.
- **Graph memory (M1 only)** soft-deleted contradicted edges (`r.valid=false`).

### Cited Findings

**M1 update prompt, `DEFAULT_UPDATE_MEMORY_PROMPT`.** Source: [M1 prompts.py L175-324](https://github.com/mem0ai/mem0/blob/144627c4ce5bc4db6acac17cbd158065f2b27a8d/mem0/configs/prompts.py#L175).
- "You are a smart memory manager which controls the memory of a system. You can perform four operations: (1) add into the memory, (2) update the memory, (3) delete from the memory, and (4) no change."
- UPDATE: "If the retrieved facts contain information that is already present in the memory but the information is totally different, then you have to update it."
- DELETE: "If the retrieved facts contain information that contradicts the information present in the memory, then you have to delete it. Or if the direction is to delete the memory, then you have to delete it."
- Example: old "Loves cheese pizza" plus fact "Dislikes cheese pizza" → DELETE.
- Example: "User likes to play cricket" → UPDATE to "Loves to play cricket with friends".

**M1 wrapper, `get_update_memory_messages`.** Source: [M1 prompts.py L405-470](https://github.com/mem0ai/mem0/blob/144627c4ce5bc4db6acac17cbd158065f2b27a8d/mem0/configs/prompts.py#L405).
- It wraps the old memories in "Below is the current content of my memory …".
- Required output: `{"memory":[{"id","text","event": "ADD"|"UPDATE"|"DELETE"|"NONE","old_memory"}]}`.
- It instructs: "If there is an addition, generate a new key … If there is an update, the ID key should remain the same".

**M1 `_delete_memory` is a hard delete.** It calls `vector_store.delete`, then writes history with `old_memory=prev, new_memory=None, event="DELETE", is_deleted=1` ([M1 main.py L1340-1365](https://github.com/mem0ai/mem0/blob/144627c4ce5bc4db6acac17cbd158065f2b27a8d/mem0/memory/main.py#L1340)). The prior text survives only in SQLite history, not in the searchable store.

**SQLite history schema (same in M1 and M2).** Source: [M2 mem0/memory/storage.py L68-143](https://github.com/mem0ai/mem0/blob/0724291bd864cf807e88ee8981c8226644e8fb42/mem0/memory/storage.py#L68).
- `history(id TEXT PK, memory_id, old_memory, new_memory, event, created_at, updated_at, is_deleted INTEGER, actor_id, role)`.
- M2 adds `messages(id, session_scope, role, content, name, created_at)`, used for the last-10-messages context.
- `history(memory_id)` returns the audit trail for one memory.

**M2 manual update.** `Memory.update()` / `_update_memory` still exists for user-driven edits. It re-embeds, re-lemmatises and re-hashes, preserves `created_at`, writes an UPDATE history row, and re-links entities if the text changed ([M2 main.py L2052-2113](https://github.com/mem0ai/mem0/blob/0724291bd864cf807e88ee8981c8226644e8fb42/mem0/memory/main.py#L2052)).

**M2 never stores the LLM's `linked_memory_ids`.**
- The extraction loop copies only `text` and `attributed_to` into the payload ([M2 main.py ~L1035-1060](https://github.com/mem0ai/mem0/blob/0724291bd864cf807e88ee8981c8226644e8fb42/mem0/memory/main.py#L1035)).
- The prompt even says "linked_memory_ids uses the UUIDs from this list", but the code feeds integer IDs "0", "1", ….
- The only `linked_memory_ids` that persist are the spaCy entity→memory links in the entities collection.

**Vendor framing of the new model.** Search summaries of the release notes describe it as: "the new fact is stored next to the old one when information changes, and retrieval ranking surfaces the current information" ([newreleases.io v2.0.0](https://newreleases.io/project/github/mem0ai/mem0/release/v2.0.0); [docs changelog](https://docs.mem0.ai/changelog/sdk)).

**Graph soft-delete (M1).**
- `DELETE_RELATIONS_SYSTEM_PROMPT` says: "Delete a relationship only if … Outdated or Inaccurate … Contradictory … DO NOT DELETE if their is a possibility of same type of relationship but different destination nodes", with the example "alice -- loves_to_eat -- pizza" plus "Alice also loves to eat burger" → do not delete ([M1 graphs/utils.py L57-97](https://github.com/mem0ai/mem0/blob/144627c4ce5bc4db6acac17cbd158065f2b27a8d/mem0/graphs/utils.py#L57)).
- Execution is "Soft-delete: mark relationship as invalid … SET r.valid = false, r.invalidated_at = datetime()". Searches filter `WHERE r.valid IS NULL OR r.valid = true` ([M1 memory/graph_memory.py L383-440, L294-345](https://github.com/mem0ai/mem0/blob/144627c4ce5bc4db6acac17cbd158065f2b27a8d/mem0/memory/graph_memory.py#L383)).

### Inferences
- For Relic, the M1 approach risks wrong deletions, for example "Loves cheese pizza" being deleted on a single negative statement. Every UPDATE also destroys provenance in the live index.
- M2 avoids that risk but accumulates stale facts with no supersession marker.
- A better on-device design combines the two:
  - keep M2's ADD-only append log;
  - add an explicit `supersedes` / `valid_to` field, set either by a small LLM judgement or by user confirmation;
  - add recency weighting in ranking.

  This mirrors M1's graph `valid=false` idea, applied to text memories.
- MD5 dedup on LLM-generated paraphrases will almost never fire, because rephrasings differ by a single character. Semantic near-duplicate merging (cosine ≥ ~0.95) is needed. M2 already uses that threshold for entities, but not for memories.

### Gaps
- No public evaluation of M2's stale-fact behaviour (knowledge-update questions) separate from aggregate LoCoMo/LongMemEval scores was found.

---

## Q4. Graph memory (Mem0g) as implemented in M1 (removed from OSS in M2)

### Takeaway
M1 graph memory makes **three or more LLM tool calls per add**:
1. Entity extraction.
2. Relation-triple extraction.
3. Deletion judgement over existing triples, with node matching by embedding similarity ≥ 0.7.

Nodes and edges are MERGEd in Neo4j, Memgraph, Kuzu or AGE with mention counters. Search re-extracts entities from the query with an LLM, expands one hop, and BM25-reranks to the top-5 triples. M2 removed all of this from OSS.

### Cited Findings

**Entity extraction call.** System prompt: "You are a smart assistant who understands entities and their types in a given text. If user message contains self reference such as 'I', 'me', 'my' etc. then use {user_id} as the source entity. Extract all the entities from the text. ***DO NOT*** answer the question itself if the given text is a question." It uses the `EXTRACT_ENTITIES_TOOL` function call. Names are lower-cased and spaces become underscores ([M1 graph_memory.py L219-250](https://github.com/mem0ai/mem0/blob/144627c4ce5bc4db6acac17cbd158065f2b27a8d/mem0/memory/graph_memory.py#L219)).

**Relation extraction, `EXTRACT_RELATIONS_PROMPT`.** Verbatim: "You are an advanced algorithm designed to extract structured information from text to construct knowledge graphs … 1. Extract only explicitly stated information from the text. 2. Establish relationships among the entities provided. 3. Use "USER_ID" as the source entity for any self-references … Use consistent, general, and timeless relationship types. Example: Prefer "professor" over "became_professor."" Called via `RELATIONS_TOOL` ([M1 graphs/utils.py L35-55](https://github.com/mem0ai/mem0/blob/144627c4ce5bc4db6acac17cbd158065f2b27a8d/mem0/graphs/utils.py#L35); [graph_memory.py L252-292](https://github.com/mem0ai/mem0/blob/144627c4ce5bc4db6acac17cbd158065f2b27a8d/mem0/memory/graph_memory.py#L252)).

**add() sequence.** Source: [M1 graph_memory.py L76-95](https://github.com/mem0ai/mem0/blob/144627c4ce5bc4db6acac17cbd158065f2b27a8d/mem0/memory/graph_memory.py#L76).
1. `_retrieve_nodes_from_data`
2. `_establish_nodes_relations_from_data`
3. `_search_graph_db` (one embedding plus one Cypher query per node)
4. `_get_delete_entities_from_search_output` (LLM)
5. `_delete_entities`
6. `_add_entities`

**Node and edge details.**
- Node similarity is `round(2 * vector.similarity.cosine(...) - 1, 4)` with the threshold defaulting to 0.7 ("default to 0.7 for backward compatibility").
- Neighbours are fetched one hop in both directions, `LIMIT 100`.
- MERGE sets `created`, `mentions = coalesce(mentions,0)+1`, and `r.created_at` / `r.mentions` on edges ([M1 graph_memory.py L73-74, L294-345, L440-560](https://github.com/mem0ai/mem0/blob/144627c4ce5bc4db6acac17cbd158065f2b27a8d/mem0/memory/graph_memory.py#L294)).

**search().** Runs the LLM entity extraction on the query, then `_search_graph_db`, then `BM25Okapi(...)` over the [source, relationship, destination] token lists, then `get_top_n(..., n=5)` ([M1 graph_memory.py L96-130](https://github.com/mem0ai/mem0/blob/144627c4ce5bc4db6acac17cbd158065f2b27a8d/mem0/memory/graph_memory.py#L96)).

**Removal in M2.** "The external graph store integration is removed from OSS; graph memory is now a built-in, always-on Mem0 Platform feature" ([M2 migration doc](https://github.com/mem0ai/mem0/blob/0724291bd864cf807e88ee8981c8226644e8fb42/docs/migration/oss-v2-to-v3.mdx)). Note that `mem0/CLAUDE.md` at HEAD still lists "graphs/ 4 providers", which is stale; the directory is gone.

### Inferences
- Graph search needs an LLM call *at query time* (entity extraction), which hurts on-device latency. M2's spaCy entity collection is a far cheaper "graph-lite" that keeps most of the benefit.
- Only the triple-extraction step genuinely needs function-calling reliability. Small local models are the weak point here: tool-call JSON errors are reported even for gpt-4.1-nano in M1-style pipelines ([arXiv 2609.10413 via search](https://arxiv.org/pdf/2609.10413)).

### Gaps
- I did not verify the paper's Mem0g accuracy and latency figures, because arxiv.org was not reachable.

---

## Q5. OpenMemory MCP: app scoping and permissions

### Takeaway
OpenMemory, in the M1 tree under `openmemory/` and **removed from HEAD**, is a FastAPI and MCP server on top of `mem0.Memory`. Key properties:
- Identity comes from **URL path parameters** (`/mcp/{client_name}/sse/{user_id}`), with no authentication. Apps are auto-created on first call.
- All apps share one user memory pool by default.
- Scoping is enforced by SQL-side state (active/paused/archived/deleted), an app `is_active` flag and an allow/deny ACL table, applied *after* the vector search.
- An access log records every memory each app reads.
- Every memory is auto-categorised by a hard-coded OpenAI `gpt-4o-mini` call.

### Cited Findings

**Removal from HEAD.** There is no `openmemory/` directory at HEAD, and `docs/docs.json` redirects `/openmemory/overview`, `/openmemory/quickstart` and `/openmemory/integrations` to `/introduction` ([M2 docs/docs.json L1180-1192](https://github.com/mem0ai/mem0/blob/0724291bd864cf807e88ee8981c8226644e8fb42/docs/docs.json#L1180)). The SDK changelog's history of OpenMemory features includes export/import, local support and vector store integrations ([M2 docs/changelog/sdk.mdx L657-662](https://github.com/mem0ai/mem0/blob/0724291bd864cf807e88ee8981c8226644e8fb42/docs/changelog/sdk.mdx#L657)).

**SQLAlchemy schema.** Source: [M1 openmemory/api/app/models.py](https://github.com/mem0ai/mem0/blob/144627c4ce5bc4db6acac17cbd158065f2b27a8d/openmemory/api/app/models.py#L30).
- `MemoryState` enum: active / paused / archived / deleted.
- `User(id, user_id unique, name, email, metadata)`.
- `App(id, owner_id→users, name, description, metadata, is_active)`.
- `Memory(id, user_id, app_id→apps, content, vector, metadata, state, created_at, updated_at, archived_at, deleted_at)`.
- `Category` and the `memory_categories` M:N table.
- `AccessControl(subject_type, subject_id, object_type, object_id, effect)`.
- `ArchivePolicy(criteria_type, criteria_id, days_to_archive)`.
- `MemoryStatusHistory(memory_id, changed_by, old_state, new_state, changed_at)`.
- `MemoryAccessLog(memory_id, app_id, accessed_at, access_type, metadata)`.

**MCP tools.** Source: [M1 openmemory/api/app/mcp_server.py L64-430](https://github.com/mem0ai/mem0/blob/144627c4ce5bc4db6acac17cbd158065f2b27a8d/openmemory/api/app/mcp_server.py#L64).
- `add_memories(text, infer=True)`. Description: "Add a new memory. This method is called everytime the user informs anything about themselves, their preferences, or anything that has any relevant information which can be useful in the future conversation…"
- `search_memory(query)`. Description: "This method is called EVERYTIME the user asks anything."
- `list_memories`, `delete_memories(memory_ids)` and `delete_all_memories`.
- `user_id` and `client_name` travel in `contextvars` set from the route `@mcp_router.get("/{client_name}/sse/{user_id}")`, or `/{client_name}/http/{user_id}` (L435-511).
- `get_user_and_app` is "Get or create both user and their app" ([utils/db.py L29-33](https://github.com/mem0ai/mem0/blob/144627c4ce5bc4db6acac17cbd158065f2b27a8d/openmemory/api/app/utils/db.py#L29)).
- add refuses when the app is paused: "App {name} is currently paused on OpenMemory. Cannot create new memories." (L86-87).

**Permission check, `check_memory_access_permissions`.** The memory must be `active`, the app must exist and be `is_active`, and then `get_accessible_memory_ids` is applied ([M1 app/utils/permissions.py](https://github.com/mem0ai/mem0/blob/144627c4ce5bc4db6acac17cbd158065f2b27a8d/openmemory/api/app/utils/permissions.py)). The ACL semantics:
- no rules → `None` (all accessible);
- allow with null object → all;
- deny with null object → `set()`;
- otherwise allowed minus denied ([M1 app/routers/memories.py L58-95](https://github.com/mem0ai/mem0/blob/144627c4ce5bc4db6acac17cbd158065f2b27a8d/openmemory/api/app/routers/memories.py#L58)).

**`search_memory` bypasses Mem0's search pipeline.** Source: [M1 mcp_server.py L160-215](https://github.com/mem0ai/mem0/blob/144627c4ce5bc4db6acac17cbd158065f2b27a8d/openmemory/api/app/mcp_server.py#L160).
- It loads *all* of the user's Memory rows from SQL and computes accessible IDs in Python.
- It then calls `memory_client.vector_store.search(..., limit=10, filters={"user_id": uid})`. This is raw vector search: no reranker, no graph, no threshold.
- It post-filters with `allowed = set(...) if accessible_memory_ids else None; if allowed and (h.id not in allowed): continue`.
- Each returned hit writes a `MemoryAccessLog(access_type="search", metadata={query, score, hash})`.

**Auto-categorisation.** Source: [M1 app/utils/categorization.py](https://github.com/mem0ai/mem0/blob/144627c4ce5bc4db6acac17cbd158065f2b27a8d/openmemory/api/app/utils/categorization.py); [models.py L185-243](https://github.com/mem0ai/mem0/blob/144627c4ce5bc4db6acac17cbd158065f2b27a8d/openmemory/api/app/models.py#L185).
- `openai_client.beta.chat.completions.parse(model="gpt-4o-mini", ..., response_format=MemoryCategories, temperature=0)`, with tenacity retry ×3.
- It is triggered by SQLAlchemy `after_insert` and `after_update` listeners on `Memory`.
- The prompt lists 20 categories (Personal, Relationships, Preferences, Health, Travel, Work, … Goals) and adds "Feel free to create new categories based on the memory" ([app/utils/prompts.py](https://github.com/mem0ai/mem0/blob/144627c4ce5bc4db6acac17cbd158065f2b27a8d/openmemory/api/app/utils/prompts.py)).

### Inferences
- **Permission-bypass bug, from reading the code (not tested).** Suppose an app has a "deny all" rule, or every memory is paused or archived. Then `accessible_memory_ids` is an empty list, so `allowed` becomes `None`, and the `if allowed and …` filter is skipped. **Every vector hit is returned.** A local reimplementation must treat "empty set" and "no restriction" differently.
- There is no authentication, and any client can claim any `user_id`. That is acceptable only on localhost. The design is that every connected AI tool (Claude, Cursor, …) shares one memory pool, while the access log gives per-app provenance. That is a useful UX pattern for Relic: "which app read/wrote this memory".
- A hard-coded OpenAI categoriser means OpenMemory was never fully local, even when a local LLM was configured for mem0.
- Loading every memory row on every search is O(N) and will not scale.

### Gaps
- I did not inspect `openmemory/ui` or the backup router in depth. I could not determine whether `ArchivePolicy` is actually enforced by any scheduler; I found no grep hit for a job using it, but did not search exhaustively.

---

## Q6. Procedural memory in Mem0

### Takeaway
Mem0's "procedural memory" is not learned skills. It is a single LLM call that writes a verbatim, step-by-step **execution-history summary** of an agent run, stored as one memory. It requires `agent_id` and `memory_type="procedural_memory"`. At HEAD it is marked for removal.

### Cited Findings
- `PROCEDURAL_MEMORY_SYSTEM_PROMPT`: "You are a memory summarization system that records and preserves the complete interaction history between a human and an AI agent … **Every output produced by the agent must be recorded verbatim as part of the summary.**" The required structure is: Task Objective, Progress Status, then numbered steps with Agent Action, Action Result ("Mandatory, Unmodified"), Key Findings, Navigation History, Errors & Challenges, Current Context ([M2 prompts.py L326-404](https://github.com/mem0ai/mem0/blob/0724291bd864cf807e88ee8981c8226644e8fb42/mem0/configs/prompts.py#L326)).
- The code comment reads "# TODO: Remove procedural-memory support in a future breaking release." Procedural memory is invoked only when `agent_id is not None and memory_type == MemoryType.PROCEDURAL.value` ([M2 main.py ~L848-860](https://github.com/mem0ai/mem0/blob/0724291bd864cf807e88ee8981c8226644e8fb42/mem0/memory/main.py#L848); `_create_procedural_memory` at [L2007](https://github.com/mem0ai/mem0/blob/0724291bd864cf807e88ee8981c8226644e8fb42/mem0/memory/main.py#L2007)).

### Inferences
- This is effectively context compaction for browser and tool agents, not something a personal-memory app needs. LangMem's prompt optimisation (Q8) is the closer analogue of "procedural memory" in the cognitive-science sense.

### Gaps
- None material.

---

## Q7. LangMem: semantic, episodic and procedural memory; managers and tools

### Takeaway
LangMem is a thin, schema-agnostic layer over LangGraph's `BaseStore` and the `trustcall` extractor. Its pieces:
- **Memory manager:** an LLM that emits parallel tool calls to insert or JSON-patch-update Pydantic memory objects, with deletes off by default.
- **Optional multi-step consolidation:** up to `max_steps`, ending with a `Done` tool.
- **Store manager:** retrieves the existing memories to show the model, using either LLM-generated "hypothetical memory" queries or dilated windows of recent messages.
- **Agent tools:** `manage_memory` and `search_memory` for hot-path use.
- **Debounced background executor:** the "reflection" component.

"Episodic" and "semantic" are just different Pydantic schemas passed to the same manager. There is no separate episodic engine.

### Cited Findings

**Default instructions `_MEMORY_INSTRUCTIONS`.** Verbatim excerpts: "You are a long-term memory manager maintaining a core store of semantic, procedural, and episodic memory … 1. **Extract & Contextualize** … Caveat uncertain or suppositional information with confidence levels (p(x)) and reasoning … 2. **Compare & Update** … Consolidate and compress redundant memories … strengthen based on reliability and recency … Remove incorrect or redundant memories while maintaining internal consistency 3. **Synthesize & Reason** … using deduction, induction, and abduction … Prioritize retention of surprising (pattern deviation) and persistent (frequently reinforced) information, ensuring nothing worth remembering is forgotten and nothing false is remembered." ([LM src/langmem/knowledge/extraction.py L185-207](https://github.com/langchain-ai/langmem/blob/48e3c11f5bb527282c7d5339c6a87a0b35abccfc/src/langmem/knowledge/extraction.py#L185)).

**Default schema `Memory(content: str)`.** Docstring: "Call this tool once for each new memory you want to record. Use multi-tool calling to record multiple new memories." Field description: "The memory as a well-written, standalone episode/fact/note/preference/etc." ([extraction.py L86-93](https://github.com/langchain-ai/langmem/blob/48e3c11f5bb527282c7d5339c6a87a0b35abccfc/src/langmem/knowledge/extraction.py#L86)).

**`MemoryManager`.** Source: [extraction.py L217-535](https://github.com/langchain-ai/langmem/blob/48e3c11f5bb527282c7d5339c6a87a0b35abccfc/src/langmem/knowledge/extraction.py#L217).
- Defaults: `enable_inserts=True`, `enable_updates=True`, `enable_deletes=False`, `max_steps=1`.
- It uses `trustcall.create_extractor(model, tools=schemas, enable_inserts, enable_updates, enable_deletes, existing_schema_policy=False)`. From step 2 onward a `Done` tool is added ("Only call this tool once you are done forming & consolidating memories").
- The user message is `"{instructions}\n\nEnrich, prune, and organize memories based on any new information. If an existing memory is incorrect or outdated, update it based on the new information. All operations must be done in single parallel multi-tool call. Avoid duplicate extractions. <session_{uuid}>…</session_{uuid}>"`, with the system message "You are a memory subroutine for an AI." (L457-478).
- Deletes are `RemoveDoc(json_doc_id)` objects.

**`MemoryStoreManager` / `create_memory_store_manager`.** Source: [extraction.py L825-1140](https://github.com/langchain-ai/langmem/blob/48e3c11f5bb527282c7d5339c6a87a0b35abccfc/src/langmem/knowledge/extraction.py#L832); [utils.py L103-119](https://github.com/langchain-ai/langmem/blob/48e3c11f5bb527282c7d5339c6a87a0b35abccfc/src/langmem/utils.py#L103).
- Defaults: `namespace=("memories","{langgraph_user_id}")`, `query_limit=5`, an optional `query_model`, and optional `phases`.
- Retrieval of existing memories, two modes:
  - **With `query_model`:** the model must call a search tool whose instructions say "Queries should be formatted as hypothetical memories that would be relevant to the current conversation" (a HyDE-style query).
  - **Without it:** `get_dialated_windows(messages, query_limit // 4)` searches the store with the last 1, 2, 4, … messages as queries.
- Results are merged, sorted by score and cut to `query_limit`. Stable IDs are `uuid5(NAMESPACE_DNS, str((*namespace, key)))`.
- After the manager runs, extra "phases" can run consolidation. The default phase instructions are "You are a memory manager. Deduplicate, consolidate, and enrich these memories.", with deletes enabled (L1010-1022).
- Writes are `store.aput` and deletes `store.adelete`, gathered concurrently (L1133-1134).

**Agent tools.** Source: [LM knowledge/tools.py L26-340](https://github.com/langchain-ai/langmem/blob/48e3c11f5bb527282c7d5339c6a87a0b35abccfc/src/langmem/knowledge/tools.py#L26).
- `create_manage_memory_tool(namespace, instructions=..., schema=str, actions_permitted=("create","update","delete"))`.
- Default instructions: "Proactively call this tool when you: 1. Identify a new USER preference. 2. Receive an explicit USER request to remember something or otherwise alter your behavior. 3. Are working and want to record important context. 4. Identify that an existing MEMORY is incorrect or outdated."
- The user-profile example restricts it to `actions_permitted=["create","update"]`.

**Episodic memory is a user-defined schema.** The docs example is `class Episode(BaseModel): observation, thoughts, action, result`, with the docstring "Write the episode from the perspective of the agent within it. Use the benefit of hindsight to record the memory, saving the agent's key internal thought process so it can learn over time." ([LM docs/docs/guides/extract_episodic_memories.md L19-30](https://github.com/langchain-ai/langmem/blob/48e3c11f5bb527282c7d5339c6a87a0b35abccfc/docs/docs/guides/extract_episodic_memories.md#L19); [conceptual_guide.md L192-205](https://github.com/langchain-ai/langmem/blob/48e3c11f5bb527282c7d5339c6a87a0b35abccfc/docs/docs/concepts/conceptual_guide.md#L192)).

**Background reflection (`ReflectionExecutor`).** Source: [LM src/langmem/reflection.py L143-430](https://github.com/langchain-ai/langmem/blob/48e3c11f5bb527282c7d5339c6a87a0b35abccfc/src/langmem/reflection.py#L254).
- `LocalReflectionExecutor` uses a `queue.PriorityQueue` keyed on `time.time() + after_seconds` and a non-daemon worker thread.
- `submit(payload, after_seconds=0, thread_id=...)` **cancels any pending task for the same thread_id** (`existing.cancel_event.set(); existing.future.cancel()`). This is debouncing: only the latest conversation state is processed after the user goes quiet.
- `RemoteReflectionExecutor` schedules the same thing as a LangGraph Platform run.

**Short-term memory.** `summarize_messages` / `SummarizationNode` take `max_tokens`, `max_tokens_before_summary` and `max_summary_tokens`, and raise an error if `max_summary_tokens >= max_tokens` ([LM short_term/summarization.py L92-116](https://github.com/langchain-ai/langmem/blob/48e3c11f5bb527282c7d5339c6a87a0b35abccfc/src/langmem/short_term/summarization.py#L92)).

**Dependencies and maturity.**
- Dependencies are langchain, langchain-core, langchain-openai, langchain-anthropic, **trustcall**, langgraph (`>=0.6.0,<2`), langsmith and langgraph-checkpoint ([LM pyproject.toml L8-17](https://github.com/langchain-ai/langmem/blob/48e3c11f5bb527282c7d5339c6a87a0b35abccfc/pyproject.toml#L8)).
- The version is 0.0.30, pre-1.0 ([rywalker.com review via search](https://rywalker.com/research/langmem)).
- The launch blog frames the three types as "Semantic Facts & Knowledge … Episodic Past Experiences … Procedural System Behavior" ([LangChain blog](https://blog.langchain.com/langmem-sdk-launch)).

### Inferences
- LangMem has **no built-in ranking, dedup heuristics, history table or entity index**. Retrieval is whatever `BaseStore.search` provides, typically embedding similarity. Conflict handling relies entirely on the LLM patching or removing docs it can see; only the top-5 are shown by default.
- Its key transferable ideas for Relic:
  1. Debounced background consolidation per thread (cheap to build on-device with a timer).
  2. HyDE-style "hypothetical memory" queries.
  3. Dilated recent-message windows as retrieval queries, with no LLM needed.
  4. Typed schemas for episodes and profiles, with update-in-place for a single "profile" doc.
  5. Multi-phase consolidation passes, run when idle or charging.
- Its reliance on parallel multi-tool calling and JSON-patch updates via trustcall is the hardest part for small local models.

### Gaps
- I did not trace trustcall's internal JSON-patch prompt, since trustcall is a separate repo that was not cloned.
- No LangMem benchmark numbers were found.

---

## Q8. LangMem prompt optimisation (procedural memory)

### Takeaway
LangMem's "procedural memory" rewrites the agent's *system prompt* from trajectories and feedback. There are three strategies:
- `gradient`: critique, then recommend, then apply a minimal edit; 1-5 reflection steps with think and critique tools.
- `metaprompt`: a single meta-prompt.
- `prompt_memory`: a single-pass reflection.

A multi-prompt optimiser first classifies which prompts in a pipeline need updating.

### Cited Findings
- `KINDS = Literal["gradient","metaprompt","prompt_memory"]`, with gradient as the default. The config accepts `max_reflection_steps` and `min_reflection_steps` ([LM prompts/optimization.py L23-60, L116-144](https://github.com/langchain-ai/langmem/blob/48e3c11f5bb527282c7d5339c6a87a0b35abccfc/src/langmem/prompts/optimization.py#L23)). The module defaults are `DEFAULT_MAX_REFLECTION_STEPS = 5` and `DEFAULT_MIN_REFLECTION_STEPS = 1` ([gradient.py L13-14](https://github.com/langchain-ai/langmem/blob/48e3c11f5bb527282c7d5339c6a87a0b35abccfc/src/langmem/prompts/gradient.py#L13)).
- `DEFAULT_GRADIENT_PROMPT`: "You are reviewing the performance of an AI assistant in a given interaction … If the prompt seems to do well, then no further action is needed. We ONLY recommend updates if there is evidence of failures. When failures occur, we want to recommend the minimal required changes … Identify which failure mode(s) best describe the issues (examples: style mismatch, unclear or incomplete instructions, flawed logic or reasoning, hallucination, etc.) … Otherwise, mark `warrants_adjustment` as False". The tools are `think`, `critique` and `recommend(warrants_adjustment, hypotheses, full_recommendations)` ([gradient.py L16-65, L130-145](https://github.com/langchain-ai/langmem/blob/48e3c11f5bb527282c7d5339c6a87a0b35abccfc/src/langmem/prompts/gradient.py#L16)).
- `DEFAULT_GRADIENT_METAPROMPT`: "You are optimizing a prompt … We hypothesize the current prompt underperforms for these reasons: <hypotheses> … Respond with the updated prompt. Remember to ONLY make changes that are clearly necessary. Aim to be minimally invasive" ([gradient.py L67-85](https://github.com/langchain-ai/langmem/blob/48e3c11f5bb527282c7d5339c6a87a0b35abccfc/src/langmem/prompts/gradient.py#L67)).
- `DEFAULT_METAPROMPT`: "You are helping an AI assistant learn by optimizing its prompt … Retain any f-string variables in the existing prompt exactly as they are … consider synthetic few-shot examples for style or clarifying decision boundaries" ([metaprompt.py L27-55](https://github.com/langchain-ai/langmem/blob/48e3c11f5bb527282c7d5339c6a87a0b35abccfc/src/langmem/prompts/metaprompt.py#L27)).
- The multi-prompt optimiser uses a `Classify(reasoning, which_prompts)` step: "Analyze the following trajectories and decide which prompts …" ([optimization.py L317-345, L404-430](https://github.com/langchain-ai/langmem/blob/48e3c11f5bb527282c7d5339c6a87a0b35abccfc/src/langmem/prompts/optimization.py#L317)).
- The docs examples use `"anthropic:claude-3-5-sonnet-latest"` ([optimization.py L195](https://github.com/langchain-ai/langmem/blob/48e3c11f5bb527282c7d5339c6a87a0b35abccfc/src/langmem/prompts/optimization.py#L195)).

### Inferences
- For Relic, "learned instructions" (for example "user prefers terse answers") could be maintained as a small editable prompt section updated by a metaprompt pass. The pass should run rarely, in the background, and preferably with user review, because a bad rewrite silently degrades every future answer. This step needs a strong model; it is the least suitable for a 1-4B local model.

### Gaps
- No published accuracy evaluation of LangMem's optimisers was found.

---

## Q9. Which steps could run on small local models, and weaknesses found in code

### Takeaway
On-device tiers:
- **No LLM needed:** embedding, BM25 and FTS, spaCy-style NER and lemmatisation, the hybrid scoring formula, hash and cosine dedup, entity linking, debounce scheduling, history logging. All of these are deterministic.
- **A small model (~3-8B) with JSON mode / grammar-constrained decoding:** fact extraction (M1 style, short prompt) and categorisation.
- **Strong models needed:** conflict and supersession decisions (M1 UPDATE/DELETE), graph triple extraction with tool calls, M2's 10k-token exhaustive extraction prompt, multi-step consolidation, and prompt optimisation.

### Cited Findings: what needs which model
- M2 uses one LLM call per add and zero at search time; everything else is spaCy and embeddings ([M2 main.py L881-1220, L1642-1745](https://github.com/mem0ai/mem0/blob/0724291bd864cf807e88ee8981c8226644e8fb42/mem0/memory/main.py#L881)).
- spaCy is optional: "Without it, Mem0 still works but falls back to semantic-only search". The `[nlp]` extra supports Python 3.10-3.12 only ([M2 migration doc](https://github.com/mem0ai/mem0/blob/0724291bd864cf807e88ee8981c8226644e8fb42/docs/migration/oss-v2-to-v3.mdx)).
- M1 makes 2 LLM calls per add, plus 3 or more for the graph and 1 per search for graph entity extraction ([M1 main.py](https://github.com/mem0ai/mem0/blob/144627c4ce5bc4db6acac17cbd158065f2b27a8d/mem0/memory/main.py#L475); [graph_memory.py](https://github.com/mem0ai/mem0/blob/144627c4ce5bc4db6acac17cbd158065f2b27a8d/mem0/memory/graph_memory.py#L76)).
- Even gpt-4.1-nano produced frequent JSON parse errors in UPDATE and DELETE ([arXiv 2609.10413 via search](https://arxiv.org/pdf/2609.10413)).
- Mem0 already ships Ollama, LM Studio and vLLM LLM providers, and FastEmbed and HuggingFace embedders ([M2 mem0/CLAUDE.md provider table](https://github.com/mem0ai/mem0/blob/0724291bd864cf807e88ee8981c8226644e8fb42/mem0/CLAUDE.md)).

### Cited Findings: weaknesses found in code (all from static reading; none were run)
1. **M2 discards the LLM's `linked_memory_ids`** and passes integer IDs while the prompt asks for UUIDs. The advertised contradiction and continuation linking therefore has no effect in OSS ([M2 main.py ~L1035-1060](https://github.com/mem0ai/mem0/blob/0724291bd864cf807e88ee8981c8226644e8fb42/mem0/memory/main.py#L1035); [prompts.py L46](https://github.com/mem0ai/mem0/blob/0724291bd864cf807e88ee8981c8226644e8fb42/mem0/configs/prompts.py#L468)).
2. **M2 OSS never passes Summary, Recently Extracted Memories or Observation Date**, although the prompt relies on them. Relative dates are resolved against "today", which is wrong for imported or backfilled history ([M2 prompts.py L1016-1062](https://github.com/mem0ai/mem0/blob/0724291bd864cf807e88ee8981c8226644e8fb42/mem0/configs/prompts.py#L1016)).
3. **The existing-memory lookup in M2 is one embedding of the entire message batch with top_k=10.** In long multi-topic batches, relevant old memories for minor topics will be missed, so dedup and linking fail. M1 did this per fact.
4. **Dedup is MD5 of the exact text.** Paraphrased duplicates survive, and the prompt's "When in doubt, extract" pushes towards over-extraction ([M2 main.py L960-985](https://github.com/mem0ai/mem0/blob/0724291bd864cf807e88ee8981c8226644e8fb42/mem0/memory/main.py#L960)).
5. **There is no supersession, recency or decay signal in ranking** ([scoring.py](https://github.com/mem0ai/mem0/blob/0724291bd864cf807e88ee8981c8226644e8fb42/mem0/utils/scoring.py#L60)). Stale preferences rank equal to current ones.
6. **BM25 and entity signals cannot surface memories that semantic search missed.** Candidates come only from the semantic list ([main.py L1690-1715](https://github.com/mem0ai/mem0/blob/0724291bd864cf807e88ee8981c8226644e8fb42/mem0/memory/main.py#L1690)). The BM25 keyword list is used only for scores.
7. **The `max_possible` normaliser changes per query**, depending on whether *any* BM25 or entity hit exists. Absolute scores are not comparable across queries, and a fixed `threshold` gates only the semantic component.
8. **M1's fact prompt hard-codes the date at import time** via an f-string. It also contains an instruction to tell users their data came "from publicly available sources on internet", a questionable deception instruction ([M1 prompts.py L14-60](https://github.com/mem0ai/mem0/blob/144627c4ce5bc4db6acac17cbd158065f2b27a8d/mem0/configs/prompts.py#L14)).
9. **M1 DELETE is a hard delete from the vector store**, with only an SQLite history trace ([M1 main.py L1340](https://github.com/mem0ai/mem0/blob/144627c4ce5bc4db6acac17cbd158065f2b27a8d/mem0/memory/main.py#L1340)).
10. **OpenMemory has an empty-ACL bypass, no auth, O(N) permission checks per search, and a hard-coded OpenAI categoriser** (Q5).
11. **The default Qdrant config uses `path="/tmp/qdrant"` with `on_disk=False`**, which is volatile. The spaCy model is English-only.
12. **Entity-linking failures are swallowed** with `logger.warning`. Entity-store updates read-modify-write `linked_memory_ids` without locking, so concurrent adds can lose links ([M2 main.py L1160-1200](https://github.com/mem0ai/mem0/blob/0724291bd864cf807e88ee8981c8226644e8fb42/mem0/memory/main.py#L1160)).
13. **Telemetry:** `capture_event("mem0.add" / "mem0.search", …)` is called on every operation ([M2 main.py](https://github.com/mem0ai/mem0/blob/0724291bd864cf807e88ee8981c8226644e8fb42/mem0/memory/main.py#L1210); `mem0/memory/telemetry.py`, 241 lines). A privacy-first app must strip this. There is also a 1,667-line `notices.py` of upsell notices pointing to the Platform for temporal features.
14. **LangMem:** no history or audit log, deletes are off by default, retrieval is capped at `query_limit=5`, quality depends entirely on the model's parallel tool-calling and JSON-patch reliability, and the project is pre-1.0 ([LM extraction.py](https://github.com/langchain-ai/langmem/blob/48e3c11f5bb527282c7d5339c6a87a0b35abccfc/src/langmem/knowledge/extraction.py#L832)).

### Inferences: suggested Relic recipe, synthesised from both codebases

**Write path (debounced, background, LangMem-style):**
1. Run a small local LLM with a *short* extraction prompt and grammar-constrained JSON. Inputs:
   - the last ~10 messages;
   - a stored profile summary;
   - the top-k existing memories retrieved *per fact or topic*;
   - an explicit observation date.
2. Apply the deterministic steps: embed, hash plus cosine ≥ 0.95 dedup, spaCy or a multilingual NER substitute for entity links, and FTS5 lemmas.
3. Append an ADD event to a history table.
4. When candidate neighbours exceed a similarity band, run a cheap second small-LLM yes/no "does new fact supersede old?" check. Store `superseded_by` rather than deleting. M1's graph used `valid=false` in the same way.

**Read path (no LLM):** semantic over-fetch → FTS5 BM25 sigmoid → entity boost → add a recency or supersession penalty → top-k.

**Idle or charging jobs:** consolidation phases ("Deduplicate, consolidate, and enrich") and optional prompt or profile rewriting, using a larger model or user review.

### Gaps
- I did not measure local-model quality on these prompts. The tier assignments are inferences from prompt length and complexity and from the cited JSON-error report, not benchmarks.
- I did not inspect `mem0-ts` (the TypeScript SDK), which might matter if Relic is JS or React Native. The migration doc notes the TS payload key is `textLemmatized`, so collections are not cross-compatible between the Python and TS SDKs.
