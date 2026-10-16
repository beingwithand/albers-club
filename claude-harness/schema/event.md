# Event record (one JSON object per line in `$HARNESS_DATA/log/YYYY-MM.jsonl`)

Append-only: never edit a past event. Correct it with a new event that has `corrects: <id>` (or, for labels, a `label` event with `labels_for: <id>`).
The machine-readable definition is type `Event` in `schema/ontology.yaml` (v0.2.0); `scripts/schema_check.py` validates the log against it.

```json
{
  "id": "evt_20261016_143205_ab12",
  "ts": "2026-10-16T14:32:05+00:00",
  "actor": "me | harness | agent:<name>",
  "model": "haiku|sonnet|opus|fable|null",
  "scope": "global | <area> | <area>/<project>",
  "type": "prompt|session_end|decision|correction|mishap|handoff|session_note|verification|intake|task|label|precompact|postcompact|drill|pattern_proposed|pattern_promoted|pattern_retired|unknown",

  "intent": "why this was done or asked: the goal behind it",
  "situation": "the context at the time (what was happening, constraints, deadline)",
  "content": "the thing itself, or a pointer to it",

  "meta": {
    "kind_of_thing": "e.g. 'recurring setup mistake', 'style preference', 'scope decision'",
    "repeat_how": "how to repeat it if it worked",
    "prevent_how": "how to prevent it if it failed",
    "generalizes_to": ["global", "translation", "..."]
  },

  "justification": "specific reasons, not 'seemed best'",
  "proof": [{"kind": "output|test|quote|diff|screenshot|link", "ref": "..."}],
  "labels": ["..."],
  "parent_event": "evt_... | null",
  "corrects": "evt_... | null",
  "pointers": ["path/or/url", "..."],
  "outcome": "pending|worked|failed|reverted",
  "cost_usd": 0.0
}
```

`intent`, `situation` and `meta` are **mandatory** for decision, correction, mishap and session_note events. They are the labels the improvement loop learns from. Hook-written events start with `intent: null, meta: null`; the weekly pass (`scripts/label_events.py`) fills them with a later `label` event, never by editing the line. `schema_check.py` reports a missing one as a warning unless a `label` event points at the id.

## Field conventions
- **`id`**: `evt_<YYYYMMDD>_<HHMMSS>_<4 hex>` (UTC), as written by `hooks/log_event.py`, `hooks/_common.py` and `scripts/label_events.py`. Older hand-written ids with `<HHMM>` are still accepted.
- **`ts`**: ISO 8601 with offset (`+00:00` or `Z`).
- **`actor`**: `me` (a prompt typed by the user), `harness` (a hook), or `agent:<name>` (a subagent or script acting as one, e.g. `agent:librarian`).
- **`scope`**: `global`, an area (`job-search`), or `<area>/<project>` (`translation/acme`, `annotation/<platform>`). Areas come from `areas:` in the ontology. Hook events carry `scope_hint` (the cwd) instead; `weekly_report.py` derives the scope from it.
- **`session_id`, `transcript_path`**: from the Claude Code hook payload; link an event to its session.
- **`agent`**: the subagent name for `task` events from the orchestrator (`model` is the model it ran on).

## Optional fields by event type (as written by the scripts and skills)

| type | written by | extra fields |
|---|---|---|
| `prompt` | `hooks/log_event.py prompt` | `content` (the prompt), `scope_hint`, `session_id`, `transcript_path`, `correction_candidate` (bool), `correction_confidence` (0..1), `correction_patterns` (list) |
| `session_end` | `hooks/log_event.py session_end` | `end_reason` |
| `label` | `scripts/label_events.py --apply` | `labels_for: <event id>`, `parent_event` (same id), `intent`, `situation`, `meta`, `labels`, `is_correction`, `scope`, `source_batch` (path of the model output) |
| `verification` | skill `verify`; `hooks/step_check.py` (labeled `step_check`) | `verdict: pass\|fail\|needs-human`, `items` (PROGRESS/tasks entries covered; matched by `hooks/verify_gate.py`), `scope_hint`, per-criterion results with `proof`. Events labeled `step_check` are per-edit syntax checks (`items: [path]`); the Stop gate and `weekly_report.py` ignore them |
| `handoff` | skill `handoff` | `pointers` to HANDOFF.md, `cold_read: {score: "6/6", rounds: N, model: "haiku"}` |
| `precompact` | `hooks/precompact_snapshot.py` | `trigger`, `custom_instructions`, `pointers` to `log/handoffs/auto_<ts>.md` |
| `postcompact` | `hooks/precompact_snapshot.py post` | `trigger`, `content` (compact summary, truncated), `pointers` |
| `decision` | skill `why` (also mirrored to the project's `decisions.md` as `D-<YYYYMMDD>-<n>`) | `claim` (or `content`), `justification`, `proof`, `pointers` |
| `correction` | skills `review-week`, `synopsis`, `annotation-workflow` | `corrects`, plus the `Correction` fields `agent_did`, `my_correction`, `my_reasoning` |
| `mishap` | skill `mishap` (mirrored to `log/mishaps.md`) | `proof`, `pointers` |
| `task` | orchestrator and most skills | `agent`, `model`, `cost_usd`, `outcome`; fan-out runs may add `fanout_tier`, `fanout_n`, `est_tokens` |
| `drill` | monthly restore drill (`docs/BACKUP.md`) | `outcome` |
| `pattern_proposed` | `scripts/patterns.py record` (skill `pattern-review`, `retro`) | `patterns` (ids: `pat_`/`enc_`/`mp_`), `pattern_status` (the new status), `intent`, `situation`, `meta`, `pointers` (the store file) |
| `pattern_promoted` | `scripts/patterns.py record` after my approval | same; written when the new status is `approved`, `encoded` or `reopened` (an L3 promotion also carries the eval gate result in `content`) |
| `pattern_retired` | `scripts/patterns.py record` | same; written when the new status is `decaying` or `retired` |
| `unknown` | `hooks/log_event.py` called without a kind | none |

### Fan-out fields (optional, any type; mainly `task`)
- **`fanout_tier`**: the tier from `docs/FANOUT.md`: `0 | 1 | 2 | 3 | V | S`.
- **`fanout_pattern`**: the pattern used, e.g. `parallel-search`, `map-reduce`, `vote`, `judge-panel`, `refuters`, `hypotheses`, `writer-reviewer`.
- **`fanout_uncovered`**: a list of the workers or sub-questions that failed or came back empty.
- **`usage_level`**: the usage budget level at the start, `unknown | normal | conserve | ask | stop` (from `hooks/usage_guard.py`).
- **`fanout_n`**: number of parallel workers/subagents spawned (integer).
- **`est_tokens`**: estimated tokens for the unit before it ran (integer), to compare against actual cost.

## Conventions used by the scripts
- **Corrections** are either explicit `correction` events or `label` events with `is_correction: true`.
- **Verdicts**: `weekly_report.py` also accepts `outcome`/`result` and the aliases `passed`, `ok`, `failed`, `needs_human`; write the canonical `verdict` values.
- `drill` and `unknown` were used in code/docs but missing from the v0.1 type list; they are now declared.
