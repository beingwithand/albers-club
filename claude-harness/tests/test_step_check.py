"""Tests for hooks/step_check.py (PostToolUse step check) and its interaction with the Stop gate.

Run from the harness root:  python3 -I -m unittest discover -s tests -t .
"""
import datetime as dt
import importlib.util
import json
import os
import pathlib
import shutil
import subprocess
import sys
import tempfile
import time
import unittest

ROOT = pathlib.Path(__file__).resolve().parent.parent
HOOK = ROOT / "hooks" / "step_check.py"


def load(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


try:
    import yaml  # noqa: F401
    HAVE_YAML = True
except ImportError:
    HAVE_YAML = False


class StepCheckTest(unittest.TestCase):
    def setUp(self):
        self.tmp = pathlib.Path(tempfile.mkdtemp(prefix="harness-step-"))
        self.data = self.tmp / "data"
        self.proj = self.tmp / "work" / "code" / "widget"
        self.proj.mkdir(parents=True)
        (self.proj / "PROGRESS.md").write_text("# Progress\n- [ ] nothing yet\n", encoding="utf-8")
        self.env = {k: v for k, v in os.environ.items() if not k.startswith("HARNESS_")}
        self.env["HARNESS_DATA"] = str(self.data)

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    # ---------- helpers ----------
    def write(self, rel, text):
        p = self.proj / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(text, encoding="utf-8")
        return p

    def payload(self, path, tool="Edit", **kw):
        key = "notebook_path" if tool == "NotebookEdit" else "file_path"
        return dict({"session_id": "s1", "cwd": str(self.proj), "transcript_path": "/t.jsonl",
                     "hook_event_name": "PostToolUse", "tool_name": tool,
                     "tool_input": {key: str(path)}}, **kw)

    def run_hook(self, payload=None, raw=None, env=None, args=()):
        stdin = raw if raw is not None else json.dumps(payload)
        return subprocess.run([sys.executable, "-I", str(HOOK), *args], input=stdin,
                              env=env or self.env, capture_output=True, text=True, timeout=60)

    def events(self):
        out = []
        for f in sorted((self.data / "log").glob("*.jsonl")) if (self.data / "log").is_dir() else []:
            out += [json.loads(l) for l in f.read_text(encoding="utf-8").splitlines() if l.strip()]
        return out

    def assertSilent(self, p):
        self.assertEqual(p.returncode, 0, p.stderr)
        self.assertEqual(p.stdout.strip(), "")

    def assertFailed(self, p, *needles):
        self.assertEqual(p.returncode, 0, p.stderr)
        out = json.loads(p.stdout)
        hso = out["hookSpecificOutput"]
        self.assertEqual(hso["hookEventName"], "PostToolUse")
        ctx = hso["additionalContext"]
        self.assertTrue(ctx.startswith("STEP CHECK FAILED"), ctx)
        for n in needles:
            self.assertIn(n, ctx)
        return ctx

    def trust(self, cfg):
        p = self.run_hook(raw="", args=("--trust", str(cfg)))
        self.assertEqual(p.returncode, 0, p.stderr)

    # ---------- python ----------
    def test_py_syntax_error_reports_and_logs_fail(self):
        f = self.write("pkg/bad.py", "def f(:\n    return 1\n")
        ctx = self.assertFailed(self.run_hook(self.payload(f)), str(f), "py_compile", "SyntaxError")
        self.assertIn("docs/VERIFICATION.md", ctx)
        [ev] = self.events()
        self.assertEqual(ev["type"], "verification")
        self.assertEqual(ev["verdict"], "fail")
        self.assertEqual(ev["items"], [str(f)])
        self.assertEqual(ev["scope_hint"], str(self.proj))
        self.assertIn("step_check", ev["labels"])
        self.assertTrue(ev["id"].startswith("evt_"))

    def test_valid_py_is_silent_logs_pass_and_leaves_no_pycache(self):
        f = self.write("pkg/good.py", "def f():\n    return 1\n")
        t0 = time.monotonic()
        p = self.run_hook(self.payload(f, tool="Write"))
        elapsed = time.monotonic() - t0
        self.assertSilent(p)
        self.assertLess(elapsed, 5.0)
        [ev] = self.events()
        self.assertEqual(ev["verdict"], "pass")
        self.assertFalse((self.proj / "pkg" / "__pycache__").exists())

    def test_relative_path_resolved_against_cwd(self):
        self.write("rel.py", "x = (\n")
        self.assertFailed(self.run_hook(self.payload("rel.py", tool="MultiEdit")), "rel.py")

    # ---------- json / jsonl / ipynb ----------
    def test_json(self):
        good = self.write("a.json", '{"a": [1, 2]}')
        bad = self.write("b.json", '{"a": [1, 2,]}')
        self.assertSilent(self.run_hook(self.payload(good)))
        self.assertFailed(self.run_hook(self.payload(bad)), "invalid JSON", "b.json")

    def test_jsonl_reports_bad_line_numbers(self):
        good = self.write("ok.jsonl", '{"a": 1}\n\n{"b": 2}\n')
        bad = self.write("bad.jsonl", '{"a": 1}\n{"b": \n{"c": 3}\nnope\n')
        self.assertSilent(self.run_hook(self.payload(good)))
        ctx = self.assertFailed(self.run_hook(self.payload(bad)), "invalid JSONL", "line 2", "line 4")
        self.assertNotIn("line 3", ctx)

    def test_large_jsonl_is_skipped(self):
        mod = load(HOOK, "step_check_mod")
        big = self.proj / "big.jsonl"
        with open(big, "w", encoding="utf-8") as f:
            f.write("not json\n" * (mod.JSONL_MAX_BYTES // 9 + 10))
        self.assertSilent(self.run_hook(self.payload(big)))
        self.assertEqual(self.events(), [])

    def test_notebook_edit_parses_ipynb(self):
        nb = self.write("n.ipynb", '{"cells": [}')
        self.assertFailed(self.run_hook(self.payload(nb, tool="NotebookEdit")), "invalid JSON")

    # ---------- yaml / bash ----------
    @unittest.skipUnless(HAVE_YAML, "PyYAML not installed")
    def test_yaml(self):
        good = self.write("c.yaml", "a: 1\n---\nb: [1, 2]\n")
        bad = self.write("d.yml", "a: [1, 2\nb: 3\n")
        self.assertSilent(self.run_hook(self.payload(good)))
        self.assertFailed(self.run_hook(self.payload(bad)), "invalid YAML")

    @unittest.skipUnless(shutil.which("bash"), "bash not installed")
    def test_bash(self):
        good = self.write("s.sh", "#!/bin/bash\nif true; then echo hi; fi\n")
        bad = self.write("t.sh", "#!/bin/bash\nif true; then echo hi\n")
        self.assertSilent(self.run_hook(self.payload(good)))
        self.assertFailed(self.run_hook(self.payload(bad)), "bash -n", "t.sh")

    # ---------- unconfigured types ----------
    def test_ts_without_config_is_skipped_and_not_logged(self):
        f = self.write("app.ts", "const x: = ;\n")
        self.assertSilent(self.run_hook(self.payload(f)))
        self.assertEqual(self.events(), [])

    # ---------- project config ----------
    def config(self, data):
        return self.write(".claude/step_check.json", json.dumps(data))

    def test_untrusted_config_does_not_run(self):
        marker = self.tmp / "ran"
        self.config({"*.ts": f"touch {marker}"})
        f = self.write("app.ts", "x\n")
        p = self.run_hook(self.payload(f))
        self.assertEqual(p.returncode, 0, p.stderr)
        ctx = json.loads(p.stdout)["hookSpecificOutput"]["additionalContext"]
        self.assertIn("not trusted", ctx)
        self.assertIn("--trust", ctx)
        self.assertFalse(marker.exists())

    def test_trusted_config_pass_fail_and_file_placeholder(self):
        cfg = self.config({"*.ts": "grep -q ok {file}", "src/*.js": {"command": "exit 3", "timeout": 2}})
        self.trust(cfg)
        good = self.write("good file.ts", "ok\n")
        bad = self.write("bad.ts", "nope\n")
        self.assertSilent(self.run_hook(self.payload(good)))
        self.assertFailed(self.run_hook(self.payload(bad)), "grep -q ok", "bad.ts")
        js = self.write("src/x.js", "1\n")
        self.assertFailed(self.run_hook(self.payload(js)), "exit 3")
        self.assertEqual([e["verdict"] for e in self.events()], ["pass", "fail", "fail"])

    def test_config_command_timeout_kills_and_fails(self):
        cfg = self.config({"*.swift": {"command": "sleep 30", "timeout": 0.5}})
        self.trust(cfg)
        f = self.write("a.swift", "let x = 1\n")
        t0 = time.monotonic()
        p = self.run_hook(self.payload(f))
        self.assertLess(time.monotonic() - t0, 10.0)
        self.assertFailed(p, "timed out after 0.5s")

    def test_editing_config_revokes_trust(self):
        marker = self.tmp / "ran"
        cfg = self.config({"*.ts": "true"})
        self.trust(cfg)
        self.config({"*.ts": f"touch {marker}"})
        f = self.write("app.ts", "x\n")
        p = self.run_hook(self.payload(f))
        self.assertIn("not trusted", p.stdout)
        self.assertFalse(marker.exists())

    def test_config_runs_after_builtin_pass_and_not_after_fail(self):
        marker = self.tmp / "ran"
        cfg = self.config({"*.py": f"touch {marker}"})
        self.trust(cfg)
        bad = self.write("bad.py", "def (:\n")
        self.assertFailed(self.run_hook(self.payload(bad)), "py_compile")
        self.assertFalse(marker.exists())
        good = self.write("good.py", "x = 1\n")
        self.assertSilent(self.run_hook(self.payload(good)))
        self.assertTrue(marker.exists())

    def test_trust_rejects_bad_config(self):
        cfg = self.write(".claude/step_check.json", "{broken")
        p = self.run_hook(raw="", args=("--trust", str(cfg)))
        self.assertEqual(p.returncode, 1)
        self.assertIn("cannot trust", p.stderr)

    # ---------- off switch and robustness ----------
    def test_disabled_via_env(self):
        f = self.write("bad.py", "def (:\n")
        for off in ("0", "false", "off"):
            self.assertSilent(self.run_hook(self.payload(f), env=dict(self.env, HARNESS_STEP_CHECK=off)))
        self.assertEqual(self.events(), [])

    def test_garbage_input_never_crashes(self):
        missing = self.proj / "missing.py"
        for raw in ["", "not json", "[1, 2]", "null", "{}", json.dumps({"tool_name": "Edit"}),
                    json.dumps({"tool_name": "Edit", "tool_input": "x"}),
                    json.dumps({"tool_name": "Edit", "tool_input": {"file_path": 5}}),
                    json.dumps({"tool_name": "Edit", "tool_input": {"file_path": "rel.py"}}),
                    json.dumps(self.payload(missing)),
                    json.dumps(self.payload(self.proj))]:
            self.assertSilent(self.run_hook(raw=raw))
        bad = self.write("bad.py", "def (:\n")
        self.assertSilent(self.run_hook(self.payload(bad, tool="Bash")))
        self.assertEqual(self.events(), [])

    def test_unwritable_log_still_reports(self):
        (self.tmp / "data").write_text("a file where the data dir should be", encoding="utf-8")
        f = self.write("bad.json", "{")
        self.assertFailed(self.run_hook(self.payload(f)), "invalid JSON")

    # ---------- interaction with the Stop gate and weekly report ----------
    def test_step_check_pass_does_not_satisfy_verify_gate(self):
        (self.proj / "PROGRESS.md").write_text("- [x] parse input\n", encoding="utf-8")
        os.utime(self.proj / "PROGRESS.md", (time.time() - 3600, time.time() - 3600))
        f = self.write("parse input.py", "x = 1\n")
        self.assertSilent(self.run_hook(self.payload(f)))
        self.assertEqual(self.events()[0]["verdict"], "pass")
        gate = subprocess.run([sys.executable, "-I", str(ROOT / "hooks" / "verify_gate.py")],
                              input=json.dumps({"cwd": str(self.proj), "stop_hook_active": False}),
                              env=self.env, capture_output=True, text=True, timeout=30)
        self.assertEqual(json.loads(gate.stdout)["decision"], "block")

    def test_weekly_report_ignores_step_checks(self):
        wr = load(ROOT / "scripts" / "weekly_report.py", "weekly_report_mod")
        ts = "2026-10-16T10:00:00+00:00"
        evs = [{"id": "evt_a", "ts": ts, "type": "verification", "verdict": "pass", "labels": ["step_check"],
                "scope": "code/widget"},
               {"id": "evt_b", "ts": ts, "type": "verification", "verdict": "fail", "scope": "code/widget"}]
        stats, _, _ = wr.summarize(evs, dt.date(2026, 10, 10), dt.date(2026, 10, 16), {"code"})
        s = stats["code/widget"]
        self.assertEqual((s["verifications"], s["pass"], s["fail"]), (1, 0, 1))


if __name__ == "__main__":
    unittest.main()
