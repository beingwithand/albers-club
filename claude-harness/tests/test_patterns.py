"""Tests for scripts/patterns.py (multi-layer pattern system). Stdlib only. Run from the harness root:
    python3 -I -m unittest tests.test_patterns
"""
import contextlib
import importlib.util
import io
import json
import pathlib
import shutil
import sys
import tempfile
import unittest

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.dont_write_bytecode = True


def load(name):
    spec = importlib.util.spec_from_file_location(name, ROOT / "scripts" / f"{name}.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


pt = load("patterns")
sc = load("schema_check")

_n = [0]


def ev(ts, type_="prompt", session="s1", **kw):
    _n[0] += 1
    day = ts[:10].replace("-", "")
    rec = {"id": f"evt_{day}_100000_{_n[0]:04x}", "ts": ts + ("" if "T" in ts else "T10:00:00+00:00"),
           "actor": "me", "type": type_, "session_id": session}
    rec.update(kw)
    return rec


def label(target, ts, **kw):
    rec = ev(ts, "label", actor="agent:librarian", labels_for=target["id"], parent_event=target["id"])
    rec.update(kw)
    return rec


class Base(unittest.TestCase):
    TODAY = "2026-10-16"

    def setUp(self):
        self.tmp = pathlib.Path(tempfile.mkdtemp(prefix="patterns-test-"))
        self.principles = self.tmp / "PRINCIPLES.md"
        self.principles.write_text("# P\n\n1. **Keep it short.** Write short summaries for every report.\n", encoding="utf-8")

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def log(self, events, month="2026-10"):
        p = self.tmp / "log" / f"{month}.jsonl"
        p.parent.mkdir(parents=True, exist_ok=True)
        with open(p, "a", encoding="utf-8") as f:
            for e in events:
                f.write(json.dumps(e, ensure_ascii=False) + "\n")

    def store(self, name, recs):
        p = self.tmp / "patterns" / name
        p.parent.mkdir(parents=True, exist_ok=True)
        with open(p, "a", encoding="utf-8") as f:
            for r in recs:
                f.write(json.dumps(r, ensure_ascii=False) + "\n")

    def args(self, *extra, seeds=False):
        a = ["--data-dir", str(self.tmp), "--today", self.TODAY, "--principles", str(self.principles)]
        return a + ([] if seeds else ["--no-seeds"]) + list(extra)

    def run_cmd(self, cmd, *extra, seeds=False):
        out, err = io.StringIO(), io.StringIO()
        with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
            code = pt.main([cmd] + self.args(*extra, seeds=seeds))
        return code, out.getvalue(), err.getvalue()

    def json_cmd(self, cmd, *extra, seeds=False):
        code, out, err = self.run_cmd(cmd, "--json", *extra, seeds=seeds)
        self.assertEqual(code, 0, err)
        return json.loads(out)

    def correction(self, ts, session, scope, kot, labels=("register",)):
        e = ev(ts, "prompt", session, scope=scope, content="no, not like that")
        return [e, label(e, ts, is_correction=True, intent="fix the register",
                         meta={"kind_of_thing": kot}, labels=list(labels))]


class TokensTest(unittest.TestCase):
    def test_english_stopwords_and_korean_bigrams(self):
        t = pt.tokens("Please check the sources online 계약서를 확인해줘")
        self.assertIn("check", t)
        self.assertIn("online", t)
        self.assertNotIn("the", t)
        self.assertNotIn("please", t)
        for bg in ("계약", "약서", "확인"):
            self.assertIn(bg, t)
        self.assertNotIn("서를", t)  # particle stripped
        self.assertGreater(pt.dice(pt.tokens("온라인으로 확인해줘"), pt.tokens("온라인 확인 부탁")), 0.5)


class MineTest(Base):
    def test_corrections_cluster_across_sessions_and_areas(self):
        evs = []
        evs += self.correction("2026-10-01", "s1", "translation/acme", "register too casual")
        evs += self.correction("2026-10-05", "s2", "translation/acme", "register too casual")
        evs += self.correction("2026-10-09", "s3", "annotation/plat", "register too casual")
        evs.append(ev("2026-10-10", "prompt", "s4", content="translate this"))
        self.log(evs)
        res = self.json_cmd("mine")
        corr = [c for c in res["candidates"] if c["kind"] == "correction"]
        self.assertEqual(len(corr), 1)
        c = corr[0]
        self.assertEqual(c["support"], 3)
        self.assertEqual(c["sessions"], 3)
        self.assertEqual(c["areas"], ["annotation", "translation"])
        self.assertEqual(c["status"], "candidate")
        self.assertIn("register too casual", c["statement"])
        self.assertTrue(all(e.startswith("evt_") for e in c["evidence"]))
        self.assertEqual(c["sources"], ["label"])
        # cross-area structure -> a domain-analogy candidate too
        self.assertTrue(any(x["kind"] == "domain-analogy" for x in res["candidates"]))
        # the record validates against the ontology
        rep = sc.Report()
        sc.validate_records("Pattern", [("c", c)], sc.Ontology.load(), rep)
        self.assertEqual(rep.errors, [])

    def test_singletons_are_not_candidates(self):
        self.log(self.correction("2026-10-01", "s1", "code/x", "deleted wrong file"))
        res = self.json_cmd("mine")
        self.assertEqual([c for c in res["candidates"] if c["kind"] == "correction"], [])

    def test_korean_requests_cluster(self):
        self.log([ev("2026-10-02", "prompt", "a", content="이거 온라인으로 확인해줘 출처도"),
                  ev("2026-10-06", "prompt", "b", content="온라인 확인 부탁 출처 포함"),
                  ev("2026-10-07", "prompt", "c", content="draw a cat")])
        res = self.json_cmd("mine")
        req = [c for c in res["candidates"] if c["kind"] == "request"]
        self.assertEqual(len(req), 1)
        self.assertEqual(req[0]["support"], 2)
        self.assertIn("확인", req[0]["signals"]["keywords"])

    def test_dedupe_against_existing_reports_new_evidence(self):
        evs = []
        for i, d in enumerate(("2026-10-01", "2026-10-03")):
            evs += self.correction(d, f"s{i}", "translation/acme", "register too casual")
        self.log(evs)
        first = self.json_cmd("mine")["candidates"][0]
        old = dict(first, status="approved", evidence=first["evidence"][:1], support=1)
        self.store("patterns.jsonl", [old])
        res = self.json_cmd("mine")
        self.assertFalse(any(c["kind"] == "correction" for c in res["candidates"]))
        upd = [u for u in res["updates"] if u["id"] == old["id"]]
        self.assertEqual(len(upd), 1)
        self.assertEqual(len(upd[0]["new_evidence"]), 1)

    def test_workflow_and_temporal(self):
        evs = []
        for s, d in (("w1", "2026-09-28"), ("w2", "2026-10-05"), ("w3", "2026-10-12")):  # Mondays
            evs.append(ev(d, "prompt", s, content="/intake the pdf"))
            evs.append(ev(d + "T11:00:00+00:00", "prompt", s, content="/verify it"))
        self.log(evs[:2], "2026-09")
        self.log(evs[2:])
        res = self.json_cmd("mine")
        ids = {c["id"]: c for c in res["candidates"]}
        self.assertIn("pat_workflow_intake-then-verify", ids)
        self.assertEqual(ids["pat_workflow_intake-then-verify"]["sessions"], 3)
        self.assertIn("pat_temporal_intake-mon", ids)
        self.assertFalse(any(i.startswith("pat_temporal_session-start") for i in ids))  # needs 4+ sessions

    def test_project_mishaps_external_and_auto_memory(self):
        proj = self.tmp / "work" / "code" / "harness"
        (proj / "log").mkdir(parents=True)
        (proj / "log" / "mishaps.md").write_text(
            "## 2026-10-02 10:00 saved notes in unrelated repo\n- **Root cause:** wrong cwd for research notes\n"
            "## 2026-10-08 09:00 saved research notes in unrelated repo\n- **Root cause:** wrong cwd for research notes\n",
            encoding="utf-8")
        ext = self.tmp / "insights.jsonl"
        ext.write_text("\n".join(json.dumps(x) for x in [
            {"source": "insights", "text": "permission prompts blocked bash repeatedly", "ts": "2026-10-03"},
            {"source": "insights", "text": "bash permission denied in sandbox", "ts": "2026-10-09"}]), encoding="utf-8")
        mem = self.tmp / "memory"
        mem.mkdir()
        for i in (1, 2):
            (mem / f"fb{i}.md").write_text(f"---\nname: fb{i}\ndescription: user prefers formal register in emails\n"
                                           "type: feedback\n---\nprefer formal register for client email\n", encoding="utf-8")
        (mem / "MEMORY.md").write_text("- index\n", encoding="utf-8")
        res = self.json_cmd("mine", "--project", str(proj), "--external", str(ext), "--auto-memory", str(mem))
        kinds = {c["kind"]: c for c in res["candidates"]}
        self.assertEqual(kinds["mistake"]["areas"], ["code"])
        self.assertTrue(kinds["mistake"]["evidence"][0].startswith("mishap:harness#"))
        self.assertEqual(kinds["tool-friction"]["sources"], ["insights"])
        self.assertEqual(kinds["tool-friction"]["origin"], "insights")
        self.assertEqual(kinds["preference"]["sources"], ["auto-memory"])


class LadderTest(Base):
    def pattern(self, **kw):
        rec = {"id": "pat_preference_formal", "ts": "2026-10-01T00:00:00+00:00", "pattern_level": "L2",
               "kind": "preference", "statement": "Recurring preference: formal register", "status": "candidate",
               "evidence": [], "signals": {"keywords": ["formal", "register"]}}
        rec.update(kw)
        return rec

    def seed_events(self, n, start_day=1, scope="translation/acme"):
        evs = [ev(f"2026-10-{start_day + i:02d}", "decision", f"s{i}", scope=scope, intent="formal register",
                  situation="client mail", meta={"kind_of_thing": "formal register"}) for i in range(n)]
        self.log(evs)
        return [e["id"] for e in evs]

    def actions(self, **kw):
        return {(p["action"], p["id"]): p for p in self.json_cmd("ladder", **kw)}

    def test_propose_only_when_thresholds_met(self):
        ids = self.seed_events(2)
        self.store("patterns.jsonl", [self.pattern(evidence=ids)])
        self.assertNotIn(("propose", "pat_preference_formal"), self.actions())
        self.seed_events(1, start_day=10)  # third episode, picked up via mining/dedupe
        acts = self.actions()
        p = acts[("propose", "pat_preference_formal")]
        self.assertEqual(p["record"]["status"], "proposed")
        self.assertEqual(p["record"]["support"], 3)
        self.assertIn("approval", p["needs"])
        # thresholds are configurable
        (self.tmp / "patterns" / "config.json").write_text(json.dumps({"propose": {"support": 5}}), encoding="utf-8")
        self.assertNotIn(("propose", "pat_preference_formal"), self.actions())

    def test_ladder_never_writes(self):
        ids = self.seed_events(3)
        self.store("patterns.jsonl", [self.pattern(evidence=ids)])
        before = {p: p.read_bytes() for p in self.tmp.rglob("*") if p.is_file()}
        for cmd in ("mine", "ladder", "meta", "report"):
            self.run_cmd(cmd)
        after = {p: p.read_bytes() for p in self.tmp.rglob("*") if p.is_file()}
        self.assertEqual(before, after)

    def test_encoding_proposal_with_and_without_eval_gate(self):
        ids = self.seed_events(4)
        self.store("patterns.jsonl", [self.pattern(evidence=ids, status="approved")])
        p = self.actions()[("propose-encoding", "enc_preference_formal")]
        self.assertEqual(p["layer"], "L3")
        self.assertIn("ungated", p["needs"])
        self.assertEqual(p["record"]["encodes"], ["pat_preference_formal"])
        self.assertEqual(p["pattern"], "pat_preference_formal")
        t = self.tmp / "evals" / "translation" / "tasks"
        t.mkdir(parents=True)
        (t / "translation-001.yaml").write_text("id: translation-001\n", encoding="utf-8")
        p = self.actions()[("propose-encoding", "enc_preference_formal")]
        self.assertIn("eval-gate:evals/translation", p["needs"])
        self.assertEqual(p["record"]["gate"], "pending")

    def test_decay_and_retire(self):
        self.TODAY = "2026-12-31"
        self.store("patterns.jsonl", [
            self.pattern(id="pat_preference_old", status="approved", last_seen="2026-10-01T00:00:00+00:00",
                         evidence=["x:1", "x:2"]),
            self.pattern(id="pat_preference_dying", status="decaying", ts="2026-11-01T00:00:00+00:00",
                         last_seen="2026-09-01T00:00:00+00:00", evidence=["x:3", "x:4"]),
            self.pattern(id="pat_mistake_quiet", kind="mistake", status="encoded", statement="Recurring mistake: quiet",
                         last_seen="2026-09-01T00:00:00+00:00", evidence=["x:5", "x:6"]),
        ])
        self.store("encodings.jsonl", [{"id": "enc_hook_quiet", "ts": "2026-09-02T00:00:00+00:00", "pattern_level": "L3",
                                        "kind": "hook", "target": "hooks/x.py", "encodes": ["pat_mistake_quiet"],
                                        "status": "encoded"}])
        acts = self.actions()
        self.assertEqual(acts[("decay", "pat_preference_old")]["to"], "decaying")
        self.assertEqual(acts[("retire", "pat_preference_dying")]["to"], "retired")
        self.assertFalse(any(i == "pat_mistake_quiet" for _, i in acts))  # silence after encoding = working

    def test_reopen_after_reoccurrence_and_meta_signal(self):
        evs = []
        for i, d in enumerate(("2026-10-01", "2026-10-02", "2026-10-10", "2026-10-12")):
            evs += self.correction(d, f"s{i}", "code/h", "wrong repo for notes", labels=("storage",))
        self.log(evs)
        cand = self.json_cmd("mine")["candidates"][0]
        early = [e for e in cand["evidence"]][:2]
        self.store("patterns.jsonl", [dict(cand, status="encoded", evidence=early, support=2)])
        self.store("encodings.jsonl", [{"id": "enc_rule_repo", "ts": "2026-10-05T00:00:00+00:00", "pattern_level": "L3",
                                        "kind": "rule", "target": "global/CLAUDE.md", "encodes": [cand["id"]],
                                        "status": "encoded"}])
        acts = self.actions()
        r = acts[("reopen", cand["id"])]
        self.assertEqual(r["to"], "reopened")
        self.assertEqual(len(r["evidence_after"]), 2)
        sig = {m["signal"] for m in self.json_cmd("meta")}
        self.assertIn("reoccurrence-after-encoding", sig)

    def test_overrides_reopen_encoding(self):
        self.store("patterns.jsonl", [self.pattern(status="encoded", evidence=["x:1", "x:2"],
                                                   last_seen="2026-10-10T00:00:00+00:00")])
        self.store("encodings.jsonl", [{"id": "enc_rule_formal", "ts": "2026-10-01T00:00:00+00:00", "pattern_level": "L3",
                                        "kind": "rule", "target": ".claude/rules/register.md",
                                        "encodes": ["pat_preference_formal"], "status": "encoded"}])
        p1 = ev("2026-10-11", "prompt", "a", content="no, casual is fine here")
        p2 = ev("2026-10-12", "prompt", "b", content="casual again")
        self.log([p1, p2, label(p1, "2026-10-13", labels=["override:enc_rule_formal"]),
                  label(p2, "2026-10-13", labels=["override:enc_rule_formal"])])
        acts = self.actions()
        self.assertEqual(acts[("review-encoding", "enc_rule_formal")]["record"]["overrides"], 2)
        self.assertIn("encoding-overridden", {m["signal"] for m in self.json_cmd("meta")})

    def test_unused_skill_encoding_decays(self):
        self.TODAY = "2026-12-31"
        self.store("encodings.jsonl", [{"id": "enc_skill_x", "ts": "2026-09-01T00:00:00+00:00", "pattern_level": "L3",
                                        "kind": "skill", "target": "skills/x/SKILL.md", "encodes": ["pat_request_x"],
                                        "status": "encoded"}])
        self.log([ev("2026-12-30", "prompt", "z", content="/x go")], "2026-12")
        self.assertNotIn(("decay-encoding", "enc_skill_x"), self.actions())
        self.TODAY = "2027-03-31"
        self.assertIn(("decay-encoding", "enc_skill_x"), self.actions())

    def test_principle_proposal_and_review(self):
        self.principles.write_text("1. **Check sources.** Verify claims. (pat_request_a)\n", encoding="utf-8")
        self.store("patterns.jsonl", [
            self.pattern(id="pat_request_a", kind="request", status="retired", areas=["research"], evidence=["x:1", "x:2"]),
            self.pattern(id="pat_mistake_b", kind="mistake", status="approved", areas=["translation"],
                         statement="Recurring mistake: numbers not verified", evidence=["x:3", "x:4"],
                         signals={"keywords": ["verify", "numbers"]}),
            self.pattern(id="pat_mistake_c", kind="mistake", status="encoded", areas=["code"],
                         statement="Recurring mistake: test numbers not verified", evidence=["x:5", "x:6"],
                         signals={"keywords": ["verify", "numbers", "tests"]}),
        ])
        acts = self.actions()
        self.assertIn(("review-principle", "P1"), acts)
        pp = acts[("propose-principle", "P<new>")]
        self.assertEqual(sorted(pp["patterns"]), ["pat_mistake_b", "pat_mistake_c"])


class MetaTest(Base):
    def test_hotspot_blindspot_drift_conflict_labelgap_unused(self):
        evs = []
        for i in range(4):
            e = ev(f"2026-10-0{i + 1}", "prompt", f"t{i}", scope="translation/acme", content="fix it")
            kot = ["numbers wrong", "tone off", "glossary missed", "layout broken"][i]
            evs += [e, label(e, f"2026-10-0{i + 1}", is_correction=True, meta={"kind_of_thing": kot},
                             labels=[["alpha", "beta", "gamma", "delta"][i]])]
        e1 = ev("2026-09-20", "decision", "d1", scope="code/h", intent="formal tone in emails", situation="x", meta={})
        e2 = ev("2026-10-10", "decision", "d2", scope="code/h", intent="casual tone in emails", situation="x", meta={})
        evs += [e1, e2]
        evs += [ev(f"2026-10-1{i}", "prompt", f"u{i}", content=f"thing {i}") for i in range(6)]
        self.log(evs)
        self.principles.write_text("1. **Keep reports short.** Short summaries for every client report.\n"
                                   "2. **Be thorough.** Long detailed client report sections always.\n", encoding="utf-8")
        ext = self.tmp / "doctor.jsonl"
        ext.write_text(json.dumps({"source": "skill-doctor", "skill": "x", "invocations": 0, "context_tokens": 900}),
                       encoding="utf-8")
        self.store("encodings.jsonl", [{"id": "enc_skill_x", "ts": "2026-10-01T00:00:00+00:00", "pattern_level": "L3",
                                        "kind": "skill", "target": "skills/x/SKILL.md", "encodes": ["pat_request_x"],
                                        "status": "encoded"}])
        ms = self.json_cmd("meta", "--external", str(ext))
        by = {m["signal"]: m for m in ms}
        self.assertEqual(by["correction-hotspot"]["about"], ["translation"])
        self.assertIn("art", by["blind-spot"]["about"])
        self.assertIn("formal", by["preference-drift"]["statement"])
        self.assertIn("'formal' to 'casual'", by["preference-drift"]["statement"])
        self.assertEqual(sorted(by["principle-conflict"]["about"]), ["P1", "P2"])
        self.assertIn("unclassified-share", by)
        self.assertIn("label-gap", by)
        self.assertEqual(by["encoding-unused"]["about"], ["enc_skill_x"])
        onto = sc.Ontology.load()
        rep = sc.Report()
        sc.validate_records("MetaPattern", [(m["id"], m) for m in ms], onto, rep)
        self.assertEqual(rep.errors, [])

    def test_seed_concentration_not_reproposed(self):
        ms = self.json_cmd("meta", seeds=True)
        self.assertFalse(any(m["id"] == "mp_kind-concentration_provenance" for m in ms))
        ms = self.json_cmd("meta", "--no-seeds")
        self.assertFalse(any(m["signal"] == "kind-concentration" for m in ms))


class RecordTest(Base):
    def test_record_appends_store_and_events_and_validates(self):
        recs = [json.loads(l) for l in (ROOT / "patterns" / "seed_patterns.jsonl").read_text(encoding="utf-8").splitlines()]
        f = self.tmp / "approved.jsonl"
        f.write_text("\n".join(json.dumps(r, ensure_ascii=False) for r in recs), encoding="utf-8")
        code, out, err = self.run_cmd("record", "--file", str(f))
        self.assertEqual(code, 0, err)
        self.assertEqual(len((self.tmp / "patterns" / "patterns.jsonl").read_text().splitlines()), 8)
        self.assertEqual(len((self.tmp / "patterns" / "encodings.jsonl").read_text().splitlines()), 2)
        self.assertEqual(len((self.tmp / "patterns" / "meta.jsonl").read_text().splitlines()), 1)
        events = [json.loads(l) for p in (self.tmp / "log").glob("*.jsonl") for l in p.read_text().splitlines()]
        types = {e["type"] for e in events}
        self.assertEqual(types, {"pattern_proposed", "pattern_promoted"})
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf), contextlib.redirect_stderr(io.StringIO()):
            code = sc.main(["--root", str(self.tmp)])
        self.assertEqual(code, 0, buf.getvalue())
        self.assertIn("as Pattern: 8 record(s)", buf.getvalue())
        self.assertIn("0 error(s), 0 warning(s)", buf.getvalue())
        # the stores are now the source; report reads them
        code, out, _ = self.run_cmd("report")
        self.assertIn("enc_skill_check", out)

    def test_record_rejects_placeholders_and_bad_enums(self):
        f = self.tmp / "bad.jsonl"
        f.write_text("\n".join(json.dumps(r) for r in [
            {"id": "enc_x", "kind": "<choose: hook>", "target": "<path>", "encodes": ["pat_a"], "status": "proposed"},
            {"id": "pat_y", "kind": "vibes", "statement": "s", "status": "candidate", "evidence": ["x"]},
        ]), encoding="utf-8")
        code, _, err = self.run_cmd("record", "--file", str(f))
        self.assertEqual(code, 1)
        self.assertIn("placeholders", err)
        self.assertIn("'vibes' not one of", err)
        self.assertFalse((self.tmp / "patterns").exists())

    def test_record_accepts_ladder_proposals(self):
        self.log([ev(f"2026-10-0{i}", "decision", f"s{i}", scope="translation/a", intent="formal register",
                     situation="x", meta={"kind_of_thing": "formal register"}) for i in (1, 2, 3)])
        cand = self.json_cmd("mine")["candidates"][0]
        self.store("patterns.jsonl", [cand])
        out = self.tmp / "props.jsonl"
        self.run_cmd("ladder", "--out", str(out))
        code, _, err = self.run_cmd("record", "--file", str(out))
        self.assertEqual(code, 0, err)
        latest = pt.newest_per_id(pt.read_jsonl(self.tmp / "patterns" / "patterns.jsonl"))
        self.assertEqual(latest[cand["id"]]["status"], "proposed")


