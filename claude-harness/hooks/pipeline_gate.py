"""Stop hook: don't let a turn end while an active pipeline run misses a REQUIRED step.

Reads the Stop payload (cwd, session_id, stop_hook_active, agent_id). For every active run in
<project>/.harness/pipeline_state.json (scripts/pipeline.py), it evaluates the required steps against
their evidence (log events since the run started, project files, stores, builtin checks; see
pipelines/pipelines.yaml and docs/PIPELINES.md). If any is missing it prints
  {"decision": "block", "reason": "..."}
listing the missing steps and the exact next step to run, with its pre/postcondition.

- Loop guard: when `stop_hook_active` is true (Claude is already continuing because of a Stop hook) it
  allows the stop, so the gate nudges once per turn and can never trap a session.
- Subagents: a payload carrying `agent_id` is a subagent's stop; it is allowed (only the main thread
  owns a pipeline run).
- Stale runs (older than defaults.stale_days) never block; the router and SessionStart report them.
- A run whose pipeline sets strict_order also blocks on order violations.
- Off switch: HARNESS_PIPELINE_GATE=0. Never crashes: any error means exit 0 (allow stop).
"""
import importlib.util
import json
import os
import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parent
OFF = ("0", "false", "off", "no")
MAX_RUNS_LISTED = 3


def _pipeline():
    spec = importlib.util.spec_from_file_location("harness_pipeline", HERE.parent / "scripts" / "pipeline.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def build_reason(payload, env):
    if env.get("HARNESS_PIPELINE_GATE", "1").strip().lower() in OFF:
        return None
    if not isinstance(payload, dict) or str(payload.get("stop_hook_active")).lower() == "true":
        return None
    if payload.get("agent_id"):
        return None
    cwd = payload.get("cwd")
    if not isinstance(cwd, str) or not cwd or not os.path.isdir(cwd):
        return None
    P = _pipeline()
    root = P.project_root(cwd)
    if not P.state_file(root).is_file():
        return None
    cfg = P.load_config(env)
    results = [s for s in P.check(str(root), env=env, cfg=cfg, include_stale=False) if not s["ok"]]
    if not results:
        return None
    script = HERE.parent / "scripts" / "pipeline.py"
    parts = []
    for s in results[:MAX_RUNS_LISTED]:
        line = f"`{s['pipeline']}` run {s['run_id']} ({s.get('title') or ''}) is missing required step(s): {', '.join(s['missing']) or 'none'}"
        if s["strict_order"] and s["order_violations"]:
            line += f"; strict order violated: {'; '.join(s['order_violations'])}"
        n = s.get("next")
        if n:
            line += (f". Next: **{n['step']}** → run `{n['run']}`"
                     + (f" (pre: {'; '.join(map(str, n.get('pre') or []))}" if n.get("pre") else "")
                     + (f"; post: {'; '.join(map(str, n.get('post') or []))})" if n.get("post") else (")" if n.get("pre") else ""))
                     + (f"; protocol: {n['verification']}" if n.get("verification") else ""))
        parts.append(line)
    more = f" (+{len(results) - MAX_RUNS_LISTED} more runs)" if len(results) > MAX_RUNS_LISTED else ""
    return ("Pipeline gate: " + " | ".join(parts) + more
            + f". Do the step (its evidence is checked automatically), or bind a logged event to it with "
            f"`python3 -I {script} mark <step> --evidence <event id> --scope {root}`; then "
            f"`python3 -I {script} finish --scope {root}`. Only if the user explicitly decides to stop this process: "
            f"`python3 -I {script} abandon --run <run id> --reason \"<the user's words>\" --scope {root}`. "
            "HARNESS_PIPELINE_GATE=0 disables this gate.")


def main():
    try:
        raw = sys.stdin.read()
        payload = json.loads(raw) if raw.strip() else {}
        reason = build_reason(payload, os.environ)
        if reason:
            sys.stdout.write(json.dumps({"decision": "block", "reason": reason}, ensure_ascii=False))
    except Exception:
        pass
    return 0


if __name__ == "__main__":
    sys.exit(main())
