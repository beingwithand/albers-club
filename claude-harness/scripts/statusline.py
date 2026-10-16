#!/usr/bin/env python3
"""Claude Code status line: context budget, 5-hour / 7-day usage, cache, cost.

Configured in ~/.claude/settings.json (see config/settings.README.md):
    "statusLine": {"type": "command",
                   "command": "python3 -I ~/code/claude-harness/scripts/statusline.py",
                   "refreshInterval": 30}

Reads the status-line JSON on stdin (https://code.claude.com/docs/en/statusline), prints
ONE line, and persists a small state file that hooks read, because no hook input carries
rate limits or context size. Stdlib only, no subprocesses on the normal path, and it never
crashes: any error prints a minimal line and exits 0 (a non-zero exit blanks the line).

Example:  Opus 5.5 │ ctx 172k 69%⚠ │ 5h 41% ↻2h13m │ 7d 78% ↻3d4h │ cache warm 4m │ $3.12

Environment
  HARNESS_CTX_BUDGET   working budget in tokens (default 250000); % is of this, not the 1M window
  HARNESS_CTX_WARN     ⚠ threshold (default 160000)
  HARNESS_CTX_STOP     ⛔ threshold (default 200000)
  HARNESS_STATE        state file (default ~/.claude/harness-state.json)
  HARNESS_NTFY_TOPIC   if set, phone push via ntfy when 7d crosses 75/90% or 5h crosses 90%
  HARNESS_NTFY_SERVER  default https://ntfy.sh
  NO_COLOR             disables ANSI colour

Context tokens follow the docs' input-only formula (input + cache_creation + cache_read),
which is what `used_percentage` and auto-compaction use. `total_input_tokens` is the same
sum; `current_usage` is null before the first call and right after /compact.

ntfy pushes run in a detached child process, because Claude Code cancels an in-flight
status-line script when the next update arrives. Each (window, threshold, reset) is sent at
most once; the record lives in the state file under `ntfy_sent`.
"""
import json
import os
import pathlib
import re
import sys
import time

DEFAULT_BUDGET = 250_000
DEFAULT_WARN = 160_000
DEFAULT_STOP = 200_000
NTFY_RULES = (("seven_day", 75), ("seven_day", 90), ("five_hour", 90))
WINDOW_LABEL = {"five_hour": "5h", "seven_day": "7d"}
MAX_SESSIONS = 20


# ---------- small helpers ----------

def _num(v):
    """float for real numbers, else None (bools and strings are rejected)."""
    if isinstance(v, bool) or not isinstance(v, (int, float)):
        return None
    return float(v)


def _obj(d, key):
    v = d.get(key) if isinstance(d, dict) else None
    return v if isinstance(v, dict) else {}


def _env_int(env, key, default):
    try:
        v = int(str(env.get(key, "")).strip() or default)
        return v if v > 0 else default
    except ValueError:
        return default


def state_path(env=None):
    env = os.environ if env is None else env
    p = env.get("HARNESS_STATE")
    return pathlib.Path(p).expanduser() if p else pathlib.Path.home() / ".claude" / "harness-state.json"


def fmt_k(tokens):
    if tokens is None:
        return "?"
    if tokens >= 1_000_000:
        return f"{tokens / 1_000_000:.2f}M"
    return f"{tokens / 1000:.0f}k" if tokens >= 1000 else str(int(tokens))


def fmt_dur(seconds):
    """Compact countdown: 3d4h, 2h13m, 7m, <1m."""
    if seconds is None:
        return "?"
    s = int(max(0, seconds))
    d, rem = divmod(s, 86400)
    h, rem = divmod(rem, 3600)
    m = rem // 60
    if d:
        return f"{d}d{h}h"
    if h:
        return f"{h}h{m:02d}m"
    return f"{m}m" if m else "<1m"


# ---------- parsing ----------

def context_tokens(data):
    """Tokens currently in context (input-only formula), or None if unknown."""
    cw = _obj(data, "context_window")
    cu = cw.get("current_usage")
    if isinstance(cu, dict):
        parts = [_num(cu.get(k)) for k in ("input_tokens", "cache_creation_input_tokens", "cache_read_input_tokens")]
        if any(p is not None for p in parts):
            total = sum(p or 0 for p in parts)
            if total > 0:
                return int(total)
    tot = _num(cw.get("total_input_tokens"))
    if tot is not None and tot > 0:
        return int(tot)
    pct, size = _num(cw.get("used_percentage")), _num(cw.get("context_window_size"))
    if pct is not None and size:
        return int(round(pct * size / 100))
    return None


def rate_window(data, name):
    w = _obj(_obj(data, "rate_limits"), name)
    pct = _num(w.get("used_percentage"))
    if pct is None:
        return None
    return {"pct": pct, "resets_at": _num(w.get("resets_at"))}


