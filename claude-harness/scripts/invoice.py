#!/usr/bin/env python3
"""Freelance invoices for translation and annotation work: compute, number, ledger, track payment.

Run with `python3 -I scripts/invoice.py <command>` (stdlib only). Never sends anything: it writes a
Markdown invoice and appends to a CSV ledger; the user sends the invoice herself.

Commands
  count    FILE --unit per_word|per_char      Billable quantity of a source file.
  number   [--year YYYY]                      Next free invoice number (INV-YYYY-NNN) from the ledger.
  make     SPEC.json [--out FILE.md]          Compute the invoice, write Markdown, append an `issued`
           [--dry-run] [--fx-rate R --fx-date D --fx-source S]   row to the ledger (not with --dry-run).
  status   ID STATUS [--on DATE] [--amount X] [--note TEXT]      Append a payment-status change.
  list     [--status S]                       Current state of every invoice (ledger folded by id).
  overdue  [--today DATE]                     Unpaid invoices past their due date, oldest first.

Ledger: $HARNESS_DATA/finance/ledger.csv (default ~/harness-data/finance/ledger.csv; --ledger overrides).
Append-only: a status change is a new row; the current status is the last row for that id.

Calculation order (every step uses Decimal, never float)
  1. Line amount = qty x rate, rounded half-up to the rate currency's unit (KRW 1 won, USD 1 cent).
  2. Base subtotal = sum of lines. If below `minimum_fee`, a "minimum fee adjustment" line tops it up.
  3. Rush surcharge = subtotal x rush_pct / 100, rounded half-up as in step 1.
  4. If `rate_currency` differs from `currency`, convert with the exchange rate **given in the spec or
     on the command line** (1 rate_currency = R currency), rounded half-up. Rates are never fetched;
     a missing rate is an error. The rate, its date and its source are printed on the invoice.
  5. Korean withholding on 사업소득 (KRW invoices only, `withholding: true`):
       소득세 (income tax)   = 3% of the gross amount, truncated to 10 won
       지방소득세 (local tax) = 10% of the income tax,   truncated to 10 won   (= 0.3% of gross)
     Truncation below 10 won follows 국고금관리법 §47 (끝수 계산 생략), the common payroll practice.
     The 1,000-won small-amount exemption (소액부징수) is NOT applied: since 2024-07 it excludes
     ongoing personal-service business income, which freelance translation usually is.
     --> VERIFY WITH AN ACCOUNTANT before relying on these rules; `--wht-unit 1` truncates to 1 won.
  Net payable (`total`) = gross subtotal - withholding. VAT is not computed (freelance personal
  services are usually VAT-exempt; check your own status).
"""
import argparse
import csv
import datetime
import importlib.util
import json
import os
import pathlib
import re
import sys
from decimal import Decimal, ROUND_DOWN, ROUND_HALF_UP, InvalidOperation

HARNESS_ROOT = pathlib.Path(__file__).resolve().parent.parent

CURRENCY_UNIT = {"KRW": Decimal("1"), "USD": Decimal("0.01")}
UNITS = ("per_word", "per_char", "per_hour", "per_item", "flat")
_UNIT_ALIASES = {
    "per_word": "per_word", "word": "per_word", "per_source_word": "per_word", "words": "per_word",
    "per_char": "per_char", "char": "per_char", "per_ko_char": "per_char", "chars": "per_char",
    "글자": "per_char", "자": "per_char",
    "per_hour": "per_hour", "hour": "per_hour", "hourly": "per_hour", "hours": "per_hour",
    "per_item": "per_item", "item": "per_item", "per_task": "per_item", "task": "per_item", "items": "per_item",
    "flat": "flat", "fixed": "flat",
}
UNIT_LABEL = {"per_word": "source words", "per_char": "chars (incl. spaces)", "per_hour": "hours",
              "per_item": "items", "flat": "flat"}
