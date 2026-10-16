#!/usr/bin/env python3
"""Build the harness component graph, check it, and write docs/INDEX.md + docs/components.json.

    python3 -I scripts/harness_index.py --check          # no writes; exit 1 on errors (default mode)
    python3 -I scripts/harness_index.py --write          # regenerate docs/INDEX.md and docs/components.json
    python3 -I scripts/harness_index.py --json           # print the graph (same content as components.json)
    python3 -I scripts/harness_index.py --graph dot      # Graphviz text (pipe into `dot -Tsvg`)
    python3 -I scripts/harness_index.py --affected skills/translate/SKILL.md agents/coder.md [--json]
                                                         # eval areas to re-run after a change (self-eval)

Nodes: agents (frontmatter), skills (frontmatter), hooks (hooks/hooks.json), scripts (scripts/*.py|sh and
hooks/*.py, docstring first line), rubrics, eval areas (evals/<area>/), ontology types (store + writer),
docs (docs/*.md title), principles (global/PRINCIPLES.md), plus plain `file` nodes for other files that
reference components (README, BLUEPRINT, global/CLAUDE.md, schema/, config/, mac/, templates/).

Edges (src uses dst): preloads, invokes (skill), runs (script), scored_by (rubric), routes_to / runs_in
(agent), hook_runs, imports, writes / touches (ontology type), produced_by / for_skill (rubric),
evaluated_in (rubric -> eval area), reads / mentions (doc), cites (principle).

Checks. Errors (exit 1): dangling refs (skill/script/rubric/doc/agent named but missing), an agent
without an explicit `model:`, an agent preloading a skill with `disable-model-invocation: true` (Claude
Code cannot preload those), a worker agent that can spawn agents (only `may_spawn_agents` may), an
ontology writer naming a missing script/skill/agent, eval coverage below `coverage_min`, broken
hooks.json. Warnings: orphans (referenced by nothing), coverage gaps, stale config entries, unknown
principle numbers, draft rubrics.

Eval coverage: every agent and skill not listed in `exempt` (scripts/harness_index.json) must map to a
rubric AND an eval area. Rubric: `coverage_map` override, else rubrics/NAME.yaml named in its text, else a
rubric whose `producer_agent` names the agent (or that names skills/NAME / has id NAME), else inherited
from the agent it preloads into / runs in (skills) or the skills it preloads (agents). Area: an
evals/<area>/task_template.yaml whose `rubric:` is that rubric.

Output is deterministic (no timestamps), so `--write` only changes the files when the harness changed.
Stdlib only; run with `python3 -I`. Exit codes: 0 ok, 1 errors, 2 usage error.
"""
import argparse
import ast
import json
import pathlib
import re
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
CONFIG_NAME = "scripts/harness_index.json"
SELF = "scripts/harness_index.py"
INDEX_PATH = "docs/INDEX.md"
JSON_PATH = "docs/components.json"
LEARNING_PATH = "learning/contracts.yaml"
CADENCES = {"per-run", "weekly", "monthly", "on-change"}
OWNERS = {"librarian", "user", "self"}
CONTRACT_FIELDS = ("signals", "logged_as", "learns", "evaluated_by", "cadence", "owner")
GENERATED = {INDEX_PATH, JSON_PATH}
HEADER = "GENERATED — do not edit; run scripts/harness_index.py --write"
KIND_ORDER = ["agent", "skill", "hook", "script", "rubric", "eval", "type", "doc", "principle", "file"]
MODELS = {"haiku", "sonnet", "opus", "fable", "inherit"}
REFERRER_GLOBS = ["README.md", "BLUEPRINT.md", "settings.json", "install.sh", "global/*.md", "schema/*",
                  "config/*", "evals/README.md", "templates/**/*.md", "mac/**/*", "patterns/*.jsonl",
                  ".claude-plugin/*.json"]
TEXT_SUFFIXES = {".md", ".yaml", ".yml", ".json", ".jsonl", ".sh", ".py", ".plist", ".txt", ""}
DEFAULT_CONFIG = {"exempt": {}, "coverage_map": {}, "external_skills": [], "external_agents": [],
                  "may_spawn_agents": ["orchestrator"], "orphan_ignore": [], "coverage_min": 0}


# ---------------------------------------------------------------- small parsers

def read(p):
    try:
        return p.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError):
        return ""


def _unquote(v):
    v = v.strip()
    if len(v) >= 2 and v[0] == v[-1] and v[0] in "\"'":
        return v[1:-1]
    return v


def _strip_yaml_comment(v):
    """Drop a trailing ` # comment` outside quotes (enough for the scalar lines we read)."""
    v = v.strip()
    if v and v[0] in "\"'":
        end = v.find(v[0], 1)
        return v[:end + 1] if end > 0 else v
    return re.split(r"\s+#", v, maxsplit=1)[0].strip()


def _list(v):
    v = _unquote(v.strip())
    if v.startswith("[") and v.endswith("]"):
        v = v[1:-1]
    return [_unquote(x) for x in v.split(",") if x.strip()]


def frontmatter(text):
    """Top-level `key: value` lines between the first two `---` lines (multi-line values are skipped)."""
    lines = text.splitlines()
    if not lines or lines[0].strip() != "---":
        return {}, text
    fm, end = {}, None
    for i, line in enumerate(lines[1:], 1):
        if line.strip() == "---":
            end = i
            break
        m = re.match(r"^([A-Za-z][\w-]*):\s?(.*)$", line)
        if m:
            fm[m.group(1)] = m.group(2).strip()
    body = "\n".join(lines[end + 1:]) if end else ""
    return fm, body


def top_scalars(text):
    out = {}
    for line in text.splitlines():
        m = re.match(r"^([A-Za-z][\w-]*):[ \t]*(.*)$", line)
        if m and m.group(1) not in out:
            out[m.group(1)] = _unquote(_strip_yaml_comment(m.group(2)))
    return out


def first_sentence(s, n=90):
    s = re.sub(r"\s+", " ", (s or "").strip())
    m = re.match(r"^(.+?[.!?])(?=\s+[A-Z(\"'`]|$)", s)
    s = m.group(1) if m else s
    return s if len(s) <= n else s[:n - 1].rstrip() + "…"


def script_purpose(p):
    text = read(p)
    if p.suffix == ".py":
        try:
            doc = ast.get_docstring(ast.parse(text))
        except SyntaxError:
            doc = None
        return first_sentence(doc.strip().split("\n\n")[0], 120) if doc else ""
    for line in text.splitlines()[1:]:
        if line.startswith("#"):
            return line.lstrip("# ").strip()
    return ""


def bool_field(v):
    return str(v).strip().lower() in ("true", "yes", "1")


# ---------------------------------------------------------------- reference extraction

def _prefix_ok(pre):
    return pre == "" or pre.endswith("CLAUDE_PLUGIN_ROOT}/") or pre.endswith("claude-harness/") or pre == "./"


