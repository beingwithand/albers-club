#!/usr/bin/env python3
"""Weekly summary of the event log, per scope, as Markdown (BLUEPRINT.md §4.5, §4.13; librarian review).

    python3 -I scripts/weekly_report.py                       # last 7 days, to stdout
    python3 -I scripts/weekly_report.py --from 2026-10-01 --to 2026-10-07 --out report.md

Reads $HARNESS_DATA/log/*.jsonl (append-only). Label events (`type: label`, `labels_for: <id>`) written by
scripts/label_events.py are folded into the events they label; the newest label for an id wins.

Per scope it reports: events, prompts, sessions, corrections (type `correction` or labeled
`is_correction`), correction rate (corrections / prompts), mishaps, decisions, verifications with
pass / fail / needs-human and pass rate, cost (sum of cost_usd), and how many candidate events are
still unlabeled.

Scope resolution: the event's own `scope`; else the label's `scope`; else the first path component
of `scope_hint` (the cwd) that is an ontology area, plus the next component as project (e.g.
`.../translation/acme-contract/work` -> `translation/acme-contract`); else `unscoped`.

Stdlib only. Run with `python3 -I`. Exit 0 on success, 2 on usage error.
"""
import argparse
import datetime as dt
import json
import os
import pathlib
import re
import sys
from collections import defaultdict

FALLBACK_AREAS = ["translation", "annotation", "job-search", "art", "code", "research", "personal"]
NEEDS_LABEL_TYPES = {"prompt", "decision", "correction", "mishap", "session_note"}
VERDICT_ALIASES = {
    "pass": "pass", "passed": "pass", "ok": "pass", "worked": "pass",
    "fail": "fail", "failed": "fail", "reverted": "fail",
    "needs-human": "needs-human", "needs_human": "needs-human", "needs human": "needs-human",
}


def data_dir(arg):
    if arg:
        return pathlib.Path(arg).expanduser()
    return pathlib.Path(os.environ.get("HARNESS_DATA", pathlib.Path.home() / "harness-data"))


def load_areas(ontology_path):
    """Read `areas: [...]` from schema/ontology.yaml without a YAML parser; fall back to defaults."""
    try:
        text = pathlib.Path(ontology_path).read_text(encoding="utf-8")
    except OSError:
        return list(FALLBACK_AREAS)
    m = re.search(r"^areas:\s*\[([^\]]*)\]", text, re.M)
    if not m:
        return list(FALLBACK_AREAS)
    areas = [a.strip().strip("'\"") for a in m.group(1).split(",") if a.strip()]
    return areas or list(FALLBACK_AREAS)


def parse_date(s):
    try:
        return dt.date.fromisoformat(s)
    except ValueError:
        raise argparse.ArgumentTypeError(f"not a YYYY-MM-DD date: {s!r}")


def event_date(ev):
    ts = ev.get("ts")
    if not isinstance(ts, str):
        return None
    try:
        t = dt.datetime.fromisoformat(ts.replace("Z", "+00:00"))
    except ValueError:
        return None
    if t.tzinfo is not None:
        t = t.astimezone(dt.timezone.utc)
    return t.date()


def read_events(log_dir):
    events, bad = [], 0
    for path in sorted(pathlib.Path(log_dir).glob("*.jsonl")):
        with open(path, encoding="utf-8", errors="replace") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    ev = json.loads(line)
                except json.JSONDecodeError:
                    bad += 1
                    continue
                if isinstance(ev, dict):
                    events.append(ev)
                else:
                    bad += 1
    return events, bad


def scope_from_hint(hint, areas):
    if not isinstance(hint, str) or not hint:
        return None
    parts = [p for p in re.split(r"[\\/]+", hint) if p]
    for i, p in enumerate(parts):
        if p in areas:
            return f"{p}/{parts[i + 1]}" if i + 1 < len(parts) else p
    return None


def verdict_of(ev):
    for key in ("verdict", "outcome", "result"):
        v = ev.get(key)
        if isinstance(v, str) and v.strip().lower() in VERDICT_ALIASES:
            return VERDICT_ALIASES[v.strip().lower()]
    for lab in ev.get("labels") or []:
        if isinstance(lab, str) and lab.lower() in VERDICT_ALIASES:
            return VERDICT_ALIASES[lab.lower()]
    return "unknown"


