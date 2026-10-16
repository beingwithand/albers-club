"""Tests for scripts/pipeline.py, the pipeline hooks (pipeline_gate, pipeline_router, watch_inbox),
pipelines/pipelines.yaml and scripts/install_watchers.py.

Run from the harness root:  python3 -I -m unittest discover -s tests -t .
"""
import datetime as dt
import importlib.util
import json
import os
import pathlib
import plistlib
import shutil
import subprocess
import sys
import tempfile
import time
import unittest

ROOT = pathlib.Path(__file__).resolve().parent.parent
SCRIPT = ROOT / "scripts" / "pipeline.py"
HOOKS = ROOT / "hooks"


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


P = load("pipeline_under_test", SCRIPT)
IW = load("install_watchers_under_test", ROOT / "scripts" / "install_watchers.py")


def iso(ts=None):
    return dt.datetime.fromtimestamp(ts if ts is not None else time.time(), dt.timezone.utc).isoformat()


class Base(unittest.TestCase):
    def setUp(self):
        self.tmp = pathlib.Path(tempfile.mkdtemp(prefix="harness-pipe-"))
        self.data = self.tmp / "data"
        (self.data / "log").mkdir(parents=True)
        self.proj = self.tmp / "work" / "translation" / "acme"
        for d in ("inbox", "knowledge/wiki", "deliverables", "work"):
            (self.proj / d).mkdir(parents=True)
        (self.proj / "PROGRESS.md").write_text("# Progress\n\n## Goal\nx\n\n## In progress\n\n## Next\n", encoding="utf-8")
        (self.proj / "knowledge" / "manifest.json").write_text('{"sources": []}', encoding="utf-8")
        self.env = {k: v for k, v in os.environ.items() if not k.startswith(("HARNESS_", "CLAUDE_"))}
        self.env["HARNESS_DATA"] = str(self.data)
        self.env["HARNESS_STATE"] = str(self.tmp / "nostate.json")
        self.cfg = P.load_config(self.env)

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def log(self, **ev):
        ev.setdefault("id", P.new_id("evt"))
        ev.setdefault("ts", iso())
        ev.setdefault("scope_hint", str(self.proj))
        with open(self.data / "log" / f"{dt.datetime.now(dt.timezone.utc):%Y-%m}.jsonl", "a", encoding="utf-8") as f:
            f.write(json.dumps(ev) + "\n")
        return ev["id"]

    def events(self, type_=None):
        out = []
        for f in sorted((self.data / "log").glob("*.jsonl")):
            for line in f.read_text(encoding="utf-8").splitlines():
                e = json.loads(line)
                if type_ is None or e.get("type") == type_:
                    out.append(e)
        return out

    def cli(self, *args, stdin=None):
        return subprocess.run([sys.executable, "-I", str(SCRIPT), *args], env=self.env, capture_output=True,
                              text=True, timeout=60, input=stdin)

    def hook(self, name, payload, *args):
        return subprocess.run([sys.executable, "-I", str(HOOKS / name), *args], input=json.dumps(payload)
                              if not isinstance(payload, str) else payload, env=self.env, capture_output=True,
                              text=True, timeout=60)


class ConfigTest(Base):
    def test_real_file_lints_clean(self):
        errors, warnings = P.lint(self.cfg)
        self.assertEqual(errors, [], errors)

    def test_subset_parser_agrees_with_pyyaml(self):
        try:
            import yaml
        except ImportError:
            self.skipTest("PyYAML not installed")
        text = (ROOT / "pipelines" / "pipelines.yaml").read_text(encoding="utf-8")
        self.assertEqual(P.yaml_load(text), yaml.safe_load(text))

    def test_required_pipelines_present(self):
        need = {"new-project", "intake", "translation", "synopsis", "email-draft", "job-application", "research",
                "code-change", "invoice", "annotation-batch", "session-end", "context-handoff", "new-component"}
        self.assertTrue(need <= set(self.cfg["pipelines"]), need - set(self.cfg["pipelines"]))

    def test_intake_order_and_code_review_and_changelog(self):
        ids = [s["id"] for s in self.cfg["pipelines"]["intake"]["steps"]]
        self.assertEqual(ids, ["register", "convert", "wiki", "index", "manifest", "verify", "archive"])
        code = [s["id"] for s in self.cfg["pipelines"]["code-change"]["steps"]]
        self.assertLess(code.index("implement"), code.index("step-review"))
        self.assertLess(code.index("back-review"), code.index("verify"))
        for pid in ("session-end", "code-change", "new-component"):
            st = {s["id"]: s for s in self.cfg["pipelines"][pid]["steps"]}
            self.assertTrue(st["changelog"]["required"], pid)
            self.assertIn("lib:changelog", st["changelog"]["evidence"])
        nc = [s["id"] for s in self.cfg["pipelines"]["new-component"]["steps"]]
        for s in ("frontmatter", "learning-contract", "rubric-eval", "pipeline-membership", "index", "eval-run"):
            self.assertIn(s, nc)

    def test_lint_catches_bad_config(self):
        bad = {"defaults": {}, "evidence_library": {}, "standalone": {}, "pending_components": {},
               "pipelines": {"x": {"triggers": {"strong": ["("]}, "client_bound": True, "steps": [
                   {"id": "a", "run": "skill:nope", "required": True, "after": ["b"], "evidence": [{"bogus": 1}],
                    "verification": "docs/VERIFICATION.md#no-such-heading"}]}}}
        errors, _ = P.lint(bad)
        text = "\n".join(errors)
        for frag in ("bad regex", "tier-V", "after 'b'", "does not exist", "needs one of", "anchor"):
            self.assertIn(frag, text)


