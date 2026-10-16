# Fan-out policy (v1, 2026-10-16)

This file covers when the harness runs parallel subagents and how many. The orchestrator, `web-research`, `prior-art`, `verify` and every deliverable skill follow it. The planner is `skills/fanout-plan`. The usage numbers come from `hooks/usage_guard.py` (`--fanout-budget`).

**Evidence:** `research_notes/Claude harness/fanout_policy_research.md` (2026-10-16), cited below as **R§n**. Confidence tags follow that file: [H] means a primary source read in full, [M] means snippets or strong secondary, [L] means blog-level.

**Calibration:** the user confirmed these numbers on 2026-10-16. They override the research defaults wherever the two differ.

## 1. Why this is a policy, not a reflex

- **Fan-out costs a lot.** It uses roughly 3–10× the tokens of a single agent [H, R§1 claude.com blog], about 15× the tokens of a chat [H, R§1 Anthropic research system], and 2.6–5.9× in measured Claude Code runs [L, R§1 practitioners]. Each subagent first pays a bootstrap of about 33k tokens [L].
- **It buys thoroughness more than speed** [H, R§1].
- **It helps on parallelizable work and hurts on sequential work.** With independent agents and no central check, errors amplify 17× [M, R§1 Kim et al.].
- **Three situations win reliably** [H, R§1 claude.com blog]:
  - context pollution
  - genuinely parallel subtasks
  - specialization
- **Clean-context verification is the second agent that works best** [H/M, R§1 claude.com blog, Cognition 2026].

## 2. Decision rule

Run these steps in order. `fanout-plan` runs them for you.

1. **Never fan out these** (R§6):
   - **Coupled code edits.** Use 1 writer plus 1 fresh-context reviewer (tier 1). The C compiler run collapsed when parallel agents worked on "one giant task", and parallel writers overwrite each other [H, R§1].
   - **Quick questions and one-file changes.** Use tier 0. Latency and bootstrap cost dominate [H, R§1 sub-agents doc].
   - **Tasks that need the full conversation context.** A fresh subagent can't see it, and re-briefing it is a telephone game [H, R§1].
2. **Check whether the output goes to a client or employer.** This covers deliverables, synopses, translations, job applications, cover letters, invoices and client emails. If so, **tier V is mandatory**, on top of whatever tier produced the work (§4).
3. **Gate.** Producing the work fans out only if at least one of these holds [R§8]:
   - (a) there are 2 or more independent, read-mostly subproblems
   - (b) a subtask would dump more than about 1k mostly-irrelevant tokens into the lead's context
   - (c) the stakes need independent checks
   - (d) a distinct tool or permission set is needed

   If none holds, use tier 0.
4. **Classify** using the tier table (§3) and the pattern table (§4).
5. **Apply the usage modifiers** (§5), using `fanout_budget` from the usage guard.
6. **Plan, record, ask.**
   - Write the plan block (agents, models, calls, estimated tokens) to `PROGRESS.md` before spawning anything.
   - Ask the user first when §5 or §3 requires it.
7. **Run, aggregate, verify and log** (§6, §8).

## 3. Tiers

| Tier | Width (parallel) | Use when | Default pattern | Models | Per-agent budget |
|---|---|---|---|---|---|
| **0 Inline** | 0 subagents | Quick lookups (≤ ~3 sources, one source type), one-file edits, quick questions, anything needing the full conversation | — | session model | 3–10 tool calls (self) |
| **1 Single helper** | 1 | Context isolation: the subtask would put more than ~1k irrelevant tokens in the lead's context (verbose logs, long pages, big diffs). Also distinct tools or permissions, or a writer plus fresh-context reviewer for code [H, R§1] | single worker or reviewer | sonnet (haiku for mechanical work) | 3–10 calls (simple), up to 15 |
| **2 Small fan-out** | **2–4** | **Search needs more than ~3 sources, OR mixes source types** (papers, GitHub, Reddit/HN, press) *(calibration)*. Also comparisons (one agent per option or source tier), a design decision with 3 angles, or debugging with 3 hypotheses | parallel search, judge panel, competing hypotheses | sonnet workers, opus lead | 10–15 calls each [H, R§3] |
| **3 Full fan-out** | **5–10 per batch** | Broad survey, repo-wide audit, exhaustive research. More than 10 agents only through a workflow (`/deep-research` or the Workflow tool), and **ask above 25 agents or 1.5M estimated tokens** [H, R§1 workflows doc]. **Ask first when weekly usage is above 75%** *(calibration)* | multi-modal sweep or map-reduce, then dedupe, then refuters | sonnet/haiku mappers | 10–15 calls each |
| **V Verification** | **2–3 lenses** (3 refuters per high-stakes claim) | **Always for client- or employer-bound output** *(calibration)*. Also high-stakes, irreversible or uncertain claims | lens-diverse verify, adversarial refuters | judge ≥ producer capability, preferably a different model; executable checks first | criteria-scoped |
| **S Speed / map-reduce** | one agent per item, **≤16 concurrent** | Many uniform items (files, contracts, pages, segments). **Pilot on 5 first** | pipeline map, then reduce | haiku/sonnet | per item |