def path_refs(text, top, name_re, suffix=""):
    """Names X in `top/X<suffix>` written relative to the harness root (or ${CLAUDE_PLUGIN_ROOT}/...)."""
    pat = re.compile(r"(?<![\w.$/{}~-])((?:[\w${}.~-]+/)*)" + re.escape(top) + "/(" + name_re + ")"
                     + re.escape(suffix) + r"(?![\w-])")
    return [m.group(2) for m in pat.finditer(text) if _prefix_ok(m.group(1))]


def backticked(text):
    return set(re.findall(r"`([a-z][a-z0-9-]*)`", text))


def named_as(text, word):
    """Names written in backticks and followed by the word (skill, agent, ...)."""
    return set(re.findall(r"`(?:harness:)?([a-z][a-z0-9-]*)`\s+(?:" + word + r")\b", text))


def slash_mentions(text):
    return set(re.findall(r"(?:^|(?<=[\s`(\"']))/([a-z][a-z0-9-]*)(?![\w/-])(?!\.\w)", text, re.M))


# ---------------------------------------------------------------- graph

class Graph:
    def __init__(self, root, config):
        self.root = root
        self.config = config
        self.nodes = {}
        self.edges = set()
        self.errors = []
        self.warnings = []
        self.texts = {}       # node id -> text scanned for references
        self.coverage = {}
        self.learning = {}

    def add(self, nid, kind, name, path, purpose="", **attrs):
        self.nodes[nid] = {"id": nid, "kind": kind, "name": name, "path": path, "purpose": purpose,
                           "attrs": attrs}

    def edge(self, src, dst, etype):
        if src != dst:
            self.edges.add((src, dst, etype))

    def err(self, msg):
        self.errors.append(msg)

    def warn(self, msg):
        self.warnings.append(msg)

    def of_kind(self, kind):
        return sorted((n for n in self.nodes.values() if n["kind"] == kind), key=lambda n: n["name"])

    def users(self, nid, exclude_kinds=("file",)):
        return sorted({s for s, d, _ in self.edges if d == nid and self.nodes.get(s, {}).get("kind") not in exclude_kinds})

    def out(self, nid, etypes=None):
        return sorted({d for s, d, t in self.edges if s == nid and (etypes is None or t in etypes)})


def load_config(root):
    cfg = json.loads(json.dumps(DEFAULT_CONFIG))
    p = root / CONFIG_NAME
    if p.exists():
        try:
            data = json.loads(read(p))
        except json.JSONDecodeError as e:
            raise SystemExit(f"error: {CONFIG_NAME} is not valid JSON: {e}")
        for k, v in data.items():
            if not k.startswith("_"):
                cfg[k] = v
    return cfg


def rel(root, p):
    return p.relative_to(root).as_posix()


def scan(root=ROOT, config=None):
    root = pathlib.Path(root)
    g = Graph(root, config if config is not None else load_config(root))

    # agents
    for p in sorted((root / "agents").glob("*.md")):
        fm, body = frontmatter(read(p))
        name = fm.get("name") or p.stem
        tools = _list(fm["tools"]) if "tools" in fm else None
        g.add(f"agent:{name}", "agent", name, rel(root, p), first_sentence(_unquote(fm.get("description", ""))),
              model=fm.get("model"), effort=fm.get("effort"), tools=tools,
              disallowedTools=_list(fm.get("disallowedTools", "")), skills=_list(fm.get("skills", "")),
              memory=fm.get("memory"))
        g.texts[f"agent:{name}"] = read(p)

    # skills
    for p in sorted((root / "skills").glob("*/SKILL.md")):
        fm, body = frontmatter(read(p))
        name = fm.get("name") or p.parent.name
        g.add(f"skill:{name}", "skill", name, rel(root, p), first_sentence(_unquote(fm.get("description", ""))),
              dir=rel(root, p.parent), disable_model_invocation=bool_field(fm.get("disable-model-invocation", "")),
              user_invocable=not (fm.get("user-invocable", "").lower() == "false"),
              context=fm.get("context"), agent=fm.get("agent"))
        extra = [read(f) for f in sorted(p.parent.rglob("*")) if f.is_file() and f != p
                 and f.suffix in TEXT_SUFFIXES and "__pycache__" not in f.parts]
        g.texts[f"skill:{name}"] = "\n".join([read(p)] + extra)
        if name != p.parent.name:
            g.warn(f"skill dir skills/{p.parent.name} declares name '{name}'")

    # scripts (scripts/ and hooks/)
    for p in sorted(list((root / "scripts").glob("*.py")) + list((root / "scripts").glob("*.sh"))
                    + list((root / "hooks").glob("*.py"))):
        r = rel(root, p)
        g.add(f"script:{r}", "script", r, r, script_purpose(p), dir=p.parent.name, tests=[])
        if r != SELF:   # the scanner's own text is full of example names
            g.texts[f"script:{r}"] = read(p)

    # rubrics
    for p in sorted((root / "rubrics").glob("*.yaml")):
        sc = top_scalars(read(p))
        rid = sc.get("rubric") or p.stem
        if rid != p.stem:
            g.warn(f"rubrics/{p.name}: rubric id '{rid}' differs from the file name")
        g.add(f"rubric:{p.stem}", "rubric", p.stem, rel(root, p), first_sentence(sc.get("applies_to", ""), 80),
              status=sc.get("status", "active"), version=sc.get("version"),
              producer_agent=sc.get("producer_agent", ""))
        g.texts[f"rubric:{p.stem}"] = read(p)

    # eval areas
    for d in sorted(x for x in (root / "evals").glob("*") if x.is_dir() and x.name != "__pycache__"):
        tpl = d / "task_template.yaml"
        sc = top_scalars(read(tpl)) if tpl.exists() else {}
        tasks = sorted((d / "tasks").glob("*.yaml")) if (d / "tasks").is_dir() else []
        rubrics, components = [], []
        for src in ([tpl] if tpl.exists() else []) + tasks:
            text = read(src)
            m = re.search(r"(?m)^rubric:\s*['\"]?rubrics/([\w.-]+)\.yaml", text)
            if m and m.group(1) not in rubrics:
                rubrics.append(m.group(1))
            m = re.search(r"(?m)^components:\s*\[([^\]]*)\]", text)
            for c in (_list(m.group(1)) if m else []):
                if c not in components:
                    components.append(c)
        first = read(tpl).splitlines()[0] if tpl.exists() else ""
        if not first:
            first = next((l[2:] for l in read(d / "README.md").splitlines() if l.startswith("# ")), "")
        g.add(f"eval:{d.name}", "eval", d.name, rel(root, d) + "/",
              first_sentence(re.sub(r"^#\s*(Eval task template:\s*)?", "", first).split(". Copy")[0], 80),
              template=rel(root, tpl) if tpl.exists() else None, rubric=rubrics[0] if rubrics else None,
              rubrics=rubrics, components=components, repo_tasks=len(tasks))
        if not tpl.exists() and not tasks:
            g.err(f"evals/{d.name}/: no task_template.yaml and no tasks")
        elif not tpl.exists():
            g.warn(f"evals/{d.name}/: no task_template.yaml (rubric taken from its tasks)")
        elif sc.get("area") and sc["area"] != d.name:
            g.warn(f"evals/{d.name}/task_template.yaml: area '{sc['area']}' differs from the folder name")

    # docs
    for p in sorted((root / "docs").glob("*.md")):
        r = rel(root, p)
        if r in GENERATED:
            continue
        title = next((l[2:].strip() for l in read(p).splitlines() if l.startswith("# ")), p.stem)
        g.add(f"doc:{r}", "doc", r, r, title)
        g.texts[f"doc:{r}"] = read(p)

    # principles
    pr = root / "global" / "PRINCIPLES.md"
    for m in re.finditer(r"(?m)^(\d+)\. \*\*(.+?)\*\*", read(pr)):
        g.add(f"principle:{m.group(1)}", "principle", m.group(1), "global/PRINCIPLES.md", m.group(2).rstrip("."))

    # ontology types
    onto = root / "schema" / "ontology.yaml"
    in_types, cur = False, None
    for line in read(onto).splitlines():
        if re.match(r"^types:\s*$", line):
            in_types = True
            continue
        if in_types and re.match(r"^\S", line):
            in_types = False
        if not in_types:
            continue
        m = re.match(r"^  ([A-Z]\w*):", line)
        if m:
            cur = m.group(1)
            g.add(f"type:{cur}", "type", cur, "schema/ontology.yaml", "")
            continue
        if cur and line.startswith("    desc:"):
            g.nodes[f"type:{cur}"]["purpose"] = first_sentence(line.split(":", 1)[1], 80)
        if cur and line.startswith("    store:"):
            st = line.split(":", 1)[1]
            a = g.nodes[f"type:{cur}"]["attrs"]
            for key in ("root", "path", "format", "status"):
                mm = re.search(key + r':\s*("[^"]*"|[^,}]+)', st)
                a[key] = _unquote(mm.group(1)) if mm else None
            mm = re.search(r'writer:\s*"([^"]*)"', st)
            a["writer"] = mm.group(1) if mm else ""

    # eval areas must be declared in the ontology's eval_area enum (EvalTask.area)
    m = re.search(r"(?m)^\s+eval_area:\s*\[([^\]]*)\]", read(onto))
    if m:
        declared = {x.strip() for x in m.group(1).split(",") if x.strip()}
        for e in g.of_kind("eval"):
            if e["name"] not in declared:
                g.err(f"evals/{e['name']}/ is not in the ontology's eval_area enum (schema/ontology.yaml)")
        for name in sorted(declared - {e["name"] for e in g.of_kind("eval")}):
            g.warn(f"ontology eval_area '{name}' has no evals/{name}/ folder")

    # other referrer files
    seen = set()
    for pattern in REFERRER_GLOBS:
        for p in sorted(root.glob(pattern)):
            r = rel(root, p)
            if p.is_file() and r not in seen and p.suffix in TEXT_SUFFIXES and "__pycache__" not in p.parts:
                seen.add(r)
                g.add(f"file:{r}", "file", r, r, "")
                g.texts[f"file:{r}"] = read(p)

    link(g)
    check(g)
    coverage(g)
    learning(g)
    return g