class MatchTest(Base):
    def m(self, text):
        return P.match(text, self.cfg, self.env)

    def test_confident_matches(self):
        cases = {
            "translate this paragraph into English for my client": "translation",
            "번역해 주세요: 안녕하세요 고객님": "translation",
            "fix the bug in the lint function of kb.py": "code-change",
            "write a cover letter for this job posting at Acme": "job-application",
            "what's the latest stable release of Claude Code?": "research",
            "please make the invoice for October for Acme": "invoice",
            "condense this synopsis to 110 characters": "synopsis",
            "let's wrap up for today": "session-end",
        }
        for text, want in cases.items():
            self.assertEqual(self.m(text)["pipeline"], want, (text, self.m(text)))

    def test_trivial_and_unmatched_abstain(self):
        for text in ("hi", "ok thanks", "네", "tell me a joke about cats please"):
            r = self.m(text)
            self.assertTrue(r["abstain"], text)
            self.assertIsNone(r["pipeline"])

    def test_ambiguous_abstains(self):
        r = self.m("translate the job posting and write a cover letter")
        self.assertTrue(r["abstain"])
        self.assertIn("ambiguous", r["reason"])

    def test_slash_and_events(self):
        self.assertEqual(self.m("/harness:intake inbox/a.pdf")["pipeline"], "intake")
        self.assertEqual(self.m(json.dumps({"event": "inbox_file_detected"}))["pipeline"], "intake")
        self.assertEqual(self.m(json.dumps({"event": "context_threshold"}))["pipeline"], "context-handoff")
        r = self.m(json.dumps({"hook_event_name": "FileChanged", "file_path": str(self.proj / "inbox" / "a.pdf")}))
        self.assertEqual(r["pipeline"], "intake")
        r = self.m(json.dumps({"hook_event_name": "FileChanged", "file_path": str(ROOT / "skills" / "zz" / "SKILL.md")}))
        self.assertEqual(r["pipeline"], "new-component")

    def test_cli_match(self):
        r = self.cli("match", "translate this into Korean for the client")
        self.assertEqual(r.returncode, 0)
        self.assertEqual(json.loads(r.stdout)["pipeline"], "translation")


