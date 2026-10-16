"""PostToolUse hook (Edit|Write|MultiEdit|NotebookEdit): cheap syntax check of the edited file.

The automatic floor of the step-verification protocol (docs/VERIFICATION.md). It NEVER blocks
(always exit 0). On failure it prints
  {"hookSpecificOutput": {"hookEventName": "PostToolUse", "additionalContext": "STEP CHECK FAILED: ..."}}
so Claude sees the error before its next step. Every check that ran (pass or fail) appends a
`verification` event labeled `step_check` (items: [path], scope_hint: cwd) via _common's locked
append. hooks/verify_gate.py ignores step_check events: a syntax check is not verification of
the work.

Built-in checks by suffix (each with a hard timeout, HARD_TIMEOUT_S):
  .py          python3 -I -m py_compile (bytecode goes to a temp pycache prefix, not the repo)
  .json/.ipynb JSON parse
  .jsonl       parse each line (files up to JSONL_MAX_BYTES)
  .yaml/.yml   yaml.safe_load_all if PyYAML is importable, else skipped
  .sh/.bash    bash -n
Anything else (.ts, .js, .swift, ...) is checked only by a project command in
<project>/.claude/step_check.json: {"<glob>": "<cmd>" | {"command": "<cmd>", "timeout": s}}.
`{file}` in a command becomes the shell-quoted path; it runs in the project root. Config
commands also run after a passing built-in check for files they match.

Trust: hooks run outside the sandbox, so a config file is a code-execution surface (a cloned
repo, or an agent writing .claude/step_check.json). A config runs only after the user trusts
that exact content:  python3 -I hooks/step_check.py --trust <project>/.claude/step_check.json
(stored as a sha256 in $HARNESS_DATA/step_check_trust.json; any edit to the config needs a
new --trust). An untrusted config is skipped and named in additionalContext with that command.

Off switch: HARNESS_STEP_CHECK=0. Any internal error means silent exit 0.
"""
import fnmatch
import hashlib
import importlib.util
import json
import os
import pathlib
import shlex
import shutil
import signal
import subprocess
import sys
import tempfile

_spec = importlib.util.spec_from_file_location("harness_common", pathlib.Path(__file__).resolve().parent / "_common.py")
C = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(C)

TOOLS = {"Edit", "Write", "MultiEdit", "NotebookEdit"}
HARD_TIMEOUT_S = 5.0
CONFIG_DEFAULT_TIMEOUT_S = 5.0
CONFIG_MAX_TIMEOUT_S = 60.0
JSON_MAX_BYTES = 20 * 1024 * 1024
JSONL_MAX_BYTES = 5 * 1024 * 1024
YAML_MAX_BYTES = 2 * 1024 * 1024
MAX_REPORT_CHARS = 1500
MAX_BAD_LINES = 3
CONFIG_NAME = pathlib.Path(".claude") / "step_check.json"
TRUST_FILE = "step_check_trust.json"
OFF = ("0", "false", "off", "no")


def _tail(text, limit=MAX_REPORT_CHARS):
    text = (text or "").strip()
    return text if len(text) <= limit else "…" + text[-limit:]


def run_cmd(argv, cwd=None, timeout=HARD_TIMEOUT_S, shell=False):
    """Run a command in its own process group; kill the whole group on timeout.
    Returns (ok, output) where ok is True/False, or None when the command could not start."""
    try:
        p = subprocess.Popen(argv, cwd=cwd, shell=shell, stdin=subprocess.DEVNULL,
                             stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True,
                             errors="replace", start_new_session=True)
    except OSError:
        return None, ""
    try:
        out, _ = p.communicate(timeout=timeout)
    except subprocess.TimeoutExpired:
        try:
            os.killpg(p.pid, signal.SIGKILL)
        except OSError:
            p.kill()
        p.communicate()
        return False, f"timed out after {timeout:g}s"
    return p.returncode == 0, out


# ---------- built-in checks: each returns None (skipped), (True, "") or (False, message) ----------

