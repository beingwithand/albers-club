# Fan-out policy: when, and how many, parallel subagents (as of 2026-10-16)

Scope: how labs and practitioners decide **whether** to fan out to parallel agents and **how wide**, plus caps, safeguards and anti-patterns. The goal is a policy for `claude-harness` (orchestrator, web-research, verify, usage_guard).
Confidence tags: **[H]** primary source read in full; **[M]** primary source seen only through search snippets, or a strong secondary source; **[L]** single secondary or blog source, unverified.

## 0. Unreachable sources

The agent proxy returned 403 or DNS failure for the following. Their content below comes from search snippets only:
- cognition.ai and cognition.com (both "Don't build multi-agents" and "Multi-Agents: What's Actually Working")
- arxiv.org (every paper)
- research.google
- langchain.com
- developers.openai.com (Codex subagents)
- systima.ai
- xda-developers.com
- aident.ai

Fetched in full:
- anthropic.com/engineering (multi-agent research system, building effective agents, C compiler)
- claude.com/blog ("When to use multi-agent systems")
- code.claude.com docs: workflows, agents, sub-agents, agent-teams, costs
- platform.claude.com managed-agents multiagent-orchestration
- the bundled `workflow-authoring` skill, read locally

No Reddit or Hacker News threads surfaced, even with extended search. Practitioner evidence is therefore blog-level.

---

## 1. Sources and key claims

### Anthropic
- **How we built our multi-agent research system**, 2025-06-13. https://www.anthropic.com/engineering/multi-agent-research-system **[H]**
  - Effort scaling is written into the prompt:
    - simple fact-finding: 1 agent, 3–10 tool calls
    - direct comparisons: 2–4 subagents, about 10–15 calls each
    - complex research: more than 10 subagents with clearly divided responsibilities
  - Token cost: agents use about 4× the tokens of chat; multi-agent systems use about 15× the tokens of chat.
  - On BrowseComp, token usage alone explains about 80% of performance variance. Token usage, tool calls and model choice together explain about 95%.
  - The lead spawns 3–5 subagents in parallel, and each subagent calls 3+ tools in parallel. This cut time by up to 90% on complex queries.
  - Poor fit:
    - tasks that need shared context, or have many dependencies between agents
    - most coding ("fewer parallelizable parts than research")
    - anything not valuable enough to pay for the extra tokens
  - Failure modes observed:
    - spawning 50 subagents for simple queries
    - endless searching for sources that don't exist
    - agents distracting each other with updates
    - duplicated work from vague briefs
  - The lead waits synchronously for each batch, so one slow subagent stalls the run.
  - Evaluation: one LLM judge call scores 0–1 plus pass/fail on a rubric (factual accuracy, citation accuracy, completeness, source quality, tool efficiency). Start with about 20 queries.
- **When to use multi-agent systems (and when not to)**, claude.com/blog, 2026-01-23. https://claude.com/blog/building-multi-agent-systems-when-and-how-to-use-them **[H]**
  - Only three situations reliably win:
    1. context pollution
    2. genuinely parallel subtasks (this buys *thoroughness more than speed*)
    3. specialization (tool selection or focus)
  - Cost is "typically 3–10× more tokens than single-agent for equivalent tasks". Parallel runs often take *longer* in total.
  - Checklist before adding agents:
    1. a genuine constraint exists
    2. decomposition follows **context**, not problem type
    3. clear verification points exist
  - Signals that you need it:
    - a subtask produces more than about 1,000 tokens that are mostly irrelevant to the main task
    - more than 15–20 tools
    - independent subtasks
  - Anti-pattern: problem-centric splits (feature agent / test agent / review agent). They create a telephone game, and in one experiment the agents "spent more tokens on coordination than on actual work". Instead, the agent that writes a feature also writes its tests.
  - The **verification subagent** is the pattern that works best, because it sidesteps the telephone game.
    - Guard against "early victory": give concrete criteria and require "MUST run the complete test suite".
    - Cap the verification loop (the example uses 3 attempts).
  - Teams spent "months" on multi-agent architectures that better single-agent prompting matched.
