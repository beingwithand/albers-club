"""Stop hook: don't let a turn end while done items lack a verification event.

Reads the Stop hook JSON on stdin (cwd, session_id, transcript_path, stop_hook_active).
If `PROGRESS.md` or `tasks.json` in cwd marks items done after the last non-failing
`verification` event for this project in $HARNESS_DATA/log/*.jsonl, it prints
{"decision": "block", "reason": "..."} so Claude runs the verify skill first.

- Loop guard: when `stop_hook_active` is true (Claude is already continuing because of a
  Stop hook) it allows the stop. Pattern from OthmanAdi/planning-with-files (MIT),
  reimplemented.
- Off switch: HARNESS_VERIFY_GATE=0.
- Grace: done marks up to HARNESS_VERIFY_GRACE_S seconds (default 600) after a passing
  verification count as covered, so "verify, then tick the box" does not re-trigger.
- Never crashes: any error means exit 0 (allow stop).

Item timestamps: tasks.json items may carry done_at / completed_at / updated_at; otherwise
the file's mtime is used. A verification event may list `items` it covered; done items
whose text matches one of those are treated as verified regardless of time.
Events labeled `step_check` (hooks/step_check.py syntax checks) never count as verification.
"""
import datetime as dt
import json
import os
import pathlib
import re
import sys

DONE_WORDS = {"done", "complete", "completed", "passed", "pass", "finished", "verified-pending"}
ITEM_TS_KEYS = ("done_at", "completed_at", "updated_at", "ts")
NAME_KEYS = ("id", "name", "title", "task", "description", "content")
MAX_LOG_FILES = 3
MAX_LISTED = 8
STEP_CHECK_LABEL = "step_check"


def parse_ts(value):
    if isinstance(value, (int, float)):
        return float(value)
    if not isinstance(value, str) or not value:
        return None
    try:
        d = dt.datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None
    if d.tzinfo is None:
        d = d.replace(tzinfo=dt.timezone.utc)
    return d.timestamp()


# ---------- done items ----------

CHECKBOX = re.compile(r"^\s*[-*+]\s*\[[xX]\]\s*(.+)$")
STATUS = re.compile(r"\b(?:status|state)\s*[:=]\s*\**\s*(?:done|complete|completed|passed)\b", re.I)
HEADING = re.compile(r"^\s*#{1,6}\s*(.+?)\s*$")
BULLET = re.compile(r"^\s*[-*+]\s+(?!\[[ ]\])(.+)$")
DONE_HEADING = re.compile(r"^(?:done|completed?|finished)\s*(?:[:(\-].*)?$", re.I)


def progress_done_items(path):
    items = []
    in_done = False
    for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
        h = HEADING.match(line)
        if h:
            in_done = bool(DONE_HEADING.match(h.group(1)))
            continue
        m = CHECKBOX.match(line)
        if m:
            items.append(m.group(1).strip())
        elif STATUS.search(line) or "✅" in line:
            items.append(line.strip(" -*+\t"))
        elif in_done:
            b = BULLET.match(line)
            if b:
                items.append(b.group(1).strip())
    return items


def _is_done(item):
    if item.get("passes") is True or item.get("done") is True or item.get("completed") is True:
        return True
    for key in ("status", "state"):
        v = item.get(key)
        if isinstance(v, str) and v.strip().lower() in DONE_WORDS:
            return True
    return False


def tasks_done_items(path):
    data = json.loads(path.read_text(encoding="utf-8", errors="replace"))
    if isinstance(data, dict):
        for key in ("tasks", "items", "features", "todos"):
            if isinstance(data.get(key), list):
                data = data[key]
                break
        else:
            data = [dict(v, id=v.get("id", k)) for k, v in data.items() if isinstance(v, dict)]
    out = []
    if not isinstance(data, list):
        return out
    for i, item in enumerate(data):
        if not isinstance(item, dict) or not _is_done(item):
            continue
        name = next((str(item[k]) for k in NAME_KEYS if item.get(k) not in (None, "")), f"item {i + 1}")
        ts = next((parse_ts(item.get(k)) for k in ITEM_TS_KEYS if parse_ts(item.get(k)) is not None), None)
        out.append((name, ts))
    return out


def collect_done(cwd):
    """List of (label, timestamp) for every item marked done in cwd."""
    found = []
    progress = cwd / "PROGRESS.md"
    if progress.is_file():
        mtime = progress.stat().st_mtime
        found += [(f"PROGRESS.md: {t}", mtime, t) for t in progress_done_items(progress)]
    tasks = cwd / "tasks.json"
    if tasks.is_file():
        mtime = tasks.stat().st_mtime
        try:
            for name, ts in tasks_done_items(tasks):
                found.append((f"tasks.json: {name}", ts if ts is not None else mtime, name))
        except (ValueError, TypeError, AttributeError):
            pass
    return found


