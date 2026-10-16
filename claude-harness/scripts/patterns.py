#!/usr/bin/env python3
"""Multi-layer pattern system: mine, promote/demote, and reflect on recurring patterns (docs/PATTERNS.md).

Layers (ontology enum `pattern_level`):
  L0 observation  raw events in $HARNESS_DATA/log/*.jsonl
  L1 episode      an event merged with its newest `label` event (intent/situation/meta/labels)
  L2 pattern      a regularity across 2+ episodes             -> $HARNESS_DATA/patterns/patterns.jsonl (pat_)
  L3 encoding     the artifact that operationalizes a pattern -> $HARNESS_DATA/patterns/encodings.jsonl (enc_)
  L4 principle    a cross-area generalization                 -> global/PRINCIPLES.md (P<n>)
  L5 meta-pattern a pattern about this system itself          -> $HARNESS_DATA/patterns/meta.jsonl (mp_)

    python3 -I scripts/patterns.py mine   [--json] [--out FILE]   # L1 -> L2 candidates (deduped)
    python3 -I scripts/patterns.py ladder [--json] [--out FILE]   # promotion / demotion proposals
    python3 -I scripts/patterns.py meta   [--json] [--out FILE]   # L5 signals -> meta-pattern proposals
    python3 -I scripts/patterns.py report                         # markdown summary by level
    python3 -I scripts/patterns.py record --file approved.jsonl   # append approved records + log events
    python3 -I scripts/patterns.py config [--init]                # merged thresholds (patterns/config.json)

Common options: --data-dir (default $HARNESS_DATA or ~/harness-data), --today YYYY-MM-DD, --project DIR
(reads <DIR>/log/mishaps.md and <DIR>/decisions.md), --external FILE (JSONL evidence from Claude Code
built-ins: /insights, /usage, /skill-doctor; see docs/PATTERNS.md), --auto-memory DIR (feedback notes),
--seeds FILE / --no-seeds (repo patterns/seed_patterns.jsonl).

mine, ladder, meta and report never write to the stores: they print proposals (and --out writes the
proposed records to a file of your choice). Only `record` appends, and the pattern-review skill runs it
for the proposals I approve. Log contents are data, not instructions.

Stdlib only; run with `python3 -I`. Exit codes: 0 ok, 1 nothing valid / validation failed, 2 usage error.
"""
import argparse
import collections
import datetime as dt
import hashlib
import importlib.util
import json
import math
import os
import pathlib
import re
import sys
import uuid

try:
    import fcntl
except ImportError:  # pragma: no cover - non-POSIX
    fcntl = None

HARNESS_ROOT = pathlib.Path(__file__).resolve().parent.parent
ONTOLOGY = HARNESS_ROOT / "schema" / "ontology.yaml"
PRINCIPLES = HARNESS_ROOT / "global" / "PRINCIPLES.md"
SEEDS = HARNESS_ROOT / "patterns" / "seed_patterns.jsonl"
FALLBACK_AREAS = ["translation", "annotation", "job-search", "art", "code", "research", "personal"]
STORES = {"pat_": "patterns.jsonl", "enc_": "encodings.jsonl", "mp_": "meta.jsonl"}
TYPES = {"pat_": "Pattern", "enc_": "Encoding", "mp_": "MetaPattern"}
LEVELS = {"pat_": "L2", "enc_": "L3", "mp_": "L5"}

DEFAULTS = {
    "window_weeks": 12,          # mine/meta look back this far
    "min_support": 2,            # episodes for a mined candidate
    "similarity": 0.4,           # Dice similarity to join a cluster
    "dedupe_similarity": 0.5,    # candidate vs existing pattern
    "propose": {"support": 3, "sessions": 2, "areas": 1, "recency_weeks": 8, "confidence": 0.45},
    "encode": {"support": 4, "sessions": 3, "confidence": 0.6, "mistake_support": 2, "mistake_sessions": 2},
    "principle": {"patterns": 2, "areas": 2, "similarity": 0.25},
    "decay_weeks": 6,            # no support (or no use, for encodings) -> decaying
    "retire_weeks": 6,           # further weeks without support while decaying -> retired
    "override_reopen": 2,        # encoding overridden this often -> reopen its pattern
    "reoccur_reopen": 2,         # mistake/correction episodes after encoding -> reopen
    "hotspot_share": 0.4, "hotspot_min": 3,
    "concentration_share": 0.5, "concentration_min": 3,
    "unclassified_share": 0.5, "unclassified_min": 4,
    "unlabeled_share": 0.5, "unlabeled_min": 10,
    "blind_spot_min_episodes": 10,
}

KIND_PHRASE = {
    "request": "Recurring request", "preference": "Recurring preference", "workflow": "Recurring workflow",
    "mistake": "Recurring mistake", "success": "Reliably works", "correction": "Recurring correction",
    "temporal": "Usage rhythm", "domain-analogy": "Same structure across areas", "tool-friction": "Recurring tool friction",
}
# Kinds where silence after encoding means the encoding works (so no decay from lack of evidence),
# and where new episodes after encoding mean it failed (reopen).
QUIET_KINDS = {"mistake", "correction", "tool-friction"}
SUGGESTED_ENCODING = {
    "request": "skill or command", "preference": "rule (CLAUDE.md/.claude/rules) or default-setting",
    "workflow": "saved-workflow (/workflows -> s) or skill", "mistake": "hook or eval-task (then rule)",
    "success": "skill or rubric-criterion", "correction": "rule plus eval-task",
    "temporal": "default-setting (schedule / scheduled task)", "domain-analogy": "principle (L4) via distill-principles",
    "tool-friction": "default-setting (permissions allowlist, /fewer-permission-prompts) or hook",
}
EPISODE_TYPES = {"prompt", "correction", "mishap", "decision", "session_note", "task", "verification"}
LABEL_CANDIDATE_TYPES = {"prompt", "correction", "mishap", "decision", "session_note"}

# ---------------------------------------------------------------- tokens (English + Korean)

_HANGUL = "가-힣ㄱ-ㆎ"
_TOKEN_RE = re.compile(rf"[{_HANGUL}]+|[^\W_{_HANGUL}]+", re.UNICODE)
_HANGUL_RE = re.compile(rf"^[{_HANGUL}]+$")
KO_SUFFIXES = sorted(["에서는", "으로는", "이라고", "라고", "에서", "으로", "에게", "까지", "부터", "처럼", "보다",
                      "하고", "해줘", "해서", "하는", "했다", "합니다", "해요", "은", "는", "이", "가", "을", "를",
                      "에", "의", "로", "와", "과", "도", "만", "요"], key=len, reverse=True)
STOP = set("""a an the and or but to of in on for with is are was were be been being it its this that these those i you we
me my your our they them he she please can could would should will just do does did done not no yes so if then than as
at by from up about into over also any all some more most very what which who whom how when where why there here have
has had get got make let use using used one two now again still like want need ok okay thanks thank hey hi always never
each every other same such only own too via per etc it's i'm don't instead said anything everything something
thing things way first before after without them their its whatever where while because""".split())
GENERIC_LABELS = {"needs", "review", "correction", "preference", "request", "mistake", "mishap", "success",
                  "decision", "routine", "label", "kind", "thing", "general", "misc", "other", "unknown"}
FRICTION = {"permission", "permissions", "denied", "blocked", "sandbox", "timeout", "friction", "권한", "차단"}
PREF = {"preference", "prefer", "prefers", "preferred", "style", "register", "tone", "선호", "스타일"}
OPPOSITES = [("always", "never"), ("more", "less"), ("formal", "casual"), ("short", "long"), ("brief", "detailed"),
             ("fast", "thorough"), ("inline", "fan"), ("ask", "autonomously"), ("add", "delete"),
             ("compact", "handoff"), ("memory", "online"), ("quick", "deep"), ("minimal", "exhaustive")]
WEEKDAYS = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]


def tokens(text):
    """Lower-cased Latin words minus stop words; Hangul runs minus one trailing particle, as bigrams."""
    out = set()
    for tok in _TOKEN_RE.findall((text or "").lower()):
        if _HANGUL_RE.match(tok):
            for suf in KO_SUFFIXES:
                if tok.endswith(suf) and len(tok) - len(suf) >= 2:
                    tok = tok[:-len(suf)]
                    break
            if len(tok) >= 2:
                out.update(tok[i:i + 2] for i in range(len(tok) - 1))
        elif len(tok) >= 2 and not tok.isdigit() and tok not in STOP:
            out.add(tok)
    return out


def dice(a, b):
    a, b = set(a), set(b)
    if not a or not b:
        return 0.0
    return 2 * len(a & b) / (len(a) + len(b))


