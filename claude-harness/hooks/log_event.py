"""Append a raw event to $HARNESS_DATA/log/YYYY-MM.jsonl from a Claude Code hook.

Raw capture only. Labeling (intent/meta/correction detection) happens later in the
weekly review, using a cheap model, so this hook stays fast and never blocks.
Field names follow the hooks reference; verify against
https://code.claude.com/docs/en/hooks if a field comes back empty.
"""
import datetime
import json
import os
import pathlib
import sys
import uuid

kind = sys.argv[1] if len(sys.argv) > 1 else "unknown"
try:
    payload = json.load(sys.stdin)
except Exception:
    payload = {}

data_dir = pathlib.Path(os.environ.get("HARNESS_DATA", pathlib.Path.home() / "harness-data"))
now = datetime.datetime.now(datetime.timezone.utc)
log_dir = data_dir / "log"
log_dir.mkdir(parents=True, exist_ok=True)

cwd = payload.get("cwd", os.getcwd())
event = {
    "id": f"evt_{now:%Y%m%d_%H%M%S}_{uuid.uuid4().hex[:4]}",
    "ts": now.isoformat(),
    "actor": "me" if kind == "prompt" else "harness",
    "type": kind,
    "scope_hint": cwd,
    "session_id": payload.get("session_id"),
    "content": payload.get("prompt") if kind == "prompt" else None,
    "transcript_path": payload.get("transcript_path"),
    "end_reason": payload.get("reason") if kind == "session_end" else None,
    "labels": [],
    "intent": None,     # filled by weekly labeling pass
    "meta": None,       # filled by weekly labeling pass
}

with open(log_dir / f"{now:%Y-%m}.jsonl", "a", encoding="utf-8") as f:
    f.write(json.dumps(event, ensure_ascii=False) + "\n")

sys.exit(0)
