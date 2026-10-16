#!/usr/bin/env python3
"""Run an eval area's deterministic tasks and write an EvalRun JSON for scripts/eval_gate.py.

    python3 -I scripts/run_evals.py --area harness                      # all tasks, result to $HARNESS_DATA
    python3 -I scripts/run_evals.py --area harness --split train        # train | holdout | all (default)
    python3 -I scripts/run_evals.py --area harness --out run.json       # or --out - for stdout
    python3 -I scripts/run_evals.py --area harness --baseline OLD.json  # then run eval_gate against OLD.json
    python3 -I scripts/run_evals.py --area harness --task harness-003   # one task (repeatable)
    python3 -I scripts/run_evals.py --area harness --lock-hash          # print each task's lock hash; runs nothing

Stdlib only; run with `python3 -I`. Only tasks with shell-free, deterministic `input.steps` are run
here (the `harness` area today). Model-produced areas need a producer and a judge and are not run by
this script.

Task file (evals/<area>/tasks/<id>.yaml; full reference in evals/harness/README.md):

    id, area, rubric, split (train|holdout), status (draft|locked), locked (true), lock_sha256
    input.files   [{path, content, header, repeat}]  written under a fresh temp dir ($WORK) before the steps
    input.env     {NAME: value}               extra environment for every step
    input.steps   [{id, run: "argv as a shell-like string" | write: PATH, content, append, stdin, cwd,
                    env, timeout}]            run in order; no shell is involved
    expected_checks [{id, kind, step, ...}]   kinds: exit_code, stdout_contains, stdout_not_contains,
                                              stderr_contains, stdout_empty, json, file_exists,
                                              file_absent, file_contains, file_not_contains
    criteria      [{id, dimension, ...}]      which dimensions the task is scored on

Substitutions in commands, stdin, env and file contents: ${ROOT} (harness root), ${WORK}, ${DATA}
($HARNESS_DATA of the task), ${HOME}, ${PY} (this Python), ${NOW} / ${NOW+N} / ${NOW-N} (epoch
seconds), ${NOW_ISO} / ${NOW_ISO+N} (UTC ISO 8601), ${TODAY}.

Each step runs with a clean environment: HOME, HARNESS_DATA and HARNESS_STATE point inside $WORK,
every other HARNESS_* variable is dropped, so no task can read or write the user's real data.

Scores per task: correctness 1.0 when every expected check passes, else 0.0; time = wall-clock
milliseconds of the steps (`units.time` is "ms" in the result). judge = "deterministic".

Locking: only the user locks a task, by setting `status: locked` and pasting the value printed by
`--lock-hash` into `lock_sha256:`. The hash covers the task file without its top-level
`lock_sha256:` and `status:` lines (the eval set hash uses the same body, so locking alone does not
force a new baseline).
If a task has a non-empty lock_sha256 that no longer matches its file, the runner refuses to run
anything (exit 2): an edited locked task must be re-locked by the user in a reviewed commit.

Exit codes: 0 every task passed (and the gate accepted, with --baseline); 1 a task failed or the
gate rejected; 2 usage, task-file or lock error.
"""
import argparse
import datetime as dt
import hashlib
import importlib.util
import json
import os
import pathlib
import re
import shlex
import shutil
import subprocess
import sys
import tempfile
import time

ROOT = pathlib.Path(__file__).resolve().parent.parent
RUNNER_VERSION = "1"
JUDGE = "deterministic"
PRODUCER = "harness-code"           # the scripts/hooks under test; no model produces the outputs
DEFAULT_STEP_TIMEOUT = 60
DEFAULT_GATE_TOLERANCE = ["time=50%"]   # subprocess wall-clock is noisy; correctness stays strict
POLICY_DIRS = ("scripts", "hooks", "skills", "agents")
CHECK_KINDS = {"exit_code", "stdout_contains", "stdout_not_contains", "stderr_contains", "stdout_empty",
               "json", "file_exists", "file_absent", "file_contains", "file_not_contains"}
JSON_OPS = ("equals", "contains", "not_contains", "len_lte", "len_gte", "len_equals", "any_match",
            "none_match", "exists", "gte", "lte")


class TaskError(Exception):
    pass


# ---------------------------------------------------------------- YAML subset
# Block maps and lists, one-line flow [..] / {..}, quoted scalars, comments, and block scalars
# (| |- |+ >) whose lines are kept verbatim (indentation, blank lines, and '#' inside them).

class YamlError(TaskError):
    pass


