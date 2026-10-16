# Local-only tools for client text

Client documents, translations, synopses and annotation tasks are often confidential or under NDA. **Never send client text to a cloud converter, OCR service, spellchecker, translator or diagram renderer.** That covers the source, the draft and the final version. Use the local tools below. If no local tool can do the job, stop and ask the user. Don't quietly switch to a cloud one.

Public material is fine to send: a show's public title, cast and network for press searches (`synopsis`), or a sample file you made yourself to warm up a tool.

Source: the scout report of 2026-10-16 (`research_notes/Claude harness/scout_domain_skills.md`). Nothing below has been run on real client files yet. Re-check a tool's network behaviour whenever you upgrade it.

## Local (allowed for client text)

| Tool | Used by | Conditions |
|---|---|---|
| `scripts/kb.py`, `translation_qa.py`, `glossary.py`, `textlen.py` | intake, translate, synopsis, translation-qa | Stdlib only, no network |
| **kordoc** 4.22.5 (CLI and MCP) | intake (`.hwp/.hwpx/.hml`, Korean scans) | Always run with `KORDOC_OFFLINE=1`, which kb.py sets for you. For the MCP, also set `KORDOC_ROOT=<project dir>`. The OCR models come from huggingface.co **once**: warm them on a non-client file, then go offline. Never use `watch --webhook`. Never run `npx kordoc setup`. Pin `kordoc@4.22.5` |
| **rhwp** (`rhwp mcp-serve`) | editing and saving HWP/HWPX | Stdio only, no network code found. Install the release binary only after `sha256sum -c SHA256SUMS.txt` passes. The maintainer's "HWP 2024 remote conversion" service is not part of the MCP: don't use it |
| markitdown, docling, marker, pdftotext | intake | Local. docling and marker download their models on first use, so warm them on a non-client file |
| **translate-toolkit** (`pofilter`) | translation-qa | Local CLI. GPL-3.0 only matters if you redistribute it |
| **kiwipiepy** | translation-qa (Korean glossary matching) | Bundled model, no network |
| Anthropic `document-skills` (docx/pdf/xlsx/pptx) | translate deliverables, redlines | Local Python scripts |
| **PaddleOCR MCP** in `local` mode | intake OCR fallback (handwriting, hard layouts) | Only with `PADDLEOCR_MCP_PPOCR_SOURCE=local` |

## Cloud or network (never with client text)

| Tool | What leaves the machine | Instead |
|---|---|---|
| Naver spellcheck: winterjung/mcp-korean-spell, Alfex4936/Hangul-MCP | The full text, posted to Naver's public endpoint. Both are also stale | Proofread yourself. `translation-qa` covers spacing and terms; Kiwi spacing if installed |
| Nara/PNU spellcheck (nara-speller.co.kr): the `spell_nara.py` path in eun7661010/korean-content-review, k-skill `korean-spell-check` | The full text | Same as above. Copy only the local `kiwi-spacing` idea |
| **k-skill** bundle (NomaDamas) | Each skill runs `npx -y @nomadamas/k-skill@0 instruct …`, which **fetches its instructions from npm at use time** (unpinned major). The setup skill offers to star its GitHub repo for you | Don't install. Copy reviewed text (e.g. the AI-tell taxonomy) into our own skills |
| Dayoooun/hwpx-mcp and the flamingo8006 fork | **Mermaid diagram source goes to `https://mermaid.ink`**, and the server has 125+ tools | kordoc to read, rhwp to edit |
| Adobe `adobe-for-creativity` plugin | Any PDF goes to `adobe-creativity.adobe.io`. Its skill text claims "MANDATORY: any PDF task…", which hijacks routing | Keep it uninstalled. Use the local PDF path in `intake` |
| PaddleOCR MCP with `PADDLEOCR_MCP_PPOCR_SOURCE=aistudio` or `qianfan` | The document, uploaded to Baidu | `local` mode only |
| kordoc **without** `KORDOC_OFFLINE=1` | Model downloads (no document content), and webhook POSTs if `watch --webhook` is used | Always set the flag |
| `npx -y <pkg>` without a version, or `npx kordoc setup` | Code fetched at run time. `setup` also edits every AI client config it finds | Pin versions. Register MCP servers by hand with `claude mcp add` |
| saidsurucu/subtitle-translator-skill | Subtitles sent to Codex CLI (OpenAI) for translation | Our `translate` skill |
| Online MT or QA (DeepL, Google Translate, Papago web), FreelanceOS | The full text or client data | Don't use. Ask the user if a client explicitly requires a specific tool |

## Rules
- **Before adding any tool to this harness,** grep it for network calls (`fetch`, `http`, `requests`, `curl`, `axios`, `urllib`, hard-coded hostnames) and for runtime installs (`npx`, `postinstall`, self-updaters). Then add it to one of the tables above.
- **Pin versions** (`kordoc@4.22.5`, a release binary with a checked SHA256). Upgrading is a deliberate step that includes re-reading the tool's network behaviour.
- **Annotation platforms** often forbid copying task content off the platform at all. Check the platform's ToS before running any tool on its tasks, even a local one.
