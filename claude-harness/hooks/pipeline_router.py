"""UserPromptSubmit hook: route the prompt to a pipeline and keep the active run in view. Never blocks.

For each (non-trivial) prompt it adds, as hookSpecificOutput.additionalContext:
  1. Pending queue items for this project ($HARNESS_DATA/queue/inbox.jsonl: inbox files from the launchd
     watcher or the FileChanged hook, new/changed harness components), each surfaced once per session.
  2. Context >= the usage guard's ctx_stop (200k) for this session: autostarts the `context-handoff` pipeline
     (unless HARNESS_PIPELINE_AUTOSTART=0) so the Stop gate enforces the handoff.
  3. Active runs: one line each with the next required step.
  4. Otherwise `pipeline.py match` on the prompt; when it is confident (no abstain):
     "This looks like <pipeline>; run these steps in order: ..." plus the `start` command.
     It does not start task pipelines itself; the orchestrator does (agents/orchestrator.md "Pipelines").

Quiet on trivial prompts (greetings, "ok", < 12 chars) and on prompts that are themselves pipeline.py
commands. Off switch: HARNESS_PIPELINE_ROUTER=0. Never crashes: any error means exit 0 with no output.
"""
import importlib.util
import json
import os
import pathlib
import re
import sys

HERE = pathlib.Path(__file__).resolve().parent
OFF = ("0", "false", "off", "no")
MAX_CHARS = 2500
MAX_QUEUE_SHOWN = 5
MAX_SESSIONS = 50


def _load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def _surfaced_path(P, env):
    return P.queue_dir(env) / "surfaced.json"


def _take_unsurfaced(P, env, sid, items):
    path = _surfaced_path(P, env)
    try:
        mem = json.loads(path.read_text(encoding="utf-8"))
        if not isinstance(mem, dict):
            mem = {}
    except (OSError, ValueError):
        mem = {}
    seen = set(mem.get(sid or "-", []))
    fresh = [q for q in items if q.get("id") not in seen]
    if fresh:
        mem[sid or "-"] = sorted(seen | {q["id"] for q in fresh})
        if len(mem) > MAX_SESSIONS:
            for k in list(mem)[:len(mem) - MAX_SESSIONS]:
                mem.pop(k, None)
        try:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(json.dumps(mem), encoding="utf-8")
        except OSError:
            pass
    return fresh


def _context_tokens(payload, env):
    try:
        U = _load("harness_usage_guard_r", HERE / "usage_guard.py")
        C = U.C
        state = C.load_json(C.state_path(env), {}) or {}
        sid = payload.get("session_id") if isinstance(payload.get("session_id"), str) else None
        ctx = U.session_ctx(state, sid, C.now(), U._max_age(env))
        stop = U._num(state.get("ctx_stop")) or U.DEFAULT_STOP
        return ctx, stop
    except Exception:
        return None, None