def _strip_comment(s):
    quote, i = None, 0
    while i < len(s):
        ch = s[i]
        if quote == '"':
            if ch == "\\":
                i += 1
            elif ch == '"':
                quote = None
        elif quote == "'":
            if ch == "'":
                quote = None
        elif ch in "\"'" and (i == 0 or s[i - 1] in " \t[{,:"):
            quote = ch
        elif ch == "#" and (i == 0 or s[i - 1] in " \t"):
            return s[:i].rstrip()
        i += 1
    return s.rstrip()


def _resolve_plain(s):
    s = s.strip()
    if s in ("", "~", "null", "Null", "NULL"):
        return None
    if s in ("true", "True", "TRUE"):
        return True
    if s in ("false", "False", "FALSE"):
        return False
    if re.fullmatch(r"[-+]?\d+", s):
        return int(s)
    if re.fullmatch(r"[-+]?(\d+\.\d*|\.\d+)([eE][-+]?\d+)?", s):
        return float(s)
    return s


class _Flow:
    """Recursive-descent parser for one-line flow values and quoted scalars."""

    def __init__(self, s):
        self.s, self.i = s, 0

    def ws(self):
        while self.i < len(self.s) and self.s[self.i] in " \t":
            self.i += 1

    def value(self, in_flow):
        self.ws()
        if self.i >= len(self.s):
            return None
        ch = self.s[self.i]
        if ch == "[":
            return self.seq()
        if ch == "{":
            return self.mapping()
        if ch in "\"'":
            return self.quoted()
        start = self.i
        stop = ",]}" if in_flow else ""
        while self.i < len(self.s) and self.s[self.i] not in stop:
            if in_flow and self.s[self.i] == ":" and self.s[self.i + 1:self.i + 2] in (" ", ""):
                break
            self.i += 1
        return _resolve_plain(self.s[start:self.i])

    def quoted(self):
        q = self.s[self.i]
        if q == '"':
            try:
                val, end = json.decoder.scanstring(self.s, self.i + 1)
            except ValueError as e:
                raise YamlError(f"bad double-quoted string: {self.s}: {e}")
            self.i = end
            return val
        out, j = [], self.i + 1
        while True:
            k = self.s.find("'", j)
            if k < 0:
                raise YamlError(f"unclosed single-quoted string: {self.s}")
            out.append(self.s[j:k])
            if self.s[k + 1:k + 2] == "'":
                out.append("'")
                j = k + 2
                continue
            self.i = k + 1
            return "".join(out)

    def expect(self, ch):
        self.ws()
        if self.i >= len(self.s) or self.s[self.i] != ch:
            raise YamlError(f"expected {ch!r} at column {self.i} in: {self.s}")
        self.i += 1

    def seq(self):
        self.expect("[")
        out = []
        self.ws()
        if self.s[self.i:self.i + 1] == "]":
            self.i += 1
            return out
        while True:
            out.append(self.value(True))
            self.ws()
            if self.s[self.i:self.i + 1] == ",":
                self.i += 1
                self.ws()
                if self.s[self.i:self.i + 1] == "]":
                    self.i += 1
                    return out
                continue
            self.expect("]")
            return out

    def mapping(self):
        self.expect("{")
        out = {}
        self.ws()
        if self.s[self.i:self.i + 1] == "}":
            self.i += 1
            return out
        while True:
            key = self.value(True)
            self.expect(":")
            out[str(key)] = self.value(True)
            self.ws()
            if self.s[self.i:self.i + 1] == ",":
                self.i += 1
                self.ws()
                if self.s[self.i:self.i + 1] == "}":
                    self.i += 1
                    return out
                continue
            self.expect("}")
            return out


def _scalar(rest):
    rest = rest.strip()
    if rest[:1] in ("[", "{", '"', "'"):
        f = _Flow(rest)
        val = f.value(False)
        f.ws()
        if f.i != len(rest):
            raise YamlError(f"trailing text after value: {rest}")
        return val
    return _resolve_plain(rest)


def _key_split(s):
    if s[:1] in "\"'":
        f = _Flow(s)
        key = f.quoted()
        rest = s[f.i:]
        if rest.startswith(":") and (len(rest) == 1 or rest[1] in " \t"):
            return str(key), rest[1:].strip()
        return None
    m = re.match(r"^([^\s\[\]{},:#'\"][^:]*?):(?:[ \t]+(.*)|)$", s)
    if not m:
        return None
    return m.group(1).strip(), (m.group(2) or "").strip()


