import importlib.util
import pathlib
import shutil
import subprocess
import sys
import tempfile
import unittest

ROOT = pathlib.Path(__file__).resolve().parent.parent
SCRIPT = ROOT / "scripts" / "claim_check.py"
spec = importlib.util.spec_from_file_location("claim_check", SCRIPT)
cc = importlib.util.module_from_spec(spec)
spec.loader.exec_module(cc)

FACTS = """# Master facts
- Freelance KO-EN translator since 2019, 120+ projects for game and legal clients.
- Annotated 5,000 Korean dialogue samples for an LLM evaluation project at DataCo (2024).
- MA in Translation, Hankuk University of Foreign Studies, 2018.
- 계약서 번역 및 법률 문서 검수 경험 3년
- Tools: Trados Studio, memoQ, Python
"""


def verdicts(draft):
    return {r["claim"]: r["verdict"] for r in cc.check(draft, FACTS)["results"]}


class TestClaimCheck(unittest.TestCase):
    def test_supported_paraphrase(self):
        v = verdicts("I have worked as a freelance KO-EN translator since 2019 on 120+ projects.")
        self.assertEqual(list(v.values()), ["supported"])

    def test_invented_claim_unsupported(self):
        v = verdicts("I led a team of 12 engineers at Google.")
        self.assertEqual(list(v.values()), ["unsupported"])

    def test_wrong_number_blocks_even_with_overlap(self):
        r = cc.check("I hold an MA in Translation from Hankuk University of Foreign Studies, earned in 2016.",
                     FACTS)["results"][0]
        self.assertEqual(r["verdict"], "unsupported")
        self.assertEqual(r["missing_numbers"], ["2016"])
        self.assertEqual(r["fact_lines"], "4")

    def test_number_with_thousands_separator(self):
        v = verdicts("Annotated 5000 Korean dialogue samples for an LLM evaluation project.")
        self.assertEqual(list(v.values()), ["supported"])

    def test_korean_bigrams_and_particles(self):
        v = verdicts("저는 3년간 계약서를 번역하고 법률 문서를 검수했습니다.")
        self.assertEqual(list(v.values()), ["supported"])
        v = verdicts("저는 의료기기 인허가 문서를 10년 동안 번역했습니다.")
        self.assertEqual(list(v.values()), ["unsupported"])

    def test_tokens(self):
        t = cc.tokens("계약서를 Trados 2019")
        self.assertIn("계약", t)
        self.assertIn("약서", t)
        self.assertNotIn("서를", t)
        self.assertIn("trados", t)
        self.assertIn("#2019", t)

    def test_courtesy_and_fragments_skipped(self):
        rep = cc.check("Dear Hiring Manager,\n\nSincerely,\nJiwon\n감사합니다.", FACTS)
        self.assertEqual(rep["results"], [])
        self.assertEqual(len(rep["skipped"]), 4)

    def test_adjacent_lines_window(self):
        facts = "Senior translator, Acme Corp\n- Managed glossary of 3,000 legal terms\n"
        r = cc.check("At Acme Corp I managed a glossary of 3,000 legal terms.", facts)["results"][0]
        self.assertEqual(r["verdict"], "supported")
        self.assertEqual(r["fact_lines"], "1-2")

    def test_cli_exit_codes(self):
        d = pathlib.Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, d)
        (d / "facts.md").write_text(FACTS, encoding="utf-8")
        ok = subprocess.run([sys.executable, "-I", str(SCRIPT), "-", "--facts", str(d / "facts.md")],
                            input="- Tools I use daily: Trados Studio, memoQ and Python.\n",
                            capture_output=True, text=True)
        self.assertEqual(ok.returncode, 0, ok.stdout + ok.stderr)
        bad = subprocess.run([sys.executable, "-I", str(SCRIPT), "-", "--facts", str(d / "facts.md"), "--json"],
                             input="I won the national translation award in 2021.\n",
                             capture_output=True, text=True)
        self.assertEqual(bad.returncode, 1)
        self.assertIn('"unsupported": 1', bad.stdout)


if __name__ == "__main__":
    unittest.main()
