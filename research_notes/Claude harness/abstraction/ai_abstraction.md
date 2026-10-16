# How AI agent systems build hierarchical abstractions from experience (state of 2026-10)

Research date: 2026-10-16. Written for the claude-harness layered pattern system: the BLUEPRINT §0.5 improvement loop (log, then small ACE-style edits, then an eval gate, then human review, then expiry) and the intent/situation/meta event schema.

**How it was gathered.** arXiv, Hugging Face, alphaXiv, Semantic Scholar and emergentmind are all DNS- or proxy-blocked from this container. Paper claims therefore come from search-engine abstract snippets. Mechanisms for 8 systems were checked against shallow clones of their public repos, read-only, in `/tmp/claude-0/-home-user-albers-club/1397d302-c3cb-5329-ad06-e45b2c66c6d1/scratchpad/ai_abs/`:
- ace
- reasoning-bank
- generative_agents
- ExpeL
- agent-workflow-memory
- Voyager
- A-mem
- raptor

**Confidence tags** (same convention as FANOUT.md):
- **[H]** I read it in the code or the official README.
- **[M]** It comes from an abstract or search snippet, or from strong secondary sources.
- **[R]** It is my recall of the paper and could not be re-fetched today. Verify it before citing it externally.

---

## 0. TL;DR for the harness

1. **There are two families of abstraction-building, and they have very different evidence.**
   - **Compression-based** (DreamCoder, Stitch, LILO, RIMRULE). Abstractions are kept when they shrink the description length of the corpus. This is principled and measurable, but symbolic, and it needs a corpus of structured traces.
   - **LLM-reflection-based** (Generative Agents, ExpeL, Reflexion, AWM, ReasoningBank, ACE, A-MEM). An LLM reads trajectories and writes insights. It is cheap and general, and it is **fragile**:
     - Continuous LLM rewriting of memory first helps, then degrades below the no-memory baseline. GPT-5.4 failed on 54% of ARC-AGI problems it had previously solved without memory, even when consolidating from ground-truth solutions. An episodic-only control stayed competitive with every consolidator tested, ACE and AWM among them [M, Zhang et al. 2605.12978].
     - Multi-iteration experience internalization shows "progressive capability collapse" [M, 2606.04703].
     - Self-generated skills give **no average benefit**, while curated skills give +16.2pp [M, SkillsBench 2602.12670].
     - In-context "library learning" systems (LEGO-Prover, TroVE) show **near-zero real reuse** and do not beat compute-matched repeated prompting [M, Berlot-Attwell et al., EACL 2026].
2. **What reliably works is the combination: generate candidates by LLM, score them structurally, and admit them only via a held-out gate.**
   - SkillOpt: a single skill.md is the trainable parameter, reflection-driven edits are accepted only through held-out validation gates, and only 1–4 net accepted edits are needed per benchmark. Results are +19.1pts in Claude Code [M].
   - EvoSkill: Pareto-frontier selection on held-out validation took Opus 4.5 in Claude Code from 60.6% to 67.9% on OfficeQA, and SealQA skills gave +5.3% zero-shot on BrowseComp [M].
   - ASI: programmatic verification of skills gave +11.3pts over text skills [M].

   This matches BLUEPRINT §0.5 ("merge only if eval doesn't get worse").
3. **Keep raw episodes as first-class, immutable evidence. Abstractions are views over them, not replacements.** Every abstraction stores pointers to the episodes that support it, so it can be re-derived, audited or dropped. This is the main 2026 lesson (2605.12978, Hippocam 2610.12124 "keeps original interactions available for recovery", RAPTOR keeping leaves).
4. **Principle-level beats instance-level for durability, but abstraction can drop the applicability conditions.** Store every abstraction as **condition → action → rationale (+ when NOT to use)**. ReasoningBank's schema ("Description: when or when NOT to use") and RIMRULE's 5-field schema (domain, qualifier, action, strength, tool category) are both instances of this.
5. **Counters plus decay are the practical pruning mechanism.**
   - ExpeL: ADD +2, AGREE +1, EDIT +1, REMOVE −1 (−3 when the list is full), deleted at 0 [H].
   - ACE: helpful/harmful counters per bullet, plus embedding dedup at cosine 0.90 [H].
   - Generative Agents: recency decay 0.99 per hour [H].
   - Hippocam: unused history is recursively abstracted [M].

   Combine these with BLUEPRINT's "expire after N weeks unused".
6. **"Cross-task convergence" is best detected structurally, not by asking an LLM "is this general?"** The signals are:
   - **Support:** how many episodes.
   - **Spread:** how many distinct projects, domains or intents, measured by entropy.
   - **Compression gain:** an MDL saving.
   - **Lift:** the outcome when the pattern is applied versus not.
   - **Stability:** whether it holds across time windows.

   AWM gets cross-website/domain gains growing from +8.9 to +14.0 absolute as the train-test gap widens [M]. EvoSkill and RIMRULE show held-out and unseen-tool transfer [M].

---

## 1. System-by-system

Each entry covers six things: how abstractions are formed, how levels are represented, validation, pruning, gains, and maturity.

### 1.1 Generative Agents (Park et al., UIST 2023): reflection trees [H code, R numbers]

**Formation**
- Every observation gets an LLM "poignancy" (importance) score from 1 to 10.
- Reflection fires when the running sum of importance of recent events crosses a threshold: `importance_trigger_max = 150`, decremented per event in `scratch.py`/`reflect.py` [H].
- Reflection itself has two steps (`reflect.py` [H]):
  1. Generate 3 **focal points** (salient high-level questions) from the most recent ~100 memories.
  2. For each focal point, retrieve the relevant memories and generate up to 5 **insights with evidence pointers**, written as "insight (because of 1, 5, 3)".

**Levels**
- Insights are stored as `thought` nodes whose `filling` holds evidence node IDs, and the evidence can itself be thoughts.
- This gives a **tree or DAG of arbitrary depth**: observations are leaves, reflections are internal nodes, and reflections on reflections sit higher.
- Thoughts get their own poignancy and re-enter retrieval.

**Retrieval scoring**

`score = w_r·recency + w_rel·cosine + w_i·importance`

All weights are 1, `recency_decay = 0.99` per game-hour, and each component is min-max normalized [H].

