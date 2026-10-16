# Harness self-test eval set

This area tests the harness's own scripts and hooks. Every task is deterministic: it writes small
fixture files into a fresh temp directory, runs a script or hook with a clean environment, and checks
the exit codes, stdout/JSON and files that come back. No model, no network and no user data are
involved, so the whole set runs on Linux in a few seconds and gives the same result every time.

It is the gate for the harness itself. Any change to `scripts/`, `hooks/` or `skills/` must leave this
set no worse, judged by `scripts/eval_gate.py` (evals/README.md, "The gate"). Each task lists the files
it covers in `components: [...]`. The component graph (`scripts/harness_index.py`) reads that list, so
`python3 -I scripts/harness_index.py --affected <changed files>` names `harness` among the areas to
re-run (eval-on-change).

## Run it

From the harness root:

```bash
python3 -I scripts/run_evals.py --area harness                     # all 20 tasks
python3 -I scripts/run_evals.py --area harness --split train       # train only (what an optimizer may see)
python3 -I scripts/run_evals.py --area harness --task harness-010  # one task (repeatable)
python3 -I scripts/run_evals.py --area harness --keep              # keep the temp dirs to inspect a failure
```

The result is an EvalRun JSON in exactly the format `eval_gate.py` reads. By default it is written to
`$HARNESS_DATA/evals/results/harness/<UTC timestamp>.json`; use `--out FILE`, or `--out -` for stdout.
Progress and failures go to stderr. The exit code is 0 when every task passed, 1 when any task failed
(or the gate rejected), and 2 for a usage, task-file or lock error.

### Gating a change

```bash
# before the change
python3 -I scripts/run_evals.py --area harness --out /tmp/base.json
# after the change: runs the set again, then eval_gate.py against the baseline
python3 -I scripts/run_evals.py --area harness --out /tmp/cand.json --baseline /tmp/base.json
# the same check, by hand
python3 -I scripts/eval_gate.py /tmp/base.json /tmp/cand.json --tolerance time=50%
```

`--baseline` passes `--tolerance time=50%` by default, because subprocess wall-clock time varies by
machine load. Correctness has no tolerance. Override the tolerance with `--tolerance DIM=VALUE`
(repeatable). Paste the gate report into the commit or PR that adopts the change.

### What a result contains

- `eval_set`: `harness`, or `harness/train` / `harness/holdout` with `--split`, plus `[ids]` with
  `--task`. Runs on different subsets therefore never compare as equal.
- `eval_set_sha256`: a hash over the selected task files. Editing a task changes it, so the baseline has
  to be re-run. The `status:` and `lock_sha256:` lines are left out, so locking a task does not.
- `policy`: `tree-<sha12>`, a hash of `scripts/ hooks/ skills/ agents/`. Pass `--policy LABEL` to name
  it yourself, for example with a git sha.
- `producer_model: harness-code` and `judge_model: deterministic` (plus `producer` and `judge`).
  No model produces or judges anything here, and the gate's "judge equals producer" rule still holds.
- Per task: `locked`, `split`, `scores.correctness` (1.0 when every expected check passes, else 0.0),
  `scores.time` (wall-clock **milliseconds** of the steps; `units.time` is `"ms"`), `checks`
  (`check_id: bool`) and, when a task fails, `failures`.

## Tasks

| id | split | covers | what it pins down |
|---|---|---|---|
| harness-001 | train | scripts/textlen.py | 가족의 비밀 = 6 chars / 5 without spaces / 2 words; --limit exit codes |
| harness-002 | holdout | scripts/textlen.py | decomposed (NFD) jamo counted as syllables; whitespace collapsed |
| harness-003 | train | scripts/translation_qa.py | dropped number blocks; 1억 2천만 원 = KRW 120 million passes |
| harness-004 | holdout | scripts/translation_qa.py | `{0}` → `{1}` and `%s` → `%d` block; intact placeholders pass |
| harness-005 | train | scripts/translation_qa.py | glossary term behind a particle (계약서를) blocks; 계약서식 is not the term |
| harness-006 | train | scripts/style_pairs.py | `nearest`: register first, then Hangul bigram similarity over recency |
| harness-007 | train | scripts/kb.py | `register` idempotent (sha8 29a8825b); `lint` fails on an unresolved raw/ link |
| harness-008 | holdout | scripts/kb.py | `safe-to-delete` is yes only with a PASS line AND an archive URL |
| harness-009 | train | scripts/schema_check.py | `register: poetry` rejected; a valid StylePair accepted |
| harness-010 | train | scripts/invoice.py | ₩1,234,567 → 37,030 + 3,700 = **40,730** withheld; dry run leaves no ledger |
| harness-011 | holdout | scripts/invoice.py | `make` writes a ledger row; next number INV-2026-002; `--wht-unit 1` → 40,740 |
| harness-012 | train | scripts/claim_check.py | a claim with no source line is unsupported (exit 1); a traceable one is kept |
| harness-013 | train | scripts/eval_gate.py | locked-task regression rejected; self-judged run rejected; identical run accepted |
| harness-014 | train | scripts/patterns.py | `ladder` proposes an L2 promotion only after the 3rd episode, and writes nothing |
| harness-015 | train | hooks/verify_gate.py | Stop blocked on an unverified `[x]` item; loop guard; allowed after a verification |
| harness-016 | train | hooks/usage_guard.py | fan-out levels: 69 normal, 70 conserve, 7d 75 conserve, 7d 76 ask, 90 stop |
| harness-017 | train | hooks/log_event.py | 그게 아니라 tagged as a correction; 아니 괜찮아 and "No problem" are not |
| harness-018 | train | hooks/guard_protected.py | `sed -i rubrics/x` and `> evals/...` blocked (exit 2); reads and other paths allowed |
| harness-019 | holdout | hooks/precompact_snapshot.py | snapshot has trigger, instructions, PROGRESS tail, this project's decisions only |
| harness-020 | holdout | hooks/postcompact_reinject.py | re-injected context ≤ 8000 chars, marked truncated, points at HANDOFF.md |