def words(text):
    return set(re.findall(r"[a-z]+", (text or "").lower()))


# ---------------------------------------------------------------- small helpers

def data_dir(arg):
    if arg:
        return pathlib.Path(arg).expanduser()
    return pathlib.Path(os.environ.get("HARNESS_DATA", pathlib.Path.home() / "harness-data"))


def parse_ts(s):
    if isinstance(s, dt.datetime):
        return s
    if not isinstance(s, str) or not s:
        return None
    try:
        t = dt.datetime.fromisoformat(s.replace("Z", "+00:00"))
    except ValueError:
        try:
            t = dt.datetime.combine(dt.date.fromisoformat(s[:10]), dt.time())
        except ValueError:
            return None
    if t.tzinfo is None:
        t = t.replace(tzinfo=dt.timezone.utc)
    return t.astimezone(dt.timezone.utc)


def iso(t):
    return t.astimezone(dt.timezone.utc).isoformat(timespec="seconds") if t else None


def weeks(a, b):
    return (a - b).total_seconds() / (7 * 86400)


def load_areas():
    try:
        m = re.search(r"^areas:\s*\[([^\]]*)\]", ONTOLOGY.read_text(encoding="utf-8"), re.M)
        areas = [a.strip().strip("'\"") for a in m.group(1).split(",") if a.strip()] if m else []
    except OSError:
        areas = []
    return areas or list(FALLBACK_AREAS)


def area_of(scope=None, hint=None, areas=()):
    if isinstance(scope, str) and scope:
        a = scope.split("/", 1)[0]
        if a in areas:
            return a
    if isinstance(hint, str) and hint:
        for p in re.split(r"[\\/]+", hint):
            if p in areas:
                return p
    return None


def read_jsonl(path, warn=True):
    out = []
    path = pathlib.Path(path)
    if not path.is_file():
        return out
    for n, line in enumerate(path.read_text(encoding="utf-8", errors="replace").splitlines(), 1):
        if not line.strip():
            continue
        try:
            rec = json.loads(line)
        except json.JSONDecodeError:
            if warn:
                print(f"warning: {path.name}:{n}: not JSON, skipped", file=sys.stderr)
            continue
        if isinstance(rec, dict):
            out.append(rec)
    return out


def newest_per_id(records):
    """Event-sourced stores: the newest line per id wins (by ts, then file order)."""
    best = {}
    for i, r in enumerate(records):
        rid = r.get("id")
        if not rid:
            continue
        key = (parse_ts(r.get("ts")) or dt.datetime.min.replace(tzinfo=dt.timezone.utc), i)
        if rid not in best or key >= best[rid][0]:
            best[rid] = (key, r)
    return {rid: r for rid, (_, r) in best.items()}


def load_config(root):
    cfg = json.loads(json.dumps(DEFAULTS))
    p = root / "patterns" / "config.json"
    if p.is_file():
        try:
            user = json.loads(p.read_text(encoding="utf-8"))
        except ValueError:
            print(f"warning: {p} is not JSON; using defaults", file=sys.stderr)
            user = {}
        for k, v in (user or {}).items():
            if isinstance(v, dict) and isinstance(cfg.get(k), dict):
                cfg[k].update(v)
            elif not k.startswith("_"):
                cfg[k] = v
    return cfg


def short_hash(*parts):
    return hashlib.sha1("|".join(map(str, parts)).encode("utf-8")).hexdigest()[:6]


def slug(words_, n=3):
    ascii_words = [w for w in words_ if re.fullmatch(r"[a-z0-9]+", w)][:n]
    return "-".join(ascii_words)


# ---------------------------------------------------------------- L0/L1: episodes

class Episode:
    __slots__ = ("id", "ts", "session", "area", "kind", "features", "keyword", "source", "type", "labels",
                 "command", "tool", "text")

    def __init__(self, **kw):
        for k in self.__slots__:
            setattr(self, k, kw.get(k))
        self.labels = self.labels or []
        self.features = self.features or set()


def classify(ev, labels, kot):
    """Pattern kind for one episode, or None when it carries no pattern signal."""
    t = ev.get("type")
    sig = set(labels) | tokens(kot) | words(kot)
    if sig & FRICTION or (ev.get("tool_name") or ev.get("tool")) and ev.get("outcome") in ("failed", "reverted"):
        return "tool-friction"
    if t == "mishap" or ev.get("outcome") in ("failed", "reverted") or ev.get("verdict") == "fail":
        return "mistake"
    if t == "correction" or ev.get("is_correction") is True:
        return "correction"
    if sig & PREF:
        return "preference"
    if ev.get("outcome") == "worked" or ev.get("verdict") == "pass" or sig & {"success", "worked"}:
        return "success"
    if t == "prompt":
        return "request"
    if t == "decision":
        return "preference"
    return None


def load_events(root):
    log = root / "log"
    events = []
    if log.is_dir():
        for p in sorted(log.glob("*.jsonl")):
            events.extend(read_jsonl(p))
    return events


def merge_labels(events):
    """Overlay each event with its newest label event (L0 + label -> L1). Returns (merged, labeled_ids)."""
    labels = {}
    for ev in events:
        if ev.get("type") == "label" and ev.get("labels_for"):
            prev = labels.get(ev["labels_for"])
            if prev is None or (parse_ts(ev.get("ts")) or dt.datetime.min.replace(tzinfo=dt.timezone.utc)) >= \
                    (parse_ts(prev.get("ts")) or dt.datetime.min.replace(tzinfo=dt.timezone.utc)):
                labels[ev["labels_for"]] = ev
    merged = []
    for ev in events:
        if ev.get("type") == "label":
            continue
        lab = labels.get(ev.get("id"))
        if lab:
            ev = dict(ev)
            for k in ("intent", "situation", "meta", "labels", "is_correction", "scope"):
                if lab.get(k) not in (None, "", [], {}):
                    ev[k] = lab[k]
        merged.append(ev)
    return merged, set(labels)


def episode_from_event(ev, areas):
    if ev.get("type") not in EPISODE_TYPES and not (ev.get("tool_name") or ev.get("tool")):
        return None
    ts = parse_ts(ev.get("ts"))
    if not ev.get("id") or ts is None:
        return None
    meta = ev.get("meta") if isinstance(ev.get("meta"), dict) else {}
    kot = meta.get("kind_of_thing") if isinstance(meta.get("kind_of_thing"), str) else ""
    labels = [str(x).lower() for x in (ev.get("labels") or []) if isinstance(x, (str, int))]
    plain_labels = [x for x in labels if ":" not in x]
    kind = classify(ev, plain_labels, kot)
    content = ev.get("content") if isinstance(ev.get("content"), str) else ""
    cmd = None
    if ev.get("type") == "prompt":
        m = re.match(r"\s*/([a-z][a-z0-9:_-]*)", content)
        cmd = m.group(1) if m else None
    strong = tokens(kot) | set().union(*(tokens(x.replace("-", " ")) for x in plain_labels)) if plain_labels or kot else set()
    strong |= set().union(*(tokens(str(x)) for x in (ev.get("correction_patterns") or [])))
    strong -= GENERIC_LABELS
    feats = strong | tokens(ev.get("intent") if isinstance(ev.get("intent"), str) else "")
    if len(feats) < 3:
        feats |= set(list(sorted(tokens(content[:600])))[:40]) if content else set()
    if cmd:
        feats.add(f"/{cmd}")
    return Episode(id=ev["id"], ts=ts, session=ev.get("session_id") or f"day:{ts.date()}",
                   area=area_of(ev.get("scope"), ev.get("scope_hint") or ev.get("cwd"), areas),
                   kind=kind, features=feats, keyword=kot.strip().lower() or None,
                   source="label" if ev.get("_labeled") else "log", type=ev.get("type"), labels=labels,
                   command=cmd, tool=ev.get("tool_name") or ev.get("tool"), text=kot or (ev.get("intent") or ""))


def _md_sections(text, header_re):
    sections, cur = [], None
    for line in text.splitlines():
        m = re.match(header_re, line)
        if m:
            cur = {"header": m.group(1).strip(), "body": []}
            sections.append(cur)
        elif cur is not None:
            cur["body"].append(line)
    return sections


def _field(body, name):
    for line in body:
        m = re.match(rf"\s*-\s*\*\*{re.escape(name)}[^*]*:\*\*\s*(.*)", line, re.I)
        if m:
            return m.group(1).strip()
    return ""


