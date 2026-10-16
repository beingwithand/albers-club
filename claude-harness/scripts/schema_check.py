#!/usr/bin/env python3
"""Validate harness data files against schema/ontology.yaml (stdlib only; run with `python3 -I`).

    python3 -I scripts/schema_check.py                         # check $HARNESS_DATA (default ~/harness-data)
    python3 -I scripts/schema_check.py --root ~/harness-data --project ~/work/translation/acme
    python3 -I scripts/schema_check.py --file applications.jsonl --type Application
    python3 -I scripts/schema_check.py --stores                # print the storage map from the ontology
    python3 -I scripts/schema_check.py --json --strict         # machine output; warnings count as errors

What it checks, per record, using each type's `fields`, `required`, `enums`, `value_aliases`,
`aliases`, `formats`, `id_prefix`, `id_pattern`, `id_field`, `unique_id` and (Event only) `expected_when`:
  errors    missing required field, value not in enum, bad id prefix/pattern, duplicate id where ids
            must be unique, bad date/datetime/scope/sha256/url, unparseable line
  warnings  field not declared in the ontology, enum value accepted only through `value_aliases`,
            Event missing an `expected_when` field (unless a later `label` event fills it)

Formats it reads: jsonl, json (optional `container` key), csv (header row), yaml (a small subset:
block maps and lists, one-line flow [..]/{..}, quoted scalars, comments). `md`, `event` and `embedded`
stores are listed but not parsed. It never writes anything.

Exit codes: 0 no errors, 1 errors found (or warnings with --strict), 2 usage error.
"""
import argparse
import csv
import datetime as dt
import fnmatch
import json
import os
import pathlib
import re
import sys

HARNESS_ROOT = pathlib.Path(__file__).resolve().parent.parent
DEFAULT_ONTOLOGY = HARNESS_ROOT / "schema" / "ontology.yaml"
PARSED_FORMATS = ("jsonl", "json", "csv", "yaml")


class YamlError(ValueError):
    pass


# ---------------------------------------------------------------- tiny YAML subset

def _strip_comment(line):
    out, quote, prev, esc = [], None, " ", False
    for ch in line:
        if quote:
            if esc:
                esc = False
            elif quote == '"' and ch == "\\":
                esc = True
            elif ch == quote:
                quote = None
        elif ch in "\"'" and prev in " \t[{,:":
            quote = ch
        elif ch == "#" and prev in " \t":
            break
        out.append(ch)
        prev = ch
    return "".join(out).rstrip()


def _split_top(s, sep):
    """Split s on sep at bracket depth 0, outside quotes."""
    parts, buf, depth, quote, prev, esc = [], [], 0, None, ",", False
    for ch in s:
        if quote:
            buf.append(ch)
            if esc:
                esc = False
            elif quote == '"' and ch == "\\":
                esc = True
            elif ch == quote:
                quote = None
            continue
        if ch in "\"'" and prev in ",:[{":
            quote = ch
        elif ch in "[{":
            depth += 1
        elif ch in "]}":
            depth -= 1
        if ch == sep and depth == 0:
            parts.append("".join(buf))
            buf = []
        else:
            buf.append(ch)
        if not ch.isspace():
            prev = ch
    parts.append("".join(buf))
    return parts


def _key_split(s):
    """'key: value' -> (key, value) or None. Key may be quoted."""
    s = s.strip()
    if s[:1] in "\"'":
        q = s[0]
        end = s.find(q, 1)
        while q == '"' and end > 0 and s[end - 1] == "\\":
            end = s.find(q, end + 1)
        if end < 0:
            return None
        rest = s[end + 1:]
        if rest.startswith(":") and (len(rest) == 1 or rest[1] in " \t"):
            return _scalar(s[:end + 1]), rest[1:].strip()
        return None
    m = re.match(r"^([^\s\[\]{},:#][^:]*?|[^\s\[\]{},:#]):(?:\s+(.*)|)$", s)
    if not m:
        return None
    return m.group(1).strip(), (m.group(2) or "").strip()


