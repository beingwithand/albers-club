"""Shared helpers for the usage / compaction hooks. Loaded by path (hooks run with
`python3 -I`, so the hooks directory is not on sys.path):

    _common = _load_common()   # see the 6-line loader at the top of each hook

Everything here is defensive: callers wrap their main() in try/except and exit 0.
"""
import datetime as dt
import importlib.util
import json
import os
import pathlib
import subprocess
import time
import uuid

HERE = pathlib.Path(__file__).resolve().parent
GIT_TIMEOUT_S = 3


def read_payload(stream):
    try:
        raw = stream.read()
        data = json.loads(raw) if raw and raw.strip() else {}
    except ValueError:
        data = {}
    return data if isinstance(data, dict) else {}


def data_dir(env=None):
    env = os.environ if env is None else env
    return pathlib.Path(env.get("HARNESS_DATA") or (pathlib.Path.home() / "harness-data")).expanduser()


def state_path(env=None):
    env = os.environ if env is None else env
    p = env.get("HARNESS_STATE")
    return pathlib.Path(p).expanduser() if p else pathlib.Path.home() / ".claude" / "harness-state.json"


def load_json(path, default=None):
    try:
        with open(path, encoding="utf-8") as f:
            v = json.load(f)
        return v
    except (OSError, ValueError):
        return default


def write_json_atomic(path, obj):
    path = pathlib.Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(f".{path.name}.{os.getpid()}.tmp")
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(obj, f, ensure_ascii=False, separators=(",", ":"))
    os.replace(tmp, path)


def project_root(cwd):
    """Nearest directory at or above cwd holding PROGRESS.md or .git; None if none."""
    if not isinstance(cwd, str) or not cwd:
        return None
    p = pathlib.Path(cwd).expanduser()
    if not p.is_dir():
        return None
    home = pathlib.Path.home()
    for d in [p, *p.parents]:
        if d == home:  # never treat ~ itself (e.g. a dotfiles repo) or anything above as a project
            break
        if (d / "PROGRESS.md").is_file() or (d / ".git").exists():
            return d
    return None


def git(root, *args, timeout=GIT_TIMEOUT_S):
    """Run git in root; return stdout (stripped) or None on any failure/timeout."""
    try:
        p = subprocess.run(["git", "-C", str(root), *args], capture_output=True, text=True,
                           timeout=timeout, env=dict(os.environ, GIT_OPTIONAL_LOCKS="0", LC_ALL="C"))
    except (OSError, subprocess.SubprocessError):
        return None
    return p.stdout.rstrip("\n") if p.returncode == 0 else None


def age_str(seconds):
    s = int(max(0, seconds))
    if s < 3600:
        return f"{s // 60}m"
    if s < 86400:
        return f"{s // 3600}h{(s % 3600) // 60:02d}m"
    return f"{s // 86400}d{(s % 86400) // 3600}h"


def truncate(text, limit, pointer=None):
    if len(text) <= limit:
        return text
    note = f"\n…[truncated at {limit} chars" + (f"; full text: {pointer}]" if pointer else "]")
    return text[: max(0, limit - len(note))].rstrip() + note


def handoff_commit(text):
    """The git_commit recorded in a HANDOFF.md, if any (`git_commit: abc1234`)."""
    import re
    m = re.search(r"git_commit\W{0,4}\s*[:=]\s*`?([0-9a-f]{7,40})", text or "", re.I)
    return m.group(1) if m else None


def newest(paths):
    best = None
    for p in paths:
        try:
            m = p.stat().st_mtime
        except OSError:
            continue
        if best is None or m > best[1]:
            best = (p, m)
    return best


def _verify_gate():
    spec = importlib.util.spec_from_file_location("harness_verify_gate", HERE / "verify_gate.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def recent_events(log_dir, cwd_paths, types, limit=10, max_files=3):
    """Last `limit` events of the given types whose scope matches any of cwd_paths."""
    vg = _verify_gate()
    out = []
    files = sorted(pathlib.Path(log_dir).glob("*.jsonl"))[-max_files:]
    for f in files:
        try:
            fh = open(f, encoding="utf-8", errors="replace")
        except OSError:
            continue
        with fh:
            for line in fh:
                if not any(f'"{t}"' in line for t in types):
                    continue
                try:
                    ev = json.loads(line)
                except ValueError:
                    continue
                if not isinstance(ev, dict) or ev.get("type") not in types:
                    continue
                if any(vg.scope_matches(ev, c) for c in cwd_paths):
                    out.append(ev)
    out.sort(key=lambda e: vg.parse_ts(e.get("ts")) or 0)
    return out[-limit:]


def append_event(kind, payload, env=None, **fields):
    now = dt.datetime.now(dt.timezone.utc)
    log_dir = data_dir(env) / "log"
    log_dir.mkdir(parents=True, exist_ok=True)
    ev = {
        "id": f"evt_{now:%Y%m%d_%H%M%S}_{uuid.uuid4().hex[:8]}",
        "ts": now.isoformat(),
        "actor": "harness",
        "type": kind,
        "scope_hint": payload.get("cwd"),
        "session_id": payload.get("session_id"),
        "transcript_path": payload.get("transcript_path"),
        "labels": [],
        "intent": None,
        "meta": None,
    }
    ev.update(fields)
    locked_append(log_dir / f"{now:%Y-%m}.jsonl", json.dumps(ev, ensure_ascii=False) + "\n")
    return ev


def locked_append(path, line):
    """Append one line atomically w.r.t. other harness writers (parallel subagents/hooks)."""
    try:
        import fcntl
    except ImportError:  # non-POSIX: best effort
        fcntl = None
    with open(path, "a", encoding="utf-8") as f:
        if fcntl:
            fcntl.flock(f.fileno(), fcntl.LOCK_EX)
        try:
            f.write(line)
            f.flush()
        finally:
            if fcntl:
                fcntl.flock(f.fileno(), fcntl.LOCK_UN)


def now():
    return time.time()
