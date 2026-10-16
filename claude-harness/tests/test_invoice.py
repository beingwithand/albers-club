import contextlib
import csv
import datetime
import importlib.util
import io
import json
import pathlib
import shutil
import subprocess
import sys
import tempfile
import unittest
from decimal import Decimal as D

ROOT = pathlib.Path(__file__).resolve().parent.parent
SCRIPT = ROOT / "scripts" / "invoice.py"
spec = importlib.util.spec_from_file_location("invoice", SCRIPT)
invoice = importlib.util.module_from_spec(spec)
spec.loader.exec_module(invoice)


def run(argv):
    out, err = io.StringIO(), io.StringIO()
    with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
        code = invoice.main(argv)
    return code, out.getvalue(), err.getvalue()


class TestWithholding(unittest.TestCase):
    def test_truncates_to_10_won(self):
        # 1,234,567 x 3% = 37,037.01 -> 37,030; 10% of that = 3,703 -> 3,700
        self.assertEqual(invoice.withholding_krw(D("1234567")), (D("37030"), D("3700"), D("40730")))

    def test_round_amount(self):
        self.assertEqual(invoice.withholding_krw(D("1000000")), (D("30000"), D("3000"), D("33000")))

    def test_local_tax_based_on_truncated_income_tax(self):
        # 12,345 x 3% = 370.35 -> 370; 37 -> 30
        self.assertEqual(invoice.withholding_krw(D("12345")), (D("370"), D("30"), D("400")))

    def test_small_amount_not_exempted_but_truncated(self):
        self.assertEqual(invoice.withholding_krw(D("99")), (D("0"), D("0"), D("0")))
        self.assertEqual(invoice.withholding_krw(D("30000")), (D("900"), D("90"), D("990")))

    def test_one_won_unit(self):
        self.assertEqual(invoice.withholding_krw(D("1234567"), D("1")), (D("37037"), D("3703"), D("40740")))

    def test_never_rounds_up(self):
        for gross in (D("333333"), D("999999"), D("1666666"), D("7")):
            inc, loc, tot = invoice.withholding_krw(gross)
            self.assertLessEqual(inc, gross * D("0.03"))
            self.assertLessEqual(loc, inc * D("0.1"))
            self.assertEqual(inc % 10, 0)
            self.assertEqual(loc % 10, 0)


class TestCompute(unittest.TestCase):
    def base(self, **kw):
        s = {"client": "Acme", "currency": "KRW", "withholding": True,
             "items": [{"desc": "KO→EN", "unit": "per_char", "qty": "10000", "rate": "50"}]}
        s.update(kw)
        return s

    def test_simple_krw(self):
        b = invoice.compute(self.base())
        self.assertEqual(b["subtotal"], D("500000"))
        self.assertEqual(b["withholding"]["total"], D("16500"))
        self.assertEqual(b["total"], D("483500"))

    def test_minimum_then_rush(self):
        b = invoice.compute(self.base(items=[{"unit": "per_word", "qty": 100, "rate": "120"}],
                                      minimum_fee="30000", rush_pct="25"))
        self.assertEqual(b["base"], D("12000"))
        self.assertEqual(b["minimum_adjustment"], D("18000"))
        self.assertEqual(b["rush"], D("7500"))
        self.assertEqual(b["subtotal"], D("37500"))
        self.assertEqual(b["withholding"]["total"], D("1230"))   # 1125 -> 1120; 112 -> 110

    def test_no_minimum_when_above(self):
        b = invoice.compute(self.base(minimum_fee="1000"))
        self.assertEqual(b["minimum_adjustment"], 0)

    def test_usd_cents_half_up(self):
        b = invoice.compute({"client": "X", "currency": "USD", "items": [
            {"unit": "per_word", "qty": 1234, "rate": "0.085"},     # 104.89
            {"unit": "per_hour", "qty": "1.5", "rate": "33.33"},    # 49.995 -> 50.00
            {"unit": "flat", "rate": "10"}]})
        self.assertEqual([ln["amount"] for ln in b["lines"]], [D("104.89"), D("50.00"), D("10.00")])
        self.assertEqual(b["total"], D("164.89"))
        self.assertFalse(b["withholding"]["applied"])

    def test_fx_explicit(self):
        b = invoice.compute(self.base(rate_currency="USD",
                                      items=[{"unit": "per_item", "qty": 3, "rate": "100.50"}],
                                      fx={"rate": "1385.25", "as_of": "2026-10-15", "source": "bank"}))
        self.assertEqual(b["subtotal_rate_currency"], D("301.50"))
        self.assertEqual(b["subtotal"], D("417653"))    # 417,652.875 -> half-up
        self.assertEqual(b["withholding"]["total"], D("13770"))  # 12529.59->12520; 1252->1250

    def test_fx_required_and_never_fetched(self):
        with self.assertRaisesRegex(invoice.InvoiceError, "explicit"):
            invoice.compute(self.base(rate_currency="USD"))
        with self.assertRaisesRegex(invoice.InvoiceError, "as_of"):
            invoice.compute(self.base(rate_currency="USD", fx={"rate": "1300"}))

    def test_fx_override_from_cli(self):
        b = invoice.compute(self.base(rate_currency="USD", items=[{"unit": "flat", "rate": "100"}]),
                            fx_override={"rate": "1300", "as_of": "2026-10-16", "source": "user"})
        self.assertEqual(b["subtotal"], D("130000"))

    def test_fx_given_for_same_currency_rejected(self):
        with self.assertRaises(invoice.InvoiceError):
            invoice.compute(self.base(fx={"rate": "1300", "as_of": "x", "source": "y"}))

    def test_krw_needs_explicit_withholding(self):
        s = self.base()
        del s["withholding"]
        with self.assertRaisesRegex(invoice.InvoiceError, "withholding"):
            invoice.compute(s)

    def test_withholding_only_krw(self):
        with self.assertRaises(invoice.InvoiceError):
            invoice.compute({"client": "X", "currency": "USD", "withholding": True,
                             "items": [{"unit": "flat", "rate": "1"}]})

    def test_validation(self):
        with self.assertRaises(invoice.InvoiceError):
            invoice.compute(self.base(items=[{"unit": "flat", "qty": 2, "rate": "1"}]))
        with self.assertRaises(invoice.InvoiceError):
            invoice.compute(self.base(items=[{"unit": "per_word", "qty": "10.5", "rate": "1"}]))
        with self.assertRaises(invoice.InvoiceError):
            invoice.compute(self.base(items=[{"unit": "per_page", "qty": 1, "rate": "1"}]))
        with self.assertRaises(invoice.InvoiceError):
            invoice.compute(self.base(currency="EUR"))

    def test_count_from_file(self):
        d = pathlib.Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, d)
        (d / "src.txt").write_text("가족의  비밀\n", encoding="utf-8")
        b = invoice.compute(self.base(items=[{"unit": "per_char", "count_from": "src.txt", "rate": "100"}]),
                            base_dir=d)
        self.assertEqual(b["lines"][0]["qty"], 6)
        self.assertEqual(invoice.count_text("one two  three", "per_word"), 3)