def project_episodes(proj, areas):
    """Mishaps (log/mishaps.md) and decisions (decisions.md) of one project folder as episodes."""
    proj = pathlib.Path(proj).expanduser()
    area = area_of(None, str(proj.resolve()), areas)
    out = []
    for rel, kind, source in (("log/mishaps.md", "mistake", "mishap"), ("decisions.md", "preference", "decision")):
        p = proj / rel
        if not p.is_file():
            continue
        for n, sec in enumerate(_md_sections(p.read_text(encoding="utf-8", errors="replace"), r"^##\s+(.*)$"), 1):
            m = re.search(r"(\d{4}-?\d{2}-?\d{2})", sec["header"])
            ts = None
            if m:
                d = m.group(1).replace("-", "")
                ts = parse_ts(f"{d[:4]}-{d[4:6]}-{d[6:8]}")
            ts = ts or dt.datetime.fromtimestamp(p.stat().st_mtime, dt.timezone.utc)
            body = sec["body"]
            text = " ".join([sec["header"], _field(body, "Root cause"), _field(body, "Repeat pattern"),
                             _field(body, "Claim"), _field(body, "Reasons")])
            gen = _field(body, "Generalizes to")
            ep_area = area or next((a for a in areas if a in gen), None)
            out.append(Episode(id=f"{source}:{proj.name}#{n}", ts=ts, session=f"{source}:{proj.name}:{ts.date()}",
                               area=ep_area, kind=kind, features=tokens(text), keyword=None, source=source,
                               type=source, labels=[], text=sec["header"]))
    return out


def external_items(paths):
    items = []
    for p in paths or []:
        items.extend(read_jsonl(p))
    return items


def external_episodes(items, areas):
    """JSONL evidence from Claude Code built-ins (docs/PATTERNS.md). Items with `skill` + `invocations`
    are usage stats (used by ladder/meta), not episodes."""
    out = []
    for n, it in enumerate(items, 1):
        if "invocations" in it and it.get("skill"):
            continue
        text = str(it.get("text") or "")
        if not text:
            continue
        src = it.get("source") if it.get("source") in ("insights", "usage", "skill-doctor", "auto-memory",
                                                        "session-note", "mishap", "decision") else "insights"
        ts = parse_ts(it.get("ts")) or dt.datetime.now(dt.timezone.utc)
        kind = it.get("kind") if it.get("kind") in KIND_PHRASE else None
        feats = tokens(text) | set(map(str.lower, it.get("labels") or []))
        if kind is None:
            kind = "tool-friction" if feats & FRICTION else "preference" if feats & PREF else "request"
        out.append(Episode(id=str(it.get("ref") or f"{src}:{n}"), ts=ts,
                           session=str(it.get("session") or f"{src}:{ts.date()}"),
                           area=it.get("area") if it.get("area") in areas else None, kind=kind, features=feats,
                           keyword=None, source=src, type=src, labels=list(it.get("labels") or []), text=text[:120]))
    return out


def memory_episodes(dirs, areas):
    """Claude Code auto-memory notes of type `feedback` (corrections / confirmed approaches)."""
    out = []
    for d in dirs or []:
        d = pathlib.Path(d).expanduser()
        for p in sorted(d.rglob("*.md")):
            if p.name == "MEMORY.md":
                continue
            text = p.read_text(encoding="utf-8", errors="replace")
            m = re.match(r"^---\s*\n(.*?)\n---\s*\n?(.*)$", text, re.S)
            if not m:
                continue
            front, body = m.group(1), m.group(2)
            typ = re.search(r"^type:\s*['\"]?([a-z]+)", front, re.M)
            if not typ or typ.group(1) != "feedback":
                continue
            desc = " ".join(re.findall(r"^(?:name|description):\s*(.*)$", front, re.M))
            feats = tokens(desc + " " + body[:800])
            ts = dt.datetime.fromtimestamp(p.stat().st_mtime, dt.timezone.utc)
            out.append(Episode(id=f"auto-memory:{p.relative_to(d).as_posix()}", ts=ts,
                               session=f"auto-memory:{ts.date()}", area=area_of(None, str(p), areas),
                               kind="preference" if feats & PREF else "correction", features=feats, keyword=None,
                               source="auto-memory", type="auto-memory", labels=[], text=desc[:120]))
    return out


class Context:
    """Everything one run reads: episodes, stores, principles, config."""

    def __init__(self, args):
        self.root = data_dir(args.data_dir)
        self.cfg = load_config(self.root)
        self.areas = load_areas()
        self.now = (dt.datetime.combine(args.today, dt.time(23, 59), dt.timezone.utc) if args.today
                    else dt.datetime.now(dt.timezone.utc))
        raw = load_events(self.root)
        self.raw_events = raw
        merged, self.labeled = merge_labels(raw)
        for ev in merged:
            if ev.get("id") in self.labeled:
                ev["_labeled"] = True
        self.events = merged
        eps = [e for e in (episode_from_event(ev, self.areas) for ev in merged) if e]
        for proj in args.project or []:
            eps.extend(project_episodes(proj, self.areas))
        self.external = external_items(args.external)
        eps.extend(external_episodes(self.external, self.areas))
        eps.extend(memory_episodes(args.auto_memory, self.areas))
        self.all_episodes = sorted(eps, key=lambda e: e.ts)
        start = self.now - dt.timedelta(weeks=self.cfg["window_weeks"])
        self.episodes = [e for e in self.all_episodes if start <= e.ts <= self.now]
        self.by_id = {e.id: e for e in self.all_episodes}
        seed_recs = [] if args.no_seeds else read_jsonl(args.seeds or SEEDS)
        pdir = self.root / "patterns"
        self.store_recs = {pre: read_jsonl(pdir / name) for pre, name in STORES.items()}
        self.patterns = newest_per_id([r for r in seed_recs if str(r.get("id", "")).startswith("pat_")]
                                      + self.store_recs["pat_"])
        self.encodings = newest_per_id([r for r in seed_recs if str(r.get("id", "")).startswith("enc_")]
                                       + self.store_recs["enc_"])
        self.metas = newest_per_id([r for r in seed_recs if str(r.get("id", "")).startswith("mp_")]
                                   + self.store_recs["mp_"])
        self.principles = load_principles(args.principles or PRINCIPLES)


def load_principles(path):
    """Numbered items of PRINCIPLES.md -> [{id: P<n>, title, text, patterns: [pat_...]}]."""
    p = pathlib.Path(path)
    if not p.is_file():
        return []
    out, cur = [], None
    for line in p.read_text(encoding="utf-8").splitlines():
        m = re.match(r"^(\d+)\.\s+(.*)$", line)
        if m:
            cur = {"id": f"P{m.group(1)}", "text": m.group(2)}
            out.append(cur)
        elif cur is not None and line.strip() and line.startswith((" ", "\t")):
            cur["text"] += " " + line.strip()
        elif cur is not None and line.strip() and not line.startswith((" ", "\t")):
            cur = None
    for pr in out:
        t = re.match(r"\*\*(.+?)\*\*", pr["text"])
        pr["title"] = t.group(1) if t else pr["text"][:60]
        pr["patterns"] = sorted(set(re.findall(r"pat_[a-z0-9_-]+", pr["text"])))
    return out


# ---------------------------------------------------------------- L2: mining

class Cluster:
    def __init__(self, kind, key=None):
        self.kind, self.key, self.members = kind, key, []
        self.counts = collections.Counter()

    def add(self, ep):
        self.members.append(ep)
        self.counts.update(ep.features)

    def core(self):
        n = len(self.members)
        need = max(1, math.ceil(n / 2)) if n > 2 else 1
        return {t for t, c in self.counts.items() if c >= need}


def cluster_episodes(episodes, sim):
    clusters, by_key = [], {}
    for ep in episodes:
        if ep.kind is None or not ep.features:
            continue
        key = (ep.kind, ep.keyword) if ep.keyword else None
        if key and key in by_key:
            by_key[key].add(ep)
            continue
        best, bs = None, 0.0
        for c in clusters:
            if c.kind != ep.kind:
                continue
            s = dice(ep.features, c.core())
            if s > bs:
                best, bs = c, s
        if best is not None and bs >= sim:
            best.add(ep)
            if key:
                by_key.setdefault(key, best)
        else:
            c = Cluster(ep.kind, key)
            c.add(ep)
            clusters.append(c)
            if key:
                by_key[key] = c
    return clusters


def confidence(support, sessions, last_seen, now, cfg):
    s = support / (support + 2)
    d = 0.5 + 0.5 * min(1.0, sessions / 3)
    r = 1.0 if last_seen and weeks(now, last_seen) <= cfg["decay_weeks"] else 0.5
    return round(s * d * r, 2)


