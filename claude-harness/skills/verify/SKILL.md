---
name: verify
description: Independently verify a piece of work against pre-agreed criteria before it is marked done. Use before declaring any non-trivial task complete.
context: fork
agent: verifier
---

# Verify

Verify the most recent deliverable described in `PROGRESS.md` (or the path given in $ARGUMENTS). If $ARGUMENTS names a `--lens <fidelity|rules|language|format>`, check only that lens's criteria.

## How many verifiers (`docs/FANOUT.md` §4)
- **Default: 1 verifier,** this fork, for internal work.
- **MANDATORY verification fan-out (tier V)** for anything sent to **clients or employers**: deliverables, synopses, client translations, job applications and cover letters, invoices, client emails. The *caller* (the main thread or orchestrator; this fork can't spawn agents) runs it like this:
  1. **Executable checks first** (`textlen.py`, `translation_qa.py`, `claim_check.py`, `invoice.py --dry-run`, tests). Save their output as proof.
  2. Spawn **2–3 independent `verifier` agents in parallel,** one per lens: **fidelity** (source and facts), **rules/requirements** (rubric, R-rules, posting, limits), **language/style** (register, spelling, tone). Give each a brief with this skill, its `--lens` and the paths. Use the same model for every sibling. That model must be **at least as capable as the producer,** preferably a different one (e.g. sonnet producer → opus verifiers).
  3. **Aggregate:** pass only if every lens passes. A **split verdict** (verifiers disagree, or any `needs-human`) **goes to the user** with both sides' proof.
  4. **Usage:** at ≥ 70% use 2 lenses on sonnet. At ≥ 90% it **still runs at width 2 on sonnet/haiku.** Say so, and mark the verdict "reduced strength" if the producer was opus or fable.
- **High-stakes uncertain claims** (legal, financial, irreversible, or a fact the deliverable rests on) get **3 refuters** per claim. A majority kills the claim, and "uncertain" counts as refuted. Show the user any 2–1 split.
- Fix loops: at most 2 retries, then escalate to the user.

## Steps (each verifier)

1. Load the acceptance criteria from `SPEC.md`, the task entry, or the matching `rubrics/<type>.yaml`. If none exist, **stop** and report that criteria are missing. Don't make them up.
2. Check each criterion with **evidence**: run the tests, open the output, compare against the source, and quote it with its location.
3. Judge only correctness and the stated requirements. Don't invent extra wishes.
4. Return:
   - **verdict:** pass, fail or needs-human
   - **per-criterion results**, each with a proof pointer
   - **for each failure:** the smallest fix that would satisfy it
5. Append a `verification` event to the log, with `verdict`, `scope_hint` (the project cwd) and `items` (the PROGRESS/tasks entries checked). The Stop-hook gate (`hooks/verify_gate.py`) matches on these. In tier V, each lens logs its own event (name the lens in `content`), and the caller logs the aggregate with `fanout_tier: V` and `fanout_n`.
