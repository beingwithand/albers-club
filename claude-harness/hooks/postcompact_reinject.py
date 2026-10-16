"""SessionStart hook (matcher "compact", also "clear"): put the durable state back in context.

After compaction only the system prompt, root CLAUDE.md, unscoped rules, auto memory, a few
recent files and invoked skill bodies survive; hook-added context and path-scoped rules are
summarized away. This hook re-adds, as hookSpecificOutput.additionalContext:

  1. HANDOFF.md (up to ~6k chars, with a pointer to the full file; marked stale if HEAD moved
     since its git_commit, and reduced to a pointer if older than 48 h)
  2. a pointer to the newest auto snapshot (log/handoffs/auto_*.md from precompact_snapshot.py)
  3. PROGRESS.md "In progress" and "Next" sections
  4. paths of the project's rules / reviewer files to re-read (path-scoped rules are lost)

Total stays under MAX_CHARS (8000). Outside a project, or with nothing to say, it prints
nothing. Never fails: any error exits 0 silently.
"""
import importlib.util
import json
import os
import pathlib
import re
import sys

_spec = importlib.util.spec_from_file_location("harness_common", pathlib.Path(__file__).resolve().parent / "_common.py")
C = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(C)

MAX_CHARS = 8000
HANDOFF_MAX = 6000
HANDOFF_STALE_S = 48 * 3600
SECTION_MAX = 1200
MAX_RULE_FILES = 20
HEADING = re.compile(r"^(#{1,6})\s*(.+?)\s*$")


def md_section(text, names):
    """Body of the first heading whose title starts with one of names (case-insensitive)."""
    lines = text.splitlines()
    for i, line in enumerate(lines):
        m = HEADING.match(line)
        if not m or not m.group(2).strip().lower().startswith(names):
            continue
        level, body = len(m.group(1)), []
        for nxt in lines[i + 1:]:
            h = HEADING.match(nxt)
            if h and len(h.group(1)) <= level:
                break
            body.append(nxt)
        body = re.sub(r"<!--.*?-->", "", "\n".join(body), flags=re.S).strip()
        return body or None
    return None


def rule_files(root):
    cands = [root / "CLAUDE.md", root / ".claude" / "CLAUDE.md", root / "CLAUDE.local.md", root / "decisions.md"]
    rules = root / ".claude" / "rules"
    if rules.is_dir():
        cands += sorted(rules.rglob("*.md"))
    agents = root / ".claude" / "agents"
    if agents.is_dir():
        cands += sorted(p for p in agents.glob("*.md") if re.search(r"review|verif|critic|judge", p.name, re.I))
    for d in (root / "rubrics", root / ".claude" / "rubrics"):
        if d.is_dir():
            cands += sorted(d.glob("*.y*ml"))
    out = [p for p in cands if p.is_file()]
    return out[:MAX_RULE_FILES], max(0, len(out) - MAX_RULE_FILES)


def build(payload, env, now):
    root = C.project_root(payload.get("cwd") if isinstance(payload.get("cwd"), str) else None)
    if root is None:
        return None
    source = payload.get("source") or "compact"
    head = C.git(root, "rev-parse", "--short", "HEAD")
    parts = []

    # 2-4 first (small, fixed size); the handoff gets whatever budget is left.
    snap = C.newest((root / "log" / "handoffs").glob("auto_*.md")) if (root / "log" / "handoffs").is_dir() else None
    if snap:
        parts.append(f"## Newest auto snapshot\n`{snap[0]}` ({C.age_str(now - snap[1])} old): git status, "
                     "PROGRESS tail and recent decisions captured just before compaction. Read it if HANDOFF.md "
                     "is missing or stale.")
    prog = root / "PROGRESS.md"
    if prog.is_file():
        text = prog.read_text(encoding="utf-8", errors="replace")
        for title in (("in progress",), ("next",)):
            body = md_section(text, title)
            if body:
                parts.append(f"## PROGRESS.md: {title[0].title()}\n" + C.truncate(body, SECTION_MAX, str(prog)))
    files, extra = rule_files(root)
    if files:
        parts.append("## Re-read before acting (rules and reviewer files; path-scoped rules were dropped)\n"
                     + "\n".join(f"- `{p}`" for p in files) + (f"\n- … +{extra} more" if extra else ""))

    ho = root / "HANDOFF.md"
    if ho.is_file():
        age = now - ho.stat().st_mtime
        text = ho.read_text(encoding="utf-8", errors="replace")
        rec = C.handoff_commit(text)
        flags = []
        if rec and head and not (head.startswith(rec) or rec.startswith(head)):
            flags.append(f"STALE: written at `{rec}`, HEAD is now `{head}`; run its verify-first list before trusting it")
        header = f"## HANDOFF.md (`{ho}`, {C.age_str(age)} old)" + ("".join(f"\n⚠ {f}" for f in flags))
        if age > HANDOFF_STALE_S:
            parts.insert(0, header + "\nOlder than 48 h, so not inlined. Read it only if it matches the current task.")
        else:
            used = sum(len(p) + 2 for p in parts) + 600  # 600 = intro + header slack
            budget = max(800, min(HANDOFF_MAX, MAX_CHARS - used - len(header)))
            parts.insert(0, header + "\n" + C.truncate(text.strip(), budget, str(ho)))

    if not parts:
        return None
    intro = (f"[harness] Session {source}: state re-injected from disk ({root}). Files are the source of "
             "truth; the summary above may have lost detail. If the user's next request is unrelated to this "
             "project state, ignore this block.")
    out = intro + "\n\n" + "\n\n".join(parts)
    return C.truncate(out, MAX_CHARS)


def main():
    try:
        payload = C.read_payload(sys.stdin)
        ctx = build(payload, os.environ, C.now())
        if ctx:
            sys.stdout.write(json.dumps({"hookSpecificOutput": {"hookEventName": "SessionStart",
                                                                "additionalContext": ctx}}, ensure_ascii=False))
    except Exception:
        pass
    return 0


if __name__ == "__main__":
    sys.exit(main())
