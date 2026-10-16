"""Tests for scripts/translation_qa.py (Korean <-> English examples). No optional tools required.

Run from the harness root:
    python3 -I -m unittest discover -s tests -t . -p 'test_translation_qa.py'
"""
import importlib.util
import json
import pathlib
import shutil
import subprocess
import sys
import tempfile
import unittest
from types import SimpleNamespace
from unittest import mock

ROOT = pathlib.Path(__file__).resolve().parent.parent
SCRIPT = ROOT / "scripts" / "translation_qa.py"
_spec = importlib.util.spec_from_file_location("translation_qa", SCRIPT)
qa = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(qa)

GLOSSARY = """# Glossary

| Source | Target | Dir | Domain | Client | DNT | Status | Confidence | Sources | Notes |
|---|---|---|---|---|---|---|---|---|---|
| 계약서 | agreement | ko-en | legal | any | N | approved | high | user | |
| 담당자 | point of contact | ko-en | business | any | N | preferred | medium | user | |
| 수고하셨습니다 | — | ko-en | business | any | N | preferred | medium | user | no fixed equivalent |
| Acme Cloud | Acme Cloud | both | tech | acme | Y | approved | high | style sheet | product name |
| stakeholder | 이해관계자 | en-ko | business | any | N | approved | high | user | |
| stakeholder | 관계자 | en-ko | business | any | N | forbidden | high | client 2026-10 | client rejected |
"""


def terms():
    return qa.glossary_mod.parse_markdown(GLOSSARY)


def run(src, tgt, direction="ko-en", gl=None, opts=None, skip=(), warn=(), kiwi=None):
    rep = qa.Report(warn)
    seg = {"id": "1", "source": src, "target": tgt}
    s, t = direction.split("-")
    qa.check_segment(rep, seg, s, t, terms() if gl is None else gl, qa.TermMatcher(kiwi),
                     {"forbid": [], "limit": None, "min": None, "unit": "chars", **(opts or {})}, set(skip))
    return rep


def checks(rep, severity=None):
    return sorted({f["check"] for f in rep.findings if severity in (None, f["severity"])})


class TestNumbers(unittest.TestCase):
    def test_korean_compound_amount_matches_english(self):
        d, _ = qa.numbers("금액은 1억 2천만 원입니다", "ko")
        self.assertEqual(set(d), {"120000000"})
        d, _ = qa.numbers("KRW 120 million", "en")
        self.assertEqual(set(d), {"120000000"})
        self.assertEqual(set(qa.numbers("3만 원", "ko")[0]), {"30000"})
        self.assertEqual(set(qa.numbers("30,000 won", "en")[0]), {"30000"})

    def test_unit_glued_to_other_word_is_not_a_multiplier(self):
        self.assertEqual(set(qa.numbers("5백화점", "ko")[0]), {"5"})

    def test_dates_with_month_names(self):
        rep = run("2026년 10월 16일까지 제출", "Submit by October 16, 2026.", gl=[])
        self.assertEqual(rep.findings, [])

    def test_missing_number_is_blocking(self):
        rep = run("3개 파일을 보냈습니다.", "I sent the files.", gl=[])
        self.assertEqual(checks(rep, "error"), ["numbers"])
        self.assertIn("3", rep.blocking[0]["message"])

    def test_changed_number_blocking_and_extra_warning(self):
        rep = run("총 1,500명", "1,600 people in total", gl=[])
        msgs = {f["severity"]: f["message"] for f in rep.findings if f["check"] == "numbers"}
        self.assertIn("1500", msgs["error"])
        self.assertIn("1600", msgs["warning"])

    def test_number_words_satisfy(self):
        rep = run("2명이 참석합니다.", "Two people will attend.", gl=[])
        self.assertEqual(rep.findings, [])

    def test_placeholders_not_counted_as_numbers(self):
        d, _ = qa.numbers("{0}님, %1$s 확인", "ko")
        self.assertEqual(sum(d.values()), 0)


class TestUnitsTags(unittest.TestCase):
    def test_currency_category_kept(self):
        self.assertEqual(qa.units("5만 원"), {"KRW"})
        self.assertEqual(qa.units("₩50,000"), {"KRW"})
        self.assertEqual(qa.units("5 km and 3 kg"), {"km", "kg"})
        rep = run("가격은 50,000원입니다.", "The price is $50,000.", gl=[])
        self.assertIn("units", checks(rep, "error"))

    def test_percent(self):
        self.assertEqual(run("15% 할인", "15 percent off", gl=[]).findings, [])

    def test_tags_and_placeholders(self):
        src = "<b>{0}</b>님, %s개의 파일이 {{count}}개 남았습니다."
        ok = "<b>{0}</b>, {{count}} of %s files remain."
        self.assertNotIn("tags", checks(run(src, ok, gl=[])))
        bad = "<b>{1}</b>, {{count}} of %d files remain."
        rep = run(src, bad, gl=[])
        self.assertIn("tags", checks(rep, "error"))
        self.assertTrue(any("{0}" in f["message"] for f in rep.blocking))

    def test_url_with_korean_particle(self):
        rep = run("https://example.com/a에서 확인하세요.", "See https://example.com/a.", gl=[])
        self.assertNotIn("tags", checks(rep))

    def test_percent_sign_not_a_placeholder(self):
        self.assertEqual(qa.placeholders("50% discount, 30% d"), {})


