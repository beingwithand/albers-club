---
name: retro
description: End-of-session retrospective. Summarize goal, dead ends, resolution, decisions, mishaps and lessons; propose rule/skill changes for user approval. Use at the end of any substantial session or when the user says /retro.
---

# Session retrospective

1. Write `log/sessions/<YYYY-MM-DD>_<topic>.md` with these sections:
   - Goal and intent
   - Paths tried and dead ends
   - Resolution
   - Decisions, each with its justification and proof
   - Mishaps
   - Lessons
   - What to reuse
   - What not to repeat
   - Pointers
2. Review every `Status: proposed` entry in `log/mishaps.md` and any corrections from this session. For each one, draft a **small itemized change** (one rule or one skill edit, never a rewrite) with:
   - the target file: global `CLAUDE.md`, a project `CLAUDE.md`, `.claude/rules/<topic>.md`, a skill, or a hook
   - the exact text to add
   - the justification, linked to the mishap or correction
   - scope: global if the same lesson appeared in 2 or more projects, otherwise the project
3. **Pattern seeds (L1→L2).** List what repeated in this session: requests or corrections made twice or more,
   a workflow run twice, a mistake that echoes an earlier one, and anything that worked again. Turn each into a
   candidate `Pattern` line (`status: candidate`, `origin: retro`, the `kind`, a one-sentence `statement`,
   `evidence` as event ids or `session-note:<this note's path>#<anchor>`, `areas`). Check
   `python3 -I ${CLAUDE_PLUGIN_ROOT}/scripts/patterns.py mine` first so you don't duplicate a known pattern;
   add evidence to the known pattern instead. After approval, append them with
   `patterns.py record --file <file>`.
4. Show the proposals as a numbered list. Apply **only** the ones the user approves, and commit each with its justification in the message.
5. Mark applied mishaps `approved` and rejected ones `rejected`, with the reason.
6. Append a `session_note` event to the log.
