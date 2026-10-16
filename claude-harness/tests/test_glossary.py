"""Tests for scripts/glossary.py. Stdlib only.

Run from the harness root:
    python3 -I -m unittest discover -s tests -t . -p 'test_glossary.py'
"""
import importlib.util
import json
import pathlib
import shutil
import subprocess
import sys
import tempfile
import unittest

ROOT = pathlib.Path(__file__).resolve().parent.parent
SCRIPT = ROOT / "scripts" / "glossary.py"
TEMPLATE = ROOT / "templates" / "glossary.md"
_spec = importlib.util.spec_from_file_location("glossary", SCRIPT)
gl = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(gl)

OLD_FORMAT = """# Glossary

| Source | Target | Dir | Domain | Client | DNT | Status | Notes |
|---|---|---|---|---|---|---|---|
| 계약서 | agreement | ko-en | legal | any | N | preferred | a \\| b |

## Changelog
- 2026-10-16: start
"""

TMX = """<?xml version="1.0" encoding="UTF-8"?>
<tmx version="1.4"><header srclang="ko" datatype="plaintext" segtype="phrase" adminlang="en"
 creationtool="x" creationtoolversion="1" o-tmf="x"/>
<body>
  <tu><tuv xml:lang="ko-KR"><seg>담당자</seg></tuv><tuv xml:lang="en-US"><seg>point of contact</seg></tuv></tu>
  <tu><tuv xml:lang="ko"><seg>계약서</seg></tuv><tuv xml:lang="en"><seg>agreement</seg></tuv></tu>
  <tu><tuv xml:lang="ko"><seg>이 문장은 용어가 아니라 긴 문장이므로 가져오지 않아야 합니다 정말로</seg></tuv>
      <tuv xml:lang="en"><seg>This sentence is long and is not a term so it must be skipped</seg></tuv></tu>
  <tu><tuv xml:lang="ko"><seg>견적서</seg></tuv></tu>
</body></tmx>
"""

TBX3 = """<?xml version="1.0" encoding="UTF-8"?>
<tbx type="TBX-Basic" style="dca" xml:lang="ko" xmlns="urn:iso:std:iso:30042:ed-2">
<text><body>
  <conceptEntry id="c1">
    <descrip type="subjectField">legal</descrip>
    <langSec xml:lang="ko"><termSec><term>위약금</term></termSec></langSec>
    <langSec xml:lang="en">
      <termSec><term>penalty</term><termNote type="administrativeStatus">preferredTerm-admn-sts</termNote></termSec>
      <termSec><term>fine</term><termNote type="administrativeStatus">deprecatedTerm-admn-sts</termNote></termSec>
    </langSec>
  </conceptEntry>
</body></text></tbx>
"""


class Base(unittest.TestCase):
    def setUp(self):
        self.tmp = pathlib.Path(tempfile.mkdtemp())

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def write(self, name, text):
        p = self.tmp / name
        p.write_text(text, encoding="utf-8")
        return p

    def cli(self, *args):
        return subprocess.run([sys.executable, "-I", str(SCRIPT), *args], capture_output=True, text=True)


class TestParse(Base):
    def test_template_parses_with_new_columns(self):
        rows = gl.load(TEMPLATE)
        by = {r["source"]: r for r in rows}
        self.assertEqual(by["계약서"]["confidence"], "high")
        self.assertEqual(by["Acme Cloud"]["dnt"], True)
        self.assertEqual(by["Acme Cloud"]["sources"], ["acme style sheet 2026-10"])
        self.assertEqual(by["stakeholder"]["sources"], [])
        self.assertEqual(set(rows[0]), set(gl.COLUMNS))

    def test_old_format_and_escaped_pipe(self):
        rows = gl.parse_markdown(OLD_FORMAT)
        self.assertEqual(rows[0]["notes"], "a | b")
        self.assertEqual(rows[0]["confidence"], "")
        self.assertEqual(rows[0]["sources"], [])

    def test_to_json_cli(self):
        r = self.cli("to-json", str(TEMPLATE))
        self.assertEqual(r.returncode, 0, r.stderr)
        data = json.loads(r.stdout)
        self.assertTrue(any(d["source"] == "{{user_name}}" and d["dnt"] for d in data))

    def test_no_table(self):
        p = self.write("g.md", "# nothing here\n")
        self.assertEqual(self.cli("to-json", str(p)).returncode, 2)