def _scalar(s):
    s = s.strip()
    if s == "" or s in ("~", "null", "Null", "NULL"):
        return None
    if s.startswith('"'):
        try:
            return json.loads(s)
        except ValueError:
            raise YamlError(f"bad double-quoted string: {s}")
    if s.startswith("'"):
        if not s.endswith("'") or len(s) < 2:
            raise YamlError(f"bad single-quoted string: {s}")
        return s[1:-1].replace("''", "'")
    if s.startswith("["):
        if not s.endswith("]"):
            raise YamlError(f"unclosed flow list: {s}")
        inner = s[1:-1].strip()
        return [] if not inner else [_scalar(x) for x in _split_top(inner, ",") if x.strip()]
    if s.startswith("{"):
        if not s.endswith("}"):
            raise YamlError(f"unclosed flow map: {s}")
        inner = s[1:-1].strip()
        out = {}
        if inner:
            for part in _split_top(inner, ","):
                if not part.strip():
                    continue
                kv = _key_split(part)
                if kv is None:
                    raise YamlError(f"bad flow map entry: {part.strip()}")
                out[kv[0]] = _scalar(kv[1])
        return out
    if s in ("true", "True", "TRUE"):
        return True
    if s in ("false", "False", "FALSE"):
        return False
    if re.fullmatch(r"[-+]?\d+", s):
        return int(s)
    if re.fullmatch(r"[-+]?(\d+\.\d*|\.\d+)([eE][-+]?\d+)?", s):
        return float(s)
    return s


def yaml_load(text):
    lines = []
    for raw in text.splitlines():
        if raw.strip() in ("---", "..."):
            continue
        body = _strip_comment(raw.replace("\t", "    "))
        if body.strip():
            lines.append([len(body) - len(body.lstrip(" ")), body.strip(), raw])
    if not lines:
        return None
    val, i = _block(lines, 0, lines[0][0])
    if i != len(lines):
        raise YamlError(f"unexpected indentation at: {lines[i][1]}")
    return val


def _block_scalar(lines, i, indent, style):
    parts = []
    while i < len(lines) and lines[i][0] > indent:
        parts.append(lines[i][2].strip())
        i += 1
    return ("\n" if style.startswith("|") else " ").join(parts), i


def _value_after_key(lines, i, indent, rest):
    """Value for 'key: rest' found at lines[i-1] (indent = that key's indent)."""
    if rest in ("|", ">", "|-", ">-", "|+", ">+"):
        return _block_scalar(lines, i, indent, rest)
    if rest:
        return _scalar(rest), i
    if i < len(lines) and (lines[i][0] > indent or (lines[i][0] == indent and lines[i][1].startswith("- ") or lines[i][1] == "-")):
        if lines[i][0] == indent:  # list at the same indent as its key
            return _list(lines, i, indent)
        return _block(lines, i, lines[i][0])
    return None, i


def _block(lines, i, indent):
    if lines[i][1] == "-" or lines[i][1].startswith("- "):
        return _list(lines, i, indent)
    out = {}
    while i < len(lines) and lines[i][0] == indent and not (lines[i][1] == "-" or lines[i][1].startswith("- ")):
        kv = _key_split(lines[i][1])
        if kv is None:
            if len(lines) == 1:
                return _scalar(lines[i][1]), i + 1
            raise YamlError(f"expected 'key: value', got: {lines[i][1]}")
        key, rest = kv
        out[key], i = _value_after_key(lines, i + 1, indent, rest)
    return out, i


def _list(lines, i, indent):
    out = []
    while i < len(lines) and lines[i][0] == indent and (lines[i][1] == "-" or lines[i][1].startswith("- ")):
        rest = lines[i][1][1:].strip()
        if not rest:
            if i + 1 < len(lines) and lines[i + 1][0] > indent:
                val, i = _block(lines, i + 1, lines[i + 1][0])
            else:
                val, i = None, i + 1
            out.append(val)
            continue
        kv = _key_split(rest) if not rest.startswith(("[", "{", '"', "'")) or _key_split(rest) else None
        if kv is not None:
            child = indent + 2 + (len(lines[i][1]) - 2 - len(rest)) if lines[i][1].startswith("- ") else indent + 2
            lines[i] = [child, rest, lines[i][2]]
            val, i = _block(lines, i, child)
            out.append(val)
        else:
            out.append(_scalar(rest))
            i += 1
    return out, i


# ---------------------------------------------------------------- ontology