def _is_item(content):
    return content == "-" or content.startswith("- ")


class _Yaml:
    def __init__(self, text):
        if re.search(r"^ *\t", text, re.M):
            raise YamlError("tabs are not allowed for indentation")
        self.raw = text.split("\n")
        self.lines = []          # [indent, content or None (blank/comment), raw]
        for r in self.raw:
            body = _strip_comment(r) if r.strip() and not r.lstrip().startswith("#") else ""
            if r.strip() in ("---", "..."):
                body = ""
            self.lines.append([len(r) - len(r.lstrip(" ")), body.strip() or None, r])

    def sig(self, i):
        while i < len(self.lines) and self.lines[i][1] is None:
            i += 1
        return i

    def parse(self):
        i = self.sig(0)
        if i >= len(self.lines):
            return None
        val, i = self.node(i, self.lines[i][0])
        i = self.sig(i)
        if i < len(self.lines):
            raise YamlError(f"line {i + 1}: unexpected indentation: {self.lines[i][2].strip()}")
        return val

    def node(self, i, indent):
        if _is_item(self.lines[i][1]):
            return self.seq(i, indent)
        return self.mapping(i, indent)

    def value_after(self, i, indent, rest):
        """Value of 'key: rest' at line i-1 (key at `indent`)."""
        if re.fullmatch(r"[|>][-+]?", rest):
            return self.block_scalar(i, indent, rest)
        if rest:
            return _scalar(rest), i
        j = self.sig(i)
        if j < len(self.lines):
            ind, content, _ = self.lines[j]
            if ind > indent:
                return self.node(j, ind)
            if ind == indent and _is_item(content):
                return self.seq(j, indent)
        return None, i

    def block_scalar(self, i, indent, style):
        body, j = [], i
        while j < len(self.lines):
            r = self.raw_of(j)
            if r.strip() and (len(r) - len(r.lstrip(" "))) <= indent:
                break
            body.append(r)
            j += 1
        trailing = False
        while body and not body[-1].strip():
            trailing = True
            body.pop()
        content_ind = min((len(r) - len(r.lstrip(" ")) for r in body if r.strip()), default=0)
        text_lines = [r[content_ind:] if r.strip() else "" for r in body]
        if style[0] == ">":
            out, para = [], []
            for ln in text_lines:
                if ln:
                    para.append(ln)
                else:
                    out.append(" ".join(para))
                    para = []
            out.append(" ".join(para))
            text = "\n".join(out)
        else:
            text = "\n".join(text_lines)
        if style.endswith("-") or not text_lines:
            pass
        elif style.endswith("+"):
            text += "\n" + ("\n" if trailing else "")
        else:
            text += "\n"
        return text, j

    def raw_of(self, j):
        return self.raw[j].replace("\r", "")

    def mapping(self, i, indent):
        out = {}
        while True:
            i = self.sig(i)
            if i >= len(self.lines):
                return out, i
            ind, content, raw = self.lines[i]
            if ind < indent or (ind == indent and _is_item(content)):
                return out, i
            if ind > indent:
                raise YamlError(f"line {i + 1}: unexpected indentation: {raw.strip()}")
            kv = _key_split(content)
            if kv is None:
                raise YamlError(f"line {i + 1}: expected 'key: value', got: {raw.strip()}")
            key, rest = kv
            if key in out:
                raise YamlError(f"line {i + 1}: duplicate key {key!r}")
            out[key], i = self.value_after(i + 1, indent, rest)

    def seq(self, i, indent):
        out = []
        while True:
            i = self.sig(i)
            if i >= len(self.lines):
                return out, i
            ind, content, raw = self.lines[i]
            if ind != indent or not _is_item(content):
                if ind > indent:
                    raise YamlError(f"line {i + 1}: unexpected indentation: {raw.strip()}")
                return out, i
            rest = content[1:].lstrip(" ")
            if not rest:
                j = self.sig(i + 1)
                if j < len(self.lines) and self.lines[j][0] > indent:
                    val, i = self.node(j, self.lines[j][0])
                else:
                    val, i = None, i + 1
                out.append(val)
                continue
            kv = None if rest[:1] in ("[", "{") else _key_split(rest)
            if kv is not None:
                child = indent + (len(content) - len(rest))
                self.lines[i] = [child, rest, raw]
                val, i = self.mapping(i, child)
                out.append(val)
            else:
                out.append(_scalar(rest))
                i += 1