The split is 14 train and 6 holdout. Holdout tasks are never shown to an optimizer: GEPA/ACE proposals
are drafted from `--split train` failures only (evals/README.md, step 6).

## Locking a task (only the user does this)

Every task ships as `status: draft` with `lock_sha256: ""`. `locked: true` already makes the gate refuse
any drop in correctness on the task. Locking also freezes the task file itself:

1. Review the task and run it: `python3 -I scripts/run_evals.py --area harness --task harness-NNN`.
2. Print the lock hashes: `python3 -I scripts/run_evals.py --area harness --lock-hash`
   (output columns: id, hash, `locked` or `unlocked`).
3. Edit the task by hand: set `status: locked` and paste the hash into `lock_sha256: "<hash>"`.
   The hash leaves out the `status:` and `lock_sha256:` lines, so the order of these edits does not
   matter. Commit the change in a reviewed commit.

From then on, if a locked task's file differs from its `lock_sha256`, `run_evals.py` **refuses to run
anything** (exit 2) and names the task. An agent that edits a locked task therefore cannot make a
candidate look better. To change a locked task on purpose, edit it, re-run `--lock-hash`, paste the new
hash, and re-run the baseline. The changed `eval_set_sha256` forces that last step anyway.

Agents never set `lock_sha256` or `status: locked`. The permission deny rules on `evals/**` and the
`guard_protected.py` hook (harness-018 tests it) enforce this.

## Writing a task

Copy `task_template.yaml` to `tasks/harness-NNN.yaml`. The task files use a YAML subset: block maps and
lists, one-line flow `[...]` / `{...}`, quoted scalars, `#` comments, and block scalars (`|`, `|-`, `>`)
whose lines are kept verbatim, so fixture Markdown can contain `# headings`. Quote any plain value that
contains ` #`.

- `input.files`: `{path, content, header, repeat}`, written relative to `$WORK`. A path that leaves
  `$WORK` is an error. `content` is repeated `repeat` times after `header`.
- `input.steps`: either `run: "<argv>"` (split like a shell, but no shell runs; with `stdin`, `env`,
  `cwd`, `timeout`) or `write: PATH` with `content` and optional `append: true`.
- Substitutions in commands, stdin, env and file contents: `${PY}`, `${ROOT}`, `${WORK}`, `${DATA}`,
  `${HOME}`, `${TODAY}`, `${NOW}`, `${NOW+N}`, `${NOW_ISO}`, `${NOW_ISO+N}`.
- Environment: `HOME`, `HARNESS_DATA` and `HARNESS_STATE` point inside `$WORK`, and every other
  `HARNESS_*` variable is removed. A task can never reach `~/harness-data`.
- `expected_checks`: `exit_code`, `stdout_contains`, `stdout_not_contains`, `stderr_contains`,
  `stdout_empty`, `file_exists`, `file_absent`, `file_contains`, `file_not_contains`, and `json`.
  A `json` check reads stdout, or `source: "file:<glob>"`, with `format: jsonl` for JSON lines. It takes
  a `path` (`a.b[0].c`) and one operation: `equals`, `contains`, `not_contains`, `len_equals`,
  `len_lte`, `len_gte`, `gte`, `lte`, `exists`, `any_match` or `none_match`. A match key ending in `~`
  means "contains". `step` defaults to the last run step.
- Keep `components:` on one line. The component graph reads it.

Before you lock a new task, check that it can fail. Break the expected value, or the code under test
in a scratch copy of the harness, and confirm the task goes red.