def link(g):
    root = g.root
    skills = {n["name"] for n in g.of_kind("skill")}
    agents = {n["name"] for n in g.of_kind("agent")}
    ext_sk, ext_ag = set(g.config.get("external_skills", [])), set(g.config.get("external_agents", []))
    principles = {n["name"] for n in g.of_kind("principle")}

    def where(nid):
        return g.nodes[nid]["path"]

    for nid, text in sorted(g.texts.items()):
        kind = g.nodes[nid]["kind"]
        mention = kind in ("doc", "file")
        quiet = nid == "file:schema/ontology.yaml"   # its writers are checked below; avoid double reports
        err = (lambda msg: None) if quiet else g.err
        # scripts
        for top in ("scripts", "hooks"):
            for name in path_refs(text, top, r"[A-Za-z0-9_-]+\.(?:py|sh)"):
                tgt = f"script:{top}/{name}"
                if tgt in g.nodes:
                    g.edge(nid, tgt, "mentions" if mention else "runs")
                else:
                    err(f"dangling: {where(nid)} references {top}/{name} (missing)")
        # rubrics
        for name in path_refs(text, "rubrics", r"[a-z0-9][a-z0-9-]*", ".yaml"):
            if f"rubric:{name}" in g.nodes:
                g.edge(nid, f"rubric:{name}", "mentions" if mention else "scored_by")
            else:
                err(f"dangling: {where(nid)} references rubrics/{name}.yaml (missing)")
        # docs
        for name in path_refs(text, "docs", r"[A-Z][A-Z0-9_]*", ".md"):
            r = f"docs/{name}.md"
            if f"doc:{r}" in g.nodes:
                g.edge(nid, f"doc:{r}", "mentions" if mention else "reads")
            elif r not in GENERATED:
                err(f"dangling: {where(nid)} references {r} (missing)")
        # skills
        named_skills = set(path_refs(text, "skills", r"[a-z0-9][a-z0-9-]*")) | named_as(text, "skill|skills")
        for name in sorted(named_skills):
            if name in skills:
                g.edge(nid, f"skill:{name}", "mentions" if mention else "invokes")
            elif name not in ext_sk:
                err(f"dangling: {where(nid)} references skill '{name}' (missing; add to external_skills "
                      f"in {CONFIG_NAME} if it is not ours)")
        for name in (backticked(text) | slash_mentions(text)) & skills:
            g.edge(nid, f"skill:{name}", "mentions" if mention else "invokes")
        # agents
        named_agents = set(path_refs(text, "agents", r"[a-z0-9][a-z0-9-]*", ".md")) | named_as(text, "agent|agents|subagent")
        named_agents |= {n for n in path_refs(text, "agents", r"[a-z0-9][a-z0-9-]*") if n in agents}
        for name in sorted(named_agents):
            if name in agents:
                g.edge(nid, f"agent:{name}", "mentions" if mention else "routes_to")
            elif name not in ext_ag:
                err(f"dangling: {where(nid)} references agent '{name}' (missing)")
        for name in backticked(text) & agents:
            g.edge(nid, f"agent:{name}", "mentions" if mention else "routes_to")
        # principles
        for num in re.findall(r"\b[Pp]rinciples?\s+#?(\d+)\b", text):
            if num in principles:
                g.edge(nid, f"principle:{num}", "cites")
            elif nid != "file:global/PRINCIPLES.md":
                g.warn(f"{where(nid)} cites principle {num}, which global/PRINCIPLES.md does not have")

    # agent frontmatter: preloaded skills
    for a in g.of_kind("agent"):
        for s in a["attrs"]["skills"]:
            s = s.split(":", 1)[-1]
            if s in skills:
                g.edge(a["id"], f"skill:{s}", "preloads")
            else:
                g.err(f"dangling: {a['path']} preloads skill '{s}' (missing)")

    # skill frontmatter: agent / context
    for s in g.of_kind("skill"):
        ag = s["attrs"].get("agent")
        if ag:
            ag = ag.split(":", 1)[-1]
            if ag in agents:
                g.edge(s["id"], f"agent:{ag}", "runs_in")
            elif ag not in ext_ag and ag not in ("general-purpose", "Explore", "Plan"):
                g.err(f"dangling: {s['path']} runs in agent '{ag}' (missing)")

    # hooks
    hj = root / "hooks" / "hooks.json"
    if hj.exists():
        try:
            data = json.loads(read(hj))
        except json.JSONDecodeError as e:
            g.err(f"hooks/hooks.json is not valid JSON: {e}")
            data = {}
        g.add("file:hooks/hooks.json", "file", "hooks/hooks.json", "hooks/hooks.json", "")
        for event, groups in sorted((data.get("hooks") or {}).items()):
            for gi, grp in enumerate(groups or []):
                matcher = grp.get("matcher", "")
                for hi, h in enumerate(grp.get("hooks") or []):
                    cmd = h.get("command", "")
                    refs = [f"{t}/{n}" for t in ("hooks", "scripts")
                            for n in path_refs(cmd, t, r"[A-Za-z0-9_-]+\.(?:py|sh)")]
                    script = refs[0] if refs else None
                    arg = cmd.split(".py\"", 1)[-1].strip() if ".py\"" in cmd else ""
                    hid = f"hook:{event}:{gi}.{hi}"
                    g.add(hid, "hook", f"{event}" + (f"[{matcher}]" if matcher else ""), "hooks/hooks.json",
                          "", event=event, matcher=matcher, command=cmd, script=script, arg=arg,
                          timeout=h.get("timeout"))
                    g.edge("file:hooks/hooks.json", hid, "mentions")
                    for r in refs:
                        if f"script:{r}" in g.nodes:
                            g.edge(hid, f"script:{r}", "hook_runs")
                        else:
                            g.err(f"dangling: hooks/hooks.json {event} runs {r} (missing)")

    # script imports and tests
    for s in g.of_kind("script"):
        text = g.texts.get(s["id"], "")
        for mod in re.findall(r"(?m)^\s*(?:from|import)\s+([A-Za-z_]\w*)", text):
            tgt = f"script:{s['attrs']['dir']}/{mod}.py"
            if tgt in g.nodes:
                g.edge(s["id"], tgt, "imports")
        stem = pathlib.PurePosixPath(s["path"]).stem
        base = pathlib.PurePosixPath(s["path"]).name
        for t in sorted((root / "tests").glob("test_*.py")):
            tt = read(t)
            if re.search(r"\b" + re.escape(base) + r"\b", tt) or re.search(r"[\"']" + re.escape(stem) + r"[\"']", tt):
                s["attrs"]["tests"].append(rel(root, t))

    # rubric -> producer agents, skills; rubric -> eval areas
    for r in g.of_kind("rubric"):
        prod = r["attrs"]["producer_agent"]
        for tok in re.findall(r"[a-z][a-z0-9-]*", prod):
            if tok in agents:
                g.edge(r["id"], f"agent:{tok}", "produced_by")
        for name in set(path_refs(g.texts[r["id"]], "skills", r"[a-z0-9][a-z0-9-]*")) | ({r["name"]} & skills):
            if name in skills:
                g.edge(r["id"], f"skill:{name}", "for_skill")
    for e in g.of_kind("eval"):
        for rb in e["attrs"]["rubrics"]:
            if f"rubric:{rb}" in g.nodes:
                g.edge(f"rubric:{rb}", e["id"], "evaluated_in")
            else:
                g.err(f"dangling: {e['path']} uses rubrics/{rb}.yaml (missing)")
        if not e["attrs"]["rubrics"]:
            g.err(f"{e['path']}: no `rubric: rubrics/<name>.yaml` line in its template or tasks")
        for c in e["attrs"]["components"]:
            c = c.lstrip("./")
            hit = sorted(n["id"] for n in g.nodes.values() if n["kind"] not in ("type", "principle", "hook")
                         and (n["path"] == c or (n["kind"] == "skill" and c.rstrip("/") == n["attrs"]["dir"])))
            if hit:
                g.edge(e["id"], hit[0], "evaluates")
            elif not (root / c).exists():
                g.err(f"dangling: {e['path']} tasks name component {c} (missing)")

    # ontology writers and store paths
    for t in g.of_kind("type"):
        segs = re.split(r";\s*", t["attrs"].get("writer") or "")
        w = "; ".join(x for x in segs if not x.startswith("read by"))
        for x in segs:
            if x.startswith("read by"):
                for top in ("scripts", "hooks"):
                    for n in path_refs(x, top, r"[A-Za-z0-9_-]+\.(?:py|sh)"):
                        if f"script:{top}/{n}" in g.nodes:
                            g.edge(f"script:{top}/{n}", t["id"], "reads_store")
                        else:
                            g.err(f"ontology: {t['name']}.store.writer names {top}/{n} (missing)")
        for top, suffix_re, kind in (("scripts", r"[A-Za-z0-9_-]+\.(?:py|sh)", "script"),
                                     ("hooks", r"[A-Za-z0-9_-]+\.py", "script")):
            for n in path_refs(w, top, suffix_re):
                tgt = f"script:{top}/{n}"
                if tgt in g.nodes:
                    g.edge(tgt, t["id"], "writes")
                else:
                    g.err(f"ontology: {t['name']}.store.writer names {top}/{n} (missing)")
        for top, pool in (("skills", skills), ("agents", agents)):
            for n in path_refs(w, top, r"[a-z0-9][a-z0-9-]*"):
                if n in pool:
                    g.edge(f"{top[:-1]}:{n}", t["id"], "writes")
                else:
                    g.err(f"ontology: {t['name']}.store.writer names {top}/{n} (missing)")
        path = t["attrs"].get("path") or ""
        if path and not re.search(r"[*<>]|YYYY", path):
            base = path.rsplit("/", 1)[-1]
            for s in g.of_kind("script"):
                if re.search(r"(?<![\w.-])" + re.escape(base) + r"(?![\w.-])", g.texts.get(s["id"], "")):
                    g.edge(s["id"], t["id"], "touches")


