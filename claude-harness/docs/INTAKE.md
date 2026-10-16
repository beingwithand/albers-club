# Intake how-to

`scripts/kb.py` manages a project's `knowledge/` folder (layout: BLUEPRINT §0.5, steps: `skills/intake/SKILL.md`). It uses only the Python standard library. Always run it isolated with `python3 -I`. Run these from the project root (the default `--kb` is `./knowledge`), and set `H` to the harness folder:

```bash
H=~/code/claude-harness          # or $CLAUDE_PLUGIN_ROOT inside Claude Code
KB="python3 -I $H/scripts/kb.py"
```

## One source, end to end

```bash
$KB register inbox/brief.pdf          # -> registered 1a2b3c4d raw/1a2b3c4d_brief.pdf
$KB converters                        # which converters are installed
$KB convert 1a2b3c4d                  # -> work/intake/1a2b3c4d.raw.md, converter@version in manifest
#   (clean the Markdown, write knowledge/wiki/*.md pages with the intake frontmatter)
$KB index                             # rebuild knowledge/index.md from the wiki frontmatter
$KB lint                              # exit 1 if any frontmatter, source id or raw/...#p.N link is wrong
#   (verifier appends to knowledge/log.md:  - 2026-10-16 1a2b3c4d verify PASS 3/3 passages, tables ok)
$KB archive 1a2b3c4d https://drive.google.com/file/d/...
$KB safe-to-delete 1a2b3c4d           # prints "yes" (exit 0) only if verified AND archived
```

- `register` is idempotent: the same bytes under another name are reported as `already registered`.
- `convert` tries markitdown, docling, marker_single, then pdftotext (PDF only, with `<!-- p.N -->` anchors). Use `--converter NAME` to force one, or `--work DIR` to change where the output goes. To install one: `pipx install 'markitdown[all]'`, or `sudo apt install poppler-utils` for pdftotext.
- A wiki page needs `source_id, source_name, pages, converter, confidence, intake_intent`. `topic` and `summary` are optional and feed `index.md`.
- Exit codes: `0` ok, `1` problems found (lint, not safe, backcatalog errors), `2` usage error or unknown id.

## Back catalog (old work)

```bash
$KB --kb "$HARNESS_DATA/backcatalog/knowledge" backcatalog ~/old-projects --report "$HARNESS_DATA/backcatalog/knowledge/backcatalog.csv"
```

This copies every file into `raw/`, never touches the source folder, and writes a CSV with empty `area`/`project` columns to fill in. Then follow `skills/backcatalog/SKILL.md` (`/backcatalog`).

## Tests

```bash
cd $H && python3 -I -m unittest discover -s tests -t . -p 'test_kb.py'
```

`python3 -m unittest tests.test_kb` works as well. With `-I`, use `discover`, because isolated mode drops the current directory from `sys.path`.
