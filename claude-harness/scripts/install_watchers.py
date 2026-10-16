#!/usr/bin/env python3
"""Generate and install one launchd inbox watcher per project (launchd WatchPaths cannot glob).

    python3 -I scripts/install_watchers.py list [--root DIR ...] [--depth N]
    python3 -I scripts/install_watchers.py render <project dir>              # print the plist
    python3 -I scripts/install_watchers.py install [--root DIR ...] [--dry-run]
    python3 -I scripts/install_watchers.py uninstall [--dry-run]

A project is a directory (up to --depth 3 below a root) that holds `inbox/` and `PROGRESS.md` or `CLAUDE.md`.
Roots default to $HARNESS_PROJECT_ROOTS (colon-separated) or ~/projects. Each plist is rendered from
mac/launchd/com.harness.inbox-watch.plist as com.harness.inbox-watch.<slug>.plist into ~/Library/LaunchAgents
and loaded with `launchctl bootstrap gui/<uid>`; uninstall boots out and removes every plist with that prefix.
The watcher only queues files (`pipeline.py queue scan`); it never runs claude (docs/PIPELINES.md).
Re-run `install` after creating a project (new-project). Stdlib only. Exit 0 ok, 1 error, 2 usage.
"""
import argparse
import os
import pathlib
import re
import subprocess
import sys
from xml.sax.saxutils import escape

ROOT = pathlib.Path(__file__).resolve().parent.parent
TEMPLATE = ROOT / "mac" / "launchd" / "com.harness.inbox-watch.plist"
PREFIX = "com.harness.inbox-watch."
SKIP_DIRS = {".git", "node_modules", ".venv", "__pycache__", "knowledge", "deliverables", "work", "assets", "log"}


def roots_from(args_roots, env):
    if args_roots:
        return [pathlib.Path(r).expanduser() for r in args_roots]
    env_roots = env.get("HARNESS_PROJECT_ROOTS")
    if env_roots:
        return [pathlib.Path(r).expanduser() for r in env_roots.split(":") if r]
    return [pathlib.Path.home() / "projects"]


def find_projects(roots, depth=3):
    out = []
    for r in roots:
        if not r.is_dir():
            continue
        stack = [(r, 0)]
        while stack:
            d, lvl = stack.pop()
            if (d / "inbox").is_dir() and ((d / "PROGRESS.md").is_file() or (d / "CLAUDE.md").is_file()):
                out.append(d.resolve())
                continue
            if lvl >= depth:
                continue
            try:
                kids = sorted(p for p in d.iterdir() if p.is_dir() and not p.name.startswith(".") and p.name not in SKIP_DIRS)
            except OSError:
                continue
            stack += [(k, lvl + 1) for k in reversed(kids)]
    return sorted(dict.fromkeys(out))


def slug(project, roots):
    project = pathlib.Path(project).resolve()
    rel = None
    for r in roots:
        try:
            rel = project.relative_to(pathlib.Path(r).expanduser().resolve()).as_posix()
            break
        except ValueError:
            continue
    s = re.sub(r"[^a-z0-9]+", "-", (rel or project.name).lower()).strip("-")
    return s or "project"


def render(project, label, env, harness=None):
    home = str(pathlib.Path.home())
    harness = harness or env.get("HARNESS_DEV_ROOT") or str(ROOT)
    data = env.get("HARNESS_DATA") or os.path.join(home, "harness-data")
    text = TEMPLATE.read_text(encoding="utf-8")
    text = re.sub(r"<!--.*?-->\n", "", text, count=1, flags=re.S)  # drop the template's instructions
    for k, v in (("__LABEL__", label), ("__HOME__", home), ("__PROJECT__", str(project)),
                 ("__HARNESS__", str(harness)), ("__HARNESS_DATA__", str(data))):
        text = text.replace(k, escape(v))
    return text


def agents_dir():
    return pathlib.Path.home() / "Library" / "LaunchAgents"


def launchctl(*args, dry):
    cmd = ["launchctl", *args]
    if dry:
        print("would run: " + " ".join(cmd))
        return 0
    try:
        return subprocess.run(cmd, capture_output=True, text=True, timeout=20).returncode
    except (OSError, subprocess.SubprocessError) as e:
        print(f"launchctl failed: {e}", file=sys.stderr)
        return 1


def main(argv=None):
    ap = argparse.ArgumentParser(prog="install_watchers.py", description=__doc__.split("\n\n")[0])
    sub = ap.add_subparsers(dest="cmd", required=True)
    for name in ("list", "install"):
        p = sub.add_parser(name)
        p.add_argument("--root", action="append", default=[])
        p.add_argument("--depth", type=int, default=3)
        if name == "install":
            p.add_argument("--dry-run", action="store_true")
            p.add_argument("--harness", default=None, help="harness checkout (default HARNESS_DEV_ROOT or this repo)")
    p = sub.add_parser("render"); p.add_argument("project"); p.add_argument("--label", default=None)
    p = sub.add_parser("uninstall"); p.add_argument("--dry-run", action="store_true")
    a = ap.parse_args(argv)
    env = os.environ
    if a.cmd == "render":
        proj = pathlib.Path(a.project).expanduser().resolve()
        print(render(proj, a.label or PREFIX + slug(proj, roots_from([], env)), env))
        return 0
    if a.cmd == "list":
        roots = roots_from(a.root, env)
        for pr in find_projects(roots, a.depth):
            print(f"{PREFIX}{slug(pr, roots)}\t{pr}")
        return 0
    uid = str(os.getuid()) if hasattr(os, "getuid") else "501"
    if a.cmd == "install":
        if sys.platform != "darwin" and not a.dry_run:
            print("install needs macOS launchd; use --dry-run elsewhere", file=sys.stderr)
            return 1
        roots = roots_from(a.root, env)
        projects = find_projects(roots, a.depth)
        if not projects:
            print("no projects found under " + ", ".join(map(str, roots)))
            return 0
        dest = agents_dir()
        if not a.dry_run:
            dest.mkdir(parents=True, exist_ok=True)
            (pathlib.Path.home() / "Library" / "Logs" / "harness").mkdir(parents=True, exist_ok=True)
        for pr in projects:
            label = PREFIX + slug(pr, roots)
            path = dest / f"{label}.plist"
            text = render(pr, label, env, a.harness)
            if a.dry_run:
                print(f"would write {path} (watches {pr / 'inbox'})")
            else:
                path.write_text(text, encoding="utf-8")
                print(f"wrote {path}")
            launchctl("bootout", f"gui/{uid}/{label}", dry=a.dry_run)
            launchctl("bootstrap", f"gui/{uid}", str(path), dry=a.dry_run)
        return 0
    if a.cmd == "uninstall":
        for path in sorted(agents_dir().glob(PREFIX + "*.plist")):
            label = path.stem
            launchctl("bootout", f"gui/{uid}/{label}", dry=a.dry_run)
            if a.dry_run:
                print(f"would remove {path}")
            else:
                path.unlink(missing_ok=True)
                print(f"removed {path}")
        return 0
    return 2


if __name__ == "__main__":
    sys.exit(main())
