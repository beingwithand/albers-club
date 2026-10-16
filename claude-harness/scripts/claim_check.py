#!/usr/bin/env python3
"""Fact-check gate for CVs and cover letters: every claim in a draft must trace to the facts file.

Usage:
  python3 -I claim_check.py DRAFT --facts job-search/_master/facts.md [--threshold 0.5] [--json]

The facts file is the master CV / facts list: one fact per line (Markdown bullets are fine).
The draft is split into sentences and bullets. Courtesy lines ("Dear ...", "Sincerely",
"감사합니다") and fragments with fewer than --min-tokens content tokens are not claims.
Each claim is matched against every facts line and every pair of adjacent lines:

  tokens   Latin words (lower-cased, minus stop words), numbers, and Hangul character
           bigrams (after stripping a trailing particle, so "계약서를" matches "계약서").
  score    share of the claim's tokens found in the facts window (0..1).
  numbers  every number in the claim (years, %, counts, dates) must appear in that window.

Verdicts: supported (score >= threshold and all numbers found), weak (score >= threshold/2),
unsupported (anything else, or a number not in the facts). Exit code 1 if any claim is
unsupported, so the job-application skill can block on it; weak claims are for the user to judge.
Token overlap cannot prove a claim true; it only catches claims with no source line.
"""
import argparse
import json
import pathlib
import re
import sys
import unicodedata

_HANGUL = "가-힣"
_HANGUL_RUN = re.compile(rf"[{_HANGUL}]+")
_LATIN = re.compile(r"[^\W\d_]+", re.UNICODE)
_NUMBER = re.compile(r"\d+(?:[.,]\d+)*")
_SENT_SPLIT = re.compile(r"(?<=[.!?。])\s+|\n+")
_BULLET = re.compile(r"^\s*(?:[-*•·▪◦]|\d+[.)])\s+")

STOP = set("""a an the and or but of to in on at for with by from as is are was were be been being
i me my we our you your he she it they them their this that these those have has had do does did
will would can could should may might must shall not no so than then there here into onto over under
about also very more most such which who whom whose what when where why how all any each both
am its own just only per via""".split())
_PARTICLES = sorted("""을 를 이 가 은 는 의 에 에서 에게 께 으로 로 와 과 도 만 까지 부터 이며 이고 이나
으로서 로서 으로써 로써 에도 에는 과의 와의 하여 하고 했고 했으며 하였으며 했습니다 합니다 하였습니다
입니다 였습니다 이었습니다""".split(), key=len, reverse=True)

COURTESY = re.compile(
    r"^(dear\b|to whom|hello\b|hi\b|sincerely|best regards|kind regards|regards|yours\b|thank you|"
    r"thanks\b|안녕하십니까|안녕하세요|감사합니다|감사드립니다|고맙습니다|귀하|담당자님|드림|올림|"
    r"이력서|자기소개서|cover letter|curriculum vitae|resume)",
    re.IGNORECASE)


def _strip_particle(run):
    for p in _PARTICLES:
        if len(run) > len(p) + 1 and run.endswith(p):
            return run[: -len(p)]
    return run


def numbers(text):
    return {n.replace(",", "") for n in _NUMBER.findall(text)}


def tokens(text):
    text = unicodedata.normalize("NFC", text)
    toks = set()
    for w in _LATIN.findall(text):
        w = w.lower()
        if _HANGUL_RUN.fullmatch(w):
            continue
        if w not in STOP and len(w) > 1:
            toks.add(w)
    toks |= {"#" + n for n in numbers(text)}
    for run in _HANGUL_RUN.findall(text):
        run = _strip_particle(run)
        if len(run) == 1:
            toks.add(run)
        toks |= {run[i:i + 2] for i in range(len(run) - 1)}
    return toks


