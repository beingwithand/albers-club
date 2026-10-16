"""SessionStart + FileChanged hook: notice new inbox documents and new harness components, and queue the pipeline.

SessionStart (any source):
  - returns hookSpecificOutput.watchPaths = [<project>/inbox] (if it exists) plus, when the session runs inside
    a harness checkout (.claude-plugin/plugin.json name "harness", or $HARNESS_DEV_ROOT), its skills/, agents/,
    hooks/ and scripts/ dirs, so FileChanged fires for them;
  - scans <project>/inbox now (files not yet in knowledge/manifest.json and not queued -> queued +
    `inbox_file_detected`), which also catches files that landed while no session or watcher ran;
  - surfaces pending queue items (including ones the launchd watcher queued) and stale pipeline runs as
    additionalContext, and autostarts the `intake` pipeline per pending inbox file (cap 5).
FileChanged:
  - a file added/changed under <project>/inbox/ -> queue entry + `inbox_file_detected` event + autostart
    `intake` (param file) + context "new document: run /intake <file>";
  - a skill/agent/hook/script in a harness checkout: NEW (not in docs/components.json) -> `component_detected`
    (change: new) + autostart `new-component` (param component); CHANGED -> `component_detected`
    (change: changed) + queue a self-eval suggestion (once per file per day), no autostart;
  - deletions are ignored.

Payload assumptions (VERIFY ON MAC; hooks reference fields were not fully confirmed, see
research_notes/.../official_claude_code_features.md "UNCONFIRMED"):
  - the event name is `hook_event_name` ("SessionStart" / "FileChanged"); argv[1] ("session_start" /
    "file_changed") overrides it;
  - FileChanged carries the path in `file_path` (also accepted: `path`, `filePath`, `file`, `changed_path`,
    `paths[]`, `files[]`) and the change kind in `event` / `change_type` / `changeType` / `kind`
    ("add" | "change" | "unlink" or similar);
  - SessionStart may return `watchPaths` (absolute paths). If directories are not watched recursively, the
    SessionStart scan + the launchd watcher still catch new files; if FileChanged cannot add context, the
    queue entry is surfaced by hooks/pipeline_router.py on the next prompt.
Off switches: HARNESS_WATCH_INBOX=0 (whole hook), HARNESS_PIPELINE_AUTOSTART=0 (queue + notify, never start).
Never blocks, never crashes (any error -> exit 0).
"""
import importlib.util
import json
import os
import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parent
OFF = ("0", "false", "off", "no")
COMPONENT_DIRS = ("skills", "agents", "hooks", "scripts")
MAX_AUTOSTART = 5
MAX_SHOWN = 8
PATH_KEYS = ("file_path", "path", "filePath", "file", "changed_path")
KIND_KEYS = ("event", "change_type", "changeType", "kind", "type")
DELETE_WORDS = ("unlink", "delete", "deleted", "remove", "removed", "rename_from")