class RunTest(Base):
    def start(self, pid, **params):
        args = ["start", pid, "--scope", str(self.proj)] + [f"--param={k}={v}" for k, v in params.items()]
        r = self.cli(*args)
        self.assertEqual(r.returncode, 0, r.stderr)
        state = P.load_state(self.proj)
        return state["runs"][-1]

    def test_start_writes_state_block_and_event(self):
        run = self.start("translation")
        self.assertTrue((self.proj / ".harness" / "pipeline_state.json").is_file())
        prog = (self.proj / "PROGRESS.md").read_text(encoding="utf-8")
        self.assertIn(f"<!-- pipeline:{run['run_id']} -->", prog)
        self.assertNotIn("[x]", prog)
        self.assertNotIn("✅", prog)
        ev = self.events("pipeline_started")
        self.assertEqual(len(ev), 1)
        self.assertEqual(ev[0]["pipeline"], "translation")
        self.assertEqual(ev[0]["scope_hint"], str(self.proj))
        again = self.cli("start", "translation", "--scope", str(self.proj))
        self.assertIn("already active", again.stdout)
        self.assertEqual(len(P.load_state(self.proj)["runs"]), 1)

    def test_progress_block_does_not_satisfy_progress_updated(self):
        self.start("session-end")
        s = P.check(str(self.proj), env=self.env, cfg=self.cfg)[0]
        self.assertFalse(s["steps"]["park-step"]["ok"])
        with open(self.proj / "PROGRESS.md", "a", encoding="utf-8") as f:
            f.write("- parked: step 3 done, proof in log\n")
        s = P.check(str(self.proj), env=self.env, cfg=self.cfg)[0]
        self.assertTrue(s["steps"]["park-step"]["ok"])

    def test_check_finish_cycle(self):
        self.start("translation")
        r = self.cli("check", "--scope", str(self.proj))
        self.assertEqual(r.returncode, 1)
        self.assertIn("missing required", r.stdout)
        self.assertEqual(self.cli("finish", "--scope", str(self.proj)).returncode, 1)
        self.log(type="task", agent="translator")
        self.log(type="verification", verdict="pass", content="python3 -I scripts/translation_qa.py --source a", labels=["step_check"])
        self.log(type="verification", verdict="pass", labels=["lens:fidelity"])
        s = P.check(str(self.proj), env=self.env, cfg=self.cfg)[0]
        self.assertIn("verify", s["missing"])  # tier V needs 2 non-step_check passes
        self.log(type="verification", verdict="pass", labels=["lens:language"])
        s = P.check(str(self.proj), env=self.env, cfg=self.cfg)[0]
        self.assertEqual(s["missing"], [], s)
        r = self.cli("finish", "--scope", str(self.proj))
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        fin = self.events("pipeline_finished")
        self.assertEqual(fin[-1]["outcome"], "worked")
        self.assertEqual(P.load_state(self.proj)["runs"][0]["status"], "finished")

    def test_old_and_out_of_scope_events_do_not_count(self):
        self.log(type="task", agent="translator", ts=iso(time.time() - 3600))
        self.start("translation")
        self.log(type="task", agent="translator", scope_hint=str(self.tmp / "other"))
        s = P.check(str(self.proj), env=self.env, cfg=self.cfg)[0]
        self.assertFalse(s["steps"]["translate"]["ok"])

    def test_failed_verification_does_not_count(self):
        self.start("code-change")
        self.log(type="verification", verdict="fail")
        s = P.check(str(self.proj), env=self.env, cfg=self.cfg)[0]
        self.assertFalse(s["steps"]["verify"]["ok"])

    def test_mark_validates_evidence(self):
        self.start("code-change")
        bad = self.log(type="prompt", content="hello", scope_hint=str(self.tmp / "elsewhere"))
        r = self.cli("mark", "step-review", "--evidence", bad, "--scope", str(self.proj))
        self.assertEqual(r.returncode, 2)
        self.assertIn("does not match", r.stderr)
        self.assertEqual(self.cli("mark", "step-review", "--evidence", "evt_nope", "--scope", str(self.proj)).returncode, 2)
        good = self.log(type="task", agent="code-reviewer", scope="code/somewhere-else", scope_hint=str(self.tmp / "x"))
        s = P.check(str(self.proj), env=self.env, cfg=self.cfg)[0]
        self.assertFalse(s["steps"]["step-review"]["ok"])
        r = self.cli("mark", "step-review", "--evidence", good, "--scope", str(self.proj))
        self.assertEqual(r.returncode, 0, r.stderr)
        s = P.check(str(self.proj), env=self.env, cfg=self.cfg)[0]
        self.assertTrue(s["steps"]["step-review"]["ok"])
        self.assertTrue(self.events("pipeline_step"))

    def test_manual_step_accepts_any_recent_event(self):
        self.start("email-draft")
        ok = self.log(type="prompt", content="looks good, I'll send it", scope_hint=str(self.tmp / "x"))
        r = self.cli("mark", "user-ok", "--evidence", ok, "--scope", str(self.proj))
        self.assertEqual(r.returncode, 0, r.stderr)

    def test_intake_json_select_and_strict_order(self):
        f = self.proj / "inbox" / "brief.pdf"
        f.write_bytes(b"%PDF-1.4 x")
        run = self.start("intake", file=str(f))
        s = P.check(str(self.proj), env=self.env, cfg=self.cfg)[0]
        self.assertEqual(s["missing"][0], "register")
        self.assertEqual(s["next"]["step"], "register")
        man = {"sources": [{"original_name": "other.pdf", "sha256": "ab" * 32, "converter": "x", "archive": "u",
                            "pages_produced": ["p"]}]}
        (self.proj / "knowledge" / "manifest.json").write_text(json.dumps(man), encoding="utf-8")
        s = P.check(str(self.proj), env=self.env, cfg=self.cfg)[0]
        self.assertFalse(s["steps"]["register"]["ok"], "select must restrict to this file")
        man["sources"].append({"original_name": "brief.pdf", "sha256": "cd" * 32, "converter": None, "archive": None,
                               "pages_produced": []})
        (self.proj / "knowledge" / "manifest.json").write_text(json.dumps(man), encoding="utf-8")
        s = P.check(str(self.proj), env=self.env, cfg=self.cfg)[0]
        self.assertTrue(s["steps"]["register"]["ok"])
        self.assertFalse(s["steps"]["convert"]["ok"])
        self.assertEqual(s["next"]["step"], "convert")
        # archive recorded before verify: an order violation, which fails a strict pipeline
        man["sources"][1].update(converter="kordoc@4", archive="https://drive/x", pages_produced=["wiki/a.md"])
        (self.proj / "knowledge" / "manifest.json").write_text(json.dumps(man), encoding="utf-8")
        s = P.check(str(self.proj), env=self.env, cfg=self.cfg)[0]
        self.assertTrue(any("archive" in v and "verify" in v for v in s["order_violations"]), s["order_violations"])
        self.assertFalse(s["ok"])
        self.assertEqual(run["params"]["file"], str(f))

    def test_abandon_needs_reason_and_logs(self):
        run = self.start("invoice")
        r = self.cli("abandon", "--run", run["run_id"], "--reason", " ", "--scope", str(self.proj))
        self.assertEqual(r.returncode, 2)
        r = self.cli("abandon", "--run", run["run_id"], "--reason", "user: not billing this month", "--scope", str(self.proj))
        self.assertEqual(r.returncode, 0)
        self.assertEqual(self.events("pipeline_finished")[-1]["outcome"], "abandoned")
        self.assertEqual(P.check(str(self.proj), env=self.env, cfg=self.cfg), [])

    def test_unknown_pipeline_and_param(self):
        self.assertEqual(self.cli("start", "nope", "--scope", str(self.proj)).returncode, 2)
        self.assertEqual(self.cli("start", "translation", "--scope", str(self.proj), "--param", "x=1").returncode, 2)


