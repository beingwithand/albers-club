"""Keep a CHANGELOG.md current for a scope (a project or the harness repo).

Format: Keep a Changelog (https://keepachangelog.com) — entries accumulate under `## [Unreleased]`
grouped as Added / Changed / Fixed / Removed / Decisions / Lessons. Updated at the end of every
session (retro/handoff skills, session-end pipeline).

  python3 -I changelog.py draft  --scope DIR [--since ISO|REF]   # propose entries (stdout), no writes
  python3 -I changelog.py update --scope DIR --file ENTRIES.md    # append approved entries + log event
  python3 -I changelog.py check  --scope DIR                       # exit 1 if work happened since last entry

Sources for `draft`: git commits in DIR since the last changelog update, plus decision/mishap/lesson
events for this scope in $HARNESS_DATA/log. A marker comment `<!-- last-update: ISO -->` records when
the changelog was last updated.
"""
import argparse
import datetime
import json
import os
import pathlib
import re
import subprocess
import sys

HEADER = "# Changelog\n\nAll notable changes, decisions and lessons for this scope.\nFormat: [Keep a Changelog](https://keepachangelog.com).\n\n## [Unreleased]\n"
SECTIONS = ["Added", "Changed", "Fixed", "Removed", "Decisions", "Lessons"]
MARK = re.compile(r"<!-- last-update: (\S+) -->")
PREFIX_SECTION = [
    (re.compile(r"^(add|new|create|introduc)", re.I), "Added"),
    (re.compile(r"^(fix|bug|correct|repair)", re.I), "Fixed"),
    (re.compile(r"^(remove|delete|drop)", re.I), "Removed"),
]


def data_dir():
    return pathlib.Path(os.environ.get("HARNESS_DATA", pathlib.Path.home() / "harness-data"))


def now_iso():
    return datetime.datetime.now(datetime.timezone.utc).isoformat(timespec="seconds")


def last_update(text):
    m = None
    for m in MARK.finditer(text):
        pass
    return m.group(1) if m else None


def git_commits(scope, since):
    if not (pathlib.Path(scope) / ".git").exists() and subprocess.run(
            ["git", "-C", str(scope), "rev-parse"], capture_output=True).returncode != 0:
        return []
    cmd = ["git", "-C", str(scope), "log", "--no-merges", "--format=%H%x1f%cI%x1f%s", "--", "."]
    if since:
        cmd.insert(4, f"--since={since}")
    try:
        out = subprocess.run(cmd, capture_output=True, text=True, timeout=10).stdout
    except Exception:
        return []
    rows = []
    for line in out.splitlines():
        parts = line.split("\x1f")
        if len(parts) == 3 and not parts[2].startswith("WIP snapshot"):
            if since and _after(since, parts[1]) is False:
                continue  # git --since is inclusive at second granularity; keep strictly-newer only
            rows.append({"sha": parts[0][:8], "ts": parts[1], "subject": parts[2]})
    return rows


def scope_events(scope, since):
    scope = str(pathlib.Path(scope).resolve())
    out = []
    for f in sorted((data_dir() / "log").glob("*.jsonl")):
        try:
            with f.open(encoding="utf-8") as fh:
              for line in fh:
                try:
                    ev = json.loads(line)
                except ValueError:
                    continue
                if ev.get("type") not in ("decision", "mishap", "lesson", "session_note"):
                    continue
                hint = str(ev.get("scope_hint") or ev.get("cwd") or "")
                if hint and not hint.startswith(scope):
                    continue
                if since and str(ev.get("ts", "")) <= since:
                    continue
                out.append(ev)
        except OSError:
            continue
    return out


def _after(since, ts):
    """True if ts is strictly after since; None if either can't be parsed."""
    try:
        a = datetime.datetime.fromisoformat(since.replace("Z", "+00:00"))
        b = datetime.datetime.fromisoformat(ts.replace("Z", "+00:00"))
        return b > a
    except ValueError:
        return None


