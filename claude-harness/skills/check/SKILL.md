---
name: check
description: Default for any factual, technical, product, pricing, legal or "what's current" question. Check online instead of answering from memory, verify against independent sources, and log the result to the research ledger so it can be pointed to later. Use even for quick questions unless the fact is trivial and stable.
argument-hint: "<question>"
---

# Check online, verify, log

Question: $ARGUMENTS

## 1. Decide the depth (`docs/FANOUT.md`)
- **Quick (tier 0, inline):** 1–3 searches, fetch the best 2–3 sources.
- More than about 3 sources needed, or mixed source types (papers, GitHub, forums, press): hand off to `/web-research` (tier 2+).
- Skip the online check only when the fact is trivial and stable (arithmetic, well-known definitions). If you skip it, say so ("from memory, not checked").
- First look in `$HARNESS_DATA/research/ledger.jsonl` for an earlier note on the same question. If it's recent and confident, reuse it and cite it. If it's stale (past `review_by`), re-check.

## 2. Gather
- Use the real current date (`date`), and prefer the newest primary sources: official docs, the vendor's own pages, papers, repos.
- Record the URL, publication date and a short quote for each claim.

## 3. Verify (always)
- Every key claim needs **2 independent sources**, or 1 primary or official source. Otherwise mark it `unverified`.
- If sources conflict, show the conflict. Never pick one silently.
- If a source couldn't be reached, say so and ask for a link or pasted text.
- For anything sent to clients or employers, or a high-stakes decision, add tier-V verification (`verify`).

## 4. Answer
- Lead with the answer, then the caveats. Give a confidence level (high, medium or low) per key claim. End with **Sources:** as linked URLs with dates.

## 5. Log (always)
Append one `ResearchNote` to `$HARNESS_DATA/research/ledger.jsonl`. The schema is in `schema/ontology.yaml`. Fields:
- `question` and `intent`
- `answer`: 1–3 sentences
- `claims`: each with its confidence
- `sources`: URL, date and quote
- `verification`: the method, plus what's verified and what isn't
- `confidence`
- `review_by`: 3 months out for fast-moving topics, otherwise 12
- `tags`
- `notes_path` if longer notes exist

Also append a `task` event that points to the note ID, so later sessions can cite it ("see rn_…").
