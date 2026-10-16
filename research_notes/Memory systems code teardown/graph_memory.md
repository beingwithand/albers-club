# Graph/Temporal Memory Systems: Code-Level Teardown (Graphiti/Zep, Cognee, HippoRAG 2, LightRAG, MS GraphRAG/LazyGraphRAG)

Method: shallow clones (read-only, nothing installed or executed) on 2026-10-16. Commits read:
- getzep/graphiti @ `d50741d` (graphiti-core 0.31.1, Apache-2.0)
- topoteretes/cognee @ `37f788b` (Apache-2.0)
- OSU-NLP-Group/HippoRAG @ `d5c8329` (MIT)
- HKUDS/LightRAG @ `aaebfe1` (MIT)
- microsoft/graphrag @ `5faaaf4` (MIT)

Short GitHub links below use these commits. Line numbers refer to those commits. arXiv and the Zep/HF pages could not be fetched from this environment, so paper claims come from search-result snippets and are marked as such.

## Q1. How each system builds the graph: schemas, prompts, pipeline

### Takeaway
Graphiti is the only one of the five with a real bi-temporal edge model (valid_at/invalid_at plus created_at/expired_at) and an LLM-judged contradiction step. Cognee, LightRAG and GraphRAG build "entity + description" graphs keyed by normalized name. HippoRAG 2 builds a schemaless OpenIE triple graph with passage nodes and uses embedding "synonymy" edges instead of merging entities. For a lifelog, Graphiti's data model is the one to copy. HippoRAG's retrieval (PPR) is the cheapest graph-retrieval trick to copy.

### Cited Findings

