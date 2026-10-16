"""Tests for scripts/kb.py. No converters required.

Run from the harness root:
    python3 -I -m unittest discover -s tests -t . -p 'test_kb.py'
(`python3 -I -m unittest tests.test_kb` also works without -I; -I drops the cwd from sys.path.)
"""
import csv
import hashlib
import importlib.util
import json
import pathlib
import shutil
import subprocess
import sys
import tempfile
import unittest
from unittest import mock

HERE = pathlib.Path(__file__).resolve().parent
KB_PY = HERE.parent / "scripts" / "kb.py"
_spec = importlib.util.spec_from_file_location("kb", KB_PY)
kb = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(kb)


def page(source_id, body="Claim [p.1](../raw/X#p.1).", **over):
    fm = {
        "topic": "Budget",
        "summary": "Budget caps per phase",
        "source_id": source_id,
        "source_name": "brief.pdf",
        "pages": "[1, 2]",
        "converter": "markitdown@0.1.2",
        "confidence": "high",
        "intake_intent": "defines scope limits",
    }
    fm.update(over)
    lines = ["---"] + [f"{k}: {v}" for k, v in fm.items() if v is not None] + ["---", "", body, ""]
    return "\n".join(lines)


class Base(unittest.TestCase):
    def setUp(self):
        self.tmp = pathlib.Path(tempfile.mkdtemp())
        self.kb = kb.KB(self.tmp / "knowledge")
        self.src = self.tmp / "inbox"
        self.src.mkdir()

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def make(self, name, content=b"hello"):
        p = self.src / name
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_bytes(content)
        return p

    def cli(self, *args):
        return subprocess.run([sys.executable, "-I", str(KB_PY), "--kb", str(self.kb.root), *args],
                              capture_output=True, text=True)


class TestRegister(Base):
    def test_register_copies_and_records(self):
        p = self.make("My Brief.pdf", b"pdf-bytes")
        digest = hashlib.sha256(b"pdf-bytes").hexdigest()
        entry, new = self.kb.register(p)
        self.assertTrue(new)
        raw = self.kb.raw / f"{digest[:8]}_My_Brief.pdf"
        self.assertTrue(raw.is_file())
        self.assertEqual(raw.read_bytes(), b"pdf-bytes")
        m = json.loads(self.kb.manifest_path.read_text())
        self.assertEqual(len(m["sources"]), 1)
        s = m["sources"][0]
        self.assertEqual(s["sha256"], digest)
        self.assertEqual(s["original_name"], "My Brief.pdf")
        self.assertIsNone(s["converter"])
        self.assertIsNone(s["archive"])
        self.assertEqual(s["pages_produced"], [])
        self.assertRegex(s["received"], r"^\d{4}-\d{2}-\d{2}$")
        self.assertEqual(p.read_bytes(), b"pdf-bytes")  # source untouched

    def test_register_idempotent_on_same_hash(self):
        a = self.make("a.txt", b"same")
        b = self.make("b.txt", b"same")
        self.kb.register(a)
        _, new = self.kb.register(b)
        self.assertFalse(new)
        self.assertEqual(len(self.kb.load()["sources"]), 1)
        self.assertEqual(len(list(self.kb.raw.iterdir())), 1)

    def test_register_missing_file(self):
        with self.assertRaises(kb.KBError):
            self.kb.register(self.tmp / "nope.pdf")

    def test_cli_register(self):
        p = self.make("x.md", b"# x")
        r = self.cli("register", str(p))
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn("registered", r.stdout)
        r = self.cli("register", str(p))
        self.assertIn("already registered", r.stdout)


class TestConvert(Base):
    def test_no_converter_gives_clear_message(self):
        e, _ = self.kb.register(self.make("a.pdf", b"x"))
        with mock.patch.object(kb.shutil, "which", return_value=None):
            with self.assertRaises(kb.KBError) as cm:
                kb.convert(self.kb, e["id"], self.tmp / "work")
        self.assertIn("no converter installed", str(cm.exception))

    def test_convert_records_converter(self):
        e, _ = self.kb.register(self.make("a.pdf", b"x"))
        fake = ("fake", "fake", ["fake"], lambda src, out: "<!-- p.1 -->\nhello\n")
        with mock.patch.object(kb, "available_converters", return_value=[fake]), \
             mock.patch.object(kb, "_version", return_value="9.9"):
            out, conv = kb.convert(self.kb, e["id"], self.tmp / "work")
        self.assertEqual(conv, "fake@9.9")
        self.assertIn("hello", out.read_text())
        self.assertEqual(self.kb.load()["sources"][0]["converter"], "fake@9.9")