**Validation**
- There is none per-insight.
- The paper's ablation (via human evaluation) found that removing reflection degraded believability [R].

**Pruning**
- There is none. Recency decay only lowers rank, it never deletes anything.

**Maturity**
- The pattern (importance-triggered reflection, evidence pointers, recency×relevance×importance retrieval) is now standard: Letta, LangMem and A-MEM all descend from it.
- **Steal for the harness:**
  - the importance-sum trigger
  - evidence pointers
  - the three-factor retrieval score

### 1.2 Reflexion (Shinn et al., NeurIPS 2023) [R]

**Formation and levels**
- After a failed trial (judged by a binary or heuristic evaluator, or unit tests), the agent writes a verbal self-reflection.
- That reflection goes into an episodic buffer used on the next trial of the *same* task.
- There is a single level, and the abstraction is local to one task.

**Validation and pruning**
- Validation is the next trial's outcome.
- Pruning is a sliding window of 1–3 reflections.

**Gains and maturity**
- Reported 91% pass@1 on HumanEval versus 80% for the GPT-4 baseline at the time [R].
- Mature as a retry pattern. It does not transfer across tasks by itself; that was ExpeL's contribution.
- **Harness analog:** the mishap log entry plus its "how to prevent" field.

### 1.3 ExpeL (Zhao et al., AAAI 2024): experiential insights [H code, M paper]

**Formation**
- The agent first gathers Reflexion-style trajectories on training tasks.
- An LLM then compares **success/failure pairs** of the same task, plus batches of successes, against the current rule list.
- It emits operations `ADD`, `EDIT n`, `AGREE n` (upvote) and `REMOVE n` (downvote).

**Levels**
- Two levels:
  - a flat, global **insight list** (cross-task rules)
  - **retrieved successful trajectories** as few-shot examples, chosen by task similarity
- Insights are injected into every task.

**Validation and pruning** (`agent/expel.py`, `update_rules` [H])

| Event | Effect on the rule's counter |
|---|---|
| `ADD` | new rule starts at 2 |
| `AGREE` | +1 |
| `EDIT` | +1, and the text is replaced |
| `REMOVE` | −1, or −3 if the list is full |

- Ops are applied in the order REMOVE, AGREE, EDIT, ADD.
- An ADD whose text matches an existing rule is converted to AGREE.
- Rules with a counter ≤ 0 are dropped, and the list is sorted by counter.
- The whole scheme is a **vote-count importance scheme with capacity pressure**.

**Validation and gains**
- There is no held-out gate. Validation is just the downstream evaluation.
- It showed transfer from HotpotQA insights to FEVER [R].

**Maturity**
- Research, but the counter mechanism is the cleanest, simplest pruning rule in the literature and directly implementable.

### 1.4 Voyager (Wang et al., 2023): skill library [H code, R numbers]

**Formation**
- An automatic curriculum proposes the next task.
- GPT-4 writes JS code and iterates with environment feedback, execution errors and a **self-verification critic**, for up to 4 retries.
- Only code the critic judges successful is added (`skill.py` `add_new_skill` [H]).
- GPT generates a description of the skill, and that description is embedded in Chroma.

**Levels**
- Skills call other skills, so there is **compositional depth by reuse** and no explicit hierarchy.
- Retrieval takes the top-5 skills by embedding of the description [H].

**Validation**
- An LLM critic checks the environment state. This is an execution check, not a held-out check.

**Pruning**
- Rewriting a skill with the same name versions it (`nameV2.js`).
- Nothing is ever deleted.

**Gains and maturity**
- 3.3× more unique items, 2.3× longer distances, and tech-tree milestones up to 15.3× faster than baselines; the skill library also transferred to a new world [R].
- Pattern is mature: verified executable skills plus description retrieval. Anthropic Agent Skills are the human-curated descendant.

### 1.5 DreamCoder (Ellis et al., PLDI 2021), Stitch (Bowers et al., POPL 2023) and LILO (Grand et al., ICLR 2024): library learning by compression [M/R]

**DreamCoder formation: wake-sleep**
- **Wake:** solve tasks by program search guided by a neural recognition model.
- **Abstraction sleep:** refactor the solved programs (version spaces) and add the λ-abstractions that **maximize the Bayesian posterior**. In practice that means minimizing:

  `description_length(library) + Σ_tasks description_length(best program | library)`

  This is MDL.
- **Dream sleep:** train the recognition model on fantasies.

**Levels**
- A library of functions that call earlier functions, giving deep hierarchies.
- The canonical example is a rediscovered `map`/`fold`, which is then used to define higher concepts.

**Stitch**
- Replaces DreamCoder's refactoring with top-down corpus-guided search for the single abstraction with the highest **compressive utility**: roughly, how much the corpus shrinks when the abstraction is rewritten in, which is about uses × (size − arity) minus its own cost.
- It is iterated greedily.
- It is about 3–4 orders of magnitude faster and uses less memory than DreamCoder [R].

**LILO**
- Loop: an LLM synthesizes programs, Stitch compresses them, and **AutoDoc** has an LLM name and document each abstraction.
- The documentation makes abstractions *usable* by the LLM synthesizer.
- It beats DreamCoder on string editing, scene reasoning and graphics [M].

**Validation and pruning**
- The MDL objective itself is the guard against overfitting: an abstraction used once does not pay for itself.
- Abstractions that stop compressing the growing corpus are dropped at the next refactoring.

**Caveats**
- Berlot-Attwell et al. (2410.20274, and EACL 2026 2026.eacl-long.163) show that *LLM in-context* library learners (LEGO-Prover, TroVE) have negligible actual reuse, mostly reuse trivial functions, and lose their gains under compute-matched baselines [M].
- **So measure actual reuse, not just library size.**

**Maturity**
- Research (program-synthesis domains).
- The **MDL scoring principle is the single most transferable idea** for "which patterns deserve to exist".

**Successor**
- DreamProver (2604.26311) applies wake-sleep lemma libraries to theorem proving in 2026 [M].

### 1.6 Agent Workflow Memory (AWM; Wang, Mao, Fried, Neubig, ICML 2025) [H prompt, M numbers]

