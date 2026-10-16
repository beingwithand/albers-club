"""PreCompact hook: write a recoverable snapshot before compaction summarizes the thread away.

Registered for PreCompact (matcher manual|auto). It NEVER blocks: blocking auto-compaction
skips it, and if compaction was recovering from a context-limit error the request fails.

Writes <project>/log/handoffs/auto_<UTC ts>.md (project = nearest dir at or above cwd with
PROGRESS.md or .git; nothing is written outside a project) containing:
  trigger, custom_instructions, transcript_path, session id
  git branch + short HEAD + `git status --porcelain` (3 s timeout per git call)
  latest HANDOFF.md path / age / whether HEAD moved since it was written
  PROGRESS.md tail
  last 10 decision / mishap events for this project from $HARNESS_DATA/log
Then appends a `precompact` event to $HARNESS_DATA/log/YYYY-MM.jsonl and prints a
systemMessage naming the snapshot. Keeps the newest 30 auto snapshots per project.

With argument `post` it is the PostCompact hook instead: it appends the compact_summary to
this session's newest auto snapshot (so you can audit what compaction kept), and logs a
`postcompact` event. PostCompact has no control, so this is record-keeping only.
"""
import datetime as dt
import importlib.util
import json
import os
import pathlib
import sys

_spec = importlib.util.spec_from_file_location("harness_common", pathlib.Path(__file__).resolve().parent / "_common.py")
C = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(C)

PROGRESS_TAIL_LINES = 40
PROGRESS_TAIL_CHARS = 3000
STATUS_MAX_LINES = 60
KEEP_SNAPSHOTS = 30
EVENT_TYPES = ("decision", "mishap")


def _one_line(v, limit=240):
    if v is None:
        return ""
    if not isinstance(v, str):
        v = json.dumps(v, ensure_ascii=False)
    v = " ".join(v.split())
    return v if len(v) <= limit else v[: limit - 1] + "…"


def git_section(root):
    if not (root / ".git").exists() and C.git(root, "rev-parse", "--git-dir") is None:
        return ["_Not a git repository._"], None
    branch = C.git(root, "rev-parse", "--abbrev-ref", "HEAD")
    head = C.git(root, "rev-parse", "--short", "HEAD")
    status = C.git(root, "status", "--porcelain")
    lines = [f"- branch: `{branch or '?'}`", f"- HEAD: `{head or '(no commits / git timed out)'}`"]
    if status is None:
        lines.append("- status: _unavailable (git error or 3 s timeout)_")
    elif not status.strip():
        lines.append("- status: clean")
    else:
        st = status.splitlines()
        more = f"\n… +{len(st) - STATUS_MAX_LINES} more" if len(st) > STATUS_MAX_LINES else ""
        lines.append(f"- status ({len(st)} changed):\n```\n" + "\n".join(st[:STATUS_MAX_LINES]) + more + "\n```")
    return lines, head


def handoff_section(root, head, now):
    p = root / "HANDOFF.md"
    if not p.is_file():
        return ["_No HANDOFF.md in the project root._"]
    age = now - p.stat().st_mtime
    out = [f"- `{p}` (modified {C.age_str(age)} ago)"]
    rec = C.handoff_commit(p.read_text(encoding="utf-8", errors="replace")[:4000])
    if rec and head and not (head.startswith(rec) or rec.startswith(head)):
        out.append(f"- ⚠ written at `{rec}`, HEAD is now `{head}`: re-verify before trusting it")
    elif rec:
        out.append(f"- written at `{rec}` (matches HEAD)")
    return out


def progress_tail(root):
    p = root / "PROGRESS.md"
    if not p.is_file():
        return "_No PROGRESS.md._"
    lines = p.read_text(encoding="utf-8", errors="replace").splitlines()
    tail = "\n".join(lines[-PROGRESS_TAIL_LINES:])
    if len(tail) > PROGRESS_TAIL_CHARS:
        tail = "…" + tail[-PROGRESS_TAIL_CHARS:]
    return f"`{p}` (last {min(len(lines), PROGRESS_TAIL_LINES)} of {len(lines)} lines)\n\n```markdown\n{tail}\n```"


