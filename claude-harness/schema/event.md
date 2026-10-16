# Event record (one JSON object per line in `$HARNESS_DATA/log/YYYY-MM.jsonl`)

Append-only: never edit a past event. Correct it with a new event that has `corrects: <id>`.

```json
{
  "id": "evt_20261016_1432_ab12",
  "ts": "2026-10-16T14:32:05Z",
  "actor": "me | agent:<name>",
  "model": "haiku|sonnet|opus|fable|null",
  "scope": "global | <area>/<project>",
  "type": "prompt|decision|correction|mishap|handoff|session_note|verification|intake|task",

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
  "proof": [{"kind": "output|test|quote|diff|link", "ref": "..."}],
  "labels": ["..."],
  "parent_event": "evt_... | null",
  "pointers": ["path/or/url", "..."],
  "outcome": "pending|worked|failed|reverted",
  "cost_usd": 0.0
}
```

`intent`, `situation` and `meta` are **mandatory** for decision, correction, mishap and session_note events. They are the labels the improvement loop learns from.
