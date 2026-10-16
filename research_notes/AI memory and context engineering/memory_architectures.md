# Agent Memory and Context Engineering: State of the Art (as of Oct 2026), for a Lifelog Memory System

Note on sourcing: items marked [verified] were read in a primary or near-primary source this session. Items marked [prior, not re-fetched] cite well-known primary papers or repos from background knowledge; their URLs are canonical but the details were not re-read this session. Vendor benchmark numbers are self-reported unless stated otherwise.

## 1. Context engineering concepts

### Takeaway
The consensus framing (Anthropic, Sep 2025; Manus, mid-2025) treats context as a finite "attention budget" that degrades as it fills ("context rot"). Good practice is to keep the window small and high-signal: retrieve just in time from lightweight references, compact or clear stale tool output, keep persistent notes outside the window (memory tool or files), isolate exploration in sub-agents, and keep the prompt prefix stable so the KV-cache is reused. For a lifelog, the corpus (years of captures) will never fit in context even with 1M-token models, so retrieval plus a curated memory layer is required, and long context serves as a working buffer.

### Cited Findings
**Anthropic, "Effective context engineering for AI agents" (Sep 29, 2025) [verified]**
- Context engineering is defined as "the set of strategies for curating and maintaining the optimal set of tokens (information) during LLM inference," and framed as the successor to prompt engineering. — [Anthropic](https://www.anthropic.com/engineering/effective-context-engineering-for-ai-agents)
- Context rot: as the context window grows, the model's ability to recall information from it declines. This happens in all models, to differing degrees. Context is a finite attention budget with diminishing returns per token, and transformers create n² pairwise token relationships. — [Anthropic](https://www.anthropic.com/engineering/effective-context-engineering-for-ai-agents); [secondary summary](https://agentic-ai.readthedocs.io/en/latest/ContextEngineering/anthropic/)
- Just-in-time retrieval: the agent keeps lightweight identifiers (file paths, stored queries, links) and loads data through tools at runtime. In the hybrid approach, Claude Code loads CLAUDE.md up front and uses glob/grep to fetch other files just in time. — [Anthropic](https://www.anthropic.com/engineering/effective-context-engineering-for-ai-agents)
- Compaction in Claude Code: the message history is summarized by the model, which keeps architectural decisions, unresolved bugs and implementation details and drops redundant tool outputs. The agent then continues with the summary plus the 5 most recently accessed files. — [Anthropic](https://www.anthropic.com/engineering/effective-context-engineering-for-ai-agents)
- Tool-result clearing is described as "the lightest form of compaction," removing old raw tool results, and is shipped as a Claude Developer Platform feature. — [Anthropic](https://www.anthropic.com/engineering/effective-context-engineering-for-ai-agents)
- Structured note-taking: in the Claude-plays-Pokémon example, the agent kept notes outside the context window (e.g. progress over "the last 1,234 steps," maps, achievements, strategy) and re-read them after context resets. — [Anthropic](https://www.anthropic.com/engineering/effective-context-engineering-for-ai-agents)
- Sub-agents explore in clean context windows, often using tens of thousands of tokens, and return condensed summaries of about 1,000–2,000 tokens to the lead agent. — [Anthropic](https://www.anthropic.com/engineering/effective-context-engineering-for-ai-agents)
- A bloated tool set with overlapping functions is a common failure mode, so a minimal viable tool set is recommended. — [secondary summary](https://agentic-ai.readthedocs.io/en/latest/ContextEngineering/anthropic/)

**Anthropic memory tool and context management APIs [verified]**
- The memory tool (`{"type": "memory_20250818", "name": "memory"}`) runs client-side. Claude requests file operations (`view`, `create`, `str_replace`, `insert`, `delete`, `rename`) on a `/memories` path prefix, and the application maps that prefix onto its own storage (per-user dir, DB keys, encrypted files). It is available on all Claude 4+ models and no longer requires a beta header. The Python and TypeScript SDKs ship `BetaLocalFilesystemMemoryTool`. — [Claude docs: memory tool](https://platform.claude.com/docs/en/agents-and-tools/tool-use/memory-tool)
- When the tool is enabled, the API injects a system instruction: "ALWAYS VIEW YOUR MEMORY DIRECTORY BEFORE DOING ANYTHING ELSE… ASSUME INTERRUPTION: Your context window might be reset at any moment." — [Claude docs](https://platform.claude.com/docs/en/agents-and-tools/tool-use/memory-tool)
- Security guidance in the docs: (a) the developer must block path traversal (`/memories/../../secrets.env`, URL-encoded `%2e%2e%2f`) by resolving canonical paths; (b) cap file sizes and the number of characters `view` returns; (c) expire files that have not been accessed in a long time; (d) strip sensitive data before writing, since "Claude usually refuses to write sensitive information" but that is not a guarantee. `view` truncates the text of files over 16,000 characters and can display .jpg/.png images. — [Claude docs](https://platform.claude.com/docs/en/agents-and-tools/tool-use/memory-tool)
- Context editing clears specific tool results on the client side. Compaction summarizes the whole conversation server-side as it nears the window limit. Anthropic recommends using both for long-running agents, with memory holding "information that must survive summarization." Its multi-session pattern is an initializer session that writes a progress log and feature checklist, later sessions that read them first, and an update at the end of each session. — [Claude docs](https://platform.claude.com/docs/en/agents-and-tools/tool-use/memory-tool)
- The memory tool was released in public beta alongside Sonnet 4.5 (Sep 2025). — [Anthropic](https://www.anthropic.com/engineering/effective-context-engineering-for-ai-agents)

**Manus, "Context Engineering for AI Agents: Lessons from Building Manus" (Jul 2025) [verified via search snippets; direct fetch failed DNS]**
- The KV-cache hit rate is "the single most important metric" for a production agent, since it drives both latency and cost. Cached input on Claude Sonnet is $0.30/MTok versus $3/MTok uncached, a 10x difference. — [Manus](https://manus.im/en/blog/Context-Engineering-for-AI-Agents-Lessons-from-Building-Manus)
- Keep the prompt prefix stable: a second-precision timestamp in the system prompt invalidates the cache. Keep context append-only, with no edits to past actions or observations. Use deterministic serialization, because unstable JSON key ordering silently breaks caching. Do not add, remove or reorder tools mid-run; Manus masks tool logits instead of removing tools. — [Manus](https://manus.im/en/blog/Context-Engineering-for-AI-Agents-Lessons-from-Building-Manus); [summary](https://agentic-ai.readthedocs.io/en/latest/ContextEngineering/manus/)
- Other lessons from the same post [prior, not re-fetched]: use the file system as unlimited external context with restorable compression (drop a page body but keep its URL); "recite" goals by rewriting a todo.md so objectives stay at the end of context; keep errors in context so the model can adapt; vary serialization to avoid few-shot mimicry. The post reports an average input:output token ratio of about 100:1. The todo.md detail could not be confirmed in this session's search results. — [Manus](https://manus.im/en/blog/Context-Engineering-for-AI-Agents-Lessons-from-Building-Manus); [secondary](https://tianpan.co/blog/2026-03-02-context-engineering-lessons-from-manus)

**Context rot and long context versus RAG**
- Chroma's "Context Rot" report tested 18 frontier models on inputs of increasing length and found every model degraded. The degradation is continuous and starts well before the advertised window limit. — [secondary: Towards AI](https://pub.towardsai.net/context-rot-is-real-and-its-quietly-breaking-every-ai-agent-you-ve-built-8b11045dff9e) (the original Chroma report was not retrieved; per-model figures are unverified)
- LongMemEval reports that commercial chat assistants and long-context LLMs show about a 30% accuracy drop when memorizing information across sustained interactions. — [LongMemEval, ICLR 2025](https://arxiv.org/abs/2410.10813v2)
- In the Mem0 paper, the full-context baseline (about 26k tokens per LoCoMo conversation) had p50 latency of 9.87s and p95 of 17.1s. Mem0 had p50 0.708s and p95 1.44s, reported as 91% lower p95 latency and more than 90% token savings. — [Mem0 paper arXiv 2504.19413](https://arxiv.org/abs/2504.19413v1)
- Cognee notes that memory-benchmark performance begins to decline before the history exceeds the context window. — [Cognee benchmark guide](https://www.cognee.ai/ai-memory-benchmarks)
- "Context Engineering 2.0" (arXiv 2510.26493) is an academic framing of the field. — [arXiv](https://arxiv.org/pdf/2510.26493) (not read in detail)

### Inferences
- Lifelog design implication: treat the LLM context as a cache tier (L1). Use a stable system prefix holding the user profile and core memory blocks, which also maximizes the KV-cache hit rate. Append retrieved snippets after the prefix, and clear raw tool results once they have been distilled into notes.
- A lifelog of years of screen OCR easily exceeds 10^8–10^9 tokens, which is orders of magnitude beyond 1M windows. Even inside the window, context rot argues against stuffing. Long context is best used as the reader stage over about 20–100k tokens of retrieved candidates, not as storage.
- Sub-agents map naturally onto per-source or per-time-range exploration (e.g. "search Kakao in March 2024"), each returning a short summary with citations, i.e. raw-event IDs.
- Compaction loses information. Always keep immutable raw events plus pointers so summaries can be re-expanded (Manus's "restorable compression").

### Gaps
- Exact Chroma context-rot numbers and methodology were not retrieved.
- The Manus page could not be fetched directly (DNS failure), so the todo.md recitation and 100:1 ratio details are from prior knowledge.
- No independent 2026 study was found that quantifies a 1M-token-context versus RAG crossover point for personal-data QA.

## 2. Memory taxonomies

### Takeaway
The field has settled on a cognitive-science-inspired taxonomy. Working memory (the context window and core blocks) sits alongside long-term memory, which divides into episodic (time-stamped events and conversations), semantic (facts and profiles, often as KGs) and procedural (skills, prompts, rules). Reflection or consolidation turns episodes into higher-level facts. The hard problems are updating and conflict resolution (temporal invalidation rather than overwrite) and forgetting (decay, expiry).

### Cited Findings
- Generative Agents (Park et al. 2023) introduced a memory stream of observations, retrieval scored as recency (exponential decay) + importance (LLM-rated 1–10) + relevance (embedding similarity), and periodic reflection that synthesizes higher-level insights when summed importance passes a threshold. — [arXiv 2304.03442](https://arxiv.org/abs/2304.03442) [prior, not re-fetched]
- MemGPT (Packer et al. 2023) applies an OS analogy: main context (core memory, FIFO message queue) versus external context (recall storage of the full message history, archival vector storage), with the LLM paging data through function calls. — [arXiv 2310.08560](https://arxiv.org/abs/2310.08560) [prior, not re-fetched]
- Letta memory blocks are shared in real time: if one agent modifies a block, all agents see the change. — [Letta blog](https://www.letta.com/blog/memory-blocks); [Letta sleep-time docs](https://docs.letta.com/guides/agents/architectures/sleeptime/index.md)
- LangMem explicitly separates semantic (facts/profiles/collections), episodic (past experiences/few-shot) and procedural (prompt optimization) memory, with "hot path" (in-conversation tool) versus "background" (reflection) memory formation. — [LangMem docs](https://langchain-ai.github.io/langmem/concepts/conceptual_guide/) [prior, not re-fetched]
- MemOS classifies memory as textual (plaintext), activation (KV-cache) and parametric (weights/LoRA), all wrapped in a "MemCube" abstraction. — [MemOS (Gitee mirror)](https://gitee.com/joelive/MemOS)
- Update and conflict resolution: Zep/Graphiti keeps a non-lossy timeline of facts with validity periods. When a new fact contradicts an old one, the old edge is marked invalid (an `invalid_at` timestamp) rather than deleted, under a bi-temporal model (event time vs ingestion time). — [Zep paper](https://arxiv.org/html/2501.13956v1); invalidation detail from a [secondary explainer](https://signals.aktagon.com/articles/2026/07/zep-a-temporal-knowledge-graph-architecture-for-agent-memory/)
- Mem0's extraction pipeline asks the LLM to compare each candidate fact with similar existing memories and choose ADD / UPDATE / DELETE / NOOP. — [Mem0 paper](https://arxiv.org/abs/2504.19413v1) [details prior, not re-fetched]
- Forgetting: Anthropic recommends expiring memory files that have not been accessed in a long time. — [Claude docs](https://platform.claude.com/docs/en/agents-and-tools/tool-use/memory-tool). Generative Agents uses exponential recency decay in scoring rather than deletion. — [arXiv 2304.03442](https://arxiv.org/abs/2304.03442) [prior]
- BEAM's ten categories (preference following, instruction following, information extraction, knowledge update, multi-session reasoning, summarization, temporal reasoning, event ordering, abstention, contradiction resolution) are a practical checklist of memory capabilities. — [Mem0 summary of BEAM](https://mem0.ai/blog/state-of-ai-agent-memory-2026)

### Inferences
- A lifelog maps cleanly onto this taxonomy:
  - Raw events (screenshots, messages, visits) form an immutable episodic log.
  - Day and week summaries are reflections.
  - The person, place, project and preference graph is semantic memory, with bi-temporal validity because people change jobs, addresses and phone numbers.
  - Procedural memory holds the user's assistant preferences and workflows.
- For personal data, prefer invalidate-not-delete (Graphiti style). "Where did I live in 2022?" requires history, and deletion should be reserved for user-initiated forgetting or privacy requests.

### Gaps
- No consensus algorithm exists for decay or forgetting at lifelog scale. Most systems rely on recency weighting or TTLs, and I found no rigorous 2025–26 evaluation of forgetting policies.

## 3. Frameworks

### Takeaway
Nearly all major memory frameworks are permissively licensed (Apache-2.0 or MIT) and can run locally with a local LLM and embedder, but they differ in their core data model. Vector plus extracted facts (Mem0, LangMem, Memobase profiles) is cheapest. Temporal KGs (Graphiti) are best for change over time and entity-centric queries. Graph-RAG indexers (GraphRAG, LightRAG, HippoRAG 2, LazyGraphRAG) target corpus-level QA over documents. Agent runtimes (Letta) manage self-editing context. For a lifelog, Graphiti-style temporal KG plus vector/multimodal index plus LLM-maintained profile blocks is the most defensible combination.

### Cited Findings
**Licenses (read from each repo's LICENSE file on GitHub, Oct 2026) [verified]**
- Apache-2.0: mem0ai/mem0 (includes OpenMemory), getzep/graphiti, letta-ai/letta, topoteretes/cognee, MemTensor/MemOS, memodb-io/memobase. — LICENSE files at github.com/{repo}, e.g. [mem0](https://github.com/mem0ai/mem0), [graphiti](https://github.com/getzep/graphiti), [letta](https://github.com/letta-ai/letta), [cognee](https://github.com/topoteretes/cognee), [MemOS](https://github.com/MemTensor/MemOS), [memobase](https://github.com/memodb-io/memobase)
- MIT: langchain-ai/langmem, agiresearch/A-mem, supermemoryai/supermemory, microsoft/graphrag, OSU-NLP-Group/HippoRAG, HKUDS/LightRAG, illuin-tech/colpali. — [langmem](https://github.com/langchain-ai/langmem), [A-mem](https://github.com/agiresearch/A-mem), [supermemory](https://github.com/supermemoryai/supermemory), [graphrag](https://github.com/microsoft/graphrag), [HippoRAG](https://github.com/OSU-NLP-Group/HippoRAG), [LightRAG](https://github.com/HKUDS/LightRAG), [colpali](https://github.com/illuin-tech/colpali)
- Caveat: the Supermemory hosted product and API are commercial, and the MIT license covers the repo. Zep Community Edition was reportedly deprecated in April 2025, so the open-source path is now Graphiti, not Zep server. — [Atlan comparison](https://atlan.com/know/zep-vs-mem0/) (single secondary source)

**MemGPT → Letta**
- Sleep-time compute (paper arXiv 2504.13171; Letta blog Apr 21, 2025): background "sleep-time" agents asynchronously rewrite the primary agent's memory blocks, producing "learned context" during idle time. `enable_sleeptime` creates a primary agent (conversation_search, archival_memory_search) plus a sleep-time agent that manages memory blocks. Letta docs label it experimental. — [Letta docs](https://docs.letta.com/guides/agents/architectures/sleeptime/index.md); [Letta blog](https://www.letta.com/blog)

**Mem0 (paper arXiv 2504.19413, Apr 2025)**
- Two-phase pipeline (extraction, then update), with a graph variant Mem0g that stores entities and relations (Neo4j). The paper reports Mem0g scoring about 2% higher overall than base Mem0 on LoCoMo; Mem0 search p50 is 0.148s; A-Mem total p50 is 1.41s; LangMem search p50 is 17.99s and p95 59.82s. — [arXiv 2504.19413](https://arxiv.org/abs/2504.19413v1)
- OpenMemory MCP (announced May 13, 2025) is a local-first MCP server with tools `add_memories`, `search_memory`, `list_memories` and `delete_all_memories`, so multiple MCP clients (Claude Desktop, Cursor, etc.) can share one local store. — [Mem0 docs](https://docs.mem0.ai/openmemory); [CometAPI](https://www.cometapi.com/?p=25577)
- Hosted Mem0 tiers are reported at $19/$79/$249 per month (June 2026). — [hjarni comparison](https://hjarni.com/blog/mem0-vs-supermemory-vs-hjarni) (competitor source)

**Zep / Graphiti (arXiv 2501.13956, Jan 2025)**
- Graphiti is a temporally aware KG engine with episode, semantic-entity and community subgraphs. The paper reports DMR 94.8% vs MemGPT's 93.4%, and on LongMemEval up to 18.5% accuracy improvement with about 90% latency reduction versus full-context baselines. — [Zep paper](https://arxiv.org/html/2501.13956v1)

**Other systems**
- A-MEM (arXiv 2502.12110) builds Zettelkasten-style notes. Each memory gets LLM-generated keywords, tags and context, links to related notes, and triggers "memory evolution" that updates older notes. — [arXiv 2502.12110](https://arxiv.org/abs/2502.12110) [prior, not re-fetched]
- MemOS has textual, activation and parametric memory types; its README reports self-reported gains over baselines including Mem0, Memobase and others. — [MemOS](https://gitee.com/joelive/MemOS)
- Supermemory is a memory API that ingests content, extracts and updates facts and handles contradictions, and claims sub-300ms p50 search (vendor claim). — [hjarni comparison](https://hjarni.com/blog/mem0-vs-supermemory-vs-hjarni)
- Cognee reports state-of-the-art results on BEAM with a structured-memory approach, 3.5–12.7% over the strongest baseline (self-reported). — [Cognee](https://www.cognee.ai/ai-memory-benchmarks)

**Graph-RAG family**
- LazyGraphRAG (Microsoft Research, Nov 2024) has indexing cost identical to vector RAG and 0.1% of full GraphRAG's, because it defers summarization to query time. — [Microsoft Research](https://www.microsoft.com/en-us/research/blog/lazygraphrag-setting-a-new-standard-for-quality-and-cost/)
- HippoRAG 2 (arXiv 2502.14802) uses Personalized PageRank over an open-IE KG with passage nodes. It claims low online cost and latency and "significantly fewer resources for offline indexing" than GraphRAG, RAPTOR and LightRAG (self-reported). — [HippoRAG PyPI/GitHub](https://pypi.org/project/HippoRAG/)
- LightRAG (arXiv 2410.05779) uses dual-level (low/high) keyword retrieval over an entity-relation graph with incremental updates; it is commonly positioned as the cheaper GraphRAG. No primary cost figure was found. — [LightRAG repo](https://github.com/HKUDS/LightRAG) [details prior]

**Local capability**
- Local-first options: OpenMemory MCP (local by design), the Anthropic memory tool (client-side storage, though inference runs in the cloud), and Graphiti, Cognee, LightRAG and HippoRAG, which accept OpenAI-compatible or local LLM endpoints and local graph or vector DBs. — [Mem0 OpenMemory docs](https://docs.mem0.ai/openmemory); [Claude docs](https://platform.claude.com/docs/en/agents-and-tools/tool-use/memory-tool). Per-framework local-LLM quality was not verified this session.

### Inferences
- Lifelog stack sketch:
  1. An immutable event store (SQLite or DuckDB) indexed by timestamp and source.
  2. Text plus multimodal vector indexes.
  3. A Graphiti-like bi-temporal entity graph for people, places, orgs and projects.
  4. LLM-maintained profile and core blocks (Letta- or Memobase-style).
  5. Sleep-time consolidation jobs that run nightly on-device or on a home server (daily digests, entity merges, contradiction checks).
  6. MCP exposure.
- KG extraction cost per event matters at lifelog volume (thousands of screenshots per day). Use LazyGraphRAG-style deferral or cheap local extraction, and full LLM extraction only for high-salience items.

### Gaps
- Star counts and latest release dates were not retrieved (GitHub API access was blocked).
- No independent, same-stack comparison of these frameworks on personal or lifelog data was found.
- I could not confirm whether Memobase or Supermemory self-host fully offline without their cloud.

## 4. Benchmarks and critiques

### Takeaway
LoCoMo (about 26k-token conversations) is saturated and disputed. LongMemEval (500 questions, 5 abilities; ICLR 2025) is the most cited serious benchmark. MemoryAgentBench (ICLR 2026) and BEAM (1M/10M tokens) are the 2025–26 stress tests. Nearly all leaderboard numbers are vendor-reported with different LLMs, judges and top-k settings, so they are not comparable, and the Zep vs Mem0 dispute is the canonical example.

### Cited Findings
- LongMemEval tests five abilities (information extraction, multi-session reasoning, temporal reasoning, knowledge updates, abstention) with 500 questions embedded in scalable chat histories. It proposes an indexing → retrieval → reading framework. — [arXiv 2410.10813](https://arxiv.org/abs/2410.10813v2)
- LoCoMo (Maharana et al., 2024) contains very long multi-session dialogues; the original paper uses question categories including single-hop, multi-hop, temporal, open-domain and adversarial. — [arXiv 2402.17753](https://arxiv.org/abs/2402.17753) [prior, not re-fetched]
- MemoryAgentBench, "Evaluating Memory in LLM Agents via Incremental Multi-Turn Interactions" (ICLR 2026), has 2,071 questions over inputs of 103k to 1.44M tokens. Its four competencies are accurate retrieval, test-time learning, long-range understanding and conflict resolution [competency list prior]. — [Mem0 summary](https://mem0.ai/blog/state-of-ai-agent-memory-2026); [paper arXiv 2507.05257](https://arxiv.org/abs/2507.05257) [prior]
- BEAM operates at 1M and 10M token scales with 10 categories. Mem0 self-reports 64.1% at BEAM-1M and 48.6% at BEAM-10M and calls the 1M→10M drop a key open problem. A small vendor (CEM888) claims 77.2% at BEAM-10M versus Exabase 68.0% and Hindsight 64.1%. — [Mem0](https://mem0.ai/blog/state-of-ai-agent-memory-2026); [CEM888 repo](https://github.com/CEM888AI/benchmarks). Sources disagree on BEAM size: Cognee describes 100 conversations and 2,000 questions, CEM888 a 200-question set. — [Cognee](https://www.cognee.ai/ai-memory-benchmarks)

**Zep vs Mem0 dispute**
- Mem0's paper listed Zep at 65.99% J on LoCoMo. Zep responded that Zep was misconfigured (searches run sequentially rather than in parallel, inflating latency) and reported 75.14% ± 0.17 J, about 10% relative above Mem0's best. — [Zep blog](https://blog.getzep.com/lies-damn-lies-statistics-is-mem0-really-sota-in-agent-memory/) (fetch failed; per search summary); [Mem0 benchmark post](https://mem0.ai/blog/ai-memory-benchmarks)
- In Mem0's own original table, a plain full-context baseline scored about 73% while Mem0's best variant scored about 68%. — [memoryplugin field guide](https://www.memoryplugin.com/wiki/evaluating.html) (secondary)
- Current Mem0 self-reports are 92.5% on LoCoMo and 94.4% (or 93.4 vs Zep 71.2) on LongMemEval. None of these use the same model stack, judge or retrieval config. — [Mem0](https://mem0.ai/blog/zep-vs-mem0-which-ai-memory-layer-should-you-choose); [memoryplugin](https://www.memoryplugin.com/wiki/evaluating.html)
- MemPalace's claimed 100% on LoCoMo used top_k=50, effectively retrieving the whole conversation. — [Vectorize](https://vectorize.io/articles/mempalace-benchmarks); [arXiv 2604.21284](https://arxiv.org/pdf/2604.21284)
- Newer 2026 benchmarks (preprints, not read in detail): DolphinBench (Pareto frontier of memory cost/quality, [arXiv 2609.24971](https://arxiv.org/pdf/2609.24971)); StreamMemBench (streaming, future-oriented assistance, [arXiv 2606.14571](https://arxiv.org/pdf/2606.14571)); "When Does Memory Help? A Cost-Aware Evaluation" ([arXiv 2609.05441](https://arxiv.org/pdf/2609.05441)); DreamBench-SWE (memory hygiene, [arXiv 2608.20664](https://arxiv.org/pdf/2608.20664)).

### Inferences
- None of these benchmarks resembles a lifelog: multimodal, multi-source, years long, with entity aliasing. A builder should create a private eval of about 100–300 questions over their own data, stratified by LongMemEval/BEAM categories (temporal, knowledge-update, abstention, multi-hop across sources), and fix judge and model across runs.
- The full-context baseline beating Mem0 on LoCoMo suggests that at short scale, long context wins. Memory systems pay off on cost and latency and at scales beyond the window (BEAM-10M), which is where lifelogs sit.

### Gaps
- No neutral, third-party leaderboard comparing Mem0, Zep, Letta, Cognee and others on the same stack was found.
- The Zep rebuttal page could not be fetched directly.

## 5. Lifelog-specific concerns

### Takeaway
The key lifelog-specific techniques are:
- **Time as a first-class index:** bi-temporal validity plus event-time filters.
- **Cross-source entity resolution:** handles, phone numbers and emails merged into person nodes.
- **Screenshot retrieval:** OCR text plus visual late-interaction embeddings (ColPali/ColQwen) or single-vector multimodal embeddings, with storage compression.
- **Small on-device models for summarization:** e.g. Apple's ~3B Foundation Models with guided generation, but with tiny context windows.

Memory is also a persistence channel for prompt injection: documented attacks on ChatGPT (2024) and Gemini (2025), and agent variants (2026), plant false memories from untrusted content.

### Cited Findings
**Temporal indexing**
- Graphiti tracks a timeline of facts with validity periods (non-lossy). — [Zep paper](https://arxiv.org/html/2501.13956v1)
- Temporal reasoning, event ordering and knowledge update are distinct benchmark categories where systems are weakest. — [Mem0/BEAM summary](https://mem0.ai/blog/state-of-ai-agent-memory-2026); [LongMemEval](https://arxiv.org/abs/2410.10813v2)

**Entity resolution**
- Graphiti performs entity extraction and deduplication against existing nodes during ingestion. — [Zep paper](https://arxiv.org/html/2501.13956v1) [detail prior]
- I found no source specifically on cross-platform identity resolution (email ↔ Instagram ↔ KakaoTalk) in memory frameworks. See Gaps.

**Screenshot and visual embeddings**
- ColPali stores many patch vectors per page (about 1,031 × 128-dim for ColPali v1.3), which makes storage the main cost. Remedies:
  - Pooling and clustering reductions from 16× up to 516× fewer vectors ([arXiv 2609.07262](https://arxiv.org/pdf/2609.07262)).
  - HPC-ColPali compression, pruning and quantization.
  - ColModernVBERT (250M parameters; ViDoRe 68.6 vs ColPali 69.2; CPU query encoding 0.032s vs 0.222s).
  - VisRAG single-vector pooling (smaller and faster, weaker recall).
  - MUVERA fixed-dimensional encodings for standard ANN plus MaxSim rerank (ColQwen2 at 99.4% of brute-force quality; supported in Qdrant and Weaviate).

  — [emergentmind/ColPali](https://www.emergentmind.com/topics/colpali); [Mixpeek ColQwen2+MUVERA](https://blog.mixpeek.com/colqwen2-muvera-multimodal-late-interaction/); [arXiv 2506.21601](https://arxiv.org/html/2506.21601v2)
- ColPali original paper: [arXiv 2407.01449](https://arxiv.org/abs/2407.01449) [prior]. Repo is MIT-licensed. — [colpali](https://github.com/illuin-tech/colpali)

**On-device models**
- The Apple Foundation Models framework (iOS/macOS 26) exposes a ~3B on-device model. Its key feature is "guided generation" (Swift `@Generable` constrained decoding). Sessions are append-only, stateful and coupled to the KV cache. Apple says the model is not meant as a general world-knowledge chatbot. — [Apple tech report arXiv 2507.13575](https://arxiv.org/pdf/2507.13575)
- The on-device context window is reported as 4,096 tokens shared by prompt and response, readable via `SystemLanguageModel.default.contextSize`. — [third-party guide](https://blakecrosley.com/es/blog/apple-foundation-models-framework) (unverified against Apple docs; the 32K PCC figure is also third-party)

**Memory poisoning**
- SpAIware (Rehberger, Sep 2024): indirect prompt injection from a web page or document planted persistent instructions in ChatGPT memory (macOS app), so every future chat exfiltrated data. OpenAI patched the exfiltration vector in 1.2024.247 but initially treated memory writes as a model-safety issue. — [The Hacker News](https://thehackernews.com/2024/09/chatgpt-macos-flaw-couldve-enabled-long.html)
- Gemini (Rehberger, Feb 2025): "delayed tool invocation" bypassed Gemini's rule against calling memory tools while processing untrusted data. The injected doc conditions a memory save on a later user utterance, and the planted memory ("you're 102 years old") persisted. Google's mitigation was limited. — [Gigazine](https://gigazine.net/gsc_news/en/20250214-prompt-injection-gemini-long-term-memory/); [Techzine](https://www.techzine.eu/news/security/128653/a-new-hack-corrupts-geminis-long-term-memory/); original: embracethered.com (not opened)
- ZombieAgent (Radware, Jan 2026): a malicious email attachment planted a memory in a ChatGPT agent connected to the user's inbox. — reported via [The Hacker News search summary](https://thehackernews.com/2024/09/chatgpt-macos-flaw-couldve-enabled-long.html) (secondary; Radware primary not opened)

### Inferences
- **Highest-risk input:** a lifelog ingests exactly the untrusted content (web pages, emails, messages from others, screenshots containing text) that these attacks use.
- **Required controls:**
  - Provenance on every memory (source event ID, author, trust level).
  - No automatic memory writes from third-party content without quarantine or review.
  - Memory writes only from user-authored or verified sources.
  - A user-visible memory diff/audit log.
  - Treat retrieved memory as data, never instructions.
- **Entity resolution:** use deterministic keys first (phone, email, platform IDs from exports), then embedding/name similarity plus LLM adjudication with human confirmation for merges. Store merges as reversible "same_as" edges rather than destructive merges.
- **Screenshots:** OCR text plus a compressed ColQwen-class visual index (or a single-vector multimodal embedding for recall, with late-interaction rerank) fits on a laptop if pooling or MUVERA is applied.
- **On-device summarization:** 4K-token on-device models suit per-event or per-window extraction (structured via guided generation). Day- or week-level reflection needs a bigger local model or cloud.

### Gaps
- No primary source was found on cross-platform personal identity resolution for memory systems, or on KakaoTalk export formats.
- The Apple context window size was not confirmed from Apple's docs.
- No 2026 primary source was located for the Radware ZombieAgent details.
- I did not find current figures for screenshot-specific multimodal embedders (e.g. Jina, Nomic, Voyage multimodal) on lifelog-like data.

## 6. Exposing memory to assistants (MCP, permissions, scoping)

### Takeaway
MCP is the de facto interface for exposing a memory store to multiple assistants (OpenMemory MCP is the reference local example). Scoping is the builder's responsibility: path or namespace restriction (as with the memory tool's `/memories` sandbox), per-client permissions, read/write separation, and audit, combined with prompt-injection defenses, because any connected client can be the vector that writes poisoned memories.

### Cited Findings
- OpenMemory MCP runs locally and exposes `add_memories` / `search_memory` / `list_memories` / `delete_all_memories`, so memory is shared across MCP clients without cloud dependency. — [Mem0 docs](https://docs.mem0.ai/openmemory)
- Anthropic's memory tool leaves storage, scoping and security to the application: path validation, size caps, expiry and sensitive-data stripping. — [Claude docs](https://platform.claude.com/docs/en/agents-and-tools/tool-use/memory-tool)
- The MCP specification (2025 revisions) defines OAuth 2.1-based authorization for HTTP transports and tool annotations (e.g. readOnlyHint, destructiveHint). — [MCP spec](https://modelcontextprotocol.io/specification) [prior, not re-fetched]
- Gemini's memory attack shows that "don't call memory tools on untrusted data" policies can be bypassed via delayed invocation, so tool-level scoping alone is insufficient. — [Gigazine](https://gigazine.net/gsc_news/en/20250214-prompt-injection-gemini-long-term-memory/)

### Inferences
- Recommended surface for a lifelog MCP server:
  - Separate read tools (`search_events(time_range, sources, people)`, `get_event(id)`, `get_profile`) from write tools (`propose_memory`), with writes landing in a review queue.
  - Per-client scopes, e.g. coding assistant gets no access to messages, and source-level ACLs (exclude health/finance).
  - Return citations (event IDs) with every result.
  - Never place raw third-party text in tool descriptions.
  - Log every access.
- Keep the stable profile block small and in the cached prefix. Expose everything else via just-in-time search tools, which aligns the context-engineering guidance with privacy minimization.

### Gaps
- I did not verify the current (2026) MCP authorization spec revision or any standard for memory-specific permission scopes. No widely adopted "memory permissions" standard was found.
