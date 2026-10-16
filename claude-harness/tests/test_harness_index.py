"""Tests for scripts/harness_index.py (component graph, checks, eval coverage, generated docs). Run from the
harness root:
    python3 -I -m unittest tests.test_harness_index
"""
import importlib.util
import io
import json
import pathlib
import re
import shutil
import subprocess
import sys
import tempfile
import textwrap
import unittest
from contextlib import redirect_stderr, redirect_stdout

ROOT = pathlib.Path(__file__).resolve().parent.parent
SCRIPT = ROOT / "scripts" / "harness_index.py"
sys.dont_write_bytecode = True
_spec = importlib.util.spec_from_file_location("harness_index", SCRIPT)
hi = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(hi)

TIMESTAMP = re.compile(r"(?m)^.*(generated_at|Generated:).*$")


def normalize(text):
    return TIMESTAMP.sub("", text)


class RealRepoTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.g = hi.scan(ROOT)

    def test_check_has_no_errors(self):
        buf = io.StringIO()
        with redirect_stdout(buf), redirect_stderr(io.StringIO()):
            code = hi.main(["--check", "--quiet"])
        self.assertEqual(code, 0, buf.getvalue())
        self.assertEqual(self.g.errors, [])

    def test_coverage_meets_config_minimum(self):
        cfg = hi.load_config(ROOT)
        self.assertGreaterEqual(self.g.coverage["percent"], float(cfg.get("coverage_min", 0)))
        for row in self.g.coverage["rows"]:
            if row["status"] == "covered":
                self.assertTrue(row["rubrics"] and row["areas"], row)

    def test_every_eval_area_has_a_rubric(self):
        for e in self.g.of_kind("eval"):
            self.assertTrue(e["attrs"]["template"] or e["attrs"]["repo_tasks"], e["name"])
            self.assertTrue(e["attrs"]["rubrics"], e["name"])
            for rb in e["attrs"]["rubrics"]:
                self.assertIn(f"rubric:{rb}", self.g.nodes, e["name"])

    def test_generated_files_are_up_to_date(self):
        """Regenerate in a temp copy of the harness and compare with the committed files."""
        with tempfile.TemporaryDirectory() as tmp:
            dst = pathlib.Path(tmp) / "harness"
            shutil.copytree(ROOT, dst, ignore=shutil.ignore_patterns("__pycache__", ".git", "*.pyc"))
            p = subprocess.run([sys.executable, "-I", str(dst / "scripts" / "harness_index.py"), "--write", "--quiet"],
                               capture_output=True, text=True)
            self.assertIn(p.returncode, (0, 1), p.stderr)
            for rel in (hi.INDEX_PATH, hi.JSON_PATH):
                with self.subTest(rel=rel):
                    committed = ROOT / rel
                    self.assertTrue(committed.exists(), f"{rel} missing: run python3 -I scripts/harness_index.py --write")
                    self.assertEqual(normalize(committed.read_text(encoding="utf-8")),
                                     normalize((dst / rel).read_text(encoding="utf-8")),
                                     f"{rel} is stale: run python3 -I scripts/harness_index.py --write")

    def test_index_is_compact_and_marked_generated(self):
        text = (ROOT / hi.INDEX_PATH).read_text(encoding="utf-8")
        self.assertIn(hi.HEADER, text.splitlines()[0])
        self.assertLess(len(text.splitlines()), 250)
        data = json.loads((ROOT / hi.JSON_PATH).read_text(encoding="utf-8"))
        self.assertEqual(data["note"], hi.HEADER)

    def test_affected_areas(self):
        res = hi.affected(self.g, ["skills/translate/SKILL.md"])
        self.assertEqual(res["changed"], ["skill:translate"])
        self.assertIn("translation", res["areas"])
        everything = hi.affected(self.g, ["global/CLAUDE.md"])["areas"]
        self.assertEqual(everything, sorted(e["name"] for e in self.g.of_kind("eval")))

    def test_learning_coverage_has_no_errors(self):
        lerr = [e for e in self.g.errors if e.startswith(("learning", hi.LEARNING_PATH))]
        self.assertEqual(lerr, [])
        lc = self.g.learning
        work = {r["id"] for r in self.g.coverage["rows"] if r["status"] != "exempt"}
        self.assertFalse(work & set(lc["gaps"]), "work components without a learning contract")
        self.assertEqual(lc["components"], len(self.g.of_kind("agent") + self.g.of_kind("skill") + self.g.of_kind("script")))

    def test_dot_output(self):
        dot = hi.render_dot(self.g)
        self.assertTrue(dot.startswith("digraph harness {"))
        self.assertIn('"agent:translator" -> "skill:translate" [label="preloads"', dot)