def classify(subject):
    for rx, sec in PREFIX_SECTION:
        if rx.search(subject):
            return sec
    return "Changed"


def draft(scope, since=None):
    path = pathlib.Path(scope) / "CHANGELOG.md"
    text = path.read_text(encoding="utf-8") if path.exists() else ""
    since = since or last_update(text)
    buckets = {s: [] for s in SECTIONS}
    for c in git_commits(scope, since):
        buckets[classify(c["subject"])].append(f"- {c['subject']} ({c['sha']})")
    for ev in scope_events(scope, since):
        sec = {"decision": "Decisions", "mishap": "Lessons", "lesson": "Lessons"}.get(ev.get("type"))
        if sec:
            what = ev.get("claim") or ev.get("summary") or str(ev.get("content") or "")[:160]
            if what:
                buckets[sec].append(f"- {what} ({ev.get('id')})")
    lines = []
    for s in SECTIONS:
        if buckets[s]:
            lines.append(f"### {s}")
            lines.extend(buckets[s])
            lines.append("")
    return "\n".join(lines).strip()


def update(scope, entries_text):
    path = pathlib.Path(scope) / "CHANGELOG.md"
    text = path.read_text(encoding="utf-8") if path.exists() else HEADER
    if "## [Unreleased]" not in text:
        text = text.rstrip() + "\n\n## [Unreleased]\n"
    stamp = now_iso()
    block = f"\n<!-- last-update: {stamp} -->\n#### Session {stamp[:10]}\n{entries_text.strip()}\n"
    head, rest = text.split("## [Unreleased]", 1)
    nxt = re.search(r"\n## \[", rest)
    if nxt:
        text = head + "## [Unreleased]" + rest[:nxt.start()] + block + rest[nxt.start():]
    else:
        text = head + "## [Unreleased]" + rest.rstrip() + "\n" + block
    path.write_text(text, encoding="utf-8")
    log_dir = data_dir() / "log"
    log_dir.mkdir(parents=True, exist_ok=True)
    ev = {"id": f"evt_{datetime.datetime.now(datetime.timezone.utc):%Y%m%d_%H%M%S}_{os.urandom(4).hex()}",
          "ts": stamp, "actor": "harness", "type": "task", "labels": ["changelog_updated"],
          "scope_hint": str(pathlib.Path(scope).resolve()), "pointers": [str(path)],
          "content": f"changelog updated ({len(entries_text.splitlines())} lines)"}
    with open(log_dir / f"{stamp[:7]}.jsonl", "a", encoding="utf-8") as f:
        f.write(json.dumps(ev, ensure_ascii=False) + "\n")
    return ev


def check(scope):
    path = pathlib.Path(scope) / "CHANGELOG.md"
    text = path.read_text(encoding="utf-8") if path.exists() else ""
    since = last_update(text)
    pending = draft(scope, since)
    return (not pending), pending


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    sub = ap.add_subparsers(dest="cmd", required=True)
    for name in ("draft", "update", "check"):
        p = sub.add_parser(name)
        p.add_argument("--scope", default=".")
        if name == "draft":
            p.add_argument("--since")
        if name == "update":
            p.add_argument("--file", required=True, help="approved entries (markdown); '-' for stdin")
    a = ap.parse_args(argv)
    if a.cmd == "draft":
        print(draft(a.scope, a.since) or "(nothing new since the last changelog update)")
        return 0
    if a.cmd == "update":
        txt = sys.stdin.read() if a.file == "-" else pathlib.Path(a.file).read_text(encoding="utf-8")
        if not txt.strip():
            print("no entries given", file=sys.stderr)
            return 2
        ev = update(a.scope, txt)
        print(f"updated {pathlib.Path(a.scope) / 'CHANGELOG.md'} ({ev['id']})")
        return 0
    ok, pending = check(a.scope)
    if ok:
        print("changelog is current")
        return 0
    print("changelog is behind; pending entries:\n" + pending)
    return 1


if __name__ == "__main__":
    sys.exit(main())
