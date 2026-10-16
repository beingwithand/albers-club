# Local research handoff

What to do on your own computer, where fewer things are blocked, to finish what this cloud session couldn't. It covers verifying facts, reading primary sources and running hands-on tests on a real Mac.

## 1. Set up
1. Clone the research branch:
   ```
   git clone -b research/personal-data-ownership https://github.com/beingwithand/albers-club relic-research
   cd relic-research
   ```
2. Open it with Claude Code. The `reports/` folder has every report, `research_notes/` has the source notes, and `reports/CORRECTIONS.md` has the corrections log and standing checks.
3. Start the session with:
   > Read reports/CORRECTIONS.md and reports/Local research handoff.md. Work through section 3 (verification) using WebFetch on primary sources. For each item, record verified / corrected / still unverifiable with the URL, update the affected report with an errata line, and add a CORRECTIONS.md row for anything that changed. Then do section 4.

## 2. What was blocked in the cloud session
These hosts were rejected by the network proxy or failed to resolve, so findings that depend on them came from search-result summaries:
- **Papers:** arxiv.org and export.arxiv.org, so every paper was read through summaries or its code repo.
- **Vendors:** openai.com, help.openai.com, about.fb.com, research.meta.ai, developers.google.com, Google Workspace help, learn.microsoft.com, blogs.windows.com, the Android Developers blog, signal.org, brave.com, tailscale.com, iroh.computer.
- **Projects:** immich.app, nextcloud.com, docs.mem0.ai, docs.screenpi.pe, the Zep blog, sia.tech, filecoin.io, ipshipyard.com, automerge.org, Hugging Face (model and dataset cards).
- **Press and researchers:** techcrunch.com, infoq.com, selfh.st, simonwillison.net, embracethered.com, ioactive.com.
- **GitHub REST API** (star counts, release dates). Plain `git clone` worked.

The gap-research notes (in `research_notes/Relic gap research/`) each end with a "Blocked sources" list. Add those to this list.

## 3. Verification checklist (highest value first)
**Product claims that rest on search summaries:**
- [ ] OpenAI "dots" (DevDay, 29 Sep 2026): the official post, model name ("GPT-6 Astra" is unverified), memory behaviour, pricing.
- [ ] Meta Muse: the Muse Spark, Muse app and Muse Wonder announcements; the Active Memory and "forget" behaviour; the TIME article of 6 Oct 2026.
- [ ] ChatGPT memory "Dreaming" (about 4 Jun 2026): the official page and its date.
- [ ] OpenAI Atlas: discontinued in Aug 2026, or not?
- [ ] The Claude in Chrome GA date and the reported attack-success figures.
- [ ] Ninth Circuit, Amazon v. Perplexity (about Aug 2026): read the opinion itself.

**Papers to read in full (arXiv):**
- [ ] Mem0 (2504.19413): hyperparameters, and paper versus code (see the build guide).
- [ ] Zep/Graphiti (2501.13956), HippoRAG 2, LightRAG, MemGPT (2310.08560), sleep-time compute (2504.13171), MemOS, A-MEM, Generative Agents. Check the recency formula against the code bug we found.
- [ ] LongMemEval, LoCoMo, MemoryAgentBench, BEAM: how they're constructed, and their critiques.
- [ ] Walrus Red Stuff (2505.05370) and the IMC '26 NAT-traversal study (2510.27500), if the shared-storage idea comes back.

**Docs and policies:**
- [ ] Google Play's accessibility policy, and its ban on autonomous AI agents (exact text and date).
- [ ] macOS Screen Recording re-prompt behaviour, and whether a Mac App Store (sandboxed) build can do capture plus accessibility.
- [ ] Google's Data Portability API country list, and the Gmail restricted-scope / CASA cost.
- [ ] Anthropic, OpenAI and Google terms on using outputs to train models (exact clauses).
- [ ] Licenses of each candidate open teacher and student model, and of the GUI datasets (commercial use?).

**Numbers to replace with real data:**
- [ ] GitHub stars and release dates for the build guide's license table.
- [ ] Screenpipe's current license text and pricing.

## 4. Hands-on tests on your Mac (the most important part)
These can't be done in the cloud at all:
1. **Korean text recognition:** screenshot Korean pages (KakaoTalk, Naver, Instagram in Korean) and compare Apple Vision (Live Text / VNRecognizeTextRequest) against PaddleOCR. Note accuracy and speed.
2. **Accessibility text coverage:** how much on-screen text the accessibility API returns in Chrome, Safari, KakaoTalk, Slack, Instagram on the web and Electron apps, compared with OCR.
3. **Local model speed and memory:** with MLX or llama.cpp, run the 3–4B and 7–8B candidates from `on_device_models.md` at 4-bit. Record tokens per second, RAM, and quality on 20 fact-extraction examples.
4. **Permission flow:** build a tiny signed test app that requests Screen Recording, Accessibility and Automation. Record every prompt, and how often it re-prompts.
5. **The 2-week test** (from the build guide): 50–100 of your real tasks, local models versus a frontier model. This decides where the hybrid line goes.

## 5. When you're done
- Commit the updated reports and CORRECTIONS.md to `research/personal-data-ownership`.
- Check that the files are actually in the commit (`git show --stat HEAD`) before pushing. This rule exists because of CORRECTIONS row 13.