def parse(data, env=None, now=None):
    env = os.environ if env is None else env
    now = time.time() if now is None else now
    if not isinstance(data, dict):
        data = {}
    model = _obj(data, "model")
    name = model.get("display_name") or model.get("id") or "Claude"
    cache = data.get("prompt_cache") if isinstance(data.get("prompt_cache"), dict) else None
    cache_info = None
    if cache is not None and isinstance(cache.get("warm"), bool):
        exp = _num(cache.get("expires_at"))
        cache_info = {"warm": cache["warm"], "left": (exp - now) if (cache["warm"] and exp) else None,
                      "hit_ratio": _num(cache.get("hit_ratio"))}
    cwd = data.get("cwd") or _obj(data, "workspace").get("current_dir")
    return {
        "model": str(name),
        "ctx": context_tokens(data),
        "budget": _env_int(env, "HARNESS_CTX_BUDGET", DEFAULT_BUDGET),
        "warn": _env_int(env, "HARNESS_CTX_WARN", DEFAULT_WARN),
        "stop": _env_int(env, "HARNESS_CTX_STOP", DEFAULT_STOP),
        "five_hour": rate_window(data, "five_hour"),
        "seven_day": rate_window(data, "seven_day"),
        "cache": cache_info,
        "cost": _num(_obj(data, "cost").get("total_cost_usd")),
        "session_id": data.get("session_id") if isinstance(data.get("session_id"), str) else None,
        "cwd": cwd if isinstance(cwd, str) else None,
    }


# ---------- rendering ----------

class _Paint:
    def __init__(self, on):
        self.on = on

    def __call__(self, text, code):
        return f"\033[{code}m{text}\033[0m" if self.on and code else text


def _level_code(pct, warn, crit):
    if pct is None:
        return ""
    return "31" if pct >= crit else "33" if pct >= warn else ""


def render(info, env=None, now=None):
    env = os.environ if env is None else env
    now = time.time() if now is None else now
    paint = _Paint(not env.get("NO_COLOR"))
    sep = paint(" │ ", "2")
    parts = [paint(info["model"], "1")]

    ctx = info["ctx"]
    if ctx is None:
        parts.append("ctx ?")
    else:
        pct = 100 * ctx / info["budget"]
        icon, code = "", ""
        if ctx >= info["stop"]:
            icon, code = "⛔", "31;1"
        elif ctx >= info["warn"]:
            icon, code = "⚠", "33"
        parts.append(paint(f"ctx {fmt_k(ctx)} {pct:.0f}%{icon}", code))

    for key in ("five_hour", "seven_day"):
        w = info[key]
        if not w:
            continue
        text = f"{WINDOW_LABEL[key]} {w['pct']:.0f}%"
        if w["resets_at"]:
            text += f" ↻{fmt_dur(w['resets_at'] - now)}"
        parts.append(paint(text, _level_code(w["pct"], 75, 90)))

    c = info["cache"]
    if c is not None:
        if c["warm"]:
            parts.append("cache warm" + (f" {fmt_dur(c['left'])}" if c["left"] is not None else ""))
        else:
            parts.append(paint("cache cold", "2"))
    if info["cost"] is not None:
        parts.append(f"${info['cost']:.2f}")

    line = sep.join(parts)
    try:  # narrow terminal: drop cache then cost before the line wraps
        cols = int(env.get("COLUMNS", "0"))
    except ValueError:
        cols = 0
    if cols and _visible_len(line) > cols:
        keep = [p for p in parts if not p.startswith(("cache", "$", "\033[2mcache"))]
        line = sep.join(keep)
    return line


def _visible_len(s):
    return len(re.sub(r"\033\[[0-9;]*m", "", s))


# ---------- state ----------

def load_state(path):
    try:
        with open(path, encoding="utf-8") as f:
            st = json.load(f)
        return st if isinstance(st, dict) else {}
    except (OSError, ValueError):
        return {}


def write_state_atomic(path, state):
    path = pathlib.Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(f".{path.name}.{os.getpid()}.tmp")
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(state, f, ensure_ascii=False, separators=(",", ":"))
    os.replace(tmp, path)


def build_state(prev, info, now):
    """New state dict. Rate limits are account-wide: if this payload lacks a window, keep
    the previous value while its reset time is still in the future."""
    st = dict(prev) if isinstance(prev, dict) else {}
    for key in ("five_hour", "seven_day"):
        w = info[key]
        if w:
            st[f"{key}_pct"], st[f"{key}_resets"] = w["pct"], w["resets_at"]
        else:
            r = _num(st.get(f"{key}_resets"))
            if r is None or r <= now:
                st[f"{key}_pct"], st[f"{key}_resets"] = None, None
    st.update({
        "ctx_tokens": info["ctx"],
        "ctx_budget": info["budget"],
        "ctx_warn": info["warn"],
        "ctx_stop": info["stop"],
        "ts": now,
        "session_id": info["session_id"],
        "cwd": info["cwd"],
    })
    if info["session_id"]:  # per-session context, so concurrent sessions don't clobber each other
        sessions = st.get("sessions") if isinstance(st.get("sessions"), dict) else {}
        sessions[info["session_id"]] = {"ctx_tokens": info["ctx"], "ts": now, "cwd": info["cwd"]}
        if len(sessions) > MAX_SESSIONS:
            newest = sorted(sessions.items(), key=lambda kv: _num(kv[1].get("ts")) or 0, reverse=True)
            sessions = dict(newest[:MAX_SESSIONS])
        st["sessions"] = sessions
    return st


