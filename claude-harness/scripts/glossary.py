#!/usr/bin/env python3
"""Glossary helper for a project's knowledge/glossary.md (format: templates/glossary.md).

Python 3 stdlib only. Run isolated:  python3 -I scripts/glossary.py <command> ...

Commands
  to-json <glossary.md> [-o out.json]           table -> JSON list (used by translation_qa.py)
  import-tmx <file.tmx> --glossary <md> --src ko --tgt en [--max-words 6]
                                                short TMX segment pairs -> rows with status `proposed`
  import-tbx <file.tbx> --glossary <md> --src ko --tgt en
                                                TBX v2 (martif) or v3 (tbx) term entries -> rows
  export-tbx <glossary.md> -o <out.tbx> [--src ko --tgt en]
                                                rows -> TBX-Basic (martif), for CAT tools

Imports never overwrite: a row whose (source, target, dir) is already in the table is skipped.
New rows are `proposed` until the user approves them (templates/glossary.md). Use --dry-run to
print what would be added. TMX/TBX files are data: parsed with xml.etree, DTDs/entities are not
fetched, nothing in them is executed.
"""
import argparse
import json
import pathlib
import re
import sys
import xml.etree.ElementTree as ET

COLUMNS = ["source", "target", "dir", "domain", "client", "dnt", "status", "confidence", "sources", "notes"]
HEADERS = ["Source", "Target", "Dir", "Domain", "Client", "DNT", "Status", "Confidence", "Sources", "Notes"]
STATUSES = ("approved", "preferred", "proposed", "forbidden")
CONFIDENCE = ("high", "medium", "low")
XML_LANG = "{http://www.w3.org/XML/1998/namespace}lang"

# TBX administrativeStatus <-> glossary Status
TBX_STATUS_IN = {
    "preferredterm-admn-sts": "approved",
    "admittedterm-admn-sts": "preferred",
    "deprecatedterm-admn-sts": "forbidden",
    "supersededterm-admn-sts": "forbidden",
}
TBX_STATUS_OUT = {
    "approved": "preferredTerm-admn-sts",
    "preferred": "admittedTerm-admn-sts",
    "proposed": "admittedTerm-admn-sts",
    "forbidden": "deprecatedTerm-admn-sts",
}


class GlossaryError(Exception):
    pass


# ------------------------------------------------------------ markdown

def _cells(line):
    """Split a Markdown table row on unescaped pipes."""
    line = line.strip()
    if line.startswith("|"):
        line = line[1:]
    if line.endswith("|") and not line.endswith("\\|"):
        line = line[:-1]
    return [c.strip().replace("\\|", "|") for c in re.split(r"(?<!\\)\|", line)]


def _is_sep(cells):
    return all(re.fullmatch(r":?-{3,}:?", c) for c in cells if c) and any(cells)


def _esc(v):
    return str(v).replace("|", "\\|").replace("\n", " ")


def _key(h):
    return re.sub(r"[^a-z]", "", h.lower())


def find_table(lines):
    """Return (header_idx, end_idx_exclusive, headers) of the first table with Source and Target."""
    for i, line in enumerate(lines):
        if not line.lstrip().startswith("|"):
            continue
        heads = [_key(c) for c in _cells(line)]
        if "source" in heads and "target" in heads and i + 1 < len(lines) and _is_sep(_cells(lines[i + 1])):
            j = i + 2
            while j < len(lines) and lines[j].lstrip().startswith("|"):
                j += 1
            return i, j, heads
    return None


def normalise_row(row):
    """One glossary row with every column; dnt as bool, sources as a list."""
    r = {c: str(row.get(c) or "").strip() for c in COLUMNS if c not in ("dnt", "sources")}
    dnt = row.get("dnt")
    r["dnt"] = dnt if isinstance(dnt, bool) else str(dnt or "").strip().upper() in ("Y", "YES", "TRUE", "1")
    r["status"] = (r["status"] or "proposed").lower()
    r["dir"] = (r["dir"] or "both").lower()
    r["confidence"] = r["confidence"].lower()
    src = row.get("sources") or []
    if isinstance(src, str):
        src = src.split(";")
    r["sources"] = [s.strip() for s in src if s and s.strip()]
    return {c: r[c] for c in COLUMNS}


