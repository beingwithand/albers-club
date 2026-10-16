---
name: style-capture
description: Log a draft→final pair whenever the user edits (or approves) text Claude drafted, in any language or register, tagged with language, direction, register, domain, audience and the user's own reasoning. Use after translation, emails, chat replies, client deliverables or data-annotation responses.
---

# Style capture

Goal: every time the user edits text Claude wrote, keep the pair so later drafts start closer to how they write. One pair = one `StylePair` (`schema/ontology.yaml`) in `$HARNESS_DATA/style/pairs.jsonl`.

## When
- The user pastes back an edited version of a draft, or edits a file Claude wrote.
- The user approves a draft unchanged (log it too: `edited: false` pairs show what already works).
- Skip trivial fixes that carry no style signal (a typo in a name you misspelled is a correction, log it with `/mishap` or as a correction instead).

## Steps
1. **Collect the pair.**
   - `draft`: exactly what Claude produced.
   - `final`: exactly what the user kept or sent. Don't clean it up.
   - `source`: the source text if this was a translation.
   - If one long text has several unrelated changes, split it into one pair per paragraph or message so similarity search stays useful.
2. **Tag it.** Infer from context; confirm with the user only if unsure.
   - `language`: `ko`, `en` or `mixed` (language of the final text).
   - `direction`: `ko-en`, `en-ko` or `none` (not a translation).
   - `register`: one of the ontology `registers` (`formal-email`, `office`, `friendly`, `chat`, `client-deliverable`, `annotation-response`). See `docs/REGISTERS.md`.
   - `domain` (e.g. legal, tech, business, personal, general), `audience` (e.g. "new client, PM", "close friend", "annotation reviewer").
   - optional: `client`, `scope` (`global` or `<area>/<project>`), `labels` (e.g. `honorifics,concision`).
3. **Get the reasoning.** Use the user's own words if they gave any. Otherwise ask once, in one short line, naming the most notable change ("Why 'I wanted to check' instead of 'I am writing to ask'?"). If they skip it, leave `reasoning` empty. Never invent or paraphrase it into something they didn't say.
4. **Append it** (validation rejects unknown registers, directions or languages):
   ```
   python3 -I ${CLAUDE_PLUGIN_ROOT}/scripts/style_pairs.py add --json - <<'EOF'
   {"draft": "...", "final": "...", "source": "...", "language": "en", "direction": "ko-en",
    "register": "formal-email", "domain": "business", "audience": "new client",
    "reasoning": "...", "scope": "translation/<project>"}
   EOF
   ```
   Long texts can be passed as files: `--draft @draft.txt --final @final.txt`.
5. **Fixing a pair:** the file is append-only. Add a corrected pair with `"supersedes": "<old id>"`; the old one stops appearing in `nearest`.
6. Report the stored `id` in one line. If the reasoning states a general rule ("I never use '~하시길 바랍니다' with clients"), say it is a candidate for the `style-guide` skill; don't edit the guide here.

Privacy: pairs can contain client text. They live in `$HARNESS_DATA` (backed up privately), never in the plugin repo.