class TestGlossary(unittest.TestCase):
    def test_particle_tolerant_match(self):
        m = qa.TermMatcher()
        for text in ("계약서를 보내", "계약서에서는", "계약서.", "새 계약서가"):
            self.assertTrue(m.has("계약서", text), text)
        self.assertFalse(m.has("계약서", "계약서식"))       # different word
        self.assertFalse(m.has("관계자", "이해관계자와"))      # compound is not the term
        self.assertTrue(m.has("이해관계자", "이해 관계자와"))   # spacing variant

    def test_approved_term_missing_is_blocking(self):
        rep = run("계약서를 검토했습니다.", "We reviewed the contract.")
        self.assertEqual(checks(rep, "error"), ["glossary"])
        rep = run("계약서를 검토했습니다.", "We reviewed the agreements.")
        self.assertEqual(rep.findings, [])

    def test_preferred_term_is_warning(self):
        rep = run("담당자에게 연락하세요.", "Contact the person in charge.")
        self.assertEqual(checks(rep, "warning"), ["glossary"])
        self.assertEqual(rep.blocking, [])

    def test_no_fixed_equivalent_is_skipped(self):
        self.assertEqual(run("수고하셨습니다.", "Thanks for your work on this.").findings, [])

    def test_dnt_kept_byte_identical(self):
        self.assertEqual(run("Use Acme Cloud now.", "지금 Acme Cloud를 사용하세요.", "en-ko").findings, [])
        rep = run("Use Acme Cloud now.", "지금 아크미 클라우드를 사용하세요.", "en-ko")
        self.assertEqual(checks(rep, "error"), ["dnt"])
        rep = run("Use Acme Cloud now.", "지금 Acme cloud를 사용하세요.", "en-ko")
        self.assertEqual(checks(rep, "error"), ["dnt"])

    def test_forbidden_term_in_korean_target(self):
        rep = run("Ask the stakeholders.", "관계자에게 물어보세요.", "en-ko")
        self.assertIn("forbidden", checks(rep, "error"))
        self.assertIn("glossary", checks(rep, "error"))
        ok = run("Ask the stakeholders.", "이해관계자에게 물어보세요.", "en-ko")
        self.assertEqual(ok.findings, [])

    def test_forbid_option_and_warn_downgrade(self):
        rep = run(None, "충격적인 반전이 기다린다.", "ko-ko", gl=[], opts={"forbid": ["충격"]})
        self.assertEqual(rep.findings, [])  # 충격적인 is not 충격 + particle
        rep = run(None, "충격적인 반전이 기다린다.", "ko-ko", gl=[], opts={"forbid": ["충격적"]})
        self.assertEqual(checks(rep, "error"), ["forbidden"])  # 충격적 + 인 (copula) is the term
        rep = run(None, "충격적인 반전이 기다린다.", "ko-ko", gl=[], opts={"forbid": ["충격적인"]})
        self.assertEqual(checks(rep, "error"), ["forbidden"])
        rep = run(None, "충격적인 반전", "ko-ko", gl=[], opts={"forbid": ["충격적인"]}, warn=["forbidden"])
        self.assertEqual(rep.blocking, [])

    def test_kiwi_used_when_given(self):
        class FakeKiwi:
            def tokenize(self, text):
                table = {
                    "계약서": [("계약서", "NNG")],
                    "계약서들을 봤다": [("계약서", "NNG"), ("들", "XSN"), ("을", "JKO"), ("보", "VV"), ("었", "EP"), ("다", "EF")],
                }
                return [SimpleNamespace(form=f, tag=t) for f, t in table.get(text, [(text, "NNG")])]
        self.assertTrue(qa.TermMatcher(FakeKiwi()).has("계약서", "계약서들을 봤다"))
        self.assertFalse(qa.TermMatcher(None).has("계약서", "계약서들을봤다"))


class TestOtherChecks(unittest.TestCase):
    def test_double_space_and_length(self):
        rep = run(None, "가족의  비밀이 밝혀진다", "ko-ko", gl=[], opts={"limit": 5})
        self.assertEqual(checks(rep, "warning"), ["spacing"])
        self.assertEqual(checks(rep, "error"), ["length"])
        self.assertIn("over by", rep.blocking[0]["message"])

    def test_length_counts_like_textlen(self):
        rep = run(None, "가족의 비밀", "ko-ko", gl=[], opts={"limit": 6})
        self.assertEqual(rep.findings, [])

    def test_untranslated(self):
        self.assertEqual(checks(run("안녕하세요", "", gl=[]), "error"), ["untranslated"])


