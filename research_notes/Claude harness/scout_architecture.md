# Scout pass 2: harness architectures and components worth adopting (2026-10-16)

Second, deeper pass after `sota_harness_patterns.md`. That note ranked repos mostly by metadata. This one is
based on **reading the actual files** in shallow clones (`git clone --depth 1`, read only, nothing executed) under
`/tmp/claude-0/-home-user-albers-club/1397d302-c3cb-5329-ad06-e45b2c66c6d1/scratchpad/scout2/<owner_repo>/`.
Items covered in the first note (star counts, research papers, general anti-patterns) are not repeated here.

How to read the verdicts:
- **Adopt** means install as-is.
- **Vendor** means copy one named file or pattern into the harness, with attribution.
- **Borrow** means take the idea only.
- **Avoid** means don't use it.

"Last commit" is the HEAD commit date of the clone. Context cost is estimated as bytes ÷ 4 ≈ tokens.

Harness slots used below:
- **ORCH:** orchestrator and agent routing
- **PLAN:** PROGRESS.md, tasks.json, SPEC.md, handoff
- **VERIFY:** the verify skill, the verifier agent and Stop gates
- **GUARD:** reward-hacking and security guards
- **EVAL:** the `evals/` folder and `scripts/eval_gate.py`
- **LEARN:** mishap, retro, review-week, librarian, rule expiry
- **KB:** `scripts/kb.py`, knowledge/raw, wiki, index
- **RESEARCH:** web-research and web-researcher
- **BROWSER:** browser-operator and browser-task
- **ASSET:** asset-decompose and prior-art
- **OBS:** logging and cost observability (`hooks/log_event.py`, weekly_report)

---

## 0. The ten actions, in priority order

| # | Action | Slot | Source (file) | Effort |
|---|---|---|---|---|
| 1 | Add a **Stop-hook verification gate** with two layers. **(a)** A command hook: if `PROGRESS.md` or `tasks.json` marks an item done with no `verification` event, exit 2 ("run /verify"). **(b)** A `type: "prompt"` Haiku hook adapted from Trail of Bits' anti-rationalization gate, **rewritten so it only rejects unmet *stated* criteria** (the original also rejects "pre-existing / out of scope" excuses, which pushes scope creep and conflicts with §0.5's verifier rule). | VERIFY | trailofbits/claude-code-config `README.md` §Hooks "Anti-rationalization gate"; planning-with-files `scripts/gate-stop.sh` (pattern only) | S |
| 2 | Run skill evals with **`claude plugin eval --ablation with-without`**. Each case runs with and without the skill loaded, and the judge model must differ from the producer. Copy the contamination guard from **ToB `plugins/code-improver/evals/check_contamination.py`**, plus the rule "generate fixtures with scaffold.sh, never mount repo paths." Map the case files onto the existing `evals/<area>/` layout. | EVAL | trailofbits/skills `plugins/property-based-testing/README.md`, `plugins/code-improver/evals/README.md`, `plugins/goal-prompt/evals/*/case.yaml` | M |
| 3 | Vendor the **skill-creator description-optimization loop**: 20 should/shouldn't-trigger queries, a 60/40 train/held-out split, and the best description picked by *test* score. Run it on the harness's 20+ skills, where triggers overlap (retro/handoff/distill-principles, intake/backcatalog, style-capture/style-guide). | EVAL, LEARN | anthropics/claude-plugins-official `plugins/skill-creator/skills/skill-creator/scripts/run_loop.py`, `improve_description.py`, `references/schemas.md` | S |
| 4 | Make the librarian's weekly loop **SkillOpt-Sleep-shaped**: harvest → mine recurring tasks → replay → bounded add/delete/replace edit → held-out gate → *stage* → user adopts. Use the **`handoff` backend** (no provider calls) or the existing eval_gate.py. Copy the gate semantics from `skillopt_sleep/gate.py`. | LEARN, EVAL | microsoft/SkillOpt `skillopt_sleep/gate.py`, `plugins/README.md`, `docs/sleep/RESULTS.md` | M |
| 5 | Add **cheap correction detection to `hooks/log_event.py`**: claude-reflect's CORRECTION/GUARDRAIL/EXPLICIT regex tables, each with a confidence and `decay_days`. Add **Korean equivalents** (아니, 그게 아니라, 하지 마, 말고, 다시, 기억해:). The hook only tags `is_correction_candidate`. Labeling stays weekly. | LEARN, OBS | BayramAnnakov/claude-reflect `scripts/lib/reflect_utils.py` L1198-1260 | S |
| 6 | Add `kb.py fidelity`. Port the **literal-fidelity sweep** from `check_evidence.py`: every number, date and quote of 15+ characters in a wiki page must appear verbatim in its linked raw source. It also builds an inventory of raw files no article cites. Add the Anthropic knowledge-wiki rules to the intake skill: **never file a global absence claim**, close superseded facts with `valid_to`, and run a **resolve pass** on open questions before consolidating. | KB | Astro-Han/karpathy-llm-wiki `scripts/check_evidence.py` (MIT, stdlib only); anthropics/claude-quickstarts `managed-agents/knowledge-wiki/` notebook Steps 1-3 | S |
| 7 | Give web-research a **comparison mode**. Write `outline.yaml` (items) plus `fields.yaml` (columns). Each worker writes one JSON file per item, marks unknown values `[uncertain]`, and must pass `validate_json.py` before it can finish. A rerun skips items whose output already exists. This fits "compare tools/options" research and makes fan-out resumable. | RESEARCH | Weizhena/Deep-Research-skills `skills/research-en/research-deep/SKILL.md`, `research/validate_json.py` (MIT) | S |
| 8 | Switch browser-operator to **CLI over MCP** for page work. Use `playwright-cli` (Microsoft now recommends CLI+skills over MCP for coding agents) or `agent-browser` (`@eN` refs, `--allowed-domains`, `--content-boundaries`, `--max-output`). Keep Claude in Chrome for signed-in pages. Use `chrome-devtools-mcp --slim --no-usage-statistics --no-performance-crux` only when debugging. | BROWSER | microsoft/playwright-cli `skills/playwright-cli/SKILL.md`; vercel-labs/agent-browser `README.md` | S |
| 9 | Install **hookify** (official) so a mishap's "Prevention: hook" becomes a `.claude/hookify.<name>.local.md` rule you can switch on and off. Its `enabled:` flag gives rule expiry for free. Add the official **session-report** analyzer to review-week for the cost dimension: tokens, cache breaks, cost per subagent and per skill. | LEARN, OBS | claude-plugins-official `plugins/hookify/`, `plugins/session-report/skills/session-report/analyze-sessions.mjs` | S |
| 10 | Upgrade `/retro` and review-week with two borrowed pieces. **mattpocock's retro taxonomy:** Navigation, Automated checks (mechanical violations get a lint or hook, not a rule), Coding standards (enforced by the *reviewer*, not the implementer), No-ops, Tool economy, Information access. **compound-refresh's outcome set** for expiry: Keep / Update / Consolidate / Replace / Delete, with "unverifiable is not false" and no `_archived/` folder (git history is the archive). Use superpowers' **diagnosing** pattern for transcript forensics: one analyst subagent per dimension, and every finding must cite `path:line`. | LEARN | mattpocock/skills `skills/engineering/retro/SKILL.md`; EveryInc/compound-engineering-plugin `skills/ce-compound-refresh/SKILL.md`; obra/superpowers `skills/diagnosing-superpowers/prompts/*.md` | S-M |