def candidate_from(members, kind, ctx, keywords=None, statement=None, signals=None):
    members = sorted({m.id: m for m in members}.values(), key=lambda m: m.ts)
    counts = collections.Counter()
    for m in members:
        counts.update(m.features)
    kw = keywords or [t for t, _ in sorted(counts.items(), key=lambda x: (-x[1], x[0]))][:6]
    kots = collections.Counter(m.keyword for m in members if m.keyword)
    top_kot = kots.most_common(1)[0][0] if kots else None
    sessions = {m.session for m in members}
    areas = sorted({m.area for m in members if m.area})
    first, last = members[0].ts, members[-1].ts
    stmt = statement or (f"{KIND_PHRASE[kind]}: {top_kot}" if top_kot else f"{KIND_PHRASE[kind]} about: {', '.join(kw[:4])}")
    sig = {"keywords": kw}
    if top_kot:
        sig["kind_of_thing"] = top_kot
    cmds = sorted({m.command for m in members if m.command})
    if cmds:
        sig["commands"] = cmds
    tools = sorted({m.tool for m in members if m.tool})
    if tools:
        sig["tools"] = tools
    sig.update(signals or {})
    srcs = sorted({m.source for m in members if m.source})
    return {
        "id": f"pat_{kind}_{(slug(kw) + '_') if slug(kw) else ''}{short_hash(kind, *sorted(kw[:5]))}",
        "ts": iso(ctx.now), "pattern_level": "L2", "kind": kind, "statement": stmt, "status": "candidate",
        "scope": areas[0] if len(areas) == 1 else "global",
        "areas": areas, "evidence": [m.id for m in members], "sources": srcs or ["log"],
        "support": len(members), "sessions": len(sessions), "first_seen": iso(first), "last_seen": iso(last),
        "confidence": confidence(len(members), len(sessions), last, ctx.now, ctx.cfg),
        "signals": sig, "origin": "insights" if srcs == ["insights"] else "mine",
    }


def workflow_candidates(episodes, ctx):
    by_session = collections.defaultdict(list)
    for e in episodes:
        if e.command:
            by_session[e.session].append(e)
    trans = collections.defaultdict(dict)  # (a, b) -> {session: [ep_a, ep_b]}
    for sess, eps in by_session.items():
        eps.sort(key=lambda e: e.ts)
        for x, y in zip(eps, eps[1:]):
            if x.command != y.command:
                trans[(x.command, y.command)].setdefault(sess, [x, y])
    out = []
    for (a, b), sess in sorted(trans.items()):
        if len(sess) >= max(2, ctx.cfg["propose"]["sessions"]):
            members = [e for pair in sess.values() for e in pair]
            c = candidate_from(members, "workflow", ctx, keywords=[f"/{a}", f"/{b}"],
                               statement=f"{KIND_PHRASE['workflow']}: /{a} then /{b} ({len(sess)} sessions)",
                               signals={"sequence": [f"/{a}", f"/{b}"]})
            c["id"] = f"pat_workflow_{re.sub(r'[^a-z0-9-]', '-', a)}-then-{re.sub(r'[^a-z0-9-]', '-', b)}"
            c["sessions"] = len(sess)
            out.append(c)
    return out


def temporal_candidates(episodes, ctx):
    out = []
    by_cmd = collections.defaultdict(list)
    for e in episodes:
        if e.command:
            by_cmd[e.command].append(e)
    for cmd, eps in sorted(by_cmd.items()):
        if len(eps) < max(3, ctx.cfg["min_support"]):
            continue
        wd = collections.Counter(e.ts.weekday() for e in eps)
        day, n = wd.most_common(1)[0]
        on_day = [e for e in eps if e.ts.weekday() == day]
        wks = {e.ts.isocalendar()[:2] for e in on_day}
        if len(wks) >= 2 and n / len(eps) >= 0.6:
            c = candidate_from(on_day, "temporal", ctx, keywords=[f"/{cmd}", WEEKDAYS[day].lower()],
                               statement=f"{KIND_PHRASE['temporal']}: /{cmd} mostly on {WEEKDAYS[day]} "
                                         f"({n}/{len(eps)}, {len(wks)} weeks)",
                               signals={"weekday": WEEKDAYS[day], "share": round(n / len(eps), 2)})
            c["id"] = f"pat_temporal_{re.sub(r'[^a-z0-9-]', '-', cmd)}-{WEEKDAYS[day].lower()}"
            out.append(c)
    starts = {}
    for e in episodes:
        if e.type == "prompt" and not e.session.startswith("day:"):
            if e.session not in starts or e.ts < starts[e.session].ts:
                starts[e.session] = e
    if len(starts) >= 4:
        hours = [s.ts.hour for s in starts.values()]
        best = max(range(24), key=lambda h: (sum(1 for x in hours if (x - h) % 24 < 4), -h))
        inwin = [s for s in starts.values() if (s.ts.hour - best) % 24 < 4]
        if len(inwin) / len(starts) >= 0.6:
            c = candidate_from(inwin, "temporal", ctx, keywords=["session-start", f"{best:02d}h"],
                               statement=f"{KIND_PHRASE['temporal']}: sessions mostly start {best:02d}:00-"
                                         f"{(best + 4) % 24:02d}:00 UTC ({len(inwin)}/{len(starts)})",
                               signals={"hour_window_utc": [best, (best + 4) % 24]})
            c["id"] = f"pat_temporal_session-start-{best:02d}h"
            out.append(c)
    return out


def pattern_tokens(p):
    sig = p.get("signals") if isinstance(p.get("signals"), dict) else {}
    toks = set()
    for k in ("keywords", "themes"):
        for w in sig.get(k) or []:
            toks |= tokens(str(w)) | ({str(w).lower()} if str(w).startswith("/") else set())
    toks |= tokens(p.get("statement") or "") | tokens(sig.get("kind_of_thing") or "")
    return toks - GENERIC_LABELS


def match_existing(cand, existing, cfg):
    ev = set(cand["evidence"])
    best, bs = None, 0.0
    for p in existing.values():
        if p.get("kind") != cand["kind"]:
            continue
        if p.get("id") == cand["id"]:
            return p, 1.0
        pe = set(p.get("evidence") or [])
        overlap = len(ev & pe) / len(ev) if ev else 0.0
        s = max(overlap, dice(pattern_tokens(cand), pattern_tokens(p)))
        if s > bs:
            best, bs = p, s
    return (best, bs) if bs >= cfg["dedupe_similarity"] else (None, bs)


def mine(ctx):
    """Return (new_candidates, updates) where updates are {id, new_evidence, ...} for existing patterns."""
    cfg = ctx.cfg
    clusters = cluster_episodes(ctx.episodes, cfg["similarity"])
    cands = []
    for c in clusters:
        if len(c.members) >= cfg["min_support"]:
            cands.append(candidate_from(c.members, c.kind, ctx))
            areas = {m.area for m in c.members if m.area}
            if c.kind in ("mistake", "correction", "success", "preference") and len(areas) >= cfg["principle"]["areas"]:
                da = candidate_from(c.members, "domain-analogy", ctx,
                                    signals={"base_kind": c.kind})
                da["statement"] = (f"{KIND_PHRASE['domain-analogy']} ({', '.join(sorted(areas))}): "
                                   f"{cands[-1]['statement']}")
                cands.append(da)
    cands += workflow_candidates(ctx.episodes, ctx)
    cands += temporal_candidates(ctx.episodes, ctx)
    new, updates, seen = [], [], set()
    for c in cands:
        if c["id"] in seen:
            continue
        seen.add(c["id"])
        p, s = match_existing(c, ctx.patterns, cfg)
        if p is None:
            new.append(c)
        else:
            fresh = [e for e in c["evidence"] if e not in set(p.get("evidence") or [])]
            if fresh:
                updates.append({"id": p["id"], "status": p.get("status"), "similarity": round(s, 2),
                                "new_evidence": fresh, "statement": p.get("statement")})
    new.sort(key=lambda c: (-c["confidence"], -c["support"], c["id"]))
    return new, updates


# ---------------------------------------------------------------- ladder (promotion / demotion)

def evidence_view(p, ctx, extra=()):
    """Recompute support from the record plus newly matched evidence (recorded count or log, whichever is larger)."""
    ev = list(dict.fromkeys(list(p.get("evidence") or []) + list(extra)))
    known = [ctx.by_id[e] for e in ev if e in ctx.by_id]
    sess = {k.session for k in known}
    last = max([k.ts for k in known] + [t for t in [parse_ts(p.get("last_seen"))] if t], default=None)
    areas = sorted(set(p.get("areas") or []) | {k.area for k in known if k.area})
    support = max(int(p.get("support") or 0), len(ev))
    sessions = max(int(p.get("sessions") or 0), len(sess))
    return {"evidence": ev, "support": support, "sessions": sessions, "areas": areas, "last_seen": last,
            "confidence": confidence(support, sessions, last, ctx.now, ctx.cfg), "known": known}