- **Building effective agents**, 2024-12-19. https://www.anthropic.com/engineering/building-effective-agents **[H]**
  - Parallelization comes in two forms:
    - sectioning: independent subtasks, for speed
    - voting: the same task run N times, for confidence
  - Orchestrator-workers fits when the subtasks can't be predicted in advance.
  - Evaluator-optimizer fits when the criteria are clear and iteration measurably helps.
  - Start simple.
- **Building a C compiler with a team of parallel Claudes**, 2026-02-05. https://www.anthropic.com/engineering/building-c-compiler **[H]**
  - 16 agents, about 2,000 sessions, about $20k.
  - Parallelism worked while there were many independent failing tests (one agent per test, claimed through lockfiles).
  - It **collapsed on "one giant task"** (the Linux kernel build): "every agent would hit the same bug … overwrite each other's changes."
  - The fix was an oracle (GCC) that split the giant task into independent pieces.
  - "The task verifier must be nearly perfect, otherwise Claude will solve the wrong problem."
  - Harness rules:
    - keep test output to a few lines; log details to files; precompute summaries
    - deterministic `--fast` 1%/10% sampling per agent, because of "time blindness"

### Claude Code product docs (code.claude.com, read 2026-10-16) **[H]**
- **Subagents** (`/docs/en/sub-agents`)
  - Up to **20 concurrent** subagents per session by default (`CLAUDE_CODE_MAX_CONCURRENT_SUBAGENTS`). There is no limit on the total over a session.
  - Nesting is allowed **up to 3 levels** by default since v2.1.219 (`CLAUDE_CODE_MAX_SUBAGENT_SPAWN_DEPTH`; set it to 1 to turn nesting off).
  - Stay in the main conversation when:
    - there's frequent back-and-forth
    - several phases share significant context
    - the change is quick
    - latency matters (a fresh subagent has to re-gather context)
  - Use a subagent when the output is verbose, tools need restricting, or the work is self-contained and can return a summary.
  - Many subagents returning detailed results fill the parent's context.
  - Model order: per-invocation → frontmatter → `CLAUDE_CODE_SUBAGENT_MODEL` → session model. `..._FORCE=1` pins every subagent.
- **Run agents in parallel** (`/docs/en/agents`)
  - Choose by three questions: who coordinates, whether workers need to talk to each other, and whether they touch the same files (if so, use worktrees).
  - `/batch` splits one large change into **5–30 worktree-isolated subagents**. How it picks the count isn't documented; it's a model judgment inside a bundled skill **[M]**.
- **Agent teams** (`/docs/en/agent-teams`; experimental)
  - "Start with **3–5 teammates**."
  - "If you have 15 independent tasks, 3 teammates is a good starting point."
  - "**5–6 tasks per teammate**."
  - "Three focused teammates often outperform five scattered ones."
  - Token cost scales linearly with team size; about **7×** a standard session when teammates run in plan mode (costs page).
  - Best uses:
    - research and review
    - debugging with competing hypotheses (adversarial debate, because one investigator anchors on the first theory)
    - cross-layer work with separate file ownership
  - Poor fit: sequential work, same-file edits, many dependencies.
  - Teammates can't nest. Start with read-only research or review before attempting parallel implementation.
- **Dynamic workflows** (`/docs/en/workflows`)
  - Size guideline `workflowSizeGuideline`:
    - small: fewer than 5 agents (the Pro default)
    - medium: fewer than 10 agents (the default)
    - large: fewer than 50 agents
  - Runtime limits:
    - 16 concurrent agents by default (`CLAUDE_CODE_WORKFLOW_MAX_CONCURRENT_AGENTS`, settable from 1 to 256)
    - 4,096 items per `parallel()`/`pipeline()` call
    - **1,000 agents per run** as a hard backstop
  - A "**Large workflow**" warning appears above **25 agents or a projected 1.5M tokens**.
  - Pilot on a small slice first.
  - A run pauses at the usage limit and resumes after the reset (twice at most, and only if the reset is within 24 hours).
  - Siblings share the prompt cache when model, effort, agent type, tools, schema and cwd all match. A stagger of up to 5 s lets them read the first agent's cache.
  - Turning ultracode on removes the large-run warning and the concurrent-subagent cap, and draws limits down faster.
