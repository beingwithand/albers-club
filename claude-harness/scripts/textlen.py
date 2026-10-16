"""Count text length the way length-limited deliverables (e.g. synopses) are measured.

Usage:
  python3 -I textlen.py [--limit N] [--unit chars|chars_nospace|words|bytes] [FILE|-]
  python3 -I textlen.py --limit 110 --unit chars draft1.txt draft2.txt draft3.txt

Prints every unit for each input; with --limit, also prints OK/OVER/UNDER-by and exits 1 if any
input is over the limit. Counts Unicode code points after NFC normalisation, so composed Hangul
syllables count as one character each. Leading/trailing whitespace is ignored; internal runs of
whitespace count as one space (what most client tools display).
"""
import argparse
import re
import sys
import unicodedata

UNITS = ("chars", "chars_nospace", "words", "bytes")


def normalise(text):
    text = unicodedata.normalize("NFC", text).strip()
    return re.sub(r"\s+", " ", text)


def measure(text):
    t = normalise(text)
    return {
        "chars": len(t),
        "chars_nospace": len(t.replace(" ", "")),
        "words": len(t.split()) if t else 0,
        "bytes": len(t.encode("utf-8")),
    }


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("files", nargs="*", default=["-"])
    ap.add_argument("--limit", type=int)
    ap.add_argument("--unit", choices=UNITS, default="chars")
    ap.add_argument("--min", type=int, help="optional lower bound (e.g. stay close to the cap)")
    args = ap.parse_args(argv)

    over = False
    for name in args.files:
        text = sys.stdin.read() if name == "-" else open(name, encoding="utf-8").read()
        m = measure(text)
        line = f"{name}: " + "  ".join(f"{u}={m[u]}" for u in UNITS)
        if args.limit is not None:
            n = m[args.unit]
            if n > args.limit:
                over = True
                line += f"  -> OVER by {n - args.limit} {args.unit}"
            elif args.min is not None and n < args.min:
                line += f"  -> UNDER min by {args.min - n} {args.unit}"
            else:
                line += f"  -> OK ({args.limit - n} {args.unit} spare)"
        print(line)
    return 1 if over else 0


if __name__ == "__main__":
    sys.exit(main())