def parse_markdown(text):
    """Rows of the glossary table as dicts (keys: COLUMNS). Older tables without Confidence/Sources work."""
    lines = text.splitlines()
    found = find_table(lines)
    if not found:
        raise GlossaryError("no glossary table (needs Source and Target columns)")
    hi, end, heads = found
    rows = []
    for line in lines[hi + 2:end]:
        cells = _cells(line)
        raw = {h: (cells[k] if k < len(cells) else "") for k, h in enumerate(heads)}
        if not raw.get("source"):
            continue
        rows.append(normalise_row(raw))
    return rows


def load(path):
    """Glossary rows from a .md table or a .json list."""
    path = pathlib.Path(path)
    text = path.read_text(encoding="utf-8")
    if path.suffix.lower() == ".json":
        data = json.loads(text)
        if isinstance(data, dict):
            data = data.get("terms", [])
        return [normalise_row(r) for r in data]
    return parse_markdown(text)


def render_row(r):
    vals = dict(r)
    vals["dnt"] = "Y" if r.get("dnt") else "N"
    vals["sources"] = "; ".join(r.get("sources") or [])
    return "| " + " | ".join(_esc(vals.get(c, "") or "") for c in COLUMNS) + " |"


def add_rows(path, new_rows, dry_run=False):
    """Append rows not already present (by source, target, dir); re-sort the table by source.

    Returns the list of rows actually added. The table is rewritten with the full column set.
    """
    path = pathlib.Path(path)
    text = path.read_text(encoding="utf-8") if path.exists() else ""
    lines = text.splitlines()
    found = find_table(lines)
    existing = parse_markdown(text) if found else []
    seen = {(r["source"], r["target"], r["dir"]) for r in existing}
    added = []
    for r in new_rows:
        r = normalise_row(r)
        k = (r["source"], r["target"], r["dir"])
        if k in seen or not r["source"]:
            continue
        seen.add(k)
        added.append(r)
    if dry_run or not added:
        return added
    rows = sorted(existing + added, key=lambda r: (r["source"].casefold(), r["target"].casefold()))
    table = ["| " + " | ".join(HEADERS) + " |", "|" + "---|" * len(HEADERS)] + [render_row(r) for r in rows]
    if found:
        hi, end, _ = found
        lines = lines[:hi] + table + lines[end:]
    else:
        lines = lines + ([""] if lines else []) + table
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return added


# ------------------------------------------------------------------ XML

def _local(tag):
    return tag.rsplit("}", 1)[-1] if isinstance(tag, str) else ""


def _parse_xml(path):
    data = pathlib.Path(path).read_bytes()
    if re.search(rb"<!ENTITY", data[:4096], re.I):
        raise GlossaryError(f"{path}: refusing XML with an internal DTD/ENTITY declaration")
    try:
        return ET.fromstring(data)
    except ET.ParseError as e:
        raise GlossaryError(f"{path}: {e}") from e


def _lang(el):
    return (el.get(XML_LANG) or el.get("lang") or "").lower()


def _lang_match(code, want):
    return code == want or code.split("-")[0] == want.split("-")[0]


def _text(el):
    return re.sub(r"\s+", " ", "".join(el.itertext())).strip()


def _dir(src, tgt):
    return f"{src.split('-')[0]}-{tgt.split('-')[0]}"