- **Bundled `workflow-authoring` skill** (read locally)
  - Patterns:
    - adversarial verify (N=3 refuters, killed by majority, "default to refuted if uncertain")
    - perspective-diverse verify (distinct lenses beat N identical refuters)
    - judge panel (N angles, then scored, then synthesized with grafts)
    - loop-until-dry (stop after K=2 consecutive empty rounds; dedupe against *seen*, not *confirmed*)
    - multi-modal sweep
    - completeness critic
    - no silent caps (log what was dropped)
  - Default to `pipeline()` and use barriers only for cross-item dedup or early exit.
  - Scaling heuristic: "find any bugs" means a few finders and single-vote verification; "thorough audit" means a larger pool, 3–5 vote adversarial passes and a synthesis step.
  - Use `budget.total` to size the fleet, e.g. `floor(total/100k)`.
- **Costs** (`/docs/en/costs`)
  - Every subagent and workflow agent sends its own requests.
  - Subagent and teammate caches get a 5-minute TTL by default (`subagentPromptCacheTtl` can be set to 1h).
  - Advice: use Sonnet for teammates, keep spawn prompts focused, and shut teammates down when they finish.
- **Managed Agents multiagent orchestration** (platform.claude.com, beta `multiagent_20261001`) **[H]**
  - Delegation is one level deep, with at most **25 child threads** per session.
  - A **session budget** caps spend, workflow runs included.
  - Patterns: parallelization, specialization, and **escalation via an advisor model**.
  - Recommended system-prompt rule: "When asked to review more than a few [items], start a workflow run … review one or two yourself, without a run."
  - Plus three more rules:
    - one agent failing must not fail the run; list what wasn't covered
    - a run time limit
    - a plan-first statement of phases and agent counts

### Cognition
- **Don't build multi-agents**, 2025-06 (Walden Yan). **[M]**, from snippets; the site was unreachable.
  - Principles: share full context and traces, not just messages; actions carry implicit decisions, and conflicting decisions produce bad results.
  - Recommends a single-threaded linear agent plus context compression.
- **Multi-Agents: What's Actually Working**, 2026-04-22. https://cognition.com/blog/multi-agents-working **[M]**
  - The warnings still hold for parallel-*writer* swarms.
  - What works: **writes stay single-threaded, and extra agents add intelligence, not actions**. Examples:
    - a clean-context reviewer (secondary sources: about 2 bugs per PR, about 58% of them severe **[L]**)
    - a frontier "smart friend" or advisor for a weaker primary
  - Most practical setups are limited to read-only subagents (web or code search).
  - Devin Fusion (2026-09) pairs a planner and reviewer with a cheaper executor **[L]**.

### Other labs and frameworks
- **OpenAI, A practical guide to building agents** (2025). **[M]**
  - Maximize a single agent first.
  - Split only for (a) complex conditional logic or (b) tool overload, where better descriptions no longer fix selection (one summary says 15+ tools **[L]**).
  - Two patterns: manager (agents as tools) or decentralized handoffs.
- **OpenAI Codex subagents** docs. **[M]**
  - `agents.max_threads` defaults to **6**; `agents.max_depth` defaults to **1**.
  - Codex spawns subagents only when explicitly asked.
  - Warning: raising depth "can turn broad delegation instructions into repeated fan-out, which increases token usage, latency, and local resource consumption."
- **Google ADK** (community guides). **[L]**
  - ParallelAgent for independent subtasks, SequentialAgent when step N needs step N−1, LoopAgent always with `max_iterations`.
  - Typical shape: parallel fan-out followed by sequential synthesis.
- **LangChain, How and when to build multi-agent systems**, 2025-06-16 (Harrison Chase). **[M]**
  - Context engineering is the core problem.
  - **Read-heavy multi-agent systems are much easier than write-heavy ones**, so let subagents gather and one agent write.
