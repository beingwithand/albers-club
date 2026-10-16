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
- **Depth:**
  - quick: 1 agent, about 5 sources
  - standard: 3 agents
  - exhaustive: 5 or more agents, split by source tier
- **Recency window:** the default is "as of today". Get the real date with `date`.
- **Source tiers to include or exclude:**
  1. Primary sources: arXiv, Google Research / DeepMind, MIT, Stanford, other labs, official docs.
  2. GitHub: rank repos by stars, recent commits, releases and issue health. Stars alone are inflated.
  3. Practitioners: Reddit, Hacker News, YouTube transcripts.
  4. Press and vendor blogs: lowest weight, flagged as possibly biased.
- **Output:** a short answer, a report, or a comparison table.

## 2. Fan-out
Spawn `web-researcher` subagents, one per sub-question or source tier. Give each:
- the objective
- the date window
- the source tiers to use
- the output format
- a notes file path

## 3. Standards for every claim
- citation URL, publication date, and confidence (high, medium or low)
- conflicts between sources shown, not resolved silently
- anything older than about 6 months on fast-moving topics flagged
- sources that couldn't be reached listed, and asked for (links or pasted text), never guessed

## 4. Synthesis and logging
- Merge the notes, list the gaps, and save the result to `research/<date>_<topic>.md`.
- Log a `task` event with the intent and the scope answers. The scope answers are also stored as preferences for next time.