def _pipeline():
    spec = importlib.util.spec_from_file_location("harness_pipeline_w", HERE.parent / "scripts" / "pipeline.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def event_name(payload, argv):
    if len(argv) > 1:
        a = argv[1].lower().replace("-", "_")
        if a in ("session_start", "sessionstart"):
            return "SessionStart"
        if a in ("file_changed", "filechanged"):
            return "FileChanged"
    return str(payload.get("hook_event_name") or "")


def changed_paths(payload):
    out = []
    for k in PATH_KEYS:
        v = payload.get(k)
        if isinstance(v, str) and v:
            out.append(v)
    for k in ("paths", "files"):
        v = payload.get(k)
        if isinstance(v, list):
            out += [x if isinstance(x, str) else (x or {}).get("path") or (x or {}).get("file_path") for x in v]
    ti = payload.get("tool_input")
    if isinstance(ti, dict) and isinstance(ti.get("file_path"), str):
        out.append(ti["file_path"])
    cwd = payload.get("cwd") if isinstance(payload.get("cwd"), str) else None
    res = []
    for p in out:
        if not isinstance(p, str) or not p:
            continue
        if not os.path.isabs(p) and cwd:
            p = os.path.join(cwd, p)
        res.append(os.path.normpath(p))
    return list(dict.fromkeys(res))


def change_kind(payload):
    for k in KIND_KEYS:
        v = payload.get(k)
        if isinstance(v, str) and v and v != "FileChanged":
            return v.lower()
    return "change"


def harness_roots(P, cwd, env):
    roots = []
    hr = P.harness_root_of(cwd) if cwd else None
    if hr:
        roots.append(hr)
    dev = env.get("HARNESS_DEV_ROOT")
    if dev:
        d = pathlib.Path(dev).expanduser()
        if (d / ".claude-plugin" / "plugin.json").is_file() and d not in roots:
            roots.append(d)
    return roots


def known_component_paths(root):
    try:
        nodes = json.loads((root / "docs" / "components.json").read_text(encoding="utf-8")).get("nodes") or []
        return {n.get("path") for n in nodes if isinstance(n, dict)}
    except (OSError, ValueError, AttributeError):
        return set()


def autostart_on(env):
    return env.get("HARNESS_PIPELINE_AUTOSTART", "1").strip().lower() not in OFF


def inbox_project(path):
    """<project> for <project>/inbox/.../file, else None."""
    p = pathlib.Path(path)
    parts = p.parts
    if "inbox" not in parts[:-1]:
        return None
    i = len(parts) - 2 - list(reversed(parts[:-1])).index("inbox")
    return pathlib.Path(*parts[:i]) if i > 0 else None


def on_session_start(payload, env, P):
    cwd = payload.get("cwd") if isinstance(payload.get("cwd"), str) and payload.get("cwd") else os.getcwd()
    root = P.project_root(cwd)
    watch, notes = [], []
    if (root / "inbox").is_dir():
        watch.append(str(root / "inbox"))
        P.scan_inbox(root, env, source="hook:session_start")
    for hr in harness_roots(P, cwd, env):
        watch += [str(hr / d) for d in COMPONENT_DIRS if (hr / d).is_dir()]
    cfg = P.load_config(env)
    pending = P.pending_queue(env, root)
    started = []
    if autostart_on(env) and cfg["pipelines"].get("intake", {}).get("autostart") == "on_event":
        for q in [q for q in pending if q.get("kind") == "inbox_file"][:MAX_AUTOSTART]:
            run, created = P.start("intake", str(root), {"file": q["path"]}, env, source="hook:session_start", cfg=cfg)
            if created:
                started.append((run["run_id"], q["path"]))
    if pending:
        lines = [f"- {q['kind']}: {q['path']} (queued {q.get('ts', '')[:16]} by {q.get('source')})" for q in pending[:MAX_SHOWN]]
        if len(pending) > MAX_SHOWN:
            lines.append(f"- … +{len(pending) - MAX_SHOWN} more")
        notes.append("[harness pipelines] Pending queue items for this project (process them before unrelated work "
                     "unless the user says otherwise):\n" + "\n".join(lines))
    if started:
        notes.append("[harness pipelines] Started `intake` for: " + "; ".join(f"{p} ({r})" for r, p in started)
                     + ". Run /intake <file> for each; the Stop gate enforces register → convert → wiki → index → "
                       "manifest → verify → archive.")
    if P.state_file(root).is_file():
        stale = [s for s in P.check(str(root), env=env, cfg=cfg) if s.get("stale")]
        if stale:
            notes.append("[harness pipelines] Stale runs (no longer blocking): "
                         + "; ".join(f"{s['pipeline']} {s['run_id']} started {s.get('started_at', '')[:10]}" for s in stale)
                         + ". Finish them or abandon with the user's OK.")
    out = {"hookEventName": "SessionStart"}
    if watch:
        out["watchPaths"] = list(dict.fromkeys(watch))
    if notes:
        out["additionalContext"] = "\n\n".join(notes)
    return {"hookSpecificOutput": out} if len(out) > 1 else None


def on_file_changed(payload, env, P):
    kind = change_kind(payload)
    if any(w in kind for w in DELETE_WORDS):
        return None
    cfg = P.load_config(env)
    notes, sysmsg = [], []
    for path in changed_paths(payload):
        name = os.path.basename(path)
        if name.startswith(".") or not os.path.isfile(path):
            continue
        proj = inbox_project(path)
        if proj is not None:
            root = P.project_root(str(proj))
            if name in P.manifest_names(root):
                continue
            e = P.enqueue("inbox_file", path, root, env, source="hook:file_changed")
            msg = f"new document: run /intake {path}"
            if autostart_on(env) and cfg["pipelines"].get("intake", {}).get("autostart") == "on_event":
                run, created = P.start("intake", str(root), {"file": path}, env, source="hook:file_changed", cfg=cfg)
                if created:
                    msg += f" (pipeline `intake` run {run['run_id']} started; the Stop gate enforces its steps)"
            if e or msg:
                notes.append("[harness pipelines] " + msg)
                sysmsg.append(f"Inbox: {name} queued for /intake")
            continue
        hr = P.harness_root_of(path)
        if hr is None:
            continue
        try:
            rel = pathlib.Path(path).resolve().relative_to(hr.resolve()).as_posix()
        except ValueError:
            continue
        cid = P.component_id(rel)
        if not cid:
            continue
        is_new = rel not in known_component_paths(hr)
        if is_new:
            e = P.enqueue("component_new", path, hr, env, source="hook:file_changed", change="new", component=cid)
            msg = f"new harness component {cid} ({rel}): run /integrate {rel}"
            if autostart_on(env) and cfg["pipelines"].get("new-component", {}).get("autostart") == "on_event":
                run, created = P.start("new-component", str(hr), {"component": rel}, env,
                                       source="hook:file_changed", cfg=cfg)
                if created:
                    msg += f" (pipeline `new-component` run {run['run_id']} started)"
            notes.append("[harness pipelines] " + msg)
            sysmsg.append(f"New component {cid}: integration checklist queued")
        else:
            # one unacked entry per file (enqueue dedupes), so a burst of edits queues it once
            if P.enqueue("component_changed", path, hr, env, source="hook:file_changed", change="changed", component=cid):
                notes.append(f"[harness pipelines] changed harness component {cid}: before merging, run "
                             f"self-eval --changed {rel} (and /integrate {rel} if its contract, rubric or pipeline changed)")
    if not notes:
        return None
    # FileChanged may not support additionalContext (unconfirmed); the queue entry is the durable channel and
    # hooks/pipeline_router.py surfaces it on the next prompt either way.
    return {"hookSpecificOutput": {"hookEventName": "FileChanged", "additionalContext": "\n".join(notes)},
            "systemMessage": "; ".join(sysmsg) if sysmsg else None}


def main(argv=None):
    argv = sys.argv if argv is None else argv
    try:
        if os.environ.get("HARNESS_WATCH_INBOX", "1").strip().lower() in OFF:
            return 0
        raw = sys.stdin.read()
        payload = json.loads(raw) if raw.strip() else {}
        if not isinstance(payload, dict):
            return 0
        P = _pipeline()
        name = event_name(payload, argv)
        out = None
        if name == "SessionStart":
            out = on_session_start(payload, os.environ, P)
        elif name == "FileChanged":
            out = on_file_changed(payload, os.environ, P)
        if out:
            if out.get("systemMessage") is None:
                out.pop("systemMessage", None)
            sys.stdout.write(json.dumps(out, ensure_ascii=False))
    except Exception:
        pass
    return 0


if __name__ == "__main__":
    sys.exit(main())