- **LangGraph**. **[M]**
  - `Send()` map-reduce into an append-only reducer key, then an aggregator node.
  - No built-in fan-out ceiling: set `max_concurrency` yourself.
  - `recursion_limit` defaults to 25 super-steps.

### Research papers
- **Towards a Science of Scaling Agent Systems**, Kim et al., Google Research / DeepMind / MIT, arXiv 2512.08296; blog 2026-01-28. **[M]**
  - 180 configurations tested.
  - Multi-agent **helps on parallelizable tasks and hurts on sequential ones**. Blogs report up to +81% on parallel finance tasks and −39 to −70% on sequential planning **[L]** for the exact numbers.
  - **Error amplification:** independent agents 17.2×, centralized coordination 4.4×. Centralized validation contains errors.
  - **Capability saturation:** gains shrink or turn negative once the single-agent baseline exceeds about 45%.
  - Tool-heavy tasks pay a disproportionate coordination tax.
  - A predictive model picks the best architecture for 87% of unseen tasks.
- **Why Do Multi-Agent LLM Systems Fail?** (MAST), Cemri et al., NeurIPS 2025, arXiv 2503.13657. **[M]**
  - 1,642 annotated traces across 7 frameworks.
  - Failures cluster into specification/system design, inter-agent misalignment, and task verification. They stem mostly from *system design*, not model limits.
- **Debate or Vote**, Choi et al., NeurIPS 2025, arXiv 2508.17536. **[M]**
  - **Majority voting accounts for most of the gains attributed to multi-agent debate.** Debate alone doesn't raise expected correctness (martingale argument).
  - Earlier: Huang et al. 2023 found debate underperforms self-consistency at equal response counts.
  - Takeaway: at equal compute, prefer independent samples plus a vote over debate rounds.
- **Rethinking Mixture-of-Agents** (Self-MoA), Li et al., TMLR 2026, arXiv 2502.00674. **[M]**
  - Ensembling repeated samples from **one strong model** beats mixing different models: +6.6% on AlpacaEval 2.0 and +3.8% on average.
  - Mixing in weaker models lowers average quality. Diversity helps only if the aggregator/selector is good enough (the 2026 rebuttal "When Agents Disagree").
- **Self-consistency early stopping (ESC)**, Li et al., ICLR 2024. **[M]**
  - Stop sampling once a window of answers agrees.
  - Cuts samples by 34–84% at comparable accuracy (GSM8K −80%, MATH −34%).
  - Adaptive Consistency stops once the majority is statistically decided.
- **Best-of-N and verifier limits.** **[M]**
  - Coverage (pass@k) grows log-linearly with N (Brown et al. 2024).
  - With an *imperfect* verifier, returns diminish, especially when false positives dominate (Stroebl et al. 2024).
  - Large N **reward-hacks** a learned verifier (ICML 2025 "Is Best-of-N the best of them?").
  - In one program-synthesis study, the learned verifier peaked around N=512 and then fell, while an **executable sound verifier kept climbing** (preprint).
  - Takeaway: scale N only as far as the verifier is trustworthy, and prefer executable checks.
- **Multi-Agent Verification (BoN-MAV)**, Lifshitz, McIlraith, Du, arXiv 2502.20379. **[M]**
  - Scaling the *number of verifiers* (off-the-shelf "aspect verifiers", each checking a different aspect, selected by approval count) is a new axis.
  - It scales better than self-consistency or a single reward model, and weak verifiers can improve strong generators.
- **Replacing Judges with Juries (PoLL)**, Verga et al., Cohere 2024. **[M]**
  - A panel of smaller judges from **disjoint model families** beats a single large judge, has less intra-model bias, and costs about 7× less.
  - RoPoLL (ICML 2026): simple averaging is vulnerable to one systematically bad judge, so use robust aggregation such as the median.