**Formation**
- An LLM is given several trajectories judged successful, by ground truth or by an LLM `autoeval`.
- It is told to find "the repetitive subset of actions across multiple tasks" as workflows, "at least two steps".
- It replaces non-fixed elements with **descriptive variable names** and keeps invariant elements literal (`webarena/prompt/instruction.txt` [H]).
- Inputs are **deduplicated by `intent_template_id`** before induction (`induce_prompt.py` [H]). This is a support-diversity control: one template cannot dominate.

**Levels**
- Workflows can compose: later workflows build on earlier ones ("snowball" effect [R]).
- **Online mode:** induce from the test stream as you go.

**Validation**
- Autoeval judges only the source trajectories. There is no gate on the workflow itself.

**Pruning**
- In online mode the workflow memory is re-induced or replaced each time [R].

**Gains**
- +24.6% relative on Mind2Web and +51.1% relative on WebArena, with fewer steps.
- Cross-task, cross-website and cross-domain gains grow from +8.9 to +14.0 absolute as the train-test gap widens [M].

**Maturity**
- Research with code.
- **Steal:**
  - variable-ization: abstracting by replacing the parts that differ with named slots
  - template dedup before counting support

### 1.7 Agent Skill Induction (ASI; Wang, Gandhi, Neubig, Fried, COLM 2025) [M]

- Skills are induced as **programs** and **verified by execution** before admission.
- Reported +23.5pts over the static agent and +11.3pts over the text-skill variant, with 10.7–15.3% fewer steps. Skills transfer across websites, and incompatible ones get updated.
- **Lesson:** verifiable abstractions beat prose abstractions.
- **Harness analog:** prefer skills that are scripts or hooks with tests over prose rules wherever the procedure is mechanical.

### 1.8 ReasoningBank (Ouyang et al., Google, ICLR 2026) [H prompt, M numbers]

**Formation**
- After each task, an LLM judge labels the trajectory success or failure.
- A separate extraction prompt then distills **at most 3 memory items**. The success prompt asks "why it succeeded"; the failure prompt asks for "lessons / strategies to prevent".
- The extraction prompt instructs: "Prefer concrete, actionable procedures over abstract principles. Do not embed specific product names, queries, or literal string contents" (`WebArena/prompts/memory_instruction.py` [H]).

**Schema: Title, Description, Content**
- Title is the name.
- Description is "one sentence summary describing **when or when NOT** to use".
- Content is 1–3 sentences.

**Levels**
- Flat items. The paper observes that items **mature over time**, from procedural/execution-level ones to compositional strategies such as "cross-reference requirements, reassess options" [M].
- MaTTS (memory-aware test-time scaling) runs parallel or sequential rollouts per task and uses **contrast between them** to extract better memories [M].

**Retrieval and validation**
- Embedding retrieval of top-k items.
- Validation is end-task success only.

**Pruning**
- None in the core paper. The memory grows append-only [M/R].

**Gains**
- Beats raw-trajectory and success-only memories on WebArena, Mind2Web and SWE-Bench-Verified, with fewer steps [M].
- **Failures are a first-class source of abstractions.**

**Maturity**
- Early-stage, as BLUEPRINT already says. Code is released (Apache-2.0).

### 1.9 ACE: Agentic Context Engineering (Zhang et al., Stanford/SambaNova, 2510.04618) [H code, H README numbers]

**Roles**
- The **Generator** solves tasks and cites the playbook `bullet_ids` it used.
- The **Reflector** tags each cited bullet `helpful`, `harmful` or `neutral` and extracts new insights. It runs on correct answers too.
- The **Curator** emits **delta operations** (new or updated bullets), never full rewrites.

**Levels**
- A sectioned playbook, with lines in the form `[sec-00001] helpful=4 harmful=1 :: content` (`core/bulletpoint_analyzer.py` [H]).
- Sections such as strategies, formulas and common mistakes act as a shallow 2-level hierarchy.

**Pruning and dedup ("grow-and-refine")**
- `BulletpointAnalyzer` embeds the bullets, groups any pair with cosine ≥ **0.90** (the default `bulletpoint_analyzer_threshold`), and asks an LLM to merge each group, summing the helpful/harmful counts [H].
- Harmful-dominant bullets can be removed.

**Validation**
- Execution signals (code ran, API errors) plus labels when available.
- There is no explicit held-out gate in the core loop.

**Gains** (README [H])
- +10.6% on AppWorld agent tasks. It matches the top production GPT-4.1 agent on average and beats it on test-challenge, using a smaller open model.
- +8.6% on finance (FiNER, XBRL).
- Offline AppWorld: −82.3% latency and −75.1% rollouts versus GEPA.
- Online FiNER: −91.5% latency and −83.6% token cost versus Dynamic Cheatsheet.

**Caveat**
- 2605.12978 includes ACE among the consolidators whose utility degrades under continuous updating [M]. Gate it.

**Maturity**
- Early-stage but the most harness-shaped design. Delta bullets with counters is exactly BLUEPRINT's "small itemized changes".

### 1.10 Step-Back prompting (Zheng et al., ICLR 2024) [M]

- **What it does:** abstraction *at inference*. The model first asks itself a higher-level question ("what principle or concept governs this?"), answers it, then reasons on the original question grounded in that principle.
- **Gains:** PaLM-2L improved +7% on MMLU Physics, +11% on Chemistry, +27% on TimeQA (v1 says 34%) and +7% on MuSiQue.
- **Maturity:** mature as a prompt pattern.
- **Harness use:** when retrieving patterns, first generate the step-back query (the principle-level intent), then retrieve at L2/L3 by that query, not only by surface task text. This is how abstractions get *matched* across tasks with different surfaces.

### 1.11 Analogical prompting (Yasunaga et al., ICLR 2024) [R]

- The model **self-generates** relevant exemplars and high-level knowledge ("recall related problems, then solve") instead of retrieving fixed few-shots.
- It beat 0-shot CoT and manual few-shot on GSM8K, MATH and Codeforces [R].
- **Harness use:** cheap fallback when the pattern store has no match. Mark the result as `self_generated` and do not store it as an abstraction without a gate. SkillsBench shows that self-authored procedures are not reliably useful.

### 1.12 RAPTOR (Sarthi et al., ICLR 2024) [H code, R numbers]