class Ontology:
    def __init__(self, data):
        if not isinstance(data, dict) or not isinstance(data.get("types"), dict):
            raise YamlError("ontology has no 'types' mapping")
        self.data = data
        self.version = data.get("version")
        self.areas = list(data.get("areas") or [])
        self.registers = list(data.get("registers") or [])
        self.enums = dict(data.get("enums") or {})
        self.types = data["types"]

    @classmethod
    def load(cls, path=None):
        p = pathlib.Path(path or os.environ.get("HARNESS_ONTOLOGY") or DEFAULT_ONTOLOGY)
        return cls(yaml_load(p.read_text(encoding="utf-8")))

    def enum_values(self, ref):
        if isinstance(ref, list):
            return [str(v) for v in ref]
        if ref == "registers":
            return list(self.registers)
        if ref == "areas":
            return list(self.areas)
        if isinstance(ref, str) and isinstance(self.enums.get(ref), list):
            return [str(v) for v in self.enums[ref]]
        raise YamlError(f"unknown enum reference {ref!r}")

    def stores(self, root=None):
        for name, t in self.types.items():
            st = (t or {}).get("store") or {}
            if root is None or st.get("root") == root:
                yield name, st


def path_glob(path):
    """Ontology store path -> fnmatch pattern (YYYY-MM, YYYY-MM-DD and <...> are wildcards)."""
    g = re.sub(r"<[^>]+>", "*", path)
    g = g.replace("YYYY-MM-DD", "????-??-??").replace("YYYY-MM", "????-??")
    return g


# ---------------------------------------------------------------- validation

class Report:
    def __init__(self):
        self.errors, self.warnings, self.checked = [], [], []

    def err(self, where, msg):
        self.errors.append(f"{where}: {msg}")

    def warn(self, where, msg):
        self.warnings.append(f"{where}: {msg}")


_DATE = re.compile(r"^\d{4}-\d{2}-\d{2}$")


def _check_format(kind, value, onto):
    if value in (None, ""):
        return None
    s = str(value)
    if kind == "date":
        if not _DATE.match(s):
            return "not a YYYY-MM-DD date"
        try:
            dt.date.fromisoformat(s)
        except ValueError:
            return "not a valid date"
    elif kind == "datetime":
        try:
            dt.datetime.fromisoformat(s.replace("Z", "+00:00"))
        except ValueError:
            return "not an ISO 8601 datetime"
    elif kind == "scope":
        if s == "global" or re.fullmatch(r"task:[a-z0-9-]+", s):
            return None
        area = s.split("/", 1)[0]
        if area not in onto.areas or not re.fullmatch(r"[^/\s]+(/[^/\s]+)?", s):
            return f"scope must be global | <area> | <area>/<project> (areas: {', '.join(onto.areas)})"
    elif kind == "sha256":
        if not re.fullmatch(r"[0-9a-f]{64}", s):
            return "not a sha256 hex digest"
    elif kind == "url":
        if not re.match(r"^[a-z][a-z0-9+.-]*://", s):
            return "not a URL"
    return None