What **not** to do: don't install superpowers, ECC, planning-with-files, spec-kit or VoltAgent wholesale. Don't
use fast-jev-compaction, which sends your whole conversation to a third-party API. Don't use basic-memory's cloud
tier, the MCP reference memory server, or browser-use/Stagehand as the main browser path. Reasons are in each
entry below.

---

## 1. Whole-harness frameworks and configs

### obra/superpowers: MIT, last commit 2026-10-09 (v7.0.0), 238 files
- **What it contributes:**
  - `subagent-driven-development` (32.6 KB). One fresh implementer per task, then a task reviewer that issues two verdicts (spec and quality). Fix rounds are capped at 5. From round 4 the implementer is a *fresh* subagent on a stronger model. When the cap trips, the controller adjudicates the remaining findings and records "Rulings" in a ledger file. Anything that changes the plan goes in the ledger, because "conversation memory does not survive compaction" and re-dispatching completed tasks was "the single most expensive failure observed."
  - `task-reviewer-prompt.md`. "Do not trust the report." The reviewer reads one diff file and must not re-run the whole test suite. It may not spawn sub-reviewers. Every finding must be tied to a risk it names.
  - `verification-before-completion` (3.6 KB). The Iron Law, a table of claims vs. evidence, and a list of red-flag words ("should", "probably", "Great!").
  - `diagnosing-superpowers`: transcript forensics. Seven parallel analyst dimensions: skill-timeline, plan-adherence, repeated-work, stumbles, quality-evidence, request-conflicts, and cost-and-time. "Every finding cites path:line." It also has redaction and scrub prompts for sharing.
  - `writing-skills`: TDD for skills (pressure-test scenarios such as `systematic-debugging/test-pressure-1.md`). It also says the description should hold **only triggering conditions**: if it summarizes the workflow, the agent follows the summary and skips the body.
- **Context cost:** the SessionStart hook injects all of `using-superpowers` (3.2 KB ≈ 800 tokens) wrapped in `<EXTREMELY_IMPORTANT>` on every startup, clear and compact. Fifteen skill descriptions are always listed. The skills themselves total 163 KB, loaded on demand.
- **Security:** the release notes fix a Windows `run-hook.cmd` hole where a repo could plant `bash.cmd` and get it executed. The project is security-aware but cross-platform shell-heavy. Its hooks run with a broken PATH by design.
- **Verdict:** **Vendor patterns, don't install.**
  1. Copy the *task-reviewer prompt's* "do not trust the report / one diff / no sub-reviewers / name the risk" rules into `agents/verifier.md`.
  2. Copy the *fix-round cap + fresh stronger model at round 4 + ledger Rulings* into `agents/orchestrator.md` §4.
  3. Use the *diagnosing* dimension prompts as the core of `/why` and the retro forensics.
- **Conflicts:**
  - Superpowers' bootstrap competes with `interview`. Its mandatory brainstorming and TDD would duplicate the harness's interview-first rule.
  - The `<EXTREMELY_IMPORTANT>` injection goes against "keep memory small."
  - Its "Continuous execution, rulings not stalls" stance is good for coding but conflicts with "never submit forms without confirmation". Only its four stop conditions match the harness.