def fake_converters(log, fail=()):
    """Stand-in CONVERTERS table: same names, runners that record which one ran."""
    def runner(name):
        def run(src, out, **opts):
            log.append((name, opts))
            if name in fail:
                raise kb.KBError(f"{name} failed")
            return f"<!-- p.1 -->\nconverted by {name}\n"
        return run
    return [(n, n, [n, "--version"], runner(n)) for n in ("markitdown", "docling", "marker", "kordoc", "pdftotext")]


class TestConverterOrder(Base):
    def test_order_by_extension(self):
        for ext in (".hwp", ".HWPX", ".hml"):
            self.assertEqual(kb.converter_order(f"a{ext}"), ["kordoc"])
        self.assertEqual(kb.converter_order("a.hwp", ocr=True), ["kordoc"])
        pdf = kb.converter_order("a.pdf")
        self.assertEqual(pdf[0], "markitdown")
        self.assertIn("kordoc", pdf)
        self.assertLess(pdf.index("kordoc"), pdf.index("pdftotext"))
        self.assertEqual(kb.converter_order("scan.pdf", ocr=True)[0], "kordoc")

    def _convert(self, name, ocr=False, installed=None, fail=()):
        e, _ = self.kb.register(self.make(name, name.encode()))
        log = []
        which = (lambda exe: f"/usr/bin/{exe}") if installed is None else \
            (lambda exe: f"/usr/bin/{exe}" if exe in installed else None)
        with mock.patch.object(kb, "CONVERTERS", fake_converters(log, fail)), \
             mock.patch.object(kb.shutil, "which", side_effect=which), \
             mock.patch.object(kb, "_version", return_value="4.22.5"):
            out, conv = kb.convert(self.kb, e["id"], self.tmp / "work", ocr=ocr)
        return out, conv, log

    def test_hwp_goes_to_kordoc(self):
        out, conv, log = self._convert("공문.hwp")
        self.assertEqual(conv, "kordoc@4.22.5")
        self.assertEqual(log, [("kordoc", {})])
        self.assertIn("converted by kordoc", out.read_text(encoding="utf-8"))

    def test_hwp_never_falls_back_to_other_converters(self):
        e, _ = self.kb.register(self.make("a.hwpx", b"x"))
        with mock.patch.object(kb, "CONVERTERS", fake_converters([])), \
             mock.patch.object(kb.shutil, "which", side_effect=lambda exe: None if exe == "kordoc" else "/x"):
            with self.assertRaises(kb.KBError) as cm:
                kb.convert(self.kb, e["id"], self.tmp / "work")
        self.assertIn("kordoc", str(cm.exception))
        self.assertIn("kordoc@4.22.5", str(cm.exception))  # pinned install hint

    def test_pdf_default_prefers_markitdown(self):
        _, conv, log = self._convert("a.pdf")
        self.assertEqual(conv, "markitdown@4.22.5")
        self.assertEqual([n for n, _ in log], ["markitdown"])

    def test_scan_pdf_uses_kordoc_with_ocr(self):
        _, conv, log = self._convert("스캔.pdf", ocr=True)
        self.assertEqual(log, [("kordoc", {"ocr": True})])
        self.assertTrue(conv.startswith("kordoc@"))
        self.assertEqual(self.kb.load()["sources"][0]["converter_options"], ["--ocr"])

    def test_scan_falls_back_when_kordoc_fails(self):
        _, conv, log = self._convert("scan.pdf", ocr=True, fail=("kordoc",))
        self.assertEqual([n for n, _ in log], ["kordoc", "docling"])
        self.assertTrue(conv.startswith("docling@"))

    def test_kordoc_runs_offline(self):
        def fake_run(cmd, **kw):
            out = pathlib.Path(cmd[cmd.index("-o") + 1])
            out.write_text("# 제목\n", encoding="utf-8")
            calls.append((cmd, kw))
            return subprocess.CompletedProcess(cmd, 0, "", "")
        calls = []
        with mock.patch.object(kb.subprocess, "run", side_effect=fake_run):
            md = kb._conv_kordoc(pathlib.Path("a.hwp"), self.tmp, ocr=True)
        self.assertEqual(md, "# 제목\n")
        cmd, kw = calls[0]
        self.assertEqual(cmd[:2], ["kordoc", "a.hwp"])
        self.assertIn("--ocr", cmd)
        self.assertEqual(kw["env"]["KORDOC_OFFLINE"], "1")

    def test_version_check_also_offline(self):
        with mock.patch.object(kb.subprocess, "run",
                               return_value=subprocess.CompletedProcess([], 0, "4.22.5\n", "")) as m:
            self.assertEqual(kb._version(["kordoc", "--version"]), "4.22.5")
        self.assertEqual(m.call_args.kwargs["env"]["KORDOC_OFFLINE"], "1")
        with mock.patch.object(kb.subprocess, "run",
                               return_value=subprocess.CompletedProcess([], 0, "1.0\n", "")) as m:
            kb._version(["markitdown", "--version"])
        self.assertIsNone(m.call_args.kwargs["env"])  # other converters: inherited env

    def test_kordoc_failure_json_surfaces(self):
        fail = subprocess.CompletedProcess([], 1, '{"success":false,"code":"IMAGE_BASED_PDF"}', "")
        with mock.patch.object(kb.subprocess, "run", return_value=fail):
            with self.assertRaises(kb.KBError) as cm:
                kb._conv_kordoc(pathlib.Path("a.pdf"), self.tmp)
        self.assertIn("IMAGE_BASED_PDF", str(cm.exception))


