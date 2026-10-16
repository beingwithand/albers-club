<!-- GENERATED — do not edit; run scripts/harness_index.py --write -->
# Harness index

GENERATED — do not edit; run scripts/harness_index.py --write. Machine-readable graph: [components.json](components.json). Edges mean "uses"; `--affected <files>` lists the eval areas to re-run after a change. Counts: 13 agents, 30 skills, 9 hooks, 26 scripts, 12 rubrics, 12 evals, 51 types, 11 docs, 22 principles. Eval coverage: **23/23 work components (100.0%)**, 20 exempt. Learning coverage: **56/56 (100.0%)**, 13 exempt. Errors: 21. Warnings: 7.

## Agents

| agent | model | preloads | purpose |
|---|---|---|---|
| [annotation-assistant](../agents/annotation-assistant.md) | sonnet | annotation-workflow | Data-annotation helper. |
| [asset-decomposer](../agents/asset-decomposer.md) | sonnet | asset-decompose | Breaks a digital or art source file (PSD, AI, SVG, Figma, PDF, video, audio) into compone… |
| [browser-operator](../agents/browser-operator.md) | sonnet | browser-task | Carries out Chrome tasks (filling documents and forms, navigating portals, collecting dat… |
| [code-reviewer](../agents/code-reviewer.md) | opus | coding-standards, mishap | Fresh-context code reviewer that applies the shared coding-standards checklist. |
| [coder](../agents/coder.md) | sonnet | coding-standards, prior-art, mishap | Makes code changes in repos against a stated spec, with tests as proof. |
| [intake-extractor](../agents/intake-extractor.md) | haiku | intake | Converts source documents (PDF, DOCX, HTML) into cited knowledge-wiki pages with provenan… |
| [interviewer](../agents/interviewer.md) | sonnet | interview | Runs the short scope interview before any non-trivial task, proposing answers from stored… |
| [job-tracker](../agents/job-tracker.md) | haiku | email-scan | Scans Gmail (via the connector) for job applications, replies, rejections and interview i… |
| [librarian](../agents/librarian.md) | sonnet | distill-principles | Weekly curator of the harness. |
| [orchestrator](../agents/orchestrator.md) | opus | interview, fanout-plan, verify, handoff, mishap | Default main-thread agent (set by the plugin's settings.json). |
| [translator](../agents/translator.md) | sonnet | translate, synopsis, style-capture | KO↔EN translator, KO→KO synopsis condenser (length-capped, reviewer-rule driven), and reg… |
| [verifier](../agents/verifier.md) | opus | - | Independent, skeptical verifier. |
| [web-researcher](../agents/web-researcher.md) | sonnet | - | Research worker for one sub-question or source tier. |

## Skills

Flags: M = manual only (`disable-model-invocation`), H = hidden from the user (`user-invocable: false`), F = runs forked in an agent.
| skill | flags | scripts | purpose |
|---|---|---|---|
| [annotation-workflow](../skills/annotation-workflow/SKILL.md) | - | - | Data-annotation workflow. |
| [asset-decompose](../skills/asset-decompose/SKILL.md) | - | palette, psd_layers | Break a digital or art source file into its component assets (layers, text, images, vecto… |
| [backcatalog](../skills/backcatalog/SKILL.md) | - | - | Reverse-engineer the user's past work. |
| [browser-task](../skills/browser-task/SKILL.md) | - | - | Run a Chrome task (fill a document or form, navigate a portal, collect data) reliably. |
| [check](../skills/check/SKILL.md) | - | - | Default for any factual, technical, product, pricing, legal or "what's current" question. |
| [coding-standards](../skills/coding-standards/SKILL.md) | H | guard_protected | The shared coding rules for writing and reviewing code (surgical diffs, read-before-edit,… |
| [compact-prep](../skills/compact-prep/SKILL.md) | - | - | Prepare a safe /compact - refresh HANDOFF.md first, then produce one precise `/compact <i… |
| [distill-principles](../skills/distill-principles/SKILL.md) | - | patterns | Decompose what the user says, decides and corrects into short, reusable principles that a… |
| [email-scan](../skills/email-scan/SKILL.md) | - | - | Scan Gmail for job-search mail (application confirmations, recruiter replies, rejections,… |
| [fanout-plan](../skills/fanout-plan/SKILL.md) | - | usage_guard | Decide whether and how wide to fan out before spawning any subagents. |
| [handoff](../skills/handoff/SKILL.md) | - | - | Write HANDOFF.md so a cold reader (the next session after /clear, another machine, or ano… |
| [intake](../skills/intake/SKILL.md) | - | - | Ingest project inputs (PDFs, briefs, docs, links) into the project's knowledge/ wiki with… |
| [interview](../skills/interview/SKILL.md) | - | - | Short scope interview before any non-trivial task. |
| [invoice](../skills/invoice/SKILL.md) | - | invoice | Prepare a freelance invoice for translation or annotation work (per source word, per Kore… |
| [job-application](../skills/job-application/SKILL.md) | - | claim_check | Tailor a CV and cover letter to one job posting, with an explicit requirement-by-requirem… |
| [mishap](../skills/mishap/SKILL.md) | - | - | Log a mistake that was noticed and fixed (by the agent or the user) with root cause, prev… |
| [new-project](../skills/new-project/SKILL.md) | - | - | Start a new project from the standard template. |
| [pattern-review](../skills/pattern-review/SKILL.md) | M | eval_gate, label_events, patterns, schema_check | Multi-layer pattern review. |
| [prior-art](../skills/prior-art/SKILL.md) | - | - | Before implementing any technical feature, research how others have built it (apps, repos… |
| [retro](../skills/retro/SKILL.md) | - | patterns | End-of-session retrospective. |
| [review-week](../skills/review-week/SKILL.md) | M | harness_index | Weekly improvement loop. |
| [self-eval](../skills/self-eval/SKILL.md) | - | eval_gate, harness_index, schema_check | Run the eval set for an area, skill or agent and gate the result against the baseline. |
| [style-capture](../skills/style-capture/SKILL.md) | - | style_pairs | Log a draft→final pair whenever the user edits (or approves) text Claude drafted, in any… |
| [style-guide](../skills/style-guide/SKILL.md) | - | style_pairs | Distill the user's logged draft→final pairs into a personal, data-derived style guide per… |
| [synopsis](../skills/synopsis/SKILL.md) | - | textlen | Condense a Korean synopsis to a length limit (e.g. ~150 → 110) for streaming-metadata wor… |
| [translate](../skills/translate/SKILL.md) | - | style_pairs, translation_qa | Translate between Korean and English in the user's own style and register (formal email,… |
| [translation-qa](../skills/translation-qa/SKILL.md) | - | translation_qa | Run deterministic CAT-style QA on a translation or a length-capped Korean rewrite. |
| [verify](../skills/verify/SKILL.md) | F→verifier | verify_gate | Independently verify a piece of work against pre-agreed criteria before it is marked done. |
| [web-research](../skills/web-research/SKILL.md) | - | - | Scoped, cited, state-of-the-art web research with automatic fan-out. |
| [why](../skills/why/SKILL.md) | - | - | Record a decision with its intent, justification, evidence, alternatives and a checkable… |

## Hooks

| event | matcher | runs |
|---|---|---|
| PostCompact | - | `hooks/precompact_snapshot.py` post |
| PostToolUse | Edit\|Write\|MultiEdit\|NotebookEdit | `hooks/step_check.py`  |
| PreCompact | manual\|auto | `hooks/precompact_snapshot.py`  |
| PreToolUse | Bash | `hooks/guard_protected.py`  |
| SessionEnd | - | `hooks/log_event.py` session_end |
| SessionStart | compact\|clear | `hooks/postcompact_reinject.py`  |
| Stop | - | `hooks/verify_gate.py`  |
| UserPromptSubmit | - | `hooks/log_event.py` prompt |
| UserPromptSubmit | - | `hooks/usage_guard.py`  |

## Scripts

| script | used by | tests | purpose |
|---|---|---|---|
| [hooks/_common.py](../hooks/_common.py) | - | **none** | Shared helpers for the usage / compaction hooks. |
| [hooks/guard_protected.py](../hooks/guard_protected.py) | PreToolUse[Bash], coding-standards | review_wiring, usage_and_compaction | PreToolUse guard: block Bash commands that write to protected eval/rubric/test paths. |
| [hooks/log_event.py](../hooks/log_event.py) | SessionEnd, UserPromptSubmit | hooks, review_wiring, schema_check, scripts, usage_and_compaction | Append a raw event to $HARNESS_DATA/log/YYYY-MM.jsonl from a Claude Code hook. |
| [hooks/postcompact_reinject.py](../hooks/postcompact_reinject.py) | SessionStart[compact\|clear] | review_wiring, usage_and_compaction | SessionStart hook (matcher "compact", also "clear"): put the durable state back in context. |
| [hooks/precompact_snapshot.py](../hooks/precompact_snapshot.py) | PostCompact, PreCompact[manual\|auto] | review_wiring, usage_and_compaction | PreCompact hook: write a recoverable snapshot before compaction summarizes the thread away. |
| [hooks/step_check.py](../hooks/step_check.py) | PostToolUse[Edit\|Write\|MultiEdit\|NotebookEdit], hooks/verify_gate.py | review_wiring, step_check | PostToolUse hook (Edit\|Write\|MultiEdit\|NotebookEdit): cheap syntax check of the edited file. |
| [hooks/usage_guard.py](../hooks/usage_guard.py) | UserPromptSubmit, fanout-plan | review_wiring, usage_and_compaction | UserPromptSubmit hook: turn context size and 5-hour / 7-day usage into advice for Claude. |
| [hooks/verify_gate.py](../hooks/verify_gate.py) | Stop, hooks/step_check.py, verify | hooks, review_wiring, step_check, usage_and_compaction | Stop hook: don't let a turn end while done items lack a verification event. |
| [scripts/autocommit_data.sh](../scripts/autocommit_data.sh) | - | scripts | Commit and push $HARNESS_DATA (the private data repo: log/, style/, sessions/, labels/, evals/results/) |
| [scripts/claim_check.py](../scripts/claim_check.py) | job-application | claim_check, review_wiring | Fact-check gate for CVs and cover letters: every claim in a draft must trace to the facts file. |
| [scripts/eval_gate.py](../scripts/eval_gate.py) | scripts/patterns.py, scripts/run_evals.py, pattern-review, self-eval | run_evals, scripts | Accept or reject a candidate policy change by comparing eval results (BLUEPRINT.md §0.5 step 4). |
| [scripts/glossary.py](../scripts/glossary.py) | - | glossary, translation_qa | Glossary helper for a project's knowledge/glossary.md (format: templates/glossary.md). |
| [scripts/harness_index.py](../scripts/harness_index.py) | review-week, self-eval | harness_index | Build the harness component graph, check it, and write docs/INDEX.md + docs/components.json. |
| [scripts/invoice.py](../scripts/invoice.py) | invoice | invoice, usage_and_compaction | Freelance invoices for translation and annotation work: compute, number, ledger, track payment. |
| [scripts/kb.py](../scripts/kb.py) | - | kb, review_wiring, schema_check | Knowledge-base helper for a project's knowledge/ directory (BLUEPRINT §0.5, §4.11, §4.12). |
| [scripts/label_events.py](../scripts/label_events.py) | scripts/patterns.py, scripts/weekly_report.py, pattern-review | scripts | Weekly labeling pass for the raw event log (BLUEPRINT.md §0.5 "improvement loop", schema/event.md). |
| [scripts/palette.py](../scripts/palette.py) | asset-decompose | asset_scripts | Extract a colour palette from an image: hex colours, pixel shares, roles and WCAG contrast. |
| [scripts/patterns.py](../scripts/patterns.py) | librarian, distill-principles, pattern-review, retro | patterns | Multi-layer pattern system: mine, promote/demote, and reflect on recurring patterns (docs/PATTERNS.md). |
| [scripts/psd_layers.py](../scripts/psd_layers.py) | asset-decompose | asset_scripts | List the layers of a PSD/PSB and write them as assets/assets.yaml entries. |
| [scripts/run_evals.py](../scripts/run_evals.py) | - | run_evals | Run an eval area's deterministic tasks and write an EvalRun JSON for scripts/eval_gate.py. |
| [scripts/schema_check.py](../scripts/schema_check.py) | pattern-review, self-eval | patterns, review_wiring, schema_check | Validate harness data files against schema/ontology.yaml (stdlib only; run with `python3 -I`). |
| [scripts/statusline.py](../scripts/statusline.py) | hooks/usage_guard.py | usage_and_compaction | Claude Code status line: context budget, 5-hour / 7-day usage, cache, cost. |
| [scripts/style_pairs.py](../scripts/style_pairs.py) | style-capture, style-guide, translate | schema_check, style_pairs | StylePair store: draft -> final pairs the user edited, used as few-shot references. |
| [scripts/textlen.py](../scripts/textlen.py) | scripts/invoice.py, scripts/translation_qa.py, synopsis | review_wiring, run_evals, textlen | Count text length the way length-limited deliverables (e.g. synopses) are measured. |
| [scripts/translation_qa.py](../scripts/translation_qa.py) | translate, translation-qa | review_wiring, translation_qa | Deterministic QA for a translation (KO<->EN, also KO->KO rewrites): the CAT-tool checks a human reviewer runs. |
| [scripts/weekly_report.py](../scripts/weekly_report.py) | - | schema_check, scripts, step_check | Weekly summary of the event log, per scope, as Markdown (BLUEPRINT.md §4.5, §4.13; librarian review). |

## Rubrics and eval areas

| rubric | status | producer | eval area (repo tasks) | applies to |
|---|---|---|---|---|
| [annotation-batch](../rubrics/annotation-batch.yaml) | active | annotation-assistant | annotation (0) | A batch of annotation items/responses prepared or checked with annotation-assis… |
| [asset-package](../rubrics/asset-package.yaml) | active | asset-decomposer | art (0) | Decomposition of a digital/art source into component assets plus assets/assets.… |
| [browser-task](../rubrics/browser-task.yaml) | draft | browser-operator | browser (0) | One Chrome task: filling a form or document, navigating a portal, or collecting… |
| [code-change](../rubrics/code-change.yaml) | active | coder | code (0), harness (20) | Any change to a repository: feature, fix, refactor, script |
| [email-scan](../rubrics/email-scan.yaml) | draft | job-tracker | email-scan (0) | One email-scan run: thread classifications, Application record updates and the… |
| [handoff](../rubrics/handoff.yaml) | active | main session | **none** | Any HANDOFF.md written by the handoff or compact-prep skill (session to session… |
| [intake-extraction](../rubrics/intake-extraction.yaml) | active | intake-extractor | intake (0) | Extraction of PDFs/briefs/emails/links into knowledge/raw, knowledge/wiki, inde… |
| [invoice](../rubrics/invoice.yaml) | draft | main session | invoice (0) | One invoice made by skills/invoice (spec JSON + deliverables/*_invoice_*.md + l… |
| [job-application](../rubrics/job-application.yaml) | active | job-tracker, translator | job-search (0) | Materials for one Application (org, role): cover letter, tailored CV, form answ… |
| [research-report](../rubrics/research-report.yaml) | active | web-researcher | research (0) | Any cited research report or literature/market/tool comparison |
| [synopsis](../rubrics/synopsis.yaml) | active | translator | synopsis (0) | skills/synopsis drafts and the user's final combined synopsis |
| [translation](../rubrics/translation.yaml) | active | translator | translation (0) | Any KO->EN or EN->KO translation or register-aware rewrite (agent: translator) |

Eval tasks live in `evals/<area>/tasks/` (repo) or `$HARNESS_DATA/evals/<area>/tasks/`; results in `$HARNESS_DATA/evals/results/<area>/`. Run them with the `self-eval` skill.

## Eval coverage

| component | rubric | area | status |
|---|---|---|---|
| agent:annotation-assistant | annotation-batch | annotation | covered |
| agent:asset-decomposer | asset-package | art | covered |
| agent:browser-operator | browser-task (draft) | browser | covered |
| agent:code-reviewer | code-change | code, harness | covered (config) |
| agent:coder | code-change | code, harness | covered |
| agent:intake-extractor | intake-extraction | intake | covered |
| agent:job-tracker | email-scan (draft) | email-scan | covered (config) |
| agent:translator | job-application, synopsis, translation | job-search, synopsis, translation | covered |
| agent:web-researcher | research-report | research | covered |
| skill:annotation-workflow | annotation-batch | annotation | covered |
| skill:asset-decompose | asset-package | art | covered |
| skill:browser-task | browser-task (draft) | browser | covered |
| skill:check | research-report | research | covered (config) |
| skill:coding-standards | code-change | code, harness | covered (inherited) |
| skill:email-scan | email-scan (draft) | email-scan | covered (config) |
| skill:intake | intake-extraction | intake | covered (inherited) |
| skill:invoice | invoice (draft) | invoice | covered |
| skill:job-application | job-application | job-search | covered |
| skill:prior-art | research-report | research | covered (config) |
| skill:synopsis | synopsis | synopsis | covered |
| skill:translate | translation | translation | covered |
| skill:translation-qa | synopsis, translation | synopsis, translation | covered (config) |
| skill:web-research | research-report | research | covered (config) |

Exempt (meta/router/judge, see `scripts/harness_index.json`): interviewer, librarian, orchestrator, verifier, backcatalog, compact-prep, distill-principles, fanout-plan, handoff, interview, mishap, new-project, pattern-review, retro, review-week, self-eval, style-capture, style-guide, verify, why.

## Learning coverage ([contracts](../learning/contracts.yaml))

Every agent, skill and script declares how it learns (signals → logged as → learns → evaluated by, cadence, owner) or is exempt with a reason. **56 contracts (56 draft), 13 exempt, 0 gaps (100.0%).**
- monthly: asset-decomposer, browser-operator, intake-extractor, interviewer, verifier, asset-decompose, browser-task, compact-prep, distill-principles, fanout-plan, handoff, intake, invoice, job-application, new-project, pattern-review, prior-art, translation-qa, verify, why, hooks/guard_protected.py, hooks/log_event.py, hooks/postcompact_reinject.py, hooks/precompact_snapshot.py, hooks/step_check.py, hooks/usage_guard.py, hooks/verify_gate.py
- on-change: backcatalog, new-project, self-eval, scripts/eval_gate.py, scripts/harness_index.py, scripts/run_evals.py
- per-run: annotation-assistant, asset-decomposer, browser-operator, code-reviewer, coder, intake-extractor, interviewer, job-tracker, orchestrator, translator, verifier, web-researcher, annotation-workflow, asset-decompose, browser-task, check, compact-prep, email-scan, fanout-plan, handoff, intake, interview, invoice, job-application, mishap, prior-art, retro, style-capture, synopsis, translate, translation-qa, verify, web-research, why, hooks/guard_protected.py, hooks/log_event.py, hooks/postcompact_reinject.py, hooks/precompact_snapshot.py, hooks/step_check.py, hooks/usage_guard.py, hooks/verify_gate.py
- weekly: annotation-assistant, code-reviewer, coder, job-tracker, librarian, orchestrator, translator, web-researcher, annotation-workflow, coding-standards, email-scan, mishap, pattern-review, review-week, self-eval, style-guide, translate, web-research, scripts/harness_index.py, scripts/label_events.py, scripts/patterns.py, scripts/run_evals.py, scripts/weekly_report.py
- todo (declared, not built yet): script:scripts/voice.py, skill:email-draft, skill:voice-harvest

## Who uses what (`X ← users`; docs and other files left out)

- skill `annotation-workflow` ← annotation-assistant
- skill `asset-decompose` ← asset-decomposer, scripts/psd_layers.py
- skill `browser-task` ← browser-operator
- skill `check` ← orchestrator
- skill `coding-standards` ← code-reviewer, coder, orchestrator
- skill `compact-prep` ← hooks/usage_guard.py, handoff
- skill `distill-principles` ← librarian, backcatalog, pattern-review, prior-art, review-week, style-guide
- skill `email-scan` ← job-tracker
- skill `fanout-plan` ← orchestrator, prior-art, self-eval, web-research
- skill `handoff` ← orchestrator, hooks/usage_guard.py, compact-prep
- skill `intake` ← intake-extractor, annotation-workflow, new-project
- skill `interview` ← interviewer, orchestrator, new-project
- skill `mishap` ← code-reviewer, coder, orchestrator, browser-task, compact-prep, handoff, style-capture
- skill `new-project` ← job-application
- skill `pattern-review` ← librarian, review-week
- skill `prior-art` ← coder
- skill `retro` ← backcatalog, distill-principles, mishap, synopsis
- skill `review-week` ← librarian, invoice, pattern-review
- skill `style-capture` ← translator, synopsis, translate
- skill `style-guide` ← style-capture
- skill `synopsis` ← translator, translation-qa
- skill `translate` ← translator, translation-qa
- skill `translation-qa` ← synopsis, translate
- skill `verify` ← code-reviewer, coder, orchestrator, annotation-workflow, asset-decompose, browser-task, check, email-scan, fanout-plan, invoice, job-application, new-project, pattern-review, review-week, self-eval, synopsis, translate, translation-qa, web-research
- skill `web-research` ← orchestrator, check
- skill `why` ← prior-art
- agent `annotation-assistant` ← orchestrator
- agent `asset-decomposer` ← orchestrator
- agent `browser-operator` ← orchestrator
- agent `code-reviewer` ← coder, orchestrator, coding-standards
- agent `coder` ← code-reviewer, orchestrator, coding-standards
- agent `intake-extractor` ← orchestrator, backcatalog
- agent `job-tracker` ← orchestrator
- agent `translator` ← orchestrator
- agent `verifier` ← code-reviewer, orchestrator, backcatalog, self-eval, translation-qa, verify
- agent `web-researcher` ← orchestrator, prior-art, web-research
- ontology writers: `asset-decompose` → Asset; `backcatalog` → Lesson, WikiPage; `check` → ResearchNote; `distill-principles` → Principle; `email-scan` → Application; `handoff` → Handoff; `hooks/_common.py` → Event; `hooks/log_event.py` → Event; `hooks/precompact_snapshot.py` → Handoff; `intake` → WikiPage; `interview` → Preference; `job-application` → Application; `job-tracker` → Application; `mishap` → Mishap; `new-project` → Project; `orchestrator` → ProgressItem, Task; `pattern-review` → Encoding, MetaPattern, Pattern; `retro` → Lesson, Pattern, SessionNote; `review-week` → Correction; `scripts/glossary.py` → GlossaryTerm; `scripts/invoice.py` → Invoice, LedgerEntry; `scripts/kb.py` → BackcatalogRow, Document, WikiPage; `scripts/label_events.py` → Correction, Event; `scripts/palette.py` → Asset, Palette; `scripts/patterns.py` → Encoding, MetaPattern, Pattern; `scripts/psd_layers.py` → Asset; `scripts/statusline.py` → HarnessState; `scripts/style_pairs.py` → StylePair; `self-eval` → EvalRun, Evaluation; `style-guide` → StyleGuide; `synopsis` → ReviewerRule; `verifier` → IntakeLogEntry; `web-research` → ResearchNote; `why` → Decision

## Ontology types (by store root)

- **harness-data**: Account*, Application, BackcatalogRow, Client*, Contact*, Correction, Encoding, EvalRun, EvalTask, Evaluation, Event, HarvestRun, JobLead*, LedgerEntry, MetaPattern, Organization*, Pattern, Platform*, Preference, Proof, ResearchNote, StyleGuide, StylePair, Task, VoiceProfile, VoiceRule
- **home**: HarnessState
- **msg-vault**: Attachment*, Message*, StyleSample*, SyncCursor, Thread*, VoiceFeatures, VoiceSample
- **project**: Asset, Decision, Document, GlossaryTerm, Handoff, IntakeLogEntry, Invoice, Lesson, Mishap, Palette, ProgressItem, Project, ReviewerRule, SessionNote, WikiPage
- **repo**: Principle, Rubric

`*` = planned (declared, nothing writes it yet). Stores and writers: `schema/ontology.yaml`.

## Docs and principles

| doc | title | mentioned by |
|---|---|---|
| [BACKLOG.md](BACKLOG.md) | Harness backlog (from the architecture scout, 2026-10-16) | 0 |
| [BACKUP.md](BACKUP.md) | Backup plan: nothing lives only on one laptop | 3 |
| [FANOUT.md](FANOUT.md) | Fan-out policy (v1, 2026-10-16) | 19 |
| [INTAKE.md](INTAKE.md) | Intake how-to | 2 |
| [LOCAL_ONLY.md](LOCAL_ONLY.md) | Local-only tools for client text | 5 |
| [MESSAGING.md](MESSAGING.md) | Messaging and email: ingest and triggers | 2 |
| [PATTERNS.md](PATTERNS.md) | Pattern layers (v1, 2026-10-16) | 4 |
| [REGISTERS.md](REGISTERS.md) | Registers / 문체 구분 | 3 |
| [SECURITY.md](SECURITY.md) | Security | 1 |
| [VERIFICATION.md](VERIFICATION.md) | Step verification protocol (v1, 2026-10-16) | 7 |
| [VISION.md](VISION.md) | Vision: why this harness exists | 1 |

Principles ([PRINCIPLES.md](../global/PRINCIPLES.md)): 1 Study before building · 2 Look in the right places, at the right depth · 3 Consider adjacent ideas · 4 Check it's deployable, not just interesting · 5 Leave room to experiment · 6 State of the art, as of today · 7 Intent and context first · 8 Every step has a justification and proof · 9 Verify independently · 10 Learn from every mistake · 11 Never lose context between handoffs · 12 Nothing lives in only one place · 13 Break things into parts · 14 Turn what I say into principles · 15 Ask first, then act · 16 Improve on several measures at once · 17 Never compromise on quality · 18 Fan out deliberately · 19 Check, verify, log · 20 Think in layers · 21 Verify every step · 22 Every process learns.

## Errors and warnings

- ERROR dangling: schema/STORAGE.md references scripts/voice.py (missing)
- ERROR dangling: schema/STORAGE.md references scripts/voice.py (missing)
- ERROR dangling: schema/STORAGE.md references scripts/voice.py (missing)
- ERROR dangling: schema/STORAGE.md references scripts/voice.py (missing)
- ERROR dangling: schema/STORAGE.md references scripts/voice.py (missing)
- ERROR dangling: schema/STORAGE.md references scripts/voice.py (missing)
- ERROR dangling: schema/STORAGE.md references scripts/voice.py (missing)
- ERROR dangling: schema/STORAGE.md references skill 'voice-harvest' (missing; add to external_skills in scripts/harness_index.json if it is not ours)
- ERROR dangling: schema/event.md references scripts/voice.py (missing)
- ERROR dangling: schema/event.md references scripts/voice.py (missing)
- ERROR dangling: evals/harness/ tasks name component scripts/<script>.py (missing)
- ERROR ontology: HarvestRun.store.writer names scripts/voice.py (missing)
- ERROR ontology: HarvestRun.store.writer names skills/voice-harvest (missing)
- ERROR ontology: SyncCursor.store.writer names scripts/voice.py (missing)
- ERROR ontology: SyncCursor.store.writer names skills/voice-harvest (missing)
- ERROR ontology: VoiceFeatures.store.writer names scripts/voice.py (missing)
- ERROR ontology: VoiceProfile.store.writer names scripts/voice.py (missing)
- ERROR ontology: VoiceRule.store.writer names scripts/voice.py (missing)
- ERROR ontology: VoiceRule.store.writer names skills/voice-harvest (missing)
- ERROR ontology: VoiceSample.store.writer names scripts/voice.py (missing)
- ERROR ontology: VoiceSample.store.writer names skills/voice-harvest (missing)
- orphan: agent interviewer (agents/interviewer.md) is referenced by nothing
- orphan: agent librarian (agents/librarian.md) is referenced by nothing
- orphan: doc docs/BACKLOG.md (docs/BACKLOG.md) is referenced by nothing
- orphan: script scripts/run_evals.py (scripts/run_evals.py) is referenced by nothing
- draft rubric: rubrics/browser-task.yaml (status: draft; the user must review it before it gates anything)
- draft rubric: rubrics/email-scan.yaml (status: draft; the user must review it before it gates anything)
- draft rubric: rubrics/invoice.yaml (status: draft; the user must review it before it gates anything)