# ---------- verification events ----------

def _norm(p):
    try:
        return os.path.normpath(os.path.expanduser(str(p)))
    except Exception:
        return None


def scope_matches(ev, cwd):
    cwd_s = _norm(cwd)
    for key in ("cwd", "scope_hint", "project_dir"):
        v = ev.get(key)
        if isinstance(v, str) and v and _norm(v) == cwd_s:
            return True
    scope = ev.get("scope")
    if isinstance(scope, str) and scope and scope != "global":
        s = scope.strip("/")
        if os.path.isabs(scope):
            return _norm(scope) == cwd_s
        if cwd_s.endswith("/" + s) or cwd_s == s:
            return True
        parts = pathlib.PurePath(cwd_s).parts
        if s.split("/")[-1] == parts[-1] or (len(parts) > 1 and s.split("/")[-1] == parts[-2]):
            return True  # <area>/<project> scope with cwd at project root or one level below
    for p in ev.get("pointers") or []:
        if isinstance(p, str) and _norm(p) and (_norm(p) == cwd_s or _norm(p).startswith(cwd_s + os.sep)):
            return True
    return False


def last_verification(log_dir, cwd):
    """Return (timestamp, covered_item_texts) of the newest non-failing verification for cwd."""
    files = sorted(log_dir.glob("*.jsonl"))[-MAX_LOG_FILES:]
    best, covered = None, set()
    for f in files:
        try:
            fh = open(f, encoding="utf-8", errors="replace")
        except OSError:
            continue
        with fh:
            for line in fh:
                if '"verification"' not in line:
                    continue
                try:
                    ev = json.loads(line)
                except ValueError:
                    continue
                if not isinstance(ev, dict) or ev.get("type") != "verification":
                    continue
                if str(ev.get("verdict", "")).lower() == "fail" or not scope_matches(ev, cwd):
                    continue
                if STEP_CHECK_LABEL in (ev.get("labels") or []):
                    continue  # hooks/step_check.py syntax checks are not verification of the work
                ts = parse_ts(ev.get("ts"))
                if ts is None:
                    continue
                for it in ev.get("items") or []:
                    if isinstance(it, str) and it.strip():
                        covered.add(it.strip().lower())
                if best is None or ts > best:
                    best = ts
    return best, covered


def check(payload, env):
    if env.get("HARNESS_VERIFY_GATE", "1").strip().lower() in ("0", "false", "off", "no"):
        return None
    if not isinstance(payload, dict) or str(payload.get("stop_hook_active")).lower() == "true":
        return None
    cwd = payload.get("cwd")
    if not isinstance(cwd, str) or not cwd:
        return None
    cwd = pathlib.Path(cwd)
    if not cwd.is_dir():
        return None
    done = collect_done(cwd)
    if not done:
        return None
    data_dir = pathlib.Path(env.get("HARNESS_DATA") or (pathlib.Path.home() / "harness-data"))
    last_ts, covered = last_verification(data_dir / "log", cwd)
    try:
        grace = float(env.get("HARNESS_VERIFY_GRACE_S", "600"))
    except ValueError:
        grace = 600.0
    pending = []
    for label, ts, text in done:
        if any(c and (c in text.lower() or text.lower() in c) for c in covered):
            continue
        if last_ts is None or ts > last_ts + grace:
            pending.append(label)
    if not pending:
        return None
    shown = pending[:MAX_LISTED]
    more = f" (+{len(pending) - len(shown)} more)" if len(pending) > len(shown) else ""
    when = "no verification event for this project" if last_ts is None else "they were marked done after the last verification"
    return ("Verification gate: these items are marked done but " + when + ": "
            + "; ".join(shown) + more
            + ". Run the verify skill on them (it appends a `verification` event to the log), "
            "or un-mark them if they are not actually done. Set HARNESS_VERIFY_GATE=0 to disable.")


def main():
    try:
        raw = sys.stdin.read()
        payload = json.loads(raw) if raw.strip() else {}
        reason = check(payload, os.environ)
        if reason:
            sys.stdout.write(json.dumps({"decision": "block", "reason": reason}, ensure_ascii=False))
    except Exception:
        pass
    return 0


if __name__ == "__main__":
    sys.exit(main())
