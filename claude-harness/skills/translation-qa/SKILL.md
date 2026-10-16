---
name: translation-qa
description: Run deterministic CAT-style QA on a translation or a length-capped Korean rewrite. It checks numbers, dates and units, tags and placeholders, glossary and DNT terms (Korean particles tolerated), forbidden terms, double spaces and length limits, plus pofilter on XLIFF/PO/TMX when it is installed. Writes a JSON and a Markdown report and fails on blocking findings. Use it in the self-check of `translate` and `synopsis`, and whenever the `verifier` reviews a translation.
argument-hint: "<target file> [source file] [--direction ko-en|en-ko|ko-ko]"
---

# Translation QA (local, deterministic)

Inputs: $ARGUMENTS. You need the target, the source if there is one, and the direction. Use the project glossary at `knowledge/glossary.md` (format: `templates/glossary.md`) when it exists.

**Local only.** Client text never goes to an online spellchecker, translator or QA service: no Naver or Nara spellcheck, no k-skill `korean-spell-check`. See `docs/LOCAL_ONLY.md`.

## 1. Run the script
```
python3 -I ${CLAUDE_PLUGIN_ROOT}/scripts/translation_qa.py \
  --source src.txt --target tgt.txt [--by-line] --direction ko-en \
  --glossary knowledge/glossary.md [--forbid TERM ...] [--limit N --unit chars] \
  --json work/qa/<name>.qa.json --md work/qa/<name>.qa.md
```
- **Segments.** Use `--by-line` when source and target are aligned line by line. Use `--pairs file.tsv` (`id<TAB>source<TAB>target`) or a `.json` list for segment exports. Otherwise the whole file is checked as one segment.
- **Korean→Korean rewrites** (synopsis): give `--target draft.txt --direction ko-ko --limit N --unit chars`, plus `--forbid` for banned phrases from `style_notes.md`. Checks that need a source are skipped, and glossary checks become forbidden-term checks only.
- **CAT files** (`.xlf`/`.xliff`/`.po`/`.tmx`): add `--pofilter FILE`. This runs translate-toolkit's numbers, xmltags, variables, brackets, untranslated and doublespacing tests if `pofilter` is installed (`pipx install translate-toolkit`). If it isn't, the report says it was skipped.
- **Korean matching.** If `kiwipiepy` is installed (`pip install kiwipiepy`), glossary matching also compares morphemes. Without it, a particle-stripping rule still matches 계약서를, 계약서에서는 and 이해 관계자. The report says which method ran.
- **Severity.** `--warn CHECK` downgrades a check to a warning, for example `--warn numbers` when the client asked for converted dates or times. `--skip CHECK` turns a check off. Say in the report why you did either.

## 2. Read the report
Exit `0` means no blocking findings, `1` means at least one, and `2` means bad input. **Blocking** findings are:
- a missing or changed number
- a missing unit or currency category
- a tag, placeholder or URL that differs from the source
- a missing `approved` glossary term
- a DNT term that isn't byte-identical
- a forbidden term
- a length over the limit
- an empty target or misaligned lines
- any pofilter finding

**Warnings** are numbers that don't appear in the source, a missing `preferred` term, double spaces, and a length under the minimum.

## 3. Fix, re-run, report
- Fix every blocking finding, or explain to the user why it is a false positive. Common false positives: deliberate unit or date conversion, a compound word that contains the term, and a number written as a Korean native word (두 명).
- Re-run until the exit code is `0`, or until only findings the user has accepted remain.
- Show the user the Markdown summary line and the remaining findings. Keep the JSON next to the deliverable in `work/qa/` for the `verifier`.
- The script doesn't judge meaning, register or fluency. Those stay with the `translate` self-check, the back-translation and `verify`.
