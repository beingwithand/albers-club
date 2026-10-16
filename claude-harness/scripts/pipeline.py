#!/usr/bin/env python3
"""Pipelines: classify a task, track an ordered process run, and check its required steps against evidence.

    python3 -I scripts/pipeline.py match "<task description>"      # -> pipeline id + confidence (or abstain)
    python3 -I scripts/pipeline.py match '{"event": "inbox_file_detected", "path": "..."}'
    python3 -I scripts/pipeline.py start <pipeline> --scope <dir> [--param k=v ...]
    python3 -I scripts/pipeline.py status [--scope <dir>] [--json]
    python3 -I scripts/pipeline.py mark <step> --evidence <event id> [--run <run id>] [--scope <dir>]
    python3 -I scripts/pipeline.py check [--scope <dir>] [--run <run id>] [--json]   # exit 1 = missing steps
    python3 -I scripts/pipeline.py finish [--scope <dir>] [--run <run id>]          # only if check passes
    python3 -I scripts/pipeline.py abandon --run <run id> --reason "<the user's words>"
    python3 -I scripts/pipeline.py queue scan <project> [--source launchd]  |  queue list [--scope <dir>]
                                         |  queue ack <queue id> [--reason ...]
    python3 -I scripts/pipeline.py lint                                             # exit 1 on errors

The process graph is pipelines/pipelines.yaml (override with HARNESS_PIPELINES); docs/PIPELINES.md explains
it. A run's state lives in <project>/.harness/pipeline_state.json and as a checklist block in PROGRESS.md
"In progress" (markers `<!-- pipeline:<run id> -->`; ☐ pending, ☑ satisfied; never `[x]`, so the
verification gate does not count pipeline steps as done items). Evidence comes from $HARNESS_DATA/log/*.jsonl
(events in the project scope since the run started), project files, $HARNESS_DATA stores and builtin checks.

Events written (actor `harness`): pipeline_started, pipeline_step (from mark), pipeline_finished (outcome
worked | abandoned), inbox_file_detected (queue scan / watch hook). The queue is
$HARNESS_DATA/queue/inbox.jsonl (append-only) + queue/acked.jsonl.

Stdlib only (YAML via scripts/schema_check.py's subset parser, PyYAML as fallback). Exit codes: 0 ok,
1 check failed / lint errors, 2 usage error or refused (e.g. evidence that does not match the step).
"""
import argparse
import datetime as dt
import hashlib
import importlib.util
import json
import os
import pathlib
import re
import sys
import uuid

ROOT = pathlib.Path(__file__).resolve().parent.parent
DEFAULT_PIPELINES = ROOT / "pipelines" / "pipelines.yaml"
STATE_REL = pathlib.Path(".harness") / "pipeline_state.json"
MAX_LOG_FILES = 3
MATCHER_KEYS = {
    "event": {"event", "labels", "not_labels", "verdict", "agent", "where", "content_re", "min_count"},
    "file": {"file", "changed_since_start", "contains", "not_contains"},
    "json": {"json", "has", "select", "changed_since_start"},
    "store": {"store", "where"},
    "builtin": {"builtin"},
}
BUILTINS = ("component_frontmatter", "learning_contract", "rubric_eval", "pipeline_membership", "index_fresh")
STEP_KEYS = {"id", "run", "required", "after", "pre", "post", "verification", "evidence", "manual"}
PIPELINE_KEYS = {"title", "owner_agent", "client_bound", "autostart", "strict_order", "params", "triggers", "steps"}
TRIVIAL = re.compile(r"^\s*(hi|hello|hey|thanks?|thank you|ok(ay)?|yes|no|sure|great|cool|got it|ㅇㅇ|네|응|고마워|감사합니다|좋아)\s*[.!?]*\s*$", re.I)
TRIVIAL_LEN = 12
MODELS = {"haiku", "sonnet", "opus", "fable", "inherit"}


class Refused(Exception):
    pass


# ---------------------------------------------------------------- loading

def _load_module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def yaml_load(text):
    sc = ROOT / "scripts" / "schema_check.py"
    if sc.is_file():
        try:
            return _load_module("harness_schema_check", sc).yaml_load(text)
        except AttributeError:
            pass
    import yaml  # fallback only
    return yaml.safe_load(text)


_CONFIG_CACHE = {}


def pipelines_path(env=None):
    env = os.environ if env is None else env
    return pathlib.Path(env.get("HARNESS_PIPELINES") or DEFAULT_PIPELINES)


def load_config(env=None):
    path = pipelines_path(env)
    key = (str(path), path.stat().st_mtime if path.exists() else None)
    if key not in _CONFIG_CACHE:
        cfg = yaml_load(path.read_text(encoding="utf-8")) or {}
        cfg.setdefault("defaults", {})
        cfg.setdefault("pipelines", {})
        cfg.setdefault("evidence_library", {})
        _CONFIG_CACHE[key] = cfg
    return _CONFIG_CACHE[key]


def data_dir(env=None):
    env = os.environ if env is None else env
    return pathlib.Path(env.get("HARNESS_DATA") or (pathlib.Path.home() / "harness-data")).expanduser()


def now_utc():
    return dt.datetime.now(dt.timezone.utc)


def parse_ts(value):
    if isinstance(value, (int, float)) and not isinstance(value, bool):
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


def _norm(p):
    try:
        return os.path.normpath(os.path.abspath(os.path.expanduser(str(p))))
    except Exception:
        return None


def project_root(scope):
    """Nearest dir at/above scope with .harness/pipeline_state.json, PROGRESS.md or .git (never ~); else scope."""
    p = pathlib.Path(_norm(scope or os.getcwd()))
    home = pathlib.Path.home()
    for d in [p, *p.parents]:
        if d == home or d == d.parent:
            break
        if (d / STATE_REL).is_file() or (d / "PROGRESS.md").is_file() or (d / ".git").exists():
            return d
    return p


def harness_root_of(path):
    """The harness checkout containing path (.claude-plugin/plugin.json with name 'harness'), or None."""
    p = pathlib.Path(_norm(path))
    for d in [p, *p.parents]:
        pj = d / ".claude-plugin" / "plugin.json"
        if pj.is_file():
            try:
                if json.loads(pj.read_text(encoding="utf-8")).get("name") == "harness":
                    return d
            except (OSError, ValueError):
                return None
        if d == d.parent:
            break
    return None


# ---------------------------------------------------------------- events

def _common():
    return _load_module("harness_common_pl", ROOT / "hooks" / "_common.py")


def new_id(prefix):
    n = now_utc()
    return f"{prefix}_{n:%Y%m%d_%H%M%S}_{uuid.uuid4().hex[:8]}"


def append_event(kind, scope, env=None, **fields):
    env = os.environ if env is None else env
    n = now_utc()
    log_dir = data_dir(env) / "log"
    log_dir.mkdir(parents=True, exist_ok=True)
    ev = {"id": f"evt_{n:%Y%m%d_%H%M%S}_{uuid.uuid4().hex[:8]}", "ts": n.isoformat(),
          "actor": env.get("HARNESS_ACTOR") or "harness", "type": kind, "scope_hint": str(scope) if scope else None,
          "session_id": env.get("CLAUDE_SESSION_ID"), "labels": ["pipeline"], "intent": None, "meta": None}
    ev.update(fields)
    _common().locked_append(log_dir / f"{n:%Y-%m}.jsonl", json.dumps(ev, ensure_ascii=False) + "\n")
    return ev


