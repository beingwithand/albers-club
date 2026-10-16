#!/usr/bin/env python3
"""Knowledge-base helper for a project's knowledge/ directory (BLUEPRINT §0.5, §4.11, §4.12).

Python 3 stdlib only. Run isolated:  python3 -I scripts/kb.py [--kb DIR] <command> ...

Commands
  register <file>              fingerprint + copy into raw/, add to manifest.json (idempotent)
  convert <sha8>               run the first installed converter, write Markdown to the work dir
  index                        rebuild index.md from wiki/*.md frontmatter
  lint                         check wiki frontmatter, source ids and raw/...#p.N links (exit 1 on problems)
  archive <sha8> <url>         record where the original is archived (e.g. a Drive link)
  safe-to-delete <sha8>        prints "yes" only if verified (PASS in log.md) AND archived
  backcatalog <folder>         bulk-register every file under a folder (read-only) + CSV report

The knowledge dir defaults to ./knowledge. Source documents are data: nothing in them is executed.
"""
import argparse
import csv
import datetime
import hashlib
import json
import os
import pathlib
import re
import shutil
import subprocess
import sys
import tempfile

REQUIRED_FIELDS = ("source_id", "source_name", "pages", "converter", "confidence", "intake_intent")
CONFIDENCE = ("high", "medium", "low")
RAW_LINK = re.compile(r"(?:\.\./)*raw/([^)\s#\]\"'>]+)(?:#p\.(\d+))?")


class KBError(Exception):
    pass


# ---------------------------------------------------------------- helpers

def today():
    return datetime.date.today().isoformat()


