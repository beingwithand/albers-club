---
name: web-research
description: Scoped, cited, state-of-the-art web research with automatic fan-out. Interviews for depth, sources and standards first. Use for any "what's the state of the art / find out / compare" request.
argument-hint: "<question>"
---

# Web research

Question: $ARGUMENTS

## 1. Scope interview
Skip any question already answered, or one that the stored preferences answer.
- **Goal:** what decision this research feeds into.
- **Depth** (sets the fan-out tier, `docs/FANOUT.md` §3):
  - **quick: tier 0, inline, no subagents.** At most about 3 sources of one type, 3–10 tool calls. Use tier 1 (one `web-researcher`) only if the pages are long enough to flood the context (more than about 1k irrelevant tokens).
  - **standard: tier 2, 2–4 agents in parallel.** Escalate to it automatically when the search needs **more than about 3 sources OR mixes source types** (papers, GitHub, Reddit/HN, press). Use one agent per source tier or per option compared, 10–15 calls each.
  - **exhaustive: tier 3, 5–10 agents per batch,** split by source tier and sub-question. **Cap: 10 per batch.** For a truly exhaustive survey, route to the built-in **`/deep-research`** workflow when it's available (it votes on claims, drops refuted ones and marks the rest unverified). Keep this scope interview and pass its answers in. If 7-day usage is above 75%, ask the user before starting (`fanout-plan` handles it).
- **Recency window:** the default is "as of today". Get the real date with `date`.
- **Source tiers to include or exclude:**
  1. Primary sources: arXiv, Google Research / DeepMind, MIT, Stanford, other labs, official docs.
  2. GitHub: rank repos by stars, recent commits, releases and issue health. Stars alone are inflated.
  3. Practitioners: Reddit, Hacker News, YouTube transcripts.
  4. Press and vendor blogs: lowest weight, flagged as possibly biased.
- **Output:** a short answer, a report, or a comparison table.

## 2. Fan-out
Run `fanout-plan` first. It applies the usage budget: at ≥ 70% widths are halved and workers are sonnet/haiku only, and at ≥ 90% research runs inline only. It writes the plan (N agents × calls, estimated tokens) to `PROGRESS.md`. Then spawn `web-researcher` subagents in one parallel batch, one per sub-question or source tier, all on the same model and tools. Give each:
- the objective
- the date window
- the source tiers to use, and the **boundaries** (what the sibling agents cover)
- a **call budget**: 10–15 calls for comparison and standard research, at most 15 for exhaustive
- the output format
- a notes file path
- the return: ≤ 300 words plus the notes path

For "find everything" requests, run another round only for gaps, and stop after **2 rounds with nothing new**. A worker that fails or comes back empty is listed as **not covered**.

## 3. Standards for every claim
- citation URL, publication date, and confidence (high, medium or low)
- conflicts between sources shown, not resolved silently
- anything older than about 6 months on fast-moving topics flagged
- sources that couldn't be reached listed, and asked for (links or pasted text), never guessed

## 4. Synthesis and logging
- Merge the notes, **dedupe** claims before checking them, list the gaps and uncovered workers, and save the result to `research/<date>_<topic>.md`.
- Key claims a decision depends on, when they're uncertain and high-stakes, get 3 refuters (`verify`, tier V). A majority kills a claim.
- Log a `task` event with the intent, the scope answers, and `fanout_tier`, `fanout_n` and `est_tokens`. The scope answers are also stored as preferences for next time.
