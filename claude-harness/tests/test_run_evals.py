"""Tests for scripts/run_evals.py and the evals/harness task set.

Run from the harness root:  python3 -I -m unittest discover -s tests -t .
"""
import copy
import importlib.util
import json
import os
import pathlib
import shutil
import subprocess
import sys
import tempfile
import unittest

ROOT = pathlib.Path(__file__).resolve().parent.parent
SCRIPT = ROOT / "scripts" / "run_evals.py"
AREA = ROOT / "evals" / "harness"
sys.dont_write_bytecode = True


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


re_ = load("run_evals", SCRIPT)
gate = load("eval_gate", ROOT / "scripts" / "eval_gate.py")

MINI_TASK = """\
id: harness-900
area: harness
title: "mini"
rubric: rubrics/code-change.yaml
split: train
status: draft
lock_sha256: ""
locked: true
input:
  files:
    - path: a.txt
      content: |
        가족의 비밀
  steps:
    - id: count
      run: ${PY} -I ${ROOT}/scripts/textlen.py a.txt
criteria:
  - {id: checks_pass, dimension: correctness}
expected_checks:
  - {id: exit_ok, kind: exit_code, value: 0}
  - {id: six, kind: stdout_contains, values: ["chars=6"]}
"""


def cli(*args, env=None):
    e = {k: v for k, v in os.environ.items() if not k.startswith("HARNESS_")}
    e.update(env or {})
    return subprocess.run([sys.executable, "-I", str(SCRIPT), *args], capture_output=True, text=True,
                          env=e, timeout=300)


class Tmp(unittest.TestCase):
    def setUp(self):
        self.tmp = pathlib.Path(tempfile.mkdtemp(prefix="run-evals-test-"))

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def mini_area(self, text=MINI_TASK, name="harness-900.yaml"):
        tdir = self.tmp / "evals" / "harness" / "tasks"
        tdir.mkdir(parents=True, exist_ok=True)
        (tdir / name).write_text(text, encoding="utf-8")
        return self.tmp / "evals"


class YamlSubsetTest(unittest.TestCase):
    def test_block_scalars_keep_lines_verbatim(self):
        doc = re_.yaml_load("a: |\n  # Progress\n    indented\n\n  - [x] done\nb: |-\n  x\nc: 1\n")
        self.assertEqual(doc["a"], "# Progress\n  indented\n\n- [x] done\n")
        self.assertEqual(doc["b"], "x")
        self.assertEqual(doc["c"], 1)

    def test_flow_quotes_comments_and_lists_of_maps(self):
        doc = re_.yaml_load('x: "q # kept"  # dropped\ny: [1, "two", {k: v, "m~": \'it\'\'s\'}]\n'
                            'z:\n  - id: s1\n    run: a b\n  - {id: s2, run: c}\nh: "\\u1112\\u1161"\n')
        self.assertEqual(doc["x"], "q # kept")
        self.assertEqual(doc["y"], [1, "two", {"k": "v", "m~": "it's"}])
        self.assertEqual(doc["z"], [{"id": "s1", "run": "a b"}, {"id": "s2", "run": "c"}])
        self.assertEqual(doc["h"], "\u1112\u1161")

    def test_errors(self):
        for bad in ("a: [1, 2\n", "a: 1\na: 2\n", "a: 1\n   b: 2\n", "\ta: 1\n"):
            with self.assertRaises(re_.YamlError, msg=bad):
                re_.yaml_load(bad)


class TaskSetTest(unittest.TestCase):
    def setUp(self):
        self.files = re_.task_files(AREA)
        self.tasks = [re_.load_task(f) for f in self.files]

    def test_twenty_tasks_split_14_6(self):
        self.assertEqual(len(self.tasks), 20)
        ids = [t["id"] for t in self.tasks]
        self.assertEqual(len(set(ids)), 20)
        splits = [t["split"] for t in self.tasks]
        self.assertEqual((splits.count("train"), splits.count("holdout")), (14, 6))

    def test_conventions(self):
        for t, f in zip(self.tasks, self.files):
            with self.subTest(task=t["id"]):
                self.assertRegex(t["id"], r"^harness-\d{3}$")       # EvalTask.id_pattern
                self.assertEqual(f.stem, t["id"])
                self.assertEqual(t["area"], "harness")
                self.assertIn(t.get("status"), ("draft", "locked"))
                self.assertIs(t["locked"], True)
                self.assertIn("lock_sha256", t)
                self.assertTrue((ROOT / t["rubric"]).is_file())
                dims = {c["dimension"] for c in t["criteria"]}
                self.assertIn("correctness", dims)
                self.assertTrue(set(dims) <= {"correctness", "time"})
                for comp in t.get("components") or []:
                    self.assertTrue((ROOT / comp).exists(), comp)

    def test_no_task_touches_real_paths(self):
        for f in self.files:
            text = f.read_text(encoding="utf-8")
            self.assertNotIn("~/", text, f.name)
            self.assertNotIn("harness-data", text, f.name)
            self.assertNotIn("http://", text, f.name)