**Formation**
- Embed the chunks, reduce with UMAP (dim 10), and cluster with a **Gaussian mixture with BIC-selected k** and soft assignment (`threshold = 0.1`, so a chunk can sit in several clusters).
- Clustering runs in two passes, global then local (`cluster_utils.py` [H]).
- Each cluster gets an LLM summary, and this recurses until there is one root.

**Levels and retrieval**
- An explicit tree: leaves are raw chunks and each level up is a summary.
- Retrieval runs over the "collapsed tree", meaning all levels are searched together. That lets a query hit whichever granularity fits.

**Validation and pruning**
- Neither exists. It is an index rebuild, not learning.

**Gains**
- +20% absolute on QuALITY with GPT-4 over the prior best [R; could not re-verify today].

**Maturity**
- Mature as a technique, and RAPTOR-style trees ship in several RAG frameworks.
- **Steal:**
  - soft clustering, since a pattern can belong to multiple parents
  - BIC to pick the number of clusters
  - multi-level retrieval

### 1.13 GraphRAG (Edge et al., Microsoft 2024) [M]

- **How it works:** extract an entity/relation graph, then run **hierarchical Leiden** community detection recursively. Each level is a full partition. Summaries are written bottom-up, leaf communities first, and parents are summarized from their children's summaries.
- **What it is for:** "global sensemaking" queries, answered map-reduce style over the community summaries. The paper reported substantial comprehensiveness and diversity win rates over vector RAG [R: about 70–80%].
- **Cost:** indexing is expensive. LazyGraphRAG defers summarization to query time; DRIFT search starts from communities and drills down [M].
- **Maturity:** mature but costly. BLUEPRINT already restricts it to multi-hop entity questions.
- **Steal:** the "partition each level fully, summarize children into parents" invariant for the pattern hierarchy.

### 1.14 MemGPT / Letta (Packer et al. 2023, Letta 2024–26) [M]

**Levels**
- An OS-style memory hierarchy:
  - **core** memory blocks, always in context, editable by the agent with tools
  - **recall** memory, the searchable conversation history
  - **archival** memory, an unbounded vector/KV store

**Formation**
- The agent itself pages information between tiers via function calls.
- **Sleep-time compute** (Apr 2025): a second agent consolidates and reorganizes memory during idle time, cutting test-time compute up to about 5× without accuracy loss on GSM-Symbolic and AIME [M].
- Reported Feb 2026: "context repositories", which are git-backed memory [M, secondary only].

**Validation**
- None built in.
- 2605.12978 lists Letta among the consolidators whose quality degrades under continuous updating [M].

**Maturity**
- Product-mature as infrastructure. The consolidation quality is unproven.
- **Steal:**
  - tiering by *always-loaded / on-demand / archive*. This maps to CLAUDE.md (≤200 lines), skills/rules, and the knowledge store plus JSONL logs.
  - running consolidation off the critical path, as a scheduled "sleep" job

### 1.15 A-MEM (Xu et al., NeurIPS 2025) [H code, M paper]

**Formation**
- Each new memory becomes a Zettelkasten-style **note** with LLM-generated keywords, tags, a context description and an embedding.
- The top-k neighbors are retrieved, and an LLM decides `should_evolve` with the actions:
  - `strengthen`: add links and update tags
  - `update_neighbor`: rewrite the neighbors' context and tags in light of the new note

  (`memory_system.py` `process_memory` [H])
- There is a periodic `consolidate_memories` [H].

**Levels**
- Implicit: higher-order structure "emerges" through links and evolved tags rather than explicit layers.

**Validation and pruning**
- Neither is principled. LLM rewrites of old notes are exactly the failure mode 2605.12978 warns about.

**Gains and maturity**
- Beats MemGPT, MemoryBank and others on LoCoMo QA across 6 models [M].
- Research.
- **Steal:**
  - the link graph (pattern ↔ pattern "supports / refines / contradicts")
  - the evolution log (`evolution_history`)

  Do **not** let an LLM silently rewrite evidence-bearing notes.

### 1.16 SkillOpt (2605.23904, May 2026) and relatives [M]

**SkillOpt**
- A compact `skill.md` is "the sole trainable parameter" for a frozen agent.
- Scored trajectory rollouts lead to reflection-driven edits, and an edit is **accepted only if a held-out validation gate passes**.
- Reported gains over no-skill:
  - +23.5 in direct chat
  - +24.8 in the Codex loop
  - +19.1 in Claude Code
- Best or tied-best in all 52 (model × benchmark × harness) cells.
- Final skills are 379–1,995 tokens, built from **1–4 net accepted edits**.

**Self-Supervised Skill Optimization (2607.28777)**
- Removes the need for ground truth by using **pairwise comparisons of unlabeled executions** as the feedback signal [M].

**EvoSkill (2603.02766)**
- An Executor runs tasks, a Proposer diagnoses failures, and a Skill-Builder writes the skill.
- **Pareto-frontier selection on held-out validation**, with the model frozen.
- OfficeQA: Claude Code with Opus 4.5 went from 60.6% to 67.9%.
- SealQA: +12.1%, and those skills gave +5.3% zero-shot on BrowseComp [M].

**Other 2026 skill-evolution work**
- **EvoSkills** (2604.01687): surrogate testing that is information-isolated and needs no labels.
- **SkillOS** (2605.06614): learned skill curation.
- **Memento-Skills** (2603.18743): an RL-trained contrastive skill router.
- **Reward-aware execution gating** (2608.09168): gates skill use on *execution utility*, not on retrieval relevance.

**Maturity**
- The validation-gated variant is the most credible 2026 evidence that agents can improve their own skills. Note how small the accepted change set is.

### 1.17 Other 2025–2026 work on abstraction, consolidation and rule induction [M unless noted]

- **RIMRULE** (2601.00086, ACL 2026)
  - Distills if-then rules from **failure traces** of tool-using agents.
  - Candidate rules are **pruned and generalized under an MDL objective**, so a small library covers many failures.
  - Rules use a 5-field schema: domain, qualifier, action, strength, tool category.
  - Improves accuracy on held-out queries and on *unseen tools*, and is additive with fine-tuning.
  - A reviewer (Pith) says the headline claims outrun Table 3.
  - This is the closest published analog to "MDL scoring over agent logs".
