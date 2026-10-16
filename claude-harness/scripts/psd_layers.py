#!/usr/bin/env python3
"""List the layers of a PSD/PSB and write them as assets/assets.yaml entries.

Usage:
  python3 -I psd_layers.py FILE.psd                       # print YAML entries to stdout
  python3 -I psd_layers.py FILE.psd --manifest assets/assets.yaml [--export] [--owner X --license Y]

Needs psd-tools (`pip install psd-tools`; MIT). Without it, prints how to install and exits 2.
--export writes each pixel/smart-object layer as a lossless PNG (assets/layer/<id>.png, needs Pillow)
and each text layer's text to assets/text/<id>.txt, at native resolution. Without --export the
entry's `path` is null: the layer is listed, not extracted.

IDs are A-<sha8>-<n>, continuing after the highest n already in the manifest for this file, so
existing IDs are never renumbered. Re-running on a file already in the manifest is refused
unless --force. Rights default to `unknown`; they are never assumed.
The source file is opened read-only and never modified.
"""
import argparse
import datetime
import hashlib
import json
import pathlib
import re
import sys

VERSION = "0.1"
KIND_TO_TYPE = {"group": "layer", "pixel": "layer", "type": "text", "shape": "vector",
                "smartobject": "image", "psdimage": "layer"}


# ---------------------------------------------------------------- manifest helpers (shared with palette.py)