def iter_events(env, since=None, types=None):
    log_dir = data_dir(env) / "log"
    files = sorted(log_dir.glob("*.jsonl"))[-MAX_LOG_FILES:] if log_dir.is_dir() else []
    for f in files:
        try:
            fh = open(f, encoding="utf-8", errors="replace")
        except OSError:
            continue
        with fh:
            for line in fh:
                if types and not any(f'"{t}"' in line for t in types):
                    continue
                try:
                    ev = json.loads(line)
                except ValueError:
                    continue
                if not isinstance(ev, dict):
                    continue
                if types and ev.get("type") not in types:
                    continue
                ts = parse_ts(ev.get("ts"))
                if since is not None and (ts is None or ts < since):
                    continue
                yield ev


def in_scope(rec, root):
    root_s = _norm(root)
    for key in ("cwd", "scope_hint", "project_dir", "project"):
        v = rec.get(key)
        if isinstance(v, str) and v:
            n = _norm(v)
            if n == root_s or (n and n.startswith(root_s + os.sep)):
                return True
    scope = rec.get("scope")
    if isinstance(scope, str) and scope and scope != "global":
        s = scope.strip("/")
        if os.path.isabs(scope):
            n = _norm(scope)
            if n == root_s or n.startswith(root_s + os.sep):
                return True
        elif root_s.endswith("/" + s) or root_s == s:
            return True
    for p in rec.get("pointers") or []:
        if isinstance(p, str) and os.path.isabs(p):
            n = _norm(p)
            if n == root_s or n.startswith(root_s + os.sep):
                return True
    return False


def has_scope_fields(rec):
    return any(isinstance(rec.get(k), str) and rec.get(k) for k in ("cwd", "scope_hint", "project_dir", "project", "scope"))


def dotted(obj, path):
    cur = obj
    for part in path.split("."):
        if not isinstance(cur, dict):
            return None
        cur = cur.get(part)
    return cur


def value_ok(actual, want):
    if isinstance(want, list):
        return any(value_ok(actual, w) for w in want)
    if isinstance(want, str) and want.startswith("re:"):
        return actual is not None and re.search(want[3:], actual if isinstance(actual, str) else json.dumps(actual, ensure_ascii=False)) is not None
    if isinstance(want, bool):
        return actual is want
    return actual is not None and str(actual) == str(want)


def where_ok(rec, where):
    return all(value_ok(dotted(rec, k), v) for k, v in (where or {}).items())


def event_fields_match(ev, m):
    """Matcher fields other than scope/time."""
    if ev.get("type") != m.get("event"):
        return False
    labels = ev.get("labels") or []
    if not isinstance(labels, list):
        labels = [labels]
    if any(l not in labels for l in m.get("labels") or []):
        return False
    if any(l in labels for l in m.get("not_labels") or []):
        return False
    if m.get("verdict") and str(ev.get("verdict", "")).lower() not in [str(v).lower() for v in m["verdict"]]:
        return False
    if m.get("agent"):
        a = m["agent"]
        agent = str(ev.get("agent") or "")
        actor = str(ev.get("actor") or "")
        if not (agent in (a, f"harness:{a}") or actor in (f"agent:{a}", f"agent:harness:{a}")):
            return False
    if m.get("where") and not where_ok(ev, m["where"]):
        return False
    if m.get("content_re"):
        hay = " ".join(json.dumps(ev.get(k), ensure_ascii=False) for k in ("content", "command", "items", "proof", "pointers", "labels", "meta") if ev.get(k) is not None)
        if not re.search(m["content_re"], hay):
            return False
    return True


# ---------------------------------------------------------------- state

def state_file(root):
    return pathlib.Path(root) / STATE_REL


def load_state(root):
    try:
        data = json.loads(state_file(root).read_text(encoding="utf-8"))
        if isinstance(data, dict) and isinstance(data.get("runs"), list):
            return data
    except (OSError, ValueError):
        pass
    return {"version": 1, "runs": []}


def save_state(root, state):
    _common().write_json_atomic(state_file(root), state)


def active_runs(state, stale_days=None, include_stale=True, now=None):
    now = now_utc().timestamp() if now is None else now
    out = []
    for r in state.get("runs", []):
        if r.get("status") != "active":
            continue
        stale = stale_days is not None and now - float(r.get("started_ts") or 0) > float(stale_days) * 86400
        if stale and not include_stale:
            continue
        out.append(r)
    return out


def is_stale(run, cfg, now=None):
    now = now_utc().timestamp() if now is None else now
    days = float(cfg["defaults"].get("stale_days", 7))
    return now - float(run.get("started_ts") or 0) > days * 86400


# ---------------------------------------------------------------- PROGRESS.md block

BLOCK_RE = re.compile(r"\n?<!-- pipeline:(?P<id>[\w-]+) -->.*?<!-- /pipeline:(?P=id) -->\n?", re.S)


def strip_blocks(text):
    return BLOCK_RE.sub("\n", text)


def progress_hash(root):
    p = pathlib.Path(root) / "PROGRESS.md"
    try:
        text = p.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return None
    return hashlib.sha256(strip_blocks(text).strip().encode("utf-8")).hexdigest()


def render_block(run, pipe, results=None):
    head = f"**Pipeline `{run['pipeline']}`** ({pipe.get('title', '')}) run `{run['run_id']}`"
    if run.get("status") != "active":
        head += f" — {run.get('status')} {run.get('finished_at', '')}"
    lines = [f"<!-- pipeline:{run['run_id']} -->", head]
    for st in pipe.get("steps", []):
        res = (results or {}).get(st["id"]) or {}
        box = "☑" if res.get("ok") else "☐"
        req = "required" if st.get("required") else "optional"
        via = f" — evidence: {res['via']}" if res.get("ok") and res.get("via") else ""
        lines.append(f"- {box} {st['id']} ({req}) — {st.get('run', '')}{via}")
    lines.append(f"<!-- /pipeline:{run['run_id']} -->")
    return "\n".join(lines)


def write_block(root, run, pipe, results=None):
    p = pathlib.Path(root) / "PROGRESS.md"
    block = render_block(run, pipe, results)
    try:
        text = p.read_text(encoding="utf-8") if p.is_file() else "# Progress\n\n## In progress\n"
    except OSError:
        return
    pat = re.compile(r"<!-- pipeline:%s -->.*?<!-- /pipeline:%s -->" % (re.escape(run["run_id"]), re.escape(run["run_id"])), re.S)
    if pat.search(text):
        text = pat.sub(lambda _m: block, text)
    else:
        m = re.search(r"(?mi)^#{1,6}\s*in progress\s*$", text)
        if m:
            text = text[:m.end()] + "\n" + block + "\n" + text[m.end():]
        else:
            text = text.rstrip("\n") + "\n\n## In progress\n" + block + "\n"
    try:
        p.write_text(text, encoding="utf-8")
    except OSError:
        pass


# ---------------------------------------------------------------- evidence

def expand(value, params):
    if not isinstance(value, str):
        return value, True
    missing = False

    def rep(m):
        nonlocal missing
        k = m.group(1)
        if k in params and params[k] not in (None, ""):
            return str(params[k])
        missing = True
        return m.group(0)
    out = re.sub(r"\{(\w+)\}", rep, value)
    return out, not missing


