#!/usr/bin/env python3
"""Weekly labeling pass for the raw event log (BLUEPRINT.md §0.5 "improvement loop", schema/event.md).

The hooks capture raw events with `intent`/`meta` left empty. This script prepares a batch of
unlabeled events for a cheap model (haiku) to label, then merges the labels back as NEW events.
The log is append-only: past lines are never modified.

Two modes:

  1. Export (default): write a JSONL batch of unlabeled candidate events plus a prompt file, and
     print the exact `claude -p` command to run.

       python3 -I scripts/label_events.py --from 2026-10-09 --to 2026-10-16

  2. Apply: read the model's JSONL output and append one `label` event per labeled id to
     $HARNESS_DATA/log/<current YYYY-MM>.jsonl, with `labels_for: <id>`.

       python3 -I scripts/label_events.py --apply labels_out.jsonl

Candidates are events that no label event points at yet and that are either
  - prompts (each may be a correction of the previous agent turn), or
  - corrections/decisions/mishaps/session_notes missing the mandatory intent/situation/meta.

Stdlib only. Run with `python3 -I`. Exit codes: 0 ok, 1 nothing valid to apply, 2 usage error.
"""
import argparse
import datetime as dt
import json
import os
import pathlib
import sys
import uuid

try:  # advisory lock for concurrent appends (hooks may write at the same time)
    import fcntl
except ImportError:  # pragma: no cover - non-POSIX
    fcntl = None

MANDATORY_TYPES = {"decision", "correction", "mishap", "session_note"}
CANDIDATE_TYPES = {"prompt"} | MANDATORY_TYPES
LABEL_TYPE = "label"
LABEL_FIELDS = ("intent", "situation", "meta", "labels", "is_correction", "scope")
META_KEYS = ("kind_of_thing", "repeat_how", "prevent_how", "generalizes_to")

PROMPT = """You label events from a personal Claude Code work log. Input: JSON Lines on stdin, one event per
line with fields id, ts, type, scope_hint, content (the user's prompt or note) and prev_content (the user's
previous prompt in the same session, if any).

For EVERY input line output exactly one JSON object on its own line, and nothing else (no prose, no code
fences). Schema:
{"labels_for": "<the input id>",
 "intent": "why the user asked/did this: the goal behind it, one sentence",
 "situation": "the context at the time (what was happening, constraints), one sentence",
 "meta": {"kind_of_thing": "e.g. 'style preference', 'scope decision', 'recurring setup mistake', 'routine request'",
          "repeat_how": "how to repeat it if it worked, or \\"\\"",
          "prevent_how": "how to prevent it if it was a problem, or \\"\\"",
          "generalizes_to": ["global" or areas: translation, annotation, job-search, art, code, research, personal]},
 "labels": ["short", "lowercase", "tags"],
 "is_correction": true if the user is redirecting, undoing or fixing what the agent just did, else false,
 "scope": "global" or "<area>/<project>" if clear from scope_hint, else null}

Be literal and brief. Do not invent facts that are not in the content. If content is empty, still output
the object with intent "unknown" and is_correction false."""


def data_dir(arg):
    if arg:
        return pathlib.Path(arg).expanduser()
    return pathlib.Path(os.environ.get("HARNESS_DATA", pathlib.Path.home() / "harness-data"))


def parse_date(s):
    try:
        return dt.date.fromisoformat(s)
    except ValueError:
        raise argparse.ArgumentTypeError(f"not a YYYY-MM-DD date: {s!r}")


def event_date(ev):
    """Return the UTC date of an event's ts, or None if unparseable."""
    ts = ev.get("ts")
    if not isinstance(ts, str):
        return None
    try:
        t = dt.datetime.fromisoformat(ts.replace("Z", "+00:00"))
    except ValueError:
        return None
    if t.tzinfo is not None:
        t = t.astimezone(dt.timezone.utc)
    return t.date()


def iter_log(log_dir, warn=True):
    """Yield (path, lineno, event) for every valid JSON object line in log/*.jsonl, in file order."""
    for path in sorted(pathlib.Path(log_dir).glob("*.jsonl")):
        with open(path, encoding="utf-8", errors="replace") as f:
            for n, line in enumerate(f, 1):
                line = line.strip()
                if not line:
                    continue
                try:
                    ev = json.loads(line)
                except json.JSONDecodeError:
                    if warn:
                        print(f"warning: {path.name}:{n}: not JSON, skipped", file=sys.stderr)
                    continue
                if isinstance(ev, dict):
                    yield path, n, ev


def labeled_ids(events):
    return {ev["labels_for"] for ev in events if ev.get("type") == LABEL_TYPE and ev.get("labels_for")}


def is_candidate(ev):
    t = ev.get("type")
    if t not in CANDIDATE_TYPES or not ev.get("id"):
        return False
    if t == "prompt":
        return True
    return any(not ev.get(k) for k in ("intent", "situation", "meta"))


