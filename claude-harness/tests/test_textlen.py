import importlib.util
import pathlib
import subprocess
import sys
import unittest

ROOT = pathlib.Path(__file__).resolve().parent.parent
SCRIPT = ROOT / "scripts" / "textlen.py"
spec = importlib.util.spec_from_file_location("textlen", SCRIPT)
textlen = importlib.util.module_from_spec(spec)
spec.loader.exec_module(textlen)


class TestTextLen(unittest.TestCase):
    def test_korean_syllables_count_once(self):
        m = textlen.measure("가족의 비밀")
        self.assertEqual(m["chars"], 6)
        self.assertEqual(m["chars_nospace"], 5)
        self.assertEqual(m["words"], 2)

    def test_decomposed_jamo_normalised(self):
        import unicodedata
        nfd = unicodedata.normalize("NFD", "한국")
        self.assertEqual(textlen.measure(nfd)["chars"], 2)

    def test_whitespace_collapsed(self):
        self.assertEqual(textlen.measure("  a\n\n b  ")["chars"], 3)

    def test_cli_limit_exit_codes(self):
        ok = subprocess.run([sys.executable, "-I", str(SCRIPT), "--limit", "10"],
                            input="짧은 글", capture_output=True, text=True)
        self.assertEqual(ok.returncode, 0)
        self.assertIn("OK", ok.stdout)
        over = subprocess.run([sys.executable, "-I", str(SCRIPT), "--limit", "3"],
                              input="너무 긴 시놉시스", capture_output=True, text=True)
        self.assertEqual(over.returncode, 1)
        self.assertIn("OVER by", over.stdout)


if __name__ == "__main__":
    unittest.main()
