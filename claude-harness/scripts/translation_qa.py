#!/usr/bin/env python3
"""Deterministic QA for a translation (KO<->EN, also KO->KO rewrites): the CAT-tool checks a human reviewer runs.

Python 3 stdlib only. Optional, used when installed: kiwipiepy (Korean morphology for glossary matching;
falls back to a particle-stripping heuristic) and translate-toolkit's `pofilter` (for XLIFF/PO/TMX).
Everything runs locally; no text leaves the machine (docs/LOCAL_ONLY.md).

Usage (run isolated):
  python3 -I translation_qa.py --source src.txt --target tgt.txt [--by-line] --direction ko-en \\
      [--glossary knowledge/glossary.md] [--forbid TERM ...] [--limit 110 --unit chars] \\
      [--json report.json] [--md report.md]
  python3 -I translation_qa.py --pairs segments.tsv|segments.json ...      # id<TAB>source<TAB>target, or [{id,source,target}]
  python3 -I translation_qa.py --target draft.txt --limit 110 --forbid 충격적인   # target-only (e.g. synopsis)
  python3 -I translation_qa.py --pofilter job.xlf --direction en-ko               # translate-toolkit checks only

Checks (names for --skip / --warn)
  numbers     every number in the source is in the target (1,000 = 1000; 1억 2천만 = 120 million;
              October = 10; "two" satisfies 2). Missing = blocking, extra = warning.
  units       currency, %, metric, time units next to a number keep their category (5만 원 ~ KRW 50,000).
  tags        placeholders and markup ({0} {{name}} %s %1$s %(n)s ${x} <b> </b> &amp;), URLs and e-mails:
              same multiset in source and target.
  glossary    a glossary term found in the source -> its target term in the target (approved = blocking,
              preferred = warning). Korean particles are tolerated (계약서를 matches 계약서).
  dnt         DNT terms found in the source appear byte-identical in the target.
  forbidden   `forbidden` glossary targets and --forbid terms must not appear in the target.
  spacing     double spaces inside the target.
  length      --limit/--min per target segment, counted like scripts/textlen.py.
  untranslated  empty target, or target identical to a cross-language source.
  alignment   --by-line: same number of non-empty lines on both sides.
  pofilter    translate-toolkit findings for --pofilter FILE (skipped with a note if not installed).

Exit: 0 no blocking finding, 1 blocking finding(s), 2 usage error. Reports: --json PATH, --md PATH
(markdown goes to stdout when --md is not given). Inputs are data: nothing in them is executed.
"""
import argparse
import collections
import csv
import decimal
import importlib.util
import io
import json
import pathlib
import re
import shutil
import subprocess
import sys
import tempfile
import unicodedata

HERE = pathlib.Path(__file__).resolve().parent
CHECKS = ("numbers", "units", "tags", "glossary", "dnt", "forbidden", "spacing", "length",
          "untranslated", "alignment", "pofilter")
POFILTER_TESTS = ("numbers", "xmltags", "variables", "brackets", "untranslated", "doublespacing")