def meets(view, th, now, kind=None):
    if kind in QUIET_KINDS and "mistake_support" in th:
        sup, ses = th["mistake_support"], th["mistake_sessions"]
    else:
        sup, ses = th["support"], th["sessions"]
    ok = view["support"] >= sup and view["sessions"] >= ses and view["confidence"] >= th["confidence"]
    if "areas" in th:
        ok = ok and max(1, len(view["areas"])) >= th["areas"]
    if "recency_weeks" in th:
        ok = ok and view["last_seen"] is not None and weeks(now, view["last_seen"]) <= th["recency_weeks"]
    return ok


def eval_gate_for(areas, root):
    """Eval sets that gate an L3 change for these areas (scripts/eval_gate.py)."""
    sets = [a for a in areas if list((root / "evals" / a / "tasks").glob("*.yaml"))]
    if sets:
        return {"gate": "pending", "eval_sets": [f"evals/{a}" for a in sets],
                "how": "run each set with and without the change, then scripts/eval_gate.py BASELINE CANDIDATE"}
    return {"gate": "ungated", "eval_sets": [], "how": f"no eval set for {', '.join(areas) or 'global'}; say so"}


def encoding_usage(enc, ctx):
    """(invocations, last_used) from prompt events '/<name>' plus skill-doctor/usage stats."""
    name = pathlib.PurePosixPath(str(enc.get("target") or "")).name.replace("SKILL.md", "") or ""
    if not name:
        name = pathlib.PurePosixPath(str(enc.get("target") or "")).parent.name
    name = re.sub(r"\.(md|py|json)$", "", name)
    n, last = 0, parse_ts(enc.get("last_used"))
    for e in ctx.all_episodes:
        if e.command and (e.command == name or e.command.endswith(":" + name)):
            n += 1
            last = max(last, e.ts) if last else e.ts
    stat = None
    for it in ctx.external:
        if it.get("skill") in (name, enc.get("target")) and "invocations" in it:
            stat = it
    if stat is not None:
        n = max(n, int(stat.get("invocations") or 0))
    return n + int(enc.get("invocations") or 0), last, stat


def overrides(enc, ctx):
    tag = f"override:{enc['id']}"
    evs = [ev["id"] for ev in ctx.events
           if tag in [str(x).lower() for x in (ev.get("labels") or [])] or ev.get("corrects") == enc["id"]]
    ids = list(dict.fromkeys(list(enc.get("override_events") or []) + evs))
    return max(int(enc.get("overrides") or 0), len(ids)), ids


def active_encodings(pid, ctx):
    return [e for e in ctx.encodings.values()
            if pid in (e.get("encodes") or []) and e.get("status") in ("approved", "encoded")]


def ladder(ctx, updates=None):
    cfg, now = ctx.cfg, ctx.now
    if updates is None:
        _, updates = mine(ctx)
    extra = collections.defaultdict(list)
    for u in updates:
        extra[u["id"]].extend(u["new_evidence"])
    props = []

    def prop(layer, action, rec, frm, to, reason, needs=("approval",), **kw):
        props.append(dict({"layer": layer, "action": action, "id": rec["id"], "from": frm, "to": to,
                           "reason": reason, "needs": list(needs), "record": rec}, **kw))

    for pid, p in sorted(ctx.patterns.items()):
        st, kind = p.get("status"), p.get("kind")
        v = evidence_view(p, ctx, extra.get(pid, ()))
        upd = dict({k: x for k, x in p.items() if not k.startswith("_")}, ts=iso(now), evidence=v["evidence"],
                   support=v["support"], sessions=v["sessions"], areas=v["areas"],
                   last_seen=iso(v["last_seen"]) if v["last_seen"] else p.get("last_seen"),
                   confidence=v["confidence"])
        metrics = {k: v[k] for k in ("support", "sessions", "confidence")}
        metrics["areas"] = v["areas"]
        age = weeks(now, v["last_seen"]) if v["last_seen"] else None
        status_ts = parse_ts(p.get("ts")) or now
        encs = active_encodings(pid, ctx)
        new_since = [k for k in v["known"] if k.ts > status_ts]
        if st in ("candidate", "retired"):
            if meets(v, cfg["propose"], now) and (st == "candidate" or new_since):
                prop("L2", "propose" if st == "candidate" else "resurface", dict(upd, status="proposed"), st,
                     "proposed", f"support {v['support']}, sessions {v['sessions']}, confidence {v['confidence']}",
                     metrics=metrics)
            continue
        if st == "proposed":
            props.append({"layer": "L2", "action": "awaiting-approval", "id": pid, "from": st, "to": "approved",
                          "reason": f"proposed {p.get('ts', '')[:10]}; decide: approve, edit or retire",
                          "needs": ["approval"], "metrics": metrics, "record": dict(upd, status="approved")})
            continue
        if st == "decaying":
            if new_since:
                to = "encoded" if encs else "approved"
                prop("L2", "revive", dict(upd, status=to), st, to, f"{len(new_since)} new episode(s) since decay")
            elif age is None or age >= cfg["decay_weeks"] + cfg["retire_weeks"] or weeks(now, status_ts) >= cfg["retire_weeks"]:
                prop("L2", "retire", dict(upd, status="retired"), st, "retired",
                     f"no support for {age:.0f} weeks" if age is not None else "no dated support")
            continue
        if st in ("encoded",) and kind in QUIET_KINDS:
            for enc in encs:
                enc_ts = parse_ts(enc.get("ts")) or now
                after = [k for k in v["known"] if k.ts > enc_ts]
                n_over, _ = overrides(enc, ctx)
                if len(after) >= cfg["reoccur_reopen"] or n_over >= cfg["override_reopen"]:
                    why = (f"{len(after)} new episode(s) after {enc['id']} ({enc_ts.date()})" if after else "") + \
                          (f"; {enc['id']} overridden {n_over}x" if n_over >= cfg["override_reopen"] else "")
                    prop("L2", "reopen", dict(upd, status="reopened"), st, "reopened", why.strip("; "),
                         evidence_after=[k.id for k in after])
                    break
            continue  # silence after encoding a mistake/correction means the encoding works: no decay
        if st in ("approved", "encoded") and age is not None and age >= cfg["decay_weeks"]:
            prop("L2", "decay", dict(upd, status="decaying"), st, "decaying", f"no support for {age:.0f} weeks")
            continue
        if (st == "approved" and not encs and meets(v, cfg["encode"], now, kind)) or st == "reopened":
            areas = v["areas"] or [a for a in [str(p.get("scope", "")).split("/")[0]] if a in ctx.areas]
            gate = eval_gate_for(areas, ctx.root)
            enc_id = f"enc_{pid[4:]}"[:60] if st == "approved" else f"enc_{pid[4:]}-v2"[:60]
            draft = {"id": enc_id, "ts": iso(now), "pattern_level": "L3", "kind": "<choose: " + SUGGESTED_ENCODING.get(kind, "skill") + ">",
                     "target": "<path of the artifact>", "encodes": [pid], "status": "proposed",
                     "gate": gate["gate"], "scope": p.get("scope") or "global"}
            prop("L3", "propose-encoding" if st == "approved" else "re-encode", draft, st, "encoded",
                 f"support {v['support']}, sessions {v['sessions']}, confidence {v['confidence']}; "
                 f"suggested: {SUGGESTED_ENCODING.get(kind)}",
                 needs=["approval"] + (["eval-gate:" + s for s in gate["eval_sets"]] or ["ungated"]),
                 eval=gate, metrics=metrics, pattern=pid)

    for eid, enc in sorted(ctx.encodings.items()):
        if enc.get("status") not in ("approved", "encoded"):
            continue
        n_over, ids = overrides(enc, ctx)
        if n_over >= cfg["override_reopen"]:
            prop("L3", "review-encoding", dict(enc, ts=iso(now), status="reopened", overrides=n_over,
                                               override_events=ids), enc.get("status"), "reopened",
                 f"overridden {n_over}x (threshold {cfg['override_reopen']})")
            continue
        if enc.get("kind") in ("skill", "command", "saved-workflow"):
            inv, last, stat = encoding_usage(enc, ctx)
            born = parse_ts(enc.get("ts")) or now
            idle = weeks(now, last) if last else weeks(now, born)
            never = stat is not None and int(stat.get("invocations") or 0) == 0
            if (idle >= cfg["decay_weeks"] and weeks(now, born) >= cfg["decay_weeks"]) or never:
                prop("L3", "decay-encoding", dict(enc, ts=iso(now), status="decaying"), enc.get("status"),
                     "decaying", ("/skill-doctor reports 0 invocations" if never else
                                  f"unused for {idle:.0f} weeks") + f" ({inv} invocation(s) seen)")

    # L4: principles
    contradicted = collections.Counter()
    for ev in ctx.events:
        for lab in ev.get("labels") or []:
            m = re.match(r"contradicts:(p\d+)$", str(lab).lower())
            if m:
                contradicted[m.group(1).upper()] += 1
    linked = collections.defaultdict(set)
    for pid, p in ctx.patterns.items():
        for pr in p.get("principles") or []:
            linked[pr].add(pid)
    for pr in ctx.principles:
        for pid in pr["patterns"]:
            linked[pr["id"]].add(pid)
    for pr in ctx.principles:
        weak = [pid for pid in sorted(linked.get(pr["id"], ())) if ctx.patterns.get(pid, {}).get("status") in ("reopened", "retired")]
        if weak or contradicted.get(pr["id"]):
            props.append({"layer": "L4", "action": "review-principle", "id": pr["id"], "from": "active", "to": "review",
                          "reason": "; ".join(filter(None, [
                              f"linked pattern(s) {', '.join(weak)} reopened/retired" if weak else "",
                              f"contradicted by {contradicted[pr['id']]} labelled episode(s)" if contradicted.get(pr["id"]) else ""])),
                          "needs": ["approval", "distill-principles"], "record": None})
    pool = [p for p in ctx.patterns.values() if p.get("status") in ("approved", "encoded")
            and not p.get("principles") and not any(p["id"] in pr["patterns"] for pr in ctx.principles)]
    groups = []
    for p in sorted(pool, key=lambda x: x["id"]):
        for g in groups:
            if dice(pattern_tokens(p), set().union(*(pattern_tokens(x) for x in g))) >= cfg["principle"]["similarity"]:
                g.append(p)
                break
        else:
            groups.append([p])
    for g in groups:
        areas = sorted(set().union(*(set(x.get("areas") or []) for x in g)))
        if len(g) >= cfg["principle"]["patterns"] and len(areas) >= cfg["principle"]["areas"]:
            common = collections.Counter(t for x in g for t in pattern_tokens(x))
            props.append({"layer": "L4", "action": "propose-principle", "id": "P<new>", "from": None, "to": "proposed",
                          "reason": f"{len(g)} patterns across {len(areas)} areas ({', '.join(areas)}); shared: "
                                    + ", ".join(t for t, _ in common.most_common(5)),
                          "needs": ["approval", "distill-principles"], "patterns": [x["id"] for x in g],
                          "record": None})
    order = {"L2": 0, "L3": 1, "L4": 2}
    props.sort(key=lambda x: (order.get(x["layer"], 9), x["action"] == "awaiting-approval", x["id"]))
    return props