STATUSES = ("issued", "sent", "partial", "paid", "disputed", "void")
CLOSED = ("paid", "void")
INCOME_TAX_RATE = Decimal("0.03")
LOCAL_TAX_SHARE = Decimal("0.10")
LEDGER_FIELDS = ["ts", "event", "invoice_id", "client", "project", "currency", "subtotal", "withholding",
                 "total", "issued", "due", "status", "amount", "on", "fx", "note"]
NUMBER_RE = re.compile(r"^INV-(\d{4})-(\d{3,})$")


class InvoiceError(ValueError):
    pass


# ---------------------------------------------------------------- helpers

def dec(value, what):
    if isinstance(value, float):
        value = repr(value)
    try:
        d = Decimal(str(value).replace(",", "").strip())
    except (InvalidOperation, AttributeError):
        raise InvoiceError(f"{what}: {value!r} is not a number")
    if not d.is_finite():
        raise InvoiceError(f"{what}: {value!r} is not a finite number")
    return d


def currency_of(code, what="currency"):
    c = (code or "").strip().upper()
    if c not in CURRENCY_UNIT:
        raise InvoiceError(f"{what} {code!r} not one of {', '.join(CURRENCY_UNIT)}")
    return c


def money(amount, currency):
    return amount.quantize(CURRENCY_UNIT[currency], rounding=ROUND_HALF_UP)


def fmt(amount, currency):
    if currency == "KRW":
        return f"₩{amount:,.0f}"
    return f"${amount:,.2f}"


def parse_date(value, what):
    if isinstance(value, datetime.date):
        return value
    try:
        return datetime.date.fromisoformat(str(value).strip())
    except ValueError:
        raise InvoiceError(f"{what}: {value!r} is not a YYYY-MM-DD date")


def norm_unit(value):
    key = str(value or "").strip().lower().replace("-", "_").replace(" ", "_")
    if key not in _UNIT_ALIASES:
        raise InvoiceError(f"unit {value!r} not one of {', '.join(UNITS)}")
    return _UNIT_ALIASES[key]