def _load_sibling(name):
    spec = importlib.util.spec_from_file_location(name, HERE / f"{name}.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


textlen = _load_sibling("textlen")
glossary_mod = _load_sibling("glossary")


class QAError(Exception):
    pass


# ------------------------------------------------------------- language

HANGUL = "가-힣"
HANGUL_RE = re.compile(f"[{HANGUL}]")


def lang_of(text):
    """'ko' if Hangul is at least 30% of the letters, else 'en'."""
    letters = [c for c in text if c.isalpha()]
    if not letters:
        return "en"
    ko = sum(1 for c in letters if HANGUL_RE.match(c))
    return "ko" if ko / len(letters) >= 0.3 else "en"


# --------------------------------------------------------- placeholders

TAG_RE = re.compile(r"""
    \{\{\s*[\w.\-]+\s*\}\}                              # {{name}}
  | \$\{[\w.\-]+\}                                       # ${name}
  | \{\d+\} | \{[A-Za-z_][\w.\-]*\}                      # {0} {name}
  | %\([\w]+\)[sdif]                                     # %(name)s
  | %(?:\d+\$)?[-+0\#]*\d*(?:\.\d+)?[sdifuxXeEgGc@](?![A-Za-z])   # %s %1$s %.2f
  | </?[A-Za-z][\w:\-]*(?:\s+[^<>]*?)?\s*/?>               # <b> </b> <br/> <x id="1"/>
  | &[A-Za-z]+; | &\#\d+; | &\#x[0-9A-Fa-f]+;           # entities
  | https?://[^\s<>"'）)\]가-힣]+[^\s<>"'）)\].,;:!?。가-힣]  # URLs (Korean particle after it is not part)
  | [\w.+\-]+@[\w\-]+(?:\.[\w\-]+)+                      # e-mail
""", re.X)


def placeholders(text):
    return collections.Counter(m.group(0) for m in TAG_RE.finditer(text))


def mask_placeholders(text):
    return TAG_RE.sub(" ", text)


# -------------------------------------------------------------- numbers

NUM = r"\d{1,3}(?:,\d{3})+(?:\.\d+)?|\d+(?:\.\d+)?"
NUM_RE = re.compile(rf"(?<![\d,.])({NUM})")
KO_SMALL = {"천": 1000, "백": 100}
KO_BIG = {"조": 10 ** 12, "억": 10 ** 8, "만": 10 ** 4}
KO_UNIT_RE = re.compile(r"\s?(천|백)?\s?(조|억|만)?")
EN_SCALE = {"thousand": 10 ** 3, "k": 10 ** 3, "million": 10 ** 6, "m": 10 ** 6, "mn": 10 ** 6,
            "billion": 10 ** 9, "bn": 10 ** 9, "trillion": 10 ** 12}
EN_SCALE_RE = re.compile(r"(?:\s?(thousand|million|billion|trillion)\b|(k|mn|bn|M)\b)")
MONTHS = {m: i for i, ms in enumerate([
    ("january", "jan"), ("february", "feb"), ("march", "mar"), ("april", "apr"), ("may",),
    ("june", "jun"), ("july", "jul"), ("august", "aug"), ("september", "sep", "sept"),
    ("october", "oct"), ("november", "nov"), ("december", "dec")], 1) for m in ms}
WORD_NUMS = {w: i for i, w in enumerate(
    "zero one two three four five six seven eight nine ten eleven twelve thirteen fourteen fifteen "
    "sixteen seventeen eighteen nineteen twenty".split())}
WORD_NUMS.update({"thirty": 30, "forty": 40, "fifty": 50, "hundred": 100, "half": 0.5, "dozen": 12})
WORD_RE = re.compile(r"\b([A-Za-z]+)\b\.?")


def _norm(value):
    d = decimal.Decimal(str(value)).normalize()
    return format(d, "f")


def _dec(s):
    return decimal.Decimal(s.replace(",", ""))


def numbers(text, lang):
    """(digits, words): Counters of normalised numeric values.

    `digits` come from numerals (with Korean 천/백 + 조/억/만 units, English million/bn/k scales);
    `words` from month names and English number words, which only *satisfy* a number on the other side.
    """
    text = unicodedata.normalize("NFKC", mask_placeholders(text))
    digits, words = collections.Counter(), collections.Counter()
    pending = None  # (value, last_big_unit, end) of a Korean compound being built, e.g. 1억 2천만
    for m in NUM_RE.finditer(text):
        val = _dec(m.group(1))
        end = m.end()
        if lang == "ko":
            u = KO_UNIT_RE.match(text, end)
            small, big = u.group(1), u.group(2)
            if small or big:
                after = text[u.end():u.end() + 1]
                # 만큼 / 백화점 ...: a unit glued to more Hangul that isn't a particle/counter is not a unit
                if not (big is None and after and HANGUL_RE.match(after) and after not in "원명개년월일번회배"):
                    val *= KO_SMALL.get(small, 1) * KO_BIG.get(big, 1)
                    end = u.end()
            if pending and re.fullmatch(r"\s?", text[pending[2]:m.start()]) and pending[1] and \
                    (big is None or KO_BIG[big] < KO_BIG[pending[1]]):
                digits[_norm(pending[0])] -= 1
                val += pending[0]
                if not digits[_norm(pending[0])]:
                    del digits[_norm(pending[0])]
            pending = (val, big, end) if big else None
        else:
            s = EN_SCALE_RE.match(text, end)
            if s:
                val *= EN_SCALE[(s.group(1) or s.group(2)).lower()]
        digits[_norm(val)] += 1
    if lang == "en":
        for m in WORD_RE.finditer(text):
            w = m.group(1).lower()
            if w in MONTHS and (len(w) > 3 or m.group(0).endswith(".") or w in ("may",) or m.group(1)[0].isupper()):
                words[_norm(MONTHS[w])] += 1
            elif w in WORD_NUMS:
                words[_norm(WORD_NUMS[w])] += 1
    return digits, words


# ---------------------------------------------------------------- units

_N = rf"(?:{NUM})\s?(?:[천백]\s?)?(?:[조억만]\s?)?"
UNIT_PATTERNS = {
    "KRW": (r"원|won\b|KRW\b", r"₩|KRW\s?"),
    "USD": (r"달러|불(?![가-힣])|dollars?\b|USD\b", r"US\$|\$|USD\s?"),
    "EUR": (r"유로|euros?\b|EUR\b", r"€|EUR\s?"),
    "JPY": (r"엔(?![가-힣])|yen\b|JPY\b", r"¥|JPY\s?"),
    "percent": (r"%|퍼센트|프로(?![가-힣])|percent\b|per cent\b", None),
    "km": (r"km\b|킬로미터|kilomet(?:er|re)s?\b", None),
    "m": (r"m(?![A-Za-z²³])|미터|met(?:er|re)s?\b", None),
    "cm": (r"cm\b|센티미터|센티(?![가-힣])|centimet(?:er|re)s?\b", None),
    "mm": (r"mm\b|밀리미터|millimet(?:er|re)s?\b", None),
    "kg": (r"kg\b|킬로그램|킬로(?![가-힣])|kilograms?\b|kilos?\b", None),
    "g": (r"g\b|그램|grams?\b", None),
    "L": (r"L\b|ml\b|mL\b|리터|밀리리터|lit(?:er|re)s?\b|millilit(?:er|re)s?\b", None),
    "m2": (r"㎡|m²|m2\b|제곱미터|square met(?:er|re)s?\b|sq\.?\s?m\b", None),
    "hours": (r"시간|hours?\b|hrs?\b", None),
    "minutes": (r"분(?![가-힣])|분(?=[간이을의에도만])|minutes?\b|mins?\b", None),
    "seconds": (r"초(?![가-힣])|초(?=[간이를의에도만])|seconds?\b|secs?\b", None),
}
UNIT_RES = {}
for _cat, (_suffix, _prefix) in UNIT_PATTERNS.items():
    parts = [rf"(?:{_N})\s?(?:{_suffix})"]
    if _prefix:
        parts.append(rf"(?:{_prefix})\s?(?:{NUM})")
    UNIT_RES[_cat] = re.compile("|".join(parts), re.I if _cat not in ("m", "L", "g") else 0)


def units(text):
    text = unicodedata.normalize("NFC", mask_placeholders(text))
    return {cat for cat, rx in UNIT_RES.items() if rx.search(text)}


# ----------------------------------------------------------- term match

PARTICLES = sorted(set("""
이 가 을 를 은 는 의 에 에서 에게 에게서 께 께서 한테 한테서 으로 로 으로서 로서 으로써 로써 와 과 도 만 까지 부터
이나 나 이랑 랑 하고 보다 처럼 마다 조차 밖에 뿐 들 이다 입니다 이에요 예요 였다 이었다 이며 며 인 이고 고 야 이야
""".split()), key=len, reverse=True)
PARTICLE_ALT = "|".join(PARTICLES)
KIWI_DROP = {"SF", "SP", "SS", "SSO", "SSC", "SE", "SO", "SW"}


def _term_regex(term, case_sensitive):
    parts = [re.escape(p) for p in term.split()]
    if HANGUL_RE.search(term):
        # spacing is tolerated anywhere inside a Korean term (이해관계자 ~ 이해 관계자)
        body = r"\s*".join(r"\s?".join(re.escape(c) for c in p) for p in term.split())
        left = f"(?<![{HANGUL}A-Za-z0-9])" if HANGUL_RE.match(term[0]) else r"(?<![A-Za-z0-9])"
        right = f"(?:{PARTICLE_ALT})*(?![{HANGUL}])" if HANGUL_RE.match(term[-1]) else r"(?![A-Za-z0-9])"
        return re.compile(left + body + right)
    body = r"\s+".join(parts)
    left = r"(?<![A-Za-z0-9])" if term[:1].isalnum() else ""
    right = r"(?![A-Za-z0-9])" if term[-1:].isalnum() else ""
    plural = "" if case_sensitive or not term[-1:].isalpha() else r"(?:s|es|'s)?"
    return re.compile(left + body + plural + right, 0 if case_sensitive else re.I)


class TermMatcher:
    """Find glossary terms in text. Korean: particle-tolerant regex, plus Kiwi morphemes when installed."""

    def __init__(self, kiwi=None):
        self.kiwi = kiwi
        self._cache = {}

    def _forms(self, text):
        if text not in self._cache:
            self._cache[text] = [t.form for t in self.kiwi.tokenize(text)
                                 if not t.tag.startswith(("J", "E")) and t.tag not in KIWI_DROP]
        return self._cache[text]

    def has(self, term, text, case_sensitive=False):
        term = term.strip()
        if not term:
            return False
        if _term_regex(term, case_sensitive).search(unicodedata.normalize("NFC", text)):
            return True
        if self.kiwi is not None and HANGUL_RE.search(term) and not case_sensitive:
            tf, xf = self._forms(term), self._forms(text)
            n = len(tf)
            return n > 0 and any(xf[i:i + n] == tf for i in range(len(xf) - n + 1))
        return False


def load_kiwi():
    try:
        from kiwipiepy import Kiwi  # optional, local model, no network
    except Exception:
        return None
    try:
        return Kiwi()
    except Exception:
        return None


# --------------------------------------------------------------- checks

NO_TARGET = ("", "—", "-", "–")


def _ex(text, n=60):
    t = re.sub(r"\s+", " ", text).strip()
    return t if len(t) <= n else t[:n - 1] + "…"


class Report:
    def __init__(self, blocking_off=()):
        self.findings = []
        self.warn_only = set(blocking_off)

    def add(self, seg, check, severity, message, source="", target=""):
        if severity == "error" and check in self.warn_only:
            severity = "warning"
        self.findings.append({"segment": seg, "check": check, "severity": severity, "message": message,
                              "source": _ex(source), "target": _ex(target)})

    @property
    def blocking(self):
        return [f for f in self.findings if f["severity"] == "error"]


def check_segment(rep, seg, src_lang, tgt_lang, terms, matcher, opts, skip):
    sid, src, tgt = seg["id"], seg.get("source"), seg["target"]
    has_src = src is not None
    if "untranslated" not in skip:
        if has_src and src.strip() and not tgt.strip():
            rep.add(sid, "untranslated", "error", "target is empty", src, tgt)
        elif has_src and src_lang != tgt_lang and src.strip() == tgt.strip() and re.search(r"[^\W\d_]", src):
            rep.add(sid, "untranslated", "warning", "target is identical to the source", src, tgt)
    if has_src and "numbers" not in skip:
        sd, sw = numbers(src, src_lang)
        td, tw = numbers(tgt, tgt_lang)
        missing = (sd - td) - tw
        extra = (td - sd) - sw
        if missing:
            rep.add(sid, "numbers", "error", "missing in target: " + ", ".join(sorted(missing.elements())), src, tgt)
        if extra:
            rep.add(sid, "numbers", "warning", "not in source: " + ", ".join(sorted(extra.elements())), src, tgt)
    if has_src and "units" not in skip:
        su, tu = units(src), units(tgt)
        if su - tu:
            rep.add(sid, "units", "error", "unit missing in target: " + ", ".join(sorted(su - tu)), src, tgt)
        if tu - su:
            rep.add(sid, "units", "warning", "unit not in source: " + ", ".join(sorted(tu - su)), src, tgt)
    if has_src and "tags" not in skip:
        sp, tp = placeholders(src), placeholders(tgt)
        if sp - tp:
            rep.add(sid, "tags", "error", "missing/changed in target: " + " ".join(sorted((sp - tp).elements())), src, tgt)
        if tp - sp:
            rep.add(sid, "tags", "error", "not in source: " + " ".join(sorted((tp - sp).elements())), src, tgt)
    direction = f"{src_lang}-{tgt_lang}"
    for t in terms:
        row_tgt_lang = t["dir"].split("-")[-1] if "-" in t["dir"] else None
        applies = t["dir"] in ("both", direction)
        if t["status"] == "forbidden":
            if "forbidden" in skip or not (t["dir"] == "both" or row_tgt_lang == tgt_lang):
                continue
            if t["target"] not in NO_TARGET and matcher.has(t["target"], tgt):
                rep.add(sid, "forbidden", "error",
                        f"forbidden term '{t['target']}' (for '{t['source']}'){': ' + t['notes'] if t['notes'] else ''}",
                        src or "", tgt)
            continue
        if not has_src or not applies:
            continue
        if t["dnt"]:
            if "dnt" not in skip and matcher.has(t["source"], src, case_sensitive=True) and \
                    not matcher.has(t["source"], tgt, case_sensitive=True):
                rep.add(sid, "dnt", "error", f"DNT term '{t['source']}' not byte-identical in target", src, tgt)
            continue
        if "glossary" in skip or t["status"] not in ("approved", "preferred") or t["target"] in NO_TARGET:
            continue
        if src_lang == tgt_lang:
            continue
        if matcher.has(t["source"], src) and not matcher.has(t["target"], tgt):
            sev = "error" if t["status"] == "approved" else "warning"
            rep.add(sid, "glossary", sev, f"'{t['source']}' -> expected '{t['target']}' ({t['status']})", src, tgt)
    if "forbidden" not in skip:
        for term in opts.get("forbid", []):
            if matcher.has(term, tgt):
                rep.add(sid, "forbidden", "error", f"forbidden term '{term}'", src or "", tgt)
    if "spacing" not in skip:
        for m in re.finditer(r"(?<=\S)[ \u3000]{2,}(?=\S)", tgt):
            rep.add(sid, "spacing", "warning", f"double space at char {m.start()}",
                    "", tgt[max(0, m.start() - 20):m.end() + 20])
            break
    if "length" not in skip and opts.get("limit") is not None:
        n = textlen.measure(tgt)[opts["unit"]]
        if n > opts["limit"]:
            rep.add(sid, "length", "error", f"{n} {opts['unit']} > limit {opts['limit']} (over by {n - opts['limit']})", "", tgt)
        elif opts.get("min") is not None and n < opts["min"]:
            rep.add(sid, "length", "warning", f"{n} {opts['unit']} < min {opts['min']}", "", tgt)


# -------------------------------------------------------------- pofilter

def run_pofilter(path, lang, rep, exe=None):
    """Run translate-toolkit pofilter on an XLIFF/PO/TMX file; returns a status string for the summary.

    Command (verify against `pofilter --help` of the installed version):
      pofilter --language=<tgt> -t numbers -t xmltags ... <in> <out>
    Findings are read from the filtered output: PO comments `# (pofilter) <test>: <msg>` and XLIFF
    `<note from="pofilter">`.
    """
    exe = exe or shutil.which("pofilter")
    if not exe:
        return "not installed (pipx install translate-toolkit); skipped"
    path = pathlib.Path(path)
    with tempfile.TemporaryDirectory() as td:
        out = pathlib.Path(td) / f"filtered{path.suffix}"
        cmd = [exe, f"--language={lang}"]
        for t in POFILTER_TESTS:
            cmd += ["-t", t]
        cmd += [str(path), str(out)]
        try:
            r = subprocess.run(cmd, capture_output=True, text=True, timeout=600)
        except (OSError, subprocess.TimeoutExpired) as e:
            rep.add("-", "pofilter", "error", f"pofilter could not run: {e}")
            return "failed"
        if r.returncode != 0:
            rep.add("-", "pofilter", "error", f"pofilter exit {r.returncode}: {_ex(r.stderr, 200)}")
            return "failed"
        text = out.read_text(encoding="utf-8", errors="replace") if out.exists() else ""
    hits = re.findall(r"\(pofilter\)\s*([^\n<]+)", text)
    hits += re.findall(r"<note[^>]*from=\"pofilter\"[^>]*>(.*?)</note>", text, re.S)
    for h in hits:
        rep.add("-", "pofilter", "error", _ex(h.strip(), 200))
    return f"ran ({len(hits)} finding(s))"


# ---------------------------------------------------------------- inputs

def read_text(path):
    return sys.stdin.read() if path == "-" else pathlib.Path(path).read_text(encoding="utf-8")


def read_pairs(path):
    p = pathlib.Path(path)
    text = p.read_text(encoding="utf-8")
    if p.suffix.lower() == ".json":
        data = json.loads(text)
        return [{"id": str(d.get("id", i)), "source": d.get("source", ""), "target": d.get("target", "")}
                for i, d in enumerate(data, 1)]
    segs = []
    for i, row in enumerate(csv.reader(io.StringIO(text), delimiter="\t"), 1):
        if not row or not any(c.strip() for c in row):
            continue
        if len(row) >= 3:
            segs.append({"id": row[0], "source": row[1], "target": row[2]})
        elif len(row) == 2:
            segs.append({"id": str(i), "source": row[0], "target": row[1]})
        else:
            raise QAError(f"{path}:{i}: expected source<TAB>target")
    return segs


def build_segments(a, rep):
    if a.pairs:
        return read_pairs(a.pairs)
    if not a.target:
        return []
    tgt = read_text(a.target)
    src = read_text(a.source) if a.source else None
    if a.by_line:
        tl = [l for l in tgt.splitlines() if l.strip()]
        sl = [l for l in src.splitlines() if l.strip()] if src is not None else [None] * len(tl)
        if len(sl) == len(tl):
            return [{"id": str(i), "source": s, "target": t} for i, (s, t) in enumerate(zip(sl, tl), 1)]
        if "alignment" not in a.skip:
            rep.add("-", "alignment", "error", f"{len(sl)} source lines vs {len(tl)} target lines; checked as one segment")
    return [{"id": "1", "source": src, "target": tgt}]


# ---------------------------------------------------------------- output

def to_markdown(summary, findings):
    status = "FAIL" if summary["blocking"] else "PASS"
    lines = [f"# Translation QA: {summary['target']}", "",
             f"**{status}**: {summary['blocking']} blocking, {summary['warnings']} warning(s); "
             f"{summary['segments']} segment(s); direction {summary['direction']}; "
             f"glossary {summary['glossary_terms']} term(s); Korean matching: {summary['korean_matching']}; "
             f"pofilter: {summary['pofilter']}", "",
             "Checks run: " + ", ".join(summary["checks"]), ""]
    if not findings:
        lines.append("No findings.")
        return "\n".join(lines) + "\n"
    lines += ["| Seg | Check | Severity | Finding | Source | Target |", "|---|---|---|---|---|---|"]
    order = {"error": 0, "warning": 1}
    for f in sorted(findings, key=lambda f: (order.get(f["severity"], 2), f["check"])):
        cells = [f["segment"], f["check"], "**blocking**" if f["severity"] == "error" else "warning",
                 f["message"], f["source"], f["target"]]
        lines.append("| " + " | ".join(str(c).replace("|", "\\|") for c in cells) + " |")
    return "\n".join(lines) + "\n"


def main(argv=None):
    ap = argparse.ArgumentParser(prog="translation_qa.py", description=__doc__.splitlines()[0],
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--source", help="source text file (or - for stdin)")
    ap.add_argument("--target", help="target text file (or - for stdin)")
    ap.add_argument("--pairs", help="segments: .tsv (id<TAB>source<TAB>target or source<TAB>target) or .json")
    ap.add_argument("--by-line", action="store_true", help="align --source/--target line by line")
    ap.add_argument("--direction", help="ko-en, en-ko, ko-ko, en-en (default: detected)")
    ap.add_argument("--glossary", help="knowledge/glossary.md or glossary JSON (glossary.py to-json)")
    ap.add_argument("--forbid", action="append", default=[], help="term that must not appear (repeatable)")
    ap.add_argument("--forbid-file", help="file with one forbidden term per line")
    ap.add_argument("--limit", type=int, help="max length per target segment")
    ap.add_argument("--min", type=int, help="min length per target segment (warning)")
    ap.add_argument("--unit", choices=textlen.UNITS, default="chars")
    ap.add_argument("--pofilter", help="XLIFF/PO/TMX file to run translate-toolkit pofilter on, if installed")
    ap.add_argument("--skip", action="append", default=[], choices=CHECKS, help="do not run a check")
    ap.add_argument("--warn", action="append", default=[], choices=CHECKS, help="downgrade a check to warning")
    ap.add_argument("--no-kiwi", action="store_true", help="do not use kiwipiepy even if installed")
    ap.add_argument("--json", help="write the JSON report here (- for stdout)")
    ap.add_argument("--md", help="write the markdown report here (default: stdout)")
    a = ap.parse_args(argv)
    if not (a.target or a.pairs or a.pofilter):
        ap.error("give --target, --pairs or --pofilter")
    if a.source and not a.target:
        ap.error("--source needs --target")
    rep = Report(a.warn)
    try:
        segs = build_segments(a, rep)
        terms = glossary_mod.load(a.glossary) if a.glossary else []
        forbid = list(a.forbid)
        if a.forbid_file:
            forbid += [l.strip() for l in read_text(a.forbid_file).splitlines() if l.strip() and not l.startswith("#")]
    except (QAError, OSError, json.JSONDecodeError, glossary_mod.GlossaryError) as e:
        print(f"translation_qa.py: {e}", file=sys.stderr)
        return 2
    all_src = "\n".join(s["source"] or "" for s in segs)
    all_tgt = "\n".join(s["target"] for s in segs)
    if a.direction:
        if not re.fullmatch(r"(ko|en)-(ko|en)", a.direction):
            ap.error("--direction must be ko-en, en-ko, ko-ko or en-en")
        src_lang, tgt_lang = a.direction.split("-")
    else:
        tgt_lang = lang_of(all_tgt)
        src_lang = lang_of(all_src) if all_src.strip() else tgt_lang
    kiwi = None
    if not a.no_kiwi and "ko" in (src_lang, tgt_lang) and (terms or forbid):
        kiwi = load_kiwi()
    matcher = TermMatcher(kiwi)
    skip = set(a.skip)
    opts = {"forbid": forbid, "limit": a.limit, "min": a.min, "unit": a.unit}
    for seg in segs:
        check_segment(rep, seg, src_lang, tgt_lang, terms, matcher, opts, skip)
    po_status = "not requested"
    if a.pofilter and "pofilter" not in skip:
        po_status = run_pofilter(a.pofilter, tgt_lang, rep)
    has_src = any(s.get("source") is not None for s in segs)
    ran = [c for c in CHECKS if c not in skip and
           not (c in ("numbers", "units", "tags", "glossary", "dnt", "untranslated") and not has_src) and
           not (c == "length" and a.limit is None) and not (c == "alignment" and not a.by_line) and
           not (c == "pofilter" and not a.pofilter)]
    summary = {
        "target": a.target or a.pairs or a.pofilter,
        "result": "FAIL" if rep.blocking else "PASS",
        "blocking": len(rep.blocking),
        "warnings": len(rep.findings) - len(rep.blocking),
        "segments": len(segs),
        "direction": f"{src_lang}-{tgt_lang}",
        "glossary_terms": len(terms),
        "korean_matching": "kiwipiepy + particle heuristic" if kiwi else "particle heuristic",
        "pofilter": po_status,
        "checks": ran,
    }
    report = {"summary": summary, "findings": rep.findings}
    js = json.dumps(report, ensure_ascii=False, indent=2) + "\n"
    md = to_markdown(summary, rep.findings)
    if a.json == "-":
        sys.stdout.write(js)
    elif a.json:
        pathlib.Path(a.json).write_text(js, encoding="utf-8")
    if a.md:
        pathlib.Path(a.md).write_text(md, encoding="utf-8")
    elif a.json != "-":
        sys.stdout.write(md)
    print(f"translation-qa: {summary['result']} ({summary['blocking']} blocking, {summary['warnings']} warning(s))",
          file=sys.stderr)
    return 1 if rep.blocking else 0


if __name__ == "__main__":
    sys.exit(main())