- **Useful Memories Become Faulty** (Zhang et al., 2605.12978)
  - Utility under continuous LLM consolidation rises, then falls below the no-memory baseline.
  - The example is the GPT-5.4 ARC-AGI 54% figure in §0.
  - The same trajectories yield different memories under different update schedules.
  - Recommendation: **treat raw episodes as first-class and gate consolidation explicitly, not after every interaction**.
  - Methods tested: CLIN, AWM, Dynamic Cheatsheet, ACE, LangMem, Mem0, ProPlay and Letta.
- **Rethinking Continual Experience Internalization** (2606.04703)
  - Repeated internalization collapses performance; a secondary source reports 23.2% falling to 8.5% by iteration 3.
  - Principle-level experience is more durable than instance-level.
  - **Step-wise injection** (matched to intermediate decision states) beats global injection on long-horizon tool use.
- **Hippocam, "Use and Disuse"** (2610.12124, Oct 2026)
  - Organizes work as nested **intents**. A completed intent is condensed to outcome plus state.
  - **Recursive prefix consolidation** makes long-unused history progressively more abstract, while the originals stay recoverable.
  - Disuse alone does the forgetting, with no separate importance or time rules.
  - Success and failure feed back to reinforce, revise or extend.
  - This maps directly onto the harness's `intent` field.
- **HiSkill** (2607.25853)
  - A directed skill graph: high-level skill nodes plus executable action-template nodes.
  - Typed edges: decomposition, temporal transition, compatibility, support, recovery.
  - Built from successes (reusable patterns) and failures (failure modes and recovery).
  - Retrieves a compact task subgraph and uses fewer tokens.
- **SkillLens** (2605.08386)
  - A 4-layer skill graph: policies, strategies, procedures, primitives.
  - Adaptive granularity per task for cost.
  - **A good template for the harness's layer names.**
- **Survey: From Storage to Experience** (2605.06716)
  - Abstraction depth runs from shallow NL rules, to modular skeletons, to weights.
- **Dynamic Agent Skills lifecycle survey** (2607.10113)
  - Covers the creation, validation, evolution and retirement taxonomy.
- **IDEA** (ACL Findings 2025)
  - An abduction, then deduction, then induction loop for rule learning: hypothesize, test, refine.
- **HERO'S JOURNEY** (2606.02556)
  - Shows LLMs still struggle to induce rules that must drive dependent action sequences.
- **ARC / Chollet**
  - Intelligence is skill-acquisition efficiency. The **kaleidoscope hypothesis** says apparent novelty is recombination of a small set of reusable "atoms of meaning".
  - Two abstraction types:
    - **value-centric**: continuous, similarity- or embedding-based, like clustering
    - **program-centric**: discrete, structural, like Stitch or MDL
  - Chollet's proposed architecture is a growing library of reusable components with program search guided by learned intuition, which he is pursuing at Ndea.
  - ARC-AGI-3 is interactive and was previewed in Jul 2025 [M]. Its full 2026 status is unverified here.
  - **Harness reading:**
    - Patterns should be few and recombinable.
    - Score them by how much *new* work they explain (compression), not by how often an LLM restates them.
    - Use both embedding clustering and discrete structural matching.

---

## 2. Cross-cutting comparison

| System | Formation criterion | Levels | Validation | Pruning | Maturity |
|---|---|---|---|---|---|
| Generative Agents | importance-sum trigger (150) → focal Qs → insights with evidence | tree/DAG of thoughts | none per item | recency decay (rank only) | pattern mature |
| Reflexion | failure → verbal reflection | 1 (per task) | next trial | window | mature (retry) |
| ExpeL | success/fail contrast → ADD/EDIT/AGREE/REMOVE | rules + exemplars | downstream only | **vote counter, drop at 0** | research |
| Voyager | critic-verified code | compositional calls | execution critic | versioning only | pattern mature |
| DreamCoder/Stitch/LILO | **MDL / compressive utility** | deep function library | MDL plus task solve | re-refactor | research |
| AWM | repeated sub-sequences with slots, template-deduped | composable workflows | autoeval on sources | re-induce | research |
| ASI | programs, **execution-verified** | composable | execution | update on mismatch | research |
| ReasoningBank | ≤3 items per trajectory, success *and* failure; when/when-not | flat (matures) | LLM judge | none | early |
| ACE | delta bullets plus helpful/harmful tags | sectioned playbook | execution signals | **counters plus 0.90 dedup merge** | early |
| Step-Back / Analogical | inference-time principle / self-exemplar | ephemeral | none | n/a | mature (prompt) |
| RAPTOR | GMM+BIC soft clusters → summaries | explicit tree | none | rebuild | mature |
| GraphRAG | Leiden hierarchy → bottom-up summaries | community levels | none | rebuild | mature, costly |
| Letta | agent-paged tiers plus sleep-time consolidation | core/recall/archival | none | agent edits | product |
| A-MEM | note plus link plus neighbor evolution | emergent graph | none | none | research |
| SkillOpt / EvoSkill | reflection edits, **held-out gate / Pareto** | single skill / skill set | **held-out** | reject at gate | best 2026 evidence |
| RIMRULE | failure → rules, **MDL prune** | rule library | held-out plus unseen tools | MDL | research |
| Hippocam | intent completion → recursive consolidation | nested intents | outcome feedback | **disuse → more abstract** | very new |

**Criteria actually used, ranked by evidence for held-out benefit:**
1. **Held-out utility gate**: SkillOpt, EvoSkill, the ASI execution check.
2. **Compression/MDL**: DreamCoder, Stitch, RIMRULE.
3. **Contrastive success/failure evidence**: ExpeL, ReasoningBank, MaTTS.
4. **Support diversity across tasks**: AWM template dedup, AWM cross-domain results.
5. **Vote and frequency counters**: ExpeL, ACE.
6. **LLM judgment alone**: A-MEM, Letta, Generative Agents. This is the weakest; 2605.12978 shows it degrades.

---

## 3. Design implications for the harness's layered patterns

Proposed layers, borrowing SkillLens's names and BLUEPRINT's tiers:

