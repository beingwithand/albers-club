#!/usr/bin/env python3
"""StylePair store: draft -> final pairs the user edited, used as few-shot references.

Run with `python3 -I scripts/style_pairs.py <command>` (stdlib only).

Commands
  add      Validate and append one pair to $HARNESS_DATA/style/pairs.jsonl.
           Fields come from flags, or from a JSON object with --json FILE ('-' = stdin).
  nearest  Print the top-k pairs (JSON lines), ranked by register match, then
           direction match, then domain match, then text similarity
           (word tokens for Latin text, character bigrams for Hangul), then recency.
  stats    Counts by register, direction, language and domain.

Registers are read from schema/ontology.yaml (`registers: [...]`), so the list has one
source of truth. Directions and languages follow BLUEPRINT.md section 8.
Append-only: to fix a pair, add a new one with `supersedes` set to the old id.
"""
import argparse
import datetime
import json
import os
import pathlib
import re
import sys
import uuid

HARNESS_ROOT = pathlib.Path(__file__).resolve().parent.parent
ONTOLOGY = pathlib.Path(os.environ.get("HARNESS_ONTOLOGY", HARNESS_ROOT / "schema" / "ontology.yaml"))

LANGUAGES = ("ko", "en", "mixed")
DIRECTIONS = ("ko→en", "en→ko", "none")
_DIRECTION_ALIASES = {
    "ko→en": "ko→en", "ko->en": "ko→en", "ko-en": "ko→en", "ko>en": "ko→en", "ko2en": "ko→en", "koen": "ko→en",
    "en→ko": "en→ko", "en->ko": "en→ko", "en-ko": "en→ko", "en>ko": "en→ko", "en2ko": "en→ko", "enko": "en→ko",
    "none": "none", "": "none",
}
TEXT_FIELDS = ("draft", "final")
OPTIONAL_FIELDS = ("source", "reasoning", "client", "scope", "origin", "supersedes")

_HANGUL = r"ᄀ-ᇿ㄰-㆏가-힣"
_TOKEN_RE = re.compile(rf"[{_HANGUL}]+|[^\W_{_HANGUL}]+", re.UNICODE)
_HANGUL_RE = re.compile(rf"^[{_HANGUL}]+$")


class ValidationError(ValueError):
    pass


def load_registers(path=None):
    """Read the `registers: [a, b, ...]` list from the ontology (flow or block style)."""
    text = pathlib.Path(path or ONTOLOGY).read_text(encoding="utf-8")
    m = re.search(r"^registers:\s*\[([^\]]*)\]", text, re.MULTILINE)
    if m:
        items = m.group(1).split(",")
    else:
        m = re.search(r"^registers:\s*\n((?:\s+-\s*.+\n?)+)", text, re.MULTILINE)
        if not m:
            raise ValidationError(f"no 'registers' list found in {path or ONTOLOGY}")
        items = [ln.strip()[1:] for ln in m.group(1).splitlines() if ln.strip().startswith("-")]
    regs = [i.split("#")[0].strip().strip("'\"") for i in items]
    return [r for r in regs if r]


def norm_register(value):
    return re.sub(r"[\s_/]+", "-", (value or "").strip().lower())


def norm_direction(value):
    key = (value or "").strip().lower().replace(" ", "").replace("_", "-")
    if key not in _DIRECTION_ALIASES:
        raise ValidationError(f"direction {value!r} not one of {', '.join(DIRECTIONS)}")
    return _DIRECTION_ALIASES[key]


def data_file(path=None):
    if path:
        return pathlib.Path(path)
    base = pathlib.Path(os.environ.get("HARNESS_DATA", pathlib.Path.home() / "harness-data"))
    return base / "style" / "pairs.jsonl"


def validate(rec, registers=None):
    """Return a normalized copy of rec, or raise ValidationError."""
    registers = registers if registers is not None else load_registers()
    out = {}
    for f in TEXT_FIELDS:
        v = rec.get(f)
        if not isinstance(v, str) or not v.strip():
            raise ValidationError(f"'{f}' is required and must be non-empty text")
        out[f] = v
    lang = (rec.get("language") or "").strip().lower()
    if lang not in LANGUAGES:
        raise ValidationError(f"language {rec.get('language')!r} not one of {', '.join(LANGUAGES)}")
    out["language"] = lang
    out["direction"] = norm_direction(rec.get("direction", "none"))
    reg = norm_register(rec.get("register"))
    if reg not in registers:
        raise ValidationError(f"register {rec.get('register')!r} not in ontology list: {', '.join(registers)}")
    out["register"] = reg
    out["domain"] = (rec.get("domain") or "general").strip().lower()
    out["audience"] = (rec.get("audience") or "").strip()
    for f in OPTIONAL_FIELDS:
        if rec.get(f):
            out[f] = rec[f]
    labels = rec.get("labels") or []
    if isinstance(labels, str):
        labels = [x.strip() for x in labels.split(",") if x.strip()]
    out["labels"] = list(labels)
    out["edited"] = out["draft"].strip() != out["final"].strip()
    return out