def build(payload, env):
    if env.get("HARNESS_PIPELINE_ROUTER", "1").strip().lower() in OFF:
        return None
    prompt = payload.get("prompt") if isinstance(payload.get("prompt"), str) else ""
    text = prompt.strip()
    P = _load("harness_pipeline_r", HERE.parent / "scripts" / "pipeline.py")
    if len(text) < P.TRIVIAL_LEN or P.TRIVIAL.match(text) or re.search(r"\bpipeline\.py\b", text):
        return None
    cwd = payload.get("cwd") if isinstance(payload.get("cwd"), str) and payload.get("cwd") else os.getcwd()
    root = P.project_root(cwd)
    cfg = P.load_config(env)
    script = HERE.parent / "scripts" / "pipeline.py"
    parts = []

    pending = P.pending_queue(env, root)
    fresh = _take_unsurfaced(P, env, payload.get("session_id"), pending)
    if fresh:
        lines = []
        for q in fresh[:MAX_QUEUE_SHOWN]:
            if q.get("kind") == "inbox_file":
                lines.append(f"- new document: run /intake {q['path']}  (queue {q['id']}, from {q.get('source')})")
            elif q.get("kind") == "component_new":
                lines.append(f"- new harness component {q.get('component') or q['path']}: run /integrate {q['path']}")
            else:
                lines.append(f"- changed harness component {q.get('component') or q['path']}: run self-eval --changed {q['path']}")
        extra = f"\n- … +{len(fresh) - MAX_QUEUE_SHOWN} more (`python3 -I {script} queue list --scope {root}`)" if len(fresh) > MAX_QUEUE_SHOWN else ""
        parts.append("[harness pipelines] Pending queue items for this project:\n" + "\n".join(lines) + extra)

    ctx, stop = _context_tokens(payload, env)
    autostart = env.get("HARNESS_PIPELINE_AUTOSTART", "1").strip().lower() not in OFF
    if ctx is not None and stop and ctx >= stop and "context-handoff" in cfg["pipelines"] and autostart \
            and (root / "PROGRESS.md").is_file():
        run, created = P.start("context-handoff", str(root), {}, env, source="hook:pipeline_router", cfg=cfg)
        if created:
            parts.append(f"[harness pipelines] Context is ~{ctx / 1000:.0f}k ≥ {stop / 1000:.0f}k: started pipeline "
                         f"`context-handoff` ({run['run_id']}). Finish the current atomic step, update PROGRESS.md, "
                         "then /handoff; the Stop gate enforces it.")

    runs = P.check(str(root), env=env, cfg=cfg) if P.state_file(root).is_file() else []
    if runs:
        lines = []
        for s in runs:
            if s.get("stale"):
                lines.append(f"- STALE `{s['pipeline']}` run {s['run_id']} (started {s.get('started_at')}): finish it, or "
                             f"abandon with the user's OK (`pipeline.py abandon --run {s['run_id']} --reason ...`).")
            elif s["ok"]:
                lines.append(f"- `{s['pipeline']}` run {s['run_id']}: all required steps have evidence; run "
                             f"`python3 -I {script} finish --scope {root} --run {s['run_id']}`.")
            else:
                n = s.get("next") or {}
                lines.append(f"- `{s['pipeline']}` run {s['run_id']}: next **{n.get('step')}** → `{n.get('run')}`; "
                             f"missing: {', '.join(s['missing'])}.")
        parts.append("[harness pipelines] Active runs here (Stop gate enforces required steps):\n" + "\n".join(lines))
    else:
        m = P.match(text, cfg, env)
        if m.get("pipeline"):
            pid = m["pipeline"]
            pipe = cfg["pipelines"][pid]
            steps = "; ".join(f"{i}. {s['id']} ({s.get('run')}){'' if s.get('required') else ' [optional]'}"
                              for i, s in enumerate(pipe.get("steps", []), 1))
            params = " ".join(f"--param {p}=<{p}>" for p in pipe.get("params") or [])
            parts.append(f"[harness pipelines] This looks like `{pid}` ({pipe.get('title')}; confidence "
                         f"{m['confidence']}, rule: {m['reason'][:160]}); run these steps in order: {steps}. "
                         f"If this is right, start tracking it first: `python3 -I {script} start {pid} --scope {root}"
                         f"{(' ' + params) if params else ''}` (the Stop gate then enforces the required steps). "
                         "If it is not, ignore this note.")
    if not parts:
        return None
    out = "\n\n".join(parts)
    return out if len(out) <= MAX_CHARS else out[:MAX_CHARS - 20] + "\n…[truncated]"


def main():
    try:
        raw = sys.stdin.read()
        payload = json.loads(raw) if raw.strip() else {}
        if not isinstance(payload, dict):
            return 0
        ctx = build(payload, os.environ)
        if ctx:
            sys.stdout.write(json.dumps({"hookSpecificOutput": {"hookEventName": "UserPromptSubmit",
                                                                "additionalContext": ctx}}, ensure_ascii=False))
    except Exception:
        pass
    return 0


if __name__ == "__main__":
    sys.exit(main())