class QueueTest(Base):
    def test_scan_dedupes_and_skips_registered(self):
        (self.proj / "inbox" / "a.pdf").write_bytes(b"a")
        (self.proj / "inbox" / "b.docx").write_bytes(b"b")
        (self.proj / "inbox" / ".gitkeep").write_text("")
        r = self.cli("queue", "scan", str(self.proj), "--source", "launchd")
        self.assertIn("2 new", r.stdout)
        self.assertIn("0 new", self.cli("queue", "scan", str(self.proj)).stdout)
        self.assertEqual(len(self.events("inbox_file_detected")), 2)
        (self.proj / "knowledge" / "manifest.json").write_text(json.dumps({"sources": [{"original_name": "a.pdf"}]}))
        pend = P.pending_queue(self.env, self.proj)
        self.assertEqual([pathlib.Path(q["path"]).name for q in pend], ["b.docx"])
        self.cli("queue", "ack", pend[0]["id"])
        self.assertEqual(P.pending_queue(self.env, self.proj), [])

    def test_start_intake_acks_queue_entry(self):
        f = self.proj / "inbox" / "c.pdf"
        f.write_bytes(b"c")
        P.scan_inbox(self.proj, self.env)
        self.assertEqual(len(P.pending_queue(self.env, self.proj)), 1)
        P.start("intake", str(self.proj), {"file": str(f)}, self.env, cfg=self.cfg)
        self.assertEqual(P.pending_queue(self.env, self.proj), [])


