# Evaluating AI Agents and Memory Systems (state of the art, Oct 2026) — for a Relic eval harness

Scope: methodology, memory evals, agent safety evals, tooling, and practical statistics for a small team building an automated eval harness for Relic (local-first lifelog capture + memory + browser/computer-use agent). Research date 2026-10-16. Note: arxiv.org and xlang.ai were not reachable via fetch (DNS failure). Paper facts below come from search snippets, conference pages, or repos cloned read-only under `/tmp/claude-0/-home-user-albers-club/3712d12f-853b-5b60-93d4-c8956af51529/scratchpad/clones/`.

## 1. Agent eval methodology (how top teams evaluate; outcome vs trajectory; LLM judges; pass@k vs pass^k; variance; contamination)

### Takeaway
The current consensus, set out in Anthropic's "Demystifying evals for AI agents", has four parts. Grade the final environment state rather than the agent's claims or its exact path. Mix code, model and human graders, and calibrate model graders against humans. Run several trials per task from a clean environment and report pass^k when consistency matters. Treat every benchmark as buggy until someone has read its transcripts. Audits such as ABC, OSWorld-Verified, WebArena-Verified, the tau2 task fixes and Online-Mind2Web all show published scores moving by large margins once task and grader bugs are fixed.

### Cited Findings
**Anthropic, "Demystifying evals for AI agents"**
- **Grader types.** Anthropic names three: code-based (fast, cheap, reproducible, but brittle), model-based (flexible, but "requires calibration with human graders"), and human (the gold standard, used mostly to calibrate the others). They can be combined by weighted threshold, all-must-pass, or a hybrid. — [Anthropic Engineering](https://www.anthropic.com/engineering/demystifying-evals-for-ai-agents)
- **Grade the outcome.** Grade the end state of the environment. A booking agent claiming a flight is booked does not count unless the reservation exists in the database. It is "often better to grade what the agent produced, not the path it took." Avoid rigid checks on step order. Add transcript checks such as maximum turns, tool calls or tokens where useful. — [Anthropic](https://www.anthropic.com/engineering/demystifying-evals-for-ai-agents)
- **pass@k vs pass^k.** pass@k is the chance that at least one of k trials succeeds. pass^k is the chance that all k trials succeed, and suits customer-facing reliability. Example: a 75% per-trial success rate gives pass^3 ≈ 42%. — [Anthropic](https://www.anthropic.com/engineering/demystifying-evals-for-ai-agents)
- **Starting size.** Start with "20-50 simple tasks drawn from real failures". Two domain experts should reach the same pass/fail verdict on each task. Every task needs a reference solution. Balance cases where a behavior should happen against cases where it should not. — [Anthropic](https://www.anthropic.com/engineering/demystifying-evals-for-ai-agents)
- **Capability vs regression evals.** Capability evals start with a low pass rate and give the team "a hill to climb". Regression evals should sit near 100%. Saturated capability evals "graduate" into the regression suite. — [Anthropic](https://www.anthropic.com/engineering/demystifying-evals-for-ai-agents)
- **Isolation.** Run each trial in a clean environment. In one case Claude gained an unfair advantage by reading git history left by earlier trials. Limits on CPU or memory make trials correlated. — [Anthropic](https://www.anthropic.com/engineering/demystifying-evals-for-ai-agents)
- **Read the transcripts.** A grader rejected "96.12" against the expected "96.124991…", which put Opus 4.5's CORE-Bench score at 42%. After the grading fixes the score was 95%. — [Anthropic](https://www.anthropic.com/engineering/demystifying-evals-for-ai-agents)
- **Zero-pass tasks.** A 0% pass rate across many trials "is most often a signal of a broken task, not an incapable agent." — [Anthropic](https://www.anthropic.com/engineering/demystifying-evals-for-ai-agents)
- **Judge practices.** Give the LLM judge an "Unknown" escape hatch. Use structured rubrics, with one judge per dimension. Allow partial credit. Make graders resistant to bypasses. — [Anthropic](https://www.anthropic.com/engineering/demystifying-evals-for-ai-agents)
- **Combine methods.** Pair automated evals with production monitoring, A/B tests, user feedback, transcript review and periodic human studies. — [Anthropic](https://www.anthropic.com/engineering/demystifying-evals-for-ai-agents)

**pass^k in tau-bench / tau2-bench**
- tau2-bench implements pass^k as `math.comb(success_count, k) / math.comb(num_trials, k)`, citing the original tau-bench paper (arXiv 2406.12045). It filters out infrastructure errors (simulations that never ran) and requires the same number of trials for every task. — [tau2-bench repo, src/tau2/metrics/agent_metrics.py](https://github.com/sierra-research/tau2-bench)
- tau2-bench v1.0 shipped "75+ task fixes": incorrect expected actions removed, ambiguous instructions clarified, impossible constraints fixed, based on the SABER analysis (arXiv 2512.07850). The July 2026 v1.0.1 grading update states that "results produced with tau2-bench < 1.0.1 are not comparable with >= 1.0.1" and re-graded the affected leaderboard entries. It also added voice full-duplex and `banking_knowledge` (RAG) domains. — [tau2-bench README](https://github.com/sierra-research/tau2-bench)

**Benchmark-flaw audits**
- **ABC (Agentic Benchmark Checklist).** Zhu et al., arXiv 2507.02825, NeurIPS 2025. Flaws in task setup or reward design can under- or overestimate agent performance "by up to 100% in relative terms". Applying ABC to CVE-Bench cut overestimation by 33%. — [NeurIPS 2025 poster](https://neurips.cc/virtual/2025/poster/121769); [arXiv abs (blocked, cited via search)](https://arxiv.org/abs/2507.02825)
- **ABC per-benchmark figures, secondary source only.** These come from a repost, not the paper. tau-bench counted empty responses as successes and used trivial states or substrings as ground truth (+38% overestimate), and agents could list every possible answer (+40%). WebArena used an unvalidated LLM judge (+1.4–5.2%). — [GreaterWrong repost](https://www.greaterwrong.com/users/brandon-sayler)
- **OSWorld-Verified (2025-07-28).** The "major updates" fixed community-reported issues, added AWS parallel evaluation ("within 1 hour"), and made "the benchmark signals more effective". Results must be compared against the new version. Results for the verified leaderboard are run by the maintainers on their own side. Example runs use `--max_steps 15`. — [OSWorld README](https://github.com/xlang-ai/OSWorld); blog [xlang.ai/blog/osworld-verified](https://xlang.ai/blog/osworld-verified) (blocked)
- **OSWorld V2.** v2.1 continues the pattern with task snapshots, mocked websites and evaluator fixes. A community PR proposed moving a site to a hosted copy "so models can't edit backend code" and loosening matching of equivalent numeric formats. — [HF discussion](https://huggingface.co/datasets/xlangai/osworld_v2_tasks/discussions/2); [OSWorld-V2 releases](https://github.com/xlang-ai/OSWorld-V2/releases)
- **WebArena-Verified (ServiceNow, NeurIPS 2025 SEA workshop).** Every task, reference answer and evaluator was manually reviewed. LLM-as-judge and substring matching were removed "in favor of type-aware normalization and structural comparison". Evaluation is deterministic over agent responses plus captured network traces, so runs can be scored offline by replay. 812 tasks, plus a 258-task "Hard" subset for cheaper runs. Installs with `pip install webarena-verified` / `uvx`. — [WebArena-Verified README](https://github.com/ServiceNow/webarena-verified)
- **Online-Mind2Web ("An Illusion of Progress?", COLM 2025).** 300 live-web tasks across 136 sites. Under manual human evaluation most agents succeed on only about 30%, which suggests "over-optimism in previously reported results". Operator reaches 61%. Their WebJudge LLM judge agrees with humans about 85% of the time. — [arXiv html 2504.01382](https://arxiv.org/html/2504.01382v4)
- **BrowseComp (OpenAI, 2025).** 1,266 questions with short, verifiable answers, built to be hard to find but easy to check. A question was revised if more than 40% of a second set of trainers could answer it. Grading uses an LLM judge against the reference, and the model also reports a confidence score. Deep Research scored 51.5% at launch. — [arXiv 2504.12516](https://arxiv.org/abs/2504.12516v1); [Gigazine](https://www.gigazine.net/gsc_news/en/20250411-openai-browsecomp-benchmark-browsing-agent)
- **METR time horizon.** Measures the length of task (in skilled-human time) an agent completes with 50% reliability. Built from 170 tasks lasting seconds to 8 hours and 12 models. The horizon has doubled roughly every 7 months for 6 years, possibly faster in 2024–25. Critics note wide confidence intervals and a coding-heavy task set. — [summary on nunosempere forum](https://forum.nunosempere.com/posts/YJ7Pk2bwTd3ieimG8/metr-measuring-ai-ability-to-complete-long-tasks); [ai-futures critique](https://blog.ai-futures.org/p/beyond-the-last-horizon)

**LLM-as-judge reliability**
- **Known biases.** Position, verbosity and self-enhancement bias are documented. Position bias is the easiest to mitigate, by swapping the order of options. — [Judging the Judges, arXiv 2406.07791](https://arxiv.org/html/2406.07791v1)
- **Self-preference.** GPT-4 shows significant self-preference bias, attributed to a preference for familiar (low-perplexity) text. — [arXiv 2410.21819](https://arxiv.org/html/2410.21819v1)
- **AgentJudgeBench (Aug 2026), judging tool-calling agents.** Judge reliability "degrades sharply with task difficulty": judges plateau at 77–82% accuracy on hard queries without ground truth. Supplying ground truth sometimes hurts. Structured rubrics add up to 6.5 points. — [HF papers 2608.26623](https://huggingface.co/papers/2608.26623)
- **Validating judges.** Judge validation that relies on exact-match agreement does not correct for chance and overstates the judge's discriminative ability. — via search summary of [ICML 2026 IRT-judge poster](https://icml.cc/virtual/2026/poster/66110) (only the summary was seen)

### Inferences
- **What to grade in Relic.** Grade the state the agent leaves behind. For browser tasks that means the DOM, network trace, or files or DB rows written. For the memory store it means the rows actually present or absent. The agent's final message is not evidence. WebArena-Verified's offline network-trace replay is a good pattern for local-first, deterministic re-scoring.
- **Reliability metric.** Report pass^k (k = 3–5) as the headline number for the computer-use agent, because users experience the agent's reliability, not its best try. Keep pass@k only for "assistive suggestion" features.
- **Versioning.** Version the eval set like code, as tau2 does: a grading change invalidates comparisons with earlier runs.
- **Contamination.** For a private, freshly authored set from Relic's own lifelog fixtures, contamination risk is low. Public benchmarks such as LoCoMo, WebArena and OSWorld should be treated as possibly contaminated and used only as smoke tests.

### Gaps
- **OpenAI evals and graders.** The OpenAI Evals API / grader docs (string-check, text-similarity, score-model and python graders) were not fetched. Their details are unverified here.
- **ABC per-benchmark numbers.** These could not be verified against the paper because arXiv was blocked.
- **OSWorld-Verified specifics.** The number of tasks fixed is unknown because the xlang.ai blog was blocked.
- **Contamination studies.** No primary source specific to agents was gathered.

## 2. Memory evaluation (LoCoMo flaws, LongMemEval, MemoryAgentBench, BEAM, private deletion/temporal tests)

### Takeaway
LoCoMo is the most-quoted memory benchmark and also the weakest: wrong gold answers, a lenient judge, contested reproduction and saturated scores. LongMemEval (cleaned, Sep 2025; V2 in May 2026), MemoryAgentBench (ICLR 2026) and BEAM (ICLR 2026, up to 10M tokens) cover knowledge updates, temporal reasoning, abstention and conflict resolution. None of the four tests deletion or "right to forget", so Relic must build that itself.

### Cited Findings
**LoCoMo**
- **Answer-key errors.** An independent audit claims 6.4% of LoCoMo's answer key is wrong (99 errors) and that the LLM judge accepts up to 63% of intentionally wrong answers. This is an informal Substack post. — [Penfield Labs](https://penfieldlabs.substack.com/p/we-audited-locomo-64-of-the-answer)
- **Inaccurate gold answers, peer-reviewed.** The Mnemosyne paper found inaccurate gold answers on manual review. — [arXiv 2510.08601](https://arxiv.org/pdf/2510.08601)
- **Vendor disputes.** Zep argues that Mem0's comparison misconfigured Zep, and revised its own LoCoMo score to 75.14%. Both are interested parties. — [Zep blog](https://blog.getzep.com/lies-damn-lies-statistics-is-mem0-really-sota-in-agent-memory/)
- **Retrieval bypass.** With top_k=50 over a corpus of 19–32 sessions, retrieval returns everything, so the retrieval component goes untested. — [Vectorize](https://vectorize.io/articles/mempalace-benchmarks)
- **Protocol sensitivity.** Small protocol differences compound into large score differences. — [mem0 benchmarks blog](https://mem0.ai/blog/ai-memory-benchmarks)

**LongMemEval (ICLR 2025)**
- **Design.** 500 questions covering five abilities: information extraction, multi-session reasoning, knowledge updates, temporal reasoning and abstention. Built with an attribute-controlled pipeline that produces timestamped chat histories.
- **Updates.** Sessions were cleaned in Sep 2025 because some interfered with answer correctness, and a changelog was published. LongMemEval-V2 (May 2026) targets memory in agentic contexts.
- [LongMemEval README](https://github.com/xiaowu0162/LongMemEval)

**MemoryAgentBench (ICLR 2026)**
- **Competencies tested.** Four: accurate retrieval, test-time learning, long-range understanding, and conflict resolution.
- **Format.** Input is chunked into incremental multi-turn interactions under an "inject once, query multiple times" design. New datasets: EventQA and FactConsolidation. Some tasks use GPT-4o as judge.
- **Follow-up.** The same group released MemoryArena (ICML 2026) for memory on agentic tasks.
- [MemoryAgentBench README](https://github.com/HUST-AI-HYZ/MemoryAgentBench)

**BEAM (Tavakoli et al., ICLR 2026)**
- **Design.** 100 conversations and 2,000 validated questions, with conversations up to 10M tokens.
- **Finding.** Even 1M-context models, with or without RAG, struggle as dialogues lengthen. The proposed LIGHT memory (episodic, working memory and scratchpad) improves on baselines by 3.5–12.69%.
- [ICLR 2026 poster](https://iclr.cc/virtual/2026/poster/10006595); [HF dataset BEAM-10M](https://huggingface.co/datasets/Mohammadta/BEAM-10M)

### Inferences
- **A private Relic memory eval** could be built in four steps:
  1. Script synthetic lifelog timelines with ground-truth event logs. Use a fake persona; never use real user data.
  2. Ingest them through the real capture pipeline.
  3. Ask templated questions in the LongMemEval categories: extraction, multi-session, knowledge update ("what is my current dentist?" after a change), temporal ("what was I working on the Tuesday before the trip?", with relative-date anchoring) and abstention (questions about things never captured).
  4. Score with exact or normalized match where possible. Use an LLM judge only for free text, validated on a human-labelled slice.
- **Deletion and forgetting tests**, which no public benchmark covers:
  - After the user deletes item X or an app or time window, check that X is absent from raw storage, embeddings/vector index, derived summaries, caches and the agent's answers, including paraphrased and indirect probes.
  - "Pause capture" windows must yield abstention.
  - Updated facts must supersede old ones (conflict-resolution style).
  - Grade by direct inspection of the store, as a deterministic state check, plus answer probes.
- **Benchmark use.** Use LoCoMo only as a smoke test, and never with a large top_k over a small corpus. Prefer LongMemEval-S/M cleaned and BEAM slices for public comparability.

### Gaps
- No public benchmark was found that targets deletion, unlearning verification or privacy-forgetting in agent memory. This is a confirmed gap in what was searched, not proof that none exists.
- Letta's own critique of LoCoMo was not retrieved.

## 3. Safety evals for agents (prompt injection, irreversible actions, credentials; how labs report)

### Takeaway
Labs now report prompt-injection robustness as attack success rate (ASR) under an adaptive attacker with many attempts per environment. Anthropic uses Best-of-N with 100 attempts. OpenAI uses an RL-trained attacker. Both state that residual risk is non-zero. Relic should run AgentDojo- or WASP-style end-to-end injection tests that measure both utility under attack and ASR, plus irreversible-action and credential canary tests.

### Cited Findings
**How labs report**
- **Anthropic's method.** Anthropic measures browser-agent prompt-injection ASR with an internal adaptive "Best-of-N" attacker that combines known techniques, at 100 attempts per environment.
- **Anthropic's result.** It reports about 1% ASR for the current extension, "a significant improvement" that "still represents meaningful risk". It does not claim the problem is solved.
- **Anthropic's defenses.** RL training on injections embedded in simulated web content, classifiers that scan all untrusted content (hidden text, manipulated images, deceptive UI), and continuous red-teaming.
- [Anthropic, prompt-injection defenses](https://www.anthropic.com/research/prompt-injection-defenses)
- **Earlier Claude for Chrome preview.** 123 test cases over 29 attack scenarios: 23.6% ASR without mitigations. Browser-specific attacks fell from 35.7% to 0% with mitigations. — [Anthropic, Claude for Chrome](https://www.anthropic.com/news/claude-for-chrome)
- **Later Claude in Chrome post.** Reports zero successful attacks in a Cowork harness, but the grading method changed, so the numbers are not comparable. — [Claude blog](https://claude.com/blog/claude-in-chrome-generally-available) (via search summary)
- **Independent Gray Swan benchmark.** One strong attack succeeded about 4.7% of the time against Opus 4.5, about 33.6% within 10 attempts and about 63% within 100. Opus 4.5 was still better than Gemini 3 Pro and GPT-5.1. This illustrates why ASR must be reported at fixed attacker budgets. — [The Decoder](https://the-decoder.com/claude-opus-4-5-resists-prompt-injections-better-than-rivals-but-still-falls-to-strong-attacks-alarmingly-often/)
- **OpenAI's Atlas hardening (Dec 2025).** An RL-trained automated attacker found long-horizon exploits "over tens (or even hundreds) of steps" that human red-teams had missed. Example: an injected email making the agent send a resignation letter to the CEO. Findings feed rapid patch cycles. — [OpenAI](https://openai.com/index/hardening-atlas-against-prompt-injection)

**Benchmarks**
- **WASP (Meta, ICML/NeurIPS 2025).** End-to-end injection tests on VisualWebArena's gitlab and reddit environments. Simple human-written injections deceive top models: attacks partially succeed in up to 86% of cases, though agents often fail to complete the attacker's full goal. Includes Claude Computer Use support. — [WASP repo](https://github.com/facebookresearch/wasp); [ICML](https://icml.cc/virtual/2025/49781)
- **AgentDojo (ETH SPY Lab, NeurIPS 2024 D&B).**
  - Dynamic environment with suites such as workspace, using user tasks and injection tasks.
  - Defense options such as `--defense tool_filter` and attack options such as `--attack tool_knowledge`.
  - Versioned suites from v1 to v1_2_2.
  - Results are published, and also listed in the Invariant registry.
  - [AgentDojo repo](https://github.com/ethz-spylab/agentdojo)
- **Zenity Labs "AgentFlayer" (Black Hat USA 2025).** Zero-click indirect prompt injections via poisoned docs, emails or tickets against ChatGPT, Copilot Studio, Cursor+Jira MCP, Salesforce Einstein and Gemini. Some were patched, for example Salesforce on 2025-07-11. — [Zenity research](https://www.zenity.io/research/agentflayer-vulnerabilities); [eSecurityPlanet](https://www.esecurityplanet.com/news/ai-agents-vulnerable-silent-hijacking/)

### Inferences
- **Injection suite.** Plant injections in captured content: screenshots/OCR text, web pages, emails and calendar invites that Relic ingests. A lifelog is an unusually large untrusted-input surface, because injected text persists in memory and can fire later ("memory poisoning"). Measure:
  - utility without attack
  - utility under attack
  - targeted ASR at fixed attacker budgets (1, 10, 100 attempts)
- **Irreversible-action tests.** Sandboxed tasks where the correct behavior is to stop and confirm: sends, purchases, deletes, form submits, account changes. Grade from environment state (was a send API called or a file deleted?) plus whether a confirmation prompt was emitted. Include balanced negative cases where acting is correct, per Anthropic's guidance.
- **Credential tests.**
  - Seed fake canary secrets (API keys, passwords, credit-card numbers) into captured screens and pages.
  - Assert they never appear in model prompts sent off-device, logs, memory summaries or outbound network traces.
  - Assert the agent never types them into attacker-controlled forms.
  - Grade with deterministic regex or canary-token detection.

### Gaps
- **InjecAgent figures.** Specific numbers were not retrieved.
- **Google DeepMind.** Its reporting method for Gemini/Mariner browser-agent injection robustness was not retrieved.
- **Standard irreversible-action benchmark.** None was found.

## 4. Tooling (Inspect AI, promptfoo, OpenAI evals, Braintrust, LangSmith, DeepEval, Harbor) — what runs locally / open source

### Takeaway
For a local-first team the strongest open-source options are:
- **Inspect AI** (MIT; sandboxed agent evals; 200+ prebuilt evals in inspect_evals)
- **Harbor** (the Terminal-Bench 2.0 harness; runs agents like Claude Code/Codex/OpenHands in local Docker)
- **promptfoo** (open source; red-teaming; OpenAI announced its acquisition in Mar 2026 but says the OSS project continues)

Braintrust and LangSmith are hosted SaaS platforms and were not verified here.

### Cited Findings
- **Inspect AI.** MIT-licensed, from UK AISI and Meridian Labs. PyPI 0.3.268 as of 22 Sep 2026, with 246 releases since May 2024. Supports tool use, multi-turn dialog and model-graded evals, with 200+ prebuilt evals. Reportedly used by METR and Apollo. — [CASRAI guide](https://casrai.org/guides/inspect-ai-evaluation-framework-uk-aisi); [inspect.aisi.org.uk](https://inspect.aisi.org.uk)
- **Harbor.** From the Terminal-Bench creators, released with Terminal-Bench 2.0 on 2025-11-07. Runs arbitrary agents (Claude Code, OpenHands, Codex CLI) and produces RL/SFT rollouts. Installs via `uv tool install harbor`. Example: `harbor run --dataset terminal-bench@2.0 --agent claude-code --model ... --n-concurrent 4`, running in local Docker, with optional Daytona or Modal cloud. — [tbench.ai announcement](https://www.tbench.ai/news/announcement-2-0); [HF README](https://huggingface.co/datasets/harborframework/terminal-bench-2.0/blob/main/README.md)
- **promptfoo.** OpenAI announced the acquisition on 2026-03-09 to fold it into OpenAI Frontier. OpenAI says it will keep developing the open-source project. Closing was not confirmed in the sources. — [SecurityBoulevard](https://securityboulevard.com/2026/03/openai-acquires-security-startup-promptfoo-to-fortify-ai-agents); [Futurum](https://futurumgroup.com/?p=87434)
- **WebArena-Verified.** Packaged as a pip/uvx/Docker CLI for deterministic offline evaluation. — [repo](https://github.com/ServiceNow/webarena-verified)
- **tau2-bench.** Installs with `uv sync` and runs locally (`--num-trials`, `--num-tasks`). — [repo](https://github.com/sierra-research/tau2-bench)

### Inferences
- **Recommended stack.**
  - Use Inspect AI as the backbone: tasks, solvers, scorers, Docker sandboxes and a log viewer, all running offline with local models.
  - Port the memory and injection suites into Inspect tasks.
  - Add promptfoo for quick red-team and regression assertions on prompts.
  - Use Harbor only if containerized end-to-end agent runs are needed.

### Gaps
- **Not verified:** DeepEval, Braintrust and LangSmith (licensing, local operation), and the OpenAI Evals API's current grader set. They were not fetched, so no claims are made about them.

## 5. Practical guidance (golden-set size, statistical significance for small sets, regression suites, shadow deployment, canaries)

### Takeaway
Start small (20–50 tasks from real failures) and grow. Report standard errors, clustered when questions share a source, and use paired comparisons between versions. Resample each task several times to cut variance. Small sets can only detect large regressions, so gate releases on near-100% regression suites and treat capability-set deltas of a few points as noise.

### Cited Findings
- **Golden-set size.** Start with 20–50 tasks from real failures. Graduate saturated capability tasks into a regression suite near 100%. — [Anthropic](https://www.anthropic.com/engineering/demystifying-evals-for-ai-agents)
- **Anthropic's statistical guidance ("A statistical approach to model evaluations").**
  - Report the standard error of the mean (SEM) with each score.
  - Cluster standard errors on the unit of randomization. Clustered SEs can be "over three times as large" as naive ones.
  - Reduce within-question variance by resampling each question several times.
  - Use paired-difference tests; frontier models' per-question scores correlate at about 0.3–0.7.
  - Do a power analysis before running.
  - [Anthropic research](https://www.anthropic.com/research/statistical-approach-to-model-evals)
- **Standard formulas.** These are standard statistics, not quoted from the article.
  - SEM = s/√n.
  - For binary accuracy p, s ≈ √(p(1−p)). At n = 50 and p = 0.8, SEM ≈ 0.057, so the 95% CI is about ±11 points.
  - Paired-test sample size: n ≈ ((z_{α/2} + z_β)·σ_d/δ)². Detecting a 3-point difference with σ_d = 0.5 needs about 2,180 items.
- **Isolation and infra errors.** Count infrastructure errors separately and exclude them, as tau2 does. Use clean environments per trial. — [tau2-bench](https://github.com/sierra-research/tau2-bench); [Anthropic](https://www.anthropic.com/engineering/demystifying-evals-for-ai-agents)
- **Post-deployment monitoring.** Both labs pair evals with continuous red-teaming and rapid patch cycles after deployment. — [OpenAI](https://openai.com/index/hardening-atlas-against-prompt-injection); [Anthropic](https://www.anthropic.com/research/prompt-injection-defenses)

### Inferences
- **What small sets can detect.** With 50–200 tasks, Relic can only reliably detect regressions of about 10+ points. Use k = 3–5 trials per task, paired comparison against the previous build, and cluster by scenario or fixture.
- **Release gating.**
  - Block on any regression-suite failure: safety, deletion, credential canaries.
  - Track capability scores as trends with CIs.
  - Re-check zero-pass and 100%-pass tasks for broken tasks or graders.
- **Shadow deployment and canaries for a local-first app.**
  - Run the new agent or memory build in shadow mode on opt-in dogfood lifelogs, scoring the outputs offline without acting.
  - Stage rollouts to a small canary cohort.
  - Use canary tokens (fake secrets and planted injections) in fixtures to detect leakage or exfiltration regressions.

### Gaps
- **Shadow deployment.** No primary lab source specific to agents was retrieved. The recommendations above are standard software practice adapted by inference.
- **Judge calibration size.** No source was found for how many human-labelled items are needed to calibrate an LLM judge.

## Blocked sources
- https://arxiv.org/abs/2507.02825 (ABC paper; arxiv.org DNS failure, ENOTFOUND)
- https://xlang.ai/blog/osworld-verified (OSWorld-Verified report; DNS failure, ENOTFOUND)
- arxiv.org in general (all arXiv full texts; paper facts taken from search snippets, conference pages or repo READMEs instead)