def yaml_load(text):
    return _Yaml(text.replace("\r\n", "\n")).parse()


# ---------------------------------------------------------------- task files

LOCK_LINE = re.compile(r"^(?:lock_sha256|status)[ \t]*:.*(?:\n|$)", re.M)


def lock_hash(text):
    """sha256 of a task file without its top-level lock_sha256 and status lines (what the user pins
    when locking), so flipping `status: draft` -> `locked` does not change the hash being pinned."""
    body = LOCK_LINE.sub("", text.replace("\r\n", "\n"))
    return hashlib.sha256(body.encode("utf-8")).hexdigest()


def eval_set_hash(paths):
    h = hashlib.sha256()
    for p in sorted(paths, key=lambda x: x.name):
        h.update(p.name.encode("utf-8") + b"\0" + lock_hash(p.read_text(encoding="utf-8")).encode() + b"\n")
    return h.hexdigest()


def task_files(area_dir):
    tdir = area_dir / "tasks"
    return sorted(p for p in tdir.glob("*.yaml") if p.is_file()) if tdir.is_dir() else []


def load_task(path):
    text = path.read_text(encoding="utf-8")
    try:
        t = yaml_load(text)
    except YamlError as e:
        raise TaskError(f"{path.name}: {e}")
    if not isinstance(t, dict):
        raise TaskError(f"{path.name}: top level must be a mapping")
    t["_path"] = path
    t["_lock_actual"] = lock_hash(text)
    validate_task(t, path.name)
    return t


def validate_task(t, where):
    for k in ("id", "area", "split", "input", "expected_checks"):
        if t.get(k) in (None, "", [], {}):
            raise TaskError(f"{where}: missing required field '{k}'")
    if t["split"] not in ("train", "holdout"):
        raise TaskError(f"{where}: split must be train or holdout, got {t['split']!r}")
    if t.get("status", "draft") not in ("draft", "locked"):
        raise TaskError(f"{where}: status must be draft or locked")
    inp = t["input"]
    if not isinstance(inp, dict):
        raise TaskError(f"{where}: input must be a mapping")
    steps = inp.get("steps")
    if not isinstance(steps, list) or not steps:
        raise TaskError(f"{where}: input.steps must be a non-empty list")
    ids = set()
    for n, s in enumerate(steps):
        if not isinstance(s, dict) or not s.get("id"):
            raise TaskError(f"{where}: step {n + 1} needs an id")
        if s["id"] in ids:
            raise TaskError(f"{where}: duplicate step id {s['id']}")
        ids.add(s["id"])
        if ("run" in s) == ("write" in s):
            raise TaskError(f"{where}: step {s['id']} needs exactly one of 'run' or 'write'")
    for f in inp.get("files") or []:
        if not isinstance(f, dict) or not f.get("path") or "content" not in f:
            raise TaskError(f"{where}: every input.files entry needs path and content")
    cids = set()
    for c in t["expected_checks"]:
        if not isinstance(c, dict) or not c.get("id"):
            raise TaskError(f"{where}: every expected check needs an id")
        if c["id"] in cids:
            raise TaskError(f"{where}: duplicate check id {c['id']}")
        cids.add(c["id"])
        if c.get("kind") not in CHECK_KINDS:
            raise TaskError(f"{where}: check {c['id']}: unknown kind {c.get('kind')!r}")
        if c.get("step") is not None and c["step"] not in ids:
            raise TaskError(f"{where}: check {c['id']}: unknown step {c['step']!r}")
        if c["kind"] == "json" and not any(op in c for op in JSON_OPS):
            raise TaskError(f"{where}: check {c['id']}: json check needs one of {', '.join(JSON_OPS)}")


def check_locks(tasks):
    """Return refusal messages for tasks whose lock_sha256 no longer matches the file."""
    bad = []
    for t in tasks:
        want = str(t.get("lock_sha256") or "").strip()
        if want and want != t["_lock_actual"]:
            bad.append(f"{t['id']} ({t['_path'].name}): lock_sha256 {want[:12]}... does not match the file "
                       f"({t['_lock_actual'][:12]}...); the task changed after it was locked")
    return bad


# ---------------------------------------------------------------- running

VAR = re.compile(r"\$\{([A-Z_]+)(?:([+-])(\d+))?\}")