def check_py(path):
    with tempfile.TemporaryDirectory(prefix="step-check-pyc-") as tmp:
        ok, out = run_cmd([sys.executable, "-I", "-X", f"pycache_prefix={tmp}", "-m", "py_compile", str(path)])
    if ok is None:
        return None
    return (True, "") if ok else (False, _tail(out))


def check_json(path):
    if path.stat().st_size > JSON_MAX_BYTES:
        return None
    try:
        with open(path, encoding="utf-8") as f:
            json.load(f)
    except UnicodeDecodeError as e:
        return False, f"not valid UTF-8: {e}"
    except ValueError as e:
        return False, f"invalid JSON: {e}"
    return True, ""


def check_jsonl(path):
    if path.stat().st_size > JSONL_MAX_BYTES:
        return None
    bad = []
    with open(path, encoding="utf-8", errors="replace") as f:
        for n, line in enumerate(f, 1):
            if not line.strip():
                continue
            try:
                json.loads(line)
            except ValueError as e:
                bad.append(f"line {n}: {e}")
                if len(bad) >= MAX_BAD_LINES:
                    break
    return (True, "") if not bad else (False, "invalid JSONL: " + "; ".join(bad))


def check_yaml(path):
    try:
        import yaml
    except ImportError:
        return None
    if path.stat().st_size > YAML_MAX_BYTES:
        return None
    try:
        with open(path, encoding="utf-8") as f:
            for _ in yaml.safe_load_all(f):
                pass
    except (yaml.YAMLError, UnicodeDecodeError) as e:
        return False, "invalid YAML: " + _tail(str(e), 600)
    return True, ""


def check_sh(path):
    bash = shutil.which("bash")
    if not bash:
        return None
    ok, out = run_cmd([bash, "-n", str(path)])
    if ok is None:
        return None
    return (True, "") if ok else (False, _tail(out))


BUILTIN = {
    ".py": ("py_compile", check_py),
    ".json": ("json", check_json),
    ".ipynb": ("json", check_json),
    ".jsonl": ("jsonl", check_jsonl),
    ".yaml": ("yaml", check_yaml),
    ".yml": ("yaml", check_yaml),
    ".sh": ("bash -n", check_sh),
    ".bash": ("bash -n", check_sh),
}


# ---------- project config ----------

def _sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def trust_path(env):
    return C.data_dir(env) / TRUST_FILE


def is_trusted(config, env):
    trusted = C.load_json(trust_path(env), {}) or {}
    return isinstance(trusted, dict) and trusted.get(str(config)) == _sha256(config)


def trust(config, env):
    config = pathlib.Path(config).expanduser().resolve()
    json.loads(config.read_text(encoding="utf-8"))  # refuse to trust a config that doesn't parse
    trusted = C.load_json(trust_path(env), {}) or {}
    if not isinstance(trusted, dict):
        trusted = {}
    trusted[str(config)] = _sha256(config)
    C.write_json_atomic(trust_path(env), trusted)
    return config


def find_config(path, cwd):
    """The nearest .claude/step_check.json: at cwd, or at the project root of the edited file."""
    roots = []
    if cwd:
        roots.append(pathlib.Path(cwd))
    root = C.project_root(str(path.parent))
    if root:
        roots.append(root)
    for r in roots:
        cfg = r / CONFIG_NAME
        if cfg.is_file():
            return cfg
    return None


def config_commands(config, path):
    """[(glob, command, timeout)] for globs matching the file's name or its path below the root."""
    data = C.load_json(config, {})
    if not isinstance(data, dict):
        return []
    root = config.parent.parent
    try:
        rel = str(path.relative_to(root))
    except ValueError:
        rel = path.name
    out = []
    for glob, spec in data.items():
        if not isinstance(glob, str) or not (fnmatch.fnmatch(path.name, glob) or fnmatch.fnmatch(rel, glob)):
            continue
        if isinstance(spec, str):
            cmd, timeout = spec, CONFIG_DEFAULT_TIMEOUT_S
        elif isinstance(spec, dict) and isinstance(spec.get("command"), str):
            cmd = spec["command"]
            try:
                timeout = float(spec.get("timeout", CONFIG_DEFAULT_TIMEOUT_S))
            except (TypeError, ValueError):
                timeout = CONFIG_DEFAULT_TIMEOUT_S
        else:
            continue
        if cmd.strip():
            out.append((glob, cmd.replace("{file}", shlex.quote(str(path))),
                        min(max(timeout, 0.1), CONFIG_MAX_TIMEOUT_S)))
    return out


