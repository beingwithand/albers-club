---
name: synopsis
description: Condense a Korean synopsis to a length limit (e.g. ~150 → 110) for streaming-metadata work (Toin / Netflix-style), KO→KO. Uses the LRT title, sibling-episode synopses or genre exemplars, and press coverage for context; applies every reviewer rule; writes 3 distinct drafts for the user to edit and combine. Use for any synopsis/logline rewrite with a length cap.
argument-hint: "<source synopsis file> [limit] [unit]"
---

# Synopsis condense (KO→KO, length-capped)

Inputs: $ARGUMENTS. Expect a source synopsis, the **limit and unit** (characters with spaces by default; confirm once per project if unclear), and the **LRT title** as given by the platform.

**Confidentiality:** treat the source synopsis and any unreleased details as confidential. Never paste them into web searches or third-party tools. Search only with the public title, cast and network.

## 1. Load the rules (they always win)
- `knowledge/reviewer_rules.md`: one rule per line, with an ID (`R-001`…), its source (which feedback, and when) and a check method. Every rule applies to every draft.
- `knowledge/style_notes.md`: the client/platform style guide notes (tense, spoiler policy, how names and titles are written, banned phrases).
- If either file is missing, ask the user for the guide or feedback before drafting. Don't guess client rules.

## 2. Gather context (in this order, and note what each source gave you)
1. **The LRT title:** use it exactly as provided, character for character.
2. **Sibling synopses:** past episodes of the same show (in `knowledge/<show>/`). Copy their naming of characters, recurring phrasing, sentence rhythm, and how much plot they reveal.
3. **If there are no siblings:** use genre exemplars. Pull 3–5 approved synopses of the same genre from past projects (`style_pairs.py nearest --domain synopsis-<genre>`) and mimic their tone.
4. **Press context:** search the official site first, then Google News and press releases, using the public title only. Record each useful fact with its URL and date in `knowledge/<show>/press.md`. Use press **only** to confirm names, roles and premise wording. Never add plot that isn't in the source.

## 3. Write 3 drafts, each with a different strategy
- **A, faithful compression:** keep the source's structure and cut the least important clauses.
- **B, hook-first:** lead with the premise or conflict, in the style of the siblings or genre.
- **C, character-led:** frame the episode through its protagonist's situation.

Each draft must:
- fit the limit (aim for 95–100% of it unless the rules say otherwise)
- keep names consistent with the siblings and the LRT title
- add no facts and no spoilers beyond the source

## 4. Self-check every draft (show the table to the user)
For each draft, report:
- the length: `python3 -I ${CLAUDE_PLUGIN_ROOT}/scripts/textlen.py --limit <N> --unit <unit> draftA.txt draftB.txt draftC.txt`
- pass or fail for every reviewer rule, by its R-ID
- the LRT title and names checked against the siblings
- facts checked against the source (list anything it can't trace)
- spelling and spacing (맞춤법/띄어쓰기)

Then run `verify` with `rubrics/synopsis.yaml`.

## 5. The user edits and combines
- Present the 3 drafts and the check table. The user edits and merges them.
- Re-check the final version: its length and every R-rule.
- Log each draft→final pair with `style-capture`: `language=ko`, `direction=none`, `register=client-deliverable`, `domain=synopsis-<genre>`, `client=toin`, and the user's reasoning.

## 6. Reviewer feedback becomes rules
When a reviewer sends feedback:
1. Log it as a `correction` event, with intent and situation filled in.
2. Turn each point into a numbered rule in `reviewer_rules.md`: the rule, a quote from the feedback, the date, and a check method. Add a **check method that can be verified**: a script check where possible, otherwise a review question.
3. Re-check recent deliverables against the new rule and tell the user about any that would now fail.
4. If a rule repeats across shows, propose promoting it to the client-wide level (via `retro`).