class TestCLI(unittest.TestCase):
    def setUp(self):
        self.tmp = pathlib.Path(tempfile.mkdtemp())
        (self.tmp / "glossary.md").write_text(GLOSSARY, encoding="utf-8")

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def write(self, name, text):
        p = self.tmp / name
        p.write_text(text, encoding="utf-8")
        return str(p)

    def cli(self, *args):
        return subprocess.run([sys.executable, "-I", str(SCRIPT), *args], capture_output=True, text=True)

    def test_pass_writes_reports(self):
        s = self.write("s.txt", "계약서를 2026년 10월 16일까지 {0}에게 보내 주십시오.\n금액은 1억 2천만 원입니다.\n")
        t = self.write("t.txt", "Please send the agreement to {0} by October 16, 2026.\nThe amount is KRW 120 million.\n")
        r = self.cli("--source", s, "--target", t, "--by-line", "--glossary", str(self.tmp / "glossary.md"),
                     "--json", str(self.tmp / "r.json"), "--md", str(self.tmp / "r.md"))
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        data = json.loads((self.tmp / "r.json").read_text(encoding="utf-8"))
        self.assertEqual(data["summary"]["result"], "PASS")
        self.assertEqual(data["summary"]["segments"], 2)
        self.assertEqual(data["summary"]["direction"], "ko-en")
        self.assertIn("**PASS**", (self.tmp / "r.md").read_text(encoding="utf-8"))

    def test_fail_exit_1_and_json_stdout(self):
        p = self.write("p.tsv", "1\t계약서 3부\tthree copies of the contract\n2\t<b>담당자</b>\t<b>Contact\n")
        r = self.cli("--pairs", p, "--glossary", str(self.tmp / "glossary.md"), "--json", "-")
        self.assertEqual(r.returncode, 1, r.stderr)
        data = json.loads(r.stdout)
        got = {(f["segment"], f["check"], f["severity"]) for f in data["findings"]}
        self.assertIn(("1", "glossary", "error"), got)
        self.assertIn(("2", "tags", "error"), got)
        self.assertIn(("2", "glossary", "warning"), got)
        self.assertNotIn(("1", "numbers", "error"), got)  # "three" satisfies 3

    def test_alignment_mismatch(self):
        s = self.write("s.txt", "하나\n둘\n")
        t = self.write("t.txt", "one\n")
        r = self.cli("--source", s, "--target", t, "--by-line", "--json", "-")
        self.assertEqual(r.returncode, 1)
        self.assertEqual(json.loads(r.stdout)["findings"][0]["check"], "alignment")

    def test_target_only_synopsis_mode(self):
        t = self.write("d.txt", "열여섯 살 소녀가 가족의 비밀을 파헤친다.")
        r = self.cli("--target", t, "--limit", "110", "--forbid", "충격", "--json", "-")
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertNotIn("numbers", json.loads(r.stdout)["summary"]["checks"])

    def test_usage_errors(self):
        self.assertEqual(self.cli().returncode, 2)
        t = self.write("t.txt", "x")
        self.assertEqual(self.cli("--target", t, "--glossary", str(self.tmp / "missing.md")).returncode, 2)


class TestPofilter(unittest.TestCase):
    def test_not_installed_is_skipped(self):
        rep = qa.Report()
        with mock.patch.object(qa.shutil, "which", return_value=None):
            status = qa.run_pofilter("job.xlf", "ko", rep)
        self.assertIn("not installed", status)
        self.assertEqual(rep.findings, [])

    def test_findings_parsed_from_filtered_output(self):
        def fake_run(cmd, **kw):
            pathlib.Path(cmd[-1]).write_text(
                '# (pofilter) numbers: Different numbers\nmsgid "3 files"\nmsgstr "파일"\n'
                '<note from="pofilter">xmltags: Different XML tags</note>\n', encoding="utf-8")
            calls.append(cmd)
            return subprocess.CompletedProcess(cmd, 0, "", "")
        calls, rep = [], qa.Report()
        with mock.patch.object(qa.subprocess, "run", side_effect=fake_run):
            status = qa.run_pofilter("job.po", "ko", rep, exe="/usr/bin/pofilter")
        self.assertIn("2 finding", status)
        self.assertEqual([f["check"] for f in rep.blocking], ["pofilter", "pofilter"])
        self.assertIn("--language=ko", calls[0])
        self.assertIn("xmltags", calls[0])


if __name__ == "__main__":
    unittest.main()
