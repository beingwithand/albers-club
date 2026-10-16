"""UserPromptSubmit hook: turn context size and 5-hour / 7-day usage into advice for Claude.

Hooks never see context size or rate limits, so this reads the state file that
scripts/statusline.py writes on every status-line refresh (${HARNESS_STATE:-~/.claude/harness-state.json}).

- Context (this session only; state older than HARNESS_STATE_MAX_AGE_S, default 600 s, is ignored):
  * >= ctx_stop (200k): every prompt, tell Claude to finish the current atomic step and run
    /handoff, then have the user /clear. If HANDOFF.md was refreshed in the last 20 min, just
    remind the user to /clear instead.
  * >= ctx_warn (160k): a softer heads-up, once per session.
- Usage (account-wide, so fresh data from any session counts), graduated per docs/FANOUT.md §5:
  * 5h or 7d >= 70%  -> "conserve": halve fan-out widths, sonnet/haiku workers only.
  * 7d > 75%         -> "ask": as above, plus tier-3 fan-out (5+ agents) needs the user's OK first.
  * 5h or 7d >= 90%  -> "stop": no fan-out, except the minimum verification fan-out (2 verifiers
                        on sonnet/haiku) for client/employer deliverables; cheaper models, hand off.
  Each message carries a one-line `fanout_budget: ...` the orchestrator / fanout-plan skill reads.
  Said once per session per window per level (climbing to a higher level speaks again).
- Skipped for prompts that already are /handoff, /compact, /compact-prep or /clear.

CLI: `usage_guard.py --fanout-budget` prints the current budget as JSON (no stdin needed), using
the same thresholds; the fanout-plan skill calls it.

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
RATE_CRIT = 90          # >= : no fan-out (minimum verification only)
RATE_CONSERVE = 70      # >= (5h or 7d): halve widths, cheap workers only
RATE_ASK_7D = 75        # >  (7d only): tier-3 fan-out asks the user first
FULL_WIDTH = 10         # tier-3 per-batch cap (docs/FANOUT.md §3)
LEVELS = ("normal", "conserve", "ask", "stop")
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


def window_level(key, pct):
    """Usage level for one rate window ("five_hour" | "seven_day")."""
    if pct is None:
        return "normal"
    if pct >= RATE_CRIT:
        return "stop"
    if key == "seven_day" and pct > RATE_ASK_7D:
        return "ask"
    if pct >= RATE_CONSERVE:
        return "conserve"
    return "normal"


def fanout_budget(state, now, max_age):
    """Fan-out budget from the status-line state (docs/FANOUT.md §5).

    Returns a dict: level (unknown|normal|conserve|ask|stop), max_width (parallel workers per batch),
    tier3 (allowed|ask|no), workers (allowed worker models), verify_min (minimum verification
    fan-out width for client/employer deliverables), the two percentages and a short note.
    Windows whose reset time has passed count as 0%. Stale or missing state -> level "unknown":
    widths stay normal but tier 3 asks first, because weekly usage can't be confirmed <= 75%.
    """
    state = state if isinstance(state, dict) else {}
    pcts = {}
    if fresh(state.get("ts"), now, max_age):
        for key in ("five_hour", "seven_day"):
            pct, resets = _num(state.get(f"{key}_pct")), _num(state.get(f"{key}_resets"))
            pcts[key] = None if (pct is not None and resets is not None and resets <= now) else pct
    if not pcts or all(v is None for v in pcts.values()):
        level = "unknown"
    else:
        level = max((window_level(k, v) for k, v in pcts.items()), key=LEVELS.index)
    b = {"level": level, "five_hour_pct": pcts.get("five_hour"), "seven_day_pct": pcts.get("seven_day")}
    if level == "stop":
        b.update(max_width=0, tier3="no", workers="sonnet,haiku", verify_min=2,
                 note="no fan-out; client/employer deliverables still get 2 verifiers on sonnet/haiku")
    elif level in ("conserve", "ask"):
        b.update(max_width=FULL_WIDTH // 2, tier3="ask" if level == "ask" else "allowed",
                 workers="sonnet,haiku", verify_min=2,
                 note="halve fan-out widths (min 1), cheap workers only"
                      + ("; tier-3 fan-out requires asking the user first" if level == "ask" else ""))
    elif level == "unknown":
        b.update(max_width=FULL_WIDTH, tier3="ask", workers="any", verify_min=2,
                 note="usage unknown (status-line state missing or stale); tier 3 asks first")
    else:
        b.update(max_width=FULL_WIDTH, tier3="allowed", workers="any", verify_min=2, note="normal widths")
    return b


def budget_line(b):
    return (f"fanout_budget: level={b['level']} max_width={b['max_width']} tier3={b['tier3']} "
            f"workers={b['workers']} verify_min={b['verify_min']} (see docs/FANOUT.md)")


def _max_age(env):
    try:
        return float(env.get("HARNESS_STATE_MAX_AGE_S", "600"))
    except ValueError:
        return 600.0


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
    max_age = _max_age(env)
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
        hot, new = [], False
        for key in ("seven_day", "five_hour"):
            pct, resets = _num(state.get(f"{key}_pct")), _num(state.get(f"{key}_resets"))
            lvl = window_level(key, pct)
            if lvl == "normal" or (resets is not None and resets <= now):
                continue
            hot.append(f"{LABEL[key]} usage is {pct:.0f}%" + (f", {reset_text(resets, now)}" if resets else ""))
            mark = f"{key}:{lvl}:{int(round(resets / 3600)) if resets else 'na'}"
            if mark not in rate_seen:
                rate_seen[mark] = now
                new = True
        if hot and new:
            b = fanout_budget(state, now, max_age)
            head = "[harness usage guard] " + "; ".join(hot) + ". "
            if b["level"] == "stop":
                ctx_msgs.append(head + "Conserve: route heavy work to cheaper models (sonnet/haiku "
                                "subagents), pause parallel fan-out and large research sweeps (no fan-out "
                                "except minimum verification for client/employer deliverables: 2 verifiers "
                                "on sonnet/haiku), prefer finishing the current step and handing off, and ask "
                                "the user before starting anything long until the window resets.\n"
                                + budget_line(b))
                sys_msgs.append("Usage high: " + "; ".join(hot))
            else:
                ctx_msgs.append(head + "Fan-out: halve fan-out widths (minimum 1), cheap workers only "
                                "(sonnet/haiku, no Opus workers); keep verification of client/employer "
                                "deliverables at >= 2 verifiers."
                                + (" Tier-3 fan-out (5+ agents) requires asking the user first, stating "
                                   "the agent count and estimated tokens." if b["level"] == "ask" else "")
                                + "\n" + budget_line(b))
                sys_msgs.append("Usage elevated (fan-out reduced): " + "; ".join(hot))
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


def print_budget(env, now):
    b = fanout_budget(C.load_json(C.state_path(env), {}), now, _max_age(env))
    sys.stdout.write(json.dumps(b, ensure_ascii=False) + "\n")
    return 0


def main():
    if "--fanout-budget" in sys.argv[1:]:
        try:
            return print_budget(os.environ, C.now())
        except Exception:
            sys.stdout.write(json.dumps({"level": "unknown", "max_width": FULL_WIDTH, "tier3": "ask",
                                         "workers": "any", "verify_min": 2, "note": "error reading state"}) + "\n")
            return 0
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