- **Self-preference bias.** **[M]**
  - arXiv 2508.06709: judges (GPT-4o, Claude 3.5 Sonnet) score their own and same-family outputs higher.
  - Counterpoint, Chen et al. 2025 (arXiv 2504.03846): a *weaker* cross-family judge can lose more accuracy than the bias it removes. Judge accuracy tracks the judge's own task accuracy (r≈0.7–0.9).
- **LLM×MapReduce**, Zhou et al., ACL 2025. **[M]**
  - Chunked map-reduce loses information through inter-chunk *dependency* and *conflict*.
  - Fixes: a structured map output protocol plus in-context confidence calibration at reduce time.

### Practitioner evidence (blogs; no HN/Reddit threads found) **[L]**
- Measured Claude Code fan-outs used **2.6–5.9×** the input tokens of doing the same work sequentially and were reportedly *never faster* on the timed tasks (Systima, via secondary sources).
- Another run: 121k tokens direct versus 513k with 2 subagents.
- Mechanism: every subagent pays the bootstrap floor again (about 33k tokens of system prompt, tools and CLAUDE.md), plus summaries flowing back to the parent (about 60k after 10 rounds of 3 agents).
- XDA: five subagents burned a Pro or Max 5-hour window in under an hour.
- Pinning subagents to Haiku or Sonnet cut the subagent line item by about 30–37%.
- "Parallel agents buy wall-clock time, not tokens."
- Dramatic figures (887k tokens/min, $47k incidents) come from SEO content and are unverified.

---

## 2. Decision dimensions (what to score before fanning out)

| Dimension | Pushes toward fan-out | Pushes toward one agent | Key source |
|---|---|---|---|
| **Independence / coupling** | Subtasks share no state; no writes, or writes to disjoint files | Sequential dependencies, a shared mutable state, one "giant task" | Anthropic research/blog, C compiler, Kim et al. |
| **Read vs write** | Read-only gathering (search, audit, review) | Parallel writers making implicit style or design decisions | LangChain, Cognition 2025/2026 |
| **Breadth** | Many items (more than about 5 files, sources or contracts) or many angles | One narrow question | Anthropic effort scaling, Managed Agents prompt |
| **Context pressure** | A subtask produces more than about 1k tokens of mostly-irrelevant output; the parent context is already above 50% | Phases share significant context | claude.com blog, sub-agents doc |
| **Specialization / tools** | 15–20+ tools, or distinct tool or permission sets | Small tool set | claude.com blog, OpenAI guide |
| **Stakes / need for confidence** | Wrong answer is costly, so verification fan-out (votes, lenses) pays | Reversible, low-stakes work | Building effective agents (voting), workflow skill |
| **Difficulty vs capability** | The single agent is clearly below about 45% success on this kind of task, or stuck | The single agent already does well (saturation) | Kim et al. |
| **Verifier quality** | An executable or sound check exists, so a larger N is safe | Only an LLM judge, so keep N small; scale verifiers, not samples | BoN literature, C compiler |
| **Diversity need** | Unclear root cause, wide design space, anchoring risk | A single obvious approach | Agent-teams doc (competing hypotheses), judge panel |
| **Latency** | Wall-clock matters and the work is truly parallel | Quick change; subagent startup cost dominates | sub-agents doc, Systima |
| **Budget / usage** | Plenty of headroom in the 5-hour and 7-day windows; value justifies 3–15× tokens | Usage at 70% or more, or low value | Anthropic 15×, costs doc, usage_guard |

## 3. Concrete thresholds and rules of thumb (with sources)

