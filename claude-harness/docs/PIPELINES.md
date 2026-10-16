# Pipelines: the right skills, in the right order, enforced (v1, 2026-10-16)

A **pipeline** is the declared process for one kind of work: the ordered steps (skills, agents, scripts), which of them are required, each step's pre- and postcondition (`docs/VERIFICATION.md`), and the **evidence** that proves it ran. The process graph is `pipelines/pipelines.yaml`. `scripts/pipeline.py` reads it, and three hooks make it fire on its own and hold until it is done.

Before this, the order of skills lived in prose (`agents/orchestrator.md`, the skill files) and relied on the model's goodwill. Now it is data that a script can check against the log.

## 1. How it works

```
prompt ──► pipeline_router (UserPromptSubmit) ── match ──► "This looks like <p>; run these steps in order…"
                                                           orchestrator: pipeline.py start <p> --scope <project>
new file in inbox/ ──► watch_inbox (FileChanged / SessionStart scan / launchd queue) ──► queue + autostart intake
new skill/agent/hook/script ──► watch_inbox ──► autostart new-component (integration checklist)
context ≥ 200k ──► pipeline_router ──► autostart context-handoff
                      │
                      ▼
       <project>/.harness/pipeline_state.json   +  PROGRESS.md "In progress" checklist block
                      │
 steps run, and log events / write files as they normally do
                      │
 turn ends ──► pipeline_gate (Stop): required step without evidence? ──► block, naming the next step
              pipeline.py finish ──► pipeline_finished
```