| Layer | What it is | Where it lives | Who may write it |
|---|---|---|---|
| **L0 Episode** | raw event (intent/situation/meta), immutable | JSONL logs | hooks (Haiku) |
| **L1 Observation** | normalized, de-identified, typed event signature | derived JSONL | script |
| **L2 Insight** | condition→action→rationale+when-not, with evidence IDs | `patterns/insights.jsonl` | LLM proposes, script scores |
| **L3 Procedure/skill** | multi-step workflow with slots, or a script with tests | `skills/`, `.claude/rules/` | gate plus human |
| **L4 Principle** | cross-domain rule, few in number, recombinable | CLAUDE.md / shared principles §4 | human only |

**Invariants**
1. Each node at L(n) cites ≥ k children at L(n−1), as Generative Agents evidence pointers and GraphRAG full partitions do.
2. Raw L0 is never rewritten (2605.12978).
3. Promotion is upward only via a gate.
4. Demotion and expiry are automatic.
5. L3 and L4 changes are human-reviewed git commits.

---

## 4. Concrete algorithms (stdlib Python over JSONL)

Assume events look like this:

`{"id","ts","project","domain","intent","situation","meta":{"kind","generalizes_to"},"outcome":"success|fail|corrected|null","tokens","duration_s","tags":[...]}`

There are also `applied` events of the form `{"pattern_id","event_id","outcome"}`, written when a retrieved pattern is used.

### 4.1 Signature normalization (L0 → L1)

AWM-style variable-ization replaces the parts that differ with typed slots. Doing it with regex is cheap and deterministic.

```python
import re, hashlib
SLOTS = [(re.compile(r'(/[\w.\-]+)+'), '<PATH>'), (re.compile(r'\b[0-9a-f]{7,40}\b'), '<HASH>'),
         (re.compile(r'https?://\S+'), '<URL>'), (re.compile(r'\b\d+(\.\d+)?\b'), '<NUM>'),
         (re.compile(r'"[^"]{1,80}"'), '<STR>')]
def normalize(text):
    t = text.lower()
    for rx, tok in SLOTS: t = rx.sub(tok, t)
    return re.sub(r'\s+', ' ', t).strip()
def tokens(t): return re.findall(r'<\w+>|[a-z_]{3,}', t)
def sig(ev):  # discrete signature used for grouping
    return (ev['meta'].get('kind'), ev.get('outcome'), tuple(sorted(set(tokens(normalize(ev['intent'])))))[:8])
```

### 4.2 Candidate grouping without embeddings

1. Compute a MinHash over the token shingles of `intent + situation + meta.kind`.
2. Use LSH banding to find candidate pairs.
3. Confirm each pair with Jaccard ≥ τ, which plays the role of ACE's 0.90 cosine. Use a Jaccard of 0.5–0.6 on shingles.
4. Take union-find components as clusters.

All of this is stdlib (`hashlib`, `random`). If embeddings are available later, add RAPTOR-style soft membership.

```python
def shingles(ts, k=2): return {' '.join(ts[i:i+k]) for i in range(max(1, len(ts)-k+1))}
def minhash(sh, n=64):
    return [min(int(hashlib.blake2b(f'{i}:{s}'.encode(), digest_size=8).hexdigest(), 16) for s in sh) for i in range(n)]
def lsh_pairs(sigs, bands=16):
    r = len(next(iter(sigs.values())))//bands; buckets = {}
    for eid, m in sigs.items():
        for b in range(bands): buckets.setdefault((b, tuple(m[b*r:(b+1)*r])), []).append(eid)
    return {(a, c) for ids in buckets.values() for i, a in enumerate(ids) for c in ids[i+1:]}
```

### 4.3 MDL / compression scoring of a candidate pattern

This is the Stitch-style compressive utility, approximated two ways.

**(a) Exact token MDL over a cluster.** Represent pattern P as a token template with slots.

`gain(P) = Σ_{e covered} (len(e) − (1 + len(slot_fillers_e))) − (len(P) + λ·|slots|)`

Keep P only if `gain > 0` and it beats the alternative of splitting the cluster. Choose greedily, one pattern at a time, re-encoding the corpus after each choice (as Stitch does).

**(b) Compressor proxy, which needs no template.** Use `zlib`/`lzma` as the description-length oracle. The **normalized compression distance** and **conditional compression gain** are:

```python
import zlib
C = lambda b: len(zlib.compress(b, 9))
def ncd(x, y):
    cx, cy, cxy = C(x), C(y), C(x + b'\n' + y)
    return (cxy - min(cx, cy)) / max(cx, cy)
def mdl_gain(pattern_text, covered_texts):
    p = pattern_text.encode()
    raw = sum(C(t.encode()) for t in covered_texts)
    # cost of the corpus given the pattern = cost(pattern) + sum of conditional costs
    cond = sum(C(p + b'\n' + t.encode()) - C(p) for t in covered_texts)
    return raw - (C(p) + cond)        # bits (bytes) saved; >0 means the pattern pays for itself
```

Use `ncd` for clustering (it needs no embeddings) and `mdl_gain` to rank or admit L2 candidates. A pattern supported by one episode gets about zero gain, which is DreamCoder's built-in guard against single-use "libraries" (the Berlot-Attwell failure).

### 4.4 Support × utility × spread × stability (the convergence score)

For a pattern P with covered episodes E_P and applied events A_P:

- **support** `s = |E_P|`, after **template dedup** (AWM). Count at most one episode per `(project, intent-signature)` per day, so one long session cannot inflate support.
- **spread**: the Shannon entropy of `project` and of `domain` over E_P, normalized by `log(#distinct)`. Also count distinct `meta.generalizes_to` values. **Cross-task convergence** means high support *and* spread ≥ 0.5 across ≥ 3 projects or domains.
- **utility** (lift with uncertainty): from A_P versus matched non-applied episodes with the same signature:
  `lift = p̂(success | applied) − p̂(success | not applied)`.
  Use the **Wilson lower bound** on each rate, or a Beta(1,1) posterior and `P(lift > 0)`. This is ExpeL's counters, made statistically honest.
- **corrections**: the user-correction rate when P is applied versus not. This should be negative, since corrections are BLUEPRINT's strongest real signal.
- **cost delta**: the token and time deltas (ACE and ReasoningBank both report step reduction).
- **stability**: split E_P into time halves; P must have `lift > 0` in both (a temporal holdout).
- **compression**: the `mdl_gain` from §4.3.

