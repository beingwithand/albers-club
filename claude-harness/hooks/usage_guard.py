"""UserPromptSubmit hook: turn context size and 5-hour / 7-day usage into advice for Claude.

Hooks never see context size or rate limits, so this reads the state file that
scripts/statusline.py writes on every status-line refresh (${HARNESS_STATE:-~/.claude/harness-state.json}).

- Context (this session only; state older than HARNESS_STATE_MAX_AGE_S, default 600 s, is ignored):
  * >= ctx_stop (200k): every prompt, tell Claude to finish the current atomic step and run
    /handoff, then have the user /clear. If HANDOFF.md was refreshed in the last 20 min, just
    remind the user to /clear instead.
  * >= ctx_warn (160k): a softer heads-up, once per session.
- Usage (account-wide, so fresh data from any session counts): 5h or 7d >= 90% -> advise
  cheaper models / no fan-out, with the reset time. Once per session per window.
- Skipped for prompts that already are /handoff, /compact, /compact-prep or /clear.

Output: {"hookSpecificOutput": {"hookEventName": "UserPromptSubmit", "additionalContext": ...},
"systemMessage": ...}. Never blocks, always exits 0. Off switch: HARNESS_USAGE_GUARD=0.
Per-session memory of what was already said lives next to the state file (harness-guard.json).
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

DEFAULT_WARN, DEFAULT_STOP, DEFAULT_BUDGET = 160_000, 200_000, 250_000
RATE_CRIT = 90
HANDOFF_FRESH_S = 20 * 60
SKIP_PREFIXES = ("/handoff", "/compact", "/clear", "/harness:handoff", "/harness:compact-prep")
MAX_GUARD_SESSIONS = 50
LABEL = {"five_hour": "5-hour", "seven_day": "7-day"}


def _num(v):
    return float(v) if isinstance(v, (int, float)) and not isinstance(v, bool) else None


def guard_path(env):
    return C.state_path(env).with_name("harness-guard.json")


def fresh(ts, now, max_age):
    t = _num(ts)
    return t is not None and 0 <= now - t <= max_age


def session_ctx(state, sid, now, max_age):
    """This session's context tokens, or None if unknown/stale/other session."""
    if not sid:
        return None
    sess = (state.get("sessions") or {}).get(sid) if isinstance(state.get("sessions"), dict) else None
    if not isinstance(sess, dict):
        sess = state if state.get("session_id") == sid else None
    if not sess or not fresh(sess.get("ts"), now, max_age):
        return None
    return _num(sess.get("ctx_tokens"))


def reset_text(resets_at, now):
    r = _num(resets_at)
    if r is None:
        return ""
    local = dt.datetime.fromtimestamp(r).astimezone()
    return f"resets in {C.age_str(r - now)} ({local:%a %H:%M %Z})"


