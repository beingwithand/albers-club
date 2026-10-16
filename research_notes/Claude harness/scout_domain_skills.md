# Scout: existing skills, plugins and MCP servers for the work domains

Date: 2026-10-16. Scope: translation and localization, data annotation, documents and OCR, job search and freelancing, art and design.
Method: web search, plus shallow clones of every candidate into the scratchpad. I read README, SKILL.md and manifests, and grepped for network calls, install hooks and hooks.json. Nothing was executed. Repo metadata (stars, license, last push) came from the GitHub search API on 2026-10-16.
Stars are treated as attention only (BLUEPRINT §0.5).

Verdict key: **adopt** means install from the official source and wrap it in a harness skill (BLUEPRINT §9). **Borrow** means copy ideas or text into our own curated skill and install nothing. **Avoid** means don't use it.

---

## 0. Headline findings

1. **There is almost nothing official for translation, annotation or job search.** `anthropics/claude-plugins-official` (315 plugins) has no translation, localization, annotation or career plugin. The domain-relevant official items are the **document skills** (anthropics/skills), **figma**, **canva**, **adobe-for-creativity** and **intuit-quickbooks**. The Gmail, Calendar, Drive and Figma claude.ai connectors are already attached to this account.
2. **The Korean document problem (HWP/HWPX) is solved well by two MIT projects.**
   - **kordoc** reads and converts HWP 3/5, HWPX, PDF and Office files, and includes local Korean OCR.
   - **rhwp** is the upstream Rust engine. It now ships its **own built-in MCP server** for reading, searching, filling and editing.

   Most other HWP MCP servers are wrappers or forks with weaker hygiene.
3. **The harness `intake` skill has a gap.** Its converter list (markitdown, docling, marker, MinerU) handles none of HWP or HWPX. Add kordoc as the converter for `.hwp`, `.hwpx` and `.hml`, and for Korean scanned PDFs.
4. **Translation QA must be built, not installed.** No Claude skill does CAT-style QA covering tags, numbers, terminology, TMX and XLIFF. The right parts are **translate-toolkit** (`pofilter` checks plus XLIFF/TMX storage, GPL-3.0, used as a CLI tool) and **kiwipiepy**. Kiwi is needed because Korean glossary-term matching must see past particles (조사): "계약서를" has to match the term "계약서".
5. **Confidentiality is the main security risk in these domains, more than malware.** Several "Korean spell check" tools send text to Naver's or Nara's public endpoints. One HWPX server sends diagram code to mermaid.ink. Adobe's plugin routes any PDF to Adobe's cloud. For client translation work and annotation tasks (often under NDA), default to local-only tools.
6. **Several popular community repos install or update code at runtime.**
   - k-skill skills run `npx -y @nomadamas/k-skill@0 instruct …`, which fetches their instructions from npm at use time.
   - career-ops runs `postinstall` (a Chromium download) and has a self-updater.
   - The setup skill in k-skill offers to star its own GitHub repo for you.

   Treat these as **borrow**, never install.

---

## 1. Translation and localization

### Top picks