class TestIndexLint(Base):
    def setUp(self):
        super().setUp()
        self.entry, _ = self.kb.register(self.make("brief.pdf", b"brief"))
        self.sid = self.entry["id"]
        self.rawname = pathlib.Path(self.entry["raw_path"]).name

    def write(self, name, text):
        (self.kb.wiki / name).write_text(text, encoding="utf-8")

    def test_index_from_frontmatter(self):
        self.write("budget.md", page(self.sid))
        self.write("people.md", page(self.sid, topic="People", summary="Who decides"))
        n = self.kb.index()
        self.assertEqual(n, 2)
        idx = self.kb.index_path.read_text()
        self.assertIn("- Budget: Budget caps per phase: wiki/budget.md", idx)
        self.assertIn("- People: Who decides: wiki/people.md", idx)

    def test_lint_clean(self):
        self.write("budget.md", page(self.sid, body=f"Cap is 5k [p.1](../raw/{self.rawname}#p.1)."))
        self.assertEqual(self.kb.lint(), [])
        r = self.cli("lint")
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)

    def test_lint_missing_field(self):
        self.write("bad.md", page(self.sid, body=f"[p.1](../raw/{self.rawname}#p.1)", intake_intent=None))
        probs = self.kb.lint()
        self.assertTrue(any("intake_intent" in p for p in probs), probs)

    def test_lint_no_frontmatter(self):
        self.write("bare.md", "just text\n")
        self.assertTrue(any("missing frontmatter" in p for p in self.kb.lint()))

    def test_lint_unknown_source(self):
        self.write("x.md", page("deadbeef", body=f"[p.1](../raw/{self.rawname}#p.1)"))
        self.assertTrue(any("not in manifest" in p for p in self.kb.lint()))

    def test_lint_broken_link_nonzero_exit(self):
        self.write("x.md", page(self.sid, body="See [p.3](../raw/missing_file.pdf#p.3)."))
        self.assertTrue(any("does not resolve" in p for p in self.kb.lint()))
        r = self.cli("lint")
        self.assertEqual(r.returncode, 1)
        self.assertIn("does not resolve", r.stdout)

    def test_frontmatter_block_list(self):
        fm, _ = kb.parse_frontmatter("---\npages:\n  - 3\n  - 4\nconfidence: low\n---\nbody")
        self.assertEqual(fm["pages"], ["3", "4"])
        self.assertEqual(fm["confidence"], "low")