def make_subst(vars_, now):
    def sub(text):
        if not isinstance(text, str):
            return text

        def rep(m):
            name, sign, n = m.group(1), m.group(2), int(m.group(3) or 0)
            off = -n if sign == "-" else n
            if name == "NOW":
                return str(int(now) + off)
            if name == "NOW_ISO":
                return dt.datetime.fromtimestamp(now + off, dt.timezone.utc).isoformat()
            if name not in vars_:
                raise TaskError(f"unknown variable ${{{name}}}")
            if sign:
                raise TaskError(f"offset only allowed on NOW / NOW_ISO: {m.group(0)}")
            return vars_[name]
        return VAR.sub(rep, text)
    return sub


def inside(work, rel):
    p = (work / rel).resolve()
    if p != work and work not in p.parents:
        raise TaskError(f"path escapes the task directory: {rel}")
    return p


def base_env(work):
    env = {k: v for k, v in os.environ.items()
           if k in ("PATH", "SYSTEMROOT", "TMPDIR", "TEMP", "TMP", "LANG", "LC_ALL")}
    env.update(HOME=str(work / "home"), HARNESS_DATA=str(work / "data"),
               HARNESS_STATE=str(work / "state" / "harness-state.json"), NO_COLOR="1",
               PYTHONDONTWRITEBYTECODE="1", PYTHONIOENCODING="utf-8", TZ="UTC")
    env.setdefault("LANG", "C.UTF-8")
    return env


def run_task(t, step_timeout=DEFAULT_STEP_TIMEOUT, keep=False):
    work = pathlib.Path(tempfile.mkdtemp(prefix=f"eval-{t['id']}-")).resolve()
    now = time.time()
    for d in ("data", "home", "state"):
        (work / d).mkdir()
    vars_ = {"ROOT": str(ROOT), "WORK": str(work), "DATA": str(work / "data"), "HOME": str(work / "home"),
             "PY": sys.executable, "TODAY": dt.datetime.fromtimestamp(now, dt.timezone.utc).date().isoformat()}
    sub = make_subst(vars_, now)
    results, errors, elapsed = {}, [], 0.0
    try:
        inp = t["input"]
        for f in inp.get("files") or []:
            p = inside(work, f["path"])
            p.parent.mkdir(parents=True, exist_ok=True)
            content = str(f["content"] if f["content"] is not None else "")
            content = content if f.get("raw") else sub(content)
            header = sub(str(f.get("header") or ""))
            p.write_text(header + content * int(f.get("repeat") or 1), encoding="utf-8")
        env = base_env(work)
        env.update({k: sub(str(v)) for k, v in (inp.get("env") or {}).items()})
        for s in inp["steps"]:
            if "write" in s:
                p = inside(work, sub(s["write"]))
                p.parent.mkdir(parents=True, exist_ok=True)
                with open(p, "a" if s.get("append") else "w", encoding="utf-8") as fh:
                    fh.write(sub(str(s.get("content") or "")))
                results[s["id"]] = {"kind": "write", "exit": 0, "stdout": "", "stderr": ""}
                continue
            argv = [sub(a) for a in shlex.split(str(s["run"]))]
            senv = dict(env)
            senv.update({k: sub(str(v)) for k, v in (s.get("env") or {}).items()})
            cwd = inside(work, sub(s.get("cwd") or "."))
            limit = min(float(s.get("timeout") or step_timeout), float(step_timeout))
            stdin = sub(s["stdin"]) if s.get("stdin") is not None else ""
            t0 = time.perf_counter()
            try:
                p = subprocess.run(argv, input=stdin.encode("utf-8"), cwd=cwd, env=senv,
                                   capture_output=True, timeout=limit)
                res = {"kind": "run", "exit": p.returncode,
                       "stdout": p.stdout.decode("utf-8", "replace"), "stderr": p.stderr.decode("utf-8", "replace")}
            except subprocess.TimeoutExpired:
                res = {"kind": "run", "exit": None, "stdout": "", "stderr": "", "timeout": True}
                errors.append(f"step {s['id']}: timed out after {limit:g}s")
            except OSError as e:
                res = {"kind": "run", "exit": None, "stdout": "", "stderr": str(e)}
                errors.append(f"step {s['id']}: cannot run: {e}")
            elapsed += time.perf_counter() - t0
            results[s["id"]] = res
        last_run = [s["id"] for s in inp["steps"] if "run" in s]
        default_step = last_run[-1] if last_run else None
        checks, failures = {}, list(errors)
        for c in t["expected_checks"]:
            ok, why = evaluate_check(c, results, default_step, work, sub)
            checks[c["id"]] = ok
            if not ok:
                failures.append(f"{c['id']}: {why}")
    except TaskError as e:
        checks = {c["id"]: False for c in t["expected_checks"]}
        failures = [f"setup: {e}"]
    finally:
        if not keep:
            shutil.rmtree(work, ignore_errors=True)
    passed = all(checks.values()) and not errors
    return {"checks": checks, "failures": failures, "passed": passed, "time_ms": round(elapsed * 1000, 1),
            "work": str(work) if keep else None}