```python
import math
def wilson_lb(k, n, z=1.96):
    if n == 0: return 0.0
    p = k/n; d = 1 + z*z/n
    return (p + z*z/(2*n) - z*math.sqrt(p*(1-p)/n + z*z/(4*n*n))) / d
def entropy_norm(xs):
    from collections import Counter
    c = Counter(xs); n = sum(c.values())
    if len(c) < 2: return 0.0
    return -sum(v/n*math.log(v/n) for v in c.values()) / math.log(len(c))
def score(P):
    s = P['support']; spread = entropy_norm(P['projects'])
    lift_lb = wilson_lb(P['succ_app'], P['n_app']) - (P['succ_base']/max(1, P['n_base']))
    comp = max(0.0, P['mdl_gain']) / (1 + P['pattern_len'])
    return math.log1p(s) * (0.5 + spread) * max(0.0, lift_lb + 0.05) * (1 + comp) * P['recency']
```

**Promotion thresholds** (starting defaults; tune them on the logs):

| Promotion | Requirements |
|---|---|
| L1 → L2 | s ≥ 3 and `mdl_gain > 0` |
| L2 → L3 | s ≥ 5, spread ≥ 0.4, `lift_lb > 0` over n_app ≥ 5, and stable in both halves |
| L3 → L4 | ≥ 3 projects, ≥ 2 domains, passes the eval gate in each domain, and a human approves |

### 4.5 Reflection-tree construction (Generative-Agents × RAPTOR, deterministic skeleton)

1. **Trigger.** Keep an accumulator `Σ importance` of new L0 events since the last reflection, where importance is `fail = 3`, `corrected = 4`, `success = 1`, and `mishap = 5`. Fire when it is ≥ θ (start θ at 30 for one user; GA used 150 on a 1–10 scale). Run it as a scheduled **"sleep" job** (Letta), never inline.
2. **Focal questions.** Pick the top-3 clusters (§4.2) by Σ importance that contain new events. Each is a focal point.
3. **Insight proposal** (Haiku or Sonnet). For each focal cluster, pass ≤ 20 episodes, with **success and failure contrasted** (ExpeL, ReasoningBank). Ask for ≤ 3 items in the schema `{condition, action, rationale, when_not, evidence:[ids]}`. Reject any item whose `evidence` IDs are not in the input, or that has fewer than 2 IDs.
4. **Scoring and admission.** Apply §4.3 and §4.4. Merge the item into an existing L2 node when NCD < 0.35 or Jaccard ≥ 0.6 (an ExpeL AGREE, giving +1 support) instead of adding a duplicate.
5. **Recurse upward.** Cluster L2 nodes by NCD with soft membership (RAPTOR), where a node may have ≤ 2 parents. Propose an L3 parent only when a cluster has ≥ 3 children spanning ≥ 2 projects. The parent stores its child IDs, and **the parent's evidence is the union of its children's L0 evidence**, so it can always be re-scored from raw data.
6. **Retrieval.** Use the Step-Back pattern: generate the principle-level query, then score candidates at all levels together (RAPTOR collapsed tree) with

   `recency × relevance × importance`

   Here relevance is Jaccard or NCD and importance is the §4.4 score. Inject items step-wise at decision points, which beats global injection (2606.04703), via `PreToolUse`/`UserPromptSubmit` hooks and path-scoped rules.

### 4.6 Abstraction validation via eval gate (SkillOpt/EvoSkill-style)

```
for candidate edit Δ (one bullet, one skill section; ACE delta, never a rewrite):
    base  = run(eval_set_area, harness)            # cached
    trial = run(eval_set_area, harness + Δ)
    accept iff  mean(trial) ≥ mean(base)           # BLUEPRINT: "doesn't get worse"
           and  no per-task regression > ε on held-out split
           and  paired sign test p < 0.2 OR  Δ shrinks tokens/time at equal score
           and  Δ passes on ≥1 task outside its source domain   # cross-domain check (EvoSkill BrowseComp)
    keep a Pareto set over (score, cost, length)    # EvoSkill
```

Rules for the gate:
- Train and held-out tasks are disjoint. The episodes that generated Δ may never be in its held-out split.
- Expect few accepts: SkillOpt needed only 1–4 net edits.
- **Measure actual reuse.** Log `applied` events. An admitted L3 skill with zero real applications after N sessions is a "single-use library" and gets demoted (Berlot-Attwell).
- Verifier and judge run on a different model (BLUEPRINT §0.5).

### 4.7 Decay, demotion and pruning

Combine ExpeL's counter, ACE's helpful/harmful tags, GA's recency decay and Hippocam's disuse:

```python
def update(p, event, now):
    # vote counter (ExpeL): add=2, confirm=+1, contradict=-1 (-3 when layer at capacity)
    if event == 'confirm': p['votes'] += 1
    elif event == 'contradict': p['votes'] -= 3 if p['layer_full'] else 1
    elif event == 'helpful': p['helpful'] += 1
    elif event == 'harmful': p['harmful'] += 1
    p['last_used'] = now if event in ('helpful', 'harmful', 'confirm') else p['last_used']
def alive(p, now, half_life_days=42):
    age = (now - p['last_used']) / 86400
    recency = 0.5 ** (age / half_life_days)            # 6-week half-life ~ BLUEPRINT "N weeks"
    harm_ok = wilson_lb(p['helpful'], p['helpful'] + p['harmful']) >= 0.4 or p['helpful'] + p['harmful'] < 4
    return p['votes'] > 0 and harm_ok and recency > 0.1
```

When a pattern fails `alive`, apply these actions:

| Layer | Action |
|---|---|
| L2 | archive it, never delete. Keep the evidence IDs so it can be resurrected if support re-appears. |
| L3 / L4 | open a "retire?" PR for human review |

**Disuse abstraction (Hippocam).** When an L2 cluster has been unused for more than T days, collapse its children into the parent summary in the *active* index, but keep the children in the archive.

**Staleness check.** Re-score every L2/L3 node monthly from raw L0. If `lift_lb ≤ 0` over the latest window, or the cited files, tools or APIs no longer exist (check paths with `os.path.exists`, and check tool names against the current settings), mark it stale.

**Contradiction edges** (A-MEM links). When two nodes give opposite actions under overlapping conditions, link them `contradicts`. Retrieval must surface both, or the one with the higher `lift_lb`, and the pair is queued for human resolution.

