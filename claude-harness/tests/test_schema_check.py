"""Tests for scripts/schema_check.py and the v0.2 ontology. Run from the harness root:
    python3 -I -m unittest tests.test_schema_check
"""
import importlib.util
import io
import json
import pathlib
import subprocess
import sys
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout

ROOT = pathlib.Path(__file__).resolve().parent.parent
SCRIPT = ROOT / "scripts" / "schema_check.py"
sys.dont_write_bytecode = True
_spec = importlib.util.spec_from_file_location("schema_check", SCRIPT)
sc = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(sc)


def _load(name):
    spec = importlib.util.spec_from_file_location(name, ROOT / "scripts" / f"{name}.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def run(argv):
    buf = io.StringIO()
    with redirect_stdout(buf), redirect_stderr(io.StringIO()):
        code = sc.main(argv)
    return code, buf.getvalue()


class TestYamlSubset(unittest.TestCase):
    def test_block_and_flow(self):
        text = """
# comment
a: 1
b: [x, "y, z", 'q']   # trailing comment
c: {k: v, n: null, t: true, s: "a # not a comment"}
d:
  - id: one
    tags: []
  - two
e:
- 3
f: |
  line1
  line2
"""
        d = sc.yaml_load(text)
        self.assertEqual(d["a"], 1)
        self.assertEqual(d["b"], ["x", "y, z", "q"])
        self.assertEqual(d["c"], {"k": "v", "n": None, "t": True, "s": "a # not a comment"})
        self.assertEqual(d["d"], [{"id": "one", "tags": []}, "two"])
        self.assertEqual(d["e"], [3])
        self.assertEqual(d["f"], "line1\nline2")

    def test_escaped_quotes_inside_string(self):
        d = sc.yaml_load('cmd: "grep \\"^## x\\" f || echo \\"m\\"   # kept"\n')
        self.assertEqual(d["cmd"], 'grep "^## x" f || echo "m"   # kept')

    def test_bad_flow_raises(self):
        with self.assertRaises(sc.YamlError):
            sc.yaml_load("a: [1, 2\n")

    def test_all_repo_yaml_parses(self):
        for p in list((ROOT / "rubrics").glob("*.yaml")) + list((ROOT / "evals").glob("*/task_template.yaml")):
            with self.subTest(p=p.name):
                self.assertIsInstance(sc.yaml_load(p.read_text(encoding="utf-8")), dict)


class TestOntology(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.o = sc.Ontology.load()

    def test_version_and_compat_lines(self):
        self.assertEqual(self.o.version, "0.2.0")
        # style_pairs.py and weekly_report.py read these lines with regexes
        self.assertEqual(_load("style_pairs").load_registers(), self.o.registers)
        self.assertEqual(_load("weekly_report").load_areas(ROOT / "schema" / "ontology.yaml"), self.o.areas)

    def test_v01_types_kept(self):
        for t in ("Project", "Client", "Task", "Document", "Asset", "Decision", "Correction", "Mishap", "Lesson",
                  "SessionNote", "Proof", "Preference", "StylePair", "Application", "Evaluation", "Invoice",
                  "Message", "Thread", "Contact", "Organization", "Platform", "JobLead", "SyncCursor", "Attachment"):
            self.assertIn(t, self.o.types)

    def test_every_type_has_store_and_valid_refs(self):
        privacy = set(self.o.enums["privacy"])
        for name, t in self.o.types.items():
            with self.subTest(type=name):
                st = t["store"]
                for k in ("root", "path", "format", "append_only", "privacy", "status"):
                    self.assertIn(k, st)
                self.assertIn(st["privacy"], privacy)
                self.assertIn(st["status"], ("active", "planned"))
                fields = set(t["fields"])
                for f in t.get("required") or []:
                    self.assertIn(f, fields)
                for f, ref in (t.get("enums") or {}).items():
                    self.assertIn(f, fields)
                    self.assertTrue(self.o.enum_values(ref))
                for f, target in (t.get("refs") or {}).items():
                    self.assertIn(f, fields)
                    self.assertIn(target, self.o.types)
                for raw, canon in (t.get("aliases") or {}).items():
                    self.assertIn(canon, fields)

    def test_account_wiring(self):
        acct = self.o.types["Account"]
        self.assertEqual(acct["id_prefix"], "acct_")
        for t in ("Message", "Thread", "Attachment", "SyncCursor", "Application", "JobLead"):
            self.assertIn("account", self.o.types[t]["fields"])
            self.assertEqual(self.o.types[t]["refs"]["account"], "Account")

    def test_vault_types_are_never_git_synced(self):
        for t in ("Message", "Thread", "Attachment", "SyncCursor", "StyleSample"):
            self.assertEqual(self.o.types[t]["store"]["privacy"], "vault")

    def test_relations_have_domain_range(self):
        names = set()
        for r in self.o.data["relations"]:
            self.assertTrue(r["domain"] and r["range"])
            for t in r["domain"]:
                self.assertIn(t, self.o.types)
            names.add(r["name"])
        for n in ("part_of", "for_client", "produced_by", "derived_from", "evidence_for", "proven_by", "supersedes",
                  "corrects", "prevents", "learned_from", "handed_off_to", "evaluated_by", "blocks"):
            self.assertIn(n, names)


class DataBase(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = pathlib.Path(self.tmp.name)
        self.o = sc.Ontology.load()

    def tearDown(self):
        self.tmp.cleanup()

    def write(self, rel, text):
        p = self.root / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(text, encoding="utf-8")
        return p

    def jsonl(self, rel, recs):
        return self.write(rel, "".join(json.dumps(r, ensure_ascii=False) + "\n" for r in recs))


class TestValidation(DataBase):
    def check(self, rel, typ):
        rep = sc.Report()
        sc.check_file(self.root / rel, typ, self.o, rep)
        return rep

    def test_real_script_outputs_pass(self):
        """Records written by the harness's own scripts validate cleanly."""
        import os
        env = dict(os.environ, HARNESS_DATA=str(self.root))
        for kind, payload in (("prompt", {"prompt": "no, use X", "cwd": "/w/translation/acme", "session_id": "s"}),
                              ("session_end", {"reason": "exit"})):
            subprocess.run([sys.executable, "-I", str(ROOT / "hooks" / "log_event.py"), kind],
                           input=json.dumps(payload), text=True, env=env, check=True)
        sp = _load("style_pairs")
        sp.add({"draft": "a", "final": "b", "language": "en", "direction": "en-ko", "register": "office",
                "scope": "translation/acme"}, self.root / "style" / "pairs.jsonl")
        code, out = run(["--root", str(self.root)])
        self.assertEqual(code, 0, out)
        self.assertIn("as Event: 2 record(s)", out)
        self.assertIn("as StylePair: 1 record(s)", out)
        self.assertIn("0 error(s), 0 warning(s)", out)

    def test_event_errors(self):
        self.jsonl("log/2026-10.jsonl", [
            {"id": "evt_x", "ts": "bad", "actor": "me", "type": "nope", "scope": "mars/x"},
            {"ts": "2026-10-16T00:00:00Z", "type": "prompt"},
        ])
        rep = self.check("log/2026-10.jsonl", "Event")
        text = "\n".join(rep.errors)
        for needle in ("'nope' not one of", "not an ISO 8601", "scope must be", "does not match", "'id' missing",
                       "'actor' missing"):
            self.assertIn(needle, text)

    def test_duplicate_event_id(self):
        ev = {"id": "evt_20261016_143205_ab12", "ts": "2026-10-16T14:32:05Z", "actor": "me", "type": "task"}
        self.jsonl("log/2026-10.jsonl", [ev, ev])
        rep = self.check("log/2026-10.jsonl", "Event")
        self.assertTrue(any("duplicate id" in e for e in rep.errors))

    def test_expected_fields_warn_unless_labeled(self):
        dec = {"id": "evt_20261016_143205_ab12", "ts": "2026-10-16T14:32:05Z", "actor": "me", "type": "decision"}
        self.jsonl("log/2026-10.jsonl", [dec])
        rep = self.check("log/2026-10.jsonl", "Event")
        self.assertEqual(rep.errors, [])
        self.assertTrue(any("expected intent, situation, meta" in w for w in rep.warnings))
        lab = {"id": "evt_20261017_000000_cd34", "ts": "2026-10-17T00:00:00Z", "actor": "agent:librarian",
               "type": "label", "labels_for": dec["id"], "intent": "x", "situation": "y", "meta": {}}
        self.jsonl("log/2026-10.jsonl", [dec, lab])
        rep = self.check("log/2026-10.jsonl", "Event")
        self.assertEqual(rep.warnings, [])

    def test_undeclared_field_warns(self):
        self.jsonl("preferences.jsonl", [{"id": "pref_1", "statement": "s", "scope": "global", "colour": "red"}])
        rep = self.check("preferences.jsonl", "Preference")
        self.assertEqual(rep.errors, [])
        self.assertTrue(any("colour" in w for w in rep.warnings))

    def test_application_status_aliases_and_account_ref(self):
        self.jsonl("applications.jsonl", [
            {"id": "app-a", "org": "O", "role": "R", "status": "applied", "account": "acct_main"},
            {"id": "app-a", "org": "O", "role": "R", "status": "no-response"},       # alias -> warning
            {"id": "app-b", "org": "O", "role": "R", "status": "maybe"},             # error
            {"id": "x-c", "org": "O", "role": "R", "status": "lead", "account": "me@example.com"},
        ])
        rep = self.check("applications.jsonl", "Application")
        errs = "\n".join(rep.errors)
        self.assertIn("'maybe' not one of", errs)
        self.assertIn("does not start with 'app-'", errs)
        self.assertIn("is not a Account id", errs)
        self.assertNotIn("duplicate", errs)  # event-sourced: same id may repeat
        self.assertTrue(any("alias of 'ghosted'" in w for w in rep.warnings))

    def test_account_record(self):
        self.jsonl("accounts.jsonl", [
            {"id": "acct_hub", "provider": "workspace", "address": "a@example.org", "is_hub": True,
             "connected_via": ["claude-connector", "forwarding"], "privacy": "harness-data"},
            {"id": "acct_x", "provider": "pigeon", "connected_via": "telepathy", "privacy": "public",
             "forwards_to": "hub"},
        ])
        rep = self.check("accounts.jsonl", "Account")
        errs = "\n".join(rep.errors)
        self.assertNotIn("[0]", " ".join(e.split(": ")[0] for e in rep.errors))
        for needle in ("'pigeon'", "'telepathy'", "'public'", "'hub' is not a Account id"):
            self.assertIn(needle, errs)

    def test_stylepair_direction_alias(self):
        self.jsonl("style/pairs.jsonl", [{"id": "sp_20261016_000000_abcd", "ts": "2026-10-16T00:00:00+00:00",
                                         "draft": "a", "final": "b", "language": "en", "direction": "en-ko",
                                         "register": "office"}])
        rep = self.check("style/pairs.jsonl", "StylePair")
        self.assertEqual(rep.errors, [])
        self.assertTrue(any("alias of 'en→ko'" in w for w in rep.warnings))

    def test_ledger_csv(self):
        self.write("finance/ledger.csv",
                   "ts,event,invoice_id,client,currency,status,issued\n"
                   "2026-10-16T00:00:00+00:00,issued,INV-2026-001,acme,KRW,issued,2026-10-16\n"
                   "2026-10-17T00:00:00+00:00,status,INV-2026-001,acme,KRW,paid,\n"
                   "2026-10-17T00:00:00+00:00,refund,BAD-1,acme,KRW,lost,17/10/2026\n")
        rep = self.check("finance/ledger.csv", "LedgerEntry")
        errs = "\n".join(rep.errors)
        self.assertEqual(sum(":4" in e for e in rep.errors), len(rep.errors))  # only the bad row
        for needle in ("'refund'", "'lost'", "'BAD-1'", "YYYY-MM-DD"):
            self.assertIn(needle, errs)

    def test_project_manifest_and_assets(self):
        proj = self.root / "translation" / "acme"
        (proj / "knowledge").mkdir(parents=True)
        src = self.write("translation/acme/inbox/a.txt", "hello")
        kb = _load("kb")
        kb.KB(proj / "knowledge").register(src)
        self.write("translation/acme/assets/assets.yaml",
                   '- id: A-1a2b3c4d-1\n  type: layer\n  name: "bg"\n  source: "knowledge/raw/1a2b3c4d_a.psd#bg"\n'
                   '  path: null\n  provenance: {extracted_by: "psd-tools@1.9", on: "2026-10-16", from_sha256: "ab"}\n'
                   '  rights: {owner: "unknown", license: "unknown", notes: ""}\n  variants: []\n  tags: ["bbox:0,0,1,1"]\n'
                   '- id: B-2\n  type: sprite\n')
        code, out = run(["--root", str(self.root / "nope"), "--project", str(proj)])
        self.assertEqual(code, 1)
        self.assertIn("as Document: 1 record(s)", out)
        self.assertIn("as Asset: 2 record(s)", out)
        self.assertIn("'sprite' not one of", out)
        self.assertIn("does not start with 'A-'", out)
        self.assertNotIn("assets.yaml[0]", out)

    def test_cli_usage_and_json(self):
        self.jsonl("preferences.jsonl", [{"id": "pref_1", "statement": "s", "scope": "global", "extra": 1}])
        code, out = run(["--json", "--root", str(self.root)])
        self.assertEqual(code, 0)
        data = json.loads(out)
        self.assertTrue(data["ok"])
        self.assertEqual(data["ontology_version"], "0.2.0")
        code, out = run(["--json", "--strict", "--root", str(self.root)])
        self.assertEqual(code, 1)
        code, _ = run(["--file", "x", "--type", "NoSuchType"])
        self.assertEqual(code, 2)
        code, out = run(["--stores"])
        self.assertEqual(code, 0)
        self.assertIn("| Account | harness-data | `accounts.jsonl`", out)

    def test_storage_md_lists_every_type(self):
        text = (ROOT / "schema" / "STORAGE.md").read_text(encoding="utf-8")
        for name in self.o.types:
            self.assertIn(f"| {name} |", text)


if __name__ == "__main__":
    unittest.main()