| Candidate | What it is | License · last push · stars | Security read | Verdict | Harness slot | Install (official source) |
|---|---|---|---|---|---|---|
| **translate/translate** (Translate Toolkit) | `pofilter` QA (numbers, xmltags, variables, brackets, notranslatewords, untranslated, double-spacing, etc.) on PO/XLIFF/TMX. Also has XLIFF/TMX/TBX storage classes, `poconflicts` and `po2tmx` | GPL-3.0 · 2026-10-16 · 981 | Local CLI/library, no network. GPL only matters if you redistribute code; calling it as a tool is fine | **Adopt (as tool)** | New `translation-qa` skill, called by the `translator` and `verifier` agents | `pipx install translate-toolkit` (PyPI, from translate/translate) |
| **bab2min/kiwipiepy** (Kiwi) | Korean morphological analysis, spacing correction, sentence split, user dictionary | Apache-2.0 · 2026-10-16 · 408 | Local, bundled model, no network | **Adopt (as library)** | `translation-qa`: particle-aware term matching, spacing check on EN→KO output. Also used for character counts | `pip install kiwipiepy` |
| **eun7661010/korean-content-review** | 4 skills: `korean-content-review`, `kiwi-spacing` (local Kiwi spacing with protected spans), `korean-line-break`, `fluent-korean-content` | MIT · 2026-10-08 · 0 | `kiwi-spacing` is local. `spell_nara.py` posts text to nara-speller.co.kr (optional). `sync_upstream.py` calls the GitHub API | **Borrow.** Copy `kiwi-spacing` (local only) and the "protect original spans" contract into our skill. Drop the Nara path for client text | `translation-qa`, KO output proofing | n/a (copy after review). Upstream: github.com/eun7661010/korean-content-review |
| **NomaDamas/k-skill**: `korean-humanizer`, `korean-character-count`, `korean-spell-check` | 90+ Korean skills. The humanizer has a taxonomy of AI tells and translationese (번역체) in Korean | MIT · 2026-10-13 · 7.9k | **Runtime fetch.** SKILL.md runs `npx -y @nomadamas/k-skill@0 instruct <skill>`, an unpinned npm major. The spell-check skill calls Nara/PNU endpoints. The setup skill offers `gh api -X PUT /user/starred/...`. Mega-catalog | **Borrow** `korean-humanizer/references/ai-tell-taxonomy.md` and `instruction.md` as an EN→KO self-check list. **Avoid** installing the bundle | `translate` skill self-check (step 4) plus a rubric item in `rubrics/` | do not install |
| **snflkd/fluent-korean** | Output style that makes Claude write clear, natural Korean | MIT · 2026-08-23 · 1.4k | Markdown output style only | **Borrow** its rules into `docs/REGISTERS.md`. Not as a global output style, which would bleed into code work | `translator` agent prompt | n/a |
| **senshinji/claude-translation-skill** | Multi-agent pipeline: term researcher, translator and reviewer. Has a glossary JSON schema with confidence and sources, and an anti-fabrication checklist | MIT · 2026-03-12 · 32 | Markdown plus 2 test shell scripts, no network code | **Borrow** `references/glossary-schema.md` (high/medium/low confidence plus source URLs per term) and `anti-fabrication-checklist.md` (numbers copied exactly, no added explanations, `[unclear in original]` markers) | `translate` skill §glossary plus the `verifier` rubric | n/a |
| **Supervertaler/Supervertaler-for-Trados** | Trados Studio plugin with an MCP server into the live Studio session (TermLens, TM search) | NOASSERTION · 2026-10-16 · 8 | Windows/Trados only. License unclear | **Avoid unless** the user works in Trados daily | (translator, if adopted) | github.com/Supervertaler/Supervertaler-for-Trados |
| **irsali/translation-skill** | App i18n JSON/XLIFF file sync | AGPL-3.0 · 2026-05 · 0 | Node scripts | **Avoid.** Built for software string files, not freelance documents | — | — |
| **i18next/i18next-cli** skill | i18n for JS apps | (official i18next) | — | **Avoid** for this user (only relevant if she codes i18n apps) | `coder` | — |

### Gaps nobody fills, so build these small
- **TMX/TBX glossary handling.** No MCP server or skill exists. Use translate-toolkit storage classes to load `.tmx`/`.tbx` into the project `knowledge/glossary.md`, and export back.
- **Register and honorific control (존댓말/반말, -습니다/-요/-다).** No tool exists. Keep the harness's own StylePair approach and add a deterministic check: Kiwi tags the sentence-final endings (EF), and the check flags mixed endings within one register.