def truncate(s, n):
    if s is None:
        return None
    s = s if isinstance(s, str) else json.dumps(s, ensure_ascii=False)
    return s if len(s) <= n else s[:n] + f" …[+{len(s) - n} chars]"


def select_candidates(events, start, end, max_chars):
    """Unlabeled candidate events with ts in [start, end] (inclusive dates), with previous-prompt context."""
    done = labeled_ids(events)
    prev_prompt = {}  # session_id -> last prompt content seen (log order is chronological per file)
    out = []
    for ev in events:
        sid = ev.get("session_id")
        d = event_date(ev)
        if is_candidate(ev) and ev["id"] not in done and d is not None and start <= d <= end:
            out.append({
                "id": ev["id"],
                "ts": ev.get("ts"),
                "type": ev.get("type"),
                "scope_hint": ev.get("scope") or ev.get("scope_hint"),
                "session_id": sid,
                "content": truncate(ev.get("content"), max_chars),
                "prev_content": truncate(prev_prompt.get(sid), max_chars // 2) if sid else None,
            })
        if ev.get("type") == "prompt" and sid:
            prev_prompt[sid] = ev.get("content")
    return out


def export(args):
    root = data_dir(args.data_dir)
    log_dir = root / "log"
    if not log_dir.is_dir():
        print(f"error: no log directory at {log_dir}", file=sys.stderr)
        return 2
    end = args.to or dt.datetime.now(dt.timezone.utc).date()
    start = args.from_ or end - dt.timedelta(days=6)
    if start > end:
        print("error: --from is after --to", file=sys.stderr)
        return 2
    events = [ev for _, _, ev in iter_log(log_dir)]
    cands = select_candidates(events, start, end, args.max_chars)
    out_dir = pathlib.Path(args.out_dir).expanduser() if args.out_dir else root / "labels"
    out_dir.mkdir(parents=True, exist_ok=True)
    prompt_path = out_dir / "label_prompt.md"
    prompt_path.write_text(PROMPT + "\n", encoding="utf-8")
    if not cands:
        print(f"No unlabeled candidate events between {start} and {end}.")
        return 0
    chunks = [cands[i:i + args.chunk] for i in range(0, len(cands), args.chunk)]
    print(f"{len(cands)} unlabeled candidate events between {start} and {end} -> {len(chunks)} batch file(s).")
    print("Run each command (haiku, print mode), then apply the outputs:\n")
    outs = []
    for i, chunk in enumerate(chunks, 1):
        stem = f"batch_{start}_{end}" + (f"_part{i:02d}" if len(chunks) > 1 else "")
        batch = out_dir / f"{stem}.jsonl"
        result = out_dir / f"{stem}.labels.jsonl"
        with open(batch, "w", encoding="utf-8") as f:
            for c in chunk:
                f.write(json.dumps(c, ensure_ascii=False) + "\n")
        outs.append(result)
        print(f'claude -p --model haiku "$(cat {sh(prompt_path)})" < {sh(batch)} > {sh(result)}')
    print()
    for r in outs:
        print(f"python3 -I {sh(pathlib.Path(__file__).resolve())} --apply {sh(r)}"
              + (f" --data-dir {sh(root)}" if args.data_dir else ""))
    return 0


def sh(p):
    """Quote a path for a POSIX shell."""
    s = str(p)
    if s and all(c.isalnum() or c in "/._-+:@%=," for c in s):
        return s
    return "'" + s.replace("'", "'\"'\"'") + "'"


def parse_label_output(text):
    """Parse model output: JSON lines, a JSON array, or lines wrapped in ``` fences. Returns (records, bad)."""
    text = text.strip()
    if text.startswith("["):
        try:
            arr = json.loads(text)
            return [r for r in arr if isinstance(r, dict)], 0
        except json.JSONDecodeError:
            pass
    recs, bad = [], 0
    for line in text.splitlines():
        line = line.strip().rstrip(",")
        if not line or line.startswith("```"):
            continue
        try:
            r = json.loads(line)
        except json.JSONDecodeError:
            bad += 1
            continue
        if isinstance(r, dict):
            recs.append(r)
        else:
            bad += 1
    return recs, bad


def to_bool(v):
    if isinstance(v, bool):
        return v
    if isinstance(v, str) and v.strip().lower() in ("true", "yes", "1"):
        return True
    if isinstance(v, str) and v.strip().lower() in ("false", "no", "0", ""):
        return False
    if isinstance(v, (int, float)):
        return bool(v)
    return None


def clean_label(rec):
    """Validate one model record. Returns (target_id, fields) or (None, reason)."""
    target = rec.get("labels_for") or rec.get("id")
    if not isinstance(target, str) or not target:
        return None, "missing labels_for"
    fields = {}
    for k in ("intent", "situation"):
        v = rec.get(k)
        fields[k] = v.strip() if isinstance(v, str) and v.strip() else None
    meta = rec.get("meta")
    if isinstance(meta, dict):
        m = {k: meta.get(k) for k in META_KEYS if k in meta}
        g = m.get("generalizes_to")
        if isinstance(g, str):
            m["generalizes_to"] = [g]
        elif g is not None and not isinstance(g, list):
            m.pop("generalizes_to")
        fields["meta"] = m
    else:
        fields["meta"] = None
    labels = rec.get("labels")
    if isinstance(labels, str):
        labels = [labels]
    fields["labels"] = [str(x) for x in labels] if isinstance(labels, list) else []
    fields["is_correction"] = to_bool(rec.get("is_correction"))
    scope = rec.get("scope")
    fields["scope"] = scope if isinstance(scope, str) and scope else None
    if fields["intent"] is None and fields["meta"] is None and not fields["labels"]:
        return None, "no label content"
    return target, fields


def append_lines(path, lines):
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "a", encoding="utf-8") as f:
        if fcntl:
            fcntl.flock(f, fcntl.LOCK_EX)
        try:
            for line in lines:
                f.write(line + "\n")
            f.flush()
            os.fsync(f.fileno())
        finally:
            if fcntl:
                fcntl.flock(f, fcntl.LOCK_UN)


