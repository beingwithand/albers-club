---
name: style-guide
description: Distill the user's logged draft→final pairs into a personal, data-derived style guide per register, proposed as small itemized rules the user approves. Use in the weekly review, after about 20 new pairs in a register, or when the user asks "what's my style".
---

# Style guide

The guide at `$HARNESS_DATA/style/guide.md` is the user's style, learned from their edits and approved by them. It is never written from general advice.

## 1. Check there's enough data
```
python3 -I ${CLAUDE_PLUGIN_ROOT}/scripts/style_pairs.py stats
```
Work per register. A register needs at least about 5 edited pairs before you propose anything for it; say which registers are too thin and stop there for those.

## 2. Read the pairs for one register
Pull the pairs (`nearest --register <reg> -k 200`, or read `pairs.jsonl` filtered by register) and, for each `edited` pair, note what changed between draft and final:
- word choice and fixed phrases (openers, closers, thanks, apologies)
- sentence endings and honorific level (하십시오체 / 해요체 / 반말; formal vs contracted English)
- length and structure (sentence length, splitting or merging sentences, bullets)
- what the user deletes (hedges, filler, over-politeness) and adds (context, warmth, specifics)
- KO↔EN-specific moves (dropped subjects, rendering of 수고하세요-type set phrases, loanwords vs native terms)
Group by language and direction inside the register; a ko→en client email rule may not hold for en→ko.

## 3. Draft candidate rules
Each candidate must have:
- **Rule:** one imperative sentence, specific enough to check ("Close formal client emails with 'Best regards,' not 'Sincerely,'").
- **Register / language / direction** it applies to.
- **Evidence:** at least 2 pair ids, ideally 3+, with one short before→after quote. A rule from one pair is a hypothesis; label it so.
- **User's reasoning**, quoted from the pairs' `reasoning` field when present.
- **Counter-evidence:** pair ids where the user did the opposite, if any.
Merge with or refine an existing guide rule instead of creating a near-duplicate. Flag existing rules that new pairs contradict, and rules with no supporting pair in the last N weeks as candidates to expire.

## 4. Propose, don't write
Show the user a numbered list of small changes (add / edit / expire), ACE-style, never a full rewrite. The user approves, edits or rejects each item.

## 5. Write only the approved items
Update `guide.md`: one section per register, each rule with its evidence ids and the date approved. Keep a short `## Changelog` at the bottom (date, items added/edited/expired). Log a `decision` event for the approval (intent, situation, meta per `schema/event.md`).

## 6. Check it helps
Where an eval set exists for translation or writing, adopt guide changes only if style-match scores don't get worse. Otherwise, note the change as unverified and revisit at the next review.

Cross-register patterns the user repeats everywhere (e.g. "cut hedging") are candidates for `distill-principles`, not this guide.