def sha256_file(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def q(value):
    """YAML scalar: null, or a JSON-style double-quoted string (valid YAML)."""
    if value is None:
        return "null"
    return json.dumps(str(value), ensure_ascii=False)


def entry_yaml(e):
    """One assets.yaml list item in the manifest layout of skills/asset-decompose/SKILL.md."""
    p, r = e["provenance"], e["rights"]
    lines = [
        f"- id: {e['id']}",
        f"  type: {e['type']}",
        f"  name: {q(e['name'])}",
        f"  source: {q(e['source'])}",
        f"  path: {q(e.get('path'))}",
        f"  provenance: {{extracted_by: {q(p['extracted_by'])}, on: {q(p['on'])}, from_sha256: {q(p['from_sha256'])}}}",
        f"  rights: {{owner: {q(r.get('owner', 'unknown'))}, license: {q(r.get('license', 'unknown'))}, notes: {q(r.get('notes', ''))}}}",
        "  variants: []",
        "  tags: [" + ", ".join(q(t) for t in e.get("tags", [])) + "]",
    ]
    return "\n".join(lines) + "\n"


def existing_indices(manifest_text, sha8):
    return [int(n) for n in re.findall(rf"^\s*-\s*id:\s*A-{re.escape(sha8)}-(\d+)\s*$", manifest_text, re.MULTILINE)]


def next_index(manifest_text, sha8):
    return max(existing_indices(manifest_text, sha8), default=0) + 1


def append_entries(manifest, entries):
    manifest = pathlib.Path(manifest)
    manifest.parent.mkdir(parents=True, exist_ok=True)
    text = manifest.read_text(encoding="utf-8") if manifest.exists() else ""
    sep = "" if not text or text.endswith("\n") else "\n"
    with open(manifest, "a", encoding="utf-8") as f:
        f.write(sep + "".join(entry_yaml(e) for e in entries))


# ---------------------------------------------------------------- layer walk

def _call(obj, name, default=None):
    v = getattr(obj, name, default)
    return v() if callable(v) else v


def walk(container, prefix=""):
    """Yield one dict per layer, depth-first in document order. Duck-typed on psd-tools layers."""
    for layer in container:
        name = str(getattr(layer, "name", "") or "(unnamed)")
        path = f"{prefix}/{name}" if prefix else name
        kind = str(getattr(layer, "kind", "") or "").lower()
        is_group = bool(_call(layer, "is_group", False))
        if is_group:
            kind = "group"
        blend = getattr(layer, "blend_mode", None)
        blend = getattr(blend, "name", blend)
        rec = {"layer": layer, "path": path, "name": name, "kind": kind or "other",
               "visible": bool(getattr(layer, "visible", True)), "opacity": getattr(layer, "opacity", None),
               "blend_mode": str(blend).lower() if blend is not None else None,
               "bbox": tuple(getattr(layer, "bbox", ()) or ()),
               "text": getattr(layer, "text", None) if kind == "type" else None}
        yield rec
        if is_group:
            yield from walk(layer, path)


def to_entries(records, sha, src_name, start, tool, today, owner="unknown", license="unknown",
               source_base=None):
    sha8 = sha[:8]
    base = source_base or f"knowledge/raw/{sha8}_{src_name}"
    out = []
    for n, r in enumerate(records, start):
        tags = [f"kind:{r['kind']}"]
        if not r["visible"]:
            tags.append("hidden")
        if r["bbox"]:
            tags.append("bbox:" + ",".join(str(v) for v in r["bbox"]))
        if r["blend_mode"] and r["blend_mode"] not in ("normal", "pass_through"):
            tags.append(f"blend:{r['blend_mode']}")
        if r["opacity"] is not None and r["opacity"] != 255:
            tags.append(f"opacity:{r['opacity']}")
        out.append({"id": f"A-{sha8}-{n}", "type": KIND_TO_TYPE.get(r["kind"], "other"), "name": r["name"],
                    "source": f"{base}#{r['path']}", "path": None,
                    "provenance": {"extracted_by": tool, "on": today, "from_sha256": sha},
                    "rights": {"owner": owner, "license": license, "notes": ""}, "tags": tags,
                    "_record": r})
    return out


def export(entries, manifest):
    """Write PNG/text files next to the manifest and set each entry's path. Returns problems."""
    root = pathlib.Path(manifest).resolve().parent          # <project>/assets
    problems = []
    for e in entries:
        r = e["_record"]
        try:
            if r["kind"] == "type" and r["text"] is not None:
                dest = root / "text" / f"{e['id']}.txt"
                dest.parent.mkdir(parents=True, exist_ok=True)
                dest.write_text(str(r["text"]), encoding="utf-8")
            elif r["kind"] in ("pixel", "smartobject", "shape"):
                img = r["layer"].composite()
                if img is None:
                    problems.append(f"{e['id']} {r['path']}: empty layer, not exported")
                    continue
                dest = root / e["type"] / f"{e['id']}.png"
                dest.parent.mkdir(parents=True, exist_ok=True)
                img.save(dest, format="PNG")
            else:
                continue
            e["path"] = f"{root.name}/{dest.relative_to(root).as_posix()}"
        except Exception as exc:   # one bad layer must not stop the rest
            problems.append(f"{e['id']} {r['path']}: {exc}")
    return problems


def _import_psd_tools():
    try:
        import psd_tools
        from psd_tools import PSDImage
        return PSDImage, getattr(psd_tools, "__version__", "unknown")
    except ImportError:
        return None, None


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("file")
    ap.add_argument("--manifest", help="append entries to this assets.yaml (else print to stdout)")
    ap.add_argument("--export", action="store_true", help="also write layer PNGs / text files (needs --manifest)")
    ap.add_argument("--owner", default="unknown")
    ap.add_argument("--license", default="unknown")
    ap.add_argument("--source-base", help="manifest source prefix (default knowledge/raw/<sha8>_<file>)")
    ap.add_argument("--force", action="store_true", help="append even if this file is already in the manifest")
    args = ap.parse_args(argv)

    PSDImage, version = _import_psd_tools()
    if PSDImage is None:
        print("psd_layers: psd-tools is not installed. Install it with `pip install psd-tools` "
              "(add Pillow for --export), then re-run.", file=sys.stderr)
        return 2
    if args.export and not args.manifest:
        print("psd_layers: --export needs --manifest", file=sys.stderr)
        return 2

    src = pathlib.Path(args.file)
    sha = sha256_file(src)
    text = pathlib.Path(args.manifest).read_text(encoding="utf-8") if args.manifest and pathlib.Path(args.manifest).exists() else ""
    if existing_indices(text, sha[:8]) and not args.force:
        print(f"psd_layers: {src.name} (A-{sha[:8]}-*) is already in {args.manifest}; use --force to append more",
              file=sys.stderr)
        return 1
    psd = PSDImage.open(src)
    records = list(walk(psd))
    entries = to_entries(records, sha, src.name, next_index(text, sha[:8]), f"psd-tools@{version}",
                         datetime.date.today().isoformat(), args.owner, args.license, args.source_base)
    problems = export(entries, args.manifest) if args.export else []
    if args.manifest:
        append_entries(args.manifest, entries)
        print(f"{len(entries)} layers from {src.name} ({getattr(psd, 'width', '?')}x{getattr(psd, 'height', '?')}, "
              f"{getattr(psd, 'color_mode', '?')}) "
              f"appended to {args.manifest}", file=sys.stderr)
    else:
        sys.stdout.write("".join(entry_yaml(e) for e in entries))
    for p in problems:
        print("problem: " + p, file=sys.stderr)
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main())