def check(g):
    cfg = g.config
    may_spawn = set(cfg.get("may_spawn_agents", []))
    skills = {n["name"]: n for n in g.of_kind("skill")}
    for a in g.of_kind("agent"):
        at = a["attrs"]
        if not at.get("model"):
            g.err(f"{a['path']}: no explicit `model:` (agents must set one)")
        elif at["model"] not in MODELS:
            g.warn(f"{a['path']}: model '{at['model']}' is not one of {sorted(MODELS)}")
        for s in at["skills"]:
            sk = skills.get(s.split(":", 1)[-1])
            if sk and sk["attrs"]["disable_model_invocation"]:
                g.err(f"{a['path']}: preloads '{sk['name']}', which has disable-model-invocation: true "
                      "(Claude Code cannot preload such skills into an agent)")
        if a["name"] not in may_spawn:
            tools, dis = at.get("tools"), set(at.get("disallowedTools") or [])
            if tools is not None and ({"Agent", "Task"} & set(tools)):
                g.err(f"{a['path']}: worker agent lists the Agent tool (only {sorted(may_spawn)} may spawn)")
            elif tools is None and "Agent" not in dis:
                g.err(f"{a['path']}: worker agent inherits all tools incl. Agent; set `tools:` or "
                      "`disallowedTools: Agent`")
    ignore = set(cfg.get("orphan_ignore", []))
    for n in sorted(g.nodes.values(), key=lambda n: n["id"]):
        if n["kind"] in ("agent", "skill", "script", "rubric", "eval", "doc") and n["id"] not in ignore:
            used = any(d == n["id"] for _, d, _t in g.edges)
            if n["kind"] == "rubric":   # a rubric is in use when an eval area or producer is tied to it
                used = used or any(s == n["id"] and t in ("evaluated_in", "produced_by", "for_skill")
                                   for s, _d, t in g.edges)
            if not used:
                g.warn(f"orphan: {n['kind']} {n['name']} ({n['path']}) is referenced by nothing")
    for r in g.of_kind("rubric"):
        if r["attrs"]["status"] == "draft":
            g.warn(f"draft rubric: {r['path']} (status: draft; the user must review it before it gates anything)")
    for key in ("exempt", "coverage_map"):
        for cid in sorted(cfg.get(key, {})):
            if cid not in g.nodes:
                g.warn(f"{CONFIG_NAME}: {key} entry '{cid}' names no component")
    for cid, rubs in sorted(cfg.get("coverage_map", {}).items()):
        for rb in rubs:
            if f"rubric:{rb}" not in g.nodes:
                g.err(f"{CONFIG_NAME}: coverage_map {cid} -> rubric '{rb}' (missing)")
    for cid in sorted(ignore):
        if cid not in g.nodes:
            g.warn(f"{CONFIG_NAME}: orphan_ignore entry '{cid}' names no component")