class TestLedgerCLI(unittest.TestCase):
    def setUp(self):
        self.d = pathlib.Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, self.d)
        self.ledger = str(self.d / "finance" / "ledger.csv")
        self.spec = self.d / "spec.json"
        self.spec.write_text(json.dumps({
            "client": "Acme", "project": "Manual", "currency": "KRW", "withholding": True,
            "issued": "2026-09-01", "terms_days": 14,
            "items": [{"desc": "Translation", "unit": "per_char", "qty": "20000", "rate": "61.7283"}]}),
            encoding="utf-8")

    def test_issue_number_status_overdue(self):
        out = str(self.d / "inv1.md")
        code, _, err = run(["--ledger", self.ledger, "make", str(self.spec), "--out", out])
        self.assertEqual(code, 0, err)
        md = pathlib.Path(out).read_text(encoding="utf-8")
        self.assertIn("# Invoice INV-2026-001", md)
        self.assertIn("₩1,234,566", md)
        self.assertIn("Net payable", md)
        self.assertIn("Not sent", err)

        code, _, _ = run(["--ledger", self.ledger, "make", str(self.spec), "--out", str(self.d / "inv2.md")])
        self.assertEqual(code, 0)
        code, _, err = run(["--ledger", self.ledger, "make", str(self.spec), "--number", "INV-2026-001"])
        self.assertEqual(code, 2)
        self.assertIn("already", err)
        self.assertEqual(run(["--ledger", self.ledger, "--today", "2026-10-01", "number"])[1].strip(), "INV-2026-003")

        run(["--ledger", self.ledger, "status", "INV-2026-001", "paid", "--on", "2026-09-10"])
        code, out_s, _ = run(["--ledger", self.ledger, "--today", "2026-10-01", "overdue"])
        self.assertNotIn("INV-2026-001", out_s)
        self.assertIn("INV-2026-002", out_s)
        self.assertIn("16 days", out_s)

        run(["--ledger", self.ledger, "status", "INV-2026-002", "partial", "--amount", "1000000"])
        rows = invoice.read_ledger(self.ledger)
        state = invoice.fold(rows)
        self.assertEqual(state["INV-2026-002"]["status"], "partial")
        late = invoice.overdue(rows, datetime.date(2026, 10, 1))
        self.assertEqual(late[0]["outstanding"], D(state["INV-2026-002"]["total"]) - D("1000000"))
        with open(self.ledger, newline="", encoding="utf-8") as f:
            self.assertEqual(next(csv.reader(f)), invoice.LEDGER_FIELDS)

    def test_dry_run_leaves_ledger_alone(self):
        code, out, err = run(["--ledger", self.ledger, "make", str(self.spec), "--dry-run"])
        self.assertEqual(code, 0)
        self.assertIn("dry-run", err)
        self.assertFalse(pathlib.Path(self.ledger).exists())

    def test_status_unknown_invoice(self):
        self.assertEqual(run(["--ledger", self.ledger, "status", "INV-2026-099", "paid"])[0], 2)

    def test_runs_isolated(self):
        p = subprocess.run([sys.executable, "-I", str(SCRIPT), "count", "-", "--unit", "per_char"],
                           input="한국 문학", capture_output=True, text=True)
        self.assertEqual(p.returncode, 0, p.stderr)
        self.assertEqual(p.stdout.strip(), "5")


if __name__ == "__main__":
    unittest.main()