Notes:
- **Internal (non-client) work gets 1 verifier by default.** That is the existing `verify` skill. Use tier V only when §4's triggers apply.
- **"Sources" are distinct documents you expect to read,** not search queries. "Mixes source types" means two or more of these: papers or official docs, GitHub, Reddit/HN/YouTube, press or vendor blogs (the tiers in `skills/web-research`).
- **Spawn tier 3 in batches of 3–5 at a time** [H, R§1 Anthropic research]. The lead waits for each batch, so one slow agent stalls the run. Cap each batch at 10.
- **Ultracode or explicit user opt-in** allows the table's maximum widths. It never relaxes depth, budget, logging or the ask rules.

## 4. Patterns

| Pattern | Shape | Use for | Avoid when | Source |
|---|---|---|---|---|
| **Parallel search / multi-modal sweep** | N readers, each with a distinct angle, source tier or modality, then one synthesis | research, prior-art, "find everything" | narrow question (tier 0/1) | [H] R§1, R§4 |
| **Map-reduce / pipeline** | discover the list, run one agent per item through `pipeline()` with no barrier, then reduce with a structured map schema | audits, per-file review, comparison tables, batch translation QA | items depend on each other | [H] workflows doc; [M] LLM×MapReduce |
| **Vote / checker (self-consistency)** | N independent attempts at the same task, then a majority vote or an executable checker picks | classification, extraction, answers that can be checked | no trustworthy verifier (large N reward-hacks an LLM judge) | [M] R§1 Debate-or-Vote, BoN |
| **Judge panel** | N angles, parallel judges, median score, then synthesis with grafts | plans, designs, naming, architecture (wide solution space) | only one sensible approach exists | [H] workflow skill; [M] PoLL/RoPoLL |
| **Refuters (adversarial verify)** | 3 independent refuters per finding; majority kills it; uncertain counts as refuted | high-stakes or uncertain claims, bug findings, citations | low stakes; "find anything" reviewers | [H] workflow skill |
| **Lens-diverse verifiers** | 2–3 verifiers, each owning one distinct lens | **every client or employer deliverable** | — | [M] BoN-MAV; [H] workflow skill |
| **Competing hypotheses** | 3–5 investigators, each with one theory, trying to disprove the others | debugging when the cause is unclear (anchoring risk) | cause already localized | [H] agent-teams doc |
| **Writer + reviewer** | 1 writer plus 1 fresh-context reviewer or a stronger advisor. For code: `coder` (sonnet) → `code-reviewer` (opus) in `step` mode after each step, `back-review` at the end; both preload `coding-standards` (`agents/orchestrator.md` §4a) | coupled code edits, any non-trivial write | — (the cheap default "second agent") | [M] Cognition 2026; [H] claude.com blog |

**Verification lenses for client and employer output** (tier V). Each verifier owns one lens and checks only that lens:
1. **Fidelity:** meaning, facts, numbers, names and dates against the source or facts file. Uses `claim_check.py`, back-translation, and recounted invoice quantities.
2. **Rules and requirements:** reviewer rules `R-xxx`, the rubric, posting must-haves, length limits, client style guide, deadline, and "posting still open".
3. **Language and style:** register, honorific level, spelling and spacing (맞춤법/띄어쓰기), tone, typos.