def split_claims(text, min_tokens=3):
    """Return (claims, skipped) as lists of strings."""
    claims, skipped = [], []
    for chunk in _SENT_SPLIT.split(unicodedata.normalize("NFC", text)):
        if not chunk:
            continue
        s = _BULLET.sub("", chunk).strip().strip("#").strip()
        if not s:
            continue
        if COURTESY.match(s) or len(tokens(s)) < min_tokens:
            skipped.append(s)
        else:
            claims.append(s)
    return claims, skipped


def load_facts(text):
    """Non-empty lines with their 1-based line numbers, bullets stripped."""
    out = []
    for i, line in enumerate(unicodedata.normalize("NFC", text).splitlines(), 1):
        s = _BULLET.sub("", line).strip().strip("#").strip()
        if s:
            out.append((i, s))
    return out


def _windows(facts):
    for k, (ln, s) in enumerate(facts):
        yield (ln, ln), s
        if k + 1 < len(facts):
            ln2, s2 = facts[k + 1]
            yield (ln, ln2), s + " " + s2


def check_claim(claim, facts, threshold=0.5):
    ct = tokens(claim)
    cn = numbers(claim)
    best, best_key = {"score": 0.0, "lines": None, "fact": "", "missing_numbers": sorted(cn)}, None
    for lines, text in _windows(facts):
        score = len(ct & tokens(text)) / len(ct) if ct else 0.0
        missing = sorted(cn - numbers(text))
        key = (score, -len(missing), lines[0] - lines[1])   # prefer single lines on ties
        if best_key is None or key > best_key:
            best, best_key = {"score": score, "lines": lines, "fact": text, "missing_numbers": missing}, key
    if best["score"] >= threshold and not best["missing_numbers"]:
        verdict = "supported"
    elif best["missing_numbers"] and best["score"] >= threshold / 2:
        verdict = "unsupported"
    elif best["score"] >= threshold / 2:
        verdict = "weak"
    else:
        verdict = "unsupported"
    lines = best["lines"]
    return {"claim": claim, "verdict": verdict, "score": round(best["score"], 3),
            "fact_lines": (f"{lines[0]}" if lines and lines[0] == lines[1] else f"{lines[0]}-{lines[1]}") if lines else None,
            "fact": best["fact"], "missing_numbers": best["missing_numbers"]}


def check(draft_text, facts_text, threshold=0.5, min_tokens=3):
    facts = load_facts(facts_text)
    claims, skipped = split_claims(draft_text, min_tokens)
    results = [check_claim(c, facts, threshold) for c in claims]
    return {"results": results, "skipped": skipped,
            "counts": {v: sum(r["verdict"] == v for r in results) for v in ("supported", "weak", "unsupported")}}


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("draft", help="CV or cover letter text/Markdown ('-' = stdin)")
    ap.add_argument("--facts", required=True, help="master CV / facts file, one fact per line")
    ap.add_argument("--threshold", type=float, default=0.5)
    ap.add_argument("--min-tokens", type=int, default=3)
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args(argv)
    draft = sys.stdin.read() if args.draft == "-" else pathlib.Path(args.draft).read_text(encoding="utf-8")
    facts = pathlib.Path(args.facts).read_text(encoding="utf-8")
    rep = check(draft, facts, args.threshold, args.min_tokens)
    if args.json:
        print(json.dumps(rep, ensure_ascii=False, indent=2))
    else:
        for r in rep["results"]:
            mark = {"supported": "OK  ", "weak": "WEAK", "unsupported": "FAIL"}[r["verdict"]]
            print(f"{mark} [{r['score']:.2f}] {r['claim']}")
            if r["verdict"] != "supported":
                print(f"       best facts line {r['fact_lines']}: {r['fact']}")
                if r["missing_numbers"]:
                    print(f"       numbers not in facts: {', '.join(r['missing_numbers'])}")
        c = rep["counts"]
        print(f"\n{c['supported']} supported, {c['weak']} weak, {c['unsupported']} unsupported; "
              f"{len(rep['skipped'])} non-claim lines skipped")
    return 1 if rep["counts"]["unsupported"] else 0


if __name__ == "__main__":
    sys.exit(main())