class GateHookTest(Base):
    def payload(self, **kw):
        return dict({"session_id": "s1", "cwd": str(self.proj), "stop_hook_active": False, "hook_event_name": "Stop"}, **kw)

    def test_no_state_allows(self):
        r = self.hook("pipeline_gate.py", self.payload())
        self.assertEqual((r.returncode, r.stdout), (0, ""))

    def test_blocks_with_missing_and_next(self):
        P.start("code-change", str(self.proj), {}, self.env, cfg=self.cfg)
        r = self.hook("pipeline_gate.py", self.payload())
        out = json.loads(r.stdout)
        self.assertEqual(out["decision"], "block")
        for frag in ("implement", "step-review", "back-review", "verify", "changelog", "Next: **implement**",
                     "agent:coder", "HARNESS_PIPELINE_GATE=0"):
            self.assertIn(frag, out["reason"])

    def test_loop_guard_subagent_off_switch_garbage(self):
        P.start("code-change", str(self.proj), {}, self.env, cfg=self.cfg)
        self.assertEqual(self.hook("pipeline_gate.py", self.payload(stop_hook_active=True)).stdout, "")
        self.assertEqual(self.hook("pipeline_gate.py", self.payload(agent_id="abc")).stdout, "")
        self.env["HARNESS_PIPELINE_GATE"] = "0"
        self.assertEqual(self.hook("pipeline_gate.py", self.payload()).stdout, "")
        del self.env["HARNESS_PIPELINE_GATE"]
        r = self.hook("pipeline_gate.py", "{not json")
        self.assertEqual((r.returncode, r.stdout), (0, ""))

    def test_complete_and_stale_runs_allow(self):
        P.start("context-handoff", str(self.proj), {}, self.env, cfg=self.cfg)
        with open(self.proj / "PROGRESS.md", "a", encoding="utf-8") as f:
            f.write("\nparked\n")
        self.log(type="handoff")
        self.assertEqual(self.hook("pipeline_gate.py", self.payload()).stdout, "")
        state = P.load_state(self.proj)
        state["runs"].append(dict(state["runs"][0], run_id="pr_old", pipeline="invoice",
                                  started_ts=time.time() - 30 * 86400, marks={}))
        P.save_state(self.proj, state)
        self.assertEqual(self.hook("pipeline_gate.py", self.payload()).stdout, "")


class RouterHookTest(Base):
    def payload(self, prompt, **kw):
        return dict({"session_id": "s1", "cwd": str(self.proj), "prompt": prompt, "hook_event_name": "UserPromptSubmit"}, **kw)

    def ctx(self, r):
        self.assertEqual(r.returncode, 0)
        return json.loads(r.stdout)["hookSpecificOutput"]["additionalContext"] if r.stdout else ""

    def test_suggests_pipeline_without_starting(self):
        c = self.ctx(self.hook("pipeline_router.py", self.payload("translate this letter into English for the client")))
        self.assertIn("This looks like `translation`", c)
        self.assertIn("run these steps in order", c)
        self.assertIn("pipeline.py start translation", c)
        self.assertFalse(P.state_file(self.proj).exists())

    def test_quiet_on_trivial_and_unmatched(self):
        self.assertEqual(self.hook("pipeline_router.py", self.payload("ok")).stdout, "")
        self.assertEqual(self.hook("pipeline_router.py", self.payload("tell me a joke about cats please")).stdout, "")

    def test_active_run_line_and_queue_once(self):
        P.start("invoice", str(self.proj), {}, self.env, cfg=self.cfg)
        (self.proj / "inbox" / "new.pdf").write_bytes(b"x")
        P.scan_inbox(self.proj, self.env)
        c = self.ctx(self.hook("pipeline_router.py", self.payload("translate this letter into English please")))
        self.assertIn("Active runs", c)
        self.assertIn("next **count**", c)
        self.assertIn("run /intake", c)
        c2 = self.ctx(self.hook("pipeline_router.py", self.payload("and another thing to translate please")))
        self.assertNotIn("run /intake", c2)

    def test_context_threshold_autostarts_handoff(self):
        state = {"sessions": {"s1": {"ctx_tokens": 210000, "ts": time.time()}}}
        pathlib.Path(self.env["HARNESS_STATE"]).write_text(json.dumps(state), encoding="utf-8")
        U = load("ug_for_test", HOOKS / "usage_guard.py")
        if U.session_ctx(state, "s1", time.time(), 600) is None:
            self.skipTest("usage state shape differs; covered by test_usage_and_compaction")
        c = self.ctx(self.hook("pipeline_router.py", self.payload("continue with the next part of the task")))
        self.assertIn("context-handoff", c)
        self.assertEqual(P.load_state(self.proj)["runs"][0]["pipeline"], "context-handoff")

    def test_off_switch(self):
        self.env["HARNESS_PIPELINE_ROUTER"] = "0"
        self.assertEqual(self.hook("pipeline_router.py", self.payload("translate this letter into English")).stdout, "")


