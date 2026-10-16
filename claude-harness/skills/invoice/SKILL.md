---
name: invoice
description: Prepare a freelance invoice for translation or annotation work (per source word, per Korean character incl. spaces, per hour, per item/task, or flat), with minimum fee, rush surcharge, KRW/USD with an explicit exchange rate, and Korean 3.3% withholding; log it in the finance ledger and track payment and overdue invoices. Never sends. Use when the user asks to bill a client, make an invoice, mark one paid, or check what is overdue.
argument-hint: "<client/project, or: paid INV-..., overdue>"
---

# Invoice

Request: $ARGUMENTS

Script: `python3 -I ${CLAUDE_PLUGIN_ROOT}/scripts/invoice.py <command>`. It writes a Markdown invoice and appends to `$HARNESS_DATA/finance/ledger.csv`. **It never sends, emails or uploads; neither do you.** The user sends the invoice.

## 1. Gather terms (ask once, only for what is unclear)
Reuse the project `CLAUDE.md`, `SPEC.md`, the client's purchase order or earlier invoices for this client before asking. Settle:
- **Unit and rate** per line: `per_word` (source words), `per_char` (Korean characters **including spaces**), `per_hour`, `per_item` (tasks, files, pages), or `flat`.
- **Quantity.** Count from the source file rather than trusting a number someone typed: `invoice.py count <file> --unit per_word|per_char` or `count_from` in the spec. Hours come from the user or her time log; say where they came from.
- **Minimum fee** and **rush surcharge %**, if the agreement has them.
- **Currency.** If the rates are in USD and the invoice is in KRW (or vice versa), the user gives the **exchange rate, its date and its source** (e.g. her bank's 매매기준율). Never look one up silently; if she asks you to look one up, show her the figure and source and get a yes first.
- **Withholding.** `true` when a Korean payer withholds 3.3% 사업소득세 from her fee (typical for Korean agencies paying an individual), `false` for foreign clients or when the client is billed with a tax invoice instead. Required for KRW invoices; ask if unknown.
- **Issue date and due date** (or payment terms in days; default 30).

## 2. Write the spec and compute
Save as `admin/invoices/<number-or-date>_<client>.json` in the project:
```json
{
  "client": "Acme Localization", "project": "Manual KO→EN", "currency": "KRW",
  "rate_currency": "USD", "fx": {"rate": "1385.20", "as_of": "2026-10-15", "source": "Hana Bank 매매기준율"},
  "items": [
    {"desc": "Translation KO→EN", "unit": "per_char", "count_from": "../../work/source.txt", "rate": "0.08"},
    {"desc": "Terminology call", "unit": "per_hour", "qty": "1.5", "rate": "40"}
  ],
  "minimum_fee": "50", "rush_pct": "25", "withholding": true,
  "issued": "2026-10-16", "terms_days": 30,
  "from": "<name, contact>", "to": "<client billing contact>", "payment": "<bank, account>"
}
```
Write numbers as strings so nothing goes through float. Run `invoice.py make <spec> --dry-run` first and show the user the breakdown.

Calculation order (documented in the script header): lines (qty × rate, rounded half-up) → minimum fee top-up → rush surcharge → currency conversion with the given rate (half-up to whole won / cent) → withholding → net payable.

**Withholding rule.** 소득세 = 3% of gross, truncated to 10 won; 지방소득세 = 10% of that income tax, truncated to 10 won. The 1,000-won small-amount exemption is not applied. Example: gross ₩1,234,567 → 37,030 + 3,700 = ₩40,730 withheld, net ₩1,193,837. These rules are common practice, not tax advice. Say **"verify with your accountant"** whenever the withholding figure matters. `--wht-unit 1` truncates to 1 won if her accountant says so.

## 3. Issue
1. `invoice.py make <spec> --out deliverables/YYYY-MM-DD_<client>_invoice_<number>.md`. The script picks the next number `INV-YYYY-NNN` from the ledger and refuses duplicates.
2. Check the Markdown yourself: client name spelled as in the contract, quantities match the counted files, the rate and FX source are on the page, due date right. Then `verify` with those checks.
3. Hand the file to the user. If she wants PDF or DOCX, convert locally (document skills); don't upload.
4. Append a `task` event with `intent` (what is being billed), `situation` (agreement, PO, deadline) and `meta` (`kind_of_thing: invoice`, unit and rate used, anything unusual such as a rush or a minimum).

## 4. Track payment
- She sent it: `invoice.py status INV-2026-007 sent --on 2026-10-16`.
- Money arrived: `invoice.py status INV-2026-007 paid --on 2026-11-10 [--amount 1193837]`; part of it: `partial --amount ...`. Check the received amount against `total` (net of withholding) and flag differences (bank fees, wrong withholding).
- `invoice.py list [--status issued]` shows current state. `invoice.py --today YYYY-MM-DD overdue` lists unpaid invoices past due, oldest first, with outstanding totals per currency. Use it in `review-week`.
- For an overdue invoice, offer to **draft** a polite reminder (register `formal-email`). Don't send it.

The ledger is append-only: fix a mistake by adding a `status` row (`void`, then re-issue), never by editing old rows.