def rubrics_for(g, nid, inherit=True):
    cmap = g.config.get("coverage_map", {})
    if nid in cmap:
        return sorted(f"rubric:{r}" for r in cmap[nid] if f"rubric:{r}" in g.nodes), "config"
    direct = set(g.out(nid, {"scored_by"}))
    direct |= {s for s, d, t in g.edges if d == nid and t in ("produced_by", "for_skill")}
    if direct:
        return sorted(direct), "direct"
    if not inherit:
        return [], ""
    kind = g.nodes[nid]["kind"]
    via = set()
    if kind == "skill":
        hosts = {s for s, d, t in g.edges if d == nid and t == "preloads"} | set(g.out(nid, {"runs_in"}))
        for h in hosts:
            via |= set(rubrics_for(g, h, inherit=False)[0])
    else:
        for s in g.out(nid, {"preloads"}):
            via |= set(rubrics_for(g, s, inherit=False)[0])
    return sorted(via), "inherited" if via else ""


def coverage(g):
    exempt = g.config.get("exempt", {})
    rows = []
    for n in g.of_kind("agent") + g.of_kind("skill"):
        if n["id"] in exempt:
            rows.append({"id": n["id"], "status": "exempt", "reason": exempt[n["id"]], "rubrics": [], "areas": []})
            continue
        rubs, how = rubrics_for(g, n["id"])
        direct_areas = {s for s, d, t in g.edges if d == n["id"] and t == "evaluates"}
        rubs = sorted(set(rubs) | {f"rubric:{r}" for a in direct_areas for r in g.nodes[a]["attrs"]["rubrics"]
                                   if f"rubric:{r}" in g.nodes})
        how = how or ("evaluated" if direct_areas else "")
        areas = sorted({d for r in rubs for d in g.out(r, {"evaluated_in"})} | direct_areas)
        bare = [r for r in rubs if not g.out(r, {"evaluated_in"})]
        status = ("no-rubric" if not rubs else "no-area" if not areas else "partial" if bare else "covered")
        drafts = [r for r in rubs if g.nodes[r]["attrs"]["status"] == "draft"]
        rows.append({"id": n["id"], "status": status, "rubrics": rubs, "areas": areas, "via": how,
                     "draft": bool(drafts)})
    work = [r for r in rows if r["status"] != "exempt"]
    covered = [r for r in work if r["status"] == "covered"]
    pct = round(100.0 * len(covered) / len(work), 1) if work else 100.0
    g.coverage = {"work_components": len(work), "covered": len(covered), "percent": pct,
                  "exempt": len(rows) - len(work), "gaps": [r["id"] for r in work if r["status"] != "covered"],
                  "covered_by_draft_rubric": [r["id"] for r in covered if r.get("draft")], "rows": rows}
    for r in work:
        if r["status"] != "covered":
            bare = [x.split(":")[1] for x in r["rubrics"] if not g.out(x, {"evaluated_in"})]
            what = "no rubric" if r["status"] == "no-rubric" else f"rubric {', '.join(bare)} has no eval area"
            g.warn(f"coverage gap: {r['id']} ({what}); add a rubric + evals/<area>/task_template.yaml, "
                   f"a coverage_map entry, or an exemption in {CONFIG_NAME}")
    cmin = float(g.config.get("coverage_min", 0) or 0)
    if pct + 1e-9 < cmin:
        g.err(f"eval coverage {pct}% is below coverage_min {cmin:g}% ({len(work) - len(covered)} gap(s))")


# ---------------------------------------------------------------- learning coverage

def _yaml_loader(root):
    """yaml_load from scripts/schema_check.py (the harness's one YAML-subset parser)."""
    import importlib.util
    for base in (root, ROOT):
        p = base / "scripts" / "schema_check.py"
        if p.exists():
            spec = importlib.util.spec_from_file_location("_hi_schema_check", p)
            mod = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(mod)
            return mod.yaml_load
    raise SystemExit("error: scripts/schema_check.py not found (needed to read learning/contracts.yaml)")


def _as_list(v):
    if v is None or v == "":
        return []
    return [str(x) for x in v] if isinstance(v, list) else [x.strip() for x in str(v).split(",") if x.strip()]