def summarize(events, start, end, areas):
    """Return (per-scope stats dict, totals dict, mishap list)."""
    labels = {}
    for ev in events:  # file order is chronological; later labels overwrite earlier ones
        if ev.get("type") == "label" and ev.get("labels_for"):
            labels[ev["labels_for"]] = ev

    def new():
        return {"events": 0, "prompts": 0, "sessions": set(), "corrections": 0, "mishaps": 0,
                "decisions": 0, "verifications": 0, "pass": 0, "fail": 0, "needs-human": 0,
                "unknown_verdict": 0, "cost": 0.0, "unlabeled": 0}

    stats = defaultdict(new)
    mishaps = []
    for ev in events:
        t = ev.get("type")
        if t == "label":
            continue
        d = event_date(ev)
        if d is None or not (start <= d <= end):
            continue
        lab = labels.get(ev.get("id"))
        scope = (ev.get("scope") or (lab or {}).get("scope")
                 or scope_from_hint(ev.get("scope_hint"), areas) or "unscoped")
        s = stats[scope]
        s["events"] += 1
        if ev.get("session_id"):
            s["sessions"].add(ev["session_id"])
        if t == "prompt":
            s["prompts"] += 1
        if t == "correction" or (lab and lab.get("is_correction") is True):
            s["corrections"] += 1
        if t == "mishap":
            s["mishaps"] += 1
            mishaps.append((scope, ev.get("id"), ev.get("content") or ev.get("intent") or ""))
        if t == "decision":
            s["decisions"] += 1
        if t == "verification":
            s["verifications"] += 1
            v = verdict_of(ev)
            s["unknown_verdict" if v == "unknown" else v] += 1
        c = ev.get("cost_usd")
        if isinstance(c, (int, float)) and not isinstance(c, bool):
            s["cost"] += float(c)
        if t in NEEDS_LABEL_TYPES and lab is None and (
                t == "prompt" or any(not ev.get(k) for k in ("intent", "situation", "meta"))):
            s["unlabeled"] += 1

    totals = new()
    for s in stats.values():
        for k, v in s.items():
            if k == "sessions":
                totals[k] |= v
            else:
                totals[k] += v
    return dict(stats), totals, mishaps


def pct(n, d):
    return "n/a" if not d else f"{100.0 * n / d:.0f}%"


def row(name, s):
    judged = s["pass"] + s["fail"] + s["needs-human"]
    return (f"| {name} | {s['events']} | {s['prompts']} | {len(s['sessions'])} | {s['corrections']} | "
            f"{pct(s['corrections'], s['prompts'])} | {s['mishaps']} | {s['decisions']} | "
            f"{s['verifications']} | {s['pass']}/{s['fail']}/{s['needs-human']} | {pct(s['pass'], judged)} | "
            f"${s['cost']:.2f} | {s['unlabeled']} |")


def render(stats, totals, mishaps, start, end, bad_lines=0):
    out = [f"# Weekly harness report: {start} to {end}", ""]
    if not stats:
        out += ["No events in this range.", ""]
        return "\n".join(out)
    out += [
        "| scope | events | prompts | sessions | corrections | correction rate | mishaps | decisions "
        "| verifications | pass/fail/human | pass rate | cost | unlabeled |",
        "|---|---|---|---|---|---|---|---|---|---|---|---|---|",
    ]
    for name in sorted(stats, key=lambda k: (-stats[k]["events"], k)):
        out.append(row(name, stats[name]))
    out.append(row("**total**", totals))
    out.append("")
    out.append("Pass rate = pass / (pass + fail + needs-human). Correction rate = corrections / prompts.")
    out.append("")
    if mishaps:
        out.append("## Mishaps this period")
        for scope, eid, text in mishaps:
            text = " ".join(str(text).split())
            out.append(f"- `{eid}` ({scope}): {text[:120]}{'…' if len(text) > 120 else ''}")
        out.append("")
    notes = []
    if totals["unlabeled"]:
        notes.append(f"{totals['unlabeled']} events are unlabeled; run `python3 -I scripts/label_events.py` "
                     "before drawing conclusions about corrections.")
    if totals["unknown_verdict"]:
        notes.append(f"{totals['unknown_verdict']} verification events have no recognisable verdict field.")
    if bad_lines:
        notes.append(f"{bad_lines} log lines were not valid JSON and were skipped.")
    if notes:
        out.append("## Notes")
        out += [f"- {n}" for n in notes]
        out.append("")
    return "\n".join(out)


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__.split("\n\n")[0],
                                formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--data-dir", help="defaults to $HARNESS_DATA or ~/harness-data")
    p.add_argument("--from", dest="from_", type=parse_date, help="start date YYYY-MM-DD (default: --to minus 6 days)")
    p.add_argument("--to", type=parse_date, help="end date YYYY-MM-DD, inclusive (default: today UTC)")
    p.add_argument("--ontology", help="path to ontology.yaml (default: ../schema/ontology.yaml next to this script)")
    p.add_argument("--out", help="write the markdown here instead of stdout")
    args = p.parse_args(argv)

    end = args.to or dt.datetime.now(dt.timezone.utc).date()
    start = args.from_ or end - dt.timedelta(days=6)
    if start > end:
        p.error("--from is after --to")
    ontology = args.ontology or pathlib.Path(__file__).resolve().parent.parent / "schema" / "ontology.yaml"
    areas = load_areas(ontology)
    log_dir = data_dir(args.data_dir) / "log"
    events, bad = read_events(log_dir) if log_dir.is_dir() else ([], 0)
    stats, totals, mishaps = summarize(events, start, end, areas)
    md = render(stats, totals, mishaps, start, end, bad)
    if args.out:
        out = pathlib.Path(args.out).expanduser()
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(md, encoding="utf-8")
        print(f"wrote {out}")
    else:
        sys.stdout.write(md)
    return 0


if __name__ == "__main__":
    sys.exit(main())
