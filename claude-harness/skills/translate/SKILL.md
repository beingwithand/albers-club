---
name: translate
description: Translate between Korean and English in the user's own style and register (formal email, office, friendly, chat, client deliverable, annotation response). Use for any KO↔EN translation or bilingual rewrite. Loads the glossary and the user's nearest past draft→final pairs, self-checks, then verifies and captures the user's final edit.
---

# Translate (KO↔EN)

## 1. Frame the job (ask once, only for what is unclear)
Settle four things before writing. Reuse answers from the project `CLAUDE.md`, `SPEC.md` or earlier turns; ask the user **one** combined question only for what's still missing.
- **Direction:** ko→en or en→ko.
- **Register:** one of `formal-email`, `office`, `friendly`, `chat`, `client-deliverable`, `annotation-response` (see `docs/REGISTERS.md`).
- **Domain:** e.g. legal, business, tech, medical, marketing, general.
- **Audience:** who reads it, and their relationship to the user (client, manager, friend, reviewer).
Also note any client, length limit, or formatting constraint (CAT tool tags, tables, character caps).

## 2. Load references
1. Glossary: `knowledge/glossary.md` in the project (format: `templates/glossary.md`). Note every **DNT** (do-not-translate) term and every client-mandated target term.
2. Nearest style pairs (3–5):
   ```
   python3 -I ${CLAUDE_PLUGIN_ROOT}/scripts/style_pairs.py nearest \
     --register <reg> --direction <ko-en|en-ko> --domain <domain> --text @<source-file> -k 5
   ```
   Read each pair's `draft`→`final` diff and `reasoning`. Copy the **pattern** of the user's changes (word choice, sentence endings, honorific level, sentence length), not the content.
3. If `$HARNESS_DATA/style/guide.md` has an approved section for this register, follow it. Approved guide rules win over a single pair.

## 3. Translate
- Translate meaning and intent, then fit the register. Keep the source's structure unless the register calls for change (e.g. Korean chat → English chat can drop subjects; English formal → Korean 하십시오체 may need restructured sentences).
- Keep placeholders, tags, URLs, code and DNT terms byte-identical.
- Where you made a judgment call (ambiguous source, cultural adaptation, untranslatable pun), mark it inline as `[TN: ...]` for the user, never silently.

## 4. Self-check (before showing the user)
Go segment by segment and fix anything that fails:
- [ ] **Terminology:** every glossary term used as specified; DNT terms untouched; same source term → same target term throughout.
- [ ] **Numbers, dates, names, units, currency:** each matches the source. Convert date order or units only if the register/client asks (e.g. 2026년 10월 16일 ↔ October 16, 2026). Romanized names follow the glossary or the person's own spelling.
- [ ] **Omissions and additions:** every source sentence has a counterpart; nothing added that the source doesn't support. Count sentences or bullets on both sides.
- [ ] **Register:** honorific level and sentence endings are consistent (no 해요체 slipping into a 하십시오체 email; no stiff "Dear Sir" in chat).
- [ ] **Format:** line breaks, lists, tags and length limits preserved.

## 5. Back-translation spot check (risky segments only)
Pick the segments most likely to be wrong: negations, conditionals, legal/financial obligations, numbers in prose, idioms, and anything with a `[TN]`. Back-translate each one literally into the source language **without looking at the source**, then compare. If meaning drifted, revise and note what changed. Report which segments you checked.

## 6. Verify
Run the `verify` skill against the translation rubric (`rubrics/translation.yaml` if present) or the criteria agreed in step 1. Present the result with the verdict, the `[TN]` notes, and the back-translation findings. Don't call it done before verification passes or the user accepts a `needs-human` verdict.

## 7. Capture the user's final edit
When the user returns their edited version (or approves yours unchanged), run the `style-capture` skill with:
- `draft` = your output, `final` = the user's version, `source` = the source text;
- direction, register, domain and audience from step 1;
- `reasoning` = why the user changed it, in their words. Ask once, briefly, if they didn't say ("Any reason worth remembering for 표현 X → Y?"). Don't invent reasons.
If the edit reveals a glossary term, propose adding it to `knowledge/glossary.md` and add it only after the user approves.