**Graphiti (Zep): schema**
- The base `Edge` has `uuid`, `group_id` ("partition of the graph"), `source_node_uuid`, `target_node_uuid` and `created_at`. `EntityEdge` adds `name` (the relation type), `fact` (a natural-language sentence), `fact_embedding`, `episodes` (a list of source episode uuids), `expired_at`, `valid_at`, `invalid_at`, `reference_time` and `attributes` (a dict) — [graphiti edges.py L49-54, L263-288](https://github.com/getzep/graphiti/blob/d50741d/graphiti_core/edges.py#L263-L288)
- The node types are `EpisodicNode` (`source_description`, raw `content`, `valid_at` = when the event occurred, `entity_edges`, `episode_metadata`), `EntityNode` (`name_embedding`, `summary` "regional summary of surrounding edges", `attributes`), `CommunityNode` (`summary`) and `SagaNode` (summary over an episode chain, with `first_episode_uuid`/`last_episode_uuid`/`last_summarized_at`). Every node has `group_id`, `labels` and `created_at` — [graphiti nodes.py L93-98, L318-329, L499-502, L727-729, L907-916](https://github.com/getzep/graphiti/blob/d50741d/graphiti_core/nodes.py#L318-L329)
- The other edge classes are `EpisodicEdge` (MENTIONS, episode→entity), `CommunityEdge`, `HasEpisodeEdge` and `NextEpisodeEdge` (episode chains/sagas) — [graphiti edges.py L143, L580, L694, L827](https://github.com/getzep/graphiti/blob/d50741d/graphiti_core/edges.py#L580)
- The episode types are `message`, `json` and `text`. `add_episode(name, episode_body, source_description, reference_time, source, group_id, entity_types, excluded_entity_types, previous_episode_uuids, edge_types, …)` — [graphiti graphiti.py L1332-1345](https://github.com/getzep/graphiti/blob/d50741d/graphiti_core/graphiti.py#L1332-L1345); [nodes.py L54-70](https://github.com/getzep/graphiti/blob/d50741d/graphiti_core/nodes.py#L54-L70)
- The paper's framing, per a search snippet: three subgraph tiers (episodic, semantic entity, community) and two timelines (T = event chronology, T′ = ingestion order). Older conflicting edges get an invalidation timestamp instead of being deleted. This matches the code fields above — [Zep blog/paper summary](https://blog.getzep.com/zep-a-temporal-knowledge-graph-architecture-for-agent-memory) (could not fetch; snippet only)

**Graphiti pipeline (`add_episode`)**
1. Retrieve the previous episodes (`EPISODE_WINDOW_LEN = 3`) as context.
2. `extract_nodes`, then `resolve_extracted_nodes`.
3. `_extract_and_resolve_edges`, in parallel with `extract_attributes_from_nodes` (summaries).
4. `_process_episode_data` (episodic MENTIONS edges, saga).
5. Optionally, community update.
— [graphiti.py ~L1420-1560](https://github.com/getzep/graphiti/blob/d50741d/graphiti_core/graphiti.py#L1420-L1560); [graph_data_operations.py L29](https://github.com/getzep/graphiti/blob/d50741d/graphiti_core/utils/maintenance/graph_data_operations.py#L29)

`add_episode_bulk` has `use_combined_extraction=True`: "one combined node-and-edge LLM call per episode" — [graphiti.py L1586-1632](https://github.com/getzep/graphiti/blob/d50741d/graphiti_core/graphiti.py#L1586-L1632); [combined_extraction.py](https://github.com/getzep/graphiti/blob/d50741d/graphiti_core/utils/maintenance/combined_extraction.py)

**Graphiti entity-extraction prompt (`extract_message`), quoted excerpts**
- System: "You are an entity extraction specialist for conversational messages. NEVER extract abstract concepts, feelings, or generic words."
- Rules: "Always extract the speaker (the part before the colon `:` in each dialogue line) as the first entity node."
- Rules: "Bare relational or kinship terms (dad, mom, … friend, boss …) … qualify them with the possessor: extract "Nisha's dad" not "dad"."
- Rules: "Do NOT extract dates, times, or other temporal information — these will be handled separately."
- Rules: "When in doubt, do NOT extract."
- Rules: "Exclude entities mentioned only in the PREVIOUS MESSAGES (they are for context only)."
— [graphiti prompts/extract_nodes.py L84-~200](https://github.com/getzep/graphiti/blob/d50741d/graphiti_core/prompts/extract_nodes.py#L84)

**Graphiti edge/fact-extraction prompt (`extract_edges.edge`), quoted excerpts**
- System: "You are an expert fact extractor that extracts fact triples from text. 1. Extracted fact triples should also be extracted with relevant date information…"
- Rules: "`source_entity_name` and `target_entity_name` must use only the `name` values from the ENTITIES list."
- Rules: the relation_type is either a provided fact type or is derived "in SCREAMING_SNAKE_CASE (e.g., WORKS_AT, LIVES_IN…)".
- Rules: "The `fact` MUST preserve all specific details … NEVER generalize "Gamecube" to "gaming console"."
- DATETIME RULES: "If the fact is ongoing (present tense), set `valid_at` to the timestamp of the episode…"
- DATETIME RULES: "If the fact is a future-tense plan … Do NOT set `valid_at` to the future occurrence date."
- DATETIME RULES: "Use a future date as `invalid_at` only when the fact describes an ongoing state that ends then."
- DATETIME RULES: "If only a year is mentioned, use January 1st at 00:00:00."
— [graphiti prompts/extract_edges.py L95-198](https://github.com/getzep/graphiti/blob/d50741d/graphiti_core/prompts/extract_edges.py#L95-L198)

A deterministic regex post-pass (`normalize_future_temporal_bounds`) does two things. It clamps `valid_at` to reference_time for "plans to / will / scheduled to / 'll" facts. It drops a future `invalid_at` that is only a deadline ("by / due by") unless there is ongoing-state-end language ("until / expires / no longer") — [graphiti temporal_edge_utils.py L17-96](https://github.com/getzep/graphiti/blob/d50741d/graphiti_core/utils/maintenance/temporal_edge_utils.py)

**Communities in Graphiti and GraphRAG**
- Graphiti uses label propagation (`def label_propagation(projection)`), not Leiden — [graphiti community_operations.py L96](https://github.com/getzep/graphiti/blob/d50741d/graphiti_core/utils/maintenance/community_operations.py#L96)
- GraphRAG uses `hierarchical_leiden` with defaults `max_cluster_size=10`, `use_lcc=True` and `seed=0xDEADBEEF` — [graphrag cluster_graph.py L11, L86](https://github.com/microsoft/graphrag/blob/5faaaf4/packages/graphrag/graphrag/index/operations/cluster_graph.py); [defaults.py L68-73](https://github.com/microsoft/graphrag/blob/5faaaf4/packages/graphrag/graphrag/config/defaults.py#L68-L73)
- GraphRAG community report prompt (excerpt): "Write a comprehensive report of a community … TITLE … SUMMARY … IMPACT SEVERITY RATING: a float score between 0-10 … DETAILED FINDINGS: A list of 5-10 key insights", returned as JSON — [graphrag prompts/index/community_report.py](https://github.com/microsoft/graphrag/blob/5faaaf4/packages/graphrag/graphrag/prompts/index/community_report.py)

**HippoRAG 2**
- NER prompt: "Your task is to extract named entities from the given paragraph. Respond with a JSON list of entities." It is one-shot (the Radio City example), and dates are included as entities — [HippoRAG prompts/templates/ner.py](https://github.com/OSU-NLP-Group/HippoRAG/blob/d5c8329/src/hipporag/prompts/templates/ner.py)
- Triple prompt: "construct an RDF (Resource Description Framework) graph from the given passages and named entity lists… Each triple should contain at least one, but preferably two, of the named entities… Clearly resolve pronouns" — [triple_extraction.py](https://github.com/OSU-NLP-Group/HippoRAG/blob/d5c8329/src/hipporag/prompts/templates/triple_extraction.py)
- Graph build: fact edges between subject and object phrase nodes (weight = co-occurrence count), passage↔entity edges (`add_passage_edges`), and synonymy edges via embedding KNN (`synonymy_edge_topk=2047`, `synonymy_edge_sim_threshold=0.8`, capped at 100 neighbours). Synonymy is computed incrementally, only for newly inserted phrase nodes. The graph is an igraph object — [HippoRAG.py L1179-1350](https://github.com/OSU-NLP-Group/HippoRAG/blob/d5c8329/src/hipporag/HippoRAG.py#L1179-L1350); [config_utils.py L160-174](https://github.com/OSU-NLP-Group/HippoRAG/blob/d5c8329/src/hipporag/utils/config_utils.py#L160-L174)
- Node ids are `compute_mdhash_id(phrase.lower(), prefix="entity-")`, so the only "merge" is exact lowercase string identity — [HippoRAG.py ~L2050](https://github.com/OSU-NLP-Group/HippoRAG/blob/d5c8329/src/hipporag/HippoRAG.py#L2040-L2060)
- Default models: `llm_name="gpt-4o-mini"` and `embedding_model_name="nvidia/NV-Embed-v2"` — [config_utils.py L18-20, L136-138](https://github.com/OSU-NLP-Group/HippoRAG/blob/d5c8329/src/hipporag/utils/config_utils.py#L18-L20)

**LightRAG**
- One extraction prompt emits delimited rows: `entity<|#|>name<|#|>type<|#|>description` and `relation<|#|>src<|#|>tgt<|#|>keywords<|#|>description`.
- It also says: "Treat all relationships as **undirected** unless explicitly stated otherwise."
- It sets "Output at most {max_total_records}" rows (default 100 records / 40 entities).
- It asks for "Ensure **consistent naming**" (title case) — the only cross-chunk dedup aid.
— [LightRAG prompt.py L14-126](https://github.com/HKUDS/LightRAG/blob/aaebfe1/lightrag/prompt.py#L56-L126); [constants.py L26-27](https://github.com/HKUDS/LightRAG/blob/aaebfe1/lightrag/constants.py#L26-L27)
- Merging: an entity with the same normalized name is merged by concatenating descriptions with `GRAPH_FIELD_SEP`. The LLM re-summarizes (map-reduce) only when the description count ≥ `DEFAULT_FORCE_LLM_SUMMARY_ON_MERGE = 8` or the token budget is exceeded — [operate.py L372-440, L2429](https://github.com/HKUDS/LightRAG/blob/aaebfe1/lightrag/operate.py#L372-L440); [constants.py L30](https://github.com/HKUDS/LightRAG/blob/aaebfe1/lightrag/constants.py#L30)
- Summary prompt "Conflict Handling": "first determine if these conflicts arise from multiple, distinct entities … that share the same name… If conflicts within a single entity … attempt to reconcile them or present both viewpoints with noted uncertainty." This is the only contradiction handling, and it is text-level with no timestamps — [prompt.py L297-329](https://github.com/HKUDS/LightRAG/blob/aaebfe1/lightrag/prompt.py#L297-L329)
- Gleaning: `DEFAULT_MAX_GLEANING = 1` (one extra "continue extraction" call per chunk) — [constants.py L17](https://github.com/HKUDS/LightRAG/blob/aaebfe1/lightrag/constants.py#L17)

**Cognee**
- Default `cognify` tasks:
  - `classify_documents` (no LLM)
  - `extract_chunks_from_documents` (no LLM)
  - `extract_graph_and_summarize` (LLM)
  - `add_data_points` (no LLM)
  - optional `record_provenance`
  — [cognee api/v1/cognify/cognify.py L610-650](https://github.com/topoteretes/cognee/blob/37f788b/cognee/api/v1/cognify/cognify.py#L610-L650)
- Graph prompt (excerpts): "Nodes represent entities and concepts. They're akin to Wikipedia nodes."
- Graph prompt: "A point in time is a node of type **"Timestamp"** … `YYYY`, `YYYY-MM`, `YYYY-MM-DD` … A period … is ONE Timestamp named `<start>/<end>`."
- Graph prompt: "use a `{verb}_at` relationship whose target is the Timestamp, e.g. `born_at`."
- Graph prompt: "Coreference Resolution … always use the most complete identifier."
- Time is therefore modeled as leaf Timestamp nodes, not as edge validity intervals.
— [cognee generate_graph_prompt.txt](https://github.com/topoteretes/cognee/blob/37f788b/cognee/infrastructure/llm/prompts/generate_graph_prompt.txt)
- The `Timestamp` DataPoint has `time_at` (epoch ms, lower bound), `time_until` (exclusive upper bound) and `precision` ∈ {year, month, day, second, span}. The overlap test is `time_at < window_end and time_until > window_start` — [cognee modules/engine/models/Timestamp.py](https://github.com/topoteretes/cognee/blob/37f788b/cognee/modules/engine/models/Timestamp.py)
- `Entity` has `name`, `is_a`, `description`, `relations`, `conflicts_reviewed_at` and metadata `{"index_fields": ["name"], "identity_fields": ["name"]}`, so its id is deterministic from the name — [cognee Entity.py](https://github.com/topoteretes/cognee/blob/37f788b/cognee/modules/engine/models/Entity.py)

### Inferences
- For Relic, Graphiti's split is the closest fit for lifelog "episodes" (a message, photo caption or email): Episodic node → MENTIONS → Entity, plus Entity–RELATES_TO(fact, valid_at, invalid_at, expired_at, episodes[])–Entity. The `episodes[]` provenance list on every fact gives you deletion and "why do you know this" for free.
- Cognee's Timestamp-node approach is weaker for state changes ("lives in X" → "lives in Y") because validity is not attached to the fact. It is good for event dating and time-window queries.

### Gaps
- I could not read the Zep paper PDF (arXiv blocked; blog/HF DNS failed), so the paper-vs-code differences are not verified line by line. The code has clearly evolved: combined extraction, a GLiNER2 option, identity properties, MinHash dedup and sagas are likely post-paper.

## Q2. Entity resolution across sources (same person on email / Instagram / Kakao)

### Takeaway
Only Graphiti has a layered resolver. It goes from configured identity properties, to exact normalized name, to MinHash/LSH fuzzy name (Jaccard ≥ 0.9, entropy-gated), to embedding candidate search, and only then to a batched LLM judge. Cognee has an offline embedding-cluster consolidation pass. HippoRAG and LightRAG merge on exact string only (HippoRAG adds soft synonymy edges). None of them resolve people by handle/email/phone out of the box. Graphiti's `identity_properties` hook is the place to plug that in.

### Cited Findings
- Graphiti deterministic constants: `_NAME_ENTROPY_THRESHOLD = 1.5`, `_MIN_NAME_LENGTH = 6`, `_MIN_TOKEN_COUNT = 2`, `_FUZZY_JACCARD_THRESHOLD = 0.9`, `_MINHASH_PERMUTATIONS = 32`, `_MINHASH_BAND_SIZE = 4`. Shingles are character 3-grams hashed with blake2b — [graphiti dedup_helpers.py L31-117](https://github.com/getzep/graphiti/blob/d50741d/graphiti_core/utils/maintenance/dedup_helpers.py#L31-L117)
- Order in `_resolve_with_similarity`:
  - An exact normalized name with exactly 1 match resolves immediately.
  - More than 1 match is "Ambiguous … Escalate to LLM".
  - A low-entropy or short name skips the fuzzy step and goes to the LLM.
  - Otherwise LSH buckets give candidates, best Jaccard ≥ 0.9 merges, and the rest go to the LLM.
  — [dedup_helpers.py L321-380](https://github.com/getzep/graphiti/blob/d50741d/graphiti_core/utils/maintenance/dedup_helpers.py#L321-L380)
- `_resolve_with_identity_properties` uses `identity_properties: dict[label, list[prop]]`. If all configured attributes (e.g. `email`) of a typed node are non-null and equal to a candidate's, it merges deterministically, choosing the oldest by `created_at` — [dedup_helpers.py L207-290](https://github.com/getzep/graphiti/blob/d50741d/graphiti_core/utils/maintenance/dedup_helpers.py#L207-L290)
- Candidate gathering combines identity results, exact-name results and `_semantic_candidate_search`: "Run direct cosine similarity search per extracted node without reranking", which embeds the node *name* — [node_operations.py L469-480, L585-615](https://github.com/getzep/graphiti/blob/d50741d/graphiti_core/utils/maintenance/node_operations.py#L585-L615)
- The LLM judge prompt (`dedupe_nodes.nodes`) is batched over all unresolved entities. It includes previous messages and the current message, and EXISTING ENTITIES with name, entity_types and summary.
  - Rules: "Entities should only be considered duplicates if they refer to the *same real-world object or concept*… NEVER mark entities as duplicates if: They are related but distinct."
  - Output per entity: `{id, name (best full name), duplicate_candidate_id or -1}`.
  - Examples include "NYC" → "New York City", and "Java" (language) ≠ "Java" (island).
  — [graphiti prompts/dedupe_nodes.py L118-180](https://github.com/getzep/graphiti/blob/d50741d/graphiti_core/prompts/dedupe_nodes.py#L118-L180); call site [node_operations.py L737-745](https://github.com/getzep/graphiti/blob/d50741d/graphiti_core/utils/maintenance/node_operations.py#L737-L745)
- There is also a `node_list` prompt for an offline group-by-UUID dedup pass that "synthesizes the summaries into a new short summary" — [dedupe_nodes.py L183-223](https://github.com/getzep/graphiti/blob/d50741d/graphiti_core/prompts/dedupe_nodes.py#L183-L223)
- Cognee: `generate_node_id = uuid5(NAMESPACE_OID, name.lower().replace(" ", "_").replace("'", ""))`, so identical normalized names collapse at write time — [cognee generate_node_id.py](https://github.com/topoteretes/cognee/blob/37f788b/cognee/infrastructure/engine/utils/generate_node_id.py)
  - Its `consolidate_entities` memify pipeline "embeds its name, and clusters near-duplicates by cosine similarity and/or normalized-name equality" (default `similarity_threshold: 0.85`, top-k neighbours).
  - It then re-points edges to a canonical node, unions descriptions, records `merged_from`, and deletes the duplicates. It supports `dry_run`.
  — [cognee tasks/memify/consolidate_entities.py L1-44, L98-176](https://github.com/topoteretes/cognee/blob/37f788b/cognee/tasks/memify/consolidate_entities.py)
- HippoRAG does not merge. Near-duplicate phrases are linked by synonymy edges (cosine ≥ 0.8) that PPR walks across — [HippoRAG.py L1278-1350](https://github.com/OSU-NLP-Group/HippoRAG/blob/d5c8329/src/hipporag/HippoRAG.py#L1278-L1350)
- LightRAG merges by normalized name only (`normalize_extracted_info`) and exposes manual `amerge_entities` / `aedit_entity` APIs — [LightRAG utils.py L5838](https://github.com/HKUDS/LightRAG/blob/aaebfe1/lightrag/utils.py#L5838); [lightrag.py L8121, L8303](https://github.com/HKUDS/LightRAG/blob/aaebfe1/lightrag/lightrag.py#L8303)
- Graphiti's extraction prompt qualifies kinship terms with the possessor ("Nisha's dad"). That avoids false merges of "dad" across users, but it creates a separate node from "Nisha's dad = Raj" unless a later episode links them — [extract_nodes.py](https://github.com/getzep/graphiti/blob/d50741d/graphiti_core/prompts/extract_nodes.py#L84)

### Inferences
- Recommended layered resolver for Relic, mirroring Graphiti:
  1. Hard identifiers first, with no LLM. Treat the contact book (phone/email/Kakao ID/IG handle) as identity properties and union them into a "Person" node. Source-native IDs beat any name heuristic.
  2. Exact normalized-name match, scoped by entity type.
  3. MinHash/Jaccard ≥ 0.9 with an entropy gate. This is pure CPU, easy to port to Swift/Kotlin, and cheap.
  4. Name-embedding kNN to produce candidates.
  5. A small on-device LLM judge only for ambiguous cases, using Graphiti's prompt with summaries.
  6. A periodic offline consolidation pass like Cognee's (cosine ≥ 0.85, dry-run first), with user confirmation for Person merges.
- Korean/romanized/nickname variants (e.g. "지원" vs "Jiweon" vs "jiwon_c") will defeat character-3-gram MinHash. Relic needs transliteration-aware normalization or alias tables. None of the repos handle this.
- Graphiti's identity merge requires *all* configured properties to be present and equal, and picks the oldest node. Multi-handle people need an alias set rather than one tuple key.

### Gaps
- None of the repos report precision/recall figures for entity resolution. I found no published per-step dedup accuracy.

## Q3. How contradictions invalidate old facts

### Takeaway
In Graphiti an LLM decides *whether* facts contradict, and deterministic interval logic decides *when*. The old edge gets `invalid_at = new.valid_at` and `expired_at = now`, and is never deleted. Cognee has a newer batch "review_conflicts" memify stage that writes `FactConflict` records (time_varying vs fixed, resolved/unresolved) rather than invalidating edges. LightRAG only reconciles inside description summaries. HippoRAG and GraphRAG have no contradiction handling.

### Cited Findings
- Graphiti `dedupe_edges.resolve_edge` prompt. System: "NEVER mark facts as contradicted unless the new fact explicitly makes the old fact false."
  - It takes two lists with continuous idx: EXISTING FACTS (same endpoints → duplicate candidates) and FACT INVALIDATION CANDIDATES (broader).
  - Rules: "A contradiction requires explicit evidence that the old fact stopped being true or was replaced… Do NOT infer contradiction from recency alone, episode dates, meeting dates, weekly snapshots…"
  - Example: "Alice works at Acme Corp as a software engineer" vs "…as a senior engineer" → contradicted=[1]. "Bob ran 5 miles on Tuesday" vs "3 miles on Wednesday" → neither.
  - Output schema: `{duplicate_facts: [int], contradicted_facts: [int]}`.
  — [graphiti prompts/dedupe_edges.py L25-114](https://github.com/getzep/graphiti/blob/d50741d/graphiti_core/prompts/dedupe_edges.py#L25-L114)
- Candidate retrieval: related edges come from `search(..., config=EDGE_HYBRID_SEARCH_RRF, search_filter=_pair_search_filter(edge))`, i.e. the same endpoints. Invalidation candidates come from a hybrid search with no endpoint filter. `get_edge_invalidation_candidates` also matches edges touching either endpoint and filters by fact-embedding cosine (`DEFAULT_MIN_SCORE=0.6`, `RELEVANT_SCHEMA_LIMIT=10`) — [edge_operations.py L520-570](https://github.com/getzep/graphiti/blob/d50741d/graphiti_core/utils/maintenance/edge_operations.py#L520-L570); [search_utils.py L64-65, L1587](https://github.com/getzep/graphiti/blob/d50741d/graphiti_core/search/search_utils.py#L1587)
- There are two fast paths that need no LLM. If there are no candidates there is nothing to compare. If the fact text and endpoints already exist verbatim, the matching edge is reused — [edge_operations.py ~L905-952](https://github.com/getzep/graphiti/blob/d50741d/graphiti_core/utils/maintenance/edge_operations.py#L864-L960)
- `resolve_edge_contradictions` interval logic:
  - Skip if the old edge was already invalid before the new edge became valid, or the new edge is invalid before the old became valid.
  - Otherwise, if `old.valid_at < new.valid_at`, set `old.invalid_at = new.valid_at` and `old.expired_at = now` (if unset).
  - Edges with null `valid_at` are never invalidated by this path.
  — [graphiti edge_operations.py L748-783](https://github.com/getzep/graphiti/blob/d50741d/graphiti_core/utils/maintenance/edge_operations.py#L748-L783)
- Order: dedupe → `_extract_edge_timestamps` (a "lightweight LLM call") → `_apply_temporal_invalidation`. "Stops before contradiction so the caller can apply temporal invalidation after the edge is dated" — [edge_operations.py L786-880](https://github.com/getzep/graphiti/blob/d50741d/graphiti_core/utils/maintenance/edge_operations.py#L786-L880)
- Cognee `review_conflicts.txt` (excerpt): "A conflict is one attribute of one subject whose values cannot all be true at once. Report one whenever a single-valued attribute carries different values, a clean handover included: dates that settle which value holds now record the change… Do not report one when the attribute naturally holds several values at once (languages a person speaks…)". The prompt rewrites each subject's description, naming "the value that holds now where dates settle it" — [cognee review_conflicts.txt](https://github.com/topoteretes/cognee/blob/37f788b/cognee/infrastructure/llm/prompts/review_conflicts.txt)
- The `FactConflict` record has `about_id`, `attribute`, `kind: time_varying|fixed`, `status: resolved|unresolved`, `values`, `sources` and `review_pending`. `Entity.conflicts_reviewed_at` is a watermark — [cognee FactConflict.py](https://github.com/topoteretes/cognee/blob/37f788b/cognee/modules/engine/models/FactConflict.py); [Entity.py](https://github.com/topoteretes/cognee/blob/37f788b/cognee/modules/engine/models/Entity.py)
- LightRAG has only the "Conflict Handling" clause in its description summarization (quoted in Q1) — [LightRAG prompt.py L297-329](https://github.com/HKUDS/LightRAG/blob/aaebfe1/lightrag/prompt.py#L297-L329)

### Inferences
- Port the Graphiti scheme for Relic. Keep `valid_at`/`invalid_at` (world time, from message timestamp + LLM/regex date parsing) separate from `created_at`/`expired_at` (ingest time). Never delete. Queries default to `invalid_at IS NULL OR invalid_at > t`, which enables "what did I believe on date X".
- Lifelogs ingest out of order (backfilling years of Kakao history). Graphiti's rule only invalidates the *older-valid_at* edge, so a backfilled older fact will not wrongly expire a newer one. The reverse case is not handled, though: an old fact ingested after a new one is not itself marked invalid. Relic should add the symmetric branch (set the new-but-older edge's invalid_at to the newer edge's valid_at).
- Cognee's approach of a batch conflict review with "time_varying vs fixed" attributes suits a nightly on-device job (charging + idle) better than per-message LLM calls.

### Gaps
- No repo publishes accuracy for contradiction detection. Graphiti's prompt has clearly been tuned against false-positive invalidations (the role/ownership carve-outs), which suggests this was a real failure mode, but that is my inference with no data behind it.

## Q4. Retrieval: hybrid search, reranking, PPR

### Takeaway
Graphiti's retrieval needs no LLM. It combines BM25 full-text, cosine and BFS over edges/nodes/episodes/communities, then reranks with RRF, MMR, node-distance, episode-mentions or a cross-encoder. HippoRAG 2 combines embedding-matched query→triple facts, a single LLM "recognition memory" filter, seed weights and Personalized PageRank (damping 0.5) over an undirected graph. LightRAG uses an LLM to extract query keywords, then does vector lookup of entities (low-level) and relations (high-level), expanded via degree-ranked neighbours. Cognee scores triplets by summed vector distance of node1 + edge + node2.

### Cited Findings
- Graphiti search methods: edges/nodes use `cosine_similarity | bm25 | breadth_first_search`, episodes use `bm25`, communities use `cosine | bm25`. Rerankers are `reciprocal_rank_fusion | node_distance | episode_mentions | mmr | cross_encoder` — [graphiti search_config.py L32-77](https://github.com/getzep/graphiti/blob/d50741d/graphiti_core/search/search_config.py#L32-L77)
- Constants: `DEFAULT_MIN_SCORE = 0.6`, `DEFAULT_MMR_LAMBDA = 0.5`, `MAX_SEARCH_DEPTH = 3` (BFS), `MAX_QUERY_LENGTH = 128` — [search_utils.py L64-68](https://github.com/getzep/graphiti/blob/d50741d/graphiti_core/search/search_utils.py#L64-L68)
- RRF: `scores[uuid] += 1 / (i + rank_const)` with `rank_const=1` (not the usual 60) — [search_utils.py L1775-1790](https://github.com/getzep/graphiti/blob/d50741d/graphiti_core/search/search_utils.py#L1775-L1790)
- MMR: `mmr = λ·cos(q,c) + (λ−1)·max_sim(c, others)`, computed over *all* other candidates (not greedy-iterative) — [search_utils.py L1901-1940](https://github.com/getzep/graphiti/blob/d50741d/graphiti_core/search/search_utils.py#L1901-L1940)
- node_distance: despite the comment "Find the shortest path to center node", the Cypher only checks for a direct 1-hop RELATES_TO. Score is 1 if adjacent, else ∞ (→ 1/∞ = 0); the center node is scored 0.1 and placed first — [search_utils.py L1793-1852](https://github.com/getzep/graphiti/blob/d50741d/graphiti_core/search/search_utils.py#L1793-L1852)
- episode_mentions: RRF first, then sort by count of `(:Episodic)-[:MENTIONS]->(n)` — [search_utils.py L1855-1898](https://github.com/getzep/graphiti/blob/d50741d/graphiti_core/search/search_utils.py#L1855-L1898)
- Cross-encoder options: OpenAI, Gemini, and a local `bge_reranker_client.py` — [graphiti cross_encoder/](https://github.com/getzep/graphiti/tree/d50741d/graphiti_core/cross_encoder)
- HippoRAG 2 retrieve path:
  1. `get_fact_scores` (query embedding vs triple embeddings).
  2. `rerank_facts`: top `linking_top_k=5` candidates go to the DSPy-optimized LLM filter (`DSPyFilter`, prompt "fact_before_filter → fact_after_filter").
  3. If no facts survive, fall back to dense passage retrieval. Otherwise run `graph_search_with_fact_entities`.
  — [HippoRAG.py L740-775](https://github.com/OSU-NLP-Group/HippoRAG/blob/d5c8329/src/hipporag/HippoRAG.py#L740-L775); [rerank.py](https://github.com/OSU-NLP-Group/HippoRAG/blob/d5c8329/src/hipporag/rerank.py)
- HippoRAG seed weights:
  - For each surviving fact, the subject/object phrase nodes get `fact_score / (#chunks containing phrase)`, averaged over occurrences. This is an IDF-like down-weighting of hub entities.
  - Passage nodes get `min_max_normalized_DPR_score * passage_node_weight` (0.05).
  - `node_weights = phrase_weights + passage_weights`.
  — [HippoRAG.py L2040-2113](https://github.com/OSU-NLP-Group/HippoRAG/blob/d5c8329/src/hipporag/HippoRAG.py#L2040-L2113); [config_utils.py L91-93](https://github.com/OSU-NLP-Group/HippoRAG/blob/d5c8329/src/hipporag/utils/config_utils.py#L91-L93)
- HippoRAG PPR: `self.graph.personalized_pagerank(vertices=…, damping=damping, directed=False, weights='weight', reset=reset_prob, implementation='prpack')` with `damping=0.5` default. It returns only passage-node scores, sorted — [HippoRAG.py L2177-2218](https://github.com/OSU-NLP-Group/HippoRAG/blob/d5c8329/src/hipporag/HippoRAG.py#L2177-L2218); [config_utils.py L192-194](https://github.com/OSU-NLP-Group/HippoRAG/blob/d5c8329/src/hipporag/utils/config_utils.py#L192-L194)
- HippoRAG 2 paper: about a 7% gain on associative memory tasks over a state-of-the-art embedding model, while keeping factual/sense-making performance (ICML 2025) — [PMLR v267 gutierrez25a](https://proceedings.mlr.press/v267/gutierrez25a.html); [arXiv 2502.14802](https://arxiv.org/pdf/2502.14802)
- LightRAG modes: `local | global | hybrid | naive | mix | bypass` (default `mix`).
  - Keyword prompt: "extract two distinct types of keywords: high_level_keywords … low_level_keywords."
  - Local mode: entity vector query, then edges ranked "by rank + weight" (rank = degree).
  - Defaults: `TOP_K=40`, `CHUNK_TOP_K=20`, `COSINE_THRESHOLD=0.2`, total context budget 30000 tokens.
  — [LightRAG base.py L93](https://github.com/HKUDS/LightRAG/blob/aaebfe1/lightrag/base.py#L93); [prompt.py L484-516](https://github.com/HKUDS/LightRAG/blob/aaebfe1/lightrag/prompt.py#L484-L516); [operate.py L6200-6316](https://github.com/HKUDS/LightRAG/blob/aaebfe1/lightrag/operate.py#L6200-L6316); [constants.py L57-64](https://github.com/HKUDS/LightRAG/blob/aaebfe1/lightrag/constants.py#L57-L64)
- LightRAG paper: dual-level retrieval (low-level entities, high-level themes) plus an incremental update algorithm; Findings of EMNLP 2025 — [arXiv 2410.05779](https://arxiv.org/html/2410.05779v3); [ACL Anthology](https://preview.aclanthology.org/new-sigs/2025.findings-emnlp.568/)
- Cognee `brute_force_triplet_search`:
  - Score is `sum over (node1, node2, edge) of (2 − importance_weight) × cosine_distance`, optionally blended with feedback/personal weights.
  - Elements not returned by the vector search get `triplet_distance_penalty = 6.5`. `heapq.nsmallest(k)`, with `wide_search_top_k=100`.
  - Triplet embeddings were removed (TRIPLET_COMPLETION deprecated → GRAPH_COMPLETION).
  — [cognee brute_force_triplet_search.py L231-250](https://github.com/topoteretes/cognee/blob/37f788b/cognee/modules/retrieval/utils/brute_force_triplet_search.py#L231); [CogneeGraph.py L430-516](https://github.com/topoteretes/cognee/blob/37f788b/cognee/modules/graph/cognee_graph/CogneeGraph.py#L430-L516); [SearchType.py](https://github.com/topoteretes/cognee/blob/37f788b/cognee/modules/search/types/SearchType.py)
- Zep's own benchmark claims (from search snippets, not verified):
  - Paper: DMR 94.8% vs MemGPT 93.4%; LongMemEval accuracy up to +18.5% with ~90% lower latency vs baseline.
  - Later vendor page: LongMemEval 90.2% (451/500), median context 4,408 tokens, configuration unstated.
  — [Zep paper summary](https://blog.getzep.com/zep-a-temporal-knowledge-graph-architecture-for-agent-memory); [Zep research page](https://www.getzep.com/research/)

### Inferences
- Everything in Graphiti's query path (SQLite FTS5 BM25, sqlite-vec cosine, recursive-CTE BFS, RRF, MMR) is cheap to reproduce in SQLite on a phone. A local bge-reranker is optional.
- HippoRAG's PPR is a sparse power iteration (a few ms for 10^4–10^5 nodes) and suits mobile. Its LLM filter step can be replaced with a cross-encoder or skipped. When the filter returns nothing, the code already falls back to dense retrieval.
- The `/ #chunks containing phrase` seed normalization matters for lifelogs. "Me", "Mom" and "Seoul" would otherwise dominate PPR.

### Gaps
- I did not verify HippoRAG 2's exact per-dataset numbers (paper tables not fetched).

## Q5. Cost: LLM calls per ingested item, and what can be small, local or LLM-free

### Takeaway
Per item: Graphiti is the most expensive, at roughly 3 + E calls per episode (E = extracted edges with candidates). It does route dedup, timestamps, attributes and summaries to a "small" model. HippoRAG 2 is a fixed 2 calls per passage plus 1 per query. LightRAG is 1–2 calls per chunk plus occasional merge summaries and 1 per query. Cognee is about 1 call per chunk (graph + summary), plus optional batch memify passes. GraphRAG "Fast" and LazyGraphRAG replace LLM extraction with NLP noun phrases.

### Cited Findings
- Graphiti per `add_episode`:
  - `extract_nodes`: 1 call, default model.
  - `dedupe_nodes.nodes`: 0–1 batched call, only for names unresolved by the deterministic layers.
  - `extract_edges.edge`: 1 call.
  - Per extracted edge: `dedupe_edges.resolve_edge` (1 call unless a fast path hits) and `extract_timestamps` (batched), plus `extract_attributes` only when custom typed attributes exist.
  - Entity summaries: `extract_summaries_batch`.
  - Bulk mode merges node+edge extraction into one call.
  — call sites [node_operations.py L321, L737, L1057, L1236](https://github.com/getzep/graphiti/blob/d50741d/graphiti_core/utils/maintenance/node_operations.py#L737); [edge_operations.py L235, L814, L915, L982, L1047](https://github.com/getzep/graphiti/blob/d50741d/graphiti_core/utils/maintenance/edge_operations.py#L982); [combined_extraction.py L165-170](https://github.com/getzep/graphiti/blob/d50741d/graphiti_core/utils/maintenance/combined_extraction.py#L165)
- Graphiti routes these to `ModelSize.small`: edge resolution, timestamps, edge attributes, node attributes, summaries and combined-extraction timestamps — [edge_operations.py L821, L922, L989, L1054](https://github.com/getzep/graphiti/blob/d50741d/graphiti_core/utils/maintenance/edge_operations.py#L989); [node_operations.py L1064, L1243](https://github.com/getzep/graphiti/blob/d50741d/graphiti_core/utils/maintenance/node_operations.py#L1243)
- Graphiti GLiNER2 client: "GLiNER2 is a lightweight extraction model (205M-340M params) that handles named entity recognition locally on CPU. All other operations (edge/relation extraction, deduplication, summarization, etc.) are delegated to the required llm_client." Default `fastino/gliner2-base-v1`, threshold 0.5 — [graphiti llm_client/gliner2_client.py](https://github.com/getzep/graphiti/blob/d50741d/graphiti_core/llm_client/gliner2_client.py)
- Graphiti ships clients for OpenAI-generic (any OpenAI-compatible local server), Anthropic, Gemini, Groq and Azure. Embedders: OpenAI, Gemini, Voyage, Azure — [graphiti llm_client/](https://github.com/getzep/graphiti/tree/d50741d/graphiti_core/llm_client); [embedder/](https://github.com/getzep/graphiti/tree/d50741d/graphiti_core/embedder)
- Graphiti query path: 0 LLM calls (embedding + BM25 + graph + optional cross-encoder) — [search_config.py](https://github.com/getzep/graphiti/blob/d50741d/graphiti_core/search/search_config.py)
- HippoRAG 2: NER (1) + NER-conditioned triple extraction (1) per passage. Query: 1 LLM filter call. Synonymy edges and PPR need no LLM — [ner.py](https://github.com/OSU-NLP-Group/HippoRAG/blob/d5c8329/src/hipporag/prompts/templates/ner.py); [triple_extraction.py](https://github.com/OSU-NLP-Group/HippoRAG/blob/d5c8329/src/hipporag/prompts/templates/triple_extraction.py); [rerank.py](https://github.com/OSU-NLP-Group/HippoRAG/blob/d5c8329/src/hipporag/rerank.py)
- LightRAG: 1 extraction call + `MAX_GLEANING=1` continuation per chunk (chunks default ~1200 tokens in the upstream design). Merge summaries are LLM calls only at ≥8 descriptions. Query: 1 keyword call + 1 answer call — [constants.py L17, L30](https://github.com/HKUDS/LightRAG/blob/aaebfe1/lightrag/constants.py#L17-L30); [prompt.py L484](https://github.com/HKUDS/LightRAG/blob/aaebfe1/lightrag/prompt.py#L484)
- Cognee: the default pipeline marks chunking/classification/storage `needs_llm=False`. Only `extract_graph_and_summarize` uses the LLM — [cognify.py L610-650](https://github.com/topoteretes/cognee/blob/37f788b/cognee/api/v1/cognify/cognify.py#L610-L650)
- GraphRAG `IndexingMethod.Fast`: "using NLP for graph construction and language model for summarization". Noun-phrase extractors are regex, CFG and spaCy syntactic (`model_name="en_core_web_md"`, tags PROPN/NOUNS) — [graphrag config/enums.py L44-54](https://github.com/microsoft/graphrag/blob/5faaaf4/packages/graphrag/graphrag/config/enums.py#L44-L54); [defaults.py L162-187](https://github.com/microsoft/graphrag/blob/5faaaf4/packages/graphrag/graphrag/config/defaults.py#L162-L187); [np_extractors/](https://github.com/microsoft/graphrag/tree/5faaaf4/packages/graphrag/graphrag/index/operations/build_noun_graph/np_extractors)
- LazyGraphRAG (Microsoft's claim): indexing cost equals vector RAG and is 0.1% of full GraphRAG. It matches GraphRAG Global Search quality on global queries at more than 700× lower query cost. It defers LLM use to query time. These figures are not independently verified — [Microsoft Research blog](https://www.microsoft.com/en-us/research/blog/lazygraphrag/); caveat noted by [Beri analysis](https://www.beri.net/article/graphrag-vs-vector-rag-indexing-query-cost-lightrag-lazygraphrag-2026)

### Inferences
- These steps can be LLM-free in Relic:
  - chunking/episodizing
  - identity-property merges
  - exact/MinHash name dedup
  - embedding candidate search
  - synonymy edges
  - date normalization (regex/duckling-style plus Graphiti's future-tense rules)
  - temporal interval invalidation logic
  - BM25, vector and BFS search; RRF, MMR, PPR
  - community detection (label propagation)
- Small on-device model (1–4B), or GLiNER-class NER: entity extraction (GLiNER2), dedup judge, contradiction judge, timestamp extraction, summaries. Graphiti already classes most of these as "small".
- The hardest step for a small model is fact/triple extraction with good relation phrasing. Options: run it in a deferred batch on a larger local model, or use HippoRAG-style OpenIE triples with loose predicates.
- A budget-friendly Relic design looks like this: GLiNER-style NER, then 1 combined small-LLM call per episode batch (Graphiti bulk mode), then deterministic dedup, then a judge only on conflicts. Retrieval needs no LLM.

### Gaps
- No repo reports measured tokens per episode. I found no published per-item cost numbers for Graphiti/Cognee beyond the vendor and Microsoft claims above.

## Q6. Storage backends usable locally, licenses, weaknesses

### Takeaway
All five are permissively licensed: Graphiti and Cognee are Apache-2.0; HippoRAG, LightRAG and GraphRAG are MIT. For embedded/local storage, Graphiti supports Kuzu and FalkorDBLite. Cognee defaults to Ladybug (the Kuzu fork) + LanceDB + SQLite, and also has a Turso/libSQL graph+vector adapter. LightRAG defaults to NetworkX + NanoVectorDB + JSON files. HippoRAG uses igraph + parquet embedding stores. Kuzu itself is archived (Oct 2025), which matters for any mobile plan.

### Cited Findings
- Graphiti drivers: neo4j, falkordb, kuzu, neptune. Extras: `kuzu>=0.11.3`, `falkordb`, and `falkordblite` (an embedded FalkorDB, Python ≥ 3.12) — [graphiti driver/](https://github.com/getzep/graphiti/tree/d50741d/graphiti_core/driver); [pyproject.toml L28-40](https://github.com/getzep/graphiti/blob/d50741d/pyproject.toml)
- Graphiti's Kuzu path reifies edges as intermediate `RelatesToNode_` nodes (`(center)-[:RELATES_TO]->(e:RelatesToNode_)-[:RELATES_TO]->(n)`) — [search_utils.py L1812-1817](https://github.com/getzep/graphiti/blob/d50741d/graphiti_core/search/search_utils.py#L1812-L1817)
- Graphiti has no SQLite driver (grep of `driver/` found none) — [graphiti driver/](https://github.com/getzep/graphiti/tree/d50741d/graphiti_core/driver)
- Cognee defaults:
  - `graph_database_provider="ladybug"` (also kuzu-era migration, neo4j, neptune, postgres, turso)
  - `vector_db_provider="lancedb"` (also pgvector, turso)
  - relational `db_provider="sqlite"`
  - pins `ladybug==0.19.0`
  — [graph/config.py L47](https://github.com/topoteretes/cognee/blob/37f788b/cognee/infrastructure/databases/graph/config.py#L47); [vector/config.py L32](https://github.com/topoteretes/cognee/blob/37f788b/cognee/infrastructure/databases/vector/config.py#L32); [relational/config.py L22](https://github.com/topoteretes/cognee/blob/37f788b/cognee/infrastructure/databases/relational/config.py#L22); [pyproject.toml L108-109](https://github.com/topoteretes/cognee/blob/37f788b/pyproject.toml)
- Kuzu repo archived 2025-10-10 (last release v0.11.3). Apple reportedly agreed to acquire Kùzu Inc. on 2025-10-09, per a DMA filing reported by secondary sources. LadybugDB is the community fork ("the database formerly known as Kuzu") — [oneuptime](https://oneuptime.com/blog/post/2026-08-12-kuzu-archived-pin-0-11-3-fork-or-migrate/view); [dbdb.io LadybugDB](https://dbdb.io/db/ladybugdb); [Julia discourse](https://discourse.julialang.org/t/kuzudb-or-general-graphdbs/133139/5)
- LightRAG defaults: `kv_storage="JsonKVStorage"`, `vector_storage="NanoVectorDBStorage"`, `graph_storage="NetworkXStorage"`, `doc_status_storage="JsonDocStatusStorage"`. Server options include faiss, postgres (incl. graph), neo4j, memgraph, mongo, redis, qdrant, milvus and opensearch — [lightrag.py L696-706](https://github.com/HKUDS/LightRAG/blob/aaebfe1/lightrag/lightrag.py#L696-L706); [kg/](https://github.com/HKUDS/LightRAG/tree/aaebfe1/lightrag/kg)
- HippoRAG: igraph graph (pickled, `save_igraph`), embedding stores, and optional vector stores chroma/qdrant/milvus — [HippoRAG.py L1679](https://github.com/OSU-NLP-Group/HippoRAG/blob/d5c8329/src/hipporag/HippoRAG.py#L1679); [vector_stores/](https://github.com/OSU-NLP-Group/HippoRAG/tree/d5c8329/src/hipporag/vector_stores)
- Licenses: graphiti `license = "Apache-2.0"` (pyproject) and Apache LICENSE; cognee Apache-2.0; HippoRAG MIT "Copyright (c) 2025 OSU Natural Language Processing"; LightRAG MIT "Copyright (c) 2025 LightRAG Team"; GraphRAG MIT "Copyright (c) Microsoft Corporation" — LICENSE files at the commits above ([graphiti](https://github.com/getzep/graphiti/blob/d50741d/LICENSE), [cognee](https://github.com/topoteretes/cognee/blob/37f788b/LICENSE), [HippoRAG](https://github.com/OSU-NLP-Group/HippoRAG/blob/d5c8329/LICENSE), [LightRAG](https://github.com/HKUDS/LightRAG/blob/aaebfe1/LICENSE), [graphrag](https://github.com/microsoft/graphrag/blob/5faaaf4/LICENSE))

**Weaknesses observed in code**
- Graphiti:
  - node_distance reranking is 1-hop only, despite "shortest path" comments.
  - RRF uses k=1 (very top-heavy).
  - MMR is a non-iterative approximation.
  - Per-edge LLM resolution scales with fact count.
  - Edges with null `valid_at` can't be invalidated by interval logic.
  - The default stack is OpenAI LLM + embedder + reranker.
  — [search_utils.py L1775-1940](https://github.com/getzep/graphiti/blob/d50741d/graphiti_core/search/search_utils.py#L1775-L1940); [edge_operations.py L748-783](https://github.com/getzep/graphiti/blob/d50741d/graphiti_core/utils/maintenance/edge_operations.py#L748-L783); [graphiti.py L225-300](https://github.com/getzep/graphiti/blob/d50741d/graphiti_core/graphiti.py#L225-L300)
- HippoRAG:
  - No temporal model, no contradiction handling, no entity merging (exact lowercase hash ids). Designed for static corpora QA.
  - Synonymy KNN `topk=2047` is heavy at scale.
  — [HippoRAG.py](https://github.com/OSU-NLP-Group/HippoRAG/blob/d5c8329/src/hipporag/HippoRAG.py#L1278-L1350)
- LightRAG:
  - Name-only merge.
  - Descriptions accumulate as concatenated strings until LLM re-summary, which is lossy and has no timestamps.
  - Relations are treated as undirected by default.
  — [prompt.py](https://github.com/HKUDS/LightRAG/blob/aaebfe1/lightrag/prompt.py#L56-L126)
- Cognee:
  - Write-time identity is lowercased name only, so homonyms collide (two different "Jiwon"s merge).
  - Near-dup consolidation is an offline pass.
  - Time lives in Timestamp nodes, not fact validity.
  — [generate_node_id.py](https://github.com/topoteretes/cognee/blob/37f788b/cognee/infrastructure/engine/utils/generate_node_id.py)

### Inferences
- For an iOS/Android local-first app, none of these Python stacks ship as-is. Two options:
  - Re-implement in SQLite: tables for nodes/edges/episodes with bi-temporal columns, FTS5 for BM25, sqlite-vec for embeddings, recursive CTEs for BFS, and in-memory sparse PPR. The schema and algorithms are small enough to port.
  - Embed LadybugDB, accepting fork maturity risk.
- Avoid depending on Kuzu upstream, since it is archived.
- Homonym risk (Cognee/LightRAG/HippoRAG all key on name) is unacceptable for a personal contact graph. Use Graphiti's approach: type-scoped, summary-aware LLM judgement plus hard identifiers.

### Gaps
- I did not check whether LadybugDB has mobile (iOS/Android) builds. Kuzu historically had no official mobile SDK, but I could not verify this here.
- I did not verify the falkordblite platform support beyond Python ≥ 3.12.