def json_path(obj, path):
    if path in (None, "", "$"):
        return obj
    for key, idx in re.findall(r"\.?([^.\[\]]+)|\[(-?\d+)\]", path):
        if idx:
            if not isinstance(obj, list):
                raise KeyError(f"[{idx}] on non-list")
            obj = obj[int(idx)]
        else:
            if not isinstance(obj, dict) or key not in obj:
                raise KeyError(f"no key {key!r}")
            obj = obj[key]
    return obj


def _matches(item, pattern):
    if not isinstance(item, dict):
        return False
    for k, v in pattern.items():
        if k.endswith("~"):
            if v not in str(item.get(k[:-1], "")):
                return False
        elif item.get(k) != v:
            return False
    return True


def _glob_one(work, pattern):
    hits = sorted(work.glob(pattern))
    return hits[0] if hits else None


def _load_json_source(c, res, work, sub):
    src = c.get("source", "stdout")
    if src == "stdout":
        text = res["stdout"]
    elif src.startswith("file:"):
        p = _glob_one(work, sub(src[5:]))
        if p is None:
            raise ValueError(f"no file matches {src[5:]}")
        text = p.read_text(encoding="utf-8")
    else:
        raise ValueError(f"unknown source {src}")
    if c.get("format") == "jsonl":
        return [json.loads(ln) for ln in text.splitlines() if ln.strip()]
    return json.loads(text)


def evaluate_check(c, results, default_step, work, sub):
    kind = c["kind"]
    step = c.get("step") or default_step
    res = results.get(step) if step else None
    needs_step = kind in ("exit_code", "stdout_contains", "stdout_not_contains", "stderr_contains",
                          "stdout_empty") or (kind == "json" and c.get("source", "stdout") == "stdout")
    if needs_step and res is None:
        return False, f"step {step!r} did not run"
    vals = [sub(str(v)) for v in (c.get("values") or [])]
    try:
        if kind == "exit_code":
            want = int(c.get("value", 0))
            return res["exit"] == want, f"exit {res['exit']}, expected {want}"
        if kind == "stdout_contains":
            miss = [v for v in vals if v not in res["stdout"]]
            return not miss, f"stdout lacks {miss}"
        if kind == "stdout_not_contains":
            hit = [v for v in vals if v in res["stdout"]]
            return not hit, f"stdout contains {hit}"
        if kind == "stderr_contains":
            miss = [v for v in vals if v not in res["stderr"]]
            return not miss, f"stderr lacks {miss}"
        if kind == "stdout_empty":
            return res["stdout"].strip() == "", f"stdout not empty: {res['stdout'][:200]!r}"
        if kind in ("file_exists", "file_absent"):
            hit = _glob_one(work, sub(c["path"]))
            if kind == "file_exists":
                return hit is not None, f"no file matches {c['path']}"
            return hit is None, f"{c['path']} exists"
        if kind in ("file_contains", "file_not_contains"):
            p = _glob_one(work, sub(c["path"]))
            if p is None:
                return False, f"no file matches {c['path']}"
            text = p.read_text(encoding="utf-8", errors="replace")
            if kind == "file_contains":
                miss = [v for v in vals if v not in text]
                return not miss, f"{p.name} lacks {miss}"
            hit = [v for v in vals if v in text]
            return not hit, f"{p.name} contains {hit}"
        if kind == "json":
            data = _load_json_source(c, res, work, sub)
            try:
                v = json_path(data, c.get("path"))
            except (KeyError, IndexError) as e:
                if c.get("exists") is False:
                    return True, ""
                return False, f"path {c.get('path')!r}: {e}"
            if "exists" in c:
                return bool(c["exists"]), f"path {c.get('path')!r} exists"
            if "equals" in c:
                want = sub(c["equals"]) if isinstance(c["equals"], str) else c["equals"]
                return v == want, f"{c.get('path')} = {v!r}, expected {want!r}"
            if "contains" in c:
                want = sub(c["contains"]) if isinstance(c["contains"], str) else c["contains"]
                return (want in v), f"{c.get('path')} = {str(v)[:200]!r} does not contain {want!r}"
            if "not_contains" in c:
                want = sub(c["not_contains"]) if isinstance(c["not_contains"], str) else c["not_contains"]
                return (want not in v), f"{c.get('path')} contains {want!r}"
            for op, cmp_ in (("len_lte", lambda a, b: a <= b), ("len_gte", lambda a, b: a >= b),
                             ("len_equals", lambda a, b: a == b)):
                if op in c:
                    return cmp_(len(v), int(c[op])), f"len({c.get('path')}) = {len(v)}, {op} {c[op]}"
            for op, cmp_ in (("gte", lambda a, b: a >= b), ("lte", lambda a, b: a <= b)):
                if op in c:
                    return cmp_(v, c[op]), f"{c.get('path')} = {v!r}, {op} {c[op]}"
            if "any_match" in c:
                ok = isinstance(v, list) and any(_matches(x, c["any_match"]) for x in v)
                return ok, f"no item of {c.get('path') or '$'} matches {c['any_match']}"
            if "none_match" in c:
                ok = isinstance(v, list) and not any(_matches(x, c["none_match"]) for x in v)
                return ok, f"an item of {c.get('path') or '$'} matches {c['none_match']}"
    except (ValueError, TypeError, OSError) as e:
        return False, f"{type(e).__name__}: {e}"
    return False, "unhandled check"


