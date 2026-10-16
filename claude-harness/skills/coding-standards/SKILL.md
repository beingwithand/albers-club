---
name: coding-standards
description: The shared coding rules for writing and reviewing code (surgical diffs, read-before-edit, no drive-by changes, no test edits to pass, proof per step) plus the review checklist. Use whenever code is written, fixed, or reviewed. Preloaded by the coder and code-reviewer agents.
user-invocable: false
---

# Coding standards (shared by `coder` and `code-reviewer`)

One rulebook for both sides: the coder writes to it and the reviewer reviews against it, and **nothing else**. A reviewer finding that isn't backed by a rule here, the spec, or a failing check is a nitpick; leave it out.

## 1. Surgical changes (global rule)
- **Smallest change that satisfies the spec.** Before editing, state in one line which acceptance criterion the change serves. Code that serves no criterion is not written.
- **Size budget (heuristic).** A diff over **~50 changed lines** or touching **more than 3 files** needs a one-line justification in the hand-off ("why this can't be smaller"). Generated files, lockfiles and new test cases don't count toward the budget, but say they're there.
- **No unrelated changes.** No drive-by refactors, renames, reformatting, import reordering, comment rewrites, or "while I'm here" fixes. Found something else broken? Note it under "out of scope, seen" in the hand-off and leave it.
- **Root cause, not symptom.** A fix targets why it broke. Don't silence the error, widen a `try/except`, add a special case for the failing input, or bump a timeout without showing that it is the cause. Every fix carries a root-cause note: `Root cause: <file:line> <what was wrong and why>`.
- **Preserve behavior you weren't asked to change** (backwards compatibility): public function signatures, CLI flags, file formats, config keys, exit codes and log/event fields stay as they were. If the spec needs a breaking change, say so explicitly and give the migration.

## 2. Read before edit
- Read the whole function or block you change, its callers (`Grep` the symbol), and the nearest test for it before the first edit.
- Read the repo's `CLAUDE.md`, `SPEC.md`, `PROGRESS.md` and any `.claude/rules/` that match the path.
- Never edit a file you haven't read in this session. Never edit from memory of an earlier version.

## 3. Match local idioms
- Follow the file's existing style: naming, error handling, logging, string quoting, type hints, line length, and **comment density** (a sparsely commented file gets no essay comments; a heavily documented one gets a docstring).
- Reuse the helpers the repo already has (`Grep` before writing a new one). Don't introduce a second way to do the same thing.
- Comments explain *why*, never *what changed* ("fixed bug" belongs in the commit message, not the code).

## 4. Dependencies
- **No new dependency without justification:** what it does that the stdlib or an existing dependency can't, its license, maintenance status, and size. Prefer the stdlib. Pin versions the way the repo already does. Adding one counts as non-surgical (§7).

## 5. Tests, evals and rubrics are the oracle (reward-hacking guard)
- **Never edit, delete, skip, `xfail` or loosen** a test, eval case, rubric, snapshot or fixture to make it pass. Never special-case test inputs in product code. If a test looks wrong, stop and report it with the evidence; the user decides.
- **Adding** a new test for new behavior is expected (whoever writes the feature writes its tests). A bug fix gets a regression test that fails without the fix, when the repo has a test suite.
- `evals/` and `rubrics/` are off-limits to agents entirely (enforced by deny rules and `hooks/guard_protected.py`).

## 6. Proof for every step
- After each change run the **fastest relevant checks** first (the touched test file, the linter or type checker on the touched files), then the broader suite before hand-off. Quote the command and the decisive output lines (pass counts, the error). "Should work" is not proof.
- The `step_check` hook gives a free syntax check after each edit (`docs/VERIFICATION.md`). It is a floor, not proof that the change is correct.
- A change whose checks you couldn't run is marked **unverified**, with the reason.

## 7. Commits
- One verified unit of work per commit, only when asked. The message says **why** (the criterion or bug), not just what. Never `--no-verify`, never amend or force-push shared history.

## 8. Security basics
- No secrets, tokens or credentials in code, tests, logs, fixtures or commit messages; read them from env vars or the password manager.
- Validate input at trust boundaries (CLI args, files, HTTP, user text, LLM output): types, ranges, path traversal, size caps.
- No `shell=True` / string-built shell commands with outside input; no `eval`/`exec` on data; parameterized SQL only; safe YAML loaders.
- Fail closed on auth and permission checks. Don't log personal data you don't need.

## 9. When a change is not surgical
Any of these means stop and hand back (coder → orchestrator/user; reviewer → coder or user): a new dependency, a breaking interface change, a schema or data-format change, a change to more than one module's design, a security-sensitive change, or a fix that exceeds the size budget without a good justification.

## 10. Review checklist (the reviewer applies exactly this; the coder self-checks with it before hand-off)
Every finding cites `file:line`, names the rule (§n) or criterion it breaks, and names the concrete risk.

1. **Correctness vs spec:** does the diff satisfy each stated acceptance criterion? Edge cases the spec implies (empty, None, unicode/Korean text, large input, error paths)? Off-by-one, wrong comparison, swapped args?
2. **Surgical (§1):** anything unrelated in the diff? Within the size budget or justified? Root-cause note present and plausible?
3. **Read-before-edit / idioms (§2–3):** does it match the surrounding code and reuse existing helpers?
4. **Tests (§5–6):** were checks run, with output quoted? Is there a regression test for a bug fix? Were any tests, evals, rubrics or fixtures weakened? (Any weakening = `changes-requested`, or `needs-human` if intentional.)
5. **Compatibility (§1):** signatures, flags, formats, event fields unchanged unless the spec says otherwise?
6. **Security (§8):** secrets, unvalidated input, injection, unsafe deserialization.
7. **Dependencies (§4):** any new one, and is it justified?
8. **Consistency with recorded decisions:** `decisions.md`, `SPEC.md`, `.claude/rules/`, and earlier review rulings.

Out of scope for review: personal style preferences, alternative designs that also meet the spec, and improvements nobody asked for. Mention at most one such item, labeled "optional", or none.