def add(rec, path=None, registers=None, now=None):
    out = validate(rec, registers)
    now = now or datetime.datetime.now(datetime.timezone.utc)
    stored = {"id": f"sp_{now:%Y%m%d_%H%M%S}_{uuid.uuid4().hex[:4]}", "ts": now.isoformat()}
    stored.update(out)
    p = data_file(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    with p.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(stored, ensure_ascii=False) + "\n")
    return stored


def load(path=None):
    p = data_file(path)
    if not p.exists():
        return []
    pairs = []
    for n, line in enumerate(p.read_text(encoding="utf-8").splitlines(), 1):
        if not line.strip():
            continue
        try:
            pairs.append(json.loads(line))
        except json.JSONDecodeError:
            print(f"warning: skipping malformed line {n} in {p}", file=sys.stderr)
    superseded = {x.get("supersedes") for x in pairs if x.get("supersedes")}
    return [x for x in pairs if x.get("id") not in superseded]


def tokens(text):
    """Lowercased word tokens for Latin/other scripts; character bigrams for Hangul runs."""
    out = set()
    for tok in _TOKEN_RE.findall((text or "").lower()):
        if _HANGUL_RE.match(tok):
            if len(tok) == 1:
                out.add(tok)
            else:
                out.update(tok[i:i + 2] for i in range(len(tok) - 1))
        else:
            out.add(tok)
    return out


def similarity(a, b):
    ta, tb = tokens(a), tokens(b)
    if not ta or not tb:
        return 0.0
    return len(ta & tb) / len(ta | tb)


def nearest(pairs, register=None, direction=None, domain=None, text=None, k=5):
    reg = norm_register(register) if register else None
    dirn = norm_direction(direction) if direction else None
    dom = domain.strip().lower() if domain else None

    def key(p):
        hay = " ".join(filter(None, [p.get("source"), p.get("draft"), p.get("final")]))
        return (
            int(bool(reg) and p.get("register") == reg),
            int(bool(dirn) and p.get("direction") == dirn),
            int(bool(dom) and p.get("domain") == dom),
            similarity(text, hay) if text else 0.0,
            p.get("ts", ""),
        )

    scored = sorted(pairs, key=key, reverse=True)[: max(k, 0)]
    return [dict(p, _score=list(key(p)[:4])) for p in scored]


def stats(pairs):
    def count(field):
        c = {}
        for p in pairs:
            c[p.get(field) or "?"] = c.get(p.get(field) or "?", 0) + 1
        return dict(sorted(c.items(), key=lambda kv: (-kv[1], kv[0])))

    return {
        "total": len(pairs),
        "edited": sum(1 for p in pairs if p.get("edited")),
        "with_reasoning": sum(1 for p in pairs if p.get("reasoning")),
        "by_register": count("register"),
        "by_direction": count("direction"),
        "by_language": count("language"),
        "by_domain": count("domain"),
    }


def _read_text_arg(value):
    if value and value.startswith("@"):
        return pathlib.Path(value[1:]).read_text(encoding="utf-8")
    return value


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--file", help="pairs.jsonl path (default $HARNESS_DATA/style/pairs.jsonl)")
    sub = ap.add_subparsers(dest="cmd", required=True)

    a = sub.add_parser("add", help="append one validated pair; text args accept @path")
    a.add_argument("--json", help="read the pair as a JSON object from this file ('-' = stdin)")
    for f in TEXT_FIELDS + ("language", "direction", "register", "domain", "audience", "labels") + OPTIONAL_FIELDS:
        a.add_argument(f"--{f}")

    n = sub.add_parser("nearest", help="top-k closest pairs as JSON lines")
    n.add_argument("--register")
    n.add_argument("--direction")
    n.add_argument("--domain")
    n.add_argument("--text", help="source text or draft to compare against (@path allowed)")
    n.add_argument("-k", type=int, default=5)

    s = sub.add_parser("stats", help="counts by register/direction/language/domain")
    s.add_argument("--json", action="store_true")

    args = ap.parse_args(argv)
    try:
        if args.cmd == "add":
            if args.json:
                raw = sys.stdin.read() if args.json == "-" else pathlib.Path(args.json).read_text(encoding="utf-8")
                rec = json.loads(raw)
            else:
                rec = {}
            for f in TEXT_FIELDS + ("language", "direction", "register", "domain", "audience", "labels") + OPTIONAL_FIELDS:
                v = getattr(args, f)
                if v is not None:
                    rec[f] = _read_text_arg(v) if f in TEXT_FIELDS + ("source", "reasoning") else v
            print(json.dumps(add(rec, args.file), ensure_ascii=False))
        elif args.cmd == "nearest":
            for p in nearest(load(args.file), args.register, args.direction, args.domain,
                             _read_text_arg(args.text), args.k):
                print(json.dumps(p, ensure_ascii=False))
        elif args.cmd == "stats":
            st = stats(load(args.file))
            if args.json:
                print(json.dumps(st, ensure_ascii=False, indent=2))
            else:
                print(f"total {st['total']}  edited {st['edited']}  with_reasoning {st['with_reasoning']}")
                for key in ("by_register", "by_direction", "by_language", "by_domain"):
                    print(f"{key[3:]}: " + ", ".join(f"{k}={v}" for k, v in st[key].items()))
    except (ValidationError, json.JSONDecodeError, OSError) as e:
        print(f"error: {e}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
