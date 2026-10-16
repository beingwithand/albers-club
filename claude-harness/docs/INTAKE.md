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
- `convert` picks converters by file type and uses the first one that is installed and succeeds:

  | File | Order |
  |---|---|
  | `.hwp`, `.hwpx`, `.hml` | kordoc only |
  | any file with `--ocr` (Korean scans, image PDFs) | kordoc (with its `--ocr`), docling, marker |
  | everything else | markitdown, docling, marker_single, kordoc, pdftotext (PDF only, with `<!-- p.N -->` anchors) |

  Use `--converter NAME` to force one, or `--work DIR` to change where the output goes. To install one: `pipx install 'markitdown[all]'`, `npm install -g kordoc@4.22.5`, or `sudo apt install poppler-utils` for pdftotext.
- kb.py runs kordoc as `kordoc <file> -o <out.md> [--ocr]` and always sets `KORDOC_OFFLINE=1`, even for `kordoc --version`. It never falls back to `npx`, because that would download code at run time. Whether kordoc's Markdown carries `<!-- p.N -->` page anchors is **unverified**. Check the first output, and add the anchors by hand from the original if they are missing.
- A wiki page needs `source_id, source_name, pages, converter, confidence, intake_intent`. `topic` and `summary` are optional and feed `index.md`.
- Exit codes: `0` ok, `1` problems found (lint, not safe, backcatalog errors), `2` usage error or unknown id.

## Korean documents: kordoc and rhwp (one-time setup)

**kordoc** (MIT, reads HWP 3/5, HWPX, HWPML, PDF, Office and images, with local Korean OCR). Pin the version and never run `npx kordoc setup`, which rewrites every AI client config it finds.

```bash
npm install -g kordoc@4.22.5                       # CLI used by kb.py
kordoc models --status                             # OCR models present? (~18MB, PP-OCRv5 Korean)
# warm the OCR models ONCE, online, on a non-client file, then stay offline:
kordoc some-public-scan.pdf --ocr -o /tmp/warm.md  # downloads from huggingface.co
claude mcp add kordoc -e KORDOC_ROOT="$PWD" -e KORDOC_OFFLINE=1 -- npx -y kordoc@4.22.5 mcp
```

- `KORDOC_OFFLINE=1` blocks every outbound request: model downloads and `watch --webhook`. With it set, OCR fails cleanly if the models are not cached yet. `KORDOC_ROOT` limits the MCP server's file reads and writes to that folder, so set it to the project.
- Never use `kordoc watch --webhook`.

**rhwp** (MIT, Rust): use it to edit, fill and save HWP/HWPX/HML, for example to put a translation back into the client's file. Install it from the release binary, never from an unpinned script:

```bash
# download rhwp-v<version>-<platform>.tar.gz (e.g. linux-x86_64, macOS aarch64) and SHA256SUMS.txt
# from github.com/edwardkim/rhwp/releases (scout read v0.8.7), into an empty folder
sha256sum -c SHA256SUMS.txt --ignore-missing       # macOS: shasum -a 256 -c; must print OK, stop if not
tar xzf rhwp-v*-*.tar.gz && install -m 755 rhwp ~/.local/bin/
rhwp capabilities                                  # self-description of every command
claude mcp add rhwp -- rhwp mcp-serve              # stdio only, no network
```

Tools: `hwp_info`, `hwp_search`, `hwp_export_text`, `hwp_export_tables`, `hwp_fill_fields`, `hwp_open` / `hwp_doc_*` (`replace_text`, `set_cell`, `save`), `hwp_ir_diff`. Edit a copy in `work/`, never `raw/`. After saving, render the file or re-extract its text and compare it with what you meant to write.

Neither tool has been tried on real client files yet. Test both on 3–5 sample files before relying on them.

## Back catalog (old work)

```bash
$KB --kb "$HARNESS_DATA/backcatalog/knowledge" backcatalog ~/old-projects --report "$HARNESS_DATA/backcatalog/knowledge/backcatalog.csv"
```

This copies every file into `raw/`, never touches the source folder, and writes a CSV with empty `area`/`project` columns to fill in. Then follow `skills/backcatalog/SKILL.md` (`/backcatalog`).

## Tests

```bash
cd $H && python3 -I -m unittest discover -s tests -t . -p 'test_kb.py'
```

The converter tests use fake converters, so none need to be installed.

`python3 -m unittest tests.test_kb` works as well. With `-I`, use `discover`, because isolated mode drops the current directory from `sys.path`.
