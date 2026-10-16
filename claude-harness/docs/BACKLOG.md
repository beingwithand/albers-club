# Harness backlog (from the architecture scout, 2026-10-16)

Full notes: `research_notes/Claude harness/scout_architecture.md`.

## Done
- [x] Bash write guard for `evals/`, `rubrics/` and `tests/`: the `hooks/guard_protected.py` PreToolUse hook.
- [x] Extra credential paths added to the Read deny list: gh, docker, kube, npmrc, pypirc.
- [x] Deny `--no-verify` on git commit and push.
- [x] Handoff records the git commit and branch, so a stale handoff can be detected.
- [x] Item 1 (command layer): `hooks/verify_gate.py` Stop hook blocks when `PROGRESS.md`/`tasks.json` marks items done after the last non-failing `verification` event for this cwd; honors `stop_hook_active`, off via `HARNESS_VERIFY_GATE=0`. The fast-model prompt gate (layer b) is still open.
- [x] Item 5: `hooks/log_event.py` tags prompts with `correction_candidate` / `correction_confidence` from an English + Korean regex table (claude-reflect shape, MIT). Labeling stays weekly.

## Next, in priority order
1. ~~**Stop-hook verification gate.**~~ Command layer done (see Done); the fast-model gate below is still open.
   - Block the end of a turn when `PROGRESS.md` marks something done with no verification event.
   - Add a fast-model gate (Trail of Bits style, but checking only the stated criteria).
   - Guard against the hook triggering itself in a loop (planning-with-files).
2. **Run skill evals** with `claude plugin eval --ablation with-without`.
   - Copy Trail of Bits' `check_contamination.py` (CC-BY-SA, so keep attribution).
   - Needs an API key, so use the Max monthly API credit.
3. **Tune skill descriptions** with the official skill-creator loop: 20 should-trigger and should-not-trigger queries, split 60/40. These skills currently overlap: retro, handoff and distill-principles; intake and backcatalog; style-capture and style-guide.
4. **Reshape the librarian loop like SkillOpt-Sleep:** harvest, mine, replay, make a bounded edit, gate it, stage it for review. Port the logic from `gate.py` into `eval_gate.py`.
5. ~~**Cheap correction detection**~~ (done, see Done) in `log_event.py`, using claude-reflect's pattern tables plus **Korean** patterns. The hook only tags; labeling stays weekly.
6. **`kb.py fidelity`:** every number, date and quote must appear word for word in the raw source (port `check_evidence.py`, MIT). Also add `valid_to` instead of deleting facts, and never record a global "not found" claim.
7. **Comparison mode for web-research:** an items file × a fields file, one JSON per item, `[uncertain]` markers, a validator, and resumable runs (Deep-Research-skills).
8. **Browser:** use `playwright-cli` or `agent-browser` with domain allowlists. Keep Claude in Chrome for signed-in pages. Use DevTools MCP only with `--slim --no-usage-statistics`.
9. **Install the official `hookify` and `session-report` plugins.** hookify gives rules that can be expired, and session-report gives cost per agent and per skill.
   - Install (names checked against `anthropics/claude-plugins-official` `.claude-plugin/marketplace.json`; read both plugins before installing):
     ```
     claude plugin marketplace add anthropics/claude-plugins-official   # only if not already listed (repo slug: verify)
     claude plugin install hookify@claude-plugins-official --scope user
     claude plugin install session-report@claude-plugins-official --scope user
     ```
10. **Retro upgrades:** mechanical violations become a lint or a hook. Expiry outcomes are Keep, Update, Consolidate, Replace or Delete. Findings cite `path:line`.

## Avoid
- fast-jev-compaction: it sends your conversation to a third party.
- Installing superpowers, ECC, planning-with-files, spec-kit or VoltAgent wholesale. These add context bloat, and ECC auto-applies rules.
- basic-memory: AGPL plus a paid tier.
- The reference MCP memory server.
- browser-use or Stagehand as the main browser: they run a second LLM, and browser-use has telemetry on.