class WatchHookTest(Base):
    def make_harness(self):
        h = self.tmp / "harness"
        (h / ".claude-plugin").mkdir(parents=True)
        (h / ".claude-plugin" / "plugin.json").write_text('{"name": "harness"}')
        for d in ("skills/old", "agents", "hooks", "scripts", "docs", "learning"):
            (h / d).mkdir(parents=True, exist_ok=True)
        (h / "skills" / "old" / "SKILL.md").write_text("---\nname: old\ndescription: d\n---\n")
        (h / "docs" / "components.json").write_text(json.dumps({"nodes": [{"id": "skill:old", "path": "skills/old/SKILL.md"}]}))
        (h / ".git").mkdir()
        return h

    def test_session_start_watch_paths_scan_and_autostart(self):
        (self.proj / "inbox" / "brief.hwpx").write_bytes(b"x")
        r = self.hook("watch_inbox.py", {"hook_event_name": "SessionStart", "source": "startup", "cwd": str(self.proj)},
                      "session_start")
        out = json.loads(r.stdout)["hookSpecificOutput"]
        self.assertIn(str(self.proj / "inbox"), out["watchPaths"])
        self.assertIn("brief.hwpx", out["additionalContext"])
        runs = P.load_state(self.proj)["runs"]
        self.assertEqual([r_["pipeline"] for r_ in runs], ["intake"])
        self.assertEqual(len(self.events("inbox_file_detected")), 1)

    def test_session_start_in_harness_watches_component_dirs(self):
        h = self.make_harness()
        r = self.hook("watch_inbox.py", {"hook_event_name": "SessionStart", "cwd": str(h)})
        out = json.loads(r.stdout)["hookSpecificOutput"]
        self.assertIn(str(h / "skills"), out["watchPaths"])
        self.assertIn(str(h / "agents"), out["watchPaths"])

    def test_file_changed_inbox(self):
        f = self.proj / "inbox" / "spec.pdf"
        f.write_bytes(b"x")
        r = self.hook("watch_inbox.py", {"hook_event_name": "FileChanged", "file_path": str(f), "event": "add",
                                         "cwd": str(self.proj)})
        out = json.loads(r.stdout)
        self.assertIn(f"new document: run /intake {f}", out["hookSpecificOutput"]["additionalContext"])
        self.assertEqual(P.load_state(self.proj)["runs"][0]["params"]["file"], str(f))
        self.assertEqual(len(self.events("inbox_file_detected")), 1)

    def test_file_changed_alternate_field_names_and_unlink(self):
        f = self.proj / "inbox" / "alt.pdf"
        f.write_bytes(b"x")
        r = self.hook("watch_inbox.py", {"paths": [str(f)], "change_type": "unlink"}, "file_changed")
        self.assertEqual(r.stdout, "")
        r = self.hook("watch_inbox.py", {"filePath": str(f), "changeType": "change"}, "file_changed")
        self.assertIn("alt.pdf", r.stdout)

    def test_autostart_off_still_queues(self):
        self.env["HARNESS_PIPELINE_AUTOSTART"] = "0"
        f = self.proj / "inbox" / "q.pdf"
        f.write_bytes(b"x")
        self.hook("watch_inbox.py", {"hook_event_name": "FileChanged", "file_path": str(f)})
        self.assertFalse(P.state_file(self.proj).exists())
        self.assertEqual(len(P.pending_queue(self.env, self.proj)), 1)

    def test_new_and_changed_component(self):
        h = self.make_harness()
        new = h / "skills" / "fresh" / "SKILL.md"
        new.parent.mkdir()
        new.write_text("---\nname: fresh\ndescription: does x\n---\n")
        r = self.hook("watch_inbox.py", {"hook_event_name": "FileChanged", "file_path": str(new)})
        self.assertIn("/integrate skills/fresh/SKILL.md", r.stdout)
        run = P.load_state(h)["runs"][0]
        self.assertEqual((run["pipeline"], run["params"]), ("new-component", {"component": "skills/fresh/SKILL.md"}))
        self.assertEqual(self.events("component_detected")[0]["change"], "new")
        old = h / "skills" / "old" / "SKILL.md"
        r = self.hook("watch_inbox.py", {"hook_event_name": "FileChanged", "file_path": str(old)})
        self.assertIn("self-eval --changed skills/old/SKILL.md", r.stdout)
        self.assertEqual(len(P.load_state(h)["runs"]), 1, "changed components never autostart")
        r = self.hook("watch_inbox.py", {"hook_event_name": "FileChanged", "file_path": str(old)})
        self.assertEqual(r.stdout, "", "a burst of edits queues once")

    def test_builtins_on_fake_harness(self):
        h = self.make_harness()
        (h / "agents" / "nm.md").write_text("---\nname: nm\ndescription: d\n---\n")
        run = {"run_id": "r", "pipeline": "new-component", "started_ts": time.time() - 5, "params": {"component": "agents/nm.md"}}
        ctx = P.Ctx(h, run, self.cfg, self.env)
        ok, detail = P.run_builtin("component_frontmatter", ctx)
        self.assertFalse(ok)
        self.assertIn("model", detail)
        (h / "agents" / "nm.md").write_text("---\nname: nm\ndescription: d\nmodel: sonnet\n---\n")
        self.assertTrue(P.run_builtin("component_frontmatter", ctx)[0])
        (h / "learning" / "contracts.yaml").write_text('version: 0.1.0\ncontracts:\n  "agent:other":\n    status: draft\n')
        self.assertFalse(P.run_builtin("learning_contract", ctx)[0])
        (h / "learning" / "contracts.yaml").write_text('version: 0.1.0\ncontracts:\n  "agent:nm":\n    status: draft\n')
        self.assertTrue(P.run_builtin("learning_contract", ctx)[0])
        self.assertFalse(P.run_builtin("rubric_eval", ctx)[0])
        self.assertFalse(P.run_builtin("pipeline_membership", ctx)[0])
        self.assertFalse(P.run_builtin("index_fresh", ctx)[0])
        (h / "docs" / "components.json").write_text(json.dumps({
            "nodes": [{"id": "agent:nm", "path": "agents/nm.md"}],
            "coverage": {"rows": [{"id": "agent:nm", "status": "exempt"}]}}))
        self.assertTrue(P.run_builtin("index_fresh", ctx)[0])
        self.assertTrue(P.run_builtin("rubric_eval", ctx)[0])
        (h / "hooks" / "h.py").write_text('"""doc"""\n')
        ctx.params["component"] = "hooks/h.py"
        self.assertFalse(P.run_builtin("component_frontmatter", ctx)[0], "unregistered hook")