def learning(g):
    """Every agent, skill and script needs a learning contract (learning/contracts.yaml) or an exemption with
    a reason. Missing for a work-producing agent/skill (one that needs eval coverage) is an error."""
    root, path = g.root, g.root / LEARNING_PATH
    contracts, exempt = {}, {}
    if path.exists():
        try:
            data = _yaml_loader(root)(read(path)) or {}
        except ValueError as e:
            g.err(f"{LEARNING_PATH}: cannot parse: {e}")
            data = {}
        contracts, exempt = data.get("contracts") or {}, data.get("exempt") or {}
    event_types = set()
    m = re.search(r"(?m)^\s+event_type:\s*\[([^\]]*)\]", read(root / "schema" / "ontology.yaml"))
    if m:
        event_types = {x.strip() for x in m.group(1).split(",")}
    types = {n["name"] for n in g.of_kind("type")}
    todo = []
    for cid, c in sorted(contracts.items()):
        if not isinstance(c, dict):
            g.err(f"{LEARNING_PATH}: contract {cid} must be a mapping")
            continue
        if cid not in g.nodes:
            if c.get("status") == "todo":
                todo.append(cid)
            else:
                g.warn(f"{LEARNING_PATH}: contract '{cid}' names no component (set status: todo if it is coming)")
            continue
        if c.get("status") == "todo":
            todo.append(cid)
        for f in CONTRACT_FIELDS:
            if not _as_list(c.get(f)):
                g.err(f"{LEARNING_PATH}: {cid} has no `{f}`")
        for cad in _as_list(c.get("cadence")):
            if cad not in CADENCES:
                g.err(f"{LEARNING_PATH}: {cid} cadence '{cad}' not in {sorted(CADENCES)}")
        for o in _as_list(c.get("owner")):
            if o not in OWNERS:
                g.err(f"{LEARNING_PATH}: {cid} owner '{o}' not in {sorted(OWNERS)}")
        for item in _as_list(c.get("logged_as")) + _as_list(c.get("learns")):
            kind, _, val = item.partition(":")
            val = val.split()[0] if val.split() else val
            if kind == "event" and event_types and val not in event_types:
                g.err(f"{LEARNING_PATH}: {cid} names event type '{val}', not in the ontology's event_type enum")
            elif kind == "type":
                if val in types:
                    g.edge(cid, f"type:{val}", "learns_into" if item in _as_list(c.get("learns")) else "logs")
                else:
                    g.err(f"{LEARNING_PATH}: {cid} names ontology type '{val}' (missing)")
        for item in _as_list(c.get("logged_as")):
            if item.partition(":")[0] not in ("event", "type", "store"):
                g.err(f"{LEARNING_PATH}: {cid} logged_as '{item}' must start with event:, type: or store:")
        for item in _as_list(c.get("evaluated_by")):
            kind, _, val = item.partition(":")
            if kind in ("eval", "rubric"):
                val = val.split()[0] if val.split() else val
                if f"{kind}:{val}" in g.nodes:
                    g.edge(cid, f"{kind}:{val}", "learning_eval")
                else:
                    g.err(f"{LEARNING_PATH}: {cid} evaluated_by {item} (missing)")
            elif kind != "metric":
                g.err(f"{LEARNING_PATH}: {cid} evaluated_by '{item}' must start with eval:, rubric: or metric:")
    for cid, reason in sorted(exempt.items()):
        if cid not in g.nodes:
            g.warn(f"{LEARNING_PATH}: exemption '{cid}' names no component")
        elif not str(reason or "").strip():
            g.err(f"{LEARNING_PATH}: exemption {cid} needs a reason")
        if cid in contracts:
            g.warn(f"{LEARNING_PATH}: {cid} has both a contract and an exemption")
    work = {r["id"] for r in g.coverage.get("rows", []) if r["status"] != "exempt"}
    rows = []
    for n in g.of_kind("agent") + g.of_kind("skill") + g.of_kind("script"):
        nid = n["id"]
        if nid in contracts:
            c = contracts[nid]
            rows.append({"id": nid, "status": "contract", "draft": c.get("status") in ("draft", "todo"),
                         "cadence": _as_list(c.get("cadence")), "owner": _as_list(c.get("owner")),
                         "learns": _as_list(c.get("learns"))})
        elif nid in exempt:
            rows.append({"id": nid, "status": "exempt", "reason": str(exempt[nid])})
        else:
            rows.append({"id": nid, "status": "gap"})
            if nid in work:
                g.err(f"learning: work component {nid} has no learning contract or exemption in {LEARNING_PATH}")
            else:
                g.warn(f"learning gap: {nid} has no contract or exemption in {LEARNING_PATH}")
    hooks_uncovered = [h["id"] for h in g.of_kind("hook")
                       if not any(r["id"] == f"script:{h['attrs']['script']}" and r["status"] != "gap" for r in rows)]
    for h in hooks_uncovered:
        g.warn(f"learning gap: {h} ({g.nodes[h]['name']}) runs a script without a contract")
    need = [r for r in rows if r["status"] != "exempt"]
    have = [r for r in need if r["status"] == "contract"]
    g.learning = {"components": len(rows), "with_contract": len(have), "exempt": len(rows) - len(need),
                  "percent": round(100.0 * len(have) / len(need), 1) if need else 100.0,
                  "gaps": [r["id"] for r in rows if r["status"] == "gap"], "draft": sum(1 for r in have if r["draft"]),
                  "todo": todo, "hooks_uncovered": hooks_uncovered, "rows": rows}


# ---------------------------------------------------------------- affected areas (eval-on-change)

GLOBAL_FILES = ("global/", "settings.json", "hooks/hooks.json", "config/", "schema/ontology.yaml")


def affected(g, paths):
    """Eval areas to re-run when these files change: the changed components, everything that depends on
    them (reverse edges), and for routers/exempt components one hop of what they route to."""
    paths = [p.lstrip("./") for p in paths]
    all_areas = sorted(n["id"] for n in g.of_kind("eval"))
    changed, reasons, areas = set(), [], set()
    for p in paths:
        if p.startswith(GLOBAL_FILES):
            reasons.append(f"{p}: global rule/config → all areas")
            areas |= set(all_areas)
            continue
        hit = [n["id"] for n in g.nodes.values() if n["kind"] not in ("file", "principle", "type", "hook")
               and (n["path"] == p or (n["kind"] == "skill" and p.startswith(n["attrs"]["dir"] + "/"))
                    or (n["kind"] == "eval" and p.startswith(n["path"])))]
        if not hit:
            reasons.append(f"{p}: not a component")
        changed |= set(hit)
    closure, todo = set(changed), list(changed)
    while todo:
        cur = todo.pop()
        for s, d, t in g.edges:
            if d == cur and s not in closure and t not in ("mentions", "evaluated_in", "produced_by", "for_skill") \
                    and g.nodes[s]["kind"] in ("agent", "skill", "script", "hook"):
                closure.add(s)
                todo.append(s)
    cov = {r["id"]: r for r in g.coverage.get("rows", [])}
    areas |= {s for s, d, t in g.edges if t == "evaluates" and d in closure}
    for nid in sorted(closure):
        n = g.nodes[nid]
        if n["kind"] == "eval":
            areas.add(nid)
        elif n["kind"] == "rubric":
            areas |= set(g.out(nid, {"evaluated_in"}))
        elif nid in cov:
            row = cov[nid]
            areas |= set(row["areas"])
            if row["status"] == "exempt" and nid in changed:
                for d in g.out(nid, {"routes_to", "preloads", "invokes", "runs_in"}):
                    areas |= set(cov.get(d, {}).get("areas", []))
    return {"changed": sorted(changed), "dependents": sorted(closure - changed),
            "areas": sorted(a.split(":", 1)[1] for a in areas), "notes": reasons}