def validate_records(type_name, records, onto, report, where="", seen_ids=None):
    """records: iterable of (location, dict). Returns the number of records checked."""
    t = onto.types.get(type_name)
    if t is None:
        raise YamlError(f"unknown type {type_name!r}")
    fields = set(map(str, t.get("fields") or []))
    required = [str(f) for f in t.get("required") or []]
    aliases = {str(k): str(v) for k, v in (t.get("aliases") or {}).items()}
    enums = {str(k): onto.enum_values(v) for k, v in (t.get("enums") or {}).items()}
    vals_alias = {str(k): {str(a): str(b) for a, b in (v or {}).items()} for k, v in (t.get("value_aliases") or {}).items()}
    formats = {str(k): str(v) for k, v in (t.get("formats") or {}).items()}
    refs = {str(k): str(v) for k, v in (t.get("refs") or {}).items()}
    id_field = str(t.get("id_field") or "id")
    prefix = t.get("id_prefix")
    pattern = re.compile(t["id_pattern"]) if t.get("id_pattern") else None
    unique = bool(t.get("unique_id"))
    expected = t.get("expected_when") or {}
    seen = {} if seen_ids is None else seen_ids
    n = 0
    recs = list(records)
    labeled = set()
    if type_name == "Event":
        for _, r in recs:
            if isinstance(r, dict) and r.get("type") == "label" and r.get("labels_for"):
                labeled.add(r["labels_for"])
    for loc, rec in recs:
        n += 1
        w = f"{where}{loc}"
        if not isinstance(rec, dict):
            report.err(w, f"{type_name} record is not an object")
            continue
        rec = dict(rec)
        for raw, canon in aliases.items():
            if raw in rec and canon not in rec:
                rec[canon] = rec.pop(raw)
        for f in required:
            if rec.get(f) in (None, "", [], {}):
                report.err(w, f"{type_name}: required field '{f}' missing or empty")
        if fields:
            extra = sorted(k for k in rec if k not in fields and not k.startswith("_"))
            if extra:
                report.warn(w, f"{type_name}: fields not in ontology: {', '.join(extra)}")
        for f, allowed in enums.items():
            v = rec.get(f)
            if v in (None, ""):
                continue
            for item in (v if isinstance(v, list) else [v]):
                s = item if isinstance(item, str) else json.dumps(item)
                if s in allowed:
                    continue
                canon = vals_alias.get(f, {}).get(s)
                if canon in allowed:
                    report.warn(w, f"{type_name}.{f}: {s!r} accepted as alias of {canon!r}; write the canonical value")
                else:
                    report.err(w, f"{type_name}.{f}: {s!r} not one of {', '.join(allowed)}")
        for f, kind in formats.items():
            problem = _check_format(kind, rec.get(f), onto)
            if problem:
                report.err(w, f"{type_name}.{f}: {rec.get(f)!r} {problem}")
        for f, target in refs.items():
            v = rec.get(f)
            if v in (None, ""):
                continue
            tp = (onto.types.get(target) or {}).get("id_prefix")
            for item in (v if isinstance(v, list) else [v]):
                if tp and not str(item).startswith(str(tp)):
                    report.err(w, f"{type_name}.{f}: {item!r} is not a {target} id (expected prefix {tp!r})")
        rid = rec.get(id_field)
        if rid not in (None, ""):
            rid = str(rid)
            if prefix and not rid.startswith(str(prefix)):
                report.err(w, f"{type_name}.{id_field}: {rid!r} does not start with {prefix!r}")
            elif pattern and not pattern.match(rid):
                report.err(w, f"{type_name}.{id_field}: {rid!r} does not match {pattern.pattern}")
            if unique:
                if rid in seen:
                    report.err(w, f"{type_name}.{id_field}: duplicate id {rid!r} (first at {seen[rid]})")
                else:
                    seen[rid] = w
        exp = expected.get(rec.get("type")) if isinstance(rec.get("type"), str) else None
        if exp and rec.get("id") not in labeled:
            missing = [f for f in exp if rec.get(f) in (None, "", [], {})]
            if missing:
                report.warn(w, f"{type_name} type={rec.get('type')}: expected {', '.join(missing)} (fill via a label event)")
    return n


def read_records(path, fmt, container=None):
    """Yield (location, record). Unparseable lines are yielded as (location, YamlError)."""
    path = pathlib.Path(path)
    text = path.read_text(encoding="utf-8", errors="replace")
    if fmt == "jsonl":
        for n, line in enumerate(text.splitlines(), 1):
            if not line.strip():
                continue
            try:
                yield f":{n}", json.loads(line)
            except ValueError as e:
                yield f":{n}", YamlError(f"not JSON ({e})")
        return
    if fmt == "csv":
        for n, row in enumerate(csv.DictReader(text.splitlines()), 2):
            yield f":{n}", {k: v for k, v in row.items() if k is not None and v not in (None, "")}
        return
    if fmt == "json":
        try:
            data = json.loads(text)
        except ValueError as e:
            yield "", YamlError(f"not JSON ({e})")
            return
    elif fmt == "yaml":
        try:
            data = yaml_load(text)
        except YamlError as e:
            yield "", e
            return
    else:
        raise YamlError(f"format {fmt!r} is not parsed")
    if container:
        data = data.get(container) if isinstance(data, dict) else None
        if data is None:
            yield "", YamlError(f"no '{container}' key")
            return
    if isinstance(data, list):
        for i, rec in enumerate(data):
            yield f"[{i}]", rec
    elif isinstance(data, dict) and container:
        for k, rec in data.items():  # mapping of id -> record
            yield f"[{k}]", dict(rec, id=rec.get("id", k)) if isinstance(rec, dict) else rec
    elif data is not None:
        yield "", data


def check_file(path, type_name, onto, report, fmt=None, container=None, seen_ids=None):
    t = onto.types.get(type_name)
    if t is None:
        raise YamlError(f"unknown type {type_name!r}")
    st = t.get("store") or {}
    fmt = fmt or st.get("format") or pathlib.Path(path).suffix.lstrip(".")
    container = container if container is not None else st.get("container")
    good, n = [], 0
    for loc, rec in read_records(path, fmt, container):
        if isinstance(rec, Exception):
            report.err(f"{path}{loc}", str(rec))
        else:
            good.append((loc, rec))
    n = validate_records(type_name, good, onto, report, where=str(path), seen_ids=seen_ids)
    report.checked.append((str(path), type_name, n))
    return n