# ---------- hook ----------

def edited_path(payload):
    ti = payload.get("tool_input")
    if not isinstance(ti, dict):
        return None
    p = ti.get("file_path") or ti.get("notebook_path")
    if not isinstance(p, str) or not p:
        return None
    path = pathlib.Path(p).expanduser()
    if not path.is_absolute():
        cwd = payload.get("cwd")
        if not isinstance(cwd, str) or not cwd:
            return None
        path = pathlib.Path(cwd) / path
    return path


def run_checks(payload, env):
    """Return (results, notes). results: [(check_name, ok, message)]; notes: extra context lines."""
    path = edited_path(payload)
    if path is None or not path.is_file():
        return [], []
    cwd = payload.get("cwd") if isinstance(payload.get("cwd"), str) else None
    results, notes = [], []
    builtin = BUILTIN.get(path.suffix.lower())
    if builtin:
        name, fn = builtin
        r = fn(path)
        if r is not None:
            results.append((name, r[0], r[1]))
            if not r[0]:
                return results, notes
    config = find_config(path, cwd)
    if config:
        cmds = config_commands(config, path)
        if cmds and not is_trusted(config, env):
            notes.append(f"step_check: {config} is not trusted, so its commands did not run. If you (the user) "
                         f"wrote it, trust it with: python3 -I {pathlib.Path(__file__).resolve()} --trust {config}")
            cmds = []
        for glob, cmd, timeout in cmds:
            ok, out = run_cmd(cmd, cwd=str(config.parent.parent), timeout=timeout, shell=True)
            if ok is None:
                continue
            results.append((f"{glob}: {cmd}", ok, "" if ok else _tail(out)))
            if not ok:
                break
    return results, notes


def log_results(payload, path, results, env):
    p = dict(payload)
    if not isinstance(p.get("cwd"), str) or not p.get("cwd"):
        p["cwd"] = str(path.parent)
    failed = [r for r in results if not r[1]]
    verdict = "fail" if failed else "pass"
    summary = "; ".join(f"{n}: {'ok' if ok else (msg.splitlines() or ['failed'])[0][:200]}" for n, ok, msg in results)
    try:
        C.append_event("verification", p, env=env, verdict=verdict, items=[str(path)],
                       labels=["step_check"], content=f"step_check {summary}")
    except Exception:
        pass


def main(argv=None, stdin=None, env=None):
    argv = sys.argv[1:] if argv is None else argv
    env = os.environ if env is None else env
    if len(argv) == 2 and argv[0] == "--trust":
        try:
            cfg = trust(argv[1], env)
        except (OSError, ValueError) as e:
            print(f"step_check: cannot trust {argv[1]}: {e}", file=sys.stderr)
            return 1
        print(f"step_check: trusted {cfg} (sha256 recorded in {trust_path(env)})")
        return 0
    try:
        if str(env.get("HARNESS_STEP_CHECK", "1")).strip().lower() in OFF:
            return 0
        payload = C.read_payload(stdin or sys.stdin)
        if payload.get("tool_name") not in TOOLS:
            return 0
        results, notes = run_checks(payload, env)
        path = edited_path(payload)
        if results:
            log_results(payload, path, results, env)
        lines = [f"STEP CHECK FAILED: {path} ({n}): {msg or 'check failed'}" for n, ok, msg in results if not ok]
        if lines:
            lines.append("Fix this before the next step (docs/VERIFICATION.md). HARNESS_STEP_CHECK=0 disables the hook.")
        lines += notes
        if lines:
            sys.stdout.write(json.dumps({"hookSpecificOutput": {"hookEventName": "PostToolUse",
                                                                "additionalContext": "\n".join(lines)}},
                                        ensure_ascii=False))
    except Exception:
        pass
    return 0


if __name__ == "__main__":
    sys.exit(main())