def evaluate(payload, env, now):
    """Return (additional_context, system_message) or (None, None)."""
    if str(env.get("HARNESS_USAGE_GUARD", "1")).strip().lower() in ("0", "false", "off", "no"):
        return None, None
    prompt = payload.get("prompt") if isinstance(payload.get("prompt"), str) else ""
    if prompt.strip().lower().startswith(SKIP_PREFIXES):
        return None, None
    state = C.load_json(C.state_path(env), {})
    if not isinstance(state, dict) or not state:
        return None, None
    try:
        max_age = float(env.get("HARNESS_STATE_MAX_AGE_S", "600"))
    except ValueError:
        max_age = 600.0
    sid = payload.get("session_id") if isinstance(payload.get("session_id"), str) else None
    gpath = guard_path(env)
    guard = C.load_json(gpath, {})
    guard = guard if isinstance(guard, dict) else {}
    mem = guard.get(sid) if isinstance(guard.get(sid), dict) else {}
    ctx_msgs, sys_msgs, changed = [], [], False

    ctx = session_ctx(state, sid, now, max_age)
    warn = _num(state.get("ctx_warn")) or DEFAULT_WARN
    stop = _num(state.get("ctx_stop")) or DEFAULT_STOP
    budget = _num(state.get("ctx_budget")) or DEFAULT_BUDGET
    if ctx is not None and ctx >= stop:
        root = C.project_root(payload.get("cwd"))
        ho = (root / "HANDOFF.md") if root else None
        ho_age = (now - ho.stat().st_mtime) if ho and ho.is_file() else None
        head = (f"[harness usage guard] Context is ~{ctx / 1000:.0f}k tokens "
                f"(>= {stop / 1000:.0f}k; working budget {budget / 1000:.0f}k). ")
        if ho_age is not None and ho_age <= HANDOFF_FRESH_S:
            ctx_msgs.append(head + f"HANDOFF.md was refreshed {C.age_str(ho_age)} ago. Finish only the current "
                            "atomic step, update HANDOFF.md if state changed, and remind the user to run /clear "
                            "then say 'read HANDOFF.md and continue'.")
        else:
            ctx_msgs.append(head + "Finish the current atomic step only (no new sub-tasks), make sure work is "
                            "saved and PROGRESS.md is current, then run the handoff skill (/handoff: write "
                            "HANDOFF.md and pass its cold-read test). Then tell the user to run /clear and say "
                            "'read HANDOFF.md and continue'. If the user prefers compaction, use /compact-prep instead.")
        sys_msgs.append(f"⛔ Context {ctx / 1000:.0f}k ≥ {stop / 1000:.0f}k: handoff + /clear recommended.")
    elif ctx is not None and ctx >= warn and not mem.get("soft_warned"):
        ctx_msgs.append(f"[harness usage guard] Heads-up: context is ~{ctx / 1000:.0f}k tokens (>= {warn / 1000:.0f}k "
                        f"of a {budget / 1000:.0f}k working budget). Steer toward a clean stopping point within the "
                        "next few steps, keep PROGRESS.md current, and avoid reading large files whole. Around "
                        f"{stop / 1000:.0f}k: /handoff, then /clear.")
        sys_msgs.append(f"⚠ Context {ctx / 1000:.0f}k: plan a handoff soon.")
        mem["soft_warned"] = now
        changed = True

    if fresh(state.get("ts"), now, max_age):
        rate_seen = mem.get("rate") if isinstance(mem.get("rate"), dict) else {}
        hot = []
        for key in ("seven_day", "five_hour"):
            pct, resets = _num(state.get(f"{key}_pct")), _num(state.get(f"{key}_resets"))
            if pct is None or pct < RATE_CRIT or (resets is not None and resets <= now):
                continue
            mark = f"{key}:{int(round(resets / 3600)) if resets else 'na'}"
            if mark in rate_seen:
                continue
            rate_seen[mark] = now
            hot.append(f"{LABEL[key]} usage is {pct:.0f}%" + (f", {reset_text(resets, now)}" if resets else ""))
        if hot:
            ctx_msgs.append("[harness usage guard] " + "; ".join(hot) + ". Conserve: route heavy work to "
                            "cheaper models (sonnet/haiku subagents), pause parallel fan-out and large research "
                            "sweeps, prefer finishing the current step and handing off, and ask the user before "
                            "starting anything long until the window resets.")
            sys_msgs.append("Usage high: " + "; ".join(hot))
            mem["rate"] = rate_seen
            changed = True

    if changed and sid:
        guard[sid] = mem
        if len(guard) > MAX_GUARD_SESSIONS:
            items = sorted(guard.items(), key=lambda kv: max([_num(v) or 0 for v in kv[1].values()
                                                              if not isinstance(v, dict)] or [0]), reverse=True)
            guard = dict(items[:MAX_GUARD_SESSIONS])
        try:
            C.write_json_atomic(gpath, guard)
        except OSError:
            pass
    if not ctx_msgs:
        return None, None
    return "\n\n".join(ctx_msgs), " | ".join(sys_msgs)


def main():
    try:
        payload = C.read_payload(sys.stdin)
        ctx, sysmsg = evaluate(payload, os.environ, C.now())
        if ctx:
            out = {"hookSpecificOutput": {"hookEventName": "UserPromptSubmit", "additionalContext": ctx}}
            if sysmsg:
                out["systemMessage"] = sysmsg
            sys.stdout.write(json.dumps(out, ensure_ascii=False))
    except Exception:
        pass
    return 0


if __name__ == "__main__":
    sys.exit(main())
