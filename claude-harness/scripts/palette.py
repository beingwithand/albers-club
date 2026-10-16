#!/usr/bin/env python3
"""Extract a colour palette from an image: hex colours, pixel shares, roles and WCAG contrast.

Usage:
  python3 -I palette.py IMAGE [-k 6] [--method kmeans|mediancut] [--json]
  python3 -I palette.py IMAGE --manifest assets/assets.yaml [--owner X --license Y]

Reading the image needs Pillow (`pip install Pillow`); without it the script says so and exits 2.
The clustering itself is pure Python: the image is downsampled to at most --max-side pixels per
side, mostly transparent pixels (alpha < 128) are dropped, then
  kmeans     k-means++ seeding, 3 restarts keeping the lowest error, up to 30 Lloyd iterations each
             (fixed --seed, so runs are reproducible)
  mediancut  split the box with the widest channel range at its median until there are k boxes
Roles (heuristic, for a first read; a designer decides):
  background  the largest cluster
  text        the colour with the highest WCAG contrast against the background
  accent      the most saturated remaining colour
  primary, secondary   the largest remaining clusters; the rest are `support`
--manifest writes the palette as JSON to assets/palette/<id>.json and appends one `palette`
entry to assets.yaml (same layout and ID rules as psd_layers.py). The image is never modified.
"""
import argparse
import colorsys
import datetime
import importlib.util
import json
import pathlib
import random
import sys

VERSION = "0.1"