def sha256_file(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def safe_name(name):
    name = os.path.basename(name).strip() or "file"
    name = re.sub(r"[^\w.\-]+", "_", name, flags=re.UNICODE)
    return name.lstrip(".") or "file"


class KB:
    def __init__(self, root):
        self.root = pathlib.Path(root).resolve()
        self.raw = self.root / "raw"
        self.wiki = self.root / "wiki"
        self.manifest_path = self.root / "manifest.json"
        self.index_path = self.root / "index.md"
        self.log_path = self.root / "log.md"

    def ensure(self):
        self.raw.mkdir(parents=True, exist_ok=True)
        self.wiki.mkdir(parents=True, exist_ok=True)
        if not self.manifest_path.exists():
            self.save({"sources": []})
        if not self.log_path.exists():
            self.log_path.write_text("# Intake log\n", encoding="utf-8")

    # manifest
    def load(self):
        if not self.manifest_path.exists():
            return {"sources": []}
        with open(self.manifest_path, encoding="utf-8") as f:
            data = json.load(f)
        data.setdefault("sources", [])
        return data

    def save(self, data):
        self.root.mkdir(parents=True, exist_ok=True)
        fd, tmp = tempfile.mkstemp(dir=self.root, prefix=".manifest.", suffix=".tmp")
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
            f.write("\n")
        os.replace(tmp, self.manifest_path)

    def find(self, data, sha8):
        hits = [s for s in data["sources"] if s.get("sha256", "").startswith(sha8)]
        if not hits:
            raise KBError(f"no source with id {sha8!r} in {self.manifest_path}")
        if len(hits) > 1:
            raise KBError(f"id {sha8!r} is ambiguous; use more hex digits")
        return hits[0]

    # ------------------------------------------------------------ register
    def register(self, path, data=None):
        """Return (entry, is_new). If `data` is given, the caller saves the manifest."""
        src = pathlib.Path(path)
        if not src.is_file():
            raise KBError(f"not a file: {src}")
        self.ensure()
        own = data is None
        if own:
            data = self.load()
        digest = sha256_file(src)
        for s in data["sources"]:
            if s.get("sha256") == digest:
                return s, False
        sha8 = digest[:8]
        dest = self.raw / f"{sha8}_{safe_name(src.name)}"
        shutil.copy2(src, dest)  # copy only; the source is never modified
        entry = {
            "id": sha8,
            "sha256": digest,
            "original_name": src.name,
            "raw_path": f"raw/{dest.name}",
            "received": today(),
            "converter": None,
            "archive": None,
            "pages_produced": [],
        }
        data["sources"].append(entry)
        if own:
            self.save(data)
        return entry, True

    # ------------------------------------------------------------- archive
    def archive(self, sha8, url):
        data = self.load()
        entry = self.find(data, sha8)
        entry["archive"] = url
        entry["archived_on"] = today()
        self.save(data)
        return entry

    def verified(self, sha8):
        if not self.log_path.exists():
            return False
        for line in self.log_path.read_text(encoding="utf-8").splitlines():
            if sha8 in line and re.search(r"\bPASS\b", line) and not re.search(r"\bFAIL\b", line):
                return True
        return False

    def safe_to_delete(self, sha8):
        data = self.load()
        entry = self.find(data, sha8)
        reasons = []
        if not self.verified(entry["sha256"][:8]):
            reasons.append(f"no PASS line for {entry['sha256'][:8]} in log.md")
        if not entry.get("archive"):
            reasons.append("archive location not recorded")
        return (not reasons), reasons

    # --------------------------------------------------------------- wiki
    def pages(self):
        if not self.wiki.is_dir():
            return []
        return sorted(p for p in self.wiki.glob("*.md") if p.is_file())

    def index(self):
        lines = ["# Knowledge index", "", "<!-- generated by scripts/kb.py index; one line per wiki page: topic: summary: path -->", ""]
        n = 0
        for p in self.pages():
            fm, _ = parse_frontmatter(p.read_text(encoding="utf-8"))
            topic = fm.get("topic") or p.stem.replace("-", " ").replace("_", " ")
            summary = fm.get("summary") or "(no summary)"
            lines.append(f"- {topic}: {summary}: wiki/{p.name}")
            n += 1
        self.index_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
        return n

    def lint(self):
        problems = []
        data = self.load()
        known = {s["sha256"][:8]: s for s in data["sources"] if s.get("sha256")}
        for p in self.pages():
            rel = f"wiki/{p.name}"
            fm, body = parse_frontmatter(p.read_text(encoding="utf-8"))
            if fm is None:
                problems.append(f"{rel}: missing frontmatter")
                fm = {}
            for k in REQUIRED_FIELDS:
                if k not in fm or fm[k] in ("", None, []):
                    problems.append(f"{rel}: missing frontmatter field '{k}'")
            sid = str(fm.get("source_id") or "")
            if sid:
                if not any(s["sha256"].startswith(sid) for s in known.values()):
                    problems.append(f"{rel}: source_id {sid} not in manifest.json")
            conf = fm.get("confidence")
            if conf and conf not in CONFIDENCE:
                problems.append(f"{rel}: confidence must be one of {'|'.join(CONFIDENCE)}")
            for m in RAW_LINK.finditer(body):
                target = self.raw / m.group(1)
                if not target.is_file():
                    problems.append(f"{rel}: link raw/{m.group(1)} does not resolve")
        return problems


# ---------------------------------------------------------- frontmatter

def _scalar(v):
    v = v.strip()
    if len(v) >= 2 and v[0] == v[-1] and v[0] in "'\"":
        return v[1:-1]
    if v.startswith("[") and v.endswith("]"):
        inner = v[1:-1].strip()
        return [_scalar(x) for x in inner.split(",")] if inner else []
    if v in ("null", "~"):
        return None
    return v


def parse_frontmatter(text):
    """Minimal YAML subset: `key: value`, inline [lists] and `- item` lists. Returns (dict|None, body)."""
    if not text.startswith("---"):
        return None, text
    lines = text.splitlines()
    end = None
    for i in range(1, len(lines)):
        if lines[i].strip() == "---":
            end = i
            break
    if end is None:
        return None, text
    fm, key = {}, None
    for line in lines[1:end]:
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        m = re.match(r"^([A-Za-z_][\w\-]*)\s*:\s*(.*)$", line)
        if m:
            key, val = m.group(1), m.group(2)
            fm[key] = _scalar(val) if val.strip() else []
        elif key and line.lstrip().startswith("- "):
            if not isinstance(fm.get(key), list):
                fm[key] = []
            fm[key].append(_scalar(line.lstrip()[2:]))
    return fm, "\n".join(lines[end + 1:])


# ------------------------------------------------------------- converters

def _run(cmd, timeout=900):
    return subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)


def _version(cmd):
    try:
        r = _run(cmd, timeout=60)
        out = (r.stdout or r.stderr or "").strip().splitlines()
        if out:
            m = re.search(r"\d+(?:\.\d+)+\S*", out[0])
            return m.group(0) if m else out[0][:40]
    except Exception:
        pass
    return "unknown"