- **1 agent, 3–10 tool calls** for simple fact-finding. **2–4 subagents, 10–15 calls each** for comparisons. **10+** for complex research. (Anthropic 2025-06)
- Spawn **3–5 in parallel** per batch. (Anthropic 2025-06)
- Teams: **3–5 teammates** with **5–6 tasks each**; for 15 tasks, 3 teammates. (agent-teams doc)
- Workflow size: **fewer than 5 / fewer than 10 / fewer than 50**. Warn above **25 agents or 1.5M tokens**. **16 concurrent**, **1,000 per run**. (workflows doc)
- `/batch`: **5–30** worktree units. (agents doc)
- Subagents: **20 concurrent**, **depth 3**. Codex: **6 threads, depth 1**. Managed Agents: **25 child threads, depth 1**.
- Fan out when a subtask produces **more than about 1k irrelevant tokens**, or the agent has **15–20+ tools**. (claude.com blog)
- Cost: **3–10×** (claude.com blog), **15×** chat (research system), **about 7×** for plan-mode teams, **2.6–5.9×** measured in Claude Code fan-outs. (practitioner)
- Verification: **3 refuters, majority kill**, defaulting to "refuted" when uncertain. **3–5 votes** for thorough audits. A verify→fix loop capped at **3 attempts**. (workflow skill, claude.com blog; harness: 2 retries)
- Loop-until-dry: stop after **2 consecutive rounds with nothing new**. (workflow skill, workflows doc)
- Self-consistency: stop early once a **window of samples agrees**, saving 34–84%. (ESC)
- Gains from multi-agent shrink once the single-agent baseline is **above about 45%**. (Kim et al.)
- Delegate for a handful of items or more, and do **1–2 items yourself**. (Managed Agents example prompt)

## 4. Fan-out patterns and when each fits

| Pattern | Shape | Fits | Avoid when |
|---|---|---|---|
| **Parallel search / multi-modal sweep** | N readers, each with a different angle, source tier or modality, then synthesis | Research, prior-art, "find everything" | The question is narrow (1 agent is enough) |
| **Map-reduce / pipeline over items** | Discover a list, one agent per item (pipeline, no barrier), then reduce | Audits, per-file review, migrations (worktrees), comparison tables | Items depend on each other; reduce needs a structured map schema plus conflict calibration (LLM×MapReduce) |
| **Ensemble / self-consistency / best-of-N** | N independent attempts at the same task, then vote or a verifier picks | Answers that can be checked or voted on (math, classification, extraction, code with tests) | No good verifier exists (reward hacking at large N); debate rounds add little over a vote |
| **Judge panel / design tournament** | N attempts from different angles, parallel judges, synthesis with grafts | Wide solution space: plans, designs, naming, architecture | Only one sensible approach exists |
| **Adversarial verification** | Per finding, 3 refuters, majority kill; or lens-diverse verifiers | Findings that look plausible but may be wrong (bugs, claims, citations) | Low stakes; "find anything" reviewers (over-engineering) |
| **Competing hypotheses** | N investigators, each with a theory, trying to disprove the others | Debugging with an unclear root cause; anchoring risk | Cause already localized |
| **Pipeline (sequential specialists)** | Step N consumes step N−1 | Fixed-order transforms (extract → translate → format) | Splitting by *problem type* on one context (the telephone game) |
| **Clean-context reviewer / advisor** | One writer plus one fresh-context reviewer or more capable advisor | Almost always for non-trivial writes; Cognition's main working pattern | — (cheap; this is the default "second agent") |
| **Parallel writers** | N agents editing code | Only with disjoint file ownership or worktrees **and** a near-perfect test oracle | Shared files or a "one giant task" (C compiler collapse) |

## 5. Caps and safeguards

1. **Width caps by tier:**
   - default ≤3 parallel
   - comparison 2–4
   - exhaustive ≤10 per batch
   - more than 10 only through a workflow with a stated agent count and user OK above 25 agents or 1.5M tokens
2. **Depth:**
   - keep nesting at 1 (orchestrator to workers)
   - set `CLAUDE_CODE_MAX_SUBAGENT_SPAWN_DEPTH=2` so workers can't spawn workers (the main thread counts as level 0; verify the semantics)
   - or remove `Agent` from worker `tools`
   - Codex and Managed Agents both default to depth 1
3. **Budgets:**
   - per-run token target (`budget.total`, workflow sizing `floor(total/100k)`)
   - `--max-budget-usd` for headless
   - Managed Agents session budget
   - pilot on a small slice first