### trailofbits/claude-code-config: **no LICENSE file**, last commit 2026-08-24, 17 files
- **What it contributes:**
  - `settings.json`: Read-deny for credential directories, including wallet paths. Two PreToolUse blockers: an `rm -rf` regex, and a block on pushing to main.
  - `rules/*.md` with `paths:` globs.
  - `hooks/log-gam.sh`, which logs mutating CLI calls and skips read-only ones.
  - The README's prompt-type **Stop anti-rationalization gate**. It needs JSON-only output, or Haiku wraps the answer in a code fence and the hook silently breaks. It has a 30-second default timeout.
  - The README's principle: "hooks are guardrails, not walls."
- **Verdict:** **Borrow ideas only, because there's no license.** It's already referenced in `config/settings.README.md`.
  - Rewrite the Stop gate yourself; it's a short prompt.
  - Add `Read(~/.config/gh/**)`, `Read(~/.docker/config.json)`, `Read(~/.kube/**)`, `Read(~/.npmrc)` and `Read(~/.pypirc)` to the deny list. The harness currently denies only `~/.config/gh/hosts.yml`.
- **Conflict:** the stock gate prompt rejects "out of scope" claims. The harness's verifier explicitly *allows* scoping to stated criteria, so rewrite the prompt as in action 1.

### trailofbits/skills: **CC-BY-SA-4.0**, last commit 2026-10-15, 44 plugins
- **What it contributes:**
  - **Real eval discipline** for `claude plugin eval`:
    - `case.yaml` (schema 1.1) holds the prompt, `max_turns`, allowed tools and `runs`, plus an `expected_outcome`.
    - Graders are small files: regex with a weight, or an LLM rubric.
    - `--ablation with-without` reports the gain over the unaided model, so a skill that scores full marks in both arms "is spending context and buying nothing."
    - Practical notes:
      - Each case runs in a sandboxed config dir, so it needs `ANTHROPIC_API_KEY`. OAuth logins aren't visible there, and runs then fail with "Not logged in", which still looks like a score.
      - `--allow-tools Write` matters: without it, a grader that checks a created file can pass for free.
      - Per ToB, the feature was early access and needed `CLAUDE_CODE_WALNUT_SPIRE=1` (**verify** against current docs).
      - The judge model must differ from the producer.
      - `check_contamination.py` fails a run if the agent read the answer key (grader filenames or `expected_outcome` text found in its traces).
  - `code-improver`: a review→fix loop written as a **dynamic workflow** (`workflows/improve.js`). It keeps a findings ledger (`ledger.json`) with stable IDs and fixed/rejected/deferred verdicts, and detects oscillation. A **mechanical scope guard** diffs against the baseline after every round. Fixes must include a test that fails without them. If the reviewer is unavailable, the loop halts instead of improvising.
  - `second-opinion`: Codex/Gemini/Antigravity review.
  - `goal-prompt`: drafts `/goal` conditions.
  - `chrome-mcp-troubleshooting`.
- **License note:** share-alike. Vendored files would bring CC-BY-SA obligations into the harness repo. That's acceptable for a private repo, but keep the attribution and the license.
- **Verdict:**
  - **Vendor** `check_contamination.py` plus the eval layout conventions.
  - **Borrow** the code-improver guarantees for the orchestrator's coder→verifier loop: ledger, oscillation stop, scope guard, and pins.
  - **Adopt as-is (optional)** `second-opinion` as the cross-model verifier, if a Codex or Gemini CLI is installed.
  - Skip the security-audit plugins unless you do security work.

### anthropics/claude-quickstarts: MIT, last commit 2026-10-07
- `autonomous-coding/` (the long-running harness):
  - `prompts/coding_prompt.md` is the canonical session ritual. Get bearings: pwd, read the spec, read `feature_list.json`, `claude-progress.txt`, `git log`. Then run 1-2 *already-passing* core features as a regression check **before** new work. Then do one feature, verify it through the real UI, and change only `"passes"`.
  - `security.py` (359 lines) is a PreToolUse **allowlist** with extra validation for `pkill`, `chmod` and `init.sh`, and a test file.
  - **Verdict:** **Vendor the regression-first step** into `templates/project/` session-start instructions. The harness has PROGRESS.md and tasks.json but not "re-verify 1-2 passing items first." Borrow the allowlist idea only for an unattended mode. Auto mode plus the sandbox already covers interactive use.
