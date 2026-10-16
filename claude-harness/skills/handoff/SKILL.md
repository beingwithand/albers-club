---
name: handoff
description: Write HANDOFF.md so a cold reader (the next session after /clear, another machine, or another agent) can resume with zero conversation context, prove it with a cold-read test by a fresh subagent, then archive and log. Use when context reaches ~160–200K tokens or the usage guard says so, before /clear, at end of day, before switching tasks, or when the user says /handoff.
---

# Handoff

The goal is **resumability**: a reader who has only the files must pick up the exact next action, know what to verify first, and not repeat dead ends. Write what **cannot be recovered from the files, git or PROGRESS.md**, and point to everything else.

## When
- Context at **~160K** (heads-up) and no later than **~200K** (the usage guard injects a reminder at both).
- Before every `/clear`, at end of day, before switching to another task or project, and before handing work to another agent or machine.
- When 5-hour or 7-day usage is ≥90% and work may stop mid-task.
- If the user prefers compaction, use `compact-prep` instead (it calls this skill first).

## Steps

1. **Finish or park the current atomic step.** Don't hand off mid-edit. Either complete it, or revert to a clean state and record it under *Next actions*. Save files; update `PROGRESS.md` (Done with proof, In progress, Next).
2. **Gather facts, don't recall them.** Run and copy from the output:
   ```bash
   git rev-parse --abbrev-ref HEAD; git rev-parse --short HEAD; git status --porcelain; git log --oneline -5
   ```
   Also read `PROGRESS.md`, the newest `log/handoffs/auto_*.md` if one exists (pre-compaction snapshot), and this session's `decision`/`mishap` events in `$HARNESS_DATA/log/`.
3. **Archive the old note.** If `HANDOFF.md` exists, move it to `log/handoffs/<YYYYMMDD_HHMMSS>.md` (UTC).
4. **Write `HANDOFF.md`** in the project root using the template below.
5. **Cold-read test** (mandatory, below). Revise until it passes.
6. **Log** a `handoff` event (see `schema/event.md`) with `intent`, `situation`, `meta`, `pointers: ["HANDOFF.md", ...]`, and `cold_read: {"score": "6/6", "rounds": N, "model": "haiku"}`.
7. **Tell the user:** "Handoff written and cold-read tested (6/6). Run `/clear`, then say *read HANDOFF.md and continue*." (After `/clear`, the SessionStart hook also re-injects it.)

## Template (exact headings, in this order)

```markdown
# HANDOFF: <project> — <one-line task>
git_commit: <short sha>   branch: <branch>   written: <YYYY-MM-DD HH:MM TZ>   by: <model/session>
Uncommitted: <none | list from git status --porcelain>

## 1. Goal and intent
What we are trying to achieve and **why** (the user's underlying need), plus the definition of done.

## 2. State (each line has proof)
- DONE: <item> — proof: <test command + result / file:line / commit sha / verification event id>
- IN PROGRESS: <item> — where it stands, exact file(s) touched
- NOT STARTED: <item>

## 3. Decisions (with why)
- <decision> — why: <specific reason>; rejected: <alternative + reason>; proof: <pointer>; event: <evt_id if logged>

## 4. Dead ends (do not retry)
- <what was tried> — failed because <exact reason / error message> — evidence: <pointer>

## 5. Open questions
- <question> — who answers (user / research / test), and what changes depending on the answer

## 6. Next 3 actions (exact)
1. <action> — `<exact command or file:function>` — expected result: <what success looks like>
2. ...
3. ...

## 7. Verify first (before trusting this note)
- `git rev-parse --short HEAD` == git_commit above (if not, re-check sections 2 and 6)
- <the 1–3 claims most likely to be stale, with the command that checks each>

## 8. Risks and gotchas
- <what could break, irreversible actions pending user OK, deadlines, rate-limit state>

## 9. Pointers
PROGRESS.md · decisions.md · knowledge/<pages> · log/sessions/<note> · log/handoffs/auto_<ts>.md · open mishaps · artifacts produced · user corrections this session (quote them)
```

## Write for a cold reader
- **No conversation references.** Never "as discussed", "the bug above", "option B", "that file". Name the thing: path, function, sha, exact error text.
- **Absolute specifics.** Paths from the project root, commands that run as pasted, numbers with units, dates with timezone.
- **Proof or "unverified".** Every DONE has a pointer; a claim without one is labeled `unverified`.
- **Quote, don't paraphrase,** user corrections and error messages.
- **Why beats what.** The code shows what; the note must carry the reasons and rejected alternatives.
- **Link, don't copy.** ≤150 lines. Long logs, diffs and research go in files; the note points at them.
- **Next actions are executable** by someone who never saw the chat: imperative verb, exact command, expected result.

## Cold-read test (mandatory)

Spawn a **fresh subagent with `model: haiku`** and no tools except `Read`, given **only** the path to `HANDOFF.md` (not the conversation, not a summary). Prompt it:

> You are resuming this project cold. Read only `<abs path>/HANDOFF.md`. Answer in 6 numbered lines, quoting the note where possible; write "MISSING" if the note doesn't say:
> 1. What is the goal, and why does it matter?
> 2. What exactly is the next action (command or file)?
> 3. What must be verified first, and how?
> 4. What are the key decisions and the reason for each?
> 5. Which dead ends must be avoided, and why did they fail?
> 6. Where does the proof for the completed work live?

Grade each answer against your own knowledge of the session: **correct**, **wrong**, or **missing**. Pass = 6/6 correct.
- On any wrong/missing answer, fix the section that caused it (the cause is the note, not the reader) and re-test with a **new** subagent. At most **2 revision rounds**.
- If still failing after 2 rounds, keep the best version, add a `## Known gaps` section listing the failed questions, and tell the user.
- Record the score and rounds in the `handoff` event. Rubric: `rubrics/handoff.yaml`.

## Related
- `compact-prep`: when compacting instead of clearing.
- Hooks: `precompact_snapshot.py` writes raw auto snapshots to `log/handoffs/auto_*.md`; `postcompact_reinject.py` re-injects HANDOFF.md after `/compact` or `/clear`; `usage_guard.py` tells you when to hand off.