4. **Model routing:**
   - set `model:` in every agent file; a subagent with no model inherits Opus
   - Haiku for mechanical work, Sonnet for workers, Opus for lead and verifier
   - consider `CLAUDE_CODE_SUBAGENT_MODEL=sonnet` as the fallback
   - keep identical model, effort, tools and cwd across siblings so they share the cache
5. **Briefs** state objective, output format/schema, sources/tools, boundaries, effort (call budget) and output path. This prevents duplicated work and "endless searching".
6. **Return small:** summary of 300 words or less plus file pointers. Big outputs go to files, not the parent context.
7. **Dedupe and aggregation:**
   - barrier only for cross-item dedup or early exit
   - dedupe against *seen*
   - robust aggregation (median or majority, not mean)
   - surface conflicts
8. **Early stopping:** loop-until-dry (K=2), ESC-style agreement windows, stop verification when 0 findings, cap fix loops at 2–3.
9. **Failure handling:** a null or failed agent never fails the run; list what wasn't covered ("no silent caps"); stall and time limits.
10. **Usage-aware throttling:** graduated by 5-hour and 7-day usage (see §7). Workflows pause at the usage limit, but subagents and teams do not.

## 6. Anti-patterns

- Fanning out a simple query (Anthropic's "50 subagents" failure); fanning out because the feature exists.
- Problem-type splits on a single context (feature, test and review agents), which cause the telephone game and coordination costing more than the work.
- Parallel writers on shared files or one giant coupled task, which overwrite each other's work.
- Independent agents with no central validation, which amplify errors 17× versus 4.4× centralized.
- Debate rounds instead of votes, or mixing weaker models into an ensemble "for diversity" (it lowers quality).
- Large best-of-N against a learned or LLM judge, which reward-hacks. Same-family self-grading (positive skew), or switching to a much *weaker* cross-family judge.
- "Find anything" adversarial reviewers, which over-engineer.
- Vague briefs, which cause duplicated work and endless searching. Agents chatting with each other excessively.
- Verbose results flooding the parent. Uncapped nesting (now depth 3 by default). Opus inheritance.
- Silent truncation (top-N without logging). Treating an unverified claim as refuted, or the reverse.
- Letting fan-out keep running near the usage limit; idle teammates left alive.

---

## 7. Alignment with the existing harness (read 2026-10-16)

| File | Current | Gap or suggestion |
|---|---|---|
| `agents/orchestrator.md` §header | "subagents cannot spawn subagents" | **Outdated.** Nesting is allowed to depth 3 by default since v2.1.219. Either set `CLAUDE_CODE_MAX_SUBAGENT_SPAWN_DEPTH` in `config/settings.json` or say "workers must not spawn agents" and drop `Agent` from worker `tools:`. |
| `agents/orchestrator.md` §4 | "Run independent units in parallel" with no width rule | Add the decision matrix below plus a width cap and a stated agent count in `PROGRESS.md` before any fan-out. Split by context (feature and its tests together), not by problem type. Writes stay single-threaded unless files are disjoint (worktrees). |
| `skills/web-research` depth tiers | quick 1 agent / standard 3 / exhaustive 5+ | Matches Anthropic (1 / 2–4 / 10+). Suggestions: give each tier a **call budget** (quick 3–10 calls; standard 3 agents × 10–15 calls); cap exhaustive at **≤10 per batch**; for exhaustive, prefer the bundled **`/deep-research` workflow** (it votes on claims, drops refuted ones and marks unverifiable ones as "unverified"), keeping the harness scope interview; add loop-until-dry for "find everything" requests; add a completeness-critic pass. |
| `skills/verify` | One forked verifier, pass/fail/needs-human | Keep one verifier as the default (cheap, Cognition's working pattern). Escalate by **stakes**: high stakes or irreversible work gets **3 independent refuters with a majority kill**, or **lens-diverse** verifiers. Prefer executable checks over judges. Use a cross-family or different-model judge only if it is at least as capable (Chen et al. caveat). The fix-loop cap of 2 retries is consistent with Anthropic's 3. |
| `hooks/usage_guard.py` | Single threshold: 5h or 7d ≥ 90% → "pause parallel fan-out" | Make it graduated:<br>• **≥ 60–70%:** cap fan-out at 2–3 workers, Sonnet/Haiku only, no workflows above `small`.<br>• **≥ 90%:** no fan-out, finish and hand off (current behavior).<br>• Optionally inject the current tier as `fanout_budget=N` so the orchestrator reads one number. Also consider context ≥ 160k → prefer delegating verbose reads to subagents (context protection) rather than reading inline. |
| `BLUEPRINT.md` §0.5 | Opus lead + Sonnet workers; `model:` in every agent file | Consistent. Add: siblings in one fan-out use identical model, effort and tools so they share the cache; set `subagentPromptCacheTtl` only if runs are long; set `workflowSizeGuideline` (e.g. `medium`) explicitly in `config/settings.json`. |

## 8. Proposed decision matrix (fan-out policy v0)

Step 0, **gate**: fan out only if at least one of these holds:
- (a) there are 2 or more independent read-mostly subproblems
- (b) a subtask would dump more than about 1k irrelevant tokens into the lead's context
- (c) stakes justify independent verification
- (d) a distinct tool or permission set is needed

Otherwise stay on one agent.

| Task class | Example | Workers (parallel) | Pattern | Verify | Model | Notes |
|---|---|---|---|---|---|---|
| Trivial or quick | Fact lookup, one-file edit | **0** (inline) | — | Self-check | Session | Latency and bootstrap cost dominate |
| Simple research | "What's X's default?" | **1**, 3–10 calls | Single researcher | Citation check | Sonnet | |
| Comparison | Compare 3 tools | **2–4**, 10–15 calls each, one per option or tier | Parallel search, then table | 1 verifier | Sonnet workers, Opus lead | Comparison mode: `outline.yaml` + `fields.yaml` |
| Broad research / audit | SOTA survey, repo-wide audit | **5–10 per batch**; more than 10 only through a workflow | Multi-modal sweep or map-reduce, then dedupe, then synthesis | Adversarial: 3 refuters per key claim | Sonnet/Haiku mappers | Loop-until-dry (K=2); completeness critic; announce the count |
| Many uniform items | 50 files or contracts | One per item via `pipeline`, ≤16 concurrent; workflow | Map-reduce | Per-item check + sampled re-review | Haiku/Sonnet | Pilot on 5 items first; ask before going above 25 agents or 1.5M tokens |
| Coupled code change | Feature across modules | **0–1** writers + 1 clean-context reviewer | Single writer + reviewer / advisor | Tests + verifier | Sonnet writer, Opus verifier | Context-centric split only |
| Parallel code change | Mechanical migration | `/batch` 5–30, worktrees | Map + per-unit tests | CI / tests per unit | Sonnet | Needs a near-perfect oracle and disjoint files |
| Debugging, unclear cause | Flaky crash | **3–5** hypotheses | Competing hypotheses (team or workflow) | Repro required | Sonnet | Stop when one hypothesis reproduces |
| Design / plan decision | Architecture choice | **3** angles | Judge panel + synthesis | 2–3 judges, median | Opus judges | Only when the solution space is wide |
| High-stakes claim or output | Legal, financial, irreversible | +3 verifiers | Adversarial / lens-diverse verify; majority | Executable checks first | Different model if ≥ capability | `needs-human` on split votes |

**Usage modifiers:**
- 5h/7d usage ≥ 70%: halve the widths (minimum 1) and use Sonnet/Haiku only.
- ≥ 90%: no fan-out.
- Lead context ≥ 160k: delegate reads, but keep returns ≤ 300 words.
- Ultracode on: user opted in, so the widths can go up to the table's maxima, but caps (depth, budget, logging what was dropped) still apply.

**Always:**
- State "N agents × ~M calls, est. tokens" in `PROGRESS.md` before fanning out.
- One owner and one output path per unit.
- Return ≤ 300 words plus pointers.
- A failed agent is listed as not covered.
- Log `fanout_n`, `pattern` and `cost_usd` on the `task` event so the width can be tuned from evals.