def _psd_helpers():
    spec = importlib.util.spec_from_file_location("psd_layers", pathlib.Path(__file__).resolve().parent / "psd_layers.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def _import_pil():
    try:
        from PIL import Image
        import PIL
        return Image, getattr(PIL, "__version__", "unknown")
    except ImportError:
        return None, None


# ---------------------------------------------------------------- colour maths

def hex_of(rgb):
    return "#{:02x}{:02x}{:02x}".format(*(max(0, min(255, int(round(c)))) for c in rgb))


def rel_luminance(rgb):
    def ch(c):
        c = c / 255
        return c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4
    r, g, b = (ch(c) for c in rgb)
    return 0.2126 * r + 0.7152 * g + 0.0722 * b


def contrast(a, b):
    la, lb = sorted((rel_luminance(a), rel_luminance(b)), reverse=True)
    return (la + 0.05) / (lb + 0.05)


def saturation(rgb):
    _, s, v = colorsys.rgb_to_hsv(*(c / 255 for c in rgb))
    return s * v          # chroma-like: grey and near-black score low


def _dist2(a, b):
    return (a[0] - b[0]) ** 2 + (a[1] - b[1]) ** 2 + (a[2] - b[2]) ** 2


def _mean(points):
    n = len(points)
    return tuple(sum(p[i] for p in points) / n for i in range(3))


# ---------------------------------------------------------------- clustering

def kmeans(pixels, k=6, iters=30, seed=0, n_init=3):
    """Return [(centre_rgb, count)] sorted by count desc. pixels: list of (r, g, b).
    Runs n_init seeded restarts and keeps the one with the lowest within-cluster error."""
    pixels = [tuple(p[:3]) for p in pixels]
    if not pixels:
        return []
    uniq = list(dict.fromkeys(pixels))
    if len(uniq) <= k:
        counts = {}
        for p in pixels:
            counts[p] = counts.get(p, 0) + 1
        return sorted(((tuple(float(c) for c in p), n) for p, n in counts.items()), key=lambda t: -t[1])
    best = None
    for run in range(max(1, n_init)):
        result, err = _kmeans_once(pixels, k, iters, random.Random(seed * 1000 + run))
        if best is None or err < best[1]:
            best = (result, err)
    return best[0]


def _kmeans_once(pixels, k, iters, rng):
    centres = [rng.choice(pixels)]
    while len(centres) < k:                      # k-means++ seeding
        d = [min(_dist2(p, c) for c in centres) for p in pixels]
        total = sum(d)
        if total == 0:
            break
        r, acc = rng.uniform(0, total), 0.0
        for p, w in zip(pixels, d):
            acc += w
            if acc >= r:
                centres.append(p)
                break
    centres = [tuple(float(x) for x in c) for c in centres]
    assign = [0] * len(pixels)
    for _ in range(iters):
        changed = False
        for i, p in enumerate(pixels):
            j = min(range(len(centres)), key=lambda j: _dist2(p, centres[j]))
            if j != assign[i]:
                assign[i], changed = j, True
        groups = [[] for _ in centres]
        for p, j in zip(pixels, assign):
            groups[j].append(p)
        centres = [_mean(g) if g else centres[j] for j, g in enumerate(groups)]
        if not changed and _ > 0:
            break
    counts = [0] * len(centres)
    for j in assign:
        counts[j] += 1
    err = sum(_dist2(p, centres[j]) for p, j in zip(pixels, assign))
    return sorted(((c, n) for c, n in zip(centres, counts) if n), key=lambda t: -t[1]), err


def median_cut(pixels, k=6):
    """Return [(mean_rgb, count)] sorted by count desc."""
    pixels = [tuple(p[:3]) for p in pixels]
    if not pixels:
        return []
    boxes = [pixels]
    while len(boxes) < k:
        def spread(box):
            return max(max(p[i] for p in box) - min(p[i] for p in box) for i in range(3))
        splittable = [b for b in boxes if len(b) > 1 and spread(b) > 0]
        if not splittable:
            break
        box = max(splittable, key=lambda b: (spread(b), len(b)))
        ch = max(range(3), key=lambda i: max(p[i] for p in box) - min(p[i] for p in box))
        box_sorted = sorted(box, key=lambda p: p[ch])
        mid = len(box_sorted) // 2
        boxes.remove(box)
        boxes += [box_sorted[:mid], box_sorted[mid:]]
    return sorted(((_mean(b), len(b)) for b in boxes if b), key=lambda t: -t[1])


def assign_roles(clusters):
    """clusters: [(rgb, count)] -> list of dicts with hex, rgb, share, role, contrast_vs_background."""
    total = sum(n for _, n in clusters) or 1
    cols = [{"rgb": tuple(int(round(c)) for c in rgb), "share": n / total} for rgb, n in clusters]
    cols.sort(key=lambda c: -c["share"])
    for c in cols:
        c["hex"] = hex_of(c["rgb"])
        c["role"] = None
    if not cols:
        return cols
    bg = cols[0]
    bg["role"] = "background"
    rest = cols[1:]
    if rest:
        text = max(rest, key=lambda c: contrast(c["rgb"], bg["rgb"]))
        text["role"] = "text"
        free = [c for c in rest if c["role"] is None]
        if free:
            accent = max(free, key=lambda c: saturation(c["rgb"]))
            if saturation(accent["rgb"]) > 0.25:
                accent["role"] = "accent"
        for role in ("primary", "secondary"):
            free = [c for c in rest if c["role"] is None]
            if free:
                free[0]["role"] = role
        for c in rest:
            c["role"] = c["role"] or "support"
    for c in cols:
        c["contrast_vs_background"] = round(contrast(c["rgb"], bg["rgb"]), 2)
        c["share"] = round(c["share"], 4)
        c["rgb"] = list(c["rgb"])
    return cols


# ---------------------------------------------------------------- image IO

def load_pixels(path, Image, max_side=96):
    with Image.open(path) as im:
        im = im.convert("RGBA")
        im.thumbnail((max_side, max_side))
        getter = getattr(im, "get_flattened_data", None) or im.getdata   # getdata is deprecated in Pillow 12+
        data = getter()
        return [p[:3] for p in data if p[3] >= 128], im.size


def extract(path, Image, k=6, method="kmeans", max_side=96, seed=0):
    pixels, size = load_pixels(path, Image, max_side)
    clusters = kmeans(pixels, k, seed=seed) if method == "kmeans" else median_cut(pixels, k)
    return assign_roles(clusters), {"sampled_pixels": len(pixels), "sample_size": list(size)}


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("image")
    ap.add_argument("-k", type=int, default=6)
    ap.add_argument("--method", choices=("kmeans", "mediancut"), default="kmeans")
    ap.add_argument("--max-side", type=int, default=96)
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--manifest", help="append a palette entry to this assets.yaml")
    ap.add_argument("--owner", default="unknown")
    ap.add_argument("--license", default="unknown")
    ap.add_argument("--source-base", help="manifest source prefix (default knowledge/raw/<sha8>_<file>)")
    args = ap.parse_args(argv)
    if args.k < 1:
        ap.error("-k must be at least 1")

    Image, pil_version = _import_pil()
    if Image is None:
        print("palette: Pillow is not installed, so the image can't be read. Install it with "
              "`pip install Pillow`, then re-run. (The clustering itself needs nothing else.)", file=sys.stderr)
        return 2
    colours, info = extract(args.image, Image, args.k, args.method, args.max_side, args.seed)
    tool = f"palette.py@{VERSION} ({args.method}, Pillow@{pil_version})"

    if args.manifest:
        h = _psd_helpers()
        src = pathlib.Path(args.image)
        sha = h.sha256_file(src)
        manifest = pathlib.Path(args.manifest)
        text = manifest.read_text(encoding="utf-8") if manifest.exists() else ""
        aid = f"A-{sha[:8]}-{h.next_index(text, sha[:8])}"
        dest = manifest.resolve().parent / "palette" / f"{aid}.json"
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_text(json.dumps({"id": aid, "method": args.method, "k": args.k, **info, "colors": colours},
                                   ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        base = args.source_base or f"knowledge/raw/{sha[:8]}_{src.name}"
        entry = {"id": aid, "type": "palette", "name": f"palette k={args.k} ({args.method})",
                 "source": f"{base}#palette", "path": f"{dest.parent.parent.name}/palette/{aid}.json",
                 "provenance": {"extracted_by": tool, "on": datetime.date.today().isoformat(), "from_sha256": sha},
                 "rights": {"owner": args.owner, "license": args.license, "notes": ""},
                 "tags": [f"{c['role']}:{c['hex']}" for c in colours]}
        h.append_entries(manifest, [entry])
        print(f"{aid} appended to {manifest}; palette at {dest}", file=sys.stderr)

    if args.json:
        print(json.dumps({"image": args.image, "tool": tool, **info, "colors": colours}, ensure_ascii=False, indent=2))
    else:
        for c in colours:
            print(f"{c['hex']}  {c['role']:<10} {c['share'] * 100:5.1f}%  contrast vs bg {c['contrast_vs_background']}:1")
    return 0


if __name__ == "__main__":
    sys.exit(main())