- `managed-agents/knowledge-wiki/` (new; Anthropic's own Karpathy-wiki cookbook):
  - Load-bearing lessons from their testing:
    1. The schema goes on the store, not the agent.
    2. Check for an existing entity (and its aliases) before creating one.
    3. Use **temporal discipline**: close old facts with `valid_to` instead of deleting them.
    4. "**Never record a global absence claim**, only 'not in this document'." False absences were the dominant failure at scale.
    5. A **resolver pass** over `open_questions` *before* consolidation was "the single best architectural change." Unanswerable items are marked `CONFIRMED UNRESOLVABLE`, along with the document to request.
    6. The consolidation pass ("dreaming") writes a **new versioned store**, so you can A/B and roll back.
    7. "Dream the wiki as the sole source." Telling it the raw files exist gutted the coverage.
  - Dreaming itself is a gated research preview on Managed Agents, not usable from Claude Code.
  - **Verdict:** **Borrow rules 3-7 into the `intake` and `backcatalog` skills.**
- `computer-use-best-practices/`, `browser-toolset/`: reference only, for API-level agents.

### github/spec-kit: MIT, last commit 2026-10-16 (v1.2.1), 935 files
- **What it contributes:**
  - `templates/spec-template.md`: prioritized user stories, each with an "Independent Test" and Given/When/Then acceptance scenarios, `FR-###` requirements, and `[NEEDS CLARIFICATION]` markers.
  - `templates/commands/checklist.md`: "**unit tests for English**." Checklists test whether the *requirements* are complete and clear, not whether the implementation works, and the agent must not tick its own items.
  - `converge.md` compares the codebase with spec/plan/tasks and appends the unbuilt work as tasks.
  - `analyze.md` checks spec, plan and tasks for consistency.
- **Context cost:** each command is 8-22 KB, about 158 KB in total.
- **Verdict:** **Vendor `spec-template.md`'s acceptance-scenario and FR block into `templates/project/SPEC.md`.** Borrow the checklist idea for the `interview` skill: a requirements-quality self-check before work starts. Don't install it; the CLI scaffolding is overkill for a personal harness.

### OthmanAdi/planning-with-files: MIT, last commit 2026-10-16 (v3.24.1)
- **What it contributes:**
  - `task_plan.md`, `findings.md` and `progress.md`.
  - SessionStart (startup, resume, clear, compact) re-injects the plan. UserPromptSubmit and **PreToolUse on Read, Glob, Grep, Write, Edit and Bash** inject the head of the plan (`head -30`).
  - PreCompact hook.
  - Stop completion gate (`check-complete.sh --gate`, which honors `stop_hook_active`).
  - Plan-attestation and nonce framing to resist injection through the plan file.
- **Context cost:** `SKILL.md` is 39.7 KB (≈10k tokens) and `inject-plan.sh` is 1,406 lines. The PreToolUse injection fires on every read, a recurring token tax.
- **Verdict:** **Borrow two ideas.**
  1. A `SessionStart` hook with matcher `clear|compact` that prints the first ~30 lines of `PROGRESS.md` and the `HANDOFF.md` pointer. This makes "handoff, then clear" automatic.
  2. Its Stop gate reads `stop_hook_active` to avoid infinite loops. Copy that guard into the action 1 hook.
- **Conflicts:** the file names differ from PROGRESS.md and tasks.json, and skill-level hooks in frontmatter are ignored for plugin agents (BLUEPRINT §0.5).

### wshobson/agents: MIT, last commit 2026-10-15, 92 plugins
- **What it contributes:**
  - Granular plugins.
  - `plugin-eval`: a static lint for skills and plugins, plus experimental LLM-judge and Monte Carlo layers that "aren't validated against human labels."
  - `block-no-verify`: a PreToolUse hook that blocks `--no-verify` and `--no-gpg-sign`.
  - `review-agent-governance`: Cedar-gated human approval before an agent posts reviews or merges.
  - `avoid-ai-writing`.
- **Verdict:**
  - **Vendor `block-no-verify`'s pattern** into the deny list: `Bash(git commit *--no-verify*)`, `Bash(git push *--no-verify*)`.
  - **Borrow** `plugin-eval`'s static layer as a CI lint for `skills/`.
  - **Borrow** `avoid-ai-writing`'s pattern catalog for the translator and style-guide reviewer.
  - Don't install the catalog.

### VoltAgent/awesome-claude-code-subagents: MIT, last commit 2026-10-11
- The agents are generic filler. `research-analyst.md` "Query context manager for research objectives" refers to an agent that doesn't exist, and its checklists read like "Analysis comprehensive achieved properly."
- **Verdict:** **Avoid.** The harness's own agents are more specific.

### affaan-m/everything-claude-code (ECC): MIT, last commit 2026-10-15, 4,621 files, 311 skills
- **The notable part is continuous-learning-v2 "instincts"** (`skills/continuous-learning-v2/`):
  - **Instinct format:** YAML frontmatter with `id`, `trigger`, `confidence` (0.3-0.9), `domain`, `source`, `scope` (project or global) and `project_id`, followed by Action and Evidence sections.
  - **Project hash:** derived from `git remote` for portability across machines.
  - **Promotion and expiry:** promote to global once seen in 2+ projects. `instinct-cli.py` sets `PENDING_TTL_DAYS = 30` with a warning at 7 days.
  - **Clustering:** `/evolve` groups related instincts. A workflow instinct is a skill candidate at ≥0.7 confidence; a cluster becomes an agent candidate with ≥3 instincts averaging ≥0.75.
  - **Observation:** `observe.sh` hooks *every* PreToolUse and PostToolUse. A background Haiku observer is off by default.
- **Verdict:** **Borrow** the instinct schema (trigger, action, evidence, confidence, scope) as the format for the harness's `mishap` → candidate rule output. Also borrow the 30-day TTL for *unreviewed* candidates and the "2+ projects → global" rule (it already matches retro step 2).
- **Conflicts:**
  - In ECC, confidence 0.7 means "auto-approved for application." That breaks non-negotiable #4 (rules change only with your approval), so keep human approval.
  - The observe hook on every tool call goes against "raw capture only, label weekly."
  - Don't install ECC. Its own README warns of malware in re-uploads.

### shanraisshan/claude-code-best-practice: MIT, last commit 2026-10-15
- A reading list. Useful pointers:
  - `reports/claude-in-chrome-v-chrome-devtools-mcp.md` puts the tool-schema cost at about 19.0k tokens for Chrome DevTools MCP, 15.4k for Claude in Chrome and 13.7k for Playwright MCP.
  - It lists **Dynamic Workflows**, including a bundled Deep Research workflow (code.claude.com/docs/en/workflows).
  - Also listed: `/goal`, Ultrareview, the Advisor tool, and Routines.
- **Verdict:** **Reference only.**

### Newer standouts (created or active Aug-Oct 2026)
- **mattpocock/skills** (MIT, last commit 2026-10-09). Small, composable skills.
  - `engineering/retro/SKILL.md` (4.4 KB) has the best retro taxonomy found; see action 10.
  - User-only skills set `disable-model-invocation: true`, which keeps their descriptions out of the always-loaded skill list.
  - **Vendor** the retro taxonomy.
  - Apply `disable-model-invocation: true` to harness skills that only you invoke: `why`, `retro`, `new-project`, `backcatalog`, `style-capture` and `distill-principles`. Only `review-week` has it today.
- **EveryInc/compound-engineering-plugin** (MIT, last commit 2026-10-16). `ce-compound` captures learnings into `solutions/`. `ce-compound-refresh` audits them against the code with exactly one outcome per doc and a separate, opt-in "worth" pass that can delete accurate-but-redundant docs. **Borrow** this for review-week §5 Expire.
- **tigerless-labs/agent-memory** (MIT, v0.1.0, created 2026-09-01, ~3.9k★). Discussed under §2.
- **tamaratran/fast-jev-compaction** (MIT, about 7.7k★, created 2026-09-17).
  - Replaces compaction by sending **the whole conversation plus tool inputs** to `https://api.typesafe.ai/v1/systemone` (`src/request.ts`), using `TYPESAFE_API_KEY`.
  - **Avoid.** It sends the transcript to a third party, and the star count is suspicious for a 26-file repo.
- **HarnessRouter**, **yetone/magpie**: routers and proxies. **Avoid** (same reasons as in note 1).

---

## 2. Memory and knowledge

| Repo | License / last commit | What it contributes | Verdict and slot |
|---|---|---|---|
| **Astro-Han/karpathy-llm-wiki** | MIT / 2026-07-24 | A 14 KB skill (ingest, query, lint). Before compiling it triages each source: **New / Update / Disputed / No material**. Status blocks (Outdated, Disputed) mean history is never silently rewritten. **Grounding invariant:** every number, date and quote must be located in `raw/` *before* writing. `scripts/check_evidence.py` (stdlib, report-only) has fidelity, evidence-error and orphan-raw sweeps. Parallel *search*, serial *compile*. | **Vendor `check_evidence.py`** into `kb.py` as `fidelity` (action 6). **Borrow** the triage dispositions for the `intake` skill. Paths differ: it uses `wiki/<topic>/` and a `Raw:` field, while the harness uses `knowledge/wiki/` with `raw/...#p.N` anchors, so adapt `RAW_LINK`. **KB** |
| anthropics/claude-quickstarts `knowledge-wiki` | MIT / 2026-10-07 | Covered above: absence rule, `valid_to`, resolver pass, versioned consolidation | **Borrow.** **KB** |
| **tigerless-labs/agent-memory** | MIT / 2026-10-17, v0.1.0 | Markdown is the source of truth and the SQLite FTS5 index is a cache you can rebuild (enforced by a test). `MEMORY.md` is the only thing injected at startup. Recall **returns paths with one-line abstracts**, read deeper on demand (`--level outline`). Memories carry `valid_from` / `invalid_at`, and `recall --as-of` answers as of a date. A sleep-time "Manage" pass can add and update on its own, but **deletion is only ever a proposal**. No API keys. Self-reported LongMemEval-S subset: 52.9% vs 5.8% with no memory. | **Borrow the design.** It's the cleanest statement of what the harness memory should be. Optionally pilot it on one project later. `mem setup` merges into your settings and installs Stop and SessionEnd distillation hooks, so read them first. It's young (6 weeks old). **LEARN, KB** |
| AgriciDaniel/claude-obsidian | MIT / 2026-09-10, ~15.6k★ | A Karpathy wiki as an Obsidian vault: 16 skills, SessionStart and Stop hooks | **Borrow** only the idea "the wiki folder doubles as an Obsidian vault," for reading it on a phone. Don't install the hooks. **KB** |
| basicmachines-co/basic-memory | **AGPL-3.0** / 2026-10-15 | A Markdown plus SQLite MCP server with 29 tools and a paid cloud upsell | **Avoid for now.** It overlaps kb.py, its tool schemas cost context, and AGPL code must not be vendored. **KB** |
| modelcontextprotocol/servers `src/memory` | MIT / 2026-10-11 | A JSONL entity/relation knowledge graph | **Avoid.** It has no provenance, nothing a human can review, and it adds poisoning surface. |
| humanlayer/humanlayer `.claude/commands/create_handoff.md`, `resume_handoff.md` | Apache-2.0 / `.claude` last changed 2026-06-18 | Handoff frontmatter includes `git_commit` and `branch`. Sections: Tasks (with status), Critical References (2-3 only), Recent changes as `file:line`, Learnings, Artifacts, Next steps. On resume, it reads linked plans **in the main thread, not via a subagent**, then checks the current state against the handoff before acting. | **Vendor** two lines into `skills/handoff/SKILL.md`: record `git_commit`/`branch` (so a stale handoff is detectable) and "on resume, diff the current git state against the handoff before acting." **PLAN** |
| mattpocock `productivity/handoff` (940 B) | MIT | A minimal handoff | The harness's version is already better. |

---

## 3. Verification, evals and reward-hacking guards

| Component | License / last commit | Notes | Verdict and slot |
|---|---|---|---|
| **`claude plugin eval`**, as used in trailofbits/skills | CC-BY-SA (the case files) | Ablation, a judge model different from the producer, multiple runs, scaffolded fixtures, a contamination checker. See §1. | **Adopt as the runner** for `evals/`. Keep `eval_gate.py` as the accept/reject logic over its JSON output. Pilot one case first. **EVAL** |
| **skill-creator** (official) `scripts/run_eval.py`, `run_loop.py`, `agents/grader.md`, `comparator.md`, `analyzer.md` | Apache-2.0 / 2026-10-15 | Uses an `evals.json` schema (prompt, expected_output, expectations). Runs with-skill and baseline arms in the same turn, does blind comparison, and keeps a `history.json` of versions. The description loop uses a **60/40 split and selects by held-out score.** | **Adopt** (installed via the official plugin) and **vendor** `run_loop.py` usage into review-week (action 3). **EVAL** |
| **microsoft/SkillOpt** + SkillOpt-Sleep | MIT / 2026-10-06, PyPI 0.2.0 | Treats the skill document as a trainable parameter: bounded add/delete/replace edits, accepted only on a strict held-out improvement, with a rejected-edit buffer. Sleep = harvest → mine → replay → propose → validate → **stage**; "nothing live changes until the user explicitly adopts it." The Claude Code plugin is a single *async* SessionEnd hook. The `handoff` and `mock` backends make no network calls. A real backend sends truncated transcript excerpts to the provider. | **Vendor `skillopt_sleep/gate.py`'s gate semantics** (accept_new_best / accept / reject) and the staging idea into eval_gate.py and review-week. Pilot the real tool only with the handoff backend. **LEARN, EVAL** |
| **gepa-ai/gepa** `optimize_anything` | MIT / 2026-10-12 | Optimizes any text (prompts, configs, skill docs) against an evaluator you supply. One API over the GEPA, AutoResearch and MetaHarness backends plus a best-of-N baseline. Ships an 18 KB Claude skill (`.claude/skills/gepa-optimize-anything/SKILL.md`). | **Borrow later**, once you have about 20 scored tasks per area. Run offline, never in the session loop. **EVAL** |
| kayba-ai/agentic-context-engine (ACE) | Apache-2.0 / 2026-09-23 | A Python SDK around LiteLLM, from a commercial vendor. The repo root has a committed `mlflow.db` and ad-hoc `test_*_live.py` files. | **Borrow the delta-edit idea only**, which BLUEPRINT already does. Avoid the SDK. **LEARN** |
| openai/codex-plugin-cc | Apache-2.0 / 2026-07-07 | `/codex:review`, `/codex:adversarial-review`. An optional **Stop review gate** (`stop-review-gate-hook.mjs`, 900 s timeout) blocks the stop if Codex finds issues, and the README warns it "may drain usage limits quickly." | **Adopt as an optional cross-model verifier** if you have ChatGPT or Codex. Leave the Stop gate *off* by default and call `/codex:review` from `verify` on code tasks. **VERIFY** |
| ralph-loop (official) `hooks/stop-hook.sh` | Apache-2.0 | A Stop hook re-feeds the prompt until a `<promise>…</promise>` string matches, or `max_iterations` is reached | **Borrow only the max-iterations guard.** The completion promise is *self-reported*, which is a textbook reward-hacking channel. The built-in `/goal` (separate evaluator) is better. **VERIFY, GUARD** |
| 199-biotechnologies/claude-deep-research-skill | README says MIT but **no LICENSE file** / 2026-04-11 | Deterministic `verify_claim_support.py` (entity, number, date and lexical-overlap checks of claims against stored evidence quotes; no LLM). JSONL evidence store, `verify_citations.py`. | **Borrow** the claim → evidence JSONL plus deterministic support check for `rubrics/research-report.yaml`. Only vendor it after asking the author to add a license. **RESEARCH, VERIFY** |
| ECC `eval-harness`, `verification-loop` | MIT | Generic pass@k text | **Skip.** It adds nothing beyond the above. |

**Reward-hacking guard gap in the harness:** `config/settings.json` denies `Edit` and `Write` on `**/evals/**` and
`**/rubrics/**`, but **Bash writes are not covered** (`sed -i`, `>`, `cp`, `git checkout`). Following ToB ("hooks are
guardrails, not walls") and ImpossibleBench ("hidden or read-only tests cut cheating to near zero"):
- add a PreToolUse Bash hook that blocks commands touching `evals/`, `rubrics/` or `tests/` paths for non-librarian agents;
- better still, run eval fixtures from a copy outside the repo, like ToB's scaffold.sh;
- the code-improver scope guard (diff against a baseline after each round) is the post-hoc check.

---

## 4. Self-improvement (correction capture, confidence, expiry)

| Component | License / last commit | Notes | Verdict and slot |
|---|---|---|---|
| **BayramAnnakov/claude-reflect** | MIT / 2026-10-02 | Hooks: UserPromptSubmit (`capture_learning.py`, regex detection into a queue), PreCompact (warns if the queue is unprocessed), PostToolUse on Bash (reminder after a commit), and SessionStart. Each pattern table entry carries `(regex, name, confidence, decay_days)`: EXPLICIT `remember:` 0.90/120 days, GUARDRAIL "don't add X unless" 0.90/120, POSITIVE 0.70/90, plus FALSE_POSITIVE filters and a length cutoff. An optional `semantic_detector.py` shells out to `claude -p`. `/reflect` gives a human-reviewed queue and routes each item to CLAUDE.md, a `rules/` file or a skill. | **Vendor the pattern tables** into `log_event.py` as a tag only (action 5). Add Korean patterns. **Don't install the plugin**: it overlaps mishap and retro, and adds 4 hooks. **LEARN** |
| **hookify** (official) | Apache-2.0 | Rules are `.claude/hookify.<name>.local.md` files (frontmatter: `name`, `enabled`, `event`, regex pattern, message). `/hookify` with no arguments scans the conversation for behaviors you corrected. Python hooks run on PreToolUse, PostToolUse, Stop and UserPromptSubmit (10 s timeout). | **Adopt.** It's the right home for "Prevention: hook" mishaps, and `enabled: false` is reversible expiry. Cost: one python start per tool call. **LEARN, GUARD** |
| **claude-md-management** (official) `commands/revise-claude-md.md` | Apache-2.0 | End-of-session "what context was missing" → one-line additions → show the diff → apply | **Borrow** the "one line per concept, command - description" format for retro proposals. The harness's approval flow is stricter, so keep it. **LEARN** |
| ECC instincts | MIT | See §1 | **Borrow** the schema and TTL, not the auto-apply. **LEARN** |
| compound-engineering `ce-compound-refresh` | MIT | Keep/Update/Consolidate/Replace/Delete; contradictions outrank staleness; "unverifiable is not false" | **Borrow** for expiry (action 10). **LEARN** |
| superpowers `diagnosing-superpowers` | MIT | Seven-dimension transcript analysis with path:line citations | **Vendor** the dimension prompts (about 1.5 KB each) into `skills/why` or retro. **LEARN, OBS** |
| official `session-report` | Apache-2.0 | `analyze-sessions.mjs --json --since 7d` reports by_project, by_subagent_type, by_skill, cache_breaks and top_prompts from `~/.claude/projects` transcripts | **Adopt** for review-week's cost and time dimensions. It's local only. **OBS** |
| official `receipts` | Apache-2.0 | Usage "receipt" with deliberately no dollar or hours-saved figures | Optional. **OBS** |

Rule-expiry synthesis for review-week §5:
1. Candidate rules that are never reviewed auto-expire after **30 days** (ECC TTL).
2. Approved rules carry `decay_days` (claude-reflect: 90-120). After that, refresh them against the log: cited or used means Keep or Update; contradicted means Replace; never cited in 6 weeks means propose Delete.
3. Deletion is always a proposal, never automatic (agent-memory's authority tiers).
4. A mechanical rule becomes a hook or hookify rule, and the prose rule is removed (mattpocock retro).

---

## 5. Research and fan-out

| Component | License / last commit | Notes | Verdict and slot |
|---|---|---|---|
| **Weizhena/Deep-Research-skills** | MIT / 2026-08-23 | Two phases: `/research` builds `outline.yaml` (items) and `fields.yaml` (schema), then `/research-deep` runs background workers in batches, with user approval between batches. Workers write `{item}.json`, mark unknowns `[uncertain]`, and must pass `validate_json.py`. A rerun skips items whose JSON already exists. Source modules: academic, general web, GitHub debugging, Chinese-language tech. Inspired by RhinoInsight (arXiv 2511.18743). | **Vendor** the outline and fields pattern plus `validate_json.py` into web-research (action 7). Its prompt template must be reproduced exactly: a sensible "frozen worker brief." **RESEARCH** |
| 199-biotechnologies deep research | No LICENSE file | Evidence and claim stores plus deterministic checks | **Borrow** (§3). |
| humanlayer `web-search-researcher.md`, `research_codebase.md` | Apache-2.0 | Locator, analyzer and pattern-finder sub-agents; "document what is, don't critique" | **Borrow** the role split for code research only. |
| Claude Code bundled **Deep Research dynamic workflow** | Built in | Per the best-practice index and the first note; not verified locally | **Try first, before building more.** Have `web-research` call it for exhaustive depth and keep the harness's own scope interview and source tiers. **RESEARCH** |
| **morluto/rea** (REA, "Reverse Engineer Anything") | MIT / 2026-10-17, ~289k★ (inflated per note 1) | **Not a research or fan-out tool. It's a reverse-engineering MCP**: native binaries via Hopper, Ghidra or IDA, JS/Electron/ASAR, .NET, APK/JADX, firmware, packet captures, websites (structure, scripts, network) and saved HAR captures. `npx rea-agents setup` writes MCP registrations plus "workflow instructions" into your agent config (it has `--dry-run --json`). The skill is 23.5 KB. Runtime capture runs targets under your user permissions. | **Borrow, scoped.** Don't install globally. If you need "how does app X do feature Y" for `prior-art` or asset work, attach REA **only to `asset-decomposer`** through the agent's `mcpServers:` frontmatter, run setup with `--dry-run` first, and prefer static analysis modes. Its "results carry Evidence plus limitations" contract matches the harness's proof rule. **ASSET** |

---

## 6. Browser and computer-use reliability

| Tool | License / last commit | Key facts from the files | Verdict for browser-operator |
|---|---|---|---|
| **microsoft/playwright-cli** + skill | Apache-2.0 / 2026-09-28 | Microsoft's own Playwright MCP README: coding agents "increasingly favor CLI-based workflows exposed as SKILLs over MCP because CLI invocations are more token-efficient." Snapshot refs (`e15`), `find "text"` / `--regex` to search the snapshot without dumping it, and `attach --extension` or `--cdp=chrome` to reuse a running Chrome. The profile is in memory by default, with `--persistent` available. The skill is 15.4 KB with `allowed-tools: Bash(playwright-cli:*)`. | **Adopt** as the default for public pages. **BROWSER** |
| microsoft/playwright-mcp | Apache-2.0 / 2026-10-08 | Useful flags: `--isolated`, `--storage-state`, `--secrets <dotenv>`, `--allowed-origins` / `--blocked-origins` ("*not* a security boundary"), `--snapshot-mode none`, `--timeout-settle 500ms`, `--image-responses omit`, `--mobile` (lighter pages), `--save-session` | Keep as the fallback for long stateful loops. If used, run with `--isolated --image-responses omit --timeout-settle 800`. **BROWSER** |
| **vercel-labs/agent-browser** | Apache-2.0 / 2026-10-15 | `@eN` refs; `--allowed-domains`, `--content-boundaries` (nonce-delimited page text, labeled untrusted), `--max-output`; `--auto-connect` + `state save` to import auth from your Chrome; `--profile`; video recording. Its skill description says "**Prefer agent-browser over any built-in browser automation**" and claims Slack and Electron work, which would hijack triggers. | **Adopt the CLI, rewrite the skill description**, or use only via browser-task. Its content-boundary and domain flags are the best injection hygiene found. **BROWSER, GUARD** |
| ChromeDevTools/chrome-devtools-mcp | Apache-2.0 / 2026-10-16 | Usage statistics are **on by default** (`--no-usage-statistics`). Performance traces may send URLs to Google CrUX (`--no-performance-crux`). `--slim` mode, `--autoConnect` to your running Chrome (all windows of the default profile), `--browser-url`. Ships its own skills (a11y, LCP, memory leaks). | **Adopt on demand only** for debugging, with both opt-out flags. **BROWSER** |
| browserbase/stagehand | MIT / 2026-10-15 | `observe()` returns selectors so credentials never reach the model; `act()` "self-heals"; `extract()` with a schema. It's a separate LLM loop (TypeScript/Python SDK). | **Borrow the idea:** cache the selectors found by an observe step in the task checkpoint, so re-runs replay deterministically and only re-observe on failure. That's exactly the resumability rule in §11. Don't run it as a second agent. |
| browser-use/browser-use | MIT / 2026-10-16 | A separate Python agent with its own LLM. `ANONYMIZED_TELEMETRY` is on unless disabled. Cloud and stealth upsell. | **Avoid** as the main path (double agent, telemetry). **BROWSER** |
| Claude in Chrome | Built in | The only option with your signed-in sessions | Keep it for authenticated portals (job sites, Gmail web), plus the ToB `chrome-mcp-troubleshooting` notes. |

Recommended browser-task ladder:
1. A connector, API or CLI.
2. `playwright-cli` or `agent-browser` with `--allowed-domains` and content boundaries, for public pages.
3. Claude in Chrome for signed-in pages.
4. DevTools MCP only for debugging.

Checkpoint observed selectors in `PROGRESS.md`. Never submit without confirmation; that rule is unchanged.

---

## 7. Conflicts with the current harness design (summary)

1. **Always-on injection versus small memory.** superpowers' SessionStart (~800 tokens wrapped in `<EXTREMELY_IMPORTANT>`), planning-with-files' PreToolUse plan injection on every read, and ECC's observe-everything hooks all violate §0.5 "keep memory files small" and "avoid capture-everything." Allowed instead: one SessionStart hook for `clear|compact` that prints about 30 lines of PROGRESS.md and HANDOFF.md.
2. **Auto-applied learning versus non-negotiable #4.** ECC instincts at ≥0.7 and agent-memory's unattended add/update both auto-apply. In the harness, everything stays a *proposal*, and confidence and decay are metadata for review only.
3. **Anti-rationalization gate versus the scoped verifier.** Use ToB's mechanism with the harness's criteria-only wording.
4. **Self-reported completion (Ralph `<promise>`) versus non-negotiable #3** (independent verification). Pair any loop with `/verify` or `/goal`.
5. **Plugin agents ignore hooks in their frontmatter** (BLUEPRINT §0.5). Any vendored skill-level hooks (planning-with-files, ECC) must move into the plugin's `hooks/hooks.json`.
6. **Licenses.**
   - ToB claude-code-config and 199-bio have no LICENSE file: borrow ideas only.
   - ToB skills is CC-BY-SA: keep the attribution and the license on vendored files.
   - basic-memory is AGPL: don't vendor it.
   - Everything else read is MIT or Apache-2.0.
7. **Third-party data egress:** fast-jev-compaction (whole transcript), DevTools MCP (usage stats and CrUX on by default), browser-use (telemetry on by default), and SkillOpt-Sleep real backends (transcript excerpts). Set each opt-out explicitly, or use local or handoff modes.

## 8. Context-cost cheat sheet (approximate)

| Item | Always-on cost | On-demand cost |
|---|---|---|
| superpowers | about 800 tokens (SessionStart) plus 15 descriptions | 163 KB of skills |
| planning-with-files | per-tool head-30 injection | 40 KB skill |
| Playwright MCP / Claude in Chrome / DevTools MCP | about 13.7k / 15.4k / 19.0k tokens of tool schemas (third-party measurement) | none |
| playwright-cli, agent-browser | one skill description (about 60-200 tokens) | 15 KB / 38 KB (`skills get core --full`) |
| REA | the MCP schema catalog (large; scope it to one agent) | 23.5 KB skill |
| hookify | none (no skill preload) | per-tool python start |
| Harness's own 22 skill descriptions | about 5.9 KB ≈ 1.5k tokens | none |