# ---------------------------------------------------------------- L5: meta-patterns

def meta(ctx, updates=None):
    cfg, now = ctx.cfg, ctx.now
    out = []

    def mp(signal, statement, target, proposal, about=(), evidence=(), metrics=None, rid=None):
        rid = rid or f"mp_{signal}_{short_hash(signal, *sorted(map(str, about)))}"
        out.append({"id": rid, "ts": iso(now), "pattern_level": "L5", "signal": signal, "statement": statement,
                    "about": list(about), "evidence": list(evidence)[:50], "metrics": metrics or {},
                    "target": target, "proposal": proposal, "status": "proposed"})

    if updates is None:
        _, updates = mine(ctx)
    extra = collections.defaultdict(list)
    for u in updates:
        extra[u["id"]].extend(u["new_evidence"])

    # 1-2. encodings that failed: re-occurrence after encoding, overrides
    failed_by_kind = collections.defaultdict(list)
    for eid, enc in sorted(ctx.encodings.items()):
        if enc.get("status") not in ("approved", "encoded", "reopened"):
            continue
        enc_ts = parse_ts(enc.get("ts")) or now
        for pid in enc.get("encodes") or []:
            p = ctx.patterns.get(pid)
            if not p or p.get("kind") not in QUIET_KINDS:
                continue
            v = evidence_view(p, ctx, extra.get(pid, ()))
            after = [k for k in v["known"] if k.ts > enc_ts]
            if len(after) >= cfg["reoccur_reopen"]:
                failed_by_kind[enc.get("kind")].append(eid)
                mp("reoccurrence-after-encoding",
                   f"{pid} kept recurring after {eid} ({enc.get('kind')}: {enc.get('target')}) was put in place",
                   "encoding", f"Reopen {pid}; replace or strengthen {eid} (e.g. rule -> hook or eval task).",
                   about=[pid, eid], evidence=[k.id for k in after], metrics={"after": len(after), "since": iso(enc_ts)})
        n_over, ids = overrides(enc, ctx)
        if n_over >= cfg["override_reopen"]:
            failed_by_kind[enc.get("kind")].append(eid)
            mp("encoding-overridden", f"{eid} was overridden {n_over}x", "encoding",
               f"Ask whether {eid} encodes the wrong thing; revise its pattern or retire it.",
               about=[eid], evidence=ids, metrics={"overrides": n_over})
        if enc.get("kind") in ("skill", "command", "saved-workflow"):
            inv, last, stat = encoding_usage(enc, ctx)
            if stat is not None and int(stat.get("invocations") or 0) == 0:
                mp("encoding-unused", f"{eid} ({enc.get('target')}) was never invoked per /skill-doctor", "encoding",
                   f"Retire {eid} or fix its description/trigger (skill-creator description tuning).",
                   about=[eid], metrics={"invocations": 0, "context_cost": stat.get("context_tokens")})
    for kind, ids in sorted(failed_by_kind.items()):
        if len(set(ids)) >= 2:
            mp("reoccurrence-after-encoding", f"Encodings of kind '{kind}' failed {len(set(ids))} times",
               "ontology", f"Prefer a stronger encoding kind than '{kind}' for mistake/correction patterns "
                           f"(e.g. hook or eval-task), and record why in docs/PATTERNS.md.",
               about=sorted(set(ids)), metrics={"failed": len(set(ids))})

    eps = ctx.episodes
    # 3. correction hotspots per area
    corr = [e for e in eps if e.kind in ("correction", "mistake")]
    per_area = collections.Counter(e.area or "unscoped" for e in corr)
    for area, n in per_area.most_common():
        if area != "unscoped" and n >= cfg["hotspot_min"] and n / max(1, len(corr)) >= cfg["hotspot_share"]:
            mp("correction-hotspot", f"{area} produces {n}/{len(corr)} of corrections and mistakes", "cadence",
               f"Review {area} first each week; build or extend evals/{area} from these episodes.",
               about=[area], evidence=[e.id for e in corr if e.area == area], metrics={"count": n, "total": len(corr)})

    # 4. preference drift: opposite words in older vs newer preference/correction episodes on a shared topic
    prefs = [e for e in eps if e.kind in ("preference", "correction")]
    for a, b in OPPOSITES:
        ea = [e for e in prefs if a in e.features or a in words(e.text)]
        eb = [e for e in prefs if b in e.features or b in words(e.text)]
        if not ea or not eb:
            continue
        topic = (set().union(*(e.features for e in ea)) & set().union(*(e.features for e in eb))) - {a, b}
        if not topic:
            continue
        older, newer = (ea, eb) if max(e.ts for e in ea) < min(e.ts for e in eb) else \
            (eb, ea) if max(e.ts for e in eb) < min(e.ts for e in ea) else (None, None)
        if older:
            w_old, w_new = (a, b) if older is ea else (b, a)
            mp("preference-drift", f"Preference drifted from '{w_old}' to '{w_new}' on {', '.join(sorted(topic)[:4])}",
               "pattern", "Confirm the newer preference; supersede the older pattern/rule instead of keeping both.",
               about=sorted(topic)[:4], evidence=[e.id for e in older + newer],
               metrics={"older_until": iso(max(e.ts for e in older)), "newer_from": iso(min(e.ts for e in newer))})

    # 5. blind spots: areas with no episodes
    if len(eps) >= cfg["blind_spot_min_episodes"]:
        seen = {e.area for e in eps if e.area}
        empty = [a for a in ctx.areas if a not in seen]
        if empty:
            mp("blind-spot", f"No logged episodes in {', '.join(empty)} over {cfg['window_weeks']} weeks", "mining",
               "Confirm these areas are dormant, or fix logging/scoping (scope_hint paths) so their work is captured.",
               about=empty, metrics={"episodes": len(eps)})

    # 6. principle conflicts (simple keyword opposition with a shared topic)
    prs = ctx.principles
    for i in range(len(prs)):
        for j in range(i + 1, len(prs)):
            wi, wj = words(prs[i]["text"]), words(prs[j]["text"])
            for a, b in OPPOSITES[1:]:  # always/never is everywhere in principles: too weak alone
                if (a in wi and b in wj) or (b in wi and a in wj):
                    shared = (tokens(prs[i]["text"]) & tokens(prs[j]["text"])) - {a, b}
                    if len(shared) >= 2:
                        mp("principle-conflict", f"{prs[i]['id']} ({prs[i]['title']}) and {prs[j]['id']} "
                                                 f"({prs[j]['title']}) pull opposite ways ({a}/{b}) on "
                                                 f"{', '.join(sorted(shared)[:4])}",
                           "principle", "State which wins when, or merge them (distill-principles).",
                           about=[prs[i]["id"], prs[j]["id"]], metrics={"words": [a, b], "shared": sorted(shared)[:6]})
                        break

    # 7. concentration: one theme dominates the live patterns -> principle family
    live = [p for p in ctx.patterns.values() if p.get("status") not in ("retired", "candidate")]
    if len(live) >= cfg["concentration_min"]:
        theme = collections.Counter()
        for p in live:
            sig = p.get("signals") if isinstance(p.get("signals"), dict) else {}
            theme.update(set(map(str.lower, sig.get("themes") or [])) or pattern_tokens(p))
        for t, n in theme.most_common(3):
            if n / len(live) >= cfg["concentration_share"]:
                ids = sorted(p["id"] for p in live if t in set(map(str.lower, (p.get("signals") or {}).get("themes") or []))
                             | pattern_tokens(p))
                mp("kind-concentration", f"{n}/{len(live)} live patterns share the theme '{t}'", "principle",
                   f"Consider one '{t}' principle family in PRINCIPLES.md and one shared encoding instead of many.",
                   about=ids, metrics={"theme": t, "share": round(n / len(live), 2)},
                   rid=f"mp_kind-concentration_{t}" if re.fullmatch(r"[a-z0-9-]+", t) else None)
                break

    # 8. corrections/mistakes that never join a pattern -> the ontology/labels are missing a kind
    clusters = cluster_episodes(eps, cfg["similarity"])
    singles = [c.members[0] for c in clusters if len(c.members) == 1 and c.kind in ("correction", "mistake")]
    if len(corr) >= cfg["unclassified_min"] and len(singles) / max(1, len(corr)) >= cfg["unclassified_share"]:
        mp("unclassified-share", f"{len(singles)}/{len(corr)} corrections/mistakes match no pattern", "ontology",
           "Labels are too vague or a pattern kind is missing: sharpen kind_of_thing labels or add a kind.",
           about=["Pattern.kind"], evidence=[e.id for e in singles], metrics={"singletons": len(singles), "total": len(corr)})

    # 9. label gap -> cadence
    start = now - dt.timedelta(weeks=cfg["window_weeks"])
    cand = [ev for ev in ctx.raw_events if ev.get("type") in LABEL_CANDIDATE_TYPES
            and (parse_ts(ev.get("ts")) or start) >= start]
    unl = [ev for ev in cand if ev.get("id") not in ctx.labeled and not (ev.get("intent") and ev.get("meta"))]
    if len(cand) >= cfg["unlabeled_min"] and len(unl) / len(cand) >= cfg["unlabeled_share"]:
        mp("label-gap", f"{len(unl)}/{len(cand)} episodes in the window are unlabeled", "cadence",
           "Run scripts/label_events.py before pattern-review (or label twice a week); mining is blind without labels.",
           about=["Event"], metrics={"unlabeled": len(unl), "total": len(cand)})

    fresh = []
    for m in out:
        old = ctx.metas.get(m["id"])
        if old and old.get("status") in ("proposed", "approved", "encoded", "retired"):
            continue
        fresh.append(m)
    return fresh