def write(root, rel, text):
    p = root / rel
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(textwrap.dedent(text).lstrip("\n"), encoding="utf-8")


class MiniHarnessTest(unittest.TestCase):
    """A synthetic harness with one example of each problem the checks must catch."""

    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.root = pathlib.Path(self._tmp.name)
        r = self.root
        write(r, "agents/writer.md", """
            ---
            name: writer
            description: Writes things. Use for writing.
            model: sonnet
            tools: Read, Write
            skills: [work, manual]
            ---
            Use the `helper` skill and run scripts/tool.py. Docs: docs/GUIDE.md.
            """)
        write(r, "agents/nomodel.md", """
            ---
            name: nomodel
            description: Has no model.
            tools: Read
            ---
            """)
        write(r, "agents/spawner.md", """
            ---
            name: spawner
            description: A worker that can spawn agents.
            model: haiku
            tools: Read, Agent
            ---
            """)
        write(r, "agents/boss.md", """
            ---
            name: boss
            description: Router.
            model: opus
            ---
            Route writing to `writer`, then `nomodel`, `spawner`.
            """)
        write(r, "skills/work/SKILL.md", """
            ---
            name: work
            description: Main work skill.
            ---
            Run `python3 -I ${CLAUDE_PLUGIN_ROOT}/scripts/tool.py` and `scripts/missing.py`.
            Score with rubrics/work.yaml. Then the `helper` skill and the `ghost` skill.
            """)
        write(r, "skills/helper/SKILL.md", """
            ---
            name: helper
            description: Helper. Also /work.
            ---
            Nothing else.
            """)
        write(r, "skills/manual/SKILL.md", """
            ---
            name: manual
            description: Manual only.
            disable-model-invocation: true
            ---
            """)
        write(r, "skills/lonely/SKILL.md", """
            ---
            name: lonely
            description: Nobody mentions me; I produce work but have no rubric.
            ---
            """)
        write(r, "scripts/tool.py", '"""Tool that writes the store."""\nprint("store/items.jsonl")\n')
        write(r, "hooks/hooks.json", json.dumps({"hooks": {"Stop": [{"hooks": [
            {"type": "command", "command": "python3 -I \"${CLAUDE_PLUGIN_ROOT}/hooks/gate.py\""}]}]}}))
        write(r, "hooks/gate.py", '"""Stop gate."""\n')
        write(r, "rubrics/work.yaml", """
            rubric: work
            version: 0.1.0
            applies_to: "Work output"
            producer_agent: writer
            criteria: []
            """)
        write(r, "rubrics/unused.yaml", """
            status: draft
            rubric: unused
            applies_to: "Nothing"
            producer_agent: nobody
            criteria: []
            """)
        write(r, "evals/area1/task_template.yaml", """
            # Eval task template: area one. Copy to tasks/area1-NNN.yaml.
            id: area1-000
            area: area1
            rubric: rubrics/work.yaml
            """)
        write(r, "docs/GUIDE.md", "# Guide\n\nSee principle 1 and principle 9.\n")
        write(r, "global/PRINCIPLES.md", "# P\n\n1. **First.** Text.\n")
        write(r, "schema/ontology.yaml", """
            version: 0.0.1
            enums:
              eval_area: [area1, area2]
            types:
              Item:
                desc: an item
                store: {root: harness-data, path: store/items.jsonl, format: jsonl, status: active, writer: "scripts/tool.py"}
              Ghost:
                desc: written by nobody real
                store: {root: harness-data, path: "ghost/*.jsonl", format: jsonl, status: active, writer: "scripts/ghost.py, skills/nope"}
            """)
        write(r, "scripts/harness_index.json", json.dumps({
            "coverage_min": 0, "exempt": {"agent:boss": "router", "skill:helper": "meta", "agent:gone": "stale"},
            "external_skills": [], "may_spawn_agents": ["boss"]}))
        self.g = hi.scan(self.root)

    def tearDown(self):
        self._tmp.cleanup()

    def has(self, items, pattern):
        return any(re.search(pattern, x) for x in items)

    def test_nodes_and_edges(self):
        g = self.g
        for nid in ("agent:writer", "skill:work", "script:scripts/tool.py", "script:hooks/gate.py",
                    "rubric:work", "eval:area1", "type:Item", "doc:docs/GUIDE.md", "principle:1"):
            self.assertIn(nid, g.nodes)
        e = g.edges
        self.assertIn(("agent:writer", "skill:work", "preloads"), e)
        self.assertIn(("skill:work", "script:scripts/tool.py", "runs"), e)
        self.assertIn(("skill:work", "rubric:work", "scored_by"), e)
        self.assertIn(("skill:work", "skill:helper", "invokes"), e)
        self.assertIn(("skill:helper", "skill:work", "invokes"), e)          # via /work
        self.assertIn(("agent:boss", "agent:writer", "routes_to"), e)
        self.assertIn(("rubric:work", "eval:area1", "evaluated_in"), e)
        self.assertIn(("script:scripts/tool.py", "type:Item", "writes"), e)
        self.assertIn(("script:scripts/tool.py", "type:Item", "touches"), e)
        self.assertIn(("doc:docs/GUIDE.md", "principle:1", "cites"), e)
        self.assertEqual(g.nodes["script:scripts/tool.py"]["purpose"], "Tool that writes the store.")
        [hook] = g.of_kind("hook")
        self.assertEqual(hook["attrs"]["script"], "hooks/gate.py")
        self.assertIn((hook["id"], "script:hooks/gate.py", "hook_runs"), e)

    def test_dangling_refs_are_errors(self):
        errs = self.g.errors
        self.assertTrue(self.has(errs, r"dangling: skills/work/SKILL.md references scripts/missing.py"), errs)
        self.assertTrue(self.has(errs, r"dangling: .* skill 'ghost'"), errs)
        self.assertTrue(self.has(errs, r"ontology: Ghost.store.writer names scripts/ghost.py"), errs)
        self.assertTrue(self.has(errs, r"ontology: Ghost.store.writer names skills/nope"), errs)

    def test_agent_checks(self):
        errs = self.g.errors
        self.assertTrue(self.has(errs, r"agents/nomodel.md: no explicit `model:`"), errs)
        self.assertTrue(self.has(errs, r"agents/writer.md: preloads 'manual', which has disable-model-invocation"), errs)
        self.assertTrue(self.has(errs, r"agents/spawner.md: worker agent lists the Agent tool"), errs)
        self.assertTrue(self.has(errs, r"agents/nomodel.md") and not self.has(errs, r"agents/boss.md: worker"), errs)

    def test_orphans_and_other_warnings(self):
        w = self.g.warnings
        self.assertTrue(self.has(w, r"orphan: skill lonely"), w)
        self.assertFalse(self.has(w, r"orphan: skill work"), w)
        self.assertFalse(self.has(w, r"orphan: rubric work"), w)
        self.assertTrue(self.has(w, r"orphan: rubric unused"), w)
        self.assertTrue(self.has(w, r"draft rubric: rubrics/unused.yaml"), w)
        self.assertTrue(self.has(w, r"exempt entry 'agent:gone' names no component"), w)
        self.assertTrue(self.has(w, r"ontology eval_area 'area2' has no evals/area2/ folder"), w)
        self.assertTrue(self.has(w, r"principle 9"), w)

    def test_coverage(self):
        rows = {r["id"]: r for r in self.g.coverage["rows"]}
        self.assertEqual(rows["skill:work"]["status"], "covered")
        self.assertEqual(rows["skill:work"]["areas"], ["eval:area1"])
        self.assertEqual(rows["agent:writer"]["status"], "covered")         # producer_agent
        self.assertEqual(rows["skill:lonely"]["status"], "no-rubric")
        self.assertEqual(rows["agent:boss"]["status"], "exempt")
        self.assertIn("skill:lonely", self.g.coverage["gaps"])
        self.assertTrue(self.has(self.g.warnings, r"coverage gap: skill:lonely"))
        self.assertLess(self.g.coverage["percent"], 100)
        self.assertFalse(self.has(self.g.errors, r"below coverage_min"))

    def test_coverage_min_turns_gaps_into_an_error(self):
        cfg = hi.load_config(self.root)
        cfg["coverage_min"] = 100
        g = hi.scan(self.root, cfg)
        self.assertTrue(self.has(g.errors, r"eval coverage .* below coverage_min 100%"), g.errors)

    def test_rubric_without_eval_area_is_a_gap(self):
        cfg = hi.load_config(self.root)
        (self.root / "evals" / "area1" / "task_template.yaml").unlink()
        (self.root / "evals" / "area1").rmdir()
        g = hi.scan(self.root, cfg)
        rows = {r["id"]: r for r in g.coverage["rows"]}
        self.assertEqual(rows["skill:work"]["status"], "no-area")

    def test_eval_area_must_be_in_ontology(self):
        write(self.root, "evals/rogue/task_template.yaml", "id: rogue-000\narea: rogue\nrubric: rubrics/work.yaml\n")
        g = hi.scan(self.root)
        self.assertTrue(self.has(g.errors, r"evals/rogue/ is not in the ontology's eval_area enum"), g.errors)

    def test_affected(self):
        res = hi.affected(self.g, ["scripts/tool.py"])
        self.assertEqual(res["changed"], ["script:scripts/tool.py"])
        self.assertIn("skill:work", res["dependents"])
        self.assertIn("agent:writer", res["dependents"])
        self.assertEqual(res["areas"], ["area1"])
        # a changed router (exempt) re-runs the areas it routes to
        self.assertEqual(hi.affected(self.g, ["agents/boss.md"])["areas"], ["area1"])

    def test_learning_contracts(self):
        g = self.g
        # no contracts file: the work skill is an error, the exempt-from-evals helper only a warning
        self.assertTrue(self.has(g.errors, r"learning: work component skill:work has no learning contract"), g.errors)
        self.assertTrue(self.has(g.warnings, r"learning gap: skill:helper"), g.warnings)
        write(self.root, hi.LEARNING_PATH, """
            contracts:
              "skill:work":
                status: draft
                signals: [user corrections, verifier verdicts]
                logged_as: [event:correction, type:Item]
                learns: [type:Item, thresholds]
                evaluated_by: [eval:area1, rubric:work, metric:correction rate]
                cadence: per-run, weekly
                owner: self
              "agent:writer":
                signals: [edits]
                logged_as: [event:nonsense, "nowhere"]
                learns: [type:Missing]
                evaluated_by: [eval:nope]
                cadence: hourly
                owner: somebody
              "skill:future":
                status: todo
              "skill:stale":
                signals: [x]
            exempt:
              "script:scripts/tool.py": "pure utility"
              "skill:helper": ""
            """)
        write(self.root, "schema/ontology.yaml",
              (self.root / "schema/ontology.yaml").read_text() .replace("enums:\n", "enums:\n  event_type: [correction, task]\n"))
        g = hi.scan(self.root)
        e, w = g.errors, g.warnings
        self.assertFalse(self.has(e, r"skill:work"), e)
        self.assertIn(("skill:work", "type:Item", "learns_into"), g.edges)
        for pat in (r"agent:writer names event type 'nonsense'", r"agent:writer logged_as 'nowhere'",
                    r"agent:writer names ontology type 'Missing'", r"agent:writer evaluated_by eval:nope",
                    r"agent:writer cadence 'hourly'", r"agent:writer owner 'somebody'",
                    r"exemption skill:helper needs a reason", r"agent:writer has no `cadence`|agent:writer cadence"):
            self.assertTrue(self.has(e, pat), (pat, e))
        self.assertTrue(self.has(w, r"contract 'skill:stale' names no component"), w)
        self.assertFalse(self.has(w, r"skill:future"), w)
        self.assertEqual(g.learning["todo"], ["skill:future"])
        rows = {r["id"]: r["status"] for r in g.learning["rows"]}
        self.assertEqual(rows["skill:work"], "contract")
        self.assertEqual(rows["script:scripts/tool.py"], "exempt")
        self.assertEqual(rows["skill:lonely"], "gap")
        self.assertTrue(self.has(e, r"learning: work component skill:lonely"), e)

    def test_cli_modes(self):
        def run(*argv):
            buf = io.StringIO()
            with redirect_stdout(buf), redirect_stderr(io.StringIO()):
                code = hi.main(["--root", str(self.root), *argv])
            return code, buf.getvalue()

        code, out = run("--check")
        self.assertEqual(code, 1)
        self.assertIn("ERROR dangling", out)
        self.assertFalse((self.root / hi.INDEX_PATH).exists())          # --check never writes
        code, out = run("--json")
        self.assertEqual(json.loads(out)["counts"]["agent"], 4)
        code, out = run("--graph", "dot")
        self.assertEqual(code, 0)
        self.assertIn("digraph harness", out)
        run("--write")
        index = (self.root / hi.INDEX_PATH).read_text(encoding="utf-8")
        self.assertTrue(index.startswith(f"<!-- {hi.HEADER} -->"))
        self.assertIn("| skill:lonely | - | - | no-rubric |", index)
        before = (self.root / hi.JSON_PATH).read_text(encoding="utf-8")
        run("--write")
        self.assertEqual(before, (self.root / hi.JSON_PATH).read_text(encoding="utf-8"))   # deterministic


if __name__ == "__main__":
    unittest.main()