class InstallWatchersTest(Base):
    def test_find_and_render(self):
        roots = [self.tmp / "work"]
        found = IW.find_projects(roots)
        self.assertEqual(found, [self.proj.resolve()])
        label = "com.harness.inbox-watch." + IW.slug(self.proj, roots)
        self.assertEqual(label, "com.harness.inbox-watch.translation-acme")
        text = IW.render(self.proj.resolve(), label, self.env)
        self.assertNotIn("__", text)
        pl = plistlib.loads(text.encode("utf-8"))
        self.assertEqual(pl["Label"], label)
        self.assertEqual(pl["WatchPaths"], [str(self.proj.resolve() / "inbox")])
        self.assertIn("queue scan", pl["ProgramArguments"][-1])
        self.assertNotIn("claude ", pl["ProgramArguments"][-1])

    def test_install_dry_run(self):
        r = subprocess.run([sys.executable, "-I", str(ROOT / "scripts" / "install_watchers.py"), "install", "--dry-run",
                            "--root", str(self.tmp / "work")], env=self.env, capture_output=True, text=True, timeout=30)
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn("would write", r.stdout)
        self.assertIn("bootstrap", r.stdout)


class HooksJsonTest(unittest.TestCase):
    def test_registered_and_existing_kept(self):
        d = json.loads((ROOT / "hooks" / "hooks.json").read_text(encoding="utf-8"))["hooks"]
        cmds = json.dumps(d)
        for f in ("log_event.py", "usage_guard.py", "guard_protected.py", "step_check.py", "verify_gate.py",
                  "precompact_snapshot.py", "postcompact_reinject.py", "pipeline_gate.py", "pipeline_router.py",
                  "watch_inbox.py"):
            self.assertIn(f, cmds)
        self.assertIn("watch_inbox.py", json.dumps(d["FileChanged"]))
        self.assertIn("pipeline_gate.py", json.dumps(d["Stop"]))


if __name__ == "__main__":
    unittest.main()