def scan(root, root_kind, onto, report, missing_ok=False):
    """Check every file under root that matches a store of the given root kind."""
    root = pathlib.Path(root).expanduser()
    if not root.is_dir():
        (report.warn if missing_ok else report.err)(str(root), "not a directory; skipped")
        return
    files = [p for p in root.rglob("*") if p.is_file() and ".git" not in p.relative_to(root).parts]
    claimed = set()
    for name, st in onto.stores(root_kind):
        if st.get("format") not in PARSED_FORMATS or not st.get("path"):
            continue
        pat = path_glob(str(st["path"]))
        seen = {}
        for p in sorted(files):
            rel = p.relative_to(root).as_posix()
            if fnmatch.fnmatch(rel, pat) and (rel, name) not in claimed:
                claimed.add((rel, name))
                check_file(p, name, onto, report, seen_ids=seen)


def store_table(onto):
    rows = ["| Type | Root | Path | Format | Append-only | Privacy | Status |", "|---|---|---|---|---|---|---|"]
    for name, st in onto.stores():
        rows.append(f"| {name} | {st.get('root', '')} | `{st.get('path', '')}` | {st.get('format', '')} | "
                    f"{'yes' if st.get('append_only') else 'no'} | {st.get('privacy', '')} | {st.get('status', '')} |")
    return "\n".join(rows)


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--ontology", help="ontology.yaml (default: schema/ontology.yaml next to this script, or $HARNESS_ONTOLOGY)")
    ap.add_argument("--root", help="harness-data dir to scan (default $HARNESS_DATA or ~/harness-data)")
    ap.add_argument("--project", action="append", default=[], help="project folder to scan (repeatable)")
    ap.add_argument("--vault", help="msg-vault dir to scan (only when asked; never default)")
    ap.add_argument("--file", action="append", default=[], help="check one file (needs --type)")
    ap.add_argument("--type", help="ontology type for --file")
    ap.add_argument("--stores", action="store_true", help="print the storage map table and exit")
    ap.add_argument("--json", action="store_true", help="JSON report on stdout")
    ap.add_argument("--strict", action="store_true", help="warnings count as errors")
    ap.add_argument("-q", "--quiet", action="store_true", help="errors only")
    a = ap.parse_args(argv)
    try:
        onto = Ontology.load(a.ontology)
    except (OSError, YamlError) as e:
        print(f"error: cannot load ontology: {e}", file=sys.stderr)
        return 2
    if a.stores:
        print(store_table(onto))
        return 0
    if a.file and not a.type:
        ap.error("--file needs --type")
    if a.type and a.type not in onto.types:
        print(f"error: unknown type {a.type!r}; known: {', '.join(onto.types)}", file=sys.stderr)
        return 2
    report = Report()
    try:
        if a.file:
            for f in a.file:
                check_file(f, a.type, onto, report)
        else:
            root = a.root or os.environ.get("HARNESS_DATA") or str(pathlib.Path.home() / "harness-data")
            scan(root, "harness-data", onto, report, missing_ok=bool(a.project or a.vault) and not a.root)
            for p in a.project:
                scan(p, "project", onto, report)
            if a.vault:
                scan(a.vault, "msg-vault", onto, report)
    except (OSError, YamlError) as e:
        print(f"error: {e}", file=sys.stderr)
        return 2
    failed = bool(report.errors) or (a.strict and bool(report.warnings))
    if a.json:
        print(json.dumps({"ontology_version": onto.version, "ok": not failed,
                          "checked": [{"file": f, "type": t, "records": n} for f, t, n in report.checked],
                          "errors": report.errors, "warnings": report.warnings}, ensure_ascii=False, indent=2))
    else:
        for f, t, n in report.checked:
            if not a.quiet:
                print(f"checked {f} as {t}: {n} record(s)")
        for e in report.errors:
            print(f"ERROR {e}")
        if not a.quiet:
            for w in report.warnings:
                print(f"warn  {w}")
        print(f"{len(report.errors)} error(s), {len(report.warnings)} warning(s) in "
              f"{sum(n for _, _, n in report.checked)} record(s) / {len(report.checked)} file(s)")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