### Subtitles (SRT)
| Candidate | Verdict | Notes |
|---|---|---|
| **cdown/srt** (Python, MIT, 2026-10-13, 537★) and **tkarabela/pysubs2** (2026-10-11, 443★; supports SRT/ASS/VTT/TTML) | **Adopt (as library)** | Basis for a small `subtitle-qa` section in `translation-qa`. Checks: CPS (17 adult / 20 Netflix-style), ≤42 chars per line, ≤2 lines, overlaps, min/max duration, index continuity, and identical cue count and timings between source and target. `pip install srt pysubs2` |
| saidsurucu/subtitle-translator-skill | **Borrow** the glossary-first flow (build a character and term glossary over all episodes, then translate file by file). **Avoid** installing | Uses Codex CLI (OpenAI) as the translation engine, so client text leaves Claude. No license |
| omd0/srt-mcp | **Avoid** | No license, test artifacts committed in the repo root, inactive since 2025-10 |
| jianshuo/claude-skills `wjs-translating-subtitles` | **Borrow** the idea of re-segmenting cues at sentence boundaries | Targets ZH/EN |

---

## 2. Korean document formats (HWP/HWPX)

| Candidate | What it does | License · last push · stars | Security read | Verdict | Harness slot | Install (official source) |
|---|---|---|---|---|---|---|
| **chrisryugj/kordoc** | HWP 3.x/5.x, HWPX, HWPML, PDF, XLS/XLSX, DOCX, PPTX and images to Markdown. Also tables, form fields, diffs (신구대조), Markdown→HWPX, and **local Korean OCR** (PP-OCRv5 Korean ONNX). 17 MCP tools. Has a Claude Code plugin (skill only, no hooks) | MIT · 2026-10-16 · 2.5k · v4.22.5 | OCR models download from huggingface.co on first use. `watch --webhook` can POST. **`KORDOC_OFFLINE=1` blocks all outbound traffic and `KORDOC_ROOT=<dir>` confines MCP file access**: use both. `npx -y kordoc setup` edits every client config it finds, so register manually instead | **Adopt.** Becomes the first-choice converter in `intake` for `.hwp/.hwpx/.hml` and Korean scans | `intake` / `intake-extractor` (converter), `translator` (source extraction) | `claude mcp add kordoc -e KORDOC_ROOT=$HOME/work -- npx -y kordoc@4.22.5 mcp` (pin the version). Warm the OCR models once, then add `-e KORDOC_OFFLINE=1`. Plugin: `/plugin marketplace add chrisryugj/kordoc` then `/plugin install kordoc@kordoc` |
| **edwardkim/rhwp** (upstream engine) | Rust/WASM HWP/HWPX viewer and editor with a **built-in `rhwp mcp-serve`**. Tools: `hwp_info`, `hwp_search`, `hwp_export_text`, `hwp_export_tables`, `hwp_fill_fields`, `hwp_open`/`hwp_doc_*` sessions (`replace_text`, `set_cell`, `save`), `hwp_ir_diff`, SVG/PDF export. Saves HWP, HWPX and HML | MIT · 2026-10-16 · 4.0k · v0.8.7 | Stdio only. No network crates found in `src/`. Release binaries ship with `SHA256SUMS.txt`. The "HWP 2024 remote conversion" service is maintainer-only and not part of the MCP | **Adopt** for editing and filling Korean forms (deliverables back in HWP/HWPX) | `translator` (write the translation back into the client's HWP), `browser-operator` / form filling | Download a release from github.com/edwardkim/rhwp/releases and verify with `sha256sum -c SHA256SUMS.txt`. Then `claude mcp add rhwp -- rhwp mcp-serve` |
| treesoop/hwp-mcp | npm MCP wrapper over `@rhwp/core` 0.7.x (34 tools) | MIT · 2026-07-08 · 96 | No network code found | **Avoid (redundant).** Upstream rhwp now has its own MCP and a newer engine | — | — |
| Dayoooun/hwpx-mcp (and fork flamingo8006/hwpx-mcp) | HWPX-only, 125–132 tools | MIT · active | **Sends mermaid diagram source to `https://mermaid.ink`** (in `index.ts` and `HwpxDocument.ts`). 130 tools means context bloat | **Avoid** | — | — |
| Dev-Jahn/hwp-hwpx-editor | Plugin with 3 MCP servers, a skill, and SessionStart/Pre/PostToolUse **hooks** that run node scripts. First run builds a patched engine from a pinned commit (cargo, uvx, network) | MIT · 2026-09-18 · 0 | Heavy toolchain, hooks on every hwp tool call | **Borrow** its `references/verification.md` and `known-limits.md` (render-and-compare after edits). Don't install | `verify` skill: a HWP-specific check | — |
| gmlcjf0326/claude-code-hwp-mcp, m1ns2o/hwp-mcp-go, jkf87/hwp-mcp | Hancom COM automation | no license / Windows-only | Requires Hancom Office on Windows | **Avoid** (user is on Mac/Linux) | — | — |
| neolord0/hwp2hwpx (+ hwplib/hwpxlib) | Java HWP→HWPX converter | Apache-2.0 · 2026-08-31 | Local JAR | **Fallback only**, if kordoc or rhwp fail on a file | `intake` fallback | build from github.com/neolord0/hwp2hwpx |

---

## 3. Documents (PDF/DOCX/XLSX/PPTX) and OCR

| Candidate | License · activity | Security read | Verdict | Harness slot | Install |
|---|---|---|---|---|---|
| **anthropics/skills → `document-skills`** (docx, pdf, xlsx, pptx) | **Proprietary** ("governed by your agreement with Anthropic"), official, 2026-10-09, 182k★ | Local Python scripts (validators, `soffice` wrapper, `accept_changes.py`, form fill). No network calls found | **Adopt.** The docx skill's **tracked-changes (redline) workflow with `--author` validation** suits translation review and client edits. Use as-is; don't copy the files into the harness repo (license). They are already available in claude.ai sessions as `anthropic-skills:*` | `intake`, `translator` (DOCX deliverables with redlines), `job-application` (resume DOCX/PDF) | `claude plugin marketplace add anthropics/skills` then `claude plugin install document-skills@anthropic-agent-skills` |
| **kordoc** (above) | MIT | local OCR, offline flag | **Adopt.** Also the best Korean-aware PDF and scan converter found (README benchmark: OCR CER 0.041 on 102 pages; self-reported) | `intake` | see §2 |
| **PaddlePaddle/PaddleOCR → `paddleocr-mcp`** | Apache-2.0 · 2026-09-16 · 91k★ · mcp v0.8.5 | `PADDLEOCR_MCP_PPOCR_SOURCE` defaults to `local`. **Never set `aistudio`/`qianfan`** for client documents (uploads to Baidu) | **Adopt only if** kordoc's OCR is insufficient (handwriting, complex layout via PP-StructureV3) | `intake` OCR fallback | `pip install "paddleocr-mcp[local-cpu]"`, then `claude mcp add paddleocr -e PADDLEOCR_MCP_PPOCR_SOURCE=local -- paddleocr_mcp` |
| microsoft/markitdown (+ markitdown-mcp), docling-project/docling-mcp, datalab-to/marker, opendatalab/MinerU, opendataloader-pdf | MIT / MIT / Apache (marker weights have their own license) / NOASSERTION / Apache | local | Already in BLUEPRINT §0.5. Keep markitdown as the fast default for EN Office/PDF. None handle HWP | `intake` | per BLUEPRINT |
| adobe/skills → `adobe-for-creativity` (official marketplace) | Apache-2.0 | HTTP MCP to `adobe-creativity.adobe.io`. Skill descriptions say **"MANDATORY: any PDF task…"**, which hijacks routing away from local tools | **Avoid** for now: confidentiality, and it would override the harness's PDF path | — | — |
| wonderwhy-er/DesktopCommanderMCP (in official marketplace) | MIT | Grants broad terminal and process control | **Avoid.** Redundant with Claude Code's own tools, and widens the attack surface | — | — |

---

## 4. Data annotation

Nothing Claude-specific and well maintained exists. Annotation platforms (Outlier, DataAnnotation, Scale, etc.) often **forbid LLM assistance and off-platform copying of task content**. The harness must keep "prepare and check, never submit" and should check each platform's ToS before using anything.

| Candidate | License · activity | Verdict | Harness slot |
|---|---|---|---|
| **HumanSignal/label-studio-mcp-server** (official from the Label Studio vendor) | Apache-2.0 · last push 2025-05-30 · 37★ | **Adopt only if** the user runs her own Label Studio instance. Stale, so pin the commit. Install: `claude mcp add label-studio -e LABEL_STUDIO_URL=… -e LABEL_STUDIO_API_KEY=… -- uvx --from git+https://github.com/HumanSignal/label-studio-mcp-server@<sha> mcp-label-studio` | `annotation-assistant` |
| voxel51 `fiftyone` (official marketplace) | Apache-2.0 | Only for computer-vision dataset curation. **Skip** unless CV work appears | — |
| Inter-annotator agreement libraries: `krippendorff` (PyPI), pln-fing-udelar/fast-krippendorff (GPL-3.0, active), `statsmodels` Fleiss/Cohen kappa | — | **Adopt as tools** for self-consistency. Re-label a 10% sample blind a few days later and compute agreement with your earlier self per label | `annotation-workflow` consistency check |
| arXiv 2605.20809 "Refining and Reusing Annotation Guidelines for LLM Annotation" | paper | **Borrow** the "moderation loop": disagreements become guideline clarifications, logged with a rule id | `annotation-workflow` + `librarian` |
| master72o/llm-annotation-quality-lab | MIT, small | **Borrow** its before/after-guideline-change comparison idea | rubric |

---

## 5. Job search and freelancing

### Email and calendar
| Candidate | Verdict | Notes |
|---|---|---|
| **Gmail / Google Calendar / Google Drive claude.ai connectors** (official, already attached: `mcp__Gmail__*` etc.) | **Adopt** (already in use by `job-tracker`) | The `job-tracker` agent already denies send, reply, draft and trash. Keep it that way |
| GongRzhe/Gmail-MCP-Server | **Avoid** | ARCHIVED 2025-08. Needs your OAuth credentials stored locally |

### Resume and cover letter
| Candidate | License · activity · ★ | Security read | Verdict | Slot |
|---|---|---|---|---|
| **career-ops-hq/career-ops** | MIT · 2026-10-16 · 75k | ~200 `.mjs` scripts. `postinstall` downloads Chromium. Self-updater re-execs. Has OpenAI/Gemini/OpenRouter runners and job-board scanners | **Borrow** the ideas: `verify-cv-facts.mjs` (every generated claim must trace to source facts), `story-provenance-check`, `followup-cadence`, `check-liveness` (posting still open?), the 1–5 fit score before applying. **Avoid** installing (mega-app, auto-updates) | `job-application` + `verifier` |
| Paramchoudhary/ResumeSkills | MIT · 2026-06 · 2.7k | Markdown only, no scripts | **Borrow** `resume-tailor`, `job-description-analyzer`, `resume-quantifier` and `cover-letter-generator` as reference prompts | `job-application` |
| ARPeeketi/claude-resume-kit | MIT · 2026-03 · 289 | LaTeX | **Borrow** its anti-fabrication controls and "fresh session per stage" | `job-application` |
| MadsLorentzen/ai-job-search | MIT · 2026-10-15 · 48k | Danish job-board CLIs, `.claude/settings.json` pre-allows its Bash scripts | **Borrow** `tools/verify_pdf.py` / `verify_layout.py` (check rendered resume PDF layout) | `verify` |
| NomaDamas/k-skill `job-posting-match` | MIT | Searches JobKorea/Saramin public postings, but uses runtime npx fetch | **Borrow** for the Korean job market | `job-application` |
| proficientlyjobs/proficiently-claude-skills | **no license** · 2026-03 · 424 | Auto-fills Greenhouse/Lever/Workday forms | **Avoid** (no license; auto-apply conflicts with the "user submits" rule) | — |
| olegvg/resume-tailor-plugin, G-Eskayo/resume-tailor, silentashish/claude-resume-generator-skill | MIT/none, small | — | Skip. Covered by the above | — |

### Invoicing and time tracking
No tool handles **translation-style billing** (per source word or character, minimum fee, rush surcharge, KRW/USD, 원천징수 3.3%). Build it in the harness, using Kiwi or a deterministic counter for KO character counts.

| Candidate | License · activity | Verdict |
|---|---|---|
| RoseCompanion/claude-code-time-to-invoice | MIT (LICENSE file) · 2026-10-07 · 0★ | **Borrow** the exact-decimal maths, per-entry rounding, tax and minimum-charge logic for an `invoice` skill. Pure Python, no network found |
| RemoteCTO/claude-code-timelog | Apache-2.0 · 2026-02 · 9★ | **Borrow** the idea of break-aware duration estimation from the harness's own JSONL logs (the harness already logs sessions) |
| RobSpct/c2invoice | AGPL-3.0 · active | **Avoid.** It bills Claude-session time, not translation volume. AGPL |
| intuit-quickbooks, paypal (official marketplace) | official | **Adopt only if** she uses QuickBooks or PayPal invoicing. `claude plugin install intuit-quickbooks@claude-plugins-official` |
| FreelanceOS (paid hosted MCP) | — | **Avoid.** Paid, and client data goes to a third party |

---

## 6. Art, design and digital assets

| Candidate | License · activity | Security read | Verdict | Slot | Install |
|---|---|---|---|---|---|
| **Figma plugin** (`figma` in claude-plugins-official; source figma/mcp-server-guide v2.2.157) | official Figma | HTTP MCP `https://mcp.figma.com/mcp` (OAuth) plus 16 skills (`figma-use`, `figma-design-to-code`, `figma-generate-library`…) | **Adopt.** The Figma connector is already attached here. In local Claude Code, install the plugin so its skills load | `asset-decomposer` (read variables/tokens, export assets), `coder` | `claude plugin install figma@claude-plugins-official` |
| **psd-tools/psd-tools** | MIT · 2026-10-16 · 1.5k | Local Python | **Adopt (as library)** for PSD layer trees, per-layer PNG export, text layers, blend info | `asset-decompose` | `pip install psd-tools` |
| canva (official marketplace) | Apache-2.0 | Hosted Canva MCP | **Adopt only if** she uses Canva | `asset-decomposer` | `claude plugin install canva@claude-plugins-official` |
| drapon/psd-mcp-server | **no license** · 1★ | `ag-psd` + `canvas`, local | **Borrow** the `extract_colors` design (fills, strokes, shadows, gradients → CSS vars). Implement with psd-tools | `asset-decompose` palettes | — |
| x51xxx/coolors-mcp | MIT · 2026-05 · 4★ | Many deps (`mcp-proxy`, `undici`, `execa`) | **Borrow** the methods: Celebi quantization for dominant colors, HCT color space, WCAG contrast. A ~40-line Pillow script is enough | `asset-decompose` palettes | — |
| QwenLM/Qwen-Image-Layered | Apache-2.0 · 2025-12 · 2.1k | 20B diffusion model, needs a large GPU | **Borrow / later.** The only credible open model for flat image → editable RGBA layers. Keep as a vendor.md candidate for when she needs to decompose flattened art | `asset-decompose` (optional) | via `diffusers`, per repo |
| adobe-for-creativity | Apache-2.0 | cloud | **Avoid** (see §3) | — | — |
| Aseprite MCPs (pixel-mcp, etc.) | various | — | Skip unless pixel art | — | — |

---

## 7. Marketplaces and directories checked

- **anthropics/claude-plugins-official** (cloned): 315 entries. Domain-relevant entries are figma, canva, adobe-for-creativity, intuit-quickbooks, paypal, notion, slack, desktop-commander and fiftyone. There is **no** translation, annotation or careers entry.
- **anthropics/skills** (cloned): `document-skills` plugin (docx/pdf/xlsx/pptx, proprietary) and `example-skills` (skill-creator, canvas-design, theme-factory, etc.). The marketplace name is `anthropic-agent-skills`.
- **hesreallyhim/awesome-claude-code** (cloned 2026-10-16): only `i18next-localization` and some design-tool entries are relevant. Nothing for KO translation, annotation or HWP.
- **skills.sh** (via search): the top "translation" skills are code or docs translators (feiskyer `translate`, about 200 installs). Not CAT-grade.
- **claudemarketplaces.com**: DNS failed from this sandbox, so it was not checked.
- **darjeeling/awesome-mcp-korea** (248★): a useful index of Korean MCP servers (legal, public data), mostly outside these domains.
- **NomaDamas/k-skill** (7.9k★): the largest Korean skill bundle. Borrow individual skills only (see §1).

## 8. Suggested harness changes (proposals only, not applied)

1. `skills/intake/SKILL.md` step 2: route `.hwp/.hwpx/.hml` and Korean scanned PDFs to **kordoc** (`KORDOC_OFFLINE=1`, `KORDOC_ROOT`), and record `converter: kordoc@4.22.5`.
2. New skill `translation-qa`. It wraps `pofilter` (numbers, xmltags, variables, brackets, untranslated), a Kiwi particle-aware glossary check, register-ending consistency (EF tags), the anti-fabrication checklist (senshinji), and SRT checks (srt/pysubs2). The `verifier` runs it on every translation.
3. Extend the glossary format in `translate` with `confidence` and `sources[]` per term (senshinji schema), plus TMX/TBX import and export via translate-toolkit.
4. `asset-decompose`: psd-tools for PSD, the Figma plugin for Figma files, and a local palette script (Celebi/k-means + WCAG). Qwen-Image-Layered goes in vendor.md as a future option.
5. `job-application`: add a "fact provenance" gate (career-ops `verify-cv-facts` idea). Every resume bullet must cite a line in the master profile.
6. New small `invoice` skill: per-word or per-character billing with minimums, Decimal maths, and KRW/USD plus 3.3% withholding. No third-party install.
7. Add to `vendor.md`:
   - **adopted:** kordoc, rhwp, translate-toolkit, kiwipiepy, srt/pysubs2, psd-tools, document-skills, figma
   - **avoid, with reasons:** Dayoooun/flamingo hwpx-mcp (mermaid.ink), winterjung/mcp-korean-spell and Alfex4936/Hangul-MCP (text sent to Naver/Nara; stale), k-skill bundle (runtime npx fetch), career-ops install, adobe-for-creativity, proficiently (no license)

## 9. Not verified / caveats
- Stars and dates are from the GitHub search API on 2026-10-16. Licenses are as reported by GitHub. Where a repo shows "None" or "NOASSERTION", I read its LICENSE file only for RoseCompanion (MIT) and irsali (AGPL).
- I did not run any tool, so kordoc's OCR quality and rhwp's round-trip fidelity are as claimed in their READMEs. Test both on 3–5 real client files before relying on them (add these to the eval set).
- I did not open the pysubs2 license file (reported MIT by memory; verify). cdown/srt is tagged mit-license.
- Clones are in `/tmp/claude-0/-home-user-albers-club/1397d302-c3cb-5329-ad06-e45b2c66c6d1/scratchpad/scout/` for follow-up reading.