class RunEndToEndTest(Tmp):
    def test_two_tasks_produce_gate_compatible_json(self):
        out = self.tmp / "run.json"
        p = cli("--area", "harness", "--task", "harness-010", "--task", "harness-018", "--out", str(out))
        self.assertEqual(p.returncode, 0, p.stderr)
        run = gate.load(str(out))
        self.assertEqual(set(run["tasks"]), {"harness-010", "harness-018"})
        self.assertEqual(run["judge_model"], "deterministic")
        self.assertNotEqual(run["producer_model"], run["judge_model"])
        self.assertEqual(run["units"]["time"], "ms")
        self.assertRegex(run["eval_set_sha256"], r"^[0-9a-f]{64}$")
        self.assertTrue(run["run_at"].endswith("Z"))
        for tid, t in run["tasks"].items():
            self.assertIs(t["locked"], True)
            self.assertEqual(t["judge"], "deterministic")
            self.assertEqual(t["scores"]["correctness"], 1.0)
            self.assertIsInstance(t["scores"]["time"], float)
            self.assertTrue(t["checks"])
            self.assertTrue(all(t["checks"].values()))
        self.assertEqual(gate.evaluate(run, run)["decision"], "accept")

    def test_gate_rejects_synthetic_regression(self):
        out = self.tmp / "base.json"
        self.assertEqual(cli("--area", "harness", "--task", "harness-013", "--task", "harness-001",
                             "--out", str(out)).returncode, 0)
        base = gate.load(str(out))
        cand = copy.deepcopy(base)
        t = cand["tasks"]["harness-001"]
        t["scores"]["correctness"] = 0.0
        t["checks"]["counts"] = False
        res = gate.evaluate(base, cand)
        self.assertEqual(res["decision"], "reject")
        self.assertIn("harness-001", res["locked_correctness_drops"])
        self.assertTrue(any("check 'counts'" in r for r in res["reasons"]))
        # --baseline convenience: identical code accepts; time noise has a wide default tolerance
        p = cli("--area", "harness", "--task", "harness-013", "--task", "harness-001",
                "--out", str(self.tmp / "again.json"), "--baseline", str(out))
        self.assertEqual(p.returncode, 0, p.stderr)
        self.assertIn("Eval gate: ACCEPT", p.stderr)
        bad = self.tmp / "bad.json"
        bad.write_text(json.dumps(cand), encoding="utf-8")
        p = cli("--area", "harness", "--task", "harness-013", "--task", "harness-001",
                "--out", str(self.tmp / "third.json"), "--baseline", str(bad))
        self.assertEqual(p.returncode, 0, p.stderr)     # 0 -> 1 on a locked task is an improvement
        self.assertIn("Eval gate: ACCEPT", p.stderr)
        p = cli("--area", "harness", "--task", "harness-001", "--out", str(self.tmp / "fewer.json"),
                "--baseline", str(out))
        self.assertEqual(p.returncode, 1)               # different task subset -> different eval set
        self.assertIn("REJECT", p.stderr)

    def test_split_selects_and_names_the_set(self):
        out = self.tmp / "h.json"
        p = cli("--area", "harness", "--split", "holdout", "--out", str(out), "--quiet")
        self.assertEqual(p.returncode, 0, p.stderr)
        run = json.loads(out.read_text(encoding="utf-8"))
        self.assertEqual(run["eval_set"], "harness/holdout")
        self.assertEqual(len(run["tasks"]), 6)
        self.assertTrue(all(t["split"] == "holdout" for t in run["tasks"].values()))

    def test_whole_harness_area_passes(self):
        out = self.tmp / "all.json"
        p = cli("--area", "harness", "--out", str(out))
        self.assertEqual(p.returncode, 0, p.stderr)
        run = json.loads(out.read_text(encoding="utf-8"))
        failed = {tid: t.get("failures") for tid, t in run["tasks"].items() if t["scores"]["correctness"] != 1.0}
        self.assertEqual(failed, {})
        self.assertEqual(run["summary"], {"tasks": 20, "passed": 20, "failed": 0})
        self.assertEqual(run["eval_set"], "harness")

    def test_default_output_goes_under_harness_data(self):
        evals = self.mini_area()
        data = self.tmp / "data"
        p = cli("--area", "harness", "--evals-dir", str(evals), "--quiet", env={"HARNESS_DATA": str(data)})
        self.assertEqual(p.returncode, 0, p.stderr)
        [f] = list((data / "evals" / "results" / "harness").glob("*.json"))
        self.assertRegex(f.name, r"^\d{8}T\d{6}Z\.json$")