def _textlen():
    spec = importlib.util.spec_from_file_location("textlen", HARNESS_ROOT / "scripts" / "textlen.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def count_text(text, unit):
    """per_word: whitespace-separated source words. per_char: NFC code points including spaces,
    with leading/trailing whitespace dropped and internal whitespace runs counted as one space
    (same rule as scripts/textlen.py, i.e. what Word/HWP show as 공백 포함 글자 수 for one paragraph)."""
    m = _textlen().measure(text)
    unit = norm_unit(unit)
    if unit == "per_word":
        return m["words"]
    if unit == "per_char":
        return m["chars"]
    raise InvoiceError(f"cannot count a file in unit {unit}")


def truncate(amount, unit):
    return (amount / unit).to_integral_value(rounding=ROUND_DOWN) * unit


def withholding_krw(gross, unit=Decimal("10")):
    """Korean 3.3% withholding on business income. gross is whole won. Returns (income, local, total)."""
    gross = dec(gross, "gross")
    if gross < 0:
        raise InvoiceError("gross amount is negative")
    unit = dec(unit, "withholding truncation unit")
    income = truncate(gross * INCOME_TAX_RATE, unit)
    local = truncate(income * LOCAL_TAX_SHARE, unit)
    return income, local, income + local


# ---------------------------------------------------------------- compute

def compute(spec, base_dir=None, fx_override=None, wht_unit=Decimal("10")):
    """Return a breakdown dict for an invoice spec. Pure: no files written."""
    if not isinstance(spec, dict):
        raise InvoiceError("spec must be a JSON object")
    client = str(spec.get("client") or "").strip()
    if not client:
        raise InvoiceError("client is required")
    currency = currency_of(spec.get("currency"))
    rate_ccy = currency_of(spec.get("rate_currency") or currency, "rate_currency")
    items = spec.get("items") or []
    if not items:
        raise InvoiceError("at least one item is required")

    lines = []
    for i, it in enumerate(items, 1):
        if not isinstance(it, dict):
            raise InvoiceError(f"item {i} must be an object")
        unit = norm_unit(it.get("unit"))
        if "count_from" in it and "qty" not in it:
            p = pathlib.Path(it["count_from"])
            if base_dir and not p.is_absolute():
                p = pathlib.Path(base_dir) / p
            qty = Decimal(count_text(p.read_text(encoding="utf-8"), unit))
        elif unit == "flat":
            qty = dec(it.get("qty", 1), f"item {i} qty")
        else:
            if "qty" not in it:
                raise InvoiceError(f"item {i}: qty (or count_from) is required")
            qty = dec(it["qty"], f"item {i} qty")
        if unit == "flat" and qty != 1:
            raise InvoiceError(f"item {i}: flat items have qty 1")
        if unit in ("per_word", "per_char", "per_item") and qty != qty.to_integral_value():
            raise InvoiceError(f"item {i}: {unit} qty must be a whole number")
        if qty < 0:
            raise InvoiceError(f"item {i}: qty is negative")
        rate = dec(it.get("rate"), f"item {i} rate")
        if rate < 0:
            raise InvoiceError(f"item {i}: rate is negative")
        lines.append({"desc": str(it.get("desc") or it.get("description") or f"Item {i}"),
                      "unit": unit, "qty": qty, "rate": rate, "amount": money(qty * rate, rate_ccy)})

    base = sum((ln["amount"] for ln in lines), Decimal(0))
    minimum = dec(spec.get("minimum_fee", 0), "minimum_fee")
    min_adj = money(minimum - base, rate_ccy) if minimum > base else Decimal(0)
    after_min = base + min_adj
    rush_pct = dec(spec.get("rush_pct", 0), "rush_pct")
    if rush_pct < 0:
        raise InvoiceError("rush_pct is negative")
    rush = money(after_min * rush_pct / 100, rate_ccy)
    subtotal_rate_ccy = after_min + rush

    fx = dict(spec.get("fx") or {})
    if fx_override:
        fx.update({k: v for k, v in fx_override.items() if v is not None})
    if rate_ccy != currency:
        if fx.get("rate") in (None, ""):
            raise InvoiceError(f"rates are in {rate_ccy} but the invoice is in {currency}: give an explicit "
                               f"exchange rate (spec fx.rate or --fx-rate); it is never fetched")
        fx_rate = dec(fx["rate"], "fx.rate")
        if fx_rate <= 0:
            raise InvoiceError("fx.rate must be positive")
        if not fx.get("as_of") or not fx.get("source"):
            raise InvoiceError("fx needs as_of (date) and source (where the rate came from)")
        subtotal = money(subtotal_rate_ccy * fx_rate, currency)
        fx_info = {"pair": f"{rate_ccy}/{currency}", "rate": fx_rate, "as_of": str(fx["as_of"]),
                   "source": str(fx["source"])}
    else:
        if fx.get("rate") not in (None, ""):
            raise InvoiceError("an exchange rate was given but rate_currency equals currency")
        subtotal = subtotal_rate_ccy
        fx_info = None

    wht = spec.get("withholding")
    if currency == "KRW" and not isinstance(wht, bool):
        raise InvoiceError("KRW invoice: set withholding to true or false explicitly "
                           "(true when a Korean payer withholds 3.3% 사업소득세)")
    if wht and currency != "KRW":
        raise InvoiceError("withholding is computed in KRW only; invoice in KRW with an explicit fx rate")
    if wht:
        income, local, wht_total = withholding_krw(subtotal, wht_unit)
    else:
        income = local = wht_total = Decimal(0)

    return {
        "client": client, "project": str(spec.get("project") or ""), "currency": currency,
        "rate_currency": rate_ccy, "lines": lines, "base": base, "minimum_fee": minimum,
        "minimum_adjustment": min_adj, "rush_pct": rush_pct, "rush": rush,
        "subtotal_rate_currency": subtotal_rate_ccy, "fx": fx_info, "subtotal": subtotal,
        "withholding": {"applied": bool(wht), "income_tax": income, "local_tax": local, "total": wht_total,
                        "truncate_unit": dec(wht_unit, "unit")},
        "total": subtotal - wht_total,
    }


# ---------------------------------------------------------------- ledger

def ledger_path(path=None):
    if path:
        return pathlib.Path(path)
    base = pathlib.Path(os.environ.get("HARNESS_DATA", pathlib.Path.home() / "harness-data"))
    return base / "finance" / "ledger.csv"


def read_ledger(path):
    path = pathlib.Path(path)
    if not path.exists():
        return []
    with open(path, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def append_ledger(path, row):
    path = pathlib.Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    new = not path.exists() or path.stat().st_size == 0
    with open(path, "a", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=LEDGER_FIELDS, extrasaction="ignore")
        if new:
            w.writeheader()
        w.writerow({k: ("" if row.get(k) is None else str(row.get(k))) for k in LEDGER_FIELDS})


def next_number(rows, year):
    n = 0
    for r in rows:
        m = NUMBER_RE.match(r.get("invoice_id") or "")
        if m and int(m.group(1)) == year:
            n = max(n, int(m.group(2)))
    return f"INV-{year}-{n + 1:03d}"


def fold(rows):
    """Current state per invoice id, in issue order."""
    state = {}
    for r in rows:
        iid = r.get("invoice_id")
        if not iid:
            continue
        if r.get("event") == "issued":
            state[iid] = dict(r, paid="0")
            continue
        if iid not in state:
            continue
        s = state[iid]
        s["status"] = r.get("status") or s["status"]
        if r.get("amount"):
            s["paid"] = str(dec(s["paid"], "paid") + dec(r["amount"], "amount"))
        if r.get("status") == "paid" and not r.get("amount"):
            s["paid"] = s["total"]
        if r.get("on"):
            s["last_on"] = r["on"]
    return state


def overdue(rows, today):
    out = []
    for s in fold(rows).values():
        if s["status"] in CLOSED or not s.get("due"):
            continue
        due = parse_date(s["due"], "due")
        if due < today:
            outstanding = dec(s["total"], "total") - dec(s["paid"], "paid")
            out.append(dict(s, days_overdue=(today - due).days, outstanding=outstanding))
    return sorted(out, key=lambda s: -s["days_overdue"])


# ---------------------------------------------------------------- markdown

def _qty(q):
    return f"{q:,.2f}".rstrip("0").rstrip(".") if q != q.to_integral_value() else f"{q:,.0f}"


def render_markdown(b, number, issued, due, spec):
    rc, cur = b["rate_currency"], b["currency"]
    out = [f"# Invoice {number}", "",
           f"- **Issued:** {issued}", f"- **Due:** {due}",
           f"- **Client:** {b['client']}"]
    if b["project"]:
        out.append(f"- **Project:** {b['project']}")
    for key, label in (("from", "From"), ("to", "Bill to")):
        if spec.get(key):
            out.append(f"- **{label}:** {spec[key]}")
    out += ["", "| # | Description | Unit | Qty | Rate | Amount |", "|---|---|---|---:|---:|---:|"]
    for i, ln in enumerate(b["lines"], 1):
        out.append(f"| {i} | {ln['desc']} | {UNIT_LABEL[ln['unit']]} | {_qty(ln['qty'])} | "
                   f"{ln['rate']:,} {rc} | {fmt(ln['amount'], rc)} |")
    if b["minimum_adjustment"]:
        out.append(f"| | Minimum fee adjustment (minimum {fmt(b['minimum_fee'], rc)}) | | | | "
                   f"{fmt(b['minimum_adjustment'], rc)} |")
    if b["rush"]:
        out.append(f"| | Rush surcharge {b['rush_pct']}% | | | | {fmt(b['rush'], rc)} |")
    out.append("")
    if b["fx"]:
        fx = b["fx"]
        out.append(f"Subtotal in {rc}: {fmt(b['subtotal_rate_currency'], rc)}  ")
        out.append(f"Exchange rate: 1 {rc} = {fx['rate']} {cur} ({fx['source']}, {fx['as_of']})  ")
    out.append(f"**Subtotal (gross): {fmt(b['subtotal'], cur)}**  ")
    w = b["withholding"]
    if w["applied"]:
        out.append(f"Less withholding 3.3% (사업소득 원천징수): {fmt(w['total'], cur)}  ")
        out.append(f"  - 소득세 3%: {fmt(w['income_tax'], cur)}  ")
        out.append(f"  - 지방소득세 0.3%: {fmt(w['local_tax'], cur)}  ")
    out.append(f"**Net payable: {fmt(b['total'], cur)}**")
    if spec.get("payment"):
        out += ["", f"**Payment details:** {spec['payment']}"]
    if spec.get("notes"):
        out += ["", str(spec["notes"])]
    if w["applied"]:
        out += ["", f"<!-- withholding: 3% income tax and 10% local tax on it, each truncated to "
                    f"{w['truncate_unit']} won. Verify with an accountant. -->"]
    return "\n".join(out) + "\n"


# ---------------------------------------------------------------- CLI

def _today(value):
    return parse_date(value, "--today") if value else datetime.date.today()


def cmd_count(args):
    text = sys.stdin.read() if args.file == "-" else open(args.file, encoding="utf-8").read()
    print(count_text(text, args.unit))
    return 0


def cmd_number(args):
    print(next_number(read_ledger(ledger_path(args.ledger)), args.year or _today(args.today).year))
    return 0


def cmd_make(args):
    src = pathlib.Path(args.spec)
    spec = json.loads((sys.stdin.read() if args.spec == "-" else src.read_text(encoding="utf-8")),
                      parse_float=Decimal)
    fx_override = {"rate": args.fx_rate, "as_of": args.fx_date, "source": args.fx_source}
    b = compute(spec, base_dir=None if args.spec == "-" else src.parent, fx_override=fx_override,
                wht_unit=dec(args.wht_unit, "--wht-unit"))
    lp = ledger_path(args.ledger)
    rows = read_ledger(lp)
    issued = parse_date(spec.get("issued") or _today(args.today).isoformat(), "issued")
    if spec.get("due"):
        due = parse_date(spec["due"], "due")
    else:
        due = issued + datetime.timedelta(days=int(spec.get("terms_days", 30)))
    if due < issued:
        raise InvoiceError("due date is before the issue date")
    number = args.number or spec.get("number") or next_number(rows, issued.year)
    if any(r.get("invoice_id") == number for r in rows):
        raise InvoiceError(f"invoice number {number} is already in the ledger")
    md = render_markdown(b, number, issued.isoformat(), due.isoformat(), spec)
    if args.out:
        pathlib.Path(args.out).parent.mkdir(parents=True, exist_ok=True)
        pathlib.Path(args.out).write_text(md, encoding="utf-8")
    else:
        sys.stdout.write(md)
    fx = b["fx"]
    row = {"ts": datetime.datetime.now(datetime.timezone.utc).isoformat(timespec="seconds"),
           "event": "issued", "invoice_id": number, "client": b["client"], "project": b["project"],
           "currency": b["currency"], "subtotal": b["subtotal"], "withholding": b["withholding"]["total"],
           "total": b["total"], "issued": issued.isoformat(), "due": due.isoformat(), "status": "issued",
           "fx": f"{fx['pair']}={fx['rate']}@{fx['as_of']}({fx['source']})" if fx else "",
           "note": args.note or ""}
    if args.dry_run:
        print(f"[dry-run] {number}: gross {fmt(b['subtotal'], b['currency'])}, withholding "
              f"{fmt(b['withholding']['total'], b['currency'])}, net {fmt(b['total'], b['currency'])}; "
              f"ledger not touched", file=sys.stderr)
    else:
        append_ledger(lp, row)
        print(f"{number}: net {fmt(b['total'], b['currency'])} due {due}; logged to {lp}. Not sent.",
              file=sys.stderr)
    return 0


def cmd_status(args):
    lp = ledger_path(args.ledger)
    state = fold(read_ledger(lp))
    if args.id not in state:
        raise InvoiceError(f"{args.id} is not in the ledger")
    if args.status == "partial" and not args.amount:
        raise InvoiceError("partial needs --amount")
    s = state[args.id]
    amount = money(dec(args.amount, "--amount"), s["currency"]) if args.amount else ""
    on = parse_date(args.on, "--on").isoformat() if args.on else _today(args.today).isoformat()
    append_ledger(lp, {"ts": datetime.datetime.now(datetime.timezone.utc).isoformat(timespec="seconds"),
                       "event": "status", "invoice_id": args.id, "client": s["client"],
                       "currency": s["currency"], "status": args.status, "amount": amount, "on": on,
                       "note": args.note or ""})
    print(f"{args.id}: {s['status']} -> {args.status}")
    return 0


def cmd_list(args):
    for s in fold(read_ledger(ledger_path(args.ledger))).values():
        if args.status and s["status"] != args.status:
            continue
        print(f"{s['invoice_id']}  {s['status']:<8} {s['client']}  net {s['total']} {s['currency']}  "
              f"paid {s['paid']}  due {s['due']}")
    return 0


def cmd_overdue(args):
    items = overdue(read_ledger(ledger_path(args.ledger)), _today(args.today))
    if not items:
        print("No overdue invoices.")
        return 0
    sums = {}
    for s in items:
        print(f"{s['invoice_id']}  {s['days_overdue']:>4} days  {s['client']}  "
              f"outstanding {fmt(s['outstanding'], s['currency'])}  (due {s['due']}, {s['status']})")
        sums[s["currency"]] = sums.get(s["currency"], Decimal(0)) + s["outstanding"]
    print("Total outstanding: " + ", ".join(fmt(v, k) for k, v in sorted(sums.items())))
    return 0


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--ledger", help="ledger CSV (default $HARNESS_DATA/finance/ledger.csv)")
    ap.add_argument("--today", help="override today's date (YYYY-MM-DD), for reports and tests")
    sub = ap.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("count")
    p.add_argument("file")
    p.add_argument("--unit", required=True, choices=("per_word", "per_char"))
    p.set_defaults(fn=cmd_count)
    p = sub.add_parser("number")
    p.add_argument("--year", type=int)
    p.set_defaults(fn=cmd_number)
    p = sub.add_parser("make")
    p.add_argument("spec", help="invoice spec JSON ('-' = stdin)")
    p.add_argument("--out", help="write the Markdown here (default stdout)")
    p.add_argument("--number", help="use this invoice number instead of the next free one")
    p.add_argument("--dry-run", action="store_true", help="compute and print; don't touch the ledger")
    p.add_argument("--fx-rate")
    p.add_argument("--fx-date")
    p.add_argument("--fx-source")
    p.add_argument("--wht-unit", default="10", choices=("10", "1"), help="withholding truncation unit in won")
    p.add_argument("--note")
    p.set_defaults(fn=cmd_make)
    p = sub.add_parser("status")
    p.add_argument("id")
    p.add_argument("status", choices=STATUSES[1:])
    p.add_argument("--on", help="date of the change (default today)")
    p.add_argument("--amount", help="amount received (partial/paid)")
    p.add_argument("--note")
    p.set_defaults(fn=cmd_status)
    p = sub.add_parser("list")
    p.add_argument("--status", choices=STATUSES)
    p.set_defaults(fn=cmd_list)
    p = sub.add_parser("overdue")
    p.set_defaults(fn=cmd_overdue)
    args = ap.parse_args(argv)
    try:
        return args.fn(args)
    except (InvoiceError, OSError, json.JSONDecodeError) as e:
        print(f"invoice: {e}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
