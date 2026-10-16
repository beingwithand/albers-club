---
name: verify
description: Independently verify a piece of work against pre-agreed criteria before it is marked done. Use before declaring any non-trivial task complete.
context: fork
agent: verifier
---

# Verify

Verify the most recent deliverable described in `PROGRESS.md` (or the path given in $ARGUMENTS).

1. Load the acceptance criteria from `SPEC.md`, the task entry, or the matching `rubrics/<type>.yaml`. If none exist, **stop** and report that criteria are missing. Don't make them up.
2. Check each criterion with **evidence**: run the tests, open the output, compare against the source, and quote it with its location.
3. Judge only correctness and the stated requirements. Don't invent extra wishes.
4. Return:
   - **verdict:** pass, fail or needs-human
   - **per-criterion results**, each with a proof pointer
   - **for each failure:** the smallest fix that would satisfy it
5. Append a `verification` event to the log.
