---
name: handoff
description: Write a handoff note so the next session (after /clear, on another machine, or for another agent) can resume without the conversation. Use at natural stopping points, before /clear, or when context is getting long.
---

# Handoff

Write `HANDOFF.md` in the project root, overwriting any previous one after first moving it to `log/handoffs/<timestamp>.md`. Focus on what **cannot be figured out from the files or code**.

## Sections
1. **Goal and intent:** what we're trying to achieve, and why.
2. **Current state:** done, in progress, next. Link each item to a file or commit.
3. **Decisions made this session:** the claim, specific reasons, alternatives rejected, and a proof pointer.
4. **Dead ends:** what was tried and why it failed, so it isn't retried.
5. **Open mishaps / lessons:** anything not yet turned into a rule.
6. **Verify first:** what the next session must check before trusting this note.
7. **Pointers:** `PROGRESS.md`, relevant `knowledge/` pages, session notes, commits. Also record the current `git_commit` (`git rev-parse --short HEAD`) and branch at the top, so a stale handoff can be detected: if HEAD has moved since, re-verify before trusting the note.

## Then
- Append a `handoff` event to the log (see `schema/event.md`), with intent, situation and meta filled in.
- Tell the user: "Handoff written. Run `/clear`, then say *read HANDOFF.md and continue*."

Keep it under ~150 lines. If something is long, link to it instead of copying it in.