def apply(args):
    root = data_dir(args.data_dir)
    log_dir = root / "log"
    src = pathlib.Path(args.apply).expanduser()
    if not src.is_file():
        print(f"error: labels file not found: {src}", file=sys.stderr)
        return 2
    events = [ev for _, _, ev in iter_log(log_dir, warn=False)] if log_dir.is_dir() else []
    known = {ev.get("id"): ev for ev in events if ev.get("id")}
    done = labeled_ids(events)
    recs, bad = parse_label_output(src.read_text(encoding="utf-8", errors="replace"))

    now = dt.datetime.now(dt.timezone.utc)
    new, skipped, seen = [], [], set()
    for rec in recs:
        target, fields = clean_label(rec)
        if target is None:
            skipped.append(("?", fields))
            continue
        if target not in known:
            skipped.append((target, "unknown event id"))
            continue
        if known[target].get("type") == LABEL_TYPE:
            skipped.append((target, "is itself a label event"))
            continue
        if target in seen:
            skipped.append((target, "duplicate in this file"))
            continue
        if target in done and not args.force:
            skipped.append((target, "already labeled (use --force to add a newer label)"))
            continue
        seen.add(target)
        ev = {
            "id": f"evt_{now:%Y%m%d_%H%M%S}_{uuid.uuid4().hex[:4]}",
            "ts": now.isoformat(),
            "actor": "agent:librarian",
            "model": args.model,
            "type": LABEL_TYPE,
            "labels_for": target,
            "scope": fields.pop("scope") or known[target].get("scope"),
            **fields,
            "source_batch": str(src),
            "parent_event": target,
        }
        new.append(json.dumps(ev, ensure_ascii=False))

    print(f"parsed {len(recs)} records ({bad} unparseable lines); {len(new)} new label events; {len(skipped)} skipped")
    for tid, why in skipped[:50]:
        print(f"  skip {tid}: {why}")
    if not new:
        return 1 if recs or bad else 0
    out = log_dir / f"{now:%Y-%m}.jsonl"
    if args.dry_run:
        print(f"dry run: would append {len(new)} lines to {out}")
        return 0
    append_lines(out, new)
    print(f"appended {len(new)} label events to {out}")
    return 0


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__.split("\n\n")[0],
                                formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--data-dir", help="defaults to $HARNESS_DATA or ~/harness-data")
    p.add_argument("--from", dest="from_", type=parse_date, help="start date YYYY-MM-DD (default: --to minus 6 days, i.e. 7 days inclusive)")
    p.add_argument("--to", type=parse_date, help="end date YYYY-MM-DD, inclusive (default: today UTC)")
    p.add_argument("--out-dir", help="where batch files go (default: $HARNESS_DATA/labels)")
    p.add_argument("--chunk", type=int, default=150, help="events per batch file (default 150)")
    p.add_argument("--max-chars", type=int, default=2000, help="truncate content to this many chars")
    p.add_argument("--apply", metavar="LABELS_JSONL", help="merge model output as new label events")
    p.add_argument("--model", default="haiku", help="model recorded on applied label events")
    p.add_argument("--force", action="store_true", help="allow a newer label for an already-labeled event")
    p.add_argument("--dry-run", action="store_true", help="with --apply: report only, write nothing")
    args = p.parse_args(argv)
    if args.chunk < 1:
        p.error("--chunk must be >= 1")
    return apply(args) if args.apply else export(args)


if __name__ == "__main__":
    sys.exit(main())