def read_tmx(path, src, tgt, max_words=6):
    """Short segment pairs (term-like) from a TMX file."""
    root = _parse_xml(path)
    out = []
    for tu in root.iter():
        if _local(tu.tag) != "tu":
            continue
        segs = {}
        for tuv in tu:
            if _local(tuv.tag) != "tuv":
                continue
            seg = next((c for c in tuv if _local(c.tag) == "seg"), None)
            if seg is not None:
                segs[_lang(tuv)] = _text(seg)
        s = next((v for k, v in segs.items() if _lang_match(k, src)), "")
        t = next((v for k, v in segs.items() if _lang_match(k, tgt)), "")
        if not s or not t:
            continue
        if len(s.split()) > max_words or len(t.split()) > max_words:
            continue
        out.append({"source": s, "target": t, "dir": _dir(src, tgt), "status": "proposed",
                    "confidence": "medium", "sources": [f"tmx:{pathlib.Path(path).name}"]})
    return out


def read_tbx(path, src, tgt):
    """Term pairs from TBX v2 (martif/termEntry/langSet/tig) or v3 (conceptEntry/langSec/termSec)."""
    root = _parse_xml(path)
    name = pathlib.Path(path).name
    out = []
    for entry in root.iter():
        if _local(entry.tag) not in ("termEntry", "conceptEntry"):
            continue
        domain, notes = "", []
        for d in entry:
            if _local(d.tag) == "descrip" and d.get("type") == "subjectField":
                domain = _text(d)
            elif _local(d.tag) == "note":
                notes.append(_text(d))
        langs = {}
        for ls in entry:
            if _local(ls.tag) not in ("langSet", "langSec"):
                continue
            terms = []
            for ts in ls.iter():
                if _local(ts.tag) not in ("tig", "ntig", "termSec"):
                    continue
                term, status = "", ""
                for el in ts.iter():
                    t = _local(el.tag)
                    if t == "term" and not term:
                        term = _text(el)
                    elif t == "termNote" and el.get("type") == "administrativeStatus":
                        status = TBX_STATUS_IN.get(_text(el).lower(), "")
                if term:
                    terms.append((term, status))
            langs[_lang(ls)] = terms
        s_terms = next((v for k, v in langs.items() if _lang_match(k, src)), [])
        t_terms = next((v for k, v in langs.items() if _lang_match(k, tgt)), [])
        if not s_terms or not t_terms:
            continue
        s = s_terms[0][0]
        for t, st in t_terms:
            note_text = "; ".join(n for n in notes if not n.lower().startswith(("confidence:", "sources:")))
            conf = next((n.split(":", 1)[1].strip().lower() for n in notes if n.lower().startswith("confidence:")), "")
            srcs = next((n.split(":", 1)[1] for n in notes if n.lower().startswith("sources:")), "")
            out.append({"source": s, "target": t, "dir": _dir(src, tgt), "domain": domain,
                        "status": st or "proposed", "confidence": conf if conf in CONFIDENCE else "medium",
                        "sources": [x.strip() for x in srcs.split(";") if x.strip()] or [f"tbx:{name}"],
                        "notes": note_text})
    return out