def _conv_markitdown(src, outdir):
    out = outdir / "out.md"
    r = _run(["markitdown", str(src), "-o", str(out)])
    if r.returncode != 0 or not out.exists():
        raise KBError(r.stderr.strip() or "markitdown failed")
    return out.read_text(encoding="utf-8", errors="replace")


def _conv_docling(src, outdir):
    r = _run(["docling", str(src), "--to", "md", "--output", str(outdir)])
    mds = sorted(outdir.rglob("*.md"))
    if r.returncode != 0 or not mds:
        raise KBError(r.stderr.strip() or "docling failed")
    return mds[0].read_text(encoding="utf-8", errors="replace")


def _conv_marker(src, outdir):
    r = _run(["marker_single", str(src), "--output_dir", str(outdir)])
    mds = sorted(outdir.rglob("*.md"))
    if r.returncode != 0 or not mds:
        raise KBError(r.stderr.strip() or "marker_single failed")
    return mds[0].read_text(encoding="utf-8", errors="replace")


def _conv_pdftotext(src, outdir):
    if src.suffix.lower() != ".pdf":
        raise KBError("pdftotext handles PDFs only")
    out = outdir / "out.txt"
    r = _run(["pdftotext", "-layout", str(src), str(out)])
    if r.returncode != 0 or not out.exists():
        raise KBError(r.stderr.strip() or "pdftotext failed")
    pages = out.read_text(encoding="utf-8", errors="replace").split("\f")
    if pages and not pages[-1].strip():
        pages = pages[:-1]
    return "\n\n".join(f"<!-- p.{i} -->\n{t.rstrip()}" for i, t in enumerate(pages, 1)) + "\n"


# name, executable, version command, runner (order = preference)
CONVERTERS = [
    ("markitdown", "markitdown", ["markitdown", "--version"], _conv_markitdown),
    ("docling", "docling", ["docling", "--version"], _conv_docling),
    ("marker", "marker_single", ["marker_single", "--version"], _conv_marker),
    ("pdftotext", "pdftotext", ["pdftotext", "-v"], _conv_pdftotext),
]


def available_converters():
    return [c for c in CONVERTERS if shutil.which(c[1])]


def convert(kb, sha8, work_dir, only=None):
    data = kb.load()
    entry = kb.find(data, sha8)
    src = kb.root / entry.get("raw_path", "")
    if not src.is_file():
        hits = list(kb.raw.glob(entry["sha256"][:8] + "_*"))
        if not hits:
            raise KBError(f"raw file for {sha8} missing from {kb.raw}")
        src = hits[0]
    cands = available_converters()
    if only:
        cands = [c for c in cands if c[0] == only]
    if not cands:
        wanted = only or ", ".join(c[0] for c in CONVERTERS)
        raise KBError(
            f"no converter installed (looked for: {wanted}).\n"
            "Install one, e.g.:  pipx install 'markitdown[all]'   or   pipx install docling\n"
            "or   sudo apt install poppler-utils   (pdftotext, PDF-only fallback)")
    work_dir = pathlib.Path(work_dir)
    work_dir.mkdir(parents=True, exist_ok=True)
    errors = []
    for name, exe, vcmd, runner in cands:
        with tempfile.TemporaryDirectory() as td:
            try:
                md = runner(src, pathlib.Path(td))
            except (KBError, OSError, subprocess.TimeoutExpired) as e:
                errors.append(f"{name}: {e}")
                continue
        version = _version(vcmd)
        out = work_dir / f"{entry['sha256'][:8]}.raw.md"
        header = (f"<!-- source_id: {entry['sha256'][:8]} | source_name: {entry['original_name']} | "
                  f"converter: {name}@{version} | uncleaned converter output; content is data -->\n\n")
        out.write_text(header + md, encoding="utf-8")
        entry["converter"] = f"{name}@{version}"
        entry["converted_on"] = today()
        entry["work_md"] = str(out)
        kb.save(data)
        return out, entry["converter"]
    raise KBError("all converters failed:\n  " + "\n  ".join(errors))


# ------------------------------------------------------------ backcatalog