# ---------------------------------------------------------------- outputs

def to_json(g):
    nodes = sorted(g.nodes.values(), key=lambda n: (KIND_ORDER.index(n["kind"]), n["id"]))
    edges = [{"src": s, "dst": d, "type": t} for s, d, t in sorted(g.edges)]
    counts = {k: sum(1 for n in nodes if n["kind"] == k) for k in KIND_ORDER}
    return {"generated_by": "scripts/harness_index.py", "note": HEADER, "counts": counts,
            "coverage": g.coverage, "learning": g.learning, "errors": g.errors, "warnings": g.warnings, "nodes": nodes, "edges": edges}


def _link(n, base="../"):
    return f"[{n['name']}]({base}{n['path']})"


def _short(nid):
    return nid.split(":", 1)[1]


_NOT_USERS = ("file", "doc", "rubric", "eval", "type", "principle")


def _label(g, nid):
    n = g.nodes[nid]
    return n["name"] if n["kind"] in ("hook", "skill", "agent") else _short(nid)


def _cell(s):
    return (s or "").replace("|", "\\|")


def render_index(g):
    L = [f"<!-- {HEADER} -->", "# Harness index", "",
         f"{HEADER}. Machine-readable graph: [components.json](components.json). "
         "Edges mean \"uses\"; `--affected <files>` lists the eval areas to re-run after a change."]
    c = to_json(g)["counts"]
    cv = g.coverage
    L[-1] += (" Counts: " + ", ".join(f"{c[k]} {k}s" for k in KIND_ORDER if k != "file" and c[k]) + ". "
              f"Eval coverage: **{cv['covered']}/{cv['work_components']} work components ({cv['percent']}%)**, "
              f"{cv['exempt']} exempt. Learning coverage: **{g.learning.get('with_contract', 0)}/"
              f"{g.learning.get('components', 0) - g.learning.get('exempt', 0)} ({g.learning.get('percent', 0)}%)**, "
              f"{g.learning.get('exempt', 0)} exempt. Errors: {len(g.errors)}. Warnings: {len(g.warnings)}.")

    L += ["", "## Agents", "", "| agent | model | preloads | purpose |", "|---|---|---|---|"]
    for a in g.of_kind("agent"):
        at = a["attrs"]
        L.append(f"| {_link(a)} | {at.get('model') or '**none**'} | {', '.join(at['skills']) or '-'} | {_cell(a['purpose'])} |")

    L += ["", "## Skills", "", "Flags: M = manual only (`disable-model-invocation`), H = hidden from the user "
          "(`user-invocable: false`), F = runs forked in an agent.",
          "| skill | flags | scripts | purpose |", "|---|---|---|---|"]
    for s in g.of_kind("skill"):
        at = s["attrs"]
        flags = ("M" if at["disable_model_invocation"] else "") + ("" if at["user_invocable"] else "H") + \
                (f"F→{at['agent']}" if at.get("agent") else "")
        scr = ", ".join(pathlib.PurePosixPath(_short(x)).stem for x in g.out(s["id"], {"runs"}))
        L.append(f"| {_link(s, '../')} | {flags or '-'} | {scr or '-'} | {_cell(s['purpose'])} |")

    L += ["", "## Hooks", "", "| event | matcher | runs |", "|---|---|---|"]
    for h in sorted(g.of_kind("hook"), key=lambda n: n["id"]):
        at = h["attrs"]
        L.append(f"| {at['event']} | {_cell(at['matcher']) or '-'} | `{at['script'] or at['command']}` {at['arg']} |")

    L += ["", "## Scripts", "", "| script | used by | tests | purpose |", "|---|---|---|---|"]
    for s in g.of_kind("script"):
        tests = ", ".join(pathlib.PurePosixPath(t).stem.replace("test_", "") for t in s["attrs"]["tests"])
        us = [_label(g, u) for u in g.users(s["id"], exclude_kinds=_NOT_USERS)]
        L.append(f"| {_link(s)} | {_cell(', '.join(us)) or '-'} | {tests or '**none**'} | {_cell(s['purpose'])} |")

    L += ["", "## Rubrics and eval areas", "", "| rubric | status | producer | eval area (repo tasks) | applies to |",
          "|---|---|---|---|---|"]
    for r in g.of_kind("rubric"):
        ar = ", ".join(f"{_short(e)} ({g.nodes[e]['attrs']['repo_tasks']})" for e in g.out(r["id"], {"evaluated_in"}))
        prod = ", ".join(_short(x) for x in g.out(r["id"], {"produced_by"})) or _cell(r["attrs"]["producer_agent"]) or "-"
        L.append(f"| {_link(r)} | {r['attrs']['status']} | {prod} | {ar or '**none**'} | {_cell(r['purpose'])} |")
    no_rub = [e["name"] for e in g.of_kind("eval") if not any(d == e["id"] for _, d, t in g.edges if t == "evaluated_in")]
    if no_rub:
        L.append(f"\nEval areas without a rubric: {', '.join(no_rub)}.")
    L.append("\nEval tasks live in `evals/<area>/tasks/` (repo) or `$HARNESS_DATA/evals/<area>/tasks/`; "
             "results in `$HARNESS_DATA/evals/results/<area>/`. Run them with the `self-eval` skill.")

    L += ["", "## Eval coverage", "", "| component | rubric | area | status |", "|---|---|---|---|"]
    for row in cv["rows"]:
        if row["status"] == "exempt":
            continue
        rub = ", ".join(_short(x) for x in row["rubrics"]) or "-"
        if row.get("draft"):
            rub += " (draft)"
        st = row["status"] + (f" ({row['via']})" if row.get("via") and row["via"] != "direct" else "")
        L.append(f"| {row['id']} | {rub} | {', '.join(_short(x) for x in row['areas']) or '-'} | {st} |")
    ex = [f"{_short(r['id'])}" for r in cv["rows"] if r["status"] == "exempt"]
    L.append(f"\nExempt (meta/router/judge, see `{CONFIG_NAME}`): {', '.join(ex) or 'none'}.")

    lc = g.learning
    L += ["", f"## Learning coverage ([contracts](../{LEARNING_PATH}))", "",
          f"Every agent, skill and script declares how it learns (signals → logged as → learns → evaluated by, "
          f"cadence, owner) or is exempt with a reason. **{lc.get('with_contract', 0)} contracts "
          f"({lc.get('draft', 0)} draft), {lc.get('exempt', 0)} exempt, {len(lc.get('gaps', []))} gaps "
          f"({lc.get('percent', 0)}%).**"]
    by = {}
    for r in lc.get("rows", []):
        if r["status"] == "contract":
            for cad in r["cadence"] or ["?"]:
                by.setdefault(cad, []).append(_label(g, r["id"]))
    for cad in sorted(by):
        L.append(f"- {cad}: {', '.join(by[cad])}")
    if lc.get("gaps"):
        L.append(f"- **gaps**: {', '.join(lc['gaps'])}")
    if lc.get("todo"):
        L.append(f"- todo (declared, not built yet): {', '.join(lc['todo'])}")

    L += ["", "## Who uses what (`X ← users`; docs and other files left out)", ""]
    for n in g.of_kind("skill") + g.of_kind("agent"):
        us = [_label(g, u) for u in g.users(n["id"], exclude_kinds=_NOT_USERS)]
        if us:
            L.append(f"- {n['kind']} `{n['name']}` ← {', '.join(us)}")
    wr = {}
    for s, d, t in sorted(g.edges):
        if t == "writes":
            wr.setdefault(_short(s), []).append(_short(d))
    if wr:
        L.append("- ontology writers: " + "; ".join(f"`{k}` → {', '.join(v)}" for k, v in sorted(wr.items())))

    L += ["", "## Ontology types (by store root)", ""]
    roots = {}
    for t in g.of_kind("type"):
        roots.setdefault(t["attrs"].get("root") or "?", []).append(
            t["name"] + ("" if t["attrs"].get("status") != "planned" else "*"))
    for rname, names in sorted(roots.items()):
        L.append(f"- **{rname}**: {', '.join(names)}")
    L.append("\n`*` = planned (declared, nothing writes it yet). Stores and writers: `schema/ontology.yaml`.")

    L += ["", "## Docs and principles", "", "| doc | title | mentioned by |", "|---|---|---|"]
    for d in g.of_kind("doc"):
        L.append(f"| [{pathlib.PurePosixPath(d['path']).name}]({pathlib.PurePosixPath(d['path']).name}) | "
                 f"{_cell(d['purpose'])} | {len(g.users(d['id'], exclude_kinds=()))} |")
    pr = [f"{p['name']} {p['purpose']}" for p in sorted(g.of_kind("principle"), key=lambda n: int(n["name"]))]
    if pr:
        L.append("\nPrinciples ([PRINCIPLES.md](../global/PRINCIPLES.md)): " + " · ".join(pr) + ".")

    L += ["", "## Errors and warnings", ""]
    if not g.errors and not g.warnings:
        L.append("None.")
    for e in g.errors:
        L.append(f"- ERROR {_cell(e)}")
    cap = 40
    for w in g.warnings[:cap]:
        L.append(f"- {_cell(w)}")
    if len(g.warnings) > cap:
        L.append(f"- … {len(g.warnings) - cap} more (run `--check`)")
    return "\n".join(L) + "\n"