def resolve_matcher(m, cfg):
    if isinstance(m, str) and m.startswith("lib:"):
        lib = cfg.get("evidence_library", {}).get(m[4:])
        if not isinstance(lib, dict):
            raise ValueError(f"unknown evidence library entry {m}")
        return dict(lib), m
    if isinstance(m, dict):
        return m, None
    raise ValueError(f"bad matcher {m!r}")


def matcher_kind(m):
    for k in ("event", "file", "json", "store", "builtin"):
        if k in m:
            return k
    return None


class Ctx:
    def __init__(self, root, run, cfg, env):
        self.root = pathlib.Path(root)
        self.run = run
        self.cfg = cfg
        self.env = env
        self.grace = float(cfg["defaults"].get("grace_s", 120))
        self.since = float(run.get("started_ts") or 0) - self.grace
        self.params = dict(run.get("params") or {})
        if self.params.get("file") and "file_name" not in self.params:
            self.params["file_name"] = os.path.basename(str(self.params["file"]))
        self._events = None

    def events(self):
        if self._events is None:
            self._events = [e for e in iter_events(self.env, since=self.since) if in_scope(e, self.root)]
        return self._events


def _json_values(obj, path, select):
    parts = path.split(".")

    def walk(cur, i):
        if i == len(parts):
            yield cur
            return
        part = parts[i]
        star = part.endswith("[*]")
        key = part[:-3] if star else part
        if not isinstance(cur, dict):
            return
        nxt = cur.get(key)
        if star:  # `select` filters the elements of the starred list
            for el in nxt if isinstance(nxt, list) else []:
                if select and not (isinstance(el, dict) and all(str(el.get(k)) == str(v) for k, v in select.items())):
                    continue
                yield from walk(el, i + 1)
        else:
            yield from walk(nxt, i + 1)
    return list(walk(obj, 0))


