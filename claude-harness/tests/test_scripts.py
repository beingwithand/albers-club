"""Tests for scripts/ and hooks/log_event.py. Stdlib only.

Run from the harness root:  python3 -I -m unittest discover -s tests
"""
import contextlib
import datetime as dt
import importlib.util
import io
import json
import os
import pathlib
import shutil
import subprocess
import sys
import tempfile
import unittest

ROOT = pathlib.Path(__file__).resolve().parent.parent
SCRIPTS = ROOT / "scripts"


def load(name):
    spec = importlib.util.spec_from_file_location(name, SCRIPTS / f"{name}.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


label_events = load("label_events")
eval_gate = load("eval_gate")
weekly_report = load("weekly_report")


def run_main(mod, argv):
    out, err = io.StringIO(), io.StringIO()
    with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
        code = mod.main(argv)
    return code, out.getvalue(), err.getvalue()


def write_jsonl(path, events, extra_lines=()):
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        for ev in events:
            f.write(json.dumps(ev, ensure_ascii=False) + "\n")
        for line in extra_lines:
            f.write(line + "\n")


SAMPLE = [
    {"id": "evt_p1", "ts": "2026-10-14T10:00:00+00:00", "type": "prompt", "actor": "me",
     "session_id": "s1", "scope_hint": "/Users/me/work/translation/acme/work", "content": "Translate the brief into English"},
    {"id": "evt_p2", "ts": "2026-10-14T10:05:00+00:00", "type": "prompt", "actor": "me",
     "session_id": "s1", "scope_hint": "/Users/me/work/translation/acme/work", "content": "No, keep it formal, not chatty"},
    {"id": "evt_p3", "ts": "2026-10-15T09:00:00Z", "type": "prompt", "actor": "me",
     "session_id": "s2", "scope_hint": "/Users/me/code/harness", "content": "fix the hook"},
    {"id": "evt_end", "ts": "2026-10-15T09:30:00Z", "type": "session_end", "session_id": "s2"},
    {"id": "evt_d1", "ts": "2026-10-15T09:10:00Z", "type": "decision", "scope": "code/harness",
     "intent": "x", "situation": "y", "meta": {"kind_of_thing": "scope decision"}, "cost_usd": 0.5},
    {"id": "evt_m1", "ts": "2026-10-15T09:20:00Z", "type": "mishap", "scope": "code/harness",
     "content": "deleted the wrong file", "cost_usd": 0.25},
    {"id": "evt_v1", "ts": "2026-10-15T09:25:00Z", "type": "verification", "scope": "code/harness", "verdict": "pass"},
    {"id": "evt_v2", "ts": "2026-10-15T09:26:00Z", "type": "verification", "scope": "code/harness", "verdict": "fail"},
    {"id": "evt_old", "ts": "2026-09-01T09:00:00Z", "type": "prompt", "session_id": "s0", "content": "old"},
    {"id": "evt_l0", "ts": "2026-10-15T12:00:00Z", "type": "label", "labels_for": "evt_p1",
     "intent": "get a translation", "is_correction": False, "labels": []},
]


class TempDataDir(unittest.TestCase):
    def setUp(self):
        self.tmp = pathlib.Path(tempfile.mkdtemp(prefix="harness-test-"))
        self.log = self.tmp / "log"
        write_jsonl(self.log / "2026-10.jsonl", SAMPLE, extra_lines=["{not json"])
        write_jsonl(self.log / "2026-09.jsonl", [])

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def snapshot(self):
        return {p.name: p.read_bytes() for p in self.log.glob("*.jsonl")}


class LabelEventsExportTest(TempDataDir):
    def test_export_selects_unlabeled_candidates_with_context(self):
        code, out, _ = run_main(label_events, ["--data-dir", str(self.tmp), "--from", "2026-10-10", "--to", "2026-10-16"])
        self.assertEqual(code, 0)
        self.assertIn("claude -p --model haiku", out)
        batch = self.tmp / "labels" / "batch_2026-10-10_2026-10-16.jsonl"
        self.assertTrue(batch.is_file())
        rows = [json.loads(l) for l in batch.read_text(encoding="utf-8").splitlines()]
        ids = [r["id"] for r in rows]
        # p1 already labeled; d1 has full labels; end/verification not candidates; old is out of range
        self.assertEqual(ids, ["evt_p2", "evt_p3", "evt_m1"])
        p2 = rows[0]
        self.assertEqual(p2["prev_content"], "Translate the brief into English")
        self.assertTrue((self.tmp / "labels" / "label_prompt.md").is_file())

    def test_export_does_not_touch_log(self):
        before = self.snapshot()
        run_main(label_events, ["--data-dir", str(self.tmp), "--from", "2026-10-01", "--to", "2026-10-31"])
        self.assertEqual(before, self.snapshot())


class LabelEventsApplyTest(TempDataDir):
    def write_labels(self, text):
        p = self.tmp / "out.labels.jsonl"
        p.write_text(text, encoding="utf-8")
        return p

    def test_apply_is_append_only_and_idempotent(self):
        before = self.snapshot()
        labels = self.write_labels("\n".join([
            "```json",
            json.dumps({"labels_for": "evt_p2", "intent": "make register formal", "situation": "client translation",
                        "meta": {"kind_of_thing": "style preference", "generalizes_to": "translation"},
                        "labels": ["register"], "is_correction": "true", "scope": "translation/acme"}),
            json.dumps({"labels_for": "evt_missing", "intent": "x", "is_correction": False}),
            json.dumps({"labels_for": "evt_p1", "intent": "again", "is_correction": False}),  # already labeled
            "garbage line",
            "```",
        ]))
        code, out, _ = run_main(label_events, ["--data-dir", str(self.tmp), "--apply", str(labels)])
        self.assertEqual(code, 0, out)

        after = self.snapshot()
        # Past content is a byte-for-byte prefix of every file: nothing was rewritten.
        for name, old in before.items():
            self.assertTrue(after[name].startswith(old), name)
        month_file = f"{dt.datetime.now(dt.timezone.utc):%Y-%m}.jsonl"
        old_len = len(before.get(month_file, b""))
        new_lines = after[month_file][old_len:].decode("utf-8").splitlines()
        self.assertEqual(len(new_lines), 1)
        ev = json.loads(new_lines[0])
        self.assertEqual(ev["type"], "label")
        self.assertEqual(ev["labels_for"], "evt_p2")
        self.assertIs(ev["is_correction"], True)
        self.assertEqual(ev["meta"]["generalizes_to"], ["translation"])
        self.assertEqual(ev["scope"], "translation/acme")
        self.assertTrue(ev["id"].startswith("evt_"))
        self.assertNotEqual(ev["id"], "evt_p2")

        # Re-applying the same file adds nothing.
        snap2 = self.snapshot()
        code, out, _ = run_main(label_events, ["--data-dir", str(self.tmp), "--apply", str(labels)])
        self.assertEqual(code, 1)
        self.assertEqual(snap2, self.snapshot())

    def test_apply_accepts_json_array_and_dry_run(self):
        labels = self.write_labels(json.dumps([{"labels_for": "evt_p3", "intent": "fix bug", "is_correction": False}]))
        before = self.snapshot()
        code, out, _ = run_main(label_events, ["--data-dir", str(self.tmp), "--apply", str(labels), "--dry-run"])
        self.assertEqual(code, 0)
        self.assertIn("1 new label events", out)
        self.assertEqual(before, self.snapshot())

    def test_labeled_event_no_longer_exported(self):
        labels = self.write_labels(json.dumps({"labels_for": "evt_p2", "intent": "formal", "is_correction": True}))
        run_main(label_events, ["--data-dir", str(self.tmp), "--apply", str(labels)])
        run_main(label_events, ["--data-dir", str(self.tmp), "--from", "2026-10-10", "--to", "2026-10-16"])
        batch = self.tmp / "labels" / "batch_2026-10-10_2026-10-16.jsonl"
        ids = [json.loads(l)["id"] for l in batch.read_text(encoding="utf-8").splitlines()]
        self.assertNotIn("evt_p2", ids)


def result(tasks, producer="sonnet", judge="opus", **kw):
    return {"eval_set": "translation", "producer_model": producer, "judge_model": judge, "tasks": tasks, **kw}


def task(correctness, style=4.0, cost=0.10, locked=False, checks=None):
    t = {"locked": locked, "scores": {"correctness": correctness, "style_match": style, "cost": cost}}
    if checks is not None:
        t["checks"] = checks
    return t


class EvalGateTest(unittest.TestCase):
    def setUp(self):
        self.base = result({"t1": task(4.0, locked=True, checks={"numbers": True}), "t2": task(3.0), "t3": task(5.0)})

    def test_accept_when_not_worse(self):
        cand = result({"t1": task(4.0, locked=True, checks={"numbers": True}), "t2": task(3.5), "t3": task(5.0, cost=0.105)})
        res = eval_gate.evaluate(self.base, cand)
        self.assertEqual(res["decision"], "accept", res["reasons"])
        self.assertIn("ACCEPT", eval_gate.report(res))

    def test_reject_mean_regression(self):
        cand = result({"t1": task(4.0, locked=True, checks={"numbers": True}), "t2": task(3.0, style=3.0), "t3": task(5.0)})
        res = eval_gate.evaluate(self.base, cand)
        self.assertEqual(res["decision"], "reject")
        self.assertTrue(any("style_match" in r for r in res["reasons"]))

    def test_reject_cost_beyond_relative_tolerance_and_override(self):
        cand = result({k: dict(v, scores=dict(v["scores"], cost=0.2)) for k, v in self.base["tasks"].items()})
        self.assertEqual(eval_gate.evaluate(self.base, cand)["decision"], "reject")
        res = eval_gate.evaluate(self.base, cand, tolerances={"cost": (1.5, True)})
        self.assertEqual(res["decision"], "accept", res["reasons"])

    def test_reject_locked_correctness_drop_even_if_mean_improves(self):
        cand = result({"t1": task(3.5, locked=True, checks={"numbers": True}), "t2": task(5.0), "t3": task(5.0)})
        res = eval_gate.evaluate(self.base, cand)
        self.assertEqual(res["decision"], "reject")
        self.assertEqual(res["locked_correctness_drops"], ["t1"])
        corr = next(r for r in res["dimensions"] if r["dimension"] == "correctness")
        self.assertEqual(corr["status"], "improved")

    def test_reject_locked_check_regression(self):
        cand = result({"t1": task(4.0, locked=True, checks={"numbers": False}), "t2": task(3.0), "t3": task(5.0)})
        res = eval_gate.evaluate(self.base, cand)
        self.assertEqual(res["decision"], "reject")
        self.assertTrue(any("check 'numbers'" in r for r in res["reasons"]))

    def test_reject_self_judging_and_missing_and_set_mismatch(self):
        cand = result({"t1": task(4.0, locked=True, checks={"numbers": True})}, producer="sonnet", judge="Sonnet",
                      eval_set_sha256="abc")
        base = dict(self.base, eval_set_sha256="def")
        reasons = " ".join(eval_gate.evaluate(base, cand)["reasons"])
        self.assertIn("judge model", reasons)
        self.assertIn("missing from candidate", reasons)
        self.assertIn("eval_set_sha256 differs", reasons)

    def test_cli_exit_codes_and_list_format(self):
        tmp = pathlib.Path(tempfile.mkdtemp())
        try:
            b, c = tmp / "b.json", tmp / "c.json"
            b.write_text(json.dumps(self.base))
            c.write_text(json.dumps(result([dict(task(4.0, locked=True, checks={"numbers": True}), id="t1"),
                                            dict(task(3.0), id="t2"), dict(task(5.0), id="t3")])))
            code, out, _ = run_main(eval_gate, [str(b), str(c)])
            self.assertEqual(code, 0, out)
            code, out, _ = run_main(eval_gate, [str(b), str(c), "--tolerance", "correctness=0", "--json"])
            self.assertEqual(json.loads(out)["decision"], "accept")
            c.write_text(json.dumps(result({"t1": task(1.0, locked=True)})))
            code, out, _ = run_main(eval_gate, [str(b), str(c)])
            self.assertEqual(code, 1)
            self.assertIn("Reasons for rejection", out)
            c.write_text("not json")
            code, _, err = run_main(eval_gate, [str(b), str(c)])
            self.assertEqual(code, 2)
            self.assertIn("not valid JSON", err)
        finally:
            shutil.rmtree(tmp, ignore_errors=True)


class WeeklyReportTest(TempDataDir):
    def test_report_per_scope(self):
        # label evt_p2 as a correction via a new append-only label event
        with open(self.log / "2026-10.jsonl", "a", encoding="utf-8") as f:
            f.write(json.dumps({"id": "evt_l1", "ts": "2026-10-16T00:00:00Z", "type": "label",
                                "labels_for": "evt_p2", "is_correction": True, "intent": "formal"}) + "\n")
        code, md, _ = run_main(weekly_report, ["--data-dir", str(self.tmp), "--from", "2026-10-10", "--to", "2026-10-16"])
        self.assertEqual(code, 0)
        rows = {l.split("|")[1].strip(): [c.strip() for c in l.split("|")[2:-1]]
                for l in md.splitlines() if l.startswith("| ") and not l.startswith("| scope")}
        # columns: events prompts sessions corrections corr_rate mishaps decisions verifs p/f/h pass_rate cost unlabeled
        tr = rows["translation/acme"]
        self.assertEqual(tr[:5], ["2", "2", "1", "1", "50%"])
        code_row = rows["code/harness"]
        self.assertEqual(code_row[5], "1")      # mishaps
        self.assertEqual(code_row[6], "1")      # decisions
        self.assertEqual(code_row[7], "2")      # verifications
        self.assertEqual(code_row[8], "1/1/0")
        self.assertEqual(code_row[9], "50%")
        self.assertEqual(code_row[10], "$0.75")
        self.assertIn("unscoped", rows)          # evt_p3 + session_end with a non-area cwd
        self.assertNotIn("old", md)
        self.assertIn("deleted the wrong file", md)
        self.assertIn("not valid JSON", md)
        total = rows["**total**"]
        self.assertEqual(total[0], "8")          # in-range sample events; label events excluded

    def test_empty_range(self):
        code, md, _ = run_main(weekly_report, ["--data-dir", str(self.tmp), "--from", "2020-01-01", "--to", "2020-01-07"])
        self.assertEqual(code, 0)
        self.assertIn("No events in this range", md)

    def test_scope_from_hint(self):
        areas = weekly_report.load_areas(ROOT / "schema" / "ontology.yaml")
        self.assertIn("job-search", areas)
        self.assertEqual(weekly_report.scope_from_hint("/a/job-search/acme/x", areas), "job-search/acme")
        self.assertIsNone(weekly_report.scope_from_hint("/a/b", areas))


class LogEventHookTest(unittest.TestCase):
    def setUp(self):
        self.tmp = pathlib.Path(tempfile.mkdtemp(prefix="harness-hook-"))
        self.env = dict(os.environ, HARNESS_DATA=str(self.tmp))

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def run_hook(self, kind, stdin):
        return subprocess.run([sys.executable, "-I", str(ROOT / "hooks" / "log_event.py"), kind],
                              input=stdin, env=self.env, capture_output=True, text=True, timeout=30)

    def lines(self):
        files = list((self.tmp / "log").glob("*.jsonl"))
        self.assertEqual(len(files), 1)
        return [json.loads(l) for l in files[0].read_text(encoding="utf-8").splitlines()]

    def test_prompt_written(self):
        payload = {"session_id": "abc", "cwd": "/w/translation/acme", "prompt": "번역해 주세요", "transcript_path": "/t.jsonl"}
        p = self.run_hook("prompt", json.dumps(payload))
        self.assertEqual(p.returncode, 0, p.stderr)
        [ev] = self.lines()
        self.assertEqual(ev["type"], "prompt")
        self.assertEqual(ev["actor"], "me")
        self.assertEqual(ev["content"], "번역해 주세요")
        self.assertEqual(ev["session_id"], "abc")
        self.assertEqual(ev["scope_hint"], "/w/translation/acme")
        self.assertTrue(ev["id"].startswith("evt_"))

    def test_session_end_and_bad_stdin_append(self):
        self.assertEqual(self.run_hook("session_end", json.dumps({"reason": "clear", "session_id": "s"})).returncode, 0)
        self.assertEqual(self.run_hook("prompt", "not json at all").returncode, 0)
        evs = self.lines()
        self.assertEqual(len(evs), 2)
        self.assertEqual(evs[0]["end_reason"], "clear")
        self.assertIsNone(evs[0]["content"])
        self.assertEqual(evs[1]["type"], "prompt")


class StaticFilesTest(unittest.TestCase):
    def test_autocommit_script_syntax(self):
        bash = shutil.which("bash")
        if not bash:
            self.skipTest("bash not available")
        p = subprocess.run([bash, "-n", str(SCRIPTS / "autocommit_data.sh")], capture_output=True, text=True)
        self.assertEqual(p.returncode, 0, p.stderr)

    def test_rubrics_have_required_sections(self):
        names = {"translation", "annotation-batch", "job-application", "research-report",
                 "code-change", "asset-package", "intake-extraction"}
        found = {p.stem for p in (ROOT / "rubrics").glob("*.yaml")}
        self.assertTrue(names <= found, names - found)
        for n in names:
            text = (ROOT / "rubrics" / f"{n}.yaml").read_text(encoding="utf-8")
            for key in ("criteria:", "automatic_checks:", "dimensions:", "anchors:",
                        "model_must_differ_from_producer: true"):
                self.assertIn(key, text, f"{n}: {key}")
            for dim in ("correctness", "correction_rate", "cost", "time", "style_match", "outcome"):
                self.assertIn(f"  {dim}:", text, f"{n}: dimension {dim}")


if __name__ == "__main__":
    unittest.main()
