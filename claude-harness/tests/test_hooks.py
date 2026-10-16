"""Tests for hooks/verify_gate.py and the correction tagging in hooks/log_event.py.

Run from the harness root:  python3 -I -m unittest discover -s tests -t .
"""
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
HOOKS = ROOT / "hooks"


def load(name):
    spec = importlib.util.spec_from_file_location(f"hook_{name}", HOOKS / f"{name}.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


log_event = load("log_event")


def iso(ts):
    import datetime as dt
    return dt.datetime.fromtimestamp(ts, dt.timezone.utc).isoformat()


class VerifyGateTest(unittest.TestCase):
    def setUp(self):
        self.tmp = pathlib.Path(tempfile.mkdtemp(prefix="harness-gate-"))
        self.data = self.tmp / "data"
        (self.data / "log").mkdir(parents=True)
        self.proj = self.tmp / "work" / "code" / "widget"
        self.proj.mkdir(parents=True)
        self.env = {k: v for k, v in os.environ.items() if not k.startswith("HARNESS_")}
        self.env["HARNESS_DATA"] = str(self.data)

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def run_gate(self, payload=None, raw=None, env=None):
        stdin = raw if raw is not None else json.dumps(payload)
        return subprocess.run([sys.executable, "-I", str(HOOKS / "verify_gate.py")], input=stdin,
                              env=env or self.env, capture_output=True, text=True, timeout=30)

    def payload(self, **kw):
        return dict({"session_id": "s1", "cwd": str(self.proj), "transcript_path": "/t.jsonl",
                     "stop_hook_active": False, "hook_event_name": "Stop"}, **kw)

    def write_progress(self, text, mtime=None):
        p = self.proj / "PROGRESS.md"
        p.write_text(text, encoding="utf-8")
        if mtime is not None:
            os.utime(p, (mtime, mtime))

    def add_verification(self, ts, **kw):
        ev = dict({"id": "evt_v", "ts": iso(ts), "type": "verification", "verdict": "pass",
                   "scope_hint": str(self.proj)}, **kw)
        with open(self.data / "log" / "2026-10.jsonl", "a", encoding="utf-8") as f:
            f.write(json.dumps(ev) + "\n")

    def assertBlocked(self, p, *needles):
        self.assertEqual(p.returncode, 0, p.stderr)
        out = json.loads(p.stdout)
        self.assertEqual(out["decision"], "block")
        self.assertIn("verify", out["reason"])
        for n in needles:
            self.assertIn(n, out["reason"])
        return out

    def assertAllowed(self, p):
        self.assertEqual(p.returncode, 0, p.stderr)
        self.assertEqual(p.stdout.strip(), "")

    def test_blocks_done_items_without_verification(self):
        self.write_progress("# Progress\n- [x] parse input\n- [ ] write output\n")
        self.assertBlocked(self.run_gate(self.payload()), "parse input")

    def test_blocks_tasks_json_passes_true(self):
        (self.proj / "tasks.json").write_text(json.dumps(
            {"tasks": [{"id": "T1", "passes": True}, {"id": "T2", "passes": False}]}), encoding="utf-8")
        out = self.assertBlocked(self.run_gate(self.payload()), "T1")
        self.assertNotIn("T2", out["reason"])

    def test_loop_guard(self):
        self.write_progress("- [x] parse input\n")
        self.assertAllowed(self.run_gate(self.payload(stop_hook_active=True)))

    def test_passes_when_verified_after_done(self):
        now = time.time()
        self.write_progress("- [x] parse input\n", mtime=now - 3600)
        self.add_verification(now - 60)
        self.assertAllowed(self.run_gate(self.payload()))

    def test_verification_by_area_project_scope(self):
        now = time.time()
        self.write_progress("- [x] parse input\n", mtime=now - 3600)
        self.add_verification(now - 60, scope="code/widget", scope_hint=None)
        self.assertAllowed(self.run_gate(self.payload()))

    def test_blocks_when_done_after_last_verification(self):
        now = time.time()
        self.add_verification(now - 7200)
        self.write_progress("## Done\n- shipped the parser\n", mtime=now - 60)
        self.assertBlocked(self.run_gate(self.payload()), "shipped the parser", "after the last verification")

    def test_failed_or_other_project_verification_does_not_count(self):
        now = time.time()
        self.write_progress("- [x] parse input\n", mtime=now - 3600)
        self.add_verification(now - 60, verdict="fail")
        self.add_verification(now - 60, scope_hint="/somewhere/else")
        self.assertBlocked(self.run_gate(self.payload()))

    def test_tasks_item_timestamps_and_covered_items(self):
        now = time.time()
        self.add_verification(now - 600, items=["T2"])
        (self.proj / "tasks.json").write_text(json.dumps([
            {"id": "T1", "status": "done", "done_at": iso(now - 7200)},
            {"id": "T2", "status": "done", "done_at": iso(now - 10)},
        ]), encoding="utf-8")
        self.assertAllowed(self.run_gate(self.payload()))

    def test_no_progress_files_allows(self):
        self.assertAllowed(self.run_gate(self.payload()))
        self.write_progress("- [ ] nothing done yet\n## Done when\n- tests pass\n")
        self.assertAllowed(self.run_gate(self.payload()))

    def test_disabled_via_env(self):
        self.write_progress("- [x] parse input\n")
        env = dict(self.env, HARNESS_VERIFY_GATE="0")
        self.assertAllowed(self.run_gate(self.payload(), env=env))

    def test_garbage_input_never_crashes(self):
        for raw in ["", "not json", "[1, 2]", "null", json.dumps({"cwd": 5}),
                    json.dumps({"cwd": str(self.tmp / "missing")})]:
            self.assertAllowed(self.run_gate(raw=raw))
        self.write_progress("- [x] parse input\n")
        (self.proj / "tasks.json").write_text("{broken", encoding="utf-8")
        with open(self.data / "log" / "2026-10.jsonl", "a", encoding="utf-8") as f:
            f.write('{"type": "verification", garbage\n')
        p = self.run_gate(self.payload())
        self.assertBlocked(p, "parse input")


class CorrectionTaggingTest(unittest.TestCase):
    POSITIVES = [
        "No, use the formal register",
        "that's wrong, the date is 2024",
        "This is not what I asked for",
        "I said keep the headings",
        "Use tabs instead of spaces",
        "Don't touch the tests",
        "stop rewriting the intro",
        "아니, 존댓말로 해줘",
        "아니야 그 파일 말고",
        "그게 아니라 영어로 번역해",
        "표 말고 목록으로",
        "번역이 틀렸어",
        "날짜를 잘못 넣었네",
        "주석 추가하지 마",
        "왜 테스트 파일을 수정했어",
        "왜 그렇게 했어?",
    ]
    NEGATIVES = [
        "Translate the brief into English",
        "No problem, thanks",
        "Can you add a summary section?",
        "Please write the report",
        "번역해 주세요",
        "좋아요, 다음 단계로 가자",
        "이 문서 요약해 줄래?",
        "",
        None,
    ]

    def test_positives(self):
        for text in self.POSITIVES:
            cand, conf, names = log_event.detect_correction(text)
            self.assertTrue(cand, f"{text!r} -> {conf} {names}")
            self.assertGreaterEqual(conf, 0.5)

    def test_negatives(self):
        for text in self.NEGATIVES:
            cand, conf, _ = log_event.detect_correction(text)
            self.assertFalse(cand, f"{text!r} -> {conf}")

    def test_strong_beats_weak(self):
        _, strong, _ = log_event.detect_correction("그게 아니라 영어로")
        _, weak, _ = log_event.detect_correction("다시 해줘")
        self.assertGreater(strong, weak)

    def test_hook_writes_fields(self):
        tmp = pathlib.Path(tempfile.mkdtemp(prefix="harness-corr-"))
        try:
            env = dict(os.environ, HARNESS_DATA=str(tmp))
            for prompt in ("아니, 그게 아니라 존댓말로", "summarize this file"):
                p = subprocess.run([sys.executable, "-I", str(HOOKS / "log_event.py"), "prompt"],
                                   input=json.dumps({"prompt": prompt, "cwd": "/w", "session_id": "s"}),
                                   env=env, capture_output=True, text=True, timeout=30)
                self.assertEqual(p.returncode, 0, p.stderr)
                self.assertEqual(p.stdout, "")
            p = subprocess.run([sys.executable, "-I", str(HOOKS / "log_event.py"), "session_end"],
                               input="{}", env=env, capture_output=True, text=True, timeout=30)
            [f] = list((tmp / "log").glob("*.jsonl"))
            evs = [json.loads(l) for l in f.read_text(encoding="utf-8").splitlines()]
            self.assertIs(evs[0]["correction_candidate"], True)
            self.assertGreaterEqual(evs[0]["correction_confidence"], 0.8)
            self.assertIs(evs[1]["correction_candidate"], False)
            self.assertEqual(evs[1]["correction_confidence"], 0.0)
            self.assertNotIn("correction_candidate", evs[2])
        finally:
            shutil.rmtree(tmp, ignore_errors=True)


if __name__ == "__main__":
    unittest.main()