# ---------------------------------------------------------------- results

def policy_label():
    h = hashlib.sha256()
    for d in POLICY_DIRS:
        base = ROOT / d
        if not base.is_dir():
            continue
        for p in sorted(base.rglob("*")):
            if p.is_file() and "__pycache__" not in p.parts and p.suffix != ".pyc":
                h.update(str(p.relative_to(ROOT)).encode() + b"\0" + p.read_bytes() + b"\0")
    return "tree-" + h.hexdigest()[:12]


def build_run(area, split, tasks, outcomes, set_sha, policy):
    now = dt.datetime.now(dt.timezone.utc).replace(microsecond=0)
    out = {
        "eval_set": area if split == "all" else f"{area}/{split}",
        "eval_set_sha256": set_sha,
        "policy": policy,
        "producer_model": PRODUCER,
        "judge_model": JUDGE,
        "producer": "harness scripts/ and hooks/ under test (no model)",
        "judge": JUDGE,
        "run_at": now.isoformat().replace("+00:00", "Z"),
        "runner": f"scripts/run_evals.py v{RUNNER_VERSION}",
        "split": split,
        "units": {"time": "ms"},
        "summary": {"tasks": len(tasks), "passed": sum(1 for o in outcomes if o["passed"]),
                    "failed": sum(1 for o in outcomes if not o["passed"])},
        "tasks": {},
    }
    for t, o in zip(tasks, outcomes):
        entry = {
            "id": t["id"],
            "target": t.get("components") or [],
            "rubric": t.get("rubric"),
            "locked": bool(t.get("locked")),
            "split": t["split"],
            "status": t.get("status", "draft"),
            "judge": JUDGE,
            "judge_model": JUDGE,
            "producer_model": PRODUCER,
            "scores": {"correctness": 1.0 if o["passed"] else 0.0, "time": o["time_ms"]},
            "checks": o["checks"],
        }
        if o["failures"]:
            entry["failures"] = o["failures"]
        out["tasks"][t["id"]] = entry
    return out


def default_out(area, run_at):
    data = pathlib.Path(os.environ.get("HARNESS_DATA") or (pathlib.Path.home() / "harness-data"))
    stamp = run_at.replace("-", "").replace(":", "")
    return data / "evals" / "results" / area / f"{stamp}.json"


