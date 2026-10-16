---
name: integrate
description: Run the NEW COMPONENT integration checklist for a skill, agent, hook or script added to (or materially changed in) the harness. Checks frontmatter/model, learning contract, rubric + eval area, pipeline membership, docs/INDEX regeneration and the harness eval run, through the `new-component` pipeline's machine checks, and drafts the missing pieces as proposals. Never approves evals, rubrics or contracts itself. Use when a component file is created, when the watch hook queues one, or when the user says "integrate <component>".
argument-hint: "<path, e.g. skills/foo/SKILL.md | agents/bar.md | hooks/baz.py | scripts/qux.py>"
---

# Integrate a new component

Component: $ARGUMENTS. `P="python3 -I ${CLAUDE_PLUGIN_ROOT}/scripts/pipeline.py"`. Work in the harness checkout
(`~/code/claude-harness`, the one with `.claude-plugin/plugin.json`), never in the installed plugin cache.

**Hard rules.**
- Never edit `evals/`, `rubrics/` or `tests/` to make a check pass, and never mark a rubric, eval task or learning
  contract as approved or `active`. You write **drafts** (`status: draft`, or a proposal file) and the user approves.
- Each check is a script, not your judgment. If a check fails, fix the component or propose the missing piece;
  never weaken the check (`docs/VERIFICATION.md`, "Never weaken the check to pass it").

## 0. Start (or resume) the pipeline
1. `$P start new-component --scope <harness root> --param component=<relative path>`. The watch hook may already
   have started it (`$P status --scope <harness root>` shows it); starting again is a no-op.
2. `$P check --scope <harness root>` prints which of the six required steps already pass. Work only on the
   missing ones, in the order below. The Stop gate (`hooks/pipeline_gate.py`) blocks ending the turn until they pass.

## 1. Frontmatter and model (`frontmatter`)
- Skill: `name` (= folder name) and a `description` that says what it does and when to use it.
- Agent: `name`, `description`, an explicit `model:` (haiku / sonnet / opus / fable, `global/CLAUDE.md` Model
  routing), and no `Agent` tool unless it is the orchestrator (`docs/FANOUT.md` §6).
- Hook: registered in `hooks/hooks.json` (keep every existing hook) with a timeout, a module docstring stating the
  event, the off switch and "never crashes".
- Script: a module docstring whose first line says what it does (the index uses it), stdlib only, `python3 -I`.

## 2. Learning contract (`learning-contract`)
Propose an entry for `learning/contracts.yaml` keyed by the component id (`skill:<name>`, `agent:<name>`,
`script:<path>`; hooks are covered by their script): `signals`, `logged_as`, `learns`, `evaluated_by`, `cadence`,
`owner`, `status: draft`. If the component has nothing to learn (a library, a validator), propose an `exempt`
entry with a one-line reason. Show the YAML to the user; write it only after they agree with the shape, and keep
`status: draft` until they approve it in review-week.

## 3. Rubric and eval area (`rubric-eval`)
- Work-producing skills and agents need a rubric (`rubrics/<id>.yaml`) and an eval area
  (`evals/<area>/task_template.yaml`). If an existing pair fits, reference it from the component's text.
- Otherwise draft both as **proposals** under `$HARNESS_DATA/proposals/<date>_<component>/` (rubric with
  `status: draft`, task template, and how to collect ~20 real tasks: `evals/README.md` "Building a set"). The user
  moves them into the repo.
- Meta components (planning, logging, improvement loops) instead get an `exempt` reason in
  `scripts/harness_index.json`, proposed to the user.

## 4. Pipeline membership (`pipeline-membership`)
Add the component to `pipelines/pipelines.yaml`: as a step (with `required`, `after`, `pre`, `post`,
`verification` and machine-checkable `evidence`) in the pipeline where it runs, as a new pipeline with triggers,
or under `standalone:` with the reason it runs on its own. Then `$P lint` must exit 0.

## 5. Regenerate the index (`index`)
`python3 -I ${CLAUDE_PLUGIN_ROOT}/scripts/harness_index.py --write`, then `--check` (exit 0). Read the new warnings
for this component (orphan, coverage gap, dangling reference) and fix or report each.

## 6. Harness eval run (`eval-run`)
Run `self-eval --changed <path>`: it uses `harness_index.py --affected` to pick the areas, gates them with
`eval_gate.py`, and logs a `task` event with `meta.kind_of_thing: self-eval` (that event is this step's evidence).
An `ungated` area is reported, not hidden.

## 7. Changelog and finish
1. `python3 -I ${CLAUDE_PLUGIN_ROOT}/scripts/changelog.py update --scope <harness root> --file <entries>` (it logs
   `changelog_updated`); `changelog.py check --scope <harness root>` must exit 0.
2. Run the unit tests (`python3 -I -m unittest discover -s tests -t .`) and `claude plugin validate .`.
3. `$P finish --scope <harness root>`. It refuses while a required step lacks evidence.
4. Report to the user: each checklist line with its proof (command + decisive output), and the list of drafts
   waiting for their approval (contract, rubric, eval tasks, exempt reasons).