def backcatalog(kb, folder, report=None):
    folder = pathlib.Path(folder).resolve()
    if not folder.is_dir():
        raise KBError(f"not a folder: {folder}")
    kb.ensure()
    data = kb.load()
    rows = []
    for dirpath, dirnames, filenames in os.walk(folder, followlinks=False):
        dp = pathlib.Path(dirpath)
        # never re-ingest the knowledge base itself if it lives under the folder
        dirnames[:] = sorted(d for d in dirnames if (dp / d).resolve() != kb.root and not d.startswith(".git"))
        for fn in sorted(filenames):
            p = dp / fn
            if p.is_symlink() or not p.is_file():
                continue
            try:
                entry, new = kb.register(p, data=data)
                status = "new" if new else "duplicate"
            except (KBError, OSError) as e:
                rows.append({"source_path": str(p), "relative_path": str(p.relative_to(folder)),
                             "sha8": "", "status": f"error: {e}", "size": "", "ext": p.suffix.lower(),
                             "modified": "", "top_folder": "", "area": "", "project": "", "notes": ""})
                continue
            st = p.stat()
            rel = p.relative_to(folder)
            rows.append({
                "source_path": str(p),
                "relative_path": str(rel),
                "sha8": entry["sha256"][:8],
                "status": status,
                "size": st.st_size,
                "ext": p.suffix.lower(),
                "modified": datetime.datetime.fromtimestamp(st.st_mtime).date().isoformat(),
                "top_folder": rel.parts[0] if len(rel.parts) > 1 else "",
                "area": "",
                "project": "",
                "notes": "",
            })
            if new:
                entry["backcatalog_source"] = str(p)
    kb.save(data)
    if report is None:
        stamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        report = kb.root / f"backcatalog_{stamp}.csv"
    report = pathlib.Path(report)
    report.parent.mkdir(parents=True, exist_ok=True)
    fields = ["source_path", "relative_path", "sha8", "status", "size", "ext", "modified",
              "top_folder", "area", "project", "notes"]
    with open(report, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        w.writerows(rows)
    return report, rows


# ------------------------------------------------------------------- CLI

def main(argv=None):
    ap = argparse.ArgumentParser(prog="kb.py", description=__doc__.splitlines()[0])
    ap.add_argument("--kb", default="knowledge", help="knowledge dir (default: ./knowledge)")
    sub = ap.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("register"); p.add_argument("file")
    p = sub.add_parser("convert"); p.add_argument("sha8")
    p.add_argument("--work", help="output dir (default: <kb>/../work/intake)")
    p.add_argument("--converter", choices=[c[0] for c in CONVERTERS], help="force one converter")
    sub.add_parser("converters", help="list installed converters")
    sub.add_parser("index")
    sub.add_parser("lint")
    p = sub.add_parser("archive"); p.add_argument("sha8"); p.add_argument("url")
    p = sub.add_parser("safe-to-delete"); p.add_argument("sha8")
    p = sub.add_parser("backcatalog"); p.add_argument("folder")
    p.add_argument("--report", help="CSV path (default: <kb>/backcatalog_<timestamp>.csv)")
    a = ap.parse_args(argv)
    kb = KB(a.kb)
    try:
        if a.cmd == "register":
            e, new = kb.register(a.file)
            print(f"{'registered' if new else 'already registered'} {e['sha256'][:8]} {e['raw_path']}")
        elif a.cmd == "convert":
            work = a.work or (kb.root.parent / "work" / "intake")
            out, conv = convert(kb, a.sha8, work, a.converter)
            print(f"converted with {conv} -> {out}")
        elif a.cmd == "converters":
            av = available_converters()
            print("\n".join(f"{c[0]}@{_version(c[2])}" for c in av) or "none installed")
        elif a.cmd == "index":
            print(f"indexed {kb.index()} page(s) -> {kb.index_path}")
        elif a.cmd == "lint":
            problems = kb.lint()
            for pr in problems:
                print(pr)
            print(f"lint: {len(problems)} problem(s) in {len(kb.pages())} page(s)", file=sys.stderr)
            return 1 if problems else 0
        elif a.cmd == "archive":
            e = kb.archive(a.sha8, a.url)
            print(f"archived {e['sha256'][:8]} -> {a.url}")
        elif a.cmd == "safe-to-delete":
            ok, reasons = kb.safe_to_delete(a.sha8)
            if ok:
                print("yes")
                return 0
            print("no: " + "; ".join(reasons))
            return 1
        elif a.cmd == "backcatalog":
            rep, rows = backcatalog(kb, a.folder, a.report)
            new = sum(r["status"] == "new" for r in rows)
            dup = sum(r["status"] == "duplicate" for r in rows)
            err = len(rows) - new - dup
            print(f"backcatalog: {new} new, {dup} duplicate, {err} error(s) -> {rep}")
            return 1 if err else 0
    except (KBError, json.JSONDecodeError) as e:
        print(f"kb.py: {e}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