# ---------------------------------------------------------------- report

def report(ctx):
    pats, encs, metas = ctx.patterns, ctx.encodings, ctx.metas
    lines = [f"# Pattern layers report ({ctx.now.date()})", ""]
    labeled = sum(1 for e in ctx.episodes if e.source == "label")
    lines += [f"- **L0 observations:** {len(ctx.raw_events)} events in `{ctx.root / 'log'}`",
              f"- **L1 episodes:** {len(ctx.episodes)} in the last {ctx.cfg['window_weeks']} weeks "
              f"({labeled} labelled; by kind: " + ", ".join(f"{k} {n}" for k, n in
                                                           collections.Counter(e.kind or 'none' for e in ctx.episodes).most_common()) + ")"]
    lines += ["", "## L2 patterns", ""]
    if pats:
        lines += ["| id | kind | status | support | sessions | areas | statement |", "|---|---|---|---|---|---|---|"]
        for p in sorted(pats.values(), key=lambda x: (x.get("status", ""), x["id"])):
            lines.append(f"| {p['id']} | {p.get('kind')} | {p.get('status')} | {p.get('support', len(p.get('evidence') or []))} "
                         f"| {p.get('sessions', '')} | {', '.join(p.get('areas') or []) or p.get('scope', '')} | {p.get('statement')} |")
    else:
        lines.append("_none yet_")
    lines += ["", "## L3 encodings", ""]
    if encs:
        lines += ["| id | kind | status | target | encodes | gate |", "|---|---|---|---|---|---|"]
        for e in sorted(encs.values(), key=lambda x: x["id"]):
            lines.append(f"| {e['id']} | {e.get('kind')} | {e.get('status')} | `{e.get('target')}` | "
                         f"{', '.join(e.get('encodes') or [])} | {e.get('gate', '')} |")
    else:
        lines.append("_none yet_")
    lines += ["", "## L4 principles", ""]
    linked = collections.defaultdict(set)
    for p in pats.values():
        for pr in p.get("principles") or []:
            linked[pr].add(p["id"])
    for pr in ctx.principles:
        linked[pr["id"]].update(pr["patterns"])
    with_prov = sorted(((k, v) for k, v in linked.items() if v), key=lambda x: int(x[0][1:]) if x[0][1:].isdigit() else 0)
    lines.append(f"{len(ctx.principles)} principles in PRINCIPLES.md; {len(with_prov)} with pattern provenance: "
                 + (", ".join(f"{k} ({len(v)})" for k, v in with_prov) or "none"))
    lines += ["", "## L5 meta-patterns", ""]
    if metas:
        for m in sorted(metas.values(), key=lambda x: x["id"]):
            lines.append(f"- `{m['id']}` [{m.get('status')}] {m.get('signal')}: {m.get('statement')} -> {m.get('proposal', '')}")
    else:
        lines.append("_none yet_")
    return "\n".join(lines) + "\n"


# ---------------------------------------------------------------- record (the only writer)

def _schema_check():
    spec = importlib.util.spec_from_file_location("schema_check", HARNESS_ROOT / "scripts" / "schema_check.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def append_lines(path, lines):
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "a", encoding="utf-8") as f:
        if fcntl:
            fcntl.flock(f, fcntl.LOCK_EX)
        try:
            for line in lines:
                f.write(line + "\n")
            f.flush()
            os.fsync(f.fileno())
        finally:
            if fcntl:
                fcntl.flock(f, fcntl.LOCK_UN)


def event_type_for(status):
    if status in ("approved", "encoded", "reopened"):
        return "pattern_promoted"
    if status in ("decaying", "retired"):
        return "pattern_retired"
    return "pattern_proposed"


