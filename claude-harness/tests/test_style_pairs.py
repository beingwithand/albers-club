"""Tests for scripts/style_pairs.py. Run from the harness root:
    python3 -I -m unittest tests.test_style_pairs
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
SCRIPT = ROOT / "scripts" / "style_pairs.py"
sys.dont_write_bytecode = True  # keep scripts/ free of __pycache__
_spec = importlib.util.spec_from_file_location("style_pairs", SCRIPT)
sp = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(sp)


def pair(**kw):
    base = {"draft": "draft text", "final": "final text", "language": "en",
            "direction": "none", "register": "office", "domain": "general", "audience": "team"}
    base.update(kw)
    return base


class Base(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.file = pathlib.Path(self.tmp.name) / "style" / "pairs.jsonl"

    def tearDown(self):
        self.tmp.cleanup()


class TestRegisters(unittest.TestCase):
    def test_reads_ontology_list(self):
        regs = sp.load_registers()
        self.assertIn("formal-email", regs)
        self.assertIn("annotation-response", regs)
        self.assertEqual(len(regs), 6)

    def test_block_style_list(self):
        with tempfile.TemporaryDirectory() as d:
            p = pathlib.Path(d) / "o.yaml"
            p.write_text("version: 1\nregisters:\n  - chat\n  - office  # note\n", encoding="utf-8")
            self.assertEqual(sp.load_registers(p), ["chat", "office"])


class TestAdd(Base):
    def test_add_korean_pair_roundtrip(self):
        rec = sp.add(pair(draft="검토 부탁드립니다.", final="검토해 주시면 감사하겠습니다.",
                          language="ko", direction="en-ko", register="formal email",
                          reasoning="하십시오체보다 부드럽게"), self.file)
        self.assertTrue(rec["id"].startswith("sp_"))
        self.assertEqual(rec["direction"], "en→ko")
        self.assertEqual(rec["register"], "formal-email")
        self.assertTrue(rec["edited"])
        line = self.file.read_text(encoding="utf-8").strip()
        self.assertIn("검토해 주시면", line)  # stored as UTF-8, not \u escapes
        self.assertEqual(sp.load(self.file)[0]["reasoning"], "하십시오체보다 부드럽게")

    def test_unedited_pair_flagged(self):
        rec = sp.add(pair(draft="Same.", final="Same. "), self.file)
        self.assertFalse(rec["edited"])

    def test_rejects_bad_register(self):
        with self.assertRaises(sp.ValidationError):
            sp.add(pair(register="poetry"), self.file)
        self.assertFalse(self.file.exists())

    def test_rejects_bad_direction_and_language(self):
        with self.assertRaises(sp.ValidationError):
            sp.add(pair(direction="ko→ja"), self.file)
        with self.assertRaises(sp.ValidationError):
            sp.add(pair(language="jp"), self.file)

    def test_rejects_empty_text(self):
        with self.assertRaises(sp.ValidationError):
            sp.add(pair(final="   "), self.file)

    def test_direction_aliases(self):
        for alias in ("ko→en", "ko->en", "KO-EN", "ko2en"):
            self.assertEqual(sp.norm_direction(alias), "ko→en")

    def test_supersedes_hides_old(self):
        old = sp.add(pair(final="v1"), self.file)
        sp.add(pair(final="v2", supersedes=old["id"]), self.file)
        finals = [p["final"] for p in sp.load(self.file)]
        self.assertEqual(finals, ["v2"])


class TestTokens(unittest.TestCase):
    def test_korean_bigrams(self):
        self.assertEqual(sp.tokens("계약서"), {"계약", "약서"})
        self.assertEqual(sp.tokens("값"), {"값"})

    def test_mixed_text(self):
        t = sp.tokens("NDA 계약서를 review해 주세요")
        self.assertTrue({"nda", "review", "계약", "약서", "서를", "주세", "세요"} <= t)

    def test_korean_similarity_handles_particles(self):
        # Same noun with different particles still overlaps via bigrams.
        self.assertGreater(sp.similarity("계약서를 검토", "계약서가 검토됨"), 0.3)
        self.assertEqual(sp.similarity("계약서", "날씨"), 0.0)
        self.assertEqual(sp.similarity("", "anything"), 0.0)


class TestNearest(Base):
    def setUp(self):
        super().setUp()
        sp.add(pair(draft="날씨가 좋네", final="날씨 좋다 ㅋㅋ", language="ko", register="chat"), self.file)
        sp.add(pair(source="계약서 검토 요청", draft="Please review the contract.",
                    final="Could you please review the attached contract?",
                    direction="ko-en", register="formal-email", domain="legal"), self.file)
        sp.add(pair(source="회의록 공유드립니다", draft="Sharing the minutes.",
                    final="Please find the meeting minutes attached.",
                    direction="ko-en", register="formal-email", domain="business"), self.file)
        sp.add(pair(source="계약서 수정본", draft="Revised contract", final="Revised agreement",
                    direction="ko-en", register="client-deliverable", domain="legal"), self.file)
        self.pairs = sp.load(self.file)

    def test_register_ranks_first(self):
        res = sp.nearest(self.pairs, register="formal email", direction="ko→en", k=2)
        self.assertEqual({r["register"] for r in res}, {"formal-email"})

    def test_domain_then_korean_similarity(self):
        res = sp.nearest(self.pairs, register="formal-email", direction="ko-en",
                         domain="legal", text="계약서를 검토해 주세요", k=3)
        self.assertEqual(res[0]["domain"], "legal")
        self.assertEqual(res[0]["register"], "formal-email")
        self.assertEqual(res[1]["domain"], "business")

    def test_similarity_breaks_ties_without_filters(self):
        res = sp.nearest(self.pairs, text="계약서 수정", k=1)
        self.assertEqual(res[0]["final"], "Revised agreement")

    def test_k_and_empty(self):
        self.assertEqual(len(sp.nearest(self.pairs, k=2)), 2)
        self.assertEqual(sp.nearest([], register="chat"), [])


class TestStats(Base):
    def test_counts(self):
        sp.add(pair(register="chat", language="ko", reasoning="반말"), self.file)
        sp.add(pair(register="chat"), self.file)
        sp.add(pair(register="office", direction="en→ko", draft="x", final="x"), self.file)
        st = sp.stats(sp.load(self.file))
        self.assertEqual(st["total"], 3)
        self.assertEqual(st["edited"], 2)
        self.assertEqual(st["with_reasoning"], 1)
        self.assertEqual(st["by_register"], {"chat": 2, "office": 1})
        self.assertEqual(st["by_direction"]["en→ko"], 1)
        self.assertEqual(st["by_language"], {"en": 2, "ko": 1})

    def test_empty_and_malformed(self):
        self.assertEqual(sp.stats(sp.load(self.file))["total"], 0)
        self.file.parent.mkdir(parents=True)
        self.file.write_text('{"id": "a", "register": "chat"}\nnot json\n', encoding="utf-8")
        with redirect_stderr(io.StringIO()) as err:
            self.assertEqual(sp.stats(sp.load(self.file))["total"], 1)
        self.assertIn("malformed", err.getvalue())


class TestCLI(Base):
    def run_cli(self, *args, stdin=None):
        return subprocess.run([sys.executable, "-I", str(SCRIPT), "--file", str(self.file), *args],
                              input=stdin, capture_output=True, text=True, encoding="utf-8")

    def test_add_nearest_stats_cli(self):
        r = self.run_cli("add", "--json", "-", stdin=json.dumps(pair(
            draft="확인했습니다", final="확인했어요!", language="ko", register="friendly"), ensure_ascii=False))
        self.assertEqual(r.returncode, 0, r.stderr)
        r = self.run_cli("nearest", "--register", "friendly", "--text", "확인 부탁", "-k", "1")
        self.assertEqual(json.loads(r.stdout)["final"], "확인했어요!")
        r = self.run_cli("stats", "--json")
        self.assertEqual(json.loads(r.stdout)["total"], 1)

    def test_cli_rejects_invalid(self):
        r = self.run_cli("add", "--draft", "a", "--final", "b", "--language", "en", "--register", "nope")
        self.assertEqual(r.returncode, 2)
        self.assertIn("register", r.stderr)

    def test_main_inprocess(self):
        with redirect_stdout(io.StringIO()) as out:
            code = sp.main(["--file", str(self.file), "stats"])
        self.assertEqual(code, 0)
        self.assertIn("total 0", out.getvalue())


if __name__ == "__main__":
    unittest.main()