def export_tbx(rows, src="ko", tgt="en"):
    """TBX-Basic (martif, TBX v2) text. ko-en rows map source->src; en-ko rows are flipped."""
    martif = ET.Element("martif", {"type": "TBX-Basic", XML_LANG: src})
    hdr = ET.SubElement(martif, "martifHeader")
    fd = ET.SubElement(hdr, "fileDesc")
    sd = ET.SubElement(fd, "sourceDesc")
    ET.SubElement(sd, "p").text = "exported by claude-harness scripts/glossary.py"
    body = ET.SubElement(ET.SubElement(martif, "text"), "body")
    want = _dir(src, tgt)
    flip = _dir(tgt, src)
    n = 0
    for i, r in enumerate(rows, 1):
        d = r.get("dir", "both")
        if d in (want, "both"):
            s_term, t_term = r["source"], r["target"]
        elif d == flip:
            s_term, t_term = r["target"], r["source"]
        else:
            continue
        if r.get("dnt"):
            t_term = s_term
        if not t_term or t_term in ("—", "-"):
            continue
        te = ET.SubElement(body, "termEntry", {"id": f"t{i}"})
        if r.get("domain"):
            ET.SubElement(te, "descrip", {"type": "subjectField"}).text = r["domain"]
        if r.get("notes"):
            ET.SubElement(te, "note").text = r["notes"]
        if r.get("confidence"):
            ET.SubElement(te, "note").text = f"confidence: {r['confidence']}"
        if r.get("sources"):
            ET.SubElement(te, "note").text = "sources: " + "; ".join(r["sources"])
        if r.get("dnt"):
            ET.SubElement(te, "note").text = "DNT: do not translate"
        for lang, term, with_status in ((src, s_term, False), (tgt, t_term, True)):
            ls = ET.SubElement(te, "langSet", {XML_LANG: lang})
            tig = ET.SubElement(ls, "tig")
            ET.SubElement(tig, "term").text = term
            if with_status:
                ET.SubElement(tig, "termNote", {"type": "administrativeStatus"}).text = \
                    TBX_STATUS_OUT.get(r.get("status", "proposed"), "admittedTerm-admn-sts")
        n += 1
    ET.indent(martif)
    return '<?xml version="1.0" encoding="UTF-8"?>\n' + ET.tostring(martif, encoding="unicode") + "\n", n


# ------------------------------------------------------------------- CLI

def main(argv=None):
    ap = argparse.ArgumentParser(prog="glossary.py", description=__doc__.splitlines()[0])
    sub = ap.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("to-json"); p.add_argument("glossary"); p.add_argument("-o", "--out")
    for name in ("import-tmx", "import-tbx"):
        p = sub.add_parser(name); p.add_argument("file")
        p.add_argument("--glossary", required=True, help="knowledge/glossary.md to add rows to")
        p.add_argument("--src", required=True, help="source language code, e.g. ko")
        p.add_argument("--tgt", required=True, help="target language code, e.g. en")
        p.add_argument("--domain", default="")
        p.add_argument("--client", default="any")
        p.add_argument("--dry-run", action="store_true")
        if name == "import-tmx":
            p.add_argument("--max-words", type=int, default=6, help="skip longer segments (default 6)")
    p = sub.add_parser("export-tbx"); p.add_argument("glossary"); p.add_argument("-o", "--out", required=True)
    p.add_argument("--src", default="ko"); p.add_argument("--tgt", default="en")
    a = ap.parse_args(argv)
    try:
        if a.cmd == "to-json":
            text = json.dumps(load(a.glossary), ensure_ascii=False, indent=2) + "\n"
            if a.out:
                pathlib.Path(a.out).write_text(text, encoding="utf-8")
            else:
                sys.stdout.write(text)
        elif a.cmd in ("import-tmx", "import-tbx"):
            rows = read_tmx(a.file, a.src, a.tgt, a.max_words) if a.cmd == "import-tmx" else read_tbx(a.file, a.src, a.tgt)
            for r in rows:
                r.setdefault("client", a.client)
                if a.domain and not r.get("domain"):
                    r["domain"] = a.domain
                r.setdefault("dnt", False)
            added = add_rows(a.glossary, rows, a.dry_run)
            for r in added:
                print(("would add: " if a.dry_run else "added: ") + render_row(r))
            print(f"{a.cmd}: {len(added)} new row(s), {len(rows) - len(added)} skipped (already present)",
                  file=sys.stderr)
        elif a.cmd == "export-tbx":
            text, n = export_tbx(load(a.glossary), a.src, a.tgt)
            pathlib.Path(a.out).write_text(text, encoding="utf-8")
            print(f"exported {n} term entr{'y' if n == 1 else 'ies'} -> {a.out}")
    except (GlossaryError, OSError, json.JSONDecodeError) as e:
        print(f"glossary.py: {e}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