class RunnerBehaviourTest(Tmp):
    def run_mini(self, text, *extra, env=None):
        evals = self.mini_area(text)
        out = self.tmp / "r.json"
        p = cli("--area", "harness", "--evals-dir", str(evals), "--out", str(out), *extra, env=env)
        return p, (json.loads(out.read_text(encoding="utf-8")) if out.exists() else None)

    def test_failing_check_scores_zero_with_reason(self):
        p, run = self.run_mini(MINI_TASK.replace('"chars=6"', '"chars=7"'))
        self.assertEqual(p.returncode, 1)
        t = run["tasks"]["harness-900"]
        self.assertEqual(t["scores"]["correctness"], 0.0)
        self.assertEqual(t["checks"], {"exit_ok": True, "six": False})
        self.assertIn("chars=7", t["failures"][0])

    def test_timeout_fails_task(self):
        text = MINI_TASK.replace("run: ${PY} -I ${ROOT}/scripts/textlen.py a.txt",
                                 'run: ${PY} -I -c "import time; time.sleep(5)"\n      timeout: 0.5')
        p, run = self.run_mini(text)
        self.assertEqual(p.returncode, 1)
        self.assertTrue(any("timed out" in f for f in run["tasks"]["harness-900"]["failures"]))

    def test_path_escape_rejected(self):
        p, run = self.run_mini(MINI_TASK.replace("path: a.txt", "path: ../escape.txt"))
        self.assertEqual(p.returncode, 1)
        self.assertTrue(any("escapes" in f for f in run["tasks"]["harness-900"]["failures"]))
        self.assertFalse(any(self.tmp.glob("escape.txt")))

    def test_clean_environment(self):
        text = MINI_TASK.replace("run: ${PY} -I ${ROOT}/scripts/textlen.py a.txt",
                                 "run: ${PY} -I -c \"import os; print(sorted(k for k in os.environ if k.startswith('HARNESS')), os.environ['HOME'])\"")
        text = text.replace('values: ["chars=6"]', "values: [\"'HARNESS_DATA', 'HARNESS_STATE']\", \"/home\"]")
        p, run = self.run_mini(text, env={"HARNESS_VERIFY_GATE": "0", "HARNESS_NTFY_TOPIC": "leak"})
        self.assertEqual(p.returncode, 0, p.stderr + json.dumps(run))

    def test_lock_hash_and_refusal(self):
        evals = self.mini_area()
        p = cli("--area", "harness", "--evals-dir", str(evals), "--lock-hash")
        self.assertEqual(p.returncode, 0)
        tid, h, state = p.stdout.strip().split("\t")
        self.assertEqual((tid, state), ("harness-900", "unlocked"))
        path = evals / "harness" / "tasks" / "harness-900.yaml"
        locked = MINI_TASK.replace("status: draft", "status: locked").replace('lock_sha256: ""', f'lock_sha256: "{h}"')
        path.write_text(locked, encoding="utf-8")
        p = cli("--area", "harness", "--evals-dir", str(evals), "--lock-hash")
        self.assertTrue(p.stdout.strip().endswith("\tlocked"))      # flipping status keeps the hash
        out = self.tmp / "ok.json"
        self.assertEqual(cli("--area", "harness", "--evals-dir", str(evals), "--out", str(out)).returncode, 0)
        path.write_text(locked.replace('"chars=6"', '"chars="'), encoding="utf-8")
        out2 = self.tmp / "refused.json"
        p = cli("--area", "harness", "--evals-dir", str(evals), "--out", str(out2))
        self.assertEqual(p.returncode, 2)
        self.assertIn("refusing to run", p.stderr)
        self.assertFalse(out2.exists())

    def test_eval_set_hash_tracks_content_not_lock_lines(self):
        a, b, c = self.tmp / "a.yaml", self.tmp / "b.yaml", self.tmp / "c.yaml"
        a.write_text(MINI_TASK, encoding="utf-8")
        b.write_text(MINI_TASK.replace("status: draft", "status: locked")
                     .replace('lock_sha256: ""', 'lock_sha256: "abc"'), encoding="utf-8")
        c.write_text(MINI_TASK.replace("chars=6", "chars=5"), encoding="utf-8")
        h = re_.eval_set_hash
        self.assertEqual(re_.lock_hash(a.read_text()), re_.lock_hash(b.read_text()))
        self.assertNotEqual(re_.lock_hash(a.read_text()), re_.lock_hash(c.read_text()))
        self.assertNotEqual(h([a]), h([c]))

    def test_invalid_task_is_usage_error(self):
        for bad in (MINI_TASK.replace("split: train", "split: dev"),
                    MINI_TASK.replace("kind: exit_code", "kind: vibes"),
                    MINI_TASK.replace("area: harness", "area: code")):
            p, _ = self.run_mini(bad)
            self.assertEqual(p.returncode, 2, bad)


if __name__ == "__main__":
    unittest.main()