### 4.8 Guardrails from the 2026 failure literature

- Never let the LLM rewrite an existing L2+ node in place. New text is a new version with `supersedes`, and the old version is kept (2605.12978, A-MEM risk).
- Consolidate on a schedule or trigger, never after every event (2605.12978).
- Cap the injected context. Prefer step-wise injection, and keep a few focused items rather than a mega-playbook (SkillsBench: focused 2–3-module skills beat comprehensive docs; BLUEPRINT's ≤200-line CLAUDE.md).
- Every self-generated L3 skill is quarantined until it passes the eval gate. Average self-generated skill value is about 0 (SkillsBench).
- Store failures as abstractions too (ReasoningBank, RIMRULE, HiSkill recovery edges). In the harness these come from mishaps and corrections.
- Defend against memory poisoning. Only harness-authored L0 events count as evidence, and text quoted from web pages or tool output is never an instruction-bearing pattern.

---

## 5. What is mature and what is still research (2026-10)

**Mature, safe to build on now**
- Tiered memory (always-loaded / on-demand / archive)
- Importance-triggered reflection with evidence pointers
- Recency×relevance×importance retrieval
- Execution-verified skills (Voyager, ASI)
- RAPTOR/GraphRAG hierarchical summaries for *document* corpora
- Step-Back for retrieval queries
- Held-out-gated prompt and skill optimization (GEPA, SkillOpt-style)

**Early-stage, pilot behind a gate**
- ACE delta playbooks with counters
- ReasoningBank failure-derived strategies
- AWM workflow induction
- EvoSkill Pareto selection
- RIMRULE MDL rule libraries
- Self-supervised pairwise feedback

**Research, or shown fragile**
- Autonomous continuous consolidation (A-MEM evolution, Letta sleep-time rewriting, any un-gated consolidator)
- Multi-iteration internalization
- In-context library learning claims of reuse
- Emergent hierarchy without explicit evidence links
- Weight-level internalization for a personal harness

**Bottom line for the harness:** implement §4.1–4.7 as a nightly stdlib script.
1. Hooks write L0.
2. The script clusters (NCD/MinHash) and scores (MDL, support, spread, Wilson lift, stability).
3. Haiku proposes L2 items with mandatory evidence IDs.
4. The script admits or merges them, applying counters and decay.
5. Candidates above the L3 threshold become ACE-style one-item PRs that must pass the area eval set (with a cross-domain check) before human review.
6. L4 stays human-written.

---

## Sources

Repos read (shallow clones, 2026-10-16):
- github.com/ace-agent/ace
- github.com/google-research/reasoning-bank
- github.com/joonspk-research/generative_agents
- github.com/LeapLabTHU/ExpeL
- github.com/zorazrw/agent-workflow-memory
- github.com/MineDojo/Voyager
- github.com/agiresearch/A-mem
- github.com/parthsarthi03/raptor

Papers (abstract or snippet level; links as found):
- ReasoningBank: https://arxiv.org/abs/2509.25140
- ACE: https://arxiv.org/abs/2510.04618 ; https://github.com/ace-agent/ace
- AWM: https://proceedings.mlr.press/v267/wang25bx.html ; https://arxiv.org/abs/2409.07429
- ASI: https://arxiv.org/abs/2504.06821
- ExpeL: https://ojs.aaai.org/index.php/AAAI/article/view/29936 ; https://arxiv.org/abs/2308.10144
- LILO: https://iclr.cc/virtual/2024/poster/18550 ; https://arxiv.org/abs/2310.19791
- Library learning critique: https://arxiv.org/abs/2410.20274 ; https://arxiv.org/abs/2504.03048 ; https://preview.aclanthology.org/ingest-eacl/2026.eacl-long.163.pdf
- DreamProver: https://arxiv.org/abs/2604.26311
- A-MEM: https://proceedings.neurips.cc/paper_files/paper/2025/hash/19909c36f51abc4856b4560aff3d36d6-Abstract-Conference.html
- SkillOpt: https://arxiv.org/abs/2605.23904 ; Self-Supervised Skill Optimization: https://arxiv.org/abs/2607.28777
- EvoSkill: https://arxiv.org/abs/2603.02766 ; EvoSkills: https://arxiv.org/abs/2604.01687 ; Memento-Skills: https://arxiv.org/abs/2603.18743 ; SkillOS: https://arxiv.org/abs/2605.06614 ; execution gating: https://arxiv.org/abs/2608.09168
- SkillsBench: https://arxiv.org/abs/2602.12670
- Useful Memories Become Faulty: https://arxiv.org/abs/2605.12978 ; https://dylanzsz.github.io/faulty-memory/
- Continual Experience Internalization: https://arxiv.org/abs/2606.04703
- Hippocam / Use and Disuse: https://arxiv.org/abs/2610.12124
- HiSkill: https://arxiv.org/abs/2607.25853 ; SkillLens: https://arxiv.org/abs/2605.08386
- Memory surveys: https://arxiv.org/abs/2605.06716 ; https://arxiv.org/abs/2512.13564 ; skills lifecycle survey: https://arxiv.org/abs/2607.10113
- RIMRULE: https://aclanthology.org/2026.acl-long.1599/ ; https://arxiv.org/abs/2601.00086
- IDEA: https://aclanthology.org/2025.findings-acl.698/ ; HERO'S JOURNEY: https://arxiv.org/abs/2606.02556
- Step-Back: https://proceedings.iclr.cc/paper_files/paper/2024/hash/592da1445a51e54a3987958b5831948f-Abstract-Conference.html
- GraphRAG: https://arxiv.org/abs/2404.16130
- Letta: https://letta.com/blog/memgpt-and-letta ; https://www.letta.com/blog
- Chollet / ARC: https://arcprize.org/history ; https://the-decoder.com/francois-chollet-on-the-end-of-scaling-arc-3-and-his-path-to-agi/

Recall-only [R], not re-fetched today (verify before external use):
- Generative Agents ablation details
- Reflexion 91% HumanEval
- Voyager 3.3×/15.3×
- DreamCoder and Stitch speedups
- RAPTOR +20% QuALITY
- GraphRAG win-rate magnitudes
- Analogical prompting results