class SeedTest(unittest.TestCase):
    def test_seeds_validate_and_link(self):
        onto = sc.Ontology.load()
        recs = [json.loads(l) for l in (ROOT / "patterns" / "seed_patterns.jsonl").read_text(encoding="utf-8").splitlines()]
        rep = sc.Report()
        for r in recs:
            sc.validate_records(pt.TYPES[r["id"][:4] if r["id"].startswith(("pat_", "enc_")) else "mp_"],
                                [(r["id"], r)], onto, rep)
        self.assertEqual(rep.errors, [])
        self.assertEqual(rep.warnings, [])
        pats = {r["id"]: r for r in recs if r["id"].startswith("pat_")}
        encs = [r for r in recs if r["id"].startswith("enc_")]
        self.assertEqual(len(pats), 8)
        self.assertEqual({e["target"] for e in encs}, {"skills/check/SKILL.md", "skills/fanout-plan/SKILL.md"})
        for e in encs:
            self.assertTrue((ROOT / e["target"]).is_file())
            for pid in e["encodes"]:
                self.assertIn(e["id"], pats[pid]["encoded_by"])
        for p in pats.values():
            self.assertGreaterEqual(len(p["evidence"]), 2)
            self.assertTrue(all(x.startswith("session-note:") for x in p["evidence"]))
        self.assertTrue(any(r["id"].startswith("mp_") for r in recs))


if __name__ == "__main__":
    unittest.main()
