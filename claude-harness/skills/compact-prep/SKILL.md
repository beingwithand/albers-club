---
name: compact-prep
description: Prepare a safe /compact - refresh HANDOFF.md first, then produce one precise `/compact <instructions>` string listing exactly what to keep verbatim and what to drop. Use when the user prefers compacting over handoff + /clear, when the thread holds decisions that would be costly to re-explain, or when the usage guard flags context at 160-200K and the user says "compact".
---

# Compact prep

Compaction summarizes the thread; whatever the summary drops is gone. Files survive, so **write state to disk first**, then tell the compactor exactly what to keep. Claude can't run `/compact` itself: you produce the command, the user runs it.

## Steps

1. **Refresh `HANDOFF.md`** by following the `handoff` skill (template + cold-read test). If it was written in the last 20 minutes and nothing changed since, skip the rewrite but re-check `git rev-parse --short HEAD` against its `git_commit`. This is the safety net if the summary is poor.
2. **Collect the keep-list from the session and the files** (not from memory alone):
   - **Decisions** made this session, each with its one-line *why* (and `evt_` id if logged).
   - **User corrections and preferences, verbatim**, in quotes.
   - **Exact file paths** touched or about to be touched, plus branch and short HEAD.
   - **Errors and failing tests, verbatim** (the exact message line, the failing test name, the command that reproduces it).
   - **Current step**: what's mid-flight, and the next 3 actions with commands.
   - **Constraints**: deadlines, "don't touch" paths, pending user approvals.
3. **Collect the drop-list:** exploratory searches and listings, full file dumps already on disk, superseded plans and drafts, verbose tool output, resolved tangents. Dead ends are reduced to one line each (what + why it failed).
4. **Emit the command** as a single fenced block the user can paste. Keep it under ~1,500 characters; put detail in HANDOFF.md, not in the command:

   ```text
   /compact Keep verbatim: (1) decisions+why: <d1 — why>; <d2 — why>. (2) user corrections: "<quote>"; "<quote>". (3) files: <path>, <path>; branch <b> @ <sha>. (4) errors/tests: `<exact error>` from `<cmd>`; failing: <test>. (5) current step: <step>; next: <a1>; <a2>; <a3>. Dead ends (one line each): <x — why>. Drop: exploratory output, file dumps, superseded plans, resolved tangents. End the summary with: read HANDOFF.md (written <time>, <sha>) before continuing.
   ```
5. **Tell the user:** "HANDOFF.md refreshed (cold-read 6/6). Paste the `/compact …` line above. After compaction, the SessionStart hook re-injects HANDOFF.md and PROGRESS 'Next'; the PreCompact hook saves a raw snapshot to `log/handoffs/auto_<ts>.md`."
6. **After compaction** (next turn): read HANDOFF.md and run its *Verify first* list before acting. If the summary contradicts the files, the files win; note the loss as a `mishap` if it mattered.

## Rules
- Never omit a user correction or a decision's reason to save space; cut exploration instead.
- Quote errors exactly, including codes and paths; never "the test failed".
- Use paths, shas and names, never "that file" or "the earlier approach".
- If the conversation is already past ~250K, or the next task is unrelated, recommend `/handoff` + `/clear` instead: it's faster and loses less.
- Background: `global/CLAUDE.md` has a standing `# Compact instructions` section; your string adds the session-specific keep-list on top. Auto-compaction is set to 250K (`autoCompactWindow`).