A fourth lens, **format and deliverability** (file names, attachments, CAT tags, invoice arithmetic), may be added for invoices and CAT-tool deliverables.

**Rules for tier V:**
- **Executable checks run first,** before any judge: `textlen.py`, `translation_qa.py`, `claim_check.py`, `invoice.py --dry-run`, tests. Their output is proof that every lens can cite. An LLM judge is used only for what scripts can't decide [M, R§1 BoN: sound verifiers keep scaling, learned judges reward-hack].
- **Judge model:** at least as capable as the producer, and preferably a different model. For example, a sonnet producer gets opus verifiers, and an opus producer gets a fable verifier or a fresh-context opus. Never pick a *weaker* judge just to get diversity [M, R§1 Chen et al.; self-preference bias].
- **Aggregation:**
  - Lenses don't vote against each other. The overall verdict passes only when every lens passes.
  - If two verifiers disagree about the same item, or any lens returns `needs-human`, that is a **split verdict, and it goes to the user** with both sides' evidence. Never resolve it silently.
- **High-stakes uncertain claims** (legal, financial, irreversible, or a factual claim the deliverable depends on) get **3 refuters**. A majority kills the claim, and a refuter that is uncertain counts as refuted. Any 2–1 split is still shown to the user.

## 5. Usage modifiers

The usage guard injects these with every usage message, as `fanout_budget: level=… max_width=… tier3=… workers=… verify_min=…`. `python3 -I hooks/usage_guard.py --fanout-budget` prints the same values as JSON.