def events_section(root, cwd, env):
    paths = {str(root)}
    if cwd:
        paths.add(cwd)
    evs = C.recent_events(C.data_dir(env) / "log", sorted(paths), EVENT_TYPES, limit=10)
    if not evs:
        return ["_No decision or mishap events logged for this project._"]
    out = []
    for e in evs:
        what = _one_line(e.get("content") or e.get("claim") or e.get("summary"))
        why = _one_line(e.get("justification"), 160)
        out.append(f"- {e.get('ts', '?')[:16]} **{e.get('type')}** `{e.get('id', '?')}`: {what}"
                   + (f" (why: {why})" if why else ""))
    return out


def prune(handoffs):
    snaps = sorted(handoffs.glob("auto_*.md"))
    for old in snaps[:-KEEP_SNAPSHOTS]:
        try:
            old.unlink()
        except OSError:
            pass


def snapshot(payload, env, now):
    """Write the snapshot; return its path (or None outside a project)."""
    cwd = payload.get("cwd") if isinstance(payload.get("cwd"), str) else None
    root = C.project_root(cwd)
    if root is None:
        return None
    stamp = dt.datetime.fromtimestamp(now, dt.timezone.utc)
    handoffs = root / "log" / "handoffs"
    handoffs.mkdir(parents=True, exist_ok=True)
    path = handoffs / f"auto_{stamp:%Y%m%d_%H%M%S}.md"
    if path.exists():
        path = handoffs / f"auto_{stamp:%Y%m%d_%H%M%S}_{os.getpid()}.md"
    git_lines, head = git_section(root)
    custom = payload.get("custom_instructions")
    body = [
        f"# Auto snapshot before compaction ({stamp:%Y-%m-%d %H:%M:%S} UTC)",
        "",
        "Written by hooks/precompact_snapshot.py. This is raw state, not a curated handoff: "
        "prefer HANDOFF.md when it is fresh, and verify everything here against the files.",
        "",
        f"- trigger: `{payload.get('trigger') or '?'}`",
        f"- custom_instructions: {('`' + _one_line(custom, 600) + '`') if custom else '_none_'}",
        f"- session_id: `{payload.get('session_id') or '?'}`",
        f"- transcript_path: `{payload.get('transcript_path') or '?'}`",
        f"- cwd: `{cwd}`  project: `{root}`",
        "",
        "## Git",
        *git_lines,
        "",
        "## Latest handoff",
        *handoff_section(root, head, now),
        "",
        "## PROGRESS.md tail",
        progress_tail(root),
        "",
        "## Recent decisions and mishaps (newest last)",
        *events_section(root, cwd, env),
        "",
    ]
    path.write_text("\n".join(body), encoding="utf-8")
    prune(handoffs)
    return path


def post(payload, env, now):
    """PostCompact: attach the compact summary to this session's newest snapshot."""
    summary = payload.get("compact_summary")
    root = C.project_root(payload.get("cwd"))
    target = None
    if root is not None and isinstance(summary, str) and summary.strip():
        handoffs = root / "log" / "handoffs"
        best = C.newest(handoffs.glob("auto_*.md")) if handoffs.is_dir() else None
        sid = payload.get("session_id") or ""
        if best and now - best[1] < 3600 and (not sid or sid in best[0].read_text(encoding="utf-8", errors="replace")):
            target = best[0]
            with open(target, "a", encoding="utf-8") as f:
                f.write("\n## Compact summary (from PostCompact)\n\n" + summary.strip() + "\n")
    C.append_event("postcompact", payload, env, trigger=payload.get("trigger"),
                   pointers=[str(target)] if target else [],
                   content=C.truncate(summary, 2000) if isinstance(summary, str) else None)
    return target


def main():
    mode = sys.argv[1] if len(sys.argv) > 1 else "pre"
    try:
        payload = C.read_payload(sys.stdin)
        env, now = os.environ, C.now()
        if mode == "post":
            post(payload, env, now)
            return 0
        path = None
        try:
            path = snapshot(payload, env, now)
        finally:
            C.append_event("precompact", payload, env, trigger=payload.get("trigger"),
                           custom_instructions=payload.get("custom_instructions"),
                           pointers=[str(path)] if path else [])
        if path:
            sys.stdout.write(json.dumps({"systemMessage": f"Pre-compaction snapshot: {path}"}, ensure_ascii=False))
    except Exception:
        pass
    return 0


if __name__ == "__main__":
    sys.exit(main())
