#!/usr/bin/env python3
"""Accept or reject a candidate policy change by comparing eval results (BLUEPRINT.md §0.5 step 4).

A rule, skill, prompt or routing edit is merged only if the eval set does not get worse.

    python3 -I scripts/eval_gate.py BASELINE.json CANDIDATE.json [--tolerance DIM=VALUE ...] [--json]

Input format: see evals/README.md ("Result file format"). Each file has `tasks: {task_id: {locked,
scores: {dimension: number}, checks: {check_id: bool}}}` (a list of objects with an `id` also works).

REJECT if any of:
  - a dimension's mean (over tasks scored in both runs) regresses beyond its tolerance;
  - `correctness` drops on any locked task (beyond a tiny float epsilon);
  - a check on a locked task passed in the baseline and fails in the candidate;
  - a baseline task is missing from the candidate (unless --allow-missing);
  - the runs used different eval sets (`eval_set` or `eval_set_sha256` differ);
  - either run used the same model as producer and judge (self-evaluation skews positive).

Tolerances: `DIM=0.1` is absolute (score units); `DIM=10%` is relative to the baseline mean.
Defaults: correctness=0, style_match=0.1, outcome=0.05, correction_rate=0.02, cost=10%, time=15%,
other dimensions 0. Higher is better for correctness/style_match/outcome; lower is better for
correction_rate/cost/time (override with --lower-is-better DIM).

Exit codes: 0 accept, 1 reject, 2 usage/input error. The printed report is the justification to paste
into the commit/PR.
"""
import argparse
import json
import math
import sys

EPS = 1e-9
LOWER_IS_BETTER = {"correction_rate", "cost", "time"}
DEFAULT_TOLERANCE = {
    "correctness": (0.0, False),
    "style_match": (0.1, False),
    "outcome": (0.05, False),
    "correction_rate": (0.02, False),
    "cost": (0.10, True),
    "time": (0.15, True),
}


class InputError(Exception):
    pass


def load(path):
    try:
        with open(path, encoding="utf-8") as f:
            data = json.load(f)
    except OSError as e:
        raise InputError(f"cannot read {path}: {e}")
    except json.JSONDecodeError as e:
        raise InputError(f"{path} is not valid JSON: {e}")
    if not isinstance(data, dict):
        raise InputError(f"{path}: top level must be an object")
    tasks = data.get("tasks")
    if isinstance(tasks, list):
        conv = {}
        for t in tasks:
            if not isinstance(t, dict) or "id" not in t:
                raise InputError(f"{path}: every task in the list needs an 'id'")
            conv[str(t["id"])] = t
        tasks = conv
    if not isinstance(tasks, dict) or not tasks:
        raise InputError(f"{path}: 'tasks' must be a non-empty object or list")
    for tid, t in tasks.items():
        if not isinstance(t, dict) or not isinstance(t.get("scores", {}), dict):
            raise InputError(f"{path}: task {tid} must be an object with a 'scores' object")
    data["tasks"] = tasks
    return data


def num(v):
    if isinstance(v, bool) or not isinstance(v, (int, float)) or math.isnan(v) or math.isinf(v):
        return None
    return float(v)


def parse_tolerance(spec):
    if "=" not in spec:
        raise argparse.ArgumentTypeError(f"expected DIM=VALUE or DIM=VALUE%, got {spec!r}")
    dim, val = spec.split("=", 1)
    rel = val.endswith("%")
    try:
        x = float(val[:-1] if rel else val)
    except ValueError:
        raise argparse.ArgumentTypeError(f"bad tolerance value in {spec!r}")
    if x < 0:
        raise argparse.ArgumentTypeError("tolerance must be >= 0")
    return dim.strip(), (x / 100.0 if rel else x, rel)


def mean(xs):
    return sum(xs) / len(xs) if xs else None


def fmt(x):
    return "n/a" if x is None else f"{x:.4g}"


