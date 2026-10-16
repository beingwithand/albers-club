# Changelog

All notable changes, decisions and lessons for the harness.
Format: [Keep a Changelog](https://keepachangelog.com). Updated at the end of every session (`scripts/changelog.py`, `/retro`, the session-end pipeline).

## [Unreleased]

<!-- last-update: 2026-10-16T23:59:00+00:00 -->
#### Session 2026-10-16 (initial build after laptop loss)
### Added
- Plugin scaffold (marketplace, manifest), global `CLAUDE.md` with global invariants, `PRINCIPLES.md` (1–22), `VISION.md`, `DAY1.md`.
- Agents: orchestrator (the default main-thread agent), interviewer, translator, verifier, web-researcher, intake-extractor, annotation-assistant, job-tracker, coder, code-reviewer, asset-decomposer, browser-operator, librarian.
- Skills:
  - **Core workflow:** handoff (with cold-read test), compact-prep, retro, mishap, why, verify, check, web-research, prior-art, fanout-plan.
  - **Documents and language:** intake (HWP via kordoc), backcatalog, translate, translation-qa, synopsis (Toin), style-capture, style-guide.
  - **Work tasks:** job-application, email-scan, invoice, annotation-workflow, asset-decompose, browser-task, new-project.
  - **Learning and quality:** interview, distill-principles, pattern-review, review-week, coding-standards, self-eval.
- Hooks: claim gate (blocks unproven push/commit claims), prompt and session logging with EN/KO correction tagging, verification Stop gate, usage guard (context, 5-hour and 7-day), pre-compact snapshot, post-compact re-inject, eval/rubric write guard, step_check.
- Scripts:
  - **Knowledge and language:** kb.py, style_pairs.py, translation_qa.py, glossary.py, textlen.py.
  - **Work tools:** invoice.py, claim_check.py, palette.py, psd_layers.py.
  - **Learning and evals:** label_events.py, eval_gate.py, weekly_report.py, patterns.py, schema_check.py.
  - **Operations:** statusline.py, autocommit_data.sh, changelog.py, run_evals.py.
- Ontology v0.2 (46+ types, a storage and privacy map, typed relations, Account, a research ledger, pattern layers L0–L5), `STORAGE.md`, `event.md`. The **Party** registry (D12) is decided but **not yet implemented**.
- Rubrics for the core task types (several still `status: draft`). Eval areas: **only `evals/harness` has real tasks (20)**, and the other areas are templates awaiting the user's real tasks. Mac bootstrap, Brewfile, launchd jobs, settings template with fences; docs for backup, security, local-only processing, messaging, fan-out, verification and patterns.

### Decisions
- D1–D14 (D14 includes the Q3 confirmation) are recorded in `research_notes/Claude harness/session_2026-10-16_harness_build.md`. Highlights:
  - plugin packaging
  - eval-gated self-improvement
  - auto mode with sandbox instead of bypass
  - fan-out calibration
  - flat project folders plus a Party registry
  - the coder/reviewer pair
  - client-text prompts in both the vault and private GitHub
  - finance records kept 10 years

### Lessons
- **Audit (2026-10-16 late):** several CHANGELOG claims were ahead of the synced repo (items only in the working copy, "moved" when the notes were only copied, the claim gate not yet registered in `hooks.json`). These have been corrected. Rule: changelog entries describe only what exists in the synced repo, checked by audit.
- Saving non-project files in an unrelated (public) repo was a mistake. Check repo visibility before the first push.
- When a source is unreachable, say so and ask; never imply it was read.
- Preloading `disable-model-invocation` skills into subagents fails silently. `harness_index.py` now checks for it.
- Parallel appends need locks, and event IDs need ≥32 random bits.
- SQLite trigram search misses 2-syllable Korean words (found in research). The planned search index must add a Kiwi column plus a LIKE fallback. **Not yet implemented.**