class TestImport(Base):
    def test_import_tmx_adds_proposed_rows_sorted_and_keeps_rest(self):
        g = self.write("glossary.md", OLD_FORMAT)
        t = self.write("client.tmx", TMX)
        r = self.cli("import-tmx", str(t), "--glossary", str(g), "--src", "ko", "--tgt", "en",
                     "--domain", "business", "--client", "acme")
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn("1 new row", r.stderr)  # 계약서/agreement already there; long + one-sided skipped
        text = g.read_text(encoding="utf-8")
        self.assertIn("| Confidence | Sources |", text)  # table upgraded to the full column set
        self.assertIn("## Changelog", text)
        rows = gl.parse_markdown(text)
        self.assertEqual([r["source"] for r in rows], ["계약서", "담당자"])
        new = rows[1]
        self.assertEqual((new["status"], new["dir"], new["client"], new["domain"]),
                         ("proposed", "ko-en", "acme", "business"))
        self.assertEqual(new["sources"], ["tmx:client.tmx"])
        self.assertEqual(rows[0]["notes"], "a | b")
        # idempotent
        r = self.cli("import-tmx", str(t), "--glossary", str(g), "--src", "ko", "--tgt", "en")
        self.assertIn("0 new row", r.stderr)

    def test_dry_run_does_not_write(self):
        g = self.write("glossary.md", OLD_FORMAT)
        t = self.write("client.tmx", TMX)
        r = self.cli("import-tmx", str(t), "--glossary", str(g), "--src", "ko", "--tgt", "en", "--dry-run")
        self.assertIn("would add", r.stdout)
        self.assertEqual(g.read_text(encoding="utf-8"), OLD_FORMAT)

    def test_import_tbx_v3_maps_status(self):
        rows = gl.read_tbx(self.write("t.tbx", TBX3), "ko", "en")
        got = {(r["source"], r["target"], r["status"], r["domain"]) for r in rows}
        self.assertEqual(got, {("위약금", "penalty", "approved", "legal"), ("위약금", "fine", "forbidden", "legal")})

    def test_refuses_entity_declarations(self):
        bad = self.write("x.tbx", '<?xml version="1.0"?><!DOCTYPE x [<!ENTITY a "aaaa">]><martif/>')
        with self.assertRaises(gl.GlossaryError):
            gl.read_tbx(bad, "ko", "en")


class TestExport(Base):
    def test_export_tbx_round_trip(self):
        out = self.tmp / "out.tbx"
        r = self.cli("export-tbx", str(TEMPLATE), "-o", str(out))
        self.assertEqual(r.returncode, 0, r.stderr)
        text = out.read_text(encoding="utf-8")
        self.assertIn("<martif", text)
        self.assertNotIn("수고하셨습니다", text)  # no fixed target -> not exported
        back = {(x["source"], x["target"]): x for x in gl.read_tbx(out, "ko", "en")}
        self.assertIn(("계약서", "agreement"), back)
        self.assertEqual(back[("계약서", "agreement")]["confidence"], "high")
        self.assertEqual(back[("계약서", "agreement")]["sources"], ["user"])
        self.assertEqual(back[("계약서", "agreement")]["domain"], "legal")
        self.assertIn(("이해관계자", "stakeholder"), back)  # en-ko row flipped into ko->en
        self.assertIn(("Acme Cloud", "Acme Cloud"), back)
        self.assertEqual(back[("Acme Cloud", "Acme Cloud")]["status"], "approved")


if __name__ == "__main__":
    unittest.main()