# ---------- ntfy ----------

def _window_key(name, threshold, resets_at, now):
    # Round the reset time to the hour so tiny jitter in resets_at doesn't re-alert;
    # with no reset time, fall back to a per-day key.
    anchor = int(round(resets_at / 3600)) if resets_at else f"d{int(now // 86400)}"
    return f"{name}:{threshold}:{anchor}"


def due_alerts(state, info, now):
    """Return [(key, title, message, priority)] not yet sent; marks them in state['ntfy_sent']."""
    sent = state.get("ntfy_sent") if isinstance(state.get("ntfy_sent"), dict) else {}
    out = []
    for name, threshold in NTFY_RULES:
        w = info[name]
        if not w or w["pct"] < threshold:
            continue
        key = _window_key(name, threshold, w["resets_at"], now)
        if key in sent:
            continue
        # Only the highest crossed threshold per window is pushed; lower ones are marked too.
        higher = [t for n, t in NTFY_RULES if n == name and t > threshold and w["pct"] >= t]
        sent[key] = now
        if higher:
            continue
        reset = f", resets in {fmt_dur(w['resets_at'] - now)}" if w["resets_at"] else ""
        label = WINDOW_LABEL[name]
        out.append((key, f"Claude {label} usage {w['pct']:.0f}%",
                    f"{label} window at {w['pct']:.0f}% (≥{threshold}%){reset}. "
                    "Consider cheaper models / fewer parallel agents, or pause.",
                    "high" if threshold >= 90 else "default"))
    # forget keys older than 8 days
    state["ntfy_sent"] = {k: v for k, v in sent.items() if (_num(v) or 0) > now - 8 * 86400}
    return out


def send_ntfy(topic, title, message, priority="default", server=None, timeout=2.0):
    """POST one message to ntfy. Returns True on HTTP 2xx. Never raises."""
    import urllib.request
    server = (server or "https://ntfy.sh").rstrip("/")
    req = urllib.request.Request(
        f"{server}/{topic}", data=message.encode("utf-8"), method="POST",
        headers={"Title": title.encode("utf-8").decode("latin-1", "replace"),
                 "Priority": priority, "Tags": "warning"})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return 200 <= getattr(resp, "status", 200) < 300
    except Exception:
        return False


def _dispatch_ntfy(topic, alerts, server):
    """Send from a detached child so a cancelled status-line run can't drop the push."""
    import subprocess
    payload = json.dumps({"topic": topic, "server": server, "alerts": alerts})
    child = subprocess.Popen([sys.executable, "-I", os.path.abspath(__file__), "--send-ntfy"],
                             stdin=subprocess.PIPE, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                             start_new_session=True)
    child.stdin.write(payload.encode("utf-8"))
    child.stdin.close()


def _send_ntfy_child():
    job = json.loads(sys.stdin.read() or "{}")
    for _key, title, msg, prio in job.get("alerts", []):
        send_ntfy(job["topic"], title, msg, prio, job.get("server"))


# ---------- main ----------

def run(raw, env=None, now=None):
    """Parse, persist, maybe alert. Returns the line to print."""
    env = os.environ if env is None else env
    now = time.time() if now is None else now
    try:
        data = json.loads(raw) if raw and raw.strip() else {}
    except ValueError:
        data = {}
    info = parse(data, env, now)
    line = render(info, env, now)
    try:
        path = state_path(env)
        state = build_state(load_state(path), info, now)
        topic = (env.get("HARNESS_NTFY_TOPIC") or "").strip()
        alerts = due_alerts(state, info, now) if topic else []
        write_state_atomic(path, state)  # record before sending: at most once, never a storm
        if alerts:
            _dispatch_ntfy(topic, alerts, env.get("HARNESS_NTFY_SERVER"))
    except Exception:
        pass
    return line


def main():
    if len(sys.argv) > 1 and sys.argv[1] == "--send-ntfy":
        try:
            _send_ntfy_child()
        except Exception:
            pass
        return 0
    try:
        line = run(sys.stdin.read())
    except Exception:
        line = "Claude │ statusline error"
    sys.stdout.write(line + "\n")
    sys.stdout.flush()
    return 0


if __name__ == "__main__":
    sys.exit(main())