def eval_matcher(ctx, m):
    """Return (ok, ts or None, exact: bool, detail)."""
    kind = matcher_kind(m)
    if kind == "event":
        hits = [e for e in ctx.events() if event_fields_match(e, m)]
        need = int(m.get("min_count") or 1)
        if len(hits) >= need:
            hits.sort(key=lambda e: parse_ts(e.get("ts")) or 0)
            return True, parse_ts(hits[need - 1].get("ts")), True, ",".join(e.get("id", "?") for e in hits[:need])
        return False, None, True, f"{len(hits)}/{need} `{m['event']}` events"
    if kind == "file":
        pattern, _ = expand(m["file"], ctx.params)
        files = [p for p in ctx.root.glob(pattern) if p.is_file() and not p.name.startswith(".")
                 and STATE_REL.parts[0] not in p.relative_to(ctx.root).parts]
        best = None
        for p in files:
            rel = p.relative_to(ctx.root).as_posix()
            if m.get("changed_since_start"):
                if rel == "PROGRESS.md":
                    if progress_hash(ctx.root) == ctx.run.get("progress_baseline"):
                        continue
                elif p.stat().st_mtime < ctx.since:
                    continue
            if m.get("contains") or m.get("not_contains"):
                try:
                    text = p.read_text(encoding="utf-8", errors="replace")
                except OSError:
                    continue
                if rel == "PROGRESS.md":
                    text = strip_blocks(text)
                if m.get("contains") and not re.search(m["contains"], text):
                    continue
                if m.get("not_contains") and re.search(m["not_contains"], text):
                    continue
            mt = p.stat().st_mtime
            if best is None or mt > best[1]:
                best = (rel, mt)
        if best:
            return True, best[1], False, best[0]
        return False, None, False, f"no file {pattern} matching"
    if kind == "json":
        p = ctx.root / m["json"]
        try:
            data = json.loads(p.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            return False, None, False, f"{m['json']} unreadable"
        if m.get("changed_since_start") and p.stat().st_mtime < ctx.since:
            return False, None, False, f"{m['json']} unchanged since start"
        select = {}
        for k, v in (m.get("select") or {}).items():
            val, ok = expand(v, ctx.params)
            if ok:
                select[k] = val
        vals = _json_values(data, m["has"], select)
        if any(v not in (None, "", [], {}) for v in vals):
            return True, p.stat().st_mtime, False, f"{m['json']}:{m['has']}"
        return False, None, False, f"{m['json']}: {m['has']} empty" + (f" for {select}" if select else "")
    if kind == "store":
        p = data_dir(ctx.env) / m["store"]
        try:
            fh = open(p, encoding="utf-8", errors="replace")
        except OSError:
            return False, None, True, f"store {m['store']} missing"
        best = None
        with fh:
            for line in fh:
                try:
                    rec = json.loads(line)
                except ValueError:
                    continue
                if not isinstance(rec, dict):
                    continue
                ts = parse_ts(rec.get("ts"))
                if ts is None or ts < ctx.since:
                    continue
                if has_scope_fields(rec) and not in_scope(rec, ctx.root):
                    continue
                if m.get("where") and not where_ok(rec, m["where"]):
                    continue
                if best is None or ts < best[1]:
                    best = (rec.get("id") or "record", ts)
        if best:
            return True, best[1], True, f"{m['store']}:{best[0]}"
        return False, None, True, f"no {m['store']} record since start"
    if kind == "builtin":
        ok, detail = run_builtin(m["builtin"], ctx)
        return ok, None, False, detail
    return False, None, False, "unknown matcher"


def evaluate(root, run, cfg, env=None):
    """Per-step results: {step: {ok, ts, exact, via, detail, required}} plus order violations."""
    env = os.environ if env is None else env
    pipe = cfg["pipelines"].get(run["pipeline"]) or {}
    ctx = Ctx(root, run, cfg, env)
    results = {}
    marks = run.get("marks") or {}
    for st in pipe.get("steps", []):
        sid = st["id"]
        res = {"ok": False, "ts": None, "exact": False, "via": None, "detail": [], "required": bool(st.get("required"))}
        for mid in marks.get(sid, []):
            ok, ev, why = validate_mark(ctx, st, mid)
            if ok:
                res.update(ok=True, ts=parse_ts(ev.get("ts")), exact=True, via=f"mark {mid}")
                break
            res["detail"].append(f"mark {mid}: {why}")
        if not res["ok"]:
            for raw in st.get("evidence") or []:
                try:
                    m, name = resolve_matcher(raw, cfg)
                    ok, ts, exact, detail = eval_matcher(ctx, m)
                except (ValueError, re.error, KeyError) as e:
                    ok, ts, exact, detail, name = False, None, False, f"bad matcher: {e}", None
                if ok:
                    res.update(ok=True, ts=ts, exact=exact, via=(name + ": " if name else "") + str(detail))
                    break
                res["detail"].append(str(detail))
        results[sid] = res
    violations = []
    for st in pipe.get("steps", []):
        r = results[st["id"]]
        for dep in st.get("after") or []:
            d = results.get(dep)
            if not d:
                continue
            if r["ok"] and not d["ok"]:
                violations.append(f"{st['id']} has evidence but its prerequisite {dep} does not")
            elif r["ok"] and d["ok"] and r["exact"] and d["exact"] and r["ts"] is not None and d["ts"] is not None \
                    and r["ts"] + 1 < d["ts"]:
                violations.append(f"{st['id']} ran before its prerequisite {dep}")
    return results, violations


def summarize(root, run, cfg, env=None):
    pipe = cfg["pipelines"].get(run["pipeline"]) or {}
    results, violations = evaluate(root, run, cfg, env)
    missing = [s["id"] for s in pipe.get("steps", []) if s.get("required") and not results[s["id"]]["ok"]]
    strict_fail = bool(pipe.get("strict_order")) and bool(violations)
    nxt = None
    for s in pipe.get("steps", []):
        if s.get("required") and not results[s["id"]]["ok"]:
            if all(results.get(d, {}).get("ok") for d in s.get("after") or []) or nxt is None:
                nxt = s
                if all(results.get(d, {}).get("ok") for d in s.get("after") or []):
                    break
    return {"run_id": run["run_id"], "pipeline": run["pipeline"], "title": pipe.get("title"), "scope": str(root),
            "started_at": run.get("started_at"), "params": run.get("params") or {},
            "ok": not missing and not strict_fail, "missing": missing, "order_violations": violations,
            "strict_order": bool(pipe.get("strict_order")),
            "next": ({"step": nxt["id"], "run": nxt.get("run"), "pre": nxt.get("pre"), "post": nxt.get("post"),
                      "verification": nxt.get("verification")} if nxt else None),
            "steps": {k: {kk: vv for kk, vv in v.items() if kk != "exact"} for k, v in results.items()}}


def validate_mark(ctx, step, event_id):
    ev = next((e for e in iter_events(ctx.env) if e.get("id") == event_id), None)
    if ev is None:
        return False, None, "event not found in the log"
    ts = parse_ts(ev.get("ts"))
    if ts is None or ts < ctx.since:
        return False, ev, "event is older than the run"
    if step.get("manual"):
        return True, ev, ""
    for raw in step.get("evidence") or []:
        try:
            m, _ = resolve_matcher(raw, ctx.cfg)
        except ValueError:
            continue
        if matcher_kind(m) == "event" and event_fields_match(ev, m):
            return True, ev, ""
    wanted = []
    for raw in step.get("evidence") or []:
        try:
            m, _ = resolve_matcher(raw, ctx.cfg)
        except ValueError:
            continue
        if matcher_kind(m) == "event":
            wanted.append({k: v for k, v in m.items() if k != "min_count"})
    return False, ev, ("event does not match the step's evidence spec; expected one of "
                       + json.dumps(wanted, ensure_ascii=False) if wanted else
                       "this step has no event evidence; satisfy its file/json/store/builtin check instead")


# ---------------------------------------------------------------- builtins (new-component checklist)

def component_id(rel):
    rel = rel.replace(os.sep, "/")
    m = re.fullmatch(r"skills/([\w.-]+)/SKILL\.md", rel)
    if m:
        return f"skill:{m.group(1)}"
    m = re.fullmatch(r"agents/([\w.-]+)\.md", rel)
    if m:
        return f"agent:{m.group(1)}"
    if re.fullmatch(r"(hooks|scripts)/[\w.-]+\.(py|sh)", rel):
        return f"script:{rel}"
    return None


def frontmatter(text):
    if not text.startswith("---"):
        return None
    end = text.find("\n---", 3)
    if end < 0:
        return None
    out = {}
    for line in text[3:end].splitlines():
        m = re.match(r"^([\w-]+):\s*(.*)$", line)
        if m:
            out[m.group(1)] = m.group(2).strip().strip("'\"")
    return out


def _component(ctx):
    rel = ctx.params.get("component")
    if not rel:
        return None, None, "run has no `component` param (start with --param component=<path>)"
    p = pathlib.Path(rel)
    if p.is_absolute():
        try:
            rel = p.resolve().relative_to(ctx.root.resolve()).as_posix()
        except ValueError:
            return None, None, f"{p} is outside {ctx.root}"
    cid = component_id(rel)
    if not cid:
        return None, None, f"{rel} is not a skill/agent/hook/script path"
    return rel, cid, ""


def run_builtin(name, ctx):
    rel, cid, err = _component(ctx)
    if err:
        return False, err
    path = ctx.root / rel
    if name == "component_frontmatter":
        try:
            text = path.read_text(encoding="utf-8")
        except OSError:
            return False, f"{rel} missing"
        if cid.startswith(("skill:", "agent:")):
            fm = frontmatter(text)
            if not fm:
                return False, f"{rel}: no frontmatter"
            miss = [k for k in ("name", "description") if not fm.get(k)]
            if cid.startswith("agent:"):
                if fm.get("model") not in MODELS:
                    miss.append("model (explicit, one of " + "|".join(sorted(MODELS)) + ")")
            if fm.get("name") and fm.get("name") != cid.split(":", 1)[1]:
                miss.append(f"name {fm.get('name')!r} != {cid.split(':', 1)[1]!r}")
            return (not miss), (f"{rel}: frontmatter ok" if not miss else f"{rel}: missing " + ", ".join(miss))
        if rel.startswith("hooks/") and not rel.startswith("hooks/_"):
            try:
                hj = (ctx.root / "hooks" / "hooks.json").read_text(encoding="utf-8")
            except OSError:
                hj = ""
            if f"hooks/{path.name}" not in hj:
                return False, f"{rel} is not registered in hooks/hooks.json"
        if rel.endswith(".py"):
            import ast
            try:
                doc = ast.get_docstring(ast.parse(text))
            except SyntaxError as e:
                return False, f"{rel}: syntax error {e}"
            return (bool(doc), f"{rel}: docstring ok" if doc else f"{rel}: no module docstring")
        return (bool(re.search(r"(?m)^#\s*\S", text)), f"{rel}: header comment")
    if name == "learning_contract":
        lp = ctx.root / "learning" / "contracts.yaml"
        try:
            text = lp.read_text(encoding="utf-8")
        except OSError:
            return False, "learning/contracts.yaml missing"
        try:
            data = yaml_load(text) or {}
        except Exception:
            data = {}
        sections = [data.get("contracts") or {}, data.get("exempt") or {}] if isinstance(data, dict) else []
        if any(isinstance(s, dict) and cid in s for s in sections) or re.search(r'(?m)^\s+"?%s"?\s*:' % re.escape(cid), text):
            return True, f"{cid} has a learning contract or exemption"
        return False, f"{cid} has no entry in learning/contracts.yaml (propose a draft contract or an exempt reason)"
    if name == "rubric_eval":
        if not cid.startswith(("skill:", "agent:")):
            return True, f"{cid}: not a work-producing skill/agent (n/a)"
        cj = ctx.root / "docs" / "components.json"
        try:
            rows = (json.loads(cj.read_text(encoding="utf-8")).get("coverage") or {}).get("rows") or []
        except (OSError, ValueError, AttributeError):
            rows = []
        for r in rows:
            if r.get("id") == cid and r.get("status") in ("covered", "exempt"):
                return True, f"{cid}: coverage {r.get('status')}"
        try:
            ex = (json.loads((ctx.root / "scripts" / "harness_index.json").read_text(encoding="utf-8")).get("exempt") or {})
        except (OSError, ValueError, AttributeError):
            ex = {}
        if cid in ex:
            return True, f"{cid}: exempt in scripts/harness_index.json (regenerate the index)"
        return False, f"{cid}: no rubric + eval area and no exempt reason (docs/components.json coverage)"
    if name == "pipeline_membership":
        cfg = ctx.cfg
        refs = referenced_components(cfg)
        if cid in refs or cid in (cfg.get("standalone") or {}) or cid in (cfg.get("pending_components") or {}):
            return True, f"{cid} is in pipelines.yaml"
        if cid.startswith("script:") and rel in pipelines_path(ctx.env).read_text(encoding="utf-8"):
            return True, f"{rel} is referenced in pipelines.yaml"
        return False, f"{cid} is in no pipeline step and not listed under standalone in pipelines/pipelines.yaml"
    if name == "index_fresh":
        cj = ctx.root / "docs" / "components.json"
        try:
            nodes = json.loads(cj.read_text(encoding="utf-8")).get("nodes") or []
            fresh = cj.stat().st_mtime + 1 >= path.stat().st_mtime
        except (OSError, ValueError, AttributeError):
            return False, "docs/components.json unreadable"
        if not any(n.get("path") == rel or n.get("id") == cid for n in nodes if isinstance(n, dict)):
            return False, f"{rel} not in docs/components.json (run scripts/harness_index.py --write)"
        if not fresh:
            return False, f"docs/components.json is older than {rel} (run scripts/harness_index.py --write)"
        return True, "index regenerated after the component changed"
    return False, f"unknown builtin {name}"


def referenced_components(cfg):
    out = set()
    for pipe in (cfg.get("pipelines") or {}).values():
        for st in pipe.get("steps") or []:
            run = str(st.get("run") or "").split()
            if run and ":" in run[0]:
                kind, name = run[0].split(":", 1)
                out.add(f"{kind}:{name}")
        own = pipe.get("owner_agent")
        if own:
            out.add(f"agent:{own}")
        for s in (pipe.get("triggers") or {}).get("slash") or []:
            out.add(f"skill:{s}")  # the skill whose /command starts the pipeline is its entry point
    return out


# ---------------------------------------------------------------- classifier

def _compile(patterns):
    out = []
    for p in patterns or []:
        try:
            out.append((p, re.compile(p)))
        except re.error:
            continue
    return out


def classify_text(text, cfg):
    d = cfg["defaults"]
    sw, ww, nw = float(d.get("strong_weight", 0.6)), float(d.get("weak_weight", 0.15)), float(d.get("negative_weight", 0.6))
    t = (text or "").strip()
    cands = []
    slash = re.match(r"^/(?:harness:)?([\w-]+)", t)
    for pid, pipe in cfg["pipelines"].items():
        trig = pipe.get("triggers") or {}
        if slash and slash.group(1) in (trig.get("slash") or []):
            cands.append({"pipeline": pid, "score": 0.95, "why": [f"/{slash.group(1)}"]})
            continue
        why, score = [], 0.0
        strong = [p for p, rx in _compile(trig.get("strong")) if rx.search(t)]
        weak = [p for p, rx in _compile(trig.get("weak")) if rx.search(t)]
        neg = [p for p, rx in _compile(trig.get("negative")) if rx.search(t)]
        if strong:
            score += sw + 0.1 * (min(len(strong), 3) - 1)
            why += [f"strong:{p}" for p in strong]
        if weak:
            score += ww * min(len(weak), 3)
            why += [f"weak:{p}" for p in weak]
        if neg:
            score -= nw * len(neg)
            why += [f"negative:{p}" for p in neg]
        if score > 0:
            cands.append({"pipeline": pid, "score": round(min(score, 0.95), 3), "why": why})
    cands.sort(key=lambda c: -c["score"])
    return cands


def event_candidates(ev, cfg, env=None):
    env = os.environ if env is None else env
    etype = ev.get("event") or ev.get("type") or ev.get("hook_event_name")
    path = None
    for k in ("path", "file_path", "filePath", "file", "changed_path"):
        if isinstance(ev.get(k), str) and ev.get(k):
            path = ev[k]
            break
    cands = []
    for pid, pipe in cfg["pipelines"].items():
        trig = pipe.get("triggers") or {}
        if etype and etype in (trig.get("events") or []):
            cands.append({"pipeline": pid, "score": 0.95, "why": [f"event:{etype}"]})
    if not cands and path:
        kind = classify_path(path)
        if kind == "inbox":
            cands.append({"pipeline": "intake", "score": 0.9, "why": [f"path in inbox: {path}"]})
        elif kind == "component":
            cands.append({"pipeline": "new-component", "score": 0.9, "why": [f"harness component: {path}"]})
    return cands


def classify_path(path):
    p = pathlib.Path(_norm(path))
    if p.name.startswith("."):
        return None
    parts = p.parts
    if "inbox" in parts[:-1]:
        return "inbox"
    hr = harness_root_of(p)
    if hr is not None:
        try:
            rel = p.relative_to(hr).as_posix()
        except ValueError:
            return None
        if component_id(rel):
            return "component"
    return None


def match(arg, cfg, env=None):
    d = cfg["defaults"]
    ev = None
    if isinstance(arg, dict):
        ev = arg
    elif isinstance(arg, str) and arg.strip().startswith("{"):
        try:
            ev = json.loads(arg)
        except ValueError:
            ev = None
    if ev is not None and isinstance(ev, dict):
        cands = event_candidates(ev, cfg, env)
        text = ev.get("prompt") if isinstance(ev.get("prompt"), str) else None
        if not cands and text:
            cands = classify_text(text, cfg)
    else:
        text = str(arg or "")
        if len(text.strip()) < TRIVIAL_LEN or TRIVIAL.match(text):
            return {"pipeline": None, "confidence": 0.0, "abstain": True, "reason": "trivial input", "candidates": []}
        cands = classify_text(text, cfg)
    if not cands:
        return {"pipeline": None, "confidence": 0.0, "abstain": True, "reason": "no rule matched; the orchestrator decides",
                "candidates": []}
    top = cands[0]
    second = cands[1]["score"] if len(cands) > 1 else 0.0
    out = {"pipeline": top["pipeline"], "confidence": top["score"], "abstain": False, "reason": "; ".join(top["why"]),
           "candidates": cands[:4]}
    if top["score"] < float(d.get("min_confidence", 0.6)):
        out.update(pipeline=None, abstain=True, reason=f"low confidence ({top['score']} for {top['pipeline']}); the orchestrator decides")
    elif top["score"] - second < float(d.get("margin", 0.15)):
        out.update(pipeline=None, abstain=True,
                   reason=f"ambiguous: {top['pipeline']} {top['score']} vs {cands[1]['pipeline']} {second}; the orchestrator decides")
    if out["pipeline"]:
        pipe = cfg["pipelines"][out["pipeline"]]
        out["title"] = pipe.get("title")
        out["steps"] = [{"id": s["id"], "run": s.get("run"), "required": bool(s.get("required"))} for s in pipe.get("steps", [])]
    return out


# ---------------------------------------------------------------- commands

def start(pid, scope, params=None, env=None, source="cli", cfg=None):
    env = os.environ if env is None else env
    cfg = cfg or load_config(env)
    if pid not in cfg["pipelines"]:
        raise Refused(f"unknown pipeline {pid!r}; known: {', '.join(sorted(cfg['pipelines']))}")
    pipe = cfg["pipelines"][pid]
    root = project_root(scope)
    params = dict(params or {})
    allowed = set(pipe.get("params") or [])
    extra = set(params) - allowed
    if extra:
        raise Refused(f"pipeline {pid} takes params {sorted(allowed) or 'none'}, got {sorted(extra)}")
    state = load_state(root)
    for r in active_runs(state):
        if r.get("pipeline") == pid and (r.get("params") or {}) == params:
            return r, False
    n = now_utc()
    run = {"run_id": new_id("pr"), "pipeline": pid, "status": "active", "started_at": n.isoformat(),
           "started_ts": n.timestamp(), "scope": str(root), "params": params, "marks": {}, "source": source,
           "progress_baseline": progress_hash(root)}
    ev = append_event("pipeline_started", root, env, pipeline=pid, run_id=run["run_id"], params=params, source=source,
                      labels=["pipeline", f"pipeline:{pid}"], content=pipe.get("title"),
                      pointers=[str(state_file(root))])
    run["started_event"] = ev["id"]
    state["runs"].append(run)
    save_state(root, state)
    write_block(root, run, pipe)
    run["progress_baseline"] = progress_hash(root)
    save_state(root, state)
    if params.get("file"):
        for q in pending_queue(env, root):
            if q.get("kind") == "inbox_file" and _norm(q.get("path")) in (_norm(params["file"]), _norm(root / str(params["file"]))):
                ack_queue(q["id"], env, reason=f"started {run['run_id']}")
    if params.get("component"):
        for q in pending_queue(env, root):
            if q.get("kind") in ("component_new", "component_changed") and str(q.get("path", "")).endswith(str(params["component"])):
                ack_queue(q["id"], env, reason=f"started {run['run_id']}")
    return run, True


def pick_run(state, run_id=None, step=None, cfg=None):
    runs = active_runs(state)
    if run_id:
        r = next((r for r in state.get("runs", []) if r.get("run_id") == run_id), None)
        if r is None:
            raise Refused(f"no run {run_id}")
        return r
    if step and cfg:
        runs = [r for r in runs if any(s["id"] == step for s in cfg["pipelines"].get(r["pipeline"], {}).get("steps", []))]
    if not runs:
        raise Refused("no active pipeline run here" + (f" with a step {step!r}" if step else ""))
    return sorted(runs, key=lambda r: r.get("started_ts") or 0)[-1]


def mark(step, event_id, scope, run_id=None, env=None, cfg=None):
    env = os.environ if env is None else env
    cfg = cfg or load_config(env)
    root = project_root(scope)
    state = load_state(root)
    run = pick_run(state, run_id, step, cfg)
    pipe = cfg["pipelines"][run["pipeline"]]
    st = next((s for s in pipe["steps"] if s["id"] == step), None)
    if st is None:
        raise Refused(f"pipeline {run['pipeline']} has no step {step!r}")
    ok, ev, why = validate_mark(Ctx(root, run, cfg, env), st, event_id)
    if not ok:
        raise Refused(f"refused: {why}")
    run.setdefault("marks", {}).setdefault(step, [])
    if event_id not in run["marks"][step]:
        run["marks"][step].append(event_id)
    save_state(root, state)
    append_event("pipeline_step", root, env, pipeline=run["pipeline"], run_id=run["run_id"], step=step,
                 evidence=[event_id], parent_event=event_id, labels=["pipeline", f"pipeline:{run['pipeline']}"])
    s = summarize(root, run, cfg, env)
    write_block(root, run, pipe, s["steps"])
    return s


def check(scope, run_id=None, env=None, cfg=None, include_stale=True):
    env = os.environ if env is None else env
    cfg = cfg or load_config(env)
    root = project_root(scope)
    state = load_state(root)
    runs = [pick_run(state, run_id)] if run_id else active_runs(state)
    out = []
    for r in runs:
        if not include_stale and is_stale(r, cfg):
            continue
        s = summarize(root, r, cfg, env)
        s["stale"] = is_stale(r, cfg)
        out.append(s)
    return out


def finish(scope, run_id=None, env=None, cfg=None):
    env = os.environ if env is None else env
    cfg = cfg or load_config(env)
    root = project_root(scope)
    state = load_state(root)
    run = pick_run(state, run_id)
    s = summarize(root, run, cfg, env)
    if not s["ok"]:
        return s, False
    run["status"] = "finished"
    run["finished_at"] = now_utc().isoformat()
    save_state(root, state)
    append_event("pipeline_finished", root, env, pipeline=run["pipeline"], run_id=run["run_id"], outcome="worked",
                 items=[k for k, v in s["steps"].items() if v["ok"]], labels=["pipeline", f"pipeline:{run['pipeline']}"])
    write_block(root, run, cfg["pipelines"][run["pipeline"]], s["steps"])
    return s, True


def abandon(scope, run_id, reason, env=None, cfg=None):
    env = os.environ if env is None else env
    cfg = cfg or load_config(env)
    if not reason or not reason.strip():
        raise Refused("abandon needs --reason (the user's explicit decision)")
    root = project_root(scope)
    state = load_state(root)
    run = pick_run(state, run_id)
    s = summarize(root, run, cfg, env)
    run["status"] = "abandoned"
    run["finished_at"] = now_utc().isoformat()
    run["abandon_reason"] = reason
    save_state(root, state)
    append_event("pipeline_finished", root, env, pipeline=run["pipeline"], run_id=run["run_id"], outcome="abandoned",
                 justification=reason, items=s["missing"], labels=["pipeline", f"pipeline:{run['pipeline']}", "abandoned"])
    write_block(root, run, cfg["pipelines"][run["pipeline"]], s["steps"])
    return run


# ---------------------------------------------------------------- queue

def queue_dir(env):
    return data_dir(env) / "queue"


def _read_jsonl(path):
    out = []
    try:
        with open(path, encoding="utf-8", errors="replace") as f:
            for line in f:
                try:
                    rec = json.loads(line)
                except ValueError:
                    continue
                if isinstance(rec, dict):
                    out.append(rec)
    except OSError:
        pass
    return out


def queue_entries(env):
    return _read_jsonl(queue_dir(env) / "inbox.jsonl")


def acked_ids(env):
    return {r.get("id") for r in _read_jsonl(queue_dir(env) / "acked.jsonl")}


def manifest_names(project):
    try:
        data = json.loads((pathlib.Path(project) / "knowledge" / "manifest.json").read_text(encoding="utf-8"))
        return {s.get("original_name") for s in data.get("sources") or [] if isinstance(s, dict)}
    except (OSError, ValueError, AttributeError):
        return set()


def pending_queue(env, scope=None):
    acked = acked_ids(env)
    seen, out = set(), []
    root_s = _norm(scope) if scope else None
    names_cache = {}
    for q in queue_entries(env):
        if q.get("id") in acked:
            continue
        key = (q.get("kind"), q.get("path"))
        if key in seen:
            continue
        seen.add(key)
        if root_s and _norm(q.get("project") or "") != root_s:
            continue
        if q.get("kind") == "inbox_file":
            p = pathlib.Path(q.get("path") or "")
            if not p.is_file():
                continue
            proj = q.get("project") or ""
            if proj not in names_cache:
                names_cache[proj] = manifest_names(proj)
            if p.name in names_cache[proj]:
                continue  # already registered by intake
        out.append(q)
    return out


def enqueue(kind, path, project, env=None, source="hook", log=True, **extra):
    """Append a queue entry unless an unacked entry for the same (kind, path) exists. Returns the entry or None."""
    env = os.environ if env is None else env
    path = _norm(path)
    project = _norm(project)
    acked = acked_ids(env)
    for q in queue_entries(env):
        if q.get("kind") == kind and q.get("path") == path and q.get("id") not in acked:
            return None
    try:
        stt = os.stat(path)
        size, mtime = stt.st_size, stt.st_mtime
    except OSError:
        size, mtime = None, None
    entry = {"id": new_id("q"), "ts": now_utc().isoformat(), "kind": kind, "path": path, "project": project,
             "source": source, "size": size, "mtime": mtime,
             "pipeline": "intake" if kind == "inbox_file" else "new-component"}
    entry.update(extra)
    qd = queue_dir(env)
    qd.mkdir(parents=True, exist_ok=True)
    _common().locked_append(qd / "inbox.jsonl", json.dumps(entry, ensure_ascii=False) + "\n")
    if log:
        etype = "inbox_file_detected" if kind == "inbox_file" else "component_detected"
        append_event(etype, project, env, pointers=[path], items=[entry["id"]], source=source,
                     content=os.path.basename(path), labels=["pipeline", "queue", kind],
                     change=extra.get("change"), component=extra.get("component"))
    return entry


def ack_queue(qid, env=None, reason=None):
    env = os.environ if env is None else env
    qd = queue_dir(env)
    qd.mkdir(parents=True, exist_ok=True)
    _common().locked_append(qd / "acked.jsonl", json.dumps({"id": qid, "ts": now_utc().isoformat(), "reason": reason},
                                                           ensure_ascii=False) + "\n")


def scan_inbox(project, env=None, source="scan", limit=50):
    env = os.environ if env is None else env
    project = pathlib.Path(_norm(project))
    inbox = project / "inbox"
    if not inbox.is_dir():
        return []
    names = manifest_names(project)
    new = []
    for p in sorted(inbox.rglob("*")):
        if len(new) >= limit:
            break
        if not p.is_file() or any(part.startswith(".") for part in p.relative_to(inbox).parts):
            continue
        if p.name in names:
            continue
        e = enqueue("inbox_file", p, project, env, source=source)
        if e:
            new.append(e)
    return new


# ---------------------------------------------------------------- lint

def slugify(heading):
    s = heading.strip().lower()
    s = re.sub(r"[`*_()\[\],.:;!?'\"/]", "", s)
    s = re.sub(r"\s+", "-", s.strip())
    return s


def lint(cfg, root=ROOT):
    errors, warnings = [], []
    lib = cfg.get("evidence_library") or {}
    pending = cfg.get("pending_components") or {}
    standalone = cfg.get("standalone") or {}
    try:
        ver = (root / "docs" / "VERIFICATION.md").read_text(encoding="utf-8")
        slugs = [slugify(m.group(1)) for m in re.finditer(r"(?m)^#{1,6}\s+(.+)$", ver)]
    except OSError:
        slugs = []
        warnings.append("docs/VERIFICATION.md missing; verification anchors not checked")

    def check_matcher(where, m):
        if isinstance(m, str):
            if not m.startswith("lib:") or m[4:] not in lib:
                errors.append(f"{where}: unknown evidence {m!r}")
            return
        if not isinstance(m, dict):
            errors.append(f"{where}: matcher must be a mapping or lib:<name>")
            return
        kind = matcher_kind(m)
        if not kind:
            errors.append(f"{where}: matcher needs one of event/file/json/store/builtin")
            return
        bad = set(m) - MATCHER_KEYS[kind]
        if bad:
            errors.append(f"{where}: unknown {kind} matcher keys {sorted(bad)}")
        for k in ("content_re", "contains", "not_contains"):
            if m.get(k):
                try:
                    re.compile(m[k])
                except re.error as e:
                    errors.append(f"{where}: bad regex in {k}: {e}")
        for k, v in (m.get("where") or {}).items():
            for vv in v if isinstance(v, list) else [v]:
                if isinstance(vv, str) and vv.startswith("re:"):
                    try:
                        re.compile(vv[3:])
                    except re.error as e:
                        errors.append(f"{where}: bad regex in where.{k}: {e}")
        if kind == "builtin" and m["builtin"] not in BUILTINS:
            errors.append(f"{where}: unknown builtin {m['builtin']!r}")
        if kind == "json" and not m.get("has"):
            errors.append(f"{where}: json matcher needs `has`")

    for name, m in lib.items():
        check_matcher(f"evidence_library.{name}", m)

    def ref_exists(ref):
        if ref == "user":
            return True
        head = ref.split()[0]
        if ":" not in head:
            return False
        kind, name = head.split(":", 1)
        if kind == "skill":
            return (root / "skills" / name / "SKILL.md").is_file()
        if kind == "agent":
            return (root / "agents" / f"{name}.md").is_file()
        if kind in ("script", "hook"):
            return (root / name).is_file() or (root / "hooks" / name).is_file()
        return False

    for pid, pipe in (cfg.get("pipelines") or {}).items():
        if not isinstance(pipe, dict):
            errors.append(f"{pid}: not a mapping")
            continue
        bad = set(pipe) - PIPELINE_KEYS
        if bad:
            warnings.append(f"{pid}: unknown keys {sorted(bad)}")
        if pipe.get("autostart", "never") not in ("never", "on_event"):
            errors.append(f"{pid}: autostart must be never|on_event")
        trig = pipe.get("triggers") or {}
        for k in ("strong", "weak", "negative"):
            for p in trig.get(k) or []:
                try:
                    re.compile(p)
                except re.error as e:
                    errors.append(f"{pid}.triggers.{k}: bad regex {p!r}: {e}")
        if not any(trig.get(k) for k in ("strong", "events", "slash")):
            errors.append(f"{pid}: no trigger (strong / events / slash)")
        steps = pipe.get("steps") or []
        if not steps:
            errors.append(f"{pid}: no steps")
        seen = []
        if pipe.get("client_bound") and not any(
                s.get("required") and any(e == "lib:tier_v" for e in s.get("evidence") or []) for s in steps):
            errors.append(f"{pid}: client_bound but no required tier-V verify step (evidence lib:tier_v)")
        if not any(s.get("required") for s in steps):
            errors.append(f"{pid}: no required step")
        for st in steps:
            sid = st.get("id")
            where = f"{pid}.{sid}"
            if not sid or not re.fullmatch(r"[a-z0-9][a-z0-9-]*", str(sid)):
                errors.append(f"{pid}: bad step id {sid!r}")
            if sid in seen:
                errors.append(f"{where}: duplicate step id")
            bad = set(st) - STEP_KEYS
            if bad:
                errors.append(f"{where}: unknown keys {sorted(bad)}")
            if not isinstance(st.get("required"), bool):
                errors.append(f"{where}: `required` must be true or false")
            for dep in st.get("after") or []:
                if dep not in seen:
                    errors.append(f"{where}: after {dep!r} is not an earlier step")
            run = st.get("run")
            if not run:
                errors.append(f"{where}: no `run`")
            elif not ref_exists(str(run)):
                head = str(run).split()[0]
                if head in pending:
                    warnings.append(f"{where}: {head} is pending ({pending[head]})")
                else:
                    errors.append(f"{where}: run target {run!r} does not exist")
            if st.get("required") and not st.get("evidence"):
                errors.append(f"{where}: required step without evidence")
            for i, m in enumerate(st.get("evidence") or []):
                check_matcher(f"{where}.evidence[{i}]", m)
            v = st.get("verification")
            if not v:
                warnings.append(f"{where}: no verification link")
            elif slugs:
                anchor = str(v).split("#", 1)[1] if "#" in str(v) else ""
                if not anchor or not any(s.startswith(anchor) for s in slugs):
                    errors.append(f"{where}: verification anchor {v!r} matches no heading in docs/VERIFICATION.md")
            for k in ("pre", "post"):
                if not st.get(k):
                    warnings.append(f"{where}: no {k}condition")
            seen.append(sid)
    refs = referenced_components(cfg)
    for d, kind in ((root / "skills", "skill"), (root / "agents", "agent")):
        if not d.is_dir():
            continue
        names = sorted(p.parent.name for p in d.glob("*/SKILL.md")) if kind == "skill" else sorted(p.stem for p in d.glob("*.md"))
        for n in names:
            cid = f"{kind}:{n}"
            if cid not in refs and cid not in standalone:
                errors.append(f"{cid} is in no pipeline and not listed under standalone")
    for cid in standalone:
        kind, _, name = cid.partition(":")
        path = root / ("skills/" + name + "/SKILL.md" if kind == "skill" else "agents/" + name + ".md" if kind == "agent" else name)
        if not path.is_file():
            errors.append(f"standalone {cid}: no such component")
        if cid in refs and kind == "skill":
            warnings.append(f"standalone {cid} is also a pipeline step")
    for cid in pending:
        kind, _, name = cid.partition(":")
        path = root / ("skills/" + name + "/SKILL.md" if kind == "skill" else "agents/" + name + ".md" if kind == "agent" else name)
        if path.is_file():
            warnings.append(f"pending {cid} now exists; remove it from pending_components")
    return errors, warnings


# ---------------------------------------------------------------- CLI

def _print(obj, as_json):
    if as_json:
        print(json.dumps(obj, ensure_ascii=False, indent=2))


def format_summary(s):
    lines = [f"{s['pipeline']} run {s['run_id']} ({s['scope']}) — {'COMPLETE' if s['ok'] else 'INCOMPLETE'}"
             + (" [stale]" if s.get("stale") else "")]
    for sid, r in s["steps"].items():
        box = "☑" if r["ok"] else "☐"
        req = "required" if r["required"] else "optional"
        tail = f" ← {r['via']}" if r["ok"] else (f" ({'; '.join(r['detail'][:2])})" if r["detail"] else "")
        lines.append(f"  {box} {sid} [{req}]{tail}")
    if s["missing"]:
        lines.append("  missing required: " + ", ".join(s["missing"]))
    if s["order_violations"]:
        lines.append(("  ORDER (strict): " if s["strict_order"] else "  order warnings: ") + "; ".join(s["order_violations"]))
    if s.get("next"):
        lines.append(f"  next: {s['next']['step']} → {s['next']['run']}")
    return "\n".join(lines)


def main(argv=None):
    ap = argparse.ArgumentParser(prog="pipeline.py", description=__doc__.split("\n\n")[0])
    sub = ap.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("match"); p.add_argument("input", nargs="?", default="-")
    p = sub.add_parser("start"); p.add_argument("pipeline"); p.add_argument("--scope", default=None)
    p.add_argument("--param", action="append", default=[]); p.add_argument("--source", default="cli")
    for name in ("status", "check", "finish"):
        p = sub.add_parser(name); p.add_argument("--scope", default=None); p.add_argument("--run", default=None)
        p.add_argument("--json", action="store_true")
    p = sub.add_parser("mark"); p.add_argument("step"); p.add_argument("--evidence", required=True)
    p.add_argument("--run", default=None); p.add_argument("--scope", default=None); p.add_argument("--json", action="store_true")
    p = sub.add_parser("abandon"); p.add_argument("--run", required=True); p.add_argument("--reason", required=True)
    p.add_argument("--scope", default=None)
    p = sub.add_parser("queue"); qs = p.add_subparsers(dest="qcmd", required=True)
    q = qs.add_parser("scan"); q.add_argument("project"); q.add_argument("--source", default="scan")
    q = qs.add_parser("list"); q.add_argument("--scope", default=None); q.add_argument("--json", action="store_true")
    q = qs.add_parser("ack"); q.add_argument("id"); q.add_argument("--reason", default=None)
    p = sub.add_parser("lint"); p.add_argument("--json", action="store_true")
    a = ap.parse_args(argv)
    env = os.environ
    try:
        cfg = load_config(env)
    except (OSError, ValueError) as e:
        print(f"error: cannot read {pipelines_path(env)}: {e}", file=sys.stderr)
        return 2
    scope = getattr(a, "scope", None) or env.get("CLAUDE_PROJECT_DIR") or os.getcwd()
    try:
        if a.cmd == "match":
            text = sys.stdin.read() if a.input == "-" else a.input
            print(json.dumps(match(text, cfg, env), ensure_ascii=False, indent=2))
            return 0
        if a.cmd == "start":
            params = {}
            for kv in a.param:
                if "=" not in kv:
                    raise Refused(f"--param needs k=v, got {kv!r}")
                k, v = kv.split("=", 1)
                params[k.strip()] = v
            run, created = start(a.pipeline, scope, params, env, source=a.source, cfg=cfg)
            pipe = cfg["pipelines"][a.pipeline]
            print(("started" if created else "already active") + f": {run['run_id']} ({a.pipeline}) in {run['scope']}")
            for i, s in enumerate(pipe["steps"], 1):
                print(f"  {i}. {s['id']} — {s.get('run')} ({'required' if s.get('required') else 'optional'})")
            return 0
        if a.cmd in ("status", "check"):
            res = check(scope, a.run, env, cfg)
            if a.json:
                _print(res, True)
            elif not res:
                print("no active pipeline run in " + str(project_root(scope)))
            else:
                print("\n".join(format_summary(s) for s in res))
            if a.cmd == "check":
                return 1 if any(not s["ok"] for s in res) else 0
            return 0
        if a.cmd == "mark":
            s = mark(a.step, a.evidence, scope, a.run, env, cfg)
            print(json.dumps(s, ensure_ascii=False, indent=2) if a.json else format_summary(s))
            return 0
        if a.cmd == "finish":
            s, ok = finish(scope, a.run, env, cfg)
            print(format_summary(s))
            if not ok:
                print("not finished: required steps missing" + (" or strict order violated" if s["order_violations"] else ""),
                      file=sys.stderr)
                return 1
            print("finished")
            return 0
        if a.cmd == "abandon":
            run = abandon(scope, a.run, a.reason, env, cfg)
            print(f"abandoned {run['run_id']}: {a.reason}")
            return 0
        if a.cmd == "queue":
            if a.qcmd == "scan":
                new = scan_inbox(a.project, env, source=a.source)
                print(f"{len(new)} new inbox file(s) queued" + "".join(f"\n  {e['id']} {e['path']}" for e in new))
                return 0
            if a.qcmd == "list":
                items = pending_queue(env, project_root(a.scope) if a.scope else None)
                if a.json:
                    _print(items, True)
                else:
                    print("\n".join(f"{q['id']} {q['kind']} {q['path']}" for q in items) or "queue empty")
                return 0
            if a.qcmd == "ack":
                ack_queue(a.id, env, a.reason)
                print(f"acked {a.id}")
                return 0
        if a.cmd == "lint":
            errors, warnings = lint(cfg)
            if a.json:
                _print({"errors": errors, "warnings": warnings}, True)
            else:
                for w in warnings:
                    print("warning: " + w)
                for e in errors:
                    print("ERROR: " + e)
                print(f"{len(errors)} error(s), {len(warnings)} warning(s)")
            return 1 if errors else 0
    except Refused as e:
        print(str(e), file=sys.stderr)
        return 2
    return 2


if __name__ == "__main__":
    sys.exit(main())