def render_dot(g):
    colors = {"agent": "lightblue", "skill": "palegreen", "hook": "orange", "script": "khaki", "rubric": "pink",
              "eval": "plum", "type": "lightgrey", "doc": "white"}
    L = ["digraph harness {", "  rankdir=LR; node [shape=box, style=filled, fontsize=10];"]
    shown = {n["id"] for n in g.nodes.values() if n["kind"] in colors}
    for nid in sorted(shown):
        n = g.nodes[nid]
        L.append(f'  "{nid}" [label="{n["kind"]}\\n{n["name"]}", fillcolor={colors[n["kind"]]}];')
    for s, d, t in sorted(g.edges):
        if s in shown and d in shown and t != "mentions":
            L.append(f'  "{s}" -> "{d}" [label="{t}", fontsize=8];')
    L.append("}")
    return "\n".join(L) + "\n"


def outputs(g):
    return {INDEX_PATH: render_index(g), JSON_PATH: json.dumps(to_json(g), indent=1, ensure_ascii=False) + "\n"}


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    m = p.add_mutually_exclusive_group()
    m.add_argument("--check", action="store_true", help="check only (default)")
    m.add_argument("--write", action="store_true", help=f"write {INDEX_PATH} and {JSON_PATH}")
    m.add_argument("--graph", choices=["dot"], help="print the graph in Graphviz format")
    m.add_argument("--affected", nargs="+", metavar="PATH", help="eval areas affected by changed files")
    p.add_argument("--json", action="store_true", help="print JSON (graph, or the --affected result)")
    p.add_argument("--root", default=str(ROOT), help="harness root (default: this repo)")
    p.add_argument("--quiet", action="store_true", help="print only errors and the summary line")
    a = p.parse_args(argv)
    root = pathlib.Path(a.root).resolve()
    if not (root / "agents").is_dir() and not (root / "skills").is_dir():
        print(f"error: {root} does not look like a harness (no agents/ or skills/)", file=sys.stderr)
        return 2
    g = scan(root)
    if a.affected:
        res = affected(g, a.affected)
        if a.json:
            print(json.dumps(res, indent=1))
        else:
            print("areas to re-run: " + (", ".join(res["areas"]) or "none"))
            print("changed: " + (", ".join(res["changed"]) or "none"))
            print("dependents: " + (", ".join(res["dependents"]) or "none"))
            for n in res["notes"]:
                print("note: " + n)
        return 0
    if a.graph:
        sys.stdout.write(render_dot(g))
        return 0
    if a.json:
        print(json.dumps(to_json(g), indent=1, ensure_ascii=False))
        return 1 if g.errors else 0
    if a.write:
        for path, content in outputs(g).items():
            f = root / path
            f.parent.mkdir(parents=True, exist_ok=True)
            if read(f) != content:
                f.write_text(content, encoding="utf-8")
                print(f"wrote {path}")
    for e in g.errors:
        print(f"ERROR {e}")
    if not a.quiet:
        for w in g.warnings:
            print(f"warning: {w}")
    cv = g.coverage
    print(f"{len(g.nodes)} nodes, {len(g.edges)} edges; coverage {cv['covered']}/{cv['work_components']} "
          f"({cv['percent']}%), {cv['exempt']} exempt; {len(g.errors)} error(s), {len(g.warnings)} warning(s)")
    return 1 if g.errors else 0


if __name__ == "__main__":
    sys.exit(main())