| Piece | Role |
|---|---|
| `pipelines/pipelines.yaml` | Triggers, ordered steps, `required`, `after`, `pre`/`post`, `verification` anchor and evidence matchers, for: new-project, intake, translation, synopsis, email-draft, job-application, research, code-change, invoice, annotation-batch, session-end, context-handoff and new-component |
| `scripts/pipeline.py` | `match` (rule-based classifier with an abstain rule), `start`, `status`, `mark`, `check`, `finish`, `abandon`, `queue scan/list/ack` and `lint` |
| `hooks/pipeline_router.py` (UserPromptSubmit) | Suggests the matched pipeline and its steps when no run is active. With an active run, shows one line per run with its next step. Surfaces queued items once per session. Autostarts `context-handoff` at ≥ 200k context. Never blocks |
| `hooks/pipeline_gate.py` (Stop) | Blocks the end of a turn while an active, non-stale run lacks a required step (or breaks `strict_order`). The reason lists the missing steps and the exact next `run` with its pre/post |
| `hooks/watch_inbox.py` (SessionStart, FileChanged) | Returns `watchPaths` (the project's `inbox/` and the harness component dirs). Scans the inbox at session start. Queues new inbox files and harness components, logs `inbox_file_detected` / `component_detected`, and autostarts `intake` / `new-component` |
| `mac/launchd/com.harness.inbox-watch.plist` + `scripts/install_watchers.py` | The out-of-session watcher: one plist per project (launchd `WatchPaths` cannot glob), running `pipeline.py queue scan <project> --source launchd` |
| `skills/integrate` | Runs the new-component checklist and drafts the missing pieces (never approves them) |
| `agents/orchestrator.md` §0a | Match first, start, follow the order, mark with evidence, finish |

### Run state
- **State file.** `start` writes `<project>/.harness/pipeline_state.json`, holding `runs[]` with `run_id`, `pipeline`, `status` (active / finished / abandoned), `started_at`, `params` and `marks`. It also logs `pipeline_started`. The project is the nearest directory with `.harness/`, `PROGRESS.md` or `.git`. `.harness/` is runtime state: keep it out of git.
- **Checklist block.** It goes into PROGRESS.md under "In progress", between `<!-- pipeline:<id> -->` markers, with ☐ for pending and ☑ for satisfied. It never uses `[x]` or ✅, so `verify_gate.py` does not count pipeline steps as done items. Because it sits under "In progress", `postcompact_reinject.py` re-injects it after a compaction.
- **Idempotent start.** Starting the same pipeline with the same params while a run is active returns the existing run.
- **Queue acks.** Starting `intake --param file=<f>` acks the matching queue entry. `new-component --param component=<path>` does the same for its entry.

### Evidence matchers (all read-only; nothing in the YAML executes commands)

| Kind | Satisfied when |
|---|---|
| `event: <type>` (+ `labels`, `not_labels`, `verdict`, `agent`, `where` on dotted fields, `content_re`, `min_count`) | Enough matching events exist in `$HARNESS_DATA/log/*.jsonl` (the newest 3 months) **in the project scope** (cwd/scope_hint/project_dir under the project, `scope` = `<area>/<project>`, or an absolute pointer) **since the run started** (minus `grace_s`, 120 s) |
| `file: <glob>` (+ `changed_since_start`, `contains`, `not_contains`) | A file under the project matches. Dotfiles and `.harness/` are ignored. For `PROGRESS.md`, "changed" means changed **outside** the pipeline's own blocks, compared by content hash |
| `json: <file>` + `has: a[*].b` (+ `select: {k: '{param}'}`) | Some value at that path is non-empty, e.g. the intake manifest entry whose `original_name` is the run's file. Unresolved placeholders drop the select key |
| `store: <path>` (+ `where`) | A record in a `$HARNESS_DATA` JSONL store (research ledger, applications, style pairs) has `ts` ≥ start. A record that carries a scope must be in scope; one without a scope is accepted |
| `builtin: <name>` | `component_frontmatter`, `learning_contract`, `rubric_eval`, `pipeline_membership` or `index_fresh` passes for the run's `component` param (the new-component checklist) |
| `lib:<name>` | A named matcher from `evidence_library` (`verify_pass`, `tier_v` = 2+ passing non-`step_check` verifications, `changelog` = `changelog_updated`, …) |

- **`mark`.** `mark <step> --evidence <event id>` binds an event the matchers can't see, typically one logged with a different scope. It is refused (exit 2) unless the event exists, is newer than the run, and matches one of the step's event matchers. Steps with `manual: true` (e.g. the user's OK on an email) accept any event logged since the start.
- **Order.** `after` lists prerequisite steps. A step with evidence whose prerequisite has none is an order violation. So is event/store evidence older than a prerequisite's. Violations are warnings, except in a pipeline with `strict_order: true` (intake: never archive before verify), where they fail `check` and block Stop.
- **Next step.** It is the first required step that is missing and whose prerequisites are satisfied.

### Classifier (`match`)
- **Inputs.**
  - A prompt starting with a pipeline's `/skill` (or `/harness:skill`) scores 0.95.
  - Otherwise each pipeline scores `strong` regex hits 0.6 (+0.1 per extra), `weak` hits 0.15 each (max 3), and `negative` hits −0.6.
  - Event JSON (`{"event": "inbox_file_detected"}`, a FileChanged payload with an inbox or component path) maps directly.
- **Abstain.** It abstains (pipeline `null`) when the top score is below `min_confidence` (0.6), when the top two are within `margin` (0.15), or on trivial input. When it abstains, the orchestrator decides. A wrong confident match costs one ignored note, since the router never starts a task pipeline by itself.

## 2. How to add a pipeline (or a step)

1. **Add the entry.** Write it under `pipelines:` in `pipelines/pipelines.yaml` with `title`, `owner_agent`, `client_bound`, `autostart` (`never` unless the trigger is a deterministic event), `params` and `triggers` (`slash`, `strong`, `weak`, `negative`, `events`). Then list the `steps` in order.
2. **Fill in every step.** Each one needs `run`, `required`, `after`, `pre`, `post`, `verification` (a `docs/VERIFICATION.md#<slug>` that exists) and **evidence that can fail**. Prefer evidence the step already produces (an event the skill logs, a file it writes, a store row) over a new self-report.
3. **Mark client-bound work.** If the output goes to a client or employer, set `client_bound: true` and add a required `verify` step with `lib:tier_v` (lint enforces this).
4. **Lint.** `python3 -I scripts/pipeline.py lint` must exit 0. It checks the regexes, matcher keys, run targets, `after` refs, anchors and the client-bound rule. It also checks that every skill and agent is a step, an entry `/skill` or listed under `standalone:` with a reason.
5. **Test and integrate.** Add a classifier case to `tests/test_pipeline.py` (`MatchTest`), run the suite, and run `/integrate` if you added a component.
6. **Schema.** A new event type used as evidence needs to be declared in `schema/ontology.yaml` `event_type` (ask the schema owner).

## 3. Guarantees and their limits

| Guarantee | Enforced by | Limit |
|---|---|---|
| A started run cannot end a turn with a required step missing | `pipeline_gate.py` (Stop `decision: block`) | **One nudge per turn.** With `stop_hook_active` true the stop is allowed (loop guard), so the model can still stop after one block. Repeated misses show up as runs that stay active, which `status` and SessionStart report. Off with `HARNESS_PIPELINE_GATE=0`. Subagent stops are not gated |
| The intake order (verify before archive) | `strict_order` + `after`; also `kb.py safe-to-delete` (needs PASS + archive) | File/json evidence carries no exact timestamp, so file-only steps are checked for presence, not order |
| A new inbox file is noticed | `watch_inbox.py` (FileChanged, plus a scan at every SessionStart) and the launchd watcher (queue) | FileChanged payload fields and `watchPaths` on directories are **unverified on the Mac** (assumptions in the hook docstring). The SessionStart scan and launchd cover gaps. Nothing is processed without a session: the launchd job only queues and **never runs claude** on client files. There is deliberately no unattended mode (it would need an explicit opt-in flag that doesn't exist) |
| A new component gets the full integration checklist | `watch_inbox.py` autostarts `new-component`; builtins check frontmatter/model, contract, coverage, membership and index freshness from the files themselves; `pipeline.py lint` covers membership | Watched only in a harness checkout (cwd inside it, or `HARNESS_DEV_ROOT`), not in the installed plugin cache. A changed component is only queued (self-eval suggestion), never forced |
| Context ≥ 200k ends in a handoff | `pipeline_router.py` autostarts `context-handoff` from the status-line state; the gate enforces it | Needs a fresh status-line state (`statusline.py`), and only applies in a project (PROGRESS.md) |
| Which pipeline a task belongs to | **Advisory.** The router suggests; the orchestrator starts it | Regex classification can miss or abstain. A task pipeline is not tracked until `start` runs, and the gate only enforces started runs |
| Evidence is real | The matchers read the log, files and stores | **Presence, not truth.** An agent could log a fake `verification` event. The defenses are independent verifiers, `schema_check.py`, the weekly label pass and spot audits of `pipeline_step` marks. Events labeled `step_check` never satisfy `verify` steps |
| Stale runs don't nag forever | `defaults.stale_days` (7): stale runs stop blocking and are reported instead | A stale run still needs `finish` or `abandon`. `abandon` requires `--reason` with the user's words and logs `pipeline_finished` with `outcome: abandoned` |

**Hooks vs advisory, in one line.**
- **Enforced:** the Stop gate on started runs, `mark` validation, the finish refusal, strict order, autostart for inbox / new-component / context.
- **Advisory:** the classifier's suggestion, the orchestrator's choice to start a task pipeline, and optional steps.

## 4. Events and state (schema follow-ups)
| Event | Written by | Fields |
|---|---|---|
| `pipeline_started` | `pipeline.py start` | `pipeline`, `run_id`, `params`, `source`, `pointers` (state file), `labels: [pipeline, pipeline:<id>]` |
| `pipeline_step` | `pipeline.py mark` | `pipeline`, `run_id`, `step`, `evidence: [evt id]`, `parent_event` |
| `pipeline_finished` | `pipeline.py finish` / `abandon` | `pipeline`, `run_id`, `outcome: worked\|abandoned`, `items` (steps satisfied, or missing on abandon), `justification` (abandon reason) |
| `inbox_file_detected` | `pipeline.py queue scan`, `watch_inbox.py` | `pointers: [path]`, `items: [queue id]`, `source` (`launchd`, `hook:file_changed`, `hook:session_start`, `scan`) |
| `component_detected` | `watch_inbox.py` | `component` (id), `change: new\|changed`, `pointers`, `items` |

**Queue.** `$HARNESS_DATA/queue/inbox.jsonl` is append-only, with `{id: q_…, ts, kind: inbox_file|component_new|component_changed, path, project, source, size, mtime, pipeline}`. Acks go to `queue/acked.jsonl`, and the router's per-session "already shown" memory is `queue/surfaced.json`.

## 5. Mac setup
```bash
python3 -I ~/code/claude-harness/scripts/install_watchers.py list                 # projects under ~/projects
HARNESS_PROJECT_ROOTS=~/projects:~/work python3 -I …/install_watchers.py install --dry-run
python3 -I ~/code/claude-harness/scripts/install_watchers.py install              # re-run after /new-project
export HARNESS_DEV_ROOT=~/code/claude-harness   # so component edits are watched from any session
```
**Verify on the Mac** (first session after installing):
1. Drop a file into a project's `inbox/` and check that `$HARNESS_DATA/queue/inbox.jsonl` gets a `launchd` entry within ~15 s.
2. In a session, drop another file and check that the FileChanged hook fires. If it doesn't, note the real payload field names and `watchPaths` behaviour in `hooks/watch_inbox.py`.