class TestArchive(Base):
    def setUp(self):
        super().setUp()
        self.entry, _ = self.kb.register(self.make("brief.pdf", b"brief"))
        self.sid = self.entry["id"]

    def log(self, line):
        with open(self.kb.log_path, "a", encoding="utf-8") as f:
            f.write(line + "\n")

    def test_not_safe_by_default(self):
        ok, reasons = self.kb.safe_to_delete(self.sid)
        self.assertFalse(ok)
        self.assertEqual(len(reasons), 2)

    def test_archive_only_not_safe(self):
        self.kb.archive(self.sid, "https://drive.google.com/x")
        self.assertEqual(self.kb.load()["sources"][0]["archive"], "https://drive.google.com/x")
        self.assertFalse(self.kb.safe_to_delete(self.sid)[0])

    def test_verified_only_not_safe(self):
        self.log(f"- 2026-10-16 {self.sid} verify PASS 3/3 passages, tables ok")
        self.assertFalse(self.kb.safe_to_delete(self.sid)[0])

    def test_fail_line_does_not_count(self):
        self.kb.archive(self.sid, "https://drive.google.com/x")
        self.log(f"- 2026-10-16 {self.sid} verify FAIL table 2 (PASS on retry pending)")
        self.assertFalse(self.kb.safe_to_delete(self.sid)[0])

    def test_safe_when_verified_and_archived(self):
        self.kb.archive(self.sid, "https://drive.google.com/x")
        self.log(f"- 2026-10-16 {self.sid} verify PASS 3/3 passages, tables ok")
        self.assertTrue(self.kb.safe_to_delete(self.sid)[0])
        r = self.cli("safe-to-delete", self.sid)
        self.assertEqual((r.returncode, r.stdout.strip()), (0, "yes"))

    def test_cli_not_safe_exit_code(self):
        r = self.cli("safe-to-delete", self.sid)
        self.assertEqual(r.returncode, 1)
        self.assertTrue(r.stdout.startswith("no"))

    def test_unknown_id(self):
        with self.assertRaises(kb.KBError):
            self.kb.archive("00000000", "u")
        self.assertEqual(self.cli("archive", "00000000", "u").returncode, 2)


class TestBackcatalog(Base):
    def test_bulk_register_and_report(self):
        self.make("projA/notes.md", b"a")
        self.make("projA/sub/deck.pptx", b"b")
        self.make("projB/copy.md", b"a")  # duplicate of notes.md
        self.make("top.txt", b"c")
        before = {p: p.read_bytes() for p in self.src.rglob("*") if p.is_file()}
        report, rows = kb.backcatalog(self.kb, self.src, self.tmp / "report.csv")
        self.assertEqual(len(rows), 4)
        self.assertEqual(sum(r["status"] == "new" for r in rows), 3)
        self.assertEqual(sum(r["status"] == "duplicate" for r in rows), 1)
        self.assertEqual(len(self.kb.load()["sources"]), 3)
        with open(report, newline="", encoding="utf-8") as f:
            got = list(csv.DictReader(f))
        self.assertEqual(len(got), 4)
        self.assertIn("area", got[0])
        self.assertIn("project", got[0])
        tops = {r["relative_path"]: r["top_folder"] for r in got}
        self.assertEqual(tops[str(pathlib.Path("projA/sub/deck.pptx"))], "projA")
        self.assertEqual(tops["top.txt"], "")
        after = {p: p.read_bytes() for p in self.src.rglob("*") if p.is_file()}
        self.assertEqual(before, after)  # read-only on source

    def test_skips_kb_nested_in_folder(self):
        nested = kb.KB(self.src / "knowledge")
        self.make("a.txt", b"a")
        kb.backcatalog(nested, self.src, self.tmp / "r1.csv")
        _, rows = kb.backcatalog(nested, self.src, self.tmp / "r2.csv")
        self.assertEqual(len(rows), 1)  # the raw/ copy is not re-ingested

    def test_cli_backcatalog(self):
        self.make("p/a.txt", b"a")
        r = self.cli("backcatalog", str(self.src), "--report", str(self.tmp / "r.csv"))
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn("1 new", r.stdout)
        self.assertTrue((self.tmp / "r.csv").is_file())


if __name__ == "__main__":
    unittest.main()