def evaluate(base, cand, tolerances=None, lower_is_better=None, allow_missing=False):
    """Return a dict: decision ('accept'|'reject'), reasons, notes, per-dimension table."""
    tol = dict(DEFAULT_TOLERANCE)
    tol.update(tolerances or {})
    lower = set(LOWER_IS_BETTER) | set(lower_is_better or ())
    reasons, notes = [], []

    # Run validity
    for label, run in (("baseline", base), ("candidate", cand)):
        pm, jm = run.get("producer_model"), run.get("judge_model")
        if pm and jm and str(pm).strip().lower() == str(jm).strip().lower():
            reasons.append(f"{label}: judge model '{jm}' equals producer model; scores are self-evaluation")
        elif not (pm and jm):
            notes.append(f"{label}: producer_model/judge_model not recorded; cannot confirm they differ")
    for key in ("eval_set", "eval_set_sha256"):
        b, c = base.get(key), cand.get(key)
        if b is not None and c is not None and b != c:
            reasons.append(f"{key} differs (baseline {b!r}, candidate {c!r}); re-run the baseline on the same set")

    bt, ct = base["tasks"], cand["tasks"]
    missing = sorted(set(bt) - set(ct))
    extra = sorted(set(ct) - set(bt))
    if missing:
        msg = f"{len(missing)} baseline task(s) missing from candidate: {', '.join(missing[:10])}"
        (notes if allow_missing else reasons).append(msg)
    if extra:
        notes.append(f"{len(extra)} candidate-only task(s) ignored: {', '.join(extra[:10])}")
    common = sorted(set(bt) & set(ct))
    if not common:
        reasons.append("no tasks in common")

    # Locked-task checks
    locked_drops = []
    for tid in common:
        b, c = bt[tid], ct[tid]
        locked = bool(b.get("locked")) or bool(c.get("locked"))
        if bool(b.get("locked")) != bool(c.get("locked")):
            notes.append(f"{tid}: 'locked' differs between runs; treated as locked")
        if not locked:
            continue
        bc = num(b.get("scores", {}).get("correctness"))
        cc = num(c.get("scores", {}).get("correctness"))
        if bc is not None and cc is None:
            reasons.append(f"locked task {tid}: correctness missing in candidate")
        elif bc is not None and cc < bc - EPS:
            locked_drops.append(tid)
            reasons.append(f"locked task {tid}: correctness dropped {fmt(bc)} -> {fmt(cc)}")
        bchk, cchk = b.get("checks") or {}, c.get("checks") or {}
        for chk, passed in bchk.items():
            if passed is True and cchk.get(chk) is not True:
                state = "missing" if chk not in cchk else "failed"
                reasons.append(f"locked task {tid}: check '{chk}' passed in baseline, {state} in candidate")

    # Per-dimension means over tasks scored in both runs
    dims = sorted({d for tid in common for d in bt[tid].get("scores", {})}
                  | {d for tid in common for d in ct[tid].get("scores", {})})
    table = []
    for d in dims:
        pairs = [(num(bt[t].get("scores", {}).get(d)), num(ct[t].get("scores", {}).get(d))) for t in common]
        pairs = [(x, y) for x, y in pairs if x is not None and y is not None]
        row = {"dimension": d, "n": len(pairs), "direction": "lower" if d in lower else "higher"}
        if not pairs:
            row.update(baseline=None, candidate=None, delta=None, allowed=None, status="skipped")
            notes.append(f"dimension {d}: no task scored in both runs; skipped")
            table.append(row)
            continue
        bm, cm = mean([x for x, _ in pairs]), mean([y for _, y in pairs])
        t_val, rel = tol.get(d, (0.0, False))
        allowed = t_val * abs(bm) if rel else t_val
        worse_by = (cm - bm) if d in lower else (bm - cm)
        status = "regressed" if worse_by > allowed + EPS else ("improved" if worse_by < -EPS else "same")
        row.update(baseline=bm, candidate=cm, delta=cm - bm, allowed=allowed,
                   tolerance=(f"{t_val * 100:g}%" if rel else f"{t_val:g}"), status=status)
        if status == "regressed":
            reasons.append(f"dimension {d} regressed: mean {fmt(bm)} -> {fmt(cm)} "
                           f"({'lower' if d in lower else 'higher'} is better; allowed {fmt(allowed)})")
        table.append(row)

    return {
        "decision": "reject" if reasons else "accept",
        "reasons": reasons,
        "notes": notes,
        "dimensions": table,
        "tasks_compared": len(common),
        "locked_tasks": sum(1 for t in common if bt[t].get("locked") or ct[t].get("locked")),
        "locked_correctness_drops": locked_drops,
        "baseline_policy": base.get("policy"),
        "candidate_policy": cand.get("policy"),
        "eval_set": cand.get("eval_set") or base.get("eval_set"),
    }


def report(res):
    lines = [
        f"# Eval gate: {res['decision'].upper()}",
        "",
        f"- eval set: {res['eval_set'] or 'unnamed'}",
        f"- baseline policy: {res['baseline_policy'] or 'unknown'}; candidate policy: {res['candidate_policy'] or 'unknown'}",
        f"- tasks compared: {res['tasks_compared']} (locked: {res['locked_tasks']})",
        "",
        "| dimension | better | n | baseline | candidate | delta | tolerance | status |",
        "|---|---|---|---|---|---|---|---|",
    ]
    for r in res["dimensions"]:
        lines.append(f"| {r['dimension']} | {r['direction']} | {r['n']} | {fmt(r['baseline'])} | "
                     f"{fmt(r['candidate'])} | {fmt(r['delta'])} | {r.get('tolerance', 'n/a')} | {r['status']} |")
    lines.append("")
    if res["reasons"]:
        lines.append("## Reasons for rejection")
        lines += [f"- {x}" for x in res["reasons"]]
    else:
        improved = [r["dimension"] for r in res["dimensions"] if r["status"] == "improved"]
        lines.append("## Justification")
        lines.append("- No dimension regressed beyond tolerance; no locked task lost correctness or a passing check.")
        if improved:
            lines.append(f"- Improved: {', '.join(improved)}.")
    if res["notes"]:
        lines += ["", "## Notes"] + [f"- {x}" for x in res["notes"]]
    return "\n".join(lines) + "\n"


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__.split("\n\n")[0],
                                formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("baseline")
    p.add_argument("candidate")
    p.add_argument("--tolerance", action="append", type=parse_tolerance, default=[],
                   metavar="DIM=VALUE[%]", help="override a dimension's tolerance (repeatable)")
    p.add_argument("--lower-is-better", action="append", default=[], metavar="DIM",
                   help="treat an extra dimension as lower-is-better (repeatable)")
    p.add_argument("--allow-missing", action="store_true", help="do not reject when candidate lacks some tasks")
    p.add_argument("--json", action="store_true", help="print the decision as JSON instead of markdown")
    args = p.parse_args(argv)
    try:
        base, cand = load(args.baseline), load(args.candidate)
    except InputError as e:
        print(f"error: {e}", file=sys.stderr)
        return 2
    res = evaluate(base, cand, dict(args.tolerance), args.lower_is_better, args.allow_missing)
    sys.stdout.write(json.dumps(res, indent=2, ensure_ascii=False) + "\n" if args.json else report(res))
    return 0 if res["decision"] == "accept" else 1


if __name__ == "__main__":
    sys.exit(main())
