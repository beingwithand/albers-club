# Eval sets

The improvement loop (BLUEPRINT.md §0.5, §4.13) changes rules, skills, prompts and routing only when a
fixed eval set **does not get worse**. This folder defines how those eval sets are built and scored.
`scripts/eval_gate.py` makes the accept/reject call.

## Layout

```
evals/
├── README.md                    # this file
└── <area>/                      # translation, annotation, job-search, research, code, art, intake
    ├── task_template.yaml       # copy this to make a task
    └── tasks/
        ├── <area>-001.yaml      # ~20 real tasks per area
        ├── ...
        └── fixtures/            # inputs referenced by tasks (source texts, PDFs, repos at a commit)
```

Results are data, not policy, so they live in the data repo:
`$HARNESS_DATA/evals/results/<area>/<YYYY-MM-DD>_<policy-sha>.json`.

## Building a set (~20 tasks per area)

1. **Use real tasks.** Pull them from the event log: finished `task` events whose outcome is known, and
   especially tasks you **corrected** (`is_correction` labels, mishaps). Corrected tasks are the most informative.
2. **Mix difficulty.** About 10 routine, 6 hard and 4 known failure cases (past mishaps). Cover every register,
   direction or sub-type the area has.
3. **Freeze the input.** Copy the input into `tasks/fixtures/` (or pin a repo commit/URL snapshot) and record
   its sha256 in the task. Remove client-identifying data or keep the set in the private data repo.
4. **Write criteria before running anything.** Each task points at a `rubrics/<type>.yaml` and may add
   task-specific criteria (for example "must keep the term 계약 해지 as 'contract termination'").
5. **Lock the expected checks.** `expected_checks` are deterministic, automatic checks (exact numbers,
   placeholders, test commands, page counts). Set `locked: true` on tasks whose checks define correctness.
   The gate rejects any candidate that drops correctness on a locked task, whatever the averages do.
6. **Split 14 / 6.** Mark about 6 tasks `split: holdout`. Never show holdout tasks to the optimizer (GEPA/ACE
   proposals are drafted from `train` failures only). The public overfitting example in the blueprint, where
   training went from 90% to 95% while held-out dropped from 95% to 85%, is the reason for this split.
7. **Get human calibration.** Score 3 to 5 tasks yourself with the same rubric and store them as
   `human_scores`. If the judge differs from you by more than 1 point on a criterion, fix the rubric anchors
   before trusting the judge.

## Scoring a run

For each task: run the producing agent with the **candidate policy**, run the `expected_checks`, then have
the judge score the rubric.

- **The judge model must differ from the producer model** (for example, producer `sonnet` with judge `opus`).
  Self-evaluation skews positive. `eval_gate.py` rejects a result file whose `producer_model` equals its
  `judge_model`.
- The judge checks correctness and the stated criteria only. It does not "find anything", because that
  rewards over-engineering.
- Run each task 3 times when the producer is non-deterministic, and record the mean.

### Result file format (input to `eval_gate.py`)

```json
{
  "eval_set": "translation",
  "eval_set_sha256": "sha256 over the sorted task files (detects edited tasks)",
  "policy": "git sha or label of the rules/skills under test",
  "producer_model": "sonnet",
  "judge_model": "opus",
  "run_at": "2026-10-16T12:00:00Z",
  "tasks": {
    "translation-001": {
      "locked": true,
      "split": "train",
      "scores": {"correctness": 4.6, "style_match": 4.0, "correction_rate": 0.10,
                 "cost": 0.12, "time": 3.5, "outcome": 1.0},
      "checks": {"numbers_match": true, "placeholders_intact": true}
    }
  }
}
```

Direction of each dimension: `correctness`, `style_match` and `outcome` are better when **higher**.
`correction_rate`, `cost` (USD) and `time` (minutes) are better when **lower**. A dimension may be missing
when it does not apply, and it is then skipped.

## The gate

```bash
python3 -I scripts/eval_gate.py baseline.json candidate.json            # exit 0 accept, 1 reject
python3 -I scripts/eval_gate.py base.json cand.json --tolerance cost=15% --tolerance style_match=0.2
```

The gate rejects the candidate if any of these hold:
- any dimension's mean regresses beyond its tolerance
- correctness drops on any locked task
- a locked check that passed in the baseline now fails
- tasks are missing from the candidate run
- the eval set hash differs between the runs
- the judge model equals the producer model

The report it prints is the justification you paste into the commit or PR that adopts the change.

## Protecting the evals (anti reward hacking)

Producing agents must not be able to edit `evals/`, `rubrics/` or `tests/`. Enforce this two ways.

**1. Permission deny rules.** Add these to the user `settings.json` (installed by `install.sh`):

```json
{
  "permissions": {
    "deny": [
      "Edit(**/evals/**)", "Write(**/evals/**)",
      "Edit(**/rubrics/**)", "Write(**/rubrics/**)",
      "Edit(**/tests/**)", "Write(**/tests/**)"
    ]
  }
}
```

**2. A `PreToolUse` hook on `Bash`.** Deny rules on Edit and Write do not stop `sed -i`, `>` or `mv` run
through Bash. The hook should block commands that write under `evals/`, `rubrics/` or `tests/`. Like other
hook changes, it is added via a reviewed PR to `hooks/hooks.json`.

Only you change eval sets, in a reviewed commit. When a task is changed, the `eval_set_sha256` changes and
the baseline must be re-run, so an edited task can never make a candidate look better.
