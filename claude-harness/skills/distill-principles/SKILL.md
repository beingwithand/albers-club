---
name: distill-principles
description: Decompose what the user says, decides and corrects into short, reusable principles that apply across domains (code, translation, annotation, design, research). Use in /retro, the weekly review, or when the user explains how they think.
---

# Distill principles

1. Read the source material: the session transcript, corrections, decision records, or the user's explanation.
   Also read the **pattern layers**: approved and encoded L2 patterns and their L3 encodings
   (`python3 -I ${CLAUDE_PLUGIN_ROOT}/scripts/patterns.py report`), plus `propose-principle` and
   `review-principle` items from `patterns.py ladder`. A principle needs 2 or more L2/L3 items from 2 or more
   areas.
2. Extract candidate principles. Each one must have:
   - **Statement:** at most one sentence, imperative, and independent of any domain where possible.
   - **Intent:** the underlying value it serves.
   - **Evidence:** quotes or event IDs where the user expressed it, ideally from two or more occasions, plus the
     pattern ids it generalizes. Put `(patterns: pat_…)` in the source note so `patterns.py` can link L4 to L2.
   - **Applies to:** global, or the specific areas it covers.
   - **Example:** one concrete application, and if possible one in a different domain (e.g. code → design).
3. Merge it with an existing principle in `global/PRINCIPLES.md` if it overlaps. Don't create near-duplicates.
4. Propose the additions or edits to the user as a numbered list. Write only the approved ones. Then record
   each linked pattern again with `principles: [P<n>]` (`patterns.py record`).

Principles are about **how the user thinks**. Project facts go in project files, not here.