| 5h / 7d usage | Level | Effect |
|---|---|---|
| both < 70% | `normal` | table widths |
| **≥ 70%** in 5h or 7d | `conserve` | **halve every width** (minimum 1): tier 2 → 1–2, tier 3 → 3–5, S → ≤8 concurrent, V → 2. **Sonnet/haiku only,** including verifiers. `max_width=5` |
| **7d > 75%** | `ask` | everything in `conserve`, plus **tier 3 must ask the user before starting**, stating the agent count and estimated tokens |
| **≥ 90%** in 5h or 7d | `stop` | **no fan-out** (`max_width=0`): finish the current step and hand off. **Exception, stated on purpose: client- and employer-bound deliverables still get tier V at minimum width 2 on cheap models (sonnet/haiku).** If the producer was opus or fable, this breaks the "judge ≥ producer" rule, so mark the verdict "verified at reduced strength" and send any split to the user |
| state missing or stale | `unknown` | normal widths, but **tier 3 asks first** (weekly usage can't be confirmed ≤ 75%). Run `/usage` if in doubt |

**Other ask rules** apply at every level:
- more than 25 agents in one run
- more than 1.5M estimated tokens
- more than 10 agents outside a workflow (not allowed)

**Context pressure:** if the lead's context is at or above 160k, delegate verbose reads (tier 1) rather than reading them inline. Returns stay ≤300 words [R§8].

## 6. Safeguards

1. **Nesting.** Fan-out workers run at depth 1 and never spawn agents themselves.
   - **Enforced by tools:** worker agents (`agents/*.md` other than the orchestrator) have no `Agent` tool. Their `tools:` allowlists leave it out, and `browser-operator` lists it in `disallowedTools`.
   - **Backstop:** `config/settings.json` sets `CLAUDE_CODE_MAX_SUBAGENT_SPAWN_DEPTH=2` (the default is 3 since v2.1.219; 1 would turn nesting off). The main thread or orchestrator is level 0 and its workers are level 1. Level 2 exists only so that a worker can run a forked skill (e.g. `verify` → `verifier`, which has no `Agent` tool). Nothing reaches level 3 [H, R§1 sub-agents doc; R§5].
2. **Explicit `model:` in every agent file.** A subagent without one inherits the session model (opus). `CLAUDE_CODE_SUBAGENT_MODEL=sonnet` is only the fallback [H, R§5].
3. **Brief every worker** with:
   - the objective (one sub-question)
   - inputs as paths
   - the output format or schema and its path
   - a **call budget**
   - **boundaries** (which sources, tools and files are in or out of scope, and what the sibling agents cover)
   - the date window

   Vague briefs cause duplicated work and endless searching [H, R§1].
4. **Return ≤300 words plus file pointers.** Bulk goes to files, never into the lead's context.
5. **Dedupe before you verify.** Merge findings, dedupe against everything *seen* (not only what's confirmed), then verify the unique set [H, R§1 workflow skill].
6. **Robust aggregation.** Use a majority vote for categorical answers and the median for scores, never the mean. Surface conflicts instead of averaging them away [M, R§1 PoLL/RoPoLL, Debate-or-Vote].
7. **Stop rules:**
   - loop-until-dry stops after **2 rounds with nothing new**
   - verify→fix loops stop at **2 retries** (3 attempts total), then escalate to the user
   - stop sampling once votes agree (ESC)
8. **Failures are reported as uncovered.** A failed or empty worker never fails the run. List it under "not covered" in the result, and never silently drop or truncate (no silent caps) [H, R§1 Managed Agents, workflow skill].
9. **Plan before spawning.** Write the `fanout-plan` block to `PROGRESS.md` before the first spawn: tier, pattern, N agents × ~calls, models, estimated tokens, usage level.
10. **Cache reuse.** Siblings in one fan-out share the same model, effort, agent type, tools and cwd, so they reuse the prompt cache [H, R§1 workflows doc]. Never mix models within one sibling batch. That also avoids Self-MoA's weaker-model dilution [M].
11. **Writes stay single-threaded** unless files are disjoint and a near-perfect test oracle exists (`/batch` with worktrees) [H, R§1 C compiler; M Cognition].

### Token estimate (rough; calibrate from logged `cost_usd`)

`est_tokens ≈ N × (35k bootstrap + calls × 6k) + 10k × N for the lead's merge`

- tier 1, 1 × 8 calls ≈ 95k
- tier 2, 3 × 12 calls ≈ 350k
- tier 3, 8 × 15 calls ≈ 1.1M (**ask**: close to the 1.5M line)
- tier V, 3 verifiers × 8 reads ≈ 280k

The 35k bootstrap figure is [L] (practitioner measurement). The per-call figure is a harness assumption. Replace both once `est_tokens` and `cost_usd` have been logged for about 20 runs.

## 7. Anti-patterns (R§6)

- Fanning out a simple query, or fanning out "because the feature exists" (Anthropic's 50-subagent failure).
- Splitting one context by problem type (a feature agent, a test agent and a review agent). This causes a telephone game, and coordination ends up costing more than the work. Split by **context** instead: whoever writes a feature also writes its tests.
- Parallel writers on shared files, or on one coupled task.
- Independent agents with no central validation (errors amplify 17× vs 4.4× with central validation).
- Debate rounds instead of independent votes, or mixing weaker models into an ensemble "for diversity".
- A large best-of-N judged only by an LLM, same-model self-grading, or switching to a much weaker judge.
- "Find anything" reviewers (they over-engineer). Verifiers judge only the stated criteria.
- Verbose returns flooding the lead, uncapped nesting, Opus inheritance, silent truncation.
- Fan-out continuing near the usage limit (subagents don't pause at the limit; workflows do).

## 8. Logging

On the `task` event for each fan-out, record these alongside the usual `agent`, `model`, `intent`, `situation`, `meta` and `cost_usd`:

| Field | Value | Status in `schema/ontology.yaml` |
|---|---|---|
| `fanout_tier` | `0`, `1`, `2`, `3`, `V` or `S` | present |
| `fanout_n` | number of agents actually spawned | present |
| `est_tokens` | planned estimate from §6 | present |
| `fanout_pattern` | e.g. `parallel-search`, `map-reduce`, `vote`, `judge-panel`, `refuters`, `lens-verify`, `hypotheses`, `writer-reviewer` | **requested.** Until it exists, put it in `meta.fanout_pattern` |
| `fanout_uncovered` | list of failed or empty units | **requested.** Until it exists, put it in `meta.uncovered` |
| `usage_level` | `fanout_budget.level` at plan time | **requested.** Until it exists, put it in `meta.usage_level` |

Tier-V verdicts are logged as `verification` events (one per lens, plus one aggregate with `items`). This lets the eval loop tune widths against outcomes [R§8 "Always"].