def record(args):
    root = data_dir(args.data_dir)
    src = sys.stdin.read() if args.file == "-" else pathlib.Path(args.file).expanduser().read_text(encoding="utf-8")
    recs = []
    for n, line in enumerate(src.splitlines(), 1):
        if not line.strip():
            continue
        try:
            r = json.loads(line)
        except json.JSONDecodeError:
            print(f"error: line {n}: not JSON", file=sys.stderr)
            return 1
        if isinstance(r, dict) and isinstance(r.get("record"), dict):  # a ladder proposal: take its record
            r = r["record"]
        recs.append(r)
    sc = _schema_check()
    onto = sc.Ontology.load()
    rep = sc.Report()
    now = dt.datetime.now(dt.timezone.utc)
    by_store = collections.defaultdict(list)
    clean_recs = []
    for i, r in enumerate(recs, 1):
        r = {k: v for k, v in r.items() if not str(k).startswith("_")}
        pre = next((p for p in STORES if str(r.get("id", "")).startswith(p)), None)
        if pre is None:
            rep.err(f"line {i}", f"id {r.get('id')!r} is not a pat_/enc_/mp_ id")
            continue
        r.setdefault("ts", iso(now))
        r.setdefault("pattern_level", LEVELS[pre])
        if any(isinstance(v, str) and v.startswith("<") and v.endswith(">") for v in r.values()):
            rep.err(f"line {i}", f"{r['id']}: fill the <placeholders> first")
        sc.validate_records(TYPES[pre], [(f"line {i}", r)], onto, rep, where="")
        by_store[pre].append(r)
        clean_recs.append(r)
    if rep.errors:
        for e in rep.errors:
            print(f"ERROR {e}", file=sys.stderr)
        print("nothing written", file=sys.stderr)
        return 1
    for w in rep.warnings:
        print(f"warn  {w}", file=sys.stderr)
    if not clean_recs:
        print("nothing to record")
        return 1
    events = []
    for r in clean_recs:
        pre = next(p for p in STORES if r["id"].startswith(p))
        status = r.get("status")
        kind = r.get("kind") or r.get("signal")
        scope = r.get("scope") if isinstance(r.get("scope"), str) else None
        ev = {"id": f"evt_{now:%Y%m%d_%H%M%S}_{uuid.uuid4().hex[:4]}", "ts": now.isoformat(), "actor": args.actor,
              "type": event_type_for(status), "patterns": [r["id"]] + list(r.get("encodes") or []),
              "pattern_status": status, "scope": scope or "global",
              "intent": args.intent, "situation": args.situation or f"pattern-review recorded {r['id']} as {status}",
              "meta": {"kind_of_thing": f"pattern {status} ({LEVELS[pre]} {kind})",
                       "generalizes_to": list(r.get("areas") or []) or ["global"]},
              "content": str(r.get("statement") or r.get("target") or "")[:300],
              "pointers": [f"patterns/{STORES[pre]}"]}
        if r.get("gate"):
            ev["content"] += f" [eval gate: {r['gate']}]"
        events.append(ev)
    if args.dry_run:
        for pre, rs in by_store.items():
            print(f"dry run: would append {len(rs)} line(s) to {root / 'patterns' / STORES[pre]}")
        print(f"dry run: would append {len(events)} event(s) to {root / 'log' / f'{now:%Y-%m}.jsonl'}")
        return 0
    for pre, rs in by_store.items():
        append_lines(root / "patterns" / STORES[pre], [json.dumps(r, ensure_ascii=False) for r in rs])
        print(f"appended {len(rs)} line(s) to {root / 'patterns' / STORES[pre]}")
    append_lines(root / "log" / f"{now:%Y-%m}.jsonl", [json.dumps(e, ensure_ascii=False) for e in events])
    print(f"appended {len(events)} event(s) to {root / 'log' / f'{now:%Y-%m}.jsonl'}")
    return 0


# ---------------------------------------------------------------- output

def print_props(props, title):
    print(f"# {title}\n")
    if not props:
        print("_no proposals_")
        return
    layer = None
    for n, p in enumerate(props, 1):
        if p.get("layer") != layer:
            layer = p.get("layer")
            print(f"\n## {layer}\n")
        extra = ""
        if p.get("metrics"):
            extra = " | " + ", ".join(f"{k} {v}" for k, v in p["metrics"].items() if v not in (None, [], ""))
        print(f"{n}. **{p['action']}** `{p['id']}` {p.get('from') or ''} -> {p.get('to') or ''}: {p['reason']}"
              f"{extra} | needs: {', '.join(p.get('needs') or [])}")
        if p.get("patterns"):
            print(f"   patterns: {', '.join(p['patterns'])}")


def write_out(path, recs):
    if not path:
        return
    with open(pathlib.Path(path).expanduser(), "w", encoding="utf-8") as f:
        for r in recs:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
    print(f"\nwrote {len(recs)} proposed record(s) to {path} (review, then `patterns.py record --file {path}`)",
          file=sys.stderr)


def parse_date(s):
    try:
        return dt.date.fromisoformat(s)
    except ValueError:
        raise argparse.ArgumentTypeError(f"not a YYYY-MM-DD date: {s!r}")


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0],
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("command", choices=["mine", "ladder", "meta", "report", "record", "config"])
    ap.add_argument("--data-dir", help="defaults to $HARNESS_DATA or ~/harness-data")
    ap.add_argument("--today", type=parse_date, help="evaluate as of this date (default: now, UTC)")
    ap.add_argument("--project", action="append", default=[], help="project folder: read log/mishaps.md, decisions.md")
    ap.add_argument("--external", action="append", default=[], help="JSONL evidence from /insights, /usage, /skill-doctor")
    ap.add_argument("--auto-memory", action="append", default=[], help="auto-memory dir (feedback notes)")
    ap.add_argument("--seeds", help=f"seed file (default {SEEDS.relative_to(HARNESS_ROOT)})")
    ap.add_argument("--no-seeds", action="store_true", help="ignore the repo seed patterns")
    ap.add_argument("--principles", help="PRINCIPLES.md to read (default global/PRINCIPLES.md)")
    ap.add_argument("--json", action="store_true", help="machine output")
    ap.add_argument("--out", help="mine/ladder/meta: write the proposed records as JSONL to this file")
    ap.add_argument("--file", help="record: JSONL of records (or ladder proposals) to append; '-' = stdin")
    ap.add_argument("--actor", default="agent:librarian", help="record: actor on the logged events")
    ap.add_argument("--intent", default="pattern-review: record an approved change on the pattern ladder",
                    help="record: intent on the logged events")
    ap.add_argument("--situation", default="", help="record: situation on the logged events")
    ap.add_argument("--dry-run", action="store_true", help="record: validate and report only")
    ap.add_argument("--init", action="store_true", help="config: write the defaults to patterns/config.json if missing")
    a = ap.parse_args(argv)

    if a.command == "record":
        if not a.file:
            ap.error("record needs --file")
        try:
            return record(a)
        except OSError as e:
            print(f"error: {e}", file=sys.stderr)
            return 2
    if a.command == "config":
        root = data_dir(a.data_dir)
        p = root / "patterns" / "config.json"
        if a.init and not p.exists():
            p.parent.mkdir(parents=True, exist_ok=True)
            p.write_text(json.dumps(DEFAULTS, indent=2) + "\n", encoding="utf-8")
            print(f"wrote defaults to {p}", file=sys.stderr)
        print(json.dumps(load_config(root), indent=2))
        return 0

    ctx = Context(a)
    if a.command == "report":
        print(report(ctx), end="")
        return 0
    if a.command == "mine":
        new, updates = mine(ctx)
        if a.json:
            print(json.dumps({"candidates": new, "updates": updates}, ensure_ascii=False, indent=2))
        else:
            print(f"# L2 candidates ({len(ctx.episodes)} episodes, {ctx.cfg['window_weeks']} weeks)\n")
            for n, c in enumerate(new, 1):
                print(f"{n}. `{c['id']}` [{c['kind']}] {c['statement']} | support {c['support']}, sessions "
                      f"{c['sessions']}, areas {', '.join(c['areas']) or '-'}, confidence {c['confidence']}")
            if not new:
                print("_no new candidates_")
            if updates:
                print("\n## New evidence for existing patterns\n")
                for u in updates:
                    print(f"- `{u['id']}` [{u['status']}] +{len(u['new_evidence'])} episode(s) (similarity {u['similarity']})")
        write_out(a.out, new)
        return 0
    if a.command == "ladder":
        props = ladder(ctx)
        if a.json:
            print(json.dumps(props, ensure_ascii=False, indent=2, default=str))
        else:
            print_props(props, f"Ladder proposals ({ctx.now.date()}); nothing is applied without approval")
        write_out(a.out, [p["record"] for p in props if p.get("record") and p["action"] != "awaiting-approval"])
        return 0
    if a.command == "meta":
        ms = meta(ctx)
        if a.json:
            print(json.dumps(ms, ensure_ascii=False, indent=2))
        else:
            print(f"# L5 meta-pattern proposals ({ctx.now.date()})\n")
            for n, m in enumerate(ms, 1):
                print(f"{n}. `{m['id']}` [{m['signal']} -> {m['target']}] {m['statement']}\n   proposal: {m['proposal']}")
            if not ms:
                print("_no meta signals_")
        write_out(a.out, ms)
        return 0
    return 2


if __name__ == "__main__":
    sys.exit(main())