def load_gate():
    spec = importlib.util.spec_from_file_location("eval_gate", ROOT / "scripts" / "eval_gate.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__.split("\n\n")[0],
                                formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--area", required=True)
    p.add_argument("--split", choices=("train", "holdout", "all"), default="all")
    p.add_argument("--task", action="append", default=[], metavar="ID", help="run only this task (repeatable)")
    p.add_argument("--out", help="result path ('-' = stdout); default $HARNESS_DATA/evals/results/<area>/<ts>.json")
    p.add_argument("--baseline", help="previous EvalRun JSON; run scripts/eval_gate.py against it")
    p.add_argument("--tolerance", action="append", default=None, metavar="DIM=VALUE[%]",
                   help=f"gate tolerance override (repeatable; default {' '.join(DEFAULT_GATE_TOLERANCE)})")
    p.add_argument("--policy", help="label for the policy under test (default: hash of scripts/ hooks/ skills/ agents/)")
    p.add_argument("--timeout", type=float, default=DEFAULT_STEP_TIMEOUT, help="max seconds per step")
    p.add_argument("--evals-dir", default=str(ROOT / "evals"))
    p.add_argument("--lock-hash", action="store_true", help="print each task's lock_sha256 value and exit")
    p.add_argument("--keep", action="store_true", help="keep task temp dirs (for debugging)")
    p.add_argument("--quiet", action="store_true")
    args = p.parse_args(argv)

    area_dir = pathlib.Path(args.evals_dir) / args.area
    files = task_files(area_dir)
    if not files:
        print(f"error: no tasks in {area_dir / 'tasks'}", file=sys.stderr)
        return 2
    try:
        tasks = [load_task(f) for f in files]
    except TaskError as e:
        print(f"error: {e}", file=sys.stderr)
        return 2
    seen = {}
    for t in tasks:
        if t["id"] in seen:
            print(f"error: duplicate task id {t['id']}", file=sys.stderr)
            return 2
        seen[t["id"]] = t
        if t.get("area") != args.area:
            print(f"error: {t['_path'].name}: area {t.get('area')!r} is not {args.area!r}", file=sys.stderr)
            return 2

    if args.lock_hash:
        for t in tasks:
            state = "locked" if str(t.get("lock_sha256") or "").strip() == t["_lock_actual"] else "unlocked"
            print(f"{t['id']}\t{t['_lock_actual']}\t{state}")
        return 0

    refusals = check_locks(tasks)
    if refusals:
        print("refusing to run: locked task(s) changed since they were locked", file=sys.stderr)
        for r in refusals:
            print(f"  - {r}", file=sys.stderr)
        return 2

    if args.task:
        unknown = sorted(set(args.task) - set(seen))
        if unknown:
            print(f"error: unknown task id(s): {', '.join(unknown)}", file=sys.stderr)
            return 2
    sel = [t for t in tasks if (args.split == "all" or t["split"] == args.split)
           and (not args.task or t["id"] in args.task)]
    if not sel:
        print("error: no task selected", file=sys.stderr)
        return 2
    sel_files = [t["_path"] for t in sel]

    outcomes = []
    for t in sel:
        o = run_task(t, args.timeout, args.keep)
        outcomes.append(o)
        if not args.quiet:
            mark = "PASS" if o["passed"] else "FAIL"
            print(f"{mark} {t['id']} [{t['split']}] {o['time_ms']:.0f} ms  {t.get('title', '')}", file=sys.stderr)
            if not o["passed"]:
                for f in o["failures"]:
                    print(f"    - {f}", file=sys.stderr)
            if o["work"]:
                print(f"    work dir: {o['work']}", file=sys.stderr)
        unlocked = t.get("status") == "locked" and not str(t.get("lock_sha256") or "").strip()
        if unlocked and not args.quiet:
            print(f"    note: {t['id']} has status: locked but no lock_sha256 (run --lock-hash)", file=sys.stderr)

    run = build_run(args.area, args.split, sel, outcomes, eval_set_hash(sel_files),
                    args.policy or policy_label())
    if args.task:
        run["eval_set"] += "[" + ",".join(sorted(args.task)) + "]"
    text = json.dumps(run, indent=2, ensure_ascii=False) + "\n"
    if args.out == "-":
        sys.stdout.write(text)
    else:
        out = pathlib.Path(args.out) if args.out else default_out(args.area, run["run_at"])
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(text, encoding="utf-8")
        if not args.quiet:
            print(f"{run['summary']['passed']}/{run['summary']['tasks']} passed; result: {out}", file=sys.stderr)

    rc = 0 if run["summary"]["failed"] == 0 else 1
    if args.baseline:
        gate = load_gate()
        try:
            base = gate.load(args.baseline)
        except gate.InputError as e:
            print(f"error: {e}", file=sys.stderr)
            return 2
        cand = json.loads(text)
        tol = dict(gate.parse_tolerance(s) for s in (args.tolerance if args.tolerance is not None
                                                     else DEFAULT_GATE_TOLERANCE))
        res = gate.evaluate(base, cand, tol)
        sys.stderr.write(gate.report(res))
        if res["decision"] != "accept":
            rc = 1
    return rc


if __name__ == "__main__":
    sys.exit(main())
